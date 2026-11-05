extends Control
## A complete mock blackjack table over a mint "room" backdrop, rendered through a low-res SubViewport like the game (640 x 230 shown at twice the size; env RW_GALLERY_LOW=1 gives 320 x 115
## shown at four times). Env RW_GALLERY_RECTS=1 outlines the four touch rectangles, RW_GALLERY_T fixes the animation time in seconds. Every few seconds the people change mood and gesture.

const WALL := Color("1d2522")
const WALL_DARK := Color("161c1a")
const FLOOR_A := Color("1a1b20")
const FLOOR_B := Color("15161a")

class Layer:
	extends Control
	var fn: Callable

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)

var _low := false
var _size := Vector2(640, 230)
var _sub: SubViewport
var _layer: Layer
var _time := 0.0
var _fixed := -1.0
var _rects := false

const MOODS := ["neutral", "smug", "laugh", "concerned", "surprised", "annoyed", "wince", "happy", "sad", "thinking"]
const GESTURES := ["rest", "invite", "point_deck", "point_hand", "tap_table", "wave_off", "deal", "sweep", "pay", "shrug", "clap", "facepalm"]
const PLAYER := ["none", "pockets", "lay_money", "push_bet", "reach_deck", "cover_cards", "drop_cards", "empty_pockets", "gather_money"]


func _ready() -> void:
	_low = OS.get_environment("RW_GALLERY_LOW") == "1"
	_rects = OS.get_environment("RW_GALLERY_RECTS") == "1"
	if OS.has_environment("RW_GALLERY_T"):
		_fixed = float(OS.get_environment("RW_GALLERY_T"))
	_size = Vector2(320, 115) if _low else Vector2(640, 230)
	_sub = SubViewport.new()
	_sub.size = Vector2i(_size)
	_sub.transparent_bg = false
	_sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_sub)
	var rect := TextureRect.new()
	rect.texture = _sub.get_texture()
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(rect)
	_layer = Layer.new()
	_layer.size = _size
	_layer.fn = _scene
	_sub.add_child(_layer)


func _process(delta: float) -> void:
	_time += delta
	_layer.queue_redraw()


func _now() -> float:
	return _fixed if _fixed >= 0.0 else _time


func _scene(ci: Control) -> void:
	var s := _size
	var u := s.y / 230.0
	var now := _now()
	var beat := now * 2.9
	var step := int(now / 2.5)
	# room: wall, a baseboard, a checked floor
	ci.draw_rect(Rect2(0, 0, s.x, 112.0 * u), WALL)
	ci.draw_rect(Rect2(0, 96.0 * u, s.x, 16.0 * u), WALL_DARK)
	var tile := roundf(16.0 * u)
	var y := roundf(112.0 * u)
	var row := 0
	while y < s.y:
		var x := 0.0
		var col := row % 2
		while x < s.x:
			ci.draw_rect(Rect2(x, y, tile, tile), FLOOR_A if col == 0 else FLOOR_B)
			x += tile
			col = 1 - col
		y += tile
		row += 1
	BlackjackDraw.draw_exit(ci, s, u, beat, int(now / 5.0) % 2 == 1)
	var who := ["npc_a", "dealer", "npc_b"]
	var moods := [MOODS[step % 10], MOODS[(step * 3 + 1) % 10], MOODS[(step * 7 + 4) % 10]]
	var gest := [GESTURES[(step * 5 + 2) % 12], GESTURES[(step * 5 + 3) % 12], GESTURES[(step * 5 + 4) % 12]]
	var t := fposmod(now * 0.5, 1.0)
	var targets := [
		BlackjackDraw.card_spot("npc_a", 0, s), BlackjackDraw.deck_spot(s), BlackjackDraw.card_spot("player", 0, s),
	]
	for i in 3:
		var c := BlackjackDraw.seat_pos(who[i], s)
		BlackjackPeople.draw_person(ci, who[i], c, u, BlackjackPeople.face_params(moods[i]), BlackjackPeople.gaze_point(["player", "deck", "own_cards"][(step + i) % 3], who[i], s), gest[i], t, beat, _aim(gest[i], who[i], s, targets), "body")
	BlackjackDraw.draw_table(ci, s, u)
	# cards: two each, dealer's second face down, one card mid flip
	for i in 3:
		var seat: String = who[i]
		var sc := BlackjackDraw.seat_card_scale(seat)
		for k in 2:
			var card := {"rank": [1, 10, 7, 12, 5, 13][(i * 2 + k) % 6], "suit": (i * 2 + k) % 4}
			var up := not (seat == "dealer" and k == 1)
			var flip := 1.0
			if seat == "npc_b" and k == 1:
				flip = fposmod(now * 0.7, 1.0)
			BlackjackDraw.draw_card(ci, card, BlackjackDraw.card_spot(seat, k, s), u, up, flip, 0.0, 1.0, sc)
	for k in 2:
		BlackjackDraw.draw_card(ci, {"rank": [1, 10][k], "suit": [0, 1][k]}, BlackjackDraw.card_spot("player", k, s), u, true)
	BlackjackDraw.draw_card(ci, {"rank": 8, "suit": 3}, BlackjackDraw.card_spot("player", 2, s), u, true, fposmod(now * 0.6, 1.0), 0.0)
	BlackjackDraw.draw_card(ci, {"rank": 9, "suit": 2}, Vector2(s.x * 0.5 + 42.0 * u, 150.0 * u), u, true, 1.0, 0.5, 0.8)
	BlackjackDraw.draw_deck(ci, BlackjackDraw.deck_spot(s), u)
	var sp := BlackjackDraw.pile_origin(s)
	ci.draw_rect(Rect2(sp.x, sp.y - 20.0 * u, 70.0 * u, 20.0 * u), Color("4a6a50"))
	ci.draw_rect(Rect2(BlackjackDraw.bet_spot(s) - Vector2(12.0, 5.0) * u, Vector2(24.0, 10.0) * u), Color("4a6a50"))
	for i in 3:
		var c := BlackjackDraw.seat_pos(who[i], s)
		BlackjackPeople.draw_person(ci, who[i], c, u, BlackjackPeople.face_params(moods[i]), BlackjackPeople.gaze_point("player", who[i], s), gest[i], t, beat, _aim(gest[i], who[i], s, targets), "arms")
	BlackjackDraw.draw_chair_back(ci, s, u)
	BlackjackPeople.draw_player_hands(ci, s, u, PLAYER[(step + 1) % PLAYER.size()], fposmod(now / 2.5, 1.0))
	if _rects:
		for id in BlackjackDraw.TARGETS:
			ci.draw_rect(BlackjackDraw.target_rect(id, s, 4), Color(1, 0.2, 0.7), false, 1.0)


func _aim(g: String, who: String, s: Vector2, targets: Array) -> Vector2:
	match g:
		"point_deck":
			return targets[1]
		"point_hand", "invite", "pay":
			return targets[2]
		"deal":
			return BlackjackDraw.card_spot(who, 0, s)
		"sweep":
			return BlackjackDraw.dealer_tray_spot(s)
	return Vector2.ZERO
