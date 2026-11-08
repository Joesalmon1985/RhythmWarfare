#!/usr/bin/env bash
# Headless shots of the Chill-out Lounge (docs/doom/scenes/lounge.md), at 16:9 (1280x720) and 20:9 (1600x720): the reference viewpoint, the reveal viewpoints and the three route approaches with the
# camera stood at the waypoint (RW_STORY_CAM=<waypoint>, the real run scene, HUD and pads on, so overlaps show), and the stay loop on the real rail camera at song times.
#   bash tools/doom/shoot_lounge.sh [out_dir]        default out_dir docs/shots/doom/lounge
#   RW_SHOTS=<regex> only the shots whose name matches.   GODOT: the Godot binary or tools/dev/godot.sh.
# Then the contact sheet and the walk strips: python3 tools/doom/shoot_lounge.py <out_dir> (run by this script at the end).
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCENE="doom_lounge"
OUT="${1:-$ROOT/docs/shots/doom/lounge}"
GODOT="${GODOT:-$ROOT/tools/dev/godot.sh}"
TMP="$(mktemp -d)"
RAW="$TMP/raw"
mkdir -p "$OUT" "$RAW"
RATE=0.5
ONLY="${RW_SHOTS:-}"
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }

shot() {  # name aspect(16x9|20x9) cam(- for the rail camera) seconds
  local nm="$1" asp="$2" cam="$3" secs="$4" res="1280x720"
  [ "$asp" = "20x9" ] && res="1600x720"
  want "$nm" || return 0
  local steps="$(python3 -c "print(int(($secs+2.0)/$RATE)+2)"):shot:${nm}_${asp}"
  local env_=(XDG_DATA_HOME="$TMP/data" RW_DOOM_WORLDS=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$SCENE" RW_RUN_BOT=perfect)
  [ "$cam" = "-" ] || env_+=(RW_STORY_CAM="$cam")
  env "${env_[@]}" "$GODOT" --path "$ROOT" --resolution "$res" -s tools/shoot.gd -- res://src/run/run_play.tscn "$RAW" "$steps" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  if [ -f "$RAW/${nm}_${asp}.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$RAW/${nm}_${asp}.png" -q:v 3 "$TMP/${nm}_${asp}.jpg" && echo "shot ${nm}_${asp}"
  fi
}

# the guide-state captures (round 2): the rail camera, the guide tapped at beat 50 of the first window (RW_RUN_SELECT), shot on the hold (beat 50.4, selected) and early in the
# walk off (beat 52, committed); a finer frame step so the beats land
sshot() {  # name hotspot beat
  local nm="$1" hid="$2" beat="$3" rate=0.125
  want "$nm" || return 0
  local f="$(python3 -c "print(int(round(($beat*60.0/174.0+2.0)/$rate))+2)")"
  env XDG_DATA_HOME="$TMP/data" RW_DOOM_WORLDS=1 RW_RUN_VIRTUAL=1 RW_STORY_RATE=$rate RW_RUN_START="$SCENE" RW_RUN_BOT=perfect RW_RUN_SELECT="$hid@50" "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$RAW" "$f:shot:${nm}_16x9" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  if [ -f "$RAW/${nm}_16x9.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$RAW/${nm}_16x9.png" -q:v 3 "$TMP/${nm}_16x9.jpg" && echo "shot ${nm}_16x9"
  fi
}
for g in "dock dock" "bar bar" "floor floor"; do
  set -- $g
  sshot "state_$1_selected" "$SCENE.exit_$2" 50.4
  sshot "state_$1_committed" "$SCENE.exit_$2" 52
done

for asp in 16x9 20x9; do
  shot ref "$asp" lg_ref,0,-12 3   # round 2: the reference viewpoint at the pitch its choice window holds (rail place `pitch` -12)
  shot ref_level "$asp" lg_ref 3
  shot reveal_se "$asp" lg_se_view 3
  shot reveal_west "$asp" lg_west 3
  shot reveal_north "$asp" lg_north 3
  shot reveal_east "$asp" lg_east 3
  shot arrive_passage "$asp" lg_arrive 3
  shot approach_dock "$asp" lg_ahead_door 3
  shot approach_bar "$asp" lg_bar_door 3
  shot approach_floor "$asp" lg_floor_door 3
  shot stumble "$asp" lg_ref_back 3
  # the stay loop on the rail camera (west, north, east reveals, back to the reference), at four song times
  shot stay_1 "$asp" - 14
  shot stay_2 "$asp" - 28
  shot stay_3 "$asp" - 42
  shot stay_4 "$asp" - 56
done
python3 "$ROOT/tools/doom/shoot_lounge.py" "$TMP" "$OUT" || true
[ -z "${RW_KEEP:-}" ] || { mkdir -p "$RW_KEEP"; cp "$TMP"/*.jpg "$RW_KEEP"/ 2>/dev/null || true; }   # RW_KEEP=<dir>: keep the per-frame jpgs there (for looking at; they are not committed)
rm -rf "$TMP"
