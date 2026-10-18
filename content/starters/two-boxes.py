# Two open boxes that face each other, plus an open cup. One mesh, three islands, all with holes to fix.
cube, light, cam = kit.default_scene()
bpy.data.objects.remove(cube, do_unlink=True)
bm = bmesh.new()


def open_box(cx, cy, drop_normal):
    v = kit.add_box(bm, (1.6, 1.6, 1.6), (cx, cy, 0.8))
    faces = {f for vert in v for f in vert.link_faces}
    for f in faces:
        if (f.normal - Vector(drop_normal)).length < 0.1:
            bmesh.ops.delete(bm, geom=[f], context='FACES_ONLY')
            break


open_box(-2.2, 0, (1, 0, 0))
open_box(2.2, 0, (-1, 0, 0))
open_box(0, 3.4, (0, 0, 1))
ob = kit.mesh_object('Parts', bm, collection=bpy.context.scene.collection.children['Collection'])
ob.data.materials.append(kit.pbr('Parts', (0.75, 0.55, 0.35, 1)))
kit.select_only(ob)
cam.location = (0, -9, 6)
kit.look_at(cam, (0, 1.2, 0.8))
