# Every diorama part built but standing in a line off to the side. The boss lesson is to put them where they belong.
build_diorama(parts=('ground', 'tufts', 'cabin', 'post', 'rocks', 'trees'), lights=False, camera=False, cpu=None)
bpy.data.objects.remove(bpy.data.objects['Grass_Tufts'], do_unlink=True)
x = -14.0
for name in ('Cabin', 'Lamp_Post', 'PostLantern'):
    ob = bpy.data.objects.get(name)
    if ob is not None and ob.parent is None:
        ob.location = (x, -9.0, 0.0)
        x += 4.0
for ob in bpy.data.objects:
    if ob.name.startswith(('Rock', 'Pine')) and ob.parent is None:
        ob.location = (x, -12.0, ob.location.z)
        x += 2.2
kit.select_only(bpy.data.objects['Cabin'])
