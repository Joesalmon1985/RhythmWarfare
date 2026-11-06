"""Hotspot table of The Underworld: scene prefix `underworld`.

Part of the run's hotspot tables; `python tools/run/make_hotspots.py` regenerates content/run/hotspots/ and docs/VISUAL_COVERAGE.md from these files (it imports every module in hotspot_tables/
in a fixed order). Add this world's objects here, with the helpers of hotspots_common.py. Keep calls in the order the output should list them.
"""
from hotspots_common import T, W, A, P, walk, place, cin, out, avail, exits, ch, ob, ft, sc, finished

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
