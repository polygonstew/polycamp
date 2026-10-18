"""snapshot.py - read the whole Blender session into one JSON-able dict.

Read-only and main-thread only. The server evaluates lesson checks against this dict, so the
shape here is the contract (documented in docs/SNAPSHOT.md). Every section is wrapped so one
failing section never loses the rest; failures are listed in snap["errors"].
"""
import math
import platform

import bpy
from mathutils import Vector

from . import compat

MAX_OBJECTS = 400
MESH_STAT_LIMIT = 400_000     # skip numpy stats above this many loops
EDIT_SEL_LIMIT = 60_000


def _r(v, n=4):
    return round(float(v), n)


def _vec(v, n=4):
    return [_r(x, n) for x in v]


def _deg(v):
    return [_r(math.degrees(x), 2) for x in v]


def _simple_props(rna_owner, limit=48):
    """Dump simple (number/bool/enum/string/small-array/pointer-name) properties of an RNA struct."""
    out = {}
    for p in rna_owner.bl_rna.properties:
        pid = p.identifier
        if pid in ("rna_type", "name", "type", "bl_idname") or len(out) >= limit:
            continue
        try:
            val = getattr(rna_owner, pid)
        except Exception:
            continue
        t = p.type
        if t in ("BOOLEAN", "INT", "FLOAT"):
            if getattr(p, "array_length", 0):
                try:
                    val = [(_r(x) if t == "FLOAT" else (bool(x) if t == "BOOLEAN" else int(x))) for x in val][:4]
                except Exception:
                    continue
            elif t == "FLOAT":
                val = _r(val)
            elif t == "BOOLEAN":
                val = bool(val)
            else:
                val = int(val)
            out[pid] = val
        elif t == "ENUM":
            out[pid] = sorted(val) if isinstance(val, set) else val
        elif t == "STRING":
            out[pid] = str(val)[:80]
        elif t == "POINTER" and val is not None and hasattr(val, "name"):
            out[pid] = val.name
    return out


# ---------------------------------------------------------------- meshes

def _np():
    import numpy as np
    return np


def _mesh_stats(me):
    """Counts + topology facts from a non-edit-mode Mesh, via numpy for speed."""
    np = _np()
    nv, ne, nf = len(me.vertices), len(me.edges), len(me.polygons)
    d = {"verts": nv, "edges": ne, "faces": nf}
    if len(me.loops) > MESH_STAT_LIMIT or nf == 0:
        d.update(tris=0, quads=0, ngons=0)
        return d
    try:
        lt = np.empty(nf, dtype=np.int32)
        me.polygons.foreach_get("loop_total", lt)
    except Exception:
        lt = np.array([len(p.vertices) for p in me.polygons], dtype=np.int32)
    d["tris"] = int((lt - 2).clip(0).sum())
    d["n3"], d["quads"], d["ngons"] = int((lt == 3).sum()), int((lt == 4).sum()), int((lt > 4).sum())
    try:
        sm = np.empty(nf, dtype=np.bool_)
        me.polygons.foreach_get("use_smooth", sm)
        d["smooth_faces"] = int(sm.sum())
        d["flat_faces"] = int(nf - sm.sum())
    except Exception:
        pass
    try:
        a = np.empty(ne, dtype=np.bool_)
        me.edges.foreach_get("use_seam", a)
        d["seams"] = int(a.sum())
    except Exception:
        d["seams"] = 0
    try:
        a = np.empty(ne, dtype=np.bool_)
        me.edges.foreach_get("use_edge_sharp", a)
        d["sharp_edges"] = int(a.sum())
    except Exception:
        d["sharp_edges"] = 0
    try:
        ei = np.empty(len(me.loops), dtype=np.int32)
        me.loops.foreach_get("edge_index", ei)
        use = np.bincount(ei, minlength=ne)
        d["boundary_edges"] = int((use == 1).sum())
        d["nonmanifold_edges"] = int((use > 2).sum())
        d["loose_edges"] = int((use == 0).sum())
    except Exception:
        pass
    return d


def _volume(me):
    """Enclosed volume of a closed mesh (m^3), through bmesh. Used by 'is it really hollow?' style checks."""
    import bmesh
    bm = bmesh.new()
    try:
        bm.from_mesh(me)
        return abs(bm.calc_volume(signed=True))
    finally:
        bm.free()


def _uv_stats(me):
    """UV layout facts for the active UV map: area used in 0..1 and how much lies outside."""
    np = _np()
    layer = me.uv_layers.active
    if layer is None or len(me.loops) > MESH_STAT_LIMIT or len(me.polygons) == 0:
        return {}
    n = len(me.loops)
    uv = np.empty(n * 2, dtype=np.float32)
    layer.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    start = np.empty(len(me.polygons), dtype=np.int32)
    total = np.empty(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    nxt = np.arange(n, dtype=np.int32) + 1
    nxt[start + total - 1] = start
    cross = uv[:, 0] * uv[nxt, 1] - uv[nxt, 0] * uv[:, 1]
    poly_area = 0.5 * np.add.reduceat(cross, start) if len(start) else np.zeros(0)
    area = float(np.abs(poly_area).sum())
    oob = float(((uv < -0.0001) | (uv > 1.0001)).any(axis=1).mean())
    return {
        "uv_area": _r(area),
        "uv_oob": _r(oob),
        "uv_bounds": _vec([uv[:, 0].min(), uv[:, 1].min(), uv[:, 0].max(), uv[:, 1].max()]),
    }


def _edit_stats(obj):
    import bmesh
    bm = bmesh.from_edit_mesh(obj.data)
    d = {"verts": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces),
         "select_mode": sorted(bm.select_mode)}
    if len(bm.verts) + len(bm.faces) < EDIT_SEL_LIMIT:
        d["sel_verts"] = sum(1 for v in bm.verts if v.select)
        d["sel_edges"] = sum(1 for e in bm.edges if e.select)
        d["sel_faces"] = sum(1 for f in bm.faces if f.select)
        d["quads"] = sum(1 for f in bm.faces if len(f.verts) == 4)
        d["tris"] = sum(1 for f in bm.faces if len(f.verts) == 3)
        d["ngons"] = sum(1 for f in bm.faces if len(f.verts) > 4)
        d["seams"] = sum(1 for e in bm.edges if e.seam)
    return d


# ---------------------------------------------------------------- objects

def _anim(owner, prefix=""):
    """Keyframe facts for an ID with animation_data."""
    ad = getattr(owner, "animation_data", None)
    out = {"keys": 0, "paths": {}, "frames": [], "interp": [], "fmods": [], "drivers": 0, "action": None}
    if ad is None:
        return out
    out["drivers"] = len(ad.drivers)
    act = ad.action
    if act is None:
        return out
    out["action"] = act.name
    frames, interp, fmods = set(), set(), set()
    for fc in compat.iter_fcurves(act, ad):
        path = prefix + fc.data_path
        out["paths"][path] = out["paths"].get(path, 0) + len(fc.keyframe_points)
        out["keys"] += len(fc.keyframe_points)
        for kp in fc.keyframe_points:
            frames.add(round(kp.co[0], 2))
            interp.add(kp.interpolation)
        for m in fc.modifiers:
            fmods.add(m.type)
    out["frames"] = sorted(frames)[:120]
    out["interp"] = sorted(interp)
    out["fmods"] = sorted(fmods)
    return out


def _merge_anim(a, b):
    a["keys"] += b["keys"]
    for k, v in b["paths"].items():
        a["paths"][k] = a["paths"].get(k, 0) + v
    a["frames"] = sorted(set(a["frames"]) | set(b["frames"]))[:120]
    a["interp"] = sorted(set(a["interp"]) | set(b["interp"]))
    a["fmods"] = sorted(set(a["fmods"]) | set(b["fmods"]))
    a["drivers"] += b["drivers"]
    a["action"] = a["action"] or b["action"]


def _light(data):
    d = {"kind": data.type, "energy": _r(data.energy, 3), "color": _vec(data.color, 3),
         "shadow": bool(getattr(data, "use_shadow", True))}
    if data.type == "AREA":
        d["shape"] = data.shape
        d["size"] = _r(data.size, 3)
        d["size_y"] = _r(getattr(data, "size_y", data.size), 3)
    elif data.type == "SUN":
        d["angle_deg"] = _r(math.degrees(data.angle), 3)
    else:
        d["radius"] = _r(getattr(data, "shadow_soft_size", 0), 3)
    if data.type == "SPOT":
        d["spot_deg"] = _r(math.degrees(data.spot_size), 2)
        d["spot_blend"] = _r(data.spot_blend, 3)
    return d


def _camera(obj, scene):
    c = obj.data
    d = {"lens": _r(c.lens, 2), "sensor": _r(c.sensor_width, 2), "kind": c.type,
         "clip_start": _r(c.clip_start, 4), "clip_end": _r(c.clip_end, 2),
         "is_scene_camera": scene.camera is obj, "shift_x": _r(c.shift_x, 3), "shift_y": _r(c.shift_y, 3),
         "ortho_scale": _r(c.ortho_scale, 3)}
    dof = c.dof
    d["dof"] = bool(dof.use_dof)
    d["focus_object"] = dof.focus_object.name if dof.focus_object else None
    d["focus_distance"] = _r(dof.focus_distance, 3)
    d["fstop"] = _r(dof.aperture_fstop, 2)
    return d


def _object(obj, scene, view_layer, deps, active, sel_names):
    d = {
        "name": obj.name, "type": obj.type, "data": obj.data.name if obj.data else None,
        "mode": obj.mode,
        "loc": _vec(obj.location), "rot": _deg(obj.rotation_euler), "scale": _vec(obj.scale),
        "dims": _vec(obj.dimensions),
        "parent": obj.parent.name if obj.parent else None,
        "children": len(obj.children),
        "collections": [c.name for c in obj.users_collection],
        "sel": obj.name in sel_names, "active": obj is active,
        "hide": bool(obj.hide_viewport), "hide_render": bool(obj.hide_render),
        "instance": obj.instance_type if obj.instance_type != "NONE" else None,
        "display": obj.display_type,
    }
    try:
        d["hidden"] = bool(obj.hide_get(view_layer=view_layer))
    except Exception:
        d["hidden"] = False
    try:
        d["world_loc"] = _vec(obj.matrix_world.translation)
        if obj.type in ("MESH", "CURVE", "SURFACE", "FONT", "META"):
            mw = obj.matrix_world
            cs = [mw @ Vector(c) for c in obj.bound_box]
            d["wbox"] = [_r(min(c[i] for c in cs), 3) for i in range(3)] + [_r(max(c[i] for c in cs), 3) for i in range(3)]
    except Exception:
        pass
    d["mods"] = []
    for m in obj.modifiers:
        e = {"type": m.type, "name": m.name, "viewport": bool(m.show_viewport), "render": bool(m.show_render),
             "p": _simple_props(m)}
        if m.type == "NODES" and getattr(m, "node_group", None):
            e["group"] = m.node_group.name
        d["mods"].append(e)
    d["cons"] = [{"type": c.type, "target": getattr(getattr(c, "target", None), "name", None)}
                 for c in obj.constraints]
    d["mats"] = [s.material.name if s.material else None for s in obj.material_slots]
    d["vgroups"] = len(obj.vertex_groups)
    d["particles"] = len(getattr(obj, "particle_systems", []) or [])
    anim = _anim(obj)
    if obj.data is not None:
        _merge_anim(anim, _anim(obj.data, "data."))
        sk = getattr(obj.data, "shape_keys", None)
        if sk is not None:
            d["shape_keys"] = max(len(sk.key_blocks) - 1, 0)
            _merge_anim(anim, _anim(sk, "key."))
    d["anim"] = anim
    if obj.type == "MESH":
        me = obj.data
        if obj.mode == "EDIT":
            d.update(_edit_stats(obj))
            d["in_edit"] = True
        else:
            d.update(_mesh_stats(me))
            if d.get("boundary_edges") == 0 and d["faces"] < 20000:
                try:
                    d["volume"] = _r(_volume(me))
                except Exception:
                    pass
        d["uv"] = [u.name for u in me.uv_layers]
        if not d.get("in_edit"):
            d.update(_uv_stats(me))
        d["verts_eval"] = d["verts"]
        d["faces_eval"] = d["faces"]
        if obj.modifiers:
            try:
                ev = obj.evaluated_get(deps).data
                d["verts_eval"], d["faces_eval"] = len(ev.vertices), len(ev.polygons)
            except Exception:
                pass
        if d.get("in_edit"):
            d["verts_eval"], d["faces_eval"] = d["verts"], d["faces"]
    elif obj.type == "LIGHT":
        d["light"] = _light(obj.data)
    elif obj.type == "CAMERA":
        d["camera"] = _camera(obj, scene)
    elif obj.type == "ARMATURE":
        bones = obj.data.bones
        d["armature"] = {"bones": len(bones), "names": [b.name for b in bones][:40]}
    elif obj.type in ("CURVE", "SURFACE"):
        d["curve"] = {"splines": len(obj.data.splines), "bevel_depth": _r(obj.data.bevel_depth, 4),
                      "extrude": _r(obj.data.extrude, 4)}
    elif obj.type == "FONT":
        d["text"] = obj.data.body[:60]
    if obj.pose is not None:
        d["posed"] = any(any(abs(v) > 1e-4 for v in pb.location) or
                         any(abs(v) > 1e-4 for v in pb.rotation_euler) or
                         any(abs(v - 1) > 1e-4 for v in pb.scale) for pb in obj.pose.bones)
    return d


def _objects(snap, scene, view_layer):
    deps = bpy.context.evaluated_depsgraph_get()
    sel_names = set()
    for o in view_layer.objects:
        try:
            if o.select_get(view_layer=view_layer):
                sel_names.add(o.name)
        except Exception:
            pass
    active = view_layer.objects.active
    objs = list(scene.objects)
    snap["objects_total"] = len(objs)
    # selected / active first so they survive the cap
    objs.sort(key=lambda o: (o.name not in sel_names, o is not active))
    out, err = [], []
    for o in objs[:MAX_OBJECTS]:
        try:
            out.append(_object(o, scene, view_layer, deps, active, sel_names))
        except Exception as e:
            err.append(f"{o.name}: {e!r}")
    out.sort(key=lambda x: x["name"])
    snap["objects"] = out
    snap["active"] = active.name if active else None
    snap["selected"] = sorted(sel_names)
    if err:
        snap["errors"].extend(err[:5])


# ---------------------------------------------------------------- materials, images, world

def _upstream(sock_in, depth=6):
    """Node types feeding an input socket (breadth first), nearest first."""
    seen, out, frontier = set(), [], [sock_in]
    for _ in range(depth):
        nxt = []
        for s in frontier:
            for link in s.links:
                n = link.from_node
                if n.name in seen:
                    continue
                seen.add(n.name)
                out.append(n.type)
                nxt.extend(i for i in n.inputs if i.is_linked)
        frontier = nxt
        if not frontier:
            break
    return out


def _material(m):
    d = {"name": m.name, "users": m.users, "color": _vec(m.diffuse_color, 3),
         "viewport_metallic": _r(m.metallic, 3), "viewport_roughness": _r(m.roughness, 3)}
    tree = m.node_tree
    d["use_nodes"] = tree is not None
    if tree is None:
        return d
    nodes = tree.nodes
    d["types"] = sorted({n.type for n in nodes})
    d["n_nodes"], d["n_links"] = len(nodes), len(tree.links)
    d["images"] = sorted({n.image.name for n in nodes if n.type == "TEX_IMAGE" and n.image})
    out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL" and getattr(n, "is_active_output", True)), None)
    d["surface"] = None
    if out is not None:
        s = out.inputs.get("Surface")
        if s is not None and s.links:
            d["surface"] = s.links[0].from_node.type
    p = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if p is not None:
        d["principled"] = True
        for key in ("base_color", "emission"):
            s = compat.sock(p, key)
            if s is not None and not s.is_linked:
                d[key] = _vec(s.default_value, 3)
        for key in ("metallic", "roughness", "emission_strength", "alpha", "ior", "transmission", "coat", "specular"):
            s = compat.sock(p, key)
            if s is not None and not s.is_linked:
                d[key] = _r(s.default_value, 3)
        chain = {}
        for key in ("base_color", "metallic", "roughness", "normal", "emission", "alpha", "specular", "transmission"):
            s = compat.sock(p, key)
            if s is not None and s.is_linked:
                chain[key] = _upstream(s)
        d["chain"] = chain
    else:
        d["principled"] = False
    # emission node strength (for glowing lantern lessons)
    em = next((n for n in nodes if n.type == "EMISSION"), None)
    if em is not None:
        d["emit_node_strength"] = _r(em.inputs["Strength"].default_value, 3)
    return d


def _materials(snap):
    snap["materials"] = [_material(m) for m in bpy.data.materials if not m.is_grease_pencil][:120]


def _images(snap):
    out = []
    for im in bpy.data.images:
        if im.type in ("RENDER_RESULT", "COMPOSITING"):
            continue
        out.append({"name": im.name, "w": im.size[0], "h": im.size[1], "source": im.source,
                    "path": im.filepath, "colorspace": im.colorspace_settings.name,
                    "users": im.users, "packed": im.packed_file is not None, "dirty": bool(im.is_dirty),
                    "generated": im.source == "GENERATED"})
    snap["images"] = out[:80]


def _world(snap, scene):
    w = scene.world
    if w is None:
        snap["world"] = None
        return
    d = {"name": w.name, "color": _vec(w.color, 3)}
    tree = w.node_tree
    d["use_nodes"] = tree is not None
    if tree is not None:
        d["types"] = sorted({n.type for n in tree.nodes})
        bg = next((n for n in tree.nodes if n.type == "BACKGROUND"), None)
        if bg is not None:
            c = bg.inputs["Color"]
            d["bg_linked"] = c.is_linked
            if not c.is_linked:
                d["bg_color"] = _vec(c.default_value, 3)
            d["strength"] = _r(bg.inputs["Strength"].default_value, 3)
        sky = next((n for n in tree.nodes if n.type == "TEX_SKY"), None)
        if sky is not None:
            d["sky_type"] = getattr(sky, "sky_type", None)
        d["has_hdri"] = any(n.type == "TEX_ENVIRONMENT" and n.image for n in tree.nodes)
        d["has_volume"] = any(n.type in ("VOLUME_SCATTER", "VOLUME_ABSORPTION", "PRINCIPLED_VOLUME") for n in tree.nodes)
    snap["world"] = d


def _node_groups(snap):
    out = []
    for g in bpy.data.node_groups:
        out.append({"name": g.name, "kind": g.bl_idname, "n": len(g.nodes),
                    "ids": sorted({n.bl_idname for n in g.nodes}),
                    "users": g.users})
    snap["node_groups"] = out[:40]


# ---------------------------------------------------------------- scene, render, ui

def _render(snap, scene):
    r = scene.render
    kind = compat.engine_kind(r.engine)
    d = {"engine": kind, "engine_id": r.engine, "res_x": r.resolution_x, "res_y": r.resolution_y,
         "res_pct": r.resolution_percentage, "film_transparent": bool(r.film_transparent),
         "format": r.image_settings.file_format, "filepath": r.filepath,
         "fps": r.fps, "frame_start": scene.frame_start, "frame_end": scene.frame_end,
         "frame": scene.frame_current, "motion_blur": bool(getattr(r, "use_motion_blur", False)),
         "simplify": bool(r.use_simplify), "simplify_subdiv": r.simplify_subdivision_render,
         "ffmpeg_format": getattr(r.ffmpeg, "format", None) if r.image_settings.file_format == "FFMPEG" else None}
    vs = scene.view_settings
    d.update(view_transform=vs.view_transform, look=vs.look, exposure=_r(vs.exposure, 2), gamma=_r(vs.gamma, 2))
    cy = getattr(scene, "cycles", None)
    if cy is not None:
        for key in ("samples", "preview_samples", "use_denoising", "denoiser", "use_adaptive_sampling",
                    "adaptive_threshold", "device", "max_bounces", "diffuse_bounces", "glossy_bounces",
                    "transmission_bounces", "volume_bounces", "use_light_tree", "film_exposure"):
            if hasattr(cy, key):
                v = getattr(cy, key)
                d["cy_" + key] = _r(v) if isinstance(v, float) else v
    ev = getattr(scene, "eevee", None)
    if ev is not None:
        for key in ("taa_render_samples", "taa_samples", "use_bloom", "use_gtao", "use_ssr", "use_raytracing",
                    "use_soft_shadows", "use_shadows"):
            if hasattr(ev, key):
                d["ev_" + key] = getattr(ev, key)
    snap["render"] = d


def _scene(snap, scene):
    tree = compat.comp_tree(scene)
    comp_on = bool(tree) and (getattr(scene, "use_nodes", True) or tree is not None)
    snap["scene"] = {
        "name": scene.name, "camera": scene.camera.name if scene.camera else None,
        "unit_system": scene.unit_settings.system, "unit_scale": _r(scene.unit_settings.scale_length, 4),
        "markers": len(scene.timeline_markers), "gravity": _vec(scene.gravity, 2),
        "rigidbody": scene.rigidbody_world is not None, "cursor": _vec(scene.cursor.location),
        "frame": scene.frame_current,
        "comp_nodes": sorted({n.type for n in tree.nodes}) if comp_on and tree is not None else [],
        "collections": _collections(scene.collection),
    }


def _collections(col, depth=0):
    out = []
    for c in col.children:
        out.append({"name": c.name, "objects": len(c.objects), "hide_render": bool(c.hide_render),
                    "children": _collections(c, depth + 1) if depth < 3 else []})
    return out


def _ui(snap):
    wm = bpy.context.window_manager
    ui = {"windows": len(wm.windows), "areas": [], "workspace": None, "shading": None, "xray": False,
          "stats": False, "wire_overlay": False, "persp": None, "view_dist": None, "local_view": False}
    try:
        if wm.windows:
            win = wm.windows[0]
            ui["workspace"] = win.workspace.name
            ui["screen"] = win.screen.name
        for w in wm.windows:
            for a in w.screen.areas:
                ui["areas"].append(a.type)
        found = compat.find_area("VIEW_3D")
        if found:
            _, area, _ = found
            sp = area.spaces.active
            ui["shading"] = sp.shading.type
            ui["xray"] = bool(sp.shading.show_xray)
            ui["stats"] = bool(sp.overlay.show_stats)
            ui["wire_overlay"] = bool(sp.overlay.show_wireframes)
            r3d = sp.region_3d
            ui["persp"] = r3d.view_perspective
            ui["view_dist"] = _r(r3d.view_distance, 2)
            ui["local_view"] = sp.local_view is not None
            ui["gizmo"] = bool(sp.show_gizmo)
            ui["view_matrix"] = [_r(x, 3) for row in r3d.view_matrix for x in row]
    except Exception as e:
        snap["errors"].append(f"ui: {e!r}")
    ui["areas"] = sorted(set(ui["areas"]))
    snap["ui"] = ui


def _prefs(snap):
    p = bpy.context.preferences
    d = {}
    for name, fn in (
        ("emulate_numpad", lambda: bool(p.inputs.use_emulate_numpad)),
        ("emulate_3button", lambda: bool(p.inputs.use_mouse_emulate_3_button)),
        ("undo_steps", lambda: int(p.edit.undo_steps)),
        ("autosave", lambda: bool(p.filepaths.use_auto_save_temporary_files)),
        ("autosave_minutes", lambda: int(p.filepaths.auto_save_time)),
        ("ui_scale", lambda: _r(p.view.ui_scale, 2)),
        ("show_tooltips_python", lambda: bool(p.view.show_tooltips_python)),
        ("save_versions", lambda: int(p.filepaths.save_version)),
    ):
        try:
            d[name] = fn()
        except Exception:
            pass
    snap["prefs"] = d


def _file(snap):
    snap["file"] = {"path": bpy.data.filepath, "name": bpy.path.basename(bpy.data.filepath),
                    "dirty": bool(bpy.data.is_dirty), "saved": bool(bpy.data.is_saved)}


def _totals(snap):
    objs = [o for o in snap.get("objects", []) if o["type"] == "MESH" and not o["hidden"]]
    snap["totals"] = {"meshes": len(objs), "verts": sum(o.get("verts_eval", 0) for o in objs),
                      "faces": sum(o.get("faces_eval", 0) for o in objs),
                      "lights": sum(1 for o in snap.get("objects", []) if o["type"] == "LIGHT"),
                      "cameras": sum(1 for o in snap.get("objects", []) if o["type"] == "CAMERA")}


def build():
    """Collect everything. Returns a plain dict (JSON-able)."""
    ctx = bpy.context
    scene, view_layer = ctx.scene, ctx.view_layer
    snap = {"v": 1, "errors": [],
            "blender": bpy.app.version_string, "bver": list(bpy.app.version),
            "platform": platform.system().lower(), "background": bool(bpy.app.background),
            "mode": ctx.mode}
    steps = (
        ("file", lambda: _file(snap)),
        ("scene", lambda: _scene(snap, scene)),
        ("render", lambda: _render(snap, scene)),
        ("objects", lambda: _objects(snap, scene, view_layer)),
        ("materials", lambda: _materials(snap)),
        ("images", lambda: _images(snap)),
        ("world", lambda: _world(snap, scene)),
        ("node_groups", lambda: _node_groups(snap)),
        ("ui", lambda: _ui(snap)),
        ("prefs", lambda: _prefs(snap)),
        ("totals", lambda: _totals(snap)),
    )
    for name, fn in steps:
        try:
            fn()
        except Exception as e:                      # one broken section must not lose the rest
            snap["errors"].append(f"{name}: {e!r}")
    return snap
