# A properly unwrapped barrel, with a plain material, ready for image textures.
kit.wipe()
kit.reset_scene_settings()
kit.make_world((0.12, 0.13, 0.16, 1), 1.0)
build_barrel('Barrel', (0, 0, 0), get_collection('Props'), uv=True, mat=kit.pbr('Barrel', (0.6, 0.6, 0.6, 1), roughness=0.7))
kit.add_light('AREA', 'Key', (3, -4, 5), 400, (1, 0.95, 0.9), size=3, collection=get_collection('Lights'))
kit.look_at(bpy.data.objects['Key'], (0, 0, 0.5))
kit.add_camera('Camera', (2.6, -3.4, 1.8), (0, 0, 0.5), 40, get_collection('Lights'))
kit.select_only(bpy.data.objects['Barrel'])
