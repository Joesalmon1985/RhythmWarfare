"""lib_paper - bmesh geometry helpers for the `paper` prop family (books, sheets, records, boxes).

Everything here builds `Piece`s (a bmesh + an ordered role list, faces carry material_index into that list).
Pieces are composed into a `Prop` with 4x4 matrices and turned into one mesh object with bottom-centre origin.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, noise
import bsk
from bsk import mat, MATERIALS, shade, uv_box, OUT_PREVIEW

# ------------------------------------------------------------------------------------------------ new material roles
NEW_ROLES = {
    # paper / pages
    "paper_pages": ((0.93, 0.89, 0.78), 0.9, 0.0),         # cream page-block edges
    "paper_pages_aged": ((0.84, 0.75, 0.55), 0.9, 0.0),    # yellowed paperback pages
    "paper_lined": ((0.95, 0.95, 0.93), 0.9, 0.0),
    "paper_manila": ((0.82, 0.70, 0.45), 0.9, 0.0),
    "envelope_white": ((0.96, 0.95, 0.91), 0.85, 0.0),
    "print_grey": ((0.33, 0.33, 0.34), 0.9, 0.0),           # printed text block
    "print_black": ((0.07, 0.07, 0.08), 0.75, 0.0),
    "print_photo": ((0.40, 0.50, 0.58), 0.7, 0.0),          # photo / image block
    "ink_blue": ((0.30, 0.45, 0.75), 0.8, 0.0),
    "ink_red": ((0.80, 0.25, 0.25), 0.8, 0.0),
    # book boards (cloth) + jackets/paperback covers (printed card)
    "book_cloth_red": ((0.55, 0.12, 0.10), 0.85, 0.0),
    "book_cloth_blue": ((0.12, 0.20, 0.42), 0.85, 0.0),
    "book_cloth_green": ((0.13, 0.33, 0.22), 0.85, 0.0),
    "book_cloth_black": ((0.06, 0.06, 0.07), 0.8, 0.0),
    "book_cloth_brown": ((0.36, 0.22, 0.12), 0.75, 0.0),
    "book_cloth_grey": ((0.40, 0.40, 0.40), 0.85, 0.0),
    "book_cover_cream": ((0.90, 0.85, 0.72), 0.6, 0.0),
    "book_cover_orange": ((0.93, 0.45, 0.12), 0.5, 0.0),
    "book_cover_teal": ((0.10, 0.50, 0.52), 0.5, 0.0),
    "book_cover_purple": ((0.35, 0.15, 0.45), 0.5, 0.0),
    "book_cover_yellow": ((0.95, 0.78, 0.15), 0.5, 0.0),
    "book_cover_white": ((0.92, 0.92, 0.90), 0.4, 0.0),
    "book_cover_pink": ((0.92, 0.40, 0.60), 0.45, 0.0),
    "book_cover_navy": ((0.08, 0.12, 0.28), 0.5, 0.0),
    "book_cover_red": ((0.80, 0.12, 0.10), 0.45, 0.0),
    "book_cover_skyblue": ((0.45, 0.70, 0.90), 0.45, 0.0),
    "book_cover_green": ((0.20, 0.60, 0.35), 0.45, 0.0),
    "book_band_white": ((0.95, 0.94, 0.90), 0.6, 0.0),
    "book_band_gold": ((0.80, 0.62, 0.25), 0.4, 0.6),
    "book_band_black": ((0.05, 0.05, 0.05), 0.6, 0.0),
    "book_scuff": ((0.66, 0.60, 0.52), 0.9, 0.0),
    # sticky notes / flyers / glossy
    "post_it_yellow": ((0.98, 0.90, 0.30), 0.9, 0.0),
    "post_it_pink": ((0.98, 0.55, 0.70), 0.9, 0.0),
    "post_it_green": ((0.60, 0.95, 0.45), 0.9, 0.0),
    "post_it_blue": ((0.45, 0.80, 0.98), 0.9, 0.0),
    "flyer_pink": ((0.98, 0.15, 0.60), 0.5, 0.0),
    "flyer_green": ((0.25, 0.95, 0.35), 0.5, 0.0),
    "flyer_yellow": ((0.98, 0.92, 0.10), 0.5, 0.0),
    "flyer_cyan": ((0.10, 0.85, 0.95), 0.5, 0.0),
    "flyer_orange": ((0.98, 0.50, 0.08), 0.5, 0.0),
    "flyer_purple": ((0.55, 0.15, 0.90), 0.5, 0.0),
    "gloss_white": ((0.95, 0.95, 0.93), 0.25, 0.0),
    "gloss_red": ((0.85, 0.10, 0.12), 0.25, 0.0),
    "gloss_blue": ((0.12, 0.35, 0.80), 0.25, 0.0),
    "gloss_black": ((0.05, 0.05, 0.06), 0.25, 0.0),
    # records
    "vinyl_black": ((0.02, 0.02, 0.022), 0.3, 0.0),
    "vinyl_label_red": ((0.80, 0.15, 0.12), 0.6, 0.0),
    "vinyl_label_yellow": ((0.92, 0.78, 0.20), 0.6, 0.0),
    "vinyl_label_blue": ((0.15, 0.30, 0.70), 0.6, 0.0),
    "vinyl_label_white": ((0.92, 0.92, 0.88), 0.6, 0.0),
    "sleeve_black": ((0.07, 0.07, 0.08), 0.55, 0.0),
    "sleeve_white": ((0.92, 0.91, 0.87), 0.55, 0.0),
    "sleeve_orange": ((0.95, 0.50, 0.10), 0.5, 0.0),
    "sleeve_purple": ((0.40, 0.12, 0.50), 0.5, 0.0),
    "sleeve_kraft": ((0.68, 0.55, 0.38), 0.8, 0.0),
    "sleeve_teal": ((0.10, 0.55, 0.55), 0.5, 0.0),
    "sleeve_red": ((0.75, 0.10, 0.12), 0.5, 0.0),
    # packaging / stationery
    "tape_brown": ((0.55, 0.35, 0.15), 0.3, 0.0),
    "label_white": ((0.95, 0.95, 0.93), 0.7, 0.0),
    "cardboard_dark": ((0.47, 0.34, 0.19), 0.9, 0.0),
    "pencil_yellow": ((0.92, 0.68, 0.10), 0.5, 0.0),
    "graphite": ((0.15, 0.15, 0.16), 0.5, 0.2),
    "eraser_pink": ((0.95, 0.60, 0.65), 0.8, 0.0),
    "elastic_band": ((0.72, 0.62, 0.50), 0.9, 0.0),
    "nylon_blue": ((0.15, 0.25, 0.50), 0.9, 0.0),
    "plastic_yellow": ((0.95, 0.85, 0.10), 0.4, 0.0),
    "plastic_clear": ((0.80, 0.85, 0.85), 0.2, 0.0),
}
for _k, _v in NEW_ROLES.items():
    MATERIALS.setdefault(_k, _v)

# ------------------------------------------------------------------------------------------------ small maths
I4 = Matrix.Identity(4)


def Tr(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def S(x, y, z):
    return Matrix.Diagonal((x, y, z, 1.0))


# lying frame (x = cover width, spine at -x; y = book height, head at +y; z = thickness, front cover up)
# -> standing on a shelf: spine faces -Y, head up (+Z), thickness along X.
STAND = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
# lying with the spine towards the viewer (-Y), head to -X
LIE_SPINE_FRONT = R('Z', 90)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def fnoise(x, y, z, scale, seed):
    return noise.noise(Vector((x / scale + seed * 17.3, y / scale + seed * 7.1, z / scale + seed * 3.9)))


def dedupe(path, eps=1e-7):
    out = []
    for p in path:
        if not out or (abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps):
            out.append(p)
    if len(out) > 2 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


# ------------------------------------------------------------------------------------------------ Piece / Prop

class Piece:
    def __init__(self):
        self.bm = bmesh.new()
        self.roles = []

    def ri(self, role):
        if role not in self.roles:
            self.roles.append(role)
        return self.roles.index(role)

    def transform(self, M):
        bmesh.ops.transform(self.bm, matrix=M, verts=self.bm.verts)
        if M.determinant() < 0:
            bmesh.ops.reverse_faces(self.bm, faces=self.bm.faces)
        return self

    def copy(self):
        p = Piece()
        p.roles = list(self.roles)
        p.bm = self.bm.copy()
        return p

    def bounds(self):
        vs = self.bm.verts
        lo = Vector((min(v.co.x for v in vs), min(v.co.y for v in vs), min(v.co.z for v in vs)))
        hi = Vector((max(v.co.x for v in vs), max(v.co.y for v in vs), max(v.co.z for v in vs)))
        return lo, hi

    def size(self):
        lo, hi = self.bounds()
        return hi - lo

    def normalize(self, bottom=True, centre_xy=True):
        """Translate so bbox bottom is z=0 and the xy-centre is at the origin."""
        lo, hi = self.bounds()
        off = Vector(((lo.x + hi.x) / 2 if centre_xy else 0, (lo.y + hi.y) / 2 if centre_xy else 0, lo.z if bottom else 0))
        bmesh.ops.translate(self.bm, vec=-off, verts=self.bm.verts)
        return self

    def add(self, other, M=None):
        """Merge another piece (consumed) into this one."""
        remap = [self.ri(r) for r in other.roles] or [self.ri("paper_white")]
        for f in other.bm.faces:
            f.material_index = remap[min(f.material_index, len(remap) - 1)]
        if M is not None:
            other.transform(M)
        me = bpy.data.meshes.new("_tmp")
        other.bm.to_mesh(me)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        other.bm.free()
        return self

    def recalc(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        return self

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)


def merge(parts):
    """parts: list of (Piece, Matrix|None) -> one Piece."""
    out = Piece()
    for pc, M in parts:
        out.add(pc, M)
    return out


class Prop:
    def __init__(self, name):
        self.name = name
        self.piece = Piece()

    def add(self, piece, M=None):
        self.piece.add(piece, M)
        return self

    def build(self, smooth_angle=40, uv_scale=1.0, origin_bottom=True):
        pc = self.piece
        if origin_bottom:
            pc.normalize()
        me = bpy.data.meshes.new(self.name)
        pc.bm.to_mesh(me)
        pc.bm.free()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        for r in pc.roles:
            me.materials.append(mat(r))
        shade(ob, True, smooth_angle)
        uv_box(ob, uv_scale)
        return ob


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def dims(ob):
    lo, hi = bsk.bounds(ob)
    d = hi - lo
    return [round(d.x, 4), round(d.y, 4), round(d.z, 4)]


# ------------------------------------------------------------------------------------------------ primitive builders

def bevel_sharp(pc, width, segments=2, angle=50, clamp=True):
    bm = pc.bm
    bm.normal_update()
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle)]
    if edges and width > 0:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', segments=segments, profile=0.7,
                        affect='EDGES', clamp_overlap=clamp, material=-1)
    return pc


def box_piece(w, d, h, role, bevel=0.003, segments=2, centre_z=False):
    pc = Piece()
    bm = pc.bm
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= w
        v.co.y *= d
        v.co.z *= h
        if not centre_z:
            v.co.z += h / 2
    r = pc.ri(role)
    for f in bm.faces:
        f.material_index = r
    if bevel > 0:
        bevel_sharp(pc, bevel, segments)
    return pc.recalc()


def grid_solid(xs, ys, t, role, zfn=None, top_role_fn=None, side_role=None, bottom_role=None, bevel=0.0):
    """Thin solid slab/sheet. xs, ys = coordinate lists; zfn(x,y)->z of top surface; t = thickness (down).
    top_role_fn(u,v,x,y)->role for the top faces (u,v in 0..1)."""
    pc = Piece()
    bm = pc.bm
    nx, ny = len(xs), len(ys)
    top = [[bm.verts.new((x, y, zfn(x, y) if zfn else 0.0)) for x in xs] for y in ys]
    bot = [[bm.verts.new((x, y, top[j][i].co.z - t)) for i, x in enumerate(xs)] for j, y in enumerate(ys)]
    x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
    ri_base = pc.ri(role)
    ri_bot = pc.ri(bottom_role) if bottom_role else ri_base
    ri_side = pc.ri(side_role) if side_role else ri_base
    for j in range(ny - 1):
        for i in range(nx - 1):
            f = bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            if top_role_fn:
                xm = (xs[i] + xs[i + 1]) / 2
                ym = (ys[j] + ys[j + 1]) / 2
                rr = top_role_fn((xm - x0) / (x1 - x0), (ym - y0) / (y1 - y0), xm, ym)
                f.material_index = pc.ri(rr) if rr else ri_base
            else:
                f.material_index = ri_base
            fb = bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
            fb.material_index = ri_bot
    for i in range(nx - 1):
        f = bm.faces.new((top[0][i], bot[0][i], bot[0][i + 1], top[0][i + 1]))
        f.material_index = ri_side
        f = bm.faces.new((top[ny - 1][i], top[ny - 1][i + 1], bot[ny - 1][i + 1], bot[ny - 1][i]))
        f.material_index = ri_side
    for j in range(ny - 1):
        f = bm.faces.new((top[j][0], top[j + 1][0], bot[j + 1][0], bot[j][0]))
        f.material_index = ri_side
        f = bm.faces.new((top[j][nx - 1], bot[j][nx - 1], bot[j + 1][nx - 1], top[j + 1][nx - 1]))
        f.material_index = ri_side
    pc.recalc()
    if bevel > 0:
        bevel_sharp(pc, bevel, 1, 50)
    return pc


def linspace(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def slab(w, d, t, role, nx=2, ny=2, zfn=None, top_fn=None, side_role=None, bottom_role=None, bevel=0.0, centre=True):
    xs = linspace(-w / 2 if centre else 0, w / 2 if centre else w, nx + 1)
    ys = linspace(-d / 2 if centre else 0, d / 2 if centre else d, ny + 1)
    pc = grid_solid(xs, ys, t, role, zfn, top_fn, side_role, bottom_role, bevel)
    bmesh.ops.translate(pc.bm, vec=(0, 0, t), verts=pc.bm.verts)   # bottom at z=0 (before zfn offsets)
    return pc


def sweep(path, ys, role_fn, cap_role, close_path=True, caps=True):
    """Extrude a closed 2D profile (list of (x, z, tag)) along Y through the sorted positions `ys`.
    role_fn(p0, p1, y0, y1) -> role of the quad between profile points p0,p1 on segment [y0,y1]."""
    pts = dedupe(path)
    pc = Piece()
    bm = pc.bm
    n = len(pts)
    rings = [[bm.verts.new((p[0], y, p[1])) for p in pts] for y in ys]
    ne = n if close_path else n - 1
    for k in range(len(ys) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(ne):
            j = (i + 1) % n
            try:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError:
                continue
            f.material_index = pc.ri(role_fn(pts[i], pts[j], ys[k], ys[k + 1]))
    if caps and close_path:
        cf = []
        for ring in (rings[0], rings[-1]):
            try:
                f = bm.faces.new(ring)
                f.material_index = pc.ri(cap_role)
                cf.append(f)
            except ValueError:
                pass
        if cf:
            bmesh.ops.triangulate(bm, faces=cf, quad_method='BEAUTY', ngon_method='EAR_CLIP')
    return pc.recalc()


def lathe_piece(profile, segments=32, cap_role=None):
    """Surface of revolution about Z. profile = [(r, z, role), ...]; faces between entry i and i+1 use role i.
    r == 0 closes the end with a pole vertex."""
    pc = Piece()
    bm = pc.bm
    rings = []
    for (r, z, role) in profile:
        if r <= 1e-7:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments), z))
                          for i in range(segments)])
    for k in range(len(profile) - 1):
        a, b = rings[k], rings[k + 1]
        ri = pc.ri(profile[k][2])
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1 and len(b) == 1:
                continue
            try:
                if len(a) == 1:
                    f = bm.faces.new((a[0], b[j], b[i]))
                elif len(b) == 1:
                    f = bm.faces.new((a[i], a[j], b[0]))
                else:
                    f = bm.faces.new((a[i], a[j], b[j], b[i]))
                f.material_index = ri
            except ValueError:
                pass
    return pc.recalc()


def tube_piece(points, radius, role, segs=6, closed=False, caps=True):
    """Mesh tube following a polyline of Vector points (parallel-transport frames)."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    pc = Piece()
    bm = pc.bm
    ri = pc.ri(role)
    tans = []
    for i in range(n):
        if closed:
            t = pts[(i + 1) % n] - pts[i - 1]
        else:
            t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    t0 = tans[0]
    up = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    nrm = (up - t0 * up.dot(t0)).normalized()
    rings = []
    angs = [2 * math.pi * k / segs for k in range(segs)]
    for i in range(n):
        if i > 0:
            nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
        bn = tans[i].cross(nrm)
        rings.append([bm.verts.new(pts[i] + (nrm * math.cos(a) + bn * math.sin(a)) * radius) for a in angs])
    m = n if closed else n - 1
    for i in range(m):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            l = (k + 1) % segs
            f = bm.faces.new((a[k], a[l], b[l], b[k]))
            f.material_index = ri
    if caps and not closed:
        for ring in (rings[0], list(reversed(rings[-1]))):
            f = bm.faces.new(ring)
            f.material_index = ri
    return pc.recalc()


def catmull_rom(points, samples_per_seg=6, closed=False):
    """Smooth a control polyline (list of Vector)."""
    P = [Vector(p) for p in points]
    n = len(P)
    out = []
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = P[(i - 1) % n] if closed else P[max(i - 1, 0)]
        p1 = P[i]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed else P[min(i + 2, n - 1)]
        for k in range(samples_per_seg):
            t = k / samples_per_seg
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    if not closed:
        out.append(P[-1])
    return out


def tri_prism(p0, p1, p2, t, role):
    """Flat triangular solid (top at z=t, bottom at z=0). p* are (x, y)."""
    pc = Piece()
    bm = pc.bm
    ri = pc.ri(role)
    top = [bm.verts.new((p[0], p[1], t)) for p in (p0, p1, p2)]
    bot = [bm.verts.new((p[0], p[1], 0.0)) for p in (p0, p1, p2)]
    bm.faces.new(top).material_index = ri
    bm.faces.new(list(reversed(bot))).material_index = ri
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((top[i], bot[i], bot[j], top[j])).material_index = ri
    return pc.recalc()


def displace(pc, fn):
    """fn(co: Vector) -> Vector offset."""
    for v in pc.bm.verts:
        v.co += fn(v.co)
    return pc


def subdivide_piece(pc, cuts=1):
    bmesh.ops.subdivide_edges(pc.bm, edges=pc.bm.edges[:], cuts=cuts, use_grid_fill=True)
    return pc


# ------------------------------------------------------------------------------------------------ BOOKS
# spec keys: W (cover width), H (height), T (page block thickness), kind 'hard'|'paper', cover, spine, pages,
#   endpaper, bands=[{y0,y1,role,where:'all'|'spine'|'front'}], labels=[{x0,x1,y0,y1,role}] (lying-frame coords),
#   scuffs=['fh','ff','bh','bf'], jacket={cover,spine,bands,labels}, seed

def _cover_path(W, Tt, bt, bulge, groove, xsplits):
    xa = -W / 2 + bulge
    xs_top = sorted([x for x in xsplits if xa + 0.006 < x < W / 2 - 0.0005], reverse=True)
    pts = [(W / 2, Tt, 'top')] + [(x, Tt, 'top') for x in xs_top]
    if groove > 0:
        pts += [(xa + 0.0045, Tt, 'top'), (xa + 0.0028, Tt - groove, 'top'), (xa + 0.0012, Tt, 'top')]
    n_arc = 10
    for i in range(n_arc + 1):
        t = math.pi * i / n_arc
        pts.append((xa - bulge * math.sin(t), Tt / 2 + Tt / 2 * math.cos(t), 'spine'))
    if groove > 0:
        pts += [(xa + 0.0012, 0.0, 'bot'), (xa + 0.0028, groove, 'bot'), (xa + 0.0045, 0.0, 'bot')]
    pts += [(x, 0.0, 'bot') for x in sorted(xs_top)] + [(W / 2, 0.0, 'bot')]
    pts += [(W / 2, bt, 'fore')]
    ib = max(bulge - bt, 0.0002)
    for i in range(n_arc + 1):
        t = math.pi * (n_arc - i) / n_arc
        pts.append((xa - ib * math.sin(t), Tt / 2 + (Tt / 2 - bt) * math.cos(t), 'inner'))
    pts += [(W / 2, Tt - bt, 'inner'), (W / 2, Tt, 'fore')]
    return pts


def _cover_role_fn(sub, W, H, Tt, scuff_size, default_endpaper):
    cover = sub['cover']
    spine_role = sub.get('spine', cover)
    bands = sub.get('bands', [])
    labels = sub.get('labels', [])
    scuffs = sub.get('scuffs', [])
    endpaper = sub.get('endpaper', default_endpaper)

    def in_corner(code, xm, ym):
        if xm < W / 2 - scuff_size:
            return False
        return (ym > H / 2 - scuff_size) if 'h' in code else (ym < -H / 2 + scuff_size)

    def fn(p0, p1, y0, y1):
        xm = (p0[0] + p1[0]) / 2
        ym = (y0 + y1) / 2
        tag = p0[2] if p0[2] == p1[2] else p0[2]
        if tag == 'inner':
            return endpaper
        if tag == 'spine':
            for b in bands:
                if b.get('where', 'all') in ('all', 'spine') and b['y0'] <= ym <= b['y1']:
                    return b['role']
            return spine_role
        if tag == 'top':
            for lab in labels:
                if lab['x0'] <= xm <= lab['x1'] and lab['y0'] <= ym <= lab['y1']:
                    return lab['role']
        if tag in ('top', 'bot', 'fore'):
            for c in scuffs:
                if ((c[0] == 'f' and tag in ('top', 'fore')) or (c[0] == 'b' and tag in ('bot', 'fore'))) and in_corner(c, xm if tag != 'fore' else W / 2, ym):
                    return 'book_scuff'
            for b in bands:
                w = b.get('where', 'all')
                if (w == 'all' or (w == 'front' and tag == 'top')) and b['y0'] <= ym <= b['y1']:
                    return b['role']
        return cover
    return fn


def _splits(sub, W, H, scuff_size):
    xsplits, ysplits = set(), {-H / 2, H / 2}
    for lab in sub.get('labels', []):
        xsplits.update([lab['x0'], lab['x1']])
        ysplits.update([lab['y0'], lab['y1']])
    for b in sub.get('bands', []):
        ysplits.update([b['y0'], b['y1']])
    for c in sub.get('scuffs', []):
        xsplits.add(W / 2 - scuff_size)
        ysplits.add(H / 2 - scuff_size if 'h' in c else -H / 2 + scuff_size)
    ys = sorted(y for y in ysplits if -H / 2 - 1e-9 <= y <= H / 2 + 1e-9)
    return xsplits, ys


def _page_block(W, H, T, hard, bt, o, xa, pages_role, seed, z0=None, flush_inset=0.0003):
    rnd = random.Random(seed)
    px0 = xa + (0.0018 if hard else 0.0008)
    px1 = W / 2 - o - (0.0006 if hard else flush_inset)
    pz0 = (z0 if z0 is not None else bt) + 0.00015
    pz1 = pz0 + T - 0.0003
    prof = [(px0, pz0, 'pg'), (px1, pz0, 'pg'), (px1, pz1, 'fore'), (px0, pz1, 'pg')]
    hy = H / 2 - o - (0.0 if hard else flush_inset)
    ys = linspace(-hy, hy, 7)
    pc = sweep(prof, ys, lambda a, b, y0, y1: pages_role, pages_role)
    # uneven fore-edge / head / foot so the block reads as many pages
    amp = 0.0006 if hard else 0.0005
    for v in pc.bm.verts:
        if abs(v.co.x - px1) < 1e-6:
            v.co.x += rnd.uniform(-amp, 0.0 if not hard else amp * 0.4)
        if abs(abs(v.co.y) - hy) < 1e-6:
            v.co.y -= math.copysign(rnd.uniform(0, amp * 0.7), v.co.y)
    return pc


def book(spec):
    """Closed book in the lying frame, normalised (bottom z=0, xy centred). Returns Piece."""
    W, H, T = spec['W'], spec['H'], spec['T']
    hard = spec.get('kind', 'hard') == 'hard'
    bt = spec.get('board_t', 0.0025 if hard else 0.0006)
    o = spec.get('overhang', 0.0035 if hard else 0.0)
    Tt = T + 2 * bt
    bulge = spec.get('bulge', min(0.0055, Tt * 0.3) if hard else 0.0006)
    groove = 0.0009 if hard else 0.0
    xa = -W / 2 + bulge
    pages_role = spec.get('pages', 'paper_pages')
    scuff = spec.get('scuff_size', 0.012)
    out = Piece()
    xsplits, ys = _splits(spec, W, H, scuff)
    path = _cover_path(W, Tt, bt, bulge, groove, xsplits)
    fn = _cover_role_fn(spec, W, H, Tt, scuff, 'paper_pages' if hard else spec['cover'])
    out.add(sweep(path, ys, fn, spec['cover']))
    out.add(_page_block(W, H, T, hard, bt, o, xa, pages_role, spec.get('seed', 0)))
    jk = spec.get('jacket')
    if jk:
        d = 0.00045
        jx, jys = _splits(jk, W + 2 * d, H - 0.0026, scuff)
        jpath = _cover_path(W + 2 * d, Tt + 2 * d, d * 0.85, bulge + d, 0.0, jx)
        jfn = _cover_role_fn(jk, W + 2 * d, H - 0.0026, Tt + 2 * d, scuff, jk.get('endpaper', jk['cover']))
        out.add(sweep(jpath, jys, jfn, jk['cover']), Tr(0, 0, -d))
    if not hard and spec.get('curl', 0) > 0:
        # paperback cover corner curl: lift front-cover fore-edge corner verts a little
        c = spec['curl']
        for v in out.bm.verts:
            if v.co.z > Tt - bt - 1e-5 and v.co.x > W / 2 - 0.03 and v.co.y > H / 2 - 0.04:
                k = smoothstep((v.co.x - (W / 2 - 0.03)) / 0.03) * smoothstep((v.co.y - (H / 2 - 0.04)) / 0.04)
                v.co.z += c * k
    return out.normalize()


def open_book(spec, angle=160, face_down=False, front_half='left'):
    """Open book: two halves hinged at the spine (along Y). angle = angle between covers (180 = flat).
    face_down=True flips it so the covers face up (dropped open on its face). Returns normalised Piece."""
    W, H, T = spec['W'], spec['H'], spec['T']
    hard = spec.get('kind', 'hard') == 'hard'
    bt = spec.get('board_t', 0.0025 if hard else 0.0006)
    o = spec.get('overhang', 0.0035 if hard else 0.0)
    Tt = T + 2 * bt
    pages_role = spec.get('pages', 'paper_pages')
    sub = spec.get('jacket', spec)   # the visible outside is the jacket if there is one
    cover = sub['cover']
    spine_role = sub.get('spine', cover)
    bands = sub.get('bands', [])
    labels = sub.get('labels', [])
    endpaper = spec.get('endpaper', 'paper_pages' if hard else cover)
    phi = (180.0 - angle) / 2.0
    g = Tt * 0.32          # half gap between hinge lines
    Th = T / 2 - 0.0004
    curl = (not face_down)
    out = Piece()

    def board_fn(is_front):
        def fn(p0, p1, y0, y1):
            tag = p0[2]
            ym = (y0 + y1) / 2
            xm = (p0[0] + p1[0]) / 2 - W / 2     # to lying-frame x
            if tag == 'in':
                return endpaper
            if tag == 'out' and is_front:
                for lab in labels:
                    if lab['x0'] <= xm <= lab['x1'] and lab['y0'] <= ym <= lab['y1']:
                        return lab['role']
            if tag in ('out', 'fore'):
                for b in bands:
                    w = b.get('where', 'all')
                    if (w == 'all' or (w == 'front' and is_front)) and b['y0'] <= ym <= b['y1']:
                        return b['role']
            return cover
        return fn

    ysplit = {-H / 2, H / 2}
    for b in bands:
        ysplit.update([b['y0'], b['y1']])
    for lab in labels:
        ysplit.update([lab['y0'], lab['y1']])
    ys = sorted(y for y in ysplit if -H / 2 <= y <= H / 2)
    xsp = set()
    for lab in labels:
        xsp.update([lab['x0'] + W / 2, lab['x1'] + W / 2])
    xs_top = sorted(x for x in xsp if 0.002 < x < W - 0.002)
    board_path = [(0.0, 0.0, 'out')] + [(x, 0.0, 'out') for x in xs_top] + [(W, 0.0, 'fore'), (W, bt, 'in'), (0.0, bt, 'hinge')]
    # page half: curved top
    px0, px1 = 0.0015, W - o - 0.0006
    pm = spec.get('page_margin', 0.016)
    nx = 12
    xs_pg = sorted(set([px0 + (px1 - px0) * i / nx for i in range(nx + 1)] + [px0 + pm, px1 - pm]))

    def ztop(x):
        if not curl:
            return bt + 0.0002 + Th
        s = smoothstep((x - px0) / (0.33 * W))
        return bt + 0.0002 + Th * (0.45 + 0.55 * s)
    pg_path = [(px0, bt + 0.0002, 'pg'), (px1, bt + 0.0002, 'pg'), (px1, ztop(px1), 'fore')]
    pg_path += [(x, ztop(x), 'pgtop') for x in reversed(xs_pg)]
    pg_ys = sorted(set(linspace(-H / 2 + o, H / 2 - o, 5) + [-H / 2 + o + pm, H / 2 - o - pm]))
    printed = spec.get('open_print', True) and curl

    def pg_fn(p0, p1, y0, y1):
        if p0[2] == 'pgtop' and p1[2] == 'pgtop' and printed:
            xm = (p0[0] + p1[0]) / 2
            ym = (y0 + y1) / 2
            if px0 + pm < xm < px1 - pm and -H / 2 + o + pm < ym < H / 2 - o - pm:
                return 'print_grey'
            return spec.get('page_face', 'paper_white')
        if p0[2] == 'pgtop':
            return spec.get('page_face', 'paper_white') if printed else pages_role
        return pages_role

    for side in ('left', 'right'):
        is_front = (side == front_half)
        half = Piece()
        half.add(sweep(board_path, ys, board_fn(is_front), cover))
        half.add(sweep(pg_path, pg_ys, pg_fn, pages_role))
        if side == 'right':
            M = Tr(g, 0, 0) @ R('Y', -phi)
        else:
            M = Tr(-g, 0, 0) @ R('Y', phi) @ S(-1, 1, 1)
        out.add(half, M)
    # spine strip bridging the hinges, bulging away from the pages
    n_arc = 8
    sag = max(bt * 1.2, Tt * 0.18)
    outer = [(-g + 2 * g * i / n_arc, -sag * math.sin(math.pi * i / n_arc), 'spine') for i in range(n_arc + 1)]
    inner = [(-g + 2 * g * (n_arc - i) / n_arc, bt - (sag - bt * 0.8) * math.sin(math.pi * (n_arc - i) / n_arc), 'inner') for i in range(n_arc + 1)]
    sp_path = outer + inner

    def sp_fn(p0, p1, y0, y1):
        ym = (y0 + y1) / 2
        if p0[2] == 'inner':
            return endpaper
        for b in bands:
            if b.get('where', 'all') in ('all', 'spine') and b['y0'] <= ym <= b['y1']:
                return b['role']
        return spine_role
    out.add(sweep(sp_path, ys, sp_fn, spine_role))
    if face_down:
        out.transform(R('Y', 180))
    return out.normalize()


# ------------------------------------------------------------------------------------------------ placement helper

def rect_corners(cx, cy, w, d, yaw_deg):
    a = math.radians(yaw_deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = sx * w / 2, sy * d / 2
        out.append(Vector((cx + x * c - y * s, cy + x * s + y * c)))
    return out


def rects_overlap(a, b):
    for poly in (a, b):
        for i in range(4):
            e = poly[(i + 1) % 4] - poly[i]
            ax = Vector((-e.y, e.x))
            pa = [ax.dot(p) for p in a]
            pb = [ax.dot(p) for p in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def point_in_rect(p, corners):
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        if (b - a).cross(p - a) < -1e-9:
            return False
    return True


class Stacker:
    """Tracks placed footprints (rotated rectangles) and their top heights; fakes resting physics:
    an item fully over a flat item sits on it, an item partly over one tilts onto its edge."""
    def __init__(self):
        self.items = []

    def height_at(self, p):
        z = 0.0
        for c, top, flat in self.items:
            if flat and top is not None and point_in_rect(p, c):
                z = max(z, top)
        return z

    def support(self, corners):
        return max([self.height_at(c) for c in corners] + [0.0])

    def place(self, piece, cx, cy, yaw, extra_rot=None, ztop=None, lift=0.0, flat=True, tilt_ok=True, ground=False):
        """Return matrix placing a normalised piece at (cx,cy,yaw). ztop = height to use for things stacked on it."""
        sz = piece.size()
        corners = rect_corners(cx, cy, sz.x, sz.y, yaw)
        M_local = I4
        tilted = False
        z = 0.0
        if not ground:
            hs = [self.height_at(c) for c in corners]
            hc = self.height_at(Vector((cx, cy)))
            h = max(hs + [hc])
            if h > 0.0015:
                sup = [i for i, hh in enumerate(hs) if hh > h - 0.004]
                diag = (sup == [0, 2] or sup == [1, 3])
                if tilt_ok and 1 <= len(sup) <= 3 and not diag:
                    loc = [Vector((-sz.x / 2, -sz.y / 2)), Vector((sz.x / 2, -sz.y / 2)), Vector((sz.x / 2, sz.y / 2)), Vector((-sz.x / 2, sz.y / 2))]
                    d = Vector((0.0, 0.0))
                    for i in sup:
                        d += loc[i]
                    if d.length > 1e-6:
                        d.normalize()
                        L = abs(sz.x / 2 * d.x) + abs(sz.y / 2 * d.y)
                        th = math.asin(min(1.0, h / (2 * L)))
                        a = Vector((-d.y, d.x, 0.0))
                        p = Vector((-d.x * L, -d.y * L, 0.0))
                        M_local = Matrix.Translation(p) @ Matrix.Rotation(-th, 4, a) @ Matrix.Translation(-p)
                        tilted = True
                    else:
                        z = h
                else:
                    z = h
        z += lift
        M = Tr(cx, cy, z) @ R('Z', yaw) @ M_local
        if extra_rot is not None:
            M = M @ extra_rot
        top = None if tilted else z + (ztop if ztop is not None else sz.z)
        self.items.append((corners, top, flat and not tilted))
        return M


# ------------------------------------------------------------------------------------------------ contact sheet

def contact_sheet(paths, out_path, cols=4, cell=(320, 240)):
    import numpy as np
    cw, ch = cell
    rows = max(1, math.ceil(len(paths) / cols))
    sheet = np.zeros((rows * ch, cols * cw, 4), dtype=np.float32)
    sheet[:, :, 3] = 1.0
    for i, p in enumerate(paths):
        if not os.path.exists(p):
            continue
        img = bpy.data.images.load(p)
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        bpy.data.images.remove(img)
        fy, fx = max(1, h // ch), max(1, w // cw)
        px = px[::fy, ::fx][:ch, :cw]
        r, c = i // cols, i % cols
        y0 = (rows - 1 - r) * ch
        sheet[y0:y0 + px.shape[0], c * cw:c * cw + px.shape[1]] = px
    out = bpy.data.images.new("sheet", cols * cw, rows * ch, alpha=True)
    out.pixels = sheet.ravel().tolist()
    out.filepath_raw = out_path
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(out)
    return out_path


# ------------------------------------------------------------------------------------------------ book library
# lying-frame coords: x in [-W/2, W/2] (spine at -W/2), y in [-H/2, H/2] (head at +H/2)
BOOKS = {
    # hero singles -------------------------------------------------------------------------------
    "a": dict(W=0.138, H=0.215, T=0.030, kind="hard", cover="book_cloth_blue", spine="book_cloth_black", pages="paper_pages_aged",
              bands=[dict(y0=0.052, y1=0.074, role="book_band_gold", where="spine"), dict(y0=-0.082, y1=-0.077, role="book_band_gold", where="spine")],
              labels=[dict(x0=-0.030, x1=0.045, y0=0.050, y1=0.068, role="book_band_gold")], scuffs=["fh", "bf"], seed=1),
    "b": dict(W=0.111, H=0.181, T=0.017, kind="paper", cover="book_cover_orange", pages="paper_pages_aged", curl=0.004,
              bands=[dict(y0=-0.034, y1=0.034, role="book_band_white", where="all")],
              labels=[dict(x0=-0.034, x1=0.034, y0=-0.012, y1=0.004, role="print_black")], seed=2),
    "c": dict(W=0.190, H=0.246, T=0.048, kind="hard", cover="book_cloth_grey", pages="paper_white", seed=3,
              jacket=dict(cover="book_cover_white", spine="book_cover_white",
                          bands=[dict(y0=-0.1217, y1=-0.045, role="book_cover_teal", where="all"), dict(y0=0.070, y1=0.092, role="print_black", where="spine")],
                          labels=[dict(x0=-0.060, x1=0.060, y0=0.060, y1=0.090, role="print_black"), dict(x0=-0.070, x1=0.070, y0=-0.030, y1=0.040, role="print_photo")],
                          scuffs=["fh"])),
    "d": dict(W=0.112, H=0.176, T=0.011, kind="paper", cover="book_cover_white", pages="paper_pages", curl=0.002, seed=4,
              bands=[dict(y0=-0.088, y1=-0.060, role="book_cover_pink", where="all")],
              labels=[dict(x0=-0.040, x1=0.050, y0=-0.050, y1=0.058, role="print_photo"), dict(x0=-0.045, x1=0.045, y0=0.062, y1=0.080, role="print_black")]),
    "e": dict(W=0.200, H=0.255, T=0.026, kind="hard", cover="book_cloth_red", pages="paper_white", seed=5,
              jacket=dict(cover="book_cover_cream", spine="book_cover_red",
                          bands=[dict(y0=0.030, y1=0.070, role="book_band_white", where="spine")],
                          labels=[dict(x0=-0.085, x1=0.085, y0=-0.095, y1=0.060, role="print_photo"), dict(x0=-0.070, x1=0.070, y0=0.078, y1=0.104, role="book_cover_red")],
                          scuffs=["bf"])),
    # supporting cast for piles / stacks / rows -------------------------------------------------
    "f": dict(W=0.130, H=0.200, T=0.022, kind="hard", cover="book_cloth_green", pages="paper_pages_aged", seed=6,
              bands=[dict(y0=0.045, y1=0.062, role="book_band_gold", where="spine")], scuffs=["ff"]),
    "g": dict(W=0.130, H=0.198, T=0.022, kind="paper", cover="book_cover_teal", pages="paper_pages", curl=0.003, seed=7,
              bands=[dict(y0=0.050, y1=0.075, role="book_band_white", where="all")],
              labels=[dict(x0=-0.040, x1=0.040, y0=-0.040, y1=0.030, role="print_photo")]),
    "h": dict(W=0.110, H=0.178, T=0.014, kind="paper", cover="book_cover_yellow", pages="paper_pages_aged", curl=0.005, seed=8,
              bands=[dict(y0=-0.089, y1=-0.070, role="book_band_black", where="all")],
              labels=[dict(x0=-0.035, x1=0.040, y0=0.030, y1=0.060, role="print_black")]),
    "i": dict(W=0.150, H=0.230, T=0.035, kind="hard", cover="book_cloth_brown", pages="paper_pages_aged", seed=9, endpaper="paper_pages_aged",
              bands=[dict(y0=0.060, y1=0.080, role="book_band_gold", where="spine"), dict(y0=-0.010, y1=-0.005, role="book_band_gold", where="spine"),
                     dict(y0=-0.075, y1=-0.070, role="book_band_gold", where="spine")], scuffs=["fh", "ff", "bh"]),
    "j": dict(W=0.128, H=0.196, T=0.020, kind="paper", cover="book_cover_purple", pages="paper_pages", seed=10,
              bands=[dict(y0=0.070, y1=0.098, role="book_band_white", where="all")],
              labels=[dict(x0=-0.045, x1=0.045, y0=-0.060, y1=0.040, role="print_grey")]),
    "k": dict(W=0.160, H=0.240, T=0.030, kind="hard", cover="book_cloth_black", pages="paper_white", seed=11,
              jacket=dict(cover="book_cover_skyblue", spine="book_cover_navy",
                          bands=[dict(y0=-0.020, y1=0.020, role="book_band_white", where="all")],
                          labels=[dict(x0=-0.050, x1=0.060, y0=0.040, y1=0.090, role="book_cover_navy")])),
    "l": dict(W=0.110, H=0.180, T=0.027, kind="paper", cover="book_cover_red", pages="paper_pages_aged", curl=0.006, seed=12,
              bands=[dict(y0=-0.090, y1=-0.062, role="book_band_black", where="all")],
              labels=[dict(x0=-0.038, x1=0.038, y0=0.000, y1=0.040, role="book_band_white")]),
    "m": dict(W=0.135, H=0.215, T=0.018, kind="paper", cover="book_cover_white", pages="paper_white", seed=13,
              bands=[dict(y0=-0.1075, y1=0.000, role="book_cover_green", where="all")],
              labels=[dict(x0=-0.045, x1=0.045, y0=0.040, y1=0.070, role="print_black")]),
    "n": dict(W=0.140, H=0.220, T=0.028, kind="hard", cover="book_cloth_black", pages="paper_pages", seed=14,
              bands=[dict(y0=0.040, y1=0.075, role="book_band_white", where="spine")], scuffs=["fh"]),
    "o": dict(W=0.105, H=0.175, T=0.012, kind="paper", cover="book_cover_pink", pages="paper_pages", curl=0.003, seed=15,
              labels=[dict(x0=-0.035, x1=0.035, y0=-0.030, y1=0.050, role="print_photo")],
              bands=[dict(y0=0.065, y1=0.087, role="book_band_black", where="all")]),
    "p": dict(W=0.240, H=0.280, T=0.018, kind="hard", cover="book_cloth_grey", pages="paper_white", seed=16,
              jacket=dict(cover="book_cover_white", spine="print_black",
                          labels=[dict(x0=-0.100, x1=0.100, y0=-0.110, y1=0.080, role="print_photo")],
                          bands=[dict(y0=0.090, y1=0.120, role="book_band_white", where="spine")])),
    "q": dict(W=0.125, H=0.190, T=0.016, kind="paper", cover="book_cover_navy", pages="paper_pages_aged", curl=0.004, seed=17,
              bands=[dict(y0=0.040, y1=0.060, role="flyer_orange", where="all")],
              labels=[dict(x0=-0.040, x1=0.040, y0=-0.050, y1=0.020, role="book_band_white")]),
    "r": dict(W=0.145, H=0.222, T=0.040, kind="hard", cover="book_cloth_red", pages="paper_pages_aged", seed=18,
              bands=[dict(y0=0.055, y1=0.078, role="book_band_black", where="spine"), dict(y0=-0.085, y1=-0.062, role="book_band_black", where="spine")],
              labels=[dict(x0=-0.040, x1=0.040, y0=0.052, y1=0.070, role="book_band_black")], scuffs=["ff", "bh"]),
}
