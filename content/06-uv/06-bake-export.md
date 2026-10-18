---
id: bake-export
title: Texture Budgets, Baking and glTF Out
summary: Keep image sizes sane, understand baking, and send a model to Godot through Kiln.
minutes: 14
scene: starter:uv-props
keys: Ctrl+J
tags: export, textures, godot
xp: 40
---
Three practical things that come after "it looks good in Blender": keeping memory in check, getting lighting into textures when you must, and
moving the result into a game engine.

## Texture budget

Everything you load stays in RAM, and a render that runs out of memory gets killed with no explanation. Rules for an 11 GB machine:

- **1024 × 1024** for most props. **2048** for the hero prop, once. **4096** almost never.
- Reuse maps. Three props that use the same wood do not need three wood textures.
- Combine small maps into one when you can (the advanced "packed" ORM map in games).
- Check **Image Texture** sizes in the **Outliner > Blender File > Images** view (or the app's scene mirror).

The starter has three props with plain grey materials: **Barrel**, **Crate** and **Plank**. Give each its own texture from the Lab, then check sizes.

:::task id=three title="Three props, three images, all 1024 or smaller" xp=14
Texture all three props with images (Lab → Blender works). You should end up with **at least three image files**, none bigger than **1024** on either side.
check: len({i.path for i in images if i.source == 'FILE'}) >= 3 :: Three or more image files are loaded
check: all(i.w <= 1024 and i.h <= 1024 for i in images if i.source == 'FILE') :: None of them exceeds 1024 px
hint: Texture Lab: make a planks texture, select the Barrel in Blender, → Blender. Repeat for the crate and the plank with other presets or seeds.
hint: In the Lab, name each set differently (for example barrel, crate, plank) so they do not overwrite each other.
:::
:::solve task=three
for i, name in enumerate(('Barrel', 'Crate', 'Plank')):
    path = make_test_image(bpy.app.tempdir + '%s_base.png' % name.lower(), 'base_color', 64 + 16 * i)
    m = matkit.build_pbr(name + '_Tex', {'base_color': path})
    ob = bpy.data.objects[name]
    ob.data.materials.clear()
    ob.data.materials.append(m)
:::

## Baking in one paragraph

**Baking** renders something (lighting, ambient occlusion, a high-poly's detail) into a texture. Game engines cannot run Cycles at play time, so a lot of
realism is *baked into images* ahead of time. In Blender: Render engine **Cycles**, Properties > **Bake** panel, choose the type (*Ambient Occlusion*,
*Diffuse*, *Normal*...), have an **image selected in the material's Image Texture node** (this is where the result lands) and press **Bake**. On a CPU, bake at
64 samples and 1024 pixels with the denoiser, and bake **only what you need**.

:::task id=bake title="Optional: bake ambient occlusion" xp=15 optional manual
Make a new 1024 image on a prop's material (an Image Texture node, selected but not connected), set the render engine to Cycles with 32 samples, set **Bake > Bake Type: Ambient
Occlusion** and press Bake. Use **Claim** when you finish.
hint: The image node must be the *active* node in the shader editor, or Blender has nowhere to put the result.
hint: A 1024 AO bake of one prop takes seconds to a minute on a CPU.
:::

## Exporting to Godot (and Kiln)

Game engines read **glTF** (`.glb` is the single-file form). It is the open standard and handles meshes, materials, textures and animation. Before exporting:

1. **Apply scale** (and rotation) on every object. Applied transforms avoid crushed or sideways models in the engine.
2. Keep **modifiers** that you want baked into the mesh. glTF exports the *evaluated* mesh.
3. Name your objects. Names carry into the engine's scene tree.
4. Check the **Principled BSDF** is plain: colour, metallic, roughness, normal, emissive. glTF understands those, but not arbitrary node trees. Procedural textures
   must be baked to images first.

The Blender add-on adds **Export to Godot / Kiln** to the Polycamp sidebar. It writes a `.glb`, uploads it to Polycamp, and Polycamp copies it into the **models/** folder of the Godot project
or Kiln game you choose in **Settings > Godot / Kiln export**. Textures from the Texture Lab go out the same way with **→ Godot / Kiln**, which also writes a ready
`StandardMaterial3D .tres` Godot can use directly.

:::task id=godot title="Export a model to Godot / Kiln" xp=15 manual
Choose a folder in the app's **Settings** (the Kiln buttons set it with one click). In Blender select the barrel and press **Export to Godot / Kiln** in the Polycamp
sidebar (**N**). A toast in the app confirms where the file went. Use **Claim** when it is there.
hint: No folder yet? Settings > Godot / Kiln export. Pick a Kiln game, or type the path of a Godot project.
hint: Open the exported .glb in Godot by dropping it into the FileSystem dock. It imports as a scene with materials.
:::

:::note tip title="Y is up, Z is up"
Blender's up is **Z**, Godot's is **Y**. The glTF exporter converts it (the *+Y Up* option is on by default), so a model standing in Blender stands in Godot. If it ever lies on its
back, that option is the first suspect.
:::

:::quiz id=q1 xp=5
Your wood material is a procedural node tree and you export glTF. What happens in the engine?
- It looks identical
- *The procedural nodes are lost, so bake them to images first
- The exporter converts nodes to code
explain: glTF only understands standard PBR inputs and image textures. Procedural nodes must be baked into image maps before export.
:::
