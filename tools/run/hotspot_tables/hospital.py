"""Hotspot table of The Hospital: scene prefix `hospital`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

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

# ---- the quest entrances (N2.4, lead rulings 15 and 30; docs/narrative/N2_2_ROUTER.md): ungated secrets that pulse, repeatable, never the default, taken at the lap's end through the port; a
# failure flickers out (-4) and the default exit takes over. Each is a lit gate in its quest's colour with its herald beside it (docs/art/HERALDS.md). The graph's ids and objects: content/narrative/graph.json.
# (name, herald quest, gate (x, z), herald (x, z), route, text on success, text on failure). The order is the order of the heralds' opening looks.
w = "hospital"
GATES = [
    ("ember", "ember", (1.9,3.5), (0.7,3.0), "path:ember", "an orange gate, Bram holding up the ember in its glass: the Ember Road path (route path:ember)", "the ember gutters out (-4)"),
    ("bassment", "dungeon", (4.1,4.3), (2.8,4.2), "bassment", "a violet gate, the wizard pointing down: the Bassment (route bassment)", "the gate sinks out of sight (-4)"),
    ("gospel", "gospel", (4.1,2.4), (2.8,2.7), "path:gospel", "a gold gate under one white star, the shepherd pointing: the Gospel path (route path:gospel)", "the star gate flickers out (-4)"),
    ("squadron", "squadron", (1.5,1.7), (0.4,2.4), "path:squadron", "a green gate, the Gunner pointing: the Mission Count path (route path:squadron)", "the radio gate gutters out (-4)"),
]
for _n, _q, _g, _h, _route, _ok, _bad in GATES:
    _portal = sc("hospital", "enter_" + _n, P(_g[0], 1.0, _g[1]), "pulse", out(route=_route), out(energy=-4), s_text=_ok, f_text=_bad)
    if _q != "dungeon":
        _portal["look"]["finished"] = finished(_q)

from heralds import herald  # noqa: E402
for _n, _q, _g, _h, _route, _ok, _bad in GATES:
    herald(_q, "hospital.enter_" + _n, at=_h, gate=True)

# Extra entrances in the side scenes (graph extra_routes), so each offers a quest beside its mainline exit.
EXTRAS = [
    ("hospital.dayroom", "enter_bassment", "dungeon", (23.5, -5.2), (22.3, -4.2), "bassment", "a violet gate by the sofa, the wizard pointing down: the Bassment (route bassment)", "the gate sinks out of sight (-4)"),
    ("hospital.cafeteria", "enter_gospel", "gospel", (40.0, -2.6), (38.8, -1.8), "path:gospel", "a gold gate under one white star, the shepherd pointing: the Gospel path (route path:gospel)", "the star gate flickers out (-4)"),
    ("hospital.garden", "enter_squadron", "squadron", (55.0, -3.5), (53.8, -2.6), "path:squadron", "a green gate on the lawn, the Gunner pointing: the Mission Count path (route path:squadron)", "the radio gate gutters out (-4)"),
    ("hospital_late.cafe", "enter_ember", "ember", (44.8, -2.8), (43.6, -2.0), "path:ember", "an orange gate, Bram holding up the ember in its glass: the Ember Road path (route path:ember)", "the ember gutters out (-4)"),
    ("hospital_late.quiet", "enter_bassment", "dungeon", (13.8, 13.1), (14.6, 11.7), "bassment", "a violet gate at the quiet room's far end, the wizard pointing down: the Bassment (route bassment)", "the gate sinks out of sight (-4)"),
]
for _scene, _n, _q, _g, _h, _route, _ok, _bad in EXTRAS:
    _portal = sc(_scene, _n, P(_g[0], 1.0, _g[1]), "pulse", out(route=_route), out(energy=-4), s_text=_ok, f_text=_bad)
    if _q != "dungeon":
        _portal["look"]["finished"] = finished(_q)
    herald(_q, _scene + "." + _n, at=_h, gate=True)
