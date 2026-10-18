"""commands.py - things the Polycamp app can ask Blender to do. Each handler takes an args dict and
returns a dict (optionally with "_msg"). Errors become a failed result the app can show.

Handlers run on Blender's main thread (called from link.tick), so they may touch bpy freely.
"""
import math
import os
import time
import traceback

import bmesh
import bpy
import mathutils

from . import compat, matkit, scenekit

REG = {}
BACKUPS = os.path.join(os.path.expanduser("~"), ".polycamp", "backups")


def reg(name):
    def deco(fn):
        REG[name] = fn
        return fn
    return deco


def run(cmd):
    """Execute one command dict {id, cmd, args}; always returns a result dict."""
    cid, name, args = cmd.get("id"), cmd.get("cmd"), cmd.get("args") or {}
    fn = REG.get(name)
    if fn is None:
        return {"id": cid, "ok": False, "msg": "unknown command: %s" % name}
    try:
        data = fn(args) or {}
        return {"id": cid, "ok": True, "msg": data.pop("_msg", "ok"), "data": data}
    except Exception as e:
        traceback.print_exc()
        return {"id": cid, "ok": False, "msg": str(e)[:300]}


def _prefs():
    from . import link
    return link.prefs()


def _active_obj():
    return bpy.context.view_layer.objects.active


def _ctx_override(kind="VIEW_3D"):
    found = compat.find_area(kind)
    if not found:
        raise RuntimeError("No %s editor is open." % kind)
    win, area, region = found
    return bpy.context.temp_override(window=win, area=area, region=region)


def backup_if_needed(reason="before lesson"):
    """Never lose the learner's work: save a copy of an unsaved/dirty session before wiping it."""
    if not bpy.data.is_dirty:
        return None
    os.makedirs(BACKUPS, exist_ok=True)
    path = os.path.join(BACKUPS, time.strftime("%Y%m%d-%H%M%S") + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    old = sorted(os.listdir(BACKUPS))
    for f in old[:-15]:
        try:
            os.remove(os.path.join(BACKUPS, f))
        except OSError:
            pass
    return path


# ------------------------------------------------------------------ scene

@reg("ping")
def _ping(a):
    return {"pong": True, "blender": bpy.app.version_string}


@reg("new_scene")
def _new_scene(a):
    kept = backup_if_needed() if a.get("backup", True) else None
    if a.get("kind") == "empty":
        scenekit.wipe()
        scenekit.reset_scene_settings()
        scenekit.make_world()
    else:
        scenekit.default_scene()
    return {"_msg": "Fresh scene ready." + (" Your previous work was saved to %s" % kept if kept else ""),
            "backup": kept}


@reg("run_script")
def _run_script(a):
    p = _prefs()
    if p is not None and not p.allow_scripts:
        raise RuntimeError("Lesson scripts are switched off in the Polycamp Link preferences.")
    kept = backup_if_needed() if a.get("backup") else None
    ns = {"bpy": bpy, "bmesh": bmesh, "math": math, "mathutils": mathutils, "Vector": mathutils.Vector,
          "Matrix": mathutils.Matrix, "Euler": mathutils.Euler, "kit": scenekit, "matkit": matkit,
          "compat": compat, "__name__": "polycamp_script"}
    exec(compile(a["code"], "<polycamp:%s>" % a.get("label", "script"), "exec"), ns)
    return {"_msg": "Script '%s' ran." % a.get("label", "script"), "backup": kept}


@reg("select")
def _select(a):
    names = a.get("names", [])
    objs = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
    scenekit.select_only(*objs)
    if a.get("active") in bpy.data.objects:
        bpy.context.view_layer.objects.active = bpy.data.objects[a["active"]]
    if a.get("frame") and objs:
        try:
            with _ctx_override():
                bpy.ops.view3d.view_selected()
        except Exception:
            pass
    return {"selected": [o.name for o in objs]}


@reg("set_mode")
def _set_mode(a):
    ob = _active_obj()
    if ob is None:
        raise RuntimeError("Select an object first.")
    with bpy.context.temp_override(active_object=ob, object=ob):
        bpy.ops.object.mode_set(mode=a.get("mode", "OBJECT"))
    return {"mode": ob.mode}


@reg("set_shading")
def _set_shading(a):
    win, area, _ = compat.find_area("VIEW_3D") or (None, None, None)
    if area is None:
        raise RuntimeError("No 3D viewport is open.")
    area.spaces.active.shading.type = a.get("type", "SOLID")
    return {}


@reg("frame")
def _frame(a):
    with _ctx_override():
        if a.get("all"):
            bpy.ops.view3d.view_all()
        else:
            bpy.ops.view3d.view_selected()
    return {}


@reg("frame_set")
def _frame_set(a):
    bpy.context.scene.frame_set(int(a.get("frame", 1)))
    return {}


# ------------------------------------------------------------------ textures & materials

def _fetch_images(files):
    from . import link
    out = {}
    for kind, spath in files.items():
        if not spath:
            continue
        dest = os.path.join(link.CACHE, "tex", os.path.basename(spath))
        out[kind] = link.download(spath, dest)
    return out


@reg("import_image")
def _import_image(a):
    paths = _fetch_images({"img": a["path"]})
    img = bpy.data.images.load(paths["img"], check_existing=True)
    img.reload()
    return {"image": img.name, "_msg": "Loaded image %s" % img.name}


@reg("make_material")
def _make_material(a):
    paths = _fetch_images(a.get("files", {}))
    mat = matkit.build_pbr(a.get("name", "Polycamp_Material"), paths, tiling=tuple(a.get("tiling", (1, 1))),
                           normal_strength=a.get("normal_strength", 1.0), bump_strength=a.get("bump_strength", 0.2))
    target = a.get("apply", "selected")
    objs = []
    if target == "selected":
        objs = [o for o in bpy.context.view_layer.objects if o.select_get()]
    elif target == "active" and _active_obj():
        objs = [_active_obj()]
    elif target in bpy.data.objects:
        objs = [bpy.data.objects[target]]
    matkit.assign(mat, objs)
    return {"material": mat.name, "applied_to": [o.name for o in objs],
            "_msg": "Material '%s' built (%d maps) and applied to %d object(s)." % (mat.name, len(paths), len(objs))}


@reg("uv_layout")
def _uv_layout(a):
    from . import link, uvlayout
    ob = bpy.data.objects.get(a.get("object", "")) or _active_obj()
    if ob is None:
        raise RuntimeError("Select a mesh object first.")
    os.makedirs(link.CACHE, exist_ok=True)
    name = "uv-%s.png" % ob.name.replace(" ", "_")
    path = os.path.join(link.CACHE, name)
    stats = uvlayout.render_layout(ob, path, size=int(a.get("size", 1024)))
    link.queue_upload("uvlayout", name, path, stats)
    return {"_msg": "UV layout of %s sent." % ob.name, **stats}


# ------------------------------------------------------------------ render, prefs, files

@reg("cpu_preset")
def _cpu_preset(a):
    info = matkit.cpu_preset(bpy.context.scene, a.get("quality", "standard"))
    return {"_msg": "CPU-friendly Cycles preset applied (%s)." % info["quality"], **info}


@reg("send_render")
def _send_render(a):
    from . import link
    return {"name": link.send_render_result(), "_msg": "Render sent to the Trophy Room."}


PREF_SETTERS = {
    "emulate_numpad": lambda p, v: setattr(p.inputs, "use_emulate_numpad", bool(v)),
    "emulate_3button": lambda p, v: setattr(p.inputs, "use_mouse_emulate_3_button", bool(v)),
    "undo_steps": lambda p, v: setattr(p.edit, "undo_steps", int(v)),
    "autosave": lambda p, v: setattr(p.filepaths, "use_auto_save_temporary_files", bool(v)),
    "autosave_minutes": lambda p, v: setattr(p.filepaths, "auto_save_time", int(v)),
}


@reg("set_pref")
def _set_pref(a):
    fn = PREF_SETTERS.get(a.get("key"))
    if fn is None:
        raise RuntimeError("That preference can't be set from the app.")
    fn(bpy.context.preferences, a.get("value"))
    return {}


@reg("save_file")
def _save_file(a):
    path = a.get("path") or bpy.data.filepath
    if not path:
        os.makedirs(os.path.join(os.path.expanduser("~"), ".polycamp", "projects"), exist_ok=True)
        path = os.path.join(os.path.expanduser("~"), ".polycamp", "projects", a.get("name", "polycamp-project") + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return {"path": path, "_msg": "Saved %s" % path}


@reg("export_model")
def _export_model(a):
    from . import link
    os.makedirs(link.CACHE, exist_ok=True)
    name = a.get("name", "model")
    path = os.path.join(link.CACHE, name + ".glb")
    kw = dict(filepath=path, export_format="GLB", use_selection=bool(a.get("selected_only", False)))
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop("use_selection")
        bpy.ops.export_scene.gltf(**kw)
    link.queue_upload("model", name + ".glb", path, {"selected_only": kw.get("use_selection", False)})
    return {"_msg": "Exported %s.glb" % name}


@reg("toast")
def _toast(a):
    from . import link
    link.S.toast = (a.get("text", ""), time.time())
    return {}


@reg("screenshot")
def _screenshot(a):
    from . import link
    os.makedirs(link.CACHE, exist_ok=True)
    name = time.strftime("shot-%Y%m%d-%H%M%S.png")
    path = os.path.join(link.CACHE, name)
    with _ctx_override():
        bpy.ops.screen.screenshot_area(filepath=path)
    link.queue_upload("shot", name, path, {})
    return {"_msg": "Screenshot sent."}
