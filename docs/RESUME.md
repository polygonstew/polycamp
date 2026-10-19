# Build log

Newest first.

## 2026-10-18 (session 2: narration and highlights)

Asked for: a much better than average reading of the lessons, so the learner can watch Blender while hearing what to do; then, whether the
things being talked about can be highlighted inside Blender.

1. Picked **Kokoro-82M** (ONNX) for the voice: best sound I know that runs on a CPU. Benchmarked on the i5-7200U: 0.75-0.8x real time whatever the model
   (8-bit or full) or thread count, so: full model, 2 threads, low priority, everything cached, optional bulk pre-render.
2. `speech.py`: lesson markdown -> segments -> sentences, written for the ear (keys, units, acronyms, code). Swept all 62 lessons x 3 Blender generations until no
   leftover markup was left. Found and fixed on the way: indented code blocks that `md.js` rendered as a paragraph.
3. `voice.py` / `voice_worker.py`: priority queue, content-hash cache, on-demand worker, per-sentence timings. Range-capable audio route.
4. `voice.js` + bar: Coach and Audiobook modes, hints read aloud, media keys, owner logic when two windows are open, browser-speech fallback.
5. Highlights: cues derived per sentence (`speech.derive_cues`), sent when the sentence is spoken (`/api/voice/cue` -> bridge -> `cues.py`).
6. Discovered a real GUI Blender runs on Xvfb with software GL, which closed the biggest verification gap from session 1: built `tools/gui_test.sh` (every cue measured
   in screenshots) and `tools/gui_e2e.py`, ran them on 3.3, 4.5 and 5.2. They found two version differences (tab ids, 3.x screenshots) that are now handled.
7. Docs, installer (`install_voice.py`), pre-render CLI, self-tests.

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
