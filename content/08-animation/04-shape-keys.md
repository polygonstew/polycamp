---
id: shape-keys
title: Shape Keys: Morphing a Mesh
summary: Store a second shape for the same mesh and blend between them with a slider.
minutes: 10
scene: starter:shape-blob
keys: Tab
tags: animation, mesh
xp: 35
---
Transform keys move an object as a whole. To change the **shape** of a mesh itself (a face smiling, a blob squashing, a door bending open) you use **shape keys**. A shape key is a saved copy of your vertex positions. You blend between
the saved copy and the original with a slider from 0 to 1, and that slider can be keyframed like anything else.

How:

1. Select the mesh. Open **Object Data** properties (green triangle) > **Shape Keys**.
2. Click **+** once: it creates **Basis**, the original shape. Click **+** again for **Key 1**.
3. With *Key 1* selected, go into Edit Mode and move vertices. You are editing that shape only.
4. Back in Object Mode, drag the **Value** slider. The mesh blends from Basis toward Key 1.

You can add as many keys as you like (Smile, Frown, Squash, Stretch, Bulge...) and mix them. They are a big part of facial animation.

:::task id=keys title="Two shape keys: Squash and Stretch" xp=14
Give the **Blob** a Basis plus **two** more shape keys, and rename them **Squash** and **Stretch**. Edit their shapes: Squash flatter, Stretch taller.
check: any(o.name == 'Blob' and o.shape_keys >= 2 for o in meshes) :: Blob has two shape keys beyond the Basis
hint: Object Data tab > Shape Keys > + (Basis), + (Key 1), + (Key 2). Double-click to rename. Select a key, Tab into Edit Mode, then scale the mesh with S Z to squash or stretch.
hint: Edit Mode shows the active shape key. If the sliders are at 0 you see the Basis. Use the pin icon to preview one key alone.
:::
:::solve task=keys
ob = bpy.data.objects['Blob']
ob.shape_key_add(name='Basis')
sq = ob.shape_key_add(name='Squash')
st = ob.shape_key_add(name='Stretch')
for i, v in enumerate(ob.data.vertices):
    sq.data[i].co = (v.co.x * 1.25, v.co.y * 1.25, v.co.z * 0.55)
    st.data[i].co = (v.co.x * 0.8, v.co.y * 0.8, v.co.z * 1.4)
:::

## Animate the slider

The **Value** fields are ordinary numbers. Hover a Value, press [[I]] at frame 1 with Squash 1.0 (Stretch 0). At frame 12 key Stretch at 1.0 and Squash at 0. At frame 24 back to Squash. The blob pulses like it is breathing.

:::task id=anim title="Animate a shape key" xp=12
Key the **Value** of at least one shape key on two or more frames.
check: any(o.name == 'Blob' and any(p.startswith('key.') for p in o.anim.paths) for o in meshes) :: A shape key value is animated
hint: Hover over the Value slider and press I. Move the playhead, change the value, press I again.
:::
:::solve task=anim
ob = bpy.data.objects['Blob']
kb = ob.data.shape_keys.key_blocks
for frame, (a, b) in ((1, (1.0, 0.0)), (12, (0.0, 1.0)), (24, (1.0, 0.0))):
    kb['Squash'].value, kb['Stretch'].value = a, b
    kb['Squash'].keyframe_insert('value', frame=frame)
    kb['Stretch'].keyframe_insert('value', frame=frame)
:::

:::note tip title="Corrective trade-offs"
Shape keys store the position of every vertex, so each key costs memory proportional to the mesh. They only work while the vertex count stays the same: adding or deleting vertices after you have shape keys is the classic way to
break them. Finish your modelling, *then* make the keys.
:::

:::note cpu title="Where shape keys shine"
Faces, cloth-like bulges and any soft squash. For hinged things (doors, arms) use an **armature** instead. That is the next lesson.
:::

:::quiz id=q1 xp=5
You add a loop cut to a mesh that already has shape keys. What happens?
- The shape keys update automatically
- *They can break or be blocked, because every key must match the vertex count
- Nothing, shape keys are independent of the mesh
explain: Each shape key holds one position for every vertex. Change the vertex count and the keys no longer match. Finish modelling first.
:::
