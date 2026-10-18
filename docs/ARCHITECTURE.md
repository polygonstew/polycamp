# Architecture

    Blender  ──(add-on, 2 threads)──►  Polycamp server  ──(SSE)──►  browser tabs
       ▲                                     │
       └────── commands (long-poll) ◄────────┘             ComfyUI ◄── server (texture jobs)

## The add-on (`addon/polycamp_link`)

| Module | Job |
| --- | --- |
| `snapshot.py` | Reads the whole session into one JSON dict. The contract is in `SNAPSHOT.md`. Read-only, main thread. |
| `link.py` | A `bpy.app.timers` tick on the main thread builds snapshots (only sent when something changed), runs commands, counts operators from `wm.operators`. Two daemon threads do the network: **uplink** posts snapshot + results + heartbeat to `/api/bridge/sync`, **downlink** long-polls `/api/bridge/poll` for commands. Blender never waits on the network. |
| `commands.py` | What the app can ask Blender to do: fresh scene (with a backup of unsaved work first), run a lesson script, select, set mode, import an image, build a PBR material from maps, export a UV layout, CPU render preset, set a preference, save, export glTF, screenshot. |
| `scenekit.py` | Scene-building helpers that behave the same on 3.3, 4.x and 5.x (bmesh primitives, PBR material, lights, camera, wipe). |
| `matkit.py` | Material from image maps, and the CPU render presets. |
| `uvlayout.py` | Draws a UV layout PNG with numpy: teal coverage, red overlap, white edges. |
| `compat.py` | Every version difference the add-on cares about (Principled socket names, engine ids, compositor tree, slotted actions). |
| `ui.py` | Preferences, sidebar panel (N > Polycamp), operators, optional in-viewport task overlay. |

Renders are caught with `render_complete` handlers and uploaded to the app automatically.

## The server (`server/`, standard library only)

| Module | Job |
| --- | --- |
| `polycamp.py` | `ThreadingHTTPServer`, routing, SSE stream, add-on zip builder (bakes the server address in), uploads. |
| `bridge.py` | Connected Blender clients, latest snapshot, command queue with long-poll and awaitable results. |
| `engine.py` | The game: active lesson, live check evaluation, XP / gems / streak / badges, hints, claims, answers. One instance owns all learner state. |
| `checks.py` | The check language: small Python expressions over the snapshot, validated with an AST allow-list. |
| `lessons.py` | Loads `content/` into worlds, lessons, tasks and questions. Hot reloads when files change. |
| `gamify.py` | Levels (scaled so the last level is "finished everything"), rank titles, badges. |
| `dojo.py` | Flash cards and the Leitner schedule. |
| `texlab.py` | ComfyUI client (txt2img and img2img, CPU presets), texture sets on disk, send to Blender, Godot / Kiln export with a `StandardMaterial3D` file. |
| `store.py`, `config.py`, `hub.py` | SQLite, settings, server-sent-event fan-out. |

### How a task gets ticked

1. Blender's snapshot arrives (`POST /api/bridge/sync`). `engine.on_snapshot` stores it.
2. For the active lesson, each task's checks run against the snapshot (`checks.make_env`).
3. A task counts when all its checks have stayed true for 0.6 s **and** at least one check was false earlier (so a scene that is already "right" does not give free XP; such tasks show a *Claim* button).
4. XP, gems, streak and badges update; `task_done`, `award`, `lesson_done`, `badge` events go out over SSE.

## The browser (`web/`)

Plain ES modules, hash router, no build. `app.js` boots and owns the top bar and global reactions. `views/*.js` is one file
per screen. `mission.js` is the live panel (right column, bottom dock or pop-out HUD). `widgets.js` holds the quiz,
ordering, matching, fill-in and hotkey-drill widgets. `proc.js` is the Texture Lab's pixel engine (tileable noise,
seamless blend, height / normal / roughness / AO derivation). `icons.js` is the line-icon set.

## Content scripts

Starter scenes and solutions are plain `bpy` code. The server prepends `content/lib/*.py` (materials, the diorama
builders, UV and compositor helpers) and the add-on runs the result with `kit`, `matkit`, `compat` and `note_op`
available. `tools/verify_in_blender.py` runs every lesson's starter and solution in real Blender and asserts the checks.
