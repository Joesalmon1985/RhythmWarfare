"""A small DSL for authoring the Squadron path's three maps (docs/THREE_PATHS_AND_FACES_PLAN.md section 5): rooms are rectangles laid out in a plan, authored in the room's own
frame (d = metres from the entry wall along the way the camera looks, u = metres to the camera's right), then written as content/story/maps/<map>.json and the chapter data
content/story/<map>.json that the run's stage and the people-sheet baker read. Everything is deterministic; rerun `python3 tools/paths/make_squadron.py`.
"""
from __future__ import annotations

import math

# --- the textures every map names: id -> brief for the art builder (tools/story/art/tex_squadron.py) -------------------------------------------------------------------------------
TEX: dict = {}  # id -> {kind: surface|ceil|billboard|sky, size, metres, desc, maps: [map ids]}


def tex(map_id: str, tid: str, kind: str, desc: str, metres: float = 2.0, size: int = 64) -> str:
    TEX.setdefault(tid, {"kind": kind, "size": size, "metres": metres, "desc": desc, "maps": []})
    return tid  # (`maps` is filled by MapBuilder.map_json with the maps that really use the texture)


def fmt(v: float) -> float:
    return round(float(v), 3)


QUIET_STAND = {"quiet": ["stand", "chat", "lean_wall", "watch"], "dancing": ["stand", "chat", "watch", "check"], "hype": ["watch", "wave", "chat", "point"], "euphoric": ["wave", "watch", "chat", "point"]}
WAIT = {"quiet": ["stand", "lean_wall", "check", "chat"], "dancing": ["stand", "watch", "chat", "check"], "hype": ["watch", "chat", "point", "wave"], "euphoric": ["wave", "watch", "chat"]}
SOMBRE = {"quiet": ["stand", "sit", "rock", "stare"], "dancing": ["stand", "sit", "rock", "stare"], "hype": ["stand", "sit", "rock", "stare"], "euphoric": ["stand", "sit", "rock", "stare"]}
WARD = {"quiet": ["sit", "lie", "chat", "stand"], "dancing": ["sit", "lie", "chat", "watch"], "hype": ["sit", "chat", "watch", "wave"], "euphoric": ["wave", "chat", "watch", "sit"]}
BUSY = {"quiet": ["carry", "check", "stand", "chat"], "dancing": ["carry", "check", "chat", "serve"], "hype": ["carry", "wave", "chat", "check"], "euphoric": ["wave", "carry", "chat", "watch"]}
STREET = {"quiet": ["stand", "chat", "lean_wall", "pace"], "dancing": ["chat", "watch", "stand", "pace"], "hype": ["watch", "wave", "chat", "point"], "euphoric": ["wave", "watch", "chat", "point"]}
CROWD_OUT = {"quiet": ["stand", "stare", "sit", "pace"], "dancing": ["stare", "stand", "chat", "sit"], "hype": ["stare", "watch", "wave", "stand"], "euphoric": ["wave", "watch", "stare", "chat"]}


class Room:
    def __init__(self, mb: "MapBuilder", rid: str, rect, yaw: float, view: str, **sec):
        self.mb, self.id, self.view, self.yaw = mb, rid, view, float(yaw)
        x0, z0, x1, z1 = rect
        self.rect = rect
        self.fwd = (-math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)))
        self.right = (math.cos(math.radians(yaw)), -math.sin(math.radians(yaw)))
        cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
        ext_f = abs(self.fwd[0]) * (x1 - x0) + abs(self.fwd[1]) * (z1 - z0)
        self.depth = ext_f
        self.width = abs(self.right[0]) * (x1 - x0) + abs(self.right[1]) * (z1 - z0)
        self.entry = (cx - self.fwd[0] * ext_f / 2.0, cz - self.fwd[1] * ext_f / 2.0)
        self.sec = {"id": rid, "polygon": [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], "floor": 0, "ceiling": 2.8, "light": 0.55, "tint": "#ffffff", "room": view, "flags": [], **sec}

    def loc(self, d: float, u: float = 0.0):
        return [fmt(self.entry[0] + self.fwd[0] * d + self.right[0] * u), fmt(self.entry[1] + self.fwd[1] * d + self.right[1] * u)]

    def thing(self, tid, sprite, d, u, y, size, anim="none", **kw):
        t = {"id": tid, "kind": "billboard", "sprite": sprite, "at": self.loc(d, u), "y": y, "size": size, "anim": anim, "sector": self.id}
        t.update(kw)
        self.mb.things.append(t)
        return tid

    def light(self, tid, d, u, y, radius, color, strength=1.0, cone_yaw=None, cone_angle=None):
        t = {"id": tid, "kind": "light", "at": self.loc(d, u), "y": y, "radius": radius, "color": color, "strength": strength, "sector": self.id}
        if cone_yaw is not None:
            t["cone"] = {"yaw": self.yaw + cone_yaw, "angle": cone_angle or 35}
        self.mb.things.append(t)

    def wp(self, wid, d, u, dyaw=0.0):
        self.mb.waypoints.append({"id": wid, "at": self.loc(d, u), "yaw": fmt(self.yaw + dyaw), "sector": self.id})
        return wid

    def actor(self, aid, wear, variant, d, u, **kw):
        a = {"id": aid, "archetype": "groover", "variant": "a", "art": "night_one", "wear": wear, "look": variant, "group": "core", "thresh": 0}
        if self.view != "main":
            a["view"] = self.view
        a.update(kw)
        self.mb.actors.append(a)
        self.mb.homes.append({"actor": aid, "sector": self.id, "at": self.loc(d, u)})
        return aid

    def spots(self):
        """The crowd's named places of this room (door with eight slots, circle, riser, side_l, side_r): the run uses few, the stage's crowd code looks them up."""
        p = (lambda n: n) if self.view == "main" else (lambda n: f"{self.view}.{n}")
        ms = self.mb.spots
        w = self.width
        ms[p("door")] = {"sector": self.id, "at": self.loc(0.7, 0), "slots": [self.loc(0.6 + 0.9 * (k // 4), -1.5 + 1.0 * (k % 4)) for k in range(8)]}
        rx, rz = min(2.0, w / 2 - 0.8), min(1.4, self.depth / 2 - 1.0)
        ms[p("circle")] = {"sector": self.id, "at": self.loc(self.depth / 2, 0), "radii": [fmt(rx), fmt(rz)], "open": [0.0, 1.0]}
        ms[p("riser")] = {"sector": self.id, "at": self.loc(self.depth - 1.0, 0)}
        ms[p("side_l")] = {"sector": self.id, "at": self.loc(self.depth / 2, -(w / 2 - 0.5))}
        ms[p("side_r")] = {"sector": self.id, "at": self.loc(self.depth / 2, (w / 2 - 0.5))}

    def standard_rail(self, name: str, home=(1.8, 0), good=((3.6, -1.2), (5.2, 1.2)), bad=((1.2, 2.6), (2.4, -2.6)), arrive=(0.5, 0)):
        """Waypoints `<name>_home`, `_g1`, `_g2`, `_b1`, `_b2`, `_arrive` for a scene's rail (home looks along the room)."""
        self.wp(f"{name}_home", home[0], home[1])
        self.wp(f"{name}_g1", good[0][0], good[0][1], -10)
        self.wp(f"{name}_g2", good[1][0], good[1][1], 12)
        self.wp(f"{name}_b1", bad[0][0], bad[0][1], 35)
        self.wp(f"{name}_b2", bad[1][0], bad[1][1], -40)
        self.wp(f"{name}_arrive", arrive[0], arrive[1])


class MapBuilder:
    def __init__(self, mid: str, fog: dict, sky_tex: str):
        self.id = mid
        self.fog = fog
        self.sky_tex = sky_tex
        self.sectors, self.walls, self.things, self.waypoints, self.homes, self.actors = [], [], [], [], [], []
        self.spots: dict = {}
        self.rooms: dict = {}  # room (view) id -> {palette}
        self.rooms_obj: dict = {}
        self.animated: list = []

    def room(self, rid: str, rect, yaw: float, view: str = None, **sec) -> Room:
        r = Room(self, rid, rect, yaw, view or rid, **sec)
        self.rooms_obj[rid] = r
        return r

    def portal(self, a: str, b: str, p0, p1, lower="", upper=""):
        w = {"from": list(p0), "to": list(p1), "sector": a, "portal": b}
        if lower:
            w["lower_tex"] = lower
        if upper:
            w["upper_tex"] = upper
        self.walls.append(w)

    def textures_used(self) -> list:
        names = set([self.sky_tex] if self.sky_tex else [])
        for r in self.rooms_obj.values():
            for k in ("floor_tex", "ceil_tex", "wall_tex"):
                v = r.sec.get(k, "")
                if v and v != "sky":
                    names.add(v)
        for w in self.walls:
            for k in ("lower_tex", "upper_tex", "tex"):
                if w.get(k):
                    names.add(w[k])
        for t in self.things:
            if t.get("kind") == "billboard":
                names.add(t["sprite"])
        return sorted(names)

    def map_json(self, start: str) -> dict:
        names = self.textures_used()
        for n in names:
            assert n in TEX, f"texture {n} is used but never declared with tex()"
            if self.id not in TEX[n]["maps"]:
                TEX[n]["maps"].append(self.id)
        textures = {n: f"textures/{n}.png" for n in names}
        sectors = [dict(r.sec) for r in self.rooms_obj.values()]
        for r in self.rooms_obj.values():
            r.spots()
        return {"art": self.id, "units_per_m": 1, "eye_height": 1.6, "start": start, "textures": textures, "sectors": sectors, "walls": self.walls, "things": self.things,
                "homes": self.homes, "waypoints": self.waypoints, "spots": self.spots, "silhouettes": [], "occluders": [], "rooms": self.rooms,
                "sky": {"tex": f"textures/{self.sky_tex}.png", "mode": "cylinder"}, "fog": self.fog, "animated": self.animated}
