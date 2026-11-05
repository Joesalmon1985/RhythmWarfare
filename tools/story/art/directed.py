"""Which people are directed, and in which acts and faces: the data that decides what the sheets bake (docs/THREE_PATHS_AND_FACES_PLAN.md 2.2).

A directed act costs frames, so it is baked only for the actors the story directs, never for the whole crowd. The list comes from data and is merged from
three places (later stages fill the last two; stage 1a seeds the first):

1. `content/story/directed_actors.json`: {chapter: {actor id: [entry, ...]}} where an entry is `"act"`, `"act@face"`, `"act@face:front+side"` (the facings) or
   `{"act", "face", "facings"}`. Hand-kept: the
   test actors that prove every face and act, and anything the run data does not name.
2. the `acting` blocks of the hotspots in `content/run/hotspots/*.json` (plan 2.3a): `acting.actor` (default `anchor.actor`) and the `act` / `face` of each of its
   `available`, `selected`, `committed`, `success` and `failure` states and their `then`.
3. the `cast` lines of the scenes in `content/run/run.json` (plan 2.3b) and of its `cinematics` (2.3c): `actor`, `act`, `face`.
   A hotspot whose acting names a Bassment `figure` instead of an actor is skipped: creatures are billboards, not baked people.

`directed(chapter)` returns {actor id: [(act, face, facings), ...]}, deduplicated, in a stable order. A face equal to the act's own default (StoryCharacter.FACE_OF) is the
plain act (`beckon`); any other is a separate frame set the sheet names `beckon@plea` (people_sheets.state_key). Unknown acts or faces are errors, not skipped.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

# the acts that are new in stage 1a, and the older states a directed actor may also be given a face for (they keep their own facings)
NEW_ACTS = ("beckon", "nod", "shake_head", "recoil", "bow", "kneel", "offer", "plead", "collapse", "salute", "block", "cover_face", "stamp", "laugh", "write")
OLD_ACTS = ("wave", "point", "stare", "hug", "clap", "cheer", "sad", "rock", "check", "sleep", "lie", "sit", "idle", "walk", "chat", "watch", "look")
BACK_TOO = ("bow", "kneel", "collapse")  # also seen from behind (a bow away from the camera, a figure slumped in the road)
# the facings an act needs: front and the three-quarter side; the old targeted ones keep the facings the crowd gives them (people_sheets.SIDE_BACK / SIDE_ONLY)
OLD_FACINGS = {"point": ("front", "side", "back"), "stare": ("front", "side", "back"), "check": ("front", "side", "back"), "watch": ("front", "side", "back"),
               "walk": ("front", "side", "back"), "chat": ("front", "side"), "hug": ("front", "side")}


def facings_of(act: str) -> tuple:
    if act in NEW_ACTS:
        return ("front", "side", "back") if act in BACK_TOO else ("front", "side")
    return OLD_FACINGS.get(act, ("front",))


def _load(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _entry(raw, where: str, faces: tuple, default_face: dict) -> tuple:
    facings = None
    if isinstance(raw, str):
        raw, _, fc = raw.partition(":")  # `act@face:front+side`
        facings = fc.split("+") if fc else None
        act, _, face = raw.partition("@")
    elif isinstance(raw, dict):
        act, face, facings = str(raw.get("act", "")), str(raw.get("face", "")), raw.get("facings")
    else:
        raise ValueError(f"{where}: bad directed entry {raw!r}")
    if act not in NEW_ACTS + OLD_ACTS:
        raise ValueError(f"{where}: unknown act {act!r}")
    face = face or default_face.get(act, "neutral")
    if face not in faces:
        raise ValueError(f"{where}: unknown face {face!r}")
    return act, face, tuple(facings) if facings else facings_of(act)


def _acting_pairs(block: dict):
    """Every (act, face) a hotspot's acting block (or a cast line) names, including the `then` of each state."""
    for key in ("available", "selected", "committed", "success", "failure"):
        st = block.get(key)
        while isinstance(st, dict):
            if st.get("act"):
                yield str(st["act"]), str(st.get("face", ""))
            st = st.get("then")


def run_sources(root: str = ROOT) -> list:
    """[(run.json, hotspots dir)] of the main run and of every path under content/paths."""
    out = [(os.path.join(root, "content", "run", "run.json"), os.path.join(root, "content", "run", "hotspots"))]
    pd = os.path.join(root, "content", "paths")
    if os.path.isdir(pd):
        for pid in sorted(os.listdir(pd)):
            out.append((os.path.join(pd, pid, "run.json"), os.path.join(pd, pid, "hotspots")))
    return out


def directed(chapter: str, poses: dict | None = None, root: str = ROOT) -> dict:
    """{actor id: [(act, face, facings), ...]} for a chapter (see the module doc)."""
    if poses is None:
        poses = _load(os.path.join(root, "assets", "story", "people_poses.json"))
    faces = tuple(poses["faces"])
    default_face = dict(poses["face_of"])
    found: dict = {}

    def add(aid: str, raw, where: str) -> None:
        e = _entry(raw, where, faces, default_face)
        lst = found.setdefault(str(aid), [])
        if e not in lst:
            lst.append(e)

    p = os.path.join(root, "content", "story", "directed_actors.json")
    if os.path.exists(p):
        for aid, entries in (_load(p).get(chapter) or {}).items():
            for raw in entries:
                add(aid, raw, f"directed_actors.json {chapter}/{aid}")
    for rp, hs in run_sources(root):  # the main run, then every path's own run (content/paths/<id>/run.json and its hotspots)
        run = _load(rp) if os.path.exists(rp) else {}
        maps = {w["id"]: w.get("map", "") for w in run.get("worlds", [])}
        if os.path.isdir(hs):
            for fn in sorted(os.listdir(hs)):
                if not fn.endswith(".json"):
                    continue
                doc = _load(os.path.join(hs, fn))
                for h in doc.get("hotspots", []):
                    a = h.get("acting")
                    if not a:
                        continue
                    if (h.get("map") or maps.get(h.get("world") or doc.get("world"), "")) != chapter:
                        continue
                    aid = a.get("actor") or (h.get("anchor") or {}).get("actor")
                    if not aid:  # a Bassment creature (`figure`) is a billboard, not a baked person
                        continue
                    for act, face in _acting_pairs(a):
                        add(aid, {"act": act, "face": face}, f"hotspot {h.get('id')}")
        for node in run.get("nodes", []):
            if maps.get(node.get("world", "")) != chapter:
                continue
            for line in node.get("cast", []) or []:
                if line.get("actor") and line.get("act"):
                    add(line["actor"], {"act": line["act"], "face": line.get("face", "")}, f"cast {node.get('id')}")
            for fx in node.get("block_fx", []) or []:  # a path scene's block staging may carry cast lines too (RunPlay._block_fx)
                for key in ("pass", "miss"):
                    for line in (fx.get(key) or {}).get("cast", []) or []:
                        if line.get("actor") and line.get("act"):
                            add(line["actor"], {"act": line["act"], "face": line.get("face", "")}, f"block_fx {node.get('id')}")
        for name, cine in (run.get("cinematics") or {}).items():  # an outcome's cinematic may carry cast lines too (plan 2.3c)
            if maps.get(cine.get("world", "")) != chapter:
                continue
            for line in cine.get("cast", []) or []:
                if line.get("actor") and line.get("act"):
                    add(line["actor"], {"act": line["act"], "face": line.get("face", "")}, f"cinematic {name}")
    return found


def state_key(act: str, face: str, default_face: dict) -> str:
    """The sheet's name for an act shown with a face: the plain act for its own default face, `act@face` otherwise."""
    return act if face == default_face.get(act, "neutral") else f"{act}@{face}"
