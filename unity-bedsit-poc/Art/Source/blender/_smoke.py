import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib, bsk
importlib.reload(bsk)
from bsk import *

clean_scene()
# mug: lathe body + tube handle
body = lathe("mug_body", [(0.0, 0.0), (0.036, 0.0), (0.040, 0.004), (0.041, 0.09), (0.039, 0.095), (0.034, 0.093), (0.034, 0.012), (0.0, 0.012)], "ceramic_white", segments=40)
h = tube("mug_handle", [Vector(p) for p in [(0.04, 0, 0.075), (0.065, 0, 0.07), (0.072, 0, 0.05), (0.06, 0, 0.025), (0.04, 0, 0.02)]], 0.006, "ceramic_white")
h = to_mesh(h)
m = join([body, h], "smoke_mug")
export_fbx(m, "_smoke", "smoke_mug")
print(preview(m, "smoke_mug", views=("front34",)))
