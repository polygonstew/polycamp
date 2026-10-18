"""link.py - the live connection to the Polycamp server.

Main thread: a bpy.app.timers tick builds snapshots, executes commands, tracks operators.
Two daemon threads do the network so Blender never waits on it:
  uplink   POST /api/bridge/sync   snapshot + command results (+ heartbeat) -> HUD back
  downlink GET  /api/bridge/poll   long-poll for commands from the app
"""
import hashlib
import json
import os
import platform
import queue
import threading
import time
import traceback
import urllib.parse
import urllib.request
import uuid
from collections import deque

import bpy
from bpy.app.handlers import persistent

from . import commands, config, snapshot

ADDON_ID = __package__
CLIENT_ID = uuid.uuid4().hex[:10]
HOME = os.path.join(os.path.expanduser("~"), ".polycamp")
CACHE = os.path.join(HOME, "cache")


class S:
    """All mutable link state (module-level singleton)."""
    enabled = False
    server = config.DEFAULT_SERVER
    connected = False
    last_error = ""
    last_ok = 0.0
    hud = {}
    toast = None
    inbox = deque()
    results = []
    uploads = queue.Queue()
    pending = None
    up_event = threading.Event()
    stop_ev = threading.Event()
    threads = []
    last_sig = None
    last_snap_t = 0.0
    snap_every = 0.6
    tick_s = 0.25
    dirty = True
    ops_seen = []
    op_counts = {}
    view_sig = None
    view_changes = 0
    sel_sig = None
    sel_changes = 0
    render_info = {}
    render_t0 = 0.0
    render_frames = 0
    send_after = 0.0
    errors_logged = set()


def prefs():
    try:
        return bpy.context.preferences.addons[ADDON_ID].preferences
    except Exception:
        return None


def log(*a):
    print("[polycamp]", *a)


# ------------------------------------------------------------------ http

def _url(path):
    return S.server.rstrip("/") + path


def post(path, payload, timeout=8):
    data = json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(_url(path), data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def get(path, timeout=8):
    with urllib.request.urlopen(_url(path), timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def download(server_path, dest):
    """Fetch a server file (e.g. /files/textures/x.png) into dest. Blocks; only used for small files."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with urllib.request.urlopen(_url(urllib.parse.quote(server_path, safe="/%")), timeout=20) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def queue_upload(kind, name, path, meta=None):
    S.uploads.put((kind, name, path, meta or {}))
    S.up_event.set()


def client_info():
    return {"cid": CLIENT_ID, "blender": bpy.app.version_string, "bver": list(bpy.app.version),
            "platform": platform.system().lower(), "host": platform.node(), "addon": list(config.ADDON_VERSION),
            "proto": config.PROTO, "background": bool(bpy.app.background)}


# ------------------------------------------------------------------ threads

def _uplink():
    backoff = 1.0
    while not S.stop_ev.is_set():
        S.up_event.wait(2.0)
        S.up_event.clear()
        if S.stop_ev.is_set():
            break
        snap, S.pending = S.pending, None
        results, S.results = S.results, []
        body = {"client": client_info(), "results": results}
        if snap is not None:
            body["snapshot"] = snap
        try:
            resp = post("/api/bridge/sync", body)
            S.connected, S.last_ok, S.last_error = True, time.time(), ""
            S.hud = resp.get("hud", S.hud)
            if resp.get("toast"):
                S.toast = (resp["toast"], time.time())
            backoff = 1.0
            _drain_uploads()
        except Exception as e:
            S.connected, S.last_error = False, str(e)[:120]
            S.results = results + S.results
            if snap is not None and S.pending is None:
                S.pending = snap
            S.stop_ev.wait(backoff)
            backoff = min(backoff * 2, 10.0)


def _drain_uploads():
    while True:
        try:
            kind, name, path, meta = S.uploads.get_nowait()
        except queue.Empty:
            return
        try:
            with open(path, "rb") as f:
                blob = f.read()
            q = urllib.parse.urlencode({"kind": kind, "name": name, "meta": json.dumps(meta), "cid": CLIENT_ID})
            req = urllib.request.Request(_url("/api/bridge/upload?" + q), data=blob,
                                         headers={"Content-Type": "application/octet-stream"})
            urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            log("upload failed:", e)


def _downlink():
    backoff = 1.0
    while not S.stop_ev.is_set():
        if not S.connected:
            S.stop_ev.wait(1.0)
            continue
        try:
            resp = get("/api/bridge/poll?cid=%s&wait=15" % CLIENT_ID, timeout=25)
            for c in resp.get("commands", []):
                S.inbox.append(c)
            backoff = 1.0
        except Exception:
            S.stop_ev.wait(backoff)
            backoff = min(backoff * 2, 8.0)


# ------------------------------------------------------------------ main-thread work

def _track_ops():
    """Count operators the user ran (from the redo registry), so lessons can ask 'did you loop cut?'."""
    try:
        cur = [op.bl_idname for op in bpy.context.window_manager.operators]
    except Exception:
        return
    old = S.ops_seen
    added = cur
    for k in range(len(old) + 1):
        tail = old[k:]
        if cur[:len(tail)] == tail:
            added = cur[len(tail):]
            break
    for i in added:
        S.op_counts[i] = S.op_counts.get(i, 0) + 1
    S.ops_seen = cur


def count_op(idname, n=1):
    """Test hook / script hook: pretend the user ran an operator."""
    S.op_counts[idname] = S.op_counts.get(idname, 0) + n
    S.dirty = True


def _snapshot():
    _track_ops()
    snap = snapshot.build()
    ui = snap.get("ui", {})
    vm = ui.pop("view_matrix", None)
    if vm is not None:
        sig = hash(tuple(vm))
        if S.view_sig is not None and sig != S.view_sig:
            S.view_changes += 1
        S.view_sig = sig
    sel = (tuple(snap.get("selected", [])), snap.get("active"))
    if S.sel_sig is not None and sel != S.sel_sig:
        S.sel_changes += 1
    S.sel_sig = sel
    snap["ops"] = dict(S.op_counts)
    snap["counters"] = {"view_changes": S.view_changes, "sel_changes": S.sel_changes}
    snap["render_last"] = S.render_info
    snap["link"] = {"addon": list(config.ADDON_VERSION), "cid": CLIENT_ID}
    return snap


def snapshot_now():
    """Build + queue a snapshot immediately (used by tests and by 'check now')."""
    snap = _snapshot()
    S.pending = snap
    S.last_sig = None
    S.up_event.set()
    return snap


def _push_if_changed():
    snap = _snapshot()
    sig = hashlib.md5(json.dumps(snap, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if sig != S.last_sig:
        S.last_sig = sig
        S.pending = snap
        S.up_event.set()


def _drain_commands():
    n = 0
    while S.inbox and n < 6:
        cmd = S.inbox.popleft()
        n += 1
        res = commands.run(cmd)
        S.results.append(res)
        S.dirty = True
        S.up_event.set()


def tick():
    try:
        if not S.enabled:
            return 0.5
        _drain_commands()
        if bpy.app.is_job_running("RENDER"):
            return 0.5
        _maybe_send_render()
        now = time.time()
        if S.dirty or now - S.last_snap_t >= S.snap_every:
            t0 = time.time()
            _push_if_changed()
            S.dirty = False
            S.last_snap_t = time.time()
            S.snap_every = min(2.0, max(0.5, (S.last_snap_t - t0) * 6))   # back off if snapshots are slow
    except Exception:
        key = traceback.format_exc()[-200:]
        if key not in S.errors_logged:
            S.errors_logged.add(key)
            traceback.print_exc()
    return S.tick_s


# ------------------------------------------------------------------ render handlers

@persistent
def _on_render_init(scene, *a):
    S.render_t0, S.render_frames = time.time(), 0


@persistent
def _on_render_pre(scene, *a):
    S.render_frames += 1


@persistent
def _on_render_complete(scene, *a):
    try:
        r = scene.render
        info = {"time": round(time.time() - S.render_t0, 1), "frames": S.render_frames, "ts": int(time.time()),
                "engine": r.engine, "res": [r.resolution_x * r.resolution_percentage // 100,
                                            r.resolution_y * r.resolution_percentage // 100],
                "ok": True}
        try:
            info["samples"] = scene.cycles.samples if r.engine == "CYCLES" else None
        except Exception:
            pass
        S.render_info = info
        S.dirty = True
        p = prefs()
        if S.render_frames == 1 and (p is None or p.auto_send_renders):
            S.send_after = time.time() + 0.3        # the Render Result may not be readable inside the handler
    except Exception:
        traceback.print_exc()


def _maybe_send_render():
    """Called from tick: upload a finished render once its image is readable."""
    if not S.send_after or time.time() < S.send_after:
        return
    img = bpy.data.images.get("Render Result")
    if img is None or img.size[0] == 0:
        if time.time() > S.send_after + 6:
            S.send_after = 0.0
        return
    S.send_after = 0.0
    try:
        send_render_result()
    except Exception as e:
        log("render upload skipped:", e)


@persistent
def _on_render_cancel(scene, *a):
    S.render_info = dict(S.render_info, ok=False, cancelled=True)
    S.dirty = True


@persistent
def _on_load(*a):
    S.dirty = True
    S.last_sig = None
    S.ops_seen = []


def send_render_result(info=None):
    """Save the Render Result as a PNG and upload it to the app's Trophy Room."""
    img = bpy.data.images.get("Render Result")
    if img is None or img.size[0] == 0:
        raise RuntimeError("There is no render yet. Press F12 first.")
    os.makedirs(CACHE, exist_ok=True)
    name = time.strftime("render-%Y%m%d-%H%M%S.png")
    path = os.path.join(CACHE, name)
    fmt = bpy.context.scene.render.image_settings.file_format
    try:
        bpy.context.scene.render.image_settings.file_format = "PNG"
        img.save_render(path)
    finally:
        bpy.context.scene.render.image_settings.file_format = fmt
    meta = dict(info or S.render_info)
    meta["blend"] = bpy.path.basename(bpy.data.filepath)
    queue_upload("render", name, path, meta)
    return name


# ------------------------------------------------------------------ lifecycle

HANDLERS = (("render_init", _on_render_init), ("render_pre", _on_render_pre),
            ("render_complete", _on_render_complete), ("render_cancel", _on_render_cancel),
            ("load_post", _on_load))


def start():
    p = prefs()
    S.server = (p.server_url if p else config.DEFAULT_SERVER).strip() or config.DEFAULT_SERVER
    S.enabled = True
    S.stop_ev.clear()
    S.dirty = True
    S.last_sig = None
    S.threads = [threading.Thread(target=_uplink, daemon=True, name="polycamp-up"),
                 threading.Thread(target=_downlink, daemon=True, name="polycamp-down")]
    for t in S.threads:
        t.start()
    if not bpy.app.timers.is_registered(tick):
        bpy.app.timers.register(tick, first_interval=0.5, persistent=True)
    S.up_event.set()


def stop():
    S.enabled = False
    S.connected = False
    S.stop_ev.set()
    S.up_event.set()
    for t in S.threads:
        t.join(timeout=1.0)
    S.threads = []


def restart():
    stop()
    start()


def register():
    for name, fn in HANDLERS:
        lst = getattr(bpy.app.handlers, name)
        if fn not in lst:
            lst.append(fn)
    p = prefs()
    if p is None or p.enabled:
        start()


def unregister():
    stop()
    for name, fn in HANDLERS:
        lst = getattr(bpy.app.handlers, name)
        if fn in lst:
            lst.remove(fn)
    if bpy.app.timers.is_registered(tick):
        bpy.app.timers.unregister(tick)
