---
id: pbr-maps
title: Normal, Roughness and Height Maps
summary: Make a flat picture behave like a bumpy, patchy-shiny surface.
minutes: 14
scene: starter:barrel-uv
keys: Shift+A
tags: textures, materials
xp: 45
---
A colour map alone looks like a printed poster. Real surfaces have bumps that catch light and shine that varies from spot to spot.
**PBR** (physically based rendering) materials split those properties into separate maps, each a grayscale or colour image:

| Map | What it stores | Blender input | Colour space |
| --- | --- | --- | --- |
| **Base colour** (albedo) | the surface colour, without lighting | Base Color | sRGB |
| **Roughness** | how blurry reflections are, per pixel | Roughness | Non-Color |
| **Metallic** | 0 or 1: is this pixel metal? | Metallic | Non-Color |
| **Normal** | a tiny direction offset that fakes bumps | Normal, via a **Normal Map** node | Non-Color |
| **Height** | how high each pixel is | Normal, via a **Bump** node | Non-Color |
| **AO** | ambient occlusion: pre-shadowed crevices | multiplied into Base Color | Non-Color |

## Making them from one picture

The **Texture Lab** derives the extra maps from your colour image. Brightness becomes **height** (after contrast and smoothing), a Sobel filter
turns the height into a **normal map**, brightness again drives **roughness**, and blurring the height gives cheap **ambient occlusion** in the
cracks. These are approximations from a single photo, but for walls, wood and stone they are very convincing. Open the Lab and look at the
**Relief** preview: move the mouse and the light moves across the normal-mapped surface.

Sliders worth knowing:

- **height ×** makes the bumps stronger or flatter before the normal map is computed.
- **normal** is the strength of the final bump.
- **rough base / rough ×** sets average shine and its variation.
- **AO radius / power** controls how wide and how dark the crevice shading is.

Normal maps use the **OpenGL** convention here (green = up), which is what Blender and Godot both expect.

## Wiring them in Blender

The Lab's *→ Blender* button builds all of this for you. Here is what it makes, so you can read and edit it:

- Image Texture (sRGB) → **Base Color**
- Image Texture (Non-Color) → **Roughness**
- Image Texture (Non-Color) → **Normal Map** node (Tangent Space) → Normal. If there is also a height map, it goes through a **Bump** node first
  with the Normal Map into the Bump's Normal slot.

:::task id=send title="Send a full set to the barrel" xp=16
Send a texture set with **colour, normal, roughness and height** to the **barrel**. In the Lab keep all four map checkboxes ticked, then press
**→ Blender** with the barrel selected. The Principled BSDF's **Normal** socket should be fed through a **Normal Map** and a **Bump** node.
check: any(m != None and m.chain != None and m.chain.normal != None and 'NORMAL_MAP' in m.chain.normal and 'BUMP' in m.chain.normal for m in [mat(n) for o in meshes if o.name == 'Barrel' for n in o.mats]) :: The barrel's Normal goes through Bump and Normal Map nodes
check: any(m != None and m.chain != None and m.chain.roughness != None and 'TEX_IMAGE' in m.chain.roughness for m in [mat(n) for o in meshes if o.name == 'Barrel' for n in o.mats]) :: Roughness is driven by an image
hint: Texture Lab: Wood planks > Generate. Keep height, normal and rough ticked. Select the barrel in Blender, then → Blender.
hint: By hand: Shift+A > Texture > Image Texture (open the PNG), Shift+A > Vector > Normal Map, connect Image Color > Normal Map Color > Principled Normal.
:::
:::solve task=send
ob = bpy.data.objects['Barrel']
files = {k: make_test_image(bpy.app.tempdir + 'barrel_%s.png' % k, k) for k in ('base_color', 'normal', 'roughness', 'height')}
m = matkit.build_pbr('Barrel_PBR', files, tiling=(2.0, 2.0))
ob.data.materials.clear()
ob.data.materials.append(m)
:::

:::task id=nc title="Data maps are Non-Color" xp=10
At least **two images** must be set to the **Non-Color** colour space. (The Lab button does it for you; do it by hand when you load maps yourself.)
check: sum(1 for i in images if i.colorspace == 'Non-Color') >= 2 :: Two or more images use Non-Color
hint: Select the Image Texture node, and in the node's panel change Color Space from sRGB to Non-Color.
:::
:::solve task=nc
pass
:::

## Displacement: a warning

A **Height** map can also be used for real displacement, which moves actual vertices. That needs a lot of geometry and costs memory and render time.
For a CPU renderer, the **Bump** node (fake relief) is nearly always the right choice. Keep real displacement for hero close-ups.

:::note cpu title="Bump versus normal"
Both fake relief. A **normal map** captures sharper, directional detail (rivets, tile edges, stitching) and is what game engines use. A **bump** map is a simple height
map, easier to make and great for organic noise. Using both together, as the Lab does, gives broad bump with fine normal detail.
:::

:::quiz id=q1 xp=5
Which map makes the surface shine more in some places than others?
- Normal
- *Roughness
- Height
explain: Roughness controls how sharp or blurry reflections are, and it can vary across the surface: worn spots are shinier, dusty ones dull.
:::

:::match id=m1 xp=6
What does each map fake?
Normal map => Small bumps and edges that catch light
Roughness map => Patchy shine and dullness
Ambient occlusion => Darkness in cracks and corners
Height map => Surface relief (through a Bump node)
:::
