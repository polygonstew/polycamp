# content/lib/00_core.py - helpers shared by every starter scene and solution script.
# Runs inside Blender (3.3 / 4.x / 5.x) through Polycamp Link. Namespace gives you: bpy, bmesh, math, Vector, Matrix,
# kit (scenekit), matkit, compat, note_op. Everything here uses the data API, never bpy.ops, so it works anywhere.
import random as _random
from mathutils import noise as _noise


def srgb(hexcol, a=1.0):
    """'#c8a064' -> linear RGBA tuple (what node colours expect)."""
    h = hexcol.lstrip('#')
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (a,)


def get_collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def box_at(bm, size, center=(0, 0, 0), rot_deg=(0, 0, 0)):
    """Append a box of full size `size`, rotated about its own centre, then moved to `center`."""
    v = kit.add_box(bm, size)
    if any(rot_deg):
        e = Euler([math.radians(a) for a in rot_deg])
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=e.to_matrix(), verts=v)
    bmesh.ops.translate(bm, vec=Vector(center), verts=v)
    return v


def add_torus(bm, major=0.5, minor=0.08, seg_major=24, seg_minor=8, center=(0, 0, 0), axis='Y'):
    """A torus (bmesh has no primitive for it). Ring lies in XZ when axis='Y', in XY when axis='Z'."""
    rows = []
    for i in range(seg_major):
        a = 2 * math.pi * i / seg_major
        ring = []
        for j in range(seg_minor):
            b = 2 * math.pi * j / seg_minor
            r = major + minor * math.cos(b)
            u, w = r * math.cos(a), minor * math.sin(b)
            v = r * math.sin(a)
            co = (u, w, v) if axis == 'Y' else (u, v, w)
            ring.append(bm.verts.new((co[0] + center[0], co[1] + center[1], co[2] + center[2])))
        rows.append(ring)
    for i in range(seg_major):
        for j in range(seg_minor):
            try:
                bm.faces.new((rows[i][j], rows[i][(j + 1) % seg_minor], rows[(i + 1) % seg_major][(j + 1) % seg_minor],
                              rows[(i + 1) % seg_major][j]))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def add_bevel(ob, width=0.02, segments=2, angle=30):
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width, m.segments = width, segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    return m


def add_subsurf(ob, levels=2, render_levels=None):
    m = ob.modifiers.new('Subdivision', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels if render_levels is None else render_levels
    return m


def finish(ob, mat=None, smooth=False, angle=None, bevel=None):
    """Common last steps: material, shading, optional bevel (width) on a freshly built object."""
    if mat is not None:
        ob.data.materials.append(mat)
    if smooth:
        kit.set_smooth(ob, angle)
    if bevel:
        add_bevel(ob, bevel)
    return ob


# ------------------------------------------------------------------ procedural materials (all node based, no files)

def _mat(name):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m, False
    m = bpy.data.materials.new(name)
    compat.use_nodes(m)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    out.location, bsdf.location = (420, 0), (140, 0)
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m, True


def _node(nt, idname, loc, **props):
    n = nt.nodes.new(idname)
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n


def _ramp(nt, loc, stops):
    r = _node(nt, 'ShaderNodeValToRGB', loc)
    els = r.color_ramp.elements
    while len(els) > 2:
        els.remove(els[-1])
    els[0].position, els[0].color = stops[0][0], srgb(stops[0][1])
    els[1].position, els[1].color = stops[1][0], srgb(stops[1][1])
    for pos, hexcol in stops[2:]:
        e = els.new(pos)
        e.color = srgb(hexcol)
    return r


def _coords(nt, scale=(1, 1, 1)):
    tc = _node(nt, 'ShaderNodeTexCoord', (-900, 0))
    mp = _node(nt, 'ShaderNodeMapping', (-700, 0))
    mp.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp


def _principled(m):
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _bump(nt, height_socket, strength, loc=(-80, -380)):
    b = _node(nt, 'ShaderNodeBump', loc)
    b.inputs['Strength'].default_value = strength
    nt.links.new(height_socket, b.inputs['Height'])
    return b


def mat_wood(name='Wood', light='#b57b45', dark='#5b3418', scale=7.0, rough=0.62, squash=(1.0, 1.0, 0.22)):
    m, new = _mat(name)
    if not new:
        return m
    nt = m.node_tree
    bsdf = _principled(m)
    mp = _coords(nt, squash)
    wave = _node(nt, 'ShaderNodeTexWave', (-480, 120), wave_type='BANDS', bands_direction='X')
    wave.inputs['Scale'].default_value = scale
    wave.inputs['Distortion'].default_value = 5.0
    wave.inputs['Detail'].default_value = 3.0
    nt.links.new(mp.outputs['Vector'], wave.inputs['Vector'])
    ramp = _ramp(nt, (-220, 120), [(0.0, dark), (1.0, light)])
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], compat.sock(bsdf, 'base_color'))
    grain = _node(nt, 'ShaderNodeTexNoise', (-480, -200))
    grain.inputs['Scale'].default_value = 60.0
    nt.links.new(mp.outputs['Vector'], grain.inputs['Vector'])
    b = _bump(nt, grain.outputs['Fac'], 0.12)
    nt.links.new(b.outputs['Normal'], compat.sock(bsdf, 'normal'))
    compat.sock(bsdf, 'roughness').default_value = rough
    return m


def mat_stone(name='Stone', light='#9a958a', dark='#4d4a45', scale=3.5, rough=0.88):
    m, new = _mat(name)
    if not new:
        return m
    nt = m.node_tree
    bsdf = _principled(m)
    mp = _coords(nt)
    vor = _node(nt, 'ShaderNodeTexVoronoi', (-480, 160))
    vor.inputs['Scale'].default_value = scale
    nt.links.new(mp.outputs['Vector'], vor.inputs['Vector'])
    noi = _node(nt, 'ShaderNodeTexNoise', (-480, -120))
    noi.inputs['Scale'].default_value = 14.0
    noi.inputs['Detail'].default_value = 6.0
    nt.links.new(mp.outputs['Vector'], noi.inputs['Vector'])
    mix = _node(nt, 'ShaderNodeMixRGB', (-240, 60), blend_type='MIX')
    mix.inputs['Fac'].default_value = 0.35
    nt.links.new(vor.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(noi.outputs['Color'], mix.inputs['Color2'])
    ramp = _ramp(nt, (-20, 60), [(0.15, dark), (0.85, light)])
    nt.links.new(mix.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], compat.sock(bsdf, 'base_color'))
    b = _bump(nt, noi.outputs['Fac'], 0.45)
    nt.links.new(b.outputs['Normal'], compat.sock(bsdf, 'normal'))
    compat.sock(bsdf, 'roughness').default_value = rough
    return m


def mat_roof(name='Roof', c1='#4a3224', c2='#6b4a34', scale=(6.0, 5.0, 1), rough=0.8):
    m, new = _mat(name)
    if not new:
        return m
    nt = m.node_tree
    bsdf = _principled(m)
    mp = _coords(nt)
    br = _node(nt, 'ShaderNodeTexBrick', (-480, 100), offset=0.5, offset_frequency=2)
    br.inputs['Scale'].default_value = scale[0]
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Color1'].default_value = srgb(c1)
    br.inputs['Color2'].default_value = srgb(c2)
    br.inputs['Mortar'].default_value = srgb('#201510')
    nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], compat.sock(bsdf, 'base_color'))
    b = _bump(nt, br.outputs['Fac'], 0.25)
    nt.links.new(b.outputs['Normal'], compat.sock(bsdf, 'normal'))
    compat.sock(bsdf, 'roughness').default_value = rough
    return m


def _noise_ramp(name, stops, scale, detail, rough, bump=0.0, noise2=None):
    m, new = _mat(name)
    if not new:
        return m
    nt = m.node_tree
    bsdf = _principled(m)
    mp = _coords(nt)
    n1 = _node(nt, 'ShaderNodeTexNoise', (-480, 100))
    n1.inputs['Scale'].default_value = scale
    n1.inputs['Detail'].default_value = detail
    nt.links.new(mp.outputs['Vector'], n1.inputs['Vector'])
    ramp = _ramp(nt, (-220, 100), stops)
    nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], compat.sock(bsdf, 'base_color'))
    if bump:
        n2 = _node(nt, 'ShaderNodeTexNoise', (-480, -200))
        n2.inputs['Scale'].default_value = noise2 or scale * 6
        nt.links.new(mp.outputs['Vector'], n2.inputs['Vector'])
        b = _bump(nt, n2.outputs['Fac'], bump)
        nt.links.new(b.outputs['Normal'], compat.sock(bsdf, 'normal'))
    compat.sock(bsdf, 'roughness').default_value = rough
    return m


def mat_grass(name='Grass'):
    return _noise_ramp(name, [(0.35, '#2f5a22'), (0.7, '#7ea83e')], 6.0, 8.0, 0.92, 0.35, 90)


def mat_dirt(name='Dirt'):
    return _noise_ramp(name, [(0.3, '#3b2a1c'), (0.75, '#7a5a3c')], 5.0, 6.0, 0.96, 0.2, 70)


def mat_leaves(name='Leaves'):
    return _noise_ramp(name, [(0.3, '#16361f'), (0.75, '#2f6b35')], 9.0, 5.0, 0.8, 0.15, 60)


def mat_bark(name='Bark'):
    return _noise_ramp(name, [(0.3, '#2c1c12'), (0.8, '#5f4330')], 4.0, 6.0, 0.9, 0.4, 40)


def mat_iron(name='Iron', color='#26272a'):
    m, new = _mat(name)
    if new:
        b = _principled(m)
        compat.sock(b, 'base_color').default_value = srgb(color)
        compat.sock(b, 'metallic').default_value = 1.0
        compat.sock(b, 'roughness').default_value = 0.42
    return m


def mat_glow(name='Glow', color='#ffb25a', strength=4.0, base=None):
    """Light-emitting surface (windows, lantern glass, flame)."""
    m, new = _mat(name)
    if new:
        b = _principled(m)
        compat.sock(b, 'base_color').default_value = srgb(base or color)
        compat.sock(b, 'roughness').default_value = 0.35
        compat.sock(b, 'emission').default_value = srgb(color)
        compat.sock(b, 'emission_strength').default_value = strength
    return m


def mat_plain(name, color, rough=0.6, metal=0.0):
    m, new = _mat(name)
    if new:
        b = _principled(m)
        compat.sock(b, 'base_color').default_value = srgb(color)
        compat.sock(b, 'roughness').default_value = rough
        compat.sock(b, 'metallic').default_value = metal
        m.diffuse_color = srgb(color)
    return m
