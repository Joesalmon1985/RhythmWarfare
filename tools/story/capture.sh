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

# Night One's journey, one shot per node (WP6): the dancer on the floor, the walk to the steps, the climb, the booth, the queasy floor edge, the corridor, the cubicle run and
# sick beat, the recovered walk back, the endings' tableaux, reduced effects (steady picture), high contrast and the odd window shapes
shot j01_dancer_view        perfect         10
shot j02_walk_to_steps      perfect         35
shot j03_on_stage           perfect         41
shot j04_booth_dj           perfect         62
shot j05_queasy_floor_edge  none            36
shot j06_corridor_stagger   none            60
shot j07_cubicle_run        none            75
shot j08_sick_beat          none            79
shot j09_recovered_walk     none            85
shot j10_end_legendary_booth perfect        131
shot j11_end_good_steps     sloppy          131 RW_SEED=2
shot j12_end_lost_door      none            131
shot j13_reduced_motion     perfect         35  RW_REDUCED=1
shot j14_high_contrast      perfect         10  RW_HIGH_CONTRAST=1
shot j15_4x3_stage          perfect         41  RW_WINDOW=1024x768
shot j16_20x9_booth         perfect         62  RW_WINDOW=1600x720
shot j17_lowres_180         perfect         62  RW_STORY_LINES=180
shot j18_motion_none        perfect         35  RW_STORY_MOTION=2

interlude() {  # name cutscene_seconds
  local name="$1" at="$2"
  want "interlude_${name}_$(printf %02d "$at")" || return 0
  env RW_STORY_INTERLUDE="$name" RW_STORY_INTERLUDE_T="$at" RW_STORY_INTERLUDE_HOLD=1 \
    "$GODOT" --path "$ROOT" -s tools/shoot.gd -- res://src/scenes/story_interlude.tscn "$OUT" "6:shot:interlude_${name}_$(printf %02d "$at")" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
}
for t in 5 9 12 15; do interlude abduction $t; interlude descent $t; done

# the story menu and the result screens (the result plays a scripted set headless first, then shows its summary)
screen() {  # name scene frames [env assignments...]
  local name="$1" scene="$2" frames="$3"; shift 3
  want "$name" || return 0
  env "$@" "$GODOT" --path "$ROOT" -s tools/shoot.gd -- "$scene" "$OUT" "$frames:shot:$name" 2>&1 | grep -E "^shot|ERROR|SCRIPT" || true
}
screen ui_story_menu       res://src/scenes/story_campaign.tscn 30 RW_STORY_UI=1
screen ui_result_legendary res://src/scenes/story_result.tscn  30 RW_STORY_RESULT=perfect
screen ui_result_lost      res://src/scenes/story_result.tscn  30 RW_STORY_RESULT=none


# Chapters 2 to 5 in the 2.5D world: one shot per journey node (the room the player is in at that bar, by skill) and each ending's tableau.
# Names: <chapter prefix>_NN_<node>; bars are where the journey is (see tools/story/tune.gd for the places, docs/STORY_CAMPAIGN_HANDOVER.md for the bars).
chap() { local prefix="$1" id="$2"; shift 2; shot "$prefix$1" "$2" "$3" RW_STORY_CHAPTER="$id" "${@:4}"; }  # chap prefix id name policy bar [env...]

M=mothership
chap m_ $M 01_deck_dancer          perfect 10
chap m_ $M 02_walk_to_gallery      perfect 18.5
chap m_ $M 03_gallery              perfect 27
chap m_ $M 04_catwalk_reactor      perfect 40
chap m_ $M 05_bridge               perfect 52
chap m_ $M 06_helm_dj              perfect 68
chap m_ $M 07_medbay_probe         none    53
chap m_ $M 08_exam_sick            none    62
chap m_ $M 09_recovered            none    70
chap m_ $M 10_end_headliner        perfect 83
chap m_ $M 11_end_honoured         sloppy  83 RW_SEED=2
chap m_ $M 12_end_beamed_home      none    83

U=underworld
chap u_ $U 01_arena_dancer         perfect 10
chap u_ $U 02_walk_to_court        perfect 18.5
chap u_ $U 03_court                perfect 30
chap u_ $U 04_throne               perfect 44
chap u_ $U 05_pit_stage            perfect 54
chap u_ $U 06_furnace_chains       none    44
chap u_ $U 07_cage_sick            none    53
chap u_ $U 08_end_resident_dj      perfect 67
chap u_ $U 09_end_survived         sloppy  67 RW_SEED=2
chap u_ $U 10_end_devoured         none    67

H=hospital
chap h_ $H 01_bed_wakes            perfect 10
chap h_ $H 02_corridor_carried     perfect 22
chap h_ $H 03_cafeteria            perfect 38
chap h_ $H 04_garden_bandstand     perfect 48
chap h_ $H 05_bad_quiet_corridor   none    40
chap h_ $H 06_bad_back_to_bed      none    47
chap h_ $H 07_end_home             perfect 59
chap h_ $H 08_end_on_the_mend      sloppy  59 RW_SEED=2
chap h_ $H 09_end_quiet            none    59

W=mental_hospital
chap w_ $W 01_day_room             perfect 10
chap w_ $W 02_corridor             perfect 22
chap w_ $W 03_art_room             perfect 36
chap w_ $W 04_courtyard_stage      perfect 52
chap w_ $W 05_treatment_room       none    40
chap w_ $W 06_quiet_room           none    52
chap w_ $W 07_end_star             perfect 67
chap w_ $W 08_end_group_activity   sloppy  67 RW_SEED=2
chap w_ $W 09_end_lights_out       none    67

for t in 3 7 11 13; do interlude awakening $t; interlude sectioned $t; done

# WP9: Night One's new places and the activity beats (figures doing things: RW_STORY_CAM=@x:z:yaw[:pitch] stands the camera at a ground point, see StoryStage._override_pose).
# The per-room contact sheets (one shot per place of every chapter) come from tools/story/rooms.sh.
ac() { local name="$1" chapter="$2" bar="$3" cam="$4"; shot "$name" perfect "$bar" RW_STORY_CHAPTER="$chapter" RW_STORY_CAM="$cam"; }  # ac name chapter bar cam
ac act01_n1_bar_queue_and_drinks      night_one       60  @8.3:4.0:-70
ac act02_n1_chill_pair_and_sleeper    night_one       60  @9:10:0
ac act03_n1_balcony_watchers          night_one       60  balcony_rail
ac act04_ms_alien_dj_headphones_wrong mothership      60  @0:-0.4:0
ac act05_ms_grey_examines_dancer      mothership      60  exam
ac act06_uw_bouncer_checks_tickets    underworld      50  @1.4:2.0:0
ac act07_hos_patient_dances_with_drip hospital        40  @-3.7:3.0:0
ac act08_ward_chef_serves_talent_show mental_hospital 50  @53:9.6:-90
ac act09_ward_painters_at_easels      mental_hospital 50  @35.1:7:0
ac act10_ward_resident_stares_at_bars mental_hospital 50  @5:3:0
ac look01_up_at_the_rig               night_one       60  floor_centre,0,25
ac look02_down_at_the_floor           night_one       60  floor_centre,0,-22
