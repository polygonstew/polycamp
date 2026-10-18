---
id: armature
title: Bones, Weights and a Swaying Tube
summary: A three-bone armature, vertex weights, and a pose you can key.
minutes: 16
scene: starter:rig-tube
keys: Shift+A, Tab, Ctrl+Tab, R
tags: animation, rigging
xp: 50
---
A **rig** is a skeleton you can pose so that you can animate a mesh by bending bones instead of moving vertices. We keep it to the smallest useful case: a three-bone chain, enough to make a sapling sway, a rope swing or a tail wag. The
ideas are identical to a full character.

## Three parts

1. The **Armature**: an object containing **bones**. Each bone has a head, a tail and a parent. Bone chains pass motion from parent to child, so bending the bottom bone swings the ones above it.
2. **Vertex groups** with **weights**: for each vertex, how strongly each bone pulls it (0 to 1). A vertex near a joint is shared between the two bones, which is what makes the bend smooth.
3. The **Armature modifier** on the mesh, pointing at the armature. This is the link that makes the mesh follow the bones.

The fast way to get all three at once is to select the mesh, then the armature (active), and press [[Ctrl+P]] > **With Automatic Weights**. Blender builds the vertex groups from bone distance. It works well on simple shapes.

## Build it

1. [[Shift+A]] > Armature > Single Bone. In Edit Mode ([[Tab]]) select the bone's tip and **extrude** ([[E]]) twice moving straight up so you have three bones stacked along the tube, each about a metre.
2. Name them `Bone0`, `Bone1`, `Bone2`.
3. Object Mode. Select the **Tube**, ctrl-click the **armature**, [[Ctrl+P]] > With Automatic Weights.

:::task id=bones title="An armature with three bones" xp=12
Add an armature with **three bones** running up the tube.
check: any(o.type == 'ARMATURE' and o.armature.bones >= 3 for o in objects) :: There is an armature with three or more bones
hint: Shift+A > Armature > Single Bone, Tab, select the tip, E Z 1 twice. The bones should follow the tube's height of 3 m.
hint: The bone's head and tail must lie roughly along the tube's axis, or the weights will be uneven.
:::
:::solve task=bones
sc = bpy.context.scene
arm = bpy.data.armatures.new('Rig')
rig = bpy.data.objects.new('Rig', arm)
sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
prev = None
for i in range(3):
    eb = arm.edit_bones.new('Bone%d' % i)
    eb.head, eb.tail = (0, 0, i * 1.0), (0, 0, i * 1.0 + 1.0)
    if prev:
        eb.parent = prev
        eb.use_connect = True
    prev = eb
bpy.ops.object.mode_set(mode='OBJECT')
:::

:::task id=bind title="Bind the tube with weights" xp=16
Bind the **Tube** to the armature so it has vertex groups for the bones and an **Armature modifier**.
check: any(o.name == 'Tube' and o.vgroups >= 3 for o in meshes) :: The Tube has three or more vertex groups
check: any(o.name == 'Tube' and any(m.type == 'ARMATURE' for m in o.mods) for o in meshes) :: The Tube has an Armature modifier
hint: Click the Tube, Ctrl+click the armature so it is the active one, Ctrl+P > With Automatic Weights.
hint: If Blender says bone heat weighting failed, your mesh has overlapping faces or is non-manifold, or the bones sit outside the mesh.
:::
:::solve task=bind
tube = bpy.data.objects['Tube']
rig = bpy.data.objects['Rig']
for i in range(3):
    vg = tube.vertex_groups.new(name='Bone%d' % i)
    for v in tube.data.vertices:
        w = max(0.0, 1.0 - abs(v.co.z - (i + 0.5)))
        if w > 0.01:
            vg.add([v.index], w, 'REPLACE')
m = tube.modifiers.new('Armature', 'ARMATURE')
m.object = rig
tube.parent = rig
:::

## Weights, by eye

Select the tube, switch to **Weight Paint** mode ([[Ctrl+Tab]] with the armature selected too), and click each bone. Red is full influence, blue is none. Smooth gradients across joints bend nicely. A hard red-to-blue
edge makes a crease. Paint with the brush or use **Weights > Smooth**.

## Pose and animate

Select the armature and switch to **Pose Mode** ([[Ctrl+Tab]]). Select a bone and rotate it with [[R]]. The tube bends. Key the rotation with [[I]] at different frames to sway.

:::task id=pose title="Sway: pose and key the bones" xp=14
In **Pose Mode** rotate the bones and insert keyframes on **at least two frames** (for example frame 1 leaning left, frame 24 leaning right).
check: any(o.type == 'ARMATURE' and o.anim.keys >= 4 for o in objects) :: The armature has four or more rotation keys
hint: Ctrl+Tab for Pose Mode, click Bone1, R X 15 Enter, then I > Rotation. Frame 24: R X -30, I. Repeat for Bone2.
:::
:::solve task=pose
rig = bpy.data.objects['Rig']
for name in ('Bone1', 'Bone2'):
    pb = rig.pose.bones[name]
    pb.rotation_mode = 'XYZ'
    for frame, ang in ((1, 0.25), (24, -0.4), (48, 0.25)):
        pb.rotation_euler = (ang, 0, 0)
        pb.keyframe_insert('rotation_euler', frame=frame)
:::

:::note tip title="Clean up before you rig"
Rigging works best on a clean, closed mesh with **applied scale**. Edge loops across the joints (the tube's rings) let it bend without pinching. Put at least two loops at every joint you plan to bend.
:::

:::quiz id=q1 xp=5
Which piece makes the mesh actually follow the bones?
- The vertex group names
- *The Armature modifier pointing at the armature
- The Track To constraint
explain: Vertex groups say how strongly each bone pulls each vertex, but the Armature modifier is what applies the bones' movement to the mesh.
:::

:::match id=m1 xp=6
Match the rigging term.
Bone => A segment you can pose that passes motion to its children
Weight => How strongly a bone pulls a vertex (0 to 1)
Pose Mode => Where you rotate bones to animate
Armature modifier => Links the mesh to the skeleton
:::
