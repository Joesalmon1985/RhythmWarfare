#!/usr/bin/env bash
# The scripted walk of the Bassment on the real scene: from the Warehouse, the wizard is chosen, the dungeon is entered through the hatch, the default choices are walked
# to the victory and the run walks back up into the Warehouse. Virtual clock, isolated save (HOME and user:// are a temp dir).   bash tools/trial/walk_trial.sh
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
TMP="$(mktemp -d /tmp/claude-1000/walk_trial.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
out=$(env HOME="$TMP" XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_RUN_BOT=perfect RW_RUN_START=warehouse RW_TRIAL_ENTER=1 RW_TRIAL_UNTIL=63 RW_TRIAL_LEAVE_QUIT=1 RW_STORY_QUIT=1 RW_TRIAL_TRACE=1 \
  "$GODOT" --headless --path "$ROOT" res://src/run/run_play.tscn 2>&1)
echo "$out" | grep -E "^TRIAL (t=|reached|left)" | awk '{print}' | tail -50
echo "$out" | grep -E "SCRIPT ERROR|^ERROR" | head
if echo "$out" | grep -q "TRIAL reached passage 63" && echo "$out" | grep -q "TRIAL left (victory)"; then echo "WALK OK"; exit 0; fi
echo "WALK FAILED"; exit 1
