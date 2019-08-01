import urllib.request
import time
import os
import dotenv
import airtable
import traceback
import datetime

import const
import rendering_util
import screenshots_renderer
import panos_renderer
import floor_plans_renderer


dotenv.load_dotenv()

# In the order to be rendered.
COLUMN_PREFIXES = [
    "Floor Plans",
    "Panos",
    "Screenshots",
]

PREFIX_FUNCTIONS = {
    "Floor Plans": floor_plans_renderer.render,
    "Panos": panos_renderer.render,
    "Screenshots": screenshots_renderer.render,
}

unit_versions_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Unit Versions", api_key=const.AIRTABLE_API_KEY)
rendering_settings_airtable = airtable.Airtable(const.AIRTABLE_APP_ID, "Rendering Settings", api_key=const.AIRTABLE_API_KEY)

def download_unit_version_file(sketchup_file_url, tmp_filepath):
    urllib.request.urlretrieve(sketchup_file_url, tmp_filepath)
    time.sleep(5)

def download_rendering_setting(code):
    rendering_setting = rendering_settings_airtable.match("Name", code, view="Available")
    if not rendering_setting:
        return
    
    path = os.path.join(const.ENSCAPE_SETTINGS_DIR, "active")
    os.remove(path)
    time.sleep(1)

    fields = rendering_setting["fields"]
    urllib.request.urlretrieve(fields["Settings File"][0]["url"], path)
    time.sleep(5)

def create_tmp_dir():
    # Attempt to create directory.  If fails, we assume it exists.
    try:
        os.mkdir(const.TMP_SKP_DIR)
    except OSError:
        print ("Creation of the directory %s failed" % const.TMP_SKP_DIR)
    else:
        print ("Successfully created the directory %s " % const.TMP_SKP_DIR)
  
# MAIN
print("Starting robot renderer")

create_tmp_dir()

while True:
    try:
        unit_versions_to_render = unit_versions_airtable.get_all(view="To Render")

        for unit_version in unit_versions_to_render:
            fields = unit_version["fields"]
            unit_version_id = unit_version["id"]
            unit_id = fields["Unit ID"][0]
            unit_name = fields["Unit Name"][0]
            sketchup_file_url = fields["SKP File URL"]
            filename = "{} - {}".format(unit_id, os.path.basename(sketchup_file_url))
            tmp_file_path = os.path.join(const.TMP_SKP_DIR, filename)

            print("Rendering %s" % unit_name)
            print("Downloading: %s" % sketchup_file_url)
            if not os.path.isfile(tmp_file_path):
                download_unit_version_file(sketchup_file_url, tmp_file_path)

            for prefix in COLUMN_PREFIXES:
                started_at = "%s Started At" % prefix
                finished_at = "%s Finished At" % prefix
                data = { "Rendering Retries": 0 }
                settings_codes = None

                print("Prefix %s" % prefix)

                # If this asset is already rendered, move on.
                if finished_at in fields:
                    continue

                if started_at in fields:
                    # If we have started, we need to increment the retries
                    data["Rendering Retries"] = fields["Rendering Retries"] + 1
                else:
                    # If we have not started, we need to set the start time
                    data[started_at] = datetime.datetime.now().isoformat()

                unit_versions_airtable.update_by_field("Record ID", unit_version_id, data)

                if prefix == "Floor Plans":
                    settings_codes = const.FLOOR_PLANS_SETTINGS_CODES
                elif prefix == "Panos":
                    settings_codes = const.PANOS_SETTINGS_CODES
                elif prefix == "Screenshots":
                    settings_codes = fields["Rendering Settings Codes"].split(",")
                
                # Render section
                func = PREFIX_FUNCTIONS[prefix]
                if not func or not settings_codes:
                    print("%s doesn't have a rendering func..." % prefix)
                    continue

                # Render this section of assets
                for code in settings_codes:
                    download_rendering_setting(code)
                    func(unit_version, tmp_file_path, code);

                finished_data = {}
                finished_data[finished_at] = datetime.datetime.now().isoformat()
                # Set finished at
                unit_versions_airtable.update_by_field("Record ID", unit_version_id, finished_data)

            print("Done with %s!" % unit_name)

            # Remove tmp file when done
            os.remove(tmp_file_path)
                
        time.sleep(const.WAIT_DELAY)
    except Exception as e:
        print("Exception, restarting to try again...")
        print(e)
        traceback.print_exc()
        time.sleep(30)
        os.system("shutdown /r /t 1")
        # Make sure this is longer than the delay to restart.
        # We want to avoid restarting the loop.
        time.sleep(10)
