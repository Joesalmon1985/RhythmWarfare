#!/usr/bin/env bash
# Plays the game from this checkout with the imported track packs, in a window, with sound.
#
#     bash tools/dev/play_tracks.sh              the game, from the main menu
#     bash tools/dev/play_tracks.sh --run        straight into the run (src/run/run_play.tscn)
#     RW_RUN_TRACKS=0 bash tools/dev/play_tracks.sh    the same build with track scenes off (the old loops)
#
# Packs come from RW_TRACKS_DIR, else <RW_AUDIO_WORK or ~/rw-audio-work>/packs.
#
# The save and the settings are a COPY, made the first time this runs, in <work>/play_userdata: the owner's real
# save is not touched by a build under development, and the tests (which share the real user:// folder between
# worktrees and are queued by tools/dev/godot.sh) do not collide with a play session. So this does not take the
# queue's lock and can run while tests run. Delete <work>/play_userdata to start again from the real save.
set -u
here="$(cd "$(dirname "$0")/../.." && pwd)"
work="${RW_AUDIO_WORK:-$USERPROFILE/rw-audio-work}"
packs="${RW_TRACKS_DIR:-$work/packs}"
[ -d "$packs" ] || { echo "no packs folder $packs (set RW_TRACKS_DIR)" >&2; exit 2; }
bin="${GODOT_BIN:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
[ -x "$bin" ] || { echo "no Godot at $bin (set GODOT_BIN)" >&2; exit 2; }
data="$work/play_userdata"
real="${APPDATA:-}/Godot/app_userdata/Rhythm Warfare"
if [ ! -d "$data" ]; then
    mkdir -p "$data/Godot/app_userdata"
    if [ -d "$real" ]; then
        cp -r "$real" "$data/Godot/app_userdata/" && echo "copied the save and settings from $real"
    fi
fi
scene=()
[ "${1:-}" = "--run" ] && scene=(res://src/run/run_play.tscn)
echo "packs: $packs ($(ls "$packs" | wc -l) folders)   save: $data"
APPDATA="$data" RW_TRACKS_DIR="$packs" exec "$bin" --path "$here" "${scene[@]}"
