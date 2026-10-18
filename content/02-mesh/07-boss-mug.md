---
id: boss-mug
title: Boss: The Mug
summary: A hollow mug with a handle, closed and smooth. Every tool from this world.
minutes: 25
scene: fresh
boss: true
keys: E, I, Ctrl+R, Alt+LMB, Ctrl+B
tags: boss, modeling
xp: 100
---
:::cubby shock
A mug. It is the traditional first thing, the one every modelling course reaches for, and there is a
reason. It needs a round body, a hollow, a handle and clean topology. Five things you already know, all
in one object.
:::

## Brief

Model a mug in a single mesh object called **Mug**. Treat 1 unit as about 10 cm, so the mug is a little under
a metre tall in Blender's world. It must be closed (watertight), really hollow, and have a real handle you
could put a finger through.

How you get there is up to you. A suggestion that works:

1. Start from a **cylinder** (Shift+A > Mesh > Cylinder), 32 vertices, radius 0.5, height 0.95.
2. Add a few **loop cuts** around the body so you have faces to attach a handle to later.
3. Select the top ngon, **inset** it ([[I]], about 0.07) and **extrude** it down ([[E]], about 0.8). That is
   the hollow.
4. On the side, delete one or two faces near the top and the same near the bottom, build the handle with
   **extrude** or an extruded curve, and **bridge** it back to the openings. Or build it as its own
   torus and join it with a boolean. Both are valid.
5. **Shade smooth**, and add a bevel for the lip if you are feeling clever.

:::goal img=mug.png
The finished mug in the reference render. Yours does not have to match, but the shape should read at a glance.
:::

:::task id=body title="A mesh called Mug, mug sized" xp=15
One mesh object is named **Mug**. It is between 0.8 and 1.4 tall, and its footprint (handle included) is
between 0.9 and 1.9 wide and 0.6 to 1.4 deep.
check: any(o.name == 'Mug' and 0.8 <= o.dims[2] <= 1.4 for o in meshes) :: An object named Mug that is 0.8 to 1.4 tall
check: any(o.name == 'Mug' and 0.9 <= o.dims[0] <= 1.9 and 0.6 <= o.dims[1] <= 1.4 for o in meshes) :: With a sensible footprint
hint: Rename with F2. Check Dimensions in the N panel. Remember to apply scale (Ctrl+A) if you stretched the object.
hint: The suggested cylinder is 1 unit across and 0.95 tall; with a handle it comes to about 1.5 wide.
:::

:::task id=closed title="Closed, no holes" xp=20
The mesh is watertight: no boundary edges, no loose edges, no edges shared by three or more faces.
check: any(o.name == 'Mug' and o.boundary_edges == 0 and o.loose_edges == 0 and o.nonmanifold_edges == 0 for o in meshes) :: Mug is a closed manifold mesh
hint: Select > Select All by Trait > Non Manifold shows you exactly where the problems are.
hint: Gaps usually come from a deleted face you forgot to bridge, or double vertices (M > By Distance).
:::

:::task id=hollow title="Actually hollow" xp=20
The inside is carved out: the enclosed volume is well under half of the bounding box volume.
check: any(o.name == 'Mug' and o.volume != None and o.volume < 0.45 * o.dims[0] * o.dims[1] * o.dims[2] for o in meshes) :: Mug's volume is less than 45% of its bounding box
check: any(o.name == 'Mug' and o.faces >= 100 for o in meshes) :: With at least 100 faces
hint: Inset the top face and extrude it down. Pushing the inner face down leaves a floor at the bottom of the cup.
hint: If the volume is still large, your handle is solid and your body hollow, but the bounding box includes the handle. Make the hollow deeper or the walls thinner.
:::

:::task id=handle title="It has a handle" xp=20
A handle is a loop of mesh you can put a finger through. In maths terms the surface has one hole, which the
Euler characteristic (vertices minus edges plus faces) shows: zero means one handle.
check: any(o.name == 'Mug' and o.verts - o.edges + o.faces == 0 for o in meshes) :: Vertices minus edges plus faces equals 0
hint: A solid cylinder gives 2, a cylinder with a dent gives 2 as well. Only a loop through the body, like a handle, brings it to 0.
hint: If the number is 2 you have no handle. If it is -2 or less you have a second loop somewhere.
:::

:::task id=finish title="Smooth finish" xp=10
Shade smooth so the rim and body look round instead of faceted.
check: any(o.name == 'Mug' and o.smooth_faces >= 0.9 * o.faces for o in meshes) :: At least 90% of the faces are smooth-shaded
hint: Object Mode, Object menu > Shade Smooth. A Bevel modifier on the lip is a nice extra.
:::

:::note tip title="Stuck on the handle?"
Handles break first-time modellers. Take it in small steps: delete two faces on the top, two on the
bottom; extrude each outward and curl them toward each other; select both end loops and **Bridge Edge
Loops**. If the bridge twists, undo and check both loops have the same number of edges.
:::

:::solve
# cup: a cylinder with loop cuts, inset and extruded down
bm = bmesh.new()
kit.add_cylinder(bm, 0.5, 0.95, 32, center=(0, 0, 0.475))
for k in range(1, 5):
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0.19 * k), plane_no=(0, 0, 1))
top = [f for f in bm.faces if f.normal.z > 0.99 and f.calc_center_median().z > 0.9]
bmesh.ops.inset_region(bm, faces=top, thickness=0.07, depth=0.0)
inner = [f for f in bm.faces if f.normal.z > 0.99 and f.calc_area() > 0.3 and f.calc_center_median().z > 0.9]
res = bmesh.ops.extrude_face_region(bm, geom=inner)
moved = [e for e in res['geom'] if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.translate(bm, vec=(0, 0, -0.8), verts=moved)
bmesh.ops.delete(bm, geom=inner, context='FACES')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
col = bpy.context.scene.collection.children['Collection']
mug = kit.mesh_object('Mug', bm, collection=col)
mug.data.materials.append(kit.pbr('Ceramic', (0.85, 0.35, 0.2, 1), roughness=0.25))
# handle: a torus, unioned with the body by a boolean, then applied
hb = bmesh.new()
add_torus(hb, 0.27, 0.055, 24, 10, (0, 0, 0), 'Y')
handle = kit.mesh_object('Handle', hb, collection=col, loc=(0.76, 0, 0.5))
mod = mug.modifiers.new('Union', 'BOOLEAN')
mod.operation, mod.solver, mod.object = 'UNION', 'EXACT', handle
deps = bpy.context.evaluated_depsgraph_get()
joined = bpy.data.meshes.new_from_object(mug.evaluated_get(deps))
mug.modifiers.remove(mod)
old = mug.data
mug.data = joined
mug.data.materials.append(bpy.data.materials['Ceramic'])
bpy.data.objects.remove(handle, do_unlink=True)
for p in mug.data.polygons:
    p.use_smooth = True
kit.select_only(mug)
bpy.data.objects.remove(bpy.data.objects['Cube'], do_unlink=True) if 'Cube' in bpy.data.objects else None
:::
