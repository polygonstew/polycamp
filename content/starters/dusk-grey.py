# The finished diorama (materials, lights, camera) under a flat grey world. The sky lesson fixes the world.
build_diorama(mats=True, lights=True, camera=True, world=False, cpu=None)
kit.make_world((0.5, 0.5, 0.5, 1), 1.0)
kit.select_only(bpy.data.objects['Camera'])
