---
id: gn-scatter
title: Scattering Grass
summary: Distribute points over a surface and put an object on each one.
minutes: 16
scene: starter:scatter-ground
keys: Shift+A
tags: geometry nodes, instances
xp: 50
---
The most-used Geometry Nodes recipe in the world: **put lots of copies of one thing across a surface**. Grass, rocks, trees, bolts, hair, fish scales. Three nodes do the core job.

1. **Distribute Points on Faces**: sprinkles random points across the faces of the incoming mesh. The **Density** controls how many per square metre.
2. **Instance on Points**: for each point, places a copy of whatever you give it as the **Instance** input. It can be a whole object (through the next node).
3. **Object Info**: brings another object's geometry into the graph. Pick the `Tuft` and switch on **As Instance** so copies stay cheap.

Add **Random Value** nodes to vary **rotation** and **scale** per instance, so no two blades look the same. Then a **Join Geometry** node merges the instances with the original ground, so the ground stays visible.

The wiring:

    Group Input ──► Distribute Points on Faces ──► Instance on Points ──► Join Geometry ──► Group Output
                                                    ▲ Instance:  Object Info (Tuft)       ▲
                                                    ▲ Scale:     Random Value             Group Input ─┘

:::task id=nodes title="Build the scatter graph" xp=24
Select the **Ground**, add a Geometry Nodes modifier and build: **Distribute Points on Faces**, **Instance on Points**, **Object Info** (picking `Tuft`) and **Join Geometry**.
check: any(m.type == 'NODES' for o in meshes if o.name == 'Ground' for m in o.mods) :: The Ground has a Geometry Nodes modifier
check: any('GeometryNodeDistributePointsOnFaces' in g.ids and 'GeometryNodeInstanceOnPoints' in g.ids and 'GeometryNodeObjectInfo' in g.ids for g in groups) :: The graph distributes points and instances an object
check: any('GeometryNodeJoinGeometry' in g.ids for g in groups) :: Join Geometry keeps the ground in the result
hint: Geometry Nodes workspace, select Ground, New. Shift+A > Point > Distribute Points on Faces, Shift+A > Instances > Instance on Points, Shift+A > Input > Scene > Object Info.
hint: Object Info: drag the Tuft from the Outliner into its Object field, and tick As Instance (this is the default in newer versions).
:::
:::solve task=nodes
ground = bpy.data.objects['Ground']
ng, gi, go = gn_group('Scatter')
dist = gn_node(ng, 'GeometryNodeDistributePointsOnFaces', (-350, 100))
dist.distribute_method = 'RANDOM'
dist.inputs['Density'].default_value = 12.0
info = gn_node(ng, 'GeometryNodeObjectInfo', (-350, -250))
info.inputs['Object'].default_value = bpy.data.objects['Tuft']
try:
    info.inputs['As Instance'].default_value = True
except Exception:
    pass
inst = gn_node(ng, 'GeometryNodeInstanceOnPoints', (0, 0))
join = gn_node(ng, 'GeometryNodeJoinGeometry', (350, 0))
gn_link(ng, gi, 0, dist, 0)
gn_link(ng, dist, 'Points', inst, 'Points')
gn_link(ng, info, 'Geometry', inst, 'Instance')
gn_link(ng, inst, 'Instances', join, 0)
gn_link(ng, gi, 0, join, 0)
gn_link(ng, join, 0, go, 0)
gn_modifier(ground, ng)
:::

## Vary every instance

Identical blades look like a lawn from a stamp. Add a **Random Value** node (Utilities > Random Value) set to **Float** or **Vector** type, and plug its **Value** into the **Scale** of Instance on Points. Add a second one (Vector,
Z range 0 to 6.28) into **Rotation**. Each point gets its own random scale and its own random turn. The **Seed** input changes the whole pattern.

:::task id=random title="Random scale and rotation" xp=14
Add a **Random Value** node and feed it into **Instance on Points**' scale or rotation.
check: any('FunctionNodeRandomValue' in g.ids for g in groups) :: The graph has a Random Value node
hint: Shift+A > Utilities > Random Value. Plug Value into the Scale socket. Set Min and Max for a believable range (say 0.6 and 1.4 for scale).
:::
:::solve task=random
ng = bpy.data.node_groups['Scatter']
inst = next(n for n in ng.nodes if n.bl_idname == 'GeometryNodeInstanceOnPoints')
rnd = gn_node(ng, 'FunctionNodeRandomValue', (-100, -300))
out = next(o for o in rnd.outputs if o.enabled and o.name == 'Value')
ng.links.new(out, inst.inputs['Scale'])
:::

:::note tip title="Density, not count"
Density is points per square metre, so scaling the ground up adds more grass, automatically. If the viewport slows down, lower **Density** for the viewport and raise it for the render by exposing the Density as a group input and keying nothing, just changing it
before the final render.
:::

:::note cpu title="Instances are the whole trick"
Each instance shares the original blade's mesh, so 10,000 tufts cost about as much memory as one tuft plus 10,000 transforms. Cycles also handles instancing well. If you realise instances (turn them into real mesh) the memory cost
multiplies.
:::

:::quiz id=q1 xp=5
Why connect the original Group Input to the Join Geometry node as well?
- To make the instances render
- *So the ground itself still appears next to the instances
- It is required by Instance on Points
explain: Instance on Points outputs only the instances. Joining the original geometry back in keeps the surface you scattered on.
:::

:::match id=m1 xp=6
Match the node to its job.
Distribute Points on Faces => Creates random points on a surface
Instance on Points => Puts a copy of something on each point
Object Info => Brings another object's geometry into the graph
Join Geometry => Merges several geometries into one output
:::
