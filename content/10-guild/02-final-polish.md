---
id: final-polish
title: The Last Ten Percent
summary: Exposure, framing, a proper render preset and a checklist before you press the big button.
minutes: 30
scene: starter:full-diorama
keys: F12, Numpad 0, Ctrl+B
tags: final, render
xp: 90
---
Polish is where a good render turns into a pleasing one. None of it is complicated. You just have to do it deliberately instead of hoping.

## Exposure and the look

Render once at draft size ([[F12]]). Is the cabin glowing, the sky moody, the lantern the brightest point? If the whole picture is too bright or too dark, do not move every light: change **Exposure** in **Render properties > Color Management**
(a stop or two either way) or pick a **Look** for more contrast. A slightly *under*exposed dusk with glowing windows reads as dusk. An evenly lit one reads as day with a filter.

:::task id=exposure title="Set the mood: exposure or look" xp=15
Change **Exposure** from 0 or choose a **Look** other than None, so the frame is deliberately exposed.
check: render.exposure != 0 or (render.look != None and render.look != 'None') :: Exposure is changed or a Look is chosen
hint: Render properties > Color Management > Exposure. Try −0.5 for a deeper dusk. In 4.x the Look drop-down offers contrast options.
:::
:::solve task=exposure
bpy.context.scene.view_settings.exposure = -0.4
:::

## Framing, DOF and glow

- The cabin should sit on a **third**, not dead centre. The lantern lights the foreground.
- The round base fits with margin. Nothing is cut off by the frame.
- Focus on the cabin's front. The background pines are softly blurred.

:::task id=glare title="Let the lamps glow" xp=10
Add a **Glare** node in the compositor so the windows and lantern bloom (skip if you already did this in World 7).
check: 'GLARE' in scene.comp_nodes :: The compositor has a Glare node
hint: Compositing workspace > Use Nodes > Shift+A > Filter > Glare, between Render Layers and Composite.
:::
:::solve task=glare
add_glare(1.0)
:::

## The final render settings

The reference scene starts on the *Draft* preset (960 × 540, 24 samples). For the finished still use a **Final** setup: Cycles on the CPU, **1280 or 1920 wide**, **64 to 128 samples**, denoiser on. Plan the time: 1280 × 720 at 64 samples is minutes, 1920 × 1080 at 128 is a long coffee.

:::task id=settings title="Final render settings" xp=20
Cycles on the CPU, at least **1280 px wide**, **between 48 and 128 samples**, denoise on.
check: render.engine == 'CYCLES' and render.cy_device == 'CPU' :: Cycles on the CPU
check: render.res_x >= 1280 and 48 <= render.cy_samples <= 128 :: At least 1280 wide with 48 to 128 samples
check: render.cy_use_denoising :: Denoising is on
hint: Use the Polycamp sidebar's CPU-friendly preset set to Standard or Final, then adjust.
:::
:::solve task=settings
matkit.cpu_preset(bpy.context.scene, 'standard')
:::

## Preflight checklist

Go through it out loud. Every one of these has ruined a night's render.

- [ ] The correct **camera** is active.
- [ ] **Output path** is somewhere you can find. File format PNG for stills.
- [ ] **Resolution %** is 100, not left at 50 from the draft.
- [ ] **Render region** (Ctrl+B) is cleared (Ctrl+Alt+B), or you will render a rectangle.
- [ ] **Hidden objects** you wanted are visible in the render (the camera icon).
- [ ] The cutter objects from Boolean modifiers are hidden from render.
- [ ] **Denoise** is on, **samples** are sane.
- [ ] The laptop is plugged in and will not go to sleep.

:::task id=check title="Walk the checklist" xp=10 manual
Go through the checklist above once. Claim it when you have.
hint: The most common slip is Resolution % left at 50, or a leftover render region from a test.
:::

:::note cpu title="A final trick: render small, upscale"
If a full-size render is out of reach, render at **1280 × 720** and let the image viewer or a video editor upscale to 1080p. At normal viewing distance, a clean denoised 720p looks better than a noisy 1080p.
:::

:::quiz id=q1 xp=5
Your dusk render looks washed out and too bright overall. What is the cleanest single fix?
- Delete the sun
- *Lower the Exposure in Color Management by a stop or so
- Add more samples
explain: Exposure scales the whole image's brightness without redoing your lighting. More samples only removes noise.
:::
