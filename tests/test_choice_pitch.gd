extends TestCase
## A choice viewpoint's steady pitch (CONTRACTS.md 3, docs/engine/GEOGRAPHY_WORLDS.md, rulings 35 and 39): a rail place with "choice": true may author `pitch` (degrees, negative looks
## down, default 0). The run's choice hold (RunJourney: player_hold `hold: "window"`) carries it; StoryPlayer tips the head to it by the time the window opens, holds it still through
## the window (no bob, no drift, no glance), comes back to it after a herald's look, and lets it go with the walk-off. A viewpoint that authors none is exactly as before (pitch 0).
## The fixture (tests/fixtures/choice_pitch) is two one-scene geography worlds on night_one: pitch_low authors -14, pitch_plain nothing.

const FIX := "res://tests/fixtures/choice_pitch"
const TMP := "user://test_choice_pitch"
const BEAT := 60.0 / 174.0


func _read(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _write(path: String, v: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(v, "\t"))
	f.close()


## The main run with the fixture's worlds added.
func _data(tag: String) -> RunData:
	var run := _read(RunData.RUN_PATH)
	var music := _read(RunData.MUSIC_PATH)
	var fr := _read(FIX + "/run.json")
	var fm := _read(FIX + "/music.json")
	run["worlds"] = (run["worlds"] as Array) + (fr["worlds"] as Array)
	run["nodes"] = (run["nodes"] as Array) + (fr["nodes"] as Array)
	music["nodes"] = (music["nodes"] as Array) + (fm["nodes"] as Array)
	var dir := TMP + "/" + tag
	_write(dir + "/run.json", run)
	_write(dir + "/music.json", music)
	return RunData.load_files(dir + "/run.json", dir + "/music.json", RunData.PACKS_DIR, 1, RunData.ARRANGEMENTS_DIR, dir + "/hotspots")


## The run driven the way RunPlay drives it (as tests/test_geography.gd does): a perfect player, `picks` tapped at `tap_beat` of each window ([] stays).
func _drive(d: RunData, start: String, picks: Array, until_phase: int, tap_beat := 50.0) -> Dictionary:
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin(start)
	var j := RunJourney.new(d)
	j.look_heralds = false
	var actions: Array = []
	var pressed := {}
	var door_phase := -1
	var tap_phase := -1
	var t := 0.0
	while e.phase_n < until_phase and not e.over and t < 900.0:
		if e.window_open and tap_phase != e.phase_n and e.phase_n - 1 < picks.size() and e.phase_beat_at(t) >= tap_beat:
			tap_phase = e.phase_n
			if e.choose(str(picks[e.phase_n - 1])):
				e.tap_commit(t)
		if e.window_open and door_phase != e.phase_n and e.phase_beat_at(t) >= 64.0 - RunPassage.DOOR_BEATS:
			door_phase = e.phase_n
			var to0 := e.selected_route()
			if d.nodes.has(to0) and to0 != e.node_id and str(d.nodes[to0]["world"]) != str(d.nodes[e.node_id]["world"]):
				actions.append_array(j.threshold_leave(e.t_of(64.0 - RunPassage.DOOR_BEATS), e.t_of(64.0), e.node_id, to0))
		for ev in e.update(t):
			actions.append_array(j.on_event(ev, e))
			if str(ev["kind"]) == "hotspot_commit" and door_phase != e.phase_n:
				var cw := j.commit_walk(ev, e)
				actions.append_array(cw)
				if not cw.is_empty():
					door_phase = e.phase_n
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
				if n["type"] == "hold":
					e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return {"engine": e, "journey": j, "actions": actions}


## A StoryPlayer on night_one fed the night_one actions of a drive.
func _player(actions: Array, reduced := false) -> StoryPlayer:
	var p := StoryPlayer.new()
	p.setup(StoryMap.load_chapter("night_one", false), 174.0)
	p.reduced = reduced
	for a in actions:
		if str((a as Dictionary).get("world", "night_one")) == "night_one":
			p.apply_action(a)
	return p


func _window_holds(actions: Array) -> Array:
	return actions.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_hold" and str((a["args"] as Dictionary).get("hold", "")) == "window")


func test_the_fixture_validates() -> void:
	var d := _data("ok")
	assert_eq(d.errors, [], "the main run plus the two fixture worlds validates")
	for id in ["pitch_low", "pitch_plain"]:
		assert_eq(RunRail.validate(id, d.nodes[id]["rail"]), [], "the rail of %s is clean" % id)


func test_a_pitch_is_degrees_and_only_at_a_choice_viewpoint() -> void:
	var rail: Dictionary = (_read(FIX + "/run.json")["nodes"][0] as Dictionary)["place"]["rail"]
	var bad := rail.duplicate(true)
	bad["good"][0]["pitch"] = -50
	assert_true(" ".join(PackedStringArray(RunRail.validate("x", bad))).contains("pitch is degrees"), "beyond 35 degrees is an error")
	var off := rail.duplicate(true)
	off["good"][0].erase("choice")
	off["good"][0]["hold_bars"] = 1
	assert_true(" ".join(PackedStringArray(RunRail.validate("x", off))).contains("only at a choice viewpoint"), "a pitch off a choice viewpoint is an error (it would do nothing)")


func test_the_choice_hold_holds_the_authored_pitch_still_through_the_window() -> void:
	var d := _data("low")
	var r := _drive(d, "pitch_low", [], 2)
	var holds := _window_holds(r["actions"])
	assert_eq(holds.size(), 1, "one choice window held at the viewpoint")
	if holds.size() != 1:
		return
	assert_near(float(holds[0]["args"].get("pitch", 0.0)), -14.0, 1e-9, "the hold carries the viewpoint's pitch")
	var p := _player(r["actions"])
	var w0 := float(holds[0]["t0"])
	var w1 := w0 + float(holds[0]["args"]["bars"]) * p.bar_s()
	assert_near(p.held_pitch_at(w0), -14.0, 1e-6, "tipped in by the time the window opens (beat 49)")
	var yaw0 := float(p.pose_at(w0 + BEAT)["yaw"])
	var pos0: Vector2 = p.pose_at(w0 + BEAT)["pos"]
	var worst := 0.0
	var t := w0 + BEAT
	while t <= w1 - BEAT:
		var pose := p.pose_at(t)
		worst = maxf(worst, absf(float(pose["pitch"]) + 14.0) + absf(float(pose["yaw"]) - yaw0) + (pose["pos"] as Vector2).distance_to(pos0))
		t += BEAT / 8.0
	assert_near(worst, 0.0, 1e-6, "pitch -14, yaw and position steady through the window (bob and drift on: the hold stills them)")
	assert_near(p.held_pitch_at(w1 + 0.01), 0.0, 1e-9, "after the window the held pitch is gone")
	# a herald's look over the window: the look owns the head while it holds its point, then the head comes back to the held pitch and facing
	var m := StoryMap.load_chapter("night_one", false)
	var door: Vector2 = m.waypoint("to_balcony")["at"]
	p.apply_action({"t0": w0 + 2.0 * BEAT, "action": "player_look", "args": {"face": [[door.x, door.y, 1.0]], "bars": 1.0, "turn_bars": 0.25, "release_bars": 0.25, "herald": true}})
	assert_true(float(p.face_at(w0 + 4.0 * BEAT)["w"]) > 0.99, "the herald's look holds its point")
	assert_near(p.held_pitch_at(w0 + 4.0 * BEAT), -14.0, 1e-6, "the held pitch waits under the look")
	var back := p.pose_at(w0 + 7.0 * BEAT)
	assert_near(float(back["pitch"]), -14.0, 1e-6, "after the herald's look the head is back on the held pitch")
	assert_near(float(back["yaw"]), yaw0, 1e-6, "and on the held facing")


func test_the_walk_off_releases_the_pitch() -> void:
	var d := _data("walk")
	var r := _drive(d, "pitch_low", ["pitch_plain"], 2, 52.0)
	var holds := _window_holds(r["actions"])
	var walks: Array = (r["actions"] as Array).filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move" and bool((a["args"] as Dictionary).get("threshold", false)))
	assert_eq(holds.size(), 1)
	assert_eq(walks.size(), 1, "the tap walks off")
	if holds.size() != 1 or walks.size() != 1:
		return
	var p := _player(r["actions"], true)
	var t_tap := float(walks[0]["t0"])
	assert_true(t_tap > float(holds[0]["t0"]), "the tap is inside the window")
	assert_near(float(p.pose_at(t_tap - 0.25 * BEAT)["pitch"]), -14.0, 1e-6, "held until the tap")
	assert_near(float(p.pose_at(t_tap)["pitch"]), -14.0, 1e-6, "no jump at the tap")
	var mid := float(p.pose_at(t_tap + 0.5 * BEAT)["pitch"])
	assert_true(mid > -14.0 and mid < 0.0, "eased out over a beat (%f)" % mid)
	assert_near(float(p.pose_at(t_tap + 1.01 * BEAT)["pitch"]), 0.0, 1e-6, "level once the walk-off has it")
	# a walk-off before the window opens: the held pitch eases out from where it was, with no jump
	var q := StoryPlayer.new()
	q.setup(StoryMap.load_chapter("night_one", false), 174.0)
	q.reduced = true
	q.apply_action({"t0": 49.0 * BEAT, "action": "player_hold", "args": {"bars": 11.5 / 4.0, "hold": "window", "pitch": -14.0}})
	var before := q.held_pitch_at(48.5 * BEAT)
	assert_true(before < -1.0 and before > -14.0, "half way through the tip-in (%f)" % before)
	q.end_window_holds(48.5 * BEAT)
	assert_near(q.held_pitch_at(48.5 * BEAT), before, 1e-6, "an early walk-off: no jump")
	assert_near(q.held_pitch_at(50.0 * BEAT), 0.0, 1e-6, "and gone a beat later")


func test_an_unauthored_viewpoint_holds_level() -> void:
	var d := _data("plain")
	var r := _drive(d, "pitch_plain", [], 2)
	var holds := _window_holds(r["actions"])
	assert_eq(holds.size(), 1)
	if holds.size() != 1:
		return
	assert_false((holds[0]["args"] as Dictionary).has("pitch"), "the hold is as before: no pitch key")
	var p := _player(r["actions"])
	assert_true(p._pitch_holds.is_empty(), "no held pitch")
	var w0 := float(holds[0]["t0"])
	var w1 := w0 + float(holds[0]["args"]["bars"]) * p.bar_s()
	var worst := 0.0
	var t := w0 + BEAT
	while t <= w1 - BEAT:
		worst = maxf(worst, absf(float(p.pose_at(t)["pitch"])))
		t += BEAT / 8.0
	assert_near(worst, 0.0, 1e-6, "pitch 0 through the window")
