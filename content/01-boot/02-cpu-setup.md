---
id: cpu-setup
title: Make Blender Behave on a CPU
summary: Preferences and render settings that keep a GPU-less machine usable.
minutes: 12
scene: fresh
keys: F12, Z, Ctrl+Z
tags: setup, cpu, render
xp: 40
---
:::cubby smug
No graphics card? Fine. Half the Blender tutorials on the internet assume you own one. We will quietly
ignore them and make your CPU the hero. It is slower, yes. It is also very, very patient.
:::

## The two places time goes

Blender spends your CPU's attention in two places. **The viewport**, where you model, and **the
render**, where you wait. You control both separately, and almost every setting that matters lives in
one of them.

**Viewport.** Model in *Solid* mode. It is nearly free. *Material Preview* and *Rendered* shading are
fine for a quick look, but leaving them on while you push vertices around is how a laptop fan learns to
scream.

**Render.** Cycles is the renderer that works on any CPU. Its cost is roughly
`pixels × samples × scene complexity`. Cut pixels or samples and the time falls with them.

## Preferences worth five minutes

Open **Edit > Preferences**. These apply to every file you open, so you only do this once.

:::task id=undo title="Raise Undo Steps to 64" xp=10
Under **System > Memory & Limits** (older versions: *Editing*), set **Undo Steps** to 64 or more. You
will make mistakes. Cheap undo is a feature.
check: prefs.undo_steps >= 64 :: Undo Steps is 64 or higher
hint: Edit > Preferences > Editing (3.3) or System > Memory and Limits (4.x and 5.x).
hint: The field is called "Steps". Type 64 and press Enter.
:::

:::task id=autosave title="Auto Save every minute" xp=10
Open **Save & Load** and set **Timer (Minutes)** under Auto Save to 1. Crashes happen most often right
after you have done something clever.
check: prefs.autosave_minutes <= 1 :: Auto Save timer is 1 minute
hint: Preferences > Save & Load > Auto Save. The timer field is in minutes.
:::

:::task id=numpad optional title="Emulate Numpad (laptops only)" xp=5
No number pad? Open **Input** and tick **Emulate Numpad**. After that the number row works as a numpad
in the 3D viewport. Skip this if you have a real one.
check: prefs.emulate_numpad :: Emulate Numpad is on
hint: Preferences > Input > Keyboard > Emulate Numpad.
:::

:::note tip title="Preferences save themselves"
Auto-Save Preferences is on by default. If you change something and it comes back after a restart, that
switch is off at the bottom left of the Preferences window.
:::

## The render settings

Now the scene itself. Open the **Properties editor** (bottom right) and click the **Render** tab, the
camera-back icon.

:::task id=engine title="Cycles on the CPU" xp=10
Set **Render Engine** to **Cycles**. In the **Device** drop-down choose **CPU**.
check: render.engine == 'CYCLES' and render.cy_device == 'CPU' :: Engine is Cycles, device is CPU
hint: Render properties tab > Render Engine at the very top. Device appears just below once you pick Cycles.
:::

:::task id=samples title="Cheap but clean: 64 samples + denoise" xp=15
Under **Sampling > Render**, set **Max Samples** to **64** and turn **Denoise** on with
**OpenImageDenoise**. The denoiser cleans up grain so you can get away with far fewer samples.
check: render.cy_samples <= 64 :: Render samples are 64 or lower
check: render.cy_use_denoising and render.cy_denoiser == 'OPENIMAGEDENOISE' :: Denoise on, OpenImageDenoise
hint: Sampling is a collapsed panel. Click it open, then open the Render sub-panel.
hint: The denoiser drop-down shows OpenImageDenoise and OptiX. OptiX needs an Nvidia card, so pick the first.
:::

:::v 3
In 3.3 the **Denoise** checkbox sits in the *Render* sub-panel next to the sample count. A **Noise
Threshold** (adaptive sampling) is on by default and stops tiles early when they are clean.
:::

:::v 4+
In 4.x and 5.x the sampling panel also shows **Noise Threshold** and **Min Samples**. Leave them. The
Noise Threshold lets Cycles stop early on areas that are already clean, which is free speed.
:::

:::task id=percent title="Draft at half size" xp=10
Open the **Output** tab (printer icon) and set **Resolution %** to **50**. Draft renders at half
resolution have a quarter of the pixels and take roughly a quarter of the time.
check: render.res_pct == 50 :: Resolution percentage is 50
hint: Output properties tab, Format panel. The percentage slider is under the X and Y values.
:::

:::quiz id=q1 xp=5
You halve the width and the height of a render (50% resolution). Roughly how long does it take now?
- Half as long
- *About a quarter as long
- The same, only smaller
explain: Pixels go with width times height. Half of each leaves a quarter of the pixels, so the render takes about a quarter of the time.
:::

:::quiz id=q2 xp=5
Which of these helps a CPU render the most?
- Turning samples up to 4096 for "better quality"
- *Fewer samples with the denoiser on
- Rendering at 400% resolution
explain: Denoising removes the grain that low sample counts leave behind. You trade a little fine detail for a huge saving.
:::

:::note cpu title="The shortcut"
The **Polycamp** sidebar tab in Blender (press N in the viewport) has a **CPU-friendly render preset**
button. It sets everything above in one click and also turns off caustics and limits bounces. Use the
manual route here once so you know what the button does.
:::

:::reveal title="What the preset changes, line by line"
- Engine Cycles, device CPU
- Max samples 24 / 64 / 128 for Draft / Standard / Final, 8 to 16 in the viewport
- Adaptive sampling on, OpenImageDenoise on
- Max bounces 6, diffuse 2, glossy 3, transmission 4, volume 0
- Caustics off, indirect clamp 10 (kills fireflies)
- Resolution 960×540 / 1280×720 / 1920×1080
- Persistent Data on, which speeds up animation renders
:::

:::solve
p = bpy.context.preferences
p.edit.undo_steps = 64
p.filepaths.auto_save_time = 1
p.inputs.use_emulate_numpad = True
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.render.resolution_percentage = 50
:::
