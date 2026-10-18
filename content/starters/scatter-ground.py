# A round ground slab and a single grass tuft model, ready to be scattered with Geometry Nodes.
kit.wipe()
kit.reset_scene_settings()
kit.make_world((0.12, 0.13, 0.16, 1), 1.0)
bm = bmesh.new()
kit.add_grid(bm, 9.0, 24)
ground = kit.mesh_object('Ground', bm, collection=get_collection('Ground'), smooth=True)
ground.data.materials.append(mat_grass())
bm = bmesh.new()
for b in range(3):
    h = 0.35 - 0.05 * b
    v = kit.add_cylinder(bm, 0.025, h, 4, center=(0, 0, h / 2), radius2=0.0)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Euler((0.3 * (b - 1), 0.25 * b, b * 2.1)).to_matrix(), verts=v)
tuft = kit.mesh_object('Tuft', bm, collection=get_collection('Assets'), loc=(6, 0, 0))
tuft.data.materials.append(mat_grass('Grass_Tuft'))
kit.add_light('SUN', 'Sun', (-5, -6, 6), 3.0, (1.0, 0.85, 0.65), size=3, collection=get_collection('Lights'))
kit.look_at(bpy.data.objects['Sun'], (0, 0, 0))
kit.add_camera('Camera', (7, -8, 5), (0, 0, 0), 40, get_collection('Lights'))
kit.select_only(ground)
