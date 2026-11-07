#!/usr/bin/env bash
# Shoots the bedsit's four facings at 16:9 and 20:9 (needs a window, not --headless) and builds one contact sheet under 1 MB:
#     bash tools/dev/shoot_bedsit.sh [out_png_dir] [sheet_file]
# The map is flown through the same low-res pipeline the game uses (tools/story/preview_map.gd, RW_PREVIEW_POSE = x,z,yaw): north 0, east -90, south 180, west 90.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-${TMPDIR:-/tmp}/bedsit_shots}"
SHEET="${2:-$ROOT/docs/shots/bedsit/bedsit_contact.jpg}"
mkdir -p "$OUT" "$(dirname "$SHEET")"
for size in 1280x720 1600x720; do
  for f in "n 0" "e -90" "s 180" "w 90"; do
    set -- $f
    RW_MAP=bedsit RW_PREVIEW_POSE="0,0,$2" RW_PREVIEW_T=8 bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" -s tools/shoot.gd -- res://tools/story/preview_map.tscn "$OUT" "30:shot:bedsit_${1}_${size}" 2>&1 | grep -E "ERROR|SCRIPT" || true
  done
done
python3 "$ROOT/tools/dev/bedsit_sheet.py" "$OUT" "$SHEET"
