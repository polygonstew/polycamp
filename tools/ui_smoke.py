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
            # texture lab: generate each procedural kind through the UI
            pg.goto(BASE + "/#/lab")
            pg.wait_for_timeout(600)
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
