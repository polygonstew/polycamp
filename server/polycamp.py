#!/usr/bin/env python3
"""Polycamp - boot camp for Blender. Entry point + HTTP routing (stdlib only, Linux/Windows/macOS).

    python3 server/polycamp.py          ->  http://<this-pc>:8570  (reachable over the LAN)

Routing lives here; the game is engine.py, the Blender link is bridge.py, textures are texlab.py.
"""
import io
import json
import mimetypes
import queue
import re
import socket
import sys
import time
import urllib.parse
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config                      # noqa: E402
import dojo                        # noqa: E402
import store                       # noqa: E402
import texlab                      # noqa: E402
import voice                       # noqa: E402
from bridge import Bridge          # noqa: E402
from engine import Engine          # noqa: E402
from hub import Hub                # noqa: E402
from lessons import Content       # noqa: E402

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")

HUB = Hub()
BRIDGE = Bridge()
CONTENT = Content()
ENGINE = Engine(CONTENT, BRIDGE, HUB)
VOICE = voice.Voice()
SAFE = re.compile(r"[^A-Za-z0-9._-]")
FILE_KINDS = ("renders", "textures", "uv", "models", "shots")
BLOCKED_CMDS = {"run_script"}          # only the engine may send scripts


def build_addon_zip(host):
    """polycamp_link.zip with this server's address baked in as the default."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(config.ADDON_SRC.glob("*.py")):
            text = p.read_text()
            if p.name == "config.py":
                text = re.sub(r'DEFAULT_SERVER = ".*?"', 'DEFAULT_SERVER = "http://%s"' % host, text)
            z.writestr("polycamp_link/" + p.name, text)
    return buf.getvalue()


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class H(BaseHTTPRequestHandler):
    server_version = "Polycamp/" + config.VERSION

    def log_message(self, fmt, *a):                      # keep the console readable
        if "/api/bridge/" not in self.path and "/api/events" not in self.path:
            sys.stderr.write("%s %s\n" % (self.command, self.path))

    # ---- helpers -----------------------------------------------------------
    def send_json(self, data, status=200):
        raw = json.dumps(data, separators=(",", ":"), default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def send_bytes(self, raw, ctype, status=200, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def send_file(self, path):
        path = Path(path)
        if not path.is_file():
            return self.send_json({"error": "not found"}, 404)
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_bytes(path.read_bytes(), ctype)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def body_json(self):
        raw = self.body()
        return json.loads(raw) if raw else {}

    def fail(self, e, status=400):
        self.send_json({"ok": False, "error": str(e)}, status)

    # ---- dispatch ----------------------------------------------------------
    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        u = urllib.parse.urlparse(self.path)
        path, qs = u.path, dict(urllib.parse.parse_qsl(u.query))
        try:
            if path.startswith("/api/"):
                return self.api(method, path[5:], qs)
            if method != "GET":
                return self.send_json({"error": "not found"}, 404)
            if path == "/addon/polycamp_link.zip":
                zipped = build_addon_zip(self.headers.get("Host") or "localhost:%d" % config.PORT)
                return self.send_bytes(zipped, "application/zip",
                                       extra={"Content-Disposition": 'attachment; filename="polycamp_link.zip"'})
            if path.startswith("/files/"):
                return self.serve_data(path[7:])
            if path.startswith("/voice/"):
                return self.serve_voice(path[7:])
            if path.startswith("/cimg/"):
                return self.send_file(config.CONTENT / "img" / SAFE.sub("_", path[6:]))
            rel = path.lstrip("/") or "index.html"
            f = (config.WEB / rel).resolve()
            if config.WEB.resolve() in f.parents and f.is_file():
                return self.send_file(f)
            return self.send_file(config.WEB / "index.html")       # SPA fallback
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self.fail(e, 500)
            except Exception:
                pass

    def serve_data(self, rel):
        kind, _, name = urllib.parse.unquote(rel).partition("/")
        if kind not in FILE_KINDS or ".." in name:
            return self.send_json({"error": "not found"}, 404)
        f = (config.DATA / kind / name).resolve()
        if (config.DATA / kind).resolve() not in f.parents:
            return self.send_json({"error": "not found"}, 404)
        self.send_file(f)

    def serve_voice(self, name):
        """Narration audio (/voice/<key>.ogg) and its timing (/voice/<key>.json). Waits for synthesis if it has to,
        and understands Range requests, which browsers need for seeking."""
        m = re.fullmatch(r"([0-9a-f]{16})\.(ogg|wav|json)", name)
        if not m:
            return self.send_json({"error": "not found"}, 404)
        key, ext = m.groups()
        try:
            path = VOICE.wait(key, 170)
        except KeyError:
            return self.send_json({"error": "unknown segment; reload the lesson"}, 404)
        if path is None:
            return self.send_json({"error": VOICE.err or "voice not ready"}, 503)
        if ext == "json":
            return self.send_bytes(json.dumps(VOICE.meta(key) or {}).encode(), "application/json")
        raw = path.read_bytes()
        ctype = "audio/ogg" if path.suffix == ".ogg" else "audio/wav"
        rng = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", "") or "")
        if rng and (rng.group(1) or rng.group(2)):
            a = int(rng.group(1)) if rng.group(1) else max(0, len(raw) - int(rng.group(2)))
            b = int(rng.group(2)) if rng.group(1) and rng.group(2) else len(raw) - 1
            b = min(b, len(raw) - 1)
            if a > b:
                return self.send_bytes(b"", ctype, 416, {"Content-Range": "bytes */%d" % len(raw)})
            return self.send_bytes(raw[a:b + 1], ctype, 206, {"Content-Range": "bytes %d-%d/%d" % (a, b, len(raw)), "Accept-Ranges": "bytes"})
        self.send_bytes(raw, ctype, 200, {"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=86400"})

    # ---- API ---------------------------------------------------------------
    def voice_get(self, route, qs):
        if route == "voice/status":
            return VOICE.status()
        if route.startswith("voice/script/"):
            major = int(qs.get("major") or BRIDGE.blender_major() or 4)
            sc = VOICE.script(CONTENT, route[13:], major, config.load())
            if sc is None:
                return {"error": "no such lesson"}
            if qs.get("warm") and VOICE.installed():
                VOICE.warm(sc, int(qs.get("from") or 0))
            return sc
        return None

    def voice_post(self, route, data):
        if route == "voice/ensure":
            n = 0
            for k in data.get("keys", [])[:40]:
                try:
                    n += VOICE.request(k, int(data.get("prio", 1))) is not None
                except KeyError:
                    pass
            return {"ok": True, "queued": n}
        if route == "voice/prerender":
            scope = data.get("scope", "all")
            ids = [l.id for l in CONTENT.ordered_lessons()]
            if scope.startswith("world:"):
                w = CONTENT.by_id.get(scope[6:])
                ids = list(w.lessons) if w else []
            elif scope.startswith("lesson:"):
                ids = [scope[7:]] if scope[7:] in ids else []
            majors = [int(m) for m in data.get("majors", [3, 4, 5])]
            n = VOICE.prerender(CONTENT, ids, majors, config.load())
            return {"ok": True, "queued": n, "lessons": len(ids)}
        if route == "voice/cancel":
            return {"ok": True, "cancelled": VOICE.cancel_bulk()}
        if route == "voice/clear":
            return {"ok": True, "removed": VOICE.clear()}
        if route in ("voice/preview", "voice/say"):       # preview a voice / read a hint aloud
            st = config.load()
            v = SAFE.sub("", str(data.get("voice") or st["voice_narrator"]))
            text = str(data.get("text") or "Select the cube, press [[G]] [[X]] `3` [[Enter]], and it slides exactly 3 m along the X axis.")[:500]
            key = VOICE.say(v, text)
            return {"ok": bool(key), "key": key}
        if route == "voice/ctl":                 # transport buttons from the Blender panel / a keymap -> whichever page is playing
            HUB.publish("voice_ctl", action=str(data.get("action", "")), pid=data.get("pid"))
            return {"ok": True}
        if route == "voice/cue":                 # highlight something in Blender
            if not config.load().get("voice_cues", True) and data.get("cues"):
                return {"ok": True, "skipped": "cues are off"}
            try:
                BRIDGE.command("cue", {"cues": data.get("cues", []), "ttl": float(data.get("ttl", 8)), "src": data.get("src", "")})
            except RuntimeError as e:
                return {"ok": False, "error": str(e)}
            return {"ok": True}
        return None

    def api(self, method, route, qs):
        if route == "events":
            return self.sse()
        r = self.api_get(route, qs) if method == "GET" else self.api_post(route, qs)
        self.send_json(r if r is not None else {"error": "not found"}, 200 if r is not None else 404)

    def api_get(self, route, qs):
        if route == "state":
            return {"profile": ENGINE.profile(), "settings": config.load(), "bridge": BRIDGE.status(),
                    "version": config.VERSION, "lan": "http://%s:%d" % (lan_ip(), config.PORT),
                    "active": ENGINE.run["lesson"] if ENGINE.run else None, "toast": ENGINE.toast,
                    "live": {"hud": ENGINE.hud(), "scene": ENGINE.scene_summary()}}
        if route == "overview":
            return ENGINE.overview()
        if route.startswith("lesson/"):
            return ENGINE.lesson_view(route[7:])
        if route == "bridge/status":
            return BRIDGE.status()
        if route == "bridge/poll":
            return {"commands": BRIDGE.poll(qs.get("cid", ""), min(float(qs.get("wait", 10)), 20))}
        if route == "dojo/decks":
            return {"decks": dojo.deck_list(), "totals": dojo.totals()}
        if route == "dojo/queue":
            decks = [d for d in qs.get("decks", "").split("|") if d]
            return {"cards": dojo.queue(decks, int(qs.get("n", 15)))}
        if route == "badges":
            return {"badges": ENGINE.all_badges()}
        if route == "trophies":
            rows = store.q("SELECT * FROM renders ORDER BY ts DESC")
            return {"renders": [{"n": r["n"], "name": r["name"], "ts": r["ts"], "lesson": r["lesson"], "fav": r["fav"],
                                 "meta": json.loads(r["meta"] or "{}")} for r in rows]}
        if route == "settings":
            return config.load()
        if route == "scene":
            return {"snapshot": BRIDGE.snapshot(), "summary": ENGINE.scene_summary()}
        if route == "cheatsheet":
            return {"decks": dojo.load()}
        if route.startswith("voice/"):
            return self.voice_get(route, qs)
        return texlab.get(route, qs, ENGINE, BRIDGE)

    def api_post(self, route, qs):
        if route == "bridge/upload":
            return self.upload(qs)
        data = self.body_json()
        try:
            if route == "bridge/sync":
                return self.bridge_sync(data)
            if route == "bridge/command":
                if data.get("cmd") in BLOCKED_CMDS:
                    return {"ok": False, "error": "That command is reserved for lessons."}
                return BRIDGE.command(data["cmd"], data.get("args"), data.get("cid"), float(data.get("wait", 0)))
            if route == "lesson/start":
                return ENGINE.start(data["id"])
            if route == "lesson/prep":
                return ENGINE.prep(data.get("cid"), wait=not data.get("async") and "cid" not in data)
            if route == "lesson/hint":
                return ENGINE.hint(data.get("task"))
            if route == "lesson/claim":
                return ENGINE.claim(data["task"], bool(data.get("honor")))
            if route == "lesson/solution":
                return ENGINE.solution(bool(data.get("run")), data.get("cid"))
            if route == "answer":
                return ENGINE.answer(data["id"], data.get("value"))
            if route == "dojo/result":
                return self.dojo_result(data)
            if route == "settings":
                return config.save(data)
            if route == "trophies/fav":
                store.q("UPDATE renders SET fav=? WHERE n=?", (int(bool(data.get("fav"))), int(data["n"])))
                return {"ok": True}
            if route.startswith("voice/"):
                return self.voice_post(route, data)
            if route == "reset":
                if data.get("confirm") == "RESET":
                    ENGINE.reset_progress()
                    return {"ok": True}
                return {"ok": False, "error": "send confirm=RESET"}
            return texlab.post(route, qs, data, ENGINE, BRIDGE, HUB)
        except (KeyError, RuntimeError, ValueError, FileNotFoundError) as e:
            return {"ok": False, "error": str(e.args[0] if isinstance(e, KeyError) and e.args else e)}

    # ---- specific handlers ---------------------------------------------------
    def bridge_sync(self, body):
        BRIDGE.sync(body, self.client_address[0])
        snap = body.get("snapshot")
        if snap is not None:
            hud = ENGINE.on_snapshot(snap)
        else:
            hud = ENGINE.hud()
            ENGINE.publish_live()
        out = {"ok": True, "hud": hud}
        if ENGINE.toast:
            out["toast"] = ENGINE.toast
        return out

    def dojo_result(self, d):
        box = dojo.result(d["id"], bool(d["ok"]))
        if d["ok"]:
            n = dojo.totals()["right"]
            if n % 3 == 0:
                ENGINE.award(1, 1 if n % 12 == 0 else 0, "dojo", d["id"], "dojo")
            else:
                ENGINE.check_badges()
        return {"box": box, "totals": dojo.totals()}

    def upload(self, qs):
        kind, name = qs.get("kind", ""), SAFE.sub("_", qs.get("name", "file"))
        raw = self.body()
        meta = {}
        try:
            meta = json.loads(qs.get("meta") or "{}")
        except ValueError:
            pass
        folder = {"render": "renders", "uvlayout": "uv", "model": "models", "shot": "shots"}.get(kind)
        if folder is None:
            return {"ok": False, "error": "unknown upload kind"}
        (config.DATA / folder / name).write_bytes(raw)
        if kind == "render":
            store.q("INSERT INTO renders(name,ts,meta,lesson) VALUES(?,?,?,?)",
                    (name, time.time(), json.dumps(meta), ENGINE.run["lesson"] if ENGINE.run else ""))
            HUB.publish("render", name=name, meta=meta)
            ENGINE.check_badges()
        elif kind == "uvlayout":
            ENGINE.set_flag("uv_looks")
            HUB.publish("uv", name=name, stats=meta)
        elif kind == "model":
            HUB.publish("model", name=name, **texlab.export_model_file(name, ENGINE))
        else:
            HUB.publish("shot", name=name)
        return {"ok": True, "name": name}

    def sse(self):
        sub = HUB.subscribe()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            ENGINE.publish_live(force=True)
            self.wfile.write(b"retry: 2000\n\n")
            self.wfile.flush()
            while True:
                try:
                    msg = sub.get(timeout=12)
                    self.wfile.write(("data: %s\n\n" % msg).encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            HUB.unsubscribe(sub)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64


def main():
    errs = CONTENT.errors()
    for lid, es in errs.items():
        print("content error in %s: %s" % (lid, "; ".join(es)))
    srv = Server((config.HOST, config.PORT), H)
    print("Polycamp %s  |  %d worlds, %d lessons, %d XP  |  http://%s:%d" % (
        config.VERSION, len(CONTENT.worlds), len(CONTENT.lessons), CONTENT.total_xp(), lan_ip(), config.PORT))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("bye")


if __name__ == "__main__":
    main()
