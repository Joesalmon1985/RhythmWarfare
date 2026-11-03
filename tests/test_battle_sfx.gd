extends TestCase
## Battle sound layer (work package D): the map only names sounds that exist, events trigger the expected sounds,
## cooldowns and throttles hold, at most eight voices play at once, EVA lines never overlap.


func _sfx(role: String = "barracks") -> BattleSfx:
	var s := BattleSfx.new()
	s.record_only = true
	s.primary_role = role
	return s


func _names(s: BattleSfx) -> Array:
	var out: Array = []
	for p in s.played:
		out.append(p["name"])
	return out


func _shot(weapon: String, from: int = 1) -> Dictionary:
	return {"kind": "shot", "from": from, "to": 2, "weapon": weapon, "x": 1.0, "y": 1.0, "tx": 2.0, "ty": 2.0, "heading": 0.0, "actor": "e1", "side": 0}


func _destroyed(id: int, side: int, role: String, ekind: String = "unit", civilian: bool = false) -> Dictionary:
	return {"kind": "destroyed", "id": id, "side": side, "role": role, "x": 1.0, "y": 1.0, "by": 0, "crushed": false, "civilian": civilian, "actor": "x", "ekind": ekind}


func test_every_named_sound_exists() -> void:
	var map := BattleSfx.load_map()
	var names := BattleSfx.sound_names(map)
	assert_true(names.size() >= 20, "the map names its sounds (%d)" % names.size())
	var meta: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://assets/sfx/sfx.json"))
	for n in names:
		assert_true(FileAccess.file_exists("res://assets/sfx/%s.ogg" % n), "assets/sfx/%s.ogg exists" % n)
		assert_true(typeof(meta) == TYPE_DICTIONARY and meta.has(n), "sfx.json lists %s" % n)
	for n in ["gun11", "pillbox1", "gun13", "grenade1", "crmble2", "kaboom25", "girlokay", "guyokay1", "kaboom12", "unitlst1",
			"baseatk1", "placbldg", "build5", "unitrdy1", "enmyapp1", "ackno", "affirm1", "misnwon1", "misnlst1"]:
		assert_true(names.has(n), "the map uses %s" % n)
	for i in range(1, 9):
		assert_true(names.has("dedman%d" % i), "the map uses dedman%d" % i)


func test_shots_by_weapon_with_a_cooldown() -> void:
	var s := _sfx()
	s.push_events([_shot("M1Carbine"), _shot("25mm"), _shot("M60mg")])
	assert_eq(_names(s), ["gun11", "pillbox1"], "unknown weapons are silent")
	assert_eq(s.played[0]["volume_db"], -18.0)
	s.push_events([_shot("M1Carbine")])
	assert_eq(s.played.size(), 2, "same weapon inside 0.25 s is dropped")
	s.advance_time(0.2)
	s.push_events([_shot("M1Carbine")])
	assert_eq(s.played.size(), 2)
	s.advance_time(0.06)
	s.push_events([_shot("M1Carbine")])
	assert_eq(s.played.size(), 3, "after 0.26 s it plays again")
	s.free()


func test_every_rule_is_at_most_minus_three_db() -> void:
	var rules: Array = []
	_collect_rules(BattleSfx.load_map(), rules)
	assert_true(rules.size() >= 18, "the map has its rules (%d)" % rules.size())
	for r in rules:
		assert_true(float(r["volume_db"]) <= -3.0, "volume %s is at most -3 dB" % str(r["volume_db"]))
	for w in ["M1Carbine", "M60mg", "Vulcan", "Grenade"]:
		var shot: Dictionary = BattleSfx.load_map()["shot"][w]
		assert_eq(float(shot["volume_db"]), -18.0, w)
		assert_eq(float(shot["cooldown"]), 0.25, w)
		assert_eq(str(shot["group"]), "weapons", w)


func _collect_rules(node: Variant, out: Array) -> void:
	if typeof(node) != TYPE_DICTIONARY:
		return
	if node.has("volume_db"):
		out.append(node)
		return
	for k in node:
		_collect_rules(node[k], out)


func test_weapons_share_three_voices_and_extra_shots_are_dropped() -> void:
	var s := _sfx()
	s.push_events([_shot("M1Carbine"), _shot("M60mg"), _shot("Vulcan"), _shot("Grenade")])
	assert_eq(_names(s), ["gun11", "pillbox1", "gun13"], "the fourth weapon sound is dropped, nothing is stolen")
	assert_eq(s.active_voices(), 3)
	assert_eq(s.stolen.size(), 0)
	s.push_events([_destroyed(20, 1, "light_tank")])
	assert_eq(s.active_voices(), 4, "other sounds are not held back by the weapons cap")
	s.advance_time(0.62)  # gun11 is over: a weapon slot is free
	s.push_events([_shot("Grenade")])
	assert_eq(_names(s).back(), "grenade1")
	s.free()


func test_sfx_bus_has_a_limiter_once() -> void:
	var i := BattleSfx.ensure_bus()
	BattleSfx.ensure_bus()
	var limiters := 0
	for e in AudioServer.get_bus_effect_count(i):
		var fx := AudioServer.get_bus_effect(i, e)
		if fx is AudioEffectLimiter:
			limiters += 1
			assert_eq((fx as AudioEffectLimiter).ceiling_db, -1.0)
	assert_eq(limiters, 1, "one limiter, however often the bus is ensured")


func test_destroyed_sounds() -> void:
	var s := _sfx()
	s.push_events([_destroyed(10, 1, "village", "building", true)])
	assert_eq(_names(s), ["crmble2", "kaboom25"])
	s.played.clear()
	s.push_events([_destroyed(10, 0, "infantry", "unit", true), _destroyed(11, 0, "infantry", "unit", true)])
	assert_eq(_names(s), ["girlokay", "guyokay1"], "civilians by id parity, no EVA for them")
	s.played.clear()
	s.push_events([_destroyed(19, 1, "infantry")])
	assert_eq(_names(s), ["dedman4"], "infantry by id % 8")
	s.played.clear()
	s.push_events([_destroyed(20, 1, "light_tank")])
	assert_eq(_names(s), ["kaboom12"])
	s.free()


func test_own_unit_lost_adds_a_throttled_eva_line() -> void:
	var s := _sfx()
	s.push_events([_destroyed(8, 0, "infantry")])
	assert_eq(_names(s), ["dedman1", "unitlst1"])
	s.advance_time(2.0)
	s.push_events([_destroyed(16, 0, "infantry")])
	assert_eq(_names(s).count("unitlst1"), 1, "unit lost is throttled to once per 6 s")
	s.advance_time(5.0)
	s.push_events([_destroyed(24, 0, "infantry")])
	assert_eq(_names(s).count("unitlst1"), 2, "a second line after 6 s")
	s.free()


func test_base_attack_is_throttled_and_only_for_the_primary_objective() -> void:
	var s := _sfx("barracks")
	s.push_events([{"kind": "hit", "id": 1, "amount": 5, "x": 1.0, "y": 1.0, "side": 0, "role": "pillbox", "civilian": false}])
	s.push_events([{"kind": "hit", "id": 2, "amount": 5, "x": 1.0, "y": 1.0, "side": 1, "role": "barracks", "civilian": false}])
	assert_eq(s.played.size(), 0)
	var hit := {"kind": "hit", "id": 3, "amount": 5, "x": 1.0, "y": 1.0, "side": 0, "role": "barracks", "civilian": false}
	s.push_events([hit])
	assert_eq(_names(s), ["baseatk1"])
	s.advance_time(10.0)
	s.push_events([hit])
	assert_eq(s.played.size(), 1, "not again inside 15 s")
	s.advance_time(6.0)
	s.push_events([hit])
	assert_eq(s.played.size(), 2)
	s.free()


func test_reward_wave_and_section_sounds() -> void:
	var s := _sfx()
	s.push_events([{"kind": "reward_scheduled", "entry": {"kind": "build", "result": "scheduled"}}])
	assert_eq(_names(s), ["build5"])
	s.push_events([{"kind": "reward_scheduled", "entry": {"kind": "unit", "result": "scheduled"}}])
	assert_eq(s.played.size(), 1, "units announce when ready")
	s.push_events([{"kind": "reward_done", "result": "built", "entity": 5}])
	assert_eq(_names(s), ["build5", "placbldg"])
	s.push_events([{"kind": "reward_done", "result": "unit", "actor": "e1", "count": 3}])
	assert_eq(_names(s), ["build5", "placbldg", "unitrdy1"])
	s.advance_time(2.5)  # unitrdy1 is over and its 2 s throttle has run out
	s.push_events([{"kind": "wave_warning", "wave": 1, "entry": "left", "in_s": 8.0}])
	assert_eq(_names(s).back(), "enmyapp1")
	s.advance_time(2.0)
	s.push_events([{"kind": "section", "point": 0, "id": "defense_1"}])
	s.push_events([{"kind": "section", "point": 2, "id": "defense_3"}])
	s.push_events([{"kind": "section", "point": 1, "id": "defense_2"}])
	assert_eq(_names(s).slice(-3), ["ackno", "affirm1", "ackno"], "the acknowledgement alternates")
	var before := s.played.size()
	s.push_events([{"kind": "section", "point": -1, "id": ""}])
	s.push_events([{"kind": "spawned", "side": 1, "role": "infantry", "actor": "e1", "id": 3, "civilian": false}])
	assert_eq(s.played.size(), before, "clearing the section and wave spawns are silent")
	s.free()


func test_outcome_lines() -> void:
	var s := _sfx()
	s.push_events([{"kind": "outcome", "outcome": "victory", "reason": "", "tick": 1}])
	assert_eq(_names(s), ["misnwon1"])
	var d := _sfx()
	d.push_events([{"kind": "outcome", "outcome": "defeat", "reason": "x", "tick": 1}])
	assert_eq(_names(d), ["misnlst1"])
	s.free()
	d.free()


func test_eva_lines_never_overlap_and_queue_one() -> void:
	var s := _sfx()
	s.push_events([{"kind": "wave_warning", "wave": 1, "entry": "left", "in_s": 8.0}])  # enmyapp1, 1.32 s
	s.push_events([{"kind": "reward_done", "result": "unit", "actor": "e1", "count": 3}])  # queued
	s.push_events([_destroyed(8, 0, "infantry")])  # unitlst1 replaces the queued line; dedman1 plays at once
	assert_eq(_names(s), ["enmyapp1", "dedman1"], "only the first EVA line plays, the rest wait")
	s.advance_time(1.0)
	assert_eq(_names(s), ["enmyapp1", "dedman1"], "still playing")
	s.advance_time(0.5)
	assert_eq(_names(s), ["enmyapp1", "dedman1", "unitlst1"], "one queued line follows, the newest")
	s.advance_time(5.0)
	assert_eq(_names(s).size(), 3, "nothing else was kept")
	s.free()


func test_outcome_cuts_off_a_playing_eva_line() -> void:
	var s := _sfx()
	s.push_events([{"kind": "wave_warning", "wave": 1, "entry": "left", "in_s": 8.0}])
	s.push_events([{"kind": "outcome", "outcome": "victory", "reason": "", "tick": 1}])
	assert_eq(_names(s), ["enmyapp1", "misnwon1"])
	assert_eq(s.stolen, ["enmyapp1"])
	s.free()


func test_eight_voices_at_most_and_the_oldest_non_eva_is_stolen() -> void:
	var s := _sfx()
	s.push_events([{"kind": "wave_warning", "wave": 1, "entry": "left", "in_s": 8.0}])  # EVA, 1.32 s
	for i in 12:
		s.advance_time(0.01)
		s.push_events([_destroyed(100 + i * 8, 1, "light_tank")])  # kaboom12, 0.73 s each
	assert_eq(s.active_voices(), 8, "capped at eight")
	assert_eq(s.stolen.size(), 5, "twelve plus the EVA line, eight stay")
	assert_false(s.stolen.has("enmyapp1"), "the EVA line is never the one stolen")
	s.advance_time(2.0)
	assert_eq(s.active_voices(), 0, "voices end with their sounds")
	s.free()
