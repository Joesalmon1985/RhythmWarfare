"""The airfield map (worlds `base` and `air`: C01 to C06): the briefing hut, the flight line, the hospital tent, the bomber's nose at night, the Quartermaster's store and the Surgeon's office.

Plan (x to the east, z to the south, metres):

    office(-12..0, -10..0) | tent(0..10, -10..0)
    hut   (-12..0,   0..8) | line(0..26, 0..14) | store(26..40, 0..12)
                                  bomber(10..14, 14..22) hangs off the line's south edge
"""
from __future__ import annotations

from squadron_lib import BUSY, QUIET_STAND, SOMBRE, WAIT, WARD, MapBuilder, tex

M = "airfield"


def T(tid, kind, desc, metres=2.0, size=64):
    return tex(M, tid, kind, desc, metres, size)


def build():
    mb = MapBuilder(M, {"color": "#d8c79c", "density": 0.012}, T("sky_day", "sky", "bleached white-blue Mediterranean daylight strip (256x64), a pale haze at the horizon, a few thin streaks of cloud, grainy over-exposed", 1.0, 256))
    # ---- surfaces ---------------------------------------------------------------------------------------------------------------------------------------------------
    wall_hut = T("wall_hut", "surface", "weathered bleached-khaki planked hut wall (vertical planks, nail heads, sun-faded paint peeling, dust streaks)", 2.0)
    wall_tent = T("wall_tent", "surface", "dirty cream canvas tent wall with seams, rope loops, a faint red-brown stain; soft folds", 2.0)
    wall_office = T("wall_office", "surface", "yellowed plaster upper wall over a dark green painted dado, a thin dark rail between, peeling patches", 2.5)
    wall_hangar = T("wall_hangar", "surface", "corrugated iron, rust streaks, olive-drab paint worn to orange metal, bolts", 2.5)
    wall_berm = T("wall_berm", "surface", "stacked sandbags and packed orange earth, bleached by the sun, tufts of dry grass", 2.5)
    wall_bomber = T("wall_bomber", "surface", "riveted aircraft interior panels, dark green-black, a lighter ribbed strip, instrument-lamp scuffs", 1.5)
    floor_boards = T("floor_boards", "surface", "worn pale wooden floorboards with gaps, dust, boot scuffs", 2.0)
    floor_dust = T("floor_dust", "surface", "packed orange dust and gravel airfield ground, tyre tracks, tufts of dry grass", 3.0)
    floor_lino = T("floor_lino", "surface", "cracked cream-and-green linoleum, dirty", 2.0)
    floor_metal = T("floor_metal", "surface", "dark aircraft floor grating with a diamond tread plate strip, oil stains", 1.5)
    floor_concrete = T("floor_concrete", "surface", "stained concrete hangar floor, expansion joints, oil and dust, scattered straw", 2.5)
    ceil_beams = T("ceil_beams", "ceil", "plank ceiling with dark beams, cobwebs, a stovepipe stain", 2.0)
    ceil_canvas = T("ceil_canvas", "ceil", "canvas tent roof lit from above, ridge seam, rope", 2.0)
    ceil_hangar = T("ceil_hangar", "ceil", "dim corrugated iron roof with trusses and rust", 2.5)
    ceil_fuselage = T("ceil_fuselage", "ceil", "curved aircraft ceiling ribs, wiring loom, dark green-black", 1.5)
    ceil_plaster = T("ceil_plaster", "ceil", "yellowed plaster ceiling with a water stain and a bulb rose", 2.5)

    # ---- the briefing hut (C01) -------------------------------------------------------------------------------------------------------------------------------------
    hut = mb.room("hut", (-12, 0, 0, 8), 90, "main", floor_tex="floor_boards", ceil_tex="ceil_beams", wall_tex=wall_hut, ceiling=2.8, light=0.55, tint="#f0dcae", activities=QUIET_STAND)
    hut.standard_rail("c01", home=(1.8, 0), good=((4.0, -1.2), (6.0, 1.2)), bad=((1.0, 2.8), (2.4, -2.8)), arrive=(0.5, 0))
    hut.wp("c01_x_up", 6.0, 3.0, 40)  # the empty cot at the north doorway
    hut.wp("c01_x_right", 0.7, -1.6, -30)  # the east door onto the line
    hut.wp("c01_board", 9.0, 0.0)
    hut.thing("board", T("thing_board", "billboard", "the mission board: a cork-and-plank board with a hand-drawn island map, red pins, strings, and a big painted number on a small slate (a tally of missions, painted digits only), seen face on, 128x128", 1.0, 128), 11.6, 0.0, 1.55, 2.6)
    hut.thing("cot_empty", T("thing_cot_empty", "billboard", "an empty army cot: grey blanket folded square, pillow, kit bag at its foot, a pair of boots beside it, 128x128 side-on three-quarter", 1.0, 128), 6.0, 3.4, 0.5, 1.3)
    hut.thing("hut_cot_b", "thing_cot_empty", 9.4, 3.4, 0.5, 1.3)
    hut.thing("hut_stove", T("thing_stove", "billboard", "a squat iron stove with a stovepipe going up, a kettle on top, a glow in the door", 1.0, 128), 2.2, -3.3, 0.75, 1.5, "flicker")
    hut.thing("hut_table", T("thing_table_maps", "billboard", "a trestle table covered with maps, a lamp and tin mugs", 1.0, 128), 8.2, -2.6, 0.55, 1.4)
    hut.thing("hut_lamp_a", T("thing_lamp_hang", "billboard", "a hanging bare bulb on a flex with a tin shade, warm glow, 128x128 (hangs from the top)", 1.0, 128), 4.0, 0.0, 2.3, 0.8, "sway")
    hut.thing("hut_lamp_b", "thing_lamp_hang", 8.0, 0.2, 2.3, 0.8, "sway")
    hut.thing("hut_window", T("thing_window_hut", "billboard", "a small square hut window with a bright white-hot sky behind it, taped glass, a half-drawn curtain", 1.0, 128), 5.0, -3.9, 1.7, 1.3)
    hut.thing("hut_window_b", "thing_window_hut", 10.0, -3.9, 1.7, 1.3)
    hut.thing("hut_door", T("thing_door_open_light", "billboard", "an open wooden door with blinding white daylight beyond, door leaf swung inward", 1.0, 128), 0.25, -1.6, 1.15, 2.3)
    hut.light("lt_hut_a", 4.0, 0.0, 2.2, 5.5, "#ffd890", 1.0)
    hut.light("lt_hut_b", 8.0, 0.0, 2.2, 5.5, "#ffd890", 0.9)
    hut.light("lt_hut_door", 0.4, -1.6, 1.5, 6.0, "#fff0c0", 1.1, 0, 55)
    # people: the Colonel at the board, his aide, six airmen in two rows
    hut.actor("col", "officer", "a", 10.3, 0.9, fixed=True, activity="stand", target="c01_board", prop="medal")
    hut.actor("aide", "officer", "b", 10.0, -1.2, fixed=True, activity="check", prop="clipboard", target="c01_board")
    for k, (d, u, w, v) in enumerate([(6.6, -2.6, "airman", "a"), (6.6, -0.9, "airman", "b"), (6.6, 0.8, "airman", "a"), (6.6, 2.5, "airman", "c"), (8.0, -1.7, "airman", "a"), (8.0, 0.2, "airman", "b")], 1):
        hut.actor(f"a{k:02d}", w, v, d, u)

    # ---- the flight line (C02) --------------------------------------------------------------------------------------------------------------------------------------
    line = mb.room("line", (0, 0, 26, 14), -90, "line", floor_tex="floor_dust", ceil_tex="sky", wall_tex=wall_berm, ceiling=5.0, light=0.72, tint="#f2ead8", activities=BUSY)
    line.standard_rail("c02", home=(2.2, 0), good=((5.0, -1.5), (8.5, 0.8)), bad=((1.5, -4.5), (2.5, 4.0)), arrive=(0.8, 0))
    line.wp("c02_x_up", 10.0, 5.0, 60)  # the ladder (to the bomber)
    line.wp("c02_x_right", 20.0, -3.0, -10)  # the crates
    line.wp("c02_ladder", 10.6, 5.6)
    line.thing("bomber_nose", T("thing_bomber_nose", "billboard", "an invented twin-engine bomber parked nose-on at three-quarter view: glazed nose, two radial engines with olive drab cowls, a faded paint patch, no roundels or markings, orange dust on the tyres (a wide sprite, 256x128)", 1.0, 256), 13.0, 4.4, 2.1, 4.2)
    line.thing("ladder", T("thing_ladder", "billboard", "a short wooden boarding ladder leaning against a dark hatch, 128x128", 1.0, 128), 11.0, 6.0, 1.3, 2.5)
    line.thing("crates", T("thing_crate_stack", "billboard", "a stack of wooden supply crates, stencilled with blank painted squares (no letters), rope, a tarp half over them, an egg basket on top", 1.0, 128), 20.5, -3.2, 1.0, 2.1)
    line.thing("crates_b", "thing_crate_stack", 22.5, 4.6, 1.0, 2.0)
    line.thing("fuel_drums", T("thing_fuel_drums", "billboard", "three olive fuel drums with a hand pump, orange dust", 1.0, 128), 7.0, 4.6, 0.7, 1.4)
    line.thing("windsock", T("thing_windsock", "billboard", "a limp windsock on a tall pole, orange and white bands, 128x128", 1.0, 128), 17.0, -5.6, 2.5, 4.8, "sway")
    line.thing("tent_flap", T("thing_tent_flap", "billboard", "a tent doorway: canvas flaps tied back, a dark interior, a white cross painted on a sheet hanging beside (no flags, a plain red-free cross shape in grey)", 1.0, 128), 5.0, -6.5, 1.25, 2.5)
    line.thing("hangar_front", T("thing_hangar_front", "billboard", "the front of a corrugated store hangar with a big sliding door ajar on dark, crates visible inside, 128x128", 1.0, 128), 25.5, -1.0, 2.0, 4.2)
    line.thing("sandbags", T("thing_sandbags", "billboard", "a low wall of sandbags with a lazy stack of ammunition boxes", 1.0, 128), 14.5, -6.2, 0.55, 1.2)
    line.thing("jeep", T("thing_jeep", "billboard", "an open dusty utility jeep, olive, no markings, a spare wheel on the back", 1.0, 128), 4.5, 5.5, 0.8, 1.8)
    line.light("lt_line_sun", 12.0, 0.0, 4.0, 24.0, "#fff4d0", 1.3)
    line.actor("gun", "gunner", "a", 11.5, 5.0, fixed=True, activity="stand")
    line.actor("qm", "quartermaster", "a", 19.2, -2.4, fixed=True, activity="stand", prop="egg")
    line.actor("mech", "airman", "b", 8.4, 3.6)
    line.actor("l01", "airman", "a", 5.5, 2.0)
    line.actor("l02", "airman", "c", 15.5, 0.8)
    line.actor("l03", "airman", "b", 18.0, 3.5)
    line.actor("l04", "airman", "a", 13.0, -3.8)

    # ---- the hospital tent (C03) ------------------------------------------------------------------------------------------------------------------------------------
    tent = mb.room("tent", (0, -10, 10, 0), 0, "tent", floor_tex="floor_lino", ceil_tex="ceil_canvas", wall_tex=wall_tent, ceiling=3.0, light=0.6, tint="#fff2d8", activities=WARD)
    tent.standard_rail("c03", home=(1.8, 0), good=((3.6, -1.0), (5.2, 1.0)), bad=((1.0, 2.8), (2.4, -2.8)), arrive=(0.7, 0))
    tent.wp("c03_x_up", 6.4, 3.6, 70)  # the kitchen hatch (east wall)
    tent.wp("c03_x_right", 5.4, -4.2, -90)  # the west door to the Surgeon's office
    for k, d in enumerate([2.6, 4.4, 6.2, 8.0]):
        tent.thing(f"cot_l{k}", T("thing_cot_ward", "billboard", "an iron hospital cot with a white sheet and grey blanket, a bedside crate with a tin mug, seen from the side, 128x128", 1.0, 128), d, -3.7, 0.5, 1.3)
        tent.thing(f"cot_r{k}", "thing_cot_ward", d + 0.6, 3.7, 0.5, 1.3)
    tent.thing("kitchen_hatch", T("thing_kitchen_hatch", "billboard", "a serving hatch cut in a wall with a shutter propped open, steam, a ladle and a bucket, a glimpse of a kitchen lamp", 1.0, 128), 6.4, 4.8, 1.3, 1.8, "flicker")
    tent.thing("tent_drip", T("thing_drip_stand", "billboard", "an iron drip stand with a bottle and tube", 1.0, 128), 5.0, -1.8, 1.0, 1.8)
    tent.thing("tent_lamp", "thing_lamp_hang", 5.0, 0.0, 2.5, 0.9, "sway")
    tent.thing("tent_curtain", T("thing_screen_cloth", "billboard", "a folding hospital screen of grey cloth on a wooden frame", 1.0, 128), 3.0, 1.2, 0.9, 1.7)
    tent.light("lt_tent", 5.0, 0.0, 2.6, 7.0, "#fff0d0", 1.1)
    tent.light("lt_tent_door", 0.6, 0.0, 1.5, 6.0, "#fff6d8", 1.0, 0, 60)
    tent.actor("surg", "surgeon", "a", 7.6, 0.6, fixed=True, activity="check", prop="clipboard", target="c03_g2")
    tent.actor("p01", "patient", "c", 4.6, 3.2, activity="sit")  # the soldier in plaster
    tent.actor("p02", "patient", "a", 2.6, -3.7, activity="lie")
    tent.actor("p03", "patient", "b", 4.4, -3.7, activity="lie")
    tent.actor("p04", "patient", "a", 6.2, -3.7, activity="lie")
    tent.actor("p05", "patient", "b", 8.2, 3.2, activity="sit")
    tent.actor("orderly", "airman", "b", 3.0, 0.0, activity="stand")

    # ---- the Surgeon's office (C06) ---------------------------------------------------------------------------------------------------------------------------------
    office = mb.room("office", (-12, -10, 0, 0), 90, "office", floor_tex="floor_boards", ceil_tex="ceil_plaster", wall_tex=wall_office, ceiling=2.9, light=0.55, tint="#f4e6b8", activities=WAIT)
    office.standard_rail("c06", home=(1.8, 0), good=((4.0, -1.2), (6.0, 1.2)), bad=((1.2, 2.8), (2.6, -2.8)), arrive=(0.6, 0))
    office.wp("c06_x_up", 10.5, -1.6, 0)  # door A (the obvious door)
    office.wp("c06_x_right", 10.5, 1.8, 0)  # door B
    office.wp("c06_desk", 8.0, 0.0)
    office.thing("desk_clerk", T("thing_desk_office", "billboard", "a big battered wooden office desk seen from the front: blotter, an inkwell, tidy piles of forms, an in-tray and an out-tray, 128x128", 1.0, 128), 8.4, 0.0, 0.7, 1.9)
    office.thing("stamp_big", T("thing_stamp_big", "billboard", "a huge rubber stamp on a stand beside an ink pad, the stamp's face a plain red bar (no letters), larger than life, 128x128", 1.0, 128), 8.0, -0.9, 1.1, 1.0)
    office.thing("certificate", T("thing_certificate", "billboard", "a framed certificate on a wall: ornate border, a blank cream centre with ruled lines and a red ribbon seal (no readable text), 128x128", 1.0, 128), 5.5, 4.8, 1.6, 1.4)
    office.thing("door_a", T("thing_door_office", "billboard", "a heavy panelled office door, dark green paint, a brass handle, a frosted glass panel (blank), 128x128", 1.0, 128), 11.7, -1.8, 1.1, 2.2)
    office.thing("door_b", "thing_door_office", 11.7, 1.9, 1.1, 2.2)
    office.thing("files", T("thing_filing_cabinet", "billboard", "two grey steel filing cabinets, drawers one open with paper spilling out", 1.0, 128), 6.0, -4.3, 0.9, 1.8)
    office.thing("office_lamp", T("thing_desk_lamp", "billboard", "a green-shaded desk lamp with a warm cone of light", 1.0, 128), 8.2, 0.9, 1.0, 0.7)
    office.thing("office_window", T("thing_window_office", "billboard", "a tall office window with a venetian blind half-drawn, white sun slats across it", 1.0, 128), 2.0, -4.8, 1.7, 1.6)
    office.light("lt_office", 7.0, 0.0, 2.4, 6.0, "#ffe3a0", 1.0)
    office.light("lt_office_lamp", 8.2, 0.9, 1.2, 3.0, "#ffd070", 1.2)
    office.actor("clerk", "clerk", "a", 9.2, 0.0, fixed=True, activity="stand", prop="stamp")
    office.actor("surg_o", "surgeon", "a", 6.8, -1.4, fixed=True, same_as="surg", activity="stand")
    office.actor("q01", "airman", "a", 3.2, 2.6, activity="queue")
    office.actor("q02", "airman", "b", 4.2, 2.6, activity="queue")

    # ---- the bomber's nose at night (C04) ---------------------------------------------------------------------------------------------------------------------------
    bomber = mb.room("bomber", (10, 14, 14, 22), 180, "bomber", floor_tex="floor_metal", ceil_tex="ceil_fuselage", wall_tex=wall_bomber, ceiling=2.2, light=0.6, ambient=0.9, tint="#a8d0a0", activities=SOMBRE)
    bomber.standard_rail("c04", home=(1.2, 0), good=((2.8, -0.6), (4.4, 0.7)), bad=((1.0, 1.3), (2.0, -1.3)), arrive=(0.5, 0))
    bomber.wp("c04_x_up", 5.4, 0.9, 0)  # the release lever
    bomber.wp("c04_x_right", 3.0, 1.4, 60)  # the emergency controls (right wall)
    bomber.thing("nose_glass", T("thing_nose_glass", "billboard", "the glazed bomber nose from inside: a curved frame of dark struts around black night glass with distant flak flashes and tiny orange tracer lines, an instrument-lit rim, 128x128", 1.0, 128), 7.7, 0.0, 1.2, 3.0)
    bomber.thing("flak_a", T("thing_flak_burst", "billboard", "a soft orange-white flak burst with black smoke puff and a spray of tiny sparks, additive-looking (premultiplied glow, mostly transparent), 128x128", 1.0, 128), 7.4, -0.7, 1.5, 1.6, "flicker", blend="add")
    bomber.thing("flak_b", "thing_flak_burst", 7.4, 0.8, 1.0, 1.2, "flicker", blend="add")
    bomber.thing("release_lever", T("thing_release_lever", "billboard", "a bomb release lever: a red-knobbed iron lever on a dark box with a dial and a toggle, lit by a small green lamp, 128x128", 1.0, 128), 5.6, 0.2, 0.9, 1.1)
    bomber.thing("emergency_box", T("thing_emergency_box", "billboard", "a red steel emergency control box on the wall with a pull handle behind a wire guard and a warning triangle (no letters), 128x128", 1.0, 128), 3.0, 1.75, 1.2, 0.9, "pulse")
    bomber.thing("bomber_panel", T("thing_instrument_panel", "billboard", "an aircraft instrument panel: round dials with green-lit needles, switches, a compass, 128x128", 1.0, 128), 6.6, -1.55, 1.1, 1.3)
    bomber.thing("bomber_lamp", T("thing_lamp_red", "billboard", "a small caged ceiling lamp glowing dim green", 1.0, 128), 3.8, 0.0, 2.0, 0.5, "pulse")
    bomber.light("lt_bomber_panel", 6.0, -1.0, 1.2, 4.5, "#8cf0a0", 1.0)
    bomber.light("lt_bomber_flak", 7.2, 0.0, 1.4, 6.0, "#ffa060", 1.0)
    bomber.actor("pilot", "airman", "c", 3.8, -0.8, activity="sit")
    bomber.actor("gun_b", "gunner", "a", 2.6, 1.2, fixed=True, same_as="gun", activity="stand")
    bomber.actor("crew1", "airman", "b", 4.9, 0.9, activity="stand")
    bomber.actor("crew2", "airman", "a", 5.9, -0.9, activity="stand")

    # ---- the Quartermaster's store (C05) ----------------------------------------------------------------------------------------------------------------------------
    store = mb.room("store", (26, 0, 38, 12), -90, "store", floor_tex="floor_concrete", ceil_tex="ceil_hangar", wall_tex=wall_hangar, ceiling=4.0, light=0.7, ambient=0.85, tint="#f0e0b8", activities=BUSY)
    store.standard_rail("c05", home=(1.8, 0), good=((4.0, -1.4), (7.0, 1.2)), bad=((1.2, 3.0), (2.6, -3.2)), arrive=(0.8, 0))
    store.wp("c05_x_up", 8.0, 4.2, 40)  # the truck
    store.wp("c05_x_right", 9.0, -3.5, -20)  # the ledger
    store.thing("ledger", T("thing_ledger", "billboard", "an enormous open ledger on a lectern, ruled columns of tiny neat figures (drawn as lines, no letters), a pen and an inkwell, a green-shaded lamp, 128x128", 1.0, 128), 9.0, -2.8, 0.95, 1.6)
    store.thing("truck", T("thing_truck", "billboard", "an olive canvas-backed truck seen from three-quarters front, engine running, loaded with crates under a tarp, no markings, a driver's elbow out of the cab, exhaust puff, 256x128", 1.0, 256), 10.0, 3.8, 1.4, 2.8, "bob")
    store.thing("store_crates_a", "thing_crate_stack", 6.0, -4.8, 1.0, 2.2)
    store.thing("store_crates_b", "thing_crate_stack", 10.6, -4.8, 1.0, 2.4)
    store.thing("store_shelves", T("thing_shelves_tins", "billboard", "tall metal shelving packed with tins, jars, boots and blankets, price tags drawn as small coloured squares", 1.0, 128), 11.2, 1.0, 1.4, 2.8)
    store.thing("store_scales", T("thing_scales", "billboard", "a brass shop balance scale on a counter with a bag of flour and weights", 1.0, 128), 6.4, 2.2, 0.9, 1.0)
    store.thing("store_lamp", "thing_lamp_hang", 7.0, 0.0, 3.2, 1.0, "sway")
    store.thing("store_sign", T("thing_sign_ledgerless", "billboard", "a hand-painted board over the store door with a drawing of a crate and a coin and a small crown-less star (pictures only, no letters)", 1.0, 128), 11.7, 0.0, 3.0, 1.2)
    store.light("lt_store", 7.0, 0.0, 3.0, 8.0, "#ffe0a0", 1.1)
    store.light("lt_store_door", 0.5, 0.0, 2.0, 7.0, "#fff0c8", 1.0, 0, 55)
    store.actor("qm_s", "quartermaster", "a", 8.0, -0.4, fixed=True, same_as="qm", activity="stand", prop="egg")
    store.actor("sc1", "clerk", "b", 7.6, -2.6)
    store.actor("sc2", "clerk", "c", 8.4, 1.9)
    store.actor("po1", "airman", "b", 4.0, -1.8, activity="carry")
    store.actor("po2", "airman", "a", 5.4, 2.0, activity="carry")
    store.actor("drv", "airman", "a", 9.4, 4.3, activity="stand")

    # ---- the plan: doorways between the rooms -----------------------------------------------------------------------------------------------------------------------
    mb.portal("hut", "line", (0, 3), (0, 6))
    mb.portal("hut", "office", (-8, 0), (-4, 0))
    mb.portal("office", "tent", (0, -7), (0, -4))
    mb.portal("tent", "line", (3, 0), (7, 0))
    mb.portal("line", "store", (26, 4), (26, 8))
    mb.portal("line", "bomber", (11, 14), (13, 14))
    mb.rooms = {"main": {"palette": "khaki"}, "line": {"palette": "glare"}, "tent": {"palette": "khaki"}, "office": {"palette": "khaki"}, "bomber": {"palette": "instrument"}, "store": {"palette": "khaki"}}
    return mb
