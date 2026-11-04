#!/usr/bin/env bash
# Frame time of the busiest 16 bars of every chapter (the budget: 12 ms mean, 20 ms p95 on the reference laptop). Needs a display; run it on an idle machine.
#   bash tools/story/profile_all.sh [chapter ...]     (RW_STORY_LINES=270 etc. to change the internal resolution)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
declare -A FROM=( [night_one]=105 [mothership]=57 [underworld]=41 [hospital]=33 [mental_hospital]=41 )
CH=("$@"); [ ${#CH[@]} -eq 0 ] && CH=(night_one mothership underworld hospital mental_hospital)
for c in "${CH[@]}"; do
  f=${FROM[$c]}; u=$((f+16))
  out=$(RW_STORY_VIRTUAL=1 RW_AUTOPLAY=perfect RW_STORY_PROFILE_FROM=$f RW_STORY_UNTIL_BAR=$u RW_STORY_CHAPTER=$c "$GODOT" --path "$ROOT" --disable-vsync --resolution 1280x720 res://src/scenes/story_play.tscn 2>&1 | grep -E "^PROFILE|SCRIPT ERROR" | head -3)
  echo "$c bars $f-$u: $out"
done
