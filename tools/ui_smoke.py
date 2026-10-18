#!/usr/bin/env python3
"""Headless-browser smoke test: loads every page against a throw-away server, fails on JS errors, takes screenshots.

    /usr/bin/python3 tools/ui_smoke.py [outdir]          (needs python playwright + /usr/bin/chromium)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8572
BASE = "http://127.0.0.1:%d" % PORT
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="pc-shots-")
os.makedirs(OUT, exist_ok=True)
PAGES = ["", "world/boot", "lesson/link-up", "dojo", "lab", "uv", "trophies", "badges", "settings", "link", "hud", "ref"]


def main():
    from playwright.sync_api import sync_playwright
    data = tempfile.mkdtemp(prefix="pc-ui-")
    env = dict(os.environ, POLYCAMP_DATA=data, POLYCAMP_PORT=str(PORT))
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "polycamp.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors = []
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(BASE + "/api/state", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        def post(path, data):
            req = urllib.request.Request(BASE + path, data=__import__("json").dumps(data).encode(), headers={"Content-Type": "application/json"})
            return urllib.request.urlopen(req, timeout=20).read()
        post("/api/lesson/start", {"id": "link-up"})                      # give the screens some progress to draw
        for t in ("linked", "rename"):
            post("/api/lesson/claim", {"task": "link-up/" + t, "honor": True})
        post("/api/answer", {"id": "link-up/q1", "value": [1]})
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            ctx = b.new_context(viewport={"width": 1700, "height": 950})
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
            pg.on("console", lambda m: errors.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
            for path in PAGES:
                pg.goto("%s/#/%s" % (BASE, path))
                pg.wait_for_timeout(900)
                name = (path or "home").replace("/", "_")
                pg.screenshot(path=os.path.join(OUT, name + ".png"))
                print("ok", path or "home", "->", pg.title())
            # lesson widgets: pick the right quiz option in "organize" and check it
            pg.goto(BASE + "/#/lesson/organize")
            pg.wait_for_timeout(900)
            pg.locator(".widget .opt").nth(1).click()
            pg.locator(".widget button.pri").first.click()
            pg.wait_for_timeout(500)
            assert pg.locator(".widget.done").count() >= 1 or pg.locator(".fb.ok").count() >= 1, "quiz did not accept the right answer"
            pg.screenshot(path=os.path.join(OUT, "lesson_quiz.png"))
            # hotkey dojo: start a quick round and press a few keys
            pg.goto(BASE + "/#/dojo")
            pg.wait_for_timeout(600)
            pg.get_by_text("Quick round").click()
            pg.wait_for_timeout(300)
            for key in ("a", "Shift+a", "g"):
                pg.keyboard.press(key)
                pg.wait_for_timeout(250)
            pg.screenshot(path=os.path.join(OUT, "dojo_round.png"))
            # texture lab: switch preset and generate through the UI
            pg.goto(BASE + "/#/lab")
            pg.wait_for_timeout(600)
            pg.get_by_text("Stone bricks").click()
            pg.wait_for_timeout(600)
            pg.get_by_text("Relief (move the mouse)").click()
            pg.mouse.move(700, 400)
            pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(OUT, "lab_default.png"))
            b.close()
    finally:
        srv.terminate()
        shutil.rmtree(data, ignore_errors=True)
    print("screenshots in", OUT)
    if errors:
        print("JS ERRORS:")
        for e in errors:
            print("  ", e)
        sys.exit(1)
    print("UI SMOKE PASS")


if __name__ == "__main__":
    main()
