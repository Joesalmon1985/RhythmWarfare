extends TestCase
## The instrument catalogue and loadout validation (PRD section 14).

const CAMPAIGN_CATALOGUE := "res://data/instruments/catalogue.json"


func _sequences() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://assets/openra/sequences.json"))


func test_catalogue_is_valid_against_the_rules_and_art() -> void:
	var c := Catalogue.load_default()
	assert_eq(c.order.size(), 11)
	var rules := Rules.load_default("openra_mvp_01", "defense_01")
	assert_eq(c.validate(rules, _sequences()), [])
	for fam in Catalogue.FAMILIES:
		assert_true(c.profiles_of_family(fam).size() >= 3, fam)


func test_producer_tags_agree_with_where_the_simulation_builds_each_actor() -> void:
	var c := Catalogue.load_default()
	var rules := Rules.load_default("openra_mvp_01", "defense_01")
	var sim := BattleSim.new()
	sim.setup(rules, {}, 1)
	for id in c.order:
		if c.production_type(id) != "cycle":
			continue
		for step in c.steps(id):
			for u in step["units"]:
				var role := sim.producer_role_for(str(u["actor"]))
				var tag := ""
				for t in Catalogue.PRODUCER_ROLE:
					if Catalogue.PRODUCER_ROLE[t] == role:
						tag = t
				assert_true(c.required_producers(id).has(tag), "%s needs %s for %s" % [id, tag, u["actor"]])


func test_validation_rejects_broken_profiles() -> void:
	var rules := Rules.load_default("openra_mvp_01", "defense_01")
	var seqs := _sequences()
	var c := Catalogue.load_default()
	c.profiles["kick_march"]["production"]["steps"][0]["units"][0]["actor"] = "nonexistent"
	assert_contains(c.validate(rules, seqs), "not in openra_rules.json")
	c = Catalogue.load_default()
	c.profiles["kick_march"]["production"]["required_producers"] = ["war_factory"]
	var errs := c.validate(rules, seqs)
	assert_contains(errs, "needs producer 'barracks'")
	c = Catalogue.load_default()
	c.profiles["kick_march"]["family"] = "hat"
	assert_contains(c.validate(rules, seqs), "unsupported family")
	c = Catalogue.load_default()
	c.profiles["kick_march"]["production"]["steps"][0]["units"][0]["count"] = 0
	assert_contains(c.validate(rules, seqs), "positive count")


func test_recipes_from_the_pack_are_data_not_family_rules() -> void:
	var c := Catalogue.load_default()
	assert_eq(c.family_of("kick_march"), "kick")
	var kick_unit: Dictionary = c.steps("kick_march")[0]["units"][0]
	assert_true(kick_unit["actor"] == "e1" and int(kick_unit["count"]) == 2, "a kick makes infantry")
	var snare_unit: Dictionary = c.steps("snare_guard")[0]["units"][0]
	assert_true(snare_unit["actor"] == "jeep" and int(snare_unit["count"]) == 1, "a snare makes a vehicle")
	assert_eq(c.steps("kick_armour").size(), 2, "another kick alternates vehicles")
	assert_eq(c.steps("bass_patrol")[0]["units"].size(), 2, "a bass makes a mixed group")
	assert_eq(c.unit_mix_text("kick_armour"), "repeating: 1 light tank, then 1 jeep")
	assert_eq(c.unit_mix_text("kick_march"), "2 riflemen")
	assert_contains(c.unit_mix_text("bass_patrol"), "rocket soldier")
	assert_contains(c.unit_mix_text("bass_growl"), "air service")


func test_loadout_validation() -> void:
	var c := Catalogue.load_default()
	var families := {"kick_1": "kick", "kick_2": "kick", "snare_1": "snare", "bass_1": "bass"}
	var unlocked := ["kick_march", "snare_guard", "kick_armour", "bass_patrol"]
	var ok := {"kick_1": "kick_march", "kick_2": "kick_armour", "snare_1": "snare_guard", "bass_1": "bass_patrol"}
	var required := ["kick_1", "kick_2", "snare_1", "bass_1"]
	assert_eq(c.validate_loadout(ok, families, required, unlocked), [])
	# duplicate profile inside a family
	var dup := ok.duplicate()
	dup["kick_2"] = "kick_march"
	assert_contains(c.validate_loadout(dup, families, required, unlocked), "equipped twice")
	# wrong family
	var wrong := ok.duplicate()
	wrong["snare_1"] = "kick_armour"
	assert_contains(c.validate_loadout(wrong, families, required, unlocked), "takes a snare instrument")
	# missing required slot
	var missing := ok.duplicate()
	missing.erase("bass_1")
	assert_contains(c.validate_loadout(missing, families, required, unlocked), "required slot bass_1")
	# locked profile
	assert_contains(c.validate_loadout({"kick_1": "kick_siege"}, families, ["kick_1"], unlocked), "locked")
	# caps: three kicks cannot be equipped even with distinct profiles
	var many := {"a": "kick_march", "b": "kick_armour", "c": "kick_siege"}
	var fam3 := {"a": "kick", "b": "kick", "c": "kick"}
	assert_contains(c.validate_loadout(many, fam3, [], ["kick_march", "kick_armour", "kick_siege"]), "at most 2 kick")
	# bass allows three
	var bass3 := {"a": "bass_patrol", "b": "bass_reese", "c": "bass_growl"}
	var fam_b := {"a": "bass", "b": "bass", "c": "bass"}
	assert_eq(c.validate_loadout(bass3, fam_b, [], ["bass_patrol", "bass_reese", "bass_growl"]), [])


func test_every_default_loadout_has_a_render_for_each_active_slot() -> void:
	for pack in ["first_watch", "second_pulse", "hold_the_line"]:
		var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack))
		var level: Level = loaded["level"]
		for slot in level.loadout_active_slots:
			assert_true(level.renders.has(slot), "%s renders %s" % [pack, slot])
			assert_true(level.renders[slot].has(level.loadout_default[slot]))
		# the loadout screen can swap a slot to another rendered profile in place
		var slot: String = level.loadout_active_slots[0]
		for profile in level.renders[slot]:
			assert_eq(DefenseLoader.equip(level, slot, profile), "")
			assert_true(str(level.stems[slot]).contains(profile))
		assert_contains(DefenseLoader.equip(level, slot, "no_such_profile"), "no render")
