"""cues.py - "look here" marks drawn on Blender's own screen while the narration talks about them.

The app sends a `cue` command with a small list of cues and a time-to-live; this module remembers them and a few
draw handlers paint them over the editors: an outline and a tag around an editor or region (sidebar, Outliner,
Properties...), a box around objects, a ring at the 3D cursor or an origin, a ring at the navigation gizmo, and key
caps along the bottom of the viewport for the shortcut being spoken. Nothing is changed in the scene, and everything
disappears by itself when the time is up.

Cue shapes (from server/speech.py):
  {"t":"area","space":"VIEW_3D","region":"UI|TOOLS|HEADER|WINDOW","label":"...","tab":"Item"}
  {"t":"obj","m":"cube"} | {"t":"obj","sel":true} | {"t":"obj","active":true}
  {"t":"cursor"} {"t":"world_origin"} {"t":"origin"} {"t":"gizmo"} {"t":"keys","seq":["Ctrl+A"]}
"""
import math
import time

import bpy

from . import compat

ACC = (1.0, 0.42, 0.10, 1.0)
INK = (0.10, 0.05, 0.01, 1.0)
CAP = (0.13, 0.12, 0.09, 0.96)
TXT = (0.93, 0.90, 0.83, 1.0)

STATE = {"cues": [], "until": 0.0, "t0": 0.0, "src": "", "errors": 0}
BANNER = {"text": "", "until": 0.0}                   # one line across the top of the 3D viewport (the hotkey drill uses it)
_handles = []          # (space class, region type, handle)
_shader = None

# (bpy.types name, region types we may paint in)
SPACES = [("SpaceView3D", ("WINDOW", "UI", "TOOLS", "HEADER")), ("SpaceProperties", ("WINDOW",)),
          ("SpaceOutliner", ("WINDOW",)), ("SpaceDopeSheetEditor", ("WINDOW",)), ("SpaceGraphEditor", ("WINDOW",)),
          ("SpaceNodeEditor", ("WINDOW",)), ("SpaceImageEditor", ("WINDOW",)), ("SpaceSequenceEditor", ("WINDOW",)),
          ("SpaceTextEditor", ("WINDOW",)), ("SpaceSpreadsheet", ("WINDOW",))]
AREA_OF = {"TIMELINE": "DOPESHEET_EDITOR"}
TYPE_WORDS = {"camera": "CAMERA", "light": "LIGHT", "lamp": "LIGHT", "empty": "EMPTY", "armature": "ARMATURE",
              "curve": "CURVE", "text": "FONT"}
NAME_ALIAS = {"monkey": "suzanne", "lamp": "light"}


# ------------------------------------------------------------------ state
def active():
    return STATE["cues"] if STATE["cues"] and time.time() < STATE["until"] else []


def set_cues(cues, ttl=8.0, tabs=False):
    """Show these cues for `ttl` seconds (an empty list clears). Returns how many were accepted."""
    cues = [c for c in (cues or []) if isinstance(c, dict)][:6]
    STATE.update(cues=cues, until=time.time() + max(0.5, float(ttl)) if cues else 0.0, t0=time.time())
    if cues:
        if tabs:
            _switch_tabs(cues)
        if not bpy.app.timers.is_registered(_tick):
            bpy.app.timers.register(_tick, first_interval=0.4)
    _redraw()
    return len(cues)


def set_banner(text, ttl=0.0):
    """A message across the top of every 3D viewport for `ttl` seconds ('' clears it)."""
    BANNER.update(text=text, until=time.time() + float(ttl) if text else 0.0)
    _redraw()


def _tick():
    if not active():
        STATE["cues"] = []
        _redraw()
        return None
    _redraw()
    return min(0.5, max(0.1, STATE["until"] - time.time()))


def _redraw():
    try:
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                area.tag_redraw()
    except Exception:
        pass


def _switch_tabs(cues):
    """Optional (preference): bring the named Properties tab / sidebar tab to the front."""
    try:
        for win in bpy.context.window_manager.windows:
            for area in win.screen.areas:
                for c in cues:
                    if c.get("t") != "area" or not c.get("tab"):
                        continue
                    if area.type == "PROPERTIES" and c.get("space") == "PROPERTIES":
                        # Blender 5 calls the tabs MODIFIER / CONSTRAINT where 3.x and 4.x say MODIFIERS / CONSTRAINTS
                        for tab in dict.fromkeys((c["tab"], c["tab"].rstrip("S"), c["tab"] + "S")):
                            try:
                                area.spaces.active.context = tab
                                break
                            except (TypeError, AttributeError):
                                continue                    # not a tab in this version, or not for this object
                    elif area.type == "VIEW_3D" and c.get("region") == "UI":
                        for r in area.regions:
                            if r.type == "UI":
                                try:
                                    r.active_panel_category = c["tab"]
                                except (TypeError, AttributeError):
                                    pass
    except Exception:
        pass


# ------------------------------------------------------------------ drawing primitives (filled quads only: wide lines
# aren't available on every GPU backend)
def _sh():
    global _shader
    if _shader is None:
        import gpu
        for name in ("UNIFORM_COLOR", "2D_UNIFORM_COLOR"):
            try:
                _shader = gpu.shader.from_builtin(name)
                break
            except Exception:
                continue
    return _shader


def _fill(rects, col):
    """rects: [(x0, y0, x1, y1)] in region pixels."""
    import gpu
    from gpu_extras.batch import batch_for_shader
    sh = _sh()
    if sh is None or not rects:
        return
    pts = []
    for x0, y0, x1, y1 in rects:
        pts += [(x0, y0), (x1, y0), (x1, y1), (x0, y0), (x1, y1), (x0, y1)]
    b = batch_for_shader(sh, "TRIS", {"pos": pts})
    sh.bind()
    sh.uniform_float("color", col)
    gpu.state.blend_set("ALPHA")
    b.draw(sh)


def _frame_rects(x0, y0, x1, y1, t):
    return [(x0, y0, x1, y0 + t), (x0, y1 - t, x1, y1), (x0, y0 + t, x0 + t, y1 - t), (x1 - t, y0 + t, x1, y1 - t)]


def _brackets(x0, y0, x1, y1, t, arm):
    r = []
    for cx, sx in ((x0, 1), (x1, -1)):
        for cy, sy in ((y0, 1), (y1, -1)):
            r.append((min(cx, cx + sx * arm), min(cy, cy + sy * t), max(cx, cx + sx * arm), max(cy, cy + sy * t)))
            r.append((min(cx, cx + sx * t), min(cy, cy + sy * arm), max(cx, cx + sx * t), max(cy, cy + sy * arm)))
    return r


def _ring(cx, cy, r, t, col, seg=36):
    import gpu
    from gpu_extras.batch import batch_for_shader
    sh = _sh()
    if sh is None:
        return
    pts = []
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        o0 = (cx + math.cos(a0) * (r + t), cy + math.sin(a0) * (r + t))
        o1 = (cx + math.cos(a1) * (r + t), cy + math.sin(a1) * (r + t))
        i0 = (cx + math.cos(a0) * r, cy + math.sin(a0) * r)
        i1 = (cx + math.cos(a1) * r, cy + math.sin(a1) * r)
        pts += [o0, o1, i1, o0, i1, i0]
    b = batch_for_shader(sh, "TRIS", {"pos": pts})
    sh.bind()
    sh.uniform_float("color", col)
    gpu.state.blend_set("ALPHA")
    b.draw(sh)


def _scale():
    try:
        return max(0.75, float(bpy.context.preferences.system.ui_scale))
    except Exception:
        return 1.0


def _text(x, y, s, size, col):
    import blf
    compat.set_blf_size(0, size)
    blf.color(0, *col)
    blf.position(0, x, y, 0)
    blf.draw(0, s)


def _text_w(s, size):
    import blf
    compat.set_blf_size(0, size)
    return blf.dimensions(0, s)


def _tag(x, y_top, label, fade, anchor="left", w_max=None):
    """A filled label tag hanging from (x, y_top). Returns its rect."""
    us = _scale()
    size = 13 * us
    tw, th = _text_w(label, size)
    pad = 7 * us
    w, hgt = tw + 2 * pad, th + 10 * us
    if w_max:
        w = min(w, w_max)
    x0 = x if anchor == "left" else x - w
    y0 = y_top - hgt
    _fill([(x0, y0, x0 + w, y0 + hgt)], (ACC[0], ACC[1], ACC[2], 0.97 * fade))
    _text(x0 + pad, y0 + 5 * us, label, size, (INK[0], INK[1], INK[2], fade))
    return x0, y0, x0 + w, y0 + hgt


def _outline(x0, y0, x1, y1, label, fade):
    us = _scale()
    _fill([(x0, y0, x1, y1)], (ACC[0], ACC[1], ACC[2], 0.06 * fade))
    _fill(_frame_rects(x0, y0, x1, y1, 3 * us), (ACC[0], ACC[1], ACC[2], 0.95 * fade))
    if label:
        _tag(x0 + 3 * us, y1 - 3 * us, label, fade)


# ------------------------------------------------------------------ objects / places
def match_objects(view_layer, cue):
    objs = list(view_layer.objects)
    if cue.get("sel"):
        return [o for o in objs if o.select_get(view_layer=view_layer)][:6]
    if cue.get("active"):
        a = view_layer.objects.active
        return [a] if a else []
    m = str(cue.get("m", "")).lower()
    m = NAME_ALIAS.get(m, m)
    if not m:
        return []
    return [o for o in objs if m in o.name.lower() or o.type == TYPE_WORDS.get(m)][:6]


def _to_2d(region, rv3d, co):
    from bpy_extras import view3d_utils
    return view3d_utils.location_3d_to_region_2d(region, rv3d, co)


def _object_rect(region, rv3d, ob, us):
    from mathutils import Vector
    pts = [p for p in (_to_2d(region, rv3d, ob.matrix_world @ Vector(c)) for c in ob.bound_box) if p is not None]
    if not pts:
        return None
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half_w, half_h = max((max(xs) - min(xs)) / 2 + 8 * us, 24 * us), max((max(ys) - min(ys)) / 2 + 8 * us, 24 * us)
    return cx - half_w, cy - half_h, cx + half_w, cy + half_h


def _gizmo_center(area, region, us):
    side = next((r.width for r in area.regions if r.type == "UI" and r.width > 1), 0)
    top = sum(r.height for r in area.regions if r.type in ("HEADER", "TOOL_HEADER") and r.height > 1)
    return region.width - side - 58 * us, region.height - top - 72 * us


def _keycaps(region, seq, fade, us):
    size = 20 * us
    caps = []
    for k in seq:
        label = " + ".join(p.strip() for p in str(k).split("+") if p.strip()) or str(k)
        caps.append((label, _text_w(label, size)[0] + 26 * us))
    gap = 10 * us
    total = sum(w for _, w in caps) + gap * (len(caps) - 1)
    x, y, hgt = (region.width - total) / 2, 70 * us, 44 * us
    for label, w in caps:
        _fill([(x - 2 * us, y - 2 * us, x + w + 2 * us, y + hgt + 2 * us)], (ACC[0], ACC[1], ACC[2], fade))
        _fill([(x, y, x + w, y + hgt)], (CAP[0], CAP[1], CAP[2], CAP[3] * fade))
        _text(x + 13 * us, y + 13 * us, label, size, (TXT[0], TXT[1], TXT[2], fade))
        x += w + gap


def _draw_view3d_window(ctx, cues, fade, us):
    area, region, sp = ctx.area, ctx.region, ctx.space_data
    rv3d = getattr(sp, "region_3d", None)
    for c in cues:
        t = c.get("t")
        if t == "obj" and rv3d:
            for ob in match_objects(ctx.view_layer, c):
                if not ob.visible_get():
                    continue
                r = _object_rect(region, rv3d, ob, us)
                if r:
                    _fill(_frame_rects(*r, 2 * us), (ACC[0], ACC[1], ACC[2], 0.9 * fade))
                    _fill(_brackets(*r, 5 * us, 14 * us), (ACC[0], ACC[1], ACC[2], fade))
                    _tag(r[0], r[1] - 2 * us, ob.name, fade)
        elif t in ("cursor", "world_origin", "origin") and rv3d:
            if t == "cursor":
                co, label = ctx.scene.cursor.location, "3D cursor"
            elif t == "world_origin":
                co, label = (0.0, 0.0, 0.0), "World origin"
            else:
                a = ctx.view_layer.objects.active
                if a is None:
                    continue
                co, label = a.matrix_world.translation, "Object origin"
            from mathutils import Vector
            p = _to_2d(region, rv3d, Vector(co))
            if p is not None:
                _ring(p.x, p.y, 20 * us, 3 * us, (ACC[0], ACC[1], ACC[2], fade))
                _tag(p.x + 26 * us, p.y + 10 * us, label, fade)
        elif t == "gizmo":
            cx, cy = _gizmo_center(area, region, us)
            _ring(cx, cy, 50 * us, 3 * us, (ACC[0], ACC[1], ACC[2], fade))
            _tag(cx, cy - 56 * us, "Navigation gizmo", fade, anchor="right")
        elif t == "keys" and c.get("seq"):
            _keycaps(region, c["seq"][:7], fade, us)
        elif t == "area" and c.get("space") == "VIEW_3D":
            reg = c.get("region", "WINDOW")
            flag = {"UI": "show_region_ui", "TOOLS": "show_region_toolbar", "HEADER": "show_region_header"}.get(reg)
            if flag and not getattr(sp, flag, True):        # the thing they should look at is hidden: say how to open it
                how = {"UI": "Sidebar is closed. Press N", "TOOLS": "Toolbar is closed. Press T", "HEADER": "Header is hidden"}[reg]
                edge = region.width - 4 * us if reg == "UI" else 4 * us
                _tag(edge, region.height / 2, how, fade, anchor="right" if reg == "UI" else "left")


def _area_matches(area, sp, cue):
    want = AREA_OF.get(cue.get("space"), cue.get("space"))
    if area.type != want:
        return False
    if cue.get("space") == "TIMELINE":
        return getattr(sp, "mode", "") == "TIMELINE"
    return True


def _draw(region_type):
    try:
        ctx = bpy.context
        area, region, sp = ctx.area, ctx.region, ctx.space_data
        if area is None or region is None:
            return
        us = _scale()
        if BANNER["text"] and time.time() < BANNER["until"] and region_type == "WINDOW" and area.type == "VIEW_3D":
            size = 15 * us
            tw = _text_w(BANNER["text"], size)[0]
            x0, y1 = (region.width - tw) / 2 - 12 * us, region.height - 44 * us
            _fill([(x0, y1 - 30 * us, x0 + tw + 24 * us, y1)], (ACC[0], ACC[1], ACC[2], 0.97))
            _text(x0 + 12 * us, y1 - 21 * us, BANNER["text"], size, INK)
        cues = active()
        if not cues:
            return
        fade = min(1.0, (time.time() - STATE["t0"]) / 0.18)
        for c in cues:
            if c.get("t") == "area" and region.type == c.get("region", "WINDOW") and _area_matches(area, sp, c):
                _outline(0, 0, region.width, region.height, c.get("label", ""), fade)
        if region_type == "WINDOW" and area.type == "VIEW_3D":
            _draw_view3d_window(ctx, cues, fade, us)
    except Exception:
        STATE["errors"] += 1
        if STATE["errors"] == 5:
            print("polycamp cues: drawing keeps failing, switching the highlights off")
            import traceback
            traceback.print_exc()
            STATE["cues"] = []


# ------------------------------------------------------------------ register
def register():
    if bpy.app.background:
        return
    for name, regions in SPACES:
        cls = getattr(bpy.types, name, None)
        if cls is None or not hasattr(cls, "draw_handler_add"):
            continue
        for rt in regions:
            try:
                _handles.append((cls, rt, cls.draw_handler_add(_draw, (rt,), rt, "POST_PIXEL")))
            except Exception as e:                              # a region type this Blender doesn't know
                print("polycamp cues: no", name, rt, e)


def unregister():
    for cls, rt, h in _handles:
        try:
            cls.draw_handler_remove(h, rt)
        except Exception:
            pass
    _handles.clear()
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    STATE["cues"] = []
