#!/usr/bin/env python3
"""Visual polish 2 (docs/HANDOVER.md A13): the faces of the four species whose heads are too small for the full-size rules must differ at the half size by a pixel
threshold, and `kneel`, `cover_face` and `collapse` must read as what they are (a one-knee-down figure; the hands over the face).

    python3 -m unittest discover -s tools/content -p "test_faces_lod2.py"

The faces are rendered with the real people rig (tools/story/art/people.py) from the actors of the shipped chapters; nothing is baked or written.
"""
from __future__ import annotations

import json
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "story"))

from art import half_faces, people, wardrobe  # noqa: E402

POSES = json.load(open(os.path.join(ROOT, "assets", "story", "people_poses.json"), encoding="utf-8"))
KEYS = POSES["keys"]
# the four species with picture faces: (chapter, actor)
ACTORS = {"grey": ("mothership", "g08"), "cyclops": ("mothership", "c06"), "insect": ("mothership", "gallery_c05"), "skeleton": ("underworld", "court_c05")}
_SPECS: dict = {}


def spec_of(chapter: str, aid: str) -> dict:
    if chapter not in _SPECS:
        data = json.load(open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8"))
        _SPECS[chapter] = wardrobe.cast_chapter(chapter, data["actors"])
    return _SPECS[chapter][aid]


def pose_of(state: str) -> dict:
    cyc = POSES["states"][state]["frames"]
    return dict(zip(KEYS, cyc[len(cyc) // 2]))


def coloured(spec: dict, face: str, lod: int, fc: int, state: str = "stare") -> np.ndarray:
    """The whole frame as RGB (the indexed pixels through the actor's own palette row), padded to one size so frames compare."""
    img, _piv, _hand = people.render_frame(spec, pose_of(state), state, fc, lod, "", face, int(spec.get("seed", 0)))
    row = np.array(people.palette_row(spec["colours"]), np.uint8)
    out = np.zeros((72, 72, 3), np.int16)
    on = img > 0
    h, w = min(img.shape[0], 72), min(img.shape[1], 72)
    rgb = np.zeros(img.shape + (3,), np.int16)
    rgb[on] = row[img[on] & 127][:, :3]
    out[:h, :w] = rgb[:h, :w]
    return out


def diff(a: np.ndarray, b: np.ndarray) -> int:
    return int((np.abs(a - b).sum(-1) > 24).sum())


class FacesAtHalfSize(unittest.TestCase):
    def pairs(self, species, lod, fc, faces, floor):
        chapter, aid = ACTORS[species]
        spec = spec_of(chapter, aid)
        ims = {f: coloured(spec, f, lod, fc) for f in faces}
        bad = []
        for i, a in enumerate(faces):
            for b in faces[i + 1:]:
                n = diff(ims[a], ims[b])
                if n < floor:
                    bad.append(f"{a}/{b}={n}")
        self.assertEqual(bad, [], f"{species} lod {lod} facing {fc}: faces that differ by fewer than {floor} pixels")

    def test_every_face_is_distinct_at_half_size_front(self):
        for sp in ACTORS:
            self.pairs(sp, 2, 0, list(people.FACES), half_faces.MIN_DIFF)

    def test_every_face_is_distinct_at_half_size_three_quarter(self):
        for sp in ACTORS:
            self.pairs(sp, 2, 1, list(people.FACES), 3)

    def test_the_acted_faces_are_distinct_at_full_size(self):
        for sp in ACTORS:
            self.pairs(sp, 1, 0, list(people.ACT_FACES), 3)

    def test_the_pairs_the_owner_listed(self):
        """relief / grief / laugh on greys and skeletons, anger / doubt / shame on the cyclops, the insect's mandibles: each pair differs in many pixels."""
        for sp, faces in (("grey", ("relief", "grief", "laugh")), ("skeleton", ("relief", "grief", "laugh")), ("cyclops", ("anger", "doubt", "shame")), ("insect", ("anger", "doubt", "shame", "fear", "laugh"))):
            self.pairs(sp, 2, 0, list(faces), 6)
            self.pairs(sp, 1, 0, list(faces), 6)

    def test_every_picture_is_well_formed(self):
        for pics in list(half_faces.PICTURES.values()) + list(half_faces.PICTURES_L.values()):
            for mood, pic in pics.items():
                self.assertIn(mood, people.FACES)
                widths = {len(r) for r in pic.values()}
                self.assertEqual(len(widths), 1, mood)
                self.assertEqual(next(iter(widths)) % 2, 1, f"{mood}: pictures are centred on a column, so odd")
                for r in pic.values():
                    for ch in r:
                        self.assertTrue(ch == "." or ch in half_faces.LEGEND, ch)
        for sp, pics in half_faces.PICTURES.items():
            self.assertEqual(set(pics), set(people.FACES), sp)


class Acts(unittest.TestCase):
    def body(self, state, fc, actor=("underworld", "pit_c09")):
        spec = spec_of(*actor)
        S = people.H0 * float(spec.get("height", 1.0))
        return people.Body(spec, pose_of(state), S, fc, state), S

    def test_kneel_is_one_knee_down(self):
        for fc in (0, 1, 2):
            b, S = self.body("kneel", fc)
            self.assertTrue(b.kneeling)
            knees = sorted(b.legs[s]["knee"][1] for s in "lr")
            floor = -0.02 * S
            self.assertAlmostEqual(knees[1], floor, delta=0.01 * S, msg=f"facing {fc}: one knee on the floor")
            self.assertLess(knees[0], floor - 0.12 * S, f"facing {fc}: the other knee up")
            self.assertLess(b.hip[1], -0.2 * S, "the hip is a thigh above the floor, not at the standing height")
            self.assertGreater(b.hip[1], -0.3 * S)

    def test_hands_reach_the_face(self):
        for state in ("cover_face", "collapse"):
            for fc in (0, 1):
                b, S = self.body(state, fc)
                self.assertTrue(b.covering)
                for side in "lr":
                    hx, hy = b.arms[side]["hand"]
                    self.assertLess(abs(hx - b.head_c[0]), b.head_w * 0.8, f"{state} {fc} {side}: the hand is beside the head, not over the face")
                    self.assertLess(abs(hy - b.head_c[1]), b.head_h * 0.35, f"{state} {fc} {side}")
            b, S = self.body(state, 2)
            self.assertFalse(b.covering, "the back view has no face to cover")

    def test_cover_face_hides_the_face(self):
        """Seen from the front, two different faces of a person covering theirs are (almost) the same picture: the face is behind the hands."""
        spec = spec_of("underworld", "pit_c09")
        a = coloured(spec, "grief", 1, 0, "cover_face")
        b = coloured(spec, "laugh", 1, 0, "cover_face")
        c = coloured(spec, "grief", 1, 0, "stare")
        d = coloured(spec, "laugh", 1, 0, "stare")
        self.assertLessEqual(diff(a, b), max(4, diff(c, d) // 3))


if __name__ == "__main__":
    unittest.main()
