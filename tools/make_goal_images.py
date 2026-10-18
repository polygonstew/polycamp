"""Run INSIDE Blender:  blender -b --factory-startup --python tools/make_goal_images.py -- [name ...]

Renders the reference pictures used by the `:::goal img=...` blocks into content/img/, from the lessons' own
solution scripts and the content library (Cycles, CPU, small and denoised). No names = render them all.
"""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("POLYCAMP_DATA", tempfile.mkdtemp(prefix="pc-goal-"))
sys.path.insert(0, os.path.join(ROOT, "addon"))
sys.path.insert(0, os.path.join(ROOT, "server"))
import bpy

import polycamp_link as pl
from polycamp_link import commands, link

import lessons

pl.register()
link.stop()
content = lessons.Content()
OUT = os.path.join(ROOT, "content", "img")
STUDIO = """
bpy.context.scene.collection  # noqa
bm = bmesh.new()
box_at(bm, (14, 14, 0.2), (0, 0, -0.1))
kit.mesh_object('Studio_Floor', bm).data.materials.append(kit.pbr('Studio_Floor', (0.30, 0.31, 0.34, 1), roughness=0.55))
studio_world()
studio_lights(centre=(0, 0, %(cz)s), size=%(size)s)
auto_camera([o for o in bpy.data.objects if %(sel)s], lens=50.0, margin=1.45)
"""


def lesson_script(lid, task=None):
    les = content.lessons[lid]
    start = content.scene_script(les) if les.scene.startswith("starter:") else None
    return start, les


def run(code, label):
    r = commands.run({"id": 1, "cmd": "run_script", "args": {"code": code, "label": label}})
    if not r["ok"]:
        raise SystemExit("script failed (%s): %s" % (label, r["msg"]))


def build_mug():
    les = content.lessons["boss-mug"]
    run(content.lib_text() + "\nkit.default_scene()\n" + les.solve, "mug")
    run(content.lib_text() + STUDIO % {"cz": "0.5", "size": "0.7", "sel": "o.name == 'Mug'"}, "mug-studio")


def build_lantern():
    les = content.lessons["boss-lantern"]
    run(content.solve_script(les), "lantern")
    run(content.lib_text() + STUDIO % {"cz": "0.35", "size": "0.35", "sel": "o.type == 'MESH' and o.name.startswith('Lantern')"}, "lantern-studio")


def build_blockout():
    run(content.lib_text() + "\nbuild_diorama(mats=False, lights=True, camera=True, world=True, cpu=None)\n", "blockout")


def build_materials():
    run(content.lib_text() + "\nbuild_diorama(mats=True, lights=False, camera=False, world=False, cpu=None)\nstudio_world('#5a6a8a', '#1a1d26')\nstudio_lights(centre=(0, 0, 1.5), size=3.0)\nauto_camera([o for o in bpy.data.objects if o.type == 'MESH'], direction=(1.0, -1.25, 0.65), lens=45.0, margin=0.95)\n", "materials")


def build_props():
    les = content.lessons["boss-textured"]
    start = content.scene_script(les)
    run(start, "props")
    run(content.lib_text() + """
mats = {'Barrel': mat_wood('Barrel_Oak', '#9a6a3c', '#4a2d16', 8.0), 'Crate': mat_wood('Crate_Pine', '#c8a46a', '#7a5a30', 5.0, 0.7),
        'Plank': mat_wood('Plank_Dark', '#4a3020', '#1e120a', 9.0, 0.5)}
for n, m in mats.items():
    ob = bpy.data.objects[n]
    ob.data.materials.clear()
    ob.data.materials.append(m)
""" + STUDIO % {"cz": "0.7", "size": "1.2", "sel": "o.name in ('Barrel', 'Crate', 'Plank')"}, "props-studio")


def build_final():
    run(content.lib_text() + "\nbuild_diorama(cpu='standard')\nadd_glare(1.0)\n", "final")


JOBS = {
    "mug": (build_mug, 640, 32), "lantern": (build_lantern, 640, 32), "diorama-blockout": (build_blockout, 800, 24),
    "diorama-materials": (build_materials, 800, 32), "prop-set": (build_props, 800, 32), "diorama-final": (build_final, 960, 64),
}
want = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(JOBS)
os.makedirs(OUT, exist_ok=True)
for name in want:
    build, width, spp = JOBS[name]
    t0 = time.time()
    run('kit.wipe()\nkit.reset_scene_settings()\nkit.make_world()', 'reset')
    build()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "CPU", spp, True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = width, width * 9 // 16, 100
    sc.render.filepath = os.path.join(OUT, name + ".png")
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("GOAL %s %.1fs" % (name, time.time() - t0), flush=True)
