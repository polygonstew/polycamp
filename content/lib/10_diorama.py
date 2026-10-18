# content/lib/10_diorama.py - builders for "Lantern Cabin at Dusk", the campaign's final project.
# Starter scenes use the pieces they need; the final boss scene uses build_diorama(). Needs 00_core.py.

GROUND_R = 4.6
CABIN_W, CABIN_D, CABIN_H = 3.6, 2.8, 2.1


def _gh(x, y, seed=3):
    """Ground height at (x, y): gentle hills, flat under the cabin, rolling off at the rim."""
    d = math.hypot(x, y)
    flat = min(max((d - 2.2) / 1.8, 0.0), 1.0)
    n = _noise.noise(Vector((x * 0.42 + seed, y * 0.42 - seed, 0.0)))
    return 0.16 * n * flat - 0.05 * (d / GROUND_R) ** 4


def _put(bm, name, col, loc=(0, 0, 0), mat=None, smooth=False, angle=None, bevel=None, rot=(0, 0, 0), parent=None):
    ob = kit.mesh_object(name, bm, collection=col, loc=loc, rot_deg=rot)
    finish(ob, mat, smooth, angle, bevel)
    if parent is not None:
        ob.parent = parent
    return ob


# ------------------------------------------------------------------ ground, path, tufts, fence

def build_ground(collection=None, mats=True, R=GROUND_R):
    col = collection or get_collection('Ground')
    bm = bmesh.new()
    rings, segs = 14, 56
    center = bm.verts.new((0, 0, _gh(0, 0)))
    rows = []
    for r in range(1, rings + 1):
        rad = R * r / rings
        rows.append([bm.verts.new((rad * math.cos(2 * math.pi * s / segs), rad * math.sin(2 * math.pi * s / segs),
                                   _gh(rad * math.cos(2 * math.pi * s / segs), rad * math.sin(2 * math.pi * s / segs)))) for s in range(segs)])
    top = []
    for s in range(segs):
        top.append(bm.faces.new((center, rows[0][(s + 1) % segs], rows[0][s])))
    for r in range(rings - 1):
        for s in range(segs):
            top.append(bm.faces.new((rows[r][s], rows[r][(s + 1) % segs], rows[r + 1][(s + 1) % segs], rows[r + 1][s])))
    bottom = [bm.verts.new((v.co.x * 0.93, v.co.y * 0.93, -0.62)) for v in rows[-1]]
    side = [bm.faces.new((rows[-1][s], bottom[s], bottom[(s + 1) % segs], rows[-1][(s + 1) % segs])) for s in range(segs)]
    cap = bm.verts.new((0, 0, -0.62))
    side += [bm.faces.new((cap, bottom[s], bottom[(s + 1) % segs])) for s in range(segs)]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in side:
        f.material_index = 1
    ob = _put(bm, 'Ground', col, smooth=True)
    if mats:
        ob.data.materials.append(mat_grass())
        ob.data.materials.append(mat_dirt())
    return ob


def build_path(collection=None, mats=True):
    col = collection or get_collection('Ground')
    objs = []
    rng = _random.Random(5)
    stone = mat_stone('Stone_Path', '#8d877b', '#4e4a44', 5.0) if mats else None
    for i in range(7):
        t = i / 6
        x, y = 0.05 + 0.9 * math.sin(t * 2.4), -2.05 - t * 2.3
        bm = bmesh.new()
        kit.add_cylinder(bm, rng.uniform(0.28, 0.38), 0.07, 10)
        objs.append(_put(bm, 'PathStone.%02d' % i, col, (x, y, _gh(x, y) + 0.015), stone, True, bevel=0.012, rot=(0, 0, rng.uniform(0, 90))))
    return objs


def build_tufts(count=260, collection=None, mats=True, seed=11):
    col = collection or get_collection('Ground')
    rng = _random.Random(seed)
    bm = bmesh.new()
    n = 0
    while n < count:
        x, y = rng.uniform(-4.2, 4.2), rng.uniform(-4.2, 4.2)
        if math.hypot(x, y) > 4.25 or (abs(x) < 2.35 and -1.7 < y < 1.9) or (abs(x - 0.6) < 0.8 and y < -1.5):
            continue
        n += 1
        for b in range(3):
            h = rng.uniform(0.22, 0.42)
            v = kit.add_cylinder(bm, 0.025, h, 4, center=(0, 0, h / 2), radius2=0.0)
            e = Euler((rng.uniform(-.35, .35), rng.uniform(-.35, .35), rng.uniform(0, 6.28)))
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=e.to_matrix(), verts=v)
            bmesh.ops.translate(bm, vec=(x + rng.uniform(-.06, .06), y + rng.uniform(-.06, .06), _gh(x, y)), verts=v)
    return _put(bm, 'Grass_Tufts', col, mat=mat_grass('Grass_Tuft') if mats else None)


def build_fence(collection=None, mats=True, a0=200, a1=335, r=3.85, posts=9):
    col = collection or get_collection('Fence')
    wood = mat_wood('Fence_Wood', '#9a6a3c', '#4a2d16', 5.0) if mats else None
    objs, pts = [], []
    for i in range(posts):
        a = math.radians(a0 + (a1 - a0) * i / (posts - 1))
        x, y = r * math.cos(a), r * math.sin(a)
        pts.append((x, y, a))
        bm = bmesh.new()
        box_at(bm, (0.1, 0.1, 0.95), (0, 0, 0.475))
        objs.append(_put(bm, 'FencePost.%02d' % i, col, (x, y, _gh(x, y)), wood, bevel=0.012, rot=(0, 0, math.degrees(a) + 3 * (i % 3))))
    for i in range(posts - 1):
        (x0, y0, _), (x1, y1, _) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        for k, z in enumerate((0.38, 0.72)):
            bm = bmesh.new()
            box_at(bm, (L, 0.05, 0.08))
            objs.append(_put(bm, 'FenceRail.%02d.%d' % (i, k), col, ((x0 + x1) / 2, (y0 + y1) / 2, _gh((x0 + x1) / 2, (y0 + y1) / 2) + z), wood, rot=(0, 0, ang)))
    return objs


# ------------------------------------------------------------------ cabin

def build_cabin(loc=(0, 0.3, 0), collection=None, mats=True):
    col = collection or get_collection('Cabin')
    W, D, H, z0, p, t = CABIN_W, CABIN_D, CABIN_H, 0.3, math.radians(33), 0.14
    wood = mat_wood('Cabin_Wood', '#a8723e', '#4f2f16', 9.0) if mats else None
    dark = mat_wood('Door_Wood', '#6a4322', '#2e1a0c', 7.0) if mats else None
    stone = mat_stone('Cabin_Stone', '#8a857a', '#46433e', 3.0) if mats else None
    roofm = mat_roof() if mats else None
    glow = mat_glow('Window_Glow', '#ffb45e', 8.0) if mats else None
    iron = mat_iron() if mats else None
    ob = {}
    root = bpy.data.objects.new('Cabin', None)
    root.location = loc
    col.objects.link(root)
    ob['root'] = root

    bm = bmesh.new()
    box_at(bm, (W + 0.18, D + 0.18, z0 + 0.1), (0, 0, (z0 + 0.1) / 2 - 0.05))
    ob['foundation'] = _put(bm, 'Cabin_Foundation', col, mat=stone, bevel=0.02, parent=root)

    bm = bmesh.new()
    box_at(bm, (W, D, H), (0, 0, z0 + H / 2))
    ridge_h = (D / 2) * math.tan(p)
    for sx in (-1, 1):                                      # gable ends: triangle prisms
        x0, x1 = sx * W / 2, sx * (W / 2 - 0.2)
        a = [bm.verts.new((x, y, z)) for x in (x0, x1) for y, z in ((-D / 2, z0 + H), (D / 2, z0 + H), (0, z0 + H + ridge_h))]
        for tri in ((0, 1, 2), (3, 5, 4)):
            bm.faces.new([a[i] for i in tri])
        for i, j in ((0, 1), (1, 2), (2, 0)):
            bm.faces.new((a[i], a[j], a[j + 3], a[i + 3]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob['walls'] = _put(bm, 'Cabin_Walls', col, mat=wood, bevel=0.015, parent=root)

    bm = bmesh.new()
    a = D / 2 + 0.4
    zmid = z0 + H + (t / 2) / math.cos(p) + (D / 2) * math.tan(p)
    for sy in (-1, 1):
        zc = zmid - (a / 2) * math.tan(p)
        box_at(bm, (W + 0.7, a / math.cos(p) + 0.08, t), (0, sy * (a / 2 - 0.02), zc), (-sy * math.degrees(p), 0, 0))
    box_at(bm, (W + 0.7, 0.2, 0.1), (0, 0, zmid + t * 0.8))
    ob['roof'] = _put(bm, 'Cabin_Roof', col, mat=roofm, bevel=0.01, parent=root)

    fy = -D / 2
    bm = bmesh.new()
    box_at(bm, (0.98, 0.07, 1.78), (0, fy - 0.03, z0 + 0.89))
    ob['door'] = _put(bm, 'Cabin_Door', col, mat=dark, bevel=0.01, parent=root)
    bm = bmesh.new()
    box_at(bm, (1.22, 0.1, 0.1), (0, fy - 0.02, z0 + 1.88))
    for sx in (-1, 1):
        box_at(bm, (0.12, 0.1, 1.9), (sx * 0.6, fy - 0.02, z0 + 0.95))
    for wx in (-1.2, 1.2):                                   # front windows
        for dx, dz, sx_, sz in ((0, 0.36, 0.78, 0.07), (0, -0.36, 0.78, 0.07), (-0.36, 0, 0.07, 0.8), (0.36, 0, 0.07, 0.8), (0, 0, 0.04, 0.72), (0, 0, 0.72, 0.04)):
            box_at(bm, (sx_, 0.08, sz), (wx + dx, fy - 0.02, 1.62 + dz))
    for sx in (-1, 1):                                       # side windows
        for dy, dz, sy_, sz in ((0, 0.36, 0.78, 0.07), (0, -0.36, 0.78, 0.07), (-0.36, 0, 0.07, 0.8), (0.36, 0, 0.07, 0.8)):
            box_at(bm, (0.08, sy_, sz), (sx * (W / 2 + 0.02), 0.1 + dy, 1.62 + dz))
    ob['frames'] = _put(bm, 'Cabin_Frames', col, mat=dark, bevel=0.008, parent=root)
    bm = bmesh.new()
    for wx in (-1.2, 1.2):
        box_at(bm, (0.68, 0.03, 0.7), (wx, fy - 0.005, 1.62))
    for sx in (-1, 1):
        box_at(bm, (0.03, 0.68, 0.7), (sx * (W / 2 + 0.005), 0.1, 1.62))
    ob['panes'] = _put(bm, 'Cabin_Panes', col, mat=glow, parent=root)
    bm = bmesh.new()
    kit.add_sphere(bm, 0.045, 10, 6, center=(0.34, fy - 0.09, z0 + 0.9))
    ob['knob'] = _put(bm, 'Cabin_Knob', col, mat=iron, smooth=True, parent=root)
    bm = bmesh.new()
    box_at(bm, (1.5, 0.55, 0.16), (0, fy - 0.36, 0.06))
    ob['step'] = _put(bm, 'Cabin_Step', col, mat=stone, bevel=0.02, parent=root)

    bm = bmesh.new()
    box_at(bm, (0.58, 0.58, 3.45), (1.15, 0.65, 1.9))
    box_at(bm, (0.74, 0.74, 0.12), (1.15, 0.65, 3.66))
    ob['chimney'] = _put(bm, 'Cabin_Chimney', col, mat=stone, bevel=0.02, parent=root)
    return ob


# ------------------------------------------------------------------ lantern (the hero prop) and lamp post

def build_lantern(loc=(0, 0, 0), collection=None, mats=True, scale=1.0, name='Lantern', parent=None):
    col = collection or get_collection('Lantern')
    iron = mat_iron('Lantern_Iron') if mats else None
    glass = mat_glow('Lantern_Glass', '#ffbf6b', 8.0) if mats else None
    flame = mat_glow('Flame', '#ffd08a', 40.0) if mats else None
    root = bpy.data.objects.new(name, None)
    root.location = loc
    root.scale = (scale,) * 3
    col.objects.link(root)
    if parent is not None:
        root.parent = parent
    out = {'root': root}
    bm = bmesh.new()
    box_at(bm, (0.30, 0.30, 0.04), (0, 0, 0.02))
    box_at(bm, (0.24, 0.24, 0.03), (0, 0, 0.055))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box_at(bm, (0.028, 0.028, 0.36), (sx * 0.125, sy * 0.125, 0.25))
    box_at(bm, (0.31, 0.31, 0.035), (0, 0, 0.455))
    out['frame'] = _put(bm, name + '_Frame', col, mat=iron, bevel=0.004, parent=root)
    bm = bmesh.new()
    box_at(bm, (0.22, 0.22, 0.33), (0, 0, 0.25))
    out['glass'] = _put(bm, name + '_Glass', col, mat=glass, parent=root)
    bm = bmesh.new()
    kit.add_icosphere(bm, 0.045, 2, center=(0, 0, 0.17))
    out['flame'] = _put(bm, name + '_Flame', col, mat=flame, smooth=True, parent=root)
    add_subsurf(out['flame'], 1, 2)
    bm = bmesh.new()
    v = kit.add_cylinder(bm, 0.205, 0.13, 4, center=(0, 0, 0.54), radius2=0.03)
    bmesh.ops.rotate(bm, cent=(0, 0, 0.54), matrix=Euler((0, 0, math.pi / 4)).to_matrix(), verts=v)
    out['cap'] = _put(bm, name + '_Cap', col, mat=iron, bevel=0.004, parent=root)
    bm = bmesh.new()
    add_torus(bm, 0.075, 0.01, 24, 8, (0, 0, 0.66), 'Y')
    out['ring'] = _put(bm, name + '_Ring', col, mat=iron, smooth=True, parent=root)
    return out


def build_lamp_post(loc=(1.15, -2.15, 0), collection=None, mats=True):
    col = collection or get_collection('Lantern')
    iron = mat_iron('Post_Iron') if mats else None
    z = _gh(loc[0], loc[1])
    bm = bmesh.new()
    kit.add_cylinder(bm, 0.05, 2.3, 10, center=(0, 0, 1.15))
    box_at(bm, (0.7, 0.05, 0.05), (-0.33, 0, 2.2))
    box_at(bm, (0.18, 0.18, 0.06), (0, 0, 0.03))
    post = _put(bm, 'Lamp_Post', col, (loc[0], loc[1], z), iron, smooth=True, bevel=0.006)
    lan = build_lantern((loc[0] - 0.66, loc[1], z + 1.74), col, mats, 0.85, 'PostLantern')
    return {'post': post, **lan}


# ------------------------------------------------------------------ rocks and trees

def build_rock(name, loc, size, seed, collection=None, mats=True, squash=(1.0, 0.85, 0.7)):
    col = collection or get_collection('Rocks')
    bm = bmesh.new()
    kit.add_icosphere(bm, 1.0, 3)
    for v in bm.verts:
        n = _noise.noise(v.co * 1.25 + Vector((seed * 1.7, seed * 0.6, seed * 2.3)))
        v.co *= 1.0 + 0.3 * n
        v.co.x *= squash[0]
        v.co.y *= squash[1]
        v.co.z = max(v.co.z * squash[2], -0.45)
    z = _gh(loc[0], loc[1]) + 0.12 * size
    ob = _put(bm, name, col, (loc[0], loc[1], z), mat_stone('Rock', '#8e8a82', '#3f3d3a', 2.6) if mats else None, True,
              rot=(0, 0, seed * 37 % 360))
    ob.scale = (size, size, size)
    return ob


def build_rocks(collection=None, mats=True):
    col = collection or get_collection('Rocks')
    spec = [(-2.9, -1.6, 0.6, 1), (-3.3, -0.9, 0.38, 2), (2.9, -1.2, 0.5, 3), (3.2, 1.0, 0.7, 4), (-1.4, 3.1, 0.45, 5), (0.7, -3.3, 0.22, 6)]
    return [build_rock('Rock.%02d' % i, (x, y), s, sd, col, mats) for i, (x, y, s, sd) in enumerate(spec)]


def build_pine(name, loc, height=2.8, seed=1, collection=None, mats=True):
    col = collection or get_collection('Trees')
    rng = _random.Random(seed)
    s = height / 2.8
    bm = bmesh.new()
    trunk = kit.add_cylinder(bm, 0.11 * s, 0.9 * s, 8, center=(0, 0, 0.45 * s))
    tr = set(trunk)
    for i in range(4):
        r, d = (1.0 - i * 0.2) * s, 1.0 * s
        v = kit.add_cylinder(bm, r, d, 9, center=(0, 0, 0.6 * s + i * 0.55 * s + d / 2), radius2=0.0)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Euler((0, 0, rng.uniform(0, 3))).to_matrix(), verts=v)
    for f in bm.faces:
        f.material_index = 0 if all(v in tr for v in f.verts) else 1
    ob = _put(bm, name, col, (loc[0], loc[1], _gh(loc[0], loc[1]) - 0.03), None, smooth=False)
    if mats:
        ob.data.materials.append(mat_bark())
        ob.data.materials.append(mat_leaves())
    ob.rotation_euler[2] = rng.uniform(0, 6.28)
    return ob


def build_pines(collection=None, mats=True):
    col = collection or get_collection('Trees')
    spec = [(-3.1, 1.7, 3.1), (-2.2, 3.0, 2.5), (3.0, 2.3, 2.9), (3.8, 0.5, 2.1), (0.2, 3.6, 2.3)]
    return [build_pine('Pine.%02d' % i, (x, y), h, i + 1, col, mats) for i, (x, y, h) in enumerate(spec)]


# ------------------------------------------------------------------ world, lights, camera

def build_world_dusk(strength=0.6, top='#0e1740', mid='#58396e', horizon='#e07a38'):
    """A dusk gradient sky made of plain nodes (same result on every Blender version, cheap on the CPU).
    The sky mirrors below the horizon (Absolute), so a floating diorama sits in a glow, not a void."""
    w = kit.make_world((0.03, 0.04, 0.08, 1.0), strength)
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    tc = _node(nt, 'ShaderNodeTexCoord', (-1100, 0))
    sep = _node(nt, 'ShaderNodeSeparateXYZ', (-900, 0))
    ab = _node(nt, 'ShaderNodeMath', (-720, 0), operation='ABSOLUTE')
    mr = _node(nt, 'ShaderNodeMapRange', (-540, 0))
    mr.inputs['From Min'].default_value = 0.0         # |z| of the view direction: 0 = horizon, 1 = straight up
    mr.inputs['From Max'].default_value = 0.32
    ramp = _ramp(nt, (-280, 0), [(0.0, horizon), (0.4, mid), (1.0, top)])
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], ab.inputs[0])
    nt.links.new(ab.outputs['Value'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    return w


def build_lights(collection=None, with_lantern_light=True):
    col = collection or get_collection('Lights')
    sun = kit.add_light('SUN', 'Sun_Dusk', (-6, -5, 4.2), 2.2, (1.0, 0.62, 0.36), size=3, collection=col)
    kit.look_at(sun, (0, 0, 0.6))
    fill = kit.add_light('AREA', 'Fill_Blue', (6, 5, 5), 90, (0.5, 0.62, 1.0), size=7, collection=col)
    kit.look_at(fill, (0, 0, 1))
    out = {'sun': sun, 'fill': fill}
    if with_lantern_light:
        out['lantern'] = kit.add_light('POINT', 'Lantern_Light', (0.49, -2.15, 1.82 + _gh(1.15, -2.15)), 220, (1.0, 0.72, 0.4), size=0.08, collection=col)
        for i, x in enumerate((-1.2, 1.2)):
            out['win%d' % i] = kit.add_light('POINT', 'Window_Light.%d' % i, (x, -1.9, 1.5), 110, (1.0, 0.66, 0.32), size=0.1, collection=col)
    return out


def build_camera(lens=36.0, dof=True, collection=None):
    cam = kit.add_camera('Camera', (8.6, -10.8, 2.7), (0.2, 0.0, 1.5), lens, collection or get_collection('Lights'))
    if dof:
        d = cam.data.dof
        d.use_dof = True
        d.focus_distance = (Vector(cam.location) - Vector((0, -1.4, 1.2))).length
        d.aperture_fstop = 4.0
    return cam


def build_diorama(parts=('ground', 'tufts', 'path', 'cabin', 'post', 'rocks', 'trees', 'fence'), mats=True,
                  lights=True, camera=True, world=True, cpu='standard'):
    """The finished scene. Pass a subset of parts to get a half-built one (used by starters)."""
    kit.wipe()
    kit.reset_scene_settings()
    out = {}
    if world:
        build_world_dusk()
    else:
        kit.make_world()
    table = {'ground': build_ground, 'tufts': build_tufts, 'path': build_path, 'cabin': build_cabin,
             'post': build_lamp_post, 'rocks': build_rocks, 'trees': build_pines, 'fence': build_fence}
    for p in parts:
        out[p] = table[p](mats=mats)
    if lights:
        out['lights'] = build_lights()
    if camera:
        out['camera'] = build_camera()
    if cpu:
        matkit.cpu_preset(bpy.context.scene, cpu)
    return out
