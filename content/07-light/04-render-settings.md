---
id: render-settings
title: Rendering on a CPU Without Losing a Week
summary: Samples, denoising, bounces, resolution and Simplify: a budget you can plan around.
minutes: 14
scene: starter:bare-render
keys: F12, Ctrl+B, Alt+B
tags: render, cpu
xp: 45
---
You met some of these settings in the very first world. This is the deeper pass, with real numbers, on the actual diorama.

## What a render costs

Cycles shoots rays through every pixel, bounces them around the scene and averages the results. The cost scales roughly with:

    time  ≈  pixels  ×  samples  ×  bounces  ×  scene complexity

So you have four levers, and the order to pull them is: **resolution** first (cheap to cut), then **samples with a denoiser**, then **bounces**, then **scene complexity** (Simplify, fewer subdivisions, smaller textures).

On the machine this course was written for (a 4-thread laptop CPU), the diorama takes about **half a minute for a 800 × 450 draft at 24 samples**, **a minute or two at 1280 × 720 and 64 samples**, and **five to ten minutes at 1920 × 1080 and 128 samples**. Your numbers will differ but the shape is right: pixels are the expensive part.

## The knobs

- **Samples**: more samples, less noise. 64 plus the denoiser is a sweet spot for stills, 24 for drafts. **Noise Threshold** (adaptive sampling) stops early where the image is already clean.
- **Denoise**: OpenImageDenoise (OIDN) is a free, CPU-friendly neural denoiser built into Blender. It cleans a 64-sample render to look like a 500-sample one, at the price of some very fine detail.
- **Light Paths > Max Bounces**: the default (12) is overkill for most scenes. **6** total with 2 diffuse and 3 glossy is a good CPU setting. Set **Volume bounces to 0** unless you use fog.
- **Caustics** (Reflective and Refractive): off. They are noisy and rarely worth the samples.
- **Clamp Indirect** about 10 stops a single hot ray from leaving white "fireflies" on the image.
- **Simplify** (Render properties): caps the Subdivision level and texture size for the whole scene. A subdivided model at *Max Subdivision 2* is far cheaper than one at 4.
- **Resolution %**: scales the output. 50% for drafts, 100% for finals.
- **Render Region**: [[Ctrl+B]] in the camera view and drag a rectangle. Only that area renders. Perfect for checking one detail. [[Ctrl+Alt+B]] clears it.

## Colour management

The **View Transform** (Render > Color Management) decides how scene brightness is shown on a screen. **Filmic** in 3.x and **AgX** in 4.x and newer both roll bright light off gracefully instead of clipping to white. A glowing window with detail in the glow needs one of them. Standard clips bluntly. Keep the default.

:::task id=engine title="Cycles on the CPU" xp=8
Switch the engine to **Cycles** and the device to **CPU**.
check: render.engine == 'CYCLES' and render.cy_device == 'CPU' :: Engine is Cycles, device is CPU
hint: Render properties > Render Engine. Device is under it.
:::
:::solve task=engine
matkit.cpu_preset(bpy.context.scene, 'standard')
:::

:::task id=samples title="64 samples, denoised, adaptive" xp=10
Set **Max Samples to 96 or fewer**, keep **Noise Threshold** (adaptive sampling) on, and enable **OpenImageDenoise**.
check: render.cy_samples <= 96 and render.cy_use_adaptive_sampling :: Samples 96 or fewer with adaptive sampling on
check: render.cy_use_denoising and render.cy_denoiser == 'OPENIMAGEDENOISE' :: Denoise on with OpenImageDenoise
hint: Sampling > Render: Max Samples, and tick Noise Threshold. Denoise panel: tick it and choose OpenImageDenoise.
:::
:::solve task=samples
pass
:::

:::task id=bounces title="Fewer bounces" xp=10
Set **Total max bounces to 8 or fewer** and keep **Volume bounces at 0**.
check: render.cy_max_bounces <= 8 and render.cy_volume_bounces == 0 :: Max bounces 8 or less, volume bounces 0
hint: Render properties > Light Paths > Max Bounces. Total is the first number.
:::
:::solve task=bounces
pass
:::

:::task id=res title="1280 × 720 at 100%" xp=8
Set the output size to **1280 × 720** at **100%**. A good all-round size for a still.
check: render.res_x == 1280 and render.res_y == 720 and render.res_pct == 100 :: Output is 1280 by 720 at 100%
hint: Output properties > Format. Width, Height and the Resolution % slider.
:::
:::solve task=res
pass
:::

:::task id=simplify title="Simplify the scene" xp=10
Turn on **Simplify** and cap the render subdivision at **2** or lower.
check: render.simplify and render.simplify_subdiv <= 2 :: Simplify on, max render subdivision 2 or lower
hint: Render properties > Simplify. Tick it, open the Render sub-panel and set Max Subdivision.
:::
:::solve task=simplify
sc = bpy.context.scene
sc.render.use_simplify = True
sc.render.simplify_subdivision_render = 2
:::

:::note tip title="Work in draft"
Keep a **Draft** setting (480 × 270 at 16 samples) while you move lights around and a **Final** setting for the one run you leave overnight. The Polycamp sidebar's **CPU-friendly render preset** switches
between them.
:::

:::reveal title="Why the denoiser does not like animation"
Denoising a still is great. Denoising an animation can make details flicker from frame to frame, because each frame is denoised separately. For animations, either use more samples with a gentle
denoise, or render with the denoiser's *albedo and normal* passes enabled. We cover animation render budgets in World 8.
:::

:::order id=o1 xp=6
Order these from the cheapest to pull first, to the most work to change, when a render takes too long.
1. Lower the Resolution %
2. Lower the samples and rely on the denoiser
3. Cut the maximum bounces
4. Simplify the scene or reduce subdivisions
5. Remodel the heavy parts
:::

:::quiz id=q1 xp=5
Doubling the width and height of a render does what to the time?
- Doubles it
- *Roughly quadruples it
- Nothing
explain: Pixels scale with width × height, so 2× in both directions is 4× the pixels and roughly 4× the time.
:::
