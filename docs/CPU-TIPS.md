# Blender on a CPU, with 11 GB of RAM

The course is built around a machine without a usable GPU (a 2-core laptop CPU). These are the rules it teaches.

**Viewport.** Model in Solid. Material Preview for colour checks. Rendered view only briefly. Subdivision at 1 or 2 in the
viewport, higher only for the render. Statistics overlay on.

**Render.** Cycles on the CPU, OpenImageDenoise on, adaptive sampling on. 24 samples for drafts, 64 for stills.
Max bounces 6, volume bounces 0, caustics off, clamp indirect 10. Resolution % 50 while iterating. Simplify to cap subdivisions.
`matkit.cpu_preset` (the add-on's one-click button) sets all of it.

**Measured here** (4 threads, the library's diorama): 800 × 450 at 24 samples about 15 s; 960 × 540 at 64 samples about 40 s;
1280 × 720 at 64 samples roughly 1.5 minutes. Pixels are the expensive part.

**Animation.** Time one frame, multiply. Image sequence rather than video so a crash loses nothing. Persistent Data on.

**Textures.** 1024 pixels for most props, one 2048 for a hero. Reuse maps. Procedural materials cost no memory.

**Many copies.** Linked duplicates, collection instances, Geometry Nodes instances. Do not realise instances.

**ComfyUI** (Texture Lab): LCM LoRA with 5 steps at 512 px, about 30 s per step on this CPU, so a texture takes a couple of
minutes. Quality mode (16 steps, no LCM) takes many times longer. One job at a time.

**Verifying content** does not need a GPU either: `tools/verify_in_blender.py` runs headless. Blender 3.3's Workbench and EEVEE
need a display even with `-b`; use Cycles for headless renders.
