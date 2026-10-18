---
id: three-point
title: Key, Fill, Rim
summary: The three-light recipe behind most portraits, product shots and film frames.
minutes: 12
scene: starter:light-bench
keys: Shift+A, G
tags: lighting, composition
xp: 40
---
Almost every well-lit subject uses the same three ingredients:

- **Key**: the main light, the brightest, usually 30 to 60° off to one side and above the subject. It shapes the form.
- **Fill**: a weaker light from the other side that lifts the shadows so they are not pitch black. Soft and often cooler.
- **Rim** (or back light): a light from behind that traces an outline around the subject and separates it from the background.

![Three point lighting seen from above](img:three-point.svg)

**Ratios matter more than absolute values.** A key twice as bright as the fill is gentle and flat. Four times is dramatic. Eight times is moody and cinematic. The
rim is usually about as strong as the fill or a bit more, with a slight warm tint.

The camera in the bench scene sits at the front looking toward +Y. So "in front of the subject" means a negative Y, "behind" a positive Y, "left" a negative X.

:::task id=key title="Key light, front left, high" xp=10
Add an **Area** light **in front** (Y below −2), to the **left** (X below −1) and **above** the spheres (Z above 2), with a power of **at least 200 W**.
check: any(o.light.kind == 'AREA' and o.loc[0] < -1 and o.loc[1] < -2 and o.loc[2] > 2 and o.light.energy >= 200 for o in lights) :: A strong key area light front left and above
hint: Shift+A > Light > Area. Type the location into the N panel Item tab. An area light shines along its own -Z axis, so it needs aiming at the spheres.
hint: To aim it, press R and rotate by hand, or add a Track To constraint (Properties > Constraints tab) that targets the middle sphere, with Track Axis -Z and Up Axis Y.
:::
:::solve task=key
k = kit.add_light('AREA', 'Key', (-3.5, -4.5, 4.5), 400, (1.0, 0.95, 0.88), size=3)
kit.look_at(k, (0, 0, 0.9))
:::

:::task id=fill title="Fill from the other side, softer and cooler" xp=10
Add a second light on the **right** (X above 1) with a **lower power than the key** and a **cooler colour** (blue channel higher than red).
check: any(f.light.kind == 'AREA' and f.loc[0] > 1 and f.light.color[2] > f.light.color[0] and k.light.energy > f.light.energy for k in lights for f in lights) :: A cool fill on the right, dimmer than the key
hint: Duplicate the key (Shift+D), mirror its X position, drop the power to about a third and click the colour to a pale blue.
:::
:::solve task=fill
f = kit.add_light('AREA', 'Fill', (4, -3, 2), 120, (0.7, 0.82, 1.0), size=4)
kit.look_at(f, (0, 0, 0.9))
:::

:::task id=rim title="Rim light from behind" xp=10
Add a third light **behind** the spheres (Y above 2) and above them (Z above 2).
check: any(o.type == 'LIGHT' and o.loc[1] > 2 and o.loc[2] > 2 for o in lights) :: A light behind and above the subject
hint: Y positive is away from the camera. Put it up high and back, aimed toward the camera side of the spheres.
:::
:::solve task=rim
r = kit.add_light('AREA', 'Rim', (-1, 4.5, 3.5), 250, (1.0, 0.8, 0.6), size=2)
kit.look_at(r, (0, 0, 0.9))
:::

:::task id=three title="Exactly three lights" xp=6
Finish with **at least three lights** in the scene and a key that outshines the fill.
check: len(lights) >= 3 :: Three or more lights
hint: Do not stop at one light. Every light you can name a job for earns its place.
:::
:::solve task=three
pass
:::

:::note tip title="Break the rules"
Three-point is a starting point, not a law. A single hard sunset sun and a bit of sky light is a perfectly good setup (that is what our diorama uses). A rim
light on a dusk landscape is the setting sun. The point is to know *why* each light is there.
:::

:::cubby wink
When a render looks flat, add a rim light. When it looks harsh, add fill. When it looks muddy, remove something. It is not a very scientific profession, and I love it.
:::

:::quiz id=q1 xp=5
Which light does most to make the subject stand out from the background?
- Key
- Fill
- *Rim
explain: A rim light from behind creates a bright edge that separates the subject from what is behind it.
:::
