class_name BlackjackView
extends Control
## The seated blackjack table as a picture (docs/BLACKJACK_INTEGRATION.md sections 6 and 8): composed from the drawing kit (`BlackjackDraw`, `BlackjackPeople`, `MoneyDraw`) and driven entirely by the
## activity's `state()` snapshot and the song time. It owns no game state; the only memory it keeps is presentation: each person's previous mood and gaze (to ease between them), the last touch
## (for the response ring) and whether the picture was wobbling (to ease the rocking out).
##
## The host (RunMinigameHost) mounts it full-rect in the stage's low-res viewport and sets `now_fn`, `beat_s`, `reduced`, `high_contrast`, `state_fn` and `screen_size` (the stage area in screen pixels),
## then calls `hit(local_pos)` with a tap in screen pixels. Everything is drawn under one child control (`_pic`) so that the whole table can rise, sink, rock and tip as one picture: the
## rise (sitting), the sink (leaving), the rocking (wobble) and the tumble (falling) are only that child's position and rotation, and `hit` undoes the same transform.
## The picture is a stack of layers (`_Layer`, back to front) that each frame are offered what they should show; a layer redraws only when that changed, so the static room, table and chair cost
## nothing per frame and the people, money and cards cost only while they move. There is no text anywhere: every cue is a shape that moves.
##
## The money pile is drawn at 1.25 of the unit (a fiver is about 48 x 25 canvas pixels: big enough to find and touch on a phone) from the kit's `pile_origin` (see `pile_geometry`).
## What `pile_geometry` guarantees: the pile for any balance up to 10000 pence lies inside the canvas, clear of the player's cards and of the bet spot.

const PEOPLE: Array[String] = ["npc_a", "dealer", "npc_b"]
const LOOPING: Array[String] = ["rest", "invite", "tap_table", "wave_off", "clap"]
const HOLDING: Array[String] = ["point_deck", "point_hand"]
const MOOD_EASE := 0.2
const FLIP_S := 0.3
const FEEDBACK_S := 0.4
const RING_POINTS := 28
const REACT_DELAY := {"npc_a": 0.0, "dealer": 0.12, "npc_b": 0.24}  # seconds: a table of people reacting one after another, not as one
const BACKLIGHT := {"npc_a": Color("e070c8"), "dealer": Color("ffd27a"), "npc_b": Color("5ad0e0")}
const CLEAR_BEATS := 0.8
const RISE_BEATS := 1.2
const SINK_BEATS := 1.2
const FALL_BEATS := 1.5
const FALL_TIP_BEATS := 1.6
const FALL_LURCH_BEATS := 0.3
const PILE_SCALE := 1.25
const TALLEST_PILE := 2000  # four fivers: the tallest column of notes the pile layout makes


## One layer of the picture, a child of the picture control in draw order. It draws its `spec` with `fn` and keeps that drawing (the renderer replays it every frame) until the view offers a
## different spec, so a layer whose inputs did not change costs no drawing at all: the room's light, the table and the chair are drawn once per canvas size, a head when the face, the gaze or the
## beat's whole-pixel bob changes, arms when the pose does, the money and the cards only while something moves. A layer's draw function reads its spec and constants, nothing else.
class _Layer:
	extends Control
	var fn: Callable
	var spec: Array = []

	func _draw() -> void:
		if fn.is_valid() and not spec.is_empty():
			fn.call(self, spec)


var now_fn: Callable = Callable()
var state_fn: Callable = Callable()
var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var screen_size := Vector2(844, 250)

var _pic: Control
var _layers: Dictionary = {}  # name -> _Layer, created in draw order
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
## The card entries last made and what they were made from (the snapshot's seats, the bob of the hinted hand, the size, the beat), valid until `until`: the next song time at which a card
## appears, turns or is cleared away (-INF while one moves).
var _cards_memo := {"seats": null, "bob": 0.0, "size": Vector2.ZERO, "beat_s": 0.0, "until": -INF, "entries": []}
var _cards_until := INF  # set by `_card_entries`
## Per person, the inputs the last torso and arms states were made from (the torso moves only in a shrug, resting arms not at all).
var _torso_in: Dictionary = {}
var _arms_in: Dictionary = {}


func _init() -> void:
	_pic = Control.new()
	_pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_pic)
	# back to front: the room's light, the table's shadow, the door, the people's bodies, the lamp and the table, the rings and the deck, the money, the people's arms, the cards, the
	# chair, the player's hands, the light on the edges of what may be touched and the answer to a touch
	_add_layer("backlight", _draw_backlight)
	_add_layer("shadow", _draw_shadow)
	_add_layer("door", _draw_door)
	for who in PEOPLE:
		_add_layer("torso_" + who, _draw_person)
		_add_layer("head_" + who, _draw_person)
	_add_layer("table", _draw_table)
	_add_layer("rings", _draw_rings)
	_add_layer("money", _draw_money)
	_add_layer("money_over", _draw_money)
	for who in PEOPLE:
		_add_layer("arms_" + who, _draw_person)
	_add_layer("cards", _draw_cards)
	_add_layer("chair", _draw_chair)
	_add_layer("hands", _draw_hands)
	_add_layer("marks", _draw_marks)


func _add_layer(name: String, fn: Callable) -> void:
	var l := _Layer.new()
	l.name = name
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.set_anchors_preset(Control.PRESET_FULL_RECT)  # the picture's size: a zero-size control is culled away once the picture rotates
	l.fn = fn
	_pic.add_child(l)
	_layers[name] = l


func _process(_delta: float) -> void:
	_fetch()
	if _pic.size != size:
		_pic.size = size
	var pose := _pose(_snap, _now)
	_pic.pivot_offset = pose["pivot"]
	_pic.position = Vector2(0.0, float(pose["dy"]))
	_pic.rotation = float(pose["ang"])
	_pic.visible = _live(_snap) and not bool(pose["gone"])
	if _pic.visible and is_visible_in_tree():
		_prepare()


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
	var org := BlackjackDraw.pile_origin(canvas)
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
			# a lurch, then the chair hangs tipping for a moment (the table's faces go from shock to laughter in plain view), then the drop
			var pre := _smooth(clampf((now - t0) / (FALL_LURCH_BEATS * bs), 0.0, 1.0))
			var tip := _smooth(clampf((now - t0 - FALL_LURCH_BEATS * bs) / (FALL_TIP_BEATS * bs), 0.0, 1.0))
			var k := clampf((now - t0 - (FALL_LURCH_BEATS + FALL_TIP_BEATS) * bs) / (FALL_BEATS * bs), 0.0, 1.0)
			if reduced:
				dy = _ease_in(k) * h * 1.1
				ang = dir * (0.05 * pre + 0.03 * tip + 0.04 * k)
			else:
				var teeter := 0.025 * sin(TAU * (now - t0) / bs * 2.0) * tip * (1.0 - k)
				ang = dir * (0.1 * pre + 0.2 * tip + teeter + 0.7 * _ease_in(k))
				dy = -6.0 * float(_geometry()["u"]) * tip * (1.0 - k) + pow(k, 2.2) * h * 1.6
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


func _gesture_state(gs: Dictionary, now: float, who := "dealer") -> Dictionary:
	var name := str(gs.get("name", "rest"))
	var dur := float(gs.get("dur", 0.0))
	var el := maxf(now - float(gs.get("t0", 0.0)), 0.0)
	var bs := maxf(beat_s, 0.05)
	if name in LOOPING and name != "rest" and who != "dealer" and el >= 2.0 * (dur if dur > 0.0 else 2.0 * bs):
		return {"name": "rest", "t": fposmod(now / (2.0 * bs), 1.0)}  # a player's loop plays twice and the hand goes back to rest (the dealer keeps inviting until you act)
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
				return g["bet_spot"]  # the open palm over the bet ring: put it here
			return hand_c
		"pay":
			return g["tray"]
		"sweep":
			return g["bet_spot"]
	return Vector2.ZERO


# ------------------------------------------------------------------ painting

## Hands `spec` to a layer: it is redrawn only if the spec differs from the one it drew last.
func _offer(name: String, spec: Array) -> void:
	var l: _Layer = _layers[name]
	if spec != l.spec:
		l.spec = spec
		l.queue_redraw()


## The picture at the fetched snapshot and time, as one spec per layer (every frame the picture is on show).
func _prepare() -> void:
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
	var lift := _lift(bp)
	# the room's light on the people (it breathes through the layer's alpha, so its rows are drawn once per size) and the table's shadow on the room
	var breathe := 0.0 if reduced else 0.03 * sin(TAU * bp / 4.0)
	(_layers["backlight"] as _Layer).self_modulate = Color(1.0, 1.0, 1.0, 0.045 + breathe * 0.5)
	_offer("backlight", [size, u])
	_offer("shadow", [size, u])
	# the door (always there; it swings and spills light on the beat only while it is a target)
	_offer("door", [size, u, bp if "exit" in tg else 0.5, bool(hints.get("exit_urged", false))])
	# people: bodies before the table, arms after it
	for who in PEOPLE:
		var s: Dictionary = seats.get(who, {})
		var mood: Dictionary = s.get("mood", {})
		var gaze: Dictionary = s.get("gaze", {})
		var m := _track(who, mood, gaze)
		var w := _smooth(clampf((now - float(m["mood_t0"]) - float(REACT_DELAY[who])) / MOOD_EASE, 0.0, 1.0))
		var face: Dictionary = BlackjackPeople.face_params(str(m["mood"])) if w >= 1.0 else BlackjackPeople.blend(BlackjackPeople.face_params(str(m["prev"])), BlackjackPeople.face_params(str(m["mood"])), w)
		var gw := _smooth(clampf((now - float(m["gaze_t0"])) / MOOD_EASE, 0.0, 1.0))
		var gp: Vector2 = _gaze_target(str(m["gaze"]), who, snap, g)
		if gw < 1.0:
			gp = _gaze_target(str(m["gaze_prev"]), who, snap, g).lerp(gp, gw)
		var gs := _gesture_state(s.get("gesture", {}), now, who)
		var seat := BlackjackDraw.seat_pos(who, size)
		var aim := _aim(str(gs["name"]), snap, g, hand_c)
		var torso_in := [seat, u, gs["name"] == "shrug", gs["t"] if gs["name"] == "shrug" else 0.0]
		if torso_in != _torso_in.get(who):
			_torso_in[who] = torso_in
			_offer("torso_" + who, [BlackjackPeople.person_state(who, seat, u, face, gp, gs["name"], gs["t"], bp, aim, "torso")])
		_offer("head_" + who, [BlackjackPeople.person_state(who, seat, u, face, gp, gs["name"], gs["t"], bp, aim, "head")])
		var arms_in := [seat, u, gs["name"], 0.0 if gs["name"] == "rest" else gs["t"], aim]  # resting arms do not depend on the gesture's time
		if arms_in != _arms_in.get(who):
			_arms_in[who] = arms_in
			_offer("arms_" + who, [BlackjackPeople.person_state(who, seat, u, face, gp, gs["name"], gs["t"], bp, aim, "arms")])
	_offer("table", [size, u, g["bet_spot"], u * PILE_SCALE])
	# rings of light on the baize under everything that may be touched now (the run's hotspot language: a warm ring that breathes on the beat), and the deck
	var rings: Array = []
	for id: String in tg:
		if id != "exit" and bool(hints.get(id, false)):
			rings.append(_thing_rect(id, snap, hand_box))
	_offer("rings", [u, high_contrast, rings, lift if not rings.is_empty() else 0.0, g["deck"], lift if bool(hints.get("deck", false)) else 0.0])
	# the money: the top fiver hops on the beat while the bet is hinted. The pile up to the first item that moves (in flight or hopping) is one layer, it and everything over it another,
	# so the resting notes are not redrawn while one note hops or a few fly
	var items := _pile_items(snap, now)
	var top := -1
	var split := items.size()
	for i in items.size():
		if bool(items[i].get("moving", false)):
			split = mini(split, i)
		elif bool(hints.get("bet", false)) and int(items[i]["denomination"]) == 500:
			top = i
	if top >= 0:
		split = mini(split, top)
	_offer("money", [g["pu"], u, items.slice(0, split), -1, 0.0, []])
	_offer("money_over", [g["pu"], u, items.slice(split), top - split if top >= 0 else -1, lift if top >= 0 else 0.0, _bet_items(snap, now)])
	_offer("cards", [u, _cards(snap, now, g, -roundf(3.0 * u * lift) if bool(hints.get("hand", false)) else 0.0)])
	_offer("chair", [size, u])
	var pg: Dictionary = (seats.get("player", {}) as Dictionary).get("gesture", {})
	var pdur := float(pg.get("dur", 0.0))
	var pt := 1.0 if pdur <= 0.0 else clampf((now - float(pg.get("t0", 0.0))) / pdur, 0.0, 1.0)
	if pdur > 0.0 and str(snap.get("phase", "")) == "broke" and str(pg.get("name", "")) == "empty_pockets":
		pt = fposmod((now - float(pg.get("t0", 0.0))) / pdur, 1.0)  # the empty pockets keep turning out while you are broke
	var pm: Dictionary = snap.get("pile", {})
	var pile_note := _top_note(maxi(int(pm.get("pence", 0)), int(pm.get("from_pence", 0))))
	var tgt := {"bet": g["bet_spot"], "deck": g["deck"], "hand": hand_c, "pockets": g["pockets"]}
	tgt["pile"] = pile_note.get_center() if pile_note.size.x > 0.0 else g["origin"]
	_offer("hands", [size, u, str(pg.get("name", "none")), pt, tgt])
	_offer("marks", [u, _hint_frames(snap, u, hints, hand_box, lift), _feedback(snap, now, u, hand_box)])


## How far a hinted thing has risen on the beat, 0..1: a quick swell up to the beat and an easy fall after it (the same breath the hotspot rings take). Steady at 0.5 in reduced motion.
func _lift(bp: float) -> float:
	if reduced:
		return 0.5
	var ph := 0.5 + 0.5 * cos(TAU * fposmod(bp, 1.0))
	return ph * ph


## Soft halos of the room's coloured light behind the three people, so they sit in the live room instead of on top of it (pink from the left, the lamp's warmth on the dealer, teal from the right).
## Drawn at full alpha: the layer's alpha is the light's strength (0.045, breathing on four beats).
func _draw_backlight(ci: Control, s: Array) -> void:
	var sz: Vector2 = s[0]
	var u: float = s[1]
	for who in PEOPLE:
		var c := BlackjackDraw.seat_pos(who, sz)
		var col: Color = BACKLIGHT[who]
		for i in 3:
			var k := 1.0 - 0.22 * float(i)
			BlackjackDraw.ell(ci, c.x, c.y + 16.0 * u, 52.0 * u * k, 48.0 * u * k, col)


func _draw_shadow(ci: Control, s: Array) -> void:
	BlackjackDraw.draw_table_shadow(ci, s[0], s[1])


func _draw_door(ci: Control, s: Array) -> void:
	BlackjackDraw.draw_exit(ci, s[0], s[1], s[2], s[3])


func _draw_person(ci: Control, s: Array) -> void:
	BlackjackPeople.draw_person_state(ci, s[0])


## The lamp's cone, the table, the lamp's pool of light on the baize and the bet ring.
func _draw_table(ci: Control, s: Array) -> void:
	var sz: Vector2 = s[0]
	var u: float = s[1]
	BlackjackDraw.draw_lamp(ci, sz, u, "cone")
	BlackjackDraw.draw_table(ci, sz, u)
	BlackjackDraw.draw_lamp(ci, sz, u, "pool")
	BlackjackDraw.draw_bet_ring(ci, s[2], s[3])


func _draw_rings(ci: Control, s: Array) -> void:
	var u: float = s[0]
	for r: Rect2 in s[2]:
		_hint_ring(ci, r, u, s[3], false, s[1])
	var c: Vector2 = s[4]
	var hint: float = s[5]
	BlackjackDraw.draw_deck(ci, c, u)
	if hint > 0.0:  # the top card slides out toward the player and back, on the beat
		BlackjackDraw.draw_card(ci, {}, c + Vector2(-2.0 * u * hint, 8.0 * u * hint), u, false, 1.0, -0.12 * hint)


func _draw_money(ci: Control, s: Array) -> void:
	var pu: float = s[0]
	var u: float = s[1]
	var items: Array = s[2]
	var top: int = s[3]
	var lift: float = s[4]
	for i in items.size():
		var it: Dictionary = items[i]
		if i == top:  # the top fiver hops on the beat and lifts its near corner, as if it wanted picking up
			var pos: Vector2 = it["pos"]
			pos.y -= roundf((1.0 + 3.0 * lift) * u)
			MoneyDraw.draw_item(ci, 500, pos, pu, -0.1 * lift, float(it.get("alpha", 1.0)))
		else:
			_draw_money_item(ci, it, pu, u)
	for it: Dictionary in s[5]:
		_draw_money_item(ci, it, pu, u)


## One item of a pile; a flying one swells a little at the top of its arc and leaves its shadow on the baize under it, so the eye can follow it.
func _draw_money_item(ci: Control, it: Dictionary, pu: float, u: float) -> void:
	var d := int(it["denomination"])
	var a := float(it.get("alpha", 1.0))
	var h := float(it.get("lift", 0.0))
	if h > 0.0:
		var gp: Vector2 = it.get("ground", it["pos"])
		var sz := MoneyDraw.item_size(d, pu)
		var sk := 1.0 - 0.3 * h
		BlackjackDraw.ell(ci, gp.x + 2.0 * u, gp.y + 3.0 * u, sz.x * 0.5 * sk, maxf(2.0, sz.y * 0.35 * sk), BlackjackDraw.shade(BlackjackDraw.INK, 0.28 * a * (1.0 - 0.4 * h)))
	MoneyDraw.draw_item(ci, d, it["pos"], pu * (1.0 + 0.2 * h), float(it["angle"]), a)


## The card entries at `now`, made again only when something they depend on changed (see `_cards_memo`).
func _cards(snap: Dictionary, now: float, g: Dictionary, hand_bob: float) -> Array:
	var m := _cards_memo
	var seats: Variant = snap.get("seats", {})
	if is_same(m["seats"], seats) and m["bob"] == hand_bob and m["size"] == size and m["beat_s"] == beat_s and now < float(m["until"]):
		return m["entries"]
	var entries := _card_entries(snap, now, g, hand_bob)
	_cards_memo = {"seats": seats, "bob": hand_bob, "size": size, "beat_s": beat_s, "until": _cards_until, "entries": entries}
	return entries


## Every card on the table at `now` as {card, pos, ang, scale, alpha, flip, up}, in draw order: the landed ones, then the ones in flight over them. Sets `_cards_until` to the next song time
## at which the entries change by time alone (-INF while a card moves, turns or is cleared away, or the player's cards scatter).
func _card_entries(snap: Dictionary, now: float, g: Dictionary, hand_bob: float) -> Array:
	var u: float = g["u"]
	var bs := maxf(beat_s, 0.05)
	var seats: Dictionary = snap.get("seats", {})
	var pg: Dictionary = (seats.get("player", {}) as Dictionary).get("gesture", {})
	var scatter := 0.0
	var until := INF
	if str(pg.get("name", "")) == "drop_cards":
		var st0 := float(pg.get("t0", 0.0))
		scatter = _ease_out(clampf((now - st0) / (0.6 * bs), 0.0, 1.0))
		until = st0 if now < st0 else (-INF if now < st0 + 0.6 * bs else until)
	var deck: Vector2 = g["deck"]
	var tray: Vector2 = g["tray"]
	var landed: Array = []
	var flying: Array = []
	for seat in ["npc_a", "dealer", "npc_b", "player"]:
		var cards: Array = (seats.get(seat, {}) as Dictionary).get("cards", [])
		var sc := BlackjackDraw.seat_card_scale(seat)
		for i in cards.size():
			var c: Dictionary = cards[i]
			var td := float(c["t_deal"])
			if now < td:
				until = minf(until, td)
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
			var tf := float(c["t_flip"])
			if in_flight or (tf >= 0.0 and now >= tf and now < tf + FLIP_S):
				until = -INF
			elif tf > now:
				until = minf(until, tf)
			if in_flight:
				var e := _ease_out(clampf((now - td) / maxf(tl - td, 0.001), 0.0, 1.0))
				var spin := 0.8 * (1.0 if (int(c["rank"]) + int(c["suit"]) + i) % 2 == 0 else -1.0)
				pos = deck.lerp(spot, e) + Vector2(0.0, -sin(PI * e) * 14.0 * u)
				ang = (1.0 - e) * spin
				scl = lerpf(1.0, sc, e)
			else:
				if tf >= 0.0 and now >= tf and now < tf + FLIP_S:
					flip = (now - tf) / FLIP_S
					up = true
				if seat == "player":
					pos.y += hand_bob
				if seat == "player" and scatter > 0.0:
					pos += Vector2(float((i * 37) % 5 - 2) * 5.0 * u, float(i % 2 * 2 - 1) * 4.0 * u) * scatter
					ang = sin(float(i) * 2.1 + 1.0) * 0.35 * scatter
			var tc := float(c["t_clear"])
			if tc > now:
				until = minf(until, tc)
			if tc >= 0.0 and now >= tc:
				var q := (now - tc) / (CLEAR_BEATS * bs)
				if q >= 1.0:
					continue
				until = -INF
				pos = pos.lerp(tray, _ease_in(q))
				alpha = 1.0 - maxf(0.0, (q - 0.6) / 0.4)
			var entry := {"card": {"rank": c["rank"], "suit": c["suit"]}, "pos": pos, "ang": ang, "scale": scl, "alpha": alpha, "flip": flip, "up": up}
			if in_flight:
				flying.append(entry)
			else:
				landed.append(entry)
	landed.append_array(flying)
	_cards_until = until
	return landed


func _draw_cards(ci: Control, s: Array) -> void:
	var u: float = s[0]
	for e: Dictionary in s[1]:
		BlackjackDraw.draw_card(ci, e["card"], e["pos"], u, bool(e["up"]), float(e["flip"]), float(e["ang"]), float(e["alpha"]), float(e["scale"]))


func _draw_chair(ci: Control, s: Array) -> void:
	BlackjackDraw.draw_chair_back(ci, s[0], s[1])


func _draw_hands(ci: Control, s: Array) -> void:
	BlackjackPeople.draw_player_hands(ci, s[0], s[1], s[2], s[3], s[4])


## A ring of warm light on the baize round the foot of `r` and a soft glow inside it, breathing with `lift` (0..1). `bright` is the touched flash; `hc` high contrast.
func _hint_ring(ci: Control, r: Rect2, u: float, lift: float, bright: bool, hc_on: bool) -> void:
	if r.size.x <= 0.0:
		return
	var c := Vector2(r.get_center().x, r.end.y - r.size.y * 0.25)
	var rx := r.size.x * 0.5 + (6.0 + 3.0 * lift) * u
	var ry := r.size.y * 0.42 + (4.0 + 2.0 * lift) * u
	var hc := 1.0 if hc_on else 0.0
	BlackjackDraw.ell(ci, c.x, c.y, rx, ry, BlackjackDraw.shade(BlackjackDraw.WARM, 0.12 + 0.14 * lift + 0.1 * hc))
	var pts := PackedVector2Array()
	for i in RING_POINTS + 1:
		var th := TAU * float(i) / float(RING_POINTS)
		pts.append(Vector2(roundf(c.x + cos(th) * rx), roundf(c.y + sin(th) * ry)))
	var wid := maxf(1.0, roundf(u * (2.0 if hc_on or bright else 1.0)))
	ci.draw_polyline(pts, BlackjackDraw.shade(BlackjackDraw.WARM_HOT, 0.55 + 0.45 * lift if not bright else 1.0), wid)


## Light catching the edges of every hinted thing (drawn over it), in the warm of the rings below: [frame rect, line width, colour] each.
func _hint_frames(snap: Dictionary, u: float, hints: Dictionary, hand_box: Rect2, lift: float) -> Array:
	var out: Array = []
	var px := maxf(1.0, roundf(u * (2.0 if high_contrast else 1.0)))
	for id: String in snap.get("targets", []):
		if id == "exit" or not bool(hints.get(id, false)):
			continue
		var r := _thing_rect(id, snap, hand_box)
		if r.size.x <= 0.0:
			continue
		match id:
			"bet":
				r.position.y -= roundf((1.0 + 3.0 * lift) * u)
			"hand":
				r.position.y -= roundf(3.0 * u * lift)
		out.append([r.grow(px), px, BlackjackDraw.shade(BlackjackDraw.WARM_HOT, 0.3 + 0.55 * lift)])
	return out


## The answer to a touch, as [the touched thing's rect, progress 0..1], or empty when there is none to show.
func _feedback(snap: Dictionary, now: float, u: float, hand_box: Rect2) -> Array:
	var el := now - float(_last_hit["t"])
	var id := str(_last_hit["id"])
	if id == "" or el < 0.0 or el > FEEDBACK_S:
		return []
	var r := _thing_rect(id, snap, hand_box)
	if r.size.x <= 0.0:
		return []
	return [r, el / FEEDBACK_S]


## The light on the hinted edges, then the answer to a touch: the thing flashes white and its ring of light opens out and fades (the run's committed-hotspot look).
func _draw_marks(ci: Control, s: Array) -> void:
	var u: float = s[0]
	for f: Array in s[1]:
		_frame(ci, f[0], f[1], f[2])
	var fb: Array = s[2]
	if fb.is_empty():
		return
	var r: Rect2 = fb[0]
	var k: float = fb[1]
	ci.draw_rect(r.grow(2.0 * u), Color(1.0, 0.98, 0.85, 0.55 * (1.0 - k) * (1.0 - k)))
	var e := _ease_out(k)
	var c := Vector2(r.get_center().x, r.end.y - r.size.y * 0.25)
	var rx := r.size.x * 0.5 + (8.0 + 30.0 * e) * u
	var ry := r.size.y * 0.42 + (5.0 + 14.0 * e) * u
	var pts := PackedVector2Array()
	for i in RING_POINTS + 1:
		var th := TAU * float(i) / float(RING_POINTS)
		pts.append(Vector2(roundf(c.x + cos(th) * rx), roundf(c.y + sin(th) * ry)))
	ci.draw_polyline(pts, Color(1.0, 0.97, 0.78, 1.0 - k), maxf(1.0, roundf(u * 3.0 * (1.0 - k) + u)))


func _frame(ci: Control, r: Rect2, px: float, col: Color) -> void:
	var q := Rect2(roundf(r.position.x), roundf(r.position.y), roundf(r.size.x), roundf(r.size.y))
	ci.draw_rect(Rect2(q.position.x + px, q.position.y, q.size.x - 2.0 * px, px), col)
	ci.draw_rect(Rect2(q.position.x + px, q.end.y - px, q.size.x - 2.0 * px, px), col)
	ci.draw_rect(Rect2(q.position.x, q.position.y + px, px, q.size.y - 2.0 * px), col)
	ci.draw_rect(Rect2(q.end.x - px, q.position.y + px, px, q.size.y - 2.0 * px), col)


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
