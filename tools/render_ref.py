"""Run INSIDE Blender:  blender -b --factory-startup --python tools/render_ref.py -- <out.png> [res_x] [samples] [part,part,...|all]

Builds (part of) the diorama with the content library and renders it with Cycles on the CPU. Used to make the
reference images in content/img and to eyeball the library after changes.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("POLYCAMP_DATA", "/tmp/pc-ref-data")
sys.path.insert(0, os.path.join(ROOT, "addon"))
sys.path.insert(0, os.path.join(ROOT, "server"))
import bpy

import polycamp_link as pl
from polycamp_link import commands, link

import lessons

pl.register()
link.stop()
a = sys.argv[sys.argv.index("--") + 1:]
out, rx, spp = a[0], int(a[1]) if len(a) > 1 else 640, int(a[2]) if len(a) > 2 else 24
parts = a[3].split(",") if len(a) > 3 and a[3] != "all" else None
c = lessons.Content()
code = c.lib_text() + "\nbuild_diorama(%scpu=None)\n" % ("parts=%r, " % (tuple(parts),) if parts else "")
t0 = time.time()
r = commands.run({"id": 1, "cmd": "run_script", "args": {"code": code, "label": "ref"}})
print("build:", r, "%.1fs" % (time.time() - t0), flush=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "CPU", spp, True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = rx, rx * 9 // 16, 100
sc.render.filepath = out
sc.render.image_settings.file_format = "PNG"
t0 = time.time()
bpy.ops.render.render(write_still=True)
print("rendered %s in %.1fs" % (out, time.time() - t0), flush=True)
