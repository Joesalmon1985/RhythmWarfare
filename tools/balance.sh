#!/usr/bin/env bash
# Run the autoplay harness for several policies and print a compact table.
#   tools/balance.sh [pack] [enemy_fraction] [policies...]          duel packs (schema 1)
#   RW_SEEDS="1 2 3" RW_CHART=level_02.campaign RW_WAVES=1 tools/balance.sh res://songs/second_pulse 1.0 perfect accuracy:0.85 none
# Schema 2 (defense) packs print one line per policy and seed (objective health, groups per defense point) and, with
# RW_WAVES=1, each wave's spawn / arrival / clear times.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
PACK="${1:-res://songs/level_01}"
ENEMY="${2:-1.0}"
shift 2 2>/dev/null
POLICIES=("$@")
SEEDS="${RW_SEEDS:-1}"
CHART="${RW_CHART:-}"
if [ ${#POLICIES[@]} -eq 0 ]; then POLICIES=(perfect "accuracy:0.85" "accuracy:0.6" none perfect_no_bass); fi
for pol in "${POLICIES[@]}"; do
  for seed in $SEEDS; do
    "$GODOT" --headless --path "$ROOT" -s tools/autoplay.gd -- "$PACK" "$pol" "$ENEMY" "$seed" "$CHART" 2>&1 | grep -vE "^\s*$|^Godot Engine" | python -I "$ROOT/tools/balance_report.py" "$pol" ${RW_WAVES:+--waves}
  done
done
