#!/usr/bin/env bash
# Review screenshots of the mothership's extra views: tools/story/shoot_views.sh <view> <mode> [out_dir]
# view = main | gallery | reactor | bridge; mode = stage (crowd + pieces) | set (bare room) | stage_low | pieces | passage. Needs a display. NOIMPORT=1 skips the import pass.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
VIEW="${1:-gallery}"
MODE="${2:-stage}"
OUT="${3:-/tmp/story_views}"
[ "${NOIMPORT:-0}" = "1" ] || "$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1 || true
RW_VIEW="$VIEW" RW_PREVIEW="$MODE" DISPLAY="${DISPLAY:-:0}" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://tools/story/preview_views.tscn "$OUT" "30:shot:${VIEW}_$MODE" 2>&1 | grep -E "shot |view |ERROR|SCRIPT|Parse" || true
