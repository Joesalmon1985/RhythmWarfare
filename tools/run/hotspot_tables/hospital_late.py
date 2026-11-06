"""Hotspot table of The Hospital, late (node world hospital): scene prefix `hospital_late`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

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
