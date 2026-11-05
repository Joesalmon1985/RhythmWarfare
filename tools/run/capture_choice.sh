#!/usr/bin/env bash
# The choice-clarity strips (docs/CHOICE_CLARITY.md, docs/shots/choice/): a scene in four states on the virtual clock, from the player's own camera (or RW_STORY_CAM), at phone size:
#   start (beat 50: the window open, nothing touched, the default is current) | B touched (beat 53) | A touched again (beat 57) | committed (beat 61)
# and, from the scene's first beats, `early` (beat 6: the options are staged before the window).
#   bash tools/run/capture_choice.sh <name> <scene> <option B id> <option A id> [extra env assignments: RW_RUN_PATH=gospel RW_STORY_CAM=... RW_RUN_FLAGS=...]
# Writes docs/shots/choice/<name>_{early,start,b,a,committed}.jpg and <name>_strip.jpg (the five side by side). Needs a display; GODOT names the binary.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
PY="${PYTHON:-python}"
name="$1" scene="$2" b="$3" a="$4"; shift 4
OUT="${CHOICE_OUT:-$ROOT/docs/shots/choice}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.25
fr() { "$PY" -c "print(int(($1*60/${BPM:-174}+2.0)/$RATE)+2)"; }
SHOTS="${SHOTS:-early@6 start@50.5 b@53.5 a@57.5 committed@61.2}"  # label@beat ...
SELECT="${SELECT:-$b@51,$a@55}"  # the touches: id@beat,...
steps=(); labels=()
for sb in $SHOTS; do steps+=("$(fr "${sb##*@}"):shot:${name}_${sb%%@*}"); labels+=("${sb%%@*}"); done
env XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$scene" RW_RUN_BOT=perfect RW_RUN_ROUTES="" RW_RUN_CLEAN=1 \
  RW_RUN_SELECT="$SELECT" "$@" "$GODOT" --path "$ROOT" --resolution 844x390 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "${steps[@]}" 2>&1 </dev/null \
  | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
for s in "${labels[@]}"; do
  [ -f "$TMP/${name}_$s.png" ] && ffmpeg -nostdin -y -loglevel error -i "$TMP/${name}_$s.png" -q:v 3 "$OUT/${name}_$s.jpg" && echo "shot $OUT/${name}_$s.jpg"
done
files=(); for s in "${labels[@]}"; do files+=("$OUT/${name}_$s.jpg"); done
"$PY" "$ROOT/tools/run/choice_strip.py" "$OUT/${name}_strip.jpg" "${files[@]}" && echo "strip $OUT/${name}_strip.jpg"
rm -rf "$TMP"
