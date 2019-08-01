import time
import os
import uuid
import boto3
import airtable
import dotenv

import const
import util

dotenv.load_dotenv()

S3 = boto3.client('s3', aws_access_key_id=os.getenv("ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY"))
finish_options_airtable = airtable.Airtable(const.AIRTABLE_FINISHES_APP_ID, "Finish Options", api_key=const.AIRTABLE_API_KEY)

def save_unit_file(finish_option, model_file_path):
    finish_option_id = finish_option["id"]

    print("Uploading SKP file... This will take a while...")
    skp_key = const.FINISH_SKP_KEY_PREFIX + str(uuid.uuid4()) + ".skp"
    S3.upload_file(model_file_path, const.BUCKET_NAME, skp_key, ExtraArgs={
        'ACL':'public-read',
        'ContentDisposition': "attachment;",
    })

    skp_url = const.S3_DOMAIN + "/" + const.BUCKET_NAME + "/" + skp_key
    finish_options_airtable.update_by_field("Record ID", finish_option_id, { "SketchUp Model URL": skp_url })

print("Starting uploader...")

while True:
    files = os.listdir(const.FINISH_UPLOAD_DIR)
    tasks = []

    for file in files:
        file_path = os.path.join(const.FINISH_UPLOAD_DIR, file)

        if "AutoSave" in file or ".png" in file or ".skp" not in file:
            os.remove(file_path)
            continue

        finish_id = util.parse_finish_id(file)
        finish_options = finish_options_airtable.get_all(formula="{Record ID} = '%s'" % finish_id)

        if finish_options:
            finish_option = finish_options[0]
            save_unit_file(finish_option, file_path)

        os.remove(file_path)

    time.sleep(const.WAIT_DELAY)
