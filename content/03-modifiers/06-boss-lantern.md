---
id: boss-lantern
title: Boss: The Lantern
summary: Build the hero prop of the final scene: an iron lantern with glowing glass and a flame.
minutes: 30
scene: empty
boss: true
keys: Shift+A, Ctrl+A, Ctrl+P, M
tags: boss, hard surface
xp: 120
---
:::cubby shock
This is not a practice object. This lantern ends up hanging next to the cabin door in your final render,
glowing, so build it like you will be looking at it for a month.
:::

## Brief

The scene is empty. Build a **lantern** about 0.7 m tall: a metal frame, four corner posts, a pyramid cap, a ring on
top to hang it by, a glass box in the middle and a small flame inside. Details you choose are yours. The
checks look for craft, not for a specific shape.

A recipe if you want one:

1. **Frame:** a flat base plate and a slightly smaller block above it. Four thin posts ([[Shift+A]] cube, scale
   X and Y down, **apply scale**, duplicate with [[Shift+D]]). A thin plate on top.
2. **Cap:** a cone with only **4 vertices** (Shift+A > Cone, set Vertices to 4 in the Adjust Last Operation panel),
   rotated 45° so its corners face the posts. Tip radius small, but not zero.
3. **Ring:** a **Torus** (major radius 0.075, minor 0.01) standing up on the cap.
4. **Glass:** a box that fits between the posts.
5. **Flame:** an Icosphere inside, small. A **Subdivision Surface** modifier makes it round.
6. **Bevel modifiers** on the metal parts, Angle limit, width about 0.004.
7. Parent everything to an **Empty** named `Lantern`, and put the lot in a **collection** called `Lantern`.
8. **Materials:** dark metal for the frame (Metallic 1, Roughness about 0.4), and an **emissive** material for the
   glass and the flame. You will meet materials properly in a later world. For now: Material tab > New,
   scroll to **Emission**, set a warm colour and a **Strength** of 5 or more.
9. A **Point light** inside, warm, around 40 W.

:::goal img=lantern.png
The reference lantern, rendered in Cycles on a CPU. Yours can be fatter, thinner, taller or stranger.
:::

:::task id=parts title="A real assembly" xp=20
At least five mesh objects live in a collection called **Lantern**, parented under an Empty (the Empty has
four or more children).
check: any(c.name == 'Lantern' and c.objects >= 6 for c in cols) :: A collection named Lantern with six or more objects
check: any(o.type == 'EMPTY' and o.children >= 4 for o in objects) :: An Empty with at least four children
hint: Shift+A > Empty > Plain Axes. Select the parts, the Empty last, Ctrl+P > Object. Then M to move the group to a new collection called Lantern.
hint: The collection count includes the Empty itself, so five parts plus the Empty make six objects.
:::

:::task id=size title="Lantern sized" xp=15
From its lowest to its highest point the lantern spans between 0.5 and 0.95 m. Only the objects in the
Lantern collection count.
check: max(o.wbox[5] for o in meshes if 'Lantern' in o.collections) - min(o.wbox[2] for o in meshes if 'Lantern' in o.collections) >= 0.5 :: At least 0.5 m tall
check: max(o.wbox[5] for o in meshes if 'Lantern' in o.collections) - min(o.wbox[2] for o in meshes if 'Lantern' in o.collections) <= 0.95 :: At most 0.95 m tall
hint: Use the Dimensions in the sidebar (N) to judge each part. A frame about 0.3 wide and 0.45 high works.
hint: The default cube is 2 m: scale everything down, then apply scale with Ctrl+A.
:::

:::task id=mods title="Non-destructive craft" xp=20
At least two *different* modifier types are in use across the lantern (Bevel on the metal and Subdivision
Surface on the flame is the obvious pair), and a Bevel has an Angle limit with 2+ segments.
check: len({m.type for o in meshes if 'Lantern' in o.collections for m in o.mods}) >= 2 :: Two or more modifier types in use
check: any(m.type == 'BEVEL' and m.p.limit_method == 'ANGLE' and m.p.segments >= 2 for o in meshes if 'Lantern' in o.collections for m in o.mods) :: A Bevel with an Angle limit and 2+ segments
hint: Modifiers tab > Add Modifier > Generate > Bevel. Limit Method: Angle. Add Subdivision Surface to the flame.
:::

:::task id=glow title="It glows" xp=20
At least one material has **Emission Strength 2 or more**, and a **Point** light of 10 W or more sits in the scene.
check: any(m.emission_strength != None and m.emission_strength >= 2 for m in materials) :: A material emits light (strength 2 or more)
check: any(o.type == 'LIGHT' and o.light.kind == 'POINT' and o.light.energy >= 10 for o in objects) :: A Point light of 10 W or more
hint: Material tab > Surface > scroll to Emission. Put a warm colour in Color and 5 in Strength.
hint: Shift+A > Light > Point. Put it inside the glass and set Power to about 40 W in the Light tab.
:::

:::task id=budget title="Light on the polygons" xp=15
The entire lantern stays under 4,000 faces. Hard-surface props should be efficient, because the cabin
scene is going to hold plenty of other things.
check: sum(o.faces_eval for o in meshes if 'Lantern' in o.collections) <= 4000 :: Under 4,000 evaluated faces
check: sum(o.faces_eval for o in meshes if 'Lantern' in o.collections) >= 60 :: But not empty either
hint: Statistics (Overlays > Statistics) shows the face count. A cap of 4 sides and a torus of 24 by 8 is cheap.
:::

:::task id=named title="Named parts" xp=10
Every mesh in the lantern has a real name (no Cube, Cylinder, Cone, Sphere, Torus or Icosphere left).
check: len(meshes) >= 5 and all(not any(o.name.startswith(p) for p in ('Cube', 'Cylinder', 'Cone', 'Sphere', 'Torus', 'Icosphere', 'Plane', 'Circle')) for o in meshes) :: Five or more meshes, none with a default name
hint: F2 over the viewport renames the active object. Names such as Lantern_Frame, Lantern_Glass, Lantern_Cap.
:::

:::note tip title="Keep this file"
Save it as `lantern.blend` somewhere safe. Later worlds start from a ready-made lantern so nobody is stuck,
but yours is the one you will want in the final scene.
:::

:::solve
col = get_collection('Lantern')
parts = build_lantern((0, 0, 0), col, True, 1.0, 'Lantern')
kit.add_light('POINT', 'Lantern_Light', (0, 0, 0.25), 40, (1.0, 0.72, 0.4), size=0.06, collection=col)
:::
