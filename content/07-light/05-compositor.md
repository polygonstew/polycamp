---
id: compositor
title: The Compositor: Glow and Colour After the Render
summary: Add the bloom around the lantern and warm the grade without re-rendering.
minutes: 12
scene: starter:full-diorama
keys: Shift+A
tags: render, post
xp: 40
---
A renderer produces light. A **compositor** adjusts the image *after* it is rendered, the way a photo editor does, but with nodes and without touching pixels by hand. It is also the
cheapest place to fix things: re-rendering costs minutes, a compositor tweak costs a second.

Open the **Compositing** workspace and tick **Use Nodes** on the top bar of the node editor (Blender 5 always has nodes). You see a **Render Layers** node (the raw render) connected to a
**Composite** node (the output). Everything you add goes between them.

## Glare: the glow

Light blooms in real lenses: a bright lamp bleeds a soft halo into its surroundings. Cycles does not produce this on its own. The **Glare** node does.

- **Fog Glow** (or **Bloom** in newer versions) gives the soft halo. This is the one for the lantern and windows.
- **Streaks** gives star points. Use sparingly.
- **Threshold** says how bright something must be to glow. Around 1 to 3 catches only the lights.
- **Size** is the halo's reach.

Insert it with [[Shift+A]] > Filter > Glare, then drag it onto the wire between Render Layers and Composite.

:::task id=glare title="Glow around the lights" xp=16
Enable the compositor and add a **Glare** node (Fog Glow or Bloom) between **Render Layers** and **Composite**.
check: 'GLARE' in scene.comp_nodes :: The compositor has a Glare node
hint: Compositing workspace, Use Nodes. Shift+A > Filter > Glare, drop it on the connecting wire.
hint: Blender 5 has a different compositor setup but the Add menu is the same: Filter > Glare.
:::
:::solve task=glare
add_glare(1.0)
:::

## Colour grading

A **Color Balance** node tints shadows, midtones and highlights separately. Lift the shadows toward blue and push the highlights toward orange and you have the "teal and orange" look of half
of Hollywood, and exactly the colours of our dusk. The **Exposure** node adjusts overall brightness, and **Hue Correct** nudges individual colours.

:::task id=grade title="Add a Color Balance" xp=12
Add a **Color Balance** node (Shift+A > Color > Color Balance) and push the shadows a little blue, highlights a little orange.
check: 'COLORBALANCE' in scene.comp_nodes :: The compositor has a Color Balance node
hint: Use the Lift (shadows) and Gain (highlights) colour wheels. Small changes: a hint of colour is enough.
:::
:::solve task=grade
nt = comp_tree()
nt.nodes.new('CompositorNodeColorBalance')
:::

## More ideas, same graph

- **Vignette**: an *Ellipse Mask* through a *Blur* node drives a *Mix* (Multiply) so the corners go slightly darker. It pulls the eye to the middle.
- **Lens distortion / chromatic aberration**: a hint of colour fringing at the edges. A tiny amount sells "photograph".
- **Denoise node**: a standalone denoiser if you skipped the render one.
- **Film grain**: a touch of noise over the top makes a CG image feel photographic.

:::note cpu title="Cheap and reversible"
Compositing runs after the render and costs almost nothing. To tweak it without re-rendering, render once, press **F11** to show the Render Result, or load the saved PNG with an **Image** node, and fiddle
with the nodes as long as you like.
:::

:::note warn title="EEVEE bloom"
Older EEVEE had a Bloom switch in the render settings. Blender 4.2 removed it. If you use EEVEE today, the Glare node in the compositor is the way to glow.
:::

:::quiz id=q1 xp=5
Why do the glow in the compositor and not in the 3D scene?
- Because 3D lights cannot glow
- *It is faster to adjust and you do not have to re-render the scene to change it
- Because the compositor is more accurate
explain: A compositor tweak works on a finished image, so you can iterate on the look in seconds instead of re-rendering for minutes.
:::
