#!/usr/bin/env bash
# The Story chapters menu's thumbnails (finding F13 of docs/art/VISUAL_AUDIT.md): a frame of each chapter's room as the run draws it now
# (no falling notes, no HUD: RW_RUN_CLEAN=1), its picture cropped to 16:9 and boxed down to 256 x 144, JPEG quality 82 (about 10 to 20 KB
# each), into assets/run/thumbs/<art world>.jpg, which src/scenes/story_campaign.gd shows. Needs a display. Rerun after a world's look changes.
#   bash tools/art/make_thumbs.sh            GODOT must be tools/dev/godot.sh; PY a python with Pillow (default python)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${PY:-python}"
GODOT="${GODOT:?set GODOT to tools/dev/godot.sh}"
OUT="$ROOT/assets/run/thumbs"
TMP="$(mktemp -d)"; TMPW="$(cygpath -m "$TMP" 2>/dev/null || echo "$TMP")"
mkdir -p "$OUT"
RATE=0.25
SHOT=$("$PY" -c "print(int(round((14.0+2.0)/$RATE))+2)")   # 14 song seconds in: the room lit and peopled
while read -r art scene; do
  echo "thumb $art ($scene)"
  env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_RUN_START="$scene" RW_RUN_BOT=perfect RW_RUN_ROUTES="" RW_RUN_CLEAN=1 \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" "$SHOT:shot:$art" 2>&1 </dev/null \
    | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
  "$PY" - "$TMP/png/$art.png" "$OUT/$art.jpg" <<'PYEOF'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
w, h = im.size
ph = int(round(h * 0.64))  # the picture above the pad strip (standard pad size, Session.PAD_SIZES[1] = 0.36)
cw = int(round(ph * 16 / 9))
x0 = (w - cw) // 2
im.crop((x0, 0, x0 + cw, ph)).resize((256, 144), Image.BOX).save(sys.argv[2], quality=82, optimize=True)
print("wrote", sys.argv[2])
PYEOF
done <<'EOF'
night_one warehouse
mothership mothership.bridge
underworld underworld.pit
hospital hospital.corridor
mental_hospital ward.courtyard
EOF
rm -rf "$TMP"
