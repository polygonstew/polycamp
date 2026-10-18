"""Run INSIDE Blender (any version):  blender -b --factory-startup --python tools/addon_selftest.py
Exercises the add-on's snapshot, scene kit, material builder, UV layout and commands. Prints PASS/FAIL lines.
"""
import math
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "addon"))

import bmesh
import bpy

import polycamp_link as pl
from polycamp_link import commands, compat, link, matkit, scenekit, snapshot, uvlayout

FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""), flush=True)
    if not cond:
        FAILS.append(name)


def obj(snap, name):
    return next((o for o in snap["objects"] if o["name"] == name), None)


print("== Blender", bpy.app.version_string)
pl.register()
link.stop()      # no network in the self-test

# --- fresh scene via command
r = commands.run({"id": 1, "cmd": "new_scene", "args": {"backup": False}})
check("new_scene ok", r["ok"], r)
s = snapshot.build()
check("snapshot no errors", not s["errors"], s["errors"])
check("default objects", {o["name"] for o in s["objects"]} == {"Cube", "Light", "Camera"})
check("cube is 2m", obj(s, "Cube")["dims"] == [2.0, 2.0, 2.0])
check("cube verts", obj(s, "Cube")["verts"] == 8 and obj(s, "Cube")["faces"] == 6)
check("cube material principled", s["materials"][0]["principled"] and s["materials"][0].get("roughness") == 0.5)
check("camera is scene camera", obj(s, "Camera")["camera"]["is_scene_camera"])
check("light info", obj(s, "Light")["light"]["kind"] == "POINT")

# --- modifiers
cube = bpy.data.objects["Cube"]
m = cube.modifiers.new("Bevel", "BEVEL")
m.width, m.segments = 0.1, 3
m2 = cube.modifiers.new("Subdivision", "SUBSURF")
m2.levels = 2
s = snapshot.build()
c = obj(s, "Cube")
check("modifier types", [x["type"] for x in c["mods"]] == ["BEVEL", "SUBSURF"], c["mods"])
check("bevel params", c["mods"][0]["p"].get("segments") == 3 and abs(c["mods"][0]["p"].get("width") - 0.1) < 1e-6)
check("evaluated verts grow", c["verts_eval"] > 8, c["verts_eval"])

# --- scenekit primitives (all three version families)
bm = bmesh.new()
scenekit.add_box(bm, (1, 2, 3))
scenekit.add_cylinder(bm, 0.5, 2, 12, center=(3, 0, 0))
scenekit.add_cylinder(bm, 0.5, 1, 12, center=(5, 0, 0), radius2=0.0)
scenekit.add_sphere(bm, 0.5, 12, 8, center=(7, 0, 0))
scenekit.add_icosphere(bm, 0.5, 2, center=(9, 0, 0))
scenekit.add_grid(bm, 4.0, 4)
ob = scenekit.mesh_object("Kit", bm, smooth=True)
scenekit.set_smooth(ob, 40)
check("kit object made", ob.name == "Kit" and len(ob.data.vertices) > 100, len(ob.data.vertices))
mat = scenekit.pbr("Glow", (1, 0.5, 0.1, 1), roughness=0.3, emission=(1, 0.5, 0.1), emission_strength=5)
ob.data.materials.append(mat)
scenekit.add_light("AREA", "Key", (3, -3, 4), 200, size=2.0)
scenekit.add_camera("Cam2", (0, -8, 3), (0, 0, 1), make_active=False)
s = snapshot.build()
g = next(x for x in s["materials"] if x["name"] == "Glow")
check("emission strength read", g.get("emission_strength") == 5.0, g)
check("area light", obj(s, "Key")["light"]["kind"] == "AREA")
check("sharp edges after set_smooth(angle)", obj(s, "Kit").get("sharp_edges", 0) > 0 or compat.VER < (4, 1, 0))

# --- edit mode stats
scenekit.select_only(bpy.data.objects["Cube"])
bpy.ops.object.mode_set(mode="EDIT")
s = snapshot.build()
c = obj(s, "Cube")
check("edit mode flagged", s["mode"].startswith("EDIT") and c.get("in_edit"), s["mode"])
check("edit sel counts", "sel_verts" in c, c.keys())
bpy.ops.object.mode_set(mode="OBJECT")

# --- animation
cube.location = (0, 0, 0)
cube.keyframe_insert("location", frame=1)
cube.location = (0, 0, 4)
cube.keyframe_insert("location", frame=24)
s = snapshot.build()
a = obj(s, "Cube")["anim"]
check("keyframes counted", a["keys"] == 6 and a["frames"] == [1.0, 24.0], a)
check("anim path", "location" in a["paths"])

# --- UV layout picture
tmp = tempfile.mkdtemp(prefix="pcself")
r = commands.run({"id": 2, "cmd": "uv_layout", "args": {"object": "Cube", "size": 256}})
check("uv_layout cmd (no network: upload queued)", r["ok"], r)
p = os.path.join(link.CACHE, "uv-Cube.png")
check("uv png written", os.path.exists(p) and os.path.getsize(p) > 500)
st = uvlayout.render_layout(bpy.data.objects["Cube"], os.path.join(tmp, "uv.png"), 128)
check("uv coverage sane", 0.2 < st["coverage"] < 0.9, st)

# --- material from maps
for kind in ("base_color", "normal", "height", "roughness"):
    im = bpy.data.images.new("t_" + kind, 8, 8)
    im.filepath_raw = os.path.join(tmp, kind + ".png")
    im.file_format = "PNG"
    im.save()
mat = matkit.build_pbr("TexTest", {k: os.path.join(tmp, k + ".png") for k in ("base_color", "normal", "height", "roughness")})
matkit.assign(mat, [bpy.data.objects["Cube"]])
s = snapshot.build()
tm = next(x for x in s["materials"] if x["name"] == "TexTest")
check("pbr chain base_color has image", "TEX_IMAGE" in tm["chain"].get("base_color", []), tm.get("chain"))
check("pbr chain normal map", "NORMAL_MAP" in tm["chain"].get("normal", []), tm.get("chain"))
check("pbr chain bump", "BUMP" in tm["chain"].get("normal", []), tm.get("chain"))

# --- cpu preset
commands.run({"id": 3, "cmd": "cpu_preset", "args": {"quality": "draft"}})
s = snapshot.build()
check("cpu preset engine", s["render"]["engine"] == "CYCLES" and s["render"]["cy_device"] == "CPU")
check("cpu preset denoise", s["render"]["cy_use_denoising"] and s["render"]["res_x"] == 960)

# --- operator tracking + render handlers (Workbench so it is instant)
link.count_op("mesh.loopcut_slide", 2)
s = link._snapshot()
check("op counts in snapshot", s["ops"].get("mesh.loopcut_slide") == 2)
sc = bpy.context.scene
sc.render.engine = "CYCLES"          # 3.3 Workbench needs a GL display even with -b; Cycles/CPU does not
sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "CPU", 1, False
sc.render.resolution_x = sc.render.resolution_y = 64
sc.render.resolution_percentage = 100
bpy.ops.render.render(write_still=False)
check("render handler recorded", link.S.render_info.get("ok") and link.S.render_info.get("frames") == 1, link.S.render_info)

# --- run_script command
code = "o = kit.add_box.__name__\nbpy.context.scene['pc_test'] = o"
r = commands.run({"id": 4, "cmd": "run_script", "args": {"code": code, "label": "t"}})
check("run_script", r["ok"] and bpy.context.scene.get("pc_test") == "add_box", r)

# --- icons used by the panel exist on this version
try:
    icons = {i.identifier for i in bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items}
    need = {"CHECKMARK", "ERROR", "BOOKMARKS", "BLANK1", "CHECKBOX_HLT", "CHECKBOX_DEHLT", "QUESTION", "FILE_NEW",
            "URL", "SETTINGS", "RENDER_STILL", "WINDOW", "FILE_REFRESH"}
    check("panel icons exist", need <= icons, sorted(need - icons))
except Exception as e:
    print("SKIP icon check", e)

pl.unregister()
print("RESULT", "FAIL %d: %s" % (len(FAILS), FAILS) if FAILS else "ALL PASS", bpy.app.version_string)
