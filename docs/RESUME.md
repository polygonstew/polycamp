# Build log

Newest first.

## 2026-10-18 (session 1, one long run)

1. **Add-on first** (it fixes the snapshot schema everything else is checked against). Snapshot, link threads, commands, scene kit,
   PBR material builder, UV layout drawer, sidebar panel. Tested on 3.3.21, 4.5.14, 5.2.2.
2. **Server**: bridge with long-poll commands, check evaluator (AST allow-list), lesson parser, game engine, SSE, Texture Lab backend,
   Dojo. End-to-end test with a real headless Blender.
3. **Web app** and first look. Texture Lab with a browser pixel engine (seamless blend, height / normal / roughness / AO).
4. **Verification harness** (`verify_in_blender.py`): builds each lesson's start scene, requires that no check already passes, runs the
   solution, requires all checks to pass. It caught many real mistakes (contradictory checks, wrong vertex counts, bmesh extrude keeping the
   old face, API differences on 3.3 and 5.x).
5. **Content library** (diorama builders, procedural materials, UV helpers, compositor helpers), then the 62 lessons world by world,
   verifying each on 5.2.2 and finally all of them on all three versions.
6. **Creative pass** after the user asked for a less "AI-looking" result: new visual identity, no emoji, plainer copy.
7. Docs, installers, service, Panel registration.

Decisions worth remembering: lessons are plain Markdown so they can be edited by hand; checks are expressions, not code; the
add-on is thin and the server owns content so lessons can change without reinstalling; progress is SQLite in `./data`; nothing is
locked (the map only recommends the next step) because the learner already knows some Blender.
