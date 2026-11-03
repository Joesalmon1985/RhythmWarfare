"""Tiny SVG drawing helpers shared by the Night One art generators.

Everything is drawn in "design pixels" (1 unit = 1 px of the 1280 x 720 stage, or 1 px of a character rig) and written at 2x
(`SCALE`): the SVG `width/height` are twice the viewBox, so Godot imports a crisp texture and the manifest says px_scale 0.5.
Godot's SVG importer (ThorVG) supports gradients, clipPath, opacity and strokes with round caps, but no filters.
"""
from __future__ import annotations

import math
import os

SCALE = 2
OUT = "#1b1040"  # the outline colour of every character and prop: deep indigo, never pure black

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ASSET_DIR = os.path.join(ROOT, "assets", "story", "night_one")
SVG_DIR = os.path.join(ASSET_DIR, "source")
PNG_DIR = os.path.join(ASSET_DIR, "processed")


def f(v: float) -> str:
    """Compact number formatting."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def pts(points) -> str:
    return " ".join(f"{f(x)},{f(y)}" for x, y in points)


# ---- colour -------------------------------------------------------------------------------------------------------

def hex_to_rgb(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, int(round(v)))):02x}" for v in rgb)


def mix(a: str, b: str, t: float) -> str:
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def darken(c: str, t: float) -> str:
    return mix(c, "#150a33", t)  # towards the shadow indigo, so shade never goes muddy grey


def lighten(c: str, t: float) -> str:
    return mix(c, "#ffffff", t)


# ---- shapes -------------------------------------------------------------------------------------------------------

def _attrs(fill=None, stroke=None, sw=None, op=None, sop=None, cap=None, join="round", extra="") -> str:
    a = []
    a.append(f'fill="{fill}"' if fill else 'fill="none"')
    if stroke:
        a.append(f'stroke="{stroke}"')
        a.append(f'stroke-width="{f(sw if sw is not None else 3)}"')
        a.append(f'stroke-linejoin="{join}"')
        if cap:
            a.append(f'stroke-linecap="{cap}"')
        if sop is not None:
            a.append(f'stroke-opacity="{f(sop)}"')
    if op is not None:
        a.append(f'fill-opacity="{f(op)}"')
    if extra:
        a.append(extra)
    return " ".join(a)


def poly(points, fill=None, stroke=None, sw=3, op=None, sop=None, extra="") -> str:
    return f'<polygon points="{pts(points)}" {_attrs(fill, stroke, sw, op, sop, None, "round", extra)}/>'


def path(d, fill=None, stroke=None, sw=3, op=None, sop=None, cap="round", extra="") -> str:
    return f'<path d="{d}" {_attrs(fill, stroke, sw, op, sop, cap, "round", extra)}/>'


def circle(cx, cy, r, fill=None, stroke=None, sw=3, op=None, sop=None, extra="") -> str:
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" {_attrs(fill, stroke, sw, op, sop, None, "round", extra)}/>'


def ellipse(cx, cy, rx, ry, fill=None, stroke=None, sw=3, op=None, sop=None, extra="") -> str:
    return f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" {_attrs(fill, stroke, sw, op, sop, None, "round", extra)}/>'


def rect(x, y, w, h, fill=None, stroke=None, sw=3, rx=0, op=None, sop=None, extra="") -> str:
    r = f' rx="{f(rx)}"' if rx else ""
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"{r} {_attrs(fill, stroke, sw, op, sop, None, "round", extra)}/>'


def line(p1, p2, stroke, sw=3, op=None, cap="round") -> str:
    sop = f' stroke-opacity="{f(op)}"' if op is not None else ""
    return (f'<line x1="{f(p1[0])}" y1="{f(p1[1])}" x2="{f(p2[0])}" y2="{f(p2[1])}" stroke="{stroke}" '
            f'stroke-width="{f(sw)}" stroke-linecap="{cap}"{sop}/>')


def group(body: str, extra: str = "") -> str:
    return f"<g {extra}>{body}</g>"


def lin_grad(gid, stops, x1=0, y1=0, x2=0, y2=1, units="objectBoundingBox") -> str:
    s = "".join(f'<stop offset="{f(o)}" stop-color="{c}"' + (f' stop-opacity="{f(a)}"' if a is not None and a < 1 else "") + "/>"
                for o, c, a in _norm_stops(stops))
    return f'<linearGradient id="{gid}" gradientUnits="{units}" x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}">{s}</linearGradient>'


def rad_grad(gid, stops, cx=0.5, cy=0.5, r=0.5, units="objectBoundingBox", fx=None, fy=None) -> str:
    s = "".join(f'<stop offset="{f(o)}" stop-color="{c}"' + (f' stop-opacity="{f(a)}"' if a is not None and a < 1 else "") + "/>"
                for o, c, a in _norm_stops(stops))
    foc = f' fx="{f(fx)}" fy="{f(fy)}"' if fx is not None else ""
    return f'<radialGradient id="{gid}" gradientUnits="{units}" cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}"{foc}>{s}</radialGradient>'


def _norm_stops(stops):
    for st in stops:
        if len(st) == 2:
            yield st[0], st[1], None
        else:
            yield st


def clip(cid: str, shape: str) -> str:
    return f'<clipPath id="{cid}">{shape}</clipPath>'


def capsule(p1, p2, w, fill, shade=None, light=None, ol=3.0, outline=OUT) -> str:
    """A rounded limb segment: outline, fill, a shade strip on the right side and a highlight on the left."""
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln  # normal; for a downward limb (dx=0, dy>0) this points to screen-left
    out = line(p1, p2, outline, w + 2 * ol)
    out += line(p1, p2, fill, w)
    if shade:
        o = -w * 0.24
        out += line((x1 + nx * o, y1 + ny * o), (x2 + nx * o, y2 + ny * o), shade, w * 0.42, 0.75)
    if light:
        o = w * 0.22
        out += line((x1 + nx * o, y1 + ny * o), (x2 + nx * o, y2 + ny * o), light, w * 0.16, 0.7)
    return out


# ---- files --------------------------------------------------------------------------------------------------------

def write_svg(rel_path: str, box, body: str, defs: str = "") -> dict:
    """Write `body` (drawn in absolute coordinates) as an SVG whose viewBox is `box` = (x0, y0, x1, y1). Returns
    {"w","h","x0","y0"} of the viewBox so the caller can compute pivots."""
    x0, y0, x1, y1 = (math.floor(box[0]), math.floor(box[1]), math.ceil(box[2]), math.ceil(box[3]))
    w, h = x1 - x0, y1 - y0
    d = f"<defs>{defs}</defs>" if defs else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * SCALE}" height="{h * SCALE}" viewBox="{x0} {y0} {w} {h}">'
           f"{d}{body}</svg>\n")
    full = os.path.join(SVG_DIR, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    return {"w": w, "h": h, "x0": x0, "y0": y0}


def pivot_in(info: dict, joint_xy) -> list:
    """The joint's position inside the written texture, in texture pixels (the texture is SCALE x the viewBox)."""
    return [round((joint_xy[0] - info["x0"]) * SCALE, 1), round((joint_xy[1] - info["y0"]) * SCALE, 1)]


def bbox(points, pad=6.0):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def union(*boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
