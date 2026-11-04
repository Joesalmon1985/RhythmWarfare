"""The six ward-dwellers of the Mental Hospital chapter: affectionately drawn eccentrics in fancy dress.

Archetypes: pirate, king (paper crown + dressing gown), chef, superhero (towel cape), ballerina, orderly (calm, friendly staff).
Variants a and b differ in palette and a costume detail. Same rig/face contract as Night One (chars.py): parts are drawn at the
rest pose in rig space (origin between the feet, +y down), swinging extras (bandana tails, feather, towel cape, bun) are parts with
`swing: true` and a `swing_pivot`. Tone: kind and whimsical; nobody is menacing or ridiculed, the costumes are homemade fancy dress.
"""
from __future__ import annotations

import math

from . import chars as C
from .lib import (OUT, capsule, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly,
                  rect, write_svg)

RIM_L, RIM_R = "#8fe8d2", "#ffb89a"  # fluorescent mint from the left, a warm party-light peach from the right
INK = "#2a1b3e"
EXPRESSIONS = C.EXPRESSIONS

SKIN = {"pale": "#fbd9c0", "tan": "#e6aa7a", "brown": "#b67a52", "deep": "#8a5233", "dark": "#68402a", "olive": "#d9a273",
        "rosy": "#f5c4a8"}

ARCH = {
    "pirate": dict(hip_y=100, sh_y=-180, sh_dx=31, neck_y=-189, cy=-215, rx=25, ry=29, up=40, fore=41, aw=15, sw=30, ww=25, hw=26,
                   lw=16, leg_dx=12, shoe_h=14),
    "king": dict(hip_y=88, sh_y=-170, sh_dx=34, neck_y=-179, cy=-203, rx=26, ry=29, up=36, fore=37, aw=16, sw=34, ww=33, hw=32,
                 lw=14, leg_dx=12, shoe_h=11),
    "chef": dict(hip_y=96, sh_y=-176, sh_dx=36, neck_y=-185, cy=-210, rx=27, ry=29, up=38, fore=39, aw=17, sw=36, ww=41, hw=33,
                 lw=16, leg_dx=13, shoe_h=11),
    "superhero": dict(hip_y=110, sh_y=-192, sh_dx=32, neck_y=-201, cy=-228, rx=24, ry=28, up=43, fore=45, aw=15, sw=33, ww=22,
                      hw=24, lw=16, leg_dx=12, shoe_h=18),
    "ballerina": dict(hip_y=104, sh_y=-184, sh_dx=23, neck_y=-193, cy=-219, rx=24, ry=29, up=38, fore=41, aw=11, sw=22, ww=14,
                      hw=17, lw=11, leg_dx=9, shoe_h=8),
    "orderly": dict(hip_y=108, sh_y=-188, sh_dx=31, neck_y=-197, cy=-224, rx=24, ry=28, up=42, fore=44, aw=15, sw=32, ww=26,
                    hw=26, lw=17, leg_dx=12, shoe_h=12),
}
TOP_EXTRA = {"pirate": 34, "king": 36, "chef": 72, "superhero": 24, "ballerina": 34, "orderly": 14}

VARIANTS = {
    "pirate": {
        "a": dict(skin=SKIN["tan"], hair="#5a3320", cloth="#f4efe0", cloth2="#2c3f7a", trousers="#2b2f55", boots="#3a2a2a", cuff="#8a5a34",
                  sash="#d6354a", accent="#ffc23f", hat="#2a2440", detail="tricorn", beard="#5a3320", patch="left"),
        "b": dict(skin=SKIN["pale"], hair="#1e1a2e", cloth="#fffaf0", cloth2="#fffaf0", trousers="#6a4a3a", boots="#4a3426", cuff="#c7954f",
                  sash="#ffb23f", accent="#ffffff", hat="#d6354a", detail="bandana", beard=None, patch="right", vest="#7a4a2a"),
    },
    "king": {
        "a": dict(skin=SKIN["rosy"], hair="#f2f0f8", cloth="#7a3c9a", cloth2="#fbf7ee", trousers="#bfe0ee", slipper="#ff9ac0", accent="#ffd23f",
                  crown="#ffd23f", gem="#e03a5a", detail="plum", beard="#f2f0f8"),
        "b": dict(skin=SKIN["tan"], hair="#b9b4c6", cloth="#2a9a94", cloth2="#fffaf0", trousers="#f3d9e6", slipper="#8a7ad0", accent="#ff7a8a",
                  crown="#e8c15a", gem="#3a86ff", detail="ermine", beard=None, mous="#b9b4c6"),
    },
    "chef": {
        "a": dict(skin=SKIN["olive"], hair="#2a1f28", cloth="#fdfdf8", cloth2="#fdfdf8", trousers="#3a3f66", shoes="#f4f0ff", accent="#3a6ad0",
                  hat="#ffffff", detail="classic", mous="#2a1f28"),
        "b": dict(skin=SKIN["brown"], hair="#1f1a24", cloth="#fffaf4", cloth2="#fffaf4", trousers="#4a7a6a", shoes="#ffd27a", accent="#e0453a",
                  hat="#fffaf0", detail="apron", apron="#3a8ad0", mous=None),
    },
    "superhero": {
        "a": dict(skin=SKIN["pale"], hair="#6a3a22", cloth="#3b86ff", cloth2="#ffd23f", trousers="#3a6ad0", boots="#e0364a", accent="#e0364a",
                  cape="#ff9a2e", cape2="#fff2c8", mask="#e0364a", glove="#ffd23f", detail="star"),
        "b": dict(skin=SKIN["deep"], hair="#1f1730", cloth="#e0364a", cloth2="#ffd23f", trousers="#a8203a", boots="#ffd23f", accent="#3b86ff",
                  cape="#3b86ff", cape2="#d6ecff", mask="#ffd23f", glove="#ff8ac0", detail="bolt"),
    },
    "ballerina": {
        "a": dict(skin=SKIN["pale"], hair="#f2c24a", cloth="#ff9ac8", cloth2="#ffd6ea", trousers="#ffc4d6", shoes="#ffb0cf", accent="#ffffff",
                  tiara="#d9ecff", detail="pink"),
        "b": dict(skin=SKIN["brown"], hair="#2a1a2a", cloth="#a98aef", cloth2="#e4d8ff", trousers="#e8c9e6", shoes="#d9c4ff", accent="#ffd23f",
                  tiara="#ffe08a", detail="lilac"),
    },
    "orderly": {
        "a": dict(skin=SKIN["dark"], hair="#1d1620", cloth="#2fb5a8", cloth2="#eafaf6", trousers="#2a9a90", shoes="#ffffff", accent="#ff9a5a",
                  detail="glasses"),
        "b": dict(skin=SKIN["tan"], hair="#5a4a42", cloth="#9a86e0", cloth2="#f1ecff", trousers="#8470c8", shoes="#f4f0ff", accent="#2fd0b8",
                  detail="beard", beard="#4a3a34"),
    },
}


def bb(points, pad=8.0):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ---- torso ---------------------------------------------------------------------------------------------------------------

def torso_wrap(P, base, inner, outer="", flare=0.0):
    sw = P["sw"]
    ts = P["sh_y"] - 8
    by = -P["hip_y"] + 14
    d = C.torso_outline(P, flare)
    defs = clip("tc", f'<path d="{d}"/>') + C.SHADE_GRAD
    body = f'<path d="{d}" fill="{base}"/>' + group(inner, 'clip-path="url(#tc)"')
    shade = f'<rect x="{f(-sw - 8)}" y="{f(ts - 6)}" width="{f(sw * 2 + 16)}" height="{f(by - ts + 12)}" fill="url(#shd)"/>'
    rim_l = f'<rect x="{f(-sw - 3)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="{RIM_L}" fill-opacity="0.5"/>'
    rim_r = f'<rect x="{f(sw - 2)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="{RIM_R}" fill-opacity="0.38"/>'
    body += group(shade + rim_l + rim_r, 'clip-path="url(#tc)"')
    body += path(d, None, OUT, 3)
    body += outer
    return defs, body, (-sw - 30, ts - 24, sw + 30, by + 26)


def button(x, y, r=2.2, c="#ffffff"):
    return circle(x, y, r, c, OUT, 1.1)


def torso_part(arch, P, V):
    sw, ww, hw = P["sw"], P["ww"], P["hw"]
    ts = P["sh_y"] - 8
    wy = -P["hip_y"] - 34
    by = -P["hip_y"] + 14
    skin, cl, cl2, acc = V["skin"], V["cloth"], V["cloth2"], V["accent"]
    inner, outer, base, flare = "", "", cl, 0.0
    if arch == "pirate":
        flare = 1
        if V["detail"] == "tricorn":  # breton stripes
            for k in range(9):
                inner += rect(-sw - 4, ts + 8 + k * 12, sw * 2 + 8, 5.4, cl2, None, op=0.95)
        else:  # billowy poet shirt with a leather waistcoat
            for k in (-1, 1):
                inner += path(f"M{f(k * 6)} {f(ts + 12)} Q{f(k * 16)} {f(ts + 44)} {f(k * 10)} {f(by - 30)}", None, darken(cl, 0.16), 2.0, sop=0.7)
            vl = [(-sw - 3, ts - 4), (-9, ts - 4), (-4, ts + 34), (-hw - 5, by - 4), (-sw - 3, by - 4)]
            vr = [(sw + 3, ts - 4), (9, ts - 4), (4, ts + 34), (hw + 5, by - 4), (sw + 3, by - 4)]
            inner += poly(vl, V["vest"], OUT, 2.4) + poly(vr, V["vest"], OUT, 2.4)
            for k in range(4):
                inner += line((-8 + k * 0.5, ts + 8 + k * 10), (8 - k * 0.5, ts + 10 + k * 10), lighten(V["vest"], 0.35), 1.4)
        inner += poly([(-9, ts - 4), (9, ts - 4), (0, ts + 24)], skin, OUT, 2)  # open laced collar
        for k in range(3):
            inner += line((-3.4 + k * 0.4, ts + 6 + k * 6), (3.4 - k * 0.4, ts + 6 + k * 6), V["cuff"], 1.4)
        inner += rect(-hw - 6, by - 26, hw * 2 + 12, 15, V["sash"], OUT, 2.2)  # the sash
        inner += line((-hw - 4, by - 22), (hw + 4, by - 22), lighten(V["sash"], 0.3), 1.4, 0.7)
        inner += rect(-hw - 6, by - 14, hw * 2 + 12, 5, "#3a2a2a", OUT, 1.8) + rect(-5, by - 14.5, 10, 6, acc, OUT, 1.4)
    elif arch == "king":  # dressing gown with a shawl collar
        flare = 3
        inner += poly([(-14, ts - 4), (14, ts - 4), (0, ts + 36)], V["trousers"], OUT, 2)  # pyjama top showing
        for k in range(4):
            inner += line((-8 + k * 0.4, ts + 4 + k * 8), (8 - k * 0.4, ts + 4 + k * 8), lighten(V["trousers"], 0.3), 1.6, 0.9)
        gown = darken(cl, 0.04)
        inner += poly([(-sw - 3, ts - 4), (-12, ts - 4), (-2, by + 4), (-hw - 7, by + 4)], gown, OUT, 2.4)
        inner += poly([(sw + 3, ts - 4), (12, ts - 4), (2, by + 4), (hw + 7, by + 4)], gown, OUT, 2.4)
        coll = cl2
        left = [(-12, ts - 6), (-22, ts - 2), (-12, ts + 22), (-6, by - 40), (-1, by - 40), (-3, ts + 34)]
        inner += poly([(-13, ts - 6), (-24, ts), (-13, ts + 22), (-6, by - 20), (0, by - 20), (-1, ts + 26)], coll, OUT, 2.2)
        inner += poly([(13, ts - 6), (24, ts), (13, ts + 22), (6, by - 20), (0, by - 20), (1, ts + 26)], coll, OUT, 2.2)
        if V["detail"] == "ermine":  # paper ermine tails
            for k in range(5):
                for sg in (-1, 1):
                    inner += poly([(sg * (14 - k * 1.6), ts + 4 + k * 11), (sg * (14 - k * 1.6) + sg * 2.2, ts + 12 + k * 11), (sg * (14 - k * 1.6) - sg * 2.2, ts + 12 + k * 11)], "#2a2440", None)
        else:
            for k in range(7):  # terry towelling loops
                for sg in (-1, 1):
                    inner += circle(sg * (13 - k * 1.1), ts + 2 + k * 8, 1.2, darken(coll, 0.12), None, op=0.7)
        inner += rect(-hw - 8, by - 26, hw * 2 + 16, 8, acc, OUT, 2, rx=3)  # tied cord
        inner += circle(8, by - 22, 4, acc, OUT, 1.8)
        inner += path(f"M8 {f(by - 19)} L5 {f(by - 2)} M8 {f(by - 19)} L12 {f(by - 2)}", None, OUT, 4.2) + path(f"M8 {f(by - 19)} L5 {f(by - 2)} M8 {f(by - 19)} L12 {f(by - 2)}", None, acc, 2.4)
        inner += rect(sw - 18, by - 52, 15, 15, darken(gown, 0.14), OUT, 1.8, rx=2)  # pocket
    elif arch == "chef":  # double-breasted whites over a round tummy: a wrap panel, two rows of buttons, a mandarin collar
        flare = 3
        inner += poly([(-ww - 6, ts - 4), (ww + 6, ts - 4), (ww + 6, by + 4), (-ww - 6, by + 4)], cl, None)
        inner += ellipse(-ww * 0.42, wy - 6, ww * 0.5, 30, "#ffffff", None, op=0.5)  # the light on the tummy
        inner += path(f"M{f(ww * 0.15)} {f(ts + 2)} Q{f(ww * 0.32)} {f(wy - 10)} {f(ww * 0.42)} {f(by + 6)}", None, "#cfcbe0", 2.4)  # the wrap edge
        inner += poly([(ww * 0.15, ts + 2), (ww * 0.42, by + 6), (ww + 6, by + 6), (ww + 6, ts - 4)], "#e8e6f2", None, op=0.55)
        inner += path(f"M{f(-ww - 4)} {f(wy + 6)} Q0 {f(wy + 14)} {f(ww + 4)} {f(wy + 6)}", None, "#d8d4e8", 1.8, sop=0.9)  # where the jacket folds at the belt line
        for k in range(4):
            for sg in (-1, 1):
                inner += button(sg * 10 - 2, ts + 16 + k * 12.5, 2.8, "#cfcbe0")
        inner += rect(-sw + 6, ts + 20, 13, 3, "#cfcbe0", None)  # the sleeve-pocket line and a pen
        inner += line((-sw + 10, ts + 14), (-sw + 10, ts + 22), "#3a6ad0", 2.2)
        if V["detail"] == "apron":
            ap = V["apron"]
            inner += poly([(-ww + 3, wy + 2), (ww - 3, wy + 2), (hw + 6, by + 4), (-hw - 6, by + 4)], ap, OUT, 2.4)
            inner += rect(-15, by - 28, 30, 4, "#ffffff", None, op=0.9)
            inner += rect(-17, by - 30, 12, 15, lighten(ap, 0.18), OUT, 1.6, rx=2) + rect(5, by - 30, 12, 15, lighten(ap, 0.18), OUT, 1.6, rx=2)
            inner += line((-ww + 3, wy + 2), (-sw + 6, ts + 6), ap, 3) + line((ww - 3, wy + 2), (sw - 6, ts + 6), ap, 3)
        # mandarin collar and neckerchief
        inner += rect(-14, ts - 6, 28, 8, "#f4f2fa", OUT, 1.8, rx=3)
        inner += poly([(-11, ts + 1), (11, ts + 1), (0, ts + 16)], acc, OUT, 2.0) + circle(0, ts + 3, 3.4, darken(acc, 0.1), OUT, 1.4)
        if V["detail"] == "classic":
            inner += path(f"M{f(-sw + 2)} {f(by - 14)} L{f(sw - 2)} {f(by - 14)}", None, acc, 0)
            for sg in (-1, 1):
                inner += line((sg * (sw + 2), ts + 6), (sg * (sw - 3), ts + 6), acc, 2.4)
    elif arch == "superhero":  # pyjama top with a big emblem and a bold belt
        inner += rect(-sw - 4, ts + 36, sw * 2 + 8, 4, darken(cl, 0.12), None, op=0.5)
        cx_, cy_ = 0, ts + 26
        if V["detail"] == "star":
            pts_ = [(cx_ + math.cos(math.radians(-90 + k * 36)) * (15 if k % 2 == 0 else 6.5), cy_ + math.sin(math.radians(-90 + k * 36)) * (15 if k % 2 == 0 else 6.5)) for k in range(10)]
            inner += circle(cx_, cy_, 17, V["cloth2"], OUT, 2.4) + poly(pts_, V["accent"], OUT, 1.6)
        else:
            inner += poly([(cx_, cy_ - 18), (cx_ + 17, cy_), (cx_, cy_ + 18), (cx_ - 17, cy_)], V["cloth2"], OUT, 2.4)
            inner += poly([(cx_ + 3, cy_ - 13), (cx_ - 7, cy_ + 2), (cx_ - 1, cy_ + 2), (cx_ - 4, cy_ + 13), (cx_ + 7, cy_ - 3), (cx_ + 1, cy_ - 3)], V["accent"], OUT, 1.4)
        inner += rect(-hw - 4, by - 18, hw * 2 + 8, 9, V["accent"], OUT, 2.2, rx=1)
        inner += rect(-8, by - 19, 16, 11, V["cloth2"], OUT, 2, rx=2)
        inner += poly([(-9, ts - 4), (9, ts - 4), (0, ts + 8)], skin, OUT, 1.8)  # collar
        outer += circle(-8, ts + 2, 3.4, V["cloth2"], OUT, 1.6) + circle(8, ts + 2, 3.4, V["cloth2"], OUT, 1.6)  # towel knot at the neck
    elif arch == "ballerina":  # leotard, sweetheart neckline, ribbon waist
        base = skin
        inner += rect(-sw - 4, ts + 20, sw * 2 + 8, by - ts, cl, None)
        inner += path(f"M{f(-sw - 4)} {f(ts + 16)} L{f(-sw - 4)} {f(ts + 22)} Q-12 {f(ts + 30)} 0 {f(ts + 22)} Q12 {f(ts + 30)} {f(sw + 4)} {f(ts + 22)} L{f(sw + 4)} {f(ts + 16)} L{f(sw - 4)} {f(ts - 4)} L{f(sw - 6)} {f(ts - 4)} Q0 {f(ts + 12)} {f(-sw + 6)} {f(ts - 4)} L{f(-sw + 4)} {f(ts - 4)} Z", cl, None)
        inner += rect(-ww - 8, ts + 20, ww * 2 + 16, by - ts, cl, None)
        for sg in (-1, 1):  # straps
            inner += line((sg * 10, ts + 2), (sg * 11, ts + 24), cl, 3.6)
        inner += path(f"M-10 {f(ts + 22)} Q-5 {f(ts + 30)} 0 {f(ts + 23)} Q5 {f(ts + 30)} 10 {f(ts + 22)}", None, darken(cl, 0.2), 1.6, sop=0.8)
        if V["detail"] == "lilac":
            for k in range(7):
                inner += circle(-12 + (k % 4) * 8, ts + 38 + (k // 4) * 11, 1.4, V["accent"], None)
        inner += rect(-ww - 3, wy + 4, ww * 2 + 6, 6, V["cloth2"], OUT, 1.6, rx=2)
    elif arch == "orderly":  # scrubs: V neck with contrast trim, chest pocket, lanyard and badge
        inner += poly([(-14, ts - 4), (14, ts - 4), (0, ts + 26)], skin, OUT, 2)
        inner += path(f"M-14 {f(ts - 3)} L0 {f(ts + 26)} L14 {f(ts - 3)}", None, cl2, 3.2)
        inner += rect(-sw + 3, ts + 32, 17, 17, darken(cl, 0.1), OUT, 1.8, rx=2)
        inner += line((-sw + 8, ts + 30), (-sw + 8, ts + 38), "#2a6ad0", 2.0) + line((-sw + 12, ts + 30), (-sw + 12.4, ts + 38), "#e0453a", 2.0)
        inner += rect(-hw - 4, by - 18, hw * 2 + 8, 5, darken(cl, 0.18), None, op=0.6)
        for sg in (-1, 1):
            inner += line((sg * 9, ts - 3), (sg * 4, ts + 40), acc, 2.6)
        inner += rect(-7, ts + 38, 14, 18, "#ffffff", OUT, 1.8, rx=2.5) + circle(0, ts + 45, 3.4, SKIN["tan"], None) + rect(-4.5, ts + 50, 9, 2.4, acc, None)
        inner += rect(-2.5, ts + 36, 5, 3, "#9a9ab0", OUT, 1.0)
    return torso_wrap(P, base, inner, outer, flare)


def pelvis_part(arch, P, V):
    hy = -P["hip_y"]
    hw = P["hw"] + 1
    cloth = {"pirate": V["trousers"], "king": V["trousers"], "chef": V["trousers"], "orderly": V["trousers"],
             "superhero": V["trousers"], "ballerina": V["cloth"]}[arch]
    d = f"M{f(-hw)} {f(hy - 12)} L{f(hw)} {f(hy - 12)} L{f(hw + 1)} {f(hy + 12)} Q0 {f(hy + 22)} {f(-hw - 1)} {f(hy + 12)} Z"
    body = path(d, cloth, OUT, 3)
    body += line((-hw + 2, hy - 8), (hw - 2, hy - 8), darken(cloth, 0.3), 3, 0.7)
    if arch == "superhero":  # bold trunks over the leggings
        tr = V["accent"]
        body = path(f"M{f(-hw - 2)} {f(hy - 12)} L{f(hw + 2)} {f(hy - 12)} L{f(hw + 6)} {f(hy + 16)} L{f(2)} {f(hy + 20)} L0 {f(hy + 8)} L{f(-2)} {f(hy + 20)} L{f(-hw - 6)} {f(hy + 16)} Z", tr, OUT, 3)
        body += line((-hw - 1, hy + 12), (-4, hy + 15), darken(tr, 0.3), 1.6, 0.7) + line((hw + 1, hy + 12), (4, hy + 15), darken(tr, 0.3), 1.6, 0.7)
    elif arch == "pirate":
        body += line((0, hy - 8), (0, hy + 12), darken(cloth, 0.4), 2, 0.6)
    elif arch == "chef":
        for k in range(-3, 4):
            body += line((k * 7, hy - 10), (k * 7, hy + 14), "#ffffff", 2.2, 0.55)
        body += line((-hw, hy + 2), (hw, hy + 2), "#ffffff", 2.2, 0.55)
    return body, (-hw - 12, hy - 18, hw + 12, hy + 30)


def skirt_part(arch, P, V):
    """Hip-level overlay: the ballerina's tutu, the king's gown flaps, the pirate's sash tail and the chef-b apron skirt."""
    hy = -P["hip_y"]
    hw = P["hw"]
    top = hy - 16
    if arch == "ballerina":
        c1, c2 = V["cloth2"], V["cloth"]
        w1 = hw + 44
        bot = hy + 22
        defs = ""
        body = ""
        for layer_i, (wd, yb, col, ph) in enumerate(((w1, bot + 4, lighten(c2, 0.35), 0), (w1 - 8, bot - 2, c1, 1), (w1 - 16, bot - 8, lighten(c1, 0.35), 0))):
            n = 7
            hem = []
            for k in range(n + 1):
                x = -wd + k * (2 * wd / n)
                hem.append((x, yb + (6 if (k + ph) % 2 == 0 else -1)))
            d = f"M{f(-hw + 1)} {f(top)} L{f(hw - 1)} {f(top)} Q{f(wd * 0.7)} {f(top + 2)} {f(wd + 2)} {f(yb - 4)} " + " ".join(f"L{f(x)} {f(y)}" for x, y in reversed(hem)) + f" Q{f(-wd * 0.7)} {f(top + 2)} {f(-hw + 1)} {f(top)} Z"
            body += path(d, col, OUT, 2.6)
            for k in range(-4, 5):
                body += line((k * 3.2, top + 3), (k * wd / 4.2, yb - 3), darken(col, 0.22), 1.1, 0.5)
        body += rect(-hw - 2, top - 3, hw * 2 + 4, 8, V["cloth"], OUT, 2, rx=2)
        body += circle(0, top + 1, 3.4, V["accent"], OUT, 1.4)
        return defs, body, (-w1 - 10, top - 10, w1 + 10, bot + 18)
    if arch == "king":  # two gown flaps hanging to the knee with a gap between, showing pyjama legs
        c = darken(V["cloth"], 0.03)
        bot = hy + 52
        w1 = hw + 15
        defs = ""
        body = ""
        for sg in (-1, 1):
            d = f"M{f(sg * 2)} {f(top)} L{f(sg * (hw + 5))} {f(top)} Q{f(sg * (w1 + 2))} {f((top + bot) / 2)} {f(sg * w1)} {f(bot)} Q{f(sg * w1 * 0.55)} {f(bot + 6)} {f(sg * 6)} {f(bot)} Z"
            body += path(d, c, OUT, 3)
            body += path(d, None, None, 0)
            body += line((sg * (hw - 1), top + 4), (sg * (w1 - 4), bot - 5), darken(c, 0.3), 1.6, 0.5)
            body += rect(min(sg * 6, sg * w1) - 0, bot - 8, abs(w1 - 6), 6, V["cloth2"] if V["detail"] == "plum" else V["cloth2"], None, op=0.95)
            body += rect(sg * 6 if sg > 0 else -w1, bot - 8, w1 - 6, 6, V["cloth2"], None, op=0.0)
        return defs, body, (-w1 - 10, top - 6, w1 + 10, bot + 16)
    if arch == "pirate":
        c = V["sash"]
        body = poly([(-hw + 2, hy - 8), (-hw + 12, hy - 8), (-hw + 18, hy + 30), (-hw + 8, hy + 24), (-hw - 2, hy + 32)], c, OUT, 2.2)
        body += poly([(-hw + 12, hy - 8), (-hw + 22, hy - 6), (-hw + 30, hy + 22), (-hw + 18, hy + 30)], darken(c, 0.12), OUT, 2.2)
        body += circle(-hw + 11, hy - 9, 5, darken(c, 0.14), OUT, 1.8)
        return "", body, (-hw - 12, hy - 20, -hw + 40, hy + 44)
    if arch == "chef" and V["detail"] == "apron":
        return None
    return None


# ---- limbs ---------------------------------------------------------------------------------------------------------------

def limb_colors(arch, V):
    """(upper arm, forearm, stripe colour for the upper arm, cuff colour at the wrist, glove?)"""
    s = V["skin"]
    if arch == "pirate":
        return (V["cloth"], V["cloth"], V["cloth2"] if V["detail"] == "tricorn" else None, V["cuff"], False)
    if arch == "king":
        return (V["cloth"], V["cloth"], None, V["cloth2"], False)
    if arch == "chef":
        return (V["cloth"], V["cloth"], None, V["accent"], False)
    if arch == "superhero":
        return (V["cloth"], V["cloth"], None, V["glove"], True)
    if arch == "ballerina":
        return (s, s, None, V["accent"] if V["detail"] == "lilac" else V["cloth2"], False)
    return (V["cloth"], s, None, None, False)  # orderly: short scrub sleeve, bare forearm


def arm_parts(arch, P, V, J, side):
    name = "l" if side < 0 else "r"
    s, e = J["shoulder_" + name], J["elbow_" + name]
    w = C.wrist(P, J, side)
    aw = P["aw"]
    skin = V["skin"]
    upc, forec, stripe, cuffc, glove = limb_colors(arch, V)
    out = {}
    dx, dy = e[0] - s[0], e[1] - s[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    short = arch == "orderly"
    body = line(s, e, OUT, aw + 6, cap="butt") + circle(s[0], s[1], aw / 2 + 3, OUT)
    if short:  # bare upper arm below a short sleeve
        body += line(s, e, skin, aw, cap="round")
        o = aw * 0.24 * side
        body += line((s[0] + nx * o, s[1] + ny * o), (e[0] + nx * o, e[1] + ny * o), darken(skin, 0.25), aw * 0.4, 0.7)
        se = (s[0] + dx * 0.5, s[1] + dy * 0.5)
        body += line(s, se, OUT, aw + 5, cap="round") + line(s, se, upc, aw + 0.5, cap="round")
        body += line((s[0] + nx * o, s[1] + ny * o), (se[0] + nx * o, se[1] + ny * o), darken(upc, 0.22), aw * 0.4, 0.6)
        body += line((se[0] - nx * (aw / 2 + 1.5), se[1] - ny * (aw / 2 + 1.5)), (se[0] + nx * (aw / 2 + 1.5), se[1] + ny * (aw / 2 + 1.5)), V["cloth2"], 2.4, cap="butt")
    else:
        body += line(s, e, upc, aw, cap="round")
        o = aw * 0.24 * side
        body += line((s[0] + nx * o, s[1] + ny * o), (e[0] + nx * o, e[1] + ny * o), darken(upc, 0.25), aw * 0.4, 0.7)
        o2 = -aw * 0.26 * side
        body += line((s[0] + nx * o2, s[1] + ny * o2), (e[0] + nx * o2, e[1] + ny * o2), lighten(upc, 0.3), aw * 0.14, 0.65)
    if stripe:
        for t in (0.2, 0.4, 0.6, 0.8):
            m = (s[0] + dx * t, s[1] + dy * t)
            body += line((m[0] - nx * aw / 2, m[1] - ny * aw / 2), (m[0] + nx * aw / 2, m[1] + ny * aw / 2), stripe, 3.0, cap="butt")
    if arch == "ballerina":  # a puffed ribbon band high on the arm
        m = (s[0] + dx * 0.15, s[1] + dy * 0.15)
        body += circle(m[0], m[1], aw * 0.72, V["cloth"], OUT, 1.8)
    out["up"] = (body, bb([s, e], aw / 2 + 24))
    # forearm + hand
    fc = forec
    body = circle(e[0], e[1], aw / 2 + 3, OUT)
    body += line(e, w, OUT, aw + 6, cap="butt") + circle(w[0], w[1], aw / 2 + 3, OUT)
    body += line(e, w, fc, aw, cap="round")
    dx, dy = w[0] - e[0], w[1] - e[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    ux, uy = dx / ln, dy / ln
    body += line((e[0] + nx * aw * 0.24 * side, e[1] + ny * aw * 0.24 * side), (w[0] + nx * aw * 0.24 * side, w[1] + ny * aw * 0.24 * side), darken(fc, 0.25), aw * 0.4, 0.7)
    body += line((e[0] - nx * aw * 0.26 * side, e[1] - ny * aw * 0.26 * side), (w[0] - nx * aw * 0.26 * side, w[1] - ny * aw * 0.26 * side), lighten(fc, 0.3), aw * 0.14, 0.65)
    if arch == "pirate" and V["detail"] == "tricorn":
        for t in (0.25, 0.45, 0.65):
            m = (e[0] + dx * t, e[1] + dy * t)
            body += line((m[0] - nx * aw / 2, m[1] - ny * aw / 2), (m[0] + nx * aw / 2, m[1] + ny * aw / 2), V["cloth2"], 3.0, cap="butt")
    hand_c = (w[0] + ux * aw * 0.28, w[1] + uy * aw * 0.28)
    hr = aw * 0.62
    hand_col = V["glove"] if glove else skin
    if cuffc:
        cuff = (w[0] - ux * 4, w[1] - uy * 4)
        wd = 7.0
        if arch in ("pirate", "king", "chef"):
            wd = 8.0
        body += line((cuff[0] - nx * (aw / 2 + 2.5), cuff[1] - ny * (aw / 2 + 2.5)), (cuff[0] + nx * (aw / 2 + 2.5), cuff[1] + ny * (aw / 2 + 2.5)), OUT, wd + 2.4, cap="butt")
        body += line((cuff[0] - nx * (aw / 2 + 1.5), cuff[1] - ny * (aw / 2 + 1.5)), (cuff[0] + nx * (aw / 2 + 1.5), cuff[1] + ny * (aw / 2 + 1.5)), cuffc, wd, cap="butt")
        if arch == "ballerina":  # ribbon bow tails
            body += poly([(cuff[0] + nx * 5, cuff[1] + ny * 5), (cuff[0] + nx * 11 + ux * 8, cuff[1] + ny * 11 + uy * 8), (cuff[0] + nx * 4 + ux * 10, cuff[1] + ny * 4 + uy * 10)], cuffc, OUT, 1.2)
        if glove:  # marigold gloves flare at the wrist
            body += poly([(cuff[0] - nx * (aw / 2 + 4), cuff[1] - ny * (aw / 2 + 4)), (cuff[0] + nx * (aw / 2 + 4), cuff[1] + ny * (aw / 2 + 4)), (cuff[0] + nx * (aw / 2 + 1.5) + ux * 9, cuff[1] + ny * (aw / 2 + 1.5) + uy * 9), (cuff[0] - nx * (aw / 2 + 1.5) + ux * 9, cuff[1] - ny * (aw / 2 + 1.5) + uy * 9)], hand_col, OUT, 1.8)
    body += circle(hand_c[0], hand_c[1], hr + 2.6, OUT)
    body += circle(hand_c[0], hand_c[1], hr, hand_col)
    body += circle(hand_c[0] - nx * side * hr * 0.25, hand_c[1] - ny * side * hr * 0.25, hr * 0.4, lighten(hand_col, 0.3), None, op=0.6)
    out["fore"] = (body, bb([e, w, hand_c], aw / 2 + 24), (hand_c[0], hand_c[1]))
    return out


def shoe(ax, side, color, sole, rx_=13, toe=3, high=13, lace=None, extra=""):
    fx = ax + side * 4
    d = path(f"M{f(ax - rx_ + 2)} -4 Q{f(ax - rx_)} {f(-high)} {f(ax)} {f(-high)} Q{f(fx + side * rx_)} {f(-high)} {f(fx + side * (rx_ + toe))} -4 Q{f(fx + side * (rx_ + toe))} 1 {f(fx + side * (rx_ - 2))} 1 L{f(ax - rx_ + 4)} 1 Q{f(ax - rx_ - 1)} 0 {f(ax - rx_ + 2)} -4 Z", color, OUT, 3)
    d += line((ax - rx_ + 3, -2), (fx + side * (rx_ + toe - 1), -2), sole, 3.4, cap="butt")
    if lace:
        d += line((ax - 3, -high + 2), (ax + 4, -high + 2), lace, 1.8, 0.9) + line((ax - 3, -high + 6), (ax + 4, -high + 6), lace, 1.8, 0.9)
    return d + extra, [(fx + side * (rx_ + toe + 3), 0), (ax - rx_ - 2, 0)]


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
    if arch == "pirate":
        tr = V["trousers"]
        body += capsule(h, (ax, ay - 8), lw, tr, darken(tr, 0.3), lighten(tr, 0.2))
        boot = V["boots"]
        body += capsule((ax, ay - 30), (ax, ay), lw + 5, boot, lighten(boot, 0.04), lighten(boot, 0.3))
        body += poly([(ax - lw / 2 - 6, ay - 32), (ax + lw / 2 + 6, ay - 32), (ax + lw / 2 + 4, ay - 20), (ax - lw / 2 - 4, ay - 20)], V["cuff"], OUT, 2.4)
        body += rect(ax - 2.5, ay - 29, 5, 6, V["accent"], OUT, 1.0)
        sv, pp = shoe(ax, side, boot, darken(boot, 0.3), 14, 4, 12)
        body += sv
        pts_ += pp
    elif arch == "king":
        tr = V["trousers"]
        body += capsule(h, (ax, ay), lw, tr, darken(tr, 0.2), lighten(tr, 0.3))
        for k in range(1, 5):  # pyjama stripes
            m = (h[0] + (ax - h[0]) * k / 5.0, h[1] + (ay - h[1]) * k / 5.0)
            body += line((m[0] - lw / 2, m[1]), (m[0] + lw / 2, m[1]), V["cloth"], 2.0, 0.5, cap="butt")
        sl = V["slipper"]
        fx = ax + side * 4
        body += path(f"M{f(ax - 12)} -3 Q{f(ax - 13)} -15 {f(ax)} -15 Q{f(fx + side * 15)} -15 {f(fx + side * 17)} -5 Q{f(fx + side * 18)} 1 {f(fx + side * 10)} 1 L{f(ax - 10)} 1 Q{f(ax - 13)} 0 {f(ax - 12)} -3 Z", sl, OUT, 3)
        for k in range(5):  # fluffy tufts
            body += circle(ax - 8 + k * 6.5, -14 + (k % 2) * 1.5, 3.4, lighten(sl, 0.35), OUT, 1.4)
        pts_ += [(fx + side * 20, 0), (ax - 14, 0)]
    elif arch == "chef":
        tr = V["trousers"]
        body += capsule(h, (ax, ay), lw, tr, darken(tr, 0.3), lighten(tr, 0.2))
        for k in range(1, 7):  # houndstooth-ish check
            m = (h[0] + (ax - h[0]) * k / 7.0, h[1] + (ay - h[1]) * k / 7.0)
            body += line((m[0] - lw / 2, m[1]), (m[0] + lw / 2, m[1]), "#ffffff", 2.2, 0.55, cap="butt")
        body += line((ax - 2, h[1] + 4), (ax - 2, ay), "#ffffff", 2.2, 0.55, cap="butt") + line((ax + 3, h[1] + 4), (ax + 3, ay), "#ffffff", 2.2, 0.55, cap="butt")
        sv, pp = shoe(ax, side, V["shoes"], "#3a3a58", 13, 3, 14, extra=circle(ax, -9, 1.6, "#3a3a58"))
        body += sv
        pts_ += pp
    elif arch == "superhero":
        tr = V["trousers"]
        body += capsule(h, (ax, ay - 12), lw, tr, darken(tr, 0.3), lighten(tr, 0.25))
        boot = V["boots"]  # wellington boots
        body += capsule((ax, ay - 22), (ax, ay + 3), lw + 6, boot, darken(boot, 0.18), lighten(boot, 0.4))
        body += poly([(ax - lw / 2 - 5, ay - 24), (ax + lw / 2 + 5, ay - 24), (ax + lw / 2 + 3, ay - 17), (ax - lw / 2 - 3, ay - 17)], lighten(boot, 0.15), OUT, 2.0)
        body += path(f"M{f(ax - lw / 2 - 3)} {f(ay + 3)} Q{f(ax + side * 14)} {f(ay + 6)} {f(ax + side * 22)} {f(-3)} Q{f(ax + side * 24)} 2 {f(ax + side * 16)} 2 L{f(ax - lw / 2 - 3)} 2 Z", boot, OUT, 3)
        body += line((ax - lw / 2 - 2, -1.5), (ax + side * 21, -1.5), darken(boot, 0.4), 3, cap="butt")
        pts_ += [(ax + side * 26, 0), (ax - lw, 0)]
    elif arch == "ballerina":
        tr = V["trousers"]
        body += capsule(h, (ax, ay), lw, tr, darken(tr, 0.18), lighten(tr, 0.35))
        sl = V["shoes"]
        fx = ax + side * 3
        body += path(f"M{f(ax - 8)} -3 Q{f(ax - 9)} -9 {f(ax)} -9 Q{f(fx + side * 9)} -9 {f(fx + side * 13)} -3 Q{f(fx + side * 16)} 1 {f(fx + side * 9)} 1 L{f(ax - 7)} 1 Q{f(ax - 9)} 0 {f(ax - 8)} -3 Z", sl, OUT, 2.8)
        body += path(f"M{f(ax - 5)} -9 L{f(ax + side * 5)} {f(ay - 9)} M{f(ax + 5)} -9 L{f(ax - side * 5)} {f(ay - 9)}", None, OUT, 3.6)
        body += path(f"M{f(ax - 5)} -9 L{f(ax + side * 5)} {f(ay - 9)} M{f(ax + 5)} -9 L{f(ax - side * 5)} {f(ay - 9)}", None, V["cloth2"], 1.8)
        body += circle(ax, ay - 8, 2.0, V["accent"], OUT, 1.0)
        pts_ += [(fx + side * 17, 0), (ax - 11, 0)]
    else:  # orderly
        tr = V["trousers"]
        body += capsule(h, (ax, ay), lw, tr, darken(tr, 0.3), lighten(tr, 0.2))
        body += line((ax - lw / 2 - 1, ay - 3), (ax + lw / 2 + 1, ay - 3), darken(tr, 0.4), 3, cap="butt")
        sv, pp = shoe(ax, side, V["shoes"], V["accent"], 13, 4, 14, lace=darken(V["shoes"], 0.3))
        body += sv
        pts_ += pp
    return body, bb(pts_, lw / 2 + 14)


# ---- heads ---------------------------------------------------------------------------------------------------------------

def head_part(arch, P, V):
    rx, ry, cy, ny = P["rx"], P["ry"], P["cy"], P["neck_y"]
    skin = V["skin"]
    d = C.head_path(P)
    defs = clip("hc", f'<path d="{d}"/>') + C.SHADE_GRAD
    body = rect(-7.5, cy + ry * 0.55, 15, ny - (cy + ry * 0.55) + 14, darken(skin, 0.12), OUT, 2.6, rx=3)
    body += rect(-7.5, cy + ry * 0.78, 15, 9, "#2a1b4e", None, op=0.16)
    for side in (-1, 1):
        ex = side * (rx - 1)
        body += ellipse(ex, cy + 2, 4.6, 6.2, skin, OUT, 2.4)
        body += ellipse(ex + side * 0.4, cy + 2.5, 1.8, 3, darken(skin, 0.3), None, op=0.7)
    if arch == "pirate" and V["detail"] == "bandana":  # a small gold hoop
        body += circle(rx + 3.5, cy + 12, 4.8, None, "#ffc23f", 1.8)
    body += f'<path d="{d}" fill="{skin}"/>'
    inner = f'<rect x="{f(-rx - 4)}" y="{f(cy - ry * 1.3)}" width="{f(rx * 2 + 8)}" height="{f(ry * 2.5)}" fill="url(#shd)"/>'
    inner += f'<rect x="{f(-rx - 2)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="{RIM_L}" fill-opacity="0.55"/>'
    inner += f'<rect x="{f(rx - 2.5)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="{RIM_R}" fill-opacity="0.42"/>'
    inner += ellipse(-rx * 0.32, cy - ry * 0.45, rx * 0.28, ry * 0.14, lighten(skin, 0.35), None, op=0.45)
    body += group(inner, 'clip-path="url(#hc)"')
    body += path(d, None, OUT, 3)
    beard = V.get("beard")
    if beard and arch in ("pirate", "king", "orderly"):
        my = cy + ry * 0.58
        if arch == "orderly":  # neat short beard, jaw line only
            bd = (f"M{f(-rx + 1)} {f(cy + ry * 0.1)} Q{f(-rx - 1)} {f(cy + ry * 0.8)} {f(-rx * 0.45)} {f(cy + ry * 1.04)} Q0 {f(cy + ry * 1.18)} {f(rx * 0.45)} {f(cy + ry * 1.04)} "
                  f"Q{f(rx + 1)} {f(cy + ry * 0.8)} {f(rx - 1)} {f(cy + ry * 0.1)} L{f(rx - 5)} {f(cy + ry * 0.3)} Q{f(rx * 0.5)} {f(my + 6)} 0 {f(my + 6)} Q{f(-rx * 0.5)} {f(my + 6)} {f(-rx + 5)} {f(cy + ry * 0.3)} Z")
        else:
            ln = 20 if arch == "king" else 14
            bd = (f"M{f(-rx - 1)} {f(cy + ry * 0.05)} Q{f(-rx - 5)} {f(cy + ry * 0.9)} {f(-rx * 0.5)} {f(cy + ry + ln * 0.7)} Q0 {f(cy + ry + ln * 1.15)} {f(rx * 0.5)} {f(cy + ry + ln * 0.7)} "
                  f"Q{f(rx + 5)} {f(cy + ry * 0.9)} {f(rx + 1)} {f(cy + ry * 0.05)} L{f(rx - 4)} {f(cy + ry * 0.3)} Q{f(rx * 0.7)} {f(my + 7)} {f(rx * 0.3)} {f(my + 7)} L{f(-rx * 0.3)} {f(my + 7)} Q{f(-rx * 0.7)} {f(my + 7)} {f(-rx + 4)} {f(cy + ry * 0.3)} Z")
        body += path(bd, beard, OUT, 3)
        body += path(f"M{f(-rx * 0.6)} {f(cy + ry * 1.0)} Q{f(-rx * 0.2)} {f(cy + ry * 1.12)} {f(rx * 0.1)} {f(cy + ry * 1.06)}", None, lighten(beard, 0.4), 2.2, sop=0.6)
    return defs, body, (-rx - 14, cy - ry - 8, rx + 14, ny + 34)


def eyes_face(P, V, expr, brow_c, lashes=False, big=0.0, blush="#ff4f9a", brow_w=2.4):
    """Generic human face overlay (neutral/happy/cheer/sad) in the style of Night One."""
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    skin = V["skin"]
    ex = rx * 0.43
    ey = cy + 2.5
    er = 5.0 + big
    erx, ery = er, er * 1.25
    body = ""
    mouth_y = cy + ry * 0.58
    E = C._eye
    if expr == "neutral":
        body += E(-ex, ey, erx, ery, 3.1, lashes, -1) + E(ex, ey, erx, ery, 3.1, lashes, 1)
        by_ = ey - ery - 4.5
        body += line((-ex - 5, by_ + 0.5), (-ex + 5, by_ - 0.6), brow_c, brow_w) + line((ex - 5, by_ - 0.6), (ex + 5, by_ + 0.5), brow_c, brow_w)
        body += path(f"M-5 {f(mouth_y)} Q0 {f(mouth_y + 3.4)} 5 {f(mouth_y)}", None, "#5a1f3a", 2.2)
        body += ellipse(-ex - 3, ey + 8, 4.2, 2.4, blush, None, op=0.2) + ellipse(ex + 3, ey + 8, 4.2, 2.4, blush, None, op=0.2)
    elif expr == "happy":
        body += E(-ex, ey, erx, ery * 0.88, 3.1, lashes, -1) + E(ex, ey, erx, ery * 0.88, 3.1, lashes, 1)
        by_ = ey - ery - 6.2
        body += path(f"M{f(-ex - 5)} {f(by_ + 1.8)} Q{f(-ex)} {f(by_ - 1.6)} {f(-ex + 5)} {f(by_ + 0.8)}", None, brow_c, brow_w)
        body += path(f"M{f(ex - 5)} {f(by_ + 0.8)} Q{f(ex)} {f(by_ - 1.6)} {f(ex + 5)} {f(by_ + 1.8)}", None, brow_c, brow_w)
        body += path(f"M-7 {f(mouth_y - 1)} Q0 {f(mouth_y + 9)} 7 {f(mouth_y - 1)} Q0 {f(mouth_y + 2.6)} -7 {f(mouth_y - 1)} Z", "#7a1f45", OUT, 1.6)
        body += path(f"M-5.6 {f(mouth_y - 0.2)} Q0 {f(mouth_y + 2.8)} 5.6 {f(mouth_y - 0.2)} L5 {f(mouth_y + 1.4)} Q0 {f(mouth_y + 3.8)} -5 {f(mouth_y + 1.4)} Z", "#ffffff", None)
        body += ellipse(-ex - 3, ey + 8, 4.5, 2.6, blush, None, op=0.38) + ellipse(ex + 3, ey + 8, 4.5, 2.6, blush, None, op=0.38)
    elif expr == "cheer":
        for sx in (-1, 1):
            body += path(f"M{f(sx * ex - 5)} {f(ey + 1.4)} Q{f(sx * ex)} {f(ey - 6.5)} {f(sx * ex + 5)} {f(ey + 1.4)}", None, "#2a1b4e", 2.8)
        by_ = ey - ery - 8.4
        body += path(f"M{f(-ex - 5.5)} {f(by_ + 2.4)} Q{f(-ex)} {f(by_ - 2.4)} {f(-ex + 5.5)} {f(by_ + 1.2)}", None, brow_c, brow_w + 0.2)
        body += path(f"M{f(ex - 5.5)} {f(by_ + 1.2)} Q{f(ex)} {f(by_ - 2.4)} {f(ex + 5.5)} {f(by_ + 2.4)}", None, brow_c, brow_w + 0.2)
        my = mouth_y - 3.2
        body += path(f"M-9 {f(my)} L9 {f(my)} Q8 {f(my + 14)} 0 {f(my + 14)} Q-8 {f(my + 14)} -9 {f(my)} Z", "#6e1540", OUT, 2)
        body += path(f"M-8 {f(my + 0.8)} L8 {f(my + 0.8)} L7.4 {f(my + 4.4)} L-7.4 {f(my + 4.4)} Z", "#ffffff", None)
        body += ellipse(0, my + 11, 4.8, 3.2, "#ff6f9c", None)
        body += ellipse(-ex - 3.5, ey + 8.5, 5, 3, blush, None, op=0.5) + ellipse(ex + 3.5, ey + 8.5, 5, 3, blush, None, op=0.5)
    else:
        body += E(-ex, ey + 1, erx, ery * 0.9, 3.0, lashes, -1, look=-0.6, lid=ery * 0.9, skin=skin)
        body += E(ex, ey + 1, erx, ery * 0.9, 3.0, lashes, 1, look=-0.6, lid=ery * 0.9, skin=skin)
        by_ = ey - ery - 3.4
        body += line((-ex - 5.5, by_ + 3.2), (-ex + 4.5, by_ - 2.6), brow_c, brow_w + 0.1) + line((ex - 4.5, by_ - 2.6), (ex + 5.5, by_ + 3.2), brow_c, brow_w + 0.1)
        body += path(f"M-5.6 {f(mouth_y + 3.6)} Q0 {f(mouth_y - 2.4)} 5.6 {f(mouth_y + 3.6)}", None, "#5a1f3a", 2.4)
        body += path(f"M{f(rx * 0.72)} {f(cy - ry * 0.35)} Q{f(rx * 0.95)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy + ry * 0.1)} Q{f(rx * 0.5)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy - ry * 0.35)} Z", "#8fe6ff", OUT, 1.4)
    nose_y = cy + ry * 0.3
    body += path(f"M-1.8 {f(nose_y)} Q0.4 {f(nose_y + 3.6)} 2.8 {f(nose_y + 1.8)}", None, darken(skin, 0.42), 1.5, sop=0.85)
    return body, ex, ey


def face_overlay(arch, P, V, expr):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    brow = V["hair"] if arch in ("king", "pirate", "chef") and V["hair"] not in ("#f2f0f8", "#b9b4c6") else "#3a2f3f"
    if arch == "king":
        brow = "#8a8498"
    if arch == "ballerina":
        brow = darken(V["hair"], 0.2)
    big = 0.5 if arch in ("ballerina", "chef") else 0.0
    body, ex, ey = eyes_face(P, V, expr, brow, lashes=arch == "ballerina", big=big, brow_w=2.8 if arch in ("king", "pirate", "chef") else 2.4)
    mask = ""
    if arch == "superhero":  # domino mask, drawn under the eyes so they show through
        mc = V["mask"]
        mask = path(f"M{f(-rx * 0.98)} {f(ey - 8)} Q{f(-ex)} {f(ey - 14)} 0 {f(ey - 7)} Q{f(ex)} {f(ey - 14)} {f(rx * 0.98)} {f(ey - 8)} L{f(rx * 0.92)} {f(ey + 5)} Q{f(ex)} {f(ey + 12)} {f(rx * 0.3)} {f(ey + 3)} Q0 {f(ey - 1)} {f(-rx * 0.3)} {f(ey + 3)} Q{f(-ex)} {f(ey + 12)} {f(-rx * 0.92)} {f(ey + 5)} Z", mc, OUT, 2.2)
        mask += path(f"M{f(-ex - 6)} {f(ey - 9)} Q{f(-ex)} {f(ey - 12)} {f(-ex + 5)} {f(ey - 9)}", None, lighten(mc, 0.5), 1.6, sop=0.7)
        body += ""
    extra = ""
    mouth_y = cy + ry * 0.58
    if arch == "pirate":
        sg = -1 if V["patch"] == "left" else 1
        px = sg * ex
        extra += line((px - sg * 4, ey - 6), (sg * rx * 1.0, cy - ry * 0.5), OUT, 2.2)
        extra += line((px + sg * 4, ey - 5), (-sg * rx * 0.9, cy - ry * 0.75), OUT, 2.2)
        extra += ellipse(px, ey + 0.5, 8.2, 8.8, "#1e1a2e", OUT, 2.2) + ellipse(px - 2.2, ey - 2.6, 2.6, 1.6, "#ffffff", None, op=0.28)
        if V["beard"]:  # bushy moustache above the beard
            mc = V["beard"]
            extra += path(f"M0 {f(mouth_y - 4)} Q{f(-7)} {f(mouth_y - 9)} {f(-12)} {f(mouth_y - 2)} Q{f(-8)} {f(mouth_y + 3)} 0 {f(mouth_y - 1)} Q{f(8)} {f(mouth_y + 3)} {f(12)} {f(mouth_y - 2)} Q{f(7)} {f(mouth_y - 9)} 0 {f(mouth_y - 4)} Z", mc, OUT, 1.8)
        else:  # stubble + a cheeky mole
            for k in range(7):
                extra += circle(-9 + k * 3, cy + ry * 0.86 + (k % 2) * 2, 0.7, darken(V["skin"], 0.5), None, op=0.7)
    elif arch == "king" and V.get("mous"):
        mc = V["mous"]
        extra += path(f"M0 {f(mouth_y - 4)} Q{f(-8)} {f(mouth_y - 10)} {f(-15)} {f(mouth_y - 3)} Q{f(-9)} {f(mouth_y + 1)} 0 {f(mouth_y - 1.5)} Q{f(9)} {f(mouth_y + 1)} {f(15)} {f(mouth_y - 3)} Q{f(8)} {f(mouth_y - 10)} 0 {f(mouth_y - 4)} Z", mc, OUT, 1.8)
    elif arch == "king":
        extra += path(f"M0 {f(mouth_y - 4)} Q{f(-6)} {f(mouth_y - 8)} {f(-11)} {f(mouth_y - 3)} Q{f(-6)} {f(mouth_y)} 0 {f(mouth_y - 1.5)} Q{f(6)} {f(mouth_y)} {f(11)} {f(mouth_y - 3)} Q{f(6)} {f(mouth_y - 8)} 0 {f(mouth_y - 4)} Z", V["beard"], OUT, 1.6)
    elif arch == "chef" and V.get("mous"):
        mc = V["mous"]
        extra += path(f"M0 {f(mouth_y - 5)} Q{f(-6)} {f(mouth_y - 9)} {f(-13)} {f(mouth_y - 5)} Q{f(-17)} {f(mouth_y - 9)} {f(-15)} {f(mouth_y - 13)} Q{f(-18)} {f(mouth_y - 2)} {f(-8)} {f(mouth_y - 1)} Q{f(-3)} {f(mouth_y - 1)} 0 {f(mouth_y - 3)} Q{f(3)} {f(mouth_y - 1)} {f(8)} {f(mouth_y - 1)} Q{f(18)} {f(mouth_y - 2)} {f(15)} {f(mouth_y - 13)} Q{f(17)} {f(mouth_y - 9)} {f(13)} {f(mouth_y - 5)} Q{f(6)} {f(mouth_y - 9)} 0 {f(mouth_y - 5)} Z", mc, OUT, 1.5)
    elif arch == "chef":
        for sx in (-1, 1):  # flushed from the kitchen
            extra += ellipse(sx * (ex + 5), ey + 7, 6, 3.6, "#ff6f7a", None, op=0.28)
    elif arch == "orderly" and V["detail"] == "glasses":  # round tortoiseshell-coral frames, clear lenses so the eyes read
        fc = "#e8734a"
        for sx in (-1, 1):
            extra += circle(sx * ex, ey + 0.3, 9.0, "#ffffff", None, op=0.1) + circle(sx * ex, ey + 0.3, 9.0, None, OUT, 3.0) + circle(sx * ex, ey + 0.3, 9.0, None, fc, 1.6)
            extra += line((sx * ex - 5, ey - 4), (sx * ex - 2, ey - 6.5), "#ffffff", 1.4, 0.7)
        extra += path(f"M{f(-ex + 8.8)} {f(ey - 0.5)} Q0 {f(ey - 3.4)} {f(ex - 8.8)} {f(ey - 0.5)}", None, fc, 2.0)
        extra += line((-ex - 9, ey - 1), (-rx, ey - 2), fc, 1.8) + line((ex + 9, ey - 1), (rx, ey - 2), fc, 1.8)
    elif arch == "ballerina":
        extra += ellipse(0, mouth_y + 1.6, 3.6, 1.0, "#ff4f7a", None, op=0.0)
    return mask + body + extra, (-rx - 8, cy - ry - 6, rx + 8, cy + ry + 8)


# ---- hair, hats and swinging extras --------------------------------------------------------------------------------------

def tricorn_hat(P, V):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    hat, trim = V["hat"], V["accent"]
    by = cy - ry * 0.52
    w = rx + 16
    # the crown, then the up-turned brim in three folds: two side wings and a front point
    d = ""
    d += path(f"M{f(-w)} {f(by + 4)} Q{f(-w - 2)} {f(by - 16)} {f(-rx * 0.62)} {f(by - 22)} L{f(-rx * 0.2)} {f(by - 34)} Q0 {f(by - 38)} {f(rx * 0.2)} {f(by - 34)} L{f(rx * 0.62)} {f(by - 22)} Q{f(w + 2)} {f(by - 16)} {f(w)} {f(by + 4)} Q0 {f(by + 12)} {f(-w)} {f(by + 4)} Z", hat, OUT, 3)
    d += path(f"M{f(-w + 3)} {f(by + 4)} Q0 {f(by + 11)} {f(w - 3)} {f(by + 4)}", None, trim, 3.2)
    d += path(f"M{f(-rx * 0.6)} {f(by - 16)} Q0 {f(by - 24)} {f(rx * 0.6)} {f(by - 16)}", None, lighten(hat, 0.2), 2.4, sop=0.8)
    d += poly([(0, by - 30), (5, by - 22), (12, by - 22), (6, by - 17), (8, by - 10), (0, by - 15), (-8, by - 10), (-6, by - 17), (-12, by - 22), (-5, by - 22)], trim, OUT, 1.4)
    for sg in (-1, 1):
        d += circle(sg * (w - 3), by - 2, 2.6, trim, OUT, 1.2)
    return d, (-w - 6, by - 44, w + 6, by + 18)


def hair_parts(arch, P, V):
    """Returns {"back": (body, box, pivot, swing) or None, "front": (body, box) or None, "extra": [...]}."""
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    hair = V["hair"]
    hl = lighten(hair, 0.28)
    out = {"back": None, "front": None, "extra": []}
    if arch == "pirate":
        sh = (f"M{f(-rx - 4)} {f(cy - 4)} Q{f(-rx - 9)} {f(cy + 14)} {f(-rx - 3)} {f(cy + 20)} L{f(-rx + 4)} {f(cy + 8)} Z M{f(rx + 4)} {f(cy - 4)} Q{f(rx + 9)} {f(cy + 14)} {f(rx + 3)} {f(cy + 20)} L{f(rx - 4)} {f(cy + 8)} Z")
        if V["detail"] == "tricorn":
            back = path(f"M{f(-rx - 7)} {f(cy - 14)} C{f(-rx - 14)} {f(cy + 8)} {f(-rx - 6)} {f(cy + 26)} {f(-rx + 4)} {f(cy + 24)} L{f(rx - 4)} {f(cy + 24)} C{f(rx + 6)} {f(cy + 26)} {f(rx + 14)} {f(cy + 8)} {f(rx + 7)} {f(cy - 14)} Z", hair, OUT, 3)
            out["back"] = (back, (-rx - 22, cy - 24, rx + 22, cy + 34), None, False)
            hd, hbox = tricorn_hat(P, V)
            out["front"] = (hd, hbox)
            # the white plume: a swinging feather tucked in the hat band
            fx0, fy0 = rx + 8, cy - ry * 0.52 - 12
            fe = path(f"M{f(fx0)} {f(fy0)} C{f(fx0 + 26)} {f(fy0 - 6)} {f(fx0 + 34)} {f(fy0 + 20)} {f(fx0 + 28)} {f(fy0 + 40)} C{f(fx0 + 20)} {f(fy0 + 26)} {f(fx0 + 10)} {f(fy0 + 14)} {f(fx0)} {f(fy0)} Z", "#ffffff", OUT, 2.6)
            fe += path(f"M{f(fx0 + 2)} {f(fy0 + 1)} C{f(fx0 + 16)} {f(fy0 + 10)} {f(fx0 + 24)} {f(fy0 + 22)} {f(fx0 + 28)} {f(fy0 + 38)}", None, "#c9c4e0", 1.6)
            for k in range(4):
                fe += line((fx0 + 6 + k * 5, fy0 + 7 + k * 6), (fx0 + 13 + k * 4, fy0 + 5 + k * 6), "#c9c4e0", 1.2, 0.8)
            out["extra"].append({"name": "hat_feather", "joint": "head", "z": 21, "body": fe, "box": (fx0 - 8, fy0 - 14, fx0 + 46, fy0 + 52), "swing": True, "pivot_xy": (fx0, fy0)})
        else:
            # swinging bandana tails behind the head, knotted at the right side
            kx, ky = rx * 0.72, cy - ry * 0.52
            tails = path(f"M{f(kx)} {f(ky)} C{f(kx + 14)} {f(ky + 6)} {f(kx + 24)} {f(ky + 24)} {f(kx + 20)} {f(ky + 44)} L{f(kx + 13)} {f(ky + 38)} L{f(kx + 8)} {f(ky + 46)} C{f(kx + 4)} {f(ky + 30)} {f(kx + 2)} {f(ky + 16)} {f(kx - 4)} {f(ky + 8)} Z", V["hat"], OUT, 2.8)
            for (dx_, dy_) in ((12, 22), (16, 34), (6, 16), (10, 40)):
                tails += circle(kx + dx_, ky + dy_, 1.6, "#ffffff", None)
            out["back"] = (tails, (kx - 12, ky - 8, kx + 34, ky + 56), (kx, ky), True)
            back = path(f"M{f(-rx - 5)} {f(cy - 12)} C{f(-rx - 12)} {f(cy + 8)} {f(-rx - 4)} {f(cy + 22)} {f(-rx + 4)} {f(cy + 20)} L{f(-rx + 8)} {f(cy)} Z M{f(rx + 5)} {f(cy - 12)} C{f(rx + 12)} {f(cy + 8)} {f(rx + 4)} {f(cy + 22)} {f(rx - 4)} {f(cy + 20)} L{f(rx - 8)} {f(cy)} Z", hair, OUT, 3)
            out["extra"].append({"name": "hair_sides", "joint": "head", "z": -19, "body": back, "box": (-rx - 22, cy - 24, rx + 22, cy + 32), "swing": False})
            hd = (f"M{f(-rx - 3)} {f(cy - 3)} C{f(-rx - 5)} {f(cy - ry * 1.5)} {f(rx + 5)} {f(cy - ry * 1.5)} {f(rx + 3)} {f(cy - 3)} "
                  f"L{f(rx - 2)} {f(cy - ry * 0.5)} Q0 {f(cy - ry * 0.34)} {f(-rx + 2)} {f(cy - ry * 0.5)} Z")
            b = path(hd, V["hat"], OUT, 3)
            for (dx_, dy_) in ((-14, -26), (-4, -34), (8, -30), (16, -22), (-8, -18), (4, -20), (-18, -12)):
                b += circle(dx_, cy + dy_ + 4, 1.9, "#ffffff", None)
            b += path(f"M{f(-rx - 2)} {f(cy - ry * 0.5)} Q0 {f(cy - ry * 0.3)} {f(rx + 2)} {f(cy - ry * 0.5)}", None, darken(V["hat"], 0.3), 3.4, sop=0.8)
            b += circle(kx, ky + 2, 5.4, darken(V["hat"], 0.12), OUT, 2.2)
            b += path(f"M{f(-rx * 0.6)} {f(cy - ry * 1.05)} Q{f(-rx * 0.1)} {f(cy - ry * 1.28)} {f(rx * 0.4)} {f(cy - ry * 1.15)}", None, lighten(V["hat"], 0.35), 2.8, sop=0.7)
            out["front"] = (b, (-rx - 16, cy - ry - 18, rx + 16, cy + 6))
    elif arch == "king":
        puffs = ""
        for sg in (-1, 1):
            for k, (px_, py_, r_) in enumerate(((rx + 3, cy - 10, 9), (rx + 8, cy + 2, 10), (rx + 4, cy + 14, 8))):
                puffs += circle(sg * px_, py_, r_, hair, OUT, 2.6)
        out["back"] = (puffs, (-rx - 26, cy - 26, rx + 26, cy + 30), None, False)
        cr, gem = V["crown"], V["gem"]
        by = cy - ry * 0.74
        w = rx * 0.92
        pts_ = [(-w, by + 3), (-w, by - 14), (-w * 0.62, by - 4), (-w * 0.32, by - 24), (0, by - 6), (w * 0.32, by - 24), (w * 0.62, by - 4), (w, by - 14), (w, by + 3)]
        d = f'<g transform="rotate(-5 0 {f(by)})">' + poly(pts_, cr, OUT, 3)
        d += rect(-w, by - 1, w * 2, 9, darken(cr, 0.14), OUT, 2.2, rx=1)
        d += path(f"M{f(-w + 3)} {f(by - 5)} L{f(-w * 0.6)} {f(by - 3)}", None, lighten(cr, 0.5), 1.6, sop=0.8)
        for (gx, gy, gc) in ((-w * 0.32, by - 19, gem), (w * 0.32, by - 19, "#3ad0b8"), (0, by + 3.5, gem), (-w * 0.7, by + 3.5, "#ffffff"), (w * 0.7, by + 3.5, "#ffffff")):
            d += circle(gx, gy, 2.8, gc, OUT, 1.2)
        d += "</g>"
        if V["detail"] == "ermine":  # fluffy band under the crown
            for k in range(7):
                d += circle(-w + 4 + k * (w * 2 - 8) / 6, by + 8, 3.2, "#ffffff", OUT, 1.2)
        d += path(f"M{f(-rx * 0.62)} {f(cy - ry * 0.9)} Q{f(-rx * 0.2)} {f(cy - ry * 0.84)} 0 {f(cy - ry * 0.88)}", None, hair, 5, sop=0.0)
        out["front"] = (d, (-w - 10, by - 36, w + 10, by + 20))
    elif arch == "chef":
        hat = V["hat"]
        by = cy - ry * 0.7
        w = rx * 0.9
        d = path(f"M{f(-w)} {f(by + 4)} L{f(-w - 3)} {f(by - 26)} C{f(-w - 26)} {f(by - 30)} {f(-w - 24)} {f(by - 66)} {f(-w * 0.5)} {f(by - 62)} C{f(-w * 0.35)} {f(by - 80)} {f(w * 0.35)} {f(by - 80)} {f(w * 0.5)} {f(by - 62)} C{f(w + 24)} {f(by - 66)} {f(w + 26)} {f(by - 30)} {f(w + 3)} {f(by - 26)} L{f(w)} {f(by + 4)} Z", hat, OUT, 3)
        for k in (-2, -1, 0, 1, 2):  # pleats
            d += path(f"M{f(k * 7)} {f(by - 28)} Q{f(k * 9)} {f(by - 45)} {f(k * 12)} {f(by - 66)}", None, darken(hat, 0.14), 1.8, sop=0.8)
        d += rect(-w - 3, by - 8, w * 2 + 6, 14, hat, OUT, 2.8, rx=3)
        d += rect(-w - 3, by - 1, w * 2 + 6, 7, V["accent"], None, op=0.9) if V["detail"] == "classic" else line((-w - 1, by + 2), (w + 1, by + 2), V["accent"], 3.0)
        d += path(f"M{f(-w - 14)} {f(by - 52)} Q{f(-w - 16)} {f(by - 40)} {f(-w - 8)} {f(by - 34)}", None, "#eceaff", 2.6, sop=0.8)
        out["front"] = (d, (-w - 34, by - 90, w + 34, by + 10))
        hairb = path(f"M{f(-rx - 3)} {f(cy - 6)} Q{f(-rx - 6)} {f(cy + 10)} {f(-rx + 2)} {f(cy + 14)} L{f(-rx + 5)} {f(cy)} Z M{f(rx + 3)} {f(cy - 6)} Q{f(rx + 6)} {f(cy + 10)} {f(rx - 2)} {f(cy + 14)} L{f(rx - 5)} {f(cy)} Z", V["hair"], OUT, 2.6)
        out["extra"].append({"name": "hair_sides", "joint": "head", "z": -19, "body": hairb, "box": (-rx - 14, cy - 14, rx + 14, cy + 24), "swing": False})
    elif arch == "superhero":
        if V["detail"] == "star":  # big swept-back quiff
            fr = path(f"M{f(-rx - 3)} {f(cy + 4)} C{f(-rx - 8)} {f(cy - ry * 1.7)} {f(rx * 0.4)} {f(cy - ry * 2.0)} {f(rx + 8)} {f(cy - ry * 0.9)} C{f(rx + 8)} {f(cy - ry * 0.4)} {f(rx + 4)} {f(cy)} {f(rx + 2)} {f(cy + 4)} L{f(rx - 2)} {f(cy - 8)} Q{f(rx * 0.3)} {f(cy - ry * 0.7)} {f(-rx * 0.4)} {f(cy - ry * 0.5)} Q{f(-rx * 0.8)} {f(cy - ry * 0.3)} {f(-rx + 1)} {f(cy + 2)} Z", hair, OUT, 3)
            fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.1)} Q{f(rx * 0.2)} {f(cy - ry * 1.6)} {f(rx * 0.9)} {f(cy - ry * 1.15)}", None, hl, 3.2, sop=0.75)
        else:  # short with a cheeky tuft
            fr = path(f"M{f(-rx - 3)} {f(cy + 4)} C{f(-rx - 6)} {f(cy - ry * 1.5)} {f(rx + 6)} {f(cy - ry * 1.5)} {f(rx + 3)} {f(cy + 4)} L{f(rx - 2)} {f(cy - 8)} Q0 {f(cy - ry * 0.6)} {f(-rx + 2)} {f(cy - 8)} Z", hair, OUT, 3)
            fr += path(f"M-2 {f(cy - ry * 1.25)} Q{f(-6)} {f(cy - ry * 1.9)} {f(2)} {f(cy - ry * 1.95)} Q{f(8)} {f(cy - ry * 1.6)} {f(6)} {f(cy - ry * 1.2)} Z", hair, OUT, 2.6)
            fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.0)} Q{f(-rx * 0.1)} {f(cy - ry * 1.2)} {f(rx * 0.4)} {f(cy - ry * 1.05)}", None, hl, 3, sop=0.75)
        out["front"] = (fr, (-rx - 18, cy - ry * 2.1, rx + 18, cy + 8))
        # the towel cape, a swinging part hung from the neck: a bath towel with stripes and a fringe, clipped to its outline
        sy = P["sh_y"] - 6
        cw = P["sw"] + 6
        hemy = -P["hip_y"] + 30
        hw_ = cw + 30
        shape = (f"M{f(-10)} {f(sy)} Q{f(-cw - 2)} {f(sy + 4)} {f(-cw - 4)} {f(sy + 40)} Q{f(-hw_ + 6)} {f((sy + hemy) / 2)} {f(-hw_)} {f(hemy)} "
                 f"L{f(hw_)} {f(hemy)} Q{f(hw_ - 6)} {f((sy + hemy) / 2)} {f(cw + 4)} {f(sy + 40)} Q{f(cw + 2)} {f(sy + 4)} {f(10)} {f(sy)} Z")
        cdefs = clip("cp", f'<path d="{shape}"/>')
        inner = ""
        for k in range(6):
            yy = sy + 34 + k * 26
            if yy < hemy - 6:
                inner += rect(-hw_ - 4, yy, hw_ * 2 + 8, 6.0, V["cape2"], None, op=0.92)
        inner += rect(0, sy, hw_ + 4, hemy - sy + 4, "#2a1b4e", None, op=0.14)
        cape = f'<path d="{shape}" fill="{V["cape"]}"/>' + group(inner, 'clip-path="url(#cp)"') + path(shape, None, OUT, 3)
        for k in range(15):
            x = -hw_ + 3 + k * (2 * hw_ - 6) / 14.0
            cape += line((x, hemy), (x * 1.0, hemy + 7), OUT, 3.0) + line((x, hemy), (x, hemy + 6), V["cape2"], 1.6)
        cape += path(f"M{f(-cw - 2)} {f(sy + 44)} L{f(-hw_ + 8)} {f(hemy - 10)}", None, "#ffffff", 3, sop=0.28)
        out["extra"].append({"name": "cape", "joint": "torso", "z": -15, "body": cdefs + cape, "box": (-hw_ - 8, sy - 8, hw_ + 8, hemy + 14), "swing": True, "pivot_xy": (0, sy)})
    elif arch == "ballerina":
        # bun: a swinging ball behind the head crown (swings about its base)
        bx, by = 0, cy - ry * 1.12
        bun = circle(bx, by - 10, 14, hair, OUT, 3) + path(f"M{f(-8)} {f(by - 18)} Q0 {f(by - 24)} {f(8)} {f(by - 18)}", None, lighten(hair, 0.35), 2.4, sop=0.8)
        for k in range(3):
            bun += path(f"M{f(-10 + k * 3)} {f(by - 6 - k * 3)} Q{f(0)} {f(by - 2 - k * 4)} {f(10 - k * 3)} {f(by - 6 - k * 3)}", None, darken(hair, 0.28), 1.4, sop=0.6)
        bun += path(f"M{f(-12)} {f(by - 2)} L{f(12)} {f(by - 2)}", None, V["cloth"], 4.2)
        out["back"] = (bun, (-26, by - 32, 26, by + 6), (0, by), True)
        fr = path(f"M{f(-rx - 3)} {f(cy + 8)} C{f(-rx - 6)} {f(cy - ry * 1.5)} {f(rx + 6)} {f(cy - ry * 1.5)} {f(rx + 3)} {f(cy + 8)} L{f(rx - 2)} {f(cy - 8)} C{f(rx * 0.5)} {f(cy - ry * 0.55)} {f(-rx * 0.5)} {f(cy - ry * 0.55)} {f(-rx + 2)} {f(cy - 8)} Z", hair, OUT, 3)
        fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.0)} Q{f(0)} {f(cy - ry * 1.28)} {f(rx * 0.5)} {f(cy - ry * 1.0)}", None, lighten(hair, 0.35), 2.8, sop=0.7)
        ty = cy - ry * 0.98  # tiara
        t = V["tiara"]
        fr += path(f"M{f(-rx * 0.55)} {f(ty + 6)} L{f(-rx * 0.45)} {f(ty - 4)} L{f(-rx * 0.22)} {f(ty + 3)} L0 {f(ty - 9)} L{f(rx * 0.22)} {f(ty + 3)} L{f(rx * 0.45)} {f(ty - 4)} L{f(rx * 0.55)} {f(ty + 6)} Z", t, OUT, 2.0)
        for (gx, gy) in ((0, ty - 5), (-rx * 0.4, ty + 1), (rx * 0.4, ty + 1)):
            fr += circle(gx, gy, 1.9, "#ff7ab8" if V["detail"] == "pink" else "#7ad0ff", OUT, 0.8)
        out["front"] = (fr, (-rx - 14, cy - ry - 14, rx + 14, cy + 12))
    elif arch == "orderly":
        if V["detail"] == "glasses":  # short tight curls
            fr = ""
            rr = 7.0
            for k in range(11):
                a = math.radians(-168 + k * 15.6)
                fr += circle(math.cos(a) * (rx + 1), cy - 4 + math.sin(a) * (ry * 1.15), rr, hair, OUT, 2.2)
            fr += path(f"M{f(-rx - 2)} {f(cy)} C{f(-rx - 4)} {f(cy - ry * 1.3)} {f(rx + 4)} {f(cy - ry * 1.3)} {f(rx + 2)} {f(cy)} L{f(rx - 2)} {f(cy - 10)} Q0 {f(cy - ry * 0.64)} {f(-rx + 2)} {f(cy - 10)} Z", hair, None)
            for k in range(7):
                fr += circle(-14 + k * 4.6, cy - ry * 0.98 - (k % 2) * 3, 4, hair, None) + path(f"M{f(-14 + k * 4.6 - 3)} {f(cy - ry * 0.98 - (k % 2) * 3)} q3 -3 6 0", None, hl, 1.2, sop=0.5)
        else:  # neat side-swept
            fr = path(f"M{f(-rx - 3)} {f(cy + 2)} C{f(-rx - 6)} {f(cy - ry * 1.55)} {f(rx + 6)} {f(cy - ry * 1.55)} {f(rx + 3)} {f(cy + 2)} L{f(rx - 2)} {f(cy - 10)} Q{f(rx * 0.2)} {f(cy - ry * 0.7)} {f(-rx * 0.6)} {f(cy - ry * 0.52)} Q{f(-rx * 0.9)} {f(cy - ry * 0.3)} {f(-rx + 1)} {f(cy)} Z", hair, OUT, 3)
            fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.0)} Q{f(rx * 0.1)} {f(cy - ry * 1.3)} {f(rx * 0.7)} {f(cy - ry * 1.0)}", None, hl, 3, sop=0.75)
        out["front"] = (fr, (-rx - 18, cy - ry * 1.9, rx + 18, cy + 8))
    return out


# ---- assembly ------------------------------------------------------------------------------------------------------------

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
    emit("pelvis", "hips", -5, pel[0], pel[1])
    defs, body, box = torso_part(arch, P, V)
    emit("torso", "torso", 0, body, box, defs)
    sk = skirt_part(arch, P, V)
    if sk:
        emit("skirt", "hips", 3 if arch == "ballerina" else 2, sk[1], sk[2], sk[0])
    if arch == "pirate" and V["detail"] == "bandana":  # a toy parrot on the shoulder
        s = J["shoulder_r"]
        px, py = s[0] + 2, s[1] - 6
        pb = ellipse(px, py + 6, 8, 10, "#3ad07a", OUT, 2.2) + poly([(px - 6, py + 12), (px - 14, py + 28), (px - 4, py + 22)], "#e0364a", OUT, 1.6)
        pb += circle(px + 1, py - 6, 6.6, "#3ad07a", OUT, 2.2) + poly([(px + 6, py - 8), (px + 14, py - 4), (px + 6, py - 2)], "#ffc23f", OUT, 1.4)
        pb += circle(px + 2.5, py - 8, 2.0, "#ffffff", OUT, 1.0) + circle(px + 3, py - 8, 0.9, "#1b1040") + ellipse(px - 2, py + 6, 3.6, 6, "#2f9a5a", None, op=0.7)
        pb += path(f"M{f(px - 5)} {f(py - 11)} Q{f(px - 4)} {f(py - 17)} {f(px + 1)} {f(py - 14)}", None, "#e0364a", 3.4)
        emit("parrot", "torso", 6, pb, (px - 22, py - 24, px + 22, py + 34))
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
        emit("hair_front", "head", 20, body, box)
    fb = arms["r"]["fore"][1]
    hand = arms["r"]["fore"][2]
    hand_px = [round((hand[0] - math.floor(fb[0])) * 2, 1), round((hand[1] - math.floor(fb[1])) * 2, 1)]
    fbl = arms["l"]["fore"][1]
    handl = arms["l"]["fore"][2]
    hand_px_l = [round((handl[0] - math.floor(fbl[0])) * 2, 1), round((handl[1] - math.floor(fbl[1])) * 2, 1)]
    return {"parts": parts, "faces": faces, "face_z": 12,
            "glow_hand": {"joint": "elbow_r", "at": hand_px, "joint_l": "elbow_l", "at_l": hand_px_l}}


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
