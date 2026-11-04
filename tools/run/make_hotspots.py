#!/usr/bin/env python3
"""Authors the run's hotspots (workstream C of docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md): content/run/hotspots/<world>.json for the seven run worlds, the named cinematics that
tools/run/make_scenes.py copies into content/run/run.json ("cinematics"), and docs/VISUAL_COVERAGE.md (the matrix: world, scene, hotspot, S outcome, F outcome).

    python3 tools/run/make_hotspots.py          # writes the hotspot files and the coverage doc (make_scenes.py writes the cinematics, the things and the waypoints)

The contract is section 2 of the plan: one hotspot is {id, world, scene, map, anchor, kind, radius_m, min_px, available, look, challenge, on_success, on_failure, cinematic?, default,
repeatable}. A world file is {"world": id, "hotspots": [...]}. The exits of a scene are generated from its `next` and the doorway of each route in `place.rail.exits` (the default is the
first route, the lit "ajar" door); the interactions are authored below, each with a success and a different failure. Outcomes: {route?, flags_set?, cinematic?, energy?, music?}.
A `route` is a scene id (a route of that scene) or a Bassment passage id ("1"). Cinematics are rail actions: {"move": "walk" | "place", "to": waypoint, "bars", "role", "style",
"look_at"?: waypoint, actor or thing}; `walk` stays in the room the rail is in (player_walk), `place` is a journey move (player_move). Flags are world-state ids set by outcomes.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "content/run/hotspots"
DOC = ROOT / "docs/VISUAL_COVERAGE.md"

CINEMATICS: dict[str, dict] = {}   # name -> {"world", "steps": [...]}
ROWS: list[dict] = []              # the coverage matrix rows
HOTSPOTS: dict[str, list] = {}     # world -> [hotspot]


# ---- small vocabulary ------------------------------------------------------------------------------------------------------------------------------
def T(thing):
    return {"thing": thing}


def W(wp):
    return {"waypoint": wp}


def A(actor):
    return {"actor": actor}


def P(x, y, z):
    return {"pos": [x, y, z]}


def walk(to, role="dancer", style="walk", bars=2, look=None, move="walk"):
    s = {"move": move, "to": to, "bars": bars, "role": role, "style": style}
    if look:
        s["look_at"] = look
    return s


def place(to, role="queasy", style="carried", bars=3, look=None):
    return walk(to, role, style, bars, look, move="place")


def cin(world, name, *steps):
    full = f"{world}.{name}"
    CINEMATICS[full] = {"world": world, "steps": list(steps)}
    return full


def out(route=None, flags=(), cin=None, energy=None, music=None):
    o = {}
    if route:
        o["route"] = route
    if flags:
        o["flags_set"] = list(flags)
    if cin:
        o["cinematic"] = cin
    if energy:
        o["energy"] = energy
    if music:
        o["music"] = music
    return o


def avail(all=(), none=(), energy_min=0, once=False):
    return {"flags_all": list(all), "flags_none": list(none), "energy_min": energy_min, "once": once}


# ---- scenes (read from run.json for the exits) -----------------------------------------------------------------------------------------------------
RUN = json.loads((ROOT / "content/run/run.json").read_text(encoding="utf-8"))
NODES = {n["id"]: n for n in RUN["nodes"]}
WORLD_MAP = {w["id"]: w["map"] for w in RUN["worlds"]}
EXIT_LOOK = {"default": "open", "other": "glow"}


def add(scene, name, kind, anchor, look, s, f, *, s_text, f_text, default=False, av=None, hook=None, radius=0.8, min_px=72, repeatable=True):
    n = NODES[scene]
    world = n["world"]
    h = {"id": f"{scene}.{name}", "world": world, "scene": scene, "map": WORLD_MAP[world], "anchor": anchor, "kind": kind, "radius_m": radius, "min_px": min_px,
         "available": av or avail(), "look": {"available": look, "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": s, "on_failure": f}
    if hook:
        h["cinematic"] = hook
    h["default"] = default
    h["repeatable"] = repeatable
    HOTSPOTS.setdefault(world, []).append(h)
    ROWS.append({"world": world, "scene": scene, "hotspot": h["id"], "kind": kind, "s": s_text, "f": f_text, "default": default,
                 "gate": (av or {}).get("flags_all", []) + ["not " + x for x in (av or {}).get("flags_none", [])]})
    return h


def exits(scene, anchors=None, looks=None, f_energy=-5):
    """One exit hotspot per route of the scene: anchored to its doorway, the first route the default (the door ajar). A failed exit still leaves by the same door, staggering."""
    n = NODES[scene]
    ex = n["place"]["rail"]["exits"]
    anchors = anchors or {}
    looks = looks or {}
    for i, r in enumerate(n["next"]):
        wp = ex[r["dir"]]
        dest = r["to"]
        short = dest.split(".")[-1] if "." in dest else dest
        name = "exit_" + short if "." in dest else "exit_" + dest
        look = looks.get(r["dir"], EXIT_LOOK["default"] if i == 0 else EXIT_LOOK["other"])
        fc = cin(NODES[scene]["world"], f"stagger_{scene.split('.', 1)[1] if '.' in scene else 'entry'}_{r['dir']}", walk(wp, "queasy", "stagger", 2))
        loop = " (round again)" if r.get("loop") else ""
        add(scene, name, "exit", anchors.get(r["dir"], W(wp)), look, out(route=dest), out(route=dest, cin=fc, energy=f_energy),
            s_text=f"route {dest}{loop}", f_text=f"same door, staggering ({f_energy} energy)", default=(i == 0), radius=1.0)


def ch(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "character", anchor, look, s, f, **kw)


def ob(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "object", anchor, look, s, f, **kw)


def ft(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "feature", anchor, look, s, f, **kw)


def sc(scene, name, anchor, look, s, f, **kw):
    add(scene, name, "secret", anchor, look, s, f, **kw)


# =========================================================================================================================================================
# The Warehouse (night_one)
# =========================================================================================================================================================
w = "warehouse"
exits("warehouse")
ch("warehouse", "wizard", T("wizard_floor"), "beckon",
   out(route="1", flags=["wh_wizard_met"]), out(flags=["wh_wizard_shrug"], energy=-2, cin=cin(w, "wizard_shrug", walk("floor_edge", "dancer", "walk", 2, look="wizard_floor"))),
   s_text="he leads you down the hatch: the Bassment (route 1)", f_text="he shrugs; nothing happens (-2), the door stays shut", av=avail(none=["wh_wizard_met"]),
   hook=walk("floor_edge", "dancer", "walk", 2, look="wizard_floor"))
ch("warehouse", "dancer", A("g07"), "beckon",
   out(flags=["wh_circle"], energy=6, music="variation", cin=cin(w, "join_circle", walk("floor_centre", "dancer", "walk", 2, look="g07"))),
   out(energy=-6, cin=cin(w, "stumble_circle", walk("floor_edge", "queasy", "stagger", 2))),
   s_text="a circle forms round you (+6, music variation)", f_text="you stumble in, queasy (-6)", av=avail(none=["wh_circle"]),
   hook=walk("floor_centre", "dancer", "walk", 2, look="g07"))
ft("warehouse", "led_wall", T("disco_ball"), "pulse",
   out(flags=["wh_led"], energy=5, music="variation"), out(energy=-4, music="dip"),
   s_text="the lights follow you: palette shift, music variation (+5)", f_text="the show flickers and cuts (-4, music dips)", av=avail(all=["wh_circle"], none=["wh_led"]))

exits("warehouse.bar")
ch("warehouse.bar", "bartender", A("b01"), "beckon",
   out(flags=["wh_drink"], energy=6, music="variation", cin=cin(w, "drink_at_bar", walk("bar_taps", "dancer", "walk", 3, look="b01"))),
   out(flags=["wh_spilled"], energy=-8, cin=cin(w, "spill", walk("bar_taps", "queasy", "stagger", 2))),
   s_text="a drink at the bar (+6, music variation)", f_text="it spills, you reel (-8, queasy)", hook=walk("bar_taps", "dancer", "walk", 2, look="b01"))
sc("warehouse.bar", "stranger", A("b03"), "flicker",
   out(flags=["wh_vip_pass"], energy=2, cin=cin(w, "whisper", walk("bar_end", "dancer", "walk", 2, look="b03"))), out(flags=["wh_stranger_gone"], energy=-3),
   s_text="a stranger on a phone slips you a VIP pass (flag wh_vip_pass: the booth headphones, the bouncer)", f_text="he pockets the phone and goes (-3)", av=avail(none=["wh_vip_pass", "wh_stranger_gone"], once=True))

exits("warehouse.balcony")
ft("warehouse.balcony", "rail", P(-7.15, 1.2, 1.0), "glow",
   out(flags=["wh_saw_floor"], energy=4, music="variation", cin=cin(w, "rail_look", walk("balcony_rail", "dancer", "walk", 2, look="floor_centre"))),
   out(energy=-6, cin=cin(w, "vertigo", walk("balcony_far", "queasy", "stagger", 2))),
   s_text="look over the floor, the crowd waves (+4, music variation)", f_text="vertigo (-6, queasy)", hook=walk("balcony_rail", "dancer", "walk", 2, look="floor_centre"))
ch("warehouse.balcony", "promoter", A("v03"), "beckon",
   out(route="warehouse.booth", flags=["wh_promoter_nod"], energy=4, cin=cin(w, "promoter_walk", walk("balcony_stairs", "dancer", "walk", 2, look="v03"))),
   out(flags=["wh_promoter_snub"], energy=-4),
   s_text="the promoter waves you straight to the booth (route warehouse.booth)", f_text="he looks through you (-4)", hook=walk("balcony_stairs", "dancer", "walk", 2, look="v03"))

exits("warehouse.chill")
ob("warehouse.chill", "sofas", T("sofa_left"), "glow",
   out(flags=["wh_rested"], energy=10, cin=cin(w, "sofa_rest", walk("sofa_nook", "recovered", "walk", 3, look="s01"))),
   out(flags=["wh_dozed"], energy=-10, cin=cin(w, "sofa_doze", walk("sofa_front", "queasy", "walk", 2))),
   s_text="sink into the sofa and recover (+10)", f_text="you doze off and a phase is lost (-10)")
ch("warehouse.chill", "wizard", T("wizard_chill"), "beckon",
   out(route="1", flags=["wh_wizard_met"]), out(flags=["wh_wizard_shrug"], energy=-2),
   s_text="the wizard again: the Bassment (route 1)", f_text="he shrugs (-2)", av=avail(none=["wh_wizard_met"]))
ft("warehouse.chill", "lavalamp", T("lavalamp"), "pulse",
   out(flags=["wh_lava_gaze"], energy=5, music="variation"), out(energy=-3, music="dip"),
   s_text="watch the wax rise (+5, music variation)", f_text="it is only a lamp (-3, music dips)")

exits("warehouse.booth")
ob("warehouse.booth", "decks", P(0.0, 1.1, -8.25), "glow",
   out(flags=["wh_dj_set"], energy=8, music="variation", cin=cin(w, "drop_decks", walk("booth_decks", "dj", "walk", 3))),
   out(flags=["wh_wrong_record"], energy=-8, music="dip", cin=cin(w, "wrong_record", walk("booth_decks", "queasy", "stagger", 2))),
   s_text="drop the decks: DJ role, the drop (+8, music variation)", f_text="the wrong record, the crowd drifts (-8, music dips)", hook=walk("booth_decks", "dj", "walk", 2))
sc("warehouse.booth", "headphones", T("headphones_booth"), "glow",
   out(flags=["wh_headphones"], energy=6, music="variation", cin=cin(w, "headphones_on", walk("booth_decks", "dj", "walk", 2))), out(flags=["wh_headphones_wrong"], energy=-3),
   s_text="the VIP headphones: a private mix (+6, music variation)", f_text="they are on the wrong way round (-3)", av=avail(all=["wh_vip_pass"], none=["wh_headphones", "wh_headphones_wrong"], once=True))

exits("warehouse.exit", anchors={"right": T("crack_door")}, looks={"right": "crack"})
ch("warehouse.exit", "bouncer", A("d01"), "beckon",
   out(route="mothership", flags=["wh_door_clear"], energy=4), out(route="underworld", flags=["wh_thrown_out"], energy=-6, cin=cin(w, "thrown_out", walk("door_r", "queasy", "run", 2))),
   s_text="the bouncer nods you through to the light (route mothership)", f_text="thrown out, through the crack (route underworld, -6, flag wh_thrown_out)", av=avail(none=["wh_vip_pass"]))
ch("warehouse.exit", "bouncer_vip", A("d01"), "beckon",
   out(route="mothership", flags=["wh_guest_list"], energy=6), out(route="mothership", flags=["wh_pass_scuffed"], energy=-3),
   s_text="the VIP pass: waved on to the light (+6)", f_text="he squints at the pass; the same door, slower (-3)", av=avail(all=["wh_vip_pass"]))

# =========================================================================================================================================================
# The Mothership (mothership)
# =========================================================================================================================================================
w = "mothership"
exits("mothership")
ch("mothership", "grey", A("g08"), "beckon",
   out(flags=["ms_grey_friend"], energy=5, cin=cin(w, "grey_gentle", walk("deck_ramp", "dancer", "walk", 2, look="g08"))),
   out(flags=["ms_probed"], energy=-7, cin=cin(w, "probe_light", walk("deck_sw_corner", "queasy", "stagger", 2))),
   s_text="a grey beckons; it is examined gently (+5)", f_text="the probe light finds you (-7, flag ms_probed)", hook=walk("deck_ramp", "dancer", "walk", 2, look="g08"))
ch("mothership", "dj", A("m01"), "beckon",
   out(flags=["ms_dj_pal"], energy=6, music="variation", cin=cin(w, "dais_walk", walk("deck_dais", "on_stage", "climb", 3, look="m01"))),
   out(flags=["ms_feedback"], energy=-6, music="dip"),
   s_text="the alien DJ sets the headphones right: up on the dais (+6, music variation)", f_text="feedback squeals (-6, music dips)")

exits("mothership.gallery")
ft("mothership.gallery", "window", T("glow_g"), "glow",
   out(flags=["ms_saw_planet"], energy=5, music="variation", cin=cin(w, "window_gaze", walk("planet_window", "dancer", "walk", 3))),
   out(energy=-5, cin=cin(w, "cruiser_glare", walk("gallery_west", "queasy", "stagger", 2))),
   s_text="gaze at the planet (+5, music variation)", f_text="the cruiser's searchlight (-5, queasy)")
ob("mothership.gallery", "menu", T("menu_g"), "pulse",
   out(flags=["ms_ordered"], energy=8, cin=cin(w, "order", walk("gallery_mid", "dancer", "walk", 2))),
   out(flags=["ms_bad_order"], energy=-6, cin=cin(w, "bad_order", walk("gallery_west", "queasy", "walk", 2))),
   s_text="order from the hologram menu (+8)", f_text="it orders for you (-6, queasy)")

exits("mothership.reactor")
ob("mothership.reactor", "core", T("core_r"), "pulse",
   out(flags=["ms_surge"], energy=8, music="variation", cin=cin(w, "core_surge", walk("reactor_core", "on_stage", "climb", 3))),
   out(flags=["ms_alarm"], energy=-8, music="dip", cin=cin(w, "alarm_run", walk("catwalk_door", "queasy", "run", 2))),
   s_text="a power surge (+8, music variation)", f_text="the alarm sounds (-8, music dips)")
ch("mothership.reactor", "engineer", A("reactor_s01"), "beckon",
   out(flags=["ms_badge"], energy=4, cin=cin(w, "badge", walk("catwalk_mid", "dancer", "walk", 2, look="reactor_s01"))), out(flags=["ms_shooed"], energy=-3),
   s_text="the engineer clips a badge on you (flag ms_badge: the star chart on the bridge)", f_text="he shoos you off (-3)", av=avail(none=["ms_badge"]))

exits("mothership.bridge")
ob("mothership.bridge", "helm", T("captain_h"), "glow",
   out(flags=["ms_warp"], energy=10, music="variation", cin=cin(w, "warp", walk("helm", "on_stage", "climb", 3))),
   out(flags=["ms_crash"], energy=-10, music="dip", cin=cin(w, "crash", walk("bridge_door", "queasy", "stagger", 2))),
   s_text="the helm: warp (+10, music variation)", f_text="a crash, thrown back towards the airlock (-10, music dips)")
sc("mothership.bridge", "star_chart", T("globe_b"), "flicker",
   out(flags=["ms_star_chart"], energy=6, music="variation"), out(flags=["ms_lockout"], energy=-4),
   s_text="the star chart opens (flag ms_star_chart, +6, music variation)", f_text="locked out (-4)", av=avail(all=["ms_badge"], none=["ms_star_chart", "ms_lockout"], once=True))

exits("mothership.exit")
ch("mothership.exit", "exam", A("med02"), "beckon",
   out(flags=["ms_exam_ok"], energy=6, cin=cin(w, "exam_ok", walk("exam", "dancer", "walk", 2, look="med01"))),
   out(route="ward", flags=["ms_probed"], energy=-8, cin=cin(w, "exam_strapped", walk("exam", "queasy", "stagger", 2))),
   s_text="the exam passes (+6)", f_text="strapped to the table, out the exam door (route ward, -8)")
ob("mothership.exit", "airlock_wheel", T("wheel_a"), "pulse",
   out(route="hospital", flags=["ms_airlock_cycled"], energy=5, cin=cin(w, "cycle_lock", walk("airlock_door", "dancer", "walk", 2))),
   out(route="hospital", flags=["ms_airlock_alarm"], energy=-6, cin=cin(w, "alarm_lock", walk("med_door", "queasy", "stagger", 2))),
   s_text="cycle the airlock (route hospital, +5)", f_text="the alarm; out anyway, shaken (route hospital, -6)")

# =========================================================================================================================================================
# The Underworld (underworld)
# =========================================================================================================================================================
w = "underworld"
exits("underworld")
ch("underworld", "bouncer", A("gate_bouncer"), "beckon",
   out(flags=["uw_gate_pass"], energy=5, cin=cin(w, "gate_nod", walk("arena_gate", "dancer", "walk", 2, look="gate_bouncer"))),
   out(flags=["uw_tossed"], energy=-7, cin=cin(w, "gate_shove", walk("arena_edge", "queasy", "stagger", 2))),
   s_text="the demon bouncer waves you in (+5)", f_text="no ticket: shoved back (-7)", av=avail(none=["wh_thrown_out"]))
ch("underworld", "bouncer_grudge", A("gate_bouncer"), "beckon",
   out(flags=["uw_gate_pass"], energy=4, cin="underworld.gate_nod"), out(route="underworld.furnace", flags=["uw_tossed"], energy=-8, cin="underworld.gate_shove"),
   s_text="he laughs: you were thrown out of the club (+4)", f_text="he remembers; thrown down to the furnace (route underworld.furnace, -8)", av=avail(all=["wh_thrown_out"]))
ob("underworld", "chains", T("chains_a"), "glow",
   out(flags=["uw_swung"], energy=8, music="variation", cin=cin(w, "chain_swing", walk("arena_gate", "on_stage", "climb", 3))),
   out(flags=["uw_caged"], energy=-9, cin=cin(w, "dragged_cage", place("cage", "queasy", "carried", 3))),
   s_text="swing on the chains (+8, music variation)", f_text="dragged to the cage (-9)")

exits("underworld.court")
ft("underworld.court", "seal", T("seal_c"), "glow",
   out(flags=["uw_seal"], energy=6, music="variation", cin=cin(w, "seal_stand", walk("court_mid", "on_stage", "walk", 2))),
   out(energy=-8, music="dip", cin=cin(w, "seal_burn", walk("court_in", "queasy", "stagger", 2))),
   s_text="stand on the seal: the court bows (+6, music variation)", f_text="the seal burns (-8, music dips)")
ch("underworld.court", "queen", A("court_g06"), "beckon",
   out(flags=["uw_queen_favour"], energy=8, cin=cin(w, "queen_dance", walk("court_mid", "dancer", "walk", 3, look="court_g06"))),
   out(flags=["uw_hexed"], energy=-6, music="dip"),
   s_text="the horned queen dances with you (+8)", f_text="she hexes you (-6, music dips)")

exits("underworld.furnace")
ob("underworld.furnace", "anvil", T("anvil_f0"), "glow",
   out(flags=["uw_forged"], energy=6, music="variation", cin=cin(w, "forge", walk("furnace_mid", "on_stage", "walk", 2))),
   out(energy=-8, cin=cin(w, "forge_burn", walk("furnace_door", "queasy", "stagger", 2))),
   s_text="forge a beat on the anvil (+6, music variation)", f_text="a burn (-8)")
ft("underworld.furnace", "ladle", T("ladle_f"), "pulse",
   out(flags=["uw_molten"], energy=5), out(energy=-7, cin=cin(w, "ladle_spill", walk("furnace_in", "queasy", "stagger", 2))),
   s_text="pour the molten metal (+5)", f_text="it spills (-7)")

exits("underworld.pit")
ft("underworld.pit", "lava_bridge", T("lavaflow_p"), "glow",
   out(flags=["uw_bridge"], energy=8, music="variation", cin=cin(w, "lava_bridge", walk("pit_edge", "on_stage", "walk", 3))),
   out(flags=["uw_scorched"], energy=-12, music="dip", cin=cin(w, "lava_fall", walk("pit_rim_e", "queasy", "stagger", 3))),
   s_text="cross the lava bridge (+8, music variation)", f_text="you fall, scorched (-12, music dips)")
ob("underworld.pit", "brazier", T("uw_br_p0"), "flicker",
   out(flags=["uw_lit"], energy=4), out(energy=-5),
   s_text="light the pit braziers (+4)", f_text="the flare burns your hand (-5)")

exits("underworld.exit")
ob("underworld.exit", "throne", T("uw_throne"), "glow",
   out(flags=["uw_throned"], energy=10, music="variation", cin=cin(w, "take_throne", walk("throne", "on_stage", "climb", 3))),
   out(route="ward", flags=["uw_devoured"], energy=-10, cin=cin(w, "devoured", walk("throne_steps", "queasy", "stagger", 2))),
   s_text="take the throne: resident DJ (+10, music variation)", f_text="devoured, dumped out the south door (route ward, -10)")

# =========================================================================================================================================================
# The Hospital (hospital)
# =========================================================================================================================================================
w = "hospital"
exits("hospital")
ch("hospital", "nurse", A("h02"), "beckon",
   out(flags=["hp_wheeled"], energy=6, cin=cin(w, "wheel_on", walk("ward_door", "dancer", "carried", 3, look="h02"))),
   out(energy=-7, cin=cin(w, "back_to_bed", walk("bed_corner", "queasy", "stagger", 2))),
   s_text="the nurse wheels you on (+6)", f_text="back to bed (-7, queasy)", hook=walk("bed_far", "dancer", "walk", 2, look="h02"))
ch("hospital", "family", A("h03"), "beckon",
   out(flags=["hp_family"], energy=8, music="variation", cin=cin(w, "family_cheer", walk("bed_far", "dancer", "walk", 2, look="h03"))),
   out(flags=["hp_visitor_asleep"], energy=-4), s_text="the family cheers (+8, music variation)", f_text="a visitor sleeps through it (-4)")
ft("hospital", "monitor", T("monitor_w"), "pulse",
   out(energy=5, music="variation"), out(energy=-9, music="dip", cin=cin(w, "flatline", walk("bed_corner", "queasy", "stagger", 2))),
   s_text="the heart monitor keeps the beat (+5, music variation)", f_text="it flatlines (-9, music dips)")

exits("hospital.corridor")
ch("hospital.corridor", "trolley", A("h07"), "beckon",
   out(flags=["hp_tea"], energy=6, cin=cin(w, "tea", walk("corridor_mid", "dancer", "walk", 2, look="h07"))),
   out(energy=-5, cin=cin(w, "tea_spill", walk("corridor_mid", "queasy", "stagger", 2))),
   s_text="a cup of tea from the trolley (+6)", f_text="it spills (-5)")
sc("hospital.corridor", "quiet_door", W("corridor_quiet_door"), "crack",
   out(flags=["hp_saw_quiet"], energy=3, cin=cin(w, "peek_quiet", walk("corridor_quiet_door", "dancer", "walk", 2))), out(flags=["hp_quiet_locked"], energy=-4),
   s_text="a peek into the quiet room (flag hp_saw_quiet)", f_text="locked (-4)", av=avail(none=["hp_saw_quiet", "hp_quiet_locked"], once=True))

exits("hospital.dayroom")
ob("hospital.dayroom", "tv", T("tv_set"), "flicker",
   out(flags=["hp_tv_on"], energy=6, music="variation", cin=cin(w, "tv_watch", walk("day_tv_in", "dancer", "walk", 3, look="tv_set"))),
   out(energy=-5, music="dip", cin=cin(w, "tv_static", walk("dayroom_mid", "queasy", "stagger", 2))),
   s_text="the right channel (+6, music variation)", f_text="static (-5, music dips)")
ch("hospital.dayroom", "granny", A("h08"), "beckon",
   out(flags=["hp_granny_tale"], energy=8, cin=cin(w, "granny", walk("dayroom_mid", "dancer", "walk", 2, look="h08"))),
   out(energy=-5, cin=cin(w, "granny_long", walk("dayroom_mid", "queasy", "walk", 2))),
   s_text="granny tells the story (+8)", f_text="the long version (-5, queasy)")

exits("hospital.cafeteria")
sc("hospital.cafeteria", "vending", T("vending_f"), "flicker",
   out(flags=["hp_token"], energy=6, cin=cin(w, "vend", walk("cafe_serving", "dancer", "walk", 2))), out(flags=["hp_jam"], energy=-3),
   s_text="a snack and a brass token (flag hp_token: free drinks in the late cafeteria) (+6)", f_text="the machine eats the coin (-3)", av=avail(none=["hp_token", "hp_jam"], once=True))
ch("hospital.cafeteria", "kid", A("h14"), "beckon",
   out(flags=["hp_kid_friend"], energy=6, cin=cin(w, "kid", walk("cafe_mid", "dancer", "walk", 2, look="h14"))), out(energy=-5),
   s_text="the waving kid shows you a trick (+6)", f_text="the kid cries (-5)")

exits("hospital.garden")
ft("hospital.garden", "lamp", T("lamp_g0"), "flicker",
   out(flags=["hp_lamp_lit"], energy=5, music="variation"), out(energy=-5, music="dip"),
   s_text="the lamppost comes on (flag hp_lamp_lit, +5, music variation)", f_text="the bulb pops (-5, music dips)")
ch("hospital.garden", "mum", A("h16"), "beckon",
   out(flags=["hp_called_home"], energy=6, cin=cin(w, "phone", walk("garden_south", "dancer", "walk", 2, look="h16"))), out(energy=-4),
   s_text="mum on the phone holds it out to you (+6)", f_text="no answer (-4)")

exits("hospital.exit")
ob("hospital.exit", "mic", T("mic_band"), "glow",
   out(flags=["hp_sang"], energy=10, music="variation", cin=cin(w, "sing", walk("bandstand_front", "on_stage", "climb", 3))),
   out(energy=-8, music="dip", cin=cin(w, "feedback", walk("bandstand", "queasy", "stagger", 2))),
   s_text="sing at the bandstand mic (flag hp_sang, +10, music variation)", f_text="feedback (-8, music dips)")

# =========================================================================================================================================================
# The Ward (mental_hospital)
# =========================================================================================================================================================
w = "ward"
exits("ward")
ch("ward", "orderly", A("e04"), "beckon",
   out(flags=["wd_orderly_ok"], energy=4, cin=cin(w, "orderly_nod", walk("day_centre", "dancer", "walk", 2, look="e04"))),
   out(flags=["wd_treated"], energy=-9, cin=cin(w, "to_treatment", place("treat", "queasy", "carried", 3))),
   s_text="the orderly lets it pass (+4)", f_text="taken to the treatment room (-9)")
ft("ward", "window", T("wlight_d"), "glow",
   out(flags=["wd_window"], energy=5, music="variation", cin=cin(w, "window_gaze", walk("bars_in", "dancer", "walk", 2, look="x09"))),
   out(energy=-5, music="dip"), s_text="the barred window lets the light in (+5, music variation)", f_text="the bars rattle (-5, music dips)")

exits("ward.art")
ch("ward.art", "painter", A("x10"), "beckon",
   out(flags=["wd_painted"], energy=6, cin=cin(w, "paint_look", walk("art_easels", "dancer", "walk", 3, look="x10"))),
   out(flags=["wd_paint_spill"], energy=-6, cin=cin(w, "paint_spill", walk("art_mid", "queasy", "stagger", 2))),
   s_text="the painter shows a painting of a door (flag wd_painted: opens the courtyard from the corridor) (+6)", f_text="paint thrown over you (-6)")
ob("ward.art", "easel", T("easel_a3"), "glow",
   out(flags=["wd_own_painting"], energy=5), out(energy=-4), s_text="paint your own (+5)", f_text="a smudge (-4)")

exits("ward.dorm")
ch("ward.dorm", "sleeper", A("x14"), "beckon",
   out(flags=["wd_lullaby"], energy=8, cin=cin(w, "lullaby", walk("dorm_mid", "recovered", "walk", 2, look="x14"))),
   out(energy=-6, cin=cin(w, "woken", walk("dorm_door", "queasy", "stagger", 2))),
   s_text="a lullaby for the sleeper (+8)", f_text="you wake him (-6)")
ob("ward.dorm", "cabinet", T("cab_m0"), "glow",
   out(flags=["wd_dorm_key"], energy=3, cin=cin(w, "search", walk("dorm_bed", "dancer", "walk", 2))), out(energy=-7, music="dip"),
   s_text="a key in the cabinet (flag wd_dorm_key) (+3)", f_text="the alarm bell (-7, music dips)")

exits("ward.corridor", anchors={}, looks={})
ob("ward.corridor", "phone", T("phone_o"), "flicker",
   out(flags=["wd_phone_call"], energy=5), out(energy=-3), s_text="answer the office phone (+5)", f_text="dial tone (-3)")
ch("ward.corridor", "king", A("x06"), "beckon",
   out(flags=["wd_king"], energy=6, cin=cin(w, "king", walk("corr_mid", "dancer", "walk", 2, look="x06"))), out(energy=-5),
   s_text="the pacing king bows you past (+6)", f_text="he will not be disturbed (-5)")
sc("ward.corridor", "mural_door", T("mural_door"), "open",
   out(route="ward.courtyard", flags=["wd_mural_open"], energy=8, cin=cin(w, "mural_walk", walk("corr_east", "dancer", "walk", 2, look="mural_door"))),
   out(energy=-5, cin=cin(w, "mural_bump", walk("corr_mid", "queasy", "stagger", 2))),
   s_text="the painted door opens on the courtyard (route ward.courtyard, +8)", f_text="it is only paint (-5)", av=avail(all=["wd_painted"]))

exits("ward.courtyard")
ch("ward.courtyard", "chef", A("x01"), "beckon",
   out(flags=["wd_plate"], energy=6, cin=cin(w, "plate", walk("court_mid", "dancer", "walk", 2, look="x01"))),
   out(energy=-5, cin=cin(w, "plate_spill", walk("court_mid", "queasy", "stagger", 2))),
   s_text="a plate from the chef (+6)", f_text="it lands on you (-5)")
ft("ward.courtyard", "lights", T("lights_y"), "flicker",
   out(flags=["wd_lights"], energy=5, music="variation"), out(energy=-5, music="dip"),
   s_text="the string lights come up (+5, music variation)", f_text="a fuse blows (-5, music dips)")

exits("ward.exit")
ob("ward.exit", "talent_lamp", T("cage_y"), "glow",
   out(flags=["wd_star"], energy=10, music="variation", cin=cin(w, "star_turn", walk("stage", "on_stage", "climb", 3))),
   out(flags=["wd_lights_out"], energy=-10, music="dip", cin=cin(w, "lights_out", walk("stage_edge", "queasy", "stagger", 2))),
   s_text="the talent stage: a star turn (+10, music variation)", f_text="lights out (-10, music dips)")

# =========================================================================================================================================================
# The Hospital, late (hospital)
# =========================================================================================================================================================
w = "hospital_late"
exits("hospital_late")
ft("hospital_late", "lamp", T("lamp_g1"), "flicker",
   out(flags=["hp_lamp_lit"], energy=5, music="variation"), out(energy=-5, music="dip"),
   s_text="the lamppost comes on (+5, music variation)", f_text="the bulb pops (-5)", av=avail(none=["hp_lamp_lit"]))
ft("hospital_late", "lamp_lit", T("lamp_g1"), "pulse",
   out(flags=["hl_lamp_again"], energy=6, music="variation"), out(energy=-3),
   s_text="the lamp you lit burns steady, lit differently on the second round (+6)", f_text="it gutters (-3)", av=avail(all=["hp_lamp_lit"]))
ch("hospital_late", "doctor", A("h17"), "beckon",
   out(flags=["hl_doctor"], energy=5, cin=cin(w, "doctor", walk("garden_north", "dancer", "walk", 2, look="h17"))), out(energy=-5),
   s_text="the garden doctor beckons you on (+5)", f_text="he checks his clipboard and frowns (-5)")

exits("hospital_late.cafe")
ob("hospital_late.cafe", "vending", T("vending_f2"), "flicker",
   out(flags=["hp_token"], energy=6), out(energy=-3), s_text="a snack from the machine (+6, flag hp_token)", f_text="it is out of order (-3)", av=avail(none=["hp_token"]))
ob("hospital_late.cafe", "vending_token", T("vending_f2"), "pulse",
   out(energy=10, music="variation", flags=["hl_free_drink"]), out(energy=-3), s_text="the brass token buys a free drink (+10, music variation)", f_text="it is the wrong token (-3)",
   av=avail(all=["hp_token"]))
ch("hospital_late.cafe", "kid", A("h14"), "beckon",
   out(energy=6, cin=cin(w, "kid", walk("cafe_mid", "dancer", "walk", 2, look="h14"))), out(energy=-5),
   s_text="the waving kid again (+6)", f_text="the kid cries (-5)")

exits("hospital_late.quiet")
ob("hospital_late.quiet", "nightlight", T("nl_q0"), "pulse",
   out(flags=["hl_calm"], energy=10, cin=cin(w, "calm", walk("quiet_far", "recovered", "walk", 3))), out(energy=-5),
   s_text="the night light calms you (+10)", f_text="it goes out (-5)")
ft("hospital_late.quiet", "nightlight_b", T("nl_q2"), "glow",
   out(energy=5, music="variation"), out(energy=-4, music="dip"), s_text="a second light, a softer mix (+5)", f_text="it flickers (-4)")

exits("hospital_late.exit")
ob("hospital_late.exit", "mic", T("mic_band"), "glow",
   out(flags=["hp_sang"], energy=10, music="variation", cin=cin(w, "sing", walk("bandstand_front", "on_stage", "climb", 3))),
   out(energy=-8, music="dip", cin=cin(w, "feedback", walk("bandstand", "queasy", "stagger", 2))),
   s_text="sing at the mic (+10)", f_text="feedback (-8)", av=avail(none=["hp_sang"]))
ob("hospital_late.exit", "mic_encore", T("mic_band"), "pulse",
   out(flags=["hl_encore"], energy=10, music="variation", cin="hospital_late.sing"), out(energy=-6, music="dip"),
   s_text="the encore: they remember the song (+10)", f_text="hoarse (-6)", av=avail(all=["hp_sang"]))

# =========================================================================================================================================================
# The Ward, late (mental_hospital)
# =========================================================================================================================================================
w = "ward_late"
exits("ward_late")
ft("ward_late", "stage_lamp", T("cage_y"), "glow",
   out(energy=8, music="variation"), out(energy=-6, music="dip"), s_text="the stage lamp warms the courtyard (+8, music variation)", f_text="it blinds you (-6)")
ft("ward_late", "fireflies", T("flies_y"), "flicker",
   out(flags=["wl_fireflies"], energy=6), out(energy=-4), s_text="fireflies settle on you (+6)", f_text="they scatter (-4)")

exits("ward_late.treat")
ch("ward_late.treat", "orderly", A("x02"), "beckon",
   out(flags=["wl_orderly_ok"], energy=4, cin=cin(w, "orderly", walk("treat", "dancer", "walk", 2, look="x02"))),
   out(energy=-9, music="dip", cin=cin(w, "injection", walk("treat_door", "queasy", "stagger", 2))),
   s_text="the orderly checks the clipboard and nods (+4)", f_text="the needle (-9, music dips)")
ob("ward_late.treat", "trolley", T("trolley_t"), "glow",
   out(energy=6), out(energy=-5), s_text="the trolley holds a gift (+6)", f_text="it rattles away (-5)")

exits("ward_late.dorm")
ch("ward_late.dorm", "sleeper", A("x13"), "beckon",
   out(flags=["wl_lullaby"], energy=8, cin=cin(w, "lullaby", walk("dorm_mid", "recovered", "walk", 2, look="x13"))), out(energy=-6),
   s_text="a lullaby (+8)", f_text="you wake him (-6)")
ob("ward_late.dorm", "cabinet", T("cab_m1"), "glow",
   out(energy=3, cin=cin(w, "search", walk("dorm_bed", "dancer", "walk", 2)), flags=["wl_cabinet"]), out(energy=-7, music="dip"),
   s_text="the cabinet gives a little (+3)", f_text="the alarm bell (-7)")

exits("ward_late.exit")
ch("ward_late.exit", "stare", A("x09"), "beckon",
   out(flags=["wl_window"], energy=5, cin=cin(w, "stare", walk("bars_in", "dancer", "walk", 2, look="x09"))), out(energy=-5),
   s_text="he is staring at the bars; you look with him (+5)", f_text="he turns away (-5)")


# =========================================================================================================================================================
def write() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for world, lst in HOTSPOTS.items():
        (OUT / f"{world}.json").write_text(json.dumps({"world": world, "hotspots": lst}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Visual coverage matrix (workstream C)", "",
             "Generated by `tools/run/make_hotspots.py` from the same tables that write `content/run/hotspots/<world>.json`; `python3 tools/run/check_hotspots.py` enforces the rules and the reachability.",
             "S = the outcome when the player's last block passes, F = when it fails. Status: `data` = authored and checked, `engine` = awaiting workstream A, `tests` = awaiting workstream E.", "",
             "| World | Scene | Hotspot | Kind | S outcome | F outcome | Available when | Status |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in ROWS:
        gate = ", ".join(r["gate"]) or "always"
        dflt = " (default)" if r["default"] else ""
        lines.append(f"| {r['world']} | {r['scene']} | {r['hotspot'].split('.', 1)[1] if r['hotspot'].startswith(r['scene']) else r['hotspot']}{dflt} | {r['kind']} | {r['s']} | {r['f']} | {gate} | data |")
    lines.append("")
    DOC.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("%d hotspots in %d worlds, %d cinematics" % (sum(len(v) for v in HOTSPOTS.values()), len(HOTSPOTS), len(CINEMATICS)))


if __name__ == "__main__":
    write()
