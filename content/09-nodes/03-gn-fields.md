---
id: gn-fields
title: Fields and Attributes: Bumpy Ground
summary: Move every vertex by a noise value with Set Position, and meet the idea that makes Geometry Nodes tick.
minutes: 14
scene: starter:scatter-ground
keys: Shift+A
tags: geometry nodes
xp: 45
---
Geometry Nodes has one big idea that confuses people for a week and then feels obvious: a **field**.

A normal value is one number: 5. A **field** is a value that can be *different for each element* (each vertex, point or face), calculated when the node uses it. The **Position** node does not output one position,
it outputs *the position of whichever vertex is asking*. A **Noise Texture** fed from Position gives each vertex a different number. Plug that into **Set Position**'s offset and every vertex moves by its own amount.
That is a whole procedural terrain in four nodes.

Fields flow along **diamond-dotted** wires (dotted lines show a field, solid lines a single value). Sockets that accept fields show a small diamond.

## The graph

    Group Input ► Set Position ► Group Output
                    ▲ Offset
    Noise Texture ► Combine XYZ (Z only)

1. **Set Position** (Geometry > Write > Set Position) between input and output.
2. **Noise Texture** (Texture > Noise). In geometry nodes its *Vector* input defaults to the vertex position, so no wiring is needed. Set **Scale** about 1.5.
3. **Combine XYZ** (Converter > Combine XYZ): put the noise **Fac** into **Z**, leaving X and Y at 0, so the push is only upward.
4. Plug Combine XYZ **Vector** into Set Position **Offset**.

A noise value goes 0 to 1, so also subtract about 0.5 and scale by 0.4 with a **Math** node, or the whole ground just lifts. (Many tutorials skip this and wonder why their landscape floats.)

:::task id=ground title="Set Position with a noise offset" xp=22
Build a graph on the **Ground** using **Set Position**, a **Noise Texture** and **Combine XYZ**.
check: any('GeometryNodeSetPosition' in g.ids and 'ShaderNodeTexNoise' in g.ids and 'ShaderNodeCombineXYZ' in g.ids for g in groups) :: Set Position driven by a Noise Texture through Combine XYZ
check: any(m.type == 'NODES' for o in meshes if o.name == 'Ground' for m in o.mods) :: The Ground uses a Geometry Nodes modifier
hint: Geometry Nodes workspace, select Ground, New. Shift+A > Geometry > Write > Set Position. Shift+A > Texture > Noise Texture.
hint: Set the noise Scale to about 1.5. Put the Z of Combine XYZ from the noise Fac. Remember to also subtract about 0.5 or the whole ground just rises.
:::
:::solve task=ground
ground = bpy.data.objects['Ground']
ng, gi, go = gn_group('Bumps')
sp = gn_node(ng, 'GeometryNodeSetPosition', (0, 0))
noise = gn_node(ng, 'ShaderNodeTexNoise', (-500, -200))
noise.inputs['Scale'].default_value = 1.5
sub = gn_node(ng, 'ShaderNodeMath', (-300, -200))
sub.operation = 'MULTIPLY_ADD'
sub.inputs[1].default_value = 0.8
sub.inputs[2].default_value = -0.4
comb = gn_node(ng, 'ShaderNodeCombineXYZ', (-150, -200))
gn_link(ng, noise, 'Fac', sub, 0)
gn_link(ng, sub, 0, comb, 'Z')
gn_link(ng, gi, 0, sp, 'Geometry')
gn_link(ng, comb, 0, sp, 'Offset')
gn_link(ng, sp, 'Geometry', go, 0)
gn_modifier(ground, ng)
:::

:::note tip title="Stack it with the scatter"
Put the Set Position first, then the Distribute Points. Now the grass follows the bumpy ground, because the points are placed on the already-displaced surface. Order of nodes (like modifiers) is order of events.
:::

## Attributes

An **attribute** is a named value stored on every element of a mesh: position, normal, UV, a vertex colour, a vertex group, or one you invent. A field *reads* attributes and computes new ones. The **Spreadsheet** shows them all, as
columns. The **Store Named Attribute** node saves a field's result as an attribute that a material can read through the **Attribute** node. Grass that is darker where it is thicker, or snow only on up-facing surfaces: that is the
pattern.

:::reveal title="A tiny example: snow on up-facing faces"
Take the **Normal** node (a field), take its **Z** with Separate XYZ, compare it to 0.7 with **Compare**, and use the result as the **Selection** input of Instance on Points or Set Material. Only faces pointing upward pass. That is
snow, moss or dust on tops, in three nodes.
:::

:::quiz id=q1 xp=5
What is a *field*?
- A big number
- *A value that is evaluated separately for each element (vertex, point, face) when a node uses it
- A kind of mesh
explain: Fields let one wire carry "a different value per vertex". The Position node, noise textures and Random Value all produce fields.
:::

:::quiz id=q2 xp=5
You build the noise offset graph and the whole ground floats upward by half a metre on average. What did you forget?
- The Join Geometry node
- *To centre the noise around zero (subtract about 0.5)
- Smooth shading
explain: Noise returns 0 to 1, so on average it lifts everything. Subtract the average (about 0.5) so the ground goes up in some places and down in others.
:::
