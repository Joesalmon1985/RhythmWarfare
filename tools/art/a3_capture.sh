#!/usr/bin/env bash
# Package A3's proof frames (needs a display): one scene per world family with the pad strip and notes in flight, at song seconds
# chosen to catch holds, and the title screen. JPEGs into <raw_dir>. user:// goes to a temp folder, so the shared save is never touched.
#   bash tools/art/a3_capture.sh <raw_dir> [WxH] [group ...]      groups: families title (default both); WxH default 1280x720
#   RW_SHOTS=<regex on the family name> limits the families. GODOT must be tools/dev/godot.sh; PY a python with the standard library.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?raw dir}"; shift
WIN="${1:-1280x720}"; [ $# -gt 0 ] && shift
WANT="${*:-families title}"
PY="${PY:-python}"
GODOT="${GODOT:?set GODOT to tools/dev/godot.sh}"
ONLY="${RW_SHOTS:-}"
TMP="$(mktemp -d)"; TMPW="$(cygpath -m "$TMP" 2>/dev/null || echo "$TMP")"
mkdir -p "$OUT"
RATE=0.25
TAG="${WIN/x/_}"
has() { [[ " $WANT " == *" $1 "* ]]; }
fr() { "$PY" -c "print(int(round(($1+2.0)/$RATE))+2)"; }
flush() {
  for f in "$TMP"/png/*.png; do
    [ -f "$f" ] || continue
    ffmpeg -nostdin -y -loglevel error -i "$f" -q:v 3 "$OUT/$(basename "$f" .png).jpg" && rm -f "$f"
  done
}
quiet() { grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true; }

if has families; then
  while read -r fam path scene; do
    [ -z "$ONLY" ] || [[ "$fam" =~ $ONLY ]] || continue
    pe=(); [ "$path" = "-" ] || pe=("RW_RUN_PATH=$path")
    steps=()
    for t in 8 12 16 20 26 32; do steps+=("$(fr $t):shot:a3_${fam}__${TAG}__t$t"); done
    echo "launch $fam $scene $WIN"
    env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_RUN_START="$scene" RW_RUN_BOT=perfect RW_RUN_ROUTES="" "${pe[@]}" \
      "$GODOT" --path "$ROOT" --resolution "$WIN" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" "${steps[@]}" 2>&1 </dev/null | quiet
    flush
  done <<'EOF'
club - warehouse
ship - mothership.bridge
hell - underworld.pit
hospital - hospital.corridor
ward - ward.courtyard
gospel gospel jordan.baptism
squadron squadron base
ember_north ember north
ember_hollow ember hollow.inn
EOF
  if [ -z "$ONLY" ] || [[ "bassment" =~ $ONLY ]]; then
    echo "launch bassment $WIN"
    env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_TRIAL_DIRECT=1 RW_TRIAL_START=12 RW_TRIAL_BOT=perfect RW_TRIAL_TAPS=0 \
      "$GODOT" --path "$ROOT" --resolution "$WIN" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" "40:shot:a3_bassment__${TAG}__a" "120:shot:a3_bassment__${TAG}__b" "230:shot:a3_bassment__${TAG}__c" 2>&1 </dev/null | quiet
    flush
  fi
fi

if has title; then
  echo "launch title $WIN"
  env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" "$GODOT" --path "$ROOT" --resolution "$WIN" -s tools/shoot.gd -- res://src/scenes/main_menu.tscn "$TMPW/png" \
    "3:shot:a3_title__${TAG}__f3" "60:shot:a3_title__${TAG}__f60" "240:shot:a3_title__${TAG}__f240" 2>&1 </dev/null | quiet
  flush
fi
rm -rf "$TMP"
