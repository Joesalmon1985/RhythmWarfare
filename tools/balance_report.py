"""Prints one compact line (plus wave lines for schema 2 runs) from an autoplay.gd JSON report on stdin.
   usage: balance_report.py <label> [--waves]"""
import json
import sys

label = sys.argv[1]
show_waves = "--waves" in sys.argv
txt = sys.stdin.read()
try:
    d = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
except Exception:
    print(label + ": ERROR", txt[:1500])
    sys.exit(0)
if d.get("mode") == "mission":
    core = d["objective_hp"].get("command_core", {"hp": 0, "max": 1})
    g = d["grades"]
    print("%-10s seed %-2s %-8s %-30s t=%5.1fs acc=%3.0f%% seq %2d/%2d (sharp %d steady %d loose %d) built %2d units %d repairs %d alive %2d core %3d%% lost P:%s E:%s peak=%s" % (
        d["policy"], str(d["seed"])[-1], d["outcome"], d["reason"], d["outcome_time_s"], d["accuracy"] * 100, d["sequences_passed"], d["sequences"],
        g["sharp"], g["steady"], g["loose"], d["built"], d["units"], d["repairs"], d["defenses_alive"],
        round(100 * core["hp"] / core["max"]), sum(d["lost"][0].values()), sum(d["lost"][1].values()), d["peak_live_units"]))
    if show_waves:
        for wid, w in sorted(d["waves"].items()):
            print("      %-8s spawned %2d/%2d killed %2d  first %6.1fs cleared %6.1fs" % (wid, w["spawned"], w["total"], w["killed"], w["first_spawn_s"], w["cleared_s"]))
    sys.exit(0)
if d.get("mode") == "defense":
    core = d["objective_hp"].get("command_core", {"hp": 0, "max": 1})
    ps = d["production_summary"]
    print("%-14s seed %-2s %-8s %-28s t=%5.1fs acc=%3.0f%% core %3d%%  groups %3d by point %s  lost P:%s E:%s peak=%s" % (
        d["policy"], str(d["seed"])[-1], d["outcome"], d["reason"], d["outcome_time_s"], d["accuracy"] * 100,
        round(100 * core["hp"] / core["max"]), d["groups"], ps["groups_by_point"],
        sum(d["lost"][0].values()), sum(d["lost"][1].values()), d["peak_live_units"]))
    if show_waves:
        for wid, w in sorted(d["waves"].items()):
            print("      %-8s spawned %2d/%2d killed %2d  first %6.1fs reached %6.1fs cleared %6.1fs" % (wid, w["spawned"], w["total"], w["killed"], w["first_spawn_s"], w["reached_s"], w["cleared_s"]))
    sys.exit(0)
p = d["produced"]
l = d["lost"]
print("%-16s %-8s %-22s t=%6.1fs acc=%4.0f%%  built P:%dt/%di/%da  E:%dt/%di/%da  lost P:%s E:%s  peak=%s  mainHP P=%d E=%d  busy=%s blocked=%s" % (
    d["policy"], d["outcome"], d["reason"], d["outcome_time_s"], d["accuracy"] * 100,
    p[0]["tank"], p[0]["infantry"], p[0]["aircraft"], p[1]["tank"], p[1]["infantry"], p[1]["aircraft"],
    {k: v for k, v in l[0].items() if k in ("factory", "barracks", "pad", "main")}, {k: v for k, v in l[1].items() if k in ("factory", "barracks", "pad", "main")},
    d["peak_live_units"], d["player_main_hp"], d["enemy_main_hp"], d["air_busy"], d["blocked"]))
for e in d["timeline"]:
    ev = e["event"]
    if ev["kind"] in ("producer_lost", "pad_lost", "outcome"):
        print("    %6.1fs %s %s" % (e["t"], ev["kind"], {k: v for k, v in ev.items() if k in ("side", "role", "slot", "reason", "pads_alive")}))
