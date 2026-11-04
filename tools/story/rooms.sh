#!/usr/bin/env bash
# One screenshot per place of every chapter (tools/story/room_shots.py lists them), then a contact sheet per chapter.
#   bash tools/story/rooms.sh [out_png_dir] [sheet_dir]      RW_ROOMS=<regex on "chapter|name"> limits it; up to RW_JOBS (default 4) shots run in parallel
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-/tmp/story_rooms}"; SHEETS="${2:-$ROOT/docs/shots/story}"
ONLY="${RW_ROOMS:-}"; JOBS="${RW_JOBS:-4}"; RATE=2.0
mkdir -p "$OUT"
one() {
  local c="$1" name="$2" cam="$3" bar="$4"
  local secs frames
  secs=$(python3 -c "print(($bar-1)*4*60/174)"); frames=$(python3 -c "print(int(max(($secs-1.0),0)/$RATE)+40)")
  env RW_STORY_CHAPTER="$c" RW_STORY_CAM="$cam" RW_STORY_VIRTUAL=1 RW_STORY_RATE=$RATE RW_STORY_UNTIL_BAR="$bar" RW_AUTOPLAY=perfect \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/scenes/story_play.tscn "$OUT" "$frames:shot:room_${c}_${name}" 2>&1 | grep -E "ERROR|SCRIPT" || true
}
while IFS='|' read -r c name cam bar; do
  [ -z "$ONLY" ] || [[ "$c|$name" =~ $ONLY ]] || continue
  one "$c" "$name" "$cam" "$bar" &
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do sleep 1; done
done < <(python3 "$ROOT/tools/story/room_shots.py" list)
wait
python3 "$ROOT/tools/story/room_shots.py" sheets "$OUT" "$SHEETS"
