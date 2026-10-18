"""Polycamp Link - two-way bridge between Blender and the Polycamp learning app.

Install: Edit > Preferences > Add-ons > Install (3.3) / "Install from Disk" (4.2+), pick polycamp_link.zip,
tick the add-on. Open the 3D viewport sidebar (N) > Polycamp tab. Works on Blender 3.3, 4.x and 5.x.
"""

bl_info = {
    "name": "Polycamp Link",
    "author": "Polycamp",
    "version": (1, 0, 0),
    "blender": (3, 3, 0),
    "location": "3D Viewport > Sidebar (N) > Polycamp",
    "description": "Live link between Blender and the Polycamp lesson app: checks your work, builds lesson scenes, "
                   "sends textures and renders back and forth",
    "category": "System",
}

if "bpy" in locals():                      # F8 / reload support
    import importlib
    for _m in ("config", "compat", "snapshot", "scenekit", "matkit", "uvlayout", "commands", "link", "ui"):
        if _m in globals():
            importlib.reload(globals()[_m])
else:
    import bpy
    from . import config, compat, snapshot, scenekit, matkit, uvlayout, commands, link, ui  # noqa: F401


def register():
    ui.register()
    link.register()


def unregister():
    link.unregister()
    ui.unregister()
