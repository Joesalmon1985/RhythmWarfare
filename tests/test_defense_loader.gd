extends TestCase
## Schema 2 (defense campaign) pack loader and importer regression: the three shipped packs, the chart contract
## and every rejection the PRD section 14 lists.

const PACKS := {1: "first_watch", 2: "second_pulse", 3: "hold_the_line"}


static func _pack_json(name: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("songs/%s/level.json" % name)))


static func _parse(d: Dictionary, chart_id := "") -> Dictionary:
	var errors: Array = []
	var warnings: Array = []
	var level := DefenseLoader.parse(d, "/pack", {"chart_id": chart_id}, errors, warnings)
	return {"level": level, "errors": errors, "warnings": warnings}


func test_all_three_packs_load_with_aligned_stems() -> void:
	var expected := {1: 64, 2: 96, 3: 89}
	var stems := {1: 3, 2: 4, 3: 5}
	for n in PACKS:
		var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + PACKS[n]))
		assert_eq(loaded["errors"], [], "level %d errors" % n)
		var level: Level = loaded["level"]
		if level == null:
			continue
		assert_eq(level.schema_version, 2)
		assert_true(level.is_defense())
		assert_eq(level.notes.size(), expected[n], "level %d notes" % n)
		assert_eq(level.stems.size(), stems[n], "level %d streams" % n)
		assert_true(level.is_placeholder_audio())
		assert_contains(loaded["warnings"], "placeholder")
		assert_eq(loaded["warnings"].size(), 1, "no thumb warnings: " + str(loaded["warnings"]))
		assert_eq(level.chart_id, "level_0%d.campaign" % n)


func test_level_two_practice_and_campaign_share_audio_with_separate_chart_ids() -> void:
	var camp := LevelLoader.load_pack(TestCase.project_path("songs/second_pulse"), {"chart_id": "level_02.campaign"})
	var prac := LevelLoader.load_pack(TestCase.project_path("songs/second_pulse"), {"chart_id": "level_02.practice"})
	assert_eq(camp["errors"], [])
	assert_eq(prac["errors"], [])
	var a: Level = camp["level"]
	var b: Level = prac["level"]
	assert_eq(a.notes.size(), 96)
	assert_eq(b.notes.size(), 80)
	assert_eq(a.stems, b.stems, "identical audio files")
	assert_eq(a.renders, b.renders)
	assert_eq(a.source, b.source, "same source hashes")
	assert_true(a.chart_id != b.chart_id)
	assert_true(a.progression)
	assert_false(b.progression)
	assert_eq(b.play_mode, "practice")
	var bad := LevelLoader.load_pack(TestCase.project_path("songs/second_pulse"), {"chart_id": "nope"})
	assert_contains(bad["errors"], "not found")


## The importer's compile equals the owner's pack note for note (the pack's player_chart files are the reference).
func test_packs_equal_the_campaign_reference_charts() -> void:
	var refs := {
		"first_watch": [["level_01", "player_chart.json", "level_01.campaign"]],
		"second_pulse": [["level_02", "player_chart.json", "level_02.campaign"], ["level_02", "player_chart.practice.json", "level_02.practice"]],
		"hold_the_line": [["level_03", "player_chart.json", "level_03.campaign"]],
	}
	for pack in refs:
		var d := _pack_json(pack)
		for ref in refs[pack]:
			var reference: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("campaign/First_Three/%s/%s" % [ref[0], ref[1]])))
			var chart: Dictionary = {}
			for c in d["charts"]:
				if c["chart_id"] == ref[2]:
					chart = c
			assert_false(chart.is_empty(), ref[2])
			assert_eq(chart["notes"].size(), reference["notes"].size(), ref[2])
			for i in reference["notes"].size():
				var r: Dictionary = reference["notes"][i]
				var n: Dictionary = chart["notes"][i]
				for key in ["id", "tick", "button", "type", "slot_id", "part_id", "source_note_id", "family"]:
					if r[key] != n[key]:
						fail("%s note %d %s: %s vs %s" % [ref[2], i, key, str(r[key]), str(n[key])])
						break
				assert_eq(int(r.get("duration_ticks", 0)), int(n.get("duration_ticks", 0)), "%s note %d length" % [ref[2], i])
			assert_eq(chart["sections"].size(), reference["sections"].size())


func test_midi_sources_unchanged() -> void:
	var integrity: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("campaign/Musical_Source_Integrity.json")))
	var checked := 0
	for rel in integrity["after_sha256"]:
		var path := TestCase.project_path("campaign/" + str(rel))
		var digest := FileAccess.get_sha256(path)
		assert_eq(digest, integrity["after_sha256"][rel], rel)
		checked += 1
	assert_eq(checked, 18)


func test_level_three_bass_holds_run_across_all_four_buttons_at_full_length() -> void:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/hold_the_line"))
	var level: Level = loaded["level"]
	var buttons := {}
	var holds := 0
	for n in level.notes:
		if n["type"] == "hold":
			holds += 1
			buttons[n["button"]] = true
			assert_eq(n["slot_id"], "bass_1")
			assert_true(n["duration_ticks"] >= 1920, "hold %s keeps its musical length" % n["id"])
	assert_eq(holds, 29)
	assert_eq(buttons.keys().size(), 4, "bass uses all four buttons")
	var longest := 0
	for n in level.notes:
		longest = maxi(longest, int(n["duration_ticks"]))
	assert_eq(longest, 7680, "the two-bar hold is not shortened")
	# sections alternate and every hold ends inside its bass section
	for n in level.notes:
		if n["type"] == "hold":
			var inside := false
			for s in level.sections:
				if s["mode"] == "bass" and n["tick"] >= s["start_tick"] and n["end_tick"] <= s["end_tick"]:
					inside = true
			assert_true(inside, "hold %s inside one bass section" % n["id"])


func test_rejections() -> void:
	var d := _pack_json("hold_the_line")
	d["charts"][0]["notes"][0]["lane"] = "kick"
	assert_contains(_parse(d)["errors"], "slot_id, not lane")
	d = _pack_json("hold_the_line")
	d["charts"][0]["notes"][0].erase("button")
	assert_contains(_parse(d)["errors"], "explicit button")
	d = _pack_json("hold_the_line")
	d["charts"][0]["notes"][0]["slot_id"] = "kick_9"
	assert_contains(_parse(d)["errors"], "not an active slot")
	# mixed drum and bass bars: flip the first drum section to bass
	d = _pack_json("hold_the_line")
	d["charts"][0]["sections"][0]["mode"] = "bass"
	assert_contains(_parse(d)["errors"], "lies in bass section")
	# a hold that reaches the next focus change
	d = _pack_json("hold_the_line")
	for n in d["charts"][0]["notes"]:
		if n["type"] == "hold":
			n["duration_ticks"] = 40000
			break
	assert_contains(_parse(d)["errors"], "crosses a focus change")
	# a wave after the deadline
	d = _pack_json("first_watch")
	d["waves"][0]["start_tick"] = d["duration_ticks"] + 10
	assert_contains(_parse(d)["errors"], "outside the song")
	# a stale render hash
	d = _pack_json("first_watch")
	d["renders"]["kick_1"]["kick_march"]["source_sha256"] = "00"
	assert_contains(_parse(d)["errors"], "source_sha256")
	# a note with no source note id
	d = _pack_json("first_watch")
	d["charts"][0]["notes"][0]["source_note_id"] = ""
	assert_contains(_parse(d)["errors"], "source_note_id")


func test_thumb_rules() -> void:
	# same-thumb hold plus tap is an error: bass hold on button 1 with another note on button 2 inside it
	var d := _pack_json("hold_the_line")
	var notes: Array = d["charts"][0]["notes"]
	var hold: Dictionary = {}
	for n in notes:
		if n["type"] == "hold":
			hold = n
			break
	notes.append({"id": "x1", "tick": hold["tick"] + 960, "button": 2 if hold["button"] == 1 else (1 if hold["button"] == 2 else (4 if hold["button"] == 3 else 3)),
		"type": "tap", "slot_id": "bass_1", "part_id": "bass_1", "source_note_id": "bass_1:x", "family": "bass"})
	var r := _parse(d)
	assert_contains(r["errors"], "same-thumb hold-plus-tap")
	# two taps on one thumb 500 ticks apart: a warning, not an error
	d = _pack_json("first_watch")
	var first: Dictionary = d["charts"][0]["notes"][0]
	d["charts"][0]["notes"].append({"id": "x2", "tick": int(first["tick"]) + 500, "button": 2, "type": "tap", "slot_id": "snare_1", "part_id": "snare_1", "source_note_id": "snare_1:x", "family": "snare"})
	d["charts"][0]["notes"].sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["tick"] < b["tick"])
	r = _parse(d)
	assert_eq(r["errors"], [])
	assert_contains(r["warnings"], "after 500 ticks")
	# three simultaneous touches are an error
	d = _pack_json("first_watch")
	for b in [1, 2, 3]:
		d["charts"][0]["notes"].append({"id": "t%d" % b, "tick": 99, "button": b, "type": "tap", "slot_id": "kick_1", "part_id": "kick_1", "source_note_id": "kick_1:t%d" % b, "family": "kick"})
	assert_contains(_parse(d)["errors"], "simultaneous touches")


func test_judge_resolves_rewards_through_the_slot() -> void:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/hold_the_line"))
	var level: Level = loaded["level"]
	var j := Judge.new()
	j.setup(level.notes)
	# play the first bass hold and the first drum notes perfectly
	var seen := {}
	for n in level.notes.slice(0, 40):
		j.press(int(n["button"]), n["time"], 1)
		if n["type"] == "hold":
			j.release(int(n["button"]), n["end_time"], 1)
		j.update(n["end_time"] + 0.001)
		for ev in j.drain_events():
			if ev.get("reward", false):
				seen[ev["slot_id"]] = int(seen.get(ev["slot_id"], 0)) + 1
	assert_true(seen.has("kick_1") and seen.has("snare_1") and seen.has("kick_2"), str(seen))
	# availability is per slot
	j.set_slot_available("kick_1", false)
	assert_false(j.is_slot_available("kick_1"))
	assert_true(j.is_slot_available("snare_1"))
