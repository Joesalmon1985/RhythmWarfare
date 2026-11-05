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


# ------------------------------------------------------------------ primitives

## A filled rect from float edges, rounded to whole pixels, at least one pixel in each direction.
static func rect(ci: CanvasItem, x: float, y: float, w: float, h: float, col: Color) -> void:
	var x0 := roundf(x)
	var y0 := roundf(y)
	var x1 := roundf(x + w)
	var y1 := roundf(y + h)
	ci.draw_rect(Rect2(x0, y0, maxf(1.0, x1 - x0), maxf(1.0, y1 - y0)), col)


## A filled pixel ellipse built from rect rows (so it has no ragged edge). `top` and `bottom` clip the rows (offsets from the centre row, defaults: all).
static func ell(ci: CanvasItem, cx: float, cy: float, rx: float, ry: float, col: Color, top := -1000, bottom := 1000) -> void:
	var cxr := roundf(cx)
	var cyr := roundf(cy)
	var ryi := int(maxf(0.0, roundf(ry)))
	var rr := ry + 0.5
	for j in range(maxi(-ryi, top), mini(ryi, bottom) + 1):
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


## A filled polygon with an outline `t` pixels thick (the outline is the polygon stamped four times around the fill).
static func poly_o(ci: CanvasItem, pts: PackedVector2Array, fill: Color, ink: Color, t := 1.0) -> void:
	for off: Vector2 in [Vector2(t, 0), Vector2(-t, 0), Vector2(0, t), Vector2(0, -t)]:
		var moved := PackedVector2Array()
		moved.resize(pts.size())
		for i in pts.size():
			moved[i] = pts[i] + off
		ci.draw_colored_polygon(moved, ink)
	ci.draw_colored_polygon(pts, fill)


## A thick limb from `a` to `b` (widths `wa`, `wb`) with round ends.
static func limb(ci: CanvasItem, a: Vector2, b: Vector2, wa: float, wb: float, col: Color) -> void:
	var d := b - a
	if d.length() > 0.5:
		var n := Vector2(-d.y, d.x).normalized()
		ci.draw_colored_polygon(PackedVector2Array([a + n * wa * 0.5, b + n * wb * 0.5, b - n * wb * 0.5, a - n * wa * 0.5]), col)
	ell(ci, a.x, a.y, maxf(0.5, wa * 0.5 - 0.5), maxf(0.5, wa * 0.5 - 0.5), col)
	ell(ci, b.x, b.y, maxf(0.5, wb * 0.5 - 0.5), maxf(0.5, wb * 0.5 - 0.5), col)


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
	# shadow, outline, body (corners cut by one pixel for a rounded card)
	var sh := shade(INK, 0.28 * alpha)
	ci.draw_rect(Rect2(x + 1, y + 2, w, h), sh)
	_round_rect(ci, x, y, w, h, shade(INK, alpha))
	if showing_face:
		_round_rect(ci, x + 1, y + 1, w - 2, h - 2, shade(CREAM, alpha))
		_card_face(ci, card, x, y, w, h, u, scale, alpha)
	else:
		_round_rect(ci, x + 1, y + 1, w - 2, h - 2, shade(CREAM, alpha))
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
	ci.draw_rect(Rect2(x + 2, y + 2, w - 4, h - 4), shade(BACK_BASE, alpha))
	ci.draw_rect(Rect2(x + 3, y + 3, w - 6, 1), shade(BACK_LIGHT, alpha))
	ci.draw_rect(Rect2(x + 3, y + h - 4, w - 6, 1), shade(BACK_LIGHT, alpha))
	ci.draw_rect(Rect2(x + 3, y + 3, 1, h - 6), shade(BACK_LIGHT, alpha))
	ci.draw_rect(Rect2(x + w - 4, y + 3, 1, h - 6), shade(BACK_LIGHT, alpha))
	var cx := x + floorf(w * 0.5)
	var cy := y + floorf(h * 0.5)
	var rx := floorf(w * 0.3)
	var ry := floorf(h * 0.3)
	var dia := PackedVector2Array([Vector2(cx, cy - ry), Vector2(cx + rx + 1, cy), Vector2(cx, cy + ry + 1), Vector2(cx - rx, cy)])
	ci.draw_colored_polygon(dia, shade(BACK_LIGHT, alpha))
	var rx2 := maxf(1.0, floorf(rx * 0.55))
	var ry2 := maxf(1.0, floorf(ry * 0.55))
	var dia2 := PackedVector2Array([Vector2(cx, cy - ry2), Vector2(cx + rx2 + 1, cy), Vector2(cx, cy + ry2 + 1), Vector2(cx - rx2, cy)])
	ci.draw_colored_polygon(dia2, shade(BACK_DARK, alpha))
	ci.draw_rect(Rect2(cx, cy, 1, 1), shade(BACK_LIGHT, alpha))


## A stack of cards seen from above with visible thickness (`count` cards), back pattern on top. `center` is the middle of the top card.
static func draw_deck(ci: CanvasItem, center: Vector2, u: float, count := 30) -> void:
	var sz := card_size(u)
	var t := clampf(roundf(float(count) / 6.0 * u), 1.0, 9.0 * maxf(u, 1.0))
	var x := roundf(center.x) - floorf(sz.x * 0.5)
	var y := roundf(center.y) - floorf(sz.y * 0.5)
	ci.draw_rect(Rect2(x + 2, y + 2 + t, sz.x, sz.y), shade(INK, 0.3))
	_round_rect(ci, x, y + t, sz.x, sz.y, INK)
	for i in int(t):
		ci.draw_rect(Rect2(x + 1, y + sz.y - 1 + i, sz.x - 2, 1), CREAM if i % 2 == 0 else CREAM_SHADE)
	_round_rect(ci, x, y, sz.x, sz.y, INK)
	_round_rect(ci, x + 1, y + 1, sz.x - 2, sz.y - 2, CREAM)
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
	var d := {
		"ink": _super_points(cx, cy + 1.0, rx + 1.0, ry + 1.0, 56),
		"rim": _super_points(cx, cy, rx, ry, 56),
		"rim_low": _super_points(cx, cy + maxf(1.0, roundf(2.0 * u)), rx, ry, 56),
		"edge": _super_points(cx, cy + 3.0 * u, rx - 6.0 * u, ry - 5.0 * u, 56),
		"baize": _super_points(cx, cy + 4.0 * u, rx - 8.0 * u, ry - 7.0 * u, 56),
		"mid": _super_points(cx, cy + 10.0 * u, rx * 0.84, ry * 0.8, 48),
		"glow": _super_points(cx, cy + 40.0 * u, rx * 0.56, ry * 0.5, 40),
		"shadow_far": _super_points(cx, cy + 2.0 * u, rx + 10.0 * u, ry + 9.0 * u, 40),
		"shadow_near": _super_points(cx, cy + 2.0 * u, rx + 4.0 * u, ry + 4.0 * u, 40),
	}
	if _table_cache.size() > 6:
		_table_cache.clear()
	_table_cache[size] = d
	return d


## The ward day-room table: a worn green baize top with a wooden rim, wide and shallow, far edge higher than the near one, fading into the bottom of the picture.
static func draw_table(ci: CanvasItem, size: Vector2, u: float) -> void:
	var s := _table_shapes(size)
	poly(ci, s["ink"], INK)
	poly(ci, s["rim"], RIM_LIGHT)
	poly(ci, s["rim_low"], RIM)
	poly(ci, s["edge"], BAIZE_EDGE)
	poly(ci, s["baize"], BAIZE_DARK)
	poly(ci, s["mid"], BAIZE)
	poly(ci, s["glow"], Color("37895f"))
	# worn patches, a coffee ring and a scuff (fixed, so they never flicker)
	var w := size.x
	rect(ci, w * 0.28, 150.0 * u, 14.0 * u, 2.0 * u, BAIZE_WEAR)
	rect(ci, w * 0.62, 168.0 * u, 18.0 * u, 2.0 * u, BAIZE_WEAR)
	rect(ci, w * 0.47, 206.0 * u, 10.0 * u, 2.0 * u, BAIZE_DARK)
	rect(ci, w * 0.74, 142.0 * u, 3.0 * u, 3.0 * u, BAIZE_DARK)
	var rc := Vector2(w * 0.78, 176.0 * u)
	ell(ci, rc.x, rc.y, 7.0 * u, 3.5 * u, BAIZE_DARK)
	ell(ci, rc.x, rc.y, 5.0 * u, 2.0 * u, BAIZE)
	rect(ci, w * 0.16, 190.0 * u, 3.0 * u, 3.0 * u, BAIZE_WEAR)


## The table's shadow on the room round its far edge (drawn before the people, who cover most of it): it grounds the close-up where the rim meets the live room at the sides.
static func draw_table_shadow(ci: CanvasItem, size: Vector2, u: float) -> void:
	var s := _table_shapes(size)
	poly(ci, s["shadow_far"], shade(INK, 0.22))
	poly(ci, s["shadow_near"], shade(INK, 0.28))


## The lamp over the table, the same hanging lamp the day room shows from across the room: `part` "cone" draws the shade at the top of the picture and its cone of warm light over the
## people (before the table), "pool" the pool of light on the baize (after the table).
static func draw_lamp(ci: CanvasItem, size: Vector2, u: float, part: String) -> void:
	var cx := roundf(size.x * 0.5)
	if part == "pool":
		ell(ci, cx, 150.0 * u, 190.0 * u, 44.0 * u, shade(WARM, 0.06))
		ell(ci, cx, 146.0 * u, 120.0 * u, 26.0 * u, shade(WARM, 0.07))
		return
	var t := maxf(1.0, roundf(u))
	poly(ci, PackedVector2Array([Vector2(cx - 22.0 * u, 14.0 * u), Vector2(cx + 22.0 * u, 14.0 * u), Vector2(cx + 200.0 * u, 120.0 * u), Vector2(cx - 200.0 * u, 120.0 * u)]), shade(WARM, 0.07))
	poly(ci, PackedVector2Array([Vector2(cx - 18.0 * u, 14.0 * u), Vector2(cx + 18.0 * u, 14.0 * u), Vector2(cx + 120.0 * u, 120.0 * u), Vector2(cx - 120.0 * u, 120.0 * u)]), shade(WARM, 0.07))
	rect(ci, cx - t, 0.0, 2.0 * t, 6.0 * u, INK)
	poly_o(ci, PackedVector2Array([Vector2(roundf(cx - 7.0 * u), roundf(5.0 * u)), Vector2(roundf(cx + 7.0 * u), roundf(5.0 * u)), Vector2(roundf(cx + 22.0 * u), roundf(14.0 * u)), Vector2(roundf(cx - 22.0 * u), roundf(14.0 * u))]), LAMP_SHADE, INK, t)
	rect(ci, cx - 6.0 * u, 6.0 * u, 12.0 * u, maxf(1.0, u), LAMP_SHADE_LIGHT)
	ell(ci, cx, 15.0 * u, 7.0 * u, 3.0 * u, WARM_HOT)


## The bet spot: an oval painted on the baize where the stake goes, worn and faint, `pu` the money's unit (so the ring holds a note).
static func draw_bet_ring(ci: CanvasItem, c: Vector2, pu: float) -> void:
	var rx := 28.0 * pu
	var ry := 16.0 * pu
	var pts := PackedVector2Array()
	for i in 29:
		var th := TAU * float(i) / 28.0
		pts.append(Vector2(roundf(c.x + cos(th) * rx), roundf(c.y + sin(th) * ry)))
	ell(ci, c.x, c.y, rx, ry, shade(BAIZE_DARK, 0.6))
	ci.draw_polyline(pts, shade(BAIZE_WEAR, 0.9), maxf(1.0, roundf(pu * 0.8)))


## A hint of the player's own chair at the very bottom corners (optional).
static func draw_chair_back(ci: CanvasItem, size: Vector2, u: float) -> void:
	var y := size.y - 9.0 * u
	for sx in [0.0, 1.0]:
		var x0: float = 0.0 if sx == 0.0 else size.x - 22.0 * u
		poly_o(ci, PackedVector2Array([
			Vector2(roundf(x0), roundf(y)), Vector2(roundf(x0 + 22.0 * u), roundf(y)),
			Vector2(roundf(x0 + 22.0 * u), roundf(size.y)), Vector2(roundf(x0), roundf(size.y)),
		]), RIM_DARK, INK, maxf(1.0, roundf(u)))


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
