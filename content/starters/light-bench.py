# The material test spheres with no lights at all, and a camera. For the lighting lessons.
kit.wipe()
kit.reset_scene_settings()
kit.make_world((0.02, 0.02, 0.03, 1), 1.0)
col = get_collection('Bench')
palette = {'Sphere_A': ('Red_Plastic', (0.8, 0.06, 0.05, 1), 0.3, 0.0), 'Sphere_B': ('Gold', (1.0, 0.77, 0.34, 1), 0.3, 1.0),
           'Sphere_C': ('Stone', (0.5, 0.5, 0.55, 1), 0.9, 0.0)}
for name, x in (('Sphere_A', -2.2), ('Sphere_B', 0.0), ('Sphere_C', 2.2)):
    bm = bmesh.new()
    kit.add_sphere(bm, 0.9, 48, 24)
    ob = kit.mesh_object(name, bm, collection=col, loc=(x, 0, 0.9), smooth=True)
    n, c, r, m = palette[name]
    ob.data.materials.append(kit.pbr(n, c, roughness=r, metallic=m))
bm = bmesh.new()
box_at(bm, (9, 5, 0.1), (0, 0, -0.05))
floor = kit.mesh_object('Floor', bm, collection=col)
floor.data.materials.append(kit.pbr('Floor', (0.35, 0.36, 0.4, 1), roughness=0.8))
kit.add_camera('Camera', (0, -7.5, 2.4), (0, 0, 0.9), 45, get_collection('Lights'))
kit.select_only(bpy.data.objects['Sphere_B'])
