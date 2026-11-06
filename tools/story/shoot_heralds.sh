#!/usr/bin/env bash
# Shots of the quest entrances and their heralds (docs/art/HERALDS.md): the real run scene on the virtual song clock, a few seconds in (the herald must already be
# there) and in the route window, with the flags each entrance needs, plus a close shot framed on the herald (RW_STORY_CAM=@x:z:yaw:pitch).
#   bash tools/story/shoot_heralds.sh [out_dir] [tag]     default out_dir docs/shots/art/heralds, tag "after" (file names <tag>_<entrance>_<when>.jpg)
#   RW_SHOTS=<regex> only the shots whose name matches. GODOT: the Godot binary or tools/dev/godot.sh (the queue wrapper).
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$ROOT/tools/dev/godot.sh}"
OUT="${1:-$ROOT/docs/shots/art/heralds}"
TAG="${2:-after}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
ONLY="${RW_SHOTS:-}"
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
  local env_=(XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$node" RW_RUN_BOT=perfect RW_RUN_ROUTES="")
  [ "$flags" = "-" ] || env_+=(RW_RUN_FLAGS="$flags")
  [ "$cam" = "-" ] || env_+=(RW_STORY_CAM="$cam" RW_RUN_CLEAN=1)  # (a close shot: no notes or HUD over the herald; the plain shots keep the pads and the HUD, to see that nothing overlaps them)
  env "${env_[@]}" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI\|ERR_CANT_OPEN" || true
  for nm in "${names[@]}"; do
    if [ -f "$TMP/$nm.png" ]; then
      ffmpeg -nostdin -y -loglevel error -i "$TMP/$nm.png" -q:v 3 "$OUT/$nm.jpg" && rm -f "$TMP/$nm.png"
      echo "shot $OUT/$nm.jpg"
    fi
  done
}

# entrance       scene              flags          close camera (x:z:yaw:pitch, looking at the entrance and its herald)
while read -r ent node flags cam; do
  shots "$node" "$flags" - "${TAG}_${ent}_start:5.0" "${TAG}_${ent}_early:9.0" "${TAG}_${ent}_route:19.0"
  [ "$cam" = "-" ] || shots "$node" "$flags" "@$cam" "${TAG}_${ent}_close:5.0" "${TAG}_${ent}_close_b:5.4" "${TAG}_${ent}_close_route:19.0"
done <<'LIST'
dungeon_floor  warehouse          -              -1.5:7.0:90:0
gospel_star    warehouse.balcony  wh_saw_floor   -7.5:1.4:90:6
squadron_radio warehouse.booth    -              0.6:-4.6:0:4
ember_glass    warehouse.bar      wh_vip_pass    7.6:2.2:-125:0
LIST
rm -rf "$TMP"
