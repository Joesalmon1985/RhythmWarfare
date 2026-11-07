"""The Warehouse's railing tile: assets/story/doom_warehouse/textures/wh_railing.png, 128 x 128 RGBA (1 m x 1 m at the style guide's 128 texels per metre).

    python -I tools/doom/art/make_railing.py

A steel lattice fence for the renderer's `railing` wall kind (docs/story/HEIGHTS_AND_PATHS.md): a top rail and a foot rail, a post at the tile's left edge (so the posts fall every
metre where the tile repeats), and a diamond mesh between them. Everything else is alpha 0 (the renderer cuts at alpha 0.5, unshaded, nearest filtering), so the floor is seen
through it. Colours are brighter than a lit wall because a railing is not shaded.
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_warehouse", "textures", "wh_railing.png")
S = 128
STEEL = (150, 168, 214, 255)
LIGHT = (214, 228, 255, 255)
DARK = (74, 88, 140, 255)
AMBER = (255, 196, 110, 255)  # the lamp-lit top edge


def main():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(-S, S * 2, 32):  # the diamond mesh: two families of diagonals every 32 texels, 3 wide, with a light edge and a dark edge
        for dx in range(3):
            c = LIGHT if dx == 0 else (STEEL if dx == 1 else DARK)
            d.line([(k + dx, 10), (k + dx + S, 10 + S)], fill=c, width=1)
            d.line([(k + dx + S, 10), (k + dx, 10 + S)], fill=c, width=1)
    clear = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mesh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mesh.paste(im.crop((0, 10, S, S - 10)), (0, 10))  # the mesh only between the rails
    im = mesh
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, 9], fill=STEEL)  # the top rail, 10 texels: amber lamp light on its upper edge, a dark underside
    d.rectangle([0, 0, S - 1, 2], fill=AMBER)
    d.rectangle([0, 3, S - 1, 4], fill=LIGHT)
    d.rectangle([0, 8, S - 1, 9], fill=DARK)
    d.rectangle([0, S - 10, S - 1, S - 1], fill=STEEL)  # the foot rail
    d.rectangle([0, S - 10, S - 1, S - 9], fill=LIGHT)
    d.rectangle([0, S - 2, S - 1, S - 1], fill=DARK)
    d.rectangle([0, 0, 5, S - 1], fill=STEEL)  # the post, 6 texels, light on its left edge and dark on its right
    d.rectangle([0, 0, 1, S - 1], fill=LIGHT)
    d.rectangle([4, 0, 5, S - 1], fill=DARK)
    d.rectangle([0, 0, 5, 2], fill=AMBER)
    im.save(OUT)
    print("wrote", OUT)
    _ = clear


if __name__ == "__main__":
    main()
