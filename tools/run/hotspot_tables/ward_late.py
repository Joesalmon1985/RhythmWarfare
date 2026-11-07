"""Hotspot table of The Ward, late (node world mental_hospital): scene prefix `ward_late`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

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
sc("ward_late.treat", "enter_bassment", P(16.4, 1.1, 11.8), "pulse", out(route="bassment"), out(energy=-4),
   s_text="a hatch under the trolley bay, chalk marks round it: the Bassment (route bassment)", f_text="the hatch is stuck fast (-4)")
sc("ward_late.dorm", "enter_gospel", P(28.8, 1.1, 8.3), "pulse", out(route="path:gospel"), out(energy=-4),
   s_text="a figure of light in the alcove under a drawn star: the Gospel path (route path:gospel)", f_text="the light goes out (-4)")

# ---- the heralds (lead ruling 25, docs/art/HERALDS.md).
from heralds import herald  # noqa: E402
herald("dungeon", "ward_late.treat.enter_bassment", at=(14.8, 11.9), gate=True)
herald("gospel", "ward_late.dorm.enter_gospel", at=(29.2, 10.0), gate=True)
