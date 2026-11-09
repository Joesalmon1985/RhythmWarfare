"""exterior.py - `exterior` family: the two street views seen from the bedsit windows + skyline backdrop.

Run:  "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P Art/Source/blender/exterior.py -- [names|all]
Names: shop_corner terrace_a terrace_b shop_props street_lamp pavement_kerb parked_car_a parked_car_b
       club_building club_neon_sign club_queue_barriers club_posters_hoarding club_speaker_wall club_props
       arch_bridge_backdrop skyline_backdrop tree_street

Conventions: 1 unit = 1 m, FRONT faces -Y, origin at ground-level front-centre (buildings) / bottom centre (props).
"""
import bpy, math, random, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import bsk, lib_exterior
importlib.reload(bsk)
importlib.reload(lib_exterior)
from lib_exterior import *   # noqa

FAMILY = "exterior"
EAVES = 7.2          # shared eaves height for the shop street so the terrace roofline is continuous
RIDGE = 9.2


# ================================================================================================= shared pieces

def shell(mb, w, depth, h, role="brick", x_shrink=0.0):
    """Building body behind the facade skin (no front face, no bottom)."""
    mb.box((-w / 2, 0.0, 0.0), (w / 2 - x_shrink, depth, h), role, skip=("-y", "-z"))


def alarm_box(mb, tf, u, z):
    mb.box((u, z, 0.0), (u + 0.30, z + 0.24, 0.10), "sign_yellow", tf, inset=0.01, inset_face="+z")
    mb.box((u + 0.03, z + 0.03, 0.10), (u + 0.09, z + 0.07, 0.112), "led_red", tf)


def satellite_dish(mb, tf, u, z):
    mb.box((u - 0.03, z, 0.0), (u + 0.03, z + 0.5, 0.06), "metal_painted_grey", tf)
    mb.bar(tf((u, z + 0.45, 0.06)), tf((u + 0.05, z + 0.62, 0.42)), 0.025, "metal_painted_grey")
    dtf = seg_tf(tf((u, z + 0.65, 0.12)), tf((u, z + 0.95, 0.62)))
    mb.lathe([(0.0, 0.0), (0.22, 0.0), (0.30, 0.05)], "plastic_grey", 16, dtf, smooth=True, cap_bottom=False, cap_top=False)
    mb.lathe([(0.29, 0.052), (0.21, 0.004), (0.0, 0.004)], "plastic_grey", 16, dtf, smooth=True, cap_bottom=False, cap_top=False)
    mb.bar(dtf((0, -0.25, 0.0)), dtf((0, -0.05, 0.42)), 0.02, "metal_painted_grey")
    mb.box((-0.03, -0.03, 0.40), (0.03, 0.03, 0.48), "plastic_grey", dtf)


def shelf_unit(mb, u0, u1, d_back, z0, h, n_shelves, depth, seed, face_dir=-1, role="metal_painted_grey"):
    """Shop shelving against a wall (facade-local coords: u along, d depth negative into the shop).
    face_dir=-1 -> products face the window (towards +d)."""
    rnd = random.Random(seed)
    d_front = d_back + depth if face_dir < 0 else d_back - depth
    dlo, dhi = min(d_back, d_front), max(d_back, d_front)
    mb.box((u0, z0, dlo), (u0 + 0.03, z0 + h, dhi), role)
    mb.box((u1 - 0.03, z0, dlo), (u1, z0 + h, dhi), role)
    mb.box((u0, z0, dlo - 0.005), (u1, z0 + h, dlo + 0.0), role)   # back panel
    roles = ["product_a", "product_b", "product_c", "product_d", "product_e"]
    for s in range(n_shelves):
        zs = z0 + 0.1 + s * (h - 0.2) / max(1, n_shelves - 1)
        mb.box((u0, zs, dlo), (u1, zs + 0.025, dhi), role)
        if s == n_shelves - 1:
            continue
        u = u0 + 0.05
        while u < u1 - 0.1:
            bw = rnd.uniform(0.06, 0.14)
            bh = rnd.uniform(0.10, 0.26)
            bd = rnd.uniform(0.05, min(0.18, depth - 0.04))
            if u + bw > u1 - 0.04:
                break
            r = rnd.choice(roles)
            mb.box((u, zs + 0.025, dhi - 0.02 - bd), (u + bw, zs + 0.025 + bh, dhi - 0.02), r, inset=0.003, inset_face="+z")
            # label band
            mb.face([(u + 0.01, zs + 0.025 + bh * 0.4, dhi - 0.0195), (u + bw - 0.01, zs + 0.025 + bh * 0.4, dhi - 0.0195),
                     (u + bw - 0.01, zs + 0.025 + bh * 0.7, dhi - 0.0195), (u + 0.01, zs + 0.025 + bh * 0.7, dhi - 0.0195)],
                    "product_e" if r != "product_e" else "product_a")
            u += bw + rnd.uniform(0.005, 0.04)


def barber_pole(mb, tf, u, z):
    ptf = frame_tf(tf((u, z, 0.12)), (1, 0, 0), (0, 0.35, 0.94))
    bands = ["wood_painted_red", "sign_letters", "sign_blue"]
    prof = [(0.06, 0.0)]
    n = 7
    for i in range(1, n + 1):
        prof.append((0.075, i * 0.1))
    rolemap = {i: bands[i % 3] for i in range(n)}
    mb.lathe(prof, "wood_painted_red", 14, ptf, rolemap=rolemap)
    mb.lathe([(0.0, -0.06), (0.09, -0.06), (0.09, 0.0), (0.075, 0.0)], "metal_chrome", 14, ptf)
    mb.lathe([(0.075, 0.70), (0.09, 0.70), (0.09, 0.76), (0.0, 0.80)], "metal_chrome", 14, ptf)
    mb.bar(tf((u, z + 0.35, 0.0)), tf((u, z + 0.35, 0.12)), 0.03, "metal_chrome")


# ================================================================================================= 1. shop corner

def build_shop_corner():
    W, D = 6.0, 8.0
    mb = MB()
    tf = facade_tf(W)
    rnd = random.Random(3)
    openings = []
    # ---- shopfront joinery (z 0 .. 3.75) ----
    G = "wood_painted_green"
    for (a, b) in ((0.0, 0.28), (4.42, 4.72), (5.72, 6.0)):      # pilasters
        mb.box((a, 0.0, -0.05), (b, 2.95, 0.10), G, tf)
        mb.box((a - 0.02, 2.75, -0.05), (b + 0.02, 2.95, 0.14), G, tf)       # capital
        mb.box((a - 0.02, 0.0, -0.05), (b + 0.02, 0.25, 0.13), "render_dark", tf)   # plinth
    mb.box((0.28, 0.0, -0.05), (4.42, 0.55, 0.06), G, tf)                           # stall riser
    mb.box((0.28, 0.52, -0.05), (4.42, 0.58, 0.09), G, tf)                           # riser moulding
    # shop window frame
    fx0, fx1, fz0, fz1 = 0.28, 4.42, 0.55, 2.62
    fd0, fd1 = -0.04, -0.12
    for (a, b, c, d) in ((fx0, fx0 + 0.07, fz0, fz1), (fx1 - 0.07, fx1, fz0, fz1), (fx0, fx1, fz1 - 0.07, fz1), (fx0, fx1, fz0, fz0 + 0.07),
                         (fx0, fx1, 2.28, 2.34)):
        mb.box((a, c, fd1), (b, d, fd0), G, tf)
    mb.face([tf((fx0, fz0, -0.08)), tf((fx1, fz0, -0.08)), tf((fx1, fz1, -0.08)), tf((fx0, fz1, -0.08))], "glass_shop")
    reveal(mb, tf, fx0, fz0, fx1 - fx0, fz1 - fz0, 0.12, G, top=True)
    # "OPEN" sign hanging inside the glass
    mb.box((3.45, 1.50, -0.21), (4.25, 1.74, -0.19), "plastic_black", tf)
    block_text(mb, tf, "OPEN", 0.15, 3.52, 1.545, -0.19, -0.185, "led_red", stroke=0.028, spacing=0.18)
    mb.tube([tf((3.55, 1.74, -0.2)), tf((3.85, 2.0, -0.2)), tf((4.15, 1.74, -0.2))], 0.004, "metal_dark", 6)
    # door (glazed shop door, recessed) + lit fanlight
    door(mb, tf, 4.72, 0.0, 1.0, 2.62, recess=0.35, leaf_role=G, reveal_role=G, glazed=True, kick=True, fanlight=True,
         lintel=0.0, frame_role=G, handle_side="left")
    mb.box((4.72, 0.0, -0.35), (5.72, 0.03, 0.0), "stone_sill", tf)
    # roller shutter housing + fascia + cornice
    mb.box((0.10, 2.62, -0.05), (5.90, 2.95, 0.19), "metal_painted_grey", tf, inset=0.01, inset_face="+z")
    mb.box((-0.04, 2.95, -0.02), (6.04, 3.60, 0.08), "sign_fascia", tf)
    mb.box((-0.08, 3.60, -0.02), (6.08, 3.75, 0.17), "wood_painted_cream", tf)
    mb.box((-0.08, 2.92, -0.02), (6.08, 2.98, 0.11), "wood_painted_cream", tf)
    # fascia content: NEWS + logo disc + OFF LICENCE
    block_text(mb, tf, "NEWS", 0.36, 0.30, 3.11, 0.08, 0.11, "sign_letters", stroke=0.07)
    ltf = frame_tf(tf((2.15, 3.275, 0.08)), (1, 0, 0), (0, 0, 1))
    mb.cyl((0, 0, 0), 0.24, 0.24, 0.03, "sign_yellow", 24, ltf)
    mb.box((-0.17, -0.04, 0.03), (0.17, 0.04, 0.045), "sign_blue", ltf)
    mb.box((-0.04, -0.17, 0.03), (0.04, 0.17, 0.045), "sign_blue", ltf)
    block_text(mb, tf, "OFF LICENCE", 0.17, 2.55, 3.19, 0.08, 0.10, "sign_letters", stroke=0.032, spacing=0.16)
    # awning (striped, retractable) over the window
    mb.box((0.30, 2.36, 0.0), (4.40, 2.62, 0.22), "metal_painted_grey", tf, inset=0.01, inset_face="+z")
    a_u0, a_u1 = 0.32, 4.38
    z_back, d_back, z_front, d_front = 2.40, 0.22, 2.02, 1.35
    nstr = 13
    sw = (a_u1 - a_u0) / nstr
    for i in range(nstr):
        u0 = a_u0 + i * sw
        u1 = u0 + sw
        r = "awning_red" if i % 2 == 0 else "awning_white"
        mb.face([tf((u0, z_back, d_back)), tf((u1, z_back, d_back)), tf((u1, z_front, d_front)), tf((u0, z_front, d_front))], r)
        mb.face([tf((u0, z_front, d_front)), tf((u1, z_front, d_front)), tf((u1, z_back, d_back)), tf((u0, z_back, d_back))], r)
        # scalloped valance
        vz = z_front - 0.2
        mb.face([tf((u0, z_front, d_front)), tf((u0, vz, d_front)), tf(((u0 + u1) / 2, vz - 0.07, d_front)), tf((u1, vz, d_front)), tf((u1, z_front, d_front))], r)
        mb.face([tf((u0, z_front, d_front - 0.004)), tf((u1, z_front, d_front - 0.004)), tf((u1, vz, d_front - 0.004)),
                 tf(((u0 + u1) / 2, vz - 0.07, d_front - 0.004)), tf((u0, vz, d_front - 0.004))], r)
    mb.bar(tf((a_u0 - 0.02, z_front, d_front)), tf((a_u1 + 0.02, z_front, d_front)), 0.04, "metal_painted_grey")
    for u in (a_u0 + 0.12, a_u1 - 0.12):
        mb.bar(tf((u, 1.95, 0.02)), tf((u, z_front + 0.02, d_front - 0.03)), 0.03, "metal_painted_grey")
        mb.box((u - 0.04, 1.90, 0.0), (u + 0.04, 2.0, 0.04), "metal_painted_grey", tf)
    # ---- interior (visible through the glass) ----
    iu0, iu1, idf, idb, ih = 0.28, 5.72, -0.12, -3.0, 2.9
    mb.face([tf((iu0, 0.01, idf)), tf((iu1, 0.01, idf)), tf((iu1, 0.01, idb)), tf((iu0, 0.01, idb))], "lino_floor")
    mb.face([tf((iu0, ih, idb)), tf((iu1, ih, idb)), tf((iu1, ih, idf)), tf((iu0, ih, idf))], "interior_wall")
    mb.face([tf((iu0, 0.0, idb)), tf((iu1, 0.0, idb)), tf((iu1, ih, idb)), tf((iu0, ih, idb))], "interior_wall")
    mb.face([tf((iu0, 0.0, idf)), tf((iu0, 0.0, idb)), tf((iu0, ih, idb)), tf((iu0, ih, idf))], "interior_wall")
    mb.face([tf((iu1, 0.0, idf)), tf((iu1, ih, idf)), tf((iu1, ih, idb)), tf((iu1, 0.0, idb))], "interior_wall")
    for dd in (-0.9, -2.2):
        mb.box((1.0, 2.84, dd - 0.08), (2.4, 2.88, dd + 0.08), "shop_light", tf)
        mb.box((3.2, 2.84, dd - 0.08), (4.6, 2.88, dd + 0.08), "shop_light", tf)
    # interior fittings are built in facade-local coords (u, z, d) in a sub-builder, then mapped through tf
    sub = MB()
    shelf_unit(sub, 0.45, 1.95, idb + 0.02, 0.0, 2.0, 5, 0.42, 11)
    shelf_unit(sub, 2.15, 3.65, idb + 0.02, 0.0, 2.0, 5, 0.42, 12)
    shelf_unit(sub, 3.85, 5.35, idb + 0.02, 0.0, 2.0, 5, 0.42, 13)
    shelf_unit(sub, 1.0, 3.4, -1.75, 0.0, 1.45, 4, 0.40, 14)            # gondola facing the window
    # counter + till
    sub.box((4.75, 0.0, -1.95), (5.65, 0.95, -1.35), "wood_light")
    sub.box((4.70, 0.95, -2.0), (5.70, 1.0, -1.30), "wood_dark")
    sub.box((5.1, 1.0, -1.75), (5.5, 1.3, -1.45), "plastic_grey", inset=0.01, inset_face="+z")
    sub.face([(5.12, 1.12, -1.449), (5.48, 1.12, -1.449), (5.48, 1.28, -1.449), (5.12, 1.28, -1.449)], "screen_on")
    # drinks fridge on the right wall
    sub.box((5.0, 0.0, -1.25), (5.70, 1.95, -0.55), "plastic_white", inset=0.01, inset_face="+z")
    sub.face([(5.05, 0.25, -0.549), (5.65, 0.25, -0.549), (5.65, 1.85, -0.549), (5.05, 1.85, -0.549)], "shop_light")
    for k in range(4):
        zz = 0.35 + k * 0.4
        sub.box((5.06, zz, -1.2), (5.64, zz + 0.02, -0.6), "metal_steel")
        for i in range(6):
            sub.box((5.08 + i * 0.095, zz + 0.02, -0.9), (5.08 + i * 0.095 + 0.07, zz + 0.16, -0.70), random.Random(k * 7 + i).choice(["product_a", "product_b", "product_d", "product_c"]))
    # window display: tiered newspaper / magazine stand
    for t in range(3):
        d0 = -0.32 - t * 0.2
        zz = 0.6 + t * 0.32
        sub.box((2.3, zz, d0 - 0.24), (4.3, zz + 0.03, d0), "wood_light")
        ptf = frame_tf((0, zz + 0.03, d0 - 0.02), (1, 0, 0), (0, 0.94, -0.34))
        for i in range(5):
            x = 2.38 + i * 0.39
            r = ["paper_white", "paper_yellow", "poster_b", "paper_white", "poster_a"][(i + t) % 5]
            sub.box((x, 0.0, -0.012), (x + 0.33, 0.42, 0.0), r, ptf)
            sub.face([ptf((x + 0.02, 0.30, 0.001)), ptf((x + 0.31, 0.30, 0.001)), ptf((x + 0.31, 0.40, 0.001)), ptf((x + 0.02, 0.40, 0.001))],
                     "sign_fascia" if i % 2 == 0 else "sign_blue")
    # sweets / low display left of the window
    sub.box((0.5, 0.0, -0.95), (2.0, 0.7, -0.35), "wood_light")
    for i in range(10):
        rr = random.Random(100 + i)
        x = 0.55 + (i % 5) * 0.29
        dd = -0.9 + (i // 5) * 0.3
        sub.box((x, 0.7, dd), (x + rr.uniform(0.18, 0.25), 0.7 + rr.uniform(0.08, 0.18), dd + 0.22), rr.choice(["product_a", "product_b", "product_c", "product_d"]))
    # map the interior sub-mesh (built in facade-local coords) into the main builder through tf
    sub.bm.verts.ensure_lookup_table()
    for f in sub.bm.faces:
        mb.face([tf(v.co) for v in f.verts], sub.roles[f.material_index], f.smooth)
    sub.bm.free()
    # ---- upper floor: 3 sash windows ----
    z0, hgt = 4.5, 1.5
    looks = (("lit", "curtain_red"), ("tv", "curtain_cream"), ("dark", "curtain_blue"))
    for i, cx in enumerate((1.1, 3.0, 4.9)):
        lk, cu = looks[i]
        openings.append(window(mb, tf, cx - 0.525, z0, 1.05, hgt, "sash", lk, cu, "upvc_white", "brick_dark"))
    alarm_box(mb, tf, 5.45, 6.55)
    # string course + bricks
    mb.box((-0.02, 6.95, -0.01), (6.02, 7.05, 0.05), "stone_sill", tf)
    brick_wall(mb, tf, W, EAVES, openings, z_from=3.75, seed=1)
    # ---- side (+X) facade: brick skin on the first 4 m with a door + window + ghost sign ----
    stf = frame_tf((W / 2, 0.0, 0.0), (0, 1, 0), (0, 0, 1))
    sop = []
    sop.append(window(mb, stf, 1.0, 4.5, 1.05, 1.5, "sash", "lit", "curtain_cream", "upvc_white", "brick_dark"))
    sop.append(door(mb, stf, 2.6, 0.0, 0.9, 2.025, recess=0.2, leaf_role="wood_painted_black", reveal_role="brick_dark",
                    number="4A", lintel=0.15))
    mb.box((0.3, 2.55, 0.0), (2.4, 3.45, 0.03), "render_dark", stf)
    block_text(mb, stf, "TEAS", 0.28, 0.42, 2.98, 0.03, 0.04, "sign_letters", stroke=0.045)
    block_text(mb, stf, "ICES", 0.28, 0.42, 2.62, 0.03, 0.04, "sign_letters", stroke=0.045)
    sop.append({"x0": 0.3, "x1": 2.4, "z0": course(2.55), "z1": course(3.45)})
    satellite_dish(mb, stf, 3.4, 5.6)
    brick_wall(mb, stf, 4.0, EAVES, sop, seed=2)
    # ---- shell, roof, chimneys, drainpipes ----
    shell(mb, W, D, EAVES, "brick", x_shrink=0.015)
    gable_roof(mb, -W / 2, W / 2, 0.0, D, EAVES, RIDGE)
    chimney(mb, -2.55, D / 2, 8.4, 10.1, 1.0, 0.55, 3)
    chimney(mb, 2.5, D / 2, 8.4, 10.0, 1.0, 0.55, 2)
    # TV aerial on the right chimney
    mb.bar((2.5, D / 2, 10.0), (2.5, D / 2, 11.2), 0.02, "metal_painted_grey")
    for k in range(5):
        mb.bar((2.5, D / 2 - 0.35, 10.75 + k * 0.1), (2.5, D / 2 + 0.35, 10.75 + k * 0.1), 0.012, "metal_painted_grey")
    drainpipe(mb, -2.82, 0.0, 0.1, EAVES - 0.12)
    # side drainpipe (normal +X): build with a frame rotated
    mb.cyl((W / 2 + 0.08, 4.1, 0.1), 0.034, 0.034, EAVES - 0.25, "plastic_black", 12)
    for z in (0.8, 2.6, 4.4, 6.2):
        mb.box((W / 2, 4.05, z), (W / 2 + 0.13, 4.15, z + 0.035), "metal_painted_black")
    root = mb.build("exterior_shop_corner")
    info = dict(category="building", views=("front", "front34", "close", "side"),
                notes="Hero corner shop + flat. Origin ground-level front-centre; front facade plane y=0 (faces -Y); footprint x -3..3, y 0..8; "
                      "+X side has a 4 m brick return with a door; -X side is a plain party wall for exterior_terrace_a. Eaves 7.2, ridge 9.2, chimney tops 10.1. "
                      "Shopfront glass at y=0.08 shows a modelled interior (shelves, fridge, counter, paper stand). Fascia sign z 2.95-3.6 (role sign_fascia + sign_letters), "
                      "awning projects 1.35 m over the pavement at z 2.0-2.4. Lit roles: window_lit/window_tv (upper flat), shop_light (interior strips), led_red (OPEN sign), sign_yellow (logo/alarm).")
    return root, info


# ================================================================================================= 2. terraces

def build_terrace(variant):
    W, D = 4.0, 8.0
    mb = MB()
    tf = facade_tf(W)
    openings = []
    if variant == "a":
        roles, weights, mortar = ("brick_yellow", "brick_yellow_dark", "brick"), (0.62, 0.28, 0.10), "mortar"
        # ground: front door + window, door canopy, wall lamp, window box
        openings.append(door(mb, tf, 0.35, 0.0, 0.9, 2.1, recess=0.25, leaf_role="wood_painted_blue", reveal_role="brick_yellow_dark",
                             number="42", lintel=0.15, lit_fan=True))
        openings.append(window(mb, tf, 1.75, 0.9, 1.85, 1.5, "sash", "lit", "curtain_cream", "upvc_white", "brick_yellow_dark"))
        # window box with plants
        mb.box((1.9, 0.72, 0.07), (3.45, 0.90, 0.30), "terracotta", tf, inset=0.01, inset_face="+z")
        for i in range(6):
            rr = random.Random(50 + i)
            mb.sphere(tf((2.0 + i * 0.28, 0.98 + rr.uniform(0, 0.08), 0.18)), rr.uniform(0.09, 0.13), rr.choice(["leaf_green", "leaf_dark"]), 1, noise_amp=0.25, seed=i)
        # door canopy (little pitched hood on brackets)
        ctf = tf
        for (a, b) in ((0.28, 0.33), (1.27, 1.32)):
            mb.bar(ctf((a + 0.025, 2.62, 0.0)), ctf((a + 0.025, 2.62, 0.55)), 0.05, "wood_painted_cream")
            mb.bar(ctf((a + 0.025, 2.25, 0.0)), ctf((a + 0.025, 2.62, 0.55)), 0.04, "wood_painted_cream")
        mb.face([tf((0.22, 2.64, 0.60)), tf((1.38, 2.64, 0.60)), tf((1.38, 2.92, 0.0)), tf((0.22, 2.92, 0.0))], "slate_roof")
        mb.face([tf((0.22, 2.64, 0.60)), tf((0.22, 2.92, 0.0)), tf((1.38, 2.92, 0.0)), tf((1.38, 2.64, 0.60))], "wood_painted_cream")
        mb.box((0.22, 2.64, 0.58), (1.38, 2.70, 0.62), "plastic_black", tf)
        # porch lamp (lit) + house alarm + satellite dish
        mb.box((1.45, 2.25, 0.0), (1.53, 2.33, 0.08), "metal_painted_black", tf)
        mb.lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.12), (0.05, 0.14), (0.0, 0.14)], "lamp_glow", 10, base=tf((1.49, 2.15, 0.11)))
        alarm_box(mb, tf, 3.45, 6.5)
        satellite_dish(mb, tf, 3.55, 5.55)
        # first floor windows
        openings.append(window(mb, tf, 0.35, 4.5, 1.05, 1.5, "sash", "dark", "curtain_blue", "upvc_white", "brick_yellow_dark"))
        openings.append(window(mb, tf, 1.95, 4.5, 1.65, 1.5, "sash", "lit", "curtain_red", "upvc_white", "brick_yellow_dark", blind=0.45))
        mb.box((-0.02, 3.9, -0.01), (4.02, 4.0, 0.04), "stone_sill", tf)       # string course
        mb.box((-0.02, 6.95, -0.01), (4.02, 7.05, 0.05), "stone_sill", tf)
        brick_wall(mb, tf, W, EAVES, openings, roles, weights, mortar, seed=21)
        drainpipe(mb, -W / 2 + 0.16, 0.0, 0.1, EAVES - 0.12)
        gable_roof(mb, -W / 2, W / 2, 0.0, D, EAVES, RIDGE)
        chimney(mb, -W / 2 + 0.5, D / 2, 8.4, 10.1, 1.0, 0.55, 3, roles=("brick_yellow", "brick_yellow_dark"))
        notes = ("Terrace house (London-stock yellow brick) to sit at the -X side of exterior_shop_corner (place at x=-5). Front door no.42 with lit fanlight, "
                 "porch hood, window box, satellite dish, alarm. Eaves 7.2 / ridge 9.2 shared with the shop. Lit: window_lit, lamp_glow.")
    else:
        roles, weights, mortar = ("brick_dark", "brick", "brick_sooty_light"), (0.55, 0.30, 0.15), "mortar"
        G = "wood_painted_black"
        # closed-down barber: pilasters, roller shutter down, side door to the flat, dark fascia, barber pole
        for (a, b) in ((0.0, 0.25), (2.95, 3.15), (3.9, 4.0)):
            mb.box((a, 0.0, -0.05), (b, 2.72, 0.10), G, tf)
            mb.box((a - 0.02, 0.0, -0.05), (b + 0.02, 0.22, 0.12), "render_dark", tf)
        reveal(mb, tf, 0.25, 0.0, 2.70, 2.72, 0.30, G, top=True)
        shutter_corrugated(mb, tf, 0.25, 2.95, 0.0, 2.35, -0.28)
        # graffiti tag on the shutter
        block_text(mb, tf, "ZK", 0.55, 0.9, 0.7, -0.255, -0.25, "graffiti_white", stroke=0.13, spacing=0.1)
        block_text(mb, tf, "ZK", 0.55, 0.9, 0.7, -0.252, -0.245, "graffiti_a", stroke=0.08, spacing=0.1)
        openings.append(door(mb, tf, 3.15, 0.0, 0.75, 2.1, recess=0.2, leaf_role="wood_painted_red", reveal_role="brick_dark",
                             number="7", lintel=0.0, lit_fan=False, panels=2))
        mb.box((-0.04, 2.72, -0.02), (4.04, 3.40, 0.08), "sign_fascia_dark", tf)
        mb.box((-0.08, 3.40, -0.02), (4.08, 3.525, 0.15), "wood_painted_cream", tf)
        mb.box((-0.08, 2.70, -0.02), (4.08, 2.75, 0.11), "wood_painted_cream", tf)
        block_text(mb, tf, "CUTS", 0.36, 0.4, 2.88, 0.08, 0.105, "sign_letters", stroke=0.065)
        block_text(mb, tf, "BARBER", 0.14, 2.3, 2.98, 0.08, 0.095, "sign_letters", stroke=0.022, spacing=0.2)
        barber_pole(mb, tf, 3.52, 2.0)
        # first floor: TO LET board + 2 windows (one lit with blind, one dark)
        openings.append(window(mb, tf, 0.35, 4.5, 1.05, 1.5, "sash", "lit", "curtain_cream", "wood_painted_cream", "brick_dark", blind=0.55))
        openings.append(window(mb, tf, 2.25, 4.5, 1.4, 1.5, "sash", "dark", None, "wood_painted_cream", "brick_dark"))
        mb.box((1.55, 6.3, 0.05), (2.95, 7.0, 0.08), "sign_blue", tf)
        block_text(mb, tf, "TO LET", 0.22, 1.63, 6.68, 0.08, 0.095, "sign_letters", stroke=0.04, spacing=0.16)
        for i in range(4):
            mb.box((1.65 + i * 0.32, 6.40, 0.08), (1.9 + i * 0.32, 6.52, 0.09), "sign_letters", tf)
        mb.bar(tf((2.25, 7.0, 0.065)), tf((2.25, 7.4, 0.065)), 0.05, "wood_painted_cream")
        openings.append({"x0": 1.55, "x1": 2.95, "z0": course(6.3), "z1": course(7.0)})
        mb.box((-0.02, 6.95, -0.01), (4.02, 7.05, 0.05), "stone_sill", tf)
        brick_wall(mb, tf, W, EAVES, openings, roles, weights, mortar, z_from=course(3.525), seed=22)
        drainpipe(mb, W / 2 - 0.16, 0.0, 0.1, EAVES - 0.12)
        gable_roof(mb, -W / 2, W / 2, 0.0, D, EAVES, RIDGE)
        chimney(mb, W / 2 - 0.5, D / 2, 8.4, 10.0, 1.0, 0.55, 2, roles=("brick_dark", "brick"))
        notes = ("Closed barber shop with flat above, dark red brick, to sit at the +X side of exterior_shop_corner (place at x=+5). Roller shutter down with graffiti tag, "
                 "CUTS/BARBER fascia, barber pole, TO LET board, 2 upper windows (one lit with blind). Eaves 7.2 / ridge 9.2.")
    shell(mb, W, D, EAVES, roles[0])
    root = mb.build(f"exterior_terrace_{variant}")
    return root, dict(category="building", views=("front", "front34"), notes=notes)


# ================================================================================================= 3. shop props

def crate(mb, cx, cy, z, w=0.5, d=0.35, h=0.28, rot=0.0, fruit="produce_orange", seed=0, fill=True):
    tf = frame_tf((cx, cy, z), (math.cos(rot), math.sin(rot), 0), (0, 0, 1))
    t = 0.012
    for (x0, y0, x1, y1) in ((-w / 2, -d / 2, -w / 2 + t, d / 2), (w / 2 - t, -d / 2, w / 2, d / 2)):
        for zz in (0.0, h - 0.05):
            mb.box((x0, y0, zz), (x1, y1, zz + 0.05), "wood_light", tf)
    for s in range(3):                       # slats on long sides
        zz = 0.02 + s * (h - 0.07) / 2
        mb.box((-w / 2, -d / 2, zz), (w / 2, -d / 2 + t, zz + 0.05), "wood_light", tf)
        mb.box((-w / 2, d / 2 - t, zz), (w / 2, d / 2, zz + 0.05), "wood_light", tf)
    for (x0, x1) in ((-w / 2, -w / 2 + 0.04), (w / 2 - 0.04, w / 2), (-0.02, 0.02)):
        mb.box((x0, -d / 2, 0.0), (x1, d / 2, h), "wood_light", tf)   # corner posts / centre batten
    mb.box((-w / 2, -d / 2, 0.0), (w / 2, d / 2, 0.015), "wood_light", tf)
    if fill:
        rnd = random.Random(seed)
        for i in range(12):
            r = rnd.uniform(0.035, 0.045)
            px = -w / 2 + 0.07 + (i % 4) * (w - 0.14) / 3 + rnd.uniform(-0.01, 0.01)
            py = -d / 2 + 0.07 + (i // 4) * (d - 0.14) / 2 + rnd.uniform(-0.01, 0.01)
            mb.sphere(tf((px, py, h - 0.09 + r + rnd.uniform(0, 0.03))), r, fruit, 1, noise_amp=0.06, seed=i)


def wheelie_bin(mb, cx, cy, rot=0.0, role="plastic_dark_green", w=0.58, d=0.72, h=1.07):
    tf = frame_tf((cx, cy, 0), (math.cos(rot), math.sin(rot), 0), (0, 0, 1))
    mb.box((-w / 2, -d / 2, 0.22), (w / 2, d / 2 - 0.05, h), role, tf, inset=0.02, inset_face="-z")
    mb.box((-w / 2 - 0.015, -d / 2 - 0.015, h), (w / 2 + 0.015, d / 2 + 0.03, h + 0.03), role, tf)
    mb.face([tf((-w / 2 - 0.015, -d / 2 - 0.015, h + 0.03)), tf((w / 2 + 0.015, -d / 2 - 0.015, h + 0.03)),
             tf((w / 2 + 0.015, d / 2 + 0.03, h + 0.1)), tf((-w / 2 - 0.015, d / 2 + 0.03, h + 0.1))], role)
    mb.face([tf((-w / 2 - 0.015, d / 2 + 0.03, h + 0.03)), tf((-w / 2 - 0.015, d / 2 + 0.03, h + 0.1)), tf((w / 2 + 0.015, d / 2 + 0.03, h + 0.1)), tf((w / 2 + 0.015, d / 2 + 0.03, h + 0.03))], role)
    for s in ((-w / 2 - 0.015, d / 2 + 0.03), (w / 2 + 0.015, d / 2 + 0.03)):
        mb.face([tf((s[0], -d / 2 - 0.015, h + 0.03)), tf((s[0], s[1], h + 0.03)), tf((s[0], s[1], h + 0.1))], role)
    mb.bar(tf((-w / 2 + 0.05, d / 2 + 0.02, h - 0.1)), tf((w / 2 - 0.05, d / 2 + 0.02, h - 0.1)), 0.03, role)     # handle
    for x in (-w / 2 + 0.1, w / 2 - 0.1):
        wtf = frame_tf(tf((x - 0.03, d / 2 - 0.12, 0.1)), (0, 1, 0), (0, 0, 1))
        mb.cyl((0, 0, 0), 0.1, 0.1, 0.06, "rubber_black", 14, wtf, cap_role="plastic_grey")
    mb.box((-w / 2 + 0.05, -d / 2 + 0.15, 0.0), (w / 2 - 0.05, d / 2 - 0.25, 0.22), role, tf)


def bicycle(mb, cx, cy, rot=0.0, lean=0.12, frame_role="metal_painted_green"):
    """Side-on bicycle along local x, leaning (rotation about x) by `lean` radians."""
    tf = frame_tf((cx, cy, 0), (math.cos(rot), math.sin(rot), 0), (0, -math.sin(lean), math.cos(lean)))
    R = 0.34
    for wx in (-0.52, 0.52):
        circ = [(wx + R * math.cos(a), 0, R + R * math.sin(a)) for a in [2 * math.pi * i / 28 for i in range(29)]]
        mb.tube([tf(p) for p in circ], 0.022, "rubber_black", 8, caps=False)
        circ2 = [(wx + (R - 0.03) * math.cos(a), 0, R + (R - 0.03) * math.sin(a)) for a in [2 * math.pi * i / 28 for i in range(29)]]
        mb.tube([tf(p) for p in circ2], 0.01, "metal_steel", 6, caps=False)
        for i in range(14):
            a = 2 * math.pi * i / 14
            mb.bar(tf((wx, 0.0, R)), tf((wx + (R - 0.04) * math.cos(a), 0.0, R + (R - 0.04) * math.sin(a))), 0.004, "metal_steel")
    O = Vector(tf((0, 0, 0)))
    E1 = Vector(tf((1, 0, 0))) - O          # bike x axis (world)
    E2 = Vector(tf((0, 0, 1))) - O          # bike up axis (leaning)
    for wx in (-0.52, 0.52):
        mb.cyl((0, 0, 0), 0.03, 0.03, 0.10, "metal_steel", 10, frame_tf(tf((wx, -0.05, R)), E1, E2))   # hub along bike y
    # frame (diamond)
    rear, bb, seat, head_lo, head_hi, bars_c = (-0.52, 0, R), (-0.08, 0, 0.30), (-0.22, 0, 0.82), (0.36, 0, 0.56), (0.30, 0, 0.90), (0.26, 0, 1.0)
    fr = 0.016
    for (p, q) in ((bb, seat), (bb, head_lo), (seat, head_hi), (head_lo, head_hi), (rear, bb), (rear, seat), (head_lo, (0.52, 0, R)), (seat, (-0.22, 0, 0.98))):
        mb.tube([tf(p), tf(q)], fr, frame_role, 8)
    mb.tube([tf(head_hi), tf(bars_c)], 0.013, "metal_steel", 8)
    mb.tube([tf((0.26, -0.26, 1.0)), tf((0.26, -0.06, 1.0)), tf(bars_c), tf((0.26, 0.06, 1.0)), tf((0.26, 0.26, 1.0))], 0.012, "metal_steel", 8)
    for y in (-0.26, 0.26):
        mb.tube([tf((0.26, y, 1.0)), tf((0.26, y + (-0.1 if y < 0 else 0.1), 1.0))], 0.016, "rubber_black", 8)
    # saddle
    mb.box((-0.34, -0.07, 0.98), (-0.08, 0.07, 1.03), "leather_black", tf, inset=0.02, inset_face="+z")
    # cranks, pedals, chainring
    mb.cyl((0, 0, 0), 0.09, 0.09, 0.012, "metal_steel", 18, frame_tf(tf((-0.08, -0.07, 0.30)), E1, E2))
    mb.bar(tf((-0.08, -0.06, 0.30)), tf((0.05, -0.08, 0.16)), 0.02, "metal_steel")
    mb.bar(tf((-0.08, 0.06, 0.30)), tf((-0.21, 0.08, 0.44)), 0.02, "metal_steel")
    mb.box((0.0, -0.14, 0.14), (0.10, -0.08, 0.18), "plastic_black", tf)
    mb.box((-0.26, 0.08, 0.42), (-0.16, 0.14, 0.46), "plastic_black", tf)
    # chain (thin tube loop)
    chain = [(-0.08, -0.05, 0.39), (-0.52, -0.05, R + 0.04), (-0.52, -0.05, R - 0.04), (-0.08, -0.05, 0.21), (-0.08, -0.05, 0.39)]
    mb.tube([tf(p) for p in chain], 0.006, "metal_dark", 6, caps=False)
    # D-lock through the rear wheel, with the cable lock loop reaching out to the lamp post position
    mb.tube([tf(p) for p in [(-0.48, 0.03, 0.5), (-0.48, 0.03, 0.72), (-0.34, 0.03, 0.72), (-0.34, 0.03, 0.5)]], 0.014, "metal_painted_black", 8)
    mb.box((-0.50, 0.0, 0.42), (-0.32, 0.06, 0.50), "metal_painted_black", tf)
    return tf


def build_shop_props():
    mb = MB()
    # crates stacked under the shop window (shop origin = props origin)
    crate(mb, -1.6, -0.45, 0.0, rot=0.03, fruit="produce_orange", seed=1)
    crate(mb, -1.6, -0.45, 0.28, rot=-0.05, fruit="produce_green", seed=2)
    crate(mb, -1.02, -0.45, 0.0, rot=0.0, fruit="produce_red", seed=3)
    crate(mb, -1.02, -0.45, 0.28, rot=0.06, fruit="produce_yellow", seed=4)
    crate(mb, -1.3, -0.42, 0.56, rot=0.02, fruit="produce_orange", seed=5)
    # A-board (sandwich board) with chalk scribbles
    atf = frame_tf((0.9, -1.25, 0.0), (1, 0, 0), (0, 0, 1))
    for sgn in (-1, 1):
        ptf = frame_tf(atf((0, 0, 0)), (1, 0, 0), (0, sgn * math.sin(0.25), math.cos(0.25)))
        mb.box((-0.3, -0.015, 0.0), (0.3, 0.015, 0.95), "wood_painted_black", ptf)
        # the outward face of each leaf is the side it leans towards (sgn<0 -> local -y)
        f0, f1 = (-0.016, -0.015) if sgn < 0 else (0.015, 0.016)
        mb.box((-0.26, f0, 0.12), (0.26, f1, 0.88), "interior_dark", ptf)
        d0, d1 = (-0.0175, -0.0165) if sgn < 0 else (0.0165, 0.0175)
        # chalk scribbles: white ribbons on the board face; ribbon local (u, v, d) -> board (x, up, normal)
        board = lambda p, ptf=ptf: ptf((p[0], p[2], p[1]))
        for s in text_strokes("NEWS", 0.12, -0.2, 0.68, 0.16)[0]:
            mb.ribbon(s, 0.006, d0, d1, "graffiti_white", board)
        for line in range(3):
            mb.ribbon([(-0.18, 0.5 - line * 0.1), (0.1 + line * 0.03, 0.5 - line * 0.1)], 0.006, d0, d1, "graffiti_white", board)
    mb.bar(atf((-0.3, 0, 0.96)), atf((0.3, 0, 0.96)), 0.04, "metal_painted_black")
    # newspaper rack (wire) by the door
    rx, ry = 2.35, -0.38
    rtf = frame_tf((rx, ry, 0), (1, 0, 0), (0, 0, 1))
    for x in (-0.3, 0.3):
        mb.bar(rtf((x, -0.15, 0)), rtf((x, 0.15, 0)), 0.02, "metal_painted_black")
        mb.bar(rtf((x, 0.12, 0)), rtf((x, 0.12, 1.25)), 0.02, "metal_painted_black")
        mb.bar(rtf((x, -0.12, 0)), rtf((x, 0.0, 0.9)), 0.02, "metal_painted_black")
    for t in range(3):
        z = 0.3 + t * 0.32
        ptf = frame_tf(rtf((0, 0.1 - t * 0.0, z)), (1, 0, 0), (0, -0.9, 0.42))
        mb.bar(rtf((-0.3, 0.1, z)), rtf((0.3, 0.1, z)), 0.012, "metal_painted_black")
        mb.bar(rtf((-0.3, -0.03, z + 0.28)), rtf((0.3, -0.03, z + 0.28)), 0.012, "metal_painted_black")
        for i in range(2):
            x = -0.28 + i * 0.3
            mb.box((x, 0.0, -0.012), (x + 0.26, 0.32, 0.0), "paper_white", ptf)
            mb.face([ptf((x + 0.02, 0.22, 0.001)), ptf((x + 0.24, 0.22, 0.001)), ptf((x + 0.24, 0.30, 0.001)), ptf((x + 0.02, 0.30, 0.001))], "sign_fascia" if (i + t) % 2 else "sign_blue")
    mb.box((rx - 0.32, ry + 0.09, 1.25), (rx + 0.32, ry + 0.15, 1.45), "sign_fascia")
    block_text(mb, frame_tf((rx - 0.32, ry + 0.09, 1.25), (1, 0, 0), (0, 0, 1)), "NEWS", 0.12, 0.0, 0.04, 0.0, 0.004, "sign_letters", stroke=0.02, centre_w=0.64)
    # wheelie bins (shop's green bin + a grey one)
    wheelie_bin(mb, 3.3, -0.55, rot=0.1)
    wheelie_bin(mb, 2.72, -0.5, rot=-0.08, role="plastic_grey", w=0.5, d=0.62, h=0.95)
    # bicycle leaning against the lamp post position (lamp at x=-3.4, y=-2.05 -> see manifest)
    bicycle(mb, -2.9, -1.85, rot=0.0, lean=0.14)
    # cable lock looping towards the lamp post
    mb.tube([(-3.35, -1.85, 0.5), (-3.42, -1.95, 0.7), (-3.4, -2.05, 0.9), (-3.5, -2.15, 0.7), (-3.42, -2.12, 0.5)], 0.012, "plastic_black", 8)
    root = mb.build("exterior_shop_props")
    notes = ("Pavement clutter for the corner shop. Origin = SAME as exterior_shop_corner origin (drop both at the same point): crates stacked under the window (x -1.9..-0.75, y -0.65..-0.25), "
             "A-board at (0.9,-1.25), paper rack by the door (2.35,-0.38), wheelie bins at x 2.4..3.6, bicycle at (-2.9,-1.85) with cable lock reaching the lamp post at (-3.4,-2.05): "
             "place exterior_street_lamp there. Pavement is y 0..-2.0.")
    return root, dict(category="props", views=("front", "front34"), notes=notes)


# ================================================================================================= 4. street lamp

def build_street_lamp():
    mb = MB()
    mb.lathe([(0.0, 0), (0.19, 0), (0.19, 0.08), (0.16, 0.10), (0.16, 0.85), (0.19, 0.88), (0.19, 0.95), (0.11, 1.0)], "metal_painted_green", 8, smooth=False)
    mb.box((-0.07, -0.19, 0.2), (0.07, -0.155, 0.72), "metal_painted_green", inset=0.01, inset_face="-y")
    mb.lathe([(0.10, 1.0), (0.085, 2.0), (0.07, 3.5), (0.058, 5.3)], "metal_painted_green", 12, cap_bottom=False, cap_top=False)
    mb.lathe([(0.11, 2.4), (0.11, 2.47), (0.07, 2.5)], "metal_painted_green", 12, cap_bottom=True, cap_top=False)
    # bracket arm (smooth curve) to the lantern
    pts = fillet([(0, 5.30), (0, 5.62), (-0.42, 5.85), (-0.95, 5.92)], 0.25, 6)
    arm = [(0.0, p[0], p[1]) for p in pts]
    mb.tube(arm, 0.045, "metal_painted_green", 10, taper=(0.058, 0.04))
    mb.lathe([(0.0, 5.3), (0.09, 5.3), (0.09, 5.36), (0.0, 5.4)], "metal_painted_green", 12)
    # lantern housing (sloped top), glow lens underneath
    ltf = frame_tf((0, -0.95, 5.60), (1, 0, 0), (0, 1, 0))
    mb.poly_prism([(-0.16, -0.32), (0.16, -0.32), (0.16, 0.32), (-0.16, 0.32)], 0.0, 0.22, "lamp_housing", ltf)
    mb.poly_prism([(-0.13, -0.30), (0.13, -0.30), (0.13, 0.30), (-0.13, 0.30)], -0.03, 0.0, "lamp_glow", ltf)
    mb.poly_prism([(-0.19, -0.36), (0.19, -0.36), (0.19, 0.36), (-0.19, 0.36)], 0.22, 0.26, "lamp_housing", ltf)
    mb.poly_prism([(-0.10, -0.26), (0.10, -0.26), (0.10, 0.26), (-0.10, 0.26)], 0.26, 0.31, "lamp_housing", ltf)
    mb.cyl((0.0, 0.2, 0.31), 0.025, 0.025, 0.03, "plastic_grey", 8, ltf)   # photocell
    # parking sign plate on the column
    mb.box((-0.2, -0.085, 2.6), (0.2, -0.07, 3.0), "sign_blue", inset=0.01, inset_face="-y")
    block_text(mb, frame_tf((-0.2, -0.085, 2.6), (1, 0, 0), (0, 0, 1)), "P", 0.26, 0.0, 0.07, 0.0, 0.004, "sign_letters", stroke=0.05, centre_w=0.4)
    mb.bar((-0.17, -0.09, 2.63), (0.17, -0.09, 2.97), 0.004, "wood_painted_red", h=0.025)
    mb.box((-0.06, -0.07, 1.4), (0.06, -0.06, 1.55), "sign_letters")   # council sticker
    root = mb.build("exterior_street_lamp")
    notes = "Street lamp 6 m, lantern projects 0.95 m towards -Y (over the road). Lens role lamp_glow at z 5.57 (underside) - put a Unity point/spot light there. Column green painted steel."
    return root, dict(category="street", views=("front", "front34"), notes=notes)


# ================================================================================================= 5. pavement / kerb

def build_pavement_kerb():
    mb = MB()
    rnd = random.Random(7)
    L = 4.0
    PV, KB, ROAD = 2.0, 0.15, 5.0
    yoff = (PV + KB + ROAD) / 2                   # shift so the bbox centre is the origin
    def Y(y):
        return y + yoff
    mb.box((-L / 2, Y(-PV), 0.0), (L / 2, Y(0.0), 0.075), "concrete", skip=("-z",))     # bed
    s = 0.5
    for i in range(int(L / s)):
        for j in range(int(PV / s)):
            x0 = -L / 2 + i * s + 0.004
            y0 = -PV + j * s + 0.004
            jit = rnd.uniform(-0.002, 0.003)
            role = "paving" if rnd.random() > 0.2 else "paving_dark"
            mb.box((x0, Y(y0), 0.075), (x0 + s - 0.008, Y(y0 + s - 0.008), 0.125 + jit), role, skip=("-z",), inset=0.003, inset_face="+z")
    for i in range(4):          # kerb stones
        x0 = -L / 2 + i * 1.0 + 0.004
        mb.box((x0, Y(-PV - KB), 0.0), (x0 + 1.0 - 0.008, Y(-PV), 0.125), "kerb_stone", skip=("-z",), inset=0.004, inset_face="+z")
    mb.face([(-L / 2, Y(-PV - KB - ROAD), 0), (L / 2, Y(-PV - KB - ROAD), 0), (L / 2, Y(-PV - KB), 0), (-L / 2, Y(-PV - KB), 0)], "asphalt")
    for yy in (-PV - KB - 0.18, -PV - KB - 0.36):   # double yellow
        mb.face([(-L / 2, Y(yy - 0.08), 0.002), (L / 2, Y(yy - 0.08), 0.002), (L / 2, Y(yy), 0.002), (-L / 2, Y(yy), 0.002)], "road_paint_yellow")
    # gully grating in the gutter
    gx, gy = 0.9, -PV - KB - 0.22
    mb.box((gx - 0.23, Y(gy - 0.17), 0.0), (gx + 0.23, Y(gy + 0.17), 0.012), "drain_iron")
    for k in range(6):
        mb.box((gx - 0.19 + k * 0.07, Y(gy - 0.13), 0.012), (gx - 0.19 + k * 0.07 + 0.03, Y(gy + 0.13), 0.013), "interior_dark")
    # manhole cover on the pavement
    mb.cyl((-1.0, Y(-1.1), 0.125), 0.3, 0.3, 0.006, "drain_iron", 20)
    mb.cyl((-1.0, Y(-1.1), 0.131), 0.27, 0.27, 0.002, "interior_dark", 20)
    # a dropped-kerb edge feature: tactile paving tiles at one end
    for i in range(2):
        for j in range(4):
            x0 = L / 2 - 0.8 + i * 0.4 + 0.004
            y0 = -PV + j * 0.4 + 0.004
            mb.box((x0, Y(y0), 0.125), (x0 + 0.392, Y(y0 + 0.392), 0.129), "terracotta", skip=("-z",))
    root = mb.build("exterior_pavement_kerb")
    notes = (f"4 m street section, 7.15 m deep: pavement 2.0 m (top z 0.125), kerb 0.15 m, road 5.0 m (z 0). Origin = bottom centre of the whole piece; the BUILDING LINE (back edge of the pavement) "
             f"is at y=+{yoff:.3f} - place so that edge touches the facade plane. Roles asphalt / paving / kerb_stone / road_paint_yellow separate for Unity materials. Tile along x in 4 m steps.")
    return root, dict(category="street", views=("front34", "top"), notes=notes)


# ================================================================================================= 6. cars

def build_car(variant):
    mb = MB()
    hatch = variant == "a"
    paint = "car_paint_red" if hatch else "car_paint_blue"
    L = 4.0 if hatch else 4.6
    yw = 1.25 if hatch else 1.4
    half = L / 2
    if hatch:
        waist_pts = [(-half, 0.70), (-1.6, 0.80), (-0.9, 0.88), (1.75, 0.93), (half, 0.93)]
        cabin = [(-0.9, 0.88, 0.78), (-0.2, 1.44, 0.66), (0.28, 1.47, 0.66), (0.34, 1.47, 0.66), (1.0, 1.46, 0.66), (1.42, 1.36, 0.68), (1.75, 0.93, 0.76)]
        glass_side = {1, 3, 4}
        glass_roof = {0, 5}
    else:
        waist_pts = [(-half, 0.70), (-1.9, 0.80), (-1.05, 0.88), (1.2, 0.93), (half, 0.90)]
        cabin = [(-1.05, 0.88, 0.78), (-0.35, 1.42, 0.66), (0.14, 1.45, 0.66), (0.20, 1.45, 0.66), (0.78, 1.44, 0.66), (1.2, 0.93, 0.76)]
        glass_side = {1, 3}
        glass_roof = {0, 4}

    def waist(y):
        for (y0, z0), (y1, z1) in zip(waist_pts[:-1], waist_pts[1:]):
            if y0 <= y <= y1:
                t = (y - y0) / (y1 - y0)
                return z0 + (z1 - z0) * t
        return waist_pts[-1][1]

    def wb(y):
        return 0.85 - 0.13 * (abs(y) / half) ** 3

    def zs(y):
        z = 0.25
        for yc in (-yw, yw):
            dy = abs(y - yc)
            if dy < 0.42:
                z = max(z, 0.27 + math.sqrt(0.42 ** 2 - dy ** 2))
        return z
    ys = set([-half, half] + [round(-half + i * 0.25, 3) for i in range(int(L / 0.25) + 1)])
    for yc in (-yw, yw):
        for k in range(-5, 6):
            ys.add(round(yc + k * 0.085, 3))
    for p in waist_pts:
        ys.add(round(p[0], 3))
    ys = sorted(y for y in ys if -half <= y <= half)

    def ring(y):
        w = wb(y); zw = waist(y); zb = zs(y)
        z3 = zw - 0.05
        z2 = min(max(zw - 0.28, zb + 0.12), z3 - 0.02)
        z1 = min(zb + 0.08, z2 - 0.02)
        right = [(w - 0.02, y, zb), (w + 0.015, y, z1), (w + 0.02, y, z2), (w, y, z3), (w - 0.07, y, zw)]
        top = (0.0, y, zw + 0.02)
        left = [(-x, yy, z) for (x, yy, z) in reversed(right)]
        return right + [top] + left
    rings = [ring(y) for y in ys]
    for A, B in zip(rings[:-1], rings[1:]):
        for i in range(len(A) - 1):
            pts = [A[i], B[i], B[i + 1], A[i + 1]]
            mb.face(pts, paint, True)
    # nose / tail caps (polygon of the ring, closed across the bottom)
    mb.face([Vector(p) for p in rings[0]], paint)                 # nose cap (orientation fixed after build)
    mb.face([Vector(p) for p in reversed(rings[-1])], paint)      # tail cap
    # underbody
    mb.box((-0.78, -half + 0.2, 0.17), (0.78, half - 0.2, 0.26), "car_trim_black")
    # cabin / greenhouse loft
    def cring(st):
        y, zr, wr = st
        zw = waist(y); w = wb(y)
        return [(w - 0.07, y, zw), (wr, y, zr), (0.0, y, zr + 0.03), (-wr, y, zr), (-(w - 0.07), y, zw)]
    crings = [cring(s) for s in cabin]
    for k, (A, B) in enumerate(zip(crings[:-1], crings[1:])):
        for i in range(4):
            side = i in (0, 3)
            if side:
                role = "car_glass" if k in glass_side else paint
            else:
                role = "car_glass" if k in glass_roof else paint
            pts = [A[i], B[i], B[i + 1], A[i + 1]]
            # drop duplicate points (windscreen base where roof edge == shoulder)
            clean = []
            for p in pts:
                if not clean or (Vector(p) - Vector(clean[-1])).length > 1e-6:
                    clean.append(p)
            if (Vector(clean[0]) - Vector(clean[-1])).length < 1e-6:
                clean.pop()
            if len(clean) >= 3:
                mb.face(clean, role, True)
    # door seams, handles, mirrors
    seams = [-0.75, 0.3, 1.3] if hatch else [-0.95, 0.15, 1.2]
    for sgn in (-1, 1):
        for yq in seams:
            x0, x1 = (0.80, 0.868) if sgn > 0 else (-0.868, -0.80)
            mb.box((x0, yq - 0.006, 0.30), (x1, yq + 0.006, waist(yq) - 0.08), "car_trim_black")
        for yh in ((-0.2, 0.85) if hatch else (-0.35, 0.75)):
            x0, x1 = (0.84, 0.885) if sgn > 0 else (-0.885, -0.84)
            mb.box((x0, yh - 0.09, 0.80), (x1, yh + 0.09, 0.835), "car_trim_black", inset=0.006, inset_face=("+x" if sgn > 0 else "-x"))
        my = cabin[0][0] + 0.25
        mb.box((sgn * 0.86 - 0.02, my - 0.05, 0.95), (sgn * 0.86 + 0.02, my + 0.05, 1.02), paint)
        mb.box((min(sgn * 0.86, sgn * 1.04) - 0.0, my - 0.08, 0.92), (max(sgn * 0.86, sgn * 1.04), my + 0.08, 1.05), paint, inset=0.012, inset_face=("+x" if sgn > 0 else "-x"))
        mb.face([(sgn * 1.04 + sgn * 0.001, my - 0.07, 0.93), (sgn * 1.04 + sgn * 0.001, my + 0.07, 0.93), (sgn * 1.04 + sgn * 0.001, my + 0.07, 1.04), (sgn * 1.04 + sgn * 0.001, my - 0.07, 1.04)][:: (1 if sgn > 0 else -1)], "car_glass")
    # wheels
    for sgn in (-1, 1):
        for yc in (-yw, yw):
            wtf = frame_tf((sgn * 0.62, yc, 0.31), (0, sgn, 0), (0, 0, 1))
            mb.lathe([(0.20, 0.0), (0.29, 0.02), (0.31, 0.06), (0.31, 0.16), (0.29, 0.20), (0.21, 0.22)], "rubber_black", 20, wtf, cap_bottom=True, cap_top=False)
            mb.lathe([(0.21, 0.22), (0.20, 0.235), (0.11, 0.235), (0.11, 0.215), (0.05, 0.215), (0.0, 0.215)], "car_wheel_rim", 20, wtf, cap_bottom=False, cap_top=False)
            for k in range(5):
                a = 2 * math.pi * k / 5
                mb.box((0.06 * math.cos(a) - 0.035, 0.06 * math.sin(a) - 0.035, 0.235), (0.06 * math.cos(a) + 0.035, 0.06 * math.sin(a) + 0.035, 0.238), "car_trim_black", wtf)
    # front: bumper, grille, headlights, plate
    yn = -half
    mb.box((-0.82, yn - 0.07, 0.34), (0.82, yn + 0.12, 0.52), "car_trim_black" if hatch else paint, inset=0.02, inset_face="-y")
    mb.box((-0.32, yn - 0.015, 0.56), (0.32, yn + 0.05, 0.64), "car_trim_black", inset=0.01, inset_face="-y")
    for sgn in (-1, 1):
        mb.box((min(sgn * 0.36, sgn * 0.72), yn - 0.02, 0.58), (max(sgn * 0.36, sgn * 0.72), yn + 0.06, 0.70), "car_light_front", inset=0.012, inset_face="-y")
        mb.box((min(sgn * 0.62, sgn * 0.78), yn - 0.03, 0.40), (max(sgn * 0.62, sgn * 0.78), yn + 0.05, 0.46), "sign_yellow")   # fog/indicator
    mb.box((-0.26, yn - 0.085, 0.38), (0.26, yn - 0.07, 0.49), "car_plate_white")
    # rear: bumper, lights, plate, exhaust
    yt = half
    mb.box((-0.82, yt - 0.12, 0.34), (0.82, yt + 0.07, 0.52), "car_trim_black" if hatch else paint, inset=0.02, inset_face="+y")
    for sgn in (-1, 1):
        mb.box((min(sgn * 0.42, sgn * 0.76), yt - 0.06, 0.60), (max(sgn * 0.42, sgn * 0.76), yt + 0.025, 0.82), "car_light_rear", inset=0.012, inset_face="+y")
        mb.box((min(sgn * 0.42, sgn * 0.76), yt - 0.05, 0.68), (max(sgn * 0.42, sgn * 0.76), yt + 0.03, 0.72), "car_plate_white")
    mb.box((-0.26, yt + 0.07, 0.38), (0.26, yt + 0.085, 0.49), "car_plate_yellow")
    mb.cyl((0, 0, 0), 0.025, 0.025, 0.2, "metal_dark", 10, frame_tf((0.55, yt - 0.1, 0.27), (0, 0, 1), (1, 0, 0)))   # exhaust along +Y
    # roof aerial
    mb.cyl((-0.45, cabin[-2][0] - 0.1, cabin[-2][1] + 0.02), 0.006, 0.004, 0.3, "metal_dark", 6)
    root = mb.build(f"exterior_parked_car_{variant}")
    # make sure the nose/tail caps face outward: flip faces whose normal points inward relative to the car centre
    me = root.data
    fix = []
    for p in me.polygons:
        if len(p.vertices) > 6:        # only the big caps are >6-gons
            c = p.center
            if (p.normal.y * c.y) < 0:
                fix.append(p.index)
    if fix:
        import bmesh as _bm
        bm = _bm.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        _bm.ops.reverse_faces(bm, faces=[bm.faces[i] for i in fix])
        bm.to_mesh(me); bm.free()
    notes = (("Hatchback (red) 4.0 m" if hatch else "Saloon (blue) 4.6 m") + ", 1.7 m wide. Bonnet faces -Y. Origin ground centre (tyre contact z=0). "
             "Roles car_paint_*, car_glass (transparent), car_light_rear / car_light_front (emissive-capable), car_plate_white/yellow (UK plates).")
    return root, dict(category="vehicle", views=("front34", "back34", "side"), notes=notes)


# ================================================================================================= driver

def build_terrace_a():
    return build_terrace("a")


def build_terrace_b():
    return build_terrace("b")


def build_parked_car_a():
    return build_car("a")


def build_parked_car_b():
    return build_car("b")


BUILDERS = {
    "shop_corner": build_shop_corner,
    "terrace_a": build_terrace_a,
    "terrace_b": build_terrace_b,
    "shop_props": build_shop_props,
    "street_lamp": build_street_lamp,
    "pavement_kerb": build_pavement_kerb,
    "parked_car_a": build_parked_car_a,
    "parked_car_b": build_parked_car_b,
}

try:
    import exterior_club            # second half of the family (club view + backdrops)
    importlib.reload(exterior_club)
    BUILDERS.update(exterior_club.BUILDERS)
except ImportError as e:
    print("exterior_club not available:", e)


def run(names, do_export=True, do_preview=True):
    for n in names:
        print(f"==== building {n}")
        bsk.clean_scene()
        root, info = BUILDERS[n]()
        name = f"{FAMILY}_{n}"
        tris = tri_count(root)
        lo, hi = dims(root)
        if do_export:
            bsk.export_fbx(root, FAMILY, name)
        paths = preview_views(root, name, views=info.get("views", ("front", "front34"))) if do_preview else []
        entry = dict(name=name, file=f"Assets/Bedsit/Art/Models/{FAMILY}/{name}.fbx", category=info.get("category", "exterior"),
                     dims_m=[round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)], tris=tris, roles=roles_of(root),
                     variant_of=info.get("variant_of"), notes=info.get("notes", ""), previews=[os.path.relpath(p, bsk.ROOT).replace("\\", "/") for p in paths])
        manifest_update(entry)
        print(f"==== {name}: {tris} tris, dims {entry['dims_m']}, previews {paths}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    names = list(BUILDERS.keys()) if argv == ["all"] else argv
    run(names)
