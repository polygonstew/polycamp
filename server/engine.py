"""engine.py - the game: which lesson is active, live check evaluation, XP/gems/streak/badges, hints.

One Engine instance owns all learner state. It is fed by the HTTP layer (snapshots, answers, claims)
and publishes what changed on the SSE hub. See docs/ARCHITECTURE.md.
"""
import datetime
import json
import threading
import time

import checks
import dojo
import gamify
import store
from store import kv_get, kv_set, q

SETTLE_S = 0.6        # a check must stay true this long before it counts (ignores mid-drag flickers)
HINT_FREE = 2         # first two hints per task are free
HINT_COST = 2
SOLUTION_COST = 5


def _day(ts=None):
    return datetime.date.fromtimestamp(ts or time.time()).isoformat()


class Engine:
    def __init__(self, content, bridge, hub):
        self.content, self.bridge, self.hub = content, bridge, hub
        self.lock = threading.RLock()
        self.run = None
        self.snap = None
        self.last_ops = {}
        self.ops_dirty = 0.0
        self.was_connected = False
        self.last_live = ""
        self.toast = None
        if kv_get("gems") is None:
            kv_set("gems", 10)
        active = kv_get("active_lesson")
        if active and content.lesson(active):
            self._open(active)
        threading.Thread(target=self._ticker, daemon=True, name="engine-tick").start()

    # ---------------------------------------------------------------- profile
    def total_xp(self):
        return self.content.total_xp()

    def streak(self):
        days = {r["day"] for r in q("SELECT day FROM days")}
        d, n = datetime.date.today(), 0
        if d.isoformat() not in days:
            d -= datetime.timedelta(days=1)
        while d.isoformat() in days:
            n += 1
            d -= datetime.timedelta(days=1)
        return n

    def profile(self):
        xp = kv_get("xp", 0)
        badges = {r["id"]: r["ts"] for r in q("SELECT * FROM badges")}
        return {"xp": xp, "gems": kv_get("gems", 0), "level": gamify.level(xp, self.total_xp()), "streak": self.streak(),
                "badges": [self._badge_public(b, ts) for b, ts in badges.items()],
                "dojo": dojo.totals()}

    def _badge_public(self, bid, ts):
        if bid.startswith("boss-"):
            w = self.content.by_id.get(bid[5:])
            return {"id": bid, "emoji": "🗡️", "title": "Boss slain: " + (w.title if w else bid[5:]),
                    "desc": "Beat the boss lesson", "ts": ts}
        e, t, d = gamify.BADGES.get(bid, ("🏅", bid, ""))
        return {"id": bid, "emoji": e, "title": t, "desc": d, "ts": ts}

    def all_badges(self):
        have = {b["id"] for b in self.profile()["badges"]}
        out = [{"id": k, "emoji": v[0], "title": v[1], "desc": v[2], "have": k in have} for k, v in gamify.BADGES.items()]
        for w in self.content.worlds:
            out.append({"id": "boss-" + w.id, "emoji": "🗡️", "title": "Boss slain: " + w.title,
                        "desc": "Finish every lesson in " + w.title, "have": ("boss-" + w.id) in have})
        return out

    def stats(self):
        r = lambda sql: q(sql, one=True)[0]
        renders = q("SELECT meta FROM renders")
        mx = 0
        for row in renders:
            try:
                mx = max(mx, float(json.loads(row["meta"]).get("time", 0)))
            except Exception:
                pass
        flags = kv_get("flags", {})
        return {"tasks": r("SELECT COUNT(*) FROM done WHERE kind='task'"),
                "lessons": r("SELECT COUNT(*) FROM lessons WHERE completed IS NOT NULL"),
                "dojo_right": dojo.totals()["right"], "streak": self.streak(), "renders": len(renders),
                "max_render_s": mx, "ops": kv_get("ops_total", {}), "linked": kv_get("linked", False),
                "night": flags.get("night"), "textures": flags.get("textures"), "uv_looks": flags.get("uv_looks"),
                "godot": flags.get("godot"), "peeked": flags.get("peeked"),
                "campaign": self._campaign_done()}

    def _completed_lessons(self):
        return {r["id"] for r in q("SELECT id FROM lessons WHERE completed IS NOT NULL")}

    def _campaign_done(self):
        c = self._completed_lessons()
        seq = self.content.ordered_lessons()
        return bool(seq) and all(l.id in c for l in seq)

    def worlds_done(self):
        c = self._completed_lessons()
        return [w.id for w in self.content.worlds if w.lessons and all(l in c for l in w.lessons)]

    def set_flag(self, name):
        flags = kv_get("flags", {})
        if not flags.get(name):
            flags[name] = True
            kv_set("flags", flags)
            self.check_badges()

    def check_badges(self):
        have = {r["id"] for r in q("SELECT id FROM badges")}
        for bid in gamify.earned(self.stats(), self.worlds_done()) - have:
            q("INSERT OR IGNORE INTO badges(id,ts) VALUES(?,?)", (bid, time.time()))
            self.hub.publish("badge", badge=self._badge_public(bid, time.time()))

    # ---------------------------------------------------------------- awards
    def award(self, xp=0, gems=0, kind="", ref="", note=""):
        with self.lock:
            old = kv_get("xp", 0)
            kv_set("xp", old + xp)
            kv_set("gems", max(0, kv_get("gems", 0) + gems))
            q("INSERT INTO ledger(ts,kind,ref,xp,gems,note) VALUES(?,?,?,?,?,?)", (time.time(), kind, ref, xp, gems, note))
            bonus = 0
            if xp > 0:
                today = _day()
                new_day = not q("SELECT 1 FROM days WHERE day=?", (today,))
                q("INSERT INTO days(day,xp) VALUES(?,?) ON CONFLICT(day) DO UPDATE SET xp=xp+?", (today, xp, xp))
                if new_day and self.streak() >= 2:
                    bonus = min(self.streak(), 7)
                    kv_set("gems", kv_get("gems", 0) + bonus)
                if datetime.datetime.now().hour < 5:
                    self.set_flag("night")
            lv0 = gamify.level(old, self.total_xp())["n"]
            lv1 = gamify.level(old + xp, self.total_xp())
            self.hub.publish("award", xp=xp, gems=gems + bonus, kind=kind, ref=ref, note=note,
                             level_up=lv1["n"] > lv0, level=lv1, streak_bonus=bonus)
            self.check_badges()
            self.hub.publish("profile", profile=self.profile())

    # ---------------------------------------------------------------- overview
    def overview(self):
        done_rows = q("SELECT lesson, COUNT(*) c FROM done GROUP BY lesson")
        done_n = {r["lesson"]: r["c"] for r in done_rows}
        completed = self._completed_lessons()
        worlds, nxt = [], None
        for w in self.content.fresh().worlds:
            ls = []
            for lid in w.lessons:
                les = self.content.lessons[lid]
                total = len(les.required_tasks()) + len(les.quiz_ids)
                ls.append({"id": lid, "title": les.title, "summary": les.summary, "minutes": les.minutes,
                           "boss": les.boss, "xp": les.total_xp(), "total": total, "done_n": done_n.get(lid, 0),
                           "done": lid in completed, "scene": les.scene})
                if nxt is None and lid not in completed:
                    nxt = lid
            worlds.append(dict(w.public(), lessons=ls, done=sum(1 for x in ls if x["done"]), count=len(ls),
                               xp=sum(x["xp"] for x in ls)))
        return {"worlds": worlds, "next": nxt, "active": self.run["lesson"] if self.run else None,
                "total_xp": self.total_xp(), "errors": self.content.errors()}

    def lesson_view(self, lid):
        les = self.content.lesson(lid)
        if les is None:
            return None
        pub = les.public()
        rows = {r["id"]: {"how": r["how"], "xp": r["xp"]} for r in q("SELECT * FROM done WHERE lesson=?", (lid,))}
        les_row = q("SELECT * FROM lessons WHERE id=?", (lid,), one=True)
        hints = {r["task"]: r["level"] for r in q("SELECT * FROM hints WHERE task LIKE ?", (lid + "/%",))}
        nxt = self.content.next_after(lid)
        pub["state"] = {"done": rows, "completed": bool(les_row and les_row["completed"]), "hints": hints,
                        "solution": bool(les_row and les_row["solution"]), "has_solution": les.has_solution(),
                        "active": bool(self.run and self.run["lesson"] == lid),
                        "next": nxt.id if nxt else None, "next_title": nxt.title if nxt else None,
                        "live": self.run["live"] if self.run and self.run["lesson"] == lid else {}}
        return pub

    # ---------------------------------------------------------------- active lesson
    def _open(self, lid):
        snap = self.snap
        self.run = {"lesson": lid, "base": self._baseline(snap), "seen_false": set(), "true_since": {}, "live": {},
                    "rebase": False}
        q("INSERT OR IGNORE INTO lessons(id,started) VALUES(?,?)", (lid, time.time()))

    def _baseline(self, snap):
        s = snap or {}
        return {"ops": dict(s.get("ops", {})), "counters": dict(s.get("counters", {})), "t0": time.time()}

    def start(self, lid):
        with self.lock:
            if self.content.lesson(lid) is None:
                raise KeyError("no such lesson")
            if not self.run or self.run["lesson"] != lid:
                self._open(lid)
                kv_set("active_lesson", lid)
            self.evaluate()
            self.publish_live(force=True)
        return self.lesson_view(lid)

    def prep(self, cid=None, wait=True):
        les = self._active()
        if les.scene == "keep":
            return {"ok": True, "msg": "This lesson uses your current scene - nothing to set up."}
        wt = (40 if les.scene.startswith("starter") else 25) if wait else 0
        if les.scene in ("fresh", "empty"):
            r = self.bridge.command("new_scene", {"kind": "default" if les.scene == "fresh" else "empty", "backup": True},
                                    cid, wait=wt)
        else:
            r = self.bridge.command("run_script", {"code": self.content.scene_script(les), "label": les.id, "backup": True},
                                    cid, wait=wt)
        with self.lock:
            self.run["seen_false"] = set()
            self.run["true_since"] = {}
            self.run["rebase"] = True
        return {"ok": r.get("ok", True), "msg": r.get("msg", "Asked Blender to set up the scene.")}

    def _active(self):
        if not self.run:
            raise RuntimeError("Open a lesson in the app first.")
        return self.content.lesson(self.run["lesson"])

    # ---------------------------------------------------------------- snapshots & checks
    def on_snapshot(self, snap):
        with self.lock:
            self.snap = snap
            self._accumulate_ops(snap)
            if not kv_get("linked"):
                kv_set("linked", True)
                self.check_badges()
            if self.run and self.run.get("rebase"):
                self.run["base"] = self._baseline(snap)
                self.run["rebase"] = False
            self.evaluate()
            self.publish_live()
            return self.hud()

    def _accumulate_ops(self, snap):
        cid = (snap.get("link") or {}).get("cid", "?")
        last, tot = self.last_ops.get(cid, {}), kv_get("ops_total", {})
        for op, n in (snap.get("ops") or {}).items():
            d = n - last.get(op, 0)
            tot[op] = tot.get(op, 0) + (d if d >= 0 else n)
        self.last_ops[cid] = dict(snap.get("ops") or {})
        if time.time() - self.ops_dirty > 10:
            kv_set("ops_total", tot)
            self.ops_dirty = time.time()
            self.check_badges()

    def evaluate(self):
        """Re-run the active lesson's checks against the latest snapshot; complete tasks that settled."""
        run = self.run
        if not run or not self.snap or not self.bridge.connected():
            return
        les = self.content.lesson(run["lesson"])
        if les is None:
            return
        env = checks.make_env(self.snap, run["base"])
        done = {r["id"] for r in q("SELECT id FROM done WHERE lesson=?", (les.id,))}
        now, live = time.time(), {}
        for blk in les.tasks():
            tid = blk["id"]
            if tid in done:
                continue
            priv = les.priv[tid]
            res = [{"label": lbl, "ok": checks.run(expr, env)} for expr, lbl in priv["checks"]]
            allok = bool(res) and all(r["ok"] for r in res)
            pre = False
            if not allok:
                run["seen_false"].add(tid)
                run["true_since"].pop(tid, None)
            elif tid in run["seen_false"] or priv["allow_initial"]:
                ts = run["true_since"].setdefault(tid, now)
                if now - ts >= SETTLE_S:
                    self._complete(les, blk, "auto")
                    continue
            else:
                pre = True           # already true before the learner did anything: needs a Claim click
            live[tid] = {"checks": res, "pre": pre, "ok": allok}
        run["live"] = live

    def _complete(self, les, blk, how, xp=None):
        tid = blk["id"]
        if q("SELECT 1 FROM done WHERE id=?", (tid,)):
            return False
        xp = blk["xp"] if xp is None else xp
        q("INSERT INTO done(id,lesson,kind,xp,how,ts) VALUES(?,?,?,?,?,?)", (tid, les.id, "task", xp, how, time.time()))
        self.hub.publish("task_done", id=tid, title=blk["title"], xp=xp, how=how, lesson=les.id)
        self.award(xp, 2 if les.boss else 1, "task", tid, blk["title"])
        self._maybe_finish(les)
        return True

    def _maybe_finish(self, les):
        if q("SELECT 1 FROM lessons WHERE id=? AND completed IS NOT NULL", (les.id,)):
            return
        done = {r["id"] for r in q("SELECT id FROM done WHERE lesson=?", (les.id,))}
        need = [b["id"] for b in les.required_tasks()] + list(les.quiz_ids)
        if not all(n in done for n in need):
            return
        q("INSERT INTO lessons(id,started,completed) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET completed=?",
          (les.id, time.time(), time.time(), time.time()))
        nxt = self.content.next_after(les.id)
        self.hub.publish("lesson_done", lesson=les.id, title=les.title, boss=les.boss, xp=les.xp_bonus,
                         next=nxt.id if nxt else None, next_title=nxt.title if nxt else None)
        self.award(les.xp_bonus, 10 if les.boss else 3, "lesson", les.id, les.title)

    # ---------------------------------------------------------------- learner actions
    def claim(self, tid, honor=False):
        with self.lock:
            les, blk = self._find_task(tid)
            if q("SELECT 1 FROM done WHERE id=?", (tid,)):
                return {"ok": True, "msg": "Already done."}
            priv = les.priv[tid]
            if priv["checks"] and self.snap and self.bridge.connected():
                env = checks.make_env(self.snap, self.run["base"] if self.run else None)
                if all(checks.run(e, env) for e, _ in priv["checks"]):
                    self._complete(les, blk, "claim")
                    return {"ok": True, "msg": "Checked: nice work!"}
            if not priv["checks"]:
                self._complete(les, blk, "manual")
                return {"ok": True, "msg": "Marked done."}
            if honor:
                self._complete(les, blk, "honor", xp=max(1, blk["xp"] // 2))
                return {"ok": True, "msg": "Marked done on your word (half XP)."}
            return {"ok": False, "msg": "The checks aren't passing yet."
                    if self.bridge.connected() else "Blender isn't linked, so I can't check. Link it, or mark it done on your word."}

    def _find_task(self, tid):
        lid = tid.split("/", 1)[0]
        les = self.content.lesson(lid)
        blk = next((b for b in (les.tasks() if les else []) if b["id"] == tid), None)
        if blk is None:
            raise KeyError("no such task")
        return les, blk

    def hint(self, tid=None):
        with self.lock:
            les = self._active()
            if tid is None:
                done = {r["id"] for r in q("SELECT id FROM done WHERE lesson=?", (les.id,))}
                tid = next((b["id"] for b in les.required_tasks() if b["id"] not in done), None)
            if tid is None:
                return {"error": "Every task here is done. Nothing to hint about!"}
            hints = les.priv[tid]["hints"]
            row = q("SELECT level FROM hints WHERE task=?", (tid,), one=True)
            lvl = row["level"] if row else 0
            if not hints:
                return {"error": "No hints written for this one. Re-read the task and try the keys shown beside it."}
            shown = min(lvl, len(hints) - 1)
            if lvl >= len(hints):
                return {"text": hints[-1], "level": len(hints), "of": len(hints), "task": tid, "cost": 0,
                        "note": "That's the last hint."}
            cost = HINT_COST if lvl >= HINT_FREE else 0
            if cost > kv_get("gems", 0):
                return {"error": "That hint costs %d gems and you have %d. Do a Hotkey Dojo round to earn some." %
                        (cost, kv_get("gems", 0))}
            q("INSERT INTO hints(task,level) VALUES(?,?) ON CONFLICT(task) DO UPDATE SET level=?", (tid, lvl + 1, lvl + 1))
            q("UPDATE lessons SET hints=hints+1 WHERE id=?", (les.id,))
            if cost:
                self.award(0, -cost, "hint", tid, "hint %d" % (lvl + 1))
            self.toast = hints[shown]
            self.hub.publish("hint", task=tid, text=hints[shown], level=lvl + 1, of=len(hints), cost=cost)
            return {"text": hints[shown], "level": lvl + 1, "of": len(hints), "task": tid, "cost": cost}

    def solution(self, run=False, cid=None):
        with self.lock:
            les = self._active()
            if not les.has_solution():
                return {"error": "This lesson has no solution script."}
            row = q("SELECT solution, completed FROM lessons WHERE id=?", (les.id,), one=True)
            free = bool(row and (row["solution"] or row["completed"]))
            if not free:
                if kv_get("gems", 0) < SOLUTION_COST:
                    return {"error": "The solution script costs %d gems." % SOLUTION_COST}
                self.award(0, -SOLUTION_COST, "solution", les.id, "peek")
            q("UPDATE lessons SET solution=1 WHERE id=?", (les.id,))
            self.set_flag("peeked")
        out = {"code": les.solution_text(), "cost": 0 if free else SOLUTION_COST}
        if run:
            r = self.bridge.command("run_script", {"code": self.content.solve_script(les), "label": les.id + "-solution"},
                                    cid, wait=40)
            out["ran"] = r
        return out

    def answer(self, qid, value):
        with self.lock:
            lid = qid.split("/", 1)[0]
            les = self.content.lesson(lid)
            priv = les.priv.get(qid) if les else None
            if priv is None or priv["kind"] == "task":
                raise KeyError("no such question")
            kind, ans = priv["kind"], priv["answer"]
            if kind == "quiz":
                got = sorted(value) if isinstance(value, list) else [value]
                ok = got == sorted(ans)
            elif kind == "order":
                ok = value == ans
            elif kind == "match":
                ok = value == ans
            elif kind == "fill":
                ok = str(value).strip().lower() in ans
            else:                                   # keys: judged in the browser
                ok = bool(value)
            blk = next(b for b in les.blocks if b.get("id") == qid)
            fresh = False
            if ok and not q("SELECT 1 FROM done WHERE id=?", (qid,)):
                q("INSERT INTO done(id,lesson,kind,xp,how,ts) VALUES(?,?,?,?,?,?)",
                  (qid, lid, kind, blk["xp"], "answer", time.time()))
                fresh = True
                self.award(blk["xp"], 1 if kind == "fill" else 0, "quiz", qid, kind)
                self._maybe_finish(les)
            out = {"correct": ok, "first": fresh, "xp": blk["xp"] if fresh else 0}
            if ok or kind == "keys":
                out["explain"] = priv["explain"]
            if not ok and kind in ("order", "match"):
                out["answer"] = ans
            return out

    # ---------------------------------------------------------------- live view
    def hud(self):
        run = self.run
        base = {"level": gamify.level(kv_get("xp", 0), self.total_xp()), "toast": self.toast,
                "connected": self.bridge.connected()}
        if not run:
            return dict(base, lesson=None, tasks=[])
        les = self.content.lesson(run["lesson"])
        if les is None:
            return dict(base, lesson=None, tasks=[])
        done = {r["id"] for r in q("SELECT id FROM done WHERE lesson=?", (les.id,))}
        tasks = []
        for b in les.tasks():
            lv = run["live"].get(b["id"], {})
            tasks.append({"id": b["id"], "title": b["title"], "done": b["id"] in done, "optional": b.get("optional", False),
                          "pre": lv.get("pre", False), "checks": lv.get("checks") or [{"label": l, "ok": False} for l in b["labels"]]})
        n_done = sum(1 for t in tasks if t["done"])
        return dict(base, lesson={"id": les.id, "title": les.title, "boss": les.boss, "world": les.world,
                                  "scene": les.scene}, tasks=tasks, progress={"done": n_done, "total": len(tasks)})

    def scene_summary(self):
        s = self.snap
        if not s:
            return None
        objs = [{"name": o["name"], "type": o["type"], "sel": o["sel"], "active": o["active"],
                 "verts": o.get("verts_eval", o.get("verts")), "mods": [m["type"] for m in o.get("mods", [])],
                 "mats": [m for m in o.get("mats", []) if m], "keys": (o.get("anim") or {}).get("keys", 0)}
                for o in s.get("objects", [])[:80]]
        r = s.get("render", {})
        return {"mode": s.get("mode"), "active": s.get("active"), "selected": s.get("selected", []),
                "objects": objs, "total": s.get("objects_total"), "file": (s.get("file") or {}).get("name"),
                "dirty": (s.get("file") or {}).get("dirty"), "blender": s.get("blender"), "totals": s.get("totals"),
                "render": {k: r.get(k) for k in ("engine", "res_x", "res_y", "res_pct", "cy_samples", "cy_use_denoising",
                                                 "frame", "frame_start", "frame_end", "fps")},
                "ui": {k: (s.get("ui") or {}).get(k) for k in ("shading", "windows", "workspace", "persp")}}

    def publish_live(self, force=False):
        payload = {"hud": self.hud(), "scene": self.scene_summary(), "bridge": self.bridge.status()}
        # 'ago' values change every second; leave them out of the change test
        sig = json.dumps({"h": payload["hud"], "s": payload["scene"], "c": payload["bridge"]["connected"]},
                         sort_keys=True, default=str)
        if force or sig != self.last_live:
            self.last_live = sig
            self.hub.publish("live", **payload)

    def _ticker(self):
        while True:
            time.sleep(0.5)
            try:
                with self.lock:
                    conn = self.bridge.connected()
                    if conn != self.was_connected:
                        self.was_connected = conn
                        self.publish_live(force=True)
                    elif conn:
                        self.evaluate()
                        self.publish_live()
            except Exception as e:
                print("engine tick:", e)

    def reset_progress(self):
        with self.lock:
            for t in ("done", "lessons", "ledger", "cards", "renders", "badges", "hints", "days", "kv"):
                q("DELETE FROM " + t)
            kv_set("gems", 10)
            self.run = None
            self.hub.publish("profile", profile=self.profile())
