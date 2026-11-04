#!/usr/bin/env bash
# Review screenshots of the mental_hospital chapter (the crowd rig in every room): tools/story/shoot_mh.sh <view> <mode> [out_dir]
# view = main | corridor | art_room | courtyard; mode = stage | stage_low | set | pieces | chars | chars_b | close | sil | deck | passage | interlude | interlude_flood
# Needs a display (not headless). GODOT overrides the binary. NOIMPORT=1 skips the import pass. Writes <out_dir>/mh_<view>_<mode>.png
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
VIEW="${1:-main}"
MODE="${2:-stage}"
OUT="${3:-/tmp/story_mh}"
[ "${NOIMPORT:-0}" = "1" ] || "$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1 || true
if [ "$VIEW" = "main" ]; then unset RW_VIEW; else export RW_VIEW="$VIEW"; fi
RW_CHAPTER=mental_hospital RW_PREVIEW="$MODE" DISPLAY="${DISPLAY:-:0}" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://tools/story/preview_mh.tscn "$OUT" "30:shot:mh_${VIEW}_$MODE" 2>&1 | grep -E "shot |view |ERROR|SCRIPT|Parse" || true
