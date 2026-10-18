---
id: gn-intro
title: Geometry Nodes: First Contact
summary: A node group in a modifier: geometry flows in, flows out, and you change it in between.
minutes: 12
scene: starter:gn-plane
keys: Shift+A, Ctrl+Shift+LMB
tags: geometry nodes
xp: 40
---
A **Geometry Nodes** modifier is a modifier whose behaviour you build yourself. It works like a Shader Editor graph, but what flows through the wires is **geometry**. A tiny graph does three jobs:

1. **Group Input**: the mesh the modifier is attached to comes in here (the blue-green *Geometry* socket).
2. Some **nodes** that do things to it.
3. **Group Output**: the result leaves here, and that is what you see and render.

Open the **Geometry Nodes** workspace. Select the cube (called `Block` in the starter) and press **New** in the node editor header. Blender makes a group called "Geometry Nodes" with Group Input wired straight to
Group Output, and adds a Geometry Nodes modifier to the object. The cube looks unchanged because nothing happens between input and output yet.

## Add a Transform

Press [[Shift+A]] > **Geometry > Transform Geometry**. Drop it onto the wire between the two nodes. It has **Translation**, **Rotation** and **Scale** inputs. Set the Z translation to 1 and scale to 1.5. The cube jumps up and
grows, and you did it without touching the object or its mesh. Move the numbers: it updates live.

:::task id=mod title="A Geometry Nodes modifier" xp=10
Give the **Block** a **Geometry Nodes** modifier with a new node group.
check: any(m.type == 'NODES' for o in meshes for m in o.mods) :: An object has a Geometry Nodes modifier
check: any(g.kind == 'GeometryNodeTree' for g in groups) :: A geometry node group exists
hint: Select the cube, Modifiers tab > Add Modifier > Geometry Nodes > New. Or use the Geometry Nodes workspace and press New.
:::
:::solve task=mod
ob = bpy.data.objects['Block']
ng, gi, go = gn_group('Lift')
gn_link(ng, gi, 0, go, 0)
gn_modifier(ob, ng)
:::

:::task id=xf title="Move and scale it with a Transform Geometry node" xp=14
Put a **Transform Geometry** node between the input and the output.
check: any('GeometryNodeTransform' in g.ids for g in groups) :: The node group contains Transform Geometry
hint: Shift+A, search "Transform", drop it onto the connecting wire. The nodes auto-connect when you drop on a wire.
:::
:::solve task=xf
ng = bpy.data.node_groups['Lift']
gi = next(n for n in ng.nodes if n.bl_idname == 'NodeGroupInput')
go = next(n for n in ng.nodes if n.bl_idname == 'NodeGroupOutput')
for l in list(ng.links):
    ng.links.remove(l)
tf = gn_node(ng, 'GeometryNodeTransform', (0, 0))
tf.inputs['Translation'].default_value = (0, 0, 1)
tf.inputs['Scale'].default_value = (1.5, 1.5, 1.5)
gn_link(ng, gi, 0, tf, 'Geometry')
gn_link(ng, tf, 'Geometry', go, 0)
:::

## Parameters you can expose

Drag a node's input to the **Group Input** node's empty socket (the one at the end of the list) and Blender creates a new **modifier input**. Name it ("Height") and it appears as a slider in the **Modifiers
tab**, so anyone using your object can change it without opening the node editor. That is how artists build reusable tools.

:::v 3
**Blender 3.3:** exposed inputs are listed in the **N panel > Group** tab of the node editor, where you can rename and set ranges.
:::

:::v 4+
**Blender 4.x and 5.x:** open the **Group** tab of the N panel for the **interface** panel, with sockets, defaults, min and max values, and panels for organising them.
:::

:::note tip title="Spreadsheet"
The **Spreadsheet** editor (a workspace tab, or change an area to it) shows the actual data after each node: points, edges, faces, their positions, anything. Click the monitor icon on a node's header to make the spreadsheet
(and viewport) show that node's output. It is the debugger for geometry nodes.
:::

:::note cpu title="Geometry Nodes on a CPU"
Geometry nodes run on the CPU anyway, which is good news: no GPU needed. A scatter of 50,000 instances is fine. Realising millions of instances into real geometry (the *Realize Instances* node) is where memory
runs out, so keep things as instances whenever you can.
:::

:::quiz id=q1 xp=5
In a Geometry Nodes group, what does the Group Input's blue-green socket carry?
- A texture
- *The geometry (mesh, curve or points) the modifier is attached to
- The render settings
explain: The Geometry socket brings in the object's own geometry. Everything in the group transforms it before it leaves through Group Output.
:::
