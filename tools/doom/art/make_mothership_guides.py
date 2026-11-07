"""The Mothership's three guides (docs/doom/scenes/mothership.md), 160 x 256 billboard sprites, idle 1, available 5, selected 2, committed 2 (the Warehouse guides' sheet layout):
`booth` (left, the DJ in the painting: teal hair, headphones, an orange jacket over black), `underworld` (ahead, the red horned figure with a brass drum on a strap, a red robe) and `dock`
(right, the broad bald man in the long green coat with the yellow armband: the Lounge's `dock` guide, the same character, redrawn here by tools/doom/art/make_lounge_guides.py's drawing code).

    python -I tools/doom/art/make_mothership_guides.py     writes assets/story/doom_mothership/textures/guide_<who>_<state>_<n>.png and docs/shots/doom/mothership/guides_sheet.png

PLACEHOLDER art, procedural like the Warehouse's: below art/reference/standard/guide_floor_sprite_standard.png. An art pass replaces the PNGs; names and frame counts are the contract.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402
import make_lounge_guides as lg  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT = os.path.join(mg.ROOT, "assets", "story", "doom_mothership", "textures")
SHEET = os.path.join(mg.ROOT, "docs", "shots", "doom", "mothership", "guides_sheet.png")
hexc = mg.hexc


def decorate_booth(im, state, i):
    """Headphones over the teal hair: a band and two ear cups (head centre about x 80, y 47)."""
    d = ImageDraw.Draw(im)
    p = mg.poses(state, i)
    cx = int(mg.CX + p["lean"] * 0.4 + p["tilt"])
    band, cup, glow = hexc("#d8dce6"), hexc("#3a3e4a"), hexc("#60e0d0")
    d.arc([cx - 21, 18, cx + 21, 64], 180, 360, fill=band, width=3)
    for sx in (-1, 1):
        x = cx + sx * 19
        d.rounded_rectangle([x - 5, 42, x + 5, 60], radius=3, fill=cup, outline=hexc("#0e0e16"))
        d.rectangle([x - 2, 48, x + 2, 52], fill=glow)
    return im


def decorate_uw(im, state, i):
    """Cream horns over the head and the brass drum on a strap across the belly."""
    d = ImageDraw.Draw(im)
    p = mg.poses(state, i)
    cx = int(mg.CX + p["lean"] * 0.4 + p["tilt"])
    horn, edge = hexc("#e8dcc0"), hexc("#2a1a14")
    for sx in (-1, 1):
        d.polygon([(cx + sx * 12, 32), (cx + sx * 20, 22), (cx + sx * 26, 8), (cx + sx * 31, 12), (cx + sx * 25, 28), (cx + sx * 17, 38)], fill=horn, outline=edge)
    brass, dark = hexc("#c89a30"), hexc("#5a3a14")
    d.ellipse([cx - 30, 108, cx + 30, 140], fill=dark)
    d.ellipse([cx - 28, 106, cx + 28, 134], fill=brass, outline=edge)
    d.ellipse([cx - 22, 110, cx + 22, 128], outline=hexc("#f0d880"), width=2)
    for k in range(-24, 25, 12):
        d.line([(cx + k, 108), (cx + k // 2, 138)], fill=dark)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    base = {k: dict(v) for k, v in mg.GUIDES.items()}
    variants = {
        "booth": ("stage", dict(skin="#e8c0a0", hair="#2aa898", top="#e8782c", vest="#2a2a34", trousers="#1c1c26", shoes="#15121c", accent="#1c1c24"), decorate_booth),
        "underworld": ("bar", dict(skin="#b4302a", hair="#1c0808", top="#a82424", vest="#6a1414", trousers="#2c1214", shoes="#1a0e0e", curly=False, moustache=False, accent="#d0a030"), decorate_uw),
    }
    cols = sum(mg.FRAMES.values())
    sheet = Image.new("RGBA", (cols * mg.W, 3 * mg.H), (14, 12, 34, 255))
    n = 0
    for row, who in enumerate(["booth", "underworld", "dock"]):
        x = 0
        for state, frames in mg.FRAMES.items():
            for i in range(frames):
                if who == "dock":
                    im = lg.draw("dock", state, i)
                else:
                    arch, patch, deco = variants[who]
                    mg.GUIDES[arch] = {**base[arch], **patch}
                    im = deco(mg.draw_guide(arch, state, i), state, i)
                    mg.GUIDES[arch] = dict(base[arch])
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                sheet.alpha_composite(im, (x * mg.W, row * mg.H))
                x += 1
                n += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(SHEET)
    print("wrote %d guide frames to %s and the sheet %s" % (n, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
