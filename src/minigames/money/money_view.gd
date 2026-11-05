class_name MoneyDraw
extends RefCounted
## UK notes and coins drawn in code as pixel art, laid out as a pile on a table and animated when the amount changes. Reusable (blackjack, shops); it knows nothing about either.
## Everything is built from whole-pixel rects (coins from scanline spans, notes from a few rects and ellipse rows) so it stays crisp in the low-res viewport; `u = size.y / 230.0` scales it.
## Positions and sizes passed in are centres, in the canvas item's own coordinates. The draw functions reset the item's draw transform to identity when they finish.
##
## Pile layout. Origin is the centre of the first £5 note. Fivers form columns of four that grow toward the player (each note 10 u lower than the last, so every top-left numeral shows and four
## fivers read as four); the fifth fiver starts a second column 44 u to the right; twenties form a column 46 u to the left; coins sit in a fixed grid two cells wide and four tall right of the
## second fiver column (pounds on top), one cell per denomination. A note's place depends only on its denomination and
## its index within that denomination, so an item shared by two amounts never moves when the pile changes.

const NOTE_SIZE := {500: Vector2(38, 20), 1000: Vector2(40, 21), 2000: Vector2(42, 22)}
const COIN_DIAMETER := {200: 14.0, 100: 12.0, 50: 13.0, 20: 11.0, 10: 12.0, 5: 9.0, 2: 13.0, 1: 10.0}
const COIN_SIDES := {200: 0, 100: 12, 50: 7, 20: 7, 10: 0, 5: 0, 2: 0, 1: 0}
const COIN_LANE := {200: Vector2i(0, 0), 100: Vector2i(1, 0), 50: Vector2i(0, 1), 20: Vector2i(1, 1), 10: Vector2i(0, 2), 5: Vector2i(1, 2), 2: Vector2i(0, 3), 1: Vector2i(1, 3)}
const COIN_LABEL := {200: "£2", 100: "£1", 50: "50", 20: "20", 10: "10", 5: "5", 2: "2p", 1: "1p"}
const NOTE_LABEL := {500: "5", 1000: "10", 2000: "20"}
const NOTE_COLUMN_X := {500: 0.0, 1000: -46.0, 2000: -46.0}
const NOTE_STEP := 10.0
const NOTE_ROWS := 4  # a column holds four notes; the fifth of a denomination starts the next column to the right
const NOTE_COLUMN_STEP := 44.0
const MIN_NOTE_STEP_PX := 6.0  # the numeral is 5 pixels tall, so even the low-res stack shows each one whole
const NOTE_JITTER: Array[float] = [0.0, 1.0, 0.0, -1.0, 1.0, 0.0]
const COIN_GRID_X := 69.0
const COIN_CELL := Vector2(16.0, 15.0)
const COIN_GRID_TOP := -10.0

const CREAM := Color(0.95, 0.92, 0.80)
const FOIL := Color(0.93, 0.85, 0.50)
const GOLD := Color(0.90, 0.74, 0.28)
const GOLD_DARK := Color(0.58, 0.42, 0.10)
const SILVER := Color(0.84, 0.86, 0.88)
const SILVER_DARK := Color(0.46, 0.49, 0.55)
const COPPER := Color(0.76, 0.42, 0.22)
const COPPER_DARK := Color(0.38, 0.18, 0.09)
const WARM := Color(1.0, 0.85, 0.5)

static var _spans := {}  # sides * 1000 + diameter -> PackedInt32Array of (x0, x1) per row


# --- sizes ---------------------------------------------------------------------------------------------------------------------

## The designed size of one item (centre-based, linear in u). Notes are landscape, coins square-boxed.
static func item_size(denomination: int, u: float) -> Vector2:
	if MoneyBreakdown.is_note(denomination):
		return NOTE_SIZE.get(denomination, Vector2(40, 21)) * u
	var d: float = COIN_DIAMETER.get(denomination, 10.0)
	return Vector2(d, d) * u


static func draw_item(ci: CanvasItem, denomination: int, center: Vector2, u: float, angle := 0.0, alpha := 1.0) -> void:
	if MoneyBreakdown.is_note(denomination):
		draw_note(ci, denomination, center, u, angle, alpha)
	else:
		draw_coin(ci, denomination, center, u, alpha)


# --- notes ---------------------------------------------------------------------------------------------------------------------

static func _note_palette(denomination: int) -> Array:
	match denomination:
		500:
			return [Color(0.17, 0.62, 0.66), Color(0.08, 0.37, 0.42), Color(0.55, 0.85, 0.84)]
		1000:
			return [Color(0.80, 0.47, 0.18), Color(0.48, 0.25, 0.09), Color(0.95, 0.74, 0.45)]
		_:
			return [Color(0.52, 0.32, 0.64), Color(0.29, 0.16, 0.41), Color(0.76, 0.60, 0.84)]


static func _a(c: Color, alpha: float) -> Color:
	return Color(c.r, c.g, c.b, c.a * alpha)


static func _rect(ci: CanvasItem, x: int, y: int, w: int, h: int, c: Color) -> void:
	if w > 0 and h > 0:
		ci.draw_rect(Rect2(x, y, w, h), c)


static func _frame(ci: CanvasItem, x: int, y: int, w: int, h: int, c: Color) -> void:
	_rect(ci, x, y, w, 1, c)
	_rect(ci, x, y + h - 1, w, 1, c)
	_rect(ci, x, y + 1, 1, h - 2, c)
	_rect(ci, x + w - 1, y + 1, 1, h - 2, c)


## Filled ellipse (or, with half = 1, its bottom half) as whole-pixel rows; (cx, cy) is the centre in pixels.
static func _ellipse(ci: CanvasItem, cx: int, cy: int, rx: int, ry: int, c: Color, half := 0) -> void:
	for dy in range(0 if half == 1 else -ry, ry + 1):
		var k := 1.0 - float(dy * dy) / float((ry + 1) * (ry + 1))
		var hw := roundi(float(rx) * sqrt(maxf(k, 0.0)))
		_rect(ci, cx - hw, cy + dy, hw * 2 + 1, 1, c)


## One note, centred on `center`, tilted by `angle` radians. Whole-pixel size from u. The value is told three ways: a big cream numeral in the top-left corner (the largest thing on the note),
## the colour (£5 teal, £10 orange, £20 purple) and the size (a twenty is a little bigger than a fiver). At low detail (a note under 16 pixels tall) everything else is dropped so the numeral
## stays clean: just the body, a dark lower edge and the numeral on a darker plate.
static func draw_note(ci: CanvasItem, denomination: int, center: Vector2, u: float, angle := 0.0, alpha := 1.0) -> void:
	var pal := _note_palette(denomination)
	var body: Color = pal[0]
	var dark: Color = pal[1]
	var light: Color = pal[2]
	var base: Vector2 = NOTE_SIZE.get(denomination, Vector2(40, 21))
	var w := maxi(12, roundi(base.x * u))
	var h := maxi(6, roundi(base.y * u))
	var x0 := -(w / 2)
	var y0 := -(h / 2)
	var num: String = NOTE_LABEL.get(denomination, "")
	ci.draw_set_transform(Vector2(roundf(center.x), roundf(center.y)), angle, Vector2.ONE)
	_rect(ci, x0 + 1, y0 + 2, w + 1, h + 1, Color(0, 0, 0, 0.28 * alpha))
	_rect(ci, x0 - 1, y0 - 1, w + 2, h + 2, Color(0.06, 0.04, 0.08, 0.85 * alpha))
	_rect(ci, x0, y0, w, h, _a(CREAM, alpha))
	_rect(ci, x0 + 1, y0 + 1, w - 2, h - 2, _a(body, alpha))
	_rect(ci, x0 + 1, y0 + h - 1 - maxi(1, h / 8), w - 2, maxi(1, h / 8), _a(dark, alpha))
	if h < 16:
		# low detail: the numeral on a darker plate, a light corner tick on the right so the note still looks like a note
		var c1 := 1
		var tw := int(PixelGlyphs.text_width(num, c1))
		_rect(ci, x0 + 1, y0 + 1, tw + 3, 5 * c1 + 1, _a(dark, alpha))
		PixelGlyphs.draw_text(ci, num, Vector2(x0 + 2, y0 + 1), c1, _a(CREAM, alpha))
		if w - tw - 8 >= 6:
			_ellipse(ci, x0 + w - 1 - maxi(3, w / 5), y0 + h / 2, maxi(1, w / 10), maxi(1, h / 2 - 2), _a(light, 0.6 * alpha))
		ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return
	_frame(ci, x0 + 2, y0 + 2, w - 4, h - 4, _a(light, 0.45 * alpha))
	# the portrait on the right: a head and shoulders in the dark tone, with a light watermark oval behind
	var hx := x0 + roundi(w * 0.72)
	var hy := y0 + roundi(h * 0.44)
	_ellipse(ci, hx, hy + 1, roundi(w * 0.15), roundi(h * 0.34), _a(light, 0.55 * alpha))
	var rx := maxi(2, roundi(w * 0.07))
	var ry := maxi(2, roundi(h * 0.17))
	_ellipse(ci, hx, hy - 1, rx, ry, _a(dark, alpha))
	_ellipse(ci, hx, hy + ry + rx, roundi(w * 0.13), maxi(1, y0 + h - 3 - (hy + ry + rx)), _a(dark, alpha), 1)
	# the foil strip
	var fx := x0 + roundi(w * 0.5)
	_rect(ci, fx, y0 + 1, maxi(1, roundi(w * 0.05)), h - 2, _a(FOIL, alpha))
	_rect(ci, fx, y0 + 1, 1, h - 2, _a(CREAM, 0.8 * alpha))
	# the big numeral, with a dark drop shadow, top left; the small £ sits before it, the value repeats small in the bottom right corner
	var cell := maxi(2, floori(h / 10.0))
	var small := maxi(1, cell / 2)
	var pound_w := int(PixelGlyphs.text_width("£", small)) + small
	var nx := x0 + 3 + pound_w
	var ny := y0 + 2
	PixelGlyphs.draw_text(ci, "£", Vector2(x0 + 3 + 1, ny + 1), small, _a(dark, alpha))
	PixelGlyphs.draw_text(ci, "£", Vector2(x0 + 3, ny), small, _a(CREAM, alpha))
	PixelGlyphs.draw_text(ci, num, Vector2(nx + 1, ny + 1), cell, _a(dark, alpha))
	PixelGlyphs.draw_text(ci, num, Vector2(nx, ny), cell, _a(CREAM, alpha))
	if h >= 20:
		var bw := PixelGlyphs.text_width(num, small)
		PixelGlyphs.draw_text(ci, num, Vector2(x0 + w - 3 - bw, y0 + h - 3 - maxi(1, h / 8) - PixelGlyphs.text_height(small)), small, _a(CREAM, 0.9 * alpha))
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# --- coins ---------------------------------------------------------------------------------------------------------------------

## Row spans (x0, x1 exclusive) of a filled circle (sides 0) or regular polygon in a diameter x diameter box; cached.
static func _shape_spans(sides: int, diameter: int) -> PackedInt32Array:
	var key := sides * 1000 + diameter
	if _spans.has(key):
		return _spans[key]
	var out := PackedInt32Array()
	var r := diameter * 0.5
	var verts: Array[Vector2] = []
	if sides > 0:
		var rot := -PI * 0.5 if sides == 7 else -PI * 0.5 + PI / sides
		var rad := r if sides == 7 else r / cos(PI / sides)
		for k in sides:
			var a := rot + TAU * k / sides
			verts.append(Vector2(r + cos(a) * rad, r + sin(a) * rad))
	for row in diameter:
		var y := row + 0.5
		var lo := INF
		var hi := -INF
		if sides == 0:
			var k := r * r - (y - r) * (y - r)
			if k > 0.0:
				lo = r - sqrt(k)
				hi = r + sqrt(k)
		else:
			for i in sides:
				var p := verts[i]
				var q := verts[(i + 1) % sides]
				if (p.y <= y and q.y > y) or (q.y <= y and p.y > y):
					var x := p.x + (y - p.y) / (q.y - p.y) * (q.x - p.x)
					lo = minf(lo, x)
					hi = maxf(hi, x)
		if lo < hi:
			out.append(clampi(roundi(lo), 0, diameter))
			out.append(clampi(roundi(hi), 0, diameter))
		else:
			out.append(0)
			out.append(0)
	_spans[key] = out
	return out


## Fills the shape of the given diameter whose box top-left is (bx, by).
static func _fill_shape(ci: CanvasItem, sides: int, diameter: int, bx: int, by: int, c: Color) -> void:
	if diameter < 1:
		return
	var sp := _shape_spans(sides, diameter)
	var run_start := 0
	for row in diameter:
		var same_next := row + 1 < diameter and sp[row * 2] == sp[row * 2 + 2] and sp[row * 2 + 1] == sp[row * 2 + 3]
		if not same_next:
			var x0 := sp[row * 2]
			var x1 := sp[row * 2 + 1]
			if x1 > x0:
				_rect(ci, bx + x0, by + run_start, x1 - x0, row - run_start + 1, c)
			run_start = row + 1


static func draw_coin(ci: CanvasItem, denomination: int, center: Vector2, u: float, alpha := 1.0) -> void:
	var base: float = COIN_DIAMETER.get(denomination, 10.0)
	var sides: int = COIN_SIDES.get(denomination, 0)
	var d := maxi(4, roundi(base * u))
	var bx := -(d / 2)
	var by := -(d / 2)
	var metal := SILVER
	var edge := SILVER_DARK
	var ink := Color(0.26, 0.28, 0.34)
	if denomination == 2 or denomination == 1:
		metal = COPPER
		edge = COPPER_DARK
		ink = Color(0.34, 0.15, 0.07)
	elif denomination >= 100:
		metal = GOLD
		edge = GOLD_DARK
	var shine := metal.lerp(Color.WHITE, 0.55)
	ci.draw_set_transform(Vector2(roundf(center.x), roundf(center.y)), 0.0, Vector2.ONE)
	_fill_shape(ci, sides, d, bx + 1, by + 1, Color(0, 0, 0, 0.30 * alpha))
	_fill_shape(ci, sides, d, bx, by, _a(edge, alpha))
	_fill_shape(ci, sides, d - 2, bx + 1, by + 1, _a(metal, alpha))
	var face := d - 2
	var face_off := 1
	if denomination >= 100:  # bimetal: a silver centre inside a gold ring
		if d >= 10:
			_fill_shape(ci, sides, d - 4, bx + 2, by + 2, _a(edge, alpha))
			_fill_shape(ci, sides, d - 6, bx + 3, by + 3, _a(SILVER, alpha))
			face = d - 6
			face_off = 3
		else:
			_fill_shape(ci, sides, d - 4, bx + 2, by + 2, _a(SILVER, alpha))
			face = d - 4
			face_off = 2
		ink = Color(0.26, 0.28, 0.34)
	if d >= 8:  # a small shine on the upper left of the rim
		var sp := _shape_spans(sides, d)
		var row := 2 if d >= 10 else 1
		_rect(ci, bx + sp[row * 2] + 1, by + row, maxi(1, d / 5), 1, _a(shine, 0.9 * alpha))
	var cell := maxi(1, roundi(u))
	var label: String = COIN_LABEL.get(denomination, "")
	if label.length() == 2 and PixelGlyphs.text_width(label, cell) > face - 1:
		label = label.right(1) if label.begins_with("£") else label.left(1)
	if not label.is_empty() and PixelGlyphs.text_width(label, cell) <= face - 1 and PixelGlyphs.text_height(cell) <= face - 1:
		var tw := PixelGlyphs.text_width(label, cell)
		var th := PixelGlyphs.text_height(cell)
		var tp := Vector2(bx + face_off + roundf((face - tw) * 0.5), by + face_off + roundf((face - th) * 0.5))
		PixelGlyphs.draw_text(ci, label, tp, cell, _a(ink, alpha))
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# --- piles ---------------------------------------------------------------------------------------------------------------------

## Where each item of `breakdown(pence)` lies: [{denomination, pos (centre), angle, index (in the breakdown)}] in draw order. Deterministic; an item's place depends only on its denomination and
## its index within that denomination.
static func pile_layout(pence: int, origin: Vector2, u: float) -> Array:
	var out: Array = []
	var seen := {}
	var parts := MoneyBreakdown.breakdown(pence)
	for i in parts.size():
		var d: int = parts[i]
		var k: int = seen.get(d, 0)
		seen[d] = k + 1
		var pos: Vector2
		if MoneyBreakdown.is_note(d):
			var colx: float = float(NOTE_COLUMN_X.get(d, 0.0)) + float(k / NOTE_ROWS) * NOTE_COLUMN_STEP
			pos = origin + Vector2(roundf((colx + NOTE_JITTER[k % NOTE_JITTER.size()]) * u), roundf((k % NOTE_ROWS) * maxf(NOTE_STEP * u, MIN_NOTE_STEP_PX)))
		else:
			var lane: Vector2i = COIN_LANE.get(d, Vector2i.ZERO)
			var cx := COIN_GRID_X + lane.x * COIN_CELL.x + COIN_CELL.x * 0.5 + k * 2.0
			var cy := COIN_GRID_TOP + lane.y * COIN_CELL.y + COIN_CELL.y * 0.5 - k * 3.0
			pos = origin + Vector2(roundf(cx * u), roundf(cy * u))
		out.append({"denomination": d, "pos": pos, "angle": 0.0, "index": i})
	return out


static func _item_rect(denomination: int, pos: Vector2, u: float) -> Rect2:
	var sz := item_size(denomination, u)
	return Rect2(pos - sz * 0.5, sz)


## The rectangle that holds every item of the pile (a pixel of margin for the shadows). A zero-size rect at the origin for an empty pile.
static func pile_bounds(pence: int, origin: Vector2, u: float) -> Rect2:
	var items := pile_layout(pence, origin, u)
	if items.is_empty():
		return Rect2(origin, Vector2.ZERO)
	var r := _item_rect(items[0]["denomination"], items[0]["pos"], u)
	for it in items:
		r = r.merge(_item_rect(it["denomination"], it["pos"], u))
	return r.grow(1.0)


## The rect of the topmost £5 note (the bet touch target); empty when the pile has no fiver.
static func top_note_rect(pence: int, origin: Vector2, u: float) -> Rect2:
	var best := Rect2()
	for it in pile_layout(pence, origin, u):
		if int(it["denomination"]) == 500:
			best = _item_rect(500, it["pos"], u)
	return best


static func draw_pile(ci: CanvasItem, pence: int, origin: Vector2, u: float, alpha := 1.0) -> void:
	for it in pile_layout(pence, origin, u):
		draw_item(ci, it["denomination"], it["pos"], u, it["angle"], alpha)


# --- transition ----------------------------------------------------------------------------------------------------------------

static func _ease(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


## Start and length (of 0..1 progress) of item i of n inside the window [p0, p1].
static func _slot(i: int, n: int, p0: float, p1: float) -> Vector2:
	var w := p1 - p0
	if n <= 1:
		return Vector2(p0, w)
	var dur := w * clampf(2.0 / (n + 1), 0.35, 0.6)
	return Vector2(p0 + i * (w - dur) / (n - 1), dur)


static func _t(p: float, slot: Vector2) -> float:
	var t := clampf((p - slot.x) / slot.y, 0.0, 1.0)
	return 1.0 if t > 0.9999 else (0.0 if t < 0.0001 else t)


static func _flight(it: Dictionary, a: Vector2, b: Vector2, t: float, u: float, alpha_in: bool, seq: int) -> Dictionary:
	var d: int = it["denomination"]
	var e := _ease(t)
	var lift := (16.0 if MoneyBreakdown.is_note(d) else 18.0) * u
	var ground := a.lerp(b, e)
	var pos := ground + Vector2(0.0, -sin(PI * t) * lift)
	var angle := 0.0
	if MoneyBreakdown.is_note(d):
		angle = sin(PI * t) * 0.28 * (1.0 if seq % 2 == 0 else -1.0)
	var alpha := _ease(clampf(t / 0.25, 0.0, 1.0)) if alpha_in else 1.0 - _ease(clampf((t - 0.75) / 0.25, 0.0, 1.0))
	return {"denomination": d, "pos": pos, "angle": angle, "alpha": alpha, "moving": true, "index": it["index"], "lift": sin(PI * t), "ground": ground}


## The items on show at `progress` (0..1) while the pile goes from `from_pence` to `to_pence`, in draw order (resting items first, moving ones last): [{denomination, pos, angle, alpha, moving, index}];
## a moving item also carries `lift` (0..1, the height of its arc now) and `ground` (the point on the table under it), for a caller that draws its shadow or swells it in flight.
## Removed items travel to `away` one after another (top of the pile first), then new ones travel from `away` to their places. Items in both amounts never move.
static func transition_items(from_pence: int, to_pence: int, progress: float, origin: Vector2, u: float, away: Vector2) -> Array:
	var p := clampf(progress, 0.0, 1.0)
	var keep_left := {}
	for d in MoneyBreakdown.diff(from_pence, to_pence)["keep"]:
		keep_left[d] = int(keep_left.get(d, 0)) + 1
	var resting: Array = []
	var moving: Array = []
	var removing: Array = []
	var adding: Array = []
	var left := keep_left.duplicate()
	for it in pile_layout(from_pence, origin, u):
		var d: int = it["denomination"]
		if int(left.get(d, 0)) > 0:
			left[d] = int(left[d]) - 1
			resting.append({"denomination": d, "pos": it["pos"], "angle": 0.0, "alpha": 1.0, "moving": false, "index": it["index"]})
		else:
			removing.append(it)
	left = keep_left.duplicate()
	for it in pile_layout(to_pence, origin, u):
		var d: int = it["denomination"]
		if int(left.get(d, 0)) > 0:
			left[d] = int(left[d]) - 1
		else:
			adding.append(it)
	removing.reverse()
	var split := 0.5 if not adding.is_empty() and not removing.is_empty() else 1.0
	for i in removing.size():
		var it: Dictionary = removing[i]
		var s := _slot(i, removing.size(), 0.0, split)
		var t := _t(p, s)
		if t <= 0.0:
			resting.append({"denomination": it["denomination"], "pos": it["pos"], "angle": 0.0, "alpha": 1.0, "moving": false, "index": it["index"]})
		elif t < 1.0:
			moving.append(_flight(it, it["pos"], away, t, u, false, i))
	var start := 0.0 if removing.is_empty() else split
	for i in adding.size():
		var it: Dictionary = adding[i]
		var s := _slot(i, adding.size(), start, 1.0)
		var t := _t(p, s)
		if t >= 1.0:
			resting.append({"denomination": it["denomination"], "pos": it["pos"], "angle": 0.0, "alpha": 1.0, "moving": false, "index": it["index"]})
		elif t > 0.0:
			moving.append(_flight(it, away, it["pos"], t, u, true, i))
	resting.append_array(moving)
	return resting


static func draw_transition(ci: CanvasItem, from_pence: int, to_pence: int, progress: float, origin: Vector2, u: float, away: Vector2) -> void:
	for it in transition_items(from_pence, to_pence, progress, origin, u, away):
		draw_item(ci, it["denomination"], it["pos"], u, it["angle"], it["alpha"])


# --- touch target hint ---------------------------------------------------------------------------------------------------------

## A soft warm glow round `rect` that breathes with the beat, corner brackets that draw in and out, and a spark that runs round the edge. `beat_phase` counts beats (fraction = position in the beat;
## the spark takes four beats per lap). No colour-only meaning: the movement is the signal.
static func draw_target_hint(ci: CanvasItem, rect: Rect2, u: float, beat_phase: float) -> void:
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	var px := maxi(1, roundi(u))
	var ph := fposmod(beat_phase, 1.0)
	var pulse := 0.5 + 0.5 * cos(TAU * ph)
	var r := Rect2(Vector2(roundf(rect.position.x), roundf(rect.position.y)), Vector2(roundf(rect.size.x), roundf(rect.size.y)))
	for i in 3:
		var g := r.grow((i + 1) * px)
		var c := Color(WARM.r, WARM.g, WARM.b, (0.55 - 0.17 * i) * (0.5 + 0.5 * pulse))
		_frame_f(ci, g, px, c)
	ci.draw_rect(r, Color(WARM.r, WARM.g, WARM.b, 0.12 * pulse))
	var off := roundf(px * (1.0 + 1.5 * pulse))
	var arm := float(maxi(3, roundi(5.0 * u)))
	var bright := Color(1.0, 0.94, 0.68, 0.95)
	var bb := r.grow(off)
	for corner in 4:
		var sx := -1.0 if corner % 2 == 0 else 1.0
		var sy := -1.0 if corner < 2 else 1.0
		var cx := bb.position.x if sx < 0.0 else bb.end.x
		var cy := bb.position.y if sy < 0.0 else bb.end.y
		ci.draw_rect(Rect2(cx if sx < 0.0 else cx - arm, cy if sy < 0.0 else cy - px, arm, px), bright)
		ci.draw_rect(Rect2(cx if sx < 0.0 else cx - px, cy if sy < 0.0 else cy - arm, px, arm), bright)
	var sg := r.grow(2.0 * px)
	var per := 2.0 * (sg.size.x + sg.size.y)
	var lap := fposmod(beat_phase * 0.25, 1.0)
	for k in 4:
		var dist := fposmod(lap * per - k * 2.0 * px, per)
		var sp := _perimeter_point(sg, dist)
		ci.draw_rect(Rect2(roundf(sp.x), roundf(sp.y), px, px), Color(1.0, 0.97, 0.8, 1.0 - 0.25 * k))


static func _frame_f(ci: CanvasItem, g: Rect2, t: int, c: Color) -> void:
	ci.draw_rect(Rect2(g.position.x, g.position.y, g.size.x, t), c)
	ci.draw_rect(Rect2(g.position.x, g.end.y - t, g.size.x, t), c)
	ci.draw_rect(Rect2(g.position.x, g.position.y + t, t, g.size.y - 2 * t), c)
	ci.draw_rect(Rect2(g.end.x - t, g.position.y + t, t, g.size.y - 2 * t), c)


static func _perimeter_point(r: Rect2, dist: float) -> Vector2:
	if dist < r.size.x:
		return r.position + Vector2(dist, 0.0)
	dist -= r.size.x
	if dist < r.size.y:
		return r.position + Vector2(r.size.x, dist)
	dist -= r.size.y
	if dist < r.size.x:
		return r.position + Vector2(r.size.x - dist, r.size.y)
	dist -= r.size.x
	return r.position + Vector2(0.0, r.size.y - dist)
