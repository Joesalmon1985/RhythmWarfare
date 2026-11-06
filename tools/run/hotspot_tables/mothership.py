"""Hotspot table of The Mothership: scene prefix `mothership`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

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
