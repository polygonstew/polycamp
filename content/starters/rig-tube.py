# A tall tube with plenty of rings, to rig with a three-bone armature (a sapling, a rope, a tail).
kit.wipe()
kit.reset_scene_settings()
kit.make_world((0.1, 0.11, 0.14, 1), 1.0)
bm = bmesh.new()
kit.add_cylinder(bm, 0.2, 3.0, 12, center=(0, 0, 1.5))
for k in range(1, 10):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0.3 * k), plane_no=(0, 0, 1))
tube = kit.mesh_object('Tube', bm, collection=get_collection('Stage'), smooth=True)
tube.data.materials.append(kit.pbr('Tube', (0.5, 0.35, 0.2, 1), roughness=0.6))
kit.add_light('AREA', 'Key', (2, -5, 5), 500, (1, 0.95, 0.9), size=4, collection=get_collection('Lights'))
kit.look_at(bpy.data.objects['Key'], (0, 0, 1.5))
kit.add_camera('Camera', (0, -8, 2.0), (0, 0, 1.5), 40, get_collection('Lights'))
kit.select_only(tube)
