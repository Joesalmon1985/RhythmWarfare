"""Copy the OpenRA Red Alert sprites, catalogue entries and rules this game needs out of the DuelMasterBattle checkout.

Run from the project root:  python -I tools/import_openra_assets.py [--dmb <path to DuelMasterBattle>]

Writes:
  assets/openra/*.png              the sprite frames (unchanged pixels)
  assets/openra/catalogue.json     the matching catalogue entries, paths rewritten to res://assets/openra/
  data/openra_rules.json           the actors, weapons and locomotors the roster uses, plus the pinned repair rules
  assets/openra/PROVENANCE.md      where every file came from and under what terms
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DMB = ROOT.parent / "DuelMaster" / "DuelMasterBattle"

# Catalogue ids the rhythm game draws.
CATALOGUE_IDS = [
    "openra.1tnk", "openra.2tnk", "openra.3tnk", "openra.e1", "openra.heli",
    "openra.hpad", "openra.powr", "openra.fact", "openra.weap", "openra.barr", "openra.barracks",
    "openra.brik", "openra.sbag", "openra.gun", "openra.agun", "openra.sam", "openra.ftur",
    "openra.piff", "openra.explosion", "openra.120mm",
]
# File-name families in the art folder. A trailing "-" means "every file starting with this".
FILE_PREFIXES = [
    "1tnk", "1tnk-body", "1tnk-turret", "2tnk", "2tnk-body", "2tnk-turret", "3tnk", "3tnk-body", "3tnk-turret",
    "e1", "heli", "hpad-b-", "powr-b-", "fact", "fact-b-", "weap", "weap-b-", "weap-top", "barr", "barr-b-",
    "brik-b-", "sbag-b-", "gun", "gun-b-", "agun-b-", "sam-b-", "ftur", "ftur-b-", "piff", "veh-hit3", "120mm",
]
ACTORS = ["1tnk", "2tnk", "3tnk", "e1", "heli", "hpad", "powr", "fact", "weap", "barr", "tent", "brik", "sbag",
          "gun", "agun", "sam", "ftur"]

OLD_PREFIX = "res://client/hybrid/art/openra/"
NEW_PREFIX = "res://assets/openra/"


def wanted_file(name: str) -> bool:
    if not name.endswith(".png"):
        return False
    stem = re.sub(r"-\d{4}\.png$", "", name)
    if stem.endswith(".png"):
        stem = stem[:-4]
    for p in FILE_PREFIXES:
        if p.endswith("-"):
            if stem.startswith(p):
                return True
        elif stem == p:
            return True
    return False


def rewrite(obj):
    if isinstance(obj, str):
        return obj.replace(OLD_PREFIX, NEW_PREFIX)
    if isinstance(obj, list):
        return [rewrite(x) for x in obj]
    if isinstance(obj, dict):
        return {k: rewrite(v) for k, v in obj.items()}
    return obj


def repair_rules(openra_dir: Path) -> dict:
    """RepairableBuilding values from the pinned mods/ra rules: the ^Building default and every actor override."""
    out: dict = {}
    for yml in sorted((openra_dir / "mods" / "ra" / "rules").glob("*.yaml")):
        actor = None
        in_block = False
        for line in yml.read_text(encoding="utf-8", errors="replace").splitlines():
            if line and not line[0].isspace() and line.rstrip().endswith(":"):
                actor = line.strip()[:-1]
                in_block = False
                continue
            s = line.strip()
            if s.startswith("RepairableBuilding") and line.startswith("\t") and not line.startswith("\t\t"):
                in_block = True
                out.setdefault(actor, {"file": yml.name})
                continue
            if in_block:
                if line.startswith("\t\t") and ":" in s:
                    k, v = s.split(":", 1)
                    out[actor][k.strip()] = v.strip()
                else:
                    in_block = False
    return out


def collect_refs(o, into: set) -> None:
    if isinstance(o, str) and o.startswith(NEW_PREFIX):
        into.add(o[len(NEW_PREFIX):])
    elif isinstance(o, list):
        for x in o:
            collect_refs(x, into)
    elif isinstance(o, dict):
        for x in o.values():
            collect_refs(x, into)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dmb", type=Path, default=DEFAULT_DMB)
    args = ap.parse_args()
    dmb: Path = args.dmb
    art = dmb / "godot_project" / "client" / "hybrid" / "art"
    rules_src = dmb / "WizardRTSHybrid" / "wizard_rts" / "data" / "openra_rules.json"
    manifest_src = dmb / "WizardRTSHybrid" / "sources" / "manifest.json"
    openra_dir = dmb / "WizardRTSHybrid" / "external" / "openra"
    for p in (art / "catalogue.json", rules_src, manifest_src):
        if not p.exists():
            print("missing:", p)
            return 2

    out_art = ROOT / "assets" / "openra"
    out_art.mkdir(parents=True, exist_ok=True)
    (ROOT / "data").mkdir(exist_ok=True)

    # 1. sprites
    copied = []
    for f in sorted((art / "openra").iterdir()):
        if wanted_file(f.name):
            shutil.copyfile(f, out_art / f.name)
            copied.append(f.name)

    # 2. catalogue subset
    cat = json.loads((art / "catalogue.json").read_text(encoding="utf-8"))
    items = {i["id"]: i for i in cat["items"]}
    missing_ids = [i for i in CATALOGUE_IDS if i not in items]
    if missing_ids:
        print("catalogue ids missing:", missing_ids)
        return 2
    sub = {
        "openra_commit": cat["openra_commit"],
        "display_scale_note": cat.get("display_scale_note", ""),
        "remap_ramp_rgb": [[247, 215, 121], [231, 203, 113], [215, 190, 105], [199, 178, 97], [182, 166, 89],
                           [170, 154, 85], [146, 138, 77], [146, 117, 65], [134, 113, 56], [109, 101, 56],
                           [89, 85, 44], [85, 77, 36], [73, 69, 32], [56, 52, 28], [52, 44, 20], [40, 32, 8]],
        "remap_note": "temperat.pal indices 80..95: the player-colour ramp baked into these PNGs; "
                      "the faction shader maps these exact colours.",
        "items": [rewrite(items[i]) for i in CATALOGUE_IDS],
    }
    referenced: set = set()
    collect_refs(sub["items"], referenced)
    for it in sub["items"]:
        layers = it.get("layers")
        if layers:
            for f in range(int(layers.get("facings", 32))):
                for key in ("body_prefix", "turret_prefix"):
                    referenced.add("%s-%04d.png" % (layers[key], f))
    unresolved = sorted(r for r in referenced if not (out_art / r).exists())
    if unresolved:
        print("catalogue references files that were not copied:", unresolved[:20])
        return 2
    (out_art / "catalogue.json").write_text(json.dumps(sub, indent=1), encoding="utf-8")

    # 3. rules subset
    rules = json.loads(rules_src.read_text(encoding="utf-8"))
    actors = {a: rules["actors"][a] for a in ACTORS if a in rules["actors"]}
    absent = [a for a in ACTORS if a not in rules["actors"]]
    weapons_needed = sorted({w for a in actors.values() for w in a.get("armaments", [])})
    weapons = {w: rules["weapons"][w] for w in weapons_needed}
    out_rules = {
        "source": rules["source"],
        "openra_commit": cat["openra_commit"],
        "actors": actors,
        "weapons": weapons,
        "locomotors": rules["locomotors"],
        "repair": repair_rules(openra_dir) if openra_dir.exists() else {"note": "pinned checkout not found"},
        "repair_trait_defaults": {
            "RepairPercent": 20, "RepairInterval": 24, "RepairStep": 7,
            "note": "RepairableBuilding.cs defaults at the pinned commit; mods/ra ^Building overrides RepairStep to 700",
        },
    }
    (ROOT / "data" / "openra_rules.json").write_text(json.dumps(out_rules, indent=1), encoding="utf-8")

    # 4. provenance
    manifest = json.loads(manifest_src.read_text(encoding="utf-8"))
    pins = {s["id"]: s for s in manifest["sources"]}
    digest = hashlib.sha256()
    for n in copied:
        digest.update((out_art / n).read_bytes())
    lines = [
        "# Provenance of assets/openra and data/openra_rules.json",
        "",
        f"Generated by `tools/import_openra_assets.py` from the DuelMasterBattle checkout at `{dmb}`.",
        "Nothing here was drawn or edited by hand; pixels are byte-identical to the source files.",
        "",
        "## Art",
        "",
        f"- {len(copied)} PNG frames copied from `godot_project/client/hybrid/art/openra/` "
        f"(sha256 over all frames in name order: `{digest.hexdigest()}`).",
        "- The frames were extracted from the owner's own Red Alert content packages (`conquer.mix` and friends) with "
        "OpenRA.Utility and the project's own `mix_read.py`/`shp_td.py`, rendered with the `temperat` palette. The source "
        "catalogue records that use was permitted for this project. The OpenRA engine is GPL-3.0-or-later; the original "
        "Red Alert artwork is not covered by that licence (Electronic Arts released Red Alert as freeware in 2008).",
        "- Player-colour remap: temperat.pal indices 80..95 are baked in as the exact RGB values listed in "
        "`catalogue.json` (`remap_ramp_rgb`).",
        f"- Catalogue ids kept: {', '.join(CATALOGUE_IDS)}.",
        "- Never imported upstream, so not available here: `openra.tent` (Allied barracks). Both sides use `barr`.",
        "",
        "## Rules",
        "",
        f"- `data/openra_rules.json` is a subset of `WizardRTSHybrid/wizard_rts/data/openra_rules.json` ({rules['source']}): "
        f"actors {', '.join(actors)}; weapons {', '.join(weapons_needed)}; all locomotors.",
        f"- Actors requested but absent upstream: {absent or 'none'}.",
        "- `repair` lists every `RepairableBuilding` block in the pinned `mods/ra/rules/*.yaml`; "
        "`repair_trait_defaults` are the C# trait defaults.",
        "",
        "## Pins",
        "",
        f"- OpenRA: {pins['openra']['url']} @ `{pins['openra']['commit']}` "
        f"({pins['openra']['branch']}, {pins['openra']['license']})",
        f"- OpenRA mod SDK: {pins['openra-mod-sdk']['url']} @ `{pins['openra-mod-sdk']['commit']}`",
        f"- DuelMasterBattle manifest pinned on {manifest['pinned']}.",
        "",
    ]
    (out_art / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"copied {len(copied)} frames, {len(sub['items'])} catalogue items, {len(actors)} actors, {len(weapons)} weapons")
    if absent:
        print("actors absent upstream:", absent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
