#!/usr/bin/env bash
# Review sheets of the Hospital chapter's art, every room at once: tools/story/shoot_hp.sh <mode> [out_dir]
# mode = stage | set | pieces | stage_low (one shot per room: main, corridor, cafeteria, garden) or chars | chars_b | heads | close | sil |
# deck | interlude | passage (one shot). Needs a display (DISPLAY defaults to :0). NOIMPORT=1 skips the import pass.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
MODE="${1:-stage}"
OUT="${2:-/tmp/story_hp}"
export DISPLAY="${DISPLAY:-:0}"
[ "${NOIMPORT:-0}" = "1" ] || "$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1 || true
case "$MODE" in
  stage|set|pieces|stage_low) VIEWS="main corridor cafeteria garden" ;;
  *) VIEWS="main" ;;
esac
for v in $VIEWS; do
  if [ "$v" = "main" ]; then
    RW_CHAPTER=hospital RW_PREVIEW="$MODE" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://tools/story/preview_chapter.tscn "$OUT" "30:shot:hp_${v}_$MODE" 2>&1 | grep -E "^shot|ERROR|SCRIPT|Parse" || true
  else
    RW_VIEW="$v" RW_CHAPTER=hospital RW_PREVIEW="$MODE" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://tools/story/preview_chapter.tscn "$OUT" "30:shot:hp_${v}_$MODE" 2>&1 | grep -E "^shot|ERROR|SCRIPT|Parse" || true
  fi
done
