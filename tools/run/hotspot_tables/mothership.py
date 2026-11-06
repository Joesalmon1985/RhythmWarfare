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


# ---- the quest entrances (work package N2.4, docs/narrative/N2_2_ROUTER.md "What N2.4 and N2.5 must author"): ungated secrets that pulse, repeatable, taken at the lap's end through the port; a miss
# flickers out (-4) with no route. Each is a lit doorway in its quest's colour (herald(..., gate=True): the entrance has no thing of its own), its herald beside it gesturing at it, the mark in its crown.
# The hub's four stand in a row on the far side of the dance floor, clear of the crowd (x -3 to 3, z 1 to 4.5), the exits (right wall) and the camera's own places (home, the ramp, the dais), so the
# camera at the deck's opening sees all four with their heralds. The ids are the graph's (content/narrative/graph.json).
w = "mothership"
from heralds import herald  # noqa: E402


def _entrance(scene, name, route, quest, pos, s_text, f_text, f_text_cost=-4):
    h = sc(scene, name, P(*pos), "pulse", out(route=route), out(energy=f_text_cost), s_text=s_text, f_text=f_text, radius=0.7)
    if route.startswith("path:"):
        h["look"]["finished"] = finished(route[len("path:"):])
    return h


_entrance("mothership", "enter_gospel", "path:gospel", "gospel", (2.6, 1.2, 0.6), "a figure of light under a single star in the viewport: the Gospel path (route path:gospel)", "the star flickers out (-4)")
_entrance("mothership", "enter_bassment", "bassment", "dungeon", (0.4, 1.2, 0.6), "the maintenance hatch in the deck plating, chalk marks beside it: the Bassment (route bassment)", "the hatch rattles shut (-4)")
_entrance("mothership", "enter_squadron", "path:squadron", "squadron", (-1.8, 1.2, 0.6), "the old military radio wired into the comms console, a bomber's shadow on the bulkhead: the Mission Count path (route path:squadron)", "the radio crackles out (-4)")
_entrance("mothership", "enter_ember", "path:ember", "ember", (4.8, 1.2, 0.6), "an ember glowing in a specimen jar: the Ember Road path (route path:ember)", "the ember gutters out (-4)")
herald("gospel", "mothership.enter_gospel", at=(3.7, 1.1), gate=True)
herald("dungeon", "mothership.enter_bassment", at=(1.5, 1.1), gate=True)
herald("squadron", "mothership.enter_squadron", at=(-0.7, 1.1), gate=True)
herald("ember", "mothership.enter_ember", at=(5.9, 1.1), gate=True)

_entrance("mothership.gallery", "enter_bassment", "bassment", "dungeon", (17.8, 1.2, 4.6), "a hatch in the gallery floor: the Bassment (route bassment)", "the hatch rattles shut (-4)")
herald("dungeon", "mothership.gallery.enter_bassment", side="left", gate=True)
_entrance("mothership.reactor", "enter_gospel", "path:gospel", "gospel", (33.6, 1.2, 2.0), "a figure of light under a star over the reactor catwalk: the Gospel path (route path:gospel)", "the star flickers out (-4)")
herald("gospel", "mothership.reactor.enter_gospel", side="right", gate=True)
_entrance("mothership.bridge", "enter_squadron", "path:squadron", "squadron", (46.5, 1.2, 6.5), "a radio on the comms console, a bomber's shadow on the screen: the Mission Count path (route path:squadron)", "the radio crackles out (-4)")
herald("squadron", "mothership.bridge.enter_squadron", side="right", gate=True)
