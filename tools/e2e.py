#!/usr/bin/env python3
"""End-to-end test: server + a real headless Blender with the add-on + a scripted learner.

    python3 tools/e2e.py [path/to/blender]

Starts the server on :8571 with a throw-away data dir (never touches your real progress), opens lesson
`link-up`, preps the scene, lets "the learner" rename the cube and save, and checks the tasks tick.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8571
BASE = "http://127.0.0.1:%d" % PORT
BLENDER = sys.argv[1] if len(sys.argv) > 1 else "blender"


def api(path, data=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def main():
    data = tempfile.mkdtemp(prefix="pc-e2e-")
    env = dict(os.environ, POLYCAMP_DATA=data, POLYCAMP_PORT=str(PORT))
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "polycamp.py")], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    bl = None
    ok = False
    try:
        for _ in range(50):
            try:
                api("/api/state")
                break
            except Exception:
                time.sleep(0.2)
        api("/api/lesson/start", {"id": "link-up"})
        bl = subprocess.Popen([BLENDER, "-b", "--factory-startup", "--python",
                               os.path.join(ROOT, "tools", "e2e_blender_side.py"), "--", BASE, "26"],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for _ in range(40):
            if api("/api/bridge/status")["connected"]:
                break
            time.sleep(0.5)
        else:
            raise SystemExit("FAIL: Blender never connected")
        print("connected:", api("/api/bridge/status")["clients"][0]["blender"])
        print("prep:", api("/api/lesson/prep", {}))
        deadline = time.time() + 20
        while time.time() < deadline:
            les = api("/api/lesson/link-up")
            done = les["state"]["done"]
            if "link-up/rename" in done and "link-up/save" in done:
                ok = True
                break
            time.sleep(0.5)
        les = api("/api/lesson/link-up")
        print("done tasks:", sorted(les["state"]["done"]))
        print("live:", json.dumps(les["state"]["live"])[:300])
        prof = api("/api/state")["profile"]
        print("xp=%s gems=%s level=%s" % (prof["xp"], prof["gems"], prof["level"]["title"]))
        # the claim button for the allow_initial task must work too
        print("claim linked:", api("/api/lesson/claim", {"task": "link-up/linked"}))
        print("quiz:", api("/api/answer", {"id": "link-up/q1", "value": [1]}))
        les = api("/api/lesson/link-up")
        print("lesson completed:", les["state"]["completed"])
        ok = ok and les["state"]["completed"]
    finally:
        for p in (bl, srv):
            if p and p.poll() is None:
                p.terminate()
        if bl:
            try:
                print("--- blender tail:\n" + bl.communicate(timeout=10)[0][-600:])
            except Exception:
                pass
        try:
            print("--- server tail:\n" + srv.communicate(timeout=5)[0][-800:])
        except Exception:
            pass
        shutil.rmtree(data, ignore_errors=True)
    print("E2E", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
