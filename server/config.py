"""config.py - paths, port, and the small settings.json the learner can change in the app."""
import json
import os
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
WEB = ROOT / "web"
ADDON_SRC = ROOT / "addon" / "polycamp_link"
DATA = Path(os.environ.get("POLYCAMP_DATA", ROOT / "data"))
PORT = int(os.environ.get("POLYCAMP_PORT", "8570"))
HOST = os.environ.get("POLYCAMP_HOST", "0.0.0.0")
VERSION = "1.0.0"

for sub in ("renders", "textures", "uv", "models", "shots", "tmp"):
    (DATA / sub).mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    "name": "Maker",
    "layout": "auto",              # auto | dual | single
    "blender_major": "auto",       # auto | 3 | 4 | 5  (which version notes to show)
    "comfy_url": "http://127.0.0.1:8188",
    "comfy_ckpt": "DreamShaper_8_pruned.safetensors",
    "comfy_steps": 16,
    "comfy_side": 512,
    "godot_dir": "",               # folder inside a Godot project / Kiln asset folder that gets models/ + textures/
    "sound": False,
    "theme": "ember",
    "text_scale": 1.0,
    "unlock_all": True,            # nothing is locked; the map just recommends the next step
}

_lock = threading.Lock()
_path = DATA / "settings.json"


def load():
    s = dict(DEFAULTS)
    try:
        s.update(json.loads(_path.read_text()))
    except Exception:
        pass
    return s


def save(patch):
    with _lock:
        s = load()
        for k, v in patch.items():
            if k in DEFAULTS:
                s[k] = type(DEFAULTS[k])(v) if not isinstance(DEFAULTS[k], bool) else bool(v)
        _path.write_text(json.dumps(s, indent=1))
        return s
