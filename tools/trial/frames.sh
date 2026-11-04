#!/usr/bin/env bash
# Frame times (real time, windowed 1280x720, vsync off, perfect autoplay) of the heaviest zones of the Bassment: from the zone's first passage to a later one.
#   bash tools/trial/frames.sh
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
for spec in "19 20 cellar" "15 16 stacks" "26 28 fungus" "30 32 mirrors" "48 50 kitchens"; do
  read -r from until name <<< "$spec"
  echo "== $name (passages $from to $until)"
  env RW_TRIAL_DIRECT=1 RW_TRIAL_START="$from" RW_TRIAL_UNTIL="$until" RW_STORY_QUIT=1 RW_TRIAL_BOT=perfect \
    timeout 120 "$GODOT" --path "$ROOT" --resolution 1280x720 --disable-vsync res://src/run/run_play.tscn 2>&1 | grep -E "FRAMES|ERROR|SCRIPT"
done
