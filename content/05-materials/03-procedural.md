---
id: procedural
title: Procedural Wood and Stone
summary: Real-looking surfaces from mathematics. No image files, no UVs, no memory.
minutes: 14
scene: starter:material-balls
keys: Shift+A
tags: materials, nodes
xp: 45
---
A **procedural** material is built from maths, not pictures. Blender generates the pattern on the fly, at any resolution,
and it costs no texture memory. On a machine with limited RAM that is a real advantage. The price: a little more
set-up time and a slightly "clean" look until you break it up with noise.

The big procedural textures (all under **Shift+A > Texture**):

- **Noise**: soft clouds. The workhorse of dirt, variation and wood grain.
- **Voronoi**: cells. Stone, cobbles, cracks, leather, scales.
- **Wave**: bands and rings. Wood grain, marble veins, ripples.
- **Brick**: rows of bricks or shingles with mortar.
- **Musgrave** (3.x) / merged into Noise (4.1+): fractal clouds.
- **Gradient, Magic, Checker**: utilities.

## Wood

Wood is bands (from the **Wave** texture), wobbled by **distortion**, remapped through a **Color Ramp** from dark brown
to light brown. Add a fine **Noise** into the **Bump** node and you also get the tiny grain relief.

The classic bump hookup: *Noise > Bump (Height) > Principled BSDF Normal*. A Bump node pretends the surface has height
without adding geometry.

:::task id=wood title="Wood on Sphere_A" xp=14
Give **Sphere_A** a wood material whose **Base Color** comes from a **Wave Texture** through a **Color Ramp**, with a
**Bump** node feeding the shader's **Normal**.
check: any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_WAVE' in m.chain.base_color and 'VALTORGB' in m.chain.base_color for m in [mat(n) for o in meshes if o.name == 'Sphere_A' for n in o.mats]) :: Sphere_A's colour comes from a Wave Texture through a Color Ramp
check: any(m != None and m.chain != None and m.chain.normal != None and 'BUMP' in m.chain.normal for m in [mat(n) for o in meshes if o.name == 'Sphere_A' for n in o.mats]) :: Its Normal goes through a Bump node
hint: Wave Texture: type Bands, Distortion around 5, Scale 7. Color Ramp from dark brown to light brown.
hint: Shift+A > Vector > Bump. Connect a Noise Texture's Fac into Bump Height, and Bump Normal into the Principled Normal.
:::
:::solve task=wood
ob = bpy.data.objects['Sphere_A']
ob.data.materials.clear()
ob.data.materials.append(mat_wood('Wood_Test'))
:::

## Stone

Stone is cells (**Voronoi**) roughened by noise. Voronoi gives you a different value for each cell, which a
**Color Ramp** can turn into grey and brown patches. Use Voronoi's **Distance to Edge** output for cracks and
mortar lines.

:::task id=stone title="Stone on Sphere_C" xp=14
Give **Sphere_C** a stone material whose Base Color comes from a **Voronoi Texture**, with **Roughness 0.8 or higher** and a
**Bump** on the normal.
check: any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_VORONOI' in m.chain.base_color for m in [mat(n) for o in meshes if o.name == 'Sphere_C' for n in o.mats]) :: Sphere_C's colour is driven by a Voronoi Texture
check: any(m != None and m.roughness != None and m.roughness >= 0.8 and m.chain != None and m.chain.normal != None and 'BUMP' in m.chain.normal for m in [mat(n) for o in meshes if o.name == 'Sphere_C' for n in o.mats]) :: Rough surface with a bump
hint: Shift+A > Texture > Voronoi Texture. Plug its Color output through a Color Ramp or Mix into Base Color.
hint: Set Roughness 0.9 on the Principled BSDF. Add a Noise through Bump into Normal for tiny chips.
:::
:::solve task=stone
ob = bpy.data.objects['Sphere_C']
ob.data.materials.clear()
ob.data.materials.append(mat_stone('Stone_Test'))
:::

## Break the perfection

Real surfaces are never uniform. Three ways to ruin a clean procedural material in a good way:

1. **Layer two scales of noise**: a big soft one and a fine one, mixed with a **Mix** node at 20 or 30%.
2. **Drive roughness** with a texture: a Color Ramp from a Noise into the Roughness input gives patchy shine.
3. **Mix two materials** with a **Mix Shader** and a noise as the factor: moss on stone, rust on metal, dirt in
   the corners.

:::task id=rough title="Patchy roughness" xp=10 optional
For extra credit: connect a Noise (through a Color Ramp) to the **Roughness** of one of the materials so it shines unevenly.
check: any(m != None and m.chain != None and m.chain.roughness != None and 'TEX_NOISE' in m.chain.roughness for m in materials) :: Roughness is driven by a Noise Texture
hint: Remap the Noise with a Color Ramp (values 0.5 to 0.95), then plug it into Roughness.
:::
:::solve task=rough
ob = bpy.data.objects['Sphere_A']
m = ob.data.materials[0]
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
noise = nt.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 12
ramp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], compat.sock(bsdf, 'roughness'))
:::

:::note cpu title="Procedural versus image textures"
Procedural nodes are evaluated per sample, so a huge network slows Cycles down a little. A 1K image texture costs RAM
but is read in an instant. Rule of thumb: procedural for large surfaces seen from far, images when a detail must be
exactly right.
:::

:::quiz id=q1 xp=5
What does a Bump node do?
- Moves the vertices
- *Fakes surface relief by tilting the shading normal, with no extra geometry
- Subdivides the mesh
explain: Bump reads a height value and changes how light bounces. The silhouette is untouched, but surfaces look carved.
:::
