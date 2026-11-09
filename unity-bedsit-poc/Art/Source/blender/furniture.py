"""furniture family - modest, slightly worn bedsit furniture (flat-pack / second-hand).

Run all:    blender -b -P Art/Source/blender/furniture.py
Run some:   blender -b -P Art/Source/blender/furniture.py -- desk desk_chair wardrobe
Views:      add  views=front34,back34,front  after --  (default front34 + back34)

Every prop: metres, FRONT faces -Y, origin bottom centre. Movable parts are child objects (door_L, door_R, drawer_N, leaf,
head, glass...). Static geometry is joined into `body` (or into the root when nothing moves).
"""
import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(__file__))
import importlib, bsk, lib_furniture
importlib.reload(bsk); importlib.reload(lib_furniture)
from bsk import *
from lib_furniture import *
from lib_furniture import _bm_cube

FAMILY = "furniture"
MANIFEST = os.path.join(os.path.dirname(__file__), f"manifest_{FAMILY}.json")
BUILDERS = {}


def prop(category, notes="", variant_of=None, views=("front34", "back34")):
    def deco(fn):
        BUILDERS[fn.__name__] = (fn, category, notes, variant_of, views)
        return fn
    return deco


# ================================================================================================= DESK
@prop("furniture", "Desk top surface at z=0.74. Pedestal (2 drawers + open shelf) on the RIGHT, panel leg on the LEFT. "
                   "Cable grommet at x=+0.45 y=+0.20 on the top. Back = +Y. drawer_1/drawer_2 slide along -Y (origin front-bottom-centre).")
def furniture_desk():
    W, D, H = 1.30, 0.65, 0.74
    tt = 0.025
    S = []
    # --- top with grommet hole
    top = panel("top", (W, D, tt), "laminate_oak", (0, 0, H - tt / 2), "laminate_edge", bevel=0.0025)
    cutter = cylinder("cutter", 0.030, 0.1, "plastic_black", segments=24, bevel=0.0, center=(0.45, 0.20, H - 0.06))
    bm = top.modifiers.new("hole", "BOOLEAN"); bm.operation = "DIFFERENCE"; bm.object = cutter; bm.solver = "EXACT"
    apply_modifiers(top)
    bpy.data.objects.remove(cutter)
    uv_box(top)
    S.append(top)
    # grommet ring (black plastic) sitting in the hole
    S.append(lathe("grommet", [(0.026, H - tt + 0.001), (0.0305, H - tt + 0.001), (0.0305, H - 0.001), (0.038, H + 0.001), (0.038, H + 0.0035),
                               (0.030, H + 0.004), (0.026, H + 0.002), (0.026, H - tt + 0.001)], "plastic_black", segments=28, center=(0.45, 0.20, 0)))
    # --- pedestal (right)
    pw, pd, ph = 0.40, 0.60, H - tt
    px = W / 2 - pw / 2 - 0.02
    yc = 0.02   # set back 2 cm from the top's front edge
    parts, info = carcass("ped", pw, pd, ph, role="laminate_oak", edge="laminate_edge", top=False, plinth=0.06, plinth_recess=0.025)
    for p in parts:
        p.location.x += px; p.location.y += yc
    S += parts
    # fixed shelf between drawers and open section
    S.append(panel("ped_shelf", (info["inner_w"] + 0.001, pd - 0.003, 0.018), "laminate_oak", (px, yc - 0.0015, 0.40 + 0.009), "laminate_edge"))
    front_y = yc - pd / 2
    dw = info["inner_w"] - 0.004
    movable = []
    d1 = drawer("drawer_1", dw, 0.145, px, front_y, ph - 0.004 - 0.145, 0.50, "laminate_oak", "laminate_edge", handle="bar", handle_role="metal_steel")
    d2 = drawer("drawer_2", dw, 0.145, px, front_y, ph - 0.004 - 0.145 - 0.003 - 0.145, 0.50, "laminate_oak", "laminate_edge", handle="missing")
    movable += [d1, d2]
    # cam caps on pedestal outer side
    S += cam_caps("ped_caps", px + pw / 2, [yc - 0.22, yc + 0.22, yc - 0.22, yc + 0.22], [0.08, 0.08, 0.41, 0.41], +1)
    S += cam_caps("ped_caps2", px + pw / 2, [yc - 0.22, yc + 0.22], [0.70, 0.70], +1)
    # sticker on pedestal outer side
    S.append(sticker("ped_sticker", (px + pw / 2, yc - 0.12, 0.55), (0.09, 0.06), "x", "sticker_a", sign=+1, rot=math.radians(-12)))
    # --- left panel leg
    lx = -W / 2 + 0.02 + 0.009
    S.append(panel("leg_L", (0.018, pd, ph), "laminate_oak", (lx, yc, ph / 2), "laminate_edge"))
    S += cam_caps("leg_caps", lx - 0.009, [yc - 0.22, yc + 0.22, yc - 0.22, yc + 0.22], [0.08, 0.08, 0.68, 0.68], -1)
    # modesty rail between leg and pedestal
    rx0, rx1 = lx + 0.009, px - pw / 2
    S.append(panel("modesty", (rx1 - rx0, 0.018, 0.22), "laminate_oak", ((rx0 + rx1) / 2, yc + pd / 2 - 0.009 - 0.003, 0.52), "laminate_edge"))
    # adjustable plastic glides under the leg
    for yy in (yc - 0.26, yc + 0.26):
        S.append(cylinder("glide", 0.012, 0.004, "plastic_black", segments=12, bevel=0.0, center=(lx, yy, -0.002)))
    # --- wear: scuffs on the leg bottom corner, chipped top edge, coffee ring on the top
    S.append(decal("scuff1", (lx - 0.009, yc - 0.20, 0.05), (0.035, 0.02), "x", "scuff_dark", sign=-1, seed=4))
    S.append(decal("scuff2", (lx - 0.009, yc + 0.10, 0.025), (0.06, 0.012), "x", "scuff_light", sign=-1, seed=5))
    S.append(decal("chip", (-0.35, -D / 2 + 0.004, H - 0.0005), (0.05, 0.008), "z", "scuff_dark", sign=+1, seed=6, offset=0.0006))
    S.append(decal("chip2", (0.10, -D / 2, H - 0.004), (0.03, 0.006), "y", "scuff_dark", sign=-1, seed=8, offset=0.0006))
    S.append(torus("coffee_ring", (-0.30, -0.05, H + 0.0004), 0.041, 0.0025, "scuff_dark", seg_major=32, seg_minor=6))
    S.append(decal("scuff_plinth", (px - 0.1, front_y + 0.025, 0.02), (0.08, 0.025), "y", "scuff_dark", sign=-1, seed=9))
    return assemble("furniture_desk", S, movable)


# ================================================================================================= DESK CHAIR
@prop("furniture", "Swivel office chair. Seat top ~z=0.52, backrest top z=1.03, armrest top z=0.72. Footprint ~0.62 m. "
                   "Front = -Y (where knees go). Worn/shiny patches on the seat front edge.")
def furniture_desk_chair():
    S = []
    # --- 5 star base
    hub_z = 0.085
    S.append(cylinder("hub", 0.045, 0.06, "plastic_black", segments=24, bevel=0.003, center=(0, 0, hub_z - 0.03), origin="bottom"))
    for i in range(5):
        a = math.radians(90 + 72 * i + 36)
        L = 0.28
        bmm = _bm_cube((L, 0.05, 0.035))
        for v in bmm.verts:
            if v.co.x > 0:
                v.co.y *= 0.55; v.co.z *= 0.7; v.co.z -= 0.012
            else:
                v.co.z += 0.0
        arm = bsk._obj_from_bm(bmm, f"arm{i}", ["plastic_black"])
        arm.location = (math.cos(a) * (L / 2 + 0.02), math.sin(a) * (L / 2 + 0.02), hub_z)
        arm.rotation_euler = (0, math.radians(6), a)
        shade(arm, False); add_bevel(arm, 0.004, 2); uv_box(arm)
        S.append(arm)
        ex, ey = math.cos(a) * (L + 0.005), math.sin(a) * (L + 0.005)
        cs = caster(f"caster{i}", (ex, ey, 0.0))
        for c in cs:
            c.rotation_euler = (c.rotation_euler[0], c.rotation_euler[1], c.rotation_euler[2] + a + math.radians(12))
        # casters are built along X (wheel axle along X); rotate each about its own floor point
        for c in cs:
            # rotate the position around (ex,ey)
            rel = Vector(c.location) - Vector((ex, ey, 0))
            rel = Matrix.Rotation(a + math.radians(12), 4, "Z") @ rel
            c.location = Vector((ex, ey, 0)) + rel
        S += cs
    # --- gas lift
    S.append(cylinder("lift_outer", 0.028, 0.16, "plastic_black", segments=24, bevel=0.002, center=(0, 0, hub_z + 0.02)))
    S.append(cylinder("lift_inner", 0.019, 0.20, "metal_chrome", segments=24, bevel=0.001, center=(0, 0, hub_z + 0.17)))
    S.append(cylinder("lift_collar", 0.030, 0.012, "plastic_black", segments=24, bevel=0.002, center=(0, 0, hub_z + 0.17)))
    # --- seat mechanism
    seat_z = 0.44
    S.append(panel("mech", (0.26, 0.22, 0.035), "metal_dark", (0, 0.02, seat_z - 0.018), bevel=0.003))
    S.append(cylinder("mech_cone", 0.032, 0.03, "metal_dark", segments=20, bevel=0.002, center=(0, 0, hub_z + 0.36)))
    lever = bar("lever", (0.12, -0.05, seat_z - 0.02), (0.26, -0.06, seat_z - 0.03), 0.006, "metal_steel", segments=10)
    S.append(lever)
    S.append(cylinder("lever_tip", 0.011, 0.045, "plastic_black", segments=12, bevel=0.003, center=(0.265, -0.06, seat_z - 0.03), origin="center"))
    S[-1].rotation_euler = RY90
    # --- seat cushion (plastic shell underneath + padded top)
    S.append(panel("seat_shell", (0.47, 0.45, 0.012), "plastic_black", (0, 0, seat_z + 0.006), bevel=0.004))
    S += cushion("seat", (0.48, 0.46, 0.085), (0, 0, seat_z + 0.012 + 0.0425), "fabric_office_grey", puff=0.015, noise=0.003, seed=2,
                 worn_role="fabric_office_worn", worn_frac=0.18, subsurf_level=1)
    # --- backrest support: curved bar from under the seat up the back
    sup = wire("back_support", [(0, 0.10, seat_z - 0.01), (0, 0.24, seat_z - 0.005), (0, 0.27, seat_z + 0.10), (0, 0.255, seat_z + 0.30)], 0.016,
               "plastic_black", n=8, segments=16)
    S.append(sup)
    S.append(panel("back_plate", (0.14, 0.03, 0.12), "plastic_black", (0, 0.245, seat_z + 0.33), bevel=0.004))
    # --- backrest cushion, tilted back 7 deg
    bc = cushion("backrest", (0.44, 0.075, 0.50), (0, 0, 0), "fabric_office_grey", puff=0.014, noise=0.003, seed=5, seam=True, subsurf_level=1)
    for o in bc:
        o.rotation_euler = (math.radians(-7), 0, 0)
        o.location = Vector((0, 0.215, seat_z + 0.045 + 0.25 + 0.02)) + Vector(o.location)
    # the seam wire is built around the top of the cushion (z axis) - for a backrest we want it around the front face; rebuild
    bpy.data.objects.remove(bc[1])
    bc = [bc[0]]
    sx, sz = 0.44, 0.50
    inset = 0.014
    rp = []
    pts = [Vector((-sx / 2 + inset, -0.0375 + 0.004, -sz / 2 + inset)), Vector((sx / 2 - inset, -0.0375 + 0.004, -sz / 2 + inset)),
           Vector((sx / 2 - inset, -0.0375 + 0.004, sz / 2 - inset)), Vector((-sx / 2 + inset, -0.0375 + 0.004, sz / 2 - inset))]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        rp += [a + (b - a) * 0.08, a + (b - a) * 0.92]
    seam = wire("back_seam", rp, 0.0025, "stitch_thread", n=5, segments=8, closed=True)
    seam.rotation_euler = (math.radians(-7), 0, 0)
    seam.location = (0, 0.215, seat_z + 0.045 + 0.25 + 0.02)
    # lumbar stitching: two horizontal lines across the backrest
    for zz in (-0.08, 0.06):
        ln = wire(f"back_stitch{zz}", [(-sx / 2 + 0.03, -0.0375 + 0.003, zz), (0, -0.0375 - 0.004, zz), (sx / 2 - 0.03, -0.0375 + 0.003, zz)], 0.002,
                  "stitch_thread", n=6, segments=8)
        ln.rotation_euler = (math.radians(-7), 0, 0)
        ln.location = (0, 0.215, seat_z + 0.045 + 0.25 + 0.02)
        S.append(ln)
    S += bc + [seam]
    # --- armrests
    for s in (-1, 1):
        x = s * 0.25
        post = wire(f"arm_post{s}", [(x * 0.92, 0.0, seat_z - 0.01), (x, 0.0, seat_z + 0.12), (x, 0.0, seat_z + 0.26)], 0.014, "plastic_black", n=6, segments=14)
        S.append(post)
        S.append(panel(f"arm_pad{s}", (0.07, 0.26, 0.022), "plastic_black", (x, 0.02, seat_z + 0.27), bevel=0.008, segments=3))
    return assemble("furniture_desk_chair", S)


# ================================================================================================= WARDROBE
def _wardrobe(name, open_door=False):
    W, D, H = 0.85, 0.55, 1.85
    t = 0.018
    corn = 0.030
    plinth = 0.08
    S = []
    body_h = H - corn
    parts, info = carcass("w", W, D - t, body_h, role="laminate_white", edge="laminate_edge_white", plinth=plinth, plinth_recess=0.03)
    for p in parts:
        p.location.y += t / 2        # carcass behind the door plane
    S += parts
    front_y = -D / 2
    # cornice: two stepped boards
    S.append(panel("cornice_a", (W + 0.02, D + 0.01, 0.014), "laminate_white", (0, 0.0, body_h + 0.007), "laminate_edge_white"))
    S.append(panel("cornice_b", (W + 0.04, D + 0.02, 0.016), "laminate_white", (0, 0.0, body_h + 0.014 + 0.008), "laminate_edge_white"))
    # doors
    gap = 0.003
    dw = (W - 3 * gap) / 2
    dh = body_h - plinth - 2 * gap
    dz = plinth + gap
    movable = []
    dL = door("door_L", dw, dh, t, -(gap / 2 + dw / 2), front_y, dz, "L", "laminate_white", "laminate_edge_white", handle="bar", handle_len=0.16,
              handle_z=dz + dh / 2 + 0.05)
    dR = door("door_R", dw, dh, t, (gap / 2 + dw / 2), front_y, dz, "R", "laminate_white", "laminate_edge_white", handle="bar", handle_len=0.16,
              handle_z=dz + dh / 2 + 0.05)
    movable += [dL, dR]
    # wear
    S.append(decal("kick1", (-0.2, front_y + 0.03 + t / 2, 0.03), (0.10, 0.035), "y", "scuff_dark", seed=11))
    S.append(decal("kick2", (0.25, front_y + 0.03 + t / 2, 0.045), (0.06, 0.03), "y", "scuff_light", seed=12))
    S.append(decal("side_scuff", (W / 2, 0.1, 0.9), (0.03, 0.08), "x", "scuff_light", sign=+1, seed=13))
    S += cam_caps("caps_R", W / 2, [-0.18, 0.20, -0.18, 0.20, -0.18, 0.20], [0.10, 0.10, 0.95, 0.95, 1.80, 1.80], +1)
    S += cam_caps("caps_L", -W / 2, [-0.18, 0.20, -0.18, 0.20, -0.18, 0.20], [0.10, 0.10, 0.95, 0.95, 1.80, 1.80], -1)
    if open_door:
        # interior: shelf + chrome rail + clothes on hangers
        iw = info["inner_w"]
        S.append(panel("shelf", (iw, D - t - 0.003 - 0.02, t), "laminate_white", (0, t / 2 - 0.0015 + 0.01, 1.62 + t / 2), "laminate_edge_white"))
        rail_z = 1.56
        S.append(bar("rail", (-iw / 2, 0.04, rail_z), (iw / 2, 0.04, rail_z), 0.011, "metal_chrome", segments=16))
        for s in (-1, 1):
            S.append(panel(f"rail_bracket{s}", (0.008, 0.03, 0.045), "metal_chrome", (s * (iw / 2 - 0.004), 0.04, rail_z + 0.01), bevel=0.001))
        clothes = [("cotton_black", 0.39, 0.64, False), ("cotton_hoodie_grey", 0.40, 0.66, True), ("cotton_blue", 0.38, 0.62, False),
                   ("cotton_red", 0.37, 0.60, False), ("cotton_white", 0.39, 0.63, False)]
        xs = [-0.20, -0.11, -0.02, 0.07, 0.16]
        for i, ((role, cw, cl, longs), xx) in enumerate(zip(clothes, xs)):
            S += garment_on_hanger(f"g{i}", xx, 0.04, rail_z, role, cw, cl, 0.065 if longs else 0.05, 10 + i, long_sleeve=longs,
                                   hanger_role="plastic_black" if i % 2 else "metal_steel", compact=True)
        # a pair of folded jumpers on the shelf... keep it simple: a folded stack
        st = cushion("folded", (0.26, 0.30, 0.07), (-0.15, 0.03, 1.62 + t + 0.035), "cotton_green", puff=0.006, noise=0.003, seed=21, seam=False)
        S += st
        dR.rotation_euler = (0, 0, math.radians(58))
    root = assemble(name, S, movable)
    return root


@prop("furniture", "Two-door wardrobe, back = +Y. Doors door_L (hinge left, opens with -Z rotation) / door_R (hinge right, +Z rotation), "
                   "origins on hinge axes. Top of cornice z=1.85. Interior empty in this closed variant.")
def furniture_wardrobe():
    return _wardrobe("furniture_wardrobe")


@prop("furniture", "Wardrobe with door_R open 58 deg, interior shelf (z=1.62), chrome rail (z=1.56) and 5 garments on hangers. "
                   "Same footprint/origin as furniture_wardrobe.", variant_of="furniture_wardrobe", views=("front34", "front"))
def furniture_wardrobe_open():
    return _wardrobe("furniture_wardrobe_open", open_door=True)


# ================================================================================================= CLOTHES RAIL
@prop("furniture", "Cheap chrome clothes rail 1.2 m wide, 1.55 m high, with 3 hangers and 2 garments. Rail bar at z=1.50.")
def furniture_clothes_rail():
    S = []
    W = 1.20
    rail_z = 1.50
    for s in (-1, 1):
        x = s * (W / 2 - 0.02)
        S.append(bar(f"foot{s}", (x, -0.22, 0.02), (x, 0.22, 0.02), 0.0125, "metal_chrome", segments=14))
        for yy in (-0.20, 0.20):
            S += [c for c in caster(f"caster{s}{yy}", (x, yy, 0.0), r=0.020)]
        S.append(bar(f"lower{s}", (x, 0, 0.02), (x, 0, 0.86), 0.0125, "metal_chrome", segments=14))
        S.append(cylinder(f"collar{s}", 0.017, 0.035, "plastic_black", segments=16, bevel=0.002, center=(x, 0, 0.86)))
        S.append(bar(f"upper{s}", (x, 0, 0.88), (x, 0, rail_z), 0.0095, "metal_chrome", segments=14))
        S.append(wire(f"corner{s}", [(x, 0, rail_z - 0.001), (x, 0, rail_z + 0.03), (x - s * 0.03, 0, rail_z + 0.03), (x - s * 0.06, 0, rail_z + 0.03)], 0.0095, "metal_chrome", n=6))
    S.append(bar("rail", (-(W / 2 - 0.08), 0, rail_z + 0.03), ((W / 2 - 0.08), 0, rail_z + 0.03), 0.0095, "metal_chrome", segments=14))
    S.append(bar("shelf_bar", (-(W / 2 - 0.02), 0.0, 0.30), ((W / 2 - 0.02), 0.0, 0.30), 0.009, "metal_chrome", segments=12))
    S.append(bar("shelf_bar2", (-(W / 2 - 0.02), -0.12, 0.30), ((W / 2 - 0.02), -0.12, 0.30), 0.009, "metal_chrome", segments=12))
    S.append(bar("shelf_bar3", (-(W / 2 - 0.02), 0.12, 0.30), ((W / 2 - 0.02), 0.12, 0.30), 0.009, "metal_chrome", segments=12))
    for s in (-1, 1):
        S.append(bar(f"shelf_x{s}", (s * (W / 2 - 0.02), -0.12, 0.30), (s * (W / 2 - 0.02), 0.12, 0.30), 0.009, "metal_chrome", segments=12))
    rz = rail_z + 0.03
    S += garment_on_hanger("g0", -0.30, 0, rz, "denim", 0.46, 0.68, 0.055, 31, long_sleeve=True, hanger_role="plastic_black")
    S += garment_on_hanger("g1", -0.20, 0, rz, "cotton_yellow", 0.43, 0.60, 0.045, 32, hanger_role="metal_steel")
    S += garment_on_hanger("g2", -0.11, 0, rz, "cotton_black", 0.44, 0.62, 0.05, 33, hanger_role="plastic_black")
    for i, xx in enumerate((0.22, 0.27, 0.33)):
        hp = hanger(f"h{i}", (0, 0, rz + 0.018), role="plastic_black" if i != 1 else "metal_steel")
        for o in hp:
            o.rotation_euler = (0, 0, math.pi / 2)
            o.location = (xx + 0.016, 0, 0)
        S += hp
    return assemble("furniture_clothes_rail", S)


# ================================================================================================= DRESSER
@prop("furniture", "Chest of 4 drawers, painted white with pine top. Top surface z=0.95. Back = +Y. drawer_1 (top) .. drawer_4 slide -Y, "
                   "origins front-bottom-centre. Drawer 3 is missing its left knob.")
def furniture_dresser():
    W, D, H = 0.90, 0.45, 0.95
    t = 0.018
    tt = 0.022
    plinth = 0.07
    S = []
    body_h = H - tt
    parts, info = carcass("c", W, D - 0.015, body_h, role="wood_painted_white", top=True, plinth=plinth, plinth_recess=0.012)
    for p in parts:
        p.location.y += 0.0075
    S += parts
    S.append(panel("top", (W + 0.03, D + 0.015, tt), "wood_light", (0, -0.0075, H - tt / 2), bevel=0.006, segments=3))
    # bracket feet (blocks at the corners of the plinth)
    for sx in (-1, 1):
        for sy in (-1, 1):
            S.append(panel(f"foot{sx}{sy}", (0.06, 0.05, plinth - 0.002), "wood_painted_white", (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03) + 0.0075, plinth / 2), bevel=0.003))
    front_y = -D / 2
    gap = 0.004
    n = 4
    dh = (body_h - plinth - t - (n + 1) * gap) / n
    dw = W - 2 * t - 0.006
    movable = []
    handles = ["knob2", "knob2", "knob2_missing", "knob2"]
    for i in range(n):
        zb = body_h - t - gap - (i + 1) * dh - i * gap
        movable.append(drawer(f"drawer_{i + 1}", dw, dh, 0, front_y, zb, D - 0.08, "wood_painted_white", handle=handles[i], knob_role="wood_dark",
                              t=0.018))
    # wear: chipped paint along the top front edge, scuffs near the feet
    S.append(decal("chip1", (-0.30, -D / 2 - 0.0075, H - tt - 0.003), (0.03, 0.008), "y", "scuff_dark", seed=41))
    S.append(decal("scuffL", (-W / 2, -0.05, 0.18), (0.08, 0.05), "x", "scuff_dark", sign=-1, seed=42))
    S.append(decal("scuffR", (W / 2, 0.1, 0.5), (0.05, 0.08), "x", "scuff_light", sign=+1, seed=43))
    S.append(torus("ring", (0.25, -0.05, H + 0.0004), 0.042, 0.0022, "scuff_dark", seg_major=32, seg_minor=6))
    return assemble("furniture_dresser", S, movable)


# ================================================================================================= BOOKCASE
@prop("furniture", "Tall bookcase 0.8x0.3x1.8, back = +Y. Shelf top surfaces at z=0.068, 0.418, 0.768, 1.118 (sagging ~12 mm in the middle), 1.468; "
                   "top at 1.80. Inner width 0.764.")
def furniture_bookcase():
    W, D, H = 0.80, 0.30, 1.80
    t = 0.018
    S = []
    parts, info = carcass("b", W, D, H, role="laminate_white", edge="laminate_edge_white", plinth=0.05, plinth_recess=0.0)
    S += parts
    iw = info["inner_w"]
    shelf_z = [0.40, 0.75, 1.45]
    for z in shelf_z:
        S.append(panel(f"shelf{z}", (iw - 0.002, D - 0.003 - 0.004, t), "laminate_white", (0, -0.0015 - 0.002, z + t / 2), "laminate_edge_white"))
    # sagging shelf at 1.10
    zs = 1.10
    bm = _bm_cube((iw - 0.002, D - 0.007, t))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 0.1], cuts=10, use_grid_fill=True)
    bm.normal_update()
    for f in bm.faces:
        if abs(f.normal.z) < 0.5:
            f.material_index = 1
    for v in bm.verts:
        u = max(-1.0, min(1.0, v.co.x / ((iw - 0.002) / 2)))
        v.co.z -= 0.012 * (1 - u * u) ** 1.2
    sag = bsk._obj_from_bm(bm, "shelf_sag", ["laminate_white", "laminate_edge_white"])
    sag.location = (0, -0.0035, zs + t / 2)
    shade(sag, True, angle=30); add_bevel(sag, 0.002, 2); uv_box(sag)
    S.append(sag)
    # shelf pins (4 per shelf) + rows of pin holes on the inner sides
    for z in shelf_z + [zs]:
        for sx in (-1, 1):
            for yy in (-0.10, 0.08):
                S.append(cylinder(f"pin{z}{sx}{yy}", 0.0025, 0.012, "metal_steel", segments=8, bevel=0.0, center=(sx * (iw / 2 - 0.004), yy, z - 0.0025), origin="center"))
                S[-1].rotation_euler = RY90
    for sx in (-1, 1):
        for k in range(0, 18):
            zz = 0.26 + k * 0.064
            for yy in (-0.10, 0.08):
                if any(abs(zz - z) < 0.01 for z in shelf_z + [zs]):
                    continue
                h = cylinder(f"hole{sx}{k}{yy}", 0.0025, 0.002, "scuff_dark", segments=8, bevel=0.0, center=(sx * (iw / 2 - 0.0005), yy, zz), origin="center")
                h.rotation_euler = RY90
                S.append(h)
    # nail heads on the back panel (visible from behind) and wear
    for xx in (-0.35, -0.12, 0.12, 0.35):
        for zz in (0.3, 0.9, 1.5):
            S.append(cylinder(f"nail{xx}{zz}", 0.002, 0.001, "metal_steel", segments=8, bevel=0.0, center=(xx, D / 2 + 0.0005, zz), origin="center"))
            S[-1].rotation_euler = RX90
    S.append(decal("scuff", (-W / 2, -0.08, 0.10), (0.06, 0.06), "x", "scuff_dark", sign=-1, seed=51))
    S.append(decal("chip", (0.2, -D / 2 + 0.0035, 0.40 + t), (0.025, 0.006), "z", "scuff_dark", sign=+1, seed=52, offset=0.0005))
    S.append(sticker("stk", (W / 2, -0.02, 1.25), (0.07, 0.05), "x", "sticker_b", sign=+1, rot=math.radians(8)))
    return assemble("furniture_bookcase", S)


# ================================================================================================= WALL SHELF
@prop("furniture", "Floating wall shelf 0.8x0.2, board top surface at z=0.035 above origin; brackets hang below (overall height 0.17). "
                   "Back (wall side) = +Y. Mount so origin is at the desired board underside height.", views=("front34", "back34"))
def furniture_wall_shelf():
    W, D, T = 0.80, 0.20, 0.035
    S = []
    S.append(panel("board", (W, D, T), "wood_dark", (0, 0, 0.13 + T / 2), bevel=0.004))
    for x in (-0.26, 0.26):
        S.append(panel(f"brk_v{x}", (0.03, 0.006, 0.13), "metal_dark", (x, D / 2 - 0.003, 0.065), bevel=0.001))
        S.append(panel(f"brk_h{x}", (0.03, D - 0.03, 0.006), "metal_dark", (x, -0.015 + 0.0, 0.13 - 0.003), bevel=0.001))
        S.append(bar(f"brk_d{x}", (x, D / 2 - 0.006, 0.012), (x, -D / 2 + 0.035, 0.13 - 0.012), 0.004, "metal_dark", segments=10))
        for zz in (0.02, 0.11):
            S.append(cylinder(f"screw{x}{zz}", 0.0035, 0.002, "metal_steel", segments=8, bevel=0.0, center=(x, D / 2 - 0.006, zz), origin="center"))
            S[-1].rotation_euler = RX90
    return assemble("furniture_wall_shelf", S)


# ================================================================================================= TV STAND
@prop("furniture", "Low TV unit 1.0x0.4x0.45, back = +Y. Top surface z=0.45; open shelf (left) surfaces at z=0.098 and z=0.265; "
                   "cupboard door_R on the right (hinge right, +Z opens). Cable hole in the back panel.")
def furniture_tv_stand():
    W, D, H = 1.00, 0.40, 0.45
    t = 0.018
    leg = 0.08
    S = []
    parts, info = carcass("tv", W, D, H - leg, role="laminate_grey", edge="laminate_grey", z0=leg, back=False)
    S += parts
    # back panel in 3 pieces leaving a cable slot
    bz0, bz1 = leg, H
    S.append(panel("back_a", (W - 0.002, 0.003, (bz1 - bz0) * 0.55), "hardboard_back", (0, D / 2 - 0.0015, bz0 + (bz1 - bz0) * 0.725), bevel=0.0))
    S.append(panel("back_b", (W - 0.002, 0.003, (bz1 - bz0) * 0.25), "hardboard_back", (0, D / 2 - 0.0015, bz0 + (bz1 - bz0) * 0.125), bevel=0.0))
    S.append(panel("back_c", (0.52, 0.003, (bz1 - bz0) * 0.20), "hardboard_back", (-0.24 + 0.0, D / 2 - 0.0015, bz0 + (bz1 - bz0) * 0.35), bevel=0.0))
    # divider at x=0.15; mid shelf on the left
    div_x = 0.15
    S.append(panel("div", (t, D - 0.003, H - leg - 2 * t), "laminate_grey", (div_x, -0.0015, leg + (H - leg) / 2), "laminate_grey"))
    left_w = div_x - t / 2 - (-W / 2 + t)
    S.append(panel("mid", (left_w, D - 0.003 - 0.01, t), "laminate_grey", ((-W / 2 + t + div_x - t / 2) / 2, -0.0015 - 0.005, 0.265 - t / 2), "laminate_grey"))
    # tapered wooden legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            lg = tapered_leg(f"leg{sx}{sy}", (sx * (W / 2 - 0.06), sy * (D / 2 - 0.06), 0), leg, 0.012, 0.018, "wood_light")
            lg.rotation_euler = (math.radians(-8 * sy), math.radians(8 * sx), 0)
            S.append(lg)
    # door on the right
    front_y = -D / 2
    dw = (W / 2 - t) - (div_x + t / 2) - 0.004
    dx = (div_x + t / 2 + W / 2 - t) / 2
    dh = H - leg - 2 * t - 0.004
    dr = door("door_R", dw, dh, t, dx, front_y, leg + t + 0.002, "R", "laminate_grey", "laminate_grey", handle="knob", knob_role="metal_steel")
    # wear
    S.append(torus("ring", (-0.3, 0.05, H + 0.0004), 0.04, 0.0022, "scuff_dark", seg_major=32, seg_minor=6))
    S.append(decal("scuff", (-W / 2, 0.0, 0.12), (0.04, 0.02), "x", "scuff_light", sign=-1, seed=62))
    return assemble("furniture_tv_stand", S, [dr])


# ================================================================================================= BEDSIDE TABLE
@prop("furniture", "Bedside table 0.40x0.35x0.50, pine. Top surface z=0.50; open shelf surface z=0.145. drawer_1 (knob) slides -Y. Back = +Y.")
def furniture_bedside_table():
    W, D, H = 0.40, 0.35, 0.50
    t = 0.018
    leg = 0.06
    S = []
    parts, info = carcass("bt", W, D, H - leg - 0.02, role="wood_light", z0=leg, top=False, bottom=True, back=True)
    S += parts
    S.append(panel("top", (W + 0.02, D + 0.015, 0.02), "wood_light", (0, -0.0075, H - 0.01), bevel=0.005, segments=3))
    # shelf under the drawer
    S.append(panel("shelf", (info["inner_w"], D - 0.003 - 0.01, t), "wood_light", (0, -0.0015 - 0.005, 0.145 + 0.0 - t / 2 + 0.0)))
    S[-1].location.z = 0.145 - t / 2
    # drawer housing: rail panel under drawer
    drawer_h = 0.12
    dz = H - 0.02 - 0.004 - drawer_h
    S.append(panel("rail", (info["inner_w"], D - 0.003, t), "wood_light", (0, -0.0015, dz - t / 2 - 0.002)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            S.append(tapered_leg(f"leg{sx}{sy}", (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), 0), leg, 0.014, 0.02, "wood_light"))
    d1 = drawer("drawer_1", info["inner_w"] - 0.004, drawer_h, 0, -D / 2, dz, D - 0.07, "wood_light", handle="knob", knob_role="ceramic_white")
    S.append(torus("ring", (0.08, -0.05, H + 0.0004), 0.04, 0.0022, "scuff_dark", seg_major=32, seg_minor=6))
    S.append(decal("scuff", (-W / 2, 0.02, 0.3), (0.03, 0.015), "x", "scuff_dark", sign=-1, seed=72))
    return assemble("furniture_bedside_table", S, [d1])


# ================================================================================================= RADIATOR
@prop("furniture", "Single panel radiator 0.9 wide, panel from z=0.12 to 0.72 (0.6 high), 0.08 deep + brackets; pipes to the floor. "
                   "Back = +Y against the wall (wall face at y=+0.055). TRV valve on the left, lockshield on the right.")
def furniture_radiator():
    W, Hh, D = 0.90, 0.60, 0.08
    z0 = 0.12
    S = []
    # front corrugated panel: flat back sheet + vertical ribs
    S.append(panel("panel", (W, 0.018, Hh), "radiator_white", (0, -0.02, z0 + Hh / 2), bevel=0.004, segments=3))
    n = 26
    for i in range(n):
        x = -W / 2 + 0.03 + i * (W - 0.06) / (n - 1)
        S.append(cylinder(f"rib{i}", 0.009, Hh - 0.03, "radiator_white", segments=10, bevel=0.0, center=(x, -0.029, z0 + 0.015)))
    # convector fins behind (zigzag) + top grille
    fins = []
    for i in range(n * 2):
        x = -W / 2 + 0.03 + i * (W - 0.06) / (n * 2 - 1)
        fins.append(Vector((x, -0.011 + (0.0 if i % 2 == 0 else 0.03), 0)))
    rings = [[Vector((p.x, p.y, z0 + 0.03)) for p in fins], [Vector((p.x, p.y, z0 + Hh - 0.03)) for p in fins]]
    bm = bmesh.new()
    va = [bm.verts.new(p) for p in rings[0]]
    vb = [bm.verts.new(p) for p in rings[1]]
    for i in range(len(va) - 1):
        bm.faces.new((va[i], va[i + 1], vb[i + 1], vb[i]))
    fin = bsk._obj_from_bm(bm, "fins", ["radiator_white"])
    shade(fin, False)
    solidify(fin, 0.0012)
    uv_box(fin)
    S.append(fin)
    S.append(panel("back_sheet", (W, 0.004, Hh - 0.02), "radiator_white", (0, 0.027, z0 + Hh / 2), bevel=0.001))
    # top grille with slots
    S.append(panel("grille", (W, D - 0.025, 0.004), "radiator_white", (0, 0.0045, z0 + Hh - 0.002), bevel=0.001))
    for i in range(14):
        x = -W / 2 + 0.06 + i * (W - 0.12) / 13
        S.append(decal(f"slot{i}", (x, 0.0045, z0 + Hh + 0.0022), (0.02, 0.035), "z", "scuff_dark", sign=+1, irregular=False, offset=0.0))
    # side end caps
    for s in (-1, 1):
        S.append(panel(f"cap{s}", (0.004, D - 0.025, Hh - 0.01), "radiator_white", (s * (W / 2 - 0.002), 0.0045, z0 + Hh / 2), bevel=0.001))
    # wall brackets
    for x in (-0.28, 0.28):
        S.append(panel(f"brk{x}", (0.03, 0.03, Hh - 0.1), "metal_steel", (x, 0.045, z0 + Hh / 2), bevel=0.002))
    # valves + pipes (copper down to the floor)
    for s, kind in ((-1, "trv"), (1, "lockshield")):
        x = s * (W / 2 + 0.045)
        S.append(bar(f"tail{s}", (s * W / 2 - s * 0.002, -0.02, z0 + 0.04), (x - s * 0.02, -0.02, z0 + 0.04), 0.009, "metal_chrome", segments=14))
        S.append(cylinder(f"valve_body{s}", 0.016, 0.05, "metal_chrome", segments=16, bevel=0.002, center=(x, -0.02, z0 + 0.015)))
        if kind == "trv":
            S.append(lathe(f"trv_head", [(0, 0), (0.014, 0), (0.019, 0.01), (0.021, 0.04), (0.017, 0.05), (0.0, 0.05)], "plastic_white", segments=20,
                           center=(x, -0.02, z0 + 0.065)))
            # setting numbers ring as a decal band
            S.append(torus("trv_band", (x, -0.02, z0 + 0.097), 0.0212, 0.0015, "scuff_dark", seg_major=20, seg_minor=5))
        else:
            S.append(lathe(f"ls_cap", [(0, 0), (0.016, 0), (0.016, 0.02), (0.01, 0.026), (0, 0.026)], "plastic_white", segments=16, center=(x, -0.02, z0 + 0.065)))
        S.append(bar(f"pipe{s}", (x, -0.02, 0), (x, -0.02, z0 + 0.0), 0.0075, "metal_copper", segments=14))
        S.append(cylinder(f"floor_collar{s}", 0.014, 0.004, "plastic_white", segments=14, bevel=0.0, center=(x, -0.02, 0)))
    # rust-ish drip stain near the TRV + scuff
    S.append(decal("drip", (-W / 2 + 0.05, -0.0385, z0 + 0.04), (0.012, 0.06), "y", "scuff_dark", seed=81, offset=0.0003))
    return assemble("furniture_radiator", S)


# ================================================================================================= KETTLE UNIT + MINI FRIDGE
@prop("furniture", "Kitchenette base unit 0.6 wide with dark laminate worktop (top surface z=0.905) and 0.06 upstand at the back. "
                   "drawer_1 at the top (slides -Y) and door_L below (hinge left, -Z opens). Back = +Y. Plinth 0.12.")
def furniture_kettle_unit():
    W, D, H = 0.60, 0.58, 0.905
    t = 0.018
    wt = 0.038
    plinth = 0.12
    S = []
    body_h = H - wt
    parts, info = carcass("k", W, D - t, body_h, role="laminate_white", edge="laminate_edge_white", plinth=plinth, plinth_recess=0.06)
    for p in parts:
        p.location.y += t / 2
    S += parts
    S.append(panel("worktop", (W + 0.02, D + 0.02, wt), "worktop_laminate", (0, -0.01, H - wt / 2), bevel=0.006, segments=3))
    S.append(panel("upstand", (W + 0.02, 0.018, 0.06), "worktop_laminate", (0, D / 2 - 0.009, H + 0.03), bevel=0.003))
    front_y = -D / 2
    gap = 0.003
    dh = 0.14
    dz = body_h - gap - dh
    d1 = drawer("drawer_1", W - 2 * gap, dh, 0, front_y, dz, D - 0.1, "laminate_white", "laminate_edge_white", handle="bar", handle_role="metal_chrome",
                handle_len=0.16)
    door_h = dz - gap - plinth - gap
    dl = door("door_L", W - 2 * gap, door_h, t, 0, front_y, plinth + gap, "L", "laminate_white", "laminate_edge_white", handle="bar",
              handle_role="metal_chrome", handle_len=0.16, handle_z=plinth + gap + door_h - 0.09)
    # wear: greasy patch near the handle, kick scuffs on plinth, chipped worktop corner
    S.append(decal("kick", (0.1, front_y + 0.06 + t / 2, 0.03), (0.12, 0.04), "y", "scuff_dark", seed=91))
    S.append(decal("chip", (W / 2 + 0.01, -D / 2 - 0.01 + 0.012, H - 0.002), (0.02, 0.018), "z", "scuff_light", sign=+1, seed=92, offset=0.0005))
    S.append(sticker("stk", (-W / 2, -0.1, 0.5), (0.08, 0.05), "x", "sticker_c", sign=-1, rot=math.radians(5)))
    return assemble("furniture_kettle_unit", S, [d1, dl])


@prop("furniture", "Table-top/under-counter mini fridge 0.5x0.5x0.85, white. door_L hinged on the LEFT (-Z opens), origin on hinge axis. "
                   "Top surface z=0.85. Back = +Y with condenser grille. 3 magnets + a sticker on the door.")
def furniture_mini_fridge():
    W, D, H = 0.50, 0.50, 0.85
    S = []
    body = panel("body", (W, D - 0.035, H - 0.03), "appliance_white", (0, 0.0175, 0.03 + (H - 0.03) / 2), bevel=0.012, segments=4)
    S.append(body)
    # top & bottom frame strips where the door sits
    for s in (-1, 1):
        S.append(cylinder(f"foot{s}a", 0.012, 0.03, "plastic_black", segments=12, bevel=0.002, center=(s * (W / 2 - 0.04), -D / 2 + 0.05, 0)))
        S.append(cylinder(f"foot{s}b", 0.012, 0.03, "plastic_black", segments=12, bevel=0.002, center=(s * (W / 2 - 0.04), D / 2 - 0.05, 0)))
    # condenser grille at the back
    S.append(panel("grille", (W - 0.08, 0.01, H - 0.12), "metal_dark", (0, D / 2 - 0.006, 0.07 + (H - 0.12) / 2), bevel=0.001))
    for i in range(9):
        z = 0.10 + i * (H - 0.20) / 8
        S.append(bar(f"cond{i}", (-W / 2 + 0.06, D / 2 - 0.0005, z), (W / 2 - 0.06, D / 2 - 0.0005, z), 0.003, "metal_dark", segments=8))
    S.append(panel("compressor", (0.18, 0.12, 0.16), "metal_dark", (0.08, D / 2 - 0.09, 0.03 + 0.08), bevel=0.01, segments=3))
    # door
    front_y = -D / 2
    dw, dh, dt = W - 0.004, H - 0.03 - 0.004, 0.035
    extras = []
    # magnets
    extras.append(lathe("mag_red", [(0, 0), (0.015, 0), (0.016, 0.005), (0.012, 0.008), (0, 0.008)], "magnet_red", segments=18, center=(-0.12, front_y, 0.60)))
    extras[-1].rotation_euler = RX90
    extras.append(panel("mag_yellow", (0.03, 0.006, 0.02), "magnet_yellow", (0.08, front_y - 0.003, 0.55), bevel=0.002))
    extras[-1].rotation_euler = (0, math.radians(14), 0)
    extras.append(lathe("mag_blue", [(0, 0), (0.011, 0), (0.013, 0.004), (0.008, 0.010), (0, 0.010)], "magnet_blue", segments=16, center=(0.14, front_y, 0.66)))
    extras[-1].rotation_euler = RX90
    extras.append(sticker("stk", (-0.05, front_y, 0.38), (0.11, 0.07), "y", "sticker_b", rot=math.radians(-7)))
    extras.append(sticker("stk2", (0.12, front_y, 0.30), (0.05, 0.05), "y", "sticker_a", rot=math.radians(20)))
    # peeling sticker edge: a tiny lighter triangle
    extras.append(decal("peel", (0.005, front_y, 0.415), (0.012, 0.012), "y", "scuff_light", seed=1, offset=0.0012))
    # energy label-ish worn patch and a scuff
    extras.append(decal("scuff", (0.18, front_y, 0.08), (0.05, 0.03), "y", "scuff_light", seed=2))
    dl = door("door_L", dw, dh, dt, 0, front_y, 0.032, "L", "appliance_white", None, handle=None, knuckles=False, extra=extras)
    # fridge door: vertical bar handle on the right side (free edge) - added as part of door: rebuild handle manually into door before join is complex,
    # so we add it to the door mesh now by joining
    hparts = []
    hx = W / 2 - 0.045
    hparts.append(panel("fh_bar", (0.022, 0.018, 0.30), "appliance_white", (hx, front_y - 0.02, 0.50), bevel=0.006, segments=3))
    hparts.append(panel("fh_top", (0.022, 0.03, 0.02), "appliance_white", (hx, front_y - 0.012, 0.66), bevel=0.004))
    hparts.append(panel("fh_bot", (0.022, 0.03, 0.02), "appliance_white", (hx, front_y - 0.012, 0.34), bevel=0.004))
    # hinge pins (top & bottom on the left)
    hparts.append(panel("hinge_top", (0.025, 0.04, 0.003), "metal_steel", (-W / 2 + 0.0125, front_y + 0.018, 0.032 + dh + 0.0015), bevel=0.0005))
    hparts.append(panel("hinge_bot", (0.025, 0.04, 0.003), "metal_steel", (-W / 2 + 0.0125, front_y + 0.018, 0.0305), bevel=0.0005))
    loc = Vector(dl.location)
    dl = join([dl] + hparts, "door_L")
    set_origin_to(dl, loc)
    return assemble("furniture_mini_fridge", S, [dl])


# ================================================================================================= STOOL / COAT HOOKS / SHOE RACK
@prop("furniture", "Round pine kitchen stool, seat top z=0.45, seat diameter 0.32, splayed legs (footprint 0.38).")
def furniture_stool():
    S = []
    H = 0.45
    seat = lathe("seat", [(0, H - 0.03), (0.14, H - 0.03), (0.16, H - 0.022), (0.16, H - 0.006), (0.15, H), (0.10, H - 0.004), (0, H - 0.006)],
                 "wood_light", segments=36)
    S.append(seat)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        top = Vector((math.cos(a) * 0.105, math.sin(a) * 0.105, H - 0.03))
        bot = Vector((math.cos(a) * 0.17, math.sin(a) * 0.17, 0))
        S.append(bar(f"leg{i}", bot, top, 0.016, "wood_light", segments=14, bevel=0.002))
        # stretcher between legs
        a2 = math.radians(45 + 90 * (i + 1))
        p1 = Vector((math.cos(a) * 0.145, math.sin(a) * 0.145, 0.17))
        p2 = Vector((math.cos(a2) * 0.145, math.sin(a2) * 0.145, 0.17))
        S.append(bar(f"str{i}", p1, p2, 0.009, "wood_light", segments=10))
        S.append(cylinder(f"glide{i}", 0.011, 0.004, "plastic_black", segments=10, bevel=0.0, center=(bot.x, bot.y, 0)))
    S.append(decal("scuff", (0.16 * 0.707, -0.16 * 0.707, H - 0.014), (0.03, 0.012), "y", "scuff_dark", seed=102))
    S.append(decal("scuff_leg", (-0.12, -0.12, 0.05), (0.012, 0.03), "y", "scuff_dark", seed=103, offset=0.0165))
    return assemble("furniture_stool", S)


@prop("furniture", "Wall coat-hook board 0.6 x 0.10, three chrome hooks protruding 0.07 toward -Y. Back (wall) = +Y. Mount at ~1.6 m.")
def furniture_coat_hooks():
    S = []
    W, Hb, T = 0.60, 0.10, 0.018
    S.append(profile_extrude("board", [(0.009, 0), (-0.009, 0), (-0.009, 0.082), (-0.005, 0.088), (-0.007, 0.094), (0.0, Hb), (0.009, Hb)], -W / 2, W / 2,
                             "wood_painted_white", bevel=0.001))
    for x in (-0.20, 0.0, 0.20):
        pts = [(x, -0.009, 0.048), (x, -0.035, 0.044), (x, -0.058, 0.040), (x, -0.072, 0.048), (x, -0.076, 0.062), (x, -0.070, 0.076)]
        S.append(wire(f"hook{x}", pts, 0.0055, "metal_chrome", n=7, segments=12))
        S.append(lathe(f"hook_ball{x}", [(0, -0.008), (0.006, -0.005), (0.008, 0.0), (0.006, 0.005), (0, 0.008)], "metal_chrome", segments=14,
                       center=(x, -0.070, 0.079)))
        S.append(wire(f"peg{x}", [(x, -0.009, 0.030), (x, -0.028, 0.026), (x, -0.038, 0.030)], 0.0045, "metal_chrome", n=5, segments=10))
        S.append(cylinder(f"plate{x}", 0.016, 0.003, "metal_chrome", segments=16, bevel=0.001, center=(x, -0.009, 0.040), origin="bottom"))
        S[-1].rotation_euler = RX90
    for x in (-0.26, 0.26):
        S.append(cylinder(f"screw{x}", 0.0035, 0.0015, "metal_steel", segments=8, bevel=0.0, center=(x, -0.009, 0.05)))
        S[-1].rotation_euler = RX90
    S.append(decal("chip", (0.12, -0.009, 0.098), (0.02, 0.006), "y", "scuff_dark", seed=111))
    return assemble("furniture_coat_hooks", S)


@prop("furniture", "Two-tier chrome shoe rack 0.7 x 0.30 x 0.34. Tier bar tops at z=0.07 and z=0.32.")
def furniture_shoe_rack():
    S = []
    W, D = 0.70, 0.30
    tiers = (0.07, 0.32)
    for s in (-1, 1):
        x = s * (W / 2 - 0.015)
        S.append(wire(f"frame{s}", rounded_polyline([(x, -D / 2, 0), (x, -D / 2, 0.34), (x, D / 2, 0.34), (x, D / 2, 0)], r=0.03, n=6), 0.008,
                      "metal_chrome", segments=12, smooth_path=False))
        S.append(bar(f"brace{s}", (x, -D / 2 + 0.01, tiers[0] - 0.01), (x, D / 2 - 0.01, tiers[0] - 0.01), 0.006, "metal_chrome", segments=10))
        for yy in (-D / 2, D / 2):
            S.append(cylinder(f"cap{s}{yy}", 0.011, 0.012, "plastic_black", segments=12, bevel=0.002, center=(x, yy, 0)))
    for z in tiers:
        for k in range(4):
            y = -D / 2 + 0.02 + k * (D - 0.04) / 3
            S.append(bar(f"bar{z}{k}", (-(W / 2 - 0.015), y, z - 0.005), ((W / 2 - 0.015), y, z - 0.005), 0.005, "metal_chrome", segments=10))
    return assemble("furniture_shoe_rack", S)


# ================================================================================================= LAMPS
@prop("furniture", "Anglepoise-style desk lamp, black metal. Base dia 0.16, reach ~0.45, head centre ~z=0.55. Child `head` (shade + bulb role bulb_warm), "
                   "origin at the head pivot; aim by rotating `head`. Light points forward/down (-Y, -Z).", views=("front34", "side"))
def furniture_lamp_desk():
    S = []
    S.append(lathe("base", [(0, 0), (0.08, 0), (0.082, 0.012), (0.075, 0.02), (0.03, 0.024), (0.03, 0.045), (0.0, 0.045)], "metal_dark", segments=36))
    S.append(decal("base_scuff", (0.05, -0.05, 0.0205), (0.025, 0.015), "z", "scuff_light", sign=+1, seed=121, offset=0.0003))
    # lower arm: two parallel bars from the pivot up and back
    p0 = Vector((0, 0, 0.045))
    elbow = Vector((0, 0.16, 0.36))
    for s in (-1, 1):
        S.append(bar(f"lower{s}", p0 + Vector((s * 0.012, 0, 0)), elbow + Vector((s * 0.012, 0, 0)), 0.004, "metal_dark", segments=10))
    S.append(bar("pivot0", (-0.02, 0, 0.05), (0.02, 0, 0.05), 0.007, "metal_dark", segments=12))
    S.append(bar("pivot1", (-0.02, 0.16, 0.36), (0.02, 0.16, 0.36), 0.007, "metal_dark", segments=12))
    # springs (two) between a spring post near the base and the lower arm
    sp0 = Vector((0, -0.03, 0.09))
    S.append(bar("spring_post", (0, 0, 0.07), (0, -0.03, 0.095), 0.004, "metal_dark", segments=8))
    for s in (-1, 1):
        a = sp0 + Vector((s * 0.014, 0, 0))
        b = Vector((s * 0.014, 0.085, 0.235))
        d = b - a
        L = d.length
        hx = helix(f"spring{s}", (0, 0, 0), 0.006, 0.006, L / 0.006, 0.0014, "metal_steel", seg_per_turn=12)
        hx.location = a
        hx.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        S.append(hx)
    # upper arm from elbow forward and up to head pivot
    hp = Vector((0, -0.18, 0.55))
    S.append(bar("upper", elbow, hp, 0.006, "metal_dark", segments=12))
    S.append(bar("upper_b", elbow + Vector((0, -0.02, 0.0)), elbow + Vector((0, -0.09, 0.09)), 0.004, "metal_dark", segments=8))
    S.append(bar("pivot2", hp - Vector((0.02, 0, 0)), hp + Vector((0.02, 0, 0)), 0.007, "metal_dark", segments=12))
    # cable: from base rear along the arms (loose)
    S.append(wire("cable", [(0, 0.03, 0.03), (0, 0.06, 0.16), (0, 0.17, 0.34), (0, 0.05, 0.47), (0, -0.14, 0.55)], 0.0025, "plastic_black", n=6, segments=8))
    S.append(wire("cable_out", [(0, 0.03, 0.03), (0, 0.08, 0.004), (0.1, 0.15, 0.002)], 0.0025, "plastic_black", n=6, segments=8))
    # switch on the cable
    S.append(panel("switch", (0.018, 0.05, 0.014), "plastic_black", (0.04, 0.11, 0.007), bevel=0.004))
    # head (child): shade = lathe pointing down/forward, built along -Z then tilted
    shade_prof = [(0.012, 0.0), (0.03, -0.015), (0.045, -0.06), (0.062, -0.13), (0.064, -0.135), (0.058, -0.133), (0.040, -0.08), (0.028, -0.02), (0.0, -0.01)]
    sh = lathe("shade", shade_prof, "metal_dark", segments=32)
    bulb = lathe("bulb", [(0, -0.12), (0.016, -0.115), (0.022, -0.10), (0.02, -0.08), (0.012, -0.07), (0.0, -0.065)], "bulb_warm", segments=16)
    bulb_hold = cylinder("holder", 0.013, 0.03, "plastic_black", segments=14, bevel=0.001, center=(0, 0, -0.07))
    head_arm = bar("head_fork", (0, 0, 0.0), (0, 0.0, -0.055), 0.0, "metal_dark") if False else None
    fork = wire("fork", [(0.02, 0.02, 0.0), (0.0, 0.03, -0.01), (-0.02, 0.02, 0.0)], 0.004, "metal_dark", n=4, segments=8)
    head = join([sh, bulb, bulb_hold, fork], "head")
    head.rotation_euler = (math.radians(-35), 0, 0)
    head.location = hp
    return assemble("furniture_lamp_desk", S, [head])


@prop("furniture", "Bedside lamp 0.42 high: glazed ceramic base (dia 0.14) + fabric drum shade (role lamp_shade, emissive in Unity), "
                   "bulb role bulb_warm inside, inline cord switch. Shade top z=0.42.", views=("front34", "back34"))
def furniture_lamp_bedside():
    S = []
    base = lathe("base", [(0, 0), (0.06, 0), (0.07, 0.01), (0.072, 0.05), (0.06, 0.12), (0.035, 0.17), (0.028, 0.21), (0.032, 0.235), (0.02, 0.24), (0.0, 0.24)],
                 "ceramic_blue", segments=36)
    S.append(base)
    S.append(cylinder("holder", 0.016, 0.045, "metal_brass", segments=16, bevel=0.001, center=(0, 0, 0.235)))
    S.append(cylinder("switch_knob", 0.004, 0.02, "metal_brass", segments=8, bevel=0.0, center=(0.016, 0, 0.26), origin="bottom"))
    S[-1].rotation_euler = RY90
    S.append(lathe("bulb", [(0, 0.28), (0.02, 0.285), (0.03, 0.31), (0.026, 0.34), (0.012, 0.355), (0.0, 0.357)], "bulb_warm", segments=16))
    # shade: slightly tapered drum, thin walls (outer + inner)
    shd = lathe("shade", [(0.11, 0.26), (0.11, 0.262), (0.10, 0.42), (0.098, 0.42), (0.108, 0.262), (0.108, 0.26)], "lamp_shade", segments=48)
    S.append(shd)
    # shade rings (wire) top and bottom + spider
    S.append(torus("ring_top", (0, 0, 0.418), 0.097, 0.0015, "metal_steel", seg_major=36, seg_minor=5))
    S.append(torus("ring_bot", (0, 0, 0.262), 0.107, 0.0015, "metal_steel", seg_major=36, seg_minor=5))
    for i in range(3):
        a = math.radians(90 + 120 * i)
        S.append(bar(f"spider{i}", (0, 0, 0.30), (math.cos(a) * 0.107, math.sin(a) * 0.107, 0.263), 0.0015, "metal_steel", segments=6))
    S.append(cylinder("spider_hub", 0.014, 0.01, "metal_steel", segments=12, bevel=0.0, center=(0, 0, 0.295)))
    # cord exiting the back of the base with inline switch
    S.append(wire("cord", [(0, 0.055, 0.02), (0, 0.10, 0.006), (0.05, 0.16, 0.003), (0.12, 0.17, 0.003)], 0.0022, "plastic_white", n=6, segments=8))
    S.append(panel("inline_switch", (0.016, 0.045, 0.012), "plastic_white", (0.045, 0.15, 0.006), bevel=0.004))
    S[-1].rotation_euler = (0, 0, math.radians(-40))
    return assemble("furniture_lamp_bedside", S)


@prop("furniture", "Arc floor lamp: marble-look round base (dia 0.30) at the origin, chrome arc sweeping 0.95 m forward (-Y) to a dome shade whose "
                   "rim is at z=1.40 (top z=1.6). Shade interior role bulb_warm. Place with the base behind the seat/bed and the shade over it.", views=("front34", "side"))
def furniture_lamp_floor():
    S = []
    S.append(lathe("base", [(0, 0), (0.15, 0), (0.15, 0.03), (0.14, 0.035), (0.035, 0.035), (0.0, 0.035)], "ceramic_white", segments=40))
    arc_pts = [(0, 0.0, 0.03), (0, 0.0, 0.60), (0, -0.02, 1.10), (0, -0.20, 1.45), (0, -0.55, 1.60), (0, -0.85, 1.55), (0, -0.95, 1.45)]
    S.append(wire("arc", arc_pts, 0.016, "metal_chrome", n=10, segments=16))
    S.append(cylinder("base_collar", 0.024, 0.06, "metal_chrome", segments=20, bevel=0.002, center=(0, 0, 0.035)))
    shade_c = Vector((0, -0.95, 1.45))
    dome = lathe("dome", [(0.018, 0.0), (0.09, -0.02), (0.16, -0.08), (0.20, -0.17), (0.205, -0.20), (0.195, -0.20), (0.19, -0.19), (0.15, -0.10),
                          (0.08, -0.03), (0.0, -0.02)], "metal_chrome", segments=40, center=shade_c)
    S.append(dome)
    S.append(lathe("bulb", [(0, -0.10), (0.025, -0.095), (0.03, -0.06), (0.018, -0.035), (0.0, -0.03)], "bulb_warm", segments=16, center=shade_c))
    S.append(cylinder("lamp_holder", 0.014, 0.03, "plastic_black", segments=12, bevel=0.0, center=shade_c + Vector((0, 0, -0.05))))
    S.append(wire("cable", [(0, 0.024, 0.04), (0, 0.10, 0.01), (0.15, 0.25, 0.003), (0.4, 0.3, 0.003)], 0.003, "plastic_black", n=6, segments=8))
    S.append(panel("foot_switch", (0.03, 0.07, 0.02), "plastic_black", (0.16, 0.26, 0.01), bevel=0.005))
    S[-1].rotation_euler = (0, 0, math.radians(30))
    return assemble("furniture_lamp_floor", S)


@prop("furniture", "Paper pendant shade dia 0.35, cord + ceiling rose. Total drop 0.60 from the rose (top, z=0.60) to the shade bottom (z=0). "
                   "Place at origin z = ceiling height - 0.60. Shade role lamp_shade; bulb role bulb_warm.", views=("front34", "front"))
def furniture_ceiling_light():
    S = []
    drop = 0.60
    # paper lantern: ribbed sphere-ish shade (oblate)
    prof = []
    R, hz = 0.175, 0.145
    for i in range(1, 15):
        t = math.pi * i / 15
        prof.append((R * math.sin(t) * (1.0 + 0.004 * (i % 2)), 0.16 - hz * math.cos(t)))
    prof = [(0.045, 0.16 - hz * 0.98)] + prof + [(0.06, 0.16 + hz * 0.98)]
    shade = lathe("shade", prof, "lamp_shade", segments=40)
    S.append(shade)
    # wire ribs (horizontal thin rings) to sell the paper-lantern look
    for i in range(2, 13, 2):
        t = math.pi * i / 15
        S.append(torus(f"rib{i}", (0, 0, 0.16 - hz * math.cos(t)), R * math.sin(t) + 0.0015, 0.001, "metal_steel", seg_major=40, seg_minor=4))
    S.append(lathe("bulb", [(0, 0.09), (0.03, 0.10), (0.032, 0.16), (0.02, 0.20), (0.014, 0.22), (0.0, 0.22)], "bulb_warm", segments=18))
    S.append(cylinder("holder", 0.017, 0.045, "plastic_white", segments=14, bevel=0.001, center=(0, 0, 0.215)))
    S.append(cylinder("shade_ring", 0.045, 0.006, "plastic_white", segments=20, bevel=0.001, center=(0, 0, 0.16 + hz * 0.98 - 0.003)))
    S.append(bar("cord", (0, 0, 0.26), (0, 0, drop - 0.02), 0.003, "plastic_white", segments=10))
    S.append(lathe("rose", [(0, drop - 0.03), (0.02, drop - 0.03), (0.04, drop - 0.012), (0.042, drop), (0.0, drop)], "plastic_white", segments=24))
    return assemble("furniture_ceiling_light", S)


@prop("furniture", "String of 20 warm fairy-light bulbs on a 2.2 m catenary (ends 0.28 above the lowest point, which is the origin). "
                   "Pin the ends at x=+-1.1, z=+0.28. Bulbs role bulb_warm (emissive).", views=("front", "front34"))
def furniture_fairy_lights():
    S = []
    L, sag = 2.2, 0.28
    # catenary: a*(cosh(x/a)-1) = sag at x=L/2 ; bisection for a
    lo, hi = 0.05, 50.0
    for _ in range(60):
        a = (lo + hi) / 2
        if a * (math.cosh(L / 2 / a) - 1) > sag:
            lo = a
        else:
            hi = a
    a = (lo + hi) / 2
    pts = [Vector((x, 0, a * (math.cosh(x / a) - 1) + 0.02)) for x in [-L / 2 + i * L / 60 for i in range(61)]]
    S.append(wire("wire", pts, 0.0012, "wire_green", smooth_path=False, segments=6))
    rnd = random.Random(7)
    for i in range(20):
        x = -L / 2 + 0.07 + i * (L - 0.14) / 19
        z = a * (math.cosh(x / a) - 1) + 0.02
        slope = math.sinh(x / a)
        ang = math.atan(slope)
        tilt = rnd.uniform(-0.3, 0.3)
        sock = cylinder(f"sock{i}", 0.0035, 0.012, "wire_green", segments=8, bevel=0.0, center=(0, 0, -0.012))
        bulb = lathe(f"bulb{i}", [(0, -0.012), (0.004, -0.013), (0.0065, -0.02), (0.0055, -0.03), (0.0, -0.034)], "bulb_warm", segments=12)
        for o in (sock, bulb):
            o.location = (x, 0, z)
            o.rotation_euler = (tilt, -ang * 0.6, 0)
        S += [sock, bulb]
    S.append(cylinder("plug_end", 0.006, 0.03, "wire_green", segments=8, bevel=0.001, center=(L / 2 + 0.003, 0, sag + 0.02 - 0.015)))
    S[-1].rotation_euler = RY90
    return assemble("furniture_fairy_lights", S)


# ================================================================================================= WINDOW
@prop("furniture", "uPVC window 1.04 x 1.62 (frame), origin at frame bottom centre. Frame depth 0.07 (y -0.035..+0.035); room side = -Y. "
                   "Inner window board (sill) projects to y=-0.20 at z=0.0..0.025, width 1.14. Right casement opens; child `glass` (role glass_clear) "
                   "is both panes. Place in a wall opening 1.04 x 1.62 with the frame centred in the wall thickness.", views=("front34", "back34"))
def furniture_window_frame():
    S = []
    W, H, FD = 1.04, 1.62, 0.07
    fw = 0.065
    # outer frame (rectangular profile with a small internal step)
    prof = [(0, -FD / 2), (fw, -FD / 2), (fw, -0.010), (fw - 0.012, -0.010), (fw - 0.012, 0.012), (fw, 0.012), (fw, FD / 2), (0, FD / 2)]
    S.append(frame_sweep("frame", W, H, prof, "upvc_white", center=(0, 0, H / 2), bevel=0.002))
    # mullion
    mx = -0.03
    S.append(panel("mullion", (0.06, FD, H - 2 * fw + 0.002), "upvc_white", (mx, 0, H / 2), bevel=0.002))
    # casement sashes (left fixed glazed directly, right opening sash)
    lw = (mx - 0.03) - (-W / 2 + fw)      # left opening width
    rw = (W / 2 - fw) - (mx + 0.03)
    lcx = (-W / 2 + fw + mx - 0.03) / 2
    rcx = (mx + 0.03 + W / 2 - fw) / 2
    ih = H - 2 * fw
    # right sash frame
    sw = 0.055
    sprof = [(0, -0.030), (sw, -0.030), (sw, 0.028), (0, 0.028)]
    S.append(frame_sweep("sash_R", rw - 0.006, ih - 0.006, sprof, "upvc_white", center=(rcx, 0.0, H / 2), bevel=0.0025))
    # glazing beads (inner strip) on both openings
    bprof = [(0, -0.012), (0.014, -0.012), (0.016, -0.004), (0.016, 0.0), (0, 0.0)]
    S.append(frame_sweep("bead_R", rw - 0.006 - 2 * sw + 0.002, ih - 0.006 - 2 * sw + 0.002, bprof, "upvc_white", center=(rcx, 0.0, H / 2)))
    S.append(frame_sweep("bead_L", lw + 0.002, ih + 0.002, bprof, "upvc_white", center=(lcx, 0.0, H / 2)))
    # glass panes (child)
    gl = panel("glass_L", (lw - 0.02, 0.004, ih - 0.02), "glass_clear", (lcx, 0.006, H / 2), bevel=0.0)
    gr = panel("glass_R", (rw - 0.006 - 2 * sw - 0.02, 0.004, ih - 0.006 - 2 * sw - 0.02), "glass_clear", (rcx, 0.006, H / 2), bevel=0.0)
    glass = join([gl, gr], "glass")
    set_origin_to(glass, (0, 0, 0))
    # handle on the right sash (white lever, room side)
    hx = rcx - (rw - 0.006) / 2 + sw / 2
    S.append(panel("handle_base", (0.03, 0.012, 0.07), "upvc_white", (hx, -0.030 - 0.006, H / 2), bevel=0.003))
    S.append(wire("handle_lever", [(hx, -0.042, H / 2), (hx, -0.062, H / 2 + 0.005), (hx, -0.066, H / 2 - 0.05), (hx, -0.062, H / 2 - 0.12)], 0.007, "upvc_white", n=6, segments=12))
    # trickle vent on the top frame member (room side) + friction hinges hint
    S.append(panel("trickle", (0.30, 0.01, 0.018), "upvc_white", (rcx, -FD / 2 - 0.005, H - fw / 2), bevel=0.002))
    for i in range(8):
        S.append(decal(f"tv_slot{i}", (rcx - 0.12 + i * 0.034, -FD / 2 - 0.0101, H - fw / 2), (0.02, 0.005), "y", "scuff_dark", irregular=False, offset=0.0))
    # inner window board (sill) - timber, painted, nosing rounded
    S.append(panel("sill_board", (W + 0.10, 0.235, 0.025), "wood_painted_white", (0, 0.035 - 0.235 / 2, 0.0125), bevel=0.006, segments=3))
    # external sill (sloped) on the +Y side, small
    S.append(panel("ext_sill", (W + 0.06, 0.09, 0.025), "upvc_white", (0, FD / 2 + 0.045, 0.012), bevel=0.003))
    S[-1].rotation_euler = (math.radians(-6), 0, 0)
    # grime: dirt line on the sill corners, condensation stain at the bottom of the glass bead
    S.append(decal("sill_dirt", (-0.45, -0.17, 0.0255), (0.06, 0.04), "z", "scuff_dark", sign=+1, seed=151, offset=0.0003))
    S.append(decal("sill_dirt2", (0.40, -0.19, 0.0255), (0.04, 0.03), "z", "scuff_light", sign=+1, seed=152, offset=0.0003))
    return assemble("furniture_window_frame", S, [glass])


@prop("furniture", "Curtain pole 1.40 m (black metal) with 2 brackets, finials and 12 rings. Pole axis at z=0.065 above origin, y=-0.085 from the "
                   "wall (wall face at y=+0.0 behind the bracket plates). Mount ~0.12 above the window frame.", views=("front34", "back34"))
def furniture_window_curtain_rail():
    S = []
    L = 1.40
    pz, py = 0.065, -0.085
    S.append(bar("pole", (-L / 2 + 0.03, py, pz), (L / 2 - 0.03, py, pz), 0.014, "metal_dark", segments=18))
    for s in (-1, 1):
        x = s * (L / 2 - 0.03)
        S.append(lathe(f"finial{s}", [(0, 0), (0.016, 0), (0.024, 0.012), (0.026, 0.03), (0.018, 0.045), (0.02, 0.05), (0.008, 0.06), (0, 0.065)],
                       "metal_dark", segments=20, center=(x, py, pz)))
        S[-1].rotation_euler = RY90 if s > 0 else RYm90
    for x in (-0.50, 0.50):
        S.append(panel(f"plate{x}", (0.05, 0.006, 0.09), "metal_dark", (x, -0.003, 0.045), bevel=0.002))
        S.append(bar(f"brk{x}", (x, -0.006, 0.045), (x, py + 0.0, 0.045), 0.008, "metal_dark", segments=10))
        S.append(bar(f"brk_up{x}", (x, py, 0.042), (x, py, pz - 0.014), 0.008, "metal_dark", segments=10))
        S.append(torus(f"brk_ring{x}", (x, py, pz), 0.0185, 0.004, "metal_dark", seg_major=24, seg_minor=8, axis="x"))
    rnd = random.Random(3)
    xs = sorted([rnd.uniform(-0.62, -0.08) for _ in range(6)] + [rnd.uniform(0.08, 0.62) for _ in range(6)])
    for i, x in enumerate(xs):
        S.append(torus(f"ring{i}", (x, py, pz), 0.021, 0.0035, "metal_dark", seg_major=24, seg_minor=8, axis="x"))
        S.append(torus(f"eye{i}", (x, py, pz - 0.027), 0.005, 0.0015, "metal_dark", seg_major=12, seg_minor=5, axis="x"))
    return assemble("furniture_window_curtain_rail", S)


# ================================================================================================= DOOR
@prop("furniture", "Internal door: frame+architrave 0.83 x 2.04 (origin bottom centre of the frame, wall centre at y=0, room side -Y). "
                   "Child `leaf` (0.76 x 1.98 x 0.04, 4 recessed panels, lever handles) hinged on the LEFT, origin on the hinge axis; "
                   "opens AWAY from the room (+Y) with positive Z rotation. Fits a wall 0.10 thick.", views=("front34", "back34"))
def furniture_door_frame_internal():
    S = []
    W, H = 0.83, 2.04
    lining_t, lining_d = 0.03, 0.11
    lw = 0.762
    lh = 1.981
    # lining: two jambs + head (open bottom)
    jx = lw / 2 + 0.003 + lining_t / 2
    for s in (-1, 1):
        S.append(panel(f"jamb{s}", (lining_t, lining_d, H - 0.02), "wood_painted_white", (s * jx, 0, (H - 0.02) / 2), bevel=0.002))
    S.append(panel("head", (2 * jx + lining_t, lining_d, lining_t), "wood_painted_white", (0, 0, H - 0.02 - lining_t / 2 + 0.0), bevel=0.002))
    # door stops
    for s in (-1, 1):
        S.append(panel(f"stop{s}", (0.012, 0.03, H - 0.06), "wood_painted_white", (s * (jx - lining_t / 2 - 0.006), 0.035, (H - 0.06) / 2), bevel=0.001))
    S.append(panel("stop_top", (2 * jx - lining_t, 0.03, 0.012), "wood_painted_white", (0, 0.035, H - 0.02 - lining_t - 0.006), bevel=0.001))
    # architraves both sides: U-shaped moulding (two legs + head), stepped profile faked with 2 layers
    aw = 0.065
    for side in (-1, 1):   # -1 room side (-Y), +1 other side
        yb = side * (lining_d / 2)
        for s in (-1, 1):
            x = s * (jx + lining_t / 2 + aw / 2 - 0.006)
            S.append(panel(f"arch_leg{side}{s}", (aw, 0.018, H - 0.0), "wood_painted_white", (x, yb + side * 0.009, (H) / 2 + 0.0 - 0.0), bevel=0.002))
            S.append(panel(f"arch_leg2{side}{s}", (aw * 0.45, 0.008, H - 0.0), "wood_painted_white", (x - s * aw * 0.2, yb + side * 0.022, H / 2), bevel=0.002))
        hw = 2 * (jx + lining_t / 2 + aw - 0.006)
        S.append(panel(f"arch_head{side}", (hw, 0.018, aw), "wood_painted_white", (0, yb + side * 0.009, H - aw / 2 + 0.0), bevel=0.002))
        S.append(panel(f"arch_head2{side}", (hw - 2 * aw * 0.55, 0.008, aw * 0.45), "wood_painted_white", (0, yb + side * 0.022, H - aw / 2 - aw * 0.2), bevel=0.002))
    # ---- leaf (child)
    lt = 0.040
    st = 0.11     # stile width
    L = []
    cx = 0.0
    for s in (-1, 1):
        L.append(panel(f"stile{s}", (st, lt, lh), "wood_painted_white", (cx + s * (lw / 2 - st / 2), 0, 0.01 + lh / 2), bevel=0.002))
    rails = [(0.01, 0.20, "bottom"), (0.01 + lh - 0.11, 0.11, "top"), (0.01 + 0.20 + 0.52, 0.11, "lock"), ]
    for z0, hgt, nm in rails:
        L.append(panel(f"rail_{nm}", (lw - 2 * st + 0.002, lt, hgt), "wood_painted_white", (cx, 0, z0 + hgt / 2), bevel=0.002))
    # muntin (vertical centre) across both panel zones
    L.append(panel("muntin", (0.09, lt, lh - 0.20 - 0.11 - 0.11 + 0.002), "wood_painted_white", (cx, 0, 0.01 + 0.20 + (lh - 0.20 - 0.11) / 2), bevel=0.002))
    # 4 recessed panels (thin) + bolection-ish bevel strips
    pw = (lw - 2 * st - 0.09) / 2
    zones = [(0.01 + 0.20, 0.52), (0.01 + 0.20 + 0.52 + 0.11, lh - 0.20 - 0.52 - 0.11 - 0.11)]
    for s in (-1, 1):
        px = cx + s * (0.045 + pw / 2)
        for (z0, hgt) in zones:
            L.append(panel(f"panel{s}{z0}", (pw + 0.004, 0.012, hgt + 0.004), "wood_painted_white", (px, 0, z0 + hgt / 2), bevel=0.0))
            # inner bevel strip frame (fielded panel look)
            bp = [(0, -0.006), (0.03, -0.018), (0.03, 0.018), (0, 0.006)]
            L.append(frame_sweep(f"field{s}{z0}", pw + 0.002, hgt + 0.002, bp, "wood_painted_white", center=(px, 0, z0 + hgt / 2)))
    # handles both sides (lever on round rose), latch plate, keyhole escutcheon
    hz = 1.00
    hx_ = cx + lw / 2 - 0.06
    for side in (-1, 1):
        y = side * lt / 2
        rose = cylinder(f"rose{side}", 0.026, 0.008, "metal_steel", segments=24, bevel=0.001, center=(hx_, y, hz))
        rose.rotation_euler = RX90 if side < 0 else RXm90
        L.append(rose)
        L.append(bar(f"spindle{side}", (hx_, y, hz), (hx_, y + side * 0.055, hz), 0.009, "metal_steel", segments=14))
        L.append(wire(f"lever{side}", [(hx_, y + side * 0.055, hz), (hx_ - 0.02, y + side * 0.06, hz), (hx_ - 0.09, y + side * 0.06, hz - 0.006), (hx_ - 0.12, y + side * 0.055, hz - 0.01)],
                      0.008, "metal_steel", n=6, segments=14))
        L.append(cylinder(f"escut{side}", 0.012, 0.004, "metal_steel", segments=16, bevel=0.0, center=(hx_, y, hz - 0.075)))
        L[-1].rotation_euler = RX90 if side < 0 else RXm90
    L.append(panel("latch_plate", (0.004, 0.025, 0.07), "metal_steel", (cx + lw / 2, 0, hz), bevel=0.0))
    # hinges (3) on the left edge, knuckles visible on the +Y side (door opens away)
    hinge_x = cx - lw / 2
    for z in (0.23, 1.00, 1.80):
        L.append(cylinder(f"hinge{z}", 0.0065, 0.10, "metal_steel", segments=12, bevel=0.001, center=(hinge_x - 0.002, lt / 2 + 0.003, z - 0.05)))
        L.append(panel(f"hinge_leaf{z}", (0.03, 0.002, 0.10), "metal_steel", (hinge_x + 0.013, lt / 2 + 0.001, z), bevel=0.0))
    # wear: scuff near the bottom (kicked), grubby patch around the handle
    L.append(decal("kick", (cx + 0.1, -lt / 2, 0.12), (0.10, 0.05), "y", "scuff_dark", seed=161))
    L.append(decal("grub", (hx_ - 0.07, -lt / 2, hz + 0.02), (0.10, 0.09), "y", "scuff_light", seed=162))
    leaf = join(L, "leaf")
    set_origin_to(leaf, (hinge_x - 0.002, lt / 2 + 0.003, 0.0))
    return assemble("furniture_door_frame_internal", S, [leaf])


# ================================================================================================= TRIM & WALL THINGS
@prop("furniture", "1.0 m skirting board, 0.12 high, 0.018 thick, ogee top. Back (wall) = +Y at y=+0.009.", views=("front34", "front"))
def furniture_skirting_run():
    prof = [(0.009, 0), (-0.009, 0), (-0.009, 0.090), (-0.004, 0.098), (-0.007, 0.106), (-0.002, 0.114), (0.0, 0.12), (0.009, 0.12)]
    S = [profile_extrude("skirting", prof, -0.5, 0.5, "wood_painted_white", bevel=0.001)]
    S.append(decal("scuff", (-0.2, -0.009, 0.03), (0.08, 0.03), "y", "scuff_dark", seed=171))
    S.append(decal("scuff2", (0.3, -0.009, 0.015), (0.05, 0.02), "y", "scuff_light", seed=172))
    return assemble("furniture_skirting_run", S)


def _picture(name, w, h, frame_role, prof, print_role, mount=0.0, frame_w=0.03, depth=0.025):
    S = []
    S.append(frame_sweep("frame", w, h, prof, frame_role, center=(0, 0, h / 2), bevel=0.0015))
    S.append(panel("backboard", (w - 2 * frame_w + 0.01, 0.003, h - 2 * frame_w + 0.01), "hardboard_back", (0, depth / 2 - 0.0015 - 0.002, h / 2), bevel=0.0))
    y_print = -0.004
    if mount > 0:
        S.append(plane_quad("mount", (0, y_print + 0.0005, h / 2), (w - 2 * frame_w + 0.004, h - 2 * frame_w + 0.004), "y", "paper_white"))
    S.append(plane_quad("print", (0, y_print, h / 2), (w - 2 * frame_w - 2 * mount, h - 2 * frame_w - 2 * mount), "y", print_role))
    # hanging cord + hook on the back
    S.append(wire("cord", [(-w / 2 + frame_w, depth / 2 + 0.002, h * 0.6), (0, depth / 2 + 0.004, h * 0.8), (w / 2 - frame_w, depth / 2 + 0.002, h * 0.6)], 0.0012, "plastic_black", n=6, segments=6))
    return assemble(name, S)


@prop("furniture", "Framed print A 0.40 x 0.50 (portrait): light oak frame with white mount; print plane role print_a. Back (wall) = +Y.")
def furniture_picture_frame_a():
    prof = [(0, -0.012), (0.012, -0.015), (0.03, -0.008), (0.03, 0.012), (0, 0.012)]
    return _picture("furniture_picture_frame_a", 0.40, 0.50, "wood_light", prof, "print_a", mount=0.04, frame_w=0.03, depth=0.024)


@prop("furniture", "Framed print B 0.30 x 0.40 (portrait): thin black frame, no mount; print plane role print_b. Back (wall) = +Y.")
def furniture_picture_frame_b():
    prof = [(0, -0.010), (0.012, -0.010), (0.012, 0.010), (0, 0.010)]
    return _picture("furniture_picture_frame_b", 0.30, 0.40, "plastic_black", prof, "print_b", mount=0.0, frame_w=0.012, depth=0.02)


@prop("furniture", "Framed print C 0.50 x 0.35 (landscape): chunky dark-wood stepped frame; print plane role print_c. Back (wall) = +Y.")
def furniture_picture_frame_c():
    prof = [(0, -0.022), (0.012, -0.03), (0.022, -0.03), (0.03, -0.02), (0.042, -0.014), (0.045, -0.004), (0.045, 0.015), (0, 0.015)]
    return _picture("furniture_picture_frame_c", 0.50, 0.35, "wood_dark", prof, "print_c", mount=0.0, frame_w=0.045, depth=0.03)


@prop("furniture", "Round wall clock dia 0.30, depth 0.045, black plastic rim, paper face (role clock_face), hands at 10:10. Back (wall) = +Y.",
      views=("front", "front34"))
def furniture_wall_clock():
    S = []
    R = 0.15
    rim = lathe("rim", [(0.12, 0), (0.14, 0.0), (0.15, 0.012), (0.15, 0.032), (0.145, 0.040), (0.13, 0.044), (0.128, 0.040), (0.128, 0.012), (0.12, 0.010)],
                "plastic_black", segments=48, center=(0, 0, 0))
    rim.rotation_euler = RXm90
    rim.location = (0, 0.0, R)
    S.append(rim)
    face = cylinder("face", 0.129, 0.002, "clock_face", segments=48, bevel=0.0, center=(0, 0, R), origin="center")
    face.rotation_euler = RX90
    face.location = (0, -0.009, R)
    S.append(face)
    for i in range(12):
        a = math.radians(90 - 30 * i)
        big = i % 3 == 0
        m = panel(f"mark{i}", (0.006 if big else 0.003, 0.002, 0.018 if big else 0.010), "plastic_black",
                  (math.cos(a) * 0.112, -0.011, R + math.sin(a) * 0.112), bevel=0.0)
        m.rotation_euler = (0, -(a - math.pi / 2), 0)
        S.append(m)
    # hands at 10:10
    for ang_deg, length, wdt, yoff in ((120, 0.075, 0.008, -0.013), (60, 0.105, 0.006, -0.015)):
        a = math.radians(ang_deg)
        hnd = panel(f"hand{ang_deg}", (wdt, 0.0015, length), "plastic_black", (0, 0, 0), bevel=0.0)
        bmh = bmesh.new(); bmh.from_mesh(hnd.data)
        for v in bmh.verts:
            v.co.z += length / 2 - 0.012
            if v.co.z > length * 0.6:
                v.co.x *= 0.4
        bmh.to_mesh(hnd.data); bmh.free()
        hnd.rotation_euler = (0, -(a - math.pi / 2), 0)
        hnd.location = (0, yoff, R)
        S.append(hnd)
    sec = panel("second", (0.0015, 0.001, 0.11), "plastic_red", (0, 0, 0), bevel=0.0)
    bmh = bmesh.new(); bmh.from_mesh(sec.data)
    for v in bmh.verts:
        v.co.z += 0.11 / 2 - 0.02
    bmh.to_mesh(sec.data); bmh.free()
    sec.rotation_euler = (0, math.radians(-150), 0)
    sec.location = (0, -0.0165, R)
    S.append(sec)
    S.append(cylinder("pin", 0.005, 0.004, "plastic_black", segments=12, bevel=0.0, center=(0, -0.0145, R), origin="center"))
    S[-1].rotation_euler = RX90
    # glass dome (slightly domed disc)
    S.append(lathe("glass", [(0.0, 0.0), (0.09, -0.004), (0.127, -0.0), (0.127, 0.001), (0.09, -0.003), (0.0, 0.001)], "glass_clear", segments=48))
    S[-1].rotation_euler = RX90
    S[-1].location = (0, -0.033, R)
    S.append(panel("battery_box", (0.05, 0.012, 0.06), "plastic_black", (0, 0.006, R - 0.02), bevel=0.002))
    S.append(torus("hanger_eye", (0, 0.004, R + 0.08), 0.006, 0.0015, "metal_steel", seg_major=12, seg_minor=5, axis="y"))
    return assemble("furniture_wall_clock", S)


@prop("furniture", "Framed rectangular wall mirror 0.50 x 0.70 (portrait), white painted wood frame 0.045 wide, mirror plane role mirror_glass at y=-0.005. "
                   "Back (wall) = +Y.", views=("front34", "back34"))
def furniture_mirror_wall():
    S = []
    w, h = 0.50, 0.70
    prof = [(0, -0.018), (0.01, -0.024), (0.03, -0.022), (0.045, -0.010), (0.045, 0.012), (0, 0.012)]
    S.append(frame_sweep("frame", w, h, prof, "wood_painted_white", center=(0, 0, h / 2), bevel=0.0015))
    S.append(panel("backboard", (w - 0.08, 0.004, h - 0.08), "hardboard_back", (0, 0.009, h / 2), bevel=0.0))
    S.append(plane_quad("mirror", (0, -0.005, h / 2), (w - 0.086, h - 0.086), "y", "mirror_glass"))
    S.append(decal("chip", (-w / 2 + 0.02, -0.0245, 0.08), (0.015, 0.03), "y", "scuff_dark", seed=181))
    S.append(decal("speck", (0.1, -0.0052, 0.2), (0.012, 0.01), "y", "scuff_light", seed=182, offset=0.0003))
    for x in (-0.15, 0.15):
        S.append(panel(f"dplate{x}", (0.02, 0.002, 0.05), "metal_steel", (x, 0.0115, h * 0.8), bevel=0.0))
    return assemble("furniture_mirror_wall", S)


# ================================================================================================= RUNNER
def run():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    views_override = None
    names = []
    for a in argv:
        if a.startswith("views="):
            views_override = tuple(a.split("=", 1)[1].split(","))
        else:
            names.append(a if a.startswith("furniture_") else "furniture_" + a)
    todo = names or list(BUILDERS.keys())
    manifest = []
    if os.path.exists(MANIFEST):
        try:
            manifest = json.load(open(MANIFEST))
        except Exception:
            manifest = []
    manifest = [m for m in manifest if m["name"] not in todo]
    results = []
    for nm in todo:
        fn, category, notes, variant_of, views = BUILDERS[nm]
        print(f"\n===== building {nm}")
        clean_scene()
        try:
            root = fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"FAILED {nm}: {e}")
            continue
        glass_preview_alpha()
        lo, hi = dims(root)
        tris = tri_count(root)
        roles = roles_used(root)
        path = export_fbx(root, FAMILY, nm)
        pv = preview(root, nm, views=views_override or views, size=(800, 600))
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        entry = dict(name=nm, file=rel, category=category, dims_m=[round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)],
                     tris=tris, roles=roles, variant_of=variant_of,
                     notes=notes + f" Origin offset from bbox: x{round((lo.x + hi.x) / 2, 3)} y{round((lo.y + hi.y) / 2, 3)} zmin{round(lo.z, 3)}.",
                     children=[c.name for c in root.children] if root.type == "EMPTY" else [])
        manifest.append(entry)
        results.append((nm, tris, entry["dims_m"], pv))
        print(f"      {nm}: tris={tris} dims={entry['dims_m']} roles={roles}")
    manifest = [m for m in manifest if m["name"] != "_meta"]
    manifest.sort(key=lambda m: m["name"])
    manifest.append(dict(name="_meta", file="", category="meta", dims_m=[0, 0, 0], tris=0, roles=[], variant_of=None,
                         notes="Family-level info. new_roles = roles added by this family: role -> [rgb, roughness, metallic] fallback. "
                               "Emissive in Unity: bulb_warm, lamp_shade (soft). mirror_glass = mirror. print_a/b/c = framed print textures. "
                               "scuff_dark/scuff_light/sticker_* are thin decal polygons 0.8 mm off the surface.",
                         new_roles={k: [list(v[0]), v[1], v[2]] for k, v in NEW_ROLES.items()}))
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=1)
    new_roles = sorted(NEW_ROLES.keys())
    print("\nNEW_ROLES:", new_roles)
    for r in results:
        print("RESULT", r)


if __name__ == "__main__":
    run()
