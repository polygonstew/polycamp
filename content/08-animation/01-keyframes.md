---
id: keyframes
title: Keyframes and the Timeline
summary: Insert a key, move in time, insert another, and let Blender do the in-betweens.
minutes: 12
scene: starter:anim-ball
keys: I, Alt+I, Space, Left, Right
tags: animation
xp: 40
---
A **keyframe** says: at this frame, this property has this value. The frames in between are **interpolated** (calculated) for you. Two keys is an animation. That is genuinely all there is.

At the bottom of the Layout workspace is the **Timeline**. The vertical blue line is the **playhead** showing the current frame. Drag in the number strip to **scrub**. The numbers at the right of its header are the
**start and end frame**. The scene's **frame rate** (FPS) lives in the Output properties: 24 for film, 30 for video, 60 for smooth games.

Time basics: 24 frames a second means 48 frames is 2 seconds. Keep animations short while you learn.

## Setting a range

By default the scene runs frames 1 to 250. Almost nobody needs that. For this lesson we want 2 seconds.

:::task id=range title="Frames 1 to 48 at 24 FPS" xp=8
Set the **Start** to 1, **End** to 48 and **Frame Rate** to 24 (Output properties > Frame Range and Format).
check: render.frame_start == 1 and render.frame_end == 48 and render.fps == 24 :: Frames 1 to 48 at 24 FPS
hint: Timeline header: Start and End fields. Output tab > Format > Frame Rate.
hint: End defaults to 250. Click the End field and type 48.
:::
:::solve task=range
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 48
sc.render.fps = 24
:::

## Insert keys

Select the **Ball**. Go to frame 1. Press [[I]] over the viewport and choose **Location** (4.1 and newer ask which properties via a pop-up menu, with a default set of channels; older versions
key everything in the chosen category). A yellow diamond appears in the timeline. Jump to frame 24, move the ball up and to the right, press [[I]] again. Jump to 48, bring it back down to the floor on the other side. Press [[Space]] to play.

The ball glides in a smooth curve because Blender's default interpolation is **Bezier** (ease in and out). That "floaty" quality is why beginner animation looks slow and mushy. The next lesson fixes it.

:::task id=keys title="Three location keys: frames 1, 24 and 48" xp=14
Animate the **Ball**'s location with keyframes at **frames 1, 24 and 48**. Make frame 24 the high point of a bounce, a metre or so above the start.
check: any(o.name == 'Ball' and 'location' in o.anim.paths and all(f in o.anim.frames for f in (1, 24, 48)) for o in meshes) :: Ball has location keys at frames 1, 24 and 48
hint: Select the ball, scrub to frame 1, press I > Location. Frame 24, move the ball up and across, press I again. Frame 48, drop it, I.
hint: If I opens a long menu (older Blender), pick Location. In newer versions, a small menu offers Location, Rotation, Scale.
:::
:::solve task=keys
ball = bpy.data.objects['Ball']
for frame, loc in ((1, (-3, 0, 0.5)), (24, (0, 0, 2.5)), (48, (3, 0, 0.5))):
    ball.location = loc
    ball.keyframe_insert('location', frame=frame)
:::

:::task id=scale title="Squash and stretch: scale keys too" xp=10
Add **scale** keys: squashed flat (Z around 0.6) on frames 1 and 48 where it hits the floor, and its normal shape (1, 1, 1) at frame 24.
check: any(o.name == 'Ball' and 'scale' in o.anim.paths for o in meshes) :: Ball has scale animation
hint: At frame 1 press S Z 0.6, then I > Scale. At frame 24 reset with Alt+S and key it again.
:::
:::solve task=scale
ball = bpy.data.objects['Ball']
for frame, s in ((1, (1.2, 1.2, 0.6)), (24, (1, 1, 1)), (48, (1.2, 1.2, 0.6))):
    ball.scale = s
    ball.keyframe_insert('scale', frame=frame)
:::

:::note tip title="Which keys to use"
[[I]] inserts. [[Alt+I]] removes the keys on the current frame. Right-click a property field and choose *Insert Keyframe* to key just one number, or tick **Auto Keying** (the record dot in the Timeline)
to key everything you change as you go. Auto keying is fast and dangerous, so know where the button is when you forget it is on.
:::

## The 12 principles, abbreviated

Animation is mostly taste, but a few old rules go a long way:

- **Squash and stretch**: things that move fast stretch along the motion. Things that hit squash. It sells weight.
- **Anticipation**: a small movement opposite to the main one (a crouch before the jump).
- **Ease in, ease out**: motion starts slowly, gets fast and settles slowly. Real things have mass.
- **Arcs**: living things move along curves, not straight lines.
- **Timing**: fewer frames feel fast and light. More frames feel slow and heavy.

:::quiz id=q1 xp=5
Your animation is 72 frames at 24 FPS. How long is it?
- 2 seconds
- *3 seconds
- 72 seconds
explain: Seconds = frames divided by frame rate. 72 / 24 = 3.
:::

:::match id=m1 xp=6
Match the keys.
Insert a keyframe => I
Remove the keyframe on this frame => Alt+I
Play or pause => Space
Step one frame forward => Right arrow
:::
