#!/usr/bin/env bash
# Run walk-through: plays the REAL run scene (src/run/run_play.tscn, every world's stage, the rails, the passage frame, the saves) on the virtual song clock with scripted
# play and scripted route choices, from a throwaway user data directory (XDG_DATA_HOME), never the owner's save. A phase is a scene (a room of a world); between them the
# paths perfect_a to perfect_d visit all 36 scenes of the seven worlds (checked at the end of a full run). Fails on any ERROR or SCRIPT line, a wrong scene sequence, a step that
# is not a route of the scene before it, a rail place that is not on the scene's rails, missing glances, a wrong run save (reached = the worlds visited, never a scene), or a
# chapter save written by the run. Needs a display (the worlds are rendered).
#   RW_WALK_IGNORE=<regex> drops matching ERROR lines from the check.
#   bash tools/run/walk_run.sh [path ...]     paths: perfect_a perfect_b perfect_c perfect_d sloppy none start_late   (default: all)
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
RATE="${RW_STORY_RATE:-3}"
PATHS=("$@"); [ ${#PATHS[@]} -eq 0 ] && PATHS=(perfect_a perfect_b perfect_c perfect_d sloppy none start_late)
SEEN="$(mktemp)"
FAIL=0

# path -> "bot|routes (one direction per phase, empty = the default)|until_phase|start scene|expected scene sequence (comma separated, or - for any)"
# Directions: floor right=bar up=balcony; bar/balcony right=chill left=booth; exit up=Mothership right=Underworld; deck right=gallery up=reactor; airlock/throne/bandstand/stage
# left=Hospital (or Hospital late) right=Ward (or Ward late); arena right=court left=furnace; corridor left=day room right=cafeteria; day room right=art room up=dormitory.
spec() {
  case "$1" in
    perfect_a) echo "perfect|right,right,,up,right,,,left,,left,,,left,left,,right,left,,left|19||warehouse,warehouse.bar,warehouse.chill,warehouse.exit,mothership,mothership.gallery,mothership.bridge,mothership.exit,hospital,hospital.corridor,hospital.dayroom,hospital.garden,hospital.exit,hospital_late,hospital_late.cafe,hospital_late.exit,ward_late,ward_late.treat,ward_late.exit,hospital_late";;
    perfect_b) echo "perfect|up,left,,right,right,,,right,up,,,,right,right,,right|16||warehouse,warehouse.balcony,warehouse.booth,warehouse.exit,underworld,underworld.court,underworld.pit,underworld.exit,ward,ward.dorm,ward.corridor,ward.courtyard,ward.exit,ward_late,ward_late.dorm,ward_late.exit,ward_late";;
    perfect_c) echo "perfect|right,left,,right,left,,,left,,right,,,right,left,,right|16||warehouse,warehouse.bar,warehouse.booth,warehouse.exit,underworld,underworld.furnace,underworld.pit,underworld.exit,hospital,hospital.corridor,hospital.cafeteria,hospital.garden,hospital.exit,ward_late,ward_late.treat,ward_late.exit,ward_late";;
    perfect_d) echo "perfect|right,left,,up,up,,,right,right,,,,left,right,,left|16||warehouse,warehouse.bar,warehouse.booth,warehouse.exit,mothership,mothership.reactor,mothership.bridge,mothership.exit,ward,ward.art,ward.corridor,ward.courtyard,ward.exit,hospital_late,hospital_late.quiet,hospital_late.exit,hospital_late";;
    sloppy) echo "accuracy:0.55|right,left,right,up,right,left|6||-";;
    none) echo "none|right|6||warehouse,warehouse.bar";;
    start_late) echo "perfect|right|1|ward_late.exit|ward_late.exit,ward_late";;
  esac
}

for p in "${PATHS[@]}"; do
  IFS='|' read -r BOT ROUTES UNTIL START EXPECT <<< "$(spec "$p")"
  DIR="$(mktemp -d)"
  echo "== path $p ($BOT, routes $ROUTES)"
  env XDG_DATA_HOME="$DIR/data" RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_STORY_QUIT=1 RW_RUN_BOT="$BOT" RW_RUN_ROUTES="$ROUTES" RW_RUN_UNTIL_PHASE="$UNTIL" RW_SEED=2 \
      ${START:+RW_RUN_START=$START} timeout 900 "$GODOT" --path "$ROOT" res://src/run/run_play.tscn > "$DIR/out.txt" 2>&1
  rc=$?
  BAD="$(grep -E "ERROR|SCRIPT" "$DIR/out.txt" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" | grep -Ev "${RW_WALK_IGNORE:-^\$}" | head -5)"
  if [ -n "$BAD" ]; then echo "FAIL: errors in the run:"; echo "$BAD"; FAIL=1; fi
  if [ "$rc" -ne 0 ]; then echo "FAIL: godot exited $rc"; FAIL=1; fi
  grep -E "^RUN " "$DIR/out.txt" | cut -c1-400
  python3 - "$DIR/out.txt" "$ROOT" "$EXPECT" "$DIR/data" "$p" "$SEEN" <<'PY' || FAIL=1
import json, sys, glob, os, re
out, root, expect, data, name, seen_file = sys.argv[1:7]
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
    for a, b in zip(s["nodes"], s["nodes"][1:]):  # every step is a route of the scene before it
        if b not in [e["to"] for e in nodes[a]["next"]]:
            bad("%s does not lead to %s" % (a, b))
    open(seen_file, "a").write("\n".join(s["nodes"]) + "\n")
    for r in s["rail"]:
        _, node, place = r.split(":")[0], r.split(":")[1], r.split(":")[2]
        n = nodes[node]
        rl = n["place"]["rail"]
        allowed = {n["place"]["waypoint"]} | {p["to"] for p in rl["good"]} | {p["to"] for p in rl["bad"]}
        if place not in allowed:
            bad("rail place %s is not on the rails of %s" % (place, node))
    blocks = len(s["rail"])
    if s["glances"] < blocks:
        bad("%d glances for %d blocks (every block needs one)" % (s["glances"], blocks))
    if blocks and s["moves"] < 1:
        bad("no journey moves")
    print("levels:", " > ".join(s["nodes"]), "| rail stops:", len(s["rail"]), "| moves %d glances %d strolls %d | stages %s | worlds %s" % (s["moves"], s["glances"], s["strolls"], ",".join(sorted(s["worlds"])), ">".join(s["worlds_seen"])))
    print("rail:", " ".join(x.split(":", 1)[1] for x in s["rail"][:16]), "..." if len(s["rail"]) > 16 else "")
if over:
    print("the run ended at phase %s on %s" % over.groups())
saves = glob.glob(data + "/**/story_run.json", recursive=True)
if not saves:
    bad("no run save written")
else:
    sv = json.load(open(saves[0]))
    want = {nodes[x]["world"] for x in s["nodes"]} if s else set()
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
if [ "${#PATHS[@]}" -ge 4 ]; then  # a full walk must have visited every scene of every world
  python3 - "$ROOT" "$SEEN" <<'PY' || FAIL=1
import json, sys
run = json.load(open(sys.argv[1] + "/content/run/run.json"))
seen = {l.strip() for l in open(sys.argv[2]) if l.strip()}
missing = [n["id"] for n in run["nodes"] if n["id"] not in seen]
print("scenes visited: %d of %d" % (len(seen), len(run["nodes"])))
if missing:
    print("FAIL: scenes never visited:", ", ".join(missing))
    sys.exit(1)
PY
fi
rm -f "$SEEN"
[ "$FAIL" -eq 0 ] && echo "run walk-through: OK" || echo "run walk-through: FAILED"
exit $FAIL
