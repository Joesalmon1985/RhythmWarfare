#!/usr/bin/env bash
# Review screenshots of the Night One art: tools/story/shoot_preview.sh <mode> [out_dir]
# mode = chars | chars_b | heads | stage | stage_low | sil | deck. Needs a display (not headless). GODOT overrides the binary.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
MODE="${1:-chars}"
OUT="${2:-/tmp/story_art}"
"$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1 || true
RW_PREVIEW="$MODE" DISPLAY="${DISPLAY:-:0}" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://tools/story/preview_art.tscn "$OUT" "30:shot:$MODE" 2>&1 | grep -E "shot |ERROR|SCRIPT|Parse" || true
