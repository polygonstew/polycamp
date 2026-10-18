---
id: guildmaster
title: Final Boss: Lantern Cabin at Dusk
summary: The final still, the final animation, and the trip to Godot.
minutes: 90
scene: starter:full-diorama
boss: true
keys: F12, Ctrl+F12
tags: boss, final
xp: 300
---
:::cubby shock
The final boss is not an enemy. It is a finished thing. Press F12 and, a few minutes later, you own a picture you made from a grey cube. I am a little emotional. I am also a cube. Go.
:::

## Brief

Deliver the full set:

1. **The final still**: Cycles, CPU, at least 1280 px wide. It appears in the Trophy Room.
2. **The animation**: the orbit with the flickering lantern, rendered to MP4 or a PNG sequence.
3. **The export**: your lantern, cabin or any prop as a **.glb** in your Godot or Kiln folder.
4. **Favourite it**: open the Trophy Room and star the render you like best.

Use your own scene from the earlier worlds if you have one, or the reference version if you want to concentrate on the render itself.

:::goal img=diorama-final.png
The reference still. Compare yours against it, and notice what you did differently.
:::

:::task id=still title="The still render" xp=80 untested
Render the still at the final settings ([[F12]]). It must be a Cycles render at least 1280 px wide.
check: rendered and render_last.engine == 'CYCLES' and render_last.res[0] >= 1280 :: A 1280 px+ Cycles render finished
hint: Use the Final settings from the polish lesson. Do not touch Blender while it renders.
:::

:::task id=anim title="The animated render" xp=100 untested
Render the animation (**Ctrl+F12**) with at least 48 frames. Output to MP4 or to a PNG sequence in a folder you can find.
check: rendered and render_last.frames >= 48 :: At least 48 frames rendered
hint: Time one frame first. Multiply by the frame count. If it is too long, lower the resolution percentage for the animation only.
:::

:::task id=prep title="Animation and orbit are set up" xp=40
The scene has an animated orbit (a rotating Empty or an animated camera) and a flickering light.
check: any(o.type == 'EMPTY' and 'rotation_euler' in o.anim.paths and len(o.anim.frames) >= 2 for o in objects) or any(o.type == 'CAMERA' and 'location' in o.anim.paths and len(o.anim.frames) >= 2 for o in objects) :: A rotating Empty or a moving camera
check: any(o.type == 'LIGHT' and 'NOISE' in o.anim.fmods for o in objects) :: A light with a Noise flicker
hint: Both come from World 8. Orbit: Empty with the camera parented, keys on Z rotation. Flicker: Noise modifier on a light's power curve.
:::
:::solve task=prep
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 96
pivot = bpy.data.objects.new('Orbit', None)
pivot.location = (0, 0.3, 0)
sc.collection.objects.link(pivot)
cam = sc.camera
cam.parent = pivot
cam.matrix_parent_inverse = pivot.matrix_world.inverted()
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert('rotation_euler', frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert('rotation_euler', frame=97)
ld = bpy.data.objects['Lantern_Light'].data
ld.keyframe_insert('energy', frame=1)
ld.keyframe_insert('energy', frame=96)
for fc in compat.iter_fcurves(ld.animation_data.action):
    m = fc.modifiers.new('NOISE')
    try:
        m.strength, m.scale = 30.0, 5.0
    except Exception:
        pass
:::

:::task id=godot title="Export to Godot or Kiln" xp=40 manual
In Blender select the lantern (or the whole cabin) and press **Export to Godot / Kiln** in the Polycamp sidebar. The model lands in the folder you set in the app's Settings. Open it in Godot. Claim it when you see it there.
hint: No folder set? App > Settings > Godot / Kiln export. Kiln games have a one-click button.
:::

:::task id=fav title="Star your favourite" xp=20 manual
Open the **Trophy Room** and star the render you are proudest of. Claim it.
hint: The star icon is on each card. A favourite is just a marker for you.
:::

:::note tip title="You finished"
When every task here is ticked, the campaign is complete and you earn the Guildmaster badge. The **Hotkey Dojo**, **Texture Lab** and **UV Lab** do not expire. Keep making things.
:::
