---
id: topology
title: Topology: The Rules Nobody Tells You
summary: Quads, triangles, ngons and poles, and why they matter the moment you animate or smooth.
minutes: 14
scene: starter:tri-soup
keys: Alt+J, Ctrl+2, Alt+Z
tags: topology, theory
xp: 45
---
**Topology** is how your faces are arranged: how many sides they have and how the edges flow around the
shape. Two meshes can look identical in a still and behave completely differently when you smooth them,
bend them or hang a texture on them.

## Face types

- **Quad** (4 sides). The default. Loop cuts work through quads, they subdivide cleanly, they deform
  well, and UVs behave.
- **Triangle** (3). Fine on flat things and in game meshes, the engine converts everything to triangles
  anyway. Troublesome on anything you plan to smooth or animate.
- **Ngon** (5+ sides). Handy for flat caps and while blocking things out. Ngons shade oddly when curved
  and they block loop cuts.

:::note tip title="The working rule"
Model in **quads**. Allow triangles and ngons only on flat areas where nobody will deform or smooth the
surface. Everything else is a taste argument you can have after you ship.
:::

## Poles

A **pole** is a vertex with an unusual number of edges: three or five or more, instead of the usual four.
Poles are not evil. You cannot avoid them on organic shapes. But a pole in the middle of a flat area
that will be smoothed causes pinching, and a pole on a bending elbow makes the skin crinkle.

:::quiz id=q1 xp=5
You are modelling a cube that will be smoothed with Subdivision Surface. Which face type is the one to avoid?
- Quads
- *Ngons and awkward triangles
- All faces are equal for this
explain: Subdivision Surface is designed for quads. Triangles and ngons are turned into odd bits of geometry that show up as pinches and dents in the shading.
:::

## Your panel

The starter scene is a flat panel made entirely from triangles. It looks fine until you try to loop cut,
or until you subdivide it. Fix it.

Select everything, then use **Mesh > Faces > Tris to Quads** ([[Alt+J]]). Blender pairs up triangles that
form a nice quad. For a clean grid it finds all of them.

:::task id=quads title="Turn the triangles back into quads" xp=18
Select all the faces and join them into quads. When you are done the statistics should show **zero**
triangles and zero ngons: only quads remain.
check: any(o.n3 == 0 and o.ngons == 0 and o.quads >= 30 for o in meshes) :: Only quads remain (30 or more)
hint: Tab into Edit Mode, press A to select everything, then Alt+J (or Face menu > Tris to Quads).
hint: Turn on Statistics in the overlays first. You can watch the triangle count drop to zero.
:::
:::solve task=quads
me = bpy.context.object.data
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.join_triangles(bm, faces=bm.faces[:], angle_face_threshold=math.radians(10), angle_shape_threshold=math.radians(180))
bm.to_mesh(me)
bm.free()
:::

## Why smoothing cares

Now add a **Subdivision Surface** modifier with [[Ctrl+2]] while in Object Mode. On a clean quad grid
the smoothed result is smooth and the panel stays flat. On triangles you would see faint creases fanning
out. The cheapest test of a mesh is to smooth it and look.

:::task id=sub title="Smooth it: add Subdivision Surface" xp=10
In Object Mode press [[Ctrl+2]] to add a Subdivision Surface modifier at level 2.
check: any(m.type == 'SUBSURF' for o in meshes for m in o.mods) :: A Subdivision Surface modifier is on the panel
hint: Hover the viewport in Object Mode (Tab out of Edit Mode first) and press Ctrl+2. Or Properties > Modifiers > Add Modifier > Generate > Subdivision Surface.
:::
:::solve task=sub
ob = bpy.data.objects['Panel']
m = ob.modifiers.new('Subdivision', 'SUBSURF')
m.levels = 2
:::

:::note cpu title="Viewport vs render levels"
A Subdivision Surface modifier has two numbers: **Levels Viewport** and **Render**. Keep the viewport
at 1 or 2 and bump only the render level. Each level multiplies the face count by about four, which is a
quick way to freeze Blender on a CPU machine.
:::

## Matching things up

:::match id=m1 xp=6
Match the term to the description.
Pole => A vertex with 3, 5 or more edges instead of 4
Ngon => A face with five or more sides
Edge loop => A ring of edges that continues straight through a quad grid
Manifold => A mesh where every edge belongs to exactly two faces
:::

:::order id=o1 xp=6
Put these in order, from most to least friendly for smooth organic modelling.
1. Clean quads with evenly flowing loops
2. Quads with a few poles in sensible places
3. A mix of quads and triangles on curved areas
4. Large ngons on a curved surface
:::

:::cubby smug
The people who say "topology doesn't matter" have not yet tried to rig a character with 40,000 random
triangles. Let them learn. We will be elsewhere, with quads.
:::
