#!/usr/bin/env python3
"""Authors the Gospel path (docs/THREE_PATHS_AND_FACES_PLAN.md section 4, Stage 3): content/paths/gospel/{run.json, music.json, hotspots/<world>.json, prompts.json}.

    python3 tools/story/art/gospel_maps.py            # (or tools/story/build_gospel_art.py) the maps this reads the places of
    python3 tools/content/make_gospel.py              # run.json, hotspots, cinematics, music.json (placeholder entries), prompts.json
    python3 tools/content/make_path_placeholders.py gospel
    python3 tools/content/make_gospel.py --music-only # puts the owner's music prompts back into music.json (the placeholder writer rewrites the entries)

17 scenes in four worlds (jordan, galilee, road, jerusalem: one map each), 124 BPM. Every scene is a view of its map (tools/story/art/gospel_maps.py); the table below is the plan's 4.2:
the touches with their success and failure, the `cast` lines (what the faces say), the character hotspots' `acting`, the set pieces a scene or a result switches, and the music prompt
(verbatim from the owner's brief). No text anywhere in play: nothing here is a caption.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "story"))
sys.path.insert(0, str(ROOT / "tools" / "run"))

from art import gospel_maps  # noqa: E402
from acting_data import L, a  # noqa: E402

OUT = ROOT / "content" / "paths" / "gospel"
gospel_maps.build_all(False)
IDX = gospel_maps.INDEX
CAM = "camera"


# ---- vocabulary -------------------------------------------------------------------------------------------------------------------------------------
def A(view, local):
    return IDX[view]["actors"][local]["id"]


def TH(view, local):
    return IDX[view]["things"][local]


def WP(view, name):
    return IDX[view]["waypoints"][name]


def PC(view, local):
    return f"{view}.{local}"


def out(route=None, flags=(), cin=None, energy=None, pieces=None, music=None):
    o = {}
    if route:
        o["route"] = route
    if flags:
        o["flags_set"] = list(flags)
    if cin:
        o["cinematic"] = cin
    if energy:
        o["energy"] = energy
    if pieces:
        o["pieces"] = pieces
    if music:
        o["music"] = music
    return o


def avail(all=(), none=(), energy_min=0, once=False):
    return {"flags_all": list(all), "flags_none": list(none), "energy_min": energy_min, "once": once}


LOOKS = {"exit": "open", "character": "beckon", "object": "glow", "feature": "pulse", "encounter": "flicker", "secret": "pulse"}

# ---- the scenes ---------------------------------------------------------------------------------------------------------------------------------------
# (node id, scene name, world, view, entry, exit_scene, ending, title, routes [(to, dir)], the plan's music prompt)
P_TAIL = " Separate editable MIDI tracks."
SCENES = [
    ("jordan", "bethlehem", "jordan", "bank_night", True, False, "", "Bethlehem: the Star", [("jordan.baptism", "up")],
     "124 BPM soulful house, 8-bar seamless loop. Soft kick, dusty claps, warm organ, gentle plucks, choir-like synth and rounded bass."),
    ("jordan.baptism", "baptism", "jordan", "bank_dawn", False, False, "", "Baptism in the Jordan", [("jordan.nazareth", "up"), ("jordan.wilderness", "right")],
     "124 BPM uplifting gospel house, 8-bar seamless loop. Shimmering keys, warm bass, handclaps, four-on-floor kick and sparkling water percussion."),
    ("jordan.wilderness", "wilderness", "jordan", "rocks", False, True, "", "Temptation in the Wilderness", [("galilee", "up"), ("galilee.capernaum", "right")],
     "124 BPM minimal deep house, 8-bar seamless loop. Dry kick, hollow percussion, sparse organ, uneasy bass pulse and desert-wind synth."),
    ("jordan.nazareth", "nazareth", "jordan", "workshop", False, True, "", "Nazareth Workshop", [("galilee", "up"), ("galilee.capernaum", "right")],
     "124 BPM organic house, 8-bar seamless loop. Wooden percussion, warm piano chords, mellow bass, soft shaker and gentle handclaps."),
    ("galilee", "lakeshore", "galilee", "lakeshore", True, False, "", "Calling the Fishermen", [("galilee.mount", "up"), ("galilee.storm", "right")],
     "124 BPM funky house, 8-bar seamless loop. Bouncy bass, crisp claps, rhythmic guitar-like synth, bright organ and rolling hi-hats."),
    ("galilee.capernaum", "capernaum", "galilee", "street", True, True, "", "Healing in Capernaum", [("galilee.mount", "up"), ("road", "right")],
     "124 BPM soulful deep house, 8-bar seamless loop. Tender electric piano, rounded bass, soft drums, hopeful strings and delicate melodic responses."),
    ("galilee.mount", "mount", "galilee", "slope", False, True, "", "Sermon on the Mount", [("road.loaves", "up"), ("galilee.storm", "right")],
     "124 BPM joyful gospel house, 8-bar seamless loop. Rich organ chords, celebratory claps, melodic bass, uplifting piano and spacious choir-like synth."),
    ("galilee.storm", "storm", "galilee", "storm", False, True, "", "Storm on Galilee", [("road.loaves", "up"), ("road", "right")],
     "124 BPM dark progressive house, 8-bar seamless loop. Thunderous kick, rolling toms, tense sub-bass, stormy pads and urgent arpeggios."),
    ("road", "bethany", "road", "courtyard", True, False, "", "Bethany: the Shared Table", [("road.loaves", "up"), ("road.entry", "right")],
     "124 BPM warm soulful house, 8-bar seamless loop. Gentle Rhodes, soft kick, hand percussion, expressive bass and intimate organ chords."),
    ("road.loaves", "loaves", "road", "hill_dusk", True, False, "", "Loaves and Fishes", [("road.entry", "up"), ("road", "left")],
     "124 BPM euphoric gospel house, 8-bar seamless loop. Layered piano stabs, warm bass, claps, jubilant synth harmonies and uplifting four-on-floor drums."),
    ("road.entry", "entry", "road", "gate", False, True, "", "Entry into Jerusalem", [("jerusalem", "up"), ("jerusalem.gethsemane", "left")],
     "124 BPM festival house, 8-bar seamless loop. Triumphant brass-like synths, driving kick, crowd-style percussion, bright organ and energetic bass."),
    ("jerusalem", "temple", "jerusalem", "temple", True, False, "", "The Temple", [("jerusalem.gethsemane", "up"), ("jerusalem.trial", "right")],
     "124 BPM tense tech house, 8-bar seamless loop. Metallic percussion, sharp claps, distorted bass, clipped organ stabs and escalating rhythmic tension."),
    ("jerusalem.gethsemane", "gethsemane", "jerusalem", "grove", True, False, "", "Gethsemane", [("jerusalem.trial", "up"), ("jerusalem.road", "right")],
     "124 BPM melancholic deep house, 8-bar seamless loop. Muted kick, sparse piano, low bass heartbeat, haunting pads and restrained percussion."),
    ("jerusalem.trial", "trial", "jerusalem", "praetorium", False, False, "", "The Trial", [("jerusalem.golgotha", "up"), ("jerusalem.road", "right")],
     "124 BPM cinematic dark house, 8-bar seamless loop. Heavy kick, ominous organ, slow chord changes, deep bass and tense metallic percussion."),
    ("jerusalem.golgotha", "golgotha", "jerusalem", "hill", False, False, "", "Golgotha", [("jerusalem.tomb", "up")],
     "124 BPM atmospheric minimal house, 8-bar seamless loop. Sparse kick, distant bells, solemn organ, subdued sub-bass and slowly rising ambient strings."),
    ("jerusalem.tomb", "tomb", "jerusalem", "tomb", False, False, "tomb", "The Empty Tomb", [("run:warehouse", "up")],
     "124 BPM uplifting melodic house, 8-bar seamless loop. Radiant piano, warm bass, soaring choir-like pads, bright claps and expansive harmonies."),
    ("jerusalem.road", "road_beyond", "jerusalem", "road", False, False, "road", "The Road Beyond Jerusalem", [("run:warehouse", "up")],
     "124 BPM reflective organic house, 8-bar seamless loop. Gentle percussion, warm acoustic plucks, wandering bass melody, soft piano and hopeful atmospheric pads."),
]
SCENE = {s[0]: s for s in SCENES}
VIEW_OF = {s[0]: s[3] for s in SCENES}
WORLD_OF = {s[0]: s[2] for s in SCENES}

WORLDS = [
    {"id": "jordan", "title": "The Jordan", "map": "galilee_shore", "depth": 1, "story": "res://content/story/galilee_shore.json", "blurb": "A night road, a river at dawn, the wilderness, a workshop door."},
    {"id": "galilee", "title": "Galilee", "map": "hillside", "depth": 2, "story": "res://content/story/hillside.json", "blurb": "Nets and boats, a village street, the hillside, a storm on the lake."},
    {"id": "road", "title": "The Road to Jerusalem", "map": "bethany", "depth": 3, "story": "res://content/story/bethany.json", "blurb": "A shared table, a hill at dusk, the gate with palms."},
    {"id": "jerusalem", "title": "Jerusalem", "map": "jerusalem", "depth": 4, "story": "res://content/story/jerusalem.json", "blurb": "The temple, the olive grove, the court, the hill, the garden, the road."},
]

CINEMATICS: dict = {}
HOTSPOTS: dict = {w["id"]: [] for w in WORLDS}


def walk(to, role="queasy", style="walk", bars=2, look=None):
    s = {"move": "walk", "to": to, "bars": bars, "role": role, "style": style}
    if look:
        s["look_at"] = look
    return s


def cinematic(scene, name, steps, cast=None):
    full = f"gospel.{name}"
    c = {"world": WORLD_OF[scene], "steps": steps}
    if cast:
        c["cast"] = cast
    CINEMATICS[full] = c
    return full


def hs(scene, name, kind, anchor, s, f, *, default=False, av=None, radius=0.8, acting=None, look=None, repeatable=True, min_px=72):
    world = WORLD_OF[scene]
    mp = next(w["map"] for w in WORLDS if w["id"] == world)
    h = {"id": f"{scene}.{name}", "world": world, "scene": scene, "map": mp, "anchor": anchor, "kind": kind, "radius_m": radius, "min_px": min_px, "available": av or avail(),
         "look": {"available": look or LOOKS[kind], "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": s, "on_failure": f, "default": default, "repeatable": repeatable}
    if acting:
        h["acting"] = acting
    HOTSPOTS[world].append(h)
    return h


def exit_hs(scene, name, anchor, to, *, default=False, acting=None, radius=1.0, f_energy=-5, look=None):
    """An exit: the same way on whatever the play (a failed one staggers through the same door)."""
    view = VIEW_OF[scene]
    stagger = cinematic(scene, f"stagger_{scene.replace('.', '_')}_{name}", [walk(WP(view, "door_up") if anchor.get("waypoint") is None else anchor["waypoint"], "queasy", "stagger", 2)])
    return hs(scene, name, "exit", anchor, out(route=to), out(route=to, cin=stagger, energy=f_energy), default=default, radius=radius, acting=acting, look=look or ("open" if default else "glow"))


def W(view, name):
    return {"waypoint": WP(view, name)}


def Tg(view, local):
    return {"thing": TH(view, local)}


def Ac(view, local):
    return {"actor": A(view, local)}


# ======================================================================================================================================================
# the scenes' touches
# ======================================================================================================================================================
CAST: dict = {}
PIECES: dict = {}  # scene -> {"on": [...]}
BLOCK_FX: dict = {}

# ---- J00 Bethlehem: the Star (the one lit way is the road; the shepherds are the second touch, so the scene still shows two) ---------------------------------------
v = "bank_night"
exit_hs("jordan", "road", W(v, "door_up"), "jordan.baptism", default=True)
hs("jordan", "shepherd", "character", Ac(v, "sh2"), out(flags=["gospel_shepherds"], energy=6), out(energy=-4),
   acting={"actor": A(v, "sh2"), "available": a("beckon", "awe", CAM), "selected": a("bow", "awe"), "committed": a("kneel", "awe", beats=4), "success": a("kneel", "awe", beats=8, then=a("stare", "relief", CAM, 8)),
           "failure": a("shake_head", "doubt", beats=6)})
CAST["jordan"] = [L(A(v, "sh1"), 0, "kneel", "awe", CAM, 16), L(A(v, "sh3"), 0, "kneel", "awe", CAM, 16), L(A(v, "m1"), 16, "stare", "relief", CAM, 16),
                  L(A(v, "sh1"), 32, "bow", "awe", beats=12), L(A(v, "el1"), 48, "nod", "happy", A(v, "m1"), 10)]
PIECES["jordan"] = {"on": [PC(v, "star")]}

# ---- J01 Baptism in the Jordan ------------------------------------------------------------------------------------------------------------------------
v = "bank_dawn"
exit_hs("jordan.baptism", "nazareth", Tg(v, "town"), "jordan.nazareth", default=True)
hs("jordan.baptism", "dove", "feature", Tg(v, "dove"), out(route="jordan.wilderness", flags=["gospel_baptised"], energy=6), out(route="jordan.nazareth", energy=-4), radius=1.2,
   acting={"actor": A(v, "b1"), "available": a("bow", "awe"), "selected": a("bow", "awe"), "committed": a("point", "resolve", WP(v, "door_right"), 4),
           "success": a("point", "resolve", WP(v, "door_right"), 8), "failure": a("shake_head", "doubt", beats=6)})
CAST["jordan.baptism"] = [L(A(v, "b1"), 0, "bow", "awe", CAM, 12), L(A(v, "b1"), 32, "point", "resolve", WP(v, "door_right"), 12),
                          L(A(v, "v2"), 16, "cheer", "cheer", beats=12, if_energy_above=55), L(A(v, "v3"), 16, "cheer", "cheer", beats=12, if_energy_above=55),
                          L(A(v, "v1"), 40, "shake_head", "doubt", beats=10, if_energy_below=45), L(A(v, "v4"), 48, "stare", "awe", CAM, 12)]
PIECES["jordan.baptism"] = {"on": [PC(v, "dove")]}

# ---- J02 Temptation in the Wilderness: both touches are ways out; the tempter reacts to either --------------------------------------------------------------
v = "rocks"
t1 = A(v, "t1")
tempter = lambda: {"actor": t1, "available": a("offer", "happy", CAM), "selected": a("stare", "doubt", CAM), "committed": a("shake_head", "doubt", beats=4),
                   "success": a("recoil", "anger", beats=8, then=a("shake_head", "anger", beats=8)), "failure": a("laugh", "laugh", beats=8)}
exit_hs("jordan.wilderness", "path", W(v, "door_up"), "galilee", default=True, acting=tempter())
exit_hs("jordan.wilderness", "fires", Tg(v, "fires"), "galilee.capernaum", acting=tempter())
CAST["jordan.wilderness"] = [L(t1, 0, "stare", "doubt", CAM, 16), L(t1, 16, "offer", "happy", CAM, 14), L(t1, 32, "laugh", "laugh", beats=12, if_energy_below=50),
                             L(t1, 48, "shake_head", "doubt", beats=12, if_energy_above=50)]

# ---- J03 Nazareth Workshop ---------------------------------------------------------------------------------------------------------------------------
v = "workshop"
exit_hs("jordan.nazareth", "road", W(v, "door_up"), "galilee", default=True)
hs("jordan.nazareth", "neighbour", "character", Ac(v, "n1"), out(route="galilee.capernaum", energy=5), out(route="galilee", energy=-4),
   acting={"actor": A(v, "n1"), "available": a("plead", "plea", CAM), "selected": a("plead", "plea", CAM), "committed": a("plead", "plea", beats=4),
           "success": a("nod", "relief", beats=8), "failure": a("shake_head", "shame", beats=8, then=a("stare", "shame", beats=8))})
hs("jordan.nazareth", "cart", "object", Tg(v, "cart"), out(route="galilee", energy=5), out(route="galilee.capernaum", energy=-4))
CAST["jordan.nazareth"] = [L(A(v, "c1"), 0, "write", "neutral", beats=16), L(A(v, "c1"), 32, "nod", "happy", beats=10), L(A(v, "n1"), 16, "plead", "plea", CAM, 14),
                           L(A(v, "v1"), 48, "watch", "neutral", TH(v, "cart"), 12)]

# ---- J04 Calling the Fishermen -------------------------------------------------------------------------------------------------------------------------
v = "lakeshore"
f1, f2 = A(v, "f1"), A(v, "f2")
exit_hs("galilee", "mount", W(v, "door_up"), "galilee.mount", default=True)
hs("galilee", "fishermen", "character", Ac(v, "f1"), out(route="galilee.mount", flags=["gospel_called"], energy=8), out(route="galilee.storm", energy=-4),
   acting={"actor": f1, "available": a("stare", "awe", CAM), "selected": a("stare", "awe", CAM), "committed": a("nod", "awe", beats=4), "success": a("cheer", "cheer", beats=8, then=a("nod", "happy", beats=8)),
           "failure": a("shake_head", "doubt", beats=8, then=a("check", "doubt", beats=8))})
hs("galilee", "boat", "object", Tg(v, "boat_far"), out(route="galilee.storm", energy=5), out(route="galilee.mount", energy=-4))
CAST["galilee"] = [L(f1, 0, "stare", "neutral", CAM, 16), L(f2, 0, "stare", "neutral", CAM, 16), L(f1, 16, "stare", "awe", CAM, 16), L(f2, 32, "stare", "awe", CAM, 16),
                   L(f2, 61, "cheer", "cheer", beats=4, if_flags_all=["gospel_called"]), L(A(v, "f4"), 61, "cheer", "cheer", beats=3, if_flags_all=["gospel_called"])]

# ---- J05 Healing in Capernaum (the setback cinematic: the elder leads the camera out) --------------------------------------------------------------------------
v = "street"
p1, p2, k1, e1 = A(v, "p1"), A(v, "p2"), A(v, "k1"), A(v, "e1")
led_out = cinematic("galilee.capernaum", "led_out", [walk(WP(v, "door_up"), "queasy", "stagger", 3, look=e1)],
                    cast=[L(e1, 0, "shake_head", "doubt", CAM, 8), L(p2, 0, "cover_face", "grief", beats=10), L(p1, 2, "collapse", "grief", beats=10)])
exit_hs("galilee.capernaum", "mount", W(v, "door_up"), "galilee.mount", default=True)
hs("galilee.capernaum", "family", "character", Ac(v, "p2"), out(route="galilee.mount", flags=["gospel_healed"], energy=10), out(route="galilee.mount", cin=led_out, energy=-8),
   acting={"actor": p2, "available": a("plead", "plea", CAM), "selected": a("plead", "fear", CAM), "committed": a("plead", "plea", beats=4), "success": a("collapse", "relief", beats=8, then=a("cheer", "cheer", beats=8)),
           "failure": a("cover_face", "grief", beats=8)})
exit_hs("galilee.capernaum", "caravan", Tg(v, "caravan"), "road")
CAST["galilee.capernaum"] = [L(p1, 0, "plead", "fear", CAM, 16), L(p2, 0, "plead", "plea", CAM, 16), L(p1, 32, "plead", "plea", CAM, 16), L(e1, 48, "stare", "doubt", CAM, 12),
                             L(k1, 61, "sit", "happy", beats=3, if_flags_all=["gospel_healed"]), L(p1, 61, "collapse", "relief", beats=3, if_flags_all=["gospel_healed"])]

# ---- J06 Sermon on the Mount ----------------------------------------------------------------------------------------------------------------------------
v = "slope"
exit_hs("galilee.mount", "loaves", W(v, "door_up"), "road.loaves", default=True)
hs("galilee.mount", "crowd", "feature", Ac(v, "c4"), out(route="road.loaves", flags=["gospel_mount_heard"], energy=8), out(route="galilee.storm", energy=-4), radius=1.2,
   acting={"actor": A(v, "c4"), "available": a("sit", "awe", CAM), "selected": a("sit", "awe", CAM), "committed": a("nod", "awe", beats=4), "success": a("cheer", "cheer", beats=8), "failure": a("sad", "sad", beats=8)})
hs("galilee.mount", "boat", "object", Tg(v, "boat_far"), out(route="galilee.storm", energy=5), out(route="road.loaves", energy=-4))
CAST["galilee.mount"] = [L(A(v, "c1"), 0, "sit", "awe", CAM, 16), L(A(v, "c3"), 0, "sit", "awe", CAM, 16), L(A(v, "c5"), 16, "sit", "awe", CAM, 16), L(A(v, "h1"), 16, "laugh", "laugh", beats=12),
                         L(A(v, "d02"), 48, "point", "resolve", TH(v, "boat_far"), 12), L(A(v, "h1"), 61, "cover_face", "shame", beats=3, if_flags_all=["gospel_mount_heard"])]

# ---- J07 Storm on Galilee ------------------------------------------------------------------------------------------------------------------------------
v = "storm"
d03 = A(v, "d03")
exit_hs("galilee.storm", "loaves", W(v, "door_up"), "road.loaves", default=True)
exit_hs("galilee.storm", "south", W(v, "door_right"), "road")
hs("galilee.storm", "beacon", "feature", Tg(v, "beacon"), out(route="road.loaves", flags=["gospel_calm"], energy=8, pieces={"off": [PC(v, "storm_cloud"), PC(v, "rain"), PC(v, "lightning")]}),
   out(route="road", energy=-6), radius=1.2,
   acting={"actor": d03, "available": a("plead", "fear", CAM), "selected": a("plead", "plea", CAM), "committed": a("recoil", "fear", beats=4), "success": a("stare", "relief", beats=8, then=a("stare", "awe", beats=8)),
           "failure": a("collapse", "grief", beats=8)})
CAST["galilee.storm"] = [L(A(v, "d01"), 0, "recoil", "fear", CAM, 16), L(A(v, "d05"), 0, "recoil", "fear", CAM, 16), L(A(v, "d02"), 16, "plead", "plea", CAM, 16),
                         L(A(v, "d06"), 32, "plead", "fear", CAM, 16), L(A(v, "d04"), 61, "stare", "awe", beats=3, if_flags_all=["gospel_calm"]), L(A(v, "d02"), 61, "stare", "relief", beats=3, if_flags_all=["gospel_calm"])]
PIECES["galilee.storm"] = {"on": [PC(v, "storm_cloud"), PC(v, "rain"), PC(v, "lightning")]}

# ---- J08 Bethany: the Shared Table -----------------------------------------------------------------------------------------------------------------------
v = "courtyard"
s1, s2, d12 = A(v, "s1"), A(v, "s2"), A(v, "d12")
exit_hs("road", "loaves", W(v, "door_up"), "road.loaves", default=True)
hs("road", "table", "character", Ac(v, "s1"), out(route="road.loaves", flags=["gospel_table"], energy=8), out(route="road.entry", energy=-4),
   acting={"actor": s1, "available": a("offer", "happy", CAM), "selected": a("offer", "happy", CAM), "committed": a("offer", "happy", beats=4), "success": a("nod", "happy", beats=8),
           "failure": a("shake_head", "doubt", beats=8)})
hs("road", "donkey", "object", Tg(v, "donkey"), out(route="road.entry", energy=5), out(route="road.loaves", energy=-4))
CAST["road"] = [L(s1, 0, "offer", "happy", CAM, 16), L(s2, 0, "stare", "doubt", CAM, 16), L(s2, 32, "write", "doubt", beats=12), L(d12, 32, "stare", "shame", WP(v, "door_right"), 20),
                L(s1, 48, "offer", "happy", CAM, 12)]

# ---- J09 Loaves and Fishes ---------------------------------------------------------------------------------------------------------------------------
v = "hill_dusk"
tr1 = A(v, "tr1")
exit_hs("road.loaves", "entry", W(v, "door_up"), "road.entry", default=True)
hs("road.loaves", "baskets", "object", Tg(v, "basket2"), out(route="road.entry", flags=["gospel_fed"], energy=9, pieces={"on": [PC(v, "full1"), PC(v, "full2"), PC(v, "full3")]}),
   out(route="road", flags=["gospel_hungry"], energy=-5), radius=1.2)
hs("road.loaves", "lantern", "character", Ac(v, "tr1"), out(route="road", energy=4), out(route="road.entry", energy=-4),
   acting={"actor": tr1, "available": a("beckon", "happy", CAM), "selected": a("beckon", "happy", CAM), "committed": a("point", "resolve", WP(v, "door_left"), 4), "success": a("nod", "happy", beats=8),
           "failure": a("shake_head", "doubt", beats=8)})
CAST["road.loaves"] = [L(A(v, "c2"), 0, "plead", "plea", CAM, 16), L(A(v, "c5"), 16, "plead", "plea", CAM, 16), L(A(v, "c1"), 32, "plead", "plea", CAM, 16), L(A(v, "c7"), 32, "plead", "plea", CAM, 16),
                       L(A(v, "c3"), 61, "cheer", "cheer", beats=3, if_flags_all=["gospel_fed"]), L(A(v, "c6"), 61, "laugh", "laugh", beats=3, if_flags_all=["gospel_fed"]),
                       L(A(v, "c4"), 61, "shake_head", "sad", beats=3, if_flags_all=["gospel_hungry"]), L(A(v, "c8"), 61, "sad", "sad", beats=3, if_flags_all=["gospel_hungry"])]

# ---- J10 Entry into Jerusalem -----------------------------------------------------------------------------------------------------------------------------
v = "gate"
exit_hs("road.entry", "steps", W(v, "door_up"), "jerusalem", default=True)
exit_hs("road.entry", "grove", W(v, "door_left"), "jerusalem.gethsemane")
CAST["road.entry"] = [L(A(v, "pr1"), 0, "block", "anger", CAM, 16), L(A(v, "pr2"), 0, "block", "anger", CAM, 16), L(A(v, "k1"), 16, "offer", "happy", CAM, 16), L(A(v, "cr2"), 32, "cheer", "cheer", beats=14),
                      L(A(v, "pr1"), 48, "stamp", "anger", beats=12, if_energy_above=60), L(A(v, "cr5"), 48, "cheer", "cheer", beats=12)]

# ---- J11 The Temple ------------------------------------------------------------------------------------------------------------------------------------
v = "temple"
mc1, mc2, mc3, pr1, pr2, g1, g2 = (A(v, x) for x in ("mc1", "mc2", "mc3", "pr1", "pr2", "g1", "g2"))
walked_out = cinematic("jerusalem", "walked_out", [walk(WP(v, "door_right"), "queasy", "stagger", 3, look=g1)], cast=[L(g1, 0, "block", "anger", CAM, 8), L(g2, 0, "block", "anger", CAM, 8), L(mc2, 2, "laugh", "laugh", beats=8)])
exit_hs("jerusalem", "garden", W(v, "door_up"), "jerusalem.gethsemane", default=True)
hs("jerusalem", "tables", "object", Tg(v, "t2_up"), out(route="jerusalem.gethsemane", flags=["gospel_tables"], energy=6, pieces={"on": [PC(v, "t1_over"), PC(v, "t2_over"), PC(v, "t3_over")],
                                                                                                                       "off": [PC(v, "t1_up"), PC(v, "t2_up"), PC(v, "t3_up")]}),
   out(route="jerusalem.trial", cin=walked_out, energy=-6), radius=1.4)
hs("jerusalem", "guards", "encounter", Ac(v, "g1"), out(route="jerusalem.trial", energy=3), out(route="jerusalem.gethsemane", energy=-4),
   acting={"actor": g1, "available": a("stare", "resolve", CAM), "selected": a("block", "anger", CAM), "committed": a("block", "anger", beats=4), "success": a("salute", "resolve", beats=8),
           "failure": a("stamp", "anger", beats=8)})
CAST["jerusalem"] = [L(mc1, 0, "write", "neutral", beats=16), L(mc2, 16, "laugh", "laugh", beats=14), L(mc3, 32, "write", "neutral", beats=14), L(g1, 48, "stare", "resolve", CAM, 12),
                     L(mc1, 61, "recoil", "fear", beats=3, if_flags_all=["gospel_tables"]), L(mc2, 61, "recoil", "fear", beats=3, if_flags_all=["gospel_tables"]),
                     L(pr1, 61, "stamp", "anger", beats=3, if_flags_all=["gospel_tables"]), L(pr2, 61, "stamp", "anger", beats=3, if_flags_all=["gospel_tables"])]
PIECES["jerusalem"] = {"on": [PC(v, "t1_up"), PC(v, "t2_up"), PC(v, "t3_up")]}

# ---- J12 Gethsemane ----------------------------------------------------------------------------------------------------------------------------------
v = "grove"
d09, d10, d11, d12g, gg1, gg2, gg3 = (A(v, x) for x in ("d09", "d10", "d11", "d12", "g1", "g2", "g3"))
exit_hs("jerusalem.gethsemane", "trial", W(v, "door_up"), "jerusalem.trial", default=True)
hs("jerusalem.gethsemane", "sleepers", "character", Ac(v, "d10"), out(route="jerusalem.trial", energy=3), out(route="jerusalem.road", energy=-4),
   acting={"actor": d10, "available": a("sleep", "neutral"), "selected": a("sit", "fear", CAM), "committed": a("recoil", "fear", beats=4), "success": a("nod", "shame", beats=8), "failure": a("cover_face", "shame", beats=8)})
exit_hs("jerusalem.gethsemane", "shadowed", W(v, "door_right"), "jerusalem.road")
CAST["jerusalem.gethsemane"] = [L(d11, 32, "sit", "shame", CAM, 16), L(d12g, 48, "nod", "resolve", gg1, 12), L(gg1, 48, "block", "anger", CAM, 14), L(gg2, 48, "block", "anger", CAM, 14),
                                L(d12g, 56, "point", "resolve", CAM, 8), L(gg3, 56, "stare", "neutral", CAM, 8)]

# ---- J13 The Trial ---------------------------------------------------------------------------------------------------------------------------------------
v = "praetorium"
gov, sc1, w1 = A(v, "gov"), A(v, "sc1"), A(v, "w1")
exit_hs("jerusalem.trial", "passage", W(v, "door_up"), "jerusalem.golgotha", default=True)
exit_hs("jerusalem.trial", "gate", W(v, "door_right"), "jerusalem.road")
CAST["jerusalem.trial"] = [L(gov, 0, "write", "neutral", beats=16), L(gov, 16, "shake_head", "doubt", beats=14), L(gov, 32, "offer", "resolve", TH(v, "bowl"), 14), L(A(v, "cr2"), 32, "stamp", "anger", beats=14),
                           L(A(v, "cr4"), 32, "stamp", "anger", beats=14), L(A(v, "cr6"), 40, "stamp", "anger", beats=10), L(w1, 48, "cover_face", "grief", beats=14), L(sc1, 16, "write", "neutral", beats=12)]

# ---- J14 Golgotha: on rails; the staging follows the play (block_fx) ------------------------------------------------------------------------------------------
v = "hill"
w1h, w2h, w3h, s1h, s2h, s3h, x1, x2, x3 = (A(v, x) for x in ("w1", "w2", "w3", "s1", "s2", "s3", "x1", "x2", "x3"))
exit_hs("jerusalem.golgotha", "hill", W(v, "door_up"), "jerusalem.tomb", default=True)
hs("jerusalem.golgotha", "women", "character", Ac(v, "w1"), out(flags=["gospel_stayed"], energy=6), out(energy=-3),
   acting={"actor": w1h, "available": a("cover_face", "grief"), "selected": a("kneel", "grief"), "committed": a("kneel", "grief", beats=4), "success": a("kneel", "grief", beats=8, then=a("stare", "relief", CAM, 8)),
           "failure": a("cover_face", "grief", beats=8)})
CAST["jerusalem.golgotha"] = [L(w1h, 0, "cover_face", "grief", beats=16), L(w2h, 0, "cover_face", "grief", beats=16), L(w3h, 16, "kneel", "grief", beats=16), L(s1h, 0, "stare", "neutral", CAM, 16),
                              L(s3h, 32, "stare", "neutral", CAM, 24), L(s3h, 60, "stare", "awe", CAM, 4), L(w2h, 40, "cover_face", "grief", beats=16)]
BLOCK_FX["jerusalem.golgotha"] = [
    {"block": 0, "pass": {"pieces": {"on": [PC(v, "dark1")]}, "cast": [L(x1, 0, "kneel", "grief", CAM, 14)]}, "miss": {"pieces": {"on": [PC(v, "dark1")]}, "cast": [L(s1h, 0, "laugh", "laugh", beats=10)]}},
    {"block": 1, "pass": {"pieces": {"on": [PC(v, "dark2")]}, "cast": [L(x2, 0, "kneel", "grief", CAM, 14)]}, "miss": {"pieces": {"on": [PC(v, "dark2")]}, "cast": [L(s2h, 0, "laugh", "laugh", beats=10)]}},
    {"block": 2, "pass": {"pieces": {"on": [PC(v, "dark3")]}, "cast": [L(x3, 0, "kneel", "grief", CAM, 14)]}, "miss": {"pieces": {"on": [PC(v, "dark3")]}, "cast": [L(s3h, 0, "laugh", "laugh", beats=10)]}},
    {"block": 3, "pass": {"cast": [L(x1, 0, "bow", "grief", beats=3)]}, "miss": {"cast": [L(s1h, 0, "laugh", "laugh", beats=3)]}},
]

# ---- J15 The Empty Tomb (ending: tomb) ----------------------------------------------------------------------------------------------------------------------
v = "tomb"
tw1, tw2, tw3, gd1 = (A(v, x) for x in ("w1", "w2", "w3", "gd1"))
keep_tomb = ["keep:path_gospel_tomb"]
hs("jerusalem.tomb", "home", "exit", W(v, "door_up"), out(route="run:warehouse", flags=keep_tomb), out(route="run:warehouse", flags=keep_tomb, energy=-3), default=True, radius=1.0, look="open")
hs("jerusalem.tomb", "stone", "feature", Tg(v, "stone_rolled"), out(route="run:warehouse", flags=keep_tomb, energy=8), out(route="run:warehouse", flags=keep_tomb, energy=-3), radius=1.2,
   acting={"actor": gd1, "available": a("point", "resolve", WP(v, "door_up")), "selected": a("point", "resolve", WP(v, "door_up")), "committed": a("point", "resolve", WP(v, "door_up"), 4),
           "success": a("point", "resolve", WP(v, "door_up"), 8), "failure": a("point", "resolve", WP(v, "door_up"), 8)})
CAST["jerusalem.tomb"] = [L(tw1, 0, "stare", "grief", beats=16), L(tw2, 0, "stare", "grief", beats=16), L(tw1, 16, "recoil", "fear", beats=14), L(tw2, 16, "recoil", "fear", beats=14),
                          L(tw1, 32, "stare", "awe", CAM, 16), L(tw3, 32, "stare", "awe", CAM, 16), L(tw1, 48, "cheer", "cheer", beats=14), L(tw2, 48, "cheer", "cheer", beats=14), L(gd1, 48, "point", "resolve", WP(v, "door_up"), 14)]
PIECES["jerusalem.tomb"] = {"on": [PC(v, "stone_closed")]}
BLOCK_FX["jerusalem.tomb"] = [{"block": 0, "pass": {"pieces": {"off": [PC(v, "stone_closed")], "on": [PC(v, "stone_rolled")]}}, "miss": {"pieces": {"off": [PC(v, "stone_closed")], "on": [PC(v, "stone_rolled")]}}}]

# ---- J16 The Road Beyond Jerusalem (ending: road) ----------------------------------------------------------------------------------------------------------
v = "road"
rd1, rd2, sp1, rg1, rg2 = (A(v, x) for x in ("d01", "d02", "sp1", "g1", "g2"))
keep_road = ["keep:path_gospel_road"]
hs("jerusalem.road", "home", "exit", W(v, "door_up"), out(route="run:warehouse", flags=keep_road), out(route="run:warehouse", flags=keep_road, energy=-3), default=True, radius=1.0, look="open")
hs("jerusalem.road", "followers", "character", Ac(v, "d02"), out(flags=["gospel_followed"], energy=6), out(energy=-3),
   acting={"actor": rd2, "available": a("beckon", "happy", CAM), "selected": a("beckon", "happy", CAM), "committed": a("nod", "relief", beats=4), "success": a("laugh", "laugh", beats=8, then=a("nod", "relief", beats=8)),
           "failure": a("shake_head", "doubt", beats=8)})
CAST["jerusalem.road"] = [L(rd1, 0, "stare", "relief", CAM, 16), L(rd2, 16, "laugh", "laugh", beats=14), L(sp1, 32, "bow", "awe", beats=14), L(rg1, 48, "shake_head", "doubt", beats=14),
                          L(rg2, 48, "shake_head", "doubt", beats=14)]


# ======================================================================================================================================================
# the files
# ======================================================================================================================================================
def rail_of(sc):
    nid, scene, world, view, entry, exit_scene, ending, title, routes, prompt = sc
    wp = lambda n: WP(view, n)
    return {"waypoint": wp("home"), "rail": {
        "good": [{"to": wp("g1"), "role": "dancer", "style": "walk", "bars": 3}, {"to": wp("g2"), "role": "dancer", "style": "walk", "bars": 3}, {"to": wp("g3"), "role": "dancer", "style": "walk", "bars": 3}],
        "bad": [{"to": wp("b1"), "role": "queasy", "style": "walk", "bars": 2}, {"to": wp("b2"), "role": "queasy", "style": "walk", "bars": 2}],
        "arrive": wp("arrive"),
        "glances": [{"by": -12, "pitch": 8, "bars": 2}, {"by": -28, "bars": 2}, {"pitch": 14, "bars": 3}, {"by": 24, "bars": 2}],
        "strolls": [{"fwd": 1.6, "bars": 3}, {"turn": 35, "fwd": 1.0, "bars": 3}, {"right": 1.4, "bars": 2}],
        "exits": {d: wp("door_" + d) for _, d in routes}}}


def write_run():
    nodes = []
    for sc in SCENES:
        nid, scene, world, view, entry, exit_scene, ending, title, routes, prompt = sc
        nxt = []
        for to, d in routes:
            e = {"to": to, "dir": d, "label": f"to {to}"}
            if nid == "road.loaves" and to == "road":
                e["loop"] = True
            nxt.append(e)
        n = {"id": nid, "world": world, "scene": scene, "title": title, "entry": entry, "exit_scene": exit_scene, "role": "dancer", "blurb": title, "next": nxt, "place": rail_of(sc)}
        if ending:
            n["ending"] = ending
        if nid in CAST:
            n["cast"] = CAST[nid]
        if nid in PIECES:
            n["pieces"] = PIECES[nid]
        if nid in BLOCK_FX:
            n["block_fx"] = BLOCK_FX[nid]
        nodes.append(n)
    run = {"schema": 1,
           "path": {"id": "gospel", "title": "The Life of Jesus", "entry_from": "warehouse.balcony.star", "returns_to": "warehouse",
                    "opens": "A figure of light under a projected star on the Warehouse balcony: touch it in time and follow."},
           "timing": {"bpm": 124, "phase_beats": 64, "block_beats": 16, "cue_span_beats": 12.0, "decision_beat": 12.5, "fade_beats": 2.0},
           "start_node": "jordan", "worlds": WORLDS, "nodes": nodes, "cinematics": CINEMATICS}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hotspots").mkdir(exist_ok=True)
    (OUT / "run.json").write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")
    for w in WORLDS:
        (OUT / "hotspots" / f"{w['id']}.json").write_text(json.dumps({"world": w["id"], "hotspots": HOTSPOTS[w["id"]]}, indent=1) + "\n", encoding="utf-8")
    prompts = {sc[0]: {"scene": sc[1], "title": sc[7], "prompt": sc[9] + P_TAIL} for sc in SCENES}
    (OUT / "prompts.json").write_text(json.dumps(prompts, indent=1) + "\n", encoding="utf-8")


def write_music():
    mp = OUT / "music.json"
    music = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
    music["schema"] = 1
    music["note"] = ("Which pack each scene of the Gospel path plays. Written by tools/content/make_path_placeholders.py gospel (synthesised, temporary); the owner's loops replace them with "
                     "beatshaper.py import --path gospel. `prompt` is the owner's music prompt for the scene, verbatim (docs/paths/gospel.md). placeholder.levels_db are the RMS levels of the three stems (dBFS): "
                     "the placeholder mix is bass-forward.")
    music["placeholder"] = {"genre": "house", "key": 45, "levels_db": {"drums": -20.0, "bass": -12.0, "other": -28.0}, "sub_hz": 90.0, "sub_share_min": 0.5, "bass_over_pad_db_min": 10.0}
    have = {n["id"]: n for n in music.get("nodes", [])}
    nodes = []
    for sc in SCENES:
        e = have.get(sc[0], {"id": sc[0], "audio": f"gospel_{sc[1]}", "chart": f"gospel_{sc[1]}", "treatment": "none", "temporary": True})
        e["prompt"] = sc[9] + P_TAIL
        nodes.append(e)
    music["nodes"] = nodes
    mp.write_text(json.dumps(music, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if "--music-only" not in sys.argv:
        write_run()
    write_music()
    print("gospel:", len(SCENES), "scenes,", sum(len(v) for v in HOTSPOTS.values()), "hotspots,", len(CINEMATICS), "cinematics")
