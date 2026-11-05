#!/usr/bin/env python3
"""Zoomed head sheets of the baked people: `python3 tools/story/face_sheets.py <tag> [chapter...] [--zoom 8] [--out docs/shots/faces]`
(the tag `acting` writes the fourteen faces and the directed acts instead: docs/shots/faces/<chapter>_acting.jpg, see acting_sheet).

docs/shots/faces/<chapter>_<tag>.jpg: for every actor of the chapter, the head cropped from the built sheets (assets/story/<chapter>/people/) and shown
magnified (nearest neighbour, one sheet pixel = `zoom` x `zoom`, unlit) in the face states the actor has: neutral (idle), happy (dance / chat), cheer and
sad, front and three-quarter (the walk, or the actor's own side state), the back, then the half and quarter levels of detail of the idle front (each at
the same zoom, so they show as the small heads they are). The tag is a free label (`before`, `after`). The head is located from the actor's wardrobe spec
and the dumped pose (people.Body), so the crop follows a leaning or bobbing head; everything shown is the shipped sheet pixels.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from art import directed as directed_mod  # noqa: E402
from art import people, wardrobe  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CHAPTERS = ("night_one", "mothership", "underworld", "hospital", "mental_hospital")
BG = (24, 18, 36)
CELL_BG = (40, 34, 56)

# (label, candidate states, facing, lod): the first state the actor has is shown
COLUMNS = [
    ("neutral", ("idle", "stare", "watch", "walk"), 0, 1),
    ("happy", ("dance", "chat", "clap", "wave", "toast"), 0, 1),
    ("cheer", ("cheer", "hands_up", "solo"), 0, 1),
    ("sad", ("sad", "rock"), 0, 1),
    ("3/4", ("walk", "chat", "watch", "serve", "pace"), 1, 1),
    ("back", ("walk", "watch", "pace"), 2, 1),
    ("lod2", ("idle", "walk"), 0, 2),
    ("lod4", ("idle", "walk"), 0, 4),
]


def load(chapter):
    d = os.path.join(ROOT, "assets", "story", chapter, "people")
    doc = json.load(open(os.path.join(d, "people.json"), encoding="utf-8"))
    pages = [np.array(Image.open(os.path.join(ROOT, "assets", "story", chapter, p))) for p in doc["pages"]]
    pal = np.array(Image.open(os.path.join(ROOT, "assets", "story", chapter, doc["palette"])).convert("RGBA"))
    return doc, pages, pal


def head_crop(doc, pages, pal, row, fidx, spec, pose, state, fc, lod):
    """The head of one frame as an RGBA image (a box around the head centre, rig -> image through the frame's pivot)."""
    f = doc["frames"][fidx * 9:fidx * 9 + 9]
    pg, x, y, w, h, px, py = f[:7]
    idx = pages[pg][y:y + h, x:x + w]
    S = people.H0 / lod * float(spec.get("height", 1.0))
    b = people.Body(spec, pose, S, fc, state)
    hx, hy = b.head_c
    half_w = int(round(b.head_w * 0.95 + 2))
    half_h = int(round(b.head_h * 0.8 + 2))
    cx, cy = px + hx, py + hy - b.head_h * 0.1
    x0, y0 = int(round(cx)) - half_w, int(round(cy)) - half_h
    out = np.zeros((2 * half_h, 2 * half_w, 4), np.uint8)
    out[..., :3] = CELL_BG
    out[..., 3] = 255
    for r in range(2 * half_h):
        for c in range(2 * half_w):
            ix, iy = x0 + c, y0 + r
            if 0 <= ix < w and 0 <= iy < h and idx[iy, ix] > 0:
                out[r, c] = pal[row][idx[iy, ix] & 127]
    return Image.fromarray(out, "RGBA")


def sheet(chapter, tag, out_dir, zoom):
    doc, pages, pal = load(chapter)
    data = json.load(open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8"))
    poses = json.load(open(os.path.join(ROOT, "assets", "story", "people_poses.json"), encoding="utf-8"))
    keys = poses["keys"]
    cast = wardrobe.cast_chapter(chapter, data["actors"])
    ids = [str(a["id"]) for a in data["actors"] if str(a["id"]) in doc["actors"]]
    by_id = {str(a["id"]): a for a in data["actors"]}
    # one full-size head cell: the largest box any head needs at lod 1
    cw, chh = 0, 0
    rows = []
    for aid in ids:
        a = doc["actors"][aid]
        spec = cast[aid]
        cells = []
        for label, cands, fc, lod in COLUMNS:
            im = None
            for st in cands:
                e = a["states"].get(st)
                if not e or e[2 + fc] is None:
                    continue
                pst = "dance_s%d" % a["style"] if st == "dance" else st
                cyc = poses["states"].get(pst)
                if cyc is None:
                    continue
                n = e[1]
                li = people.LODS.index(lod)
                fidx = e[2 + fc][li * n + 0]
                pose = dict(zip(keys, cyc["frames"][0]))
                base = "dance" if st.startswith("dance") else st
                im = head_crop(doc, pages, pal, a["row"], fidx, spec, pose, base, fc, lod)
                break
            cells.append((label, im))
            if im is not None and lod == 1:
                cw, chh = max(cw, im.width), max(chh, im.height)
        rows.append((aid, cells))
    cw, chh = cw * zoom, chh * zoom
    gap = 6
    per_line = 2  # two actors side by side
    line_w = len(COLUMNS) * (cw + gap) + 90
    W = per_line * line_w + 20
    lines = (len(rows) + per_line - 1) // per_line
    H = 40 + lines * (chh + 30)
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((10, 8), f"{chapter} faces ({tag}): heads from the built sheets, 1 sheet pixel = {zoom}x{zoom}, unlit. Columns: "
            + ", ".join(c[0] for c in COLUMNS), fill=(220, 210, 240))
    for i, (aid, cells) in enumerate(rows):
        ox = 10 + (i % per_line) * line_w
        oy = 34 + (i // per_line) * (chh + 30)
        arch = str(by_id[aid].get("archetype", ""))
        dr.text((ox, oy + 4), aid, fill=(220, 210, 240))
        dr.text((ox, oy + 18), arch[:12], fill=(150, 140, 180))
        for k, (label, im) in enumerate(cells):
            x = ox + 90 + k * (cw + gap)
            dr.rectangle((x, oy, x + cw - 1, oy + chh - 1), fill=CELL_BG)
            if im is not None:
                big = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
                img.paste(big, (x + (cw - big.width) // 2, oy + (chh - big.height) // 2))
            dr.text((x + 2, oy + chh + 2), label, fill=(140, 130, 170))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{chapter}_{tag}.jpg")
    img.save(path, quality=90)
    print(path, img.size)
    return path


# ---- the acting sheet: the fourteen faces and the directed acts of the directed actors (plan 2.1, 2.2) ---------------------------------------------------------

# the four old faces come from the states that wear them; the ten acted ones from `stare@<face>` (every directed actor has them baked)
OLD_FACE_STATES = {"neutral": ("idle", "stare", "watch", "walk"), "happy": ("dance", "chat", "clap", "wave", "toast"), "cheer": ("cheer", "hands_up", "solo"),
                   "sad": ("sad", "rock")}


def face_state_keys(face, states=None, face_of=None):
    """The states of an actor that wear `face`: for the four old faces the crowd's states; for an acted face every directed state with that face (`act@face`, or an act whose own face it is),
    the first one is shown. Since stage 1d the directed people are the ones the story directs, each baked only in the acts and faces it uses, so a face an actor never wears has no cell."""
    if face in OLD_FACE_STATES:
        return OLD_FACE_STATES[face]
    if states is None:
        return (f"stare@{face}",)
    found = []
    for k in states:
        base, _, fc = k.partition("@")
        if base.startswith("dance"):
            continue
        if (fc or (face_of or {}).get(base, "neutral")) == face and (fc or base in directed_mod.NEW_ACTS):
            found.append(k)
    return tuple(sorted(found, key=lambda k: (k.partition("@")[0] not in directed_mod.NEW_ACTS, k)))


def pose_of(poses, key, frame=0):
    base = key.partition("@")[0]
    cyc = poses["states"].get("dance_s0" if base == "dance" else base)
    return base, (dict(zip(poses["keys"], cyc["frames"][frame])) if cyc else None)


def frame_image(doc, pages, pal, row, fidx):
    """A whole frame as RGBA and its feet pivot."""
    f = doc["frames"][fidx * 9:fidx * 9 + 9]
    pg, x, y, w, h, px, py = f[:7]
    idx = pages[pg][y:y + h, x:x + w]
    out = np.zeros((h, w, 4), np.uint8)
    on = idx > 0
    colours = pal[row][idx & 127]
    out[on] = colours[on]
    out[on, 3] = 255
    return Image.fromarray(out, "RGBA"), (px, py)


def acting_sheet(chapter, out_dir, zoom=5, tag="acting"):
    """docs/shots/faces/<chapter>_acting.jpg: for every directed actor the fourteen faces (front, three-quarter and the half level of detail) cropped from the built
    sheets, and for actors directed in acts the acts (the middle frame of each cycle, front and three-quarter), unlit."""
    doc, pages, pal = load(chapter)
    data = json.load(open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8"))
    poses = json.load(open(os.path.join(ROOT, "assets", "story", "people_poses.json"), encoding="utf-8"))
    cast = wardrobe.cast_chapter(chapter, data["actors"])
    by_id = {str(a["id"]): a for a in data["actors"]}
    dire = directed_mod.directed(chapter, poses)
    ids = [aid for aid in dire if aid in doc["actors"]]
    if not ids:
        return None
    faces = list(people.FACES)
    sections = []  # (label, [(row title, [(cell label, image or None)])])
    cw = ch = 0
    for aid in ids:
        a = doc["actors"][aid]
        spec = cast[aid]
        rows = []
        for title, fc, lod in (("front", 0, 1), ("3/4", 1, 1), ("half size", 0, 2)):
            cells = []
            for face in faces:
                im = None
                for key in face_state_keys(face, a["states"], poses["face_of"]):
                    e = a["states"].get(key)
                    if not e or e[2 + fc] is None:
                        continue
                    base, pose = pose_of(poses, key)
                    if pose is None:
                        continue
                    n = e[1]
                    fidx = e[2 + fc][people.LODS.index(lod) * n]
                    im = head_crop(doc, pages, pal, a["row"], fidx, spec, pose, "dance" if base.startswith("dance") else base, fc, lod)
                    break
                cells.append((face, im))
                if im is not None and lod == 1:
                    cw, ch = max(cw, im.width), max(ch, im.height)
            rows.append((title, cells))
        sections.append((f"{aid} {by_id[aid].get('archetype', '')}", rows))
    cw, ch = cw * zoom, ch * zoom
    gap = 4
    W = len(faces) * (cw + gap) + 16
    face_h = sum(len(rows) * (ch + 14) + 22 for _, rows in sections)
    act_blocks = []
    az = 2
    for aid in ids:
        a = doc["actors"][aid]
        keys = [k for k in a["states"] if k in directed_mod.NEW_ACTS]
        if keys:
            keys.sort(key=lambda k: directed_mod.NEW_ACTS.index(k))
            act_blocks.append((aid, keys))
    frames_img = {}
    acw = ach_up = ach_dn = 0
    for aid, keys in act_blocks:
        a = doc["actors"][aid]
        for k in keys:
            e = a["states"][k]
            n = e[1]
            for fc in (0, 1):
                if e[2 + fc] is None:
                    continue
                im, piv = frame_image(doc, pages, pal, a["row"], e[2 + fc][n // 2])
                frames_img[(aid, k, fc)] = (im, piv)
                acw = max(acw, im.width)
                ach_up = max(ach_up, int(piv[1]))
                ach_dn = max(ach_dn, im.height - int(piv[1]))
    per_line = max(1, (W - 16) // ((acw + 6) * az))
    cell_h = (ach_up + ach_dn + 4) * az + 14
    act_h = sum(22 + 2 * ((len(keys) + per_line - 1) // per_line) * cell_h for _, keys in act_blocks)
    H = 30 + face_h + act_h + 10
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((8, 8), f"{chapter}: the fourteen faces (each directed actor: front, three-quarter, half size; heads from the built sheets, 1 sheet pixel = {zoom}x{zoom}, "
            "unlit), then the acts (middle frame of each cycle, front and three-quarter)", fill=(220, 210, 240))
    y = 30
    for label, rows in sections:
        dr.text((8, y), label, fill=(255, 255, 160))
        y += 14
        for title, cells in rows:
            for k, (face, im) in enumerate(cells):
                x = 8 + k * (cw + gap)
                dr.rectangle((x, y, x + cw - 1, y + ch - 1), fill=CELL_BG)
                if im is not None:
                    zz = zoom * 2 if title == "half size" else zoom  # the half-size head is shown at twice the zoom, so it fills the cell
                    big = im.resize((im.width * zz, im.height * zz), Image.NEAREST)
                    img.paste(big, (x + (cw - big.width) // 2, y + (ch - big.height) // 2))
                dr.text((x + 2, y + 1), face if title == "front" else title + (" x2" if title == "half size" else ""), fill=(150, 140, 180))
            y += ch + 14
        y += 8
    for aid, keys in act_blocks:
        dr.text((8, y), f"{aid} acts", fill=(255, 255, 160))
        y += 14
        for fc in (0, 1):
            for line0 in range(0, len(keys), per_line):
                for k, key in enumerate(keys[line0:line0 + per_line]):
                    item = frames_img.get((aid, key, fc))
                    x = 8 + k * (acw + 6) * az
                    dr.rectangle((x, y, x + (acw + 4) * az - 1, y + (ach_up + ach_dn + 4) * az), fill=CELL_BG)
                    if item:
                        im, piv = item
                        big = im.resize((im.width * az, im.height * az), Image.NEAREST)
                        img.paste(big, (x + ((acw + 4 - im.width) // 2) * az, y + (ach_up - int(piv[1]) + 2) * az), big)
                    dr.text((x + 2, y + 1), key + ("" if fc == 0 else " 3/4"), fill=(150, 140, 180))
                y += cell_h
        y += 8
    img = img.crop((0, 0, W, min(H, y + 6)))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{chapter}_{tag}.jpg")
    img.save(path, quality=90)
    print(path, img.size)
    return path


def main(argv):
    out = os.path.join(ROOT, "docs", "shots", "faces")
    zoom = 8
    args = []
    i = 1
    while i < len(argv):
        if argv[i] == "--out":
            out = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--zoom":
            zoom = int(argv[i + 1])
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if not args:
        print(__doc__)
        return 2
    tag, chs = args[0], args[1:]
    for c in chs or CHAPTERS:
        if os.path.exists(os.path.join(ROOT, "assets", "story", c, "people", "people.json")):
            if tag == "acting":  # the fourteen faces and the directed acts: docs/shots/faces/<chapter>_acting.jpg
                acting_sheet(c, out, zoom if "--zoom" in argv else 5)
            else:
                sheet(c, tag, out, zoom)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
