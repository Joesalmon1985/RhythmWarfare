#!/usr/bin/env bash
# The street race in the real run scene at 16:9 and 20:9 (tools/engine/shoot_race.gd), then the contact sheet docs/shots/bedsit/race/contact.jpg.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-${TMPDIR:-/tmp}/race_shots}"
PREFIX="${RACE_PREFIX:-space}"  # space | magic | dino | transport (the theme: RACE_PREFIX=magic bash tools/dev/shoot_race.sh <out> <sheet.jpg>)
mkdir -p "$OUT"
for size in 1280x720 1600x720; do
  bash "$ROOT/tools/dev/godot.sh" --path "$ROOT" --resolution "$size" --quit-after 2000000 -s tools/engine/shoot_race.gd -- "$OUT" "$PREFIX" 2>&1 | grep -E "SCRIPT ERROR|^shot|^RACE" || true
done
python3 "$ROOT/tools/dev/race_sheet.py" "$OUT" "${2:-$ROOT/docs/shots/bedsit/race/contact.jpg}"
