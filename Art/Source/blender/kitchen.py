"""kitchen - dishes, rubbish, cables & small tech clutter for the bedsit kit.

Run:  "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P Art/Source/blender/kitchen.py [-- --only mug,can --noexport --noview]
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, bsk, lib_kitchen
importlib.reload(bsk)
importlib.reload(lib_kitchen)
from lib_kitchen import *

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = []
if "--only" in ARGS:
    ONLY = ARGS[ARGS.index("--only") + 1].split(",")
EXPORT = "--noexport" not in ARGS
VIEWS = () if "--noview" in ARGS else ("front34", "back34")
CONTACT = "--contact" in ARGS

BUILDERS = []


def prop(fn):
    BUILDERS.append(fn)
    return fn


def wanted(name):
    return not ONLY or any(k in name for k in ONLY)


def xform_group(objs, loc=(0, 0, 0), rot_z=0.0, rot=None):
    """Move a group of placed objects together (rot_z degrees about Z, or full euler degrees)."""
    bpy.context.view_layer.update()
    e = Euler([math.radians(a) for a in (rot if rot else (0, 0, rot_z))])
    M = Matrix.Translation(Vector(loc)) @ e.to_matrix().to_4x4()
    for o in objs:
        o.matrix_world = M @ o.matrix_world
    return objs


def theta(c):
    return math.atan2(c.y, c.x)


def ang_near(a, b, width):
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return abs(d) < width


# ================================================================================================ DISHES / CUPS

def mug_profile(rb, rt, h, belly=None, wall=0.0035, floor=0.008, foot=0.004):
    """Closed mug profile: foot -> outer wall -> rim -> inner wall -> inner floor."""
    outer = [(0.0, 0.0015), (rb * 0.80, 0.0015), (rb * 0.86, 0.0), (rb * 0.96, 0.0), (rb, foot)]
    if belly:
        br, bz = belly
        # smooth bulge: sample a cosine from foot to top
        for k in range(1, 10):
            t = k / 10
            z = foot + (h - 0.006 - foot) * t
            r = rb + (rt - rb) * t + (br - (rb + (rt - rb) * (bz - foot) / (h - 0.006 - foot))) * math.sin(math.pi * t) ** 1.3
            outer.append((r, z))
    else:
        outer.append((rb + (rt - rb) * 0.5, foot + (h - foot) * 0.5))
    outer += [(rt, h - 0.006), (rt + 0.0004, h - 0.0025), (rt - 0.0005, h), (rt - wall + 0.0005, h), (rt - wall - 0.0003, h - 0.003)]
    inner = []
    if belly:
        for k in range(9, 0, -1):
            t = k / 10
            z = foot + (h - 0.006 - foot) * t
            r = rb + (rt - rb) * t + (br - (rb + (rt - rb) * (bz - foot) / (h - 0.006 - foot))) * math.sin(math.pi * t) ** 1.3
            inner.append((r - wall, z))
    else:
        inner.append((rb + (rt - rb) * 0.5 - wall, foot + (h - foot) * 0.5))
    inner += [(rb - wall, floor + 0.004), (rb - wall - 0.003, floor), (0.0, floor)]
    return outer + inner


def mug_handle(prefix, rt, h, role, size=1.0, r_at=None):
    """r_at(z) -> outer wall radius at height z (so the handle roots sit in the wall of bellied mugs, not inside)."""
    r_at = r_at or (lambda z: rt)
    r0, r1 = r_at(h * 0.80), r_at(h * 0.24)
    pts = catmull([(r0 - 0.003, 0, h * 0.80), (r0 + 0.012 * size, 0, h * 0.80), (max(r0, r1) + 0.028 * size, 0, h * 0.66),
                   (max(r0, r1) + 0.029 * size, 0, h * 0.45), (r1 + 0.016 * size, 0, h * 0.27), (r1 - 0.003, 0, h * 0.24)], n=7)
    return sweep(prefix + "_handle", pts, 0.0062, role, segments=12, rx=0.75, ry=1.15, up_hint=(0, 1, 0))


def mk_mug(prefix, kind="classic", role="ceramic_white", dirty=True, liquid="liquid_coffee", stain="stain_coffee", seed=0):
    rnd = random.Random(seed)
    if kind == "classic":
        rb, rt, h, belly = 0.037, 0.040, 0.095, None
    elif kind == "tall":
        rb, rt, h, belly = 0.034, 0.035, 0.110, None
    else:  # bellied
        rb, rt, h, belly = 0.033, 0.038, 0.090, (0.047, 0.045)
    wall, floor = 0.0035, 0.008
    body = rev(prefix + "_body", mug_profile(rb, rt, h, belly, wall, floor), role, segments=48)
    foot = 0.004

    def r_at(z):
        t = max(0.0, min(1.0, (z - foot) / (h - 0.006 - foot)))
        r = rb + (rt - rb) * t
        if belly:
            br, bz = belly
            r += (br - (rb + (rt - rb) * (bz - foot) / (h - 0.006 - foot))) * math.sin(math.pi * t) ** 1.3
        return r
    parts = [body, mug_handle(prefix, rt, h, role, r_at=r_at)]
    if dirty:
        lvl = floor + rnd.uniform(0.006, 0.016)
        # inner radius at the liquid level (approx)
        ri = (rb if not belly else rb + (belly[0] - rb) * math.sin(math.pi * (lvl - 0.004) / (h - 0.01)) ** 1.3) - wall + 0.0008
        parts.append(disc(prefix + "_liquid", ri, lvl, liquid, segments=48))
        # dried tide-ring on the inner wall above the liquid + drips on the rim where it was drunk from (opposite the handle)
        ring_h = rnd.uniform(0.012, 0.02)
        paint(body, stain, lambda c, n: (n.x * c.x + n.y * c.y) < 0 and lvl < c.z < lvl + ring_h and math.hypot(c.x, c.y) < rt - wall * 0.5 + 0.001)
        paint(body, stain, lambda c, n: c.z > h - 0.0035 and ang_near(theta(c), math.pi, 0.35))
        paint(body, stain, lambda c, n: (n.x * c.x + n.y * c.y) < 0 and c.z > h - 0.012 and ang_near(theta(c), math.pi + 0.1, 0.18))
    return parts


@prop
def build_mugs():
    specs = [("kitchen_mug_dirty_a", "classic", "ceramic_red", "liquid_coffee", "stain_coffee", 1, "classic mug, red, cold coffee + tide ring"),
             ("kitchen_mug_dirty_b", "tall", "ceramic_black", "liquid_tea", "stain_tea", 2, "tall straight mug, black, tea dregs + tannin ring"),
             ("kitchen_mug_dirty_c", "bellied", "ceramic_cream", "liquid_coffee", "stain_coffee", 3, "wide-bellied mug, cream, coffee dregs + ring")]
    for name, kind, role, liq, st, seed, note in specs:
        if not wanted(name):
            continue
        finish_prop(mk_mug(name, kind, role, True, liq, st, seed), name, "dishes",
                    f"{note}. Handle on +X. Rim at {0.095 if kind=='classic' else 0.11 if kind=='tall' else 0.09} m. Tidy partner: kitchen_mug_clean / kitchen_dish_tray.",
                    variant_of=None if name.endswith("_a") else "kitchen_mug_dirty_a", views=("front34", "top") if VIEWS else (), export=EXPORT)
    if wanted("kitchen_mug_clean"):
        finish_prop(mk_mug("kitchen_mug_clean", "classic", "ceramic_white", dirty=False), "kitchen_mug_clean", "dishes",
                    "Clean white classic mug, handle on +X, 9.5 cm tall. Tidy counterpart of kitchen_mug_dirty_*.", views=VIEWS, export=EXPORT)


def mk_glass(prefix, dirty=True, seed=0):
    rb, rt, h, wall, base = 0.031, 0.036, 0.145, 0.0025, 0.009
    prof = [(0, 0.0015), (rb * 0.8, 0.0015), (rb * 0.9, 0), (rb, 0.002), (rb + 0.0005, base),
            (rb + (rt - rb) * 0.5, base + (h - base) * 0.5), (rt, h - 0.002), (rt - 0.0005, h), (rt - wall, h),
            (rt - wall - 0.0003, h - 0.004), (rb - wall + (rt - rb) * 0.5, base + (h - base) * 0.5), (rb - wall, base + 0.003), (rb - wall - 0.002, base), (0, base)]
    g = rev(prefix + "_glass", prof, "glass_clear", segments=48)
    parts = [g]
    if dirty:
        parts.append(disc(prefix + "_dregs", rb - wall + 0.0005, base + 0.011, "liquid_beer", segments=48))
        paint(g, "stain_tea", lambda c, n: (n.x * c.x + n.y * c.y) < 0 and base + 0.011 < c.z < base + 0.02)
        # a few dried drip streaks inside
        paint(g, "stain_tea", lambda c, n: (n.x * c.x + n.y * c.y) < 0 and c.z > h - 0.03 and (ang_near(theta(c), 0.7, 0.07) or ang_near(theta(c), 2.9, 0.07)))
    return parts


@prop
def build_glass():
    if wanted("kitchen_glass_dirty"):
        finish_prop(mk_glass("kitchen_glass_dirty"), "kitchen_glass_dirty", "dishes",
                    "Tall hi-ball glass, 14.5 cm, flat beer dregs + tide ring inside. Tidy partner: kitchen_dish_tray.", views=VIEWS, export=EXPORT)


def plate_profile(R=0.13, well=0.095, h=0.025):
    return [(0, 0.0065), (well * 0.85, 0.0065), (well, 0.0095), (well + 0.01, 0.014), (R - 0.004, h - 0.0025), (R, h), (R + 0.0008, h - 0.0018),
            (R - 0.0008, h - 0.0038), (well + 0.012, 0.0105), (well + 0.002, 0.0045), (well * 0.95, 0.0005), (well * 0.87, 0.0), (well * 0.84, 0.0032), (0, 0.0032)]


def mk_plate(prefix, role="ceramic_white", R=0.13):
    return rev(prefix + "_plate", plate_profile(R, R * 0.73), role, segments=56)


def mk_fork(prefix, role="metal_steel"):
    """Fork lying along +Y, tines at +Y end, origin at handle end, resting on z=0."""
    # NB sweep(): for a horizontal path rx scales the VERTICAL (normal) axis, ry the horizontal one
    handle = sweep(prefix + "_fh", [V(0, 0, 0.0025), V(0, 0.05, 0.0025), V(0, 0.095, 0.0025), V(0, 0.11, 0.0022)],
                   [0.0045, 0.0052, 0.0045, 0.0032], role, segments=10, rx=0.55, ry=1.9)
    neck = catmull([V(0, 0.108, 0.0022), V(0, 0.125, 0.0032), V(0, 0.135, 0.0062), V(0, 0.145, 0.006)], n=6)
    nk = sweep(prefix + "_fn", neck, 0.0032, role, segments=10, rx=0.45, ry=1.9)
    head = rbox(prefix + "_fp", (0.024, 0.022, 0.0014), role, center=(0, 0.155, 0.0058), bevel=0.0005, segments=1)
    tines = [rbox(prefix + f"_t{i}", (0.0026, 0.03, 0.0014), role, center=(-0.0095 + i * 0.0063, 0.178, 0.0052), bevel=0.0005, segments=1) for i in range(4)]
    for t in tines:
        t.rotation_euler.x = math.radians(-6)
    return [handle, nk, head] + tines


def mk_knife(prefix, role="metal_steel"):
    handle = sweep(prefix + "_kh", [V(0, 0, 0.005), V(0, 0.05, 0.005), V(0, 0.1, 0.005), V(0, 0.112, 0.0045)],
                   [0.0062, 0.007, 0.0062, 0.0045], role, segments=12, rx=0.75, ry=1.25)
    blade = sweep(prefix + "_kb", [V(0, 0.11, 0.0035), V(0, 0.15, 0.0035), V(0, 0.19, 0.0035), V(0, 0.215, 0.0032), V(0, 0.225, 0.0030)],
                  [0.011, 0.011, 0.0095, 0.006, 0.0015], role, segments=10, rx=0.10, ry=1.0)
    return [handle, blade]


def mk_spoon(prefix, role="metal_steel", tea=False):
    s = 0.72 if tea else 1.0
    handle = sweep(prefix + "_sh", [V(0, 0, 0.0025 * s), V(0, 0.045 * s, 0.0025 * s), V(0, 0.09 * s, 0.0025 * s), V(0, 0.11 * s, 0.004 * s), V(0, 0.122 * s, 0.006 * s)],
                   [0.0042 * s, 0.0052 * s, 0.0040 * s, 0.0030 * s, 0.0028 * s], role, segments=10, rx=0.55, ry=1.9)
    prof = [(0, 0.0), (0.012, 0.0012), (0.018, 0.0062), (0.0195, 0.0085), (0.018, 0.009), (0.0165, 0.0068), (0.011, 0.0024), (0, 0.0012)]
    bowl = rev(prefix + "_sb", prof, role, segments=24)
    bowl.scale = (s, 1.55 * s, s)
    bowl.location = (0, 0.15 * s, 0.0)
    return [handle, bowl]


def mk_toast_crust(prefix, role_a="food_toast", role_b="food_crust", r=0.045, arc=(0.3, 2.4), seed=0):
    rnd = random.Random(seed)
    pts = []
    n = 14
    for i in range(n + 1):
        a = arc[0] + (arc[1] - arc[0]) * i / n
        rr = r * (1 + 0.04 * math.sin(a * 3 + seed))
        pts.append(V(rr * math.cos(a), rr * math.sin(a), 0.0055))
    ob = sweep(prefix, pts, 0.0065, role_a, segments=10, rx=1.5, ry=0.75, smooth_angle=50)
    displace_noise(ob, strength=0.0012, scale=0.012, seed=seed)
    paint(ob, role_b, lambda c, nn: math.hypot(c.x, c.y) > r + 0.003)
    return ob


def mk_plate_leftovers(prefix, kind="a", seed=0):
    rnd = random.Random(seed)
    parts = [mk_plate(prefix)]
    z = 0.0075
    if kind == "a":
        # toast crusts, a bean/ketchup smear, knife and fork dumped on it
        for i, (arc, loc, rot) in enumerate([((0.4, 2.3), (-0.035, 0.01), 20), ((3.4, 5.0), (0.02, 0.035), -35)]):
            c = mk_toast_crust(prefix + f"_crust{i}", arc=arc, seed=seed + i)
            c.location = (loc[0], loc[1], 0.0)
            c.rotation_euler.z = math.radians(rot)
            parts.append(c)
        smear = rev(prefix + "_smear", [(0, z + 0.0006), (0.02, z + 0.0012), (0.034, z + 0.0004)], "food_sauce", segments=28,
                    rmod=lambda th, ri, r, zz: r * (1 + 0.28 * math.sin(3 * th + 1.0) + 0.14 * math.sin(7 * th)))
        smear.location = (0.012, -0.03, 0)
        smear.scale = (1.0, 0.72, 1.0)
        parts.append(smear)
        for i in range(14):
            a = rnd.uniform(0, 6.28)
            rr = rnd.uniform(0, 0.022)
            b = ellipsoid(prefix + f"_bean{i}", 0.0058, 0.0040, 0.0028, "food_beans",
                          center=(0.012 + rr * math.cos(a) * 1.1, -0.03 + rr * math.sin(a) * 0.8, z + 0.0028), subdiv=1,
                          rot=(0, 0, rnd.uniform(0, 6.28)))
            parts.append(b)
        fk = mk_fork(prefix)
        xform_group(fk, loc=(0.035, -0.09, z), rot_z=-14)
        kn = mk_knife(prefix)
        xform_group(kn, loc=(0.075, -0.08, z), rot_z=-32)
        parts += fk + kn
    else:
        # chip remains + ketchup blob, a fork
        for i in range(9):
            L = rnd.uniform(0.02, 0.055)
            ch = rbox(prefix + f"_chip{i}", (0.009, L, 0.008), "food_chips", center=(rnd.uniform(-0.04, 0.04), rnd.uniform(-0.03, 0.04), z + 0.004), bevel=0.0025, segments=2)
            ch.rotation_euler = (0, math.radians(rnd.choice([0, 0, 0, 12])), math.radians(rnd.uniform(0, 180)))
            parts.append(ch)
        bits = [ellipsoid(prefix + f"_bit{i}", 0.006, 0.0045, 0.0035, "food_chips", center=(rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), z + 0.003), subdiv=1, rot=(0, 0, rnd.uniform(0, 3))) for i in range(5)]
        parts += bits
        blob = rev(prefix + "_ketchup", [(0, z + 0.0025), (0.009, z + 0.0022), (0.016, z + 0.0004)], "food_sauce", segments=24,
                   rmod=lambda th, ri, r, zz: r * (1 + 0.2 * math.sin(2 * th + 0.5) + 0.1 * math.sin(5 * th)))
        blob.location = (0.055, 0.045, 0)
        parts.append(blob)
        fk = mk_fork(prefix)
        xform_group(fk, loc=(-0.06, -0.09, z), rot_z=28)
        parts += fk
    return parts


@prop
def build_plates():
    if wanted("kitchen_plate_leftovers_a"):
        finish_prop(mk_plate_leftovers("kitchen_plate_leftovers_a", "a", 1), "kitchen_plate_leftovers_a", "dishes",
                    "26 cm dinner plate with toast crusts, bean/ketchup smear, knife + fork on it. Rim top 2.5 cm. Tidy partner: kitchen_plate_clean / kitchen_dish_tray.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_plate_leftovers_b"):
        finish_prop(mk_plate_leftovers("kitchen_plate_leftovers_b", "b", 2), "kitchen_plate_leftovers_b", "dishes",
                    "26 cm plate with cold chip remains, ketchup blob and a fork. Tidy partner: kitchen_plate_clean / kitchen_dish_tray.",
                    variant_of="kitchen_plate_leftovers_a", views=VIEWS, export=EXPORT)
    if wanted("kitchen_plate_clean"):
        finish_prop([mk_plate("kitchen_plate_clean")], "kitchen_plate_clean", "dishes",
                    "Clean 26 cm white dinner plate, 2.5 cm tall; stackable. Tidy counterpart of kitchen_plate_leftovers_*.", views=VIEWS, export=EXPORT)


def bowl_profile(R=0.075, h=0.065):
    out = [(0, 0.0045), (0.03, 0.0045), (0.036, 0.0075)]
    for k in range(1, 8):
        t = k / 8
        out.append((0.036 + (R - 0.036) * math.sin(t * math.pi / 2) ** 0.85, 0.0075 + (h - 0.0075) * t))
    out += [(R, h), (R + 0.0006, h - 0.0015), (R - 0.0005, h - 0.0035)]
    for k in range(7, 0, -1):
        t = k / 8
        out.append((0.036 + (R - 0.036) * math.sin(t * math.pi / 2) ** 0.85 - 0.0035, 0.0075 + (h - 0.0075) * t - 0.0012))
    out += [(0.033, 0.0045), (0.030, 0.0), (0.026, 0.0), (0.024, 0.0025), (0, 0.0025)]
    return out


def mk_bowl_cereal(prefix, seed=0):
    rnd = random.Random(seed)
    bowl = rev(prefix + "_bowl", bowl_profile(), "ceramic_white", segments=48)
    paint(bowl, "ceramic_blue", lambda c, n: c.z > 0.058 and math.hypot(c.x, c.y) > 0.07)   # blue rim stripe
    lvl = 0.021
    rl = 0.036 + (0.075 - 0.036) * math.sin(((lvl - 0.0075) / (0.065 - 0.0075)) * math.pi / 2) ** 0.85 - 0.0035 + 0.0008
    milk = disc(prefix + "_milk", rl, lvl, "liquid_milk", segments=48)
    paint(bowl, "stain_tea", lambda c, n: (n.x * c.x + n.y * c.y) < 0 and lvl < c.z < lvl + 0.007)
    parts = [bowl, milk]
    for i in range(7):
        a = rnd.uniform(0, 6.28)
        rr = rnd.uniform(0.004, rl * 0.8)
        fl = rev(prefix + f"_flake{i}", [(0, lvl + 0.0005), (0.006, lvl + 0.0022), (0.009, lvl + 0.0008)], "food_cereal", segments=12,
                 rmod=lambda th, ri, r, z, s=i: r * (1 + 0.18 * math.sin(3 * th + s)))
        fl.location = (rr * math.cos(a), rr * math.sin(a), 0)
        fl.rotation_euler = (math.radians(rnd.uniform(-20, 20)), math.radians(rnd.uniform(-20, 20)), 0)
        parts.append(fl)
    sp = mk_spoon(prefix, tea=False)
    bpy.context.view_layer.update()
    for o in sp:
        o.matrix_world = Matrix.Scale(0.85, 4) @ o.matrix_world
    # spoon resting in the bowl: bowl end in the milk (y=-0.005, z=0.017), handle lying over the -Y rim at ~37 deg
    ang = math.radians(36.5)
    L = 0.157
    origin = V(0.0, -0.005 - L * math.cos(ang), 0.017 + L * math.sin(ang))
    for o in sp:
        o.matrix_world = Matrix.Rotation(math.radians(6), 4, "Z") @ Matrix.Translation(origin) @ Matrix.Rotation(-ang, 4, "X") @ o.matrix_world
    parts += sp
    return parts


@prop
def build_bowl():
    if wanted("kitchen_bowl_cereal"):
        finish_prop(mk_bowl_cereal("kitchen_bowl_cereal", 3), "kitchen_bowl_cereal", "dishes",
                    "15 cm cereal bowl (blue rim stripe) with milk film, soggy flakes and a spoon resting on the rim (-Y). Rim at 6.5 cm. Tidy partner: kitchen_dish_tray.", views=VIEWS, export=EXPORT)


@prop
def build_cutlery():
    if not wanted("kitchen_cutlery_loose"):
        return
    p = "kitchen_cutlery_loose"
    parts = []
    parts += xform_group(mk_fork(p + "_f1"), loc=(-0.03, -0.09, 0), rot_z=12)
    parts += xform_group(mk_knife(p + "_k1"), loc=(0.02, -0.1, 0), rot_z=-8)
    parts += xform_group(mk_spoon(p + "_s1"), loc=(0.055, -0.07, 0), rot_z=-30)
    parts += xform_group(mk_spoon(p + "_s2", tea=True), loc=(-0.07, -0.02, 0), rot_z=75)
    parts += xform_group(mk_fork(p + "_f2"), loc=(0.0, 0.03, 0.0), rot=(180, 0, 100))
    settle(parts)
    finish_prop(parts, p, "dishes", "Loose cutlery dumped on a surface: 2 forks (one face down), knife, spoon, teaspoon, ~0.22 x 0.2 m footprint. Tidy partner: kitchen_dish_tray.",
                views=VIEWS, export=EXPORT)


def mk_dish_tray(prefix):
    W, D, H = 0.40, 0.30, 0.012
    role_w = "metal_steel"
    parts = []
    # drip tray: floor + 4 lips
    parts.append(rbox(prefix + "_tray", (W, D, 0.003), "plastic_white", center=(0, 0, 0.0015), bevel=0.001))
    for sx in (-1, 1):
        parts.append(rbox(prefix + f"_lipx{sx}", (0.004, D, H), "plastic_white", center=(sx * (W / 2 - 0.002), 0, H / 2), bevel=0.0015))
    for sy in (-1, 1):
        parts.append(rbox(prefix + f"_lipy{sy}", (W, 0.004, H), "plastic_white", center=(0, sy * (D / 2 - 0.002), H / 2), bevel=0.0015))
    # wire rack: base frame
    w, d, zb = 0.36, 0.25, 0.03
    r = 0.0022
    frame = [V(-w / 2, -d / 2, zb), V(w / 2, -d / 2, zb), V(w / 2, d / 2, zb), V(-w / 2, d / 2, zb)]
    fr = sweep(prefix + "_frame", catmull(frame, n=4, closed=True), r, role_w, segments=8, closed=True)
    parts.append(fr)
    for x in (-w / 2 + 0.02, w / 2 - 0.02):
        for y in (-d / 2 + 0.02, d / 2 - 0.02):
            parts.append(cylinder(prefix + f"_leg{x:.2f}{y:.2f}", r, zb, role_w, segments=8, center=(x, y, 0.003), bevel=0))
    # two rows of U prongs (plate slots) + cross wires
    for yy in (-0.045, 0.045):
        for i in range(9):
            x = -w / 2 + 0.03 + i * 0.0375
            pts = catmull([V(x - 0.009, yy, zb), V(x - 0.009, yy, zb + 0.07), V(x - 0.006, yy, zb + 0.10), V(x, yy, zb + 0.112),
                           V(x + 0.006, yy, zb + 0.10), V(x + 0.009, yy, zb + 0.07), V(x + 0.009, yy, zb)], n=4)
            parts.append(sweep(prefix + f"_prong{yy}{i}", pts, r, role_w, segments=8))
    for yy in (-0.045, 0.045, -0.1, 0.1):
        parts.append(sweep(prefix + f"_cross{yy}", [V(-w / 2, yy, zb), V(w / 2, yy, zb)], r, role_w, segments=8))
    # cutlery cup at the right end (perforated look via dark paint rows)
    cup = rev(prefix + "_cup", [(0, zb + 0.001), (0.028, zb + 0.001), (0.03, zb + 0.004), (0.031, zb + 0.11), (0.0295, zb + 0.11), (0.029, zb + 0.004), (0, zb + 0.004)], "plastic_white", segments=28)
    cup.location = (w / 2 - 0.035, -0.0, 0)
    for k in range(3):
        paint(cup, "plastic_grey", lambda c, n, k=k: (n.x * c.x + n.y * c.y) > 0 and zb + 0.03 + k * 0.025 < c.z < zb + 0.038 + k * 0.025 and int((theta(c) + 3.2) / 0.3) % 2 == 0)
    parts.append(cup)
    # clean things in it: two plates standing in the slots, a mug upside down, a glass, a fork in the cup
    for i, x in enumerate((-0.11, -0.065)):
        pl = mk_plate(prefix + f"_cp{i}")
        pl.rotation_euler = (math.radians(80 if i == 0 else 83), 0, 0)
        pl.location = (x, 0.012, zb + 0.13)
        parts.append(pl)
    mug = mk_mug(prefix + "_cm", "classic", "ceramic_white", dirty=False)
    xform_group(mug, loc=(0.03, 0.03, zb + 0.097), rot=(180, 0, 40))
    parts += mug
    gl = mk_glass(prefix + "_cg", dirty=False)
    xform_group(gl, loc=(0.075, -0.06, zb + 0.147), rot=(180, 0, 0))
    parts += gl
    fk = mk_fork(prefix + "_cf")
    xform_group(fk, loc=(w / 2 - 0.035, 0.0, zb + 0.015), rot=(80, 0, 20))
    parts += fk
    return parts


@prop
def build_dish_tray():
    if wanted("kitchen_dish_tray"):
        finish_prop(mk_dish_tray("kitchen_dish_tray"), "kitchen_dish_tray", "dishes",
                    "Wire dish rack on a white drip tray, 0.40 x 0.30 m, 0.19 m tall with 2 clean plates, mug and glass upside down, fork in the cutlery cup. "
                    "The TIDY destination for dirty dishes. Tray top 1.2 cm, rack base 3 cm.", views=VIEWS, export=EXPORT)


# ================================================================================================ RUBBISH - cans & bottles

def can_profile():
    return [(0, 0.0055), (0.012, 0.0055), (0.020, 0.0035), (0.025, 0.0006), (0.0268, 0.0), (0.029, 0.0012), (0.0312, 0.0045), (0.0328, 0.009), (0.033, 0.014),
            (0.033, 0.098), (0.0325, 0.1025), (0.0300, 0.1075), (0.0282, 0.1115), (0.0288, 0.1135), (0.0294, 0.115), (0.0286, 0.1165), (0.0270, 0.1163),
            (0.0262, 0.1145), (0.0258, 0.1125), (0, 0.1125)]


def mk_can(prefix, body_role="can_red", opened=True, tab_up=False, dents=(), seed=0):
    can = rev(prefix + "_can", can_profile(), "aluminium", segments=40)
    paint(can, body_role, zband(0.0095, 0.1045))
    parts = [can]
    # rivet + ring-pull on the lid (lid at z=0.1125)
    zl = 0.1125
    parts.append(cylinder(prefix + "_rivet", 0.002, 0.0012, "aluminium", segments=10, center=(0.0, -0.002, zl), bevel=0.0003))
    if tab_up:
        tab = rbox(prefix + "_tab", (0.0085, 0.019, 0.0008), "aluminium", center=(0, 0, 0), bevel=0.0004, segments=1)
        tab.location = (0, -0.002, zl + 0.0012)
        tab.rotation_euler.x = math.radians(-70)
        tab.location.y -= 0.004
        tab.location.z += 0.008
    else:
        tab = rbox(prefix + "_tab", (0.0085, 0.019, 0.0008), "aluminium", center=(0, 0.0065, zl + 0.0016), bevel=0.0004, segments=1)
    parts.append(tab)
    if opened:
        # the pressed-in opening (dark hole)
        hole = rev(prefix + "_hole", [(0, zl - 0.0004), (0.0055, zl - 0.0004)], "plastic_black", segments=16)
        hole.location = (0, -0.013, 0)
        hole.scale = (1.0, 1.35, 1.0)
        parts.append(hole)
    for (th, z, rad, depth) in dents:
        dent(can, (0.033 * math.cos(th), 0.033 * math.sin(th), z), rad, depth)
    return parts


@prop
def build_cans():
    # a: standing red, slightly dented
    if wanted("kitchen_can_a"):
        parts = mk_can("kitchen_can_a", "can_red", opened=True, dents=[(2.2, 0.045, 0.022, 0.006), (4.0, 0.08, 0.016, 0.003)], seed=1)
        finish_prop(parts, "kitchen_can_a", "rubbish", "330 ml drinks can standing, red, opened, dented side. 11.6 cm tall, 6.6 cm dia.", views=VIEWS, export=EXPORT)
    # b: crushed silver
    if wanted("kitchen_can_b"):
        parts = mk_can("kitchen_can_b", "can_silver", opened=True, seed=2)
        for o in parts:
            apply_xform(o)
        can = merge(parts, "kitchen_can_b_m")
        crush_can(can, k=0.42, lean=0.10, seed=2, amp=0.11)
        dent(can, (0.03, 0.01, 0.025), 0.03, 0.009)
        finish_prop([can], "kitchen_can_b", "rubbish", "330 ml can stamped flat-ish: 5 cm tall, buckled body, silver. Opened.", variant_of="kitchen_can_a", views=VIEWS, export=EXPORT)
    # c: tipped over blue
    if wanted("kitchen_can_c"):
        parts = mk_can("kitchen_can_c", "can_blue", opened=True, dents=[(1.3, 0.06, 0.03, 0.008)], seed=3)
        xform_group(parts, rot=(0, 92, 25))
        settle(parts)
        finish_prop(parts, "kitchen_can_c", "rubbish", "330 ml blue can lying on its side (axis ~X), big dent, opened. 6.6 cm high when lying.", variant_of="kitchen_can_a", views=VIEWS, export=EXPORT)
    # d: standing black with the ring-pull lifted
    if wanted("kitchen_can_d"):
        parts = mk_can("kitchen_can_d", "can_black", opened=True, tab_up=True, dents=[(5.2, 0.03, 0.02, 0.004)], seed=4)
        xform_group(parts, rot=(2.5, -1.5, 0))
        settle(parts)
        finish_prop(parts, "kitchen_can_d", "rubbish", "330 ml black energy-style can standing slightly tilted, ring-pull lifted up, small dent.", variant_of="kitchen_can_a", views=VIEWS, export=EXPORT)


def bottle_profile(R, H, body_top, neck_r, neck_start, lip_r=None, wall=0.003, punt=0.004, shoulder_pow=1.0):
    """Hollow bottle: outer + inner surfaces. body_top = z where shoulder starts, neck_start = z where neck is reached."""
    lip_r = lip_r or neck_r + 0.0018
    out = [(0, punt), (R * 0.55, punt * 0.5), (R * 0.8, 0.0), (R * 0.93, 0.0), (R, 0.004), (R, body_top)]
    for k in range(1, 7):
        t = k / 7
        z = body_top + (neck_start - body_top) * t
        r = neck_r + (R - neck_r) * (1 - t ** shoulder_pow) ** 0.75 * (1 - 0.0) if True else 0
        # smooth cosine shoulder
        r = neck_r + (R - neck_r) * (0.5 + 0.5 * math.cos(math.pi * t)) ** (1 / shoulder_pow)
        out.append((r, z))
    out += [(neck_r, neck_start), (neck_r, H - 0.012), (lip_r, H - 0.009), (lip_r, H - 0.0015), (lip_r - 0.0012, H), (neck_r - wall + 0.0008, H),
            (neck_r - wall, H - 0.004), (neck_r - wall, neck_start - 0.002)]
    for k in range(6, 0, -1):
        t = k / 7
        z = body_top + (neck_start - body_top) * t
        r = neck_r + (R - neck_r) * (0.5 + 0.5 * math.cos(math.pi * t)) ** (1 / shoulder_pow)
        out.append((r - wall, z))
    out += [(R - wall, body_top), (R - wall, 0.008), (R * 0.75, punt + wall), (0, punt + wall)]
    return out


def mk_bottle_beer(prefix, glass="glass_brown", label="label_red", seed=0, lying=False, label2=None):
    R, H = 0.0305, 0.232
    prof = bottle_profile(R, H, 0.125, 0.0135, 0.185, lip_r=0.0152, wall=0.0028)
    b = rev(prefix + "_bottle", prof, glass, segments=40)
    paint(b, label, lambda c, n: (n.x * c.x + n.y * c.y) > 0 and 0.03 < c.z < 0.105 and math.hypot(c.x, c.y) > R - 0.001)
    paint(b, label2 or label, lambda c, n: (n.x * c.x + n.y * c.y) > 0 and 0.145 < c.z < 0.17)
    dregs = rev(prefix + "_dregs", [(0, 0.0095), (R - 0.0028 + 0.0005, 0.0095), (R - 0.0028 + 0.0005, 0.016), (0, 0.016)], "liquid_beer", segments=40)
    parts = [b, dregs]
    if lying:
        xform_group(parts, rot=(0, 90, 0))
        settle(parts)
    return parts


def mk_bottle_wine(prefix):
    R, H = 0.0375, 0.300
    prof = bottle_profile(R, H, 0.185, 0.0145, 0.238, lip_r=0.016, wall=0.0035, punt=0.018, shoulder_pow=1.2)
    b = rev(prefix + "_bottle", prof, "glass_green", segments=44)
    paint(b, "label_paper", lambda c, n: (n.x * c.x + n.y * c.y) > 0 and 0.055 < c.z < 0.15 and math.hypot(c.x, c.y) > R - 0.001 and ang_near(theta(c), -math.pi / 2, 1.05))
    paint(b, "label_black", lambda c, n: (n.x * c.x + n.y * c.y) > 0 and c.z > 0.252)      # capsule
    paint(b, "label_red", lambda c, n: (n.x * c.x + n.y * c.y) > 0 and 0.262 < c.z < 0.268 and math.hypot(c.x, c.y) > 0.013)
    dregs = rev(prefix + "_dregs", [(0, 0.0215), (R - 0.0035 + 0.0005, 0.0215), (R - 0.0035 + 0.0005, 0.028), (0, 0.028)], "liquid_wine", segments=40)
    return [b, dregs]


def cap_ribbed(prefix, r, h, role, z, teeth=28, depth=0.00045, segments=56):
    prof = [(0, z + h), (r - 0.0015, z + h), (r, z + h - 0.0012), (r, z + 0.0006), (r - 0.0008, z), (0, z)]
    return rev(prefix + "_cap", prof, role, segments=segments,
               rmod=lambda th, ri, rr, zz: rr + (depth * math.sin(th * teeth) if 2 <= ri <= 3 else 0.0), smooth_angle=30)


def mk_bottle_cola(prefix, lying=False):
    R, H = 0.0325, 0.228
    pts = [(0, 0.0045), (0.012, 0.0045), (0.021, 0.001), (0.0265, 0.0), (0.03, 0.003), (R, 0.012), (R, 0.055), (R - 0.0015, 0.07),
           (0.0285, 0.085), (0.0275, 0.1), (0.0285, 0.115), (0.0305, 0.128), (R, 0.142), (R, 0.158)]
    for k in range(1, 6):
        t = k / 6
        pts.append((0.0125 + (R - 0.0125) * (0.5 + 0.5 * math.cos(math.pi * t)) ** 0.9, 0.158 + (0.198 - 0.158) * t))
    pts += [(0.0125, 0.198), (0.0125, 0.203), (0.0145, 0.2035), (0.0145, 0.207), (0.0125, 0.2075), (0.0125, 0.21), (0.012, 0.2102), (0.012, 0.209), (0.0115, 0.207),
            (0.0115, 0.195)]
    for k in range(5, 0, -1):
        t = k / 6
        pts.append((0.0125 + (R - 0.0125) * (0.5 + 0.5 * math.cos(math.pi * t)) ** 0.9 - 0.0008, 0.158 + (0.198 - 0.158) * t))
    pts += [(R - 0.0008, 0.158), (R - 0.0008, 0.142), (0.0297, 0.128), (0.0277, 0.115), (0.0267, 0.1), (0.0277, 0.085), (R - 0.0023, 0.07), (R - 0.0008, 0.055), (R - 0.0008, 0.012), (0.029, 0.0045), (0.021, 0.0025), (0, 0.006)]
    # 5-lobe petaloid base on the lowest rings
    def rmod(th, ri, r, z):
        if ri in (1, 2, 3, 4) or ri >= len(pts) - 3:
            return r * (1 + 0.05 * math.cos(5 * th))
        return r
    b = rev(prefix + "_bottle", pts, "plastic_clear", segments=40, rmod=rmod)
    paint(b, "label_red", lambda c, n: (n.x * c.x + n.y * c.y) > 0 and 0.076 < c.z < 0.128 and math.hypot(c.x, c.y) > 0.026)
    cap = cap_ribbed(prefix, 0.0152, 0.016, "plastic_red", 0.2105, teeth=30)
    cola = rev(prefix + "_cola", [(0, 0.006), (0.0268, 0.006), (0.0285, 0.012), (0.0285, 0.034), (0, 0.034)], "liquid_cola", segments=40)
    parts = [b, cap, cola]
    if lying:
        xform_group(parts, rot=(0, 90, 0))
        settle(parts)
    return parts


def mk_bottle_water(prefix, seed=0):
    R, H = 0.0315, 0.205
    pts = [(0, 0.004), (0.015, 0.004), (0.024, 0.0005), (0.028, 0.0), (R, 0.005), (R, 0.02)]
    z = 0.02
    while z < 0.14:
        pts.append((R - 0.0022, z + 0.004))
        pts.append((R - 0.0022, z + 0.007))
        pts.append((R, z + 0.011))
        pts.append((R, z + 0.015))
        z += 0.015
    pts += [(R, 0.15)]
    for k in range(1, 6):
        t = k / 6
        pts.append((0.0125 + (R - 0.0125) * (0.5 + 0.5 * math.cos(math.pi * t)) ** 0.8, 0.15 + (0.185 - 0.15) * t))
    pts += [(0.0125, 0.185), (0.0125, 0.19), (0.0145, 0.1905), (0.0145, 0.193), (0.0125, 0.1935), (0.0125, 0.196), (0.0118, 0.196), (0.0118, 0.186), (0, 0.186)]
    b = rev(prefix + "_bottle", pts, "plastic_clear", segments=36, smooth_angle=50)
    paint(b, "label_blue", lambda c, n: 0.055 < c.z < 0.098 and math.hypot(c.x, c.y) > 0.027)
    cap = cap_ribbed(prefix, 0.0148, 0.013, "plastic_blue", 0.1965, teeth=26)
    water = rev(prefix + "_water", [(0, 0.005), (0.028, 0.005), (0.029, 0.009), (0.029, 0.022), (0, 0.022)], "liquid_water", segments=36)
    for o in (b, cap, water):
        apply_xform(o)
    m = merge([b, cap, water], prefix + "_m")
    crush_can(m, k=0.80, lean=0.06, seed=seed, amp=0.13)
    dent(m, (0.03, 0.01, 0.07), 0.045, 0.014)
    dent(m, (-0.02, -0.025, 0.10), 0.03, 0.008)
    m.rotation_euler = (0, math.radians(88), math.radians(-30))
    settle([m])
    return [m]


@prop
def build_bottles():
    if wanted("kitchen_bottle_beer_green"):
        finish_prop(mk_bottle_beer("kitchen_bottle_beer_green", "glass_green", "label_paper", label2="label_green"), "kitchen_bottle_beer_green", "rubbish",
                    "330 ml green long-neck beer bottle standing, no cap, dregs inside, paper label facing -Y... (label wraps). 23 cm tall.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_bottle_beer_brown"):
        finish_prop(mk_bottle_beer("kitchen_bottle_beer_brown", "glass_brown", "label_red", label2="label_black", lying=True), "kitchen_bottle_beer_brown", "rubbish",
                    "330 ml brown beer bottle lying on its side (neck +X), red label, dregs. 6 cm high when lying.", variant_of="kitchen_bottle_beer_green", views=VIEWS, export=EXPORT)
    if wanted("kitchen_bottle_cola"):
        finish_prop(mk_bottle_cola("kitchen_bottle_cola"), "kitchen_bottle_cola", "rubbish",
                    "500 ml PET cola bottle with red ribbed cap and red label band, 2 cm of flat cola left. 22.7 cm tall.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_bottle_water_plastic"):
        finish_prop(mk_bottle_water("kitchen_bottle_water_plastic", 5), "kitchen_bottle_water_plastic", "rubbish",
                    "500 ml ribbed PET water bottle, crumpled/buckled, blue cap, lying on its side.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_bottle_wine"):
        finish_prop(mk_bottle_wine("kitchen_bottle_wine"), "kitchen_bottle_wine", "rubbish",
                    "75 cl green wine bottle, 30 cm, paper label facing -Y, black capsule, red dregs, punt. Standing.", views=VIEWS, export=EXPORT)


# ================================================================================================ RUBBISH - packaging

def mk_pizza_slice(prefix, r=0.145, ang=48, z=0.0, seed=0):
    rnd = random.Random(seed)
    a0, a1 = math.radians(-ang / 2), math.radians(ang / 2)
    arc = [(r * math.cos(a0 + (a1 - a0) * i / 8), r * math.sin(a0 + (a1 - a0) * i / 8)) for i in range(9)]
    base = poly_prism(prefix + "_base", [(0.012, 0)] + arc, z, z + 0.010, "food_pizza")
    cheese = poly_prism(prefix + "_cheese", [(0.03, 0)] + [((r - 0.018) * math.cos(a0 * 0.9 + (a1 - a0) * 0.9 * i / 8), (r - 0.018) * math.sin(a0 * 0.9 + (a1 - a0) * 0.9 * i / 8)) for i in range(9)],
                        z + 0.0095, z + 0.0125, "food_cheese")
    subdivide(cheese, 2)
    displace_noise(cheese, strength=0.0015, scale=0.015, seed=seed)
    crust = sweep(prefix + "_crust", [V((r - 0.004) * math.cos(a0 + (a1 - a0) * i / 10), (r - 0.004) * math.sin(a0 + (a1 - a0) * i / 10), z + 0.011) for i in range(11)],
                  0.0095, "food_crust", segments=10, rx=0.9, ry=1.1)
    displace_noise(crust, strength=0.0012, scale=0.02, seed=seed + 1)
    parts = [base, cheese, crust]
    for i in range(3):
        rr = rnd.uniform(0.05, r - 0.035)
        aa = rnd.uniform(a0 * 0.6, a1 * 0.6)
        parts.append(cylinder(prefix + f"_pep{i}", 0.015, 0.002, "food_pepperoni", segments=16, center=(rr * math.cos(aa), rr * math.sin(aa), z + 0.0125), bevel=0.0006))
    return parts


def mk_pizza_box(prefix, open_deg=None, slice_=True, seed=0, ajar=0.0):
    S, H, T = 0.33, 0.045, 0.004
    rnd = random.Random(seed)
    parts = []
    parts.append(rbox(prefix + "_floor", (S, S, T), "cardboard", center=(0, 0, T / 2), bevel=0.0015))
    inner = sheet(prefix + "_inner", S - 2 * T, S - 2 * T, 36, 36, "cardboard")
    inner.location.z = T + 0.0003
    blobs = [(-0.04 + rnd.uniform(-0.02, 0.02), 0.03 + rnd.uniform(-0.02, 0.02), 0.07), (0.07, -0.06, 0.045), (0.09, 0.08, 0.03), (-0.1, -0.09, 0.035), (0.0, -0.11, 0.025)]
    paint(inner, "food_grease", lambda c, n: any(math.hypot((c.x - bx) * 1.0, (c.y - by) * 1.25) < br for bx, by, br in blobs))
    parts.append(inner)
    for sx in (-1, 1):
        parts.append(rbox(prefix + f"_wx{sx}", (T, S, H), "cardboard", center=(sx * (S / 2 - T / 2), 0, H / 2), bevel=0.0015))
    for sy in (-1, 1):
        parts.append(rbox(prefix + f"_wy{sy}", (S - 2 * T, T, H), "cardboard", center=(0, sy * (S / 2 - T / 2), H / 2), bevel=0.0015))
    # lid (hinged at the back edge y=+S/2, z=H)
    lid = [rbox(prefix + "_lid", (S + 0.002, S + 0.002, T), "cardboard", center=(0, 0, H + T / 2), bevel=0.0015)]
    for sx in (-1, 1):
        lid.append(rbox(prefix + f"_lx{sx}", (T, S - 0.01, H - 0.003), "cardboard", center=(sx * (S / 2 + 0.001 + T / 2), -0.005, H - (H - 0.003) / 2 + 0.002), bevel=0.0015))
    lid.append(rbox(prefix + "_lf", (S + 0.002 + 2 * T, T, H - 0.003), "cardboard", center=(0, -(S / 2 + 0.001 + T / 2), H - (H - 0.003) / 2 + 0.002), bevel=0.0015))
    top = sheet(prefix + "_top", S - 0.02, S - 0.02, 16, 16, "cardboard")
    top.location.z = H + T + 0.0003
    paint(top, "print_red", lambda c, n: abs(c.x) < 0.09 and abs(c.y + 0.01) < 0.05 and not (abs(c.x) < 0.075 and abs(c.y + 0.01) < 0.035))
    paint(top, "print_red", lambda c, n: abs(c.y - 0.11) < 0.012)
    lid.append(top)
    if open_deg is not None:
        for o in lid:
            rot_about(o, (0, S / 2, H), (1, 0, 0), open_deg)
    elif ajar:
        for o in lid:
            rot_about(o, (0, S / 2, H), (1, 0, 0), ajar)
    parts += lid
    if slice_:
        sl = mk_pizza_slice(prefix + "_slice", z=T + 0.0006, seed=seed)
        xform_group(sl, loc=(-0.075, -0.02, 0), rot_z=rnd.uniform(-30, 30))
        parts += sl
        # a stray crust end
        c2 = sweep(prefix + "_crustbit", [V(0.06 + 0.05 * math.cos(a), 0.09 + 0.05 * math.sin(a), T + 0.0096) for a in [math.radians(x) for x in range(20, 80, 10)]],
                   0.0085, "food_crust", segments=8, rx=0.9, ry=1.0)
        parts.append(c2)
    return parts


@prop
def build_pizza_boxes():
    if wanted("kitchen_pizza_box_open"):
        finish_prop(mk_pizza_box("kitchen_pizza_box_open", open_deg=112, slice_=True, seed=7), "kitchen_pizza_box_open", "rubbish",
                    "33 cm pizza box, lid open ~112 deg leaning back (+Y), greasy inner floor, one slice left + a crust end. Box top edge 4.5 cm; lid rises to ~0.35 m behind.",
                    views=VIEWS, export=EXPORT)
    if wanted("kitchen_pizza_box_closed"):
        finish_prop(mk_pizza_box("kitchen_pizza_box_closed", open_deg=None, slice_=False, seed=8, ajar=5), "kitchen_pizza_box_closed", "rubbish",
                    "33 cm closed pizza box, lid slightly ajar, red print on top. 5-8 cm tall; stackable surface at 5 cm.",
                    variant_of="kitchen_pizza_box_open", views=VIEWS, export=EXPORT)


def mk_carton(prefix, seed=0, open_top=False):
    rnd = random.Random(seed)
    bw, bd, tw, td, h = 0.043, 0.036, 0.056, 0.048, 0.10
    rings = [[(-bw, -bd, 0), (bw, -bd, 0), (bw, bd, 0), (-bw, bd, 0)]]
    for k in range(1, 6):
        t = k / 5
        w, d = bw + (tw - bw) * t, bd + (td - bd) * t
        rings.append([(-w, -d, h * t), (w, -d, h * t), (w, d, h * t), (-w, d, h * t)])
    body = loft(prefix + "_body", rings, "paper_white", close_bottom=True)
    subdivide(body, 1)
    solidify(body, 0.0009)
    # small red pagoda-ish logo on the front (-Y) face
    paint(body, "print_red", lambda c, n: n.y < -0.5 and abs(c.x) < 0.014 and 0.045 < c.z < 0.075)
    parts = [body]
    if open_top:
        # flaps splayed open
        fl = [quad(prefix + "_fa", [(-tw, -td, h), (tw, -td, h), (tw - 0.004, -td - 0.03, h + 0.025), (-tw + 0.004, -td - 0.03, h + 0.025)], "paper_white", thickness=0.0009),
              quad(prefix + "_fb", [(tw, td, h), (-tw, td, h), (-tw + 0.004, td + 0.025, h + 0.03), (tw - 0.004, td + 0.025, h + 0.03)], "paper_white", thickness=0.0009),
              quad(prefix + "_fc", [(-tw, td, h), (-tw, -td, h), (-tw - 0.03, 0, h + 0.02)], "paper_white", thickness=0.0009),
              quad(prefix + "_fd", [(tw, -td, h), (tw, td, h), (tw + 0.025, 0, h + 0.025)], "paper_white", thickness=0.0009)]
        parts += fl
        rice = ellipsoid(prefix + "_rice", 0.04, 0.034, 0.014, "food_rice", center=(0, 0, h - 0.03), subdiv=2, seed=seed, bump=0.004)
        parts.append(rice)
    else:
        ridge = h + 0.03
        fl = [quad(prefix + "_fa", [(-tw, -td, h), (tw, -td, h), (tw - 0.012, 0, ridge), (-tw + 0.012, 0, ridge)], "paper_white", thickness=0.0009),
              quad(prefix + "_fb", [(tw, td, h), (-tw, td, h), (-tw + 0.012, 0.0, ridge - 0.001), (tw - 0.012, 0.0, ridge - 0.001)], "paper_white", thickness=0.0009),
              quad(prefix + "_fc", [(-tw, td, h), (-tw, -td, h), (-tw + 0.014, 0, ridge - 0.008)], "paper_white", thickness=0.0009),
              quad(prefix + "_fd", [(tw, -td, h), (tw, td, h), (tw - 0.014, 0, ridge - 0.008)], "paper_white", thickness=0.0009)]
        parts += fl
    # wire handle
    pts = catmull([V(-tw + 0.006, 0, h - 0.01), V(-tw + 0.004, 0, h + 0.02), V(-tw * 0.6, 0, h + 0.05), V(0, 0, h + 0.062), V(tw * 0.6, 0, h + 0.05), V(tw - 0.004, 0, h + 0.02), V(tw - 0.006, 0, h - 0.01)], n=6)
    parts.append(sweep(prefix + "_wire", pts, 0.0009, "metal_steel", segments=8))
    return parts


@prop
def build_cartons():
    if not wanted("kitchen_takeaway_cartons"):
        return
    p = "kitchen_takeaway_cartons"
    parts = []
    parts += xform_group(mk_carton(p + "_c1", seed=1), loc=(0, 0, 0), rot=(0, 0, -8))
    parts += xform_group(mk_carton(p + "_c2", seed=2), loc=(0.004, -0.003, 0.126), rot=(4, -3, 24))
    parts += xform_group(mk_carton(p + "_c3", seed=3, open_top=True), loc=(0.116, 0.01, 0), rot=(0, 0, 35))
    settle(parts)
    finish_prop(parts, p, "rubbish", "Chinese takeaway cartons: two stacked closed (wire handles, red logo) ~0.26 m tall, one open with rice remains beside them (+X). Footprint ~0.22 x 0.14 m.",
                views=VIEWS, export=EXPORT)


def mk_foil_tray(prefix, seed=0, with_lid=True, food=True):
    w, d, h = 0.085, 0.065, 0.045
    def ring(sw, sd, z):
        return [(x, y, z) for x, y in superellipse(sw, sd, 3.2, 40)]
    rings = [ring(w - 0.014, d - 0.014, 0.0), ring(w - 0.010, d - 0.010, 0.012), ring(w - 0.004, d - 0.004, 0.03), ring(w, d, h),
             ring(w + 0.007, d + 0.007, h + 0.001), ring(w + 0.0075, d + 0.0075, h - 0.002), ring(w + 0.004, d + 0.004, h - 0.003)]
    tray = loft(prefix + "_tray", rings, "foil", close_bottom=True)
    subdivide(tray, 1)
    solidify(tray, 0.0005)
    crinkle(tray, strength=0.0012, scale=0.025, seed=seed, octaves=3, ridge=0.4)
    parts = [tray]
    if food:
        rice = ellipsoid(prefix + "_rice", 0.045, 0.03, 0.009, "food_rice", center=(-0.01, 0.005, 0.012), subdiv=2, seed=seed, bump=0.004)
        sauce = rev(prefix + "_sauce", [(0, 0.0048), (0.02, 0.0042), (0.03, 0.0032)], "food_sauce", segments=24, rmod=lambda th, ri, r, z: r * (1 + 0.2 * math.sin(3 * th + 0.3)))
        sauce.location = (0.035, -0.012, 0)
        parts += [rice, sauce]
    if with_lid:
        lid = rbox(prefix + "_lid", (2 * w + 0.012, 2 * d + 0.012, 0.0012), "paper_white", center=(0.035, 0.03, h + 0.0026), bevel=0.0004)
        lid.rotation_euler = (math.radians(3), math.radians(-2), math.radians(14))
        parts.append(lid)
    return parts


@prop
def build_foil_tray():
    if wanted("kitchen_takeaway_tray_foil"):
        finish_prop(mk_foil_tray("kitchen_takeaway_tray_foil", seed=3), "kitchen_takeaway_tray_foil", "rubbish",
                    "Crinkled foil takeaway tray 18 x 14 x 4.5 cm with rice/sauce remains and its card lid skewed on top.", views=VIEWS, export=EXPORT)


def mk_kebab_wrapper(prefix, seed=0):
    rnd = random.Random(seed)
    w = 0.30
    sh = sheet(prefix + "_paper", w, w * 0.92, 40, 40, "paper_white")
    me = sh.data
    ph = rnd.random() * 6
    for v in me.vertices:
        x, y = v.co.x, v.co.y
        dd = math.hypot(x / (w / 2), y / (w * 0.46))
        # asymmetric dish: one side (+x+y) lifts much more, the opposite corner stays flat-ish
        side = 0.5 + 0.5 * math.tanh((x * 0.8 + y) / 0.08)
        z = 0.085 * max(0.0, dd - 0.25) ** 1.8 * (0.45 + 0.9 * side)
        z += 0.012 * max(0.0, math.sin(5.5 * (x * math.cos(ph) + y * math.sin(ph)) + 1.0)) * smoothstep(0.3, 0.8, dd)
        z += 0.008 * max(0.0, math.sin(8 * (x * math.cos(ph + 1.9) + y * math.sin(ph + 1.9)))) * smoothstep(0.4, 0.9, dd)
        v.co.z = z
        # gather the sheet inward so the rim turns over (more on the lifted side)
        g = 1 - (0.12 + 0.16 * side) * smoothstep(0.5, 1.0, dd)
        v.co.x *= g
        v.co.y *= g
    me.update()
    crinkle(sh, strength=0.004, scale=0.04, seed=seed, octaves=3, ridge=0.5)
    solidify(sh, 0.0004)
    off = Vector((rnd.random() * 10, rnd.random() * 10, 0))
    blobs = [(0.02, -0.01, 0.055), (-0.06, 0.04, 0.03), (0.07, 0.05, 0.022), (-0.03, -0.07, 0.018)]
    paint(sh, "food_grease", lambda c, n: any(math.hypot(c.x - bx, c.y - by) < br * (1 + 0.35 * noise.noise((c + off) / 0.03)) for bx, by, br in blobs))
    parts = [sh]
    for i in range(5):
        a, rr = rnd.uniform(0, 6.28), rnd.uniform(0.0, 0.06)
        parts.append(ellipsoid(prefix + f"_let{i}", 0.016, 0.009, 0.002, "food_lettuce", center=(rr * math.cos(a), rr * math.sin(a), 0.006), subdiv=1, rot=(rnd.uniform(-0.4, 0.4), 0, rnd.uniform(0, 6))))
    for i in range(3):
        a, rr = rnd.uniform(0, 6.28), rnd.uniform(0.0, 0.05)
        parts.append(ellipsoid(prefix + f"_meat{i}", 0.014, 0.008, 0.004, "food_crust", center=(rr * math.cos(a), rr * math.sin(a), 0.008), subdiv=1, rot=(0, 0, rnd.uniform(0, 6))))
    parts.append(rbox(prefix + "_pitta", (0.06, 0.035, 0.01), "food_toast", center=(0.04, -0.03, 0.01), bevel=0.004, segments=2))
    return parts


@prop
def build_kebab():
    if wanted("kitchen_kebab_wrapper"):
        finish_prop(mk_kebab_wrapper("kitchen_kebab_wrapper", 4), "kitchen_kebab_wrapper", "rubbish",
                    "Greasy kebab wrapper paper opened out (~0.26 m across) with lettuce shreds, meat bits and a pitta end. Lies flat, 7-9 cm tall at the curled edges.", views=VIEWS, export=EXPORT)


def mk_crisp_packet(prefix, role, w=0.20, h=0.135, puff=0.028, seed=0, scrunch=False):
    bag = pillow_bag(prefix + "_bag", w, h, puff, 34, 22, role, seam=0.012, seed=seed, crinkle_amp=0.0035 if not scrunch else 0.006)
    paint(bag, "label_paper", lambda c, n: abs(c.x) < 0.052 and abs(c.y) < 0.03 and c.z > 0.004 and not (abs(c.x) < 0.042 and abs(c.y) < 0.021))
    paint(bag, "foil", lambda c, n: abs(c.x) > w / 2 - 0.011)
    if scrunch:
        twist_x(bag, 330.0, squeeze=0.35)
        me = bag.data
        for v in me.vertices:
            v.co.x *= 0.72
        me.update()
    return [bag]


@prop
def build_crisps():
    if wanted("kitchen_crisp_packet_a"):
        parts = mk_crisp_packet("kitchen_crisp_packet_a", "foil_crisps_red", seed=11)
        xform_group(parts, rot=(0, 0, -18))
        settle(parts)
        finish_prop(parts, "kitchen_crisp_packet_a", "rubbish", "Crisp packet (red foil, label panel, silver seams) lying flat, half-puffed, 20 x 13 cm.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_crisp_packet_b"):
        parts = mk_crisp_packet("kitchen_crisp_packet_b", "foil_crisps_blue", w=0.18, h=0.12, puff=0.022, seed=12, scrunch=True)
        xform_group(parts, rot=(0, 0, 40))
        settle(parts)
        finish_prop(parts, "kitchen_crisp_packet_b", "rubbish", "Crisp packet (blue foil) twisted/scrunched into a ~13 cm wad.", variant_of="kitchen_crisp_packet_a", views=VIEWS, export=EXPORT)


def mk_choc_wrapper(prefix, seed=0):
    rnd = random.Random(seed)
    sh = sheet(prefix + "_foil", 0.15, 0.085, 30, 18, "foil_purple")
    me = sh.data
    for v in me.vertices:
        x, y = v.co.x, v.co.y
        # loosely scrunched: gathered toward the centre line + curled ends
        g = 1 - 0.5 * smoothstep(0.02, 0.075, abs(x)) ** 1.5
        v.co.y = y * g
        v.co.z = 0.010 * (1 - math.cos(math.pi * min(1, abs(x) / 0.075))) + 0.0015 * math.sin(6 * y / 0.085 * math.pi + x * 40) + 0.004 * (1 - abs(y) / 0.0425)
    me.update()
    crinkle(sh, strength=0.0045, scale=0.018, seed=seed, octaves=3, ridge=0.7)
    solidify(sh, 0.0003)
    paint(sh, "label_paper", lambda c, n: n.z < -0.3)   # white inside shows where it curls over
    paint(sh, "foil_gold", lambda c, n: abs(c.x) < 0.035 and abs(c.y) < 0.012 and n.z > 0.2)
    return [sh]


@prop
def build_choc():
    if wanted("kitchen_chocolate_wrapper"):
        parts = mk_choc_wrapper("kitchen_chocolate_wrapper", 5)
        settle(parts)
        finish_prop(parts, "kitchen_chocolate_wrapper", "rubbish", "Purple/gold chocolate bar wrapper, scrunched and curled, ~15 x 7 cm.", views=VIEWS, export=EXPORT)


@prop
def build_paper_balls():
    if not wanted("kitchen_paper_balls"):
        return
    p = "kitchen_paper_balls"
    parts = [crumpled_ball(p + "_a", 0.038, "paper_white", seed=21, amp=0.34),
             crumpled_ball(p + "_b", 0.031, "paper_white", seed=22, amp=0.38),
             crumpled_ball(p + "_c", 0.042, "paper_yellow", seed=23, amp=0.30)]
    parts[0].location.x = -0.07
    parts[1].location = (0.02, 0.05, parts[1].location.z)
    parts[2].location = (0.07, -0.03, parts[2].location.z)
    finish_prop(parts, p, "rubbish", "Three crumpled paper balls (two white, one yellow lined), 6-8 cm each, spread over ~0.2 m. Can be used individually by scaling/rotating the prop.", views=VIEWS, export=EXPORT)


@prop
def build_tissues():
    if not wanted("kitchen_tissues_used"):
        return
    p = "kitchen_tissues_used"
    a = crumpled_ball(p + "_a", 0.03, "paper_tissue", seed=31, amp=0.5, squash=0.6)
    b = crumpled_ball(p + "_b", 0.026, "paper_tissue", seed=32, amp=0.55, squash=0.55)
    b.location = (0.055, 0.02, b.location.z)
    sh = sheet(p + "_sheet", 0.14, 0.12, 20, 18, "paper_tissue")
    me = sh.data
    for v in me.vertices:
        v.co.z = 0.004 * (1 + math.sin(v.co.x * 60)) * smoothstep(0.02, 0.07, abs(v.co.x)) + 0.002
    me.update()
    crinkle(sh, strength=0.004, scale=0.03, seed=33, ridge=0.5)
    solidify(sh, 0.0003)
    sh.location = (-0.02, -0.02, 0)
    sh.rotation_euler.z = math.radians(25)
    parts = [a, b, sh]
    finish_prop(parts, p, "rubbish", "Used tissues: two balled up and one loosely crumpled flat, ~0.17 m spread, 4-5 cm tall.", views=VIEWS, export=EXPORT)


def mk_paper_cup(prefix, with_lid=True, sleeve=True, stain=True):
    rb, rt, h, wall = 0.028, 0.040, 0.112, 0.0008
    prof = [(0, 0.004), (rb - 0.002, 0.004), (rb, 0.0), (rb + 0.0003, 0.006), (rt - 0.0008, h - 0.004), (rt, h - 0.0015), (rt + 0.0005, h + 0.0004), (rt - 0.0005, h + 0.0012),
            (rt - 0.0015, h), (rt - wall - 0.0012, h - 0.003), (rb - wall, 0.007), (rb - wall - 0.002, 0.006), (0, 0.006)]
    cup = rev(prefix + "_cup", prof, "paper_cup", segments=40)
    parts = [cup]
    if stain:
        paint(cup, "stain_coffee", lambda c, n: (n.x * c.x + n.y * c.y) > 0 and c.z > h - 0.03 and ang_near(theta(c), 0.6, 0.12) and math.hypot(c.x, c.y) > rt - 0.004)
        parts.append(disc(prefix + "_dregs", rb - wall + (rt - rb) * 0.15, 0.021, "liquid_coffee", segments=40))
    if sleeve:
        z0, z1 = 0.032, 0.078
        r0 = rb + (rt - rb) * (z0 / h) + 0.0012
        r1 = rb + (rt - rb) * (z1 / h) + 0.0012
        sl = rev(prefix + "_sleeve", [(r0, z0), (r1, z1), (r1 - 0.0012, z1), (r0 - 0.0012, z0)], "cardboard", segments=40)
        sl.data.polygons.foreach_set("use_smooth", [True] * len(sl.data.polygons))
        parts.append(sl)
    if with_lid:
        R = rt + 0.0022
        lid = rev(prefix + "_lid", [(0.0, 0.006), (0.012, 0.006), (0.0225, 0.0085), (0.030, 0.0085), (0.032, 0.004), (0.036, 0.0015), (R - 0.0015, 0.0015), (R, 0.0), (R, -0.0055), (R - 0.0012, -0.0055), (R - 0.0012, -0.001), (0.034, -0.001)],
                  "plastic_black", segments=40)
        lid.location.z = h + 0.0005
        paint(lid, "screen_off", lambda c, n: 0.0235 < math.hypot(c.x, c.y) < 0.03 and ang_near(theta(c), math.pi * 1.5, 0.35) and n.z > 0.5)
        parts.append(lid)
    return parts


@prop
def build_paper_cup():
    if wanted("kitchen_cup_paper_takeaway"):
        finish_prop(mk_paper_cup("kitchen_cup_paper_takeaway"), "kitchen_cup_paper_takeaway", "rubbish",
                    "Takeaway coffee cup 12 cm with black sip lid and cardboard sleeve, coffee drip stain down one side.", views=VIEWS, export=EXPORT)


@prop
def build_cup_stack():
    if not wanted("kitchen_cup_stack"):
        return
    p = "kitchen_cup_stack"
    rb, rt, h = 0.024, 0.036, 0.09
    parts = []
    for i in range(4):
        prof = [(0, 0.0015), (rb - 0.0015, 0.0015), (rb, 0), (rt - 0.0006, h - 0.0025), (rt + 0.0008, h - 0.0008), (rt + 0.0008, h + 0.0006), (rt - 0.0008, h + 0.0006), (rt - 0.0014, h - 0.0012),
                (rb - 0.0007, 0.0028), (rb - 0.0022, 0.0022), (0, 0.0022)]
        c = rev(p + f"_c{i}", prof, "plastic_white" if i % 2 == 0 else "plastic_clear", segments=36)
        c.location.z = i * 0.022
        c.rotation_euler = (math.radians(i * 1.5), math.radians(-i * 1.0), 0)
        parts.append(c)
    xform_group(parts, rot=(0, 86, 20))
    settle(parts)
    finish_prop(parts, p, "rubbish", "Four nested plastic party cups toppled over, lying along ~+X, 7 cm high, 13 cm long.", views=VIEWS, export=EXPORT)


# ================================================================================================ RUBBISH - piles, bins, bags

@prop
def build_piles():
    if wanted("kitchen_rubbish_pile_a"):
        p = "kitchen_rubbish_pile_a"
        parts = []
        parts += xform_group(mk_pizza_box(p + "_pb", open_deg=None, slice_=False, seed=41, ajar=3), rot=(0, 0, 14))
        can = mk_can(p + "_canb", "can_silver", seed=42)
        for o in can:
            apply_xform(o)
        cm = merge(can, p + "_canb_m")
        crush_can(cm, k=0.42, lean=0.1, seed=42, amp=0.11)
        parts += xform_group([cm], loc=(-0.06, 0.03, 0.055), rot=(0, 0, 60))
        parts += xform_group(mk_can(p + "_canc", "can_blue", dents=[(1.0, 0.06, 0.03, 0.008)], seed=43), loc=(0.08, -0.02, 0.055 + 0.033), rot=(0, 92, -40))
        parts += xform_group(mk_can(p + "_cand", "can_red", dents=[(2.0, 0.05, 0.025, 0.006)], seed=44), loc=(0.19, 0.13, 0), rot=(3, 0, 10))
        parts += xform_group(mk_crisp_packet(p + "_cr", "foil_crisps_red", seed=45), loc=(-0.03, -0.08, 0.055 + 0.03), rot=(0, 0, -30))
        parts += xform_group(mk_bottle_beer(p + "_bb", "glass_brown", "label_red", label2="label_black", lying=True), loc=(0.05, 0.1, 0.055), rot=(0, 0, -20))
        b1 = crumpled_ball(p + "_pa", 0.035, "paper_white", seed=46)
        b1.location = (-0.19, -0.1, b1.location.z)
        b2 = crumpled_ball(p + "_pbw", 0.03, "paper_yellow", seed=47)
        b2.location = (0.12, -0.06, b2.location.z + 0.055)
        parts += [b1, b2]
        parts += xform_group(mk_choc_wrapper(p + "_cw", seed=48), loc=(-0.2, 0.05, 0.0), rot=(0, 0, 50))
        settle(parts)
        finish_prop(parts, p, "rubbish", "Rubbish heap ~0.5 m: closed pizza box as base with crushed/tipped cans, crisp packet, beer bottle and paper balls on and around it. ~0.14 m tall.",
                    views=VIEWS, export=EXPORT)
    if wanted("kitchen_rubbish_pile_b"):
        p = "kitchen_rubbish_pile_b"
        parts = []
        parts += xform_group(mk_kebab_wrapper(p + "_kw", seed=51), loc=(0.0, 0.0, 0), rot=(0, 0, 30))
        parts += xform_group(mk_foil_tray(p + "_ft", seed=52, with_lid=False), loc=(0.17, 0.06, 0.0), rot=(0, 0, -25))
        parts += xform_group(mk_carton(p + "_ct", seed=53, open_top=True), loc=(-0.14, 0.1, 0), rot=(0, 0, 15))
        parts += xform_group(mk_carton(p + "_ct2", seed=54), loc=(-0.12, -0.08, 0), rot=(0, 90, 40))
        parts += xform_group(mk_can(p + "_can", "can_black", dents=[(0.5, 0.05, 0.03, 0.007)], seed=55), loc=(0.13, -0.11, 0), rot=(0, 88, 70))
        parts += xform_group(mk_bottle_water(p + "_wb", seed=56), loc=(0.02, 0.16, 0), rot=(0, 0, 50))
        t1 = crumpled_ball(p + "_t1", 0.028, "paper_tissue", seed=57, amp=0.5, squash=0.6)
        t1.location = (0.03, -0.03, t1.location.z + 0.012)
        t2 = crumpled_ball(p + "_t2", 0.024, "paper_tissue", seed=58, amp=0.5, squash=0.6)
        t2.location = (0.22, -0.04, t2.location.z)
        parts += [t1, t2]
        parts += xform_group(mk_crisp_packet(p + "_cr", "foil_crisps_blue", w=0.18, h=0.12, puff=0.022, seed=59, scrunch=True), loc=(-0.02, -0.14, 0.0), rot=(0, 0, 10))
        settle(parts)
        finish_prop(parts, p, "rubbish", "Rubbish heap ~0.5 m: kebab wrapper, foil tray, takeaway cartons (one tipped), can, crumpled water bottle, tissues, scrunched crisp packet. ~0.14 m tall.",
                    variant_of="kitchen_rubbish_pile_a", views=VIEWS, export=EXPORT)


def bin_body_profile(rb=0.125, rt=0.135, h=0.40):
    return [(0, 0.004), (rb * 0.82, 0.004), (rb * 0.93, 0.0), (rb, 0.006), (rb + (rt - rb) * 0.5, h * 0.5), (rt, h - 0.012), (rt + 0.003, h - 0.008), (rt + 0.0045, h - 0.003),
            (rt + 0.004, h), (rt - 0.003, h), (rt - 0.0045, h - 0.004), (rt - 0.0045, h - 0.012), (rb - 0.0045 + (rt - rb) * 0.5, h * 0.5), (rb - 0.0045, 0.02), (rb - 0.009, 0.015), (0, 0.015)]


def mk_bin(prefix, body_role="metal_steel", trim_role="plastic_black", open_deg=0.0, full=False, seed=0):
    rb, rt, h = 0.125, 0.135, 0.40
    rnd = random.Random(seed)
    body = rev(prefix + "_body", bin_body_profile(rb, rt, h), body_role, segments=56)
    if body_role == "metal_steel":
        dent(body, (rt * 0.7 * math.cos(2.4), rt * 0.7 * math.sin(2.4), 0.12), 0.05, 0.004)
    bodyparts = [body]
    # inner liner rim (plastic bucket lip) peeking over the top
    bodyparts.append(rev(prefix + "_liner", [(rt - 0.0045, h - 0.03), (rt - 0.0055, h + 0.004), (rt - 0.0065, h + 0.006), (rt - 0.012, h + 0.006), (rt - 0.012, h - 0.03)], trim_role, segments=56))
    # pedal housing at the front base (-Y) + pedal
    bodyparts.append(rbox(prefix + "_ph", (0.10, 0.035, 0.026), trim_role, center=(0, -(rb - 0.012), 0.013), bevel=0.003))
    pedal = [rbox(prefix + "_pedal", (0.085, 0.055, 0.010), trim_role, center=(0, -(rb + 0.02), 0.014), bevel=0.0025)]
    paint(pedal[0], "rubber_black", lambda c, n: n.z > 0.5 and abs(c.x) < 0.03)
    # back lever rod + brackets
    rod = sweep(prefix + "_rod", [V(0, rt - 0.001, 0.02), V(0, rt - 0.001, 0.5 * h), V(0, rt - 0.001, h + 0.004)], 0.0035, "metal_steel", segments=10)
    bodyparts.append(rod)
    bodyparts.append(rbox(prefix + "_brk", (0.03, 0.012, 0.03), trim_role, center=(0, rt + 0.003, h - 0.01), bevel=0.002))
    # hinge knuckle on the body (axis along X at the back)
    hz, hy = h + 0.012, rt + 0.004
    bodyparts.append(cylinder(prefix + "_knuckle", 0.006, 0.05, trim_role, segments=14, center=(0, hy, hz), bevel=0.0008, origin="center"))
    bodyparts[-1].rotation_euler.y = math.radians(90)
    # lid
    R = rt + 0.006
    lid = [rev(prefix + "_lid", [(0, 0.020), (0.06, 0.018), (0.11, 0.012), (R - 0.004, 0.005), (R, 0.0015), (R, -0.012), (R - 0.0015, -0.012), (R - 0.0015, 0.0), (R - 0.004, 0.003), (0.11, 0.010), (0.06, 0.016), (0, 0.018)],
               trim_role, segments=56)]
    lid[0].location.z = h + 0.006
    lid.append(rbox(prefix + "_lidarm", (0.03, 0.03, 0.008), trim_role, center=(0, R - 0.006, h + 0.012 - 0.0), bevel=0.0015))
    lid.append(cylinder(prefix + "_lidknuckle", 0.0055, 0.03, trim_role, segments=14, center=(0.0, hy, hz), bevel=0.0008, origin="center"))
    lid[-1].rotation_euler.y = math.radians(90)
    # handle bump on the lid front
    lid.append(rbox(prefix + "_lidgrip", (0.05, 0.012, 0.006), trim_role, center=(0, -(R - 0.02), h + 0.006 + 0.012), bevel=0.0025))
    if open_deg:
        for o in lid:
            rot_about(o, (0, hy, hz), (-1, 0, 0), open_deg)
    contents = []
    if full:
        zt = h - 0.08
        b1 = crumpled_ball(prefix + "_rb1", 0.045, "paper_white", seed=seed + 1)
        b1.location = (-0.04, 0.02, zt + b1.location.z)
        b2 = crumpled_ball(prefix + "_rb2", 0.04, "paper_yellow", seed=seed + 2)
        b2.location = (0.06, -0.05, zt + 0.02 + b2.location.z)
        contents += [b1, b2]
        can = mk_can(prefix + "_rcan", "can_red", dents=[(1.5, 0.05, 0.03, 0.007)], seed=seed)
        xform_group(can, loc=(0.02, 0.07, zt + 0.07), rot=(0, 75, 30))
        contents += can
        can2 = mk_can(prefix + "_rcan2", "can_blue", seed=seed + 5)
        for o in can2:
            apply_xform(o)
        cm = merge(can2, prefix + "_rcan2_m")
        crush_can(cm, k=0.45, seed=seed + 5, amp=0.11)
        cm.location = (-0.07, -0.06, zt + 0.045)
        cm.rotation_euler.z = 1.0
        contents.append(cm)
        contents += xform_group(mk_crisp_packet(prefix + "_rcr", "foil_crisps_blue", w=0.17, h=0.12, puff=0.02, seed=seed + 3, scrunch=True), loc=(0.0, -0.03, zt + 0.1), rot=(20, 0, 50))
        contents += xform_group(mk_pizza_slice(prefix + "_rsl", seed=seed + 4), loc=(-0.01, 0.02, zt + 0.055), rot=(0, -55, 120))
        contents += xform_group(mk_choc_wrapper(prefix + "_rcw", seed=seed + 6), loc=(0.05, 0.03, zt + 0.12), rot=(0, 0, 80))
        contents += xform_group(mk_paper_cup(prefix + "_rpc", with_lid=True, sleeve=True, stain=False), loc=(-0.02, -0.03, zt + 0.045), rot=(0, 100, -30))
        # overflow on the floor in front
        c3 = crumpled_ball(prefix + "_rb3", 0.035, "paper_white", seed=seed + 7)
        c3.location = (0.1, -0.2, c3.location.z)
        contents.append(c3)
    return [("body", bodyparts, None), ("lid", lid, (0, hy, hz)), ("pedal", pedal, (0, -(rb - 0.012), 0.014))] + ([("rubbish", contents, None)] if contents else [])


@prop
def build_bins():
    if wanted("kitchen_bin_small_a"):
        finish_hier(mk_bin("kitchen_bin_small_a", "metal_steel", "plastic_black", seed=61), "kitchen_bin_small_a", "rubbish",
                    "Brushed-steel pedal bin 0.27 m dia x 0.43 m tall, black lid (child `lid`, pivot at the back hinge, opens about +X axis negative), pedal at the front (-Y, child `pedal`), lever rod at the back. Closed.",
                    views=VIEWS, export=EXPORT)
    if wanted("kitchen_bin_small_b"):
        finish_hier(mk_bin("kitchen_bin_small_b", "plastic_cream", "plastic_grey", seed=62), "kitchen_bin_small_b", "rubbish",
                    "Cream plastic pedal bin 0.27 x 0.43 m with grey lid/pedal. Same rig as kitchen_bin_small_a (children `lid`, `pedal`). Closed.",
                    variant_of="kitchen_bin_small_a", views=VIEWS, export=EXPORT)
    if wanted("kitchen_bin_open_full"):
        finish_hier(mk_bin("kitchen_bin_open_full", "metal_steel", "plastic_black", open_deg=80, full=True, seed=63), "kitchen_bin_open_full", "rubbish",
                    "Steel pedal bin with lid open (80 deg) and rubbish overflowing (cans, paper, pizza slice, cup, wrappers) + a paper ball on the floor in front (-Y). Children `lid`, `pedal`, `rubbish`. Pair: kitchen_bin_small_a (tidy).",
                    variant_of="kitchen_bin_small_a", views=VIEWS, export=EXPORT)


def mk_bin_bag(prefix, seed=0):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            c = lp.vert.co
            lp[uvl].uv = ((math.atan2(c.y, c.x) / (2 * math.pi)) % 1.0, c.z * 0.5 + 0.5)
    ob = obj_from_bm(bm, prefix + "_bag", ["plastic_bag_black"])
    me = ob.data
    off = Vector((rnd.random() * 40, rnd.random() * 40, rnd.random() * 40))
    H = 0.40
    for v in me.vertices:
        p = v.co.copy()           # unit sphere
        # base ellipsoid 0.19 x 0.17 x 0.19 (half sizes), centre z=0.19
        q = Vector((p.x * 0.19, p.y * 0.17, p.z * 0.19 + 0.19))
        # neck gather above z=0.30 -> knot at ~0.42
        t = smoothstep(0.27, 0.40, q.z)
        rad = 1 - 0.80 * t
        q.x *= rad
        q.y *= rad
        q.z += t * 0.06
        # sag: wider at the bottom, flattened base
        sp = 1 + 0.22 * (1 - smoothstep(0.0, 0.17, q.z))
        q.x *= sp
        q.y *= sp
        if q.z < 0.035:
            q.z = 0.035 - (0.035 - q.z) * 0.22
        # lumps (contents) + creases
        n1 = noise.noise(q / 0.075 + off)
        n2 = noise.noise(q / 0.035 + off * 2)
        rid = abs(noise.noise(q / 0.06 + off * 3))
        amp = (1 - t * 0.6) * (0.4 + 0.6 * smoothstep(0.02, 0.1, q.z))
        disp = (0.022 * n1 + 0.009 * n2 - 0.014 * rid) * amp
        nrm = Vector((p.x, p.y, p.z * 0.6)).normalized()
        q += nrm * disp
        v.co = q
    me.update()
    shade(ob, True, angle=45)
    parts = [ob]
    # knot: twisted lump + two ears
    kz = 0.455
    knot = ellipsoid(prefix + "_knot", 0.034, 0.030, 0.024, "plastic_bag_black", center=(0.0, 0.0, kz), subdiv=2, seed=seed + 1, bump=0.006)
    knot.rotation_euler = (0.3, 0.2, 0.5)
    e1 = ellipsoid(prefix + "_ear1", 0.055, 0.02, 0.012, "plastic_bag_black", center=(0.05, 0.015, kz + 0.01), subdiv=2, seed=seed + 2, bump=0.006, rot=(0.2, -0.35, 0.3))
    e2 = ellipsoid(prefix + "_ear2", 0.045, 0.018, 0.010, "plastic_bag_black", center=(-0.045, -0.02, kz + 0.005), subdiv=2, seed=seed + 3, bump=0.006, rot=(-0.2, 0.4, 0.4))
    parts += [knot, e1, e2]
    return parts


@prop
def build_bin_bags():
    if wanted("kitchen_bin_bag_full"):
        parts = mk_bin_bag("kitchen_bin_bag_full", seed=71)
        settle(parts)
        finish_prop(parts, "kitchen_bin_bag_full", "rubbish", "Knotted black bin bag, bulging with contents, flattened base, ~0.45 wide x 0.47 m tall.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_bin_bag_empty_roll"):
        p = "kitchen_bin_bag_empty_roll"
        r, L = 0.034, 0.145
        roll = rev(p + "_roll", [(0, 0.001), (0.009, 0.001), (0.0105, 0.0), (r - 0.003, 0.0), (r, 0.003), (r, L - 0.003), (r - 0.003, L), (0.0105, L), (0.009, L - 0.001), (0, L - 0.001)],
                   "plastic_bag_black", segments=40, rmod=lambda th, ri, rr, z: rr * (1 + 0.01 * math.sin(7 * th + z * 30)) if 4 <= ri <= 5 else rr)
        # core hole: dark
        band = rev(p + "_band", [(r + 0.0006, L * 0.35), (r + 0.0006, L * 0.65), (r + 0.0012, L * 0.65), (r + 0.0012, L * 0.35)], "label_paper", segments=40)
        paint(band, "label_red", lambda c, n: ang_near(theta(c), 0.0, 0.9) or ang_near(theta(c), math.pi, 0.9))
        # unrolled flap trailing out from the roll
        fl = sheet(p + "_flap", 0.22, L * 0.92, 26, 10, "plastic_bag_black")
        me = fl.data
        for v in me.vertices:
            x = v.co.x + 0.11   # 0..0.22 from the roll outwards
            v.co.z = 0.0008 + 0.012 * math.exp(-x / 0.05) + 0.0025 * math.sin(x * 70)
        me.update()
        crinkle(fl, strength=0.0025, scale=0.03, seed=72, ridge=0.5)
        solidify(fl, 0.0002)
        fl.location = (-(0.11 + r * 0.9), 0.0, 0.0)
        fl.location.y = 0.0
        parts = [roll, band]
        xform_group(parts, rot=(0, 90, 0))                      # roll lying along X
        for o in parts:
            o.location.z += r
            o.location.x -= L / 2
        fl.rotation_euler.z = math.radians(90)
        fl.location = (0.0, -(0.11 + r * 0.9), 0.0)
        parts.append(fl)
        settle(parts)
        finish_prop(parts, p, "rubbish", "Roll of black bin bags (14.5 cm wide, 7 cm dia) lying along X with the paper band, one bag half unrolled trailing to -Y (~0.25 m). Tidy counterpart of kitchen_bin_bag_full.",
                    variant_of="kitchen_bin_bag_full", views=VIEWS, export=EXPORT)


# ================================================================================================ CABLES / SMALL TECH

def tangle_path(rnd, n=9, ext=(0.17, 0.12), r=0.0025, z_start=None, z_end=None, centre=(0, 0)):
    """Wandering, loosely looped cable path lying on the floor with occasional hops over itself."""
    pts = []
    a = rnd.uniform(0, 6.28)
    for i in range(n):
        a += rnd.uniform(0.9, 1.9)
        rad = rnd.uniform(0.3, 1.0)
        x = centre[0] + ext[0] * rad * math.cos(a) + rnd.uniform(-0.02, 0.02)
        y = centre[1] + ext[1] * rad * math.sin(a) + rnd.uniform(-0.02, 0.02)
        z = r + (r * 2.3 if rnd.random() < 0.3 else 0.0)
        pts.append(V(x, y, z))
    if z_start is not None:
        pts[0].z = z_start
        pts[1].z = max(pts[1].z, z_start * 0.5)
    if z_end is not None:
        pts[-1].z = z_end
        pts[-2].z = max(pts[-2].z, z_end * 0.5)
    dense = catmull(pts, n=12)
    for p in dense:
        p.z = max(p.z, r * 0.98)
    return dense


def end_dir(path, end=True):
    return (path[-1] - path[-4]).normalized() if end else (path[0] - path[3]).normalized()


def mk_plug_usb_a(prefix, body_role="plastic_black"):
    """USB-A plug; cable enters at local origin, plug extends +Y. Lies flat (thin axis = Z)."""
    parts = [rbox(prefix + "_body", (0.0155, 0.030, 0.0072), body_role, center=(0, 0.021, 0), bevel=0.0018, segments=3)]
    relief = cylinder(prefix + "_relief", 0.0032, 0.012, body_role, segments=12, center=(0, 0.0, 0), bevel=0.0005, r_top=0.0045, origin="center")
    relief.rotation_euler.x = math.radians(-90)
    relief.location = (0, 0.006, 0)
    parts.append(relief)
    shell = rbox(prefix + "_shell", (0.012, 0.0125, 0.0045), "metal_steel", center=(0, 0.0415, 0), bevel=0.0006, segments=2)
    paint(shell, "plastic_black", lambda c, n: n.y > 0.9)
    parts.append(shell)
    return parts


def mk_plug_usb_c(prefix, body_role="plastic_white"):
    parts = [rbox(prefix + "_body", (0.0115, 0.026, 0.0062), body_role, center=(0, 0.018, 0), bevel=0.0016, segments=3)]
    relief = cylinder(prefix + "_relief", 0.0028, 0.011, body_role, segments=12, center=(0, 0, 0), bevel=0.0004, r_top=0.004, origin="center")
    relief.rotation_euler.x = math.radians(-90)
    relief.location = (0, 0.0055, 0)
    parts.append(relief)
    shell = rbox(prefix + "_shell", (0.0083, 0.0068, 0.0026), "metal_steel", center=(0, 0.0344, 0), bevel=0.0011, segments=3)
    paint(shell, "plastic_black", lambda c, n: n.y > 0.9)
    parts.append(shell)
    return parts


def mk_plug_jack(prefix, body_role="plastic_black"):
    body = cylinder(prefix + "_body", 0.0038, 0.02, body_role, segments=16, center=(0, 0, 0), bevel=0.0008, origin="center")
    body.rotation_euler.x = math.radians(-90)
    body.location = (0, 0.01, 0)
    tip = cylinder(prefix + "_tip", 0.00175, 0.0145, "metal_steel", segments=12, center=(0, 0, 0), bevel=0.0004, origin="center")
    tip.rotation_euler.x = math.radians(-90)
    tip.location = (0, 0.02 + 0.00725, 0)
    parts = [body, tip]
    for k, zz in enumerate((-0.0035, 0.0015)):      # insulating rings (two dark bands along the tip)
        ring = cylinder(prefix + f"_ring{k}", 0.0019, 0.0012, "plastic_black", segments=12, center=(0, 0, 0), bevel=0.0, origin="center")
        ring.rotation_euler.x = math.radians(-90)
        ring.location = (0, 0.02 + 0.00725 + zz, 0)
        parts.append(ring)
    relief = cylinder(prefix + "_relief", 0.0022, 0.012, body_role, segments=12, center=(0, 0, 0), bevel=0.0004, r_top=0.0032, origin="center")
    relief.rotation_euler.x = math.radians(-90)
    relief.location = (0, -0.004, 0)
    parts.append(relief)
    return parts


def mk_plug_uk(prefix, body_role="plastic_white", usb_port=False):
    """UK 13 A plug lying on its back: pins point +Z, cable exits at local origin toward -Y (plug body extends +Y)."""
    parts = [rbox(prefix + "_body", (0.048, 0.050, 0.018), body_role, center=(0, 0.027, 0.009), bevel=0.004, segments=4)]
    # fuse cover (slightly proud panel) + pins: earth all brass, live/neutral with black insulating sleeves
    parts.append(rbox(prefix + "_fuse", (0.018, 0.013, 0.0012), "plastic_grey" if body_role != "plastic_grey" else "plastic_black", center=(0.013, 0.014, 0.0183), bevel=0.0004, segments=1))
    pins = [rbox(prefix + "_pe", (0.004, 0.008, 0.0227), "metal_brass", center=(0, 0.038, 0.018 + 0.0227 / 2), bevel=0.0006, segments=2)]
    for sx, tag in ((-1, "l"), (1, "n")):
        pins.append(rbox(prefix + f"_p{tag}s", (0.0064, 0.004, 0.009), "plastic_black", center=(sx * 0.0111, 0.016, 0.018 + 0.0045), bevel=0.0004, segments=1))
        pins.append(rbox(prefix + f"_p{tag}", (0.0064, 0.004, 0.0087), "metal_brass", center=(sx * 0.0111, 0.016, 0.027 + 0.00435), bevel=0.0006, segments=2))
    parts += pins
    if usb_port:
        port = rbox(prefix + "_port", (0.0125, 0.002, 0.0055), "plastic_black", center=(0, 0.0015, 0.009), bevel=0.0004, segments=1)
        parts.append(port)
    else:
        relief = cylinder(prefix + "_relief", 0.0032, 0.012, body_role, segments=12, center=(0, 0, 0), bevel=0.0005, r_top=0.006, origin="center")
        relief.rotation_euler.x = math.radians(-90)
        relief.location = (0, 0.004, 0.009)
        parts.append(relief)
    return parts


def mk_plug_iec(prefix, body_role="plastic_black"):
    """IEC C13 'kettle' connector lying flat; cable at origin, connector extends +Y."""
    body = rbox(prefix + "_body", (0.026, 0.036, 0.017), body_role, center=(0, 0.025, 0), bevel=0.0035, segments=3)
    paint(body, "plastic_grey", lambda c, n: n.y > 0.9 and abs(c.x) < 0.009 and abs(c.z) < 0.005)
    relief = cylinder(prefix + "_relief", 0.0035, 0.014, body_role, segments=12, center=(0, 0, 0), bevel=0.0005, r_top=0.0055, origin="center")
    relief.rotation_euler.x = math.radians(-90)
    relief.location = (0, 0.007, 0)
    return [body, relief]


def place_plug(parts, path, at_end=True, lift=0.0, roll=0.0):
    """Align a plug (built along +Y from the cable entry) to a path end."""
    P = path[-1] if at_end else path[0]
    d = end_dir(path, at_end)
    d = Vector((d.x, d.y, 0)).normalized() if abs(d.z) < 0.95 else d
    bpy.context.view_layer.update()
    q = d.to_track_quat("Y", "Z")
    M = Matrix.Translation(P + Vector((0, 0, lift))) @ q.to_matrix().to_4x4() @ Matrix.Rotation(roll, 4, "Y")
    for o in parts:
        o.matrix_world = M @ o.matrix_world
    return parts


def mk_cable(prefix, path, r, role):
    return sweep(prefix, path, r, role, segments=10, uv_scale=0.1)


@prop
def build_cables_tangled():
    specs = {"kitchen_cables_tangled_a": (101, [("white", "cable_white", 0.0018, "usb_a", "usb_c", (0.16, 0.11)),
                                                ("mains", "cable_black", 0.0032, "uk", "iec", (0.19, 0.13)),
                                                ("aux", "cable_black", 0.0016, "jack", "jack", (0.13, 0.10)),
                                                ("red", "cable_red", 0.0018, "usb_a", "usb_c", (0.15, 0.12))]),
             "kitchen_cables_tangled_b": (202, [("white", "cable_white", 0.0018, "usb_c", "usb_c", (0.17, 0.12)),
                                                ("black", "cable_black", 0.002, "usb_a", "usb_c", (0.16, 0.12)),
                                                ("charger", "cable_white", 0.0032, "uk_usb", "iec", (0.18, 0.13)),
                                                ("aux", "cable_black", 0.0016, "jack", "jack", (0.12, 0.09))])}
    for name, (seed, cables) in specs.items():
        if not wanted(name):
            continue
        rnd = random.Random(seed)
        parts = []
        for ci, (tag, role, r, e0, e1, ext) in enumerate(cables):
            z0 = 0.009 if e0 in ("uk", "uk_usb") else None
            z1 = 0.009 if e1 in ("uk", "uk_usb") else None
            path = tangle_path(rnd, n=rnd.randint(8, 11), ext=ext, r=r, z_start=z0, z_end=z1, centre=(rnd.uniform(-0.03, 0.03), rnd.uniform(-0.02, 0.02)))
            parts.append(mk_cable(f"{name}_{tag}", path, r, role))
            for at_end, kind in ((False, e0), (True, e1)):
                pr = f"{name}_{tag}_{'e' if at_end else 's'}"
                prole = "plastic_white" if role == "cable_white" else ("plastic_red" if role == "cable_red" else "plastic_black")
                if kind == "usb_a":
                    pl = mk_plug_usb_a(pr, prole)
                    lift = 0.0036 - r
                elif kind == "usb_c":
                    pl = mk_plug_usb_c(pr, prole)
                    lift = 0.0031 - r
                elif kind == "jack":
                    pl = mk_plug_jack(pr, prole)
                    lift = 0.0038 - r
                elif kind == "iec":
                    pl = mk_plug_iec(pr, prole)
                    lift = 0.0085 - r
                elif kind == "uk_usb":
                    pl = mk_plug_uk(pr, "plastic_white", usb_port=True)
                    lift = -0.009
                else:
                    pl = mk_plug_uk(pr, "plastic_white" if ci % 2 else "plastic_black")
                    lift = -0.009
                # the plug "entry" for a start-end plug points backwards along the path
                if not at_end:
                    place_plug(pl, path, at_end=False, lift=lift)
                else:
                    place_plug(pl, path, at_end=True, lift=lift)
                parts += pl
        settle(parts)
        finish_prop(parts, name, "tech", f"Tangle of {len(cables)} cables (~0.4 m) lying on the floor: " + ", ".join(f"{t} ({a}->{b})" for t, _, _, a, b, _ in cables) +
                    ". Tidy counterpart: kitchen_cables_coiled.", variant_of=None if name.endswith("_a") else "kitchen_cables_tangled_a", views=VIEWS, export=EXPORT)


@prop
def build_cables_coiled():
    if not wanted("kitchen_cables_coiled"):
        return
    p = "kitchen_cables_coiled"
    rnd = random.Random(303)
    r = 0.002
    R = 0.052
    loops = 6
    pts = []
    N = 44 * loops
    for i in range(N + 1):
        t = i / N
        a = t * loops * 2 * math.pi
        rr = R + 0.004 * math.sin(a * 0.37 + 1.0) + 0.0025 * math.sin(a * 1.3) + 0.003 * (t - 0.5)
        z = r + 2 * r * (0.5 + 0.5 * math.sin(a * 0.5 + t * 3.0)) * 0.9 + 0.5 * r * math.sin(a * 2.1)
        pts.append(V(rr * math.cos(a), rr * math.sin(a), z))
    # tails: both ends leave the coil tangentially a little
    tail0 = [pts[0] + V(0, -0.02, 0), pts[0] + V(0.01, -0.045, 0)]
    pts = list(reversed(tail0)) + pts
    pts += [pts[-1] + V(-0.015, 0.01, 0), pts[-1] + V(-0.035, 0.03, 0)]
    for q in pts:
        q.z = max(q.z, r)
    cable = sweep(p + "_cable", pts, r, "cable_white", segments=10, uv_scale=0.1)
    parts = [cable]
    parts += place_plug(mk_plug_usb_a(p + "_a", "plastic_white"), pts, at_end=False, lift=0.0036 - r)
    parts += place_plug(mk_plug_usb_c(p + "_c", "plastic_white"), pts, at_end=True, lift=0.0031 - r)
    # velcro strap around the bundle at angle th0 (bundle section ~ 16 mm radial x 12 mm tall)
    th0 = math.radians(205)
    cx, cy = R * math.cos(th0), R * math.sin(th0)
    rad = V(math.cos(th0), math.sin(th0), 0)
    loop = []
    for i in range(28):
        a = 2 * math.pi * i / 28
        loop.append(V(cx, cy, 0.006) + rad * (0.0095 * math.cos(a)) + V(0, 0, 0.0065 * math.sin(a)))
    strap = sweep(p + "_strap", loop, 0.006, "velcro_black", segments=8, closed=True, rx=0.2, ry=1.0)
    tail = sweep(p + "_straptail", catmull([V(cx, cy, 0.006) + rad * 0.0095 + V(0, 0, 0.004), V(cx, cy, 0.006) + rad * 0.018 + V(0, 0, 0.002), V(cx, cy, 0.006) + rad * 0.028 + V(0, 0, -0.004)], n=6),
                 0.006, "velcro_black", segments=8, rx=0.2, ry=1.0)
    parts += [strap, tail]
    settle(parts)
    finish_prop(parts, p, "tech", "Neatly coiled white USB-A to USB-C cable (6 loops, ~12 cm dia) held with a black velcro strap. 1.3 cm tall. Tidy counterpart of kitchen_cables_tangled_*.",
                views=VIEWS, export=EXPORT)


def mk_phone(prefix, screen_role="screen_off"):
    body = rbox(prefix + "_body", (0.0715, 0.1465, 0.0078), "plastic_black", center=(0, 0, 0.0039), bevel=0.0034, segments=5)
    paint(body, "metal_dark", lambda c, n: abs(n.z) < 0.5)                 # metal frame
    screen = rbox(prefix + "_screen", (0.066, 0.141, 0.0006), screen_role, center=(0, 0, 0.0078), bevel=0.0003, segments=1)
    paint(screen, "plastic_black", lambda c, n: n.z > 0.5 and abs(c.x) < 0.006 and c.y > 0.064)   # notch
    port = rbox(prefix + "_port", (0.009, 0.0016, 0.0032), "plastic_grey", center=(0, -0.0735, 0.0039), bevel=0.0005, segments=1)
    return [body, screen, port]


@prop
def build_phone_charger():
    if not wanted("kitchen_phone_charger_plugged"):
        return
    p = "kitchen_phone_charger_plugged"
    rnd = random.Random(404)
    parts = []
    phone = mk_phone(p + "_phone")
    xform_group(phone, loc=(-0.03, -0.09, 0), rot=(0, 0, 16))
    parts += phone
    # charger block in a wall socket at the back (+Y): pins point +Y into the wall, USB port at the bottom.
    # mk_plug_uk builds pins +Z, body +Y from the port; Euler (90,0,180) maps local +Y -> +Z (body up) and +Z -> +Y (pins into wall)
    E = V(0.02, 0.12, 0.30)                                                     # port position (bottom face of the block), wall at y = 0.138
    block = mk_plug_uk(p + "_charger", "plastic_white", usb_port=True)
    xform_group(block, rot=(90, 0, 180))
    xform_group(block, loc=E)
    parts += block
    # USB-A plug pushed up into the port: built along +Y from its cable entry, rotate +Y -> +Z
    pa = mk_plug_usb_a(p + "_usba", "plastic_white")
    xform_group(pa, rot=(90, 0, 0))
    entry = E + V(0, 0, -0.036)
    xform_group(pa, loc=entry)
    parts += pa
    # cable: hangs down the wall, loops on the floor and curls back into the phone's bottom port
    r = 0.0017
    phone_port = Matrix.Translation(V(-0.03, -0.09, 0)) @ Matrix.Rotation(math.radians(16), 4, "Z") @ V(0, -0.0735, 0.0039)
    dir_in = Matrix.Rotation(math.radians(16), 3, "Z") @ V(0, 1, 0)             # phone's local +Y in world
    ctrl = [entry, entry + V(0, 0, -0.05), V(0.03, 0.118, 0.12), V(0.05, 0.112, 0.03), V(0.07, 0.09, r), V(0.09, 0.0, r), V(0.07, -0.12, r),
            V(0.045, -0.21, r), V(0.02, -0.245, r), phone_port - dir_in * 0.05, phone_port - dir_in * 0.034]
    path = catmull(ctrl, n=10)
    for q in path:
        q.z = max(q.z, r)
    parts.append(sweep(p + "_cable", path, r, "cable_white", segments=10, uv_scale=0.1))
    plug = mk_plug_usb_c(p + "_usbc", "plastic_white")
    bpy.context.view_layer.update()
    M = Matrix.Translation(path[-1] + V(0, 0, 0.0039 - r)) @ dir_in.to_track_quat("Y", "Z").to_matrix().to_4x4()
    for o in plug:
        o.matrix_world = M @ o.matrix_world
    parts += plug
    finish_prop(parts, p, "tech", "Smartphone lying face up on the floor charging: white cable runs from the USB-C port, loops on the floor and up the wall to a white UK charger block "
                "whose pins face +Y (place the +Y bound of this prop against the wall; socket centre 0.33 m above the floor).", views=VIEWS, export=EXPORT)


@prop
def build_extension_lead():
    if not wanted("kitchen_extension_lead"):
        return
    p = "kitchen_extension_lead"
    L, W, H = 0.265, 0.062, 0.038
    body = rbox(p + "_body", (L, W, H), "plastic_white", center=(0, 0, H / 2), bevel=0.004, segments=4)
    parts = [body]
    for i in range(4):
        x = -L / 2 + 0.04 + i * 0.058
        face = rbox(p + f"_sf{i}", (0.047, 0.047, 0.0012), "plastic_grey", center=(x, 0.0, H + 0.0003), bevel=0.0015, segments=2)
        parts.append(face)
        parts.append(rbox(p + f"_se{i}", (0.0045, 0.0085, 0.0012), "plastic_black", center=(x, 0.0115, H + 0.0012), bevel=0.0003, segments=1))
        parts.append(rbox(p + f"_sl{i}", (0.0075, 0.0045, 0.0012), "plastic_black", center=(x - 0.0111, -0.0105, H + 0.0012), bevel=0.0003, segments=1))
        parts.append(rbox(p + f"_sn{i}", (0.0075, 0.0045, 0.0012), "plastic_black", center=(x + 0.0111, -0.0105, H + 0.0012), bevel=0.0003, segments=1))
    # switch + LED at the cable end
    sw = rbox(p + "_switch", (0.012, 0.02, 0.006), "plastic_red", center=(L / 2 - 0.018, 0.012, H + 0.002), bevel=0.0015, segments=2)
    sw.rotation_euler.x = math.radians(8)
    parts.append(sw)
    parts.append(cylinder(p + "_led", 0.0022, 0.002, "led_red", segments=12, center=(L / 2 - 0.018, -0.012, H - 0.0005), bevel=0.0003))
    # mains cable out of the +X end to a UK plug lying on its back ~0.35 m away
    r = 0.0033
    rnd = random.Random(505)
    ctrl = [V(L / 2 - 0.01, 0, H / 2), V(L / 2 + 0.03, 0.005, H / 2 - 0.004), V(L / 2 + 0.09, 0.03, r), V(L / 2 + 0.16, -0.01, r), V(L / 2 + 0.2, -0.07, r), V(L / 2 + 0.13, -0.12, r), V(L / 2 + 0.07, -0.13, 0.009)]
    path = catmull(ctrl, n=10)
    for q in path:
        q.z = max(q.z, r)
    parts.append(sweep(p + "_cable", path, r, "cable_white", segments=10, uv_scale=0.1))
    parts += place_plug(mk_plug_uk(p + "_plug", "plastic_white"), path, at_end=True, lift=-0.009)
    parts.append(cylinder(p + "_grommet", 0.0055, 0.01, "plastic_white", segments=12, center=(0, 0, 0), bevel=0.0008, origin="center"))
    parts[-1].rotation_euler.y = math.radians(90)
    parts[-1].location = (L / 2 + 0.003, 0, H / 2)
    # one black plug (another appliance) inserted in socket 2, its cable leaving toward -Y
    x2 = -L / 2 + 0.04 + 1 * 0.058
    plug2 = mk_plug_uk(p + "_plug2", "plastic_black")
    xform_group(plug2, rot=(180, 0, 0))                                           # pins down
    bpy.context.view_layer.update()
    xform_group(plug2, loc=(x2, 0.027, H + 0.0012 + 0.018), rot=(0, 0, 0))
    parts += plug2
    ctrl2 = [V(x2, 0.027, H + 0.0012 + 0.009), V(x2 + 0.005, 0.06, H * 0.6), V(x2 + 0.02, 0.1, 0.0025), V(x2 + 0.06, 0.15, 0.0025)]
    path2 = catmull(ctrl2, n=10)
    for q in path2:
        q.z = max(q.z, 0.0025)
    parts.append(sweep(p + "_cable2", path2, 0.0025, "cable_black", segments=10, uv_scale=0.1))
    finish_prop(parts, p, "tech", "4-gang UK extension lead (26.5 x 6.2 x 3.8 cm, white) lying along X with red switch and red LED; its own cable runs to a white plug on its back at +X/-Y; "
                "a black plug is inserted in socket 2 with its cable leaving to +Y (cut off; extend/hide as needed).", views=VIEWS, export=EXPORT)


def mk_headphones(prefix):
    parts = []
    cz = 0.052                     # cup centre height (cups rest on the floor)
    cx = 0.084
    for s in (-1, 1):
        # cup shell (axis X), built along Z then rotated: z = depth from the outer back (0) to the pad face (0.052)
        prof = [(0, 0.0), (0.018, 0.0015), (0.034, 0.007), (0.043, 0.016), (0.0468, 0.028), (0.0472, 0.036), (0.044, 0.0375), (0.0405, 0.039), (0.0395, 0.044), (0.0, 0.044)]
        cup = rev(prefix + f"_cup{s}", prof, "plastic_black", segments=44)
        paint(cup, "metal_dark", lambda c, n: 0.016 <= c.z <= 0.036 and math.hypot(c.x, c.y) > 0.042)   # metal ring band
        paint(cup, "metal_dark", lambda c, n: math.hypot(c.x, c.y) < 0.017 and c.z < 0.0025)           # logo disc
        paint(cup, "cotton_black", lambda c, n: c.z > 0.043 and math.hypot(c.x, c.y) < 0.039)           # driver grille cloth
        # pad: closed rounded profile around (0.030, 0.049), r 0.011 -> torus-ish cushion
        pad_prof = [(0.030 + 0.012 * math.cos(2 * math.pi * k / 12), 0.047 + 0.009 * math.sin(2 * math.pi * k / 12)) for k in range(13)]
        pad = rev(prefix + f"_pad{s}", pad_prof, "leather_black", segments=44)
        displace_noise(pad, strength=0.0007, scale=0.01, seed=s + 5)
        for o in (cup, pad):
            o.rotation_euler = (0, math.radians(-90 * s), 0)       # local +Z -> toward the head (inward)
            o.location = (s * (cx + 0.004), 0, cz)
        parts += [cup, pad]
        # yoke: arm from the cup top up to the hinge block, plus pivot screw on the cup side
        arm = sweep(prefix + f"_arm{s}", catmull([V(s * (cx - 0.016), 0, cz + 0.040), V(s * (cx - 0.012), 0, cz + 0.056), V(s * (cx + 0.004), 0, cz + 0.078), V(s * (cx + 0.004), 0, cz + 0.095)], n=6),
                    0.0045, "metal_dark", segments=10, rx=0.6, ry=1.3)
        parts.append(arm)
        piv = cylinder(prefix + f"_piv{s}", 0.0065, 0.014, "metal_dark", segments=16, center=(0, 0, 0), bevel=0.0008, origin="center")
        piv.rotation_euler = (0, math.radians(90), 0)
        piv.location = (s * (cx - 0.016), 0, cz + 0.047)
        parts.append(piv)
        hinge = rbox(prefix + f"_hinge{s}", (0.016, 0.03, 0.03), "plastic_black", center=(s * (cx + 0.004), 0, cz + 0.105), bevel=0.003, segments=3)
        parts.append(hinge)
    # headband: half-ellipse over the top from hinge to hinge; flat section 30 mm wide (Y) x 9 mm thick
    hz = cz + 0.115
    band_pts = []
    for i in range(41):
        th = -math.pi / 2 + math.pi * i / 40
        band_pts.append(V((cx + 0.006) * math.sin(th), 0, hz + 0.088 * math.cos(th)))
    band = sweep(prefix + "_band", band_pts, 0.015, "plastic_black", segments=12, rx=1.0, ry=0.3, up_hint=(0, 1, 0))
    parts.append(band)
    # band cushion on the inside of the middle 60 %
    cush_pts = []
    for i in range(25):
        th = -math.pi * 0.3 + math.pi * 0.6 * i / 24
        cush_pts.append(V((cx + 0.006) * math.sin(th) * 0.93, 0, hz + 0.088 * math.cos(th) - 0.007))
    cush = sweep(prefix + "_cush", cush_pts, 0.013, "leather_black", segments=12, rx=0.95, ry=0.45, up_hint=(0, 1, 0))
    displace_noise(cush, strength=0.0008, scale=0.012, seed=9)
    parts.append(cush)
    # coiled cable from the left cup down to the floor, then a straight run to a jack plug
    r = 0.0019
    A0 = V(-(cx + 0.006), -0.006, cz - 0.02)
    A1 = V(-(cx + 0.03), 0.16, 0.0075)
    coil = []
    turns = 11
    for i in range(turns * 24 + 1):
        t = i / (turns * 24)
        a = t * turns * 2 * math.pi
        ax = A0.lerp(A1, t)
        d = (A1 - A0).normalized()
        n1 = d.cross(V(0, 0, 1)).normalized()
        n2 = d.cross(n1)
        rr = 0.0075 if t > 0.05 else 0.0075 * (t / 0.05)
        coil.append(ax + n1 * (rr * math.cos(a)) + n2 * (rr * math.sin(a)))
    lead_in = [V(-(cx + 0.004), -0.006, cz - 0.004), V(-(cx + 0.006), -0.006, cz - 0.012)]
    tail = [A1 + V(0.0, 0.02, -0.004), A1 + V(0.02, 0.05, -0.0055), A1 + V(0.06, 0.07, -0.0055)]
    path = lead_in + coil + catmull(tail, n=8)
    for q in path:
        q.z = max(q.z, r)
    parts.append(sweep(prefix + "_cable", path, r, "cable_black", segments=10, uv_scale=0.1))
    parts += place_plug(mk_plug_jack(prefix + "_jack", "plastic_black"), path, at_end=True, lift=0.0038 - r)
    return parts


@prop
def build_headphones():
    if wanted("kitchen_headphones_over_ear"):
        parts = mk_headphones("kitchen_headphones_over_ear")
        settle(parts)
        finish_prop(parts, "kitchen_headphones_over_ear", "tech", "Big DJ-style over-ear headphones standing on their cups (band up), 19 x 21 cm, with coiled cable from the left cup to a 3.5 mm jack lying ~0.25 m behind (+Y). "
                    "Metal rings, leather pads, hinge blocks, padded band.", views=VIEWS, export=EXPORT)
    if wanted("kitchen_headphones_earbuds_tangled"):
        p = "kitchen_headphones_earbuds_tangled"
        rnd = random.Random(606)
        r = 0.0011
        main = tangle_path(rnd, n=8, ext=(0.07, 0.05), r=r)
        parts = [sweep(p + "_main", main, r, "cable_white", segments=8, uv_scale=0.1)]
        parts += place_plug(mk_plug_jack(p + "_jack", "plastic_white"), main, at_end=False, lift=0.0038 - r)
        split = rbox(p + "_split", (0.006, 0.011, 0.0032), "plastic_white", center=(0, 0.0055, 0), bevel=0.0012, segments=2)
        place_plug([split], main, at_end=True, lift=0.0016 - r)
        parts.append(split)
        Y = main[-1]
        d = end_dir(main)
        for s, tag in ((-1, "l"), (1, "r")):
            side = d.cross(V(0, 0, 1)) * s
            ctrl = [Y + d * 0.011, Y + d * 0.04 + side * 0.02, Y + d * 0.05 + side * 0.06 + V(0, 0, r), Y + d * 0.02 + side * 0.09, Y - d * 0.01 + side * 0.08 + V(0, 0, 0.003)]
            pth = catmull(ctrl, n=8)
            for q in pth:
                q.z = max(q.z, r)
            parts.append(sweep(p + f"_{tag}", pth, r, "cable_white", segments=8, uv_scale=0.1))
            bud = rev(p + f"_bud{tag}", [(0, 0), (0.0045, 0.001), (0.0065, 0.004), (0.0068, 0.009), (0.0055, 0.0125), (0.004, 0.0145), (0.0042, 0.0175), (0.0036, 0.0205), (0.0, 0.0215)], "plastic_white", segments=20)
            paint(bud, "rubber_black", lambda c, n: c.z > 0.0135)
            bpy.context.view_layer.update()
            dd = end_dir(pth)
            bud.matrix_world = Matrix.Translation(pth[-1] + V(0, 0, 0.0068 - r)) @ dd.to_track_quat("Z", "Y").to_matrix().to_4x4()
            parts.append(bud)
        settle(parts)
        finish_prop(parts, p, "tech", "White wired earbuds in a loose tangle ~0.15 m across: 3.5 mm jack, Y-splitter, two buds with black silicone tips.", views=VIEWS, export=EXPORT)


# ================================================================================================ main

def main():
    clean_scene()
    for fn in BUILDERS:
        fn()
    write_manifest()
    if CONTACT:
        contact_sheet()


if __name__ == "__main__":
    main()
