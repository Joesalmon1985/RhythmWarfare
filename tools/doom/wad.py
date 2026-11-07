"""Doom WAD reader (Doom/Doom II format only, not Hexen). Standard library only.

Reads the header, the directory and the map lumps of a level: THINGS, LINEDEFS, SIDEDEFS, VERTEXES, SECTORS.
The WAD is an input outside Git: path from the environment variable RW_DOOM_WAD (default DEFAULT_WAD).

Everything returned here is in raw Doom units (integers, y up). Scale and axis conventions are applied in convert.py
(see docs/doom/CONVERSION.md).

Usage:  python tools/doom/wad.py            (lump report: maps present and which have the four geometry lumps)
"""
import os
import struct
import sys

DEFAULT_WAD = r"C:\Users\joesa\rw-audio-work\doom\doom2.wad"
MAP_LUMPS = ["THINGS", "LINEDEFS", "SIDEDEFS", "VERTEXES", "SEGS", "SSECTORS", "NODES", "SECTORS", "REJECT", "BLOCKMAP"]
GEOMETRY = ["VERTEXES", "LINEDEFS", "SIDEDEFS", "SECTORS"]
TWO_SIDED = 0x0004
IMPASSABLE = 0x0001


def wad_path():
    return os.environ.get("RW_DOOM_WAD") or DEFAULT_WAD


def _name(b):
    return b.split(b"\0", 1)[0].decode("ascii", "replace").upper()


class Wad:
    def __init__(self, data):
        if len(data) < 12:
            raise ValueError("not a WAD (too short)")
        self.data = data
        self.ident = data[:4].decode("ascii", "replace")
        if self.ident not in ("IWAD", "PWAD"):
            raise ValueError("not a WAD: header %r" % self.ident)
        n, off = struct.unpack_from("<ii", data, 4)
        if n < 0 or off < 0 or off + 16 * n > len(data):
            raise ValueError("WAD directory runs past the end of the file")
        self.lumps = []  # (name, offset, size) in directory order
        for i in range(n):
            pos, size, nm = struct.unpack_from("<ii8s", data, off + 16 * i)
            if pos < 0 or size < 0 or pos + size > len(data):
                raise ValueError("lump %d runs past the end of the file" % i)
            self.lumps.append((_name(nm), pos, size))

    @classmethod
    def open(cls, path=None):
        with open(path or wad_path(), "rb") as f:
            return cls(f.read())

    def lump_data(self, index):
        _, pos, size = self.lumps[index]
        return self.data[pos:pos + size]

    def map_names(self):
        """Names of all maps (MAPxx or ExMy markers): a marker is followed by a THINGS lump."""
        out = []
        for i, (nm, _, _) in enumerate(self.lumps[:-1]):
            if self.lumps[i + 1][0] == "THINGS" and (_is_map_name(nm)):
                out.append(nm)
        return out

    def map_lumps(self, name):
        """{lump name: raw bytes} of the map named `name` (the lumps that follow its marker, up to the next non-map lump)."""
        name = name.upper()
        for i, (nm, _, _) in enumerate(self.lumps):
            if nm == name and i + 1 < len(self.lumps) and self.lumps[i + 1][0] == "THINGS":
                out = {}
                for j in range(i + 1, min(i + 1 + len(MAP_LUMPS), len(self.lumps))):
                    ln = self.lumps[j][0]
                    if ln not in MAP_LUMPS:
                        break
                    out[ln] = self.lump_data(j)
                return out
        raise KeyError("map %s not found" % name)

    def read_map(self, name):
        """A DoomMap with vertices [(x, y)], linedefs, sidedefs, sectors, things (all raw Doom units)."""
        L = self.map_lumps(name)
        missing = [g for g in GEOMETRY if g not in L or len(L[g]) == 0]
        if missing:
            raise ValueError("map %s lacks %s" % (name, ", ".join(missing)))
        return parse_map(name, L)


def _is_map_name(nm):
    if len(nm) == 5 and nm.startswith("MAP") and nm[3:].isdigit():
        return True
    return len(nm) == 4 and nm[0] == "E" and nm[1].isdigit() and nm[2] == "M" and nm[3].isdigit()


class DoomMap:
    def __init__(self, name):
        self.name = name
        self.vertices = []   # (x, y)
        self.linedefs = []   # dict v1, v2, flags, special, tag, right, left (side index or -1)
        self.sidedefs = []   # dict xoff, yoff, upper, lower, middle, sector
        self.sectors = []    # dict floor, ceiling, floor_tex, ceil_tex, light, special, tag
        self.things = []     # dict x, y, angle, type, flags


def parse_map(name, L):
    m = DoomMap(name)
    v = L["VERTEXES"]
    for i in range(len(v) // 4):
        m.vertices.append(struct.unpack_from("<hh", v, 4 * i))
    d = L["LINEDEFS"]
    for i in range(len(d) // 14):
        v1, v2, fl, sp, tag, r, l = struct.unpack_from("<hhhhhhh", d, 14 * i)
        m.linedefs.append({"v1": v1, "v2": v2, "flags": fl, "special": sp, "tag": tag,
                           "right": r if r != -1 else -1, "left": l if l != -1 else -1})
    s = L["SIDEDEFS"]
    for i in range(len(s) // 30):
        xo, yo, up, lo, mi, sec = struct.unpack_from("<hh8s8s8sh", s, 30 * i)
        m.sidedefs.append({"xoff": xo, "yoff": yo, "upper": _name(up), "lower": _name(lo), "middle": _name(mi), "sector": sec})
    c = L["SECTORS"]
    for i in range(len(c) // 26):
        fh, ch, ft, ct, li, sp, tag = struct.unpack_from("<hh8s8shhh", c, 26 * i)
        m.sectors.append({"floor": fh, "ceiling": ch, "floor_tex": _name(ft), "ceil_tex": _name(ct), "light": li, "special": sp, "tag": tag})
    t = L.get("THINGS", b"")
    for i in range(len(t) // 10):
        x, y, a, ty, fl = struct.unpack_from("<hhhhh", t, 10 * i)
        m.things.append({"x": x, "y": y, "angle": a, "type": ty, "flags": fl})
    for ld in m.linedefs:  # sanity: indices in range
        for k in ("v1", "v2"):
            if not 0 <= ld[k] < len(m.vertices):
                raise ValueError("%s: linedef vertex %d out of range" % (name, ld[k]))
        for k in ("right", "left"):
            if ld[k] != -1 and not 0 <= ld[k] < len(m.sidedefs):
                raise ValueError("%s: linedef side %d out of range" % (name, ld[k]))
    for sd in m.sidedefs:
        if not 0 <= sd["sector"] < len(m.sectors):
            raise ValueError("%s: sidedef sector %d out of range" % (name, sd["sector"]))
    return m


def report(path=None):
    w = Wad.open(path)
    lines = ["%s, %d lumps, %d bytes" % (w.ident, len(w.lumps), len(w.data))]
    maps = w.map_names()
    lines.append("maps present (%d): %s" % (len(maps), " ".join(maps)))
    for n in ["MAP02", "MAP04", "MAP07", "MAP08", "MAP11", "MAP13", "MAP15", "MAP29"]:
        if n not in maps:
            lines.append("%s: MISSING" % n)
            continue
        L = w.map_lumps(n)
        have = ["%s=%dB" % (g, len(L.get(g, b""))) for g in GEOMETRY]
        try:
            m = parse_map(n, L)
            lines.append("%s: %s | %d vertices, %d linedefs, %d sidedefs, %d sectors, %d things" % (
                n, " ".join(have), len(m.vertices), len(m.linedefs), len(m.sidedefs), len(m.sectors), len(m.things)))
        except Exception as e:  # noqa: BLE001
            lines.append("%s: %s | PROBLEM %s" % (n, " ".join(have), e))
    return "\n".join(lines)


if __name__ == "__main__":
    print(report(sys.argv[1] if len(sys.argv) > 1 else None))
