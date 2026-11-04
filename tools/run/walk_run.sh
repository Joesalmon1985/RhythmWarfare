#!/usr/bin/env bash
# Run walk-through: plays the REAL run scene (src/run/run_play.tscn, every world's stage, the rails, the passage frame, the saves) on the virtual song clock with scripted
# play and scripted route choices, from a throwaway user data directory (XDG_DATA_HOME), never the owner's save. Between them the paths visit all seven nodes. Fails on any
# ERROR or SCRIPT line, a wrong level sequence, a rail place that is not on the node's rails, missing glances, a wrong run save, or a chapter save written by the run.
# Needs a display (the worlds are rendered).
#   bash tools/run/walk_run.sh [path ...]     paths: perfect_a perfect_b sloppy none start_late   (default: all)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
RATE="${RW_STORY_RATE:-3}"
PATHS=("$@"); [ ${#PATHS[@]} -eq 0 ] && PATHS=(perfect_a perfect_b sloppy none start_late)
FAIL=0

# path -> "bot|routes|until_phase|start node|expected level sequence (comma separated, or - for any)"
spec() {
  case "$1" in
    perfect_a) echo "perfect|up,left,right,left|4||warehouse,mothership,hospital,ward_late,hospital_late";;
    perfect_b) echo "perfect|right,right,left|3||warehouse,underworld,ward,hospital_late";;
    sloppy) echo "accuracy:0.55|up,right,left|4||-";;
    none) echo "none|up|6||warehouse,mothership";;
    start_late) echo "perfect|right|1|ward_late|ward_late,ward_late";;
  esac
}

for p in "${PATHS[@]}"; do
  IFS='|' read -r BOT ROUTES UNTIL START EXPECT <<< "$(spec "$p")"
  DIR="$(mktemp -d)"
  echo "== path $p ($BOT, routes $ROUTES)"
  env XDG_DATA_HOME="$DIR/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_STORY_QUIT=1 RW_RUN_BOT="$BOT" RW_RUN_ROUTES="$ROUTES" RW_RUN_UNTIL_PHASE="$UNTIL" RW_SEED=2 \
      ${START:+RW_RUN_START=$START} timeout 900 "$GODOT" --path "$ROOT" res://src/run/run_play.tscn > "$DIR/out.txt" 2>&1
  rc=$?
  BAD="$(grep -E "ERROR|SCRIPT" "$DIR/out.txt" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" | head -5)"
  if [ -n "$BAD" ]; then echo "FAIL: errors in the run:"; echo "$BAD"; FAIL=1; fi
  if [ "$rc" -ne 0 ]; then echo "FAIL: godot exited $rc"; FAIL=1; fi
  grep -E "^RUN " "$DIR/out.txt" | cut -c1-400
  python3 - "$DIR/out.txt" "$ROOT" "$EXPECT" "$DIR/data" "$p" <<'PY' || FAIL=1
import json, sys, glob, os, re
out, root, expect, data, name = sys.argv[1:6]
text = open(out).read()
run = json.load(open(root + "/content/run/run.json"))
nodes = {n["id"]: n for n in run["nodes"]}
ok = True
def bad(msg):
    global ok
    ok = False
    print("FAIL:", msg)
m = re.search(r"^RUN summary (\{.*\})$", text, re.M)
over = re.search(r"^RUN over at phase (\d+) \((\w+)\)", text, re.M)
if not m and not over:
    bad("the run neither reached its phase nor ended")
    sys.exit(1)
s = json.loads(m.group(1)) if m else None
if s:
    if expect != "-" and ",".join(s["nodes"]) != expect:
        bad("levels %s, expected %s" % (",".join(s["nodes"]), expect))
    for r in s["rail"]:
        _, node, place = r.split(":")[0], r.split(":")[1], r.split(":")[2]
        n = nodes[node]
        allowed = {n["waypoint"]} | {p["to"] for p in n["rail"]["good"]} | {p["to"] for p in n["rail"]["bad"]}
        if place not in allowed:
            bad("rail place %s is not on the rails of %s" % (place, node))
    blocks = len(s["rail"])
    if s["glances"] < blocks:
        bad("%d glances for %d blocks (every block needs one)" % (s["glances"], blocks))
    if blocks and s["moves"] < 1:
        bad("no journey moves")
    print("levels:", " > ".join(s["nodes"]), "| rail stops:", len(s["rail"]), "| moves %d glances %d strolls %d | worlds %s" % (s["moves"], s["glances"], s["strolls"], ",".join(sorted(s["worlds"]))))
    print("rail:", " ".join(x.split(":", 1)[1] for x in s["rail"][:16]), "..." if len(s["rail"]) > 16 else "")
if over:
    print("the run ended at phase %s on %s" % over.groups())
saves = glob.glob(data + "/**/story_run.json", recursive=True)
if not saves:
    bad("no run save written")
else:
    sv = json.load(open(saves[0]))
    want = set(s["nodes"]) if s else set()
    if s and set(sv["reached"]) != want:
        bad("the save reached %s, expected %s" % (sorted(sv["reached"]), sorted(want)))
    if int(sv["runs"]) != 1:
        bad("the save counts %s runs, expected 1" % sv["runs"])
    print("save: reached", ",".join(sorted(sv["reached"])), "| runs", sv["runs"], "| best phases", sv["best_phases"])
if glob.glob(data + "/**/story_campaign.json", recursive=True):
    bad("the run wrote a chapter save (story_campaign.json)")
sys.exit(0 if ok else 1)
PY
  rm -rf "$DIR"
done
[ "$FAIL" -eq 0 ] && echo "run walk-through: OK" || echo "run walk-through: FAILED"
exit $FAIL
