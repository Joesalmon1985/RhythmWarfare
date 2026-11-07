# A new rave (magic | dinos | transport) through the game's low-res pipeline (tools/story/preview_map.gd), at 16:9 and 20:9: the hub viewpoint, the stage approach, the deck before and after the bass is
# fixed, the cloakroom and the bar holds. Writes docs/shots/bedsit/<theme>/<theme>_contact.jpg.   bash tools/dev/shoot_rave.sh magic [out dir]
set -u
THEME="${1:?theme: magic | dinos | transport}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${2:-${TMPDIR:-/tmp}/${THEME}_shots}"
SHEET="$ROOT/docs/shots/bedsit/$THEME/${THEME}_contact.jpg"
mkdir -p "$OUT" "$(dirname "$SHEET")"
case "$THEME" in
  magic) MAP=magic_rave; LIGHTS="mg_aurora,mg_sparkle_ring,mg_orb_dome"; KNOB="res://assets/story/rave_magic/textures/mg_knob_" ;;
  dinos) MAP=dino_rave; LIGHTS="dn_lava_sheets,dn_fire_ring,dn_ember_dome"; KNOB="res://assets/story/rave_dinos/textures/dn_knob_" ;;
  transport) MAP=transport_rave; LIGHTS="tr_signal_beams,tr_track_lights,tr_headlamp_dome"; KNOB="res://assets/story/rave_transport/textures/tr_knob_" ;;
esac
POSES="$(python3 - "$ROOT/content/story/maps/$MAP.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
w = {x["id"]: x for x in m["waypoints"]}
def pose(i, dz=0.0):
    p = w[i]
    return "%s,%s,%s" % (p["at"][0], p["at"][1] + dz, p["yaw"])
print("hub", pose("hub_view"))
print("approach", pose("stage_foot"))
print("deck_before", pose("deck_view"))
print("deck_after", pose("deck_view"))
print("cloak", pose("cloak_hold"))
print("bar", pose("bar_hold"))
PY
)"
for size in 1280x720 1600x720; do
  echo "$POSES" | while read -r name pose; do
    extra="X=1"
    [ "$name" = deck_before ] && extra="RW_PREVIEW_KNOB=0 RW_PREVIEW_KNOB_PREFIX=$KNOB"
    [ "$name" = deck_after ] && extra="RW_PREVIEW_KNOB=3 RW_PREVIEW_KNOB_PREFIX=$KNOB RW_PREVIEW_PIECES=$LIGHTS"
    env $extra RW_MAP=$MAP RW_PREVIEW_POSE="$pose" RW_PREVIEW_T=8 bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" -s tools/shoot.gd -- res://tools/story/preview_map.tscn "$OUT" "30:shot:${name}_${size}" 2>&1 | grep -E "SCRIPT" || true
  done
done
python3 "$ROOT/tools/dev/rave_sheet.py" "$OUT" "$SHEET"
