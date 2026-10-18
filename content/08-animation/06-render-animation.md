---
id: render-animation
title: Rendering Many Frames Without Crying
summary: The time budget, video versus image sequences, and a draft you can afford.
minutes: 12
scene: starter:full-diorama
keys: Ctrl+F12, F12, Esc
tags: render, cpu, animation
xp: 40
---
A still frame that takes two minutes is nothing. An animation of 72 frames at two minutes each is **2 hours and 24 minutes**. Almost everyone who learns Blender on a CPU hits this wall once, usually at 10 p.m. before a deadline.
Learn the maths now and you will not.

## The budget

    total time  =  frames  ×  seconds per frame

Seconds per frame depends on everything from the last world. So plan *backwards*. Decide how long you are willing to wait (say 30 minutes for a draft, one night for a final), and divide by the frame count to get the seconds per frame
you can spend. Then pick resolution and samples to fit.

Example for our 3 second, 72 frame orbit:

| Version | Size | Samples | Per frame | Total |
| --- | --- | --- | --- | --- |
| Test | 640 × 360 | 16 | about 8 s | 10 min |
| Draft | 960 × 540 | 24 | about 20 s | 24 min |
| Final | 1280 × 720 | 48 | about 70 s | 85 min |

(Typical numbers on a 4-thread laptop CPU. Time yours: render one frame and multiply.)

Cheaper options if even that is too much:

- Render at **half resolution** and upscale the video.
- Use **EEVEE** instead of Cycles. It does not use ray tracing, so frames take seconds, but quality and features differ. On Blender 4.2 and newer EEVEE needs a reasonably modern GPU/driver, so test it.
- **Persistent Data** (Render > Performance > Final Render): keeps scene data between frames so each frame skips setup. Free speed for animation.
- **Fewer frames**: an animation can run at 12 or 15 FPS for a stylised look.

## Video or frames?

- **Image sequence (PNG)**: one file per frame. If Blender crashes at frame 60 you do not lose frames 1 to 59, and Blender will skip frames that already exist (turn **Overwrite** off). This is what professionals do. Combine later in the **Video Sequencer** or ffmpeg.
- **Video (FFmpeg, MP4)**: one file. Convenient, but a crash can corrupt it. Fine for short drafts.

Set it in **Output properties > Output**: the *File Format* drop-down. For MP4 choose **FFmpeg Video**, Container **MPEG-4**, Video Codec **H.264**, quality **Medium**.

:::v 5
**Blender 5:** the Output panel has a new **Media Type** selector (Image, Multilayer Image, Video). Pick **Video** first, and the FFmpeg Video format and its encoding options appear.
:::

## The denoiser and flicker

Cycles' denoiser treats each frame separately, so slight differences between frames can shimmer when the video plays. More samples help. If it shimmers, increase samples a little rather than turning the denoiser off.

:::task id=range title="72 frames at 24 FPS" xp=8
Set the animation to **frames 1 to 72** at **24 FPS** (3 seconds).
check: render.frame_start == 1 and render.frame_end == 72 and render.fps == 24 :: Frames 1 to 72 at 24 FPS
hint: Output properties > Frame Range, and the Frame Rate drop-down. Or the Timeline's Start and End fields.
:::
:::solve task=range
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 72
sc.render.fps = 24
:::

:::task id=draft title="A draft you can afford" xp=10
Halve the render size (**Resolution 50%**) and keep samples at **32 or fewer**.
check: render.res_pct <= 50 and render.cy_samples <= 32 :: Half resolution with 32 samples or fewer
hint: Output tab > Resolution % = 50. Render tab > Sampling > Render = 24.
:::
:::solve task=draft
bpy.context.scene.render.resolution_percentage = 50
:::

:::task id=mp4 title="Output an MP4" xp=10
Set the output **File Format** to **FFmpeg Video** with the **MPEG-4** container.
check: render.format == 'FFMPEG' and render.ffmpeg_format == 'MPEG4' :: Output is an MPEG-4 video
hint: Output properties > Output panel > File Format: FFmpeg Video. Encoding panel appears; Container: MPEG-4.
:::
:::solve task=mp4
set_video_output('MPEG4')
:::

:::note tip title="Test one frame first"
Before committing to 72 frames, render **one** with [[F12]] at the final settings and note the time. Then use **Render > Render Animation** ([[Ctrl+F12]]). Press [[Esc]] to stop a render. Blender keeps the frames done so far when
you are using an image sequence.
:::

:::note warn title="Do not touch the machine"
A long render uses every core. Avoid heavy work (and Blender itself, if you can) while it runs, or you slow both. On a laptop, plug in the charger and make sure the fans can breathe.
:::

:::quiz id=q1 xp=5
A frame takes 25 seconds. How long do 72 frames take?
- 12 minutes
- *30 minutes
- 3 hours
explain: 72 × 25 seconds = 1800 seconds, which is 30 minutes.
:::

:::quiz id=q2 xp=5
Why do professionals prefer rendering to an image sequence instead of straight to MP4?
- MP4 files are not allowed in Blender
- *A crash does not lose the frames you finished, and you can resume where you stopped
- Image sequences render faster
explain: With frame files on disk, an interrupted render can continue. A half-written video file is usually unusable.
:::
