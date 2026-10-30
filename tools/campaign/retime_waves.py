"""Assigns entries and spawn times to the tuned waves in data/campaign/waves/level_0N.json.

    python tools/campaign/retime_waves.py [1 2 3]

Entries follow a readable pattern per level (ENTRY_PLAN). Spawn times are chosen from contact times: the first wave's
slowest actor reaches its defense point shortly after the four opening bars, the last wave's final unit arrives
`END_MARGIN_S` before the song ends, and the waves between keep the authored spacing in proportion. The authored
`start_tick` is kept as `authored_start_tick`; `contact_tick` is when the slowest actor of the first spawn reaches the
defense point (straight line at the rules speed). Run `build_defense_pack.py <n> --waves-only` afterwards."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIA = {"left": "defense_1", "top": "defense_2", "right": "defense_3"}
# Production is round robin over the three defense points, so every level uses all three approaches: a wave from one
# side only would leave two thirds of the defenders out of the fight.
ENTRY_PLAN = {
    1: ["left", "top", "right", "left", "top", "right", "left"],       # a sweep, left to top to right
    2: ["left", "right", "top"] * 3,                                    # the sides in turn, the top as the third beat
    3: ["left", "top", "right"] * 3 + ["left", "top"],                  # the sweep again, longer
}
OPENING_BARS = 4
FIRST_CONTACT_AFTER_S = 1.0  # first contact this long after the opening bars at the earliest
END_MARGIN_S = 2.0           # the last unit reaches its defense point this long before the song ends
TICKS_PER_BAR = 3840


def travel_seconds(actor: dict, a: tuple, b: tuple) -> float:
    cps = actor["speed"] / 1024.0 * 25.0
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 / cps


def field() -> tuple[dict, dict, dict]:
    bf = json.loads((ROOT / "data/battlefields/defense_01.json").read_text())
    actors = json.loads((ROOT / "data/openra_rules.json").read_text())["actors"]
    entries = {e["id"]: (e["x"] + 0.5, e["y"] + 0.5) for e in bf["entries"]}
    points = {p["id"]: (p["x"] + 0.5, p["y"] + 0.5) for p in bf["defense_points"]}
    return entries, points, actors


def slowest_travel(wave: dict, entries: dict, points: dict, actors: dict) -> float:
    return max(travel_seconds(actors[g["actor"]], entries[wave["entry"]], points[wave["via_defense_point"]]) for g in wave["groups"])


def retime(number: int, duration_ticks: int, ticks_per_second: float) -> None:
    path = ROOT / f"data/campaign/waves/level_{number:02d}.json"
    data = json.loads(path.read_text())
    entries, points, actors = field()
    waves = data["waves"]
    plan = ENTRY_PLAN[number]
    assert len(plan) == len(waves), f"level {number}: {len(waves)} waves, plan has {len(plan)}"
    for w, entry in zip(waves, plan):
        w.setdefault("authored_start_tick", w["start_tick"])
        w["entry"] = entry
        w["via_defense_point"] = VIA[entry]
    old = [w["authored_start_tick"] for w in waves]
    travel = [slowest_travel(w, entries, points, actors) for w in waves]
    first_contact = max(OPENING_BARS * TICKS_PER_BAR / ticks_per_second + FIRST_CONTACT_AFTER_S, travel[0] + 0.5)
    last = waves[-1]
    spread = max((g["count"] - 1) * g["spawn_spacing_ticks"] for g in last["groups"]) / ticks_per_second
    last_contact = duration_ticks / ticks_per_second - END_MARGIN_S - spread
    for i, w in enumerate(waves):
        frac = (old[i] - old[0]) / max(old[-1] - old[0], 1)
        contact = first_contact + (last_contact - first_contact) * frac
        w["contact_tick"] = int(round(contact * ticks_per_second))
        w["start_tick"] = max(0, int(round((contact - travel[i]) * ticks_per_second)))
        w["start_bar"] = w["start_tick"] // TICKS_PER_BAR + 1
    path.write_text(json.dumps(data, indent=1) + "\n")
    print(f"level {number}: entries {plan}, first contact {first_contact:.1f} s, last contact {last_contact:.1f} s of {duration_ticks / ticks_per_second:.1f} s")


if __name__ == "__main__":
    bpm, tpb = 174, 960
    tps = bpm * tpb / 60.0
    bars = {1: 32, 2: 40, 3: 48}
    for n in [int(a) for a in sys.argv[1:]] or [1, 2, 3]:
        retime(n, bars[n] * TICKS_PER_BAR, tps)
