---
id: soft-things
title: Soft Things: Proportional Editing and Smooth Shading
summary: Pull a hill out of a flat grid and make faceted meshes look round.
minutes: 12
scene: starter:hill-grid
keys: O, Z
tags: edit mode, shading
xp: 40
---
Two ideas in this lesson, both about making things look less like they came out of a calculator.

## Proportional editing

Normally, moving one vertex moves exactly one vertex. Turn on **Proportional Editing** (press [[O]], or
click the circle-with-dot icon in the header) and nearby vertices follow along with a falloff. Move one
point and you pull a *hill* instead of a spike.

While you are moving something with proportional editing on:

- **Scroll the mouse wheel** to grow or shrink the influence circle.
- The falloff curve (smooth, sphere, root, sharp, linear, constant, random) is a drop-down in the header.
  *Smooth* is a good default. *Sharp* pulls a peak. *Constant* acts like a hard-edged selection.
- Switch **Connected Only** on when you only want to move mesh that is actually joined, not things that
  happen to be close.

The starter is a flat 24 × 24 grid. Make it into a hill.

:::task id=hill title="Pull a hill at least 1 m high" xp=14
Tab into Edit Mode with proportional editing on. Select a single vertex near the middle of the grid and
lift it with [[G]] [[Z]] `1.5`. While you drag, scroll to make the influence circle roughly 2 m wide.
check: any(o.dims[2] >= 1.0 and o.verts >= 400 for o in meshes) :: A grid with 400+ vertices that is at least 1 m tall
hint: Press O to switch on proportional editing, click a vertex in the centre, then G Z 1.5. Scroll the wheel while moving to change the radius.
hint: Nothing happens to the neighbours? The proportional icon in the header must be highlighted.
:::
:::solve task=hill
me = bpy.context.object.data
bm = bmesh.new()
bm.from_mesh(me)
for v in bm.verts:
    d = (v.co.x ** 2 + v.co.y ** 2) ** 0.5
    v.co.z += 1.5 * math.exp(-(d / 1.6) ** 2)
bm.to_mesh(me)
bm.free()
:::

## Smooth and flat shading

Every face of a mesh is flat. A sphere built from 500 flat faces still looks faceted, because each face is
shaded with its own normal. **Shade Smooth** blends the normals across shared edges so the surface looks
curved while the geometry stays the same. (Fewer faces, rounder look: that is the entire economy of real
time graphics.)

Right-click in Object Mode and choose **Shade Smooth**, or use the **Object** menu. **Shade Flat**
goes back.

:::task id=smooth title="Shade the hill smooth" xp=10
Switch to Object Mode, select the hill, and choose **Object > Shade Smooth**. The grid's blocky terraces
disappear.
check: any(o.faces > 100 and o.smooth_faces == o.faces for o in meshes) :: Every face of the hill is smooth-shaded
hint: Object Mode (Tab), right-click > Shade Smooth.
hint: In Edit Mode there is Face > Shade Smooth, which only affects the selected faces.
:::
:::solve task=smooth
for p in bpy.data.objects['Hill'].data.polygons:
    p.use_smooth = True
:::

Smooth shading has a drawback: it rounds *everything*, including the corners that should be sharp, which
makes a box look pillowy. The answer is to smooth the surfaces but keep the sharp creases.

:::v 3
**Blender 3.3:** select the object, open Properties > **Object Data** (green triangle) > **Normals** and tick
**Auto Smooth**. The **Angle** field decides which edges stay sharp: anything sharper than the angle is
left alone. 30° is a sensible start.
:::

:::v 4+
**Blender 4.1 and newer:** Auto Smooth was removed from the Object Data panel. Use **Object > Shade Auto
Smooth** (4.1) or **Object > Shade Smooth by Angle** (4.2 and newer). It marks sharp edges based on the
angle you choose and leaves the rest smooth. For something you can adjust later, add the **Smooth by
Angle** modifier from the Add Modifier menu (Normals section).
:::

:::note tip title="A flat shaded box that you subdivide"
If you plan to use a Subdivision Surface modifier, you do not need Shade Smooth for roundness: the
modifier makes real geometry. You still turn on smooth shading to hide the facets on the subdivided result.
:::

:::quiz id=q1 xp=5
Shade Smooth changes what about the mesh?
- It adds more faces so the surface is rounder
- *Only how light is calculated across edges; the geometry is identical
- It removes sharp edges permanently
explain: Smooth shading only blends normals. The silhouette is still made of the same flat faces, which you can see at the edge of a smooth-shaded sphere.
:::

:::keys id=k1 xp=8
Toggle proportional editing | O
Shading pie menu | Z
Grab | G
Extrude | E
:::
