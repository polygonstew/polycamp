"""compat.py - the Blender 3.3 / 4.x / 5.x differences the add-on cares about, in one place."""
import bpy

VER = tuple(bpy.app.version)

# Principled BSDF socket names changed in 4.0; look them up by a canonical key.
SOCKETS = {
    "base_color": ["Base Color"],
    "metallic": ["Metallic"],
    "roughness": ["Roughness"],
    "ior": ["IOR"],
    "alpha": ["Alpha"],
    "normal": ["Normal"],
    "emission": ["Emission Color", "Emission"],
    "emission_strength": ["Emission Strength"],
    "transmission": ["Transmission Weight", "Transmission"],
    "coat": ["Coat Weight", "Clearcoat"],
    "specular": ["Specular IOR Level", "Specular"],
    "subsurface": ["Subsurface Weight", "Subsurface"],
}


def sock(node, key):
    """Return the input socket of a Principled BSDF for a canonical key, or None."""
    for name in SOCKETS.get(key, [key]):
        s = node.inputs.get(name)
        if s is not None:
            return s
    return None


def engine_items():
    try:
        return [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    except Exception:
        return []


def engine_id(kind):
    """Map 'CYCLES' / 'EEVEE' / 'WORKBENCH' to this Blender's identifier."""
    if kind == "EEVEE":
        items = engine_items()
        for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            if cand in items:
                return cand
        return "BLENDER_EEVEE"
    if kind == "WORKBENCH":
        return "BLENDER_WORKBENCH"
    return "CYCLES"


def engine_kind(ident):
    if ident.startswith("BLENDER_EEVEE"):
        return "EEVEE"
    if ident == "BLENDER_WORKBENCH":
        return "WORKBENCH"
    return ident


def use_nodes(datablock):
    """Materials/worlds: nodes are always on in 5.x; before that they must be switched on."""
    try:
        if not datablock.use_nodes:
            datablock.use_nodes = True
    except Exception:
        pass


def comp_tree(scene):
    """Compositor node tree (moved in 5.0)."""
    t = getattr(scene, "compositing_node_group", None)
    if t is None:
        t = getattr(scene, "node_tree", None)
    return t


def iter_fcurves(action):
    """F-curves of an action in every API generation (legacy <=4.5, layered 4.4+, 5.x only layered)."""
    if action is None:
        return
    try:
        for f in action.fcurves:
            yield f
        return
    except (AttributeError, RuntimeError):
        pass
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for f in cb.fcurves:
                        yield f
    except Exception:
        return


def set_blf_size(font_id, size):
    import blf
    try:
        blf.size(font_id, size)          # 4.0+
    except TypeError:
        blf.size(font_id, size, 72)      # <= 3.x


def find_area(kind="VIEW_3D"):
    """(window, area, region) of the first matching area, or None (background mode has no windows)."""
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == kind:
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                return win, area, region
    return None
