---
id: camera
title: The Camera: Lens, Depth of Field, Framing
summary: Focal length, f-stop, where to put the subject, and why 18 mm makes everything look weird.
minutes: 12
scene: starter:bare-camera
keys: Numpad 0, Ctrl+Alt+Numpad 0, Shift+F
tags: camera, composition
xp: 40
---
The lit diorama is ready and nobody is looking at it. A Blender camera behaves like a real one, and the same rules of photography apply.

## Add and aim

**Shift+A > Camera** adds one, and the first camera you add becomes the **scene camera** (the one that renders). Look through it with [[Numpad 0]]. Instead of typing numbers, fly your viewport
to a good angle and press [[Ctrl+Alt+Numpad 0]]: *Align Camera to View*. Or in the sidebar View tab tick **Lock Camera to View**, then orbit with the camera frame border following you. Untick when done,
or you will drag the camera around when you meant to orbit.

## Focal length

The **Focal Length** (Object Data tab) is the zoom, in millimetres.

- **18 to 24 mm**: wide, dramatic, distorted at the edges. Interiors, big landscapes. Easy to overuse.
- **35 to 50 mm**: natural, close to the human eye. The all-rounder. Good for a diorama.
- **85 to 135 mm**: long, flattened perspective. Portraits and product shots, because long lenses make shapes look smaller and calmer.

:::task id=cam title="A camera with a natural lens" xp=10
Add a **camera** and make it the **scene camera**, with a focal length between **30 and 60 mm**.
check: scene.camera != None and any(o.type == 'CAMERA' and 30 <= o.camera.lens <= 60 for o in cams) :: A scene camera with a lens of 30 to 60 mm
hint: Shift+A > Camera, press Numpad 0 to see through it. Object Data tab (the green camera icon) > Lens > Focal Length.
hint: If scene.camera is empty, select the camera and press Ctrl+Numpad 0 to make it the active one.
:::
:::solve task=cam
kit.add_camera('Camera', (8.4, -10.6, 4.1), (0.2, 0, 1.45), 36.0)
:::

## Depth of field

Real lenses focus on one distance. Things nearer or farther blur, and the amount depends on the **aperture**, written as an **f-stop**. Small f-number (f/1.4, f/2.8) means a wide opening and strong blur. Big
f-number (f/11, f/16) means a pinhole and everything sharp. In Blender, tick **Depth of Field** on the camera, pick a **Focus Object** (easier than a distance) and set **F-Stop**. For a diorama
f/2.8 to f/5.6 gives a lovely toy-like background blur. It reads as *miniature*.

:::task id=dof title="Depth of field on the cabin" xp=14
Enable **Depth of Field**, set **F-Stop to 5.6 or less**, and give it a **Focus Object** (the cabin) or a focus distance.
check: any(o.type == 'CAMERA' and o.camera.dof and o.camera.fstop <= 5.6 and (o.camera.focus_object != None or o.camera.focus_distance > 0.5) for o in cams) :: Depth of Field on, f/5.6 or lower, with a focus target
hint: Camera data tab > Depth of Field. Click the Focus on Object field and pick Cabin_Walls. F-Stop is below it.
hint: Lower the F-Stop to see more blur. Press Numpad 0 and look at the Rendered viewport, or do a quick F12.
:::
:::solve task=dof
cam = bpy.context.scene.camera
d = cam.data.dof
d.use_dof = True
d.focus_object = bpy.data.objects['Cabin_Walls']
d.aperture_fstop = 4.0
:::

:::note cpu title="Depth of field and render time"
DOF costs very little in Cycles (it is just a different ray start), but it **adds noise** at the blurred areas, so you need more samples or the denoiser. In EEVEE it is
nearly free. For drafts you can switch it off and add it only to the final.
:::

## Composition in four ideas

1. **Rule of thirds.** Imagine the frame divided into a 3 × 3 grid. Put your subject on a line or an intersection instead of dead centre. In the camera data tab,
   *Viewport Display > Composition Guides > Thirds* draws it.
2. **Leading lines.** The path of stepping stones in the diorama pulls the eye toward the door.
3. **Foreground, middle, background.** Layers give depth. The fence in front, the cabin in the middle, the pines behind.
4. **Odd numbers and breathing room.** Leave space in the direction the subject faces or points.

Also set the **Clip Start** and **Clip End** sensibly (0.1 m and 100 m is fine) so nothing is cut off by accident.

:::task id=safe title="Keep the whole diorama in frame" xp=8 manual
Look through the camera ([[Numpad 0]]). The round base should fit inside the frame with a little margin. Use the **Thirds** composition guide. Use **Claim** when you are happy.
hint: Tilt the camera down slightly, 20 to 25 degrees from horizontal reads well. A camera at roughly the height of the roof looks natural.
:::

:::quiz id=q1 xp=5
For a flat, calm, "product photo" look which lens would you pick?
- 14 mm
- 24 mm
- *85 mm
explain: A long lens compresses perspective, so shapes look smaller, rounder and less distorted. A wide lens exaggerates depth and bends edges.
:::

:::quiz id=q2 xp=5
You want a strong blurry background. Which f-stop?
- f/16
- *f/2.8
- f/22
explain: Small numbers are wide apertures: shallow depth of field and a lot of blur.
:::
