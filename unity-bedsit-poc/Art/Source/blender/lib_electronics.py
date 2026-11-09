"""lib_electronics - helpers for the `electronics` prop family (built on bsk, does not modify it).

All builders return mesh objects positioned in WORLD space (x width, y depth, z up, front = -Y).
Bevels are done directly in bmesh (no modifiers) so joining many small parts stays fast.
"""
import bpy, bmesh, math, random, os, json
from mathutils import Vector, Matrix, Euler
import bsk
from bsk import mat, MATERIALS, _obj_from_bm

# ---------------------------------------------------------------- extra material roles (also listed in the manifest)
NEW_ROLES = {
    "plastic_beige":   ((0.80, 0.74, 0.58), 0.55, 0.0),   # yellowed 90s/2000s cream plastic
    "plastic_beige_worn": ((0.70, 0.64, 0.50), 0.30, 0.0),# shinier, greasier (worn spacebar, mouse buttons)
    "plastic_silver":  ((0.58, 0.58, 0.57), 0.40, 0.2),   # matte silver-painted plastic
    "plastic_dark":    ((0.11, 0.11, 0.12), 0.50, 0.0),   # dark charcoal plastic (between black and grey)
    "plastic_orange":  ((0.90, 0.40, 0.05), 0.45, 0.0),
    "plastic_cyan":    ((0.10, 0.60, 0.70), 0.45, 0.0),
    "foam_black":      ((0.05, 0.05, 0.05), 0.98, 0.0),   # speaker grille cloth / foam
    "carpet_black":    ((0.06, 0.06, 0.065), 0.98, 0.0),  # PA-speaker carpet covering
    "cone_paper":      ((0.16, 0.15, 0.14), 0.85, 0.0),   # speaker cone
    "vinyl_black":     ((0.03, 0.03, 0.035), 0.25, 0.0),
    "rubber_grey":     ((0.30, 0.30, 0.31), 0.85, 0.0),   # pads, feet, keys of a phone dock
    "label_white":     ((0.92, 0.92, 0.90), 0.60, 0.0),   # brand-less label regions / stickers
    "label_red":       ((0.80, 0.12, 0.10), 0.60, 0.0),
    "label_blue":      ((0.12, 0.30, 0.75), 0.60, 0.0),
    "label_yellow":    ((0.92, 0.75, 0.15), 0.60, 0.0),
    "label_black":     ((0.05, 0.05, 0.05), 0.60, 0.0),
    "metal_chrome":    ((0.85, 0.86, 0.88), 0.12, 1.0),
    "metal_alu":       ((0.70, 0.71, 0.72), 0.30, 1.0),
    "metal_red":       ((0.60, 0.08, 0.06), 0.35, 0.8),   # powder-coated red audio interface
    "glass_dark":      ((0.04, 0.045, 0.05), 0.05, 0.0),  # tinted windows (tape deck door, phone back)
    "pad_rubber":      ((0.78, 0.78, 0.74), 0.55, 0.0),   # translucent-look drum pads (Unity may swap to emissive per pad)
}
MATERIALS.update(NEW_ROLES)


# ---------------------------------------------------------------- bmesh primitives (world-space, bevelled, no modifiers)

def _bm_bevel(bm, offset, segments=2, angle=35, verts=None):
    if offset <= 0:
        return
    cos_lim = math.cos(math.radians(angle))
    edges = []
    for e in bm.edges:
        if len(e.link_faces) == 2:
            if e.link_faces[0].normal.dot(e.link_faces[1].normal) < cos_lim:
                edges.append(e)
        else:
            edges.append(e)
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=offset, segments=segments, affect="EDGES", clamp_overlap=True, profile=0.7)


def _make(bm, name, role, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj_from_bm(bm, name, [role])
    for p in ob.data.polygons:
        p.use_smooth = smooth
    return ob


def rbox(name, size, role, center=(0, 0, 0), bevel=0.003, segs=2, origin="center", taper=None, taper_axis="z"):
    """Bevelled box. taper=(sx, sy) scales the +axis face (e.g. top) for wedge/pyramid shapes."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    if taper:
        ax = "xyz".index(taper_axis)
        for v in bm.verts:
            if v.co[ax] > 0:
                others = [i for i in range(3) if i != ax]
                v.co[others[0]] *= taper[0]
                v.co[others[1]] *= taper[1]
    _bm_bevel(bm, min(bevel, min(size) * 0.45), segs)
    ob = _make(bm, name, role, smooth=True)
    c = Vector(center)
    if origin == "bottom":
        c.z += size[2] / 2
    ob.location = c
    return ob


def boxes(name, items, role, bevel=0.0008, segs=1):
    """Many bevelled boxes in ONE mesh. items: list of (size, center) or (size, center, taper_xy)."""
    bm = bmesh.new()
    for it in items:
        size, center = it[0], it[1]
        taper = it[2] if len(it) > 2 else None
        geom = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        for v in geom:
            v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
            if taper and v.co.z > 0:
                v.co.x *= taper[0]; v.co.y *= taper[1]
            v.co += Vector(center)
    if bevel > 0:
        b = min(bevel, min(min(it[0]) for it in items) * 0.4)
        _bm_bevel(bm, b, segs)
    return _make(bm, name, role, smooth=True)


def _axis_mat(axis):
    """Rotation taking local +Z to `axis`, keeping local +Y = world up (for side faces) and local +X = the viewer's right
    when looking at that face. Columns are the images of local x, y, z."""
    cols = {"z": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            "-z": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
            "-y": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
            "y": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
            "x": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
            "-x": ((0, -1, 0), (0, 0, 1), (-1, 0, 0))}[axis]
    m = Matrix((cols[0], cols[1], cols[2]))
    m.transpose()
    return m


def _axis_rot(axis):
    return _axis_mat(axis).to_euler()


def cyl(name, r, h, role, center=(0, 0, 0), axis="z", segments=24, bevel=0.0015, r_top=None, origin="center"):
    """Cylinder along `axis` ('z','-y','x'...). origin='bottom' only meaningful for axis z. Bevelled rims."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r,
                          radius2=(r if r_top is None else r_top), depth=h)
    _bm_bevel(bm, min(bevel, r * 0.4, h * 0.4), 2, angle=35)
    ob = _make(bm, name, role, smooth=True)
    c = Vector(center)
    if origin == "bottom" and axis == "z":
        c.z += h / 2
    ob.location = c
    ob.rotation_euler = _axis_rot(axis)
    return ob


def lathe(name, profile, role, center=(0, 0, 0), axis="z", segments=32, smooth=True):
    """Surface of revolution, profile [(r, t)...] along the axis. t measured along axis from `center`."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments), z)) for i in range(segments)])
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    ob = _make(bm, name, role, smooth=smooth)
    ob.location = Vector(center)
    ob.rotation_euler = _axis_rot(axis)
    return ob


def ring(name, r_out, r_in, h, role, center=(0, 0, 0), axis="z", segments=32):
    return lathe(name, [(r_in, 0), (r_out, 0), (r_out, h), (r_in, h)], role, center, axis, segments)


def torus(name, R, r, role, center=(0, 0, 0), axis="z", seg_major=32, seg_minor=8, arc=(0, 2 * math.pi)):
    """(Partial) torus - headphone band, handles, hinge rings."""
    bm = bmesh.new()
    rings = []
    full = abs(arc[1] - arc[0] - 2 * math.pi) < 1e-6
    n = seg_major if full else seg_major + 1
    for i in range(n):
        a = arc[0] + (arc[1] - arc[0]) * i / seg_major
        ca, sa = math.cos(a), math.sin(a)
        rr = []
        for j in range(seg_minor):
            b = 2 * math.pi * j / seg_minor
            rad = R + r * math.cos(b)
            rr.append(bm.verts.new((rad * ca, rad * sa, r * math.sin(b))))
        rings.append(rr)
    for k in range(len(rings) - 1 if not full else len(rings)):
        a, b = rings[k], rings[(k + 1) % len(rings)]
        for j in range(seg_minor):
            jj = (j + 1) % seg_minor
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    if not full:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    ob = _make(bm, name, role, smooth=True)
    ob.location = Vector(center)
    ob.rotation_euler = _axis_rot(axis)
    return ob


def cr_sample(points, per_seg=8):
    """Catmull-Rom sampling of a polyline so tubes bend smoothly."""
    pts = [Vector(p) for p in points]
    if len(pts) < 3:
        return pts
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(per_seg):
            t = s / per_seg
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def cable(name, points, radius=0.003, role="rubber_black", per_seg=8, segments=8):
    """Smooth cable mesh through control points (Catmull-Rom)."""
    pts = cr_sample(points, per_seg)
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
    ob = bsk.to_mesh(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def helix(center, r, pitch, turns, axis_dir=Vector((0, 0, -1)), per_turn=12, start=Vector((1, 0, 0))):
    """Points of a coiled cable (headphone / phone cord)."""
    c = Vector(center)
    d = Vector(axis_dir).normalized()
    u = Vector(start).normalized()
    v = d.cross(u).normalized()
    u = v.cross(d).normalized()
    out = []
    n = int(turns * per_turn)
    for i in range(n + 1):
        a = 2 * math.pi * i / per_turn
        out.append(c + d * (pitch * i / per_turn) + (u * math.cos(a) + v * math.sin(a)) * r)
    return out


def dome(name, r, h, role, center=(0, 0, 0), axis="z", segments=24, rings=6, flat_bottom=True):
    """Spherical cap (dust cap, dome tweeter, LED lens, convex screen bump)."""
    prof = []
    if flat_bottom:
        prof.append((0, 0))
    for i in range(rings + 1):
        a = (math.pi / 2) * i / rings
        prof.append((r * math.cos(a), h * math.sin(a)))
    prof[1] = (r, 0.0) if flat_bottom else prof[1]
    return lathe(name, prof, role, center, axis, segments)


def plane_grid(name, w, h, role, center=(0, 0, 0), axis="-y", nx=8, ny=6, bulge=0.0):
    """Subdivided rectangle facing +Z (then rotated to axis). bulge>0 makes it convex (CRT screen)."""
    bm = bmesh.new()
    verts = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = (i / nx - 0.5) * w
            y = (j / ny - 0.5) * h
            rx, ry = x / (w / 2), y / (h / 2)
            z = bulge * (1 - 0.5 * (rx ** 2 + ry ** 2)) if bulge else 0
            row.append(bm.verts.new((x, y, z)))
        verts.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    ob = _make(bm, name, role, smooth=True)
    # planar 0..1 UVs (Unity emissive screen texture)
    me = ob.data
    me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (co.x / w + 0.5, co.y / h + 0.5)
    ob.location = Vector(center)
    ob.rotation_euler = _axis_rot(axis)
    ob["keep_uv"] = True
    return ob


def screen_plane(w, h, center, axis="-y", bulge=0.0, name="screen"):
    """Child screen object: flat (or convex) quad facing -Y (or any axis), role screen_off."""
    return plane_grid(name, w, h, "screen_off", center, axis, nx=(10 if bulge else 2), ny=(8 if bulge else 2), bulge=bulge)


def loft_shell(name, stations, role, nseg=20, expo=2.4, bottom_round=0.003):
    """Organic shell lofted through cross-section stations along Y: [(y, width, height, z_bottom)...].
    Each section is a superellipse-ish top half on a flat (slightly rounded) bottom. Ends closed. (mouse, controller grips)"""
    bm = bmesh.new()
    rings = []
    for (y, w, h, zb) in stations:
        ring_v = []
        hw = w / 2
        # top arc from +x to -x
        for i in range(nseg + 1):
            a = math.pi * i / nseg
            cx, sz = math.cos(a), math.sin(a)
            x = hw * math.copysign(abs(cx) ** (2 / expo), cx)
            z = zb + bottom_round + (h - bottom_round) * (abs(sz) ** (2 / expo))
            ring_v.append(bm.verts.new((x, y, z)))
        # bottom: small rounding then flat
        ring_v.append(bm.verts.new((-hw + bottom_round * 0.3, y, zb)))
        ring_v.append(bm.verts.new((hw - bottom_round * 0.3, y, zb)))
        rings.append(ring_v)
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    ob = _make(bm, name, role, smooth=True)
    return ob


def rotate_parts(parts, euler, pivot):
    """Rotate a list of (possibly nested) part objects about `pivot` (world) by Euler (radians)."""
    R = Matrix.Translation(Vector(pivot)) @ Euler(euler).to_matrix().to_4x4() @ Matrix.Translation(-Vector(pivot))
    def walk(p):
        if isinstance(p, (list, tuple)):
            for q in p:
                walk(q)
        elif p is not None:
            # matrix_world may be stale before a depsgraph update: compose from loc/rot/scale explicitly
            M = Matrix.Translation(p.location) @ p.rotation_euler.to_matrix().to_4x4() @ Matrix.Diagonal((*p.scale, 1.0))
            M = R @ M
            p.location = M.to_translation()
            p.rotation_euler = M.to_euler()
            p.scale = M.to_scale()
    walk(parts)
    return parts


def wedge(name, size, role, center=(0, 0, 0), back_h=None, bevel=0.003, segs=2):
    """Box whose top slopes: height `size[2]` at the front (-y) and `back_h` at the back (+y). origin bottom centre."""
    back_h = back_h or size[2]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]
        v.co.z = (size[2] if v.co.y < 0 else back_h) if v.co.z > 0 else 0.0
    _bm_bevel(bm, min(bevel, min(size[2], back_h) * 0.45), segs)
    ob = _make(bm, name, role, smooth=True)
    ob.location = Vector(center)
    return ob


def cut(ob, cutters):
    """Boolean-subtract cutter specs from `ob` (applied immediately, cutters removed).
    cutter spec: ("box", size, center) or ("cyl", r, depth, center, axis)."""
    tmp = []
    for c in cutters:
        if c[0] == "box":
            t = rbox("cutter", c[1], "plastic_black", c[2], bevel=0)
        else:
            t = cyl("cutter", c[1], c[2], "plastic_black", c[3], c[4], 32, bevel=0)
        tmp.append(t)
    for t in tmp:
        m = ob.modifiers.new("cut", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"
        m.object = t
    bsk.apply_modifiers(ob)
    for t in tmp:
        me = t.data
        bpy.data.objects.remove(t)
        bpy.data.meshes.remove(me)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def hollow_cabinet(name, size, role, center=(0, 0, 0), wall=0.015, bevel=0.006, extra_cuts=()):
    """Open-fronted cabinet shell (front = -Y) with real wall thickness, for speakers. origin bottom centre."""
    W, D, H = size
    cab = rbox(name, size, role, center, bevel=bevel, segs=3, origin="bottom")
    inner = ("box", (W - 2 * wall, D - wall, H - 2 * wall), (center[0], center[1] - wall / 2 - 0.001, center[2] + H / 2))
    return cut(cab, [inner] + list(extra_cuts))


def baffle_with_holes(name, size, role, center, holes, bevel=0.002):
    """Front plate (thickness = size[1]) with circular holes [(lx, lz, r)...] cut through along Y."""
    pl = rbox(name, size, role, center, bevel=bevel)
    cuts = [("cyl", r, size[1] * 3, (center[0] + lx, center[1], center[2] + lz), "y") for (lx, lz, r) in holes]
    return cut(pl, cuts)


# ---------------------------------------------------------------- compound details

def knob(name, r, h, role, center, axis="z", segments=20, pointer_role="label_white", skirt=True):
    """Rotary knob: slightly tapered cylinder with a pointer line on top and an optional skirt."""
    parts = []
    parts.append(cyl(name, r, h, role, center, axis, segments, bevel=min(0.0012, r * 0.3), r_top=r * 0.9))
    # local frame to place pointer on the cap along the axis
    rot = _axis_rot(axis).to_matrix()
    c = Vector(center)
    cap = c + rot @ Vector((0, 0, h / 2 + 0.0003))
    pw = rot @ Vector((r * 0.14, r * 0.6, 0.0006))
    pc = cap + rot @ Vector((0, r * 0.4, 0))
    parts.append(boxes(name + "_ptr", [((abs(pw.x) or 0.0006, abs(pw.y) or 0.0006, abs(pw.z) or 0.0006), pc)], pointer_role, bevel=0))
    if skirt:
        parts.append(cyl(name + "_skirt", r * 1.25, 0.0012, "plastic_dark", c - rot @ Vector((0, 0, h / 2 - 0.0006)), axis, segments, bevel=0.0004))
    return parts


def fader(name, slot_len, center, role_cap="plastic_dark", horizontal=False, pos=0.5, cap=(0.012, 0.022, 0.012), axis="z", slot_w=0.003):
    """Fader: dark slot + cap sitting on a stem. For axis 'z' (panel facing up), slot runs along y (or x if horizontal)."""
    c = Vector(center)
    parts = []
    if horizontal:
        slot = ((slot_len, slot_w, 0.004), c + Vector((0, 0, -0.001)))
        cap_c = c + Vector(((pos - 0.5) * slot_len, 0, cap[2] / 2 + 0.002))
        cap_size = (cap[1], cap[0], cap[2])
    else:
        slot = ((slot_w, slot_len, 0.004), c + Vector((0, 0, -0.001)))
        cap_c = c + Vector((0, (pos - 0.5) * slot_len, cap[2] / 2 + 0.002))
        cap_size = cap
    parts.append(boxes(name + "_slot", [slot], "label_black", bevel=0))
    parts.append(boxes(name + "_stem", [((slot_w * 0.8, slot_w * 0.8, 0.004), cap_c - Vector((0, 0, cap[2] / 2)))], "metal_dark", bevel=0))
    parts.append(boxes(name + "_cap", [(cap_size, cap_c, (0.85, 0.85))], role_cap, bevel=0.0012, segs=2))
    # grip line on the cap
    gl = (cap_size[0] * 0.9, 0.0012, 0.0006) if not horizontal else (0.0012, cap_size[1] * 0.9, 0.0006)
    parts.append(boxes(name + "_line", [(gl, cap_c + Vector((0, 0, cap[2] / 2)))], "label_white", bevel=0))
    return parts


def button(name, size, center, role, axis="z", round_=False, bevel=0.0008, segments=16):
    """Push button proud of a panel. For axis '-y' the button sticks out of a front face."""
    rot = _axis_rot(axis).to_matrix()
    c = Vector(center)
    if round_:
        return cyl(name, size[0] / 2, size[2], role, c + rot @ Vector((0, 0, size[2] / 2)), axis, segments, bevel=bevel, r_top=size[0] / 2 * 0.92)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        if v.co.z > 0:
            v.co.x *= 0.9; v.co.y *= 0.9
        v.co.z += size[2] / 2
    _bm_bevel(bm, min(bevel, min(size) * 0.3), 2)
    ob = _make(bm, name, role)
    ob.location = c
    ob.rotation_euler = _axis_rot(axis)
    return ob


def led(name, r, center, role, axis="-y", depth=0.0015):
    """Small LED dome sticking out of a panel."""
    return dome(name, r, depth, role, center, axis, segments=12, rings=3)


def grille(name, w, h, center, nx, ny, hole, depth=0.003, axis="-y", role="label_black", round_holes=False, margin=0.0, mask_radius=None):
    """Perforated-look grille: a field of dark recessed holes (small boxes/cylinders) pressed into a face.
    `center` is the centre of the face; holes extend `depth` INTO the face (behind it along -axis).
    mask_radius keeps only holes inside a circle (round speaker grilles)."""
    rot = _axis_rot(axis).to_matrix()
    c = Vector(center)
    items = []
    bm = bmesh.new()
    for j in range(ny):
        for i in range(nx):
            lx = (-(w - 2 * margin) / 2 + (i + 0.5) * (w - 2 * margin) / nx) if nx > 1 else 0
            ly = (-(h - 2 * margin) / 2 + (j + 0.5) * (h - 2 * margin) / ny) if ny > 1 else 0
            if mask_radius and math.hypot(lx, ly) > mask_radius:
                continue
            lc = Vector((lx, ly, -depth / 2 + 0.0002))
            if round_holes:
                g = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=hole[0] / 2, radius2=hole[0] / 2, depth=depth)["verts"]
                for v in g:
                    v.co += lc
            else:
                g = bmesh.ops.create_cube(bm, size=1.0)["verts"]
                for v in g:
                    v.co.x *= hole[0]; v.co.y *= hole[1]; v.co.z *= depth
                    v.co += lc
    ob = _make(bm, name, role, smooth=False)
    ob.location = c
    ob.rotation_euler = _axis_rot(axis)
    return ob


def port_slots(name, items, center, axis="-y", role="label_black", depth=0.006):
    """Rectangular ports (USB/HDMI/SCART/Ethernet) as dark recesses in a face. items: [(w,h,(lx,ly))...]"""
    bm = bmesh.new()
    for (w, h, (lx, ly)) in items:
        g = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        for v in g:
            v.co.x *= w; v.co.y *= h; v.co.z *= depth
            v.co += Vector((lx, ly, -depth / 2 + 0.0002))
    ob = _make(bm, name, role, smooth=False)
    ob.location = Vector(center)
    ob.rotation_euler = _axis_rot(axis)
    return ob


def rca_ports(name, positions, center, axis="y", role="metal_chrome", r=0.0045):
    """RCA / jack sockets: short rings sticking out of a face at (lx,ly) offsets."""
    parts = []
    rot = _axis_rot(axis).to_matrix()
    for k, (lx, ly) in enumerate(positions):
        c = Vector(center) + rot @ Vector((lx, ly, 0.0025))
        parts.append(ring(f"{name}_{k}", r, r * 0.6, 0.005, role, c - rot @ Vector((0, 0, 0.0025)), axis, 12))
    return parts


SEGS = {  # 7-segment: a(top) b(top-right) c(bottom-right) d(bottom) e(bottom-left) f(top-left) g(middle)
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcfgd", " ": "",
}


def seven_seg(name, text, center, digit_h, role="led_red", axis="-y", thickness=None, gap=None):
    """LED digits as real segment geometry. text may contain ':' for the colon dots. Lies on the plane facing `axis`."""
    t = thickness or digit_h * 0.13
    w = digit_h * 0.55
    gap = gap or digit_h * 0.35
    items = []
    # total width
    widths = [(w * 0.45 if ch == ":" else w) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = -total / 2
    for ch, cw in zip(text, widths):
        cx = x + cw / 2
        if ch == ":":
            items.append(((t, t, 0.0012), (cx, digit_h * 0.25, 0)))
            items.append(((t, t, 0.0012), (cx, -digit_h * 0.25, 0)))
        else:
            hw, hh = w / 2 - t / 2, digit_h / 2 - t / 2
            seg = {
                "a": ((w - t, t, 0.0012), (cx, hh, 0)), "d": ((w - t, t, 0.0012), (cx, -hh, 0)), "g": ((w - t, t, 0.0012), (cx, 0, 0)),
                "b": ((t, digit_h / 2 - t, 0.0012), (cx + hw, digit_h / 4, 0)), "c": ((t, digit_h / 2 - t, 0.0012), (cx + hw, -digit_h / 4, 0)),
                "f": ((t, digit_h / 2 - t, 0.0012), (cx - hw, digit_h / 4, 0)), "e": ((t, digit_h / 2 - t, 0.0012), (cx - hw, -digit_h / 4, 0)),
            }
            for s in SEGS.get(ch, ""):
                items.append(seg[s])
        x += cw + gap
    bm = bmesh.new()
    for (size, c) in items:
        g = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        for v in g:
            v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
            # chamfer segment ends a little: taper x by y for horizontal segs is overkill; keep boxes
            v.co += Vector(c) + Vector((0, 0, 0.0006))
    ob = _make(bm, name, role, smooth=False)
    ob.location = Vector(center)
    ob.rotation_euler = _axis_rot(axis)
    return ob


def speaker_driver(name, r, center, axis="-y", depth=None, role_cone="cone_paper", role_surround="rubber_black", role_cap="plastic_dark", frame="metal_dark", segments=32, screws=4):
    """Loudspeaker driver facing `axis`: mounting frame ring, rubber surround, paper cone, dust cap, screws."""
    depth = depth or r * 0.55
    rot = _axis_rot(axis).to_matrix()
    c = Vector(center)
    parts = []
    # frame ring sits proud of baffle by 3mm
    parts.append(ring(name + "_frame", r * 1.08, r * 0.96, 0.003, frame, c, axis, segments))
    # surround: half-round torus
    parts.append(torus(name + "_surr", r * 0.90, r * 0.065, role_surround, c + rot @ Vector((0, 0, 0.001)), axis, segments, 8))
    # cone going back into the cabinet: double-walled (1.2 mm) so normals are unambiguous and it reads from the front
    front = [(r * 0.84, 0.0), (r * 0.70, -depth * 0.30), (r * 0.50, -depth * 0.62), (r * 0.30, -depth * 0.92), (r * 0.22, -depth)]
    back = [(rr - 0.0008, t - 0.0012) for (rr, t) in reversed(front)]
    parts.append(lathe(name + "_cone", front + back, role_cone, c, axis, segments))
    # dust cap
    parts.append(dome(name + "_cap", r * 0.26, r * 0.12, role_cap, c + rot @ Vector((0, 0, -depth * 0.9)), axis, segments, 5))
    # screws
    for k in range(screws):
        a = 2 * math.pi * (k + 0.5) / screws
        p = c + rot @ Vector((r * 1.02 * math.cos(a), r * 1.02 * math.sin(a), 0.0032))
        parts.append(cyl(f"{name}_scr{k}", 0.0025, 0.001, "metal_steel", p, axis, 8, bevel=0.0003))
    return parts


def feet(name, positions, r=0.006, h=0.004, role="rubber_black", z=0.0):
    """Rubber feet (short cylinders) under a body. positions = [(x,y)...]."""
    return [cyl(f"{name}_{k}", r, h, role, (x, y, z + h / 2), "z", 12, bevel=0.0008, r_top=r * 0.85) for k, (x, y) in enumerate(positions)]


def corner_feet(w, d, inset=0.02, **kw):
    hw, hd = w / 2 - inset, d / 2 - inset
    return feet("foot", [(-hw, -hd), (hw, -hd), (-hw, hd), (hw, hd)], **kw)


def label(name, size, center, role="label_white", axis="-y"):
    """Flat colour-region label/sticker standing 0.3 mm proud of a face."""
    rot = _axis_rot(axis).to_matrix()
    bm = bmesh.new()
    g = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    for v in g:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= 0.0006
        v.co.z += 0.0003
    ob = _make(bm, name, role, smooth=False)
    ob.location = Vector(center)
    ob.rotation_euler = _axis_rot(axis)
    return ob


def sticker(name, size, center, role, axis="z", angle=0.0, peel=False):
    """Peeling sticker: thin slab, rotated a bit around the face normal, one corner lifted."""
    rot = _axis_rot(axis).to_matrix()
    bm = bmesh.new()
    nx, ny = 4, 3
    vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = (i / nx - 0.5) * size[0]
            y = (j / ny - 0.5) * size[1]
            z = 0.0005
            if peel and i == nx and j == ny:
                z += size[1] * 0.12
            if peel and (i == nx and j == ny - 1 or i == nx - 1 and j == ny):
                z += size[1] * 0.03
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    bmesh.ops.solidify(bm, geom=bm.faces[:] + bm.edges[:] + bm.verts[:], thickness=0.0005)
    ob = _make(bm, name, role, smooth=True)
    ob.location = Vector(center)
    ob.rotation_euler = (Euler((0, 0, angle)).to_matrix() @ rot.to_3x3() if False else (rot.to_3x3() @ Euler((0, 0, angle)).to_matrix())).to_euler()
    return ob


def keycaps(name, keys, role, bevel=0.0012, taper=(0.8, 0.78), dish=True):
    """keys: list of (cx, cy, w, d, h, z0). One mesh of sculpted keycaps (top tapered, slight front slope)."""
    bm = bmesh.new()
    for (cx, cy, w, d, h, z0) in keys:
        g = bmesh.ops.create_cube(bm, size=1.0)["verts"]
        for v in g:
            v.co.x *= w; v.co.y *= d; v.co.z *= h
            if v.co.z > 0:
                v.co.x *= taper[0]; v.co.y *= taper[1]
                v.co.y += d * 0.04          # top shifted back a touch (sculpted feel)
                if dish and v.co.y < 0:
                    v.co.z -= h * 0.12       # front of the top lower than the back
            v.co += Vector((cx, cy, z0 + h / 2))
    _bm_bevel(bm, bevel, 2)
    return _make(bm, name, role, smooth=True)


# ---------------------------------------------------------------- assembly / export / manifest

def tris(ob):
    n = 0
    def walk(o):
        nonlocal n
        if o.type == "MESH":
            n += sum(len(p.vertices) - 2 for p in o.data.polygons)
        for c in o.children:
            walk(c)
    walk(ob)
    return n


def apply_xform(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.select_set(False)


def merge(parts, name, smooth_angle=40, uv_scale=1.0):
    """Join parts into one mesh object with world transforms baked, auto-smooth and box UVs (keeps screen UVs)."""
    parts = [p for p in parts if p is not None]
    flat = []
    for p in parts:
        if isinstance(p, (list, tuple)):
            flat.extend(p)
        else:
            flat.append(p)
    for p in flat:
        if p.rotation_euler != Euler((0, 0, 0)) or p.location.length > 0 or p.scale != Vector((1, 1, 1)):
            apply_xform(p)
    keep_uv = any(p.get("keep_uv") for p in flat)
    ob = bsk.join(flat, name)
    if not keep_uv:
        bsk.uv_box(ob, uv_scale)
    # merge coincident verts inside each part is unnecessary; just clean loose
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bm.to_mesh(ob.data)
    bm.free()
    bsk.shade(ob, True, smooth_angle)
    return ob


def ground(ob, centre_xy=True):
    """Put the bottom centre of the bounding box of `ob` (+children) at world origin."""
    pts = []
    def walk(o):
        if o.type == "MESH":
            pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
        for c in o.children:
            walk(c)
    walk(ob)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    off = Vector(((lo.x + hi.x) / 2 if centre_xy else 0, (lo.y + hi.y) / 2 if centre_xy else 0, lo.z))
    # shift geometry of every mesh in the tree so that root sits at origin
    def shift(o):
        if o.type == "MESH":
            for v in o.data.vertices:
                v.co -= off
            o.data.update()
        for c in o.children:
            shift(c)
    shift(ob)
    return hi - lo


def assemble(name, body_parts, children=None):
    """Root for a prop. children = {"screen": [parts...], ...} become separate child meshes (same origin as root)."""
    body = merge(body_parts, name if not children else name + "_body")
    if not children:
        ground(body)
        body.location = (0, 0, 0)
        return body
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    body.parent = root
    for cname, cparts in children.items():
        c = merge(cparts, cname)
        c.parent = root
    size = ground(root)
    for c in root.children:
        c.location = (0, 0, 0)
    return root


def dims(ob):
    pts = []
    def walk(o):
        if o.type == "MESH":
            pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
        for c in o.children:
            walk(c)
    walk(ob)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return [round(v, 4) for v in (hi - lo)]


def roles_of(ob):
    rs = set()
    def walk(o):
        if o.type == "MESH":
            for s in o.material_slots:
                if s.material:
                    rs.add(s.material.name.split(".")[0])
        for c in o.children:
            walk(c)
    walk(ob)
    return sorted(rs)


MANIFEST_PATH = os.path.join(bsk.ROOT, "Art", "Source", "blender", "manifest_electronics.json")


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"family": "electronics", "front": "-Y", "origin": "bottom centre", "new_roles": sorted(NEW_ROLES.keys()), "props": []}


def save_manifest(m):
    m["new_roles"] = sorted(NEW_ROLES.keys())
    m["props"].sort(key=lambda p: p["name"])
    with open(MANIFEST_PATH, "w") as f:
        json.dump(m, f, indent=1)


def record(manifest, ob, name, category, notes, variant_of=None):
    entry = {"name": name, "file": f"Assets/Bedsit/Art/Models/electronics/{name}.fbx", "category": category,
             "dims_m": dims(ob), "tris": tris(ob), "roles": roles_of(ob), "variant_of": variant_of, "notes": notes,
             "children": [c.name for c in ob.children] if ob.type == "EMPTY" else []}
    manifest["props"] = [p for p in manifest["props"] if p["name"] != name] + [entry]
    return entry
