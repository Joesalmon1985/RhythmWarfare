#!/usr/bin/env bash
# The art audit's captures (Windows-friendly; needs a display). One Godot launch per scene, six frames each (tools/art/audit_plan.py), JPEGs into a raw folder:
#   bash tools/art/audit_capture.sh <raw_dir> [main|gospel|squadron|ember|all]      RW_SHOTS=<regex on scene id> limits it; RW_WINDOW=WxH (default 1280x720)
# Godot: $GODOT (use tools/dev/godot.sh, the one-at-a-time queue). Python: $PY (default python). user:// goes to a temp folder (APPDATA, XDG_DATA_HOME),
# so the shared save is never touched. The raw frames are not committed; tools/art/audit_sheets.py turns them into the contact sheets.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?raw dir}"; WHICH="${2:-all}"
PY="${PY:-python}"
GODOT="${GODOT:?set GODOT to tools/dev/godot.sh}"
RATE="${RW_RATE:-0.25}"
WIN="${RW_WINDOW:-1280x720}"
ONLY="${RW_SHOTS:-}"
TMP="$(mktemp -d)"; TMPW="$(cygpath -m "$TMP" 2>/dev/null || echo "$TMP")"
mkdir -p "$OUT"
"$PY" "$ROOT/tools/art/audit_plan.py" "$WHICH" --rate "$RATE" > "$TMP/plan.txt"
while read -r path scene steps; do
  [ -z "$ONLY" ] || [[ "$scene" =~ $ONLY ]] || continue
  pe=(); [ "$path" = "-" ] || pe=("RW_RUN_PATH=$path")
  echo "launch $path $scene"
  # shellcheck disable=SC2086
  env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_RUN_START="$scene" RW_RUN_BOT=perfect RW_RUN_ROUTES="" "${pe[@]}" \
    "$GODOT" --path "$ROOT" --resolution "$WIN" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" $steps 2>&1 </dev/null \
    | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
  for f in "$TMP"/png/*.png; do
    [ -f "$f" ] || continue
    ffmpeg -nostdin -y -loglevel error -i "$f" -q:v 3 "$OUT/$(basename "$f" .png).jpg" && rm -f "$f"
  done
done < "$TMP/plan.txt"
rm -rf "$TMP"
