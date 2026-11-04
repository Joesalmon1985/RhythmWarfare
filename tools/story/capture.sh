#!/usr/bin/env bash
# Real Godot screenshots of the running Story Campaign scene (needs a display; opens a window briefly per shot).
#   bash tools/story/capture.sh [out_dir]
# Each shot runs the actual story_play scene on a virtual song clock (no audio) with a scripted input policy up to a bar, so the
# crowd, branches and lighting are exactly what a real run of that skill level looks like at that moment.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/story}"
mkdir -p "$OUT"
RATE=2.0

ONLY="${RW_SHOTS:-}"  # optional regex: only the shots whose name matches (RW_SHOTS='^0' Night One, RW_SHOTS=cam_ the camera)
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }

shot() {  # name policy until_bar [extra env assignments...]
  local name="$1" policy="$2" bar="$3"; shift 3
  want "$name" || return 0
  local secs frames
  secs=$(python3 -c "print(($bar-1)*4*60/174)")
  frames=$(python3 -c "print(int(max(($secs-1.0),0)/$RATE)+40)")
  local res=()  # RW_WINDOW=WxH opens the window at that size (other aspect ratios)
  for kv in "$@"; do case "$kv" in RW_WINDOW=*) res=(--resolution "${kv#RW_WINDOW=}");; esac; done
  env RW_STORY_VIRTUAL=1 RW_STORY_RATE=$RATE RW_STORY_UNTIL_BAR="$bar" RW_AUTOPLAY="$policy" "$@" \
    "$GODOT" --path "$ROOT" "${res[@]}" -s tools/shoot.gd -- res://src/scenes/story_play.tscn "$OUT" "$frames:shot:$name" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
}

shot 01_opening            perfect         3
shot 02_act2_dancing       accuracy:0.8    45
shot 03_peak_energy        perfect         107
shot 04_low_energy         none            50
shot 05_end_legendary      perfect         131
shot 06_end_good_night     sloppy          131 RW_SEED=2
shot 07_end_lost_the_floor none            131
shot 08_layout_compact     perfect         107 RW_PAD_SIZE=0
shot 09_layout_large       perfect         107 RW_PAD_SIZE=2
shot 10_reduced_effects    perfect         107 RW_REDUCED=1
shot 11_high_contrast      perfect         107 RW_HIGH_CONTRAST=1
shot 12_bass_reveal        perfect         17.3
shot 13_hero_circle        perfect         47.5
shot 14_hero_riser         perfect         68.5
shot 15_floor_ripple       accuracy:0.8    89.6
shot 16_narrow_4x3         perfect         107 RW_WINDOW=1024x768
shot 17_wide_20x9          perfect         107 RW_WINDOW=1600x720
shot 18_hold_notes         perfect         21.3
shot 19_gather_at_door     perfect         28
shot 20_door_crowd_enters  perfect         33.8
shot 21_countdown          perfect         0.7
shot 22_title_card         perfect         1.3
shot 23_compact_narrow     perfect         107 RW_PAD_SIZE=0 RW_WINDOW=1024x768
shot 24_large_wide         perfect         107 RW_PAD_SIZE=2 RW_WINDOW=1600x720
shot 25_drop_stumble       none            73.6
shot 26_drop_jump          perfect         73.6
shot 27_circle_awkward     none            57.8

# chapters 2 and 3 (their own art, music packs and endings) and the cutscenes between chapters
shot ch2_01_opening         perfect       3  RW_STORY_CHAPTER=mothership
shot ch2_02_groove          accuracy:0.8  27 RW_STORY_CHAPTER=mothership
shot ch2_03_peak            perfect       69 RW_STORY_CHAPTER=mothership
shot ch2_04_low_energy      none          40 RW_STORY_CHAPTER=mothership
shot ch2_05_end_headliner   perfect       83 RW_STORY_CHAPTER=mothership
shot ch2_06_end_beamed_home none          83 RW_STORY_CHAPTER=mothership
shot ch3_01_opening         perfect       3  RW_STORY_CHAPTER=underworld
shot ch3_02_groove          accuracy:0.8  21 RW_STORY_CHAPTER=underworld
shot ch3_03_peak            perfect       55 RW_STORY_CHAPTER=underworld
shot ch3_04_low_energy      none          30 RW_STORY_CHAPTER=underworld
shot ch3_05_end_resident_dj perfect       67 RW_STORY_CHAPTER=underworld
shot ch3_06_end_devoured    none          67 RW_STORY_CHAPTER=underworld

interlude() {  # name cutscene_seconds
  local name="$1" at="$2"
  want "interlude_${name}_$(printf %02d "$at")" || return 0
  env RW_STORY_INTERLUDE="$name" RW_STORY_INTERLUDE_T="$at" RW_STORY_INTERLUDE_HOLD=1 \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/scenes/story_interlude.tscn "$OUT" "6:shot:interlude_${name}_$(printf %02d "$at")" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
}
for t in 5 9 12 15; do interlude abduction $t; interlude descent $t; done

# the moving camera mid-move (dolly, step, turn)
shot cam_mothership_step_17    perfect 17.9 RW_STORY_CHAPTER=mothership
shot cam_mothership_gallery    perfect 22   RW_STORY_CHAPTER=mothership
shot cam_mothership_turn_33    perfect 33.9 RW_STORY_CHAPTER=mothership
shot cam_mothership_reactor    perfect 45   RW_STORY_CHAPTER=mothership
shot cam_mothership_walk_49    perfect 49.9 RW_STORY_CHAPTER=mothership
shot cam_mothership_bridge     perfect 61   RW_STORY_CHAPTER=mothership
shot cam_underworld_step_17    perfect 17.9 RW_STORY_CHAPTER=underworld
shot cam_underworld_court      perfect 27   RW_STORY_CHAPTER=underworld
shot cam_underworld_walk_33    perfect 33.9 RW_STORY_CHAPTER=underworld
shot cam_underworld_pit        perfect 43   RW_STORY_CHAPTER=underworld
shot cam_underworld_turn_49    perfect 49.9 RW_STORY_CHAPTER=underworld
shot cam_underworld_furnace    perfect 54   RW_STORY_CHAPTER=underworld
# a move frame by frame: step through the hatch (bar 17), the turn (33), the walk (49); u = progress through the 2-bar move
for b in 17.3 17.6 18.2 18.6; do shot "camseq_step_$b" perfect "$b" RW_STORY_CHAPTER=mothership; done
for b in 33.5 34.5; do shot "camseq_turn_$b" perfect "$b" RW_STORY_CHAPTER=mothership; done
for b in 49.5 50.5; do shot "camseq_walk_$b" perfect "$b" RW_STORY_CHAPTER=mothership; done

# the story menu and the result screens (the result plays a scripted set headless first, then shows its summary)
screen() {  # name scene frames [env assignments...]
  local name="$1" scene="$2" frames="$3"; shift 3
  want "$name" || return 0
  env "$@" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- "$scene" "$OUT" "$frames:shot:$name" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
}
screen ui_story_menu       res://src/scenes/story_campaign.tscn 30 RW_STORY_UI=1
screen ui_result_legendary res://src/scenes/story_result.tscn  30 RW_STORY_RESULT=perfect
screen ui_result_lost      res://src/scenes/story_result.tscn  30 RW_STORY_RESULT=none

# chapters 4 and 5 (the waking chapters) and their camera moves
shot ch4_01_opening         perfect       3  RW_STORY_CHAPTER=hospital
shot ch4_02_corridor        perfect       21 RW_STORY_CHAPTER=hospital
shot ch4_03_cafeteria       perfect       29 RW_STORY_CHAPTER=hospital
shot ch4_04_garden          perfect       43 RW_STORY_CHAPTER=hospital
shot ch4_05_end_home        perfect       59 RW_STORY_CHAPTER=hospital
shot ch4_06_end_quiet       none          59 RW_STORY_CHAPTER=hospital
shot ch5_01_opening         perfect       3  RW_STORY_CHAPTER=mental_hospital
shot ch5_02_corridor        perfect       21 RW_STORY_CHAPTER=mental_hospital
shot ch5_03_art_room        perfect       31 RW_STORY_CHAPTER=mental_hospital
shot ch5_04_courtyard       perfect       47 RW_STORY_CHAPTER=mental_hospital
shot ch5_05_end_star        perfect       67 RW_STORY_CHAPTER=mental_hospital
shot ch5_06_end_lights_out  none          67 RW_STORY_CHAPTER=mental_hospital
shot cam_hospital_step_17   perfect       17.9 RW_STORY_CHAPTER=hospital
shot cam_ward_walk_41       perfect       41.9 RW_STORY_CHAPTER=mental_hospital
for t in 3 7 11 13; do interlude awakening $t; interlude sectioned $t; done
