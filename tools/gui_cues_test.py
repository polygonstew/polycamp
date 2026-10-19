"""Run INSIDE a real (GUI) Blender, normally under a virtual display - see tools/gui_test.sh:

    sh tools/gui_test.sh /usr/bin/blender /tmp/gui-shots

Registers the add-on, fires every kind of highlight cue, takes a screenshot of each and checks that accent-coloured
pixels really appeared in the right place (compared with a screenshot taken with no cue). Also draws the sidebar panel
and presses the narration operator, so a drawing or operator error shows up. Prints PASS/FAIL lines.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "addon"))
OUT = (sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/polycamp-gui")
os.makedirs(OUT, exist_ok=True)

import bpy
import numpy as np

import polycamp_link as pl
from polycamp_link import cues, link

FAILS = []
print("== GUI Blender", bpy.app.version_string, flush=True)


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""), flush=True)
    if not cond:
        FAILS.append(name)


pl.register()
link.stop()                                   # no server in this test


def areas(kind):
    return [a for a in bpy.context.window_manager.windows[0].screen.areas if a.type == kind]


OFF = [0]            # rows between the bottom of the picture and the bottom of Blender's window


def _load(path):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def shot(name):
    path = os.path.join(OUT, name + ".png")
    px = None
    if bpy.app.version >= (4, 0, 0):      # 3.x's own screenshot blanks the window on Mesa's virtual display: use the X server
        bpy.ops.screen.screenshot(filepath=path)
        px = _load(path)
    OFF[0] = 0
    if px is None or not px.any():
        import subprocess
        subprocess.run(["import", "-window", "root", path], check=True)
        px = _load(path)
        OFF[0] = max(0, px.shape[0] - bpy.context.window.height)
    return px


def accent(px, area, sub=None):
    """How many accent-orange pixels are inside the area (optionally a sub-rectangle (x0, y0, x1, y1) of it)."""
    x0, y0, x1, y1 = (area.x, area.y, area.x + area.width, area.y + area.height) if sub is None else sub
    y0, y1 = y0 + OFF[0], y1 + OFF[0]
    a = px[max(0, y0):y1, max(0, x0):x1]
    m = (a[..., 0] > 0.85) & (a[..., 1] > 0.25) & (a[..., 1] < 0.6) & (a[..., 2] < 0.3)
    return int(m.sum())


V3D = areas("VIEW_3D")[0]
OUTL = areas("OUTLINER")[0]
PROP = areas("PROPERTIES")[0]
TIME = next(a for a in areas("DOPESHEET_EDITOR"))
SPACE3D = V3D.spaces.active
state = {}

# keymap present?
kc = bpy.context.window_manager.keyconfigs.addon
km = kc.keymaps.get("Window") if kc else None
check("narration shortcuts registered", bool(km) and sum(1 for k in km.keymap_items if k.idname == "polycamp.voice") == 3)
check("draw handlers installed", len(cues._handles) >= 8, len(cues._handles))

# fake a linked session so the sidebar panel has something to draw
link.S.connected = True
link.S.hud = {"level": {"n": 3, "title": "Vertex Pusher", "xp": 220}, "lesson": {"id": "transform", "title": "Grab, Rotate, Scale, Mean It"},
              "tasks": [{"id": "a", "title": "Move the cube exactly 3 m along X", "done": True, "checks": []},
                        {"id": "b", "title": "Rotate it 45 degrees around Z", "done": False, "checks": [{"label": "A mesh is rotated 45 degrees", "ok": False}]}]}
STEPS = []


def step(fn, wait=1.0):
    STEPS.append((fn, wait))


def s_baseline():
    state["base"] = shot("00_baseline")
    state["b3d"], state["bo"], state["bp"], state["bt"] = (accent(state["base"], a) for a in (V3D, OUTL, PROP, TIME))


def s_obj_keys():
    cues.set_cues([{"t": "obj", "m": "cube"}, {"t": "obj", "m": "camera"}, {"t": "keys", "seq": ["G", "X", "3", "Enter"]}], 6)


def s_obj_keys_check():
    px = shot("01_object_and_keys")
    check("object box + key caps appear in the 3D viewport", accent(px, V3D) - state["b3d"] > 400, accent(px, V3D) - state["b3d"])


def s_areas():
    cues.set_cues([{"t": "area", "space": "OUTLINER", "region": "WINDOW", "label": "Outliner"},
                   {"t": "area", "space": "PROPERTIES", "region": "WINDOW", "label": "Modifiers tab", "tab": "MODIFIERS"},
                   {"t": "area", "space": "TIMELINE", "region": "WINDOW", "label": "Timeline"}], 6, tabs=True)


def s_areas_check():
    px = shot("02_editor_outlines")
    check("Outliner outlined", accent(px, OUTL) - state["bo"] > 500, accent(px, OUTL) - state["bo"])
    check("Properties editor outlined", accent(px, PROP) - state["bp"] > 500, accent(px, PROP) - state["bp"])
    check("Timeline outlined", accent(px, TIME) - state["bt"] > 300, accent(px, TIME) - state["bt"])
    check("Properties switched to the Modifiers tab when asked", PROP.spaces.active.context.startswith("MODIFIER"), PROP.spaces.active.context)


def s_sidebar_closed():
    SPACE3D.show_region_ui = False
    cues.set_cues([{"t": "area", "space": "VIEW_3D", "region": "UI", "label": "Sidebar > Item", "tab": "Item"}], 6)


def s_sidebar_closed_check():
    px = shot("03_sidebar_closed")
    right = (V3D.x + V3D.width - 420, V3D.y + V3D.height // 2 - 40, V3D.x + V3D.width, V3D.y + V3D.height // 2 + 40)
    base = accent(state["base"], V3D, right)
    check("closed sidebar: a 'press N' tag is drawn", accent(px, V3D, right) - base > 150, accent(px, V3D, right) - base)


def s_sidebar_open():
    SPACE3D.show_region_ui = True
    cues.set_cues([{"t": "area", "space": "VIEW_3D", "region": "UI", "label": "Sidebar > Item", "tab": "Item"}], 6, tabs=True)


def s_sidebar_open_check():
    ui = next(r for r in V3D.regions if r.type == "UI")
    box = (ui.x, ui.y, ui.x + ui.width, ui.y + ui.height)
    px = shot("04_sidebar_open")
    check("open sidebar outlined", accent(px, V3D, box) - accent(state["base"], V3D, box) > 400, accent(px, V3D, box))
    if hasattr(ui, "active_panel_category"):                      # not in Blender 3.3
        check("sidebar switched to the Item tab", ui.active_panel_category == "Item", ui.active_panel_category)


def s_places():
    bpy.context.scene.cursor.location = (2.0, 1.0, 0.5)
    cues.set_cues([{"t": "cursor"}, {"t": "world_origin"}, {"t": "origin"}, {"t": "gizmo"}], 6)


def s_places_check():
    px = shot("05_cursor_origins_gizmo")
    check("cursor / origin / gizmo rings appear", accent(px, V3D) - state["b3d"] > 300, accent(px, V3D) - state["b3d"])
    bpy.context.scene.cursor.location = (0, 0, 0)


def s_panel():
    for r in V3D.regions:
        if r.type == "UI":
            try:
                r.active_panel_category = "Polycamp"
            except Exception:
                pass
    for a in bpy.context.window_manager.windows[0].screen.areas:
        a.tag_redraw()


def s_panel_check():
    shot("06_polycamp_panel")
    r = bpy.ops.polycamp.voice(action="toggle")          # no server: must warn, not raise
    check("narration operator runs without a server", "FINISHED" in r, r)


def s_expire():
    cues.set_cues([{"t": "area", "space": "OUTLINER", "region": "WINDOW", "label": "Outliner"}], 1.0)


def s_expire_check():
    check("cues expire on their own", cues.active() == [], cues.STATE)
    px = shot("07_after_expiry")
    check("expired cue is gone from the screen", accent(px, OUTL) - state["bo"] < 100, accent(px, OUTL) - state["bo"])


step(s_baseline, 1.5)
for a, b in ((s_obj_keys, s_obj_keys_check), (s_areas, s_areas_check), (s_sidebar_closed, s_sidebar_closed_check),
             (s_sidebar_open, s_sidebar_open_check), (s_places, s_places_check)):
    step(a, 1.2)
    step(b, 0.4)
    step(lambda: cues.set_cues([], 0), 0.6)
step(s_panel, 1.0)
step(s_panel_check, 0.4)
step(s_expire, 2.6)
step(s_expire_check, 0.2)


def runner():
    if not STEPS:
        print("== %s" % ("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS)), flush=True)
        pl.unregister()
        bpy.ops.wm.quit_blender()
        return None
    fn, wait = STEPS.pop(0)
    try:
        fn()
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("step %s ran" % getattr(fn, "__name__", "?"), False, e)
    return wait


bpy.app.timers.register(runner, first_interval=4.0)
