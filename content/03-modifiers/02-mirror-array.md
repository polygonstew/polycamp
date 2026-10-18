---
id: mirror-array
title: Mirror and Array
summary: Model half and get the other half free. Model one and get a row of them.
minutes: 12
scene: starter:post-and-half
keys: Shift+Alt+X
tags: modifiers
xp: 40
---
Most objects are symmetrical, and most scenes repeat things: fence posts, windows, steps, bars of a cage.
Modelling each copy by hand wastes time and guarantees they will not match. Two modifiers solve that.

## Mirror

Model **one half**. Add a **Mirror** modifier. The other half appears, and every edit you make to the first half
appears in the second as well.

The mirror happens around the object's **origin** (the little orange dot), along the axes you tick (X, Y, Z).
So the origin has to sit on the line of symmetry. The starter's `HalfHull` has been placed with its origin on
the centre line. Its open edge touches the mirror plane.

Settings that matter:

- **Axis**: X, Y or Z. Tick more than one for four-way or eight-way symmetry.
- **Merge** (on by default): welds vertices that touch the mirror plane so there is no seam. The distance field
  decides how close counts as touching.
- **Clipping**: while editing, stops vertices crossing the mirror plane so you cannot open a gap.
- **Bisect**: slices off whatever sticks over the plane, handy when you start from a full model.

:::task id=mirror title="Mirror the half hull across X" xp=14
Select **HalfHull** and add a **Mirror** modifier (Add Modifier > Generate > Mirror). X is ticked by default.
Make sure **Merge** is on and tick **Clipping**.
check: any(o.name == 'HalfHull' and any(m.type == 'MIRROR' and m.p.use_axis[0] and m.p.use_mirror_merge for m in o.mods) for o in meshes) :: HalfHull has a Mirror on X with Merge on
check: any(o.name == 'HalfHull' and any(m.type == 'MIRROR' and m.p.use_clip for m in o.mods) for o in meshes) :: Clipping is on
hint: Click HalfHull, then the Modifiers tab (wrench) > Add Modifier > Generate > Mirror.
hint: Clipping is a checkbox in the modifier panel. Merge is another one, usually already ticked.
:::
:::solve task=mirror
ob = bpy.data.objects['HalfHull']
m = ob.modifiers.new('Mirror', 'MIRROR')
m.use_axis = (True, False, False)
m.use_mirror_merge = True
m.use_clip = True
:::

:::note tip title="Mirror about another object"
Slot an Empty or any object into the modifier's **Mirror Object** field and the mirror plane moves to that
object's origin. Useful when you cannot or do not want to move an origin.
:::

## Array

An **Array** modifier makes N copies of the object, each shifted from the last. Three ways to set the shift,
usable alone or together:

- **Relative Offset**: the shift is a multiple of the object's own size. X = 1 puts copies edge to edge,
  X = 2 leaves a gap equal to the object's width. Good for tiles and bricks.
- **Constant Offset**: a fixed distance in metres. Good for fence posts at exactly 1.5 m.
- **Object Offset**: use another object's transform as the shift. Rotate an Empty and the array curves into
  a spiral staircase.

The **Count** can be fixed, or **Fit Length** can fill a given distance, or **Fit Curve** follows a curve.

:::task id=array title="Five posts, spaced out" xp=14
Select **Post** and add an **Array** modifier with **Count 5**. Set the **Relative Offset X** to **4**, so the
gaps between posts are three post-widths.
check: any(o.name == 'Post' and any(m.type == 'ARRAY' and m.p.count == 5 for m in o.mods) for o in meshes) :: Post has an Array with count 5
check: any(o.name == 'Post' and any(m.type == 'ARRAY' and m.p.relative_offset_displace[0] >= 3 for m in o.mods) for o in meshes) :: Relative Offset X is 3 or more
hint: Add Modifier > Generate > Array. The default is count 2 and Relative Offset X = 1.
hint: Relative Offset is a three-number row (X, Y, Z). Type 4 into the first.
:::
:::solve task=array
ob = bpy.data.objects['Post']
m = ob.modifiers.new('Array', 'ARRAY')
m.count = 5
m.use_relative_offset = True
m.relative_offset_displace = (4.0, 0.0, 0.0)
:::

## Stack them

Modifiers do not mind being combined. Give the post a **Bevel** above the Array and every copy gets bevelled
edges; put the Array above and the Bevel works on the combined shape. Try both and look at the difference.

:::quiz id=q1 xp=5
A Mirror modifier is doing something odd: the copy appears far from the original. What is the most likely cause?
- Merge is off
- *The object's origin is not on the line you want to mirror across
- Clipping is on
explain: Mirror reflects through the object's origin. Move the origin to the symmetry line (or use a Mirror Object) and the copy lands where you expect.
:::

:::quiz id=q2 xp=5
You want fence posts exactly 1.5 m apart no matter how wide the post is. Which offset?
- Relative Offset
- *Constant Offset
- Merge
explain: Relative Offset scales with the object's size. Constant Offset is in real units.
:::
