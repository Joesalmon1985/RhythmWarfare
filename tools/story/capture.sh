#!/usr/bin/env bash
# Real Godot screenshots of the running Story Campaign scene (needs a display; opens a window briefly per shot).
#   bash tools/story/capture.sh [out_dir]
# Each shot runs the actual story_play scene on a virtual song clock (no audio) with a scripted input policy up to a bar, so the
# crowd, branches and lighting are exactly what a real run of that skill level looks like at that moment.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/story}"
mkdir -p "$OUT"
RATE=2.0

shot() {  # name policy until_bar [extra env assignments...]
  local name="$1" policy="$2" bar="$3"; shift 3
  local secs frames
  secs=$(python3 -c "print(($bar-1)*4*60/174)")
  frames=$(python3 -c "print(int(max(($secs-1.0),0)/$RATE)+40)")
  env RW_STORY_VIRTUAL=1 RW_STORY_RATE=$RATE RW_STORY_UNTIL_BAR="$bar" RW_AUTOPLAY="$policy" "$@" \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/scenes/story_play.tscn "$OUT" "$frames:shot:$name" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
}

shot 01_opening            perfect         3
shot 02_act2_dancing       accuracy:0.8    45
shot 03_peak_energy        perfect         107
shot 04_low_energy         none            50
shot 05_end_legendary      perfect         131
shot 06_end_good_night     sloppy          131 RW_SEED=2
shot 07_end_lost_the_floor none            131
shot 08_layout_compact     perfect         107 RW_PAD_SIZE=0
shot 09_layout_large       perfect         107 RW_PAD_SIZE=2
shot 10_reduced_effects    perfect         107 RW_REDUCED=1
shot 11_high_contrast      perfect         107 RW_HIGH_CONTRAST=1
