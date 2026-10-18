# content/lib/20_uv.py - UV and texture helpers for the UV Isle lessons (barrel builder, seam net, tiny test images).
import numpy as _np


def uv_cylinder(bm, segs=16):
    """Unwrap a cylinder into: one side strip (top half of the tile) and two cap discs (bottom half). No overlaps."""
    layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        if abs(n.z) > 0.9:                                  # caps
            cx = 0.27 if n.z > 0 else 0.73
            for lp in f.loops:
                lp[layer].uv = (cx + lp.vert.co.x * 0.48, 0.26 + lp.vert.co.y * 0.48)
        else:
            c = f.calc_center_median()
            tc = (math.atan2(c.y, c.x) / (2 * math.pi)) % 1.0
            for lp in f.loops:
                t = (math.atan2(lp.vert.co.y, lp.vert.co.x) / (2 * math.pi)) % 1.0
                if t < tc - 0.5:
                    t += 1.0
                elif t > tc + 0.5:
                    t -= 1.0
                lp[layer].uv = (t, 0.52 + lp.vert.co.z * 0.46)


def mark_seam_net(bm):
    """Mark a minimal set of seams that lets the mesh unfold flat: everything not on a spanning tree of the faces."""
    bm.faces.ensure_lookup_table()
    seen, tree = {bm.faces[0].index}, set()
    todo = [bm.faces[0]]
    while todo:
        f = todo.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g.index not in seen:
                    seen.add(g.index)
                    tree.add(e.index)
                    todo.append(g)
    for e in bm.edges:
        e.seam = e.index not in tree


def build_barrel(name='Barrel', loc=(0, 0, 0), collection=None, uv=True, segs=16, mat=None):
    bm = bmesh.new()
    kit.add_cylinder(bm, 0.5, 1.0, segs, center=(0, 0, 0.5))
    if uv:
        uv_cylinder(bm, segs)
    ob = kit.mesh_object(name, bm, collection=collection, loc=loc)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob


def make_test_image(path, kind='base_color', size=64):
    """Write a small PNG that stands in for a Texture Lab map (planks for colour, flat blue for normals...)."""
    a = _np.zeros((size, size, 4), dtype=_np.float32)
    a[..., 3] = 1.0
    xs = _np.linspace(0, 1, size)
    stripe = (_np.floor(xs * 6) % 2)[None, :] * _np.ones((size, 1))
    if kind == 'base_color':
        a[..., 0], a[..., 1], a[..., 2] = 0.45 + 0.2 * stripe, 0.28 + 0.12 * stripe, 0.12 + 0.06 * stripe
    elif kind == 'normal':
        a[..., 0], a[..., 1], a[..., 2] = 0.5, 0.5, 1.0
    else:
        a[..., 0] = a[..., 1] = a[..., 2] = 0.5 + 0.2 * stripe
    im = bpy.data.images.new('pc_test_' + kind, size, size, alpha=True)
    im.pixels.foreach_set(a.ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    return path
