#!/usr/bin/env python3
"""The narrator marks "the paragraph being read" by index, so server/speech.py:md_units() must split markdown into the
same units as web/js/md.js:md() renders. This checks that for every markdown block of every lesson.

    /usr/bin/python3 tools/md_parity.py            (needs python playwright + /usr/bin/chromium)
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))
import speech  # noqa: E402

PORT = 8574
BASE = "http://127.0.0.1:%d" % PORT


def main():
    from playwright.sync_api import sync_playwright
    env = dict(os.environ, POLYCAMP_DATA=tempfile.mkdtemp(prefix="pc-parity-"), POLYCAMP_PORT=str(PORT))
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "polycamp.py")], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bad, n = [], 0
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(BASE + "/api/state", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        ov = json.load(urllib.request.urlopen(BASE + "/api/overview"))
        ids = [l["id"] for w in ov["worlds"] for l in w["lessons"]]
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            pg = b.new_page()
            pg.goto(BASE + "/")
            pg.wait_for_timeout(500)
            for lid in ids:
                les = json.load(urllib.request.urlopen(BASE + "/api/lesson/" + lid))
                texts = [(i, blk["text"]) for i, blk in enumerate(les["blocks"]) if blk["t"] == "md"]
                counts = pg.evaluate("""async (texts) => {
                    const { md } = await import('/js/md.js');
                    return texts.map(t => { const d = document.createElement('div'); d.innerHTML = md(t); return d.children.length; });
                }""", [t for _, t in texts])
                for (i, text), js in zip(texts, counts):
                    n += 1
                    py = len(speech.md_units(text))
                    if py != js:
                        bad.append("%s block %d: python %d units, browser %d elements" % (lid, i, py, js))
            b.close()
    finally:
        srv.terminate()
    print("checked %d markdown blocks in %d lessons" % (n, len(ids)))
    for m in bad[:30]:
        print("MISMATCH", m)
    print("PASS" if not bad else "FAIL: %d mismatches" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
