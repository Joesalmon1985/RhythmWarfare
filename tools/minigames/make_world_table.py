#!/usr/bin/env python3
"""Draws the day room's card table (docs/BLACKJACK_INTEGRATION.md, the world side): one 320 x 208 billboard of a table with three people playing cards behind it and one empty chair
pulled out on the camera's side. Pixel art in the palette family of the Ward's things (dark teal-greys, rust, a dithered shade), written to assets/minigames/blackjack/world_table.png.
It reads nothing from the chapter's art and writes nothing into it. The map uses it as an occluder through a `res://` texture path (so the crowd's dancers stand behind it).

    python3 tools/minigames/make_world_table.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/minigames/blackjack/world_table.png"
W, H = 320, 208

INK = (22, 30, 34, 255)
TOP = (150, 160, 150, 255)
TOP_HI = (176, 186, 172, 255)
FELT = (52, 92, 78, 255)
FELT_D = (40, 74, 64, 255)
EDGE = (96, 108, 104, 255)
LEG = (70, 82, 84, 255)
RUST = (150, 82, 48, 255)
CHAIR = (60, 128, 120, 255)
CHAIR_D = (42, 96, 92, 255)
CHAIR_HI = (84, 154, 142, 255)
SKIN = [(214, 170, 136, 255), (176, 124, 92, 255), (232, 192, 160, 255)]
HAIR = [(60, 44, 36, 255), (120, 118, 112, 255), (150, 96, 52, 255)]
CLOTH = [((110, 70, 84, 255), (80, 50, 62, 255)), ((196, 190, 170, 255), (150, 146, 130, 255)), ((86, 100, 140, 255), (62, 74, 108, 255))]
CARD = (232, 228, 214, 255)
CARD_BACK = (150, 52, 60, 255)
CHIP = [(210, 170, 70, 255), (190, 70, 60, 255), (90, 140, 190, 255)]


def dither(d: ImageDraw.ImageDraw, box, a, b, phase=0):
    """Fills `box` with a two-colour checker (the Ward's shade): a on one parity, b on the other."""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d.point((x, y), a if (x + y + phase) % 2 == 0 else b)


def person(d: ImageDraw.ImageDraw, cx: int, k: int, face_dx: int):
    """A seated person seen from the front, shoulders at y 76, hands down at the table top (y 110); k picks skin, hair and clothes; face_dx turns the gaze (-1 left, 0 centre, 1 right)."""
    skin, hair, (cl, cld) = SKIN[k % 3], HAIR[k % 3], CLOTH[k % 3]
    d.rectangle((cx - 22, 76, cx + 22, 112), fill=INK)  # torso outline
    dither(d, (cx - 21, 77, cx + 21, 112), cl, cld)
    d.rectangle((cx - 19, 78, cx - 17, 112), fill=cl)  # arms
    d.rectangle((cx + 17, 78, cx + 19, 112), fill=cl)
    if k % 3 == 2:  # a striped jumper
        for y in range(80, 112, 6):
            d.line((cx - 21, y, cx + 21, y), fill=(200, 200, 190, 255))
    d.rectangle((cx - 5, 66, cx + 5, 77), fill=skin)  # neck
    d.ellipse((cx - 15, 36, cx + 15, 72), fill=INK)
    d.ellipse((cx - 14, 37, cx + 14, 71), fill=skin)
    d.pieslice((cx - 15, 33, cx + 15, 66), 180, 360, fill=hair)  # hair
    if k % 3 == 1:
        d.rectangle((cx - 15, 46, cx - 12, 62), fill=hair)
        d.rectangle((cx + 12, 46, cx + 15, 62), fill=hair)
    for ex in (-6, 6):  # eyes
        d.rectangle((cx + ex - 2 + face_dx, 51, cx + ex + 1 + face_dx, 54), fill=(240, 236, 224, 255))
        d.rectangle((cx + ex - 1 + face_dx * 2, 52, cx + ex + face_dx * 2, 53), fill=INK)
    d.line((cx - 4 + face_dx, 64, cx + 4 + face_dx, 64), fill=(120, 60, 56, 255))  # mouth


def hand_of_cards(d: ImageDraw.ImageDraw, cx: int, n: int):
    for i in range(n):
        x = cx - n * 4 + i * 8
        d.rectangle((x, 92, x + 9, 108), fill=INK)
        d.rectangle((x + 1, 93, x + 8, 107), fill=CARD_BACK)
        d.rectangle((x + 3, 97, x + 6, 103), fill=(190, 96, 100, 255))


def table(d: ImageDraw.ImageDraw):
    for lx in (88, 218):  # legs
        d.rectangle((lx - 1, 134, lx + 11, 192), fill=INK)
        d.rectangle((lx, 134, lx + 9, 191), fill=LEG)
        d.rectangle((lx + 2, 150, lx + 5, 156), fill=RUST)
    d.rectangle((44, 104, 276, 136), fill=INK)  # slab front
    dither(d, (45, 124, 275, 135), EDGE, LEG)
    d.polygon([(52, 106), (268, 106), (276, 124), (44, 124)], fill=INK)  # top face
    d.polygon([(54, 108), (266, 108), (273, 123), (47, 123)], fill=FELT)
    dither(d, (60, 116, 262, 122), FELT, FELT_D, 1)
    d.line((54, 108, 266, 108), fill=TOP_HI)
    d.rectangle((60, 124, 70, 125), fill=RUST)
    d.rectangle((250, 126, 258, 127), fill=RUST)
    # the dealer's deck, the players' cards, a few chips
    d.rectangle((150, 109, 162, 117), fill=INK)
    d.rectangle((151, 110, 161, 116), fill=CARD_BACK)
    for x, c in ((98, CARD), (106, CARD), (206, CARD), (214, CARD)):
        d.rectangle((x, 111, x + 6, 118), fill=INK)
        d.rectangle((x + 1, 112, x + 5, 117), fill=c)
    for i, x in enumerate((126, 134, 186)):
        d.ellipse((x, 114, x + 7, 119), fill=INK)
        d.ellipse((x + 1, 115, x + 6, 118), fill=CHIP[i % 3])


def empty_chair(d: ImageDraw.ImageDraw):
    """The empty chair on the camera's side, back towards us, pulled out a little and turned a shade (the Ward's thing_chair family, drawn here)."""
    cx = 160
    for lx in (cx - 24, cx - 14, cx + 12, cx + 22):  # legs
        d.line((lx, 176, lx + (-3 if lx < cx else 3), 206), fill=INK, width=3)
        d.line((lx, 176, lx + (-3 if lx < cx else 3), 206), fill=LEG, width=1)
    d.polygon([(cx - 36, 160), (cx + 36, 160), (cx + 42, 180), (cx - 42, 180)], fill=INK)  # seat edge
    d.polygon([(cx - 34, 162), (cx + 34, 162), (cx + 39, 178), (cx - 39, 178)], fill=CHAIR_D)
    d.rectangle((cx - 38, 178, cx + 38, 181), fill=CHAIR_HI)
    d.polygon([(cx - 31, 118), (cx + 31, 118), (cx + 35, 162), (cx - 35, 162)], fill=INK)  # the back
    d.polygon([(cx - 29, 120), (cx + 29, 120), (cx + 33, 160), (cx - 33, 160)], fill=CHAIR)
    dither(d, (cx - 28, 140, cx + 28, 160), CHAIR, CHAIR_D)
    d.line((cx - 29, 121, cx + 29, 121), fill=CHAIR_HI)
    d.rectangle((cx - 12, 134, cx - 8, 137), fill=RUST)  # a worn patch


def main() -> None:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    person(d, 62, 0, 1)
    person(d, 160, 1, 0)
    person(d, 258, 2, -1)
    table(d)
    hand_of_cards(d, 70, 2)
    hand_of_cards(d, 250, 2)
    empty_chair(d)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT)
    print("wrote", OUT.relative_to(ROOT), im.size)


if __name__ == "__main__":
    main()
