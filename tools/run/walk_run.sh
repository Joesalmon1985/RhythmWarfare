#!/usr/bin/env bash
# Run walk-through: plays the REAL run scene (src/run/run_play.tscn, every world's stage, the rails, the passage frame, the saves) on the virtual song clock with scripted
# play and scripted route choices, from a throwaway user data directory (XDG_DATA_HOME), never the owner's save. A phase is a scene (a room of a world); between them the
# paths perfect_a to perfect_d visit all 36 scenes of the seven worlds (checked at the end of a full run). Fails on any ERROR or SCRIPT line, a wrong scene sequence, a step that
# is not a route of the scene before it, a rail place that is not on the scene's rails, missing glances, a wrong run save (reached = the worlds visited, never a scene), or a
# chapter save written by the run. Needs a display (the worlds are rendered). The save goes to the throwaway directory on Linux (XDG_DATA_HOME) and on Windows (APPDATA); the audio driver is Dummy.
#   RW_WALK_IGNORE=<regex> drops matching ERROR lines from the check.
#   RW_RUN_TAPS=scripted|none|changed|failure  the tap policy of the hotspot window (default scripted: the bot taps the hotspot that leads where the path says; none: no taps, the default exits;
#                changed: a decoy first, then the scripted tap; failure: scripted taps with the last block of every phase missed, so every tapped hotspot takes its failure outcome). With none and
#                failure the scene sequence is not fixed (only "every step is a route of the scene before it" and the saves are checked, and the all-scenes check is skipped).
#   RW_RUN_TRACK_EXIT=end|first  track scenes (docs/RUN_TRACK_SCENES.md): the bot plays every track scene to its default end (end, the default), or touches its route at the first open lap
#                (first). Each track scene that ended is checked against its plan. Point RW_TRACKS_DIR at a packs folder on the command line to have track scenes at all.
#   bash tools/run/walk_run.sh [path ...]     paths: perfect_a perfect_b perfect_c perfect_d sloppy none start_late   (default: all)
#   bash tools/run/walk_run.sh --path <id> [walk ...]   a sister run (content/paths/<id>) started with RW_RUN_PATH: the walks are tools/run/path_walk_spec.py's (perfect: every default route to the first ending
#                and back into the Warehouse; sloppy; none; and the ones in content/paths/<id>/walks.json). The save must hold the path's worlds under `paths`, never under `reached`.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
RATE="${RW_STORY_RATE:-3}"
PATH_ID=""
if [ "${1:-}" = "--path" ]; then PATH_ID="$2"; shift 2; fi
PATHS=("$@")
if [ -n "$PATH_ID" ]; then
  [ ${#PATHS[@]} -eq 0 ] && read -r -a PATHS <<< "$(python3 "$ROOT/tools/run/path_walk_spec.py" "$PATH_ID" names)"
else
  [ ${#PATHS[@]} -eq 0 ] && PATHS=(perfect_a perfect_b perfect_c perfect_d sloppy none start_late)
fi
SEEN="$(mktemp)"
FAIL=0

# path -> "bot|routes (one direction per phase, empty = the default)|until_phase|start scene|expected scene sequence (comma separated, or - for any)"
# Directions: floor right=bar up=balcony; bar/balcony right=chill left=booth; exit up=Mothership right=Underworld; deck right=gallery up=reactor; airlock/throne/bandstand/stage
# left=Hospital (or Hospital late) right=Ward (or Ward late); arena right=court left=furnace; corridor left=day room right=cafeteria; day room right=art room up=dormitory.
spec() {
  if [ -n "$PATH_ID" ]; then python3 "$ROOT/tools/run/path_walk_spec.py" "$PATH_ID" "$1"; return; fi
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
  case "${RW_RUN_TAPS:-scripted}" in none|failure) EXPECT="-";; esac
  DIR="$(mktemp -d)"
  echo "== path $p ($BOT, routes $ROUTES)${PATH_ID:+ in the path $PATH_ID}"
  env XDG_DATA_HOME="$DIR/data" APPDATA="$DIR/data" ${PATH_ID:+RW_RUN_PATH=$PATH_ID} RW_RUN_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_STORY_QUIT=1 RW_RUN_BOT="$BOT" RW_RUN_ROUTES="$ROUTES" RW_RUN_UNTIL_PHASE="$UNTIL" RW_SEED=2 \
      ${START:+RW_RUN_START=$START} timeout 900 "$GODOT" --audio-driver Dummy --path "$ROOT" res://src/run/run_play.tscn > "$DIR/out.txt" 2>&1
  rc=$?
  BAD="$(grep -E "ERROR|SCRIPT" "$DIR/out.txt" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" | grep -Ev "${RW_WALK_IGNORE:-^\$}" | head -5)"
  if [ -n "$BAD" ]; then echo "FAIL: errors in the run:"; echo "$BAD"; FAIL=1; fi
  if [ "$rc" -ne 0 ]; then echo "FAIL: godot exited $rc"; FAIL=1; fi
  grep -E "^RUN " "$DIR/out.txt" | cut -c1-400
  PATH_ID="$PATH_ID" python3 - "$DIR/out.txt" "$ROOT" "$EXPECT" "$DIR/data" "$p" "$SEEN" <<'PY' || FAIL=1
import json, sys, glob, os, re
out, root, expect, data, name, seen_file = sys.argv[1:7]
path_id = os.environ.get("PATH_ID", "")
text = open(out).read()
run = json.load(open(root + "/content/run/run.json"))
nodes = {n["id"]: n for n in run["nodes"]}
path_nodes = {}
if path_id:  # a path's scenes (and, after its ending, the Warehouse's): each step is a route of the scene before it, or the way back
    prun = json.load(open(root + "/content/paths/%s/run.json" % path_id))
    path_nodes = {n["id"]: n for n in prun["nodes"]}
    nodes = {**nodes, **path_nodes}
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
        if b not in [e["to"] for e in nodes[a]["next"]] and not (a in path_nodes and path_nodes[a].get("ending") and b == "warehouse"):
            bad("%s does not lead to %s" % (a, b))
    # the laps (docs/CONTINUOUS_RUN.md "Two laps"): each scene played all its laps but the last one started (a lap_start per extra lap, in order); the scene the walk stopped in has played none, some or all
    default_laps = int(prun["path"].get("laps", 1)) if path_id else 1
    def laps_of(x):
        return int(path_nodes[x].get("laps", default_laps)) if x in path_nodes else 1
    # a track scene (docs/RUN_TRACK_SCENES.md) plays the laps its summary entry says (in visit order); every other scene its data's laps
    tracks = s.get("tracks", [])
    visit_laps, ti = [], 0
    for x in s["nodes"]:
        if ti < len(tracks) and tracks[ti]["node"] == x:
            visit_laps.append(int(tracks[ti]["laps"]))
            ti += 1
        else:
            visit_laps.append(laps_of(x))
    want_laps = [x for x, k in zip(s["nodes"][:-1], visit_laps[:-1]) for _ in range(k - 1)]
    got_laps = s.get("laps", [])
    if got_laps[:len(want_laps)] != want_laps:
        bad("laps %s, expected %s first" % (",".join(got_laps), ",".join(want_laps)))
    elif any(x != s["nodes"][-1] for x in got_laps[len(want_laps):]) or len(got_laps) - len(want_laps) > visit_laps[-1] - 1:
        bad("laps of the last scene: %s" % ",".join(got_laps[len(want_laps):]))
    # the track scenes that ended reach their planned length (RW_RUN_TRACK_EXIT=end, the default), or end at their first open lap where the bot left (first)
    exit_mode = os.environ.get("RW_RUN_TRACK_EXIT", "end")
    for tr in tracks:
        if tr.get("end") != "route":
            continue
        if tr["left_early"]:
            if exit_mode != "first" or int(tr["laps"]) != int(tr["doors_from_lap"]):
                bad("track scene %s (%s) left at lap %d of %d (exit %s)" % (tr["node"], tr["track"], int(tr["laps"]), int(tr["planned"]), exit_mode))
        elif int(tr["laps"]) != int(tr["planned"]) + int(tr["extended"]):
            bad("track scene %s (%s) played %d laps, planned %d" % (tr["node"], tr["track"], int(tr["laps"]), int(tr["planned"])))
    if tracks:
        print("track scenes:", " ".join("%s=%s:%d/%d%s" % (tr["node"], tr["track"], int(tr["laps"]), int(tr["planned"]), "" if tr.get("end") else "(on)") for tr in tracks))
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
    want = {nodes[x]["world"] for x in s["nodes"] if x not in path_nodes} if s else set()
    if s and set(sv["reached"]) != want:
        bad("the save reached %s, expected %s" % (sorted(sv["reached"]), sorted(want)))
    if path_id and s:
        pw = {nodes[x]["world"] for x in s["nodes"] if x in path_nodes}
        got = set(sv.get("paths", {}).get(path_id, {}).get("reached", []))
        if got != pw:
            bad("the save's paths.%s.reached is %s, expected %s" % (path_id, sorted(got), sorted(pw)))
        ends = {path_nodes[x]["ending"] for i, x in enumerate(s["nodes"][:-1]) if x in path_nodes and path_nodes[x].get("ending") and s["nodes"][i + 1] == "warehouse"}
        if set(sv.get("paths", {}).get(path_id, {}).get("endings", [])) != ends:
            bad("the save's endings %s, expected %s" % (sv.get("paths", {}).get(path_id, {}).get("endings"), sorted(ends)))
    if int(sv["runs"]) != 1:
        bad("the save counts %s runs, expected 1" % sv["runs"])
    print("save: reached", ",".join(sorted(sv["reached"])), "| runs", sv["runs"], "| best phases", sv["best_phases"])
if glob.glob(data + "/**/story_campaign.json", recursive=True):
    bad("the run wrote a chapter save (story_campaign.json)")
sys.exit(0 if ok else 1)
PY
  rm -rf "$DIR"
done
if [ -n "$PATH_ID" ] && [ "${RW_RUN_TAPS:-scripted}" != "none" ] && [ "${RW_RUN_TAPS:-scripted}" != "failure" ]; then  # every scene of the path visited by the walks together
  python3 - "$ROOT" "$SEEN" "$PATH_ID" <<'PY' || FAIL=1
import json, sys
run = json.load(open(sys.argv[1] + "/content/paths/%s/run.json" % sys.argv[3]))
seen = {l.strip() for l in open(sys.argv[2]) if l.strip()}
missing = [n["id"] for n in run["nodes"] if n["id"] not in seen]
print("scenes of the path visited: %d of %d" % (len(run["nodes"]) - len(missing), len(run["nodes"])))
if missing:
    print("FAIL: scenes never visited:", ", ".join(missing))
    sys.exit(1)
PY
fi
if [ -z "$PATH_ID" ] && [ "${#PATHS[@]}" -ge 4 ] && [ "${RW_RUN_TAPS:-scripted}" != "none" ] && [ "${RW_RUN_TAPS:-scripted}" != "failure" ]; then  # a full walk must have visited every scene of every world
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
