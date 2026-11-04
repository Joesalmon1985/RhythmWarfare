#!/usr/bin/env bash
# One screenshot per zone of the Bassment (the zone's first passage, window open, exits lit) into docs/shots/trial/, then the contact sheet.
#   bash tools/trial/capture.sh [out_dir]     RW_ZONES=<regex on zone id> limits it; RW_JOBS parallel shots (default 3)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/trial}"; JOBS="${RW_JOBS:-3}"; ONLY="${RW_ZONES:-}"
mkdir -p "$OUT"
one() {
  local zone="$1" start="$2"
  env RW_RUN_VIRTUAL=1 RW_TRIAL_DIRECT=1 RW_TRIAL_START="$start" RW_TRIAL_BOT=perfect \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$OUT" "80:shot:zone_$zone" 2>&1 | grep -E "ERROR|SCRIPT" || true
}
while read -r zone start; do
  [ -z "$ONLY" ] || [[ "$zone" =~ $ONLY ]] || continue
  one "$zone" "$start" &
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do sleep 1; done
done < <(python3 "$ROOT/tools/trial/contact_sheet.py" --list)
wait
python3 "$ROOT/tools/trial/contact_sheet.py" "$OUT"
