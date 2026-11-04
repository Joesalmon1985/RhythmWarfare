#!/usr/bin/env bash
# Campaign walk-through (docs/STORY_25D_PLAN.md 8.2): runs the REAL scene chain story_play > story_result > story_interlude > story_play ... on the virtual song clock,
# with scripted inputs per chapter, from a throwaway user data directory (XDG_DATA_HOME), never the owner's save. Fails on any ERROR or SCRIPT line, a wrong chain, or a
# story save / Story Campaign menu that does not show exactly the right unlocks. Needs a display (the world is rendered).
#   bash tools/story/walk_campaign.sh [path ...]     paths: perfect none sloppy2 mixed_a mixed_b   (default: all)   TRACE_OUT=<file> keeps the combined trace
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/godot/Godot_v4.5.1-stable_linux.x86_64}"
RATE="${RW_STORY_RATE:-3}"
PATHS=("$@"); [ ${#PATHS[@]} -eq 0 ] && PATHS=(perfect none sloppy2 mixed_a mixed_b)
FAIL=0

policies() {  # the per-chapter policies of a path
  case "$1" in
    perfect) echo "night_one=perfect;mothership=perfect;hospital=perfect;underworld=perfect;mental_hospital=perfect";;
    none) echo "night_one=none;mothership=none;hospital=none;underworld=none;mental_hospital=none";;
    sloppy2) echo "night_one=sloppy@2;mothership=sloppy@2;hospital=sloppy@2;underworld=sloppy@2;mental_hospital=sloppy@2";;
    mixed_a) echo "night_one=perfect;mothership=none;mental_hospital=none;hospital=none";;
    mixed_b) echo "night_one=none;underworld=perfect;hospital=perfect;mothership=none;mental_hospital=none";;
  esac
}
expected() {  # the named endings and the final menu of a path ("-" for a path that only has to be self-consistent)
  case "$1" in
    perfect) echo "night_one:legendary_set mothership:galactic_headliner hospital:family_celebration | night_one,mothership,hospital";;
    none) echo "night_one:lost_the_floor underworld:devoured mental_hospital:lights_out | night_one,underworld,mental_hospital";;
    sloppy2) echo "night_one:good_night | -";;
    mixed_a) echo "night_one:legendary_set mothership:beamed_home | night_one,mothership,mental_hospital";;
    mixed_b) echo "night_one:lost_the_floor underworld:resident_dj | night_one,underworld,hospital";;
  esac
}

for p in "${PATHS[@]}"; do
  DIR="$(mktemp -d)"
  TRACE="$DIR/trace.txt"
  : > "$TRACE"
  echo "== path $p"
  env XDG_DATA_HOME="$DIR/data" RW_STORY_VIRTUAL=1 RW_STORY_RATE="$RATE" RW_STORY_AUTO_ADVANCE=1 RW_STORY_RECORD=1 RW_STORY_TRACE="$TRACE" \
      RW_STORY_POLICIES="$(policies "$p")" RW_AUTOPLAY= \
      timeout 900 "$GODOT" --path "$ROOT" res://src/scenes/story_play.tscn > "$DIR/out.txt" 2>&1
  rc=$?
  BAD="$(grep -E "ERROR|SCRIPT" "$DIR/out.txt" | grep -v "RID allocations\|leaked\|still in use\|ObjectDB" | head -5)"
  if [ -n "$BAD" ]; then echo "FAIL: errors in the run:"; echo "$BAD"; FAIL=1; fi
  if [ "$rc" -ne 0 ]; then echo "FAIL: godot exited $rc"; FAIL=1; fi
  cat "$TRACE"
  [ -n "${TRACE_OUT:-}" ] && { echo "# path $p"; cat "$TRACE"; } >> "$TRACE_OUT"
  python3 - "$TRACE" "$ROOT" "$(expected "$p")" "$DIR/data" <<'PY' || FAIL=1
import json, sys, glob, os
trace, root, exp, data = sys.argv[1:5]
lines = [l.split() for l in open(trace).read().strip().splitlines()]
kv = lambda l: dict(x.split("=", 1) for x in l[1:])
chapters = {c["id"]: c for c in json.load(open(root + "/content/story/chapters.json"))["chapters"]}
ok = True
def bad(msg):
    global ok
    ok = False
    print("FAIL:", msg)
results, plays = [], []
expect_next = "night_one"
for i, l in enumerate(lines):
    d = kv(l)
    if l[0] == "play":
        plays.append(d["chapter"])
        if d["chapter"] != expect_next:
            bad("played %s but the route led to %s" % (d["chapter"], expect_next))
    elif l[0] == "result":
        results.append((d["chapter"], d["ending"]))
        route = next((r for r in chapters[d["chapter"]]["routes"] if d["ending"] in r["on"]), None)
        want = route["to"] if route else "end"
        if d["route"] != want:
            bad("%s ending %s routed to %s, expected %s" % (d["chapter"], d["ending"], d["route"], want))
        expect_next = want
    elif l[0] == "interlude":
        route = next(r for r in chapters[d["from"]]["routes"] if d["ending"] in r["on"])
        if d["to"] != route["to"] or d["name"] != route["interlude"]:
            bad("interlude %s does not match the route" % d)
named, final = exp.split("|")
for pair in named.split():
    ch, e = pair.split(":")
    if (ch, e) not in results:
        bad("expected %s to end with %s, got %s" % (ch, e, results))
menus = [kv(l) for l in lines if l[0] == "menu"]
if not menus:
    bad("the walk never reached the Story Campaign menu")
else:
    seen = {}
    for ch, e in results:
        seen.setdefault(ch, set()).add(e)
    unlocked = ["night_one"] + [c for c in chapters if c != "night_one" and any(r["to"] == c and set(r["on"]) & seen.get(o, set()) for o in chapters for r in chapters[o]["routes"])]
    order = [c for c in chapters if c in unlocked]
    got = menus[-1]["unlocked"].split(",")
    want = order if final.strip() == "-" else final.strip().split(",")
    if got != want or got != order:
        bad("the menu lists %s, expected %s (from the endings seen)" % (got, want))
    saves = glob.glob(data + "/**/story_campaign.json", recursive=True)
    if not saves:
        bad("no story save written")
    else:
        lv = json.load(open(saves[0]))["levels"]
        if sorted(lv) != sorted(seen):
            bad("the save has levels %s, expected %s" % (sorted(lv), sorted(seen)))
print("chain:", " > ".join("%s(%s)" % r for r in results), "| menu:", menus[-1]["unlocked"] if menus else "-")
sys.exit(0 if ok else 1)
PY
  rm -rf "$DIR"
done
[ "$FAIL" -eq 0 ] && echo "walk-through: OK" || echo "walk-through: FAILED"
exit $FAIL
