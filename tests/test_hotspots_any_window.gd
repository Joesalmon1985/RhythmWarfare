extends TestCase
## The "any" window (docs/CONTINUOUS_RUN.md "Hotspots"): a hotspot with an activity and `window: "any"` is on show in every block of the phase, commits at the decision of the block it was touched in,
## judges by its own `pass_credit` and latches nothing, so it can be touched again. Pure logic first, then inside RunEngine on the real ward scene, then the contract's checks.


func _any(extra: Dictionary = {}) -> Dictionary:
	var h := {"id": "table", "scene": "s", "kind": "object", "anchor": {"waypoint": "x"}, "window": "any", "pass_credit": 0.25, "repeatable": true,
		"on_success": {"activity": "fake"}, "on_failure": {"energy": -3}}
	for k in extra:
		h[k] = extra[k]
	return HotspotContract.normalize(h, "w", "m")


func _exit(id: String, default: bool) -> Dictionary:
	return HotspotContract.normalize({"id": id, "scene": "s", "kind": "exit", "anchor": {"waypoint": "x"}, "default": default, "on_success": {"route": "to_default"}, "on_failure": {"route": "to_default"}}, "w", "m")


func _hs(list: Array = []) -> RunHotspots:
	var d := RunData.new()
	d.hotspots = {"s": list if not list.is_empty() else [_exit("a", true), _any()]}
	var hs := RunHotspots.new(d, {}, {})
	hs.begin_scene("s", 60.0)
	return hs


# ---- pure logic ----------------------------------------------------------------------------------------------------------------------------

func test_window_of_and_shown_in_every_block() -> void:
	var hs := _hs()
	assert_eq(RunHotspots.window_of(_any()), "any")
	assert_eq(RunHotspots.window_of(_exit("a", true)), "final")
	assert_eq(RunHotspots.window_of(HotspotContract.normalize({"id": "w", "scene": "s", "kind": "character", "anchor": {"waypoint": "x"}, "on_success": {"route": "trial:1"}}, "w", "m")), "early")
	for b in 4:
		var ids: Array = hs.shown(b, b == 3).map(func(h: Dictionary) -> String: return str(h["id"]))
		assert_contains(ids, "table", "the table shows in block %d" % b)
		assert_eq(ids.has("a"), b == 3, "the exit shows only in the final window")
	for b in 4:
		assert_true(hs.select("table", b, b == 3), "touchable in block %d" % b)
	hs.committed = "table"
	assert_false(hs.is_shown("table", 3, true), "gone once the final commit has happened")


func test_the_table_is_no_option_of_the_choice_so_it_never_recolours_the_doors() -> void:
	var hs := _hs([_exit("a", true), _exit("b", false), _any()])
	for b in 4:
		var ids: Array = hs.staged(b).map(func(h: Dictionary) -> String: return str(h["id"]))
		assert_eq(ids, ["a", "b"], "only the ways on are staged in block %d" % b)
	hs.select("table", 1, false)
	assert_eq(hs.current_id(1), "a", "touching the table does not make it the current choice: the default exit stays current")
	assert_eq(hs.destination(1), hs.destination(0), "and where the player is going is unchanged")


func test_a_touch_in_block_0_1_or_2_commits_at_that_block_with_the_activity_outcome() -> void:
	for b in 3:
		var hs := _hs()
		assert_true(hs.select("table", b, false))
		var out := hs.on_block(b, true, 0.9)
		assert_eq(out["hotspot"], "table")
		assert_eq(out["activity"], "fake")
		assert_eq(out["route"], "s", "the run stays at the scene")
		assert_true(bool(out["stays"]))
		assert_true(bool(out["success"]))
		assert_eq(out["window"], "any")
		assert_eq(hs.selected, "", "the selection is used up")
		assert_eq(hs.committed, "", "nothing latched")
		assert_eq(hs.committed_early, "")
		assert_true(hs.is_shown("table", b + 1, false), "still on show afterwards")


func test_a_failure_mid_phase_is_the_failure_outcome_without_a_route_and_the_table_can_be_touched_again() -> void:
	var hs := _hs()
	assert_true(hs.select("table", 0, false))
	var out := hs.on_block(0, false, 0.1)
	assert_false(bool(out["success"]))
	assert_eq(out["route"], "", "no route change")
	assert_false(bool(out["stays"]))
	assert_eq(out["activity"], "")
	assert_near(float(out["energy"]), -3.0, 1e-9)
	assert_eq(hs.committed, "")
	assert_true(hs.select("table", 1, false), "touched again")
	var out2 := hs.on_block(1, true, 0.5)
	assert_true(bool(out2["success"]))
	assert_eq(hs.log.size(), 2)
	hs.begin_scene("s", 60.0)
	assert_eq(hs.commit_final(true)["route"], "to_default", "with nothing selected the default exit commits at the final")
	var hs2 := _hs()
	hs2.select("table", 0, false)
	hs2.on_block(0, false, 0.0)
	var fin := hs2.commit_final(false, 0.0)
	assert_eq(fin["hotspot"], "a", "after a wave-off the default exit commits as normal")
	assert_eq(fin["route"], "to_default")
	assert_true(bool(fin["defaulted"]))


func test_pass_credit_boundary_and_the_fallback_to_the_runs_pass() -> void:
	for c in [[0.25, true], [0.24, false], [0.6, true], [0.0, false], [1.0, true]]:
		var hs := _hs()
		hs.select("table", 1, false)
		assert_eq(bool(hs.on_block(1, false, float(c[0]))["success"]), bool(c[1]), "credit %s" % str(c[0]))
	for p in [true, false]:
		var hs := _hs()
		hs.select("table", 1, false)
		assert_eq(bool(hs.on_block(1, p)["success"]), p, "credit unknown: the run's pass (%s) decides" % str(p))
	var no_pc := _any()
	no_pc.erase("pass_credit")
	var plain := _hs([_exit("a", true), no_pc])
	plain.selected = "table"
	assert_eq(bool(plain.on_block(0, false, 0.99)["success"]), false, "no pass_credit: the run's pass decides whatever the credit")


func test_the_final_commit_accepts_a_selected_any_hotspot_as_before() -> void:
	var hs := _hs()
	assert_true(hs.select("table", 3, true))
	var out := hs.commit_final(false, 0.3)
	assert_true(bool(out["success"]), "0.3 passes the table's 0.25 though the run's pass failed")
	assert_eq(out["window"], "final")
	assert_eq(out["route"], "s")
	assert_true(bool(out["stays"]))
	assert_eq(hs.committed, "table")
	var hs2 := _hs()
	hs2.select("table", 3, true)
	var miss := hs2.commit_final(false, 0.1)
	assert_false(bool(miss["success"]))
	assert_eq(miss["route"], "to_default")
	assert_true(bool(miss["continued"]))


func test_final_and_early_window_hotspots_are_unchanged() -> void:
	var wiz := HotspotContract.normalize({"id": "wiz", "scene": "s", "kind": "character", "anchor": {"waypoint": "x"}, "on_success": {"route": "trial:1"}, "on_failure": {"energy": -2}}, "w", "m")
	var hs := _hs([_exit("a", true), wiz, _exit("b", false)])
	assert_true(hs.select("wiz", 0, false))
	var out := hs.on_block(0, true, 0.1)  # credit is ignored without pass_credit
	assert_true(bool(out["success"]))
	assert_eq(out["window"], "early")
	assert_eq(hs.committed_early, "wiz")
	var hs2 := _hs([_exit("a", true), _exit("b", false)])
	hs2.select("b", 3, true)
	assert_eq(hs2.on_block(1, true, 1.0), {}, "a final hotspot never commits mid-phase")
	assert_eq(hs2.selected, "b")
	var fin := hs2.commit_final(true, 0.0)
	assert_eq(fin["hotspot"], "b")
	assert_true(bool(fin["success"]))


func test_the_same_calls_give_the_same_log() -> void:
	var logs: Array = []
	for i in 2:
		var hs := _hs()
		hs.select("table", 0, false)
		hs.on_block(0, false, 0.2)
		hs.select("table", 1, false)
		hs.on_block(1, true, 0.4)
		hs.select("table", 3, true)
		hs.commit_final(true, 0.8)
		logs.append(JSON.stringify(hs.log))
	assert_eq(logs[0], logs[1])


# ---- inside the engine, on the real ward --------------------------------------------------------------------------------------------------

## Plays the ward from its start; `taps` = [{beat, phase}] touches of the table; `weak` is a predicate on (phase, block) that plays only some of the block's cues; `miss` blocks entirely.
func _ward(taps: Array, until_phase: int, weak: Array = [], miss: Array = []) -> Dictionary:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin("ward")
	var t := 0.0
	var pressed := {}
	var released := {}
	var done := {}
	var events: Array = []
	var guard := 0
	while e.phase_n < until_phase and not e.over and guard < 200000:
		guard += 1
		for i in taps.size():
			var tp: Dictionary = taps[i]
			if not done.has(i) and t >= e.t_of(float(tp["beat"])) and int(tp.get("phase", 1)) == e.phase_n:
				done[i] = true
				e.hotspots.select("ward.cards", e.block, e.window_open)
		events.append_array(e.update(t))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			var skip := false
			for m in miss:
				if int(n["phase"]) == int(m[0]) and int(n["block"]) == int(m[1]):
					skip = true
			for m in weak:
				if int(n["phase"]) == int(m[0]) and int(n["block"]) == int(m[1]) and i % 3 != 0:
					skip = true
			if skip:
				continue
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return {"engine": e, "events": events}


func _kind(events: Array, kind: String) -> Array:
	return events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func test_a_touch_in_block_1_commits_at_that_blocks_decision_with_the_credit() -> void:
	var r := _ward([{"beat": 20.0}], 2)
	var e: RunEngine = r["engine"]
	var commits := _kind(r["events"], "hotspot_commit")
	assert_eq(int((commits[0] as Dictionary)["block"]), 1, "the touch at beat 20 is judged at block 1's decision")
	assert_eq(commits.size(), 2, "the mid-phase commit and the final default exit")
	var c: Dictionary = commits[0]
	assert_near(float(c["t"]), (16.0 + e._decision_beat()) * e.beat_s, 1e-6, "phase 1 starts at song time 0")
	assert_eq(c["outcome"]["activity"], "blackjack")
	assert_true(bool(c["outcome"]["stays"]))
	assert_eq(str(c["outcome"]["window"]), "any")
	assert_eq(str((commits[1] as Dictionary)["outcome"]["hotspot"]), "ward.exit_art", "and nothing latched: the scene's default exit still commits at the final")


func test_a_weak_block_with_credit_between_the_table_and_the_run_still_sits() -> void:
	var r := _ward([{"beat": 20.0}], 2, [[1, 1]])
	var res: Dictionary = (_kind(r["events"], "block_result").filter(func(ev: Dictionary) -> bool: return int(ev["phase"]) == 1 and int(ev["block"]) == 1))[0]
	var credit := float(res["credit"])
	assert_true(credit >= 0.25 and credit < 0.6, "the weak block's credit is between 0.25 and 0.6: %s" % str(credit))
	assert_false(bool(res["passed"]))
	var c: Dictionary = _kind(r["events"], "hotspot_commit")[0]
	assert_true(bool(c["outcome"]["success"]), "the table's own 0.25 rule seats the player")
	assert_eq(c["outcome"]["activity"], "blackjack")


func test_a_missed_block_waves_off_without_leaving_and_the_table_is_still_there() -> void:
	var r := _ward([{"beat": 20.0}, {"beat": 36.0}], 2, [], [[1, 1]])
	var commits := _kind(r["events"], "hotspot_commit")
	assert_false(bool((commits[0] as Dictionary)["outcome"]["success"]))
	assert_eq(str((commits[0] as Dictionary)["outcome"]["route"]), "")
	assert_eq(int((commits[1] as Dictionary)["block"]), 2, "touched again, judged at the next block")
	assert_true(bool((commits[1] as Dictionary)["outcome"]["success"]))


func test_credit_reaches_the_hotspots_and_a_final_touch_is_as_before() -> void:
	var r := _ward([{"beat": 52.0}], 2)
	var commits := _kind(r["events"], "hotspot_commit")
	assert_eq(int((commits[0] as Dictionary)["block"]), 3)
	assert_eq(str((commits[0] as Dictionary)["outcome"]["window"]), "final")
	assert_eq(str((commits[0] as Dictionary)["outcome"]["route"]), "ward")


func test_the_same_taps_give_the_same_event_log() -> void:
	var a := _ward([{"beat": 20.0}, {"beat": 40.0}], 3, [[1, 2]])
	var b := _ward([{"beat": 20.0}, {"beat": 40.0}], 3, [[1, 2]])
	assert_eq(JSON.stringify(a["events"]), JSON.stringify(b["events"]))


# ---- the contract -------------------------------------------------------------------------------------------------------------------------

func _validate(extra: Dictionary, success: Dictionary = {"activity": "fake"}) -> Array:
	var errors: Array = []
	var base := {"id": "ward.t", "world": "ward", "scene": "ward", "map": "mental_hospital", "anchor": {"waypoint": "day_cards"}, "kind": "object", "on_success": success, "on_failure": {"energy": -3}}
	for k in extra:
		base[k] = extra[k]
	HotspotContract._validate_one(HotspotContract.normalize(base, "ward", "mental_hospital"), "hotspot t", {"map": "mental_hospital", "world": "ward", "routes": ["ward.art"]}, errors)
	return errors


func _has(errors: Array, needle: String) -> bool:
	return errors.any(func(x: String) -> bool: return x.contains(needle))


func test_contract_window_values_any_needs_an_activity_and_normalize_fills_the_default() -> void:
	assert_eq(_validate({"window": "any"}), [])
	assert_eq(_validate({"window": "final"}), [])
	assert_true(_has(_validate({"window": "sometimes"}), "window"))
	assert_true(_has(_validate({"window": "any"}, {"flags_set": ["x"]}), "needs an on_success activity"))
	assert_eq(HotspotContract.normalize({"id": "x"}, "w", "m")["window"], "final")
	assert_eq(HotspotContract.normalize({"id": "x", "window": "any"}, "w", "m")["window"], "any")


func test_contract_pass_credit_range_and_activity_and_the_claim_look() -> void:
	assert_eq(_validate({"pass_credit": 0.0}), [])
	assert_eq(_validate({"pass_credit": 1}), [])
	assert_true(_has(_validate({"pass_credit": 1.01}), "pass_credit"))
	assert_true(_has(_validate({"pass_credit": -0.1}), "pass_credit"))
	assert_true(_has(_validate({"pass_credit": "x"}), "pass_credit"))
	assert_true(_has(_validate({"pass_credit": 0.5}, {"flags_set": ["x"]}), "pass_credit needs an on_success activity"))
	assert_eq(_validate({"look": {"selected": "claim"}}), [])
	assert_true(_has(_validate({"look": {"selected": "blob"}}), "look.selected"))
	assert_eq(_validate({"look": {"selected": "claim", "ring_m": 1.7}}), [])
	assert_true(_has(_validate({"look": {"ring_m": 0.0}}), "ring_m"))
	assert_true(_has(_validate({"look": {"ring_m": 5.0}}), "ring_m"))


func test_contract_on_select_resolves_like_an_outcome_cinematic() -> void:
	var named := {"ward.cards_approach": {"world": "ward", "steps": [{"move": "walk", "to": "day_cards", "bars": 2, "role": "dancer", "style": "walk"}]}}
	var errors: Array = []
	var h := HotspotContract.normalize({"id": "t", "scene": "ward", "map": "mental_hospital", "anchor": {"waypoint": "day_cards"}, "kind": "object", "on_success": {"activity": "fake"}, "on_failure": {"energy": -3},
		"on_select": {"cinematic": "ward.cards_approach"}}, "ward", "mental_hospital")
	HotspotContract._validate_one(h, "hotspot t", {"map": "mental_hospital", "world": "ward", "routes": [], "cinematics": named}, errors)
	assert_eq(errors, [])
	errors = []
	HotspotContract._validate_one(h, "hotspot t", {"map": "mental_hospital", "world": "ward", "routes": [], "cinematics": {}}, errors)
	assert_true(_has(errors, "on_select"), "an unknown name does not resolve")
	errors = []
	h["on_select"] = {"cinematic": "ward.cards_approach", "x": 1}
	HotspotContract._validate_one(h, "hotspot t", {"map": "mental_hospital", "world": "ward", "routes": [], "cinematics": named}, errors)
	assert_true(_has(errors, "on_select must be"))


func test_the_shipped_table_has_the_new_fields_and_every_other_hotspot_has_none() -> void:
	var d := RunData.load_default()
	assert_true(d.errors.is_empty(), str(d.errors))
	for w in d.hotspots:
		for h in d.hotspots[w]:
			if str(h["id"]) == "ward.cards":
				assert_eq(str(h["window"]), "any")
				assert_near(float(h["pass_credit"]), 0.25, 1e-9)
				assert_near(float(h["radius_m"]), 2.4, 1e-9)
				assert_near(float(h["min_px"]), 220.0, 1e-9)
				assert_eq(str(h["look"]["selected"]), "claim")
				assert_near(float(h["look"]["ring_m"]), 1.7, 1e-9)
				assert_eq(str(h["on_select"]["cinematic"]), "ward.cards_approach")
			else:
				assert_eq(str(h["window"]), "final", "%s keeps the final window" % str(h["id"]))
				assert_false(h.has("pass_credit") or h.has("on_select"), str(h["id"]))
