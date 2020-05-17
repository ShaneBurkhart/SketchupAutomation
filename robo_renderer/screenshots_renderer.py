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
screenshot_versions_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Screenshot Versions", api_key=const.AIRTABLE_API_KEY)

def render(unit_version, skp_file_path, settings_code):
    uv_fields = unit_version["fields"]
    
    rendering_util.remove_all_screenshot_files()

    programs = rendering_util.start_rendering_programs(skp_file_path)
    window = programs["SketchUp"]
    app = programs["App"]

    rendering_util.set_settings_code(app, window, settings_code)

    # Use scene count to figure sleep
    rendering_util.type_keys(window, const.SETUP_SCREENSHOT_RENDERING_KEY)
    time.sleep(20)

    screenshot_count = rendering_util.get_num_of_pages(app, window)
    print("Rendering %d Screenshots..." % screenshot_count)

    for i in range(screenshot_count):
        # Turn off live updates while switching scenes to avoid crashing...
        rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
        time.sleep(8)

        rendering_util.type_keys(window, const.NEXT_PAGE_KEY)
        time.sleep(8)

        # Sync camera before enabling live updates to hopefully decrease load.
        rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)
        time.sleep(8)
        # Back off
        rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)
        time.sleep(8)

        # Turn on live updates again.  To refresh in increments.
        rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
        time.sleep(15)

        # Render Image
        rendering_util.type_keys(window, const.TAKE_SCREENSHOT_KEY)
        time.sleep(45)

    save(unit_version, rendering_util.get_all_screenshot_files())

    # Gracefully close our programs...
    rendering_util.close_rendering_programs(app, window)

def save(unit_version, screenshot_files):
    unit_version_id = unit_version["id"]

    for file_path in screenshot_files:
        key = const.SCREENSHOT_KEY_PREFIX + str(uuid.uuid4()) + ".png"

        S3.upload_file(file_path, const.BUCKET_NAME, key, ExtraArgs={
            'ACL': 'public-read',
            'ContentDisposition': "attachment;",
            "ContentType": "image/png"
        })

        url = const.S3_DOMAIN + "/" + const.BUCKET_NAME + "/" + key

        screenshot_versions_airtable.insert({
            "Unit Version": [unit_version_id],
            "Image URL": url,
        })
