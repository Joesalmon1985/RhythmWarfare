# The Space rave through the game's low-res pipeline (tools/story/preview_map.gd), at 16:9 and 20:9: the hub viewpoint, the stage approach, the deck before and after the bass is fixed.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-${TMPDIR:-/tmp}/space_shots}"
SHEET="${2:-$ROOT/docs/shots/bedsit/space/space_contact.jpg}"
mkdir -p "$OUT" "$(dirname "$SHEET")"
LIGHTS="pylon_beams,ring_lights,hologram_dome"
for size in 1280x720 1600x720; do
  while read -r name pose env; do
    env $env RW_MAP=space_rave RW_PREVIEW_POSE="$pose" RW_PREVIEW_T=8 bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" -s tools/shoot.gd -- res://tools/story/preview_map.tscn "$OUT" "30:shot:${name}_${size}" 2>&1 | grep -E "ERROR|SCRIPT" || true
  done <<LIST
hub 0,14.2,0 X=1
approach 0,-15.2,0 X=1
deck_before 0,-22.6,0 RW_PREVIEW_KNOB=0
deck_after 0,-22.6,0 RW_PREVIEW_KNOB=3 RW_PREVIEW_PIECES=$LIGHTS
LIST
done
python3 "$ROOT/tools/dev/space_sheet.py" "$OUT" "$SHEET"
