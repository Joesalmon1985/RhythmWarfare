#!/usr/bin/env bash
# Headless shots of a Doom worlds scene, at 16:9 (1280x720) and 20:9 (1600x720): every choice viewpoint, reveal viewpoint and destination approach with the camera stood at the
# waypoint (RW_STORY_CAM=<waypoint>, the real run scene, HUD and pads on, so overlaps show), and the stay loop on the real rail camera at song times.
#   bash tools/doom/shoot_scene.sh --scene doom_warehouse [out_dir]      default out_dir docs/shots/doom/warehouse
#   RW_SHOTS=<regex> only the shots whose name matches.   GODOT: the Godot binary or tools/dev/godot.sh.
# RW_WALK=1 adds the walk strips (python3 tools/doom/shoot_scene.py walk <out_dir>).
# Then a contact sheet: python3 tools/doom/shoot_scene.py <out_dir>   (run by this script at the end), and python3 tools/shrink_shots.py <out_dir>.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCENE="doom_warehouse"
if [ "${1:-}" = "--scene" ]; then SCENE="$2"; shift 2; fi
OUT="${1:-$ROOT/docs/shots/doom/warehouse}"
GODOT="${GODOT:-$ROOT/tools/dev/godot.sh}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
ONLY="${RW_SHOTS:-}"
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }
[ "$SCENE" = "doom_warehouse" ] || { echo "only doom_warehouse has a shot list so far" >&2; exit 2; }

shot() {  # name aspect(16x9|20x9) cam(- for the rail camera) seconds
  local nm="$1" asp="$2" cam="$3" secs="$4" res="1280x720"
  [ "$asp" = "20x9" ] && res="1600x720"
  want "$nm" || return 0
  local steps="$(python3 -c "print(int(($secs+2.0)/$RATE)+2)"):shot:${nm}_${asp}"
  local env_=(XDG_DATA_HOME="$TMP/data" RW_DOOM_WORLDS=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$SCENE" RW_RUN_BOT=perfect)
  [ "$cam" = "-" ] || env_+=(RW_STORY_CAM="$cam")
  env "${env_[@]}" "$GODOT" --path "$ROOT" --resolution "$res" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$steps" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  if [ -f "$TMP/${nm}_${asp}.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$TMP/${nm}_${asp}.png" -q:v 3 "$OUT/${nm}_${asp}.jpg" && rm -f "$TMP/${nm}_${asp}.png"
    echo "shot $OUT/${nm}_${asp}.jpg"
  fi
}

# the guide-state captures (round 2, DOOM_WORLDS_BRIEF section 8): the rail camera, the guide tapped at beat 50 of the choice window (RW_RUN_SELECT), shot on the hold with
# the guide selected (beat 50.4, the tap commits: ruling 39) and on an early frame of the walk off with it committed (beat 52); a finer frame step so the beats land
sshot() {  # name hotspot beat
  local nm="$1" hid="$2" beat="$3" rate=0.125
  want "$nm" || return 0
  local f="$(python3 -c "print(int(round(($beat*60.0/174.0+2.0)/$rate))+2)")"
  env XDG_DATA_HOME="$TMP/data" RW_DOOM_WORLDS=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=$rate RW_RUN_START="$SCENE" RW_RUN_BOT=perfect RW_RUN_SELECT="$hid@50"     "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$f:shot:${nm}_16x9" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  if [ -f "$TMP/${nm}_16x9.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$TMP/${nm}_16x9.png" -q:v 3 "$OUT/${nm}_16x9.jpg" && rm -f "$TMP/${nm}_16x9.png"
    echo "shot $OUT/${nm}_16x9.jpg"
  fi
}
for g in "stage balcony" "bar bar" "lounge lounge"; do
  set -- $g
  sshot "state_$1_selected" "$SCENE.exit_$2" 50.4
  sshot "state_$1_committed" "$SCENE.exit_$2" 52
done

for asp in 16x9 20x9; do
  shot ref "$asp" wh_ref 3
  shot reveal_fence "$asp" wh_fence 3
  shot reveal_plinths "$asp" wh_plinths 3
  shot reveal_platform "$asp" wh_platform 3
  shot arrive_corridor "$asp" wh_arrive 3
  shot approach_stage_a "$asp" wh_stage_approach 3
  shot approach_stage_b "$asp" wh_stage_steps 3
  shot approach_stage_c "$asp" wh_stage_top 3
  shot approach_bar_a "$asp" wh_bar_approach 3
  shot approach_bar_b "$asp" wh_bar_door 3
  shot approach_lounge_a "$asp" wh_lounge_approach 3
  shot approach_lounge_b "$asp" wh_lounge_door 3
  shot stumble "$asp" wh_ref_back 3
  # the stay loop on the rail camera (the default route: fence, plinths, platform, back to the reference), at four song times
  shot stay_1 "$asp" - 14
  shot stay_2 "$asp" - 28
  shot stay_3 "$asp" - 42
  shot stay_4 "$asp" - 56
done
rm -rf "$TMP"
python3 "$ROOT/tools/doom/shoot_scene.py" "$OUT" || true
[ -z "${RW_WALK:-}" ] || python3 "$ROOT/tools/doom/shoot_scene.py" walk "$OUT" || true   # RW_WALK=1: also the camera-path strips of the ahead route and the stay loop (walk_ahead.jpg, walk_stay.jpg)
