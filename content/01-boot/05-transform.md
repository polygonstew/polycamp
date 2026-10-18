---
id: transform
title: Grab, Rotate, Scale, Mean It
summary: Exact numbers, snapping, the 3D cursor, and why you apply scale.
minutes: 14
scene: fresh
keys: G, R, S, Ctrl+A, Shift+D, Shift+S
tags: object mode, transform
xp: 40
---
You know G, R and S. What separates tidy scenes from messy ones is **precision**: typing exact values,
snapping, and keeping transforms clean. A scene full of objects at `x = 2.3187` and `scale = 1.0004` will
bite you the first time you use a modifier.

## Type the number

Start a transform, then just type. No need to click a field first.

- [[G]] [[X]] `3` [[Enter]] moves exactly 3 m along X.
- [[R]] [[Z]] `45` [[Enter]] rotates 45° around Z.
- [[S]] `0.5` [[Enter]] scales to half size. [[S]] [[Z]] `2` doubles only the height.
- `-` flips the sign. Type `-2` for the opposite direction.
- Hold [[Ctrl]] while dragging to snap to increments. Hold [[Shift]] to move in slow motion.
- **N panel > Item** shows and edits Location, Rotation, Scale and Dimensions by hand.

:::task id=move title="Move the cube exactly 3 m along X" xp=8
Select the cube and use [[G]] [[X]] `3` [[Enter]], so it ends at X = 3, Y = 0, Z = 0.
check: any(near(o.loc, [3, 0, 0], 0.001) for o in meshes) :: A mesh sits at exactly (3, 0, 0)
hint: Hover the viewport, press G, then X, then type 3 and press Enter.
hint: Or open the sidebar with N, go to the Item tab and type 3 in Location X.
:::

:::task id=rot title="Rotate it 45 degrees around Z" xp=8
Now [[R]] [[Z]] `45` [[Enter]]. Check the Rotation Z field in the sidebar afterwards.
check: any(near(o.rot, [0, 0, 45], 0.5) for o in meshes) :: A mesh is rotated 45° around Z
hint: R then Z then 45 then Enter. The number is degrees.
:::

:::task id=scale title="Squash it: scale 2, 1, 0.5" xp=8
Scale it to a long, flat slab: X doubled, Y unchanged, Z halved. Type it into the sidebar or use
[[S]] [[X]] `2` then [[S]] [[Z]] `0.5`.
check: any(near(o.dims, [4, 2, 1], 0.01) for o in meshes) :: A mesh measures 4 × 2 × 1 m
hint: In the N panel Item tab, set Scale X to 2, Y to 1, Z to 0.5.
:::

## Apply it, or regret it

The slab above has a scale of (2, 1, 0.5) but a mesh that is still a 2 m cube. Blender is remembering
the stretch as a *transform*, not as geometry. Modifiers like Bevel and Solidify read that stretch and
behave strangely: a bevel on a squashed cube comes out squashed too.

**Apply** bakes the transform into the vertices and resets the scale to 1:
[[Ctrl+A]] > **Scale**. (Do the same for Rotation when you want the mesh to keep its tilt but the object to
stop remembering it.)

:::task id=apply title="Apply the scale" xp=10
With the slab selected press [[Ctrl+A]] and choose **Scale**. The Scale fields go back to 1, 1, 1 while
the slab stays long and flat.
check: any(near(o.scale, [1, 1, 1], 0.001) and near(o.dims, [4, 2, 1], 0.01) for o in meshes) :: Scale is 1,1,1 and the object is 4 × 2 × 1 m
hint: Object menu > Apply > Scale. The dimensions in the N panel should read 4, 2, 1 before and after.
:::

:::note warn title="Order matters"
Apply scale *before* adding Bevel, Solidify, Array or anything dimension-sensitive. Make it a reflex.
:::

## Duplicate, and the 3D cursor

- [[Shift+D]] duplicates and starts a grab. Right-click or [[Esc]] cancels the move but keeps the copy.
- [[Alt+D]] makes a *linked* duplicate that shares the mesh. Edit one and all of them change.
- The **3D cursor** (the red-white target) is where new objects appear. Click with the cursor tool,
  or press [[Shift+S]] and use **Cursor to Selected**, **Cursor to World Origin**, or snap the selection to it.

:::task id=dup title="Make a second object" xp=6
Duplicate the slab with [[Shift+D]]. You need at least two meshes in the scene.
check: len(meshes) >= 2 :: There are two or more mesh objects
hint: Shift+D, then click or press Enter to drop it. Escape also keeps the copy at the old position.
:::

:::task id=cursor title="Park the cursor at X = 5" xp=6
Place the 3D cursor exactly on X = 5. In the sidebar open the **View** tab and type 5 into
**3D Cursor > Location X**.
check: near(scene.cursor, [5, 0, 0], 0.001) :: The 3D cursor is at (5, 0, 0)
hint: N panel > View tab > 3D Cursor. Y and Z should stay 0.
:::

:::match id=m1 xp=6
Match the shortcut to what it does.
Duplicate => Shift+D
Snap pie menu (cursor and selection) => Shift+S
Apply menu => Ctrl+A
Hide the selected object => H
:::

:::cubby
Applying scale is a bit like cleaning your desk. Nothing visibly improves, and everything later goes
smoother. Do it.
:::

:::solve
cube = bpy.data.objects['Cube']
cube.location = (3, 0, 0)
cube.rotation_euler = (0, 0, math.radians(45))
cube.scale = (2, 1, 0.5)
# apply scale: bake it into the mesh, reset the object's scale
cube.data.transform(Matrix.Diagonal((2, 1, 0.5, 1)))
cube.scale = (1, 1, 1)
dup = cube.copy()
dup.data = cube.data.copy()
dup.location = (3, 4, 0)
bpy.context.scene.collection.objects.link(dup)
bpy.context.scene.cursor.location = (5, 0, 0)
:::
