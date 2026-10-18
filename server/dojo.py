"""dojo.py - the Hotkey Dojo: flash cards from content/dojo/*.md with a small spaced-repetition (Leitner) schedule."""
import random
import re
import time

import store
from config import CONTENT

INTERVALS = [0, 60, 600, 86400, 3 * 86400, 10 * 86400]     # seconds until a card is due again, per box


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load():
    """decks: {deck name: [{id, deck, action, combo, tip}]} - '## Deck' headers, 'Action | Combo | tip' lines."""
    decks = {}
    d = CONTENT / "dojo"
    for f in sorted(d.glob("*.md")) if d.exists() else []:
        deck = None
        for line in f.read_text().splitlines():
            if line.startswith("## "):
                deck = line[3:].strip()
                decks.setdefault(deck, [])
            elif deck and "|" in line and not line.startswith("#"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    decks[deck].append({"id": _slug(deck) + ":" + _slug(parts[0]), "deck": deck, "action": parts[0],
                                        "combo": parts[1], "tip": parts[2] if len(parts) > 2 else ""})
    return decks


def deck_list():
    out = []
    rows = {r["id"]: r for r in store.q("SELECT * FROM cards")}
    now = time.time()
    for name, cards in load().items():
        due = sum(1 for c in cards if c["id"] not in rows or rows[c["id"]]["due"] <= now)
        known = sum(1 for c in cards if c["id"] in rows and rows[c["id"]]["box"] >= 3)
        out.append({"name": name, "cards": len(cards), "due": due, "known": known})
    return out


def queue(decks, n=15):
    allc = [c for name, cs in load().items() if not decks or name in decks for c in cs]
    rows = {r["id"]: r for r in store.q("SELECT * FROM cards")}
    now = time.time()
    due, new, rest = [], [], []
    for c in allc:
        r = rows.get(c["id"])
        if r is None:
            new.append(c)
        elif r["due"] <= now:
            due.append((r["due"], c))
        else:
            rest.append((r["box"], c))
    due.sort(key=lambda x: x[0])
    random.shuffle(new)
    rest.sort(key=lambda x: x[0] + random.random())
    out = [c for _, c in due] + new + [c for _, c in rest]
    return out[:n]


def result(card_id, ok):
    r = store.q("SELECT * FROM cards WHERE id=?", (card_id,), one=True)
    box = r["box"] if r else 0
    box = min(box + 1, len(INTERVALS) - 1) if ok else 0
    now = time.time()
    store.q("INSERT INTO cards(id,box,due,right,wrong,last) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET box=?, due=?, right=right+?, wrong=wrong+?, last=?",
            (card_id, box, now + INTERVALS[box], int(ok), int(not ok), now, box, now + INTERVALS[box], int(ok), int(not ok), now))
    return box


def totals():
    r = store.q("SELECT COALESCE(SUM(right),0) AS r, COALESCE(SUM(wrong),0) AS w FROM cards", one=True)
    return {"right": r["r"], "wrong": r["w"]}
