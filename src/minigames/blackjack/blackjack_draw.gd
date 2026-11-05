class_name BlackjackDraw
extends RefCounted
## The blackjack drawing kit, part one: pixel primitives, playing cards, the deck, the table, the exit door and where everything sits on the picture.
##
## Everything is drawn with `_draw()` primitives into the low-res viewport (about 640 x 230, sometimes half that), so every shape is built from whole-pixel rects, rect rows and
## unrounded-free polygons: no anti-aliasing, no fonts. `u = size.y / 230.0` is the unit. Geometry functions take the canvas `size` and return canvas pixels.
## The people and the player's hands are in `BlackjackPeople`, which uses the primitives here.

const INK := Color("1b1420")
const CREAM := Color("f4ecd2")
const CREAM_SHADE := Color("d6c8a0")
const RED := Color("c8283a")
const BLACK := Color("221f30")
const BACK_BASE := Color("3b3f8c")
const BACK_LIGHT := Color("9aa0e8")
const BACK_DARK := Color("272a66")
const RIM_LIGHT := Color("a07848")
const RIM := Color("74512f")
const RIM_DARK := Color("4b321d")
const BAIZE_EDGE := Color("1f5a3d")
const BAIZE_DARK := Color("266b49")
const BAIZE := Color("2e7d55")
const BAIZE_WEAR := Color("4aa070")
const WARM := Color("ffcf6a")
const WARM_HOT := Color("fff3b8")
const DOOR_LEAF := Color("9fb8aa")
const DOOR_LEAF_DARK := Color("6f8a7c")
const DOOR_FRAME := Color("5a3d26")
const LAMP_SHADE := Color("3c785a")
const LAMP_SHADE_LIGHT := Color("78be96")

## The house look (the Ward's day room seen close: a dark room, the green enamel lamp as the key light, the room's magenta and teal spill at the sides). No dark outlines: an edge is a
## darker step of its own material. Tones step in two or three values with ordered dithering between them (`dither_fill`), never a smooth gradient.
const FELT_DEEP := Color("13261d")
const FELT_DARK := Color("1b3528")
const FELT := Color("244534")
const FELT_LIT := Color("2f5a40")
const FELT_HOT := Color("3b6a4a")
const FELT_LINE := Color("7d8a62")
const WOOD_DEEP := Color("1e130c")
const WOOD_DARK := Color("38231a")
const WOOD := Color("573822")
const WOOD_LIT := Color("80583a")
const WOOD_HOT := Color("a87a4e")
const PAPER := Color("e4dac0")
const PAPER_SHADE := Color("b9ac8c")
const PAPER_EDGE := Color("6b604c")
const CARD_BACK := Color("3a3f6e")
const CARD_BACK_LIGHT := Color("7d82ae")
const CARD_BACK_DARK := Color("252848")
const ENAMEL := Color("2f5f45")
const ENAMEL_LIT := Color("5f9a6e")
const ENAMEL_DARK := Color("1a3326")
const BULB := Color("fff0c0")
const LAMP_LIGHT := Color("ffd890")
const SPILL_L := Color("c45ab8")  # the room's magenta from the left
const SPILL_R := Color("4ab8c8")  # and its teal from the right
## Ordered-dither densities for `dither_fill` (lit cells of 16).
const D_SPARSE := 2
const D_QUARTER := 4
const D_HALF := 8
const D_THREE := 12
const BAYER4 := [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]

const CARD_W := 26.0
const CARD_H := 36.0
const NPC_SCALE := 0.7
const DEALER_SCALE := 0.8
const SEATS := ["npc_a", "dealer", "npc_b"]
const TARGETS := ["bet", "deck", "hand", "exit"]
## The side by side distance of the player's cards in u (a card is 26 wide, so they overlap a little and every rank corner shows).
const PLAYER_SPACING := 22.0
const MIN_TARGET := 72.0

## Pip bitmaps, one string per row, `#` lit. Big pips are 7 wide, small ones 5 wide. Order: spades, hearts, diamonds, clubs.
const PIP_BIG := [
	["...#...", "..###..", ".#####.", "#######", "#######", "...#...", "..###.."],
	[".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#..."],
	["...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#..."],
	["..###..", ".#####.", "..###..", "##.#.##", "#######", "##.#.##", "...#...", "..###.."],
]
const PIP_SMALL := [
	["..#..", ".###.", "#####", "#####", "..#..", ".###."],
	[".#.#.", "#####", "#####", ".###.", "..#.."],
	["..#..", ".###.", "#####", ".###.", "..#.."],
	[".###.", ".###.", "##.##", "#####", "..#..", ".###."],
]

static var _table_cache: Dictionary = {}
static var _cap_cache: Dictionary = {}  # radius -> a limb's round end as triangles (`_cap`)
static var _ell_cache: Dictionary = {}  # [rx, ry, first row, last row] -> an ellipse's rows as triangles, or true once seen (`ell`)
static var _dither_tex: Dictionary = {}  # density -> a 4 x 4 ordered-dither tile (white where lit, clear elsewhere), generated once


# ------------------------------------------------------------------ primitives

## A filled rect from float edges, rounded to whole pixels, at least one pixel in each direction.
static func rect(ci: CanvasItem, x: float, y: float, w: float, h: float, col: Color) -> void:
	var x0 := roundf(x)
	var y0 := roundf(y)
	var x1 := roundf(x + w)
	var y1 := roundf(y + h)
	ci.draw_rect(Rect2(x0, y0, maxf(1.0, x1 - x0), maxf(1.0, y1 - y0)), col)


## A filled pixel ellipse built from rect rows (so it has no ragged edge). `top` and `bottom` clip the rows (offsets from the centre row, defaults: all).
## An ellipse of eight rows or more that is drawn again (a head, an eye, a halo: most shapes come back every redraw) goes to the renderer as one cached triangle list (see `fill`): the same
## pixels in one call instead of a rect per row. One whose size changes every frame (a breathing ring) stays rect rows.
static func ell(ci: CanvasItem, cx: float, cy: float, rx: float, ry: float, col: Color, top := -1000, bottom := 1000) -> void:
	var cxr := roundf(cx)
	var cyr := roundf(cy)
	var ryi := int(maxf(0.0, roundf(ry)))
	var j0 := maxi(-ryi, top)
	var j1 := mini(ryi, bottom)
	if j1 - j0 >= 7:
		var key := [rx, ry, j0, j1]
		var hit: Variant = _ell_cache.get(key)
		if hit is PackedVector2Array:
			fill(ci, Transform2D(0.0, Vector2(cxr, cyr)) * (hit as PackedVector2Array), col)
			return
		if hit != null:  # seen once before: keep it
			var rows := _row_tris(rx, ry, j0, j1)
			_ell_cache[key] = rows
			fill(ci, Transform2D(0.0, Vector2(cxr, cyr)) * rows, col)
			return
		if _ell_cache.size() >= 256:
			_ell_cache.clear()
		_ell_cache[key] = true
	var rr := ry + 0.5
	for j in range(j0, j1 + 1):
		var k := float(j) / rr
		var hw := floorf(rx * sqrt(maxf(0.0, 1.0 - k * k)) + 0.5)
		ci.draw_rect(Rect2(cxr - hw, cyr + j, 2.0 * hw + 1.0, 1.0), col)


## An ellipse with a dark outline `t` pixels thick.
static func ell_o(ci: CanvasItem, cx: float, cy: float, rx: float, ry: float, fill: Color, ink: Color, t := 1.0, top := -1000, bottom := 1000) -> void:
	ell(ci, cx, cy, rx + t, ry + t, ink, top - 1 if top > -1000 else top, bottom)
	ell(ci, cx, cy, rx, ry, fill, top, bottom)


## A filled polygon.
static func poly(ci: CanvasItem, pts: PackedVector2Array, col: Color) -> void:
	ci.draw_colored_polygon(pts, col)


## A filled polygon with an outline `t` pixels thick (the outline is the polygon stamped four times around the fill). The polygon is triangulated once, as the renderer would, and the
## four stamps go as one triangle list, the fill as another.
static func poly_o(ci: CanvasItem, pts: PackedVector2Array, fill_col: Color, ink: Color, t := 1.0) -> void:
	var idx := Geometry2D.triangulate_polygon(pts)
	if idx.is_empty():  # not a simple polygon: drawn as before, stamp by stamp
		for off: Vector2 in [Vector2(t, 0), Vector2(-t, 0), Vector2(0, t), Vector2(0, -t)]:
			ci.draw_colored_polygon(Transform2D(0.0, off) * pts, ink)
		ci.draw_colored_polygon(pts, fill_col)
		return
	var tri := PackedVector2Array()
	tri.resize(idx.size())
	for i in idx.size():
		tri[i] = pts[idx[i]]
	var stamps := PackedVector2Array()
	for off: Vector2 in [Vector2(t, 0), Vector2(-t, 0), Vector2(0, t), Vector2(0, -t)]:
		stamps.append_array(Transform2D(0.0, off) * tri)
	fill(ci, stamps, ink)
	fill(ci, tri, fill_col)


## A thick limb from `a` to `b` (widths `wa`, `wb`) with round ends.
static func limb(ci: CanvasItem, a: Vector2, b: Vector2, wa: float, wb: float, col: Color) -> void:
	var tris := PackedVector2Array()
	limb_into(tris, a, b, wa, wb)
	fill(ci, tris, col)


## Adds a limb to a triangle list (see `fill`): the quad between the ends as two triangles, then each round end's rect rows (the rows `ell` draws) as two triangles each.
static func limb_into(tris: PackedVector2Array, a: Vector2, b: Vector2, wa: float, wb: float) -> void:
	var d := b - a
	if d.length() > 0.5:
		var n := Vector2(-d.y, d.x).normalized()
		var p0 := a + n * wa * 0.5
		var p2 := b - n * wb * 0.5
		tris.append_array(PackedVector2Array([p0, b + n * wb * 0.5, p2, p0, p2, a - n * wa * 0.5]))
	tris.append_array(Transform2D(0.0, Vector2(roundf(a.x), roundf(a.y))) * _cap(maxf(0.5, wa * 0.5 - 0.5)))
	tris.append_array(Transform2D(0.0, Vector2(roundf(b.x), roundf(b.y))) * _cap(maxf(0.5, wb * 0.5 - 0.5)))


## Draws a triangle list in one colour with one call: one polygon command (no triangulation, one set of buffers, one draw call) instead of a polygon and a rect per row for every shape.
## The triangles cover exactly the pixels the shapes cover drawn one by one, so a run of shapes of one opaque colour (an outline pass, a hand's fingers) may share one list.
static func fill(ci: CanvasItem, tris: PackedVector2Array, col: Color) -> void:
	if not tris.is_empty():
		RenderingServer.canvas_item_add_triangle_array(ci.get_canvas_item(), PackedInt32Array(), tris, PackedColorArray([col]))


## A limb's round end of radius `r` (the rows of `ell(0, 0, r, r)`) as triangles, cached per radius (they come in a handful of sizes; the cache is cleared when it grows past 256).
static func _cap(r: float) -> PackedVector2Array:
	var hit: Variant = _cap_cache.get(r)
	if hit != null:
		return hit
	var ri := int(maxf(0.0, roundf(r)))
	var rows := _row_tris(r, r, -ri, ri)
	if _cap_cache.size() >= 256:
		_cap_cache.clear()
	_cap_cache[r] = rows
	return rows


## The rect rows `j0`..`j1` of `ell(0, 0, rx, ry)` as two triangles each.
static func _row_tris(rx: float, ry: float, j0: int, j1: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	out.resize((j1 - j0 + 1) * 6)
	var rr := ry + 0.5
	var i := 0
	for j in range(j0, j1 + 1):
		var k := float(j) / rr
		var hw := floorf(rx * sqrt(maxf(0.0, 1.0 - k * k)) + 0.5)
		var a := Vector2(-hw, j)
		var b := Vector2(hw + 1.0, j)
		var c := Vector2(hw + 1.0, j + 1)
		var d := Vector2(-hw, j + 1)
		out[i] = a
		out[i + 1] = b
		out[i + 2] = c
		out[i + 3] = a
		out[i + 4] = c
		out[i + 5] = d
		i += 6
	return out


## A run of fills drawn as few calls as possible: consecutive fills of one dither density (16 = solid) go to the renderer as one triangle list with per-vertex colours, so the pixels are
## exactly those of the fills drawn one by one, in order. `flush` before drawing anything else on the item (a rect, a line) and at the end.
class Batch:
	var ci: CanvasItem
	var density := -1
	var pts := PackedVector2Array()
	var cols := PackedColorArray()

	func _init(item: CanvasItem = null) -> void:
		ci = item

	func add(tris: PackedVector2Array, col: Color, d := 16) -> void:
		if tris.is_empty() or d <= 0:
			return
		if d != density:
			flush()
			density = d
		var c := PackedColorArray()
		c.resize(tris.size())
		c.fill(col)
		pts.append_array(tris)
		cols.append_array(c)

	## Adds a limb (see `BlackjackDraw.limb`) straight into the run, with no list of its own.
	func add_limb(a: Vector2, b: Vector2, wa: float, wb: float, col: Color, d := 16) -> void:
		if d != density:
			flush()
			density = d
		var n := pts.size()
		BlackjackDraw.limb_into(pts, a, b, wa, wb)
		var c := PackedColorArray()
		c.resize(pts.size() - n)
		c.fill(col)
		cols.append_array(c)

	## Draws what was added since the last flush (or, for a batch made without an item, records it as a run for `BlackjackDraw.draw_runs`).
	func flush() -> void:
		if pts.is_empty():
			return
		if ci == null:
			runs.append([density, pts, cols])
		else:
			BlackjackDraw.draw_run(ci, density, pts, cols)
		pts = PackedVector2Array()
		cols = PackedColorArray()

	var runs: Array = []


## One run of a `Batch`: a triangle list with per-vertex colours, solid (`density` 16) or through the dither tile.
static func draw_run(ci: CanvasItem, density: int, pts: PackedVector2Array, cols: PackedColorArray) -> void:
	var rid := ci.get_canvas_item()
	if density >= 16:
		RenderingServer.canvas_item_add_triangle_array(rid, PackedInt32Array(), pts, cols)
		return
	RenderingServer.canvas_item_set_default_texture_repeat(rid, RenderingServer.CANVAS_ITEM_TEXTURE_REPEAT_ENABLED)
	RenderingServer.canvas_item_set_default_texture_filter(rid, RenderingServer.CANVAS_ITEM_TEXTURE_FILTER_NEAREST)
	var uvs := Transform2D(Vector2(0.25, 0.0), Vector2(0.0, 0.25), Vector2.ZERO) * pts
	RenderingServer.canvas_item_add_triangle_array(rid, PackedInt32Array(), pts, cols, uvs, PackedInt32Array(), PackedFloat32Array(), dither_texture(density).get_rid())


## Draws runs recorded by a `Batch` made without an item (a shape built once and drawn many times).
static func draw_runs(ci: CanvasItem, runs: Array) -> void:
	for r: Array in runs:
		draw_run(ci, int(r[0]), r[1], r[2])


## The part of polygon `a` outside polygon `b`, triangulated (a ring between two nested shapes).
static func ring_tris(a: PackedVector2Array, b: PackedVector2Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	var parts := Geometry2D.clip_polygons(a, b)
	var holed := false
	for i in parts.size():
		for j in parts.size():
			if i != j and Geometry2D.is_point_in_polygon((parts[j] as PackedVector2Array)[0], parts[i]):
				holed = true
	if not holed:
		for p: PackedVector2Array in parts:
			out.append_array(tris_of(p))
		return out
	# a ring round a hole: cut it into bands of rows so that every piece is a simple polygon
	var r := Rect2(a[0], Vector2.ZERO)
	for v in a:
		r = r.expand(v)
	var y := floorf(r.position.y)
	while y < r.end.y:
		var band := PackedVector2Array([Vector2(r.position.x - 1.0, y), Vector2(r.end.x + 1.0, y), Vector2(r.end.x + 1.0, y + 3.0), Vector2(r.position.x - 1.0, y + 3.0)])
		for piece: PackedVector2Array in Geometry2D.intersect_polygons(band, a):
			for q: PackedVector2Array in Geometry2D.clip_polygons(piece, b):
				out.append_array(tris_of(q))
		y += 3.0
	return out


## The 4 x 4 ordered-dither tile with `density` cells of 16 lit (white), the rest clear; generated in code once per density.
static func dither_texture(density: int) -> ImageTexture:
	var hit: Variant = _dither_tex.get(density)
	if hit != null:
		return hit
	var img := Image.create(4, 4, false, Image.FORMAT_RGBA8)
	for i in 16:
		img.set_pixel(i % 4, i / 4, Color(1, 1, 1, 1) if int(BAYER4[i]) < density else Color(1, 1, 1, 0))
	var tex := ImageTexture.create_from_image(img)
	_dither_tex[density] = tex
	return tex


## Draws a triangle list in one colour through the ordered-dither tile of `density` (of 16): the pixel-art way to step between two tones (one call, the pattern locked to the canvas
## item's own pixel grid). Density 16 is a plain `fill`.
static func dither_fill(ci: CanvasItem, tris: PackedVector2Array, col: Color, density := D_HALF) -> void:
	if tris.is_empty() or density <= 0:
		return
	if density >= 16:
		fill(ci, tris, col)
		return
	var rid := ci.get_canvas_item()
	RenderingServer.canvas_item_set_default_texture_repeat(rid, RenderingServer.CANVAS_ITEM_TEXTURE_REPEAT_ENABLED)
	RenderingServer.canvas_item_set_default_texture_filter(rid, RenderingServer.CANVAS_ITEM_TEXTURE_FILTER_NEAREST)
	var uvs := Transform2D(Vector2(0.25, 0.0), Vector2(0.0, 0.25), Vector2.ZERO) * tris
	RenderingServer.canvas_item_add_triangle_array(rid, PackedInt32Array(), tris, PackedColorArray([col]), uvs, PackedInt32Array(), PackedFloat32Array(), dither_texture(density).get_rid())


## A polygon as a triangle list (empty when it is not simple).
static func tris_of(pts: PackedVector2Array) -> PackedVector2Array:
	var idx := Geometry2D.triangulate_polygon(pts)
	var tri := PackedVector2Array()
	tri.resize(idx.size())
	for i in idx.size():
		tri[i] = pts[idx[i]]
	return tri


## The rect rows of `ell(cx, cy, rx, ry)` as a triangle list (for `fill` / `dither_fill`).
static func ell_tris(cx: float, cy: float, rx: float, ry: float, top := -1000, bottom := 1000) -> PackedVector2Array:
	var ryi := int(maxf(0.0, roundf(ry)))
	return Transform2D(0.0, Vector2(roundf(cx), roundf(cy))) * _row_tris(rx, ry, maxi(-ryi, top), mini(ryi, bottom))


## A rect (whole pixels) as two triangles.
static func rect_tris(x: float, y: float, w: float, h: float) -> PackedVector2Array:
	var x0 := roundf(x)
	var y0 := roundf(y)
	var x1 := x0 + maxf(1.0, roundf(x + w) - x0)
	var y1 := y0 + maxf(1.0, roundf(y + h) - y0)
	return PackedVector2Array([Vector2(x0, y0), Vector2(x1, y0), Vector2(x1, y1), Vector2(x0, y0), Vector2(x1, y1), Vector2(x0, y1)])


## The parts of polygon `a` inside polygon `b`, triangulated (a pool of light clipped to the felt).
static func clip_tris(a: PackedVector2Array, b: PackedVector2Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p: PackedVector2Array in Geometry2D.intersect_polygons(a, b):
		out.append_array(tris_of(p))
	return out


## An ellipse outline as a polygon of `n` points (rounded to whole pixels).
static func ell_points(cx: float, cy: float, rx: float, ry: float, n := 40) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		var th := TAU * float(i) / float(n)
		pts.append(Vector2(roundf(cx + cos(th) * rx), roundf(cy + sin(th) * ry)))
	return pts


static func shade(c: Color, alpha: float) -> Color:
	return Color(c.r, c.g, c.b, c.a * alpha)


## Draws a bitmap given as strings (`#` lit) with its top-left at `pos`, each lit cell `m` pixels.
static func bitmap(ci: CanvasItem, rows: Array, pos: Vector2, m: float, col: Color) -> void:
	var px := roundf(pos.x)
	var py := roundf(pos.y)
	for r in rows.size():
		var row: String = rows[r]
		var c := 0
		while c < row.length():
			if row[c] != "#":
				c += 1
				continue
			var s := c
			while c < row.length() and row[c] == "#":
				c += 1
			ci.draw_rect(Rect2(px + s * m, py + r * m, (c - s) * m, m), col)


# ------------------------------------------------------------------ cards

## The pixel size of a card at `u` (and `scale`: 1 for the player's own cards, `NPC_SCALE` / `DEALER_SCALE` far side).
static func card_size(u: float, scale := 1.0) -> Vector2:
	return Vector2(maxf(9.0, roundf(CARD_W * u * scale)), maxf(12.0, roundf(CARD_H * u * scale)))


## The pixel size of one cell of the rank font on a card at this `u` and `scale`.
static func rank_cell(u: float, scale := 1.0) -> float:
	return maxf(1.0, roundf(1.5 * u * scale))


## The width in pixels of the widest rank corner ("10") at this `u` and `scale`: every card of a fan must show at least this much of its left edge.
static func rank_corner_width(u: float, scale := 1.0) -> float:
	return PixelGlyphs.text_width("10", rank_cell(u, scale)) + maxf(1.0, roundf(2.0 * u * scale))


static func rank_text(rank: int) -> String:
	match rank:
		1:
			return "A"
		11:
			return "J"
		12:
			return "Q"
		13:
			return "K"
	return str(clampi(rank, 2, 10))


static func suit_color(suit: int) -> Color:
	return RED if suit == 1 or suit == 2 else BLACK


## Draws one card centred on `center`. `card` is `{"rank": 1..13, "suit": 0..3}` (spades, hearts, diamonds, clubs).
## Turn-over convention: `flip` is the animation progress of a turn-over with 1.0 meaning at rest. The card is squashed to `abs(cos(PI * flip))` of its width; while `flip` < 0.5 the
## side NOT given by `face_up` shows, from 0.5 on the side `face_up` names. So to turn a card from back to face the caller passes `face_up = true` and eases `flip` 0 to 1; to turn it face down,
## `face_up = false` and 0 to 1 too. A resting card is `flip = 1.0`. `angle` is radians, `alpha` fades it, `scale` shrinks it for the far side of the table.
static func draw_card(ci: CanvasItem, card: Dictionary, center: Vector2, u: float, face_up: bool, flip := 1.0, angle := 0.0, alpha := 1.0, scale := 1.0) -> void:
	var sx := absf(cos(PI * clampf(flip, 0.0, 1.0)))
	var showing_face := face_up if flip >= 0.5 else not face_up
	var sz := card_size(u, scale)
	var w := sz.x
	var h := sz.y
	var c := Vector2(roundf(center.x), roundf(center.y))
	ci.draw_set_transform(c, angle, Vector2(maxf(sx, 0.05), 1.0))
	var x := -floorf(w * 0.5)
	var y := -floorf(h * 0.5)
	# its shadow on the felt, the paper's darker edge (no ink line), a step of shade along the bottom and the far side, the lamp-lit face (corners cut by one pixel for a rounded card)
	ci.draw_rect(Rect2(x + 1, y + 2, w, h), shade(FELT_DEEP, 0.75 * alpha))
	_round_rect(ci, x, y, w, h, shade(PAPER_EDGE, alpha))
	_round_rect(ci, x + 1, y + 1, w - 2, h - 2, shade(PAPER_SHADE, alpha))
	ci.draw_rect(Rect2(x + 1, y + 1, w - 3, h - 3), shade(PAPER, alpha))
	if showing_face:
		_card_face(ci, card, x, y, w, h, u, scale, alpha)
	else:
		_card_back(ci, x, y, w, h, alpha)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


static func _round_rect(ci: CanvasItem, x: float, y: float, w: float, h: float, col: Color) -> void:
	ci.draw_rect(Rect2(x + 1, y, w - 2, h), col)
	ci.draw_rect(Rect2(x, y + 1, w, h - 2), col)


static func _card_face(ci: CanvasItem, card: Dictionary, x: float, y: float, w: float, h: float, u: float, scale: float, alpha: float) -> void:
	var rank: int = int(card.get("rank", 1))
	var suit: int = clampi(int(card.get("suit", 0)), 0, 3)
	var col := shade(suit_color(suit), alpha)
	var k := rank_cell(u, scale)
	var pad := maxf(2.0, roundf(2.0 * u * scale))
	PixelGlyphs.draw_text(ci, rank_text(rank), Vector2(x + pad, y + pad), k, col)
	var big: Array = PIP_BIG[suit]
	var small: Array = PIP_SMALL[suit]
	if h >= 22.0:
		var sw := PixelGlyphs.text_width("0", k)
		bitmap(ci, small, Vector2(x + pad + floorf((sw - 5.0) * 0.5), y + pad + 5.0 * k + 2.0), 1.0, col)
	var m := maxf(1.0, roundf(1.8 * u * scale))
	var bw := 7.0 * m
	var bh := big.size() * m
	var cx := x + w * 0.5 + (2.0 if w >= 20.0 else 1.0)
	var cy := y + h * 0.5 + (2.0 if w >= 20.0 else 3.0)
	if rank >= 11:  # court cards get a coloured frame so they read apart from the number cards
		var fx := x + w * 0.28
		var fy := y + h * 0.2
		ci.draw_rect(Rect2(roundf(fx), roundf(fy), roundf(w * 0.62), 1), col)
		ci.draw_rect(Rect2(roundf(fx), roundf(y + h * 0.88), roundf(w * 0.62), 1), col)
	bitmap(ci, big, Vector2(cx - floorf(bw * 0.5), cy - floorf(bh * 0.5)), m, col)


static func _card_back(ci: CanvasItem, x: float, y: float, w: float, h: float, alpha: float) -> void:
	ci.draw_rect(Rect2(x + 2, y + 2, w - 4, h - 4), shade(CARD_BACK, alpha))
	ci.draw_rect(Rect2(x + 3, y + 3, w - 6, 1), shade(CARD_BACK_LIGHT, alpha))
	ci.draw_rect(Rect2(x + 3, y + h - 4, w - 6, 1), shade(CARD_BACK_DARK, alpha))
	ci.draw_rect(Rect2(x + 3, y + 3, 1, h - 6), shade(CARD_BACK_LIGHT, alpha))
	ci.draw_rect(Rect2(x + w - 4, y + 3, 1, h - 6), shade(CARD_BACK_DARK, alpha))
	var cx := x + floorf(w * 0.5)
	var cy := y + floorf(h * 0.5)
	var rx := floorf(w * 0.3)
	var ry := floorf(h * 0.3)
	var dia := PackedVector2Array([Vector2(cx, cy - ry), Vector2(cx + rx + 1, cy), Vector2(cx, cy + ry + 1), Vector2(cx - rx, cy)])
	ci.draw_colored_polygon(dia, shade(CARD_BACK_LIGHT, alpha))
	var rx2 := maxf(1.0, floorf(rx * 0.55))
	var ry2 := maxf(1.0, floorf(ry * 0.55))
	var dia2 := PackedVector2Array([Vector2(cx, cy - ry2), Vector2(cx + rx2 + 1, cy), Vector2(cx, cy + ry2 + 1), Vector2(cx - rx2, cy)])
	ci.draw_colored_polygon(dia2, shade(CARD_BACK_DARK, alpha))
	ci.draw_rect(Rect2(cx, cy, 1, 1), shade(CARD_BACK_LIGHT, alpha))


## A stack of cards seen from above with visible thickness (`count` cards), back pattern on top. `center` is the middle of the top card.
static func draw_deck(ci: CanvasItem, center: Vector2, u: float, count := 30) -> void:
	var sz := card_size(u)
	var t := clampf(roundf(float(count) / 6.0 * u), 1.0, 9.0 * maxf(u, 1.0))
	var x := roundf(center.x) - floorf(sz.x * 0.5)
	var y := roundf(center.y) - floorf(sz.y * 0.5)
	ci.draw_rect(Rect2(x + 2, y + 2 + t, sz.x, sz.y), shade(FELT_DEEP, 0.8))
	_round_rect(ci, x, y + t, sz.x, sz.y, PAPER_EDGE)
	for i in int(t):  # the edges of the stacked cards, lit from above, darker toward the felt
		ci.draw_rect(Rect2(x + 1, y + sz.y - 1 + i, sz.x - 2, 1), PAPER_SHADE if i % 2 == 0 else PAPER_EDGE.lerp(PAPER_SHADE, 0.5))
	_round_rect(ci, x, y, sz.x, sz.y, PAPER_EDGE)
	_round_rect(ci, x + 1, y + 1, sz.x - 2, sz.y - 2, PAPER)
	_card_back(ci, x, y, sz.x, sz.y, 1.0)


# ------------------------------------------------------------------ geometry

static func unit(size: Vector2) -> float:
	return size.y / 230.0


static func _seat_x(seat: String, size: Vector2) -> float:
	match seat:
		"npc_a":
			return size.x * 0.2
		"npc_b":
			return size.x * 0.8
	return size.x * 0.5


## Where the head centre of the person in `seat` sits (`npc_a` left, `dealer` centre, `npc_b` right). Pass this to `BlackjackPeople.draw_person` as `center`.
static func seat_pos(seat: String, size: Vector2) -> Vector2:
	var u := unit(size)
	return Vector2(roundf(_seat_x(seat, size)), roundf((56.0 if seat == "dealer" else 63.0) * u))


## The scale of a card in front of `seat` (1 for the player).
static func seat_card_scale(seat: String) -> float:
	match seat:
		"dealer":
			return DEALER_SCALE
		"npc_a", "npc_b":
			return NPC_SCALE
	return 1.0


## Where card `index` (0 based) of `seat` lies: `"player"` is bottom centre, large and overlapping to the right; the others sit in front of each person, smaller.
static func card_spot(seat: String, index: int, size: Vector2) -> Vector2:
	var u := unit(size)
	var cx := size.x * 0.5
	match seat:
		"player":
			var dx := -11.0 if index == 0 else 11.0 + (index - 1) * PLAYER_SPACING
			return Vector2(roundf(cx + dx * u), roundf(190.0 * u))
		"dealer":
			return Vector2(roundf(cx + (-18.0 + index * 13.0) * u), roundf(131.0 * u))
	var sp := seat_pos(seat, size)
	return Vector2(roundf(sp.x + (-18.0 + index * 13.0) * u), roundf(sp.y + 63.0 * u))


static func deck_spot(size: Vector2) -> Vector2:
	var u := unit(size)
	return Vector2(roundf(size.x * 0.5 + 74.0 * u), roundf(112.0 * u))


## The bet spot: a ring on the baize between the player's money and the dealer, above the pile and left of the player's cards (inside the picture's middle, which the falling notes cross least).
static func bet_spot(size: Vector2) -> Vector2:
	var u := unit(size)
	return Vector2(roundf(size.x * 0.5 - 88.0 * u), roundf(124.0 * u))


## The centre of the first £5 note of the player's money pile (`MoneyDraw.pile_layout` origin): twenties lie to its left, coins to its right, more fivers below it toward the player.
## It sits at 0.23 of the width, in the gap between the first two pads' lanes of falling notes, so the fivers you touch are crossed by the notes as little as possible.
static func pile_origin(size: Vector2) -> Vector2:
	var u := unit(size)
	return Vector2(roundf(size.x * 0.23), roundf(154.0 * u))


## The rectangle the money pile may occupy (bottom left, under the bet spot, left of the player's cards).
static func pile_rect(size: Vector2) -> Rect2:
	var u := unit(size)
	return Rect2(0.0, 140.0 * u, size.x * 0.5 - 52.0 * u, 90.0 * u)


## Off the bottom edge: where the player's money comes from and goes back to.
static func pockets_spot(size: Vector2) -> Vector2:
	var u := unit(size)
	return Vector2(roundf(size.x * 0.5 - 70.0 * u), roundf(size.y + 20.0 * u))


## Where the dealer keeps and collects money.
static func dealer_tray_spot(size: Vector2) -> Vector2:
	var u := unit(size)
	return Vector2(roundf(size.x * 0.5 - 52.0 * u), roundf(114.0 * u))


static func exit_rect(size: Vector2) -> Rect2:
	var u := unit(size)
	return Rect2(roundf(size.x - 76.0 * u), roundf(40.0 * u), roundf(76.0 * u), roundf(90.0 * u))


## The touch rectangle of `id` (`bet`, `deck`, `hand`, `exit`): at least 72 u in both directions (about 78 px on an 844 x 390 phone), never overlapping another one.
## `card_count` widens the hand's rect over a longer fan.
static func target_rect(id: String, size: Vector2, card_count := 2) -> Rect2:
	var u := unit(size)
	var m := MIN_TARGET * u
	match id:
		"bet":
			var c := bet_spot(size)
			return Rect2(c.x - m * 0.5, c.y - m * 0.5, m, m)
		"deck":
			var c := deck_spot(size)
			return Rect2(c.x - m * 0.5, c.y - m * 0.5, m, m)
		"hand":
			var n := maxi(card_count, 2)
			var x0 := card_spot("player", 0, size).x - CARD_W * 0.5 * u
			var x1 := card_spot("player", n - 1, size).x + CARD_W * 0.5 * u
			var pad := 24.0 * u
			var cy := 190.0 * u
			return Rect2(x0 - pad, cy - m * 0.5, x1 - x0 + 2.0 * pad, m)
	return exit_rect(size)


## The y of the table's far edge at canvas x (the table is a rounded wide shape seen from a seated player).
static func table_edge_y(size: Vector2, x: float) -> float:
	var u := unit(size)
	var rx := size.x * 0.5 + 34.0 * u
	var t := minf(0.999, absf(x - size.x * 0.5) / rx)
	return 236.0 * u - 128.0 * u * pow(maxf(0.0, 1.0 - t * t * t), 1.0 / 3.0)


# ------------------------------------------------------------------ table, chair, door

static func _super_points(cx: float, cy: float, rx: float, ry: float, n: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(n + 1):
		var th := PI + PI * float(i) / float(n)
		var c := cos(th)
		var s := sin(th)
		var x := cx + rx * signf(c) * pow(absf(c), 2.0 / 3.0)
		var y := cy + ry * signf(s) * pow(absf(s), 2.0 / 3.0)
		pts.append(Vector2(roundf(x), roundf(y)))
	return pts


static func _table_shapes(size: Vector2) -> Dictionary:
	var hit: Variant = _table_cache.get(size)
	if hit != null:
		return hit
	var u := unit(size)
	var cx := size.x * 0.5
	var cy := 236.0 * u
	var rx := size.x * 0.5 + 34.0 * u
	var ry := 128.0 * u
	var rim := _super_points(cx, cy, rx, ry, 56)
	var baize := _super_points(cx, cy + 4.0 * u, rx - 8.0 * u, ry - 7.0 * u, 56)
	# the lamp's pool on the felt: nested ellipses round the point under the shade, each clipped to the felt, stepped by dithering (outermost first)
	var pc := Vector2(cx, 156.0 * u)
	# the near edge, away from the lamp, falls into the dark; the room's spill tints the far corners
	var near := PackedVector2Array()
	near.append_array(clip_tris(rect_points(0.0, 204.0 * u, size.x, 40.0 * u), baize))
	var nearer := clip_tris(rect_points(0.0, 218.0 * u, size.x, 30.0 * u), baize)
	var d := {
		"ink": _super_points(cx, cy + 1.0, rx + 1.0, ry + 1.0, 56),
		"rim": rim,
		"rim_low": _super_points(cx, cy + maxf(1.0, roundf(2.0 * u)), rx, ry, 56),
		"rim_glint": clip_tris(ell_points(cx, 112.0 * u, 150.0 * u, 9.0 * u, 40), rim),
		"edge": _super_points(cx, cy + 3.0 * u, rx - 6.0 * u, ry - 5.0 * u, 56),
		"baize": baize,
		"near": near,
		"nearer": nearer,
		"spill_l": clip_tris(ell_points(-20.0 * u, 168.0 * u, 120.0 * u, 70.0 * u), baize),
		"spill_r": clip_tris(ell_points(size.x + 20.0 * u, 168.0 * u, 120.0 * u, 70.0 * u), baize),
		"shadow_far": _super_points(cx, cy + 2.0 * u, rx + 10.0 * u, ry + 9.0 * u, 40),
		"shadow_near": _super_points(cx, cy + 2.0 * u, rx + 4.0 * u, ry + 4.0 * u, 40),
	}
	d["shadow_far_tris"] = tris_of(d["shadow_far"])
	# the table as recorded runs (solid planes, then the dithered steps densest first): the pool's steps as rings between its nested ellipses, so the solid planes and the
	# dithered seams each go to the renderer in one call
	var b := Batch.new()
	b.add(tris_of(d["ink"]), WOOD_DEEP)
	b.add(tris_of(rim), WOOD_LIT)
	b.add(tris_of(d["rim_low"]), WOOD)
	b.add(tris_of(d["edge"]), FELT_DEEP)
	b.add(tris_of(baize), FELT_DARK)
	var e := func(rxu: float, ryu: float) -> PackedVector2Array: return ell_points(pc.x, pc.y, rxu * u, ryu * u, 48)
	var felt_in := Geometry2D.intersect_polygons(e.call(252.0, 68.0), baize)
	var lit_in := Geometry2D.intersect_polygons(e.call(158.0, 42.0), baize)
	for q: PackedVector2Array in felt_in:
		b.add(tris_of(q), FELT)
	for q: PackedVector2Array in lit_in:
		b.add(tris_of(q), FELT_LIT)
	var w := size.x
	b.add(rect_tris(w * 0.47, 206.0 * u, 10.0 * u, maxf(1.0, u)), FELT_DEEP)
	b.add(rect_tris(w * 0.74, 142.0 * u, 2.0 * u, 2.0 * u), FELT_DARK)
	b.add(ell_tris(w * 0.78, 176.0 * u, 7.0 * u, 3.5 * u), FELT_DARK)
	b.add(ell_tris(w * 0.78, 176.0 * u, 5.0 * u, 2.0 * u), FELT)
	for q: PackedVector2Array in Geometry2D.intersect_polygons(e.call(300.0, 84.0), baize):
		for f: PackedVector2Array in felt_in:
			b.add(ring_tris(q, f), FELT, D_HALF)
	for q: PackedVector2Array in Geometry2D.intersect_polygons(e.call(200.0, 54.0), baize):
		for f: PackedVector2Array in lit_in:
			b.add(ring_tris(q, f), FELT_LIT, D_HALF)
	b.add(tris_of(e.call(80.0, 21.0)), FELT_HOT, D_HALF)
	b.add(d["rim_glint"], WOOD_HOT, D_HALF)
	b.add(rect_tris(w * 0.28, 150.0 * u, 16.0 * u, 3.0 * u), FELT_HOT, D_HALF)
	b.add(rect_tris(w * 0.62, 168.0 * u, 20.0 * u, 3.0 * u), FELT_LIT, D_HALF)
	b.add(rect_tris(w * 0.16, 190.0 * u, 4.0 * u, 3.0 * u), FELT_LIT, D_HALF)
	b.add(nearer, FELT_DEEP, D_HALF)
	b.add(ring_tris(e.call(112.0, 30.0), e.call(80.0, 21.0)), FELT_HOT, D_QUARTER)
	b.add(near, FELT_DEEP, D_QUARTER)
	b.add(d["spill_l"], shade(SPILL_L, 0.4 if u >= 0.75 else 0.25), D_SPARSE)
	b.add(d["spill_r"], shade(SPILL_R, 0.4 if u >= 0.75 else 0.25), D_SPARSE)
	b.flush()
	d["runs"] = b.runs
	if _table_cache.size() > 6:
		_table_cache.clear()
	_table_cache[size] = d
	return d


static func rect_points(x: float, y: float, w: float, h: float) -> PackedVector2Array:
	return PackedVector2Array([Vector2(x, y), Vector2(x + w, y), Vector2(x + w, y + h), Vector2(x, y + h)])


## The ward day-room table: a worn green felt top in a wooden rim, wide and shallow, far edge higher than the near one. Lit only by the lamp over it: a pool of light on the felt round the
## point under the shade, stepped by dithering, the near edge falling into the dark, the room's magenta and teal spill on the far corners.
static func draw_table(ci: CanvasItem, size: Vector2, u: float) -> void:
	draw_runs(ci, _table_shapes(size)["runs"])


## The table's shadow on the room round its far edge (drawn before the people, who cover most of it): it grounds the close-up where the rim meets the live room at the sides.
static func draw_table_shadow(ci: CanvasItem, size: Vector2, u: float) -> void:
	var s := _table_shapes(size)
	dither_fill(ci, s["shadow_far_tris"], shade(WOOD_DEEP, 0.8), D_HALF)
	poly(ci, s["shadow_near"], shade(WOOD_DEEP, 0.45))


## The lamp over the table, the same green enamel lamp the day room shows from across the room: `part` "cone" draws the shade at the top of the picture and the haze in its beam
## (before the table), "pool" the warmth of the bulb on the felt right under it (after the table; the stepped pool itself is part of `draw_table`).
static func draw_lamp(ci: CanvasItem, size: Vector2, u: float, part: String) -> void:
	var cx := roundf(size.x * 0.5)
	if part == "pool":
		dither_fill(ci, ell_tris(cx, 150.0 * u, 60.0 * u, 14.0 * u), shade(LAMP_LIGHT, 0.35), D_SPARSE)
		return
	var t := maxf(1.0, roundf(u))
	# haze in the beam: a sparse dither, denser toward the bulb (at low detail only the denser core, the sparse pixels would be as big as a face's features)
	if u >= 0.75:
		dither_fill(ci, tris_of(PackedVector2Array([Vector2(cx - 20.0 * u, 15.0 * u), Vector2(cx + 20.0 * u, 15.0 * u), Vector2(cx + 150.0 * u, 118.0 * u), Vector2(cx - 150.0 * u, 118.0 * u)])), shade(LAMP_LIGHT, 0.12), D_SPARSE)
	dither_fill(ci, tris_of(PackedVector2Array([Vector2(cx - 17.0 * u, 15.0 * u), Vector2(cx + 17.0 * u, 15.0 * u), Vector2(cx + 60.0 * u, 50.0 * u), Vector2(cx - 60.0 * u, 50.0 * u)])), shade(LAMP_LIGHT, 0.14), D_QUARTER)
	rect(ci, cx - t * 0.5, 0.0, t, 6.0 * u, WOOD_DEEP)
	var shade_pts := PackedVector2Array([Vector2(roundf(cx - 6.0 * u), roundf(5.0 * u)), Vector2(roundf(cx + 6.0 * u), roundf(5.0 * u)), Vector2(roundf(cx + 21.0 * u), roundf(14.0 * u)), Vector2(roundf(cx - 21.0 * u), roundf(14.0 * u))])
	poly_o(ci, shade_pts, ENAMEL, ENAMEL_DARK, t)
	dither_fill(ci, tris_of(PackedVector2Array([Vector2(roundf(cx - 5.0 * u), roundf(5.0 * u)), Vector2(roundf(cx + 1.0 * u), roundf(5.0 * u)), Vector2(roundf(cx - 4.0 * u), roundf(14.0 * u)), Vector2(roundf(cx - 17.0 * u), roundf(14.0 * u))])), ENAMEL_LIT, D_HALF)
	rect(ci, cx - 5.0 * u, 5.0 * u, 10.0 * u, t, ENAMEL_LIT)
	rect(ci, cx - 21.0 * u, 14.0 * u, 42.0 * u, t, ENAMEL_DARK)
	ell(ci, cx, 15.0 * u + t, 6.0 * u, 2.0 * u, BULB, 0, 1000)


## The bet spot: an oval painted on the felt where the stake goes, worn and faint, `pu` the money's unit (so the ring holds a note).
static func draw_bet_ring(ci: CanvasItem, c: Vector2, pu: float) -> void:
	var rx := 28.0 * pu
	var ry := 16.0 * pu
	var pts := PackedVector2Array()
	for i in 29:
		var th := TAU * float(i) / 28.0
		pts.append(Vector2(roundf(c.x + cos(th) * rx), roundf(c.y + sin(th) * ry)))
	dither_fill(ci, ell_tris(c.x, c.y, rx, ry), FELT_DEEP, D_QUARTER)
	ci.draw_polyline(pts, shade(FELT_LINE, 0.6), maxf(1.0, roundf(pu * 0.8)))


## A hint of the player's own chair at the very bottom corners (optional).
static func draw_chair_back(ci: CanvasItem, size: Vector2, u: float) -> void:
	var y := size.y - 9.0 * u
	for sx: float in [0.0, 1.0]:
		var x0: float = 0.0 if sx == 0.0 else size.x - 22.0 * u
		poly_o(ci, PackedVector2Array([
			Vector2(roundf(x0), roundf(y)), Vector2(roundf(x0 + 22.0 * u), roundf(y)),
			Vector2(roundf(x0 + 22.0 * u), roundf(size.y)), Vector2(roundf(x0), roundf(size.y)),
		]), WOOD_DARK, WOOD_DEEP, maxf(1.0, roundf(u)))
		rect(ci, x0 + 2.0 * u, y, 18.0 * u, maxf(1.0, u), WOOD)


## The exit: a door standing ajar at the right edge with a slit of warm light spilling on the floor. `beat_phase` is continuous beats (only the fraction matters), pulse peaks on the beat;
## `urged` makes the slit wider and brighter and the leaf swing.
static func draw_exit(ci: CanvasItem, size: Vector2, u: float, beat_phase: float, urged: bool) -> void:
	var r := exit_rect(size)
	var pulse := 0.5 + 0.5 * cos(TAU * beat_phase)
	pulse *= pulse
	var fx := r.position.x + 30.0 * u
	var fw := 40.0 * u
	var ft := r.position.y + 6.0 * u
	var fb := ft + 78.0 * u
	var slit := ((15.0 + 8.0 * pulse) if urged else (8.0 + 4.0 * pulse)) * u
	var glow := (0.9 if urged else 0.6) + 0.4 * pulse
	var lit := WARM.lerp(WARM_HOT, clampf(glow - 0.5, 0.0, 1.0))
	# spill on the floor
	var a := (0.5 if urged else 0.34) * (0.6 + 0.5 * pulse)
	poly(ci, PackedVector2Array([
		Vector2(roundf(fx), roundf(fb - 2.0 * u)), Vector2(roundf(fx + slit + 2.0 * u), roundf(fb - 2.0 * u)),
		Vector2(roundf(fx - 46.0 * u), roundf(fb + 30.0 * u)), Vector2(roundf(fx - 84.0 * u), roundf(fb + 30.0 * u)),
	]), shade(lit, a))
	# frame, light, leaf
	var t := maxf(1.0, roundf(u))
	rect(ci, fx - 3.0 * u - t, ft - 3.0 * u - t, fw + 6.0 * u + 2.0 * t, fb - ft + 3.0 * u + t, INK)
	rect(ci, fx - 3.0 * u, ft - 3.0 * u, fw + 6.0 * u, fb - ft + 3.0 * u, DOOR_FRAME)
	rect(ci, fx, ft, fw, fb - ft, lit)
	var lx := fx + slit
	var leaf := PackedVector2Array([
		Vector2(roundf(lx), roundf(ft + 3.0 * u)), Vector2(roundf(fx + fw), roundf(ft)),
		Vector2(roundf(fx + fw), roundf(fb)), Vector2(roundf(lx), roundf(fb - 3.0 * u)),
	])
	poly_o(ci, leaf, DOOR_LEAF, INK, t)
	rect(ci, lx + 1.0, ft + 4.0 * u, maxf(1.0, 2.0 * u), fb - ft - 8.0 * u, DOOR_LEAF_DARK)
	rect(ci, lx + (fx + fw - lx) * 0.35, ft + 12.0 * u, (fx + fw - lx) * 0.45, 22.0 * u, DOOR_LEAF_DARK)
	rect(ci, lx + (fx + fw - lx) * 0.38, ft + 14.0 * u, (fx + fw - lx) * 0.39, 18.0 * u, DOOR_LEAF)
	rect(ci, lx + 3.0 * u, ft + 44.0 * u, 3.0 * u, 3.0 * u, WARM_HOT)
	if urged:  # rays leaning out of the gap
		for i in 3:
			var ry := ft + (14.0 + 24.0 * i) * u
			poly(ci, PackedVector2Array([
				Vector2(roundf(fx), roundf(ry)), Vector2(roundf(fx - (18.0 + 14.0 * pulse) * u), roundf(ry + 4.0 * u)),
				Vector2(roundf(fx - (18.0 + 14.0 * pulse) * u), roundf(ry + 7.0 * u)), Vector2(roundf(fx), roundf(ry + 3.0 * u)),
			]), shade(WARM_HOT, 0.45 + 0.3 * pulse))
