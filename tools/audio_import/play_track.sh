#!/usr/bin/env bash
# Plays an imported track pack in the game's track mode.
#   tools/audio_import/play_track.sh <pack id> [chart] [start seconds]
# chart is easy, normal or hard (default: the pack's own default); packs live in $RW_AUDIO_WORK/packs.
# Other switches pass through the environment, for example RW_AUTOPLAY=accuracy:0.7 or RW_CALIBRATION_MS=40.
set -euo pipefail
here="$(cd "$(dirname "$0")/../.." && pwd)"
if [ -n "${USERPROFILE:-}" ]; then
    default_godot="$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe"
else
    default_godot="/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64"
fi
godot="${GODOT:-$default_godot}"
pack="${RW_AUDIO_WORK:-$HOME/rw-audio-work}/packs/${1:?pack id, for example acuna_go_back}"
[ -f "$pack/track.json" ] || { echo "no pack at $pack" >&2; exit 1; }
[ -n "${2:-}" ] && export RW_TRACK_CHART="$2"
[ -n "${3:-}" ] && export RW_TRACK_START="$3"
RW_TRACK="$pack" exec "$godot" --path "$here" res://src/track/track_play.tscn
