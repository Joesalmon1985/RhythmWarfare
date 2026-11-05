#!/usr/bin/env bash
# Real Godot screenshots of the continuous run (needs a display; opens a window briefly per shot). Writes JPEGs into docs/shots/run (or the folder you give).
#   bash tools/run/capture.sh [out_dir]          RW_SHOTS=<regex> only the shots whose name matches (RW_SHOTS=node_ the scenes, rail_ the rail places, home, route, passage, doorwalk)
#   A scene is a phase at a place in a world: `node_<scene>` and `route_<scene>` (the route window with the lit doors) exist for all 36 scenes (dots in a scene id become underscores
#   in the file name); the rail places are shot for the worlds' entry scenes (RW_RAILS=all: every scene).
# Each shot runs the actual run scene on the virtual song clock (no audio) with a scripted player up to a song time, so the crowd, the camera on its rail, the lights and
# the route window are what a run of that skill is at that moment. `node_*`: the level a few seconds in (the journey's arrival), `rail_<node>_<place>`: the camera stood at
# that rail place (RW_STORY_CAM) in the middle of a perfect phase, `journey_*`: the camera really walking the rail under scripted play.
#   bash tools/run/capture.sh --acting [out_dir]   (stage 1d) every character hotspot in its five states, the actor framed at about 2x: docs/shots/acting/<hotspot>.jpg (a strip of
#                                                   available | selected | committed | success | failure) and contact_acting_<world>.jpg; RW_SHOTS=<regex> limits it to matching hotspot ids
set -eu
ACTING=0
if [ "${1:-}" = "--acting" ]; then ACTING=1; shift; fi
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
if [ "$ACTING" = 1 ]; then OUT="${1:-$ROOT/docs/shots/acting}"; else OUT="${1:-$ROOT/docs/shots/run}"; fi
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
    "$GODOT" --path "$ROOT" "${res[@]}" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$frames:shot:$name" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
  if [ -f "$TMP/$name.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$TMP/$name.png" -q:v 3 "$OUT/$name.jpg" && rm -f "$TMP/$name.png"
    echo "shot $OUT/$name.jpg"
  fi
}


# --- the acting pass (--acting): every character hotspot in its five states, the actor framed by RW_STORY_CAM at about twice the usual size ---------------------------------------------------
# One run with perfect play gives available (beat 50), selected (the scripted touch is at beat 52), committed (the commit is at beat 60.5, the flash lasts one beat) and success (two beats on); a second run that
# misses the last block gives failure. The camera stands where tools/run/acting_frames.py says for the whole run, so the person is in the picture whatever the room does.
acting_run() {  # id scene flags cam policy shot_beat:state ...
  local hid="$1" scene="$2" flags="$3" cam="$4" bot="$5"; shift 5
  local name="${hid//./_}" steps=() last=0
  for bs in "$@"; do
    local beat="${bs%%:*}" st="${bs##*:}" f
    f=$(python3 -c "print(int(($beat*60/174+2.0)/$RATE)+2)")
    steps+=("$f:shot:${name}__${st}"); last="$f"
  done
  local fl=(); [ "$flags" = "-" ] || fl=("RW_RUN_FLAGS=$flags")
  env XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$scene" RW_RUN_BOT="$bot" RW_RUN_ROUTES="" RW_RUN_CLEAN=1 RW_STORY_CAM="$cam" RW_RUN_SELECT="$hid@52" "${fl[@]}"     "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP/acting" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
}
if [ "$ACTING" = 1 ]; then
  mkdir -p "$TMP/acting"
  RATE=0.25
  python3 "$ROOT/tools/run/acting_frames.py" > "$TMP/acting_frames.txt"
  while read -r _world hid scene actor flags cam; do
    want "$hid" || continue
    echo "acting $hid ($actor)"
    acting_run "$hid" "$scene" "$flags" "$cam" perfect 50.5:available 56:selected 61.0:committed 62.6:success
    acting_run "$hid" "$scene" "$flags" "$cam" blocks:1110 62.6:failure
  done < "$TMP/acting_frames.txt"
  python3 "$ROOT/tools/run/contact_acting.py" "$TMP/acting" "$OUT"
  rm -rf "$TMP"
  exit 0
fi

# --- every scene, a few seconds in (the camera has just walked in) and again with the route window open (lit doors) -------------------------------------------------------
python3 - "$ROOT" > "$TMP/scenes.txt" <<'PY'
import json, sys
run = json.load(open(sys.argv[1] + "/content/run/run.json"))
for n in run["nodes"]:
    print(n["id"], int(n["entry"]))
PY
while read -r node entry; do
  f="${node//./_}"
  shot "node_${f}" "$node" perfect "" 9.0
  shot "route_${f}" "$node" perfect "" 19.0
done < "$TMP/scenes.txt"

# --- every rail place of a scene (the camera stood there; a perfect phase, so the crowd is at its best): the entry scenes, or all with RW_RAILS=all -------------------------------
python3 - "$ROOT" "${RW_RAILS:-entry}" > "$TMP/places.txt" <<'PY'
import json, sys
run = json.load(open(sys.argv[1] + "/content/run/run.json"))
for n in run["nodes"]:
    if sys.argv[2] != "all" and not n["entry"]:
        continue
    r = n["place"]["rail"]
    print(n["id"], "home", n["place"]["waypoint"])
    for i, p in enumerate(r["good"], 1):
        print(n["id"], "up%d_%s" % (i, p["to"]), p["to"])
    for i, p in enumerate(r["bad"], 1):
        print(n["id"], "down%d_%s" % (i, p["to"]), p["to"])
PY
while read -r node label wp; do
  shot "rail_${node//./_}_${label}" "$node" perfect "" 14.0 "RW_STORY_CAM=$wp"
done < "$TMP/places.txt"

# --- the camera really walking the rails under scripted play ----------------------------------------------------------------------------------------------------------
shot journey_warehouse_steps      warehouse perfect right 8.0
shot journey_warehouse_balcony    warehouse perfect right 17.0
shot journey_warehouse_booth      warehouse perfect right 21.0
shot journey_warehouse_queasy     warehouse none    right 12.0
shot journey_warehouse_sick       warehouse none    right 21.0
shot journey_mothership_bridge    mothership.bridge perfect "" 21.0
shot journey_underworld_pit       underworld.pit perfect "" 19.0
shot journey_hospital_garden      hospital.garden perfect "" 21.0
shot journey_ward_courtyard       ward.courtyard perfect "" 20.0
shot journey_hospital_late_stage  hospital_late.exit perfect right 20.0

# --- a path inside a world: the camera walks to the door three beats before the downbeat and on through it (no frame; the same stage) --------------------------------------
shot doorwalk_before   warehouse perfect right "$(python3 -c "print(61.5*60/174)")"
shot doorwalk_through  warehouse perfect right "$(python3 -c "print(66*60/174)")"
shot doorwalk_arrived  warehouse perfect right "$(python3 -c "print(78*60/174)")"
shot doorwalk_mothership_reactor mothership perfect up "$(python3 -c "print(70*60/174)")"
shot doorwalk_hospital_corridor  hospital.corridor perfect left "$(python3 -c "print(70*60/174)")"

# --- the passage (a world change keeps the frame): the frame closing on the doorway, the doorway on the new world, the new world opening ------------------------------------
shot passage_closing   warehouse.exit perfect up "$(python3 -c "print(64*60/174-0.55)")"
shot passage_doorway   warehouse.exit perfect up "$(python3 -c "print(64*60/174+0.05)")"
shot passage_opening   warehouse.exit perfect up "$(python3 -c "print(64*60/174+0.75)")"
shot passage_arrived   warehouse.exit perfect up "$(python3 -c "print(64*60/174+6.0)")"

# --- hotspots: before a selection, after it, and after a success and a failure outcome (RW_RUN_SELECT=<hotspot id>@<phase beat> touches it; the bot misses the last block with blocks:1110) -------------
shot hotspots_before     warehouse perfect "" "$(python3 -c "print(53*60/174)")"
shot hotspots_selected   warehouse perfect "" "$(python3 -c "print(55*60/174)")" "RW_RUN_SELECT=warehouse.exit_balcony@52"
shot hotspots_committed  warehouse perfect "" "$(python3 -c "print(60.9*60/174)")" "RW_RUN_SELECT=warehouse.exit_balcony@52"
shot hotspots_success    warehouse perfect "" "$(python3 -c "print(66*60/174)")" "RW_RUN_SELECT=warehouse.dancer@52"
shot hotspots_failure    warehouse blocks:1110 "" "$(python3 -c "print(66*60/174)")" "RW_RUN_SELECT=warehouse.dancer@52"
shot hotspots_wizard     warehouse perfect "" "$(python3 -c "print(8*60/174)")" "RW_RUN_SELECT=warehouse.wizard@3"
shot hotspots_phone      warehouse perfect "" "$(python3 -c "print(55*60/174)")" "RW_RUN_SELECT=warehouse.exit_balcony@52" RW_WINDOW=844x390

# --- the hotspot window of every scene (nothing touched yet: the default brighter), then a contact sheet per world: docs/shots/run/contact_hotspots_<world>.jpg ------------------------------------
while read -r node entry; do
  shot "hotspots_${node//./_}" "$node" perfect "" "$(python3 -c "print(54*60/174)")"
done < "$TMP/scenes.txt"
if [ -z "$ONLY" ] || [[ "contact_hotspots" =~ $ONLY ]]; then python3 "$ROOT/tools/run/contact_hotspots.py" "$OUT"; fi

# --- layouts and settings ---------------------------------------------------------------------------------------------------------------------------------------------------
shot phone_route_window warehouse perfect right 19.0 RW_WINDOW=844x390
shot phone_journey      warehouse perfect right 17.0 RW_WINDOW=844x390
shot wide_20x9_route    mothership perfect right 19.0 RW_WINDOW=1600x720
shot reduced_motion     warehouse perfect right 17.0 RW_REDUCED=1
shot lines_180          warehouse perfect right 17.0 RW_STORY_LINES=180

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
