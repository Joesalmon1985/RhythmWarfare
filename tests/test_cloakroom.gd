extends TestCase
## The cloakroom same/different activity (docs/briefs/BEDSIT_RAVES_BRIEF.md section 5): the trial generator, the scoring against the immediately previous symbol, one answer per
## trial, the fast and slow processing times in song time, completion and its flag, leaving and returning, and (with the engine and the run scene, the way
## test_activity_modes drives a replace activity) the rhythm suspended while it is seated, the pad strip reaching its controls and not the pads, and judging resuming on the boundary.

const BEAT := 60.0 / 174.0
const CFG_PATH := "res://content/minigames/cloakroom.json"
const TMP_SAVE := "user://test_cloakroom_save.json"
const FIX := "res://tests/fixtures/cloakroom_scene/"
const THEMES := ["space", "magic", "dinos", "transport"]

var _saved: RunProgress


func _cfg(extra := {}) -> Dictionary:
	var c: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CFG_PATH))
	c.merge(extra, true)
	return c


## A fresh activity (the session store emptied first), begun at song time 0 and advanced past the demonstration and the reference: `[activity, t_awaiting_first_trial]`.
func _ready_act(theme := "space", seed_value := 7, extra := {}, skip_intro := true) -> Array:
	CloakroomSession.reset()
	var a := CloakroomActivity.new()
	a.setup({"seed": seed_value, "beat_s": BEAT, "config": _cfg(extra), "request": {"theme": theme}})
	a.begin(0.0)
	var t := 0.0
	if skip_intro:
		t = 11.0 * BEAT
		a.update(t)
	return [a, t]


func _right(a: CloakroomActivity) -> String:
	return a.expected[a.answers.size()]


func _wrong(a: CloakroomActivity) -> String:
	return "different" if _right(a) == "same" else "same"


# --- the generator ----------------------------------------------------------------------------------------------------------------

func test_the_generator_is_balanced_seeded_and_uses_four_symbols() -> void:
	for coats in [8, 7, 9, 12, 5]:
		for s in range(1, 41):
			var g := CloakroomTrials.generate(s, coats)
			var seq: Array = g["seq"]
			var exp: Array = g["expected"]
			assert_eq(seq.size(), coats + 1, "reference plus one symbol per coat")
			assert_eq(exp.size(), coats)
			var same := exp.filter(func(x: Variant) -> bool: return x == "same").size()
			assert_true(absi(same - (coats - same)) <= 1, "matches and non-matches within one: coats %d seed %d: %d same" % [coats, s, same])
			var flags: Array = exp.map(func(x: Variant) -> bool: return x == "same")
			assert_true(CloakroomTrials.longest_run(flags) <= 3, "no run longer than three: coats %d seed %d" % [coats, s])
			for i in coats:
				assert_eq(exp[i], CloakroomTrials.answer_for(seq[i], seq[i + 1]), "expected is the comparison with the immediately previous symbol")
			assert_true(seq.all(func(x: int) -> bool: return x >= 0 and x < 4))
	assert_eq(CloakroomTrials.generate(5, 8), CloakroomTrials.generate(5, 8), "the same seed gives the same sequence")
	assert_true(CloakroomTrials.generate(5, 8)["seq"] != CloakroomTrials.generate(6, 8)["seq"], "another seed another sequence")
	# over many seeds every one of the four symbols turns up
	var seen := {}
	for s in range(1, 30):
		for x: int in CloakroomTrials.generate(s, 8)["seq"]:
			seen[x] = true
	assert_eq(seen.size(), 4)


func test_every_theme_has_four_distinct_symbols_drawn_at_64_px() -> void:
	var all := {}
	for th: String in THEMES:
		var a := CloakroomActivity.new()
		a.setup({"seed": 1, "config": _cfg(), "request": {"theme": th}})
		assert_eq(a.symbol_ids.size(), 4, th)
		var imgs := {}
		for id: String in a.symbol_ids:
			assert_false(all.has(id), "%s is used by one theme only" % id)
			all[id] = true
			var img := CloakroomArt.symbol_image(id)
			assert_eq(img.get_size(), Vector2i(64, 64), "%s is a 64 px sprite" % id)
			var opaque := 0
			for y in 64:
				for x in 64:
					if img.get_pixel(x, y).a > 0.5:
						opaque += 1
			assert_true(opaque > 300 and opaque < 3600, "%s has a body: %d opaque pixels" % [id, opaque])
			imgs[img.get_data().hex_encode()] = true
			assert_true(CloakroomArt.symbol_texture(id) != null)
		assert_eq(imgs.size(), 4, "%s: four different pictures" % th)
		assert_eq(a.symbol_ids, CloakroomArt.DEFAULTS[th], "the brief's symbols for %s" % th)
		var gen := CloakroomTrials.generate(a.rng_seed, a.coats, 0.5, a.symbol_ids.size())
		assert_eq(a.seq, gen["seq"], "the activity's sequence is the generator's for the run seed")
	# the contract fixture's symbols are honoured where the art knows them, else the theme's own four stand
	var fx: Dictionary = ContractShapes.load_fixture("theme_space.json")
	assert_eq(CloakroomArt.symbols_for("space", fx["cloakroom_symbols"]), ["planet", "rocket", "star", "comet"], "ringed_planet is the planet; crescent and ufo are not drawn: the defaults")
	assert_eq(CloakroomArt.symbols_for("magic", [{"id": "wand"}, {"id": "crown"}, {"id": "potion"}, {"id": "unicorn"}]), ["wand", "crown", "potion", "unicorn"])


# --- the state machine ------------------------------------------------------------------------------------------------------------

func test_the_demonstration_then_the_reference_then_the_trials() -> void:
	var r := _ready_act("space", 7, {}, false)
	var a: CloakroomActivity = r[0]
	var s := a.state()
	assert_eq(s["phase"], "demo")
	assert_eq(s["demo_steps"], 3, "a reference and two auto-played trials")
	assert_eq(s["demo_answer"], "", "the reference first")
	assert_eq(a.targets().filter(func(x: String) -> bool: return x == "same"), [], "nothing to answer yet")
	a.update(2.1 * BEAT)
	assert_eq(a.state()["demo_answer"], "same", "first demo trial: a match")
	assert_eq(a.state()["current"], a.state()["previous"])
	a.update(5.1 * BEAT)
	assert_eq(a.state()["demo_answer"], "different", "second: a non-match")
	assert_true(a.state()["current"] != a.state()["previous"])
	a.update(8.1 * BEAT)
	assert_eq(a.state()["phase"], "reference")
	assert_eq(a.state()["current"], a.symbol_ids[a.seq[0]], "the first symbol is the unscored reference")
	assert_eq(a.state()["previous"], "")
	assert_eq(a.state()["trial"], -1)
	assert_false(a.tap("same", 8.5 * BEAT), "no answer to the reference")
	assert_eq(a.answers.size(), 0)
	a.update(10.2 * BEAT)
	s = a.state()
	assert_eq(s["phase"], "await")
	assert_eq(s["trial"], 0)
	assert_eq(s["current"], a.symbol_ids[a.seq[1]])
	assert_eq(s["previous"], a.symbol_ids[a.seq[0]])
	assert_true(s["show_previous"], "the first three trials show the previous symbol")
	assert_true("same" in a.targets() and "different" in a.targets())
	assert_eq(a.controls().map(func(c: Dictionary) -> String: return str(c["id"])), ["same", "different"])
	assert_true(a.controls().all(func(c: Dictionary) -> bool: return str(c["label"]) == ""), "no words on the controls")


func test_scoring_always_compares_with_the_immediately_previous_symbol() -> void:
	var r := _ready_act()
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	assert_true(a.tap(_wrong(a), t), "a wrong answer to trial 0")
	assert_false(bool(a.answers[0]["correct"]))
	t += 3.01
	a.update(t)
	assert_eq(a.state()["phase"], "await")
	assert_eq(a.state()["trial"], 1)
	# the next comparison is symbol 2 against symbol 1 (the symbol shown last), not against the last correct one or the reference
	assert_eq(a.state()["previous"], a.symbol_ids[a.seq[1]])
	assert_eq(a.state()["current"], a.symbol_ids[a.seq[2]])
	var want := "same" if a.seq[2] == a.seq[1] else "different"
	assert_eq(_right(a), want)
	assert_true(a.tap(want, t))
	assert_true(bool(a.answers[1]["correct"]), "right against the previous symbol")
	assert_eq(a.correct_count(), 1)
	# a different run: answer every trial wrongly, then check each expected answer is the comparison with the preceding symbol
	var r2 := _ready_act("magic", 21)
	var b: CloakroomActivity = r2[0]
	var tb: float = r2[1]
	for i in b.coats:
		var exp_cmp := "same" if b.seq[i] == b.seq[i + 1] else "different"
		assert_eq(b.expected[i], exp_cmp)
		assert_true(b.tap(_wrong(b), tb))
		tb += 3.0
		b.update(tb)
	assert_eq(b.correct_count(), 0)


func test_repeated_taps_score_one_trial_once() -> void:
	var r := _ready_act()
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	var right := _right(a)
	assert_true(a.tap(right, t))
	for k in 6:
		assert_false(a.tap(right if k % 2 == 0 else _wrong(a), t + 0.05 + 0.1 * float(k)), "taps after the answer are ignored")
	assert_eq(a.answers.size(), 1, "one answer for the trial")
	assert_eq(a.ignored_taps, 6)
	assert_eq(a.correct_count(), 1)
	# taps during the demonstration are ignored as well
	var d := _ready_act("space", 7, {}, false)[0] as CloakroomActivity
	assert_false(d.tap("same", 0.5))
	assert_eq(d.answers.size(), 0)
	assert_eq(d.ignored_taps, 1)
	# and a stray target is not an answer
	assert_false(a.tap("pad1", t + 5.0))


func test_fast_and_slow_processing_is_measured_in_song_time() -> void:
	var r := _ready_act()
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	assert_true(a.tap(_right(a), t))
	assert_eq(a.state()["phase"], "process")
	assert_eq(a.state()["reaction"], "happy")
	a.update(t + 0.99)
	assert_eq(a.state()["phase"], "process", "still handing the coat over just before a second")
	assert_false(a.tap("same", t + 0.99), "no answer while the coat is processed")
	a.update(t + 1.0)
	assert_eq(a.state()["phase"], "await", "a right answer takes one second")
	var t2 := t + 1.0
	assert_true(a.tap(_wrong(a), t2))
	assert_eq(a.state()["reaction"], "impatient")
	a.update(t2 + 2.99)
	assert_eq(a.state()["phase"], "process")
	a.update(t2 + 3.0)
	assert_eq(a.state()["phase"], "await", "a wrong answer takes three seconds")
	assert_near(a.state()["phase_t0"], t2 + 3.0, 1e-9, "the next trial starts exactly where the processing ended (no wall clock)")
	# configurable
	var r3 := _ready_act("space", 7, {"fast_s": 0.5, "slow_s": 2.0})
	var c: CloakroomActivity = r3[0]
	c.tap(_right(c), r3[1])
	c.update(float(r3[1]) + 0.5)
	assert_eq(c.state()["phase"], "await")
	# a long gap between frames takes the transitions in order
	var r4 := _ready_act()
	var d: CloakroomActivity = r4[0]
	d.tap(_right(d), r4[1])
	d.update(float(r4[1]) + 30.0)
	assert_eq(d.state()["phase"], "await")
	assert_near(d.state()["phase_t0"], float(r4[1]) + 1.0, 1e-9)


func test_eight_coats_complete_and_set_the_flag() -> void:
	var r := _ready_act("dinos", 11)
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	assert_eq(a.coats, 8)
	for i in 8:
		assert_eq(a.state()["remaining"], 8 - i)
		assert_true(a.tap(_right(a), t))
		t += 1.0
		a.update(t)
	assert_eq(a.state()["phase"], "payoff", "every coat processed: the payoff")
	assert_eq(a.state()["remaining"], 0, "the rail is empty")
	assert_false(a.is_done())
	assert_eq(a.state()["reaction"], "happy")
	t += 4.0 * BEAT
	a.update(t)
	assert_true(a.is_done())
	assert_eq(a.done_reason(), "done")
	var res := a.result()
	assert_eq(ContractShapes.activity_result(res), [], "the contract's shape")
	assert_true(bool(res["completed"]))
	assert_eq(res["score"], 8)
	assert_eq(res["flags_to_set"], ["rave.dinos.cloakroom_done"], "the rave's cloakroom flag")
	assert_false(CloakroomSession.has("dinos/cloakroom"), "a finished cloakroom leaves nothing behind")
	# with every answer wrong it still completes (the workload is finite), only slower
	var r2 := _ready_act("space", 3)
	var b: CloakroomActivity = r2[0]
	var tb: float = r2[1]
	for i in 8:
		b.tap(_wrong(b), tb)
		tb += 3.0
		b.update(tb)
	tb += 4.0 * BEAT
	b.update(tb)
	assert_true(b.is_done() and bool(b.result()["completed"]))
	assert_eq(b.result()["score"], 0)
	assert_true(tb - float(r2[1]) > 24.0, "slow work took 3 s a coat")
	# fewer coats by configuration
	var r3 := _ready_act("space", 3, {"coats": 3})
	var c: CloakroomActivity = r3[0]
	var tc: float = r3[1]
	for i in 3:
		c.tap(_right(c), tc)
		tc += 1.0
		c.update(tc)
	c.update(tc + 4.0 * BEAT)
	assert_true(c.is_done())
	assert_eq(c.seq.size(), 4)
	# the request's flag list wins when it carries one
	var r4 := _ready_act("magic", 3, {"coats": 1, "flags_on_complete": ["rave.{theme}.cloakroom_done", "met_the_coat_girl"]})
	var d: CloakroomActivity = r4[0]
	d.tap(_right(d), r4[1])
	d.update(float(r4[1]) + 1.0 + 4.0 * BEAT)
	assert_eq(d.result()["flags_to_set"], ["rave.magic.cloakroom_done", "met_the_coat_girl"])


func test_leaving_and_returning_keeps_the_queue() -> void:
	var r := _ready_act("magic", 5)
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	for i in 3:
		a.tap(_right(a) if i != 1 else _wrong(a), t)
		t += 3.0
		a.update(t)
	var seq: Array = a.seq.duplicate()
	var expected: Array = a.expected.duplicate()
	var answers: Array = a.answers.duplicate(true)
	a.request_leave(t + 0.5)
	assert_true(a.is_done())
	assert_eq(a.done_reason(), "left")
	var res := a.result()
	assert_false(bool(res["completed"]))
	assert_eq(res["flags_to_set"], [], "no flag for half a job")
	assert_eq(ContractShapes.activity_result(res), [])
	assert_true(CloakroomSession.has("magic/cloakroom"), "the progress is kept in the session store")
	# the return: a NEW activity object (the controller builds one per request), another seed, the same theme
	var b := CloakroomActivity.new()
	b.setup({"seed": 999, "beat_s": BEAT, "config": _cfg(), "request": {"theme": "magic"}})
	assert_true(b.state()["restored"])
	assert_eq(b.seq, seq, "the same symbols")
	assert_eq(b.expected, expected)
	b.begin(100.0)
	var s := b.state()
	assert_eq(b.answers, answers, "the answers so far")
	assert_eq(s["remaining"], 5, "five coats still queued")
	assert_eq(s["phase"], "await", "straight to the next coat, no second demonstration")
	assert_eq(s["trial"], 3)
	assert_eq(s["previous"], b.symbol_ids[seq[3]], "compared with the symbol before it")
	assert_eq(b.correct_count(), 2)
	# another rave is not touched
	var c := CloakroomActivity.new()
	c.setup({"seed": 999, "beat_s": BEAT, "config": _cfg(), "request": {"theme": "space"}})
	assert_false(c.state()["restored"])
	assert_eq(c.answers.size(), 0)
	# finishing the rest completes it, and the store is cleared
	var tb := 100.0
	for i in 5:
		assert_true(b.tap(_right(b), tb))
		tb += 1.0
		b.update(tb)
	b.update(tb + 4.0 * BEAT)
	assert_true(b.is_done() and bool(b.result()["completed"]))
	assert_eq(b.result()["flags_to_set"], ["rave.magic.cloakroom_done"])
	assert_false(CloakroomSession.has("magic/cloakroom"))
	# leaving mid-demonstration, mid-processing, and a changed workload
	var d := _ready_act("space", 5, {}, false)[0] as CloakroomActivity
	d.request_leave(1.0)
	var e := CloakroomActivity.new()
	e.setup({"seed": 1, "beat_s": BEAT, "config": _cfg(), "request": {"theme": "space"}})
	e.begin(5.0)
	assert_eq(e.state()["phase"], "demo", "left before the demonstration finished: it plays again")
	var f := _ready_act("space", 5)
	var fa: CloakroomActivity = f[0]
	fa.tap(_right(fa), f[1])
	fa.request_leave(float(f[1]) + 0.2)
	var g := CloakroomActivity.new()
	g.setup({"seed": 1, "beat_s": BEAT, "config": _cfg({"coats": 5}), "request": {"theme": "space"}})
	assert_false(g.state()["restored"], "a different workload does not inherit the old queue")
	var h := CloakroomActivity.new()
	h.setup({"seed": 1, "beat_s": BEAT, "config": _cfg(), "request": {"theme": "space"}})
	h.begin(50.0)
	assert_eq(h.answers.size(), 1, "the coat in the middle of processing was dealt with")
	assert_eq(h.state()["phase"], "await")
	# leaving after the last answer is the work done
	var last := _ready_act("space", 5, {"coats": 1})
	var la: CloakroomActivity = last[0]
	la.tap(_right(la), last[1])
	la.request_leave(float(last[1]) + 0.3)
	assert_eq(la.done_reason(), "done")
	assert_eq(la.result()["flags_to_set"], ["rave.space.cloakroom_done"])
	CloakroomSession.reset()


func test_an_interrupted_activity_keeps_or_drops_its_progress_as_it_should() -> void:
	var r := _ready_act("space", 5)
	var a: CloakroomActivity = r[0]
	a.tap(_right(a), r[1])
	a.interrupt("host", float(r[1]) + 0.1)
	assert_eq(a.done_reason(), "host")
	assert_true(CloakroomSession.has("space/cloakroom"))
	var r2 := _ready_act("space", 5)
	var b: CloakroomActivity = r2[0]
	b.tap(_right(b), r2[1])
	b.interrupt("run_over", float(r2[1]) + 0.1)
	assert_false(CloakroomSession.has("space/cloakroom"), "a run that ends clears it")
	assert_false(bool(b.result()["completed"]))
	assert_eq(b.result()["reason"], "run_over")


func test_exit_targets_leave_by_a_door() -> void:
	CloakroomSession.reset()
	var a := CloakroomActivity.new()
	a.setup({"seed": 7, "beat_s": BEAT, "config": _cfg(), "request": {"theme": "space"}, "exits": [{"id": "x", "route": "space.floor", "default": true}]})
	a.begin(0.0)
	assert_true("exit:space.floor" in a.targets())
	assert_false(a.tap("exit:elsewhere", 1.0), "not one of this room's doors")
	assert_true(a.tap("exit", 1.0), "the bare exit is the default door")
	assert_eq(a.done_reason(), "left")
	assert_eq(a.done_route(), "space.floor")
	CloakroomSession.reset()


func test_the_registry_knows_the_activity_and_it_draws_nothing_itself() -> void:
	assert_true(CloakroomActivity.new().make_view() == null, "no canvas view: the stage draws the room")
	assert_false(FileAccess.file_exists("res://src/minigames/cloakroom/cloakroom_view.gd"), "the close-up layer is gone (ruling 38)")
	var c := MinigameController.new(null)
	c.load_registry()
	assert_true(c.is_registered("cloakroom"), "content/minigames/cloakroom.json is in the registry")
	assert_eq(ActivityMode.of_config(c.config_of("cloakroom")), ActivityMode.Mode.REPLACE)
	assert_eq(ContractShapes.activity_config(c.config_of("cloakroom")), [], "and fits the contract")
	# a request built from data seats it with the theme's keys
	var theme: Dictionary = ContractShapes.load_fixture("theme_space.json")
	var req := RunMinigameHost.build_request("cloakroom", c.config_of("cloakroom"), "space", theme, "rave.space", "space_floor")
	assert_eq(ContractShapes.activity_request(req), [])
	CloakroomSession.reset()
	assert_true(c.request("cloakroom", 0.0, 1.0, [], req))
	var act: CloakroomActivity = c.activity
	assert_eq(act.theme, "space")
	assert_eq(act.coats, 8)
	c.update(1.0)
	assert_eq(c.state, "active")
	assert_true(c.owns_strip(1.0))
	assert_eq(c.input_mode(1.0), ActivityMode.Mode.REPLACE)
	c.request_leave(2.0)
	c.update(2.0)
	assert_eq(c.last_result["reason"], "left", "(the plain controller: leaving ends the activity at once)")
	CloakroomSession.reset()


func test_the_hotspot_row_for_a_raves_cloakroom_commits_the_activity() -> void:
	# the shape a rave's cloakroom entry takes (content/run/hotspots/<scene>.json): an object hotspot whose success outcome is {"activity": "cloakroom"}; the host builds the request from the theme
	var row: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/bedsit/cloakroom_hotspot_example.json"))
	assert_eq(row["kind"], "object")
	assert_eq((row["on_success"] as Dictionary)["activity"], "cloakroom")
	assert_eq(row["id"], "{theme}.cloakroom")
	assert_eq(row["scene"], "rave.{theme}")
	for th: String in THEMES:
		var cfg := _cfg()
		var req := RunMinigameHost.build_request(str((row["on_success"] as Dictionary)["activity"]), cfg, th, {"stations": {"cloakroom": {"waypoint": "cloak_view"}}}, str(row["scene"]).replace("{theme}", th), "home")
		assert_eq(req["return_pose"], "cloak_view")
		assert_eq(req["theme"], th)
		assert_eq(req["config"]["flags_on_complete"], ["rave.%s.cloakroom_done" % th])


# --- with the engine: the rhythm is suspended while it is seated ----------------------------------------------------------------------

func _engine() -> RunEngine:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin("warehouse")
	return e


func test_while_seated_the_rhythm_is_suspended_and_judging_resumes_on_the_boundary() -> void:
	CloakroomSession.reset()
	var e := _engine()
	var c := MinigameController.new(e, null, 7)
	c.register("cloakroom", CloakroomActivity, _cfg())
	var events: Array = []
	var st := {"t_tap": -1.0, "seat_energy": -1.0, "done_t": -1.0}
	var t := 0.0
	var pressed := {}
	while t < 200.0 * BEAT and not e.over:
		if t >= 29.0 * BEAT and c.started == 0:
			assert_true(c.request("cloakroom", t, 32.0 * BEAT), "requested")
		if st["seat_energy"] < 0.0 and t >= 32.0 * BEAT:
			st["seat_energy"] = e.energy
		var evs := e.update(t)
		for ev: Dictionary in evs:
			if str(ev["kind"]) == "block_result":
				c.on_block_result(bool(ev["passed"]), float(ev["t"]))
		events.append_array(evs)
		c.update(t)
		if c.state == "active" and c.activity != null:
			var act: CloakroomActivity = c.activity
			if act.state()["phase"] == "await" and t >= float(st["t_tap"]):
				c.tap(_right(act), t)
				st["t_tap"] = t + 0.2
		# the player plays nothing while it is seated and every cue otherwise
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if pressed.has(i) or float(n["time"]) > t:
				continue
			var plays := float(n["time"]) < 32.0 * BEAT or (c.resume_t >= 0.0 and float(n["time"]) >= c.resume_t - 1e-6)
			pressed[i] = plays and not e.judge.is_withdrawn(i)
			if pressed[i]:
				e.press(int(n["pad"]), float(n["time"]))
		t += 1.0 / 60.0
	assert_eq(c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "suspend").size(), 1, "the request suspended the rhythm")
	assert_eq(c.log.filter(func(l: Dictionary) -> bool: return l["kind"] in ["wobble", "interrupt"]).size(), 0, "no wobble, no fall")
	assert_eq(e.judge.misses, 0, "no misses while the activity owned the controls")
	var res: Array = c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "resume")
	assert_eq(res.size(), 1, "done once, resumed once")
	var b1 := float(res[0]["at"])
	assert_true(b1 >= float(res[0]["t"]) + 4.0 * BEAT - 1e-6, "at least a bar of lead-in after it was done")
	var seated: Array = events.filter(func(b: Dictionary) -> bool: return str(b["kind"]) == "block_result" and float(b["t"]) - e._decision_beat() * e.beat_s >= 32.0 * BEAT - 1e-6 and float(b["t"]) - e._decision_beat() * e.beat_s < b1 - 1e-6)
	assert_true(seated.size() >= 3, "several blocks went by while it was seated")
	for b: Dictionary in seated:
		assert_true(bool(b.get("suspended", false)) and bool(b.get("neutral", false)), "suspended and neutral")
		assert_near(float(b["energy"]), float(st["seat_energy"]), 1e-9, "no energy change")
	var first: Array = events.filter(func(b: Dictionary) -> bool: return str(b["kind"]) == "block_result" and absf(float(b["t"]) - e._decision_beat() * e.beat_s - b1) < 1e-6)
	assert_eq(first.size(), 1)
	assert_false(bool(first[0].get("suspended", false)), "judging resumes on the boundary")
	assert_true(bool(first[0]["passed"]), "and the player's play passes")
	assert_eq(c.state, "")
	assert_false(e.hold)
	assert_eq(ContractShapes.activity_result(c.last_result), [])
	assert_eq(c.last_result["flags_to_set"], [], "(no theme in this run scene: no flag)")
	assert_true(bool(c.last_result["completed"]))


# --- the run scene: the pad strip belongs to the controls ----------------------------------------------------------------------------------

func _scene(bot: String) -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_MINIGAME_TAPS", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS"]:
		OS.set_environment(k, "")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_in_the_scene_strip_taps_reach_the_controls_not_the_pads_and_judging_resumes() -> void:
	CloakroomSession.reset()
	# the bot plays phase 1 and, in the two blocks of phase 2 that the activity covers, nothing (the controls own the strip), then everything
	var d := _scene("blocks:1111" + "00" + "11111111111111111")
	var scene: Node = d["scene"]
	scene.minigames.register("cloakroom", CloakroomActivity, _cfg({"coats": 2}))
	for h in scene.data.hotspots["warehouse"]:
		if h["id"] == "warehouse.dancer":
			h["on_success"] = {"activity": "cloakroom"}
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	_run_to(scene, 64.5 * BEAT)
	var mg: MinigameController = scene.minigames
	assert_eq(mg.state, "active")
	var act: CloakroomActivity = mg.activity
	var e: RunEngine = scene.engine
	assert_true(scene._mg.owns_strip(), "the controls own the strip")
	var layer: RunActivityInput = scene._mg.controls_layer
	assert_true(layer != null and layer.ids == ["same", "different"], "SAME and DIFFERENT")
	assert_false(scene.pad_view.visible)
	var pad1: Rect2 = scene.pad_view.button_rects()[1]
	var pad2: Rect2 = scene.pad_view.button_rects()[2]
	var pad3: Rect2 = scene.pad_view.button_rects()[3]
	var pad4: Rect2 = scene.pad_view.button_rects()[4]
	var strays0: int = e.judge.strays
	var misses0: int = e.judge.misses
	var energy0: float = e.energy
	# during the demonstration a strip tap reaches the controls (and is ignored by the activity), never a pad
	assert_eq(scene.dispatch_tap(pad1.get_center()), "activity_controls")
	assert_eq(act.answers.size(), 0)
	assert_eq(act.ignored_taps, 1)
	_run_to(scene, 76.5 * BEAT)  # (the demonstration and the reference are over)
	assert_eq(act.state()["phase"], "await")
	var left_right := "same" if _right(act) == "same" else "different"
	var centre_of := {"same": pad2.get_center(), "different": pad3.get_center()}
	assert_eq(scene.dispatch_tap(centre_of[left_right]), "activity_controls", "the left pair is SAME, the right pair DIFFERENT: either pad of a pair works")
	assert_eq(act.answers.size(), 1)
	assert_true(bool(act.answers[0]["correct"]))
	assert_eq(scene.dispatch_tap(pad4.get_center()), "activity_controls", "a second tap while the coat is processed is the controls' and scores nothing")
	assert_eq(act.answers.size(), 1, "no double scoring")
	assert_eq(e.judge.strays, strays0, "no pad was pressed")
	scene._on_button_pressed(1, 0)
	assert_eq(e.judge.strays, strays0, "a pad press that got through is refused")
	# the second coat
	_run_to(scene, scene._vt + 1.2)
	assert_eq(act.state()["phase"], "await")
	var ok2 := pad1.get_center() if _right(act) == "same" else pad4.get_center()
	scene.dispatch_tap(ok2)
	assert_eq(act.answers.size(), 2)
	assert_eq(e.judge.misses, misses0, "zero misses while seated")
	assert_near(e.energy, energy0, 1e-9, "zero energy change")
	# done: the payoff, then the boundary
	_run_to(scene, scene._vt + 1.0 + 4.0 * BEAT + 0.3)
	assert_eq(mg.state, "resuming")
	var b1: float = mg.resume_t
	assert_true(b1 > scene._vt)
	_run_to(scene, b1 + 14.0 * BEAT)
	assert_eq(mg.state, "")
	assert_false(e.hold)
	assert_true(scene.pad_view.visible and scene.lane_input.enabled, "the pads are back")
	var blocks: Array = (scene.event_log as Array).filter(func(x: Dictionary) -> bool: return x["kind"] == "block_result" and absf(float(x["t"]) - e._decision_beat() * e.beat_s - b1) < 1e-6)
	assert_eq(blocks.size(), 1)
	assert_false(bool(blocks[0].get("suspended", false)), "the first block on the boundary is judged")
	assert_eq(e.judge.misses, misses0, "still no miss")
	_free(d)
	CloakroomSession.reset()


# --- the staging (ruling 38): things, crowd actors and feedback as data ----------------------------------------------------------------------

func _staged(theme := "space", extra := {}) -> Array:
	CloakroomSession.reset()
	var w := WorldThings.new()
	var a := CloakroomActivity.new()
	a.setup({"seed": 7, "beat_s": BEAT, "config": _cfg(extra), "request": {"theme": theme}, "world": w})
	a.begin(0.0)
	a.update(11.0 * BEAT)
	return [a, 11.0 * BEAT, w]


func _frames(w: WorldThings, prefix: String) -> Array:
	return w.things.filter(func(t: Dictionary) -> bool: return str(t["id"]).begins_with(prefix))


func test_the_things_show_one_coat_per_coat_still_to_come_and_the_symbols() -> void:
	var r := _staged()
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	var w: WorldThings = r[2]
	var coats := _frames(w, "cloak_coat_")
	assert_eq(coats.size(), 8, "eight coats in the room")
	assert_eq(coats.filter(func(c: Dictionary) -> bool: return int(c["frame"]) < 4).size(), 7, "seven on the rail, one carried by the customer")
	assert_true(int(w.thing("cloak_coat_0")["frame"]) >= 4 and int(w.thing("cloak_coat_0")["frame"]) < 8, "the customer's coat is the carried row")
	var cur := w.thing("cloak_symbol_current")
	assert_eq(int(cur["frame"]), a.symbol_ids.find(a.state()["current"]), "the tag's frame is the current symbol")
	assert_eq(cur["sprite"], "cloak_symbols_space")
	var prev := w.thing("cloak_symbol_previous")
	assert_eq(int(prev["frame"]), 4 + a.symbol_ids.find(a.state()["previous"]), "the previous symbol, the faded row")
	# trials 0 to 2 show the previous symbol, trial 3 on do not
	for i in 4:
		assert_eq(not w.thing("cloak_symbol_previous").is_empty(), i < 3, "previous symbol at trial %d" % i)
		a.tap(_right(a), t)
		t += 1.0
		a.update(t)
	# a handover moves the coat across the counter and then it is gone
	a.tap(_right(a), t)
	a.update(t + 0.3)
	var c4: Dictionary = w.thing("cloak_coat_4")
	assert_true(int(c4["frame"]) >= 8, "handed over: the third row")
	var at1: Array = c4["at"]
	a.update(t + 0.7)
	assert_true((w.thing("cloak_coat_4")["at"] as Array) != at1, "it moves in song time")
	a.update(t + 1.0)
	assert_true(w.thing("cloak_coat_4").is_empty(), "handled: gone")
	assert_eq(_frames(w, "cloak_coat_").size(), 3, "three coats left")
	# at the end the rail is empty
	for i in 3:
		t += 1.0
		a.update(t)
		a.tap(_right(a), t)
	a.update(t + 1.0)
	assert_eq(a.state()["phase"], "payoff")
	assert_eq(_frames(w, "cloak_coat_").size(), 0, "the rail of coats is empty")


func test_the_crowd_is_directed_by_state_and_feedback_is_asked_for() -> void:
	var r := _staged()
	var a: CloakroomActivity = r[0]
	var t: float = r[1]
	var w: WorldThings = r[2]
	assert_eq(w.state_of("customer_0"), "waiting")
	assert_eq(w.state_of("attendant"), "idle")
	a.tap(_right(a), t)
	assert_eq(w.state_of("customer_0"), "happy")
	assert_eq(w.state_of("attendant"), "happy")
	assert_eq(w.feedback_log[-1], {"thing": "cloak_symbol_current", "kind": "tick", "t": t})
	t += 1.0
	a.update(t)
	assert_eq(w.state_of("customer_1"), "waiting", "the next customer steps up")
	a.tap(_wrong(a), t)
	assert_eq(w.state_of("customer_1"), "impatient")
	var imp: Dictionary = w.people_log.filter(func(p: Dictionary) -> bool: return p["state"] == "impatient")[0]
	assert_near(float(imp["dur"]), 3.0, 1e-9, "for the slow processing time")
	assert_eq(w.feedback_log[-1]["kind"], "cross")
	assert_eq(w.feedback_log.size(), 2, "one cue per answer")
	a.tap("same", t + 0.5)
	assert_eq(w.feedback_log.size(), 2, "an ignored tap asks for nothing")
	# the payoff
	CloakroomSession.reset()
	var r2 := _staged("magic", {"coats": 1})
	var b: CloakroomActivity = r2[0]
	var w2: WorldThings = r2[2]
	b.tap(_right(b), r2[1])
	b.update(float(r2[1]) + 1.0)
	assert_eq(w2.state_of("attendant"), "clap")
	assert_eq(w2.state_of("customer_0"), "hands_up")
	assert_eq(w2.feedback_log[-1]["thing"], "cloak_counter")
	assert_eq(w2.feedback_log[-1]["kind"], "glow")
	for e: Dictionary in w2.people_log:
		assert_true(e["state"] in ["idle", "waiting", "happy", "impatient", "clap", "hands_up"], "only the states the crowd knows")


func test_the_test_scene_map_and_sprite_sheets_carry_the_things() -> void:
	var m: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIX + "map.json"))
	var ids := (m["things"] as Array).map(func(x: Dictionary) -> String: return str(x["id"]))
	for need in ["cloak_counter", "cloak_rail", "cloak_tag_board"]:
		assert_true(need in ids, "map piece %s" % need)
	assert_true(ids.all(func(i: String) -> bool: return i.begins_with("cloak_")), "the activity's prefix")
	var poly: PackedVector2Array = PackedVector2Array((m["sectors"][0]["polygon"] as Array).map(func(p: Array) -> Vector2: return Vector2(p[0], p[1])))
	var dir := FIX + "assets/story/cloak_test/sprites/"
	for p: Dictionary in m["things"]:
		assert_true(FileAccess.file_exists(dir + str(p["sprite"]) + ".png"), "sprite for %s" % p["id"])
	var r := _staged("dinos")
	var w: WorldThings = r[2]
	assert_true(w.things.size() >= 9)
	for t: Dictionary in w.things:
		var at: Array = t["at"]
		assert_true(Geometry2D.is_point_in_polygon(Vector2(at[0], at[1]), poly), "%s stands inside the room" % t["id"])
		assert_eq(t["sector"], "cloak")
		assert_true(float((t["size"] as Array)[0]) > 0.0 and float((t["size"] as Array)[1]) >= 0.5, "%s is big enough to read (>= 0.5 m tall)" % t["id"])
		var sheet := str(t["sprite"])
		assert_true(FileAccess.file_exists(dir + sheet + ".png"), "sheet %s" % sheet)
		var img := Image.load_from_file(ProjectSettings.globalize_path(dir + sheet + ".png"))
		var cols := 4
		var rows := img.get_height() / 64 if sheet.begins_with("cloak_symbols") else 3
		assert_true(int(t["frame"]) >= 0 and int(t["frame"]) < cols * rows, "%s frame %d is in its sheet" % [t["id"], int(t["frame"])])
	for th: String in THEMES:
		assert_true(FileAccess.file_exists(dir + "cloak_symbols_%s.png" % th), "a symbol sheet for %s" % th)
