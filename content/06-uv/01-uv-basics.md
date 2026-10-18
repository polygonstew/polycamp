---
id: uv-basics
title: Unwrapping: Seams and the UV Editor
summary: Cut a crate open like a cardboard box, lay it flat, and check what you made.
minutes: 14
scene: starter:crate-nouv
keys: U, Alt+LMB
tags: uv
xp: 45
---
Think of a **cardboard box**. Slice along some of its edges and you can fold it flat into a cross. Every face keeps its shape
and every part of the surface has a spot on the flat sheet. That is a UV unwrap. The cuts you make are **seams**. The flat
sheet is the **UV map**. The names are U and V because X, Y and Z were taken.

## The steps

1. In Edit Mode choose **edges**, select the ones you want cut, then **Edge > Mark Seam** (or [[Ctrl+E]] > Mark Seam). Seams
   show up red.
2. Select all faces ([[A]]) and press [[U]] > **Unwrap**.
3. Open the **UV Editing** workspace and look at the left panel. Each connected piece of surface is an **island**.

A cube has twelve edges. To flatten it you need **seven** seams: five of the twelve edges stay joined to hold the six faces
together as a net (any tree over the faces works), and the other seven are cut.

The starter crate has no UV map at all. The checks look at its seam count, the UV map and how much of the tile the layout covers.

:::task id=seams title="Cut seven seams" xp=14
Mark **seven seams** on the crate so it can unfold: cut all **four vertical edges** and **three of the four edges around the
bottom face**. The top face stays attached to its four sides, and the bottom hangs off the fourth. That is the classic cross shape.
check: any(o.name == 'Crate' and o.seams >= 7 for o in meshes) :: The crate has seven or more seam edges
hint: Edge mode (2). Click an edge, then Shift+click the others. Edge menu > Mark Seam. They turn red.
hint: Alt+click an edge selects a whole loop. The four vertical edges are not a loop, so click them one by one.
:::
:::solve task=seams
ob = bpy.data.objects['Crate']
bm = bmesh.new()
bm.from_mesh(ob.data)
mark_seam_net(bm)
bm.to_mesh(ob.data)
bm.free()
:::

:::task id=unwrap title="Unwrap it" xp=16
Select every face and press [[U]] > **Unwrap**. The crate now has a UV map. The islands should lie inside the 0 to 1 square (nothing outside)
and cover at least 30% of it.
check: any(o.name == 'Crate' and len(o.uv) >= 1 and o.uv_oob == 0 and o.uv_area >= 0.3 for o in meshes) :: The crate has a UV map inside the tile covering 30%+
hint: Edit Mode, A to select all, U > Unwrap. If the islands look tiny, scale them up in the UV Editor (A, then S).
hint: Anything outside the 0 to 1 box wraps around when tiled, which usually you do not want for a unique map.
:::
:::solve task=unwrap
ob = bpy.data.objects['Crate']
bm = bmesh.new()
bm.from_mesh(ob.data)
kit.uv_cross_cube(bm)
bm.to_mesh(ob.data)
bm.free()
:::

## Check your work: the checker

An unwrapped model can still stretch the texture like gum. The fix is a **UV checker**: a picture of squares and letters. In Blender:
**Image Editor** (or the UV Editor) > **New Image** > *UV Grid* or *Color Grid*, then plug it into a material's Base Color. Squares
should look square and the same size across the whole object. Where squares stretch to rectangles the unwrap is distorted. Where they
are bigger or smaller than their neighbours the **texel density** is uneven.

:::note tip title="The app can look too"
Use the **UV Lab** in this app: press **Get UV layout**. It shows the layout of the active object, coloured teal where
islands cover the tile and **red where islands overlap**. Overlap is only OK on purpose (mirrored halves, repeated bricks).
:::

## Which unwrap?

- **Unwrap** (needs seams): the careful one, best for characters, props, hard-surface.
- **Smart UV Project**: automatic, cuts on angles, many small islands. Quick and dirty, fine for game assets.
- **Cube / Cylinder / Sphere Projection**: wraps from the outside. Good for simple shapes.
- **Project from View**: flattens what the camera sees. Used for decals and painting.

:::quiz id=q1 xp=5
Why are seams necessary to unwrap a 3D shape?
- Because Blender cannot flatten triangles
- *A closed surface cannot lie flat without being cut, like peeling a box open
- Seams make the texture brighter
explain: Flat paper cannot cover a closed 3D shape without cutting it. Seams are where you choose to cut so the flattening has the least distortion.
:::

:::match id=m1 xp=6
Match the term.
Seam => A cut line that lets the mesh unfold
Island => A connected piece of the unwrapped mesh
UV map => Flat 2D coordinates for each point on the surface
Texel density => How many texture pixels cover each metre of surface
:::
