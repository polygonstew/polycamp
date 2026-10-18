---
id: pipeline
title: Clean Files, Safe Files
summary: Names, collections, orphans, backups and versions: what keeps a project alive.
minutes: 12
scene: starter:messy-file
keys: M, F2
tags: pipeline, organization
xp: 40
---
Real projects last weeks or months. The difference between a project you can still open in month three and one you abandon is mostly habits, not talent. This lesson works on a deliberately messy file: eight objects with default names in one pile, and
five unused materials left behind by experiments.

## Habit 1: names

You will name things in the order you wish you had at the start.

- **Objects**: `Cabin_Walls`, `Lantern_Glass`, `Rock.03`. Words, not shapes. Use `_` or `.` and a number for variants.
- **Materials**: by what they are, not by colour. `Wood_Planks`, not `Brown`.
- **Collections**: by role: `Cabin`, `Lights`, `Props`.
- **Meshes** share the object's name by default. In the Outliner's *Blender File* view you can rename them too.

:::task id=names title="Rename the eight objects" xp=10
No mesh may keep a default name (Cube, Sphere, Cylinder, Cone, Torus, with or without numbers).
check: len(meshes) >= 8 and all(not any(o.name.startswith(p) for p in ('Cube', 'Sphere', 'Cylinder', 'Cone', 'Torus')) for o in meshes) :: Eight meshes, none with a default name
hint: Double-click a name in the Outliner, or select and press F2. Pick names that describe the object's job.
hint: Batch rename: select several, Ctrl+F2 opens the Batch Rename tool.
:::
:::solve task=names
for i, ob in enumerate([o for o in bpy.data.objects if o.type == 'MESH']):
    ob.name = 'Prop_%02d' % (i + 1)
:::

## Habit 2: collections

Collections are folders. Put things that belong together in one, and you can hide, exclude from the render or lock a whole group. Typical layout: one for each location or system (`Cabin`, `Terrain`, `Lights`, `Cameras`, `Props`, `Helpers`).

:::task id=coll title="Three collections" xp=10
Make at least **three collections** and move the objects into them: one for the cubes, one for the round things, one for the lights and camera.
check: len(cols) >= 3 :: Three or more collections
hint: Select objects, press M, choose New Collection. Repeat for each group.
:::
:::solve task=coll
sc = bpy.context.scene
groups = {'Boxes': lambda o: o.type == 'MESH' and o.dimensions.x == o.dimensions.y == 1.0, 'Rounds': lambda o: o.type == 'MESH', 'Stage': lambda o: True}
made = {}
for gname, test in groups.items():
    col = bpy.data.collections.new(gname)
    sc.collection.children.link(col)
    made[gname] = col
for ob in list(sc.objects):
    key = next(k for k, t in groups.items() if t(ob))
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    made[key].objects.link(ob)
:::

## Habit 3: purge the orphans

When nothing uses a material, image or mesh, it becomes an **orphan** (zero users). It stays in the session, and Blender throws it away when you save and reopen, unless it has a **fake user**. Orphans clutter menus and
waste memory. Clean up with **File > Clean Up > Purge Unused Data**.

In the Outliner switch the display mode to **Blender File** (or **Orphan Data**) to see them, and click the shield icon to give an item a fake user, if you really want to keep it.

:::task id=purge title="Purge the unused materials" xp=12
Remove every material that has no users. (Outliner > Orphan Data, or File > Clean Up > Purge Unused Data.)
check: len(materials) >= 1 and all(m.users > 0 for m in materials) :: Every remaining material is in use
hint: File menu > Clean Up > Purge Unused Data, and confirm. In 4.2 and newer it is Purge Unused Data… with a preview dialog.
hint: If it does nothing, switch the Outliner to Orphan Data to check they are truly unused.
:::
:::solve task=purge
for m in list(bpy.data.materials):
    if m.users == 0:
        bpy.data.materials.remove(m)
:::

## Habit 4: do not lose it

- **Save often**, and **Save Versions** (Preferences > Save & Load > *Save Versions*: 2 to 5) keeps `project.blend1`, `.blend2`: the previous saves. They have rescued more projects than any other feature.
- **Auto Save** you set in World 1.
- **Incremental names**: `cabin_v01.blend`, `cabin_v02.blend` before risky changes. [[Ctrl+Shift+S]] > Save As, then a `+` in the file browser increments a trailing number.
- **Relative paths** (File > External Data > Make Paths Relative): so moving the project folder does not break textures.
- **Pack or keep** textures next to the .blend. A texture on the Desktop that you later delete shows up as a pink surface.
- **Back up** the folder. An actual copy somewhere else, on a different drive.

:::task id=backup title="Check your save settings" xp=8 manual
Open **Edit > Preferences > Save & Load**. Set **Save Versions** to 3 or more. Claim this when you have done it.
hint: The field is under the File Paths and Save & Load sections. Preferences save by themselves if Auto-Save Preferences is on.
:::

:::note tip title="One file, one scene, one purpose"
When a single .blend gets big and slow, split it. Model assets in their own files, and **link** (File > Link) them into the scene file. Edit the asset file and every scene that links it updates. It is how studios keep
massive scenes manageable, and it works fine for a hobbyist with a 10 GB scene too.
:::

:::quiz id=q1 xp=5
A material has zero users and no fake user. What happens to it when you save and reopen the file?
- It is kept forever
- *It is discarded
- It is turned into a texture
explain: Blender drops unused data on save/reload. Give it a fake user (the shield icon) if you want to keep it around.
:::
