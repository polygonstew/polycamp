---
id: instances
title: Duplicates, Linked Copies and Instances
summary: Make twenty fence posts without making twenty of anything.
minutes: 12
scene: starter:fence-start
keys: Shift+D, Alt+D, Shift+A
tags: organization, efficiency
xp: 40
---
Scenes repeat things. Fence posts, windows, trees, bricks, books on a shelf. Blender has three levels of "copy"
and picking the right one decides whether you can fix a mistake in one place or in forty.

| Copy | Keys | What it shares with the original |
| --- | --- | --- |
| Duplicate | [[Shift+D]] | nothing: a separate mesh. Edit one and the others stay the same |
| Linked duplicate | [[Alt+D]] | the **mesh data**. Edit the shape of one and all copies change |
| Collection instance | Add > Collection Instance | an entire **collection**. Edit the collection and every instance follows |

Linked duplicates are cheap on memory too: a hundred linked posts use one mesh. That matters on a machine
with limited RAM.

## Linked duplicates

The starter has a post with a Bevel modifier and a rail. Select the post and press [[Alt+D]], then move the copy
along X. Both posts share one mesh called `Post`. Tab into Edit Mode on one, stretch it taller, and the other
grows too.

:::task id=linked title="Two linked posts" xp=12
Make at least two more posts as **linked duplicates** ([[Alt+D]]). All of them should use the same mesh data.
check: sum(1 for o in meshes if o.name.startswith('Post')) >= 3 :: Three or more posts
check: len({o.data for o in meshes if o.name.startswith('Post')}) == 1 :: They all share one mesh
hint: Select the post, Alt+D, then click to drop it. Do not use Shift+D: that makes independent copies.
hint: In the Outliner, linked copies show the same green mesh data name when you expand them.
:::
:::solve task=linked
post = bpy.data.objects['Post']
for i in (1, 2):
    dup = post.copy()                     # object.copy() shares the mesh data, just like Alt+D
    dup.name = 'Post.%03d' % i
    dup.location = (post.location.x + 1.5 * i, 0, 0)
    for m in post.modifiers:
        pass
    post.users_collection[0].objects.link(dup)
:::

## Arrays, again

For a long straight row an **Array** modifier is tidier than hand-placed copies. Remember Constant Offset gives
exact spacing. On the rail try Count 6 with **Constant Offset X = 1.5**.

:::task id=array title="A rail that repeats" xp=10
Add an **Array** modifier to the **Rail** with **Count 6** and a **Constant Offset** of **1.5 m** on X (turn Relative
Offset off).
check: any(o.name == 'Rail' and any(m.type == 'ARRAY' and m.p.count >= 6 and m.p.use_constant_offset for m in o.mods) for o in meshes) :: Rail has an Array of 6 with Constant Offset
hint: In the Array panel untick Relative Offset, tick Constant Offset and type 1.5 in its X field.
:::
:::solve task=array
rail = bpy.data.objects['Rail']
m = rail.modifiers.new('Array', 'ARRAY')
m.count = 6
m.use_relative_offset = False
m.use_constant_offset = True
m.constant_offset_displace = (1.5, 0, 0)
:::

## Collection instances

What if the thing you are repeating is made of many objects: a lantern (frame, glass, flame...), a tree
(trunk, tiers)? Put the parts in a collection and use **Add > Collection Instance > (name)**. You get an
Empty that displays the whole collection. Move, rotate and scale the Empty, and the entire assembly follows.
Edit the collection's contents and every instance updates.

:::task id=inst title="Instance a collection three times" xp=12
Make a collection called **FencePiece** that holds the post and the rail (move them in with [[M]]), then add **three
Collection Instances** of it (Shift+A > Collection Instance > FencePiece), placed at different positions.
check: sum(1 for o in objects if o.instance == 'COLLECTION') >= 3 :: Three or more collection instances
check: any(c.name == 'FencePiece' for c in cols) :: A collection named FencePiece exists
hint: M > New Collection > FencePiece moves the selected objects. Then Add menu > Collection Instance.
hint: The original collection is still visible in the scene. Exclude it (uncheck it in the Outliner) so you only see the instances.
:::
:::solve task=inst
sc = bpy.context.scene
col = bpy.data.collections.new('FencePiece')
sc.collection.children.link(col)
for name in ('Post', 'Rail'):
    ob = bpy.data.objects[name]
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
for i in range(3):
    e = bpy.data.objects.new('FenceInst.%02d' % i, None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = col
    e.location = (i * 2.0, 2.0, 0)
    sc.collection.objects.link(e)
:::

:::note cpu title="Why this matters on a CPU box"
Instances and linked copies keep memory down and make Cycles render faster to start (it only builds the shared
geometry once). A forest of instanced trees is much cheaper than a forest of unique ones.
:::

:::match id=m1 xp=6
Pick the copy that fits.
Forty identical bricks, one mesh => Linked duplicate (Alt+D)
A lantern made of six objects, placed in several spots => Collection Instance
A tree you want to reshape individually => Duplicate (Shift+D)
A long run of evenly spaced posts => Array modifier
:::

:::quiz id=q1 xp=5
You stretch one linked duplicate in Edit Mode and all its twins stretch as well. Why?
- Blender is confused
- *They share one mesh data block
- Linked duplicates are always parented
explain: Alt+D copies the object but keeps pointing at the same mesh. Shape edits go to the mesh, so every user of that mesh changes.
:::
