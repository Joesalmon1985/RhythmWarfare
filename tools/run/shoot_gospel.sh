#!/usr/bin/env bash
# Real Godot screenshots of the Gospel path (Stage 3): every scene twice, a few seconds in (the camera has walked in, the cast is acting) and with the hotspot window open (beat 54), on the virtual
# song clock, no audio, no HUD (RW_RUN_CLEAN=1). Needs a display. Writes JPEGs into docs/shots/gospel (or the folder you give).
#   bash tools/run/shoot_gospel.sh [out_dir]        RW_SHOTS=<regex> only the scenes whose id matches (dots become underscores in the file names)   GODOT=<console binary>
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
OUT="${1:-$ROOT/docs/shots/gospel}"
cd "$ROOT"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
BEAT=$(python3 -c "print(60/124)")
ONLY="${RW_SHOTS:-}"
IDS=$(python3 -c "
import json
run = json.load(open('content/paths/gospel/run.json'))
print(' '.join('%s:%d' % (n['id'], 64 * (int(n.get('laps', run['path'].get('laps', 1))) - 1)) for n in run['nodes']))")  # (id:beats of the laps before the last: the hotspot window is in the last lap)
for idl in $IDS; do
  id="${idl%%:*}"; lapoff="${idl##*:}"
  [[ -z "$ONLY" || "$id" =~ $ONLY ]] || continue
  name="${id//./_}"
  a=$(python3 -c "print(int((${SHOT_A:-12}*$BEAT+2.0)/$RATE)+2)")
  b=$(python3 -c "print(int(((54+$lapoff)*$BEAT+2.0)/$RATE)+2)")
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_PATH=gospel RW_RUN_START="$id" RW_RUN_BOT=perfect RW_RUN_ROUTES="" RW_RUN_CLEAN=1 ${RW_SHOT_ENV:-} \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$a:shot:${name}_a" "$b:shot:${name}_b" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  for s in a b; do
    if [ -f "$TMP/${name}_$s.png" ]; then
      ffmpeg -nostdin -y -loglevel error -i "$TMP/${name}_$s.png" -q:v 3 "$OUT/${name}_$s.jpg" && rm -f "$TMP/${name}_$s.png"
    fi
  done
  echo "shot $name"
done
rm -rf "$TMP"
