#!/usr/bin/env python3
"""The acting pass on the five existing worlds (docs/THREE_PATHS_AND_FACES_PLAN.md 2.5, stage 1d): who does what, with which face, so that the story is told by people and not by text.

Three tables, all plain data that make_hotspots.py (ACTING, CINE_CAST) and make_scenes.py (CAST) copy into content/run/hotspots/<world>.json and content/run/run.json. Nothing here is
text: an act, a face, a look and a beat for a person of the scene's map (the validators are HotspotContract.validate_acting / validate_cast and RunData._validate_casts).

ACTING   hotspot id -> {actor?, available, selected, committed, success, failure}. Every character hotspot (kind `character`) and the Bassment-style secret stranger have one.
         available  = what the person does while the hotspot waits (beats 48 to 60.5: the choice window), selected = once touched, committed = the one beat of the commit flash,
         success / failure = what they do with the outcome (8 beats unless `beats`; `then` is what they settle into). Only the states that make the story are given.
CAST     scene id -> [line]: the beats that happen whether or not anything is touched. at_beat 0 to 63 of the scene's 64-beat phase (blocks start at 0, 16, 32, 48; the choice window opens at 48,
         the route commits at 60.5). if_energy_below / above and if_flags_all / none make a line conditional (read at that beat). A line with a flag the outcome sets (`wd_treated`...) fires at
         beat 61 to 63, right after the commit at 60.5: that is how a bystander reacts to the player's result in a scene where the outcome has no cinematic.
CINE_CAST cinematic name -> [line]: at_beat is relative to the commit (0 to 16): the reaction of the people around to a result that already has a cinematic (the setbacks above all).

Only acts the Stage 1a sheets can show: the fifteen directed acts plus the older states (wave, point, stare, cheer, sad, rock, check, sleep, sit, watch, look...). tools/story/art/directed.py reads this
data (through the generated files) to decide what the sheet builder bakes for whom, so everything named here is baked, and nothing else is.
"""
from __future__ import annotations


def a(act: str, face: str | None = None, look: str | None = None, beats: float | None = None, then: dict | None = None) -> dict:
    """One state of a hotspot's acting block."""
    s = {"act": act}
    if face:
        s["face"] = face
    if look:
        s["look_at"] = look
    if beats is not None:
        s["beats"] = beats
    if then:
        s["then"] = then
    return s


def L(actor: str, beat: float, act: str, face: str | None = None, look: str | None = None, beats: float | None = None, **cond) -> dict:
    """One cast line: {actor, at_beat, act, face?, look_at?, beats?, if_*}."""
    s = {"actor": actor, "at_beat": beat, "act": act}
    if face:
        s["face"] = face
    if look:
        s["look_at"] = look
    if beats is not None:
        s["beats"] = beats
    for k, v in cond.items():
        s[k] = v
    return s


CAM = "camera"

# character hotspots with nobody to direct: the two wizards are billboard things of the map, not baked people
NO_ACTOR = {"warehouse.wizard", "warehouse.chill.wizard"}

# =========================================================================================================================================================
# Hotspots: the people who can be touched
# =========================================================================================================================================================
ACTING: dict[str, dict] = {
    # ---- Warehouse (night_one) ------------------------------------------------------------------------------------------------------------------------
    # (warehouse.wizard and warehouse.chill.wizard are billboard things, not baked people: no actor to direct; see docs/HANDOVER.md stage 1d)
    "warehouse.dancer": {  # g07: come and dance; the circle cheers you in, or turns its back
        "available": a("beckon", "happy", CAM), "selected": a("nod", "happy", CAM), "committed": a("point", "happy", "floor_centre", 1),
        "success": a("cheer", "cheer", CAM, 8), "failure": a("recoil", "fear", CAM, 4, then=a("shake_head", "doubt", CAM, 8)),
    },
    "warehouse.bar.bartender": {  # b01: a drink slid across, or you are cut off
        "available": a("offer", "happy", CAM), "selected": a("nod", "happy", CAM), "committed": a("offer", "happy", CAM, 1),
        "success": a("nod", "relief", CAM, 8), "failure": a("block", "anger", CAM, 8, then=a("stare", "anger", CAM)),
    },
    "warehouse.bar.stranger": {  # b03: a whisper in the corner
        "available": a("beckon", "doubt", CAM), "selected": a("stare", "resolve", CAM), "committed": a("nod", "resolve", CAM, 1),
        "success": a("nod", "resolve", CAM, 8), "failure": a("shake_head", "doubt", CAM, 6, then=a("look", "neutral")),
    },
    "warehouse.balcony.promoter": {  # v03: tickets in hand, or withdrawn
        "available": a("beckon", "resolve", CAM), "selected": a("offer", "resolve", CAM), "committed": a("offer", "happy", CAM, 1),
        "success": a("nod", "happy", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8, then=a("stare", "neutral", CAM)),
    },
    "warehouse.exit.bouncer": {  # d01: the door is shut; he steps aside or throws you back at the floor
        "available": a("block", "anger", CAM), "selected": a("stare", "doubt", CAM), "committed": a("block", "resolve", CAM, 1),
        "success": a("nod", "resolve", CAM, 8), "failure": a("stamp", "anger", CAM, 4, then=a("point", "anger", "floor_centre", 12)),
    },
    "warehouse.exit.bouncer_vip": {  # d01 with your name on the list
        "available": a("beckon", "resolve", CAM), "selected": a("nod", "resolve", CAM), "committed": a("bow", "neutral", CAM, 1),
        "success": a("bow", "relief", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8, then=a("stare", "doubt", CAM)),
    },
    # ---- The Mothership --------------------------------------------------------------------------------------------------------------------------------
    "mothership.grey": {  # g08: wonder at you, then fright if you are rough
        "available": a("beckon", "awe", CAM), "selected": a("nod", "awe", CAM), "committed": a("offer", "awe", CAM, 1),
        "success": a("cheer", "awe", CAM, 8), "failure": a("recoil", "fear", CAM, 6, then=a("stare", "fear", CAM)),
    },
    "mothership.dj": {  # m01: the wrong-way headphones, laughing
        "available": a("beckon", "laugh", CAM), "selected": a("laugh", "laugh", CAM), "committed": a("point", "laugh", CAM, 1),
        "success": a("cheer", "laugh", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8, then=a("stare", "doubt", CAM)),
    },
    "mothership.reactor.engineer": {  # reactor_s01: please, the reactor
        "available": a("plead", "plea", CAM), "selected": a("point", "resolve", "reactor_core"), "committed": a("point", "resolve", "reactor_core", 1),
        "success": a("nod", "relief", CAM, 8), "failure": a("collapse", "grief", CAM, 8, then=a("sad", "grief")),
    },
    "mothership.exit.exam": {  # med02: the chart, the stare, the strap
        "available": a("write", "neutral", CAM), "selected": a("stare", "doubt", CAM), "committed": a("stare", "resolve", CAM, 1),
        "success": a("nod", "relief", CAM, 8), "failure": a("block", "anger", CAM, 8, then=a("write", "neutral")),
    },
    # ---- The Underworld ------------------------------------------------------------------------------------------------------------------------------------
    "underworld.bouncer": {  # gate_bouncer: planted, then a mocking bow, or a stamp and a point back
        "available": a("block", "anger", CAM), "selected": a("stare", "doubt", CAM), "committed": a("block", "anger", CAM, 1),
        "success": a("bow", "laugh", CAM, 8), "failure": a("stamp", "anger", CAM, 4, then=a("point", "anger", "arena_edge", 12)),
    },
    "underworld.bouncer_grudge": {  # the same bouncer, who remembers the Warehouse door
        "available": a("stamp", "anger", CAM), "selected": a("block", "anger", CAM), "committed": a("stare", "anger", CAM, 1),
        "success": a("bow", "laugh", CAM, 8), "failure": a("stamp", "anger", CAM, 4, then=a("point", "anger", "arena_edge", 12)),
    },
    "underworld.court.queen": {  # court_g06: she watches, beckons, nods, or points at the pit while the court laughs
        "available": a("stare", "resolve", CAM), "selected": a("beckon", "resolve", CAM), "committed": a("stare", "resolve", CAM, 1),
        "success": a("nod", "resolve", CAM, 8), "failure": a("point", "laugh", "pit_edge", 10, then=a("laugh", "laugh", CAM)),
    },
    # ---- The Hospital (hospital) ---------------------------------------------------------------------------------------------------------------------------
    "hospital.nurse": {  # h02: calm, sure
        "available": a("beckon", "resolve", CAM), "selected": a("nod", "resolve", CAM), "committed": a("point", "resolve", "ward_door", 1),
        "success": a("nod", "relief", CAM, 8), "failure": a("shake_head", "doubt", CAM, 6, then=a("point", "resolve", "bed_corner", 8)),
    },
    "hospital.family": {  # h03: afraid, asking for help, then glad or in tears
        "available": a("plead", "plea", CAM), "selected": a("nod", "relief", CAM), "committed": a("plead", "plea", CAM, 1),
        "success": a("cheer", "relief", CAM, 8), "failure": a("cover_face", "grief", CAM, 8, then=a("sad", "grief")),
    },
    "hospital.corridor.trolley": {  # h07: a cup of tea on the tray
        "available": a("offer", "happy", CAM), "selected": a("nod", "happy", CAM), "committed": a("offer", "happy", CAM, 1),
        "success": a("nod", "relief", CAM, 8, then=a("offer", "happy", CAM)), "failure": a("recoil", "fear", CAM, 4, then=a("shake_head", "doubt", CAM, 8)),
    },
    "hospital.dayroom.granny": {  # h08: a sweet from her pocket
        "available": a("offer", "relief", CAM), "selected": a("nod", "happy", CAM), "committed": a("offer", "happy", CAM, 1),
        "success": a("nod", "relief", CAM, 8, then=a("offer", "happy", CAM)), "failure": a("shake_head", "doubt", CAM, 6, then=a("watch", "neutral", "tv_set")),
    },
    "hospital.cafeteria.kid": {  # h14: laughing, wants you to play
        "available": a("beckon", "laugh", CAM), "selected": a("laugh", "laugh", CAM), "committed": a("wave", "happy", CAM, 1),
        "success": a("cheer", "laugh", CAM, 8), "failure": a("shake_head", "shame", CAM, 6, then=a("sad", "sad")),
    },
    "hospital.garden.mum": {  # h16: grief turning to relief, or into her hands
        "available": a("beckon", "grief", CAM), "selected": a("nod", "grief", CAM), "committed": a("plead", "plea", CAM, 1),
        "success": a("nod", "grief", CAM, 3, then=a("cheer", "relief", CAM, 8)), "failure": a("cover_face", "grief", CAM, 8, then=a("sad", "grief")),
    },
    # ---- The Hospital, late -------------------------------------------------------------------------------------------------------------------------------
    "hospital_late.doctor": {  # h17: the chart, a doubt, then agreement
        "available": a("write", "doubt", CAM), "selected": a("nod", "doubt", CAM), "committed": a("write", "resolve", CAM, 1),
        "success": a("nod", "relief", CAM, 8), "failure": a("shake_head", "doubt", CAM, 8, then=a("write", "doubt")),
    },
    "hospital_late.cafe.kid": {  # h14 again, beckoning
        "available": a("beckon", "happy", CAM), "selected": a("wave", "happy", CAM), "committed": a("beckon", "happy", CAM, 1),
        "success": a("laugh", "laugh", CAM, 8), "failure": a("sad", "sad", CAM, 8),
    },
    # ---- The Ward (mental_hospital) -----------------------------------------------------------------------------------------------------------------------
    "ward.orderly": {  # e04: blocks the way, shakes his head; sends you to treatment
        "available": a("block", "resolve", CAM), "selected": a("shake_head", "doubt", CAM), "committed": a("stare", "resolve", CAM, 1),
        "success": a("nod", "resolve", CAM, 8), "failure": a("shake_head", "doubt", CAM, 4, then=a("point", "resolve", "treat", 12)),
    },
    "ward.art.painter": {  # x10: the brush held out, wonder
        "available": a("offer", "awe", CAM), "selected": a("nod", "awe", CAM), "committed": a("offer", "happy", CAM, 1),
        "success": a("cheer", "awe", CAM, 8), "failure": a("recoil", "fear", CAM, 4, then=a("shake_head", "doubt", CAM, 8)),
    },
    "ward.dorm.sleeper": {  # x14: asleep, startled awake, or soothed
        "available": a("sleep", "neutral"), "selected": a("recoil", "fear", CAM), "committed": a("rock", "fear", CAM, 1),
        "success": a("sleep", "relief", None, 8), "failure": a("recoil", "fear", CAM, 6, then=a("cover_face", "fear", CAM)),
    },
    "ward.corridor.king": {  # x06: bows to you and expects a bow
        "available": a("bow", "resolve", CAM), "selected": a("stare", "resolve", CAM), "committed": a("bow", "resolve", CAM, 1),
        "success": a("cheer", "cheer", CAM, 8), "failure": a("stamp", "anger", CAM, 4, then=a("block", "anger", CAM)),
    },
    "ward.courtyard.chef": {  # x01: a plate held out, a laugh
        "available": a("offer", "happy", CAM), "selected": a("laugh", "laugh", CAM), "committed": a("offer", "happy", CAM, 1),
        "success": a("laugh", "laugh", CAM, 8, then=a("offer", "happy", CAM)), "failure": a("recoil", "fear", CAM, 4, then=a("stamp", "anger", CAM, 8)),
    },
    # ---- The Ward, late ---------------------------------------------------------------------------------------------------------------------------------
    "ward_late.treat.orderly": {  # x02: writes, then points
        "available": a("write", "neutral", CAM), "selected": a("point", "resolve", "treat_door"), "committed": a("point", "resolve", "treat_door", 1),
        "success": a("nod", "relief", CAM, 8), "failure": a("block", "anger", CAM, 6, then=a("point", "resolve", "treat_door", 12)),
    },
    "ward_late.dorm.sleeper": {  # x13
        "available": a("sleep", "neutral"), "selected": a("recoil", "fear", CAM), "committed": a("rock", "fear", CAM, 1),
        "success": a("sleep", "relief", None, 8), "failure": a("recoil", "fear", CAM, 6, then=a("cover_face", "fear", CAM)),
    },
    "ward_late.exit.stare": {  # x09: the long stare at the window, wonder or anger
        "available": a("stare", "neutral", CAM), "selected": a("stare", "doubt", CAM), "committed": a("stare", "resolve", CAM, 1),
        "success": a("stare", "awe", CAM, 8, then=a("cheer", "awe", CAM)), "failure": a("stare", "anger", CAM, 8, then=a("stamp", "anger", CAM)),
    },
}

# =========================================================================================================================================================
# Scenes: what happens whether or not anything is touched
# =========================================================================================================================================================
CAST: dict[str, list[dict]] = {
    # ---- Warehouse ----------------------------------------------------------------------------------------------------------------------------------------
    "warehouse": [  # the floor: a welcome, a call, a dancer's wave, a sceptic when you arrive played out
        L("c01", 0, "cheer", "cheer", CAM, 10),
        L("c02", 16, "beckon", "happy", CAM, 12),
        L("c08", 36, "wave", "happy", CAM, 8),
        L("c03", 44, "shake_head", "doubt", CAM, 8, if_energy_below=45),
    ],
    "warehouse.bar": [  # laughter at the bar, a nod to the barman, a watcher in the corner, a barfly in tears when you are low
        L("b02", 0, "laugh", "laugh", "b04", 10),
        L("b04", 16, "nod", "happy", "b01", 8),
        L("b03", 30, "stare", "doubt", CAM, 14),
        L("b02", 48, "cover_face", "shame", None, 10, if_energy_below=40),
    ],
    "warehouse.balcony": [  # the view over the floor, a clap, the promoter noticing you
        L("v01", 0, "watch", "awe", "floor_centre", 16),
        L("v02", 16, "clap", "happy", CAM, 12),
        L("v03", 36, "stare", "resolve", CAM, 10),
        L("e03", 48, "cheer", "cheer", CAM, 10, if_energy_above=65),
    ],
    "warehouse.chill": [  # two friends on the sofas, a phone call, a frown for the state you are in
        L("s03", 0, "laugh", "laugh", "s02", 12),
        L("s02", 16, "nod", "relief", "s03", 8),
        L("s04", 36, "wave", "happy", CAM, 8),
        L("s03", 52, "shake_head", "doubt", CAM, 8, if_energy_below=45),
    ],
    "warehouse.booth": [  # the floor worships the DJ when it is going well
        L("c10", 0, "cheer", "awe", CAM, 12),
        L("c07", 20, "clap", "happy", CAM, 12),
        L("e01", 40, "bow", "awe", CAM, 8, if_energy_above=70),
        L("g02", 52, "kneel", "awe", CAM, 10, if_energy_above=85),
    ],
    "warehouse.exit": [  # the bouncer at the door, a goodbye wave, the floor laughing at you when you leave played out
        L("d01", 0, "block", "anger", CAM, 16),
        L("c01", 16, "wave", "happy", CAM, 8),
        L("d01", 24, "stare", "doubt", CAM, 16),
        L("c09", 48, "laugh", "laugh", CAM, 10, if_energy_below=40),
    ],
    # ---- The Mothership -------------------------------------------------------------------------------------------------------------------------------------
    "mothership": [  # greys marvel at you, the DJ's point, a blob hides when you are weak
        L("c07", 0, "stare", "awe", CAM, 16),
        L("c10", 16, "wave", "awe", CAM, 10),
        L("m01", 36, "point", "laugh", CAM, 8),
        L("c08", 48, "recoil", "fear", CAM, 8, if_energy_below=40),
    ],
    "mothership.gallery": [  # the window on the planet, a nod, a doubt, a plea when you look worn
        L("gallery_c03", 0, "stare", "awe", "planet_window", 16),
        L("gallery_c05", 16, "nod", "happy", "gallery_c03", 8),
        L("gallery_c01", 32, "shake_head", "doubt", CAM, 8),
        L("gallery_s01", 48, "plead", "plea", CAM, 8, if_energy_below=45),
    ],
    "mothership.reactor": [  # the reactor is in danger: fright, the engineer pointing, a crew member on the floor if you are low
        L("reactor_c01", 0, "recoil", "fear", "core_r", 12),
        L("reactor_c09", 16, "cover_face", "fear", None, 10),
        L("reactor_s01", 24, "point", "resolve", "reactor_core", 12),
        L("reactor_c06", 52, "collapse", "grief", None, 10, if_energy_below=35),
    ],
    "mothership.bridge": [  # the crew: a salute, agreement, a laugh, the warp seen with awe
        L("bridge_c03", 0, "salute", "resolve", CAM, 12),
        L("bridge_c05", 16, "nod", "happy", "helm", 8),
        L("bridge_c01", 32, "laugh", "laugh", "bridge_c01", 8),
        L("bridge_c07", 48, "stare", "awe", "warp_b", 12),
    ],
    "mothership.exit": [  # the medbay: a chart, a stare, a doubt, the strap if you arrive worn down
        L("med01", 0, "write", "neutral", None, 16),
        L("med02", 16, "stare", "doubt", CAM, 12),
        L("med01", 36, "shake_head", "doubt", "med02", 8),
        L("med02", 52, "block", "anger", CAM, 8, if_energy_below=35),
    ],
    # ---- The Underworld ---------------------------------------------------------------------------------------------------------------------------------------
    "underworld": [  # the gate's bouncer, laughter from the imps, a cheer, a skeleton's fright
        L("gate_bouncer", 0, "block", "anger", CAM, 16),
        L("c07", 16, "laugh", "laugh", CAM, 12),
        L("c12", 32, "cheer", "cheer", None, 8),
        L("c06", 48, "recoil", "fear", CAM, 8, if_energy_below=40),
    ],
    "underworld.court": [  # the queen's stare, a fiend bowing to her, laughter, a skeleton cowering when you are low
        L("court_c04", 0, "stare", "resolve", CAM, 16),
        L("court_c03", 16, "bow", "awe", "court_c04", 8),
        L("court_c07", 32, "laugh", "laugh", CAM, 12),
        L("court_c05", 48, "cover_face", "fear", None, 10, if_energy_below=40),
    ],
    "underworld.furnace": [  # the forge: a cheer, a laugh, the smith's hammering, a recoil from the heat
        L("furnace_c10", 0, "cheer", "cheer", CAM, 12),
        L("furnace_c02", 16, "laugh", "laugh", "furnace_c10", 8),
        L("smith_carry", 32, "stamp", "anger", None, 8),
        L("furnace_c04", 48, "recoil", "fear", CAM, 8, if_energy_below=40),
    ],
    "underworld.pit": [  # the pit: a brute barring the way, a laugh, a skeleton begging, a cheer when it is going well
        L("pit_c06", 0, "block", "anger", CAM, 16),
        L("pit_c01", 16, "laugh", "laugh", CAM, 12),
        L("pit_c09", 32, "kneel", "plea", CAM, 12),
        L("pit_c05", 48, "cheer", "cheer", CAM, 10, if_energy_above=60),
    ],
    "underworld.exit": [  # the throne: bows and kneeling to it, a laugh at you, a salute when you have earned it
        L("stair_chat_a", 0, "bow", "awe", "uw_throne", 16),
        L("stair_chat_b", 16, "kneel", "awe", "uw_throne", 16),
        L("stair_sit", 32, "laugh", "laugh", CAM, 12),
        L("stair_chat_a", 48, "salute", "resolve", CAM, 8, if_energy_above=60),
    ],
    # ---- The Hospital -----------------------------------------------------------------------------------------------------------------------------------------
    "hospital": [  # the family's fear on arrival and their plea, the nurse's calm, the mother in tears when you come played out
        L("h03", 0, "stare", "fear", CAM, 16),
        L("h03", 16, "plead", "plea", CAM, 16),
        L("h02", 32, "point", "resolve", "ward_door", 12),
        L("h03", 48, "cover_face", "grief", None, 12, if_energy_below=40),
    ],
    "hospital.corridor": [  # a child waves, a father pleads with the doctor, who shakes his head, a nurse reassures
        L("corridor_c03", 0, "wave", "happy", CAM, 12),
        L("corridor_c02", 16, "plead", "plea", "corridor_c09", 12),
        L("corridor_c09", 32, "shake_head", "doubt", "corridor_c02", 10),
        L("corridor_c08", 48, "nod", "resolve", CAM, 10, if_energy_above=55),
    ],
    "hospital.dayroom": [  # the television's laughter, the granny's sweet, a child's fright when you are low
        L("h10", 0, "laugh", "laugh", "tv_set", 14),
        L("h08", 28, "offer", "relief", CAM, 10),
        L("h10", 48, "cover_face", "fear", None, 10, if_energy_below=40),
    ],
    "hospital.cafeteria": [  # the kid waves, a mother nods, a granny offers, the doctor at the station writes
        L("h14", 0, "wave", "happy", CAM, 12),
        L("cafeteria_c08", 16, "nod", "relief", "h14", 8),
        L("cafeteria_c02", 32, "offer", "happy", CAM, 8),
        L("h06", 48, "write", "doubt", None, 12),
    ],
    "hospital.garden": [  # the garden in the sun: a granny rocking in relief, a child laughing, a father's nod, a mother in tears if you are low
        L("garden_c01", 0, "rock", "relief", None, 16),
        L("garden_c02", 16, "laugh", "laugh", "garden_c07", 10),
        L("garden_c03", 32, "nod", "relief", "garden_c06", 10),
        L("garden_c06", 48, "cover_face", "grief", None, 10, if_energy_below=40),
    ],
    "hospital.exit": [  # the bandstand: applause, a cheer, a laugh, awe when the band is on form
        L("garden_c10", 0, "clap", "happy", CAM, 12),
        L("h15", 16, "cheer", "cheer", CAM, 12),
        L("garden_c05", 32, "laugh", "laugh", "garden_c07", 10),
        L("garden_c07", 48, "cheer", "awe", CAM, 10, if_energy_above=60),
    ],
    # ---- The Ward -------------------------------------------------------------------------------------------------------------------------------------------
    "ward": [  # the day room: a cheer, a patient at the window, the orderly blocking, a patient hiding when you are low
        L("c03", 0, "cheer", "cheer", CAM, 10),
        L("x09", 16, "stare", "doubt", "wlight_d", 16),
        L("c05", 32, "block", "resolve", CAM, 14),
        L("c06", 48, "cover_face", "shame", None, 10, if_energy_below=40),
    ],
    "ward.art": [  # the art room: wonder at the easel, a cheer, the painter's brush, a sceptic when you are low
        L("art_room_c03", 0, "stare", "awe", "art_easels", 16),
        L("art_room_c02", 16, "cheer", "awe", None, 10),
        L("x10", 32, "offer", "happy", CAM, 12),
        L("art_room_c01", 48, "shake_head", "doubt", "easel_a3", 10, if_energy_below=50),
    ],
    "ward.dorm": [  # the dormitory: sleepers, a restless one, a wake-up fright when you arrive worn out, calm when it is going well
        L("x13", 0, "sleep", "relief", None, 28),
        L("x14", 36, "rock", "fear", None, 10),
        L("x13", 48, "recoil", "fear", CAM, 8, if_energy_below=45),
        L("x14", 54, "sleep", "relief", None, 10, if_energy_above=55),
    ],
    "ward.corridor": [  # the king and his court: his stare, a salute, a kneel, a patient in the queue in fear
        L("x06", 0, "stare", "resolve", CAM, 16),
        L("corridor_c03", 16, "salute", "resolve", "x06", 12),
        L("corridor_c02", 32, "kneel", "awe", "x06", 12),
        L("x04", 40, "cover_face", "fear", None, 10, if_energy_below=45),
    ],
    "ward.courtyard": [  # the courtyard: an orderly writing, a bow, the chef's offer, a cheer when it is going well
        L("courtyard_c03", 0, "write", "neutral", None, 16),
        L("courtyard_c01", 16, "bow", "happy", "courtyard_c01", 10),
        L("x01", 32, "offer", "happy", CAM, 12),
        L("courtyard_c02", 48, "cheer", "cheer", CAM, 10, if_energy_above=60),
    ],
    "ward.exit": [  # the stage: applause, a cheer, the king's bow, awe when it is going well
        L("courtyard_c10", 0, "clap", "happy", CAM, 12),
        L("x01", 16, "cheer", "cheer", CAM, 12),
        L("courtyard_c05", 32, "bow", "awe", CAM, 10),
        L("courtyard_c07", 48, "cheer", "awe", CAM, 10, if_energy_above=65),
    ],
    # ---- The Hospital, late ---------------------------------------------------------------------------------------------------------------------------------
    "hospital_late": [  # the garden after dark: relief, a granny rocking, the doctor writing, a child's wave
        L("garden_c06", 0, "nod", "relief", "garden_c10", 12),
        L("garden_c10", 16, "rock", "relief", None, 16),
        L("garden_c04", 32, "write", "neutral", None, 12),
        L("garden_c07", 48, "wave", "happy", CAM, 8, if_energy_above=55),
    ],
    "hospital_late.cafe": [  # the late cafeteria: a doctor writing, a nod, a laugh, a child's wave
        L("cafeteria_c05", 0, "write", "doubt", None, 16),
        L("cafeteria_c09", 16, "nod", "relief", "cafeteria_c05", 10),
        L("cafeteria_c07", 32, "laugh", "laugh", "cafeteria_g06", 10),
        L("cafeteria_c10", 48, "wave", "happy", CAM, 10),
    ],
    "hospital_late.quiet": [  # the quiet room is empty by design: the corridor's people look in at its door
        L("h07", 0, "stare", "relief", "quiet_door", 16),
        L("corridor_c03", 16, "wave", "happy", "quiet_door", 12),
        L("corridor_c08", 36, "nod", "relief", "quiet_door", 12),
    ],
    "hospital_late.exit": [  # the late bandstand: applause, a granny's cheer, a father's relief, awe when it goes well
        L("garden_c10", 0, "clap", "happy", CAM, 12),
        L("h15", 16, "cheer", "relief", CAM, 12),
        L("garden_c07", 32, "nod", "relief", "garden_c07", 10),
        L("garden_p03", 48, "cheer", "awe", CAM, 10, if_energy_above=60),
    ],
    # ---- The Ward, late ---------------------------------------------------------------------------------------------------------------------------------
    "ward_late": [  # the courtyard after hours: a nod, an offer, the king's bow, a patient in grief when you are low
        L("courtyard_c10", 0, "nod", "relief", "x01", 12),
        L("x01", 24, "offer", "happy", CAM, 12),
        L("courtyard_c07", 40, "bow", "awe", CAM, 10),
        L("courtyard_c06", 52, "cover_face", "grief", None, 10, if_energy_below=35),
    ],
    "ward_late.treat": [  # the treatment room: the orderly writing, a plea, fear, and the pointing finger when you are low
        L("x02", 0, "write", "neutral", None, 16),
        L("x03", 16, "plead", "plea", CAM, 14),
        L("x04", 32, "cover_face", "fear", None, 12),
        L("x02", 48, "point", "resolve", "treat_door", 10, if_energy_below=50),
    ],
    "ward_late.dorm": [  # the late dormitory: calm sleepers, a restless one, a shake of the head when you are low
        L("x14", 0, "sleep", "relief", None, 30),
        L("x13", 36, "rock", "fear", None, 12),
        L("x14", 52, "shake_head", "fear", None, 8, if_energy_below=40),
    ],
    "ward_late.exit": [  # the day room again: a wave, a bow of thanks, a salute, wonder when it goes well
        L("c08", 0, "wave", "happy", CAM, 12),
        L("c02", 16, "bow", "relief", CAM, 10),
        L("c04", 32, "salute", "resolve", CAM, 10),
        L("x07", 48, "stare", "awe", CAM, 10, if_energy_above=60),
    ],
}

# =========================================================================================================================================================
# Cinematics: the people around reacting to a result (at_beat counts from the commit)
# =========================================================================================================================================================
CINE_CAST: dict[str, list[dict]] = {
    "warehouse.join_circle": [  # the circle cheers you in
        L("c02", 0.5, "cheer", "cheer", CAM, 8), L("c03", 1, "cheer", "cheer", CAM, 8), L("c04", 1.5, "clap", "happy", CAM, 8)],
    "warehouse.stumble_circle": [  # the circle turns its back
        L("c02", 0.5, "stare", "doubt", "stage", 8), L("c03", 1, "shake_head", "doubt", CAM, 6), L("c01", 1.5, "laugh", "laugh", "stage", 6)],
    "warehouse.spill": [  # the bar laughs and winces
        L("b02", 0.5, "laugh", "laugh", CAM, 6), L("b04", 1, "shake_head", "doubt", CAM, 6)],
    "warehouse.thrown_out": [  # the floor laughs at the thrown-out
        L("c01", 1, "laugh", "laugh", CAM, 6), L("c05", 2, "shake_head", "doubt", CAM, 6)],
    "mothership.probe_light": [  # the deck backs away from the probe
        L("c07", 0.5, "recoil", "fear", CAM, 6), L("c06", 1, "cover_face", "fear", None, 6)],
    "mothership.exam_strapped": [  # the second examiner notes it down
        L("med01", 1, "write", "neutral", None, 8)],
    "underworld.gate_shove": [  # the arena laughs
        L("c07", 1, "laugh", "laugh", CAM, 6), L("c06", 2, "laugh", "laugh", CAM, 6)],
    "hospital.back_to_bed": [  # the family weeps and the ward nurse points back to bed
        L("h03", 1, "cover_face", "grief", None, 8), L("c01", 0.5, "point", "resolve", "bed_corner", 8)],
    "hospital.family_cheer": [  # the other family cheers with them
        L("c02", 1, "cheer", "relief", CAM, 8), L("c01", 1.5, "clap", "happy", CAM, 8)],
    "hospital.tea_spill": [  # a child laughs, a father flinches
        L("corridor_c03", 0.5, "laugh", "laugh", CAM, 6), L("corridor_c02", 1, "recoil", "fear", CAM, 6)],
    "hospital.granny_long": [  # the television kid laughs at the long story
        L("h10", 1, "laugh", "laugh", "tv_set", 8)],
    "ward.to_treatment": [  # the queue backs away
        L("x03", 1, "recoil", "fear", CAM, 8), L("x04", 2, "cover_face", "fear", None, 8)],
    "ward.paint_spill": [  # the art room gasps and laughs
        L("art_room_c03", 0.5, "recoil", "fear", CAM, 6), L("art_room_c02", 1, "laugh", "laugh", CAM, 6)],
    "ward.woken": [  # the dormitory wakes
        L("x13", 0.5, "recoil", "fear", CAM, 8)],
    "ward.plate_spill": [  # the courtyard laughs and flinches
        L("courtyard_c01", 0.5, "laugh", "laugh", CAM, 6), L("courtyard_c02", 1, "recoil", "fear", CAM, 6)],
    "ward_late.injection": [  # the queue cowers
        L("x03", 1, "cover_face", "fear", None, 8), L("x04", 2, "recoil", "fear", CAM, 8)],
}
