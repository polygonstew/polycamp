---
id: extrude-inset
title: Extrude and Inset
summary: The two tools behind most of what you will ever model.
minutes: 14
scene: fresh
keys: E, I, X, Alt+E
tags: edit mode, modeling
xp: 45
---
If you only learned two modelling tools, these would carry you through a surprising amount of work.
Almost every hard-surface object starts as a box, then gets **extruded** into a shape and **inset** into
detail.

## Extrude: pull new geometry out of old

Select a face, press [[E]], move the mouse and click. Blender copies the face, drags it away, and builds
walls between the old position and the new one. Type a number to be exact: [[E]] `2` [[Enter]] pushes it
2 m along its normal.

Two details trip people:

- With **one face** selected, [[E]] extrudes along its normal, the direction it points away from the
  surface. With **several faces** selected, [[E]] moves each in its own direction ("individual faces"
  is **Alt+E** > *Extrude Faces Along Normals*).
- Cancel with [[Esc]] or right-click **after** extruding and the new faces stay where they started,
  stacked on the old ones, invisible but real. Then press [[Ctrl+Z]], not Esc, to remove them.

:::note warn title="The classic ghost"
If you press E, change your mind, and press Esc, you leave a duplicate face sitting inside the mesh. It
looks fine and wrecks shading and booleans later. Undo instead. Statistics will show you extra faces
if you have done this.
:::

:::task id=tower title="Build a tower" xp=14
Extrude the cube's top face upward by 2 m so it becomes a 2 × 2 × 4 tower. (A single extrude of 2 m is
fine.)
check: any(near(o.dims, [2, 2, 4], 0.02) and o.faces == 10 for o in meshes) :: A 2 × 2 × 4 box with exactly 10 faces
hint: Tab into Edit Mode, press 3 for face mode, click the top face, then E Z 2 Enter. Tab out.
hint: Exactly 10 faces means one clean extrude. If you see more, you probably extruded twice or left a ghost. Undo and try again.
:::
:::solve task=tower
bpy.ops.object.mode_set(mode='EDIT')
me = bpy.context.object.data
bm = bmesh.from_edit_mesh(me)
top = [f for f in bm.faces if f.normal.z > 0.9]
res = bmesh.ops.extrude_face_region(bm, geom=top)
moved = [e for e in res['geom'] if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.translate(bm, vec=(0, 0, 2), verts=moved)
bmesh.ops.delete(bm, geom=top, context='FACES')      # the editor's Extrude removes the original face; bmesh keeps it
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
:::

## Inset: a smaller face inside a face

[[I]] shrinks the selected face toward its centre and leaves a **frame** of new faces around it. Type a
value or drag. Use it to make panels, windows, buttons and the rim of anything that will be hollowed out.

The recipe for a recessed panel:

1. Select the face, [[I]], type `0.3`, [[Enter]]. You now have a frame and an inner face.
2. Press [[E]] and push the inner face *inwards* with a negative number: `-0.2`. That is a pocket.

Or pull it *outwards* with a positive number and you get a raised button.

:::task id=pit title="Carve a pit into the top" xp=14
On the tower's top face: inset by 0.3, then extrude the inner face down by 0.4. You will end up with
**18 faces** (10 original, 4 from the inset, 4 from the pit walls).
check: any(o.faces == 18 and o.verts == 20 for o in meshes) :: A mesh with 18 faces and 20 vertices
hint: Select the top face, press I, type 0.3, Enter. Then E, type -0.4, Enter. Negative goes inwards.
hint: Wrong counts? An extra ghost face probably sneaked in. Ctrl+Z back to the inset and redo the extrude.
:::
:::solve task=pit
bpy.ops.object.mode_set(mode='EDIT')
me = bpy.context.object.data
bm = bmesh.from_edit_mesh(me)
top = [f for f in bm.faces if f.normal.z > 0.9]
bmesh.ops.inset_region(bm, faces=top, thickness=0.3, depth=0.0)
inner = [f for f in bm.faces if f.normal.z > 0.9 and f.calc_area() > 1.0]      # the frame faces are small, the middle one is big
res = bmesh.ops.extrude_face_region(bm, geom=inner)
moved = [e for e in res['geom'] if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.translate(bm, vec=(0, 0, -0.4), verts=moved)
bmesh.ops.delete(bm, geom=inner, context='FACES')
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
:::

## Delete without making a mess

[[X]] opens the delete menu, and the choices matter:

- **Vertices** removes the points and every face that used them. Leaves holes.
- **Edges** and **Faces** remove those elements and the things that depended on them.
- **Only Faces** removes the surface but keeps the edges, so you can rebuild it.
- **Dissolve** removes the element but heals the hole around it. This is usually what you want.

Rule of thumb: **Delete** when you want something gone, **Dissolve** when you want the shape to stay
closed.

:::task id=hole title="Open a window: delete the bottom face" xp=10
Delete only the **bottom face** of the tower ([[X]] > **Faces**) so it is open underneath. The mesh now
has boundary edges (the rim of the hole).
check: any(o.boundary_edges == 4 for o in meshes) :: A single 4-edge opening exists
hint: Face mode, click the bottom face (rotate the view or use X-ray), X, then Faces.
hint: Alt+Z toggles X-ray so you can click faces that face away from you.
:::
:::solve task=hole
bpy.ops.object.mode_set(mode='EDIT')
me = bpy.context.object.data
bm = bmesh.from_edit_mesh(me)
bot = [f for f in bm.faces if f.normal.z < -0.9]
bmesh.ops.delete(bm, geom=bot, context='FACES')
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
:::

:::quiz id=q1 xp=5
You extrude a face, change your mind and press Esc. What is left behind?
- Nothing, it is fully cancelled
- *A copy of the face that sits exactly where it started, stacked on the old one
- The extruded walls
explain: Esc cancels the movement, not the extrusion. The duplicated face stays. Use Ctrl+Z to undo the extrusion entirely.
:::

:::match id=m1 xp=6
Match the tool to the job.
Make a raised button on a flat panel => Inset, then Extrude outwards
Remove an edge loop and keep the surface closed => Dissolve
Pull a wall up from a floor plan => Extrude
Remove a face but keep its edges => Delete > Only Faces
:::

:::keys id=k1 xp=8
Extrude | E
Inset | I
Delete menu | X
Face select mode | 3
:::
