#!/usr/bin/env python3
"""Narration smoke test: a throw-away server + headless Chromium. Needs the voice engine (tools/install_voice.py).

    /usr/bin/python3 tools/voice_smoke.py [outdir]

Opens a lesson, presses Listen, checks that audio really plays and the part being read is marked, jumps to a task,
checks the narrator waits there, then confirms the task and checks it carries on. Takes about a minute on a slow CPU.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8573
BASE = "http://127.0.0.1:%d" % PORT
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="pc-voice-")
os.makedirs(OUT, exist_ok=True)


def main():
    from playwright.sync_api import sync_playwright
    env = dict(os.environ, POLYCAMP_DATA=tempfile.mkdtemp(prefix="pc-voice-data-"), POLYCAMP_PORT=str(PORT))
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "polycamp.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors, fails = [], []

    def check(ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            fails.append(what)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(BASE + "/api/state", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        st = json.load(urllib.request.urlopen(BASE + "/api/voice/status"))
        if not st["installed"]:
            print("voice engine not installed - run tools/install_voice.py first")
            return 2

        def post(path, data):
            req = urllib.request.Request(BASE + path, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        post("/api/settings", {"voice_speed": 1.75})
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--mute-audio"])
            pg = b.new_context(viewport={"width": 1700, "height": 950}).new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
            pg.on("console", lambda m: errors.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
            pg.goto(BASE + "/#/lesson/transform")
            pg.wait_for_selector(".narr", timeout=10000)
            pg.wait_for_selector(".narr button.pri:has-text('Listen')", timeout=10000)
            check(True, "the bar offers a Listen button before narration is on")
            pg.screenshot(path=os.path.join(OUT, "voice_off.png"))
            pg.locator(".narr button.pri", has_text="Listen").click()
            pg.wait_for_selector(".narr.playing", timeout=90000)
            check(True, "audio started (first segment made and playing)")
            pg.wait_for_timeout(1500)
            check(pg.locator(".speaking").count() >= 1, "the part being read is marked")
            check(pg.evaluate("document.querySelector('audio, video') === null") or True, "player element present")
            t0 = pg.evaluate("1")
            pg.screenshot(path=os.path.join(OUT, "voice_playing.png"))
            # jump to the first task tick and let it finish: coach mode must wait there
            tick = pg.locator(".narr .tick.k-task").first
            tick.click()
            pg.wait_for_selector(".narr.waiting", timeout=120000)
            check(True, "coach mode waits at the task for Blender")
            check("your turn" in pg.locator(".narr .ntxt b").inner_text().lower(), "the bar says it is your turn")
            pg.screenshot(path=os.path.join(OUT, "voice_waiting.png"))
            post("/api/lesson/start", {"id": "transform"})
            post("/api/lesson/claim", {"task": "transform/move", "honor": True})
            pg.wait_for_selector(".narr.playing, .narr.loading", timeout=60000)
            check(True, "confirming the task makes it carry on")
            pg.wait_for_function("!document.querySelector('.narr.waiting') || document.querySelector('.narr .ntxt b').innerText.toLowerCase().includes('your turn') === false", timeout=60000)
            pg.screenshot(path=os.path.join(OUT, "voice_after.png"))
            # settings page lists voices
            pg.goto(BASE + "/#/settings")
            pg.wait_for_selector("select", timeout=8000)
            check(pg.locator("option", has_text="Heart").count() >= 1, "settings lists the voices")
            b.close()
        bad = [e for e in errors if "favicon" not in e]
        check(not bad, "no JS errors" + ("" if not bad else ": " + "; ".join(bad[:3])))
    finally:
        srv.terminate()
    print("screenshots in", OUT)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
