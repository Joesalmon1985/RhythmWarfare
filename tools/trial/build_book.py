"""Builds the 400-passage Deathtrap Dungeon: content/trial/book_graph.json (links, kinds, zones, tiers, defaults) and content/trial/book_text.json (short original descriptions).

    python tools/trial/build_book.py graph --pack <puca deathtrap_ff folder>      # read-only source: the owner's OCR passage pack (GlenGame feature/deathtrap-full-book)
    python tools/trial/build_book.py text  --chunks <folder of chunk_N.json>      # assemble the original descriptions written for the OCR passages
    python tools/trial/build_book.py report                                       # statuses and reachability

Honest scope. The book-verified macrograph (28 passages, content/trial/quest_map.json) is authoritative. The OCR pack (deathtrap_ff) holds a noisy transcription: 239 of its 400
passages have text, 161 are placeholders, passage numbers are sometimes misaligned and its mechanics (combat, luck tests) are patchy. Everything built from it is marked
OCR_GRAPH (unverified). Where the dungeon would otherwise dead-end or be unreachable, links are invented to keep it connected: marked BRIDGED. The "spine" below is a hand-made
chain of bridges that joins the verified fragments, in the order of the legacy adaptation's zones, into one walkable route from passage 1 to the victory 400.
Replace any of it by editing content/trial/passages.json (hand-authored passages win over the book files) or by correcting the graph and rebuilding.
"""
from __future__ import annotations

import collections
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "content" / "trial" / "book_graph.json"
TEXT = ROOT / "content" / "trial" / "book_text.json"
QMAP = ROOT / "content" / "trial" / "quest_map.json"
OVERRIDES = ROOT / "content" / "trial" / "passages.json"

ZONE_ORDER = ["dd_entrance", "dd_fork", "dd_galleries", "dd_pit", "dd_lower", "dd_trialmaster", "dd_idol", "dd_grotto", "dd_vaults", "dd_vault_inner", "dd_service",
              "dd_mirror", "dd_blood", "dd_grub", "dd_troglodytes", "dd_manticore", "dd_igbut"]
ZONE_NAME = {"dd_entrance": "the crystal entrance", "dd_fork": "the fork", "dd_galleries": "the footprint galleries", "dd_pit": "Throm's pit", "dd_lower": "the lower route",
             "dd_trialmaster": "the Trialmaster's complex", "dd_idol": "the idol cavern", "dd_grotto": "the drowned grotto", "dd_vaults": "the sapphire vaults",
             "dd_vault_inner": "the inner vault", "dd_service": "the service tunnels", "dd_mirror": "the mirror gallery", "dd_blood": "the bloodbeast's lair",
             "dd_grub": "the grub tunnels", "dd_troglodytes": "the troglodyte cavern", "dd_manticore": "the manticore's gate", "dd_igbut": "Igbut's door"}
# the hand-made spine: (from, to, why). Each is added as a BRIDGED link when `from` does not already link to `to`.
SPINE = [
    (1, 66, "verified"), (66, 293, "verified"), (293, 382, "verified"),
    (382, 222, "the riddle's answer (the legacy adaptation's: 150)"), (222, 154, "the galleries end at Throm (legacy dd_galleries to dd_pit)"),
    (154, 22, "verified"), (22, 184, "verified"), (184, 323, "verified: join Throm below"), (323, 194, "the pit ends in the lower route (legacy dd_pit to dd_lower)"),
    (63, 194, "every way through the pit reaches the lower route"), (311, 194, "same"), (149, 194, "same"),
    (194, 52, "verified"), (52, 169, "the lower route ends at the Cave Trolls (verified 169)"), (369, 169, "same"), (397, 169, "same"), (25, 169, "same"),
    (169, 288, "verified"), (288, 221, "verified"), (221, 60, "the lower route ends at the Trialmaster (legacy dd_lower to dd_trialmaster)"), (64, 60, "same"),
    (60, 365, "verified"), (365, 290, "verified"), (191, 302, "the tests end with Throm's forced duel (verified 302)"), (290, 302, "same"), (179, 302, "same"),
    (302, 379, "verified"), (379, 213, "verified"), (213, 37, "the Trialmaster's way leads to the idol cavern (legacy dd_trialmaster to dd_idol)"), (95, 37, "same"),
    (37, 351, "verified"), (351, 240, "the idol cavern: the guardians fall, the emerald comes free (verified 240)"), (239, 240, "same"), (240, 89, "verified"), (34, 281, "to the grotto (legacy dd_idol to dd_grotto)"),
    (89, 281, "same"), (281, 399, "verified"), (399, 192, "verified"), (192, 162, "to the vaults (legacy dd_grotto to dd_vaults)"),
    (162, 218, "the sapphire box leads on to the vaults' temptation (the backbone's edge 162 to 442 names a passage the 400-passage book does not have: needs a page check)"), (218, 65, "verified"), (65, 269, "the false diamond fails: on to the true one (verified 269)"), (252, 269, "same"),
    (269, 127, "verified"), (127, 6, "to the Manticore's gate (legacy dd_troglodytes to dd_manticore)"), (6, 364, "the Manticore falls: Igbut (pack 6 to 364)"),
    (364, 31, "verified"), (31, 62, "the gem check passes: the lock (verified 62)"), (62, 16, "verified: one of the six orders is the right one (ADAPTED: the legacy's)"),
    (392, 62, "a wrong order: try the lock again"), (177, 62, "same"), (287, 62, "same"), (132, 62, "same"), (249, 62, "same"), (16, 241, "the right order (ADAPTED)"), (241, 400, "verified"),
]
DEATH_NOT = {192, 399}  # the pack calls these deaths; the verified backbone says they are not
DEMO = {101}  # hand-written demo passage in the pack, not the book
ENEMIES = {"giant fly": "giant_fly", "ciant fly": "giant_fly", "manticore": "manticore", "pit fiend": "pit_fiend", "bloodbeast": "bloodbeast", "cave troll": "cave_troll",
           "minotaur": "minotaur", "skeleton": "skeleton", "ivy": "poison_ivy", "caveman": "caveman", "hobgoblin": "hobgoblin", "orc": "orc", "flying guardian": "flying_guardian",
           "scorpion": "scorpion", "dwarf": "dwarf", "goblin": "goblin", "troll": "cave_troll", "dog": "guard_dog", "grub": "rock_grub", "demon": "mirror_demon"}


ANOMALIES: list[str] = []


def load_pack(pack: Path) -> dict[int, dict]:
    out = {}
    for f in sorted(glob.glob(str(pack / "passages" / "*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        out[int(d["id"])] = d
    return out


def enemy_of(d: dict) -> dict | None:
    cb = d.get("combat") or {}
    if not cb:
        return None
    name = str(cb.get("enemy_name") or "")
    if not name and cb.get("enemies"):
        name = str(cb["enemies"][0].get("name", ""))
    hay = (name + " " + " ".join(c["label"] for c in d["choices"])).lower()
    ident = "creature"
    disp = "Creature"
    for k, v in ENEMIES.items():
        if k in hay:
            ident, disp = v, v.replace("_", " ").title()
            break
    skill = int(cb.get("enemy_skill") or cb.get("skill") or 8)
    return {"id": ident, "name": disp, "skill": max(3, min(skill, 14))}


def build_graph(pack_dir: Path) -> None:
    pack = load_pack(pack_dir)
    qm = json.loads(QMAP.read_text(encoding="utf-8"))
    verified = {int(k): v for k, v in qm["passages"].items() if v["status"] == "BOOK_VERIFIED" and 1 <= int(k) <= 400}
    zone_known = {int(k): v["zone"] for k, v in qm["passages"].items() if v["zone"] and 1 <= int(k) <= 400}
    G: dict[int, dict] = {i: {"status": "BRIDGED", "links": [], "kind": "normal", "src_pack": False} for i in range(1, 401)}

    def add(a: int, to: int, src: str, **kw) -> None:
        if not 1 <= to <= 400:
            ANOMALIES.append(f"passage {a}: a link to {to}, outside the book's 1 to 400 (source {src}); not built")
            return
        if any(l["to"] == to and "test" not in l for l in G[a]["links"]):
            return
        link = {"to": to, "src": src}
        link.update(kw)
        G[a]["links"].append(link)

    # 1. the OCR pack: real passages only (not placeholders, not the demo chain)
    for i, d in pack.items():
        if d["text"].startswith("[Passage") or i in DEMO or i in verified:
            continue
        g = G[i]
        g["status"] = "OCR_GRAPH"
        g["src_pack"] = True
        ending = d.get("ending")
        if i in DEATH_NOT and ending == "death":
            ending = None
        g["ending"] = ending
        for c in d["choices"]:
            if ending != "death" and 1 <= int(c["to"]) <= 400 and int(c["to"]) != i:
                add(i, int(c["to"]), "pack")
        g["enemy"] = enemy_of(d)
        tests = [t for t in d.get("tests", []) if t.get("type") == "luck"]
        if tests:
            t = tests[0]
            ok = t.get("success_to") or t.get("lucky_to")
            bad = t.get("failure_to") or t.get("unlucky_to")
            g["luck"] = {"pass": ok, "fail": bad}
        cb = d.get("combat") or {}
        g["win_to"] = cb.get("win_to") if cb else None
    # 2. the verified overlay: authoritative
    for i, v in verified.items():
        g = G[i]
        g["status"] = "BOOK_VERIFIED"
        g["links"] = []
        g["ending"] = None
        g["enemy"] = None
        g.pop("luck", None)
        g["win_to"] = None
        for e in v["edges"]:
            for t in (e["to"] if isinstance(e["to"], list) else [e["to"]]):
                add(i, int(t), "verified", book=e["action"])
    G[400]["status"] = "BOOK_VERIFIED"
    G[400]["links"] = []
    G[400]["ending"] = "victory"
    # known fights among the verified nodes (the legacy adaptation's)
    G[169]["enemy"] = {"id": "cave_troll", "name": "Cave Troll", "skill": 9}
    G[302]["enemy"] = {"id": "throm", "name": "Throm", "skill": 9}
    G[6]["enemy"] = {"id": "manticore", "name": "Manticore", "skill": 11}
    # 3. the spine
    for a, b, why in SPINE:
        if G[a].get("ending") in ("death", "victory"):
            continue
        add(a, b, "verified" if why == "verified" else "bridge", why=why)
    for a, b, why in SPINE:  # a spine passage that the pack called a death is not one
        if G[a].get("ending") == "death" and a in (6,):
            G[a]["ending"] = None
    # 4. zones by BFS from the start through the links (the verified ones are fixed)
    zone: dict[int, str] = dict(zone_known)
    zone[0] = "dd_igbut"

    def bfs_zones() -> None:
        q = collections.deque(sorted(zone))
        seen = set(zone)
        while q:
            n = q.popleft()
            for l in G.get(n, {}).get("links", []):
                t = l["to"]
                if t not in seen and t in G:
                    seen.add(t)
                    zone.setdefault(t, zone.get(n, "dd_entrance"))
                    q.append(t)

    bfs_zones()
    hubs = {}
    for a, b, _ in SPINE:
        hubs.setdefault(zone.get(b, "dd_entrance"), b)

    def next_hub(z: str) -> int:
        i = ZONE_ORDER.index(z) if z in ZONE_ORDER else 0
        for z2 in ZONE_ORDER[i + 1:] + ZONE_ORDER[i:i + 1]:
            if z2 in hubs:
                return hubs[z2]
        return 66

    # 5. dead ends carry on to the next hub; deaths and the victory stay
    for i, g in G.items():
        if g.get("ending") in ("death", "victory") or i == 400:
            continue
        if not g["links"]:
            add(i, next_hub(zone.get(i, "dd_entrance")) if next_hub(zone.get(i, "dd_entrance")) != i else 66, "bridge", why="dead end carried on")
    # 6. everything reachable: unreachable passages are hung off reachable ones, round the zones
    def reach() -> set[int]:
        seen = {1}
        q = [1]
        while q:
            n = q.pop()
            for l in G[n]["links"]:
                t = l["to"]
                if t not in seen:
                    seen.add(t)
                    q.append(t)
        return seen

    r = reach()
    hosts_used: collections.Counter = collections.Counter()
    for u in range(1, 401):
        r = reach()
        if u in r:
            continue
        spine_nodes = {a for a, _, _ in SPINE} | {b for _, b, _ in SPINE}
        free = [h for h in sorted(r) if G[h]["status"] != "BOOK_VERIFIED" and h not in spine_nodes]
        cands = [h for h in free if G[h].get("ending") not in ("death", "victory") and h != 400 and len(G[h]["links"]) < 4 and hosts_used[h] == 0]
        if not cands:
            cands = [h for h in free if G[h].get("ending") not in ("death", "victory") and h != 400]
        # prefer a host in a zone in the middle of the order for variety
        h = cands[(u * 7) % len(cands)]
        hosts_used[h] += 1
        add(h, u, "bridge", why="side passage hung on to keep every passage reachable", side=True)
        zone.setdefault(u, zone.get(h, "dd_entrance"))
    for k in range(1, 401):
        zone.setdefault(k, "dd_entrance")
    # zones of the passages the map does not place: by how far they are from the start along the walkable graph, so every zone of the dungeon is met in order
    dep = {1: 0}
    qq = collections.deque([1])
    while qq:
        n = qq.popleft()
        for l in G[n]["links"]:
            if l["to"] not in dep:
                dep[l["to"]] = dep[n] + 1
                qq.append(l["to"])
    top = max(dep.values()) + 1
    for k in range(1, 401):
        if k in zone_known:
            zone[k] = zone_known[k]
        else:
            zone[k] = ZONE_ORDER[min(len(ZONE_ORDER) - 1, int(dep.get(k, top - 1) / top * len(ZONE_ORDER)))]
    # 7. every passage can reach the end or a death: otherwise give it a way on
    def dist_to_end() -> dict[int, int]:
        rev = collections.defaultdict(list)
        for a, g in G.items():
            for l in g["links"]:
                if not l.get("side"):  # a side passage is a way to be reachable, never the way on
                    rev[l["to"]].append(a)
        dist = {400: 0}
        q = collections.deque([400])
        while q:
            n = q.popleft()
            for p in rev[n]:
                if p not in dist:
                    dist[p] = dist[n] + 1
                    q.append(p)
        return dist

    dist = dist_to_end()
    for i, g in G.items():
        if i not in dist and g.get("ending") != "death":
            add(i, next_hub(zone[i]) if next_hub(zone[i]) != i else 66, "bridge", why="no way on from here")
            dist = dist_to_end()
    # 8. depth from the start (for the difficulty tier) and the default choice (the shortest way to the end)
    depth = {1: 0}
    q = collections.deque([1])
    while q:
        n = q.popleft()
        for l in G[n]["links"]:
            if l["to"] not in depth:
                depth[l["to"]] = depth[n] + 1
                q.append(l["to"])
    out = {}
    for i in range(1, 401):
        g = G[i]
        links = g["links"]
        d = depth.get(i, 99)
        tier = 1 if d < 6 else (2 if d < 14 else (3 if d < 24 else 4))
        default = 0
        best = 10 ** 9
        for k, l in enumerate(links):
            if l.get("side"):
                continue
            dd = dist.get(l["to"], 10 ** 6)
            if dd < best:
                best, default = dd, k
        kind = "death" if g.get("ending") == "death" else ("victory" if i == 400 else "normal")
        entry = {"status": g["status"], "zone": zone[i], "kind": kind, "tier": tier, "depth": d, "default": default,
                 "links": [{k: v for k, v in l.items()} for l in links]}
        if g.get("enemy") and kind == "normal":
            entry["enemy"] = g["enemy"]
            entry["win_to"] = g.get("win_to")
        if g.get("luck") and kind == "normal":
            entry["luck"] = g["luck"]
        out[str(i)] = entry
    GRAPH.write_text(json.dumps({"schema": 1, "source": "owner's OCR pack deathtrap_ff (read-only), the verified backbone (content/trial/quest_map.json) and the spine in tools/trial/build_book.py",
                                 "passages": out}, indent=0, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    report()


def report() -> None:
    g = json.loads(GRAPH.read_text(encoding="utf-8"))["passages"]
    c = collections.Counter(v["status"] for v in g.values())
    k = collections.Counter(v["kind"] for v in g.values())
    srcs = collections.Counter(l["src"] for v in g.values() for l in v["links"])
    for a in ANOMALIES:
        print("ANOMALY", a)
    print("passages", len(g), "status", dict(c), "kinds", dict(k), "links by source", dict(srcs))
    fights = [i for i, v in g.items() if v.get("enemy")]
    luck = [i for i, v in g.items() if v.get("luck")]
    print("fights", len(fights), "luck tests", len(luck), "deaths", [i for i, v in g.items() if v["kind"] == "death"])
    print("zones", dict(collections.Counter(v["zone"] for v in g.values())))


HAND_TEXT = {56: {"text": "A soft, brown, boulder-like mass fills the tunnel. It gives under your hand, and you could climb over it or cut your way through.",
                  "labels": {"171": "Climb over it", "215": "Slice it open", "198": "Press on if you are still standing"}}}
TEMPLATES = {
    "dd_entrance": ["Crystal light hums in the walls and the passage runs on into the dark.", "The crystals thin out here; the tunnel narrows and drips."],
    "dd_fork": ["Footprints cross the wet floor in several directions, none of them sure.", "The way splits again, and the dust shows that others went through."],
    "dd_galleries": ["A long gallery of branching tracks, with old marks on the walls.", "Side rooms open off the gallery; someone has scratched arrows and crossed them out."],
    "dd_pit": ["The floor drops away into a deep pit and the rock is slick with damp.", "Rope marks scar the lip of the pit; a voice echoes up from below."],
    "dd_lower": ["A low tunnel below the pit, close and full of old bones.", "The roof presses down; somewhere ahead something heavy shuffles."],
    "dd_trialmaster": ["Cold stone chambers lead on, each with a door that looks too neat to be natural.", "The walls here are dressed and measured: this part was built, and is watched."],
    "dd_idol": ["A cavern of carved stone, with something large and jewelled watching from the dark.", "Gems glint high above, and the floor is littered with the bones of the careless."],
    "dd_grotto": ["Black water laps at a stone shore, and the air tastes of salt and rot.", "The grotto's pools mirror the roof; one of them moves when you do not."],
    "dd_vaults": ["Iron-bound doors line the passage, some ajar, some sealed, all promising something.", "Dust lies thick on the vault floors, except where a few footprints cross it."],
    "dd_vault_inner": ["A hush falls in the inner vault, and a thin light plays on the walls.", "Cold glitter fills the chamber; nothing here is as safe as it looks."],
    "dd_service": ["Pipes and ropes run along a narrow service tunnel built for those who run the Trial.", "Wicker, rope and rusted iron: the working side of the dungeon."],
    "dd_mirror": ["Tall mirrors line the walls and show you a crowd that is not there.", "Your reflection is a half-beat late; the gallery waits for you to make a mistake."],
    "dd_blood": ["A red-stained cavern, wet underfoot, with a smell of copper.", "The air is warm and heavy here, and the pool in the floor is not water."],
    "dd_grub": ["A tight tunnel, hot and dry, scraped smooth by something that digs.", "Loose rock, a heavy boulder and a chest that looks too easily reached."],
    "dd_troglodytes": ["Smoke and drumming drift from a cavern where a tribe makes its camp.", "Firelight and watchful shapes: this cave is somebody's home."],
    "dd_manticore": ["Great pillars rise in a hall where something large paces just out of sight.", "Gouged stone and old spikes: the last great guardian is near."],
    "dd_igbut": ["A cold hall before a great door with three sockets, and a small figure waiting beside it.", "The final door looms, and the air smells of old iron and patience."],
}


def build_text(chunks: Path) -> None:
    pack_path = Path(sys.argv[sys.argv.index("--pack") + 1]) if "--pack" in sys.argv else None
    src = load_pack(pack_path) if pack_path else {}
    qm = json.loads(QMAP.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))["passages"]
    agent: dict[int, dict] = {}
    for f in sorted(glob.glob(str(chunks / "chunk_*.json"))):
        for item in json.loads(Path(f).read_text(encoding="utf-8")):
            agent[int(item["id"])] = item

    def words(s: str) -> list[str]:
        return re.findall(r"[a-z']+", s.lower())

    def overlap(a: str, b: str, n: int = 5) -> bool:
        wa, wb = words(a), words(b)
        grams = {tuple(wb[i:i + n]) for i in range(len(wb) - n + 1)}
        return any(tuple(wa[i:i + n]) in grams for i in range(len(wa) - n + 1))

    out = {}
    rejected = 0
    for i in range(1, 401):
        g = graph[str(i)]
        text, labels, how = "", {}, "template"
        if g["status"] == "BOOK_VERIFIED" and qm["passages"][str(i)]["status"] == "BOOK_VERIFIED":
            text, how = qm["passages"][str(i)]["beat"], "verified beat (the owner's backbone)"
        a = agent.get(i)
        if a and not a.get("garbled") and a.get("text"):
            s = src[i]["text"] if i in src else ""
            if s and overlap(a["text"], s):
                rejected += 1
            else:
                text, how = a["text"], "original summary of the OCR pack passage"
        if a:
            ocr_choices = [c for c in src[i]["choices"]] if i in src else []
            for k, lab in enumerate(a.get("labels", [])):
                if k < len(ocr_choices):
                    labels[str(ocr_choices[k]["to"])] = lab
        if i in HAND_TEXT:
            text, labels, how = HAND_TEXT[i]["text"], HAND_TEXT[i]["labels"], "written for this game"
        if not text:
            zn = g["zone"]
            variants = TEMPLATES.get(zn, ["The tunnel runs on."])
            text = variants[i % len(variants)]
            if g["kind"] == "death":
                text = "Something goes badly wrong in the dark, and your adventure ends here."
            elif g.get("enemy"):
                text += " A " + g["enemy"]["name"].lower() + " bars the way."
            elif g.get("luck"):
                text += " Whatever happens next is a matter of luck."
            how = "placeholder (zone template)"
        out[str(i)] = {"text": text, "labels": labels, "how": how}
    TEXT.write_text(json.dumps({"schema": 1, "note": "Short original descriptions. 'how' says where each came from; an empty text means the loader writes a placeholder for the zone.", "passages": out},
                               indent=0, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    have = sum(1 for v in out.values() if v["text"])
    print(f"text for {have} of 400 passages; {rejected} agent texts rejected for copying 5-word runs of the source; {len(agent)} agent entries read")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "graph" and sys.argv[2] == "--pack":
        build_graph(Path(sys.argv[3]))
    elif len(sys.argv) >= 4 and sys.argv[1] == "text" and sys.argv[2] == "--chunks":
        build_text(Path(sys.argv[3]))
    elif sys.argv[1:2] == ["report"]:
        report()
    else:
        print(__doc__)
        sys.exit(2)
