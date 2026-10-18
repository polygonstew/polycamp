---
id: shader-editor
title: Nodes Without the Fear
summary: Wire a noise texture through a colour ramp into Base Color, and read what you built.
minutes: 12
scene: starter:material-balls
keys: Shift+A, Ctrl+Shift+LMB, Ctrl+T
tags: materials, nodes
xp: 40
---
The **Shader Editor** shows a material as a graph. Boxes are **nodes**, each doing one small job. Wires
carry values from the **outputs** on the right of a node to the **inputs** on the left of another. That is all
there is to it. Data flows left to right.

To open it: switch to the **Shading** workspace, or change any area's editor type to **Shader Editor**. In it:

- [[Shift+A]] adds a node (type to search).
- Drag from an output dot to an input dot to connect. Drag a wire off a socket to cut it.
- [[Ctrl+LMB]] drag across wires cuts them.
- [[X]] deletes selected nodes. [[Shift+D]] duplicates. [[H]] collapses.
- Select two nodes and press [[F]] to make a connection between them.
- Colours of sockets tell types: yellow is colour, grey is a number, purple is a vector.

## The three-node classic

A material usually needs only three things: a **source** of variation, a **remap** into colours, and the **shader** that uses
them.

1. **Noise Texture**: outputs a smoothly random value between 0 and 1.
2. **Color Ramp**: remaps that value into a gradient. Slide the stops to choose which values give which colour.
3. **Principled BSDF** Base Color: receives the result.

Add a **Texture Coordinate** and a **Mapping** node in front to control where and how big the pattern is. The
Mapping node's **Scale** is the usual knob.

:::task id=ramp title="Noise through a ramp into Base Color" xp=16
Select **Sphere_A**. Give it a material whose **Base Color** is driven by a **Noise Texture** that goes through a
**Color Ramp**. Choose any two colours.
check: any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_NOISE' in m.chain.base_color and 'VALTORGB' in m.chain.base_color for m in materials) :: Base Color is fed by a Noise Texture through a Color Ramp
hint: Shading workspace. Shift+A > Texture > Noise Texture, Shift+A > Converter > Color Ramp. Connect Noise Fac to Ramp Fac, Ramp Color to Base Color.
hint: A new node dropped onto an existing wire inserts itself into it automatically.
:::
:::solve task=ramp
ob = bpy.data.objects['Sphere_A']
m = bpy.data.materials.new('Mottled')
compat.use_nodes(m)
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
noise = nt.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 5.0
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.05, 0.1, 0.4, 1)
ramp.color_ramp.elements[1].color = (0.9, 0.4, 0.1, 1)
nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], compat.sock(bsdf, 'base_color'))
ob.data.materials.clear()
ob.data.materials.append(m)
:::

## Control the scale

Without a Texture Coordinate and a Mapping node the pattern uses a default placement. Add them and you can scale,
rotate and offset the whole texture.

:::task id=mapping title="Add Texture Coordinate and Mapping" xp=12
In front of the Noise Texture add a **Texture Coordinate** and a **Mapping** node, connected
*Texture Coordinate > Mapping > Noise Vector*. Set the Mapping **Scale** to something other than 1.
check: any(m != None and m.chain != None and m.chain.base_color != None and 'MAPPING' in m.chain.base_color and 'TEX_COORD' in m.chain.base_color for m in materials) :: The texture goes through Texture Coordinate and Mapping
hint: Shift+A > Input > Texture Coordinate, Shift+A > Vector > Mapping. Connect Object (or UV) to Mapping Vector, Mapping Vector to the Noise's Vector input.
hint: The Mapping node has Location, Rotation and Scale rows.
:::
:::solve task=mapping
m = bpy.data.materials['Mottled']
nt = m.node_tree
noise = next(n for n in nt.nodes if n.type == 'TEX_NOISE')
tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping')
mp.inputs['Scale'].default_value = (2, 2, 2)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
nt.links.new(mp.outputs['Vector'], noise.inputs['Vector'])
:::

:::note tip title="Node Wrangler"
Turn on the **Node Wrangler** add-on (Preferences > Add-ons, search it, tick). Then [[Ctrl+Shift+LMB]] on any node
previews that node's output straight on the object, and [[Ctrl+T]] on a Principled BSDF sets up a full image
texture stack. It is the single most useful node add-on.
:::

## Texture Coordinate: which one?

- **UV**: follows the unwrapped UV map. Best for painted or image textures (the UV world is next door).
- **Object**: uses the object's own local position. Great for procedural textures: no UVs needed and the pattern
  stays glued to the object when it moves.
- **Generated**: a bounding-box coordinate. Similar to Object but stretches to fit.
- **Camera / Window / Reflection**: special purpose.

:::quiz id=q1 xp=5
You are making a procedural stone and have not unwrapped the mesh. Which Texture Coordinate should feed the pattern?
- UV
- *Object (or Generated)
- Window
explain: UV needs an unwrapped mesh. Object or Generated work with no setup at all, which is why procedural textures use them.
:::

:::order id=o1 xp=6
Put the usual flow of a simple procedural material in order, from left to right.
1. Texture Coordinate
2. Mapping
3. Noise Texture
4. Color Ramp
5. Principled BSDF
:::
