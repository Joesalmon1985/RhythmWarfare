"""Writes the hand-authored `staging` blocks of tools/run/staging_data.py into the shipped hotspot files (docs/CHOICE_CLARITY.md). Idempotent; a block removed from the table is
removed from the file. Files: content/run/hotspots/*.json, content/paths/*/hotspots/*.json, content/trial/hotspots.json.

It also writes every hotspot's `show` block (package A7, lead ruling 35b; docs/art/CHOICE_STATES.md): how the choice shows its state with its own artwork. Nothing is
hand-authored: the block names the show archetype its row gets by default (show_of: a quest entrance with a herald is a door, its gate and pool; a door is a door; a person or
a billboard figure a figure; anything else an object), and src/run/choice_show.gd fills in the archetype's frames, lights and sounds from content/run/choice_show.json. A path's
return object gets the Warehouse's own door (returns_common.show_of). src/run/choice_show.gd `default_archetype` decides the same; tests/test_choice_states.gd compares them.

    python tools/run/apply_staging.py          write
    python tools/run/apply_staging.py --check  exit 1 if a file is not up to date (tools/content tests call this)
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import staging_data  # noqa: E402
import returns_common  # noqa: E402  (the staging of a path's return object, N2.5)


def files() -> list:
    return sorted(glob.glob(os.path.join(ROOT, "content", "run", "hotspots", "*.json")) + glob.glob(os.path.join(ROOT, "content", "paths", "*", "hotspots", "*.json"))
                  + [os.path.join(ROOT, "content", "trial", "hotspots.json")])


def staging_archetype(h: dict) -> str:
    """ChoiceStaging.archetype_of (src/run/choice_staging.gd) in Python."""
    st = h.get("staging")
    if isinstance(st, dict) and "archetype" in st:
        return st["archetype"]
    if isinstance(st, dict) and st.get("actor", ""):
        return "person"
    ac = h.get("acting")
    if isinstance(ac, dict) and ac and ac.get("actor", ""):
        return "person"
    if "actor" in h.get("anchor", {}):
        return "person"
    return {"exit": "door", "feature": "feature", "encounter": "feature"}.get(h.get("kind", ""), "object")


def show_of(h: dict) -> dict:
    """The `show` block a row gets by default (ChoiceShow.default_archetype)."""
    own = returns_common.show_of(h["id"])
    if own is not None:
        return own
    hb = h.get("herald")
    if isinstance(hb, dict) and "self" not in hb:
        return {"archetype": "door"}
    a = staging_archetype(h)
    return {"archetype": {"door": "door", "person": "figure", "figure": "figure", "none": "none"}.get(a, "object")}


def main(argv: list) -> int:
    check = "--check" in argv
    seen = set()
    stale = []
    for fn in files():
        with open(fn, encoding="utf-8") as fh:
            text = fh.read()
        doc = json.loads(text)
        changed = False
        for h in doc.get("hotspots", []):
            want = staging_data.STAGING.get(h["id"])
            if want is None:
                want = returns_common.staging_of(h["id"])
            if want is not None:
                seen.add(h["id"])
            if want is None and "staging" in h:
                del h["staging"]
                changed = True
            elif want is not None and h.get("staging") != want:
                h["staging"] = json.loads(json.dumps(want))
                changed = True
            show = show_of(h)
            if h.get("show") != show:
                h["show"] = show
                changed = True
        if changed:
            stale.append(os.path.relpath(fn, ROOT))
            if not check:
                with open(fn, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    missing = sorted(set(staging_data.STAGING) - seen)
    if missing:
        print("staging_data names hotspots that do not exist: " + ", ".join(missing))
        return 1
    if check and stale:
        print("not up to date: " + ", ".join(stale))
        return 1
    print("%d staging blocks; %s" % (len(staging_data.STAGING), ("wrote " + ", ".join(stale)) if stale and not check else "up to date"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
