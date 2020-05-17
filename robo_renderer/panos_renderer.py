import os
import time
import base64
import uuid
import xml.etree.ElementTree as ET
import boto3
import airtable
import dotenv

import const
import util
import rendering_util


dotenv.load_dotenv()

S3 = boto3.client('s3', aws_access_key_id=os.getenv("ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY"))
panos_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Panos", api_key=const.AIRTABLE_API_KEY)
pano_versions_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Pano Versions", api_key=const.AIRTABLE_API_KEY)
units_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Units", api_key=const.AIRTABLE_API_KEY)

def render(unit_version, skp_file_path, settings_code):
    uv_fields = unit_version["fields"]
    unit_id = uv_fields["Unit"][0]
    airtable_panos = panos_airtable.get_all(formula="(FIND(\"" + unit_id + "\", ARRAYJOIN({Unit ID})))")
    panos_dicts = []
    
    rendering_util.remove_all_pano_files()

    programs = rendering_util.start_rendering_programs(skp_file_path)
    window = programs["SketchUp"]
    app = programs["App"]

    rendering_util.set_settings_code(app, window, settings_code)
    
    # Remove all Enscape Views now that we have rendered them
    rendering_util.type_keys(window, const.UPDATE_CAMERA_LOCATIONS_KEY)
    time.sleep(5)

    # Loop over panos
    for i in range(len(airtable_panos)):
        air_pano = airtable_panos[i]
        p_fields = air_pano["fields"]
        pano_name = p_fields["Name"]
        
        # Turn off live updates while switching scenes to avoid crashing...
        rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
        time.sleep(1)

        # Set pano page w/ Ruby Console.
        rendering_util.set_pano_name(app, window, pano_name)

        # Toggle sync views to get camera in correct spot.
        rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)
        time.sleep(3)
        rendering_util.type_keys(window, const.SYNC_CAMERA_KEY)

        # Turn on live updates again.  To refresh in increments.
        rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
        time.sleep(10)

        # Turn off live updates while switching scenes to avoid crashing...
        rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
        time.sleep(1)

        rendering_util.type_keys(window, const.SET_PANO_GEOLOCATION_KEY)
        time.sleep(5)

        # Turn on live updates again.
        rendering_util.type_keys(window, const.LIVE_UPDATES_KEY)
        time.sleep(15)

        # Render!
        rendering_util.type_keys(window, const.TAKE_MONO_PANO_KEY)
        time.sleep(45)

        # We explicitly store the Index since the list index might not match up
        # when missing a pano render or something like that.
        panos_dicts.append({ "Index": i, "Pano ID": air_pano["id"], "Pano Name": pano_name })

    save(unit_version, panos_dicts)

    # Gracefully close our programs...
    rendering_util.close_rendering_programs(app, window)

def save(unit_version, panos_dicts):
    uv_fields = unit_version["fields"]
    unit_version_id = unit_version["id"]
    unit_id = uv_fields["Unit"][0]
    unit_name = uv_fields["Unit Name"][0]
    project_name = uv_fields["Project Name"][0]
    panos_files = rendering_util.get_all_pano_files()
    
    for i in range(len(panos_files)):
        file = panos_files[i]
        tree = ET.parse(file)
        root = tree.getroot()
        pano_dict = next(d for d in panos_dicts if d["Index"] == i)

        if not pano_dict:
            continue
        
        pano_id = pano_dict["Pano ID"]
        pano_name = pano_dict["Pano Name"]
        img_data = root.find("ImageContent").text
        filename = str(uuid.uuid4()) + ".png"
        pretty_filename =  pano_name + " - " + unit_name + " - " + project_name + ".png"
        file_path = os.path.join(const.PANO_OUTPUT_DIR, filename)
        key = const.PANO_KEY_PREFIX + filename

        with open(file_path, "wb") as fh:
            fh.write(base64.b64decode(img_data))

        S3.upload_file(file_path, const.BUCKET_NAME, key, ExtraArgs={
            'ACL': 'public-read',
            'ContentDisposition': "attachment; filename=%s;" % pretty_filename,
            "ContentType": "image/png"
        })
        #S3.ObjectAcl(BUCKET_NAME, key).put(ACL='public-read')

        url = const.S3_DOMAIN + "/" + const.BUCKET_NAME + "/" + key

        pano_versions_airtable.insert({
            "Pano": [pano_id],
            "Unit Version": [unit_version_id],
            "Image URL": url,
        })
