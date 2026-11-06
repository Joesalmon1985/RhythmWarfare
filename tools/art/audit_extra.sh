#!/usr/bin/env bash
# The art audit's other captures (Windows-friendly; needs a display): the quest entrances and the passage into a path, the hotspot states, the passage
# between worlds, the main menu, the 20:9 phone shape, the Bassment. JPEGs into <raw_dir>. user:// goes to a temp folder, so the shared save is never touched.
#   bash tools/art/audit_extra.sh <raw_dir> [group ...]      groups: portals states passage home wide bassment (default all)
# GODOT must be tools/dev/godot.sh (one Godot at a time); PY a python with the standard library.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?raw dir}"; shift
WANT="${*:-portals states passage home wide bassment}"
PY="${PY:-python}"
GODOT="${GODOT:?set GODOT to tools/dev/godot.sh}"
TMP="$(mktemp -d)"; TMPW="$(cygpath -m "$TMP" 2>/dev/null || echo "$TMP")"
mkdir -p "$OUT"
has() { [[ " $WANT " == *" $1 "* ]]; }
fr() { "$PY" -c "print(int(round(($1+2.0)/$RATE))+2)"; }    # song seconds -> frame
bt() { "$PY" -c "print($1*60/${BPM:-174})"; }                  # beats -> seconds
flush() {
  for f in "$TMP"/png/*.png; do
    [ -f "$f" ] || continue
    ffmpeg -nostdin -y -loglevel error -i "$f" -q:v 3 "$OUT/$(basename "$f" .png).jpg" && rm -f "$f"
  done
}
run() {  # scene win "env..." -- steps...
  local scene="$1" win="$2"; shift 2
  local envs=()
  while [ "$1" != "--" ]; do envs+=("$1"); shift; done; shift
  echo "launch $scene $win ${envs[*]}"
  env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_RUN_START="$scene" RW_RUN_BOT=perfect RW_RUN_ROUTES="" "${envs[@]}" \
    "$GODOT" --path "$ROOT" --resolution "$win" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" "$@" 2>&1 </dev/null \
    | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
  flush
}
RATE=0.25

if has portals; then  # each quest entrance: the window with the entrance lit, selected, then through it into the path (the main-to-path join)
  P=$(bt 64)
  while read -r scene hid flags name; do
    run "$scene" 1280x720 "RW_RUN_FLAGS=${flags#-}" "RW_RUN_PORTAL=$hid" -- \
      "$(fr "$(bt 50)"):shot:portal_${name}__lit" "$(fr "$(bt 56)"):shot:portal_${name}__selected" \
      "$(fr "$("$PY" -c "print($P-0.25)")"):shot:portal_${name}__end" "$(fr "$("$PY" -c "print($P+0.3)")"):shot:portal_${name}__nx0" \
      "$(fr "$("$PY" -c "print($P+3.0)")"):shot:portal_${name}__nx3" "$(fr "$("$PY" -c "print($P+10.0)")"):shot:portal_${name}__nx10"
  done <<'EOF'
warehouse.balcony warehouse.balcony.star wh_saw_floor gospel
warehouse.booth warehouse.booth.radio - squadron
warehouse.bar warehouse.bar.ember wh_vip_pass ember
warehouse warehouse.wizard - wizard
EOF
fi

if has states; then  # a hotspot in each state (the recipes of tools/run/capture.sh)
  run warehouse 1280x720 -- "$(fr "$(bt 53)"):shot:state_before"
  run warehouse 1280x720 "RW_RUN_SELECT=warehouse.exit_balcony@52" -- "$(fr "$(bt 55)"):shot:state_selected" "$(fr "$(bt 60.9)"):shot:state_committed"
  run warehouse 1280x720 "RW_RUN_SELECT=warehouse.dancer@52" -- "$(fr "$(bt 66)"):shot:state_success"
  run warehouse 1280x720 "RW_RUN_BOT=blocks:1110" "RW_RUN_SELECT=warehouse.dancer@52" -- "$(fr "$(bt 66)"):shot:state_failure"
  run warehouse 1280x720 "RW_RUN_SELECT=warehouse.wizard@3" -- "$(fr "$(bt 8)"):shot:state_wizard"
  run mothership 1280x720 "RW_RUN_ROUTES=up" -- "$(fr "$(bt 61.5)"):shot:doorwalk_mothership_before" "$(fr "$(bt 66)"):shot:doorwalk_mothership_through"
fi

if has passage; then  # the passage between worlds, finely: every quarter beat around the downbeat of warehouse.exit -> mothership
  P=$(bt 64)
  steps=()
  for d in -2.0 -1.0 -0.55 -0.3 0.05 0.3 0.75 1.5 3.0 6.0; do
    t=$("$PY" -c "print($P+$d)")
    steps+=("$(fr "$t"):shot:passage_wh_ms__$(echo "$d" | tr -- '-.' 'm_')")
  done
  run warehouse.exit 1280x720 "RW_RUN_ROUTES=up" -- "${steps[@]}"
  steps=()
  for d in -0.55 0.05 0.75 3.0; do
    t=$("$PY" -c "print($P+$d)")
    steps+=("$(fr "$t"):shot:passage_uw_ward__$(echo "$d" | tr -- '-.' 'm_')")
  done
  run underworld.exit 1280x720 "RW_RUN_ROUTES=right" -- "${steps[@]}"
fi

if has home; then
  for spec in "home_screen 20:shot:home_screen" "home_chapters 10:keydown:Down 11:keyup:Down 12:keydown:Enter 13:keyup:Enter 50:shot:home_chapters"; do
    set -- $spec; name="$1"; shift
    echo "launch home $name"
    env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_STORY_VIRTUAL=1 RW_STORY_RATE=0.5 "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/scenes/main_menu.tscn "$TMPW/png" "$@" 2>&1 </dev/null \
      | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
    flush
  done
fi

if has wide; then  # the 20:9 phone shape (1600 x 720) for a sample of scenes: a few seconds in, and the window
  for spec in "- warehouse 174" "- mothership.bridge 174" "- underworld.pit 174" "- hospital.corridor 174" "- ward.courtyard 174" "gospel jordan.baptism 124" "squadron base 140" "ember hollow.inn 145"; do
    set -- $spec; path="$1"; scene="$2"; BPM="$3"
    laps=1; [ "$path" = "-" ] || laps=2
    pe=(); [ "$path" = "-" ] || pe=("RW_RUN_PATH=$path")
    n="${scene//./_}"; [ "$path" = "-" ] || n="${path}__$n"
    run "$scene" 1600x720 "${pe[@]}" -- "$(fr "$(bt 24)"):shot:wide_${n}__a24" "$(fr "$(bt $((64 * (laps - 1) + 54)))"):shot:wide_${n}__win"
  done
  BPM=174
fi

if has bassment; then  # the Bassment: every zone's first passage, the window open (as tools/trial/capture.sh), and a fight
  while read -r zone start; do
    echo "launch bassment $zone"
    env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_TRIAL_DIRECT=1 RW_TRIAL_START="$start" RW_TRIAL_BOT=perfect RW_TRIAL_TAPS="" \
      "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" "30:shot:bassment_${zone}__a" "80:shot:bassment_${zone}__win" 2>&1 </dev/null \
      | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
    flush
  done < <("$PY" "$ROOT/tools/trial/contact_sheet.py" --list | tr -d '\r')
  echo "launch bassment fight"
  env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_TRIAL_DIRECT=1 RW_TRIAL_START=12 RW_TRIAL_BOT=perfect RW_TRIAL_TAPS=0 \
    "$GODOT" --path "$ROOT" --resolution 1280x720 -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" 40:shot:bassment_fight__1 230:shot:bassment_fight__2 345:shot:bassment_fight__3 2>&1 </dev/null \
    | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
  flush
fi
rm -rf "$TMP"
