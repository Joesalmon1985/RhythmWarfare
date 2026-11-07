#!/usr/bin/env python3
"""The shared half of the rave generators (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 to 6): what tools/story/build_space_rave.py, build_magic_rave.py, build_dinos_rave.py and
build_transport_rave.py have in common. Nothing here writes a file by itself; the theme generators call it.

  compass: north is -z, a yaw of 0 looks north. A FRAME (phi, origin) is a local grid: u runs outward along `phi` degrees counted from SOUTH through EAST (0 south, 90 east, 180 north, 270 west), s
  runs sideways: loc(phi, u, s) = (u sin phi + s cos phi, u cos phi - s sin phi); a camera looking along u has negative s on its right. Every station (the stage, the cloakroom, the bar, the
  race entrance) is an alcove in a frame whose u = 17 is its mouth; the activity layouts (content/bedsit/themes.json cloakroom.<theme>.layout / bar.<theme>.layout) are written in the same local
  numbers, so a theme can put a station on any wall and the activity's things still land inside it.

  RaveMap                       a map under construction: sectors, portals found from shared edges (`link`), railings, waypoints, decals, billboards, lights, actors and homes.
  add_stage / add_cloak / add_bar / add_race   the four stations as alcoves in a frame, the Space rave's proportions with a theme's look (sprite names, tints) handed in.
  story_json, theme_json, write_activity_layouts, place_activity_sheets, write.
"""
from __future__ import annotations

import json
import math
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

TRACK = "origin_unknown_valley_of_the_shadows_chase_status_remix"
A_OUT = 17.0                      # the mouth of every alcove, in its frame's u
CEIL = 6.0

QUIET = {"quiet": ["stand", "chat", "drink", "lean_wall", "point"], "dancing": ["dance", "dance", "dance", "chat", "drink"], "hype": ["dance", "dance", "dance", "wave", "point"],
         "euphoric": ["dance", "dance", "wave", "point", "toast"]}
STANDING = {"quiet": ["stand", "chat", "lean_wall"], "dancing": ["stand", "chat", "drink", "watch"], "hype": ["watch", "wave", "chat", "drink"], "euphoric": ["wave", "watch", "chat", "toast"]}
STAGEACT = {"quiet": ["stand", "mix", "point"], "dancing": ["mix", "dance", "point", "wave"], "hype": ["mix", "dance", "wave", "point"], "euphoric": ["mix", "dance", "wave", "point"]}

APSES = {"cloak": (6.0, 3.6, 4.6), "bar": (6.0, 3.6, 4.6)}  # (depth D, half width at the mouth w0, half width at the far end w1) of the alcoves (the Space rave's)
STAGE_W0, STAGE_W1, STAGE_D = 4.4, 7.2, 11.0
STEP1_U, STEP2_U = 19.2, 21.4
CLOAK_HOLD_U = BAR_HOLD_U = 16.4  # just outside the alcove's mouth: the whole alcove is in the picture
CLOAK_CUSTOMER_SLOTS = [(19.6, -1.3), (19.6, -2.0), (19.6, -2.7), (19.6, -3.4), (20.4, -1.7), (20.4, -2.4), (20.4, -3.1), (20.4, -3.8)]  # (u, s) of customer_0..7: a queue to the camera's right
CLOAK_ATTENDANT = (21.8, 0.8)
CLOAK_RAIL = (22.7, 1.05, -0.3)  # (u, s of coat 0, s step per coat): eight coats along the back wall
CLOAK_SYMBOL, CLOAK_PREV, CLOAK_LAMP = (20.5, 0.0), (20.5, 0.9), (20.5, -0.55)
BAR_CUSTOMER, BAR_GLASS, BAR_CUSTOMER_GLASS, BAR_BUBBLE = (19.2, -1.6), (20.3, 0.5), (20.0, -1.0), (19.2, -1.6)
BAR_BAYS = (-3.0, -1.0, 1.0, 3.0)


# ---------------------------------------------------------------------------------------------------------------------------------------- geometry
def loc(phi: float, u: float, s: float = 0.0, origin=(0.0, 0.0)):
    """Local frame at `phi` degrees (from south through east), `origin` shifted: u outward, s along the wall (towards increasing phi)."""
    a = math.radians(phi)
    return [round(origin[0] + u * math.sin(a) + s * math.cos(a), 3), round(origin[1] + u * math.cos(a) - s * math.sin(a), 3)]


def pol(r: float, phi: float):
    a = math.radians(phi)
    return [round(r * math.sin(a), 3), round(r * math.cos(a), 3)]


def yaw_out(phi: float) -> float:
    """The yaw of looking outward at `phi` (the way u points); yaw 0 looks -z, 90 looks -x."""
    y = (phi + 180) % 360
    return round(y - 360 if y > 180 else y, 3)


def yaw_in(phi: float) -> float:
    return round(phi if phi <= 180 else phi - 360, 3)


def width_at(w0, w1, d, du):
    return w0 + (w1 - w0) * du / d


class Frame:
    def __init__(self, phi: float, origin=(0.0, 0.0)):
        self.phi, self.origin = phi, tuple(origin)

    def loc(self, u: float, s: float = 0.0):
        return loc(self.phi, u, s, self.origin)

    def out(self) -> float:
        return yaw_out(self.phi)

    def inward(self) -> float:
        return yaw_in(self.phi)

    @staticmethod
    def at_mouth(phi: float, mouth_xz, s_mouth: float = 0.0) -> "Frame":
        """The frame whose mouth (u = 17, s = s_mouth) is the point `mouth_xz`."""
        a = math.radians(phi)
        u, s = A_OUT, s_mouth
        return Frame(phi, (round(mouth_xz[0] - (u * math.sin(a) + s * math.cos(a)), 4), round(mouth_xz[1] - (u * math.cos(a) - s * math.sin(a)), 4)))


def sec(sid, poly, floor, ceiling, floor_tex, ceil_tex, light, tint, flags=None, room="main", wall_tex="wall_hull", **kw):
    d = {"id": sid, "polygon": poly, "floor": floor, "ceiling": ceiling, "floor_tex": floor_tex, "ceil_tex": ceil_tex, "wall_tex": wall_tex, "light": light, "tint": tint, "room": room,
         "flags": flags or []}
    d.update(kw)
    return d


def shared_edges(pa, pb, eps=2.0e-3):
    """The stretches where an edge of polygon `pa` and an edge of polygon `pb` lie on one line and overlap: [(p, q)] along pa's edges."""
    out = []
    for i in range(len(pa)):
        a0, a1 = pa[i], pa[(i + 1) % len(pa)]
        dx, dz = a1[0] - a0[0], a1[1] - a0[1]
        ln = math.hypot(dx, dz)
        if ln < 1e-6:
            continue
        ux, uz = dx / ln, dz / ln
        for j in range(len(pb)):
            b0, b1 = pb[j], pb[(j + 1) % len(pb)]
            c0 = ux * (b0[1] - a0[1]) - uz * (b0[0] - a0[0])
            c1 = ux * (b1[1] - a0[1]) - uz * (b1[0] - a0[0])
            if abs(c0) > eps or abs(c1) > eps:
                continue
            t0 = ux * (b0[0] - a0[0]) + uz * (b0[1] - a0[1])
            t1 = ux * (b1[0] - a0[0]) + uz * (b1[1] - a0[1])
            lo, hi = max(0.0, min(t0, t1)), min(ln, max(t0, t1))
            if hi - lo > 0.01:
                out.append(([round(a0[0] + ux * lo, 4), round(a0[1] + uz * lo, 4)], [round(a0[0] + ux * hi, 4), round(a0[1] + uz * hi, 4)]))
    return out


def rect(x0, z0, x1, z1):
    """An axis-aligned rectangle as a polygon (x0 < x1 west to east, z0 < z1 north to south)."""
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]


# ---------------------------------------------------------------------------------------------------------------------------------------- the map under construction
class RaveMap:
    def __init__(self, art: str, start: str, geography: dict, textures: dict, sky: dict, fog: dict, gain: float = 1.0, lgain: float = 1.0):
        self.art, self.start, self.geography, self.textures, self.sky, self.fog = art, start, geography, textures, sky, fog
        self.gain, self.lgain = gain, lgain  # a dark set of tiles is lifted: sector light and lamp strength are multiplied by these when written
        self.sectors, self.walls, self.things, self.lights, self.decals, self.waypoints, self.homes, self.actors = [], [], [], [], [], [], [], []
        self.poly = {}

    # ---- sectors and portals
    def sector(self, sid, poly, floor, ceiling, floor_tex, ceil_tex, light, tint, flags=None, room="main", **kw):
        self.sectors.append(sec(sid, poly, floor, ceiling, floor_tex, ceil_tex, round(min(1.0, light * self.gain), 3), tint, flags, room, **kw))
        self.poly[sid] = poly
        return poly

    def link(self, a, b, **kw):
        """A portal wherever sectors `a` and `b` share an edge (partly, too); `kw` is added to every wall written (a texture, a kind...)."""
        n = 0
        for p, q in shared_edges(self.poly[a], self.poly[b]):
            w = {"from": p, "to": q, "sector": a, "portal": b}
            w.update(kw)
            self.walls.append(w)
            n += 1
        assert n > 0, "no shared edge between %s and %s" % (a, b)
        return n

    def railing(self, a, void, tex, height=1.1):
        """A railing wherever sector `a` borders the void sector `void`."""
        return self.link(a, void, kind="railing", tex=tex, height=height)

    def alcove(self, sid, fr, D, w0, w1, floor_tex, tint, light, flags=None, floor=0.0, u0=A_OUT, u1=None, ceiling=7.0, room="main", acts=STANDING, ceil_tex="ceil_hull", **kw):
        u1 = u1 if u1 is not None else A_OUT + D
        du0, du1 = u0 - A_OUT, u1 - A_OUT
        wa, wb = width_at(w0, w1, D, du0), width_at(w0, w1, D, du1)
        poly = [fr.loc(u0, -wa), fr.loc(u0, wa), fr.loc(u1, wb), fr.loc(u1, -wb)]
        self.sector(sid, poly, floor, ceiling, floor_tex, ceil_tex, light, tint, flags, room, activities=acts, **kw)
        return poly

    # ---- waypoints, decals, billboards, lights, people
    def wp(self, wid, at, yaw, sector, **kw):
        d = {"id": wid, "at": at, "yaw": yaw, "sector": sector}
        d.update(kw)
        self.waypoints.append(d)

    def decal(self, did, sprite, fr, u, s, y, size, **kw):
        d = {"id": did, "kind": "decal", "sprite": sprite, "at": fr.loc(u, s), "y": y, "size": size, "yaw": fr.inward(), "emissive": True}
        d.update(kw)
        self.decals.append(d)

    def decal_at(self, did, sprite, at, yaw, y, size, **kw):
        d = {"id": did, "kind": "decal", "sprite": sprite, "at": at, "y": y, "size": size, "yaw": yaw, "emissive": True}
        d.update(kw)
        self.decals.append(d)

    def bb(self, tid, sprite, at, size, y=None, **kw):
        d = {"id": tid, "kind": "billboard", "sprite": sprite, "at": at, "size": size, "anim": kw.pop("anim", "none")}
        if y is not None:
            d["y"] = y
        d.update(kw)
        self.things.append(d)

    def light(self, lid, at, y, radius, color, strength, **kw):
        d = {"id": lid, "kind": "light", "at": at, "y": y, "radius": radius, "color": color, "strength": round(min(2.5, strength * self.lgain), 3)}
        d.update(kw)
        self.lights.append(d)

    def actor(self, aid, arch, var, sector, at, thresh=0, **kw):
        a = {"id": aid, "archetype": arch, "variant": var, "group": "core"}
        a.update(kw)
        a["thresh"] = thresh
        self.actors.append(a)
        self.homes.append({"actor": aid, "sector": sector, "at": at})

    def guide(self, aid, arch, var, sector, at, glow=False):
        a = {"id": aid, "archetype": arch, "variant": var, "group": "core", "role": "front", "thresh": -20, "glow": glow}
        self.actors.append(a)
        self.homes.append({"actor": aid, "sector": sector, "at": at})

    def to_json(self) -> dict:
        m = {
            "units_per_m": 1, "eye_height": 1.6, "art": self.art, "start": self.start, "max_step": 0.5, "void_drop": 3.0,
            "visibility": {"mode": "clip", "depth": 48, "far": 0},
            "geography": self.geography,
            "textures": self.textures,
            "sky": self.sky, "fog": self.fog,
            "sectors": self.sectors, "walls": self.walls, "homes": self.homes, "spots": {}, "silhouettes": [], "occluders": [],
            "waypoints": self.waypoints,
        }
        m["things"] = self.things + self.lights + self.decals
        return m


# ---------------------------------------------------------------------------------------------------------------------------------------- the four stations
def add_stage(m: RaveMap, fr: Frame, fore: str, look: dict) -> None:
    """The stage in frame `fr` off sector `fore`: two steps and a dais (the Space rave's, ids ap6_a, ap6_b, stage), the DJ's deck at u = 25.2 (the bass knob activity puts the knob at the world
    point (0, -25.12): the stage is at the north, frame phi 180 and origin (0, 0), in every rave) and the light group.
    look: floor, tint, dais, dais_tint, ceil, wall, trim, deck_sprite, arch, spk_l, spk_r, woofer, pieces (three piece names), lt_a, lt_b, dj (arch, var), dancers [(arch, var) x3]."""
    tint, ftex = look["tint"], look["floor"]
    kw = dict(ceil_tex=look["ceil"], wall_tex=look["wall"], step_tex=look.get("trim", "trim"))
    m.alcove("ap6_a", fr, STAGE_D, STAGE_W0, STAGE_W1, ftex, tint, 0.55, [], floor=0.3, u0=A_OUT, u1=STEP1_U, ceiling=7.5, acts=STANDING, **kw)
    m.alcove("ap6_b", fr, STAGE_D, STAGE_W0, STAGE_W1, ftex, tint, 0.58, [], floor=0.6, u0=STEP1_U, u1=STEP2_U, ceiling=7.5, acts=STANDING, **kw)
    m.alcove("stage", fr, STAGE_D, STAGE_W0, STAGE_W1, look["dais"], look["dais_tint"], 0.62, ["stage"], floor=0.9, u0=STEP2_U, u1=A_OUT + STAGE_D, ceiling=8.5, acts=STAGEACT, **kw)
    m.link(fore, "ap6_a")
    m.link("ap6_a", "ap6_b")
    m.link("ap6_b", "stage")
    m.wp("stage_foot", fr.loc(15.2), fr.out(), fore)
    m.wp("stage_steps", fr.loc(20.3), fr.out(), "ap6_b")
    m.wp("deck_view", fr.loc(22.6), fr.out(), "stage")
    far = A_OUT + STAGE_D - 0.015
    m.decal("stage_arch", look["arch"], fr, far, 0.0, 0.9, 4.6)
    m.decal("stage_spk_l", look["spk_l"], fr, far, -5.2, 0.9, 3.4)
    m.decal("stage_spk_r", look["spk_r"], fr, far, 5.2, 0.9, 3.4)
    m.bb("deck", look["deck_sprite"], fr.loc(25.2), 1.05, y=0.525)
    m.bb("stage_ball", "disco_ball", fr.loc(24.0), 1.4, y=5.6, anim="rotate")
    for i, s in enumerate((-4.2, 4.2)):
        m.bb("woofer_%d" % i, look.get("woofer", "woofer"), fr.loc(23.0, s), 1.7, y=0.85, anim="pump")
    p0, p1, p2 = look["pieces"]
    m.bb("stage_beams_l", p0, fr.loc(25.8, -4.4), 4.2, y=3.0, piece=p0)
    m.bb("stage_ring", p1, fr.loc(22.6), 2.6, y=0.9, piece=p1)
    m.bb("stage_dome", p2, fr.loc(26.4), 3.4, y=2.6, piece=p2)
    m.bb("glow_stage", look.get("glow", "glow"), fr.loc(25.5), 3.0, y=1.4, anim="pulse", blend="add")
    m.light("lt_stage_a", fr.loc(24.0, -3.0), 5.0, 9.0, look["lt_a"], 1.2)
    m.light("lt_stage_b", fr.loc(24.0, 3.0), 5.0, 9.0, look["lt_b"], 1.2)
    m.guide("dj", look["dj"][0], look["dj"][1], "stage", fr.loc(26.2, 0.9), glow=True)
    m.actor("s1", look["dancers"][0][0], look["dancers"][0][1], "ap6_a", fr.loc(18.0, -3.0), thresh=(len("s1") * 5) % 11 - 5)
    m.actor("s2", look["dancers"][1][0], look["dancers"][1][1], "stage", fr.loc(24.0, -4.6), thresh=(len("s2") * 5) % 11 - 5)
    m.actor("s3", look["dancers"][2][0], look["dancers"][2][1], "stage", fr.loc(24.0, 4.8), thresh=(len("s3") * 5) % 11 - 5)


def add_cloak(m: RaveMap, fr: Frame, fore: str, look: dict, customers: list, attendant: tuple, floor=0.0) -> None:
    """The cloakroom alcove (sector `cloak`) in `fr`, its hold in `fore`: counter, lamp piece, coat rail, the attendant and the eight customers of the activity's queue.
    look: floor, tint, ceil, wall, counter, rail, cabinet, hatch_decal (the three wall panels), lt."""
    D, w0, w1 = APSES["cloak"]
    m.alcove("cloak", fr, D, w0, w1, look["floor"], look["tint"], 0.55, [], floor=floor, ceil_tex=look["ceil"], wall_tex=look["wall"])
    m.link(fore, "cloak")
    m.wp("cloak_door", fr.loc(15.2), fr.out(), fore)
    m.wp("cloak_view", fr.loc(20.0), fr.out(), "cloak")
    m.wp("cloak_hold", fr.loc(CLOAK_HOLD_U), fr.out(), fore)
    cfar = A_OUT + D - 0.015
    for i, s in enumerate((-2.6, 0.0, 2.6)):
        m.decal("coat_hatch_%d" % i, look["hatch_decal"], fr, cfar, s, 0.0, 2.0)
    m.bb("cloak_counter", look["counter"], fr.loc(20.6), 1.2, y=0.6)
    m.bb("cloak_lamp", "pc_lamp_lit", fr.loc(*CLOAK_LAMP), 0.5, y=1.5, piece="cloak_lamp", emissive=True)
    m.bb("cloak_rail", look["rail"], fr.loc(22.95), 1.8, y=0.9)
    m.bb("coat_cabinet", look["cabinet"], fr.loc(22.2, -3.0), 1.8, y=0.9)
    m.light("lt_cloak", fr.loc(21.0), 3.4, 7.0, look["lt"], 1.1)
    m.guide("attendant", attendant[0], attendant[1], "cloak", fr.loc(*CLOAK_ATTENDANT))
    for k, (u, s_) in enumerate(CLOAK_CUSTOMER_SLOTS):
        arch, var = customers[k % len(customers)]
        m.actors.append({"id": "customer_%d" % k, "archetype": arch, "variant": var, "group": "core", "role": "front", "thresh": -20 if k < 4 else 100})
        m.homes.append({"actor": "customer_%d" % k, "sector": "cloak", "at": fr.loc(u, s_)})


def add_bar(m: RaveMap, fr: Frame, fore: str, look: dict, bartender: tuple, customer: tuple, extras: list, floor=0.0) -> None:
    """The bar alcove (sector `bar`): counter, the back shelf's four bays with a glass piece each, the bartender, the customer and `extras` ([(id, arch, var, u, s)]).
    look: floor, tint, ceil, wall, counter, cabinet, screen, window_a, window_b, lt."""
    D, w0, w1 = APSES["bar"]
    m.alcove("bar", fr, D, w0, w1, look["floor"], look["tint"], 0.55, [], floor=floor, ceil_tex=look["ceil"], wall_tex=look["wall"])
    m.link(fore, "bar")
    m.wp("bar_door", fr.loc(15.2), fr.out(), fore)
    m.wp("bar_view", fr.loc(20.0), fr.out(), "bar")
    m.wp("bar_hold", fr.loc(BAR_HOLD_U), fr.out(), fore)
    bfar = A_OUT + D - 0.015
    m.decal("bar_screen", look["screen"], fr, bfar, 0.0, 2.2, 0.9)
    m.decal("bar_window", look["window_a"], fr, bfar, -3.0, 1.0, 2.2)
    m.decal("bar_window_b", look["window_b"], fr, bfar, 3.0, 1.0, 2.2)
    m.bb("glow_bar", look.get("glow", "glow"), fr.loc(22.5), 2.2, y=1.4, anim="pulse", blend="add")
    m.bb("bar_counter", look["counter"], fr.loc(20.6), 1.3, y=0.65)
    for i, s_ in enumerate(BAR_BAYS):
        m.bb("bar_cab_%d" % (i + 1), look["cabinet"], fr.loc(22.9, s_), 1.8, y=0.9)
        m.bb("bar_shelf_%d" % (i + 1), "pc_glass_lit", fr.loc(22.5, s_), 0.6, y=1.75, piece="bar_shelf_%d" % (i + 1), emissive=True)
    m.light("lt_bar", fr.loc(21.0), 3.4, 7.0, look["lt"], 1.2)
    m.guide("bartender", bartender[0], bartender[1], "bar", fr.loc(22.0, 0.0))
    for aid, arch, var, u, s in extras:
        m.actor(aid, arch, var, "bar", fr.loc(u, s), thresh=(len(aid) * 5) % 11 - 5)
    m.actors.append({"id": "customer", "archetype": customer[0], "variant": customer[1], "group": "core", "role": "front", "thresh": -20})
    m.homes.append({"actor": "customer", "sector": "bar", "at": fr.loc(*BAR_CUSTOMER)})


def add_race(m: RaveMap, fr: Frame, fore: str, look: dict, pilot: tuple, D=7.5, w0=3.8, w1=5.0, door_u=15.2, floor=0.0) -> None:
    """The race entrance (sector `hangar`, a placeholder node the race agent wires): a big door at the end wall with a vehicle glimpsed in front, a console and the pilot.
    look: floor, tint, ceil, wall, door, side_a, side_b, vehicle, console, lt, vehicle_size, door_size."""
    m.alcove("hangar", fr, D, w0, w1, look["floor"], look["tint"], 0.6, [], floor=floor, ceil_tex=look["ceil"], wall_tex=look["wall"])
    m.link(fore, "hangar")
    m.wp("hangar_door", fr.loc(door_u), fr.out(), fore)
    m.wp("hangar_view", fr.loc(21.0 if D > 6 else 19.8), fr.out(), "hangar")
    hfar = A_OUT + D - 0.015
    m.decal("hangar_door", look["door"], fr, hfar, 0.0, 0.0, look.get("door_size", 3.4))
    if w0 > 3.0:
        m.decal("hangar_warn", look["side_a"], fr, hfar, -3.7, 0.0, 2.4)
        m.decal("hangar_glow", look["side_b"], fr, hfar, 3.7, 0.0, 2.4)
    m.bb("glow_hangar", look.get("glow", "glow"), fr.loc(A_OUT + D - 0.9), 3.0, y=1.4, anim="pulse", blend="add")
    vs = look.get("vehicle_size", 1.5)
    m.bb("hangar_racer", look["vehicle"], fr.loc(A_OUT + D - 1.1), vs, y=vs / 2)
    m.bb("hangar_console", look["console"], fr.loc(A_OUT + 4.6, -(w0 - 0.6)), 1.3, y=0.65)
    m.light("lt_hangar", fr.loc(A_OUT + 5.0), 3.6, 8.0, look["lt"], 1.3)
    m.guide("pilot", pilot[0], pilot[1], "hangar", fr.loc(A_OUT + 3.4, 2.0 if w0 > 3.0 else 0.8))


def add_home(m: RaveMap, fr: Frame, fore: str, look: dict, arrive: str) -> None:
    """The way home: a shallow alcove behind the hub (sector `home`) with the arrival pose, the threshold pose and the hatch (the thing `home_hatch` the hub's home hotspot is anchored on).
    look: floor, tint, ceil, wall, hatch (sprite), window (decal)."""
    m.alcove("home", fr, 5.0, 2.5, 2.5, look["floor"], look["tint"], 0.55, [], ceil_tex=look["ceil"], wall_tex=look["wall"])
    m.link(fore, "home")
    m.wp(arrive, fr.loc(20.4), fr.inward(), "home")
    m.wp("home_door", fr.loc(19.0), fr.out(), "home")
    m.decal("home_window", look["window"], fr, A_OUT + 5.0 - 0.015, 0.0, 1.6, 1.0)
    m.bb("home_hatch", look["hatch"], fr.loc(19.9), 2.3, y=1.15)
    m.light("lt_home", fr.loc(20.0), 3.0, 6.0, "#fff2c8", 1.0)


def add_crowd(m: RaveMap, spots: list, kinds: list) -> int:
    """The dance-floor crowd: `spots` is [(sector, [x, z])]; `kinds` [(arch, var)] cycles. Returns the count."""
    n = 0
    for sector, at in spots:
        arch, var = kinds[n % len(kinds)]
        aid = "a%02d" % n
        n += 1
        m.actor(aid, arch, var, sector, at, thresh=(n * 7) % 13 - 6)
    return n


# ---------------------------------------------------------------------------------------------------------------------------------------- the story, the theme file, the layouts
def story_json(actors: list, sid: str, title: str, art: str, block_title: str, ambient_piece: str, palettes: dict | None = None, description: str = "") -> dict:
    base = json.loads(open(os.path.join(ROOT, "content", "story", "mothership.json"), encoding="utf-8").read())
    ids = [a["id"] for a in actors]
    d = {k: base[k] for k in ["palettes", "energy", "initial_energy", "sequence_bars"]}
    if palettes:
        d["palettes"] = palettes
    d.update({"id": sid, "title": title, "chapter": 9, "art": art, "music_pack": base["music_pack"], "music_packs": base["music_packs"],
              "description": description or "A rave (docs/briefs/BEDSIT_RAVES_BRIEF.md section 3): a path's world, not a Story Campaign chapter.",
              "duration_bars": 8, "intro": "",
              "acts": [{"id": "I", "title": title, "start_bar": 1}],
              "blocks": [{"id": "the_rave", "title": block_title, "act": "Act I", "start_bar": 1, "bars": 8,
                          "events": [{"at_bar": 1, "action": "lights_cool"}, {"at_bar": 1, "action": "player_role", "role": "dancer"}, {"at_bar": 1, "action": "piece_on", "piece": ambient_piece}]}],
              "groups": {"circle": ids[:], "all": ids[:]}, "actors": actors, "silhouettes": []})
    d["groups"]["early"] = []
    d["endings"] = {k: {kk: vv for kk, vv in v.items() if kk != "journey"} for k, v in base["endings"].items()}  # (a rave has no helm: no ending journeys)
    d["ending_order"] = base["ending_order"]
    return d


def leg(to, bars, hold_bars, look=None, via=None) -> dict:
    d = {"to": to, "bars": bars, "hold_bars": hold_bars, "style": "walk"}
    if look:
        d["look"] = look
    if via:
        d["via"] = via
    return d


def route(map_id: str, frm: str, legs: list, arrive: str) -> dict:
    return {"map": map_id, "from": frm, "legs": legs, "arrive": {"waypoint": arrive, "choice_view": True, "hold": "window"}, "eye_m": 1.6}


def theme_json(spec: dict) -> dict:
    """content/raves/<theme>.json: contract 2's shape (src/contracts/fixtures/theme_space.json). spec: id, prefix (the scene id prefix: space, magic, dino, transport), scene_id (the map),
    geography, arrival, props, customers, guides, ingredients, cloakroom_symbols, routes {stage, cloak, bar} (route dicts without ids)."""
    pre, tid = spec["prefix"], spec["id"]
    routes = {}
    for k, key in (("stage", "to_stage"), ("cloak", "to_cloak"), ("bar", "to_bar")):
        rid = "%s.%s" % (tid, key)
        routes[rid] = dict({"id": rid}, **{kk: vv for kk, vv in spec["routes"][k].items()})
    return {
        "id": tid, "scene_id": spec["scene_id"], "geography": spec["geography"], "map": spec["scene_id"], "track": TRACK, "arrival": spec["arrival"],
        "props": spec["props"], "customers": spec["customers"], "guides": spec["guides"], "ingredients": spec["ingredients"], "cloakroom_symbols": spec["cloakroom_symbols"],
        "stations": {"stage": {"waypoint": "deck_view", "route": "%s.to_stage" % tid}, "cloakroom": {"waypoint": "cloak_hold", "route": "%s.to_cloak" % tid},
                     "bar": {"waypoint": "bar_hold", "route": "%s.to_bar" % tid}},
        "race": {"entrance": "hangar_view", "course": "race_street_%s" % tid, "activity": "race"},
        "home": {"threshold": "home_door", "route": "home"},
        "activities": {"stage": "bass_knob", "cloakroom": "cloakroom", "bar": "bar", "race": "race"},
        "routes": routes,
        "hub": {"viewpoint": "hub_view", "choice_view": True, "hold_bars": 8,
                "choices": {"stage": {"actor": "dj", "node": "%s_stage" % pre}, "cloakroom": {"actor": "attendant", "node": "%s_cloakroom" % pre},
                            "bar": {"actor": "bartender", "node": "%s_bar" % pre}, "race": {"actor": "pilot", "node": "%s_race" % pre}, "home": {"thing": "home_hatch", "node": "bedsit"}}},
    }


def r2(v):
    return [round(v[0], 3), round(v[1], 3)]


def write_activity_layouts(theme: str, cloak_fr: Frame, bar_fr: Frame, art_name: str) -> None:
    """Where the cloakroom's and the bar's things stand in THIS map: content/bedsit/themes.json cloakroom.<theme>.layout and bar.<theme>.layout (the activities read them: CloakroomActivity.layout,
    BarData.layout). The blocks are merged into the file, nothing else in it changes (tools/run/make_bedsit.py keeps them too)."""
    path = os.path.join(ROOT, "content", "bedsit", "themes.json")
    d = json.loads(open(path, encoding="utf-8").read())
    c = cloak_fr
    d["cloakroom"][theme]["layout"] = {
        "sector": "cloak", "customer_slots": [r2(c.loc(u, s_)) for (u, s_) in CLOAK_CUSTOMER_SLOTS], "hand_off": r2(loc(c.phi, -0.3, 0.0)), "attendant_at": r2(c.loc(*CLOAK_ATTENDANT)),
        "rail_at": r2(c.loc(CLOAK_RAIL[0], CLOAK_RAIL[1])), "rail_step": r2(loc(c.phi, 0.0, CLOAK_RAIL[2])), "rail_y": 0.8, "coat_size": [0.5, 0.8],
        "symbol_at": r2(c.loc(*CLOAK_SYMBOL)), "symbol_y": 1.35, "symbol_size": [0.8, 0.8], "prev_at": r2(c.loc(*CLOAK_PREV)), "prev_y": 1.45, "prev_size": [0.5, 0.5],
        "counter_piece": "cloak_counter", "lamp_piece": "cloak_lamp",
    }
    b = bar_fr
    d["bar"][theme]["layout"] = {
        "map": art_name, "sector": "bar", "customer_at": r2(b.loc(*BAR_CUSTOMER)), "customer_glass_at": r2(b.loc(*BAR_CUSTOMER_GLASS)), "glass_at": r2(b.loc(*BAR_GLASS)), "glass_y": 1.55,
        "glass_size": [0.3, 0.5], "bubble_at": r2(b.loc(*BAR_BUBBLE)), "bubble_y": 2.25, "bubble_size": [0.9, 0.9], "counter_piece": "bar_counter", "shelf_prefix": "bar_shelf_",
    }
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        json.dump(d, fh, indent=1)
        fh.write(chr(10))


def place_activity_sheets(art: str, theme: str, knob_png: str) -> None:
    """The activities' dynamic-thing sheets (PLACEHOLDERS) under assets/story/<art>/sprites/, each with its grid sidecar: copies of the cloakroom and bar packages' test sheets for `theme`, and the
    bass knob's frames. Rows are states, columns frames."""
    dst = os.path.join(ROOT, "assets", "story", art, "sprites")
    os.makedirs(dst, exist_ok=True)
    cloak = os.path.join(ROOT, "tests", "fixtures", "cloakroom_scene", "assets", "story", "cloak_test", "sprites")
    bar = os.path.join(ROOT, "assets", "story", "bar_test", "sprites")
    src = {
        "cloak_coat": (os.path.join(cloak, "cloak_coat.png"), [4, 3]),
        "cloak_symbols_%s" % theme: (os.path.join(cloak, "cloak_symbols_%s.png" % theme), [4, 2]),
        "bar_glass_%s" % theme: (os.path.join(bar, "bar_glass_%s.png" % theme), [6, 1]),
        "bar_order_%s" % theme: (os.path.join(bar, "bar_order_%s.png" % theme), [4, 1]),
        "sr_knob": (knob_png, [4, 1]),
    }
    for name, (path, grid) in src.items():
        shutil.copyfile(path, os.path.join(dst, name + ".png"))
        with open(os.path.join(dst, name + ".json"), "w", encoding="utf-8", newline=chr(10)) as fh:
            json.dump({"grid": grid}, fh)
            fh.write(chr(10))


def write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")


def hub_bearings(m: RaveMap, hub_at, hub_yaw: float, ids: list) -> dict:
    """The bearing (degrees, + to the left) of each actor's home from the hub viewpoint: the hub's choices must all be in the picture (the view is about 82 degrees wide at 16:9)."""
    homes = {h["actor"]: h["at"] for h in m.homes}
    out = {}
    for i in ids:
        dx, dz = homes[i][0] - hub_at[0], homes[i][1] - hub_at[1]
        bearing = math.degrees(math.atan2(-dx, -dz))  # 0 looks -z, + turns left
        out[i] = round(((bearing - hub_yaw + 180) % 360) - 180, 1)
    return out
