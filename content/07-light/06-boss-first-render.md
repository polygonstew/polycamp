---
id: boss-first-render
title: Boss: The First Dusk Render
summary: Light it, frame it, set it up for your CPU, press F12 and show it off.
minutes: 40
scene: starter:bare-render
boss: true
keys: F12, Numpad 0, Shift+A
tags: boss, render
xp: 160
---
:::cubby shock
You have everything now: a built, dressed diorama and a head full of lighting. It is sitting under a flat grey world with no lights and no camera. Make it look like the end of a good day.
:::

## Brief

Produce one finished render of the diorama at dusk.

1. **Sky:** a gradient or sky texture, strength under 1, so the sky is the dimmest source in the picture.
2. **Lights:** at least three, with a **warm** one (the setting sun) and a **cool** one (sky fill). Put a small warm **point light** near the lantern by the door.
3. **Camera:** 30 to 60 mm, depth of field on, framed on the cabin.
4. **Render settings:** Cycles on CPU, 128 samples or fewer, denoise on, between 960 and 1920 pixels wide.
5. **Compositor:** a Glare node so the windows and lantern bloom.
6. **Render it** with [[F12]]. The finished image appears in the app's **Trophy Room**.

A hint on mood: dusk is about contrast. The brighter your lamp and windows are compared with the sky, the warmer the cabin feels.

:::goal img=diorama-final.png
A reference render from the course library (Cycles, CPU, 800 px wide). Yours will differ, and that is the point.
:::

:::task id=sky title="A dusk sky" xp=20
The **World** background is driven by a sky or gradient, with a strength under 1.
check: world != None and world.bg_linked and world.strength != None and world.strength < 1.0 :: A node-driven sky with strength below 1
hint: World tab > Color > Sky Texture, or build the gradient from the World lesson. Strength 0.7 is a good start.
:::
:::solve task=sky
build_world_dusk(0.8)
:::

:::task id=lights title="Warm sun, cool fill, lantern glow" xp=25
At least three lights, with one clearly warm (red above blue), one clearly cool (blue above red) and a **Point** light in front of the cabin (Y below −1).
check: len(lights) >= 3 :: Three or more lights
check: any(o.light.color[0] > o.light.color[2] + 0.2 for o in lights) and any(o.light.color[2] > o.light.color[0] + 0.1 for o in lights) :: One warm and one cool light
check: any(o.light.kind == 'POINT' and o.loc[1] < -1 for o in lights) :: A point light in front of the cabin
hint: The library scene put its lights on a collection called Lights. You can duplicate and recolour them.
:::
:::solve task=lights
build_lights()
:::

:::task id=cam title="Camera with depth of field" xp=20
A scene camera with a lens of 30 to 60 mm and depth of field enabled.
check: scene.camera != None and any(o.type == 'CAMERA' and 30 <= o.camera.lens <= 60 and o.camera.dof for o in cams) :: A 30 to 60 mm scene camera with depth of field
hint: Look through it with Numpad 0. Camera data tab > Depth of Field.
:::
:::solve task=cam
build_camera()
:::

:::task id=settings title="Render set up for the CPU" xp=25
Cycles, CPU, **128 samples or fewer**, denoise on, output **960 to 1920 pixels wide**.
check: render.engine == 'CYCLES' and render.cy_device == 'CPU' and render.cy_samples <= 128 :: Cycles on CPU with 128 samples or fewer
check: render.cy_use_denoising and 960 <= render.res_x <= 1920 :: Denoise on, 960 to 1920 px wide
hint: The Polycamp sidebar in Blender has a one-click CPU preset (Standard is 1280 × 720, 64 samples). Or set it by hand like in World 1.
:::
:::solve task=settings
matkit.cpu_preset(bpy.context.scene, 'draft')
:::

:::task id=glare title="Make the lamps bloom" xp=20
A **Glare** node is in the compositor.
check: 'GLARE' in scene.comp_nodes :: The compositor has a Glare node
hint: Compositing workspace > Use Nodes > Shift+A > Filter > Glare.
:::
:::solve task=glare
add_glare(1.0)
:::

:::task id=render title="Render it" xp=50 untested
Press [[F12]]. When it finishes it is uploaded to the **Trophy Room** automatically. Wait for it, you earned the pause.
check: rendered and render_last.engine == 'CYCLES' :: A Cycles render finished after you started this boss
hint: F12 renders. A draft (50% resolution) is fine while you tune things, but do the full-size one for this task.
hint: The render window shows a progress bar. On a CPU a 1280 × 720 render takes a couple of minutes. Do not touch the scene while it runs.
:::

:::note tip title="After the render"
The Render window has **Image > Save As** ([[Shift+Alt+S]]). Save a PNG. In the Trophy Room you can star your favourites. Compare a Draft and a Final side by side and notice what the extra
samples bought you.
:::
