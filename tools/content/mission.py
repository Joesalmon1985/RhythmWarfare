"""A mission: a title, a length, the form (which 8-bar phases are drums or bass), the battlefield and the waves.

A mission no longer authors music. The player's one loadout (groove, fill, kick sound, snare sound, bass line, bass
sound, backing) plays in every mission, as the 8-bar loops of songs/library (see library.py). content/missions/
level_NN.json is the authoring file and `build(...)` turns it into songs/<pack>/level.json (schema 4): phases from the
form, the baked waves, the intro lines and the `base` the battlefield gives the player.

    {"level_id": "level_01", "number": 1, "title": "First Watch", "pack": "m01_first_watch", "bars": 128, "seed": 1001,
     "form": "DDBDBDDBDBDBDDBD", "battle": {"battlefield": "village_01", "waves": "data/campaign/waves/level_01.json",
     "rules": {...optional...}}, "intros": [{"bar": 1, "text": "..."}], "note": "..."}

`form` has one letter per 8-bar phase (D = drums, B = bass) and `bars` must be 8 * len(form).
"""
from __future__ import annotations

from pathlib import Path

from common import ROOT, SONGS, TICKS_PER_BAR, ContentError, read_json, rel, write_json

PHASE_BARS = 8
SEQUENCE_BARS = 2
MODES = {"D": "drums", "B": "bass"}
SEQUENCE_THRESHOLD = 0.6


class Mission:
    def __init__(self, path: Path):
        self.path = path
        self.data = read_json(path)
        d = self.data
        self.errors: list[str] = []
        self.warnings: list[str] = []
        try:
            self.level_id = d["level_id"]
            self.number = int(d["number"])
            self.title = d["title"]
            self.pack = d["pack"]
            self.bars = int(d["bars"])
            self.form = str(d["form"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ContentError(f"{rel(path)}: needs level_id, number, title, pack, bars and form ({exc})") from exc
        self.duration_ticks = self.bars * TICKS_PER_BAR
        self.phases: list[dict] = []
        self.intros: list[dict] = []
        self.waves: list[dict] = []
        self.enemies = 0

    def err(self, msg: str) -> None:
        self.errors.append(f"{rel(self.path)}: {msg}")

    # --- parsing -------------------------------------------------------------------------------------------------
    def parse(self) -> None:
        d = self.data
        if d.get("bpm", 174) != 174 or d.get("meter", [4, 4]) != [4, 4]:
            self.err("missions are 174 BPM in 4/4")
        if not self.form or any(c not in MODES for c in self.form):
            self.err(f"form '{self.form}' must be letters D (drums) and B (bass), one per {PHASE_BARS}-bar phase")
        if self.bars != PHASE_BARS * len(self.form):
            self.err(f"{self.bars} bars but the form '{self.form}' has {len(self.form)} phases of {PHASE_BARS} bars "
                     f"({PHASE_BARS * len(self.form)} bars)")
        for i, c in enumerate(self.form):
            start = i * PHASE_BARS * TICKS_PER_BAR
            self.phases.append({"id": f"p{i + 1:02d}", "start_tick": start, "end_tick": start + PHASE_BARS * TICKS_PER_BAR,
                                "mode": MODES.get(c, "")})
        for it in d.get("intros", []):
            bar = int(it.get("bar", 1))
            if not 1 <= bar <= self.bars or not str(it.get("text", "")):
                self.err(f"intros: each entry needs a bar inside the song and a text ({it})")
            self.intros.append({"bar": bar, "text": str(it.get("text", ""))})
        battle = d.get("battle", {})
        if not battle.get("waves"):
            self.err("battle.waves names the waves file")

    # --- the battlefield's base ------------------------------------------------------------------------------------
    @staticmethod
    def base_of(battlefield: str) -> dict:
        """What the battlefield gives the player: the production buildings (the roles of its exits), the number of
        entries and defense points, and the civilians that wander in it."""
        bf = read_json(ROOT / "data" / "battlefields" / f"{battlefield}.json")
        roles = list(bf.get("exits", {}))
        order = {"barracks": 0, "factory": 1}
        return {"production": sorted(roles, key=lambda r: (order.get(r, 2), r)), "entries": len(bf.get("entries", [])),
                "points": len(bf.get("defense_points", [])), "civilians": len(bf.get("civilians", []))}

    # --- output ---------------------------------------------------------------------------------------------------
    def level_json(self) -> dict:
        d = self.data
        waves_path = ROOT / d["battle"]["waves"]
        waves = read_json(waves_path)
        battle = d["battle"]
        rules = dict(waves.get("rules", {}))
        rules.update(battle.get("rules", {}))
        field = battle.get("battlefield", waves.get("battlefield", "defense_02"))
        self._check_walls(rules, field)
        objective = self.primary_objective(field)
        self.waves = [self._wave(w, objective) for w in waves["waves"]]
        self.enemies = sum(g["count"] for w in self.waves for g in w["groups"])
        return {
            "schema_version": 4,
            "level_id": self.level_id,
            "number": self.number,
            "title": self.title,
            "bpm": 174,
            "ticks_per_beat": 960,
            "time_signature": [4, 4],
            "duration_ticks": self.duration_ticks,
            "seed": int(d.get("seed", 1000 + self.number)),
            "battlefield": field,
            "roster": "openra_mvp_01",
            "rules": rules,
            "sequence_threshold": float(d.get("sequence_threshold", SEQUENCE_THRESHOLD)),
            "sequence_bars": int(d.get("sequence_bars", SEQUENCE_BARS)),
            "phases": self.phases,
            "waves": self.waves,
            "intros": self.intros,
            "base": self.base_of(field),
        }

    VIA = {"left": "defense_1", "top": "defense_2", "right": "defense_3"}

    def _check_walls(self, rules: dict, battlefield: str) -> None:
        """Sandbag cells (rules.walls) must keep every route open and stay off sockets, buildings and the map edge."""
        bf = read_json(ROOT / "data" / "battlefields" / f"{battlefield}.json")
        taken = {(b["x"] + i, b["y"] + j) for b in bf["buildings"] for i in range(b["w"]) for j in range(b["h"])}
        taken |= {(sk["x"], sk["y"]) for sk in bf.get("sockets", [])}
        for x, y in rules.get("walls", []):
            on_route = (19 <= y <= 23 and (x < 28 or x > 50)) or (37 <= x <= 41 and y < 16)
            if on_route or (x, y) in taken or not (0 < x < bf["width"] - 1 and 0 < y < bf["height"] - 1):
                self.err(f"wall cell ({x}, {y}) is on a route, a socket or a building")

    TARGETS = ("defenses", "civilians", "core")

    @staticmethod
    def primary_objective(battlefield: str) -> str:
        """The id of the battlefield's first required objective (the one waves attack by default); the command core when
        the battlefield cannot be read."""
        try:
            bf = read_json(ROOT / "data" / "battlefields" / f"{battlefield}.json")
            return next(o["id"] for o in bf["objectives"] if o.get("required"))
        except (OSError, ValueError, KeyError, StopIteration):
            return "command_core"

    def _wave(self, w: dict, objective: str = "command_core") -> dict:
        """Waves are authored by bar (start_bar, 1-based, fractions allowed) or tick; the defense point follows the
        entry, the objective defaults to the battlefield's first required objective and `target` (what the wave goes
        for: defenses, civilians or core, default core) may be overridden per group."""
        out = dict(w)
        if "start_bar" in w and "start_tick" not in w:
            out["start_tick"] = int(round((float(w["start_bar"]) - 1.0) * TICKS_PER_BAR))
        out.setdefault("via_defense_point", self.VIA.get(w["entry"], "defense_1"))
        out.setdefault("target_objective", objective)
        out.setdefault("target", "core")
        for where, t in [(f"wave {w['id']}", out["target"])] + [(f"wave {w['id']} group {g.get('actor', '?')}", g["target"]) for g in w["groups"] if "target" in g]:
            if t not in self.TARGETS:
                self.err(f"{where}: target '{t}' is not one of {', '.join(self.TARGETS)}")
        out["groups"] = [{**g, "spawn_spacing_ticks": int(g.get("spawn_spacing_ticks", 480))} for g in w["groups"]]
        if not 0 <= out["start_tick"] < self.duration_ticks:
            self.err(f"wave {w['id']} starts outside the song")
        return out


def build(path: Path, songs: Path = SONGS, write: bool = True) -> Mission:
    """Parse and check one mission and (with `write`) write songs/<pack>/level.json. No audio: the loops are the library's."""
    m = Mission(path)
    m.parse()
    if m.errors:
        return m
    level = m.level_json()
    if m.errors:
        return m
    if write:
        write_json(songs / m.pack / "level.json", level)
    return m
