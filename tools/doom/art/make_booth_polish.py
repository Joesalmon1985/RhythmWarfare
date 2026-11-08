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




# --- round 2 (docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md, Booth): the window looks out on the iron balcony, the drop and the moonlit skyline (a lighter storm sky, the Balcony's rail,
# lit facades across the drop); the dock door's thick steel leaf with its louvre; the shutter's street drawn as a street (perspective, a sodium lamp, wet reflections, rain); the
# Mothership chamber toned down to the painting's dark violet doorway (one violet portal behind the figure)

def sky2():
    """The window's sky: torn storm cloud lit by the moon (upper left of the view west), a low skyline with lit windows and red mast lamps (lighter than round 1: the exposure rule)."""
    return dk.to_img(dk.sky_strip(632, clouds=("#18243c", "#203050", "#2c3e64", "#3a507a", "#4c6894", "#6a88b4"), glow="#5a6ab0", lift=0.06, moon=(770, 150, 13),
                                  skyline={"layers": (("#2c3a5c", 12, 40, 0.12), ("#222c4a", 16, 50, 0.14)), "win": ("#e0a448", "#ffc068", "#5ad0ff", "#ff2a20"), "street": "#0a0c1a"}))


def steel_leaf():
    """The dock door's steel leaf swung open against the aisle wall (decal, 2.2 m): a thick grey leaf with a louvre grille low down, a push bar, rivets, a worn edge and a wet sheen."""
    W_, H_ = 128, 272
    arr = dk.ramp(dk.vnoise(W_, H_, 691, ((3, 0.5), (12, 0.5)), False, False) * 0.5 + 0.3, ("#26282c", "#3a3c42", "#50545a", "#6a6e76", "#8a8e96"), cell=2)
    arr[:, :8] = dk.hexa("#16181c")
    arr[:, -8:] = dk.hexa("#16181c")
    arr[:6, :] = dk.hexa("#16181c")
    arr[-6:, :] = dk.hexa("#16181c")
    for y in range(176, 240, 8):  # the louvre
        arr[y:y + 4, 22:106] = dk.hexa("#121316")
        arr[y + 4:y + 6, 22:106] = dk.hexa("#7a7e86")
    arr[120:128, 20:108] = dk.hexa("#9a9ea6")  # the push bar
    arr[128:130, 20:108] = dk.hexa("#1a1c20")
    for y in (20, 100, 160, 250):
        for x in (14, 112):
            arr[y:y + 3, x:x + 3] = dk.hexa("#a8acb4")
    rust = dk.vnoise(W_, H_, 692, ((6, 0.5), (24, 0.5)), False, False)
    dk.mix_dither(arr, np.clip((rust - 0.6) * 2.0, 0, 0.5) * np.linspace(0.3, 1.0, H_)[:, None], "#6a3418", k=0.5, cell=2)
    dk.mix_dither(arr, np.clip(1 - np.abs(np.arange(W_) - 90) / 12.0, 0, 0.5)[None, :].repeat(H_, 0), "#c8ccd8", k=0.35, cell=2)
    return dk.to_img(arr).convert("RGBA")


def shutter_open2():
    """The annex's far wall: the roller shutter three quarters up and under it the loading street in the rain, drawn in perspective: wet asphalt running away to a vanishing point,
    a dark brick wall left, warehouses right with two lit windows, a sodium street lamp and its long reflection, a van's tail lights, rain (emissive decal)."""
    W_, H_ = 256, 256
    yy, xx = np.indices((H_, W_))
    hz, vx = 132, 150
    arr = dk.ramp(np.clip((hz - yy) / hz, 0, 1) * 0.6 + dk.vnoise(W_, H_, 701, ((4, 0.5), (12, 0.5)), False, False) * 0.25, ("#1a1838", "#24224a", "#302c5e", "#3e3870"))
    road = yy > hz
    t = np.clip((yy - hz) / (H_ - hz), 0, 1)
    arr[road] = dk.ramp((dk.vnoise(W_, H_, 702, ((6, 0.5), (24, 0.5)), False, False) * 0.4 + 0.25 + t * 0.15)[road][None, :], ("#141420", "#22223a", "#34345a", "#4a4a70"))[0]
    wall_l = (xx < vx - 30 - (yy - hz) * 0.9) & (yy > 50) & (xx < 110)
    arr[wall_l] = dk.ramp(dk.vnoise(W_, H_, 703, ((8, 0.5), (32, 0.5)), False, False)[wall_l][None, :] * 0.5 + 0.2, ("#2a1410", "#401e18", "#582a20"))[0]
    wall_r = (xx > vx + 40 + (yy - hz) * 0.6) & (yy > 70) & (xx > 160)
    arr[wall_r] = dk.ramp(dk.vnoise(W_, H_, 704, ((8, 0.5), (32, 0.5)), False, False)[wall_r][None, :] * 0.5 + 0.2, ("#1a1814", "#2a261e", "#3a342a"))[0]
    for x0, y0 in ((200, 96), (228, 120)):
        arr[y0:y0 + 14, x0:x0 + 12] = dk.hexa("#ffc068")
    lx, ly = 120, 78
    arr[ly:hz + 10, lx:lx + 2] = dk.hexa("#2a2a30")
    g = np.clip(1 - np.sqrt(((xx - lx) / 26.0) ** 2 + ((yy - ly) / 20.0) ** 2), 0, 1)
    dk.mix_dither(arr, g * 0.9, "#ffb050", k=0.6)
    arr[ly - 2:ly + 3, lx - 4:lx + 6] = dk.hexa("#fff0c0")
    dk.mix_dither(arr, np.where(road, np.clip(1 - np.abs(xx - lx - (yy - hz) * 0.25) / (3 + t * 8), 0, 1) * 0.9, 0), "#ffc060", k=0.6)
    arr[hz + 6:hz + 9, vx + 4:vx + 8] = dk.hexa("#ff2a20")
    arr[hz + 6:hz + 9, vx + 18:vx + 22] = dk.hexa("#ff2a20")
    rng = np.random.default_rng(705)
    for _ in range(110):
        x, y = int(rng.integers(0, W_)), int(rng.integers(64, H_ - 8))
        arr[y:y + 7, x] = arr[y:y + 7, x] * 0.4 + dk.hexa("#9ab0e0") * 0.6
    for y in range(0, 60, 6):  # the shutter's slats, rolled three quarters up
        arr[y:y + 5, :] = dk.ramp(np.full((5, W_), 0.5) + dk.vnoise(W_, 5, 706 + y, ((16, 1.0),), False, False) * 0.3, ("#3a3a40", "#5a5a62", "#7a7a84"))
        arr[y + 5, :] = dk.hexa("#141418")
    arr[58:64, :] = dk.hexa("#8a6a20")
    arr[:, :12] = dk.hexa("#2a2a30")
    arr[:, -12:] = dk.hexa("#2a2a30")
    return dk.to_img(arr)


def facade():
    return dk.p_wall_bldg(711, ("#2c3854", "#3a4866", "#4a587a", "#5c6c90"))


def iron_rail():
    import make_balcony_art as ba
    return ba.rail_tile()


def window_glass():
    """Round 2: the window over the desk as glass, not mesh (the painting's): a dark steel frame (a mullion, a transom, the sill) and clear panes with rain running down them (opaque
    pale streaks and drops; the panes are alpha, so the balcony, the drop and the skyline show through). A 128 px tile with alpha (the railing contract)."""
    from PIL import Image as _I
    W_ = 128
    arr = np.zeros((W_, W_, 3), np.float32) + dk.hexa("#26221e")
    alpha = np.zeros((W_, W_), bool)
    frame = np.zeros((W_, W_), bool)
    frame[:, :5] = True
    frame[:4, :] = True
    frame[40:44, :] = True
    frame[116:, :] = True
    arr[frame] = dk.ramp(dk.vnoise(W_, W_, 731, ((4, 0.5), (16, 0.5)), False, False)[frame][None, :] * 0.5 + 0.3, ("#1a1814", "#2e2a24", "#4a4238", "#6a5e4e"))[0]
    alpha |= frame
    rng = np.random.default_rng(732)
    for _ in range(26):
        x, y, ln = int(rng.integers(6, W_)), int(rng.integers(4, 110)), int(rng.integers(4, 22))
        y1 = min(116, y + ln)
        arr[y:y1, x] = dk.hexa("#a8b8d8")
        alpha[y:y1, x] = True
        arr[y1 - 1:y1 + 1, max(5, x - 1):x + 1] = dk.hexa("#d8e4f4")
        alpha[y1 - 1:y1 + 1, max(5, x - 1):x + 1] = True
    for _ in range(40):
        x, y = int(rng.integers(6, W_ - 1)), int(rng.integers(5, 114))
        arr[y, x] = dk.hexa("#c8d4ec")
        alpha[y, x] = True
    rgba = np.dstack([np.clip(arr, 0, 255).astype(np.uint8), np.where(alpha, 255, 0).astype(np.uint8)])
    return _I.fromarray(rgba, "RGBA")


ROUND2 = {"bt_sky": sky2, "bt_window": window_glass, "bt_steel_leaf": steel_leaf, "bt_shutter_open": shutter_open2, "bt_facade": facade, "bt_iron_rail": iron_rail,
          "bt_win_amber": lambda: dk.p_window("#ffb050", 721), "bt_win_violet": lambda: dk.p_window("#c070ff", 722), "bt_win_dark": lambda: dk.p_window(None, 723),
          "bt_moth_portal": dk.p_violet_door}


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {"bt_desk_big": desk_big, "bt_wall_foam": wall_foam, "bt_floor_grate": floor_grate, "bt_floor_conc": floor_conc, "bt_sky": sky, "bt_shutter_open": shutter_open,
           "bt_wall_dock": wall_dock, "bt_wall_steel": wall_steel, "bt_ceil": ceil, "bt_floor_plate": floor_plate}
    out.update(ROUND2)
    for name, fn in out.items():
        fn().save(os.path.join(OUT, name + ".png"))
    n = sum(mc.write(mc.CROPS[key], OUT, who) for who, key in CROPPED.items())
    return len(out), n


if __name__ == "__main__":
    print("polish: %d images and %d guide frames (cropped) to %s" % (*main(), OUT))
