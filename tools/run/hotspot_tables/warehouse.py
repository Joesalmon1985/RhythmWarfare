"""Hotspot table of The Warehouse (night_one): scene prefix `warehouse`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

w = "warehouse"
exits("warehouse")
# ---- the Floor's own quest entrances (the shared wiring step; lead ruling 15, content/narrative/graph.json `warehouse_rave.*`): the hub shows all four, like the other hubs. An ungated
# hatch into the Bassment (the wizard stays an extra, rhythm-gated way in) and the three copies of the Balcony's star, the Booth's radio and the Bar's ember, each a lit gate in its
# quest's colour with its herald beside it, taken at the lap's end through the port; a failure flickers out (-4) and the default exit takes over. They stand in an arc on the Floor's left
# side between the stairs to the balcony and the wizard, so one look from the middle of the Floor holds the four and the wizard, and the route window's look from the booth frames them.
# (name, herald quest, gate (x, z), herald (x, z), route, text on success, text on failure). They come before the wizard: the heralds' opening looks (three, one a block) go to
# the gates first, the wizard after them; each look also frames the other entrances on offer where they fit (RunJourney.herald_looks).
GATES = [
    ("bassment", "dungeon", (-5.0, 3.25), (-3.7, 3.3), "bassment", "a violet hatch, the wizard pointing down: the Bassment (route bassment)", "the hatch sinks out of sight (-4)"),
    ("squadron", "squadron", (-4.5, 4.75), (-3.2, 4.9), "path:squadron", "a green gate, the Gunner pointing: the Mission Count path (route path:squadron)", "the radio gate gutters out (-4)"),
    ("ember", "ember", (-3.75, 6.25), (-2.45, 6.0), "path:ember", "an orange gate, Bram holding up the ember in its glass: the Ember Road path (route path:ember)", "the ember gutters out (-4)"),
    ("gospel", "gospel", (-2.75, 7.5), (-4.0, 8.1), "path:gospel", "a gold gate under one white star, the shepherd pointing: the Gospel path (route path:gospel)", "the star gate flickers out (-4)"),
]
for _n, _q, _g, _h, _route, _ok, _bad in GATES:
    _portal = sc("warehouse", "enter_" + _n, P(_g[0], 1.0, _g[1]), "pulse", out(route=_route), out(energy=-4), s_text=_ok, f_text=_bad)
    if _q != "dungeon":
        _portal["look"]["finished"] = finished(_q)

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
   s_text="look over the floor, the crowd waves (+4, music variation)", f_text="vertigo (-6, queasy)", hook=walk("balcony_rail", "dancer", "walk", 2, look="floor_centre"),
   av=avail(none=["wh_saw_floor"]))  # (once the floor has been seen the star below takes its place in the 2 to 4 rule)
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

# ---- the three portals into the paths (docs/THREE_PATHS_AND_FACES_PLAN.md 3.3, stage 2): secrets that pulse, never the default, repeatable; a failure flickers out (-4) and the default exit takes over.
# Each takes the place of something in its room's 2 to 4 rule: the star appears once the floor has been seen from the rail, the ember once the stranger's VIP pass is in the pocket, the radio always (the booth has room).
# The route is "path:<id>"; RunData leaves a portal out of play until content/paths/<id>/run.json exists (RW_PATH_REMAP=gospel=stub plays the stub path through the balcony star).
w = "warehouse"
# (the entrances stand where the camera's rail can see them: docs/art/HERALDS.md, the visibility rule. The star is a lit doorway in the balcony's back wall, seen from the far end
# of the balcony and over the shoulder from its door; the radio stands on the stage at the booth's corner, in front of the decks rather than behind them; the ember is a glass
# on the bar counter, clear of the people by the curtain.)
_portal = sc("warehouse.balcony", "star", P(-10.75, 1.2, 0.5), "pulse", out(route="path:gospel"), out(energy=-4),
   s_text="the figure under the projected star: the Gospel path (route path:gospel, house 124)", f_text="the star flickers out (-4)", av=avail(all=["wh_saw_floor"]))
_portal["look"]["finished"] = finished("gospel")
_portal = sc("warehouse.booth", "radio", P(2.8, 0.6, -6.6), "pulse", out(route="path:squadron"), out(energy=-4),
   s_text="the flickering military radio and the bomber's shadow: the Mission Count path (route path:squadron, dubstep 140)", f_text="the radio crackles out (-4)")
_portal["look"]["finished"] = finished("squadron")
_portal = sc("warehouse.bar", "ember", P(11.75, 1.05, 3.75), "pulse", out(route="path:ember"), out(energy=-4),
   s_text="a warm ember in a glass: the Ember Road path (route path:ember, psytrance 145)", f_text="the ember gutters out (-4)", av=avail(all=["wh_vip_pass"]))
_portal["look"]["finished"] = finished("ember")

# ---- the heralds (lead ruling 25, docs/art/HERALDS.md): a character of each quest at its entrance, gesturing towards it. Scenery of the entrance, never a choice.
from heralds import herald  # noqa: E402
herald("dungeon", "warehouse.wizard", self_thing=True, toward=T("sign_wc_door"))  # the wizard IS the entrance: his staff held, his arm pointing to the corridor and the hatch
herald("gospel", "warehouse.balcony.star", at=(-10.05, -0.55), gate=True)  # the shepherd of the first night, beside the lit doorway (the star has no thing of its own)
herald("squadron", "warehouse.booth.radio", at=(3.7, -5.6))  # the Gunner, on the stage beside the radio, seen from the decks
herald("ember", "warehouse.bar.ember", at=(10.2, 2.9))  # Bram, under the bar's lamp, pointing to the glass on the counter
herald("dungeon", "warehouse.chill.wizard", self_thing=True, toward=W("chill_door"), mark_over_self=True)  # the chill-out's wizard: the Bassment's mark over his hat, his arm to the way out

for _n, _q, _g, _h, _route, _ok, _bad in GATES:
    herald(_q, "warehouse.enter_" + _n, at=_h, gate=True)
