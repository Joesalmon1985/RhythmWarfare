"""lib_textiles - soft-goods helpers for the `textiles` family (Blender 4.5 Python).

Everything here builds on bsk.py (do not edit that one).  The main tools:
  * grid_surface(rows, ...)   -> open or tubular surface from a 2D array of points (+optional solidify)
  * crease_rows(rows, ...)    -> fbm crease displacement along the local normal of a point grid
  * pillow(...)               -> closed seam-edged cushion (pillows, cushions, garment bodies, heaps)
  * grid_box(...)             -> densely tessellated bevelled box (mattress, folded items, bag bodies)
  * soft_tube(...)            -> creased tube along a Catmull-Rom path, tapered, round caps (sleeves, legs, socks)
  * tube_curve / strap        -> smooth round / flat straps along a path (laces, zips, handles, straps)
  * wicker_basket(...)        -> woven basket shell
  * assign_role_by(...)       -> second material slot by face position (stripes, borders, patches)
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler, noise
import bsk
from bsk import *

# ------------------------------------------------------------------------------------------------ roles
NEW_ROLES = {
    "fabric_ticking": ((0.82, 0.80, 0.72), 0.92, 0.0),      # cream mattress ticking (stripes in Unity)
    "fabric_duvet": ((0.40, 0.52, 0.50), 0.96, 0.0),        # dusty teal duvet cover
    "cotton_pale_blue": ((0.64, 0.72, 0.82), 0.96, 0.0),    # fitted sheet / pillowcase b
    "cotton_marl": ((0.55, 0.55, 0.56), 0.97, 0.0),         # grey marl hoodie / jumper
    "cotton_navy": ((0.12, 0.15, 0.26), 0.96, 0.0),
    "knit_mustard": ((0.76, 0.56, 0.16), 0.98, 0.0),        # chunky throw
    "terry_teal": ((0.14, 0.46, 0.48), 0.98, 0.0),
    "terry_white": ((0.90, 0.90, 0.87), 0.98, 0.0),
    "wicker": ((0.70, 0.52, 0.30), 0.85, 0.0),
    "nylon_navy": ((0.10, 0.13, 0.26), 0.70, 0.0),
    "nylon_olive": ((0.30, 0.32, 0.20), 0.70, 0.0),
    "foam_white": ((0.88, 0.88, 0.86), 0.60, 0.0),           # trainer midsole
    "rubber_gum": ((0.72, 0.52, 0.30), 0.60, 0.0),           # gum outsole
    "fabric_rug_border": ((0.38, 0.17, 0.15), 0.95, 0.0),    # rust red rug border
    "fabric_curtain": ((0.55, 0.32, 0.20), 0.95, 0.0),       # burnt orange curtains
}
for _k, _v in NEW_ROLES.items():
    MATERIALS.setdefault(_k, _v)


# ------------------------------------------------------------------------------------------------ maths
def fbm(p, scale=0.1, octaves=3, seed=0):
    """Multi-octave Perlin in [-1, 1] sampled at world point p (Vector)."""
    ox = seed * 17.17
    v = Vector((p.x / scale + ox, p.y / scale + ox * 0.37 + 3.1, p.z / scale + ox * 1.91 + 7.7))
    a = 0.0; amp = 1.0; tot = 0.0; f = 1.0
    for _ in range(octaves):
        a += amp * noise.noise(v * f)
        tot += amp; amp *= 0.5; f *= 2.03
    return a / tot


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def gauss(d, s):
    return math.exp(-(d * d) / (2 * s * s))


def catmull_rom(pts, samples=6):
    """Smoothly sample a polyline of Vectors (Catmull-Rom)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    if n < 2:
        return pts
    out = []
    for i in range(n - 1):
        p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, n - 1)]
        for s in range(samples):
            t = s / samples
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return out


def scalar_keys(keys, t):
    """Piecewise Catmull-Rom interpolation of [(t, value), ...] sorted by t."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, v0 = keys[i]; t1, v1 = keys[i + 1]
        if t0 <= t <= t1:
            vm = keys[max(i - 1, 0)][1]; vp = keys[min(i + 2, len(keys) - 1)][1]
            s = (t - t0) / (t1 - t0)
            return 0.5 * ((2 * v0) + (-vm + v1) * s + (2 * vm - 5 * v0 + 4 * v1 - vp) * s * s
                          + (-vm + 3 * v0 - 3 * v1 + vp) * s * s * s)
    return keys[-1][1]


def frames_along(samples):
    """Parallel-transport frames for a list of points -> list of (tangent, normal, binormal)."""
    n = len(samples)
    tans = []
    for i in range(n):
        a = samples[max(i - 1, 0)]; b = samples[min(i + 1, n - 1)]
        t = (b - a)
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 1, 0)))
    up = Vector((0, 0, 1))
    if abs(tans[0].dot(up)) > 0.95:
        up = Vector((1, 0, 0))
    nrm = tans[0].cross(up).normalized()
    frames = []
    for i in range(n):
        t = tans[i]
        nrm = (nrm - t * nrm.dot(t))
        if nrm.length < 1e-6:
            nrm = t.cross(Vector((0, 0, 1)))
            if nrm.length < 1e-6:
                nrm = t.cross(Vector((1, 0, 0)))
        nrm.normalize()
        frames.append((t, nrm, t.cross(nrm).normalized()))
    return frames


# ------------------------------------------------------------------------------------------------ surfaces
def crease_rows(rows, strength, scale, seed=0, octaves=3, wrap=False, mask=None):
    """Displace a point grid along its local normal with fbm noise. mask(u, v) -> 0..1 optional."""
    nu = len(rows); nv = len(rows[0])
    out = [[None] * nv for _ in range(nu)]
    for i in range(nu):
        for j in range(nv):
            p = rows[i][j]
            du = rows[min(i + 1, nu - 1)][j] - rows[max(i - 1, 0)][j]
            if wrap:
                dv = rows[i][(j + 1) % nv] - rows[i][(j - 1) % nv]
            else:
                dv = rows[i][min(j + 1, nv - 1)] - rows[i][max(j - 1, 0)]
            n = du.cross(dv)
            n = n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))
            m = 1.0 if mask is None else mask(i / max(nu - 1, 1), j / max(nv - 1, 1))
            out[i][j] = p + n * (fbm(p, scale, octaves, seed) * strength * m)
    return out


def grid_surface(name, rows, role, wrap=False, thickness=0.0, offset=0.0, uv_scale=(1.0, 1.0), merge=1e-6,
                 smooth=True, angle=70, flip=False, roles=None):
    """rows: list of rows (list of Vectors). Faces between consecutive rows; wrap -> last column joins first.
    thickness>0 -> Solidify applied (offset -1..1). UVs are (row index, column index) scaled."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    nu = len(rows); nv = len(rows[0])
    verts = [[bm.verts.new(p) for p in row] for row in rows]
    ncols = nv if wrap else nv - 1
    for i in range(nu - 1):
        for j in range(ncols):
            j2 = (j + 1) % nv
            vs = [verts[i][j], verts[i + 1][j], verts[i + 1][j2], verts[i][j2]]
            uvs = [(i / (nu - 1), j / ncols), ((i + 1) / (nu - 1), j / ncols),
                   ((i + 1) / (nu - 1), (j + 1) / ncols), (i / (nu - 1), (j + 1) / ncols)]
            if flip:
                vs.reverse(); uvs.reverse()
            if len(set(map(id, vs))) < 4:
                continue
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            for l, uv in zip(f.loops, uvs):
                l[uvl].uv = (uv[0] * uv_scale[0], uv[1] * uv_scale[1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    bmesh.ops.dissolve_degenerate(bm, dist=merge, edges=bm.edges)
    ob = bsk._obj_from_bm(bm, name, roles or [role])
    if thickness > 0:
        m = ob.modifiers.new("solid", "SOLIDIFY")
        m.thickness = thickness
        m.offset = offset
        m.use_even_offset = True
        m.use_quality_normals = True
        apply_modifiers(ob)
    shade(ob, smooth, angle)
    return ob


def pillow_profile(u, v, w, d, h, p=4.0, k=0.55, top_frac=0.62, shape=None):
    """Square (u,v) -> point on a superellipse-outlined cushion: returns (x, y, z_top, z_bottom) before the
    bottom is rested on z=0. The square's corners are pulled in onto the superellipse so there is no flat skirt."""
    a, b = 2 * u - 1, 2 * v - 1
    r_inf = max(abs(a), abs(b))
    if r_inf > 1e-9:
        r_p = (abs(a) ** p + abs(b) ** p) ** (1 / p)
        f = r_inf / r_p
    else:
        f = 1.0
    x = a * f * w / 2; y = b * f * d / 2
    t = h * (max(0.0, 1 - r_inf * r_inf)) ** k
    mt, mb, dz = (1.0, 1.0, 0.0) if shape is None else shape(u, v)
    return x, y, t * top_frac * mt + dz, -t * (1 - top_frac) * mb + dz


def pillow(name, w, d, h, role, nu=24, nv=18, p=4.0, k=0.55, seed=0, crease=0.012, crease_scale=0.09,
           octaves=3, shape=None, top_frac=0.62, angle=75, uv_scale=1.0):
    """Closed, seam-edged cushion centred on the origin, resting on z=0 (bottom at z=0).
    w, d, h = width (x), depth (y), total thickness. p = superellipse exponent (corner squareness),
    k = edge softness (0.5 = round edge, 0.3 = fatter). shape(u, v) -> (top_mult, bot_mult, dz)."""
    top = [[None] * (nv + 1) for _ in range(nu + 1)]
    bot = [[None] * (nv + 1) for _ in range(nu + 1)]
    for i in range(nu + 1):
        for j in range(nv + 1):
            u = i / nu; v = j / nv
            x, y, zt, zb = pillow_profile(u, v, w, d, h, p, k, top_frac, shape)
            top[i][j] = Vector((x, y, zt))
            bot[i][j] = Vector((x, y, zb))
    if crease > 0:
        rim_mask = lambda u, v: smoothstep(0.0, 0.12, min(u, 1 - u, v, 1 - v))
        top = crease_rows(top, crease, crease_scale, seed, octaves, mask=rim_mask)
        bot = crease_rows(bot, crease * 0.6, crease_scale, seed + 5, octaves, mask=rim_mask)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vt = [[None] * (nv + 1) for _ in range(nu + 1)]
    vb = [[None] * (nv + 1) for _ in range(nu + 1)]
    for i in range(nu + 1):
        for j in range(nv + 1):
            vt[i][j] = bm.verts.new(top[i][j])
            if i in (0, nu) or j in (0, nv):
                vb[i][j] = vt[i][j]
            else:
                vb[i][j] = bm.verts.new(bot[i][j])

    def mk(vs, uvs):
        if len(set(map(id, vs))) < 4:
            return
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        for l, uv in zip(f.loops, uvs):
            l[uvl].uv = (uv[0] * uv_scale, uv[1] * uv_scale)
    for i in range(nu):
        for j in range(nv):
            u0, u1, v0, v1 = i / nu * w, (i + 1) / nu * w, j / nv * d, (j + 1) / nv * d
            mk([vt[i][j], vt[i + 1][j], vt[i + 1][j + 1], vt[i][j + 1]], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
            mk([vb[i][j], vb[i][j + 1], vb[i + 1][j + 1], vb[i + 1][j]],
               [(u0, v0 + d + 0.02), (u0, v1 + d + 0.02), (u1, v1 + d + 0.02), (u1, v0 + d + 0.02)])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= zmin
    ob = bsk._obj_from_bm(bm, name, [role])
    shade(ob, True, angle)
    return ob


def rim_points(w, d, p=4.0, n=64, z=0.0):
    """Closed superellipse loop (for piping along a pillow seam)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        x = math.copysign(abs(c) ** (2 / p), c) * w / 2
        y = math.copysign(abs(s) ** (2 / p), s) * d / 2
        pts.append(Vector((x, y, z)))
    return pts


def grid_box(name, dims, n, role, center=(0, 0, 0), bevel=0.0, bevel_segments=4, origin="bottom"):
    """Box whose 6 faces are grids (nx, ny, nz cells); bevelled edges applied.
    origin 'bottom' -> mesh z from 0..h at the object origin."""
    w, d, h = dims; nx, ny, nz = n
    bm = bmesh.new()
    vmap = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            for k in range(nz + 1):
                if i in (0, nx) or j in (0, ny) or k in (0, nz):
                    vmap[(i, j, k)] = bm.verts.new(((i / nx - 0.5) * w, (j / ny - 0.5) * d,
                                                    (k / nz) * h if origin == "bottom" else (k / nz - 0.5) * h))

    def quad(a, b, c, d_):
        bm.faces.new((vmap[a], vmap[b], vmap[c], vmap[d_]))
    for i in range(nx):
        for j in range(ny):
            quad((i, j, nz), (i + 1, j, nz), (i + 1, j + 1, nz), (i, j + 1, nz))
            quad((i, j, 0), (i, j + 1, 0), (i + 1, j + 1, 0), (i + 1, j, 0))
    for i in range(nx):
        for k in range(nz):
            quad((i, 0, k), (i + 1, 0, k), (i + 1, 0, k + 1), (i, 0, k + 1))
            quad((i, ny, k), (i, ny, k + 1), (i + 1, ny, k + 1), (i + 1, ny, k))
    for j in range(ny):
        for k in range(nz):
            quad((0, j, k), (0, j, k + 1), (0, j + 1, k + 1), (0, j + 1, k))
            quad((nx, j, k), (nx, j + 1, k), (nx, j + 1, k + 1), (nx, j, k + 1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bsk._obj_from_bm(bm, name, [role])
    ob.location = center
    if bevel > 0:
        add_bevel(ob, bevel, bevel_segments)
        apply_modifiers(ob)
    uv_box(ob, 1.0)
    shade(ob, True, 60)
    return ob


def displace(ob, fn):
    """fn(co, normal) -> new co, applied to every vertex (object local space)."""
    me = ob.data
    for v in me.vertices:
        v.co = fn(v.co.copy(), v.normal.copy())
    me.update()


def noise_displace(ob, strength, scale, seed=0, octaves=3, mask=None):
    me = ob.data
    for v in me.vertices:
        m = 1.0 if mask is None else mask(v.co)
        v.co += v.normal * (fbm(v.co, scale, octaves, seed) * strength * m)
    me.update()


def subsurf_apply(ob, level=1):
    subsurf(ob, level)
    apply_modifiers(ob)


def soft_tube(name, path, radius, role, segs=14, samples=5, taper=None, caps="round", seed=0,
              crease=0.004, crease_scale=0.05, squash=1.0, uv_scale=1.0, angle=75):
    """Creased tube along a Catmull-Rom path. taper(t)->radius multiplier. squash<1 flattens vertically
    (collapsed garment). caps 'round' closes the ends with hemispheres, None leaves them open."""
    pts = catmull_rom(path, samples)
    frames = frames_along(pts)
    rows = []
    n = len(pts)
    for i, (c, (t, nrm, bin_)) in enumerate(zip(pts, frames)):
        tt = i / (n - 1)
        r = radius * (taper(tt) if taper else 1.0)
        ring = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            off = nrm * math.cos(a) * r + bin_ * math.sin(a) * r
            off.z *= squash
            ring.append(c + off)
        rows.append(ring)
    if caps == "round":
        ends = []
        for sign, idx in ((-1, 0), (1, n - 1)):
            c = pts[idx]; t, nrm, bin_ = frames[idx]
            tt = idx / (n - 1)
            r = radius * (taper(tt) if taper else 1.0)
            cap = []
            for s in (0.55, 0.85, 1.0):
                rr = r * math.sqrt(max(0.0, 1 - s * s))
                ring = []
                for j in range(segs):
                    a = 2 * math.pi * j / segs
                    off = nrm * math.cos(a) * rr + bin_ * math.sin(a) * rr
                    off.z *= squash
                    ring.append(c + off + t * (sign * s * r * 0.8))
                cap.append(ring)
            ends.append(cap)
        rows = list(reversed(ends[0])) + rows + ends[1]
    if crease > 0:
        rows = crease_rows(rows, crease, crease_scale, seed, 3, wrap=True)
    return grid_surface(name, rows, role, wrap=True, uv_scale=(uv_scale, uv_scale), angle=angle)


def tube_curve(name, pts, radius, role, cyclic=False, res=4, smooth_pts=0):
    """Round tube on a (optionally Catmull-Rom smoothed) path, converted to mesh."""
    if smooth_pts:
        pts = catmull_rom(pts, smooth_pts)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = res
    cu.use_fill_caps = not cyclic
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, v in zip(sp.points, pts):
        p.co = (v[0], v[1], v[2], 1)
    sp.use_cyclic_u = cyclic
    sp.use_smooth = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat(role))
    ob = to_mesh(ob)
    shade(ob, True, 60)
    uv_box(ob, 1.0)
    return ob


def strap(name, pts, width, thickness, role, smooth_pts=4, hint=None):
    """Flat webbing strap along a path. The strap lies flat against the surface whose normal is `hint`
    (width direction = tangent x hint). hint defaults to the path's own best-fit normal."""
    pts = catmull_rom(pts, smooth_pts) if smooth_pts else [Vector(p) for p in pts]
    if hint is None:
        # best-fit: average cross of consecutive segments, fallback Z
        acc = Vector((0, 0, 0))
        for a, b, c in zip(pts[:-2], pts[1:-1], pts[2:]):
            acc += (b - a).cross(c - b)
        hint = acc.normalized() if acc.length > 1e-9 else Vector((0, 0, 1))
    hint = Vector(hint).normalized()
    n = len(pts)
    rows = []
    for i in range(n):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        t = (b - a).normalized()
        wdir = t.cross(hint)
        if wdir.length < 1e-6:
            wdir = t.cross(Vector((1, 0, 0)))
        wdir.normalize()
        rows.append([pts[i] - wdir * width / 2, pts[i] + wdir * width / 2])
    return grid_surface(name, rows, role, thickness=thickness, offset=0.0, uv_scale=(1.0, 0.2), angle=50)


def wicker_basket(name, r_bottom, r_top, height, role, rows=24, stakes=24, bump=0.0045, thickness=0.006,
                  profile=None):
    """Woven round basket shell (open top). profile(t)->radius multiplier for belly shapes."""
    segs = stakes * 2
    grid = []
    for k in range(rows + 1):
        t = k / rows
        z = t * height
        r = lerp(r_bottom, r_top, t) * (profile(t) if profile else 1.0)
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            weave = bump * (1 if (i + k) % 2 == 0 else -1)
            if k in (0, rows):
                weave = 0.0
            rr = r + weave
            ring.append(Vector((rr * math.cos(a), rr * math.sin(a), z)))
        grid.append(ring)
    ob = grid_surface(name, grid, role, wrap=True, thickness=thickness, offset=0.0, uv_scale=(2, 8), angle=50)
    return ob


def assign_role_by(ob, role, pred):
    """Give faces whose centre satisfies pred(center_local) a second material slot (role)."""
    me = ob.data
    m = mat(role)
    if m.name not in [x.name for x in me.materials if x]:
        me.materials.append(m)
    idx = [x.name if x else "" for x in me.materials].index(m.name)
    for p in me.polygons:
        if pred(p.center):
            p.material_index = idx


def transform_mesh(ob, matrix):
    """Bake a matrix into the mesh data (object transform untouched)."""
    me = ob.data
    for v in me.vertices:
        v.co = matrix @ v.co
    me.update()


def rest_on_floor(ob, z=0.0):
    lo, hi = bounds(ob)
    ob.location.z += z - lo.z


def set_origin_world(ob, point=(0, 0, 0)):
    """Make the object's origin the given world point without moving the geometry."""
    mw = ob.matrix_world.copy()
    me = ob.data
    pt = Vector(point)
    for v in me.vertices:
        v.co = mw @ v.co - pt
    me.update()
    ob.matrix_world = Matrix.Translation(pt)


def origin_bottom_centre(ob):
    """Origin -> bottom centre of world bounding box."""
    lo, hi = bounds(ob)
    set_origin_world(ob, ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    ob.location = (0, 0, 0)        # mesh now lives around its own bottom-centre pivot; park the pivot at the world origin


def place(ob, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    """Set world transform (rotation in degrees XYZ)."""
    ob.location = loc
    ob.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")
    if scale:
        ob.scale = scale
    return ob


def mark_sharp_by_angle(root, angle=40.0):
    """Blender 4.1+ has no auto-smooth flag: mark edges sharp where the face angle exceeds `angle` so the FBX
    carries split normals on hard edges (soft meshes with big creases get a few sharps, which is fine)."""
    cos_lim = math.cos(math.radians(angle))

    def walk(o):
        if o.type == "MESH":
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.normal_update()
            for e in bm.edges:
                if len(e.link_faces) == 2:
                    n0, n1 = e.link_faces[0].normal, e.link_faces[1].normal
                    e.smooth = not (n0.dot(n1) < cos_lim)
            bm.to_mesh(o.data)
            bm.free()
            for p in o.data.polygons:
                p.use_smooth = True
        for c in o.children:
            walk(c)
    walk(root)


def tri_count(root):
    n = 0
    dg = bpy.context.evaluated_depsgraph_get()

    def walk(o):
        nonlocal n
        if o.type == "MESH":
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            n += sum(len(p.vertices) - 2 for p in me.polygons)
            ev.to_mesh_clear()
        for c in o.children:
            walk(c)
    walk(root)
    return n


def dims_of(root):
    pts = []

    def walk(o):
        if o.type == "MESH":
            pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
        for c in o.children:
            walk(c)
    walk(root)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def roles_of(root):
    out = []

    def walk(o):
        if o.type == "MESH":
            for s in o.material_slots:
                if s.material and s.material.name not in out:
                    out.append(s.material.name)
        for c in o.children:
            walk(c)
    walk(root)
    return out


def contact_sheet(paths, out_path, cols=3):
    """Tile PNG previews into one image using numpy (for quick visual QA)."""
    import numpy as np
    imgs = []
    for p in paths:
        if not os.path.exists(p):
            continue
        im = bpy.data.images.load(p)
        w, h = im.size
        arr = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        imgs.append(arr)
        bpy.data.images.remove(im)
    if not imgs:
        return None
    h, w = imgs[0].shape[:2]
    rows = (len(imgs) + cols - 1) // cols
    sheet = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        r = rows - 1 - r          # Blender pixel rows run bottom-up: keep reading order top-left first
        ih, iw = im.shape[:2]
        sheet[r * h:r * h + ih, c * w:c * w + iw] = im
    out = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
    out.pixels[:] = sheet.ravel().tolist()
    out.filepath_raw = out_path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    return out_path
