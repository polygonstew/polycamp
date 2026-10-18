---
id: blockout
title: Blocking Out and Real Scale
summary: Rough shapes first, in real units, before any detail.
minutes: 12
scene: empty
keys: Shift+Tab, N, Shift+A
tags: scale, planning
xp: 40
---
Pros do not start with a door handle. They start with **big, ugly, correctly sized boxes**. This is called a
**blockout**. If the proportions are wrong, no amount of bevelling will rescue the model, and changing a
box is a thirty-second job while changing a finished model is a day.

## Units

Blender's default unit is the **metre** (Scene properties > Units: Metric, Unit Scale 1). One grid square
in the viewport is one metre. Model things at real size: a door is about 0.9 × 2.0 m, a person about 1.75 m,
a mug 0.1 m. Real scale pays off later because physics, lights, depth of field and camera lenses all behave
as if the scene is real.

:::note tip title="Check against a person"
A quick sanity trick: drop in a 1.75 m tall box, call it `Human`, and look at it next to your door. Delete it
before you render.
:::

## Plan the footprint

The cabin for the final scene is 3.6 m wide, 2.8 m deep and 2.1 m to the eaves (the top of the walls). The roof
sits above that with a bit of overhang. The ground is a round slab 9 m across.

Build five boxes. Dimensions go in the sidebar ([[N]] > Item > Dimensions) so you can type them exactly.
Put the cabin boxes at ground level: their bottom should sit at Z = 0.

:::task id=walls title="Walls: 3.6 × 2.8 × 2.1 m" xp=10
Add a cube, name it **Cabin_Walls**, set its **Dimensions** to **3.6, 2.8, 2.1** and move it up so the bottom
is on the ground (Z location 1.05).
check: any(o.name == 'Cabin_Walls' and near(o.dims, [3.6, 2.8, 2.1], 0.05) for o in meshes) :: Cabin_Walls measures 3.6 × 2.8 × 2.1
check: any(o.name == 'Cabin_Walls' and abs(o.wbox[2]) < 0.05 for o in meshes) :: And its bottom sits on the ground
hint: Shift+A > Mesh > Cube. Name it with F2. In the N panel Item tab, type the three dimensions.
hint: Changing Dimensions does not move the origin. Set Location Z to half the height so the bottom touches Z = 0.
:::
:::solve task=walls
bm = bmesh.new()
box_at(bm, (3.6, 2.8, 2.1), (0, 0, 1.05))
kit.mesh_object('Cabin_Walls', bm)
:::

:::task id=roof title="Roof: wider than the walls" xp=10
Add **Cabin_Roof**: a slab 4.4 × 3.6 × 0.5 m, sitting on top of the walls (its bottom at Z = 2.1). The extra width
is the overhang.
check: any(o.name == 'Cabin_Roof' and o.dims[0] >= 4.2 and o.dims[1] >= 3.4 for o in meshes) :: Cabin_Roof is at least 4.2 × 3.4 m
check: any(o.name == 'Cabin_Roof' and abs(o.wbox[2] - 2.1) < 0.1 for o in meshes) :: Its bottom rests on the walls
hint: Duplicate the walls with Shift+D, then change the dimensions and move it. Or add a new cube.
:::
:::solve task=roof
bm = bmesh.new()
box_at(bm, (4.4, 3.6, 0.5), (0, 0, 2.35))
kit.mesh_object('Cabin_Roof', bm)
:::

:::task id=door title="A door-sized marker" xp=8
Add a thin block named **Door_Marker**, 0.95 m wide and 1.9 m tall, flush against the front wall (the side facing
−Y). It shows where the door will go so you can check proportions.
check: any(o.name == 'Door_Marker' and near(o.dims[0], 0.95, 0.08) and near(o.dims[2], 1.9, 0.1) for o in meshes) :: Door_Marker is 0.95 wide and 1.9 tall
hint: Cube, dimensions 0.95 × 0.1 × 1.9. Place it against the front wall.
:::
:::solve task=door
bm = bmesh.new()
box_at(bm, (0.95, 0.1, 1.9), (0, -1.4, 0.95))
kit.mesh_object('Door_Marker', bm)
:::

:::task id=ground title="The ground disc" xp=10
Add a **Cylinder** called **Ground**, radius 4.5 (9 m wide), only 0.2 m thick, its top surface at Z = 0.
check: any(o.name == 'Ground' and o.dims[0] >= 8.5 and o.dims[2] <= 0.5 and abs(o.wbox[5]) < 0.05 for o in meshes) :: Ground is about 9 m across, thin, with its top at Z = 0
hint: Shift+A > Mesh > Cylinder, then in the Adjust Last Operation panel set Radius 4.5 and Depth 0.2. Move it down by 0.1.
:::
:::solve task=ground
bm = bmesh.new()
kit.add_cylinder(bm, 4.5, 0.2, 48, center=(0, 0, -0.1))
kit.mesh_object('Ground', bm)
:::

## Keep it in a collection

Organise from the first box: select all four and press [[M]] > **New Collection** called **Blockout**. When you
build the real thing you can hide the blockout and use it as reference.

:::task id=coll title="Put them in a Blockout collection" xp=6
Move all four objects into a collection called **Blockout**.
check: any(c.name == 'Blockout' and c.objects >= 4 for c in cols) :: A collection Blockout holds four or more objects
hint: Select all with A, press M, choose New Collection.
:::
:::solve task=coll
col = bpy.data.collections.new('Blockout')
bpy.context.scene.collection.children.link(col)
for ob in list(bpy.context.scene.objects):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
:::

:::note cpu title="Snapping"
Hold [[Ctrl]] while moving to snap to increments, or turn on the **magnet** icon in the header and choose
*Increment* or *Vertex*. [[Shift+Tab]] toggles snapping. Snapping to the grid is the cheapest way to line things up.
:::

:::quiz id=q1 xp=5
Why model at real-world size even for a stylised scene?
- It looks better in the viewport
- *Lights, camera lenses, depth of field and physics all assume real units
- Blender refuses to work otherwise
explain: A 50 mm lens, an 80 W lamp and a gravity simulation all behave as in real life when your objects are real size.
:::
