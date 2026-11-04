"""Draws the zone pictures of the whole Deathtrap Dungeon (one per zone of the legacy adaptation's 17, plus death, victory and a generic monster) into assets/trial/.

    python tools/trial/make_zone_scenes.py

Own work, procedural pixel art on the same helpers as make_scenes.py (which draws the six pictures of the opening). Placeholders: replace a file with a 1280x720 PNG of the
same name and nothing else changes.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_scenes as ms  # noqa: E402

ROOT = ms.ROOT
OUT = ms.OUT
W, H = ms.W, ms.H
TINTS = {"dd_pit": (-6, -6, 0), "dd_lower": (8, 0, -10), "dd_trialmaster": (14, 6, -6), "dd_idol": (16, 10, -12), "dd_grotto": (-14, 4, 16), "dd_vaults": (4, 8, 20),
         "dd_vault_inner": (10, 4, 26), "dd_service": (10, 10, 0), "dd_mirror": (6, 6, 22), "dd_blood": (30, -12, -12), "dd_grub": (14, 4, -8), "dd_troglodytes": (24, 8, -14),
         "dd_manticore": (22, 0, -6), "dd_igbut": (18, 14, 4)}
WARM = ("dd_trialmaster", "dd_troglodytes", "dd_manticore", "dd_igbut")


def base(rng: random.Random, zone: str):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    keep = ms.STONE
    ms.STONE = [tuple(max(0, min(255, c + t)) for c, t in zip(col, TINTS.get(zone, (0, 0, 0)))) for col in keep]
    ms.tunnel(d, far=(112, 60, 208, 108))
    ms.STONE = keep
    ms.crystals(d, rng, 10, (255, 190, 120) if zone in WARM else ms.CRYSTAL)
    return img, d


def zone_scene(zone: str, rng: random.Random) -> Image.Image:
    img, d = base(rng, zone)
    if zone == "dd_pit":
        d.ellipse((90, 112, 230, 166), fill=(4, 4, 10))
        d.ellipse((104, 120, 216, 160), fill=(0, 0, 4))
        d.line([(228, 108), (236, 132), (240, 150)], fill=(150, 110, 70), width=2)
    elif zone == "dd_lower":
        d.rectangle((0, 0, W, 22), fill=(18, 16, 28))
        ms.box(d, 70, 128, 22, 14)
        ms.box(d, 240, 126, 22, 14)
    elif zone == "dd_trialmaster":
        d.rectangle((124, 56, 196, 120), fill=(60, 56, 78))
        d.rectangle((140, 66, 180, 120), fill=(10, 8, 16))
        for x, y in ((60, 140), (84, 148), (106, 138)):
            d.rectangle((x, y, x + 12, y + 12), fill=(235, 232, 220))
            d.point((x + 3, y + 3), fill=(20, 20, 30))
            d.point((x + 8, y + 8), fill=(20, 20, 30))
    elif zone == "dd_idol":
        d.rectangle((110, 20, 210, 150), fill=(98, 80, 60))
        d.rectangle((126, 40, 194, 100), fill=(120, 100, 76))
        d.ellipse((136, 52, 156, 72), fill=(40, 220, 120))
        d.ellipse((164, 52, 184, 72), fill=(220, 40, 60))
        d.rectangle((138, 82, 182, 94), fill=(30, 22, 18))
    elif zone == "dd_grotto":
        d.rectangle((0, 120, W, H), fill=(18, 40, 70))
        for k in range(14):
            y = 124 + k * 4
            d.line([(rng.randint(0, 120), y), (rng.randint(180, W), y)], fill=(40, 80, 130))
        d.polygon([(250, 112), (280, 100), (292, 124), (264, 132)], fill=(70, 60, 50))
    elif zone == "dd_vaults":
        for x in (40, 130, 220):
            d.rectangle((x, 80, x + 56, 150), fill=(46, 48, 78))
            d.rectangle((x + 8, 90, x + 48, 140), fill=(24, 26, 48))
            d.ellipse((x + 22, 108, x + 34, 120), fill=ms.GOLD)
    elif zone == "dd_vault_inner":
        d.polygon([(160, 76), (184, 104), (160, 140), (136, 104)], fill=(210, 240, 255))
        d.polygon([(160, 76), (172, 104), (160, 128)], fill=(250, 255, 255))
        ms.glow_floor(img, 160, 110, 50, (200, 235, 255), 0.35)
    elif zone == "dd_service":
        for x in (40, 70, 260):
            d.rectangle((x, 0, x + 6, H), fill=(88, 90, 100))
        d.rectangle((140, 100, 190, 136), outline=(160, 120, 70), width=3)
        d.line([(165, 0), (165, 100)], fill=(150, 150, 160), width=2)
    elif zone == "dd_mirror":
        for x in range(30, 300, 52):
            d.rectangle((x, 40, x + 40, 130), fill=(120, 150, 190))
            d.line([(x + 6, 46), (x + 20, 120)], fill=(220, 240, 255))
    elif zone == "dd_blood":
        d.ellipse((70, 118, 250, 168), fill=(110, 14, 20))
        d.ellipse((92, 124, 228, 160), fill=(150, 20, 26))
    elif zone == "dd_grub":
        d.rectangle((0, 0, 90, H), fill=(12, 10, 18))
        d.rectangle((230, 0, W, H), fill=(12, 10, 18))
        ms.box(d, 150, 130, 24, 14, seal=True)
        d.ellipse((130, 70, 160, 90), fill=(60, 40, 30))
    elif zone == "dd_troglodytes":
        d.polygon([(146, 124), (160, 96), (174, 124)], fill=(255, 150, 40))
        d.polygon([(152, 124), (160, 108), (168, 124)], fill=(255, 220, 90))
        for x in (50, 250):
            d.polygon([(x, 120), (x + 20, 80), (x + 40, 120)], fill=(80, 56, 36))
    elif zone == "dd_manticore":
        for x in (50, 130, 210, 270):
            d.rectangle((x, 20, x + 16, 150), fill=(70, 64, 90))
        d.polygon([(130, 150), (150, 110), (190, 110), (210, 150)], fill=(150, 80, 30))
    elif zone == "dd_igbut":
        d.rectangle((110, 30, 210, 150), fill=(72, 70, 96))
        d.rectangle((122, 42, 198, 150), fill=(28, 26, 44))
        for x, c in ((134, (40, 200, 110)), (154, (60, 100, 240)), (174, (230, 240, 250))):
            d.ellipse((x, 82, x + 14, 96), fill=c)
    ms.noise(img, rng, 7)
    ms.glow_floor(img, 160, 128, 38)
    ms.vignette(img)
    return img


def scene_death(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (22, 4, 6))
    d = ImageDraw.Draw(img)
    d.ellipse((120, 40, 200, 120), fill=(220, 214, 200))
    d.ellipse((136, 70, 156, 92), fill=(20, 4, 6))
    d.ellipse((164, 70, 184, 92), fill=(20, 4, 6))
    d.polygon([(160, 94), (154, 108), (166, 108)], fill=(20, 4, 6))
    d.rectangle((136, 112, 184, 128), fill=(214, 208, 194))
    for x in range(138, 184, 8):
        d.line([(x, 112), (x, 128)], fill=(20, 4, 6))
    ms.noise(img, rng, 9)
    ms.vignette(img)
    return img


def scene_victory(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (255, 214, 120))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(255 - 80 * t), int(214 - 70 * t), int(150 - 60 * t)))
    d.polygon([(100, 180), (130, 60), (190, 60), (220, 180)], fill=(255, 250, 230))
    d.rectangle((96, 40, 104, 180), fill=(80, 70, 90))
    d.rectangle((216, 40, 224, 180), fill=(80, 70, 90))
    d.ellipse((140, 20, 180, 60), fill=(255, 255, 240))
    ms.noise(img, rng, 5)
    return img


def monster() -> tuple[Image.Image, Image.Image]:
    frames = []
    for hit in (False, True):
        im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        body = (200, 200, 200) if hit else (150, 150, 150)  # grey: the game tints it per creature
        d.ellipse((14, 20, 50, 56), fill=body)
        d.polygon([(16, 24), (10, 6), (24, 18)], fill=body)
        d.polygon([(48, 24), (54, 6), (40, 18)], fill=body)
        eye = (255, 255, 255) if hit else (255, 40, 30)
        d.ellipse((22, 30, 30, 38), fill=eye)
        d.ellipse((34, 30, 42, 38), fill=eye)
        d.rectangle((24, 44, 40, 48), fill=(20, 10, 10))
        frames.append(im)
    return frames[0], frames[1]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out = {"death": scene_death, "victory": scene_victory}
    for name, fn in out.items():
        fn(random.Random(sum(map(ord, name)))).resize((W * 4, H * 4), Image.NEAREST).save(OUT / f"{name}.png", optimize=True)
        print("wrote", f"assets/trial/scenes/{name}.png")
    for zone in TINTS:
        zone_scene(zone, random.Random(sum(map(ord, zone)))).resize((W * 4, H * 4), Image.NEAREST).save(OUT / f"{zone}.png", optimize=True)
        print("wrote", f"assets/trial/scenes/{zone}.png")
    a, b = monster()
    a.save(ROOT / "assets" / "trial" / "art" / "monster_0.png")
    b.save(ROOT / "assets" / "trial" / "art" / "monster_1.png")
    print("wrote the generic monster")


if __name__ == "__main__":
    main()
