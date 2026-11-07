#!/usr/bin/env bash
# The card table's shots (package A8b): the walk-up, the hold with a dealt hand, a bust, a payout, at 16:9 (1280 x 720) and 20:9 (1600 x 720), with the pad strip
# showing the table's controls; then one contact sheet under 1 MB. Needs a window (not --headless):
#     bash tools/minigames/shoot_cardtable.sh [png_dir] [sheet_file]
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-${TMPDIR:-/tmp}/cardtable_shots}"
SHEET="${2:-$ROOT/docs/shots/bedsit/cardtable/contact.jpg}"
mkdir -p "$OUT" "$(dirname "$SHEET")"
for size in 1280x720 1600x720; do
  RW_SHOT_DIR="$OUT" bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" -s tools/minigames/shoot_cardtable.gd 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
done
python "$ROOT/tools/minigames/cardtable_sheet.py" "$OUT" "$SHEET"
