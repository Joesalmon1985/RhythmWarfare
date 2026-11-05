"""The wardrobe: every Story Campaign actor dressed as an individual from their seed (docs/STORY_25D_ART_DIRECTION.md 2.E).

`cast_chapter(chapter, actors)` returns {actor id: spec} for people.py: build (height, width, curve), skin, hair (style and colours), face (eyes, beard,
glasses, freckles), clothes (top with its pattern or print, an outer layer, bottoms, shoes, hat) and accessories, each colour drawn from the chapter's
wardrobe palette. The actor's archetype keeps who they are in the story (a nurse is in scrubs, the grey examiner is a grey, the chef wears whites); everything
else comes from the seed. Rule: no two actors in one room (`view`) share build, hair and top; a clash re-rolls deterministically.
Ravers who came along to another chapter (`art: night_one`) keep the ravers' wardrobe. Original designs; no reference is copied.
"""
from __future__ import annotations

import random
import zlib

SKINS = ["#f6d8c2", "#f0c7a6", "#e8b48e", "#dca07a", "#c98c62", "#b8784f", "#a3653f", "#8d5434", "#76432a", "#5f3522", "#4c2a1c"]
HAIR_NATURAL = ["#1b1416", "#2a1c18", "#3b281e", "#523422", "#6e4426", "#8a5a30", "#b07a3e", "#d2a55a", "#e6c47e", "#a83c22", "#c9c3bd", "#ece8e2"]
HAIR_DYED = ["#e0457f", "#2fb5c8", "#7a4cff", "#f4d23a", "#3ad08a", "#ff7a3a"]

# Night One: a 90s warehouse rave. Muted wardrobe colours with saturated accents, in the chapter's amber and magenta.
RAVE = ["#e8e2d0", "#f2efe6", "#2a6a6e", "#1f4f5a", "#c8902a", "#e0b040", "#7a2a3a", "#9a3040", "#3a5a9a", "#5a7ab8", "#6a3a8a", "#9a5ab0", "#c0402a",
        "#d86a2a", "#2a3a2a", "#3a6a3a", "#e05a8a", "#2a2a36", "#4a3a5a", "#d8c8a0", "#b84a6a", "#3aa0a0"]
DENIM = ["#5a7ab0", "#4a6aa0", "#7a9ac8", "#3a4a78", "#8aa8d0", "#2e3656"]
DARKS = ["#2a2a36", "#3a3040", "#2e3a40", "#40363a", "#1e2230", "#4a4048"]
SHOE = ["#ecebe6", "#d8d4cc", "#2a2428", "#6a4a32", "#c03a3a", "#3a5aa0", "#e8c040"]

# The Mothership: cold cyan and silver suits, violet and gold trims, glowing badges.
SPACE = ["#9ad8e0", "#5ab8c8", "#2a8a9a", "#c8d4e8", "#a8b4d0", "#6a5ac8", "#9a7ae0", "#e8c860", "#3a4a6a", "#2a3050", "#e0e8f0", "#4ad0b0"]
ALIEN_SKIN = {"grey": ["#b8c4d0", "#a8b8c0", "#c0c8b8", "#9aa8b8", "#b0b8c8"], "antenna": ["#8fe07a", "#ff8fc4", "#7ad0a0", "#c0e070", "#ffa0a0"],
              "blob": ["#6af0a0", "#d070ff", "#70c8ff", "#ffb070", "#a0f0e0"], "insect": ["#a6d94a", "#ffb23f", "#80c060", "#d0b040", "#70b0a0"],
              "cyclops": ["#ff9a4a", "#a77aff", "#ffc06a", "#e07ab0", "#7ab0ff"], "tentacle": ["#c07aff", "#33d6c0", "#ff7aa0", "#7ae0ff", "#b0a0ff"]}

# The Underworld: red and black, ember orange, bone and brass.
HELL = ["#2a1018", "#3a1420", "#1a0a12", "#6a1a20", "#8a2a1a", "#c04a1a", "#e07a2a", "#d8b060", "#4a2a3a", "#5a3a2a", "#2a2a30", "#a03050"]
DEMON_SKIN = {"imp": ["#d84a3a", "#9a5cff", "#e06a4a", "#c03a5a", "#ff7a5a"], "brute": ["#a82a3c", "#4f74c4", "#6a2a2a", "#8a4a3a", "#3a5a7a"],
              "fiend": ["#8d3fd0", "#cdb4ff", "#6a2a8a", "#b05ac0", "#3a2a5a"], "skeleton": ["#e8e0c8", "#d6e0d8", "#f0e8d0", "#dcd2b4", "#e0e4dc"],
              "flame": ["#ff7a1a", "#ff5a1a", "#e06a20", "#5a6cff", "#ff9a2a"], "horned_queen": ["#c83a7a", "#e9d4ff", "#a02a5a", "#d05a8a", "#8a3aa0"]}

# The Hospital: night blue with warm visitors' coats; scrubs and white coats.
VISIT = ["#8a3a3a", "#c8604a", "#3a5a8a", "#5a7a9a", "#6a8a5a", "#c89a4a", "#8a6a9a", "#e8d8c0", "#4a4a5a", "#a87a5a", "#3a6a6a", "#d0a0a0", "#7a4a6a"]
SCRUBS = ["#2fa5a0", "#3a6ab0", "#2a3a6a", "#b05a8a", "#8a7ac8", "#3a8a6a"]
GOWN = ["#a8c8e0", "#b8d8d0", "#c8d0e8"]

# The Ward: grim institutional green; the residents' homemade fancy dress is the warmth.
WARD_STAFF = ["#4a6a4a", "#3a5a48", "#5a7a52", "#40604a"]
COSTUME = ["#c03a3a", "#e0b040", "#3a6ab0", "#7a3c9a", "#f0e8d8", "#2a2a3a", "#e07a9a", "#3a8a5a", "#e0703a", "#5a4a8a", "#a8d0e8", "#f2c0d0"]

MOTIFS = ["smiley", "sun", "star", "rings", "heart", "bolt", "diamond", "flower"]


def seed_of(chapter: str, aid: str) -> int:
    return zlib.crc32(f"{chapter}/{aid}".encode()) & 0x7FFFFFFF


def _base(r: random.Random, colours: dict) -> dict:
    """The colours every spec needs (eyes, mouth, props, furniture), around the person's own."""
    c = {"eye_w": "#ece6e0", "eye_d": "#1c1220", "mouth": "#7a2a34", "teeth": "#f2eee6", "liquid": "#e2a23a", "glass": "#d6e4ec", "metal": "#a4acbc",
         "lit": "#d8faff", "furn": "#4a3e4c", "furn2": "#2e2634", "prop": r.choice(["#c04050", "#3a6ab0", "#e0b040", "#3a8a5a"]), "prop2": "#f2eee2",
         "horn": "#e8dcc0", "extra": "#5a6070", "skin2": "#d07868", "acc": "#2a2430", "acc2": "#d8b048", "hat": "#2a3a6a", "hat2": "#1a2440",
         "outer": "#3a3a4a", "outer2": "#2a2a36", "top3": "#d8d0c4", "bottom2": "#2a2a36", "shoes2": "#8a8890", "hair2": "#4a3a30"}
    c.update(colours)
    return c


def _hair_colours(r: random.Random, dyed=0.12, old=False):
    if old:
        h = r.choice(["#d8d4cf", "#ece8e2", "#b8b4b0", "#c9c3bd"])
    elif r.random() < dyed:
        h = r.choice(HAIR_DYED)
    else:
        h = r.choice(HAIR_NATURAL[:10])
    return h


def _lighter(hexc: str, k: float) -> str:
    v = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{min(255, int(x + (255 - x) * k)):02x}" for x in v)


def _darker(hexc: str, k: float) -> str:
    v = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(x * (1 - k)):02x}" for x in v)


def _two(r: random.Random, pool: list):
    a = r.choice(pool)
    b = r.choice([c for c in pool if c != a])
    return a, b


def _build(r: random.Random, height=(0.92, 1.08), width=(0.86, 1.18), curve=None):
    return {"height": round(r.uniform(*height), 3), "width": round(r.uniform(*width), 3),
            "curve": round(r.random() if curve is None else curve, 2)}


def _face(r: random.Random, beard=0.25):
    f = {"eyes": r.choice(["open", "open", "lost", "lost", "closed"]) if r.random() < 0.8 else "open"}
    if r.random() < beard:
        f["beard"] = r.choice(["stubble", "beard", "moustache", "stubble"])
    if r.random() < 0.14:
        f["glasses"] = r.choice(["round", "square", "shades"])
    if r.random() < 0.18:
        f["freckles"] = True
    if r.random() < 0.2:
        f["blush"] = True
    return f


# ---- the ravers (Night One, and the friends who come along) ------------------------------------------------------------------------------------------

RAVE_HAIR = ["short", "curly", "afro", "locs", "braids", "long", "bun", "buzz", "ponytail", "bob", "wavy", "spiky", "quiff", "mohawk", "shaved"]
RAVE_TOPS = ["tee", "tee", "tank", "crop", "longsleeve", "jumper", "hoodie", "shirt", "polo"]


def raver(r: random.Random, arch: str) -> dict:
    curve = r.random()
    hair = r.choice(RAVE_HAIR)
    hair = {"curly": r.choice(["curly", "afro", "curly_long"]), "ponytail": r.choice(["ponytail", "long", "bun"]), "bob": r.choice(["bob", "wavy"]),
            "punk": r.choice(["mohawk", "spiky", "shaved"]), "hoodie": hair, "groover": hair}.get(arch, hair)
    top_kind = {"hoodie": "hoodie"}.get(arch) if r.random() < 0.6 else None
    top_kind = top_kind or r.choice(RAVE_TOPS)
    if top_kind == "crop" and curve < 0.4:
        top_kind = "tank"
    c1, c2 = _two(r, RAVE)
    pattern = r.choice(["plain", "print", "print", "stripes", "band", "check", "tiedye", "dots", "plain"])
    if top_kind in ("shirt",):
        pattern = r.choice(["check", "plain", "vstripes"])
    if top_kind in ("jumper",):
        pattern = r.choice(["stripes", "band", "plain", "print"])
    top = {"kind": top_kind, "pattern": pattern, "motif": r.choice(MOTIFS), "neck": "crew" if top_kind in ("tee", "jumper", "longsleeve") else
           ("collar" if top_kind in ("shirt", "polo") else ("scoop" if top_kind in ("crop", "tank") else "crew")), "back_print": r.random() < 0.4}
    outer = None
    if top_kind in ("tee", "tank", "longsleeve") and r.random() < 0.28:
        outer = {"kind": r.choice(["overshirt", "jacket", "overshirt", "gilet"]), "pattern": r.choice(["check", "plain"])}
    bottom = {"kind": r.choice(["jeans", "baggy", "baggy", "trousers", "dungarees", "skirt", "shorts", "flares"])}
    if bottom["kind"] == "skirt":
        bottom["tights"] = r.random() < 0.4
        bottom["len"] = r.uniform(0.6, 0.95)
    bcol = r.choice(DENIM) if bottom["kind"] in ("jeans", "dungarees", "flares") or r.random() < 0.3 else r.choice(RAVE + DARKS)
    hat = None
    if r.random() < 0.32:
        hat = {"kind": r.choice(["cap", "cap_back", "bucket", "bucket", "beanie"]), "pom": r.random() < 0.3}
    acc = [a for a, p in (("strap", 0.3), ("bracelet", 0.35), ("necklace", 0.25), ("phones_neck", 0.1), ("watch", 0.2), ("belt", 0.2),
                          ("scarf", 0.05)) if r.random() < p]
    hc = _hair_colours(r, 0.18)
    oc1, oc2 = _two(r, RAVE)
    hb = r.choice(RAVE + DARKS)
    cols = {"skin": r.choice(SKINS), "hair": hc, "hair2": _lighter(hc, 0.25), "top": c1, "top2": c2, "top3": _lighter(c1, 0.35),
            "outer": oc1, "outer2": oc2, "bottom": bcol, "bottom2": _darker(bcol, 0.3) if bottom["kind"] != "skirt" else r.choice(DARKS),
            "shoes": r.choice(SHOE), "shoes2": r.choice(["#f2f0ea", "#3a3238", "#c8c4bc"]), "hat": hb, "hat2": _darker(hb, 0.35),
            "acc": r.choice(["#2a2430", "#6a4a32", "#c03a5a", "#3a5a9a"]), "acc2": r.choice(["#e0b848", "#c8d0d8", "#e05a8a"])}
    spec = _build(r, curve=curve)
    spec.update({"hair": {"style": hair, "part": round(r.uniform(-0.3, 0.3), 2), "len": round(r.uniform(0.8, 1.15), 2)}, "top": top, "outer": outer,
                 "bottom": bottom, "shoes": {"kind": r.choice(["trainers", "trainers", "trainers", "boots"])}, "hat": hat, "acc": acc,
                 "face": _face(r, 0.35 * (1 - curve)), "colours": cols})
    return spec


# ---- the Mothership's aliens -----------------------------------------------------------------------------------------------------------------------

def alien(r: random.Random, arch: str) -> dict:
    skin = r.choice(ALIEN_SKIN[arch])
    spec = _build(r)
    sp = {"kind": arch}
    hair = {"style": "none"}
    if arch == "grey":
        sp.update(head_h=1.32, head_w=1.5)
        spec.update(width=round(r.uniform(0.78, 0.95), 3), height=round(r.uniform(0.86, 1.0), 3))
        if r.random() < 0.3:
            sp["antennae"] = True
    elif arch == "antenna":
        sp["antennae"] = True
        spec.update(height=round(r.uniform(1.02, 1.12), 3), width=round(r.uniform(0.8, 0.95), 3))
        hair = {"style": r.choice(["none", "mohawk", "spiky", "short"])}
    elif arch == "blob":
        sp.update(head_w=1.3)
        spec.update(width=round(r.uniform(1.3, 1.5), 3), height=round(r.uniform(0.82, 0.94), 3), legs=0.62, neck=0.3)
    elif arch == "insect":
        sp.update(head_w=0.88, head_h=1.05, arm_len=1.08)
        sp["antennae"] = True
        spec.update(width=round(r.uniform(0.75, 0.88), 3), height=round(r.uniform(1.0, 1.1), 3), limb=0.72)
    elif arch == "cyclops":
        sp.update(head_w=1.2, head_h=1.1)
        spec.update(width=round(r.uniform(1.1, 1.3), 3))
        if r.random() < 0.5:
            sp["horns"] = "small"
        hair = {"style": r.choice(["none", "short", "curly", "spiky"])}
    elif arch == "tentacle":
        hair = {"style": "tentacles", "len": round(r.uniform(0.8, 1.2), 2)}
    c1, c2 = _two(r, SPACE)
    kind = r.choice(["jumpsuit", "jumpsuit", "tunic", "tee", "vest", "longsleeve"])
    top = {"kind": kind, "pattern": r.choice(["plain", "emblem", "band", "plain", "vstripes"]), "motif": r.choice(["star", "diamond", "rings", "bolt"]),
           "neck": r.choice(["collar", "crew", "v"])}
    bottom = {"kind": r.choice(["trousers", "leggings", "trousers", "baggy"])}
    outer = {"kind": "cape"} if r.random() < 0.12 else ({"kind": "gilet"} if r.random() < 0.15 else None)
    hc = r.choice(SPACE + HAIR_DYED)
    cols = {"skin": skin, "skin2": _darker(skin, 0.25), "hair": hc, "hair2": _lighter(hc, 0.3), "top": c1, "top2": c2, "top3": _lighter(c1, 0.4),
            "bottom": c1 if kind == "jumpsuit" else r.choice(SPACE), "bottom2": _darker(c1, 0.3), "shoes": r.choice(["#c8d4e8", "#3a4a6a", "#e8c860", "#2a3050"]),
            "outer": c2, "outer2": _lighter(c2, 0.3), "acc": r.choice(["#e8c860", "#c8d4e8", "#6a5ac8"]), "acc2": "#e8f0ff",
            "eye_d": "#0b0822" if arch != "grey" else "#06040e", "extra": _darker(skin, 0.35), "horn": _lighter(skin, 0.4)}
    spec.update({"species": sp, "hair": hair, "top": top, "outer": outer, "bottom": bottom, "shoes": {"kind": r.choice(["boots", "trainers"])},
                 "hat": None, "acc": [a for a, p in (("belt", 0.5), ("sash", 0.12), ("bracelet", 0.2)) if r.random() < p],
                 "face": {"eyes": r.choice(["open", "open", "lost"])}, "colours": cols})
    return spec


# ---- the Underworld's demons ------------------------------------------------------------------------------------------------------------------------

def demon(r: random.Random, arch: str) -> dict:
    skin = r.choice(DEMON_SKIN[arch])
    spec = _build(r)
    sp = {"kind": {"horned_queen": "queen"}.get(arch, arch)}
    hair = {"style": r.choice(["none", "short", "long", "mohawk", "spiky"])}
    top = {"kind": r.choice(["vest", "tank", "tee", "bare"]), "pattern": r.choice(["plain", "plain", "stripes", "print"]), "motif": r.choice(["star", "bolt", "diamond", "sun"]), "neck": "v"}
    bottom = {"kind": r.choice(["trousers", "leggings", "baggy", "loincloth"])}
    outer = None
    acc = []
    if arch == "imp":
        sp.update(horns="small", tail=True, ears="pointed")
        spec.update(height=round(r.uniform(0.74, 0.84), 3), head=1.18, width=round(r.uniform(0.85, 1.05), 3))
        hair = {"style": r.choice(["none", "spiky", "short"])}
    elif arch == "brute":
        sp.update(horns=r.choice(["big", "ram"]))
        spec.update(width=round(r.uniform(1.25, 1.45), 3), height=round(r.uniform(1.04, 1.12), 3), head=0.92, curve=0.0)
        top = {"kind": "bare", "pattern": "plain"}
        acc = [r.choice(["harness", "plates", "harness"])]
        bottom = {"kind": r.choice(["loincloth", "trousers", "baggy"])}
        hair = {"style": r.choice(["none", "mohawk", "buzz"])}
    elif arch == "fiend":
        sp.update(horns=r.choice(["long", "small", "ram"]), wings="bat")
        spec.update(width=round(r.uniform(0.84, 0.98), 3), height=round(r.uniform(1.0, 1.08), 3))
        hair = {"style": r.choice(["long", "wavy", "bob", "mohawk"])}
        top = {"kind": r.choice(["crop", "vest", "longsleeve"]), "pattern": r.choice(["plain", "stripes"]), "neck": "v"}
    elif arch == "skeleton":
        spec.update(width=round(r.uniform(0.85, 1.0), 3), limb=0.7)
        top = {"kind": r.choice(["bare", "vest", "tee"]), "pattern": "ribs" if r.random() < 0.7 else "plain"}
        if top["kind"] == "bare":
            top = {"kind": "tank", "pattern": "ribs"}
        hair = {"style": "none"}
        acc = [r.choice(["bow", "scarf", "necklace"])] if r.random() < 0.5 else []
    elif arch == "flame":
        hair = {"style": "flames"}
        top = {"kind": r.choice(["tank", "vest", "tee"]), "pattern": r.choice(["plain", "print"]), "motif": "sun"}
    elif arch == "horned_queen":
        sp.update(horns=r.choice(["long", "ram"]))
        spec.update(curve=round(r.uniform(0.6, 1.0), 2), height=round(r.uniform(1.0, 1.1), 3))
        top = {"kind": r.choice(["dress", "dress", "leotard"]), "pattern": "plain", "neck": "v"}
        outer = {"kind": "cape"}
        hair = {"style": r.choice(["long", "wavy", "bun"])}
    c1, c2 = _two(r, HELL)
    hc = r.choice(["#1a0a12", "#2a1018", "#e0d0b0", "#c04a1a", "#6a1a20", "#e05a8a"])
    cols = {"skin": skin, "skin2": _lighter(skin, 0.3) if arch != "flame" else "#ffe45a", "hair": hc if arch != "flame" else r.choice(["#ff7a1a", "#ff5a2a", "#7a3cff"]),
            "hair2": _lighter(hc, 0.3) if arch != "flame" else "#ffe45a", "top": c1, "top2": c2, "top3": _lighter(c1, 0.35), "bottom": r.choice(HELL),
            "bottom2": r.choice(HELL), "shoes": r.choice(["#2a1a1a", "#3a2a20", "#1a0a10"]), "outer": r.choice(["#8a1a2a", "#3a1a70", "#1a0a12"]),
            "outer2": r.choice(["#e0b040", "#ff2f9d"]), "acc": r.choice(["#3a2a20", "#2a1a1a"]), "acc2": "#e0b040", "horn": r.choice(["#efe2c0", "#d8c8a0", "#2a1a1a", "#c8b090"]),
            "extra": _darker(skin, 0.4), "metal": "#8a8890", "eye_d": "#1a0808" if arch != "skeleton" else "#0a0406"}
    if arch == "skeleton":
        cols["top"] = r.choice(["#1a0a12", "#2a1018"])
    spec.update({"species": sp, "hair": hair, "top": top, "outer": outer, "bottom": bottom,
                 "shoes": {"kind": r.choice(["boots", "bare", "boots"]) if arch not in ("horned_queen",) else "heels"}, "hat": None, "acc": acc,
                 "face": {"eyes": r.choice(["open", "open", "lost"])}, "colours": cols})
    if arch == "skeleton" and r.random() < 0.4:
        spec["hat"] = {"kind": r.choice(["party", "cap", "bucket"])}
    if arch == "horned_queen":
        spec["hat"] = {"kind": "crown"} if r.random() < 0.6 else None
    return spec


# ---- the Hospital's families, staff and patients ----------------------------------------------------------------------------------------------------

def hospital(r: random.Random, arch: str, actor: dict) -> dict:
    spec = _build(r)
    hc = _hair_colours(r, 0.05, old=(arch == "granny"))
    c1, c2 = _two(r, VISIT)
    cols = {"skin": r.choice(SKINS), "hair": hc, "hair2": _lighter(hc, 0.25), "top": c1, "top2": c2, "top3": _lighter(c1, 0.35), "outer": r.choice(VISIT),
            "outer2": r.choice(VISIT), "bottom": r.choice(DENIM + DARKS), "bottom2": r.choice(DARKS), "shoes": r.choice(SHOE), "hat": r.choice(VISIT)}
    cols["hat2"] = _darker(cols["hat"], 0.3)
    hair = {"style": r.choice(["short", "bob", "long", "curly", "bun", "ponytail", "wavy", "buzz", "braids", "locs"]), "part": round(r.uniform(-0.3, 0.3), 2)}
    top = {"kind": r.choice(["jumper", "shirt", "tee", "longsleeve", "polo"]), "pattern": r.choice(["plain", "stripes", "check", "plain", "band", "print"]),
           "motif": r.choice(MOTIFS), "neck": "crew"}
    outer = {"kind": r.choice(["coat", "cardigan", "jacket"]), "long": r.random() < 0.4} if r.random() < 0.5 else None
    bottom = {"kind": r.choice(["jeans", "trousers", "skirt"]) }
    hat = None
    acc = [a for a, p in (("strap", 0.3), ("scarf", 0.2), ("watch", 0.3)) if r.random() < p]
    face = _face(r, 0.3)
    if arch == "granny":
        spec.update(height=round(r.uniform(0.86, 0.96), 3), curve=round(r.uniform(0.5, 1.0), 2))
        hair = {"style": r.choice(["perm", "bun", "short", "bob"])}
        outer = {"kind": "cardigan"}
        bottom = {"kind": r.choice(["skirt", "trousers"]), "len": 0.95}
        face["glasses"] = r.choice(["round", "square", None])
        cols["outer"] = r.choice(["#b79be0", "#f0b04a", "#c8604a", "#6a8a5a", "#d0a0a0"])
    elif arch == "dad":
        spec.update(curve=round(r.uniform(0.0, 0.3), 2))
        face = _face(r, 0.6)
        hair = {"style": r.choice(["short", "buzz", "bald", "short", "quiff", "curly"])}
        bottom = {"kind": r.choice(["jeans", "trousers"])}
    elif arch == "mum":
        spec.update(curve=round(r.uniform(0.6, 1.0), 2))
        face = _face(r, 0.0)
        if r.random() < 0.15:
            hat = {"kind": "scarf"}
    elif arch == "kid":
        spec.update(height=round(r.uniform(0.6, 0.72), 3), head=1.28, width=round(r.uniform(0.9, 1.05), 3))
        face = _face(r, 0.0)
        hair = {"style": r.choice(["short", "curly", "pigtails", "bob", "afro", "spiky", "ponytail"])}
        top = {"kind": "tee", "pattern": r.choice(["print", "stripes", "print", "emblem"]), "motif": r.choice(MOTIFS), "neck": "crew"}
        bottom = {"kind": r.choice(["shorts", "jeans", "leggings"])}
        outer = None
        cols["shoes"] = r.choice(["#e05a8a", "#3a8ad0", "#e8c040", "#ecebe6"])
        cols["top"] = r.choice(["#e05a5a", "#3a9ad0", "#e8c040", "#5ab86a", "#9a6ad0", "#f0a040"])
    elif arch == "nurse":
        sc = r.choice(SCRUBS)
        top = {"kind": "scrubs", "neck": "v", "pattern": "plain"}
        bottom = {"kind": "trousers"}
        outer = None
        cols.update(top=sc, top3=_darker(sc, 0.2), bottom=sc, shoes=r.choice(["#ecebe6", "#3a3a4a", "#e8e0f0"]))
        hat = {"kind": "scrubcap"} if r.random() < 0.45 else None
        cols["hat"] = r.choice(SCRUBS + ["#e0a0c0", "#a0c0e0"])
        hair = {"style": r.choice(["bun", "ponytail", "short", "braids", "bob"])}
        acc = ["lanyard"] + (["watch"] if r.random() < 0.5 else [])
    elif arch == "doctor":
        top = {"kind": r.choice(["shirt", "scrubs", "polo"]), "pattern": r.choice(["plain", "vstripes"]), "neck": "collar"}
        outer = {"kind": "labcoat", "long": True}
        cols.update(outer="#eef0f2", outer2="#c8ccd4")
        bottom = {"kind": "trousers"}
        acc = ["stethoscope", "lanyard"]
        hair = {"style": r.choice(["short", "bald", "bob", "bun", "curly", "buzz"])}
    if str(actor.get("prop", "")) == "drip" or str(actor.get("activity", "")) == "lie":  # a patient: a hospital gown, bare legs, slippers
        top = {"kind": "gown", "pattern": "dots", "neck": "crew"}
        cols.update(top=r.choice(GOWN), top2="#6a8ab0")
        outer = None
        bottom = {"kind": "gownlegs"}
        spec["shoes"] = {"kind": "slippers"}
    cols["acc"] = cols.get("acc", r.choice(["#3a2a2a", "#2a3a5a", "#c03a3a"]))
    cols["acc2"] = "#e0e8f0" if arch in ("nurse", "doctor") else "#d8b048"
    if arch in ("nurse", "doctor"):
        cols["acc"] = r.choice(["#2a5aa0", "#c03a3a", "#2a8a6a"])
    spec.setdefault("shoes", {"kind": r.choice(["trainers", "boots"]) if arch not in ("nurse",) else "clogs"})
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "hat": hat, "acc": acc, "face": face, "colours": cols})
    return spec


# ---- the Ward: residents in fancy dress, staff in green ----------------------------------------------------------------------------------------------

def ward(r: random.Random, arch: str) -> dict:
    spec = _build(r)
    hc = _hair_colours(r, 0.08, old=r.random() < 0.25)
    cols = {"skin": r.choice(SKINS), "hair": hc, "hair2": _lighter(hc, 0.25), "shoes": r.choice(["#3a2a2a", "#e8e0d0", "#6a4a32"])}
    hair = {"style": r.choice(["short", "curly", "long", "buzz", "bald", "bob", "wavy", "spiky", "bun"]), "part": round(r.uniform(-0.3, 0.3), 2)}
    face = _face(r, 0.35)
    acc = []
    outer = None
    hat = None
    if arch == "pirate":
        top = {"kind": r.choice(["tee", "longsleeve"]), "pattern": "stripes", "neck": "v"}
        cols.update(top=r.choice(["#f0e8d8", "#e8e0d0"]), top2=r.choice(["#c03a3a", "#2a3a6a", "#2a2a3a"]), bottom=r.choice(["#2b2f55", "#5a4a3a", "#3a3030"]))
        hat = {"kind": r.choice(["tricorn", "bandana", "bandana"])}
        cols.update(hat=r.choice(["#2a2a30", "#c03a3a", "#3a3a6a"]), hat2=r.choice(["#e0b040", "#f0e8d8"]))
        acc = ["eyepatch"] + (["sash"] if r.random() < 0.6 else []) + (["belt"] if r.random() < 0.5 else [])
        bottom = {"kind": r.choice(["trousers", "baggy", "shorts"])}
        spec["shoes"] = {"kind": "boots"}
        face["beard"] = r.choice(["beard", "stubble", None, "moustache"])
    elif arch == "king":
        top = {"kind": r.choice(["shirt", "jumper"]), "pattern": r.choice(["plain", "vstripes"]), "neck": "collar"}
        outer = {"kind": "coat", "long": True, "trim": True}
        cols.update(top=r.choice(["#f0e8d8", "#a8d0e8", "#f2c0d0"]), top2="#8a8ab0", outer=r.choice(["#7a3c9a", "#a02a3a", "#2a5a9a", "#2a8a7a"]), outer2="#f4f0e6",
                    bottom=r.choice(["#bfe0ee", "#f3d9e6", "#c8c8d8"]))
        hat = {"kind": "crown"}
        cols.update(hat="#e8c040", hat2="#c09020")
        bottom = {"kind": "pyjamas"}
        spec["shoes"] = {"kind": "slippers"}
        hair = {"style": r.choice(["short", "bald", "curly", "perm"])}
        cols["hair"] = r.choice(["#d8d4cf", "#ece8e2", "#8a6a4a"])
        face["beard"] = r.choice(["beard", "beard", None])
    elif arch == "chef":
        top = {"kind": "chef", "pattern": "plain", "neck": "collar"}
        cols.update(top="#f4f2ec", top3="#dcd8d0", bottom=r.choice(["#2a2a3a", "#3a3f66"]), bottom2="#e8e4dc")
        bottom = {"kind": "trousers", "pattern": "check"}
        hat = {"kind": "chef"}
        cols.update(hat="#f6f4ee", hat2="#dcd8d0")
        acc = ["scarf"] if r.random() < 0.6 else []
        cols["acc"] = r.choice(["#c03a3a", "#3a6ad0"])
    elif arch == "superhero":
        top = {"kind": "tee", "pattern": "emblem", "motif": r.choice(["bolt", "star", "diamond"]), "neck": "crew"}
        c1, c2 = _two(r, ["#3a6ab0", "#c03a3a", "#e0b040", "#3a8a5a", "#7a3c9a"])
        cols.update(top=c1, top2=c2, bottom=r.choice(["#2a3a7a", "#a8203a", "#3a3a4a"]), bottom2=c1)
        outer = {"kind": "cape"}
        cols.update(outer=r.choice(["#e05050", "#e8c040", "#5ab0e0", "#e07ab0"]), outer2="#f0e8d8")
        bottom = {"kind": r.choice(["leggings", "pyjamas", "shorts"])}
        spec["shoes"] = {"kind": r.choice(["boots", "wellies", "slippers"])}
        acc = ["mask"] if r.random() < 0.6 else []
        cols["acc"] = r.choice(["#1a1a2a", "#c03a3a"])
    elif arch == "ballerina":
        top = {"kind": "leotard", "pattern": "plain", "neck": "scoop", "sleeves": "none"}
        cc = r.choice(["#ff9ac8", "#a98aef", "#e8e0f0", "#a8d0e8", "#f2c0d0"])
        cols.update(top=cc, top3=_lighter(cc, 0.3), bottom=_lighter(cc, 0.2), bottom2=r.choice(["#f2d0dc", "#e8c9e6", "#d8d0e8"]))
        bottom = {"kind": "tutu", "tights": True}
        hair = {"style": "bun"}
        spec.update(curve=round(r.uniform(0.3, 1.0), 2), width=round(r.uniform(0.82, 1.02), 3))
        spec["shoes"] = {"kind": "slippers"}
        cols["shoes"] = _lighter(cc, 0.2)
    else:  # the orderly: institutional green, keys and a lanyard
        g = r.choice(WARD_STAFF)
        top = {"kind": r.choice(["scrubs", "polo", "scrubs"]), "pattern": "plain", "neck": "v"}
        cols.update(top=g, top3=_darker(g, 0.25), bottom=_darker(g, 0.1), shoes=r.choice(["#ecebe6", "#2a2a2a"]))
        bottom = {"kind": "trousers"}
        acc = ["lanyard", "belt"] + (["watch"] if r.random() < 0.5 else [])
        cols.update(acc="#2a3a2a", acc2="#d8d4c8")
        hair = {"style": r.choice(["short", "buzz", "bun", "ponytail", "bald", "braids", "curly"])}
    spec.setdefault("shoes", {"kind": r.choice(["slippers", "trainers"])})
    cols.setdefault("top2", "#c8c0b0")
    cols.setdefault("top3", "#d8d0c4")
    cols.setdefault("bottom2", "#2a2a36")
    cols.setdefault("hat", "#3a3a4a")
    cols.setdefault("hat2", "#2a2a36")
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "hat": hat, "acc": acc, "face": face, "colours": cols})
    return spec


# ---- the Gospel path: robes, tunics and sandals (docs/THREE_PATHS_AND_FACES_PLAN.md 4.3) --------------------------------------------------------------------

GOSPEL_MAPS = ("galilee_shore", "hillside", "bethany", "jerusalem")
WOOL = ["#e6dcc0", "#d8c8a0", "#c8b088", "#bca078", "#a88860", "#8a6a48", "#d2c4a4", "#b8a688"]
DYE = ["#8a4a30", "#4a5a7a", "#8a3a2a", "#5a6a48", "#6a4a6a", "#a8782a", "#3a6a6a", "#7a5a3a"]
HEAD_CLOTH = ["#e8e0cc", "#d4c4a0", "#c8a878", "#a86a48", "#7a8aa8", "#b8b098"]
MID_SKINS = SKINS[2:9]


def gospel(r: random.Random, actor: dict) -> dict:
    """The Gospel path's people. `wear` names who they are (fisher, villager, disciple, priest, soldier, merchant, sister / woman / mother, child, elder, governor, tempter, baptist,
    shepherd, carpenter, gardener); undyed wool, stripes, headscarves, sandals; soldiers in a plain lamellar cuirass and a plumeless helmet, priests in white with a blue sash, the
    governor in a white toga with one red band. No emblem of any real force and no copy of any painting."""
    wear = str(actor.get("wear", "villager"))
    spec = _build(r, height=(0.94, 1.08))
    skin = r.choice(MID_SKINS)
    hc = r.choice(["#1b1416", "#2a1c18", "#3b281e", "#523422", "#6e4426"])
    cols = {"skin": skin, "hair": hc, "hair2": _lighter(hc, 0.25), "shoes": r.choice(["#6a4a32", "#8a6a48", "#5a3a28"]), "acc": "#5a3a22", "acc2": "#c8a050",
            "hat": r.choice(HEAD_CLOTH), "outer": r.choice(WOOL), "outer2": r.choice(DYE)}
    cols["hat2"] = _darker(cols["hat"], 0.3)
    top = {"kind": "dress", "pattern": "plain", "neck": "v"}
    bottom = {"kind": "dress_legs"}
    outer = None
    hat = None
    acc: list = []
    shoes = {"kind": "slippers"}
    hair = {"style": r.choice(["short", "curly", "long", "wavy", "buzz"]), "part": round(r.uniform(-0.3, 0.3), 2)}
    face = _face(r, 0.55)
    c1 = r.choice(WOOL + DYE[:4])
    c2 = r.choice(DYE)
    cols.update(top=c1, top2=c2, top3=_darker(c1, 0.22), bottom=c1, bottom2=_darker(c1, 0.3))
    fem = wear in ("sister", "woman", "mother")
    if fem:
        spec.update(curve=round(r.uniform(0.6, 1.0), 2), height=round(r.uniform(0.9, 1.0), 3))
        hair = {"style": r.choice(["long", "bun", "braids", "wavy"])}
        face = _face(r, 0.0)
        hat = {"kind": "scarf"} if r.random() < 0.8 else None
        top["pattern"] = r.choice(["plain", "band", "plain", "stripes"])
        cols["top3"] = r.choice(DYE)
    else:
        spec.update(curve=round(r.uniform(0.0, 0.3), 2))
    if wear == "disciple":
        top["pattern"] = r.choice(["plain", "stripes", "band", "vstripes"])
        outer = {"kind": "cape"} if r.random() < 0.35 else None
        acc = ["sash"] if r.random() < 0.6 else (["belt"] if r.random() < 0.5 else [])
        hat = {"kind": "scarf"} if r.random() < 0.25 else None
    elif wear == "villager":
        top["pattern"] = r.choice(["plain", "stripes", "plain"])
        hat = {"kind": "scarf"} if r.random() < 0.4 else None
        acc = ["belt"] if r.random() < 0.4 else []
    elif wear in ("sister", "woman", "mother"):
        acc = ["necklace"] if r.random() < 0.3 else []
    elif wear == "fisher":
        top = {"kind": "tank", "pattern": r.choice(["plain", "stripes"]), "neck": "scoop"}
        bottom = {"kind": r.choice(["shorts", "baggy"])}
        cols.update(top=r.choice(["#d8c8a0", "#bca078", "#9a8a68"]), bottom=r.choice(["#8a6a48", "#6a5a48", "#a89060"]), bottom2="#5a4a38")
        spec.update(width=round(r.uniform(1.0, 1.2), 3))
        hat = {"kind": "bandana"} if r.random() < 0.6 else None
        cols["hat"] = r.choice(["#b04a30", "#c8b088", "#4a5a7a"])
        shoes = {"kind": "bare"}
        face["beard"] = r.choice(["beard", "stubble", "beard", None])
        acc = ["belt"]
    elif wear == "priest":
        c = r.choice(["#f2eee4", "#ece6d6"])
        cols.update(top=c, top3=_darker(c, 0.18), top2="#3a5a9a", bottom=c, acc="#3a5a9a", acc2="#d8c8a0")
        top["pattern"] = "plain"
        acc = ["sash"]
        hat = {"kind": "turban"} if r.random() < 0.7 else None
        cols["hat"] = "#e8e2d2"
        cols["hat2"] = "#c8c0a8"
        face["beard"] = r.choice(["beard", "beard", "moustache"])
        spec.update(height=round(r.uniform(1.0, 1.1), 3))
    elif wear == "soldier":
        top = {"kind": "tee", "pattern": "check", "neck": "crew"}
        bottom = {"kind": "shorts"}
        cols.update(top="#a8864a", top2="#6a4a30", top3="#8a6a38", bottom="#7a3a2a", bottom2="#5a2a20", shoes="#4a3424", hat="#a8905a", hat2="#7a6a3a", metal="#a8905a", acc="#4a3424", acc2="#c8a050")
        acc = ["plates", "belt"]
        hat = {"kind": "helmet"}
        shoes = {"kind": "boots"}
        spec.update(width=round(r.uniform(1.05, 1.22), 3), height=round(r.uniform(1.0, 1.1), 3))
        hair = {"style": "buzz"}
        face["beard"] = r.choice([None, "stubble", "moustache"])
    elif wear == "merchant":
        top = {"kind": "longsleeve", "pattern": r.choice(["stripes", "band", "vstripes"]), "neck": "crew"}
        bottom = {"kind": "trousers"}
        outer = {"kind": "gilet", "pattern": "plain"} if r.random() < 0.6 else None
        cols.update(top=r.choice(["#8a3a2a", "#a8782a", "#3a6a6a", "#6a4a6a"]), top2="#e6dcc0", bottom="#5a4a38", outer="#7a5a3a", hat=r.choice(["#a8782a", "#8a3a2a", "#3a6a6a"]))
        hat = {"kind": "turban"}
        acc = ["necklace", "belt"]
        shoes = {"kind": "boots"}
        spec.update(width=round(r.uniform(1.05, 1.2), 3))
    elif wear == "child":
        spec.update(height=round(r.uniform(0.6, 0.72), 3), head=1.28, width=round(r.uniform(0.9, 1.05), 3))
        top = {"kind": "tee", "pattern": "plain", "neck": "crew"}
        bottom = {"kind": "shorts"}
        hair = {"style": r.choice(["short", "curly", "braids", "bob"])}
        face = _face(r, 0.0)
        hat = None
        acc = []
        shoes = {"kind": "bare"}
    elif wear == "elder":
        spec.update(height=round(r.uniform(0.9, 0.97), 3), curve=round(r.uniform(0.3, 0.7), 2))
        hc = r.choice(["#d8d4cf", "#ece8e2", "#b8b4b0", "#c9c3bd"])
        cols.update(hair=hc, hair2=_lighter(hc, 0.2))
        hair = {"style": r.choice(["short", "bald", "wavy", "long"])}
        face["beard"] = r.choice(["beard", "beard", None])
        outer = {"kind": "cape"}
        hat = {"kind": "scarf"} if r.random() < 0.5 else None
    elif wear == "governor":
        cols.update(top="#f4f0e6", top3="#a02a2a", top2="#a02a2a", bottom="#f4f0e6", outer="#f4f0e6", outer2="#a02a2a", acc="#a02a2a", acc2="#c8a050")
        top = {"kind": "dress", "pattern": "band", "neck": "v"}
        outer = {"kind": "cape"}
        hair = {"style": "short"}
        hat = None
        spec.update(height=round(r.uniform(1.0, 1.06), 3), width=round(r.uniform(1.1, 1.2), 3))
        face["beard"] = None
        acc = ["necklace"]
    elif wear == "tempter":
        c = r.choice(["#b8a078", "#a89068", "#c0a880"])
        cols.update(top=c, top3=_darker(c, 0.25), bottom=c, hat="#a08c64", hat2="#7a6a48")
        top["pattern"] = "plain"
        hat = {"kind": "scarf"}
        spec.update(height=1.12, width=0.9)
        face["beard"] = "stubble"
        outer = {"kind": "cape"}
    elif wear == "baptist":
        cols.update(top="#8a6a40", top3="#6a4a28", bottom="#8a6a40", acc="#4a3018")
        top = {"kind": "dress", "pattern": "plain", "neck": "v"}
        hair = {"style": "long"}
        face["beard"] = "beard"
        acc = ["belt"]
        shoes = {"kind": "bare"}
        hat = None
        spec.update(height=1.04, width=1.0)
    elif wear == "shepherd":
        cols.update(top=r.choice(["#c8b088", "#a88860", "#8a6a48"]), outer="#e6dcc0", outer2="#c8b088")
        outer = {"kind": "gilet", "pattern": "plain"}
        hat = {"kind": "scarf"}
        acc = ["belt"]
        face["beard"] = r.choice(["beard", "stubble", None])
    elif wear == "carpenter":
        top = {"kind": "longsleeve", "pattern": "plain", "neck": "crew"}
        bottom = {"kind": "trousers"}
        cols.update(top="#d8c8a0", bottom="#8a6a48", outer="#6a4a30", hat="#c8b088")
        outer = {"kind": "gilet", "pattern": "plain"}
        hair = {"style": "short"}
        acc = ["belt"]
        shoes = {"kind": "boots"}
        face["beard"] = "stubble"
    elif wear == "gardener":
        top = {"kind": "longsleeve", "pattern": "plain", "neck": "crew"}
        bottom = {"kind": "trousers"}
        cols.update(top="#c8b088", bottom="#6a5a48", hat="#d8c070")
        hat = {"kind": "bucket"}
        acc = ["strap"]
        shoes = {"kind": "boots"}
        face["beard"] = r.choice(["stubble", None])
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "shoes": shoes, "hat": hat, "acc": acc, "face": face, "colours": cols})
    return spec


# ---- the Squadron: the people of "The Mission Count" (docs/THREE_PATHS_AND_FACES_PLAN.md 5.3) -------------------------------------------------------
# A dark-comic 1940s air-force story told in generic khaki: no roundels, flags, national badges, unit emblems or lettering anywhere. Rank is shown only by
# invented things (plain gold stripes on the shoulder loops, ribbon bars in made-up colours, plain white or green bands). An actor carries `wear` (one of
# SQUADRON_WEARS) and a `variant` letter; `squadron()` dresses them. The airfield people are muted (bleached khaki, olive drab, orange dust, whites for the
# coats) so that the Colonel's ribbon bars are the only bright colour among them; the city is sepia and browns; the harbour cold blue with yellow oilskins.

SQUADRON_WEARS = ("airman", "officer", "clerk", "surgeon", "quartermaster", "gunner", "mp", "civilian_city", "fisherman", "patient")
VARIANT_ALIAS = {"man": "a", "woman": "b", "child": "c", "singer": "d", "mechanic": "b", "pilot": "c", "colonel": "a", "aide": "b", "chaplain": "c"}

KHAKI = ["#b4a474", "#ab9c6a", "#bcae80", "#a89a68", "#b8a878", "#c0b284"]
KHAKI_DK = ["#9c8e5e", "#948858", "#8a7e54"]
OLIVE = ["#6e7048", "#7a7a50", "#60673f", "#7c7e58"]
LEATHER = ["#7a5232", "#6a4628", "#8a6038", "#5e3e26"]
BOOTS = ["#3e2e22", "#4a3626", "#2e241c", "#54402c"]
DUST = ["#b8803a", "#a8703a", "#c09050"]
WHITES = ["#ebe8de", "#e4dfd0", "#f0ece2"]
SEPIA = ["#7a6248", "#5c4a38", "#8a7458", "#6a5440", "#9a8668", "#4a3c30", "#a08a6a", "#605848", "#8a6a50", "#6c6252", "#52483e", "#98846a"]
SEPIA_DRESS = ["#7a5a50", "#5a6068", "#6a6a50", "#805e48", "#4e5058", "#8a7070", "#6a5a6a", "#7a7058"]
SEPIA_LIGHT = ["#cbbfa4", "#d4c8ac", "#bcb094", "#c8bca0", "#ddd2b8"]
COLD = ["#3e5068", "#4a5a70", "#566878", "#2e3e52", "#6a7a8a", "#44586a", "#d4d0c0", "#8c9aa6"]
OILSKIN = ["#d6b030", "#c8a428", "#dcbc3c", "#c4a030"]
OIL_DARK = ["#26364a", "#2a3a40", "#32323c"]
PYJ = [("#cfd6d8", "#8da4b8"), ("#d8d4c6", "#98a8a0"), ("#c8d0d8", "#a89a8a"), ("#d4d8d0", "#9aa0b4"), ("#e0dcd0", "#b0b8c4")]
SCRUB_GREEN = ["#6a8a7a", "#5e8078", "#7a9a88"]

SQ_HAIR = ["short", "short", "quiff", "buzz", "curly", "wavy", "bald", "short", "spiky", "perm"]
SQ_HAIR_TIDY = ["short", "quiff", "buzz", "short"]


def _skin(r: random.Random, pale: bool = False) -> str:
    return r.choice(SKINS[:7]) if pale else r.choice(SKINS)


def _sq_cols(r: random.Random, skin: str, hair: str) -> dict:
    """The colours every squadron spec starts from (muted khaki); each wear then changes what it wears."""
    k = r.choice(KHAKI)
    return {"skin": skin, "hair": hair, "hair2": _lighter(hair, 0.25), "top": k, "top2": _darker(k, 0.14), "top3": _lighter(k, 0.2),
            "bottom": r.choice(KHAKI + OLIVE), "bottom2": "#4a4030", "shoes": r.choice(BOOTS), "shoes2": "#2a2018", "outer": r.choice(OLIVE),
            "outer2": "#4e5034", "hat": r.choice(KHAKI + OLIVE), "hat2": "#5a5a3c", "acc": r.choice(LEATHER), "acc2": "#c0a24c", "prop": "#7a4a2c",
            "prop2": "#ece6d6", "liquid": "#c8a040", "glass": "#d6e4ec", "horn": "#8a5444"}


def _sq_hair(r: random.Random, old: bool = False, pool=None) -> str:
    if old:
        return r.choice(OLD_HAIR)
    return r.choice(HAIR_NATURAL[:8])


def _sq_build(r, height, width, curve=None, **kw):
    b = _build(r, height, width, curve)
    b.update(kw)
    return b


def _w_airman(r, variant, actor):
    c = _sq_cols(r, _skin(r), _sq_hair(r))
    spec = _sq_build(r, (0.94, 1.07), (0.86, 1.12), curve=round(r.uniform(0.0, 0.4), 2))
    sleeves = r.choice(["rolled", "rolled", "long", "short"])
    top = {"kind": "uniform", "pattern": "plain", "neck": "collar", "sleeves": sleeves, "rank": 0, "epaulettes": r.random() < 0.5}
    outer, hat, acc = None, None, []
    bottom = {"kind": "trousers"}
    hair = {"style": r.choice(SQ_HAIR), "part": round(r.uniform(-0.3, 0.3), 2)}
    shoes = {"kind": "boots"}
    face = _face(r, 0.25)
    if variant == "b":  # ground crew: overalls, an oily rag, grime
        v = r.choice(OLIVE + KHAKI_DK)
        top = {"kind": "jumpsuit", "pattern": "plain", "neck": "collar", "sleeves": r.choice(["rolled", "long", "rolled"])}
        c.update(top=v, top2=_darker(v, 0.2), top3=_lighter(v, 0.18), bottom=v, bottom2=_darker(v, 0.25), acc=r.choice(["#3a3028", "#4a3c2c"]))
        hat = {"kind": "sidecap"} if r.random() < 0.4 else ({"kind": "knit"} if r.random() < 0.15 else None)
        c.update(hat=_darker(v, 0.05), hat2=_darker(v, 0.3))
        if hat and hat["kind"] == "knit":
            c.update(hat="#4a5058", hat2="#34383e")
        acc = ["rag"] if r.random() < 0.8 else []
        c["prop2"] = r.choice(["#d8d0bc", "#c8c0a8", "#b8b098"])
        bottom = {"kind": "trousers"}
    elif variant == "c":  # pilot: a leather flight jacket with a fleece collar, a scarf, a flying cap with goggles
        lea = r.choice(LEATHER)
        outer = {"kind": "jacket", "trim": True, "pattern": "plain"}
        c.update(outer=lea, outer2=r.choice(["#d8ccb0", "#cfc4a6", "#e0d6bc"]), hat=_darker(lea, 0.1), hat2=_darker(lea, 0.35), acc=r.choice(["#e4dcc4", "#d8c8a0", DUST[0], "#cfc6ac"]))
        c["glass"] = r.choice(["#d6e4ec", "#e0c88c", "#b8d0c8"])
        hat = {"kind": "flightcap", "goggles": True}
        acc = ["scarf"]
        top["sleeves"] = "long"
        hair = {"style": r.choice(SQ_HAIR_TIDY + ["wavy"]), "part": round(r.uniform(-0.3, 0.3), 2)}
        face = _face(r, 0.12)
    else:  # a plain airman
        if r.random() < 0.55:
            hat = {"kind": "sidecap"}
        if r.random() < 0.22:
            bottom = {"kind": "shorts"}
            spec["socks"] = True
            c["bottom2"] = r.choice(["#8a8a68", "#cfc7ac", "#9a9078"])
            shoes = {"kind": "boots"}
        acc = ["belt"]
        c["acc"] = r.choice(["#6a4a2c", "#54402c", "#7a5a38"])
        if r.random() < 0.18:
            top["rank"] = r.choice([1, 1, 2])
            top["epaulettes"] = True
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "shoes": shoes, "hat": hat, "acc": acc, "face": face, "colours": c})
    return spec


def _w_officer(r, variant, actor):
    old = variant in ("a", "c") and r.random() < 0.85
    hc = _sq_hair(r, old=old)
    c = _sq_cols(r, _skin(r), hc)
    k = r.choice(["#bcae80", "#b4a678", "#c2b688"])  # smarter, pressed khaki
    c.update(top=k, top2=_darker(k, 0.14), top3=_lighter(k, 0.22), bottom=_darker(k, 0.08), bottom2=_darker(k, 0.3), shoes=r.choice(["#2e2218", "#3a2a1c"]),
             acc=r.choice(["#6a4a2c", "#5a3c24"]), hat=_darker(k, 0.04), hat2=r.choice(["#5a5a3c", "#4e4a34"]))
    top = {"kind": "uniform", "pattern": "plain", "neck": "collar", "sleeves": "long", "rank": 1, "epaulettes": True}
    outer, hat, acc = None, None, ["webbing"]
    bottom = {"kind": "trousers"}
    shoes = {"kind": "boots"}
    face = _face(r, 0.0)
    extra = {}
    if variant == "a":  # the Colonel: broad, a peaked cap, a grey moustache, a chestful of ribbons
        spec = _sq_build(r, (1.0, 1.07), (1.14, 1.28), curve=round(r.uniform(0.0, 0.15), 2))
        top["rank"] = 3
        hat = {"kind": "peaked"}
        face["beard"] = "moustache"
        hair = {"style": r.choice(["short", "buzz", "bald", "short"]), "part": round(r.uniform(-0.2, 0.2), 2)}
        c.update(hair=r.choice(["#c9c3bd", "#b8b4b0", "#d8d4cf"]))
        c["hair2"] = _lighter(c["hair"], 0.25)
        c.update(prop="#a8403a", liquid="#d4a83a", horn="#3a5f9a", glass="#e8e6dc", shoes2="#3f7a4a")
        extra["ribbons"] = {"rows": 4, "cols": 3, "mats": ["prop", "liquid", "horn", "glass", "shoes2"], "seed": r.randrange(7)}
        acc = ["webbing", "ribbons"]
    elif variant == "b":  # the aide: slim, glasses, a neat head, a cap under his arm or on
        spec = _sq_build(r, (1.0, 1.08), (0.82, 0.93), curve=round(r.uniform(0.0, 0.35), 2))
        top["rank"] = 1
        hat = {"kind": "peaked"} if r.random() < 0.5 else ({"kind": "sidecap"} if r.random() < 0.5 else None)
        face["glasses"] = r.choice(["round", "square", "round"])
        hair = {"style": r.choice(SQ_HAIR_TIDY), "part": round(r.uniform(-0.3, 0.3), 2)}
        c.update(prop2="#f0ecdf")
        c["hair"] = r.choice(["#2a1c18", "#3b281e", "#523422", "#1b1416", "#6e4426"])
        c["hair2"] = _lighter(c["hair"], 0.25)
    else:  # the Chaplain: the same uniform without the belt, a dark plain collar band, no cap, bald or grey
        spec = _sq_build(r, (0.96, 1.03), (0.9, 1.05), curve=round(r.uniform(0.0, 0.3), 2))
        top["rank"] = 0
        top["epaulettes"] = False
        acc = ["collarband"]
        c.update(acc="#2e2a28")
        hair = {"style": r.choice(["bald", "short", "bald"]), "part": 0.0}
        if face.get("glasses") is None and r.random() < 0.4:
            face["glasses"] = "round"
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "shoes": shoes, "hat": hat, "acc": acc, "face": face, "colours": c})
    spec.update(extra)
    return spec


def _w_clerk(r, variant, actor):
    old = variant == "c"
    hc = _sq_hair(r, old=old)
    c = _sq_cols(r, _skin(r, pale=r.random() < 0.7), hc)
    shirt = r.choice(["#e6e0cc", "#ddd8c4", "#ece6d4", "#d8d4c0"])
    c.update(top=shirt, top2=_darker(shirt, 0.16), top3=_lighter(shirt, 0.15), bottom=r.choice(["#5e5a48", "#4e5040", "#6a6450", "#585a54"]), bottom2="#3a3628",
             shoes=r.choice(["#3a2a1e", "#2e241c"]), outer=r.choice(["#5e5a48", "#6a6248", "#54584c", "#6a6658"]), outer2="#34301f", acc="#3a3028", acc2="#b89a48",
             hat="#7aa088", hat2="#4e6e5c", prop="#6a3c26", prop2="#f0ecdf")
    spec = _sq_build(r, (0.79, 0.85), (0.84, 0.98), curve=round(r.uniform(0.05, 0.55), 2))
    top = {"kind": "shirt", "pattern": r.choice(["plain", "plain", "vstripes"]), "neck": "collar", "sleeves": "long"}
    outer, hat = {"kind": "waistcoat"}, None
    acc = ["garters", "bow"] if r.random() < 0.7 else ["garters"]
    face = _face(r, 0.0)
    face["glasses"] = "round"
    face["eyes"] = "open"
    hair = {"style": r.choice(["short", "quiff", "short", "buzz"]) if spec["curve"] < 0.5 else r.choice(["bob", "short", "bun"]),
            "part": round(r.choice([-0.3, -0.2, 0.2, 0.3]), 2)}
    if variant == "b":  # sleeves rolled, a cardigan instead of the waistcoat
        top["sleeves"] = "rolled"
        outer = {"kind": "cardigan", "pattern": "plain"}
        c.update(outer=r.choice(["#6a7060", "#7a6a58", "#5e6a6a"]), outer2="#e0dcc8")
        acc = ["bow"] if r.random() < 0.5 else []
    elif variant == "c":  # an older clerk with an eyeshade and a moustache
        hat = {"kind": "eyeshade"}
        face["beard"] = "moustache" if r.random() < 0.6 else None
        hair = {"style": r.choice(["short", "bald", "short"]), "part": 0.2}
        acc = ["garters", "chain"]
    else:
        acc = acc + (["chain"] if r.random() < 0.5 else [])
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"}, "hat": hat, "acc": acc, "face": face,
                 "colours": c})
    return spec


def _w_surgeon(r, variant, actor):
    old = variant == "c" or r.random() < 0.6
    hc = _sq_hair(r, old=old)
    c = _sq_cols(r, _skin(r, pale=r.random() < 0.65), hc)
    white = r.choice(WHITES)
    c.update(outer=white, outer2=_darker(white, 0.12), horn=r.choice(["#8a4c3c", "#7a4a3c", "#94503e"]), acc=r.choice(SCRUB_GREEN), hat=r.choice(SCRUB_GREEN),
             hat2=_darker(r.choice(SCRUB_GREEN), 0.2), bottom=r.choice(KHAKI_DK), shoes=r.choice(["#e4e0d4", "#3a2a1e", "#cfcabc"]), metal="#9aa2ac")
    spec = _sq_build(r, (1.0, 1.08), (0.86, 1.0), curve=round(r.uniform(0.0, 0.35), 2))
    top = {"kind": "uniform", "pattern": "plain", "neck": "collar", "sleeves": "long", "rank": 0, "epaulettes": False}
    outer = {"kind": "labcoat", "long": True, "pattern": "stained"}
    hat = {"kind": "surgcap"} if variant == "a" else None
    acc = ["stethoscope", "maskdown"]
    face = _face(r, 0.0)
    face["beard"] = "stubble"
    face["glasses"] = r.choice([None, None, "round", "square"])
    face["eyes"] = "open"
    hair = {"style": "bald" if variant == "c" else r.choice(["short", "bald", "buzz", "short"]), "part": round(r.uniform(-0.2, 0.2), 2)}
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": {"kind": "trousers"}, "shoes": {"kind": r.choice(["boots", "clogs"])}, "hat": hat, "acc": acc,
                 "face": face, "colours": c})
    return spec


def _w_quartermaster(r, variant, actor):
    hc = _sq_hair(r, old=variant == "c" and r.random() < 0.6)
    c = _sq_cols(r, _skin(r), hc)
    cream = r.choice(["#d8ceb2", "#cfc4a4", "#c4b894", "#d4cab0"])
    c.update(outer=cream, outer2=_darker(cream, 0.28), acc=r.choice(["#6a4a2c", "#54402c"]), prop2="#f2ecda", hat=r.choice(KHAKI_DK + OLIVE), hat2="#4a4630")
    spec = _sq_build(r, (0.93, 1.0), (1.12, 1.3), curve=round(r.uniform(0.05, 0.4), 2))
    top = {"kind": "uniform", "pattern": "plain", "neck": "collar", "sleeves": "rolled", "rank": 0, "epaulettes": False}
    hat = None
    face = _face(r, 0.0)
    face["beard"] = r.choice(["moustache", "moustache", "stubble"])
    hair = {"style": r.choice(["short", "bald", "quiff", "buzz", "short"]), "part": round(r.uniform(-0.3, 0.3), 2)}
    if variant == "b":
        hat = {"kind": "sidecap"} if r.random() < 0.5 else {"kind": "flatcap"}
    elif variant == "c":
        hair = {"style": "bald", "part": 0.0}
    spec.update({"hair": hair, "top": top, "outer": None, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"}, "hat": hat, "acc": ["apron"], "face": face,
                 "colours": c})
    return spec


def _w_gunner(r, variant, actor):
    c = _sq_cols(r, _skin(r), _sq_hair(r))
    lea = r.choice(LEATHER)
    c.update(outer=_darker(lea, 0.1), outer2=r.choice(["#d8ccb0", "#cfc4a6"]), hat=r.choice(["#a07a4c", "#946e44", "#b08456"]), hat2=_darker(lea, 0.3), acc=r.choice(["#e4dcc4", "#cfc6ac"]),
             glass=r.choice(["#d6e4ec", "#e0c88c"]), bottom=r.choice(KHAKI_DK + OLIVE), shoes=r.choice(BOOTS))
    spec = _build(r, (0.66, 0.74), (0.92, 1.04), curve=0.3)
    spec["head"] = round(r.uniform(1.24, 1.32), 2)
    spec["limb"] = 1.05
    top = {"kind": "uniform", "pattern": "plain", "neck": "collar", "sleeves": "long", "epaulettes": False}
    outer = {"kind": "jacket", "trim": True, "big": 1.38, "hem": 0.1, "pattern": "plain"}
    hat = {"kind": "flightcap", "goggles": True, "big": 1.1}
    acc = ["scarf"] if variant == "b" else []
    face = _face(r, 0.0)
    face["freckles"] = variant == "c" or r.random() < 0.3
    face["glasses"] = None
    hair = {"style": r.choice(["short", "curly", "spiky", "short"]), "part": round(r.uniform(-0.3, 0.3), 2)}
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"}, "hat": hat, "acc": acc, "face": face,
                 "colours": c})
    return spec


def _w_mp(r, variant, actor):
    c = _sq_cols(r, _skin(r), _sq_hair(r))
    k = r.choice(["#b8aa7c", "#b0a274", "#bcae82"])
    c.update(top=k, top2=_darker(k, 0.14), top3=_lighter(k, 0.2), bottom=_darker(k, 0.06), bottom2=_darker(k, 0.3), shoes=r.choice(["#1e1812", "#2a2018"]),
             acc="#ece8dc", acc2="#c0a24c", hat="#ece9e0", hat2="#a8a498", prop2="#f4f0e4")
    spec = _sq_build(r, (1.0, 1.1), (1.02, 1.2), curve=round(r.uniform(0.0, 0.2), 2))
    spec["gloves"] = r.random() < 0.6
    top = {"kind": "uniform", "pattern": "plain", "neck": "collar", "sleeves": "long", "rank": 2 if variant != "c" else 1, "epaulettes": True}
    face = _face(r, 0.1)
    face["glasses"] = "shades" if variant == "b" else None
    hair = {"style": r.choice(["buzz", "short", "short", "bald"]), "part": 0.0}
    spec.update({"hair": hair, "top": top, "outer": None, "bottom": {"kind": "trousers"}, "shoes": {"kind": "boots"}, "hat": {"kind": "mphelm"},
                 "acc": ["webbing", "armband"], "face": face, "colours": c})
    return spec


def _w_civilian(r, variant, actor):
    sep = r.choice(SEPIA)
    c = _sq_cols(r, _skin(r), _sq_hair(r))
    c.update(top=r.choice(SEPIA_LIGHT), top2=_darker(sep, 0.1), bottom=r.choice(SEPIA[:8]), bottom2="#4a4034", shoes=r.choice(["#3a2a1e", "#2e241c", "#4a3626"]),
             outer=sep, outer2=_darker(sep, 0.3), hat=r.choice(SEPIA[:8]), hat2=r.choice(["#3a3028", "#4a3c30"]), acc=r.choice(["#3a3028", "#6a5440"]),
             acc2="#b09a60", prop2="#e8e0cc")
    c["top3"] = _lighter(c["top"], 0.2)
    face = _face(r, 0.0)
    if variant == "b":  # a woman
        spec = _sq_build(r, (0.9, 1.0), (0.84, 1.04), curve=round(r.uniform(0.6, 1.0), 2))
        dress = r.random() < 0.45
        dc = r.choice(SEPIA_DRESS)
        if dress:
            top = {"kind": "dress", "pattern": r.choice(["plain", "plain", "dots"]), "neck": "scoop" if r.random() < 0.4 else "crew", "sleeves": "short"}
            c.update(top=dc, top2=_lighter(dc, 0.25), top3=_lighter(dc, 0.3), bottom=dc)
            bottom = {"kind": "trousers"}
            bottom = {"kind": "skirt", "len": 0.95, "tights": r.random() < 0.5}
            c["bottom2"] = r.choice(["#4a4034", "#6a5a48"])
        else:
            top = {"kind": r.choice(["shirt", "jumper", "longsleeve"]), "pattern": "plain", "neck": "collar", "sleeves": "long"}
            c.update(top=r.choice(SEPIA_LIGHT + [dc]), bottom=r.choice(SEPIA_DRESS), bottom2="#4a4034")
            bottom = {"kind": "skirt", "len": 0.95, "tights": r.random() < 0.5}
        outer, acc = None, []
        roll = r.random()
        if roll < 0.4:
            outer = {"kind": "coat", "long": True, "pattern": "plain"}
        elif roll < 0.65:
            outer = {"kind": "cardigan", "pattern": "plain"}
        elif roll < 0.85:
            acc = ["apron"]
            c.update(outer=r.choice(SEPIA_LIGHT), outer2=r.choice(["#8a7a62", "#6a5a48"]))
        hat = {"kind": "scarf"} if r.random() < 0.55 else None
        if hat:
            c.update(hat=r.choice(SEPIA_DRESS + SEPIA_LIGHT), hat2=r.choice(["#4a4034", "#6a5a48"]))
        hair = {"style": r.choice(["bun", "bob", "wavy", "long", "perm", "ponytail", "braids"]), "part": round(r.uniform(-0.3, 0.3), 2)}
        shoes = {"kind": r.choice(["heels", "boots", "boots"])}
        face = _face(r, 0.0)
    elif variant == "c":  # a child
        spec = _build(r, (0.6, 0.72), (0.9, 1.04), curve=0.3)
        spec["head"] = round(r.uniform(1.24, 1.32), 2)
        top = {"kind": r.choice(["jumper", "shirt", "longsleeve"]), "pattern": r.choice(["plain", "stripes", "plain"]), "neck": "crew", "sleeves": "long"}
        c.update(top=r.choice(SEPIA_LIGHT + COLD[:2] + SEPIA[:4]))
        c["top2"] = _darker(c["top"], 0.18)
        bottom = {"kind": "shorts"}
        spec["socks"] = True
        c.update(bottom=r.choice(SEPIA[:8]), bottom2=r.choice(["#8a8a7a", "#cfc7ac", "#9a9078"]))
        outer = {"kind": "gilet", "pattern": "plain"} if r.random() < 0.35 else None
        acc = ["braces"] if r.random() < 0.4 else []
        hat = {"kind": "flatcap"} if r.random() < 0.55 else None
        hair = {"style": r.choice(["short", "curly", "pigtails", "bob", "spiky", "short"]), "part": round(r.uniform(-0.3, 0.3), 2)}
        shoes = {"kind": r.choice(["boots", "boots", "slippers"])}
        face["freckles"] = r.random() < 0.3
    elif variant == "d":  # a street singer: a waistcoat, rolled sleeves, a hat held out for coins
        spec = _sq_build(r, (0.97, 1.06), (0.9, 1.12), curve=round(r.uniform(0.0, 0.3), 2))
        top = {"kind": "shirt", "pattern": r.choice(["plain", "vstripes"]), "neck": "collar", "sleeves": "rolled"}
        c.update(top=r.choice(["#e0d8c0", "#d8d0b8", "#cfc6aa"]), outer=r.choice(["#4a4034", "#5c4a38", "#3e3a34"]), outer2="#c0a24c")
        outer = {"kind": "waistcoat"}
        bottom = {"kind": "trousers"}
        acc = ["chain"] if r.random() < 0.5 else []
        hat = None
        c.update(hat=r.choice(["#6a5440", "#5c4a38", "#4e463a"]), hat2="#3a3028")
        hair = {"style": r.choice(["short", "curly", "quiff", "wavy"]), "part": round(r.uniform(-0.3, 0.3), 2)}
        shoes = {"kind": "boots"}
        face = _face(r, 0.35)
        face["eyes"] = "lost"
    else:  # a man
        spec = _sq_build(r, (0.95, 1.08), (0.9, 1.16), curve=round(r.uniform(0.0, 0.35), 2))
        top = {"kind": r.choice(["shirt", "shirt", "jumper", "longsleeve"]), "pattern": r.choice(["plain", "plain", "vstripes"]), "neck": "collar", "sleeves": "long"}
        if top["kind"] != "shirt":
            top["neck"] = "crew"
        c.update(top=r.choice(SEPIA_LIGHT + COLD[6:7]))
        c["top2"] = _darker(c["top"], 0.18)
        roll = r.random()
        outer, acc = None, []
        if roll < 0.45:
            outer = {"kind": "coat", "long": True, "pattern": "plain"}
        elif roll < 0.7:
            outer = {"kind": "jacket", "pattern": "plain"}
        elif roll < 0.85:
            outer = {"kind": "waistcoat"}
        else:
            acc = ["braces"]
        if r.random() < 0.3:
            acc = acc + ["scarf"]
        bottom = {"kind": "trousers"}
        hat = r.choice([{"kind": "flatcap"}, {"kind": "flatcap"}, {"kind": "fedora"}, None])
        hair = {"style": r.choice(SQ_HAIR), "part": round(r.uniform(-0.3, 0.3), 2)}
        shoes = {"kind": "boots"}
        face = _face(r, 0.38)
        if c["bottom"] in SEPIA_LIGHT:
            c["bottom"] = "#5c4a38"
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": bottom, "shoes": shoes, "hat": hat, "acc": acc, "face": face, "colours": c})
    return spec


def _w_fisherman(r, variant, actor):
    old = r.random() < 0.3
    c = _sq_cols(r, _skin(r), _sq_hair(r, old=old))
    sw = r.choice(COLD)
    yellow = variant != "b"
    oil = r.choice(OILSKIN) if yellow else r.choice(OIL_DARK)
    c.update(top=sw, top2=_darker(sw, 0.2), top3=_lighter(sw, 0.2), outer=oil, outer2=_darker(oil, 0.3), bottom=r.choice(["#2e3a48", "#34343c", "#3e4650"]),
             bottom2="#20262e", shoes=r.choice(["#1e1c1c", "#2a2624"]), hat=r.choice(["#34465a", "#7a3a34", "#44505a", "#6a6a58"]), hat2="#222c38", acc="#4a3c2c")
    spec = _sq_build(r, (0.98, 1.08), (1.04, 1.24), curve=round(r.uniform(0.0, 0.2), 2))
    top = {"kind": "jumper", "pattern": "knit", "neck": "crew", "sleeves": "long"}
    outer = {"kind": "oilskin", "long": True, "pattern": "plain"}
    hat = {"kind": "knit"}
    acc = []
    if variant == "b":
        hat = {"kind": "fisher"}
        c.update(hat=oil, hat2=_darker(oil, 0.3))
    elif variant == "c":  # in his jersey, no coat
        outer = None
        acc = ["scarf"] if r.random() < 0.5 else []
        c["acc"] = r.choice(["#a89a78", "#6a3a34", "#4a5a70"])
        top["pattern"] = "knit"
    face = _face(r, 0.0)
    face["beard"] = r.choice(["beard", "beard", "beard", "stubble"])
    hair = {"style": r.choice(["short", "curly", "buzz", "wavy"]), "part": round(r.uniform(-0.3, 0.3), 2)}
    spec.update({"hair": hair, "top": top, "outer": outer, "bottom": {"kind": "trousers"}, "shoes": {"kind": r.choice(["wellies", "boots"])}, "hat": hat, "acc": acc,
                 "face": face, "colours": c})
    return spec


def _w_patient(r, variant, actor):
    c = _sq_cols(r, _skin(r), _sq_hair(r))
    pj = r.choice(PYJ)
    c.update(top=pj[0], top2=pj[1], top3=_lighter(pj[0], 0.2), bottom=pj[0], bottom2=pj[1], shoes=r.choice(["#6a5a48", "#8a8070"]), shoes2="#c8c0b0", prop2="#f2eee4",
             horn=r.choice(["#9a5a48", "#8a4c3c"]), acc="#d8d4c8")
    spec = _sq_build(r, (0.94, 1.06), (0.84, 1.08), curve=round(r.uniform(0.0, 0.45), 2))
    gown = variant == "c" and r.random() < 0.3
    if gown:
        top = {"kind": "gown", "pattern": "dots", "neck": "crew"}
        c.update(top=r.choice(GOWN), top2="#6a8ab0")
        bottom = {"kind": "gownlegs"}
    else:
        top = {"kind": "pyjamas", "pattern": r.choice(["stripes", "vstripes", "plain"]), "neck": "collar", "sleeves": "long"}
        bottom = {"kind": "pyjamas", "pattern": "stripes" if r.random() < 0.7 else "plain"}
    acc = []
    face = _face(r, 0.4)
    if variant == "a":
        acc = ["bandage"]
    elif variant == "b":
        spec["sling"] = True
        acc = ["sling"]
    else:
        spec["plaster"] = r.choice(["l", "r"])
    shoes = {"kind": r.choice(["slippers", "bare", "slippers"])}
    hair = {"style": r.choice(SQ_HAIR), "part": round(r.uniform(-0.3, 0.3), 2)}
    spec.update({"hair": hair, "top": top, "outer": None, "bottom": bottom, "shoes": shoes, "hat": None, "acc": acc, "face": face, "colours": c})
    return spec


_SQ_WEAR = {"airman": _w_airman, "officer": _w_officer, "clerk": _w_clerk, "surgeon": _w_surgeon, "quartermaster": _w_quartermaster, "gunner": _w_gunner,
            "mp": _w_mp, "civilian_city": _w_civilian, "fisherman": _w_fisherman, "patient": _w_patient}


def squadron(r: random.Random, wear: str, actor: dict) -> dict:
    """The spec of a squadron-story actor: `wear` (SQUADRON_WEARS) and `variant` a/b/c (civilian_city also d). The wear fixes who they are; the seed everything else."""
    if wear not in _SQ_WEAR:
        raise ValueError(f"unknown wear {wear!r}: one of {', '.join(SQUADRON_WEARS)}")
    v = str(actor.get("look", actor.get("variant", "a"))).lower()
    v = VARIANT_ALIAS.get(v, v)
    if v not in ("a", "b", "c", "d"):
        v = "a"
    if v == "d" and wear != "civilian_city":
        v = "c"
    spec = _SQ_WEAR[wear](r, v, actor)
    spec["wear"] = wear
    spec["variant"] = v
    return spec


def _squadron_face(spec: dict, chapter: str, aid: str, wear: str, variant: str) -> None:
    """Face traits that make the squadron's people individuals and fit who they are (brows, nose, lips, chin, eyes), from a random stream of their own."""
    r = random.Random(seed_of(chapter, aid) * 53 + 1301)
    f = spec["face"]
    cols = spec["colours"]
    old = f.get("age") == "old"
    pk = r.choice
    if wear == "clerk":  # a small, exact, bird-like face
        f.update(brow=pk(["thin", "arched", "angled", "thin"]), nose=pk(["long", "hooked", "button", "straight"]), lips="thin", chin=pk(["pointed", "round", "pointed"]),
                 jaw=round(r.uniform(0.18, 0.34), 2), eye=pk(["round", "almond", "round"]), wk=pk([0.93, 1.0]), cheek=False, sing=False)
        f["lash"] = 1 if spec.get("curve", 0.3) < 0.55 else 2
    elif wear == "surgeon":  # long, tired, hooded
        f.update(brow=pk(["angled", "thick", "straight"]), nose=pk(["long", "hooked", "straight"]), lips="thin", chin=pk(["square", "pointed", "round"]),
                 jaw=round(r.uniform(0.28, 0.45), 2), eye="hooded", wk=pk([0.93, 1.0]), cheek=True, sing=False, lines=True)
    elif wear == "officer":
        if variant == "a":  # broad, heavy, assured
            f.update(brow="thick", nose=pk(["wide", "hooked", "straight"]), lips=pk(["thin", "full"]), chin="square", jaw=round(r.uniform(0.3, 0.45), 2),
                     eye=pk(["hooded", "almond"]), wk=pk([1.0, 1.04]), cheek=True, sing=False, lines=True)
        elif variant == "b":  # clean, narrow, alert
            f.update(brow=pk(["thin", "arched", "straight"]), nose=pk(["straight", "long", "button"]), lips=pk(["thin", "full"]), chin=pk(["pointed", "round"]),
                     jaw=round(r.uniform(0.15, 0.3), 2), eye=pk(["almond", "round"]), wk=pk([0.93, 1.0]), cheek=False, sing=False)
        else:  # soft, kindly, old
            f.update(brow=pk(["arched", "straight"]), nose=pk(["wide", "straight", "button"]), lips=pk(["full", "thin"]), chin="round", jaw=round(r.uniform(0.15, 0.3), 2),
                     eye=pk(["round", "almond"]), wk=1.0, cheek=False, sing=False, lines=True)
    elif wear == "quartermaster":  # sly, round, a wide mouth, hooded eyes
        f.update(brow=pk(["angled", "arched"]), nose=pk(["long", "wide", "hooked"]), lips="wide", chin=pk(["round", "round", "pointed"]), jaw=round(r.uniform(0.12, 0.3), 2),
                 eye="hooded", wk=pk([1.0, 1.04]), cheek=True, sing=pk([True, False]))
    elif wear == "mp":  # stern
        f.update(brow=pk(["thick", "angled"]), nose=pk(["straight", "wide"]), lips="thin", chin="square", jaw=round(r.uniform(0.32, 0.46), 2), eye=pk(["hooded", "almond"]),
                 cheek=True, sing=False)
    elif wear == "gunner":
        f.update(brow=pk(["straight", "arched", "thin"]), nose="button", lips="thin", chin="round", jaw=round(r.uniform(0.1, 0.2), 2), eye=pk(["round", "round", "almond"]),
                 cheek=False, sing=False)
        f["blush"] = True
    elif wear == "fisherman":
        f.update(brow=pk(["thick", "straight", "angled"]), nose=pk(["wide", "long", "straight"]), eye=pk(["hooded", "almond"]), cheek=True, lines=True if r.random() < 0.6 else f.get("lines", False))
    if wear == "civilian_city" and variant == "d":
        f["sing"] = True
    f["age"] = f.get("age", "adult")
    if wear in ("officer",) and variant == "c":
        f["age"] = "old"


# ---- casting -----------------------------------------------------------------------------------------------------------------------------------------

CHAPTER_FURNITURE = {"night_one": ("#4a3a4c", "#2a2230"), "mothership": ("#8aa0b8", "#4a5a70"), "underworld": ("#3a2a2a", "#1a1010"),
                     "hospital": ("#5a7a8a", "#3a4a5a"), "mental_hospital": ("#6a7a5a", "#3a4a3a"),
                     "airfield": ("#6a5e44", "#463e2c"), "city": ("#5e4e3e", "#3a2e24"), "harbour": ("#3e4e5e", "#26323e")}


PATH_WARDROBES = {"orchard", "birch_hall", "deep_halls", "ash_land"}  # the Ember Road's maps (tools/story/art/wardrobe_ember.py); other paths add theirs here


def dress(chapter: str, actor: dict, salt: int = 0) -> dict:
    aid = str(actor["id"])
    wear = str(actor.get("wear", ""))
    if wear not in SQUADRON_WEARS:  # (the Gospel path names its own `wear` values: only the squadron's ten are this branch)
        wear = ""
    chapter_seed = chapter
    sq_aid = aid
    if chapter in GOSPEL_MAPS:  # a look comes from the seed id: a disciple (d01..d12) wears the same face in every map of the path
        aid = str(actor.get("seed_id", aid))
        sq_aid = aid
        chapter_seed = "gospel" if (aid[0] == "d" and aid[1:].isdigit()) else chapter
    elif chapter in PATH_WARDROBES:  # a named person who stands in several rooms (`person`) is dressed and faced the same in each, on every map of the Ember Road
        aid = str(actor.get("person") or aid)
        sq_aid = aid
        chapter_seed = "ember"
    if wear:  # the squadron's recurring people look the same in every map: seeded by who they are (`same_as` names the first actor of the same person), not by chapter
        chapter_seed, sq_aid = "squadron", str(actor.get("same_as", aid))
    r = random.Random(seed_of(chapter_seed, sq_aid) + salt * 7919)
    arch = str(actor.get("archetype", ""))
    borrowed = str(actor.get("art", "")) == "night_one" or chapter == "night_one"
    # the squadron story's people: a wear and a look (a/b/c/d) come before every other rule
    if wear:
        spec = squadron(r, wear, actor)
    elif chapter in GOSPEL_MAPS:
        spec = gospel(r, actor)
    elif chapter in PATH_WARDROBES:
        from . import wardrobe_ember
        spec = wardrobe_ember.dress(r, str(actor.get("kind", arch)), actor)
    elif borrowed:
        spec = raver(r, arch)
    elif chapter == "mothership":
        spec = alien(r, arch)
    elif chapter == "underworld":
        spec = demon(r, arch)
    elif chapter == "hospital":
        spec = hospital(r, arch, actor)
    else:
        spec = ward(r, arch)
    cols = _base(r, spec["colours"])
    fu = CHAPTER_FURNITURE.get(chapter, ("#4a3e4c", "#2e2634"))
    cols["furn"], cols["furn2"] = fu
    if str(actor.get("activity", "")) == "lie":
        cols["furn"], cols["furn2"] = ("#c8d0dc", "#e8ecf2") if (chapter in ("hospital",) or wear) else ("#8a9a7a", "#c8ccc0")
    spec["colours"] = cols
    spec["seed"] = seed_of(chapter_seed, sq_aid) % 100000
    _face_detail(spec, chapter_seed, sq_aid, arch)
    if wear:
        _squadron_face(spec, chapter_seed, sq_aid, wear, spec.get("variant", "a"))
    return spec


# ---- the face: who this person is around the eyes, nose and mouth ------------------------------------------------------------------------------------
# Drawn from a random stream of its own (the actor's seed with a salt), so adding face traits never changes anyone's clothes, hair or build.

IRIS_DARK = ["#3a2418", "#4a2c1c", "#2e1c14", "#5a3a22"]
IRIS_LIGHT = ["#3a2418", "#5a3a22", "#6a4a2a", "#7a6a3a", "#4a6a4a", "#5a7a9a", "#4a6aa0", "#7a8a96", "#5a8a7a"]
OLD_HAIR = ("#d8d4cf", "#ece8e2", "#b8b4b0", "#c9c3bd")
LIPSTICK = ["#a0283a", "#7a2040", "#c04a5a", "#5a1a2a", "#b0506a", "#2a1a2a"]


def _mix(a: str, b: str, k: float) -> str:
    va = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    vb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(round(x + (y - x) * k)):02x}" for x, y in zip(va, vb))


def _lum(c: str) -> float:
    v = [int(c[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    return 0.3 * v[0] + 0.59 * v[1] + 0.11 * v[2]


def _face_detail(spec: dict, chapter: str, aid: str, arch: str) -> None:
    """Face shape and features per person (people.Painter.face_features reads them): brows, lashes, nose, lips, jaw and chin, cheekbones, head width,
    an age read, a singer who opens their mouth to the music; and the colours of the face: the iris (`extra` for people, a spare slot they do not use),
    lips (`mouth`) and blush (`skin2`) from the skin tone, the skin's undertone (people.skin_ramp)."""
    r = random.Random(seed_of(chapter, aid) * 31 + 977)
    f = spec.setdefault("face", {})
    cols = spec["colours"]
    species = (spec.get("species") or {}).get("kind", "")
    hc = cols.get("hair", "#2a1c18")
    old = hc in OLD_HAIR or arch in ("granny",)
    kid = arch == "kid" or float(spec.get("head", 1.0)) > 1.2 and float(spec.get("height", 1.0)) < 0.8 and not species
    curve = float(spec.get("curve", 0.5))
    fem = curve > 0.55
    f["age"] = "kid" if kid else ("old" if old else "adult")
    f["brow"] = r.choice(["straight", "arched", "thick", "thin", "angled", "straight", "arched"] if not fem else ["arched", "thin", "arched", "straight", "thick"])
    f["lash"] = 2 if (fem and r.random() < 0.75) else (1 if r.random() < 0.6 else 0)
    f["nose"] = r.choice(["button", "straight", "wide", "long", "hooked", "straight"] if not kid else ["button", "button", "wide"])
    f["lips"] = r.choice(["thin", "full", "wide", "full", "thin"]) if not kid else "thin"
    f["jaw"] = round(r.uniform(0.12, 0.42) if not fem else r.uniform(0.3, 0.5), 2)
    f["chin"] = r.choice(["round", "square", "pointed", "round"] if not fem else ["round", "pointed", "round"])
    f["cheek"] = r.random() < 0.4
    f["wk"] = r.choice([0.93, 1.0, 1.0, 1.04])
    f["eye"] = r.choice(["almond", "round", "hooded", "almond"])
    f["sing"] = r.random() < 0.45
    f["lines"] = old
    if species:
        if chapter == "underworld" and species != "skeleton":  # demon eyes: a hot sclera around a dark pupil
            cols["eye_w"] = r.choice(["#f0c040", "#ffa040", "#f06a3a", "#f0d870"])
        if species in ("antenna", "tentacle", "blob"):
            cols["eye_w"] = r.choice(["#e8f0f0", "#f0f0d0", "#d8f0ff"])
        if chapter == "mothership":
            cols["mouth"] = _darker(cols.get("skin", "#8fe07a"), 0.5)
        return
    skin = cols.get("skin", "#c98c62")
    lum = _lum(skin)
    cols["extra"] = r.choice(IRIS_DARK) if lum < 0.5 else r.choice(IRIS_LIGHT)
    lip = _mix(skin, "#a03848" if lum > 0.45 else "#6a2430", 0.42 if lum > 0.45 else 0.35)
    if lum < 0.36:
        lip = _mix(_darker(skin, 0.18), "#7a3040", 0.3)
    if fem and not kid and r.random() < 0.3 and chapter in ("night_one", "mental_hospital", "hospital"):
        lip = r.choice(LIPSTICK)
    cols["mouth"] = lip
    cols["skin2"] = _mix(skin, "#e05060", 0.32 if lum > 0.5 else 0.22)
    cols["skin_tone"] = r.choice(["warm", "warm", "neutral", "olive", "cool"]) if lum > 0.42 else r.choice(["warm", "neutral", "warm"])
    cols["eye_w"] = _mix("#e8e0d8", skin, 0.12)
    cols["teeth"] = _mix("#efe8dc", skin, 0.15)


def look_key(spec: dict) -> tuple:
    """What two people in a room may not share: build (height and width class), hair (style) and top (kind and pattern)."""
    h = round(float(spec.get("height", 1.0)) * 10)
    w = round(float(spec.get("width", 1.0)) * 6)
    hair = (spec.get("hair") or {}).get("style", "")
    top = spec.get("top") or {}
    return (h, w, hair, top.get("kind", ""), top.get("pattern", ""))


def cast_chapter(chapter: str, actors: list) -> dict:
    """{actor id: spec} for the chapter's actors, re-rolling (deterministically) anyone whose look repeats someone's in the same room."""
    out: dict = {}
    seen: dict = {}
    for a in actors:
        room = str(a.get("view", "main"))
        keys = seen.setdefault(room, set())
        for salt in range(40):
            spec = dress(chapter, a, salt)
            k = look_key(spec)
            if k not in keys or a.get("fixed"):  # (a recurring named person is never re-rolled: they must look the same in every room and map)
                break
        keys.add(k)
        out[str(a["id"])] = spec
    return out
