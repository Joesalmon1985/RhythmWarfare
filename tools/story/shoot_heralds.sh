#!/usr/bin/env bash
# Shots of the quest entrances and their heralds (docs/art/HERALDS.md): the real run scene on the virtual song clock, a few seconds in (the herald must already be
# there) and in the route window, with the flags each entrance needs, plus a close shot framed on the herald (RW_STORY_CAM=@x:z:yaw:pitch).
#   bash tools/story/shoot_heralds.sh [out_dir] [tag]     default out_dir docs/shots/art/heralds, tag "after" (file names <tag>_<entrance>_<when>.jpg)
#   RW_SHOTS=<regex> only the shots whose name matches. GODOT: the Godot binary or tools/dev/godot.sh (the queue wrapper). RW_WINDOW=1600x720: the window's size (a 20:9 phone).
#   RW_HERALD_CLOSE=0: no close shots. The plain shots are the real camera: `start` 3 s in (beat 8.7, the heralds' look holds the entrance: RunJourney.herald_looks), `route` 19 s (the window).
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$ROOT/tools/dev/godot.sh}"
OUT="${1:-$ROOT/docs/shots/art/heralds}"
TAG="${2:-after}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
ONLY="${RW_SHOTS:-}"
RES=()
[ -n "${RW_WINDOW:-}" ] && RES=(--resolution "$RW_WINDOW")
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }

shots() {  # node flags cam name:seconds ...   (one Godot run per entrance and camera)
  local node="$1" flags="$2" cam="$3"; shift 3
  local steps=() names=()
  for ns in "$@"; do
    local nm="${ns%%:*}" secs="${ns##*:}"
    want "$nm" || continue
    steps+=("$(python3 -c "print(int(($secs+2.0)/$RATE)+2)"):shot:$nm"); names+=("$nm")
  done
  [ "${#steps[@]}" -gt 0 ] || return 0
  local env_=(XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$node" RW_RUN_BOT=perfect RW_RUN_ROUTES="${ROUTES_:-}")
  [ "$flags" = "-" ] || env_+=(RW_RUN_FLAGS="$flags")
  [ "$cam" = "-" ] || env_+=(RW_STORY_CAM="$cam" RW_RUN_CLEAN=1)  # (a close shot: no notes or HUD over the herald; the plain shots keep the pads and the HUD, to see that nothing overlaps them)
  env "${env_[@]}" "$GODOT" --path "$ROOT" "${RES[@]}" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  for nm in "${names[@]}"; do
    if [ -f "$TMP/$nm.png" ]; then
      ffmpeg -nostdin -y -loglevel error -i "$TMP/$nm.png" -q:v 3 "$OUT/$nm.jpg" && rm -f "$TMP/$nm.png"
      echo "shot $OUT/$nm.jpg"
    fi
  done
}

# The plain shots come into the scene the way a run does (from the Warehouse's first scene, by the routes in the last column, one 64-beat phase each), so the camera is the
# one the player has: through the door, the heralds' look, the rail. The close shots start in the scene itself.
PHASE_S=$(python3 -c "print(64*60/174)")
# entrance       scene              flags          close camera (x:z:yaw:pitch, looking at the entrance and its herald)   routes from the Warehouse (- none)
while read -r ent node flags cam via; do
  [[ "$ent" == \#* ]] && continue  # (a comment line of the list)
  if [ "$via" = "-" ]; then start="$node"; ROUTES_=""; off=0; else start=warehouse; ROUTES_="$via"; off=$(python3 -c "print(len('$via'.split(','))*$PHASE_S)"); fi
  t0=$(python3 -c "print(round($off+3.0,2))"); t1=$(python3 -c "print(round($off+19.0,2))")
  t0b=$(python3 -c "print(round($off+4.2,2))")  # (start_b: 4.2 s, beat 12: the camera has walked in through the door)
  ROUTES_="$ROUTES_" RW_RUN_START_="$start" shots "$start" "$flags" - "${TAG}_${ent}_start:$t0" "${TAG}_${ent}_start_b:$t0b" "${TAG}_${ent}_route:$t1"
  ROUTES_=""
  [ "$cam" = "-" ] || [ "${RW_HERALD_CLOSE:-1}" = "0" ] || shots "$node" "$flags" "@$cam" "${TAG}_${ent}_close:5.0" "${TAG}_${ent}_close_b:5.4" "${TAG}_${ent}_close_route:19.0"
done <<'LIST'
dungeon_floor  warehouse          -              -1.5:7.0:90:0     -
gospel_star    warehouse.balcony  wh_saw_floor   -7.5:1.4:90:6     up
squadron_radio warehouse.booth    -              0.6:-4.6:0:4      up,left
ember_glass    warehouse.bar      wh_vip_pass    7.6:2.2:-125:0    right
chill_wizard   warehouse.chill    -              -                 right,right
# Mental Hospital (N2.4)
ward_bassment  ward               -              1.8:5.4:-120:2    right,right,up,up,right,up,up,right
ward_gospel    ward               -              1.8:5.4:-130:2    right,right,up,up,right,up,up,right
ward_squadron  ward               -              2.6:5.4:-110:2    right,right,up,up,right,up,up,right
ward_ember     ward               -              3.0:5.2:-100:2    right,right,up,up,right,up,up,right
ward_art_bassment ward.art           -              41.0:8.0:137:2    right,right,up,up,right,up,up,right,right
ward_dorm_gospel ward.dorm          -              26.0:9.6:156:0     right,right,up,up,right,up,up,right,up
ward_corridor_squadron ward.corridor      -              20.0:5.0:124:2    right,right,up,up,right,up,up,right,right,up
ward_courtyard_ember ward.courtyard     -              55.5:6.5:-70:2    right,right,up,up,right,up,up,right,right,up,up
ward_late_treat_bassment ward_late.treat    -              14.6:8.6:-144:0    right,right,up,up,right,up,up,left,up,left,up,up,right,left
ward_late_dorm_gospel ward_late.dorm     -              26.0:9.6:156:0    right,right,up,up,right,up,up,left,up,left,up,up,right,right
LIST
rm -rf "$TMP"
