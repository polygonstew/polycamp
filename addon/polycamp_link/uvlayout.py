"""uvlayout.py - draw a mesh's UV layout to a PNG with numpy (no editor, no operators, any version).

Teal = covered once, red = overlapping islands, white lines = edges. The picture's top is v=1,
so it looks the same as Blender's UV Editor.
"""
import bpy


def _uv_arrays(me):
    import numpy as np
    layer = me.uv_layers.active
    if layer is None:
        raise ValueError("This object has no UV map yet. Select it, press Tab, select all (A) and unwrap with U.")
    n = len(me.loops)
    uv = np.empty(n * 2, dtype=np.float32)
    layer.data.foreach_get("uv", uv)
    start = np.empty(len(me.polygons), dtype=np.int32)
    total = np.empty(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("loop_start", start)
    me.polygons.foreach_get("loop_total", total)
    return uv.reshape(-1, 2), start, total


def _fill(cov, tri_uv, size):
    import numpy as np
    for tri in tri_uv:
        p = tri * (size - 1)
        x0, y0 = np.floor(p.min(axis=0)).astype(int)
        x1, y1 = np.ceil(p.max(axis=0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        (ax, ay), (bx, by), (cx, cy) = p
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        w1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        w3 = 1 - w1 - w2
        m = (w1 >= -0.001) & (w2 >= -0.001) & (w3 >= -0.001)
        cov[y0:y1 + 1, x0:x1 + 1][m] += 1


def _wire(img, uv, start, total, size, color):
    import numpy as np
    n = len(uv)
    nxt = np.arange(n, dtype=np.int32) + 1
    nxt[start + total - 1] = start
    a, b = uv * (size - 1), uv[nxt] * (size - 1)
    steps = np.maximum(np.abs(b - a).max(axis=1), 1).astype(int) + 1
    idx = np.repeat(np.arange(n), steps)
    t = (np.arange(steps.sum()) - np.repeat(np.cumsum(steps) - steps, steps)) / np.repeat(np.maximum(steps - 1, 1), steps)
    pts = a[idx] + (b[idx] - a[idx]) * t[:, None]
    px = np.rint(pts).astype(int)
    ok = (px[:, 0] >= 0) & (px[:, 0] < size) & (px[:, 1] >= 0) & (px[:, 1] < size)
    img[px[ok, 1], px[ok, 0]] = color


def render_layout(obj, path, size=1024):
    """Write the UV layout of `obj` to `path` (PNG). Returns a stats dict."""
    import numpy as np
    if obj.type != "MESH":
        raise ValueError("Pick a mesh object.")
    if obj.mode == "EDIT":
        obj.update_from_editmode()
    me = obj.data
    uv, start, total = _uv_arrays(me)
    if len(me.polygons) > 30000:
        raise ValueError("Too many faces for the live UV picture (limit 30,000).")
    tc = np.maximum(total - 2, 0)
    ntri = int(tc.sum())
    poly = np.repeat(np.arange(len(start)), tc)
    local = np.arange(ntri) - np.repeat(np.cumsum(tc) - tc, tc)
    a = start[poly]
    tri_uv = np.stack([uv[a], uv[a + 1 + local], uv[a + 2 + local]], axis=1)
    cov = np.zeros((size, size), dtype=np.int16)
    _fill(cov, tri_uv, size)
    img = np.zeros((size, size, 4), dtype=np.float32)
    img[...] = (0.07, 0.08, 0.10, 1.0)
    img[cov == 1] = (0.10, 0.52, 0.55, 1.0)
    img[cov >= 2] = (0.85, 0.20, 0.22, 1.0)
    _wire(img, uv, start, total, size, (0.95, 0.95, 0.95, 1.0))
    # grid ticks every tenth so scale is readable
    for k in range(0, size, size // 10):
        img[k, ::4] = (0.3, 0.3, 0.35, 1.0)
        img[::4, k] = (0.3, 0.3, 0.35, 1.0)
    im = bpy.data.images.new("pc_uv_layout", size, size, alpha=True)
    try:
        im.pixels.foreach_set(img.ravel())
        im.filepath_raw = path
        im.file_format = "PNG"
        im.save()
    finally:
        bpy.data.images.remove(im)
    oob = float(((uv < -0.0001) | (uv > 1.0001)).any(axis=1).mean())
    return {"size": size, "coverage": round(float((cov >= 1).mean()), 4), "overlap": round(float((cov >= 2).mean()), 4),
            "oob": round(oob, 4), "faces": int(len(start)), "object": obj.name}
