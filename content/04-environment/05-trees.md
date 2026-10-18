---
id: trees
title: Low-Poly Pines
summary: A forest from one tree: build it from cones, then instance it with variety.
minutes: 12
scene: empty
keys: Shift+A, Shift+D, S, R
tags: organic, instances
xp: 40
---
A pine tree is stacked cones on a stick. That is not an insult: stylised, low-poly trees are cheap to render,
read perfectly well at a distance, and hold up in a diorama where everything shares the same chunky style.
They are also a gentle lesson in making variety out of one asset.

## One pine

Build it from four parts, all inside a collection called **Pine**:

- **Trunk**: a cylinder, 8 vertices, radius 0.11, height 0.9.
- **Three or four tiers**: **cones** with 9 vertices, each smaller than the one below, overlapping so no
  gaps show. Radius 1.0, 0.8, 0.6, 0.4 for a 2.8 m tree, and each about 1 m tall.
- Stagger them: each tier starts 0.55 m above the last, and rotate each a little around Z so the points do not line
  up like a stack of hats.

Give each part a clear name: `Pine_Trunk`, `Pine_Tier1`, `Pine_Tier2`...

:::task id=build title="Build the pine in a Pine collection" xp=16
Make a pine from a trunk and at least **three tiers** (cones). Keep all the parts inside a collection called **Pine**.
Together they should stand between 2 and 4 m tall.
check: any(c.name == 'Pine' and c.objects >= 4 for c in cols) :: A collection Pine with four or more objects
check: max(o.wbox[5] for o in meshes if 'Pine' in o.collections) - min(o.wbox[2] for o in meshes if 'Pine' in o.collections) >= 2 :: At least 2 m tall
check: max(o.wbox[5] for o in meshes if 'Pine' in o.collections) - min(o.wbox[2] for o in meshes if 'Pine' in o.collections) <= 4 :: At most 4 m tall
hint: Shift+A > Mesh > Cone. In Adjust Last Operation set Vertices 9, Radius 1, Depth 1. Move it up, duplicate, scale down.
hint: Put the finished parts in a collection: select them all, M, New Collection, name it Pine.
:::
:::solve task=build
col = get_collection('Pine')
for name, r, d, z in (('Pine_Trunk', 0.11, 0.9, 0.45), ('Pine_Tier1', 1.0, 1.0, 1.1), ('Pine_Tier2', 0.8, 1.0, 1.65), ('Pine_Tier3', 0.6, 1.0, 2.2), ('Pine_Tier4', 0.4, 1.0, 2.75)):
    bm = bmesh.new()
    kit.add_cylinder(bm, r, d, 9 if 'Tier' in name else 8, radius2=0.0 if 'Tier' in name else None)
    kit.mesh_object(name, bm, collection=col, loc=(0, 0, z))
:::

:::note tip title="Why low poly works"
Nine segments per cone and flat shading give crisp faceted foliage. Smooth shading would make it look like
green balloons. Choose a style and keep it consistent across the whole scene: that is what makes a scene
feel designed.
:::

## Make a forest, cheaply

Do not duplicate the parts. Hide the original collection (uncheck the box in the Outliner) and place **Collection
Instances** of **Pine** around the scene. Give each instance its own **rotation** around Z, and a scale
between 0.7 and 1.3. Four or five instances with different sizes and rotations already read as "different trees".

:::task id=forest title="Plant five pines with variety" xp=14
Add at least **five Collection Instances** of **Pine**. They should not all have the same scale: use at least three different
scales.
check: sum(1 for o in objects if o.instance == 'COLLECTION') >= 5 :: Five or more collection instances
check: len({round(o.scale[0], 1) for o in objects if o.instance == 'COLLECTION'}) >= 3 :: At least three different scales
hint: Shift+A > Collection Instance > Pine. Then S to scale and R Z to turn each one.
hint: Scales like 0.8, 1.0, 1.2 and so on are enough. A tiny random-looking tilt can help too but is not needed.
:::
:::solve task=forest
sc = bpy.context.scene
col = bpy.data.collections['Pine']
for i, (x, y, s) in enumerate(((3, 1, 1.0), (4, -1, 0.8), (-3, 2, 1.2), (-4, -2, 0.9), (0, 4, 1.1))):
    e = bpy.data.objects.new('PineInst.%02d' % i, None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = col
    e.location = (x, y, 0)
    e.scale = (s, s, s)
    e.rotation_euler[2] = i * 1.3
    sc.collection.objects.link(e)
:::

## Rule of three

Placing things in groups of **three** (or odd numbers) with different spacing looks more natural than lines or pairs.
Cluster a few trees, leave a gap, put one or two alone. Nature does not use a grid.

:::quiz id=q1 xp=5
Why instance the Pine collection instead of duplicating its parts?
- Instances render in higher quality
- *Instances share data, so memory stays low and one edit changes every tree
- Duplicates are not allowed in collections
explain: A collection instance is a lightweight reference. Fix the trunk once and every tree in the forest is fixed.
:::
