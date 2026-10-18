---
id: texture-lab
title: Texture Lab: Make It, Send It
summary: Generate a tileable wood texture in the app and have it appear on your barrel in Blender.
minutes: 15
scene: starter:barrel-uv
keys: Ctrl+V
tags: textures, comfyui
xp: 45
---
You have a barrel with proper UVs and a flat grey material. In this lesson the **Texture Lab** (in the top bar of this app)
makes the picture and delivers it.

## Three ways to get a texture

1. **Procedural (instant).** The Lab has generators for planks, bricks, cobbles, rust, shingles, grass, plaster. They are made of maths and
   they tile perfectly. Seeds and colours are yours to change. Start here.
2. **ComfyUI (AI, slow).** Type a description, and the Lab sends it to ComfyUI running on your machine. On this CPU a 512 pixel
   texture takes a couple of minutes in the *Fast* mode (an LCM model with 5 steps) and over ten in *Quality*. Start it, go
   model something, come back. It works through your own checkpoint, no cloud involved.
3. **Your own picture.** Drop a photo of a wall, a floor, bark or paper onto the preview, or paste it with [[Ctrl+V]].

AI and photos are not tileable by default. The Lab fixes that with **Make seamless**: it blends the picture with a half-shifted copy of itself so the
edges match. Check the **2×2 tile** preview. If you still see a grid of repeating blobs, change the seed or raise **blend**.

## Prompts that work for textures

- Ask for **flat, top-down, even lighting**: "seamless oak planks, top down, flat lighting, detailed grain".
- Name the **material and wear**: "mossy stone bricks", "rusty corrugated metal", "worn leather".
- Avoid objects, scenes and perspective. A texture is a surface, not a picture of something.

## Send it to Blender

In the Lab: pick a generator or prompt, press **Generate**, look at the maps, then **→ Blender (selected objects)** with the **barrel selected** in
Blender. The add-on downloads the images, builds a material (Image Texture nodes into a Principled BSDF) and assigns it. You will see the barrel
change.

:::task id=sent title="The barrel gets a textured material" xp=18
Use the **Texture Lab** to make a wood-planks texture and send it to the barrel. The barrel's material now draws its Base Color from an
**Image Texture**.
check: any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_IMAGE' in m.chain.base_color for m in [mat(n) for o in meshes if o.name == 'Barrel' for n in o.mats]) :: The barrel's Base Color comes from an Image Texture
check: any(i.source == 'FILE' and i.w >= 64 and i.w == i.h for i in images) :: A square image loaded from a file exists
hint: Open the Texture Lab, click Wood planks, then Generate. Select the barrel in Blender and press → Blender in the Lab's right column.
hint: Not linked? You can load the image by hand: Material tab, Base Color dot > Image Texture > Open, and pick a PNG from the Lab's saved sets.
:::
:::solve task=sent
ob = bpy.data.objects['Barrel']
path = make_test_image(bpy.app.tempdir + 'barrel_base.png', 'base_color')
m = matkit.build_pbr('Barrel_Wood', {'base_color': path}, tiling=(2.0, 2.0))
ob.data.materials.clear()
ob.data.materials.append(m)
:::

## Colour spaces: a trap with a quiet failure

Blender stores every image with a **colour space**. A colour picture (albedo) is **sRGB**: the numbers are display-encoded. A *data* map (normal,
roughness, height) must be **Non-Color**, meaning "do not touch these numbers". If a roughness map is left as sRGB, Blender gamma-corrects it and
the surface comes out wrong with no error message. The Lab-to-Blender button sets this for you, but you should know it when you load maps by hand.

:::task id=cs title="Albedo stays sRGB" xp=6
Check the image's colour space (Image Texture node > the dropdown under the filename): the **colour** map should be **sRGB**.
check: any(i.source == 'FILE' and i.colorspace == 'sRGB' for i in images) :: The colour image uses the sRGB colour space
hint: It is already correct unless you changed it. Data maps are the ones that need Non-Color.
:::
:::solve task=cs
pass
:::

## Tiling

An image on a small object is stretched across the UV 0 to 1 box once. On a big surface like a floor you want it to **repeat**. The **Tiling** slider next
to the send button sets the Mapping node's scale. A tileable texture repeating at tiling 4 on a wall gives 16 copies.

:::task id=ai title="Optional: cook a ComfyUI texture" xp=15 optional manual
In the Lab choose **ComfyUI (AI, slow)**, pick *Fast*, write "seamless dark oak planks, top down, flat lighting" and press **Cook texture**. Come back in a
few minutes and send it. Use **Claim** when you have done it.
hint: ComfyUI must be running (the Lab shows a green status line when it is). One job at a time; it will tell you if the CPU is busy.
:::

:::quiz id=q1 xp=5
You load a roughness map by hand and leave it as sRGB. What happens?
- Blender shows an error
- *The map is gamma corrected so the values are wrong, but nothing warns you
- Nothing, colour space only matters for colour images
explain: A roughness map holds numbers, not colours. sRGB decoding changes them, so the shine looks off. Set data maps to Non-Color.
:::
