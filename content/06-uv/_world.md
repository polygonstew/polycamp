---
id: uv
title: UV Isle
tagline: Unfold the model, paint on the flat copy, wrap it back. Textures, ComfyUI and Godot.
emoji: ▦
color: #b07ad8
project: Textured props for the diorama
---
Procedural materials only go so far. When you need a *specific* look (planks with knots, a weathered door, a mossy stone) you
need an **image**, and to put an image on a 3D object you must tell Blender how to flatten the surface onto it. That flattening
is a **UV map**: for every point on the model, a coordinate (U, V) on a flat picture.

This is the world where the app's **Texture Lab** and **UV Lab** earn their keep. The Lab makes tileable textures (procedurally,
with AI through ComfyUI on your CPU, or from a photo), derives the extra maps a modern material needs (normal, roughness, height,
ambient occlusion) and sends them straight into a Blender material. The UV Lab pulls a model's UV layout out of Blender so you can
paint on it.

By the end you will have textured props, exported one as glTF into your Godot or Kiln folder, and know why game artists spend half
their lives looking at checkerboards.
