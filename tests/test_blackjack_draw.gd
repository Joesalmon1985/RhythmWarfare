extends TestCase
## The blackjack drawing kit's pure parts: the vocabulary of the contract (section 8 of docs/BLACKJACK_INTEGRATION.md) is all implemented, and the geometry holds on every canvas size.

const SIZES := [Vector2(640, 230), Vector2(780, 231), Vector2(320, 115), Vector2(914, 360)]
const CONTRACT_MOODS := ["neutral", "happy", "laugh", "surprised", "annoyed", "sad", "wince", "concerned", "smug", "thinking"]
const CONTRACT_GESTURES := ["rest", "invite", "point_deck", "point_hand", "deal", "sweep", "pay", "shrug", "clap", "facepalm", "tap_table", "wave_off"]
const CONTRACT_PLAYER := ["none", "pockets", "lay_money", "push_bet", "reach_deck", "cover_cards", "drop_cards", "empty_pockets", "gather_money"]
const CONTRACT_GAZE := ["player", "deck", "own_cards", "dealer", "npc_a", "npc_b", "pile", "bet", "away"]


func _sorted(a: Array) -> Array:
	var b := a.duplicate()
	b.sort()
	return b


func test_vocabulary_matches_the_contract() -> void:
	assert_eq(_sorted(BlackjackPeople.MOOD_NAMES), _sorted(CONTRACT_MOODS))
	assert_eq(_sorted(BlackjackPeople.GESTURES), _sorted(CONTRACT_GESTURES))
	assert_eq(_sorted(BlackjackPeople.PLAYER_GESTURES), _sorted(CONTRACT_PLAYER))
	assert_eq(_sorted(BlackjackPeople.GAZE_TARGETS), _sorted(CONTRACT_GAZE))


func test_unknown_names_fall_back_to_neutral() -> void:
	assert_eq(BlackjackPeople.face_params(""), BlackjackPeople.face_params("neutral"))
	assert_false(BlackjackPeople.GESTURES.has("no_such_gesture"))


func test_every_mood_has_a_complete_parameter_set() -> void:
	for m in CONTRACT_MOODS:
		var p := BlackjackPeople.face_params(m)
		for k in BlackjackPeople.FACE_KEYS:
			assert_true(p.has(k), "%s lacks %s" % [m, k])
		assert_eq(p.size(), BlackjackPeople.FACE_KEYS.size(), m)
	assert_eq(BlackjackPeople.face_params("no_such_mood"), BlackjackPeople.face_params("neutral"))


func test_moods_differ_from_each_other() -> void:
	for i in CONTRACT_MOODS.size():
		for j in range(i + 1, CONTRACT_MOODS.size()):
			assert_true(BlackjackPeople.face_params(CONTRACT_MOODS[i]) != BlackjackPeople.face_params(CONTRACT_MOODS[j]), "%s equals %s" % [CONTRACT_MOODS[i], CONTRACT_MOODS[j]])


func test_blend_endpoints_and_middle() -> void:
	var a := BlackjackPeople.face_params("neutral")
	var b := BlackjackPeople.face_params("laugh")
	assert_eq(BlackjackPeople.blend(a, b, 0.0), a)
	assert_eq(BlackjackPeople.blend(a, b, 1.0), b)
	var mid := BlackjackPeople.blend(a, b, 0.5)
	assert_near(float(mid["mouth_open"]), (float(a["mouth_open"]) + float(b["mouth_open"])) * 0.5, 0.0001)
	var bm: Vector2 = mid["brow_l"]
	assert_near(bm.x, ((a["brow_l"] as Vector2).x + (b["brow_l"] as Vector2).x) * 0.5, 0.0001)


func test_card_ranks_and_sizes() -> void:
	for suit in 4:
		for rank in range(1, 14):
			assert_true(BlackjackDraw.rank_text(rank).length() >= 1)
			assert_true(PixelGlyphs.text_width(BlackjackDraw.rank_text(rank), 1.0) > 0.0)
	assert_eq(BlackjackDraw.rank_text(1), "A")
	assert_eq(BlackjackDraw.suit_color(1), BlackjackDraw.RED)
	assert_eq(BlackjackDraw.suit_color(3), BlackjackDraw.BLACK)
	assert_eq(BlackjackDraw.rank_text(10), "10")
	assert_eq(BlackjackDraw.rank_text(13), "K")
	assert_true(BlackjackDraw.card_size(1.0).x >= 24.0 and BlackjackDraw.card_size(1.0).y >= 34.0)
	assert_true(BlackjackDraw.card_size(1.0, 0.7).x < BlackjackDraw.card_size(1.0).x)


func _inside(r: Rect2, size: Vector2) -> bool:
	return r.position.x >= -0.5 and r.position.y >= -0.5 and r.end.x <= size.x + 0.5 and r.end.y <= size.y + 0.5


func test_points_lie_inside_the_canvas() -> void:
	for s: Vector2 in SIZES:
		var rect := Rect2(Vector2.ZERO, s)
		for seat in BlackjackDraw.SEATS:
			assert_true(rect.has_point(BlackjackDraw.seat_pos(seat, s)), "seat %s %s" % [seat, s])
			for i in 7:
				var c := BlackjackDraw.card_spot(seat, i, s)
				var half := BlackjackDraw.card_size(BlackjackDraw.unit(s), BlackjackDraw.seat_card_scale(seat)) * 0.5
				assert_true(_inside(Rect2(c - half, half * 2.0), s), "card %s %d %s" % [seat, i, s])
		for i in 7:
			var c := BlackjackDraw.card_spot("player", i, s)
			var half := BlackjackDraw.card_size(BlackjackDraw.unit(s)) * 0.5
			assert_true(_inside(Rect2(c - half, half * 2.0), s), "player card %d %s" % [i, s])
		for p: Vector2 in [BlackjackDraw.deck_spot(s), BlackjackDraw.bet_spot(s), BlackjackDraw.pile_origin(s), BlackjackDraw.dealer_tray_spot(s)]:
			assert_true(rect.has_point(p), "spot %s %s" % [p, s])
		assert_true(BlackjackDraw.pockets_spot(s).y > s.y, "pockets are off the bottom edge")
		assert_true(_inside(BlackjackDraw.pile_rect(s), s))
		for id in BlackjackDraw.TARGETS:
			assert_true(_inside(BlackjackDraw.target_rect(id, s, 7), s), "target %s %s" % [id, s])
			assert_true(_inside(BlackjackDraw.target_rect(id, s, 2), s), "target %s %s" % [id, s])
		assert_eq(BlackjackDraw.target_rect("exit", s), BlackjackDraw.exit_rect(s))


func test_targets_are_big_enough_and_apart() -> void:
	for s: Vector2 in SIZES:
		var u := BlackjackDraw.unit(s)
		var phone_scale := 250.0 / s.y
		for n in [2, 3, 5, 7]:
			var rects := {}
			for id in BlackjackDraw.TARGETS:
				var r := BlackjackDraw.target_rect(id, s, n)
				rects[id] = r
				assert_true(r.size.x >= 30.0 * u - 0.5 and r.size.y >= 30.0 * u - 0.5, "%s is %s at %s" % [id, r.size, s])
				assert_true(r.size.x * phone_scale >= 72.0 - 0.5 and r.size.y * phone_scale >= 72.0 - 0.5, "%s is %s px on the phone at %s" % [id, r.size * phone_scale, s])
			for i in BlackjackDraw.TARGETS.size():
				for j in range(i + 1, BlackjackDraw.TARGETS.size()):
					var a: Rect2 = rects[BlackjackDraw.TARGETS[i]]
					var b: Rect2 = rects[BlackjackDraw.TARGETS[j]]
					assert_false(a.intersects(b), "%s overlaps %s with %d cards at %s" % [BlackjackDraw.TARGETS[i], BlackjackDraw.TARGETS[j], n, s])


func test_player_cards_keep_corners_visible_and_clear_of_pile_and_bet() -> void:
	for s: Vector2 in SIZES:
		var u := BlackjackDraw.unit(s)
		var corner := BlackjackDraw.rank_corner_width(u)
		var half := BlackjackDraw.card_size(u) * 0.5
		var pile := BlackjackDraw.pile_rect(s)
		var bet := Rect2(BlackjackDraw.bet_spot(s) - Vector2(14.0, 6.0) * u, Vector2(28.0, 12.0) * u)
		for i in 7:
			var c := BlackjackDraw.card_spot("player", i, s)
			if i > 0:
				var prev := BlackjackDraw.card_spot("player", i - 1, s)
				assert_true(c.x - prev.x >= corner - 0.5, "spacing %f < corner %f at %s" % [c.x - prev.x, corner, s])
			var r := Rect2(c - half, half * 2.0)
			assert_false(r.intersects(pile), "card %d hits the pile at %s" % [i, s])
			assert_false(r.intersects(bet), "card %d hits the bet at %s" % [i, s])
