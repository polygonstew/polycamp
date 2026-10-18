# A vase profile drawn as a loose polyline (vertices and edges, no faces) in the XZ plane, for the Screw modifier.
cube, light, cam = kit.default_scene()
bpy.data.objects.remove(cube, do_unlink=True)
col = bpy.context.scene.collection.children['Collection']
me = bpy.data.meshes.new('Profile')
pts = [(0.0, 0, 0.0), (0.55, 0, 0.0), (0.6, 0, 0.1), (0.45, 0, 0.5), (0.3, 0, 0.95), (0.35, 0, 1.3), (0.5, 0, 1.55), (0.48, 0, 1.6)]
me.from_pydata(pts, [(i, i + 1) for i in range(len(pts) - 1)], [])
me.update()
prof = bpy.data.objects.new('Profile', me)
col.objects.link(prof)
prof.data.materials.append(kit.pbr('Vase', (0.8, 0.45, 0.25, 1), roughness=0.3))
kit.select_only(prof)
cam.location = (3.4, -5.5, 2.6)
kit.look_at(cam, (0, 0, 0.8))
