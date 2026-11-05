"""The Ember Road's people (docs/THREE_PATHS_AND_FACES_PLAN.md 6.3): hand-spun wool and leather in the Hollow, white with birch-leaf embroidery in the Birch Hall,
a grey hooded cloak and a plain sword for the Warden, a gaunt grey barefoot Hollow One with wide pale eyes, riders faceless in ash-grey hoods with a red glint.
No pointed ears, no wizard hats or staves, no ring, no eye, nothing from a published book or film.

`dress(r, kind, actor)` is called by wardrobe.dress for the chapters in wardrobe.PATH_WARDROBES; `kind` is the actor's `kind` (an archetype of the plan 6.3 list, or `grandmother`).
It returns the spec people.py draws (see wardrobe.raver for the fields); wardrobe.dress adds the colours every spec needs, the face detail and the seed.
"""
from __future__ import annotations

import random

from . import wardrobe as W

# wool, leather and field colours of the Hollow (greens, harvest gold, rust, undyed cream, brown)
WOOL = ["#7a8a4a", "#5a7a4a", "#c8a050", "#d8c690", "#a8784a", "#8a5a3a", "#b0603a", "#e0d8bc", "#6a7a6a", "#9a8a5a", "#4a6a4a", "#c8b070"]
LEATHER = ["#4a3220", "#5a3c26", "#3a2a1c", "#6a4a2c", "#2e2418"]
BIRCH = ["#f0f0ec", "#e4e8ee", "#d4dce6", "#c8d0dc", "#fafafa", "#b8c4d4"]
SILVER = ["#c0c8d4", "#a8b4c4", "#e0e4ec", "#9aa8bc"]
ASH = ["#6a6a6e", "#58585c", "#7a7a7e", "#48484c", "#868688"]
GREY_CLOAK = ["#6e7278", "#5e6268", "#7a7e84"]
BRONZE = ["#8a5a2a", "#a87a3a", "#6a4a24"]
FOLK_HAIR = ["#2a1c18", "#3b281e", "#523422", "#6e4426", "#8a5a30", "#b07a3e", "#d2a55a", "#c9c3bd"]
HOLLOW_SKIN = ["#f0c7a6", "#e8b48e", "#dca07a", "#c98c62", "#b8784f", "#a3653f", "#8d5434"]


def _col(r, pool):
    return r.choice(pool)


def dress(r: random.Random, kind: str, actor: dict) -> dict:
    fn = KINDS.get(kind)
    if fn is None:
        raise ValueError(f"ember wardrobe: unknown kind {kind!r} for {actor.get('id')}")
    spec = fn(r, actor)
    spec.setdefault("species", None)
    if not spec["species"]:
        spec.pop("species")
    return spec


def _hair(r, styles, old=False):
    hc = r.choice(["#d8d4cf", "#ece8e2", "#b8b4b0", "#c9c3bd"]) if old else r.choice(FOLK_HAIR)
    return {"style": r.choice(styles), "part": round(r.uniform(-0.3, 0.3), 2), "len": round(r.uniform(0.85, 1.15), 2)}, hc


def villager_hollow(r, actor):
    """A person of the orchard village: wool jerkin or smock, leather belt, bare or booted feet. Everyone knits and nobody wears a hat bigger than a cap."""
    old = bool(actor.get("old"))
    curve = r.random()
    hair, hc = _hair(r, ["short", "bun", "braids", "ponytail", "wavy", "bob", "curly", "buzz"], old)
    c1, c2 = W._two(r, WOOL)
    top_kind = r.choice(["tunic", "longsleeve", "jumper", "shirt"])
    top = {"kind": top_kind, "pattern": r.choice(["plain", "plain", "stripes", "band", "check"]), "neck": "crew"}
    outer = {"kind": r.choice(["gilet", "gilet", "cardigan"])} if r.random() < 0.55 else None
    bottom = {"kind": r.choice(["trousers", "skirt", "baggy"] if curve > 0.45 else ["trousers", "baggy", "trousers"])}
    if bottom["kind"] == "skirt":
        bottom["len"] = r.uniform(0.75, 0.97)
    if old:
        outer = {"kind": "cardigan"}
        bottom = {"kind": "skirt", "len": 0.97}
    hat = {"kind": r.choice(["scarf", "beanie", "bucket"])} if r.random() < 0.25 else None
    skin = r.choice(HOLLOW_SKIN)
    spec = W._build(r, height=(0.9, 1.05) if not old else (0.86, 0.94), curve=curve)
    leather = _col(r, LEATHER)
    cols = {"skin": skin, "hair": hc, "hair2": W._lighter(hc, 0.25), "top": c1, "top2": c2, "top3": W._lighter(c1, 0.3), "outer": _col(r, WOOL), "outer2": W._darker(c2, 0.2),
            "bottom": _col(r, LEATHER + ["#5a5240", "#6a5a3a", "#4a4a3a"]), "bottom2": W._darker(leather, 0.2), "shoes": leather, "shoes2": "#8a7a5a", "hat": _col(r, WOOL), "hat2": leather,
            "acc": leather, "acc2": "#c8a050"}
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "shoes": {"kind": r.choice(["boots", "boots", "bare", "clogs"])}, "hat": hat,
                 "acc": [a for a, p in (("belt", 0.7), ("bracelet", 0.15), ("strap", 0.2)) if r.random() < p], "face": W._face(r, 0.18 if curve < 0.5 else 0.0), "colours": cols})
    return spec


def grandmother(r, actor):
    actor = dict(actor, old=True)
    spec = villager_hollow(r, actor)
    spec["colours"]["hair"] = "#e4e0da"
    spec["colours"]["hair2"] = "#f2eee8"
    spec["hair"] = {"style": "bun", "part": 0.1, "len": 1.0}
    spec["hat"] = None
    spec["face"] = {"eyes": "open"}
    spec["curve"] = 0.7
    return spec


def bram(r, actor):
    """Bram the gardener: broad, kind, a mud-coloured jerkin, rolled sleeves, a straw-coloured hat, a gardener's apron."""
    spec = W._build(r, height=(0.98, 1.0), width=(1.15, 1.2), curve=0.1)
    cols = {"skin": "#d8a070", "hair": "#8a5a30", "hair2": "#b07a3e", "top": "#9a8a58", "top2": "#7a6a42", "top3": "#b8a874", "outer": "#6a7a3a", "outer2": "#4a5a28",
            "bottom": "#5a4a30", "bottom2": "#3a2c1c", "shoes": "#4a3220", "shoes2": "#8a7a5a", "hat": "#d8c070", "hat2": "#9a8040", "acc": "#4a3220", "acc2": "#c8a050"}
    spec.update({"hair": {"style": "wavy", "part": 0.1, "len": 0.9}, "top": {"kind": "shirt", "pattern": "plain", "neck": "collar"}, "outer": {"kind": "gilet"}, "bottom": {"kind": "dungarees"},
                 "shoes": {"kind": "boots"}, "hat": {"kind": "bucket"}, "acc": ["belt"], "face": {"eyes": "open", "beard": "stubble", "freckles": True}, "colours": cols})
    return spec


def warden(r, actor):
    """The Warden: a ranger in a grey hooded cloak, a plain sword at the belt, weathered, lean."""
    spec = W._build(r, height=(1.04, 1.06), width=(0.95, 0.98), curve=0.1)
    g = _col(r, GREY_CLOAK)
    cols = {"skin": "#c4966a", "hair": "#3b281e", "hair2": "#523422", "top": "#4a5048", "top2": "#3a4038", "top3": "#6a7068", "outer": g, "outer2": W._darker(g, 0.25), "bottom": "#3a3c3a",
            "bottom2": "#2a2c2a", "shoes": "#2e2418", "shoes2": "#4a3a28", "hat": g, "hat2": W._darker(g, 0.35), "acc": "#4a3220", "acc2": "#a8aab0"}
    spec.update({"hair": {"style": "short", "part": 0.0, "len": 0.8}, "top": {"kind": "longsleeve", "pattern": "plain", "neck": "crew"}, "outer": {"kind": "cape"},
                 "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"}, "hat": {"kind": "hood"}, "acc": ["belt", "strap"], "face": {"eyes": "open", "beard": "stubble"}, "colours": cols})
    return spec


def lady(r, actor):
    """The Lady of the Birch Hall: white, long, a silver circlet, birch-leaf embroidery (a band of silver on the white)."""
    spec = W._build(r, height=(1.04, 1.06), width=(0.9, 0.94), curve=0.85)
    cols = {"skin": "#f0d8c4", "hair": "#d8d4cf", "hair2": "#ece8e2", "top": "#f4f4f0", "top2": "#b8c4d4", "top3": "#ffffff", "outer": "#e8ecf2", "outer2": "#a8b4c4", "bottom": "#f4f4f0",
            "bottom2": "#d4dce6", "shoes": "#c8d0dc", "shoes2": "#a8b4c4", "hat": "#c0c8d4", "hat2": "#e0e4ec", "acc": "#c0c8d4", "acc2": "#e8f0ff"}
    spec.update({"hair": {"style": "long", "part": 0.0, "len": 1.2}, "top": {"kind": "robe", "pattern": "band", "neck": "v"}, "outer": {"kind": "cape"}, "bottom": {"kind": "skirt", "len": 1.0},
                 "shoes": {"kind": "slippers"}, "hat": {"kind": "crown"}, "acc": ["sash"], "face": {"eyes": "open"}, "colours": cols})
    return spec


def birch_folk(r, actor):
    """The hall's people: white and silver wool robes with a pale-blue sash, hair worn long or braided."""
    curve = r.random()
    hair, hc = _hair(r, ["long", "braids", "bun", "wavy", "bob", "ponytail", "short"])
    w1, w2 = W._two(r, BIRCH)
    spec = W._build(r, height=(0.94, 1.08), curve=curve)
    cols = {"skin": r.choice(W.SKINS[:6]), "hair": hc, "hair2": W._lighter(hc, 0.25), "top": w1, "top2": _col(r, SILVER), "top3": W._lighter(w1, 0.3), "outer": w2, "outer2": _col(r, SILVER),
            "bottom": w2, "bottom2": W._darker(w2, 0.2), "shoes": "#c8d0dc", "shoes2": "#a8b4c4", "hat": _col(r, SILVER), "hat2": "#e0e4ec", "acc": _col(r, SILVER), "acc2": "#dfe8f8"}
    spec.update({"hair": hair, "top": {"kind": r.choice(["robe", "tunic", "robe"]), "pattern": r.choice(["band", "plain", "vstripes"]), "neck": "v"}, "outer": {"kind": "cape"} if r.random() < 0.3 else None,
                 "bottom": {"kind": r.choice(["trousers", "skirt"]), "len": 0.95}, "shoes": {"kind": r.choice(["slippers", "boots"])}, "hat": None, "acc": ["sash"] if r.random() < 0.7 else [],
                 "face": W._face(r, 0.1 if curve < 0.4 else 0.0), "colours": cols})
    return spec


def innkeeper(r, actor):
    """The innkeeper: round, an apron over a wool shirt, rolled sleeves, a ledger under the arm (the clipboard)."""
    spec = W._build(r, height=(0.96, 0.98), width=(1.25, 1.3), curve=0.4)
    cols = {"skin": "#e0a880", "hair": "#5a3a22", "hair2": "#8a5a30", "top": "#e0d8bc", "top2": "#b0a078", "top3": "#f0ead0", "outer": "#b8a890", "outer2": "#8a7a60", "bottom": "#4a3c2c",
            "bottom2": "#2e2418", "shoes": "#3a2a1c", "shoes2": "#6a5a3a", "hat": "#e0d8bc", "hat2": "#b0a078", "acc": "#4a3220", "acc2": "#c8a050"}
    spec.update({"hair": {"style": "short", "part": 0.2, "len": 0.8}, "top": {"kind": "shirt", "pattern": "plain", "neck": "collar"}, "outer": {"kind": "gilet"}, "bottom": {"kind": "trousers"},
                 "shoes": {"kind": "boots"}, "hat": None, "acc": ["belt"], "face": {"eyes": "open", "beard": "moustache"}, "colours": cols})
    spec["outer"] = {"kind": "coat", "long": False}
    return spec


def drinker(r, actor):
    spec = villager_hollow(r, actor)
    spec["acc"] = [a for a in spec["acc"] if a != "bracelet"] + (["strap"] if r.random() < 0.3 else [])
    spec["face"]["blush"] = r.random() < 0.5
    return spec


def hollow_one(r, actor):
    """The Hollow One: a gaunt former carrier, grey-skinned, barefoot, wrapped in rags, with wide pale eyes (the greys' big-eye rule)."""
    spec = W._build(r, height=(0.9, 0.92), width=(0.74, 0.76), curve=0.2)
    skin = "#a8b0b4"
    cols = {"skin": skin, "skin2": W._darker(skin, 0.25), "hair": "#8a8a8c", "hair2": "#a8a8aa", "top": "#6a6258", "top2": "#4a4238", "top3": "#8a8070", "outer": "#58524a", "outer2": "#3a362e",
            "bottom": "#52483c", "bottom2": "#38322a", "shoes": skin, "shoes2": W._darker(skin, 0.3), "hat": "#58524a", "hat2": "#3a362e", "acc": "#4a4238", "acc2": "#a8a090", "eye_d": "#06040e",
            "extra": W._darker(skin, 0.35), "eye_w": "#e8f0f0"}
    spec.update({"species": {"kind": "grey", "head_h": 1.3, "head_w": 1.42}, "hair": {"style": "none"}, "top": {"kind": "tunic", "pattern": "plain", "neck": "crew"}, "outer": {"kind": "cape"},
                 "bottom": {"kind": "trousers"}, "shoes": {"kind": "bare"}, "hat": None, "acc": ["sash"], "face": {"eyes": "open"}, "colours": cols})
    return spec


def rider(r, actor):
    """An Ashen Rider: tall, an ash-grey cloak and a hood with nothing in it but a red glint, black gloves and a black belt."""
    spec = W._build(r, height=(1.08, 1.14), width=(0.95, 1.1), curve=0.0)
    g = _col(r, ASH)
    cols = {"skin": "#3a3a3e", "hair": "#2a2a2e", "hair2": "#3a3a3e", "top": W._darker(g, 0.3), "top2": "#2a2a2e", "top3": g, "outer": g, "outer2": W._darker(g, 0.3), "bottom": "#2e2e32",
            "bottom2": "#1e1e22", "shoes": "#1e1e22", "shoes2": "#3a3a3e", "hat": g, "hat2": "#161618", "acc": "#1e1e22", "acc2": "#e03a2a"}
    spec.update({"hair": {"style": "none"}, "top": {"kind": "longsleeve", "pattern": "plain", "neck": "crew"}, "outer": {"kind": "cape"}, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"},
                 "hat": {"kind": "hood", "blank": "dark"}, "acc": ["belt"], "face": {"eyes": "open"}, "colours": cols})
    return spec


def captain(r, actor):
    """The riders' captain: the same ash-grey, taller, with a broad dark pauldron cape, bronze trim and a red glint brighter than the rest."""
    spec = rider(r, actor)
    spec.update(height=1.2, width=1.18)
    spec["colours"].update(outer="#4a4a50", outer2="#2a2a2e", acc="#8a5a2a", acc2="#ff5a3a")
    spec["acc"] = ["belt", "plates"]
    return spec


def sentinel(r, actor):
    """The blind sentinel of the Stair of Bells: bronze-green robed, a hood over a pale blank face with no eyes."""
    spec = W._build(r, height=(1.16, 1.18), width=(1.1, 1.15), curve=0.0)
    cols = {"skin": "#c8c0b0", "hair": "#58584c", "hair2": "#6a6a5c", "top": "#5a6a58", "top2": "#3a4a3a", "top3": "#7a8a72", "outer": "#6a7a62", "outer2": "#46564a", "bottom": "#4a5a48",
            "bottom2": "#34402e", "shoes": "#2a2a22", "shoes2": "#4a4a3a", "hat": "#6a7a62", "hat2": "#3a4a3a", "acc": "#8a5a2a", "acc2": "#a87a3a"}
    spec.update({"hair": {"style": "none"}, "top": {"kind": "robe", "pattern": "plain", "neck": "v"}, "outer": {"kind": "cape"}, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"},
                 "hat": {"kind": "hood", "blank": "skin"}, "acc": ["sash"], "face": {"eyes": "closed"}, "colours": cols})
    return spec


KINDS = {"villager_hollow": villager_hollow, "grandmother": grandmother, "bram": bram, "warden": warden, "lady": lady, "birch_folk": birch_folk, "innkeeper": innkeeper, "drinker": drinker,
         "hollow_one": hollow_one, "rider": rider, "sentinel": sentinel, "captain": captain}
