import pywinauto
import time
import uuid
import os

import util
import const

def type_keys(window, key):
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

# Small scripts please :)
def ruby_console_exec(app, sketchup_window, script):
    type_keys(sketchup_window, const.OPEN_RUBY_CONSOLE_KEY)
    ruby_console_window = app.window(title_re=".*?Ruby Console.*?")

    ruby_console_window[1].set_text(script)
    type_keys(ruby_console_window, const.ENTER_KEY)
    time.sleep(5)

    return ruby_console_window["Edit2"].texts()[-2].strip()

def set_settings_code(app, sketchup_window, code):
    script = "FinishVisionVR::RenderingPlugin.set_settings_code('%s')" % code
    return ruby_console_exec(app, sketchup_window, script)

def set_pano_name(app, sketchup_window, name):
    script = "FinishVisionVR::RenderingPlugin.set_pano_name('%s')" % name
    return ruby_console_exec(app, sketchup_window, script)

def get_num_of_pages(app, sketchup_window):
    script = "Sketchup.active_model.pages.length"
    return int(ruby_console_exec(app, sketchup_window, script))
   
def start_rendering_programs(file_path):
    print(file_path)

    print("Starting SketchUp...")
    command = const.SKETCHUP_EXE + " \"" + file_path + "\""
    #For testing
    #app = pywinauto.Application().connect(path=const.SKETCHUP_EXE)
    app = pywinauto.Application().start(command)
    time.sleep(30)

    # Try to press enter if there is read only warning
    try:
        window = app.top_window()
        type_keys(window, const.ENTER_KEY)
    except:
        pass

    time.sleep(const.START_SKETCHUP_DELAY-30)

    window = app.window(title_re=".+ - SketchUp Pro 2019")
    window.move_window(x=None, y=None, width=1920, height=1080, repaint=True)
    print("SketchUp ready...")

    print("Starting Enscape...")
    type_keys(window, const.START_ENSCAPE_KEY)
    time.sleep(90)

    enscape_window = app.window(title_re=".*?Enscape.*?")
    enscape_window.move_window(x=None, y=None, width=1920, height=1080, repaint=True)
    print("SketchUp ready...")

    return { "App": app, "SketchUp": window, "Enscape": enscape_window }

def find_rendering_programs():
    app = pywinauto.Application().connect(path=const.SKETCHUP_EXE)

    window = app.window(title_re=".+ - SketchUp Pro 2019")
    window.move_window(x=None, y=None, width=1920, height=1080, repaint=True)

    enscape_window = app.window(title_re=".*Enscape.*")
    enscape_window.move_window(x=None, y=None, width=1920, height=1080, repaint=True)

    return { "App": app, "SketchUp": window, "Enscape": enscape_window }

def close_rendering_programs(app, sketchup_window):
    app.kill()
    #type_keys(sketchup_window, const.CLOSE_KEY)
    #time.sleep(1)
    #type_keys(sketchup_window.top_window(), const.TAB_KEY)
    #time.sleep(1)
    #type_keys(sketchup_window, const.ENTER_KEY)

def get_all_pano_files():
    files = os.listdir(const.ENSCAPE_PANO_DIR)
    paths = [os.path.join(const.ENSCAPE_PANO_DIR, basename) for basename in files]
    return paths

def get_all_screenshot_files():
    files = os.listdir(const.FP_OUTPUT_DIR)
    paths = [os.path.join(const.FP_OUTPUT_DIR, basename) for basename in files]
    return paths

def remove_all_screenshot_files():
    files = os.listdir(const.FP_OUTPUT_DIR)
    for basename in files:
        path = os.path.join(const.FP_OUTPUT_DIR, basename)
        os.remove(path)

def remove_all_pano_files():
    files = os.listdir(const.ENSCAPE_PANO_DIR)
    for basename in files:
        path = os.path.join(const.ENSCAPE_PANO_DIR, basename)
        os.remove(path)
