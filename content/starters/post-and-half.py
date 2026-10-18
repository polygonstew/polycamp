# Two things to practise Mirror and Array on: one fence post, and the right half of a little hull.
cube, light, cam = kit.default_scene()
bpy.data.objects.remove(cube, do_unlink=True)
col = bpy.context.scene.collection.children['Collection']
bm = bmesh.new()
lib_box = box_at(bm, (0.18, 0.18, 1.3), (0, 0, 0.65))
post = kit.mesh_object('Post', bm, collection=col, loc=(-4, 0, 0))
post.data.materials.append(mat_wood('Post_Wood'))
# a half hull: a tapered wedge that touches the X = 0 plane
bm = bmesh.new()
pts = [(0, -1.4, 0), (0.9, -0.9, 0), (0.9, 0.9, 0), (0, 1.8, 0), (0, -1.4, 0.8), (0.7, -0.8, 0.8), (0.7, 0.8, 0.8), (0, 1.5, 0.8)]
vs = [bm.verts.new(p) for p in pts]
for q in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
    bm.faces.new([vs[i] for i in q])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
half = kit.mesh_object('HalfHull', bm, collection=col, loc=(1.5, 0, 0))
half.data.materials.append(kit.pbr('Hull', (0.6, 0.65, 0.75, 1), roughness=0.4, metallic=0.5))
kit.select_only(post)
cam.location = (3, -9, 5)
kit.look_at(cam, (-1.2, 0, 0.6))
