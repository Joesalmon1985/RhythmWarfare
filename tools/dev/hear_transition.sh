#!/usr/bin/env bash
# Hear one scene change between two recorded tracks, with sound, without playing through the game (stage M2.6, docs/music/TRANSITIONS_BUILT.md).
# The last lap (16 bars) of track A's scene plays, then the run goes into track B's scene through the real TransitionDirector and RunAudio, as in the game, and B plays on for 20 bars
# (past its first drop). It prints which mode was chosen (blend, halftime_blend, echo_out or cut) and why. A perfect player taps the cues; nothing needs touching.
#
#     bash tools/dev/hear_transition.sh <track A> <track B>          the transition as the game plans it
#     bash tools/dev/hear_transition.sh <track A> <track B> --cut    the same scene change as a plain cut, to compare
#     bash tools/dev/hear_transition.sh --list                       the recommended pairs
#     bash tools/dev/hear_transition.sh --pair 1                     one of them by its number (add --cut to compare)
#
# Packs come from RW_TRACKS_DIR, else <RW_AUDIO_WORK or ~/rw-audio-work>/packs. RW_PAIR_MUTE=1 plays it muted (a check that it runs). Like play_tracks.sh it takes no lock: it can run while
# tests run, but a quiet machine plays it best. The save is not touched (nothing is saved).
set -u
here="$(cd "$(dirname "$0")/../.." && pwd)"
work="${RW_AUDIO_WORK:-$USERPROFILE/rw-audio-work}"
packs="${RW_TRACKS_DIR:-$work/packs}"
PAIRS=(
  "chase_status_no_problem_original_mix stimpy_party_last_sounds blend, -29.9 cents (balcony to chill)"
  "ternion_sound_artifice acuna_go_back echo_out (140 to 174 BPM)"
  "chase_status_no_problem_original_mix mampi_swift_soldiers_gyrhlx7pafa cut (Soldiers has its first drop at bar 0: no lead-in to blend over)"
  "unglued_telefonik amplify_crossy_badman blend at +49.6 cents (the widest blend)"
)
if [ "${1:-}" = "--list" ] || [ $# -eq 0 ]; then
  echo "Recommended pairs (bash tools/dev/hear_transition.sh --pair N, add --cut to hear the same change as a cut):"
  for i in "${!PAIRS[@]}"; do set -- ${PAIRS[$i]}; a="$1"; b="$2"; shift 2; echo "  $((i + 1)). $a -> $b: $*"; done
  exit 0
fi
cut=""
if [ "$1" = "--pair" ]; then
  n="${2:-0}"; [ "$n" -ge 1 ] && [ "$n" -le ${#PAIRS[@]} ] || { echo "no pair $n (see --list)" >&2; exit 2; }
  [ "${3:-}" = "--cut" ] && cut=1
  set -- ${PAIRS[$((n - 1))]}
  A="$1"; B="$2"
else
  A="$1"; B="${2:-}"
  [ "${3:-}" = "--cut" ] && cut=1
fi
[ -n "$B" ] || { echo "usage: hear_transition.sh <track A> <track B> [--cut] | --list | --pair N [--cut]" >&2; exit 2; }
[ -d "$packs" ] || { echo "no packs folder $packs (set RW_TRACKS_DIR)" >&2; exit 2; }
for t in "$A" "$B"; do [ -f "$packs/$t/track.json" ] || { echo "no pack for $t in $packs" >&2; exit 2; }; done
bin="${GODOT_BIN:-$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe}"
[ -x "$bin" ] || { echo "no Godot at $bin (set GODOT_BIN)" >&2; exit 2; }
data="$work/hear_userdata"
mkdir -p "$data"
echo "playing the last 16 bars of $A into $B${cut:+, as a cut}..."
APPDATA="$data" RW_TRACKS_DIR="$packs" RW_PAIR_A="$A" RW_PAIR_B="$B" RW_RUN_TRANSITIONS="${cut:+cut}" "$bin" --path "$here" -s res://tools/music/transition_pair.gd 2>&1 \
  | grep -E "^PAIR (mode|start|[^ ]+: its scene)|SCRIPT ERROR|^ERROR" | sed -e 's/^PAIR //'
