"""exterior_club_building: a converted-warehouse nightclub seen across the street (viewed from ~8-14 m).
Origin = ground level, front-centre; front faces Blender -Y (Unity +Z). 12 m wide, 8.5 m high, 9 m deep.
Run: blender -b -P Art/Source/blender/club.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from bsk import *

MATERIALS["neon_pink"] = ((1.0, 0.2, 0.7), 0.3, 0.0)
MATERIALS["neon_cyan"] = ((0.2, 0.9, 1.0), 0.3, 0.0)
MATERIALS["poster_a"] = ((0.95, 0.75, 0.1), 0.6, 0.0)
MATERIALS["poster_b"] = ((0.15, 0.7, 0.95), 0.6, 0.0)
MATERIALS["poster_c"] = ((0.9, 0.2, 0.5), 0.6, 0.0)
MATERIALS["poster_d"] = ((0.95, 0.95, 0.9), 0.6, 0.0)
MATERIALS["window_lit"] = ((1.0, 0.8, 0.45), 0.3, 0.0)
MATERIALS["brick_dark"] = ((0.22, 0.12, 0.1), 0.9, 0.0)
MATERIALS["concrete"] = ((0.35, 0.35, 0.37), 0.9, 0.0)

clean_scene()
parts = []
W, H, D = 12.0, 8.5, 9.0


def B(name, size, role, c, bevel=0.01):
    # c = centre (x, y_front_offset_into_building, z)
    return box(name, size, role, center=c, bevel=bevel)


# main mass (front face at y = 0, building extends to +Y)
parts.append(B("mass", (W, D, H), "brick_dark", (0, D / 2, H / 2), 0.02))
# plinth + black lower shopfront band
parts.append(B("plinth", (W + 0.1, 0.12, 1.1), "concrete", (0, -0.06, 0.55)))
parts.append(B("band", (W, 0.1, 3.4), "metal_dark", (0, -0.05, 1.7), 0.01))
# heavy door with steel frame and a lit transom
parts.append(B("doorframe", (2.3, 0.18, 2.7), "metal_steel", (-3.2, -0.09, 1.35)))
parts.append(B("door", (1.9, 0.12, 2.5), "plastic_black", (-3.2, -0.14, 1.25)))
parts.append(B("handle_L", (0.05, 0.08, 1.0), "metal_steel", (-3.65, -0.24, 1.2)))
parts.append(B("handle_R", (0.05, 0.08, 1.0), "metal_steel", (-2.75, -0.24, 1.2)))
parts.append(B("transom", (1.9, 0.08, 0.28), "window_lit", (-3.2, -0.13, 2.72)))
# roller shutter on the right
parts.append(B("shutter", (3.6, 0.12, 2.8), "metal_dark", (2.6, -0.08, 1.4)))
for i in range(14):
    parts.append(B(f"slat{i}", (3.6, 0.03, 0.04), "metal_steel", (2.6, -0.16, 0.15 + i * 0.19), 0.005))
# canopy over the entrance with pink light strips
parts.append(B("canopy", (4.4, 1.3, 0.14), "plastic_black", (-3.2, -0.65, 3.35)))
parts.append(B("canopy_strip", (4.4, 0.06, 0.06), "neon_pink", (-3.2, -1.33, 3.28), 0.005))
for i in range(9):
    parts.append(B(f"bar{i}", (0.06, 0.06, 0.9), "neon_cyan", (-5.2 + i * 0.5, -1.28, 2.85), 0.005))
# queue barrier posts and rope
for i in range(4):
    parts.append(cylinder(f"post{i}", 0.04, 0.95, "metal_brass", center=(-5.4 + i * 1.45, -2.6, 0), segments=12, bevel=0.004))
    parts.append(cylinder(f"postbase{i}", 0.16, 0.03, "metal_dark", center=(-5.4 + i * 1.45, -2.6, 0), segments=16, bevel=0.003))
rope = tube("rope", [Vector(p) for p in [(-5.4, -2.6, 0.88), (-4.7, -2.6, 0.75), (-3.95, -2.6, 0.88), (-3.25, -2.6, 0.75), (-2.5, -2.6, 0.88), (-1.8, -2.6, 0.75), (-1.05, -2.6, 0.88)]], 0.015, "cotton_red")
parts.append(to_mesh(rope))

# giant neon wordmark "VOID" on the upper facade (stroke geometry)
def bar(name, p0, p1, w=0.22, d=0.14, role="neon_pink"):
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    o = box(name, (L, d, w), role, center=(p0 + p1) / 2, bevel=0.03)
    ang = math.atan2(p1.z - p0.z, p1.x - p0.x)
    o.rotation_euler = (0, -ang, 0)
    return o

SZ = 2.2; Z0 = 4.3; X0 = -3.9; GAP = 2.2
# V
parts += [bar("V1", (X0, -0.12, Z0 + SZ), (X0 + 0.7, -0.12, Z0)), bar("V2", (X0 + 0.7, -0.12, Z0), (X0 + 1.4, -0.12, Z0 + SZ))]
# O (torus)
bpy.ops.mesh.primitive_torus_add(major_radius=0.85, minor_radius=0.11, major_segments=32, minor_segments=12, location=(X0 + GAP * 1 + 1.0, -0.12, Z0 + SZ / 2), rotation=(math.pi / 2, 0, 0))
o = bpy.context.active_object; o.scale = (0.8, 1, 1.25); o.name = "O"; o.data.materials.append(mat("neon_cyan")); parts.append(o)
# I
parts.append(bar("I", (X0 + GAP * 2 + 1.1, -0.12, Z0), (X0 + GAP * 2 + 1.1, -0.12, Z0 + SZ), role="neon_pink"))
# D
dx = X0 + GAP * 3 + 0.6
parts.append(bar("D1", (dx - 0.38, -0.12, Z0), (dx - 0.38, -0.12, Z0 + SZ), role="neon_cyan"))
bpy.ops.mesh.primitive_torus_add(major_radius=0.85, minor_radius=0.11, major_segments=32, minor_segments=12, location=(dx + 0.22, -0.12, Z0 + SZ / 2), rotation=(math.pi / 2, 0, 0))
o = bpy.context.active_object; o.scale = (0.72, 1, 1.25); o.name = "D2"; o.data.materials.append(mat("neon_cyan")); parts.append(o)

# posters pasted on the hoarding strip beside the shutter
for i, (r, h) in enumerate([("poster_a", 1.3), ("poster_b", 1.5), ("poster_c", 1.2), ("poster_d", 1.4)]):
    parts.append(B(f"poster{i}", (0.9, 0.03, h), r, (1.4 + i * 1.05, -0.17, 1.3 + h / 2 + (0.5 if i % 2 else 0)), 0.003))
# hung loudspeakers
for sx in (-5.4, 5.4):
    parts.append(B(f"spk{sx}", (0.55, 0.45, 0.8), "plastic_black", (sx, -0.25, 4.0), 0.02))
    parts.append(cylinder(f"cone{sx}", 0.19, 0.06, "rubber_black", center=(sx, -0.5, 4.2), segments=24, bevel=0.003, origin="center"))
    parts[-1].rotation_euler = (math.pi / 2, 0, 0)
# upper windows, lit
for i in range(5):
    parts.append(B(f"win{i}", (1.1, 0.08, 1.2), "window_lit", (-4.6 + i * 2.3, -0.03, 7.3), 0.01))
    parts.append(B(f"winframe{i}", (1.3, 0.05, 1.4), "concrete", (-4.6 + i * 2.3, -0.02, 7.3), 0.01))
# roofline: spotlights, parapet
parts.append(B("parapet", (W + 0.2, 0.4, 0.4), "concrete", (0, 0.1, H + 0.2), 0.01))
for i in range(5):
    parts.append(cylinder(f"spot{i}", 0.14, 0.4, "light_beam_emitter", center=(-4.4 + i * 2.2, -0.1, H + 0.4), segments=16, bevel=0.003))
# kegs + bin by the door
for i in range(3):
    parts.append(cylinder(f"keg{i}", 0.2, 0.5, "metal_steel", center=(0.1 + i * 0.5, -0.5, 0), segments=20, bevel=0.01))
parts.append(cylinder("ashbin", 0.15, 0.9, "metal_dark", center=(-1.6, -0.5, 0), segments=16, bevel=0.006))

# make sure every mesh has UVs (box helper adds them) and join to one root
meshes = [p for p in parts if p.type == "MESH"]
club = join(meshes, "exterior_club_building")
export_fbx(club, "exterior", "exterior_club_building")
print("tris", sum(len(p.vertices) for p in [club.data]))
preview(club, "exterior_club_building", views=("front", "front34"), size=(900, 600), fit=0.9)
