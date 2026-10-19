# Polycamp

A boot camp for Blender. You do the work in Blender. A small add-on reports your scene to a local web app, and
the app ticks each task off when your scene really matches it. Built for two monitors (it works on one), CPU-only
machines, Linux and Windows.

62 lessons in 10 worlds, from the default cube to a lantern-lit cabin that you model, texture, light, animate
and render yourself. Verified against Blender **3.3, 4.5 and 5.2**.

## Run it

    python3 server/polycamp.py          # or ./run.sh, or run.bat on Windows
    # then open http://<this-pc>:8570 from any machine on your network

Python 3.8+ and nothing else. Progress lives in `./data` (SQLite and your renders and textures).

Install as a service on Linux: `sh tools/install_service.sh`.

## Connect Blender

1. Open the app, click **Blender not linked** in the top bar, download `polycamp_link.zip`
   (it already contains this server's address).
2. Blender 3.3: Edit > Preferences > Add-ons > Install. Blender 4.2 and newer: the arrow menu > Install from Disk.
   Or on the same PC: `python3 tools/install_addon.py --enable --blender blender`.
3. In a 3D viewport press **N**, open the **Polycamp** tab. It says *Linked*.

## Hear the lessons (optional)

    python3 tools/install_voice.py              # once: about 330 MB, no GPU, works on Windows too
    python3 tools/voice_prerender.py            # optional: voice every lesson in the background (a few hours of CPU)

Without the pre-render a lesson is voiced as you go (about 0.75x real time on a 2-core laptop), and it is kept after
that. Pick voices and speed in Settings > Narration. Media keys, or **Ctrl+Shift+ , . /** inside Blender, replay, skip
and pause. After updating the add-on (download it again from the Link page) the highlights show up in Blender.

## What is in it

| | |
| --- | --- |
| **The campaign** | 10 worlds: setup, mesh modelling, modifiers, environment, materials, UV and textures, light and render, animation, geometry nodes and pipeline, the final boss. Each lesson has tasks that are checked live, quizzes, hints and a solution script. |
| **Hotkey Dojo** | Flash cards you answer by pressing the real keys, with spaced repetition. |
| **Texture Lab** | Tileable textures (procedural, ComfyUI on the CPU, or your own picture), seamless blending, normal / roughness / height / AO maps, sent to Blender or exported to Godot or Kiln. |
| **UV Lab** | Pull an object's UV layout out of Blender, paint on it, optionally repaint with ComfyUI img2img, send it back. |
| **Renders** | Every render you finish in Blender lands here automatically. |
| **Narration** | Press **Listen** on any lesson and it is read aloud in a natural voice (Kokoro, runs on the CPU, no GPU). In *Coach* mode it waits at every task until Blender confirms it, then says "got it" and carries on. While a sentence is spoken, the add-on outlines what it mentions inside Blender: the sidebar, Outliner, the cube, the 3D cursor, and the keys to press. |
| **Two-screen layout** | Lesson on one side, live checklist and scene mirror on the other. A pop-out HUD window for the second monitor, or a docked panel and an in-viewport overlay on a single screen. |

## Layout of the repo

    addon/polycamp_link/   the Blender add-on
    server/                the web app's Python server (standard library only)
    web/                   the browser app (plain JS modules, no build step)
    content/               the campaign: worlds, lessons, starter scenes, shared script library, Dojo cards, images
    tools/                 verification, installers, render helpers
    docs/                  architecture, authoring guide, snapshot contract, curriculum, CPU tips, handoff

Start with `docs/HANDOFF.md` if you are picking the project up.
