# A typical messy first project: default names, everything in one collection, and leftover unused materials.
kit.wipe()
kit.reset_scene_settings()
kit.make_world()
col = bpy.context.scene.collection
names = ['Cube', 'Cube.001', 'Cube.002', 'Sphere', 'Sphere.001', 'Cylinder', 'Cone', 'Torus']
for i, n in enumerate(names):
    bm = bmesh.new()
    kit.add_box(bm, (1, 1, 1)) if n.startswith('Cube') else (kit.add_sphere(bm, 0.5, 16, 8) if n.startswith('Sphere') else kit.add_cylinder(bm, 0.5, 1, 16))
    ob = kit.mesh_object(n, bm, collection=col, loc=(i * 1.6 - 5.6, 0, 0.5))
    ob.data.materials.append(kit.pbr('Material.%03d' % i, (0.3 + 0.08 * i, 0.4, 0.6, 1)))
for i in range(5):
    kit.pbr('Old_Test_%d' % i, (0.9, 0.2, 0.2, 1))            # zero users: these are the orphans
kit.add_light('SUN', 'Sun', (-4, -5, 6), 3.0, (1, 0.9, 0.8), size=3)
kit.add_camera('Camera', (0, -9, 3), (0, 0, 0.5), 40)
kit.select_only(bpy.data.objects['Cube'])
