---
id: python
title: Blender Python in 15 Minutes
summary: Read the Info editor, run a script, and place ten cubes in a ring with a loop.
minutes: 15
scene: empty
keys: Alt+P, Ctrl+Space
tags: python, scripting
xp: 45
---
Every **solution script** you have peeked at in this course was Python using Blender's `bpy` module. You can read them now, and you can write small ones. You do not need to learn Python properly to benefit. A dozen idioms cover most
useful scripts, and the Blender interface will write much of the code for you.

## Three tools

1. **Info editor** (the *Scripting* workspace, bottom strip). Every operator you run is printed there as a line of Python, such as `bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))`. Add a cube, then look at the Info
   editor. Copy lines from it into a script. This is the secret.
2. **Python Console** (same workspace). A live prompt: type `bpy.data.objects` and press Enter.
3. **Text Editor**: write a script, run it with [[Alt+P]].

:::v 3
In **Blender 3.3** the Python console prompt already starts with `bpy`, `C` (context) and `D` (data) available.
:::

:::v 4+
In **Blender 4.x and 5.x** the same shortcuts apply: `C` is `bpy.context`, `D` is `bpy.data`. Press Ctrl+Space in the console for auto-complete.
:::

## The vocabulary

    import bpy                               # always the first line
    bpy.data.objects['Cube']                  # find a thing by name
    bpy.context.active_object                 # whatever is selected and active
    obj.location = (1, 2, 3)                  # set a property (tuples for vectors)
    obj.location.x += 0.5                     # change one axis
    bpy.ops.mesh.primitive_cube_add(...)      # run an operator (a menu action)
    for i in range(10):                       # repeat ten times: i is 0, 1, 2 ...
        ...

Hover any property in the UI with **Python Tooltips** switched on and it shows you the exact name to use. Turn them on once:

:::task id=tips title="Python tooltips" xp=6
Enable **Python Tooltips** (Edit > Preferences > Interface > Display) so every hover shows you the code name of what it controls.
check: prefs.show_tooltips_python :: Python Tooltips are on
hint: Preferences > Interface > Display > Python Tooltips. Hover over any field afterwards and read the bottom line.
:::
:::solve task=tips
bpy.context.preferences.view.show_tooltips_python = True
:::

## A ring of cubes

Ten cubes arranged in a ring of radius 3 is five lines. Open the **Scripting** workspace, make a **New** text, paste this and run it:

    import bpy, math
    for i in range(10):
        a = 2 * math.pi * i / 10
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(3 * math.cos(a), 3 * math.sin(a), 0.25))

The loop runs ten times. Each time `a` is the next angle around the circle. `cos` and `sin` convert an angle to x and y. Change the 10 to 24 and run it again for a denser ring.

:::task id=ring title="Ten cubes on a ring of radius 3" xp=20
Run a script that places **at least ten** cubes on a circle of **radius 3** around the origin.
check: sum(1 for o in meshes if abs((o.loc[0] ** 2 + o.loc[1] ** 2) ** 0.5 - 3) < 0.1) >= 10 :: Ten or more meshes sit on a ring of radius 3
hint: Use the loop above. Paste it into the Text Editor and press Alt+P (or the Run Script button).
hint: Scripting workspace > New (top of the Text Editor) > paste > Run Script. Errors print in the system console.
:::
:::solve task=ring
for i in range(10):
    a = 2 * math.pi * i / 10
    bm = bmesh.new()
    kit.add_box(bm, (0.5, 0.5, 0.5))
    kit.mesh_object('Ringcube_%02d' % i, bm, loc=(3 * math.cos(a), 3 * math.sin(a), 0.25))
:::

## Why bother

- **Repetition**: a hundred objects, a hundred renames, a hundred keyframes.
- **Batch jobs**: export every collection to its own file, rename textures, set every light to the same colour.
- **Add-ons**: an add-on is just a Python file with a few extra lines. The Polycamp Link add-on you installed in the first lesson is one.
- **Reading other people's work**: when a forum post says "run this script", you now know what you are doing.

:::note warn title="Never run scripts you do not understand"
A Python script can do anything on your computer, including deleting files. Read it first. Scripts from this course are plain `bpy` calls you can read in the Peek window.
:::

:::note tip title="Ask the Info editor"
When you cannot work out the code for something, do it with the mouse, then open the Info editor. The line it printed is usually 90 percent of the script you need.
:::

:::quiz id=q1 xp=5
Where do you find the Python for something you just did with the mouse?
- In the Preferences
- *In the Info editor, which logs each operator as a line of Python
- Blender cannot show that
explain: The Info editor records the bpy.ops calls behind your actions. Copy them straight into a script.
:::
