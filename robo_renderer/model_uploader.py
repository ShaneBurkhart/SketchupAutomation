import time
import os
import uuid
import boto3
import airtable
import dotenv
import subprocess

import const
import util

dotenv.load_dotenv()

S3 = boto3.client('s3', aws_access_key_id=os.getenv("ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY"))
unit_versions_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Unit Versions", api_key=const.AIRTABLE_API_KEY)

def save_unit_file(unit_version, unit_file_path):
    unit_version_id = unit_version["id"]

    print("Uploading SKP file... This will take a while...")
    skp_key = const.UNIT_SKP_KEY_PREFIX + str(uuid.uuid4()) + ".skp"
    S3.upload_file(unit_file_path, const.BUCKET_NAME, skp_key, ExtraArgs={
        'ACL':'public-read',
        'ContentDisposition': "attachment;",
    })

    skp_url = const.S3_DOMAIN + "/" + const.BUCKET_NAME + "/" + skp_key
    unit_versions_airtable.update_by_field("Record ID", unit_version_id, { "SKP File URL": skp_url })

def save_model_data(unit_version, unit_file_path):
    unit_version_id = unit_version["id"]

    result = subprocess.run(["C:\\Users\\shane\\Workspace\\SketchupAutomation\\robo_renderer\\ModelDataScraper.exe", unit_file_path], stdout=subprocess.PIPE)
    output = result.stdout.decode("utf-8")

    unit_versions_airtable.update_by_field("Record ID", unit_version_id, { "Model Data Output": output })


print("Starting uploader...")

while True:
    unit_files = os.listdir(const.TO_RENDER_DIR)
    tasks = []

    for unit_file in unit_files:
        unit_file_path = os.path.join(const.TO_RENDER_DIR, unit_file)

        if "AutoSave" in unit_file or ".png" in unit_file or ".skp" not in unit_file:
            os.remove(unit_file_path)
            continue

        unit_id = util.parse_unit_id(unit_file)
        unit_version = unit_versions_airtable.insert({ "Unit": [unit_id] })
        unit_version_id = unit_version["id"]

        save_unit_file(unit_version, unit_file_path)
        save_model_data(unit_version, unit_file_path)

        os.remove(unit_file_path)

    time.sleep(const.WAIT_DELAY)
