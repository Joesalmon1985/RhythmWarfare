"""Bake every actor of a chapter to indexed sprite sheets: `python3 tools/story/build_assets.py <chapter> people`.

For each actor: the wardrobe spec (wardrobe.py), the states the runtime can show them in (the activities their sector's lists give them by their own seed,
exactly as StoryCrowd.pick_activity picks, the dance set on dancing sectors, the walk, the look at the door, the hero's solo), and for each state the frames of
StoryCharacter.SHEET_CYCLES in up to three facings and three levels of detail (people.py). Identical frames are stored once. Output in
assets/story/<chapter>/people/: page_<n>.png (8-bit indexed pixels, 2048 square), palette.png (one row of 128 colours per actor) and people.json (the frame
table and, per actor, the frames of each state and facing). Deterministic: the same inputs give the same bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
import zlib
from multiprocessing import Pool

import numpy as np
from PIL import Image

from . import lib, people, wardrobe

PAGE = 2048
PAD = 1
DEFAULT_PROPS = {"drink": "cup", "toast": "cup", "phone": "phone", "paint": "brush", "carry": "tray", "serve": "tray", "check": "clipboard"}
DANCE_SET = ["idle", "dance", "cheer", "sad", "clap", "hands_up", "look", "footwork"]
BANDS = ["quiet", "dancing", "hype", "euphoric"]
DANCING = ("dance_floor", "stage", "stage_steps", "booth")
SIDE_BACK = {"walk", "pace", "serve", "watch", "stare", "point", "check", "paint", "mix"}
SIDE_ONLY = {"chat", "hug", "toast"}


def id_seed(aid: str) -> int:
    """StoryCrowd._id_seed."""
    h = 7
    for ch in aid:
        h = (h * 31 + ord(ch)) % 100003
    return h


FLAIR_MOVES = ["flair_toprock", "flair_drop", "flair_robot", "flair_spin"]


def flair_of(aid: str) -> str:
    """StoryCrowd.flair_of: the one break-dance move this person carries (about one dancer in eleven), or ''."""
    seed = id_seed(aid)
    if (seed * 31 + 7) % 10007 % 11 != 0:
        return ""
    return FLAIR_MOVES[(seed * 70 + 3) % 997 % 4]


def default_activities(flags) -> dict:
    """StoryMap.default_activities."""
    if any(f in ("dance_floor", "stage") for f in flags):
        return {"quiet": ["stand", "chat", "drink", "phone", "lean_wall"], "dancing": ["dance", "dance", "dance", "drink", "chat"],
                "hype": ["dance", "dance", "dance", "wave", "point"], "euphoric": ["dance", "dance", "wave", "point"]}
    return {"quiet": ["stand", "chat", "lean_wall"], "dancing": ["stand", "chat", "watch", "drink"], "hype": ["watch", "wave", "chat"],
            "euphoric": ["wave", "watch", "chat"]}


def picks(sector: dict, seed: int) -> set:
    acts = sector.get("activities") or default_activities(sector.get("flags", []))
    out = set()
    for rank, band in enumerate(BANDS):
        lst = acts.get(band) or acts.get("hype") or ["stand"]
        out.add(str(lst[(seed + 3 * rank) % len(lst)]))
    return out


def actor_states(actor: dict, home_sec: dict, room_secs: list, hero: bool, style: int) -> dict:
    """{state: set(facings)} the runtime can show this person in."""
    aid = str(actor["id"])
    lock = str(actor.get("activity", ""))
    seed = id_seed(aid)
    want: dict = {}

    def add(st, *fc):
        want.setdefault(st, set()).update(fc or ("front",))
    add("idle")
    add("walk", "front", "side", "back")
    add("look")
    acts = {lock} if lock else picks(home_sec, seed)
    dancing_here = any(f in DANCING for f in home_sec.get("flags", []))
    if not lock and (dancing_here or any(any(f in DANCING for f in s.get("flags", [])) for s in room_secs)):
        for st in DANCE_SET:
            add(st)
        for s in room_secs:  # a dancer who ends up on the floor (a circle, a wave) picks from the floor's list
            if any(f in ("dance_floor",) for f in s.get("flags", [])):
                acts |= picks(s, seed)
    for a in acts:
        if a == "dance":
            for st in DANCE_SET:
                add(st)
        elif a == "stand":
            add("idle")
            add("sad")
        elif a in SIDE_BACK:
            add(a, "front", "side", "back")
        elif a in SIDE_ONLY:
            add(a, "front", "side")
        else:
            add(a)
        if a in ("chat", "hug"):
            add("idle")
        if a == "toast":
            add("drink")
    if hero:
        add("idle", "front", "side", "back")
        add("cheer", "front", "side", "back")
        for k in range(5):
            add("dance_s%d" % k, "front")
    move = flair_of(aid)
    if move and not lock and not hero and "dance" in want:  # a flair dancer: their move's frames (the spin turns through every facing)
        add(move, *(("front", "side", "back") if move == "flair_spin" else ("front",)))
    if "dance" in want:
        want["dance_s%d" % style] = want.pop("dance")
    return want


def held_of(actor: dict, state: str) -> str:
    fixed = str(actor.get("prop", ""))
    if fixed:
        return fixed
    h = DEFAULT_PROPS.get(state, "")
    if h == "cup" and id_seed(str(actor["id"])) % 3 == 0:
        h = "bottle"
    return h


def _render_actor(job):
    """One actor's frames: {(state, facing, lod, i): (bytes, shape, pivot, hand)} (run in a worker)."""
    spec, states, poses, actor, face_of = job
    keys = poses["keys"]
    out = {}
    cache = {}
    for st in sorted(states):
        pst = poses["states"].get(st if not st.startswith("dance_s") else st)
        if pst is None:
            continue
        base = "dance" if st.startswith("dance_s") else st
        held = held_of(actor, base)
        face = face_of.get(base, "neutral")
        if base == "sleep":
            face = "sleep"
        for fc in sorted(states[st]):
            fci = people.FACINGS.index(fc)
            for i, row in enumerate(pst["frames"]):
                pose = dict(zip(keys, row))
                for lod in people.LODS:
                    q = tuple(round(v * (20 if lod == 1 else 10 if lod == 2 else 5), 0) for v in row)
                    ck = (base if base in ("sit", "sleep", "rock", "lie") else "_", fci, lod, held, face, q)
                    if ck not in cache:
                        img, piv, hand = people.render_frame(spec, pose, base, fci, lod, held, face, int(spec.get("seed", 0)))
                        cache[ck] = (img.tobytes(), img.shape, (round(piv[0]), round(piv[1])), (round(hand[0]), round(hand[1])))
                    out[(st, fc, lod, i)] = cache[ck]
    return out


def build(chapter: str, jobs_n: int = 4) -> dict:
    root = lib.ROOT
    data = json.load(open(os.path.join(root, "content", "story", chapter + ".json"), encoding="utf-8"))
    mp = json.load(open(os.path.join(root, "content", "story", "maps", chapter + ".json"), encoding="utf-8"))
    poses = json.load(open(os.path.join(root, "assets", "story", "people_poses.json"), encoding="utf-8"))
    sectors = {s["id"]: s for s in mp["sectors"]}
    homes = {h["actor"]: h for h in mp["homes"]}
    actors = data["actors"]
    cast = wardrobe.cast_chapter(chapter, actors)
    face_of = poses.get("face_of", {})
    jobs, metas = [], []
    for a in actors:
        aid = str(a["id"])
        view = str(a.get("view", "main"))
        h = homes.get(aid)
        if h is None:
            continue
        home_sec = sectors.get(h["sector"], {})
        room_secs = [s for s in mp["sectors"] if s.get("room") == view]
        spec = cast[aid]
        style = int(spec["seed"]) % 5
        states = actor_states(a, home_sec, room_secs, str(a.get("role", "")) == "hero", style)
        jobs.append((spec, states, poses, a, face_of))
        metas.append((aid, spec, states, style))
    with Pool(jobs_n) as pool:
        results = pool.map(_render_actor, jobs, chunksize=1)
    # pack: unique frames, tallest first per level of detail, shelf by shelf, page by page
    uniq: dict = {}
    order: list = []
    for res in results:
        for k in sorted(res, key=lambda k: (k[0], k[1], k[2], k[3])):
            b, shape, piv, hand = res[k]
            hk = hashlib.sha1(b + bytes(str(shape) + str(piv) + str(hand), "ascii")).digest()
            if hk not in uniq:
                uniq[hk] = len(order)
                order.append((b, shape, piv, hand))
    idxs = sorted(range(len(order)), key=lambda i: (-order[i][1][0], -order[i][1][1], i))
    pages = [np.zeros((PAGE, PAGE), np.uint8)]
    x = y = row_h = 0
    place = [None] * len(order)
    for i in idxs:
        b, (h, w), piv, hand = order[i]
        if x + w + PAD > PAGE:
            x, y, row_h = 0, y + row_h + PAD, 0
        if y + h + PAD > PAGE:
            pages.append(np.zeros((PAGE, PAGE), np.uint8))
            x = y = row_h = 0
        pages[-1][y:y + h, x:x + w] = np.frombuffer(b, np.uint8).reshape(h, w)
        place[i] = (len(pages) - 1, x, y, w, h, piv[0], piv[1], hand[0], hand[1])
        x += w + PAD
        row_h = max(row_h, h)
    out_dir = os.path.join(root, "assets", "story", chapter, "people")
    os.makedirs(out_dir, exist_ok=True)
    for fn in os.listdir(out_dir):
        if fn.startswith("page_") and fn.endswith(".png"):
            os.remove(os.path.join(out_dir, fn))
    files = []
    for n, pg in enumerate(pages):
        used = int(np.nonzero(pg.any(axis=1))[0].max()) + 1 if pg.any() else 1
        hh = 1
        while hh < used:
            hh *= 2
        fn = f"page_{n}.png"
        Image.fromarray(pg[:hh], "L").save(os.path.join(out_dir, fn), optimize=False, compress_level=9)
        files.append("people/" + fn)
    frames = []
    for p in place:
        frames.extend(int(v) for v in p)
    pal = []
    table = {}
    for row, (aid, spec, states, style) in enumerate(metas):
        pal.append(people.palette_row(spec["colours"]))
        res = results[row]
        st_out = {}
        for st in sorted(states):
            base = "dance" if st.startswith("dance_s") else st
            if st not in poses["states"]:
                continue
            cyc = poses["states"][st]
            n = len(cyc["frames"])
            facing_lists = []
            for fc in people.FACINGS:
                if fc not in states[st]:
                    facing_lists.append(None)
                    continue
                lst = []
                for lod in people.LODS:
                    for i in range(n):
                        b, shape, piv, hand = res[(st, fc, lod, i)]
                        hk = hashlib.sha1(b + bytes(str(shape) + str(piv) + str(hand), "ascii")).digest()
                        lst.append(uniq[hk])
                facing_lists.append(lst)
            key = st if not st.startswith("dance_s") or int(st[-1]) != style else "dance"
            st_out[key] = [float(cyc["beats"]), n] + facing_lists
            if key == "dance" and st != "dance":
                st_out[st] = st_out[key]
        table[aid] = {"row": row, "style": style, "height": round(float(spec.get("height", 1.0)), 3), "look": list(map(str, wardrobe.look_key(spec))),
                      "states": st_out}
    palimg = np.array(pal, dtype=np.uint8)  # rows x 128 x 4
    Image.fromarray(palimg, "RGBA").save(os.path.join(out_dir, "palette.png"), optimize=False, compress_level=9)
    doc = {"version": 1, "h0": people.H0, "lods": list(people.LODS), "facings": list(people.FACINGS), "pages": files, "palette": "people/palette.png",
           "frame_fields": ["page", "x", "y", "w", "h", "pivot_x", "pivot_y", "hand_x", "hand_y"], "frames": frames, "actors": table}
    with open(os.path.join(out_dir, "people.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, separators=(",", ":"), sort_keys=True)
        fh.write("\n")
    px = sum(order[i][1][0] * order[i][1][1] for i in range(len(order)))
    print(f"{chapter} people: {len(metas)} actors, {len(order)} unique frames, {len(pages)} pages, {px / 1e6:.1f} Mpx")
    return {"file": "people/people.json", "pages": files, "palette": "people/palette.png"}
