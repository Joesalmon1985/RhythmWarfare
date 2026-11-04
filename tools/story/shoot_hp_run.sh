#!/usr/bin/env bash
# Real Godot screenshots of the running Hospital chapter (and its waking cutscene) on a virtual song clock, one window per shot.
#   tools/story/shoot_hp_run.sh <out_dir> <name>:<policy>:<bar>[:ENV=VALUE,ENV=VALUE] ...
#     policy as in capture.sh (perfect, none, sloppy, accuracy:0.8 written accuracy=0.8); bar may be fractional
#   tools/story/shoot_hp_run.sh <out_dir> <name>:interlude:<seconds>[:ENV=VALUE,...]   the `awakening` cutscene held at that time
# Needs a display (DISPLAY defaults to :0).
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="$1"; shift
export DISPLAY="${DISPLAY:-:0}"
RATE=2.0
for spec in "$@"; do
  IFS=':' read -r NAME POLICY AT EXTRA <<< "$spec"
  POLICY="${POLICY//=/:}"
  envs=()
  if [ -n "${EXTRA:-}" ]; then IFS=',' read -r -a envs <<< "$EXTRA"; fi
  if [ "$POLICY" = "interlude" ]; then
    env RW_STORY_INTERLUDE=awakening RW_STORY_INTERLUDE_T="$AT" RW_STORY_INTERLUDE_HOLD=1 "${envs[@]}" \
      "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/scenes/story_interlude.tscn "$OUT" "4:shot:$NAME" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
    continue
  fi
  secs=$(python3 -c "print(($AT-1)*4*60/174)")
  frames=$(python3 -c "print(int(max(($secs-1.0),0)/$RATE)+40)")
  env RW_STORY_CHAPTER=hospital RW_STORY_VIRTUAL=1 RW_STORY_RATE=$RATE RW_STORY_UNTIL_BAR="$AT" RW_AUTOPLAY="$POLICY" "${envs[@]}" \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/scenes/story_play.tscn "$OUT" "$frames:shot:$NAME" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
done
