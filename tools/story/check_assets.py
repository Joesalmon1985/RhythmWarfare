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
STORY = os.path.join(ROOT, "assets", "story")
ART = os.path.join(STORY, "night_one")  # the folder being checked (set per chapter by validate)
CHAPTERS = ("night_one", "mothership", "underworld", "hospital", "mental_hospital")
CHAPTER_ANCHORS = {"floor_grid", "wall_left_x", "wall_right_x", "horizon_y"}
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
ANCHORS = {"led_screen", "doorway", "floor_rows", "floor_polygon", "light_points", "woofers", "disco_ball", "riser", "circle_centre", "circle_radii"}
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
    if not ANCHORS <= set(st["anchors"]):
        errors.append(f"missing anchors {sorted(ANCHORS - set(st['anchors']))}")
    if len(st["anchors"]["light_points"]) != 8:
        errors.append("light_points must have 8 points")
    rows = st["anchors"]["floor_rows"]
    if not (4 <= len(rows) <= 6) or rows[-1]["scale"] != 1.0 or rows[-1]["y"] > 440:
        errors.append(f"floor_rows: {rows}")
    if not SPRITES <= set(st["sprites"]):
        errors.append(f"missing sprites {sorted(SPRITES - set(st['sprites']))}")
    for sid, e in st["sprites"].items():
        check_entry(errors, f"sprite {sid}", e)
    if chapter != "night_one":
        chapter_checks(errors, chapter, m, st)
    texture_checks(errors, chapter, m)
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


VIEW_ANCHORS = {"floor_rows", "floor_polygon", "light_points", "circle_centre", "circle_radii", "vanish"}
VIEWS = {"mothership": ["gallery", "reactor", "bridge"], "underworld": ["court", "pit", "furnace"],
         "hospital": ["corridor", "cafeteria", "garden"], "mental_hospital": ["corridor", "art_room", "courtyard"]}


def view_checks(errors, chapter, st) -> None:
    """The moving-camera rooms (ART_CONTRACT_VIEWS.md): ids, layer files, required anchors, 8 light points, 5 floor rows, passage frame."""
    want = VIEWS.get(chapter)
    if not want:
        return
    views = {v["id"]: v for v in st.get("views", [])}
    if list(views) != want:
        errors.append(f"views {list(views)} != {want}")
    for vid, v in views.items():
        for l in v.get("layers", []):
            if not os.path.exists(os.path.join(STORY, chapter, l["file"])):
                errors.append(f"view {vid}: missing layer file {l['file']}")
        missing = VIEW_ANCHORS - set(v.get("anchors", {}))
        if missing:
            errors.append(f"view {vid}: missing anchors {sorted(missing)}")
        a = v.get("anchors", {})
        if len(a.get("light_points", [])) != 8 or len(a.get("floor_rows", [])) != 5:
            errors.append(f"view {vid}: needs 8 light points and 5 floor rows")
        if not 2 <= len(v.get("pieces", [])) <= 4:
            errors.append(f"view {vid}: expected 2 to 4 pieces")
    if "passage_frame" not in st.get("sprites", {}):
        errors.append("missing sprite passage_frame")


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
    if not CHAPTER_ANCHORS <= set(st["anchors"]):
        errors.append(f"missing anchors {sorted(CHAPTER_ANCHORS - set(st['anchors']))}")
    if len(st["anchors"]["floor_rows"]) != 5:
        errors.append("floor_rows must have 5 rows")
    if len(st["anchors"]["woofers"]) != 4:
        errors.append("woofers must have 4 entries")
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
