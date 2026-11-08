"""The Mothership's three guides (docs/doom/scenes/mothership.md), 160 x 256 billboard sprites, idle 1, available 5, selected 2, committed 2 (the Warehouse guides' sheet layout):
`booth` (left, the DJ in the painting: teal hair, headphones, an orange jacket over black), `underworld` (ahead, the red horned figure with a brass drum on a strap, a red robe) and `dock`
(right, the broad bald man in the long green coat with the yellow armband: CROPPED from this painting, about 335 px tall in it, by tools/doom/art/make_underworld_guides.py's crop helper).
`booth` and `underworld` are PROCEDURAL (about 110 px in the painting, under ruling 36's 180 px): placeholders toward the sprite standard.

    python -I tools/doom/art/make_mothership_guides.py     writes assets/story/doom_mothership/textures/guide_<who>_<state>_<n>.png and docs/shots/doom/mothership/guides_sheet.png

The procedural two are PLACEHOLDER art, below art/reference/standard/guide_floor_sprite_standard.png. An art pass replaces the PNGs; names and frame counts are the contract.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402
import make_underworld_guides as uwg  # noqa: E402  (crop_figure / crop_frames, finish, write_sheet)
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
    """Ruling 36: a guide is CROPPED from the painting where the painting shows it at 180 px or more, else PROCEDURAL toward the sprite standard. In the Mothership painting the Dock guide
    stands about 335 px tall (cropped: make_underworld_guides.crop_frames on its DOCK_FIG outline, the same crop the Underworld uses); the Booth DJ shows about 110 px above her desk (the desk
    hides the rest) and the Underworld drummer about 110 px (both procedural: make_guides' figure with the painting's costume colours, then make_underworld_guides.finish: a warm lamp rim,
    a cool rim, sequins dithered over the jacket / robe)."""
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    base = {k: dict(v) for k, v in mg.GUIDES.items()}
    variants = {
        "booth": ("stage", dict(skin="#e8c0a0", hair="#2aa898", top="#e8782c", vest="#2a2a34", trousers="#1c1c26", shoes="#15121c", accent="#1c1c24"), decorate_booth, "#e8782c"),
        "underworld": ("bar", dict(skin="#b4302a", hair="#1c0808", top="#a82424", vest="#6a1414", trousers="#2c1214", shoes="#1a0e0e", curly=False, moustache=False, accent="#d0a030"), decorate_uw,
                       "#a82424"),
    }
    rows, n = [], 0
    for who in ["booth", "underworld", "dock"]:
        if who == "dock":
            fr = uwg.crop_frames(uwg.DOCK_FIG)
        else:
            arch, patch, deco, cloth = variants[who]
            fr = {}
            for state, frames in mg.FRAMES.items():
                fr[state] = []
                for i in range(frames):
                    mg.GUIDES[arch] = {**base[arch], **patch}
                    im = deco(mg.draw_guide(arch, state, i), state, i)
                    mg.GUIDES[arch] = dict(base[arch])
                    fr[state].append(uwg.finish(uwg._outline(im), robe=cloth, sequins=("#ffe0b0", "#f0b070")))
        for state, fs in fr.items():
            for i, im in enumerate(fs):
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                n += 1
        rows.append(fr)
    uwg.write_sheet(rows, SHEET, (14, 12, 34, 255))
    print("wrote %d guide frames to %s and the sheet %s" % (n, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
