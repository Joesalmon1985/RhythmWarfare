"""Top-down plan PNG of a converted map: pieces shaded by floor height, walls light, portals orange, portals with a step or drop over 0.6 m red.

  python tools/doom/render_plan.py content/story/maps/doom_warehouse.json docs/shots/doom/plan_warehouse.png [--size 900]
  python tools/doom/render_plan.py --all
Pure standard library (zlib PNG writer). North (Doom +y, StoryMap -z) is up, as in the ian-albert renders.
"""
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAX_BYTES = 300 * 1024


def write_png(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(t, data):
        c = struct.pack(">I", len(data)) + t + data
        return c + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


class Canvas:
    def __init__(self, w, h, bg=(14, 16, 22)):
        self.w, self.h = w, h
        self.rows = [bytearray(bg * w) for _ in range(h)]

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = 3 * x
            self.rows[y][i:i + 3] = bytes(c)

    def fill_convex(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(self.h - 1, int(max(ys))) + 1):
            yc = y + 0.5
            xs = []
            n = len(pts)
            for i in range(n):
                a, b = pts[i], pts[(i + 1) % n]
                if (a[1] <= yc < b[1]) or (b[1] <= yc < a[1]):
                    xs.append(a[0] + (yc - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
            if len(xs) >= 2:
                x0, x1 = int(min(xs)), int(max(xs))
                row = self.rows[y]
                for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                    row[3 * x:3 * x + 3] = bytes(c)

    def line(self, a, b, c, thick=1):
        x0, y0, x1, y1 = int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            for ox in range(thick):
                for oy in range(thick):
                    self.px(x0 + ox, y0 + oy, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy


GLYPHS = {  # 5 x 7 pixel capitals for the APPROXIMATE stamp
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"], "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"], "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"], "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"], "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"]}


def stamp(cv, text, x, y, c, k=3):
    for ch in text:
        for r, row in enumerate(GLYPHS[ch]):
            for q, bit in enumerate(row):
                if bit == "1":
                    for dx in range(k):
                        for dy in range(k):
                            cv.px(x + q * k + dx, y + r * k + dy, c)
        x += 6 * k


def render(d, size=900):
    secs = d["sectors"]
    pts = [tuple(p) for s in secs for p in s["polygon"]]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    z0, z1 = min(p[1] for p in pts), max(p[1] for p in pts)
    margin = 12
    sc = (size - 2 * margin) / max(x1 - x0, z1 - z0, 1e-6)
    W, H = int((x1 - x0) * sc) + 2 * margin, int((z1 - z0) * sc) + 2 * margin

    def tp(p):
        return (margin + (p[0] - x0) * sc, margin + (p[1] - z0) * sc)  # z grows down the image: Doom north is up
    cv = Canvas(W, H)
    fl = [float(s["floor"]) for s in secs]
    lo, hi = min(fl), max(fl)
    by_id = {s["id"]: s for s in secs}
    for s in secs:
        t = (float(s["floor"]) - lo) / (hi - lo) if hi > lo else 0.5
        c = (int(36 + 70 * t), int(52 + 120 * t), int(86 + 130 * t))
        cv.fill_convex([tp(p) for p in s["polygon"]], c)
    portal_keys = {}
    for w in d.get("walls", []):
        if w.get("portal"):
            a, b = tuple(w["from"]), tuple(w["to"])
            portal_keys[(a, b) if a <= b else (b, a)] = abs(float(by_id[w["sector"]]["floor"]) - float(by_id[w["portal"]]["floor"])) > 0.6
    for s in secs:
        p = [tuple(q) for q in s["polygon"]]
        for i in range(len(p)):
            a, b = p[i], p[(i + 1) % len(p)]
            k = (a, b) if a <= b else (b, a)
            if k in portal_keys:
                cv.line(tp(a), tp(b), (230, 60, 50) if portal_keys[k] else (255, 170, 40))
            else:
                cv.line(tp(a), tp(b), (235, 235, 235), 2 if sc > 3 else 1)
    if d.get("doom", {}).get("approximate"):
        stamp(cv, "APPROXIMATE", 6, 6, (255, 60, 60))
    wp = {w["id"]: w for w in d.get("waypoints", [])}.get(d.get("start"))
    if wp:
        q = tp(wp["at"])
        cv.line((q[0] - 5, q[1]), (q[0] + 5, q[1]), (80, 255, 120))
        cv.line((q[0], q[1] - 5), (q[0], q[1] + 5), (80, 255, 120))
    return W, H, cv.rows


def render_file(src, dst, size=900):
    with open(src, encoding="utf-8") as f:
        d = json.load(f)
    while True:
        W, H, rows = render(d, size)
        n = write_png(dst, W, H, rows)
        if n <= MAX_BYTES or size <= 300:
            break
        size = int(size * 0.8)
    return W, H, n


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    size = 900
    if "--size" in argv:
        i = argv.index("--size")
        size = int(argv[i + 1])
        del argv[i:i + 2]
    jobs = []
    if "--all" in argv:
        with open(os.path.join(HERE, "scenes.json"), encoding="utf-8") as f:
            for e in json.load(f).values():
                jobs.append((os.path.join(ROOT, e["output"]), os.path.join(ROOT, e["plan"])))
    elif len(argv) == 2:
        jobs.append((argv[0], argv[1]))
    else:
        print(__doc__)
        return 2
    for src, dst in jobs:
        if not os.path.exists(src):
            print("%s: MISSING (convert first)" % src)
            continue
        W, H, n = render_file(src, dst, size)
        print("%s -> %s (%dx%d, %d bytes)" % (os.path.basename(src), dst, W, H, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
