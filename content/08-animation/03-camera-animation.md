---
id: camera-animation
title: Moving the Camera
summary: Track To, a fly-in, and a focus pull: three camera moves that make a still scene feel directed.
minutes: 14
scene: starter:full-diorama
keys: I, Ctrl+T
tags: animation, camera
xp: 45
---
A camera move can turn a static diorama into a shot. Three techniques cover most of what you need.

## Track To: always look at the cabin

Keyframing a camera's *rotation* to follow a subject is painful, because every position change needs a matching rotation change. A **Track To** constraint solves that: the camera automatically aims at a target
object whatever it does.

1. Add an **Empty** ([[Shift+A]] > Empty > Plain Axes), name it `Look_Target`, and move it to the middle of the cabin (about 0, 0.3, 1.4).
2. Select the camera, open the **Constraints** tab (the object-with-chain icon), Add Object Constraint > **Track To**.
3. Set **Target** to `Look_Target`, **Track Axis** to **−Z**, **Up** to **Y**. (These two settings are the camera's convention, and the cause of most "why is my camera spinning" questions.)

:::task id=track title="A camera that tracks the cabin" xp=14
Give the **camera** a **Track To** constraint pointed at an Empty in the cabin.
check: any(c.type == 'TRACK_TO' and c.target != None for o in cams for c in o.cons) :: The camera has a Track To constraint with a target
hint: Constraints tab > Add Object Constraint > Track To. Pick the Empty as Target. Track Axis -Z, Up Axis Y.
hint: Move the Empty with G to change what the camera looks at, without touching the camera.
:::
:::solve task=track
sc = bpy.context.scene
tgt = bpy.data.objects.new('Look_Target', None)
tgt.location = (0, 0.3, 1.4)
sc.collection.objects.link(tgt)
cam = sc.camera
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
:::

## A fly-in

With Track To in place, animating the camera is just animating its **location**. Key it at frame 1 far and high, and at frame 96 close and lower. The tracking keeps the cabin centred the whole way.

:::task id=fly title="Fly the camera in" xp=14
Key the camera's **location** at two different frames (for example frame 1 and frame 96), moving it noticeably closer to the cabin by the end.
check: any('location' in o.anim.paths and len(o.anim.frames) >= 2 for o in cams) :: The camera's location is keyed on two or more frames
hint: Frame 1: place the camera far and high, press I > Location. Frame 96: closer and lower, I again. Also set End frame to 96.
hint: Switch interpolation to Linear (T in the Graph Editor) if the move surges and slows too much.
:::
:::solve task=fly
sc = bpy.context.scene
sc.frame_end = 96
cam = sc.camera
cam.location = (9.5, -12.0, 5.5)
cam.keyframe_insert('location', frame=1)
cam.location = (5.5, -7.0, 2.6)
cam.keyframe_insert('location', frame=96)
:::

## Focus pull

Depth of field is a property like any other, so you can animate it. A **focus pull** shifts focus from something near to something far while the shot plays, the classic "look here now" cinema gesture. Animate the camera's
**Focus Distance** (or its **F-Stop**), right-click the field and choose Insert Keyframe.

:::task id=focus title="Pull the focus" xp=10
Key the camera's **depth of field** (focus distance or F-stop) on at least two frames.
check: any(any(p.startswith('data.dof') for p in o.anim.paths) for o in cams) :: The camera's depth of field is animated
hint: Select the camera, scrub to frame 1, hover Focus Distance and press I. Go to frame 96, change the value, press I.
:::
:::solve task=focus
cam = bpy.context.scene.camera
d = cam.data.dof
d.use_dof = True
d.focus_object = None
d.focus_distance = 14.0
cam.data.keyframe_insert('dof.focus_distance', frame=1)
d.focus_distance = 8.0
cam.data.keyframe_insert('dof.focus_distance', frame=96)
:::

:::note tip title="Follow Path and parenting"
For a smooth orbit, parent the camera to an **Empty** at the centre and rotate the Empty. Or add a **Follow Path** constraint that pulls the camera along a Bezier circle. Both are better than keying a circle by hand.
The boss lesson uses the Empty method.
:::

:::note cpu title="Preview cheaply"
Switch the viewport to Solid or Material Preview and play the animation with [[Space]]. Use the **Playback** popover in the timeline to enable *Sync > Frame Dropping* so a slow machine still shows real timing.
:::

:::quiz id=q1 xp=5
Why use a Track To constraint on the camera?
- It makes the render faster
- *The camera aims at the target automatically, so you only animate its position
- It is required to render an animation
explain: Aiming by hand means keying rotation to match every move. Track To does that for you.
:::
