#!/usr/bin/env bash
# The blackjack acceptance pictures, as JPEGs in docs/shots/blackjack (or the folder you give). Needs a display; opens a window briefly per run.
#   bash tools/minigames/capture_blackjack.sh [out_dir]       RW_SHOTS=<regex> only the shots whose name matches (e.g. RW_SHOTS=08_ or RW_SHOTS=demo_)
# Real run scene (the ward, the table hotspot ward.cards, the live day room): shots 01 to 16. Each run uses the virtual song clock (no audio): the bot passes every block, selects the table at beat 52 of
# the first phase (so the player sits on the downbeat of phase 2, song time 64 beats), then RW_MINIGAME_TAPS plays the hand (target@beats after sitting) with RW_MINIGAME_SEED fixing the cards.
# Seeds (found by scanning BlackjackGame): 3 win when sticking at once (settles at beat 21.6, the hole card turns at 17.55), 5 loss (settles at 23.6), 16 win after one twist, 6 four losses in a row (broke at beat 89.6).
# The wobble and the fall need missed blocks: RW_RUN_BOT=blocks:<pattern> (1 pass, 0 miss; four blocks per phase). The player sits at the start of phase 2 (blocks 4..7).
# Also shoots the demo scene (tools/minigames/blackjack_demo.tscn) at low resolution and with high contrast / reduced motion: demo_*.
set -eu
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
OUT="${1:-$ROOT/docs/shots/blackjack}"
TMP="$(mktemp -d)"
mkdir -p "$OUT"
RATE=0.25
BEAT=$(python3 -c "print(60/174)")
SEAT=$(python3 -c "print(64*60/174)")  # song seconds of the downbeat the player sits on
ONLY="${RW_SHOTS:-}"
want() { [ -z "$ONLY" ] || [[ "$1" =~ $ONLY ]]; }
wantany() { local n; for n in "$@"; do want "${n%%:*}" && return 0; done; return 1; }

jpeg() {  # name
  if [ -f "$TMP/$1.png" ]; then
    ffmpeg -nostdin -y -loglevel error -i "$TMP/$1.png" -q:v 3 "$OUT/$1.jpg" && rm -f "$TMP/$1.png"
    echo "shot $OUT/$1.jpg"
  fi
}

# real <seed> <taps> <bot> <window or ""> name:beat ...   beat is counted from the phase start when it begins with p (p51 = beat 51 of phase 1), otherwise from sitting down
real() {
  local seed="$1" taps="$2" bot="$3" win="$4"; shift 4
  wantany "$@" || return 0
  local steps=() nb n b secs frame
  for nb in "$@"; do
    n="${nb%%:*}"; b="${nb##*:}"
    want "$n" || continue
    if [[ "$b" == p* ]]; then secs=$(python3 -c "print(${b#p}*60/174)"); else secs=$(python3 -c "print($SEAT+$b*60/174)"); fi
    frame=$(python3 -c "print(int(($secs+2.0)/$RATE)+2)")
    steps+=("$frame:shot:$n")
  done
  local res=()
  [ -n "$win" ] && res=(--resolution "$win")
  env XDG_DATA_HOME="$TMP/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE=$RATE RW_RUN_START=ward RW_RUN_BOT="$bot" RW_RUN_SELECT="${SEL:-ward.cards@52}" RW_MINIGAME_SEED="$seed" RW_MINIGAME_TAPS="$taps" \
    "$GODOT" --path "$ROOT" "${res[@]}" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMP" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
  for nb in "$@"; do jpeg "${nb%%:*}"; done
}

# demo <env assignments> name:beat ...   the demo scene (beats after sitting; 0.05 song seconds per frame)
demo() {
  local envs="$1"; shift
  wantany "$@" || return 0
  local steps=() nb n b frame
  for nb in "$@"; do
    n="${nb%%:*}"; b="${nb##*:}"
    want "$n" || continue
    frame=$(python3 -c "print(int(round($b*60/174/0.05))+2)")
    steps+=("$frame:shot:$n")
  done
  env $envs RW_DEMO_STEP=0.05 "$GODOT" --path "$ROOT" --resolution 1280x460 -s tools/shoot.gd -- res://tools/minigames/blackjack_demo.tscn "$TMP" "${steps[@]}" 2>&1 </dev/null | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" || true
  for nb in "$@"; do jpeg "${nb%%:*}"; done
}

WIN="bet@5,hand@13"
real 3 "$WIN,exit@40" perfect "" 01_table_in_room:p58 02_sitting_down:0.5 03_money_from_pockets:1.6 04_twenty_on_the_table:4.3 05_placing_the_bet:5.8 06_dealing:8.2 07_dealer_signals_turn:12.2 09_sticking:13.8 10_dealer_reveals:17.7 11_winning_and_paid:23.6
real 16 "bet@5,deck@12,hand@16" perfect "" 08_twisting:12.55
real 5 "$WIN" perfect "" 12_losing_and_collected:25.6
# every hand is a bet and an immediate stick; a tap that is not live is simply refused, so one of each every beat plays all four hands whatever the length of the NPC turns (seed 6 is broke at beat 89.6)
SPAM=$(python3 -c "print(','.join(['bet@%d' % n for n in range(5, 100)] + ['hand@%d' % n for n in range(11, 100)]))")
real 6 "$SPAM" perfect "" 13_out_of_money:92.5
real 3 "bet@5,hand@13,exit@27" perfect "" 14_leaving_with_money:28.6
# the chair: 2 missed blocks in a row wobble, 3 fall. 1111 = phase 1 passed (sit), 11 = blocks 4 and 5 passed, then misses
real 3 "bet@5" "blocks:11111100" "" 15_chair_wobbling:66
real 3 "bet@5" "blocks:111111000" "" 16_falling_off_the_chair:78

# joining: the touch (a burst and the camera setting off), the wait (the camera at the table, the countdown ring closing), the refusal. A finer clock (0.05 s a frame), the touch at beat 18 of phase 1.
RATE=0.05
SEL="ward.cards@18"
real 3 "bet@5" perfect "" 17_touch_registered:p18.5
real 3 "bet@5" perfect "" 18_waiting_to_sit:p26.5
real 3 "bet@5" none "" 19_waved_off:p29.1
RATE=0.25
SEL=""

# demo-scene extras (small canvas, high contrast, reduced motion)
demo "RW_GALLERY_LOW=1 RW_MINIGAME_SEED=3 RW_DEMO_TAPS=bet@5,hand@13" demo_low_await_bet:4.8 demo_low_player_turn:12.2
demo "RW_DEMO_HC=1 RW_MINIGAME_SEED=3 RW_DEMO_TAPS=bet@5,hand@13" demo_contrast_player_turn:12.2
demo "RW_DEMO_REDUCED=1 RW_MINIGAME_SEED=3 RW_DEMO_FALL=8" demo_reduced_fall:10.2
rm -rf "$TMP"
