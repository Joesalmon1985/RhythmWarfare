"""Copy the chosen Poly Haven (CC0) 1k texture sets into the Unity project under short role names.
Run:  python -I Tools/art/stage_textures.py
Source: Art/ThirdParty/polyhaven/<id>/   ->  Assets/Bedsit/Art/Textures/<name>_albedo.jpg / <name>_normal.jpg
Licence: CC0 (https://polyhaven.com/license) - see Art/inventory/third_party.csv.
"""
import os, shutil, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "Art", "ThirdParty", "polyhaven")
DST = os.path.join(ROOT, "Assets", "Bedsit", "Art", "Textures")

# short name -> poly haven id
SETS = {
    "wall_plaster": "beige_wall_001",
    "wall_plaster_b": "beige_wall_002",
    "floor_boards": "old_wooden_floor_02",
    "floor_parquet": "herringbone_parquet",
    "floor_laminate": "laminate_floor_02",
    "wood_dark": "dark_wood",
    "carpet_dirty": "dirty_carpet",
    "brick_red": "red_brick_03",
    "brick_orange": "brick_wall_006",
    "brick_brown": "brown_brick_02",
    "concrete": "concrete_wall_003",
    "asphalt": "asphalt_03",
    "paving": "pavement_02",
    "metal_worn": "metal_plate_02",
    "metal_rust": "rusty_metal_02",
    "denim": "denim_fabric_05",
    "cotton": "cotton_jersey",
    "fabric_pattern": "fabric_pattern_07",
}

os.makedirs(DST, exist_ok=True)
for name, pid in SETS.items():
    d = os.path.join(SRC, pid)
    diff = glob.glob(os.path.join(d, pid + "_diff_1k.jpg")) or glob.glob(os.path.join(d, "*col_1_1k.jpg"))
    nor = glob.glob(os.path.join(d, pid + "_nor_gl_1k.jpg"))
    if not diff:
        print("missing diffuse", pid); continue
    shutil.copy(diff[0], os.path.join(DST, name + "_albedo.jpg"))
    if nor:
        shutil.copy(nor[0], os.path.join(DST, name + "_normal.jpg"))
    print("ok", name, "<-", pid)
