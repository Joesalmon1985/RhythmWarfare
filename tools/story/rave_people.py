#!/usr/bin/env python3
"""The clubgoers of the three new raves (docs/briefs/BEDSIT_RAVES_BRIEF.md section 3): themed rigs made from the Mothership's alien rigs (tools/story/art/alien_chars.py), same joints, same part names,
same four faces, so StoryCharacter and the crowd directives drive them unchanged. PLACEHOLDER art in the sense of the brief: recolours with a prop added to the head, not new anatomy.

    magic      pastel and iridescent (pink, lilac, cyan, mint, gold) with a spiral unicorn horn on every forehead
    dinos      scaled greens, oranges and teals with a row of crest spikes along the head and two brow horns
    transport  hi-vis orange, yellow and lime suits with two reflective bands on the torso and a hard hat

    build(theme) writes assets/story/<art>/source/chars/<arch>_<a|b>/*.svg and returns the manifest `archetypes` block (paths relative to the art folder).
The recolour keeps the shading of the original SVGs: every colour is mapped by the role it plays (skin, suit, trim, accent, iris: the nearest original role by hue) onto the theme's colour for that
role, keeping its lightness relative to the role's own. Outline and shadow indigo, white and greys are left alone.
"""
from __future__ import annotations

import colorsys
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from art import lib  # noqa: E402

ROLES = ("skin", "suit", "trim", "accent", "iris")

# theme palettes per archetype and variant: skin, suit, trim, accent, iris
PALETTES = {
    "magic": {
        "grey": {"a": ("#ff9ad8", "#6a4cff", "#7ff0ff", "#ffe27a", "#7a4cff"), "b": ("#5ae8c8", "#ff5ab8", "#fff0fa", "#7ff0ff", "#ff4fc8")},
        "antenna": {"a": ("#ffb0e8", "#4a3ad8", "#8fffd0", "#ffe27a", "#ff4fc8"), "b": ("#8ac8ff", "#e83ab8", "#fff0a0", "#7ff0ff", "#6a4cff")},
        "blob": {"a": ("#6af0c8", "#c8a0ff", "#fff0ff", "#ffe36a", "#2a1a5a"), "b": ("#ff8ad8", "#80d8ff", "#ffffff", "#ff7ad8", "#2a1a5a")},
        "insect": {"a": ("#c890ff", "#5a3ae0", "#ff7ad8", "#ffe27a", "#2a1a5a"), "b": ("#7af0d0", "#ff7ab8", "#7ff0ff", "#ffffff", "#2a1a5a")},
        "cyclops": {"a": ("#ffa0c8", "#20c8b8", "#ffe27a", "#ff4fc8", "#7a4cff"), "b": ("#a0b8ff", "#ff90e0", "#ff7ad8", "#7ff0ff", "#20c8b8")},
        "tentacle": {"a": ("#b890ff", "#20d8c0", "#fff0a0", "#ff7ad8", "#ffe27a"), "b": ("#80f0c0", "#ff6ad0", "#ffffff", "#9a70ff", "#ff4fc8")},
    },
    "dinos": {
        "grey": {"a": ("#7cc450", "#f0a030", "#ffe27a", "#ff5a2a", "#ffcf3a"), "b": ("#e8883a", "#3a8a50", "#ffd23f", "#9a3f1a", "#ffee66")},
        "antenna": {"a": ("#5fa83a", "#8a4a1a", "#e8c83a", "#ff5a2a", "#ffcf3a"), "b": ("#3fb0a0", "#d8d070", "#ff8a3a", "#7a3a8a", "#ffee66")},
        "blob": {"a": ("#8ad860", "#c8e890", "#fff2c0", "#ffe36a", "#3a2a10"), "b": ("#f0a050", "#ffd890", "#fff0d0", "#19d2ff", "#3a2a10")},
        "insect": {"a": ("#98c83a", "#4a7a1c", "#ff8a2a", "#ffe36a", "#3a2a10"), "b": ("#e8a030", "#a04a1a", "#3fd0b0", "#ff5a2a", "#3a2a10")},
        "cyclops": {"a": ("#6ab84a", "#d89030", "#ffe27a", "#ff5a2a", "#ffcf3a"), "b": ("#b87a3a", "#3a9a70", "#ffc23f", "#e8503a", "#ffee66")},
        "tentacle": {"a": ("#58b87a", "#e8a030", "#fff0a0", "#ff6a3a", "#ffe27a"), "b": ("#d8803a", "#2a8a7a", "#fff0c4", "#9a70ff", "#ffee66")},
    },
    "transport": {
        "grey": {"a": ("#c8d0d8", "#ff8a1f", "#e8f4ff", "#ffd23f", "#2a6aff"), "b": ("#b8c4b0", "#f0e020", "#e8f4ff", "#ff5a1f", "#2a6aff")},
        "antenna": {"a": ("#e8c8a0", "#1f3a8a", "#ffd23f", "#ff8a1f", "#ff8a1f"), "b": ("#a8d8c0", "#ff8a1f", "#e8f4ff", "#f0e020", "#1f3a8a")},
        "blob": {"a": ("#d8e8a0", "#f0e020", "#fffbe0", "#ff8a1f", "#1f2a3a"), "b": ("#a8c8f0", "#ff8a1f", "#ffffff", "#f0e020", "#1f2a3a")},
        "insect": {"a": ("#b8d860", "#ff8a1f", "#e8f4ff", "#f0e020", "#1f2a3a"), "b": ("#e8b060", "#a8e020", "#e8f4ff", "#ff5a1f", "#1f2a3a")},
        "cyclops": {"a": ("#e8a878", "#f0e020", "#2a6aff", "#ff8a1f", "#2a6aff"), "b": ("#a8b8d0", "#ff8a1f", "#e8f4ff", "#2a6aff", "#f0e020")},
        "tentacle": {"a": ("#c8a8e8", "#ff8a1f", "#e8f4ff", "#f0e020", "#2a6aff"), "b": ("#a8e0c8", "#f0e020", "#2a3a8a", "#ff8a1f", "#ff5a1f")},
    },
}
HAT = {"transport": {"a": ("#ffd23f", "#b8861a"), "b": ("#f4f4f4", "#9aa0a8")}}
CREST = {"dinos": {"a": ("#ff8a2a", "#a8481a"), "b": ("#3fd0b0", "#1a7a66")}}
HORN = ("#fff4c8", "#ff7ad8", "#7ff0ff")
EXEMPT = {c.lower() for c in HORN} | {c.lower() for v in CREST["dinos"].values() for c in v} | {c.lower() for v in HAT["transport"].values() for c in v} | {"#fff2c0", "#e8f4ff", "#9aa6b8"}


def hexrgb(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def rgbhex(rgb) -> str:
    return "#" + "".join("%02x" % max(0, min(255, int(round(v * 255)))) for v in rgb)


class Recolour:
    """Maps the colours of one original rig (arch, variant) onto the theme's, role by role."""

    def __init__(self, orig: tuple, new: tuple):
        self.o = [colorsys.rgb_to_hsv(*hexrgb(c)) for c in orig]
        self.n = [colorsys.rgb_to_hsv(*hexrgb(c)) for c in new]
        self.cache = {}

    def __call__(self, c: str) -> str:
        c = c.lower()
        if c in self.cache:
            return self.cache[c]
        h, s, v = colorsys.rgb_to_hsv(*hexrgb(c))
        out = c
        if c not in EXEMPT and s > 0.18 and v > 0.28:  # white, greys and the indigo outline stay
            best, bd = 0, 9.0
            for i, (oh, os_, ov) in enumerate(self.o):
                d = min(abs(h - oh), 1.0 - abs(h - oh)) + 0.25 * abs(s - os_)
                if d < bd:
                    best, bd = i, d
            oh, os_, ov = self.o[best]
            nh, ns, nv = self.n[best]
            h2 = (nh + (h - oh + 0.5) % 1.0 - 0.5) % 1.0
            s2 = max(0.0, min(1.0, s * (ns / os_ if os_ > 0.05 else 1.0)))
            v2 = max(0.0, min(1.0, v * (nv / ov if ov > 0.05 else 1.0)))
            out = rgbhex(colorsys.hsv_to_rgb(h2, s2, v2))
        self.cache[c] = out
        return out


def _patched(theme: str):
    """alien_chars with the theme's head and torso props added."""
    from art import alien_chars as ch
    from art.lib import f
    head0, torso0 = ch.head_part, ch.torso_part

    def head(arch, P, V):
        defs, body, box = head0(arch, P, V)
        rx, ry, cy = P["rx"], P["ry"], P["cy"]
        x0, y0, x1, y1 = box
        var = "a" if V is ch.VARIANTS[arch]["a"] else "b"
        if theme == "magic":  # a spiral horn on the forehead
            hy = cy - ry * 0.92
            horn = ('<path d="M%s %s L0 %s L%s %s Z" fill="%s" stroke="#1b1040" stroke-width="2.4" stroke-linejoin="round"/>' % (f(-7), f(hy), f(cy - ry - 38), f(7), f(hy), HORN[0]))
            for k, col in enumerate((HORN[1], HORN[2], HORN[1])):
                yy = hy - 6 - k * 7
                horn += '<path d="M%s %s L%s %s" stroke="%s" stroke-width="2.2" stroke-linecap="round" fill="none"/>' % (f(-4.4 + k * 1.2), f(yy), f(4.4 - k * 1.2), f(yy - 3), col)
            horn += '<circle cx="0" cy="%s" r="2.8" fill="#ffffff"/>' % f(cy - ry - 38)
            body += horn
            y0 = min(y0, cy - ry - 44)
        elif theme == "dinos":  # crest spikes behind the head, two brow horns in front
            c1, c2 = CREST["dinos"][var]
            spikes = ""
            for k in range(-2, 3):
                bx = k * rx * 0.34
                by = cy - ry * (0.98 - 0.06 * abs(k))
                h = 18 - 3 * abs(k)
                spikes += '<path d="M%s %s L%s %s L%s %s Z" fill="%s" stroke="#1b1040" stroke-width="2.2" stroke-linejoin="round"/>' % (f(bx - 6), f(by + 4), f(bx), f(by - h), f(bx + 6), f(by + 4), c1 if k % 2 == 0 else c2)
            body = spikes + body
            for s in (-1, 1):
                body += '<path d="M%s %s L%s %s L%s %s Z" fill="#fff2c0" stroke="#1b1040" stroke-width="2" stroke-linejoin="round"/>' % (f(s * rx * 0.5 - 3), f(cy - ry * 0.55), f(s * rx * 0.62), f(cy - ry * 0.55 - 15), f(s * rx * 0.5 + 3), f(cy - ry * 0.55))
            y0 = min(y0, cy - ry - 24)
        elif theme == "transport":  # a hard hat
            h1, h2 = HAT["transport"][var]
            ty = cy - ry * 0.55
            hat = ('<path d="M%s %s Q%s %s 0 %s Q%s %s %s %s Z" fill="%s" stroke="#1b1040" stroke-width="2.6" stroke-linejoin="round"/>'
                   % (f(-rx * 0.86), f(ty), f(-rx * 0.86), f(cy - ry * 1.75), f(cy - ry * 1.55), f(rx * 0.86), f(cy - ry * 1.75), f(rx * 0.86), f(ty), h1))
            hat += '<rect x="%s" y="%s" width="%s" height="6" rx="3" fill="%s" stroke="#1b1040" stroke-width="2.2"/>' % (f(-rx * 1.06), f(ty - 2), f(rx * 2.12), h2)
            hat += '<rect x="-3" y="%s" width="6" height="%s" fill="%s"/>' % (f(cy - ry * 1.5), f(ry * 0.8), h2)
            body += hat
            y0 = min(y0, cy - ry * 1.62 - 6)
        return defs, body, (x0 - 4, y0, x1 + 4, y1)

    def torso(arch, P, V):
        defs, body, box = torso0(arch, P, V)
        if theme == "transport" and arch != "blob":
            ts = P["sh_y"] - 8
            by = -P["hip_y"] + 14
            sw = P["sw"]
            y1 = ts + (by - ts) * 0.42
            y2 = ts + (by - ts) * 0.62
            bands = "".join('<rect x="%s" y="%s" width="%s" height="5" fill="#e8f4ff" stroke="#9aa6b8" stroke-width="0.8"/>' % (f(-sw - 6), f(y), f(sw * 2 + 12)) for y in (y1, y2))
            body += '<g clip-path="url(#tc)">%s</g>' % bands
        return defs, body, box

    ch.head_part, ch.torso_part = head, torso
    return ch


def build(theme: str, art: str) -> dict:
    """Writes the rigs of `theme` into assets/story/<art>/source/chars and returns the archetypes block of the manifest."""
    lib.set_chapter(art)
    chars = os.path.join(lib.SVG_DIR, "chars")  # (written over, never cleared: Godot's .import files beside the SVGs keep their uids)
    ch = _patched(theme)
    orig = {a: {v: tuple(ch.VARIANTS[a][v][r] for r in ROLES) for v in ch.VARIANTS[a]} for a in ch.VARIANTS}
    archetypes = ch.build_all()
    for arch in orig:
        for var in orig[arch]:
            rc = Recolour(orig[arch][var], PALETTES[theme][arch][var])
            d = os.path.join(chars, "%s_%s" % (arch, var))
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".svg"):
                    continue
                p = os.path.join(d, fn)
                txt = open(p, encoding="utf-8").read()
                txt = re.sub(r"#[0-9a-fA-F]{6}", lambda m: rc(m.group(0)), txt)
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(txt)
    return archetypes


if __name__ == "__main__":
    for th in sys.argv[1:] or ["magic"]:
        a = build(th, "rave_" + th)
        print(th, len(a), "archetypes")
