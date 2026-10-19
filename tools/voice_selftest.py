#!/usr/bin/env python3
"""Checks the spoken scripts of every lesson without needing the voice engine:

    python3 tools/voice_selftest.py

For all 62 lessons x 3 Blender generations: nothing that looks like leftover markup in a spoken sentence, no oversized
segment, every task has a segment, every segment key is stable and its spec is complete, cues are well-formed.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))
import speech  # noqa: E402
from lessons import Content  # noqa: E402

FAILS = []


def check(name, cond, extra=""):
    if not cond:
        FAILS.append("%s %s" % (name, extra))
        print("FAIL", name, extra)


# spot checks of the wording rules
CASES = {
    "[[Ctrl+A]] > **Scale**": "Control A, Scale",
    "Press [[G]] [[X]] `3` [[Enter]] now.": "Press G, X, 3, Enter, now.",       # a beat after a key sequence
    "Press [[N]] to open it.": "Press N to open it.",
    "move it 3 m along X": "move it 3 metres along X",
    "a 2 m cube": "a 2 metre cube",
    "rotate 45° around Z": "rotate 45 degrees around Z",
    "scale (2, 1, 0.5)": "scale 2, 1, 0.5",
    "4 × 2 × 1 m": "4 by 2 by 1 metres",
    "`scale = 1.0004`": "scale equals 1.0004",
    "the UVs and PBR": "the U Vees and P B R",
    "Cabin_Walls": "Cabin Walls",
    "Blender 4.2+": "Blender 4.2 and newer",
    "x = 3": "x equals 3",
}
for src, want in CASES.items():
    got = speech.clean(src)
    check("clean(%r)" % src, got == want, "-> %r, wanted %r" % (got, want))

content = Content()
seq = content.ordered_lessons()
voices = {"narrator": "af_heart", "cubby": "am_puck"}
BAD = re.compile(r"[\[\]\*`#<>|{}\\~^]|:::|\s{2,}|,\s*,")
n_seg = n_words = 0
for i, les in enumerate(seq):
    for major in (3, 4, 5):
        pos = {"idx": i + 1, "total": len(seq), "next": seq[i + 1].title if i + 1 < len(seq) else ""}
        pub, specs = speech.build_script(les, major, voices, pos)
        tag = "%s/v%d" % (les.id, major)
        check(tag + " has intro and outro", pub[0]["kind"] == "intro" and pub[-1]["kind"] == "outro")
        spoken_tasks = {s["task"] for s in pub if s["kind"] == "task"}
        check(tag + " every task is spoken", spoken_tasks == {b["id"] for b in les.tasks()}, spoken_tasks)
        for s in pub:
            check(tag + " segment %d has a spec" % s["i"], s["key"] in specs and specs[s["key"]]["chunks"])
            check(tag + " segment %d size" % s["i"], s["words"] <= 130, s["words"])
            check(tag + " segment %d cues align with chunks" % s["i"], len(s["cues"]) == len(specs[s["key"]]["chunks"]))
            for text, pause in specs[s["key"]]["chunks"]:
                check(tag + " clean sentence", not BAD.search(text) and 0 <= pause <= 1, text[:100])
                check(tag + " sentence length", len(text) <= 330, text[:80])
            for cl in s["cues"]:
                for c in cl:
                    check(tag + " cue shape", isinstance(c, dict) and c.get("t") in ("area", "obj", "cursor", "world_origin", "origin", "gizmo", "keys"), c)
        again, _ = speech.build_script(les, major, voices, pos)
        check(tag + " keys are stable", [s["key"] for s in again] == [s["key"] for s in pub])
        if major == 4:
            n_seg += len(pub)
            n_words += sum(s["words"] for s in pub)
        json.dumps(pub)                                       # must serialize

print("%d lessons, %d segments, %d words (about %d minutes of speech)" % (len(seq), n_seg, n_words, n_words // 160))
print("PASS" if not FAILS else "FAILED: %d problems" % len(FAILS))
sys.exit(1 if FAILS else 0)
