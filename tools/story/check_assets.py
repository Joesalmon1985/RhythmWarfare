#!/usr/bin/env python3
"""Sanity checks for the generated Story Campaign art: `python3 tools/story/check_assets.py [--determinism]`.

Checks Night One and every chapter whose folder exists (`mothership`). Validates the manifest against the art contract (every referenced file exists, six archetypes x two variants, every part has a
pivot inside its texture, four faces, the required layers/anchors/sprites). With --determinism it rebuilds twice and compares
hashes of every generated file. Exit code 0 when everything holds.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
STORY = os.path.join(ROOT, "assets", "story")
from art import directed as directed_mod  # noqa: E402
from art import people  # noqa: E402
ART = os.path.join(STORY, "night_one")  # the folder being checked (set per chapter by validate)
CHAPTERS = ("night_one", "mothership", "underworld", "hospital", "mental_hospital")
INTERLUDE = {"mothership": ({"ufo", "tractor_beam", "ufo_glow", "sparkle", "light_flood"}, {"ufo_hover", "beam_floor"}),
             "underworld": ({"crack_glow", "flame_jet", "portal_vortex", "embers", "dark_wash"}, {"crack_origin", "portal_centre"}),
             "hospital": ({"eyelid_top", "eyelid_bottom", "white_wash", "monitor_line"}, set()),
             "mental_hospital": ({"fluoro_wash", "tunnel_vignette", "cell_door", "flicker_tube"}, set())}
ARCH_IDS = {"mothership": {"grey", "antenna", "blob", "insect", "cyclops", "tentacle"},
            "underworld": {"imp", "brute", "fiend", "skeleton", "flame", "horned_queen"},
            "hospital": {"mum", "dad", "granny", "kid", "nurse", "doctor"},
            "mental_hospital": {"pirate", "king", "chef", "superhero", "ballerina", "orderly"}}
PIECE_ANIMS = {"none", "pulse", "flicker", "rotate", "bob", "sway"}

JOINTS = {"hips", "torso", "head", "shoulder_l", "elbow_l", "shoulder_r", "elbow_r", "hip_l", "hip_r"}
LAYERS = {"backdrop", "speaker_l", "speaker_r", "riser", "desk_top"}
SPRITES = {"woofer", "fixture", "disco_ball", "glowstick", "door_open", "spot_pool", "haze_a", "haze_b", "glow", "beam", "vignette",
           "confetti", "desk_lip_glow", "pad_bezel", "platter", "knob", "fader_slot", "fader_cap", "crossfader", "vu_segment", "deck_screw"}


def svg_size(path: str):
    with open(path, encoding="utf-8") as fh:
        head = fh.read(400)
    m = re.search(r'width="([\d.]+)" height="([\d.]+)"', head)
    return float(m.group(1)), float(m.group(2))


def png_size(path: str):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def size_of(rel: str):
    p = os.path.join(ART, rel)
    return svg_size(p) if rel.endswith(".svg") else png_size(p)


def check_entry(errors, where, e, need_pivot=True, margin=1.0):
    p = os.path.join(ART, e["file"])
    if not os.path.exists(p):
        errors.append(f"{where}: missing {e['file']}")
        return
    if need_pivot:
        w, h = size_of(e["file"])
        px, py = e["pivot"]
        if not (-margin <= px <= w + margin and -margin <= py <= h + margin):
            errors.append(f"{where}: pivot {e['pivot']} outside texture {w}x{h}")


def validate(chapter: str = "night_one") -> list:
    global ART
    ART = os.path.join(STORY, chapter)
    errors: list = []
    with open(os.path.join(ART, "manifest.json"), encoding="utf-8") as fh:
        m = json.load(fh)
    arch = m["archetypes"]
    if len(arch) != 6:
        errors.append(f"expected 6 archetypes, got {len(arch)}")
    for name, a in arch.items():
        if set(a["joints"]) != JOINTS:
            errors.append(f"{name}: joints {sorted(a['joints'])}")
        if set(a["variants"]) != {"a", "b"}:
            errors.append(f"{name}: variants {list(a['variants'])}")
        for v, vd in a["variants"].items():
            tag = f"{name}_{v}"
            need = {"torso", "head", "arm_l_up", "arm_l_fore", "arm_r_up", "arm_r_fore", "leg_l", "leg_r"}
            have = {p["name"] for p in vd["parts"]}
            if not need <= have:
                errors.append(f"{tag}: missing parts {sorted(need - have)}")
            for p in vd["parts"]:
                if p["joint"] not in JOINTS:
                    errors.append(f"{tag}.{p['name']}: bad joint {p['joint']}")
                check_entry(errors, f"{tag}.{p['name']}", p, margin=400.0)  # a joint may lie outside a hair or hood texture
                if p.get("swing") and "swing_pivot" not in p:
                    errors.append(f"{tag}.{p['name']}: swing without swing_pivot")
            if set(vd["faces"]) != {"neutral", "happy", "cheer", "sad"}:
                errors.append(f"{tag}: faces {list(vd['faces'])}")
            for e, fd in vd["faces"].items():
                check_entry(errors, f"{tag}.face_{e}", fd, margin=400.0)
    sil = m["silhouettes"]
    if len(sil) != 3:
        errors.append(f"expected 3 silhouettes, got {len(sil)}")
    for n, s in sil.items():
        for state in ("idle", "up"):
            check_entry(errors, f"{n}.{state}", s[state])
    st = m["stage"]
    ids = {l["id"] for l in st["layers"]}
    if not LAYERS <= ids:
        errors.append(f"missing layers {sorted(LAYERS - ids)}")
    for l in st["layers"]:
        check_entry(errors, f"layer {l['id']}", l, need_pivot=False)
    if "anchors" in st:
        errors.append("stage.anchors is a dead field of the 2D rooms: the map places everything (tools/story/build_assets.py strips it)")
    if not SPRITES <= set(st["sprites"]):
        errors.append(f"missing sprites {sorted(SPRITES - set(st['sprites']))}")
    for sid, e in st["sprites"].items():
        check_entry(errors, f"sprite {sid}", e)
    if chapter != "night_one":
        chapter_checks(errors, chapter, m, st)
    texture_checks(errors, chapter, m)
    people_checks(errors, chapter, m)
    if chapter == CHAPTERS[0]:
        pose_checks(errors)
    return errors


# the 2.5D world's texture tiles (tools/story/art/tiles.py): chapters list them under manifest["textures"] once their world is authored
TEXTURES_REQUIRED = {"night_one": {"wall_brick", "wall_panel", "wall_led", "trim", "floor_led", "floor_dark", "floor_stage", "ceil_truss",
                                   "wall_bar", "bar_front", "toilet_tile", "toilet_floor", "cubicle_door", "wall_door"}}


def texture_checks(errors, chapter, m) -> None:
    tex = m.get("textures")
    if tex is None:
        if chapter in TEXTURES_REQUIRED:
            errors.append("manifest has no textures section")
        return
    missing = TEXTURES_REQUIRED.get(chapter, set()) - set(tex)
    if missing:
        errors.append(f"textures missing {sorted(missing)}")
    for tid, e in tex.items():
        p = os.path.join(ART, e.get("file", ""))
        if not os.path.exists(p):
            errors.append(f"texture {tid}: missing {e.get('file')}")
            continue
        w, h = png_size(p)
        sky = tid.startswith("sky_")  # a sky strip wraps once around the world: 256 x 64
        if [w, h] != list(e.get("size", [])) or (sky and (w, h) != (256, 64)) or (not sky and (w != h or w not in (32, 64, 128))):
            errors.append(f"texture {tid}: size {w}x{h} (manifest {e.get('size')}); tiles are square 32, 64 or 128 px, a sky is 256 x 64")
        if float(e.get("metres", 0)) <= 0:
            errors.append(f"texture {tid}: metres must be positive")
    on_disk = {fn for fn in os.listdir(os.path.join(ART, "textures")) if fn.endswith(".png")} if os.path.isdir(os.path.join(ART, "textures")) else set()
    listed = {os.path.basename(e["file"]) for e in tex.values()}
    if on_disk - listed:
        errors.append(f"textures on disk but not in the manifest: {sorted(on_disk - listed)}")


PEOPLE_STATES = {"idle", "walk"}  # every person has at least these
POSES = json.load(open(os.path.join(STORY, "people_poses.json"), encoding="utf-8"))
FACE_LIST = list(people.FACES)
DIRECTED: dict = {}  # {actor id: [(act, face, facings)]} of the chapter being checked (directed.py: the data decides which people are baked in which acts and faces)
SHEET_STATES = {"idle", "dance", "cheer", "hands_up", "sad", "clap", "walk", "footwork", "look", "drink", "toast", "chat", "point", "phone", "lean_wall", "sit", "lie",
                "sleep", "paint", "pace", "serve", "carry", "check", "stare", "rock", "hug", "queue", "wave", "watch", "mix",
                "dance_s0", "dance_s1", "dance_s2", "dance_s3", "dance_s4", "flair_toprock", "flair_drop", "flair_robot", "flair_spin",
                "beckon", "nod", "shake_head", "recoil", "bow", "kneel", "offer", "plead", "collapse", "salute", "block", "cover_face", "stamp", "laugh", "write"}


def pose_checks(errors) -> None:
    """The dumped poses (tools/story/dump_poses.gd) and the pixel rig agree on the faces and the acts, and every face and act has a cycle and a default face."""
    if list(POSES.get("faces", [])) != FACE_LIST:
        errors.append(f"people_poses.json faces {POSES.get('faces')} != people.FACES {FACE_LIST} (rerun tools/story/dump_poses.gd)")
    if list(POSES.get("acts", [])) != list(directed_mod.NEW_ACTS):
        errors.append(f"people_poses.json acts {POSES.get('acts')} != directed.NEW_ACTS (rerun tools/story/dump_poses.gd)")
    for act in directed_mod.NEW_ACTS:
        if act not in POSES["states"]:
            errors.append(f"people_poses.json has no cycle for {act}")
        if POSES["face_of"].get(act) not in FACE_LIST:
            errors.append(f"act {act} has no default face in FACE_OF")
    for st, f in POSES["face_of"].items():
        if f not in FACE_LIST:
            errors.append(f"FACE_OF[{st}] = {f} is not a face")


def people_checks(errors, chapter, m) -> None:
    """The baked people (tools/story/art/people_sheets.py): every actor of the chapter has a sheet entry with the states the runtime needs (their own activity,
    the dance set on dancing sectors, the walk), every frame lies inside its page, the palette has a row per actor, no two people in a room share build, hair
    and top, and the frames are a sensible size (a full-size frame stands about as tall as the person's build says, h0 x height, plus hair, horns or a hat)."""
    sec = m.get("people")
    if not sec:
        errors.append("manifest has no people section (build_assets.py <chapter> people)")
        return
    path = os.path.join(ART, sec["file"])
    if not os.path.exists(path):
        errors.append(f"people: missing {sec['file']}")
        return
    doc = json.load(open(path, encoding="utf-8"))
    pages = []
    for f in doc["pages"]:
        p = os.path.join(ART, f)
        if not os.path.exists(p):
            errors.append(f"people: missing page {f}")
            return
        pages.append(png_size(p))
    pw, ph = png_size(os.path.join(ART, doc["palette"]))
    fr = doc["frames"]
    if len(fr) % 9:
        errors.append("people: frame table is not a multiple of 9 fields")
        return
    nfr = len(fr) // 9
    for i in range(nfr):
        pg, x, y, w, h = fr[i * 9:i * 9 + 5]
        if pg >= len(pages) or x + w > pages[pg][0] or y + h > pages[pg][1] or w <= 0 or h <= 0:
            errors.append(f"people: frame {i} outside its page")
            break
    with open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8") as fh:
        data = json.load(fh)
    global DIRECTED
    DIRECTED = directed_mod.directed(chapter, POSES)
    for aid in DIRECTED:
        if aid not in {str(a["id"]) for a in data["actors"]}:
            errors.append(f"people: directed actor {aid} is not an actor of {chapter}")
    looks: dict = {}
    for a in data["actors"]:
        aid = str(a["id"])
        e = doc["actors"].get(aid)
        if e is None:
            errors.append(f"people: no sheet for actor {aid}")
            continue
        if e["row"] >= ph or pw != 128:
            errors.append(f"people: {aid} palette row {e['row']} outside the palette ({pw}x{ph})")
        st = e["states"]
        need = set(PEOPLE_STATES)
        if a.get("activity"):
            need.add(str(a["activity"]) if str(a["activity"]) != "dance" else "dance")
        if not need <= set(st):
            errors.append(f"people: {aid} lacks states {sorted(need - set(st))}")
        for k, v in st.items():
            base, _, face = k.partition("@")  # `beckon@plea`: a directed act shown with another face
            if base not in SHEET_STATES or (face and face not in FACE_LIST):
                errors.append(f"people: {aid} unknown state {k}")
            n = v[1]
            if v[2] is None or len(v[2]) != 3 * n:
                errors.append(f"people: {aid}.{k} has no front frames for three levels of detail")
            for lst in v[2:]:
                if lst is not None and (len(lst) != 3 * n or max(lst) >= nfr):
                    errors.append(f"people: {aid}.{k} frame list malformed")
        for act, face, facings in DIRECTED.get(aid, []):  # a directed person lacks no act and no face the story gives them
            key = directed_mod.state_key(act, face, POSES["face_of"])
            e2 = st.get(key)
            if e2 is None:
                errors.append(f"people: directed actor {aid} lacks {key}")
                continue
            for fcn in facings:
                if e2[2 + people.FACINGS.index(fcn)] is None:
                    errors.append(f"people: directed actor {aid}.{key} lacks the {fcn} facing")
        idle = st.get("idle")
        if idle:
            h = fr[idle[2][0] * 9 + 4]
            hb = float(e["height"]) * doc.get("h0", 112)  # the person's own standing height at full size (hair, horns and hats on top)
            lo, hi = int(hb * 0.85), int(hb * 1.4) + 4
            if not lo <= h <= hi:
                errors.append(f"people: {aid} stands {h} px tall at full size (expected {lo} to {hi})")
        room = str(a.get("view", "main"))
        key = tuple(e["look"][:5])
        if key in looks.setdefault(room, {}):
            errors.append(f"people: {aid} and {looks[room][key]} in {room} share build, hair and top {key}")
        looks[room][key] = aid


VIEWS = {"mothership": ["gallery", "reactor", "bridge"], "underworld": ["court", "pit", "furnace"],
         "hospital": ["corridor", "cafeteria", "garden"], "mental_hospital": ["corridor", "art_room", "courtyard"]}


def view_checks(errors, chapter, st) -> None:
    """The rooms (crowd views) that own set pieces: their ids in order, 2 to 4 pieces each."""
    want = VIEWS.get(chapter)
    if not want:
        return
    views = {v["id"]: v for v in st.get("views", [])}
    if list(views) != want:
        errors.append(f"views {list(views)} != {want}")
    for vid, v in views.items():
        if not 2 <= len(v.get("pieces", [])) <= 4:
            errors.append(f"view {vid}: expected 2 to 4 pieces")
        for dead in ("layers", "anchors", "palette_hint"):
            if dead in v:
                errors.append(f"view {vid}: dead field {dead}")


def chapter_checks(errors, chapter, m, st) -> None:
    """Extra checks of the chapter addendum: archetype ids, 5 floor rows, 4 woofers, extra anchors, pieces, interlude."""
    ids = ARCH_IDS.get(chapter)
    if ids and set(m["archetypes"]) != ids:
        errors.append(f"archetype ids {sorted(m['archetypes'])} != {sorted(ids)}")
    for name, a in m["archetypes"].items():
        for v in a["variants"].values():
            gh = v.get("glow_hand", {})
            if gh.get("joint") != "elbow_r" or len(gh.get("at", [])) != 2:
                errors.append(f"{name}: glow_hand {gh}")
    view_checks(errors, chapter, st)
    pieces = st.get("pieces", [])
    if not 6 <= len(pieces) <= 8:
        errors.append(f"expected 6 to 8 pieces, got {len(pieces)}")
    seen = set()
    for p in pieces:
        if p["id"] in seen:
            errors.append(f"duplicate piece {p['id']}")
        seen.add(p["id"])
        if p["anim"] not in PIECE_ANIMS or p["z"] not in ("behind", "front"):
            errors.append(f"piece {p['id']}: anim {p['anim']} z {p['z']}")
        check_entry(errors, f"piece {p['id']}", p, need_pivot="pivot" in p)
    if chapter in INTERLUDE:
        il = m.get("interlude")
        sprites, anchors = INTERLUDE[chapter]
        if not il:
            errors.append("missing interlude")
            return
        if not sprites <= set(il["sprites"]):
            errors.append(f"interlude sprites missing {sorted(sprites - set(il['sprites']))}")
        if not anchors <= set(il["anchors"]):
            errors.append(f"interlude anchors missing {sorted(anchors - set(il['anchors']))}")
        for sid, e in il["sprites"].items():
            check_entry(errors, f"interlude {sid}", e)


def tree_hash() -> str:
    h = hashlib.sha256()
    for base, _d, files in sorted(os.walk(ART)):
        for fn in sorted(files):
            if fn.endswith(".import"):
                continue
            with open(os.path.join(base, fn), "rb") as fh:
                h.update(os.path.relpath(os.path.join(base, fn), ART).encode() + fh.read())
    return h.hexdigest()


def all_hash() -> str:
    global ART
    h = hashlib.sha256()
    for ch in CHAPTERS:
        ART = os.path.join(STORY, ch)
        if os.path.isdir(ART):
            h.update(tree_hash().encode())
    return h.hexdigest()


def main(argv) -> int:
    errors: list = []
    for ch in CHAPTERS:
        if os.path.isdir(os.path.join(STORY, ch)):
            errs = validate(ch)
            errors += [f"[{ch}] {e}" for e in errs]
            print(f"{ch}:", "OK" if not errs else f"{len(errs)} problems")
    for e in errors:
        print("FAIL", e)
    if "--determinism" in argv:
        build = os.path.join(HERE, "build_assets.py")
        subprocess.run([sys.executable, build], check=True, stdout=subprocess.DEVNULL)
        a = all_hash()
        subprocess.run([sys.executable, build], check=True, stdout=subprocess.DEVNULL)
        b = all_hash()
        print("determinism:", "OK" if a == b else "FAIL (outputs differ between runs)")
        if a != b:
            errors.append("not deterministic")
    print("manifest check:", "OK" if not errors else f"{len(errors)} problems")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
