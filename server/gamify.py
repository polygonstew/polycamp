"""gamify.py - levels, rank titles and badges. Pure functions over numbers; engine.py owns the state."""

TITLES = ["Default Cube", "Vertex Wrangler", "Edge Runner", "Face Tracer", "Loop Cutter", "Modifier Mage",
          "Material Maker", "UV Cartographer", "Light Weaver", "Keyframe Knight", "Node Sorcerer", "Render Wizard",
          "Pipeline Pro", "Master Maker", "Guildmaster"]
# Fraction of the whole campaign's XP at which each level starts (so level 15 == finishing everything).
FRACTIONS = [0, .012, .035, .065, .10, .15, .21, .28, .36, .45, .55, .66, .78, .90, 1.0]


def thresholds(total_xp):
    t = max(int(total_xp), 1500)
    return [int(f * t) for f in FRACTIONS]


def level(xp, total_xp):
    th = thresholds(total_xp)
    i = max(k for k, v in enumerate(th) if xp >= v)
    nxt = th[i + 1] if i + 1 < len(th) else None
    cur = th[i]
    return {"n": i + 1, "title": TITLES[i], "xp": xp, "from": cur, "to": nxt,
            "pct": 100 if nxt is None else round(100 * (xp - cur) / max(nxt - cur, 1), 1)}


# id -> (emoji, title, description). World badges are added dynamically ("boss-<world>").
BADGES = {
    "first-task": ("cross", "First Blood", "Complete your first task"),
    "linked": ("plug", "Hello, Blender", "Link Blender to Polycamp"),
    "lesson-1": ("check", "Student", "Finish a lesson"),
    "lesson-10": ("layers", "Regular", "Finish 10 lessons"),
    "lesson-25": ("crown", "Dedicated", "Finish 25 lessons"),
    "hotkey-100": ("keys", "Hotkey Hero", "100 correct Dojo answers"),
    "hotkey-500": ("keys", "Keyboard Samurai", "500 correct Dojo answers"),
    "streak-3": ("flame", "On a Roll", "3-day streak"),
    "streak-7": ("flame", "Week of Fire", "7-day streak"),
    "streak-30": ("flame", "Unstoppable", "30-day streak"),
    "first-render": ("photo", "Ink Dry", "Finish your first render"),
    "render-10": ("photo", "Darkroom", "Finish 10 renders"),
    "cpu-warrior": ("gear", "CPU Warrior", "Wait out a render of 5+ minutes. Respect."),
    "loop-cutter": ("cube", "Loop Cutter", "Use Loop Cut 10 times"),
    "extruder": ("verts", "Extruder", "Extrude 25 times"),
    "texture-smith": ("tex", "Texture Smith", "Save a texture set in the Texture Lab"),
    "uv-cartographer": ("uv", "UV Cartographer", "Inspect a UV layout"),
    "to-godot": ("play", "Game Dev", "Export a model to your Godot/Kiln folder"),
    "night-owl": ("eye", "Night Owl", "Learn something between midnight and 5am"),
    "peeked": ("eye", "Cubby Saw That", "Peek at a solution script"),
    "campaign": ("crown", "Guildmaster", "Finish every lesson in the campaign"),
}


def earned(stats, worlds_done):
    """Which badge ids the stats justify. stats: dict of counters from engine.stats()."""
    e = set()
    if stats["tasks"] >= 1:
        e.add("first-task")
    if stats["linked"]:
        e.add("linked")
    for n in (1, 10, 25):
        if stats["lessons"] >= n:
            e.add("lesson-%d" % n)
    for n in (100, 500):
        if stats["dojo_right"] >= n:
            e.add("hotkey-%d" % n)
    for n in (3, 7, 30):
        if stats["streak"] >= n:
            e.add("streak-%d" % n)
    if stats["renders"] >= 1:
        e.add("first-render")
    if stats["renders"] >= 10:
        e.add("render-10")
    if stats["max_render_s"] >= 300:
        e.add("cpu-warrior")
    if stats["ops"].get("mesh.loopcut_slide", 0) >= 10:
        e.add("loop-cutter")
    if sum(stats["ops"].get(k, 0) for k in ("mesh.extrude_region_move", "view3d.edit_mesh_extrude_move_normal",
                                              "mesh.extrude_region_shrink_fatten")) >= 25:
        e.add("extruder")
    for flag, bid in (("textures", "texture-smith"), ("uv_looks", "uv-cartographer"), ("godot", "to-godot"),
                      ("night", "night-owl"), ("peeked", "peeked"), ("campaign", "campaign")):
        if stats.get(flag):
            e.add(bid)
    e.update("boss-" + w for w in worlds_done)
    return e
