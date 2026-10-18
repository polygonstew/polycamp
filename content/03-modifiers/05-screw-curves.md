---
id: screw-curves
title: Spin a Profile, Bevel a Curve
summary: Turn a line into a vase with Screw, and a curve into a rope or pipe.
minutes: 12
scene: starter:profile-lathe
keys: Shift+A
tags: modifiers, curves
xp: 40
---
Some shapes are easier to *describe* than to build. A vase is a silhouette spun around an axis. A rope is a
path with thickness. This lesson covers the two modifiers (and one curve setting) that handle those.

## Screw: the lathe

Look at the starter. A thin line of vertices and edges, drawn in profile, hangs in space: half the outline of
a vase. The **Screw** modifier rotates that line around an axis and builds faces as it goes. With a full 360°
turn it is a lathe, exactly what a potter or a machinist does.

Settings:

- **Angle**: 360° for a full turn.
- **Steps**: how many segments around. 16 looks polygonal, 32 is fine for the viewport, 48 or more for a
  render.
- **Axis**: Z for something standing upright.
- **Merge**: welds the first and last ring so the seam closes. Turn it on.
- If the surface looks inside-out, tick **Flip** under Normals.

The profile has to be **on the correct side of the axis**. If the line drifts across the axis, the shape
folds in on itself.

:::task id=lathe title="Spin the vase" xp=14
Select **Profile** and add a **Screw** modifier. Set **Steps** to **32**, keep the angle at 360° around Z and
turn on **Merge**. A vase appears.
check: any(o.name == 'Profile' and any(m.type == 'SCREW' and m.p.steps >= 32 and m.p.use_merge_vertices and m.p.angle >= 6.2 for m in o.mods) for o in meshes) :: Profile has a 360° Screw with 32+ steps and Merge on
hint: Add Modifier > Generate > Screw. Angle already says 360°. The Steps field is the one that says 16.
hint: Merge is a checkbox near the bottom of the modifier panel.
:::
:::solve task=lathe
ob = bpy.data.objects['Profile']
m = ob.modifiers.new('Screw', 'SCREW')
m.angle = math.radians(360)
m.steps = 32
m.render_steps = 48
m.axis = 'Z'
m.use_merge_vertices = True
for p in ob.data.polygons:
    p.use_smooth = True
:::

Edit the profile in Edit Mode and the vase reshapes live. Try pinching the neck. This is a nice workflow for
bottles, wine glasses, chess pieces, lamp bases, columns and the cap of a lantern.

## Curves with thickness

A **curve** object is a mathematical path, not a mesh. **Shift+A > Curve > Bezier** makes one. Pull its
handles in Edit Mode to bend it. By itself it renders as nothing, because a path has no width.

Open its **Object Data** tab (the curve icon) > **Geometry > Bevel** and set **Depth** to something like 0.03.
The curve now has a round cross-section: a pipe, a rope, a wire, a vine, a chain link.

Other settings in the same panel: **Resolution** (smoothness of the round section), **Fill Caps** to close
the ends, **Extrude** (flat ribbon) and **Taper Object** to make it thinner at one end.

:::task id=rope title="A rope from a curve" xp=14
Add a **Bezier** curve (Shift+A > Curve > Bezier). In its **Object Data** tab set **Bevel > Depth** to at
least **0.02**. It should appear as a thick pipe.
check: any(o.type == 'CURVE' and o.curve.bevel_depth >= 0.02 for o in objects) :: A curve with a bevel depth of 0.02 or more
hint: Shift+A > Curve > Bezier. The green curve-shaped icon in Properties is Object Data. Open the Geometry panel, then Bevel.
hint: In Blender 3.3 the panel is called Geometry > Bevel. In newer versions it is the same. Choose Round if you see a mode choice.
:::
:::solve task=rope
cd = bpy.data.curves.new('Rope', 'CURVE')
cd.dimensions = '3D'
sp = cd.splines.new('BEZIER')
sp.bezier_points.add(2)
pts = [(-1.5, 0, 0.2), (0, 0, 1.2), (1.5, 0, 0.2)]
for bp, co in zip(sp.bezier_points, pts):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = 'AUTO'
cd.bevel_depth = 0.04
cd.bevel_resolution = 4
ob = bpy.data.objects.new('Rope', cd)
bpy.context.scene.collection.objects.link(ob)
:::

:::note tip title="Chains, cables, handles"
A Bezier curve with bevel depth is how you make the ring on top of a lantern, the cable between two poles,
and a mug handle if the Euler characteristic ever frightens you. **Convert** it to a mesh (Object > Convert >
Mesh) when you need to edit faces.
:::

:::quiz id=q1 xp=5
Your Screw result looks inside-out (dark and weirdly shaded). Which fix is the fastest?
- Increase Steps
- *Tick Flip under Normals, or reverse the profile direction
- Apply the modifier and delete everything
explain: The faces are being built facing inward. Flip tells Screw to build them the other way around.
:::

:::quiz id=q2 xp=5
A new Bezier curve renders as nothing. Why?
- Curves cannot be rendered
- *It has no thickness yet: set Bevel Depth under Geometry
- It needs a material first
explain: A curve is an infinitely thin path until you give it a bevel depth or an extrude amount.
:::
