"""The city map (world `city`: C07 to C10): the bomber again under red light, the old city street with its staff car, the Colonel's office and the ruined city at night with a train beyond.

Plan (x east, z south, metres):

                bomber_r(10..14, -8..0)
    street(0..24, 0..8)  ruins(24..46, 0..10)
        office(2..12, 8..16)
"""
from __future__ import annotations

from squadron_lib import BUSY, CROWD_OUT, SOMBRE, STREET, WAIT, MapBuilder, tex

M = "city"


def T(tid, kind, desc, metres=2.0, size=64):
    return tex(M, tid, kind, desc, metres, size)


def build():
    mb = MapBuilder(M, {"color": "#7a6046", "density": 0.016}, T("sky_dusk", "sky", "a sepia dusk strip (256x64): amber glow low at the horizon fading to a brown-grey sky, thin smoke columns, no stars", 1.0, 256))
    wall_stone = T("wall_stone", "surface", "sepia limestone blocks of an old city wall, chipped corners, shrapnel pocks, soot stains", 3.0)
    wall_stucco = T("wall_stucco", "surface", "cracked ochre-and-grey stucco with bare brick showing through, faded shutters painted on, stains", 2.5)
    wall_ruin = T("wall_ruin", "surface", "blown-out brick wall, blackened by fire, rubble at its foot, bare lath, deep shadow", 2.5)
    wall_panel = T("wall_panel", "surface", "dark oak wall panelling with a gold-trimmed picture rail, polished, a sepia sheen", 2.5)
    wall_bomber = T("wall_bomber", "surface", "riveted aircraft interior panels, dark green-black, a lighter ribbed strip, instrument-lamp scuffs", 1.5)
    floor_cobble = T("floor_cobble", "surface", "sepia cobblestones, wheel ruts, puddles, scattered straw and paper", 2.5)
    floor_rubble = T("floor_rubble", "surface", "broken paving and rubble, brick dust, charred planks, glass glints", 3.0)
    floor_carpet = T("floor_carpet", "surface", "a worn burgundy-brown office carpet with a pale border pattern", 2.5)
    floor_metal = T("floor_metal", "surface", "dark aircraft floor grating with a diamond tread plate strip, oil stains", 1.5)
    ceil_plaster = T("ceil_plaster", "ceil", "yellowed plaster ceiling with a water stain and a bulb rose", 2.5)
    ceil_fuselage = T("ceil_fuselage", "ceil", "curved aircraft ceiling ribs, wiring loom, dark green-black", 1.5)
    ceil_night_red = T("ceil_night_red", "ceil", "a painted night sky ceiling (256 wide look): smoke clouds lit red-orange from below by fires, a few stars", 4.0)
    ceil_arcade = T("ceil_arcade", "ceil", "dusk sky strip seen between sagging washing lines and wires: sepia-amber, smoke wisps", 4.0)

    # ---- the bomber again, red light (C07) --------------------------------------------------------------------------------------------------------------------------
    br = mb.room("bomber_r", (10, -8, 14, 0), 0, "main", floor_tex=floor_metal, ceil_tex=ceil_fuselage, wall_tex=wall_bomber, ceiling=2.2, light=0.6, ambient=0.9, tint="#ff8068", activities=SOMBRE)
    br.standard_rail("c07", home=(1.2, 0), good=((2.8, -0.6), (4.4, 0.7)), bad=((1.0, 1.3), (2.0, -1.3)), arrive=(0.5, 0))
    br.wp("c07_x_up", 5.3, 0.9, 20)  # the jacket
    br.wp("c07_x_right", 3.0, 1.4, 60)  # the medical kit
    br.thing("jacket", T("thing_jacket_blood", "billboard", "a leather flight jacket thrown over a seat, dark stains on it (stylised, not gory), a scarf trailing, 128x128", 1.0, 128), 5.4, 1.2, 0.8, 1.2)
    br.thing("medkit", T("thing_medkit", "billboard", "a white first-aid case with a plain grey cross (no colour flag), open on the floor with bandages out, 128x128", 1.0, 128), 3.0, 1.5, 0.35, 0.8)
    br.thing("nose_glass_r", "thing_nose_glass", 7.7, 0.0, 1.2, 3.0)
    br.thing("flak_r", "thing_flak_burst", 7.3, -0.6, 1.4, 1.5, "flicker", blend="add")
    br.thing("alarm_lamp", T("thing_lamp_alarm", "billboard", "a caged ceiling lamp glowing deep red with a halo, 128x128", 1.0, 128), 3.8, 0.0, 2.0, 0.6, "pulse")
    br.thing("bomber_panel_r", "thing_instrument_panel", 6.6, -1.55, 1.1, 1.3)
    br.light("lt_red_a", 3.0, 0.0, 1.8, 6.0, "#ff3a28", 1.4)
    br.light("lt_red_b", 6.0, 0.0, 1.5, 5.0, "#ff6040", 1.0)
    br.actor("gun_c", "gunner", "a", 3.4, 0.0, fixed=True, same_as="gun", activity="lie")
    br.actor("pilot_c", "airman", "c", 6.2, -0.9, fixed=True, same_as="pilot", activity="stand")
    br.actor("crew1c", "airman", "b", 3.0, 1.2, fixed=True, same_as="crew1", activity="sit")
    br.actor("crew2c", "airman", "a", 4.8, 1.2, fixed=True, same_as="crew2", activity="rock")

    # ---- the old city street (C08) ----------------------------------------------------------------------------------------------------------------------------------
    st = mb.room("street", (0, 0, 24, 8), -90, "street", floor_tex=floor_cobble, ceil_tex=ceil_arcade, wall_tex=wall_stucco, ceiling=6.0, light=0.55, tint="#ffd898", activities=STREET)
    st.standard_rail("c08", home=(2.0, 0), good=((5.0, -1.2), (8.5, 0.8)), bad=((1.2, -2.8), (2.4, 2.6)), arrive=(0.8, 0))
    st.wp("c08_x_up", 19.5, 0.0, 0)  # the damaged arch
    st.wp("c08_x_right", 9.5, -2.0, -30)  # the staff car
    st.thing("arch", T("thing_arch_broken", "billboard", "a big stone archway half collapsed: a gap in the top, fallen keystone, sunset-orange sky and a smoky street beyond, 128x128", 1.0, 128), 22.4, 0.0, 2.2, 4.4)
    st.thing("staff_car", T("thing_staff_car", "billboard", "a boxy 1940s staff car, olive green, a pennant-less bonnet, chrome headlamps, dust and a dented wing, three-quarter front view (256x128)", 1.0, 256), 10.5, -2.2, 0.9, 1.9)
    st.thing("cafe_table", T("thing_cafe_table", "billboard", "a little round cafe table with two bentwood chairs, a bottle and glasses", 1.0, 128), 6.0, 2.8, 0.55, 1.2)
    st.thing("street_lamp", T("thing_street_lamp", "billboard", "a tall iron street lamp, glass cracked, a faint warm glow", 1.0, 128), 8.0, 3.4, 1.5, 3.2)
    st.thing("street_lamp_b", "thing_street_lamp", 17.0, -3.4, 1.5, 3.2)
    st.thing("awning", T("thing_awning", "billboard", "a striped shop awning sagging over a shuttered shopfront, sun-faded sepia stripes", 1.0, 128), 13.0, 3.6, 2.0, 2.4)
    st.thing("rubble_c", T("thing_rubble", "billboard", "a low pile of fallen bricks and plaster with a bent lamp bracket", 1.0, 128), 15.0, 3.0, 0.45, 1.2)
    st.thing("washing", T("thing_washing_line", "billboard", "a washing line of sepia shirts and sheets strung across the street (hangs from the top)", 1.0, 128), 12.0, 0.0, 4.4, 2.2, "sway")
    st.light("lt_street_sun", 12.0, 0.0, 5.0, 20.0, "#ffcc80", 1.0)
    st.light("lt_street_lamp", 8.0, 3.2, 3.0, 5.0, "#ffc070", 1.0)
    st.actor("singer", "civilian_city", "d", 5.4, 2.4, activity="stand", prop="hat")
    st.actor("mp1", "mp", "a", 20.0, -1.4, activity="stand")
    st.actor("mp2", "mp", "b", 20.0, 1.6, activity="stand")
    st.actor("kid_c", "civilian_city", "c", 23.0, 0.2, activity="stand")
    st.actor("civ1", "civilian_city", "a", 8.0, -3.0)
    st.actor("civ2", "civilian_city", "b", 13.5, 2.0)
    st.actor("civ3", "civilian_city", "a", 15.5, -2.2)

    # ---- the Colonel's office (C09) ---------------------------------------------------------------------------------------------------------------------------------
    of = mb.room("office_c", (2, 8, 12, 16), 180, "colonel", floor_tex=floor_carpet, ceil_tex=ceil_plaster, wall_tex=wall_panel, ceiling=3.0, light=0.5, tint="#ffd9a0", activities=WAIT)
    of.standard_rail("c09", home=(1.4, 0), good=((3.0, -1.2), (4.2, 1.2)), bad=((1.0, 2.8), (2.4, -2.8)), arrive=(0.6, 0))
    of.wp("c09_x_up", 1.2, 3.4, 90)  # the office door (thrown out)
    of.wp("c09_x_right", 5.6, -1.9, 0)  # (unused doorway key kept for the second route)
    of.thing("medal", T("thing_medal_case", "billboard", "a velvet-lined display case holding one big gold medal on a striped ribbon (colour bars only, no text) glinting on a stand, 128x128", 1.0, 128), 4.6, -1.4, 1.0, 1.0, "pulse")
    of.thing("escape_map", T("thing_map_wall", "billboard", "a large wall map of a sea with coasts drawn in ink, a dotted route line, one corner torn and loose, pins; no names (scribble marks only), 128x128", 1.0, 128), 7.7, 2.6, 1.6, 2.4)
    of.thing("desk_col", T("thing_desk_colonel", "billboard", "a huge polished officer's desk seen from the front: a green leather top, brass lamp, a stack of ribbon-tied papers and a tiny model aeroplane, 128x128", 1.0, 128), 5.2, 0.4, 0.75, 2.2)
    of.thing("globe", T("thing_globe", "billboard", "a brass-mounted globe with blank pale continents, in a stand", 1.0, 128), 6.6, -3.8, 0.9, 1.3)
    of.thing("window_dusk", T("thing_window_dusk", "billboard", "a tall window with heavy velvet curtains, an amber dusk sky and a column of smoke beyond", 1.0, 128), 5.0, -4.8, 1.8, 2.0)
    of.thing("count_slate", T("thing_count_slate", "billboard", "a small blackboard on the wall with a painted number in white digits (a tally: the digits are the only marks), a duster", 1.0, 128), 7.6, -1.8, 1.7, 1.1)
    of.light("lt_office_c", 4.0, 0.0, 2.6, 6.5, "#ffd890", 1.1)
    of.light("lt_window_dusk", 5.0, -4.6, 1.8, 6.0, "#ffa860", 1.0, 90, 40)
    of.actor("col_c", "officer", "a", 5.9, 0.4, fixed=True, same_as="col", activity="stand", prop="medal")
    of.actor("aide_c", "officer", "b", 5.0, 2.7, fixed=True, same_as="aide", activity="check", prop="clipboard", target="c09_x_right")
    of.actor("chap", "officer", "c", 3.0, -3.3, fixed=True, activity="stand")

    # ---- the ruined city at night (C10) -----------------------------------------------------------------------------------------------------------------------------
    ru = mb.room("ruins", (24, 0, 46, 10), -90, "ruins", floor_tex=floor_rubble, ceil_tex=ceil_night_red, wall_tex=wall_ruin, ceiling=7.0, light=0.55, ambient=0.8, tint="#e89070", activities=CROWD_OUT)
    ru.standard_rail("c10", home=(2.0, 0), good=((5.0, -1.5), (9.0, 1.0)), bad=((1.5, 3.0), (2.8, -3.2)), arrive=(0.8, 0))
    ru.wp("c10_x_up", 2.0, -3.9, 140)  # headquarters (back the way you came)
    ru.wp("c10_x_right", 18.0, 0.0, 0)  # the night train
    ru.thing("night_train", T("thing_night_train", "billboard", "a long dark steam train standing on a viaduct far away across the ruins, one big lamp glowing yellow-white on the engine, smoke, silhouetted wagons (a wide sprite, 256x128)", 1.0, 256), 20.5, 0.0, 2.0, 3.6, "pulse")
    ru.thing("hq_door", T("thing_hq_door", "billboard", "the battered door of the headquarters building in a half-ruined wall: a lit rectangle, sandbags, a blank brass plate, 128x128", 1.0, 128), 1.6, -4.4, 1.2, 2.4)
    ru.thing("rubble_a", "thing_rubble", 6.0, 2.4, 0.45, 1.6)
    ru.thing("rubble_b", "thing_rubble", 11.0, -3.0, 0.45, 1.8)
    ru.thing("burnt_car", T("thing_burnt_car", "billboard", "a burnt-out car shell on its rims, soot black, a glow of embers in it", 1.0, 128), 9.0, 3.6, 0.7, 1.7, "flicker")
    ru.thing("fire_barrel", T("thing_fire_barrel", "billboard", "an oil drum fire: flames licking out the top, a few sparks", 1.0, 128), 4.0, -2.6, 0.7, 1.1, "flicker")
    ru.thing("broken_wall", T("thing_broken_wall", "billboard", "a freestanding jagged remnant of a brick wall with a hole where a window was, lit from behind by orange", 1.0, 128), 14.0, 3.8, 1.6, 3.2)
    ru.light("lt_ruin_fire", 4.0, -2.6, 1.0, 6.0, "#ff8038", 1.3)
    ru.light("lt_ruin_train", 18.5, 0.0, 2.0, 12.0, "#fff0b0", 1.1, 0, 25)
    ru.actor("surv1", "civilian_city", "a", 4.6, 2.2, activity="sit")
    ru.actor("surv2", "civilian_city", "b", 6.4, -1.4, activity="sit")
    ru.actor("surv3", "civilian_city", "a", 8.2, 2.8, activity="stand")
    ru.actor("wom", "civilian_city", "b", 5.2, 0.0, fixed=True, activity="stand")
    ru.actor("drunk", "officer", "b", 10.0, -2.4, activity="stand")
    ru.actor("surv4", "civilian_city", "c", 12.0, 1.6, activity="stand")

    mb.portal("bomber_r", "street", (11, 0), (13, 0))
    mb.portal("street", "office_c", (5, 8), (9, 8))
    mb.portal("street", "ruins", (24, 3), (24, 6))
    mb.rooms = {"main": {"palette": "red"}, "street": {"palette": "sepia"}, "colonel": {"palette": "sepia"}, "ruins": {"palette": "fire"}}
    return mb
