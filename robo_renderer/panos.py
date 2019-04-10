import pyautogui
import pywinauto
import datetime
import base64
import time
import os
import xml.etree.ElementTree as ET
import airtable
import threading
import asyncio
import urllib.request
import boto3
import uuid
import dotenv
import subprocess

dotenv.load_dotenv()

#TODO Pull in settings for Enscape
#TODO Create server to check airtables every X minutes

panos_airtable = airtable.Airtable("appTAmLzyXUW1RxaH", "Panos", api_key="keyg0WJMB3XPaM6J7")
units_airtable = airtable.Airtable("appTAmLzyXUW1RxaH", "Units", api_key="keyg0WJMB3XPaM6J7")
unit_versions_airtable = airtable.Airtable("appTAmLzyXUW1RxaH", "Unit Versions", api_key="keyg0WJMB3XPaM6J7")
pano_versions_airtable = airtable.Airtable("appTAmLzyXUW1RxaH", "Pano Versions", api_key="keyg0WJMB3XPaM6J7")
screenshot_versions_airtable = airtable.Airtable("appTAmLzyXUW1RxaH", "Screenshot Versions", api_key="keyg0WJMB3XPaM6J7")
finish_options_airtable = airtable.Airtable("app5xuA2wJKN1rkp0", "Finish Options", api_key="keyg0WJMB3XPaM6J7")

S3_DOMAIN = "https://s3-us-west-2.amazonaws.com"
S3 = boto3.client('s3', aws_access_key_id=os.getenv("ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY"))
BUCKET_NAME = "finish-vision-vr"
PANO_KEY_PREFIX = "panos/"
SCREENSHOT_KEY_PREFIX = "screenshots/"
FLOOR_PLAN_KEY_PREFIX = "floor-plans/"
FINISH_SKP_KEY_PREFIX = "finish-skp/"
UNIT_SKP_KEY_PREFIX = "unit-skp/"

FINISH_UPLOAD_DIR = "D:\\Google Drive\\NewDev\\10000 Construction VR\\MAGIC FOLDERS\\FINISH UPLOAD"
TO_RENDER_DIR = "D:\\Google Drive\\NewDev\\10000 Construction VR\\MAGIC FOLDERS\\TO RENDER"
TMP_SKP_DIR = "D:\\TMP_SKPs"
FP_OUTPUT_DIR = "C:\\Users\\shane\\Documents\\FinishVisionVR\\Rendered Floor Plans"
PANO_OUTPUT_DIR = "C:\\Users\\shane\\Documents\\FinishVisionVR\\Rendered Panos"
ENSCAPE_PANO_DIR = "C:\\Users\\shane\\Documents\\Enscape\\Panoramas"
SKETCHUP_EXE = "C:\\Program Files\\SketchUp\\SketchUp 2019\\SketchUp.exe"

UPDATE_CAMERA_LOCATIONS_KEY = "+{F2}"
SET_PANO_GEOLOCATION_KEY = "+{F3}"
SET_FLOOR_PLAN_GEOLOCATION_KEY = "+{F4}"
SYNC_CAMERA_KEY = "+{F5}"
SET_FLOOR_PLAN_CAMERA_KEY = "+{F6}"
LIVE_UPDATES_KEY = "+{F7}"
START_ENSCAPE_KEY = "+{F8}"
TAKE_MONO_PANO_KEY = "+{F10}"
TAKE_SCREENSHOT_KEY = "+{F11}"
SETUP_SCREENSHOT_RENDERING_KEY = "+{F12}"
NEXT_PAGE_KEY = "{PGUP}"
TAB_KEY = "{TAB}"
ENTER_KEY = "{ENTER}"

# In meters
CAMERA_POSITION_THRESHOLD = 0.0001

WAIT_DELAY = 60
START_SKETCHUP_DELAY = 90

AIRTABLE_LOCK = threading.RLock()
ENSCAPE_LOCK = threading.RLock()
WINDOW_LOCK = threading.RLock()
RENDER_PANO_LOCK = threading.RLock()
RENDER_IMAGE_LOCK = threading.RLock()

# Multithreading not really working atm
MAX_TASKS = 1

def get_latest_screenshot_file():
    files = os.listdir(FP_OUTPUT_DIR)
    paths = [os.path.join(FP_OUTPUT_DIR, basename) for basename in files]
    return max(paths, key=os.path.getctime)

def get_latest_pano_file():
    files = os.listdir(ENSCAPE_PANO_DIR)
    paths = [os.path.join(ENSCAPE_PANO_DIR, basename) for basename in files]
    return max(paths, key=os.path.getctime)

def get_latest_pano_files():
    files = os.listdir(ENSCAPE_PANO_DIR)
    paths = []
    for basename in files:
        path = os.path.join(ENSCAPE_PANO_DIR, basename)
        ctime = os.path.getctime(path)
        if ctime > start.timestamp():
            paths.append(path)
    return paths

def get_all_pano_files():
    files = os.listdir(ENSCAPE_PANO_DIR)
    paths = [os.path.join(ENSCAPE_PANO_DIR, basename) for basename in files]
    return paths

def get_all_screenshot_files():
    files = os.listdir(FP_OUTPUT_DIR)
    paths = [os.path.join(FP_OUTPUT_DIR, basename) for basename in files]
    return paths

def remove_all_pano_files():
    files = os.listdir(ENSCAPE_PANO_DIR)
    for basename in files:
        path = os.path.join(ENSCAPE_PANO_DIR, basename)
        os.remove(path)

def remove_all_screenshot_files():
    files = os.listdir(FP_OUTPUT_DIR)
    for basename in files:
        path = os.path.join(FP_OUTPUT_DIR, basename)
        os.remove(path)

def parse_unit_id(filename):
    parts = filename.split("-")
    return parts[0].strip()

def get_panos_for_unit(unit_id):
    return panos_airtable.get_all(formula="(FIND(\"" + unit_id + "\", ARRAYJOIN({Unit ID})))")

def get_unit(unit_id):
    return units_airtable.get(unit_id)

def type_keys(window, key):
    WINDOW_LOCK.acquire()
    print(key)

    for i in range(3):
        print("Try {}".format(i+1))
        
        try:
            window.type_keys(key)
            # Break if we make it.
            break
        except Exception as e:
            print("Exception, trying again...")
            
            if i == 2:
                print("Tried 3 times... Throwing exception...")
                raise e

            time.sleep(15)

    WINDOW_LOCK.release()

# ~20 mins per file
async def render(unit_version, skp_file_path):
    uv_fields = unit_version["fields"]
    print("Rendering: %s" % uv_fields["Unit Name"][0])
    first_camera=None
    pano_files = []

    remove_all_pano_files()

    unit_file_path = skp_file_path
    unit_id = uv_fields["Unit ID"][0]
    unit_version_id = unit_version["id"]

    AIRTABLE_LOCK.acquire()
    airtable_unit = get_unit(unit_id)
    AIRTABLE_LOCK.release()

    print(unit_file_path)
    WINDOW_LOCK.acquire()
    #For testing
    #app = pywinauto.Application().connect(path=SKETCHUP_EXE)
    command = SKETCHUP_EXE + " \"" + unit_file_path + "\""
    app = pywinauto.Application().start(command)
    await asyncio.sleep(30)
    try:
        # Try to press enter if there is read only warning
        window = app.top_window()
        type_keys(window, ENTER_KEY)
    except:
        pass

    await asyncio.sleep(START_SKETCHUP_DELAY-30)
    print("Started...")

    window = app.window(title_re=".+ - SketchUp Pro 2019")
    window.move_window(x=None, y=None, width=1920, height=1080, repaint=True)
    WINDOW_LOCK.release()

    ENSCAPE_LOCK.acquire()
    print("Starting Enscape")
    type_keys(window, START_ENSCAPE_KEY)
    await asyncio.sleep(90)
    ENSCAPE_LOCK.release()

    enscape_window = app.window(title_re=".*Enscape.*")
    enscape_window.move_window(x=None, y=None, width=1920, height=1080, repaint=True)

    remove_all_screenshot_files()

    # Use scene count to figure sleep
    screenshot_count = uv_fields["Screenshot Count"]
    type_keys(window, SETUP_SCREENSHOT_RENDERING_KEY)
    await asyncio.sleep(8)

    for i in range(screenshot_count):
        # Turn off live updates while switching scenes to avoid crashing...
        type_keys(window, LIVE_UPDATES_KEY)
        await asyncio.sleep(8)

        type_keys(window, NEXT_PAGE_KEY)
        await asyncio.sleep(8)

        # Sync camera before enabling live updates to hopefully decrease load.
        type_keys(window, SYNC_CAMERA_KEY)
        await asyncio.sleep(8)
        # Back off
        type_keys(window, SYNC_CAMERA_KEY)
        await asyncio.sleep(8)

        # Turn on live updates again.  To refresh in increments.
        type_keys(window, LIVE_UPDATES_KEY)
        await asyncio.sleep(15)

        # Render Image
        type_keys(window, TAKE_SCREENSHOT_KEY)
        await asyncio.sleep(45)

    screenshot_files = get_all_screenshot_files()

    # Restart SketchUp to make it through without crashing...
    WINDOW_LOCK.acquire()
    app.kill()
    WINDOW_LOCK.release()

    await asyncio.sleep(8)

    WINDOW_LOCK.acquire()
    #For testing
    #app = pywinauto.Application().connect(path=SKETCHUP_EXE)
    command = SKETCHUP_EXE + " \"" + unit_file_path + "\""
    app = pywinauto.Application().start(command)
    await asyncio.sleep(30)
    try:
        # Try to press enter if there is read only warning
        window = app.top_window()
        type_keys(window, ENTER_KEY)
    except:
        pass

    await asyncio.sleep(START_SKETCHUP_DELAY-30)
    print("Started...")

    window = app.window(title_re=".+ - SketchUp Pro 2019")
    WINDOW_LOCK.release()

    ENSCAPE_LOCK.acquire()
    print("Starting Enscape")
    type_keys(window, START_ENSCAPE_KEY)
    await asyncio.sleep(60)
    ENSCAPE_LOCK.release()

    # Remove all Enscape Views now that we have rendered them
    type_keys(window, UPDATE_CAMERA_LOCATIONS_KEY)
    await asyncio.sleep(5)

    # Turn off live updates while switching scenes to avoid crashing...
    type_keys(window, LIVE_UPDATES_KEY)
    await asyncio.sleep(1)

    # Take Floor Plan image
    type_keys(window, SET_FLOOR_PLAN_CAMERA_KEY)
    await asyncio.sleep(15)

    # Sync camera before enabling live updates to hopefully decrease load.
    type_keys(window, SYNC_CAMERA_KEY)
    await asyncio.sleep(8)
    # Back off
    type_keys(window, SYNC_CAMERA_KEY)
    await asyncio.sleep(8)

    # Turn on live updates again.  To refresh in increments.
    type_keys(window, LIVE_UPDATES_KEY)
    await asyncio.sleep(5)

    # Turn off live updates while switching scenes to avoid crashing...
    type_keys(window, LIVE_UPDATES_KEY)
    await asyncio.sleep(1)
    type_keys(window, SET_FLOOR_PLAN_GEOLOCATION_KEY)
    await asyncio.sleep(8)

    # Turn on live updates again.
    type_keys(window, LIVE_UPDATES_KEY)
    await asyncio.sleep(5)

    # Assuming we are turning on sync
    type_keys(window, SYNC_CAMERA_KEY)
    await asyncio.sleep(8)

    # Render Image
    RENDER_IMAGE_LOCK.acquire()
    type_keys(window, TAKE_SCREENSHOT_KEY)
    await asyncio.sleep(30)

    # Rename Floor Plan image
    unit_fields = airtable_unit["fields"]
    floor_plan_filename = unit_fields["Project Name"][0] + " - " + unit_fields["Name"] + ".png"
    floor_plan_path = os.path.join(FP_OUTPUT_DIR, floor_plan_filename)
    if os.path.isfile(floor_plan_path):
        print("Removing previous floor plan: " + floor_plan_path)
        os.remove(floor_plan_path)
    os.rename(get_latest_screenshot_file(), floor_plan_path)
    RENDER_IMAGE_LOCK.release()

    # Turn off sync
    type_keys(window, SYNC_CAMERA_KEY)

    while True:
        # Turn off live updates while switching scenes to avoid crashing...
        type_keys(window, LIVE_UPDATES_KEY)
        await asyncio.sleep(1)

        type_keys(window, NEXT_PAGE_KEY)
        await asyncio.sleep(8)

        # Toggle sync views to get camera in correct spot.
        type_keys(window, SYNC_CAMERA_KEY)
        await asyncio.sleep(3)
        type_keys(window, SYNC_CAMERA_KEY)

        # Turn on live updates again.  To refresh in increments.
        type_keys(window, LIVE_UPDATES_KEY)
        await asyncio.sleep(10)

        # Turn off live updates while switching scenes to avoid crashing...
        type_keys(window, LIVE_UPDATES_KEY)
        await asyncio.sleep(1)
    
        type_keys(window, SET_PANO_GEOLOCATION_KEY)
        await asyncio.sleep(5)

        # Turn on live updates again.
        type_keys(window, LIVE_UPDATES_KEY)
        await asyncio.sleep(10)

        RENDER_PANO_LOCK.acquire()
        # Render!
        type_keys(window, TAKE_MONO_PANO_KEY)

        await asyncio.sleep(120)

        pano_num = len(pano_files) + 1
        file = os.path.join(ENSCAPE_PANO_DIR, "panorama_%i.xml" % pano_num)
        RENDER_PANO_LOCK.release()
        print(file)

        tree = ET.parse(file)
        root = tree.getroot()
        camera = root.find("Camera")

        if first_camera == None:
            first_camera = [camera.find("x").text, camera.find("y").text, camera.find("z").text]
        else:
            if first_camera[0] == camera.find("x").text and \
               first_camera[1] == camera.find("y").text and \
               first_camera[2] == camera.find("z").text:
                # Remove the last pano file since it's a repeat
                os.remove(file)
                print("Breaking")
                break

        pano_files.append(file)

    WINDOW_LOCK.acquire()
    app.kill()
    WINDOW_LOCK.release()

    await asyncio.sleep(5)

    # Remove unit file now that we are done with it

    await save_unit_version(unit_version, pano_files, screenshot_files, floor_plan_path)

    os.remove(unit_file_path)

async def save_unit_file(unit_version, unit_file_path):
    unit_version_id = unit_version["id"]

    print("Uploading SKP file... This will take a while...")
    skp_key = UNIT_SKP_KEY_PREFIX + str(uuid.uuid4()) + ".skp"
    S3.upload_file(unit_file_path, BUCKET_NAME, skp_key, ExtraArgs={
        'ACL':'public-read',
        'ContentDisposition': "attachment;",
    })

    skp_url = S3_DOMAIN + "/" + BUCKET_NAME + "/" + skp_key
    unit_versions_airtable.update_by_field("Record ID", unit_version_id, { "SKP File URL": skp_url })

async def save_model_data(unit_version, unit_file_path):
    unit_version_id = unit_version["id"]

    result = subprocess.run(["C:\\Users\\shane\\Workspace\\SketchupAutomation\\robo_renderer\\ModelDataScraper.exe", unit_file_path], stdout=subprocess.PIPE)
    output = result.stdout.decode("utf-8")

    unit_versions_airtable.update_by_field("Record ID", unit_version_id, { "Model Data Output": output })

async def save_unit_version(unit_version, pano_files, screenshot_files, floor_plan_path):
    unit_version_id = unit_version["id"]
    unit_id = unit_version["fields"]["Unit ID"][0]
    print(pano_files)

    AIRTABLE_LOCK.acquire()
    airtable_panos = get_panos_for_unit(unit_id)
    AIRTABLE_LOCK.release()

    for file_path in screenshot_files:
        key = SCREENSHOT_KEY_PREFIX + str(uuid.uuid4()) + ".png"

        S3.upload_file(file_path, BUCKET_NAME, key, ExtraArgs={
            'ACL': 'public-read',
            'ContentDisposition': "attachment;",
            "ContentType": "image/png"
        })

        url = S3_DOMAIN + "/" + BUCKET_NAME + "/" + key

        screenshot_versions_airtable.insert({
            "Unit Version": [unit_version_id],
            "Image URL": url,
        })


    i = 0
    for file in pano_files:
        i += 1
        tree = ET.parse(file)
        root = tree.getroot()
        camera = root.find("Camera")
        pano_x = abs(float(camera.find("x").text))
        pano_y = abs(float(camera.find("y").text))
        pano_z = abs(float(camera.find("z").text))

        for air_pano in airtable_panos:
            fields = air_pano["fields"]

            if fields.get("Scene Camera X") == None or \
               fields.get("Scene Camera Y") == None or \
               fields.get("Scene Camera Z") == None:
                continue

            # We abs all cords even though we could have positive and negative cords.
            # I haven't figured out the Sketchup to Enscape alignment yet and we check
            # the threshold to a 10th of a mm...
            dx = abs(abs(fields["Scene Camera X"]) - abs(pano_x))
            # Swapped pano_z and pano_y since they are stored swapped.
            dy = abs(abs(fields["Scene Camera Y"]) - abs(pano_z))
            dz = abs(abs(fields["Scene Camera Z"]) - abs(pano_y))

            # print("dX: %f  dY: %f  dZ: %f" % [dx, dy, dz])

            if dx < CAMERA_POSITION_THRESHOLD and \
               dy < CAMERA_POSITION_THRESHOLD and \
               dz < CAMERA_POSITION_THRESHOLD:
                # Found matching pano, upload file
                img_data = root.find("ImageContent").text
                filename = fields["Project Name"][0] + " - " + fields["Unit Name"][0] + " - " + fields["Name"] + ".png"
                file_path = os.path.join(PANO_OUTPUT_DIR, filename)
                key = PANO_KEY_PREFIX + str(uuid.uuid4()) + ".png"

                with open(file_path, "wb") as fh:
                    fh.write(base64.b64decode(img_data))

                S3.upload_file(file_path, BUCKET_NAME, key, ExtraArgs={
                    'ACL': 'public-read',
                    'ContentDisposition': "attachment; filename=%s;" % filename,
                    "ContentType": "image/png"
                })
                #S3.ObjectAcl(BUCKET_NAME, key).put(ACL='public-read')

                url = S3_DOMAIN + "/" + BUCKET_NAME + "/" + key

                pano_versions_airtable.insert({
                    "Pano": [air_pano["id"]],
                    "Unit Version": [unit_version_id],
                    "Image URL": url,
                })

    # Updating floor plan takes unit version out of "To Render" view so do it last.
    fp_key = FLOOR_PLAN_KEY_PREFIX + str(uuid.uuid4()) + ".png"
    S3.upload_file(floor_plan_path, BUCKET_NAME, fp_key, ExtraArgs={
        'ACL':'public-read',
        "ContentType": "image/png"
    })

    fp_url = S3_DOMAIN + "/" + BUCKET_NAME + "/" + fp_key
    unit_versions_airtable.update_by_field("Record ID", unit_version_id, { "Floor Plan Image URL": fp_url })
    print("Done!")


async def tester():
    print("Starting tester")

    while True:
        unit_files = os.listdir(TO_RENDER_DIR)
        tasks = []
        print(unit_files)

        for unit_file in unit_files:
            unit_file_path = os.path.join(TO_RENDER_DIR, unit_file)

            if "AutoSave" in unit_file or ".png" in unit_file or ".skp" not in unit_file:
                os.remove(unit_file_path)
                continue

            unit_id = parse_unit_id(unit_file)
            unit_version = unit_versions_airtable.insert({ "Unit": [unit_id] })
            unit_version_id = unit_version["id"]

            await save_unit_file(unit_version, unit_file_path)
            await save_model_data(unit_version, unit_file_path)

            os.remove(unit_file_path)

        await asyncio.sleep(WAIT_DELAY)

async def download_unit_version_file(sketchup_file_url, tmp_filepath):
    urllib.request.urlretrieve(sketchup_file_url, tmp_filepath)
    await asyncio.sleep(5)

async def renderer():
    print("Starting robot renderer")

    try:
        os.mkdir(TMP_SKP_DIR)
    except OSError:
        print ("Creation of the directory %s failed" % TMP_SKP_DIR)
    else:
        print ("Successfully created the directory %s " % TMP_SKP_DIR)

    while True:
        unit_versions_to_render = unit_versions_airtable.get_all(view="To Render")
        print(unit_versions_to_render)

        for unit_version in unit_versions_to_render:
            fields = unit_version["fields"]
            unit_version_id = unit_version["id"]
            unit_id = fields["Unit ID"][0]
            sketchup_file_url = fields["SKP File URL"]
            filename = "{} - {}".format(unit_id, os.path.basename(sketchup_file_url))
            tmp_file_path = os.path.join(TMP_SKP_DIR, filename)

            print("Downloading: %s" % sketchup_file_url)
            if not os.path.isfile(tmp_file_path):
                await download_unit_version_file(sketchup_file_url, tmp_file_path)
            await render(unit_version, tmp_file_path)

        await asyncio.sleep(WAIT_DELAY)

async def finish_uploader():
    print("Starting finish uploader")

    while True:
        finish_files = os.listdir(FINISH_UPLOAD_DIR)
        tasks = []
        print(finish_files)

        for finish_file in finish_files:
            finish_id = parse_unit_id(finish_file)
            finish_file_path = os.path.join(FINISH_UPLOAD_DIR, finish_file)
            print(finish_file)
            print(finish_id)

            if ".skp" not in finish_file:
                os.remove(finish_file_path)
                continue

            f_key = FINISH_SKP_KEY_PREFIX + str(uuid.uuid4()) + ".skp"
            S3.upload_file(finish_file_path, BUCKET_NAME, f_key, ExtraArgs={ 'ACL':'public-read' })

            f_url = S3_DOMAIN + "/" + BUCKET_NAME + "/" + f_key
            finish_options_airtable.update_by_field("Record ID", finish_id, { "SketchUp Model URL": f_url })

            os.remove(finish_file_path)

        await asyncio.sleep(WAIT_DELAY)

TEST_PANO_FILES = [
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_644.xml',
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_645.xml',
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_645.xml',
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_647.xml',
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_647.xml',
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_649.xml',
    'C:\\Users\\shane\\Documents\\Enscape\\Panoramas\\panorama_650.xml'
]

async def main():
    #server_task = asyncio.create_task(server())
    tester_task = asyncio.create_task(tester())
    renderer_task = asyncio.create_task(renderer())
    finish_uploader_task  = asyncio.create_task(finish_uploader())
    #await save_unit_version("recNEgNBsRfG73J7B", TEST_PANO_FILES)
    #await renderer_task
    done, pending = await asyncio.wait([finish_uploader_task, renderer_task, tester_task], return_when=asyncio.FIRST_COMPLETED)

async def error_handler():
    await main()

    # Something went wrong.  Wait so we can see the output.
    input("Press Enter to exit...")

asyncio.run(error_handler())
