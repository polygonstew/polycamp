#!/bin/sh
# Run the GUI highlight test in a real Blender on a virtual display (Linux, needs xvfb-run):
#     sh tools/gui_test.sh [blender-binary] [screenshot-dir]
# Works with any Blender 3.3+. A throw-away user config keeps the splash screen and old prefs out of the way.
BLENDER="${1:-blender}"
OUT="${2:-/tmp/polycamp-gui}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="$(mktemp -d)"
export BLENDER_USER_CONFIG="$CFG"
# Software OpenGL; the version override is what lets Blender 3.3 draw on Mesa's virtual display
export LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=4.5 MESA_GLSL_VERSION_OVERRIDE=450
cat > "$CFG/prefs.py" <<'EOF'
import bpy
bpy.context.preferences.view.show_splash = False
bpy.ops.wm.save_userpref()
EOF
"$BLENDER" -b --factory-startup --python "$CFG/prefs.py" >/dev/null 2>&1
mkdir -p "$OUT"
xvfb-run -a -s "-screen 0 1920x1080x24 +extension GLX +render -noreset" "$BLENDER" --python "$HERE/gui_cues_test.py" -- "$OUT" 2>&1 | tee "$OUT/log.txt" | grep -E "^(PASS|FAIL|==|Traceback|Error|  File)|Error:"
rm -rf "$CFG"
! grep -q "^FAIL\|Traceback" "$OUT/log.txt" && grep -q "ALL PASSED" "$OUT/log.txt"
