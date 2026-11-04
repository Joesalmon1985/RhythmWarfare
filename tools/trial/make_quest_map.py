"""Builds the whole-quest map of the Deathtrap Dungeon: content/trial/quest_map.json, docs/TRIAL_QUEST_MAP.md and docs/trial_quest_map.png.

    python tools/trial/make_quest_map.py build  <DuelMasterBattle checkout>     # reads that repository (read-only) and writes the JSON
    python tools/trial/make_quest_map.py render                                 # JSON -> the markdown and the picture (no checkout needed)

What the map is, honestly: the *verified macrograph*. The book has 400 passages and DuelMasterBattle has only verified 28 of them (`status:
verified_macrograph_not_full_400_node_adjacency`), so the map holds every verified passage with its book-checked edges, every passage those edges
point at (marked REFERENCED: its own onward links are not verified and are not invented here), the 17 physical zones of the legacy adaptation with
their real exits and the flags that gate them, the three gems and the final lock, the contestants and the major encounters. Every passage lists the
zone it belongs to; the zone order is the legacy adaptation's, which is the route a run takes from passage 1 to the victory passage 400.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "content" / "trial" / "quest_map.json"
PASSAGES = ROOT / "content" / "trial" / "passages.json"

# zone id -> (design zone letter of the canonical report, passages the TRIAL_CANON_STATUS table assigns to it, role, key items, key encounters)
ZONES = {
    "dd_entrance": ("A", [1, 270], "Trial gate and crystal entrance: the contestants, Sukumvit's aid box, the first corridor", ["aid box (2 gold pieces, Sukumvit's note)"], []),
    "dd_fork": ("A", [66, 119, 56], "First fork: the painted arrow, the footprints, the east loop that reconnects", ["draught to the service tunnels once the east loop is walked"], ["Giant Fly (legacy placement)"]),
    "dd_galleries": ("B", [293, 382, 137, 44, 222, 391], "Footprint Galleries: branching tracks, the old man's riddle, the petrified Knight", ["torch", "bell", "chest"], ["Guard Dog"]),
    "dd_pit": ("D", [154, 22, 184, 63, 311, 323, 149], "Throm's Pit: the Barbarian joins; lower him, be lowered, jump or climb alone (ally or betray)", [], []),
    "dd_lower": ("D", [194, 138, 52, 169, 288, 221, 397, 25, 369, 64], "Lower Route: the books, the Cave Troll ambush with Throm, the bone ring", ["red book (a fourth weave place)", "black book (a potion)", "bone ring"], ["Cave Trolls"]),
    "dd_trialmaster": ("E", [60, 365, 290, 191, 84, 302, 379, 179, 213, 95], "Dwarf Trialmaster complex: the lock-in, the dice and cobra tests, Throm's forced duel, the concealed way", ["Stone taught at the end"], ["Dwarf Trialmaster", "Throm (forced duel)"]),
    "dd_idol": ("C", [37, 240, 351, 239, 34, 89], "Idol Cavern: the Flying Guardians, the emerald eye, the false eye", ["EMERALD"], ["Flying Guardians"]),
    "dd_grotto": ("F", [281, 399, 192], "Drowned Grotto: the Boa, the dying Elf, her bread and charm, the diamond clue", ["bread (herbs)", "charm", "the diamond clue"], ["Boa Constrictor"]),
    "dd_vaults": ("I", [162, 218, 65, 252, 442], "Sapphire Vaults: the iron key and sapphire, the false diamond that wounds and seals the inner vault", ["SAPPHIRE", "iron key"], ["false diamond trap"]),
    "dd_vault_inner": ("I", [269, 127, 330], "Inner Vault: the true diamond (the legacy puts it here; the book's route is the later hall, 269 and 330)", ["DIAMOND"], []),
    "dd_service": ("H", [], "Service Tunnels: the prisoner, Poison Ivy's toll, the Basket man's lift; the way back to the fork once the east loop was walked", ["torch (Ivy's toll)"], ["Poison Ivy"]),
    "dd_mirror": ("G", [], "Mirror Gallery: smash the mirrors or fight the demon; the shard teaches Light", ["light shard"], ["Mirror Demon"]),
    "dd_blood": ("G", [], "Bloodbeast Lair: the herbs or the prisoner's knowledge ban Vine from its Ward", ["blood clue"], ["Bloodbeast"]),
    "dd_grub": ("G", [], "Grub Tunnels: the boulder, the trapped chest", ["gold in the trapped chest"], ["Rock Grub"]),
    "dd_troglodytes": ("F", [], "Troglodyte Cavern: the rite, the run of the arrow, or the champion; the reed back to the grotto", ["hollow tube"], ["Troglodytes"]),
    "dd_manticore": ("J", [], "Manticore Gate: the last major creature, a boss; winning leads on to Igbut", [], ["Manticore"]),
    "dd_igbut": ("K", [364, 31, 3, 62, 16, 392, 177, 287, 132, 249, 241, 376, 400], "Igbut's door: the gem check, the three-position lock, the final crossbow trap, daylight", ["the three gems are checked and, on a wrong order, scattered"], ["Igbut", "Sukumvit's crossbow"]),
}
EXIT_ZONE = "dd_exit"
ORDER = ["dd_entrance", "dd_fork", "dd_galleries", "dd_pit", "dd_lower", "dd_trialmaster", "dd_idol", "dd_grotto", "dd_vaults", "dd_vault_inner", "dd_service", "dd_mirror",
         "dd_blood", "dd_grub", "dd_troglodytes", "dd_manticore", "dd_igbut"]
# layout for the picture: serpentine, three rows
GRID = {"dd_entrance": (0, 0), "dd_fork": (1, 0), "dd_galleries": (2, 0), "dd_pit": (3, 0), "dd_lower": (4, 0), "dd_trialmaster": (5, 0),
        "dd_idol": (5, 1), "dd_grotto": (4, 1), "dd_vaults": (3, 1), "dd_vault_inner": (2, 1), "dd_service": (1, 1), "dd_mirror": (0, 1),
        "dd_blood": (0, 2), "dd_grub": (1, 2), "dd_troglodytes": (2, 2), "dd_manticore": (3, 2), "dd_igbut": (4, 2), EXIT_ZONE: (5, 2)}
NAMES = {EXIT_ZONE: "Daylight: Champion (400)"}


def build(src: Path) -> None:
    bb = json.loads((src / "DD" / "Deathtrap_Dungeon_Verified_Backbone.json").read_text(encoding="utf-8"))
    canon = json.loads((src / "godot_project/content/dd_canon.json").read_text(encoding="utf-8"))
    zones_src = json.loads((src / "WizardRTSHybrid/wizard_rts/data/trial/legacy_zones.json").read_text(encoding="utf-8"))["zones"]
    zs = zones_src if isinstance(zones_src, list) else list(zones_src.values())
    commit = (src / ".git" / "HEAD")
    head = ""
    try:
        import subprocess
        head = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    status = canon["passage_status"]
    zone_of: dict[int, str] = {}
    for zid, (_l, pl, *_rest) in ZONES.items():
        for p in pl:
            zone_of[p] = zid
    zone_of[400] = "dd_igbut"
    passages: dict[str, dict] = {}
    for n in bb["verified_nodes"]:
        p = int(n["passage"])
        passages[str(p)] = {"zone": zone_of.get(p, ""), "status": status.get(str(p), "BOOK_VERIFIED"), "beat": n["beat"],
                            "edges": [{"action": e["action"], "to": e["to"]} for e in n["edges"]], "adaptation": n["adaptation"]}
    referenced: set[int] = set()
    for n in bb["verified_nodes"]:
        for e in n["edges"]:
            for t in (e["to"] if isinstance(e["to"], list) else [e["to"]]):
                if str(t) not in passages:
                    referenced.add(int(t))
    for p in sorted(referenced):
        passages[str(p)] = {"zone": zone_of.get(p, ""), "status": "REFERENCED", "beat": "Named as the target of a verified edge; its own text and onward links are not verified.",
                            "edges": [], "adaptation": ""}
    passages["56"].update({"beat": "Where the named box (270) and the eastern branch (119) both lead: the soft obstruction opens. Prototype endpoint of the opening.",
                           "status": "PROTOTYPE_ENDPOINT", "zone": "dd_fork"})
    passages["293"]["status"] = "BOOK_VERIFIED"
    zones = []
    for zid in ORDER:
        z = next(a for a in zs if a["id"] == zid)
        letter, pl, role, items, encs = ZONES[zid]
        exits = []
        seen = set()
        for e in z["entities"]:
            if e["kind"] == "exit":
                req = e.get("requires_run_flag") or e.get("requires") or ""
                key = (e["to_area"], req)
                if key not in seen:
                    seen.add(key)
                    exits.append({"to": e["to_area"], "requires": req})
        zones.append({"id": zid, "name": z["name"], "design_zone": letter, "role": role, "passages": pl, "items": items, "encounters": encs, "exits": exits})
    zones[-1]["exits"].append({"to": EXIT_ZONE, "requires": "the three gems in the right order (the victory door)"})
    enc_rows = list(csv.DictReader(open(src / "DD" / "Deathtrap_Major_Encounter_Adaptation.csv", encoding="utf-8-sig")))
    encounters = [{"name": r["Encounter"], "book_role": r["Book role"], "dungeon_role": r["Dungeon role"], "translation": r["Duel Master translation"]} for r in enc_rows]
    out = {
        "schema": 1,
        "title": "Deathtrap Dungeon: the whole quest",
        "status": "verified_macrograph_not_full_400_passage_adjacency",
        "start": 1,
        "victory": 400,
        "source": {"repo": "https://github.com/Joesalmon1985/DuelMasterBattle", "commit": head,
                   "files": ["DD/Deathtrap_Dungeon_Verified_Backbone.json", "godot_project/content/dd_canon.json", "WizardRTSHybrid/wizard_rts/data/trial/legacy_zones.json",
                             "DD/Deathtrap_Major_Encounter_Adaptation.csv", "docs/TRIAL_CANON_STATUS.md", "DD/Deathtrap_Dungeon_Canonical_Adaptation_Report.md"],
                   "note": "Zone membership of passages follows docs/TRIAL_CANON_STATUS.md; zone exits and their flags are the legacy zones' real exits."},
        "route": ORDER + [EXIT_ZONE],
        "route_note": "A run's order of play: the legacy adaptation's zone graph (see 'exits'). Gems may be taken in any order that the exits allow; Igbut (dd_igbut) checks all three.",
        "gems": {"emerald": {"zone": "dd_idol", "passages": bb["required_items"]["emerald"]["key_passages"], "how": "an idol's eye, after the Flying Guardians"},
                 "sapphire": {"zone": "dd_vaults", "passages": [162], "how": "a box with an iron key"},
                 "diamond": {"zone": "dd_vault_inner", "passages": bb["required_items"]["diamond"]["key_passages"], "how": "a later hall route (book); the legacy places it in the inner vault; a false diamond waits in dd_vaults (218)"},
                 "final_use": {"zone": "dd_igbut", "passages": bb["required_items"]["final_use"]["key_passages"], "how": "Igbut checks all three, then the three-position lock"}},
        "contestants": bb["contestants"],
        "encounters": encounters,
        "zones": zones,
        "passages": passages,
    }
    MAP.parent.mkdir(parents=True, exist_ok=True)
    MAP.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("wrote", MAP.relative_to(ROOT).as_posix(), f"({len(zones)} zones, {len(passages)} passages)")


def render() -> None:
    from PIL import Image, ImageDraw, ImageFont
    m = json.loads(MAP.read_text(encoding="utf-8"))
    play = set(int(k) for k in json.loads(PASSAGES.read_text(encoding="utf-8"))["passages"]) if PASSAGES.exists() else set()
    names = {z["id"]: z["name"] for z in m["zones"]}
    names.update(NAMES)
    # --- markdown
    L = ["# The whole quest: the Deathtrap Dungeon map", "",
         "Generated by `python tools/trial/make_quest_map.py render` from `content/trial/quest_map.json`. **Playable** passages are the ones in `content/trial/passages.json`; every other passage is mapped and waiting.", "",
         f"Status of the source: `{m['status']}`. The book has 400 passages; only the verified macrograph below is known edge by edge. A passage marked REFERENCED is the target of a verified edge whose own links are not verified, so none are invented. See `assets/trial/PROVENANCE.md`.", "",
         "![the map](trial_quest_map.png)", "", "## Order of play", "",
         "```mermaid", "flowchart LR"]
    for z in m["zones"]:
        L.append(f'  {z["id"]}["{z["name"]}<br/>zone {z["design_zone"]}"]')
    L.append(f'  {EXIT_ZONE}(["{NAMES[EXIT_ZONE]}"])')
    done = set()
    for z in m["zones"]:
        for e in z["exits"]:
            a, b = z["id"], e["to"]
            key = tuple(sorted((a, b))) + (e["requires"],)
            if key in done:
                continue
            done.add(key)
            lab = f'|{e["requires"]}|' if e["requires"] else ""
            L.append(f"  {a} ---{lab} {b}" if e["requires"] else f"  {a} --- {b}")
    L += ["```", "", "## Gems and the final lock", ""]
    for k, g in m["gems"].items():
        L.append(f"* **{k.replace('_', ' ')}**: {g['how']} (zone `{g['zone']}`, passages {', '.join(map(str, g['passages']))})")
    L += ["", "## Zones", "", "| Zone | Design zone | Passages | Items | Encounters | Exits (flag that opens it) |", "| --- | --- | --- | --- | --- | --- |"]
    for z in m["zones"]:
        ex = ", ".join(f"{names.get(e['to'], e['to'])}" + (f" ({e['requires']})" if e["requires"] else "") for e in z["exits"])
        pl = ", ".join(("**%d**" % p if p in play else str(p)) for p in z["passages"]) or "none verified"
        L.append(f"| {z['name']} (`{z['id']}`) | {z['design_zone']} | {pl} | {'; '.join(z['items'])} | {'; '.join(z['encounters'])} | {ex} |")
    L += ["", "## Passages", "", "Bold = playable now. Edges are the book-verified wording.", "", "| Passage | Zone | Status | Beat | Verified edges |", "| --- | --- | --- | --- | --- |"]
    for k in sorted(m["passages"], key=int):
        p = m["passages"][k]
        edges = "; ".join(f"{e['action']} → {e['to']}" for e in p["edges"]) or ("(endpoint)" if int(k) in (400,) else "not verified")
        mark = f"**{k}**" if int(k) in play else k
        L.append(f"| {mark} | {p['zone'] or '?'} | {p['status']} | {p['beat'][:150]} | {edges} |")
    L += ["", "## Contestants", ""]
    for k, c in m["contestants"].items():
        L.append(f"* **{k}**: {c.get('start', '')}" + (f"; fate: {c['known_fate']}" if c.get("known_fate") else "") + (f" (passages {', '.join(map(str, c['key_passages']))})" if c.get("key_passages") else ""))
    L += ["", "## Major encounters", "", "| Encounter | Book role | Dungeon role | Here |", "| --- | --- | --- | --- |"]
    for e in m["encounters"]:
        L.append(f"| {e['name']} | {e['book_role']} | {e['dungeon_role']} | {e['translation']} |")
    (ROOT / "docs" / "TRIAL_QUEST_MAP.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    # --- picture
    W, H, bw, bh, mx, my = 2000, 1010, 290, 240, 40, 90
    img = Image.new("RGB", (W, H), (14, 12, 28))
    d = ImageDraw.Draw(img)

    def font(sz: int):
        for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(f, sz)
            except OSError:
                continue
        return ImageFont.load_default()

    ft, fb, fs = font(24), font(17), font(15)
    d.text((mx, 22), "DEATHTRAP DUNGEON: THE WHOLE QUEST  (passage 1 to the victory, 400)", font=font(30), fill=(255, 210, 120))
    d.text((mx, 58), "bright = playable now   green = book-verified passage   grey = referenced, onward links not verified   arrows = real zone exits (dashed = needs a flag)", font=fs, fill=(170, 170, 210))

    def box(zid):
        gx, gy = GRID[zid]
        x = mx + gx * (bw + 30)
        y = my + 20 + gy * (bh + 55)
        return x, y

    for z in m["zones"]:  # edges first
        for e in z["exits"]:
            if e["to"] not in GRID or z["id"] not in GRID:
                continue
            if abs(GRID[z["id"]][0] - GRID[e["to"]][0]) + abs(GRID[z["id"]][1] - GRID[e["to"]][1]) != 1:
                continue  # links between boxes that are not neighbours are written inside the box as "to X if flag"
            ax, ay = box(z["id"])
            bx, by = box(e["to"])
            col = (255, 170, 90) if e["requires"] else (120, 120, 200)
            d.line([(ax + bw / 2, ay + bh / 2), (bx + bw / 2, by + bh / 2)], fill=col, width=4 if not e["requires"] else 3)
    for zid in GRID:
        x, y = box(zid)
        z = next((q for q in m["zones"] if q["id"] == zid), None)
        has_play = z is not None and any(p in play for p in z["passages"])
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=14, fill=(34, 30, 64) if not has_play else (46, 40, 96), outline=(255, 210, 120) if has_play else (90, 80, 160), width=3 if has_play else 2)
        if z is None:
            d.text((x + 16, y + 16), names[zid], font=ft, fill=(255, 235, 170))
            d.text((x + 16, y + 56), "the victory door opens,\nIgbut falls to Sukumvit's\ncrossbow, John reaches\ndaylight.", font=fb, fill=(220, 220, 240))
            continue
        d.text((x + 14, y + 10), f"{z['design_zone']}", font=ft, fill=(255, 210, 120))
        d.text((x + 44, y + 10), z["name"], font=ft, fill=(240, 240, 255))
        yy = y + 48
        row = []
        for p in z["passages"]:
            row.append(p)
        px = x + 14
        for p in row:
            st = m["passages"].get(str(p), {}).get("status", "REFERENCED")
            col = (255, 220, 110) if p in play else ((110, 220, 160) if st == "BOOK_VERIFIED" else (130, 130, 150))
            t = str(p)
            w = d.textlength(t, font=fb) + 14
            if px + w > x + bw - 8:
                px = x + 14
                yy += 28
            d.rounded_rectangle((px, yy, px + w, yy + 24), radius=6, fill=(20, 18, 40), outline=col, width=2)
            d.text((px + 7, yy + 2), t, font=fb, fill=col)
            px += w + 6
        if not row:
            d.text((x + 14, yy), "no passage numbers verified", font=fs, fill=(150, 150, 180))
        yy += 40
        for line in z["items"][:3]:
            d.text((x + 14, yy), "+ " + line[:32], font=fs, fill=(150, 240, 200))
            yy += 19
        for line in z["encounters"][:2]:
            d.text((x + 14, yy), "! " + line[:32], font=fs, fill=(255, 150, 130))
            yy += 19
        for e in z["exits"]:
            far = abs(GRID[zid][0] - GRID.get(e["to"], (99, 99))[0]) + abs(GRID[zid][1] - GRID.get(e["to"], (99, 99))[1]) != 1
            if far and e["to"] in GRID and yy < y + bh - 20:
                tag = "~ " + names.get(e["to"], e["to"]).split(" ")[0] + (": " + e["requires"] if e["requires"] else "")
                d.text((x + 14, yy), tag[:34], font=fs, fill=(255, 190, 110))
                yy += 19
    img.save(ROOT / "docs" / "trial_quest_map.png", optimize=True)
    print("wrote docs/TRIAL_QUEST_MAP.md and docs/trial_quest_map.png")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "build":
        build(Path(sys.argv[2]))
        render()
    elif len(sys.argv) >= 2 and sys.argv[1] == "render":
        render()
    else:
        print(__doc__)
        sys.exit(2)
