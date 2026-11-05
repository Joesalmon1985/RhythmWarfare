#!/usr/bin/env bash
# The scripted walk of the Bassment on the real scene: from the Warehouse, the wizard is chosen, the dungeon is entered through the hatch, the choices are made and the run walks back up
# into the Warehouse. Virtual clock, isolated save (HOME and user:// are a temp dir).   bash tools/trial/walk_trial.sh
#   walk 1: nobody picks anything (the default of every window) to the victory.
#   walk 2: the picks are made by TAPS (RW_TRIAL_TAPS, one token per window: a hotspot index, or d for no tap): the finger lands on the centre of that hotspot's target, through the
#           same hit test a phone uses; the walk must still reach the victory, and every tap must have hit the hotspot it aimed at.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
TMP="$(mktemp -d /tmp/claude-1000/walk_trial.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
ok=1
walk() {  # walk <label> [extra env ...]
  local label="$1"; shift
  local out
  out=$(env HOME="$TMP" XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_RUN_BOT=perfect RW_RUN_START=warehouse RW_TRIAL_ENTER=1 RW_TRIAL_UNTIL=63 RW_TRIAL_LEAVE_QUIT=1 RW_STORY_QUIT=1 RW_TRIAL_TRACE=1 "$@" \
    "$GODOT" --headless --path "$ROOT" res://src/run/run_play.tscn 2>&1)
  echo "== $label"
  echo "$out" | grep -E "^TRIAL (t=|reached|left|tap)" | tail -40
  echo "$out" | grep -E "SCRIPT ERROR|^ERROR" | head
  if ! { echo "$out" | grep -q "TRIAL reached passage 63" && echo "$out" | grep -q "TRIAL left (victory)"; }; then ok=0; echo "$label: the victory was not reached"; fi
  if [ "$label" = "taps" ]; then
    local taps hits
    taps=$(echo "$out" | grep -c "^TRIAL tap ")
    hits=$(echo "$out" | grep "^TRIAL tap " | awk '$4 == "->" && $3 == $5 {n++} END {print n+0}')
    echo "taps: $taps made, $hits hit the hotspot aimed at"
    if [ "$taps" -lt 3 ] || [ "$taps" != "$hits" ]; then ok=0; echo "taps: some missed their hotspot (or too few were made)"; fi
  fi
}
walk defaults
# the picks: hatch 1 (chalk 1), cable run 4 (the second way), live junction 5 (the first), the rest the defaults, plus a change of mind is covered by the tests
walk taps RW_TRIAL_TAPS="1;d;d;0;d;0;d;d;d;d;d;d;d;d;d;d;d;d;d;d"
if [ "$ok" = "1" ]; then echo "WALK OK"; exit 0; fi
echo "WALK FAILED"; exit 1
