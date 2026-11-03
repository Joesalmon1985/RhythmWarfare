#!/usr/bin/env python3
"""Sanity checks for the generated Night One art: `python3 tools/story/check_assets.py [--determinism]`.

Validates the manifest against the art contract (every referenced file exists, six archetypes x two variants, every part has a
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
ART = os.path.join(ROOT, "assets", "story", "night_one")

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


def validate() -> list:
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
    return errors


CHAPTERS = {"underworld": dict(archetypes={"imp", "brute", "fiend", "skeleton", "flame", "horned_queen"},
                               pieces={"lava_flow", "fire_pits_left", "fire_pits_right", "hellmouth_portal", "chains_swing", "skull_throne", "bone_arches", "ember_rain"},
                               interlude={"crack_glow", "flame_jet", "portal_vortex", "embers", "dark_wash"},
                               anchors={"crack_origin", "portal_centre"})}
CHAPTER_ANCHORS = {"floor_grid", "wall_left_x", "wall_right_x", "horizon_y"}
ANIMS = {"none", "pulse", "flicker", "rotate", "bob", "sway"}


def validate_chapter(name: str) -> list:
    """The base contract (validate) on assets/story/<name>/, plus the chapters addendum: archetype ids, stage.pieces, interlude."""
    global ART
    spec = CHAPTERS[name]
    saved = ART
    ART = os.path.join(ROOT, "assets", "story", name)
    try:
        errors = [f"{name}: {e}" for e in validate()]
        with open(os.path.join(ART, "manifest.json"), encoding="utf-8") as fh:
            m = json.load(fh)
        if set(m["archetypes"]) != spec["archetypes"]:
            errors.append(f"{name}: archetype ids {sorted(m['archetypes'])}")
        st = m["stage"]
        if not CHAPTER_ANCHORS <= set(st["anchors"]):
            errors.append(f"{name}: missing anchors {sorted(CHAPTER_ANCHORS - set(st['anchors']))}")
        if len(st["anchors"]["woofers"]) != 4:
            errors.append(f"{name}: woofers must have 4 entries")
        pieces = st.get("pieces", [])
        if not 6 <= len(pieces) <= 8:
            errors.append(f"{name}: expected 6 to 8 pieces, got {len(pieces)}")
        if not spec["pieces"] <= {p["id"] for p in pieces}:
            errors.append(f"{name}: missing pieces {sorted(spec['pieces'] - {p['id'] for p in pieces})}")
        for p in pieces:
            if p["anim"] not in ANIMS or p["z"] not in ("behind", "front"):
                errors.append(f"{name}: piece {p['id']} bad anim/z {p['anim']}/{p['z']}")
            check_entry(errors, f"{name} piece {p['id']}", p, need_pivot=False)
        il = m.get("interlude", {})
        for sid in spec["interlude"]:
            if sid not in il.get("sprites", {}):
                errors.append(f"{name}: interlude sprite {sid} missing")
        for sid, e in il.get("sprites", {}).items():
            check_entry(errors, f"{name} interlude {sid}", e)
        if not spec["anchors"] <= set(il.get("anchors", {})):
            errors.append(f"{name}: interlude anchors missing {sorted(spec['anchors'] - set(il.get('anchors', {})))}")
        return errors
    finally:
        ART = saved


def tree_hash(art=None) -> str:
    art = art or ART
    h = hashlib.sha256()
    for base, _d, files in sorted(os.walk(art)):
        for fn in sorted(files):
            if fn.endswith(".import"):
                continue
            with open(os.path.join(base, fn), "rb") as fh:
                h.update(os.path.relpath(os.path.join(base, fn), art).encode() + fh.read())
    return h.hexdigest()


def main(argv) -> int:
    errors = validate()
    for ch in CHAPTERS:
        if os.path.exists(os.path.join(ROOT, "assets", "story", ch, "manifest.json")):
            errors += validate_chapter(ch)
    for e in errors:
        print("FAIL", e)
    if "--determinism" in argv:
        build = os.path.join(HERE, "build_assets.py")
        subprocess.run([sys.executable, build], check=True, stdout=subprocess.DEVNULL)
        dirs = [ART] + [os.path.join(ROOT, "assets", "story", ch) for ch in CHAPTERS]
        a = [tree_hash(d) for d in dirs]
        subprocess.run([sys.executable, build], check=True, stdout=subprocess.DEVNULL)
        b = [tree_hash(d) for d in dirs]
        print("determinism:", "OK" if a == b else "FAIL (outputs differ between runs)")
        if a != b:
            errors.append("not deterministic")
    print("manifest check:", "OK" if not errors else f"{len(errors)} problems")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
