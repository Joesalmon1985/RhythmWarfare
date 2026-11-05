#!/usr/bin/env bash
# Real Godot screenshots of a sister run (content/paths/<id>; needs a display): every scene, and with --acting every character hotspot in its five states.
#   bash tools/run/capture_path.sh <path id> [out_dir]            docs/shots/<id>/node_<scene>.jpg (a few seconds in) and route_<scene>.jpg (the hotspot window open); RW_SHOTS=<regex> limits them
#   bash tools/run/capture_path.sh <path id> --acting [out_dir]   docs/shots/acting/<id>_<hotspot>.jpg (available | selected | committed | success | failure, the person framed at about 2x)
#                                                                 and contact_acting_<id>_<world>.jpg
# The same virtual-clock, scripted-play runs as tools/run/capture.sh, at the path's tempo (RW_RUN_PATH). Flags a hotspot needs are set with RW_RUN_FLAGS.
set -eu
PID="$1"; shift
ACTING=0
if [ "${1:-}" = "--acting" ]; then ACTING=1; shift; fi
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ROOTW="$(cd "$ROOT" && pwd -W 2>/dev/null || pwd)"  # (a native Windows python needs C:/..., not /c/...)
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
if [ "$ACTING" = 1 ]; then OUT="${1:-$ROOT/docs/shots/acting}"; else OUT="${1:-$ROOT/docs/shots/$PID}"; fi
TMP="$(mktemp -d)"; TMP="$(cygpath -m "$TMP" 2>/dev/null || echo "$TMP")"
mkdir -p "$OUT"
RATE=0.5
BPM=$(python3 -c "import json; print(json.load(open('$ROOTW/content/paths/$PID/run.json'))['timing']['bpm'])")
ONLY="${RW_SHOTS:-}"
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }
beats() { python3 -c "print($1*60/$BPM)"; }

shot() {  # name node bot routes song_seconds [env...]
  local name="$1" node="$2" bot="$3" routes="$4" secs="$5"; shift 5
  want "$name" || return 0
  local frames; frames=$(python3 -c "print(int(($secs+2.0)/$RATE)+2)")
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/data" RW_RUN_PATH="$PID" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$node" RW_RUN_BOT="$bot" RW_RUN_ROUTES="$routes" "$@" \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$frames:shot:$name" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
  if [ -f "$TMP/$name.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$TMP/$name.png" -q:v 3 "$OUT/$name.jpg" && rm -f "$TMP/$name.png"
    echo "shot $OUT/$name.jpg"
  fi
}

acting_run() {  # id scene flags cam policy shot_beat:state ...
  local hid="$1" scene="$2" flags="$3" cam="$4" bot="$5"; shift 5
  local name="${hid//./_}" steps=()
  for bs in "$@"; do
    local beat="${bs%%:*}" st="${bs##*:}" f
    f=$(python3 -c "print(int(($beat*60/$BPM+2.0)/$RATE)+2)")
    steps+=("$f:shot:${name}__${st}")
  done
  local fl=(); [ "$flags" = "-" ] || fl=("RW_RUN_FLAGS=$flags")
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/data" RW_RUN_PATH="$PID" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$scene" RW_RUN_BOT="$bot" RW_RUN_ROUTES="" RW_RUN_CLEAN=1 RW_STORY_CAM="$cam" RW_RUN_SELECT="$hid@52" "${fl[@]}" \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP/acting" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
}

if [ "$ACTING" = 1 ]; then
  mkdir -p "$TMP/acting"
  RATE=0.25
  RW_PATH_ID="$PID" python3 "$ROOTW/tools/run/acting_frames.py" | sed 's/$//' > "$TMP/acting_frames.txt"
  while read -r _world hid scene actor flags cam; do
    want "$hid" || continue
    echo "acting $hid ($actor)"
    acting_run "$hid" "$scene" "$flags" "$cam" perfect 50.5:available 56:selected 60.8:committed 61.8:success
    acting_run "$hid" "$scene" "$flags" "$cam" blocks:1110 61.8:failure
  done < "$TMP/acting_frames.txt"
  RW_PATH_ID="$PID" python3 "$ROOTW/tools/run/contact_acting.py" "$TMP/acting" "$OUT" --prefix "${PID}_"
  rm -rf "$TMP"
  exit 0
fi

python3 - "$ROOTW" "$PID" <<'PY' | sed 's/$//' > "$TMP/scenes.txt"
import json, sys
run = json.load(open("%s/content/paths/%s/run.json" % (sys.argv[1], sys.argv[2])))
for n in run["nodes"]:
    print(n["id"])
PY
while read -r node; do
  f="${node//./_}"
  shot "node_${f}" "$node" perfect "" "$(beats 28)"
  shot "route_${f}" "$node" perfect "" "$(beats 52)"
done < "$TMP/scenes.txt"
rm -rf "$TMP"
