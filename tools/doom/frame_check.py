#!/usr/bin/env python3
"""Exposure of the Doom scene shots against the A1 night-interior rules (tools/art/frame_check.py, docs/art/STYLE_GUIDE.md section 2).

    python -I tools/doom/frame_check.py <dir with the *_16x9.jpg shots>      (run it before tools/shrink_shots.py: it wants full-size frames)

Prints the frame_check row (p5, p50, p95, saturation, crushed, blown) per shot and for all of them together, and the pilot's own targets: p50 0.25 to 0.38, p95 - p5 over 0.4.
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "art"))
import frame_check as fc  # noqa: E402


def main(d):
    files = sorted(glob.glob(os.path.join(d, "*_16x9.jpg")))
    files = [f for f in files if not os.path.basename(f).startswith("contact")]
    print("%-22s %5s %5s %5s  %4s  %6s %6s  %s" % ("shot", "p5", "p50", "p95", "sat", "crush", "blown", "target"))
    for f in files:
        r = fc.measure([f])
        ok = 0.25 <= r["p50"] <= 0.38 and r["p95"] - r["p5"] > 0.4
        print("%-22s %5.2f %5.2f %5.2f  %4.2f  %5.1f%% %5.1f%%  %s" % (os.path.basename(f)[:-9], r["p5"], r["p50"], r["p95"], r["sat"], 100 * r["crush"], 100 * r["blown"], "ok" if ok else "off"))
    r = fc.measure(files)
    print("%-22s %5.2f %5.2f %5.2f  %4.2f  %5.1f%% %5.1f%%  contrast p95-p5 %.2f" % ("ALL", r["p5"], r["p50"], r["p95"], r["sat"], 100 * r["crush"], 100 * r["blown"], r["p95"] - r["p5"]))


if __name__ == "__main__":
    main(sys.argv[1])
