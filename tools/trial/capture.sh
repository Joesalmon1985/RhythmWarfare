#!/usr/bin/env bash
# Screenshots of the Bassment into docs/shots/trial/ (needs a display; virtual clock, 1280x720):
#   zone_<zone>.png      the zone's first passage, window open, the hotspots lit (the default brighter), no text but the caption band; then contact_bassment.jpg
#   select_before / select_after   the hatch before and after a tap on the second hotspot (the scripted finger goes through the hit test: RW_TRIAL_TAPS)
#   fight_1_hotspot / fight_2_phrase / fight_3_win   the Cable Eel standing in the room as a hotspot, tapped, then the phrase and the win
#   death_before / death_tableau    the way out of a death, lit, then YOU DIED     victory_before / victory_tableau
#   bash tools/trial/capture.sh [out_dir]     RW_ZONES=<regex on zone id> limits the zone shots; RW_JOBS parallel shots (default 3); RW_SPECIAL=0 skips the others
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/trial}"; JOBS="${RW_JOBS:-3}"; ONLY="${RW_ZONES:-}"
mkdir -p "$OUT"
# shoot <start passage> <taps or ""> <step> ...   (steps are frame:shot:name for tools/shoot.gd)
shoot() {
  local start="$1" taps="$2"; shift 2
  env RW_RUN_VIRTUAL=1 RW_TRIAL_DIRECT=1 RW_TRIAL_START="$start" RW_TRIAL_BOT=perfect RW_TRIAL_TAPS="$taps" \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$OUT" "$@" 2>&1 | grep -E "ERROR|SCRIPT" || true
}
while read -r zone start; do
  [ -z "$ONLY" ] || [[ "$zone" =~ $ONLY ]] || continue
  shoot "$start" "" "80:shot:zone_$zone" &
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do sleep 1; done
done < <(python3 "$ROOT/tools/trial/contact_sheet.py" --list)
wait
if [ "${RW_SPECIAL:-1}" = "1" ] && [ -z "$ONLY" ]; then
  shoot 1 "1" "40:shot:select_before" "120:shot:select_after" &
  shoot 12 "0" "40:shot:fight_1_hotspot" "230:shot:fight_2_phrase" "345:shot:fight_3_win" &
  shoot 13 "" "20:shot:death_before" "50:shot:death_tableau" &
  wait
  shoot 63 "" "20:shot:victory_before" "50:shot:victory_tableau"
fi
python3 "$ROOT/tools/trial/contact_sheet.py" "$OUT"
