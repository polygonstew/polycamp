# Dressed diorama, default EEVEE settings, no lights, no camera, grey world. The boss lights, frames and renders it.
build_diorama(mats=True, lights=False, camera=False, world=False, cpu=None)
kit.make_world((0.5, 0.5, 0.5, 1), 1.0)
kit.select_only(bpy.data.objects['Cabin_Walls'])
