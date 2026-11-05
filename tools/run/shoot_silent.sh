#!/usr/bin/env bash
# Before/after screenshots of the silent HUD (docs/THREE_PATHS_AND_FACES_PLAN.md 2.4 and 2.6) into docs/shots/silent/ (needs a display; virtual clock, 1280x720):
#   scene_change_before / scene_change_after     the first seconds of a new room (the Balcony): the title card and HUD words with RW_DEV_TEXT=1, then the silent HUD
#   swell_low_after / swell_full_after           the new room's lamps on its downbeat (low) and two beats later (full)
#   route_window_before / route_window_after     the choice window: the RISER caption and numeric stage label, then the thin bar along the bottom of the picture
#   bassment_before / bassment_after             the Bassment's hatch with its caption band, then without
#   bassment_creature_before / _after            the Cable Eel standing in the room: caption band and banner, then the creature's own stance
#   bash tools/run/shoot_silent.sh [out_dir]     GODOT=<console binary> (default: the Windows download folder, else the Linux path of the other capture scripts)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-}"
if [ -z "$GODOT" ]; then
  if [ -n "${USERPROFILE:-}" ]; then GODOT="$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe"; else GODOT="$HOME/godot/Godot_v4.5.1-stable_linux.x86_64"; fi
fi
OUT="${1:-$ROOT/docs/shots/silent}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.5
BEAT=$(python3 -c "print(60/174)" 2>/dev/null || python -c "print(60/174)")
py() { python3 "$@" 2>/dev/null || python "$@"; }

# run_shot <name> <dev_text 0|1> <song seconds> <start node> <routes> [extra env...]
run_shot() {
  local name="$1" dev="$2" secs="$3" node="$4" routes="$5"; shift 5
  local frames
  frames=$(py -c "print(int(($secs+2.0)/$RATE)+2)")
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/appdata" RW_DEV_TEXT=$([ "$dev" = 1 ] && echo 1 || echo "") RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START="$node" RW_RUN_BOT=perfect RW_RUN_ROUTES="$routes" "$@" \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$frames:shot:$name" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
}

# trial_shot <name> <dev_text> <start passage> <taps> <frame>
trial_shot() {
  local name="$1" dev="$2" start="$3" taps="$4" frame="$5"
  env XDG_DATA_HOME="$TMP/data" APPDATA="$TMP/appdata" RW_DEV_TEXT=$([ "$dev" = 1 ] && echo 1 || echo "") RW_RUN_VIRTUAL=1 RW_TRIAL_DIRECT=1 RW_TRIAL_START="$start" RW_TRIAL_BOT=perfect RW_TRIAL_TAPS="$taps" \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "$frame:shot:$name" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" || true
}

# a scene change: the warehouse floor, a perfect player, up to the balcony; the new room's downbeat is at 64 beats
T0=$(py -c "print(64*60/174)")
run_shot scene_change_before 1 "$(py -c "print($T0+1.2)")" warehouse up
run_shot scene_change_after 0 "$(py -c "print($T0+1.2)")" warehouse up
run_shot swell_low_after 0 "$(py -c "print($T0+0.12)")" warehouse up
run_shot swell_full_after 0 "$(py -c "print($T0+2.2*60/174)")" warehouse up
run_shot route_window_before 1 "$(py -c "print(56*60/174)")" warehouse up
run_shot route_window_after 0 "$(py -c "print(56*60/174)")" warehouse up
trial_shot bassment_before 1 1 "" 80
trial_shot bassment_after 0 1 "" 80
trial_shot bassment_creature_before 1 12 "0" 40
trial_shot bassment_creature_after 0 12 "0" 40

for f in "$TMP"/*.png; do
  [ -f "$f" ] || continue
  n="$(basename "$f" .png)"
  ffmpeg -nostdin -y -loglevel error -i "$f" -q:v 3 "$OUT/$n.jpg" && echo "shot $OUT/$n.jpg"
done
rm -rf "$TMP"
