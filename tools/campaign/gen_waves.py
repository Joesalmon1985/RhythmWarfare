"""Derives data/campaign/waves/level_0N.json from the pack's waves.proposed.json by scaling group counts.

    python tools/campaign/gen_waves.py <level> <objective_hp> <infantry_scale> [vehicle_scale]

The proposed waves were authored for entries at the map edge and a 150000 hp core; the tuned files record the
scales that the balance harness (tools/balance.sh, docs/BALANCE.md) settled on. Edit the JSON by hand afterwards if
a level needs a different shape; this script only produces the starting point. It keeps the proposed entries, so run
tools/campaign/retime_waves.py afterwards to assign left / right / top entries and spawn times for the centred base."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
level = int(sys.argv[1])
hp = int(sys.argv[2])
inf_scale = float(sys.argv[3])
veh_scale = float(sys.argv[4]) if len(sys.argv) > 4 else inf_scale
src = json.loads((ROOT / f"campaign/First_Three/level_{level:02d}/waves.proposed.json").read_text())
waves = []
for w in src["waves"]:
    w = json.loads(json.dumps(w))
    for g in w["groups"]:
        scale = inf_scale if g["actor"].startswith("e") else veh_scale
        g["count"] = max(1, round(g["count"] * scale))
    waves.append(w)
out = {"battlefield": "defense_01", "rules": {"objective_hp": {"command_core": hp}}, "tuning": {"source": "waves.proposed.json", "infantry_scale": inf_scale, "vehicle_scale": veh_scale}, "waves": waves}
(ROOT / f"data/campaign/waves/level_{level:02d}.json").write_text(json.dumps(out, indent=1) + "\n")
print(f"level {level}: hp {hp}, infantry x{inf_scale}, vehicles x{veh_scale}")
