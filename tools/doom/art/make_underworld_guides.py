"""The Underworld's three guides (docs/doom/scenes/underworld.md): `mothership` (ahead: the tall pale violet figure with a white crest, in the painting's purple robe), `floor` (left: the
braided woman with the magenta top and silver trousers, as the Lounge's) and `dock` (right: the broad bearded man in the green coat with the yellow armband, as the Lounge's), as 160 x 256
billboard sprites in the Warehouse guides' sheet layout (idle 1, available 5, selected 2, committed 2), written to assets/story/doom_underworld/textures/.

    python -I tools/doom/art/make_underworld_guides.py     also writes docs/shots/doom/underworld/guides_sheet.png

PLACEHOLDER art, like the other scenes': procedural capsule limbs and ordered dither; NOT the painterly finish of art/reference/standard/guide_floor_sprite_standard.png. The floor and dock
guides are drawn by tools/doom/art/make_lounge_guides.py (the same two people appear in the Lounge and the Underworld paintings); the mothership guide is the Booth's violet variant with a
white crest and a longer robe colour. An art pass replaces the PNGs; names and frame counts are the contract.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402
import make_lounge_guides as lg  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = mg.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_underworld", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "underworld", "guides_sheet.png")
W, H = mg.W, mg.H
MOTHERSHIP = dict(skin="#cbb8dc", hair="#f0ecff", top="#7a3a9e", vest="#3a1a52", trousers="#241432", shoes="#140c1e", accent="#e8c8ff")


def mothership(state, i):
    base = dict(mg.GUIDES["stage"])
    mg.GUIDES["stage"] = {**base, **MOTHERSHIP}
    try:
        return mg.draw_guide("stage", state, i)
    finally:
        mg.GUIDES["stage"] = base


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    cols = sum(mg.FRAMES.values())
    who_list = ["mothership", "floor", "dock"]
    sheet = Image.new("RGBA", (cols * W, len(who_list) * H), (40, 8, 8, 255))
    n = 0
    for r, who in enumerate(who_list):
        x = 0
        for state, k in mg.FRAMES.items():
            for i in range(k):
                im = mothership(state, i) if who == "mothership" else lg.draw(who, state, i)
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                sheet.alpha_composite(im, (x * W, r * H))
                x += 1
                n += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(SHEET)
    print("wrote %d sprites to %s and the sheet %s" % (n, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
