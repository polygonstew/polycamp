---
id: boolean
title: Boolean: Cutting With Objects
summary: Punch windows, notches and slots using a second object as the cookie cutter.
minutes: 12
scene: starter:wall-cutter
keys: Ctrl+A
tags: modifiers, hard surface
xp: 40
---
A **Boolean** modifier uses one object to cut, add to, or trim another. It is how you cut a round window out
of a wall in seconds, with no vertex pushing.

Three operations:

- **Difference**: subtract the cutter from the wall. A hole.
- **Union**: merge the two into one shape.
- **Intersect**: keep only the part where they overlap.

The object that does the cutting is the **operand**, and it lives in the scene like anything else. You can
move it afterwards and the hole follows. That is the real power: change your mind about where the window
goes by dragging one cylinder.

## Two solvers

- **Exact** is the default and the one to use. It handles overlapping cuts, coplanar faces and awkward
  geometry, at the cost of speed on very heavy meshes.
- **Fast** is quicker and breaks on coincident faces. It also does not like cutters that touch the wall's
  surface precisely.

:::task id=cut title="Cut a round window" xp=14
Select **Wall** and add a **Boolean** modifier. Set the **Operation** to **Difference**, pick **Cutter** as
the **Object**, and use the **Exact** solver. A circular hole appears.
check: any(o.name == 'Wall' and any(m.type == 'BOOLEAN' and m.p.operation == 'DIFFERENCE' and m.p.object == 'Cutter' for m in o.mods) for o in meshes) :: Wall has a Boolean difference with Cutter
check: any(o.name == 'Wall' and any(m.type == 'BOOLEAN' and m.p.solver == 'EXACT' for m in o.mods) for o in meshes) :: Using the Exact solver
hint: Add Modifier > Generate > Boolean. Click the Object field and choose Cutter from the list, or click the eyedropper and then the cutter.
hint: Operation is a row of three buttons: Intersect, Union, Difference.
:::
:::solve task=cut
wall = bpy.data.objects['Wall']
m = wall.modifiers.new('Window cut', 'BOOLEAN')
m.operation = 'DIFFERENCE'
m.solver = 'EXACT'
m.object = bpy.data.objects['Cutter']
:::

## Tidy the cutter

Right now the red cylinder is still visible and would render. A cutter should be a ghost: visible while you
work, hidden from the final image. Two common tricks:

1. **Display As: Wire** (Object properties > Viewport Display) so it shows as an outline you can still grab.
2. Switch off its **camera** icon in the Outliner (Disable in Renders) so it never appears in a render.

:::task id=ghost title="Make the cutter a wireframe ghost" xp=10
In the Object properties tab > **Viewport Display** set **Display As** to **Wire** (or Bounds) for the cutter.
check: any(o.name == 'Cutter' and o.display in ('WIRE', 'BOUNDS') for o in objects) :: Cutter is displayed as Wire or Bounds
hint: Click the cutter, orange square icon tab (Object), expand Viewport Display, change Display As.
hint: Alt+click selects the cylinder if it sits inside the wall and is awkward to pick. Or click its name in the Outliner.
:::
:::solve task=ghost
bpy.data.objects['Cutter'].display_type = 'WIRE'
bpy.data.objects['Cutter'].hide_render = True
:::

Now grab the cutter, move it along the wall with [[G]] and watch the hole follow.

:::note warn title="Do not apply early"
Applying a Boolean throws away the cutter's flexibility and often leaves ugly ngons on the cut edge. Keep
it live until the design is final. If you do apply it, clean up with Dissolve and a bevel afterwards.
:::

## The Bool Tool shortcut

Blender ships an add-on called **Bool Tool** (Edit > Preferences > Add-ons, tick *Object: Bool Tool*). It
adds one-key boolean operations ([[Ctrl+Numpad -]] for difference, [[Ctrl+Numpad +]] for union). It is not
essential, but if you cut many things in a model, it saves a lot of clicks.

:::quiz id=q1 xp=5
Your Boolean difference leaves a bumpy, broken hole. What do you try first?
- Raise the Subdivision level
- *Switch the solver to Exact
- Delete the cutter
explain: The Fast solver is unreliable on coplanar or touching faces. Exact is slower but much more forgiving.
:::

:::order id=o1 xp=6
Put the steps of a clean Boolean cut in order.
1. Model the wall and the cutter as separate objects
2. Add a Boolean modifier to the wall
3. Set Operation to Difference and pick the cutter object
4. Set the cutter to display as Wire and hide it from the render
5. Move the cutter until the hole is exactly where you want it
:::
