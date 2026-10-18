# Polycamp: handoff (start here)

Written 2026-10-18 when the usage limit hit mid-build. Branch `worktree-polycamp-build`; nothing is merged to master yet.

## What it is
Boot.dev-style campaign for learning Blender, built for 2 monitors (and 1). A web app (stdlib Python, :8570, LAN)
plus a Blender add-on (**Polycamp Link**) that reads the live scene, checks lesson tasks, builds lesson starter
scenes, and moves textures/renders/UV layouts both ways. Works on Blender **3.3, 4.x, 5.x** (tested on 3.3.21,
4.5.14 and 5.2.2). CPU friendly by design.

## Layout
- `addon/polycamp_link/`: Blender add-on (snapshot.py = the scene JSON contract, link.py = threads + tick, commands.py,
  scenekit.py, matkit.py, uvlayout.py, ui.py). Served as a zip at `/addon/polycamp_link.zip` with the server address baked in.
- `server/`: polycamp.py (routes, SSE), engine.py (game: XP, gems, streak, badges, hints, live check evaluation),
  lessons.py (markdown parser), checks.py (safe expression evaluator), bridge.py, texlab.py (ComfyUI + texture sets + Godot export), dojo.py, store.py (sqlite).
- `web/`: vanilla JS modules, hash router. `js/views/*` one file per screen. `proc.js` = Texture Lab pixel engine.
- `content/NN-world/_world.md` + `NN-lesson.md`, `content/starters/*.py` (scene builders), `content/lib/*.py` (diorama + material builders shared by all scripts), `content/dojo/keys.md`.
- `tools/`: `verify_in_blender.py` (builds each lesson's start scene, runs its `:::solve`, asserts checks), `addon_selftest.py`, `e2e.py` (server + real Blender), `ui_smoke.py` (headless Chromium), `render_ref.py`, `jscheck.sh`.

Lesson format: see the existing lessons. Blocks: `:::task id= title= xp=` with `check: expr :: label`, `hint:`, `:::solve` or `:::solve task=ID`, quiz/order/match/fill/keys, cubby/note/v/reveal/goal. Mark tasks `untested` when they depend on GUI state; `allow_initial` when true from the start.

## Done and verified
- Add-on self-test passes on 3.3 / 4.5 / 5.2 (`blender -b --factory-startup --python tools/addon_selftest.py`).
- `tools/e2e.py` passes (real Blender connects, learner actions tick tasks, XP, lesson completes).
- UI smoke passes (no JS errors on any page). Texture Lab (procedural) looks right.
- Worlds 1 (Boot Sequence, 7 lessons), 2 (Vertex Town, 7 lessons) and lesson 1 of 3 (Modifier Mountain) written and verified on 5.2.2.
- Diorama library renders (`tools/render_ref.py`) on 3.3, 4.5, 5.2.

## Still to do (in this order)
1. **User's request (2026-10-18): a creative pass to remove the "AI look"**. Replace emoji with custom SVG/typographic marks, give the UI a distinct hand-made identity (not stock dark cards + gradients), rewrite copy in a plain human voice (no em-dash habit, no "not X but Y", no tidy triplets), vary layouts, check every screen by screenshot.
2. World 3 lessons 2-6 (starters already written: `post-and-half`, `wall-cutter`, `profile-lathe`): mirror/array, solidify/bevel, boolean, screw + curve bevel, boss lantern (`build_lantern` in lib).
3. Worlds 4-10 per the plan: 4 Cabin Cove (environment modelling, rocks, trees, terrain, assemble), 5 Material Marsh (Principled, nodes, procedural, emission/glass, world), 6 UV Isle (UV, seams, Texture Lab + ComfyUI, PBR maps, painting, bake, glTF to Godot/Kiln), 7 Lightfall Lake (lights, 3-point, camera, CPU render settings, compositor glare, first render boss), 8 Keyframe Keep (keys, graph editor, camera anim, shape keys/rig, animation render, turntable boss), 9 Node Nebula (geometry nodes scatter, pipeline, Python), 10 Guild Hall (final: Lantern Cabin at Dusk render + animation + Godot export). `build_diorama()` in `content/lib/10_diorama.py` is the reference final scene.
4. Goal images for `:::goal img=` blocks (e.g. `mug.png`) in `content/img/` (render the solve scene; add `auto_camera`/studio helpers to lib).
5. Run `tools/verify_in_blender.py` on 3.3 (`~/blender-test/b33/blender`) and 4.5 (`b45`) for every lesson. Only 5.2.2 was run for lessons so far.
6. Install as a user service (systemd `polycamp.service`, port 8570; Windows: `run.bat`), `tools/install_addon.py`, register in Panel, add `docs/ARCHITECTURE.md`, `AUTHORING.md`, `SNAPSHOT.md`.
7. Merge branch to master (user allows ff-merge in ~/.jcodes repos) once the above is in.

## Run it
`python3 server/polycamp.py` then http://<LAN-ip>:8570. Test data goes to `$POLYCAMP_DATA` (default `./data`, gitignored).
Blender builds for testing: `~/blender-test/b33`, `~/blender-test/b45`, system `blender` is 5.2.2.

## Gotchas learned
- Background Blender 3.3 cannot render Workbench/EEVEE without a display; use Cycles for headless renders.
- `bpy.data.is_dirty` stays True after `save_as_mainfile` in background mode, so "file saved" checks are `untested`.
- bmesh `extrude_face_region` keeps the original face; delete it to match the editor's Extrude.
- World shader `Generated` coordinate = ray direction; z = height above the horizon.
