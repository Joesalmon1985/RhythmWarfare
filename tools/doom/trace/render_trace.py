"""Hand traces read off the ian-albert renders (C:\\Users\\joesa\\rw-audio-work\\doom\\renders\\MAPxx.jpg), written as tools/doom/trace/<scene>.json.

The renders are top-down, rotated 45 degrees (north is the upper right, east the lower right) and drawn at about 1 render pixel = 1 Doom unit.
Every polygon below is in pixels of a thumbnail (the render shrunk so its longer side is 1500 px, `THUMB` below), as read by eye from the image;
`Scene.xf` rotates it into Doom units: u (east) = (dx + dy) / sqrt 2 * s, v (north) = (dx - dy) / sqrt 2 * s, with s = render px per thumbnail px.
Heights are NOT in the renders (floors are textured, not coloured by height): only wall faces show that a level changes. Heights below are guesses
from what is raised or sunk in the picture; each scene lists what was and was not readable.

python -I tools/doom/trace/make_traces.py    writes the traces; python -I tools/doom/trace/render_trace.py --overlay draws polygons over the render
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_traces as mt  # noqa: E402

RENDERS = os.environ.get("RW_DOOM_RENDERS", r"C:\Users\joesa\rw-audio-work\doom\renders")
R2 = math.sqrt(0.5)


def D(cx, cy, h):
    return [(cx - h, cy), (cx, cy + h), (cx + h, cy), (cx, cy - h)]


def rr(cx, cy, a, b):
    """Rectangle rotated 45 degrees: half length a along the down-right axis, half width b."""
    pts = []
    for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        pts.append((round(cx + sa * a * R2 + sb * b * R2), round(cy + sa * a * R2 - sb * b * R2)))
    return pts


def oct8(cx, cy, apo):
    h = round(apo * 0.4142)
    return [(cx + apo, cy - h), (cx + apo, cy + h), (cx + h, cy + apo), (cx - h, cy + apo), (cx - apo, cy + h), (cx - apo, cy - h), (cx - h, cy - apo), (cx + h, cy - apo)]


def seg_closest(p, q, r, t):
    """Closest points between segments pq and rt by sampling (good enough to find a door position)."""
    best = (1e18, None, None)
    for i in range(41):
        a = (p[0] + (q[0] - p[0]) * i / 40.0, p[1] + (q[1] - p[1]) * i / 40.0)
        for j in range(41):
            b = (r[0] + (t[0] - r[0]) * j / 40.0, r[1] + (t[1] - r[1]) * j / 40.0)
            d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if d < best[0]:
                best = (d, i / 40.0, j / 40.0)
    return best


class Scene:
    def __init__(self, name, title, s, origin, image):
        self.name, self.title, self.s, self.origin, self.image = name, title, s, origin, image
        self.secs = {}
        self.order = []
        self.start = None
        self.uncertain = []

    def xf(self, v):
        dx, dy = v[0] - self.origin[0], v[1] - self.origin[1]
        return (round((dx + dy) * R2 * self.s), round((dx - dy) * R2 * self.s))

    def add(self, sid, ring, floor, ceil, light, holes=(), ftex="FLOOR4_8", ctex="CEIL3_5"):
        ring = [tuple(p) for p in ring]
        if mt.area2(ring) > 0:  # clockwise on the y-down image = counter-clockwise in Doom units
            ring.reverse()
        self.secs[sid] = {"id": sid, "ring": ring, "holes": list(holes), "floor": floor, "ceiling": ceil, "light": light, "floor_tex": ftex, "ceil_tex": ctex}
        self.order.append(sid)
        return ring

    def link(self, sid, a, b, width, floor, ceil, light, ftex="FLOOR4_8", ctex="CEIL3_5"):
        """A door / corridor sector joining the nearest edges of sectors a and b (both gain the door's two vertices)."""
        ra, rb = self.secs[a]["ring"], self.secs[b]["ring"]
        best = (1e18,)
        for i in range(len(ra)):
            for j in range(len(rb)):
                d, ta, tb = seg_closest(ra[i], ra[(i + 1) % len(ra)], rb[j], rb[(j + 1) % len(rb)])
                if d < best[0]:
                    best = (d, i, ta, j, tb)
        _, i, ta, j, tb = best

        def door(ring, i, t):
            p, q = ring[i], ring[(i + 1) % len(ring)]
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            w = min(width, 0.7 * L)
            c = t * L
            c = min(max(c, w / 2 + 1), L - w / 2 - 1)
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            d1 = (round(p[0] + ux * (c - w / 2)), round(p[1] + uy * (c - w / 2)))
            d2 = (round(p[0] + ux * (c + w / 2)), round(p[1] + uy * (c + w / 2)))
            return d1, d2
        a1, a2 = door(ra, i, ta)
        b1, b2 = door(rb, j, tb)
        ring = [a2, a1, b2, b1]
        if mt.area2(ring) >= 0 or len({a1, a2, b1, b2}) < 4:
            print("  link %s (%s - %s) skipped: degenerate" % (sid, a, b))
            return
        ra[i + 1:i + 1] = [a1, a2]
        rb[j + 1:j + 1] = [b1, b2]
        self.secs[sid] = {"id": sid, "ring": ring, "holes": [], "floor": floor, "ceiling": ceil, "light": light, "floor_tex": ftex, "ceil_tex": ctex}
        self.order.append(sid)

    def build(self):
        S = []
        for sid in self.order:
            s = self.secs[sid]
            rings = [s["ring"]] + [self.secs[h]["ring"] for h in s["holes"]]
            S.append(mt.sector(sid, rings, s["floor"], s["ceiling"], s["light"], s["floor_tex"], s["ceil_tex"]))
        sx, sy, face = self.start
        x, y = self.xf((sx, sy))
        fx, fy = face
        ang = round(math.degrees(math.atan2((fx - fy) * R2, (fx + fy) * R2)))
        things = [{"x": x, "y": y, "angle": ang % 360, "type": 1, "flags": 7}]
        return mt.build(self.name, self.title, S, self.uncertain, things, xf=self.xf)


SKY = "F_SKY1"


def map07():
    sc = Scene("MAP07", "Dead Simple (traced from the render)", 2.087, (700, 760), "MAP07.jpg")
    c = (700, 760)
    outer, stone, court = D(*c, 700), D(*c, 515), D(*c, 350)
    plats = {"plat_n": (740, 600), "plat_e": (910, 775), "plat_w": (520, 810), "plat_s": (690, 980)}
    slots = {"pit_n1": (805, 480), "pit_n2": (1020, 690), "pit_s1": (405, 885), "pit_s2": (630, 1090)}
    for k, p in plats.items():
        sc.add(k, D(*p, 70), 80, 320, 230, ftex="FLOOR0_1")
    sc.add("pedestal", D(730, 775, 55), 64, 320, 255, ftex="FLOOR0_1")
    for k, p in slots.items():
        sc.add(k, rr(*p, 55, 17), -96, 320, 60, ftex="NUKAGE1")
    sc.add("courtyard", court, 32, 320, 200, holes=list(plats) + ["pedestal"], ftex="GRASS1", ctex=SKY)
    sc.add("stone_ring", stone, 0, 320, 170, holes=["courtyard"] + list(slots), ftex="FLOOR0_1", ctex=SKY)
    sc.add("terrace", outer, 96, 512, 190, holes=["stone_ring"], ftex="GRASS1", ctex=SKY)
    sc.add("nub", [(575, 185), (640, 120), (560, 40), (495, 105)], 96, 512, 150, ftex="GRASS1", ctex=SKY)
    sc.start = (905, 1005, (-1, 0))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP07.jpg (rotated 45 degrees, north upper right), at an assumed 1 render px = 1 Doom unit: the arena is about 2100 units across (outer grass terrace 2100, grey stone ring 1550, inner grass courtyard 1030).",
        "Read from the render: a square outer grass terrace, a grey stone ring inside it, an inner grass courtyard with four square grey platforms (about 210 units, one per quadrant) and a small central pedestal, four dark slots in the stone ring, a small room nub off the terrace's north-west side, ramps along the terrace and courtyard edges.",
        "NOT readable: floor and ceiling heights (the render is textured; only wall faces show that levels differ, the terrace and courtyard edges clearly stand above the ring). Heights here are guesses: ring 0, courtyard +32, platforms +80, pedestal +64, terrace +96, slots -96.",
        "NOT traced: the ramps and stairs up to the terrace and platforms (they are drawn as brown wedges along the walls; here the levels meet in steps and ledges), the small lift squares at the courtyard corners, exact slot sizes and positions (4 slots read from the picture), the player start (placed at the green marker).",
        "Exact sizes are readings by eye on a 1500 px thumbnail of the render; a few percent of error is likely."]
    return sc


def map11():
    sc = Scene("MAP11", "Circle of Death (traced from the render)", 2.33, (470, 780), "MAP11.jpg")
    ring_o = [(160, 740), (290, 520), (430, 462), (580, 520), (755, 700), (770, 790), (650, 960), (480, 1050), (340, 990), (190, 860)]
    ring_i = [(290, 760), (350, 610), (470, 575), (560, 610), (610, 700), (610, 830), (560, 900), (470, 930), (350, 890)]
    grass = [(35, 640), (150, 500), (230, 410), (400, 240), (520, 240), (640, 330), (700, 500), (760, 560), (940, 700), (945, 800), (780, 990), (690, 1030), (650, 1140), (540, 1250), (340, 1190), (320, 1120), (140, 1040), (30, 880)]
    sc.add("pedestal", [(415, 780), (470, 725), (525, 780), (470, 835)], 24, 320, 240, ftex="FLOOR0_1")
    sc.add("void_w", [(228, 690), (262, 662), (262, 790), (228, 805)], -160, 600, 20, ftex="NUKAGE1")
    sc.add("void_e", [(640, 705), (672, 680), (686, 810), (645, 835)], -160, 600, 20, ftex="NUKAGE1")
    sc.add("courtyard", ring_i, 0, 480, 170, holes=["pedestal"], ftex="GRASS1", ctex=SKY)
    sc.add("walkway", ring_o, 48, 480, 190, holes=["courtyard", "void_w", "void_e"], ftex="FLOOR0_1", ctex=SKY)
    sc.add("grass", grass, 0, 480, 140, holes=["walkway"], ftex="GRASS1", ctex=SKY)
    sc.add("round_hall", [(930, 560), (990, 480), (1090, 455), (1190, 500), (1285, 600), (1290, 760), (1210, 860), (1100, 920), (950, 860)], 96, 360, 110,
           ftex="FLOOR4_8")
    sc.add("se_hall", [(740, 1210), (970, 975), (1150, 1170), (1170, 1250), (990, 1415), (910, 1415)], 64, 300, 100, ftex="FLOOR5_1")
    sc.add("north_room", [(415, 120), (470, 20), (580, 30), (600, 130), (560, 210), (460, 225)], 96, 300, 130, ftex="FLOOR5_1")
    sc.link("link_round", "grass", "round_hall", 80, 48, 300, 130)
    sc.link("link_se", "grass", "se_hall", 80, 32, 300, 120)
    sc.link("link_north", "grass", "north_room", 80, 48, 300, 130)
    sc.start = (470, 1160, (0, -1))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP11.jpg (rotated 45 degrees, north upper right), at an assumed 1 render px = 1 Doom unit; about 2400 units across the central ring.",
        "Read from the render: a large grass basin with tall brown cliff faces on its north and east sides, a raised grey walkway ring (an irregular ten sided oval about 1400 units across) holding a grass courtyard with a central raised block, two black voids between the ring and the courtyard (west and east), a big round building to the east, a large brown hall to the south-east and a room to the north.",
        "NOT readable: heights (guessed: grass 0, walkway +48, courtyard 0, pedestal +24, voids -160, round hall +96, south-east hall +64, north room +96), the full outlines of the outer rooms (only the main masses are traced; the north corridors, the far east water rooms and the small west rooms are NOT traced), stairs and lifts, the true depth of the voids.",
        "The 'deep central chamber' of the brief is only partly visible: the black voids read as pits beside the ring, not a pit under the courtyard; the courtyard is a floor, not a void.",
        "Door and corridor links between the basin and the three outer rooms are inserted by the tracer at the nearest edges, not read from the render."]
    return sc


def map08():
    sc = Scene("MAP08", "Tricks and Traps (traced from the render)", 2.686, (440, 650), "MAP08.jpg")
    c = (440, 650)
    sc.add("pool", D(440, 650, 58), -24, 256, 90, ftex="FWATER1")
    sc.add("hub", oct8(*c, 95), 0, 256, 190, holes=["pool"], ftex="FLOOR4_8")
    sc.add("r_ne_brown", [(500, 560), (905, 40), (1020, 150), (710, 520), (570, 600)], 24, 256, 130, ftex="FLOOR5_1")
    sc.add("r_east", [(545, 625), (735, 565), (940, 610), (1020, 690), (1000, 860), (960, 985), (840, 985), (720, 1020), (705, 925), (590, 895)], 8, 256, 150, ftex="FLOOR4_8")
    sc.add("r_far_ne", [(975, 245), (1120, 232), (1360, 480), (1390, 590), (1335, 655), (1230, 590), (1115, 505), (1040, 420)], 16, 256, 140, ftex="FLOOR4_8")
    sc.add("cross_tower", [(1260, 280), (1330, 220), (1400, 130), (1480, 200), (1450, 250), (1380, 340), (1340, 360), (1290, 340)], 40, 256, 120, ftex="FLOOR4_8")
    sc.add("r_sw_grey", [(415, 775), (470, 770), (430, 860), (530, 940), (655, 1105), (520, 1255), (385, 1105), (250, 905), (305, 860)], 0, 256, 150, ftex="FLOOR4_8")
    sc.add("r_west_brown", [(65, 640), (105, 590), (210, 622), (310, 700), (385, 690), (385, 765), (300, 860), (210, 860), (180, 795)], 24, 256, 120, ftex="FLOOR5_1")
    sc.add("r_nw_brown", [(355, 250), (400, 85), (520, 85), (640, 195), (520, 270), (500, 335), (510, 430), (470, 500), (395, 500), (365, 440), (385, 330), (420, 300)], 40, 256, 120, ftex="FLOOR5_1")
    sc.add("r_south_cross", [(720, 1180), (850, 1070), (985, 1180), (850, 1305)], 0, 256, 130, ftex="FLOOR4_8")
    sc.add("snake_room", [(990, 1180), (1080, 1090), (1200, 1060), (1215, 1180), (1130, 1270), (1060, 1310), (1000, 1260)], 16, 256, 100, ftex="FLOOR5_1")
    sc.link("l_ne", "hub", "r_ne_brown", 70, 12, 256, 160)
    sc.link("l_east", "hub", "r_east", 70, 4, 256, 170)
    sc.link("l_sw", "hub", "r_sw_grey", 60, 0, 256, 160)
    sc.link("l_west", "hub", "r_west_brown", 70, 12, 256, 140)
    sc.link("l_nw", "hub", "r_nw_brown", 60, 20, 256, 140)
    sc.link("l_far", "r_east", "r_far_ne", 90, 12, 256, 150)
    sc.link("l_cross", "r_far_ne", "cross_tower", 60, 28, 256, 140)
    sc.link("l_south", "r_sw_grey", "r_south_cross", 70, 0, 256, 150)
    sc.link("l_snake", "r_south_cross", "snake_room", 60, 8, 256, 130)
    sc.start = (440, 560, (0, 1))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP08.jpg (rotated 45 degrees, north upper right), at an assumed 1 render px = 1 Doom unit; the hub is about 510 units across.",
        "Read from the render: an octagonal blue-water hub (a sunken square pool inside) with big rooms radiating from it: a long brown room to the north-east, a large grey room to the east leading to a far north-east grey hall and a cross-shaped tower, a long grey room to the south-west leading to a cross-shaped south room and a brown snake-shaped room, a brown room to the west, a brown stepped room to the north-west.",
        "NOT readable: heights (guessed 0 to +40, pool -24), the doors between rooms (the tracer inserts 60 to 90 unit links at the nearest edges, not where the real doors are), the interior walls and the small trap rooms, the long diagonal corridor to the north-west, the small dark tower west of the hub and the little room south-east of the hub.",
        "The brief's eight doors on the hub are NOT confirmed by the render: five links are inserted on the hub here.",
        "Room outlines are coarse readings of a 1500 px thumbnail."]
    return sc


def map02():
    sc = Scene("MAP02", "Underhalls (traced from the render)", 1.342, (0, 0), "MAP02.jpg")
    chan = [(405, 350), (520, 215), (740, 25), (880, 60), (990, 120), (960, 250), (1090, 310), (1260, 440), (1330, 560), (1220, 780), (1140, 850), (960, 900), (830, 840), (760, 780), (670, 700), (520, 630), (410, 530)]
    sc.add("plaza_ne", [(640, 270), (810, 135), (880, 205), (780, 345), (630, 400)], 24, 192, 150, ftex="FLOOR4_8")
    sc.add("plaza_mid", [(630, 420), (790, 345), (1000, 520), (1050, 650), (940, 720), (830, 760), (640, 560)], 24, 192, 160, ftex="FLOOR4_8")
    sc.add("brown_hall", [(1010, 60), (1130, 120), (1300, 300), (1310, 330), (1250, 400), (1090, 340), (1010, 260)], 16, 192, 140, ftex="FLOOR5_1")
    sc.add("brown_island", [(950, 760), (1010, 690), (1060, 750), (1000, 820)], 16, 192, 140, ftex="FLOOR5_1")
    sc.add("channel", chan, 0, 192, 90, holes=[], ftex="NUKAGE1")
    sc.add("grey_plaza", [(380, 700), (480, 650), (700, 780), (830, 900), (940, 1000), (1000, 1100), (1240, 1130), (1240, 1260), (1100, 1330), (1000, 1260), (900, 1120), (700, 1200), (620, 1100), (480, 1000), (380, 880)], 24, 192, 130, ftex="FLOOR4_8")
    sc.add("grey_lower", [(700, 1200), (900, 1130), (1000, 1260), (1100, 1330), (990, 1420), (860, 1450), (520, 1470), (400, 1440), (360, 1340), (500, 1290)], 8, 192, 120, ftex="FLOOR4_8")
    sc.add("brown_sw", [(230, 1190), (300, 1090), (450, 960), (580, 1110), (560, 1290), (420, 1370), (300, 1330)], 40, 192, 110, ftex="FLOOR5_1")
    sc.add("pond_w1", [(60, 410), (190, 280), (330, 130), (420, 140), (430, 260), (300, 430), (230, 520), (110, 450)], -16, 192, 80, ftex="NUKAGE1")
    sc.add("pond_w2", [(20, 650), (200, 560), (330, 700), (260, 840), (330, 950), (230, 960), (100, 780)], -16, 192, 80, ftex="NUKAGE1")
    sc.link("l_chan_w", "channel", "pond_w1", 80, -8, 192, 90, ftex="NUKAGE1")
    sc.link("l_grey_chan", "channel", "grey_plaza", 90, 12, 192, 120)
    sc.link("l_grey_low", "grey_plaza", "grey_lower", 100, 16, 192, 120)
    sc.link("l_sw", "grey_lower", "brown_sw", 80, 24, 192, 110)
    sc.link("l_w2", "grey_plaza", "pond_w2", 80, 4, 192, 100)
    sc.start = (1200, 260, (-1, 0))
    sc.uncertain = ["TRACED FROM THE RENDER MAP02.jpg, rough; see CONVERSION.md"]
    return sc


SCENES = {"warehouse": map07, "mothership": map11, "lounge": map08, "bar": map02}


def overlay(scene, sc):
    from PIL import Image, ImageDraw
    im = Image.open(os.path.join(RENDERS, sc.image))
    im.thumbnail((1500, 1500))
    dr = ImageDraw.Draw(im)
    for sid in sc.order:
        s = sc.secs[sid]
        dr.polygon(s["ring"], outline=(255, 255, 0))
    return im


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    want = [a for a in argv if not a.startswith("--")] or list(SCENES)
    for scene in want:
        sc = SCENES[scene]()
        d = sc.build()
        with open(os.path.join(HERE, scene + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(d, f, indent=0, separators=(",", ":"))
            f.write("\n")
        print(scene, len(d["vertices"]), "vertices", len(d["linedefs"]), "linedefs", len(d["sectors"]), "sectors")
        if "--overlay" in argv:
            out = os.environ.get("RW_OVERLAY_DIR", HERE)
            overlay(scene, sc).save(os.path.join(out, "overlay_%s.png" % scene))


if __name__ == "__main__":
    main()
