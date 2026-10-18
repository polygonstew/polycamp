#!/usr/bin/env python3
"""Install the Polycamp Link add-on into every Blender profile on this machine (Linux, Windows, macOS).

    python3 tools/install_addon.py                          copy into each Blender version folder it finds
    python3 tools/install_addon.py --server http://192.168.0.105:8570
    python3 tools/install_addon.py --versions 3.3 4.5       create the folders for these versions too
    python3 tools/install_addon.py --enable --blender blender   also switch it on (runs that Blender headless)
    python3 tools/install_addon.py --dest /some/addons      copy to one folder only (for testing)

Blender 4.2 and newer still load legacy add-ons from scripts/addons, so one copy works for 3.3, 4.x and 5.x.
"""
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "addon" / "polycamp_link"


def config_roots():
    home = Path.home()
    system = platform.system()
    if system == "Windows":
        return [Path(os.environ.get("APPDATA", home / "AppData/Roaming")) / "Blender Foundation" / "Blender"]
    if system == "Darwin":
        return [home / "Library" / "Application Support" / "Blender"]
    return [Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "blender"]


def targets(extra_versions):
    found = []
    for root in config_roots():
        if root.exists():
            found += [d for d in sorted(root.iterdir()) if d.is_dir() and re.fullmatch(r"\d+\.\d+", d.name)]
        for v in extra_versions:
            found.append(root / v)
    return sorted({d for d in found})


def install(dest_addons, server):
    dest = Path(dest_addons) / "polycamp_link"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SRC, dest, ignore=shutil.ignore_patterns("__pycache__"))
    if server:
        cfg = dest / "config.py"
        cfg.write_text(re.sub(r'DEFAULT_SERVER = ".*?"', 'DEFAULT_SERVER = "%s"' % server.rstrip("/"), cfg.read_text()))
    return dest


def enable(blender):
    code = ("import bpy, addon_utils; addon_utils.enable('polycamp_link', default_set=True, persistent=True); "
            "bpy.ops.wm.save_userpref(); print('POLYCAMP_ENABLED')")
    r = subprocess.run([blender, "-b", "--python-expr", code], capture_output=True, text=True, timeout=120)
    return "POLYCAMP_ENABLED" in r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="", help="address baked in as the default (e.g. http://192.168.0.105:8570)")
    ap.add_argument("--versions", nargs="*", default=[], help="Blender versions to create folders for (e.g. 3.3 4.5)")
    ap.add_argument("--dest", help="copy only into this add-ons folder")
    ap.add_argument("--enable", action="store_true", help="also enable it, by running --blender headless")
    ap.add_argument("--blender", action="append", default=[], help="a Blender executable (repeatable)")
    a = ap.parse_args()
    if a.dest:
        print("installed:", install(a.dest, a.server))
    else:
        dirs = targets(a.versions)
        if not dirs:
            print("No Blender config folders found. Run Blender once, or pass --versions 4.5 (and so on).")
            return 1
        for d in dirs:
            addons = d / "scripts" / "addons"
            addons.mkdir(parents=True, exist_ok=True)
            print("installed:", install(addons, a.server))
    for exe in (a.blender if a.enable else []):
        print("enabled in", exe, "->", "yes" if enable(exe) else "FAILED")
    print("In Blender: Edit > Preferences > Add-ons, tick 'System: Polycamp Link', then press N in a 3D view.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
