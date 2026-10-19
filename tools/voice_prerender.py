#!/usr/bin/env python3
"""Make the narration audio ahead of time, so every lesson plays instantly instead of being voiced as you read.

    python3 tools/voice_prerender.py                       the whole campaign (about 3-4 hours of CPU in the background)
    python3 tools/voice_prerender.py --scope world:boot    one world
    python3 tools/voice_prerender.py --scope lesson:transform
    python3 tools/voice_prerender.py --wait                stay and show progress until it is finished
    python3 tools/voice_prerender.py --stop                cancel what is still queued

It only queues the work on the running Polycamp server (default http://127.0.0.1:8570); the server does it at the
lowest priority and a lesson you open jumps the queue, so Blender and your reading are never held up. Only text that
isn't already voiced is made, so running it again after editing a lesson costs almost nothing.
"""
import argparse
import json
import sys
import time
import urllib.request


def call(server, path, body=None):
    req = urllib.request.Request(server + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="http://127.0.0.1:8570")
    ap.add_argument("--scope", default="all", help="all | world:<id> | lesson:<id>")
    ap.add_argument("--majors", default="3,4,5", help="Blender generations whose version-specific notes get voiced")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--stop", action="store_true")
    a = ap.parse_args()
    if a.stop:
        print("cancelled", call(a.server, "/api/voice/cancel", {})["cancelled"], "queued segments")
        return 0
    st = call(a.server, "/api/voice/status")
    if not st["installed"]:
        sys.exit("The voice engine isn't installed. Run: python3 tools/install_voice.py")
    r = call(a.server, "/api/voice/prerender", {"scope": a.scope, "majors": [int(m) for m in a.majors.split(",")]})
    print("queued %d segments from %d lessons" % (r["queued"], r["lessons"]))
    if not a.wait:
        print("running in the background; Settings > Narration shows the progress")
        return 0
    while True:
        b = call(a.server, "/api/voice/status")["batch"]
        eta = ""
        s = call(a.server, "/api/voice/status")
        if s.get("job_s") and b["left"]:
            eta = ", about %d min left" % max(1, round(b["left"] * s["job_s"] / 60))
        print("\r%d / %d done%s%s   " % (b["done"], b["total"], ", %d failed" % b["failed"] if b["failed"] else "", eta), end="", flush=True)
        if not b["left"]:
            print("\nfinished")
            return 1 if b["failed"] else 0
        time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
