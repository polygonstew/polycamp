"""hub.py - Server-Sent Events fan-out. Every open browser tab (lesson screen, pop-out HUD...) subscribes."""
import json
import queue
import threading


class Hub:
    def __init__(self):
        self.subs = set()
        self.lock = threading.Lock()

    def subscribe(self):
        q = queue.Queue(maxsize=300)
        with self.lock:
            self.subs.add(q)
        return q

    def unsubscribe(self, q):
        with self.lock:
            self.subs.discard(q)

    def publish(self, type_, **data):
        msg = json.dumps(dict(data, type=type_), separators=(",", ":"))
        with self.lock:
            subs = list(self.subs)
        for q in subs:
            try:
                q.put_nowait(msg)
            except queue.Full:                      # a stuck tab must not block the rest
                self.unsubscribe(q)
