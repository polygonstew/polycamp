"""voice.py - the narration engine: a priority queue in front of one synthesizer process, and a cache of the audio it makes.

Audio files are named by a hash of (wording rules, voice, text, pauses), so a segment is only ever synthesized once,
and changing a lesson re-voices only the sentences that changed. Priorities:
    0  the browser is waiting for this segment right now
    1  the next few segments of the lesson being played
    2  the rest of that lesson
    5+ bulk pre-render (lowest; cancellable)
The synthesizer (voice_worker.py) lives in its own venv, starts on demand and quits after ten idle minutes.
"""
import heapq
import itertools
import json
import os
import subprocess
import sys
import threading
import time

import config
import speech

WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_worker.py")
IDLE_S = 600
JOB_TIMEOUT_S = 300


def venv_python():
    sub = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
    return config.VOICE_HOME.joinpath("venv", *sub)


class Voice:
    def __init__(self):
        self.cv = threading.Condition()
        self.dir = config.DATA / "voice"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.specs = {}                 # key -> {"voice", "chunks"}, filled whenever a script is built
        self.jobs = {}                  # key -> {"key","prio","seq","state","err","t"}
        self.heap = []
        self.seq = itertools.count()
        self.proc = None
        self.info = {}
        self.err = ""
        self.busy = None
        self.last_active = time.time()
        self.batch = {"label": "", "total": 0, "done": 0, "failed": 0, "keys": set(), "t0": 0.0}
        self.made = {"n": 0, "ms": 0, "dur": 0.0}
        threading.Thread(target=self._loop, daemon=True, name="voice").start()

    # ---- files ------------------------------------------------------------------
    def find(self, key):
        for ext in (".ogg", ".wav"):
            p = self.dir / (key + ext)
            if p.exists():
                return p
        return None

    def meta(self, key):
        try:
            return json.loads((self.dir / (key + ".json")).read_text())
        except (OSError, ValueError):
            return None

    def installed(self):
        return venv_python().exists() and (config.VOICE_HOME / "models" / "voices-v1.0.bin").exists()

    # ---- status -----------------------------------------------------------------
    def status(self):
        files = [p for p in self.dir.iterdir() if p.suffix in (".ogg", ".wav")]
        with self.cv:
            queued = sum(1 for j in self.jobs.values() if j["state"] == "queued")
            b = self.batch
            batch = {"label": b["label"], "total": b["total"], "done": b["done"], "failed": b["failed"],
                     "left": max(0, b["total"] - b["done"] - b["failed"]), "t0": b["t0"]}
            rtf = (self.made["ms"] / 1000.0 / self.made["dur"]) if self.made["dur"] else None
            job_s = (self.made["ms"] / 1000.0 / self.made["n"]) if self.made["n"] else None
            return {"installed": self.installed(), "ready": bool(self.info.get("ready")), "running": bool(self.proc and self.proc.poll() is None),
                    "voices": self.info.get("voices") or [], "model": self.info.get("model", ""), "queued": queued,
                    "busy": self.busy, "error": self.err, "batch": batch, "rtf": round(rtf, 2) if rtf else None,
                    "job_s": round(job_s, 1) if job_s else None,
                    "cache": {"files": len(files), "mb": round(sum(p.stat().st_size for p in files) / 1e6, 1)},
                    "install_cmd": "python3 tools/install_voice.py"}

    # ---- requests ---------------------------------------------------------------
    def register(self, specs):
        with self.cv:
            self.specs.update(specs)

    def request(self, key, prio=0):
        """Queue `key` for synthesis (no-op when cached). Returns the job, or None if it is already on disk."""
        if self.find(key):
            return None
        with self.cv:
            spec = self.specs.get(key)
            if spec is None:
                raise KeyError("unknown voice segment " + key)
            job = self.jobs.get(key)
            if job and job["state"] == "error" and time.time() - job["t"] > 4:
                job = None
            if job is None or job["state"] in ("cancelled", "done"):
                job = self.jobs[key] = {"key": key, "prio": prio, "seq": 0, "state": "queued", "err": "", "t": time.time()}
            elif job["state"] == "queued" and prio >= job["prio"]:
                return job
            elif job["state"] != "queued":
                return job
            job["prio"], job["seq"] = prio, next(self.seq)
            heapq.heappush(self.heap, (job["prio"], job["seq"], key))
            self.cv.notify_all()
            return job

    def wait(self, key, timeout=150):
        """Block until the audio for `key` exists. Returns its path, or None (error or timeout)."""
        job = self.request(key, 0)
        end = time.time() + timeout
        while True:
            p = self.find(key)
            if p:
                return p
            with self.cv:
                j = self.jobs.get(key)
                if j and j["state"] == "error":
                    return None
                left = end - time.time()
                if left <= 0:
                    return None
                self.cv.wait(min(left, 1.0))

    def enqueue(self, keys, prio, label=None):
        n = 0
        with self.cv:
            if label is not None:
                self.batch = {"label": label, "total": 0, "done": 0, "failed": 0, "keys": set(), "t0": time.time()}
        for k in keys:
            if self.find(k):
                continue
            if self.request(k, prio) is not None and label is not None:
                with self.cv:
                    if k not in self.batch["keys"]:
                        self.batch["keys"].add(k)
                        self.batch["total"] += 1
                        n += 1
        return n

    def cancel_bulk(self):
        with self.cv:
            n = 0
            for j in self.jobs.values():
                if j["state"] == "queued" and j["prio"] >= 5:
                    j["state"] = "cancelled"
                    n += 1
            self.batch["total"] = self.batch["done"] + self.batch["failed"]
            self.batch["keys"] = set()
            return n

    def clear(self):
        self.cancel_bulk()
        n = 0
        for p in self.dir.iterdir():
            if p.suffix in (".ogg", ".wav", ".json", ".part"):
                try:
                    p.unlink()
                    n += 1
                except OSError:
                    pass
        with self.cv:
            self.jobs = {k: j for k, j in self.jobs.items() if j["state"] == "running"}
        return n

    # ---- scripts ----------------------------------------------------------------
    def script(self, content, lid, major, settings):
        les = content.lesson(lid)
        if les is None:
            return None
        seq = content.ordered_lessons()
        ids = [l.id for l in seq]
        i = ids.index(lid)
        voices = {"narrator": settings.get("voice_narrator", "af_heart"), "cubby": settings.get("voice_cubby", "am_puck")}
        pos = {"idx": i + 1, "total": len(seq), "next": seq[i + 1].title if i + 1 < len(seq) else "",
               "next_id": seq[i + 1].id if i + 1 < len(seq) else ""}
        pub, specs = speech.build_script(les, major, voices, pos)
        lines = {}
        for name, text in [("ack%d" % n, t) for n, t in enumerate(speech.ACKS)] + [("done", speech.LESSON_DONE)]:
            key, spec = speech.line_spec(text, voices["narrator"])
            specs[key] = spec
            lines[name] = {"key": key, "text": text}
        self.register(specs)
        for s in pub:
            s["ready"] = self.find(s["key"]) is not None
        for v in lines.values():
            v["ready"] = self.find(v["key"]) is not None
        return {"lesson": lid, "major": major, "voices": voices, "segments": pub, "lines": lines, "next": pos["next_id"]}

    def warm(self, script, from_idx=0):
        """Queue a lesson's segments in reading order, nearest first."""
        keys = [s["key"] for s in script["segments"][from_idx:] if not s["ready"]]
        lines = [v["key"] for v in script["lines"].values() if not v["ready"]]
        keys = keys[:2] + lines + keys[2:]                 # the "got it" lines must be ready before the first task ends
        for n, k in enumerate(keys):
            self.request(k, 1 if n < 3 else 2)

    def prerender(self, content, lids, majors, settings):
        keys = []
        for lid in lids:
            for m in majors:
                sc = self.script(content, lid, m, settings)
                if sc:
                    keys += [s["key"] for s in sc["segments"] if not s["opt"] or settings.get("voice_cubby_on", True) or s["kind"] != "cubby"]
                    keys += [v["key"] for v in sc["lines"].values()]
        seen, uniq = set(), []
        for k in keys:
            if k not in seen:
                seen.add(k)
                uniq.append(k)
        return self.enqueue(uniq, 5, "pre-render %d lessons" % len(lids))

    def say(self, voice, text):
        """Register arbitrary text to be spoken (a hint, a voice preview); returns its key, or None if nothing speakable."""
        key, spec = speech.say_spec(text, voice)
        if key:
            self.register({key: spec})
        return key

    # ---- the worker ---------------------------------------------------------------
    def _pop(self):
        while self.heap:
            prio, seq, key = heapq.heappop(self.heap)
            j = self.jobs.get(key)
            if j and j["state"] == "queued" and j["seq"] == seq and j["prio"] == prio:
                return j
        return None

    def _loop(self):
        while True:
            with self.cv:
                job = self._pop()
                if job is None:
                    self.cv.wait(timeout=5)
                    if self.proc and time.time() - self.last_active > IDLE_S and not self.heap:
                        self._stop()
                    continue
                job["state"], self.busy = "running", job["key"]
            try:
                self._run(job)
            except Exception as e:                                     # never let the thread die
                self._finish(job, False, "%s: %s" % (type(e).__name__, e))

    def _stop(self):
        p, self.proc, self.info = self.proc, None, {}
        if p and p.poll() is None:
            try:
                p.stdin.close()
                p.terminate()
            except OSError:
                pass

    def _start(self):
        if not self.installed():
            raise RuntimeError("The voice engine isn't installed. Run: python3 tools/install_voice.py")
        env = dict(os.environ, POLYCAMP_VOICE_MODELS=str(config.VOICE_HOME / "models"), PYTHONUNBUFFERED="1",
                   POLYCAMP_VOICE_THREADS=str(config.load().get("voice_threads", 2)))
        log = open(config.DATA / "tmp" / "voice-worker.log", "a")
        kw = {"creationflags": 0x08000000} if os.name == "nt" else {}
        self.proc = subprocess.Popen([str(venv_python()), "-u", WORKER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=log, text=True, bufsize=1, env=env, **kw)
        timer = threading.Timer(120, self._stop)
        timer.start()
        try:
            line = self.proc.stdout.readline()
        finally:
            timer.cancel()
        if not line:
            self.proc = None
            raise RuntimeError("The voice worker didn't start. See data/tmp/voice-worker.log")
        self.info = json.loads(line)

    def _run(self, job):
        key = job["key"]
        spec = self.specs[key]
        if not (self.proc and self.proc.poll() is None):
            self._start()
        ext = ".ogg" if self.info.get("ogg", True) else ".wav"
        out = self.dir / (key + ext)
        req = {"id": key, "voice": spec["voice"], "chunks": spec["chunks"], "out": str(out)}
        timer = threading.Timer(JOB_TIMEOUT_S, self._stop)
        timer.start()
        try:
            self.proc.stdin.write(json.dumps(req) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
        finally:
            timer.cancel()
        if not line:
            self._stop()
            raise RuntimeError("The voice worker stopped unexpectedly. See data/tmp/voice-worker.log")
        res = json.loads(line)
        if not res.get("ok"):
            self._finish(job, False, res.get("error", "synthesis failed"))
            return
        (self.dir / (key + ".json")).write_text(json.dumps({"dur": res["dur"], "marks": res["marks"], "voice": spec["voice"]}))
        with self.cv:
            self.made["n"] += 1
            self.made["ms"] += res["ms"]
            self.made["dur"] += res["dur"]
        self._finish(job, True, "")

    def _finish(self, job, ok, err):
        with self.cv:
            job["state"], job["err"], job["t"] = ("done" if ok else "error"), err, time.time()
            self.busy = None
            self.last_active = time.time()
            self.err = "" if ok else err
            b = self.batch
            if job["key"] in b["keys"]:
                b["done" if ok else "failed"] += 1
            self.cv.notify_all()
        if not ok:
            sys.stderr.write("voice: %s failed: %s\n" % (job["key"], err))
