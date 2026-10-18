---
id: final-assembly
title: Make It Yours
summary: Add your own texture, your own object and your own touches to the finished diorama.
minutes: 45
scene: starter:full-diorama
keys: Shift+A, M
tags: final, composition
xp: 100
---
The reference scene is competent and slightly anonymous. Everyone who built it from this course has the same one. This lesson turns it into *yours*, with three kinds of change.

## 1. Your own texture

Every surface in the starter is procedural. Go to the **Texture Lab** and make **something specific** for the cabin walls: oak planks, weathered grey boards, painted red timber (try the ComfyUI option for this one: *"red painted timber planks, chipped paint, top down, flat lighting"*).
Send it to the **Cabin_Walls** object so it replaces the procedural wood. Use **Tiling 3** or so, since the walls are big.

:::task id=lab title="Image-textured cabin walls" xp=25
**Cabin_Walls** uses an **Image Texture** for its Base Color (from the Texture Lab or any picture you like).
check: any(o.name == 'Cabin_Walls' and any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_IMAGE' in m.chain.base_color for m in [mat(n) for n in o.mats]) for o in meshes) :: Cabin_Walls has an image-based Base Color
hint: Texture Lab: pick a preset or cook with ComfyUI, Generate, then select Cabin_Walls in Blender and press → Blender. Tiling 3.
hint: Not linked? In the Shader Editor add Image Texture, open a PNG from ~/polycamp textures or any image, connect Color into Base Color.
:::
:::solve task=lab
ob = bpy.data.objects['Cabin_Walls']
files = {k: make_test_image(bpy.app.tempdir + 'walls_%s.png' % k, k, 128) for k in ('base_color', 'normal', 'roughness')}
m = matkit.build_pbr('Cabin_Walls_Image', files, tiling=(3.0, 3.0))
ob.data.materials.clear()
ob.data.materials.append(m)
:::

## 2. Your own object

Add **one thing** that is not in the reference scene. A bench by the door, a stack of firewood, a barrel from the prop set, a wheelbarrow, a bird house on a pole, a swing. Give it a proper name, materials and put it in the right collection. It should
add story: why is it there, who left it?

:::task id=own title="One object of your own" xp=25
Add at least one mesh that is not part of the library scene (anything with a name not starting with Cabin, Ground, Rock, Pine, Fence, Path, Grass, Lamp or PostLantern), with at least one material.
check: sum(1 for o in meshes if not o.name.startswith(('Cabin', 'Ground', 'Rock', 'Pine', 'Fence', 'Path', 'Grass', 'Lamp', 'PostLantern')) and len([n for n in o.mats if n]) >= 1) >= 1 :: A new, textured mesh of your own exists
hint: Reuse what you know: a box with a bevel and a wood material is a bench in five minutes. The Barrel from World 6 works too.
:::
:::solve task=own
bm = bmesh.new()
box_at(bm, (1.2, 0.35, 0.08), (0, 0, 0.45))
for sx in (-0.5, 0.5):
    box_at(bm, (0.08, 0.3, 0.45), (sx, 0, 0.225))
bench = kit.mesh_object('Bench', bm, collection=get_collection('Props'), loc=(-1.9, -2.4, 0.0))
add_bevel(bench, 0.01)
bench.data.materials.append(mat_wood('Bench_Wood'))
:::

## 3. Make it feel lived in

Details that sell the story, cheap to add: a light in the window you can see from the camera, a path of stepping stones (the reference has it), a lantern that glows warm on the ground around it, a tree stump, scattered pebbles with Geometry Nodes, grass tufts at
the base of the walls. Take the 'odd numbers and uneven spacing' rule.

:::task id=orga title="Your object lives in a Props collection" xp=15
Put your new object into a collection called **Props**, so the Outliner stays readable.
check: any(c.name == 'Props' and c.objects >= 1 for c in cols) :: A collection named Props holds your object
hint: Select your object, press M, choose New Collection, name it Props.
:::
:::solve task=orga
pass
:::

:::task id=story title="A reason for the object" xp=10 manual
Write one sentence (in your head or in a text file) about why your object is there. That is the difference between an arrangement and a scene. Claim it.
hint: "Someone just finished chopping firewood and went in for tea" is a perfectly good story.
:::

:::note tip title="Save a milestone"
Save as `lantern-cabin-v1.blend` now. You will probably want to go back to this version when you over-polish in the next lesson.
:::
