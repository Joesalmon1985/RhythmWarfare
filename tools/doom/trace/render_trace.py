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
        ca = (sum(p[0] for p in ra) / len(ra), sum(p[1] for p in ra) / len(ra))
        cb = (sum(p[0] for p in rb) / len(rb), sum(p[1] for p in rb) / len(rb))
        best = (1e18,)
        for i in range(len(ra)):
            for j in range(len(rb)):
                pa, qa, pb, qb = ra[i], ra[(i + 1) % len(ra)], rb[j], rb[(j + 1) % len(rb)]
                la, lb = math.hypot(qa[0] - pa[0], qa[1] - pa[1]), math.hypot(qb[0] - pb[0], qb[1] - pb[1])
                if la < 50 or lb < 50:
                    continue
                facing = ((qa[0] - pa[0]) * (qb[0] - pb[0]) + (qa[1] - pa[1]) * (qb[1] - pb[1])) / (la * lb)
                if facing > -0.5:  # the two edges must face each other (roughly anti-parallel)
                    continue
                d, ta, tb = seg_closest(pa, qa, pb, qb)
                if d < 16:  # the edges already touch: a door would overlap them
                    continue
                ma, mb = ((pa[0] + qa[0]) / 2, (pa[1] + qa[1]) / 2), ((pb[0] + qb[0]) / 2, (pb[1] + qb[1]) / 2)
                score = math.hypot(ma[0] - cb[0], ma[1] - cb[1]) + math.hypot(mb[0] - ca[0], mb[1] - ca[1]) + 3 * math.sqrt(d)
                if score < best[0]:
                    best = (score, i, ta, j, tb)
        if len(best) < 5:
            print("  link %s (%s - %s) skipped: no facing edges" % (sid, a, b))
            return
        _, i, ta, j, tb = best

        def door(ring, i, t):
            p, q = ring[i], ring[(i + 1) % len(ring)]
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            w = min(width, L - 24)
            c = t * L
            c = min(max(c, w / 2 + 12), L - w / 2 - 12)
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
    sc.add("r_ne_brown", [(548, 565), (905, 40), (1020, 150), (710, 520), (580, 605)], 24, 256, 130, ftex="FLOOR5_1")
    sc.add("r_east", [(565, 625), (735, 565), (940, 610), (1020, 690), (1000, 860), (960, 985), (840, 985), (720, 1020), (705, 925), (600, 895)], 8, 256, 150, ftex="FLOOR4_8")
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
    sc = Scene("MAP02", "Underhalls (traced from the render)", 1.342, (700, 750), "MAP02.jpg")
    chan = [(405, 350), (520, 215), (740, 25), (900, 70), (985, 125), (1000, 255), (1170, 400), (1330, 540), (1330, 600), (1220, 790), (1130, 860), (960, 905), (830, 845), (760, 785), (670, 705), (520, 635), (410, 530)]
    island = [(625, 420), (650, 290), (810, 135), (880, 205), (1000, 330), (1150, 430), (1140, 560), (1040, 640), (990, 700), (940, 730), (830, 760), (700, 640), (640, 560)]
    sc.add("plateau", island, 24, 192, 160, ftex="FLOOR4_8")
    sc.add("channel", chan, -16, 192, 90, holes=["plateau"], ftex="NUKAGE1")
    sc.add("brown_hall", [(1030, 75), (1125, 130), (1290, 300), (1290, 335), (1240, 385), (1030, 255)], 16, 192, 140, ftex="FLOOR5_1")
    sc.add("grey_plaza", [(390, 745), (485, 690), (690, 825), (800, 905), (930, 965), (1000, 1105), (1235, 1135), (1240, 1260), (1100, 1330), (990, 1420), (860, 1450), (630, 1460), (600, 1330), (620, 1105), (500, 1000), (400, 860)], 24, 192, 130, ftex="FLOOR4_8")
    sc.add("brown_sw", [(240, 1190), (300, 1110), (400, 1020), (510, 1130), (500, 1290), (420, 1365), (305, 1330)], 40, 192, 110, ftex="FLOOR5_1")
    sc.add("pond_w1", [(60, 410), (190, 280), (330, 130), (420, 140), (430, 260), (300, 430), (230, 520), (110, 450)], -16, 192, 80, ftex="NUKAGE1")
    sc.add("pond_w2", [(20, 650), (200, 560), (330, 700), (260, 840), (310, 940), (230, 960), (100, 780)], -16, 192, 80, ftex="NUKAGE1")
    sc.link("l_chan_w", "channel", "pond_w1", 80, -8, 192, 90, ftex="NUKAGE1")
    sc.link("l_chan_grey", "channel", "grey_plaza", 100, 12, 192, 120)
    sc.link("l_chan_hall", "channel", "brown_hall", 70, 0, 192, 120)
    sc.link("l_sw", "grey_plaza", "brown_sw", 70, 32, 192, 110)
    sc.start = (1150, 280, (-1, 0))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP02.jpg (rotated 45 degrees, north upper right; 1 render px = 1 Doom unit assumed; about 2400 units tall).",
        "Read from the render: a winding blue nukage channel looping round a raised grey plateau in the north, a brown hall in the north-east corner, two nukage-floored side rooms in the west, a big grey plaza running diagonally across the south with a brown room at its south-west end.",
        "NOT readable: heights (guessed: nukage -16, plateau and plazas +24, brown rooms +16 to +40), the walkways along the channel edges (thin fence lines), the stairs, doors and small side rooms, the second ring of the channel in the east (traced as one loop), the brown steps inside the plateau. Doors between the traced areas are inserted by the tracer at the nearest facing edges.",
        "The brief's low interconnected cellar rooms, winding passages, drainage channels and short stairs are read here as the channel loop and the plazas; the render shows an open industrial hall complex more than a cellar. Room outlines are coarse readings of a 1500 px thumbnail."]
    return sc


def map04():
    sc = Scene("MAP04", "The Focus (traced from the render)", 1.403, (700, 750), "MAP04.jpg")
    sc.add("start_room", [(770, 455), (835, 390), (905, 470), (855, 540), (815, 525)], 0, 160, 140, ftex="FLOOR4_8")
    sc.add("hall", [(440, 830), (560, 650), (760, 510), (785, 545), (880, 700), (880, 870), (850, 990), (780, 1085), (690, 1105), (600, 1000), (480, 905)], 0, 192, 100, ftex="FLOOR4_8")
    sc.add("tl_complex", [(105, 185), (215, 100), (300, 105), (560, 330), (565, 400), (430, 600), (330, 560), (250, 520), (150, 380), (105, 260)], 32, 192, 110, ftex="FLOOR5_1")
    sc.add("s_corridor", [(910, 700), (955, 620), (1035, 610), (1045, 810), (1120, 930), (1120, 1195), (940, 1210), (915, 1120), (905, 900)], 0, 192, 90, ftex="FLOOR4_8")
    sc.add("right_room", [(1075, 745), (1180, 590), (1260, 640), (1400, 790), (1400, 925), (1260, 1020), (1115, 885)], 16, 192, 140, ftex="FLOOR4_8")
    sc.add("pit", [(520, 1060), (720, 1235), (650, 1350), (450, 1290), (390, 1190)], -64, 192, 40, ftex="FLOOR4_8")
    sc.add("bl_L", [(90, 1100), (300, 905), (520, 1000), (520, 1060), (390, 1190), (450, 1290), (650, 1350), (720, 1235), (770, 1290), (650, 1430), (500, 1430), (190, 1245)], 8, 192, 120, ftex="FLOOR4_8")
    sc.link("l_start", "hall", "start_room", 60, 0, 160, 130)
    sc.link("l_tl", "hall", "tl_complex", 80, 8, 192, 110)
    sc.link("l_s", "hall", "s_corridor", 80, 0, 192, 100)
    sc.link("l_right", "s_corridor", "right_room", 80, 8, 192, 120)
    sc.link("l_bl", "hall", "bl_L", 80, 4, 192, 110)
    sc.start = (830, 480, (0, 1))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP04.jpg (rotated 45 degrees, north upper right; 1 render px = 1 Doom unit assumed; about 2900 units across).",
        "Read from the render: a big central dark hall running north-east to south-west, a small start room at its north end, a stepped brown complex with arms in the north-west, an S-shaped corridor to the east leading to a room with brown blocks, an L-shaped grey corridor in the south-west wrapping a dark pit.",
        "NOT readable: heights (guessed 0 to +32, pit -64), the many small windowed control rooms, equipment bays and doors the brief names (the render shows large rooms and green-grey wall faces, not the interiors), the three arms of the north-west complex, the brown steps, the window walls. Links between traced rooms are inserted at the nearest facing edges.",
        "The brief's tight windowed control rooms, equipment bays and interlocking corridors are NOT visible at this resolution; this trace gives the macro footprint only."]
    return sc


def blocks(sc, specs, floor, ceil):
    ids = []
    for i, (cx, cy, h) in enumerate(specs):
        sid = "block_%d" % (i + 1)
        sc.add(sid, D(cx, cy, h), floor, ceil, 70 + 15 * (i % 4), ftex="FLOOR5_1")
        ids.append(sid)
    return ids


def map13():
    sc = Scene("MAP13", "Downtown (traced from the render)", 3.49, (700, 750), "MAP13.jpg")
    street = [(-10, 835), (150, 640), (300, 520), (480, 330), (640, 170), (830, 150), (1000, 300), (1180, 450), (1300, 540), (1375, 745), (610, 1500), (400, 1350), (230, 1170), (60, 1030)]
    ids = blocks(sc, [(585, 345, 95), (440, 520, 95), (275, 690, 95), (585, 700, 105), (740, 510, 105), (890, 360, 90), (1050, 510, 95), (430, 830, 105), (580, 960, 105), (740, 1130, 100), (610, 1290, 100), (1210, 640, 95)], 64, 480)
    sc.add("block_big", [(790, 970), (950, 720), (1105, 840), (930, 1110)], 64, 480, 80, ftex="FLOOR5_1")
    sc.add("block_red", [(45, 835), (190, 740), (370, 940), (250, 1075)], 64, 480, 85, ftex="FLOOR5_1")
    sc.add("street", street, 0, 640, 150, holes=ids + ["block_big", "block_red"], ftex="FLOOR0_1", ctex=SKY)
    sc.start = (800, 740, (1, -1))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP13.jpg (rotated 45 degrees, north upper right; 1 render px = 1 Doom unit assumed). CURATED REGION: the whole central street grid with fourteen of its building blocks, about 4800 units across; NOT traced: the tall brown fence walls beyond the north-east edge, the arch-shaped platform at the north tip, the black arrow and entrance at the west, the guard walls at the south-west.",
        "Read from the render: one huge open grey plaza (the street) with separate square city blocks standing in it in a loose grid; each block is a walled enclosure whose interior is drawn (brown, grey, red, green rooms). Block footprints are traced as diamonds of about 400 to 700 units (positions read by eye).",
        "NOT readable: heights (guessed: street 0, block floors +64, block ceilings 480, street open to the sky at 640), block interiors (each block is ONE flat room here: no doors, no inner walls, no props; the blocks are holes in the street joined to it by their whole edge, so street-to-block walls have a 2 m ledge, not a door), the true sizes of the small blocks, the big south-east block's inner water.",
        "Street corners, loading areas and service yards of the brief are read as the open spaces between blocks; none is individually marked in the render."]
    return sc


def map15():
    sc = Scene("MAP15", "Industrial Zone (traced from the render)", 4.62, (700, 700), "MAP15.jpg")
    plateau = [(240, 570), (450, 330), (680, 140), (790, 150), (930, 310), (1170, 430), (1230, 520), (1050, 640), (850, 720), (840, 1000), (720, 1080), (380, 1110), (310, 950), (330, 730), (300, 600)]
    sc.add("lake", [(930, 310), (880, 210), (1020, 5), (1190, 60), (1500, 380), (1340, 680), (1230, 520), (1170, 430)], -64, 400, 40, ftex="NUKAGE1")
    sc.add("tower_a", D(680, 265, 60), 80, 520, 130, ftex="FLOOR5_1")
    sc.add("tower_b", D(800, 360, 60), 64, 520, 130, ftex="FLOOR5_1")
    sc.add("keep", D(610, 440, 40), 128, 520, 150, ftex="FLOOR0_1")
    sc.add("lava_moat", D(610, 520, 112), -48, 520, 200, holes=["keep"], ftex="LAVA1")
    sc.add("lava_pit", D(1010, 480, 65), -32, 520, 210, ftex="LAVA1")
    sc.add("stone_block", D(1010, 480, 105), 64, 520, 110, holes=["lava_pit"], ftex="FLOOR0_1")
    sc.add("ring_void", D(570, 820, 45), -160, 520, 30, ftex="FLOOR4_8")
    sc.add("ring_hall", D(570, 820, 125), 48, 520, 100, holes=["ring_void"], ftex="FLOOR5_1")
    sc.add("plateau", plateau, 0, 520, 150, holes=["tower_a", "tower_b", "lava_moat", "stone_block", "ring_hall"], ftex="GRASS1", ctex=SKY)
    sc.start = (900, 620, (-1, -1))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP15.jpg (rotated 45 degrees, north upper right; 1 render px = 1 Doom unit assumed; the full map is about 6900 units across). CURATED REGION: the grass plateau with its northern and central masses (about 3300 by 3300 units) and the lake at its east edge. NOT traced: the south-west lava circle, the wooden complex and round rooms in the south, the dark winding paths and the small rooms at the west edge.",
        "Read from the render: a grass-floored plateau enclosed by a dark grey wall on its north and west sides, a large dark-blue lake to the east, and separate building masses on the plateau: two brown towers in the north, a lava moat around an inner tower, a stone block holding a lava pit, a large brown checkered ring building with black voids at its centre.",
        "NOT readable: heights (guessed: plateau 0, towers +64 and +80, ring hall +48, lava -48 and -32, lake -64, keep +128), roof ledges, bridges and the interiors of the buildings (each is ONE flat room here), the exposed drops: the render shows no bridges between the masses, so none is traced. The brief's rooftop ledges and bridges are therefore NOT present.",
        "The ring building's voids are one square pit at its centre (the render shows four-armed black voids)."]
    return sc


def map29():
    sc = Scene("MAP29", "The Living End (traced from the render)", 3.41, (700, 700), "MAP29.jpg")
    basin = [(140, 890), (220, 610), (300, 500), (440, 365), (830, 375), (900, 520), (1100, 780), (1105, 1060), (880, 1310), (570, 1370), (160, 1000)]
    top = [(470, 900), (520, 810), (590, 750), (690, 760), (730, 830), (730, 960), (670, 1020), (590, 1050), (520, 1010), (470, 930)]
    mid = [(420, 900), (470, 780), (575, 700), (725, 710), (775, 810), (775, 990), (700, 1065), (585, 1110), (500, 1050), (420, 950)]
    outer = [(395, 900), (440, 760), (570, 665), (740, 680), (800, 800), (800, 1000), (710, 1090), (580, 1140), (480, 1070), (395, 950)]
    sc.add("rock_top", top, 192, 700, 200, ftex="FLOOR0_1")
    sc.add("rock_mid", mid, 144, 700, 170, holes=["rock_top"], ftex="FLOOR0_1")
    sc.add("rock_foot", outer, 96, 700, 130, holes=["rock_mid"], ftex="FLOOR0_1")
    sc.add("east_mass", [(945, 830), (1060, 820), (1065, 1050), (945, 1065)], 64, 700, 120, ftex="FLOOR5_1")
    sc.add("west_ledge", [(205, 780), (330, 740), (335, 820), (210, 860)], 24, 700, 140, ftex="FLOOR0_1")
    sc.add("basin", basin, -192, 800, 60, holes=["rock_foot", "east_mass", "west_ledge"], ftex="LAVA1", ctex=SKY)
    sc.add("north_ledge", [(300, 500), (440, 365), (830, 375), (900, 520), (945, 470), (870, 330), (440, 320), (320, 410)], 128, 700, 130, ftex="FLOOR5_1")
    sc.start = (600, 345, (0, 1))
    sc.uncertain = [
        "TRACED FROM THE RENDER MAP29.jpg (rotated 45 degrees, north upper right; 1 render px = 1 Doom unit assumed). CURATED REGION: the lava basin (about 3600 by 3600 units), the central rock mass and a strip of the north cliff top. NOT traced: the cluster of rooms and the square lava pool at the north, the east octopus-like lava arms with their green ledges, the west grey ledges and small rooms, the south-west rooms.",
        "Read from the render: a huge ten-sided red lava basin; at its centre a rock mass rising in terraces (a stepped round tower with grey rim ledges and a brown top); a smaller brown mass on the east; a tall brown cliff along the north rim; grey ledges on the west rim.",
        "NOT readable: heights (guessed: lava -192, west ledge +24, east mass +64, rock mass three terraces +96, +144, +192, north cliff top +128), the true terrace count and width (three nested rings are traced; the render shows narrow ledges winding up the rock, not rings), the narrow ascending cliff paths of the brief (NOT traced: the render does not show where they run), the red diamond lifts in the lava.",
        "The central rock mass stands free in the lava: there is no bridge or path from the rim to it in the render, so none is traced; the terraces connect to the basin only by sheer ledges."]
    return sc


SCENES = {"warehouse": map07, "mothership": map11, "lounge": map08, "bar": map02, "booth": map04, "dock": map13, "balcony": map15, "underworld": map29}


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
