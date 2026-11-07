"""The harbour map (world `escape`: C11 to C14): the briefing hut again with the count painted higher, the harbour at night with its boat and searchlights, the neutral coast (the one
saturated place in the path) and the cell with the window latch.

Plan (x east, z south, metres):

                cell(0..10, -8..0)
    hut2(-12..0, 0..8) | quay(0..22, 0..12) | coast(22..44, 0..14)
"""
from __future__ import annotations

from squadron_lib import BUSY, CROWD_OUT, QUIET_STAND, SOMBRE, WAIT, MapBuilder, tex

M = "harbour"


def T(tid, kind, desc, metres=2.0, size=64):
    return tex(M, tid, kind, desc, metres, size)


def build():
    mb = MapBuilder(M, {"color": "#0e1c34", "density": 0.018}, T("sky_harbour", "sky", "a cold blue night strip (256x64): deep navy to a slightly lighter horizon, a few small stars, thin high cloud, a pale smear of moon glow", 1.0, 256))
    wall_hut = T("wall_hut", "surface", "weathered bleached-khaki planked hut wall (vertical planks, nail heads, sun-faded paint peeling, dust streaks)", 1.0)
    wall_quay = T("wall_quay", "surface", "cold dark harbour wall: wet stone blocks with green weed at the base, iron rings, blue night light", 1.0)
    wall_shed = T("wall_shed", "surface", "dark corrugated net-shed wall in night blue, rust, hanging nets", 1.0)
    wall_cell = T("wall_cell", "surface", "damp cell wall of grey stone blocks with scratched tally marks (scratches only), a pale smear of light, drips", 1.0)
    wall_dunes = T("wall_dunes", "surface", "bright sandy dunes with tufts of green marram grass and a white wall of sea haze above, saturated warm", 1.25)
    wall_sea = T("wall_sea", "surface", "a bright turquoise-blue sea horizon with sparkles and tiny white wave crests (lit, saturated)", 4.0)
    floor_boards = T("floor_boards", "surface", "worn pale wooden floorboards with gaps, dust, boot scuffs", 1.0)
    floor_quay = T("floor_quay", "surface", "wet dark quay planks and stone setts, puddles reflecting blue light, a coil of rope here and there", 1.0)
    floor_sand = T("floor_sand", "surface", "warm bright sand with tiny shells, footprints, dry seaweed lines (saturated golden)", 1.25)
    floor_cell = T("floor_cell", "surface", "cold stone cell floor with a drain, straw and a damp patch", 1.0)
    ceil_beams = T("ceil_beams", "ceil", "plank ceiling with dark beams, cobwebs, a stovepipe stain", 1.25)
    ceil_cell = T("ceil_cell", "ceil", "dark vaulted stone cell ceiling with a single iron ring", 1.0)
    mb.sky_by_name["day"] = T("sky_harbour_day", "sky", "the coast's cobalt morning strip (256x64): saturated blue to a pale gold horizon, cloud bands, a low sun, gulls as small marks, a far headland and the sea line, the only saturated sky of the path", 1.0, 256)

    # ---- the briefing hut, again (C11) ------------------------------------------------------------------------------------------------------------------------------
    h2 = mb.room("hut2", (-12, 0, 0, 8), 90, "main", floor_tex=floor_boards, ceil_tex=ceil_beams, fog={"color": "#3a2c1c", "density": 0.016}, wall_tex=wall_hut, ceiling=2.8, light=0.55, tint="#f0d0a0", activities=QUIET_STAND)
    h2.standard_rail("c11", home=(1.8, 0), good=((4.0, -1.2), (6.0, 1.2)), bad=((1.0, 2.8), (2.4, -2.8)), arrive=(0.5, 0))
    h2.wp("c11_x_up", 0.8, -1.6, -30)  # the aircraft (the east door, the loop)
    h2.wp("c11_x_right", 9.2, -2.4, 10)  # the broken radio
    h2.wp("c11_count", 9.0, 0.0)
    h2.thing("count_board", T("thing_count_board", "billboard", "the mission count: a big plank board with an enormous painted number in white digits, the last digit freshly painted and still dripping, an old crossed-out number under it, a paint pot and brush on a ledge", 1.0, 128), 11.6, 0.0, 1.55, 2.8)
    h2.thing("radio_broken", T("thing_radio_broken", "billboard", "a smashed military radio set on a crate: dented grey case, a dangling headset cable, one valve still glowing orange, sparks, 128x128", 1.0, 128), 9.2, -2.9, 0.75, 1.3, "flicker")
    h2.thing("aircraft_door", T("thing_aircraft_door", "billboard", "the hut's open east door framing the invented bomber waiting outside with its engines turning, a white sun glare, dust, 128x128", 1.0, 128), 0.25, -1.6, 1.15, 2.4)
    h2.thing("hut2_stove", "thing_stove", 2.2, 3.3, 0.75, 1.5, "flicker")
    h2.thing("hut2_lamp_a", "thing_lamp_hang", 4.0, 0.0, 2.3, 0.8, "sway")
    h2.thing("hut2_lamp_b", "thing_lamp_hang", 8.0, 0.2, 2.3, 0.8, "sway")
    h2.thing("hut2_window", "thing_window_hut", 6.0, 3.9, 1.7, 1.3)
    h2.light("lt_hut2_a", 4.0, 0.0, 2.2, 5.5, "#ffd890", 1.0)
    h2.light("lt_hut2_b", 8.0, 0.0, 2.2, 5.5, "#ffd890", 0.9)
    h2.light("lt_hut2_door", 0.4, -1.6, 1.5, 6.0, "#fff0c0", 1.1, 0, 55)
    h2.actor("col_h", "officer", "a", 10.2, 0.9, fixed=True, same_as="col", activity="stand", prop="medal")
    h2.actor("chap_h", "officer", "c", 9.6, 2.9, fixed=True, same_as="chap", activity="stand")
    h2.actor("clerk_h", "clerk", "a", 10.2, -1.5, fixed=True, same_as="clerk", activity="paint", prop="brush", target="c11_count")
    for k, (d, u, w, v) in enumerate([(6.4, -2.5, "airman", "a"), (6.4, -0.8, "airman", "b"), (6.4, 0.9, "airman", "a"), (6.4, 2.6, "airman", "c"), (7.8, -1.6, "airman", "b"), (7.8, 0.3, "airman", "a")], 1):
        h2.actor(f"h{k:02d}", w, v, d, u)

    # ---- the harbour at night (C12) ---------------------------------------------------------------------------------------------------------------------------------
    qy = mb.room("quay", (0, 0, 22, 12), -90, "quay", floor_tex=floor_quay, ceil_tex="sky", wall_tex=wall_quay, ceiling=3.6, light=0.55, ambient=0.8, tint="#7f9fe0", activities=CROWD_OUT)
    qy.standard_rail("c12", home=(2.0, 0), good=((5.0, -1.5), (9.0, 1.0)), bad=((1.5, -4.0), (2.6, 3.6)), arrive=(0.6, 0))
    qy.wp("c12_x_up", 14.0, 4.0, -20)  # the searchlights
    qy.wp("c12_x_right", 17.5, -1.0, 10)  # the boat
    qy.thing("boat", T("thing_fishing_boat", "billboard", "a small wooden fishing boat with a stubby mast, a swinging lantern giving a warm gold glow, nets heaped, a tarpaulin, low in black water, lapping ripples (256x128)", 1.0, 256), 19.6, 0.4, 1.45, 4.2, "bob")  # (visual polish 2: bigger and nearer, it was a small dark shape behind the fisherman)
    qy.thing("search_a", T("thing_searchlight", "billboard", "a searchlight on a tripod tower at a quay head: a dark steel tower with a big round lamp throwing a long, wide white-blue beam up and across, additive-looking glow, 128x128", 1.0, 128), 12.0, 4.6, 1.9, 3.8, "sway")
    qy.thing("search_b", "thing_searchlight", 19.0, -4.8, 1.9, 3.8, "sway")
    qy.thing("beam_a", T("thing_beam", "billboard", "a soft wide white-blue searchlight beam as a tall cone (mostly transparent, premultiplied glow), 128x128", 1.0, 128), 12.0, 3.8, 3.4, 6.0, "sway", blend="add")
    qy.thing("beam_b", "thing_beam", 19.0, -3.8, 3.4, 6.0, "sway", blend="add")
    qy.thing("bollard", T("thing_bollard", "billboard", "an iron mooring bollard with a coil of rope", 1.0, 128), 16.0, 2.6, 0.45, 0.9)
    qy.thing("nets_heap", T("thing_nets", "billboard", "a heap of drying fishing nets with cork floats on a rack", 1.0, 128), 7.0, -4.8, 0.9, 1.8)
    qy.thing("quay_crates", "thing_crate_stack", 9.5, 4.8, 1.0, 1.8)
    qy.thing("quay_lamp", T("thing_quay_lamp", "billboard", "a dim blue-glass quayside lamp on a post", 1.0, 128), 4.0, 4.9, 1.5, 3.0, "flicker")
    qy.light("lt_boat", 19.0, 0.0, 1.6, 9.0, "#ffc060", 2.2)  # (visual polish 2: the boat was a dark hulk: a stronger lantern)
    qy.light("lt_search_a", 12.0, 4.6, 3.4, 12.0, "#b8d8ff", 1.1)
    qy.light("lt_moon", 8.0, 0.0, 5.0, 14.0, "#6f8fd0", 0.8)
    qy.actor("fish", "fisherman", "a", 16.0, -1.9, fixed=True, activity="stand")  # (polish 2: beside the boat, not in front of it)
    qy.actor("sent", "mp", "a", 11.0, 3.2, fixed=True, activity="stand")
    qy.actor("dock1", "fisherman", "b", 6.0, -3.4)
    qy.actor("dock2", "fisherman", "c", 8.5, 3.0)
    qy.actor("dock3", "civilian_city", "b", 4.0, 3.0)

    # ---- the neutral coast (C13) ------------------------------------------------------------------------------------------------------------------------------------
    co = mb.room("coast", (22, 0, 44, 14), -90, "coast", floor_tex=floor_sand, ceil_tex="sky", sky="day", fog={"color": "#7c96ae", "density": 0.006}, wall_tex=wall_dunes, ceiling=2.6, light=0.5, tint="#f4ecd8", activities=QUIET_STAND)
    co.standard_rail("c13", home=(2.2, 0), good=((5.0, -1.5), (9.0, 1.0)), bad=((1.5, 3.5), (2.8, -3.5)), arrive=(0.7, 0))
    co.wp("c13_x_up", 17.0, 0.0, 0)  # the shore
    co.thing("shore_boat", T("thing_shore_boat", "billboard", "the small fishing boat pulled up on the sand in bright sun, blue and white paint, nets drying, 256x128", 1.0, 256), 12.0, -3.2, 0.9, 2.2)
    co.thing("birds", T("thing_birds", "billboard", "a loose flock of white gulls in flight against the sky, transparent background, 128x128", 1.0, 128), 14.0, 1.0, 3.2, 1.8, "bob")
    co.thing("birds_b", "thing_birds", 20.0, -3.0, 3.4, 1.6, "bob")
    co.thing("pine", T("thing_pine_umbrella", "billboard", "a tall umbrella pine, saturated green crown, warm brown trunk, bright", 1.0, 128), 10.0, 5.6, 2.1, 4.2)
    co.thing("pine_b", "thing_pine_umbrella", 18.0, 5.8, 2.0, 4.0)
    co.thing("nets_dry", "thing_nets", 9.0, -5.6, 0.9, 1.8)
    co.thing("shore_post", T("thing_wooden_post", "billboard", "a weathered wooden jetty post with a coil of rope and a bright blue-painted top", 1.0, 128), 19.5, 2.4, 0.9, 1.8)
    co.thing("sun_umbrella", T("thing_sunshade", "billboard", "a faded orange-and-white beach sunshade over a little table with a jug and cups", 1.0, 128), 7.0, 4.2, 1.0, 2.0)
    co.light("lt_coast_sun", 10.0, 0.0, 8.0, 30.0, "#fff2c0", 1.0)
    co.actor("fish_c", "fisherman", "a", 14.5, 1.2, fixed=True, same_as="fish", activity="stand")
    co.actor("quay_w", "civilian_city", "b", 18.5, -1.6, fixed=True, activity="stand")
    co.actor("kid_q", "civilian_city", "c", 17.0, 2.6, activity="stand")
    co.actor("dock_c", "fisherman", "c", 9.0, 1.0)

    # ---- the cell (C14) ---------------------------------------------------------------------------------------------------------------------------------------------
    ce = mb.room("cell", (0, -8, 10, 0), 0, "cell", floor_tex=floor_cell, ceil_tex=ceil_cell, wall_tex=wall_cell, ceiling=2.8, light=0.6, ambient=0.9, tint="#a8c0d8", activities=SOMBRE)
    ce.standard_rail("c14", home=(1.4, 0), good=((3.0, -1.0), (4.6, 1.0)), bad=((1.0, 2.8), (2.2, -2.8)), arrive=(0.6, 0))
    ce.wp("c14_x_up", 5.5, 3.6, 60)  # the cell door (the guard stands there)
    ce.wp("c14_x_right", 6.4, -2.6, -40)  # the stamped order on the table
    ce.wp("c14_latch", 6.2, 0.0)
    ce.thing("latch", T("thing_window_latch", "billboard", "a small barred cell window high in a stone wall with a rusty iron latch on its frame and a thin shaft of cold moonlight, 128x128", 1.0, 128), 7.6, 0.0, 1.8, 1.7)
    ce.thing("order_paper", T("thing_order_paper", "billboard", "a table with a single sheet of paper bearing a huge red stamp bar and a ruled body of wavy lines (no readable text), an ink pad and a lamp, 128x128", 1.0, 128), 6.2, -2.8, 0.7, 1.3)
    ce.thing("bunk", T("thing_bunk", "billboard", "a plank bunk bed against a wall with a grey blanket, a tin cup, scratched wall behind, 128x128", 1.0, 128), 4.0, 3.6, 0.6, 1.5)
    ce.thing("cell_door", T("thing_cell_door", "billboard", "a heavy iron-banded cell door with a small grille and a big lock, a guard's lantern glow in the grille, 128x128", 1.0, 128), 0.25, 0.0, 1.2, 2.4)
    ce.thing("cell_lantern", "thing_lamp_hang", 2.8, 0.0, 2.2, 0.7, "sway")
    ce.light("lt_cell_moon", 7.6, 0.0, 2.0, 5.0, "#a8c0ff", 1.2)
    ce.light("lt_cell_lantern", 2.8, 0.0, 2.0, 5.0, "#ffb060", 1.0)
    ce.actor("guard", "mp", "b", 2.0, 3.2, activity="stand")
    ce.actor("clerk_k", "clerk", "a", 6.2, -1.6, fixed=True, same_as="clerk", activity="stand", prop="stamp")
    ce.actor("mate", "airman", "a", 4.6, 3.1, activity="sit")

    mb.portal("hut2", "quay", (0, 3), (0, 6))
    mb.portal("quay", "coast", (22, 10.8), (22, 11.7))  # (visual polish 2: was (22, 5)-(22, 7), a 2 m gap behind the boat through which the lit day coast showed as a block of bright dither; now a crack of daylight in the far corner, still a portal because a sector must be reachable)
    # The root cause of the bright block: the coast's own west wall (wall_dunes, 4.5 m high) lies in the same plane as the quay's east wall and is drawn over it (the walls are not
    # back-face culled), so the whole end of the quay showed the coast's dunes. The coast's west wall is the harbour wall's other face: the same stone.
    mb.walls.append({"from": [22, 14], "to": [22, 11.7], "sector": "coast", "portal": None, "tex": "wall_quay"})
    mb.walls.append({"from": [22, 10.8], "to": [22, 0], "sector": "coast", "portal": None, "tex": "wall_quay"})
    mb.portal("cell", "quay", (3, 0), (7, 0))
    mb.rooms = {"main": {"palette": "khaki"}, "quay": {"palette": "searchlight"}, "coast": {"palette": "bright"}, "cell": {"palette": "cold"}}
    return mb
