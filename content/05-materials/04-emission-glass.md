---
id: emission-glass
title: Making Light and Letting It Through
summary: Emission for the lantern's glow, transmission for glass, and what each costs.
minutes: 12
scene: starter:glow-box
keys: Z
tags: materials, lighting
xp: 40
---
Two kinds of material interact with light in an unusual way: surfaces that **give it off** (emission) and surfaces that **let
it through** (glass). The lantern needs both.

## Emission

Emission makes a surface behave like a light source. In the Principled BSDF it is two sockets: **Emission Color** and
**Emission Strength** (in 3.3 the colour is just *Emission*). A strength of 1 is the same brightness as the colour would
be if it were lit. Anything above that glows.

Emissive surfaces light up the **bloom** in EEVEE and, in **Cycles**, they truly light the scene: a glowing glass box casts
warm light on the floor around it. In Cycles that light is noisy at low sample counts, so use a real **Point light** too
when you can.

:::task id=glass title="The glass glows" xp=12
Give **Lantern_Glass** a material with a warm **Emission Color** (orange-yellow) and an **Emission Strength of 3 or more**.
check: any(o.name == 'Lantern_Glass' and any(m != None and m.emission_strength != None and m.emission_strength >= 3 for m in [mat(n) for n in o.mats]) for o in meshes) :: Lantern_Glass emits light, strength 3 or more
hint: Select the glass box, Material tab > New, open the Emission panel and set a warm colour and Strength 5.
hint: In 3.3 the Emission colour swatch is directly under Clearcoat; set Emission Strength just below it.
:::
:::solve task=glass
ob = bpy.data.objects['Lantern_Glass']
ob.data.materials.clear()
ob.data.materials.append(mat_glow('Lantern_Glass_Mat', '#ffbf6b', 6.0))
:::

:::task id=flame title="The flame glows brighter" xp=10
The flame inside needs to be hotter than the glass: give **Lantern_Flame** an emissive material with **Strength 20 or more**.
check: any(o.name == 'Lantern_Flame' and any(m != None and m.emission_strength != None and m.emission_strength >= 20 for m in [mat(n) for n in o.mats]) for o in meshes) :: Lantern_Flame emits at strength 20 or more
hint: Same recipe as the glass, with a much higher Emission Strength. 30 to 50 is typical for a flame.
:::
:::solve task=flame
ob = bpy.data.objects['Lantern_Flame']
ob.data.materials.clear()
ob.data.materials.append(mat_glow('Flame_Mat', '#ffd08a', 40.0))
:::

## Glass

Real glass is clear and bends light. In the Principled BSDF turn up **Transmission** (called *Transmission Weight* in
4.x). Set **Roughness** near 0 for clear glass or 0.2 to 0.4 for frosted. The **IOR** (index of refraction) controls how
much it bends: 1.45 is glass, 1.33 water, 2.4 diamond.

:::note cpu title="Glass is expensive"
Cycles has to follow rays through the glass and out the other side. Glass needs more **bounces** and more samples. On a CPU:
keep Transmission Bounces at 4, make sure the **Light Paths > Caustics** switches are off, and for flat windows consider
a cheaper trick: an ordinary **Emission** pane for lit windows, or **Alpha** blend for a see-through look.
:::

:::task id=pane title="A window that is really glass" xp=12
Give **Window_Pane** a **Transmission of 0.9 or more** (Principled BSDF). Keep Roughness low.
check: any(o.name == 'Window_Pane' and any(m != None and m.transmission != None and m.transmission >= 0.9 for m in [mat(n) for n in o.mats]) for o in meshes) :: Window_Pane has Transmission 0.9 or more
hint: Material tab > Transmission panel > Weight. In 3.3 it is a Transmission slider directly in the Surface panel.
:::
:::solve task=pane
ob = bpy.data.objects['Window_Pane']
m = kit.pbr('Glass', (0.9, 0.95, 1.0, 1), roughness=0.05)
b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
compat.sock(b, 'transmission').default_value = 1.0
ob.data.materials.clear()
ob.data.materials.append(m)
:::

:::match id=m1 xp=6
Match the setting to the effect.
Emission Strength => How brightly a surface glows
Transmission => How much light passes through it
IOR => How strongly it bends light
Roughness => How blurred the reflections or refractions are
:::

:::quiz id=q1 xp=5
In Cycles, why do you still add a real Point light inside an emissive lantern?
- Emission does not work in Cycles
- *Emissive surfaces light scenes with more noise, a real light is cleaner and cheaper at low samples
- A glowing surface needs a light to render at all
explain: Emission does illuminate the scene in Cycles, but light from a big surface is noisier than from a point. A small real light gives the same glow with far less grain.
:::
