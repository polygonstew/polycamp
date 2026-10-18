"""bridge.py - the server side of the Blender link: who is connected, their latest scene snapshot,
and a command queue Blender picks up by long-polling. Commands return results (optionally awaited)."""
import itertools
import threading
import time
from collections import deque

ALIVE_S = 7.0


class Bridge:
    def __init__(self):
        self.cv = threading.Condition()
        self.clients = {}        # cid -> {info, ip, seen, q, snap, snap_t}
        self.results = {}        # command id -> result dict
        self.seq = itertools.count(1)
        self.was_connected = False

    # ---- state ---------------------------------------------------------------
    def _alive(self, c):
        return time.time() - c["seen"] < ALIVE_S

    def primary(self):
        """The most recently active live client (Blender instance), or None."""
        with self.cv:
            live = [c for c in self.clients.values() if self._alive(c)]
        return max(live, key=lambda c: c["seen"]) if live else None

    def connected(self):
        return self.primary() is not None

    def status(self):
        with self.cv:
            cl = [{"cid": cid, "blender": c["info"].get("blender"), "bver": c["info"].get("bver"),
                   "host": c["info"].get("host"), "platform": c["info"].get("platform"), "ip": c["ip"],
                   "alive": self._alive(c), "ago": round(time.time() - c["seen"], 1),
                   "file": ((c["snap"] or {}).get("file") or {}).get("name", ""),
                   "background": c["info"].get("background", False)} for cid, c in self.clients.items()]
        prim = self.primary()
        return {"connected": prim is not None, "primary": next((k for k, c in self.clients.items() if c is prim), None),
                "clients": sorted(cl, key=lambda x: x["ago"])}

    def snapshot(self):
        c = self.primary()
        return c["snap"] if c else None

    def blender_major(self):
        c = self.primary()
        return (c["info"].get("bver") or [0])[0] if c else 0

    # ---- from Blender ---------------------------------------------------------
    def sync(self, body, ip):
        """Heartbeat + optional snapshot + command results. Returns the client record."""
        info = body.get("client", {})
        cid = info.get("cid", "unknown")
        with self.cv:
            c = self.clients.get(cid)
            if c is None:
                c = self.clients[cid] = {"info": info, "ip": ip, "seen": 0, "q": deque(), "snap": None, "snap_t": 0}
            c["info"], c["ip"], c["seen"] = info, ip, time.time()
            for r in body.get("results", []):
                self.results[r.get("id")] = r
            if len(self.results) > 200:
                for k in list(self.results)[:100]:
                    self.results.pop(k, None)
            if body.get("snapshot") is not None:
                c["snap"], c["snap_t"] = body["snapshot"], time.time()
            self.cv.notify_all()
        return c

    def poll(self, cid, wait):
        """Long-poll: block up to `wait` seconds for commands addressed to this client."""
        end = time.time() + wait
        with self.cv:
            while True:
                c = self.clients.get(cid)
                if c is not None:
                    c["seen"] = time.time()
                    if c["q"]:
                        cmds = list(c["q"])
                        c["q"].clear()
                        return cmds
                left = end - time.time()
                if left <= 0:
                    return []
                self.cv.wait(min(left, 2.0))

    # ---- to Blender -----------------------------------------------------------
    def command(self, cmd, args=None, cid=None, wait=0):
        """Queue a command. With wait>0 blocks for the result and returns it; else returns {"id": ...}."""
        with self.cv:
            target = self.clients.get(cid) if cid else None
        if target is None or not self._alive(target):
            target = self.primary()
        if target is None:
            raise RuntimeError("Blender isn't linked. Open Blender with the Polycamp Link add-on enabled.")
        cmd_id = "c%d" % next(self.seq)
        with self.cv:
            target["q"].append({"id": cmd_id, "cmd": cmd, "args": args or {}})
            self.cv.notify_all()
        if wait <= 0:
            return {"id": cmd_id, "queued": True}
        end = time.time() + wait
        with self.cv:
            while cmd_id not in self.results:
                left = end - time.time()
                if left <= 0:
                    return {"id": cmd_id, "ok": False, "msg": "Blender didn't answer in time (is it busy?)"}
                self.cv.wait(min(left, 1.0))
            return self.results.pop(cmd_id)
