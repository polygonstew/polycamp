---
id: pro-habits
title: How Pros Actually Work
summary: References, checklists, budgets and the unglamorous habits that make work fast.
minutes: 10
scene: keep
keys: Shift+Alt+A
tags: workflow, habits
xp: 30
---
You now know the whole pipeline: model, material, texture, light, animate, render. This lesson is not about a tool. It is what working artists do that beginners do not, and it is cheap to start.

## Always start with references

Nobody models a lantern from memory. They gather **reference images** first: photos of real lanterns, a drawing of the layout, a mood image for the lighting. In Blender add them in the viewport with
**Add > Image > Reference** and use them in the front and side orthographic views. Sit them behind the model and lower their opacity in the Empty's data panel.

:::task id=ref title="Add a reference image" xp=8 manual
Add any image as a **reference** (Add > Image > Reference) in a Blender scene and look at it through an orthographic view. Claim it when done.
hint: Shift+A > Image > Reference. Pick any image file. Then set Numpad 1 to see it in front view.
:::

## Work from big to small

1. **Block out** (silhouette and proportion). Squint test.
2. **Secondary shapes** (windows, doors, major parts).
3. **Details** (bevels, bolts, wear).
4. **Materials** and **textures**.
5. **Light** and **camera**.
6. **Polish**: the last 10 percent that takes 50 percent of the time.

Resist the pull to polish a detail before the blockout reads well. A beautifully bevelled door in the wrong place is wasted work.

## Habits worth building

- **Save versions** before anything risky. Disk is cheap, regret is not.
- **Name as you go**, because "later" never arrives.
- **Apply scale** (Ctrl+A) before modifiers and before exporting.
- **Check from every angle** (Numpad 1, 3, 7), not only the one you modelled from.
- **Use the Statistics overlay** to watch your face count.
- **Test render small and often.** A 480 × 270 draft at 16 samples is enough to judge composition and light.
- **Ask what the camera sees.** Do not model what nobody will ever see.
- **Take breaks.** Fresh eyes find the problem in 10 seconds that tired eyes missed for an hour.

## Your CPU checklist

- Model in **Solid**, preview in Material Preview, render in Cycles with the denoiser.
- Subdivision at **1 to 2** in the viewport, higher only for the render.
- Textures **1024**, one 2048 for the hero.
- Many copies? **Instances** and **linked duplicates**.
- Test at **50% resolution** and half the samples, then do the full render once.
- Animations: time **one frame** first, then multiply.

## Where to go next

- Study **real objects** and model them again and again. A mug, a chair, a boot, a kettle.
- Learn **sculpting** (Sculpting workspace) for organic things and **retopology** to turn sculpts into clean quads.
- Learn **UV painting** workflows and layered materials for characters.
- Try **simulation**: cloth, rigid bodies and fluids are all in the Physics tab.
- Make **one small thing a week** and put it in a folder. A year of that is a portfolio.
- Take your models into **Godot** (Kiln can carry them) and make something playable.

:::note tip title="Keep the Dojo going"
Ten minutes a day of Hotkey Dojo does more than an hour once a week. Blender is a keyboard instrument. The people who are fast are the people who stopped looking for menus.
:::

:::task id=plan title="Plan your next project" xp=10 manual
Write down (anywhere) three things you want to make after this course, and the first one to start. Claim it when it is on paper.
hint: Small is good. A lantern, a rock, a tree. Anything you can finish in a weekend.
:::

:::quiz id=q1 xp=5
Which comes first when building a new object?
- Fine details
- *A rough blockout that reads correctly
- Materials
explain: Big shapes first. If the proportions are wrong, no detail or material will save it, and changing a blockout takes seconds.
:::

:::order id=o1 xp=6
Put the usual order of work in sequence.
1. Gather references
2. Block out the main shapes
3. Add secondary shapes and detail
4. Materials and textures
5. Lighting and camera
6. Render and polish
:::
