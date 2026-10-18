---
id: world-sky
title: The World: Sky and Ambient Light
summary: Everything the camera sees beyond your objects is a material too.
minutes: 10
scene: starter:dusk-grey
keys: Z
tags: world, lighting
xp: 35
---
The **World** is the infinite sphere around your scene. It does two jobs at once: it is the **backdrop** the camera sees, and it is
the **ambient light** that shines on everything. In the Properties editor the world tab is the red-and-blue globe icon.

A world is a shader like any other, with a **Background** node as its output. The Background has a **Color** and a **Strength**.
A flat grey is a perfectly legal sky. It is also why the starter scene looks like a dull office.

## Three ways to make a sky

1. **A plain colour** with a strength around 0.5. Cheap and moody. Good for night.
2. **A Sky Texture**: a physically based sun and atmosphere.
3. **An HDRI**: a photo of a real sky, loaded through an **Environment Texture** node. Light and background in one.

:::v 3
Blender 3.3 offers the **Sky Texture** types **Nishita** (the best, realistic), **Preetham** and **Hosek-Wilkie**. Pick Nishita and
lower **Sun Elevation** to around 3° for sunset.
:::

:::v 4+
Blender 4.x still has Nishita; Blender 5 renamed the types to **Single Scattering** and **Multiple Scattering**. They work the
same way: sun elevation and rotation, air, dust and ozone.
:::

## Dusk without any images

Our diorama uses something cheaper and fully controllable: a **gradient** made from the direction of the view. A Texture
Coordinate (Generated) gives each direction a vector. Its Z part is 0 at the horizon and 1 straight up. A **Map Range** squeezes
that into 0 to 1, and a **Color Ramp** paints orange at the horizon fading through purple to deep blue overhead.

Open **Shading** workspace, set the editor to **World** (the drop-down that says Object), and build:

*Texture Coordinate > Separate XYZ (Z) > Map Range > Color Ramp > Background Color*

:::task id=sky title="Give the world a sky" xp=14
Make the **World's Background Color** come from a node: a gradient (Color Ramp), a Sky Texture, or an Environment Texture.
It should no longer be a flat colour.
check: world != None and world.bg_linked and (any(t in world.types for t in ('TEX_SKY', 'TEX_ENVIRONMENT', 'VALTORGB', 'TEX_GRADIENT'))) :: The World background is driven by a sky, gradient or HDRI
hint: World tab > Surface > Color: click the little dot to its left and choose Sky Texture, or build the gradient above in the shader editor.
hint: In the Sky Texture, pull the Sun Elevation down to a few degrees for a sunset look.
:::
:::solve task=sky
build_world_dusk()
:::

## Strength is your exposure knob

World Strength scales all the ambient light and the backdrop. At 1 it is a normal daylight sky. A dusk wants it dimmer, 0.3 to 0.8,
so the lantern and windows become the brightest things in the picture. A well-exposed dusk is mostly about the ratio between the
sky and your artificial lights.

:::task id=dim title="Dim it for dusk" xp=10
Set the world **Strength** between **0.3 and 0.9**.
check: world != None and world.strength != None and 0.3 <= world.strength <= 0.9 :: World strength is between 0.3 and 0.9
hint: In the Background node, change Strength. Lower values make the whole scene darker, so lamps stand out.
:::
:::solve task=dim
for n in bpy.context.scene.world.node_tree.nodes:
    if n.type == 'BACKGROUND':
        n.inputs['Strength'].default_value = 0.7
:::

:::note tip title="Film: Transparent"
For a **product render with no background**, turn on **Render Properties > Film > Transparent** and save as PNG with alpha. The
world still lights the object but the camera sees nothing behind it.
:::

:::quiz id=q1 xp=5
Why does the default grey world make a scene look flat?
- It is not bright enough to render
- *It lights everything evenly from all directions, so there are no strong shadows or colour contrast
- Grey cannot be used as a world colour
explain: Uniform ambient light removes shape-defining shadow. A directional sun, a coloured sky and a warm lamp bring the depth back.
:::
