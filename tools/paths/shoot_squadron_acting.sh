#!/usr/bin/env bash
# The Mission Count's acting shots (needs a display): every hotspot that directs a person in its five states, the person framed at about twice the usual size, at 140 BPM:
#   GODOT=<console binary> bash tools/paths/shoot_squadron_acting.sh [out_dir]       RW_SHOTS=<regex on the hotspot id> limits it. See tools/run/capture.sh --acting (the same method).
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/acting}"
TMP="$(mktemp -d)"
mkdir -p "$TMP/acting"
RATE=0.25
ONLY="${RW_SHOTS:-}"
BEAT=$(python3 -c "print(60/140)")
acting_run() {  # id scene cam bot shot_beat:state ...
  local hid="$1" scene="$2" cam="$3" bot="$4"; shift 4
  local name="${hid//./_}" steps=() f
  for bs in "$@"; do
    local beat="${bs%%:*}" st="${bs##*:}"
    f=$(python3 -c "print(int((($beat+64)*$BEAT+2.0)/$RATE)+2)")  # (every scene of the Mission Count plays two laps: the hotspots are on show in the second)
    steps+=("$f:shot:${name}__${st}")
  done
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/data" RW_RUN_PATH=squadron RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$scene" RW_RUN_BOT="$bot" RW_RUN_ROUTES="" RW_RUN_CLEAN=1 RW_STORY_CAM="$cam" RW_RUN_SELECT="$hid@52" \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP/acting" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
}
python3 "$ROOT/tools/paths/acting_squadron.py" list | tr -d '\r' > "$TMP/frames.txt"
while read -r _world hid scene actor cam; do
  [ -z "$ONLY" ] || [[ "$hid" =~ $ONLY ]] || continue
  echo "acting $hid ($actor)"
  acting_run "$hid" "$scene" "$cam" perfect 50.5:available 56:selected 61.0:committed 62.6:success
  acting_run "$hid" "$scene" "$cam" blocks:1110 62.6:failure
done < "$TMP/frames.txt"
python3 "$ROOT/tools/paths/acting_squadron.py" stitch "$TMP/acting" "$OUT"
rm -rf "$TMP"
