---
id: link-up
title: Link Up
summary: Install the add-on, watch your own actions turn into checkmarks.
minutes: 8
scene: fresh
keys: F2, Ctrl+S, N
tags: setup
xp: 30
---
:::cubby
Hi. I'm **Cubby**, the default cube. Every Blender user deletes me within four seconds of opening the
program. Today we repair that relationship. Also: I'll be your guide, and I have *opinions*.
:::

## How Polycamp works

You read here. You work in **Blender**. A tiny add-on called **Polycamp Link** reads your scene a couple of
times a second and tells this page what it sees. When what you built matches a task, the checkbox
ticks by itself and you get XP. No screenshots, no honour system (well, only if you ask nicely).

If you have two monitors: put this page on one and Blender on the other. One monitor? Use the **Single**
layout in the top bar, or switch on *Show tasks in the 3D viewport* in the add-on preferences.

## Install the add-on

Download **polycamp_link.zip** from the *Link* button in the top bar (it already knows this server's
address). Then:

:::v 3
In Blender 3.3: **Edit > Preferences > Add-ons > Install...**, pick the zip, then tick the box next to
**System: Polycamp Link**.
:::

:::v 4+
In Blender 4.x or 5.x: **Edit > Preferences > Add-ons**, open the small **down arrow (v)** menu in the
top right, choose **Install from Disk...**, pick the zip, then make sure **Polycamp Link** is ticked.
:::

Now hover over the 3D viewport and press [[N]]. A **Polycamp** tab appears in the sidebar. If it says
*Linked to Polycamp* you are in.

:::task id=linked title="Connect Blender to Polycamp" xp=10
Enable the add-on and wait for **Linked to Polycamp** in the sidebar. The status dot in this page's
top bar turns green.
allow_initial:
check: snap.link != None :: Blender is talking to Polycamp
hint: Preferences > Add-ons. In 4.x use the little arrow menu > Install from Disk, not drag and drop.
hint: In the add-on's preferences, check that **Polycamp server** is the address in your browser's address bar.
hint: Still red? Open the add-on preferences and press **Reconnect**. A firewall on the app's PC can block port 8570.
:::

## Prepare the scene

Press **Set up scene** in the lesson bar above (or in the Blender sidebar). It gives you the factory
scene: Cube, Light, Camera. If you had unsaved work, it is first copied to `~/.polycamp/backups/`. Cubby
is not a monster.

:::task id=rename title="Give the cube a name" xp=15
Click the cube, press [[F2]] and rename it to **Cubby**.
check: any(o.name == 'Cubby' and o.type == 'MESH' for o in objects) :: A mesh object named Cubby
hint: Hover over the viewport, select the cube, press F2, type the name, Enter.
hint: Or double-click the name in the Outliner (top right list).
:::

:::task id=save title="Save the file" xp=15
Names mean nothing if Blender crashes. Press [[Ctrl+S]] and save as `polycamp-first.blend` somewhere you
will find it again.
check: file.saved and file.name != '' :: The file has been saved
hint: Ctrl+S opens the file browser the first time. Type a name at the bottom and press Save.
:::

:::quiz id=q1 xp=5
What does Polycamp Link do with your scene?
- Uploads your whole .blend file to a server
- *Reads a summary (objects, modifiers, materials, settings) and compares it to the tasks
- Nothing, it is just a bookmark to this website
explain: It only sends a small JSON summary to the server you configured. Your .blend never leaves your PC unless you export.
:::

:::note tip title="Your safety net"
Whenever a lesson sets up a scene for you, Polycamp first saves a copy of your current session to
`~/.polycamp/backups/`. The last 15 are kept.
:::

:::solve
cube = bpy.data.objects['Cube']
cube.name = 'Cubby'
bpy.ops.wm.save_as_mainfile(filepath='/tmp/polycamp-selftest.blend')
:::
