"""Runs INSIDE a GUI Blender for tools/gui_e2e.py: links the add-on to a test server and reports what arrives.

It prints a CUE_SEEN line whenever the set of active highlights changes, takes a screenshot when the driver creates
<out>/shot, and presses the add-on's Narration "next" button when the driver creates <out>/press.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "addon"))
import bpy

import polycamp_link as pl
from polycamp_link import config, cues, link

server, out = sys.argv[sys.argv.index("--") + 1:][:2]
config.DEFAULT_SERVER = server
pl.register()
link.stop()
link.S.server = server
link.start()
last = [None]


def take(name):
    f = os.path.join(out, name)
    if os.path.exists(f):
        os.remove(f)
        return True
    return False


def watch():
    sig = json.dumps(cues.active(), sort_keys=True)
    if sig != last[0]:
        last[0] = sig
        print("CUE_SEEN", sig, flush=True)
    if take("shot"):
        if bpy.app.version >= (4, 0, 0):
            bpy.ops.screen.screenshot(filepath=os.path.join(out, "blender.png"))
        else:
            import subprocess
            subprocess.run(["import", "-window", "root", os.path.join(out, "blender.png")])
        print("SHOT_TAKEN", flush=True)
    if take("press"):
        print("PRESSED", bpy.ops.polycamp.voice(action="next"), flush=True)
    if take("quit"):
        pl.unregister()
        bpy.ops.wm.quit_blender()
        return None
    return 0.25


bpy.app.timers.register(watch, first_interval=1.0, persistent=True)
