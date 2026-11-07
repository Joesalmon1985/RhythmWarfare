"""PLACEHOLDER sprite sheets for the engine's dynamic-things tests and shots (CONTRACTS.md 10, package A8), written into assets/story/night_one/sprites/:
  engine_test_crate.png   2 x 2 cells of 64 x 64: a crate in four states (rows: closed, open; columns: plain, lit), sidecar engine_test_crate.json {"grid": [2, 2]}
  engine_test_glass.png   3 cells of 48 x 72 in one row: empty, half, full (no sidecar: the grid is inferred from the thing's size, 2:3)
They are test art (flat shading with a dithered highlight), not the art standard; real sheets come from the activity packages.
    python tools/engine/make_thing_sheets.py
"""
import json
import os
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "story", "night_one", "sprites")
INK = (19, 17, 31, 255)


def dither(x, y):
    return ((x + y * 3) % 4) / 4.0


def crate(img, ox, oy, open_lid, lit):
    wood = (150, 96, 52) if not lit else (214, 150, 74)
    dark = (92, 56, 30)
    for y in range(64):
        for x in range(64):
            inside = 6 <= x < 58 and (14 if open_lid else 8) <= y < 60
            if not inside:
                continue
            edge = x in (6, 57) or y in ((14 if open_lid else 8), 59)
            plank = (y - 8) % 13 == 0
            c = INK if edge else (dark if plank else wood)
            if not edge and not plank and x > 40 and dither(x, y) < 0.5:
                c = tuple(min(255, v + 24) for v in c[:3]) + (255,)
            img.putpixel((ox + x, oy + y), c if len(c) == 4 else c + (255,))
    if open_lid:  # the lid tipped back
        for y in range(2, 10):
            for x in range(10, 54):
                img.putpixel((ox + x, oy + y), INK if y in (2, 9) else wood + (255,))
    if lit:  # a warm glow from inside
        for y in range(16, 24):
            for x in range(12, 52):
                if dither(x, y) < 0.75:
                    img.putpixel((ox + x, oy + y), (255, 214, 120, 255))


def glass(img, ox, level):
    for y in range(72):
        for x in range(48):
            w = 14 + (y * 4) // 72
            if abs(x - 24) > w or y < 6 or y > 68:
                continue
            edge = abs(x - 24) == w or y in (6, 68)
            c = INK if edge else (200, 228, 255, 255)
            fill_top = 68 - int(62 * level)
            if not edge and y > fill_top:
                c = (255, 120, 190, 255) if dither(x, y) > 0.25 else (255, 170, 214, 255)
            img.putpixel((ox + x, y), c)


def main():
    os.makedirs(OUT, exist_ok=True)
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for row in range(2):
        for col in range(2):
            crate(img, col * 64, row * 64, row == 1, col == 1)
    img.save(os.path.join(OUT, "engine_test_crate.png"))
    with open(os.path.join(OUT, "engine_test_crate.json"), "w") as f:
        json.dump({"grid": [2, 2], "placeholder": True}, f)
    g = Image.new("RGBA", (144, 72), (0, 0, 0, 0))
    for i, lv in enumerate([0.0, 0.5, 1.0]):
        glass(g, i * 48, lv)
    g.save(os.path.join(OUT, "engine_test_glass.png"))
    print("written", OUT)


if __name__ == "__main__":
    main()
