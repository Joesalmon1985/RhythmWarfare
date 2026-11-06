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
