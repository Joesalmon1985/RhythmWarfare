extends TestCase
## Every mission in data/campaign/campaign.json is built, loads with the default loadout, stays within the stream
## budget and completes: perfect play wins and passes every sequence, no input loses. Then every item of the loop
## library (clips and sounds) is swapped into the default loadout in turn and played perfectly.

const MAX_STREAMS := 16
const ITEM_MISSION := "m03_hold_the_line"  # drums and bass, short


func _missions() -> Array:
	var c := Campaign.load_data("user://test_all_missions_save.json", 0)
	return c.levels


func _load(pack: String, loadout: Dictionary = {}, warnings: Array = []) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), {"loadout": loadout})
	assert_eq(loaded["errors"], [], pack + " " + str(loadout))
	warnings.append_array(loaded["warnings"])
	return loaded["level"]


func _perfect(level: Level) -> Dictionary:
	var harness: Script = load("res://tools/autoplay.gd")
	var m := Match.new()
	m.setup(level)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	return harness.run_mission(m, level, "perfect", rng)


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
		assert_eq(level.gain_program.size(), level.bar_count(), "%s has a program for every bar" % pack)
		for s in level.sequences:
			assert_true(MissionRules.reward(str(s["reward"])).size() > 0)


func test_every_mission_completes_perfect_wins_and_no_input_loses() -> void:
	var harness: Script = load("res://tools/autoplay.gd")
	var heavy: Dictionary = harness.load_loadout("heavy")
	for l in _missions():
		var pack := str(l["pack"])
		if pack.is_empty():
			continue
		var level := _load(pack)
		if level == null:
			continue
		var r := _perfect(level)
		assert_eq(r["outcome"], "victory", pack + " perfect")
		assert_eq(r["sequences_passed"], r["sequences"], pack + " every sequence passes with perfect input")
		var lv2 := _load(pack)
		var m2 := Match.new()
		m2.setup(lv2)
		var rng := RandomNumberGenerator.new()
		rng.seed = 1
		var none: Dictionary = harness.run_mission(m2, lv2, "none", rng)
		assert_eq(none["outcome"], "defeat", pack + " no input")
		assert_eq(none["built"], 0)
		var lv3 := _load(pack, heavy)
		if lv3 != null:
			var rh := _perfect(lv3)
			assert_eq(rh["outcome"], "victory", pack + " perfect with the heavy loadout")
			assert_eq(rh["sequences_passed"], rh["sequences"], pack + " every sequence passes with the heavy loadout")


## The default loadout with `item` (a clip or a sound id) in it, the other slots made to fit it (Loadout.resolve). {} when
## the item cannot be played on its own (a backing track's own sound).
func _with_item(idx: LibraryIndex, item: String) -> Dictionary:
	var lo: Dictionary = idx.defaults.duplicate()
	match idx.kind(item):
		"groove", "bass":
			lo[idx.kind(item)] = item
		"backing":
			lo["backing"] = item
			var key := str(idx.clips[item].get("key", ""))
			for b in idx.clips_of("bass"):  # a backing track plays with a bass line in its key
				if key.is_empty() or str(idx.clips[b].get("key", "")) == key:
					lo["bass"] = b
					break
		"fill":
			var kick: String = idx.clips[item]["sounds"]["kick"][0]
			var snare: String = idx.clips[item]["sounds"]["snare"][0]
			for g in idx.clips_of("groove"):
				if idx.clips[g]["sounds"]["kick"].has(kick) and idx.clips[g]["sounds"]["snare"].has(snare):
					lo["groove"] = g
					break
			lo["fill"] = item
			lo["kick_sound"] = kick
			lo["snare_sound"] = snare
		"sound":
			var family := str(idx.sounds[item]["family"])
			if family == "bass":
				for b in idx.clips_of("bass"):
					if idx.clips[b]["sounds"]["bass"].has(item):
						lo["bass"] = b
						lo["bass_sound"] = item
						break
			elif family == "kick" or family == "snare":
				for g in idx.clips_of("groove"):
					if idx.clips[g]["sounds"][family].has(item):
						lo["groove"] = g
						lo[family + "_sound"] = item
						break
			else:
				return {}
	return Loadout.resolve(idx, MissionLoader.everything(idx), lo, [])


func test_every_library_item_swapped_into_the_default_loadout_plays_and_wins() -> void:
	var idx := LibraryIndex.load_default()
	assert_false(idx.is_empty(), "the loop library is built")
	var tried := 0
	var items: Array = []
	items.append_array(idx.clips.keys())
	items.append_array(idx.sounds.keys())
	for item in items:
		var wanted := _with_item(idx, str(item))
		if wanted.is_empty():
			continue
		var warnings: Array = []
		var level := _load(ITEM_MISSION, wanted, warnings)
		if level == null:
			continue
		assert_true(Loadout.ids(level.loadout).has(item), "%s is in the loadout that was played (%s)" % [item, str(level.loadout)])
		assert_eq(warnings, [], "%s: the swap needs no fallback" % item)
		var r := _perfect(level)
		assert_eq(r["outcome"], "victory", "%s perfect" % item)
		assert_eq(r["sequences_passed"], r["sequences"], "%s every sequence passes" % item)
		tried += 1
	assert_true(tried >= idx.clips.size(), "every clip was tried (%d of %d items)" % [tried, items.size()])
