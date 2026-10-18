"""matkit.py - build a PBR material from image maps, and the "CPU friendly" render preset."""
import os

import bpy

from . import compat

# Texture Lab hands over files keyed by these names.
MAP_KINDS = ("base_color", "roughness", "metallic", "normal", "height", "ao", "emission")
NON_COLOR = {"roughness", "metallic", "normal", "height", "ao"}


def build_pbr(name, files, tiling=(1.0, 1.0), normal_strength=1.0, bump_strength=0.2):
    """files: {map kind: absolute image path}. Returns the Material."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    compat.use_nodes(mat)
    nt = mat.node_tree
    nt.nodes.clear()
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (700, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (400, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-1000, 0)
    mp = nodes.new("ShaderNodeMapping")
    mp.location = (-800, 0)
    mp.inputs["Scale"].default_value = (tiling[0], tiling[1], 1.0)
    links.new(tc.outputs["UV"], mp.inputs["Vector"])

    imgs = {}
    y = 500
    for kind in MAP_KINDS:
        path = files.get(kind)
        if not path or not os.path.exists(path):
            continue
        n = nodes.new("ShaderNodeTexImage")
        n.location = (-560, y)
        y -= 300
        img = bpy.data.images.load(path, check_existing=True)
        img.reload()
        if kind in NON_COLOR:
            img.colorspace_settings.name = "Non-Color"
        n.image = img
        n.label = kind
        links.new(mp.outputs["Vector"], n.inputs["Vector"])
        imgs[kind] = n

    def feed(kind, key, via=None):
        n = imgs.get(kind)
        s = compat.sock(bsdf, key)
        if n is None or s is None:
            return
        links.new(n.outputs["Color"], s)

    feed("base_color", "base_color")
    feed("roughness", "roughness")
    feed("metallic", "metallic")
    feed("emission", "emission")
    if "ao" in imgs and "base_color" in imgs:
        _multiply_ao(nt, imgs["base_color"], imgs["ao"], bsdf)
    normal_src = None
    if "normal" in imgs:
        nm = nodes.new("ShaderNodeNormalMap")
        nm.location = (-100, -300)
        nm.inputs["Strength"].default_value = normal_strength
        links.new(imgs["normal"].outputs["Color"], nm.inputs["Color"])
        normal_src = nm.outputs["Normal"]
    if "height" in imgs:
        bp = nodes.new("ShaderNodeBump")
        bp.location = (150, -400)
        bp.inputs["Strength"].default_value = bump_strength
        links.new(imgs["height"].outputs["Color"], bp.inputs["Height"])
        if normal_src is not None:
            links.new(normal_src, bp.inputs["Normal"])
        normal_src = bp.outputs["Normal"]
    if normal_src is not None:
        links.new(normal_src, compat.sock(bsdf, "normal"))
    return mat


def _multiply_ao(nt, base, ao, bsdf):
    try:
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        mix.location = (-150, 300)
        nt.links.new(base.outputs["Color"], mix.inputs["Color1"])
        nt.links.new(ao.outputs["Color"], mix.inputs["Color2"])
        nt.links.new(mix.outputs["Color"], compat.sock(bsdf, "base_color"))
    except Exception:
        pass


def assign(mat, objs):
    for ob in objs:
        if ob.type not in ("MESH", "CURVE", "SURFACE", "FONT"):
            continue
        if ob.material_slots:
            ob.material_slots[0].material = mat
        else:
            ob.data.materials.append(mat)


# ------------------------------------------------------------------ CPU preset

PRESETS = {
    # name: (res_x, res_y, samples, preview samples, adaptive threshold)
    "draft": (960, 540, 24, 8, 0.10),
    "standard": (1280, 720, 64, 16, 0.05),
    "final": (1920, 1080, 128, 16, 0.03),
}


def _set(obj, **kw):
    for k, v in kw.items():
        try:
            setattr(obj, k, v)
        except Exception:
            pass


def cpu_preset(scene, quality="standard"):
    """Cycles on the CPU with a sane budget: low samples + OpenImageDenoise + adaptive sampling."""
    rx, ry, spp, pv, thr = PRESETS.get(quality, PRESETS["standard"])
    scene.render.engine = "CYCLES"
    cy = scene.cycles
    _set(cy, device="CPU", samples=spp, preview_samples=pv, use_adaptive_sampling=True, adaptive_threshold=thr,
         use_denoising=True, denoiser="OPENIMAGEDENOISE", max_bounces=6, diffuse_bounces=2, glossy_bounces=3,
         transmission_bounces=4, volume_bounces=0, transparent_max_bounces=4, caustics_reflective=False,
         caustics_refractive=False, sample_clamp_indirect=10.0, use_preview_denoising=True)
    _set(scene.render, resolution_x=rx, resolution_y=ry, resolution_percentage=100, use_persistent_data=True)
    return {"quality": quality, "res": [rx, ry], "samples": spp, "threshold": thr}
