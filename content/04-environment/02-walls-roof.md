---
id: walls-roof
title: A Real Roof and Real Openings
summary: Turn the box into a gabled cabin with a door and a window cut into it.
minutes: 14
scene: starter:cabin-blockout
keys: Ctrl+R, G Z, S
tags: modeling, architecture
xp: 45
---
The starter has the walls, a flat roof slab and the ground. Now it needs to look like a cabin.

## A gable roof from a box

A gabled roof has two sloping sides meeting in a **ridge**. You do not need a special tool: it is a box with a
loop cut, and one edge loop lifted.

1. Select the roof, go into Edit Mode.
2. [[Ctrl+R]] across the **short** direction so the loop runs along the length of the roof, right through the
   middle. Right-click to centre it.
3. In edge mode, select that middle loop on the **top** surface only.
4. Move it up: [[G]] [[Z]] `0.7`. The flat slab is now a peaked roof.

Check from the front in ortho view ([[Numpad 1]]): you should see a triangle-ish silhouette, not a flat line.

:::task id=gable title="Raise the ridge" xp=14
Cut a loop through the middle of **Roof**, then lift the top middle edge loop by about 0.7 m so the roof is a
gable. Its height should now be at least 1.1 m.
check: any(o.name == 'Roof' and o.dims[2] >= 1.1 and o.verts >= 12 for o in meshes) :: Roof is 1.1 m or more tall with 12+ vertices
hint: Edit Mode, Ctrl+R along the long axis, right-click to centre. Edge mode (2), Alt+click the top-middle edge to pick the loop, then G Z 0.7.
hint: If you lift the whole loop including the bottom, the roof just gets taller. You want only the edges on the upper surface.
:::
:::solve task=gable
roof = bpy.data.objects['Roof']
me = roof.data
bm = bmesh.new()
bm.from_mesh(me)
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 1, 0))
top = max(v.co.z for v in bm.verts)
for v in bm.verts:
    if abs(v.co.y) < 1e-4 and v.co.z > top - 1e-4:
        v.co.z += 0.7
bm.to_mesh(me)
bm.free()
:::

## Overhang

Real roofs overshoot the walls so rain does not run down them. The starter roof is already 0.4 m wider than the
walls on every side. Keep an eye on that when you reshape it: an overhang of 0.3 m or more is what reads as "roof"
rather than "lid".

## Openings with Booleans

Cut a **door** and a **window** into the front wall with cutters, the way you did in the Boolean lesson:

- Door: a box 0.95 × 0.5 × 1.9 m, at the front wall (Y ≈ −1.4), bottom on the ground.
- Window: a box 0.7 × 0.5 × 0.7 m, at about X = −1.2, Z = 1.6.

Add a Boolean modifier for each to the **Walls** (Difference, Exact), and set the cutters to display as Wire.

:::task id=openings title="A door and a window" xp=16
Cut two openings into **Walls**: two Boolean Difference modifiers on it, each using its own cutter object. Hide
both cutters from the render.
check: sum(1 for o in meshes if o.name == 'Walls' for m in o.mods if m.type == 'BOOLEAN' and m.p.operation == 'DIFFERENCE') >= 2 :: Walls has two Boolean differences
check: sum(1 for o in meshes if o.display in ('WIRE', 'BOUNDS')) >= 2 :: Two objects are displayed as Wire or Bounds
hint: Add Cube, scale it to fit, move it to the wall. Add the Boolean modifier on Walls and click the cutter into Object.
hint: Repeat for the window. In Object properties > Viewport Display set Display As: Wire on each cutter.
:::
:::solve task=openings
walls = bpy.data.objects['Walls']
col = bpy.data.collections['Cabin']
for name, size, loc in (('Door_Cut', (0.95, 0.5, 1.9), (0, -1.4, 0.95)), ('Window_Cut', (0.7, 0.5, 0.7), (-1.2, -1.4, 1.6))):
    bm = bmesh.new()
    box_at(bm, size, loc)
    cut = kit.mesh_object(name, bm, collection=col)
    cut.display_type = 'WIRE'
    cut.hide_render = True
    m = walls.modifiers.new(name, 'BOOLEAN')
    m.operation, m.solver, m.object = 'DIFFERENCE', 'EXACT', cut
:::

:::note tip title="Frames and glass"
A door sitting inside a hole looks bare. In the finished cabin each opening has a thicker frame
(slightly proud of the wall) and a pane. We build those in the final assembly, but try adding a thin frame
box around the window now, it is a good five-minute exercise.
:::

:::quiz id=q1 xp=5
In Edit Mode, which keys lift only the selected middle edge loop 0.7 m straight up?
- *G, Z, 0.7, Enter
- R, Z, 0.7
- E, 0.7
explain: G is grab, Z locks the movement to the Z axis, 0.7 is the distance. E would extrude new geometry instead of moving the existing edges.
:::
