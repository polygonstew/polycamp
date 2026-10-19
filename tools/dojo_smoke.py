#!/usr/bin/env python3
"""Hotkey drills in a real browser: laptop-friendly alternatives, two-press cards, Skip, the key tester, keys relayed from Blender,
and the in-lesson drill. Throw-away server, headless Chromium.

    /usr/bin/python3 tools/dojo_smoke.py [outdir]
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8578
BASE = "http://127.0.0.1:%d" % PORT
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="pc-dojo-")
os.makedirs(OUT, exist_ok=True)
FAILS = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what, flush=True)
    if not ok:
        FAILS.append(what)


def post(path, data):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=20))


# What to press for a card on a laptop with no numpad (what the page must accept), in Playwright's key names.
NAMES = {"Ctrl": "Control", "Esc": "Escape", "Up": "ArrowUp", "Down": "ArrowDown", "Left": "ArrowLeft", "Right": "ArrowRight"}
LAPTOP = {"Numpad .": "Period", "Numpad /": "Slash", "Numpad -": "Minus", "Numpad +": "Shift+Equal", "Numpad *": "Shift+Digit8"}


def pw(combo):
    out, i, cur, toks = "", 0, "", []
    for ch in combo:
        if ch == "+" and cur and not cur.endswith("Numpad ") and cur.strip():
            toks.append(cur)
            cur = ""
        else:
            cur += ch
    toks.append(cur)
    keys = []
    for t in toks:
        if t in LAPTOP:
            keys.append(LAPTOP[t])
        elif t.startswith("Numpad ") and t[7:].isdigit():
            keys.append("Digit" + t[7:])
        else:
            keys.append(NAMES.get(t, t))
    return "+".join(keys)


def main():
    from playwright.sync_api import sync_playwright
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "server", "polycamp.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           env=dict(os.environ, POLYCAMP_DATA=tempfile.mkdtemp(prefix="pc-dojo-data-"), POLYCAMP_PORT=str(PORT)))
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(BASE + "/api/state", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        decks = json.load(urllib.request.urlopen(BASE + "/api/dojo/decks"))["decks"]
        allcards = json.load(urllib.request.urlopen(BASE + "/api/dojo/queue?n=500&decks=" + urllib.parse.quote("|".join(d["name"] for d in decks))))["cards"]
        by_action = {}
        for c in allcards:
            by_action.setdefault(c["action"], c)
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            pg = b.new_context(viewport={"width": 1500, "height": 950}).new_page()
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            # ---- 1. matching rules (the page's own keys.js)
            pg.goto(BASE + "/")
            pg.wait_for_timeout(400)
            r = pg.evaluate("""async () => {
                const k = await import('/js/keys.js');
                const st = { step: 0 };
                return {
                  laptopDot: k.matches('Numpad .', '.'), laptopSlash: k.matches('Numpad /', '/'), laptopDigit: k.matches('Numpad 7', '7'),
                  laptopPlus: k.matches('Ctrl+Numpad +', 'Ctrl+Shift+='), strict: k.matches('Z', 'Shift+Z'), alt: k.matches('Shift+A or Ctrl+Space', 'Ctrl+Space'),
                  seq1: k.judge('G G', 'G', st), seq2: k.judge('G G', 'G', st), seqBad: (() => { const s = { step: 0 }; k.judge('G G', 'G', s); return k.judge('G G', 'H', s); })(),
                  isSeq: !!k.seqOf('G G'), notSeq: !k.seqOf('Numpad 1') && !k.seqOf('Ctrl+Numpad +') && !k.seqOf('Shift+A'),
                };
            }""")
            check(r["laptopDot"] and r["laptopSlash"] and r["laptopDigit"] and r["laptopPlus"], "laptop stand-ins count for numpad keys")
            check(not r["strict"] and r["alt"], "wrong modifiers still fail; 'or' alternatives work")
            check(r["seq1"] == "more" and r["seq2"] == "ok" and r["seqBad"] == "wrong" and r["isSeq"] and r["notSeq"], "'G G' is a two-press card")

            # ---- 2. a whole round on a "laptop": press what each card needs, numpad cards via their stand-ins
            pg.goto(BASE + "/#/"); pg.wait_for_timeout(250); pg.goto(BASE + "/#/dojo")
            pg.wait_for_selector(".deck", timeout=8000)
            pg.get_by_text("Quick round").click()
            pg.wait_for_selector(".arena .q", timeout=5000)
            results = []
            for _ in range(10):
                if pg.locator(".arena .q").count() == 0:
                    break
                action = pg.locator(".arena .q").inner_text()
                card = by_action[action]
                pg.keyboard.press(pw(card["combo"]))
                pg.wait_for_timeout(250)
                results.append((card["combo"], "ok" in (pg.locator(".arena").get_attribute("class") or "")))
                pg.wait_for_timeout(800)
            check(len(results) >= 8 and all(ok for _, ok in results), "a Navigation round answered with laptop keys: " + ", ".join(c for c, _ in results))

            # ---- 3. the two-press card, Skip, and the idle hint (Edit Mode deck)
            pg.goto(BASE + "/#/"); pg.wait_for_timeout(250); pg.goto(BASE + "/#/dojo")
            pg.wait_for_selector(".deck", timeout=8000)
            pg.locator(".deck").nth(0).click()                                   # un-pick Navigation
            pg.locator(".deck", has_text="Edit Mode").click()
            pg.get_by_text("25 cards").click()
            pg.wait_for_selector(".arena .q", timeout=5000)
            seen_gg, skipped_one, idle_seen = False, False, False
            for _ in range(30):
                if pg.locator(".arena .q").count() == 0:
                    break
                action = pg.locator(".arena .q").inner_text()
                card = by_action[action]
                if card["combo"] == "G G":
                    pg.keyboard.press("g")
                    pg.wait_for_timeout(200)
                    mid = pg.locator(".arena .got").inner_text()
                    pg.keyboard.press("g")
                    pg.wait_for_timeout(250)
                    seen_gg = "then" in mid and "ok" in (pg.locator(".arena").get_attribute("class") or "")
                elif not skipped_one:
                    pg.locator(".arena .skip").click()
                    skipped_one = True
                    pg.wait_for_timeout(300)
                    continue
                elif not idle_seen:
                    pg.wait_for_timeout(7600)                                     # press nothing: the page should offer the way out
                    idle_seen = "Nothing arriving" in pg.locator(".arena .got").inner_text() and "pri" in (pg.locator(".arena .skip").get_attribute("class") or "")
                    pg.locator(".arena .skip").click()
                    pg.wait_for_timeout(300)
                    continue
                else:
                    pg.keyboard.press(pw(card["combo"]))
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(800)
            check(seen_gg, "'G G' needs two presses and shows progress after the first")
            stored = pg.evaluate("JSON.parse(localStorage.getItem('pc_dojo_skipped') || '[]').length")
            check(skipped_one and stored >= 1, "Skip works and is remembered (%d stored)" % stored)
            check(idle_seen, "after 7 s of nothing the page says so and highlights Skip")

            # ---- 4. keys relayed from Blender answer the card (server -> SSE -> page), nothing else needed
            pg.goto(BASE + "/#/"); pg.wait_for_timeout(250); pg.goto(BASE + "/#/dojo")
            pg.wait_for_selector(".deck", timeout=8000)
            pg.get_by_text("Quick round").click()
            pg.wait_for_selector(".arena .q", timeout=5000)
            relayed = 0
            for _ in range(4):
                if pg.locator(".arena .q").count() == 0:
                    break
                card = by_action[pg.locator(".arena .q").inner_text()]
                post("/api/bridge/keys", {"combo": card["combo"]})
                pg.wait_for_timeout(350)
                relayed += "ok" in (pg.locator(".arena").get_attribute("class") or "")
                pg.wait_for_timeout(800)
            check(relayed >= 3, "keys relayed from Blender answered the cards (%d of 4)" % relayed)

            # ---- 5. the key tester
            pg.goto(BASE + "/#/"); pg.wait_for_timeout(250); pg.goto(BASE + "/#/dojo")
            pg.wait_for_selector(".keytest", timeout=8000)
            pg.locator(".keytest").click()
            pg.keyboard.press("Shift+KeyA")
            pg.wait_for_timeout(200)
            shown = pg.locator(".keytest .out").inner_text()
            check("Shift" in shown and "KeyA" in shown, "the key tester shows what the page receives: " + shown.replace("\n", " "))
            pg.screenshot(path=os.path.join(OUT, "dojo_menu.png"))

            # ---- 6. the drill inside a lesson, laptop keys, relayed keys and skip
            pg.goto(BASE + "/#/lesson/navigate")
            pg.wait_for_selector(".keydrill", timeout=8000)
            area = pg.locator(".keydrill")
            area.scroll_into_view_if_needed()
            area.click()
            for key in ("Digit1", "Digit5", "Period"):
                pg.keyboard.press(key)
                pg.wait_for_timeout(250)
            check("Shading pie menu" in area.inner_text(), "lesson drill accepts number row and '.' for the numpad keys")
            post("/api/bridge/keys", {"combo": "Z"})                              # the last row, pressed in Blender
            pg.wait_for_timeout(600)
            check("Done" in area.inner_text(), "lesson drill accepts a key relayed from Blender")
            pg.screenshot(path=os.path.join(OUT, "lesson_drill.png"))
            b.close()
            check(not [e for e in errors if "favicon" not in e], "no JS errors" + ("" if not errors else ": " + errors[0][:120]))
    finally:
        srv.terminate()
    print("screenshots in", OUT)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
