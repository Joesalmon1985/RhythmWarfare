extends TestCase
## Match: rewards and enemy events applied once each in tick order (A08), pause and retry semantics (A10),
## stem muting follows producer loss (A03, A04), song end is a loss (A11).


static func _level() -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/test_16"))
	return loaded["level"]


func test_enemy_events_apply_exactly_once_in_order_even_across_frozen_time() -> void:
	var level := _level()
	if level == null:
		fail("test_16 missing")
		return
	var m := Match.new()
	m.setup(level)
	var t := 0.0
	var mid := level.duration_seconds() * 0.5
	while t < mid:
		t += 1.0 / 60.0
		m.advance(t)
	# pause: time is frozen, advance is called with the same t many times
	for i in 200:
		m.advance(mid)
	var log_mid := m.production_log.duplicate(true)
	for i in 50:
		m.advance(mid)
	assert_eq(m.production_log.size(), log_mid.size(), "no duplicate enemy waves while frozen")
	while t < level.duration_seconds() + 0.1 and m.outcome.is_empty():
		t += 1.0 / 60.0
		m.advance(t)
	var enemy_ids := []
	for entry in m.production_log:
		if entry["side"] == 1:
			enemy_ids.append(entry["id"])
	var expected := []
	for e in level.enemy_events:
		expected.append(e["id"])
	assert_eq(enemy_ids, expected, "every authored enemy event applied once, in schedule order")
	assert_eq(m.outcome, "defeat")
	assert_eq(m.outcome_reason, "song_end", "the song ended without a decision")


func test_rewards_reach_the_battle_and_retry_resets_everything() -> void:
	var level := _level()
	if level == null:
		return
	var m := Match.new()
	m.setup(level)
	var t := -1.0
	var pressed := 0
	var next := 0
	while t < 6.0:
		t += 1.0 / 60.0
		while next < level.notes.size() and level.notes[next]["time"] <= t:
			var n: Dictionary = level.notes[next]
			if n["type"] == "tap":
				m.press(int(n["button"]), n["time"])
				pressed += 1
			next += 1
		m.advance(t)
	assert_eq(m.judge.perfect, pressed, "every scripted tap judged Perfect")
	var kicks: int = m.judge.rewards["kick"]
	var snares: int = m.judge.rewards["snare"]
	assert_eq(m.sim.stats["produced"][0]["tank"], kicks, "one tank per kick reward")
	assert_eq(m.sim.stats["produced"][0]["infantry"], snares * 5, "five infantry per snare reward")
	# retry: a fresh match has nothing carried over
	var again := Match.new()
	again.setup(level)
	assert_eq(again.judge.perfect, 0)
	assert_eq(again.sim.stats["produced"][0]["tank"], 0)
	assert_eq(again.sim.credits[0], int(level.rules["repair_budget_credits_per_side"]))
	assert_eq(again.sim.tick_count, 0)


func test_producer_loss_mutes_only_its_stem_and_pads_restore_bass() -> void:
	var level := _level()
	if level == null:
		return
	var m := Match.new()
	m.setup(level)
	m.advance(0.1)
	var factory: BattleSim.Ent = null
	for e in m.sim.entities:
		if e.side == 0 and e.role == "factory":
			factory = e
	m.sim._damage(factory, factory.hp, null)
	m.advance(0.2)
	var muted := {}
	for ev in m.drain_events():
		if ev["kind"] == "stem":
			muted[ev["stem"]] = ev["muted"]
	assert_eq(muted, {"kick": true}, "only the kick stem changed")
	assert_false(m.judge.is_lane_available("kick"))
	assert_true(m.judge.is_lane_available("snare"))
	assert_false(m.stems_muted["bass"], "bass audible before any pad exists (initial exception)")
	# build a pad, lose it, rebuild: bass mutes on the loss and returns on the rebuild
	m.sim.produce(0, "bass")
	m.advance(0.3)
	m.drain_events()
	var pad: BattleSim.Ent = m.sim.get_entity(m.sim.slots[0][0]["pad"])
	m.sim._damage(pad, pad.hp, null)
	m.advance(0.4)
	var seen := []
	for ev in m.drain_events():
		if ev["kind"] == "stem":
			seen.append([ev["stem"], ev["muted"]])
	assert_eq(seen, [["bass", true]], "last pad lost mutes bass")
	m.sim.produce(0, "bass")
	m.advance(0.5)
	seen = []
	for ev in m.drain_events():
		if ev["kind"] == "stem":
			seen.append([ev["stem"], ev["muted"]])
	assert_eq(seen, [["bass", false]], "rebuilding restores bass")
	# enemy losses never touch the human mix
	var enemy_barracks: BattleSim.Ent = null
	for e in m.sim.entities:
		if e.side == 1 and e.role == "barracks":
			enemy_barracks = e
	m.sim._damage(enemy_barracks, enemy_barracks.hp, null)
	m.advance(0.6)
	for ev in m.drain_events():
		assert_true(ev["kind"] != "stem", "no stem change for an enemy producer")
	assert_true(m.judge.is_lane_available("snare"))


func test_same_input_trace_gives_same_production_log() -> void:
	var level := _level()
	if level == null:
		return
	var logs := []
	for run in 2:
		var m := Match.new()
		m.setup(level)
		var t := -0.5
		var next := 0
		while t < level.duration_seconds() and m.outcome.is_empty():
			t += 1.0 / 60.0
			while next < level.notes.size() and level.notes[next]["time"] <= t:
				var n: Dictionary = level.notes[next]
				if next % 3 != 0:
					m.press(int(n["button"]), n["time"])
					if n["type"] == "hold":
						m.release(int(n["button"]), n["end_time"] + 0.01)
				next += 1
			m.advance(t)
		logs.append(JSON.stringify(m.production_log))
	assert_eq(logs[0], logs[1], "identical traces for the same seed and inputs")
