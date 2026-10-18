---
id: boss-materials
title: Boss: Dress the Diorama
summary: Take the grey scene and make it look like timber, stone, grass, shingles and warm light.
minutes: 30
scene: starter:bare-diorama
boss: true
keys: Z, Shift+A
tags: boss, materials
xp: 140
---
:::cubby shock
It is the grey scene from last time, with everything exactly where you left it. Now it needs surfaces. You may use any
approach from this world: Principled colours, procedural nodes, emission, glass. The checks only care that it is *dressed*.
:::

## Brief

Apply materials so every major piece of the diorama has one. The scene contains: **Cabin_Walls**, **Cabin_Roof**, **Cabin_Panes** (the
glowing windows), **Ground**, six **Rock.**\* objects, five **Pine.**\* objects (they need a trunk and a leaf material in two slots), the
lamp post and its lantern.

Use the library of ideas from the lessons:

- **Cabin walls:** wood from a Wave texture and Color Ramp, with a bump.
- **Roof:** shingles from a Brick texture.
- **Ground:** a green noise gradient (two scales of noise).
- **Rocks:** stone from Voronoi and noise, high roughness.
- **Windows and lantern:** emission, strength 3 or more.
- **Pines:** a dark green leaf material and a brown bark.

You can build them by hand, or copy techniques from the earlier lessons' solution scripts. The scene's lights and camera are ready
and waiting.

:::goal img=diorama-materials.png
Reference with materials, before lighting and sky are tuned. The next world does the light.
:::

:::task id=walls title="Timber walls" xp=20
**Cabin_Walls** gets a material whose Base Color is driven by a texture (so it is not a flat colour).
check: any(o.name == 'Cabin_Walls' and any(m != None and m.chain != None and m.chain.base_color != None for m in [mat(n) for n in o.mats]) for o in meshes) :: Cabin_Walls has a texture-driven Base Color
hint: Copy the wood recipe from the Procedural lesson: Wave Texture, Color Ramp, then Bump from Noise.
:::

:::task id=roof title="Shingled roof" xp=20
**Cabin_Roof** gets its own material, also texture driven.
check: any(o.name == 'Cabin_Roof' and any(m != None and m.chain != None and m.chain.base_color != None for m in [mat(n) for n in o.mats]) for o in meshes) :: Cabin_Roof has a texture-driven Base Color
hint: The Brick Texture node makes rows of tiles. Set Scale about 6 and Mortar Size small.
:::

:::task id=ground title="Green ground" xp=15
**Ground** gets a green-dominant material (the Base Color is either green or driven by a texture).
check: any(o.name == 'Ground' and any(m != None and ((m.base_color != None and m.base_color[1] > m.base_color[0]) or (m.chain != None and m.chain.base_color != None)) for m in [mat(n) for n in o.mats]) for o in meshes) :: Ground has a green or texture-driven material
hint: A Noise Texture through a Color Ramp from dark green to yellow-green is enough.
:::

:::task id=rocks title="Stone rocks" xp=15
Every **Rock** has a material with **Roughness 0.7 or higher**.
check: sum(1 for o in meshes if o.name.startswith('Rock') and any(m != None and m.roughness != None and m.roughness >= 0.7 for m in [mat(n) for n in o.mats])) >= 6 :: All six rocks have a rough material
hint: Make one material, select all the rocks, and assign it: click the active rock last, then Ctrl+L > Link Materials.
:::

:::task id=pines title="Trunks and needles" xp=15
Every **Pine** has two materials in its slots (bark and leaves).
check: sum(1 for o in meshes if o.name.startswith('Pine') and len([n for n in o.mats if n]) >= 2) >= 5 :: All five pines have two materials
hint: Material tab > click + twice to add two slots. In Edit Mode select the trunk faces, pick the bark slot and press Assign.
:::

:::task id=glow title="Windows and lantern glow" xp=25
The cabin's **Cabin_Panes** and the lamp post's **PostLantern_Glass** both emit light (Emission Strength 3 or more).
check: any(o.name == 'Cabin_Panes' and any(m != None and m.emission_strength != None and m.emission_strength >= 3 for m in [mat(n) for n in o.mats]) for o in meshes) :: The windows emit light
check: any(o.name == 'PostLantern_Glass' and any(m != None and m.emission_strength != None and m.emission_strength >= 3 for m in [mat(n) for n in o.mats]) for o in meshes) :: The lantern glass emits light
hint: You made this exact material in the Emission lesson. Emission colour warm, strength 5.
:::

:::task id=variety title="Six materials or more" xp=10
The scene uses at least six different materials, so nothing looks like one plastic.
check: len({n for o in meshes for n in o.mats if n}) >= 6 :: Six or more distinct materials in use
hint: Walls, roof, ground, rocks, leaves, bark, glow: that is already seven.
:::

:::solve
build_diorama(mats=True, lights=True, camera=True, world=True, cpu=None)
:::
