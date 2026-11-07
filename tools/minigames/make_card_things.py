#!/usr/bin/env python3
"""The card table's things in the room (CONTRACTS.md 10, ruling 38, package A8b): the playing cards and the chip stacks the blackjack activity places on the felt as dynamic things.
PLACEHOLDER art, drawn procedurally (flat pixel shapes, no dithered painting): it is below the art standard of ruling 36 and stands in until the art stream paints the sheets.

Outputs (assets/minigames/blackjack/), each with a grid sidecar read by StoryDynamicThings:
* `bj_cards.png` + `bj_cards.json` {"grid": [13, 5]}: a card is a cell of CARD_W x CARD_H. Rows 0..3 are the suits (0 spades, 1 hearts, 2 diamonds, 3 clubs: the order
  the close-up drew them in, blackjack_draw.gd), columns the ranks 1 (ace) .. 13 (king): frame = suit * 13 + rank - 1. Row 4: column 0 the back (frame 52), column 1 a blank face (frame 53), the rest empty.
  Big corner rank and a big pip so a card reads from the chair (at least 48 px tall on a 1280 x 720 screen).
* `bj_chips.png` + `bj_chips.json` {"grid": [16, 8]}: a stack of 0..15 chips standing on the felt, the chips at the bottom of the cell. Rows: 2 * colour + change, colour
  0 the player's (gold), 1 the left player's (blue), 2 the right player's (green), 3 the bet pile (red); change 1 adds a small coin beside the stack (the pence under 5 pounds).
  frame = row * 16 + chips (BlackjackActivity.chip_frame).

    python tools/minigames/make_card_things.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/minigames/blackjack"

CARD_W, CARD_H = 24, 34
CHIP_W, CHIP_H = 24, 68
MAX_CHIPS = 15

# the 3 x 5 font of src/minigames/draw/pixel_glyphs.gd (bit 2 = left column)
GLYPHS = {"0": [7, 5, 5, 5, 7], "1": [2, 6, 2, 2, 7], "2": [7, 1, 7, 4, 7], "3": [7, 1, 7, 1, 7], "4": [5, 5, 7, 1, 1], "5": [7, 4, 7, 1, 7],
          "6": [7, 4, 7, 5, 7], "7": [7, 1, 1, 2, 2], "8": [7, 5, 7, 5, 7], "9": [7, 5, 7, 1, 7], "A": [2, 5, 7, 5, 5], "J": [1, 1, 1, 5, 2],
          "Q": [7, 5, 5, 7, 1], "K": [5, 5, 6, 5, 5]}
RANKS = {1: "A", 11: "J", 12: "Q", 13: "K"}

# suit pips, 7 x 7, drawn at 1 or 2 px per cell
PIPS = {
    0: ["0001000", "0011100", "0111110", "1111111", "1111111", "0001000", "0011100"],  # spades
    1: ["0110110", "1111111", "1111111", "1111111", "0111110", "0011100", "0001000"],  # hearts
    2: ["0001000", "0011100", "0111110", "1111111", "0111110", "0011100", "0001000"],  # diamonds
    3: ["0011100", "0011100", "1101011", "1111111", "1101011", "0001000", "0011100"],  # clubs
}
RED, BLACK = (196, 30, 44, 255), (24, 22, 34, 255)
PAPER, PAPER_EDGE, PAPER_SHADE = (246, 240, 226, 255), (120, 104, 92, 255), (222, 212, 192, 255)


def glyph(d: ImageDraw.ImageDraw, ch: str, x: int, y: int, cell: int, col) -> None:
    for r, bits in enumerate(GLYPHS[ch]):
        for c in range(3):
            if bits & (4 >> c):
                d.rectangle([x + c * cell, y + r * cell, x + (c + 1) * cell - 1, y + (r + 1) * cell - 1], fill=col)


def pip(d: ImageDraw.ImageDraw, suit: int, x: int, y: int, cell: int, col) -> None:
    for r, row in enumerate(PIPS[suit]):
        for c, b in enumerate(row):
            if b == "1":
                d.rectangle([x + c * cell, y + r * cell, x + (c + 1) * cell - 1, y + (r + 1) * cell - 1], fill=col)


def blank(d: ImageDraw.ImageDraw, x0: int, y0: int) -> None:
    d.rectangle([x0 + 1, y0, x0 + CARD_W - 2, y0 + CARD_H - 1], fill=PAPER_EDGE)
    d.rectangle([x0, y0 + 1, x0 + CARD_W - 1, y0 + CARD_H - 2], fill=PAPER_EDGE)
    d.rectangle([x0 + 1, y0 + 1, x0 + CARD_W - 2, y0 + CARD_H - 2], fill=PAPER)
    d.rectangle([x0 + 1, y0 + CARD_H - 4, x0 + CARD_W - 2, y0 + CARD_H - 2], fill=PAPER_SHADE)


def face(d: ImageDraw.ImageDraw, x0: int, y0: int, suit: int, rank: int) -> None:
    blank(d, x0, y0)
    col = RED if suit in (1, 2) else BLACK
    text = RANKS.get(rank, str(rank))
    x = x0 + 3
    for ch in text:  # the rank, big, top left (2 px a cell: 6 x 10 a glyph)
        glyph(d, ch, x, y0 + 3, 2, col)
        x += 7
    if len(text) == 1:  # a small pip top right ("10" fills that corner)
        pip(d, suit, x0 + CARD_W - 10, y0 + 3, 1, col)
    pip(d, suit, x0 + 5, y0 + 15, 2, col)  # the big pip, low centre (14 x 14)


def back(d: ImageDraw.ImageDraw, x0: int, y0: int) -> None:
    blank(d, x0, y0)
    d.rectangle([x0 + 2, y0 + 2, x0 + CARD_W - 3, y0 + CARD_H - 3], fill=(150, 28, 44, 255))
    for yy in range(y0 + 3, y0 + CARD_H - 3):
        for xx in range(x0 + 3, x0 + CARD_W - 3):
            if (xx + yy) % 4 == 0 or (xx - yy) % 4 == 0:
                d.point((xx, yy), fill=(214, 84, 92, 255))
    d.rectangle([x0 + 9, y0 + 13, x0 + 14, y0 + 20], fill=(246, 214, 120, 255))


CHIP_COLS = [((232, 186, 54), (150, 104, 20), (255, 236, 150)),  # the player's: gold
             ((60, 108, 214), (28, 52, 120), (160, 196, 255)),  # the left player's: blue
             ((52, 162, 92), (22, 86, 48), (150, 232, 170)),  # the right player's: green
             ((206, 44, 56), (112, 18, 30), (255, 150, 150))]  # the bet pile: red


def stack(d: ImageDraw.ImageDraw, x0: int, y0: int, n: int, colour: int, change: bool) -> None:
    """n chips, 3 px apart: each a rounded disc seen from a little above (a lit rim line, the body with its edge stripes, a dark underside)."""
    body, dark, light = CHIP_COLS[colour]
    bottom = y0 + CHIP_H - 1
    cx0, cx1 = x0 + 1, x0 + CHIP_W - 7  # a 16 px wide chip, room for the coin on the right
    for i in range(n):  # 4 px a chip: a dark underside, the body with its edge stripes (two rows), a lit rim
        yb = bottom - i * 4
        d.line([cx0 + 1, yb, cx1 - 1, yb], fill=dark + (255,))
        d.rectangle([cx0, yb - 2, cx1, yb - 1], fill=body + (255,))
        for k in range(cx0 + 1, cx1, 3):  # the edge stripes
            d.point((k, yb - 1), fill=(250, 246, 236, 255))
            d.point((k, yb - 2), fill=(250, 246, 236, 255))
        d.line([cx0 + 1, yb - 3, cx1 - 1, yb - 3], fill=light + (255,))
    if change:
        d.ellipse([x0 + CHIP_W - 7, bottom - 4, x0 + CHIP_W - 2, bottom], fill=(204, 204, 214, 255), outline=(110, 110, 124, 255))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cards = Image.new("RGBA", (CARD_W * 13, CARD_H * 5), (0, 0, 0, 0))
    d = ImageDraw.Draw(cards)
    for suit in range(4):
        for rank in range(1, 14):
            face(d, (rank - 1) * CARD_W, suit * CARD_H, suit, rank)
    back(d, 0, 4 * CARD_H)
    blank(d, CARD_W, 4 * CARD_H)
    cards.save(OUT / "bj_cards.png", optimize=True)
    (OUT / "bj_cards.json").write_text(json.dumps({"grid": [13, 5], "placeholder": True}) + "\n", encoding="utf-8", newline="\n")
    chips = Image.new("RGBA", (CHIP_W * (MAX_CHIPS + 1), CHIP_H * 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(chips)
    for colour in range(4):
        for change in (0, 1):
            for n in range(MAX_CHIPS + 1):
                stack(d, n * CHIP_W, (colour * 2 + change) * CHIP_H, n, colour, bool(change))
    chips.save(OUT / "bj_chips.png", optimize=True)
    (OUT / "bj_chips.json").write_text(json.dumps({"grid": [MAX_CHIPS + 1, 8], "placeholder": True}) + "\n", encoding="utf-8", newline="\n")
    print("wrote", (OUT / "bj_cards.png").relative_to(ROOT), cards.size, (OUT / "bj_chips.png").relative_to(ROOT), chips.size)


if __name__ == "__main__":
    main()
