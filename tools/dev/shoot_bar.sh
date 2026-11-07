#!/usr/bin/env bash
# Shoots the bar's data preview (tools/minigames/bar_demo.tscn) at 16:9 and 20:9 (needs a window, not --headless): a demonstration, a mistake, the completion, and one contact sheet under 1 MB:
#     bash tools/dev/shoot_bar.sh [out_png_dir] [sheet_file]
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-${TMPDIR:-/tmp}/bar_shots}"
SHEET="${2:-$ROOT/docs/shots/bedsit/bar/bar_contact.jpg}"
mkdir -p "$OUT" "$(dirname "$SHEET")"
for size in 1280x720 1600x720; do
  for sc in demo mistake complete; do
    RW_BAR_SCENE=$sc bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" -s tools/shoot.gd -- res://tools/minigames/bar_demo.tscn "$OUT" "20:shot:bar_${sc}_${size}" 2>&1 | grep -E "ERROR|SCRIPT" || true
  done
done
python3 "$ROOT/tools/dev/bar_sheet.py" "$OUT" "$SHEET"
