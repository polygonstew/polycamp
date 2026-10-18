---
id: edit-mode
title: Edit Mode and Selecting
summary: Vertex, edge and face mode, and the selection tricks that save hours.
minutes: 12
scene: fresh
keys: Tab, 1, 2, 3, A, Alt+A, B, C, L
tags: edit mode, selection
xp: 40
---
Object Mode moves whole things. **Edit Mode** changes what a thing is made of. Press [[Tab]] with a mesh
selected and the cube suddenly shows its eight corner **vertices**, twelve **edges** and six **faces**.

Inside Edit Mode there are three **select modes**, one key each on the number row:

- [[1]] **Vertex**: points.
- [[2]] **Edge**: lines between points.
- [[3]] **Face**: the flat surfaces.

Select in whichever mode matches what you want to move. Moving a face moves the four corners with it, but
you never have to click each corner.

:::task id=enter title="Enter Edit Mode" xp=6
Select the cube and press [[Tab]]. The header now says *Edit Mode* and the cube shows its vertices.
check: edit :: You are in Edit Mode
hint: Hover the viewport first. Tab toggles between Object and Edit Mode.
:::
:::solve task=enter
bpy.ops.object.mode_set(mode='EDIT')
:::

## Select, add, subtract

Plain click selects one. [[Shift+LMB]] adds or removes. Beyond clicking:

| Keys | What it does |
| --- | --- |
| [[A]] | select all |
| [[Alt+A]] | select nothing |
| [[Ctrl+I]] | invert the selection |
| [[B]] | box select (drag a rectangle) |
| [[C]] | circle select, paint with the mouse; scroll to resize the brush |
| [[L]] | select everything connected under the cursor |
| [[Alt+LMB]] | select a whole **edge loop** or ring |

Box select normally ignores things behind the front surface. Turn on X-ray with [[Alt+Z]] to select
straight through.

:::task id=face title="Select exactly one face" xp=8
Switch to Face mode with [[3]] and click one face of the cube. Exactly one should be selected, so the
statistics overlay reads 1/6 faces.
check: edit and 'FACE' in active.select_mode and active.sel_faces == 1 :: Face mode, one face selected
hint: Press 3 for face select mode, then click in the middle of a face (the dot in the centre).
hint: If more than one face lights up, press Alt+A to clear and click again.
:::
:::solve task=face
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.select_all(action='DESELECT')
me = bpy.context.object.data
bm = bmesh.from_edit_mesh(me)
bm.faces.ensure_lookup_table()
bm.faces[0].select_set(True)
bmesh.update_edit_mesh(me)
:::

:::task id=all title="Select everything" xp=6
Press [[A]] to select every vertex.
check: edit and active.sel_verts == active.verts :: All vertices are selected
hint: A selects all, Alt+A clears. In 2.7x it toggled, but not any more.
:::
:::solve task=all
bpy.ops.mesh.select_all(action='SELECT')
:::

## Move something, then go back

Face mode, click the **top** face, then [[G]] [[Z]] `1` [[Enter]] lifts it one metre. Press [[Tab]] again to
return to Object Mode. The cube is now a 2 × 2 × 3 box. You changed the mesh itself, not an object
transform: the Scale fields still say 1, 1, 1.

:::task id=lift title="Lift the top face by 1 m, then Tab out" xp=14
Select the top face only, move it up exactly 1 m, and leave Edit Mode. The object's Dimensions in the
sidebar should read 2, 2, 3.
check: not edit and any(near(o.dims, [2, 2, 3], 0.01) for o in meshes) :: Back in Object Mode, and a mesh measures 2 × 2 × 3 m
hint: Switch to Face mode (3), click the top face, then G Z 1 Enter. Then Tab.
hint: Dimensions live in the N panel under the Item tab. They update only after you leave Edit Mode.
:::
:::solve task=lift
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.select_all(action='DESELECT')
me = bpy.context.object.data
bm = bmesh.from_edit_mesh(me)
for f in bm.faces:
    f.select_set(f.normal.z > 0.9)
bmesh.update_edit_mesh(me)
bpy.ops.transform.translate(value=(0, 0, 1))
bpy.ops.object.mode_set(mode='OBJECT')
:::

:::quiz id=q1 xp=5
You want to move a whole face as one piece. Which select mode is the most direct?
- Vertex mode, because faces are made of vertices
- *Face mode, because one click picks the whole face
- Object mode
explain: All three can move a face. Face mode needs the fewest clicks and shows you the surface you are actually working on.
:::

:::keys id=k1 xp=8
Toggle Edit Mode | Tab
Vertex select mode | 1
Select all | A
Select nothing | Alt+A
Box select | B
:::

:::cubby think
Fun fact: in Edit Mode I stop being a cube and become a small collection of nervous dots. Please be gentle
with the dots.
:::
