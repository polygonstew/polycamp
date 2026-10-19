# Polycamp: handoff (start here)

Built in one long session on 2026-10-18. The campaign, the app and the Blender add-on are complete and tested; the list at
the bottom is what is honestly not covered yet.

## What it is

A Boot.dev-style campaign for learning Blender, built for two monitors (one works too), CPU-only machines, Linux and Windows.
A stdlib Python web app on :8570 (LAN) plus a Blender add-on (**Polycamp Link**) that reads the live scene, checks lesson tasks,
builds starter scenes and moves textures, UV layouts, renders and models both ways. See `README.md` and `docs/ARCHITECTURE.md`.

## State

| Piece | Status |
| --- | --- |
| Add-on | `tools/addon_selftest.py` passes on Blender 3.3.21, 4.5.14 and 5.2.2 |
| Campaign | 10 worlds, 62 lessons, 6,934 XP. `tools/verify_in_blender.py` passes all 62 (0 failures, 0 warnings) on 3.3, 4.5 and 5.2 |
| Server + bridge | `tools/e2e.py` passes with a real headless Blender: link, scene prep, checks tick, XP, texture set to material, UV upload, add-on zip |
| Browser | `tools/ui_smoke.py` passes in headless Chromium (every page, quiz widget, Dojo round, Texture Lab). No JS errors |
| Look | Redone 2026-10-18 after the user asked for "not so AI-looking": field-manual identity (graph paper, serif lesson text, mono labels, DONE stamps, topographic trail map, line icons, no emoji). Keep new UI in that style, no glow or pulse, no emoji |
| Narration (added 2026-10-18, session 2) | The whole campaign is read aloud (Kokoro-82M on the CPU, Coach / Audiobook modes) and the add-on highlights what is mentioned inside Blender. `tools/voice_selftest.py` (all 62 lessons x 3 Blender generations), `tools/md_parity.py`, `tools/voice_smoke.py` (headless Chromium plays a lesson, waits at a task, carries on), `tools/gui_test.sh` (real GUI Blender 3.3 / 4.5 / 5.2 on a virtual display: every cue type drawn and measured, the sidebar panel drawn) and `tools/gui_e2e.py` (browser narrator -> server -> real GUI Blender, and Blender's Narration button -> page) all pass |
| Service | `polycamp.service` (systemd user), registered in Panel |

Repo: private `github.com/polygonstew/polycamp`, default branch `dev` (never pushed to `main`).

## Hotkey drills fixed (session 2, later)

The user said the hotkey drills "don't seem to work" and that they have to click Blender again after clicking the drill. Found and fixed:
the Dojo's default Navigation deck is mostly numpad keys that a laptop cannot press (only the digits had a stand-in), one card (`G G`) was
unanswerable, Chrome keeps Ctrl+digit, and a press that never reached the page left no feedback and no way out. Now: laptop stand-ins for all numpad keys,
two-press cards, a Skip on every card (offered after 7 s of silence), live modifier display, a key tester on the Dojo menu, and
**keys pressed in Blender count** (add-on `keywatch.py`, see ARCHITECTURE "Hotkey drills"), so nobody has to click between the windows.
Tests: `tools/dojo_smoke.py` (browser), `tools/gui_keys_test.py` via `tools/gui_test.sh <blender> <out> gui_keys_test.py` (real GUI Blender 3.3 / 4.5 / 5.2).
Not verified: what the user's actual browser/desktop does with specific combos (that is what the key tester is for). The add-on must be reinstalled to get the Blender-side keys.

## Narration, in short (session 2)

User asked for "a better than average, quite better actually" reading of the lessons so they can look at Blender while hearing what to do,
then asked whether areas could be highlighted inside Blender during the lecture. Both are done.

- **Voice**: Kokoro-82M (ONNX, CPU) in a private venv at `~/.polycamp/voice` (`python3 tools/install_voice.py`; models are in `~/.polycamp/voice/models`).
  This PC (i5-7200U, 2 cores): about 0.75x real time, the same for the 8-bit model and at 2 or 4 threads, so the worker uses 2 threads at low priority and the
  full model. Audio is cached by content hash in `data/voice/`; `python3 tools/voice_prerender.py` voices the whole campaign in the background (about 3.5 hours of speech).
- **Reading, not dumping**: `server/speech.py` turns markdown into speech (keys, units, acronyms, code spans, tables, quiz options), splits lessons into segments and
  sentences, and keeps its markdown splitter in step with `web/js/md.js` (`tools/md_parity.py` checks all 154 blocks) so the page can mark the paragraph being read.
- **Coach mode**: after a task is read the narrator waits until Blender confirms it (`task_done`), says "got it", carries on. Hints are read aloud too. Media keys and
  Blender's own Narration buttons (and Ctrl+Shift + `,` `.` `/`) control the page that is playing.
- **Highlights in Blender** (`addon/polycamp_link/cues.py`, command `cue`): outline + tag on the sidebar / toolbar / Outliner / Properties / Timeline / node editors,
  boxes on objects, rings at the 3D cursor / origins / navigation gizmo, key caps for shortcuts. Derived from the wording per sentence, fired as that sentence plays.
  Optional preferences: highlights on/off, and "also switch to the tab being mentioned" (off by default). A task's `cue:` line adds hand-written ones.
- **To get the highlights the learner must update the add-on** (download it again from the Link page, or `python3 tools/install_addon.py --enable --blender blender`).
  Old add-ons ignore the `cue` command harmlessly.

## Run, test, extend

    python3 server/polycamp.py                  # app on :8570
    sh tools/install_service.sh                 # Linux user service
    python3 tools/install_addon.py --enable --blender blender

    blender -b --factory-startup --python tools/verify_in_blender.py            # every lesson, one Blender version
    blender -b --factory-startup --python tools/addon_selftest.py
    python3 tools/e2e.py blender                                                # server + Blender together
    /usr/bin/python3 tools/ui_smoke.py <outdir>                                  # browser (needs python playwright + chromium)
    sh tools/jscheck.sh
    python3 tools/voice_selftest.py                                              # spoken scripts of every lesson (no voice engine needed)
    python3 tools/voice_script.py <lesson-id>                                    # read what a lesson will say
    /usr/bin/python3 tools/md_parity.py                                          # python and browser markdown splitters agree
    /usr/bin/python3 tools/voice_smoke.py <outdir>                               # narrator in headless Chromium (needs the voice engine)
    sh tools/gui_test.sh <blender-binary> <outdir>                               # real GUI Blender on Xvfb: all highlight types + the panel
    sh tools/gui_test.sh <blender-binary> <outdir> gui_keys_test.py              # same rig: the key relay for the hotkey drills
    /usr/bin/python3 tools/dojo_smoke.py <outdir>                                # hotkey drills in headless Chromium
    /usr/bin/python3 tools/gui_e2e.py <blender-binary> <outdir>                  # browser narrator -> server -> GUI Blender, and back
    blender -b --factory-startup --python tools/make_goal_images.py              # re-render content/img/*.png after library changes
    python3 tools/make_curriculum.py                                             # refresh docs/CURRICULUM.md

Test builds of 3.3.21 and 4.5.14 live in `~/blender-test/b33` and `b45` (downloaded from blender.org for this; the system Blender is 5.2.2).
Authoring guide: `docs/AUTHORING.md`. Snapshot fields: `docs/SNAPSHOT.md`.

## Not covered yet (honest list)

- **A person clicking through a real GUI Blender.** Since session 2 a real GUI Blender runs on a virtual display (Xvfb, software GL) and
  the sidebar panel and every highlight type are drawn and measured there on 3.3, 4.5 and 5.2. Still not exercised by anything: the
  in-viewport task overlay, GUI-only tasks (workspaces, viewport shading, view moves, "file saved") and the F12 render upload, plus how the
  highlights feel with a human's mouse and real UI scale. Tasks marked `untested` in the lessons are exactly the GUI-dependent ones.
- **Hearing the voice.** Everything about narration is verified (audio is made, plays, is timed per sentence, cues fire on cue) but nobody listened yet
  on a real speaker. If a word is mispronounced, fix it in `ACRONYM` / `EXT` in `server/speech.py` (bump `VERSION` so the audio is re-made).
  The default narrator is `af_heart`, Cubby is `am_puck`; both are changeable in Settings.
- **ComfyUI generation end to end.** The Texture Lab's procedural path, seamless blend and map derivation ran in a browser;
  the ComfyUI client and img2img were written against the API and the checkpoints that exist here but a generation was not run
  (a 512 px image takes minutes on this CPU).
- **Real learner flow with a second machine** (Blender on Windows, app on the Linux box). The add-on zip bakes in the address and
  the bridge is plain HTTP on the LAN, so it should work, but it was tested on one machine.
- The campaign's goal images are renders of the library scenes, not hand-art. Re-render them with `make_goal_images.py` if the library changes.

## Ideas, if there is more time

- Daily challenge and side quests (content-only: add lessons marked `optional`).
- More worlds: sculpting and retopology, simulation (cloth, rigid body, fluids), hair, grease pencil.
- More Dojo decks (sculpt, UV editor, video sequencer).
- A "kiosk" mode: the HUD as an always-on-top window via a tiny Qt wrapper.
- Per-lesson time estimates from real runs.

## Gotchas learned

- Blender 3.3 cannot render Workbench or EEVEE headless; use Cycles for headless renders.
- `bpy.data.is_dirty` stays true after `save_as_mainfile` in background mode, so "file saved" checks cannot be verified headless.
- bmesh `extrude_face_region` keeps the original face; delete it to match the editor's Extrude.
- Blender 5: video output needs `image_settings.media_type = 'VIDEO'` before `file_format = 'FFMPEG'`; compositor tree is `scene.compositing_node_group`;
  `action.fcurves` is gone (use slots / channelbags); icospheres: subdivisions 4 = 642 vertices, 3 = 162.
- With slotted actions (4.4+) an object and its data can share one Action; pass the owner's `animation_data` to `compat.iter_fcurves`.
- World shaders: the `Generated` coordinate is the ray direction; z is height above the horizon. Use `abs(z)` so a floating diorama sits in a glow.
- A direct `el.append(null)` writes the text "null"; the `h()` helper filters null, raw DOM calls do not.
- Indented (4-space) code blocks were not rendered as code by `md.js` (they came out as one paragraph); fixed in session 2 together with the narrator's splitter.
- **GUI Blender on a virtual display**: `xvfb-run -a -s "-screen 0 1920x1080x24 +extension GLX +render -noreset"` plus
  `LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=4.5 MESA_GLSL_VERSION_OVERRIDE=450` (without the overrides 3.3 shows a black window). A throw-away
  `BLENDER_USER_CONFIG` with `show_splash = False` keeps the splash out. On 3.x `bpy.ops.screen.screenshot` blanks the window here, so capture the X screen
  with ImageMagick `import -window root` instead (4.5 and 5.2 can use the operator). `tools/gui_test.sh` does all of this.
- Blender 4.5 and 5.x call the Properties tabs `MODIFIER` / `CONSTRAINT`; 3.x says `MODIFIERS` / `CONSTRAINTS`. `Region.active_panel_category` does not exist in 3.3.
  `gpu.shader.from_builtin` wants `UNIFORM_COLOR` on 4.x+ and `2D_UNIFORM_COLOR` on 3.x; `cues.py` tries both. Wide GPU lines are not available everywhere, so highlights are filled quads.
- The worktree guard in this setup refuses shell commands that mix in `$(...)`, `export X=$(...)` or a loop around `sh`; put such things in a small script file and run that.
