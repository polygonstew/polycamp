"""Run INSIDE a real (GUI) Blender started with --enable-event-simulate (tools/gui_test.sh does this):

    sh tools/gui_test.sh /usr/bin/blender /tmp/gui-keys gui_keys_test.py

Checks the key relay for the hotkey drills: while watching is on, keys pressed in Blender are reported to the app in the drill's
own words; in pass-through mode Blender still acts on them, in swallow mode (a Dojo round) it does not and shows a banner;
and the watch switches itself off after its time is up.
"""
import http.server
import json
import os
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "addon"))

import bpy

import polycamp_link as pl
from polycamp_link import commands, cues, keywatch, link

FAILS = []
print("== GUI Blender", bpy.app.version_string, flush=True)


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (" " + str(extra) if extra and not cond else ""), flush=True)
    if not cond:
        FAILS.append(name)


# a stand-in for the app: remembers every combo posted to /api/bridge/keys
got = []


class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path == "/api/bridge/keys":
            got.append(json.loads(body)["combo"])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
pl.register()
link.stop()
link.S.server = "http://127.0.0.1:%d" % srv.server_address[1]


class Ev:
    def __init__(self, type, ctrl=False, alt=False, shift=False, oskey=False):
        self.type, self.ctrl, self.alt, self.shift, self.oskey = type, ctrl, alt, shift, oskey


for ev, want in [(Ev("A", shift=True), "Shift+A"), (Ev("NUMPAD_7"), "Numpad 7"), (Ev("NUMPAD_PERIOD"), "Numpad ."),
                 (Ev("NUMPAD_PLUS", ctrl=True), "Ctrl+Numpad +"), (Ev("TWO", ctrl=True), "Ctrl+2"), (Ev("F12"), "F12"),
                 (Ev("ESC"), "Esc"), (Ev("RET"), "Enter"), (Ev("TAB", ctrl=True), "Ctrl+Tab"), (Ev("PERIOD"), "."),
                 (Ev("SLASH"), "/"), (Ev("LEFT_ARROW"), "Left"), (Ev("G"), "G"), (Ev("Z", alt=True), "Alt+Z"),
                 (Ev("LEFTMOUSE"), None), (Ev("LEFT_SHIFT"), None), (Ev("TIMER"), None)]:
    check("combo_of %s -> %s" % (ev.type, want), keywatch.combo_of(ev) == want, keywatch.combo_of(ev))

win = bpy.context.window_manager.windows[0]
area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
cx, cy = area.x + area.width // 2, area.y + area.height // 2
rv3d = area.spaces.active.region_3d
mem = {}


def press(**kw):
    win.event_simulate(x=cx, y=cy, value="PRESS", **kw)         # needs Blender started with --enable-event-simulate


def view():
    return tuple(round(v, 3) for v in rv3d.view_rotation)


def s_start():
    mem["v0"] = view()
    r = commands.run({"id": 1, "cmd": "keywatch", "args": {"on": True, "ttl": 20}})
    check("keywatch command accepted", r["ok"], r)


def s_press_pass():
    press(type="NUMPAD_7")
    press(type="Z", alt=True)


def s_check_pass():
    check("pass-through: keys reported", got == ["Numpad 7", "Alt+Z"], got)
    check("pass-through: Blender still acted (top view, x-ray on)", view() != mem["v0"] and area.spaces.active.shading.show_xray, (view(), mem["v0"]))
    mem["top"] = view()
    got.clear()
    commands.run({"id": 2, "cmd": "keywatch", "args": {"on": True, "ttl": 4, "swallow": True}})


def s_press_swallow():
    press(type="NUMPAD_1")


def s_check_swallow():
    check("swallow: the key was still reported", got == ["Numpad 1"], got)
    check("swallow: Blender did NOT act on it", view() == mem["top"], (view(), mem["top"]))
    check("swallow: a banner says Blender is ignoring keys", bool(cues.BANNER["text"]), cues.BANNER)
    got.clear()


def s_wait():
    pass


def s_check_expired():
    check("the watcher switched itself off", not keywatch.STATE["running"], keywatch.STATE)
    check("the banner is gone", not cues.BANNER["text"], cues.BANNER)
    press(type="NUMPAD_1")


def s_check_after():
    check("after it stopped: nothing is reported", got == [], got)
    check("after it stopped: Blender acts on keys again", view() != mem["top"], view())
    commands.run({"id": 3, "cmd": "keywatch", "args": {"on": True, "ttl": 3}})
    commands.run({"id": 4, "cmd": "keywatch", "args": {"on": False}})


def s_check_off():
    time.sleep(0.2)
    check("an explicit off stops it", not keywatch.STATE["running"], keywatch.STATE)


steps = [(s_start, 1.0), (s_press_pass, 1.2), (s_check_pass, 1.0), (s_press_swallow, 1.0), (s_check_swallow, 6.5),
         (s_check_expired, 1.2), (s_check_after, 1.5), (s_check_off, 0.2)]


def runner():
    if not steps:
        print("== %s" % ("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS)), flush=True)
        pl.unregister()
        bpy.ops.wm.quit_blender()
        return None
    fn, wait = steps.pop(0)
    try:
        fn()
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("step %s ran" % fn.__name__, False, e)
    return wait


bpy.app.timers.register(runner, first_interval=4.0)
