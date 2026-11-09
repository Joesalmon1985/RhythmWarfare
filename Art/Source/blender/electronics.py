"""electronics - Bedsit prop kit family: TVs, monitors, PC, DJ gear, phones, console, clock, boombox, socket.

Run all:      blender -b -P electronics.py
Run a subset: blender -b -P electronics.py -- --only crt_tv,monitor_a [--noexport] [--views front34,back34]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, bsk, lib_electronics
importlib.reload(bsk); importlib.reload(lib_electronics)
from bsk import *
from lib_electronics import *
from lib_electronics import _make, _bm_bevel

FAMILY = "electronics"
BUILDERS = {}


def prop(category, notes, variant_of=None):
    def deco(fn):
        BUILDERS[fn.__name__] = (fn, category, notes, variant_of)
        return fn
    return deco


# =====================================================================================================  TVs & monitors

@prop("tv", "15 inch CRT portable. Back (tube bulge) is +Y. Screen child `screen` (convex). Top surface ~0.36 m (slightly domed, vents).")
def crt_tv():
    W, D, H = 0.40, 0.42, 0.38
    body_d = 0.22                      # front cabinet depth
    P = []
    # front cabinet: slightly tapered towards the back, big soft bevel
    P.append(rbox("cab", (W, body_d, H - 0.02), "plastic_beige", (0, -D / 2 + body_d / 2, 0.012), bevel=0.012, segs=3, origin="bottom",
                  taper=(0.985, 0.97), taper_axis="y"))
    # tube bulge: tapered box behind, rounded
    bd = D - body_d - 0.01
    P.append(rbox("bulge", (W * 0.90, bd, (H - 0.02) * 0.88), "plastic_beige", (0, -D / 2 + body_d + bd / 2 - 0.005, 0.035), bevel=0.045, segs=5,
                  origin="bottom", taper=(0.66, 0.66), taper_axis="y"))
    # bezel: dark recessed frame around screen (screen area 0.30 x 0.225, left-of-centre; control strip on right)
    sx, sz = 0.29, 0.22
    scx, scz = -0.03, 0.012 + 0.20
    fy = -D / 2
    frame_d = 0.014
    # bezel ring = 4 dark slabs standing proud of the cabinet face, tapered outwards like a moulded surround
    bz = 0.020
    for (sz_, c_) in [((sx + 2 * bz, bz), (scx, scz + sz / 2 + bz / 2)), ((sx + 2 * bz, bz), (scx, scz - sz / 2 - bz / 2)),
                      ((bz, sz), (scx - sx / 2 - bz / 2, scz)), ((bz, sz), (scx + sx / 2 + bz / 2, scz))]:
        P.append(rbox("bezel", (sz_[0], frame_d, sz_[1]), "plastic_dark", (c_[0], fy + 0.002 - frame_d / 2, c_[1]), bevel=0.004, segs=2))
    # dark glass edge zone just behind the convex screen (fills the corners the bulge leaves)
    P.append(rbox("glass_edge", (sx + 0.006, 0.006, sz + 0.006), "glass_dark", (scx, fy - 0.004, scz), bevel=0.001))
    # control strip on the right: two dials, 4 buttons, small label panel, power LED
    cx = scx + sx / 2 + bz + 0.030
    P.append(rbox("ctrl_panel", (0.052, 0.006, sz + 2 * bz), "plastic_beige_worn", (cx, fy - 0.001, scz), bevel=0.002))
    fy2 = fy - 0.004
    P += knob("vol_knob", 0.012, 0.012, "plastic_dark", (cx, fy2 - 0.006, scz + 0.07), axis="-y", segments=24)
    P += knob("ch_knob", 0.012, 0.012, "plastic_dark", (cx, fy2 - 0.006, scz + 0.03), axis="-y", segments=24)
    for k in range(4):
        P.append(button(f"btn{k}", (0.009, 0.006, 0.004), (cx - 0.016 + k * 0.0105, fy2, scz - 0.012), "plastic_dark", axis="-y"))
    P.append(label("ctrl_lbl", (0.04, 0.006), (cx, fy2 - 0.0005, scz - 0.03), "label_white", "-y"))
    P.append(button("pwr", (0.014, 0.012, 0.006), (cx, fy2, scz - 0.055), "plastic_dark", axis="-y", round_=True))
    P.append(led("pwr_led", 0.002, (cx + 0.018, fy2, scz - 0.055), "led_red", "-y"))
    P.append(label("brand", (0.035, 0.007), (scx - 0.10, fy - 0.0005, scz - sz / 2 - bz - 0.012), "label_white", "-y"))
    # speaker grille strip under the screen
    P.append(grille("spk", 0.24, 0.028, (scx, fy - 0.0002, 0.012 + 0.03), 22, 3, (0.0045, 0.006), depth=0.004, axis="-y"))
    # top vents
    P.append(grille("vent_top", 0.26, 0.10, (0, -D / 2 + body_d / 2 + 0.01, H - 0.008 - 0.0003), 2, 10, (0.11, 0.003), depth=0.004, axis="z"))
    # side vents
    for sgn in (-1, 1):
        P.append(grille("vent_side", 0.08, 0.14, (sgn * (W / 2 - 0.0005), -D / 2 + body_d / 2 + 0.02, 0.19), 1, 12, (0.07, 0.0025), depth=0.004, axis=("x" if sgn > 0 else "-x")))
    # rear: antenna socket, scart slot, power cable
    by = -D / 2 + body_d + bd - 0.005          # back face of the tube bulge (0.25 wide, z 0.04..0.35)
    P.append(rbox("rear_panel", (0.13, 0.006, 0.08), "plastic_dark", (0.025, by - 0.001, 0.15), bevel=0.0015))
    P.append(ring("ant", 0.0075, 0.0045, 0.008, "metal_chrome", (0.065, by + 0.002, 0.17), "y", 16))
    P.append(cyl("ant_pin", 0.0012, 0.008, "metal_chrome", (0.065, by + 0.004, 0.17), "y", 8, bevel=0))
    P.append(port_slots("scart", [(0.052, 0.012, (-0.02, 0.018)), (0.02, 0.008, (-0.04, -0.015)), (0.02, 0.008, (-0.01, -0.015))], (0.025, by + 0.002, 0.15), axis="y"))
    P.append(label("rating", (0.045, 0.022), (-0.065, by + 0.0012, 0.15), "label_white", "y"))
    P.append(cable("pwr_cable", [(0.045, by + 0.002, 0.13), (0.06, by + 0.03, 0.11), (0.10, by + 0.035, 0.03), (0.13, by + 0.02, 0.003), (0.17, by + 0.01, 0.003)], 0.0035))
    # feet
    P += feet("foot", [(-0.16, -D / 2 + 0.03), (0.16, -D / 2 + 0.03), (-0.13, -D / 2 + body_d - 0.02), (0.13, -D / 2 + body_d - 0.02)], r=0.01, h=0.012, z=0)
    # yellowed sticker on the top, peeling corner
    P.append(sticker("sticker", (0.05, 0.03), (0.12, -D / 2 + 0.06, H - 0.008), "label_yellow", "z", angle=0.2, peel=True))
    # convex screen child
    screen = screen_plane(sx, sz, (scx, fy - 0.0045, scz), "-y", bulge=0.012)
    return assemble("electronics_crt_tv", P, {"screen": [screen]})


@prop("tv", "28 inch LCD on a stand. Back (ports/vents) is +Y. Screen child `screen` flat. Base footprint 0.30x0.18.")
def flatscreen_tv():
    W, D, H = 0.65, 0.18, 0.42
    P = []
    pw, ph, pd = W, 0.37, 0.045
    pz = H - ph                               # panel bottom z
    py = 0.0                                  # panel front plane at y = -pd/2
    P.append(rbox("panel", (pw, pd, ph), "plastic_black", (0, 0, pz), bevel=0.004, segs=2, origin="bottom", taper=(0.97, 0.96), taper_axis="y"))
    # glossy bezel face proud of body by 1 mm
    P.append(rbox("bezel", (pw - 0.006, 0.002, ph - 0.006), "plastic_dark", (0, -pd / 2 - 0.001, pz + ph / 2), bevel=0.001))
    sx, sz = pw - 0.034, ph - 0.040
    scz = pz + 0.022 + sz / 2
    # chin: silver strip + logo + LED + IR window
    P.append(rbox("chin", (pw - 0.02, 0.0015, 0.014), "plastic_silver", (0, -pd / 2 - 0.0025, pz + 0.010), bevel=0.0005))
    P.append(label("logo", (0.05, 0.006), (0, -pd / 2 - 0.0035, pz + 0.010), "label_white", "-y"))
    P.append(led("led", 0.002, (pw / 2 - 0.05, -pd / 2 - 0.0033, pz + 0.010), "led_red", "-y"))
    P.append(label("ir", (0.012, 0.006), (pw / 2 - 0.035, -pd / 2 - 0.0033, pz + 0.010), "glass_dark", "-y"))
    # side buttons on right edge
    for k in range(5):
        P.append(button(f"sbtn{k}", (0.006, 0.012, 0.0025), (pw / 2 - 0.004, 0.0, pz + 0.10 + k * 0.016), "plastic_black", axis="x"))
    # back: vent grid, ports, cable
    by = pd / 2 * 0.96
    P.append(grille("vents", 0.30, 0.10, (0.0, by - 0.0002, pz + ph * 0.72), 2, 9, (0.14, 0.004), depth=0.004, axis="y"))
    P.append(rbox("port_bay", (0.16, 0.004, 0.08), "plastic_dark", (-0.17, by - 0.001, pz + 0.10), bevel=0.001))
    P.append(port_slots("ports", [(0.016, 0.006, (-0.05, 0.02)), (0.016, 0.006, (-0.025, 0.02)), (0.016, 0.006, (0.0, 0.02)), (0.052, 0.012, (0.03, 0.02)), (0.012, 0.005, (-0.05, -0.02)), (0.012, 0.005, (-0.03, -0.02))],
                        (-0.17, by + 0.001, pz + 0.10), axis="y"))
    P += rca_ports("rca", [(0.02, -0.02), (0.035, -0.02), (0.05, -0.02)], (-0.17, by + 0.001, pz + 0.10), axis="y")
    P.append(cable("cable", [(0.18, by, pz + 0.08), (0.19, by + 0.04, pz + 0.05), (0.20, by + 0.06, 0.02), (0.19, D / 2 + 0.03, 0.003)], 0.0035))
    # stand: neck + oval-ish base
    P.append(rbox("neck", (0.10, 0.024, pz + 0.01), "plastic_black", (0, 0.015, 0.006), bevel=0.004, origin="bottom", taper=(1.5, 0.9), taper_axis="z"))
    base = cyl("base", 0.15, 0.012, "plastic_black", (0, 0.0, 0.0), "z", 40, bevel=0.004, r_top=0.14, origin="bottom")
    base.scale = (1, 0.6, 1)
    P.append(base)
    P.append(cyl("base_top", 0.12, 0.004, "plastic_dark", (0, 0.0, 0.012), "z", 40, bevel=0.0015, r_top=0.11, origin="bottom"))
    P += feet("foot", [(-0.11, -0.04), (0.11, -0.04), (-0.11, 0.04), (0.11, 0.04)], r=0.007, h=0.003, z=-0.003)
    screen = screen_plane(sx, sz, (0, -pd / 2 - 0.0015, scz), "-y")
    return assemble("electronics_flatscreen_tv", P, {"screen": [screen]})


def _lcd_monitor(name, W, ph, bezel, role_body, role_bezel, stand, sz_override=None, chin=0.02):
    """shared monitor builder. returns (parts, screen)"""
    P = []
    pd = 0.035
    pz = stand["h"]
    P.append(rbox("panel", (W, pd, ph), role_body, (0, 0, pz), bevel=0.004, segs=2, origin="bottom", taper=(0.96, 0.94), taper_axis="y"))
    P.append(rbox("bezel", (W - 0.004, 0.0025, ph - 0.004), role_bezel, (0, -pd / 2 - 0.0012, pz + ph / 2), bevel=0.0015))
    sx, sz = W - 2 * bezel, ph - bezel - chin
    scz = pz + chin + sz / 2
    # buttons under the chin, LED
    for k in range(5):
        P.append(button(f"btn{k}", (0.008, 0.005, 0.002), (W / 2 - 0.09 + k * 0.014, -pd / 2 - 0.0025, pz + chin / 2), role_bezel if role_bezel != "plastic_black" else "plastic_dark", axis="-y"))
    P.append(led("led", 0.0018, (W / 2 - 0.02, -pd / 2 - 0.0025, pz + chin / 2), "led_green", "-y"))
    P.append(label("logo", (0.03, 0.005), (0, -pd / 2 - 0.0028, pz + chin / 2), "label_white", "-y"))
    # back: vesa plate, vents, ports
    by = pd / 2 * 0.94
    P.append(rbox("vesa", (0.12, 0.006, 0.12), "plastic_dark", (0, by, pz + ph * 0.5), bevel=0.002))
    for (dx, dz) in [(-0.05, -0.05), (0.05, -0.05), (-0.05, 0.05), (0.05, 0.05)]:
        P.append(cyl("vesa_hole", 0.003, 0.003, "label_black", (dx, by + 0.003, pz + ph * 0.5 + dz), "y", 8, bevel=0))
    P.append(grille("vents", W * 0.5, 0.05, (0, by - 0.0002, pz + ph * 0.86), 2, 5, (W * 0.23, 0.0035), depth=0.004, axis="y"))
    P.append(port_slots("ports", [(0.016, 0.006, (-0.03, 0)), (0.012, 0.005, (-0.008, 0)), (0.030, 0.009, (0.02, 0))], (0.05, by + 0.001, pz + 0.03), axis="y"))
    P.append(label("rating", (0.04, 0.02), (-0.09, by + 0.0008, pz + 0.04), "label_white", "y"))
    screen = screen_plane(sx, sz, (0, -pd / 2 - 0.0028, scz), "-y")
    return P, screen, pd


@prop("monitor", "22 inch 16:10 LCD on a tilting stand, cable down the back. Back is +Y. Top of panel ~0.44 m.")
def monitor_a():
    W, ph = 0.50, 0.33
    stand = {"h": 0.10}
    P, screen, pd = _lcd_monitor("monitor_a", W, ph, 0.016, "plastic_black", "plastic_black", stand, chin=0.022)
    pz = stand["h"]
    # tilting hinge: horizontal cylinder (axis x) behind the panel, bracket clasps
    P.append(cyl("hinge", 0.014, 0.08, "plastic_dark", (0, pd / 2 + 0.012, pz + 0.07), "x", 20, bevel=0.002))
    P.append(rbox("hinge_brk", (0.06, 0.02, 0.03), "plastic_dark", (0, pd / 2 + 0.006, pz + 0.045), bevel=0.003))
    # column: tilted back a little, flat with a cable clip hole
    col = rbox("column", (0.055, 0.022, pz + 0.07), "plastic_black", (0, pd / 2 + 0.018, 0.012), bevel=0.004, origin="bottom", taper=(1.0, 0.75), taper_axis="z")
    col.rotation_euler = (math.radians(-6), 0, 0)
    P.append(col)
    P.append(ring("clip", 0.012, 0.009, 0.006, "plastic_dark", (0, pd / 2 + 0.032, 0.05), "y", 16))
    # base: oval dish
    base = cyl("base", 0.13, 0.014, "plastic_black", (0, 0.03, 0.0), "z", 40, bevel=0.005, r_top=0.12, origin="bottom")
    base.scale = (1, 0.75, 1)
    P.append(base)
    P.append(cyl("base_ring", 0.045, 0.004, "plastic_dark", (0, 0.03, 0.014), "z", 32, bevel=0.0015, r_top=0.04, origin="bottom"))
    P += feet("foot", [(-0.10, 0.0), (0.10, 0.0), (0, -0.06), (0, 0.11)], r=0.008, h=0.003, z=-0.003)
    # power + video cables running from the back ports down through the clip to the floor
    P.append(cable("cable_v", [(0.02, pd / 2 * 0.94, pz + 0.03), (0.01, pd / 2 + 0.04, pz), (0.004, pd / 2 + 0.034, 0.05), (0.004, pd / 2 + 0.03, 0.01), (0.03, 0.16, 0.003), (0.05, 0.21, 0.003)], 0.003))
    P.append(cable("cable_p", [(0.08, pd / 2 * 0.94, pz + 0.03), (0.04, pd / 2 + 0.045, pz - 0.01), (-0.004, pd / 2 + 0.036, 0.05), (-0.006, pd / 2 + 0.03, 0.01), (-0.04, 0.17, 0.003), (-0.08, 0.20, 0.003)], 0.0035))
    return assemble("electronics_monitor_a", P, {"screen": [screen]})


@prop("monitor", "17 inch 4:3 LCD, early-2000s silver/beige with thick bezel, round base. Back is +Y. Top of panel ~0.40 m.")
def monitor_b():
    W, ph = 0.37, 0.31
    stand = {"h": 0.085}
    P, screen, pd = _lcd_monitor("monitor_b", W, ph, 0.028, "plastic_beige", "plastic_silver", stand, chin=0.032)
    pz = stand["h"]
    # chunky neck + round base
    P.append(rbox("neck", (0.07, 0.04, pz + 0.05), "plastic_beige", (0, 0.0, 0.01), bevel=0.006, origin="bottom", taper=(0.8, 0.5), taper_axis="z"))
    P.append(cyl("base", 0.11, 0.012, "plastic_beige", (0, 0.0, 0.0), "z", 40, bevel=0.004, r_top=0.10, origin="bottom"))
    P.append(cyl("base_pad", 0.07, 0.004, "plastic_silver", (0, 0.0, 0.012), "z", 32, bevel=0.0015, r_top=0.062, origin="bottom"))
    P += feet("foot", [(-0.08, 0.0), (0.08, 0.0), (0, -0.08), (0, 0.08)], r=0.008, h=0.003, z=-0.003)
    P.append(cable("cable_v", [(0.02, pd / 2 * 0.94, pz + 0.03), (0.0, pd / 2 + 0.04, pz - 0.01), (0.0, 0.05, 0.02), (0.03, 0.14, 0.003), (0.05, 0.20, 0.003)], 0.003))
    P.append(cable("cable_p", [(0.08, pd / 2 * 0.94, pz + 0.03), (0.05, pd / 2 + 0.05, pz - 0.02), (0.02, 0.06, 0.015), (-0.03, 0.15, 0.003), (-0.07, 0.19, 0.003)], 0.0035))
    # yellowed sticker on the bezel corner
    P.append(sticker("sticker", (0.022, 0.014), (-W / 2 + 0.035, -pd / 2 - 0.003, pz + 0.05), "label_blue", "-y", angle=-0.15, peel=True))
    return assemble("electronics_monitor_b", P, {"screen": [screen]})


# =====================================================================================================  PC & peripherals

@prop("computer", "Mid-tower PC, silver front / black body. Front -Y, back (+Y) has IO shield, PSU, slot covers and cable stubs. Top surface 0.42 m (can take clutter).")
def pc_tower():
    W, D, H = 0.19, 0.42, 0.42
    P = []
    P.append(rbox("case", (W, D - 0.012, H - 0.006), "plastic_black", (0, 0.006, 0.006), bevel=0.003, origin="bottom"))
    fy = -D / 2
    P.append(rbox("front", (W, 0.014, H - 0.006), "plastic_silver", (0, fy + 0.007, 0.006), bevel=0.005, segs=3, origin="bottom", taper=(0.985, 0.99), taper_axis="y"))
    ff = fy - 0.0002
    # 5.25" bays: optical drive + blank cover
    bay_w, bay_h = 0.148, 0.042
    bz1, bz2 = H - 0.05, H - 0.095
    P.append(rbox("odd", (bay_w, 0.004, bay_h), "plastic_black", (0, ff - 0.002, bz1), bevel=0.0015))
    P.append(rbox("odd_tray", (bay_w - 0.012, 0.002, 0.016), "plastic_dark", (0, ff - 0.004, bz1 + 0.006), bevel=0.0008))
    P.append(port_slots("odd_slot", [(0.11, 0.0015, (0, 0))], (0, ff - 0.0045, bz1 + 0.013), axis="-y", depth=0.002))
    P.append(button("odd_eject", (0.009, 0.004, 0.002), (0.055, ff - 0.004, bz1 - 0.010), "plastic_dark", axis="-y"))
    P.append(led("odd_led", 0.0015, (0.04, ff - 0.004, bz1 - 0.010), "led_green", "-y"))
    P.append(label("odd_lbl", (0.03, 0.006), (-0.04, ff - 0.0045, bz1 - 0.010), "label_white", "-y"))
    P.append(rbox("blank", (bay_w, 0.003, bay_h), "plastic_silver", (0, ff - 0.0015, bz2), bevel=0.0012))
    P.append(grille("blank_lines", bay_w - 0.02, 0.03, (0, ff - 0.0032, bz2), 1, 4, (bay_w - 0.03, 0.0015), depth=0.002, axis="-y"))
    # 3.5" card reader
    P.append(rbox("cr", (0.10, 0.003, 0.025), "plastic_black", (0, ff - 0.0015, H - 0.13), bevel=0.001))
    P.append(port_slots("cr_slots", [(0.03, 0.003, (-0.025, 0.005)), (0.025, 0.003, (0.02, 0.005)), (0.016, 0.0035, (-0.03, -0.006)), (0.012, 0.008, (0.03, -0.004))], (0, ff - 0.0032, H - 0.13), axis="-y", depth=0.004))
    # front IO + power/reset + LEDs
    pz = H - 0.165
    P.append(button("power", (0.018, 0.018, 0.003), (0.0, ff, pz), "plastic_silver", axis="-y", round_=True, segments=24))
    P.append(ring("power_ring", 0.011, 0.0095, 0.0015, "metal_chrome", (0.0, ff, pz), "-y", 24))
    P.append(button("reset", (0.006, 0.006, 0.0015), (0.03, ff, pz), "plastic_dark", axis="-y", round_=True))
    P.append(led("led_pwr", 0.0018, (-0.03, ff, pz + 0.005), "led_green", "-y"))
    P.append(led("led_hdd", 0.0018, (-0.03, ff, pz - 0.005), "led_red", "-y"))
    P.append(port_slots("usb", [(0.012, 0.0045, (-0.025, 0)), (0.012, 0.0045, (-0.008, 0))], (0, ff - 0.0002, pz - 0.03), axis="-y", depth=0.008))
    P += rca_ports("jack", [(0.012, 0), (0.026, 0)], (0, ff - 0.0002, pz - 0.03), axis="-y", role="plastic_green", r=0.0035)
    P.append(ring("jack_pink", 0.0035, 0.002, 0.001, "plastic_red", (0.026, ff - 0.0048, pz - 0.03), "-y", 12))
    # perforated grille over the lower half
    gh = H - 0.22
    P.append(rbox("grille_frame", (W - 0.02, 0.003, gh - 0.02), "plastic_dark", (0, ff - 0.0012, 0.01 + (gh - 0.02) / 2 + 0.004), bevel=0.0015))
    P.append(grille("mesh", W - 0.036, gh - 0.036, (0, ff - 0.0028, 0.01 + (gh - 0.02) / 2 + 0.004), 8, 14, (0.0065, 0.0065), depth=0.003, axis="-y", round_holes=True))
    P.append(sticker("sticker_os", (0.022, 0.016), (0.06, ff - 0.003, 0.08), "label_blue", "-y", angle=0.05))
    P.append(sticker("sticker_cpu", (0.02, 0.02), (0.06, ff - 0.003, 0.105), "label_white", "-y", angle=-0.08, peel=True))
    # side vents (left side -x), rave sticker on side
    P.append(grille("side_vent", 0.12, 0.10, (-W / 2 + 0.0002, 0.05, 0.14), 8, 7, (0.004, 0.010), depth=0.003, axis="-x"))
    P.append(sticker("side_sticker", (0.07, 0.045), (-W / 2 - 0.0005, -0.02, 0.30), "label_yellow", "-x", angle=0.3, peel=True))
    P.append(cyl("thumbscrew", 0.005, 0.002, "metal_steel", (-W / 2 - 0.001, D / 2 - 0.02, H - 0.03), "-x", 12, bevel=0.0005))
    P.append(cyl("thumbscrew2", 0.005, 0.002, "metal_steel", (-W / 2 - 0.001, D / 2 - 0.02, 0.03), "-x", 12, bevel=0.0005))
    # rear
    by = D / 2 - 0.0002
    P.append(rbox("psu", (0.15, 0.004, 0.085), "metal_dark", (0, by - 0.001, H - 0.05), bevel=0.001))
    P.append(grille("psu_fan", 0.075, 0.075, (0.03, by + 0.001, H - 0.05), 6, 6, (0.008, 0.008), depth=0.003, axis="y", round_holes=True))
    P.append(port_slots("iec", [(0.02, 0.014, (0, 0))], (-0.05, by + 0.001, H - 0.05), axis="y", depth=0.008))
    P.append(rbox("io_shield", (0.044, 0.002, 0.16), "metal_steel", (-0.05, by, H - 0.19), bevel=0.0005))
    P.append(port_slots("io_ports", [(0.012, 0.0045, (-0.008, 0.06)), (0.012, 0.0045, (0.008, 0.06)), (0.012, 0.0045, (-0.008, 0.04)), (0.012, 0.0045, (0.008, 0.04)),
                                      (0.016, 0.008, (0, 0.015)), (0.028, 0.009, (0, -0.012)), (0.016, 0.006, (0, -0.035))], (-0.05, by + 0.001, H - 0.19), axis="y", depth=0.01))
    P += rca_ports("io_jacks", [(-0.01, -0.058), (0.0, -0.058), (0.01, -0.058)], (-0.05, by + 0.001, H - 0.19), axis="y", role="plastic_green", r=0.003)
    for k in range(7):
        P.append(rbox(f"slot{k}", (0.012, 0.0015, 0.11), "metal_steel", (0.05 - k * 0.02 if k < 5 else 0.05 - k * 0.02, by, H - 0.19 - 0.02), bevel=0.0004))
    P.append(grille("rear_vent", 0.14, 0.06, (0, by + 0.001, 0.05), 10, 5, (0.006, 0.006), depth=0.003, axis="y", round_holes=True))
    P.append(cable("cable_pwr", [(-0.05, by + 0.003, H - 0.05), (-0.06, by + 0.05, H - 0.08), (-0.07, by + 0.06, 0.03), (-0.06, by + 0.05, 0.003), (-0.02, by + 0.07, 0.003)], 0.004))
    P.append(cable("cable_dvi", [(-0.05, by + 0.003, H - 0.19 - 0.012), (-0.03, by + 0.04, H - 0.22), (0.02, by + 0.05, 0.05), (0.06, by + 0.06, 0.003), (0.09, by + 0.08, 0.003)], 0.003))
    P += corner_feet(W, D, inset=0.025, r=0.009, h=0.006)
    return assemble("electronics_pc_tower", P)


def _key_rows():
    """Returns (keys, special) in key units (u). keys = [(x, y, w, d, worn)] in u, x,y = centre."""
    rows = []
    def row(y, specs, x0=0.0):
        x = x0
        out = []
        for s in specs:
            if isinstance(s, tuple) and s[0] == "gap":
                x += s[1]
                continue
            w, worn = (s, False) if not isinstance(s, tuple) else (s[0], s[1] == "worn")
            out.append((x + w / 2, y, w, 1.0, worn))
            x += w
        return out
    # main block
    rows += row(5.25, [1, ("gap", 1), 1, 1, 1, 1, ("gap", 0.5), 1, 1, 1, 1, ("gap", 0.5), 1, 1, 1, 1])
    rows += row(4, [1] * 13 + [2])
    rows += row(3, [1.5, 1, (1, "worn"), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1.5])
    rows += row(2, [1.75, (1, "worn"), (1, "worn"), (1, "worn"), 1, 1, 1, 1, 1, 1, 1, 1, (2.25, "worn")])
    rows += row(1, [2.25, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2.75])
    rows += row(0, [1.25, 1.25, 1.25, (6.25, "worn"), 1.25, 1.25, 1.25, 1.25])
    # nav cluster
    nx = 15.25
    rows += row(5.25, [1, 1, 1], nx)
    rows += row(4, [1, 1, 1], nx)
    rows += row(3, [1, 1, 1], nx)
    rows += row(1, [("gap", 1), 1], nx)
    rows += row(0, [1, 1, 1], nx)
    # numpad
    px = 18.5
    rows += row(4, [1, 1, 1, 1], px)
    rows += row(3, [1, 1, 1], px)
    rows += row(2, [1, 1, 1], px)
    rows += row(1, [1, 1, 1], px)
    rows += row(0, [2, 1], px)
    tall = [(px + 3.5, 2.5, 1, 2, False), (px + 3.5, 0.5, 1, 2, False)]  # + and Enter (2u tall)
    return rows + tall


@prop("computer", "Full-size yellowed beige keyboard, 0.445 x 0.155, 0.035 high at the back. Front -Y, cable exits back centre. Sits on a desk.")
def keyboard():
    u = 0.019
    W, D = 0.445, 0.155
    P = []
    base_h_front, base_h_back = 0.016, 0.026
    P.append(wedge("base", (W, D, base_h_front), "plastic_beige", (0, 0, 0), back_h=base_h_back, bevel=0.005, segs=3))
    # key field recess
    keys = []
    x0 = -W / 2 + 0.012
    y0 = -D / 2 + 0.014
    for (kx, ky, kw, kd, worn) in _key_rows():
        cx = x0 + kx * u
        cy = y0 + (ky + kd / 2) * u
        # base top at this y (wedge) -> key sits on the slope
        t = (cy + D / 2) / D
        z0 = base_h_front + (base_h_back - base_h_front) * t - 0.004
        keys.append((cx, cy, kw * u - 0.0025, kd * u - 0.0025, 0.0105, z0, worn))
    P.append(keycaps("keys", [k[:6] for k in keys if not k[6]], "plastic_beige"))
    P.append(keycaps("keys_worn", [k[:6] for k in keys if k[6]], "plastic_beige_worn", taper=(0.82, 0.78)))
    # a dark recess plate under the keys so gaps read as shadow
    P.append(wedge("recess", (W - 0.016, D - 0.016, base_h_front - 0.0035), "plastic_dark", (0, 0, 0), back_h=base_h_back - 0.0035, bevel=0.001))
    # LEDs + legend strip above numpad, logo on left
    ledz = base_h_back - 0.0025
    for k, (dx, role) in enumerate([(0.0, "led_green"), (0.019, "led_green"), (0.038, "led_green")]):
        P.append(led(f"led{k}", 0.0016, (x0 + 18.75 * u + dx, D / 2 - 0.0095, ledz), role, "z"))
    P.append(label("led_lbl", (0.055, 0.005), (x0 + 19.5 * u, D / 2 - 0.016, ledz), "label_white", "z"))
    P.append(label("logo", (0.03, 0.006), (x0 + 1.5 * u, D / 2 - 0.009, ledz), "label_white", "z"))
    # cable out the back centre, flip-out feet + pads underneath
    P.append(cable("cable", [(0.05, D / 2 - 0.01, 0.012), (0.05, D / 2 + 0.01, 0.01), (0.06, D / 2 + 0.05, 0.003), (0.03, D / 2 + 0.10, 0.003)], 0.0025))
    P += feet("pad", [(-W / 2 + 0.03, -D / 2 + 0.02), (W / 2 - 0.03, -D / 2 + 0.02)], r=0.006, h=0.002, z=-0.002)
    P.append(boxes("flipfeet", [((0.02, 0.012, 0.006), (-W / 2 + 0.03, D / 2 - 0.02, -0.003)), ((0.02, 0.012, 0.006), (W / 2 - 0.03, D / 2 - 0.02, -0.003))], "plastic_beige", bevel=0.001))
    P.append(sticker("sticker", (0.02, 0.014), (x0 + 17.5 * u, D / 2 - 0.009, ledz), "label_red", "z", angle=-0.2, peel=True))
    return assemble("electronics_keyboard", P)


@prop("computer", "Ergonomic two-button scroll mouse, cable from the front (-Y). 0.065 x 0.115 x 0.038.")
def mouse():
    P = []
    # (y, width, height, z_bottom): low flat nose, hump under the palm, tapering tail
    st = [(-0.058, 0.030, 0.009, 0.002), (-0.054, 0.044, 0.013, 0.0015), (-0.045, 0.054, 0.018, 0.001), (-0.03, 0.060, 0.024, 0.001), (-0.012, 0.063, 0.030, 0.001),
          (0.008, 0.066, 0.035, 0.001), (0.028, 0.065, 0.036, 0.001), (0.044, 0.058, 0.030, 0.001), (0.054, 0.042, 0.019, 0.0015), (0.058, 0.022, 0.008, 0.002)]
    def hz(y):
        for (a, b) in zip(st[:-1], st[1:]):
            if a[0] <= y <= b[0]:
                t = (y - a[0]) / (b[0] - a[0])
                return a[3] + a[2] + (b[2] + b[3] - a[2] - a[3]) * t
        return st[0][2]
    P.append(loft_shell("shell", st, "plastic_beige", nseg=22, expo=2.6))
    # button shell: a second, 0.6 mm bigger loft over the front third (greasier, shinier plastic) -> real seam + colour break
    bst = [(y, w + 0.0012, h + 0.0006, zb + 0.004) for (y, w, h, zb) in st if y <= -0.012] + [(-0.011, 0.0632, 0.0304, 0.005)]
    P.append(loft_shell("buttons", bst, "plastic_beige_worn", nseg=22, expo=2.6, bottom_round=0.002))
    # centre seam between the two buttons
    P.append(cable("seam", [(0, y, hz(y) + 0.0004) for y in (-0.056, -0.05, -0.04, -0.03, -0.02, -0.013)], 0.0005, "plastic_dark", per_seg=3, segments=6))
    # scroll wheel in a slot
    P.append(boxes("wheel_slot", [((0.009, 0.020, 0.012), (0, -0.032, hz(-0.032) - 0.005))], "label_black", bevel=0))
    P.append(cyl("wheel", 0.0085, 0.006, "rubber_grey", (0, -0.032, hz(-0.032) - 0.003), "x", 20, bevel=0.0012))
    # rubber side grips
    for sx in (-1, 1):
        g = loft_shell("grip", [(y, 0.002, 0.012, 0.004) for y in (-0.02, 0.0, 0.02, 0.035)], "rubber_grey", nseg=6, expo=2.0, bottom_round=0.001)
        g.location = (sx * 0.0315, 0, 0.0)
        P.append(g)
    # cable, feet, base plate
    P.append(cable("cable", [(0, -0.056, 0.008), (0, -0.075, 0.006), (0.01, -0.10, 0.003), (0.04, -0.13, 0.003), (0.08, -0.15, 0.003)], 0.0018))
    P.append(boxes("base", [((0.05, 0.095, 0.002), (0, 0, 0.0012))], "plastic_dark", bevel=0.0005))
    P += feet("foot", [(-0.018, -0.038), (0.018, -0.038), (-0.02, 0.035), (0.02, 0.035)], r=0.005, h=0.0008, z=0.0)
    return assemble("electronics_mouse", P)


@prop("computer", "Cloth mouse mat 0.25 x 0.21, 4 mm, one corner curling. Pairs with electronics_mouse on top (mat top z=0.004).")
def mousemat():
    W, D, T = 0.25, 0.21, 0.004
    bm = bmesh.new()
    nx, ny = 16, 14
    def curl(x, y):   # far-right-back corner lifts and curls up
        d = max(0.0, (x - W / 2 + 0.09) / 0.09) * max(0.0, (y - D / 2 + 0.08) / 0.08)
        return 0.022 * d ** 2.0
    def corner_pull(i, j):
        # chamfer the four outline corners
        x = (i / nx - 0.5) * W
        y = (j / ny - 0.5) * D
        if i in (0, nx) and j in (0, ny):
            x *= 0.94; y *= 0.93
        return x, y
    top, bot = [], []
    for j in range(ny + 1):
        rt, rb = [], []
        for i in range(nx + 1):
            x, y = corner_pull(i, j)
            c = curl(x, y)
            rt.append(bm.verts.new((x, y, T + c)))
            rb.append(bm.verts.new((x, y, c)))
        top.append(rt); bot.append(rb)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
    # side walls
    for i in range(nx):
        bm.faces.new((top[0][i], bot[0][i], bot[0][i + 1], top[0][i + 1]))
        bm.faces.new((top[ny][i], top[ny][i + 1], bot[ny][i + 1], bot[ny][i]))
    for j in range(ny):
        bm.faces.new((top[j][0], top[j + 1][0], bot[j + 1][0], bot[j][0]))
        bm.faces.new((top[j][nx], bot[j][nx], bot[j + 1][nx], top[j + 1][nx]))
    ob = _make(bm, "mat", "cotton_black", smooth=True)
    P = [ob, label("print", (0.06, 0.03), (-0.07, -0.06, T + 0.0003), "label_cyan" if "label_cyan" in MATERIALS else "plastic_cyan", "z")]
    return assemble("electronics_mousemat", P)


def _laptop_base(W=0.34, D=0.24, Hb=0.024):
    P = []
    P.append(rbox("base", (W, D, Hb), "plastic_dark", (0, 0, 0), bevel=0.005, segs=3, origin="bottom", taper=(0.985, 0.98), taper_axis="z"))
    top = Hb + 0.0001
    # keyboard recess + chiclet keys (6 rows x 14)
    kw, kp = 0.0155, 0.0185
    kx0 = -6.5 * kp
    ky0 = 0.085 - 2.5 * kp
    P.append(boxes("kb_recess", [((14 * kp + 0.004, 6 * kp + 0.004, 0.002), (0, ky0 + 2.5 * kp, top - 0.0011))], "plastic_black", bevel=0))
    keys = []
    for r in range(6):
        for c in range(14):
            w = kw
            cx = kx0 + c * kp
            if r == 0 and c == 13:
                continue
            if r == 5 and 4 <= c <= 8:
                continue
            keys.append((cx, ky0 + r * kp, w, kw * (0.6 if r == 0 else 1.0), 0.002, top - 0.0008))
    keys.append((kx0 + 6 * kp, ky0 + 5 * kp, 5 * kp - 0.003, kw, 0.002, top - 0.0008))   # spacebar
    P.append(keycaps("keys", keys, "plastic_black", bevel=0.0005, taper=(0.92, 0.92), dish=False))
    # trackpad + buttons, palm rest sticker, power button + LEDs
    P.append(boxes("trackpad", [((0.085, 0.05, 0.001), (0, -0.06, top - 0.0004))], "plastic_grey", bevel=0.0004))
    P.append(boxes("tp_btns", [((0.041, 0.012, 0.0015), (-0.021, -0.093, top + 0.0004)), ((0.041, 0.012, 0.0015), (0.021, -0.093, top + 0.0004))], "plastic_dark", bevel=0.0006))
    P.append(sticker("palm_sticker", (0.03, 0.012), (-0.11, -0.07, top), "label_white", "z", angle=0.1))
    P.append(sticker("palm_sticker2", (0.02, 0.02), (-0.13, -0.045, top), "label_blue", "z", angle=-0.3, peel=True))
    P.append(button("power", (0.012, 0.012, 0.001), (W / 2 - 0.03, 0.105, top), "plastic_silver", axis="z", round_=True))
    for k, role in enumerate(["led_green", "led_green", "led_red"]):
        P.append(led(f"led{k}", 0.0012, (-W / 2 + 0.04 + k * 0.008, -D / 2 - 0.0001, Hb * 0.5), role, "-y"))
    # side ports: left = power, vent, USB; right = USB x2, headphone, ethernet
    P.append(grille("vent", 0.07, 0.012, (-W / 2 + 0.0002, 0.03, Hb * 0.55), 10, 1, (0.0045, 0.010), depth=0.004, axis="-x"))
    P.append(port_slots("ports_l", [(0.012, 0.0045, (-0.05, 0)), (0.012, 0.0045, (-0.034, 0))], (-W / 2 + 0.0002, 0.0, Hb * 0.55), axis="-x", depth=0.008))
    P.append(ring("dc", 0.004, 0.0015, 0.004, "metal_dark", (-W / 2 - 0.001, -0.09, Hb * 0.55), "x", 12))
    P.append(port_slots("ports_r", [(0.012, 0.0045, (0.0, 0)), (0.012, 0.0045, (0.016, 0)), (0.016, 0.012, (0.05, 0))], (W / 2 - 0.0002, 0.0, Hb * 0.55), axis="x", depth=0.008))
    P += rca_ports("hp", [(-0.03, 0), (-0.04, 0)], (W / 2 - 0.0002, 0.0, Hb * 0.55), axis="x", role="plastic_dark", r=0.0028)
    P.append(port_slots("odd", [(0.125, 0.002, (0, 0))], (W / 2 - 0.0002, -0.07, Hb * 0.5), axis="x", depth=0.002))
    P += feet("foot", [(-W / 2 + 0.02, -D / 2 + 0.02), (W / 2 - 0.02, -D / 2 + 0.02), (-W / 2 + 0.02, D / 2 - 0.02), (W / 2 - 0.02, D / 2 - 0.02)], r=0.006, h=0.003, z=-0.003)
    # hinges: two barrels along x at the back edge, top of base
    hy, hz = D / 2 - 0.012, Hb + 0.004
    for sx in (-1, 1):
        P.append(cyl("hinge", 0.0065, 0.05, "plastic_black", (sx * 0.10, hy, hz), "x", 16, bevel=0.001))
    return P, (hy, hz)


def _laptop_lid(W, Ld, hy, hz, open_deg, inner=True):
    """Lid built upright (screen facing -Y) with its bottom edge on the hinge line, then rotated open."""
    t = 0.009
    L = []
    L.append(rbox("lid", (W, t, Ld), "plastic_dark", (0, hy + 0.001, hz + 0.0), bevel=0.004, segs=3, origin="bottom"))
    if inner:
        L.append(rbox("bezel", (W - 0.008, 0.002, Ld - 0.010), "plastic_black", (0, hy + 0.001 - t / 2 - 0.0008, hz + 0.004 + (Ld - 0.010) / 2), bevel=0.001))
        L.append(dome("cam", 0.002, 0.0008, "glass_dark", (0, hy + 0.001 - t / 2 - 0.002, hz + Ld - 0.012), "-y", 10, 3))
        L.append(label("lid_logo", (0.02, 0.005), (0, hy + 0.001 - t / 2 - 0.0021, hz + 0.011), "label_white", "-y"))
    # outside of the lid: stickers (rave stuff) + logo
    oy = hy + 0.001 + t / 2
    L.append(label("logo_out", (0.03, 0.03), (0, oy + 0.0003, hz + Ld / 2), "plastic_silver", "y"))
    L.append(sticker("s1", (0.05, 0.03), (-0.09, oy, hz + Ld * 0.3), "label_yellow", "y", angle=0.25, peel=True))
    L.append(sticker("s2", (0.035, 0.035), (0.10, oy, hz + Ld * 0.7), "label_red", "y", angle=-0.4))
    L.append(sticker("s3", (0.04, 0.02), (0.08, oy, hz + Ld * 0.25), "plastic_cyan", "y", angle=0.1))
    L.append(sticker("s4", (0.025, 0.025), (-0.11, oy, hz + Ld * 0.75), "label_white", "y", angle=0.6, peel=True))
    sx, sz = W - 0.040, Ld - 0.044
    screen = screen_plane(sx, sz, (0, hy + 0.001 - t / 2 - 0.0022, hz + 0.028 + sz / 2), "-y") if inner else None
    ang = math.radians(-(open_deg - 90))      # 110 deg open -> leans back 20 deg
    rotate_parts(L, (ang, 0, 0), (0, hy, hz))
    if screen:
        rotate_parts([screen], (ang, 0, 0), (0, hy, hz))
    return L, screen


@prop("computer", "15 inch laptop open to 110 degrees, screen child `screen`, stickers on the lid back. Front -Y. Deck height 0.024.")
def laptop_open():
    W, D = 0.34, 0.24
    P, (hy, hz) = _laptop_base(W, D)
    L, screen = _laptop_lid(W, 0.23, hy, hz, 110)
    return assemble("electronics_laptop_open", P + L, {"screen": [screen]})


@prop("computer", "Same laptop closed (lid flat, stickers on top). 0.34 x 0.24 x 0.034. Front -Y.", variant_of="electronics_laptop_open")
def laptop_closed():
    W, D = 0.34, 0.24
    P, (hy, hz) = _laptop_base(W, D)
    L, _ = _laptop_lid(W, 0.23, hy, hz, 180, inner=False)
    # open_deg=180 lays the lid flat pointing +Y; flip it 180 about the hinge so it lies over the base, stickers up
    rotate_parts(L, (math.radians(180), 0, 0), (0, hy, hz))
    return assemble("electronics_laptop_closed", P + L)


# =====================================================================================================  audio / DJ gear

def _desk_speaker(x, active):
    W, D, H = 0.11, 0.15, 0.20
    P = []
    P.append(hollow_cabinet("cab", (W, D, H), "wood_light", (x, 0, 0), wall=0.012, bevel=0.0025))
    fy = -D / 2
    P.append(baffle_with_holes("baffle", (W - 0.004, 0.008, H - 0.004), "plastic_black", (x, fy - 0.001, H / 2),
                               [(0, 0.075 - H / 2, 0.034), (0, 0.158 - H / 2, 0.0125), (0.03, 0.03 - H / 2, 0.0085)]))
    P.append(boxes("liner", [((W - 0.026, 0.003, H - 0.026), (x, D / 2 - 0.014, H / 2))], "foam_black", bevel=0))
    P += speaker_driver("woofer", 0.036, (x, fy - 0.005, 0.075), "-y", depth=0.02, segments=28)
    P.append(ring("tw_ring", 0.016, 0.012, 0.002, "plastic_dark", (x, fy - 0.005, 0.158), "-y", 24))
    P.append(dome("tweeter", 0.011, 0.006, "metal_alu", (x, fy - 0.005, 0.158), "-y", 24, 5))
    P.append(ring("port", 0.011, 0.008, 0.003, "plastic_dark", (x + 0.03, fy - 0.005, 0.03), "-y", 20))
    P.append(cyl("port_in", 0.0082, 0.03, "label_black", (x + 0.03, fy + 0.012, 0.03), "y", 16, bevel=0))
    if active:
        P += knob("vol", 0.007, 0.008, "plastic_dark", (x - 0.03, fy - 0.009, 0.03), "-y", 16)
        P.append(led("led", 0.0015, (x - 0.014, fy - 0.0052, 0.03), "led_green", "-y"))
        P.append(ring("hp", 0.0035, 0.002, 0.001, "metal_chrome", (x - 0.03, fy - 0.0055, 0.05), "-y", 12))
        P.append(label("badge", (0.025, 0.005), (x, fy - 0.0055, 0.018), "label_white", "-y"))
    else:
        P.append(label("badge", (0.025, 0.005), (x, fy - 0.0055, 0.018), "label_white", "-y"))
    # rear: terminals
    by = D / 2
    P.append(rbox("term", (0.04, 0.004, 0.03), "plastic_black", (x, by - 0.0005, 0.05), bevel=0.001))
    P.append(boxes("term_clips", [((0.01, 0.006, 0.01), (x - 0.01, by + 0.004, 0.05)), ((0.01, 0.006, 0.01), (x + 0.01, by + 0.004, 0.05))], "label_red", bevel=0.0008))
    P += feet("foot", [(x - 0.04, -0.055), (x + 0.04, -0.055), (x - 0.04, 0.055), (x + 0.04, 0.055)], r=0.005, h=0.003, z=-0.003)
    return P


@prop("audio", "Pair of 2.0 desktop speakers (wood-effect vinyl, exposed drivers), cabinets 0.11x0.15x0.20 at x=+-0.16. Right one is the active (knob+LED). Cables link rear-to-rear.")
def speakers_pair_desk():
    P = _desk_speaker(-0.16, False) + _desk_speaker(0.16, True)
    P.append(cable("link", [(0.15, 0.075, 0.05), (0.12, 0.11, 0.03), (0.0, 0.13, 0.003), (-0.12, 0.11, 0.03), (-0.15, 0.075, 0.05)], 0.002))
    P.append(cable("pwr", [(0.17, 0.075, 0.05), (0.19, 0.10, 0.02), (0.22, 0.14, 0.003), (0.26, 0.17, 0.003)], 0.003))
    P.append(sticker("sticker", (0.03, 0.02), (-0.16 - 0.03, -0.075 - 0.0065, 0.11), "label_yellow", "-y", angle=0.3, peel=True))
    return assemble("electronics_speakers_pair_desk", P)


@prop("audio", "PA-style 12 inch 2-way speaker cab, carpet covered, corner protectors, side handles. 0.40x0.35x0.70. Front -Y. Top is flat (clutter ok).")
def speaker_big():
    W, D, H = 0.40, 0.35, 0.70
    P = []
    handle_cuts = [("box", (0.03, 0.13, 0.06), (sx * (W / 2 - 0.0), 0, 0.42)) for sx in (-1, 1)]
    P.append(hollow_cabinet("cab", (W, D, H), "carpet_black", (0, 0, 0), wall=0.018, bevel=0.008, extra_cuts=handle_cuts))
    fy = -D / 2
    P.append(baffle_with_holes("baffle", (W - 0.03, 0.012, H - 0.03), "plastic_dark", (0, fy - 0.0, H / 2),
                               [(0, 0.27 - H / 2, 0.14), (-0.12, 0.09 - H / 2, 0.031), (0.12, 0.09 - H / 2, 0.031)]))
    P.append(boxes("liner", [((W - 0.04, 0.003, H - 0.04), (0, D / 2 - 0.02, H / 2))], "foam_black", bevel=0))
    P += speaker_driver("woofer", 0.145, (0, fy - 0.005, 0.27), "-y", depth=0.075, segments=40, screws=8)
    # horn tweeter: flared rectangular mouth
    P.append(rbox("horn", (0.22, 0.05, 0.11), "plastic_black", (0, fy + 0.02, 0.56), bevel=0.004, taper=(0.35, 0.3), taper_axis="y"))
    P.append(rbox("horn_throat", (0.06, 0.03, 0.03), "label_black", (0, fy + 0.03, 0.56), bevel=0.002))
    P.append(rbox("horn_mouth", (0.19, 0.004, 0.08), "label_black", (0, fy - 0.0035, 0.56), bevel=0.001))
    # bass ports
    for sx in (-1, 1):
        P.append(ring("port", 0.035, 0.03, 0.005, "plastic_black", (sx * 0.12, fy - 0.006, 0.09), "-y", 28))
        P.append(cyl("port_in", 0.0302, 0.06, "label_black", (sx * 0.12, fy + 0.03, 0.09), "y", 24, bevel=0))
    P.append(label("badge", (0.06, 0.012), (0.0, fy - 0.0065, 0.12), "label_white", "-y"))
    # corner protectors: three plates per corner
    cp = []
    t, L = 0.003, 0.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz, z in ((-1, 0.0), (1, H)):
                cx, cy = sx * W / 2, sy * D / 2
                cp.append(((t, L, L), (cx - sx * t / 2 + sx * 0.0015, cy - sy * L / 2, z - sz * L / 2)))
                cp.append(((L, t, L), (cx - sx * L / 2, cy - sy * t / 2 + sy * 0.0015, z - sz * L / 2)))
                cp.append(((L, L, t), (cx - sx * L / 2, cy - sy * L / 2, z - sz * t / 2 + sz * 0.0015)))
    P.append(boxes("corners", cp, "metal_dark", bevel=0.0008))
    # recessed side handles (cup cut into the cabinet wall by hollow_cabinet; add cup liner, plate frame and bar)
    for sx in (-1, 1):
        P.append(boxes("handle_cup", [((0.004, 0.132, 0.062), (sx * (W / 2 - 0.017), 0, 0.42))], "plastic_dark", bevel=0))
        P.append(boxes("handle_frame", [((0.002, 0.15, 0.012), (sx * (W / 2 + 0.0005), 0, 0.42 + 0.036)), ((0.002, 0.15, 0.012), (sx * (W / 2 + 0.0005), 0, 0.42 - 0.036)),
                                         ((0.002, 0.012, 0.084), (sx * (W / 2 + 0.0005), 0.069, 0.42)), ((0.002, 0.012, 0.084), (sx * (W / 2 + 0.0005), -0.069, 0.42))], "metal_dark", bevel=0.0005))
        P.append(cyl("handle_bar", 0.006, 0.12, "metal_steel", (sx * (W / 2 - 0.006), 0, 0.442), "y", 12, bevel=0.001))
    # rear connector plate + cable
    by = D / 2
    P.append(rbox("conn_plate", (0.10, 0.003, 0.08), "metal_dark", (0, by + 0.0005, 0.25), bevel=0.0008))
    P += rca_ports("speakon", [(-0.02, 0.0), (0.02, 0.0)], (0, by + 0.002, 0.25), axis="y", role="plastic_dark", r=0.011)
    P.append(cable("cable", [(0.02, by + 0.006, 0.25), (0.03, by + 0.05, 0.20), (0.05, by + 0.08, 0.02), (0.08, by + 0.10, 0.003), (0.14, by + 0.12, 0.003)], 0.004))
    P += corner_feet(W, D, inset=0.05, r=0.02, h=0.012)
    # stickers/scuffs
    P.append(sticker("s1", (0.06, 0.04), (-0.09, fy - 0.006, 0.65), "label_red", "-y", angle=-0.2, peel=True))
    P.append(sticker("s2", (0.05, 0.05), (W / 2 + 0.0005, -0.08, 0.60), "label_white", "x", angle=0.5))
    P.append(sticker("s3", (0.08, 0.03), (0.08, fy - 0.006, 0.42), "label_yellow", "-y", angle=0.1))
    return assemble("electronics_speaker_big", P)


@prop("audio", "1210-style direct-drive turntable with slipmat + record on the platter, S-tonearm, pitch fader. 0.45x0.35, plinth top 0.085 m, arm top ~0.14 m. Front -Y.")
def turntable():
    W, D, Hp = 0.45, 0.35, 0.085
    P = []
    P.append(rbox("plinth", (W, D, Hp), "plastic_silver", (0, 0, 0.012), bevel=0.006, segs=3, origin="bottom"))
    P.append(rbox("plinth_base", (W - 0.01, D - 0.01, 0.014), "rubber_black", (0, 0, 0.0), bevel=0.003, origin="bottom"))
    top = Hp + 0.012
    P += corner_feet(W, D, inset=0.045, r=0.024, h=0.014, z=-0.014)
    # platter + strobe dots
    px, py = -0.065, 0.02
    P.append(cyl("platter", 0.165, 0.012, "metal_alu", (px, py, top), "z", 64, bevel=0.002, origin="bottom"))
    dots = []
    for k in range(60):
        a = 2 * math.pi * k / 60
        dots.append(((0.0035, 0.0035, 0.0035), (px + 0.165 * math.cos(a), py + 0.165 * math.sin(a), top + 0.004)))
    P.append(boxes("strobe_dots", dots, "plastic_dark", bevel=0))
    P.append(cyl("slipmat", 0.15, 0.002, "cotton_grey", (px, py, top + 0.012), "z", 56, bevel=0.0005, origin="bottom"))
    P.append(cyl("vinyl", 0.15, 0.0016, "vinyl_black", (px, py, top + 0.014), "z", 56, bevel=0.0004, origin="bottom"))
    for r in (0.142, 0.125, 0.105, 0.088, 0.068):
        P.append(ring("groove", r + 0.0012, r, 0.0003, "label_black", (px, py, top + 0.0156), "z", 56))
    P.append(cyl("label", 0.05, 0.0005, "label_red", (px, py, top + 0.0156), "z", 32, bevel=0, origin="bottom"))
    P.append(cyl("spindle", 0.0036, 0.016, "metal_chrome", (px, py, top + 0.012), "z", 12, bevel=0.0005, origin="bottom"))
    # tonearm: base, pivot, counterweight, S-arm, headshell, cartridge
    ax, ay = 0.165, 0.10
    P.append(cyl("arm_base", 0.032, 0.014, "plastic_dark", (ax, ay, top), "z", 32, bevel=0.002, origin="bottom"))
    P.append(ring("arm_ring", 0.034, 0.031, 0.004, "metal_alu", (ax, ay, top + 0.014), "z", 32))
    P.append(cyl("pivot", 0.012, 0.03, "metal_alu", (ax, ay, top + 0.014), "z", 24, bevel=0.0015, origin="bottom"))
    P.append(cyl("gimbal", 0.009, 0.03, "metal_alu", (ax, ay, top + 0.044), "x", 16, bevel=0.001))
    zarm = top + 0.044
    # arm goes from pivot forward-left to the record, counterweight behind
    P.append(cyl("cw", 0.016, 0.028, "metal_dark", (ax + 0.024, ay + 0.035, zarm), "y", 24, bevel=0.002))
    P.append(cyl("cw_stub", 0.004, 0.02, "metal_alu", (ax, ay + 0.02, zarm), "y", 10, bevel=0.0005))
    arm_pts = [(ax, ay, zarm), (ax - 0.01, ay - 0.04, zarm - 0.002), (ax - 0.05, ay - 0.10, zarm - 0.008), (ax - 0.11, ay - 0.14, zarm - 0.016), (ax - 0.16, ay - 0.145, zarm - 0.022)]
    P.append(cable("arm", arm_pts, 0.0045, "metal_alu", per_seg=6, segments=12))
    hx, hy, hz_ = ax - 0.16, ay - 0.145, zarm - 0.022
    P.append(rbox("headshell", (0.014, 0.03, 0.006), "metal_alu", (hx - 0.012, hy - 0.01, hz_ - 0.003), bevel=0.0012))
    P.append(rbox("cartridge", (0.012, 0.016, 0.007), "plastic_dark", (hx - 0.012, hy - 0.012, hz_ - 0.012), bevel=0.0008))
    P.append(rbox("finger", (0.003, 0.02, 0.004), "metal_alu", (hx - 0.02, hy - 0.002, hz_ - 0.004), bevel=0.0005))
    # arm rest + clip, anti-skate knob, arm lift lever
    P.append(cyl("rest", 0.004, 0.028, "plastic_dark", (ax - 0.06, ay - 0.075, top), "z", 10, bevel=0.0005, origin="bottom"))
    P.append(boxes("rest_clip", [((0.014, 0.006, 0.01), (ax - 0.06, ay - 0.075, top + 0.030))], "plastic_dark", bevel=0.001))
    P += knob("antiskate", 0.007, 0.006, "plastic_dark", (ax - 0.045, ay + 0.03, top + 0.003), "z", 16, skirt=False)
    P.append(boxes("lift", [((0.004, 0.02, 0.003), (ax - 0.035, ay - 0.035, top + 0.02))], "plastic_dark", bevel=0.0005))
    # pitch fader + scale labels
    P += fader("pitch", 0.10, (0.185, -0.08, top), "plastic_dark", cap=(0.014, 0.028, 0.012), slot_w=0.004)
    P.append(label("pitch_scale", (0.004, 0.10), (0.172, -0.08, top), "label_white", "z"))
    P.append(label("pitch_lbl", (0.025, 0.006), (0.185, -0.02, top), "label_white", "z"))
    P.append(led("pitch_led", 0.0015, (0.198, -0.03, top), "led_green", "z"))
    # start/stop, 33/45, power/strobe, target light
    P.append(button("startstop", (0.034, 0.034, 0.006), (-0.185, -0.135, top), "plastic_dark", "z", round_=True, segments=28))
    P.append(label("ss_lbl", (0.03, 0.004), (-0.185, -0.158, top), "label_white", "z"))
    P.append(button("b33", (0.016, 0.012, 0.004), (-0.135, -0.14, top), "plastic_dark", "z"))
    P.append(button("b45", (0.016, 0.012, 0.004), (-0.113, -0.14, top), "plastic_dark", "z"))
    P.append(led("led33", 0.0015, (-0.135, -0.128, top), "led_red", "z"))
    P.append(rbox("strobe_house", (0.03, 0.03, 0.02), "plastic_dark", (-0.195, 0.145, top), bevel=0.003, origin="bottom", taper=(0.9, 0.9)))
    P.append(label("strobe_lens", (0.012, 0.012), (-0.195, 0.145 - 0.0152, top + 0.01), "label_red", "-y"))
    P += knob("power", 0.012, 0.01, "plastic_dark", (-0.195, 0.145, top + 0.02), "z", 20, skirt=False)
    P.append(cyl("target_light", 0.007, 0.02, "plastic_dark", (0.045, -0.13, top), "z", 16, bevel=0.001, origin="bottom"))
    P.append(dome("target_lens", 0.005, 0.002, "glass_dark", (0.045, -0.13, top + 0.02), "z", 12, 3))
    # dust cover hinges at the back, labels on the front edge
    P.append(boxes("hinges", [((0.03, 0.012, 0.012), (-0.15, D / 2 - 0.004, top + 0.006)), ((0.03, 0.012, 0.012), (0.15, D / 2 - 0.004, top + 0.006))], "plastic_dark", bevel=0.001))
    P.append(label("front_lbl", (0.08, 0.008), (-0.15, -D / 2 - 0.0003, top - 0.02), "label_black", "-y"))
    P.append(label("front_lbl2", (0.03, 0.006), (0.17, -D / 2 - 0.0003, top - 0.02), "label_black", "-y"))
    # rear: RCA + ground + power
    P += rca_ports("rca", [(-0.02, 0), (0.02, 0)], (0.15, D / 2 + 0.0002, 0.05), axis="y")
    P.append(cable("pwr", [(0.10, D / 2, 0.05), (0.10, D / 2 + 0.04, 0.03), (0.12, D / 2 + 0.06, 0.003), (0.15, D / 2 + 0.08, 0.003)], 0.0035))
    P.append(cable("rca_cable", [(0.15, D / 2 + 0.004, 0.05), (0.16, D / 2 + 0.05, 0.03), (0.18, D / 2 + 0.07, 0.003), (0.22, D / 2 + 0.07, 0.003)], 0.0025))
    return assemble("electronics_turntable", P)


@prop("audio", "2-channel DJ battle mixer: EQ/gain knobs, two channel faders, crossfader, LED VU meters. 0.30x0.35x0.10. Front -Y (headphone jack on the front face).")
def dj_mixer():
    W, D, H = 0.30, 0.35, 0.095
    P = []
    P.append(rbox("body", (W, D, H - 0.003), "plastic_dark", (0, 0, 0.003), bevel=0.004, segs=2, origin="bottom", taper=(0.99, 0.985)))
    P.append(rbox("face", (W - 0.012, D - 0.012, 0.003), "plastic_silver", (0, 0, H - 0.003), bevel=0.001, origin="bottom"))
    top = H
    P += corner_feet(W, D, inset=0.03, r=0.01, h=0.004, z=-0.004)
    # channel strips
    for cx in (-0.05, 0.05):
        P += knob("gain", 0.0075, 0.012, "plastic_black", (cx, 0.135, top), "z", 16)
        for k, y in enumerate((0.095, 0.06, 0.025)):
            P += knob(f"eq{k}", 0.009, 0.014, "plastic_black", (cx, y, top), "z", 18)
            P.append(label("eq_lbl", (0.012, 0.004), (cx, y - 0.0145, top + 0.0003), "label_white", "z"))
        P.append(button("cue", (0.012, 0.008, 0.004), (cx, -0.012, top), "plastic_grey", "z"))
        P.append(led("cue_led", 0.0015, (cx, -0.022, top), "led_red", "z"))
        P += fader("chfader", 0.085, (cx, -0.082, top), "plastic_black", cap=(0.012, 0.022, 0.011), slot_w=0.0035)
        P.append(label("ch_scale", (0.003, 0.085), (cx + 0.012, -0.082, top + 0.0003), "label_white", "z"))
    # VU meters: two columns of 10 LEDs
    P.append(boxes("vu_bg", [((0.03, 0.105, 0.0015), (0, 0.075, top + 0.0005))], "label_black", bevel=0))
    for cx in (-0.007, 0.007):
        for k in range(10):
            role = "led_green" if k < 7 else "led_red"
            P.append(boxes(f"vu{k}", [((0.006, 0.004, 0.0015), (cx, 0.03 + k * 0.01, top + 0.0015))], role, bevel=0))
    P.append(label("vu_lbl", (0.03, 0.006), (0, 0.137, top + 0.0003), "label_white", "z"))
    # crossfader + curve switch
    P += fader("xfader", 0.085, (0, -0.148, top), "plastic_black", horizontal=True, pos=0.45, cap=(0.012, 0.022, 0.011), slot_w=0.0035)
    P.append(label("x_scale", (0.085, 0.003), (0, -0.136, top + 0.0003), "label_white", "z"))
    P.append(button("curve", (0.01, 0.006, 0.004), (0.11, -0.148, top), "plastic_grey", "z"))
    # master section (right) and mic/fx (left)
    for k, (y, r) in enumerate(((0.13, 0.011), (0.09, 0.009), (0.05, 0.009), (0.01, 0.009))):
        P += knob(f"mstr{k}", r, 0.014, "plastic_black", (0.12, y, top), "z", 18)
        P.append(label("m_lbl", (0.016, 0.004), (0.12, y - r - 0.006, top + 0.0003), "label_white", "z"))
    for k, y in enumerate((0.13, 0.09)):
        P += knob(f"mic{k}", 0.008, 0.012, "plastic_black", (-0.12, y, top), "z", 16)
    P.append(button("mic_sw", (0.008, 0.014, 0.005), (-0.12, 0.05, top), "plastic_grey", "z"))
    P.append(button("fx1", (0.012, 0.008, 0.004), (-0.12, 0.015, top), "plastic_grey", "z"))
    P.append(button("fx2", (0.012, 0.008, 0.004), (-0.12, -0.0, top), "plastic_grey", "z"))
    P.append(led("pwr_led", 0.0015, (-0.12, -0.03, top), "led_green", "z"))
    P.append(label("logo", (0.035, 0.007), (-0.10, -0.148, top + 0.0003), "label_white", "z"))
    # front face: headphone jack + mic jack; rear: RCA pairs, ground post, power
    fy = -D / 2
    P += rca_ports("hp", [(0.09, 0.0)], (0, fy - 0.0002, 0.05), axis="-y", role="metal_chrome", r=0.0045)
    P += rca_ports("mic", [(-0.09, 0.0)], (0, fy - 0.0002, 0.05), axis="-y", role="metal_chrome", r=0.0045)
    by = D / 2
    P.append(rbox("rear_plate", (0.22, 0.002, 0.045), "plastic_black", (0, by + 0.0003, 0.05), bevel=0.0006))
    pos = []
    for i in range(5):
        pos += [(-0.08 + i * 0.03, 0.012), (-0.08 + i * 0.03, -0.012)]
    P += rca_ports("rca_r", [p for p in pos if p[1] > 0], (0, by + 0.0005, 0.05), axis="y", role="plastic_red", r=0.0045)
    P += rca_ports("rca_w", [p for p in pos if p[1] < 0], (0, by + 0.0005, 0.05), axis="y", role="plastic_white", r=0.0045)
    P.append(cyl("gnd", 0.003, 0.012, "metal_brass", (0.095, by + 0.006, 0.05), "y", 8, bevel=0.0005))
    P.append(cable("pwr", [(0.0, by + 0.001, 0.02), (0.01, by + 0.03, 0.015), (0.03, by + 0.05, 0.003), (0.06, by + 0.08, 0.003)], 0.003))
    return assemble("electronics_dj_mixer", P)


@prop("audio", "25-key MIDI controller with a 4x4 pad grid. Pads are 16 child objects `pad_r{row}c{col}` (role pad_rubber) so Unity can light them individually. 0.32x0.20, 0.045 at the back. Front -Y.")
def midi_controller():
    W, D = 0.32, 0.20
    P = []
    P.append(wedge("body", (W, D, 0.030), "plastic_dark", (0, 0, 0), back_h=0.040, bevel=0.004, segs=3))
    def topz(y):
        return 0.030 + (0.040 - 0.030) * (y + D / 2) / D
    # mini keys: 15 white, 10 black
    kw, kp, kl = 0.0135, 0.0145, 0.068
    kx0 = -W / 2 + 0.065
    ky = -D / 2 + 0.012 + kl / 2
    zk = topz(ky) - 0.003
    whites = [(kx0 + i * kp, ky, kw, kl - 0.002, 0.009, zk) for i in range(15)]
    P.append(keycaps("white_keys", whites, "plastic_white", bevel=0.0008, taper=(0.97, 0.98), dish=False))
    blacks = []
    for i in (0, 1, 3, 4, 5, 7, 8, 10, 11, 12):
        blacks.append((kx0 + (i + 0.5) * kp, ky + 0.016, 0.0085, kl * 0.55, 0.014, zk))
    P.append(keycaps("black_keys", blacks, "plastic_black", bevel=0.0008, taper=(0.85, 0.9), dish=False))
    P.append(boxes("key_bed", [((15 * kp + 0.004, kl + 0.004, 0.002), (kx0 + 7 * kp, ky, zk))], "label_black", bevel=0))
    # pitch / mod wheels in slots (left of keys)
    for k, x in enumerate((-W / 2 + 0.018, -W / 2 + 0.040)):
        zw = topz(ky)
        P.append(boxes("wheel_slot", [((0.013, 0.04, 0.012), (x, ky - 0.01, zw - 0.006))], "label_black", bevel=0))
        P.append(cyl("wheel", 0.019, 0.010, "rubber_grey", (x, ky - 0.01, zw - 0.012), "x", 28, bevel=0.0012))
    # knobs row (back left) + small buttons + display label
    for k in range(8):
        x = -W / 2 + 0.02 + k * 0.021
        y = D / 2 - 0.03
        P += knob(f"knob{k}", 0.0065, 0.012, "plastic_black", (x, y, topz(y)), "z", 16, skirt=False)
    y2 = D / 2 - 0.058
    for k in range(4):
        P.append(button(f"tbtn{k}", (0.012, 0.007, 0.003), (-W / 2 + 0.02 + k * 0.016, y2, topz(y2)), "plastic_grey", "z"))
    P.append(led("led_a", 0.0014, (-W / 2 + 0.09, y2, topz(y2)), "led_green", "z"))
    P.append(label("disp", (0.03, 0.012), (-W / 2 + 0.12, y2, topz(y2) + 0.0003), "label_black", "z"))
    P.append(label("logo", (0.03, 0.006), (W / 2 - 0.03, -D / 2 + 0.012, topz(-D / 2 + 0.012) + 0.0003), "label_white", "z"))
    P.append(button("oct_m", (0.009, 0.007, 0.003), (-W / 2 + 0.014, ky + 0.03, topz(ky + 0.03)), "plastic_grey", "z"))
    P.append(button("oct_p", (0.009, 0.007, 0.003), (-W / 2 + 0.028, ky + 0.03, topz(ky + 0.03)), "plastic_grey", "z"))
    # pad grid 4x4 (children)
    pads = {}
    px0, py0, pp, ps = W / 2 - 0.115, D / 2 - 0.105, 0.026, 0.022
    P.append(boxes("pad_bed", [((4 * pp + 0.004, 4 * pp + 0.004, 0.002), (px0 + 1.5 * pp, py0 + 1.5 * pp, topz(py0 + 1.5 * pp) - 0.0005))], "label_black", bevel=0))
    for r in range(4):
        for c in range(4):
            x, y = px0 + c * pp, py0 + r * pp
            pads[f"pad_r{r}c{c}"] = [boxes("pad", [((ps, ps, 0.005), (x, y, topz(y) + 0.0025), (0.9, 0.9))], "pad_rubber", bevel=0.0015, segs=2)]
    # rear: USB + DC + sustain jack, cable; feet
    P.append(port_slots("usb", [(0.012, 0.011, (0, 0))], (0.0, D / 2 + 0.0002, 0.02), axis="y", depth=0.008))
    P += rca_ports("sus", [(0.03, 0)], (0, D / 2 + 0.0002, 0.02), axis="y", role="plastic_dark", r=0.004)
    P.append(cable("usb_cable", [(0.0, D / 2 + 0.002, 0.02), (0.0, D / 2 + 0.03, 0.015), (0.02, D / 2 + 0.06, 0.003), (0.06, D / 2 + 0.08, 0.003)], 0.0022))
    P += corner_feet(W, D, inset=0.02, r=0.007, h=0.003, z=-0.003)
    return assemble("electronics_midi_controller", P, pads)


@prop("audio", "2-in/2-out USB audio interface, red metal box, combo jacks + halo gain knobs on the front. 0.18x0.14x0.05. Front -Y.")
def audio_interface():
    W, D, H = 0.18, 0.14, 0.048
    P = []
    P.append(rbox("body", (W, D, H), "metal_red", (0, 0, 0.004), bevel=0.006, segs=3, origin="bottom"))
    fy = -D / 2
    P.append(rbox("front", (W - 0.004, 0.004, H - 0.006), "plastic_dark", (0, fy - 0.0015, H / 2 + 0.004), bevel=0.0015))
    ff = fy - 0.0035
    zc = H / 2 + 0.004
    for k, x in enumerate((-0.062, -0.028)):
        P.append(ring("combo", 0.012, 0.0095, 0.003, "metal_chrome", (x, ff, zc + 0.006), "-y", 24))
        P.append(cyl("combo_in", 0.0096, 0.004, "label_black", (x, ff + 0.001, zc + 0.006), "y", 24, bevel=0))
        P.append(grille("combo_pins", 0.012, 0.012, (x, ff - 0.0005, zc + 0.006), 2, 2, (0.0025, 0.0025), depth=0.003, axis="-y", round_holes=True))
        P.append(ring("halo", 0.0085, 0.0065, 0.0015, "led_green", (x, ff, zc - 0.012), "-y", 20))
        P += knob("gain", 0.006, 0.009, "plastic_dark", (x, ff - 0.005, zc - 0.012), "-y", 16, skirt=False)
        P.append(button("inst", (0.006, 0.004, 0.002), (x + 0.015, ff, zc + 0.014), "plastic_grey", "-y"))
        P.append(led("inst_led", 0.001, (x + 0.015, ff, zc + 0.008), "led_red", "-y"))
    P += knob("monitor", 0.016, 0.012, "plastic_dark", (0.03, ff - 0.006, zc), "-y", 28)
    P.append(label("mon_scale", (0.036, 0.003), (0.03, ff - 0.0002, zc - 0.020), "label_white", "-y"))
    P += knob("hp_vol", 0.0065, 0.009, "plastic_dark", (0.07, ff - 0.005, zc + 0.008), "-y", 16, skirt=False)
    P.append(ring("hp_jack", 0.0045, 0.0032, 0.002, "metal_chrome", (0.07, ff, zc - 0.012), "-y", 16))
    P.append(button("p48", (0.008, 0.005, 0.002), (0.0, ff, zc + 0.014), "plastic_grey", "-y"))
    P.append(led("p48_led", 0.001, (0.0, ff, zc + 0.007), "led_red", "-y"))
    P.append(label("logo", (0.05, 0.012), (0.03, 0.0, H + 0.0043), "label_white", "z"))
    P.append(sticker("sticker", (0.025, 0.018), (-0.055, 0.03, H + 0.004), "label_white", "z", angle=0.4, peel=True))
    # rear
    by = D / 2
    P.append(rbox("rear", (W - 0.004, 0.003, H - 0.006), "plastic_dark", (0, by + 0.001, zc), bevel=0.0015))
    P += rca_ports("outs", [(-0.03, 0.0), (-0.015, 0.0), (0.03, 0.0), (0.045, 0.0)], (0, by + 0.0025, zc), axis="y", role="metal_chrome", r=0.0045)
    P.append(port_slots("usb", [(0.012, 0.011, (0.0, 0.0))], (0.065, by + 0.0025, zc), axis="y", depth=0.008))
    P.append(cable("usb_cable", [(-0.065, by + 0.003, zc), (-0.07, by + 0.03, 0.02), (-0.06, by + 0.06, 0.003), (-0.03, by + 0.09, 0.003)], 0.0022))
    P += corner_feet(W, D, inset=0.015, r=0.006, h=0.004)
    return assemble("electronics_audio_interface", P)


@prop("audio", "DJ headphones (closed cups, coiled cable) hanging on a hook stand. Base r 0.06, 0.29 tall. Cups face +-X; front -Y.")
def headphones_on_stand():
    P = []
    P.append(cyl("base", 0.06, 0.012, "metal_dark", (0, 0.02, 0), "z", 40, bevel=0.003, r_top=0.055, origin="bottom"))
    P.append(cyl("pole", 0.006, 0.23, "metal_dark", (0, 0.02, 0.012), "z", 16, bevel=0.001, origin="bottom"))
    # hook curling forward (-y) at the top
    hook_c = (0, -0.01, 0.242)
    P.append(torus("hook", 0.03, 0.006, "metal_dark", hook_c, "x", 24, 10, arc=(math.pi, 2 * math.pi)))
    P.append(dome("hook_tip", 0.006, 0.004, "metal_dark", (0, -0.04, 0.242), "z", 10, 3))
    # headband: partial torus in the XZ plane hanging from the hook (top inner surface rests on the hook)
    R, hb_c = 0.085, (0, -0.025, 0.248 - 0.085)
    P.append(torus("band", R, 0.0055, "plastic_black", hb_c, "y", 36, 10, arc=(math.radians(15), math.radians(165))))
    P.append(torus("band_pad", R + 0.0015, 0.011, "leather_black", hb_c, "y", 20, 12, arc=(math.radians(60), math.radians(120))))
    # cups with yokes and pads at the band ends
    for sx in (-1, 1):
        ex = hb_c[0] + sx * R * math.cos(math.radians(15))
        ez = hb_c[2] + R * math.sin(math.radians(15))
        P.append(rbox("slider", (0.008, 0.012, 0.045), "plastic_black", (ex, hb_c[1], ez - 0.012), bevel=0.002))
        P.append(cyl("yoke_pivot", 0.007, 0.012, "metal_alu", (ex, hb_c[1], ez - 0.034), "x", 14, bevel=0.001))
        cx, cz = hb_c[0] + sx * 0.078, ez - 0.062
        P.append(torus("yoke", 0.042, 0.004, "plastic_black", (cx, hb_c[1], cz), "x", 28, 8, arc=(math.radians(20), math.radians(160))))
        P.append(cyl("cup", 0.044, 0.028, "plastic_black", (cx + sx * 0.004, hb_c[1], cz), "x", 32, bevel=0.004, r_top=0.038))
        P.append(cyl("cup_badge", 0.022, 0.002, "metal_alu", (cx + sx * 0.019, hb_c[1], cz), "x", 24, bevel=0.0005))
        P.append(torus("pad", 0.035, 0.013, "leather_black", (cx - sx * 0.012, hb_c[1], cz), "x", 32, 10))
        P.append(cyl("driver_cloth", 0.025, 0.002, "foam_black", (cx - sx * 0.012, hb_c[1], cz), "x", 20, bevel=0))
    # coiled cable from the left cup down to the base, then a tail
    cx_l, cz_l = hb_c[0] - 0.078, hb_c[2] + R * math.sin(math.radians(15)) - 0.062
    coil = helix((cx_l - 0.01, hb_c[1] + 0.01, cz_l - 0.05), 0.009, 0.009, 9, Vector((0.05, 0.1, -1)), per_turn=12, start=Vector((1, 0, 0)))
    pts = [(cx_l - 0.004, hb_c[1], cz_l - 0.04), (cx_l - 0.008, hb_c[1] + 0.004, cz_l - 0.046)] + coil + [(coil[-1][0] - 0.01, coil[-1][1] + 0.02, 0.01), (-0.08, 0.06, 0.003), (-0.12, 0.09, 0.003)]
    P.append(cable("coil", pts, 0.0022, "rubber_black", per_seg=2, segments=8))
    P.append(cyl("plug", 0.004, 0.02, "metal_chrome", (-0.13, 0.095, 0.004), "x", 10, bevel=0.0005))
    return assemble("electronics_headphones_on_stand", P)


# =====================================================================================================  small devices

def _phone_body(name_prefix, center, upright=False):
    """Smartphone body 0.07 x 0.145 x 0.008 built lying face-up (screen +Z, home button toward -Y). Returns (parts, screen)."""
    W, L, T = 0.07, 0.145, 0.008
    cx, cy, cz = center
    P = []
    P.append(rbox("body", (W, L, T), "plastic_black", (cx, cy, cz), bevel=0.0035, segs=3, origin="bottom"))
    P.append(rbox("glass", (W - 0.004, L - 0.004, 0.0008), "glass_dark", (cx, cy, cz + T + 0.0004), bevel=0.0003))
    P.append(cyl("home", 0.0055, 0.0006, "plastic_dark", (cx, cy - 0.063, cz + T + 0.0008), "z", 20, bevel=0.0002, origin="bottom"))
    P.append(ring("home_ring", 0.0062, 0.0055, 0.0005, "metal_chrome", (cx, cy - 0.063, cz + T + 0.0008), "z", 20))
    P.append(port_slots("earpiece", [(0.012, 0.0015, (0, 0))], (cx, cy + 0.066, cz + T + 0.0009), axis="z", depth=0.001))
    P.append(dome("cam", 0.0015, 0.0004, "glass_dark", (cx - 0.012, cy + 0.066, cz + T + 0.0008), "z", 10, 2))
    # side buttons + bottom port
    P.append(boxes("vol", [((0.001, 0.012, 0.003), (cx - W / 2 - 0.0003, cy + 0.03, cz + T / 2)), ((0.001, 0.012, 0.003), (cx - W / 2 - 0.0003, cy + 0.015, cz + T / 2))], "metal_alu", bevel=0.0003))
    P.append(boxes("pwr", [((0.001, 0.012, 0.003), (cx + W / 2 + 0.0003, cy + 0.03, cz + T / 2))], "metal_alu", bevel=0.0003))
    P.append(port_slots("usb", [(0.009, 0.003, (0, 0)), (0.012, 0.0015, (-0.02, 0)), (0.012, 0.0015, (0.02, 0))], (cx, cy - L / 2 + 0.0002, cz + T / 2), axis="-y", depth=0.004))
    screen = screen_plane(W - 0.008, L - 0.034, (cx, cy + 0.0025, cz + T + 0.0009), "z")
    return P, screen


@prop("phone", "Smartphone lying face-up (screen +Z, home button toward -Y). 0.07 x 0.145 x 0.009. Screen child `screen`.")
def smartphone_flat():
    P, screen = _phone_body("phone", (0, 0, 0))
    return assemble("electronics_smartphone_flat", P, {"screen": [screen]})


@prop("phone", "Smartphone standing in a charging dock, leaning back 15 deg, screen facing -Y. Dock 0.085 x 0.075, cable out the back.")
def phone_on_charger():
    P = []
    P.append(rbox("dock", (0.085, 0.075, 0.016), "plastic_white", (0, 0.0, 0), bevel=0.004, segs=3, origin="bottom", taper=(0.95, 0.9)))
    P.append(boxes("dock_pad", [((0.072, 0.014, 0.002), (0, -0.012, 0.0165))], "rubber_grey", bevel=0.0005))
    P.append(led("dock_led", 0.0015, (0.03, -0.075 / 2 * 0.95 - 0.0003, 0.008), "led_green", "-y"))
    # back rest leaning 15 deg
    rest = [rbox("rest", (0.06, 0.008, 0.075), "plastic_white", (0, 0.004, 0.012), bevel=0.003, origin="bottom", taper=(0.8, 1.0))]
    rotate_parts(rest, (math.radians(-15), 0, 0), (0, 0.0, 0.012))
    P += rest
    # phone: built flat then stood upright (face -Y) and leaned back
    body, screen = _phone_body("phone", (0, 0, 0))
    rotate_parts(body + [screen], (math.radians(90), 0, 0), (0, 0, 0))          # face up -> face -Y, length along +Z
    rotate_parts(body + [screen], (0, 0, 0), (0, 0, 0))
    # after the rotation the phone spans z in [-L/2..L/2]*; lift it so its bottom edge sits in the dock slot
    for o in body + [screen]:
        o.location += Vector((0, -0.010, 0.0725 + 0.012))
    rotate_parts(body + [screen], (math.radians(-15), 0, 0), (0, -0.010, 0.012))
    P += body
    P.append(cable("cable", [(0, 0.075 / 2 * 0.9, 0.008), (0, 0.06, 0.006), (0.02, 0.10, 0.003), (0.05, 0.13, 0.003)], 0.002))
    return assemble("electronics_phone_on_charger", P, {"screen": [screen]})


@prop("console", "Boxy 2000s games console lying flat (0.30 x 0.18 x 0.078) with a wired controller lying in front (-Y). Overall footprint 0.30 x 0.35.")
def games_console():
    W, D, H = 0.30, 0.18, 0.075
    cy = 0.085
    P = []
    P.append(rbox("body", (W, D, H), "plastic_black", (0, cy, 0.003), bevel=0.005, segs=3, origin="bottom", taper=(0.98, 0.98)))
    P.append(rbox("skirt", (W - 0.006, D - 0.006, 0.004), "plastic_dark", (0, cy, 0), bevel=0.001, origin="bottom"))
    top = H + 0.003
    # disc tray lid (circle label + lid seam), vents, logo
    P.append(rbox("lid", (0.145, 0.15, 0.0025), "plastic_dark", (-0.06, cy, top + 0.0005), bevel=0.0008))
    P.append(ring("lid_ring", 0.055, 0.052, 0.0008, "plastic_black", (-0.06, cy, top + 0.0033), "z", 40))
    P.append(label("lid_logo", (0.03, 0.03), (-0.06, cy, top + 0.0033), "label_white", "z"))
    P.append(grille("top_vent", 0.09, 0.14, (0.09, cy, top - 0.0002), 1, 14, (0.08, 0.003), depth=0.003, axis="z"))
    P.append(label("badge", (0.05, 0.008), (0.09, cy - 0.075, top + 0.0003), "label_blue", "z"))
    # front: power + eject, LEDs, controller ports, memory card slots, USB
    fy = cy - D / 2
    P.append(button("power", (0.014, 0.008, 0.003), (0.10, fy, 0.05), "plastic_dark", "-y"))
    P.append(led("led_pwr", 0.0015, (0.10, fy, 0.038), "led_green", "-y"))
    P.append(button("eject", (0.012, 0.008, 0.003), (-0.11, fy, 0.05), "plastic_dark", "-y"))
    P.append(led("led_disc", 0.0015, (-0.11, fy, 0.038), "led_red", "-y"))
    P.append(rbox("port_bay", (0.12, 0.003, 0.03), "plastic_dark", (-0.01, fy - 0.0005, 0.03), bevel=0.0008))
    P.append(port_slots("mem", [(0.03, 0.004, (-0.03, 0.009)), (0.03, 0.004, (0.03, 0.009))], (-0.01, fy - 0.002, 0.03), axis="-y", depth=0.006))
    P.append(port_slots("ctrl", [(0.02, 0.012, (-0.03, -0.006)), (0.02, 0.012, (0.03, -0.006))], (-0.01, fy - 0.002, 0.03), axis="-y", depth=0.008))
    P.append(port_slots("usb", [(0.012, 0.0045, (0.0, -0.006)), (0.012, 0.0045, (0.0, 0.009))], (-0.01, fy - 0.002, 0.03), axis="-y", depth=0.008))
    # sides + rear
    P.append(grille("side_vent", 0.12, 0.04, (W / 2 + 0.0002, cy, 0.04), 12, 1, (0.004, 0.03), depth=0.004, axis="x"))
    by = cy + D / 2
    P.append(port_slots("av", [(0.018, 0.009, (0.08, 0.0)), (0.02, 0.014, (-0.08, 0.0)), (0.014, 0.012, (0.0, 0.0))], (0, by + 0.0002, 0.04), axis="y", depth=0.008))
    P.append(cable("pwr_cable", [(-0.08, by + 0.001, 0.04), (-0.09, by + 0.03, 0.02), (-0.10, by + 0.05, 0.003), (-0.13, by + 0.07, 0.003)], 0.003))
    P.append(cable("av_cable", [(0.08, by + 0.001, 0.04), (0.09, by + 0.03, 0.03), (0.12, by + 0.05, 0.003), (0.15, by + 0.06, 0.003)], 0.0025))
    P += feet("foot", [(-0.12, cy - 0.07), (0.12, cy - 0.07), (-0.12, cy + 0.07), (0.12, cy + 0.07)], r=0.008, h=0.003, z=-0.003)
    P.append(sticker("sticker", (0.03, 0.02), (0.10, cy + 0.05, top + 0.0003), "label_yellow", "z", angle=0.4, peel=True))
    # controller lying in front, slightly rotated
    C = []
    ccy = -0.095
    C.append(rbox("c_body", (0.105, 0.052, 0.022), "plastic_dark", (0, ccy, 0), bevel=0.006, segs=3, origin="bottom", taper=(0.92, 0.85)))
    for sx in (-1, 1):
        grip = [cyl("grip", 0.016, 0.065, "plastic_dark", (sx * 0.042, ccy - 0.03, 0.013), "y", 20, bevel=0.004, r_top=0.013),
                dome("grip_end", 0.013, 0.008, "plastic_dark", (sx * 0.042, ccy - 0.0625, 0.013), "-y", 20, 4),
                dome("grip_top", 0.016, 0.006, "plastic_dark", (sx * 0.042, ccy + 0.0025, 0.013), "y", 20, 4)]
        rotate_parts(grip, (0, 0, math.radians(sx * -16)), (sx * 0.042, ccy + 0.0, 0.013))
        C += grip
    # d-pad (left), 4 buttons (right), two sticks, start/select, shoulders
    C.append(boxes("dpad", [((0.02, 0.006, 0.004), (-0.035, ccy + 0.004, 0.023)), ((0.006, 0.02, 0.004), (-0.035, ccy + 0.004, 0.023))], "plastic_black", bevel=0.0008))
    for (dx, dy, role) in [(0.0, 0.009, "plastic_green"), (0.0, -0.009, "plastic_blue"), (-0.009, 0.0, "plastic_red"), (0.009, 0.0, "plastic_white")]:
        C.append(cyl("btn", 0.0035, 0.004, "plastic_" + role.split("_")[1] if role != "plastic_white" else "plastic_white", (0.035 + dx, ccy + 0.004 + dy, 0.022), "z", 12, bevel=0.0006, origin="bottom"))
    for sx in (-1, 1):
        C.append(cyl("stick", 0.0045, 0.010, "plastic_black", (sx * 0.016, ccy - 0.012, 0.022), "z", 12, bevel=0.0005, origin="bottom"))
        C.append(dome("stick_cap", 0.0075, 0.003, "rubber_black", (sx * 0.016, ccy - 0.012, 0.030), "z", 16, 4))
    C.append(boxes("ss", [((0.008, 0.004, 0.0025), (-0.008, ccy + 0.006, 0.0225)), ((0.008, 0.004, 0.0025), (0.008, ccy + 0.006, 0.0225))], "plastic_grey", bevel=0.0005))
    C.append(boxes("shoulders", [((0.022, 0.008, 0.006), (-0.034, ccy + 0.028, 0.012)), ((0.022, 0.008, 0.006), (0.034, ccy + 0.028, 0.012)),
                                  ((0.022, 0.006, 0.005), (-0.034, ccy + 0.03, 0.006)), ((0.022, 0.006, 0.005), (0.034, ccy + 0.03, 0.006))], "plastic_dark", bevel=0.001))
    rotate_parts(C, (0, 0, math.radians(14)), (0, ccy, 0))
    P += C
    # controller cable to the left controller port
    P.append(cable("c_cable", [(-0.005, ccy + 0.03, 0.012), (-0.01, ccy + 0.06, 0.006), (-0.06, ccy + 0.09, 0.003), (-0.09, fy - 0.03, 0.003), (-0.05, fy - 0.01, 0.015), (-0.04, fy - 0.002, 0.024)], 0.0025))
    return assemble("electronics_games_console", P)


@prop("network", "Home ADSL router with two hinged antennas and a row of LEDs on the front. 0.20 x 0.14 x 0.033 (antennas to ~0.19). Front -Y, ports at the back.")
def router():
    W, D, H = 0.20, 0.14, 0.032
    P = []
    P.append(rbox("body", (W, D, H), "plastic_white", (0, 0, 0.003), bevel=0.006, segs=3, origin="bottom", taper=(0.96, 0.94)))
    P.append(rbox("skirt", (W - 0.004, D - 0.004, 0.0035), "plastic_grey", (0, 0, 0), bevel=0.001, origin="bottom"))
    top = H + 0.003
    P.append(rbox("top_inset", (W - 0.03, D - 0.05, 0.0015), "plastic_grey", (0, 0.0, top), bevel=0.0005, origin="bottom"))
    P.append(grille("top_vent", W - 0.05, 0.03, (0, 0.03, top + 0.0015), 14, 2, (0.006, 0.01), depth=0.003, axis="z"))
    P.append(sticker("sticker", (0.05, 0.03), (-0.04, -0.03, top + 0.0015), "label_white", "z", angle=0.0))
    P.append(label("logo", (0.03, 0.008), (0.05, -0.035, top + 0.0018), "label_blue", "z"))
    fy = -D / 2 * 0.97
    for k in range(8):
        role = "led_red" if k == 5 else "led_green"
        P.append(led(f"led{k}", 0.0014, (-0.06 + k * 0.014, fy - 0.0006, 0.02), role, "-y"))
        P.append(label(f"lbl{k}", (0.006, 0.0025), (-0.06 + k * 0.014, fy - 0.0005, 0.013), "label_black", "-y"))
    P.append(button("wps", (0.01, 0.006, 0.002), (0.07, fy - 0.0005, 0.02), "plastic_grey", "-y"))
    # rear: 4 LAN (yellow), WAN (blue), DSL, power, switch
    by = D / 2 * 0.97
    P.append(rbox("rear_panel", (0.15, 0.002, 0.02), "plastic_grey", (0, by, 0.018), bevel=0.0005))
    lan = [(0.016, 0.013, (-0.06 + k * 0.02, 0)) for k in range(4)]
    P.append(port_slots("lan", lan, (0, by + 0.001, 0.018), axis="y", depth=0.012))
    for k in range(4):
        P.append(boxes(f"lan_in{k}", [((0.013, 0.004, 0.004), (0.06 - k * 0.02, by - 0.004, 0.021))], "label_yellow", bevel=0))
    P.append(port_slots("wan", [(0.016, 0.013, (0.03, 0))], (0, by + 0.001, 0.018), axis="y", depth=0.012))
    P.append(boxes("wan_in", [((0.013, 0.004, 0.004), (-0.03, by - 0.004, 0.021))], "label_blue", bevel=0))
    P.append(port_slots("dsl", [(0.011, 0.009, (0.05, 0))], (0, by + 0.001, 0.018), axis="y", depth=0.01))
    P.append(ring("dc", 0.004, 0.0015, 0.003, "metal_dark", (-0.07, by + 0.0015, 0.018), "y", 12))
    P.append(button("pwr_sw", (0.006, 0.006, 0.003), (-0.08, by + 0.0005, 0.03), "plastic_dark", "y"))
    P.append(cable("dc_cable", [(-0.07, by + 0.003, 0.018), (-0.07, by + 0.03, 0.012), (-0.06, by + 0.06, 0.003), (-0.03, by + 0.09, 0.003)], 0.0018))
    P.append(cable("eth_cable", [(0.06, by + 0.004, 0.018), (0.06, by + 0.03, 0.012), (0.08, by + 0.06, 0.003), (0.12, by + 0.08, 0.003)], 0.0025, "label_yellow"))
    # antennas: knuckle on the back-top corners, angled
    for sx in (-1, 1):
        kx, ky, kz = sx * 0.08, D / 2 - 0.012, top
        P.append(cyl("knuckle", 0.006, 0.012, "plastic_black", (kx, ky, kz + 0.006), "x", 14, bevel=0.0012))
        ant = [cyl("ant_base", 0.0055, 0.02, "plastic_black", (kx, ky, kz + 0.012), "z", 14, bevel=0.0008, origin="bottom"),
               cyl("ant", 0.0045, 0.13, "plastic_black", (kx, ky, kz + 0.032), "z", 14, bevel=0.0012, r_top=0.004, origin="bottom"),
               dome("ant_tip", 0.004, 0.003, "plastic_black", (kx, ky, kz + 0.162), "z", 12, 3)]
        rotate_parts(ant, (math.radians(-20), math.radians(sx * 18), 0), (kx, ky, kz + 0.006))
        P += ant
    P += corner_feet(W, D, inset=0.02, r=0.006, h=0.003, z=-0.003)
    return assemble("electronics_router", P)


@prop("clock", "Digital bedside alarm clock, sloped front with red LED digits (7:48) as `led_red` geometry. 0.14 x 0.075 x 0.06. Front -Y, cable out the back.")
def alarm_clock():
    W, D, Hf, Hb = 0.14, 0.075, 0.045, 0.062
    # body: box whose front face leans back (front-top edge moved back)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    lean = 0.022
    for v in bm.verts:
        v.co.x *= W; v.co.y *= D
        v.co.z = (Hb if v.co.y > 0 else Hf) if v.co.z > 0 else 0.0
        if v.co.y < 0 and v.co.z > 0:
            v.co.y += lean
    _bm_bevel(bm, 0.004, 3)
    body = _make(bm, "body", "plastic_black", smooth=True)
    P = [body]
    # sloped front face frame: normal of the slope
    ang = math.atan2(lean, Hf)                      # slope angle from vertical
    fy, fz = -D / 2, 0.0
    # display window centre on the slope (at half height)
    cy = fy + lean * 0.5
    cz = Hf * 0.5
    disp = [label("display", (0.10, 0.03), (0, cy - 0.0006, cz), "glass_dark", "-y"),
            seven_seg("digits", "7:48", (0, cy - 0.0012, cz + 0.001), 0.02, "led_red", "-y"),
            boxes("alarm_dot", [((0.0015, 0.0015, 0.0012), (-0.044, cy - 0.0012, cz - 0.008))], "led_red", bevel=0),
            label("pm", (0.006, 0.0025), (-0.044, cy - 0.0012, cz + 0.008), "label_white", "-y")]
    rotate_parts(disp, (-ang, 0, 0), (0, cy, cz))
    P += disp
    # top: snooze bar, three small buttons, alarm slider; sides: dimmer switch
    P.append(rbox("snooze", (0.07, 0.022, 0.004), "plastic_grey", (-0.02, 0.012, Hb - 0.001), bevel=0.0015, origin="bottom", taper=(0.95, 0.9)))
    for k in range(3):
        P.append(button(f"btn{k}", (0.008, 0.006, 0.003), (0.04 + k * 0.012, 0.012, Hb), "plastic_grey", "z"))
    P.append(boxes("slider_slot", [((0.02, 0.004, 0.003), (0.05, 0.03, Hb - 0.0005))], "label_black", bevel=0))
    P.append(boxes("slider", [((0.006, 0.0035, 0.004), (0.046, 0.03, Hb + 0.001))], "plastic_grey", bevel=0.0005))
    P.append(label("top_lbl", (0.03, 0.005), (-0.02, 0.03, Hb + 0.0003), "label_white", "z"))
    P.append(boxes("dimmer", [((0.003, 0.012, 0.005), (W / 2 + 0.0005, 0.0, 0.03))], "plastic_grey", bevel=0.0006))
    # back: speaker holes + cable; bottom feet
    P.append(grille("spk", 0.03, 0.03, (-0.04, D / 2 + 0.0002, 0.03), 4, 4, (0.003, 0.003), depth=0.003, axis="y", round_holes=True))
    P.append(cable("cable", [(0.04, D / 2, 0.012), (0.045, D / 2 + 0.03, 0.008), (0.06, D / 2 + 0.06, 0.003), (0.10, D / 2 + 0.08, 0.003)], 0.002))
    P += corner_feet(W, D, inset=0.015, r=0.005, h=0.002)
    return assemble("electronics_alarm_clock", P)


@prop("audio", "80s/90s boombox radio-cassette: two speakers, tape deck window, piano keys, tuning dial, carry handle, aerial. 0.45 x 0.20 x 0.25 (handle). Front -Y.")
def radio_cassette():
    W, D, H = 0.45, 0.17, 0.21
    P = []
    P.append(rbox("body", (W, D, H), "plastic_silver", (0, 0, 0.004), bevel=0.006, segs=3, origin="bottom"))
    P.append(rbox("base", (W - 0.01, D - 0.01, 0.004), "plastic_black", (0, 0, 0), bevel=0.001, origin="bottom"))
    fy = -D / 2
    P.append(rbox("front", (W - 0.012, 0.004, H - 0.012), "plastic_black", (0, fy - 0.0015, H / 2 + 0.004), bevel=0.002))
    ff = fy - 0.0037
    # speakers: ring + perforated circle
    for sx in (-1, 1):
        P.append(ring("spk_ring", 0.072, 0.066, 0.004, "plastic_silver", (sx * 0.15, ff, 0.105), "-y", 40))
        P.append(grille("spk_grille", 0.13, 0.13, (sx * 0.15, ff - 0.0002, 0.105), 15, 15, (0.0045, 0.0045), depth=0.003, axis="-y", round_holes=True, mask_radius=0.064))
        P.append(label("spk_badge", (0.02, 0.005), (sx * 0.15, ff - 0.0005, 0.03), "label_white", "-y"))
    # tape deck: window with reels, door frame, piano keys below
    P.append(rbox("door", (0.12, 0.004, 0.075), "plastic_dark", (0, ff - 0.002, 0.14), bevel=0.0015))
    P.append(rbox("window", (0.10, 0.002, 0.045), "glass_dark", (0, ff - 0.0045, 0.15), bevel=0.0005))
    for sx in (-1, 1):
        P.append(ring("reel", 0.009, 0.006, 0.0015, "plastic_white", (sx * 0.0215, ff - 0.0056, 0.15), "-y", 16))
        P.append(cyl("hub", 0.0035, 0.0015, "plastic_white", (sx * 0.0215, ff - 0.0056, 0.15), "-y", 10, bevel=0))
    P.append(label("tape_lbl", (0.06, 0.006), (0, ff - 0.0045, 0.115), "label_white", "-y"))
    for k in range(6):
        w = 0.016
        P.append(button(f"pkey{k}", (w, 0.012, 0.018), (-0.05 + k * 0.02, fy - 0.004, 0.083), "plastic_dark", "-y"))
    P.append(label("pkey_lbl", (0.12, 0.004), (0, ff - 0.0005, 0.07), "label_white", "-y"))
    # tuning dial on the top-right of the front, VU window, knobs
    P.append(rbox("dial_bg", (0.11, 0.0015, 0.025), "label_white", (0.15, ff - 0.0012, 0.18), bevel=0.0003))
    P.append(boxes("dial_lines", [((0.0008, 0.0008, 0.012), (0.10 + k * 0.012, ff - 0.0022, 0.18)) for k in range(9)], "label_black", bevel=0))
    P.append(boxes("needle", [((0.0012, 0.0012, 0.022), (0.135, ff - 0.0028, 0.18))], "label_red", bevel=0))
    P.append(rbox("dial_glass", (0.112, 0.001, 0.027), "glass_dark", (0.15, ff - 0.0035, 0.18), bevel=0.0002))
    P.append(rbox("vu", (0.05, 0.0015, 0.02), "label_white", (-0.15, ff - 0.0012, 0.18), bevel=0.0003))
    P.append(boxes("vu_needle", [((0.0012, 0.0012, 0.015), (-0.145, ff - 0.0025, 0.18))], "label_black", bevel=0))
    P.append(led("stereo_led", 0.0015, (-0.11, ff - 0.0005, 0.185), "led_red", "-y"))
    top = H + 0.004
    P += knob("vol", 0.011, 0.012, "plastic_black", (0.12, 0.03, top), "z", 24)
    P += knob("tune", 0.011, 0.012, "plastic_black", (0.16, 0.03, top), "z", 24)
    P += knob("bass", 0.008, 0.01, "plastic_black", (-0.12, 0.03, top), "z", 20)
    P += knob("treble", 0.008, 0.01, "plastic_black", (-0.16, 0.03, top), "z", 20)
    P.append(boxes("band_sw", [((0.03, 0.006, 0.003), (0.0, 0.05, top - 0.001)), ((0.007, 0.005, 0.005), (-0.006, 0.05, top + 0.0015))], "plastic_dark", bevel=0.0005))
    P.append(label("top_lbl", (0.08, 0.01), (0.0, -0.04, top + 0.0003), "label_black", "z"))
    # handle: arc tube with hinge blocks
    hpts = [(-0.13, 0, top - 0.01), (-0.13, 0, top + 0.02), (-0.11, 0, top + 0.04), (-0.05, 0, top + 0.047), (0.05, 0, top + 0.047), (0.11, 0, top + 0.04), (0.13, 0, top + 0.02), (0.13, 0, top - 0.01)]
    P.append(cable("handle", hpts, 0.008, "plastic_black", per_seg=6, segments=12))
    P.append(boxes("hinges", [((0.024, 0.024, 0.014), (-0.13, 0, top + 0.005)), ((0.024, 0.024, 0.014), (0.13, 0, top + 0.005))], "plastic_black", bevel=0.002))
    # telescopic aerial from the back-right corner, angled
    ax, ay, az = 0.20, D / 2 - 0.015, top
    aer = [cyl("aer_base", 0.005, 0.012, "plastic_black", (ax, ay, az), "z", 12, bevel=0.0008, origin="bottom"),
           cyl("aer1", 0.0035, 0.10, "metal_chrome", (ax, ay, az + 0.012), "z", 10, bevel=0.0005, origin="bottom"),
           cyl("aer2", 0.0025, 0.09, "metal_chrome", (ax, ay, az + 0.11), "z", 10, bevel=0.0004, origin="bottom"),
           cyl("aer3", 0.0017, 0.08, "metal_chrome", (ax, ay, az + 0.20), "z", 8, bevel=0.0003, origin="bottom"),
           dome("aer_tip", 0.003, 0.003, "metal_chrome", (ax, ay, az + 0.28), "z", 8, 3)]
    rotate_parts(aer, (math.radians(-30), math.radians(-45), 0), (ax, ay, az))
    P += aer
    # rear: battery door, cable; feet; stickers
    by = D / 2
    P.append(rbox("batt_door", (0.16, 0.003, 0.07), "plastic_silver", (0, by + 0.0005, 0.05), bevel=0.001))
    P.append(label("batt_lbl", (0.05, 0.02), (0.1, by + 0.0012, 0.14), "label_white", "y"))
    P.append(cable("cable", [(-0.15, by, 0.03), (-0.16, by + 0.03, 0.02), (-0.17, by + 0.06, 0.003), (-0.14, by + 0.09, 0.003)], 0.003))
    P += corner_feet(W, D, inset=0.03, r=0.008, h=0.004, z=-0.004)
    P.append(sticker("s1", (0.03, 0.03), (0.055, ff - 0.0005, 0.045), "label_yellow", "-y", angle=0.3, peel=True))
    P.append(sticker("s2", (0.04, 0.02), (-0.06, ff - 0.0005, 0.195), "label_red", "-y", angle=-0.1))
    return assemble("electronics_radio_cassette", P)


@prop("fixture", "UK double 13A switched socket plate, wall-mounted (back = +Y against the wall). 0.146 x 0.012 x 0.086; place bottom at ~0.45 m. Front -Y.")
def wall_socket_double():
    W, T, H = 0.146, 0.010, 0.086
    P = []
    P.append(rbox("plate", (W, T, H), "plastic_white", (0, T / 2, 0), bevel=0.0025, segs=3, origin="bottom", taper=(0.975, 0.96), taper_axis="-y" if False else "y"))
    ff = -0.0002
    zc = H / 2
    for sx in (-1, 1):
        x = sx * 0.040
        # pin apertures: earth (vertical, top centre), live/neutral (horizontal, below)
        P.append(port_slots("pins", [(0.0045, 0.009, (0, 0.012)), (0.0075, 0.0045, (-0.011, -0.008)), (0.0075, 0.0045, (0.011, -0.008))], (x, ff, zc), axis="-y", depth=0.006))
        P.append(label("earth_lbl", (0.008, 0.002), (x, ff - 0.0003, zc + 0.022), "label_black", "-y"))
        # rocker switch with red indicator (switch sits between the sockets)
        sxw = sx * 0.012
        P.append(boxes("sw_frame", [((0.012, 0.002, 0.02), (sxw, ff - 0.0005, zc + 0.012))], "plastic_grey", bevel=0.0004))
        rocker = rbox("rocker", (0.010, 0.0045, 0.017), "plastic_white", (sxw, ff - 0.0025, zc + 0.012), bevel=0.0012, taper=(0.9, 0.9), taper_axis="y")
        rocker.rotation_euler = (math.radians(sx * 8 if sx > 0 else -8), 0, 0)
        P.append(rocker)
        P.append(label("sw_red", (0.005, 0.0025), (sxw, ff - 0.0048, zc + 0.012 + 0.006), "label_red", "-y"))
    # fixing screws, plate edge chamfer seam, a faint scuff label
    for sx in (-1, 1):
        P.append(cyl("screw", 0.0028, 0.0008, "metal_chrome", (sx * 0.0603, ff - 0.0004, zc), "-y", 12, bevel=0.0002))
        P.append(boxes("screw_slot", [((0.004, 0.0005, 0.0006), (sx * 0.0603, ff - 0.0010, zc))], "label_black", bevel=0))
    P.append(label("scuff", (0.02, 0.01), (-0.05, ff - 0.0002, 0.012), "plastic_grey", "-y"))
    return assemble("electronics_wall_socket_double", P)


# =====================================================================================================  runner

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = None
    export = "--noexport" not in argv
    views = ("front34", "back34")
    for i, a in enumerate(argv):
        if a == "--only":
            only = argv[i + 1].split(",")
        if a == "--views":
            views = tuple(argv[i + 1].split(","))
    names = only or list(BUILDERS.keys())
    manifest = load_manifest()
    for n in names:
        fn, cat, notes, variant_of = BUILDERS[n]
        clean_scene()
        random.seed(hash(n) & 0xffff)
        ob = fn()
        full = f"{FAMILY}_{n}"
        ob.name = full
        t = tris(ob)
        print(f"[electronics] {full}: {t} tris dims {dims(ob)}")
        pngs = preview(ob, full, views=views, size=(800, 600))
        print("  previews:", pngs)
        if export:
            export_fbx(ob, FAMILY, full)
            record(manifest, ob, full, cat, notes, variant_of)
            save_manifest(manifest)
    print("[electronics] done")


main()
