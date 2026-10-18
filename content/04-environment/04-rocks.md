---
id: rocks
title: Rocks Without Sculpting
summary: Irregular, convincing stones from an icosphere, a noise texture and a decimate.
minutes: 12
scene: empty
keys: Ctrl+A, Shift+A
tags: organic, modifiers
xp: 40
---
Rocks are a great test of whether you can make something look un-made. Straight edges and even spacing say
*computer*. Good rocks are lumpy, flat-bottomed and slightly chipped. You can get there with three
non-destructive steps and a little taste, no sculpting required.

## Recipe

1. **Icosphere**, subdivisions 4 (642 vertices). It has evenly sized triangles, so noise displaces it evenly.
2. A **Displace** modifier with a **Clouds** texture. Strength about 0.3. The clouds texture is a smooth
   lumpy noise, and the modifier pushes vertices in and out along their normals by that amount.
3. A **Decimate** modifier (Collapse, ratio about 0.4). It merges triangles and makes the surface faceted
   and chipped, like broken stone, and cuts the face count for free.
4. Flatten the base: select the bottom vertices and scale them to Z = 0 (S Z 0), or just bury the rock a bit in the
   ground.

Where does the Clouds texture come from? Open the Displace modifier, click **New** next to Texture, and
change its **Type** to *Clouds* in the Texture tab (the checkerboard icon at the bottom of the properties
tabs). Raise **Size** to about 0.6 for big lumps.

:::task id=ico title="An icosphere to start" xp=8
Add an **Icosphere** with 4 subdivisions and call it **Rock**. It should have 642 vertices.
check: any(o.name == 'Rock' and o.verts >= 300 for o in meshes) :: A mesh called Rock with 300+ vertices
hint: Shift+A > Mesh > Ico Sphere. Open Adjust Last Operation and set Subdivisions to 4. (The default of 2 is only 42 vertices, far too coarse to displace.)
:::
:::solve task=ico
bm = bmesh.new()
kit.add_icosphere(bm, 1.0, 4)
kit.mesh_object('Rock', bm, loc=(0, 0, 0.7))
:::

:::task id=displace title="Displace it with clouds" xp=14
Add a **Displace** modifier with a new **Clouds** texture and **Strength 0.3 or more**. The sphere turns lumpy.
check: any(o.name == 'Rock' and any(m.type == 'DISPLACE' and m.p.strength >= 0.25 and m.p.texture for m in o.mods) for o in meshes) :: Rock has a Displace modifier with a texture, strength 0.25+
hint: Add Modifier > Deform > Displace. Click New under Texture, then open the texture tab and set Type: Clouds.
hint: Strength is in the modifier panel. 0.3 gives a good lumpiness on a 1 m rock.
:::
:::solve task=displace
rock = bpy.data.objects['Rock']
tex = bpy.data.textures.new('RockClouds', 'CLOUDS')
tex.noise_scale = 0.6
m = rock.modifiers.new('Displace', 'DISPLACE')
m.texture = tex
m.strength = 0.3
:::

:::task id=decimate title="Chip it with Decimate" xp=10
Add a **Decimate** modifier (Collapse) below the Displace, with a **Ratio of 0.5 or less**.
check: any(o.name == 'Rock' and any(m.type == 'DECIMATE' and m.p.ratio <= 0.55 for m in o.mods) for o in meshes) :: Rock has a Decimate with ratio 0.55 or lower
hint: Add Modifier > Generate > Decimate. The Ratio slider is the main control. Keep Collapse as the type.
:::
:::solve task=decimate
rock = bpy.data.objects['Rock']
m = rock.modifiers.new('Decimate', 'DECIMATE')
m.ratio = 0.4
:::

## Make three

One rock repeated looks like a stamp. Duplicate it ([[Shift+D]], then S to scale, R to turn it) and change the
seed of the texture by moving the **Offset** in the texture panel or by rotating the rock so the noise lands
differently. Three sizes, three angles.

:::note tip title="Sculpt Mode, when you want it"
Blender's **Sculpt Mode** (the Sculpting workspace) lets you push and carve with brushes, like clay. It is the
right tool for faces, creatures and hero rocks. On a CPU-only machine keep the mesh under about 100,000 faces,
use **Remesh** (voxel) to even things out, and avoid **Dyntopo** at high detail.
:::

:::quiz id=q1 xp=5
Which modifier gives the rock its faceted, chipped look while also reducing the face count?
- Subdivision Surface
- *Decimate (Collapse)
- Mirror
explain: Decimate merges triangles and removes detail. Combined with Displace it leaves a chunky, broken-stone surface.
:::
