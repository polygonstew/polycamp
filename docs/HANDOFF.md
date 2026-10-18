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
| Service | `polycamp.service` (systemd user), registered in Panel |

Repo: private `github.com/polygonstew/polycamp`. Work was pushed on the branch `worktree-polycamp-build` (never to `main`).

## Run, test, extend

    python3 server/polycamp.py                  # app on :8570
    sh tools/install_service.sh                 # Linux user service
    python3 tools/install_addon.py --enable --blender blender

    blender -b --factory-startup --python tools/verify_in_blender.py            # every lesson, one Blender version
    blender -b --factory-startup --python tools/addon_selftest.py
    python3 tools/e2e.py blender                                                # server + Blender together
    /usr/bin/python3 tools/ui_smoke.py <outdir>                                  # browser (needs python playwright + chromium)
    sh tools/jscheck.sh
    blender -b --factory-startup --python tools/make_goal_images.py              # re-render content/img/*.png after library changes
    python3 tools/make_curriculum.py                                             # refresh docs/CURRICULUM.md

Test builds of 3.3.21 and 4.5.14 live in `~/blender-test/b33` and `b45` (downloaded from blender.org for this; the system Blender is 5.2.2).
Authoring guide: `docs/AUTHORING.md`. Snapshot fields: `docs/SNAPSHOT.md`.

## Not covered yet (honest list)

- **A real GUI Blender session.** Everything was verified headless. The sidebar panel drawing, the in-viewport overlay,
  GUI-only tasks (workspaces, viewport shading, view moves, "file saved") and the F12 render upload were checked by reading the
  API and in headless render runs, not by clicking through the GUI. Expect a small first-session bug or two in those spots.
  Tasks marked `untested` in the lessons are exactly the GUI-dependent ones.
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
