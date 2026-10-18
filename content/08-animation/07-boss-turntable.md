---
id: boss-turntable
title: Boss: The Dusk Orbit
summary: Animate a slow orbit around the cabin while the lantern flickers, and render it to video.
minutes: 40
scene: starter:full-diorama
boss: true
keys: I, T, Ctrl+F12
tags: boss, animation
xp: 180
---
:::cubby shock
The diorama exists. The lights exist. The camera exists. Nothing moves, which makes me feel like a very expensive photograph. Fix that.
:::

## Brief

Make a short looping shot:

1. **A slow orbit.** The camera circles the cabin once. The easy way: put an **Empty** at the cabin's centre, parent the camera to it, and rotate the Empty 360° around **Z** over the clip.
   Linear interpolation, so the speed is steady.
2. **A flickering lantern.** The lantern's point light gets keyframes on its power and a **Noise** modifier (as in the Graph Editor lesson).
3. **A sensible length.** Between 48 and 144 frames. Three seconds is plenty.
4. **A draft-sized render.** No bigger than 1280 × 720 in effect, because you will render every frame.
5. **Output as MP4**, then render the animation with [[Ctrl+F12]].

Check the loop: the last frame should *almost* equal the first. The simplest trick for a clean loop is keying 0° on the first frame and 360° on the frame **after** your last, so no frame repeats.

:::task id=orbit title="An orbiting camera" xp=30
Something animated makes the camera orbit: an Empty with **rotation keys** (the camera parented to it), or keys on the camera's location. At least two frames.
check: any(o.type == 'EMPTY' and 'rotation_euler' in o.anim.paths and len(o.anim.frames) >= 2 for o in objects) or any(o.type == 'CAMERA' and 'location' in o.anim.paths and len(o.anim.frames) >= 2 for o in objects) :: A rotating Empty or a moving camera
hint: Shift+A > Empty. Move it to the cabin. Select the camera, then the Empty (active), Ctrl+P > Object (Keep Transform). Key the Empty's Z rotation at frames 1 and 97.
hint: The camera already has a Depth of Field focus object, so it stays sharp on the cabin as it orbits.
:::
:::solve task=orbit
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 96
sc.render.fps = 24
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
:::

:::task id=linear title="Constant speed" xp=15
The orbit uses **Linear** interpolation so the camera does not surge and slow.
check: any('LINEAR' in o.anim.interp for o in objects if o.type in ('EMPTY', 'CAMERA')) :: The orbit's keys are Linear
hint: Graph Editor or Dope Sheet: select the keys and press T > Linear.
:::
:::solve task=linear
pivot = bpy.data.objects['Orbit']
for fc in compat.iter_fcurves(pivot.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
:::

:::task id=flicker title="The lantern flickers" xp=30
A **light** has animated power with a **Noise** modifier on its curve.
check: any(o.type == 'LIGHT' and 'NOISE' in o.anim.fmods for o in objects) :: A light's power has a Noise modifier
hint: Select Lantern_Light, key its Power at frame 1 and frame 96 (I over the field), then Graph Editor > N > Modifiers > Add Noise.
:::
:::solve task=flicker
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

:::task id=length title="A sensible length" xp=15
The animation is between **48 and 144 frames** long.
check: 48 <= render.frame_end - render.frame_start + 1 <= 144 :: The clip is 48 to 144 frames
hint: Timeline Start and End fields. 96 frames at 24 FPS is 4 seconds.
:::
:::solve task=length
pass
:::

:::task id=video title="MP4 at a draft size" xp=20
Output to **MPEG-4** video, and keep the effective frame no larger than 1280 × 720.
check: render.format == 'FFMPEG' and render.ffmpeg_format == 'MPEG4' :: Output is an MPEG-4 video
check: render.res_x * render.res_y * render.res_pct * render.res_pct / 10000 <= 1280 * 720 + 1 :: Frames are 1280 × 720 or smaller
hint: Output properties > File Format > FFmpeg Video > Container MPEG-4. Resolution 960 × 540 at 100% is a good draft.
:::
:::solve task=video
set_video_output('MPEG4')
r = bpy.context.scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 960, 540, 100
:::

:::task id=render title="Render the animation" xp=70 untested
Press [[Ctrl+F12]] and wait. Go and do something else. It is worth it. The video file lands in the output folder.
check: rendered and render_last.frames >= 24 :: At least 24 frames rendered
hint: Set the Output path in the Output tab to somewhere sensible first (a folder you can find).
hint: To stop early press Esc in the render window. For a safe long render, use an image sequence and combine later.
:::

:::note tip title="Time it first"
Render frame 1 on its own and note the time. Multiply by your frame count. If the estimate is more than you wanted to spend, lower the resolution percentage or samples *now*, not at frame 40.
:::
