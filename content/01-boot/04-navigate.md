---
id: navigate
title: Getting Around
summary: Orbit, pan, zoom, ortho views and the shading toggles you will touch all day.
minutes: 8
scene: fresh
keys: Numpad 1, Numpad 5, Numpad ., Z
tags: viewport
xp: 25
---
You can already move around a 3D viewport, so this is a speed run. The only goal is to make sure the
habits that save time are already in your fingers.

## The three moves

| Action | Mouse | Without a middle button |
| --- | --- | --- |
| Orbit | hold [[MMB]] and drag | [[Alt+LMB]] drag (needs *Emulate 3 Button Mouse*) |
| Pan | [[Shift+MMB]] | [[Shift+Alt+LMB]] |
| Zoom | scroll wheel, or [[Ctrl+MMB]] | scroll wheel |

Zoom heads toward the middle of the screen by default. If you want it to zoom to the point under your
cursor, turn on **Zoom to Mouse Position** in Preferences > Navigation. Many people find it nicer for
detail work.

:::task id=orbit title="Wander about" xp=6 untested
Orbit, pan and zoom around the default scene a few times. Polycamp counts view changes, so give it six
or more.
check: view_moves >= 6 :: The view has moved
hint: Hover the viewport first. Navigation only works while the mouse is over it.
:::

## Views you will use constantly

The numpad is a set of camera presets. If you enabled *Emulate Numpad*, use the number row instead.

- [[Numpad 1]] front, [[Numpad 3]] right, [[Numpad 7]] top. [[Ctrl]] with the same keys gives back, left, bottom.
- [[Numpad 5]] switches between perspective and orthographic. Use **ortho** for modelling anything with
  straight lines. Perspective lies about proportions.
- [[Numpad .]] frames whatever is selected. [[Home]] frames everything. If you lose your object, these two keys find it.
- [[Numpad 0]] looks through the active camera.
- [[Numpad /]] isolates the selected object (Local View). Press again to come back.

:::task id=ortho title="Front view in orthographic" xp=6 untested
Press [[Numpad 1]] to look from the front. The header says *Front Orthographic*. Blender switched to ortho
for you because you chose an axis view.
check: ui.persp == 'ORTHO' :: The viewport is orthographic
hint: Use the View menu if you have no numpad: View > Viewpoint > Front.
:::

## Shading and X-ray

- [[Z]] opens the shading pie menu. Solid, Wireframe, Material Preview, Rendered.
- [[Shift+Z]] toggles wireframe straight away.
- [[Alt+Z]] toggles X-ray, which lets you see and select through things.

:::task id=wire title="Wireframe, then back" xp=6 untested
Switch the viewport to **Wireframe**. Look at the cube's edges. Leave it there for the check, then return
to Solid.
check: ui.shading == 'WIREFRAME' :: Viewport shading is Wireframe
hint: Press Z and pick Wireframe in the pie menu, or click the first of the four sphere icons in the header.
:::

:::note cpu title="On a CPU machine"
Stay in **Solid** while modelling. Switch to **Material Preview** to judge colour, and to **Rendered**
only when you mean it. Rendered view runs Cycles live and will eat the machine.
:::

:::keys id=k1 xp=8
Front view | Numpad 1
Toggle perspective and orthographic | Numpad 5
Frame the selected object | Numpad .
Shading pie menu | Z
:::

:::quiz id=q2 xp=5
You lost your object somewhere outside the screen. Which key brings everything back into view?
- Tab
- *Home
- Shift+C
explain: Home is "View All". Shift+C does the same and also resets the 3D cursor, which is usually what you want when you are completely lost.
:::
