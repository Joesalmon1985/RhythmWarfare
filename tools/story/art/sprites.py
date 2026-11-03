"""Pillow-made PNG sprites for what SVG cannot do (Godot's SVG importer has no blur): light beams, glows, floor spot pools,
tileable haze, the screen vignette and confetti. All white (or near white) with a computed alpha so the runtime tints them
with `modulate` and draws them additively. Small textures, scaled up by `px_scale`.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw

from .lib import PNG_DIR


def _save(name: str, rgba: np.ndarray) -> str:
    os.makedirs(PNG_DIR, exist_ok=True)
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(PNG_DIR, name), compress_level=9)
    return f"processed/{name}"


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _white(alpha: np.ndarray, tint=(255, 255, 255)) -> np.ndarray:
    h, w = alpha.shape
    out = np.zeros((h, w, 4), dtype=np.float64)
    out[..., 0], out[..., 1], out[..., 2] = tint
    out[..., 3] = alpha * 255.0
    return out


def periodic_noise(w: int, h: int, sx: float, sy: float, seed: int) -> np.ndarray:
    """Gaussian-smoothed white noise via FFT, so it tiles in both directions. Returns 0..1."""
    rng = np.random.RandomState(seed)
    n = rng.randn(h, w)
    F = np.fft.fft2(n)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-((fx * sx) ** 2 + (fy * sy) ** 2) * (2 * np.pi ** 2))
    o = np.real(np.fft.ifft2(F * g))
    o -= o.min()
    o /= max(o.max(), 1e-9)
    return o


def build_png_sprites() -> dict:
    sprites: dict = {}

    # glow: white radial falloff
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx - n / 2 + 0.5, yy - n / 2 + 0.5) / (n / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2
    sprites["glow"] = {"file": _save("glow.png", _white(a)), "pivot": [n / 2, n / 2], "px_scale": 1.0}

    # beam: a soft cone pointing down from the top centre
    w, h = 256, 640
    yy, xx = np.mgrid[0:h, 0:w]
    half = 5 + yy * (125.0 / h)
    t = np.abs(xx - w / 2 + 0.5) / half
    edge = np.clip(1 - t ** 1.7, 0, 1)
    fade = np.clip(1 - yy / h, 0, 1) ** 0.9
    core = np.clip(1 - t, 0, 1) ** 2.2
    a = (0.55 * edge + 0.45 * core) * fade * 0.85
    a[:6] *= np.linspace(0.3, 1, 6)[:, None]
    sprites["beam"] = {"file": _save("beam.png", _white(a)), "pivot": [w / 2, 0], "px_scale": 1.0, "length": h, "half_width_at_end": 130}

    # floor spot pool: a soft ellipse with a brighter rim
    w, h = 400, 140
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = np.clip(1 - r ** 2, 0, 1) ** 1.3 * 0.75
    a += np.exp(-((r - 0.86) / 0.07) ** 2) * 0.25 * (r < 1.0)
    sprites["spot_pool"] = {"file": _save("spot_pool.png", _white(np.clip(a, 0, 1))), "pivot": [w / 2, h / 2], "px_scale": 1.0}

    # haze: tileable horizontally and vertically, two different bands; 640 x 100 shown at 1280 x 200
    for name, seed, sx, sy in (("haze_a", 21, 70.0, 16.0), ("haze_b", 77, 54.0, 12.0)):
        w, h = 640, 100
        n1 = periodic_noise(w, h, sx, sy, seed)
        n2 = periodic_noise(w, h, sx * 0.45, sy * 0.45, seed + 1)
        m = 0.65 * n1 + 0.35 * n2
        m = _smooth((m - 0.38) / 0.4)
        env = np.sin(np.linspace(0, np.pi, h)) ** 1.6
        a = m * env[:, None] * 0.7
        sprites[name] = {"file": _save(name + ".png", _white(a, (226, 216, 255))), "pivot": [w / 2, h / 2], "px_scale": 2.0, "tileable_x": True}

    # vignette: dark indigo edges, 640 x 360 shown at 1280 x 720
    w, h = 640, 360
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = _smooth((r - 0.62) / 0.62) * 0.7
    sprites["vignette"] = {"file": _save("vignette.png", _white(a, (5, 2, 18))), "pivot": [w / 2, h / 2], "px_scale": 2.0}

    # confetti: four 32 x 32 frames, each a small rotated paper rectangle (supersampled 4x for clean edges)
    cols = [(255, 47, 157), (25, 210, 255), (255, 194, 63), (154, 112, 255)]
    big = Image.new("RGBA", (128 * 4, 32 * 4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    import math
    for i, c in enumerate(cols):
        ang = math.radians(20 + i * 38)
        cx, cy = (16 + i * 32) * 4, 16 * 4
        hw_, hh = 12 * 4, 6 * 4
        pts = []
        for sx, sy in ((-hw_, -hh), (hw_, -hh), (hw_, hh), (-hw_, hh)):
            pts.append((cx + sx * math.cos(ang) - sy * math.sin(ang), cy + sx * math.sin(ang) + sy * math.cos(ang)))
        dr.polygon(pts, fill=c + (255,), outline=(27, 16, 64, 255))
    small = big.resize((128, 32), Image.LANCZOS)
    os.makedirs(PNG_DIR, exist_ok=True)
    small.save(os.path.join(PNG_DIR, "confetti.png"), compress_level=9)
    sprites["confetti"] = {"file": "processed/confetti.png", "pivot": [16, 16], "px_scale": 1.0, "frames": 4, "frame_size": [32, 32]}
    return sprites
