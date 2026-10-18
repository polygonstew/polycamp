---
id: loops-bevel
title: Loop Cuts and Bevels
summary: Add resolution where you need it and soften the edges that need softening.
minutes: 12
scene: fresh
keys: Ctrl+R, Ctrl+B, G G, Alt+LMB
tags: edit mode, modeling
xp: 40
---
Real objects do not have razor-sharp corners. Every manufactured edge catches light because it has a
tiny rounded bevel, and the look of "this is real" comes from those glints. Loop cuts and bevels are how
you put them there.

## Loop cut

[[Ctrl+R]] shows a pink preview line wrapping around the mesh at the mouse position. Before you click:

- **Scroll the wheel** up for more parallel cuts. You will see the number in the header.
- **Click once** to place the loop, **move the mouse** to slide it, then **click again** to confirm.
- **Right-click** (or Esc) after the first click to confirm it *centred* without sliding. People forget
  this one and live with a wonky cut for years.
- Afterwards the **Adjust Last Operation** panel (bottom-left) lets you change the number of cuts, the
  slide factor, even the falloff.

A loop cut works around any ring of connected quads. It stops dead at triangles and ngons. That is the
first hint that topology matters, and the next lesson is all about it.

:::task id=cuts title="Two loop cuts around the cube" xp=12
Add **two** horizontal loop cuts to the cube so its sides are split into three bands. The cube should
end up with 16 vertices and 14 faces.
check: any(o.verts == 16 and o.faces == 14 for o in meshes) :: A mesh with 16 vertices and 14 faces
hint: Hover a side face and press Ctrl+R. The pink preview line should run horizontally around the cube. Scroll up once for two cuts, click, then right-click.
hint: If the preview runs vertically, move the mouse over a different face. The cut goes across whichever edge direction the pointer is nearest to.
:::
:::solve task=cuts
me = bpy.context.object.data
bm = bmesh.new()
bm.from_mesh(me)
for z in (-0.3333, 0.3333):
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
bm.to_mesh(me)
bm.free()
:::

:::note tip title="Slide the loop afterwards"
Already cut but wrong spot? Select the loop and press [[G]] twice ([[G]] [[G]]) to slide along the
surface. That is **Edge Slide**, and it keeps the shape intact while you move the line.
:::

## Bevel

Select edges and press [[Ctrl+B]]. Move the mouse to set the **width**, **scroll** for more
**segments** (a segment count of 1 is a flat chamfer, 3 or more starts to look round) and click. Select
vertices instead and use [[Ctrl+Shift+B]] to bevel corners.

Bevelling *everything* is the fastest way to a believable box: **A**, **Ctrl+B**, a small width, three
segments.

:::task id=bevel title="Bevel all the edges, 3 segments" xp=14
Select everything and bevel all edges by 0.1 with **3 segments**. The result is a rounded block, so the
face count jumps well past 100.
check: any(o.faces >= 100 and o.verts >= 100 for o in meshes) :: A rounded mesh with 100+ faces and 100+ vertices
hint: In Edit Mode press A, then Ctrl+B, type 0.1 and press Enter. Scroll the wheel before the click to change the segment count.
hint: The segment count can also be changed in the Adjust Last Operation panel afterwards.
:::
:::solve task=bevel
me = bpy.context.object.data
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.1, segments=3, affect='EDGES', profile=0.5)
bm.to_mesh(me)
bm.free()
:::

:::note cpu title="Geometry costs real time"
Each bevel segment multiplies faces. Three segments on every edge of a detailed model can make it ten
times heavier. Bevel the edges people will *see* up close, and let the **Bevel modifier** (a later
lesson) handle the rest, since that one is adjustable and non-destructive.
:::

## Why loops matter later

When you smooth a mesh with a Subdivision Surface modifier, flat areas stay flat only if there are
**support loops** close to the edges. Two parallel loops near a corner hold it tight. That is the whole
trick behind "crisp but soft" models: put loops where you want sharpness.

:::quiz id=q1 xp=5
You press Ctrl+R, scroll once to get two cuts, click, and want them perfectly centred. What do you do?
- Click again anywhere
- *Right-click (or Esc) after the first click
- Press Enter twice
explain: The first click places the cut, the mouse then slides it. A right-click confirms without sliding, so the cuts stay evenly spaced.
:::

:::keys id=k1 xp=8
Loop cut | Ctrl+R
Bevel | Ctrl+B
Edge slide | G G
Select all | A
:::
