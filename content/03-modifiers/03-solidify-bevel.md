---
id: solidify-bevel
title: Solidify and the Bevel Modifier
summary: Give thin surfaces thickness, then catch the light on every edge.
minutes: 12
scene: starter:tray
keys: Ctrl+A
tags: modifiers, hard surface
xp: 40
---
Two modifiers do most of the work behind clean hard-surface models.

## Solidify

A single flat face has no thickness: it renders as an infinitely thin sheet. **Solidify** pushes it out in
both directions (or just one) into a real slab with walls. Use it for trays, panels, leaves, cloth, paper,
a shelf.

The settings:

- **Thickness**: how deep, in metres.
- **Offset**: -1 grows inward (the original surface is the outside), 0 is centred, 1 grows outward.
- **Even Thickness**: keeps walls the same thickness around sharp corners. Almost always worth ticking.

The starter scene is a flat open-bottomed plate. Make it a tray.

:::task id=solid title="Give the tray thickness" xp=12
Select **Tray** and add a **Solidify** modifier with **Thickness 0.08** and **Even Thickness** on.
check: any(o.name == 'Tray' and any(m.type == 'SOLIDIFY' and m.p.thickness >= 0.07 and m.p.use_even_offset for m in o.mods) for o in meshes) :: Solidify, thickness 0.07 or more, Even Thickness on
hint: Add Modifier > Generate > Solidify. Thickness is the first field.
hint: Even Thickness is a checkbox in the panel under Thickness. Tick it.
:::
:::solve task=solid
ob = bpy.data.objects['Tray']
m = ob.modifiers.new('Solidify', 'SOLIDIFY')
m.thickness = 0.08
m.use_even_offset = True
:::

## The Bevel modifier

Last lesson you bevelled in Edit Mode. The **Bevel modifier** does the same job *non-destructively*: change
the width, the segments, which edges, and the model updates. For hard-surface work you will use this
much more than Ctrl+B.

The decisions in the panel:

- **Width** and **Segments**. Small width (a millimetre or two in real life), 2 to 3 segments.
- **Limit Method**. *None* bevels every edge. **Angle** bevels only edges sharper than a threshold, which
  is almost always right, so flat areas and curves are left alone. **Weight** bevels only edges you painted
  with bevel weight, for full control.
- **Harden Normals** keeps flat faces looking flat after the bevel. It is a shading trick that matters when
  you also use smooth shading.

Put **Solidify first, Bevel second**: the bevel then sees the finished slab and softens its new edges.

:::task id=bevel title="Bevel by angle, 2 segments, tiny width" xp=14
Add a **Bevel** modifier below the Solidify. Set **Limit Method** to **Angle**, **Segments** to **2** and
**Width** to **0.015** or less.
check: [m.type for o in meshes if o.name == 'Tray' for m in o.mods][:2] == ['SOLIDIFY', 'BEVEL'] :: The stack is SOLIDIFY then BEVEL
check: any(o.name == 'Tray' and any(m.type == 'BEVEL' and m.p.limit_method == 'ANGLE' and m.p.segments >= 2 and m.p.width <= 0.02 for m in o.mods) for o in meshes) :: Bevel: Angle limit, 2+ segments, width 0.02 or less
hint: Add Modifier > Generate > Bevel. Limit Method is a row of buttons near the top.
hint: Width is in metres: 0.015 is a millimetre and a half on a tray this size.
:::
:::solve task=bevel
ob = bpy.data.objects['Tray']
b = ob.modifiers.new('Bevel', 'BEVEL')
b.limit_method = 'ANGLE'
b.angle_limit = math.radians(30)
b.segments = 2
b.width = 0.015
:::

:::note cpu title="Cheap realism"
A bevel of one or two millimetres on every hard edge is the single cheapest realism upgrade in 3D. It
costs a few faces and catches highlights that a perfectly sharp edge never would.
:::

## Applying and what could go wrong

If you *Apply* the Solidify before the Bevel, the mesh becomes real geometry. Do it only when you need to
edit the result by hand. Most of the time, leave the stack alone.

:::quiz id=q1 xp=5
Which Bevel Limit Method is the best default for a hard-surface object?
- None
- *Angle
- Vertex Group
explain: Angle bevels the sharp edges and leaves curved or flat areas alone, so you do not have to select anything.
:::

:::match id=m1 xp=6
Match the setting to what it changes.
Solidify > Offset => Which side the thickness grows toward
Bevel > Segments => How round the bevel is
Bevel > Limit Method => Which edges get bevelled
Solidify > Even Thickness => Walls stay the same thickness at corners
:::
