extends TestCase
## Break-dance flair (docs/DANCE_POLISH.md): a few dancers carry one move and perform it in short bursts on the bar; most of the room dances normally.

const CHAPTERS := ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]


func _stage(id: String) -> StoryStage:
	var run := StoryRun.create({}, "res://content/story/%s.json" % id)
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_art(run.data.art), run.data, run)
	return stage


func test_flair_moves_are_states_with_cycles_and_pure_poses() -> void:
	var c := StoryCharacter.new()
	c.setup(null, {}, "x", 7)
	for mv in StoryCharacter.FLAIR_MOVES:
		assert_true(mv in StoryCharacter.STATES, "%s is a state" % mv)
		assert_true(StoryCharacter.SHEET_CYCLES.has(mv), "%s has a sheet cycle" % mv)
		assert_true(StoryCharacter.FLAIR_BARS.has(mv), "%s has a burst length" % mv)
		var cyc := float(StoryCharacter.SHEET_CYCLES[mv][0])
		assert_near(fposmod(cyc, 4.0), 0.0, 1e-6, "%s lasts whole bars" % mv)
		assert_true(int(StoryCharacter.FLAIR_BARS[mv]) * 4 % int(cyc) == 0, "%s: a burst is a whole number of cycles" % mv)
		for beats in [0.0, 0.5, 1.3, 2.0, 5.25, 7.9, 100.25]:
			var p := c.sample(mv, beats, 0.7)
			for k in StoryCharacter.POSE_KEYS:
				assert_true(is_finite(float(p[k])), "%s %s is finite" % [mv, k])
			assert_eq(p, c.sample(mv, beats, 0.7), "%s is a pure function of the beat" % mv)
		var start := c.sample(mv, 0.0, 0.7)
		assert_true(float(start["crouch"]) < 0.1, "%s starts near the standing dance stance" % mv)
		assert_eq(c.sample(mv, 4.0 * 7.0, 0.7), c.sample(mv, 4.0 * 7.0 + cyc * 3.0, 0.7), "%s is locked to its cycle, not the personal phase" % mv)
	var drop := c.sample("flair_drop", 5.5, 0.7)
	assert_true(float(drop["crouch"]) > 0.2 and absf(float(drop["lean"])) > 0.4, "the drop holds a low leaning freeze on beat 6")
	var robot_a := c.sample("flair_robot", 0.5, 0.7)
	var robot_b := c.sample("flair_robot", 0.8, 0.7)
	assert_near(float(robot_a["arm_l"]), float(robot_b["arm_l"]), 1e-6, "the robot holds its pose between hits")
	c.free()


func test_flair_frames_start_on_the_bar() -> void:
	var c := StoryCharacter.new()
	c.setup(null, {}, "x", 11)
	c.phase = 0.73
	for mv in StoryCharacter.FLAIR_MOVES:
		var cyc: Array = StoryCharacter.SHEET_CYCLES[mv]
		assert_eq(c.sheet_frame(mv, float(cyc[0]), int(cyc[1]), 40.0), 0, "%s shows its first frame on the bar whatever the personal phase" % mv)
	var mid: Array = StoryCharacter.spin_facing(PI, 0, false)
	assert_eq(mid[0], 2, "half way through a spin the back shows")
	var q: Array = StoryCharacter.spin_facing(PI * 0.5, 0, false)
	assert_eq(q, [1, false], "a quarter turn shows the three-quarter view")
	c.free()


func test_flair_is_sparse_and_deterministic() -> void:
	var total := 0
	var flair := 0
	var moves := {}
	for id in CHAPTERS:
		var data: StoryData = StoryData.load_file("res://content/story/%s.json" % id)["data"]
		for a in data.actors:
			total += 1
			var mv := StoryCrowd.flair_of(str(a["id"]))
			assert_eq(mv, StoryCrowd.flair_of(str(a["id"])), "the move is a stable function of the id")
			if mv != "":
				flair += 1
				moves[mv] = true
				assert_true(mv in StoryCharacter.FLAIR_MOVES, "%s: a known move" % mv)
	var share := float(flair) / float(maxi(total, 1))
	assert_true(share > 0.05 and share < 0.14, "about one person in ten to twelve carries a move: %d of %d" % [flair, total])
	assert_eq(moves.size(), StoryCharacter.FLAIR_MOVES.size(), "every move is carried by someone")
	for mv in StoryCharacter.FLAIR_MOVES:  # a dancer flairs in a small share of the bars, a burst never spills over its phrase
		var on := 0
		for bar in 400:
			if StoryCrowd.flair_scheduled(4321, mv, bar):
				on += 1
				var bars := int(StoryCharacter.FLAIR_BARS[mv])
				var first := bar
				while first > 0 and StoryCrowd.flair_scheduled(4321, mv, first - 1) and (first - 1) / 4 == bar / 4:
					first -= 1
				assert_eq(first % bars, 0, "%s: a burst starts on a multiple of its length in the phrase" % mv)
		assert_true(on > 0 and on <= 400 * int(StoryCharacter.FLAIR_BARS[mv]) / 4, "%s: bursts in at most one slot a phrase (%d of 400 bars)" % [mv, on])


func test_only_flair_dancers_have_flair_frames() -> void:
	for id in CHAPTERS:
		var stage := _stage(id)
		var carriers := 0
		for vid in stage.crowds:
			var crowd: StoryCrowd = stage.crowds[vid]
			for aid in crowd.actors:
				var a: Dictionary = crowd.actors[aid]
				var c: StoryCharacter = a["node"]
				if not c.uses_sheet():
					continue
				var mine := StoryCrowd.flair_of(str(aid))
				var states: Dictionary = c.sheet.get("states", {})
				for st in states:
					if str(st).begins_with("flair"):
						assert_eq(str(st), mine, "%s/%s: the only flair frames are the person's own move" % [id, aid])
				var dancer := states.has("dance") and str(a["lock"]) == "" and str(a["data"].get("role", "")) != "hero"
				if mine != "" and dancer:
					assert_true(states.has(mine), "%s/%s: a flair dancer has the frames of %s" % [id, aid, mine])
					assert_eq(str(a["flair"]), mine, "%s/%s: and the crowd knows it" % [id, aid])
					carriers += 1
				if mine == "flair_spin" and dancer:
					var e: Array = states[mine]
					assert_true(e[3] != null and e[4] != null, "%s/%s: the spin has its side and back frames" % [id, aid])
		assert_true(carriers >= 2, "%s: a few flair dancers (%d)" % [id, carriers])
		stage.queue_free()


func test_a_crowd_shows_only_a_few_bursts_on_the_bar() -> void:
	var stage := _stage("night_one")
	var crowd: StoryCrowd = stage.crowds["main"]
	for aid in crowd.actors:
		crowd.actors[aid]["present"] = true
		crowd.actors[aid]["alpha"] = 1.0
	var spb := 60.0 / crowd.bpm
	var seen := 0
	var most := 0
	var first: Dictionary = {}
	for i in 600:
		var t := 8.0 + float(i) * spb * 0.5
		crowd.update(t, 80.0)
		var n := 0
		var dancing := 0
		for aid in crowd.actors:
			var st: String = (crowd.actors[aid]["node"] as StoryCharacter).state
			if st.begins_with("flair"):
				n += 1
				assert_eq(st, str(crowd.actors[aid]["flair"]), "%s performs their own move" % aid)
				if not first.has(aid) or first[aid] < 0.0:
					first[aid] = t
					var into := fposmod(t * crowd.bpm / 60.0, 4.0)
					assert_true(into < 0.6, "%s starts a burst on the bar (%.2f beats in)" % [aid, into])
			else:
				first[aid] = -1.0
				if st in ["dance", "cheer"]:
					dancing += 1
		most = maxi(most, n)
		seen += n
		assert_true(n <= StoryCrowd.FLAIR_CAP, "never more than a handful at once: %d" % n)
		assert_true(n * 4 <= dancing + n, "most of the room dances normally (%d flair, %d dancing)" % [n, dancing])
	assert_true(seen > 0 and most >= 1, "flair does happen in a lively room")
	var again := crowd.flair_bursts(123.0)
	assert_eq(again, crowd.flair_bursts(123.0), "the bursts are a pure function of the bar")
	crowd.update(400.0, 10.0)  # a quiet room: nobody flairs
	for aid in crowd.actors:
		assert_false((crowd.actors[aid]["node"] as StoryCharacter).state.begins_with("flair"), "%s does not flair in a quiet room" % aid)
	stage.queue_free()
