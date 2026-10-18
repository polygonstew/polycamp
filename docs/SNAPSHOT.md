# The snapshot (what the add-on tells the server)

`addon/polycamp_link/snapshot.py` builds one dict; about 5 KB for a small scene. It is the contract that every
`check:` expression is written against. Sent only when it changes. All numbers are rounded. Rotations are in degrees.

    v, blender, bver [major, minor, patch], platform, background, mode (context.mode), errors []
    file        {path, name, dirty, saved}
    scene       {name, camera, unit_system, unit_scale, markers, gravity, rigidbody, cursor, frame, comp_nodes [], collections []}
    render      {engine (CYCLES|EEVEE|WORKBENCH), engine_id, res_x, res_y, res_pct, film_transparent, format, filepath, fps,
                 frame_start, frame_end, frame, motion_blur, simplify, simplify_subdiv, ffmpeg_format,
                 view_transform, look, exposure, gamma,
                 cy_samples, cy_preview_samples, cy_use_denoising, cy_denoiser, cy_use_adaptive_sampling, cy_adaptive_threshold,
                 cy_device, cy_max_bounces, cy_diffuse/glossy/transmission/volume_bounces, cy_use_light_tree, cy_film_exposure,
                 ev_* (EEVEE flags that exist on this version)}
    objects[]   {name, type, data, mode, loc, rot, scale, dims, wbox [minx miny minz maxx maxy maxz], world_loc, parent, children,
                 collections, sel, active, hide, hide_render, hidden, instance, display,
                 mods [{type, name, viewport, render, p: {all simple RNA properties}, group}],
                 cons [{type, target}], mats [names], vgroups, particles, shape_keys,
                 anim {keys, paths {data_path: n}, frames [], interp [], fmods [], drivers, action},
                 posed,
                 mesh: verts, edges, faces, tris, quads, n3, ngons, smooth_faces, flat_faces, seams, sharp_edges,
                       boundary_edges, nonmanifold_edges, loose_edges, volume (closed meshes), verts_eval, faces_eval,
                       uv [layer names], uv_area, uv_oob, uv_bounds,
                       in_edit + sel_verts, sel_edges, sel_faces, select_mode (the active object in Edit Mode)
                 light {kind, energy, color, shadow, size|radius|angle_deg, spot_deg, spot_blend}
                 camera {lens, sensor, kind, clip_start, clip_end, is_scene_camera, dof, focus_object, focus_distance, fstop, ortho_scale}
                 armature {bones, names}, curve {splines, bevel_depth, extrude}, text}
    objects_total, active, selected [names]
    materials[] {name, users, use_nodes, color, principled, base_color, metallic, roughness, emission, emission_strength,
                 alpha, ior, transmission, coat, specular, types [node types], n_nodes, n_links, images [names], surface,
                 chain {socket: [upstream node types]}, emit_node_strength}
    images[]    {name, w, h, source, path, colorspace, users, packed, dirty, generated}
    world       {name, color, use_nodes, types, bg_linked, bg_color, strength, sky_type, has_hdri, has_volume}
    node_groups[] {name, kind (bl_idname of the tree), n, ids [node bl_idnames], users}
    ui          {windows, areas [], workspace, screen, shading, xray, stats, wire_overlay, persp, view_dist, local_view, gizmo}
    prefs       {emulate_numpad, emulate_3button, undo_steps, autosave, autosave_minutes, ui_scale, show_tooltips_python, save_versions}
    totals      {meshes, verts, faces, lights, cameras}
    ops         {operator idname: times run this Blender session}     counters {view_changes, sel_changes}
    render_last {time, frames, ts, engine, res, samples, ok}          link {addon, cid}

`materials[].chain` is the useful trick for shader checks: for each Principled input that has a link, the node types
upstream of it, nearest first. `'NORMAL_MAP' in m.chain.normal` means a normal map feeds the Normal socket, whatever
else is in between. Principled socket names differ between 3.x and 4.x; the snapshot normalises them to canonical keys
(`base_color`, `metallic`, `roughness`, `normal`, `emission`, `emission_strength`, `alpha`, `transmission`, `coat`, `specular`).

Edit-mode counts come from bmesh, so they are live while the learner works. Everything else reads the data API.
