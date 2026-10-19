"""keywatch.py - lets the web app's hotkey drills hear the keys you press in Blender.

A web page only receives keys typed into its own window, so drilling shortcuts meant clicking the page and then clicking Blender
again for everything else. While a drill is open the app asks this module to watch (command `keywatch`); a tiny modal operator then
reports every key press to the app and passes it on to Blender untouched. The request expires after `ttl` seconds unless the page
renews it, so closing the drill, or the page, always puts things back by itself.

Keys are reported in the same words the page uses ("Ctrl+Shift+A", "Numpad 7", "Esc"); see KEYS.
"""
import queue
import threading
import time

import bpy

from . import compat

STATE = {"until": 0.0, "running": False, "swallow": False}
_q = queue.Queue()
_worker = [None]

KEYS = {
    "PERIOD": ".", "COMMA": ",", "SLASH": "/", "BACK_SLASH": "\\", "MINUS": "-", "EQUAL": "=", "LEFT_BRACKET": "[",
    "RIGHT_BRACKET": "]", "ACCENT_GRAVE": "`", "QUOTE": "'", "SEMI_COLON": ";",
    "UP_ARROW": "Up", "DOWN_ARROW": "Down", "LEFT_ARROW": "Left", "RIGHT_ARROW": "Right",
    "RET": "Enter", "ESC": "Esc", "DEL": "Delete", "BACK_SPACE": "Backspace", "TAB": "Tab", "SPACE": "Space",
    "HOME": "Home", "END": "End", "PAGE_UP": "PageUp", "PAGE_DOWN": "PageDown", "INSERT": "Insert",
    "NUMPAD_PERIOD": "Numpad .", "NUMPAD_SLASH": "Numpad /", "NUMPAD_ASTERIX": "Numpad *", "NUMPAD_MINUS": "Numpad -",
    "NUMPAD_PLUS": "Numpad +", "NUMPAD_ENTER": "Numpad Enter",
}
DIGITS = {"ZERO": "0", "ONE": "1", "TWO": "2", "THREE": "3", "FOUR": "4", "FIVE": "5", "SIX": "6", "SEVEN": "7", "EIGHT": "8", "NINE": "9"}


def key_name(etype):
    """Blender event type -> the drill's name for the key, or None for things that aren't keys we report (mouse, modifiers...)."""
    if etype in KEYS:
        return KEYS[etype]
    if etype in DIGITS:
        return DIGITS[etype]
    if len(etype) == 1 and etype.isalpha():
        return etype
    if etype.startswith("NUMPAD_") and etype[7:].isdigit():
        return "Numpad " + etype[7:]
    if etype[:1] == "F" and etype[1:].isdigit():
        return etype
    return None


def combo_of(event):
    name = key_name(event.type)
    if name is None:
        return None
    mods = [m for m, on in (("Ctrl", event.ctrl or event.oskey), ("Alt", event.alt), ("Shift", event.shift)) if on]
    return "+".join(mods + [name])


def _pump():
    from . import link
    while True:
        combo = _q.get()
        if combo is None:
            return
        try:
            link.post("/api/bridge/keys", {"combo": combo}, timeout=2)
        except Exception:
            pass                                     # the app is gone; the request will expire on its own


def _ensure_worker():
    if _worker[0] is None or not _worker[0].is_alive():
        _worker[0] = threading.Thread(target=_pump, daemon=True, name="polycamp-keys")
        _worker[0].start()


class POLYCAMP_OT_keywatch(bpy.types.Operator):
    bl_idname = "polycamp.keywatch"
    bl_label = "Polycamp key watch"
    bl_options = {"INTERNAL"}

    _timer = None

    def invoke(self, context, event):
        STATE["running"] = True
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if time.time() > STATE["until"]:
            return self._stop(context)
        if event.type == "TIMER":
            _banner()
            return {"PASS_THROUGH"}
        if event.value != "PRESS" or getattr(event, "is_repeat", False):
            return {"PASS_THROUGH"}
        combo = combo_of(event)
        if combo:
            _q.put(combo)
            if STATE["swallow"]:                     # a drill round: the key answers the card, Blender does not act on it
                return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def _stop(self, context):
        STATE["running"] = False
        _banner(clear=True)
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        return {"CANCELLED", "PASS_THROUGH"}

    def cancel(self, context):                       # Blender is closing (or the operator was cancelled) mid-watch
        STATE["running"] = False
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


def _banner(clear=False):
    """While keys are being swallowed, say so on screen: Blender looks unresponsive otherwise."""
    from . import cues
    if clear or not STATE["swallow"]:
        if cues.BANNER["text"]:
            cues.set_banner("")
    else:
        cues.set_banner("Hotkey drill: Blender is ignoring keys until the drill stops (a few seconds after you leave it)", 2.0)


def set_watch(on=True, ttl=25.0, swallow=False):
    """Start (or renew) watching for `ttl` seconds; on=False stops it. Safe to call every few seconds.
    swallow=True keeps Blender from acting on the keys (a Dojo round); False passes them through as normal."""
    if not on:
        STATE["until"] = 0.0
        STATE["swallow"] = False
        return
    STATE["until"] = time.time() + max(2.0, float(ttl))
    STATE["swallow"] = bool(swallow)
    if bpy.app.background or STATE["running"]:
        return
    _ensure_worker()
    found = compat.find_area("VIEW_3D")
    if found:
        win, area, region = found
    else:
        win = bpy.context.window_manager.windows[0]
        area, region = win.screen.areas[0], None
    with bpy.context.temp_override(window=win, area=area, **({"region": region} if region else {})):
        bpy.ops.polycamp.keywatch("INVOKE_DEFAULT")


def register():
    bpy.utils.register_class(POLYCAMP_OT_keywatch)


def unregister():
    STATE["until"] = 0.0
    STATE["swallow"] = False
    _q.put(None)
    try:
        bpy.utils.unregister_class(POLYCAMP_OT_keywatch)
    except Exception:
        pass
