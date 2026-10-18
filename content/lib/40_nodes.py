# content/lib/40_nodes.py - build Geometry Nodes groups from Python on Blender 3.3, 4.x and 5.x.


def gn_group(name):
    """A new geometry node group with Geometry in and out. Returns (group, group_input, group_output)."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    if hasattr(ng, 'interface'):                                  # 4.0 and newer
        ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    else:                                                         # 3.x
        ng.inputs.new('NodeSocketGeometry', 'Geometry')
        ng.outputs.new('NodeSocketGeometry', 'Geometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')
    gi.location, go.location = (-600, 0), (700, 0)
    return ng, gi, go


def gn_node(ng, idname, loc=(0, 0), **inputs):
    """Add a node; keyword arguments set input default values by socket name."""
    n = ng.nodes.new(idname)
    n.location = loc
    for k, v in inputs.items():
        s = n.inputs.get(k.replace('_', ' '))
        if s is not None:
            s.default_value = v
    return n


def gn_link(ng, a, out, b, inp):
    """Link output `out` of node a to input `inp` of node b (names or indices)."""
    ng.links.new(a.outputs[out], b.inputs[inp])


def gn_modifier(obj, ng, name='GeometryNodes'):
    m = obj.modifiers.new(name, 'NODES')
    m.node_group = ng
    return m
