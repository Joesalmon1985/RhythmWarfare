#!/usr/bin/env bash
# Real Godot screenshots of the continuous run (needs a display; opens a window briefly per shot). Writes JPEGs into docs/shots/run (or the folder you give).
#   bash tools/run/capture.sh [out_dir]          RW_SHOTS=<regex> only the shots whose name matches (RW_SHOTS=node_ the nodes, rail_ the rail places, home, route, passage)
# Each shot runs the actual run scene on the virtual song clock (no audio) with a scripted player up to a song time, so the crowd, the camera on its rail, the lights and
# the route window are what a run of that skill is at that moment. `node_*`: the level a few seconds in (the journey's arrival), `rail_<node>_<place>`: the camera stood at
# that rail place (RW_STORY_CAM) in the middle of a perfect phase, `journey_*`: the camera really walking the rail under scripted play.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/run}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
BEAT=$(python3 -c "print(60/174)")
ONLY="${RW_SHOTS:-}"
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }

shot() {  # name node bot routes song_seconds [extra env assignments...]
  local name="$1" node="$2" bot="$3" routes="$4" secs="$5"; shift 5
  want "$name" || return 0
  local frames
  frames=$(python3 -c "print(int(($secs+2.0)/$RATE)+2)")
  local res=()
  for kv in "$@"; do case "$kv" in RW_WINDOW=*) res=(--resolution "${kv#RW_WINDOW=}");; esac; done
  env XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$node" RW_RUN_BOT="$bot" RW_RUN_ROUTES="$routes" "$@" \
    "$GODOT" --path "$ROOT" "${res[@]}" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$frames:shot:$name" 2>&1 | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
  if [ -f "$TMP/$name.png" ]; then
    ffmpeg -y -loglevel error -i "$TMP/$name.png" -q:v 3 "$OUT/$name.jpg" && rm -f "$TMP/$name.png"
    echo "shot $OUT/$name.jpg"
  fi
}

# --- every level, a few seconds in (the camera has just walked in) and again with the route window open ----------------------------------------------------------------
for node in warehouse mothership underworld hospital ward hospital_late ward_late; do
  shot "node_${node}" "$node" perfect up 9.0
  shot "route_${node}" "$node" perfect up 19.0
done

# --- every rail place of every level (the camera stood there; a perfect phase, so the crowd is at its best) ---------------------------------------------------------------
python3 - "$ROOT" > "$TMP/places.txt" <<'PY'
import json, sys
run = json.load(open(sys.argv[1] + "/content/run/run.json"))
for n in run["nodes"]:
    seen = set()
    print(n["id"], "home", n["waypoint"])
    for i, p in enumerate(n["rail"]["good"], 1):
        print(n["id"], "up%d_%s" % (i, p["to"]), p["to"])
    for i, p in enumerate(n["rail"]["bad"], 1):
        print(n["id"], "down%d_%s" % (i, p["to"]), p["to"])
PY
while read -r node label wp; do
  shot "rail_${node}_${label}" "$node" perfect up 14.0 "RW_STORY_CAM=$wp"
done < "$TMP/places.txt"

# --- the camera really walking the rails under scripted play ----------------------------------------------------------------------------------------------------------
shot journey_warehouse_steps      warehouse perfect up 8.0
shot journey_warehouse_balcony    warehouse perfect up 17.0
shot journey_warehouse_booth      warehouse perfect up 21.0
shot journey_warehouse_queasy     warehouse none    up 12.0
shot journey_warehouse_sick       warehouse none    up 21.0
shot journey_mothership_helm      mothership perfect left 21.0
shot journey_underworld_pit       underworld perfect left 19.0
shot journey_hospital_bandstand   hospital perfect left 21.0
shot journey_ward_stage           ward perfect left 20.0
shot journey_hospital_late_stage  hospital_late perfect right 20.0

# --- the passage: the frame closing on the doorway, the doorway on the new world, the new world opening -------------------------------------------------------------
P=$(python3 -c "print(64*60/174)")
shot passage_closing   warehouse perfect up "$(python3 -c "print(64*60/174-0.55)")"
shot passage_doorway   warehouse perfect up "$(python3 -c "print(64*60/174+0.05)")"
shot passage_opening   warehouse perfect up "$(python3 -c "print(64*60/174+0.75)")"
shot passage_arrived   warehouse perfect up "$(python3 -c "print(64*60/174+6.0)")"

# --- layouts and settings ---------------------------------------------------------------------------------------------------------------------------------------------------
shot phone_route_window warehouse perfect up 19.0 RW_WINDOW=844x390
shot phone_journey      warehouse perfect up 17.0 RW_WINDOW=844x390
shot wide_20x9_route    mothership perfect up 19.0 RW_WINDOW=1600x720
shot reduced_motion     warehouse perfect up 17.0 RW_REDUCED=1
shot lines_180          warehouse perfect up 17.0 RW_STORY_LINES=180

# --- home, and both entry points end to end: keys press the buttons (Play is focused; Down goes to Story chapters) ---------------------------------------------------------------
home() {  # name "steps..."
  local name="$1"; shift
  want "$name" || return 0
  env XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_BOT=perfect RW_AUTOPLAY=perfect "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/scenes/main_menu.tscn "$TMP" "$@" 2>&1 \
    | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
  for f in "$TMP"/*.png; do
    [ -f "$f" ] || continue
    b="$(basename "$f" .png)"
    ffmpeg -y -loglevel error -i "$f" -q:v 3 "$OUT/$b.jpg" && rm -f "$f" && echo "shot $OUT/$b.jpg"
  done
}
home home_screen 20:shot:home_screen
home home_play_enters_the_run 10:keydown:Enter 11:keyup:Enter 80:shot:home_play_enters_the_run
home home_chapters_menu 10:keydown:Down 11:keyup:Down 12:keydown:Enter 13:keyup:Enter 50:shot:home_chapters_menu
home home_chapters_enter_a_chapter 10:keydown:Down 11:keyup:Down 12:keydown:Enter 13:keyup:Enter 40:keydown:Enter 41:keyup:Enter 140:shot:home_chapters_enter_a_chapter
rm -rf "$TMP"
