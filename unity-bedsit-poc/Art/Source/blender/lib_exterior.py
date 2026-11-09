"""lib_exterior.py - helpers for the `exterior` family (street scenes seen through the bedsit windows).

Everything is built into a single bmesh via the MB (mesh builder) class so that a whole facade with
thousands of bricks becomes ONE object with one material slot per role (fast, no per-part ops calls).

Coordinate conventions (see BRIEF.md): 1 unit = 1 m, +Z up, FRONT faces -Y, origin at the ground-level
front-centre of each building. Facades are built in a local frame via `frame_tf(origin, e1, e2)`:
  u along the wall (left->right seen from outside), v up, e3 = e1 x e2 = OUTWARD normal.
  d (third local coordinate) is 0 on the brick face, NEGATIVE going into the building, positive = proud.
"""
import bpy, bmesh, math, random, os, sys, json
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bsk
from bsk import MATERIALS

# ------------------------------------------------------------------------------------------------ roles
NEW_ROLES = {
    # masonry
    "brick": ((0.56, 0.31, 0.23), 0.9, 0.0),
    "brick_dark": ((0.42, 0.22, 0.17), 0.9, 0.0),
    "brick_light": ((0.66, 0.42, 0.31), 0.9, 0.0),
    "brick_yellow": ((0.70, 0.62, 0.45), 0.9, 0.0),
    "brick_yellow_dark": ((0.55, 0.47, 0.33), 0.9, 0.0),
    "brick_sooty": ((0.26, 0.19, 0.17), 0.9, 0.0),
    "brick_sooty_dark": ((0.17, 0.13, 0.12), 0.9, 0.0),
    "brick_sooty_light": ((0.36, 0.27, 0.23), 0.9, 0.0),
    "mortar": ((0.60, 0.56, 0.50), 0.95, 0.0),
    "mortar_dark": ((0.30, 0.28, 0.26), 0.95, 0.0),
    "stone_sill": ((0.72, 0.70, 0.64), 0.8, 0.0),
    "render_painted": ((0.86, 0.84, 0.78), 0.85, 0.0),
    "render_dark": ((0.22, 0.24, 0.27), 0.85, 0.0),
    "concrete": ((0.55, 0.54, 0.50), 0.9, 0.0),
    "slate_roof": ((0.22, 0.23, 0.26), 0.7, 0.0),
    "terracotta": ((0.62, 0.33, 0.22), 0.8, 0.0),
    # joinery / metal
    "upvc_white": ((0.90, 0.90, 0.88), 0.4, 0.0),
    "wood_painted_green": ((0.10, 0.30, 0.22), 0.45, 0.0),
    "wood_painted_black": ((0.04, 0.04, 0.045), 0.45, 0.0),
    "wood_painted_blue": ((0.12, 0.20, 0.40), 0.45, 0.0),
    "wood_painted_red": ((0.55, 0.10, 0.10), 0.45, 0.0),
    "wood_painted_cream": ((0.88, 0.84, 0.72), 0.45, 0.0),
    "metal_painted_grey": ((0.45, 0.47, 0.48), 0.5, 0.3),
    "metal_painted_black": ((0.05, 0.05, 0.055), 0.5, 0.3),
    "metal_painted_green": ((0.10, 0.28, 0.20), 0.5, 0.3),
    "metal_chrome": ((0.85, 0.86, 0.88), 0.15, 1.0),
    "corrugated_metal": ((0.40, 0.42, 0.44), 0.55, 0.6),
    "shutter_grey": ((0.55, 0.56, 0.58), 0.5, 0.4),
    # glass & lit surfaces (window_* / *_glow / neon_* / led_* are emissive in Unity)
    "glass_window": ((0.55, 0.65, 0.75), 0.05, 0.0),
    "glass_shop": ((0.70, 0.80, 0.85), 0.05, 0.0),
    "window_lit": ((1.0, 0.78, 0.48), 0.2, 0.0),
    "window_tv": ((0.45, 0.60, 1.0), 0.2, 0.0),
    "window_club": ((0.90, 0.20, 0.80), 0.2, 0.0),
    "window_dark": ((0.04, 0.05, 0.07), 0.1, 0.0),
    "curtain_red": ((0.55, 0.12, 0.12), 0.95, 0.0),
    "curtain_cream": ((0.85, 0.80, 0.70), 0.95, 0.0),
    "curtain_blue": ((0.25, 0.35, 0.55), 0.95, 0.0),
    "blind_white": ((0.90, 0.90, 0.88), 0.9, 0.0),
    "interior_dark": ((0.03, 0.03, 0.035), 0.9, 0.0),
    "interior_wall": ((0.85, 0.82, 0.72), 0.9, 0.0),
    "lino_floor": ((0.45, 0.40, 0.32), 0.6, 0.0),
    "shop_light": ((1.0, 0.95, 0.85), 0.3, 0.0),
    "lamp_glow": ((1.0, 0.72, 0.35), 0.3, 0.0),
    "lamp_housing": ((0.10, 0.10, 0.11), 0.5, 0.4),
    "neon_pink": ((1.0, 0.15, 0.65), 0.3, 0.0),
    "neon_cyan": ((0.15, 0.90, 1.0), 0.3, 0.0),
    "neon_backing": ((0.06, 0.06, 0.07), 0.6, 0.3),
    "light_beam_emitter": ((1.0, 1.0, 1.0), 0.2, 0.0),
    "taxi_sign": ((1.0, 0.85, 0.20), 0.3, 0.0),
    # signage
    "sign_fascia": ((0.72, 0.08, 0.08), 0.4, 0.0),
    "sign_fascia_dark": ((0.08, 0.10, 0.14), 0.4, 0.0),
    "sign_letters": ((0.95, 0.92, 0.80), 0.4, 0.0),
    "sign_letters_dark": ((0.05, 0.05, 0.06), 0.4, 0.0),
    "sign_yellow": ((1.0, 0.80, 0.10), 0.4, 0.0),
    "sign_blue": ((0.10, 0.30, 0.70), 0.4, 0.0),
    "awning_red": ((0.70, 0.12, 0.12), 0.9, 0.0),
    "awning_white": ((0.92, 0.90, 0.84), 0.9, 0.0),
    "poster_a": ((0.85, 0.15, 0.35), 0.8, 0.0),
    "poster_b": ((0.15, 0.60, 0.85), 0.8, 0.0),
    "poster_c": ((0.95, 0.80, 0.15), 0.8, 0.0),
    "poster_d": ((0.10, 0.10, 0.12), 0.8, 0.0),
    "poster_e": ((0.35, 0.80, 0.30), 0.8, 0.0),
    "poster_white": ((0.92, 0.91, 0.88), 0.8, 0.0),
    "hoarding_wood": ((0.30, 0.33, 0.38), 0.8, 0.0),
    "graffiti_a": ((0.95, 0.30, 0.70), 0.7, 0.0),
    "graffiti_b": ((0.20, 0.85, 0.90), 0.7, 0.0),
    "graffiti_c": ((0.95, 0.85, 0.20), 0.7, 0.0),
    "graffiti_white": ((0.95, 0.95, 0.95), 0.7, 0.0),
    # street
    "asphalt": ((0.12, 0.12, 0.125), 0.95, 0.0),
    "paving": ((0.48, 0.47, 0.44), 0.9, 0.0),
    "paving_dark": ((0.40, 0.39, 0.37), 0.9, 0.0),
    "kerb_stone": ((0.55, 0.55, 0.52), 0.85, 0.0),
    "road_paint_yellow": ((0.85, 0.70, 0.15), 0.8, 0.0),
    "road_paint_white": ((0.85, 0.85, 0.82), 0.8, 0.0),
    "drain_iron": ((0.12, 0.12, 0.12), 0.7, 0.8),
    # props
    "speaker_black": ((0.05, 0.05, 0.05), 0.8, 0.0),
    "speaker_grille": ((0.10, 0.10, 0.10), 0.9, 0.5),
    "keg_steel": ((0.70, 0.71, 0.73), 0.35, 1.0),
    "rope_red": ((0.60, 0.08, 0.10), 0.95, 0.0),
    "produce_orange": ((0.95, 0.50, 0.10), 0.7, 0.0),
    "produce_green": ((0.35, 0.60, 0.20), 0.7, 0.0),
    "produce_red": ((0.80, 0.15, 0.10), 0.6, 0.0),
    "produce_yellow": ((0.95, 0.85, 0.20), 0.7, 0.0),
    "product_a": ((0.85, 0.20, 0.15), 0.6, 0.0),
    "product_b": ((0.15, 0.40, 0.80), 0.6, 0.0),
    "product_c": ((0.95, 0.80, 0.20), 0.6, 0.0),
    "product_d": ((0.25, 0.65, 0.35), 0.6, 0.0),
    "product_e": ((0.90, 0.90, 0.85), 0.6, 0.0),
    "plastic_dark_green": ((0.07, 0.22, 0.12), 0.5, 0.0),
    # vehicles
    "car_paint_red": ((0.65, 0.08, 0.08), 0.3, 0.2),
    "car_paint_blue": ((0.10, 0.18, 0.45), 0.3, 0.2),
    "car_paint_silver": ((0.70, 0.72, 0.75), 0.3, 0.8),
    "car_glass": ((0.15, 0.20, 0.25), 0.05, 0.0),
    "car_trim_black": ((0.04, 0.04, 0.045), 0.6, 0.0),
    "car_light_rear": ((0.90, 0.08, 0.05), 0.2, 0.0),
    "car_light_front": ((0.95, 0.95, 0.90), 0.2, 0.0),
    "car_wheel_rim": ((0.70, 0.70, 0.72), 0.3, 1.0),
    "car_plate_white": ((0.95, 0.95, 0.92), 0.4, 0.0),
    "car_plate_yellow": ((0.95, 0.80, 0.15), 0.4, 0.0),
    # nature / backdrop
    "bark": ((0.30, 0.24, 0.18), 0.95, 0.0),
    "leaf_green": ((0.20, 0.38, 0.14), 0.9, 0.0),
    "leaf_dark": ((0.12, 0.26, 0.10), 0.9, 0.0),
    "skyline_dark": ((0.10, 0.11, 0.14), 0.9, 0.0),
    "skyline_mid": ((0.16, 0.17, 0.20), 0.9, 0.0),
}
for _k, _v in NEW_ROLES.items():
    MATERIALS.setdefault(_k, _v)

EMISSIVE = {"window_lit", "window_tv", "window_club", "shop_light", "lamp_glow", "neon_pink", "neon_cyan",
            "light_beam_emitter", "taxi_sign", "car_light_rear", "car_light_front", "led_red", "led_green",
            "sign_yellow", "screen_on"}
GLASS = {"glass_window", "glass_shop", "car_glass", "glass_clear"}


def mat(role):
    """bsk.mat plus preview niceties: alpha for glass, emission for lit roles."""
    m = bsk.mat(role)
    if role in GLASS:
        c = m.diffuse_color
        m.diffuse_color = (c[0], c[1], c[2], 0.35)
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    if role in EMISSIVE and m.use_nodes:
        b = m.node_tree.nodes.get("Principled BSDF")
        if b:
            col = MATERIALS[role][0]
            b.inputs["Emission Color"].default_value = (col[0], col[1], col[2], 1)
            b.inputs["Emission Strength"].default_value = 3.0
    return m


# ------------------------------------------------------------------------------------------------ frames

def frame_tf(origin, e1, e2):
    """Local->world mapping p = origin + e1*p.x + e2*p.y + (e1 x e2)*p.z (right handed, winding preserved)."""
    o = Vector(origin)
    a = Vector(e1).normalized()
    b = Vector(e2).normalized()
    c = a.cross(b)

    def tf(p):
        return o + a * p[0] + b * p[1] + c * p[2]
    return tf


def IDENT(p):
    return Vector(p)


def facade_tf(width, y=0.0, z=0.0):
    """Front facade frame: u in [0,width] left->right, v up, outward = -Y. Local origin at bottom-left."""
    return frame_tf((-width / 2, y, z), (1, 0, 0), (0, 0, 1))


def seg_tf(p0, p1):
    """Frame along a segment: local z from p0 to p1 (length = |p1-p0|), x/y perpendicular."""
    p0 = Vector(p0); p1 = Vector(p1)
    t = (p1 - p0).normalized()
    up = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
    e1 = up.cross(t).normalized()
    e2 = t.cross(e1)
    o = p0

    def tf(p):
        return o + e1 * p[0] + e2 * p[1] + t * p[2]
    return tf


# ------------------------------------------------------------------------------------------------ mesh builder

_BOX_FACES = {
    "-z": [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
    "+z": [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    "-y": [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
    "+y": [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
    "-x": [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
    "+x": [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
}
_AXIS = {"x": 0, "y": 1, "z": 2}


class MB:
    """Accumulates faces (with role material indices) into one bmesh; build() -> mesh object."""

    def __init__(self):
        self.bm = bmesh.new()
        self.roles = []
        self.ridx = {}
        self.nfaces = 0

    def slot(self, role):
        if role not in self.ridx:
            self.ridx[role] = len(self.roles)
            self.roles.append(role)
        return self.ridx[role]

    # --- primitives -------------------------------------------------------------------------
    def face(self, pts, role, smooth=False):
        try:
            vs = [self.bm.verts.new(Vector(p)) for p in pts]
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = self.slot(role)
        f.smooth = smooth
        self.nfaces += 1
        return f

    def quad(self, p0, p1, p2, p3, role, smooth=False):
        return self.face([p0, p1, p2, p3], role, smooth)

    def box(self, lo, hi, role, tf=IDENT, skip=(), inset=0.0, inset_face="+z", rolemap=None, smooth=False):
        """Axis box in local coords lo..hi mapped by tf. skip faces by name ('-y', '+z'...).
        inset: shrink the `inset_face` so the box becomes a chamfered frustum (brick / tile look)."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        P = {}
        ia = _AXIS[inset_face[1]] if inset else -1
        iside = 1 if (inset and inset_face[0] == "+") else 0
        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    idx = (ix, iy, iz)
                    p = [x0 if ix == 0 else x1, y0 if iy == 0 else y1, z0 if iz == 0 else z1]
                    if inset and idx[ia] == iside:
                        for b in range(3):
                            if b != ia:
                                p[b] += inset if idx[b] == 0 else -inset
                    P[idx] = tf(p)
        for k, order in _BOX_FACES.items():
            if k in skip:
                continue
            r = rolemap.get(k, role) if rolemap else role
            self.face([P[i] for i in order], r, smooth)

    def box_c(self, center, size, role, tf=IDENT, **kw):
        c = Vector(center); s = Vector(size) / 2
        self.box(c - s, c + s, role, tf, **kw)

    def bar(self, p0, p1, w, role, h=None, cap=True):
        """Square-section bar from p0 to p1 (world), thickness w (x) and h (y)."""
        h = w if h is None else h
        L = (Vector(p1) - Vector(p0)).length
        skip = () if cap else ("-z", "+z")
        self.box((-w / 2, -h / 2, 0), (w / 2, h / 2, L), role, seg_tf(p0, p1), skip=skip)

    def cyl(self, base, r0, r1, h, role, segs=16, tf=IDENT, caps=(True, True), smooth=True, cap_role=None, phase=0.0):
        """Cylinder/frustum along local +z starting at `base` (local), radius r0 bottom, r1 top."""
        bx, by, bz = base
        ang = [phase + 2 * math.pi * i / segs for i in range(segs)]
        r0 = max(r0, 0.0); r1 = max(r1, 0.0)
        ring0 = [tf((bx + r0 * math.cos(a), by + r0 * math.sin(a), bz)) for a in ang]
        ring1 = [tf((bx + r1 * math.cos(a), by + r1 * math.sin(a), bz + h)) for a in ang]
        cr = cap_role or role
        if r1 < 1e-6:
            apex = tf((bx, by, bz + h))
            for i in range(segs):
                j = (i + 1) % segs
                self.face([ring0[i], ring0[j], apex], role, smooth)
        elif r0 < 1e-6:
            apex = tf((bx, by, bz))
            for i in range(segs):
                j = (i + 1) % segs
                self.face([apex, ring1[j], ring1[i]], role, smooth)
        else:
            for i in range(segs):
                j = (i + 1) % segs
                self.face([ring0[i], ring0[j], ring1[j], ring1[i]], role, smooth)
        if caps[0] and r0 > 1e-6:
            self.face(list(reversed(ring0)), cr, False)
        if caps[1] and r1 > 1e-6:
            self.face(ring1, cr, False)

    def lathe(self, profile, role, segs=24, tf=IDENT, base=(0, 0, 0), smooth=True, cap_bottom=True, cap_top=True, rolemap=None):
        """Surface of revolution about local z: profile = [(r, z), ...] bottom->top; r=0 closes the end.
        rolemap: {segment_index: role} to recolour individual profile bands (e.g. keg chimes)."""
        bx, by, bz = base
        ang = [2 * math.pi * i / segs for i in range(segs)]
        rings = []
        for (r, z) in profile:
            if r <= 1e-6:
                rings.append([tf((bx, by, bz + z))])
            else:
                rings.append([tf((bx + r * math.cos(a), by + r * math.sin(a), bz + z)) for a in ang])
        for k, (a, b) in enumerate(zip(rings[:-1], rings[1:])):
            rr = rolemap.get(k, role) if rolemap else role
            for i in range(segs):
                j = (i + 1) % segs
                if len(a) == 1 and len(b) == 1:
                    continue
                if len(a) == 1:
                    self.face([a[0], b[j], b[i]], rr, smooth)
                elif len(b) == 1:
                    self.face([a[i], a[j], b[0]], rr, smooth)
                else:
                    self.face([a[i], a[j], b[j], b[i]], rr, smooth)
        if cap_bottom and len(rings[0]) > 1:
            self.face(list(reversed(rings[0])), role, False)
        if cap_top and len(rings[-1]) > 1:
            self.face(rings[-1], role, False)

    def tube(self, pts, r, role, segs=8, caps=True, smooth=True, taper=None):
        """Round tube swept along a polyline (parallel-transport frames). taper: (r_start, r_end)."""
        pts = [Vector(p) for p in pts]
        n = len(pts)
        if n < 2:
            return
        tang = []
        for i in range(n):
            if i == 0:
                t = pts[1] - pts[0]
            elif i == n - 1:
                t = pts[-1] - pts[-2]
            else:
                t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
                if t.length < 1e-6:
                    t = pts[i + 1] - pts[i]
            tang.append(t.normalized())
        t0 = tang[0]
        up = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
        nrm = (up - t0 * up.dot(t0)).normalized()
        ang = [2 * math.pi * i / segs for i in range(segs)]
        rings = []
        for i in range(n):
            t = tang[i]
            nrm = (nrm - t * nrm.dot(t))
            if nrm.length < 1e-6:
                nrm = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
                nrm = (nrm - t * nrm.dot(t))
            nrm.normalize()
            bn = t.cross(nrm)
            ri = r if taper is None else taper[0] + (taper[1] - taper[0]) * i / (n - 1)
            rings.append([pts[i] + (nrm * math.cos(a) + bn * math.sin(a)) * ri for a in ang])
        for i in range(n - 1):
            a, b = rings[i], rings[i + 1]
            for k in range(segs):
                j = (k + 1) % segs
                self.face([a[k], a[j], b[j], b[k]], role, smooth)
        if caps:
            self.face(list(reversed(rings[0])), role, False)
            self.face(rings[-1], role, False)

    def merge_bm(self, tmp, role, smooth=True):
        tmp.verts.ensure_lookup_table()
        tmp.verts.index_update()
        vmap = [self.bm.verts.new(v.co) for v in tmp.verts]
        for f in tmp.faces:
            try:
                nf = self.bm.faces.new([vmap[v.index] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = self.slot(role)
            nf.smooth = smooth
            self.nfaces += 1
        tmp.free()

    def sphere(self, center, radius, role, subdiv=2, scale=(1, 1, 1), noise_amp=0.0, noise_scale=1.0, seed=0, smooth=True):
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1.0)
        rnd = random.Random(seed)
        off = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
        c = Vector(center)
        for v in tmp.verts:
            p = v.co.copy()
            if noise_amp:
                p *= 1.0 + noise_amp * noise.noise(p * noise_scale + off)
            v.co = Vector((p.x * scale[0] * radius, p.y * scale[1] * radius, p.z * scale[2] * radius)) + c
        self.merge_bm(tmp, role, smooth)

    def ribbon(self, pts, hw, d0, d1, role, tf=IDENT, closed=None):
        """Thick 2D polyline (local u,v) extruded between d0..d1 along e3 -> block letters / stripes."""
        P = [Vector((p[0], p[1])) for p in pts]
        if closed is None:
            closed = (P[0] - P[-1]).length < 1e-6
        if closed and (P[0] - P[-1]).length < 1e-6:
            P = P[:-1]
        n = len(P)
        if n < 2:
            return
        L, R = offset_polyline(P, hw, closed)
        segs = n if closed else n - 1
        def W(p2, d):
            return tf((p2.x, p2.y, d))
        for i in range(segs):
            j = (i + 1) % n
            self.face([W(R[i], d1), W(R[j], d1), W(L[j], d1), W(L[i], d1)], role)
            self.face([W(L[i], d0), W(L[j], d0), W(R[j], d0), W(R[i], d0)], role)
            self.face([W(L[i], d1), W(L[j], d1), W(L[j], d0), W(L[i], d0)], role)
            self.face([W(R[i], d0), W(R[j], d0), W(R[j], d1), W(R[i], d1)], role)
        if not closed:
            self.face([W(L[0], d1), W(L[0], d0), W(R[0], d0), W(R[0], d1)], role)
            self.face([W(R[-1], d1), W(R[-1], d0), W(L[-1], d0), W(L[-1], d1)], role)

    def poly_prism(self, pts, d0, d1, role, tf=IDENT, cap_role=None):
        """Extrude a simple CCW polygon (local u,v) from d0 to d1 along e3."""
        P = [Vector((p[0], p[1])) for p in pts]
        if (P[0] - P[-1]).length < 1e-6:
            P = P[:-1]
        area = sum(P[i].x * P[(i + 1) % len(P)].y - P[(i + 1) % len(P)].x * P[i].y for i in range(len(P)))
        if area < 0:
            P.reverse()
        cr = cap_role or role
        top = [tf((p.x, p.y, d1)) for p in P]
        bot = [tf((p.x, p.y, d0)) for p in P]
        self.face(top, cr)
        self.face(list(reversed(bot)), cr)
        n = len(P)
        for i in range(n):
            j = (i + 1) % n
            self.face([bot[i], bot[j], top[j], top[i]], role)

    # --- finish --------------------------------------------------------------------------------
    def build(self, name, smooth_angle=35, uv_scale=1.0, location=(0, 0, 0)):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        for r in self.roles:
            me.materials.append(mat(r))
        ob.location = location
        bsk.shade(ob, True, angle=smooth_angle)
        bsk.uv_box(ob, uv_scale)
        return ob


# ------------------------------------------------------------------------------------------------ 2D helpers

def offset_polyline(P, hw, closed):
    n = len(P)
    L, R = [], []
    for i in range(n):
        if closed:
            d0 = P[i] - P[i - 1]
            d1 = P[(i + 1) % n] - P[i]
        else:
            d0 = (P[i] - P[i - 1]) if i > 0 else (P[1] - P[0])
            d1 = (P[i + 1] - P[i]) if i < n - 1 else (P[-1] - P[-2])
        if d0.length < 1e-9:
            d0 = d1.copy()
        if d1.length < 1e-9:
            d1 = d0.copy()
        d0.normalize(); d1.normalize()
        n0 = Vector((-d0.y, d0.x))
        n1 = Vector((-d1.y, d1.x))
        m = n0 + n1
        if m.length < 1e-6:
            m = n0.copy(); k = 1.0
        else:
            m.normalize()
            k = 1.0 / max(m.dot(n0), 0.4)
        L.append(P[i] + m * hw * k)
        R.append(P[i] - m * hw * k)
    return L, R


def arc(cx, cy, r, a0, a1, n=8, rx=None):
    rx = r if rx is None else rx
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy + r * math.sin(a)))
    return out


def fillet(pts, r=0.05, n=4, closed=False):
    """Round the corners of a polyline with small quadratic arcs (for neon tubes)."""
    P = [Vector((p[0], p[1])) for p in pts]
    if closed and (P[0] - P[-1]).length < 1e-6:
        P = P[:-1]
    m = len(P)
    out = []
    rng = range(m) if closed else range(1, m - 1)
    if not closed:
        out.append(P[0])
    for i in rng:
        a, b, c = P[i - 1], P[i], P[(i + 1) % m]
        d0 = b - a; d1 = c - b
        if d0.length < 1e-9 or d1.length < 1e-9:
            out.append(b); continue
        cosang = d0.normalized().dot(d1.normalized())
        if cosang > 0.985:          # nearly straight: keep point
            out.append(b); continue
        cut = min(r, 0.45 * d0.length, 0.45 * d1.length)
        A = b - d0.normalized() * cut
        B = b + d1.normalized() * cut
        for k in range(n + 1):
            t = k / n
            out.append(A * (1 - t) ** 2 + b * 2 * (1 - t) * t + B * t * t)
    if not closed:
        out.append(P[-1])
    else:
        out.append(out[0])
    return [(p.x, p.y) for p in out]


# ------------------------------------------------------------------------------------------------ stroke font
# glyph -> (advance width, [stroke polylines in a 0..1 em box]); a stroke whose first==last point is closed.
FONT = {
    "A": (0.80, [[(0, 0), (0.4, 1), (0.8, 0)], [(0.17, 0.38), (0.63, 0.38)]]),
    "B": (0.72, [[(0, 0), (0, 1)], [(0, 1), (0.42, 1)] + arc(0.42, 0.76, 0.24, 90, -90, 6) + [(0, 0.52)],
                 [(0, 0.52), (0.46, 0.52)] + arc(0.46, 0.26, 0.26, 90, -90, 6) + [(0, 0)]]),
    "C": (0.76, [arc(0.42, 0.5, 0.5, 48, 312, 10, rx=0.42)]),
    "D": (0.76, [[(0, 0), (0, 1), (0.3, 1)] + arc(0.3, 0.5, 0.5, 90, -90, 8, rx=0.46) + [(0, 0)]]),
    "E": (0.65, [[(0.65, 0), (0, 0), (0, 1), (0.65, 1)], [(0, 0.5), (0.55, 0.5)]]),
    "F": (0.62, [[(0, 0), (0, 1), (0.62, 1)], [(0, 0.52), (0.52, 0.52)]]),
    "G": (0.80, [arc(0.42, 0.5, 0.5, 48, 360, 12, rx=0.42) + [(0.84, 0.5), (0.48, 0.5)]]),
    "H": (0.72, [[(0, 0), (0, 1)], [(0.72, 0), (0.72, 1)], [(0, 0.5), (0.72, 0.5)]]),
    "I": (0.22, [[(0.11, 0), (0.11, 1)]]),
    "J": (0.62, [[(0.62, 1), (0.62, 0.3)] + arc(0.31, 0.3, 0.3, 0, -180, 6)]),
    "K": (0.72, [[(0, 0), (0, 1)], [(0.72, 1), (0, 0.42)], [(0.24, 0.58), (0.72, 0)]]),
    "L": (0.62, [[(0, 1), (0, 0), (0.62, 0)]]),
    "M": (0.92, [[(0, 0), (0, 1), (0.46, 0.42), (0.92, 1), (0.92, 0)]]),
    "N": (0.76, [[(0, 0), (0, 1), (0.76, 0), (0.76, 1)]]),
    "O": (0.84, [arc(0.42, 0.5, 0.5, 0, 360, 16, rx=0.42)]),
    "P": (0.70, [[(0, 0), (0, 1), (0.42, 1)] + arc(0.42, 0.74, 0.26, 90, -90, 6) + [(0, 0.48)]]),
    "Q": (0.84, [arc(0.42, 0.5, 0.5, 0, 360, 16, rx=0.42), [(0.55, 0.25), (0.86, -0.05)]]),
    "R": (0.74, [[(0, 0), (0, 1), (0.42, 1)] + arc(0.42, 0.74, 0.26, 90, -90, 6) + [(0, 0.48)], [(0.36, 0.48), (0.74, 0)]]),
    "S": (0.70, [arc(0.35, 0.75, 0.25, 20, 270, 8, rx=0.34) + arc(0.35, 0.25, 0.25, 90, -160, 8, rx=0.34)[1:]]),
    "T": (0.70, [[(0, 1), (0.7, 1)], [(0.35, 0), (0.35, 1)]]),
    "U": (0.74, [[(0, 1), (0, 0.37)] + arc(0.37, 0.37, 0.37, 180, 360, 8) + [(0.74, 1)]]),
    "V": (0.80, [[(0, 1), (0.4, 0), (0.8, 1)]]),
    "W": (1.02, [[(0, 1), (0.23, 0), (0.51, 0.62), (0.79, 0), (1.02, 1)]]),
    "X": (0.76, [[(0, 0), (0.76, 1)], [(0, 1), (0.76, 0)]]),
    "Y": (0.76, [[(0, 1), (0.38, 0.5), (0.76, 1)], [(0.38, 0), (0.38, 0.5)]]),
    "Z": (0.70, [[(0, 1), (0.7, 1), (0, 0), (0.7, 0)]]),
    "0": (0.66, [arc(0.33, 0.5, 0.5, 0, 360, 14, rx=0.33)]),
    "1": (0.40, [[(0.05, 0.78), (0.28, 1), (0.28, 0)]]),
    "2": (0.66, [[(0.02, 0.72)] + arc(0.33, 0.7, 0.3, 160, -30, 6, rx=0.31) + [(0, 0), (0.66, 0)]]),
    "4": (0.70, [[(0.5, 0), (0.5, 1), (0, 0.3), (0.7, 0.3)]]),
    "7": (0.66, [[(0, 1), (0.66, 1), (0.22, 0)]]),
    "-": (0.50, [[(0.06, 0.5), (0.44, 0.5)]]),
    ".": (0.24, [[(0.08, 0.0), (0.16, 0.0)]]),
    " ": (0.40, []),
}


def text_strokes(text, h, x0=0.0, z0=0.0, spacing=0.14):
    """Lay out `text` -> list of stroke polylines in metres (u,v), letter height h. Returns (strokes, width)."""
    strokes = []
    x = x0
    for ch in text.upper():
        adv, glyphs = FONT.get(ch, FONT[" "])
        for g in glyphs:
            strokes.append([(x + p[0] * h, z0 + p[1] * h) for p in g])
        x += (adv + spacing) * h
    return strokes, x - x0 - spacing * h


def text_width(text, h, spacing=0.14):
    return sum((FONT.get(c.upper(), FONT[" "])[0] + spacing) * h for c in text) - spacing * h


def block_text(mb, tf, text, h, x0, z0, d0, d1, role, stroke=None, spacing=0.14, centre_w=None):
    """Block letters (ribbon prisms) on a facade frame. centre_w: centre the text in a span of that width from x0."""
    stroke = stroke if stroke is not None else h * 0.18
    w = text_width(text, h, spacing)
    if centre_w is not None:
        x0 = x0 + (centre_w - w) / 2
    strokes, _ = text_strokes(text, h, x0, z0, spacing)
    for k, s in enumerate(strokes):
        off = 0.0006 * (k % 5)       # avoid coplanar fronts where strokes overlap
        mb.ribbon(s, stroke / 2, d0, d1 + off, role, tf)
    return w


def neon_text(mb, tf, text, h, x0, z0, d, r, role, spacing=0.2, bend=None, segs=8, centre_w=None):
    """Neon tube letters along the stroke font (filleted corners)."""
    bend = bend if bend is not None else h * 0.08
    w = text_width(text, h, spacing)
    if centre_w is not None:
        x0 = x0 + (centre_w - w) / 2
    strokes, _ = text_strokes(text, h, x0, z0, spacing)
    for s in strokes:
        closed = (Vector(s[0]) - Vector(s[-1])).length < 1e-6
        pts = fillet(s, bend, 4, closed)
        world = [tf((p[0], p[1], d)) for p in pts]
        mb.tube(world, r, role, segs=segs, caps=not closed)
    return w


# ------------------------------------------------------------------------------------------------ brick walls

BRICK_L, BRICK_H, JOINT = 0.215, 0.065, 0.010
PW, PH = BRICK_L + JOINT, BRICK_H + JOINT      # 0.225 x 0.075 pitch


def course(z):
    """Snap a height to the nearest brick course line."""
    return round(z / PH) * PH


def _interval(op, z):
    if z < op["z0"] or z > op["z1"]:
        return None
    r = op.get("arch_r", 0.0)
    if r > 0:
        zs = op["z1"] - r
        if z > zs:
            h = r * r - (z - zs) ** 2
            if h <= 0:
                return None
            h = math.sqrt(h)
            cx = (op["x0"] + op["x1"]) / 2
            return (cx - h, cx + h)
    return (op["x0"], op["x1"])


def _subtract(intervals, a, b):
    out = []
    for (x0, x1) in intervals:
        if b <= x0 or a >= x1:
            out.append((x0, x1))
        else:
            if a > x0:
                out.append((x0, a))
            if b < x1:
                out.append((b, x1))
    return out


def brick_wall(mb, tf, width, height, openings, roles=("brick", "brick_dark", "brick_light"), weights=(0.6, 0.25, 0.15),
               mortar="mortar", depth=0.010, seed=0, z_from=0.0, x_from=0.0, inset=0.004, jitter=0.0015):
    """Stretcher-bond brick skin on a facade frame: real proud bricks (chamfered front) over a recessed mortar plane.
    openings: list of {x0,x1,z0,z1[,arch_r]} in wall coords. z0/z1 should be on course lines (use course())."""
    rnd = random.Random(seed)
    nrows = int(math.ceil((height - z_from) / PH))
    row0 = int(round(z_from / PH))
    for k in range(row0, row0 + nrows):
        z0 = k * PH
        z1 = min(z0 + BRICK_H, height)
        if z1 - z0 < 0.02:
            continue
        zc = (z0 + z1) / 2
        # mortar strips for this course band
        band_top = min(z0 + PH, height)
        strips = [(x_from, width)]
        for op in openings:
            iv = _interval(op, zc)
            if iv:
                strips = _subtract(strips, iv[0], iv[1])
        for (a, b) in strips:
            if b - a > 0.005:
                mb.face([tf((a, z0, -depth)), tf((b, z0, -depth)), tf((b, band_top, -depth)), tf((a, band_top, -depth))], mortar)
        # bricks
        off = (PW / 2) if (k % 2) else 0.0
        x = x_from - off
        while x < width:
            xa = max(x, x_from)
            xb = min(x + BRICK_L, width)
            x += PW
            if xb - xa < 0.03:
                continue
            drop = False
            for op in openings:
                iv = _interval(op, zc)
                if not iv:
                    continue
                a, b = iv
                if xa >= a and xb <= b:
                    drop = True; break
                if xa < a < xb and xa < b < xb:      # opening narrower than brick: keep left part
                    xb = a
                elif xa < a < xb:
                    xb = a
                elif xa < b < xb:
                    xa = b
            if drop or xb - xa < 0.03:
                continue
            role = rnd.choices(roles, weights)[0]
            jd = (rnd.random() - 0.5) * 2 * jitter
            mb.box((xa, z0, -depth - 0.004), (xb, z1, jd), role, tf, skip=("-z",), inset=inset, inset_face="+z")
    # note: brick local z axis is the facade depth (e3), box '+z' face = brick front, '-z' = hidden back


def arch_ring(mb, tf, cx, zs, r, depth_in, role, n=22, thick=0.24, proud=0.02, jamb_to=None):
    """Voussoir ring + soffit for a semicircular arch (spring line zs, radius r to the intrados)."""
    for i in range(n):
        a0 = math.pi * i / n
        a1 = math.pi * (i + 1) / n
        pts_in = [(cx + r * math.cos(a0), zs + r * math.sin(a0)), (cx + r * math.cos(a1), zs + r * math.sin(a1))]
        pts_out = [(cx + (r + thick) * math.cos(a1), zs + (r + thick) * math.sin(a1)), (cx + (r + thick) * math.cos(a0), zs + (r + thick) * math.sin(a0))]
        g = 0.006   # joint gap between voussoirs (angular shrink)
        def shrink(p, q):
            v = Vector(q) - Vector(p); L = v.length
            if L < 1e-6:
                return p, q
            v = v / L
            return (Vector(p) + v * g), (Vector(q) - v * g)
        pi0, pi1 = shrink(pts_in[0], pts_in[1])
        po1, po0 = shrink(pts_out[1], pts_out[0])
        poly = [(pi0.x, pi0.y), (pi1.x, pi1.y), (po1.x, po1.y), (po0.x, po0.y)]
        mb.poly_prism(poly, -0.012, proud, role, tf)
    # soffit (inner curved surface) + jambs down to the opening bottom, going into the wall by depth_in
    for i in range(n):
        a0 = math.pi * i / n
        a1 = math.pi * (i + 1) / n
        p0 = (cx + r * math.cos(a0), zs + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), zs + r * math.sin(a1))
        # inward facing (towards the arch centre): order so normal points to centre
        mb.face([tf((p1[0], p1[1], 0)), tf((p0[0], p0[1], 0)), tf((p0[0], p0[1], -depth_in)), tf((p1[0], p1[1], -depth_in))], role)
    if jamb_to is not None:
        zb = jamb_to
        mb.face([tf((cx - r, zb, 0)), tf((cx - r, zb, -depth_in)), tf((cx - r, zs, -depth_in)), tf((cx - r, zs, 0))], role)
        mb.face([tf((cx + r, zb, 0)), tf((cx + r, zs, 0)), tf((cx + r, zs, -depth_in)), tf((cx + r, zb, -depth_in))], role)


# ------------------------------------------------------------------------------------------------ openings

def reveal(mb, tf, x, z, w, h, depth, role, top=True, bottom=False):
    """Inward-facing reveal faces around a rectangular opening (local wall coords), from d=0 to d=-depth."""
    mb.face([tf((x, z, 0)), tf((x, z, -depth)), tf((x, z + h, -depth)), tf((x, z + h, 0))], role)
    mb.face([tf((x + w, z, 0)), tf((x + w, z + h, 0)), tf((x + w, z + h, -depth)), tf((x + w, z, -depth))], role)
    if top:
        mb.face([tf((x, z + h, 0)), tf((x, z + h, -depth)), tf((x + w, z + h, -depth)), tf((x + w, z + h, 0))], role)
    if bottom:
        mb.face([tf((x, z, 0)), tf((x + w, z, 0)), tf((x + w, z, -depth)), tf((x, z, -depth))], role)


def curtains(mb, tf, x, z, w, h, d, role, cover=0.36, waves=5, amp=0.02, both=True):
    """Two rippled curtain panels hanging inside a window opening (plane at depth d)."""
    panels = [(x, x + w * cover)]
    if both:
        panels.append((x + w * (1 - cover), x + w))
    n = 10
    for (a, b) in panels:
        pts_lo, pts_hi = [], []
        for i in range(n + 1):
            u = a + (b - a) * i / n
            dd = d + amp * math.sin(i / n * math.pi * waves)
            pts_lo.append(tf((u, z + 0.01, dd)))
            pts_hi.append(tf((u, z + h - 0.01, dd)))
        for i in range(n):
            mb.face([pts_lo[i], pts_lo[i + 1], pts_hi[i + 1], pts_hi[i]], role, True)


def window(mb, tf, x, z, w, h, kind="sash", look="lit", curtain="curtain_red", frame_role="upvc_white",
           reveal_role="brick", sill_role="stone_sill", lintel=0.15, R=0.30, bars=True, blind=0.0):
    """A complete window in a wall opening. look: 'lit' | 'tv' | 'dark' | 'club'.
    Returns the opening dict to pass to brick_wall (includes the lintel band)."""
    fd0, fd1 = -0.10, -0.16          # frame depth range (into the wall)
    fw = 0.07 if kind != "industrial" else 0.045
    reveal(mb, tf, x, z, w, h, R, reveal_role, top=True, bottom=False)
    # sill: proud, sloped top
    if sill_role:
        s0, s1 = x - 0.06, x + w + 0.06
        mb.face([tf((s0, z, -R)), tf((s1, z, -R)), tf((s1, z - 0.02, 0.07)), tf((s0, z - 0.02, 0.07))], sill_role)   # sloped top
        mb.face([tf((s0, z - 0.02, 0.07)), tf((s1, z - 0.02, 0.07)), tf((s1, z - 0.09, 0.07)), tf((s0, z - 0.09, 0.07))], sill_role)  # nose
        mb.face([tf((s0, z - 0.09, 0.07)), tf((s1, z - 0.09, 0.07)), tf((s1, z - 0.09, 0.0)), tf((s0, z - 0.09, 0.0))], sill_role)  # underside
        mb.face([tf((s0, z, -R)), tf((s0, z - 0.02, 0.07)), tf((s0, z - 0.09, 0.07)), tf((s0, z - 0.09, 0.0)), tf((s0, z - 0.0, -0.0))], sill_role)
        mb.face([tf((s1, z, -R)), tf((s1, z - 0.0, -0.0)), tf((s1, z - 0.09, 0.0)), tf((s1, z - 0.09, 0.07)), tf((s1, z - 0.02, 0.07))], sill_role)
    # lintel (stone/concrete band above)
    if lintel > 0:
        mb.box((x - 0.08, z + h, -0.02), (x + w + 0.08, z + h + lintel, 0.03), sill_role or "stone_sill", tf)
    # outer frame
    mb.box((x, z, fd1), (x + fw, z + h, fd0), frame_role, tf)
    mb.box((x + w - fw, z, fd1), (x + w, z + h, fd0), frame_role, tf)
    mb.box((x + fw, z + h - fw, fd1), (x + w - fw, z + h, fd0), frame_role, tf)
    mb.box((x + fw, z, fd1), (x + w - fw, z + fw, fd0), frame_role, tf)
    gx0, gx1, gz0, gz1 = x + fw, x + w - fw, z + fw, z + h - fw
    if kind == "sash":
        zm = z + h * 0.52
        mb.box((gx0, zm - 0.035, fd1 - 0.02), (gx1, zm + 0.035, fd0), frame_role, tf)   # meeting rail
        mb.box((gx0, zm, fd1 - 0.02), (gx0 + 0.04, gz1, fd1 + 0.03), frame_role, tf)      # upper sash stiles set back
        mb.box((gx1 - 0.04, zm, fd1 - 0.02), (gx1, gz1, fd1 + 0.03), frame_role, tf)
        if bars:
            xm = (gx0 + gx1) / 2
            mb.box((xm - 0.014, gz0, fd1), (xm + 0.014, zm, fd0 - 0.01), frame_role, tf)
            mb.box((xm - 0.014, zm, fd1 - 0.02), (xm + 0.014, gz1, fd1 + 0.02), frame_role, tf)
    elif kind == "casement":
        xm = (gx0 + gx1) / 2
        mb.box((xm - 0.03, gz0, fd1), (xm + 0.03, gz1, fd0), frame_role, tf)
        zt = z + h * 0.72
        mb.box((gx0, zt - 0.03, fd1), (gx1, zt + 0.03, fd0), frame_role, tf)
    elif kind == "industrial":
        nx = max(1, int(round(w / 0.42)))
        nz = max(1, int(round(h / 0.42)))
        for i in range(1, nx):
            u = gx0 + (gx1 - gx0) * i / nx
            mb.box((u - 0.012, gz0, fd1), (u + 0.012, gz1, fd0 + 0.02), frame_role, tf)
        for j in range(1, nz):
            v = gz0 + (gz1 - gz0) * j / nz
            mb.box((gx0, v - 0.012, fd1), (gx1, v + 0.012, fd0 + 0.02), frame_role, tf)
    # glass
    glass_role = "glass_window" if look != "dark" else "window_dark"
    gd = (fd0 + fd1) / 2
    mb.face([tf((gx0, gz0, gd)), tf((gx1, gz0, gd)), tf((gx1, gz1, gd)), tf((gx0, gz1, gd))], glass_role)
    # what is behind the glass
    if look == "dark":
        if curtain:
            curtains(mb, tf, x, z, w, h, -0.22, curtain, cover=0.3)
        mb.face([tf((x, z, -R)), tf((x + w, z, -R)), tf((x + w, z + h, -R)), tf((x, z + h, -R))], "interior_dark")
    else:
        glow = {"lit": "window_lit", "tv": "window_tv", "club": "window_club"}.get(look, "window_lit")
        if blind > 0:
            zb = z + h * (1 - blind)
            mb.face([tf((x + 0.01, zb, -0.2)), tf((x + w - 0.01, zb, -0.2)), tf((x + w - 0.01, z + h, -0.2)), tf((x + 0.01, z + h, -0.2))], "blind_white")
        if curtain:
            curtains(mb, tf, x, z, w, h, -0.22, curtain)
        mb.face([tf((x, z, -R)), tf((x + w, z, -R)), tf((x + w, z + h, -R)), tf((x, z + h, -R))], glow)
    return {"x0": x, "x1": x + w, "z0": z, "z1": z + h + (lintel if lintel > 0 else 0.0)}


def door(mb, tf, x, z, w, h, recess=0.25, leaf_role="wood_painted_blue", reveal_role="brick", panels=4, fanlight=True,
         handle_side="right", kick=False, number=None, letterbox=True, step_role="stone_sill", double=False, glazed=False,
         lintel=0.15, sill_role="stone_sill", frame_role="wood_painted_cream", lit_fan=True):
    """Recessed entrance door with frame, raised panel mouldings, handle, letterbox, step, fanlight."""
    R = recess + 0.12
    reveal(mb, tf, x, z, w, h, R, reveal_role, top=True)
    if lintel > 0:
        mb.box((x - 0.08, z + h, -0.02), (x + w + 0.08, z + h + lintel, 0.03), sill_role, tf)
    # step / threshold
    mb.box((x, z, -recess), (x + w, z + 0.03, 0.02), step_role, tf)
    # frame (architrave) at the recess
    fw = 0.08
    fd1, fd0 = -recess - 0.06, -recess + 0.02
    fan_h = 0.35 if fanlight else 0.0
    mb.box((x, z, fd1), (x + fw, z + h, fd0), frame_role, tf)
    mb.box((x + w - fw, z, fd1), (x + w, z + h, fd0), frame_role, tf)
    mb.box((x + fw, z + h - fw, fd1), (x + w - fw, z + h, fd0), frame_role, tf)
    if fanlight:
        zt = z + h - fan_h
        mb.box((x + fw, zt - 0.04, fd1), (x + w - fw, zt + 0.04, fd0), frame_role, tf)
        mb.face([tf((x + fw, zt + 0.04, fd1 + 0.02)), tf((x + w - fw, zt + 0.04, fd1 + 0.02)),
                 tf((x + w - fw, z + h - fw, fd1 + 0.02)), tf((x + fw, z + h - fw, fd1 + 0.02))],
                "window_lit" if lit_fan else "window_dark")
        if number is not None:
            block_text(mb, tf, str(number), 0.16, x + fw + 0.08, zt + 0.1, fd1 + 0.021, fd1 + 0.03, "sign_letters", stroke=0.025, spacing=0.2)
    # leaf(s)
    ld1, ld0 = -recess - 0.05, -recess
    leaves = [(x + fw, x + w - fw)] if not double else [(x + fw, x + w / 2 - 0.005), (x + w / 2 + 0.005, x + w - fw)]
    top = z + h - fan_h - (0.04 if fanlight else fw)
    for (lx0, lx1) in leaves:
        mb.box((lx0, z + 0.03, ld1), (lx1, top, ld0), leaf_role, tf)
        lw = lx1 - lx0
        if glazed:
            # upper glazed panel (shop door)
            g0, g1, gz0, gz1 = lx0 + 0.1, lx1 - 0.1, z + 0.03 + (top - z) * 0.42, top - 0.12
            mb.box((g0 - 0.03, gz0 - 0.03, ld0), (g1 + 0.03, gz1 + 0.03, ld0 + 0.012), leaf_role, tf,
                   rolemap={"+z": leaf_role})
            mb.face([tf((g0, gz0, ld0 + 0.013)), tf((g1, gz0, ld0 + 0.013)), tf((g1, gz1, ld0 + 0.013)), tf((g0, gz1, ld0 + 0.013))], "window_lit")
            # lower raised panel
            mb.box((lx0 + 0.1, z + 0.18, ld0), (lx1 - 0.1, gz0 - 0.2, ld0 + 0.012), leaf_role, tf)
        elif panels:
            rows = panels // 2 if panels >= 2 else 1
            cols = 2 if panels >= 2 else 1
            m = 0.09
            ph = (top - z - 0.03 - m * (rows + 1)) / rows
            pw = (lw - m * (cols + 1)) / cols
            for rI in range(rows):
                for cI in range(cols):
                    px0 = lx0 + m + cI * (pw + m)
                    pz0 = z + 0.03 + m + rI * (ph + m)
                    # raised moulding frame around a recessed field
                    t = 0.03
                    for (ax0, ax1, az0, az1) in ((px0, px0 + t, pz0, pz0 + ph), (px0 + pw - t, px0 + pw, pz0, pz0 + ph),
                                                 (px0 + t, px0 + pw - t, pz0, pz0 + t), (px0 + t, px0 + pw - t, pz0 + ph - t, pz0 + ph)):
                        mb.box((ax0, az0, ld0), (ax1, az1, ld0 + 0.014), leaf_role, tf)
        if kick:
            mb.box((lx0 + 0.02, z + 0.04, ld0), (lx1 - 0.02, z + 0.30, ld0 + 0.006), "metal_steel", tf)
        if letterbox and not double and not glazed:
            cx = (lx0 + lx1) / 2
            mb.box((cx - 0.17, z + 1.0, ld0), (cx + 0.17, z + 1.08, ld0 + 0.012), "metal_brass", tf)
        # handle
        hx = (lx1 - 0.08) if handle_side == "right" else (lx0 + 0.08)
        if double:
            hx = lx1 - 0.08 if lx0 < x + w / 2 else lx0 + 0.08
        if glazed or double:
            # pull handle bar
            mb.cyl((hx, z + 0.95, ld0), 0.012, 0.012, 0.05, "metal_chrome", 10, tf)
            mb.cyl((hx, z + 1.25, ld0), 0.012, 0.012, 0.05, "metal_chrome", 10, tf)
            mb.bar(tf((hx, z + 0.93, ld0 + 0.05)), tf((hx, z + 1.27, ld0 + 0.05)), 0.024, "metal_chrome")
        else:
            mb.cyl((hx, z + 1.02, ld0), 0.03, 0.03, 0.012, "metal_brass", 12, tf)
            mb.cyl((hx, z + 1.02, ld0 + 0.012), 0.012, 0.02, 0.04, "metal_brass", 12, tf)
            mb.cyl((hx, z + 1.02, ld0 + 0.052), 0.034, 0.034, 0.02, "metal_brass", 12, tf)
    return {"x0": x, "x1": x + w, "z0": z, "z1": z + h + (lintel if lintel > 0 else 0.0)}


# ------------------------------------------------------------------------------------------------ roofs / details

def gable_roof(mb, x0, x1, y0, y1, z_eaves, z_ridge, role="slate_roof", overhang=0.12, ridge_role="terracotta",
               courses=True, gutter=True, front_only=False):
    """Pitched roof with ridge parallel to the street (X). Front slope faces -Y. Adds slate courses + gutter."""
    ym = (y0 + y1) / 2
    yf = y0 - overhang
    yb = y1 + overhang
    xa, xb = x0 - 0.02, x1 + 0.02
    # front slope (normal -Y/+Z)
    mb.face([(xa, yf, z_eaves), (xb, yf, z_eaves), (xb, ym, z_ridge), (xa, ym, z_ridge)], role)
    if not front_only:
        mb.face([(xb, yb, z_eaves), (xa, yb, z_eaves), (xa, ym, z_ridge), (xb, ym, z_ridge)], role)
        # gable triangles (closing ends)
        mb.face([(xa, yf, z_eaves), (xa, ym, z_ridge), (xa, yb, z_eaves)], "brick")
        mb.face([(xb, yf, z_eaves), (xb, yb, z_eaves), (xb, ym, z_ridge)], "brick")
    # underside (soffit) strip at the front overhang
    mb.face([(xa, yf, z_eaves - 0.02), (xa, y0, z_eaves - 0.02), (xb, y0, z_eaves - 0.02), (xb, yf, z_eaves - 0.02)], "wood_painted_cream")
    mb.face([(xa, yf, z_eaves - 0.02), (xb, yf, z_eaves - 0.02), (xb, yf, z_eaves), (xa, yf, z_eaves)], "wood_painted_cream")
    # ridge tiles
    mb.box((xa, ym - 0.12, z_ridge - 0.02), (xb, ym + 0.12, z_ridge + 0.06), ridge_role, inset=0.02, inset_face="+z")
    # slate courses on the front slope: thin slabs stepping down the slope
    if courses:
        slope = Vector((0, ym - yf, z_ridge - z_eaves))
        L = slope.length
        tf = frame_tf((xa, yf, z_eaves), (1, 0, 0), slope.normalized())
        n = int(L / 0.28)
        for i in range(n):
            v0 = i * L / n
            mb.box((0.0, v0, 0.004), (xb - xa, v0 + L / n + 0.03, 0.016), role, tf, skip=("-z",))
    if gutter:
        mb.box((xa - 0.05, yf - 0.12, z_eaves - 0.12), (xb + 0.05, yf, z_eaves - 0.0), "plastic_black",
               rolemap={"+z": "interior_dark"})


def chimney(mb, cx, cy, z0, z1, w=0.9, d=0.5, pots=2, roles=("brick", "brick_dark"), pot_role="terracotta"):
    mb.box((cx - w / 2, cy - d / 2, z0), (cx + w / 2, cy + d / 2, z1), roles[0], skip=("-z",))
    mb.box((cx - w / 2 - 0.04, cy - d / 2 - 0.04, z1 - 0.18), (cx + w / 2 + 0.04, cy + d / 2 + 0.04, z1 - 0.10), roles[1])
    mb.box((cx - w / 2 - 0.07, cy - d / 2 - 0.07, z1 - 0.10), (cx + w / 2 + 0.07, cy + d / 2 + 0.07, z1), "stone_sill")
    for i in range(pots):
        px = cx - w / 2 + (i + 0.5) * w / pots
        mb.lathe([(0.13, 0), (0.12, 0.45), (0.14, 0.52), (0.10, 0.60), (0.09, 0.70), (0.0, 0.70)], pot_role, 14, base=(px, cy, z1))
        mb.lathe([(0.0, 0.70), (0.07, 0.70), (0.07, 0.50)], "interior_dark", 14, base=(px, cy, z1), cap_bottom=True, cap_top=False)


def drainpipe(mb, x, y_face, z0, z1, role="plastic_black", r=0.034, hopper=True, brackets=True):
    """Vertical downpipe proud of a facade whose outward normal is -Y (x in world)."""
    yc = y_face - 0.08
    mb.cyl((x, yc, z0), r, r, z1 - z0, role, 12)
    if brackets:
        z = z0 + 0.6
        while z < z1 - 0.3:
            mb.box((x - r - 0.012, y_face - 0.13, z), (x + r + 0.012, y_face, z + 0.035), "metal_painted_black")
            z += 1.8
    if hopper:
        mb.box((x - 0.12, y_face - 0.20, z1), (x + 0.12, y_face - 0.01, z1 + 0.26), role, inset=0.01, inset_face="-z")
    # shoe at the bottom
    mb.tube([(x, yc, z0 + 0.25), (x, yc, z0 + 0.1), (x, yc - 0.08, z0 + 0.03)], r, role, 10, caps=True)


def shutter_corrugated(mb, tf, x0, x1, z0, z1, d, role="corrugated_metal", slat=0.075, amp=0.012, box_role="shutter_grey"):
    """Horizontal-slat roller shutter surface at depth d (local), with a housing box above."""
    n = int((z1 - z0) / slat)
    for k in range(n):
        za = z0 + k * slat
        zm = za + slat / 2
        zb = za + slat
        mb.face([tf((x0, za, d)), tf((x1, za, d)), tf((x1, zm, d + amp)), tf((x0, zm, d + amp))], role, True)
        mb.face([tf((x0, zm, d + amp)), tf((x1, zm, d + amp)), tf((x1, zb, d)), tf((x0, zb, d))], role, True)
    mb.box((x0 - 0.04, z0 + n * slat, d - 0.05), (x1 + 0.04, z0 + n * slat + 0.30, d + 0.25), box_role, tf)
    # guide rails
    mb.box((x0 - 0.05, z0, d - 0.02), (x0, z0 + n * slat, d + 0.06), box_role, tf)
    mb.box((x1, z0, d - 0.02), (x1 + 0.05, z0 + n * slat, d + 0.06), box_role, tf)


def poster(mb, tf, x, z, w, h, d, base, rot=0.0, seed=0, headline="poster_white"):
    """A pasted poster: coloured sheet + headline band + image block + text lines, all slightly proud."""
    rnd = random.Random(seed)
    c, s = math.cos(rot), math.sin(rot)
    cx, cz = x + w / 2, z + h / 2

    def P(u, v, dd):
        du, dv = u - cx, v - cz
        return tf((cx + du * c - dv * s, cz + du * s + dv * c, dd))

    def rect(u0, v0, u1, v1, dd, role):
        mb.face([P(u0, v0, dd), P(u1, v0, dd), P(u1, v1, dd), P(u0, v1, dd)], role)
    rect(x, z, x + w, z + h, d, base)
    m = w * 0.08
    style = rnd.randint(0, 2)
    if style == 0:      # big headline top, image middle, text bottom
        rect(x + m, z + h * 0.78, x + w - m, z + h - m, d + 0.001, headline)
        rect(x + m, z + h * 0.30, x + w - m, z + h * 0.74, d + 0.001, "poster_d" if base != "poster_d" else "poster_b")
        for i in range(4):
            rect(x + m, z + h * (0.08 + i * 0.05), x + w - m - rnd.random() * w * 0.3, z + h * (0.08 + i * 0.05) + h * 0.025, d + 0.001, headline)
    elif style == 1:    # diagonal band + circle-ish blob
        rect(x + m, z + h * 0.45, x + w - m, z + h * 0.62, d + 0.001, headline)
        mb.ribbon(arc(cx, z + h * 0.8, h * 0.1, 0, 360, 12), h * 0.012, d + 0.0008, d + 0.0012, "poster_c" if base != "poster_c" else "poster_a", lambda p: P(p[0], p[1], p[2]))
        for i in range(3):
            rect(x + m, z + h * (0.1 + i * 0.07), x + m + w * (0.4 + rnd.random() * 0.4), z + h * (0.1 + i * 0.07) + h * 0.03, d + 0.001, headline)
    else:               # bold vertical stripes + bottom band
        for i in range(3):
            rect(x + m + i * (w - 2 * m) / 3, z + h * 0.35, x + m + (i + 0.6) * (w - 2 * m) / 3, z + h - m, d + 0.001, headline if i % 2 == 0 else "poster_d")
        rect(x + m, z + m, x + w - m, z + h * 0.25, d + 0.001, headline)


# ------------------------------------------------------------------------------------------------ preview / export

def all_mesh_objs(root):
    out = []
    def walk(o):
        if o.type == "MESH":
            out.append(o)
        for c in o.children:
            walk(c)
    walk(root)
    return out


def tri_count(root):
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in all_mesh_objs(root):
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        total += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    return total


def dims(root):
    pts = []
    for o in all_mesh_objs(root):
        pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def preview_views(root, name, views=("front", "front34"), size=(1280, 800), eye=1.6, lens=28, bg=(0.16, 0.16, 0.19),
                  fit=1.0, target_h=None):
    """Workbench preview with a real eye-height 'front' camera (as seen from across the street)."""
    os.makedirs(bsk.OUT_PREVIEW, exist_ok=True)
    lo, hi = dims(root)
    w = hi.x - lo.x
    h = hi.z - lo.z
    cx = (lo.x + hi.x) / 2
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = "BOTH"
    for attr, val in (("show_shadow", True), ("shadow_intensity", 0.4)):
        try:
            setattr(sc.display.shading, attr, val)
        except Exception:
            pass
    try:
        sc.display.light_direction = (0.35, 0.55, 0.75)
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.color = bg
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lens
    cam_d.clip_end = 2000
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    hf = 2 * math.atan(18.0 / lens)
    vf = 2 * math.atan(18.0 * size[1] / size[0] / lens)
    D = max(w / 2 / math.tan(hf / 2), (h * 1.05) / 2 / math.tan(vf / 2)) * 0.95 * fit
    th = h * 0.5 if target_h is None else target_h
    outs = []
    for v in views:
        if v == "front":
            cam.location = (cx, lo.y - D, eye if h > 2.5 else max(h * 0.6, 0.6))
            target = Vector((cx, lo.y, th))
        elif v == "front34":
            cam.location = (cx - D * 0.72, lo.y - D * 0.78, eye + h * 0.22)
            target = Vector((cx, (lo.y + hi.y) / 2 * 0.3 + lo.y * 0.7, th))
        elif v == "back34":
            cam.location = (cx + D * 0.72, hi.y + D * 0.78, eye + h * 0.22)
            target = Vector((cx, hi.y, th))
        elif v == "top":
            cam.location = (cx, (lo.y + hi.y) / 2 - 0.01, h + D)
            target = Vector((cx, (lo.y + hi.y) / 2, 0))
        elif v == "side":
            cam.location = (hi.x + D, (lo.y + hi.y) / 2, eye + h * 0.2)
            target = Vector((hi.x, (lo.y + hi.y) / 2, th))
        elif v == "close":    # closer eye-level look at the ground floor
            cam.location = (cx, lo.y - D * 0.45, eye)
            target = Vector((cx, lo.y, min(th, 2.2)))
        else:
            continue
        look = (target - Vector(cam.location)).to_track_quat("-Z", "Y")
        cam.rotation_euler = look.to_euler()
        p = os.path.join(bsk.OUT_PREVIEW, f"{name}_{v}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cam_d)
    return outs


def recentre_root(root, keep_xy=False):
    """Shift the mesh data of root (+children) so the bbox bottom centre is the origin (object stays at 0,0,0)."""
    lo, hi = dims(root)
    off = Vector((0 if keep_xy else (lo.x + hi.x) / 2, 0 if keep_xy else (lo.y + hi.y) / 2, lo.z))
    for o in all_mesh_objs(root):
        for v in o.data.vertices:
            v.co -= off
        o.data.update()
    return off


MANIFEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest_exterior.json")


def manifest_update(entry):
    data = []
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    data = [e for e in data if e.get("name") != entry["name"]]
    data.append(entry)
    data.sort(key=lambda e: e["name"])
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)


def roles_of(root):
    rs = set()
    for o in all_mesh_objs(root):
        for s in o.material_slots:
            if s.material:
                rs.add(s.material.name)
    return sorted(rs)
