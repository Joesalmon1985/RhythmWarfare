class_name BlackjackView
extends Control
## The seated blackjack table as a picture (docs/BLACKJACK_INTEGRATION.md sections 6 and 8): composed from the drawing kit (`BlackjackDraw`, `BlackjackPeople`, `MoneyDraw`) and driven entirely by the
## activity's `state()` snapshot and the song time. It owns no game state; the only memory it keeps is presentation: each person's previous mood and gaze (to ease between them), the last touch
## (for the response ring) and whether the picture was wobbling (to ease the rocking out).
##
## The host (RunMinigameHost) mounts it full-rect in the stage's low-res viewport and sets `now_fn`, `beat_s`, `reduced`, `high_contrast`, `state_fn` and `screen_size` (the stage area in screen pixels),
## then calls `hit(local_pos)` with a tap in screen pixels. Everything is drawn into one child control (`_Pic`) so that the whole table can rise, sink, rock and tip as one picture: the
## rise (sitting), the sink (leaving), the rocking (wobble) and the tumble (falling) are only that child's position and rotation, and `hit` undoes the same transform.
## There is no text anywhere: every cue is a shape that moves.
##
## The money pile is drawn at 0.85 of the unit, from a view-owned origin (see `pile_geometry`), because the kit's `pile_rect` (118 u wide) cannot hold twenties, fivers and the coin grid.
## What `pile_geometry` guarantees: the pile for any balance up to 10000 pence lies inside the canvas, clear of the player's cards and of the bet spot.

const PEOPLE: Array[String] = ["npc_a", "dealer", "npc_b"]
const LOOPING: Array[String] = ["rest", "invite", "tap_table", "wave_off", "clap"]
const HOLDING: Array[String] = ["point_deck", "point_hand"]
const MOOD_EASE := 0.2
const FLIP_S := 0.3
const FEEDBACK_S := 0.3
const CLEAR_BEATS := 0.8
const RISE_BEATS := 1.2
const SINK_BEATS := 1.2
const FALL_BEATS := 2.6
const FALL_LURCH_BEATS := 0.3
const PILE_SCALE := 0.85
const TALLEST_PILE := 3500  # seven fivers: the highest stack of notes the breakdown makes


class _Pic:
	extends Control
	var fn: Callable

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)


var now_fn: Callable = Callable()
var state_fn: Callable = Callable()
var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var screen_size := Vector2(844, 250)

var _pic: _Pic
var _snap: Dictionary = {}
var _now := 0.0
var _mem: Dictionary = {}  # per person: {mood, prev, mood_t0, gaze, gaze_prev, gaze_t0}
var _last_hit := {"id": "", "t": -100.0}
var _was_wobbling := false
var _geo_size := Vector2.ZERO
var _geo: Dictionary = {}
var _pile_cache := {"pence": -1, "origin": Vector2.ZERO, "items": []}
var _bet_cache := {"pence": -1, "origin": Vector2.ZERO, "items": []}
var _top_cache := {"pence": -1, "origin": Vector2.ZERO, "rect": Rect2()}


func _init() -> void:
	_pic = _Pic.new()
	_pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pic.fn = _paint
	add_child(_pic)


func _process(_delta: float) -> void:
	_fetch()
	if _pic.size != size:
		_pic.size = size
	var pose := _pose(_snap, _now)
	_pic.pivot_offset = pose["pivot"]
	_pic.position = Vector2(0.0, float(pose["dy"]))
	_pic.rotation = float(pose["ang"])
	_pic.visible = _live(_snap) and not bool(pose["gone"])
	_pic.queue_redraw()


# ------------------------------------------------------------------ the public surface

## The target under a tap: `local_pos` is in screen pixels from the stage area's top-left. "" for nothing, and for any target that is not in the snapshot's `targets`.
func hit(local_pos: Vector2) -> String:
	var snap := _fetch()
	if not _live(snap) or screen_size.x <= 0.0 or screen_size.y <= 0.0:
		return ""
	var p := Vector2(local_pos.x * size.x / screen_size.x, local_pos.y * size.y / screen_size.y)
	p = _xform(_pose(snap, _now)).affine_inverse() * p
	var rects := _target_rects(snap)
	var best := ""
	var best_d := INF
	for id: String in rects:
		var r: Rect2 = rects[id]
		if r.has_point(p):
			var d := (p - r.get_center()).length_squared()
			if d < best_d:
				best_d = d
				best = id
	if best != "":
		_last_hit = {"id": best, "t": _now}
	return best


## The touch rectangles live right now, id to Rect2 in canvas coordinates (empty when nothing is seated or nothing may be touched).
func target_rects() -> Dictionary:
	var snap := _fetch()
	return _target_rects(snap) if _live(snap) else {}


## The denominations drawn in the money pile at song time `now` (resting and flying items alike).
func shown_pile(now: float) -> Array:
	return _denominations(_pile_items(_fetch(), now))


## The denominations drawn on the bet spot at song time `now`.
func shown_bet(now: float) -> Array:
	return _denominations(_bet_items(_fetch(), now))


## The view's money layout for a canvas `size`: {origin (the centre of the first fiver), scale (the unit the notes are drawn at)}.
## Guarantee: for every balance up to 10000 pence `MoneyDraw.pile_bounds(pence, origin, scale)` lies inside the canvas, right of nothing the player touches: clear of the hand target, the deck and the bet spot.
static func pile_geometry(canvas: Vector2) -> Dictionary:
	var u := BlackjackDraw.unit(canvas)
	var pu := u * PILE_SCALE
	var org := Vector2(roundf(62.0 * u), roundf(170.0 * u))
	var tall := MoneyDraw.pile_bounds(TALLEST_PILE, org, pu)
	var over := tall.end.y - (canvas.y - 1.0)
	if over > 0.0:
		org.y -= ceilf(over)
	return {"origin": org, "scale": pu}


# ------------------------------------------------------------------ snapshot, pose, geometry

func _fetch() -> Dictionary:
	_now = float(now_fn.call()) if now_fn.is_valid() else 0.0
	_snap = state_fn.call() if state_fn.is_valid() else {}
	var w: Variant = _snap.get("wobble", null)
	if w is Dictionary and int((w as Dictionary).get("level", 0)) == 1:
		_was_wobbling = true
	return _snap


func _live(snap: Dictionary) -> bool:
	return not snap.is_empty() and str(snap.get("phase", "")) != ""


func _geometry() -> Dictionary:
	if size == _geo_size and not _geo.is_empty():
		return _geo
	_geo_size = size
	var pg := pile_geometry(size)
	_geo = {"u": maxf(BlackjackDraw.unit(size), 0.05), "origin": pg["origin"], "pu": pg["scale"], "deck": BlackjackDraw.deck_spot(size), "bet_spot": BlackjackDraw.bet_spot(size), "tray": BlackjackDraw.dealer_tray_spot(size), "pockets": BlackjackDraw.pockets_spot(size)}
	_pile_cache["pence"] = -1
	_bet_cache["pence"] = -1
	_top_cache["pence"] = -1
	return _geo


## How far (negative: up) a hinted thing lifts on the beat: nothing between beats, a clear hop on the beat.
static func _bob(beat_phase: float, u: float) -> float:
	var ph := 0.5 + 0.5 * cos(TAU * fposmod(beat_phase, 1.0))
	return -roundf(3.0 * u * ph * ph)


## The top fiver rests a little raised and hops higher on the beat.
static func _bet_nudge(beat_phase: float, u: float) -> float:
	var ph := 0.5 + 0.5 * cos(TAU * fposmod(beat_phase, 1.0))
	return -roundf((1.0 + 3.0 * ph * ph) * u)


static func _ease_out(k: float) -> float:
	return 1.0 - (1.0 - k) * (1.0 - k) * (1.0 - k)


static func _ease_in(k: float) -> float:
	return k * k


static func _smooth(k: float) -> float:
	return k * k * (3.0 - 2.0 * k)


## The whole picture's pose at `now`: {dy, ang, pivot, gone}. At rest (and not wobbling) it is the identity.
func _pose(snap: Dictionary, now: float) -> Dictionary:
	var h := size.y
	var dy := 0.0
	var ang := 0.0
	var gone := false
	var bs := maxf(beat_s, 0.05)
	var phase := str(snap.get("phase", ""))
	var t0 := float(snap.get("phase_t0", 0.0))
	match phase:
		"sitting":
			var k := clampf((now - t0) / (RISE_BEATS * bs), 0.0, 1.0)
			dy = (1.0 - _ease_out(k)) * h * 1.05
		"leaving":
			var pile: Dictionary = snap.get("pile", {})
			var end := t0
			if str(pile.get("via", "")) == "pockets":
				end = float(pile.get("t0", t0)) + float(pile.get("dur", 0.0))
			var k := clampf((now - (end - SINK_BEATS * bs)) / (SINK_BEATS * bs), 0.0, 1.0)
			dy = _ease_in(k) * h * 1.05
			gone = k >= 1.0
		"falling":
			var dir := 1.0 if int(snap.get("hand", 0)) % 2 == 0 else -1.0
			var pre := _smooth(clampf((now - t0) / (FALL_LURCH_BEATS * bs), 0.0, 1.0))
			var k := clampf((now - t0 - FALL_LURCH_BEATS * bs) / (FALL_BEATS * bs), 0.0, 1.0)
			if reduced:
				dy = _ease_in(k) * h * 1.1
				ang = dir * (0.05 * pre + 0.06 * k)
			else:
				ang = dir * (0.12 * pre + 0.95 * _ease_in(k))
				dy = pow(k, 2.2) * h * 1.6
			gone = k >= 1.0
	if phase != "falling" and phase != "":
		var wob: Dictionary = snap.get("wobble", {})
		var amp := 0.0
		if int(wob.get("level", 0)) == 1:
			amp = clampf((now - float(wob.get("t0", 0.0))) / bs, 0.0, 1.0)
		elif _was_wobbling:
			amp = 1.0 - clampf((now - float(wob.get("t0", 0.0))) / (1.5 * bs), 0.0, 1.0)
		if amp > 0.0:
			var b := now / bs
			var lurch := (1.0 if int(floorf(b)) % 2 == 0 else -1.0) * exp(-5.0 * fposmod(b, 1.0))
			var scale := 0.5 if reduced else 1.0
			ang += amp * scale * (0.06 * sin(TAU * b / 6.0) + 0.03 * lurch)
			dy += amp * scale * lurch * 1.5 * _geometry()["u"] * -1.0
	return {"dy": dy, "ang": ang, "pivot": Vector2(size.x * 0.5, size.y), "gone": gone}


func _xform(pose: Dictionary) -> Transform2D:
	var piv: Vector2 = pose["pivot"]
	return Transform2D(0.0, Vector2(0.0, float(pose["dy"]))) * Transform2D(0.0, piv) * Transform2D(float(pose["ang"]), Vector2.ZERO) * Transform2D(0.0, -piv)


## How many of the player's cards are on the table (flying or landed, not cleared away); at least two so the target is always the width of a starting hand.
func _player_count(snap: Dictionary, now: float) -> int:
	var n := 0
	for c: Dictionary in (snap.get("seats", {}) as Dictionary).get("player", {}).get("cards", []):
		if now >= float(c["t_deal"]):
			n += 1
	return maxi(n, 2)


func _top_note(pence: int) -> Rect2:
	var g := _geometry()
	var org: Vector2 = g["origin"]
	if int(_top_cache["pence"]) != pence or _top_cache["origin"] != org:
		_top_cache["pence"] = pence
		_top_cache["origin"] = org
		_top_cache["rect"] = MoneyDraw.top_note_rect(pence, org, float(g["pu"]))
	return _top_cache["rect"]


func _hand_box(snap: Dictionary, now: float) -> Rect2:
	var g := _geometry()
	var u: float = g["u"]
	var n := _player_count(snap, now)
	var a := BlackjackDraw.card_spot("player", 0, size)
	var b := BlackjackDraw.card_spot("player", n - 1, size)
	return Rect2(a.x - BlackjackDraw.CARD_W * 0.5 * u, a.y - BlackjackDraw.CARD_H * 0.5 * u, b.x - a.x + BlackjackDraw.CARD_W * u, BlackjackDraw.CARD_H * u)


func _deck_box() -> Rect2:
	var g := _geometry()
	var u: float = g["u"]
	var c: Vector2 = g["deck"]
	return Rect2(c.x - BlackjackDraw.CARD_W * 0.5 * u, c.y - BlackjackDraw.CARD_H * 0.5 * u, BlackjackDraw.CARD_W * u, (BlackjackDraw.CARD_H + 5.0) * u)


func _bet_rect(snap: Dictionary) -> Rect2:
	var g := _geometry()
	var u: float = g["u"]
	var m := BlackjackDraw.MIN_TARGET * u
	var note := _top_note(int((snap.get("pile", {}) as Dictionary).get("pence", 0)))
	if note.size.x <= 0.0:
		return BlackjackDraw.target_rect("bet", size)
	var c := note.get_center()
	return Rect2(clampf(c.x - m * 0.5, 0.0, size.x - m), clampf(c.y - m * 0.5, 0.0, size.y - m), m, m)


func _target_rects(snap: Dictionary) -> Dictionary:
	var out := {}
	for id: String in snap.get("targets", []):
		match id:
			"bet":
				out[id] = _bet_rect(snap)
			"deck":
				out[id] = BlackjackDraw.target_rect("deck", size)
			"hand":
				out[id] = BlackjackDraw.target_rect("hand", size, _player_count(snap, _now))
			"exit":
				out[id] = BlackjackDraw.exit_rect(size)
	return out


# ------------------------------------------------------------------ money

func _denominations(items: Array) -> Array:
	var out: Array = []
	for it: Dictionary in items:
		out.append(int(it["denomination"]))
	return out


func _rest_items(cache: Dictionary, pence: int, origin: Vector2, pu: float) -> Array:
	if int(cache["pence"]) != pence or cache["origin"] != origin:
		cache["pence"] = pence
		cache["origin"] = origin
		cache["items"] = MoneyDraw.pile_layout(pence, origin, pu)
	return cache["items"]


func _money_items(m: Dictionary, cache: Dictionary, origin: Vector2, pu: float, away: Vector2, now: float) -> Array:
	var to := int(m.get("pence", 0))
	var from := int(m.get("from_pence", to))
	var dur := float(m.get("dur", 0.0))
	var p := 1.0 if dur <= 0.0 else clampf((now - float(m.get("t0", 0.0))) / dur, 0.0, 1.0)
	if from == to or p >= 1.0:
		return _rest_items(cache, to, origin, pu)
	return MoneyDraw.transition_items(from, to, p, origin, pu, away)


func _pile_away(m: Dictionary, g: Dictionary) -> Vector2:
	match str(m.get("via", "")):
		"pockets":
			return g["pockets"]
		"bet":
			return g["bet_spot"]
		"dealer":
			return g["tray"]
	return g["origin"]


func _bet_away(snap: Dictionary, b: Dictionary, g: Dictionary) -> Vector2:
	match str(b.get("via", "")):
		"pile":
			var pile: Dictionary = snap.get("pile", {})
			var note := _top_note(maxi(int(pile.get("pence", 0)), int(pile.get("from_pence", 0))))
			return note.get_center() if note.size.x > 0.0 else g["origin"]
		"dealer":
			return g["tray"]
	return g["bet_spot"]


func _pile_items(snap: Dictionary, now: float) -> Array:
	if not _live(snap):
		return []
	var g := _geometry()
	var m: Dictionary = snap.get("pile", {})
	return _money_items(m, _pile_cache, g["origin"], g["pu"], _pile_away(m, g), now)


func _bet_items(snap: Dictionary, now: float) -> Array:
	if not _live(snap):
		return []
	var g := _geometry()
	var b: Dictionary = snap.get("bet", {})
	return _money_items(b, _bet_cache, g["bet_spot"], g["pu"], _bet_away(snap, b, g), now)


# ------------------------------------------------------------------ people memory

func _track(who: String, mood: Dictionary, gaze: Dictionary) -> Dictionary:
	var m: Dictionary = _mem.get(who, {})
	var mn := str(mood.get("name", "neutral"))
	var gn := str(gaze.get("target", "player"))
	if m.is_empty():
		m = {"mood": mn, "prev": mn, "mood_t0": float(mood.get("t0", 0.0)), "gaze": gn, "gaze_prev": gn, "gaze_t0": float(gaze.get("t0", 0.0))}
		_mem[who] = m
	if m["mood"] != mn:
		m["prev"] = m["mood"]
		m["mood"] = mn
		m["mood_t0"] = float(mood.get("t0", 0.0))
	if m["gaze"] != gn:
		m["gaze_prev"] = m["gaze"]
		m["gaze"] = gn
		m["gaze_t0"] = float(gaze.get("t0", 0.0))
	return m


func _gaze_target(target: String, who: String, snap: Dictionary, g: Dictionary) -> Vector2:
	match target:
		"pile":
			return (g["origin"] as Vector2) + Vector2(20.0, 0.0) * float(g["pu"])
		"bet":
			if int((snap.get("bet", {}) as Dictionary).get("pence", 0)) <= 0:
				var note := _top_note(int((snap.get("pile", {}) as Dictionary).get("pence", 0)))
				if note.size.x > 0.0:
					return note.get_center()
	return BlackjackPeople.gaze_point(target, who, size)


func _gesture_state(gs: Dictionary, now: float) -> Dictionary:
	var name := str(gs.get("name", "rest"))
	var dur := float(gs.get("dur", 0.0))
	var el := maxf(now - float(gs.get("t0", 0.0)), 0.0)
	var bs := maxf(beat_s, 0.05)
	if name in LOOPING:
		var per := dur if dur > 0.0 else 2.0 * bs
		return {"name": name, "t": fposmod(el / per, 1.0)}
	if name in HOLDING:
		return {"name": name, "t": 1.0 if dur <= 0.0 else clampf(el / dur, 0.0, 1.0)}
	if dur <= 0.0:
		return {"name": "rest", "t": 0.0}
	if el > dur + 0.5 * bs:
		return {"name": "rest", "t": fposmod(now / (2.0 * bs), 1.0)}
	return {"name": name, "t": clampf(el / dur, 0.0, 1.0)}


func _aim(name: String, snap: Dictionary, g: Dictionary, hand_c: Vector2) -> Vector2:
	match name:
		"point_deck", "deal":
			return g["deck"]
		"point_hand":
			return hand_c
		"invite":
			if "bet" in (snap.get("targets", []) as Array):
				var note := _top_note(int((snap.get("pile", {}) as Dictionary).get("pence", 0)))
				if note.size.x > 0.0:
					return note.get_center()
			return hand_c
		"pay", "sweep":
			return g["tray"]
	return Vector2.ZERO


# ------------------------------------------------------------------ painting

func _paint(ci: Control) -> void:
	if not _live(_snap):
		return
	var snap := _snap
	var now := _now
	var g := _geometry()
	var u: float = g["u"]
	var bs := maxf(beat_s, 0.05)
	var bp := now / bs
	var seats: Dictionary = snap.get("seats", {})
	var tg: Array = snap.get("targets", [])
	var hints: Dictionary = snap.get("hints", {})
	var hand_box := _hand_box(snap, now)
	var hand_c := hand_box.get_center()
	# the door (always there; it pulses on the beat only while it is a target)
	BlackjackDraw.draw_exit(ci, size, u, bp if "exit" in tg else 0.5, bool(hints.get("exit_urged", false)))
	# people: pose data once, then bodies, table, ..., arms
	var crew: Array = []
	for who in PEOPLE:
		var s: Dictionary = seats.get(who, {})
		var mood: Dictionary = s.get("mood", {})
		var gaze: Dictionary = s.get("gaze", {})
		var m := _track(who, mood, gaze)
		var w := _smooth(clampf((now - float(m["mood_t0"])) / MOOD_EASE, 0.0, 1.0))
		var face: Dictionary = BlackjackPeople.face_params(str(m["mood"])) if w >= 1.0 else BlackjackPeople.blend(BlackjackPeople.face_params(str(m["prev"])), BlackjackPeople.face_params(str(m["mood"])), w)
		var gw := _smooth(clampf((now - float(m["gaze_t0"])) / MOOD_EASE, 0.0, 1.0))
		var gp: Vector2 = _gaze_target(str(m["gaze"]), who, snap, g)
		if gw < 1.0:
			gp = _gaze_target(str(m["gaze_prev"]), who, snap, g).lerp(gp, gw)
		var gs := _gesture_state(s.get("gesture", {}), now)
		crew.append({"who": who, "face": face, "gaze": gp, "g": gs["name"], "t": gs["t"], "aim": _aim(str(gs["name"]), snap, g, hand_c)})
	for c: Dictionary in crew:
		BlackjackPeople.draw_person(ci, c["who"], BlackjackDraw.seat_pos(c["who"], size), u, c["face"], c["gaze"], c["g"], c["t"], bp, c["aim"], "body")
	BlackjackDraw.draw_table(ci, size, u)
	var bob := _bob(bp, u)
	BlackjackDraw.draw_deck(ci, (g["deck"] as Vector2) + Vector2(0.0, bob if bool(hints.get("deck", false)) else 0.0), u)
	_paint_money(ci, snap, now, g, bool(hints.get("bet", false)), bp)
	for c: Dictionary in crew:
		BlackjackPeople.draw_person(ci, c["who"], BlackjackDraw.seat_pos(c["who"], size), u, c["face"], c["gaze"], c["g"], c["t"], bp, c["aim"], "arms")
	_paint_cards(ci, snap, now, g, bob if bool(hints.get("hand", false)) else 0.0)
	BlackjackDraw.draw_chair_back(ci, size, u)
	var pg: Dictionary = (seats.get("player", {}) as Dictionary).get("gesture", {})
	var pdur := float(pg.get("dur", 0.0))
	var pt := 1.0 if pdur <= 0.0 else clampf((now - float(pg.get("t0", 0.0))) / pdur, 0.0, 1.0)
	if pdur > 0.0 and str(snap.get("phase", "")) == "broke" and str(pg.get("name", "")) == "empty_pockets":
		pt = fposmod((now - float(pg.get("t0", 0.0))) / pdur, 1.0)  # the empty pockets keep turning out while you are broke
	var pile_note := _top_note(int((snap.get("pile", {}) as Dictionary).get("pence", 0)))
	var tgt := {"bet": g["bet_spot"], "deck": g["deck"], "hand": hand_c, "pockets": g["pockets"]}
	tgt["pile"] = pile_note.get_center() if pile_note.size.x > 0.0 else g["origin"]
	BlackjackPeople.draw_player_hands(ci, size, u, str(pg.get("name", "none")), pt, tgt)
	_paint_hints(ci, snap, now, g, hints, hand_box, bp)
	_paint_feedback(ci, snap, now, g, hand_box)


func _paint_money(ci: Control, snap: Dictionary, now: float, g: Dictionary, hint_bet: bool, bp: float) -> void:
	var pu: float = g["pu"]
	var items := _pile_items(snap, now)
	var top := -1
	var nud := 0.0
	if hint_bet:
		for i in items.size():
			if int(items[i]["denomination"]) == 500:
				top = i
		nud = _bet_nudge(bp, float(g["u"]))
	for i in items.size():
		var it: Dictionary = items[i]
		var pos: Vector2 = it["pos"]
		if i == top:
			pos.y += nud
		MoneyDraw.draw_item(ci, int(it["denomination"]), pos, pu, float(it["angle"]), float(it.get("alpha", 1.0)))
	for it: Dictionary in _bet_items(snap, now):
		MoneyDraw.draw_item(ci, int(it["denomination"]), it["pos"], pu, float(it["angle"]), float(it.get("alpha", 1.0)))


func _paint_cards(ci: Control, snap: Dictionary, now: float, g: Dictionary, hand_bob: float) -> void:
	var u: float = g["u"]
	var bs := maxf(beat_s, 0.05)
	var seats: Dictionary = snap.get("seats", {})
	var pg: Dictionary = (seats.get("player", {}) as Dictionary).get("gesture", {})
	var scatter := 0.0
	if str(pg.get("name", "")) == "drop_cards":
		scatter = _ease_out(clampf((now - float(pg.get("t0", 0.0))) / (0.6 * bs), 0.0, 1.0))
	var deck: Vector2 = g["deck"]
	var tray: Vector2 = g["tray"]
	var flying: Array = []
	for seat in ["npc_a", "dealer", "npc_b", "player"]:
		var cards: Array = (seats.get(seat, {}) as Dictionary).get("cards", [])
		var sc := BlackjackDraw.seat_card_scale(seat)
		for i in cards.size():
			var c: Dictionary = cards[i]
			var td := float(c["t_deal"])
			if now < td:
				continue
			var spot := BlackjackDraw.card_spot(seat, i, size)
			var pos := spot
			var ang := 0.0
			var scl := sc
			var alpha := 1.0
			var flip := 1.0
			var up := bool(c["face_up"])
			var tl := float(c["t_land"])
			var in_flight := now < tl
			if in_flight:
				var e := _ease_out(clampf((now - td) / maxf(tl - td, 0.001), 0.0, 1.0))
				var spin := 0.8 * (1.0 if (int(c["rank"]) + int(c["suit"]) + i) % 2 == 0 else -1.0)
				pos = deck.lerp(spot, e) + Vector2(0.0, -sin(PI * e) * 14.0 * u)
				ang = (1.0 - e) * spin
				scl = lerpf(1.0, sc, e)
			else:
				var tf := float(c["t_flip"])
				if tf >= 0.0 and now >= tf and now < tf + FLIP_S:
					flip = (now - tf) / FLIP_S
					up = true
				if seat == "player":
					pos.y += hand_bob
				if seat == "player" and scatter > 0.0:
					pos += Vector2(float((i * 37) % 5 - 2) * 5.0 * u, float(i % 2 * 2 - 1) * 4.0 * u) * scatter
					ang = sin(float(i) * 2.1 + 1.0) * 0.35 * scatter
			var tc := float(c["t_clear"])
			if tc >= 0.0 and now >= tc:
				var q := (now - tc) / (CLEAR_BEATS * bs)
				if q >= 1.0:
					continue
				pos = pos.lerp(tray, _ease_in(q))
				alpha = 1.0 - maxf(0.0, (q - 0.6) / 0.4)
			var entry := {"card": c, "pos": pos, "ang": ang, "scale": scl, "alpha": alpha, "flip": flip, "up": up}
			if in_flight:
				flying.append(entry)
			else:
				_draw_card_entry(ci, entry, u)
	for e: Dictionary in flying:
		_draw_card_entry(ci, e, u)


func _draw_card_entry(ci: Control, e: Dictionary, u: float) -> void:
	BlackjackDraw.draw_card(ci, e["card"], e["pos"], u, bool(e["up"]), float(e["flip"]), float(e["ang"]), float(e["alpha"]), float(e["scale"]))


func _paint_hints(ci: Control, snap: Dictionary, now: float, g: Dictionary, hints: Dictionary, hand_box: Rect2, bp: float) -> void:
	var u: float = g["u"]
	var hu := u * (2.2 if high_contrast else 1.4)
	var bob := _bob(bp, u)
	for id: String in snap.get("targets", []):
		if not bool(hints.get(id, false)) or id == "exit":
			continue
		var r := _thing_rect(id, snap, hand_box)
		r.position.y += _bet_nudge(bp, u) if id == "bet" else bob
		MoneyDraw.draw_target_hint(ci, r.grow(u), hu, bp)
		if id == "bet":
			_arrow(ci, Vector2(r.end.x + 3.0 * u, r.get_center().y), Vector2.RIGHT, u, bp)
		else:
			_arrow(ci, Vector2(r.get_center().x, r.position.y - 3.0 * u), Vector2.UP, u, bp)


## A chunky arrow pointing down at `tip`, hopping towards it on the beat (a second cue besides the glow: the shape and the motion say "touch here").
func _arrow(ci: Control, tip: Vector2, away: Vector2, u: float, bp: float) -> void:
	var ph := 0.5 + 0.5 * cos(TAU * fposmod(bp, 1.0))
	var lift := roundf(5.0 * u * (1.0 - ph * ph))
	var t := Vector2(roundf(tip.x + away.x * lift), roundf(tip.y + away.y * lift))
	var hw := roundf(8.0 * u)
	var hh := roundf(8.0 * u)
	var sw := roundf(3.0 * u)
	var sh := roundf(8.0 * u)
	var rot := Vector2.UP.angle_to(away)
	var pts := PackedVector2Array()
	for v in [Vector2.ZERO, Vector2(hw, -hh), Vector2(sw, -hh), Vector2(sw, -hh - sh), Vector2(-sw, -hh - sh), Vector2(-sw, -hh), Vector2(-hw, -hh)]:
		var q: Vector2 = (v as Vector2).rotated(rot)
		pts.append(Vector2(roundf(t.x + q.x), roundf(t.y + q.y)))
	BlackjackDraw.poly_o(ci, pts, BlackjackDraw.WARM_HOT, BlackjackDraw.INK, maxf(1.0, roundf(u)))


## The rectangle of the thing a target is (not its generous touch area): the top fiver, the deck, the player's cards, the door.
func _thing_rect(id: String, snap: Dictionary, hand_box: Rect2) -> Rect2:
	match id:
		"bet":
			return _top_note(int((snap.get("pile", {}) as Dictionary).get("pence", 0)))
		"deck":
			return _deck_box()
		"hand":
			return hand_box
	return BlackjackDraw.exit_rect(size).grow(-6.0 * float(_geometry()["u"]))


func _paint_feedback(ci: Control, snap: Dictionary, now: float, g: Dictionary, hand_box: Rect2) -> void:
	var el := now - float(_last_hit["t"])
	var id := str(_last_hit["id"])
	if id == "" or el < 0.0 or el > FEEDBACK_S:
		return
	var u: float = g["u"]
	var k := el / FEEDBACK_S
	var r := _thing_rect(id, snap, hand_box)
	if r.size.x <= 0.0:
		return
	var px := float(maxi(1, roundi(u)))
	ci.draw_rect(r.grow(2.0 * u), Color(1.0, 0.97, 0.8, 0.4 * (1.0 - k)))
	for ring in 3:
		var gr := r.grow((3.0 + ring * 3.0 + 16.0 * _ease_out(k)) * u)
		var col := Color(1.0, 0.96, 0.7, (1.0 - k) * (1.0 - 0.25 * ring))
		ci.draw_rect(Rect2(gr.position.x, gr.position.y, gr.size.x, px), col)
		ci.draw_rect(Rect2(gr.position.x, gr.end.y - px, gr.size.x, px), col)
		ci.draw_rect(Rect2(gr.position.x, gr.position.y + px, px, gr.size.y - 2.0 * px), col)
		ci.draw_rect(Rect2(gr.end.x - px, gr.position.y + px, px, gr.size.y - 2.0 * px), col)
