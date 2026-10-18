---
id: modeling-tools
title: Bridge, Fill, Merge, Knife
summary: Closing holes, joining parts and cutting new edges across a face.
minutes: 12
scene: starter:two-boxes
keys: F, K, M, Alt+M
tags: edit mode, modeling
xp: 40
---
Extrude and inset make geometry. This lesson is the cleanup crew: the tools you use to connect, close,
merge and cut what is already there.

## The starter

The scene holds one mesh with three separate pieces. Two open boxes face each other, each missing the
wall that points at its neighbour. Off to the side is a cup with no lid. Statistics shows a pile of
**boundary edges**: edges that belong to only one face, which means there is a hole.

## Bridge Edge Loops: connect two openings

Select the rim of one hole and the rim of the other, then **Edge > Bridge Edge Loops**. Blender builds a
tube of faces between them. Both loops need roughly the same number of edges to join cleanly, and here both
have four.

:::task id=bridge title="Join the two boxes into one tube" xp=14
Select the open rims of both boxes ( [[Alt+LMB]] on an edge of the opening selects the whole loop, then
[[Shift+Alt+LMB]] on the other) and use **Edge > Bridge Edge Loops**. The openings between the two boxes
are now closed by four new faces.
check: any(o.faces >= 14 and o.boundary_edges == 4 for o in meshes) :: The boxes are bridged, only the cup's rim is still open
hint: Edge select mode (2). Alt+click an edge of the left box's open side, Shift+Alt+click an edge of the right box's open side, then Edge menu > Bridge Edge Loops.
hint: You should have 8 edges selected at the moment you press Bridge: four from each loop.
:::
:::solve task=bridge
me = bpy.context.object.data
bm = bmesh.new()
bm.from_mesh(me)
bm.edges.ensure_lookup_table()
rim = [e for e in bm.edges if e.is_boundary and abs((e.verts[0].co + e.verts[1].co).y / 2) < 1.5]
bmesh.ops.bridge_loops(bm, edges=rim)
bm.to_mesh(me)
bm.free()
:::

## Fill: make a face from edges

Select the rim of the cup and press [[F]]. Blender fills whatever the selected edges enclose. Select
**three or more vertices** and F makes a face from them too. (With only two vertices selected it makes an
edge.) The filled face is an ngon. For a flat lid that is fine.

:::task id=fill title="Put a lid on the cup" xp=12
Select the cup's top rim and press [[F]] to fill it. Afterwards no open edges should remain.
check: any(o.boundary_edges == 0 for o in meshes) :: The mesh is watertight (no open edges)
hint: Alt+click one edge of the cup's open rim to select the whole loop, then press F.
hint: In vertex mode, selecting every rim vertex and pressing F works as well.
:::
:::solve task=fill
me = bpy.context.object.data
bm = bmesh.new()
bm.from_mesh(me)
rim = [e for e in bm.edges if e.is_boundary]
bmesh.ops.edgeloop_fill(bm, edges=rim)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me)
bm.free()
:::

## Merge and dissolve

[[M]] merges selected vertices: **At Center**, **At Cursor**, **Collapse** (each connected group to its own
centre), or **By Distance**, which welds vertices that sit on top of each other. Use **By Distance** after
you duplicate and join pieces, because doubled vertices cause shading and boolean trouble.

[[Ctrl+X]] **dissolves** edges and vertices: the element disappears and the faces around it close up and
merge. Dissolve an edge between two quads to make one ngon. Dissolve a vertex on an edge loop to
shorten the loop.

## Knife

[[K]] lets you draw cuts across faces. Click to place points, [[Enter]] to confirm, and hold [[C]] to
constrain to the face you started on. Useful for adding a detail edge without a full loop cut, but it
breeds triangles and ngons, so tidy afterwards.

:::task id=knife optional title="Stretch: cut a diagonal with the Knife" xp=10 manual
Try it on a spare cube: press [[K]], click two edge midpoints on a face, press [[Enter]]. Look at the new
triangles. Then undo.
hint: Hold C while cutting to snap cuts to the face under the mouse. Right-click or Esc cancels the whole cut.
:::

:::match id=m1 xp=6
Which tool fits the job?
Weld vertices that are on top of each other => M > By Distance
Close a hole made of selected edges => F
Make a tube between two openings => Bridge Edge Loops
Cut a new edge across one face => K
:::

:::quiz id=q1 xp=5
You merged two chunks of mesh and the shading looks strangely sharp along the seam. What is the likely cause?
- The normals are inverted
- *Overlapping duplicate vertices that were never merged
- The viewport needs a restart
explain: Two vertices at the same position leave a hairline gap in the connectivity, so normals do not average across it. Select all and use M > By Distance to weld them.
:::
