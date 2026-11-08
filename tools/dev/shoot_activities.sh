# A rave's three activities in the real run scene at 16:9 and 20:9 (tools/engine/shoot_space_activities.gd) and their contact sheet docs/shots/bedsit/<theme>/activities.jpg.
#   bash tools/dev/shoot_activities.sh magic [out dir]        (theme: space | magic | dinos | transport)
set -u
THEME="${1:?theme: space | magic | dinos | transport}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${2:-${TMPDIR:-/tmp}/${THEME}_activity_shots}"
mkdir -p "$OUT"
for size in 1280x720 1600x720; do
  bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" -s tools/engine/shoot_space_activities.gd -- "$OUT" "$THEME" 2>&1 | grep -E "SCRIPT" || true
done
python3 "$ROOT/tools/dev/space_activities_sheet.py" "$OUT" "$ROOT/docs/shots/bedsit/$THEME/activities.jpg" "$THEME"
