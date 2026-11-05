#!/usr/bin/env bash
# Real Godot screenshots of the Mission Count path (needs a display): every scene a few seconds in (node_<scene>) and with the hotspot window open (route_<scene>), at 140 BPM.
#   GODOT=<console binary> bash tools/paths/shoot_squadron.sh [out_dir]      RW_SHOTS=<regex> limits the shots by name; RW_SECS="6 24" changes the song seconds
# The run is the real scene on the virtual song clock (no audio) from a throwaway user directory (APPDATA / XDG_DATA_HOME).
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/squadron}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
ONLY="${RW_SHOTS:-}"
read -r S1 S2 <<< "${RW_SECS:-6 24}"
shot() {  # name node secs [extra env]
  local name="$1" node="$2" secs="$3"; shift 3
  [ -z "$ONLY" ] || [[ "$name" =~ $ONLY ]] || return 0
  local frames
  frames=$(python3 -c "print(int(($secs+2.0)/$RATE)+2)")
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/data" RW_RUN_PATH=squadron RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$node" RW_RUN_BOT=perfect RW_RUN_ROUTES="" "$@" \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$frames:shot:$name" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" || true
  if [ -f "$TMP/$name.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$TMP/$name.png" -q:v 3 "$OUT/$name.jpg" && rm -f "$TMP/$name.png"
    echo "shot $OUT/$name.jpg"
  fi
}
python3 - "$ROOT" > "$TMP/scenes.txt" <<'PY'
import json, sys
run = json.load(open(sys.argv[1] + "/content/paths/squadron/run.json"))
for n in run["nodes"]:
    print(n["id"], n["scene"])
PY
while read -r node code; do
  shot "node_${code}" "$node" "$S1"
  shot "route_${code}" "$node" "$S2"
done < <(sed 's/[[:cntrl:]]//g' "$TMP/scenes.txt")
rm -rf "$TMP"
