---
id: light-types
title: Four Kinds of Light
summary: Point, Sun, Spot and Area: what each one is for and which numbers matter.
minutes: 12
scene: starter:light-bench
keys: Shift+A
tags: lighting
xp: 40
---
The test bench has three spheres, a floor, a camera and **no lights**. The world is nearly black, so everything is too. Time to put the sun in.

Add a light with **Shift+A > Light**. Blender has four types:

| Type | Behaves like | Strength unit | Good for |
| --- | --- | --- | --- |
| **Point** | a bare bulb | watts (W) | lanterns, candles, lamps |
| **Sun** | the sun, parallel rays | W/m², a plain number, 1 to 5 | daylight, moonlight, hard sources |
| **Spot** | a torch with a cone | watts | stage lights, streetlamps, headlights |
| **Area** | a softbox or window | watts | soft studio light, windows, big glowing panels |

Two ideas decide how a light looks:

- **Size.** A big light is soft (gentle shadow edges). A tiny light is hard. Size is the **Radius** of a point light, the **Size** of an area light, the
  **Angle** of a sun. The sun is far away, but its angle matters: 0.5° is crisp, 5° is soft.
- **Distance.** Light fades with the *square* of the distance (except the sun, which has no falloff). Double the distance, quarter the light.

Also: **colour**. Warm light (orange) for sunset and candles, cool (blue) for shade and moonlight. Mixing a warm key with a cool fill is the oldest trick in film.

:::task id=sun title="A warm sun" xp=10
Add a **Sun** light with **Strength 2 or more**, and a warm colour (red channel higher than blue).
check: any(o.light.kind == 'SUN' and o.light.energy >= 2 and o.light.color[0] > o.light.color[2] for o in lights) :: A warm Sun of strength 2 or more
hint: Shift+A > Light > Sun. In the light's Object Data tab (green bulb icon) set Strength and click the Color swatch.
hint: Orange: R 1.0, G 0.65, B 0.35.
:::
:::solve task=sun
sun = kit.add_light('SUN', 'Sun', (-5, -4, 6), 3.0, (1.0, 0.65, 0.35), size=3)
kit.look_at(sun, (0, 0, 0.8))
:::

:::task id=point title="A small warm point light" xp=10
Add a **Point** light of **at least 100 W** and a **Radius of 0.2 or less** (a hard little bulb).
check: any(o.light.kind == 'POINT' and o.light.energy >= 100 and o.light.radius <= 0.2 for o in lights) :: A Point light of 100 W or more with a small radius
hint: Shift+A > Light > Point. Power is in watts; radius is under Power in the same panel.
:::
:::solve task=point
kit.add_light('POINT', 'Bulb', (-1, -1.5, 2.5), 300, (1.0, 0.75, 0.45), size=0.1)
:::

:::task id=spot title="A spot with a cone" xp=10
Add a **Spot** light with a **Spot Size under 60°** and a **Blend** above 0.1 so the edge of the cone is soft.
check: any(o.light.kind == 'SPOT' and o.light.spot_deg < 60 and o.light.spot_blend > 0.1 for o in lights) :: A Spot with a narrow cone and a soft edge
hint: Shift+A > Light > Spot. Spot Shape panel has Size and Blend.
:::
:::solve task=spot
ld = bpy.data.lights.new('Spot', 'SPOT')
ld.energy = 600
ld.spot_size = math.radians(45)
ld.spot_blend = 0.3
ob = bpy.data.objects.new('Spot', ld)
ob.location = (2, -3, 5)
bpy.context.scene.collection.objects.link(ob)
kit.look_at(ob, (0, 0, 0.8))
:::

:::task id=area title="A big soft area light" xp=10
Add an **Area** light with a **Size of 2 m or more**: big enough to wrap around the subject.
check: any(o.light.kind == 'AREA' and o.light.size >= 2 for o in lights) :: An Area light 2 m or larger
hint: Shift+A > Light > Area. Size is in the Light tab. Rotate it so its flat face points at the spheres.
:::
:::solve task=area
a = kit.add_light('AREA', 'Softbox', (0, -4, 4), 500, (1, 1, 1), size=3)
kit.look_at(a, (0, 0, 0.8))
:::

:::note cpu title="Which lights cost what?"
In Cycles all lights are cheap to *evaluate*, but **large soft** lights are noisier than small ones, so they need more samples or the denoiser. A tiny point light
gives the cleanest result per sample. Many lights are fine, because modern Cycles picks which lights matter at each point.
:::

:::quiz id=q1 xp=5
You want a hard, crisp shadow from a lamp. What do you change?
- *Make the light smaller (lower radius or size)
- Raise the strength
- Change its colour to white
explain: Shadow softness comes from how big the source looks from the object. Smaller source, sharper shadow edge.
:::

:::match id=m1 xp=6
Match the source to the light.
Late afternoon sunshine => Sun, warm colour, low angle
A window on a cloudy day => Large area light, cool white
A candle on a table => Small warm point light
A theatre spotlight => Spot with a narrow cone
:::
