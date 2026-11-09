"""paper - Bedsit prop kit: books, loose paper, magazines, flyers, records, stationery, cardboard boxes.

Run:  "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P Art/Source/blender/paper.py
Optional env PAPER_ONLY="name1,name2" to build a subset. Exports Assets/Bedsit/Art/Models/paper/paper_<name>.fbx,
previews Art/Source/previews/paper_<name>_<view>.png (+ paper_sheet_N.png contact sheets) and manifest_paper.json.
"""
import sys, os, math, random, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bsk; importlib.reload(bsk)
from bsk import *
import lib_paper; importlib.reload(lib_paper)
from lib_paper import *

FAMILY = "paper"
ONLY = [s.strip() for s in os.environ.get("PAPER_ONLY", "").split(",") if s.strip()]
NO_EXPORT = os.environ.get("PAPER_NO_EXPORT", "") == "1"


def rnd_of(seed):
    return random.Random(seed)


# ================================================================================================= sheets & flat stuff

def text_fn(mu=0.14, mv=0.10, skip=4, head=None, role="print_grey", ny=14):
    """Region function painting a printed text block (paragraph rows) onto a sheet, optional letterhead band."""
    def fn(u, v, x, y):
        if head and v > 1 - head[0]:
            return head[1]
        if mu < u < 1 - mu and mv < v < 1 - mv:
            row = int(v * ny)
            if skip and row % skip == 0:
                return None
            return role
        return None
    return fn


def sheet_piece(w, h, t=0.0005, role="paper_white", nx=10, ny=14, top_fn=None, curls=(), creases=(), noise_amp=0.0, seed=0,
                side_role=None, bottom_role=None):
    """Loose sheet. curls: (dir_x, dir_y, start, amount). creases: (axis, pos, width, amount) ridge lines."""
    xs = set(linspace(-w / 2, w / 2, nx + 1))
    ys = set(linspace(-h / 2, h / 2, ny + 1))
    for ax, pos, wd, amt in creases:
        for p in (pos - wd, pos, pos + wd):
            (xs if ax == 'x' else ys).add(max(-(w if ax == 'x' else h) / 2, min((w if ax == 'x' else h) / 2, p)))
    xs, ys = sorted(xs), sorted(ys)

    def zfn(x, y):
        z = 0.0
        for dx, dy, start, amt in curls:
            s = (x / (w / 2) * dx + y / (h / 2) * dy) / (abs(dx) + abs(dy))
            if s > start:
                z += amt * ((s - start) / (1 - start)) ** 2
        for ax, pos, wd, amt in creases:
            c = x if ax == 'x' else y
            z += amt * max(0.0, 1 - abs(c - pos) / wd)
        if noise_amp:
            z += noise_amp * fnoise(x, y, 0, 0.09, seed)
        return z
    pc = grid_solid(xs, ys, t, role, zfn, top_fn, side_role, bottom_role)
    return pc.normalize(centre_xy=False)


def envelope_piece(seed=0, stamp="flyer_pink"):
    rnd = rnd_of(seed)
    body = sheet_piece(0.22, 0.11, 0.0015, "envelope_white", 4, 2)
    out = Piece()
    out.add(body)
    # flap (closed) - triangle on top
    out.add(tri_prism((-0.108, 0.053), (0.108, 0.053), (0.0, -0.012), 0.0004, "envelope_white"), Tr(0, 0, 0.0015))
    # stamp + address lines
    out.add(slab(0.022, 0.026, 0.0003, stamp, 1, 1), Tr(0.085, 0.035, 0.0019))
    for i in range(3):
        out.add(slab(0.07 - i * 0.012, 0.0028, 0.0003, "print_grey", 1, 1, bevel=0), Tr(-0.02, -0.02 - i * 0.009, 0.0019))
    return out.normalize()


def folded_letter_piece(seed=0):
    """A4 letter folded in thirds, lying flat (slightly sprung open)."""
    def zfn(x, y):
        return 0.002 * max(0.0, 1 - abs(y - 0.03) / 0.015) + 0.0012 * max(0.0, (x / 0.105) ** 2 - 0.3)
    pc = slab(0.21, 0.099, 0.0022, "paper_white", 6, 4, zfn=zfn,
              top_fn=lambda u, v, x, y: "print_grey" if (0.18 < u < 0.82 and 0.15 < v < 0.3) else None)
    return pc.normalize()


def magazine_piece(cover, accent, seed=0, curl=0.0, slump=0.0, photo="print_photo"):
    rnd = rnd_of(seed)
    style = rnd.randint(0, 2)

    def art(u, v, x, y):
        if v > 0.86:
            return accent
        if 0.1 < u < 0.9 and 0.28 < v < 0.82:
            return photo
        if style == 0 and v < 0.2 and u < 0.45:
            return "print_black"
        if style == 1 and v < 0.24 and 0.55 < u:
            return accent
        if style == 2 and 0.06 < v < 0.24 and 0.1 < u < 0.9:
            return "print_grey"
        return None
    curls = []
    if curl:
        curls.append((1, 1, 0.55, curl))
    if slump:
        curls.append((1, 0, 0.25, slump))
    pc = sheet_piece(0.21, 0.28, 0.0045, cover, 8, 10, top_fn=art, curls=curls, side_role="paper_white", bottom_role=cover,
                     noise_amp=0.0004, seed=seed)
    return pc.normalize()


def flyer_piece(role, style=0, t=0.0004, curl=0.0, seed=0):
    def art(u, v, x, y):
        if style == 0 and 0.36 < v < 0.64:
            return "print_black"
        if style == 1:
            if v > 0.66:
                return "print_black"
            if 0.2 < u < 0.8 and 0.1 < v < 0.25:
                return "paper_white"
        if style == 2 and 0.2 < u < 0.8 and 0.2 < v < 0.8:
            return "print_black"
        if style == 3 and (u < 0.2 or u > 0.8 or v < 0.1 or v > 0.9):
            return "print_black"
        return None
    curls = [(1, 0, 0.5, curl)] if curl else []
    pc = sheet_piece(0.105, 0.148, t, role, 5, 6, top_fn=art, curls=curls, bottom_role="print_black" if style in (1, 3) else role, seed=seed)
    return pc.normalize()


def post_it_piece(role, curl=0.006, lines=False, t=0.0004, nx=4, ny=12):
    def art(u, v, x, y):
        if lines and 0.15 < u < 0.8 and int(v * ny) in (4, 7):
            return "ink_blue"
        return None
    pc = sheet_piece(0.076, 0.076, t, role, nx, ny, top_fn=art if lines else None, curls=[(0, -1, 0.35, curl)] if curl else [])
    return pc.normalize()


# ================================================================================================= stationery

def pen_piece(kind="bic", seed=0):
    """Writing tool built along +Z, tip at z=0."""
    if kind == "bic":
        body, cap = "plastic_clear", "plastic_blue"
        prof = [(0, 0, "metal_steel"), (0.0009, 0, "metal_steel"), (0.0012, 0.003, "metal_steel"), (0.0035, 0.012, body),
                (0.0040, 0.014, body), (0.0040, 0.095, cap), (0.0049, 0.097, cap), (0.0049, 0.140, cap), (0.0042, 0.146, cap), (0, 0.146, cap)]
        pc = lathe_piece(prof, 6)
        pc.add(box_piece(0.0025, 0.0016, 0.036, cap, 0.0004, 1), Tr(0.0052, 0, 0.104))
    elif kind == "marker":
        body, cap = "plastic_black", "plastic_black"
        prof = [(0, 0, "graphite"), (0.0025, 0.0, "graphite"), (0.0045, 0.006, "graphite"), (0.0068, 0.010, cap), (0.0078, 0.012, cap), (0.0078, 0.055, cap),
                (0.0070, 0.057, body), (0.0070, 0.130, body), (0.0060, 0.134, body), (0, 0.134, body)]
        pc = lathe_piece(prof, 14)
        pc.add(box_piece(0.003, 0.002, 0.032, cap, 0.0004, 1), Tr(0.0084, 0, 0.022))
    elif kind == "red":
        body, cap = "plastic_red", "plastic_red"
        prof = [(0, 0, "metal_steel"), (0.0009, 0, "metal_steel"), (0.0012, 0.003, "metal_steel"), (0.0036, 0.012, body),
                (0.0042, 0.014, body), (0.0042, 0.100, body), (0.0046, 0.102, cap), (0.0046, 0.142, cap), (0.0030, 0.148, cap), (0, 0.148, cap)]
        pc = lathe_piece(prof, 12)
        pc.add(box_piece(0.0025, 0.0016, 0.034, "metal_steel", 0.0004, 1), Tr(0.0049, 0, 0.108))
    elif kind == "highlighter":
        body, cap = "plastic_yellow", "plastic_grey"
        prof = [(0, 0, cap), (0.004, 0, cap), (0.0075, 0.004, cap), (0.0075, 0.040, cap), (0.0068, 0.042, body), (0.0068, 0.120, body), (0.0055, 0.125, body), (0, 0.125, body)]
        pc = lathe_piece(prof, 10)
    elif kind == "pencil":
        prof = [(0, 0, "graphite"), (0.0009, 0.003, "graphite"), (0.0018, 0.006, "wood_light"), (0.0037, 0.018, "pencil_yellow"),
                (0.0037, 0.155, "metal_steel"), (0.0041, 0.157, "metal_steel"), (0.0041, 0.166, "eraser_pink"), (0.0038, 0.167, "eraser_pink"), (0.0038, 0.173, "eraser_pink"), (0, 0.173, "eraser_pink")]
        pc = lathe_piece(prof, 6)
    else:  # plain stick pen
        body, cap = "plastic_white", "plastic_black"
        prof = [(0, 0, "metal_steel"), (0.0009, 0, "metal_steel"), (0.0014, 0.004, cap), (0.0040, 0.016, body), (0.0040, 0.105, body),
                (0.0045, 0.107, cap), (0.0045, 0.138, cap), (0.0030, 0.142, cap), (0, 0.142, cap)]
        pc = lathe_piece(prof, 8)
        pc.add(box_piece(0.0025, 0.0016, 0.030, cap, 0.0004, 1), Tr(0.0048, 0, 0.108))
    return pc


def mug_piece(outer="ceramic_blue", inner="ceramic_white"):
    prof = [(0, 0, outer), (0.032, 0, outer), (0.038, 0.002, outer), (0.040, 0.006, outer), (0.041, 0.060, outer), (0.040, 0.090, outer),
            (0.0395, 0.095, inner), (0.036, 0.0945, inner), (0.0355, 0.088, inner), (0.0345, 0.015, inner), (0.028, 0.010, inner), (0, 0.010, inner)]
    pc = lathe_piece(prof, 36)
    pts = catmull_rom([Vector(p) for p in [(0.039, 0, 0.078), (0.060, 0, 0.080), (0.070, 0, 0.060), (0.064, 0, 0.032), (0.046, 0, 0.020), (0.038, 0, 0.020)]], 5)
    pc.add(tube_piece(pts, 0.0058, outer, 10))
    return pc


def paperclip_piece():
    def arc(cx, cy, r, a0, a1, n=6):
        return [Vector((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), 0)) for a in linspace(a0, a1, n)]
    pts = [Vector((0.011, -0.0012, 0.0005))] + arc(0.026, 0.0015, 0.0027, -90, 90) + [Vector((0.004, 0.0042, 0.0))] + \
          arc(0.004, 0.0, 0.0042, 90, 270) + [Vector((0.030, -0.0042, 0.0))] + arc(0.030, 0.0, 0.0042, -90, 90) + [Vector((0.012, 0.0042, 0.0005))]
    pts = catmull_rom(pts, 3)
    return tube_piece(pts, 0.00045, "metal_steel", 6)


def spiral_coil(length, pitch, radius, wire, cx, cz, y0, turns_ppt=10):
    n = int(length / pitch * turns_ppt)
    pts = []
    for i in range(n + 1):
        th = 2 * math.pi * i / turns_ppt
        pts.append(Vector((cx + radius * math.cos(th), y0 + pitch * i / turns_ppt, cz + radius * math.sin(th))))
    return tube_piece(pts, wire, "metal_steel", 6)


def notebook_closed():
    W, H = 0.148, 0.210
    cover_t, pages_t = 0.0018, 0.012
    out = Piece()
    out.add(slab(W, H, cover_t, "book_cover_teal", 2, 2, bevel=0.0006), Tr(0.004, 0, 0))
    out.add(slab(W - 0.002, H - 0.002, pages_t, "paper_lined", 2, 2, side_role="paper_white"), Tr(0.0045, 0, cover_t))
    out.add(slab(W, H, cover_t, "book_cover_teal", 2, 2, bevel=0.0006,
                 top_fn=lambda u, v, x, y: "label_white" if (0.25 < u < 0.8 and 0.62 < v < 0.8) else None), Tr(0.004, 0, cover_t + pages_t))
    # elastic closure band
    out.add(slab(0.012, H + 0.001, cover_t * 2 + pages_t + 0.0012, "cotton_black", 1, 1), Tr(W / 2 - 0.024, 0, -0.0006))
    total = cover_t * 2 + pages_t
    out.add(spiral_coil(H - 0.016, 0.0127, 0.0105, 0.0009, -W / 2 + 0.004, total / 2, -H / 2 + 0.008))
    return out.normalize()


def notebook_open(with_pen=True):
    W, H = 0.148, 0.210
    cover_t = 0.0018
    left_t, right_t = 0.003, 0.010
    out = Piece()
    # left: front cover flipped over (outside down), few pages on top
    out.add(slab(W, H, cover_t, "book_cover_teal", 2, 2, bevel=0.0006), Tr(-W / 2 - 0.004, 0, 0))
    out.add(slab(W - 0.002, H - 0.002, left_t, "paper_lined", 2, 2, side_role="paper_white"), Tr(-W / 2 - 0.0045, 0, cover_t))
    # right: back cover + page pile
    out.add(slab(W, H, cover_t, "book_cover_teal", 2, 2, bevel=0.0006), Tr(W / 2 + 0.004, 0, 0))
    out.add(slab(W - 0.002, H - 0.002, right_t, "paper_lined", 2, 2, side_role="paper_white"), Tr(W / 2 + 0.0045, 0, cover_t))
    # ruled lines + red margin on both top pages
    for cx, zt in ((-W / 2 - 0.0045, cover_t + left_t), (W / 2 + 0.0045, cover_t + right_t)):
        n = 0
        y = H / 2 - 0.022
        while y > -H / 2 + 0.012:
            out.add(box_piece(W - 0.014, 0.0006, 0.00025, "ink_blue", 0), Tr(cx + 0.001, y, zt))
            y -= 0.008
            n += 1
        out.add(box_piece(0.0007, H - 0.016, 0.00025, "ink_red", 0), Tr(cx - W / 2 + 0.022, 0, zt))
    # handwriting scribbles on the left page (short dark dashes)
    rnd = rnd_of(3)
    y = H / 2 - 0.026
    for i in range(9):
        x0 = -W + 0.024 + rnd.uniform(0, 0.01)
        ln = rnd.uniform(0.05, 0.10)
        out.add(box_piece(ln, 0.0022, 0.0003, "print_grey", 0), Tr(x0 + ln / 2, y, cover_t + left_t))
        y -= 0.008
    out.add(spiral_coil(H - 0.016, 0.0127, 0.0085, 0.0009, 0.0, 0.0065, -H / 2 + 0.008))
    if with_pen:
        pen = pen_piece("bic")
        pen.transform(R('Y', 90))
        pen.normalize()
        out.add(pen, Tr(W / 2 + 0.01, -0.02, cover_t + right_t) @ R('Z', 28))
    return out.normalize()


def pencil_case():
    h = 0.052
    pc = box_piece(0.205, 0.075, h, "nylon_blue", 0.020, 4)
    subdivide_piece(pc, 2)
    # pillow it: wider belly, narrower zip line, slumped end, then soft wrinkles
    for v in pc.bm.verts:
        k = v.co.z / h
        v.co.x *= 1 - 0.10 * k * k
        v.co.y *= (1 - 0.22 * k * k) * (1 + 0.10 * math.sin(math.pi * k))
        v.co.z *= 1 - 0.12 * max(0.0, (v.co.x / 0.1025)) ** 2 * k
    displace(pc, lambda co: Vector((fnoise(co.x, co.y, co.z, 0.045, 4), fnoise(co.y, co.z, co.x, 0.045, 5), fnoise(co.z, co.x, co.y, 0.05, 6))) * 0.0035)
    pc.normalize()
    sz = pc.size()
    out = Piece()
    out.add(pc)
    # zip: fabric tape, metal teeth, slider + pull
    out.add(box_piece(0.19, 0.014, 0.0015, "cotton_black", 0.0004), Tr(0, 0, sz.z - 0.0006))
    out.add(box_piece(0.185, 0.0035, 0.0022, "metal_steel", 0.0004), Tr(0, 0, sz.z + 0.0006))
    out.add(box_piece(0.012, 0.007, 0.0045, "metal_steel", 0.0008), Tr(0.055, 0, sz.z + 0.0006))
    out.add(box_piece(0.022, 0.0055, 0.0015, "metal_steel", 0.0004), Tr(0.075, 0.0, sz.z + 0.002))
    return out.normalize()


def poster_roll(L=0.594, r0=0.012, r1=0.021, turns=3.3, t=0.0005, print_role="flyer_pink"):
    N = int(turns * 24)
    thmax = 2 * math.pi * turns
    pc = Piece()
    bm = pc.bm
    r_out, r_in, r_blk = pc.ri("paper_white"), pc.ri(print_role), pc.ri("print_black")
    nz = 6
    zs = linspace(0, L, nz + 1)
    rings_i, rings_o = [], []
    for z in zs:
        ri_, ro_ = [], []
        for i in range(N + 1):
            th = thmax * i / N
            r = r0 + (r1 - r0) * th / thmax
            ri_.append(bm.verts.new((r * math.cos(th), r * math.sin(th), z)))
            ro_.append(bm.verts.new(((r + t) * math.cos(th), (r + t) * math.sin(th), z)))
        rings_i.append(ri_)
        rings_o.append(ro_)
    for k in range(nz):
        for i in range(N):
            f = bm.faces.new((rings_i[k][i], rings_i[k][i + 1], rings_i[k + 1][i + 1], rings_i[k + 1][i]))
            # printed inside: blocks of black / colour so the visible end shows a printed poster
            f.material_index = r_out
            f = bm.faces.new((rings_o[k][i], rings_o[k + 1][i], rings_o[k + 1][i + 1], rings_o[k][i + 1]))
            # poster rolled print-side out: colour blocks + black text bands along the outside
            blk = ((i // 9) + k) % 3 == 0
            f.material_index = r_blk if blk else r_in
    for i in range(N):
        bm.faces.new((rings_i[0][i], rings_o[0][i], rings_o[0][i + 1], rings_i[0][i + 1])).material_index = r_out
        bm.faces.new((rings_i[-1][i], rings_i[-1][i + 1], rings_o[-1][i + 1], rings_o[-1][i])).material_index = r_out
    for idx in (0, N):
        bm.faces.new((rings_i[0][idx], rings_i[-1][idx], rings_o[-1][idx], rings_o[0][idx])).material_index = r_out
    pc.recalc()
    pc.transform(R('Y', 90))   # along X
    out = Piece()
    out.add(pc)
    # two elastic bands
    for x in (L * 0.20, L * 0.78):
        band = lathe_piece([(r1 + t + 0.0004 + 0.0012 * math.cos(a), 0.0012 * math.sin(a), "elastic_band") for a in linspace(0, 2 * math.pi, 9)], 36)
        band.transform(R('Y', 90))
        out.add(band, Tr(x, 0, 0))
    return out.normalize()


# ================================================================================================= records

def record_piece(label="vinyl_label_red", segments=48, t=0.0016):
    V = "vinyl_black"
    prof = [(0.0036, t, label), (0.051, t, V), (0.055, t, V)]
    r = 0.055
    k = 0
    while r < 0.141:
        r2 = r + 0.0095
        prof += [(r2 - 0.001, t - 0.00028, V), (r2, t, V)]
        r = r2
        k += 1
    prof += [(0.1485, t, V), (0.150, t - 0.0005, V), (0.150, 0.0005, V), (0.1485, 0.0, V), (0.051, 0.0, label), (0.0036, 0.0, V), (0.0036, t, V)]
    pc = lathe_piece(prof, segments)
    return pc.normalize()


def sleeve_piece(role, role2, style="disc", seed=0, t=0.0045, title=True, detail=8):
    rnd = rnd_of(seed)

    def art(u, v, x, y):
        if u > 0.78 and v < 0.11:
            return "label_white"
        if title and v > 0.88 and 0.08 < u < 0.7:
            return "print_black" if role not in ("sleeve_black",) else "label_white"
        if style == "band" and 0.33 < v < 0.62:
            return role2
        elif style == "quarter" and ((u < 0.5) == (v < 0.5)):
            return role2
        elif style == "frame" and 0.1 < u < 0.9 and 0.12 < v < 0.82:
            return role2
        elif style == "photo" and 0.08 < u < 0.92 and 0.08 < v < 0.84:
            return "print_photo"
        return None

    def zfn(x, y):
        d = math.hypot(x, y)
        return 0.0012 * max(0.0, 1 - (d / 0.15) ** 2)
    pc = slab(0.312, 0.312, t, role, detail, detail, zfn=zfn, top_fn=art, side_role=role, bottom_role=role, bevel=0.0007)
    if style == "disc":
        # big printed circle as a thin lathe decal following the sleeve bulge
        rr = 0.112
        prof = [(0, t + zfn(0, 0) + 0.00025, role2)]
        for r in linspace(0.02, rr, 5):
            prof.append((r, t + zfn(r, 0) + 0.00025, role2))
        prof += [(rr, t + zfn(rr, 0) - 0.0003, role2)]
        for r in reversed(linspace(0.02, rr, 5)):
            prof.append((r, t + zfn(r, 0) - 0.0003, role2))
        prof.append((0, t + zfn(0, 0) - 0.0003, role2))
        pc.add(lathe_piece(prof, 28 if detail >= 8 else 16), Tr(0, -0.006, 0))
    return pc.normalize()


SLEEVES = [("sleeve_black", "flyer_pink", "disc"), ("sleeve_white", "print_black", "band"), ("sleeve_orange", "print_black", "quarter"),
           ("sleeve_purple", "flyer_cyan", "frame"), ("sleeve_kraft", "print_black", "photo"), ("sleeve_teal", "sleeve_white", "disc"),
           ("sleeve_red", "book_band_white", "band"), ("sleeve_white", "flyer_green", "quarter"), ("sleeve_black", "book_band_gold", "frame"),
           ("sleeve_white", "print_photo", "photo"), ("sleeve_purple", "flyer_yellow", "band"), ("sleeve_teal", "print_black", "quarter")]


def record_crate():
    W, D, H = 0.37, 0.345, 0.32
    wood = "wood_light"
    out = Piece()
    post = 0.03
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.add(box_piece(post, post, H, wood, 0.002), Tr(sx * (W / 2 - post / 2), sy * (D / 2 - post / 2), 0))
    # slats: two per side, with a gap; base slats
    for zc, hgt in ((0.045, 0.11), (0.195, 0.11)):
        for sy in (-1, 1):
            out.add(box_piece(W - 2 * post, 0.012, hgt, wood, 0.0015), Tr(0, sy * (D / 2 - 0.006), zc))
        for sx in (-1, 1):
            out.add(box_piece(0.012, D - 2 * post, hgt, wood, 0.0015), Tr(sx * (W / 2 - 0.006), 0, zc))
    for i in range(4):
        out.add(box_piece(W - 2 * post, 0.07, 0.012, wood, 0.0015), Tr(0, -D / 2 + post + 0.045 + i * 0.082, 0.012))
    # records
    rnd = rnd_of(21)
    y = -D / 2 + 0.028
    i = 0
    base_z = 0.024
    while y < D / 2 - 0.03:
        role, role2, style = SLEEVES[(i * 5 + 1) % len(SLEEVES)]
        sl = sleeve_piece(role, role2, style, seed=i, title=(i % 2 == 0), detail=4)
        sl.transform(R('X', 90))
        sl.normalize()
        tilt = rnd.uniform(-7, -3)
        if i == 6:
            tilt = 24   # one flipped forward while browsing
        M = Tr(rnd.uniform(-0.004, 0.004), y, base_z) @ R('Z', rnd.uniform(-1.5, 1.5)) @ R('X', tilt)
        out.add(sl, M)
        y += 0.0115 + (0.03 if i == 6 else 0)
        i += 1
    return out.normalize()


def records_scattered():
    out = Piece()
    st = Stacker()
    poses = [(0, -0.17, 0.08, -28), (1, -0.04, -0.04, 12), (4, 0.13, 0.06, 38), (3, 0.04, 0.13, -8), (8, 0.19, -0.10, 70)]
    for k, (si, x, y, yaw) in enumerate(poses):
        role, role2, style = SLEEVES[si]
        sl = sleeve_piece(role, role2, style, seed=si)
        M = st.place(sl, x, y, yaw, ztop=0.005)
        out.add(sl, M)
        if k == 1:
            # record half-pulled out of this sleeve (open edge towards +x of the sleeve)
            rec = record_piece("vinyl_label_yellow")
            out.add(rec, M @ Tr(0.13, 0.0, 0.0012))
    rec = record_piece("vinyl_label_blue")
    out.add(rec, st.place(rec, 0.02, 0.02, 0, ztop=0.0016))
    rec = record_piece("vinyl_label_red")
    out.add(rec, st.place(rec, -0.11, -0.11, 0, ztop=0.0016))
    return out.normalize()


# ================================================================================================= cardboard

def open_box_piece(W, D, H, t, role_out, role_in, cuts=3, warp=0.0, crush=None, seed=0, bevel=0.0015):
    pc = Piece()
    bm = pc.bm
    ro, ri_ = pc.ri(role_out), pc.ri(role_in)
    V = lambda x, y, z: bm.verts.new((x, y, z))
    ox = [(-W / 2, -D / 2), (W / 2, -D / 2), (W / 2, D / 2), (-W / 2, D / 2)]
    ix = [(-W / 2 + t, -D / 2 + t), (W / 2 - t, -D / 2 + t), (W / 2 - t, D / 2 - t), (-W / 2 + t, D / 2 - t)]
    ob0 = [V(x, y, 0) for x, y in ox]
    ob1 = [V(x, y, H) for x, y in ox]
    ib0 = [V(x, y, t) for x, y in ix]
    ib1 = [V(x, y, H) for x, y in ix]
    bm.faces.new(ob0).material_index = ro
    bm.faces.new(ib0).material_index = ri_
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((ob0[i], ob0[j], ob1[j], ob1[i])).material_index = ro
        bm.faces.new((ib0[i], ib1[i], ib1[j], ib0[j])).material_index = ri_
        bm.faces.new((ob1[i], ob1[j], ib1[j], ib1[i])).material_index = ro
    pc.recalc()
    if cuts:
        subdivide_piece(pc, cuts)
    if warp:
        for v in bm.verts:
            h = max(0.0, min(1.0, v.co.z / H))
            n = fnoise(v.co.x, v.co.y, v.co.z, 0.16, seed)
            k = warp * (0.25 + 0.75 * h * h)
            if abs(abs(v.co.x) - W / 2) < t + 1e-5:
                v.co.x += math.copysign(n * k, v.co.x)
            if abs(abs(v.co.y) - D / 2) < t + 1e-5:
                v.co.y += math.copysign(fnoise(v.co.y, v.co.z, v.co.x, 0.16, seed + 3) * k, v.co.y)
    if crush:
        sx, sy, rad, depth = crush
        cp = Vector((sx * W / 2, sy * D / 2, H))
        for v in bm.verts:
            d = (v.co - cp).length
            if d < rad:
                k = (1 - d / rad) ** 2
                v.co.z -= k * depth
                v.co.x -= sx * k * depth * 0.8
                v.co.y -= sy * k * depth * 0.8
    pc.recalc()
    if bevel:
        bevel_sharp(pc, bevel, 1, 60)
    return pc


def flap_piece(L, depth, t, bow=0.004, role_out="cardboard", role_in="cardboard_dark"):
    xs = linspace(-L / 2, L / 2, 5)
    ys = linspace(0, depth, 4)
    return grid_solid(xs, ys, t, role_in, zfn=lambda x, y: bow * (y / depth) ** 2, bottom_role=role_out, side_role=role_out)


def label_piece(w=0.10, h=0.065):
    return slab(w, h, 0.0004, "label_white", 1, 7, top_fn=lambda u, v, x, y: "print_grey" if (0.12 < u < 0.85 and int(v * 7) in (1, 3)) or (u > 0.55 and int(v * 7) == 5) else None)


def cardboard_box(W, D, H, t=0.004, flaps=(112, 125, 96, 150), warp=0.003, crush=(1, 1, 0.09, 0.012), seed=0, label=True, prints=True, tape=True):
    out = Piece()
    out.add(open_box_piece(W, D, H, t, "cardboard", "cardboard_dark", 3, warp, crush, seed))
    depth = D / 2 - 0.002
    hinges = [("front", 0, -D / 2, 0, W), ("back", 0, D / 2, 180, W), ("right", W / 2, 0, 90, D), ("left", -W / 2, 0, -90, D)]
    rnd = rnd_of(seed)
    for (name, hx, hy, yaw, L), a in zip(hinges, flaps):
        fl = flap_piece(L - 0.003, depth, t, bow=rnd.uniform(0.002, 0.007))
        M = Tr(hx, hy, H) @ R('Z', yaw) @ R('X', a)
        if tape and name == "front":
            fl.add(slab(0.048, 0.11, 0.0004, "tape_brown", 1, 2), Tr(-L * 0.2, depth * 0.45, 0.0))
            fl.add(slab(0.048, 0.06, 0.0004, "tape_brown", 1, 2), Tr(L * 0.25, depth * 0.6, 0.0))
        out.add(fl, M)
    if tape:
        tp = slab(0.048, 0.09, 0.0004, "tape_brown", 1, 2)
        tp.transform(R('X', 90))
        out.add(tp, Tr(-W * 0.2, -D / 2 + 0.0002, H - 0.09))
    if label:
        lb = label_piece(min(0.10, W * 0.4), min(0.065, H * 0.4))
        lb.transform(R('X', 90))
        out.add(lb, Tr(W * 0.18, -D / 2 - 0.0002, H * 0.30))
    if prints:
        for (w_, h_, x_, z_) in ((W * 0.30, 0.016, 0.0, H * 0.62), (W * 0.18, 0.012, -W * 0.06, H * 0.55), (W * 0.22, 0.012, 0.0, H * 0.18)):
            pb = slab(h_, w_, 0.0004, "print_black", 1, 1)
            pb.transform(R('Y', 90))
            out.add(pb, Tr(W / 2 + 0.0001, 0.0 + x_, z_))
        # a "this way up" style band on the back wall
        pb = slab(W * 0.5, 0.02, 0.0004, "print_black", 1, 1)
        pb.transform(R('X', -90))
        out.add(pb, Tr(0, D / 2 + 0.0001, H * 0.7))
    return out.normalize()


def cardboard_box_flat(W=0.45, D=0.30, H=0.32):
    """A flattened RSC box lying on the floor: width = W + D (two layers), height = H + flaps."""
    fw = W + D
    fh = H
    t = 0.009
    flap = D / 2
    out = Piece()
    xs = set(linspace(-fw / 2, fw / 2, 9))
    creases_x = [-fw / 2 + W, -fw / 2 + W + D]      # vertical fold lines (panel edges)
    creases_x = [-fw / 2 + W / 2, -fw / 2 + W / 2 + D / 2, -fw / 2 + W / 2 + D / 2 + W / 2]
    for c in creases_x:
        xs.update([c - 0.0025, c + 0.0025])
    xs = sorted(xs)
    ys = set(linspace(-fh / 2, fh / 2, 5))
    ys.update([-fh / 2 + 0.002, fh / 2 - 0.002])
    ys = sorted(ys)

    def zfn(x, y):
        z = 0.0
        for c in creases_x:
            z -= 0.002 * max(0.0, 1 - abs(x - c) / 0.0025)
        z += 0.0015 * fnoise(x, y, 0, 0.2, 9)
        return z
    body = grid_solid(xs, ys, t, "cardboard", zfn, side_role="cardboard_dark")
    bmesh.ops.translate(body.bm, vec=(0, 0, t + 0.002), verts=body.bm.verts)
    out.add(body)
    # flaps top and bottom with 2 mm slits between them, slightly lifted at the free end
    panel_x = -fw / 2
    widths = [W / 2, D / 2, W / 2, D / 2]
    for w_ in widths:
        for sgn in (1, -1):
            xs_f = linspace(panel_x + 0.0015, panel_x + w_ - 0.0015, 3)
            ys_f = sorted([0.0, sgn * flap * 0.5, sgn * flap])
            fl = grid_solid(xs_f, ys_f, t, "cardboard", zfn=lambda x, y: 0.004 * (abs(y) / flap) ** 2 + 0.001 * fnoise(x, y, 1, 0.2, 10), side_role="cardboard_dark")
            bmesh.ops.translate(fl.bm, vec=(0, sgn * fh / 2, t + 0.002), verts=fl.bm.verts)
            out.add(fl)
        panel_x += w_
    # tape remnants and print
    out.add(slab(0.048, 0.16, 0.0004, "tape_brown", 1, 2), Tr(-fw / 2 + W / 2 + D / 2, fh / 2 - 0.03, t + 0.004))
    out.add(slab(0.12, 0.016, 0.0004, "print_black", 1, 1), Tr(-fw / 2 + W / 4, 0.03, t + 0.0042))
    out.add(slab(0.07, 0.012, 0.0004, "print_black", 1, 1), Tr(-fw / 2 + W / 4, 0.005, t + 0.0042))
    return out.normalize()


def shoebox():
    W, D, H = 0.33, 0.20, 0.115
    base_role, lid_role = "book_cover_navy", "book_cover_navy"
    out = Piece()
    out.add(open_box_piece(W, D, H, 0.0025, base_role, "cardboard_dark", 2, 0.0008, None, 3, 0.001))
    lid = open_box_piece(W + 0.006, D + 0.006, 0.040, 0.0025, lid_role, "cardboard_dark", 2, 0.0, None, 4, 0.001)
    lid.transform(R('X', 180))
    # brand stripe around the lid + label on the end
    for (w_, rot, pos, ends) in ((W + 0.006, R('X', 90), (0, -(D + 0.006) / 2 - 0.0002, -0.024), False), (W + 0.006, R('X', -90), (0, (D + 0.006) / 2 + 0.0002, -0.024), False),
                                 (D + 0.006, R('Y', -90), (-(W + 0.006) / 2 - 0.0002, 0, -0.024), True), (D + 0.006, R('Y', 90), ((W + 0.006) / 2 + 0.0002, 0, -0.024), True)):
        s = slab(0.014, w_ - 0.001, 0.0004, "label_white", 1, 1) if ends else slab(w_ - 0.001, 0.014, 0.0004, "label_white", 1, 1)
        s.transform(rot)
        lid.add(s, Tr(*pos))
    out.add(lid, Tr(0.009, -0.004, H + 0.0035) @ R('Z', 2.5))
    lb = label_piece(0.08, 0.05)
    lb.transform(R('Y', -90))
    out.add(lb, Tr(-W / 2 - 0.0002, 0.0, 0.03))
    return out.normalize()


# ================================================================================================= book scenes

def lean_piece(spec, tilt):
    """Standing book tilted back by `tilt` degrees (top towards +Y), normalised."""
    pc = book(spec)
    pc.transform(STAND)
    pc.normalize()
    pc.transform(R('X', -tilt))
    pc.normalize()
    return pc


def books_scattered(variant):
    """Messy pile. Items: (key, mode, x, y, yaw[, angle]). The first item is a flat book at yaw 0 that a leaning
    book rests against ('lean' items give x and tilt; y is derived so the bottom edge sits in front of the base book)."""
    out = Piece()
    st = Stacker()
    if variant == "a":
        items = [("k", "flat", -0.13, 0.03, 0), ("h", "flat", -0.10, 0.10, -25), ("n", "flat", 0.08, -0.15, 80),
                 ("g", "open_up", 0.16, 0.05, -10, 165), ("b", "tent", 0.03, 0.18, 95, 62), ("l", "splay", 0.21, -0.10, 160, 135),
                 ("o", "lean", -0.15, 0, 0, 58)]
    elif variant == "b":
        items = [("f", "flat", 0.16, 0.08, 0), ("j", "flat", 0.19, 0.12, 35), ("e", "open_up", -0.10, 0.03, 8, 170),
                 ("a", "tent", 0.18, -0.13, -70, 70), ("d", "splay", -0.20, -0.15, 20, 125), ("q", "flat", 0.0, -0.17, -85),
                 ("m", "lean", 0.15, 0, 0, 62)]
    else:
        items = [("i", "flat", -0.08, -0.06, 0), ("r", "flat", -0.11, -0.03, -15), ("c", "splay", 0.15, 0.08, 165, 150),
                 ("h", "tent", -0.20, 0.15, 30, 55), ("o", "open_up", 0.09, -0.16, 10, 160), ("b", "flat", 0.25, -0.12, -70),
                 ("g", "tent", 0.0, 0.18, -100, 80), ("q", "lean", -0.07, 0, 0, 55)]
    base = None
    for it in items:
        key, mode, x, y, yaw = it[:5]
        spec = BOOKS[key]
        if mode == "flat":
            pc = book(spec)
            M = st.place(pc, x, y, yaw)
            if base is None:
                base = (x, y, pc.size())
            out.add(pc, M)
        elif mode == "open_up":
            pc = open_book(spec, angle=it[5], face_down=False)
            out.add(pc, st.place(pc, x, y, yaw, flat=False))
        elif mode in ("tent", "splay"):
            pc = open_book(spec, angle=it[5], face_down=True)
            out.add(pc, st.place(pc, x, y, yaw, flat=False, tilt_ok=True))
        elif mode == "lean":
            tilt = it[5]
            bx, by, bsz = base
            pc = lean_piece(spec, tilt)
            sz = pc.size()
            y_bottom = by - bsz.y / 2 - bsz.z * math.tan(math.radians(tilt)) - 0.002
            out.add(pc, Tr(x, y_bottom + sz.y / 2, 0))
    return out.normalize()


def books_stacked(variant):
    keys = ["k", "i", "a", "f", "g", "h"] if variant == "a" else ["p", "e", "n", "j", "m", "d", "o"]
    rnd = rnd_of(31 if variant == "a" else 32)
    out = Piece()
    z = 0.0
    for key in keys:
        pc = book(BOOKS[key])
        pc.transform(LIE_SPINE_FRONT)
        pc.normalize()
        sz = pc.size()
        out.add(pc, Tr(rnd.uniform(-0.012, 0.012), rnd.uniform(-0.008, 0.008), z) @ R('Z', rnd.uniform(-6, 6)))
        z += sz.z
    return out.normalize()


def books_row():
    keys = ["c", "a", "g", "n", "b", "k", "r", "h", "f", "i", "j", "l", "o"]
    out = Piece()
    be_w, be_d, be_h, be_t = 0.10, 0.13, 0.17, 0.002
    x = -0.255
    # left bookend (L-bracket), books sit on its plate
    out.add(box_piece(be_w, be_d, be_t, "metal_dark", 0.0008), Tr(x + be_w / 2, 0, 0))
    out.add(box_piece(be_t, be_d, be_h, "metal_dark", 0.0008), Tr(x + be_t / 2, 0, 0))
    x += be_t + 0.001
    plate_end = x + be_w - be_t
    for i, key in enumerate(keys):
        pc = book(BOOKS[key])
        pc.transform(STAND)
        pc.normalize()
        sz = pc.size()
        lift = be_t if (x < plate_end or i >= len(keys) - 3) else 0.0
        if i == len(keys) - 1:
            # last one leans on the right bookend
            pc.transform(R('Y', -14))
            pc.normalize()
            sz = pc.size()
        out.add(pc, Tr(x + sz.x / 2, 0.0 + (0.004 if i % 3 == 1 else 0.0), lift))
        x += sz.x + 0.0008
    x += 0.001
    out.add(box_piece(be_w, be_d, be_t, "metal_dark", 0.0008), Tr(x - be_w / 2 + be_t, 0, 0))
    out.add(box_piece(be_t, be_d, be_h, "metal_dark", 0.0008), Tr(x + be_t / 2, 0, 0))
    return out.normalize()


# ================================================================================================= paper scenes

def papers_scattered(variant):
    rnd = rnd_of(41 if variant == "a" else 42)
    out = Piece()
    st = Stacker()
    n = 15 if variant == "a" else 18
    heads = ["flyer_cyan", "book_cover_red", "print_black", "flyer_orange"]
    for i in range(n):
        kind = rnd.random()
        x, y = rnd.uniform(-0.2, 0.2), rnd.uniform(-0.14, 0.14)
        yaw = rnd.uniform(-40, 40) + (90 if rnd.random() < 0.25 else 0)
        curls = []
        if rnd.random() < 0.5:
            curls.append((rnd.choice([-1, 1]), rnd.choice([-1, 0, 1]), rnd.uniform(0.3, 0.6), rnd.uniform(0.006, 0.02)))
        creases = []
        if rnd.random() < 0.3:
            creases.append(('y', rnd.uniform(-0.05, 0.05), 0.012, rnd.uniform(0.003, 0.007)))
        if kind < 0.55:
            fn = text_fn(head=(0.08, heads[i % 4]) if rnd.random() < 0.35 else None, skip=rnd.choice([3, 4, 5]))
            pc = sheet_piece(0.21, 0.297, 0.0005, "paper_white", 8, 12, top_fn=fn, curls=curls, creases=creases, noise_amp=0.0008, seed=i)
        elif kind < 0.72:
            pc = sheet_piece(0.21, 0.297, 0.0005, "paper_white", 6, 8, curls=curls, creases=creases, noise_amp=0.0008, seed=i)
        elif kind < 0.82:
            pc = sheet_piece(0.148, 0.21, 0.0005, "paper_yellow" if variant == "b" else "paper_white", 6, 8, top_fn=text_fn(mu=0.1, skip=0, role="ink_blue", ny=8), curls=curls, seed=i)
        elif kind < 0.9:
            pc = folded_letter_piece(i)
        else:
            pc = envelope_piece(i, rnd.choice(["flyer_pink", "book_cover_red", "ink_blue"]))
        out.add(pc, st.place(pc, x, y, yaw, ztop=0.0006))
    if variant == "b":
        pc = envelope_piece(99, "flyer_pink")
        out.add(pc, st.place(pc, 0.12, 0.1, -25, ztop=0.0018))
    return out.normalize()


def papers_neat():
    out = Piece()
    # manila folder underneath, with a tab
    out.add(slab(0.24, 0.32, 0.0035, "paper_manila", 2, 2, bevel=0.0006), Tr(0, 0, 0))
    out.add(slab(0.06, 0.014, 0.0035, "paper_manila", 1, 1, bevel=0.0006), Tr(0.07, 0.16 + 0.007, 0))
    # squared stack with slightly uneven edges
    stack = slab(0.21, 0.297, 0.014, "paper_white", 3, 3)
    rnd = rnd_of(7)
    for v in stack.bm.verts:
        if 0.0005 < v.co.z < 0.0135:
            v.co.x += rnd.uniform(-0.0006, 0.0006)
            v.co.y += rnd.uniform(-0.0006, 0.0006)
    out.add(stack, Tr(0, 0, 0.0035))
    top = sheet_piece(0.21, 0.297, 0.0005, "paper_white", 8, 12, top_fn=text_fn(head=(0.07, "print_black"), skip=4), noise_amp=0.0002, seed=3)
    out.add(top, Tr(0, 0, 0.0175))
    clip = paperclip_piece()
    out.add(clip, Tr(-0.095, 0.125, 0.0180) @ R('Z', 90))
    return out.normalize()


def magazines(messy):
    out = Piece()
    st = Stacker()
    specs = [("gloss_white", "gloss_red"), ("gloss_black", "flyer_yellow"), ("gloss_blue", "gloss_white")]
    if messy:
        poses = [(-0.05, -0.03, -24, 0.012, 0.0), (0.02, 0.01, 6, 0.0, 0.02), (0.09, 0.05, 31, 0.018, 0.0)]
    else:
        poses = [(0.0, 0.0, 0.0, 0.0, 0.0), (0.002, -0.001, 1.2, 0.0, 0.0), (-0.002, 0.002, -0.8, 0.0, 0.0)]
    for (cover, accent), (x, y, yaw, curl, slump) in zip(specs, poses):
        pc = magazine_piece(cover, accent, seed=hash(cover) % 100, curl=curl, slump=slump)
        out.add(pc, st.place(pc, x, y, yaw, ztop=0.0047))
    return out.normalize()


def flyers(variant):
    rnd = rnd_of({"a": 51, "b": 52, "c": 53, "single": 54}[variant])
    roles = ["flyer_pink", "flyer_green", "flyer_yellow", "flyer_cyan", "flyer_orange", "flyer_purple"]
    out = Piece()
    st = Stacker()
    n = {"a": 4, "b": 6, "c": 5, "single": 1}[variant]
    for i in range(n):
        role = roles[(i + {"a": 0, "b": 2, "c": 4, "single": 1}[variant]) % len(roles)]
        pc = flyer_piece(role, style=(i + ord(variant[0])) % 4, curl=rnd.uniform(0, 0.008) if n > 1 else 0.0, seed=i)
        if n == 1:
            out.add(pc, st.place(pc, 0, 0, 0, ztop=0.0005))
        else:
            out.add(pc, st.place(pc, rnd.uniform(-0.05, 0.05), rnd.uniform(-0.04, 0.04), rnd.uniform(-50, 50), ztop=0.0005))
    return out.normalize()


def post_it_cluster():
    out = Piece()
    st = Stacker()
    pad = slab(0.076, 0.076, 0.0085, "post_it_yellow", 2, 2)
    out.add(pad, st.place(pad, -0.06, 0.03, 8))
    top = post_it_piece("post_it_yellow", 0.004, True)
    out.add(top, Tr(-0.06, 0.03, 0.0085) @ R('Z', 8))
    notes = [("post_it_pink", 0.03, 0.05, -12, 0.007, True), ("post_it_green", 0.07, -0.02, 20, 0.010, False), ("post_it_blue", -0.01, -0.06, -30, 0.005, True),
             ("post_it_yellow", 0.09, 0.06, 45, 0.012, False), ("post_it_pink", 0.04, -0.07, 5, 0.004, True)]
    for role, x, y, yaw, curl, lines in notes:
        pc = post_it_piece(role, curl, lines)
        out.add(pc, st.place(pc, x, y, yaw, ztop=0.0005))
    return out.normalize()


def pen_cup():
    out = Piece()
    out.add(mug_piece("ceramic_blue", "ceramic_white"))
    rnd = rnd_of(61)
    kinds = ["bic", "pencil", "marker", "red", "highlighter", "pencil", "stick", "bic"]
    for i, k in enumerate(kinds):
        pen = pen_piece(k, i)
        ang = 360 * i / len(kinds) + rnd.uniform(-15, 15)
        tilt = rnd.uniform(6, 15)
        M = Tr(0.012 * math.cos(math.radians(ang)), 0.012 * math.sin(math.radians(ang)), 0.011) @ R('Z', ang) @ R('Y', tilt) @ R('Z', rnd.uniform(0, 360))
        out.add(pen, M)
    return out.normalize()


# ================================================================================================= build list

PROPS = []   # (name, builder, category, views, notes, variant_of)


def P(name, fn, cat, notes, views=("front34", "back34"), variant_of=None):
    PROPS.append((name, fn, cat, views, notes, variant_of))


for k, desc in (("a", "hardback novel, quarter-bound blue cloth / black spine, gold stamping, scuffed corners"),
                ("b", "orange paperback with white belly band (penguin style), curled cover corner"),
                ("c", "fat textbook: grey boards + white/teal dust jacket"),
                ("d", "thin manga/comic paperback, pink band"),
                ("e", "cookbook: red boards + cream dust jacket with photo block")):
    P("book_" + k, (lambda key: (lambda: Prop("paper_book_" + key).add(book(BOOKS[key]), LIE_SPINE_FRONT)))(k), "books",
      desc + ". Lying flat, front cover up, spine towards -Y (front). Top surface = total thickness (dims z).", variant_of=None if k == "a" else "book_a")
for v in "abc":
    P("books_scattered_" + v, (lambda vv: (lambda: Prop("x").add(books_scattered(vv))))(v), "books",
      "MESSY pile of 7-8 books (flat, tents face-down, splayed, open face-up, one leaning). Tidy partner: paper_books_stacked_a/_b, paper_books_row.", views=("front34", "top"),
      variant_of=None if v == "a" else "books_scattered_a")
for v in "ab":
    P("books_stacked_" + v, (lambda vv: (lambda: Prop("x").add(books_stacked(vv))))(v), "books",
      "TIDY stack of 6-7 books, spines towards -Y, slightly offset. Messy partner: paper_books_scattered_*. Top of stack = dims z (usable as a surface).",
      variant_of=None if v == "a" else "books_stacked_a")
P("books_row", lambda: Prop("x").add(books_row()), "books", "TIDY shelf row: 10 upright books between two metal L bookends, spines face -Y, last book leans. Needs shelf depth >= 0.25 m.")
P("notebook_closed", lambda: Prop("x").add(notebook_closed()), "stationery", "A5 spiral notebook, teal cover with label, elastic band, coil along -X edge. Lies flat.")
P("notebook_open", lambda: Prop("x").add(notebook_open()), "stationery", "A5 spiral notebook open flat, ruled pages with red margin, scribbles, bic pen lying across the right page. ~0.31 m wide.", views=("front34", "top"))
for v in "ab":
    P("papers_scattered_" + v, (lambda vv: (lambda: Prop("x").add(papers_scattered(vv))))(v), "paper",
      "MESSY loose A4 sheets (printed/blank/yellow notes), folded letter(s), envelope(s), curled and creased. Tidy partner: paper_papers_neat.", views=("front34", "top"),
      variant_of=None if v == "a" else "papers_scattered_a")
P("papers_neat", lambda: Prop("x").add(papers_neat()), "paper", "TIDY squared A4 stack on a manila folder, printed top sheet, paperclip. Messy partner: paper_papers_scattered_*.", views=("front34", "top"))
P("magazines_messy", lambda: Prop("x").add(magazines(True)), "paper", "MESSY: 3 glossy magazines fanned, curled corners, one slumped. Tidy partner: paper_magazines_tidy.", views=("front34", "top"))
P("magazines_tidy", lambda: Prop("x").add(magazines(False)), "paper", "TIDY: 3 glossy magazines squared in a pile. Messy partner: paper_magazines_messy.", variant_of=None)
for v in "abc":
    P("flyers_" + v, (lambda vv: (lambda: Prop("x").add(flyers(vv))))(v), "paper", "Heap of 4-6 A6 rave flyers (bright flyer_* roles, black print blocks), loose. Pairs with paper_flyer_single.",
      views=("front34", "top"), variant_of=None if v == "a" else "flyers_a")
P("flyer_single", lambda: Prop("x").add(flyers("single")), "paper", "One A6 rave flyer lying flat.", views=("front34", "top"))
for v, (role, role2, style) in zip("abc", [SLEEVES[0], SLEEVES[2], SLEEVES[3]]):
    P("vinyl_record_sleeve_" + v, (lambda r, r2, s: (lambda: Prop("x").add(sleeve_piece(r, r2, s, seed=5))))(role, role2, style), "records",
      "12 inch record sleeve lying flat, art side up, colourway %s/%s. Open edge towards +X." % (role, role2), views=("front34", "top"),
      variant_of=None if v == "a" else "vinyl_record_sleeve_a")
P("vinyl_record", lambda: Prop("x").add(record_piece("vinyl_label_red")), "records", "12 inch vinyl disc lying flat, concentric groove rings, red centre label.", views=("front34", "top"))
P("records_scattered", lambda: Prop("x").add(records_scattered()), "records", "MESSY: 5 sleeves fanned across a surface, one record half out of its sleeve, two loose discs. Tidy partner: paper_record_crate.", views=("front34", "top"))
P("record_crate", lambda: Prop("x").add(record_crate()), "records", "TIDY: wooden slat crate full of upright records (one flipped forward). Sits on the floor; front = -Y. Messy partner: paper_records_scattered.")
P("post_it_cluster", lambda: Prop("x").add(post_it_cluster()), "stationery", "Post-it pad plus 5 loose curled notes (yellow/pink/green/blue, some with ink lines) on a flat surface.", views=("front34", "top"))
P("pen_cup", lambda: Prop("x").add(pen_cup()), "stationery", "Blue mug with white interior full of pens/pencils/marker/highlighter leaning outwards. Mug top rim at 0.095 m.")
P("pencil_case", lambda: Prop("x").add(pencil_case()), "stationery", "Soft blue nylon zip pouch with metal zip, slider and pull; lies flat, zip on top.")
P("sticky_poster_roll", lambda: Prop("x").add(poster_roll()), "paper", "Rolled A2 poster (visible spiral ends show printed inside) with two elastic bands; lies along X.")
P("cardboard_box_small", lambda: Prop("x").add(cardboard_box(0.25, 0.20, 0.15, 0.004, (112, 125, 96, 150), 0.0025, (1, 1, 0.07, 0.010), 1)), "boxes",
  "Small open shipping box, flaps open, tape remnants, label on front (-Y), print bands on +X. Top rim ~0.15 m.")
P("cardboard_box_medium", lambda: Prop("x").add(cardboard_box(0.40, 0.30, 0.28, 0.0045, (105, 140, 92, 110), 0.0035, (-1, 1, 0.10, 0.016), 2)), "boxes",
  "Medium open shipping box, flaps open, crushed back-left corner, label on front (-Y). Top rim ~0.28 m.", variant_of="cardboard_box_small")
P("cardboard_box_large", lambda: Prop("x").add(cardboard_box(0.55, 0.40, 0.40, 0.005, (120, 100, 165, 95), 0.0045, (1, -1, 0.14, 0.022), 3)), "boxes",
  "Large open shipping box, one flap flopped out, crushed front-right corner. Top rim ~0.40 m.", variant_of="cardboard_box_small")
P("cardboard_box_flat", lambda: Prop("x").add(cardboard_box_flat()), "boxes", "Flattened medium box lying on the floor, crease grooves, slit flaps, tape remnant. ~0.75 x 0.62 m, 1.4 cm thick.", views=("front34", "top"))
P("shoebox", lambda: Prop("x").add(shoebox()), "boxes", "Navy shoebox with lid slightly askew, white brand stripe round the lid, end label on -X. Lid top ~0.12 m.")


# ================================================================================================= run

def main():
    clean_scene()
    manifest = []
    previews = []
    for (name, fn, cat, views, notes, variant_of) in PROPS:
        if ONLY and name not in ONLY:
            continue
        full = FAMILY + "_" + name
        print("building", full)
        prop = fn()
        prop.name = full
        ob = prop.build()
        roles = [m.name for m in ob.data.materials]
        d = dims(ob)
        tris = tri_count(ob)
        previews += preview(ob, full, views=views)
        path = export_fbx(ob, FAMILY, full) if not NO_EXPORT else ""
        manifest.append(dict(name=full, file=os.path.relpath(path, ROOT).replace("\\", "/") if path else "", category=cat, dims_m=d, tris=tris,
                             roles=roles, variant_of=(FAMILY + "_" + variant_of) if variant_of else None, notes=notes))
        print("  dims", d, "tris", tris)
        me = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    if not ONLY:
        used = sorted({r for m in manifest for r in m["roles"]})
        new_roles = {k: v for k, v in NEW_ROLES.items() if k in used}
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest_%s.json" % FAMILY), "w") as f:
            json.dump(dict(family=FAMILY, origin="bottom centre", front="-Y", new_roles=new_roles, props=manifest), f, indent=1)
    # contact sheets
    per = 12
    for i in range(0, len(previews), per):
        contact_sheet(previews[i:i + per], os.path.join(OUT_PREVIEW, "%s_sheet_%d.png" % (FAMILY, i // per + 1)), cols=4)
    print("TOTAL TRIS", sum(m["tris"] for m in manifest))


main()
