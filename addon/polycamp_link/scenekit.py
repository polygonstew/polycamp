"""scenekit.py - tiny scene-building helpers that behave the same on Blender 3.3 / 4.x / 5.x.

Lesson starter scripts and the add-on's own "fresh scene" command use these. Everything goes
through the data API / bmesh (no bpy.ops), so it works from a timer, from a headless run and
without any editor open.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import compat


# ------------------------------------------------------------------ wiping

def wipe(keep_world=False):
    """Delete (almost) everything in the file. Used by 'fresh scene' and starter scripts."""
    try:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass
    for scene in bpy.data.scenes:
        for m in list(scene.timeline_markers):
            scene.timeline_markers.remove(m)
    colls = [bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
             bpy.data.curves, bpy.data.armatures, bpy.data.actions, bpy.data.node_groups, bpy.data.textures,
             bpy.data.collections, bpy.data.images, bpy.data.shape_keys, bpy.data.texts]
    if not keep_world:
        colls.append(bpy.data.worlds)
    for coll in colls:
        for item in list(coll):
            try:
                if coll is bpy.data.images and item.type in ("RENDER_RESULT", "COMPOSITING"):
                    continue
                coll.remove(item)
            except Exception:
                pass


def reset_scene_settings(scene=None):
    scene = scene or bpy.context.scene
    r = scene.render
    r.engine = compat.engine_id("EEVEE")
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    r.film_transparent = False
    r.use_simplify = False
    try:
        if hasattr(r.image_settings, "media_type"):          # Blender 5: back to still images before the format
            r.image_settings.media_type = "IMAGE"
        r.image_settings.file_format = "PNG"
    except Exception:
        pass
    r.fps = 24
    scene.frame_start, scene.frame_end, scene.frame_current = 1, 250, 1
    scene.camera = None
    try:                                                      # compositor leftovers from an earlier scene (<= 4.5 keeps the tree)
        tree = getattr(scene, "node_tree", None)
        if tree is not None:
            tree.nodes.clear()
        if hasattr(scene, "use_nodes"):
            scene.use_nodes = False
    except Exception:
        pass
    scene.use_gravity = True
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    try:
        scene.view_settings.view_transform = "AgX" if compat.VER >= (4, 0, 0) else "Filmic"
        scene.view_settings.look = "None"
        scene.view_settings.exposure = 0.0
    except Exception:
        pass
    try:
        scene.cycles.samples = 128 if compat.VER < (4, 0, 0) else 4096
    except Exception:
        pass


def make_world(color=(0.0508, 0.0508, 0.0508, 1.0), strength=1.0, name="World"):
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    compat.use_nodes(w)
    bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg is None:
        bg = w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = color
    bg.inputs["Strength"].default_value = strength
    bpy.context.scene.world = w
    return w


def default_scene():
    """The factory scene: Cube, Light, Camera, World. Returns (cube, light, camera)."""
    wipe()
    reset_scene_settings()
    make_world()
    scene = bpy.context.scene
    col = scene.collection.children.get("Collection")
    if col is None:
        col = bpy.data.collections.new("Collection")
        scene.collection.children.link(col)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    uv_cross_cube(bm)
    cube = mesh_object("Cube", bm, collection=col)
    cube.data.materials.append(pbr("Material", (0.8, 0.8, 0.8, 1.0), roughness=0.5))
    ld = bpy.data.lights.new("Light", "POINT")
    ld.energy = 1000.0
    light = bpy.data.objects.new("Light", ld)
    light.location = (4.0762, 1.0055, 5.9039)
    col.objects.link(light)
    cd = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cd)
    cam.location = (7.3589, -6.9258, 4.9583)
    cam.rotation_euler = [math.radians(a) for a in (63.5593, 0.0, 46.6919)]
    col.objects.link(cam)
    scene.camera = cam
    select_only(cube)
    return cube, light, cam


# ------------------------------------------------------------------ objects

def select_only(*objs):
    vl = bpy.context.view_layer
    for o in vl.objects:
        try:
            o.select_set(False)
        except Exception:
            pass
    for o in objs:
        try:
            o.select_set(True)
        except Exception:
            pass
    if objs:
        vl.objects.active = objs[-1]


def mesh_object(name, bm, collection=None, loc=(0, 0, 0), rot_deg=(0, 0, 0), scale=(1, 1, 1), smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    ob.scale = scale
    (collection or bpy.context.scene.collection).objects.link(ob)
    if smooth:
        set_smooth(ob)
    return ob


def set_smooth(obj, angle_deg=None):
    """Shade smooth; with angle_deg keep edges sharper than that angle crisp (works without auto-smooth)."""
    me = obj.data
    if angle_deg is not None:
        bm = bmesh.new()
        bm.from_mesh(me)
        lim = math.radians(angle_deg)
        for e in bm.edges:
            e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim)
        for f in bm.faces:
            f.smooth = True
        bm.to_mesh(me)
        bm.free()
        if compat.VER < (4, 1, 0):
            me.use_auto_smooth = True
            me.auto_smooth_angle = math.radians(angle_deg)
    else:
        for p in me.polygons:
            p.use_smooth = True
    me.update()


def _try(fn, bm, variants, **kw):
    last = None
    for extra in variants:
        try:
            return fn(bm, **kw, **extra)
        except TypeError as e:
            last = e
    raise last


def add_box(bm, size=(1, 1, 1), center=(0, 0, 0)):
    """Append a box (size = full width/depth/height) to bmesh bm."""
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    bmesh.ops.scale(bm, vec=Vector(size), verts=verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return verts


def add_cylinder(bm, radius=0.5, depth=1.0, segments=16, center=(0, 0, 0), radius2=None, cap=True):
    verts = _try(bmesh.ops.create_cone, bm,
                 [dict(radius1=radius, radius2=radius if radius2 is None else radius2),
                  dict(diameter1=radius * 2, diameter2=(radius if radius2 is None else radius2) * 2)],
                 cap_ends=cap, cap_tris=False, segments=segments, depth=depth)["verts"]
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return verts


def add_sphere(bm, radius=0.5, u=16, v=10, center=(0, 0, 0)):
    verts = _try(bmesh.ops.create_uvsphere, bm,
                 [dict(radius=radius), dict(diameter=radius)], u_segments=u, v_segments=v)["verts"]
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return verts


def add_icosphere(bm, radius=0.5, subdiv=2, center=(0, 0, 0)):
    verts = _try(bmesh.ops.create_icosphere, bm,
                 [dict(radius=radius), dict(diameter=radius)], subdivisions=subdiv)["verts"]
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return verts


def uv_box_project(bm, scale=1.0):
    """Box-project UVs: every face is flattened along its dominant normal axis. scale = tiles per metre."""
    layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [i for i in range(3) if i != ax]
        for lp in f.loops:
            co = lp.vert.co
            lp[layer].uv = (co[a] * scale, co[b] * scale)


def uv_cross_cube(bm):
    """The classic cross-shaped unwrap of a cube (what the factory Cube ships with)."""
    layer = bm.loops.layers.uv.verify()
    cell = {(2, 1): (1, 2), (2, -1): (1, 0), (1, -1): (1, 1), (0, 1): (2, 1), (1, 1): (3, 1), (0, -1): (0, 1)}
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        sign = 1 if n[ax] > 0 else -1
        col, row = cell[(ax, sign)]
        a, b = [i for i in range(3) if i != ax]
        for lp in f.loops:
            co = lp.vert.co
            lo = min(v.co[a] for v in f.verts), min(v.co[b] for v in f.verts)
            span = max(max(v.co[a] for v in f.verts) - lo[0], 1e-6), max(max(v.co[b] for v in f.verts) - lo[1], 1e-6)
            lp[layer].uv = ((col + (co[a] - lo[0]) / span[0]) * 0.25, (row + (co[b] - lo[1]) / span[1]) * 0.25 + 0.125)


def add_grid(bm, size=2.0, div=10):
    res = _try(bmesh.ops.create_grid, bm, [dict(size=size / 2), dict(size=size)], x_segments=div, y_segments=div)
    return res["verts"]


# ------------------------------------------------------------------ materials, lights, camera

def pbr(name, color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0, emission=None, emission_strength=0.0,
        alpha=1.0):
    """Principled material with the usual knobs; emission=(r,g,b) turns it into a light-emitting surface."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    compat.use_nodes(mat)
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if len(color) == 3:
        color = (*color, 1.0)
    compat.sock(bsdf, "base_color").default_value = color
    compat.sock(bsdf, "roughness").default_value = roughness
    compat.sock(bsdf, "metallic").default_value = metallic
    compat.sock(bsdf, "alpha").default_value = alpha
    if emission is not None:
        compat.sock(bsdf, "emission").default_value = (*emission[:3], 1.0)
        compat.sock(bsdf, "emission_strength").default_value = emission_strength
    mat.diffuse_color = color
    return mat


def add_light(kind, name, loc, energy, color=(1, 1, 1), rot_deg=None, size=None, collection=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color[:3]
    if size is not None:
        if kind == "AREA":
            ld.size = size
        elif kind == "SUN":
            ld.angle = math.radians(size)
        else:
            ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    if rot_deg:
        ob.rotation_euler = [math.radians(a) for a in rot_deg]
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def add_camera(name, loc, target=(0, 0, 0), lens=50.0, collection=None, make_active=True):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    (collection or bpy.context.scene.collection).objects.link(ob)
    look_at(ob, target)
    if make_active:
        bpy.context.scene.camera = ob
    return ob


def look_at(obj, target):
    """Aim obj's -Z at target with +Y up (what a camera or spot light wants)."""
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
