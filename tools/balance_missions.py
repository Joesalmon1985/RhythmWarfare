"""Seeded balance trials for every mission, as a Markdown table (docs/BALANCE.md quotes it).

    python tools/balance_missions.py [--seeds 1 2 3] [--policies perfect beginner sloppy none] [--missions m01 m02] > out.md

Runs tools/autoplay.gd headless per mission, policy and seed (no audio, no rendering) and prints one row per run:
outcome, sequences passed and their grades, rewards built, defenses alive, core health, enemies killed, peak live units.
A simulation pass is evidence about the waves, not about how hard a mission feels to a person.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = os.environ.get("GODOT", str(Path(os.environ.get("USERPROFILE", "")) / "Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe"))


def run(pack: str, policy: str, seed: int) -> dict:
    out = subprocess.run([GODOT, "--headless", "--path", str(ROOT), "-s", "tools/autoplay.gd", "--", f"res://songs/{pack}", policy, "1.0", str(seed)],
                         capture_output=True, text=True, timeout=600).stdout
    try:
        return json.loads(out[out.index("{"):out.rindex("}") + 1])
    except ValueError:
        return {"error": out[-500:]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="*", type=int, default=[1, 2, 3])
    ap.add_argument("--policies", nargs="*", default=["perfect", "beginner", "sloppy", "none"])
    ap.add_argument("--missions", nargs="*", default=[])
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    packs = sorted(p.name for p in (ROOT / "songs").glob("m[0-9][0-9]_*") if (p / "level.json").exists())
    if args.missions:
        packs = [p for p in packs if any(p.startswith(m) for m in args.missions)]
    jobs = [(p, pol, s) for p in packs for pol in args.policies for s in args.seeds]
    with ThreadPoolExecutor(args.jobs) as ex:
        results = list(ex.map(lambda j: (j, run(*j)), jobs))
    print("| Mission | Policy | Seed | Outcome | At | Sequences (sharp/steady/loose) | Built | Units | Repairs | Defenses alive | Core | Enemies killed | Peak units (you / enemy) |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for (pack, pol, seed), d in results:
        if "error" in d:
            print(f"| {pack} | {pol} | {seed} | ERROR | | | | | | | | | |")
            continue
        core = d["objective_hp"].get("command_core", {"hp": 0, "max": 1})
        g = d["grades"]
        print(f"| {pack} | {pol} | {seed} | {d['outcome']} | {d['outcome_time_s']:.1f} s | {d['sequences_passed']}/{d['sequences']} "
              f"({g['sharp']}/{g['steady']}/{g['loose']}) | {d['built']} | {d['units']} | {d['repairs']} | {d['defenses_alive']} | "
              f"{round(100 * core['hp'] / max(core['max'], 1))}% | {sum(d['lost'][1].values())} | {d['peak_live_units'][0]} / {d['peak_live_units'][1]} |")


if __name__ == "__main__":
    main()
