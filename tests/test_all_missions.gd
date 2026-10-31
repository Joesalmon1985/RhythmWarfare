extends TestCase
## Every mission in data/campaign/campaign.json is built, loads with its defaults and with every single-option change,
## stays within the stream budget, and completes: perfect play wins and passes every sequence, no input loses.

const MAX_STREAMS := 16


func _missions() -> Array:
	var c := Campaign.load_data("user://test_all_missions_save.json", 0)
	return c.levels


func _load(pack: String, selection: Dictionary = {}) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), {"selection": selection})
	assert_eq(loaded["errors"], [], pack + " " + str(selection))
	return loaded["level"]


func test_all_ten_missions_are_built_and_load() -> void:
	var missions := _missions()
	assert_eq(missions.size(), 10)
	for l in missions:
		var pack := str(l["pack"])
		assert_false(pack.is_empty(), "mission %d has a pack" % int(l["number"]))
		if pack.is_empty():
			continue
		var level := _load(pack)
		if level == null:
			continue
		assert_eq(level.level_id, str(l["level_id"]))
		assert_eq(level.campaign_level, int(l["number"]))
		assert_true(level.stems.size() <= MAX_STREAMS, "%s plays %d streams" % [pack, level.stems.size()])
		assert_true(level.sequences.size() >= 6, "%s has sequences" % pack)
		assert_true(level.notes.size() > 0)
		for s in level.sequences:
			assert_true(MissionRules.reward(str(s["reward"])).size() > 0)


func test_every_offered_option_loads() -> void:
	for l in _missions():
		var pack := str(l["pack"])
		if pack.is_empty():
			continue
		var base := _load(pack)
		if base == null:
			continue
		for ch in base.choices:
			for o in ch["pool"]:
				var sel: Dictionary = base.selection.duplicate(true)
				var picks: Array = (sel[ch["id"]] as Array).duplicate()
				if picks.has(o["id"]):
					continue
				picks[0] = o["id"]
				sel[ch["id"]] = picks
				var lv := _load(pack, sel)
				if lv != null:
					assert_eq(lv.selection[ch["id"]], picks, "%s %s" % [pack, ch["id"]])


func test_every_mission_completes_perfect_wins_and_no_input_loses() -> void:
	var harness: Script = load("res://tools/autoplay.gd")
	for l in _missions():
		var pack := str(l["pack"])
		if pack.is_empty():
			continue
		var level := _load(pack)
		if level == null:
			continue
		var m := Match.new()
		m.setup(level)
		var rng := RandomNumberGenerator.new()
		rng.seed = 1
		var r: Dictionary = harness.run_mission(m, level, "perfect", rng)
		assert_eq(r["outcome"], "victory", pack + " perfect")
		assert_eq(r["sequences_passed"], r["sequences"], pack + " every sequence passes with perfect input")
		var lv2 := _load(pack)
		var m2 := Match.new()
		m2.setup(lv2)
		var none: Dictionary = harness.run_mission(m2, lv2, "none", rng)
		assert_eq(none["outcome"], "defeat", pack + " no input")
		assert_eq(none["built"], 0)
