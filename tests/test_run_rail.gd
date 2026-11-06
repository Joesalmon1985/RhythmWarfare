extends TestCase
## The rails inside the run: every scene's journey data sits on real waypoints, a pass steps up the good rail and a hold along the bad one, two holds start the queasy
## look, the bottom plays the sick beat, a pass walks back, moves start in the cue-free guard and last 2 to 4 bars, every block has a glance, the passage frame and the
## lit exits are functions of song time.

const BPM := 174.0
const BEAT := 60.0 / 174.0


func _data() -> RunData:
	var d := RunData.load_default()
	assert_eq(d.errors, [], "run data validates")
	return d


func _rail(id: String) -> RunRail:
	var d := _data()
	var r := RunRail.new()
	r.setup(id, d.nodes[id], BPM)
	return r


func _kinds(actions: Array, name: String) -> Array:
	return actions.filter(func(a: Dictionary) -> bool: return a["action"] == name)


func test_every_rail_sits_on_real_waypoints_and_every_step_has_a_route() -> void:
	var d := _data()
	for id in d.nodes:
		var n: Dictionary = d.nodes[id]
		var map := StoryMap.load_chapter(str(n["map"]))
		assert_eq(map.errors, [], "%s map is clean" % id)
		var r := _rail(id)
		var named: Array = [r.home, r.arrive]
		for p in r.good:
			named.append(p["to"])
		for p in r.bad:
			named.append(p["to"])
		for dir in r.exits:
			named.append(r.exits[dir])
		for wid in named:
			if str(wid) != "":
				assert_true(map.has_waypoint(str(wid)), "%s: waypoint %s exists in %s" % [id, wid, n["map"]])
		for chain in [[r.home] + r.good.map(func(p: Dictionary) -> String: return p["to"]), [r.home] + r.bad.map(func(p: Dictionary) -> String: return p["to"])]:
			for i in range(1, chain.size()):
				var a: Dictionary = map.waypoint(str(chain[i - 1]))
				var b: Dictionary = map.waypoint(str(chain[i]))
				var route := map.route(a["at"], str(a["sector"]), b["at"], str(b["sector"]))
				assert_true((route["points"] as PackedVector2Array).size() >= 2, "%s: a route from %s to %s" % [id, chain[i - 1], chain[i]])
		for dir in r.exits:  # a doorway for every route of the node
			assert_true((n["next"] as Array).any(func(e: Dictionary) -> bool: return e["dir"] == dir), "%s: exit %s matches a route" % [id, dir])
		for e in n["next"]:
			assert_true(r.exits.has(e["dir"]), "%s: the %s route has a lit doorway" % [id, e["dir"]])


func test_the_authored_rails() -> void:
	var want := {  # scene -> [good, bad]: the Warehouse floor keeps the chapter's rail, every other scene's rail stays within reach of its own room
		# (the reactor's core, the arena's gate, the corridor's east end and the quiet room's far end faced a wall from arm's length: docs/art/CAMERA_CLEARANCE.md)
		"warehouse": [["steps", "stage", "balcony", "booth"], ["floor_edge", "corridor", "cubicle"]],
		"warehouse.bar": [["bar_taps", "bar_end"], ["bar_door", "floor_bar"]],
		"warehouse.booth": [["booth_decks"], ["stage", "steps"]],
		"mothership": [["deck_ramp", "deck_dais"], ["deck_edge", "deck_sw_corner"]],
		"mothership.reactor": [["catwalk_mid", "catwalk_bridge"], ["catwalk_door", "medbay"]],
		"underworld": [["gate_dais"], ["arena_edge", "tier_l_in"]],
		"underworld.pit": [["pit_edge", "pit_stage"], ["pit_rim_e", "court_in"]],
		"hospital": [["ward_chair", "ward_door"], ["bed_corner", "bed_far"]],
		"hospital.garden": [["garden_edge", "bandstand"], ["garden_south", "garden_sw"]],
		"ward": [["bars_in", "day_stage_in"], ["day_edge", "day_corner"]],
		"ward.corridor": [["corr_mid"], ["treat", "quiet"]],
		"hospital_late.quiet": [["quiet"], ["quiet_door", "corridor_in"]],
		"ward_late.exit": [["day_centre", "day_stage_in"], ["day_corner", "bars_in"]],
	}
	for id in want:
		var r := _rail(id)
		assert_eq(r.good.map(func(p: Dictionary) -> String: return p["to"]), want[id][0], "%s good rail" % id)
		assert_eq(r.bad.map(func(p: Dictionary) -> String: return p["to"]), want[id][1], "%s bad rail" % id)


func test_passes_climb_the_good_rail_and_stay_at_the_top() -> void:
	var r := _rail("warehouse")
	var notes: Array = []
	var places: Array = []
	var roles: Array = []
	for b in 6:
		var acts := r.step(true, float(b) * 16.0 * BEAT + 12.5 * BEAT, notes)
		places.append(r.place())
		roles.append(r.role)
		if b < 4:
			assert_eq(_kinds(acts, "player_move").size(), 1, "block %d moves one place" % b)
		else:
			assert_eq(_kinds(acts, "player_move").size(), 0, "at the top it stays")
	assert_eq(places, ["steps", "stage", "balcony", "booth", "booth", "booth"])
	assert_eq(roles, ["dancer", "on_stage", "on_stage", "dj", "dj", "dj"], "the role follows the place")
	assert_true(r.at_top())


func test_holds_walk_the_bad_rail_with_queasy_and_the_sick_beat_then_a_pass_walks_back() -> void:
	var r := _rail("warehouse")
	var notes: Array = []
	var t := 12.5 * BEAT
	var a1 := r.step(false, t, notes)
	assert_eq(r.place(), "floor_edge")
	assert_eq(_kinds(a1, "fx_queasy").size(), 0, "one hold is not yet queasy")
	assert_eq(r.role, "queasy")
	var a2 := r.step(false, t + 16.0 * BEAT, notes)
	assert_eq(r.place(), "corridor")
	assert_true(_kinds(a2, "fx_queasy").size() == 1 and float((_kinds(a2, "fx_queasy")[0]["args"])["amount"]) > 0.0, "two holds in a row start the queasy look")
	var a3 := r.step(false, t + 32.0 * BEAT, notes)
	assert_eq(r.place(), "cubicle")
	assert_eq(_kinds(a3, "sick_beat").size(), 1, "the bottom of the bad rail plays the sick beat")
	assert_eq(r.role, "sick")
	var a4 := r.step(false, t + 48.0 * BEAT, notes)
	assert_eq(_kinds(a4, "player_move").size(), 0, "held at the bottom: no new move")
	assert_eq(_kinds(a4, "sick_beat").size(), 0, "and the sick beat is not replayed")
	var back: Array = []
	for i in 3:
		var acts := r.step(true, t + float(5 + i) * 16.0 * BEAT, notes)
		back.append(r.place())
		assert_eq(_kinds(acts, "player_move").size(), 1)
		if i == 0:
			assert_true(_kinds(acts, "player_role").any(func(a: Dictionary) -> bool: return (a["args"] as Dictionary)["role"] == "recovered"), "recovered on the way back")
			assert_true(_kinds(acts, "fx_queasy").any(func(a: Dictionary) -> bool: return float((a["args"] as Dictionary)["amount"]) == 0.0), "the queasy look clears")
	assert_eq(back, ["corridor", "floor_edge", "floor_centre"], "a pass walks back toward the floor")
	assert_eq(r.role, "dancer", "and the floor makes a dancer again")


func test_a_hold_on_the_good_rail_drops_to_the_bad_rail() -> void:
	var r := _rail("mothership")
	r.step(true, 12.5 * BEAT, [])
	r.step(true, 28.5 * BEAT, [])
	assert_eq(r.place(), "deck_dais")
	r.step(false, 44.5 * BEAT, [])
	assert_eq(r.place(), "deck_edge")
	assert_eq(r.pos, -1)


func test_moves_start_on_the_decision_beat_and_last_two_to_four_bars() -> void:
	for id in _data().nodes:
		var r := _rail(id)
		var t := 12.5 * BEAT
		for passed in [true, true, false, false, false, true, true, true, true]:
			for a in r.step(passed, t, []):
				if a["action"] == "player_move":
					var bars := float((a["args"] as Dictionary)["bars"])
					assert_true(bars >= 2.0 and bars <= 4.0, "%s: a move lasts %.1f bars" % [id, bars])
					assert_true(fposmod(float(a["t0"]) / BEAT, 16.0) >= 12.0, "%s: starts in the cue-free guard" % id)
			t += 16.0 * BEAT
		assert_true(r.visited.size() == 9)


func test_dense_cues_shorten_a_move_but_never_below_two_bars() -> void:
	var notes: Array = []
	for i in 80:  # eight notes a bar from beat 0: dense everywhere
		notes.append({"time": float(i) * BEAT / 2.0})
	assert_true(RunRail.move_is_dense(notes, 0.0, 4.0, BPM))
	assert_eq(RunRail.pick_bars(4.0, notes, 0.0, BPM), 2.0)
	var sparse: Array = []
	for i in 10:
		sparse.append({"time": float(i) * BEAT * 2.0})
	assert_false(RunRail.move_is_dense(sparse, 0.0, 4.0, BPM))
	assert_eq(RunRail.pick_bars(4.0, sparse, 0.0, BPM), 4.0)
	assert_eq(RunRail.pick_bars(9.0, sparse, 0.0, BPM), 4.0, "never more than four bars")
	assert_eq(RunRail.pick_bars(1.0, sparse, 0.0, BPM), 2.0, "never fewer than two")
	# only the second bar dense: a move over it is allowed at four bars only when at most half of them are dense
	var half: Array = []
	for i in 8:
		half.append({"time": 4.0 * BEAT + float(i) * BEAT / 2.0})
	assert_false(RunRail.move_is_dense(half, 0.0, 4.0, BPM))


func test_every_block_has_a_glance_and_the_glances_vary() -> void:
	for id in _data().nodes:
		var r := _rail(id)
		var seen := {}
		var strolls := 0
		for blk in 12:
			var acts := r.ambient(float(blk) * 16.0 * BEAT, blk / 4 + 1, blk % 4, [])
			var looks := _kinds(acts, "player_look")
			assert_eq(looks.size(), 1, "%s block %d has a glance" % [id, blk])
			seen[JSON.stringify(looks[0]["args"])] = true
			strolls += _kinds(acts, "player_walk").size()
		assert_true(seen.size() >= 3, "%s: the glances vary from block to block (%d kinds)" % [id, seen.size()])
		assert_true(strolls >= 3, "%s: some blocks add an in-room walk (%d)" % [id, strolls])


## Visual polish: in the hotspot window (the last block) the head stays on the room, so the hotspots are things in the picture and not beacons at its edge.
func test_the_glance_of_the_hotspot_window_never_looks_up_or_far_away() -> void:
	for id in _data().nodes:
		var r := _rail(id)
		for ph in 6:
			var acts := r.ambient(48.0 * BEAT, ph + 1, 3, [])
			for a in _kinds(acts, "player_look"):
				assert_eq(float(a["args"]["pitch"]), 0.0, "%s: no look at the ceiling in the window" % id)
				assert_true(absf(float(a["args"]["by"])) <= RunRail.WINDOW_GLANCE_DEG, "%s: a small turn at most" % id)
			for w in _kinds(acts, "player_walk"):
				assert_false((w["args"] as Dictionary).has("turn"), "%s: an in-room walk in the window does not turn away" % id)


func test_arriving_in_a_new_world_is_a_cut_to_the_doorway_then_a_walk_home() -> void:
	var r := _rail("hospital")
	var t0 := 64.0 * BEAT
	var acts := r.arrival(t0, [])
	var moves := _kinds(acts, "player_move")
	assert_eq(moves.size(), 2)
	assert_eq((moves[0]["args"] as Dictionary)["to"], "ward_door", "in at the doorway")
	assert_true(bool((moves[0]["args"] as Dictionary).get("cut", false)))
	assert_eq((moves[1]["args"] as Dictionary)["to"], "bed", "then into the start waypoint")
	assert_true(float(moves[1]["t0"]) < t0 and fposmod(float(moves[1]["t0"]) / BEAT, 16.0) >= 12.0, "the walk starts in the guard before the downbeat")
	# on the real stage the walk ends at home
	var map := StoryMap.load_chapter("hospital")
	var pl := StoryPlayer.new()
	pl.setup(map, BPM)
	for a in acts:
		pl.apply_action(a)
	assert_eq(pl.pose_at(t0 - 1.5 * BEAT)["sector"], "ward", "hidden behind the closed frame it is at the doorway")
	assert_eq(pl.pose_at(t0 + 20.0 * BEAT)["sector"], "bed")


func test_every_path_inside_a_world_is_a_door_walk_without_a_cut() -> void:
	var d := _data()
	var walks := 0
	for id in d.nodes:
		var n: Dictionary = d.nodes[id]
		for e in n["next"]:
			var to := str(e["to"])
			var tn: Dictionary = d.nodes[to]
			if str(tn["world"]) != str(n["world"]):
				continue
			walks += 1
			var r := _rail(id)
			var map := StoryMap.load_chapter(str(n["map"]))
			var pl := StoryPlayer.new()
			pl.setup(map, BPM)
			pl.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": str(n["waypoint"]), "bars": 0.5, "style": "walk", "cut": true}})
			var t_leave := 61.0 * BEAT
			var acts := r.leave(t_leave, str(tn["rail"]["arrive"]) if str(tn["rail"].get("arrive", "")) != "" else str(tn["waypoint"]), [])
			assert_eq(_kinds(acts, "player_move").size(), 1, "%s > %s: one walk" % [id, to])
			for a in acts:
				assert_true(fposmod(float(a["t0"]) / BEAT, 16.0) >= 12.0, "%s > %s starts in the cue-free guard" % [id, to])
				assert_false(bool((a["args"] as Dictionary).get("cut", false)), "a plain door walk, not a cut")
				pl.apply_action(a)
			var tr := _rail(to)
			var arrive := str(tr.arrive) if tr.arrive != "" else tr.home
			var end: Dictionary = pl.pose_at(t_leave + 4.0 * 4.0 * BEAT + BEAT)
			assert_eq(pl.errors, [], "%s > %s: the map has a route through the door" % [id, to])
			assert_eq(str(end["sector"]), str(map.waypoint(arrive)["sector"]), "%s > %s: ends at the arrival place" % [id, to])
			# the camera is never in a sector of another map room it should not cross: every sampled pose is in a sector of the map
			var tt := t_leave
			while tt < t_leave + 16.0 * BEAT:
				assert_false(map.sector(str(pl.pose_at(tt)["sector"])).is_empty(), "%s > %s: the walk stays inside the map" % [id, to])
				tt += 0.5
	assert_true(walks >= 25, "paths inside the worlds: %d" % walks)


func test_a_scene_started_without_a_door_walk_walks_in_on_the_downbeat() -> void:
	var r := _rail("warehouse.bar")
	var acts := r.door_walk(64.0 * BEAT, [], false)
	var moves := _kinds(acts, "player_move")
	assert_eq(moves.size(), 1)
	assert_eq((moves[0]["args"] as Dictionary)["to"], "bar_door", "to the arrival place")
	var walked := r.door_walk(64.0 * BEAT, [], true)
	assert_eq(_kinds(walked, "player_move").size(), 0, "already on the way: only the role")
	assert_eq(_kinds(walked, "player_role").size(), 1)


func test_the_passage_frame_closes_before_the_downbeat_and_opens_after_it() -> void:
	var swap := 64.0 * BEAT
	assert_eq(RunPassage.aperture(swap - 4.0 * BEAT, swap, BEAT), 1.0, "open before beat 62")
	assert_true(RunPassage.aperture(swap - 1.0 * BEAT, swap, BEAT) < 0.8, "closing")
	assert_near(RunPassage.aperture(swap, swap, BEAT), RunPassage.MIN_OPEN, 1e-6, "shut to the doorway on the downbeat")
	assert_true(RunPassage.aperture(swap + 1.0 * BEAT, swap, BEAT) > RunPassage.MIN_OPEN, "opening")
	assert_eq(RunPassage.aperture(swap + 3.0 * BEAT, swap, BEAT), 1.0, "fully open again")
	assert_eq(RunPassage.aperture(swap, -1.0, BEAT), 1.0, "no passage under way: open")
	var prev := 1.0
	var t := swap - 2.0 * BEAT
	while t < swap:  # monotone closing
		var a := RunPassage.aperture(t, swap, BEAT)
		assert_true(a <= prev + 1e-9)
		prev = a
		t += 0.01
	var view := Vector2(800, 300)
	assert_true(RunPassage.doorway(view, RunPassage.MIN_OPEN).size.x < view.x * 0.2)
	assert_eq(RunPassage.doorway(view, 1.0), Rect2(Vector2.ZERO, view))


