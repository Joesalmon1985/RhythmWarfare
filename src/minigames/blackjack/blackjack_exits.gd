class_name BlackjackExits
extends RefCounted
## The doors of the seated table (docs/BLACKJACK_INTEGRATION.md, exits while seated): where each way out of the room stands on the picture, its touch rectangle, and its drawing.
##
## Each exit the room gave the activity (MinigameActivity "exits") is its own open doorway with a glimpse of where it leads, drawn from data about the destination: its scene picks the
## glimpse (`GLIMPSES`: easels and paint for an art room, an iron bed under a barred window for a dormitory ...; `_` for a room the table does not know) and its sector's tint and light
## colour the walls. No words, letters or arrows: what a door leads to is what you see through it. Every door is drawn the same size and the same way whatever its rank (the default exit
## is told apart only by what it shows). With no exits there is one plain door (the plain "exit": get up, the room decides).
##
## Where the doors stand (`layout`): first the two edges of the picture, beside the outer people (a door whose route goes "left" or "right" takes that edge), then the far wall in the
## two gaps between the heads (`far_l`, `far_r`) for a third and a fourth. All of it is clear of the three people (`people_rects`), the money, the cards and the other touch targets, and
## every touch rectangle is at least 72 u in both directions. A door is drawn as a cached image (frame, swung leaf and glimpse: one draw per door) and redrawn only when what it shows changes.
## Its light (the spill on the floor, the warm ring and the edge light when leaving is urged) is a separate drawing whose strength breathes on the beat through the layer's alpha.

const SLOTS: Array[String] = ["right", "left", "far_l", "far_r"]
const EDGE_W := 74.0  # the touch rectangle at an edge, u
const EDGE_TOP := 26.0
const EDGE_H := 98.0
const EDGE_OPEN := Vector2(40.0, 72.0)  # the doorway's opening at an edge, u
const EDGE_FLOOR := 118.0  # the y of an edge door's threshold, u
const FAR_W := 72.0
const FAR_TOP := 3.0
const FAR_H := 72.0
const FAR_OPEN := Vector2(30.0, 52.0)
const FAR_FLOOR := 70.0

const INK := Color("10140f")
const FRAME := Color("2c3128")
const FRAME_LIGHT := Color("4a5244")
const LEAF := Color("4d6658")
const LEAF_LIGHT := Color("67826f")
const LEAF_DARK := Color("31443a")
const LEAF_GLASS := Color("86a49a")
const JAMB := Color("1d231c")
const WARM := Color("ffcf6a")
const WARM_HOT := Color("fff3b8")

## What a door shows of the room behind it, by the destination's scene id. wall / floor / light are the room's colours when its map gives no tint (a tint from the map replaces the wall
## and darkens into the floor); `props` are shapes in the opening's own unit square (x right, y down from the top of the opening; the far wall meets the floor at `horizon`):
## ["rect", x, y, w, h, colour], ["ell", cx, cy, rx, ry, colour], ["tri", x0, y0, x1, y1, x2, y2, colour], ["line", x0, y0, x1, y1, colour], ["bars", x, y, w, h, count, colour].
const GLIMPSES := {
	"art": {"wall": "8ea383", "floor": "5d4c3a", "light": "ffe2a0", "horizon": 0.64, "props": [
		["rect", 0.06, 0.16, 0.24, 0.17, "2a2a22"], ["rect", 0.08, 0.18, 0.20, 0.13, "e8c060"], ["ell", 0.18, 0.245, 0.06, 0.04, "d04848"],
		["rect", 0.70, 0.12, 0.24, 0.19, "2a2a22"], ["rect", 0.72, 0.14, 0.20, 0.15, "5aa0d8"], ["rect", 0.76, 0.20, 0.12, 0.05, "f4ecd2"],
		["line", 0.0, 0.07, 1.0, 0.09, "3a3428"],
		["tri", 0.04, 0.075, 0.16, 0.08, 0.10, 0.16, "e070a0"], ["tri", 0.22, 0.08, 0.34, 0.083, 0.28, 0.165, "f0c040"], ["tri", 0.40, 0.083, 0.52, 0.085, 0.46, 0.17, "50c0b0"],
		["tri", 0.58, 0.085, 0.70, 0.087, 0.64, 0.17, "e070a0"], ["tri", 0.76, 0.087, 0.88, 0.089, 0.82, 0.175, "f0c040"],
		["line", 0.40, 0.44, 0.27, 0.90, "7a5230"], ["line", 0.60, 0.44, 0.73, 0.90, "7a5230"], ["line", 0.50, 0.38, 0.50, 0.84, "5e3e24"],
		["rect", 0.28, 0.33, 0.44, 0.28, "3a2c20"], ["rect", 0.30, 0.35, 0.40, 0.24, "f4ecd2"],
		["rect", 0.33, 0.38, 0.14, 0.09, "e04848"], ["ell", 0.58, 0.44, 0.08, 0.06, "3870c8"], ["rect", 0.36, 0.50, 0.28, 0.05, "f0c040"],
		["rect", 0.24, 0.62, 0.52, 0.03, "7a5230"],
		["rect", 0.08, 0.82, 0.10, 0.07, "d04848"], ["rect", 0.08, 0.80, 0.10, 0.02, "f08080"], ["rect", 0.82, 0.84, 0.10, 0.07, "3870c8"], ["rect", 0.82, 0.82, 0.10, 0.02, "80b0f0"],
		["rect", 0.30, 0.94, 0.06, 0.02, "e070a0"], ["rect", 0.62, 0.74, 0.05, 0.02, "f0c040"], ["rect", 0.48, 0.88, 0.04, 0.02, "50c0b0"],
	]},
	"dorm": {"wall": "4f6a5a", "floor": "3a2e24", "light": "b8d0f0", "horizon": 0.60, "props": [
		["rect", 0.26, 0.08, 0.48, 0.30, "1c2420"], ["rect", 0.29, 0.11, 0.42, 0.24, "9ab8d8"], ["ell", 0.60, 0.18, 0.06, 0.05, "eef2e0"],
		["bars", 0.29, 0.11, 0.42, 0.24, 4, "1c2420"], ["rect", 0.29, 0.22, 0.42, 0.02, "1c2420"],
		["tri", 0.30, 0.62, 0.70, 0.62, 0.86, 0.98, "51697a"], ["tri", 0.30, 0.62, 0.86, 0.98, 0.42, 0.98, "51697a"],
		["rect", 0.05, 0.44, 0.05, 0.36, "1a1c20"], ["rect", 0.90, 0.54, 0.05, 0.26, "1a1c20"], ["rect", 0.05, 0.47, 0.90, 0.03, "1a1c20"],
		["rect", 0.08, 0.58, 0.86, 0.11, "d8d8cc"], ["rect", 0.34, 0.56, 0.60, 0.15, "56749c"], ["rect", 0.34, 0.56, 0.60, 0.03, "7c98c0"],
		["rect", 0.11, 0.52, 0.20, 0.07, "f0f0e6"], ["rect", 0.11, 0.58, 0.20, 0.01, "b0b0a6"],
		["rect", 0.08, 0.69, 0.86, 0.03, "1a1c20"], ["rect", 0.09, 0.72, 0.04, 0.14, "1a1c20"], ["rect", 0.88, 0.72, 0.04, 0.14, "1a1c20"],
	]},
	"corridor": {"wall": "6d8a78", "floor": "4a3c2e", "light": "ffd890", "horizon": 0.58, "props": [
		["tri", 0.0, 0.0, 0.36, 0.30, 0.0, 1.0, "3e5246"], ["tri", 0.0, 1.0, 0.36, 0.30, 0.36, 0.58, "3e5246"],
		["tri", 1.0, 0.0, 0.64, 0.30, 1.0, 1.0, "3a4c40"], ["tri", 1.0, 1.0, 0.64, 0.30, 0.64, 0.58, "3a4c40"],
		["rect", 0.42, 0.34, 0.16, 0.24, "1a1c18"], ["rect", 0.44, 0.36, 0.12, 0.22, "ffd890"],
		["tri", 0.44, 0.58, 0.56, 0.58, 0.70, 1.0, "8a7450"], ["tri", 0.44, 0.58, 0.70, 1.0, 0.30, 1.0, "8a7450"],
		["rect", 0.08, 0.30, 0.10, 0.36, "24302a"], ["rect", 0.84, 0.30, 0.08, 0.36, "24302a"],
	]},
	"courtyard": {"wall": "1d2644", "floor": "4a4e46", "light": "c8d4ff", "horizon": 0.66, "props": [
		["ell", 0.70, 0.18, 0.09, 0.07, "e8e8c8"], ["rect", 0.20, 0.30, 0.02, 0.02, "e0e0ff"], ["rect", 0.42, 0.12, 0.02, 0.02, "e0e0ff"],
		["ell", 0.24, 0.46, 0.18, 0.16, "16241a"], ["rect", 0.22, 0.52, 0.05, 0.16, "20180f"],
		["line", 0.0, 0.40, 1.0, 0.34, "2a2a30"], ["rect", 0.12, 0.38, 0.03, 0.03, "ffd070"], ["rect", 0.38, 0.37, 0.03, 0.03, "ff90c0"], ["rect", 0.62, 0.355, 0.03, 0.03, "90e0ff"],
		["rect", 0.86, 0.34, 0.03, 0.03, "ffd070"], ["rect", 0.0, 0.62, 1.0, 0.04, "2a2c28"],
	]},
	"garden": {"wall": "1a2238", "floor": "2e4a2c", "light": "c8d4ff", "horizon": 0.62, "props": [
		["ell", 0.30, 0.18, 0.07, 0.06, "e8e8c8"], ["ell", 0.70, 0.40, 0.22, 0.20, "142a18"], ["rect", 0.68, 0.48, 0.05, 0.16, "20180f"],
		["ell", 0.18, 0.56, 0.16, 0.08, "1c3a20"], ["rect", 0.40, 0.70, 0.30, 0.03, "6a5a40"],
	]},
	"treat": {"wall": "9cb6ae", "floor": "6c7c78", "light": "f4fff8", "horizon": 0.64, "props": [
		["bars", 0.0, 0.0, 1.0, 0.64, 6, "86a098"], ["line", 0.0, 0.21, 1.0, 0.21, "86a098"], ["line", 0.0, 0.42, 1.0, 0.42, "86a098"],
		["line", 0.50, 0.0, 0.50, 0.12, "30363a"], ["ell", 0.50, 0.15, 0.16, 0.05, "fff8d0"], ["tri", 0.36, 0.17, 0.64, 0.17, 0.82, 0.62, "fffbe0"],
		["rect", 0.22, 0.56, 0.56, 0.06, "b8c0c4"], ["rect", 0.26, 0.62, 0.04, 0.24, "6a7276"], ["rect", 0.70, 0.62, 0.04, 0.24, "6a7276"],
	]},
	"cafeteria": {"wall": "a8a088", "floor": "6a6458", "light": "fff0c8", "horizon": 0.62, "props": [
		["rect", 0.0, 0.30, 1.0, 0.10, "c8c0a8"], ["rect", 0.10, 0.22, 0.12, 0.08, "e0d8c0"], ["rect", 0.60, 0.22, 0.20, 0.08, "d06040"],
		["rect", 0.16, 0.66, 0.68, 0.05, "8a6a48"], ["rect", 0.20, 0.71, 0.04, 0.18, "5a4430"], ["rect", 0.76, 0.71, 0.04, 0.18, "5a4430"],
		["ell", 0.36, 0.64, 0.06, 0.02, "f4f4ec"], ["ell", 0.62, 0.64, 0.06, 0.02, "f4f4ec"],
	]},
	"bar": {"wall": "2a1830", "floor": "20141c", "light": "ff9ad8", "horizon": 0.62, "props": [
		["rect", 0.0, 0.18, 1.0, 0.04, "ff70c0"], ["rect", 0.08, 0.26, 0.06, 0.14, "60e0d0"], ["rect", 0.20, 0.28, 0.05, 0.12, "f0c040"], ["rect", 0.30, 0.26, 0.06, 0.14, "60a0ff"],
		["rect", 0.0, 0.52, 1.0, 0.14, "4a2a3a"], ["rect", 0.0, 0.52, 1.0, 0.02, "ff9ad8"],
	]},
	"_": {"wall": "5a6e64", "floor": "3c342a", "light": "ffe0a8", "horizon": 0.62, "props": [
		["ell", 0.50, 0.06, 0.18, 0.05, "fff0c0"], ["tri", 0.36, 0.08, 0.64, 0.08, 0.86, 0.62, "fff0c0"],
		["rect", 0.66, 0.30, 0.16, 0.32, "1c201c"], ["rect", 0.68, 0.32, 0.12, 0.30, "2c3430"],
	]},
}
const ALIASES := {"cafe": "cafeteria", "quiet": "treat", "floor": "bar", "booth": "bar", "chill": "bar", "balcony": "bar"}
const BAYER := [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]

static var _art_cache: Dictionary = {}  # key -> ImageTexture of one door (frame, leaf, glimpse)


# ------------------------------------------------------------------ layout

## The slot of each exit (in the exits' order): an exit whose route goes "right" or "left" takes that edge, the others the edges left over (right first), then the far wall.
static func slots_for(exits: Array) -> Array:
	var out: Array = []
	out.resize(exits.size())
	var free: Array = SLOTS.duplicate()
	for i in exits.size():
		var dir := str((exits[i] as Dictionary).get("dir", ""))
		if (dir == "right" or dir == "left") and dir in free:
			out[i] = dir
			free.erase(dir)
	for i in exits.size():
		if out[i] != null:
			continue
		var dir := str((exits[i] as Dictionary).get("dir", ""))
		var order: Array = ["right", "left", "far_r", "far_l"] if dir != "left" else ["left", "right", "far_l", "far_r"]
		for s: String in order:
			if s in free:
				out[i] = s
				free.erase(s)
				break
	return out


## Where every door stands on a canvas of `size`: [{route, slot, touch (Rect2, the touch rectangle), open (Rect2, the doorway's opening), side (+1 the leaf swings right, -1 left),
## far (bool)}] in the exits' order. `exits` are the snapshot's exit entries (or one entry {"route": ""} for the plain door).
static func layout(exits: Array, size: Vector2) -> Array:
	var u := maxf(BlackjackDraw.unit(size), 0.05)
	var out: Array = []
	var slots := slots_for(exits)
	for i in exits.size():
		var slot := str(slots[i]) if slots[i] != null else "right"
		out.append(slot_rects(slot, size, u))
		out[i]["route"] = str((exits[i] as Dictionary).get("route", ""))
	return out


## The rectangles of one slot: {slot, touch, open, side, far}.
static func slot_rects(slot: String, size: Vector2, u := -1.0) -> Dictionary:
	if u <= 0.0:
		u = maxf(BlackjackDraw.unit(size), 0.05)
	var far := slot.begins_with("far")
	var touch: Rect2
	var open: Rect2
	var side := 1.0
	if far:
		var cx := size.x * (0.35 if slot == "far_l" else 0.65)
		touch = Rect2(roundf(cx - FAR_W * 0.5 * u), roundf(FAR_TOP * u), roundf(FAR_W * u), roundf(FAR_H * u))
		var ow := roundf(FAR_OPEN.x * u)
		var oh := roundf(FAR_OPEN.y * u)
		open = Rect2(roundf(cx - ow * 0.5), roundf(FAR_FLOOR * u) - oh, ow, oh)
		side = -1.0 if slot == "far_l" else 1.0
	else:
		var w := roundf(EDGE_W * u)
		var x0 := size.x - w if slot == "right" else 0.0
		touch = Rect2(x0, roundf(EDGE_TOP * u), w, roundf(EDGE_H * u))
		var ow := roundf(EDGE_OPEN.x * u)
		var oh := roundf(EDGE_OPEN.y * u)
		var cx := x0 + w * 0.5 - (3.0 * u if slot == "right" else -3.0 * u)  # the opening a little in from the edge, the swung leaf on the outer side
		open = Rect2(roundf(cx - ow * 0.5), roundf(EDGE_FLOOR * u) - oh, ow, oh)
		side = 1.0 if slot == "right" else -1.0
	return {"slot": slot, "touch": touch, "open": open, "side": side, "far": far}


## Where the three people may be (their heads, shoulders and the reach of their arms at rest and in the usual gestures), for keeping the doors clear of them.
static func people_rects(size: Vector2) -> Array:
	var u := BlackjackDraw.unit(size)
	var out: Array = []
	for who in BlackjackDraw.SEATS:
		var c := BlackjackDraw.seat_pos(who, size)
		out.append(Rect2(c.x - 34.0 * u, c.y - 36.0 * u, 68.0 * u, 56.0 * u))  # head and hair
		out.append(Rect2(c.x - 50.0 * u, c.y + 20.0 * u, 100.0 * u, 70.0 * u))  # shoulders, arms, hands on the table
	return out


# ------------------------------------------------------------------ colours of a destination

static func glimpse_of(scene: String) -> Dictionary:
	var key := str(ALIASES.get(scene, scene))
	return GLIMPSES.get(key, GLIMPSES["_"])


## {wall, wall_lit, floor, light} of a destination: the glimpse's own colours, or the map's tint when it gave one (the wall in that light, the floor a darker shade of it).
static func palette(scene: String, tint: String, light: float) -> Dictionary:
	var g := glimpse_of(scene)
	var lit := Color(str(g["light"]))
	var wall := Color(str(g["wall"]))
	var floor := Color(str(g["floor"]))
	if tint != "" and Color.html_is_valid(tint):
		var t := Color(tint)
		wall = (t * (0.45 + 0.55 * clampf(light, 0.0, 1.0))).lerp(wall, 0.35)
		wall.a = 1.0
	return {"wall": wall.darkened(0.2), "wall_lit": wall.lerp(lit, 0.42), "floor": floor, "light": lit}


# ------------------------------------------------------------------ drawing

## The doors (layer "door"): `doors` = [[slot, scene, tint, light, chosen, hc], ...]; every door is one cached image, drawn at whole pixels.
static func draw_doors(ci: CanvasItem, size: Vector2, u: float, doors: Array) -> void:
	for d: Array in doors:
		var r := slot_rects(str(d[0]), size, u)
		var tex := door_texture(r, u, str(d[1]), str(d[2]), float(d[3]), bool(d[4]), bool(d[5]))
		var org: Vector2 = tex.get_meta("origin", Vector2.ZERO)
		ci.draw_texture(tex, (r["open"] as Rect2).position - org)


## The light of the doors (layer "door_glow", its alpha breathes on the beat): `lit` = [[slot, scene, tint, light, urged, chosen], ...]: a spill of the room's light on the floor in front of
## each touchable door; when leaving is urged also the warm ring at the door's foot and light on the doorway's edges (the table's hint language); the chosen door floods.
static func draw_glow(ci: CanvasItem, size: Vector2, u: float, hc: bool, lit: Array) -> void:
	for d: Array in lit:
		var r := slot_rects(str(d[0]), size, u)
		var o: Rect2 = r["open"]
		var pal := palette(str(d[1]), str(d[2]), float(d[3]))
		var urged := bool(d[4])
		var chosen := bool(d[5])
		var col: Color = (pal["light"] as Color).lerp(WARM, 0.45)
		var side: float = r["side"]
		var far: bool = r["far"]
		var reach := (10.0 if far else 22.0) * u * (1.6 if chosen else 1.0)
		var lean := -side * (6.0 if far else 16.0) * u * (1.6 if chosen else 1.0)  # the spill falls toward the middle of the room
		var by := o.end.y
		BlackjackDraw.poly(ci, PackedVector2Array([
			Vector2(roundf(o.position.x), by), Vector2(roundf(o.end.x), by),
			Vector2(roundf(o.end.x + lean + 6.0 * u), roundf(by + reach)), Vector2(roundf(o.position.x + lean - 6.0 * u), roundf(by + reach)),
		]), BlackjackDraw.shade(col, 0.7 if chosen else 0.42))
		BlackjackDraw.ell(ci, o.get_center().x, o.get_center().y, o.size.x * 0.9, o.size.y * 0.62, BlackjackDraw.shade(col, 0.18 if not chosen else 0.34))
		if chosen:  # lit, but light enough that the room it leads to still shows through
			BlackjackDraw.rect(ci, o.position.x, o.position.y, o.size.x, o.size.y, BlackjackDraw.shade(WARM_HOT, 0.24))
		if urged or chosen:
			var c := Vector2(o.get_center().x + lean * 0.4, by + 2.0 * u)
			var rx := o.size.x * 0.5 + 12.0 * u
			var ry := (4.0 if far else 6.0) * u
			BlackjackDraw.ell(ci, c.x, c.y, rx, ry, BlackjackDraw.shade(WARM, 0.38))
			var pts := PackedVector2Array()
			for i in 29:
				var th := TAU * float(i) / 28.0
				pts.append(Vector2(roundf(c.x + cos(th) * rx), roundf(c.y + sin(th) * ry)))
			ci.draw_polyline(pts, WARM_HOT, maxf(1.0, roundf(u * (3.0 if hc else 2.0))))
			var px := maxf(1.0, roundf(u * (2.0 if hc else 1.0)))
			var f := o.grow(px + maxf(1.0, roundf(4.0 * u)))
			BlackjackDraw.rect(ci, f.position.x, f.position.y, f.size.x, px, WARM_HOT)
			BlackjackDraw.rect(ci, f.position.x, f.position.y, px, f.size.y - roundf(2.0 * u), WARM_HOT)
			BlackjackDraw.rect(ci, f.end.x - px, f.position.y, px, f.size.y - roundf(2.0 * u), WARM_HOT)


## One door as a texture (cached): the frame, the leaf swung open on the slot's outer side (wide open against the wall once chosen) and, in the opening, the glimpse of the room behind.
## The texture's meta "origin" is the opening's top-left inside it.
static func door_texture(r: Dictionary, u: float, scene: String, tint: String, light: float, chosen: bool, hc: bool) -> ImageTexture:
	var o: Rect2 = r["open"]
	var side: float = r["side"]
	var key := "%s|%s|%s|%.2f|%d|%d|%d|%d|%d" % [scene, tint, str(r["far"]), light, int(o.size.x), int(o.size.y), int(side), int(chosen), int(hc)]
	var hit: Variant = _art_cache.get(key)
	if hit != null:
		return hit
	var ow := int(o.size.x)
	var oh := int(o.size.y)
	var ft := maxi(2, int(roundf((3.0 if r["far"] else 4.0) * u)))  # the frame's thickness
	var lw := int(roundf(float(ow) * (0.22 if chosen else 0.42)))  # the leaf's width as seen
	var lift := maxi(1, int(roundf(3.0 * u)))  # the leaf's near edge is taller (it is nearer)
	var left_pad := ft + 1 + (lw + 1 if side < 0.0 else 0)
	var w := ow + 2 * (ft + 1) + lw + 1
	var h := oh + ft + 1 + lift + 1
	var img := Image.create_empty(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var ox := left_pad
	var oy := ft + 1
	_glimpse(img, Rect2i(ox, oy, ow, oh), scene, tint, light, r["far"], u, chosen)
	# the jamb's depth on the side away from the leaf (the doorway is in a thick wall)
	var jw := maxi(1, int(roundf(2.0 * u)))
	var jx := ox + ow - jw if side < 0.0 else ox
	img.fill_rect(Rect2i(jx, oy, jw, oh), JAMB)
	# the frame: ink outside, the frame, a lit inner edge on top
	var fx := ox - ft
	var fy := oy - ft
	var fw := ow + 2 * ft
	var fh := oh + ft
	img.fill_rect(Rect2i(fx - 1, fy - 1, fw + 2, ft + 1), INK)
	img.fill_rect(Rect2i(fx - 1, fy - 1, ft + 1, fh + 1), INK)
	img.fill_rect(Rect2i(fx + fw - ft, fy - 1, ft + 1, fh + 1), INK)
	img.fill_rect(Rect2i(fx, fy, fw, ft - 1), FRAME)
	img.fill_rect(Rect2i(fx, fy, ft - 1, fh), FRAME)
	img.fill_rect(Rect2i(fx + fw - ft + 1, fy, ft - 1, fh), FRAME)
	img.fill_rect(Rect2i(fx, fy, fw, 1), FRAME_LIGHT)
	img.fill_rect(Rect2i(fx + (0 if side > 0.0 else fw - ft + 1), fy, 1, fh), FRAME_LIGHT)
	if hc:
		var hcc := Color("fff3b8")
		img.fill_rect(Rect2i(fx - 1, fy - 1, fw + 2, 1), hcc)
		img.fill_rect(Rect2i(fx - 1, fy - 1, 1, fh + 1), hcc)
		img.fill_rect(Rect2i(fx + fw, fy - 1, 1, fh + 1), hcc)
	# the leaf, swung open toward us on the outer side: a trapezoid, its far (hinge) edge at the frame, its near edge taller
	var hinge_x := fx + fw if side > 0.0 else fx - 1
	var near_x := hinge_x + int(side) * lw
	var top_h := oy
	var bot_h := oy + oh - 1
	var top_n := oy - lift
	var bot_n := oy + oh - 1 + lift
	var x_from := mini(hinge_x, near_x)
	var x_to := maxi(hinge_x, near_x)
	for x in range(x_from, x_to + 1):
		var k := 0.0 if lw == 0 else float(absi(x - hinge_x)) / float(lw)
		var y0 := int(roundf(lerpf(top_h, top_n, k)))
		var y1 := int(roundf(lerpf(bot_h, bot_n, k)))
		y0 = clampi(y0, 0, h - 1)
		y1 = clampi(y1, 0, h - 1)
		var edge := x == x_from or x == x_to
		for y in range(y0, y1 + 1):
			var c := LEAF
			if edge or y == y0 or y == y1:
				c = INK
			elif k > 0.82:
				c = LEAF_LIGHT if not chosen else LEAF_LIGHT.lerp(WARM, 0.25)
			elif k < 0.18:
				c = LEAF_DARK
			else:
				var fy0 := lerpf(top_h, top_n, k)
				var span := maxf(1.0, lerpf(bot_h, bot_n, k) - fy0)
				var v := (float(y) - fy0) / span
				if v > 0.12 and v < 0.36 and k > 0.3 and k < 0.72:
					c = LEAF_GLASS if not chosen else LEAF_GLASS.lerp(WARM_HOT, 0.4)  # the wired-glass panel
				elif v > 0.84:
					c = LEAF_DARK  # the kick plate
				elif (x + y) % 2 == 0 and v > 0.5 and v < 0.53:
					c = LEAF_DARK
			img.set_pixel(x, y, c)
	var tex := ImageTexture.create_from_image(img)
	tex.set_meta("origin", Vector2(ox, oy))
	if _art_cache.size() >= 48:
		_art_cache.clear()
	_art_cache[key] = tex
	return tex


## The room behind a door, painted into `img` inside `at`: a dithered wall brighter where its light is, a floor, the scene's props, and the far wall's shadow at the top.
static func _glimpse(img: Image, at: Rect2i, scene: String, tint: String, light: float, far: bool, u: float, chosen: bool) -> void:
	var g := glimpse_of(scene)
	var pal := palette(scene, tint, light)
	var hz := int(roundf(float(at.size.y) * float(g.get("horizon", 0.62))))
	var wall: Color = pal["wall"]
	var wall_lit: Color = pal["wall_lit"]
	var flo: Color = pal["floor"]
	var lit: Color = pal["light"]
	if chosen:
		wall = wall.lerp(lit, 0.18)
		wall_lit = wall_lit.lerp(lit, 0.25)
	var cx := float(at.size.x) * 0.5
	for y in at.size.y:
		for x in at.size.x:
			var c: Color
			var b: int = BAYER[(y % 4) * 4 + (x % 4)]
			if y < hz:
				var dx := (float(x) - cx) / maxf(1.0, cx)
				var dy := float(y) / maxf(1.0, float(hz))
				var k := clampf(1.0 - (dx * dx * 0.8 + (dy - 0.45) * (dy - 0.45) * 1.6), 0.0, 1.0)
				c = wall_lit if float(b) < k * 16.0 else wall
			else:
				var fy := float(y - hz) / maxf(1.0, float(at.size.y - hz))
				var k := clampf(0.75 - absf((float(x) - cx) / maxf(1.0, cx)) * 0.6 + fy * 0.2, 0.0, 1.0)
				c = flo.lerp(lit, 0.22) if float(b) < k * 9.0 else flo
				if y == hz:
					c = flo.darkened(0.35)
			img.set_pixel(at.position.x + x, at.position.y + y, c)
	for p: Array in g["props"]:
		_prop(img, at, p)
	# the top of the doorway in shadow, so the glimpse reads as a room beyond, not a picture
	var sh := maxi(1, int(roundf(2.0 * u)))
	for y in sh:
		for x in at.size.x:
			if (x + y) % 2 == 0 or y == 0:
				img.set_pixel(at.position.x + x, at.position.y + y, JAMB)


static func _prop(img: Image, at: Rect2i, p: Array) -> void:
	var W := float(at.size.x)
	var H := float(at.size.y)
	var ax := at.position.x
	var ay := at.position.y
	match str(p[0]):
		"rect":
			var x0 := ax + int(roundf(float(p[1]) * W))
			var y0 := ay + int(roundf(float(p[2]) * H))
			var x1 := ax + int(roundf((float(p[1]) + float(p[3])) * W))
			var y1 := ay + int(roundf((float(p[2]) + float(p[4])) * H))
			_fill(img, at, x0, y0, maxi(x1, x0 + 1), maxi(y1, y0 + 1), Color(str(p[5])))
		"ell":
			var ccx := float(ax) + float(p[1]) * W
			var ccy := float(ay) + float(p[2]) * H
			var rx := maxf(0.5, float(p[3]) * W)
			var ry := maxf(0.5, float(p[4]) * H)
			var col := Color(str(p[5]))
			for yy in range(int(floorf(ccy - ry)), int(ceilf(ccy + ry)) + 1):
				var k := (float(yy) + 0.5 - ccy) / ry
				if absf(k) > 1.0:
					continue
				var hw := rx * sqrt(1.0 - k * k)
				_fill(img, at, int(roundf(ccx - hw)), yy, maxi(int(roundf(ccx + hw)), int(roundf(ccx - hw)) + 1), yy + 1, col)
		"tri":
			var a := Vector2(ax + float(p[1]) * W, ay + float(p[2]) * H)
			var b := Vector2(ax + float(p[3]) * W, ay + float(p[4]) * H)
			var c := Vector2(ax + float(p[5]) * W, ay + float(p[6]) * H)
			var col := Color(str(p[7]))
			var lo := Vector2i(int(floorf(minf(a.x, minf(b.x, c.x)))), int(floorf(minf(a.y, minf(b.y, c.y)))))
			var hi := Vector2i(int(ceilf(maxf(a.x, maxf(b.x, c.x)))), int(ceilf(maxf(a.y, maxf(b.y, c.y)))))
			var poly := PackedVector2Array([a, b, c])
			for yy in range(lo.y, hi.y + 1):
				for xx in range(lo.x, hi.x + 1):
					if Geometry2D.is_point_in_polygon(Vector2(xx + 0.5, yy + 0.5), poly):
						_put(img, at, xx, yy, col)
		"line":
			var a := Vector2(ax + float(p[1]) * W, ay + float(p[2]) * H)
			var b := Vector2(ax + float(p[3]) * W, ay + float(p[4]) * H)
			var col := Color(str(p[5]))
			var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y))) + 1
			for i in n + 1:
				var q := a.lerp(b, float(i) / float(maxi(n, 1)))
				_put(img, at, int(floorf(q.x)), int(floorf(q.y)), col)
		"bars":
			var x0 := float(ax) + float(p[1]) * W
			var bw := float(p[3]) * W
			var y0 := ay + int(roundf(float(p[2]) * H))
			var y1 := ay + int(roundf((float(p[2]) + float(p[4])) * H))
			var count := int(p[5])
			var col := Color(str(p[6]))
			for i in range(1, count):
				var xx := int(roundf(x0 + bw * float(i) / float(count)))
				_fill(img, at, xx, y0, xx + 1, y1, col)


static func _fill(img: Image, at: Rect2i, x0: int, y0: int, x1: int, y1: int, col: Color) -> void:
	var r := Rect2i(x0, y0, x1 - x0, y1 - y0).intersection(at)
	if r.size.x > 0 and r.size.y > 0:
		img.fill_rect(r, col)


static func _put(img: Image, at: Rect2i, x: int, y: int, col: Color) -> void:
	if at.has_point(Vector2i(x, y)):
		img.set_pixel(x, y, col)
