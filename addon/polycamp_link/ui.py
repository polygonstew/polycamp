"""ui.py - preferences, the sidebar panel (N > Polycamp), its operators and the optional task overlay."""
import textwrap
import time
import webbrowser

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

from . import config, link, matkit


def _restart(self, context):
    if link.S.enabled:
        link.restart()


class POLYCAMP_Prefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    server_url: StringProperty(name="Polycamp server", default=config.DEFAULT_SERVER,
                               description="Where the Polycamp web app runs (this PC or another one on your network)",
                               update=_restart)
    enabled: BoolProperty(name="Connect automatically", default=True)
    allow_scripts: BoolProperty(name="Let lessons set up scenes", default=True,
                                description="Lets the app run its lesson starter scripts inside Blender")
    auto_send_renders: BoolProperty(name="Send finished renders to the Trophy Room", default=True)
    overlay: BoolProperty(name="Show tasks in the 3D viewport", default=False,
                          description="Single-screen mode: draws the current tasks over the viewport")

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "server_url")
        col.prop(self, "enabled")
        col.prop(self, "allow_scripts")
        col.prop(self, "auto_send_renders")
        col.prop(self, "overlay")
        row = col.row()
        row.operator("polycamp.reconnect", icon="FILE_REFRESH")
        row.operator("polycamp.open_app", icon="URL")


# ------------------------------------------------------------------ operators

class POLYCAMP_OT_open_app(bpy.types.Operator):
    bl_idname = "polycamp.open_app"
    bl_label = "Open Polycamp"
    bl_description = "Open the Polycamp lesson app in your web browser"

    def execute(self, context):
        webbrowser.open(link.S.server)
        return {"FINISHED"}


class POLYCAMP_OT_reconnect(bpy.types.Operator):
    bl_idname = "polycamp.reconnect"
    bl_label = "Reconnect"
    bl_description = "Restart the connection to the Polycamp server"

    def execute(self, context):
        link.restart()
        self.report({"INFO"}, "Reconnecting to " + link.S.server)
        return {"FINISHED"}


class POLYCAMP_OT_hint(bpy.types.Operator):
    bl_idname = "polycamp.hint"
    bl_label = "Hint"
    bl_description = "Ask the app for the next hint on the current task"

    def execute(self, context):
        try:
            r = link.post("/api/lesson/hint", {"source": "blender"}, timeout=4)
            link.S.toast = (r.get("text") or r.get("error") or "No hint available.", time.time())
            self.report({"INFO"}, link.S.toast[0][:200])
        except Exception as e:
            self.report({"WARNING"}, "Can't reach Polycamp: %s" % e)
        return {"FINISHED"}


class POLYCAMP_OT_prep(bpy.types.Operator):
    bl_idname = "polycamp.prep"
    bl_label = "Set up this lesson's scene"
    bl_description = "Build the starting scene for the current lesson (your unsaved work is backed up first)"

    def execute(self, context):
        try:
            r = link.post("/api/lesson/prep", {"cid": link.CLIENT_ID}, timeout=4)
            self.report({"INFO"}, r.get("msg", "Asked the app to prepare the scene."))
        except Exception as e:
            self.report({"WARNING"}, "Can't reach Polycamp: %s" % e)
        return {"FINISHED"}


class POLYCAMP_OT_cpu_preset(bpy.types.Operator):
    bl_idname = "polycamp.cpu_preset"
    bl_label = "CPU-friendly render preset"
    bl_description = "Cycles on CPU with low samples, adaptive sampling and the denoiser"

    quality: EnumProperty(name="Quality", items=[("draft", "Draft (960x540)", ""), ("standard", "Standard (1280x720)", ""),
                                                 ("final", "Final (1920x1080)", "")], default="standard")

    def execute(self, context):
        info = matkit.cpu_preset(context.scene, self.quality)
        self.report({"INFO"}, "Cycles/CPU: %d samples at %dx%d" % (info["samples"], *info["res"]))
        return {"FINISHED"}


class POLYCAMP_OT_send_render(bpy.types.Operator):
    bl_idname = "polycamp.send_render"
    bl_label = "Send last render"
    bl_description = "Send the last render (F12) to the Polycamp Trophy Room"

    def execute(self, context):
        try:
            self.report({"INFO"}, "Sent " + link.send_render_result())
        except Exception as e:
            self.report({"WARNING"}, str(e))
        return {"FINISHED"}


class POLYCAMP_OT_export_model(bpy.types.Operator):
    bl_idname = "polycamp.export_model"
    bl_label = "Export to Godot / Kiln"
    bl_description = "Export the selected objects as glTF (.glb) and let Polycamp copy it into your Godot or Kiln folder"

    selected_only: BoolProperty(name="Selected only", default=True)

    def execute(self, context):
        from . import commands
        name = bpy.path.display_name_from_filepath(bpy.data.filepath) or "polycamp-model"
        r = commands.run({"cmd": "export_model", "args": {"name": name, "selected_only": self.selected_only}})
        self.report({"INFO"} if r["ok"] else {"WARNING"}, r["msg"])
        return {"FINISHED"}


class POLYCAMP_OT_overlay(bpy.types.Operator):
    bl_idname = "polycamp.overlay"
    bl_label = "Toggle task overlay"

    def execute(self, context):
        p = link.prefs()
        if p:
            p.overlay = not p.overlay
        for a in context.screen.areas:
            a.tag_redraw()
        return {"FINISHED"}


# ------------------------------------------------------------------ panel

def _wrap(text, width=34):
    return textwrap.wrap(text, width) or [""]


class POLYCAMP_PT_main(bpy.types.Panel):
    bl_label = "Polycamp"
    bl_idname = "POLYCAMP_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Polycamp"

    def draw(self, context):
        lay, S = self.layout, link.S
        row = lay.row()
        if S.connected:
            row.label(text="Linked to Polycamp", icon="CHECKMARK")
        else:
            row.label(text="Not linked", icon="ERROR")
            if S.last_error:
                lay.label(text=S.last_error[:48])
        hud = S.hud or {}
        lv = hud.get("level")
        if lv:
            lay.label(text="Lv %s  %s   %s XP" % (lv.get("n"), lv.get("title"), lv.get("xp")))
        lesson = hud.get("lesson")
        if lesson:
            box = lay.box()
            col = box.column(align=True)
            for i, ln in enumerate(_wrap(lesson.get("title", ""), 30)):
                col.label(text=ln, icon="BOOKMARKS" if i == 0 else "BLANK1")
            for t in hud.get("tasks", []):
                c = box.column(align=True)
                for i, ln in enumerate(_wrap(t.get("title", ""), 32)):
                    c.label(text=ln, icon=("CHECKBOX_HLT" if t.get("done") else "CHECKBOX_DEHLT") if i == 0 else "BLANK1")
                if not t.get("done"):
                    for chk in t.get("checks", []):
                        for i, ln in enumerate(_wrap(chk.get("label", ""), 30)):
                            c.label(text=("   " + ("+ " if chk.get("ok") else "- ") if i == 0 else "      ") + ln)
            row = box.row(align=True)
            row.operator("polycamp.hint", icon="QUESTION")
            row.operator("polycamp.prep", text="Set up scene", icon="FILE_NEW")
        else:
            lay.label(text="Pick a lesson in the app.")
        if S.toast and time.time() - S.toast[1] < 40:
            box = lay.box()
            for ln in _wrap(S.toast[0], 34):
                box.label(text=ln)
        lay.separator()
        col = lay.column(align=True)
        col.operator("polycamp.open_app", icon="URL")
        col.operator("polycamp.cpu_preset", icon="SETTINGS").quality = "standard"
        col.operator("polycamp.send_render", icon="RENDER_STILL")
        col.operator("polycamp.export_model", icon="EXPORT")
        col.operator("polycamp.overlay", icon="WINDOW")


# ------------------------------------------------------------------ overlay (single-screen mode)

_draw_handle = None


def _draw_overlay():
    p = link.prefs()
    if p is None or not p.overlay:
        return
    import blf
    hud = link.S.hud or {}
    lines = []
    lesson = hud.get("lesson")
    if lesson:
        lines.append((lesson.get("title", ""), (1.0, 0.78, 0.2, 1.0)))
        for t in hud.get("tasks", []):
            lines.append(("[%s] %s" % ("x" if t.get("done") else " ", t.get("title", "")),
                          (0.6, 1.0, 0.6, 1.0) if t.get("done") else (1, 1, 1, 1)))
    else:
        lines.append(("Polycamp: pick a lesson in the app", (1, 1, 1, 1)))
    if link.S.toast and time.time() - link.S.toast[1] < 25:
        lines.append(("hint: " + link.S.toast[0], (0.5, 0.9, 1.0, 1.0)))
    font = 0
    compat_size = None
    try:
        from . import compat
        compat_size = compat.set_blf_size
    except Exception:
        pass
    y = bpy.context.region.height - 60
    for text, col in lines:
        if compat_size:
            compat_size(font, 14)
        blf.color(font, *col)
        blf.enable(font, blf.SHADOW)
        blf.shadow(font, 3, 0.0, 0.0, 0.0, 1.0)
        blf.position(font, 70, y, 0)
        blf.draw(font, text[:110])
        y -= 20


CLASSES = (POLYCAMP_Prefs, POLYCAMP_OT_open_app, POLYCAMP_OT_reconnect, POLYCAMP_OT_hint, POLYCAMP_OT_prep,
           POLYCAMP_OT_cpu_preset, POLYCAMP_OT_send_render, POLYCAMP_OT_export_model, POLYCAMP_OT_overlay,
           POLYCAMP_PT_main)


def register():
    global _draw_handle
    for c in CLASSES:
        bpy.utils.register_class(c)
    if not bpy.app.background:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_overlay, (), "WINDOW", "POST_PIXEL")


def unregister():
    global _draw_handle
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, "WINDOW")
        _draw_handle = None
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
