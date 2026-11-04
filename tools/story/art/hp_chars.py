"""The six hospital visitors of the `hospital` chapter: same rig/face contract as Night One (chars.py), friendly human cartoon.

Archetypes: mum, dad, granny, kid (with a balloon), nurse, doctor; variants a and b (palette + one clothing/hair detail).
Parts are drawn at the rest pose in rig space (origin between the feet, +y down). Swinging extras (mum's hair, the kid's pigtails
and balloon, the nurse's ponytail) are parts with `swing: true` exactly like Night One's ponytail. Warm daylight rim lights
(gold on the left, coral on the right) replace Night One's neon rims.
"""
from __future__ import annotations

import math

from . import chars as C
from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rect,
                  write_svg)

RIM_L, RIM_R = "#ffd98a", "#ff9f8a"
INK = "#3a1f2e"
SKIN = {"pale": "#fbd9c0", "peach": "#f4c3a0", "tan": "#e6aa7a", "olive": "#d9a273", "brown": "#b67a52", "deep": "#8a5233",
        "dark": "#6e432c"}
EXPRESSIONS = C.EXPRESSIONS

# proportions (rig space, y up is negative); adult heads are scaled 1.12 like Night One's for crowd readability
ARCH = {
    "mum": dict(hip_y=100, sh_y=-178, sh_dx=24, neck_y=-187, cy=-212, rx=22, ry=26, up=38, fore=41, aw=13, sw=25, ww=19, hw=24,
                lw=15, leg_dx=11, shoe_h=11),
    "dad": dict(hip_y=108, sh_y=-190, sh_dx=34, neck_y=-199, cy=-225, rx=23, ry=26, up=42, fore=43, aw=17, sw=36, ww=30, hw=30,
                lw=20, leg_dx=14, shoe_h=12),
    "granny": dict(hip_y=82, sh_y=-154, sh_dx=25, neck_y=-162, cy=-187, rx=23, ry=26, up=33, fore=34, aw=13, sw=27, ww=25, hw=29,
                   lw=14, leg_dx=10, shoe_h=10),
    "kid": dict(hip_y=60, sh_y=-124, sh_dx=19, neck_y=-131, cy=-160, rx=27, ry=29, up=26, fore=27, aw=11, sw=19, ww=17, hw=19,
                lw=12, leg_dx=9, shoe_h=10),
    "nurse": dict(hip_y=102, sh_y=-180, sh_dx=26, neck_y=-189, cy=-214, rx=22, ry=26, up=38, fore=41, aw=13, sw=27, ww=21, hw=25,
                  lw=16, leg_dx=11, shoe_h=11),
    "doctor": dict(hip_y=112, sh_y=-194, sh_dx=31, neck_y=-203, cy=-229, rx=21, ry=25, up=43, fore=45, aw=15, sw=33, ww=26, hw=28,
                   lw=18, leg_dx=12, shoe_h=12),
}
for _n, _p in ARCH.items():
    if _n != "kid":
        _p["rx"] = round(_p["rx"] * 1.12)
        _p["ry"] = round(_p["ry"] * 1.12)
        _p["cy"] -= 3

# arm covering: (cloth colour or None, fraction of the segment covered from its start, cuff colour or None)
VARIANTS = {
    "mum": {
        "a": dict(skin=SKIN["peach"], hair="#6b3a24", hair2="#9a5a38", dress="#e9715b", dress2="#fff1dc", trim="#fff1dc", belt="#ffd98a",
                  cardi="#4fb3a9", shoe="#fff1dc", iris="#7a4a2a", style="long", detail="cardigan", leg="bare",
                  up=("#4fb3a9", 1.0, "#3b8f87"), fore=("#4fb3a9", 0.55, "#3b8f87"), accent="#ff9f8a"),
        "b": dict(skin=SKIN["tan"], hair="#e8b95a", hair2="#fbe19a", dress="#3fa6a0", dress2="#fff1dc", trim="#fff1dc", belt="#e9715b",
                  cardi="#3fa6a0", shoe="#e9715b", iris="#3f7a5a", style="bun", detail="scarf", leg="tights", scarf="#ff9f8a",
                  up=("#3fa6a0", 0.5, "#fff1dc"), fore=(None, 0, None), accent="#e9715b"),
    },
    "dad": {
        "a": dict(skin=SKIN["pale"], hair="#5a3622", hair2="#8a5a3a", shirt="#c8473f", shirt2="#2f3a63", pants="#4a6aa8", belt="#5a3a22", shoe="#8a5a32",
                  iris="#5a7a9a", detail="plaid", beard=True, glasses=None,
                  up=("#c8473f", 0.7, "#8f2f2c"), fore=(None, 0, None), accent="#ffd98a"),
        "b": dict(skin=SKIN["deep"], hair="#241a1c", hair2="#3a2a2c", shirt="#a9d3e8", shirt2="#ffffff", pants="#5a5f7a", belt="#2a2a3a", shoe="#3a2a2a",
                  iris="#3a2418", detail="vest", vest="#f0b04a", tie="#c8473f", beard=False, glasses="rect",
                  up=("#a9d3e8", 1.0, "#ffffff"), fore=("#a9d3e8", 1.0, "#ffffff"), accent="#c8473f"),
    },
    "granny": {
        "a": dict(skin=SKIN["pale"], hair="#f3f0ec", hair2="#ffffff", blouse="#fff1dc", cardi="#b79be0", skirt="#6a5a9a", skirt2="#d9c4ff", shoe="#7a4a3a",
                  iris="#5a7a9a", brooch="#ff9f8a", glasses="#d8a84a", pearls=False,
                  up=("#b79be0", 1.0, "#fff1dc"), fore=("#b79be0", 1.0, "#fff1dc"), accent="#ff9f8a"),
        "b": dict(skin=SKIN["tan"], hair="#c9d6f0", hair2="#eef3ff", blouse="#fff1dc", cardi="#f0b04a", skirt="#4f7a8a", skirt2="#bfe4ea", shoe="#5a3a32",
                  iris="#5a3a24", brooch="#ffffff", glasses="#c85f8a", pearls=True,
                  up=("#f0b04a", 1.0, "#fff1dc"), fore=("#f0b04a", 1.0, "#fff1dc"), accent="#c85f8a"),
    },
    "kid": {
        "a": dict(skin=SKIN["brown"], hair="#2a1a1e", hair2="#4a2a2e", tee="#fff1dc", tee2="#e9715b", denim="#4d78b8", denim2="#8fb2e0", shoe="#e9715b",
                  iris="#3a2418", style="pigtails", balloon="#e9453f", ribbon="#ffd23f", leg="dungaree", detail="dungarees",
                  up=("#fff1dc", 0.5, "#e9715b"), fore=(None, 0, None), accent="#ffd23f"),
        "b": dict(skin=SKIN["pale"], hair="#8a4a22", hair2="#b4703a", tee="#59b96a", tee2="#ffe27a", denim="#d9b878", denim2="#f0d9a0", shoe="#3b86d0",
                  iris="#3f7a5a", style="cap", cap="#3b86d0", balloon="#3fa6e8", ribbon="#ffd23f", leg="shorts", detail="star",
                  up=("#59b96a", 0.55, None), fore=(None, 0, None), accent="#ffe27a"),
    },
    "nurse": {
        "a": dict(skin=SKIN["brown"], hair="#2a1a22", hair2="#4a2a3a", scrub="#2fb5a8", scrub2="#bfeee8", shoe="#ffffff", iris="#3a2418", style="bun_cap",
                  cap="#ffffff", capmark="#2fb5a8", under=None, badge="#ff7a8a", detail="cap",
                  up=("#2fb5a8", 0.6, None), fore=(None, 0, None), accent="#ff7a8a"),
        "b": dict(skin=SKIN["olive"], hair="#3a2418", hair2="#5a3a28", scrub="#e98aa8", scrub2="#ffe0ea", shoe="#ffffff", iris="#3f7a5a", style="scrubcap",
                  cap="#6ec9d8", capmark="#ffffff", under="#ffffff", badge="#2fb5a8", detail="scrubcap",
                  up=("#e98aa8", 0.6, None), fore=("#ffffff", 1.0, "#e0e6ee"), accent="#2fb5a8"),
    },
    "doctor": {
        "a": dict(skin=SKIN["tan"], hair="#9a9aa8", hair2="#cfcfd8", coat="#ffffff", shirt="#6a9ad8", pants="#4a5470", shoe="#3a2a2a", iris="#4a5a7a",
                  tie="#c8473f", glasses="round", style="mirror", steth="#4a5470", detail="mirror",
                  up=("#ffffff", 1.0, "#6a9ad8"), fore=("#ffffff", 1.0, "#6a9ad8"), accent="#c8473f"),
        "b": dict(skin=SKIN["dark"], hair="#1e1418", hair2="#3a2a2e", coat="#ffffff", shirt="#59b96a", pants="#6a4a6a", shoe="#c8473f", iris="#2a1a14",
                  tie=None, glasses="rect", style="puff", steth="#e9453f", detail="puff",
                  up=("#ffffff", 1.0, "#59b96a"), fore=("#ffffff", 1.0, "#59b96a"), accent="#e9453f"),
    },
}


def bb(points, pad=8.0):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def bez(p0, p1, p2, n=16):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / (n - 1) for i in range(n)]]


def heart(cx, cy, s, fill, sw=2.0, stroke=OUT):
    return path(f"M{f(cx)} {f(cy + s * 0.9)} C{f(cx - s * 1.5)} {f(cy - s * 0.2)} {f(cx - s * 0.8)} {f(cy - s * 1.2)} {f(cx)} {f(cy - s * 0.4)} "
                f"C{f(cx + s * 0.8)} {f(cy - s * 1.2)} {f(cx + s * 1.5)} {f(cy - s * 0.2)} {f(cx)} {f(cy + s * 0.9)} Z", fill, stroke, sw)


def star5(cx, cy, r, fill, sw=1.6, stroke=OUT):
    pts_ = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.42
        pts_.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return poly(pts_, fill, stroke, sw)


# ---- torso ------------------------------------------------------------------------------------------------------------------

def torso_wrap(P, base, inner, outer="", flare=0.0, defs_extra=""):
    sw = P["sw"]
    ts = P["sh_y"] - 8
    by = -P["hip_y"] + 14
    d = C.torso_outline(P, flare)
    defs = clip("tc", f'<path d="{d}"/>') + C.SHADE_GRAD + defs_extra
    body = f'<path d="{d}" fill="{base}"/>' + group(inner, 'clip-path="url(#tc)"')
    shade = f'<rect x="{f(-sw - 8)}" y="{f(ts - 6)}" width="{f(sw * 2 + 16)}" height="{f(by - ts + 12)}" fill="url(#shd)"/>'
    rim_l = f'<rect x="{f(-sw - 3)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="{RIM_L}" fill-opacity="0.55"/>'
    rim_r = f'<rect x="{f(sw - 2)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="{RIM_R}" fill-opacity="0.38"/>'
    body += group(shade + rim_l + rim_r, 'clip-path="url(#tc)"')
    body += path(d, None, OUT, 3)
    body += outer
    return defs, body, (-sw - 34, ts - 24, sw + 34, by + 24)


def torso_part(arch, P, V):
    sw, ww, hw = P["sw"], P["ww"], P["hw"]
    ts = P["sh_y"] - 8
    wy = -P["hip_y"] - 34
    by = -P["hip_y"] + 14
    skin = V["skin"]
    inner, outer, defs_x, flare = "", "", "", 0.0
    if arch == "mum":
        base = V["dress"]
        flare = 1
        inner += path(f"M-15 {f(ts - 4)} Q0 {f(ts + 30)} 15 {f(ts - 4)} Z", skin, None)
        inner += path(f"M-15 {f(ts - 3)} Q0 {f(ts + 30)} 15 {f(ts - 3)}", None, V["trim"], 3)
        for sgn in (-1, 1):
            inner += path(f"M{f(sgn * (sw - 4))} {f(ts + 18)} Q{f(sgn * (ww + 2))} {f(wy - 14)} {f(sgn * (ww - 1))} {f(wy + 2)}", None, darken(base, 0.28), 1.8, sop=0.6)
        inner += rect(-hw - 4, wy + 3, hw * 2 + 8, 8, V["belt"], OUT, 2, rx=2)
        inner += circle(0, wy + 7, 3.4, lighten(V["belt"], 0.5), OUT, 1.4)
        if V["detail"] == "cardigan":
            c = V["cardi"]
            for sgn in (-1, 1):
                inner += poly([(sgn * (sw + 3), ts - 4), (sgn * 15, ts - 4), (sgn * 11, ts + 20), (sgn * 7, by + 2), (sgn * (hw + 4), by + 2)], c, OUT, 2.4)
                inner += line((sgn * 11, ts + 20), (sgn * 7, by), darken(c, 0.3), 2, 0.7)
            for k in range(3):
                inner += circle(-9 if False else 0, wy - 20 + k * 0, 0, c)
            inner += circle(-4, ts + 24, 1.8, lighten(c, 0.6), OUT, 1.0) + circle(4, ts + 24, 1.8, lighten(c, 0.6), OUT, 1.0)
        else:
            for k in range(4):  # little daisies on the bodice
                for sgn in (-1, 1):
                    inner += circle(sgn * (8 + k % 2 * 6), ts + 22 + k * 10, 2.4, V["dress2"], None, op=0.9)
            outer += path(f"M-13 {f(ts + 1)} Q0 {f(ts + 14)} 13 {f(ts + 1)} L11 {f(ts + 10)} Q0 {f(ts + 22)} -11 {f(ts + 10)} Z", V["scarf"], OUT, 2.2)
            outer += path(f"M6 {f(ts + 14)} L14 {f(ts + 38)} L5 {f(ts + 34)} L1 {f(ts + 20)} Z", V["scarf"], OUT, 2)
            outer += circle(2, ts + 14, 3.6, darken(V["scarf"], 0.18), OUT, 1.6)
    elif arch == "dad":
        if V["detail"] == "plaid":
            base = V["shirt"]
            for k in range(-3, 4):
                inner += rect(k * 12 - 2.5, ts - 6, 5, by - ts + 12, V["shirt2"], None, op=0.55)
            for k in range(0, 8):
                inner += rect(-sw - 4, ts + 6 + k * 12, sw * 2 + 8, 4, V["shirt2"], None, op=0.5)
            inner += poly([(-9, ts - 4), (-1, ts - 4), (-1, ts + 14), (-14, ts + 6)], lighten(base, 0.18), OUT, 1.8)
            inner += poly([(9, ts - 4), (1, ts - 4), (1, ts + 14), (14, ts + 6)], lighten(base, 0.18), OUT, 1.8)
            inner += line((0, ts + 12), (0, by), darken(base, 0.4), 1.8, 0.8)
            for k in range(5):
                inner += circle(0, ts + 22 + k * 14, 1.9, V["accent"], OUT, 1.0)
            inner += rect(9, ts + 26, 15, 16, darken(base, 0.1), OUT, 1.8, rx=2)
            inner += line((9, ts + 30), (24, ts + 30), V["shirt2"], 1.4, 0.8)
        else:
            base = V["shirt"]
            inner += poly([(-9, ts - 4), (-1, ts - 4), (0, ts + 12), (-14, ts + 4)], V["shirt2"], OUT, 1.8)
            inner += poly([(9, ts - 4), (1, ts - 4), (0, ts + 12), (14, ts + 4)], V["shirt2"], OUT, 1.8)
            for sgn in (-1, 1):  # knitted vest with a V neck
                inner += poly([(sgn * (sw + 3), ts - 4), (sgn * 11, ts - 4), (0, ts + 40), (sgn * (hw + 4), by + 2)], V["vest"], OUT, 2.4)
            vest = V["vest"]
            for k in range(-3, 4):
                for j in range(5):
                    cx_, cy_ = k * 11 + (j % 2) * 5.5, ts + 36 + j * 11
                    inner += poly([(cx_, cy_ - 5), (cx_ + 4.5, cy_), (cx_, cy_ + 5), (cx_ - 4.5, cy_)], None, darken(vest, 0.3), 1.2, sop=0.6)
            inner += poly([(-3, ts + 2), (3, ts + 2), (4, ts + 12), (0, ts + 40), (-4, ts + 12)], V["tie"], OUT, 1.6)
            inner += rect(-sw - 4, by - 7, sw * 2 + 8, 10, darken(vest, 0.15), OUT, 2)
    elif arch == "granny":
        base = V["blouse"]
        flare = 3
        c = V["cardi"]
        for sgn in (-1, 1):
            inner += poly([(sgn * (sw + 3), ts - 4), (sgn * 11, ts - 4), (sgn * 8, ts + 20), (sgn * 7, by + 2), (sgn * (hw + 5), by + 2)], c, OUT, 2.4)
            for k in range(5):
                inner += line((sgn * (14 + k * 3.4), ts + 8), (sgn * (13 + k * 3.8), by), darken(c, 0.14), 1.4, 0.55)
        inner += path(f"M-12 {f(ts - 3)} Q0 {f(ts + 18)} 12 {f(ts - 3)}", skin, None)
        inner += path(f"M-13 {f(ts - 3)} Q0 {f(ts + 16)} 13 {f(ts - 3)}", None, V["blouse"], 3.2)
        for k in range(4):
            inner += circle(0, ts + 16 + k * 11, 2.2, lighten(c, 0.5), OUT, 1.2)
        inner += rect(-sw + 4, by - 28, 14, 17, darken(c, 0.08), OUT, 1.8, rx=3)
        if V["pearls"]:
            for k in range(11):
                a = math.radians(18 + k * 14.4)
                inner += circle(math.cos(a) * 12 * -1 * -1, ts - 3 + math.sin(a) * 15, 2.1, "#fffaf0", OUT, 0.9)
        else:
            outer += star5(-12, ts + 20, 6.2, V["brooch"], 1.4) + circle(-12, ts + 20, 2, "#ffe27a", None)
    elif arch == "kid":
        if V["detail"] == "dungarees":
            base = V["tee"]
            for k in range(0, 9):
                inner += rect(-sw - 4, ts + k * 11 - 2, sw * 2 + 8, 5.5, V["tee2"], None, op=0.95)
            den = V["denim"]
            inner += poly([(-ww + 2, wy - 6), (ww - 2, wy - 6), (hw + 3, by + 2), (-hw - 3, by + 2)], den, OUT, 2.2)
            inner += poly([(-ww + 2, wy - 6), (ww - 2, wy - 6), (ww - 4, ts + 30), (-ww + 4, ts + 30)], den, OUT, 2.2)
            for sgn in (-1, 1):
                inner += poly([(sgn * 6, ts + 30), (sgn * 14, ts + 30), (sgn * 15, ts - 4), (sgn * 8, ts - 4)], den, OUT, 2)
                inner += circle(sgn * 11, ts + 29, 2.4, V["accent"], OUT, 1.2)
            inner += rect(-8, ts + 40, 16, 12, V["denim2"], OUT, 1.6, rx=2)
            inner += heart(0, ts + 46, 3, "#ff7a8a", 1.0)
        else:
            base = V["tee"]
            inner += star5(0, ts + 36, 13, V["tee2"], 2.0)
            inner += path(f"M-9 {f(ts - 3)} Q0 {f(ts + 9)} 9 {f(ts - 3)}", None, V["tee2"], 3.6)
            inner += rect(-hw - 4, by - 8, hw * 2 + 8, 9, V["denim"], OUT, 2)
    elif arch == "nurse":
        base = V["scrub"]
        under = V["under"] or V["scrub2"]
        inner += poly([(-13, ts - 4), (13, ts - 4), (0, ts + 24)], skin, OUT, 2)
        inner += path(f"M-14 {f(ts - 3)} L0 {f(ts + 26)} L14 {f(ts - 3)}", None, under, 4)
        inner += path(f"M-12 {f(ts - 2)} L0 {f(ts + 20)} L12 {f(ts - 2)}", None, darken(V["scrub"], 0.22), 1.4, sop=0.7)
        inner += rect(-sw + 3, ts + 38, 16, 18, darken(base, 0.1), OUT, 1.8, rx=2)
        inner += line((-sw + 8, ts + 34), (-sw + 9, ts + 46), V["badge"], 2.6)
        inner += line((-9, ts + 4), (-4, ts + 30), V["scrub2"], 1.6, 0.9) + line((9, ts + 4), (4, ts + 30), V["scrub2"], 1.6, 0.9)
        inner += rect(-1, ts + 30, 14, 18, "#ffffff", OUT, 1.6, rx=2) + rect(-1, ts + 30, 14, 5, V["badge"], None) + heart(6, ts + 41, 2.6, V["badge"], 0.8)
        inner += rect(-hw - 2, by - 8, hw * 2 + 4, 8, darken(base, 0.18), OUT, 1.8)
        inner += line((-3, by - 4), (-4, by + 8), V["scrub2"], 1.6) + line((3, by - 4), (4, by + 8), V["scrub2"], 1.6)
    elif arch == "doctor":
        base = V["shirt"]
        coat = V["coat"]
        inner += poly([(-12, ts - 4), (12, ts - 4), (0, ts + 24)], skin, OUT, 1.8)
        inner += poly([(-10, ts - 4), (-1, ts - 4), (-1, ts + 8), (-13, ts + 2)], lighten(V["shirt"], 0.2), OUT, 1.4)
        inner += poly([(10, ts - 4), (1, ts - 4), (1, ts + 8), (13, ts + 2)], lighten(V["shirt"], 0.2), OUT, 1.4)
        if V["tie"]:
            inner += poly([(-3, ts + 4), (3, ts + 4), (4.5, ts + 26), (0, ts + 38), (-4.5, ts + 26)], V["tie"], OUT, 1.6)
        for sgn in (-1, 1):
            inner += poly([(sgn * (sw + 3), ts - 4), (sgn * 12, ts - 4), (sgn * 5, ts + 18), (sgn * 4, by + 3), (sgn * (hw + 5), by + 3)], coat, OUT, 2.4)
            inner += poly([(sgn * 12, ts - 4), (sgn * 24, ts + 2), (sgn * 12, ts + 24), (sgn * 5, ts + 18)], darken(coat, 0.07), OUT, 1.8)
            inner += line((sgn * 10, ts + 26), (sgn * (hw - 2), by), darken(coat, 0.13), 1.6, 0.8)
        inner += rect(7, ts + 34, 17, 15, darken(coat, 0.06), OUT, 1.6, rx=2)
        for k, c_ in enumerate(("#c8473f", "#3b86d0")):
            inner += line((11 + k * 5, ts + 34), (12 + k * 5, ts + 27), c_, 2.2)
        inner += rect(-sw + 6, ts + 36, 14, 9, "#ffffff", OUT, 1.4, rx=1.5) + line((-sw + 8, ts + 40), (-sw + 18, ts + 40), V["steth"], 1.4)
        st = V["steth"]
        tube = (f"M-14 {f(ts + 1)} C-19 {f(ts + 34)} -4 {f(ts + 48)} 0 {f(ts + 46)} C4 {f(ts + 48)} 19 {f(ts + 34)} 14 {f(ts + 1)}")
        outer += path(tube, None, OUT, 5.6) + path(tube, None, st, 3.4) + path(tube, None, lighten(st, 0.5), 1.0, sop=0.6)
        outer += path(f"M0 {f(ts + 46)} L2 {f(ts + 60)}", None, OUT, 5.6) + path(f"M0 {f(ts + 46)} L2 {f(ts + 60)}", None, st, 3.4)
        outer += circle(2, ts + 63, 6.2, "#d8dde8", OUT, 2) + circle(2, ts + 63, 3.2, "#8f9ab0", None) + circle(0.5, ts + 61.4, 1.2, "#ffffff", None)
    else:
        base = "#ffffff"
    return torso_wrap(P, base, inner, outer, flare, defs_x)


def pelvis_part(arch, P, V):
    hy = -P["hip_y"]
    hw = P["hw"] + 1
    if arch in ("mum", "granny"):
        return None
    cloth = {"dad": V.get("pants"), "kid": V.get("denim"), "nurse": V.get("scrub"), "doctor": V.get("pants")}[arch]
    if arch == "kid" and V["detail"] == "dungarees":
        cloth = V["denim"]
    d = f"M{f(-hw)} {f(hy - 12)} L{f(hw)} {f(hy - 12)} L{f(hw + 1)} {f(hy + 12)} Q0 {f(hy + 22)} {f(-hw - 1)} {f(hy + 12)} Z"
    body = path(d, cloth, OUT, 3)
    body += line((0, hy - 6), (0, hy + 14), darken(cloth, 0.4), 1.8, 0.7)
    if arch == "dad":
        body += rect(-hw - 1, hy - 14, hw * 2 + 2, 8, V["belt"], OUT, 2) + rect(-5, hy - 14, 10, 8, "#e8d8a0", OUT, 1.6)
    elif arch == "kid" and V["detail"] == "star":  # shorts
        body = path(f"M{f(-hw - 2)} {f(hy - 12)} L{f(hw + 2)} {f(hy - 12)} L{f(hw + 5)} {f(hy + 26)} L{f(2)} {f(hy + 26)} L0 {f(hy + 12)} L{f(-2)} {f(hy + 26)} L{f(-hw - 5)} {f(hy + 26)} Z", cloth, OUT, 3)
        body += line((-hw, hy + 24), (-3, hy + 24), darken(cloth, 0.3), 2.4) + line((hw, hy + 24), (3, hy + 24), darken(cloth, 0.3), 2.4)
    elif arch == "doctor":
        body += line((-hw + 2, hy - 8), (hw - 2, hy - 8), darken(cloth, 0.3), 2.6, 0.7)
    return body, (-hw - 12, hy - 18, hw + 12, hy + 34)


def skirt_part(arch, P, V):
    """mum's dress skirt and granny's long skirt: hips part, in front of the legs."""
    hy = -P["hip_y"]
    top = hy - 16
    hw = P["hw"]
    if arch == "mum":
        bot, w0, w1, n = hy + 52, hw - 1, hw + 20, 7
        c = V["dress"]
    else:
        bot, w0, w1, n = hy + 46, hw - 1, hw + 14, 6
        c = V["skirt"]
    pts_ = []
    for k in range(n + 1):
        x = -w1 + k * (2 * w1 / n)
        pts_.append((x, bot + (6 if (k % 2 == 0 and arch == "mum" and V["detail"] == "cardigan") else (3 if k % 2 == 0 else 0))))
    d = f"M{f(-w0)} {f(top)} L{f(w0)} {f(top)} Q{f(w1 + 3)} {f((top + bot) / 2)} {f(w1 + 1)} {f(bot)} "
    if arch == "mum" and V["detail"] == "cardigan":
        d += " ".join(f"L{f(x)} {f(y)}" for x, y in reversed(pts_)) + " "
    else:
        d += f"Q0 {f(bot + 9)} {f(-w1 - 1)} {f(bot)} "
    d += f"Q{f(-w1 - 3)} {f((top + bot) / 2)} {f(-w0)} {f(top)} Z"
    defs = clip("sc", f'<path d="{d}"/>')
    body = f'<path d="{d}" fill="{c}"/>'
    inner = ""
    if arch == "mum":
        for k in range(-4, 5):
            inner += line((k * 4.5, top), (k * 8.4, bot + 6), darken(c, 0.3), 1.4, 0.45)
        rr = 0
        for j in range(5):
            for k in range(-4, 5):  # daisy print (a) / polka dots (b)
                x, y = k * 11 + (j % 2) * 5.5, top + 12 + j * 11
                if V["detail"] == "cardigan":
                    inner += circle(x, y, 2.6, V["dress2"], None, op=0.9) + circle(x, y, 1.0, "#ffd23f", None)
                else:
                    inner += circle(x, y, 2.3, V["dress2"], None, op=0.85)
        inner += rect(-w1 - 4, bot - 6, w1 * 2 + 8, 5, V["trim"], None, op=0.9)
    else:
        for k in range(-5, 6):
            inner += line((k * 4.2, top), (k * 6.6, bot + 6), darken(c, 0.3), 1.5, 0.5)
        for j in range(4):
            for k in range(-4, 5):
                inner += circle(k * 9 + (j % 2) * 4.5, top + 14 + j * 11, 1.8, V["skirt2"], None, op=0.8)
        inner += rect(-w1 - 4, bot - 5, w1 * 2 + 8, 5, V["skirt2"], None, op=0.9)
    inner += rect(w0 * 0.3, top, w1, bot - top + 12, "#3a1f2e", None, op=0.14)
    body += group(inner, 'clip-path="url(#sc)"')
    body += path(d, None, OUT, 3)
    return defs, body, (-w1 - 10, top - 8, w1 + 10, bot + 16)


def coat_tails(P, V):
    """the doctor's white coat skirt: two panels parted at the front, over the trousers."""
    hy = -P["hip_y"]
    top = hy - 18
    hw = P["hw"]
    bot = hy + 56
    w1 = hw + 11
    c = V["coat"]
    out = ""
    for sgn in (-1, 1):
        d = (f"M{f(sgn * 3)} {f(top)} L{f(sgn * (hw + 4))} {f(top)} Q{f(sgn * (w1 + 5))} {f((top + bot) / 2)} {f(sgn * (w1 + 3))} {f(bot)} "
             f"Q{f(sgn * (w1 * 0.5))} {f(bot + 6)} {f(sgn * 5)} {f(bot - 1)} Q{f(sgn * 2)} {f((top + bot) / 2)} {f(sgn * 3)} {f(top)} Z")
        out += path(d, c, OUT, 3)
        out += line((sgn * (hw - 4), top + 8), (sgn * (w1 - 2), bot - 2), darken(c, 0.12), 1.6, 0.7)
        out += path(d, "#3a1f2e", None, op=0.0)
        out += f'<path d="M{f(sgn * (hw * 0.3))} {f(top)} L{f(sgn * (hw + 4))} {f(top)} Q{f(sgn * (w1 + 5))} {f((top + bot) / 2)} {f(sgn * (w1 + 3))} {f(bot)} L{f(sgn * w1 * 0.5)} {f(bot + 3)} Z" fill="#3a1f2e" fill-opacity="{0.0 if sgn < 0 else 0.1}"/>'
    out += rect(-hw, top, hw * 2, 6, "#3a1f2e", None, op=0.0)
    return out, (-w1 - 14, top - 8, w1 + 14, bot + 16)


# ---- limbs -------------------------------------------------------------------------------------------------------------------

def _seg_cloth(s, m, aw, cloth, band, hem=True, cap_start=True):
    """A garment sleeve from s to m on top of a limb (outline included)."""
    out = ""
    out += line(s, m, OUT, aw + 5.2, cap="butt")
    if cap_start:
        out += circle(s[0], s[1], aw / 2 + 2.6, OUT)
    out += line(s, m, cloth, aw + 0.8, cap="butt")
    if cap_start:
        out += circle(s[0], s[1], aw / 2 + 0.4, cloth)
    if band:
        dx, dy = m[0] - s[0], m[1] - s[1]
        ln = math.hypot(dx, dy) or 1
        ux, uy = dx / ln, dy / ln
        a = (m[0] - ux * 2.2, m[1] - uy * 2.2)
        out += line(a, m, OUT, aw + 5.2, cap="butt") + line((a[0] + ux * 0.3, a[1] + uy * 0.3), (m[0] - ux * 0.6, m[1] - uy * 0.6), band, aw + 1.4, cap="butt")
    return out


def _shade_lines(a, b, aw, side, color_dark="#3a1f2e"):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    o = aw * 0.26 * side
    o2 = -aw * 0.27 * side
    return (line((a[0] + nx * o, a[1] + ny * o), (b[0] + nx * o, b[1] + ny * o), color_dark, aw * 0.34, 0.16) +
            line((a[0] + nx * o2, a[1] + ny * o2), (b[0] + nx * o2, b[1] + ny * o2), "#ffffff", aw * 0.13, 0.28))


def arm_parts(arch, P, V, J, side):
    name = "l" if side < 0 else "r"
    s = J["shoulder_" + name]
    e = J["elbow_" + name]
    w = C.wrist(P, J, side)
    aw = P["aw"]
    skin = V["skin"]
    out = {}
    cl, fr, band = V["up"]
    full = bool(cl) and fr >= 0.99  # a sleeve down to the elbow: the forearm carries on from it, so no cuff and no round skin cap
    body = line(s, e, OUT, aw + 6, cap="butt") + circle(s[0], s[1], aw / 2 + 3, OUT)
    body += line(s, e, skin, aw, cap="butt" if full else "round")
    if cl and fr > 0:
        m = (s[0] + (e[0] - s[0]) * fr, s[1] + (e[1] - s[1]) * fr)
        body += _seg_cloth(s, m, aw, cl, None if full else band)
        if arch == "dad" and V["detail"] == "plaid":  # rolled sleeve: a plaid stripe and a fat roll
            body += line((s[0] + (e[0] - s[0]) * 0.3, s[1] + (e[1] - s[1]) * 0.3), (s[0] + (e[0] - s[0]) * 0.3, s[1] + (e[1] - s[1]) * 0.3), V["shirt2"], 0)
    body += _shade_lines(s, e, aw, side)
    if arch == "doctor":  # the coat shoulder pad
        body += circle(s[0], s[1], aw / 2 + 1.0, V["up"][0], None, op=0.0)
    out["up"] = (body, bb([s, e], aw / 2 + 10))
    cl, fr, band = V["fore"]
    body = circle(e[0], e[1], aw / 2 + 3, OUT)
    body += line(e, w, OUT, aw + 6, cap="butt") + circle(w[0], w[1], aw / 2 + 3, OUT)
    body += line(e, w, skin, aw, cap="round")
    dx, dy = w[0] - e[0], w[1] - e[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    ux, uy = dx / ln, dy / ln
    if cl and fr > 0:
        m = (e[0] + dx * min(fr, 1.0) * (0.93 if fr >= 1.0 else 1.0), e[1] + dy * min(fr, 1.0) * (0.93 if fr >= 1.0 else 1.0))
        body += _seg_cloth(e, m, aw, cl, band)
    body += _shade_lines(e, w, aw, side)
    hand_c = (w[0] + ux * aw * 0.28, w[1] + uy * aw * 0.28)
    hr = aw * 0.62
    if arch == "nurse" and V["under"]:
        pass
    body += circle(hand_c[0], hand_c[1], hr + 2.6, OUT) + circle(hand_c[0], hand_c[1], hr, skin)
    body += circle(hand_c[0] - nx * side * hr * 0.25, hand_c[1] - ny * side * hr * 0.25, hr * 0.4, lighten(skin, 0.3), None, op=0.6)
    th = (hand_c[0] + nx * side * hr * 0.78 + ux * 1.2, hand_c[1] + ny * side * hr * 0.78 + uy * 1.2)
    body += circle(th[0], th[1], hr * 0.42, skin, OUT, 1.5)  # a thumb so the hand reads as a hand
    if arch == "mum" and name == "r":  # wedding ring
        body += circle(hand_c[0], hand_c[1], hr * 0.2, "#ffd98a", None)
    if arch == "doctor" and name == "l":  # a clipboard held at the side
        pass
    out["fore"] = (body, bb([e, w, hand_c], aw / 2 + 12), (hand_c[0], hand_c[1]))
    return out


def shoe_path(ax, fx, side, rx_, top=13):
    return (f"M{f(ax - rx_ + 2)} {f(-4)} Q{f(ax - rx_)} {f(-top)} {f(ax)} {f(-top)} Q{f(fx + side * rx_)} {f(-top)} {f(fx + side * (rx_ + 3))} {f(-4)} "
            f"Q{f(fx + side * (rx_ + 3))} 1 {f(fx + side * (rx_ - 2))} 1 L{f(ax - rx_ + 4)} 1 Q{f(ax - rx_ - 1)} 0 {f(ax - rx_ + 2)} {f(-4)} Z")


def leg_part(arch, P, V, J, side):
    name = "l" if side < 0 else "r"
    h = J["hip_" + name]
    sh = P["shoe_h"]
    ax = h[0] + side * 2.0
    ay = -sh - 2
    lw = P["lw"]
    skin = V["skin"]
    body = ""
    pts_ = [h, (ax, ay)]
    shoe = None
    kind = "bare"
    if arch == "mum":
        kind = V["leg"]
        shoe = V["shoe"]
    elif arch == "granny":
        kind = "tights"
        shoe = V["shoe"]
    elif arch == "dad":
        kind = "pants"
        shoe = V["shoe"]
    elif arch == "kid":
        kind = V["leg"]
        shoe = V["shoe"]
    elif arch == "nurse":
        kind = "scrubs"
        shoe = V["shoe"]
    elif arch == "doctor":
        kind = "pants"
        shoe = V["shoe"]
    if kind == "bare":
        body += C.capsule(h, (ax, ay), lw, skin, darken(skin, 0.25), lighten(skin, 0.3))
    elif kind == "tights":
        tone = darken(skin, 0.1) if arch == "granny" else "#4a3a5a"
        if arch == "mum":
            tone = "#3b3a52"
        body += C.capsule(h, (ax, ay), lw, tone, darken(tone, 0.3), lighten(tone, 0.25))
    elif kind == "dungaree":
        body += C.capsule(h, (ax, ay - 10), lw, V["denim"], darken(V["denim"], 0.3), lighten(V["denim"], 0.25))
        body += line((ax - lw / 2 - 1, ay - 10), (ax + lw / 2 + 1, ay - 10), V["denim2"], 5, cap="butt")
        body += line((ax - lw / 2 - 2, ay - 10), (ax - lw / 2 - 2, ay - 5), OUT, 2) + line((ax + lw / 2 + 2, ay - 10), (ax + lw / 2 + 2, ay - 5), OUT, 2)
        body += C.capsule((ax, ay - 7), (ax, ay), lw - 1, skin, darken(skin, 0.25), lighten(skin, 0.3), ol=2.4)
    elif kind == "shorts":
        body += C.capsule(h, (ax, ay), lw, skin, darken(skin, 0.25), lighten(skin, 0.3))
        body += line((ax, ay - 14), (ax, ay + 1), "#ffffff", lw + 1.5, cap="butt")
        body += line((ax - lw / 2 - 0.5, ay - 14), (ax + lw / 2 + 0.5, ay - 14), V["shoe"], 3, cap="butt")
        body += line((ax - lw / 2 - 1.3, ay - 14), (ax - lw / 2 - 1.3, ay + 1), OUT, 2.2, cap="butt") + line((ax + lw / 2 + 1.3, ay - 14), (ax + lw / 2 + 1.3, ay + 1), OUT, 2.2, cap="butt")
        body += line((h[0], h[1] + 2), (h[0] + (ax - h[0]) * 0.4, h[1] + 24), V["denim"], lw + 3.2, cap="butt") if False else ""
    else:  # pants / scrubs
        cloth = {"dad": V.get("pants"), "doctor": V.get("pants"), "nurse": V.get("scrub")}[arch]
        wide = lw * (1.15 if arch == "nurse" else 1.0)
        body += C.capsule(h, (ax, ay - 2), wide, cloth, darken(cloth, 0.3), lighten(cloth, 0.25))
        body += line((h[0] + side * lw * 0.3, h[1] + 8), (ax + side * lw * 0.3, ay - 6), darken(cloth, 0.2), 1.4, 0.6)
        if arch == "dad":
            body += line((h[0] - side * lw * 0.34, h[1] + 6), (ax - side * lw * 0.34, ay - 4), lighten(cloth, 0.3), 1.4, 0.7)
            body += line((ax - lw / 2 - 1.5, ay - 5), (ax + lw / 2 + 1.5, ay - 5), lighten(cloth, 0.2), 3.4, cap="butt")
        if arch == "nurse":
            body += line((ax - wide / 2 - 1, ay - 5), (ax + wide / 2 + 1, ay - 5), darken(cloth, 0.2), 3, cap="butt")
    fx = ax + side * 4
    rx_ = 13 if arch != "kid" else 11
    if shoe:
        if arch == "dad" and V["detail"] == "plaid":  # work boots
            body += path(shoe_path(ax, fx, side, rx_ + 1, 17), shoe, OUT, 3)
            body += line((ax - 5, -14), (ax + 5, -14), "#e8d8a0", 1.8) + line((ax - 4, -9), (ax + 4, -9), "#e8d8a0", 1.8)
            body += line((ax - rx_ + 2, -1), (fx + side * (rx_ + 2), -1), "#3a2418", 3.4, cap="butt")
        elif arch == "nurse":  # chunky white clogs with a coloured strap
            body += path(shoe_path(ax, fx, side, rx_, 12), shoe, OUT, 3)
            body += path(f"M{f(ax - 8)} {f(-10)} Q{f(ax)} {f(-16)} {f(ax + 8)} {f(-10)}", None, V["badge"], 3)
            body += line((ax - rx_ + 3, -1.5), (fx + side * (rx_ + 2), -1.5), "#c8d2e0", 3, cap="butt")
            pts_ += [(fx + side * 17, 0), (ax - rx_ - 2, 0)]
        elif arch == "kid":
            body += path(shoe_path(ax, fx, side, rx_, 13), shoe, OUT, 3)
            body += line((ax - rx_ + 3, -2), (fx + side * (rx_ + 2), -2), "#ffffff", 3.4, cap="butt")
            body += path(f"M{f(fx + side * 4)} {f(-12)} Q{f(fx + side * 10)} {f(-9)} {f(fx + side * 11)} {f(-4)}", None, "#ffffff", 2.2, sop=0.9)
            body += line((ax - 3, -11), (ax + 4, -11), V["accent"], 1.8)
        elif arch == "mum" and V["detail"] == "cardigan":  # strappy sandals
            body += path(shoe_path(ax, fx, side, rx_ - 1, 8), shoe, OUT, 2.6)
            body += line((ax - 5, -7), (ax + 5, -7), V["accent"], 2)
        else:
            body += path(shoe_path(ax, fx, side, rx_ - (1 if arch == "granny" else 0), 12 if arch != "granny" else 11), shoe, OUT, 3)
            body += line((ax - rx_ + 3, -1.5), (fx + side * (rx_ + 2), -1.5), darken(shoe, 0.3), 3, cap="butt")
            if arch == "granny":
                body += line((ax - 6, -7), (ax + 6, -7), "#ffe9c4", 1.8)
            if arch == "doctor":
                body += path(f"M{f(ax - 5)} {f(-11)} Q{f(ax + side * 2)} {f(-5)} {f(ax + 8)} {f(-11)}", None, lighten(shoe, 0.3), 1.2, sop=0.7)
        pts_ += [(fx + side * (rx_ + 5), 0), (ax - rx_ - 2, 0)]
    return body, bb(pts_, lw / 2 + 12)


# ---- head ---------------------------------------------------------------------------------------------------------------------

def head_part(arch, P, V):
    rx, ry, cy, ny = P["rx"], P["ry"], P["cy"], P["neck_y"]
    skin = V["skin"]
    d = C.head_path(P)
    defs = clip("hc", f'<path d="{d}"/>') + C.SHADE_GRAD
    body = ""
    body += rect(-7.5, cy + ry * 0.55, 15, ny - (cy + ry * 0.55) + 14, darken(skin, 0.12), OUT, 2.6, rx=3)
    body += rect(-7.5, cy + ry * 0.78, 15, 9, "#3a1f2e", None, op=0.14)
    for side in (-1, 1):
        ex = side * (rx - 1)
        body += ellipse(ex, cy + 2, 4.6, 6.2, skin, OUT, 2.4)
        body += ellipse(ex + side * 0.4, cy + 2.5, 1.8, 3, darken(skin, 0.3), None, op=0.7)
        if arch in ("mum", "nurse", "granny"):
            body += circle(ex + side * 0.5, cy + 8.6, 2.2, "#fffaf0" if arch != "nurse" else V["accent"], OUT, 1)
    body += f'<path d="{d}" fill="{skin}"/>'
    inner = f'<rect x="{f(-rx - 4)}" y="{f(cy - ry * 1.3)}" width="{f(rx * 2 + 8)}" height="{f(ry * 2.5)}" fill="url(#shd)"/>'
    inner += f'<rect x="{f(-rx - 2)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="{RIM_L}" fill-opacity="0.55"/>'
    inner += f'<rect x="{f(rx - 2.5)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="{RIM_R}" fill-opacity="0.4"/>'
    inner += ellipse(-rx * 0.32, cy - ry * 0.45, rx * 0.28, ry * 0.14, lighten(skin, 0.35), None, op=0.45)
    inner += ellipse(-rx * 0.62, cy + ry * 0.35, rx * 0.26, ry * 0.18, "#ff7a8a", None, op=0.22) + ellipse(rx * 0.62, cy + ry * 0.35, rx * 0.26, ry * 0.18, "#ff7a8a", None, op=0.22)
    if arch == "dad" and V.get("beard"):  # a warm stubble beard and a moustache
        hairc = V["hair"]
        inner += path(f"M{f(-rx - 2)} {f(cy + ry * 0.12)} Q{f(-rx * 0.7)} {f(cy + ry * 0.42)} {f(-rx * 0.5)} {f(cy + ry * 0.5)} Q0 {f(cy + ry * 0.34)} {f(rx * 0.5)} {f(cy + ry * 0.5)} "
                      f"Q{f(rx * 0.7)} {f(cy + ry * 0.42)} {f(rx + 2)} {f(cy + ry * 0.12)} L{f(rx + 2)} {f(cy + ry + 6)} L{f(-rx - 2)} {f(cy + ry + 6)} Z", hairc, None, op=0.78)
        inner += path(f"M{f(-rx * 0.45)} {f(cy + ry * 0.5)} Q0 {f(cy + ry * 0.3)} {f(rx * 0.45)} {f(cy + ry * 0.5)} Q0 {f(cy + ry * 0.62)} {f(-rx * 0.45)} {f(cy + ry * 0.5)} Z", skin, None, op=0.0)
    body += group(inner, 'clip-path="url(#hc)"')
    body += path(d, None, OUT, 3)
    return defs, body, (-rx - 14, cy - ry - 8, rx + 14, ny + 18)


def _eye(cx, cy, rx, ry, iris, lashes=False, side=1, look=0.0, lid=None, skin=None, ir=3.3):
    out = ellipse(cx, cy, rx, ry, "#ffffff", OUT, 1.8)
    out += circle(cx + look * 1.5, cy + 0.8, ir, iris)
    out += circle(cx + look * 1.5, cy + 0.8, ir * 0.55, "#2a1b2e")
    out += circle(cx + look * 1.5 + ir * 0.38, cy + 0.8 - ir * 0.42, ir * 0.32, "#ffffff")
    if lid is not None:
        out += path(f"M{f(cx - rx - 0.8)} {f(cy - ry - 1.5)} L{f(cx + rx + 0.8)} {f(cy - ry - 1.5)} L{f(cx + rx + 0.8)} {f(cy - ry + lid)} Q{f(cx)} {f(cy - ry + lid + 2.2)} {f(cx - rx - 0.8)} {f(cy - ry + lid)} Z", skin, OUT, 1.6)
    if lashes:
        for k in range(3):
            ox = side * (rx - 0.5)
            out += line((cx + ox, cy - 1.5), (cx + ox + side * (1.8 + k * 0.5), cy - 4 - k * 1.8), OUT, 1.5)
    return out


def _glasses(kind, color, ex, ey, rx):
    out = ""
    if kind in ("round",) or (isinstance(kind, str) and kind not in ("rect",)):
        col = color
        for sx in (-1, 1):
            out += circle(sx * ex, ey + 0.4, 9.4, "#ffffff", None, op=0.18)
            out += circle(sx * ex, ey + 0.4, 9.4, None, col, 2.6)
            out += line((sx * ex - 5, ey - 5), (sx * ex - 1.5, ey - 7.6), "#ffffff", 1.6, 0.6)
        out += path(f"M{f(-ex + 9.2)} {f(ey - 0.5)} Q0 {f(ey - 3.4)} {f(ex - 9.2)} {f(ey - 0.5)}", None, col, 2.2)
        out += line((-ex - 9.2, ey - 1), (-rx - 3, ey - 2), col, 2.0) + line((ex + 9.2, ey - 1), (rx + 3, ey - 2), col, 2.0)
    else:
        col = color
        for sx in (-1, 1):
            out += rect(sx * ex - 9.6, ey - 7.4, 19.2, 14.6, "#ffffff", None, rx=4, op=0.18)
            out += rect(sx * ex - 9.6, ey - 7.4, 19.2, 14.6, None, col, 2.6, rx=4)
            out += line((sx * ex - 6, ey - 4.6), (sx * ex - 2, ey - 6), "#ffffff", 1.6, 0.6)
        out += line((-ex + 9.6, ey - 3), (ex - 9.6, ey - 3), col, 2.2)
        out += line((-ex - 9.6, ey - 3), (-rx - 3, ey - 3.6), col, 2.0) + line((ex + 9.6, ey - 3), (rx + 3, ey - 3.6), col, 2.0)
    return out


def face_overlay(arch, P, V, expr):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    skin = V["skin"]
    iris = V["iris"]
    ex = rx * 0.43
    ey = cy + {"kid": 5.0, "granny": 3.0}.get(arch, 2.0)
    er = {"kid": 5.9, "granny": 4.8}.get(arch, 5.0)
    erx, ery = er, er * 1.25
    lashes = arch in ("mum",) or (arch == "nurse" and V["style"] == "bun_cap") or (arch == "doctor" and V["style"] == "puff")
    brow_c = {"mum": "#3a1f2e", "dad": V["hair"], "granny": "#a89aa0", "kid": V["hair"], "nurse": "#2a1a22", "doctor": V["hair"] if V["hair"] != "#9a9aa8" else "#6a6a78"}[arch]
    if arch == "dad" and V["hair"] == "#241a1c":
        brow_c = "#241a1c"
    ir = er * 0.68
    body = ""
    blush = "#ff7a8a"
    mouth_y = cy + ry * 0.58
    mc = "#8a2f45"
    if expr == "neutral":
        body += _eye(-ex, ey, erx, ery, iris, lashes, -1, ir=ir) + _eye(ex, ey, erx, ery, iris, lashes, 1, ir=ir)
        by_ = ey - ery - 4.5
        body += line((-ex - 5, by_ + 0.5), (-ex + 5, by_ - 0.6), brow_c, 2.5) + line((ex - 5, by_ - 0.6), (ex + 5, by_ + 0.5), brow_c, 2.5)
        body += path(f"M-5.4 {f(mouth_y)} Q0 {f(mouth_y + 4.2)} 5.4 {f(mouth_y)}", None, mc, 2.3)
    elif expr == "happy":
        body += _eye(-ex, ey, erx, ery * 0.88, iris, lashes, -1, ir=ir) + _eye(ex, ey, erx, ery * 0.88, iris, lashes, 1, ir=ir)
        by_ = ey - ery - 6.2
        body += path(f"M{f(-ex - 5)} {f(by_ + 1.8)} Q{f(-ex)} {f(by_ - 1.6)} {f(-ex + 5)} {f(by_ + 0.8)}", None, brow_c, 2.5)
        body += path(f"M{f(ex - 5)} {f(by_ + 0.8)} Q{f(ex)} {f(by_ - 1.6)} {f(ex + 5)} {f(by_ + 1.8)}", None, brow_c, 2.5)
        body += path(f"M-7.6 {f(mouth_y - 1)} Q0 {f(mouth_y + 10)} 7.6 {f(mouth_y - 1)} Q0 {f(mouth_y + 2.6)} -7.6 {f(mouth_y - 1)} Z", "#7a1f45", OUT, 1.6)
        body += path(f"M-5.9 {f(mouth_y - 0.2)} Q0 {f(mouth_y + 2.8)} 5.9 {f(mouth_y - 0.2)} L5.2 {f(mouth_y + 1.4)} Q0 {f(mouth_y + 3.8)} -5.2 {f(mouth_y + 1.4)} Z", "#ffffff", None)
        body += ellipse(-ex - 3, ey + 8, 4.8, 2.8, blush, None, op=0.45) + ellipse(ex + 3, ey + 8, 4.8, 2.8, blush, None, op=0.45)
        if arch == "granny":
            body += path(f"M{f(-9.4)} {f(mouth_y - 1)} Q-10.5 {f(mouth_y + 3)} -8.4 {f(mouth_y + 5)}", None, darken(skin, 0.3), 1.2, sop=0.8)
            body += path(f"M{f(9.4)} {f(mouth_y - 1)} Q10.5 {f(mouth_y + 3)} 8.4 {f(mouth_y + 5)}", None, darken(skin, 0.3), 1.2, sop=0.8)
    elif expr == "cheer":
        for sx in (-1, 1):
            body += path(f"M{f(sx * ex - 5.4)} {f(ey + 1.6)} Q{f(sx * ex)} {f(ey - 6.8)} {f(sx * ex + 5.4)} {f(ey + 1.6)}", None, "#2a1b2e", 2.9)
        by_ = ey - ery - 8.4
        body += path(f"M{f(-ex - 5.5)} {f(by_ + 2.4)} Q{f(-ex)} {f(by_ - 2.4)} {f(-ex + 5.5)} {f(by_ + 1.2)}", None, brow_c, 2.6)
        body += path(f"M{f(ex - 5.5)} {f(by_ + 1.2)} Q{f(ex)} {f(by_ - 2.4)} {f(ex + 5.5)} {f(by_ + 2.4)}", None, brow_c, 2.6)
        my = mouth_y - 3.2
        body += path(f"M-9.4 {f(my)} L9.4 {f(my)} Q8.4 {f(my + 14.5)} 0 {f(my + 14.5)} Q-8.4 {f(my + 14.5)} -9.4 {f(my)} Z", "#7a1f45", OUT, 2)
        body += path(f"M-8.4 {f(my + 0.8)} L8.4 {f(my + 0.8)} L7.8 {f(my + 4.4)} L-7.8 {f(my + 4.4)} Z", "#ffffff", None)
        body += ellipse(0, my + 11.4, 5, 3.2, "#ff7a9c", None)
        body += ellipse(-ex - 3.5, ey + 8.5, 5.2, 3.1, blush, None, op=0.55) + ellipse(ex + 3.5, ey + 8.5, 5.2, 3.1, blush, None, op=0.55)
    else:  # sad: a gentle, worried look (never scary)
        body += _eye(-ex, ey + 1, erx, ery * 0.9, iris, lashes, -1, look=-0.6, lid=ery * 0.8, skin=skin, ir=ir)
        body += _eye(ex, ey + 1, erx, ery * 0.9, iris, lashes, 1, look=-0.6, lid=ery * 0.8, skin=skin, ir=ir)
        by_ = ey - ery - 3.6
        body += line((-ex - 5.5, by_ + 3.2), (-ex + 4.5, by_ - 2.6), brow_c, 2.6) + line((ex - 4.5, by_ - 2.6), (ex + 5.5, by_ + 3.2), brow_c, 2.6)
        body += path(f"M-5.6 {f(mouth_y + 3.8)} Q0 {f(mouth_y - 2.4)} 5.6 {f(mouth_y + 3.8)}", None, mc, 2.4)
        body += path(f"M{f(rx * 0.72)} {f(cy - ry * 0.35)} Q{f(rx * 0.95)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy + ry * 0.1)} Q{f(rx * 0.5)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy - ry * 0.35)} Z", "#9fe3ff", OUT, 1.4)
    nose_y = cy + ry * 0.3
    body += path(f"M-1.8 {f(nose_y)} Q0.4 {f(nose_y + 3.6)} 2.8 {f(nose_y + 1.8)}", None, darken(skin, 0.42), 1.5, sop=0.85)
    g = V.get("glasses")
    if g:
        col = g if (isinstance(g, str) and g.startswith("#")) else (V["accent"] if arch == "dad" else "#3a3550")
        if arch == "doctor":
            col = "#3a3550" if V["style"] == "mirror" else "#c8473f"
        body += _glasses("rect" if g == "rect" else "round", col, ex, ey, rx)
    if arch == "kid":
        for fx_, fy_ in ((-ex - 2, ey + 6), (-ex + 1.8, ey + 7.2), (ex + 2, ey + 6), (ex - 1.8, ey + 7.2)):
            body += circle(fx_, fy_, 0.9, darken(skin, 0.38), None, op=0.7)
    if arch == "dad" and V.get("beard"):  # a moustache over the stubble
        body += path(f"M-9 {f(mouth_y - 2.4)} Q-4 {f(mouth_y - 8)} 0 {f(mouth_y - 4.4)} Q4 {f(mouth_y - 8)} 9 {f(mouth_y - 2.4)} Q4 {f(mouth_y - 3.6)} 0 {f(mouth_y - 1.4)} Q-4 {f(mouth_y - 3.6)} -9 {f(mouth_y - 2.4)} Z", V["hair"], OUT, 1.2)
    return body, (-rx - 10, cy - ry - 6, rx + 10, cy + ry + 8)


# ---- hair, hats and other extras --------------------------------------------------------------------------------------------

def cap_hair(P, hair, hl, ry_k=1.5, part=0.0, low=0.4):
    """A hair cap over the top of the head with a swept fringe (as in Night One / the underworld)."""
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    fr = (f"M{f(-rx - 3)} {f(cy + ry * low)} C{f(-rx - 5)} {f(cy - ry * ry_k)} {f(rx + 5)} {f(cy - ry * ry_k)} {f(rx + 3)} {f(cy + ry * low)} "
          f"L{f(rx - 3)} {f(cy + 2)} C{f(rx * 0.5)} {f(cy - ry * 0.3)} {f(part + rx * -0.1)} {f(cy - ry * 0.7)} {f(part - rx * 0.5)} {f(cy - ry * 0.5)} "
          f"C{f(-rx * 0.8)} {f(cy - ry * 0.3)} {f(-rx + 2)} {f(cy)} {f(-rx + 3)} {f(cy + ry * low)} Z")
    body = path(fr, hair, OUT, 3)
    body += path(f"M{f(-rx * 0.6)} {f(cy - ry * 1.0)} Q{f(0)} {f(cy - ry * 1.26)} {f(rx * 0.6)} {f(cy - ry * 0.98)}", None, hl, 3, 0.75)
    return body


def hair_parts(arch, P, V):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    out = {"back": None, "front": None, "extra": []}
    hair, hl = V["hair"], V["hair2"]
    if arch == "mum":
        if V["style"] == "long":
            bk = (f"M{f(-rx - 6)} {f(cy)} C{f(-rx - 10)} {f(cy - ry * 1.6)} {f(rx + 10)} {f(cy - ry * 1.6)} {f(rx + 6)} {f(cy)} "
                  f"C{f(rx + 14)} {f(cy + ry)} {f(rx + 14)} {f(cy + ry + 28)} {f(rx + 6)} {f(cy + ry + 40)} "
                  f"Q{f(rx * 0.6)} {f(cy + ry + 30)} {f(rx * 0.1)} {f(cy + ry + 42)} Q{f(-rx * 0.5)} {f(cy + ry + 30)} {f(-rx - 6)} {f(cy + ry + 40)} "
                  f"C{f(-rx - 16)} {f(cy + ry + 28)} {f(-rx - 14)} {f(cy + ry)} {f(-rx - 6)} {f(cy)} Z")
            b = path(bk, hair, OUT, 3)
            b += path(f"M{f(rx + 5)} {f(cy + 6)} Q{f(rx + 11)} {f(cy + ry + 8)} {f(rx + 7)} {f(cy + ry + 30)}", None, hl, 2.6, 0.7)
            b += path(f"M{f(-rx - 5)} {f(cy + 10)} Q{f(-rx - 11)} {f(cy + ry + 8)} {f(-rx - 7)} {f(cy + ry + 28)}", None, hl, 2.2, 0.5)
            out["back"] = (b, (-rx - 30, cy - ry - 14, rx + 30, cy + ry + 54), (0, cy - ry * 0.5), True)
        else:
            b = circle(0, cy - ry - 12, 15, hair, OUT, 3)
            b += path(f"M-9 {f(cy - ry - 14)} Q0 {f(cy - ry - 22)} 9 {f(cy - ry - 12)} Q2 {f(cy - ry - 4)} -6 {f(cy - ry - 8)}", None, hl, 2.2, 0.75)
            b += path(f"M{f(-rx - 3)} {f(cy)} C{f(-rx - 6)} {f(cy - ry * 1.4)} {f(rx + 6)} {f(cy - ry * 1.4)} {f(rx + 3)} {f(cy)} Z", hair, OUT, 3)
            out["back"] = (b, (-rx - 14, cy - ry - 34, rx + 14, cy + 6), (0, cy - ry - 4), True)
        fr = cap_hair(P, hair, hl, 1.5, 0.0, 0.4)
        if V["style"] == "long":
            fr += circle(rx * 0.62, cy - ry * 0.55, 5.4, V["accent"], OUT, 1.6) + circle(rx * 0.62, cy - ry * 0.55, 2, "#ffe27a", None)
            fr += circle(rx * 0.62 + 6, cy - ry * 0.55 + 4, 3.4, V["accent"], OUT, 1.4)
        else:
            hb = f"M{f(-rx - 2)} {f(cy - ry * 0.2)} C{f(-rx * 0.6)} {f(cy - ry * 1.18)} {f(rx * 0.6)} {f(cy - ry * 1.18)} {f(rx + 2)} {f(cy - ry * 0.2)}"
            fr += path(hb, None, OUT, 8.4) + path(hb, None, V["belt"], 5.2) + path(hb, None, lighten(V["belt"], 0.5), 1.4, sop=0.8)
        out["front"] = (fr, (-rx - 12, cy - ry - 22, rx + 14, cy + 8), "", False)
    elif arch == "dad":
        if V["beard"]:
            fr = cap_hair(P, hair, hl, 1.42, -rx * 0.35, 0.34)
            fr += path(f"M{f(-rx * 0.1)} {f(cy - ry * 1.12)} Q{f(rx * 0.5)} {f(cy - ry * 1.5)} {f(rx * 0.95)} {f(cy - ry * 1.26)} Q{f(rx * 0.5)} {f(cy - ry * 1.16)} {f(rx * 0.1)} {f(cy - ry * 1.0)} Z", hair, OUT, 2.4)
        else:
            fr = cap_hair(P, hair, hl, 1.32, 0.0, 0.3)
            fr += path(f"M{f(-rx + 1)} {f(cy - ry * 0.55)} Q0 {f(cy - ry * 0.95)} {f(rx - 1)} {f(cy - ry * 0.55)}", None, hl, 2, 0.5)
        out["front"] = (fr, (-rx - 12, cy - ry - 22, rx + 14, cy + 8), "", False)
    elif arch == "granny":
        b = ""
        for k in range(9):
            a = math.radians(-195 + k * 26)
            b += circle(math.cos(a) * (rx + 4), cy - 3 + math.sin(a) * (ry + 2), 10.5, hair, OUT, 2.6)
        for k in range(9):
            a = math.radians(-195 + k * 26)
            b += circle(math.cos(a) * (rx + 4), cy - 3 + math.sin(a) * (ry + 2), 10.5, hair, None)
        b += circle(0, cy - ry - 11, 13, hair, OUT, 2.8) + circle(0, cy - ry - 11, 13, hair, None)  # the little bun
        b += path(f"M-7 {f(cy - ry - 13)} Q0 {f(cy - ry - 20)} 7 {f(cy - ry - 11)}", None, hl, 2.2, 0.8)
        out["back"] = (b, (-rx - 22, cy - ry - 30, rx + 22, cy + ry * 0.7), None, False)
        fr = ""
        for k in range(7):
            x = -rx * 0.8 + k * rx * 1.6 / 6
            y = cy - ry * 0.72 - math.sin(k / 6 * math.pi) * ry * 0.25 + 4
            fr += circle(x, y, 7.2, hair, OUT, 2.4)
        for k in range(7):
            x = -rx * 0.8 + k * rx * 1.6 / 6
            y = cy - ry * 0.72 - math.sin(k / 6 * math.pi) * ry * 0.25 + 4
            fr += circle(x, y, 7.2, hair, None)
            fr += path(f"M{f(x - 3)} {f(y - 1)} Q{f(x)} {f(y - 4)} {f(x + 3)} {f(y - 1)}", None, hl, 1.4, 0.8)
        out["front"] = (fr, (-rx - 6, cy - ry - 6, rx + 6, cy - ry * 0.2), "", False)
    elif arch == "kid":
        if V["style"] == "pigtails":
            b = ""
            for sgn in (-1, 1):
                root = (sgn * (rx - 2), cy - ry * 0.45)
                tip = (sgn * (rx + 20), cy + ry * 0.95)
                d = (f"M{f(root[0])} {f(root[1] - 6)} C{f(sgn * (rx + 22))} {f(cy - ry * 0.9)} {f(sgn * (rx + 30))} {f(cy + ry * 0.2)} {f(tip[0])} {f(tip[1] + 6)} "
                     f"C{f(sgn * (rx + 10))} {f(cy + ry * 1.0)} {f(sgn * (rx + 2))} {f(cy + ry * 0.4)} {f(root[0])} {f(root[1] + 8)} Z")
                b += path(d, hair, OUT, 3)
                b += path(f"M{f(sgn * (rx + 4))} {f(cy - ry * 0.3)} Q{f(sgn * (rx + 18))} {f(cy + ry * 0.1)} {f(sgn * (rx + 16))} {f(cy + ry * 0.7)}", None, hl, 2.2, 0.6)
                # ribbon
                b += poly([(root[0], root[1] + 2), (root[0] + sgn * 12, root[1] - 6), (root[0] + sgn * 12, root[1] + 10)], V["ribbon"], OUT, 1.8)
                b += poly([(root[0], root[1] + 2), (root[0] - sgn * 7, root[1] - 5), (root[0] - sgn * 7, root[1] + 9)], V["ribbon"], OUT, 1.8)
                b += circle(root[0], root[1] + 2, 3.2, darken(V["ribbon"], 0.2), OUT, 1.4)
            b += path(f"M{f(-rx - 3)} {f(cy)} C{f(-rx - 6)} {f(cy - ry * 1.4)} {f(rx + 6)} {f(cy - ry * 1.4)} {f(rx + 3)} {f(cy)} Z", hair, OUT, 3)
            out["back"] = (b, (-rx - 50, cy - ry - 12, rx + 50, cy + ry * 1.5), (0, cy - ry * 0.5), True)
            fr = cap_hair(P, hair, hl, 1.4, 0.0, 0.34)
            fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 0.62)} L{f(-rx * 0.2)} {f(cy - ry * 0.2)} L{f(rx * 0.1)} {f(cy - ry * 0.6)}", None, OUT, 1.4, sop=0.5)
            out["front"] = (fr, (-rx - 12, cy - ry - 22, rx + 14, cy + 8), "", False)
        else:  # a baseball cap, peak forward
            capc = V["cap"]
            d = f"M{f(-rx - 4)} {f(cy - ry * 0.34)} C{f(-rx - 6)} {f(cy - ry * 1.5)} {f(rx + 6)} {f(cy - ry * 1.5)} {f(rx + 4)} {f(cy - ry * 0.34)} Z"
            fr = path(f"M{f(-rx - 3)} {f(cy - ry * 0.3)} Q{f(-rx - 8)} {f(cy - ry * 0.0)} {f(-rx - 3)} {f(cy + ry * 0.1)} L{f(-rx - 2)} {f(cy - ry * 0.3)} Z", V["hair"], OUT, 2)
            fr += path(f"M{f(rx + 3)} {f(cy - ry * 0.3)} Q{f(rx + 8)} {f(cy - ry * 0.0)} {f(rx + 3)} {f(cy + ry * 0.1)} L{f(rx + 2)} {f(cy - ry * 0.3)} Z", V["hair"], OUT, 2)
            fr += path(d, capc, OUT, 3)
            fr += path(f"M{f(-rx * 0.8)} {f(cy - ry * 0.75)} Q0 {f(cy - ry * 1.25)} {f(rx * 0.8)} {f(cy - ry * 0.75)}", None, lighten(capc, 0.4), 2.6, 0.7)
            for k in (-2, -1, 0, 1, 2):
                fr += line((k * rx * 0.25, cy - ry * 0.36), (k * rx * 0.15, cy - ry * 1.14), darken(capc, 0.3), 1.2, 0.5)
            fr += circle(0, cy - ry * 1.14, 3, lighten(capc, 0.2), OUT, 1.4)
            fr += path(f"M{f(-rx * 1.05)} {f(cy - ry * 0.3)} Q0 {f(cy - ry * 0.02)} {f(rx * 1.05)} {f(cy - ry * 0.3)} Q0 {f(cy - ry * 0.46)} {f(-rx * 1.05)} {f(cy - ry * 0.3)} Z", darken(capc, 0.12), OUT, 2.6)
            fr += star5(0, cy - ry * 0.78, 6.4, "#ffe27a", 1.6)
            out["front"] = (fr, (-rx - 14, cy - ry - 22, rx + 14, cy + 10), "", False)
        # the balloon on a string, tied at the shoulder
        tie = (P["sw"] - 5, P["sh_y"] - 4)
        bc = V["balloon"]
        top = (P["sw"] + 30, P["sh_y"] - 108)
        bl = bez(tie, (tie[0] + 22, tie[1] - 40), (top[0] - 2, top[1] + 22), 14)
        b = path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in bl), None, OUT, 4.2) + path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in bl), None, "#fff1dc", 1.6)
        r_ = 25
        cx_, cy_ = top[0], top[1] - 4
        b += path(f"M{f(cx_)} {f(cy_ + r_ * 1.18)} L{f(cx_ - 5)} {f(cy_ + r_ * 1.18 + 7)} L{f(cx_ + 5)} {f(cy_ + r_ * 1.18 + 7)} Z", darken(bc, 0.12), OUT, 1.8)
        b += path(f"M{f(cx_)} {f(cy_ - r_ * 1.05)} C{f(cx_ + r_ * 1.25)} {f(cy_ - r_ * 1.05)} {f(cx_ + r_ * 1.22)} {f(cy_ + r_ * 1.2)} {f(cx_)} {f(cy_ + r_ * 1.2)} "
                  f"C{f(cx_ - r_ * 1.22)} {f(cy_ + r_ * 1.2)} {f(cx_ - r_ * 1.25)} {f(cy_ - r_ * 1.05)} {f(cx_)} {f(cy_ - r_ * 1.05)} Z", bc, OUT, 3)
        b += ellipse(cx_ - r_ * 0.42, cy_ - r_ * 0.4, r_ * 0.2, r_ * 0.36, "#ffffff", None, op=0.55)
        b += heart(cx_ + 2, cy_ + 2, 6.5, lighten(bc, 0.55), 0.0, None) if False else ""
        out["extra"].append(dict(name="balloon", joint="torso", z=-18, body=b, box=bb(bl + [(cx_ - r_ * 1.4, cy_ - r_ * 1.4), (cx_ + r_ * 1.4, cy_ + r_ * 1.5)], 6), swing=True, pivot_xy=tie))
    elif arch == "nurse":
        if V["style"] == "bun_cap":
            b = circle(0, cy - ry - 9, 13.5, hair, OUT, 3)
            b += path(f"M-8 {f(cy - ry - 11)} Q0 {f(cy - ry - 19)} 8 {f(cy - ry - 9)}", None, hl, 2.2, 0.75)
            b += path(f"M{f(-rx - 3)} {f(cy)} C{f(-rx - 6)} {f(cy - ry * 1.4)} {f(rx + 6)} {f(cy - ry * 1.4)} {f(rx + 3)} {f(cy)} Z", hair, OUT, 3)
            out["back"] = (b, (-rx - 14, cy - ry - 30, rx + 14, cy + 6), (0, cy - ry - 2), True)
            fr = cap_hair(P, hair, hl, 1.4, 0.0, 0.34)
            # the little folded nurse's cap, sitting forward on the hair
            cw = rx * 0.92
            ct = cy - ry * 1.18
            cb = cy - ry * 0.62
            cap = poly([(-cw, cb), (-cw + 4, ct), (cw - 4, ct), (cw, cb), (cw * 0.55, cb + 5), (-cw * 0.55, cb + 5)], V["cap"], OUT, 2.6)
            cap += path(f"M{f(-cw + 3)} {f(ct + 3)} L{f(cw - 3)} {f(ct + 3)}", None, "#e4eaf2", 1.6)
            cap += heart(0, (ct + cb) / 2 + 1, 4.2, V["capmark"], 1.2)
            fr += cap
            out["front"] = (fr, (-rx - 12, cy - ry - 24, rx + 14, cy + 10), "", False)
        else:  # a printed scrub cap with a knot
            cc = V["cap"]
            d = f"M{f(-rx - 4)} {f(cy - ry * 0.12)} C{f(-rx - 8)} {f(cy - ry * 1.66)} {f(rx + 8)} {f(cy - ry * 1.66)} {f(rx + 4)} {f(cy - ry * 0.12)} Q0 {f(cy - ry * 0.62)} {f(-rx - 4)} {f(cy - ry * 0.12)} Z"
            fr = path(d, cc, OUT, 3)
            for k in range(7):
                a = math.radians(205 + k * 21)
                fr += heart(math.cos(a) * rx * 0.88, cy - ry * 0.35 + math.sin(a) * ry * 0.98, 3.0, V["capmark"], 0.0, None)
            fr += path(f"M{f(-rx * 0.84)} {f(cy - ry * 0.52)} Q0 {f(cy - ry * 0.74)} {f(rx * 0.84)} {f(cy - ry * 0.52)}", None, darken(cc, 0.25), 2.2, sop=0.8)
            fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.12)} Q0 {f(cy - ry * 1.3)} {f(rx * 0.5)} {f(cy - ry * 1.1)}", None, lighten(cc, 0.5), 2.4, 0.7)
            fr += path(f"M{f(-rx - 2)} {f(cy - ry * 0.2)} L{f(-rx - 5)} {f(cy + ry * 0.5)} L{f(-rx + 3)} {f(cy + ry * 0.2)} Z", hair, OUT, 2)
            fr += path(f"M{f(rx + 2)} {f(cy - ry * 0.2)} L{f(rx + 5)} {f(cy + ry * 0.5)} L{f(rx - 3)} {f(cy + ry * 0.2)} Z", hair, OUT, 2)
            out["front"] = (fr, (-rx - 14, cy - ry - 26, rx + 14, cy + ry * 0.7), "", False)
    elif arch == "doctor":
        if V["style"] == "mirror":
            fr = cap_hair(P, hair, hl, 1.34, 0.0, 0.3)
            hb = f"M{f(-rx - 3)} {f(cy - ry * 0.52)} Q0 {f(cy - ry * 0.82)} {f(rx + 3)} {f(cy - ry * 0.52)}"
            fr += path(hb, None, OUT, 7.6) + path(hb, None, "#6a6a78", 4.4) + path(hb, None, "#b8b8c8", 1.2, sop=0.8)
            mx, my = 0, cy - ry * 0.74
            fr += circle(mx, my, 10.6, "#8a8a98", OUT, 2.4) + circle(mx, my, 8.0, "#e4f0ff", OUT, 1.4) + circle(mx, my, 2.6, "#5a6a88", OUT, 1.2)
            fr += path(f"M{f(mx - 5.8)} {f(my - 1)} Q{f(mx - 3)} {f(my - 5.4)} {f(mx + 1)} {f(my - 6)}", None, "#ffffff", 1.8, 0.9)
            out["front"] = (fr, (-rx - 12, cy - ry - 22, rx + 14, cy + 8), "", False)
        else:  # a big round curly puff with a coloured headband
            b = ""
            for k in range(11):
                a = math.radians(-200 + k * 22)
                b += circle(math.cos(a) * (rx + 7), cy - 6 + math.sin(a) * (ry + 6), 12.5, hair, OUT, 2.8)
            for k in range(11):
                a = math.radians(-200 + k * 22)
                b += circle(math.cos(a) * (rx + 7), cy - 6 + math.sin(a) * (ry + 6), 12.5, hair, None)
            b += circle(0, cy - 8, ry + 2, hair, None)
            for k in range(5):
                a = math.radians(-180 + k * 36)
                b += path(f"M{f(math.cos(a) * (rx + 3) - 3)} {f(cy - 6 + math.sin(a) * (ry + 3))} q3 -4 6 0", None, V["hair2"], 1.6, 0.8)
            out["back"] = (b, (-rx - 30, cy - ry - 30, rx + 30, cy + ry * 0.9), None, False)
            hb = f"M{f(-rx - 2)} {f(cy - ry * 0.46)} Q0 {f(cy - ry * 0.78)} {f(rx + 2)} {f(cy - ry * 0.46)}"
            fr = path(f"M{f(-rx - 3)} {f(cy + ry * 0.2)} C{f(-rx - 5)} {f(cy - ry * 1.3)} {f(rx + 5)} {f(cy - ry * 1.3)} {f(rx + 3)} {f(cy + ry * 0.2)} L{f(rx - 3)} {f(cy - 2)} C{f(rx * 0.5)} {f(cy - ry * 0.45)} {f(-rx * 0.5)} {f(cy - ry * 0.45)} {f(-rx + 3)} {f(cy - 2)} Z", hair, OUT, 3)
            fr += path(hb, None, OUT, 8.4) + path(hb, None, V["accent"], 5.2) + path(hb, None, lighten(V["accent"], 0.5), 1.4, sop=0.8)
            for k in range(-2, 3):
                fr += circle(k * rx * 0.36, cy - ry * 1.06 + abs(k) * 2.5, 6.2, hair, OUT, 2)
            for k in range(-2, 3):
                fr += circle(k * rx * 0.36, cy - ry * 1.06 + abs(k) * 2.5, 6.2, hair, None)
            out["front"] = (fr, (-rx - 12, cy - ry - 26, rx + 14, cy + 8), "", False)
    return out


# ---- assembly ------------------------------------------------------------------------------------------------------------------

def build_variant(arch, variant):
    P = ARCH[arch]
    V = VARIANTS[arch][variant]
    J = C.skeleton(P)
    base = f"chars/{arch}_{variant}/"
    parts = []

    def emit(name, joint, z, body, box, defs="", swing=False, pivot_xy=None):
        info = write_svg(base + name + ".svg", box, body, defs)
        pv = pivot_in(info, J[joint])
        e = {"name": name, "joint": joint, "z": z, "file": f"source/{base}{name}.svg", "pivot": pv, "px_scale": 0.5}
        if swing:
            e["swing"] = True
            e["swing_pivot"] = pivot_in(info, pivot_xy) if pivot_xy else pv
        parts.append(e)

    hair = hair_parts(arch, P, V)
    if hair["back"]:
        body, box, pv, sw_ = hair["back"]
        emit("hair_back", "head", -20, body, box, swing=sw_, pivot_xy=pv if (sw_ and pv) else None)
    for ex in hair["extra"]:
        emit(ex["name"], ex["joint"], ex["z"], ex["body"], ex["box"], swing=ex["swing"], pivot_xy=ex.get("pivot_xy"))
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        body, box = leg_part(arch, P, V, J, side)
        emit(f"leg_{n}", f"hip_{n}", -10, body, box)
    pel = pelvis_part(arch, P, V)
    if pel:
        emit("pelvis", "hips", -5, pel[0], pel[1])
    defs, body, box = torso_part(arch, P, V)
    emit("torso", "torso", 0, body, box, defs)
    if arch in ("mum", "granny"):
        defs, body, box = skirt_part(arch, P, V)
        emit("skirt", "hips", 2, body, box, defs)
    if arch == "doctor":
        body, box = coat_tails(P, V)
        emit("coat_tails", "hips", 2, body, box)
    arms = {}
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        a = arm_parts(arch, P, V, J, side)
        arms[n] = a
        emit(f"arm_{n}_up", f"shoulder_{n}", 5, a["up"][0], a["up"][1])
        emit(f"arm_{n}_fore", f"elbow_{n}", 4, a["fore"][0], a["fore"][1])
    defs, body, box = head_part(arch, P, V)
    emit("head", "head", 10, body, box, defs)
    faces = {}
    for ex in EXPRESSIONS:
        body, box = face_overlay(arch, P, V, ex)
        info = write_svg(f"{base}face_{ex}.svg", box, body)
        faces[ex] = {"file": f"source/{base}face_{ex}.svg", "pivot": pivot_in(info, J["head"]), "px_scale": 0.5}
    if hair["front"]:
        body, box = hair["front"][0], hair["front"][1]
        fdefs = hair["front"][2] if len(hair["front"]) > 2 else ""
        emit("hair_front", "head", 20, body, box, fdefs)
    fb = arms["r"]["fore"][1]
    hand = arms["r"]["fore"][2]
    hand_px = [round((hand[0] - math.floor(fb[0])) * 2, 1), round((hand[1] - math.floor(fb[1])) * 2, 1)]
    fbl = arms["l"]["fore"][1]
    handl = arms["l"]["fore"][2]
    hand_px_l = [round((handl[0] - math.floor(fbl[0])) * 2, 1), round((handl[1] - math.floor(fbl[1])) * 2, 1)]
    return {"parts": parts, "faces": faces, "face_z": 12,
            "glow_hand": {"joint": "elbow_r", "at": hand_px, "joint_l": "elbow_l", "at_l": hand_px_l}}


TOP_EXTRA = {"mum": 14, "dad": 12, "granny": 26, "kid": 14, "nurse": 24, "doctor": 20}


def build_all():
    out = {}
    for arch in ARCH:
        P = ARCH[arch]
        J = C.skeleton(P)
        entry = {"height": int(-(P["cy"] - P["ry"] - TOP_EXTRA[arch])),
                 "joints": {k: [round(v[0], 1), round(v[1], 1)] for k, v in J.items()}, "variants": {}}
        for variant in VARIANTS[arch]:
            entry["variants"][variant] = build_variant(arch, variant)
        out[arch] = entry
    return out
