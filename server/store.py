"""store.py - SQLite persistence (progress, XP ledger, drill cards, renders, badges). Stdlib only."""
import json
import sqlite3
import threading
import time

from config import DATA

_lock = threading.RLock()
_db = sqlite3.connect(str(DATA / "polycamp.db"), check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.execute("PRAGMA journal_mode=WAL")
_db.executescript("""
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, val TEXT);
CREATE TABLE IF NOT EXISTS done (id TEXT PRIMARY KEY, lesson TEXT, kind TEXT, xp INTEGER, how TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS lessons (id TEXT PRIMARY KEY, started REAL, completed REAL, hints INTEGER DEFAULT 0, solution INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS ledger (n INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT, ref TEXT, xp INTEGER, gems INTEGER, note TEXT);
CREATE TABLE IF NOT EXISTS cards (id TEXT PRIMARY KEY, box INTEGER DEFAULT 0, due REAL DEFAULT 0, right INTEGER DEFAULT 0, wrong INTEGER DEFAULT 0, last REAL);
CREATE TABLE IF NOT EXISTS renders (n INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, ts REAL, meta TEXT, lesson TEXT, fav INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS badges (id TEXT PRIMARY KEY, ts REAL);
CREATE TABLE IF NOT EXISTS hints (task TEXT PRIMARY KEY, level INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS days (day TEXT PRIMARY KEY, xp INTEGER DEFAULT 0);
""")
_db.commit()


def q(sql, args=(), one=False):
    with _lock:
        cur = _db.execute(sql, args)
        rows = cur.fetchall()
        _db.commit()
    return (rows[0] if rows else None) if one else rows


def kv_get(key, default=None):
    r = q("SELECT val FROM kv WHERE key=?", (key,), one=True)
    if r is None:
        return default
    try:
        return json.loads(r["val"])
    except Exception:
        return default


def kv_set(key, val):
    q("INSERT INTO kv(key,val) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET val=excluded.val", (key, json.dumps(val)))


def now():
    return time.time()
