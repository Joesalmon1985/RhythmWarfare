"""bsk - shared helpers for the Bedsit prop kit (Blender 4.5 Python).

Run a family script headless:
    "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P Art/Source/blender/<family>.py

Conventions (the Unity importer relies on these):
  * 1 Blender unit = 1 metre, +Z up in Blender; export converts to Unity (Y up, -Z forward).
  * The object ORIGIN is the point that sits on the floor/surface (bottom centre) unless stated.
    The FRONT of an object faces Blender -Y (exports to Unity +Z facing the room).
  * Every material name is a *role* name from MATERIALS below ("cotton_white", "wood_dark", "plastic_black"...).
    Unity maps role names to its own PBR materials, so authoring colours here are only a fallback/preview.
  * Each exported file contains ONE prop (a single root object, children allowed) named after the file.
  * Meshes get UVs: box-projected in metres (texel density consistent) unless a family unwraps itself.
"""
import bpy, bmesh, math, random, os, sys
from mathutils import Vector, Matrix, Euler

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))        # .../UnityBedsitPOC
OUT_MODELS = os.path.join(ROOT, "Assets", "Bedsit", "Art", "Models")
OUT_PREVIEW = os.path.join(ROOT, "Art", "Source", "previews")

# role -> (base colour linear-ish sRGB, roughness, metallic)  fallback look; Unity library overrides
MATERIALS = {
    "plaster_warm": ((0.86, 0.80, 0.70), 0.9, 0.0),
    "wood_light": ((0.62, 0.45, 0.28), 0.6, 0.0),
    "wood_dark": ((0.28, 0.17, 0.10), 0.55, 0.0),
    "wood_painted_white": ((0.88, 0.87, 0.82), 0.5, 0.0),
    "cotton_white": ((0.88, 0.88, 0.85), 0.95, 0.0),
    "cotton_blue": ((0.22, 0.34, 0.58), 0.95, 0.0),
    "cotton_red": ((0.62, 0.14, 0.12), 0.95, 0.0),
    "cotton_grey": ((0.45, 0.45, 0.47), 0.95, 0.0),
    "cotton_black": ((0.07, 0.07, 0.08), 0.95, 0.0),
    "cotton_green": ((0.22, 0.45, 0.30), 0.95, 0.0),
    "cotton_yellow": ((0.85, 0.70, 0.20), 0.95, 0.0),
    "denim": ((0.14, 0.22, 0.38), 0.95, 0.0),
    "leather_brown": ((0.30, 0.17, 0.09), 0.5, 0.0),
    "leather_black": ((0.05, 0.05, 0.05), 0.45, 0.0),
    "rubber_black": ((0.03, 0.03, 0.03), 0.8, 0.0),
    "plastic_black": ((0.04, 0.04, 0.045), 0.35, 0.0),
    "plastic_white": ((0.85, 0.85, 0.82), 0.4, 0.0),
    "plastic_grey": ((0.35, 0.35, 0.37), 0.45, 0.0),
    "plastic_red": ((0.7, 0.1, 0.08), 0.4, 0.0),
    "plastic_blue": ((0.1, 0.25, 0.7), 0.4, 0.0),
    "plastic_green": ((0.1, 0.5, 0.2), 0.4, 0.0),
    "metal_steel": ((0.62, 0.63, 0.65), 0.35, 1.0),
    "metal_dark": ((0.15, 0.15, 0.16), 0.4, 1.0),
    "metal_brass": ((0.70, 0.55, 0.25), 0.35, 1.0),
    "ceramic_white": ((0.90, 0.90, 0.88), 0.2, 0.0),
    "ceramic_blue": ((0.20, 0.35, 0.65), 0.2, 0.0),
    "ceramic_dirty": ((0.62, 0.55, 0.45), 0.3, 0.0),
    "glass_clear": ((0.85, 0.92, 0.95), 0.05, 0.0),
    "glass_green": ((0.10, 0.35, 0.15), 0.05, 0.0),
    "glass_brown": ((0.30, 0.15, 0.04), 0.05, 0.0),
    "paper_white": ((0.92, 0.91, 0.86), 0.9, 0.0),
    "paper_yellow": ((0.85, 0.78, 0.50), 0.9, 0.0),
    "cardboard": ((0.60, 0.45, 0.28), 0.9, 0.0),
    "foil": ((0.75, 0.75, 0.78), 0.25, 1.0),
    "liquid_coffee": ((0.12, 0.06, 0.03), 0.1, 0.0),
    "liquid_beer": ((0.55, 0.32, 0.05), 0.1, 0.0),
    "food_pizza": ((0.65, 0.35, 0.12), 0.8, 0.0),
    "screen_off": ((0.02, 0.025, 0.03), 0.08, 0.0),
    "screen_on": ((0.35, 0.60, 0.95), 0.1, 0.0),       # emissive in Unity
    "led_green": ((0.1, 1.0, 0.2), 0.3, 0.0),           # emissive in Unity
    "led_red": ((1.0, 0.1, 0.05), 0.3, 0.0),            # emissive in Unity
    "fabric_pattern": ((0.60, 0.55, 0.50), 0.95, 0.0),
    "skin": ((0.8, 0.6, 0.5), 0.7, 0.0),
}

_mat_cache = {}


def mat(role):
    """Return (creating if needed) the Principled material for a role name."""
    if role in _mat_cache and _mat_cache[role].name in bpy.data.materials:
        return _mat_cache[role]
    col, rough, metal = MATERIALS.get(role, ((0.5, 0.5, 0.5), 0.6, 0.0))
    m = bpy.data.materials.new(role)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if role.startswith("glass"):
        b.inputs["Alpha"].default_value = 0.35
    m.diffuse_color = (col[0], col[1], col[2], 1)
    _mat_cache[role] = m
    return m


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.images, bpy.data.cameras, bpy.data.lights):
        for b in list(coll):
            coll.remove(b)
    _mat_cache.clear()


# ------------------------------------------------------------------------------------------------ mesh builders

def _obj_from_bm(bm, name, roles=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for r in (roles or []):
        ob.data.materials.append(mat(r))
    return ob


def new_bm():
    return bmesh.new()


def finish(bm, name, role, smooth=True, uv_scale=1.0, bevel=0.0, bevel_segments=2):
    """bmesh -> object with a single material role; optionally bevel hard edges via modifier."""
    ob = _obj_from_bm(bm, name, [role])
    shade(ob, smooth)
    if bevel > 0:
        add_bevel(ob, bevel, bevel_segments)
    uv_box(ob, uv_scale)
    return ob


def shade(ob, smooth=True, angle=40):
    for p in ob.data.polygons:
        p.use_smooth = smooth
    if smooth:
        try:   # Blender 4.1+: auto smooth by angle via modifier-less approach
            ob.data.shade_smooth()
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True)
            bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
            ob.select_set(False)
        except Exception:
            pass


def add_bevel(ob, width=0.004, segments=2, angle=35):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = True
    return m


def box(name, size, role, center=(0, 0, 0), bevel=0.004, segments=2, origin="center"):
    """Bevelled box. size=(x,y,z) metres. origin 'bottom' puts the origin at the bottom centre."""
    bm = new_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    ob = _obj_from_bm(bm, name, [role])
    ob.location = center
    if origin == "bottom":
        ob.location = (center[0], center[1], center[2] + size[2] / 2)
    shade(ob, False)
    if bevel > 0:
        add_bevel(ob, bevel, segments)
    uv_box(ob, 1.0)
    return ob


def cylinder(name, radius, height, role, segments=24, center=(0, 0, 0), bevel=0.003, r_top=None, cap=True, origin="bottom"):
    bm = new_bm()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments, radius1=radius,
                          radius2=(radius if r_top is None else r_top), depth=height)
    ob = _obj_from_bm(bm, name, [role])
    ob.location = (center[0], center[1], center[2] + (height / 2 if origin == "bottom" else 0))
    shade(ob, True)
    if bevel > 0:
        add_bevel(ob, bevel, 2)
    uv_box(ob, 1.0)
    return ob


def lathe(name, profile, role, segments=32, center=(0, 0, 0), smooth=True, close_top=False):
    """Surface of revolution about Z. profile=[(radius, z), ...] bottom->top. A radius of 0 closes the end."""
    bm = new_bm()
    rings = []
    for (r, z) in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments), z)) for i in range(segments)])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj_from_bm(bm, name, [role])
    ob.location = center
    shade(ob, smooth)
    uv_cyl(ob)
    return ob


def tube(name, points, radius, role, segments=8, round_caps=True):
    """Tube following a polyline/curve of Vector points (cables, straps, cords)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = max(1, segments // 4)
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, v in zip(sp.points, points):
        p.co = (v[0], v[1], v[2], 1)
    sp.use_smooth = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat(role))
    return ob


def to_mesh(ob):
    """Convert curve/modifiers to a real mesh object (applies modifiers)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    new = bpy.data.objects.new(ob.name, me)
    new.matrix_world = ob.matrix_world
    bpy.context.collection.objects.link(new)
    for slot in ob.material_slots:
        new.data.materials.append(slot.material)
    bpy.data.objects.remove(ob)
    return new


def displace_noise(ob, strength=0.01, scale=0.15, seed=0, along_normal=True):
    """Procedural noise displacement (wear, creases, crumple) applied directly to vertices."""
    rnd = random.Random(seed)
    ox, oy, oz = rnd.random() * 100, rnd.random() * 100, rnd.random() * 100
    from mathutils import noise
    me = ob.data
    me.calc_normals_split() if hasattr(me, "calc_normals_split") else None
    for v in me.vertices:
        n = noise.noise(Vector((v.co.x / scale + ox, v.co.y / scale + oy, v.co.z / scale + oz)))
        v.co += (v.normal if along_normal else Vector((0, 0, 1))) * n * strength
    me.update()


def subdivide(ob, cuts=1):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()


def subsurf(ob, level=1):
    m = ob.modifiers.new("subsurf", "SUBSURF")
    m.levels = level
    m.render_levels = level
    return m


def solidify(ob, thickness=0.004, offset=0.0):
    m = ob.modifiers.new("solidify", "SOLIDIFY")
    m.thickness = thickness
    m.offset = offset
    return m


def apply_modifiers(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception as e:
            print("modifier apply failed", m.name, e)


# ------------------------------------------------------------------------------------------------ UVs

def uv_box(ob, scale=1.0, tex_metres=1.0):
    """Box-project UVs in metres: one UV unit = tex_metres metres * scale."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    s = 1.0 / (tex_metres * scale)
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                uv[li].uv = (co.y * s, co.z * s)
            elif ax == 1:
                uv[li].uv = (co.x * s, co.z * s)
            else:
                uv[li].uv = (co.x * s, co.y * s)


def uv_cyl(ob, tex_metres=1.0):
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u = (math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0
            uv[li].uv = (u, co.z / tex_metres)


def uv_smart(ob, angle=66, margin=0.02):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.select_set(False)


# ------------------------------------------------------------------------------------------------ assembling & export

def join(objs, name, origin_world=None):
    """Join mesh objects into one object (keeps material slots)."""
    objs = [o for o in objs if o.type == "MESH"]
    for o in objs:
        if o.modifiers:
            apply_modifiers(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    ob.select_set(False)
    return ob


def parent_all(objs, name):
    """Empty root + children (keeps separate meshes, e.g. animated parts)."""
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for o in objs:
        o.parent = root
    return root


def set_origin_bottom(ob):
    """Move the mesh so its origin is the bottom centre of its bounding box."""
    me = ob.data
    zs = [v.co.z for v in me.vertices]
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    off = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in me.vertices:
        v.co -= off
    ob.location += off


def bounds(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def export_fbx(root_objs, family, name):
    """Export root object(s) (and children) as Assets/Bedsit/Art/Models/<family>/<name>.fbx ."""
    if not isinstance(root_objs, (list, tuple)):
        root_objs = [root_objs]
    d = os.path.join(OUT_MODELS, family)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name + ".fbx")
    bpy.ops.object.select_all(action="DESELECT")
    sel = []
    def walk(o):
        sel.append(o)
        for c in o.children:
            walk(c)
    for r in root_objs:
        walk(r)
    for o in sel:
        o.select_set(True)
    bpy.context.view_layer.objects.active = sel[0]
    sel[0].name = name
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                             axis_forward="-Z", axis_up="Y", bake_space_transform=True, object_types={"MESH", "EMPTY"},
                             use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False, path_mode="COPY" if False else "AUTO")
    return path


def preview(objs, name, size=(640, 480), views=("front34",), fit=1.0, bg=(0.18, 0.18, 0.2)):
    """Render a quick Workbench PNG (materials' viewport colours) to Art/Source/previews/<name>.png ."""
    os.makedirs(OUT_PREVIEW, exist_ok=True)
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    allp = []
    def walk(o):
        if o.type == "MESH":
            allp.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
        for c in o.children:
            walk(c)
    for o in objs:
        walk(o)
    lo = Vector((min(p.x for p in allp), min(p.y for p in allp), min(p.z for p in allp)))
    hi = Vector((max(p.x for p in allp), max(p.y for p in allp), max(p.z for p in allp)))
    c = (lo + hi) / 2
    r = max((hi - lo).length / 2, 0.05) * fit
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = "BOTH"
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.color = bg
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 50
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    outs = []
    for v in views:
        d = {"front34": Vector((-0.6, -1, 0.7)), "front": Vector((0, -1, 0.15)), "top": Vector((0, -0.05, 1)), "side": Vector((1, 0, 0.2)),
             "back34": Vector((0.6, 1, 0.7))}[v].normalized()
        cam.location = c + d * r * 3.2
        look = (c - cam.location).to_track_quat("-Z", "Y")
        cam.rotation_euler = look.to_euler()
        p = os.path.join(OUT_PREVIEW, f"{name}_{v}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        outs.append(p)
    bpy.data.objects.remove(cam)
    return outs


def contact_sheet_note():
    return "Use preview() on every prop and LOOK at the PNGs before exporting."
