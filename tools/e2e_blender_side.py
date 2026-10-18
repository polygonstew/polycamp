"""Runs INSIDE Blender for tools/e2e.py: connects the add-on to a server, then plays a scripted "learner".
Usage (by e2e.py):  blender -b --python tools/e2e_blender_side.py -- http://127.0.0.1:8571 <seconds>
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "addon"))
import bpy

import polycamp_link as pl
from polycamp_link import commands, config, link

server, seconds = sys.argv[sys.argv.index("--") + 1], float(sys.argv[-1])
config.DEFAULT_SERVER = server
pl.register()
link.stop()
link.S.server = server
link.start()
t0 = time.time()
step = 0
script = [  # (seconds after connect, action)
    (4.0, lambda: setattr(bpy.data.objects["Cube"], "name", "Cubby") if "Cube" in bpy.data.objects else None),
    (6.0, lambda: bpy.ops.wm.save_as_mainfile(filepath="/tmp/polycamp-e2e.blend")),
]
conn_t = None
while time.time() - t0 < seconds:
    link.tick()
    if link.S.connected and conn_t is None:
        conn_t = time.time()
    if conn_t is not None and step < len(script) and time.time() - conn_t >= script[step][0]:
        script[step][1]()
        link.S.dirty = True
        step += 1
    time.sleep(0.1)
link.stop()
print("E2E_BLENDER_DONE connected=%s steps=%d" % (link.S.connected, step), flush=True)
