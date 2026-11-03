"""The six dancer archetypes of Night One as rigged SVG part sets (front view, facing the DJ).

Each archetype x variant writes ~17 part SVGs: back hair, hips, two legs, torso, two upper arms, two forearms, head, four
expression overlays, front hair and a few extras. Parts are drawn at rest pose in rig space (origin between the feet, +y
down, so the head is at negative y) and each carries the pivot of the joint it rotates about. The runtime assembles them.
"""
from __future__ import annotations

import math

from .lib import (OUT, bbox, capsule, circle, clip, darken, ellipse, group, lighten, line, lin_grad, mix, path, pivot_in,
                  poly, rect, union, write_svg, f)

SHADE_GRAD = ('<linearGradient id="shd" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#150a33" stop-opacity="0"/>'
              '<stop offset="0.55" stop-color="#150a33" stop-opacity="0"/><stop offset="1" stop-color="#150a33" stop-opacity="0.36"/></linearGradient>')
ARMS_REST_DEG = 7.0  # arms hang slightly outward


# ---- proportions ----------------------------------------------------------------------------------------------------

ARCH = {
    "groover": dict(hip_y=112, sh_y=-192, sh_dx=30, neck_y=-201, cy=-227, rx=21, ry=25, up=42, fore=44, aw=15,
                    sw=31, ww=22, hw=25, lw=21, leg_dx=11, shoe_h=10),
    "ponytail": dict(hip_y=100, sh_y=-178, sh_dx=24, neck_y=-187, cy=-212, rx=22, ry=26, up=38, fore=41, aw=13,
                     sw=25, ww=17, hw=23, lw=22, leg_dx=12, shoe_h=10),
    "hoodie": dict(hip_y=94, sh_y=-172, sh_dx=40, neck_y=-180, cy=-205, rx=25, ry=26, up=40, fore=40, aw=21,
                   sw=42, ww=37, hw=36, lw=26, leg_dx=17, shoe_h=12),
    "curly": dict(hip_y=106, sh_y=-184, sh_dx=30, neck_y=-193, cy=-219, rx=22, ry=26, up=40, fore=43, aw=15,
                  sw=30, ww=23, hw=26, lw=20, leg_dx=12, shoe_h=11),
    "bob": dict(hip_y=90, sh_y=-166, sh_dx=24, neck_y=-174, cy=-199, rx=23, ry=27, up=35, fore=37, aw=12,
                sw=24, ww=17, hw=22, lw=13, leg_dx=9, shoe_h=12),
    "punk": dict(hip_y=116, sh_y=-196, sh_dx=32, neck_y=-206, cy=-231, rx=20, ry=25, up=44, fore=46, aw=15,
                 sw=32, ww=22, hw=24, lw=17, leg_dx=11, shoe_h=14),
}

for _p in ARCH.values():  # a slightly big head reads better at crowd distance
    _p["rx"] = round(_p["rx"] * 1.12)
    _p["ry"] = round(_p["ry"] * 1.12)
    _p["cy"] -= 3

SKIN = {
    "pale": "#fbd9c0", "tan": "#e6aa7a", "brown": "#b67a52", "deep": "#8a5233", "dark": "#68402a", "olive": "#d9a273",
}

VARIANTS = {
    "groover": {
        "a": dict(skin=SKIN["tan"], hair="#27214a", tip="#19d2ff", top="#ff2f9d", top2="#ffe9a8", bottom="#2b3566", shoes="#19d2ff", accent="#ffc23f"),
        "b": dict(skin=SKIN["deep"], hair="#f4d77c", tip="#ff2f9d", top="#19c8e8", top2="#ffffff", bottom="#3b2a6e", shoes="#ffc23f", accent="#ff2f9d"),
    },
    "ponytail": {
        "a": dict(skin=SKIN["brown"], hair="#3b2230", tip="#ff3fa4", top="#9a6bff", top2="#d9c4ff", bottom="#16b7c7", shoes="#ffffff", accent="#ff3fa4"),
        "b": dict(skin=SKIN["pale"], hair="#d8553a", tip="#ffc23f", top="#ffb23f", top2="#fff0c4", bottom="#5a2f8e", shoes="#19d2ff", accent="#19d2ff"),
    },
    "hoodie": {
        "a": dict(skin=SKIN["deep"], hair="#2a1a24", tip="#2a1a24", top="#e0457f", top2="#ffd0e4", bottom="#343a63", shoes="#f4f0ff", accent="#19d2ff"),
        "b": dict(skin=SKIN["olive"], hair="#1f1a30", tip="#1f1a30", top="#1fae9b", top2="#bff5ec", bottom="#231f3a", shoes="#ffc23f", accent="#ff2f9d"),
    },
    "curly": {
        "a": dict(skin=SKIN["dark"], hair="#2b1a28", tip="#6a3fd0", top="#ff9a2e", top2="#6a3fd0", bottom="#262a52", shoes="#ff9a2e", accent="#ff2f9d"),
        "b": dict(skin=SKIN["pale"], hair="#8a3d22", tip="#ffb23f", top="#2fd0e8", top2="#f4f0ff", bottom="#5a2146", shoes="#ffffff", accent="#19d2ff"),
    },
    "bob": {
        "a": dict(skin=SKIN["pale"], hair="#1c1634", tip="#19d2ff", top="#3b86ff", top2="#ffffff", bottom="#ff2f9d", shoes="#1c1634", accent="#ff2f9d"),
        "b": dict(skin=SKIN["tan"], hair="#17b8a6", tip="#ff6fb8", top="#ffd23f", top2="#fffbe6", bottom="#6a3fd0", shoes="#ffffff", accent="#6a3fd0"),
    },
    "punk": {
        "a": dict(skin=SKIN["pale"], hair="#ff2f9d", tip="#ffe0f0", top="#7a4cff", top2="#d9c4ff", bottom="#2d2a46", shoes="#1e1a2e", accent="#ffc23f"),
        "b": dict(skin=SKIN["brown"], hair="#19d2ff", tip="#e6fbff", top="#ff2f9d", top2="#ffd0e4", bottom="#1f1d36", shoes="#2a1f3a", accent="#ffc23f"),
    },
}

EXPRESSIONS = ["neutral", "happy", "cheer", "sad"]


# ---- skeleton --------------------------------------------------------------------------------------------------------

def skeleton(P: dict) -> dict:
    a = math.radians(ARMS_REST_DEG)
    sx, sy = P["sh_dx"], P["sh_y"] + 6
    J = {
        "hips": (0, -P["hip_y"]),
        "torso": (0, -P["hip_y"] - 10),
        "head": (0, P["neck_y"]),
        "shoulder_l": (-sx, sy), "shoulder_r": (sx, sy),
        "hip_l": (-P["leg_dx"], -P["hip_y"] + 4), "hip_r": (P["leg_dx"], -P["hip_y"] + 4),
    }
    for side, name in ((-1, "l"), (1, "r")):
        s = J["shoulder_" + name]
        e = (s[0] + side * P["up"] * math.sin(a), s[1] + P["up"] * math.cos(a))
        J["elbow_" + name] = e
    return J


def wrist(P, J, side):
    e = J["elbow_l" if side < 0 else "elbow_r"]
    a = math.radians(ARMS_REST_DEG + 3)
    return (e[0] + side * P["fore"] * math.sin(a), e[1] + P["fore"] * math.cos(a))


def rim_defs() -> str:
    return ""


# ---- torso ------------------------------------------------------------------------------------------------------------

def torso_outline(P: dict, flare: float = 0.0) -> str:
    sw, ww, hw = P["sw"], P["ww"], P["hw"] + flare
    ts = P["sh_y"] - 8  # shoulder line top
    wy = -P["hip_y"] - 34
    by = -P["hip_y"] + 14
    nw = 8
    return (f"M{f(-nw)} {f(ts - 2)} Q{f(-sw * 0.62)} {f(ts - 3)} {f(-sw)} {f(ts + 12)} "
            f"L{f(-sw + 1)} {f(ts + 30)} Q{f(-ww - 1)} {f((ts + wy) / 2 + 6)} {f(-ww)} {f(wy)} L{f(-hw)} {f(by)} "
            f"L{f(hw)} {f(by)} L{f(ww)} {f(wy)} Q{f(ww + 1)} {f((ts + wy) / 2 + 6)} {f(sw - 1)} {f(ts + 30)} "
            f"L{f(sw)} {f(ts + 12)} Q{f(sw * 0.62)} {f(ts - 3)} {f(nw)} {f(ts - 2)} Z")


def torso_part(arch: str, P: dict, V: dict) -> tuple[str, str, tuple]:
    """Returns (defs, body, box) for the torso."""
    sw, ww, hw = P["sw"], P["ww"], P["hw"]
    ts = P["sh_y"] - 8
    wy = -P["hip_y"] - 34
    by = -P["hip_y"] + 14
    d = torso_outline(P, 2 if arch == "bob" else 0)
    skin, top, top2 = V["skin"], V["top"], V["top2"]
    defs = clip("tc", f'<path d="{d}"/>') + SHADE_GRAD
    inner = ""
    base = top
    if arch == "groover":  # tank top, V neck, chevron print, chain
        inner += poly([(-13, ts - 4), (13, ts - 4), (0, ts + 26)], skin, OUT, 2)
        for k, y in enumerate((ts + 40, ts + 52)):
            inner += path(f"M{f(-ww - 4)} {f(y)} L0 {f(y + 9)} L{f(ww + 4)} {f(y)}", None, top2, 4.5, cap="round")
        inner += path(f"M-10 {f(ts + 2)} Q0 {f(ts + 34)} 10 {f(ts + 2)}", None, V["accent"], 2.0)
        inner += "".join(circle(-6 + k * 3, ts + 18 + abs(k - 2) * -2 + 6, 1.6, V["accent"]) for k in range(5))
    elif arch == "ponytail":  # crop top over bare midriff, cap sleeves
        base = skin
        hem = by - 52
        inner += rect(-sw - 4, ts - 4, sw * 2 + 8, hem - ts + 4, top)
        inner += path(f"M{f(-sw - 4)} {f(hem)} " + "".join(f"Q{f(-sw + 7 + k * 14)} {f(hem + 8)} {f(-sw + 14 + k * 14)} {f(hem)} " for k in range(int((2 * sw + 8) / 14) + 1)) + "L40 %s L-40 %s Z" % (f(hem - 6), f(hem - 6)), top, None)
        inner += path(f"M-9 {f(ts - 2)} Q0 {f(ts + 14)} 9 {f(ts - 2)}", skin, OUT, 2)
        inner += line((-sw + 5, ts + 16), (-ww + 3, hem - 6), top2, 3, 0.6)
        inner += line((sw - 5, ts + 16), (ww - 3, hem - 6), top2, 3, 0.6)
        inner += circle(0, hem + 20, 1.6, darken(skin, 0.45))
        inner += circle(0, ts + 24, 4.2, V["accent"], OUT, 1.5)
    elif arch == "hoodie":  # big hoodie, drawstrings, kangaroo pocket
        inner += ellipse(0, ts + 2, 17, 10, darken(top, 0.35), OUT, 2.2)
        inner += ellipse(0, ts + 3, 11, 6, darken(skin, 0.25))
        inner += line((-5, ts + 8), (-6, ts + 34), top2, 2.4)
        inner += line((5, ts + 8), (6, ts + 34), top2, 2.4)
        inner += circle(-6, ts + 35, 2, top2)
        inner += circle(6, ts + 35, 2, top2)
        inner += path(f"M{f(-24)} {f(wy - 10)} L{f(24)} {f(wy - 10)} L{f(30)} {f(by - 6)} L{f(-30)} {f(by - 6)} Z", darken(top, 0.18), OUT, 2.4)
        inner += line((0, wy - 10), (0, by - 6), OUT, 1.6, 0.6)
        inner += circle(-14, ts + 50, 7, V["accent"], OUT, 2)  # chest logo
        inner += poly([(-14, ts + 46), (-10.5, ts + 53), (-17.5, ts + 53)], top2)
    elif arch == "curly":  # open jacket over a violet/white shirt
        base = V["top2"]
        jl = [(-sw - 3, ts - 4), (-8, ts - 4), (-4, ts + 20), (-9, by + 2), (-hw - 4, by + 2)]
        jr = [(sw + 3, ts - 4), (8, ts - 4), (4, ts + 20), (9, by + 2), (hw + 4, by + 2)]
        inner += poly(jl, top, OUT, 2.4) + poly(jr, top, OUT, 2.4)
        inner += poly([(-8, ts - 4), (-20, ts + 2), (-12, ts + 22), (-4, ts + 20)], lighten(top, 0.25), OUT, 2)  # lapels
        inner += poly([(8, ts - 4), (20, ts + 2), (12, ts + 22), (4, ts + 20)], lighten(top, 0.25), OUT, 2)
        inner += line((-9, ts + 26), (-9, by), darken(top, 0.4), 2, 0.7)
        inner += line((9, ts + 26), (9, by), darken(top, 0.4), 2, 0.7)
        inner += rect(-sw + 2, by - 26, 12, 4, darken(top, 0.4), None, rx=1.5)
        inner += rect(sw - 14, by - 26, 12, 4, darken(top, 0.4), None, rx=1.5)
        inner += circle(0, ts + 8, 3.2, V["accent"], OUT, 1.5)  # pin
    elif arch == "bob":  # sleeveless dress with white collar
        inner += path(f"M-13 {f(ts - 4)} Q0 {f(ts + 22)} 13 {f(ts - 4)} L25 {f(ts - 6)} L25 {f(ts + 6)} L0 {f(ts + 22)} L-25 {f(ts + 6)} L-25 {f(ts - 6)} Z", V["top2"], OUT, 2.2)
        inner += path(f"M-12 {f(ts - 3)} Q0 {f(ts + 16)} 12 {f(ts - 3)}", skin, None)
        for k in range(3):
            inner += circle(0, ts + 28 + k * 11, 2.0, V["accent"], OUT, 1.2)
        inner += rect(-hw - 4, wy + 4, hw * 2 + 8, 7, V["accent"], OUT, 2, rx=2)
    elif arch == "punk":  # studded leather vest over a coloured tee
        inner += poly([(-10, ts - 4), (10, ts - 4), (0, ts + 18)], skin, OUT, 2)
        vl = [(-sw - 3, ts - 6), (-9, ts - 6), (-2, ts + 30), (-5, by + 2), (-hw - 4, by + 2)]
        vr = [(sw + 3, ts - 6), (9, ts - 6), (2, ts + 30), (5, by + 2), (hw + 4, by + 2)]
        vest = "#1e1a2e"
        inner += poly(vl, vest, OUT, 2.4) + poly(vr, vest, OUT, 2.4)
        for k in range(5):
            inner += circle(-14 + k * 0.4, ts + 6 + k * 9, 2.0, V["accent"])
            inner += circle(14 - k * 0.4, ts + 6 + k * 9, 2.0, V["accent"])
        inner += line((-sw + 3, ts + 18), (-ww, wy), lighten(vest, 0.2), 2, 0.8)
        inner += line((sw - 3, ts + 18), (ww, wy), lighten(vest, 0.2), 2, 0.8)
        inner += rect(-hw - 2, by - 12, hw * 2 + 4, 9, "#2c2244", OUT, 2)  # belt
        inner += rect(-6, by - 12, 12, 9, V["accent"], OUT, 2)
        inner += path(f"M{f(hw)} {f(by - 8)} Q{f(hw + 5)} {f(by + 6)} {f(hw - 2)} {f(by + 12)}", None, "#cfcfe6", 1.6)  # chain
    body = f'<path d="{d}" fill="{base}"/>'
    body += group(inner, 'clip-path="url(#tc)"')
    # shading: right side shade, left cyan and right magenta rim light, inside the silhouette
    shade = f'<rect x="{f(-sw - 8)}" y="{f(ts - 6)}" width="{f(sw * 2 + 16)}" height="{f(by - ts + 12)}" fill="url(#shd)"/>'
    rim_l = f'<rect x="{f(-sw - 3)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="#19d2ff" fill-opacity="0.45"/>'
    rim_r = f'<rect x="{f(sw - 2)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="#ff2f9d" fill-opacity="0.35"/>'
    body += group(shade + rim_l + rim_r, 'clip-path="url(#tc)"')
    body += path(d, None, OUT, 3)
    box = (-sw - 8, ts - 10, sw + 8, by + 6)
    return defs, body, box


def pelvis_part(arch: str, P: dict, V: dict):
    hy = -P["hip_y"]
    hw = P["hw"] + 1
    cloth = V["bottom"]
    if arch == "bob":
        return None
    if arch == "ponytail":
        cloth = V["bottom"]
    d = f"M{f(-hw)} {f(hy - 12)} L{f(hw)} {f(hy - 12)} L{f(hw + 1)} {f(hy + 12)} Q0 {f(hy + 22)} {f(-hw - 1)} {f(hy + 12)} Z"
    body = path(d, cloth, OUT, 3)
    body += line((-hw + 2, hy - 8), (hw - 2, hy - 8), darken(cloth, 0.35), 3, 0.8)
    if arch == "hoodie":
        body += line((0, hy - 8), (0, hy + 12), darken(cloth, 0.4), 2, 0.6)
    return body, (-hw - 8, hy - 18, hw + 8, hy + 30)


def skirt_part(P: dict, V: dict):
    """The bob's skirt: flares from the waist to above the knee, in front of the legs."""
    hy = -P["hip_y"]
    top = hy - 14
    bot = hy + 34
    w0, w1 = P["hw"] - 1, P["hw"] + 14
    d = f"M{f(-w0)} {f(top)} L{f(w0)} {f(top)} Q{f(w1 + 2)} {f((top + bot) / 2)} {f(w1)} {f(bot)} Q0 {f(bot + 7)} {f(-w1)} {f(bot)} Q{f(-w1 - 2)} {f((top + bot) / 2)} {f(-w0)} {f(top)} Z"
    c = V["bottom"]
    defs = clip("sc", f'<path d="{d}"/>')
    body = f'<path d="{d}" fill="{c}"/>'
    inner = ""
    for k in range(-4, 5):  # pleats
        inner += line((k * 4.5, top), (k * 6.6, bot + 6), darken(c, 0.35), 1.6, 0.55)
    inner += rect(-w1 - 4, bot - 5, w1 * 2 + 8, 7, V["top2"], None, op=0.95)
    inner += rect(w0 * 0.3, top, w1, bot - top + 8, "#150a33", None, op=0.18)
    body += group(inner, 'clip-path="url(#sc)"')
    body += path(d, None, OUT, 3)
    return defs, body, (-w1 - 8, top - 6, w1 + 8, bot + 12)


# ---- limbs -------------------------------------------------------------------------------------------------------------

def sleeve_color(arch: str, V: dict, part: str):
    """The colour of the arm covering for this archetype, or None for bare skin."""
    if arch == "hoodie":
        return V["top"]
    if arch == "curly":
        return V["top"] if part == "up" else V["top"]
    if arch == "ponytail" and part == "up":
        return V["top"]
    return None


def arm_parts(arch: str, P: dict, V: dict, J: dict, side: int):
    name = "l" if side < 0 else "r"
    s = J["shoulder_" + name]
    e = J["elbow_" + name]
    w = wrist(P, J, side)
    aw = P["aw"]
    skin = V["skin"]
    out = {}
    # upper arm
    sc = sleeve_color(arch, V, "up")
    c = sc or skin
    sh = darken(c, 0.25)
    li = lighten(c, 0.3)
    body = ""
    # outline: butt-ended line plus a round cap at the shoulder, so the elbow end has no seam against the forearm
    body += line(s, e, OUT, aw + 6, cap="butt")
    body += circle(s[0], s[1], aw / 2 + 3, OUT)
    body += line(s, e, c, aw, cap="round")
    dx, dy = e[0] - s[0], e[1] - s[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    off = -aw * 0.24 * (1 if side < 0 else -1) * -1
    off = aw * 0.24 * side
    body += line((s[0] + nx * off, s[1] + ny * off), (e[0] + nx * off, e[1] + ny * off), sh, aw * 0.4, 0.7)
    off2 = -aw * 0.26 * side
    body += line((s[0] + nx * off2, s[1] + ny * off2), (e[0] + nx * off2, e[1] + ny * off2), li, aw * 0.14, 0.65)
    if arch == "ponytail":  # cap sleeve edge
        m = (s[0] + (e[0] - s[0]) * 0.45, s[1] + (e[1] - s[1]) * 0.45)
        body += line(m, (m[0] + nx * 0.0, m[1]), OUT, 0)
        sleeve_end = (s[0] + (e[0] - s[0]) * 0.5, s[1] + (e[1] - s[1]) * 0.5)
        body = (line(s, e, OUT, aw + 6, cap="butt") + circle(s[0], s[1], aw / 2 + 3, OUT) + line(s, e, skin, aw, cap="round") +
                line((s[0] + nx * aw * 0.24 * side, s[1] + ny * aw * 0.24 * side), (e[0] + nx * aw * 0.24 * side, e[1] + ny * aw * 0.24 * side), darken(skin, 0.25), aw * 0.4, 0.7) +
                line(s, sleeve_end, OUT, aw + 5, cap="round") + line(s, sleeve_end, V["top"], aw + 0.5, cap="round") +
                line(sleeve_end, sleeve_end, V["top2"], 0))
        body += line((sleeve_end[0] - nx * (aw / 2 + 2), sleeve_end[1] - ny * (aw / 2 + 2)), (sleeve_end[0] + nx * (aw / 2 + 2), sleeve_end[1] + ny * (aw / 2 + 2)), V["top2"], 2.2, 0.9, cap="butt")
    if arch == "punk":  # studded wristband high on the arm
        m = (s[0] + (e[0] - s[0]) * 0.55, s[1] + (e[1] - s[1]) * 0.55)
        body += line((m[0] - nx * (aw / 2 + 1), m[1] - ny * (aw / 2 + 1)), (m[0] + nx * (aw / 2 + 1), m[1] + ny * (aw / 2 + 1)), "#1e1a2e", 5, cap="butt")
        body += circle(m[0], m[1], 1.5, V["accent"])
    if arch == "groover":  # tattoo band
        m = (s[0] + (e[0] - s[0]) * 0.5, s[1] + (e[1] - s[1]) * 0.5)
        body += line((m[0] - nx * aw / 2, m[1] - ny * aw / 2), (m[0] + nx * aw / 2, m[1] + ny * aw / 2), V["tip"], 3, 0.8, cap="butt")
    box_up = bbox([s, e], aw / 2 + 8)
    out["up"] = (body, box_up)
    # forearm + hand
    fc = sleeve_color(arch, V, "fore") or skin
    if arch == "ponytail":
        fc = skin
    if arch == "hoodie" or arch == "curly":
        fc = V["top"]
    body = circle(e[0], e[1], aw / 2 + 3, OUT)  # the elbow ring (hidden under the upper arm when straight)
    wr = (w[0], w[1])
    body += line(e, wr, OUT, aw + 6, cap="butt")
    body += circle(wr[0], wr[1], aw / 2 + 3, OUT)
    body += line(e, wr, fc, aw, cap="round")
    dx, dy = wr[0] - e[0], wr[1] - e[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    body += line((e[0] + nx * aw * 0.24 * side, e[1] + ny * aw * 0.24 * side), (wr[0] + nx * aw * 0.24 * side, wr[1] + ny * aw * 0.24 * side), darken(fc, 0.25), aw * 0.4, 0.7)
    body += line((e[0] - nx * aw * 0.26 * side, e[1] - ny * aw * 0.26 * side), (wr[0] - nx * aw * 0.26 * side, wr[1] - ny * aw * 0.26 * side), lighten(fc, 0.3), aw * 0.14, 0.65)
    ux, uy = dx / ln, dy / ln
    hand_c = (wr[0] + ux * aw * 0.28, wr[1] + uy * aw * 0.28)
    hr = aw * 0.62
    if arch in ("hoodie", "curly"):  # cuff
        cuff = (wr[0] - ux * 3, wr[1] - uy * 3)
        body += line((cuff[0] - nx * (aw / 2 + 2), cuff[1] - ny * (aw / 2 + 2)), (cuff[0] + nx * (aw / 2 + 2), cuff[1] + ny * (aw / 2 + 2)), darken(fc, 0.3), 5.5, cap="butt")
    if arch == "punk":
        cuff = (wr[0] - ux * 3, wr[1] - uy * 3)
        body += line((cuff[0] - nx * (aw / 2 + 1), cuff[1] - ny * (aw / 2 + 1)), (cuff[0] + nx * (aw / 2 + 1), cuff[1] + ny * (aw / 2 + 1)), "#1e1a2e", 6, cap="butt")
        body += circle(cuff[0], cuff[1], 1.4, V["accent"])
    if arch == "bob":
        cuff = (wr[0] - ux * 3, wr[1] - uy * 3)
        body += line((cuff[0] - nx * (aw / 2 + 1), cuff[1] - ny * (aw / 2 + 1)), (cuff[0] + nx * (aw / 2 + 1), cuff[1] + ny * (aw / 2 + 1)), V["accent"], 4, cap="butt")
    body += circle(hand_c[0], hand_c[1], hr + 2.6, OUT)
    body += circle(hand_c[0], hand_c[1], hr, skin)
    body += circle(hand_c[0] - nx * side * hr * 0.25, hand_c[1] - ny * side * hr * 0.25, hr * 0.4, lighten(skin, 0.3), None, op=0.6)
    out["fore"] = (body, bbox([e, wr, hand_c], aw / 2 + 10), (hand_c[0], hand_c[1]))
    return out


def leg_part(arch: str, P: dict, V: dict, J: dict, side: int):
    name = "l" if side < 0 else "r"
    h = J["hip_" + name]
    sh = P["shoe_h"]
    ax = h[0] + side * 2.0
    ay = -sh - 2
    lw = P["lw"]
    cloth = V["bottom"]
    skin = V["skin"]
    body = ""
    pts_ = [h, (ax, ay)]
    if arch == "ponytail":  # wide trousers
        wt, wb = lw * 1.05, lw * 1.75
        d = (f"M{f(h[0] - wt / 2)} {f(h[1] - 4)} L{f(h[0] + wt / 2)} {f(h[1] - 4)} L{f(ax + wb / 2)} {f(ay + 4)} L{f(ax - wb / 2)} {f(ay + 4)} Z")
        body += path(d, cloth, OUT, 3)
        body += path(f"M{f(h[0] + side * wt * 0.1)} {f(h[1] + 6)} L{f(ax + side * wb * 0.1)} {f(ay + 2)}", None, V["top2"], 2.4, 0.9)
        body += line((ax - wb / 2 + 1, ay + 3), (ax + wb / 2 - 1, ay + 3), darken(cloth, 0.4), 4, 0.8, cap="butt")
        body += rect(h[0] + 0, h[1], wt / 2 + 1, ay - h[1], "#150a33", None, op=0.0)
        body += f'<path d="M{f(h[0] + wt * 0.05)} {f(h[1])} L{f(h[0] + wt / 2)} {f(h[1])} L{f(ax + wb / 2)} {f(ay + 4)} L{f(ax + wb * 0.05)} {f(ay + 4)} Z" fill="#150a33" fill-opacity="0.2"/>'
        pts_ += [(ax - wb / 2, ay), (ax + wb / 2, ay)]
    elif arch == "bob":  # bare legs, sock and platform boot
        body += capsule(h, (ax, ay - 14), lw, skin, darken(skin, 0.25), lighten(skin, 0.3))
        body += line((ax, ay - 14), (ax, ay + 2), V["top2"], lw + 1.5, cap="butt")
        body += line((ax - lw / 2 - 0.5, ay - 14), (ax + lw / 2 + 0.5, ay - 14), V["accent"], 3, cap="butt")
        body += line((ax - lw / 2 - 1.2, ay - 14), (ax - lw / 2 - 1.2, ay + 2), OUT, 2.2, cap="butt")
        body += line((ax + lw / 2 + 1.2, ay - 14), (ax + lw / 2 + 1.2, ay + 2), OUT, 2.2, cap="butt")
    elif arch == "hoodie":  # joggers with cuffs
        body += capsule(h, (ax, ay - 4), lw, cloth, darken(cloth, 0.3), lighten(cloth, 0.25))
        body += line((ax, ay - 10), (ax, ay + 1), darken(cloth, 0.45), lw + 3, cap="butt")
        body += line((ax - lw / 2 - 1.5, ay - 4), (ax + lw / 2 + 1.5, ay - 4), V["accent"], 2.4, cap="butt")
    elif arch == "punk":  # tight trousers, ripped knee, tall boots
        body += capsule(h, (ax, ay - 20), lw, cloth, darken(cloth, 0.3), lighten(cloth, 0.2))
        km = (h[0] + (ax - h[0]) * 0.5, h[1] + (ay - h[1]) * 0.5)
        body += line((km[0] - lw * 0.25, km[1]), (km[0] + lw * 0.25, km[1] + 1), V["skin"], 3, cap="butt")
        body += line((km[0] - lw * 0.3, km[1] + 5), (km[0] + lw * 0.3, km[1] + 6), V["skin"], 2, cap="butt")
        boot = "#1e1a2e"
        body += capsule((ax, ay - 26), (ax, ay), lw + 5, boot, lighten(boot, 0.05), lighten(boot, 0.35))
        body += line((ax - lw / 2 - 2, ay - 18), (ax + lw / 2 + 2, ay - 18), V["accent"], 2, cap="butt")
        body += line((ax - lw / 2 - 2, ay - 10), (ax + lw / 2 + 2, ay - 10), V["accent"], 2, cap="butt")
    else:  # groover / curly: slim trousers
        body += capsule(h, (ax, ay), lw, cloth, darken(cloth, 0.3), lighten(cloth, 0.25))
        if arch == "groover":
            body += line((h[0] + side * lw * 0.3, h[1] + 4), (ax + side * lw * 0.3, ay), V["top2"], 2.2, 0.8)  # side stripe
        if arch == "curly":
            body += line((ax - lw / 2 - 1, ay - 6), (ax + lw / 2 + 1, ay - 6), darken(cloth, 0.45), 3, cap="butt")
    # shoes
    shoe = V["shoes"]
    fx = ax + side * 4
    if arch == "punk":
        body += path(f"M{f(ax - lw / 2 - 4)} {f(-5)} Q{f(fx + side * 9)} {f(-14)} {f(fx + side * 14)} {f(-4)} L{f(fx + side * 14)} 0 L{f(ax - lw / 2 - 4)} 0 Z", "#1e1a2e", OUT, 3)
        body += line((ax - lw / 2 - 3, -2), (fx + side * 13, -2), "#6d5d92", 3, 0.9, cap="butt")
        pts_ += [(fx + side * 16, 0)]
    elif arch == "hoodie":
        body += path(f"M{f(ax - 12)} {f(-3)} Q{f(ax - 14)} {f(-16)} {f(ax)} {f(-16)} Q{f(fx + side * 16)} {f(-16)} {f(fx + side * 18)} {f(-5)} Q{f(fx + side * 18)} 1 {f(fx + side * 10)} 1 L{f(ax - 10)} 1 Q{f(ax - 14)} 0 {f(ax - 12)} {f(-3)} Z", shoe, OUT, 3)
        body += rect(ax - 13, -3.5, 31 if side > 0 else 31, 4.5, V["accent"], None, op=0.0)
        body += line((ax - 12, -2), (fx + side * 17, -2), darken(shoe, 0.25), 4, cap="butt")
        pts_ += [(fx + side * 20, 0), (ax - 14, 0)]
    else:
        rx_ = 13 if arch != "bob" else 11
        body += path(f"M{f(ax - rx_ + 2)} {f(-4)} Q{f(ax - rx_)} {f(-13)} {f(ax)} {f(-13)} Q{f(fx + side * rx_)} {f(-13)} {f(fx + side * (rx_ + 3))} {f(-4)} Q{f(fx + side * (rx_ + 3))} 1 {f(fx + side * (rx_ - 2))} 1 L{f(ax - rx_ + 4)} 1 Q{f(ax - rx_ - 1)} 0 {f(ax - rx_ + 2)} {f(-4)} Z", shoe, OUT, 3)
        body += line((ax - rx_ + 3, -2), (fx + side * (rx_ + 2), -2), darken(shoe, 0.3) if arch != "groover" else V["top"], 3.2, cap="butt")
        body += line((ax - 4, -11), (ax + 5, -11), V["accent"], 1.8, 0.9)
        pts_ += [(fx + side * (rx_ + 5), 0), (ax - rx_ - 2, 0)]
    return body, bbox(pts_, lw / 2 + 12)


# ---- heads: skin, hair and faces ---------------------------------------------------------------------------------------------

def head_path(P: dict, grow: float = 0.0) -> str:
    rx, ry, cy = P["rx"] + grow, P["ry"] + grow, P["cy"]
    return (f"M{f(-rx)} {f(cy)} C{f(-rx)} {f(cy - ry * 1.32)} {f(rx)} {f(cy - ry * 1.32)} {f(rx)} {f(cy)} "
            f"C{f(rx)} {f(cy + ry * 0.78)} {f(rx * 0.55)} {f(cy + ry)} 0 {f(cy + ry)} "
            f"C{f(-rx * 0.55)} {f(cy + ry)} {f(-rx)} {f(cy + ry * 0.78)} {f(-rx)} {f(cy)} Z")


def head_part(arch: str, P: dict, V: dict):
    rx, ry, cy, ny = P["rx"], P["ry"], P["cy"], P["neck_y"]
    skin = V["skin"]
    d = head_path(P)
    defs = clip("hc", f'<path d="{d}"/>') + SHADE_GRAD
    body = ""
    # neck
    body += rect(-7.5, cy + ry * 0.55, 15, ny - (cy + ry * 0.55) + 14, darken(skin, 0.12), OUT, 2.6, rx=3)
    body += rect(-7.5, cy + ry * 0.78, 15, 9, "#150a33", None, op=0.18)
    # ears
    for side in (-1, 1):
        ex = side * (rx - 1)
        body += ellipse(ex, cy + 2, 4.6, 6.2, skin, OUT, 2.4)
        body += ellipse(ex + side * 0.4, cy + 2.5, 1.8, 3, darken(skin, 0.3), None, op=0.7)
        if arch == "punk":
            body += circle(ex + side * 0.5, cy + 8, 1.5, "#d8d8f0")
        if arch in ("ponytail", "bob"):
            body += circle(ex + side * 0.5, cy + 8.2, 1.8, V["accent"], OUT, 1)
    body += f'<path d="{d}" fill="{skin}"/>'
    inner = f'<rect x="{f(-rx - 4)}" y="{f(cy - ry * 1.3)}" width="{f(rx * 2 + 8)}" height="{f(ry * 2.5)}" fill="url(#shd)"/>'
    inner += f'<rect x="{f(-rx - 2)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="#19d2ff" fill-opacity="0.5"/>'
    inner += f'<rect x="{f(rx - 2.5)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="#ff2f9d" fill-opacity="0.4"/>'
    inner += ellipse(-rx * 0.32, cy - ry * 0.45, rx * 0.28, ry * 0.14, lighten(skin, 0.35), None, op=0.45)  # forehead glint
    if arch == "punk":  # shaved sides: a darker stubble tone above the ears
        inner += ellipse(-rx, cy - ry * 0.35, rx * 0.42, ry * 0.7, darken(skin, 0.3), None, op=0.55)
        inner += ellipse(rx, cy - ry * 0.35, rx * 0.42, ry * 0.7, darken(skin, 0.3), None, op=0.55)
    body += group(inner, 'clip-path="url(#hc)"')
    body += path(d, None, OUT, 3)
    box = (-rx - 14, cy - ry - 8, rx + 14, ny + 18)
    return defs, body, box


def _eye(cx, cy, rx, ry, pupil, lashes=False, side=1, look=0.0, lid=None, skin=None):
    out = ellipse(cx, cy, rx, ry, "#ffffff", OUT, 1.8)
    out += circle(cx + look * 1.5, cy + 0.8 + (look != 0) * 0, pupil, "#2a1b4e")
    out += circle(cx + look * 1.5 + pupil * 0.35, cy + 0.8 - pupil * 0.4, pupil * 0.33, "#ffffff")
    if lid is not None:  # a sagging lid covering the top of the eye
        out += path(f"M{f(cx - rx - 0.8)} {f(cy - ry - 1.5)} L{f(cx + rx + 0.8)} {f(cy - ry - 1.5)} L{f(cx + rx + 0.8)} {f(cy - ry + lid)} Q{f(cx)} {f(cy - ry + lid + 2.2)} {f(cx - rx - 0.8)} {f(cy - ry + lid)} Z", skin, OUT, 1.6)
    if lashes:
        for k in range(3):
            a = math.radians(-35 - k * 24)
            ox = side * (rx - 0.5)
            out += line((cx + ox + math.cos(a) * 0 * side, cy - 1.5), (cx + ox + side * (1.6 + k * 0.5), cy - 3.8 - k * 1.8), OUT, 1.5)
    return out


def face_overlay(arch: str, P: dict, V: dict, expr: str) -> tuple[str, tuple]:
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    skin = V["skin"]
    ex = rx * 0.43
    ey = cy + {"hoodie": 5.0, "punk": 2.5, "bob": 3.0}.get(arch, 2.0)
    er = 5.0 if arch not in ("hoodie",) else 4.4
    erx, ery = er, er * 1.25
    lashes = arch in ("ponytail", "bob")
    brow_c = {"groover": "#1b1330", "ponytail": "#2b1a24", "hoodie": "#1b1330", "curly": "#2b1a28", "bob": "#1b1330", "punk": "#1b1330"}[arch]
    body = ""
    blush = "#ff4f9a"
    mouth_y = cy + ry * 0.58
    if expr == "neutral":
        body += _eye(-ex, ey, erx, ery, 3.1, lashes, -1) + _eye(ex, ey, erx, ery, 3.1, lashes, 1)
        by_ = ey - ery - 4.5
        body += line((-ex - 5, by_ + 0.5), (-ex + 5, by_ - 0.6), brow_c, 2.4) + line((ex - 5, by_ - 0.6), (ex + 5, by_ + 0.5), brow_c, 2.4)
        body += path(f"M-5 {f(mouth_y)} Q0 {f(mouth_y + 3.2)} 5 {f(mouth_y)}", None, "#5a1f3a", 2.2)
    elif expr == "happy":
        body += _eye(-ex, ey, erx, ery * 0.88, 3.1, lashes, -1) + _eye(ex, ey, erx, ery * 0.88, 3.1, lashes, 1)
        body += path(f"M{f(-ex - 5)} {f(ey + ery * 0.9 + 2)} Q{f(-ex)} {f(ey + ery * 0.9 - 0.5)} {f(-ex + 5)} {f(ey + ery * 0.9 + 2)}", None, darken(skin, 0.3), 1.4, sop=0.8)
        body += path(f"M{f(ex - 5)} {f(ey + ery * 0.9 + 2)} Q{f(ex)} {f(ey + ery * 0.9 - 0.5)} {f(ex + 5)} {f(ey + ery * 0.9 + 2)}", None, darken(skin, 0.3), 1.4, sop=0.8)
        by_ = ey - ery - 6.2
        body += path(f"M{f(-ex - 5)} {f(by_ + 1.8)} Q{f(-ex)} {f(by_ - 1.6)} {f(-ex + 5)} {f(by_ + 0.8)}", None, brow_c, 2.4)
        body += path(f"M{f(ex - 5)} {f(by_ + 0.8)} Q{f(ex)} {f(by_ - 1.6)} {f(ex + 5)} {f(by_ + 1.8)}", None, brow_c, 2.4)
        body += path(f"M-7 {f(mouth_y - 1)} Q0 {f(mouth_y + 9)} 7 {f(mouth_y - 1)} Q0 {f(mouth_y + 2.6)} -7 {f(mouth_y - 1)} Z", "#7a1f45", OUT, 1.6)
        body += path(f"M-5.6 {f(mouth_y - 0.2)} Q0 {f(mouth_y + 2.8)} 5.6 {f(mouth_y - 0.2)} L5 {f(mouth_y + 1.4)} Q0 {f(mouth_y + 3.8)} -5 {f(mouth_y + 1.4)} Z", "#ffffff", None)
        body += ellipse(-ex - 3, ey + 8, 4.5, 2.6, blush, None, op=0.38) + ellipse(ex + 3, ey + 8, 4.5, 2.6, blush, None, op=0.38)
    elif expr == "cheer":
        for sx in (-1, 1):  # closed laughing eyes
            body += path(f"M{f(sx * ex - 5)} {f(ey + 1.4)} Q{f(sx * ex)} {f(ey - 6.5)} {f(sx * ex + 5)} {f(ey + 1.4)}", None, "#2a1b4e", 2.8)
        by_ = ey - ery - 8.4
        body += path(f"M{f(-ex - 5.5)} {f(by_ + 2.4)} Q{f(-ex)} {f(by_ - 2.4)} {f(-ex + 5.5)} {f(by_ + 1.2)}", None, brow_c, 2.6)
        body += path(f"M{f(ex - 5.5)} {f(by_ + 1.2)} Q{f(ex)} {f(by_ - 2.4)} {f(ex + 5.5)} {f(by_ + 2.4)}", None, brow_c, 2.6)
        my = mouth_y - 3.2
        body += path(f"M-9 {f(my)} L9 {f(my)} Q8 {f(my + 14)} 0 {f(my + 14)} Q-8 {f(my + 14)} -9 {f(my)} Z", "#6e1540", OUT, 2)
        body += path(f"M-8 {f(my + 0.8)} L8 {f(my + 0.8)} L7.4 {f(my + 4.4)} L-7.4 {f(my + 4.4)} Z", "#ffffff", None)
        body += ellipse(0, my + 11, 4.8, 3.2, "#ff6f9c", None)
        body += ellipse(-ex - 3.5, ey + 8.5, 5, 3, blush, None, op=0.5) + ellipse(ex + 3.5, ey + 8.5, 5, 3, blush, None, op=0.5)
    else:  # sad: sagging lids, worried brows, frown, a sweat drop
        body += _eye(-ex, ey + 1, erx, ery * 0.9, 3.0, lashes, -1, look=-0.6, lid=ery * 0.9, skin=skin)
        body += _eye(ex, ey + 1, erx, ery * 0.9, 3.0, lashes, 1, look=-0.6, lid=ery * 0.9, skin=skin)
        by_ = ey - ery - 3.4
        body += line((-ex - 5.5, by_ + 3.2), (-ex + 4.5, by_ - 2.6), brow_c, 2.5) + line((ex - 4.5, by_ - 2.6), (ex + 5.5, by_ + 3.2), brow_c, 2.5)
        body += path(f"M-5.6 {f(mouth_y + 3.6)} Q0 {f(mouth_y - 2.4)} 5.6 {f(mouth_y + 3.6)}", None, "#5a1f3a", 2.4)
        body += path(f"M{f(rx * 0.72)} {f(cy - ry * 0.35)} Q{f(rx * 0.95)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy + ry * 0.1)} Q{f(rx * 0.5)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy - ry * 0.35)} Z", "#8fe6ff", OUT, 1.4)
    nose_y = cy + ry * 0.3
    body += path(f"M-1.8 {f(nose_y)} Q0.4 {f(nose_y + 3.6)} 2.8 {f(nose_y + 1.8)}", None, darken(skin, 0.42), 1.5, sop=0.85)
    if arch == "curly":  # round magenta glasses over every expression
        for sx in (-1, 1):
            body += circle(sx * ex, ey + 0.3, 8.6, "#ffffff", None, op=0.14)
            body += circle(sx * ex, ey + 0.3, 8.6, None, V["accent"], 2.4)
            body += line((sx * ex - 4, ey - 4), (sx * ex - 1, ey - 6.5), "#ffffff", 1.6, 0.6)
        body += path(f"M{f(-ex + 8.4)} {f(ey - 0.5)} Q0 {f(ey - 3.4)} {f(ex - 8.4)} {f(ey - 0.5)}", None, V["accent"], 2.2)
    if arch == "punk":  # studs in one brow and the lip
        body += circle(ex + 4, ey - ery - 7.0, 1.4, "#e8e8ff") + circle(ex + 6.2, ey - ery - 6.0, 1.4, "#e8e8ff")
        body += line((-ex - 5.5, ey - 1.0), (-ex - 8.4, ey - 2.2), OUT, 1.6) + line((ex + 5.5, ey - 1.0), (ex + 8.4, ey - 2.2), OUT, 1.6)
    if arch == "bob":  # freckles
        for fx_, fy_ in ((-ex - 2, ey + 6), (-ex + 1.8, ey + 7.2), (-ex - 4.2, ey + 8.4), (ex + 2, ey + 6), (ex - 1.8, ey + 7.2), (ex + 4.2, ey + 8.4)):
            body += circle(fx_, fy_, 0.8, darken(skin, 0.38), None, op=0.8)
    if arch == "groover":  # a small beauty mark and sharp stubble line
        body += circle(ex + 6, ey + 10, 0.9, darken(skin, 0.5), None, op=0.8)
    return body, (-rx - 8, cy - ry - 6, rx + 8, cy + ry + 6)


def _spikes(cx, cy, r0, tips, color, tip_color, base_w=7.0, outline=True):
    """Triangular spikes radiating from (cx, cy); tips = [(angle_deg, length)]."""
    out = ""
    for ang, ln in tips:
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        b0 = (cx + ca * r0 - sa * base_w, cy + sa * r0 + ca * base_w)
        b1 = (cx + ca * r0 + sa * base_w, cy + sa * r0 - ca * base_w)
        tip = (cx + ca * (r0 + ln), cy + sa * (r0 + ln))
        out += poly([b0, tip, b1], color, OUT, 2.6)
        mid = ((b0[0] + b1[0]) / 2 + ca * ln * 0.55, (b0[1] + b1[1]) / 2 + sa * ln * 0.55)
        out += poly([(b0[0] * 0.45 + mid[0] * 0.55, b0[1] * 0.45 + mid[1] * 0.55), tip, (b1[0] * 0.45 + mid[0] * 0.55, b1[1] * 0.45 + mid[1] * 0.55)], tip_color, None)
    return out


def hair_parts(arch: str, P: dict, V: dict) -> dict:
    """Returns {"back": (body, box, pivot, swing) or None, "front": (body, box) or None, "extra": [...]}"""
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    hair, tip, acc = V["hair"], V["tip"], V["accent"]
    hl = lighten(hair, 0.28)
    out: dict = {"back": None, "front": None}
    if arch == "groover":
        spikes = [(-160, 20), (-140, 25), (-122, 30), (-105, 33), (-90, 36), (-74, 32), (-58, 28), (-40, 24), (-22, 18)]
        back = _spikes(0, cy, ry * 0.8, [(a - 4, l * 0.8) for a, l in spikes], darken(hair, 0.3), darken(tip, 0.35))
        out["back"] = (back, (-rx - 34, cy - ry - 44, rx + 34, cy + 6), None, False)
        front = ""
        cap = (f"M{f(-rx - 2.5)} {f(cy + 8)} C{f(-rx - 4)} {f(cy - ry * 1.55)} {f(rx + 4)} {f(cy - ry * 1.55)} {f(rx + 2.5)} {f(cy + 8)} "
               f"L{f(rx - 1)} {f(cy - 6)} L{f(rx * 0.7)} {f(cy - ry * 0.52)} L{f(rx * 0.35)} {f(cy - ry * 0.34)} L0 {f(cy - ry * 0.56)} L{f(-rx * 0.38)} {f(cy - ry * 0.34)} "
               f"L{f(-rx * 0.72)} {f(cy - ry * 0.55)} L{f(-rx + 1)} {f(cy - 6)} Z")
        front += _spikes(0, cy, ry * 0.9, spikes, hair, tip)
        front += path(cap, hair, OUT, 3)
        front += path(f"M{f(-rx * 0.6)} {f(cy - ry * 0.95)} Q{f(-rx * 0.1)} {f(cy - ry * 1.25)} {f(rx * 0.4)} {f(cy - ry * 1.1)}", None, hl, 3, 0.8)
        out["front"] = (front, (-rx - 30, cy - ry - 48, rx + 30, cy + 14))
    elif arch == "ponytail":
        # the ponytail swings from a scrunchie on the right of the crown
        ax_, ay_ = rx * 0.78, cy - ry * 0.7
        tail = (f"M{f(ax_ - 4)} {f(ay_)} C{f(ax_ + 22)} {f(ay_ - 6)} {f(ax_ + 36)} {f(ay_ + 28)} {f(ax_ + 30)} {f(ay_ + 62)} "
                f"C{f(ax_ + 28)} {f(ay_ + 76)} {f(ax_ + 18)} {f(ay_ + 86)} {f(ax_ + 12)} {f(ay_ + 70)} C{f(ax_ + 14)} {f(ay_ + 46)} {f(ax_ + 8)} {f(ay_ + 22)} {f(ax_ - 6)} {f(ay_ + 8)} Z")
        body = path(tail, hair, OUT, 3)
        body += path(f"M{f(ax_ + 8)} {f(ay_ + 6)} C{f(ax_ + 22)} {f(ay_ + 16)} {f(ax_ + 26)} {f(ay_ + 40)} {f(ax_ + 22)} {f(ay_ + 64)}", None, hl, 3, 0.7)
        body += path(f"M{f(ax_ + 28)} {f(ay_ + 60)} C{f(ax_ + 26)} {f(ay_ + 74)} {f(ax_ + 20)} {f(ay_ + 82)} {f(ax_ + 14)} {f(ay_ + 74)}", tip, None, 5, 0.9)
        body += ellipse(ax_ - 1, ay_ + 2, 7.5, 6, acc, OUT, 2.4)
        out["back"] = (body, (ax_ - 14, ay_ - 12, ax_ + 46, ay_ + 96), (ax_ - 1, ay_ + 2), True)
        cap = (f"M{f(-rx - 2.5)} {f(cy + 6)} C{f(-rx - 4)} {f(cy - ry * 1.5)} {f(rx + 4)} {f(cy - ry * 1.5)} {f(rx + 2.5)} {f(cy + 6)} "
               f"L{f(rx - 1)} {f(cy - 10)} C{f(rx * 0.4)} {f(cy - ry * 0.3)} {f(-rx * 0.2)} {f(cy - ry * 0.62)} {f(-rx * 0.6)} {f(cy - ry * 0.45)} "
               f"C{f(-rx * 0.8)} {f(cy - ry * 0.3)} {f(-rx + 1)} {f(cy - 2)} {f(-rx + 1)} {f(cy + 6)} Z")
        front = path(cap, hair, OUT, 3)
        front += path(f"M{f(-rx * 0.7)} {f(cy - ry * 1.0)} Q{f(-rx * 0.1)} {f(cy - ry * 1.25)} {f(rx * 0.55)} {f(cy - ry * 1.0)}", None, hl, 3, 0.8)
        front += path(f"M{f(-rx * 0.5)} {f(cy - ry * 0.55)} Q{f(-rx * 0.2)} {f(cy - ry * 0.8)} {f(rx * 0.1)} {f(cy - ry * 0.62)}", None, darken(hair, 0.4), 2, 0.6)
        out["front"] = (front, (-rx - 10, cy - ry - 12, rx + 12, cy + 12))
    elif arch == "hoodie":  # cap with a brim, hood bunched behind
        crown = (f"M{f(-rx - 3)} {f(cy - ry * 0.28)} C{f(-rx - 6)} {f(cy - ry * 1.6)} {f(rx + 6)} {f(cy - ry * 1.6)} {f(rx + 3)} {f(cy - ry * 0.28)} Z")
        capc = V["top2"] if V["top2"] != V["top"] else "#ffffff"
        capc = mix(capc, V["accent"], 0.0)
        body = path(crown, capc, OUT, 3)
        body += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.12)} Q0 {f(cy - ry * 1.3)} {f(rx * 0.5)} {f(cy - ry * 1.12)}", None, "#ffffff", 3, 0.6)
        body += f'<path d="M{f(rx * 0.15)} {f(cy - ry * 1.4)} L{f(rx + 6)} {f(cy - ry * 0.28)} L{f(rx * 0.15)} {f(cy - ry * 0.28)} Z" fill="#150a33" fill-opacity="0.16"/>'
        body += circle(0, cy - ry * 0.92, 4.8, V["accent"], OUT, 1.8)  # cap badge
        body += path(f"M{f(-rx - 6)} {f(cy - ry * 0.28)} Q0 {f(cy - ry * 0.05)} {f(rx + 6)} {f(cy - ry * 0.28)} Q0 {f(cy - ry * 0.78)} {f(-rx - 6)} {f(cy - ry * 0.28)} Z", darken(V["top"], 0.15), OUT, 3)
        body += path(f"M{f(-rx - 3)} {f(cy - ry * 0.34)} Q0 {f(cy - ry * 0.62)} {f(rx + 3)} {f(cy - ry * 0.34)}", None, lighten(V["top"], 0.3), 2, 0.7)
        out["front"] = (body, (-rx - 14, cy - ry - 14, rx + 14, cy + 8))
        back = path(f"M{f(-rx * 0.9)} {f(cy - 4)} Q{f(-rx - 4)} {f(cy + ry * 0.7)} {f(-rx * 0.5)} {f(cy + ry * 0.85)} L{f(rx * 0.5)} {f(cy + ry * 0.85)} Q{f(rx + 4)} {f(cy + ry * 0.7)} {f(rx * 0.9)} {f(cy - 4)} Z", V["hair"], OUT, 3)
        out["back"] = (back, (-rx - 10, cy - 10, rx + 10, cy + ry + 6), None, False)
    elif arch == "curly":  # a big cloud of curls
        import random
        rng = random.Random(41)
        bk = ""
        centres = []
        for k in range(13):
            a = math.radians(-190 + k * (200 / 12.0))
            r_ = rx * 1.05 + 3
            centres.append((math.cos(a) * r_ * 1.18, cy - 2 + math.sin(a) * (ry * 1.02 + 2), 12.5 + rng.random() * 4.5))
        for (x, y, r_) in centres:
            bk += circle(x, y, r_, hair, OUT, 3)
        for (x, y, r_) in centres:
            bk += circle(x, y, r_ - 1.4, darken(hair, 0.0), None)
        for (x, y, r_) in centres[::2]:
            bk += path(f"M{f(x - r_ * 0.5)} {f(y - r_ * 0.1)} Q{f(x)} {f(y - r_ * 0.7)} {f(x + r_ * 0.5)} {f(y - r_ * 0.1)}", None, hl, 2.0, 0.6)
        bk += circle(rx * 0.5, cy - ry * 0.92, 5, V["tip"], OUT, 1.8)
        out["back"] = (bk, (-rx - 42, cy - ry - 36, rx + 42, cy + ry * 0.9), None, False)
        fr = ""
        fcs = [(-rx * 0.74, cy - ry * 0.78, 8.8), (-rx * 0.28, cy - ry * 0.98, 9.8), (rx * 0.22, cy - ry * 1.0, 10.0), (rx * 0.7, cy - ry * 0.78, 9.0),
               (-rx * 0.9, cy - ry * 0.3, 7.5), (rx * 0.92, cy - ry * 0.3, 7.5)]
        for (x, y, r_) in fcs:
            fr += circle(x, y, r_, hair, OUT, 2.8)
        for (x, y, r_) in fcs:
            fr += circle(x, y, r_ - 1.2, hair, None)
        fr += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.0)} Q0 {f(cy - ry * 1.22)} {f(rx * 0.5)} {f(cy - ry * 1.0)}", None, hl, 2.6, 0.65)
        out["front"] = (fr, (-rx - 14, cy - ry - 16, rx + 14, cy + 6))
    elif arch == "bob":
        bk = path(f"M{f(-rx - 10)} {f(cy - 4)} C{f(-rx - 14)} {f(cy - ry * 1.7)} {f(rx + 14)} {f(cy - ry * 1.7)} {f(rx + 10)} {f(cy - 4)} "
                  f"L{f(rx + 9)} {f(cy + ry * 0.7)} Q{f(rx + 4)} {f(cy + ry * 0.92)} {f(rx - 5)} {f(cy + ry * 0.8)} L{f(-rx + 5)} {f(cy + ry * 0.8)} Q{f(-rx - 4)} {f(cy + ry * 0.92)} {f(-rx - 9)} {f(cy + ry * 0.7)} Z", hair, OUT, 3)
        out["back"] = (bk, (-rx - 22, cy - ry - 18, rx + 22, cy + ry + 4), (0, cy - ry * 0.8), True)
        fr = (f"M{f(-rx - 3)} {f(cy + ry * 0.58)} C{f(-rx - 7)} {f(cy - ry * 1.5)} {f(rx + 7)} {f(cy - ry * 1.5)} {f(rx + 3)} {f(cy + ry * 0.58)} "
              f"L{f(rx - 3)} {f(cy + ry * 0.5)} L{f(rx - 2)} {f(cy - 2)} L{f(rx * 0.6)} {f(cy - ry * 0.46)} L{f(-rx * 0.6)} {f(cy - ry * 0.46)} L{f(-rx + 2)} {f(cy - 2)} L{f(-rx + 3)} {f(cy + ry * 0.5)} Z")
        body = path(fr, hair, OUT, 3)
        body += path(f"M{f(-rx * 0.5)} {f(cy - ry * 1.05)} Q{f(rx * 0.1)} {f(cy - ry * 1.3)} {f(rx * 0.65)} {f(cy - ry * 0.95)}", None, hl, 3, 0.75)
        body += path(f"M{f(-rx - 1)} {f(cy + ry * 0.36)} L{f(-rx - 1)} {f(cy + ry * 0.56)}", None, V["tip"], 4.2, 0.95)
        body += path(f"M{f(rx * 0.5)} {f(cy - ry * 0.52)} L{f(rx * 0.55)} {f(cy - ry * 0.22)}", None, V["tip"], 3, 0.9)
        out["front"] = (body, (-rx - 16, cy - ry - 14, rx + 16, cy + ry * 0.8))
    elif arch == "punk":
        crest = [(-98, 40), (-90, 49), (-82, 44), (-73, 38), (-107, 36), (-65, 30), (-116, 28)]
        back = _spikes(0, cy, ry * 0.8, [(a, l * 0.85) for a, l in crest], darken(hair, 0.3), darken(V["tip"], 0.45), base_w=6)
        out["back"] = (back, (-rx - 30, cy - ry - 56, rx + 30, cy + 4), None, False)
        fr = ""
        cap = (f"M{f(-rx * 0.46)} {f(cy - ry * 0.3)} C{f(-rx * 0.5)} {f(cy - ry * 1.3)} {f(rx * 0.5)} {f(cy - ry * 1.3)} {f(rx * 0.46)} {f(cy - ry * 0.3)} "
               f"L{f(rx * 0.2)} {f(cy - ry * 0.42)} L0 {f(cy - ry * 0.26)} L{f(-rx * 0.2)} {f(cy - ry * 0.42)} Z")
        fr += _spikes(0, cy, ry * 0.88, [(-96, 44), (-84, 52), (-106, 40), (-74, 40), (-116, 30), (-64, 30)], hair, V["tip"], base_w=6.4)
        fr += path(cap, hair, OUT, 3)
        fr += path(f"M{f(-rx * 0.2)} {f(cy - ry * 0.98)} Q0 {f(cy - ry * 1.12)} {f(rx * 0.2)} {f(cy - ry * 0.98)}", None, V["tip"], 3, 0.8)
        out["front"] = (fr, (-rx - 28, cy - ry - 62, rx + 28, cy + 4))
    return out


# ---- assembly --------------------------------------------------------------------------------------------------------------

def build_variant(arch: str, variant: str) -> dict:
    P = ARCH[arch]
    V = VARIANTS[arch][variant]
    J = skeleton(P)
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
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        body, box = leg_part(arch, P, V, J, side)
        emit(f"leg_{n}", f"hip_{n}", -10, body, box)
    pel = pelvis_part(arch, P, V)
    if pel:
        emit("pelvis", "hips", -5, pel[0], pel[1])
    defs, body, box = torso_part(arch, P, V)
    emit("torso", "torso", 0, body, box, defs)
    if arch == "bob":
        defs, body, box = skirt_part(P, V)
        emit("skirt", "hips", 2, body, box, defs)
    if arch == "hoodie":  # hood bunched behind the neck, drawn on the torso
        sw = P["sw"]
        ts = P["sh_y"] - 8
        hood = path(f"M-24 {f(ts - 2)} Q-30 {f(ts - 22)} -10 {f(ts - 24)} L10 {f(ts - 24)} Q30 {f(ts - 22)} 24 {f(ts - 2)} Q0 {f(ts + 14)} -24 {f(ts - 2)} Z", darken(V["top"], 0.22), OUT, 3)
        emit("hood", "torso", -2, hood, (-34, ts - 32, 34, ts + 22))
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
        body, box = hair["front"]
        emit("hair_front", "head", 20, body, box)
    hand = arms["r"]["fore"][2]
    # the hand position inside the right forearm texture (texture px), for glow sticks
    fore_r = [p for p in parts if p["name"] == "arm_r_fore"][0]
    fb = arms["r"]["fore"][1]
    hand_px = [round((hand[0] - math.floor(fb[0])) * 2, 1), round((hand[1] - math.floor(fb[1])) * 2, 1)]
    fore_l = [p for p in parts if p["name"] == "arm_l_fore"][0]
    fbl = arms["l"]["fore"][1]
    handl = arms["l"]["fore"][2]
    hand_px_l = [round((handl[0] - math.floor(fbl[0])) * 2, 1), round((handl[1] - math.floor(fbl[1])) * 2, 1)]
    top = min(p for p in [P["cy"] - P["ry"] - 50 if arch in ("groover", "punk", "curly") else P["cy"] - P["ry"] - 6])
    return {
        "parts": parts, "faces": faces, "face_z": 12,
        "glow_hand": {"joint": "elbow_r", "at": hand_px, "joint_l": "elbow_l", "at_l": hand_px_l},
        "head_top": top,
    }


def build_all() -> dict:
    archetypes = {}
    for arch in ARCH:
        P = ARCH[arch]
        J = skeleton(P)
        entry = {
            "height": int(-(P["cy"] - P["ry"] - (40 if arch in ("groover", "punk") else 12 if arch != "curly" else 34))),
            "joints": {k: [round(v[0], 1), round(v[1], 1)] for k, v in J.items()},
            "variants": {},
        }
        for variant in VARIANTS[arch]:
            v = build_variant(arch, variant)
            entry["variants"][variant] = {"parts": v["parts"], "faces": v["faces"], "face_z": v["face_z"], "glow_hand": v["glow_hand"]}
        archetypes[arch] = entry
    return archetypes
