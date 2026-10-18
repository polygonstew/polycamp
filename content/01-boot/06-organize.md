---
id: organize
title: Names, Collections, Parents
summary: Three habits that decide whether a scene is still usable at object number 200.
minutes: 12
scene: fresh
keys: M, Ctrl+P, F2, Shift+A
tags: object mode, organization
xp: 35
---
Everyone starts out with a scene called `Cube.001`, `Cube.002`, `Sphere.004`. It is fine until it is not.
The week you want to hide "the left window" and you cannot find it, you will think of this lesson.

Three habits fix it before it starts.

1. **Name things.** [[F2]] renames the active object. Use words: `Door`, `Lantern_Glass`, `Roof_Left`.
2. **Group things.** Collections are folders for objects. Hide a whole collection with the eye icon.
3. **Parent things.** A child follows its parent. Move the parent and the whole assembly comes with it.

## Add some objects

Press [[Shift+A]] over the viewport. The **Mesh** submenu holds the primitives: plane, cube, circle, UV
sphere, icosphere, cylinder, cone, torus. Each one pops up a small **Adjust Last Operation** panel in the
bottom-left corner of the viewport where you can change size, segments and rotation. That panel
disappears the moment you do something else, so use it right away.

:::task id=add title="Add a sphere and a cone" xp=8
Add a **UV Sphere** and a **Cone**. You should now have at least three mesh objects (the original cube
included).
check: len(meshes) >= 3 :: Three or more meshes exist
check: any(o.verts >= 400 for o in meshes) :: One of them is a UV sphere
hint: Shift+A > Mesh > UV Sphere, then Shift+A > Mesh > Cone.
hint: The default UV sphere has 32 segments and 16 rings, 482 vertices. The cone has 33.
:::

## Name them

:::task id=names title="Give them real names" xp=8
Rename the three meshes to **Body**, **Head** and **Hat** (any one of them to any name). Select an object
and press [[F2]], or double-click it in the Outliner.
check: all(o.name in ('Body', 'Head', 'Hat') for o in meshes) :: Every mesh is called Body, Head or Hat
hint: Select, F2, type, Enter. Do it three times.
:::

## Collections

Everything in a scene lives in a collection. New objects go into the *active* collection, which is the
highlighted one in the Outliner. Press [[M]] over the viewport to **move the selection to a collection**,
including a brand new one.

:::task id=coll title="Make a collection called Mascot" xp=10
Select all three meshes ([[A]]), press [[M]], choose **+ New Collection**, and name it **Mascot**.
check: any(c.name == 'Mascot' and c.objects >= 3 for c in cols) :: A collection named Mascot holds the three meshes
hint: M opens a menu of collections. The first entry creates a new one and asks for its name.
hint: You can also right-click in the Outliner > New Collection and drag objects into it.
:::

## Parenting

Select the child first, then ctrl-click the parent last so it becomes active, then press [[Ctrl+P]] >
**Object**. The relationship shows in the Outliner as a nested tree.

:::task id=parent title="Parent the Head and Hat to the Body" xp=12
Parent **Head** to **Body**, then parent **Hat** to **Head**. Move the Body and make sure they all come
along. Finish by moving it back or pressing [[Ctrl+Z]].
check: any(o.name == 'Head' and o.parent == 'Body' for o in objects) :: Head is parented to Body
check: any(o.name == 'Hat' and o.parent == 'Head' for o in objects) :: Hat is parented to Head
hint: Click Head, Ctrl+click Body (so Body is active, drawn lighter), Ctrl+P, Object.
hint: Parenting order trips everyone: the active object, selected last, is always the parent.
:::

:::note tip title="Hide, don't delete"
The eye icon hides an object in the viewport. The camera icon hides it from the render. The arrow icon
disables it for selection. Three different switches, three different uses.
:::

:::quiz id=q1 xp=5
To parent object A to object B, which should be the active (last selected) object?
- A, the child
- *B, the parent
- It does not matter
explain: The active object is the parent. Select the children first, then the parent last.
:::

:::solve
sc = bpy.context.scene
col = kit.get_collection('Mascot') if hasattr(kit, 'get_collection') else bpy.data.collections.new('Mascot')
if col.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(col)
cube = bpy.data.objects['Cube']
cube.name = 'Body'
bm = bmesh.new(); kit.add_sphere(bm, 0.7, 32, 16)
head = kit.mesh_object('Head', bm, loc=(0, 0, 2.2))
bm = bmesh.new(); kit.add_cylinder(bm, 0.5, 0.8, 32, radius2=0.0)
hat = kit.mesh_object('Hat', bm, loc=(0, 0, 3.2))
for ob in (cube, head, hat):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
head.parent = cube
hat.parent = head
:::
