extends TestCase
## The acting contract's second half (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3b and 2.3c): `cast` lines on a scene node of run.json and on a cinematic. RunEngine emits one `cast` event per line at its beat
## (pure and deterministic: the same lines at the same beats at any frame step), conditions read the crowd's energy and the world-state flags, a scene with no cast is unchanged, the validator rejects
## bad lines, and StoryCrowd.direct_actor plays them (face, look_at, chains). Also the hotspot `acting` helpers (RunActing) and the Bassment's creature table.

const WAREHOUSE_LINES := [
	{"actor": "g07", "at_beat": 0, "act": "stare", "face": "fear", "look_at": "camera", "beats": 16},
	{"actor": "g07", "at_beat": 16, "act": "plead", "face": "plea", "look_at": "camera"},
	{"actor": "d01", "at_beat": 7.5, "act": "point", "face": "resolve", "look_at": "to_bar", "beats": 12},
	{"actor": "b01", "at_beat": 32, "act": "nod"},
	{"actor": "v03", "at_beat": 48, "act": "bow", "beats": 4},
	{"actor": "g07", "at_beat": 60, "act": "cheer", "face": "cheer"},
]


## The shipped run data with its authored cast removed (stage 1d ships cast on every scene): the fixtures below inject their own lines into a bare run. `_shipped()` keeps the real data.
func _data(casts: Dictionary = {}) -> RunData:
	var d := RunData.load_default()
	assert_eq(d.errors, [], "run data validates")
	for nid in d.nodes:
		(d.nodes[nid] as Dictionary).erase("cast")
	for cn in d.cfg["cinematics"]:
		(d.cfg["cinematics"][cn] as Dictionary).erase("cast")
	for nid in casts:
		d.nodes[nid]["cast"] = casts[nid]
	return d


func _engine(d: RunData, run_flags: Dictionary = {}) -> RunEngine:
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, run_flags, {})
	e.begin("warehouse")
	return e


## Plays the run perfectly (every cue on time) on a frame step until the engine reaches phase `until_phase` (exclusive); `taps` [{beat, route}] select a hotspot like a finger (phase 1 only).
func _play(e: RunEngine, step: Callable, until_phase := 2, taps: Array = [], miss: Array = []) -> Array:
	var log: Array = []
	var t := 0.0
	var pressed := {}
	var released := {}
	var done := {}
	var guard := 0
	while e.phase_n < until_phase and not e.over and guard < 100000:
		guard += 1
		for i in taps.size():
			var tp: Dictionary = taps[i]
			if not done.has(i) and e.phase_n == 1 and t >= e.t_of(float(tp["beat"])):
				done[i] = true
				if tp.has("id"):
					e.hotspots.select(str(tp["id"]), e.block, e.window_open)
				else:
					e.hotspots.select_route(str(tp["route"]), e.block, e.window_open)
		log.append_array(e.update(t))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			var skip := false
			for m in miss:
				if int(n["phase"]) == int(m[0]) and int(n["block"]) == int(m[1]):
					skip = true
			if skip:
				continue
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += float(step.call(guard))
	return log


func _casts(log: Array) -> Array:
	return log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "cast")


func _sig(c: Dictionary) -> String:
	return "%s|%.5f|%s|%s|%s" % [c["actor"], float(c["t"]), c["act"], c["face"], c["look_at"]]


func test_every_cast_line_fires_once_in_order_at_its_beat() -> void:
	var d := _data({"warehouse": WAREHOUSE_LINES})
	var e := _engine(d)
	var log := _play(e, func(_i: int) -> float: return 1.0 / 60.0)
	var cs := _casts(log)
	assert_eq(cs.size(), WAREHOUSE_LINES.size(), "each line fired exactly once (the phase ends, the next scene has no cast)")
	var want_order := [0.0, 7.5, 16.0, 32.0, 48.0, 60.0]
	assert_eq(cs.map(func(c: Dictionary) -> float: return float(c["beat"])), want_order, "in beat order, not file order")
	for c in cs:
		assert_near(float(c["t"]), e.beat_s * float(c["beat"]), 1.0e-6, "%s fires on the clock at its beat" % c["act"])
		assert_eq(int(c["phase"]), 1)
		assert_eq(str(c["node"]), "warehouse")
		assert_eq(str(c["source"]), "scene")
	assert_eq(str(cs[0]["actor"]), "g07")
	assert_eq(str(cs[0]["face"]), "fear")
	assert_eq(str(cs[0]["look_at"]), "camera")
	assert_eq(float(cs[0]["beats"]), 16.0)
	assert_eq(float(cs[3]["beats"]), RunActing.HOLD_BEATS, "no beats given: the default hold")
	assert_eq(str(cs[3]["face"]), "", "no face given: the act's own")
	# the casts sit between the right other events: beat 16 after the first block's result, before the mix of block 1 is exceeded
	var kinds: Array = log.map(func(x: Dictionary) -> String: return str(x["kind"]))
	assert_true(kinds.find("cast") > kinds.find("phase_start"), "after the scene began")


func test_cast_events_are_the_same_at_any_frame_step_and_in_one_big_step() -> void:
	var sigs: Array = []
	var fns := {
		"30": func(_i: int) -> float: return 1.0 / 30.0,
		"60": func(_i: int) -> float: return 1.0 / 60.0,
		"variable": func(i: int) -> float: return [0.007, 0.033, 0.016, 0.051, 0.011][i % 5],
	}
	for k in fns:
		var e := _engine(_data({"warehouse": WAREHOUSE_LINES}))
		sigs.append(_casts(_play(e, fns[k])).map(_sig))
	assert_eq(sigs[0], sigs[1], "30 fps and 60 fps agree")
	assert_eq(sigs[0], sigs[2], "and a variable frame step")
	# one giant step across the whole phase: the events still carry their own scheduled times
	var e2 := _engine(_data({"warehouse": WAREHOUSE_LINES}))
	e2.update(-5.0)
	var late := _casts(e2.update(e2.beat_s * 40.0))
	assert_eq(late.map(func(c: Dictionary) -> float: return float(c["beat"])), [0.0, 7.5, 16.0, 32.0], "a stall across four lines still fires them all, in order")
	assert_near(float(late[1]["t"]), e2.beat_s * 7.5, 1.0e-6, "at their scheduled times, not the time of the frame that found them")


func test_the_cast_of_the_next_scene_fires_in_its_own_phase() -> void:
	var d := _data({"warehouse": [{"actor": "g07", "at_beat": 1, "act": "nod"}], "warehouse.bar": [{"actor": "b01", "at_beat": 0, "act": "offer", "face": "happy"}, {"actor": "b01", "at_beat": 63, "act": "nod"}]})
	var e := _engine(d)
	var log := _play(e, func(_i: int) -> float: return 1.0 / 60.0, 3)
	var cs := _casts(log)
	assert_eq(cs.map(func(c: Dictionary) -> String: return "%d:%s:%s" % [int(c["phase"]), c["node"], str(snappedf(float(c["beat"]), 0.01))]), ["1:warehouse:1.0", "2:warehouse.bar:0.0", "2:warehouse.bar:63.0"], "each scene's lines fire in its own phase")
	var bar_t0 := 0.0
	for ev in log:
		if str(ev["kind"]) == "phase_start" and int(ev["phase"]) == 2:
			bar_t0 = float(ev["t"])
	assert_near(float(cs[1]["t"]), bar_t0, 1.0e-6, "beat 0 of the next scene is its downbeat")
	assert_near(float(cs[2]["t"]), bar_t0 + 63.0 * e.beat_s, 1.0e-6, "beat 63 fires before the scene ends")


func test_conditions_energy_and_flags() -> void:
	var lines := [
		{"actor": "g07", "at_beat": 2, "act": "cover_face", "face": "grief", "if_energy_below": 40},
		{"actor": "g07", "at_beat": 3, "act": "cheer", "face": "cheer", "if_energy_above": 40},
		{"actor": "d01", "at_beat": 4, "act": "bow", "if_flags_all": ["met_king"]},
		{"actor": "d01", "at_beat": 5, "act": "block", "if_flags_none": ["met_king"]},
		{"actor": "b01", "at_beat": 6, "act": "nod", "if_flags_all": ["a", "b"], "if_energy_above": 10},
	]
	for case in [
		{"energy": 30.0, "flags": {}, "want": ["cover_face", "block"]},
		{"energy": 70.0, "flags": {}, "want": ["cheer", "block"]},
		{"energy": 70.0, "flags": {"met_king": true}, "want": ["cheer", "bow"]},
		{"energy": 70.0, "flags": {"met_king": true, "a": true, "b": true}, "want": ["cheer", "bow", "nod"]},
		{"energy": 70.0, "flags": {"a": true}, "want": ["cheer", "block"]},
		{"energy": 40.0, "flags": {}, "want": ["block"]},
	]:
		var e := _engine(_data({"warehouse": lines}), case["flags"])
		e.update(-1.0)
		e.energy = float(case["energy"])  # (the first block's decision is at beat 13: the lines under test are all before it)
		var cs := _casts(e.update(e.beat_s * 7.0))
		assert_eq(cs.map(func(c: Dictionary) -> String: return str(c["act"])), case["want"], "energy %s flags %s" % [str(case["energy"]), str(case["flags"].keys())])
	# the conditions see the energy AT the line's beat, after the block decisions before it: a missed first block lowers it by the time beat 16 comes
	var e2 := _engine(_data({"warehouse": [{"actor": "g07", "at_beat": 16, "act": "cover_face", "if_energy_below": 60}, {"actor": "g07", "at_beat": 17, "act": "cheer", "if_energy_above": 60}]}))
	var log := _play(e2, func(_i: int) -> float: return 1.0 / 60.0, 2, [], [[1, 0]])
	var acts := _casts(log).map(func(c: Dictionary) -> String: return str(c["act"]))
	assert_eq(acts, ["cover_face"], "a missed first block: below the start energy at beat 16")


func test_a_scene_without_cast_is_unchanged() -> void:
	var plain := _play(_engine(_data()), func(_i: int) -> float: return 1.0 / 60.0, 3)
	assert_eq(_casts(plain).size(), 0, "no cast lines, no cast events")
	# a cast on a scene the run never visits changes nothing about the scenes it does
	var other := _play(_engine(_data({"mothership": WAREHOUSE_LINES.slice(0, 2)})), func(_i: int) -> float: return 1.0 / 60.0, 3)
	assert_eq(other.size(), plain.size(), "the same number of events")
	for i in plain.size():
		if str(plain[i]["kind"]) in ["judge", "cues"]:
			continue
		assert_eq(JSON.stringify(plain[i]), JSON.stringify(other[i]), "event %d (%s) is the same" % [i, plain[i]["kind"]])


func test_a_cinematics_cast_fires_relative_to_the_commit() -> void:
	var d := _data()
	var cine: Dictionary = d.cfg["cinematics"]["warehouse.stagger_entry_right"]
	cine["cast"] = [{"actor": "g07", "at_beat": 1, "act": "recoil", "face": "fear"}, {"actor": "b01", "at_beat": 2.5, "act": "laugh", "face": "laugh", "look_at": "camera", "beats": 4}]
	var e := _engine(d)
	var taps := [{"beat": 52.0, "route": "warehouse.bar"}]
	var log := _play(e, func(_i: int) -> float: return 1.0 / 60.0, 2, taps, [[1, 3]])  # the last block is missed: the failure outcome (its cinematic) plays
	var commit: Dictionary = {}
	for ev in log:
		if str(ev["kind"]) == "hotspot_commit":
			commit = ev
	assert_false(commit.is_empty(), "the hotspot committed")
	assert_false(bool(commit["outcome"]["success"]))
	assert_eq((commit["outcome"]["cinematic"] as Dictionary).get("cast", []).size(), 2, "the outcome's cinematic carries its cast")
	var cs := _casts(log)
	assert_eq(cs.size(), 2)
	assert_eq(cs.map(func(c: Dictionary) -> String: return str(c["source"])), ["cinematic", "cinematic"])
	assert_near(float(cs[0]["t"]), float(commit["t"]) + e.beat_s * 1.0, 1.0e-6, "one beat after the commit")
	assert_near(float(cs[1]["t"]), float(commit["t"]) + e.beat_s * 2.5, 1.0e-6)
	assert_eq(str(cs[0]["name"]), "warehouse.stagger_entry_right")
	# a success does not play the failure's cinematic
	var d2 := _data()
	d2.cfg["cinematics"]["warehouse.stagger_entry_right"]["cast"] = cine["cast"]
	var ok := _casts(_play(_engine(d2), func(_i: int) -> float: return 1.0 / 60.0, 2, taps))
	assert_eq(ok.size(), 0, "a clean run takes the success outcome: no stagger, no cast")


# --- the shipped data (stage 1d): every authored line is valid and fires once at its beat -----------------------------------------------

## The engine begun at any scene of the shipped run (its own cast, nothing injected), played one phase with every cue hit (`miss` empty) or with the blocks named missed.
func _shipped_phase(d: RunData, node_id: String, miss: Array, taps: Array = [], run_flags: Dictionary = {}) -> Dictionary:
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, run_flags, {})
	e.begin(node_id)
	var log := _play(e, func(_i: int) -> float: return 1.0 / 30.0, 2, taps, miss)
	log = log.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) != "cast" or int(ev["phase"]) == 1)  # (the update that ends the phase also starts the next scene: its beat 0 is not this phase's)
	return {"engine": e, "log": log}


const ALL_MISSED := [[1, 0], [1, 1], [1, 2], [1, 3]]


func test_every_scene_of_the_run_has_two_to_four_cast_lines_that_validate() -> void:
	var d := RunData.load_default()
	assert_eq(d.errors, [], "the shipped run data (cast and acting included) validates")
	var scenes := 0
	for nid in d.nodes:
		var lines: Array = d.nodes[nid].get("cast", [])
		scenes += 1
		assert_true(lines.size() >= 2 and lines.size() <= 4, "%s has %d cast lines (2 to 4)" % [nid, lines.size()])
		for ln in lines:
			assert_true(float(ln["at_beat"]) >= 0.0 and float(ln["at_beat"]) <= 63.0, "%s: at_beat in the phase" % nid)
			assert_false((ln as Dictionary).has("text"), "%s: nothing but acts, faces and looks" % nid)
	assert_eq(scenes, 36, "all 36 scenes")


func test_every_shipped_scene_cast_line_fires_once_in_order_at_its_beat() -> void:
	var d := RunData.load_default()
	var fired_total := 0
	for nid in d.nodes:
		var lines: Array = d.nodes[nid]["cast"]
		var seen := {}  # line index -> true when it fired in a perfect phase or in a missed one
		for miss in [[], ALL_MISSED]:
			var r := _shipped_phase(d, nid, miss)
			var e: RunEngine = r["engine"]
			var last_t := -1.0
			var in_play := {}
			for c in _casts(r["log"]):
				assert_eq(str(c["node"]), nid, "%s: the cast of the scene" % nid)
				assert_eq(int(c["phase"]), 1)
				assert_eq(str(c["source"]), "scene")
				assert_true(float(c["t"]) >= last_t, "%s: in time order" % nid)
				last_t = float(c["t"])
				var idx := int(c["index"])
				var ln: Dictionary = lines[idx]
				assert_near(float(c["t"]), e.beat_s * float(ln["at_beat"]), 1.0e-6, "%s line %d fires on the clock at its beat %s" % [nid, idx, str(ln["at_beat"])])
				assert_eq(str(c["actor"]), str(ln["actor"]))
				assert_eq(str(c["act"]), str(ln["act"]))
				assert_false(in_play.has(idx), "%s line %d fires once per phase" % [nid, idx])
				in_play[idx] = true
				seen[idx] = true
				fired_total += 1
			for i in lines.size():  # a line with no condition always fires
				var ln2: Dictionary = lines[i]
				var conditional := false
				for k in ["if_energy_below", "if_energy_above", "if_flags_all", "if_flags_none"]:
					conditional = conditional or ln2.has(k)
				if not conditional:
					assert_true(in_play.has(i), "%s line %d (no condition) fired" % [nid, i])
		for i in lines.size():
			assert_true(seen.has(i), "%s line %d is reachable: it fires in a perfect phase or a missed one" % [nid, i])
	assert_true(fired_total > 150, "%d cast events over the 72 phases" % fired_total)


func test_the_energy_conditions_hold_at_their_beat() -> void:
	var d := RunData.load_default()
	var checked := 0
	for nid in d.nodes:
		for i in (d.nodes[nid]["cast"] as Array).size():
			var ln: Dictionary = d.nodes[nid]["cast"][i]
			if not ln.has("if_energy_below") and not ln.has("if_energy_above"):
				continue
			for miss in [[], ALL_MISSED]:
				var r := _shipped_phase(d, nid, miss)
				var e: RunEngine = r["engine"]
				var fired := false
				for c in _casts(r["log"]):
					if int(c["index"]) == i:
						fired = true
				var energy := 60.0  # the run's start energy, then each block's result up to the line's beat
				for ev in r["log"]:
					if str(ev["kind"]) == "block_result" and float(ev["t"]) <= e.beat_s * float(ln["at_beat"]):
						energy = float(ev["energy"])
				var want := true
				if ln.has("if_energy_below"):
					want = want and energy < float(ln["if_energy_below"])
				if ln.has("if_energy_above"):
					want = want and energy > float(ln["if_energy_above"])
				assert_eq(fired, want, "%s line %d (%s at beat %s) with energy %.1f" % [nid, i, ln["act"], str(ln["at_beat"]), energy])
				checked += 1
	assert_true(checked >= 40, "%d conditional lines checked" % checked)


func test_every_shipped_cinematic_cast_line_fires_once_after_its_commit() -> void:
	var d := RunData.load_default()
	var checked := {}
	for nid in d.nodes:
		for h in d.hotspots_of(nid):
			for success in [true, false]:
				var oc: Dictionary = h["on_success"] if success else h.get("on_failure", {})
				if not oc.has("cinematic") or typeof(oc["cinematic"]) != TYPE_STRING:
					continue
				var cname := str(oc["cinematic"])
				var cine: Dictionary = d.cfg["cinematics"].get(cname, {})
				if not cine.has("cast"):
					continue
				var flags := {}
				for f in (h["available"]["flags_all"] as Array):
					flags[str(f)] = true
				var r := _shipped_phase(d, nid, [] if success else [[1, 3]], [{"beat": 52.0, "id": str(h["id"])}], flags)
				var e: RunEngine = r["engine"]
				var commit: Dictionary = {}
				for ev in r["log"]:
					if str(ev["kind"]) == "hotspot_commit":
						commit = ev
				assert_false(commit.is_empty(), "%s committed" % h["id"])
				if commit.is_empty():
					continue
				assert_eq(bool(commit["outcome"]["success"]), success, "%s: the result asked for" % h["id"])
				var cs := _casts(r["log"]).filter(func(c: Dictionary) -> bool: return str(c["source"]) == "cinematic")
				var lines: Array = cine["cast"]
				assert_eq(cs.size(), lines.size(), "%s (%s): every line of %s fired once" % [h["id"], str(success), cname])
				for i in cs.size():
					assert_eq(str(cs[i]["name"]), cname)
					assert_near(float(cs[i]["t"]), float(commit["t"]) + e.beat_s * float(lines[int(cs[i]["index"])]["at_beat"]), 1.0e-6, "%s line %d after the commit" % [cname, i])
				checked[cname] = true
	for cname in d.cfg["cinematics"]:
		if (d.cfg["cinematics"][cname] as Dictionary).has("cast"):
			assert_true(checked.has(cname), "%s: its cast is played by some hotspot's outcome" % cname)
	assert_true(checked.size() >= 12, "%d acted cinematics" % checked.size())


func test_every_character_hotspot_acts_in_all_five_states() -> void:
	var d := RunData.load_default()
	var n_char := 0
	var n_acted := 0
	for nid in d.nodes:
		for h in d.hotspots_of(nid):
			if str(h["kind"]) != "character":
				continue
			n_char += 1
			if RunActing.has_acting(h):
				n_acted += 1
				assert_true(RunActing.actor_of(h) != "", "%s names the person it directs" % h["id"])
				for ph in ["available", "selected", "committed", "success", "failure"]:
					assert_false(RunActing.spec_of(h, ph).is_empty(), "%s has the %s state" % [h["id"], ph])
			else:
				assert_true(str(h["id"]) in ["warehouse.wizard", "warehouse.chill.wizard"], "%s acts (only the two wizards, billboard things, have nobody to direct)" % h["id"])
	assert_eq(n_char, 30, "thirty character hotspots")
	assert_eq(n_acted, 28, "twenty-eight of them have a person to direct")


# --- validation ------------------------------------------------------------------------------------------------------------

func _errs(lines: Array, map_id := "night_one") -> Array:
	var errors: Array = []
	HotspotContract.validate_cast(lines, "test cast", HotspotContract.map_index(map_id), errors)
	return errors


func _has_error(errors: Array, needle: String) -> bool:
	for e in errors:
		if str(e).contains(needle):
			return true
	return false


func test_the_lists_are_the_character_ones_not_copies() -> void:
	for a in StoryCharacter.ACTS:
		assert_true(a in HotspotContract.ACTS, "%s is a directable act" % a)
	assert_eq(HotspotContract.FACES, StoryCharacter.FACES, "the faces are StoryCharacter's")
	for a in HotspotContract.ACTS:
		assert_true(a in StoryCharacter.STATES, "%s is a state the crowd can play" % a)
	assert_eq(HotspotContract.ACTING_PHASES, ["available", "selected", "committed", "success", "failure"])
	assert_true("camera" in HotspotContract.LOOK_TARGETS)


func test_valid_cast_lines_pass_and_bad_ones_are_named() -> void:
	assert_eq(_errs(WAREHOUSE_LINES), [], "the sample lines are valid on night_one")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 0, "act": "moonwalk"}]), "act 'moonwalk'"), "unknown act")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 0, "act": "nod", "face": "smug"}]), "face 'smug'"), "unknown face")
	assert_true(_has_error(_errs([{"actor": "nobody", "at_beat": 0, "act": "nod"}]), "actor 'nobody'"), "an actor with no home in the map")
	assert_true(_has_error(_errs([{"act": "nod", "at_beat": 0}]), "actor"), "no actor")
	assert_true(_has_error(_errs([{"actor": "g07", "act": "nod"}]), "at_beat"), "no beat")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 64, "act": "nod"}]), "at_beat"), "beat 64 is the next scene")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": -1, "act": "nod"}]), "at_beat"), "negative")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 1, "act": "nod", "beats": 0}]), "beats"), "a hold of nothing")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 1, "act": "point", "look_at": "the_moon"}]), "look_at 'the_moon'"), "unknown look target")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 1, "act": "nod", "if_energy_below": "low"}]), "if_energy_below"), "not a number")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 1, "act": "nod", "if_flags_all": "key"}]), "if_flags_all"), "not a list")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 1, "act": "nod", "mood": "sulky"}]), "mood"), "not a field")
	assert_true(_has_error(_errs([{"actor": "g07", "at_beat": 1, "act": "nod", "text": "He nods."}]), "text"), "no text can ride on a cast line")
	assert_true(_has_error(_errs([3]), "not an object"), "a line that is not an object")


func test_run_data_validates_cast_lines_of_scenes_and_cinematics() -> void:
	var d := _data()
	var errors: Array = []
	d.validate_cast_lines(d.nodes["warehouse"], [{"actor": "g07", "at_beat": 2, "act": "nod"}], "scene warehouse", errors)
	assert_eq(errors, [])
	d.validate_cast_lines(d.nodes["warehouse"], [{"actor": "h16", "at_beat": 2, "act": "nod"}], "scene warehouse", errors)
	assert_eq(errors.size(), 1, "an actor of another chapter is not in this scene's map")
	errors = []
	d.cfg["cinematics"]["warehouse.stagger_entry_right"]["cast"] = [{"actor": "g07", "at_beat": 99, "act": "nod"}]
	d._validate_casts(errors)
	assert_true(_has_error(errors, "stagger_entry_right"), "a cinematic's late line is named: %s" % str(errors))


# --- RunActing ------------------------------------------------------------------------------------------------------------

func _h(extra: Dictionary) -> Dictionary:
	var h := {"id": "x", "scene": "s", "kind": "character", "anchor": {"actor": "g07"}, "on_success": {}}
	for k in extra:
		h[k] = extra[k]
	return HotspotContract.normalize(h, "w", "night_one")


func test_acting_chain_orders_committed_then_the_outcome_then_what_follows() -> void:
	var h := _h({"acting": {"available": {"act": "beckon", "face": "plea", "look_at": "camera"}, "committed": {"act": "point", "face": "resolve", "look_at": "to_bar"},
		"success": {"act": "cheer", "face": "cheer", "beats": 8}, "failure": {"act": "shake_head", "face": "doubt", "beats": 6, "then": {"act": "stare", "face": "sad"}}}})
	var bs := 0.5
	var ok := RunActing.outcome_chain(h, true, 10.0, bs)
	assert_eq(ok.map(func(s: Dictionary) -> String: return str(s["act"])), ["point", "cheer"])
	assert_near(float(ok[0]["from"]), 10.0, 1e-9)
	assert_near(float(ok[0]["until"]), 10.0 + RunActing.COMMITTED_BEATS * bs, 1e-9, "the commit flash")
	assert_near(float(ok[1]["from"]), float(ok[0]["until"]), 1e-9, "end to end")
	assert_near(float(ok[1]["until"]) - float(ok[1]["from"]), 8.0 * bs, 1e-9)
	var bad := RunActing.outcome_chain(h, false, 10.0, bs)
	assert_eq(bad.map(func(s: Dictionary) -> String: return str(s["act"]) + "@" + str(s["face"])), ["point@resolve", "shake_head@doubt", "stare@sad"])
	assert_near(float(bad[2]["until"]) - float(bad[2]["from"]), RunActing.THEN_BEATS * bs, 1e-9, "the settled act's own default hold")
	assert_eq(RunActing.actor_of(h), "g07")
	assert_eq(RunActing.actor_of(_h({"acting": {"actor": "d01"}, "anchor": {"thing": "wizard_floor"}})), "d01", "a hotspot on a thing may name its actor")
	assert_eq(RunActing.actor_of(_h({"anchor": {"thing": "wizard_floor"}})), "")
	assert_eq(RunActing.available_spec(h)["act"], "beckon")
	assert_eq(RunActing.selected_spec(h)["act"], "beckon", "no selected act: keep doing the available one")
	assert_eq(RunActing.available_spec(_h({}))["act"], "wave", "no acting block at all: the old wave at the player")
	assert_true(RunActing.available_spec(_h({"anchor": {"thing": "wizard_floor"}})).is_empty(), "no person, no act")
	assert_true(RunActing.outcome_chain(_h({}), true, 0.0, bs).is_empty())


func test_the_bassment_table_gives_every_creature_an_acting_block_that_validates() -> void:
	var td := TrialData.load_default()
	assert_eq(td.errors, [], "the Bassment's data validates with its acting blocks")
	var seen := {}
	for n in td.hotspots:
		for h in td.hotspots[n]:
			if str(h["kind"]) == "encounter":
				assert_true(RunActing.has_acting(h), "%s: the creature acts" % h["id"])
				var fig := str(h["acting"].get("figure", ""))
				assert_true(td.encounters.has(fig), "%s names a creature (%s)" % [h["id"], fig])
				for ph in ["available", "success", "failure"]:
					assert_true(not RunActing.spec_of(h, ph).is_empty(), "%s has %s" % [h["id"], ph])
				seen[fig] = true
			else:
				assert_false(RunActing.has_acting(h), "%s: only creatures act in the Bassment" % h["id"])
	assert_eq(seen.size(), td.encounters.size(), "all ten creatures")
	var m := RunActing.figure_motion("laugh", 0.25)
	assert_true(float(m["dy"]) > 0.0, "a laughing creature bounces")
	assert_eq(RunActing.figure_motion("idle", 3.0)["sx"], 1.0)


# --- the crowd plays it ----------------------------------------------------------------------------------------------------

func _stage() -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	return stage


func _look(stage: StoryStage, t: float) -> void:
	var map := stage.map
	var w: Dictionary = map.waypoint("floor_centre")
	var pose := {"cam": Vector3(w["at"].x, map.eye_y(str(w["sector"])), w["at"].y), "yaw": float(w["yaw"])}
	stage.crowd.set_camera(pose, Vector2(480, 170), map.visible_sectors(w["at"], float(w["yaw"]), str(w["sector"]), 480.0 / 170.0))
	stage.crowd.set_time(t)
	stage.crowd.update(t, 60.0)


func test_direct_actor_sets_the_act_the_face_and_the_look_and_hands_over_when_it_ends() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	var id := str(c.present_ids()[0])
	var node: StoryCharacter = c.actors[id]["node"]
	assert_true(c.direct_actor(id, "plead", "plea", 1.0, 3.0, "camera", "cast"))
	var dir: Dictionary = c.actors[id]["dir"]
	assert_eq([dir["state"], dir["face"], dir["look_at"], dir["src"], dir["force"]], ["plead", "plea", "camera", "cast", true], "the dir dictionary carries the face and the look")
	_look(stage, 0.5)
	assert_true(node.state != "plead", "not before its time")
	assert_eq(node.face_override, "")
	_look(stage, 1.5)
	assert_eq(node.state, "plead", "the act")
	assert_eq(node.face_override, "plea", "the face")
	assert_eq(c.directing(id, 1.5), "cast")
	_look(stage, 3.5)
	assert_true(node.state != "plead", "and back to their own life when it ends")
	assert_eq(node.face_override, "")
	assert_eq(c.directing(id, 3.5), "")
	assert_false(c.direct_actor("nobody_here", "nod", "", 0.0, 1.0), "an unknown person is ignored")
	stage.free()


func test_a_chain_plays_end_to_end_and_stand_down_only_clears_its_own() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	var id := str(c.present_ids()[0])
	var node: StoryCharacter = c.actors[id]["node"]
	var segs := [{"act": "point", "face": "resolve", "look_at": "", "from": 2.0, "until": 3.0}, {"act": "shake_head", "face": "doubt", "look_at": "", "from": 3.0, "until": 4.0}, {"act": "stare", "face": "sad", "look_at": "camera", "from": 4.0, "until": 6.0}]
	assert_true(c.direct_chain(id, segs, "outcome"))
	_look(stage, 2.5)
	assert_eq([node.state, node.face_override], ["point", "resolve"])
	_look(stage, 3.5)
	assert_eq([node.state, node.face_override], ["shake_head", "doubt"])
	_look(stage, 5.0)
	assert_eq([node.state, node.face_override], ["stare", "sad"])
	_look(stage, 7.0)
	assert_eq(node.face_override, "", "the chain is over")
	c.direct_chain(id, segs, "outcome")
	c.stand_down(id, "hotspot")
	assert_false((c.actors[id]["dir"] as Dictionary).is_empty(), "the hotspot's stand-down leaves the outcome's act alone")
	c.stand_down(id, "outcome")
	assert_true((c.actors[id]["dir"] as Dictionary).is_empty())
	c.beckon(id, 0.0, 30.0)
	assert_eq(c.actors[id]["dir"]["state"], "wave", "the old beckon is still the wave")
	c.stand_down(id)
	assert_true((c.actors[id]["dir"] as Dictionary).is_empty())
	stage.free()


func test_look_at_turns_the_person_towards_a_waypoint_an_actor_or_the_camera() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	var ids := c.present_ids()
	var id := str(ids[0])
	var other := str(ids[ids.size() - 1])
	_look(stage, 1.0)
	assert_eq(c.look_point("camera"), Vector2(c._eye.x, c._eye.z))
	assert_eq(c.look_point(other), c.actors[other]["pos"], "an actor")
	assert_eq(c.look_point("floor_centre"), stage.map.waypoint("floor_centre")["at"], "a waypoint")
	assert_eq(c.look_point("no_such_thing"), null)
	c.direct_actor(id, "point", "resolve", 0.0, 10.0, "floor_centre", "cast")
	_look(stage, 2.0)
	assert_true(bool(c.actors[id]["look_has"]), "the look is live while the act is")
	assert_eq(c._target_of(c.actors[id]), stage.map.waypoint("floor_centre")["at"], "a pointing arm goes to the look target")
	_look(stage, 11.0)
	assert_false(bool(c.actors[id]["look_has"]), "and gone with it")
	stage.free()
