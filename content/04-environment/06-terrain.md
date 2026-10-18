---
id: terrain
title: Ground That Has Some Character
summary: A grid, a displace modifier and smooth shading make a believable bit of land.
minutes: 10
scene: empty
keys: Shift+A, Ctrl+2
tags: organic, modifiers
xp: 35
---
A perfectly flat ground plane is the biggest "this is fake" tell in a lot of beginner scenes. Even a few
centimetres of undulation catches the light and gives the eye something to hold on to.

## Grid plus noise

1. **Grid** (Shift+A > Mesh > Grid) with 48 × 48 subdivisions and size 9 m. More vertices than a plane so the
   displacement has something to move.
2. **Displace** modifier, new **Clouds** texture (Size about 1.2), **Strength 0.25 or less**. Small is good:
   rolling, not mountains.
3. **Shade Smooth**.
4. For a diorama, a slab underneath: a thick cylinder with the same radius so the land looks like a cut-out
   piece of earth.

:::task id=grid title="A well-subdivided ground" xp=10
Add a **Grid** named **Terrain**, 9 m across, with at least **1,500 vertices**.
check: any(o.name == 'Terrain' and o.verts >= 1500 and o.dims[0] >= 8 for o in meshes) :: Terrain is 8 m+ wide with 1,500+ vertices
hint: Shift+A > Mesh > Grid. In Adjust Last Operation set X and Y Subdivisions to 48 and Size to 9.
:::
:::solve task=grid
bm = bmesh.new()
kit.add_grid(bm, 9.0, 48)
kit.mesh_object('Terrain', bm)
:::

:::task id=rolling title="Rolling hills, not mountains" xp=14
Add a **Displace** modifier with a **Clouds** texture. Keep **Strength between 0.05 and 0.4** so the land rolls
gently.
check: any(o.name == 'Terrain' and any(m.type == 'DISPLACE' and m.p.texture and 0.05 <= m.p.strength <= 0.4 for m in o.mods) for o in meshes) :: Displace with a texture, strength 0.05 to 0.4
hint: Add Modifier > Deform > Displace. Texture: New, then change its Type to Clouds in the Texture tab.
hint: Strength is the height in metres. Anything above 0.4 on a 9 m ground starts to look like a volcano.
:::
:::solve task=rolling
ob = bpy.data.objects['Terrain']
tex = bpy.data.textures.new('GroundClouds', 'CLOUDS')
tex.noise_scale = 1.2
m = ob.modifiers.new('Displace', 'DISPLACE')
m.texture, m.strength = tex, 0.25
:::

:::task id=smooth title="Shade smooth" xp=8
Shade the terrain smooth so the grid cells do not show as facets.
check: any(o.name == 'Terrain' and o.smooth_faces == o.faces and o.faces > 100 for o in meshes) :: Terrain is smooth-shaded
hint: Object menu > Shade Smooth (Object Mode, terrain selected).
:::
:::solve task=smooth
for p in bpy.data.objects['Terrain'].data.polygons:
    p.use_smooth = True
:::

:::note cpu title="Subdivisions on a CPU"
A 48 × 48 grid is about 2,300 vertices. Doubling both dimensions quadruples that. For scene-sized ground,
under 10,000 faces is plenty, and fine detail should come from textures and bump maps, which are far cheaper than
geometry.
:::

:::cubby wink
My cousin the Plane just discovered Displace and made a mountain. He is now insufferable. Please keep the
strength small and spare us all.
:::

:::quiz id=q1 xp=5
Why does the Displace modifier need a grid with plenty of vertices?
- Displace only works on grids
- *It moves vertices, so a coarse mesh gives coarse bumps
- More vertices make the render brighter
explain: Each vertex is pushed by the texture value at its position. With few vertices you can only make a few big blocky bumps.
:::
