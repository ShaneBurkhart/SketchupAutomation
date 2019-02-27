import pywinauto
import time

SKETCHUP_EXE = "C:\\Program Files\\SketchUp\\SketchUp 2018\\SketchUp.exe"

app = pywinauto.Application().connect(path=SKETCHUP_EXE)
window = app.window(title_re=".*SketchUp Pro 2018")

window.type_keys("+^1")
time.sleep(1)
app.EnscapeSettings.type_keys("{TAB}")
time.sleep(1)
app.EnscapeSettings.type_keys("{DOWN}")
time.sleep(1)
app.EnscapeSettings.type_keys("{UP}")
app.EnscapeSettings.close()

