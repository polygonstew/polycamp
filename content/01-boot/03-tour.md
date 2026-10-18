---
id: tour
title: The Room
summary: Editors, workspaces and how to lay Blender out for two monitors.
minutes: 10
scene: fresh
keys: N, T, Ctrl+Space, Ctrl+PageUp
tags: interface
xp: 30
---
Blender's window is a wall of rectangles. Each rectangle is an **area**, and each area shows one
**editor**. The 3D Viewport is an editor. So is the Outliner, the Timeline, the Properties panel and the
spreadsheet nobody opens until they need it. The editor type lives in the **top-left corner** of every
area, a little icon with a drop-down.

That one idea explains most of the interface. Any area can become any editor. Want a second 3D view?
Change the Timeline into one.

## The default layout, read left to right

- **3D Viewport** (centre). Where you see and touch the scene.
- **Outliner** (top right). Every object, grouped in collections. Click to select, double-click to rename.
- **Properties** (bottom right). A column of tabs for the active object: Render, Output, Scene, World,
  Object, Modifiers, Material, and so on. Which tabs show depends on what is selected.
- **Timeline** (bottom). Animation scrubbing. We will use it later.
- **Header** over each area. In the viewport it holds the **mode** selector (Object, Edit, Sculpt...),
  the shading buttons and the overlay toggles.
- **Toolbar** ([[T]]) on the left and **Sidebar** ([[N]]) on the right of the viewport, both hidden on demand.

:::quiz id=q1 xp=5
You want a second 3D viewport next to the first. What do you do?
- Open the Add menu and pick "Viewport"
- *Split an area (drag a corner) and set its editor type to 3D Viewport
- Install an add-on
explain: Every area can show any editor. Drag from a corner to split, then use the editor type menu in the top-left of the new area.
:::

## Workspaces: tabs along the top

The tabs called **Layout, Modeling, Sculpting, UV Editing, Texture Paint, Shading, Animation, Rendering,
Compositing, Geometry Nodes, Scripting** are **workspaces**. Each one is just a saved arrangement of
areas plus a starting mode. Switch with a click or with [[Ctrl+PageUp]] and [[Ctrl+PageDown]].

You can change any of them and the changes stay. Break one? Right-click the tab and there is no
"reset", but you can duplicate it before experimenting.

:::task id=ws title="Visit the Modeling workspace" xp=8 untested
Click the **Modeling** tab at the top. Notice the viewport went into Edit Mode on its own. Workspaces can
do that.
check: ui.workspace == 'Modeling' :: The Modeling workspace is open
hint: The tabs are across the top of the whole window, not inside the viewport.
:::

:::task id=ws2 title="Now the Shading workspace" xp=8 untested
Switch to **Shading**. You get a node editor, a file browser and a viewport in Material Preview. Come
back to **Layout** afterwards.
check: ui.workspace == 'Shading' :: The Shading workspace is open
hint: If Material Preview feels slow on your machine, switch the viewport back to Solid while you look around.
:::

## See what the scene costs

Statistics tell you how heavy the scene is. Turn them on now, because you will watch the face count
climb for the rest of the course.

:::task id=stats title="Turn on Statistics" xp=8 untested
In the viewport header open the **Overlays** drop-down (two overlapping circles) and tick **Statistics**.
Numbers for objects, vertices, edges, faces and triangles appear in the corner.
check: ui.stats :: Statistics overlay is on
hint: Header > Overlays drop-down > Statistics. In 4.x it is in the Overlays popover, first column.
:::

## Two monitors

You have two screens, so use them. In Blender, **Window > New Main Window** gives you a second Blender
window that shares the same file. Put the Outliner and Properties there and give the viewport the whole
first screen. Or ignore this and keep Blender on one screen and Polycamp on the other, which is what this
course assumes.

:::task id=win optional title="Open a second Blender window" xp=6 untested
Try **Window > New Main Window**. Move it to the other monitor if you like. Close it again when you
have seen enough.
check: ui.windows >= 2 :: Blender has two windows open
hint: It is under the Window menu in the top bar. Close it with the usual window close button.
:::

:::keys id=k1 xp=8
Open or close the Sidebar | N
Open or close the Toolbar | T
Maximize the area under the mouse | Ctrl+Space
Next workspace tab | Ctrl+PageDown
:::

:::cubby wink
Maximize with Ctrl+Space and the area under your mouse fills the whole window. Press it again to go
back. I use it every five minutes and will pretend I always knew.
:::
