---
id: seams-pack
title: Seams That Hide, Islands That Fit
summary: Where to cut, how to pack the islands, and how to catch stretching with a checker.
minutes: 12
scene: starter:barrel-raw
keys: Ctrl+E, U
tags: uv
xp: 40
---
A seam is invisible on a perfect texture and a glaring line on a bad one. A texture painted across a seam will not match unless
you paint across it on purpose. So seams go where they cannot be seen, or where the texture would change anyway.

## Where to cut

- **Along hard edges.** The place two surfaces meet at an angle is already a visual break.
- **On the underside or the back**, out of the camera's sight.
- **Where materials change.** Metal band to wood, handle to blade.
- **On cylinders: one straight seam down the length and one around each cap.** That is the barrel's
  three-part layout: a long strip for the side and two discs for the lid and bottom.

The barrel in the starter has no UVs. Look at it as a tin can: peel the label off (one vertical seam), pop off the lid and bottom
(a seam around each rim) and everything lies flat.

:::task id=cyl title="Seams on a barrel" xp=12
Mark seams around **both rims** of the barrel (the two circles) and **one vertical edge** between them. In Edge mode, [[Alt+LMB]] on a rim
edge selects the whole loop. Then **Edge > Mark Seam**.
check: any(o.name == 'Barrel' and o.seams >= 20 for o in meshes) :: The barrel has 20+ seam edges (two rims plus one side seam)
hint: Alt+click on an edge of the top circle selects the loop. Shift+Alt+click the bottom circle. Then Ctrl+E > Mark Seam.
hint: Add the vertical seam by clicking one single vertical edge and marking it too.
:::
:::solve task=cyl
ob = bpy.data.objects['Barrel']
bm = bmesh.new()
bm.from_mesh(ob.data)
for e in bm.edges:
    zs = {round(v.co.z, 3) for v in e.verts}
    e.seam = len(zs) == 1 or all(abs(v.co.y) < 1e-4 and v.co.x > 0 for v in e.verts)
bm.to_mesh(ob.data)
bm.free()
:::

:::task id=pack title="Unwrap and pack tight" xp=14
Unwrap everything ([[A]], [[U]] > Unwrap) and arrange the islands so the layout covers **60% or more** of the 0 to 1 tile, all inside it. In
the UV Editor, **UV > Pack Islands** does the arranging.
check: any(o.name == 'Barrel' and o.uv_oob == 0 and o.uv_area >= 0.6 for o in meshes) :: The barrel's UVs are inside the tile and cover 60%+
hint: In the UV Editor select all (A) then UV > Pack Islands. Raise the Margin a little so islands do not touch.
hint: 60% is generous. Round discs and one long strip pack comfortably around 70% or more.
:::
:::solve task=pack
ob = bpy.data.objects['Barrel']
bm = bmesh.new()
bm.from_mesh(ob.data)
uv_cylinder(bm)
bm.to_mesh(ob.data)
bm.free()
:::

## Packing and texel density

When you have several islands, **pack** them close together. Wasted space in the tile is wasted pixels. Also keep a **consistent texel density**: the
same number of pixels per metre across the object, so one part is not sharp while another is blurry. If one island is far smaller than its
neighbours on the surface, scale it up in the UV Editor ([[S]]) until the checker squares match.

:::note cpu title="Texture sizes"
Texture memory grows with the *square* of the size. A 2048 × 2048 RGBA texture is 16 MB, a 4096 is 64 MB, and with colour, normal and
roughness maps that adds up fast. On a machine with 11 GB of RAM, **1024 is the working size** and 2048 is for the hero object.
:::

## The checker

Add a **UV Grid** image to the barrel's material and read it like a map. Squares stay square? Good. Squares smear into rectangles? Add a
seam or relax the island.

:::task id=checker title="Put a UV Grid on the barrel" xp=10
Make a **New Image** of type **UV Grid** (at least 512 px) and wire it through an **Image Texture** node into the barrel's **Base Color**.
check: any(i.generated and i.w >= 512 for i in images) :: A generated UV Grid image of 512 px or more exists
check: any(m != None and m.chain != None and m.chain.base_color != None and 'TEX_IMAGE' in m.chain.base_color for m in [mat(n) for o in meshes if o.name == 'Barrel' for n in o.mats]) :: The barrel's Base Color comes from an Image Texture
hint: Shader editor: Shift+A > Texture > Image Texture, click New, set Generated Type to UV Grid, Width and Height 1024.
hint: Connect the node's Color output to the Principled BSDF Base Color.
:::
:::solve task=checker
ob = bpy.data.objects['Barrel']
im = bpy.data.images.new('UV_Grid', 1024, 1024)
im.generated_type = 'UV_GRID'
m = ob.data.materials[0]
nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = im
nt.links.new(tex.outputs['Color'], compat.sock(bsdf, 'base_color'))
:::

:::quiz id=q1 xp=5
Where is the best place for a seam on a coffee mug?
- Straight across the front where everyone looks
- *Down the back, opposite the handle
- Seams never matter
explain: A seam is easiest to hide out of sight. A vertical line on the back of the mug is hard to notice, and a wooden floor or a handle often covers it anyway.
:::
