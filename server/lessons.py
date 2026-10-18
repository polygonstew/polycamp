"""lessons.py - load the campaign from content/*.md into worlds, lessons, tasks and quizzes.

Format is documented in docs/AUTHORING.md. In short: a front-matter header, markdown, and
":::block" sections (task / quiz / order / match / fill / keys / cubby / note / v / reveal / goal / solve).
Everything the learner must not see before earning it (check expressions, answers, hints, the
solution script) lives in `priv`; `public()` is what the browser gets.
"""
import re
import shlex
import threading
import time

import checks
from config import CONTENT

DIRECTIVE = re.compile(r"^(check|hint|keys|why|allow_initial):\s*(.*)$")
FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)


def _meta(text):
    m = FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def _attrs(rest):
    try:
        toks = shlex.split(rest)
    except ValueError:
        toks = rest.split()
    pos, kw = [], {}
    for t in toks:
        if "=" in t and not t.startswith("="):
            k, v = t.split("=", 1)
            kw[k] = v
        else:
            pos.append(t)
    return pos, kw


def _int(v, d):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def _bool(v):
    return str(v).lower() in ("1", "true", "yes", "y")


def _plain_title(text, n=80):
    t = re.sub(r"[`*_#>\[\]]", "", text.strip().splitlines()[0] if text.strip() else "")
    return t[:n]


class Lesson:
    def __init__(self, path, world, order, meta, body):
        self.path = path
        self.world = world
        self.order = order
        self.id = meta.get("id") or path.stem.split("-", 1)[-1]
        self.title = meta.get("title", self.id)
        self.summary = meta.get("summary", "")
        self.minutes = _int(meta.get("minutes"), 10)
        self.boss = _bool(meta.get("boss"))
        self.scene = meta.get("scene", "keep")            # keep | fresh | empty | starter:<id>
        self.keys = [k.strip() for k in meta.get("keys", "").split(",") if k.strip()]
        self.tags = [k.strip() for k in meta.get("tags", "").split(",") if k.strip()]
        self.image = meta.get("image", "")
        self.blocks, self.priv, self.errors = [], {}, []
        self.task_ids, self.quiz_ids = [], []
        self.solve = ""
        self._parse(body)
        self.xp_bonus = _int(meta.get("xp"), 25 + (50 if self.boss else 0))

    # ---- parsing -----------------------------------------------------------
    def _parse(self, body):
        lines, i, md = body.splitlines(), 0, []

        def flush():
            text = "\n".join(md).strip("\n")
            md.clear()
            if text.strip():
                self.blocks.append({"t": "md", "text": text})

        while i < len(lines):
            line = lines[i]
            m = re.match(r"^:::(\w+)\s*(.*)$", line)
            if not m:
                md.append(line)
                i += 1
                continue
            flush()
            name, rest = m.group(1), m.group(2)
            j = i + 1
            inner = []
            while j < len(lines) and lines[j].rstrip() != ":::":
                inner.append(lines[j])
                j += 1
            i = j + 1
            try:
                self._block(name, rest, inner)
            except Exception as e:                       # a typo in one block must not hide the lesson
                self.errors.append("%s block: %s" % (name, e))
        flush()

    def _local(self, kw, kind, n):
        lid = kw.get("id") or "%s%d" % (kind, n)
        return "%s/%s" % (self.id, lid)

    def _block(self, name, rest, inner):
        pos, kw = _attrs(rest)
        text = "\n".join(inner).strip("\n")
        if name == "cubby":
            self.blocks.append({"t": "cubby", "text": text, "mood": kw.get("mood", pos[0] if pos else "")})
        elif name == "note":
            self.blocks.append({"t": "note", "kind": pos[0] if pos else "info", "text": text,
                                "title": kw.get("title", "")})
        elif name == "v":
            self.blocks.append({"t": "v", "spec": pos[0] if pos else "any", "text": text})
        elif name == "reveal":
            self.blocks.append({"t": "reveal", "title": kw.get("title", pos[0] if pos else "More"), "text": text})
        elif name == "goal":
            self.blocks.append({"t": "goal", "img": kw.get("img", ""), "text": text})
        elif name == "img":
            self.blocks.append({"t": "img", "src": kw.get("src", ""), "caption": text})
        elif name == "solve":
            self.solve = text
        elif name == "task":
            self._task(pos, kw, inner)
        elif name in ("quiz", "order", "match", "fill", "keys"):
            self._question(name, pos, kw, inner)
        else:
            raise ValueError("unknown block ':::%s'" % name)

    def _task(self, pos, kw, inner):
        tid = self._local(kw, "t", len(self.task_ids) + 1)
        prose, directives, last = [], [], None
        for ln in inner:
            m = DIRECTIVE.match(ln)
            if m:
                last = [m.group(1), m.group(2).strip()]
                directives.append(last)
            elif last is not None and ln.startswith("  ") and ln.strip():
                last[1] += " " + ln.strip()
            else:
                last = None
                prose.append(ln)
        text = "\n".join(prose).strip()
        chk, hints, tkeys, why = [], [], [], ""
        allow_initial = "allow_initial" in kw or any(d[0] == "allow_initial" for d in directives)
        for kind, val in directives:
            if kind == "check":
                expr, _, label = val.rpartition(" :: ")
                if not expr:
                    expr, label = val, val
                try:
                    checks.validate(expr)
                except Exception as e:
                    self.errors.append("task %s check %r: %s" % (tid, expr, e))
                chk.append((expr.strip(), label.strip()))
            elif kind == "hint":
                hints.append(val)
            elif kind == "keys":
                tkeys = [k.strip() for k in val.split(",") if k.strip()]
            elif kind == "why":
                why = val
        manual = "manual" in pos or "manual" in kw or not chk
        title = kw.get("title") or _plain_title(text)
        self.task_ids.append(tid)
        self.priv[tid] = {"kind": "task", "checks": chk, "hints": hints, "allow_initial": allow_initial,
                          "untested": "untested" in pos or "untested" in kw}
        self.blocks.append({"t": "task", "id": tid, "title": title, "text": text, "xp": _int(kw.get("xp"), 20),
                            "labels": [c[1] for c in chk], "nhints": len(hints), "keys": tkeys, "why": why,
                            "manual": manual, "optional": "optional" in pos or "stretch" in pos})

    def _question(self, name, pos, kw, inner):
        qid = self._local(kw, "q", len(self.quiz_ids) + 1)
        explain, prose, opts, last = "", [], [], None
        for ln in inner:
            if ln.startswith("explain:"):
                explain, last = ln[8:].strip(), "explain"
            elif last == "explain" and ln.startswith("  "):
                explain += " " + ln.strip()
            else:
                last = None
                prose.append(ln)
        xp = _int(kw.get("xp"), 5)
        self.quiz_ids.append(qid)
        b = {"t": name, "id": qid, "xp": xp}
        if name == "quiz":
            q, ans = [], []
            for ln in prose:
                m = re.match(r"^- (\*?)(.*)$", ln)
                if m:
                    opts.append(m.group(2).strip())
                    if m.group(1):
                        ans.append(len(opts) - 1)
                else:
                    q.append(ln)
            if not ans or len(opts) < 2:
                raise ValueError("quiz needs 2+ options and one marked with *")
            b.update(q="\n".join(q).strip(), options=opts, multi=len(ans) > 1)
            self.priv[qid] = {"kind": "quiz", "answer": ans, "explain": explain}
        elif name == "order":
            items = [re.sub(r"^\d+\.\s*", "", ln).strip() for ln in prose if re.match(r"^\d+\.", ln)]
            q = "\n".join(ln for ln in prose if not re.match(r"^\d+\.", ln)).strip()
            b.update(q=q, items=items)
            self.priv[qid] = {"kind": "order", "answer": items, "explain": explain}
        elif name == "match":
            pairs = [tuple(p.strip() for p in ln.split("=>", 1)) for ln in prose if "=>" in ln]
            q = "\n".join(ln for ln in prose if "=>" not in ln).strip()
            b.update(q=q, left=[p[0] for p in pairs], right=[p[1] for p in pairs])
            self.priv[qid] = {"kind": "match", "answer": [p[1] for p in pairs], "explain": explain}
        elif name == "fill":
            accepted, q = [], []
            for ln in prose:
                if ln.startswith("answer:"):
                    accepted += [a.strip().lower() for a in ln[7:].split("|") if a.strip()]
                else:
                    q.append(ln)
            b.update(q="\n".join(q).strip())
            self.priv[qid] = {"kind": "fill", "answer": accepted, "explain": explain}
        elif name == "keys":
            rows = [tuple(p.strip() for p in ln.split("|", 1)) for ln in prose if "|" in ln]
            b.update(q="\n".join(ln for ln in prose if "|" not in ln).strip(), rows=[{"action": a, "combo": c} for a, c in rows])
            self.priv[qid] = {"kind": "keys", "answer": [c for _, c in rows], "explain": explain}
        self.blocks.append(b)

    # ---- views -------------------------------------------------------------
    def tasks(self):
        return [b for b in self.blocks if b["t"] == "task"]

    def required_tasks(self):
        return [b for b in self.tasks() if not b.get("optional")]

    def public(self):
        return {"id": self.id, "world": self.world, "title": self.title, "summary": self.summary,
                "minutes": self.minutes, "boss": self.boss, "scene": self.scene, "keys": self.keys, "tags": self.tags,
                "image": self.image, "xp_bonus": self.xp_bonus, "blocks": self.blocks, "errors": self.errors}

    def total_xp(self):
        return (sum(b["xp"] for b in self.blocks if b["t"] in ("task", "quiz", "order", "match", "fill", "keys")
                    and not b.get("optional")) + self.xp_bonus)


class World:
    def __init__(self, path, order):
        meta, body = _meta((path / "_world.md").read_text())
        self.path, self.order = path, order
        self.id = meta.get("id") or path.name.split("-", 1)[-1]
        self.title = meta.get("title", self.id)
        self.tagline = meta.get("tagline", "")
        self.emoji = meta.get("emoji", "◆")
        self.color = meta.get("color", "#e87d0d")
        self.project = meta.get("project", "")
        self.body = body.strip()
        self.lessons = []

    def public(self):
        return {"id": self.id, "title": self.title, "tagline": self.tagline, "emoji": self.emoji, "color": self.color,
                "project": self.project, "body": self.body, "order": self.order}


class Content:
    """The whole campaign, reloaded automatically when files change."""

    def __init__(self):
        self.lock = threading.RLock()
        self.worlds, self.lessons, self.by_id = [], {}, {}
        self.sig, self.checked = None, 0.0
        self.load()

    def _signature(self):
        return tuple(sorted((str(p), p.stat().st_mtime_ns) for ext in ("*.md", "*.py") for p in CONTENT.rglob(ext)))

    def load(self):
        worlds, lessons = [], {}
        for d in sorted(p for p in CONTENT.iterdir() if p.is_dir() and re.match(r"^\d\d-", p.name)):
            if not (d / "_world.md").exists():
                continue
            w = World(d, len(worlds) + 1)
            for f in sorted(d.glob("[0-9][0-9]-*.md")):
                meta, body = _meta(f.read_text())
                les = Lesson(f, w.id, len(w.lessons) + 1, meta, body)
                if les.id in lessons:
                    les.errors.append("duplicate lesson id " + les.id)
                lessons[les.id] = les
                w.lessons.append(les.id)
            worlds.append(w)
        with self.lock:
            self.worlds, self.lessons = worlds, lessons
            self.by_id = {w.id: w for w in worlds}
            self.sig = self._signature()
            self.checked = time.time()

    def fresh(self):
        if time.time() - self.checked > 1.5:
            self.checked = time.time()
            try:
                if self._signature() != self.sig:
                    self.load()
            except Exception as e:
                print("content reload failed:", e)
        return self

    def lesson(self, lid):
        return self.fresh().lessons.get(lid)

    def ordered_lessons(self):
        self.fresh()
        return [self.lessons[l] for w in self.worlds for l in w.lessons]

    def next_after(self, lid):
        seq = self.ordered_lessons()
        for i, les in enumerate(seq):
            if les.id == lid and i + 1 < len(seq):
                return seq[i + 1]
        return None

    def total_xp(self):
        return sum(l.total_xp() for l in self.ordered_lessons())

    def errors(self):
        return {l.id: l.errors for l in self.ordered_lessons() if l.errors}

    # ---- scripts that run inside Blender -------------------------------------
    def lib_text(self):
        d = CONTENT / "lib"
        return "\n".join(p.read_text() for p in sorted(d.glob("*.py"))) if d.exists() else ""

    def starter_text(self, sid):
        p = CONTENT / "starters" / (sid + ".py")
        return p.read_text() if p.exists() else None

    def scene_script(self, les):
        """Python that builds a lesson's starting scene, or None for 'keep'."""
        if les.scene.startswith("starter:"):
            body = self.starter_text(les.scene.split(":", 1)[1])
            if body is None:
                raise FileNotFoundError("starter missing: " + les.scene)
            return self.lib_text() + "\n" + body
        return None

    def solve_script(self, les):
        return (self.lib_text() + "\n" + les.solve) if les.solve else None
