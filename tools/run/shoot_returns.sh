#!/usr/bin/env bash
# Shots of the path return objects (work package N2.5; needs a display): each scene at beat 14 of its first lap (the camera has settled) and at beat 54 of its last lap (the choice window).
#   RW_WINDOW=1280x720 bash tools/run/shoot_returns.sh <out dir> <path>/<scene> [<path>/<scene> ...]       (RW_WINDOW=1600x720 for 20:9)
# The Godot launch goes through tools/dev/godot.sh (export GODOT=tools/dev/godot.sh or leave it unset). user:// goes to a temp folder, so the shared save is never touched.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?out dir}"; shift
GODOT="${GODOT:-$ROOT/tools/dev/godot.sh}"
RATE="${RW_RATE:-0.25}"
WIN="${RW_WINDOW:-1280x720}"
TMP="$(mktemp -d)"; TMPW="$(cygpath -m "$TMP" 2>/dev/null || echo "$TMP")"
mkdir -p "$OUT"
for spec in "$@"; do
  path="${spec%%/*}"; scene="${spec#*/}"
  steps=$(python - "$ROOT" "$path" "$scene" "$RATE" <<'PY'
import json, sys
root, path, scene, rate = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
r = json.load(open(f"{root}/content/paths/{path}/run.json", encoding="utf-8"))
b = 60.0 / float(r["timing"]["bpm"]); pb = int(r["timing"]["phase_beats"])
n = [x for x in r["nodes"] if x["id"] == scene][0]
laps = int(n.get("laps", r["path"].get("laps", 1)))
last = pb * (laps - 1) * b
sid = scene.replace(".", "_")
for tag, t in (("a14", 14 * b), ("win", last + 54 * b)):
    print("%d:shot:%s__%s__%s" % (int(round((t + 2.0) / rate)) + 2, path, sid, tag), end=" ")
PY
)
  echo "launch $path $scene"
  # shellcheck disable=SC2086
  env APPDATA="$TMPW/data" XDG_DATA_HOME="$TMPW/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_RUN_START="$scene" RW_RUN_PATH="$path" RW_RUN_BOT=perfect RW_RUN_ROUTES="" \
    bash "$GODOT" --path "$ROOT" --resolution "$WIN" -s tools/shoot.gd -- res://src/run/run_play.tscn "$TMPW/png" $steps 2>&1 </dev/null \
    | grep -E "ERROR|SCRIPT" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB\|WASAPI" | head -5 || true
  for f in "$TMP"/png/*.png; do
    [ -f "$f" ] || continue
    ffmpeg -nostdin -y -loglevel error -i "$f" -q:v 3 "$OUT/$(basename "$f" .png).jpg" && rm -f "$f"
  done
done
rm -rf "$TMP"
