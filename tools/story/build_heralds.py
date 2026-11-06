#!/usr/bin/env python3
"""Bakes the heralds of the quest entrances (tools/story/art/heralds.py, docs/art/HERALDS.md) into assets/story/heralds/, and the gesture strips into docs/shots/art/heralds/.

    python tools/story/build_heralds.py            # the sheet, the frame table, the wizard's billboard frames and the strips
    python tools/story/build_heralds.py --no-strips

Then `godot --headless --path . --import` (new textures). Deterministic: the same inputs give the same bytes.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from art import heralds, lib  # noqa: E402

if __name__ == "__main__":
    heralds.build()
    if "--no-strips" not in sys.argv:
        for p in heralds.strips(os.path.join(lib.ROOT, "docs", "shots", "art", "heralds")):
            print("strip", os.path.relpath(p, lib.ROOT))
