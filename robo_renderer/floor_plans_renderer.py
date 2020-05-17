import pywinauto
import os
import time
import uuid
import boto3
import airtable
import dotenv

import const
import util
import rendering_util


dotenv.load_dotenv()

S3 = boto3.client('s3', aws_access_key_id=os.getenv("ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY"))
pano_versions_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Pano Versions", api_key=const.AIRTABLE_API_KEY)
unit_versions_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Unit Versions", api_key=const.AIRTABLE_API_KEY)

def render(unit_version, skp_file_path, settings_code):
    uv_fields = unit_version["fields"]
    
    rendering_util.remove_all_screenshot_files()

    programs = rendering_util.start_rendering_programs(skp_file_path)
    window = programs["SketchUp"]
    app = programs["App"]

    rendering_util.set_settings_code(app, window, settings_code)
    
    # Turn off live updates while switching scenes to avoid crashing...
    rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
    time.sleep(1)

    # Set pano page w/ Ruby Console.
    rendering_util.set_pano_name(app, window, "Floor Plan")

    # Take Floor Plan image
    rendering_util.type_keys(window, const.SET_FLOOR_PLAN_CAMERA_KEY)
    time.sleep(15)

    # Sync camera before enabling live updates to hopefully decrease load.
    rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)
    time.sleep(8)
    # Back off
    rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)
    time.sleep(8)

    # Turn on live updates again.  To refresh in increments.
    rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
    time.sleep(5)

    # Turn off live updates while switching scenes to avoid crashing...
    rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
    time.sleep(1)
    rendering_util.type_keys(window, const.SET_FLOOR_PLAN_GEOLOCATION_KEY)
    time.sleep(8)

    # Turn on live updates again.
    rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
    time.sleep(5)

    # Render Image
    rendering_util.type_keys(window, const.TAKE_SCREENSHOT_KEY)
    time.sleep(30)

    # Turn off sync.  Keep this reset for looping later.
    rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)

    save(unit_version, rendering_util.get_all_screenshot_files())

    # Gracefully close our programs...
    rendering_util.close_rendering_programs(app, window)

def save(unit_version, floor_plan_files):
    unit_version_id = unit_version["id"]
    floor_plan_path = floor_plan_files[0]

    fp_key = const.FLOOR_PLAN_KEY_PREFIX + str(uuid.uuid4()) + ".png"
    S3.upload_file(floor_plan_path, const.BUCKET_NAME, fp_key, ExtraArgs={
        'ACL':'public-read',
        "ContentType": "image/png"
    })

    fp_url = const.S3_DOMAIN + "/" + const.BUCKET_NAME + "/" + fp_key
    unit_versions_airtable.update_by_field("Record ID", unit_version_id, { "Floor Plan Image URL": fp_url })
