"""lib_kitchen - helpers for the `kitchen` clutter family (dishes, rubbish, cables, small tech).

Built on bsk (do not edit bsk; everything family-specific lives here).
  * smooth curves: catmull()  +  sweep() (own bmesh tube with parallel-transport frames, elliptical sections, per-point radius)
  * rev(): lathe with optional angular radius modulation (crimped caps, ribs) and proper UVs
  * paint(): assign a material role to faces by predicate (labels, stains, liquid levels)
  * deformers: dent(), crush_can(), crinkle(), crumpled_ball(), pillow_bag()
  * finish_prop()/finish_hier(): join -> origin bottom centre -> export -> preview -> manifest entry
"""
import bpy, bmesh, math, random, os, sys, json
from mathutils import Vector, Matrix, Euler, noise
import bsk
from bsk import *

FAMILY = "kitchen"
MANIFEST = []

NEW_ROLES = {
    # drinks cans / metal
    "can_red": ((0.72, 0.07, 0.05), 0.30, 0.55),
    "can_silver": ((0.76, 0.77, 0.78), 0.30, 0.90),
    "can_blue": ((0.07, 0.22, 0.62), 0.30, 0.55),
    "can_black": ((0.05, 0.05, 0.055), 0.30, 0.55),
    "can_green": ((0.08, 0.42, 0.22), 0.30, 0.55),
    "aluminium": ((0.80, 0.81, 0.82), 0.28, 1.0),
    # ceramics / stains / liquids
    "ceramic_red": ((0.60, 0.12, 0.10), 0.20, 0.0),
    "ceramic_black": ((0.06, 0.06, 0.07), 0.20, 0.0),
    "ceramic_green": ((0.25, 0.45, 0.35), 0.20, 0.0),
    "ceramic_cream": ((0.90, 0.86, 0.74), 0.20, 0.0),
    "stain_coffee": ((0.30, 0.18, 0.08), 0.65, 0.0),
    "stain_tea": ((0.55, 0.38, 0.20), 0.65, 0.0),
    "liquid_milk": ((0.92, 0.91, 0.86), 0.10, 0.0),
    "liquid_tea": ((0.35, 0.18, 0.05), 0.10, 0.0),
    "liquid_cola": ((0.07, 0.03, 0.02), 0.08, 0.0),
    "liquid_water": ((0.72, 0.84, 0.90), 0.05, 0.0),
    "liquid_wine": ((0.25, 0.03, 0.06), 0.08, 0.0),
    # food
    "food_beans": ((0.70, 0.24, 0.07), 0.35, 0.0),
    "food_toast": ((0.74, 0.54, 0.28), 0.90, 0.0),
    "food_crust": ((0.42, 0.24, 0.09), 0.90, 0.0),
    "food_chips": ((0.86, 0.66, 0.28), 0.70, 0.0),
    "food_sauce": ((0.58, 0.05, 0.03), 0.25, 0.0),
    "food_cereal": ((0.78, 0.56, 0.26), 0.90, 0.0),
    "food_cheese": ((0.92, 0.74, 0.32), 0.55, 0.0),
    "food_grease": ((0.40, 0.28, 0.12), 0.55, 0.0),
    "food_pepperoni": ((0.55, 0.12, 0.08), 0.6, 0.0),
    "food_rice": ((0.90, 0.88, 0.80), 0.8, 0.0),
    "food_lettuce": ((0.35, 0.60, 0.20), 0.7, 0.0),
    # labels / print
    "label_paper": ((0.90, 0.88, 0.80), 0.80, 0.0),
    "label_red": ((0.70, 0.08, 0.06), 0.45, 0.0),
    "label_green": ((0.10, 0.45, 0.20), 0.45, 0.0),
    "label_blue": ((0.10, 0.30, 0.70), 0.45, 0.0),
    "label_black": ((0.05, 0.05, 0.05), 0.45, 0.0),
    "print_red": ((0.72, 0.12, 0.10), 0.85, 0.0),
    # wrappers / bags / plastics
    "foil_crisps_red": ((0.68, 0.10, 0.08), 0.35, 0.55),
    "foil_crisps_blue": ((0.10, 0.25, 0.62), 0.35, 0.55),
    "foil_purple": ((0.36, 0.10, 0.46), 0.35, 0.55),
    "foil_gold": ((0.80, 0.62, 0.25), 0.30, 0.85),
    "plastic_bag_black": ((0.03, 0.03, 0.035), 0.28, 0.0),
    "plastic_clear": ((0.80, 0.85, 0.88), 0.12, 0.0),
    "plastic_cream": ((0.90, 0.88, 0.80), 0.40, 0.0),
    "plastic_orange": ((0.85, 0.40, 0.08), 0.40, 0.0),
    "cable_white": ((0.88, 0.88, 0.86), 0.60, 0.0),
    "cable_black": ((0.05, 0.05, 0.05), 0.60, 0.0),
    "cable_red": ((0.60, 0.08, 0.06), 0.60, 0.0),
    "velcro_black": ((0.10, 0.10, 0.11), 0.95, 0.0),
    "paper_tissue": ((0.94, 0.93, 0.90), 0.95, 0.0),
    "paper_cup": ((0.92, 0.90, 0.85), 0.75, 0.0),
    "paper_print": ((0.88, 0.86, 0.80), 0.85, 0.0),
    "plastic_bin_grey": ((0.40, 0.41, 0.42), 0.45, 0.0),
}
for _k, _v in NEW_ROLES.items():
    MATERIALS.setdefault(_k, _v)


# ------------------------------------------------------------------------------------------------ basics

def smoothstep(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    t = (x - a) / (b - a)
    return t * t * (3 - 2 * t)


def V(*a):
    return Vector(a)


def obj_from_bm(bm, name, roles):
    return bsk._obj_from_bm(bm, name, roles)


def catmull(pts, n=8, closed=False):
    """Catmull-Rom sampling of a point list -> dense smooth polyline (list of Vector)."""
    pts = [Vector(p) for p in pts]
    if closed:
        P = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * (t * t)
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * (t * t * t)))
    if not closed:
        out.append(P[-2])
    return out


def sweep(name, pts, radius, role, segments=10, caps=True, closed=False, rx=1.0, ry=1.0, twist=0.0,
          uv_scale=1.0, smooth_angle=60, up_hint=None):
    """Tube along a dense polyline with parallel-transport frames (no facet kinks).
    radius: float | list per point | callable(t in 0..1)->r. rx/ry scale the section (flat straps, bands)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tans = []
    for i in range(n):
        if closed:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        t = b - a
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    t0 = tans[0]
    ref = Vector(up_hint) if up_hint is not None else (Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0)))
    nrm = (ref - t0 * ref.dot(t0))
    nrm = nrm.normalized() if nrm.length > 1e-9 else Vector((1, 0, 0))
    frames = []
    for i in range(n):
        t = tans[i]
        if i > 0:
            axis = tans[i - 1].cross(t)
            if axis.length > 1e-9:
                ang = math.acos(max(-1.0, min(1.0, tans[i - 1].dot(t))))
                nrm = Matrix.Rotation(ang, 3, axis.normalized()) @ nrm
            nrm = (nrm - t * nrm.dot(t)).normalized()
        frames.append((nrm, t.cross(nrm)))
    lens = [0.0]
    for i in range(1, n):
        lens.append(lens[-1] + (pts[i] - pts[i - 1]).length)
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        if callable(radius):
            r = radius(i / max(n - 1, 1))
        elif isinstance(radius, (list, tuple)):
            r = radius[i]
        else:
            r = radius
        nr, bn = frames[i]
        ring = []
        for k in range(segments):
            a = 2 * math.pi * k / segments + twist * i
            ring.append(bm.verts.new(p + nr * (math.cos(a) * r * rx) + bn * (math.sin(a) * r * ry)))
        rings.append(ring)
    uvl = bm.loops.layers.uv.new("UVMap")
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(segments):
            j = (k + 1) % segments
            f = bm.faces.new((a[k], a[j], b[j], b[k]))
            v0 = lens[i] / uv_scale
            v1 = (lens[i + 1] if i + 1 < n else lens[-1] + (pts[0] - pts[-1]).length) / uv_scale
            for lp, (u, v) in zip(f.loops, ((k / segments, v0), ((k + 1) / segments, v0), ((k + 1) / segments, v1), (k / segments, v1))):
                lp[uvl].uv = (u, v)
    if caps and not closed:
        f0 = bm.faces.new(list(reversed(rings[0])))
        f1 = bm.faces.new(rings[-1])
        for f in (f0, f1):
            for lp in f.loops:
                lp[uvl].uv = (0.5 + lp.vert.co.x, 0.5 + lp.vert.co.y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bm(bm, name, [role])
    shade(ob, True, angle=smooth_angle)
    return ob


def rev(name, profile, role, segments=32, rmod=None, smooth=True, center=(0, 0, 0), smooth_angle=40, uv_v_scale=1.0):
    """Lathe about Z. profile=[(r,z),...]; rmod(theta, ring_i, r, z)->r' for ribs/crimps. r<=0 closes the end."""
    bm = bmesh.new()
    rings = []
    for ri, (r, z) in enumerate(profile):
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            ring = []
            for i in range(segments):
                th = 2 * math.pi * i / segments
                rr = rmod(th, ri, r, z) if rmod else r
                ring.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), z)))
            rings.append(ring)
    uvl = bm.loops.layers.uv.new("UVMap")
    # v coordinate = arc length along profile
    arc = [0.0]
    for (r0, z0), (r1, z1) in zip(profile[:-1], profile[1:]):
        arc.append(arc[-1] + math.hypot(r1 - r0, z1 - z0))
    for ri, (a, b) in enumerate(zip(rings[:-1], rings[1:])):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(segments):
            j = (i + 1) % segments
            u0, u1 = i / segments, (i + 1) / segments
            if len(a) == 1:
                f = bm.faces.new((a[0], b[j], b[i]))
                uvs = ((0.5 * (u0 + u1), arc[ri]), (u1, arc[ri + 1]), (u0, arc[ri + 1]))
            elif len(b) == 1:
                f = bm.faces.new((a[i], a[j], b[0]))
                uvs = ((u0, arc[ri]), (u1, arc[ri]), (0.5 * (u0 + u1), arc[ri + 1]))
            else:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                uvs = ((u0, arc[ri]), (u1, arc[ri]), (u1, arc[ri + 1]), (u0, arc[ri + 1]))
            for lp, (u, v) in zip(f.loops, uvs):
                lp[uvl].uv = (u, v / uv_v_scale)
    if profile[0] == profile[-1]:          # closed profile (torus-like pads/rings): weld the seam
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bm(bm, name, [role])
    ob.location = center
    shade(ob, smooth, angle=smooth_angle)
    return ob


def paint(ob, role, pred):
    """Assign `role` to every polygon where pred(center, normal) is true (local coords)."""
    me = ob.data
    m = mat(role)
    idx = me.materials.find(m.name)
    if idx < 0:
        me.materials.append(m)
        idx = len(me.materials) - 1
    for p in me.polygons:
        if pred(p.center, p.normal):
            p.material_index = idx
    return ob


def zband(z0, z1):
    return lambda c, n: z0 <= c.z <= z1


def rbox(name, size, role, center=(0, 0, 0), bevel=0.003, segments=2, origin="center"):
    """bsk.box with sane defaults (bevelled box)."""
    return box(name, size, role, center=center, bevel=bevel, segments=segments, origin=origin)


def disc(name, r, z, role, segments=32, r_in=0.0):
    """Flat disc or annulus at height z (liquid surfaces, films)."""
    if r_in > 0:
        return rev(name, [(r_in, z), (r, z)], role, segments=segments)
    return rev(name, [(0, z), (r, z)], role, segments=segments)


def ellipsoid(name, rx, ry, rz, role, center=(0, 0, 0), subdiv=2, rot=(0, 0, 0), seed=None, bump=0.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        v.co.x *= rx
        v.co.y *= ry
        v.co.z *= rz
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            c = lp.vert.co
            lp[uvl].uv = ((math.atan2(c.y, c.x) / (2 * math.pi)) % 1.0, (c.z / (2 * rz)) + 0.5)
    ob = obj_from_bm(bm, name, [role])
    if bump > 0 and seed is not None:
        displace_noise(ob, strength=bump, scale=max(rx, ry, rz) * 0.9, seed=seed)
    ob.location = center
    ob.rotation_euler = rot
    shade(ob, True, angle=60)
    return ob


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ------------------------------------------------------------------------------------------------ deformers

def dent(ob, point, radius, depth, toward_axis=True):
    """Push vertices near `point` (local) inward with smooth falloff (dents in cans/bins)."""
    me = ob.data
    P = Vector(point)
    for v in me.vertices:
        d = (v.co - P).length
        if d < radius:
            w = 1.0 - smoothstep(0.0, 1.0, d / radius)
            if toward_axis:
                dirn = Vector((-v.co.x, -v.co.y, 0.0))
                dirn = dirn.normalized() if dirn.length > 1e-6 else Vector((0, 0, 0))
            else:
                dirn = -v.normal
            v.co += dirn * (depth * w)
    me.update()


def crush_can(ob, k=0.5, lean=0.12, seed=0, amp=0.10):
    """Vertically crush a lathe can: compress Z, buckle folds around the body, lean a little."""
    rnd = random.Random(seed)
    ph = rnd.random() * 6.28
    me = ob.data
    zmax = max(v.co.z for v in me.vertices)
    for v in me.vertices:
        z = v.co.z
        t = z / zmax
        r = math.hypot(v.co.x, v.co.y)
        th = math.atan2(v.co.y, v.co.x)
        w = smoothstep(0.06, 0.22, t) * (1 - smoothstep(0.80, 0.94, t))
        if r > 1e-6:
            # sharp accordion folds (abs-sin creases) + a one-sided collapse + noise
            crease = 1 - 2 * abs(math.sin(2.5 * th + 6 * t * math.pi + ph))
            fold = 1 + w * (amp * crease + amp * 0.5 * math.sin(3 * th - 9 * t * math.pi + ph * 2)
                            - amp * 1.6 * max(0.0, math.cos(th - ph)) ** 2 * math.sin(t * math.pi)
                            + amp * 0.9 * math.sin(t * math.pi) ** 2
                            + amp * 0.5 * noise.noise(Vector((v.co.x * 30, v.co.y * 30, z * 30 + ph))))
            r2 = r * fold
            v.co.x = r2 * math.cos(th)
            v.co.y = r2 * math.sin(th)
        v.co.z = z * k * (1 - 0.08 * w * (1 + math.cos(th - ph)))
        v.co.x += lean * v.co.z * (1 - 0.5 * t)
    # tilt the top end (lid) over a bit, like a stamped can
    ztop = zmax * k
    R = Matrix.Rotation(math.radians(14), 3, Vector((math.cos(ph + 1.2), math.sin(ph + 1.2), 0)))
    for v in me.vertices:
        t = v.co.z / ztop
        wt = smoothstep(0.55, 0.95, t)
        if wt > 0:
            P = Vector((0, 0, ztop * 0.75))
            q = R @ (v.co - P) + P
            v.co = v.co.lerp(q, wt)
    me.update()


def poly_prism(name, pts2d, z0, z1, role):
    """Extruded polygon (pizza slice, flaps...)."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts2d]
    top = [bm.verts.new((x, y, z1)) for x, y in pts2d]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    n = len(bot)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bm(bm, name, [role])
    shade(ob, True, angle=40)
    uv_box(ob, 1.0)
    return ob


def quad(name, corners, role, thickness=0.0, cuts=0):
    """Single quad (or n-gon) sheet from world corners; optional solidify + subdivision for painting."""
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(c)) for c in corners]
    bm.faces.new(vs)
    if cuts > 0:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bm(bm, name, [role])
    shade(ob, True, angle=40)
    uv_box(ob, 1.0)
    if thickness > 0:
        solidify(ob, thickness, offset=-1.0)
    return ob


def superellipse(w, d, n=3.0, segments=32):
    """Rounded-rectangle outline points (half sizes w, d) in XY."""
    pts = []
    for i in range(segments):
        t = 2 * math.pi * i / segments
        c, s = math.cos(t), math.sin(t)
        pts.append((w * math.copysign(abs(c) ** (2 / n), c), d * math.copysign(abs(s) ** (2 / n), s)))
    return pts


def loft(name, rings, role, close_bottom=True, close_top=False, smooth_angle=40):
    """Loft a list of rings (each a list of 3D points, same count) into a surface (trays, cartons)."""
    bm = bmesh.new()
    R = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(R[0])
    for a, b in zip(R[:-1], R[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if close_bottom:
        bm.faces.new(list(reversed(R[0])))
    if close_top:
        bm.faces.new(R[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bm(bm, name, [role])
    shade(ob, True, angle=smooth_angle)
    uv_box(ob, 1.0)
    return ob


def twist_x(ob, deg_per_m, squeeze=0.0):
    """Twist the mesh about its local X axis (scrunched wrapper), optionally pinching toward the axis."""
    me = ob.data
    for v in me.vertices:
        a = math.radians(deg_per_m) * v.co.x
        y, z = v.co.y, v.co.z
        k = 1 - squeeze * abs(math.sin(a))
        v.co.y = (y * math.cos(a) - z * math.sin(a)) * k
        v.co.z = (y * math.sin(a) + z * math.cos(a)) * k
    me.update()


def crinkle(ob, strength=0.004, scale=0.03, seed=0, octaves=3, along_normal=True, ridge=0.5, mask=None):
    """Multi-octave noise crinkle (paper, foil, bags). ridge adds sharp creases. mask(co)->0..1 weight."""
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 100, rnd.random() * 100, rnd.random() * 100))
    me = ob.data
    for v in me.vertices:
        n = 0.0
        a = 1.0
        s = scale
        for o in range(octaves):
            n += a * noise.noise(v.co / s + off * (o + 1))
            a *= 0.5
            s *= 0.5
        if ridge > 0:
            n -= ridge * abs(noise.noise(v.co / (scale * 0.7) + off * 7))
        w = mask(v.co) if mask else 1.0
        dirn = v.normal if along_normal else Vector((0, 0, 1))
        v.co += dirn * (n * strength * w)
    me.update()


def crumpled_ball(name, r, role, seed=0, amp=0.32, subdiv=4, squash=0.82):
    """Crumpled paper ball: icosphere with lumpy + creased displacement, slightly flattened."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            c = lp.vert.co
            lp[uvl].uv = ((math.atan2(c.y, c.x) / (2 * math.pi)) % 1.0, c.z / (2 * r) + 0.5)
    ob = obj_from_bm(bm, name, [role])
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
    me = ob.data
    for v in me.vertices:
        p = v.co
        n1 = noise.noise(p / (r * 1.1) + off)
        n2 = noise.noise(p / (r * 0.45) + off * 2)
        n3 = noise.noise(p / (r * 0.22) + off * 3)
        rid = abs(noise.noise(p / (r * 0.7) + off * 5))
        f = 1 + amp * (0.55 * n1 + 0.3 * n2 + 0.15 * n3) - amp * 0.7 * rid
        v.co = p * f
        v.co.z *= squash
    me.update()
    shade(ob, True, angle=28)
    zmin = min(v.co.z for v in me.vertices)
    ob.location.z = -zmin
    return ob


def sheet(name, w, h, nx, ny, role):
    """Flat subdivided grid in XY (w along X, h along Y) centred, z=0, with UVs."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
    for v in bm.verts:
        v.co.x *= w
        v.co.y *= h
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x / w + 0.5, lp.vert.co.y / h + 0.5)
    ob = obj_from_bm(bm, name, [role])
    shade(ob, True, angle=35)
    return ob


def pillow_bag(name, w, h, puff, nx, ny, role, seam=0.012, seed=0, crinkle_amp=0.004, rot=(0, 0, 0)):
    """Closed pillow (crisp packet / sweet wrapper): two grids sharing the seam, with flat sealed strips at the
    short ends, puffed in the middle and crinkled. w along X (seams at +-X ends), h along Y."""
    bm = bmesh.new()
    verts = {}
    for side in (1, -1):
        for i in range(nx + 1):
            for j in range(ny + 1):
                u, vv = i / nx, j / ny
                x = (u - 0.5) * w
                y = (vv - 0.5) * h
                ex = smoothstep(0.0, 1.0, min(abs(u) * w, (1 - u) * w) / (w * 0.5 - seam) if w * 0.5 - seam > 0 else 1)
                ex = smoothstep(0.0, 0.5, (min(u, 1 - u) * w - seam) / (w * 0.5 - seam))
                pz = puff * math.sin(math.pi * vv) ** 0.8 * ex ** 0.9
                z = pz * side
                if side == 1 or (0 < j < ny and ex > 1e-6):
                    verts[(side, i, j)] = bm.verts.new((x, y, z))
                else:
                    verts[(side, i, j)] = verts[(1, i, j)]
    uvl = bm.loops.layers.uv.new("UVMap")
    for side in (1, -1):
        for i in range(nx):
            for j in range(ny):
                q = [verts[(side, i, j)], verts[(side, i + 1, j)], verts[(side, i + 1, j + 1)], verts[(side, i, j + 1)]]
                if side == -1:
                    q.reverse()
                if len(set(q)) < 3:
                    continue
                try:
                    f = bm.faces.new(q) if len(set(q)) == 4 else bm.faces.new(list(dict.fromkeys(q)))
                except ValueError:
                    continue
                for lp in f.loops:
                    lp[uvl].uv = (lp.vert.co.x / w + 0.5, (lp.vert.co.y / h + 0.5) * 0.5 + (0.5 if side == -1 else 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bm(bm, name, [role])
    shade(ob, True, angle=40)
    if crinkle_amp > 0:
        crinkle(ob, strength=crinkle_amp, scale=w * 0.22, seed=seed, octaves=3, ridge=0.6)
    ob.rotation_euler = rot
    return ob


# ------------------------------------------------------------------------------------------------ placement

def place(ob, loc=(0, 0, 0), rot=(0, 0, 0), deg=True):
    ob.location = Vector(loc)
    ob.rotation_euler = Euler([math.radians(a) for a in rot] if deg else rot)
    return ob


def align_y(ob, loc, direction, roll=0.0):
    """Put ob at loc with its local +Y pointing along `direction` (plugs on cable ends)."""
    d = Vector(direction).normalized()
    q = d.to_track_quat("Y", "Z")
    ob.rotation_euler = (q @ Euler((0, roll, 0)).to_quaternion()).to_euler()
    ob.location = Vector(loc)
    return ob


def rot_about(ob, pivot, axis, angle_deg):
    """Rotate an object (its transform) about a world pivot/axis."""
    bpy.context.view_layer.update()          # matrix_world is stale right after creation/location edits
    R = Matrix.Rotation(math.radians(angle_deg), 4, Vector(axis))
    T = Matrix.Translation(Vector(pivot))
    ob.matrix_world = T @ R @ T.inverted() @ ob.matrix_world
    return ob


def apply_xform(ob):
    """Bake the object transform into the mesh (so later lathe-space deformers see world coords)."""
    bpy.context.view_layer.update()
    me = ob.data
    M = ob.matrix_world.copy()
    for v in me.vertices:
        v.co = M @ v.co
    me.update()
    ob.matrix_world = Matrix.Identity(4)
    return ob


def merge(objs, name):
    """Join objects into one mesh in WORLD space (fresh identity carrier object), applying modifiers."""
    objs = [o for o in objs if o is not None and o.type == "MESH"]
    me = bpy.data.meshes.new(name)
    carrier = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(carrier)
    ob = join([carrier] + objs, name)
    return ob


def drop_to_floor(ob):
    lo, hi = bounds(ob)
    ob.location.z -= lo.z
    return ob


def lowest_z(objs):
    zs = []
    for o in objs:
        if o.type == "MESH":
            lo, hi = bounds(o)
            zs.append(lo.z)
    return min(zs)


def settle(objs, z=0.0):
    """Translate a group so the lowest point sits at z."""
    dz = z - lowest_z(objs)
    for o in objs:
        o.location.z += dz


# ------------------------------------------------------------------------------------------------ finish / export / manifest

def _roles_of(obs):
    rs = set()
    for o in obs:
        if o.type == "MESH":
            for s in o.material_slots:
                if s.material:
                    rs.add(s.material.name.split(".")[0])
    return sorted(rs)


def _all_meshes(root):
    out = []
    def walk(o):
        if o.type == "MESH":
            out.append(o)
        for c in o.children:
            walk(c)
    walk(root)
    return out


def _record(root, name, category, notes, variant_of=None, extra=None):
    meshes = _all_meshes(root)
    pts = []
    for m in meshes:
        pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    dims = [round(hi.x - lo.x, 4), round(hi.y - lo.y, 4), round(hi.z - lo.z, 4)]
    entry = {"name": name, "file": f"Assets/Bedsit/Art/Models/{FAMILY}/{name}.fbx", "category": category,
             "dims_m": dims, "tris": sum(tri_count(m) for m in meshes), "roles": _roles_of(meshes),
             "variant_of": variant_of, "notes": notes}
    if extra:
        entry.update(extra)
    MANIFEST.append(entry)
    print(f"[kitchen] {name}: dims={dims} tris={entry['tris']} roles={entry['roles']}")
    return entry


def finish_prop(objs, name, category, notes, variant_of=None, views=("front34", "back34"), export=True, extra=None):
    """Join parts into one mesh, origin = bottom centre, export + preview + manifest."""
    ob = merge(objs, name)
    set_origin_bottom(ob)
    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    entry = _record(ob, name, category, notes, variant_of, extra)
    if export:
        export_fbx(ob, FAMILY, name)
    if views:
        preview(ob, name, views=views)
    park(ob)
    return ob


def finish_hier(children, name, category, notes, variant_of=None, views=("front34", "back34"), export=True, extra=None):
    """children: list of (child_name, [objs], pivot_world or None). Root empty at bottom centre of everything.
    A child's object origin is placed at its pivot (hinge) so it can be rotated in Unity."""
    kids = []
    for cname, objs, pivot in children:
        ob = merge(objs, cname)
        if pivot is not None:
            P = Vector(pivot)
            for v in ob.data.vertices:
                v.co -= P
            ob.location = P
        kids.append(ob)
    bpy.context.view_layer.update()
    pts = []
    for k in kids:
        pts += [k.matrix_world @ Vector(c) for c in k.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    C = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for k in kids:
        k.location -= C
        k.parent = root
    bpy.context.view_layer.update()
    entry = _record(root, name, category, notes, variant_of, extra)
    if export:
        export_fbx(root, FAMILY, name)
    if views:
        preview(root, name, views=views)
    park(root)
    return root


FINISHED = []


def park(root):
    """After export+preview: move the prop to a parking grid and hide it from later previews
    (preview() renders the whole scene). Contact sheet un-hides everything at the end."""
    i = len(FINISHED)
    FINISHED.append(root)
    root.location = Vector((3.0 + 0.7 * (i % 8), 3.0 + 0.7 * (i // 8), 0.0))
    for m in _all_meshes(root):
        m.hide_render = True
    root.hide_render = True


def contact_sheet(name="kitchen_contact"):
    for r in FINISHED:
        r.hide_render = False
        for m in _all_meshes(r):
            m.hide_render = False
    if FINISHED:
        preview(FINISHED, name, size=(2400, 1600), views=("front34", "top"), fit=0.95)


def write_manifest():
    p = os.path.join(ROOT, "Art", "Source", "blender", f"manifest_{FAMILY}.json")
    # merge with an existing manifest so partial (--only) runs do not drop the other props
    props = []
    if os.path.exists(p):
        try:
            with open(p) as f:
                props = json.load(f).get("props", [])
        except Exception:
            props = []
    built = {e["name"]: e for e in MANIFEST}
    props = [built.pop(e["name"], e) for e in props] + list(built.values())
    roles_used = sorted({r for e in props for r in e["roles"]})
    data = {"family": FAMILY,
            "conventions": "1 unit = 1 m; origin = bottom centre; front = -Y (Blender). Roles are bsk material role names. "
                           "new_roles: role -> [r, g, b, roughness, metallic] (fallback look; Unity library overrides).",
            "new_roles": {k: list(v[0]) + [v[1], v[2]] for k, v in NEW_ROLES.items() if k in roles_used},
            "props": props}
    with open(p, "w") as f:
        json.dump(data, f, indent=1)
    print("[kitchen] manifest ->", p)
    return p


def hide_all(objs):
    for o in objs:
        o.hide_render = True
        o.hide_viewport = True
