---
id: texture-paint
title: Painting Straight onto the Model
summary: Texture Paint mode, a brush, and the one rule that saves your work: save the image.
minutes: 12
scene: starter:barrel-uv
keys: F, Shift+F, Ctrl+Z, Alt+S
tags: textures, painting
xp: 40
---
Sometimes you do not want a tiled image at all. You want a scuff here, a stain there, a hand-painted band around a barrel. **Texture Paint**
mode lets you paint on the 3D model, and Blender writes the brush strokes into an image through the UV map. So: a good UV map first
(the barrel has one), then paint.

## Set up

1. Select the barrel. Switch to the **Texture Paint** workspace (or the mode menu in the viewport > Texture Paint).
2. If the material has no image yet, Blender offers an **Add Texture Paint Slot** with a base colour. Choose **Base Color**, size **1024**, and
   name it. That creates a blank image and wires it into the material for you.
3. Pick the **Draw** brush, set a colour, and paint.

Brush controls you will use constantly: [[F]] changes radius (drag, click), [[Shift+F]] changes strength, [[X]] swaps the main and
secondary colours, [[Ctrl+Z]] undoes a stroke.

:::task id=slot title="Add a 1024 paint slot" xp=14
Create a **1024 × 1024** image for painting and connect it as the barrel's **Base Color** (Texture Paint mode will do both with *Add Texture Paint Slot > Base Color*).
check: any(i.w == 1024 and i.h == 1024 for i in images) :: A 1024 by 1024 image exists
check: any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_IMAGE' in m.chain.base_color for m in [mat(n) for o in meshes if o.name == 'Barrel' for n in o.mats]) :: The barrel's Base Color uses an image
hint: Modes menu > Texture Paint. In the Tool Settings panel (sidebar, Tool tab) click Texture Slots > Add Texture Paint Slot > Base Color.
hint: By hand: Shader editor > Image Texture > New (1024 x 1024), plug Color into Base Color.
:::
:::solve task=slot
ob = bpy.data.objects['Barrel']
im = bpy.data.images.new('Barrel_Paint', 1024, 1024)
m = ob.data.materials[0]
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = im
nt.links.new(tex.outputs['Color'], compat.sock(bsdf, 'base_color'))
:::

:::task id=paint title="Make your mark" xp=10
Paint something on the barrel: a band, a scribble, your initials. The image is now **modified** (the Image editor shows an asterisk).
check: any(i.dirty for i in images) :: An image has unsaved painted changes
hint: Pick a bright colour first, left-click-drag on the barrel. You can paint through the UV Lab too: it shows the unwrapped layout so you can aim.
hint: If nothing appears, check the active paint slot in the Texture Slots panel is the image you created.
:::
:::solve task=paint
im = bpy.data.images['Barrel_Paint']
px = [0.2, 0.5, 0.9, 1.0] * (1024 * 1024)
im.pixels.foreach_set(px)
im.update()
:::

## The trap: unsaved images vanish

A painted image lives **only in memory** until you save it. Close Blender without saving the image and your painting is gone, even if you saved the `.blend`.
In the Image Editor use **Image > Save** ([[Alt+S]]), or **Image > Pack** to embed it in the `.blend` file. The Image Texture node shows a small warning when an image has unsaved changes.

:::task id=keep title="Save it: pack or save the image" xp=10
Make sure the painted image is not just in memory: **Image > Pack** (or save it to a file).
check: any(i.w == 1024 and (i.packed or i.path != '') for i in images) :: The 1024 image is packed or saved to disk
hint: Image editor, Image menu > Pack. Or Image > Save As and choose a folder.
:::
:::solve task=keep
im = bpy.data.images['Barrel_Paint']
im.pack()
:::

:::note tip title="Paint in the UV Lab"
The app's **UV Lab** is an alternative route: **Get UV layout** pulls the layout from Blender, you paint colour blocks over it, optionally let ComfyUI add detail with an *img2img*
pass, and **Apply as this object's texture** sends it back. It is quicker for flat block colours and handy when you cannot paint in 3D.
:::

:::note cpu title="Brush tips for a slow machine"
Paint at **1024**, not 4096. Use a soft brush with a lower strength and build up. If the viewport lags, switch from Material Preview to **Solid** shading with *Texture* colour set in the shading popover.
:::

:::quiz id=q1 xp=5
You painted on the barrel, saved your .blend, and reopened it. The painting is missing. What went wrong?
- The brush was too soft
- *The painted image was never saved or packed, it only lived in memory
- Blender deletes paint on file save
explain: A .blend stores a reference to the image, not unsaved pixels. Save or pack the image (Image menu) before you close Blender.
:::
