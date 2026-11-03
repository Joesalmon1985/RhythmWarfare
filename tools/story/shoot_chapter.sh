#!/usr/bin/env bash
# Review screenshots of a chapter's art: tools/story/shoot_chapter.sh <chapter> <mode> [out_dir]
# chapter = underworld | mothership | night_one; mode = chars | chars_b | heads | joints | sil | stage | stage_low | deck | pieces | interlude
# Needs a display (not headless). GODOT overrides the binary. Set NOIMPORT=1 to skip the --import pass.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
CH="${1:-underworld}"
MODE="${2:-chars}"
OUT="${3:-/tmp/story_art}"
[ "${NOIMPORT:-0}" = "1" ] || "$GODOT" --headless --path "$ROOT" --import >/dev/null 2>&1 || true
RW_CHAPTER="$CH" RW_PREVIEW="$MODE" DISPLAY="${DISPLAY:-:0}" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://tools/story/preview_chapter.tscn "$OUT" "30:shot:${CH}_$MODE" 2>&1 | grep -E "shot |ERROR|SCRIPT|Parse" || true
