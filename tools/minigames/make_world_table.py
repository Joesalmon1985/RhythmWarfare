#!/usr/bin/env python3
"""Draws the day room's card table (docs/BLACKJACK_INTEGRATION.md, the world side): one 320 x 272 billboard of a card game under a hanging lamp, seen from across the room.
A warm lamp hangs over the table and throws a cone of light onto it; the three players of the close-up (the dealer in his green visor and braces, the grey-haired woman in mustard,
the woman with the wild purple hair in pink) sit behind it holding fans of cards, with cards, notes and coins on the lit baize; one chair on our side stands empty, pulled out and turned
toward the room. The pool of warm light and the white cards are what the eye finds in the dark day room. Palette: the Ward's dark teal-greys and rust, plus the lamp's warm yellow.
It reads nothing from the chapter's art and writes nothing into it. The map uses it as an occluder through a `res://` texture path (so the crowd's dancers stand behind it).

    python3 tools/minigames/make_world_table.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/minigames/blackjack/world_table.png"
W, H = 320, 272

INK = (20, 24, 30, 255)
FELT = (46, 118, 82, 255)
FELT_LIT = (78, 162, 104, 255)
FELT_D = (30, 80, 58, 255)
RIM = (122, 84, 50, 255)
RIM_LIT = (178, 128, 72, 255)
RIM_D = (78, 52, 32, 255)
LEG = (62, 70, 74, 255)
CHAIR = (60, 128, 120, 255)
CHAIR_D = (36, 86, 82, 255)
CHAIR_LIT = (120, 186, 160, 255)
LAMP = (60, 120, 90, 255)
LAMP_D = (34, 74, 56, 255)
BULB = (255, 244, 196, 255)
WARM = (255, 214, 120)
CARD = (246, 240, 222, 255)
CARD_S = (196, 188, 166, 255)
RED = (200, 40, 58, 255)
BLK = (34, 30, 48, 255)
BACK = (60, 64, 140, 255)
NOTE = (44, 158, 168, 255)
GOLD = (230, 190, 70, 255)

# the three players of the close-up: skin, skin shade, hair, cloth, cloth shade
DEALER = ((240, 189, 150, 255), (201, 138, 99, 255), (74, 48, 32, 255), (233, 237, 242, 255), (170, 182, 200, 255))
GRAN = ((246, 214, 192, 255), (217, 169, 142, 255), (230, 230, 238, 255), (212, 167, 62, 255), (160, 125, 39, 255))
WILD = ((150, 98, 63, 255), (111, 67, 41, 255), (52, 36, 86, 255), (204, 106, 130, 255), (156, 67, 93, 255))


def lit(c, k):
    """`c` pushed toward the lamp's warm light by k (0..1)."""
    return (min(255, int(c[0] + (WARM[0] - c[0]) * k + 20 * k)), min(255, int(c[1] + (WARM[1] - c[1]) * k + 8 * k)), int(c[2] + (WARM[2] - c[2]) * k), 255)


def dither(d: ImageDraw.ImageDraw, box, a, b, phase=0):
    """Fills `box` with a two-colour checker (the Ward's shade)."""
    x0, y0, x1, y1 = box
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d.point((x, y), a if (x + y + phase) % 2 == 0 else b)


def fan(d: ImageDraw.ImageDraw, cx: int, y: int, n: int, tilt: int):
    """A fan of n cards held up in front of a chest (we see the backs, the front one shows a red pip)."""
    for i in range(n):
        x = int(cx + (i - (n - 1) / 2) * 6 + tilt)
        dx = int((i - (n - 1) / 2) * 3)
        pts = [(x - 5 + dx, y), (x + 5 + dx, y), (x + 6, y + 15), (x - 4, y + 15)]
        d.polygon([(px - 1, py - 1) for px, py in pts], fill=INK)
        d.polygon(pts, fill=CARD)
        d.rectangle((x - 2 + dx // 2, y + 3, x + 2 + dx // 2, y + 9), fill=BACK if i < n - 1 else RED)


def person(d: ImageDraw.ImageDraw, cx: int, look, kind: str, face_dx: int, top: int):
    """A seated player from the front, head top at `top`, lit from the lamp above (the forehead and the shoulders catch the warm light)."""
    skin, sk, hair, cl, cld = look
    d.polygon([(cx - 26, top + 64), (cx + 26, top + 64), (cx + 30, top + 100), (cx - 30, top + 100)], fill=INK)
    d.polygon([(cx - 24, top + 66), (cx + 24, top + 66), (cx + 28, top + 100), (cx - 28, top + 100)], fill=cl)
    dither(d, (cx - 26, top + 88, cx + 26, top + 100), cl, cld)
    d.line((cx - 23, top + 66, cx + 23, top + 66), fill=lit(cl, 0.6))
    if kind == "dealer":  # braces and an open collar
        for sx in (-9, 9):
            d.rectangle((cx + sx - 1, top + 66, cx + sx + 1, top + 100), fill=RED)
        d.polygon([(cx - 5, top + 64), (cx + 5, top + 64), (cx, top + 74)], fill=skin)
    elif kind == "gran":
        d.polygon([(cx - 6, top + 64), (cx + 6, top + 64), (cx, top + 78)], fill=(240, 228, 196, 255))
        for yy in (top + 80, top + 86, top + 92):
            d.rectangle((cx + 2, yy, cx + 3, yy + 1), fill=cld)
    else:
        d.polygon([(cx - 7, top + 64), (cx + 7, top + 64), (cx, top + 80)], fill=(116, 44, 67, 255))
    d.rectangle((cx - 5, top + 54, cx + 5, top + 66), fill=sk)
    if kind == "wild":  # the wild hair behind the head
        spikes = [(-24, 30), (-28, 18), (-22, 12), (-26, 2), (-16, 0), (-14, -10), (-6, -4), (0, -12), (6, -4), (14, -10), (16, 0), (26, 2), (22, 12), (28, 18), (24, 30), (16, 36), (-16, 36)]
        d.polygon([(cx + x, top + 8 + y) for x, y in spikes], fill=INK)
        d.polygon([(cx + int(x * 0.9), top + 9 + int(y * 0.9)) for x, y in spikes], fill=hair)
        d.polygon([(cx - 3, top - 1), (cx + 1, top - 6), (cx + 4, top - 1)], fill=(224, 80, 138, 255))
    if kind == "gran":
        d.ellipse((cx - 18, top + 6, cx + 18, top + 40), fill=INK)
        d.ellipse((cx - 17, top + 7, cx + 17, top + 39), fill=hair)
    d.ellipse((cx - 15, top + 8, cx + 15, top + 58), fill=INK)
    d.ellipse((cx - 14, top + 9, cx + 14, top + 57), fill=skin)
    d.pieslice((cx - 14, top + 9, cx + 14, top + 57), 200, 340, fill=lit(skin, 0.35))
    d.chord((cx - 14, top + 9, cx + 14, top + 57), 30, 150, fill=sk)  # the chin in shade
    if kind == "dealer":  # the green visor, lit on top
        d.polygon([(cx - 19, top + 22), (cx - 16, top + 12), (cx + 16, top + 12), (cx + 19, top + 22)], fill=INK)
        d.polygon([(cx - 17, top + 21), (cx - 15, top + 13), (cx + 15, top + 13), (cx + 17, top + 21)], fill=(70, 168, 100, 255))
        d.line((cx - 15, top + 13, cx + 15, top + 13), fill=(150, 230, 160, 255))
        d.rectangle((cx - 14, top + 22, cx + 14, top + 23), fill=sk)
    elif kind == "gran":  # thin hair on top
        d.pieslice((cx - 15, top + 6, cx + 15, top + 30), 180, 360, fill=hair)
    else:
        fr = [(-15, 26), (-15, 14), (-8, 8), (0, 7), (8, 8), (15, 14), (15, 26), (10, 18), (4, 22), (-2, 16), (-8, 22)]
        d.polygon([(cx + x, top + 4 + y) for x, y in fr], fill=hair)
    # eyes: big whites with pupils turned toward the game (face_dx)
    for ex in (-6, 6):
        if kind == "gran":  # round glasses
            d.ellipse((cx + ex - 6, top + 26, cx + ex + 6, top + 38), fill=INK)
            d.ellipse((cx + ex - 5, top + 27, cx + ex + 5, top + 37), fill=(220, 240, 248, 255))
        d.ellipse((cx + ex - 4, top + 28, cx + ex + 4, top + 36), fill=INK)
        d.ellipse((cx + ex - 3, top + 29, cx + ex + 3, top + 35), fill=(248, 248, 244, 255))
        d.rectangle((cx + ex - 1 + face_dx, top + 31, cx + ex + 1 + face_dx, top + 34), fill=INK)
    d.rectangle((cx - 1, top + 39, cx + 1, top + 41), fill=sk)
    if kind == "wild":
        d.arc((cx - 7, top + 38, cx + 7, top + 49), 20, 160, fill=INK, width=2)
        d.ellipse((cx - 19, top + 36, cx - 15, top + 42), outline=GOLD)
    else:
        d.line((cx - 4, top + 46, cx + 4, top + 46), fill=(120, 60, 56, 255), width=2)


def arm(d: ImageDraw.ImageDraw, a, b, cl, skin):
    """An arm from the shoulder `a` out to an elbow and in to the hand `b` on the table."""
    e = (a[0] + (8 if a[0] > b[0] else -8) * (1 if abs(a[0] - b[0]) > 4 else 0), (a[1] + b[1]) // 2 + 4)
    d.line((a, e, b), fill=INK, width=11, joint="curve")
    d.line((a, e, b), fill=cl, width=7, joint="curve")
    d.ellipse((b[0] - 5, b[1] - 4, b[0] + 5, b[1] + 4), fill=INK)
    d.ellipse((b[0] - 4, b[1] - 3, b[0] + 4, b[1] + 3), fill=skin)


def lamp(d: ImageDraw.ImageDraw, im: Image.Image):
    """The hanging lamp (a cord from the top edge, a green enamel shade, a hot bulb) and the cone of warm light under it, a translucent layer over the players and the table."""
    cx = 160
    cone = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cone)
    for k, a in ((0, 34), (12, 34), (24, 38)):
        cd.polygon([(cx - 26 + k * 0.2, 46), (cx + 26 - k * 0.2, 46), (cx + 128 - k * 2, 192), (cx - 128 + k * 2, 192)], fill=WARM + (a,))
    im.alpha_composite(cone)
    d.line((cx, 0, cx, 30), fill=INK, width=3)
    d.line((cx, 0, cx, 30), fill=(90, 96, 100, 255), width=1)
    d.polygon([(cx - 8, 28), (cx + 8, 28), (cx + 30, 46), (cx - 30, 46)], fill=INK)
    d.polygon([(cx - 7, 30), (cx + 7, 30), (cx + 27, 45), (cx - 27, 45)], fill=LAMP)
    d.line((cx - 6, 31, cx + 6, 31), fill=(120, 190, 150, 255))
    d.rectangle((cx - 27, 44, cx + 27, 46), fill=LAMP_D)
    d.ellipse((cx - 9, 42, cx + 9, 52), fill=BULB)
    d.ellipse((cx - 5, 44, cx + 5, 50), fill=(255, 255, 240, 255))


def table(d: ImageDraw.ImageDraw):
    """The table top in perspective (lit in the middle by the lamp), its front apron and legs, and the game on it: the deck, cards in front of each player, notes and coins."""
    for lx in (58, 254):
        d.rectangle((lx - 2, 196, lx + 8, 252), fill=INK)
        d.rectangle((lx, 196, lx + 6, 251), fill=LEG)
    d.polygon([(40, 168), (280, 168), (296, 192), (24, 192)], fill=INK)
    d.polygon([(43, 170), (277, 170), (292, 190), (28, 190)], fill=FELT)
    d.polygon([(90, 170), (230, 170), (246, 190), (74, 190)], fill=FELT_LIT)
    dither(d, (30, 186, 290, 189), FELT, FELT_D, 1)
    d.line((43, 170, 277, 170), fill=RIM_LIT)
    d.rectangle((22, 191, 298, 200), fill=INK)
    d.rectangle((24, 192, 296, 199), fill=RIM)
    d.rectangle((110, 192, 210, 193), fill=RIM_LIT)
    dither(d, (24, 197, 296, 199), RIM, RIM_D)
    d.rectangle((176, 172, 190, 182), fill=INK)  # the deck before the dealer
    d.rectangle((177, 173, 189, 178), fill=BACK)
    d.rectangle((177, 179, 189, 181), fill=CARD_S)
    for x, y, col in ((70, 175, RED), (80, 176, BLK), (138, 177, RED), (149, 178, BLK), (226, 176, BLK), (236, 175, RED)):
        d.rectangle((x - 1, y - 1, x + 9, y + 12), fill=INK)
        d.rectangle((x, y, x + 8, y + 11), fill=CARD)
        d.rectangle((x + 3, y + 4, x + 5, y + 7), fill=col)
    for x, y in ((102, 180), (108, 183)):  # notes
        d.rectangle((x - 1, y - 1, x + 14, y + 7), fill=INK)
        d.rectangle((x, y, x + 13, y + 6), fill=NOTE)
        d.rectangle((x + 2, y + 2, x + 4, y + 4), fill=(200, 240, 236, 255))
    for x, y in ((206, 182), (213, 184), (124, 186)):  # coins
        d.ellipse((x - 1, y - 1, x + 5, y + 4), fill=INK)
        d.ellipse((x, y, x + 4, y + 3), fill=GOLD)
        d.point((x + 1, y), fill=(255, 250, 210, 255))


def empty_chair(d: ImageDraw.ImageDraw):
    """The empty chair on our side: pulled out from the table and turned three-quarters toward the room, its seat bare and catching the lamp's light."""
    cx = 160
    for x0, x1 in ((cx - 30, cx - 34), (cx - 4, cx - 2), (cx + 22, cx + 28), (cx + 40, cx + 44)):
        d.line((x0, 238, x1, 270), fill=INK, width=4)
        d.line((x0, 238, x1, 270), fill=LEG, width=2)
    d.polygon([(cx - 30, 196), (cx + 4, 190), (cx + 6, 236), (cx - 28, 240)], fill=INK)
    d.polygon([(cx - 28, 198), (cx + 2, 193), (cx + 4, 234), (cx - 26, 238)], fill=CHAIR_D)
    d.line((cx - 27, 198, cx + 1, 193), fill=CHAIR_LIT)
    d.polygon([(cx - 32, 234), (cx + 8, 228), (cx + 46, 234), (cx + 8, 244)], fill=INK)
    d.polygon([(cx - 28, 234), (cx + 8, 229), (cx + 42, 234), (cx + 8, 242)], fill=CHAIR_LIT)
    d.polygon([(cx - 14, 234), (cx + 8, 231), (cx + 28, 234), (cx + 8, 239)], fill=lit(CHAIR_LIT, 0.4))
    d.polygon([(cx - 32, 235), (cx + 8, 244), (cx + 46, 235), (cx + 46, 239), (cx + 8, 248), (cx - 32, 239)], fill=INK)
    d.polygon([(cx - 30, 236), (cx + 8, 245), (cx + 44, 236), (cx + 44, 238), (cx + 8, 246), (cx - 30, 238)], fill=CHAIR)


def floor_pool(im: Image.Image):
    """A soft warm pool of light on the floor under the table and a contact shadow, so it stands on the ground."""
    pool = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pool)
    pd.ellipse((10, 244, 310, 272), fill=WARM + (26,))
    pd.ellipse((60, 250, 260, 270), fill=(0, 0, 0, 70))
    im.alpha_composite(pool)


def main() -> None:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    floor_pool(im)
    d = ImageDraw.Draw(im)
    person(d, 74, GRAN, "gran", 1, 76)
    person(d, 160, DEALER, "dealer", 0, 70)
    person(d, 246, WILD, "wild", -1, 76)
    arm(d, (50, 146), (60, 172), GRAN[3], GRAN[0])
    arm(d, (98, 146), (94, 160), GRAN[3], GRAN[0])
    fan(d, 94, 146, 3, 2)
    arm(d, (136, 140), (146, 174), DEALER[3], DEALER[0])
    arm(d, (184, 140), (182, 172), DEALER[3], DEALER[0])
    arm(d, (222, 146), (226, 160), WILD[3], WILD[0])
    arm(d, (270, 146), (262, 172), WILD[3], WILD[0])
    fan(d, 226, 146, 3, -2)
    table(d)
    lamp(d, im)
    empty_chair(d)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT)
    print("wrote", OUT.relative_to(ROOT), im.size)


if __name__ == "__main__":
    main()
