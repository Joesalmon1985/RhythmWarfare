"""Writes the hand-authored `staging` blocks of tools/run/staging_data.py into the shipped hotspot files (docs/CHOICE_CLARITY.md). Idempotent; a block removed from the table is
removed from the file. Files: content/run/hotspots/*.json, content/paths/*/hotspots/*.json, content/trial/hotspots.json.

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


def files() -> list:
    return sorted(glob.glob(os.path.join(ROOT, "content", "run", "hotspots", "*.json")) + glob.glob(os.path.join(ROOT, "content", "paths", "*", "hotspots", "*.json"))
                  + [os.path.join(ROOT, "content", "trial", "hotspots.json")])


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
            if want is not None:
                seen.add(h["id"])
            if want is None and "staging" in h:
                del h["staging"]
                changed = True
            elif want is not None and h.get("staging") != want:
                h["staging"] = json.loads(json.dumps(want))
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
