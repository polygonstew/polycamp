#!/usr/bin/env python3
"""The whole narration chain on real software: headless Chromium plays a lesson aloud, the server forwards the
highlight cues over the live link, and a real (GUI) Blender on a virtual display receives and draws them. Also presses the
add-on's Narration button in Blender and checks the page reacts.

    /usr/bin/python3 tools/gui_e2e.py [blender-binary] [outdir]        (Linux: needs xvfb-run, chromium, the voice engine)
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER = sys.argv[1] if len(sys.argv) > 1 else "blender"
OUT = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix="pc-gui-e2e-")
PORT = 8575
BASE = "http://127.0.0.1:%d" % PORT
FAILS = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what, flush=True)
    if not ok:
        FAILS.append(what)


def api(path, data=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def touch(name):
    open(os.path.join(OUT, name), "w").close()


def wait_for(fn, secs, step=0.4):
    end = time.time() + secs
    while time.time() < end:
        try:
            if fn():
                return True
        except OSError:                       # the server is still starting
            pass
        time.sleep(step)
    return False


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    cfg = tempfile.mkdtemp(prefix="pc-gui-cfg-")
    env = dict(os.environ, BLENDER_USER_CONFIG=cfg, LIBGL_ALWAYS_SOFTWARE="1", MESA_GL_VERSION_OVERRIDE="4.5", MESA_GLSL_VERSION_OVERRIDE="450")
    open(os.path.join(cfg, "p.py"), "w").write("import bpy\nbpy.context.preferences.view.show_splash = False\nbpy.ops.wm.save_userpref()\n")
    subprocess.run([BLENDER, "-b", "--factory-startup", "--python", os.path.join(cfg, "p.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "polycamp.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           env=dict(os.environ, POLYCAMP_DATA=tempfile.mkdtemp(prefix="pc-gui-data-"), POLYCAMP_PORT=str(PORT)))
    log = open(os.path.join(OUT, "blender.log"), "w")
    bl = None
    events = []

    def listen():                                               # collect voice_ctl events the way a page would
        try:
            r = urllib.request.urlopen(BASE + "/api/events", timeout=120)
            for raw in r:
                if raw.startswith(b"data:") and b"voice_ctl" in raw:
                    events.append(json.loads(raw[5:]))
        except Exception:
            pass
    try:
        if not wait_for(lambda: api("/api/state"), 12):
            raise SystemExit("server did not start")
        if not api("/api/voice/status")["installed"]:
            raise SystemExit("voice engine not installed (tools/install_voice.py)")
        api("/api/settings", {"voice_speed": 1.75})
        bl = subprocess.Popen(["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24 +extension GLX +render -noreset", BLENDER, "--python",
                               os.path.join(ROOT, "tools", "gui_e2e_blender.py"), "--", BASE, OUT], env=env, stdout=log, stderr=subprocess.STDOUT)
        check(wait_for(lambda: api("/api/bridge/status")["connected"], 90), "the GUI Blender linked to the server")
        blender_log = lambda: open(os.path.join(OUT, "blender.log")).read()
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--mute-audio"])
            pg = b.new_context(viewport={"width": 1500, "height": 900}).new_page()
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(BASE + "/#/lesson/transform")
            pg.wait_for_selector(".narr button.pri:has-text('Listen')", timeout=15000)
            pg.locator(".narr button.pri", has_text="Listen").click()
            pg.wait_for_selector(".narr.playing", timeout=120000)
            check(True, "the page started reading the lesson")
            # the intro mentions the 3D cursor; the narrator should have sent that highlight to Blender
            check(wait_for(lambda: '"t": "cursor"' in blender_log(), 90), "Blender received the 3D-cursor highlight while the intro was read")
            touch("shot")
            check(wait_for(lambda: "SHOT_TAKEN" in blender_log(), 20), "Blender took a screenshot")
            # play a task: its key caps and object boxes should arrive
            pg.locator(".narr .tick.k-task").first.click()
            check(wait_for(lambda: '"t": "keys"' in blender_log() and '"m": "cube"' in blender_log(), 120), "the first task's key caps and cube box reached Blender")
            pg.wait_for_selector(".narr.waiting", timeout=120000)
            # now press Narration > next inside Blender: the owning page must react
            threading.Thread(target=listen, daemon=True).start()
            time.sleep(1.0)
            before = pg.locator(".narr .tick.now").evaluate("e => [...e.parentNode.children].indexOf(e)")
            touch("press")
            check(wait_for(lambda: "PRESSED" in blender_log(), 20), "the Narration button ran inside Blender")
            check(wait_for(lambda: any(e.get("action") == "next" for e in events), 10), "the server published the button press")
            pg.wait_for_timeout(1500)
            after = pg.locator(".narr .tick.now").evaluate("e => [...e.parentNode.children].indexOf(e)")
            check(after != before, "the page moved to the next part (%d -> %d)" % (before, after))
            check(not errors, "no JS errors" + ("" if not errors else ": " + errors[0]))
            b.close()
        shot = os.path.join(OUT, "blender.png")
        check(os.path.exists(shot) and os.path.getsize(shot) > 50000, "screenshot of Blender saved")
        check("Traceback" not in blender_log(), "no Python errors inside Blender")
        touch("quit")
    finally:
        for pr in (bl, srv):
            if pr and pr.poll() is None:
                pr.terminate()
        try:
            subprocess.run(["rm", "-rf", cfg])
        except Exception:
            pass
    print("outputs in", OUT)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
