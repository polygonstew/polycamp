---
id: principled
title: The Principled BSDF
summary: One shader, a handful of sliders: colour, metal, roughness. Most of what you need.
minutes: 12
scene: starter:material-balls
keys: Z
tags: materials
xp: 40
---
A **material** tells the renderer how a surface reacts to light. Every renderer in Blender (Cycles, EEVEE,
Workbench's material mode) reads the same material. The **Principled BSDF** is the all-in-one shader: a physically
motivated surface with the controls most real objects need.

Click an object and open the **Material** tab (the red sphere icon). A new material starts with a Principled
BSDF already connected to the output. The ones that matter day to day:

- **Base Color**: the colour of the surface, what you would call its paint.
- **Metallic**: 0 for plastic, wood, stone and skin, 1 for metal. Almost always 0 or 1. Values in between are for
  dirty or oxidised metal.
- **Roughness**: how blurry reflections are. 0 is a mirror, 1 is chalk. Plastic ≈ 0.3, wood ≈ 0.6, stone ≈ 0.85.

:::v 3
**Blender 3.3** shows the shader as one long panel: Subsurface, Metallic, Specular, Roughness, Anisotropic, Sheen,
Clearcoat, Transmission, Emission and so on, all expanded under Surface.
:::

:::v 4+
**Blender 4.x and 5.x** reorganise it into collapsible panels (Subsurface, Specular, Transmission, Coat, Sheen,
Emission). The names changed a little too: **Specular** became *Specular IOR Level*, **Clearcoat** became *Coat*,
**Transmission** is *Transmission Weight* and **Emission** is *Emission Color* plus *Strength*. Base Color,
Metallic and Roughness are unchanged.
:::

## Look at it properly

The starter has three spheres sharing one grey material. Switch the viewport to **Material Preview** ([[Z]] > Material
Preview) to see them lit by a built-in studio, without the cost of Cycles.

:::note cpu title="Material Preview on a CPU"
Material Preview runs EEVEE, which is OpenGL and quick enough on most machines. If your viewport crawls, stay in
Solid mode, pick colours by swatch, and check the look with a small render in Cycles once in a while.
:::

## Give each sphere its own material

All three share the same material called `Grey`. Change it and all three change. Click the
**material name** and then the **duplicate icon** (two overlapping pages) next to it to make a new, independent copy,
or click **New**.

:::task id=plastic title="Sphere_A: shiny red plastic" xp=10
Give **Sphere_A** its own new material. Base Color a strong red (R above 0.5, G under 0.3), **Metallic 0**,
**Roughness 0.4 or lower**.
check: any(m != None and m.principled and m.base_color[0] > 0.5 and m.base_color[1] < 0.3 and m.metallic <= 0.1 and m.roughness <= 0.4 for m in [mat(n) for o in meshes if o.name == 'Sphere_A' for n in o.mats]) :: Sphere_A is a glossy red plastic
hint: Select Sphere_A, Material tab, click the duplicate icon beside the material name to make a copy, then rename it Red_Plastic.
hint: Click the Base Color swatch to open the colour picker. Roughness is a slider further down.
:::
:::solve task=plastic
ob = bpy.data.objects['Sphere_A']
ob.data.materials.clear()
ob.data.materials.append(kit.pbr('Red_Plastic', (0.8, 0.05, 0.04, 1), roughness=0.3, metallic=0.0))
:::

:::task id=gold title="Sphere_B: brushed gold" xp=10
**Sphere_B** gets a metal: **Metallic 0.9 or higher**, a warm yellow Base Color (red above green above blue) and a
**Roughness between 0.2 and 0.5**.
check: any(m != None and m.principled and m.metallic >= 0.9 and m.base_color[0] > m.base_color[1] > m.base_color[2] and 0.2 <= m.roughness <= 0.5 for m in [mat(n) for o in meshes if o.name == 'Sphere_B' for n in o.mats]) :: Sphere_B is a warm metal with moderate roughness
hint: Metal gets its colour from Base Color. Try 1.0, 0.77, 0.34 for gold.
:::
:::solve task=gold
ob = bpy.data.objects['Sphere_B']
ob.data.materials.clear()
ob.data.materials.append(kit.pbr('Gold', (1.0, 0.77, 0.34, 1), roughness=0.3, metallic=1.0))
:::

:::task id=chalk title="Sphere_C: chalky stone" xp=10
**Sphere_C** should be a dry, matte stone: **Roughness 0.8 or higher**, no metal, a cool grey Base Color.
check: any(m != None and m.principled and m.roughness >= 0.8 and m.metallic <= 0.1 for m in [mat(n) for o in meshes if o.name == 'Sphere_C' for n in o.mats]) :: Sphere_C is rough and non-metallic
hint: Roughness 0.9, Metallic 0. The colour can be any grey.
:::
:::solve task=chalk
ob = bpy.data.objects['Sphere_C']
ob.data.materials.clear()
ob.data.materials.append(kit.pbr('Stone', (0.45, 0.46, 0.5, 1), roughness=0.9, metallic=0.0))
:::

:::task id=three title="Three different materials in use" xp=5
The three spheres must end up with three different materials.
check: len({n for o in meshes if o.name.startswith('Sphere_') for n in o.mats if n}) >= 3 :: Three distinct materials on the spheres
hint: If a sphere still shows Grey, it is still sharing the original. Duplicate it for that one too.
:::
:::solve task=three
pass
:::

:::note tip title="Roughness is half the look"
Beginners fiddle with colour. Professionals fiddle with roughness. The same red looks like candy, car paint or brick
depending on it. When a material looks "off", try roughness first.
:::

:::quiz id=q1 xp=5
Which Metallic value is right for a wooden table?
- 1
- 0.5
- *0
explain: Metallic is a yes/no property in practice. Wood is a dielectric, so 0. Use values between only for things like rusty or dusty metal.
:::

:::match id=m1 xp=6
Match the material to its rough settings.
Polished mirror => Metallic 1, Roughness 0
Matte stone => Metallic 0, Roughness 0.85
Glossy plastic => Metallic 0, Roughness 0.3
Brushed steel => Metallic 1, Roughness 0.4
:::
