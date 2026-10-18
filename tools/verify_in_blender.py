"""Run INSIDE Blender:  blender -b --factory-startup --python tools/verify_in_blender.py -- [lesson-id ...]

For every lesson: build its starting scene, check that no task is already satisfied, run the lesson's
:::solve script, then check that every task's checks now pass. This is how the campaign stays honest
on Blender 3.3 / 4.x / 5.x. Tasks marked `untested` (UI state, renders) are skipped.
"""
import os
import sys
import tempfile
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("POLYCAMP_DATA", tempfile.mkdtemp(prefix="pc-verify-"))
sys.path.insert(0, os.path.join(ROOT, "addon"))
sys.path.insert(0, os.path.join(ROOT, "server"))

import bpy

import polycamp_link as pl
from polycamp_link import commands, link

import checks
import lessons

pl.register()
link.stop()
wanted = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
content = lessons.Content()
fails, warns, ran = [], [], 0
print("== verify on Blender", bpy.app.version_string, flush=True)


def evaluate(les, base):
    snap = link._snapshot()
    env = checks.make_env(snap, base)
    out = {}
    for blk in les.tasks():
        priv = les.priv[blk["id"]]
        if priv["untested"] or not priv["checks"]:
            continue
        out[blk["id"]] = [(lbl, checks.run(expr, env), expr) for expr, lbl in priv["checks"]]
    return out, snap


for les in content.ordered_lessons():
    if wanted and les.id not in wanted:
        continue
    ran += 1
    t0 = time.time()
    try:
        if les.errors:
            fails.append((les.id, "content errors: %s" % les.errors))
            continue
        if les.scene == "fresh":
            r = commands.run({"id": 1, "cmd": "new_scene", "args": {"backup": False}})
        elif les.scene == "empty":
            r = commands.run({"id": 1, "cmd": "new_scene", "args": {"backup": False, "kind": "empty"}})
        elif les.scene.startswith("starter:"):
            r = commands.run({"id": 1, "cmd": "run_script", "args": {"code": content.scene_script(les), "label": les.id}})
        else:
            r = commands.run({"id": 1, "cmd": "new_scene", "args": {"backup": False}})   # 'keep' lessons start from factory
        if not r["ok"]:
            fails.append((les.id, "scene setup failed: " + r["msg"]))
            continue
        link.S.dirty = True
        base = {"ops": dict(link.S.op_counts), "counters": {}, "t0": time.time()}
        before, snap0 = evaluate(les, base)
        for tid, res in before.items():
            priv = les.priv[tid]
            if all(ok for _, ok, _ in res) and not priv["allow_initial"]:
                warns.append((les.id, "task %s already satisfied before the solution" % tid))
        if not les.solve:
            if any(les.priv[b["id"]]["checks"] and not les.priv[b["id"]]["untested"] for b in les.tasks()):
                fails.append((les.id, "has checks but no :::solve"))
            continue
        r = commands.run({"id": 2, "cmd": "run_script", "args": {"code": content.solve_script(les), "label": les.id + "-solve"}})
        if not r["ok"]:
            fails.append((les.id, "solve script failed: " + r["msg"]))
            continue
        after, snap1 = evaluate(les, base)
        bad = [(tid, lbl, expr) for tid, res in after.items() for lbl, ok, expr in res if not ok]
        if snap1.get("errors"):
            bad.append(("snapshot", "errors", str(snap1["errors"][:2])))
        if bad:
            fails.append((les.id, "; ".join("%s: '%s' [%s]" % b for b in bad[:6])))
        else:
            print("PASS %-28s (%.1fs, %d tasks)" % (les.id, time.time() - t0, len(after)), flush=True)
    except Exception:
        fails.append((les.id, "exception: " + traceback.format_exc()[-600:]))

for lid, w in warns:
    print("WARN %s: %s" % (lid, w))
for lid, f in fails:
    print("FAIL %s: %s" % (lid, f))
print("RESULT %d lessons, %d failed, %d warnings on %s" % (ran, len(fails), len(warns), bpy.app.version_string), flush=True)
