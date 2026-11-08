"""The street race's course geometry (docs/bedsit/RACE.md): a finite street built from straight runs and circular bends, sampled into the convex sectors of a story map.

Pure geometry, no art: tools/story/build_race.py draws the placeholder art and writes the files. The same numbers are written into the course file
(content/races/courses/race_<theme>.json, `segments`) so the game computes the very same centreline (src/minigames/race/race_course.gd).

Conventions (StoryMap): ground (x, z) metres, yaw in degrees, yaw 0 looks toward -z, a positive yaw turns left; forward = (-sin yaw, -cos yaw), right = (cos yaw, -sin yaw).
A bend's `turn` is in degrees, positive to the left.
"""
from __future__ import annotations

import math


def fwd(yaw_deg: float):
    r = math.radians(yaw_deg)
    return (-math.sin(r), -math.cos(r))


def right(yaw_deg: float):
    r = math.radians(yaw_deg)
    return (math.cos(r), -math.sin(r))


def build_segments(layout: list, start=(0.0, 0.0), yaw0: float = 0.0) -> list:
    """`layout`: [("straight", length_m) | ("bend", turn_deg, radius_m)] -> [{kind, s0, len, at, yaw, turn, radius}] (the start point and heading of each piece)."""
    out = []
    s, p, yaw = 0.0, start, yaw0
    for item in layout:
        if item[0] == "straight":
            ln = float(item[1])
            out.append({"kind": "straight", "s0": round(s, 4), "len": round(ln, 4), "at": [round(p[0], 4), round(p[1], 4)], "yaw": round(yaw, 6), "turn": 0.0, "radius": 0.0})
            f = fwd(yaw)
            p = (p[0] + f[0] * ln, p[1] + f[1] * ln)
        else:
            turn, rad = float(item[1]), float(item[2])
            ln = abs(math.radians(turn)) * rad
            out.append({"kind": "arc", "s0": round(s, 4), "len": round(ln, 4), "at": [round(p[0], 4), round(p[1], 4)], "yaw": round(yaw, 6), "turn": turn, "radius": rad})
            p, yaw = _arc_point(p, yaw, turn, rad, ln)
        s += ln
    return out


def _arc_point(p0, yaw0: float, turn: float, rad: float, s: float):
    sign = 1.0 if turn > 0 else -1.0
    r0 = right(yaw0)
    c = (p0[0] - sign * r0[0] * rad, p0[1] - sign * r0[1] * rad)  # the bend's centre: to the left of a left bend
    yaw = yaw0 + sign * math.degrees(s / rad)
    r = right(yaw)
    return (c[0] + sign * r[0] * rad, c[1] + sign * r[1] * rad), yaw


def total(segs: list) -> float:
    return segs[-1]["s0"] + segs[-1]["len"]


def point(segs: list, s: float, x: float = 0.0):
    """The ground point `s` metres along the centreline and `x` metres to its right, and the heading there: ((x, z), yaw). Before 0 / past the end the first / last piece is extended straight."""
    seg = segs[0]
    for g in segs:
        if s >= g["s0"]:
            seg = g
    u = s - seg["s0"]
    if seg["kind"] == "straight" or u < 0.0 or u > seg["len"]:
        if seg["kind"] == "arc" and u > seg["len"]:  # past the end of a closing bend: straight on from its end
            (pe, ye) = _arc_point(tuple(seg["at"]), seg["yaw"], seg["turn"], seg["radius"], seg["len"])
            f = fwd(ye)
            c = (pe[0] + f[0] * (u - seg["len"]), pe[1] + f[1] * (u - seg["len"]))
            yaw = ye
        else:
            f = fwd(seg["yaw"])
            c = (seg["at"][0] + f[0] * u, seg["at"][1] + f[1] * u)
            yaw = seg["yaw"]
    else:
        c, yaw = _arc_point(tuple(seg["at"]), seg["yaw"], seg["turn"], seg["radius"], u)
    r = right(yaw)
    return (c[0] + r[0] * x, c[1] + r[1] * x), yaw


def stations(segs: list, s_from: float, s_to: float, straight_step: float, arc_step_deg: float) -> list:
    """The distances where the sectors are cut: every `straight_step` on the straights, every `arc_step_deg` degrees on the bends, plus every piece's ends."""
    out = [s_from]
    for g in segs:
        a, b = g["s0"], g["s0"] + g["len"]
        if g is segs[0]:
            a = min(a, s_from)
        if g is segs[-1]:
            b = max(b, s_to)
        step = straight_step if g["kind"] == "straight" else max(math.radians(arc_step_deg) * g["radius"], 2.0)
        n = max(1, int(math.ceil((b - a) / step - 1e-6)))
        for k in range(1, n + 1):
            v = a + (b - a) * k / n
            if s_from < v <= s_to + 1e-6:
                out.append(min(v, s_to))
    clean = []
    for v in sorted(out):
        if not clean or v - clean[-1] > 0.5:
            clean.append(round(v, 4))
    if clean[-1] < s_to - 1e-6:
        clean.append(round(s_to, 4))
    return clean
