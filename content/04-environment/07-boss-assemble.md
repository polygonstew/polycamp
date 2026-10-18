---
id: boss-assemble
title: Boss: Build the Place
summary: Everything exists but is standing in a line. Arrange it into the diorama.
minutes: 20
scene: starter:lineup
boss: true
keys: G, R, S, M, Shift+A
tags: boss, composition
xp: 120
---
:::cubby shock
All the pieces are here: cabin, lamp post, rocks and trees. They are lined up on the left like suspects.
Your job is to place them so the scene feels like a place somebody could live.
:::

## Brief

The starter scene has a round ground slab 9 m across (centre at the origin), a cabin, a lamp post with a lantern, six rocks and
five pines, all standing in a row off to the side. Move them onto the ground.

What a good diorama does:

- **One focal point.** The cabin sits near the middle. Everything else points the eye toward it.
- **Odd numbers, uneven spacing.** Trees in a cluster and a loner. Rocks of different sizes, mostly near the
  edge, one or two near the path.
- **A reason for the lantern.** It stands by the door. The door faces the camera side (−Y).
- **Nothing floating, nothing buried.** Every part sits on the ground surface.

:::goal img=diorama-blockout.png
A suggested arrangement in plain grey. Yours can differ as long as it holds together.
:::

:::task id=cabin title="The cabin on the ground" xp=15
Move the **Cabin** (the Empty that owns the whole building) so it sits near the centre of the slab: within 1.2 m
of the origin on X and Y.
check: any(o.name == 'Cabin' and abs(o.world_loc[0]) <= 1.2 and abs(o.world_loc[1]) <= 1.2 for o in objects) :: Cabin is near the centre of the ground
hint: Click the Cabin in the Outliner (it is an Empty with children), then G or type exact values in the N panel.
hint: Moving the Empty moves every cabin part with it, because they are parented.
:::
:::solve task=cabin
bpy.data.objects['Cabin'].location = (0, 0.3, 0)
:::

:::task id=lantern title="The lantern by the door" xp=15
Put the **lamp post and its lantern (PostLantern)** within 3.5 m of the cabin, and on the door side (lower Y than
the cabin's centre).
check: any(((l.world_loc[0] - c.world_loc[0]) ** 2 + (l.world_loc[1] - c.world_loc[1]) ** 2) ** 0.5 <= 3.5 and l.world_loc[1] < c.world_loc[1] for l in objects if l.name == 'PostLantern' for c in objects if c.name == 'Cabin') :: The lantern is within 3.5 m of the cabin and in front of it
hint: There are two objects to move: Lamp_Post and PostLantern. Select both and move them together with G.
hint: The lamp post's Z is already right. Only move it on X and Y.
:::
:::solve task=lantern
bpy.data.objects['Lamp_Post'].location = (1.15, -2.15, bpy.data.objects['Lamp_Post'].location.z)
bpy.data.objects['PostLantern'].location = (0.49, -2.15, 1.74)
:::

:::task id=trees title="Pines around the edge" xp=15
At least three pines stand on the ground between 2.4 and 4.3 m from the centre.
check: sum(1 for o in meshes if o.name.startswith('Pine') and 2.4 <= (o.world_loc[0] ** 2 + o.world_loc[1] ** 2) ** 0.5 <= 4.3) >= 3 :: Three or more pines between 2.4 and 4.3 m from the centre
hint: Select a pine, G, drag it to the edge of the ground disc. Aim for clusters, not a ring.
:::
:::solve task=trees
spots = {'Pine.00': (-3.1, 1.7), 'Pine.01': (-2.2, 3.0), 'Pine.02': (3.0, 2.3), 'Pine.03': (3.8, 0.5), 'Pine.04': (0.2, 3.6)}
for n, (x, y) in spots.items():
    bpy.data.objects[n].location = (x, y, bpy.data.objects[n].location.z)
:::

:::task id=rocks title="Rocks that belong" xp=15
At least three rocks sit on the ground within 4.4 m of the centre, and no two of them occupy the same spot.
check: sum(1 for o in meshes if o.name.startswith('Rock') and (o.world_loc[0] ** 2 + o.world_loc[1] ** 2) ** 0.5 <= 4.4) >= 3 :: Three or more rocks on the ground
check: len({(round(o.world_loc[0]), round(o.world_loc[1])) for o in meshes if o.name.startswith('Rock')}) >= 3 :: In at least three different places
hint: Rocks look best in odd groups: a pair and a single, not a row.
:::
:::solve task=rocks
spots = {'Rock.00': (-2.9, -1.6), 'Rock.01': (-3.3, -0.9), 'Rock.02': (2.9, -1.2), 'Rock.03': (3.2, 1.0), 'Rock.04': (-1.4, 3.1), 'Rock.05': (0.7, -3.3)}
for n, (x, y) in spots.items():
    bpy.data.objects[n].location = (x, y, bpy.data.objects[n].location.z)
:::

:::task id=camera title="A camera on the scene" xp=15
Add a **camera** and aim it at the cabin so the whole diorama is in view. Make it the active scene camera
(Numpad 0 shows what it sees).
check: len(cams) >= 1 and scene.camera != None :: A scene camera exists
hint: Shift+A > Camera. Then Ctrl+Alt+Numpad 0 snaps the camera to your current viewport angle, handy for framing.
hint: Place it about 10 m away, 4 m up, looking down slightly at the cabin. A focal length near 36 mm suits a diorama.
:::
:::solve task=camera
kit.add_camera('Camera', (8.4, -10.6, 4.1), (0.2, 0.0, 1.45), 36.0)
:::

:::task id=save title="Save the blockout" xp=10 untested
Save the file as `diorama-blockout.blend`.
check: file.saved and not file.dirty :: The file is saved with no unsaved changes
hint: Ctrl+S, then give it a name.
:::

:::note tip title="Squint test"
Squint at the viewport until the details blur. Can you still tell where the cabin is? If the biggest shape
is in the right place and the second biggest balances it, you are done. If it all looks like one grey smudge,
re-spread the trees.
:::

:::note cpu title="Save it, then breathe"
Save the file as `diorama-blockout.blend`. This is your first complete scene, and the next worlds add materials,
textures, light, animation and the final render to it.
:::
