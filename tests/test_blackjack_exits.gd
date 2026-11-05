extends TestCase
## The doors of the seated table (BlackjackExits and the view's door layer): one door per way out of the room, each inside the picture at every canvas size, clear of the three
## people, the money, the cards and the other touch targets, at least 72 px on a phone, hit-tested as "exit:<route>", placed by the side the route goes, and redrawn only when what
## it shows changes (the layer-spec rule): the light of the doors changes when leaving becomes urged, the doors themselves when one is chosen.

const BEAT := 60.0 / 174.0
const CONFIG_PATH := "res://content/minigames/blackjack.json"
const SIZES := [Vector2(640, 230), Vector2(780, 231), Vector2(320, 115), Vector2(914, 360)]
const PEOPLE_SIZES := [Vector2(640, 230), Vector2(780, 231), Vector2(320, 115)]  # the wide pictures of the game (16:9 window, phone, low setting)
const SCREENS := [Vector2(844, 250), Vector2(1280, 461)]
const EXITS := [
	{"id": "r.exit_art", "route": "r.art", "scene": "art", "world": "w", "dir": "right", "default": true},
	{"id": "r.exit_dorm", "route": "r.dorm", "scene": "dorm", "world": "w", "dir": "up", "default": false},
	{"id": "r.exit_yard", "route": "r.yard", "scene": "courtyard", "world": "w", "dir": "left", "default": false},
	{"id": "r.exit_lab", "route": "r.lab", "scene": "nowhere", "world": "w2", "dir": "up", "default": false},
]


func _rig(size: Vector2, n: int, pence := 2000, seed := 3) -> Dictionary:
	var w := RunWallet.new()
	if pence < 2000:
		w.spend(2000 - pence)
	elif pence > 2000:
		w.add(pence - 2000)
	var a := BlackjackActivity.new()
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	a.setup({"wallet": w, "seed": seed, "beat_s": BEAT, "config": cfg, "exits": EXITS.slice(0, n)})
	var clock := {"t": 0.0}
	var v := BlackjackView.new()
	v.size = size
	v.beat_s = BEAT
	v.screen_size = SCREENS[0]
	v.now_fn = func() -> float: return clock["t"]
	v.state_fn = func() -> Dictionary: return a.state()
	tree.root.add_child(v)
	v.size = size
	a.begin(0.0)
	return {"a": a, "w": w, "v": v, "clock": clock, "size": size}


func _free(rig: Dictionary) -> void:
	(rig["v"] as BlackjackView).queue_free()


func _to(rig: Dictionary, t: float) -> void:
	while float(rig["clock"]["t"]) < t - 1e-9:
		rig["clock"]["t"] = minf(float(rig["clock"]["t"]) + 1.0 / 30.0, t)
		(rig["a"] as BlackjackActivity).update(float(rig["clock"]["t"]))


func _until(rig: Dictionary, phase: String, max_s := 30.0) -> bool:
	var end := float(rig["clock"]["t"]) + max_s
	while float(rig["clock"]["t"]) < end:
		if str((rig["a"] as BlackjackActivity).state()["phase"]) == phase:
			return true
		_to(rig, float(rig["clock"]["t"]) + 1.0 / 30.0)
	return false


func _frame(rig: Dictionary) -> void:
	(rig["v"] as BlackjackView)._process(1.0 / 60.0)


func _doors_of(n: int) -> Array:
	return EXITS.slice(0, n).map(func(e: Dictionary) -> String: return "exit:" + str(e["route"]))


## Everything else on the table a door must keep clear of at `size`: the bet, deck and hand touch rectangles (a fan of up to seven cards), the money pile for every balance up to 100 pounds,
## the bet spot and the people.
func _keep_clear(size: Vector2) -> Array:
	var out: Array = [BlackjackDraw.target_rect("bet", size), BlackjackDraw.target_rect("deck", size)]
	var hand := BlackjackDraw.target_rect("hand", size, 2)
	for k in range(2, 8):
		hand = hand.merge(BlackjackDraw.target_rect("hand", size, k))
	out.append(hand)
	var pg := BlackjackView.pile_geometry(size)
	for pence in range(500, 10001, 500):
		out.append(MoneyDraw.pile_bounds(pence, pg["origin"], pg["scale"]))
		out.append(MoneyDraw.top_note_rect(pence, pg["origin"], pg["scale"]).grow(BlackjackDraw.MIN_TARGET * BlackjackDraw.unit(size) * 0.5 - 1.0))
	return out


func test_every_door_is_inside_the_picture_72_px_and_clear_of_everything_else_with_0_to_4_exits() -> void:
	for size: Vector2 in SIZES:
		var canvas := Rect2(Vector2.ZERO, size)
		var clear := _keep_clear(size)
		for n in range(0, 5):
			var lay := BlackjackExits.layout(EXITS.slice(0, n) if n > 0 else [{"route": ""}], size)
			for i in lay.size():
				var d: Dictionary = lay[i]
				var touch: Rect2 = d["touch"]
				var open: Rect2 = d["open"]
				assert_true(canvas.encloses(touch), "door %d of %d inside %s: %s" % [i, n, str(size), str(touch)])
				assert_true(touch.encloses(open), "the doorway lies inside its touch rectangle (%s)" % str(size))
				for sc: Vector2 in SCREENS:
					assert_true(touch.size.x * sc.x / size.x >= 72.0 - 0.01 and touch.size.y * sc.y / size.y >= 72.0 - 0.01, "door %d is 72 px on %s at %s" % [i, str(sc), str(size)])
				for j in range(i + 1, lay.size()):
					assert_false(touch.intersects(lay[j]["touch"]), "doors %d and %d apart at %s" % [i, j, str(size)])
				for k in clear.size():
					assert_false(touch.intersects(clear[k]), "door %d of %d clear of the table's thing %d at %s: %s vs %s" % [i, n, k, str(size), str(touch), str(clear[k])])
				if size in PEOPLE_SIZES:
					for p: Rect2 in BlackjackExits.people_rects(size):
						assert_false(touch.intersects(p), "door %d of %d clear of the people at %s: %s vs %s" % [i, n, str(size), str(touch), str(p)])


func test_the_slots_follow_the_routes_sides_and_every_exit_gets_its_own() -> void:
	assert_eq(BlackjackExits.slots_for([{"dir": "right"}, {"dir": "up"}]), ["right", "left"], "the ward's day room: the art room on the right, the dormitory on the other edge")
	assert_eq(BlackjackExits.slots_for([{"dir": "up"}, {"dir": "right"}]), ["left", "right"], "a right-hand route keeps the right edge whatever its rank")
	assert_eq(BlackjackExits.slots_for([{"dir": "left"}]), ["left"])
	assert_eq(BlackjackExits.slots_for([{"dir": "up"}]), ["right"], "one door with no side: the right edge, as the plain door")
	assert_eq(BlackjackExits.slots_for([{"dir": "right"}, {"dir": "right"}, {"dir": "up"}, {"dir": "left"}]), ["right", "far_r", "far_l", "left"])
	var four := BlackjackExits.slots_for(EXITS)
	four.sort()
	assert_eq(four, ["far_l", "far_r", "left", "right"], "four doors, four places")
	assert_eq(BlackjackExits.slots_for([]), [])


func test_live_door_targets_match_the_snapshot_and_never_overlap_the_other_targets() -> void:
	for size: Vector2 in SIZES:
		for n in [0, 1, 2, 4]:
			var rig := _rig(size, n, 2000, 3)
			_until(rig, "await_bet")
			var doors := _doors_of(n) if n > 0 else ["exit"]
			var v: BlackjackView = rig["v"]
			for phase in ["await_bet", "player_turn"]:
				if phase == "player_turn":
					(rig["a"] as BlackjackActivity).tap("bet", float(rig["clock"]["t"]))
					assert_true(_until(rig, "player_turn"), "the player's turn")
				var rects := v.target_rects()
				for id: String in doors:
					assert_true(rects.has(id), "%s live in %s at %s" % [id, phase, str(size)])
				for id: String in rects:
					for other: String in rects:
						if other < id:
							assert_false((rects[id] as Rect2).intersects(rects[other]), "%s and %s overlap in %s at %s" % [id, other, phase, str(size)])
			_free(rig)


func test_a_touch_on_a_door_is_its_exit_target_through_the_views_hit_test() -> void:
	for size: Vector2 in [Vector2(640, 230), Vector2(320, 115)]:
		var rig := _rig(size, 4)
		_until(rig, "await_bet")
		var v: BlackjackView = rig["v"]
		var rects := v.target_rects()
		for sc: Vector2 in SCREENS:
			v.screen_size = sc
			for id: String in _doors_of(4):
				var r: Rect2 = rects[id]
				for f: Vector2 in [Vector2(0.5, 0.5), Vector2(0.1, 0.1), Vector2(0.9, 0.9)]:
					var c := r.position + r.size * f
					assert_eq(v.hit(Vector2(c.x * sc.x / size.x, c.y * sc.y / size.y)), id, "%s hit at %s of its rect, %s on %s" % [id, str(f), str(size), str(sc)])
		_free(rig)
	# no exits: the plain door answers "exit"
	var rig := _rig(Vector2(640, 230), 0)
	_until(rig, "await_bet")
	var v: BlackjackView = rig["v"]
	var c: Vector2 = (v.target_rects()["exit"] as Rect2).get_center()
	assert_eq(v.hit(Vector2(c.x * v.screen_size.x / 640.0, c.y * v.screen_size.y / 230.0)), "exit")
	_free(rig)


func test_the_doors_layer_redraws_only_when_what_it_shows_changes_and_urging_changes_the_light() -> void:
	var rig := _rig(Vector2(640, 230), 2, 500, 5)  # seed 5 loses the first hand: broke after it
	var v: BlackjackView = rig["v"]
	var door: Control = v._layers["door"]
	var glow: Control = v._layers["door_glow"]
	_until(rig, "await_bet")
	_frame(rig)
	var door0: Array = door.spec
	var glow0: Array = glow.spec
	assert_false(door0.is_empty())
	assert_eq((glow0[3] as Array).size(), 2, "both doors lit while they may be touched")
	assert_false(bool(glow0[3][0][4]), "not urged with money to bet")
	(rig["a"] as BlackjackActivity).tap("bet", float(rig["clock"]["t"]))
	_until(rig, "player_turn")
	_to(rig, float(rig["clock"]["t"]) + 0.3)
	_frame(rig)
	assert_true(is_same(door.spec, door0) or door.spec == door0, "the doors are not redrawn while the hand is played")
	assert_eq(glow.spec, glow0, "nor their light")
	(rig["a"] as BlackjackActivity).tap("hand", float(rig["clock"]["t"]))
	assert_true(_until(rig, "broke", 40.0), "broke after losing the only stake")
	_frame(rig)
	assert_true(glow.spec != glow0, "urging the doors changes the light's spec")
	assert_true(bool(glow.spec[3][0][4]) and bool(glow.spec[3][1][4]), "both doors urged")
	assert_eq(door.spec, door0, "the doors themselves look the same")
	var urged_glow: Array = glow.spec
	(rig["a"] as BlackjackActivity).tap("exit:r.dorm", float(rig["clock"]["t"]))
	_frame(rig)
	assert_true(door.spec != door0, "the chosen door opens wide: redrawn")
	assert_true(bool(door.spec[2][1][4]) and not bool(door.spec[2][0][4]), "the dormitory's door is the chosen one")
	assert_true(glow.spec != urged_glow)
	assert_eq((glow.spec[3] as Array).size(), 1, "only the chosen door stays lit while leaving")
	assert_eq(float(glow.self_modulate.a), 1.0, "and its light is full")
	_free(rig)


func test_the_door_light_breathes_through_the_layers_alpha_without_redrawing() -> void:
	var rig := _rig(Vector2(640, 230), 2)
	var v: BlackjackView = rig["v"]
	_until(rig, "await_bet")
	_frame(rig)
	var glow: Control = v._layers["door_glow"]
	var spec: Array = glow.spec
	var alphas := {}
	for k in 12:
		_to(rig, float(rig["clock"]["t"]) + BEAT / 3.0)
		_frame(rig)
		alphas[snappedf(glow.self_modulate.a, 0.01)] = true
		assert_true(is_same(glow.spec, spec) or glow.spec == spec, "the light is not redrawn as it breathes")
	assert_true(alphas.size() > 3, "its strength moves")
	v.reduced = true
	_frame(rig)
	var a0 := glow.self_modulate.a
	_to(rig, float(rig["clock"]["t"]) + BEAT * 0.5)
	_frame(rig)
	assert_eq(glow.self_modulate.a, a0, "steady in reduced motion")
	_free(rig)


func test_every_scene_has_a_glimpse_and_an_unknown_one_falls_back() -> void:
	for scene in ["art", "dorm", "corridor", "courtyard", "garden", "treat", "quiet", "cafeteria", "cafe", "bar", "booth", "unheard_of", ""]:
		var g := BlackjackExits.glimpse_of(scene)
		assert_true(g.has("props") and g.has("wall"), scene)
	assert_eq(BlackjackExits.glimpse_of("unheard_of"), BlackjackExits.GLIMPSES["_"])
	assert_eq(BlackjackExits.glimpse_of("cafe"), BlackjackExits.GLIMPSES["cafeteria"])
	var plain := BlackjackExits.palette("art", "", 0.5)
	var tinted := BlackjackExits.palette("art", "#a0b494", 0.52)
	assert_true(plain["wall"] != tinted["wall"], "the map's tint colours the wall")
	assert_eq(plain["light"], tinted["light"], "the room's light stays its own")
	# the drawing is the same for the same inputs (a cached texture) and differs by what it shows
	var r := BlackjackExits.slot_rects("right", Vector2(640, 230))
	var a := BlackjackExits.door_texture(r, 1.0, "art", "", 0.5, false, false)
	assert_true(is_same(a, BlackjackExits.door_texture(r, 1.0, "art", "", 0.5, false, false)), "cached")
	var b := BlackjackExits.door_texture(r, 1.0, "dorm", "", 0.5, false, false)
	assert_true(a.get_image().get_data() != b.get_image().get_data(), "an art room and a dormitory look different")
	assert_eq(a.get_size(), b.get_size(), "and the same size: no door is bigger than another")
