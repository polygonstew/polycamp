#!/usr/bin/env python3
"""Print what a lesson will sound like, sentence by sentence, with the pause after each and the Blender highlights.

    python3 tools/voice_script.py transform          [blender-major, default 4]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))
import speech  # noqa: E402
from lessons import Content  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
lid, major = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4
content = Content()
les = content.lesson(lid)
if les is None:
    sys.exit("no lesson called %r. Ids: %s" % (lid, ", ".join(l.id for l in content.ordered_lessons())))
seq = content.ordered_lessons()
i = [l.id for l in seq].index(lid)
pos = {"idx": i + 1, "total": len(seq), "next": seq[i + 1].title if i + 1 < len(seq) else ""}
pub, specs = speech.build_script(les, major, {"narrator": "af_heart", "cubby": "am_puck"}, pos)
for s in pub:
    print("[%d] %s%s%s  (%d words)" % (s["i"], s["kind"], " / cubby voice" if s["voice"] == "cubby" else "", "  task=" + s["task"] if s["task"] else "", s["words"]))
    for (text, pause), cues in zip(specs[s["key"]]["chunks"], s["cues"]):
        print("     %.2fs | %s" % (pause, text))
        for c in cues:
            print("           -> %s" % c)
print("\n%d segments, %d words, about %.1f minutes" % (len(pub), sum(s["words"] for s in pub), sum(s["words"] for s in pub) / 160))
