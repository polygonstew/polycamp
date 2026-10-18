---
id: stack
title: The Modifier Stack
summary: What a modifier is, why order matters, and viewport versus render levels.
minutes: 10
scene: fresh
keys: Ctrl+2, Ctrl+A
tags: modifiers
xp: 35
---
Open the **Modifiers** tab in Properties (the blue wrench). Click **Add Modifier** and you get a menu of
about fifty things, grouped as *Edit*, *Generate*, *Deform*, *Normals*, *Physics*. Pick one and it appears
as a panel in a vertical list called the **stack**.

The stack runs **from top to bottom**. Each modifier takes the result of the one above it as input. That
single fact explains most "why does this look wrong" moments.

## Subdivision Surface: your first modifier

Select the cube, press [[Ctrl+2]]. The cube turns into a rounded blob. You did not change a single vertex
(Tab into Edit Mode: the original eight are still there). Subdivision Surface splits every face into
smaller ones and rounds the result.

There are two sliders you must learn to love:

- **Levels Viewport**: how much smoothing you see while working.
- **Render**: how much smoothing the final render gets.

Each level multiplies the face count by four. A cube at level 3 is 384 faces, and a detailed model at level 4
can melt a laptop. Work at 1 or 2, render at 3.

:::task id=sub title="Subdivision: 1 in the viewport, 3 for the render" xp=10
Add a Subdivision Surface modifier. Set **Levels Viewport** to **1** and **Render** to **3**.
check: any(m.type == 'SUBSURF' and m.p.levels == 1 and m.p.render_levels == 3 for o in meshes for m in o.mods) :: Subdivision Surface with viewport 1, render 3
hint: Ctrl+2 sets both numbers to 2. Change them in the modifier panel: Levels Viewport and Render are separate fields.
hint: Modifiers tab (wrench icon) > expand the modifier panel > Levels Viewport, Render.
:::
:::solve task=sub
ob = bpy.context.active_object or bpy.data.objects['Cube']
m = ob.modifiers.new('Subdivision', 'SUBSURF')
m.levels, m.render_levels = 1, 3
:::

## Order matters

Add a **Bevel** modifier as well. Two arrangements are possible:

1. *Bevel on top of Subdivision*: Bevel runs last, on the already-smoothed result, so it does almost nothing.
2. *Subdivision on top of Bevel*: the bevel creates support loops first, then Subdivision rounds around
   them. The corners come out tight but soft: the classic hard-surface look.

Drag a modifier panel by its **grip dots** on the left side of its header to reorder, or use the
drop-down arrow > **Move to First**.

:::task id=order title="Bevel first, Subdivision second" xp=12
Add a **Bevel** modifier (Width 0.1, Segments 2) and make sure it sits **above** the Subdivision
Surface in the stack.
check: [m.type for o in meshes for m in o.mods][:2] == ['BEVEL', 'SUBSURF'] :: The stack starts BEVEL then SUBSURF
check: any(m.type == 'BEVEL' and m.p.segments >= 2 for o in meshes for m in o.mods) :: Bevel has at least 2 segments
hint: Add Modifier > Generate > Bevel. Then drag its header above the Subdivision panel, or open its drop-down and pick Move to First.
hint: Segments 2 gives each bevelled edge a middle vertex, which the subdivision then holds on to.
:::
:::solve task=order
ob = bpy.context.active_object or bpy.data.objects['Cube']
b = ob.modifiers.new('Bevel', 'BEVEL')
b.width, b.segments = 0.1, 2
modifier_to_front(ob, b)
:::

## Switches, and making it permanent

Each modifier has **two small icons** in its header: a *monitor* (show in viewport) and a *camera* (show in
render). Switch the monitor off when the viewport gets slow, and the camera stays on so the final render is
unaffected.

**Apply** ([[Ctrl+A]] while hovering the modifier, or the drop-down > Apply) turns the modifier's result
into real geometry and removes it. Apply is a one-way door, and only the *first* modifier in the stack can
be applied cleanly. Keep the stack for as long as you can.

:::note warn title="Apply scale first"
Modifiers that depend on distance (Bevel width, Solidify thickness, Displace) read the object's scale.
A cube scaled to (1, 1, 3) bevels unevenly. Apply scale with [[Ctrl+A]] > Scale before adding such modifiers.
:::

:::quiz id=q1 xp=5
Where do you change how smooth the *final render* is, without slowing the viewport?
- Edit Mode > Subdivide
- *The Render level on the Subdivision Surface modifier
- The Cycles samples
explain: Subdivision has separate Viewport and Render levels so you can model fast and render beautifully.
:::

:::quiz id=q2 xp=5
In the stack the order is: Subdivision Surface on top, Bevel under it. What do you get?
- The same result as Bevel first
- *A bevel on smooth geometry that barely changes the shape
- An error
explain: Modifiers run top to bottom, so Bevel gets the already-subdivided mesh. For tight edges, bevel first and subdivide second.
:::

:::cubby wink
A modifier stack is just a recipe. Change an ingredient at the top and everything below re-cooks itself. I
find it deeply satisfying and slightly unfair to cubes.
:::
