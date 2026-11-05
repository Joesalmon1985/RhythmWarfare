extends TestCase
## Stage 1a of docs/THREE_PATHS_AND_FACES_PLAN.md: fourteen faces and fifteen directed acts. The acts are states with a pose, a cycle, a default face and (for the people the story
## directs) baked frames, selected by state and face.

const CHAPTERS := ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]
const NEW_FACES := ["fear", "anger", "plea", "doubt", "relief", "awe", "grief", "laugh", "resolve", "shame"]


func test_fourteen_faces_and_every_default_face_is_one() -> void:
	assert_eq(StoryCharacter.FACES.size(), 14, "fourteen faces")
	assert_eq(StoryCharacter.FACES.slice(0, 4), ["neutral", "happy", "cheer", "sad"], "the crowd's four come first")
	for f in NEW_FACES:
		assert_true(f in StoryCharacter.FACES, "%s is a face" % f)
	for st in StoryCharacter.FACE_OF:
		assert_true(str(StoryCharacter.FACE_OF[st]) in StoryCharacter.FACES, "the default face of %s is a face" % st)


func test_acts_are_states_with_cycles_default_faces_and_pure_poses() -> void:
	var c := StoryCharacter.new()
	c.setup(null, {}, "x", 5)
	assert_eq(StoryCharacter.ACTS.size(), 15, "fifteen directed acts")
	for act in StoryCharacter.ACTS:
		assert_true(act in StoryCharacter.STATES, "%s is a state" % act)
		assert_true(StoryCharacter.SHEET_CYCLES.has(act), "%s has a sheet cycle" % act)
		assert_true(StoryCharacter.FACE_OF.has(act), "%s has a default face" % act)
		var cyc: Array = StoryCharacter.SHEET_CYCLES[act]
		assert_true(float(cyc[0]) > 0.0 and int(cyc[1]) >= 2, "%s: beats and frames" % act)
		for beats in [0.0, 0.25, 0.5, 1.0, 1.7, 3.1, 7.9, 100.25]:
			var p := c.sample(act, beats, 0.6)
			for k in StoryCharacter.POSE_KEYS:
				assert_true(is_finite(float(p[k])), "%s %s is finite at %s" % [act, k, beats])
			assert_true(float(p["fwd"]) >= 0.0 and float(p["fwd"]) <= 1.0, "%s: the forward bend is a share" % act)
			assert_eq(p, c.sample(act, beats, 0.6), "%s is a pure function of the beat" % act)
		# a cycle loops: its end is its start (the act does not jump when it repeats)
		var a0 := c.sample(act, 0.0, 0.6)
		var a1 := c.sample(act, float(cyc[0]), 0.6)
		for k in ["arm_l", "arm_r", "elb_l", "elb_r", "lean", "head_drop", "crouch", "fwd"]:
			assert_near(float(a0[k]), float(a1[k]), 1e-4, "%s loops: %s" % [act, k])
	c.free()


func test_act_poses_say_what_they_say() -> void:
	var c := StoryCharacter.new()
	c.setup(null, {}, "x", 5)
	var bow := c.sample("bow", 2.0, 0.6)
	assert_true(float(bow["fwd"]) > 0.9 and float(bow["head_drop"]) > 6.0, "the bow is held bent forward with the head down")
	assert_true(float(c.sample("bow", 0.0, 0.6)["fwd"]) < 0.01, "a bow starts and ends upright")
	var kneel := c.sample("kneel", 2.0, 0.6)
	assert_true(float(kneel["crouch"]) > 0.25 and float(kneel["lift_r"]) > 0.1, "the kneel is down on one knee")
	assert_true(float(c.sample("collapse", 2.5, 0.6)["crouch"]) > 0.3, "the collapse ends on the floor")
	var nod_hi := 0.0
	var nod_lo := 99.0
	for i in 8:
		var d := float(c.sample("nod", float(i) * 0.25, 0.6)["head_drop"])
		nod_hi = maxf(nod_hi, d)
		nod_lo = minf(nod_lo, d)
	assert_true(nod_hi > 5.0 and nod_lo < 0.5, "a nod goes down and comes back up")
	var shake_l := float(c.sample("shake_head", 0.25, 0.6)["head_tilt"])
	var shake_r := float(c.sample("shake_head", 0.75, 0.6)["head_tilt"])
	assert_true(shake_l > 0.1 and shake_r < -0.1, "a shake goes left then right")
	assert_true(float(c.sample("salute", 1.0, 0.6)["arm_r"]) > 1.5, "the salute raises the hand")
	assert_true(float(c.sample("stamp", 0.5, 0.6)["lift_l"]) > 0.05 and float(c.sample("stamp", 0.0, 0.6)["lift_l"]) < 0.01, "the stamp is planted on the kick")
	c.free()


func test_the_directed_face_picks_its_own_frames() -> void:
	var c := StoryCharacter.new()
	c.setup(null, {}, "x", 5)
	c.phase = 0.77
	c.sheet = {"states": {"idle": [4.0, 4, [], null, null], "beckon": [2.0, 8, [], null, null], "beckon@plea": [2.0, 8, [], null, null], "stare@fear": [16.0, 4, [], null, null],
		"stare": [16.0, 4, [], null, null]}}
	c.state = "beckon"
	assert_eq(c.sheet_pick(0.0)[0], "beckon", "no override: the act's own frames")
	c.face_override = "plea"
	assert_eq(c.sheet_pick(0.0)[0], "beckon@plea", "the directed face has its own frames")
	assert_eq(c.face_name(), "plea", "and is the face shown")
	c.face_override = "happy"
	assert_eq(c.sheet_pick(0.0)[0], "beckon", "the act's own default face is the plain act")
	c.face_override = "awe"
	assert_eq(c.sheet_pick(0.0)[0], "beckon", "a face the actor was not baked with falls back to the act's frames")
	c.state = "stare"
	c.face_override = "fear"
	assert_eq(c.sheet_pick(0.0)[0], "stare@fear", "the old states take a face too")
	c.state = "bow"
	c.face_override = ""
	assert_eq(c.sheet_pick(0.0)[0], "idle", "an act the person was not baked with falls back to idle")
	for act in StoryCharacter.ACTS:
		var cyc: Array = StoryCharacter.SHEET_CYCLES[act]
		assert_eq(c.sheet_frame(act, float(cyc[0]), int(cyc[1]), 40.0), 0, "%s starts on its first frame on the bar, whatever the personal phase" % act)
		assert_eq(c.sheet_frame(act + "@plea", float(cyc[0]), int(cyc[1]), 40.0), 0, "%s@plea too" % act)
	c.free()


func _json(path: String) -> Variant:
	var f := FileAccess.open(path, FileAccess.READ)
	assert_true(f != null, "%s opens" % path)
	if f == null:
		return {}
	return JSON.parse_string(f.get_as_text())


## The people the story directs, from the data itself (what tools/story/art/directed.py derives): {map id: {actor id: {sheet key: facings}}}. A sheet key is the act for the act's own face and
## `act@face` for another; a hotspot's `acting` states (and their `then` chains), a scene's `cast` lines and a cinematic's `cast` lines all count.
func _directed_from_data() -> Dictionary:
	var out := {}
	var run: Dictionary = _json("res://content/run/run.json")
	var maps := {}
	for w in run["worlds"]:
		maps[str(w["id"])] = str(w["map"])

	var add := func(map_id: String, aid: String, act: String, face: String) -> void:
		if act == "" or aid == "":
			return
		var fc := face if face != "" else str(StoryCharacter.FACE_OF.get(act, "neutral"))
		var key := act if fc == str(StoryCharacter.FACE_OF.get(act, "neutral")) else "%s@%s" % [act, fc]
		if not out.has(map_id):
			out[map_id] = {}
		if not (out[map_id] as Dictionary).has(aid):
			out[map_id][aid] = {}
		out[map_id][aid][key] = true

	var dir := DirAccess.open("res://content/run/hotspots")
	for fn in dir.get_files():
		if not fn.ends_with(".json"):
			continue
		var doc: Dictionary = _json("res://content/run/hotspots/" + fn)
		for h in doc["hotspots"]:
			var map_id := str(h.get("map", maps.get(str(doc["world"]), "")))
			var stg := ChoiceStaging.of(h)  # the choice layer's people (docs/CHOICE_CLARITY.md): an option's person in each of its roles, and the people its states steps direct
			if str(stg["archetype"]) == "person":
				for ph in ["current", "other", "touched", "committed", "declined"]:
					var sp: Dictionary = stg.get(ph, {})
					add.call(map_id, str(stg["actor"]), str(sp.get("act", "")), str(sp.get("face", "")))
			for steps in (stg["states"] as Dictionary).values():
				for step in steps:
					if (step as Dictionary).has("actor"):
						add.call(map_id, str(step["actor"]), str(step.get("act", "")), str(step.get("face", "")))
			var a: Variant = h.get("acting", null)
			if typeof(a) != TYPE_DICTIONARY:
				continue
			var aid := str((a as Dictionary).get("actor", (h["anchor"] as Dictionary).get("actor", "")))
			for ph in ["available", "selected", "committed", "success", "failure"]:
				var st: Variant = (a as Dictionary).get(ph, null)
				while typeof(st) == TYPE_DICTIONARY:
					add.call(map_id, aid, str(st.get("act", "")), str(st.get("face", "")))
					st = (st as Dictionary).get("then", null)
	for node in run["nodes"]:
		for line in node.get("cast", []):
			add.call(str(maps[str(node["world"])]), str(line["actor"]), str(line["act"]), str(line.get("face", "")))
	for name in run["cinematics"]:
		var cine: Dictionary = run["cinematics"][name]
		for line in cine.get("cast", []):
			add.call(str(maps[str(cine["world"])]), str(line["actor"]), str(line["act"]), str(line.get("face", "")))
	return out


func test_exactly_the_directed_people_are_baked_in_exactly_their_acts_and_faces() -> void:
	var want := _directed_from_data()
	var extras: Dictionary = _json("res://content/story/directed_actors.json")  # hand-kept additions (none shipped since stage 1d)
	for ch in CHAPTERS:
		var doc: Dictionary = _json("res://assets/story/%s/people/people.json" % ch)
		var actors: Dictionary = doc["actors"]
		var directed: Dictionary = want.get(ch, {})
		assert_true(not directed.is_empty(), "%s has directed people in the run data" % ch)
		assert_true((extras.get(ch, {}) as Dictionary).is_empty(), "%s: no hand-kept extras" % ch)
		var n_states := 0
		for aid in directed:
			assert_true(actors.has(aid), "%s: directed actor %s has a sheet" % [ch, aid])
			if not actors.has(aid):
				continue
			var states: Dictionary = actors[aid]["states"]
			for key in directed[aid]:
				n_states += 1
				assert_true(states.has(key), "%s %s is baked in %s" % [ch, aid, key])
				if states.has(key):
					var st0 := str(key).get_slice("@", 0)
					if st0 in StoryCharacter.ACTS:
						assert_true(states[key][2] != null and states[key][3] != null, "%s %s.%s has the front and the side" % [ch, aid, key])
						if st0 in ["bow", "kneel", "collapse"]:
							assert_true(states[key][4] != null, "%s %s.%s has the back" % [ch, aid, key])
		assert_true(n_states > 10, "%s: %d directed states" % [ch, n_states])
		# nothing is baked that the story does not use: no directed act or acted face for anyone else, and only the used ones for the directed
		var stray := 0
		for aid in actors:
			for key in (actors[aid]["states"] as Dictionary):
				var is_act: bool = str(key).get_slice("@", 0) in StoryCharacter.ACTS
				if str(key).contains("@") or is_act:
					if not directed.has(aid) or not (directed[aid] as Dictionary).has(key):
						stray += 1
		assert_eq(stray, 0, "%s: no act or acted face is baked for anything the story does not direct" % ch)
