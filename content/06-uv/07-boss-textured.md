---
id: boss-textured
title: Boss: Textured Props Set
summary: Give a barrel, a crate and a plank real image materials with proper maps.
minutes: 25
scene: starter:uv-props
boss: true
keys: Shift+A
tags: boss, textures
xp: 130
---
:::cubby shock
Three props, one barrel, one crate, one plank. Each needs to look like something. You have the Texture Lab, a UV map on each prop, and a clean view of
what makes a surface convincing. No new tools in this boss. Just do it properly.
:::

## Brief

Build a small **prop set**: the **Barrel** in oak, the **Crate** in weathered pine and the **Plank** in dark stained timber. Use different presets or seeds so they look related but
not identical. Send full sets (colour, normal, roughness, height) with the Texture Lab.

Quality checks the pros apply, and so does this boss:

- Every prop has its **own image-based Base Color**.
- At least two props use a **normal map**, correctly wired through a Normal Map node.
- Data maps are **Non-Color**.
- Nothing bigger than **1024**.
- Roughness comes from an image too, so shine varies across the surface.

:::goal img=prop-set.png
The prop set in the reference render. Your wood can be anything: grey ash, red mahogany, blue-painted pine.
:::

:::task id=color title="Image colour on all three" xp=25
All three props (**Barrel**, **Crate**, **Plank**) have a Base Color fed by an Image Texture.
check: sum(1 for o in meshes if o.name in ('Barrel', 'Crate', 'Plank') and any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_IMAGE' in m.chain.base_color for m in [mat(n) for n in o.mats])) >= 3 :: Three props have image-based colour
hint: Select a prop in Blender, make a set in the Texture Lab, press → Blender. Repeat for each prop.
:::

:::task id=normals title="Normal maps on two of them" xp=25
At least two props have a **Normal Map** node in their material (the Texture Lab sets include one).
check: sum(1 for o in meshes if o.name in ('Barrel', 'Crate', 'Plank') and any(m != None and m.chain != None and m.chain.normal != None and 'NORMAL_MAP' in m.chain.normal for m in [mat(n) for n in o.mats])) >= 2 :: Two props use a Normal Map
hint: Keep the normal checkbox ticked in the Lab before sending.
:::

:::task id=cs title="Data maps are Non-Color" xp=15
At least two images use the **Non-Color** colour space.
check: sum(1 for i in images if i.colorspace == 'Non-Color') >= 2 :: Two or more Non-Color images
hint: The Lab's button sets this. If you loaded maps by hand, set Color Space on the Image Texture node.
:::

:::task id=size title="Within the texture budget" xp=15
Every image is **1024 px or smaller** and there are at least **three different image files**.
check: len({i.path for i in images if i.source == 'FILE'}) >= 3 :: Three or more different image files
check: all(i.w <= 1024 and i.h <= 1024 for i in images if i.source == 'FILE') :: None bigger than 1024
hint: The Lab produces 384 to 512 px images. If you scaled one up by hand, scale it back down in the Image editor.
:::

:::task id=rough title="Shine that varies" xp=10
At least two props have their **Roughness** driven by an image.
check: sum(1 for o in meshes if o.name in ('Barrel', 'Crate', 'Plank') and any(m != None and m.chain != None and m.chain.roughness != None and 'TEX_IMAGE' in m.chain.roughness for m in [mat(n) for n in o.mats])) >= 2 :: Two props have image-driven roughness
hint: Keep the rough checkbox ticked in the Texture Lab before you press the Blender button.
:::

:::solve
for i, name in enumerate(('Barrel', 'Crate', 'Plank')):
    files = {k: make_test_image(bpy.app.tempdir + '%s_%s.png' % (name.lower(), k), k, 64 + 16 * i) for k in ('base_color', 'normal', 'roughness', 'height')}
    m = matkit.build_pbr(name + '_PBR', files, tiling=(1.0, 1.0))
    ob = bpy.data.objects[name]
    ob.data.materials.clear()
    ob.data.materials.append(m)
:::
