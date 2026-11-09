"""textiles - bed set, bedding, clothes, laundry, bags, trainers, curtains, rug for the Bedsit prop kit.

Run:  "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P Art/Source/blender/textiles.py -- [all|name ...] [--noexport] [--sheet]
Each prop is built in a fresh scene, previewed (front34 + back34 or top), exported to
Assets/Bedsit/Art/Models/textiles/textiles_<name>.fbx and recorded in manifest_textiles.json.
"""
import sys, os, json, math, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, bsk, lib_textiles
importlib.reload(bsk); importlib.reload(lib_textiles)
from bsk import *
from lib_textiles import *

FAMILY = "textiles"
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, f"manifest_{FAMILY}.json")
BUILDERS = {}
ORDER = []


def prop(name, category, variant_of=None, notes="", views=("front34", "back34")):
    def deco(fn):
        BUILDERS[name] = dict(fn=fn, category=category, variant_of=variant_of, notes=notes, views=views)
        ORDER.append(name)
        return fn
    return deco


# ================================================================================================ BED SET
BED_W, BED_L = 0.95, 2.0
MAT_TOP, MAT_BOT = 0.50, 0.32           # mattress top / bottom (slat top) heights
MAT_HW, MAT_HD = 0.465, 0.99            # mattress half extents
EDGE_R = 0.045                           # rounded edge radius used by drapes


def bed_frame_parts(role="wood_light"):
    parts = []
    post = 0.06
    px, py = BED_W / 2 - post / 2, BED_L / 2 - post / 2
    # posts
    for sx in (-1, 1):
        parts.append(box("post_h", (post, post, 0.92), role, center=(sx * px, py, 0), origin="bottom", bevel=0.004))
        parts.append(box("post_f", (post, post, 0.62), role, center=(sx * px, -py, 0), origin="bottom", bevel=0.004))
        # finials (turned knobs)
        for yy, zz in ((py, 0.92), (-py, 0.62)):
            parts.append(lathe("finial", [(0.0, 0), (0.022, 0), (0.026, 0.008), (0.018, 0.016), (0.026, 0.028),
                                           (0.03, 0.045), (0.022, 0.062), (0.0, 0.068)], role, segments=20,
                               center=(sx * px, yy, zz)))
        # side rails + inner ledge batten
        parts.append(box("rail_side", (0.03, BED_L - 2 * post, 0.14), role, center=(sx * (BED_W / 2 - 0.015), 0, 0.20),
                         origin="bottom", bevel=0.003))
        parts.append(box("ledge", (0.03, BED_L - 2 * post, 0.03), role, center=(sx * (BED_W / 2 - 0.045), 0, 0.27),
                         origin="bottom", bevel=0.002))
    # end rails
    for sy in (-1, 1):
        parts.append(box("rail_end", (BED_W - 2 * post, 0.03, 0.14), role, center=(0, sy * (BED_L / 2 - post / 2), 0.20),
                         origin="bottom", bevel=0.003))
    # headboard: top rail, mid rail, spindles
    inner = BED_W - 2 * post
    parts.append(box("head_top", (inner, 0.045, 0.08), role, center=(0, py, 0.80), origin="bottom", bevel=0.004))
    parts.append(box("head_mid", (inner, 0.035, 0.05), role, center=(0, py, 0.46), origin="bottom", bevel=0.003))
    for i in range(6):
        x = -inner / 2 + inner * (i + 0.5) / 6
        parts.append(box("spindle", (0.03, 0.025, 0.29), role, center=(x, py, 0.51), origin="bottom", bevel=0.003))
    # footboard: top rail + spindles
    parts.append(box("foot_top", (inner, 0.045, 0.06), role, center=(0, -py, 0.52), origin="bottom", bevel=0.004))
    for i in range(6):
        x = -inner / 2 + inner * (i + 0.5) / 6
        parts.append(box("spindle_f", (0.03, 0.025, 0.18), role, center=(x, -py, 0.34), origin="bottom", bevel=0.003))
    # slats
    n = 13
    for i in range(n):
        y = -(BED_L / 2 - post - 0.06) + (BED_L - 2 * post - 0.12) * i / (n - 1)
        parts.append(box("slat", (BED_W - 2 * 0.03 - 0.004, 0.07, 0.02), role, center=(0, y, 0.30), origin="bottom",
                         bevel=0.002))
    # centre support rail under slats + 2 small feet
    parts.append(box("centre_rail", (0.04, BED_L - 2 * post, 0.06), role, center=(0, 0, 0.24), origin="bottom", bevel=0.002))
    for y in (-0.6, 0.6):
        parts.append(box("foot", (0.04, 0.04, 0.24), role, center=(0, y, 0), origin="bottom", bevel=0.002))
    return parts


@prop("bed_frame", "furniture",
      notes="Pine single bed frame 0.95x2.0 m. Headboard end at +Y (back against wall), foot faces -Y. Slat top 0.32 m, "
            "side rail top 0.34 m, headboard top 0.88 m, footboard top 0.58 m. Mattress/bedding share this origin (floor, footprint centre).")
def build_bed_frame():
    parts = bed_frame_parts()
    ob = join(parts, "textiles_bed_frame")
    set_origin_world(ob, (0, 0, 0))
    return ob


def mattress_body(name="mattress", sag=0.015, seed=1):
    w, d, h = MAT_HW * 2, MAT_HD * 2, MAT_TOP - MAT_BOT
    ob = grid_box(name, (w, d, h), (13, 28, 3), "cotton_white", center=(0, 0, MAT_BOT), bevel=0.035, bevel_segments=4)
    top_z = h

    def fn(co, n):
        if n.z > 0.8:
            u = co.x / (w / 2); v = co.y / (d / 2)
            dome = max(0.0, 1 - 0.55 * u * u - 0.35 * v * v)
            co.z -= sag * dome * (1 - gauss(v + 0.55, 0.25) * 0.4)       # sleeper's hollow more toward the head
            co.z += 0.006 * math.sin(co.x * 2 * math.pi / 0.155) * math.sin(co.y * 2 * math.pi / 0.155) * \
                smoothstep(0.0, 0.08, min(w / 2 - abs(co.x), d / 2 - abs(co.y)))   # quilting
        elif abs(n.z) < 0.5:
            co.x += n.x * 0.004 * math.sin((co.z - MAT_BOT) / h * math.pi)         # side belly
            co.y += n.y * 0.004 * math.sin((co.z - MAT_BOT) / h * math.pi)
        return co
    displace(ob, fn)
    noise_displace(ob, 0.0025, 0.12, seed)
    subsurf_apply(ob, 1)
    assign_role_by(ob, "fabric_ticking", lambda c: 0.012 < c.z - MAT_BOT < h - 0.012)
    return ob


@prop("mattress", "furniture",
      notes="Single mattress 0.93x1.98x0.18 m sitting on the bed frame slats; mesh spans z 0.32-0.50 so it shares the bed_frame "
            "origin (floor, footprint centre). Mattress top 0.50 m. Quilted white top/bottom, ticking border, piping, 4 fabric handles.")
def build_mattress():
    w, d, h = MAT_HW * 2, MAT_HD * 2, MAT_TOP - MAT_BOT
    parts = [mattress_body()]
    for z in (MAT_BOT + 0.03, MAT_TOP - 0.03):
        loop = rim_points(w + 0.006, d + 0.006, p=5.0, n=96, z=z)
        parts.append(tube_curve("piping", loop, 0.006, "cotton_grey", cyclic=True, res=3))
    for sx in (-1, 1):
        for y in (-0.55, 0.55):
            pts = [Vector((sx * (MAT_HW + 0.002), y - 0.09, MAT_BOT + 0.09)), Vector((sx * (MAT_HW + 0.02), y - 0.05, MAT_BOT + 0.075)),
                   Vector((sx * (MAT_HW + 0.024), y, MAT_BOT + 0.07)), Vector((sx * (MAT_HW + 0.02), y + 0.05, MAT_BOT + 0.075)),
                   Vector((sx * (MAT_HW + 0.002), y + 0.09, MAT_BOT + 0.09))]
            parts.append(strap("handle", pts, 0.03, 0.005, "cotton_grey", smooth_pts=4, hint=(sx, 0, 0)))
    parts.append(box("label", (0.06, 0.004, 0.045), "paper_white", center=(0.25, -(MAT_HD + 0.004), MAT_BOT + 0.04), bevel=0.001))
    ob = join(parts, "textiles_mattress")
    set_origin_world(ob, (0, 0, 0))
    return ob


# ---------------------------------------------------------------------------------------------- drape mapping
def wrap_point(xf, yf, hw, hd, top, r=EDGE_R, floor=0.0, pool_wave=0.0):
    """Flat fabric coordinate -> point draped over a rounded-edged block (hw,hd half extents, top height).
    Excess beyond the edge goes round the edge, hangs vertically, and pools on the floor."""
    dx = max(0.0, abs(xf) - hw); dy = max(0.0, abs(yf) - hd)
    dist = math.hypot(dx, dy)
    if dist <= 1e-9:
        return Vector((xf, yf, top)), 0.0, 0.0
    nx = math.copysign(dx, xf) / dist; ny = math.copysign(dy, yf) / dist
    bx = max(-hw, min(hw, xf)); by = max(-hd, min(hd, yf))
    arc = r * math.pi / 2
    if dist < arc:
        th = dist / r
        out = r * math.sin(th); z = top - r * (1 - math.cos(th))
    else:
        out = r; z = top - r - (dist - arc)
    pooled = 0.0
    if z < floor + 0.02:
        pooled = (floor + 0.02) - z
        z = floor + 0.02 + 0.012 * math.sin(pooled * 18 + xf * 7) * pool_wave
        out += pooled * 0.9
    return Vector((bx + nx * out, by + ny * out, z)), dist, pooled


def shell_surface(name, rows, role, thick, uv_scale=(1.0, 1.0), rim_taper=0.012, angle=75, roles=None):
    """Closed slab from a point grid: top = p + n*t/2, bottom = p - n*t/2, shared rim. thick(i,j) or float."""
    nu = len(rows); nv = len(rows[0])
    normals = [[None] * nv for _ in range(nu)]
    for i in range(nu):
        for j in range(nv):
            du = rows[min(i + 1, nu - 1)][j] - rows[max(i - 1, 0)][j]
            dv = rows[i][min(j + 1, nv - 1)] - rows[i][max(j - 1, 0)]
            n = du.cross(dv)
            normals[i][j] = n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vt = [[None] * nv for _ in range(nu)]; vb = [[None] * nv for _ in range(nu)]
    for i in range(nu):
        for j in range(nv):
            t = thick(i, j) if callable(thick) else thick
            edge = min(i, nu - 1 - i, j, nv - 1 - j)
            tf = min(1.0, edge / 2.5) if edge < 3 else 1.0
            t = lerp(rim_taper, t, tf)
            n = normals[i][j]
            vt[i][j] = bm.verts.new(rows[i][j] + n * t / 2)
            vb[i][j] = bm.verts.new(rows[i][j] - n * t / 2)

    def mk(vs, uvs):
        if len(set(map(id, vs))) < 4:
            return
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        for l, uv in zip(f.loops, uvs):
            l[uvl].uv = uv
    su, sv = uv_scale
    for i in range(nu - 1):
        for j in range(nv - 1):
            u0, u1, v0, v1 = i / (nu - 1) * su, (i + 1) / (nu - 1) * su, j / (nv - 1) * sv, (j + 1) / (nv - 1) * sv
            mk([vt[i][j], vt[i + 1][j], vt[i + 1][j + 1], vt[i][j + 1]], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
            mk([vb[i][j], vb[i][j + 1], vb[i + 1][j + 1], vb[i + 1][j]], [(u0, v0 + 1.1 * sv), (u0, v1 + 1.1 * sv), (u1, v1 + 1.1 * sv), (u1, v0 + 1.1 * sv)])
    # rim walls
    for i in range(nu - 1):
        mk([vt[i][0], vb[i][0], vb[i + 1][0], vt[i + 1][0]], [(0, 0)] * 4)
        mk([vt[i][nv - 1], vt[i + 1][nv - 1], vb[i + 1][nv - 1], vb[i][nv - 1]], [(0, 0)] * 4)
    for j in range(nv - 1):
        mk([vt[0][j], vt[0][j + 1], vb[0][j + 1], vb[0][j]], [(0, 0)] * 4)
        mk([vt[nu - 1][j], vb[nu - 1][j], vb[nu - 1][j + 1], vt[nu - 1][j + 1]], [(0, 0)] * 4)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bsk._obj_from_bm(bm, name, roles or [role])
    shade(ob, True, angle)
    return ob


def fitted_sheet(role, wrinkle=0.004, seed=3, drop=0.12):
    """Fitted sheet over the mattress: top + sides down `drop` with gathered elastic corners."""
    nu, nv = 30, 56
    hw, hd = MAT_HW + 0.004, MAT_HD + 0.004
    rows = []
    for i in range(nu + 1):
        xf = -(hw + drop) + (2 * (hw + drop)) * i / nu
        row = []
        for j in range(nv + 1):
            yf = -(hd + drop) + (2 * (hd + drop)) * j / nv
            p, dist, _ = wrap_point(xf, yf, hw, hd, MAT_TOP + 0.004, r=EDGE_R + 0.004)
            dx = max(0.0, abs(xf) - hw); dy = max(0.0, abs(yf) - hd)
            if dx > 0 and dy > 0:        # elastic gathers at the corners
                ang = math.atan2(dy, dx)
                g = 0.006 * math.sin(ang * 14) * smoothstep(0.0, 0.05, dist)
                p.x += math.copysign(g, xf) * math.cos(ang); p.y += math.copysign(g, yf) * math.sin(ang)
            row.append(p)
        rows.append(row)
    rows = crease_rows(rows, wrinkle, 0.11, seed, 3)
    return grid_surface("fitted_sheet", rows, role, thickness=0.003, offset=1.0, uv_scale=(2, 4))


def duvet_made(role="fabric_duvet", seed=11):
    """Duvet pulled flat: top of mattress from foot (wraps down the foot face) to y=0.75, overhangs the sides 0.2."""
    nu, nv = 36, 60
    W, L = 1.35, 2.0
    rows = []
    foot_over = 0.27
    for i in range(nu + 1):
        u = i / nu
        xf = (u - 0.5) * W
        row = []
        for j in range(nv + 1):
            v = j / nv
            yf = -MAT_HD - foot_over + v * L
            p, dist, _ = wrap_point(xf, yf, MAT_HW, MAT_HD, MAT_TOP + 0.03, r=EDGE_R + 0.02)
            dx = max(0.0, abs(xf) - MAT_HW); dy = max(0.0, abs(yf) - MAT_HD)
            if dist == 0:
                # gentle realistic folds: a couple of long soft ridges + the sleeper's hollow echo
                p.z += 0.012 * math.sin(xf * 5.5 + 0.8) * math.sin(yf * 2.2) + 0.007 * math.sin(yf * 9 + xf * 3)
                p.z += 0.008 * math.sin(xf * 13 + yf * 2) * (0.5 + 0.5 * math.sin(yf * 4.5))
                p.z += 0.012 * smoothstep(0.55, 0.75, yf)          # slight lift toward the open end
            else:
                if dx > 0 and dy > 0:     # hospital corner: diagonal fold ridge
                    diag = (dx - dy) / dist
                    p += Vector((math.copysign(1, xf) * dx / dist, math.copysign(1, yf) * dy / dist, 0)) * 0.018 * gauss(diag, 0.25)
                # hanging part: vertical soft folds
                sway = 0.006 * math.sin(xf * 20 + yf * 7) * smoothstep(0.0, 0.1, dist)
                p.x += sway * (1 if dx > dy else 0); p.y += sway * (1 if dy >= dx else 0)
            row.append(p)
        rows.append(row)
    rows = crease_rows(rows, 0.005, 0.14, seed, 3)
    thick = lambda i, j: 0.055 if abs(rows[i][j].x) < MAT_HW and rows[i][j].y > -MAT_HD else 0.035
    ob = shell_surface("duvet", rows, role, thick, uv_scale=(1.35, 2.0), rim_taper=0.012)
    # piped edge seam along the rim (visible head edge + sides)
    rim = [rows[i][nv] for i in range(nu + 1)]
    parts = [ob, tube_curve("duvet_seam", rim, 0.006, role, res=3)]
    return parts


def turned_sheet(role="cotton_white", seed=5):
    """Flat sheet turned down over the duvet's head edge: lies on the duvet from y=0.47 to 0.75 then folds over the edge."""
    nu, nv = 30, 16
    rows = []
    for i in range(nu + 1):
        x = (i / nu - 0.5) * 0.98
        row = []
        for j in range(nv + 1):
            s = j / nv
            # path: along the duvet top (s<0.65), round the duvet edge (0.65..0.85), down to the sheet (0.85..1)
            if s < 0.65:
                y = 0.47 + (s / 0.65) * 0.28; z = MAT_TOP + 0.085 + 0.004 * math.sin(x * 12)
            elif s < 0.85:
                a = (s - 0.65) / 0.2 * math.pi / 2
                y = 0.75 + 0.03 * math.sin(a); z = MAT_TOP + 0.085 - 0.03 * (1 - math.cos(a))
            else:
                y = 0.78 - (s - 0.85) / 0.15 * 0.015; z = MAT_TOP + 0.055 - (s - 0.85) / 0.15 * 0.045
            row.append(Vector((x, y, z)))
        rows.append(row)
    rows = crease_rows(rows, 0.003, 0.1, seed, 2)
    return grid_surface("turned_sheet", rows, role, thickness=0.004, offset=1.0, uv_scale=(1, 0.4))


@prop("bedding_made", "bedding", variant_of="bedding_messy",
      notes="Made bed: fitted sheet (cotton_pale_blue), duvet pulled flat with hospital corners wrapping the foot, 0.2 m side "
            "overhang, flat sheet turned down over the duvet edge at y 0.47-0.78. Shares the bed_frame/mattress origin. Duvet top "
            "surface ~0.56-0.58 m; pillows go at y~0.70 on the turned-down sheet, z=0.555. Pairs with bedding_messy (tidy state).")
def build_bedding_made():
    parts = [fitted_sheet("cotton_pale_blue", wrinkle=0.0025, seed=3)]
    parts += duvet_made()
    parts.append(turned_sheet())
    ob = join(parts, "textiles_bedding_made")
    set_origin_world(ob, (0, 0, 0))
    return ob


def duvet_messy(role="fabric_duvet", seed=21):
    """Duvet kicked half off: bunched toward the foot in ridges, shifted +X so half hangs down the side to the floor,
    the foot corner pooling on the floor; fitted sheet exposed on the -X strip and head end."""
    nu, nv = 44, 84
    W, L = 1.35, 2.0
    shift = 0.40
    rot = math.radians(12)
    rnd = random.Random(seed)
    FOLD = 1.45                      # flat-length where the head end is thrown back over itself
    R = 0.05                         # fold-over radius
    comp = 0.62
    # random bunch ridges: (centre yf, wave amp, wave freq, phase, width, height, tilt)
    ridges = []
    yc_ = 0.12
    while yc_ < FOLD - 0.1:
        ridges.append((yc_, rnd.uniform(0.04, 0.14), rnd.uniform(3.0, 7.0), rnd.uniform(0, 6.3), rnd.uniform(0.06, 0.13),
                       rnd.uniform(0.05, 0.13), rnd.uniform(-0.25, 0.25)))
        yc_ += rnd.uniform(0.17, 0.30)
    ridges_b = [(rnd.uniform(0.1, 0.45), rnd.uniform(0.03, 0.08), rnd.uniform(3, 6), rnd.uniform(0, 6.3), rnd.uniform(0.05, 0.1),
                 rnd.uniform(0.04, 0.09), rnd.uniform(-0.2, 0.2)) for _ in range(3)]
    diag = [(rnd.uniform(-0.5, 0.5), rnd.uniform(-0.6, 0.6), rnd.uniform(0.05, 0.09), rnd.uniform(0.03, 0.06)) for _ in range(3)]

    def ridge_h(xf, yf, lst):
        hsum = 0.0
        for (c, a, f, ph, wd, hh, tilt) in lst:
            cl = c + a * math.sin(xf * f + ph) + tilt * xf
            d = abs(yf - cl)
            if d < wd:
                hsum += hh * (0.5 + 0.5 * math.cos(math.pi * d / wd))
        return hsum
    rows = []
    for i in range(nu + 1):
        u = i / nu
        row = []
        for j in range(nv + 1):
            v = j / nv
            yf = v * L
            xf0 = (u - 0.5) * W
            if yf <= FOLD:
                yc = yf * comp
                zoff = ridge_h(xf0, yf, ridges)
                # a few diagonal pulls
                for (dx0, dy0, wd, hh) in diag:
                    d = abs((xf0 - dx0) * 0.7 - (yf * comp - 0.45 - dy0))
                    if d < wd:
                        zoff += hh * (0.5 + 0.5 * math.cos(math.pi * d / wd))
                layer = 0.0
            else:
                s = yf - FOLD
                if s < math.pi * R:
                    th = s / R
                    yc = FOLD * comp + R * math.sin(th)
                    layer = R * (1 - math.cos(th))
                else:
                    yc = FOLD * comp - (s - math.pi * R) * 0.75
                    layer = 2 * R
                zoff = layer * 0.85 + ridge_h(xf0, s, ridges_b) * (1 if s > math.pi * R else 0)
            # skew/shift so the +x side hangs off
            xr = xf0 * math.cos(rot) - yc * math.sin(rot) + shift
            yr = xf0 * math.sin(rot) + yc * math.cos(rot) - MAT_HD + 0.04
            p, dist, pooled = wrap_point(xr, yr, MAT_HW, MAT_HD, MAT_TOP + 0.03, r=EDGE_R + 0.02, pool_wave=1.0)
            dx = max(0.0, abs(xr) - MAT_HW)
            on = 1.0 - smoothstep(0.0, 0.22, dist)
            p.z += zoff * on
            # ridges continue a little way over the edge as bulges outward
            if dist > 0:
                p += Vector((math.copysign(1, xr) if dx > 0 else 0, 0, 0)) * zoff * 0.35 * smoothstep(0.0, 0.12, dist) * (1 - smoothstep(0.1, 0.35, dist))
            if dist > 0 and pooled <= 0:
                f = 0.02 * math.sin(yr * 16 + xr * 3) * smoothstep(0.0, 0.12, dist)
                p.y += f * 0.5
                p.x += 0.014 * math.sin(yr * 21 + 1.0) * smoothstep(0.0, 0.12, dist) * (1 if dx > 0 else 0)
            if pooled > 0:
                p.z += 0.035 * (0.5 + 0.5 * math.sin(xr * 25 + yr * 11))
            row.append(p)
        rows.append(row)
    rows = crease_rows(rows, 0.016, 0.17, seed, 2)
    rows = crease_rows(rows, 0.006, 0.055, seed + 1, 2)
    thick = lambda i, j: 0.05 if rows[i][j].z > MAT_TOP - 0.02 else 0.035
    ob = shell_surface("duvet", rows, role, thick, uv_scale=(1.35, 2.0), rim_taper=0.012)
    rim = [rows[i][nv] for i in range(nu + 1)]
    parts = [ob, tube_curve("duvet_seam", rim, 0.006, role, res=3)]
    return parts


@prop("bedding_messy", "bedding",
      notes="Slept-in bed: wrinkled fitted sheet (cotton_pale_blue) exposed on the -X strip and head end; duvet bunched in ridges "
            "toward the foot, kicked half off the +X side, foot corner dragged to the floor at x~0.55-0.75. Shares the "
            "bed_frame/mattress origin. Duvet ridges reach ~0.68 m. Messy pillows go at head end y~0.72, z=0.505. Pairs with bedding_made.")
def build_bedding_messy():
    parts = [fitted_sheet("cotton_pale_blue", wrinkle=0.006, seed=8)]
    parts += duvet_messy()
    ob = join(parts, "textiles_bedding_messy")
    set_origin_world(ob, (0, 0, 0))
    return ob


# ---------------------------------------------------------------------------------------------- pillows & cushions
def pillow_made(name, role, seed, w=0.66, d=0.43, h=0.15):
    def shape(u, v):
        return (1.0 + 0.05 * math.sin(u * 6 + seed), 1.0, 0.0)
    P, K, TF = 4.5, 0.5, 0.6
    body = pillow(name, w, d, h, role, nu=26, nv=18, p=P, k=K, seed=seed, crease=0.006, crease_scale=0.1, shape=shape, top_frac=TF)
    # pillowcase: rim seam + housewife flap seam across one end following the top surface
    rim = rim_points(w - 0.004, d - 0.004, p=P, n=80, z=h * (1 - TF))
    seam = tube_curve("seam", rim, 0.0035, role, cyclic=True, res=2)
    fl = []
    for j in range(25):
        v = 0.02 + 0.96 * j / 24
        x, y, zt, zb = pillow_profile(0.12, v, w, d, h, P, K, TF, shape)
        fl.append(Vector((x, y, zt + h * (1 - TF) + 0.002)))
    flap = tube_curve("flap_seam", fl, 0.003, role, res=2)
    ob = join([body, seam, flap], name)
    origin_bottom_centre(ob)
    return ob


def pillow_messy(name, role, seed, w=0.66, d=0.43, h=0.14):
    rnd = random.Random(seed)
    cu, cv = 0.55 + 0.15 * rnd.random(), 0.45 + 0.1 * rnd.random()
    lift_corner = (0.08, 0.9) if rnd.random() < 0.5 else (0.92, 0.1)

    def shape(u, v):
        dent = 1 - 0.55 * gauss(math.hypot((u - cu) * 1.3, (v - cv)), 0.17)
        lump = 1 + 0.35 * gauss(math.hypot(u - (1 - cu), v - 0.5), 0.2)
        dz = 0.06 * gauss(math.hypot((u - lift_corner[0]) * 0.8, v - lift_corner[1]), 0.14)
        return (dent * lump, 0.9 + 0.1 * dent, dz)
    body = pillow(name, w, d, h, role, nu=28, nv=20, p=3.2, k=0.45, seed=seed, crease=0.016, crease_scale=0.08, octaves=3,
                  shape=shape, top_frac=0.62)
    noise_displace(body, 0.004, 0.025, seed + 3)
    # loose pillowcase end bunched flat on the sheet
    flap = pillow("flap", 0.15, d - 0.05, 0.022, role, nu=10, nv=12, p=4, k=0.3, seed=seed + 9, crease=0.008, crease_scale=0.04)
    flap.location = (w / 2 - 0.03, 0.01 * (1 if seed % 2 else -1), 0.0)
    flap.rotation_euler = (0, 0, math.radians(12 if seed % 2 else -9))
    ob = join([body, flap], name)
    origin_bottom_centre(ob)
    return ob


@prop("pillow_made_a", "bedding", notes="Plumped pillow 0.66x0.43x0.15, cotton_white case with flap seam. Origin bottom centre; sits at z=0.555 on bedding_made. Pairs with pillow_messy_a.")
def build_pillow_made_a():
    return pillow_made("textiles_pillow_made_a", "cotton_white", 1)


@prop("pillow_made_b", "bedding", variant_of="pillow_made_a", notes="Plumped pillow, pale blue case, slightly fatter. Pairs with pillow_messy_b.")
def build_pillow_made_b():
    return pillow_made("textiles_pillow_made_b", "cotton_pale_blue", 2, h=0.165)


@prop("pillow_messy_a", "bedding", variant_of="pillow_made_a", notes="Squashed, dented, creased pillow with bunched case end. Pairs with pillow_made_a (tidy).")
def build_pillow_messy_a():
    return pillow_messy("textiles_pillow_messy_a", "cotton_white", 4)


@prop("pillow_messy_b", "bedding", variant_of="pillow_made_b", notes="Squashed pale blue pillow, one corner lifted. Pairs with pillow_made_b (tidy).")
def build_pillow_messy_b():
    return pillow_messy("textiles_pillow_messy_b", "cotton_pale_blue", 7, h=0.13)


@prop("cushion_a", "soft_furnishing", notes="Square scatter cushion 0.45x0.45x0.13, mustard with white piping. Origin bottom centre.")
def build_cushion_a():
    body = pillow("cushion", 0.45, 0.45, 0.13, "cotton_yellow", nu=20, nv=20, p=2.8, k=0.38, seed=31, crease=0.007, crease_scale=0.07)
    rim = rim_points(0.45, 0.45, p=2.8, n=72, z=0.13 * 0.4)
    pipe = tube_curve("piping", rim, 0.006, "cotton_white", cyclic=True, res=3)
    ob = join([body, pipe], "textiles_cushion_a")
    origin_bottom_centre(ob)
    return ob


@prop("cushion_b", "soft_furnishing", variant_of="cushion_a", notes="Rectangular cushion 0.52x0.32x0.12, patterned cover with two covered buttons and dimples. Origin bottom centre.")
def build_cushion_b():
    def shape(u, v):
        d = 1 - 0.45 * (gauss(math.hypot((u - 0.3) * 1.6, (v - 0.5)), 0.08) + gauss(math.hypot((u - 0.7) * 1.6, (v - 0.5)), 0.08))
        return (d, d, 0.0)
    body = pillow("cushion", 0.52, 0.32, 0.12, "fabric_pattern", nu=24, nv=16, p=3.5, k=0.42, seed=32, crease=0.006, crease_scale=0.06, shape=shape)
    parts = [body]
    for x in (-0.104, 0.104):
        parts.append(lathe("button", [(0, 0), (0.011, 0), (0.012, 0.004), (0.008, 0.007), (0, 0.008)], "cotton_navy", segments=16,
                           center=(x, 0, 0.12 * 0.6 * 0.58)))
    ob = join(parts, "textiles_cushion_b")
    origin_bottom_centre(ob)
    return ob


@prop("throw_blanket_folded", "soft_furnishing",
      notes="Folded chunky-knit throw 0.48x0.36x0.075 with tassel fringe along -Y edge. Fold edge at +X, open layers at -X. Lay on bed foot or chair. Origin bottom centre.")
def build_throw():
    w, d, h = 0.48, 0.36, 0.075
    ob = grid_box("throw", (w, d, h), (14, 10, 2), "knit_mustard", bevel=0.03, bevel_segments=3)

    def fn(co, n):
        # knit ribbing + open-side layer grooves + fold edge rounder
        co += n * 0.0015 * math.sin(co.y * 2 * math.pi / 0.018)
        if co.x < -w / 2 + 0.02:
            g = sum(gauss(co.z - zc, 0.004) for zc in (h * 0.33, h * 0.66))
            co.x += 0.006 * g
        if n.z > 0.5:
            co.z -= 0.012 * ((co.x / (w / 2)) ** 2) * 0.5 + 0.004 * math.sin(co.y * 9)
        return co
    displace(ob, fn)
    noise_displace(ob, 0.003, 0.06, 41)
    subsurf_apply(ob, 1)
    parts = [ob]
    rnd = random.Random(41)
    for i in range(22):
        x = -w / 2 + 0.02 + (w - 0.04) * i / 21
        for zc in (0.012, 0.03, 0.05):
            a = rnd.uniform(-0.6, 0.6)
            pts = [Vector((x, -d / 2 + 0.006, zc)), Vector((x + 0.006 * a, -d / 2 - 0.012, zc - 0.006)),
                   Vector((x + 0.012 * a, -d / 2 - 0.022, max(0.004, zc - 0.014)))]
            parts.append(tube_curve("tassel", pts, 0.0036, "knit_mustard", res=1, smooth_pts=2))
    ob = join(parts, "textiles_throw_blanket_folded")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ GARMENT PARTS
def ribbed_ring(name, center, radius, height, role, ribs=16, squash=1.0, rot=(0, 0, 0)):
    """Ribbed cuff / hem / collar: short tube with radial ribs."""
    rows = []
    for k in range(4):
        z = -height / 2 + height * k / 3
        ring = []
        for i in range(ribs * 2):
            a = 2 * math.pi * i / (ribs * 2)
            r = radius + ((0.0012 if i % 2 == 0 else -0.0012) if ribs > 1 else 0.0) * (1 if 0 < k < 3 else 0.3)
            ring.append(Vector((r * math.cos(a), r * math.sin(a) * squash, z)))
        rows.append(ring)
    ob = grid_surface(name, rows, role, wrap=True, thickness=0.0035, offset=0.0, uv_scale=(1, 0.1), angle=80)
    ob.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")
    ob.location = center
    return ob


def sleeve(name, path, radius, role, seed, taper_end=0.8, squash=0.6, crease=0.005, cuff=True, cuff_role=None, taper_start=1.0, bunch=0.08):
    """Collapsed garment tube (sleeve / trouser leg) along path with a ribbed or hemmed cuff at the end."""
    pts = [Vector(p) for p in path]
    ph = seed * 1.7
    plen = sum((b - a).length for a, b in zip(pts[:-1], pts[1:]))
    cyc = max(1.0, plen / 0.11)
    # bunched fabric: radius pulses along the length (gathered folds), flattened, creased
    tap = lambda t: lerp(taper_start, taper_end, t) * (1 + bunch * math.sin(t * cyc * 2 * math.pi + ph) + bunch * 0.5 * math.sin(t * cyc * 2.3 * 2 * math.pi + 2 * ph))
    parts = [soft_tube(name, pts, radius, role, segs=16, samples=6, taper=tap, caps="round",
                       seed=seed, crease=crease * 1.8, crease_scale=0.045, squash=squash)]
    if cuff:
        sm = catmull_rom(pts, 5)
        end = sm[-1]; prev = sm[-3]
        t = (end - prev).normalized()
        q = t.to_track_quat("Z", "Y")
        rr = radius * taper_end
        cuffob = ribbed_ring(name + "_cuff", end - t * rr * 0.5, rr + 0.0015, 0.026, cuff_role or role, ribs=14, squash=squash + 0.1)
        cuffob.rotation_euler = q.to_euler()
        parts.append(cuffob)
    return parts


def sock(name, toe, cuff_pt, role, seed, squash=0.55, inside_out=False, heel_role=None, r=0.034):
    """Sock lying on the floor: toe -> heel bend -> ankle -> ribbed cuff. toe/cuff_pt are (x, y) floor positions."""
    tx, ty = toe; cx, cy = cuff_pt
    hx, hy = lerp(tx, cx, 0.62), lerp(ty, cy, 0.62)
    # bend the ankle sideways at the heel
    dx, dy = cx - tx, cy - ty
    nx, ny = -dy, dx
    nl = math.hypot(nx, ny) or 1.0
    nx, ny = nx / nl * 0.07, ny / nl * 0.07
    z = r * squash
    path = [(tx, ty, z), (lerp(tx, hx, 0.5), lerp(ty, hy, 0.5), z), (hx, hy, z * 1.1), (hx + nx, hy + ny, z * 1.15), (cx + nx * 1.4, cy + ny * 1.4, z * 1.2)]
    parts = sleeve(name, path, r, role, seed, taper_end=1.0, taper_start=0.78, squash=squash,
                   crease=0.01 if inside_out else 0.005, cuff=not inside_out, bunch=0.12 if inside_out else 0.06)
    if heel_role:
        hp = Vector((hx, hy, 0)); tp = Vector((tx, ty, 0))
        assign_role_by(parts[0], heel_role, lambda c: (Vector((c.x, c.y, 0)) - hp).length < r * 1.1 or (Vector((c.x, c.y, 0)) - tp).length < r * 1.3)
    return parts


def hood(name, role, seed, center=(0, 0, 0), rot_z=0.0, open_=True):
    """Hoodie hood lying flat (folded shell), with drawstrings."""
    body = pillow(name, 0.30, 0.27, 0.055, role, nu=14, nv=12, p=3.0, k=0.4, seed=seed, crease=0.009, crease_scale=0.05,
                  shape=lambda u, v: (1.0 - 0.5 * smoothstep(0.75, 1.0, v) * (1 if open_ else 0), 1.0, 0.0))
    parts = [body]
    rnd = random.Random(seed)
    for sx in (-1, 1):
        pts = [Vector((sx * 0.06, -0.12, 0.02)), Vector((sx * (0.08 + 0.04 * rnd.random()), -0.2, 0.006)),
               Vector((sx * (0.05 + 0.08 * rnd.random()), -0.3, 0.003))]
        parts.append(tube_curve(name + "_string", pts, 0.0028, "cotton_white", res=2, smooth_pts=4))
        parts.append(cylinder(name + "_aglet", 0.004, 0.018, "plastic_black", segments=10, center=(pts[-1].x, pts[-1].y - 0.006, 0.0), bevel=0.0))
    ob = join(parts, name)
    ob.rotation_euler = (0, 0, math.radians(rot_z))
    ob.location = center
    return ob


def tshirt_flat(name, role, seed, center=(0, 0, 0), rot_z=0.0, crease=0.012, collar_role=None):
    rnd = random.Random(seed)
    body = pillow(name, 0.50, 0.66, 0.035, role, nu=22, nv=26, p=6.0, k=0.3, seed=seed, crease=crease, crease_scale=0.07,
                  shape=lambda u, v: (1.0 + 0.6 * gauss(math.hypot(u - 0.5 - 0.2 * math.sin(seed), v - 0.5), 0.25), 1.0, 0.0))
    parts = [body]
    for sx in (-1, 1):
        sl = pillow(name + "_sleeve", 0.20, 0.19, 0.03, role, nu=8, nv=8, p=5.0, k=0.3, seed=seed + 1, crease=0.008, crease_scale=0.05)
        sl.location = (sx * 0.30, 0.20 + rnd.uniform(-0.02, 0.02), 0.0)
        sl.rotation_euler = (0, 0, math.radians(sx * rnd.uniform(20, 40)))
        parts.append(sl)
    coll = rim_points(0.17, 0.09, p=2.0, n=36, z=0.0)
    cob = tube_curve(name + "_collar", coll, 0.005, collar_role or role, cyclic=True, res=2)
    cob.location = (0.0, 0.29, 0.02)
    parts.append(cob)
    ob = join(parts, name)
    ob.rotation_euler = (0, 0, math.radians(rot_z))
    ob.location = center
    return ob


def jeans_parts(name, role, seed, legA, legB, seat_center=(0, -0.12, 0), waist_center=(0, 0.0), squash=0.55):
    """Jeans: waistband ring + seat cushion + two legs (paths given from hip to hem) + pockets, belt loops, fly."""
    rnd = random.Random(seed)
    parts = []
    seat = pillow(name + "_seat", 0.40, 0.30, 0.075, role, nu=14, nv=12, p=3.5, k=0.4, seed=seed, crease=0.009, crease_scale=0.06)
    seat.location = seat_center
    parts.append(seat)
    wb = rim_points(0.38, 0.16, p=2.2, n=48, z=0.0)
    wbo = tube_curve(name + "_waist", wb, 0.011, role, cyclic=True, res=3)
    wbo.location = (waist_center[0], waist_center[1], 0.012)
    parts.append(wbo)
    for k in range(5):
        a = math.pi * (0.1 + 0.8 * k / 4)
        x, y = 0.19 * math.cos(a), 0.08 * math.sin(a) + waist_center[1]
        parts.append(box(name + "_loop", (0.012, 0.004, 0.03), role, center=(x, y, 0.004), bevel=0.001))
    parts.append(tube_curve(name + "_fly", [Vector((0, waist_center[1] - 0.01, 0.03)), Vector((0.005, waist_center[1] - 0.08, 0.05)),
                                            Vector((0.0, waist_center[1] - 0.15, 0.03))], 0.0025, "cotton_yellow", res=1, smooth_pts=3))
    squash = min(squash, 0.42)
    for i, (pk, sx) in enumerate(((legA, -1), (legB, 1))):
        parts += sleeve(name + f"_leg{i}", pk, 0.09, role, seed + i, taper_end=0.82, squash=squash, crease=0.006, cuff=False)
        # hem: plain folded hem ring
        sm = catmull_rom([Vector(p) for p in pk], 5)
        end, prev = sm[-1], sm[-3]
        t = (end - prev).normalized()
        q = t.to_track_quat("Z", "Y")
        hem = ribbed_ring(name + "_hem", end - t * 0.03, 0.09 * 0.82 + 0.002, 0.02, role, ribs=1, squash=squash + 0.1)
        hem.rotation_euler = q.to_euler()
        parts.append(hem)
    return parts


def folded_item(name, w, d, h, role, seed=0, layers=2, fold_side="+x", fuzz=0.0025):
    """Neatly folded garment: rounded slab, fold edge on fold_side, layer grooves on the opposite side."""
    ob = grid_box(name, (w, d, h), (10, 8, 2), role, bevel=min(h * 0.45, 0.03), bevel_segments=3)
    sgn = 1 if fold_side == "+x" else -1

    def fn(co, n):
        if sgn * co.x < -w / 2 + 0.02:      # open side: grooves between layers
            g = sum(gauss(co.z - h * (k + 1) / (layers + 1), h * 0.08) for k in range(layers))
            co.x += sgn * 0.006 * g
        if n.z > 0.5:                        # soft dome + slight sag at corners
            co.z += 0.004 * (1 - (2 * co.x / w) ** 2) * (1 - (2 * co.y / d) ** 2) - 0.002 * ((2 * co.x / w) ** 4)
        return co
    displace(ob, fn)
    noise_displace(ob, fuzz, 0.05, seed)
    return ob


def heap_base(name, w, d, h, role, seed, lumps=3, crease=0.014, sigma=(0.18, 0.3)):
    rnd = random.Random(seed)
    cs = [(rnd.uniform(0.25, 0.75), rnd.uniform(0.25, 0.75), rnd.uniform(0.4, 1.0), rnd.uniform(*sigma)) for _ in range(lumps)]
    # fabric fold ridges: random lines through uv space (px, py, angle, width, height, wobble)
    ridges = [(rnd.uniform(0.2, 0.8), rnd.uniform(0.2, 0.8), rnd.uniform(0, math.pi), rnd.uniform(0.04, 0.08), rnd.uniform(0.12, 0.28), rnd.uniform(2, 5))
              for _ in range(lumps + 2)]

    def raw(u, v):
        return 0.4 + sum(a * gauss(math.hypot(u - cu, v - cv), sg) for cu, cv, a, sg in cs)
    mx = max(raw(i / 20, j / 20) for i in range(21) for j in range(21))

    def shape(u, v):
        base = raw(u, v) / mx
        dz = 0.0
        for px, py, ang, wd, hh, wob in ridges:
            dd = abs((u - px) * math.sin(ang) - (v - py) * math.cos(ang) + 0.04 * math.sin(wob * (u + v) * 3.0))
            if dd < wd:
                dz += hh * (0.5 + 0.5 * math.cos(math.pi * dd / wd)) * h * base * 0.5
        return (base, 1.0, dz)
    ob = pillow(name, w, d, h, role, nu=28, nv=24, p=2.6, k=0.5, seed=seed, crease=crease, crease_scale=0.07, octaves=3, shape=shape,
                top_frac=0.9)
    noise_displace(ob, 0.005, 0.03, seed + 2)
    return ob


# ================================================================================================ CLOTHES PILES
@prop("clothes_pile_a", "clutter", views=("front34", "top"),
      notes="Floor heap ~0.66x0.6x0.26 m: grey-marl hoodie bunched on top (hood + one sleeve out), denim jeans leg trailing -X, black T-shirt "
            "half under, white socks at the front. MESSY state; tidy partner textiles_folded_stack_a. Origin bottom centre.")
def build_pile_a():
    parts = []
    t = tshirt_flat("tee", "cotton_black", 101, center=(0.08, -0.05, 0.0), rot_z=28)
    parts.append(t)
    base = heap_base("hoodie_body", 0.50, 0.44, 0.18, "cotton_marl", 102, lumps=3, crease=0.016)
    base.location = (0.0, 0.02, 0.025)
    parts.append(base)
    parts.append(hood("hood", "cotton_marl", 103, center=(0.08, 0.1, 0.14), rot_z=-30, open_=False))
    parts += sleeve("hoodie_sleeve", [(0.08, 0.08, 0.14), (0.2, 0.16, 0.09), (0.3, 0.2, 0.035), (0.34, 0.12, 0.03)], 0.062, "cotton_marl", 104,
                    taper_end=0.75, squash=0.55, crease=0.005)
    parts += sleeve("hoodie_sleeve2", [(-0.1, 0.12, 0.12), (-0.2, 0.2, 0.06), (-0.26, 0.26, 0.03)], 0.06, "cotton_marl", 106,
                    taper_end=0.75, squash=0.55, crease=0.005)
    hemr = tube_curve("hoodie_hem", [p for p in rim_points(0.46, 0.12, p=2.0, n=40, z=0.0) if p.y < 0], 0.007, "cotton_marl", res=2)
    hemr.location = (0.02, -0.17, 0.012); hemr.rotation_euler = (0, 0, math.radians(10))
    parts.append(hemr)
    parts += sleeve("jeans_leg", [(-0.08, -0.08, 0.1), (-0.2, -0.04, 0.05), (-0.3, 0.02, 0.035), (-0.38, -0.02, 0.035)], 0.09, "denim", 105,
                    taper_end=0.8, squash=0.4, crease=0.006, cuff=False)
    hem = ribbed_ring("jeans_hem", (-0.38, -0.02, 0.03), 0.074, 0.02, "denim", ribs=1, squash=0.5, rot=(0, 90, -20))
    parts.append(hem)
    parts += sock("sock0", (-0.02, -0.33), (-0.14, -0.22), "cotton_white", 110, heel_role="cotton_grey")
    parts += sock("sock1", (0.14, -0.3), (0.06, -0.18), "cotton_white", 111, inside_out=True)
    ob = join(parts, "textiles_clothes_pile_a")
    origin_bottom_centre(ob)
    return ob


@prop("clothes_pile_b", "clutter", variant_of="clothes_pile_a", views=("front34", "top"),
      notes="Taller heap ~0.55x0.55x0.3 m: red T-shirt mass with jeans folded over the top (leg arching over, waistband visible), navy hoodie "
            "sleeve across the front, grey socks. MESSY state; tidy partner textiles_folded_stack_b. Origin bottom centre.")
def build_pile_b():
    parts = []
    base = heap_base("tee_body", 0.50, 0.46, 0.24, "cotton_red", 201, lumps=2)
    parts.append(base)
    parts += jeans_parts("jeans", "denim", 202,
                         legA=[(-0.08, -0.1, 0.22), (-0.2, -0.2, 0.16), (-0.26, -0.3, 0.06), (-0.2, -0.38, 0.04)],
                         legB=[(0.08, -0.1, 0.22), (0.1, 0.05, 0.26), (0.05, 0.22, 0.18), (0.0, 0.33, 0.05)],
                         seat_center=(0.0, -0.02, 0.20), waist_center=(0.0, 0.08), squash=0.6)
    # the waistband + seat need lifting onto the heap top: jeans_parts put them at z~0 -> move via join later; raise here
    for p in parts[1:]:
        if p.name.startswith("jeans_waist") or p.name.startswith("jeans_loop") or p.name.startswith("jeans_fly"):
            p.location.z += 0.21
    parts += sleeve("hoodie_sleeve", [(0.2, -0.18, 0.1), (0.3, -0.26, 0.05), (0.38, -0.3, 0.03), (0.44, -0.24, 0.03)], 0.06, "cotton_navy", 203,
                    taper_end=0.78, squash=0.6)
    hb = pillow("hoodie_body", 0.34, 0.30, 0.06, "cotton_navy", nu=12, nv=12, p=3, k=0.35, seed=204, crease=0.01, crease_scale=0.05)
    hb.location = (0.22, -0.12, 0.0); hb.rotation_euler = (0, 0, math.radians(20))
    parts.append(hb)
    parts += sock("sock0", (-0.3, 0.22), (-0.2, 0.1), "cotton_grey", 210)
    parts += sock("sock1", (-0.34, 0.02), (-0.24, -0.06), "cotton_grey", 211, inside_out=True)
    ob = join(parts, "textiles_clothes_pile_b")
    origin_bottom_centre(ob)
    return ob


@prop("clothes_pile_c", "clutter", variant_of="clothes_pile_a", views=("front34", "top"),
      notes="Wide low spread ~0.7x0.6x0.2 m: green T-shirt flat underneath, denim jeans crumpled with both legs and waistband on top, "
            "black hoodie hood over one corner, one white + one grey sock. MESSY state; tidy partner textiles_folded_stack_c. Origin bottom centre.")
def build_pile_c():
    parts = []
    parts.append(tshirt_flat("tee", "cotton_green", 301, center=(-0.05, 0.02, 0.0), rot_z=-70, crease=0.014))
    mound = heap_base("tee_mass", 0.42, 0.36, 0.15, "cotton_green", 305, lumps=2, crease=0.012)
    mound.location = (-0.06, 0.0, 0.02)
    parts.append(mound)
    parts += jeans_parts("jeans", "denim", 302,
                         legA=[(-0.09, -0.12, 0.17), (-0.22, -0.22, 0.09), (-0.3, -0.12, 0.05), (-0.26, 0.0, 0.045)],
                         legB=[(0.09, -0.12, 0.17), (0.18, -0.26, 0.08), (0.3, -0.26, 0.05), (0.34, -0.16, 0.045)],
                         seat_center=(0.0, -0.02, 0.12), waist_center=(0.0, 0.1), squash=0.55)
    for p in parts[2:]:
        if p.name.startswith("jeans_waist") or p.name.startswith("jeans_loop") or p.name.startswith("jeans_fly"):
            p.location.z += 0.13
    parts.append(hood("hood", "cotton_black", 303, center=(0.2, 0.16, 0.03), rot_z=140, open_=True))
    hb = pillow("hoodie_body", 0.36, 0.32, 0.07, "cotton_black", nu=12, nv=12, p=3, k=0.35, seed=304, crease=0.012, crease_scale=0.05)
    hb.location = (0.26, 0.08, 0.0); hb.rotation_euler = (0, 0, math.radians(-25))
    parts.append(hb)
    parts += sock("sock0", (-0.3, 0.2), (-0.22, 0.06), "cotton_white", 310, heel_role="cotton_grey")
    parts += sock("sock1", (0.04, 0.3), (0.18, 0.26), "cotton_grey", 311)
    ob = join(parts, "textiles_clothes_pile_c")
    origin_bottom_centre(ob)
    return ob


def stack(name, items, seed):
    """items: list of (w, d, h, role, layers). Stacked largest first with small offsets/rotations."""
    rnd = random.Random(seed)
    parts = []
    z = 0.0
    for k, (w, d, h, role, layers) in enumerate(items):
        it = folded_item(f"{name}_{k}", w, d, h, role, seed + k, layers=layers)
        it.location = (rnd.uniform(-0.012, 0.012), rnd.uniform(-0.012, 0.012), z - 0.003 * k)
        it.rotation_euler = (0, 0, math.radians(rnd.uniform(-5, 5)))
        parts.append(it)
        z += h - 0.004
    ob = join(parts, name)
    origin_bottom_centre(ob)
    return ob


@prop("folded_stack_a", "clutter", notes="Neat folded stack ~0.3x0.25x0.2: folded jeans (denim) at the bottom, grey-marl hoodie, black T-shirt, white socks roll on top. TIDY partner of clothes_pile_a. Origin bottom centre.")
def build_stack_a():
    ob = stack("textiles_folded_stack_a", [(0.30, 0.25, 0.07, "denim", 3), (0.30, 0.24, 0.065, "cotton_marl", 2), (0.27, 0.22, 0.035, "cotton_black", 2)], 401)
    roll = soft_tube("socks", [Vector((-0.06, 0, 0.0)), Vector((0.06, 0, 0.0))], 0.033, "cotton_white", segs=14, samples=4, seed=402, crease=0.003, squash=0.8)
    roll.rotation_euler = (0, 0, math.radians(25))
    lo, hi = bounds(ob)
    roll.location = (0.0, 0.0, hi.z + 0.026)
    ob = join([ob, roll], "textiles_folded_stack_a")
    origin_bottom_centre(ob)
    return ob


@prop("folded_stack_b", "clutter", variant_of="folded_stack_a", notes="Folded stack: red T-shirt, folded jeans, navy hoodie on top, grey socks. TIDY partner of clothes_pile_b. Origin bottom centre.")
def build_stack_b():
    ob = stack("textiles_folded_stack_b", [(0.31, 0.26, 0.04, "cotton_red", 2), (0.30, 0.25, 0.07, "denim", 3), (0.29, 0.24, 0.06, "cotton_navy", 2)], 411)
    roll = soft_tube("socks", [Vector((-0.05, 0, 0.0)), Vector((0.05, 0, 0.0))], 0.03, "cotton_grey", segs=14, samples=4, seed=412, crease=0.003, squash=0.8)
    lo, hi = bounds(ob)
    roll.location = (0.05, 0.03, hi.z + 0.024); roll.rotation_euler = (0, 0, math.radians(-30))
    ob = join([ob, roll], "textiles_folded_stack_b")
    origin_bottom_centre(ob)
    return ob


@prop("folded_stack_c", "clutter", variant_of="folded_stack_a", notes="Folded stack: black hoodie bottom, folded jeans, green T-shirt, white + grey socks. TIDY partner of clothes_pile_c. Origin bottom centre.")
def build_stack_c():
    ob = stack("textiles_folded_stack_c", [(0.31, 0.26, 0.065, "cotton_black", 2), (0.29, 0.25, 0.07, "denim", 3), (0.27, 0.23, 0.035, "cotton_green", 2)], 421)
    lo, hi = bounds(ob)
    r1 = soft_tube("socks", [Vector((-0.05, 0, 0.0)), Vector((0.05, 0, 0.0))], 0.03, "cotton_white", segs=14, samples=4, seed=422, crease=0.003, squash=0.8)
    r1.location = (-0.05, 0.0, hi.z + 0.024)
    r2 = soft_tube("socks2", [Vector((-0.05, 0, 0.0)), Vector((0.05, 0, 0.0))], 0.03, "cotton_grey", segs=14, samples=4, seed=423, crease=0.003, squash=0.8)
    r2.location = (0.06, 0.01, hi.z + 0.024); r2.rotation_euler = (0, 0, math.radians(12))
    ob = join([ob, r1, r2], "textiles_folded_stack_c")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ SINGLE GARMENTS
@prop("tshirt_crumpled", "clutter",
      notes="Black T-shirt hung over a horizontal rail (chair back / radiator): rail axis along X at z=0.40 above the hem, front panel on -Y, "
            "sleeves hanging at the sides. Origin bottom centre of the hanging hem; place so z=0.40 lands on the chair-back top.")
def build_tshirt_crumpled():
    RAIL_Z, R = 0.40, 0.025
    nu, nv = 24, 44
    rnd = random.Random(501)
    rows = []
    for i in range(nu + 1):
        u = i / nu
        row = []
        for j in range(nv + 1):
            v = j / nv
            s = (v - 0.5) * 2                     # -1 back hem .. 0 fold .. +1 front hem
            L = abs(s) * 0.42                     # path length from the fold
            arc = R * math.pi / 2
            side = -1 if s > 0 else 1             # front is -Y
            if L < arc:
                th = L / R
                y = side * R * math.sin(th); z = RAIL_Z + R * math.cos(th)
            else:
                y = side * (R + 0.012 * (L - arc) / 0.3); z = RAIL_Z - (L - arc)
            width = 0.50 * (1 - 0.12 * smoothstep(0.0, 0.1, L)) * (1 + 0.08 * (L / 0.42) ** 2)
            x = (u - 0.5) * width
            # vertical pleats and a neck dip at the fold
            y += side * 0.012 * math.sin(x * 22 + 0.5 * side) * smoothstep(0.05, 0.3, L)
            y += side * 0.006 * math.sin(x * 55) * smoothstep(0.15, 0.4, L)
            neck = 0.07 * gauss(x, 0.07) * (1 - smoothstep(0.0, 0.08, L))
            z -= neck
            row.append(Vector((x, y, z)))
        rows.append(row)
    rows = crease_rows(rows, 0.006, 0.08, 501, 3)
    body = grid_surface("tee_body", rows, "cotton_black", thickness=0.004, offset=0.0, uv_scale=(1, 2))
    parts = [body]
    for sx in (-1, 1):
        path = [(sx * 0.24, 0.0, RAIL_Z - 0.02), (sx * 0.31, -0.01, RAIL_Z - 0.1), (sx * (0.3 + 0.03 * rnd.random()), -0.03, RAIL_Z - 0.2)]
        parts.append(soft_tube("sleeve", [Vector(p) for p in path], 0.06, "cotton_black", segs=14, samples=5, taper=lambda t: 1 - 0.1 * t,
                               caps=None, seed=502 + (sx > 0), crease=0.005, squash=1.0))
        # flatten the sleeve in Y (it hangs empty)
        parts[-1].scale = (1, 0.45, 1)
    # ribbed collar around the neck dip
    coll = [Vector((0.09 * math.cos(a), 0.045 * math.sin(a) - 0.0, RAIL_Z + R - 0.07 * gauss(0.09 * math.cos(a), 0.07) + 0.004)) for a in [2 * math.pi * k / 32 for k in range(32)]]
    parts.append(tube_curve("collar", coll, 0.005, "cotton_grey", cyclic=True, res=2))
    ob = join(parts, "textiles_tshirt_crumpled")
    set_origin_world(ob, (0, 0, 0))
    lo, hi = bounds(ob)
    set_origin_world(ob, (0, 0, lo.z))
    return ob


@prop("jeans_crumpled", "clutter", views=("front34", "top"),
      notes="Jeans stepped out of and left on the floor ~0.75x0.6x0.12: waistband ring, seat, one leg half inside-out folded back, "
            "belt loops, fly, back pockets. Origin bottom centre.")
def build_jeans_crumpled():
    parts = jeans_parts("jeans", "denim", 601,
                        legA=[(-0.09, -0.2, 0.06), (-0.2, -0.38, 0.05), (-0.16, -0.55, 0.045), (0.0, -0.6, 0.045)],
                        legB=[(0.09, -0.2, 0.06), (0.22, -0.3, 0.07), (0.26, -0.12, 0.09), (0.12, 0.0, 0.07)],
                        seat_center=(0.0, -0.08, 0.0), waist_center=(0.0, 0.06), squash=0.55)
    for p in parts:
        if p.name.startswith("jeans_waist") or p.name.startswith("jeans_loop") or p.name.startswith("jeans_fly"):
            p.location.z += 0.03
    for sx in (-1, 1):
        pk = pillow("pocket", 0.13, 0.12, 0.008, "denim", nu=6, nv=6, p=4, k=0.3, seed=602, crease=0.002)
        pk.location = (sx * 0.1, -0.1, 0.06); pk.rotation_euler = (0, 0, math.radians(sx * -8))
        parts.append(pk)
    ob = join(parts, "textiles_jeans_crumpled")
    origin_bottom_centre(ob)
    return ob


@prop("hoodie_crumpled", "clutter", views=("front34", "top"),
      notes="Grey-marl hoodie dropped on the floor ~0.75x0.7x0.14: body bunched, hood up, one sleeve folded over the body, kangaroo pocket, "
            "drawstrings, ribbed cuffs/hem. Origin bottom centre.")
def build_hoodie_crumpled():
    body = heap_base("body", 0.56, 0.5, 0.12, "cotton_marl", 701, lumps=3, crease=0.012)
    parts = [body]
    pocket = pillow("pocket", 0.30, 0.16, 0.012, "cotton_marl", nu=10, nv=6, p=4, k=0.3, seed=702, crease=0.003)
    pocket.location = (0.0, -0.13, 0.085)
    parts.append(pocket)
    parts.append(hood("hood", "cotton_marl", 703, center=(0.0, 0.3, 0.02), rot_z=0, open_=True))
    parts += sleeve("sleeve_l", [(-0.26, 0.15, 0.08), (-0.4, 0.05, 0.05), (-0.42, -0.12, 0.04), (-0.3, -0.24, 0.035)], 0.062, "cotton_marl", 704, taper_end=0.78, squash=0.65)
    parts += sleeve("sleeve_r", [(0.26, 0.15, 0.09), (0.3, 0.0, 0.14), (0.12, -0.05, 0.14), (-0.05, -0.02, 0.12)], 0.062, "cotton_marl", 705, taper_end=0.78, squash=0.75)
    hem = rim_points(0.52, 0.1, p=2.0, n=40, z=0.0)
    hemob = tube_curve("hem", [p for p in hem if p.y < 0.0], 0.007, "cotton_marl", res=2)
    hemob.location = (0.0, -0.22, 0.012)
    parts.append(hemob)
    ob = join(parts, "textiles_hoodie_crumpled")
    origin_bottom_centre(ob)
    return ob


@prop("sock_pair", "clutter", views=("front34", "top"),
      notes="Pair of white sports socks on the floor ~0.3x0.2x0.05, one half inside-out (grey heel/toe), ribbed cuffs. Origin bottom centre.")
def build_sock_pair():
    parts = []
    parts += sock("sock_a", (-0.12, -0.1), (-0.02, 0.08), "cotton_white", 801, heel_role="cotton_grey", r=0.036)
    parts += sock("sock_b", (0.12, -0.06), (0.05, 0.05), "cotton_white", 802, inside_out=True, heel_role="cotton_grey", r=0.038)
    ob = join(parts, "textiles_sock_pair")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ TOWELS
@prop("towel_crumpled", "clutter", views=("front34", "top"),
      notes="Damp bath towel dropped in a heap ~0.55x0.45x0.14 (teal terry) with a tail flopped out. Tidy partner textiles_towel_folded. Origin bottom centre.")
def build_towel_crumpled():
    heap = heap_base("towel", 0.48, 0.40, 0.11, "terry_teal", 901, lumps=4, crease=0.016, sigma=(0.26, 0.36))
    tail = pillow("tail", 0.26, 0.2, 0.03, "terry_teal", nu=10, nv=8, p=4, k=0.3, seed=902, crease=0.009, crease_scale=0.05)
    tail.location = (0.25, -0.12, 0.0); tail.rotation_euler = (0, 0, math.radians(-35))
    tail2 = pillow("tail2", 0.2, 0.3, 0.03, "terry_teal", nu=8, nv=10, p=4, k=0.3, seed=903, crease=0.009, crease_scale=0.05)
    tail2.location = (-0.2, 0.14, 0.0); tail2.rotation_euler = (0, 0, math.radians(25))
    ob = join([heap, tail, tail2], "textiles_towel_crumpled")
    noise_displace(ob, 0.0015, 0.012, 904)
    origin_bottom_centre(ob)
    return ob


@prop("towel_folded", "clutter", variant_of="towel_crumpled",
      notes="Folded white bath towel 0.36x0.26x0.07 with a blue woven stripe near the open end (-X). Fold edge +X. Messy partner textiles_towel_crumpled. Origin bottom centre.")
def build_towel_folded():
    ob = folded_item("textiles_towel_folded", 0.36, 0.26, 0.07, "terry_white", seed=911, layers=3, fuzz=0.0035)
    assign_role_by(ob, "cotton_blue", lambda c: -0.12 < c.x < -0.085 or -0.075 < c.x < -0.065)
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ LAUNDRY BASKET
def basket_parts(name):
    parts = []
    H, RB, RT = 0.48, 0.16, 0.205
    prof = lambda t: 1.0 + 0.04 * math.sin(t * math.pi)       # slight belly
    shell = wicker_basket(name + "_weave", RB, RT, H, "wicker", rows=26, stakes=24, bump=0.0045, thickness=0.007, profile=prof)
    parts.append(shell)
    # rim wrap, foot ring, base
    parts.append(tube_curve(name + "_rim", [Vector(((RT + 0.003) * math.cos(a), (RT + 0.003) * math.sin(a), H)) for a in [2 * math.pi * k / 48 for k in range(48)]], 0.011, "wicker", cyclic=True, res=3))
    parts.append(tube_curve(name + "_foot", [Vector(((RB + 0.004) * math.cos(a), (RB + 0.004) * math.sin(a), 0.008)) for a in [2 * math.pi * k / 48 for k in range(48)]], 0.008, "wicker", cyclic=True, res=3))
    base = lathe(name + "_base", [(0, 0.004), (RB - 0.004, 0.004), (RB - 0.004, 0.016), (0, 0.016)], "wicker", segments=48)
    parts.append(base)
    # vertical stakes (every other) as thin tubes for extra woven read
    for k in range(16):
        a = 2 * math.pi * k / 16 + 0.13
        pts = []
        for s in range(7):
            t = s / 6
            r = lerp(RB, RT, t) * prof(t) + 0.0065
            pts.append(Vector((r * math.cos(a), r * math.sin(a), 0.015 + t * (H - 0.03))))
        parts.append(tube_curve(name + "_stake", pts, 0.0045, "wicker", res=2))
    # two handles (woven loops) at +/-Y
    for sx in (-1, 1):
        r = RT * prof(0.9) + 0.004
        pts = []
        for s in range(11):
            t = s / 10
            a = (math.pi / 2 if sx > 0 else -math.pi / 2) - 0.42 + 0.84 * t
            bul = 0.075 * math.sin(t * math.pi) ** 0.8
            pts.append(Vector(((r + bul) * math.cos(a), (r + bul) * math.sin(a), H - 0.08 + 0.05 * math.sin(t * math.pi))))
        parts.append(tube_curve(name + "_handle", pts, 0.012, "wicker", res=3, smooth_pts=3))
    return parts


@prop("laundry_basket", "furniture", notes="Round wicker laundry basket 0.42 dia x 0.48 m, open top, two side handles at +/-Y. Rim top 0.48 m, inner base at 0.016 m. Pairs with laundry_basket_full. Origin bottom centre.")
def build_basket():
    ob = join(basket_parts("basket"), "textiles_laundry_basket")
    origin_bottom_centre(ob)
    return ob


@prop("laundry_basket_full", "furniture", variant_of="laundry_basket",
      notes="Same wicker basket overflowing: red/white/navy clothes mound above the rim (to ~0.64 m), grey sleeve hanging over the -Y side, sock over the rim. Origin bottom centre.")
def build_basket_full():
    parts = basket_parts("basket")
    mound = heap_base("mound", 0.40, 0.40, 0.22, "cotton_red", 1001, lumps=3, crease=0.012)
    mound.location = (0.0, 0.0, 0.40)
    parts.append(mound)
    t2 = pillow("tee", 0.26, 0.2, 0.05, "cotton_white", nu=10, nv=8, p=3, k=0.35, seed=1002, crease=0.01, crease_scale=0.04)
    t2.location = (0.08, 0.06, 0.55); t2.rotation_euler = (math.radians(15), math.radians(-10), math.radians(30))
    parts.append(t2)
    parts += sleeve("sleeve", [(0.0, -0.08, 0.55), (0.02, -0.19, 0.5), (0.03, -0.24, 0.38), (0.05, -0.23, 0.26)], 0.055, "cotton_navy", 1003, taper_end=0.8, squash=1.0)
    parts[-2].scale = (1, 0.6, 1)
    parts += sleeve("sock", [(-0.12, 0.14, 0.56), (-0.16, 0.18, 0.5), (-0.17, 0.2, 0.42)], 0.03, "cotton_grey", 1004, taper_end=0.85, squash=1.0, crease=0.004)
    ob = join(parts, "textiles_laundry_basket_full")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ BACKPACK
def zip_pull(name, at, direction, role="metal_dark"):
    """Zip slider + pull tab at point `at`, tab trailing along `direction`."""
    d = Vector(direction).normalized()
    parts = [box(name + "_slider", (0.009, 0.014, 0.006), role, center=at, bevel=0.001)]
    pts = [Vector(at), Vector(at) + d * 0.012 + Vector((0, 0, -0.002)), Vector(at) + d * 0.03 + Vector((0, 0, -0.006))]
    parts.append(tube_curve(name + "_pull", pts, 0.0018, role, res=2, smooth_pts=3))
    parts.append(box(name + "_tab", (0.012, 0.004, 0.02), "plastic_black", center=pts[-1] + d * 0.01 + Vector((0, 0, -0.004)), bevel=0.001))
    return parts


def backpack_parts(name, role, W=0.30, D=0.17, H=0.44, seed=0, open_mouth=False, bottle=True):
    """Rucksack built upright, front at -Y, resting on z=0."""
    parts = []
    body = grid_box(name + "_body", (W, D, H), (10, 6, 14), role, bevel=0.035, bevel_segments=4)

    def fn(co, n):
        t = co.z / H
        bul = 0.014 * math.sin(math.pi * t) * (1 - abs(n.z))
        co.x += n.x * bul; co.y += n.y * bul * 1.4
        shrink = 1 - 0.07 * smoothstep(0.6, 1.0, t)
        co.x *= shrink; co.y *= shrink
        if open_mouth and n.z > 0.6:
            co.z -= 0.09 * max(0.0, 1 - (2 * co.x / W) ** 2) ** 0.6 * max(0.0, 1 - (2 * co.y / D) ** 2) ** 0.5
        return co
    displace(body, fn)
    noise_displace(body, 0.002, 0.06, seed)
    assign_role_by(body, "rubber_black", lambda c: c.z < 0.035)
    parts.append(body)
    # front pocket
    pk = grid_box(name + "_pocket", (0.22, 0.065, 0.19), (8, 3, 6), role, center=(0, -(D / 2 + 0.022), 0.05), bevel=0.025, bevel_segments=3)
    displace(pk, lambda co, n: co + n * 0.006 * math.sin(math.pi * (co.z - 0.0) / 0.19) * (1 if n.y < -0.5 else 0))
    parts.append(pk)
    parts.append(box(name + "_logo", (0.045, 0.003, 0.028), "cotton_white", center=(0.0, -(D / 2 + 0.055), 0.11), bevel=0.001))
    # pocket zip (curved along the top of the pocket)
    pz = [Vector((-0.1 + 0.2 * k / 10, -(D / 2 + 0.045) - 0.006 * (1 - (k / 5 - 1) ** 2), 0.235 - 0.006 * (k / 5 - 1) ** 2)) for k in range(11)]
    parts.append(tube_curve(name + "_zip2", pz, 0.0035, "metal_dark", res=2))
    parts += zip_pull(name + "_pull2", pz[-1] + Vector((0, 0, 0.0)), (0.3, -0.2, -1))
    # main zip: U around the front top
    yf = -D / 2 + 0.012
    mz = [Vector((-W / 2 - 0.002, yf + 0.03, 0.24)), Vector((-W / 2 - 0.004, yf + 0.025, 0.36)), Vector((-W / 2 + 0.04, yf + 0.012, H - 0.014)),
          Vector((0.0, yf, H + 0.002)), Vector((W / 2 - 0.04, yf + 0.012, H - 0.014)), Vector((W / 2 + 0.004, yf + 0.025, 0.36)),
          Vector((W / 2 + 0.002, yf + 0.03, 0.24))]
    if open_mouth:
        # unzipped: the two zip halves gape
        za = [p + Vector((0, 0.0, 0.0)) for p in mz[:4]]
        zb = [p + Vector((0, 0.06, -0.03)) if 2 <= k <= 3 else p for k, p in enumerate(mz[3:])]
        parts.append(tube_curve(name + "_zipA", za, 0.0035, "metal_dark", res=2, smooth_pts=4))
        parts.append(tube_curve(name + "_zipB", zb, 0.0035, "metal_dark", res=2, smooth_pts=4))
        parts += zip_pull(name + "_pull1", mz[0] + Vector((0.004, 0.0, 0.0)), (0.3, 0.3, -1))
    else:
        parts.append(tube_curve(name + "_zip1", mz, 0.0035, "metal_dark", res=2, smooth_pts=4))
        parts += zip_pull(name + "_pull1", mz[3] + Vector((0.03, 0.002, -0.002)), (1, 0.2, 0))
        parts += zip_pull(name + "_pull1b", mz[3] + Vector((-0.02, 0.002, -0.002)), (-1, 0.2, 0))
    # grab handle (webbing loop) on the top towards the back
    hp = [Vector((-0.05, 0.025, H - 0.004)), Vector((-0.04, 0.03, H + 0.03)), Vector((0.0, 0.032, H + 0.042)), Vector((0.04, 0.03, H + 0.03)), Vector((0.05, 0.025, H - 0.004))]
    parts.append(strap(name + "_handle", hp, 0.022, 0.004, "nylon_navy" if role != "nylon_navy" else "cotton_black", smooth_pts=4, hint=(0, 1, 0)))
    # shoulder straps on the back (+Y): padded top part + thin webbing + ladder-lock buckle
    for sx in (-1, 1):
        pad = [Vector((sx * 0.05, D / 2 - 0.01, H - 0.06)), Vector((sx * 0.07, D / 2 + 0.012, H - 0.14)), Vector((sx * 0.1, D / 2 + 0.014, H - 0.24)),
               Vector((sx * 0.115, D / 2 + 0.01, 0.17))]
        parts.append(strap(name + "_strap_pad", pad, 0.06, 0.014, role, smooth_pts=5, hint=(0, 1, 0)))
        web = [Vector((sx * 0.115, D / 2 + 0.008, 0.17)), Vector((sx * 0.12, D / 2 + 0.006, 0.11)), Vector((sx * 0.125, D / 2 + 0.004, 0.05))]
        parts.append(strap(name + "_strap_web", web, 0.025, 0.004, "cotton_black", smooth_pts=4, hint=(0, 1, 0)))
        parts.append(box(name + "_buckle", (0.034, 0.008, 0.028), "plastic_black", center=(sx * 0.116, D / 2 + 0.01, 0.165), bevel=0.0015))
        parts.append(box(name + "_buckle_bar", (0.03, 0.004, 0.006), "plastic_black", center=(sx * 0.116, D / 2 + 0.013, 0.165), bevel=0.001))
    # side bottle pocket (+X) with a water bottle
    sp = grid_box(name + "_sidepocket", (0.075, 0.11, 0.16), (3, 4, 5), role, center=(W / 2 + 0.004, 0.0, 0.03), bevel=0.028, bevel_segments=3)
    parts.append(sp)
    if bottle:
        parts.append(cylinder(name + "_bottle", 0.033, 0.21, "plastic_blue", segments=20, center=(W / 2 + 0.012, 0.0, 0.035), bevel=0.003))
        parts.append(cylinder(name + "_bottle_neck", 0.018, 0.02, "plastic_blue", segments=16, center=(W / 2 + 0.012, 0.0, 0.245), bevel=0.001))
        parts.append(cylinder(name + "_bottle_cap", 0.021, 0.022, "plastic_black", segments=16, center=(W / 2 + 0.012, 0.0, 0.262), bevel=0.002))
    return parts


@prop("backpack_closed", "clutter",
      notes="Navy rucksack upright, zipped, straps tidy against the back (+Y), front pocket and logo on -Y, water bottle in the +X side pocket. "
            "0.37x0.24x0.49 m. Pairs with backpack_open_spilled (messy). Origin bottom centre.")
def build_backpack_closed():
    parts = backpack_parts("bag", "nylon_navy", seed=1101)
    ob = join(parts, "textiles_backpack_closed")
    origin_bottom_centre(ob)
    return ob


@prop("backpack_open_spilled", "clutter", views=("front34", "top"),
      notes="Olive rucksack lying on its left side, mouth gaping toward -X, unzipped; a blue hardback book, a cardboard notebook and a grey "
            "hoodie spill out onto the floor. ~0.85x0.45x0.3 m. Pairs with backpack_closed (tidy). Origin bottom centre.")
def build_backpack_open():
    H = 0.40
    parts = backpack_parts("bag", "nylon_olive", W=0.31, D=0.21, H=H, seed=1102, open_mouth=True, bottle=False)
    bag = join(parts, "bag")
    bag.rotation_euler = (0, math.radians(-82), math.radians(15))
    bpy.context.view_layer.update()
    rest_on_floor(bag)
    bpy.context.view_layer.update()
    lo, hi = bounds(bag)
    mx = lo.x + 0.10                 # mouth end (bbox min includes straps, so step back in)
    items = [bag]
    # hardback book half out of the mouth
    cover = box("book", (0.215, 0.15, 0.032), "plastic_blue", center=(mx - 0.02, 0.0, 0.03), bevel=0.002)
    pages = box("pages", (0.205, 0.142, 0.026), "paper_white", center=(mx - 0.02 - 0.006, 0.0, 0.03), bevel=0.001)
    for o in (cover, pages):
        o.rotation_euler = (math.radians(6), math.radians(-8), math.radians(22))
    items += [cover, pages]
    nb = box("notebook", (0.21, 0.148, 0.012), "cardboard", center=(mx - 0.2, -0.1, 0.006), bevel=0.001)
    nb.rotation_euler = (0, 0, math.radians(-35))
    items.append(nb)
    ang = math.radians(-35)
    ex, ey = math.cos(ang), math.sin(ang)          # notebook long axis
    spiral = [Vector((mx - 0.2 + s * ex - 0.074 * (-ey), -0.1 + s * ey - 0.074 * ex, 0.009)) for s in [-0.095 + 0.19 * k / 24 for k in range(25)]]
    items.append(tube_curve("spiral", spiral, 0.0035, "metal_dark", res=2))
    hd = pillow("hoodie", 0.3, 0.26, 0.09, "cotton_marl", nu=14, nv=12, p=3, k=0.4, seed=1103, crease=0.012, crease_scale=0.05)
    hd.location = (mx - 0.08, 0.12, 0.0); hd.rotation_euler = (0, 0, math.radians(40))
    items.append(hd)
    items += sleeve("hoodie_sleeve", [(mx - 0.14, 0.2, 0.05), (mx - 0.26, 0.24, 0.035), (mx - 0.34, 0.18, 0.03)], 0.055, "cotton_marl", 1104, taper_end=0.8, squash=0.55)
    ob = join(items, "textiles_backpack_open_spilled")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ TRAINERS
def mirror_x(ob):
    transform_mesh(ob, Matrix.Scale(-1, 4, Vector((1, 0, 0))))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def shoe(name, laces="tidy", upper_role="cotton_grey", sole_role="rubber_gum", mid_role="foam_white", trim_role="cotton_white", seed=0):
    """Low-top trainer, toe toward -Y, heel at +Y, resting on z=0 (right foot)."""
    L = 0.285
    NT, NS = 44, 17
    z0 = 0.03
    half_w = lambda t: scalar_keys([(0, 0.0), (0.03, 0.026), (0.1, 0.036), (0.3, 0.037), (0.5, 0.040), (0.68, 0.050), (0.82, 0.050), (0.93, 0.037), (1.0, 0.0)], t)
    xc = lambda t: -0.007 * math.sin(math.pi * t) ** 2
    ypos = lambda t: 0.1425 - t * L
    zlift = lambda t: 0.012 * smoothstep(0.78, 1.0, t) ** 1.5 + 0.005 * (1 - smoothstep(0.0, 0.12, t))
    hu = lambda t: scalar_keys([(0.5, 0.078), (0.68, 0.072), (0.8, 0.06), (0.9, 0.042), (1.0, 0.014)], t)
    hc = lambda t: scalar_keys([(0, 0.07), (0.06, 0.082), (0.2, 0.072), (0.35, 0.064), (0.55, 0.06), (0.7, 0.056)], t)
    ck = [(0.0, -1.0, 0.0), (0.1, -1.07, 0.5), (0.2, -1.0, 0.92), (0.25, -0.9, 1.0), (0.3, -0.8, 0.9), (0.38, -0.74, 0.25), (0.5, 0.0, 0.08)]
    kx = [(s, x) for s, x, z in ck]; kz = [(s, z) for s, x, z in ck]

    def channel(s, c, w, h):
        m = s <= 0.5
        ss = s if m else 1 - s
        xo = scalar_keys(kx, ss); zz = scalar_keys(kz, ss)
        return c + w * (xo if m else -xo), z0 + h * zz

    rows = []
    for i in range(NT):
        t = i / (NT - 1)
        w = half_w(t); c = xc(t); y = ypos(t); zl = zlift(t)
        heel = 1 - smoothstep(0.05, 0.16, t)                 # closed rounded heel counter
        beta = min(1.0, smoothstep(0.56, 0.74, t) + heel)
        arc_h = hu(t) if t > 0.4 else hc(t) * lerp(1.0, 0.85, heel)
        if t < 0.03:
            y -= 0.004                                       # round off the very back of the heel
        row = []
        for k in range(NS):
            s = k / (NS - 1)
            ax = c - w * 1.02 * math.cos(math.pi * s); az = z0 + arc_h * math.sin(math.pi * s) ** 0.72
            chx, chz = channel(s, c, w, hc(t))
            row.append(Vector((lerp(chx, ax, beta), y, lerp(chz, az, beta) + zl)))
        rows.append(row)
    rows = crease_rows(rows, 0.0012, 0.03, seed, 2)
    upper = grid_surface(name + "_upper", rows, upper_role, thickness=0.0035, offset=0.0, uv_scale=(1, 0.5), angle=60)
    tof = lambda y: (0.1425 - y) / L
    assign_role_by(upper, mid_role, lambda cc: tof(cc.y) > 0.88 and cc.z < z0 + 0.04)                                  # toe bumper
    assign_role_by(upper, trim_role, lambda cc: tof(cc.y) < 0.16 and cc.z < z0 + 0.055)                                # heel counter
    assign_role_by(upper, trim_role, lambda cc: 0.2 < tof(cc.y) < 0.62 and abs(cc.z - (z0 + 0.018 + 0.03 * tof(cc.y))) < 0.006 and abs(cc.x - xc(tof(cc.y))) > half_w(tof(cc.y)) * 0.8)   # side stripe
    parts = [upper]
    # sole: outline rings -> bridged, capped
    def outline(t_samples, z, flare):
        pts = []
        for t in t_samples:
            w = half_w(t) + flare; pts.append(Vector((xc(t) - w, ypos(t), z + zlift(t))))
        for t in reversed(t_samples):
            w = half_w(t) + flare; pts.append(Vector((xc(t) + w, ypos(t), z + zlift(t))))
        return pts
    ts = [i / 36 for i in range(37)]
    ts = [tt for tt in ts if 0.0 < tt < 1.0]
    r0 = outline(ts, 0.0, -0.002)
    r1 = outline(ts, 0.012, 0.004)
    r2 = outline(ts, 0.022, 0.004)
    r3 = outline(ts, z0, 0.001)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rings = [[bm.verts.new(p) for p in r] for r in (r0, r1, r2, r3)]
    n = len(r0)
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            for l in f.loops:
                l[uvl].uv = (l.vert.co.x * 4 + l.vert.co.y * 4, l.vert.co.z * 4)
    fb = bm.faces.new(list(reversed(rings[0])))
    ft = bm.faces.new(rings[-1])
    for f in (fb, ft):
        for l in f.loops:
            l[uvl].uv = (l.vert.co.x * 4, l.vert.co.y * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[fb, ft])
    sole = bsk._obj_from_bm(bm, name + "_sole", [mid_role])
    shade(sole, True, 50)
    assign_role_by(sole, sole_role, lambda cc: cc.z < 0.012 + zlift(tof(cc.y)) - 0.001)
    # outsole tread grooves (light displacement on the bottom)
    displace(sole, lambda co, nn: co + Vector((0, 0, 0.0015 * (1 if math.sin(co.y * 2 * math.pi / 0.016) > 0.3 else 0))) if nn.z < -0.8 else co)
    parts.append(sole)
    # tongue
    tz = [(0.40, z0 + 0.079), (0.5, z0 + 0.077), (0.6, z0 + 0.07), (0.7, z0 + 0.058)]
    trows = []
    for i in range(12):
        t = 0.70 - 0.30 * i / 11
        zt = scalar_keys(tz, t)
        row = []
        for k in range(7):
            x = xc(t) + (-0.026 + 0.052 * k / 6)
            row.append(Vector((x, ypos(t), zt + zlift(t) + 0.006 * (1 - (x - xc(t)) ** 2 / 0.026 ** 2) + 0.004 * (i / 11) ** 2)))
        trows.append(row)
    trows = crease_rows(trows, 0.001, 0.03, seed + 1, 2)
    tongue = grid_surface(name + "_tongue", trows, upper_role, thickness=0.006, offset=-1.0, uv_scale=(0.3, 0.3), angle=60)
    parts.append(tongue)
    parts.append(box(name + "_label", (0.02, 0.012, 0.003), trim_role, center=(xc(0.43), ypos(0.43), scalar_keys(tz, 0.43) + zlift(0.43) + 0.009), bevel=0.0005))
    # eyestays + eyelets + laces
    eye = []
    for sx in (-1, 1):
        es = []
        for k in range(5):
            t = 0.67 - 0.21 * k / 4
            x = xc(t) + sx * (0.012 + 0.02 * k / 4)
            zt = scalar_keys(tz, t) + zlift(t) + 0.004 + 0.003 * ((0.7 - t) / 0.3) ** 2
            es.append(Vector((x, ypos(t), zt)))
        parts.append(strap(name + "_eyestay", es, 0.014, 0.0025, upper_role, smooth_pts=3, hint=(0, 0, 1)))
        eye.append(es)
        for p in es[1:]:
            ring = [p + Vector((0.0036 * math.cos(a), 0.0036 * math.sin(a), 0.0025)) for a in [2 * math.pi * q / 12 for q in range(12)]]
            parts.append(tube_curve(name + "_eyelet", ring, 0.0012, "metal_dark", cyclic=True, res=2))
    lace_r = 0.0026
    lace_role = trim_role if trim_role != upper_role else "cotton_white"
    for k in range(1, 4):
        for a_side, b_side in ((0, 1), (1, 0)):
            a = eye[a_side][k]; b = eye[b_side][k + 1]
            mid = (a + b) / 2 + Vector((0, 0, 0.006))
            parts.append(tube_curve(name + "_lace", [a + Vector((0, 0, 0.003)), mid, b + Vector((0, 0, 0.003))], lace_r, lace_role, res=2, smooth_pts=4))
    # lace ends
    if laces == "tidy":
        a, b = eye[0][4], eye[1][4]
        knot = pillow(name + "_knot", 0.018, 0.014, 0.01, lace_role, nu=4, nv=4, p=3, crease=0.0)
        knot.location = ((a + b) / 2) + Vector((0, 0, 0.004))
        parts.append(knot)
        for sx, p in ((-1, a), (1, b)):
            loop = [p + Vector((0, 0, 0.003)), p + Vector((sx * 0.02, -0.01, 0.014)), p + Vector((sx * 0.03, 0.01, 0.01)), p + Vector((sx * 0.012, 0.014, 0.004)), knot.location + Vector((sx * 0.004, 0.002, 0.004))]
            parts.append(tube_curve(name + "_bowloop", loop, lace_r, lace_role, res=2, smooth_pts=4))
            tail = [knot.location + Vector((sx * 0.003, -0.002, 0.003)), p + Vector((sx * 0.008, -0.02, -0.01)), p + Vector((sx * 0.006, -0.03, -0.03))]
            parts.append(tube_curve(name + "_tail", tail, lace_r, lace_role, res=2, smooth_pts=3))
    else:
        rnd = random.Random(seed)
        for sx, p in ((-1, eye[0][4]), (1, eye[1][4])):
            w = half_w(0.44) + 0.01
            tail = [p + Vector((0, 0, 0.003)), p + Vector((sx * w * 0.6, 0.02, 0.01)), Vector((xc(0.44) + sx * (w + 0.02), p.y + 0.05, 0.03)),
                    Vector((xc(0.44) + sx * (w + 0.05 + 0.02 * rnd.random()), p.y + 0.09, 0.003)), Vector((xc(0.44) + sx * (w + 0.09), p.y + 0.06 + 0.04 * rnd.random(), 0.0025))]
            parts.append(tube_curve(name + "_tail", tail, lace_r, lace_role, res=2, smooth_pts=5))
            parts.append(cylinder(name + "_aglet", 0.003, 0.012, "plastic_black", segments=8, center=tail[-1], bevel=0.0))
    # heel pull tab
    hp = [Vector((xc(0.02) - 0.008, ypos(0.02) + 0.003, z0 + 0.07)), Vector((xc(0.02), ypos(0.02) + 0.015, z0 + 0.078)), Vector((xc(0.02) + 0.008, ypos(0.02) + 0.003, z0 + 0.07))]
    parts.append(strap(name + "_pulltab", hp, 0.012, 0.0025, trim_role, smooth_pts=3, hint=(0, 0, 1)))
    ob = join(parts, name)
    noise_displace(ob, 0.0006, 0.02, seed + 7)      # scuffs
    return ob


@prop("trainers_tidy", "clutter",
      notes="Pair of grey/white low-top trainers side by side, toes to -Y, laces tied in bows. ~0.25x0.29x0.11 m. Pairs with trainers_scattered (messy). Origin bottom centre.")
def build_trainers_tidy():
    r = shoe("shoe_R", "tidy", seed=1201)
    l = shoe("shoe_L", "tidy", seed=1202)
    mirror_x(l)
    r.location = (0.065, 0, 0); l.location = (-0.065, 0.004, 0)
    l.rotation_euler = (0, 0, math.radians(2))
    ob = join([r, l], "textiles_trainers_tidy")
    origin_bottom_centre(ob)
    return ob


@prop("trainers_scattered", "clutter", variant_of="trainers_tidy", views=("front34", "top"),
      notes="Same trainers kicked off: one upright at an angle with laces trailing on the floor, the other on its side 0.35 m away. ~0.6x0.45x0.12 m. Pairs with trainers_tidy. Origin bottom centre.")
def build_trainers_scattered():
    r = shoe("shoe_R", "undone", seed=1203)
    l = shoe("shoe_L", "undone", seed=1204)
    mirror_x(l)
    r.location = (0.12, 0.05, 0); r.rotation_euler = (0, 0, math.radians(-28))
    l.rotation_euler = (math.radians(0), math.radians(-78), math.radians(140))
    bpy.context.view_layer.update()
    rest_on_floor(l)
    l.location.x = -0.22; l.location.y = -0.08
    ob = join([r, l], "textiles_trainers_scattered")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ CURTAINS & RUG
def curtain_panel(name, x0, x1, drop, folds, seed, role="fabric_curtain"):
    nu, nv = 40, 36
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.3) for _ in range(3)]
    rows = []
    for i in range(nu + 1):
        u = i / nu
        x = x0 + (x1 - x0) * u
        row = []
        for j in range(nv + 1):
            v = j / nv
            z = drop * (1 - v)
            A = lerp(0.024, 0.045, v ** 0.8)
            y = -0.06 + A * math.sin(2 * math.pi * folds * u + ph[0] + 0.4 * v)
            y += 0.009 * math.sin(2 * math.pi * folds * 2.3 * u + ph[1]) * v
            y += 0.006 * math.sin(2 * math.pi * 1.3 * u + ph[2]) * v * v
            # heading: tight pencil pleats in the top 8 cm
            y *= lerp(0.55, 1.0, smoothstep(0.0, 0.07, v))
            # hem curl
            if v > 0.96:
                y += 0.004 * (v - 0.96) / 0.04
            row.append(Vector((x, y, z)))
        rows.append(row)
    rows = crease_rows(rows, 0.003, 0.25, seed, 2)
    ob = grid_surface(name, rows, role, thickness=0.006, offset=0.0, uv_scale=(1, 3), angle=70)
    # heading tape band + rings
    peaks = []
    for k in range(folds + 1):
        u = (k + 0.25) / folds
        if u <= 1.0:
            peaks.append(x0 + (x1 - x0) * u)
    return ob, peaks


@prop("curtain_pair", "furniture", views=("front34", "back34"),
      notes="Two burnt-orange curtains (0.54 m gathered width each, 1.5 m drop) on a 1.3 m brass rod with finials, rings and two wall brackets. "
            "Rod axis at z=1.55, y=-0.06; bracket backs touch the wall at y=0 (back = +Y). Hem at z=0 (origin bottom centre of the pair at floor "
            "level: place so the hem clears the floor / sill as wanted). Root is an empty with children rod, curtain_L, curtain_R.")
def build_curtains():
    drop = 1.5
    rod_z = drop + 0.05
    cl, pk_l = curtain_panel("curtain_L", -0.62, -0.08, drop, 6, 1301)
    cr, pk_r = curtain_panel("curtain_R", 0.08, 0.62, drop, 6, 1302)
    rod_parts = []
    rod = cylinder("rod", 0.013, 1.3, "metal_brass", segments=20, center=(0, -0.06, rod_z), bevel=0.0, origin="center")
    rod.rotation_euler = (0, math.radians(90), 0)
    rod_parts.append(rod)
    for sx in (-1, 1):
        fin = lathe("finial", [(0, 0), (0.016, 0), (0.02, 0.01), (0.012, 0.02), (0.026, 0.04), (0.03, 0.06), (0.02, 0.08), (0.0, 0.09)], "metal_brass", segments=20,
                    center=(sx * 0.65, -0.06, rod_z))
        fin.rotation_euler = (0, math.radians(sx * 90), 0)
        rod_parts.append(fin)
        rod_parts.append(box("bracket_arm", (0.02, 0.07, 0.012), "metal_brass", center=(sx * 0.56, -0.03, rod_z - 0.018), bevel=0.001))
        rod_parts.append(box("bracket_plate", (0.03, 0.006, 0.06), "metal_brass", center=(sx * 0.56, -0.003, rod_z - 0.02), bevel=0.001))
        rod_parts.append(cylinder("bracket_cup", 0.017, 0.012, "metal_brass", segments=16, center=(sx * 0.56, -0.06, rod_z - 0.024), bevel=0.0))
    for x in pk_l + pk_r:
        ring = [Vector((x, -0.06 + 0.021 * math.cos(a), rod_z + 0.021 * math.sin(a))) for a in [2 * math.pi * q / 20 for q in range(20)]]
        rod_parts.append(tube_curve("ring", ring, 0.003, "metal_brass", cyclic=True, res=2))
        rod_parts.append(tube_curve("hook", [Vector((x, -0.06, rod_z - 0.024)), Vector((x, -0.06, rod_z - 0.04)), Vector((x, -0.06, drop - 0.004))], 0.0015, "metal_steel", res=1))
    rodob = join(rod_parts, "rod")
    root = parent_all([rodob, cl, cr], "textiles_curtain_pair")
    root.location = (0, 0, 0)
    return root


@prop("rug", "furniture", views=("front34", "top"),
      notes="Worn 1.2x0.8 m flat-weave rug: beige field, rust border, navy central medallion, cream fringe at the +/-X ends, one corner (+X,+Y) "
            "curled up ~3 cm. 12 mm thick. Origin bottom centre.")
def build_rug():
    W, D = 1.2, 0.8
    nu, nv = 48, 32
    rows = []
    for i in range(nu + 1):
        u = i / nu; x = (u - 0.5) * W
        row = []
        for j in range(nv + 1):
            v = j / nv; y = (v - 0.5) * D
            z = 0.002 + 0.003 * fbm(Vector((x, y, 0)), 0.25, 2, 1401) + 0.0015 * math.sin(x * 40) * math.sin(y * 40)
            # curled corner
            dc = math.hypot(x - W / 2, y - D / 2)
            z += 0.035 * gauss(dc, 0.09) * smoothstep(0.2, 0.0, dc)
            # frayed long edges: jitter the boundary rows
            if j in (0, nv):
                y += 0.004 * fbm(Vector((x * 3, 0, 0)), 0.1, 2, 1402) * (1 if j else -1) - 0.002 * (1 if j else -1)
            if i in (0, nu):
                x += 0.004 * fbm(Vector((0, y * 3, 0)), 0.1, 2, 1403) * (1 if i else -1)
            row.append(Vector((x, y, z)))
        rows.append(row)
    rug = grid_surface("rug", rows, "fabric_pattern", thickness=0.012, offset=-1.0, uv_scale=(2.4, 1.6), angle=60)
    assign_role_by(rug, "fabric_rug_border", lambda c: abs(c.x) > W / 2 - 0.1 or abs(c.y) > D / 2 - 0.1)
    assign_role_by(rug, "cotton_navy", lambda c: abs(c.x) / 0.3 + abs(c.y) / 0.2 < 1.0 and abs(c.x) / 0.22 + abs(c.y) / 0.14 > 1.0)
    assign_role_by(rug, "fabric_rug_border", lambda c: (abs(c.x) / 0.08 + abs(c.y) / 0.055 < 1.0))
    parts = [rug]
    rnd = random.Random(1404)
    for sx in (-1, 1):
        for k in range(44):
            y = -D / 2 + 0.012 + (D - 0.024) * k / 43
            a = rnd.uniform(-0.5, 0.5); ln = rnd.uniform(0.035, 0.055)
            z = 0.004 + 0.035 * gauss(math.hypot(sx * W / 2 - W / 2, y - D / 2), 0.09) * (0.6 if sx > 0 else 0.0)
            pts = [Vector((sx * (W / 2 - 0.004), y, z + 0.004)), Vector((sx * (W / 2 + ln * 0.5), y + 0.01 * a, max(0.0025, z * 0.5 + 0.002))),
                   Vector((sx * (W / 2 + ln), y + 0.02 * a, 0.0025))]
            parts.append(tube_curve("fringe", pts, 0.0025, "cotton_white", res=1, smooth_pts=3))
    ob = join(parts, "textiles_rug")
    origin_bottom_centre(ob)
    return ob


# ================================================================================================ RUNNER
def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_manifest(entries):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=1)


def run(names, export=True, sheet=False):
    entries = load_manifest()
    pngs = []
    for name in names:
        info = BUILDERS[name]
        t0 = time.time()
        clean_scene()
        root = info["fn"]()
        full = f"{FAMILY}_{name}"
        root.name = full
        mark_sharp_by_angle(root, 38.0 if info["category"] == "furniture" else 62.0)
        tris = tri_count(root)
        lo, hi = dims_of(root)
        views = info["views"]
        outs = preview(root, full, views=views)
        pngs += outs
        if export:
            export_fbx(root, FAMILY, full)
        roles = roles_of(root)
        entry = dict(name=full, file=f"Assets/Bedsit/Art/Models/{FAMILY}/{full}.fbx", category=info["category"],
                     dims_m=[round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)], tris=tris, roles=roles,
                     variant_of=(f"{FAMILY}_{info['variant_of']}" if info["variant_of"] else None), notes=info["notes"],
                     bounds_min=[round(c, 3) for c in lo], bounds_max=[round(c, 3) for c in hi])
        entries = [e for e in entries if e["name"] != full] + [entry]
        print(f"[textiles] {full}: {tris} tris, dims {entry['dims_m']}, {time.time() - t0:.1f}s, roles {roles}")
    new_roles = sorted(NEW_ROLES.keys())
    entries = [e for e in entries if e["name"] != "_meta"]
    used = {r for e in entries for r in e.get("roles", [])}
    entries.sort(key=lambda e: ORDER.index(e["name"][len(FAMILY) + 1:]) if e["name"][len(FAMILY) + 1:] in ORDER else 999)
    entries.append({"name": "_meta", "family": FAMILY, "new_roles": {r: list(NEW_ROLES[r][0]) + [NEW_ROLES[r][1], NEW_ROLES[r][2]] for r in new_roles if r in used},
                    "origin": "bottom centre, front -Y (bed set: floor at footprint centre, headboard +Y)"})
    save_manifest(entries)
    if sheet and pngs:
        out = os.path.join(OUT_PREVIEW, f"{FAMILY}_sheet_{names[0]}.png")
        contact_sheet(pngs, out, cols=4)
        print("[textiles] sheet", out)


def bed_check():
    """Assemble frame + mattress + bedding + pillows in one scene (not exported) to verify fit."""
    for state in ("made", "messy"):
        clean_scene()
        objs = [build_bed_frame(), build_mattress()]
        if state == "made":
            objs.append(build_bedding_made())
            for k, fn in enumerate((build_pillow_made_a, build_pillow_made_b)):
                p = fn(); p.location = (-0.22 + 0.44 * k, 0.70, 0.555); p.rotation_euler = (0, 0, math.radians(-4 + 8 * k))
                objs.append(p)
        else:
            objs.append(build_bedding_messy())
            for k, fn in enumerate((build_pillow_messy_a, build_pillow_messy_b)):
                p = fn(); p.location = (-0.2 + 0.36 * k, 0.72 - 0.08 * k, 0.505 + 0.06 * k); p.rotation_euler = (0, 0, math.radians(12 - 40 * k))
                objs.append(p)
        print(preview(objs, f"{FAMILY}_bedcheck_{state}", views=("front34", "back34")))


def reimport_check(name):
    """Import an exported FBX into a fresh scene and report size / origin / facing."""
    clean_scene()
    path = os.path.join(OUT_MODELS, FAMILY, name + ".fbx")
    bpy.ops.import_scene.fbx(filepath=path)
    for o in bpy.context.scene.objects:
        if o.parent is None:
            lo, hi = dims_of(o)
            print(f"[reimport] {name}: root '{o.name}' type {o.type} loc {tuple(round(c, 4) for c in o.location)} "
                  f"rot {tuple(round(math.degrees(a), 2) for a in o.rotation_euler)} scale {tuple(round(c, 3) for c in o.scale)}")
            print(f"[reimport]   bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)} "
                  f"(origin at bottom centre -> min.z~0, x/y centred; front -Y)")
            print(preview(o, f"{FAMILY}_reimport_{name}", views=("front34",)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    export = "--noexport" not in argv
    sheet = "--sheet" in argv
    if "--bedcheck" in argv:
        bed_check()
        sys.exit(0)
    if "--reimport" in argv:
        for n in [a for a in argv if not a.startswith("--")]:
            reimport_check(n)
        sys.exit(0)
    names = [a for a in argv if not a.startswith("--")]
    if not names or names == ["all"]:
        names = ORDER
    bad = [n for n in names if n not in BUILDERS]
    if bad:
        print("unknown props:", bad, "available:", ORDER)
        sys.exit(1)
    run(names, export, sheet)
