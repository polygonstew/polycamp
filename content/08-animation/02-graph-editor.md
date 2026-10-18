---
id: graph-editor
title: The Graph Editor: Where the Polish Lives
summary: Interpolation, loops, and a Noise modifier that makes the lantern flicker.
minutes: 14
scene: starter:flicker-lamp
keys: T, Shift+E, Home
tags: animation, graph editor
xp: 45
---
Every keyed property becomes an **F-curve**: a graph of value against time. The **Graph Editor** (switch any area to it, or use the **Animation** workspace's top-left editor) shows those curves.
The horizontal axis is frames. The vertical axis is the value. The shape of the line *is* the motion: steep means fast, flat means still, a bump is a bounce.

Keys are the points on the curve. How the curve travels *between* them is its **interpolation**, which you change with [[T]] over the editor:

- **Bezier** (default): smooth ease in and out. Floaty. Great for camera moves, wrong for impacts.
- **Linear**: constant speed. Mechanical, perfect for a turntable.
- **Constant**: the value jumps at each key. Blinking lights, flip-book animation.
- **Back, Bounce, Elastic** and the *Easing* variants: overshoot and spring. Use sparingly.

The starter scene has the lantern and a point light inside it, with **one keyframe** on its power at frame 1. You will make it flicker the way a flame does: using a **modifier on the curve** instead of keying dozens of random values.

## Step 1: a second key

A curve needs at least two keys to be a curve at all. Go to frame 48 and key the Flame_Light's **Power** again (right-click the Power field > Insert Keyframe, or hover it and press [[I]]).

:::task id=keys title="A second key at frame 48" xp=8
Insert a second keyframe on the **Power** of **Flame_Light**, at frame 48.
check: any(o.type == 'LIGHT' and len(o.anim.frames) >= 2 for o in objects) :: The light's power has keys on two or more frames
hint: Select the light, scrub to frame 48, then hover the Power field in the Light properties and press I.
hint: A keyed field turns yellow (or green when it is on a keyframe).
:::
:::solve task=keys
ld = bpy.data.objects['Flame_Light'].data
bpy.context.scene.frame_set(48)
ld.energy = 120
ld.keyframe_insert('energy', frame=48)
bpy.context.scene.frame_set(1)
:::

## Step 2: linear, then loop

Press [[T]] in the Graph Editor, choose **Linear**. Now choose a **Cycles** modifier: select the curve, open the sidebar ([[N]]) > **Modifiers** tab > Add Modifier > **Cycles**. The animation repeats forever. [[Shift+E]]
is the shortcut for **Extrapolation Mode**, with *Make Cyclic* as a quick version of the same idea.

:::task id=linear title="Make the keys Linear" xp=8
Set the keyframe interpolation on the curve to **Linear**.
check: any(o.type == 'LIGHT' and 'LINEAR' in o.anim.interp for o in objects) :: The light's keys use Linear interpolation
hint: In the Graph Editor select the keys (A) and press T > Linear. The Dope Sheet works too: T over the keys.
:::
:::solve task=linear
ld = bpy.data.objects['Flame_Light'].data
for fc in compat.iter_fcurves(ld.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
:::

:::task id=cyc title="Loop it with a Cycles modifier" xp=10
Add a **Cycles** modifier to the Power curve so the animation repeats.
check: any(o.type == 'LIGHT' and 'CYCLES' in o.anim.fmods for o in objects) :: The light's curve has a Cycles modifier
hint: Graph Editor > select the curve in the channel list > N panel > Modifiers tab > Add Modifier > Cycles.
:::
:::solve task=cyc
ld = bpy.data.objects['Flame_Light'].data
for fc in compat.iter_fcurves(ld.animation_data.action):
    fc.modifiers.new('CYCLES')
:::

## Step 3: noise, the flicker engine

A real flame flickers randomly, and keying that by hand is a miserable afternoon. Instead, add a **Noise** modifier: it adds random wobble on top of any curve. Set:

- **Strength**: how big the wobble is. For a lantern at 120 W try 40.
- **Scale**: how slow or quick. Smaller is faster, so 3 to 8 frames per flicker looks lively.
- **Phase** and **Depth**: change the pattern or add finer detail.

The result is a believable, non-repeating shimmer from two keyframes and one modifier.

:::task id=noise title="Flicker with Noise" xp=14
Add a **Noise** modifier to the Power curve. Press play and watch the light.
check: any(o.type == 'LIGHT' and 'NOISE' in o.anim.fmods for o in objects) :: The light's curve has a Noise modifier
hint: Same Modifiers tab as before: Add Modifier > Noise. Raise Strength until the flicker is obvious, then back off.
hint: Strength 30 to 50 with Scale around 5 works for a 120 W lantern.
:::
:::solve task=noise
ld = bpy.data.objects['Flame_Light'].data
for fc in compat.iter_fcurves(ld.animation_data.action):
    m = fc.modifiers.new('NOISE')
    for k, v in (('strength', 40.0), ('scale', 5.0)):
        try:
            setattr(m, k, v)
        except Exception:
            pass
:::

:::note tip title="Dope Sheet or Graph Editor?"
The **Dope Sheet** shows keys as diamonds on a timeline. It is for *when*: slide, copy, delete and retime keys. The **Graph Editor** is for *how*: shape the curve. You will bounce between them, and the
Animation workspace has both.
:::

:::note cpu title="Modifiers are cheaper than keys"
A Noise modifier costs nothing to evaluate and nothing to store. A hand-keyed flicker is dozens of keyframes to maintain. When an animation can be described ("hover around 120 W with a wobble"), describe it.
:::

:::quiz id=q1 xp=5
Which interpolation gives constant speed, ideal for a turntable?
- Bezier
- *Linear
- Constant
explain: Bezier eases in and out, which makes a turntable surge and slow. Linear keeps the speed steady between keys.
:::

:::match id=m1 xp=6
Match the graph feature to the effect.
Bezier handles => Control how smoothly motion eases
Cycles modifier => Repeats the animation forever
Noise modifier => Adds random wobble to a curve
Constant interpolation => Jumps from one value to the next with no in-between
:::
