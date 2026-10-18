---
id: boss-totem
title: Boss: The Totem Pole
summary: Build a tall, tidy totem from primitives. Names, collection, parent, saved.
minutes: 15
scene: fresh
boss: true
keys: Shift+A, G, S, M, Ctrl+P
tags: boss
xp: 80
---
:::cubby shock
A **boss**. Every world ends with one. You get no new information here. You use what you have, and the
link checks the result. If you pass, the world is finished and I get promoted to Assistant Cube.
:::

## The job

Build a **totem pole** at least six metres tall from stacked primitives. It should look like something a
person made on purpose: different shapes on the way up, sensible names, tidy organisation. Beauty is
optional, but if you want to give it eyes, nobody will stop you.

You can use the default cube, delete it, or reshape it. Whatever you do, the checks look at the final
scene.

:::task id=pieces title="At least five pieces, at least three different shapes" xp=15
Stack five or more mesh objects. Use at least three kinds of primitive (cube, cylinder, sphere, cone,
torus...) so the pole is not five copies of the same lump.
check: len(meshes) >= 5 :: Five or more mesh objects
check: len({o.verts for o in meshes}) >= 3 :: At least three different shapes (by vertex count)
hint: Shift+A > Mesh, pick a primitive, move it up with G Z, repeat. Scale each piece with S.
hint: Vertex counts differ per primitive: cube 8, cylinder 64, UV sphere 482, cone 33, torus 576.
:::

:::task id=tall title="Six metres tall" xp=15
From the lowest point to the highest point, the pole must be at least **6 m**. Use the sidebar
Dimensions fields or Statistics to check your sizes.
check: max(o.wbox[5] for o in meshes) - min(o.wbox[2] for o in meshes) >= 6 :: The pole spans 6 m or more in height
hint: Each piece is 2 m tall by default. Five of them stacked is 10 m, so you may need to scale them down.
:::

:::task id=names title="No default names left" xp=10
Every mesh gets a real name. Nothing called Cube, Sphere, Cylinder, Cone, Plane, Torus, Circle or
Icosphere (including the `.001` suffixed ones).
check: all(not any(o.name.startswith(p) for p in ('Cube', 'Sphere', 'Cylinder', 'Cone', 'Plane', 'Torus', 'Circle', 'Icosphere')) for o in meshes) :: No mesh has a default name
hint: F2 over the viewport renames the active object. Do it for each piece.
:::

:::task id=tidy title="One root, one collection" xp=20
Make an **Empty** (Shift+A > Empty > Plain Axes) called **Totem_Root** at the bottom of the pole. Parent
every piece to it, and move the lot into a collection called **Totem**.
check: any(o.type == 'EMPTY' and o.name == 'Totem_Root' for o in objects) :: There is an Empty called Totem_Root
check: all(o.parent == 'Totem_Root' for o in meshes) :: Every mesh is parented to Totem_Root
check: any(c.name == 'Totem' for c in cols) :: A collection named Totem exists
hint: Select all the pieces, then the Empty last, then Ctrl+P > Object. The Empty is the parent.
hint: Select the Empty and all pieces and press M to move them into a new collection called Totem.
:::

:::task id=save title="Save it" xp=5 untested
Ctrl+S. Pick a sensible filename like `totem.blend`.
check: file.saved and not file.dirty :: The file is saved, with no unsaved changes
hint: Ctrl+S. If it asks for a name, give it one.
:::

:::task id=color optional title="Stretch: four different colours" xp=20
Give the pieces at least four different materials. We cover materials properly in a later world, so for
now just add a few and change their **Base Color** under the Material tab.
check: len({m for o in meshes for m in o.mats if m}) >= 4 :: Four or more different materials in use
hint: Properties > Material tab > New, then click the Base Color swatch.
:::

:::note tip title="Test it by moving it"
Click Totem_Root and press [[G]]. If the whole pole comes with it, the parenting works. Press
[[Esc]] to cancel.
:::

:::solve
sc = bpy.context.scene
col = bpy.data.collections.new('Totem')
sc.collection.children.link(col)
root = bpy.data.objects.new('Totem_Root', None)
col.objects.link(root)
old = bpy.data.objects.get('Cube')
if old:
    bpy.data.objects.remove(old, do_unlink=True)
specs = [
    ('Base_Block', 'box', (1.6, 1.6, 1.6)), ('Frog_Body', 'sphere', 0.8), ('Wing_Slab', 'box', (2.4, 0.5, 0.5)),
    ('Eagle_Column', 'cyl', (0.55, 1.4)), ('Hat_Cone', 'cone', (0.7, 1.1)),
]
z = 0.0
for i, (name, kind, dim) in enumerate(specs):
    bm = bmesh.new()
    if kind == 'box':
        kit.add_box(bm, dim); h = dim[2]
    elif kind == 'sphere':
        kit.add_sphere(bm, dim, 16, 10); h = dim * 2
    elif kind == 'cyl':
        kit.add_cylinder(bm, dim[0], dim[1], 16); h = dim[1]
    else:
        kit.add_cylinder(bm, dim[0], dim[1], 16, radius2=0.0); h = dim[1]
    ob = kit.mesh_object(name, bm, collection=col, loc=(0, 0, z + h / 2))
    ob.parent = root
    ob.data.materials.append(kit.pbr('Paint_%d' % i, [(0.8, 0.2, 0.1, 1), (0.1, 0.5, 0.8, 1), (0.9, 0.8, 0.2, 1), (0.2, 0.7, 0.3, 1), (0.6, 0.2, 0.7, 1)][i]))
    z += h
bpy.ops.wm.save_as_mainfile(filepath=bpy.app.tempdir + 'totem.blend')
:::
