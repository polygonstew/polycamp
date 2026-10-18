# Writing lessons

A lesson is one Markdown file: `content/NN-world/NN-slug.md`. Worlds are folders with a `_world.md`.
The server reloads content by itself; the browser needs a refresh.

## Front matter

    ---
    id: extrude-inset          # unique, stable (progress is stored against it)
    title: Extrude and Inset
    summary: One sentence for the world page.
    minutes: 14
    scene: starter:tri-soup    # keep | fresh | empty | starter:<file in content/starters>
    boss: true                 # optional
    keys: E, I, Ctrl+B         # key chips in the side panel
    xp: 45                     # bonus XP for finishing (defaults to 25, 75 for bosses)
    ---

`scene` decides what **Set up scene** does: `fresh` = factory scene, `empty` = nothing, `starter:x` = run
`content/starters/x.py`, `keep` = use the learner's scene.

## Blocks

Prose is Markdown. `[[Shift+A]]` makes keycaps. `![](img:name.png)` shows `content/img/name.png`. Everything else is a
`:::block` ... `:::` section.

| Block | Use |
| --- | --- |
| `:::task id=x title="..." xp=15 [optional] [manual] [untested] [allow_initial]` | A checked task (see below) |
| `:::solve` / `:::solve task=x` | The solution script (whole lesson, or one task, run in task order) |
| `:::quiz id=q1 xp=5` | Question, then `- option` lines, correct ones as `- *option`; optional `explain:` |
| `:::order`, `:::match`, `:::fill`, `:::keys` | `1.` lines to sort; `left => right` pairs; `answer: a \| b`; `Action \| Combo` rows |
| `:::cubby [mood]` | The mascot speaks (happy, wink, smug, shock, think) |
| `:::note tip\|warn\|cpu\|info title="..."` | A callout. `cpu` is for slow-machine advice |
| `:::v 3`, `:::v 4+`, `:::v 3-4` | Text that only shows for those Blender versions |
| `:::reveal title="..."`, `:::goal img=x.png`, `:::img src=x.png` | Collapsible, reference picture with text, figure |

## Tasks

    :::task id=bevel title="Bevel by angle, 2 segments" xp=14
    Add a **Bevel** modifier below the Solidify...
    check: any(m.type == 'BEVEL' and m.p.segments >= 2 for o in meshes for m in o.mods) :: Bevel with 2+ segments
    hint: Add Modifier > Generate > Bevel.
    hint: A second, more specific hint. The third costs 2 gems.
    :::

- A task passes when **all** its `check:` lines pass. The text after ` :: ` is what the learner sees.
- No checks (or `manual`) means the learner presses **Mark done**.
- `untested`: depends on GUI state (workspace, viewport, a render); the verifier skips it.
- `allow_initial`: true from the start by design (for example "the add-on is connected").

### The check language

Python expressions over the snapshot; only a safe subset (see `server/checks.py`). Missing data reads as `None`, an error is `False`.

    objects, meshes, lights, cams, selected, active, mode, edit
    render, scene, world, materials, images, groups (node groups), ui, prefs, file, totals, cols (collections)
    mat('Name')        material by name        by_name('sub')   objects whose name contains it
    near(a, b, tol)    compare numbers or vectors      mods(o, 'BEVEL')    an object's modifiers of a type
    used('mesh.loopcut_slide', 2)   operators run since the lesson started (note_op() in solutions)
    view_moves, sel_changes, rendered, render_secs, render_last, ver

Objects expose `name, type, loc, rot (degrees), scale, dims, wbox (world bounds), world_loc, parent, children, collections,
mods [{type, p: {...}}], mats, verts, edges, faces, quads, n3, ngons, seams, boundary_edges, smooth_faces, uv, uv_area,
volume, anim {keys, paths, frames, interp, fmods}, light {...}, camera {...}`, and more: `docs/SNAPSHOT.md`.

## Solutions and the verifier

Every lesson with checks needs a solution so the verifier can run it:

    blender -b --factory-startup --python tools/verify_in_blender.py -- [lesson-id ...]

For each lesson it builds the start scene, requires that **no** check is already true (otherwise the lesson would give
free XP), runs the solution, and requires every check to pass. With per-task `:::solve task=x` blocks each task's checks
are evaluated right after its own solution, so tasks can pass in different states (Edit Mode on, then off).
Run it on 3.3, 4.5 and 5.x before merging content.

Solutions use the data API and bmesh, not `bpy.ops`, so they work from a timer and headless. The helpers in
`content/lib` (`kit`, `build_lantern`, `mat_wood`, `build_diorama` ...) are available.

## Hotkey cards

`content/dojo/*.md`: `## Deck name`, then `Action | Combo | optional tip` lines.
