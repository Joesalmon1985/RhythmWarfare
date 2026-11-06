"""Hotspot table of The Ward (node world mental_hospital): scene prefix `ward`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

w = "ward"
exits("ward")
ch("ward", "orderly", A("e04"), "beckon",
   out(flags=["wd_orderly_ok"], energy=4, cin=cin(w, "orderly_nod", walk("day_centre", "dancer", "walk", 2, look="e04"))),
   out(flags=["wd_treated"], energy=-9, cin=cin(w, "to_treatment", place("treat", "queasy", "carried", 3))),
   s_text="the orderly lets it pass (+4)", f_text="taken to the treatment room (-9)")
ft("ward", "window", T("wlight_d"), "glow",
   out(flags=["wd_window"], energy=5, music="variation", cin=cin(w, "window_gaze", walk("bars_in", "dancer", "walk", 2, look="x09"))),
   out(energy=-5, music="dip"), s_text="the barred window lets the light in (+5, music variation)", f_text="the bars rattle (-5, music dips)")

ob("ward", "cards", P(2.4, 0.5, 3.0), "beckon",
   out(activity="blackjack", cin=cin(w, "cards_sit", walk("day_cards", "dancer", "walk", 2))),
   out(energy=-3, cin=cin(w, "cards_waved_off", walk("day_cards", "dancer", "walk", 2))),
   s_text="sit at the empty chair: blackjack, the run stays in the day room (minigame)", f_text="the dealer waves you off (-3), the scene goes on by its default exit",
   radius=2.4, min_px=220, ring_m=1.7, selected="claim", window="any", pass_credit=0.25,
   on_select=cin(w, "cards_approach", walk("day_cards", "dancer", "walk", 2)))
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
