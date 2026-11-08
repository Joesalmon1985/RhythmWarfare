"""Stage D polish of the DJ Booth (docs/briefs/DOOM_POLISH_BRIEF.md, docs/doom/scenes/booth.md): run after make_booth_art.py (its `main` calls `main` here last).

    python -I tools/doom/art/make_booth_art.py

  * the big desk: CROPPED from the painting (`Rhythm Booth, Three Hidden Routes-5.png`: the turntable, mixer, lamp, mug, headphones and record crate in the lower left) as one foreground
    billboard `bt_desk_big` (an outline polygon traced on the painting, hard alpha, nearest-neighbour to 256 px tall);
  * the three guides: CROPPED from the same painting (tools/doom/art/make_dock_crop.py CROPS `balcony_booth`, `mothership_booth`, `dock_booth`: 250, 216 and 466 px tall there);
  * 256 px tiles (128 texels per metre) on the Dock's numpy helpers: olive acoustic foam in wedge panels, the aisle's diamond grate, wet dock concrete with sodium and yellow-stripe gloss,
    corrugated steel cladding, riveted plate, the joisted ceiling, the tread plate;
  * the storm sky over the iron balcony outside the window, and the dock annex's open roller shutter onto the rainy street (emissive, the Dock's way).
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_dock_art as dk  # noqa: E402
import make_dock_crop as mc  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_booth", "textures")
PAINTING = os.path.join(ROOT, "art", "reference", "doom_worlds", "Rhythm Booth, Three Hidden Routes-5.png")
T = dk.T
CROPPED = {"balcony": "balcony_booth", "mothership": "mothership_booth", "dock": "dock_booth"}
# the desk's outline in painting pixels (clockwise from the window sill at the left edge): the lamp's head and arm, the mixer, the deck at the desk's far end, the racks under it; the
# stool (a billboard of its own) is left out
DESK = [(0, 525), (205, 505), (238, 425), (298, 366), (358, 340), (420, 352), (482, 420), (470, 470), (600, 480), (720, 462), (765, 470), (930, 490), (962, 505), (962, 600), (936, 610),
        (936, 700), (760, 700), (700, 760), (560, 940), (0, 940)]
DESK_H = 256


def desk_big():
    im = Image.open(PAINTING).convert("RGB")
    xs, ys = [p[0] for p in DESK], [p[1] for p in DESK]
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(DESK, fill=255)
    rgba = im.crop(box).convert("RGBA")
    rgba.putalpha(mask.crop(box))
    k = DESK_H / rgba.height
    small = rgba.resize((max(1, round(rgba.width * k)), DESK_H), Image.NEAREST)
    a = np.array(small)
    a[..., 3] = np.where(a[..., 3] >= 128, 255, 0)
    return Image.fromarray(a, "RGBA")


def wall_foam():
    """Olive acoustic foam in square wedge panels (the ribs alternate direction per panel), dark seams, warm light catching the rib tops, a few torn patches."""
    rng = np.random.default_rng(601)
    arr = np.zeros((T, T, 3), np.float32)
    yy, xx = np.indices((T, T))
    for py in range(0, T, 64):
        for px in range(0, T, 64):
            horiz = ((px // 64) + (py // 64)) % 2 == 0
            ph = (yy - py) if horiz else (xx - px)
            rib = (ph % 8) / 8.0
            v = np.clip(0.25 + 0.6 * (1 - np.abs(rib - 0.35) * 2.2), 0, 1)
            v = v + (dk.vnoise(T, T, int(rng.integers(1 << 30)), ((8, 0.5), (32, 0.5))) - 0.5) * 0.25
            sel = (yy >= py) & (yy < py + 64) & (xx >= px) & (xx < px + 64)
            arr[sel] = dk.ramp(np.clip(v[sel], 0, 1)[None, :], ("#0c0c04", "#22220e", "#3a3a1c", "#5a5a2e", "#8a8648"), cell=2)[0]
    for k in range(0, T, 64):
        arr[k:k + 2, :] = dk.hexa("#0a0a06")
        arr[:, k:k + 2] = dk.hexa("#0a0a06")
    for _ in range(3):
        x, y = int(rng.integers(8, T - 30)), int(rng.integers(8, T - 30))
        arr[y:y + 14, x:x + 18] = arr[y:y + 14, x:x + 18] * 0.45
    return dk.to_img(arr)


def floor_grate():
    """The aisle's anti-slip floor: diamond tread plate in dark steel, worn bright on the walking line, a warm sheen from the caged lamps."""
    arr = dk.ramp(dk.vnoise(T, T, 611, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#140e0c", "#221812", "#30221a", "#423024"), cell=2)
    yy, xx = np.indices((T, T))
    dia = ((xx // 2 + yy // 2) % 6 == 0) | ((xx // 2 - yy // 2) % 6 == 0)
    arr[dia] = arr[dia] * 0.55 + dk.hexa("#6a5038") * 0.45
    wear = np.clip(1 - np.abs(xx - 128) / 70.0, 0, 1) * 0.5
    dk.mix_dither(arr, wear * (dia > 0), "#9a7a50", k=0.5, cell=2)
    dk.wet_gloss(arr, 612, ("#ffa850", "#ff7a30"), n=4, length=(60, 140), width=(4, 9), ripples=0, sheen="#3a2a20")
    return dk.to_img(arr)


def floor_conc():
    """The dock annex: wet concrete with the painting's yellow stripes and the sodium pendants' long reflections."""
    arr = dk.conc_tile(621, base=("#1a1814", "#2a261e", "#3a3428", "#4a4434"), gloss_cols=("#ffb050", "#ffc060", "#e0a020"))
    wear = dk.vnoise(T, T, 622, ((16, 0.5), (64, 0.5)))
    sel = np.zeros((T, T), bool)
    sel[:, 100:118] = True
    sel &= wear > 0.3
    arr[sel] = dk.ramp(wear[sel][None, :], ("#6a5418", "#a8821e", "#d0a830"))[0]
    return dk.to_img(arr)


def sky():
    return dk.to_img(dk.sky_strip(631, clouds=("#060a18", "#0c1428", "#142038", "#1e2c4a", "#2c3c60", "#465a80"), glow="#3a4a90", moon=(900, 120, 16),
                                  skyline={"layers": (("#141c34", 20, 70, 0.10), ("#0c1226", 30, 110, 0.12)), "win": ("#e0a448", "#ffc068", "#5ad0ff", "#ff2a20"), "street": "#0a0c1a"}))


def shutter_open():
    """The annex's far wall: a roller shutter three quarters up, the rainy loading street under it (sodium light, wet asphalt, rain), the shutter's slats above (emissive decal)."""
    W_, H_ = 256, 256
    arr = dk.ramp(dk.vnoise(W_, H_, 641, ((4, 0.5), (16, 0.5)), False, False) * 0.5 + 0.25, ("#0a0c18", "#141a30", "#202a48", "#30406a"))
    yy, xx = np.indices((H_, W_))
    street = yy > 170
    arr[street] = dk.ramp(dk.vnoise(W_, H_, 642, ((8, 0.5), (32, 0.5)), False, False)[street][None, :] * 0.5 + 0.2, ("#141420", "#24243a", "#3a3a5a"))[0]
    for cx in (60, 190):
        g = np.clip(1 - np.sqrt(((xx - cx) / 40.0) ** 2 + ((yy - 120) / 60.0) ** 2), 0, 1) * 0.8
        dk.mix_dither(arr, g, "#ffb050", k=0.55)
        dk.mix_dither(arr, np.where(street, np.clip(1 - np.abs(xx - cx) / 10.0, 0, 1) * 0.8, 0), "#ffc060", k=0.6)
    rng = np.random.default_rng(643)
    for _ in range(90):
        x, y = int(rng.integers(0, W_)), int(rng.integers(60, H_ - 10))
        arr[y:y + 6, x] = arr[y:y + 6, x] * 0.4 + dk.hexa("#9ab0e0") * 0.6
    for y in range(0, 60, 6):
        arr[y:y + 5, :] = dk.ramp(np.full((5, W_), 0.5) + dk.vnoise(W_, 5, 644 + y, ((16, 1.0),), False, False) * 0.3, ("#3a3a40", "#5a5a62", "#7a7a84"))
        arr[y + 5, :] = dk.hexa("#141418")
    arr[:, :12] = dk.hexa("#2a2a30")
    arr[:, -12:] = dk.hexa("#2a2a30")
    return dk.to_img(arr)


def wall_dock():
    """The dock annex and the balcony walls: corrugated steel cladding (vertical ribs lit on one side), rust runs, rain streaks."""
    arr = dk.ramp(dk.vnoise(T, T, 651, ((4, 0.5), (16, 0.5))) * 0.5 + 0.25, ("#120e0a", "#2a2018", "#443424", "#64503a", "#94724c"), cell=2)
    yy, xx = np.indices((T, T))
    rib = (xx % 16) / 16.0
    arr *= (0.75 + 0.45 * np.clip(1 - np.abs(rib - 0.3) * 3, 0, 1))[..., None]
    rust = dk.vnoise(T, T, 652, ((6, 0.5), (24, 0.5)))
    dk.mix_dither(arr, np.clip((rust - 0.55) * 2.0, 0, 0.6) * np.clip((yy / T) * 1.4, 0, 1), "#7a3a18", k=0.5, cell=2)
    rng = np.random.default_rng(653)
    for _ in range(14):
        x0, y0, ln = int(rng.integers(T)), int(rng.integers(T)), int(rng.integers(30, 120))
        dk.mix_dither(arr, np.where((np.abs(xx - x0) < 1) & ((yy - y0) % T < ln), 0.6, 0), "#8a8aa0", k=0.4)
    return dk.to_img(arr)


def wall_steel():
    """Door frames and risers: riveted steel plate, worn bright at the edges, rust at the seams."""
    arr = dk.ramp(dk.vnoise(T, T, 661, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#1c1a18", "#2e2a26", "#423c34", "#585046", "#746a5c"), cell=2)
    for k in range(0, T, 64):
        arr[k:k + 2, :] = dk.hexa("#0c0a08")
        arr[:, k:k + 2] = dk.hexa("#0c0a08")
        for r in range(8, T, 16):
            arr[k + 4:k + 6, r:r + 2] = dk.hexa("#9a8e7c")
            arr[r:r + 2, k + 4:k + 6] = dk.hexa("#9a8e7c")
    rust = dk.vnoise(T, T, 662, ((6, 0.5), (24, 0.5)))
    dk.mix_dither(arr, np.clip((rust - 0.55) * 2.0, 0, 0.6), "#6a3418", k=0.5, cell=2)
    return dk.to_img(arr)


def ceil():
    """The booth's ceiling: dark acoustic panels between steel joists, a cable tray, warm light catching the joists."""
    arr = dk.ramp(dk.vnoise(T, T, 671, ((4, 0.5), (16, 0.5))) * 0.5 + 0.2, ("#141210", "#22201a", "#323026", "#464234"), cell=2)
    for k in range(0, T, 64):
        arr[k:k + 6, :] = dk.ramp(np.full((6, T), 0.6), ("#3a3024", "#6a563c", "#9a7c54"))
        arr[k + 6:k + 8, :] = dk.hexa("#0a0806")
    arr[:, 120:136] = arr[:, 120:136] * 0.5 + dk.hexa("#2a2824") * 0.5
    return dk.to_img(arr)


def floor_plate():
    arr = dk.ramp(dk.vnoise(T, T, 681, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#16120e", "#262018", "#382e22", "#4c3e2e"), cell=2)
    yy, xx = np.indices((T, T))
    dia = ((xx // 2 + yy // 2) % 8 == 0) & ((xx // 2 - yy // 2) % 8 == 4)
    arr[dia] = arr[dia] * 0.55 + dk.hexa("#8a7050") * 0.45
    for k in range(0, T, 128):
        arr[k:k + 2, :] *= 0.45
        arr[:, k:k + 2] *= 0.45
    dk.wet_gloss(arr, 682, ("#ffa850", "#ff7a30"), n=4, length=(60, 140), width=(4, 9), ripples=0, sheen="#3a2a20")
    return dk.to_img(arr)


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {"bt_desk_big": desk_big, "bt_wall_foam": wall_foam, "bt_floor_grate": floor_grate, "bt_floor_conc": floor_conc, "bt_sky": sky, "bt_shutter_open": shutter_open,
           "bt_wall_dock": wall_dock, "bt_wall_steel": wall_steel, "bt_ceil": ceil, "bt_floor_plate": floor_plate}
    for name, fn in out.items():
        fn().save(os.path.join(OUT, name + ".png"))
    n = sum(mc.write(mc.CROPS[key], OUT, who) for who, key in CROPPED.items())
    return len(out), n


if __name__ == "__main__":
    print("polish: %d images and %d guide frames (cropped) to %s" % (*main(), OUT))
