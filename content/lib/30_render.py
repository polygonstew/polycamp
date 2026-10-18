# content/lib/30_render.py - compositor and quick studio helpers (works on Blender 3.3, 4.x and 5.x).


def comp_tree():
    """The scene's compositor node tree, created if needed. Blender 5 moved it to scene.compositing_node_group."""
    sc = bpy.context.scene
    if hasattr(sc, 'compositing_node_group'):
        if sc.compositing_node_group is None:
            sc.compositing_node_group = bpy.data.node_groups.new('Compositing', 'CompositorNodeTree')
        return sc.compositing_node_group
    sc.use_nodes = True
    return sc.node_tree


def add_glare(threshold=1.0):
    """A Glare node (fog glow / bloom) wired after the render layer: the glow around lamps and windows."""
    nt = comp_tree()
    g = nt.nodes.new('CompositorNodeGlare')
    for k, v in (('glare_type', 'FOG_GLOW'), ('threshold', threshold), ('quality', 'MEDIUM')):
        try:
            setattr(g, k, v)
        except Exception:
            pass
    try:
        rl = next((n for n in nt.nodes if n.type == 'R_LAYERS'), None) or nt.nodes.new('CompositorNodeRLayers')
        out = next((n for n in nt.nodes if n.type == 'COMPOSITE'), None) or nt.nodes.new('CompositorNodeComposite')
        nt.links.new(rl.outputs['Image'], g.inputs['Image'])
        nt.links.new(g.outputs['Image'], out.inputs['Image'])
    except Exception:
        pass
    return g


def auto_camera(objs, direction=(1.0, -1.15, 0.7), lens=50.0, margin=1.25, name='Camera'):
    """Place a camera that frames `objs` from `direction` (used for goal images and the studio helpers)."""
    pts = []
    for o in objs:
        for c in o.bound_box:
            pts.append(o.matrix_world @ Vector(c))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, radius = (lo + hi) / 2, (hi - lo).length / 2
    d = Vector(direction).normalized()
    cam = bpy.data.objects.get(name) or kit.add_camera(name, (0, 0, 0), (0, 0, 0), lens)
    cam.data.lens = lens
    dist = radius * margin / math.sin(math.atan(18.0 / lens))
    cam.location = centre + d * dist
    kit.look_at(cam, centre)
    bpy.context.scene.camera = cam
    return cam


def studio_lights(centre=(0, 0, 1), size=1.0):
    """Soft key, cool fill, warm rim: enough to show a model off."""
    k = kit.add_light('AREA', 'Studio_Key', (centre[0] + 3 * size, centre[1] - 4 * size, centre[2] + 4 * size), 350 * size * size, (1, 0.95, 0.9), size=3 * size)
    kit.look_at(k, centre)
    f = kit.add_light('AREA', 'Studio_Fill', (centre[0] - 4 * size, centre[1] - 3 * size, centre[2] + 1.5 * size), 120 * size * size, (0.75, 0.85, 1.0), size=4 * size)
    kit.look_at(f, centre)
    r = kit.add_light('AREA', 'Studio_Rim', (centre[0] - 1 * size, centre[1] + 4 * size, centre[2] + 3 * size), 220 * size * size, (1, 0.8, 0.6), size=2 * size)
    kit.look_at(r, centre)
    return k, f, r


def studio_world(top='#46506a', bottom='#14161d'):
    return build_world_dusk(1.0, top, bottom, '#2b3040')
