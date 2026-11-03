extends TestCase
## Civilian village art (work package A1): the v01..v08 houses, the c1/c2 civilians, the rally flag and the move flash
## are extracted into assets/openra, resolvable through SpriteBank, and have matching actors in data/openra_rules.json.

const ASSET_DIR := "res://assets/openra/"
const RULES := "res://data/openra_rules.json"
const HOUSES := ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08"]
const IMAGES := ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08", "c1", "c2", "flagfly", "moveflsh"]
const DIMENSIONS := {"v01": "2,2", "v02": "2,2", "v03": "2,2", "v04": "2,2", "v05": "2,1", "v06": "2,1", "v07": "2,1", "v08": "1,1"}


func _sequences() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ASSET_DIR + "sequences.json"))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _bank() -> SpriteBank:
	var bank := SpriteBank.new()
	bank.load()
	return bank


func _actors() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(RULES))
	return parsed.get("actors", {}) if typeof(parsed) == TYPE_DICTIONARY else {}


func test_sequences_json_has_the_new_images() -> void:
	var images: Dictionary = _sequences().get("images", {})
	for id in IMAGES:
		assert_true(images.has(id), "sequences.json lacks image %s" % id)
		assert_true(not images.get(id, {}).get("sequences", {}).is_empty(), "image %s has no sequences" % id)


func test_every_referenced_frame_file_exists() -> void:
	var images: Dictionary = _sequences().get("images", {})
	for id in IMAGES:
		var seqs: Dictionary = images.get(id, {}).get("sequences", {})
		for name in seqs:
			var seq: Dictionary = seqs[name]
			var file := str(seq.get("file", ""))
			assert_false(file.is_empty(), "%s.%s names no file" % [id, name])
			var table: Array = seq.get("frame_table", [])
			assert_false(table.is_empty(), "%s.%s has no frame table" % [id, name])
			for row in table:
				for frame in row:
					var path := ASSET_DIR + "%s-%04d.png" % [file, int(frame)]
					assert_true(FileAccess.file_exists(path), "%s.%s frame file missing: %s" % [id, name, path])


func test_sprite_bank_resolves_civilian_sequences() -> void:
	var bank := _bank()
	for seq in ["stand", "run", "panic-run", "die1"]:
		assert_true(bank.has_sequence("c1", seq), "c1.%s" % seq)
		assert_true(bank.has_sequence("c2", seq), "c2.%s" % seq)
	assert_eq(bank.pick("c1", ["nope", "panic-run", "run"]), "panic-run")
	assert_eq(bank.facings("c1", "stand"), 8)
	assert_eq(bank.length("c1", "run"), 6)
	assert_eq(bank.length("c1", "die1"), 8)
	assert_true(bank.texture_for("c1", "stand", 0.0, 0) != null, "c1 stand texture loads")
	assert_true(bank.texture_for("c1", "die1", 0.0, 3) != null, "c1 die1 texture loads")


func test_sprite_bank_resolves_houses_and_markers() -> void:
	var bank := _bank()
	for id in HOUSES:
		assert_true(bank.has_sequence(id, "idle"), "%s.idle" % id)
		assert_true(bank.has_sequence(id, "damaged-idle"), "%s.damaged-idle" % id)
		assert_true(bank.texture_for(id, "idle", 0.0, 0) != null, "%s idle texture loads" % id)
		assert_true(bank.texture_for(id, "damaged-idle", 0.0, 0) != null, "%s damaged texture loads" % id)
	assert_eq(bank.pick("v01", ["damaged-idle", "idle"]), "damaged-idle")
	assert_true(bank.has_sequence("flagfly", "flag"), "flagfly.flag")
	assert_true(bank.length("flagfly", "flag") > 1, "the flag waves")
	assert_true(bank.has_sequence("moveflsh", "idle"), "moveflsh.idle")
	assert_true(bank.length("moveflsh", "idle") > 1, "the move flash is an animation")
	assert_true(bank.texture_for("flagfly", "flag", 0.0, 0) != null, "flag texture loads")
	assert_true(bank.texture_for("moveflsh", "idle", 0.0, 0) != null, "flash texture loads")


func test_rules_have_the_civilian_actors() -> void:
	var actors := _actors()
	for id in ["tecn", "c1", "c2"]:
		assert_true(actors.has(id), "rules lack %s" % id)
		var a: Dictionary = actors.get(id, {})
		assert_true(int(a.get("hp", 0)) > 0, "%s hp" % id)
		assert_eq(str(a.get("locomotor", "")), "foot", "%s locomotor" % id)
		assert_true(bool(a.get("mobile", false)), "%s mobile" % id)
		assert_false(bool(a.get("is_building", true)), "%s is not a building" % id)
		assert_true((a.get("armaments", ["x"]) as Array).is_empty(), "%s is unarmed" % id)
		assert_true(float(a.get("speed", 0)) > 0.0, "%s speed" % id)
		assert_contains(a.get("target_types", []), "Infantry", "%s target types" % id)
	for id in HOUSES:
		assert_true(actors.has(id), "rules lack %s" % id)
		var h: Dictionary = actors.get(id, {})
		assert_true(int(h.get("hp", 0)) > 0, "%s hp" % id)
		assert_true(bool(h.get("is_building", false)), "%s is a building" % id)
		assert_true((h.get("armaments", ["x"]) as Array).is_empty(), "%s is unarmed" % id)
		assert_eq(str(h.get("building", {}).get("dimensions", "")), str(DIMENSIONS[id]), "%s dimensions" % id)
