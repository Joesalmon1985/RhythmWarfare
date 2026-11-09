"""lib_furniture - helpers for the `furniture` family (built on bsk; does NOT modify bsk.py).

Conventions: metres, +Z up, FRONT faces -Y, origin bottom centre (doors hinge-axis origin, drawers front-bottom-centre).
"""
import bpy, bmesh, math, random, os, sys, json
from mathutils import Vector, Matrix, Euler

sys.path.insert(0, os.path.dirname(__file__))
import bsk
from bsk import *

# ------------------------------------------------------------------------------------------------ extra roles
NEW_ROLES = {
    "laminate_oak": ((0.66, 0.50, 0.32), 0.45, 0.0),        # cheap oak-effect melamine
    "laminate_white": ((0.86, 0.85, 0.80), 0.40, 0.0),      # white melamine carcass
    "laminate_grey": ((0.42, 0.41, 0.40), 0.45, 0.0),       # grey/anthracite melamine
    "laminate_edge": ((0.56, 0.40, 0.24), 0.50, 0.0),       # ABS edge banding (oak)
    "laminate_edge_white": ((0.78, 0.77, 0.72), 0.50, 0.0), # ABS edge banding (white, yellowed)
    "hardboard_back": ((0.55, 0.42, 0.28), 0.85, 0.0),      # 3 mm hardboard back panel
    "mdf_raw": ((0.62, 0.52, 0.40), 0.90, 0.0),             # drawer boxes
    "worktop_laminate": ((0.28, 0.26, 0.25), 0.35, 0.0),    # dark kitchen worktop
    "fabric_office_grey": ((0.20, 0.20, 0.22), 0.95, 0.0),
    "fabric_office_worn": ((0.30, 0.30, 0.31), 0.98, 0.0),  # shiny/bald fabric patches
    "stitch_thread": ((0.10, 0.10, 0.10), 0.9, 0.0),
    "lamp_shade": ((0.93, 0.87, 0.74), 0.90, 0.0),          # emissive-ish in Unity (fabric/paper shade)
    "bulb_warm": ((1.00, 0.86, 0.55), 0.20, 0.0),           # emissive in Unity
    "mirror_glass": ((0.80, 0.85, 0.88), 0.02, 1.0),
    "print_a": ((0.25, 0.45, 0.60), 0.80, 0.0),             # framed print textures (Unity)
    "print_b": ((0.82, 0.38, 0.20), 0.80, 0.0),
    "print_c": ((0.16, 0.16, 0.19), 0.80, 0.0),
    "radiator_white": ((0.90, 0.90, 0.87), 0.35, 0.0),
    "upvc_white": ((0.93, 0.93, 0.91), 0.30, 0.0),
    "appliance_white": ((0.90, 0.90, 0.88), 0.30, 0.0),
    "metal_copper": ((0.72, 0.45, 0.30), 0.30, 1.0),
    "metal_chrome": ((0.85, 0.86, 0.88), 0.12, 1.0),
    "sticker_a": ((0.95, 0.30, 0.55), 0.50, 0.0),           # rave flyer pink
    "sticker_b": ((0.20, 0.80, 0.85), 0.50, 0.0),           # cyan
    "sticker_c": ((0.95, 0.85, 0.20), 0.50, 0.0),           # yellow
    "scuff_dark": ((0.28, 0.24, 0.20), 0.85, 0.0),          # scuff / chipped laminate showing chipboard
    "scuff_light": ((0.74, 0.70, 0.62), 0.85, 0.0),         # worn pale patch
    "clock_face": ((0.95, 0.94, 0.90), 0.60, 0.0),
    "magnet_red": ((0.85, 0.12, 0.10), 0.40, 0.0),
    "magnet_yellow": ((0.95, 0.80, 0.15), 0.40, 0.0),
    "magnet_blue": ((0.15, 0.35, 0.85), 0.40, 0.0),
    "wire_green": ((0.08, 0.22, 0.10), 0.60, 0.0),
    "paint_wall_magnolia": ((0.90, 0.86, 0.76), 0.9, 0.0),
    "cotton_hoodie_grey": ((0.55, 0.55, 0.57), 0.97, 0.0),
    "plastic_cream": ((0.88, 0.85, 0.75), 0.40, 0.0),
}
MATERIALS.update(NEW_ROLES)

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
RX90 = (math.pi / 2, 0, 0)     # local +Z -> world -Y  (cylinder sticks out of a front face)
RXm90 = (-math.pi / 2, 0, 0)   # local +Z -> world +Y
RY90 = (0, math.pi / 2, 0)     # local +Z -> world +X
RYm90 = (0, -math.pi / 2, 0)   # local +Z -> world -X


# ------------------------------------------------------------------------------------------------ basic builders

def _bm_cube(size):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    return bm


def panel(name, size, role, center, edge_role=None, bevel=0.002, thin_axis=None, segments=2):
    """A board. Narrow (edge) faces get the edge-banding material if edge_role is given."""
    bm = _bm_cube(size)
    bm.normal_update()
    if thin_axis is None:
        thin_axis = min(range(3), key=lambda i: size[i])
    roles = [role] + ([edge_role] if edge_role else [])
    if edge_role:
        for f in bm.faces:
            if abs(f.normal[thin_axis]) < 0.5:
                f.material_index = 1
    ob = bsk._obj_from_bm(bm, name, roles)
    ob.location = center
    shade(ob, False)
    if bevel > 0:
        add_bevel(ob, bevel, segments)
    uv_box(ob)
    return ob


def bar(name, p0, p1, radius, role, segments=16, bevel=0.0):
    """Cylinder from point p0 to p1 (any orientation)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    ob = cylinder(name, radius, L, role, segments=segments, bevel=bevel, origin="center")
    ob.location = (p0 + p1) / 2
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return ob


def sweep(name, rings, role, close_loop=False, cap=True, smooth=True, roles=None):
    """Skin a list of rings (each a list of Vector of equal length) with quads."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    pairs = list(zip(vr[:-1], vr[1:]))
    if close_loop:
        pairs.append((vr[-1], vr[0]))
    for a, b in pairs:
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap and not close_loop:
        bm.faces.new(vr[0][::-1])
        bm.faces.new(vr[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bsk._obj_from_bm(bm, name, roles or [role])
    shade(ob, smooth)
    uv_box(ob)
    return ob


def profile_extrude(name, profile_yz, x0, x1, role, bevel=0.0, smooth=False):
    """Extrude a closed 2D profile [(y,z),...] along X from x0 to x1 (skirting, cornice, architrave...)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x0, y, z)) for (y, z) in profile_yz]
    f = bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    verts = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=(x1 - x0, 0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bsk._obj_from_bm(bm, name, [role])
    shade(ob, smooth)
    if bevel > 0:
        add_bevel(ob, bevel, 2)
    uv_box(ob)
    return ob


def frame_sweep(name, w, h, profile, role, center=(0, 0, 0), bevel=0.0, smooth=False):
    """Mitred rectangular frame in the XZ plane (front = -Y). profile = closed list of (inset, y):
    inset = distance inward from the outer rectangle edge, y = depth (negative toward viewer)."""
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    rings = []
    for sx, sz in corners:
        rings.append([Vector((sx * (w / 2 - ins), y, sz * (h / 2 - ins))) for (ins, y) in profile])
    ob = sweep(name, rings, role, close_loop=True, smooth=smooth)
    ob.location = center
    if bevel > 0:
        add_bevel(ob, bevel, 2)
    return ob


def plane_quad(name, center, size, axis, role, sign=-1, offset=0.0):
    """Single quad facing along `axis` ('x','y','z') in direction sign; size=(a,b) in the other two axes."""
    cx, cy, cz = center
    a, b = size[0] / 2, size[1] / 2
    bm = bmesh.new()
    if axis == "y":
        y = cy + sign * offset
        pts = [(cx - a, y, cz - b), (cx + a, y, cz - b), (cx + a, y, cz + b), (cx - a, y, cz + b)]
    elif axis == "x":
        x = cx + sign * offset
        pts = [(x, cy - a, cz - b), (x, cy + a, cz - b), (x, cy + a, cz + b), (x, cy - a, cz + b)]
    else:
        z = cz + sign * offset
        pts = [(cx - a, cy - b, z), (cx + a, cy - b, z), (cx + a, cy + b, z), (cx - a, cy + b, z)]
    vs = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(vs)
    bm.normal_update()
    want = Vector([sign if ax == axis else 0 for ax in "xyz"])
    if f.normal.dot(want) < 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    ob = bsk._obj_from_bm(bm, name, [role])
    shade(ob, False)
    uv_box(ob)
    return ob


def decal(name, center, size, axis, role, sign=-1, offset=0.0008, irregular=True, seed=0, rot=0.0, n=9):
    """Scuff / sticker: a thin polygon hovering 0.8 mm off a surface. irregular -> ragged scuff shape."""
    rnd = random.Random(seed)
    cx, cy, cz = center
    a, b = size[0] / 2, size[1] / 2
    pts2 = []
    if irregular:
        for i in range(n):
            t = 2 * math.pi * i / n
            r = 0.6 + 0.4 * rnd.random()
            pts2.append((a * r * math.cos(t), b * r * math.sin(t)))
    else:
        pts2 = [(-a, -b), (a, -b), (a, b), (-a, b)]
    c, s = math.cos(rot), math.sin(rot)
    pts2 = [(u * c - v * s, u * s + v * c) for (u, v) in pts2]
    bm = bmesh.new()
    pts = []
    for (u, v) in pts2:
        if axis == "y":
            pts.append((cx + u, cy + sign * offset, cz + v))
        elif axis == "x":
            pts.append((cx + sign * offset, cy + u, cz + v))
        else:
            pts.append((cx + u, cy + v, cz + sign * offset))
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    bm.normal_update()
    want = Vector([sign if ax == axis else 0 for ax in "xyz"])
    if f.normal.dot(want) < 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    ob = bsk._obj_from_bm(bm, name, [role])
    shade(ob, False)
    uv_box(ob)
    return ob


def sticker(name, center, size, axis, role, sign=-1, rot=0.0, offset=0.0008):
    return decal(name, center, size, axis, role, sign=sign, offset=offset, irregular=False, rot=rot)


def smooth_pts(pts, n=6, closed=False):
    """Catmull-Rom resample of a polyline -> n points per segment (for tube())."""
    pts = [Vector(p) for p in pts]
    if closed:
        P = pts[-1:] + pts + pts[:2]
        segs = len(pts)
    else:
        P = [pts[0]] + pts + [pts[-1]]
        segs = len(pts) - 1
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(pts[-1])
    return out


def wire(name, pts, radius, role, n=6, segments=12, closed=False, smooth_path=True):
    """Smooth round tube along points (cables, hooks, hanger wire, lamp arcs). Returns a mesh object."""
    if smooth_path:
        pts = smooth_pts(pts, n, closed)
    if closed:
        pts = pts + [pts[0]]
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = max(1, segments // 4 - 1)
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (v[0], v[1], v[2], 1)
    sp.use_smooth = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat(role))
    ob = to_mesh(ob)
    shade(ob, True, angle=60)
    uv_box(ob)
    return ob


def torus(name, center, R, r, role, seg_major=32, seg_minor=10, axis="z"):
    rings = []
    for i in range(seg_minor):
        a = 2 * math.pi * i / seg_minor
        ring = []
        for j in range(seg_major):
            t = 2 * math.pi * j / seg_major
            rr = R + r * math.cos(a)
            ring.append(Vector((rr * math.cos(t), rr * math.sin(t), r * math.sin(a))))
        rings.append(ring)
    # rings here are minor-circle slices; transpose so sweep connects major rings
    rings_t = [[rings[i][j] for i in range(seg_minor)] for j in range(seg_major)]
    ob = sweep(name, rings_t, role, close_loop=True, smooth=True)
    ob.location = center
    if axis == "y":
        ob.rotation_euler = RX90
    elif axis == "x":
        ob.rotation_euler = RY90
    return ob


# ------------------------------------------------------------------------------------------------ furniture parts

def knob(name, center, r=0.015, role="wood_dark", axis_rot=RX90, length=0.028):
    """Turned knob sticking out of a front face (-Y) at `center` (point on the face)."""
    prof = [(0, 0), (r * 0.45, 0), (r * 0.42, length * 0.35), (r * 0.7, length * 0.5), (r, length * 0.68),
            (r * 0.9, length * 0.88), (r * 0.55, length), (0, length)]
    ob = lathe(name, prof, role, segments=20, center=center)
    ob.rotation_euler = axis_rot
    return ob


def bar_handle(name, center, length, role="metal_steel", axis="x", standoff=0.032, r=0.005, post_r=0.0045):
    """D / bar handle on a front face (-Y). center = point on the face (centre of the handle)."""
    cx, cy, cz = center
    objs = []
    for s in (-1, 1):
        if axis == "x":
            p = (cx + s * (length / 2 - 0.012), cy, cz)
        else:
            p = (cx, cy, cz + s * (length / 2 - 0.012))
        post = cylinder(f"{name}_post{s}", post_r, standoff, role, segments=12, bevel=0.0, center=p)
        post.rotation_euler = RX90
        objs.append(post)
    if axis == "x":
        b = bar(f"{name}_bar", (cx - length / 2, cy - standoff + r, cz), (cx + length / 2, cy - standoff + r, cz), r, role, segments=14, bevel=0.002)
    else:
        b = bar(f"{name}_bar", (cx, cy - standoff + r, cz - length / 2), (cx, cy - standoff + r, cz + length / 2), r, role, segments=14, bevel=0.002)
    objs.append(b)
    return objs


def screw_holes(name, center, spacing, axis="x", r=0.0025, role="scuff_dark"):
    """Two dark holes where a handle used to be."""
    cx, cy, cz = center
    out = []
    for i, s in enumerate((-1, 1)):
        p = (cx + s * spacing / 2, cy + 0.0005, cz) if axis == "x" else (cx, cy + 0.0005, cz + s * spacing / 2)
        ob = cylinder(f"{name}_{i}", r, 0.003, role, segments=10, bevel=0.0, center=p)
        ob.rotation_euler = RX90
        out.append(ob)
    return out


def cam_caps(name, x_face, ys, zs, sign, role="plastic_cream", r=0.0065):
    """Flat-pack cam-lock cover caps on a side panel (face at x_face, sticking out `sign` in X)."""
    out = []
    for i, (y, z) in enumerate(zip(ys, zs)):
        ob = cylinder(f"{name}_{i}", r, 0.0012, role, segments=12, bevel=0.0, center=(x_face, y, z))
        ob.rotation_euler = RY90 if sign > 0 else RYm90
        out.append(ob)
    return out


def hinge_knuckles(name, x, y, z0, z1, role="metal_steel", r=0.006, length=0.07):
    """Visible butt-hinge knuckles along a vertical axis at (x, y), one near each end plus mid if tall."""
    zs = [z0 + 0.15, z1 - 0.15]
    if z1 - z0 > 1.2:
        zs.append((z0 + z1) / 2)
    out = []
    for i, z in enumerate(zs):
        out.append(cylinder(f"{name}_{i}", r, length, role, segments=12, bevel=0.001, center=(x, y, z - length / 2)))
    return out


def carcass(prefix, w, d, h, t=0.018, role="laminate_white", edge=None, back_role="hardboard_back",
            z0=0.0, top=True, bottom=True, back=True, plinth=0.0, plinth_recess=0.02, back_t=0.003, sides=True,
            front_recess=0.0):
    """Flat-pack box: sides, top, bottom (above plinth), nailed-on back, optional plinth.
    x in [-w/2, w/2], y in [-d/2, d/2] (front = -d/2), z in [z0, z0+h]. Returns (objs, info)."""
    objs = []
    inner_w = w - 2 * t
    dd = d - back_t
    yc = -back_t / 2
    if sides:
        for s, nm in ((-1, "L"), (1, "R")):
            objs.append(panel(f"{prefix}_side_{nm}", (t, dd, h), role, (s * (w / 2 - t / 2), yc, z0 + h / 2), edge))
    if top:
        objs.append(panel(f"{prefix}_top", (inner_w + 0.001, dd, t), role, (0, yc, z0 + h - t / 2), edge))
    if bottom:
        objs.append(panel(f"{prefix}_bottom", (inner_w + 0.001, dd, t), role, (0, yc, z0 + plinth + t / 2), edge))
    if back:
        objs.append(panel(f"{prefix}_back", (w - 0.002, back_t, h - 0.002), back_role, (0, d / 2 - back_t / 2, z0 + h / 2), bevel=0.0))
    if plinth > 0:
        objs.append(panel(f"{prefix}_plinth", (inner_w + 0.001, t, plinth), role, (0, -d / 2 + plinth_recess + t / 2, z0 + plinth / 2), edge))
    info = dict(inner_w=inner_w, inner_x0=-inner_w / 2, inner_x1=inner_w / 2, bottom_top=z0 + plinth + t,
                top_bottom=z0 + h - t, front_y=-d / 2, back_y=d / 2 - back_t, inner_d=dd - 0.0)
    return objs, info


def drawer(name, w, h, x, y_front, z_bottom, depth, role, edge=None, t=0.018, box_role="mdf_raw",
           handle="bar", handle_role="metal_steel", handle_len=0.128, knob_role="wood_dark", side_t=0.012):
    """Drawer: front panel + drawer box behind it. Returns ONE object, origin at front-bottom-centre.
    handle: 'bar' | 'knob' | 'knob2' | 'missing' | None"""
    parts = []
    zc = z_bottom + h / 2
    parts.append(panel(f"{name}_front", (w, t, h), role, (x, y_front + t / 2, zc), edge, bevel=0.0025))
    bw = w - 0.03
    bh = h - 0.03
    by0 = y_front + t
    bz0 = z_bottom + 0.012
    parts.append(panel(f"{name}_side_L", (side_t, depth, bh), box_role, (x - bw / 2 + side_t / 2, by0 + depth / 2, bz0 + bh / 2), bevel=0.001))
    parts.append(panel(f"{name}_side_R", (side_t, depth, bh), box_role, (x + bw / 2 - side_t / 2, by0 + depth / 2, bz0 + bh / 2), bevel=0.001))
    parts.append(panel(f"{name}_back", (bw - 2 * side_t, side_t, bh), box_role, (x, by0 + depth - side_t / 2, bz0 + bh / 2), bevel=0.001))
    parts.append(panel(f"{name}_base", (bw - 2 * side_t, depth - side_t, 0.004), "hardboard_back", (x, by0 + (depth - side_t) / 2, bz0 + 0.012), bevel=0.0))
    hc = (x, y_front, zc)
    if handle == "bar":
        parts += bar_handle(f"{name}_h", hc, handle_len, handle_role)
    elif handle == "knob":
        parts.append(knob(f"{name}_k", hc, role=knob_role))
    elif handle == "knob2":
        parts.append(knob(f"{name}_k0", (x - w * 0.28, y_front, zc), role=knob_role))
        parts.append(knob(f"{name}_k1", (x + w * 0.28, y_front, zc), role=knob_role))
    elif handle == "knob2_missing":
        parts += screw_holes(f"{name}_sh", (x - w * 0.28, y_front, zc), 0.0)
        parts.append(knob(f"{name}_k1", (x + w * 0.28, y_front, zc), role=knob_role))
    elif handle == "missing":
        parts += screw_holes(f"{name}_sh", hc, handle_len - 0.024)
    ob = join(parts, name)
    set_origin_to(ob, (x, y_front, z_bottom))
    return ob


def door(name, w, h, t, x, y_front, z_bottom, hinge, role, edge=None, handle="bar", handle_role="metal_steel",
         handle_len=0.128, handle_z=None, knob_role="wood_dark", knuckles=True, extra=None):
    """Hinged door (overlay). hinge 'L' or 'R' (seen from the front). Origin on the hinge axis at the bottom."""
    parts = []
    zc = z_bottom + h / 2
    parts.append(panel(f"{name}_leaf", (w, t, h), role, (x, y_front + t / 2, zc), edge, bevel=0.0025))
    hx = x - w / 2 if hinge == "L" else x + w / 2
    free_x = x + w / 2 if hinge == "L" else x - w / 2
    hz = handle_z if handle_z is not None else zc
    hand_x = free_x - 0.045 if hinge == "L" else free_x + 0.045
    if handle == "bar":
        parts += bar_handle(f"{name}_h", (hand_x, y_front, hz), handle_len, handle_role, axis="z")
    elif handle == "knob":
        parts.append(knob(f"{name}_k", (hand_x, y_front, hz), role=knob_role))
    elif handle == "missing":
        parts += screw_holes(f"{name}_sh", (hand_x, y_front, hz), handle_len - 0.024, axis="z")
    if knuckles:
        parts += hinge_knuckles(f"{name}_hinge", hx + (0.0 if hinge == "L" else 0.0), y_front + t / 2, z_bottom, z_bottom + h)
    if extra:
        parts += extra
    ob = join(parts, name)
    set_origin_to(ob, (hx, y_front + t / 2, z_bottom))
    return ob


def set_origin_to(ob, pt):
    """Move the origin of a (non-rotated) mesh object to world point pt without moving the mesh."""
    off = Vector(pt) - ob.location
    for v in ob.data.vertices:
        v.co -= off
    ob.location += off


def tapered_leg(name, p_bottom, h, r0, r1, role, segments=14):
    return cylinder(name, r0, h, role, segments=segments, center=p_bottom, r_top=r1, bevel=0.002)


def cushion(name, size, center, role, cuts=(7, 7, 2), puff=0.012, noise=0.0035, seed=1, seam=True, seam_role="stitch_thread",
            worn_role=None, worn_frac=0.0, subsurf_level=2):
    """Soft padded cushion: subdivided rounded box, puffed middle, light creases, piping seam around the top."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    # subdivide per axis for a grid
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=max(cuts), use_grid_fill=True)
    sx, sy, sz = size
    for v in bm.verts:
        p = v.co.copy()
        v.co = Vector((p.x * sx, p.y * sy, p.z * sz))
    bm.normal_update()
    # puff: push outward more in the middle of each face
    for v in bm.verts:
        px, py, pz = abs(v.co.x) / (sx / 2), abs(v.co.y) / (sy / 2), abs(v.co.z) / (sz / 2)
        f = (1 - px ** 3) * (1 - py ** 3) * (1 - pz ** 3)
        # on a face, one of px,py,pz == 1 -> f==0 ; use the two other axes
        g = 1.0
        for q in (px, py, pz):
            if q < 0.999:
                g *= (1 - q ** 2.5)
        v.co += v.normal * puff * g
    ob = bsk._obj_from_bm(bm, name, [role] + ([worn_role] if worn_role else []))
    ob.location = center
    shade(ob, True, angle=80)
    m = subsurf(ob, subsurf_level)
    apply_modifiers(ob)
    if noise > 0:
        displace_noise(ob, strength=noise, scale=0.09, seed=seed)
    if worn_role:
        # faces near the front-top edge (front = -Y) become worn
        me = ob.data
        for p in me.polygons:
            c = p.center
            if c.y < -sy / 2 * (1 - worn_frac) and c.z > sz * 0.15:
                p.material_index = 1
    uv_box(ob)
    out = [ob]
    if seam:
        inset = 0.012
        z = sz / 2 - 0.004
        pts = [Vector((-sx / 2 + inset, -sy / 2 + inset, z)), Vector((sx / 2 - inset, -sy / 2 + inset, z)),
               Vector((sx / 2 - inset, sy / 2 - inset, z)), Vector((-sx / 2 + inset, sy / 2 - inset, z))]
        # round corners by inserting midpoints
        rp = []
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            rp += [a + (b - a) * 0.08, a + (b - a) * 0.92]
        w = wire(f"{name}_seam", rp, 0.0025, seam_role, n=5, segments=8, closed=True)
        w.location = center
        out.append(w)
    return out


def shirt(name, top, width=0.44, length=0.62, role="cotton_white", thickness=0.06, seed=3, sleeves=True, long_sleeve=False,
          noise=0.006, compact=False):
    """A hanging T-shirt / top, built with its WIDTH along X hanging down from `top` (neck point).
    Elliptical cross-section sweep narrowing to the hem + sleeve tubes; creased by noise. Returns parts (rotate/move them)."""
    rnd = random.Random(seed)
    rows = 16
    segs = 20
    rings = []
    tx, ty, tz = top
    for i in range(rows + 1):
        u = i / rows                         # 0 top -> 1 hem
        z = tz - u * length
        if u < 0.07:
            wf = 0.50 + u / 0.07 * 0.50     # neck -> shoulders
        else:
            wf = 1.0 - 0.14 * (u - 0.07) / 0.93
        a = width / 2 * wf
        b = thickness / 2 * (1.0 - 0.5 * u) * (0.7 if u < 0.04 else 1.0)
        ring = []
        for j in range(segs):
            t = 2 * math.pi * j / segs
            # slight random hem/side waviness so it is not a perfect ellipse
            w = 1.0 + 0.03 * math.sin(3 * t + seed) * u
            ring.append(Vector((tx + a * w * math.cos(t), ty + b * math.sin(t) * (1 + 0.25 * u * math.cos(2 * t)), z)))
        rings.append(ring)
    body = sweep(name, rings, role, smooth=True)
    displace_noise(body, strength=noise, scale=0.11, seed=seed)
    shade(body, True, angle=80)
    uv_box(body)
    parts = [body]
    if sleeves:
        sl = 0.17 if not long_sleeve else 0.52
        ang = math.radians(64) if not long_sleeve else math.radians(78)
        if compact:   # squashed into a shallow wardrobe: sleeves hang almost straight down
            sl = 0.14 if not long_sleeve else 0.50
            ang = math.radians(74) if not long_sleeve else math.radians(85)
        n = 5 if not long_sleeve else 10
        for s in (-1, 1):
            P = Vector((tx + s * (width / 2 - 0.035), ty, tz - 0.035))
            d = Vector((s * math.cos(ang), 0, -math.sin(ang)))
            e1 = Vector((0, 1, 0))
            e2 = d.cross(e1).normalized()
            rr = []
            for i in range(n + 1):
                u = i / n
                c = P + d * (sl * u)
                ra = ((0.062 if not long_sleeve else 0.058) * (0.8 if compact else 1.0)) * (1 - 0.3 * u)
                rb = thickness / 2 * 0.85 * (1 - 0.25 * u)
                ring = []
                for j in range(12):
                    t = 2 * math.pi * j / 12
                    ring.append(c + e2 * (ra * math.cos(t)) + e1 * (rb * math.sin(t)))
                rr.append(ring)
            sleeve = sweep(f"{name}_sleeve{s}", rr, role, smooth=True)
            displace_noise(sleeve, strength=noise * 0.6, scale=0.08, seed=seed + s)
            shade(sleeve, True, angle=80)
            parts.append(sleeve)
    return parts


def rounded_polyline(pts, r=0.02, n=5):
    """Insert circular-ish corner arcs (radius r) into a polyline (for bent tube frames). Use with wire(smooth_path=False)."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d0 = (a - b).normalized(); d1 = (c - b).normalized()
        la = min(r, (a - b).length / 2, (c - b).length / 2)
        p0 = b + d0 * la; p1 = b + d1 * la
        for k in range(n + 1):
            t = k / n
            # quadratic bezier p0 -> b -> p1
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t ** 2 * p1)
    out.append(pts[-1])
    return out


def garment_on_hanger(prefix, x, rail_y, rail_z, role, width, length, thickness, seed, long_sleeve=False, hanger_role="plastic_black",
                      compact=False):
    """Hanger + garment hung on a rail that runs along X at (rail_y, rail_z); garment faces along X (width along Y)."""
    hz = rail_z + 0.018
    parts = hanger(f"{prefix}_hanger", (0, 0, hz), width=min(0.42, width - 0.02), role=hanger_role)
    parts += shirt(f"{prefix}_shirt", (0, 0, hz - 0.14), width=width, length=length, role=role, thickness=thickness, seed=seed, long_sleeve=long_sleeve,
                   compact=compact)
    for o in parts:
        o.rotation_euler = (0, 0, math.pi / 2)
        o.location = (x + 0.016, rail_y, 0)
    return parts


def glass_preview_alpha():
    """Make glass/mirror materials translucent in Workbench previews (bsk.mat sets viewport alpha to 1)."""
    for m in bpy.data.materials:
        if m.name.startswith("glass"):
            c = m.diffuse_color
            m.diffuse_color = (c[0], c[1], c[2], 0.3)


def hanger(name, hook_top, width=0.40, role="plastic_black", radius=0.0035):
    """Coat hanger: triangle + hook, hanging from hook_top (the top of the hook)."""
    hx, hy, hz = hook_top
    bar_z = hz - 0.085
    pts = [(hx, hy, bar_z - 0.20), (hx + width / 2, hy, bar_z - 0.20)]
    # triangle (closed wire): left tip -> apex -> right tip -> bottom bar back to left tip
    tri = [Vector((hx - width / 2, hy, bar_z - 0.20)), Vector((hx - width * 0.1, hy, bar_z - 0.02)), Vector((hx, hy, bar_z)),
           Vector((hx + width * 0.1, hy, bar_z - 0.02)), Vector((hx + width / 2, hy, bar_z - 0.20)), Vector((hx, hy, bar_z - 0.21))]
    t = wire(f"{name}_tri", tri, radius, role, n=4, segments=10, closed=True)
    # hook: up from apex then curl over toward +Y (over the rail)
    hook = [Vector((hx, hy, bar_z)), Vector((hx, hy, hz - 0.045)), Vector((hx, hy - 0.004, hz - 0.015)), Vector((hx, hy + 0.012, hz)),
            Vector((hx, hy + 0.028, hz - 0.006)), Vector((hx, hy + 0.034, hz - 0.025)), Vector((hx, hy + 0.028, hz - 0.04))]
    h = wire(f"{name}_hook", hook, radius * 0.9, "metal_steel" if role != "metal_steel" else role, n=6, segments=10)
    return [t, h]


def caster(name, p, role_wheel="plastic_black", role_fork="plastic_black", r=0.025):
    """Twin-wheel office caster; p = floor point under the wheel axis. Returns parts."""
    px, py, pz = p
    parts = []
    for s in (-1, 1):
        w = cylinder(f"{name}_w{s}", r, 0.012, role_wheel, segments=20, bevel=0.002, center=(px + s * 0.012, py, pz + r), origin="center")
        w.rotation_euler = RY90
        parts.append(w)
    hub = cylinder(f"{name}_hub", 0.012, 0.038, role_fork, segments=12, bevel=0.001, center=(px, py, pz + r), origin="center")
    hub.rotation_euler = RY90
    parts.append(hub)
    stem = cylinder(f"{name}_stem", 0.006, 0.035, "metal_steel", segments=10, bevel=0.0, center=(px, py, pz + r))
    parts.append(stem)
    return parts


def helix(name, center_bottom, R, pitch, turns, radius, role, seg_per_turn=16):
    cx, cy, cz = center_bottom
    pts = []
    n = int(turns * seg_per_turn)
    for i in range(n + 1):
        a = 2 * math.pi * i / seg_per_turn
        pts.append(Vector((cx + R * math.cos(a), cy + R * math.sin(a), cz + pitch * i / seg_per_turn)))
    return wire(name, pts, radius, role, smooth_path=False, segments=8)


# ------------------------------------------------------------------------------------------------ measuring / export

def walk_meshes(objs):
    out = []
    def w(o):
        if o.type == "MESH":
            out.append(o)
        for c in o.children:
            w(c)
    for o in (objs if isinstance(objs, (list, tuple)) else [objs]):
        w(o)
    return out


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in walk_meshes(objs):
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        n += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    return n


def dims(objs):
    pts = []
    for o in walk_meshes(objs):
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def roles_used(objs):
    r = set()
    for o in walk_meshes(objs):
        for s in o.material_slots:
            if s.material:
                r.add(s.material.name.split(".")[0])
    return sorted(r)


def finalize_children(children):
    """Apply modifiers on separate child meshes (so tri counts / export are what we see)."""
    for c in children:
        if c.type == "MESH" and c.modifiers:
            apply_modifiers(c)


def assemble(name, static_parts, movable=None):
    """static_parts -> one joined mesh. If movable children exist: empty root `name` + `body` + children.
    Otherwise the joined mesh IS the root. Origin: bottom centre of the whole prop (root at floor point)."""
    movable = movable or []
    body = join(static_parts, name if not movable else "body")
    if not movable:
        set_origin_bottom(body)
        return body
    finalize_children(movable)
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = (0, 0, 0)          # builders are authored with bottom-centre at the world origin
    for o in [body] + movable:
        o.parent = root
    return root
