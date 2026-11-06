extends TestCase
## The full planner (MUSIC_TRANSITIONS.md section 4.2 with lead rulings 5 to 7) and the sidecar loader, on fixtures and on the real tracks' committed metadata. No packs are needed:
## content/music/tracks/*.json (tempo, sections, drift) and content/music/transitions/*.json are in Git. Nothing here plays; the planner is called directly (`plan_full`) or through
## `plan` with the switch (`modes_enabled`) turned on for one call.

const T0 := 50.0  # the boundary used by the fixtures


# --- fixtures ---------------------------------------------------------------------------------------------------------------------

## A track-to-track fixture: out 174 BPM with plenty of audio left, inc 174 BPM with the usual 16-bar lead-in (entry bar 15, drop bar 31), grids fine, no sidecars.
func _out(bpm := 174.0, track_t := 100.0, duration := 270.0, extra := {}) -> Dictionary:
	var d := {"kind": &"track", "track": "out_track", "node": "x", "path": "main", "bpm": bpm, "boundary_t": T0, "duration_s": duration, "track_t_at_T": track_t, "first_downbeat_s": 0.0, "section_role": "drop"}
	d.merge(extra, true)
	return d


func _inc(bpm := 174.0, entry_bar := 15, drop_bar := 31, extra := {}) -> Dictionary:
	var d := {"kind": &"track", "track": "inc_track", "node": "y", "path": "main", "bpm": bpm, "ordinary_bpm": 174.0, "entry_bar": entry_bar, "drop_bar": drop_bar}
	d.merge(extra, true)
	return d


func _meta(extra := {}) -> Dictionary:
	var d := {"fade_s": 0.6, "carry_beats": 16.0, "carry_gain": 0.0, "out": {}, "in": {}, "out_grid_ok": true, "in_grid_ok": true}
	d.merge(extra, true)
	return d


const READY := {"state": "ready", "may_defer": true, "deferred_once": false}


func _full(out: Dictionary, inc: Dictionary, meta: Dictionary = _meta(), ready: Dictionary = READY) -> Dictionary:
	return TransitionPlanner.plan_full(out, inc, meta, ready)


func _bpm_for_cents(base: float, c: float) -> float:
	return base * pow(2.0, c / 1200.0)


# --- rows 1 to 3 are the M1 rows -------------------------------------------------------------------------------------------------

func test_rows_one_to_three_as_in_m1() -> void:
	var loading := {"state": "loading", "may_defer": true, "deferred_once": false}
	assert_eq(_full(_out(), _inc(), _meta(), loading), {"defer": &"not_ready"}, "row 1")
	var p2 := _full(_out(), _inc(), _meta(), {"state": "loading", "may_defer": true, "deferred_once": true})
	assert_eq(p2["mode"], &"cut", "row 2: still loading after the deferral")
	assert_true(bool(p2["fallback"]))
	assert_eq(p2["recipe"]["incoming"], &"ordinary", "it plays as an ordinary scene")
	assert_eq(p2["recipe"]["reason"], &"not_ready")
	var pf := _full(_out(), _inc(), _meta(), {"state": "failed", "may_defer": true})
	assert_true(bool(pf["fallback"]))
	assert_eq(pf["recipe"]["reason"], &"load_failed")
	assert_false(_full(_out(), _inc(), _meta(), {"state": "loading", "may_defer": false}).has("defer"), "the engine's own route never defers")
	for pair in [[&"ordinary", &"track"], [&"track", &"ordinary"], [&"none", &"track"], [&"ordinary", &"ordinary"]]:
		var o := _out()
		o["kind"] = pair[0]
		var i := _inc()
		i["kind"] = pair[1]
		var p := _full(o, i)
		assert_eq(p["mode"], &"cut", "row 3: %s to %s" % pair)
		assert_false(bool(p["fallback"]))
		assert_eq(p["recipe"]["reason"], &"not_track")
		assert_near(float(p["complete_t"]), T0 + 0.6, 1e-9)
		assert_eq(int(p["blend_beats"]), 0)


# --- rows 4 and 5 ----------------------------------------------------------------------------------------------------------------

func test_row_4_no_blend_on_either_track() -> void:
	for side in ["out", "in"]:
		var m := _meta({side: {"no_blend": true}})
		var p := _full(_out(), _inc(), m)
		assert_eq(p["mode"], &"cut", "no_blend on the %s side" % side)
		assert_false(bool(p["fallback"]))
		assert_eq(p["recipe"]["reason"], &"no_blend")
	assert_eq(_full(_out(), _inc(), _meta({"out": {"no_blend": false}}))["mode"], &"blend")


func test_row_5_short_lead_and_short_tail_ruling_7() -> void:
	for lead in [0, 1, 4]:
		var p := _full(_out(), _inc(174.0, 0, lead))
		assert_eq(p["mode"], &"cut", "a lead-in of %d bars is entered with cut (ruling 7)" % lead)
		assert_false(bool(p["fallback"]))
		assert_eq(p["recipe"]["reason"], &"short_lead")
	# a lead-in of 5 is the shortest that is not a cut: W = L - 4 = 1 < 2, so an echo-out of 1 bar
	var p5 := _full(_out(), _inc(174.0, 10, 15))
	assert_eq(p5["mode"], &"echo_out")
	assert_eq(int(p5["blend_beats"]), 4)
	# 6 bars: W = 2, a real blend
	var p6 := _full(_out(), _inc(174.0, 10, 16))
	assert_eq(p6["mode"], &"blend")
	assert_eq(int(p6["blend_beats"]), 8)
	# the entry bar and the drop bar of a scene whose track starts at bar 0 and drops at bar 15 (sub_focus_rock_it): L = 15, a normal blend with W = 11
	var p15 := _full(_out(), _inc(174.0, 0, 15))
	assert_eq(p15["mode"], &"blend")
	assert_eq(int(p15["blend_beats"]), 44)
	# R: outgoing bars left after T
	var bar_out := 240.0 / 174.0
	assert_eq(_full(_out(174.0, 270.0 - 0.9 * bar_out), _inc())["recipe"]["reason"], &"short_lead", "less than one outgoing bar of audio left: cut")
	assert_eq(_full(_out(174.0, 270.0 - 1.5 * bar_out), _inc())["mode"], &"echo_out", "1.5 bars left: W = floor(R) - 1 = 0, echo-out of 1 bar")
	var p35 := _full(_out(174.0, 270.0 - 3.5 * bar_out), _inc())
	assert_eq(p35["mode"], &"blend")
	assert_eq(int(p35["blend_beats"]), 8, "3.5 bars left: W = 2")


# --- rows 6 to 8 -----------------------------------------------------------------------------------------------------------------

func test_row_6_blend_edges_of_ruling_5() -> void:
	for c in [0.0, 29.9, 49.9, 49.99, -49.9, -49.99]:
		var p := _full(_out(), _inc(_bpm_for_cents(174.0, c)))
		assert_eq(p["mode"], &"blend", "%.2f cents is inside the 50-cent limit" % c)
		assert_near(float(p["recipe"]["cents"]), c, 1e-6)
		assert_false(bool(p["fallback"]))
	for c in [50.1, 51.2, -50.1]:
		assert_eq(_full(_out(), _inc(_bpm_for_cents(174.0, c)))["mode"], &"echo_out", "%.1f cents is outside" % c)
	# the same edges as tempo ratios: 2.93 % inside, 2.95 % outside (2.93 % is 50 cents; 3 % would be 51.2)
	assert_eq(_full(_out(), _inc(174.0 * 1.0293))["mode"], &"blend", "ratio 1.0293")
	assert_eq(_full(_out(), _inc(174.0 * 1.0295))["mode"], &"echo_out", "ratio 1.0295")
	assert_eq(_full(_out(), _inc(174.0 * 1.03))["mode"], &"echo_out", "3 % is 51.2 cents")
	assert_eq(_full(_out(), _inc(174.0 * 0.9716))["mode"], &"blend", "ratio 0.9716")
	assert_eq(_full(_out(), _inc(174.0 * 0.9714))["mode"], &"echo_out", "ratio 0.9714")
	# the worked example of the design: chase status (174.9997) to stimpy (172.0), -29.9 cents, W = 12
	var p := _full(_out(174.9997), _inc(172.0, 15, 31))
	assert_eq(p["mode"], &"blend")
	assert_near(float(p["recipe"]["cents"]), -29.9, 0.1)
	assert_eq(int(p["blend_beats"]), 48)
	assert_near(float(p["complete_t"]), T0 + 12.0 * 240.0 / 172.0, 1e-9)
	assert_near(float(p["recipe"]["rate"]), 172.0 / 174.9997, 1e-9)


func test_row_6_needs_a_trusted_grid() -> void:
	for flags in [{"out_grid_ok": false}, {"in_grid_ok": false}, {"out_grid_ok": false, "in_grid_ok": false}]:
		var p := _full(_out(), _inc(172.0), _meta(flags))
		assert_eq(p["mode"], &"echo_out", "an untrusted grid: no rhythmic overlap")
		assert_false(bool(p["fallback"]))
		assert_eq(float(p["recipe"]["rate"]), 1.0)
		assert_eq(int(p["blend_beats"]), 8, "echo_out with L = 16: W = 2")


func test_row_7_half_time_blend() -> void:
	var p := _full(_out(87.0), _inc(174.0))
	assert_eq(p["mode"], &"halftime_blend", "rho 2")
	assert_near(float(p["recipe"]["rate"]), 1.0, 1e-9, "rho / 2")
	var p2 := _full(_out(174.0), _inc(87.0))
	assert_eq(p2["mode"], &"halftime_blend", "rho 0.5")
	assert_near(float(p2["recipe"]["rate"]), 1.0, 1e-9, "2 rho")
	var p3 := _full(_out(87.0), _inc(87.0 * 2.0 * 1.0293))
	assert_eq(p3["mode"], &"halftime_blend", "just inside around 2:1")
	assert_near(float(p3["recipe"]["rate"]), 1.0293, 1e-9)
	assert_eq(_full(_out(87.0), _inc(87.0 * 2.0 * 1.0295))["mode"], &"echo_out", "just outside around 2:1")
	assert_eq(_full(_out(87.0), _inc(174.0), _meta({"in_grid_ok": false}))["mode"], &"echo_out", "no grid: echo_out")
	var p4 := _full(_out(87.0), _inc(174.0))
	assert_eq(int(p4["blend_beats"]), 48, "same window as a blend")


func test_row_8_echo_out_and_its_window() -> void:
	var p := _full(_out(140.0), _inc(174.0))
	assert_eq(p["mode"], &"echo_out")
	assert_eq(int(p["blend_beats"]), 8, "L >= 6: W = 2")
	assert_near(float(p["complete_t"]), T0 + 2.0 * 240.0 / 174.0, 1e-9)
	assert_false(bool(p["fallback"]))
	assert_eq(_full(_out(140.0), _inc(174.0, 10, 15))["blend_beats"], 4, "L = 5: W = 1")
	assert_eq(_full(_out(168.0), _inc(174.0))["mode"], &"echo_out", "168 to 174 is 60.8 cents")
	assert_eq(_full(_out(172.0), _inc(168.0))["mode"], &"blend", "172 to 168 is within the limit")


func test_the_window_and_the_silence_rule() -> void:
	# W = min(12, L - 4, R - 1); the tail's floor is at least 4 incoming bars before the drop in every row
	for lead in range(5, 33):
		for bpm_in in [174.0, 172.0, 140.0, 87.0]:
			var p := _full(_out(), _inc(bpm_in, 0, lead))
			var bar_in: float = 240.0 / float(bpm_in)
			assert_true(float(p["complete_t"]) <= T0 + float(lead - 4) * bar_in + 1e-6, "complete_t within the deadline (L %d, %.0f BPM)" % [lead, bpm_in])
			if p["mode"] != &"cut":
				assert_true(float(p["recipe"]["complete_t"]) <= float(p["recipe"]["deadline_t"]) + 1e-6)
				assert_near(float(p["recipe"]["deadline_t"]), float(p["recipe"]["drop_t"]) - 4.0 * bar_in, 1e-9)
				assert_near(float(p["recipe"]["drop_t"]), T0 + float(lead) * bar_in, 1e-9)
	assert_eq(_full(_out(), _inc(174.0, 0, 40))["blend_beats"], 48, "never above 12 bars")
	assert_eq(_full(_out(), _inc(174.0, 0, 8))["blend_beats"], 16, "L = 8: W = 4")
	# the same track on both sides: at most 4 bars (two copies of one song for longer sound like a mistake)
	var same := _full(_out(174.0, 100.0, 270.0, {"track": "t"}), _inc(174.0, 15, 31, {"track": "t"}))
	assert_eq(same["mode"], &"blend")
	assert_eq(int(same["blend_beats"]), 16)
	assert_near(float(same["recipe"]["rate"]), 1.0, 1e-12)


# --- the Plan's shape, determinism, the switch -----------------------------------------------------------------------------------

func test_plan_shape_and_purity() -> void:
	var o := _out(174.9997)
	var i := _inc(172.0)
	var m := _meta({"out": {"linger": ["other"], "mix_out_bar": 60}})
	var before: Array = [o.duplicate(true), i.duplicate(true), m.duplicate(true)]
	var p1 := _full(o, i, m)
	var p2 := _full(o, i, m)
	assert_eq(p1, p2, "a pure function: same inputs, same plan")
	assert_eq([o, i, m], before, "the inputs are not changed")
	var keys: Array = p1.keys()
	keys.erase("recipe")
	keys.sort()
	var want: Array = TransitionPlanner.plan_keys()
	want.sort()
	assert_eq(keys, want, "the Plan has the contract's keys, and the recipe apart")
	assert_eq(typeof(p1["blend_beats"]), TYPE_INT)
	assert_true(TransitionPlanner.MODES.has(p1["mode"]))


func test_the_director_still_gets_cut_by_default() -> void:
	assert_false(TransitionPlanner.modes_enabled, "the game runs cut only until M2.4")
	var p := TransitionPlanner.plan(_out(174.9997), _inc(172.0), _meta(), READY)
	assert_eq(p["mode"], &"cut")
	assert_false(bool(p["fallback"]))
	assert_eq(int(p["blend_beats"]), 0)
	assert_near(float(p["complete_t"]), T0 + 0.6, 1e-9)
	assert_eq(p["recipe"]["incoming"], &"track")
	assert_false(p["recipe"].has("reason"), "the M1 planner's recipe is unchanged")
	# the switch in meta, for one call
	var pm := TransitionPlanner.plan(_out(174.9997), _inc(172.0), _meta({"modes_enabled": true}), READY)
	assert_eq(pm["mode"], &"blend")
	# the static switch, restored at once
	TransitionPlanner.modes_enabled = true
	var ps := TransitionPlanner.plan(_out(174.9997), _inc(172.0), _meta(), READY)
	var pmo := TransitionPlanner.plan(_out(174.9997), _inc(172.0), _meta({"modes_enabled": false}), READY)
	TransitionPlanner.modes_enabled = false
	assert_eq(ps["mode"], &"blend")
	assert_eq(pmo["mode"], &"cut", "meta wins over the static")
	assert_eq(TransitionPlanner.plan(_out(174.9997), _inc(172.0), _meta(), READY)["mode"], &"cut")


func test_missing_data_gives_a_forced_cut() -> void:
	for k in ["bpm", "duration_s", "track_t_at_T"]:
		var o := _out()
		o.erase(k)
		var p := _full(o, _inc())
		assert_eq(p["mode"], &"cut", "out without %s" % k)
		assert_true(bool(p["fallback"]), "forced")
		assert_eq(p["recipe"]["reason"], &"missing")
	for k in ["bpm", "entry_bar", "drop_bar"]:
		var i := _inc()
		i.erase(k)
		assert_eq(_full(_out(), i)["recipe"]["reason"], &"missing", "inc without %s" % k)
	for k in ["out_grid_ok", "in_grid_ok"]:
		var m := _meta()
		m.erase(k)
		assert_eq(_full(_out(), _inc(), m)["recipe"]["reason"], &"missing", "meta without %s" % k)
	assert_eq(_full(_out(), _inc(174.0, 0, -1))["recipe"]["reason"], &"missing", "a track without any drop (drop_bar -1)")
	assert_eq(_full(_out(0.0), _inc())["recipe"]["reason"], &"missing", "a zero tempo")
	assert_eq(_full({"kind": &"track"}, {"kind": &"track"})["recipe"]["reason"], &"missing", "nothing at all")
	# no sidecar is not missing data (sections 3.2 and 3.5): the pack's values
	assert_eq(_full(_out(), _inc(), _meta({"out": {}, "in": {}}))["mode"], &"blend")
	var nometa := _meta()
	nometa.erase("out")
	nometa.erase("in")
	assert_eq(_full(_out(), _inc(), nometa)["mode"], &"blend", "no sidecar at all")
	# the one-line alternative reading: a missing or invalid sidecar is a cut
	var req := _meta({"sidecar_required": true, "out_state": "ok", "in_state": "missing"})
	assert_eq(_full(_out(), _inc(), req)["recipe"]["reason"], &"sidecar")
	assert_true(bool(_full(_out(), _inc(), req)["fallback"]))
	req["in_state"] = "ok"
	assert_eq(_full(_out(), _inc(), req)["mode"], &"blend")


# --- the recipes -----------------------------------------------------------------------------------------------------------------

func test_blend_recipe() -> void:
	var p := _full(_out(), _inc(172.0))
	var r: Dictionary = p["recipe"]
	assert_eq(r["mode"], &"blend")
	assert_eq(int(r["window_bars"]), 12)
	assert_false(bool(r["long"]), "a tail in a drop: the short recipe")
	assert_eq(r["kinds"][&"bass"], [0.0, 1.0, &"cos"])
	assert_eq(r["kinds"][&"rhythm"], [0.0, 2.0, &"cos"])
	assert_eq(r["kinds"][&"linger"], [2.0, 12.0, &"cos"])
	assert_eq(r["highpass"]["from_hz"], 20.0)
	assert_eq(r["highpass"]["to_hz"], 250.0)
	assert_eq(r["highpass"]["end_bar"], 4.0)
	assert_eq(r["echo"], {})
	var stems: Dictionary = r["stems"]
	assert_eq(stems["bass"]["kind"], &"bass")
	assert_eq(stems["drums"]["kind"], &"rhythm")
	assert_eq(stems["backing"]["kind"], &"rhythm", "backing carries kick and bass bleed")
	assert_eq(stems["other"]["kind"], &"linger")
	assert_eq(stems["vocals"]["kind"], &"linger")
	assert_near(float(r["bar_s"]), 240.0 / 172.0, 1e-12)
	assert_near(float(r["floor_t"]), float(p["complete_t"]), 1e-12)
	# a pack's own keys: unknown keys count as rhythm; the sidecar's linger decides what lingers
	var o := _out(174.0, 100.0, 270.0, {"stem_keys": ["kick", "tops", "bass", "other", "vocals", "strange"]})
	var p2 := _full(o, _inc(172.0), _meta({"out": {"linger": ["other"]}}))
	var s2: Dictionary = p2["recipe"]["stems"]
	assert_eq(s2["kick"]["kind"], &"rhythm")
	assert_eq(s2["tops"]["kind"], &"rhythm")
	assert_eq(s2["strange"]["kind"], &"rhythm", "an unknown key is on the safe side")
	assert_eq(s2["vocals"]["kind"], &"rhythm", "not in the sidecar's linger list")
	assert_eq(s2["other"]["kind"], &"linger")
	assert_false(s2.has("drums"), "only the pack's own stems")


func test_long_recipe() -> void:
	for role in ["breakdown", "outro"]:
		var p := _full(_out(174.0, 100.0, 270.0, {"section_role": role}), _inc(172.0))
		assert_true(bool(p["recipe"]["long"]), "a tail starting in %s" % role)
		assert_eq(p["recipe"]["kinds"][&"rhythm"], [0.0, 4.0, &"cos"], "the rhythm stays twice as long")
	# the sidecar's mix_out_bar (bars of the outgoing grid): the tail at 100 s is bar 100 / 1.3793 = 72.5
	var late := _full(_out(), _inc(172.0), _meta({"out": {"mix_out_bar": 72}}))
	assert_true(bool(late["recipe"]["long"]), "at or after mix_out_bar")
	var early := _full(_out(), _inc(172.0), _meta({"out": {"mix_out_bar": 73}}))
	assert_false(bool(early["recipe"]["long"]), "before it")
	# without mix_out_bar the snapped bar of outro_start_s is the default
	var viaoutro := _full(_out(), _inc(172.0), _meta({"out": {"outro_start_s": 99.3}}))
	assert_true(bool(viaoutro["recipe"]["long"]), "outro_start_s 99.3 s is bar 72, so 72.5 is past it")
	assert_false(bool(_full(_out(), _inc(172.0), _meta({"out": {"outro_start_s": 120.0}}))["recipe"]["long"]))
	# a short window cuts the long span down: the rhythm cannot outlast the window
	var tight := _full(_out(174.0, 100.0, 270.0, {"section_role": "outro"}), _inc(172.0, 10, 18))
	assert_eq(int(tight["blend_beats"]), 16)
	assert_eq(tight["recipe"]["kinds"][&"rhythm"], [0.0, 4.0, &"cos"])
	var tighter := _full(_out(174.0, 100.0, 270.0, {"section_role": "outro"}), _inc(172.0, 10, 16))
	assert_eq(tighter["recipe"]["kinds"][&"rhythm"], [0.0, 2.0, &"cos"])


func test_echo_recipe() -> void:
	var p := _full(_out(140.0), _inc(174.0))
	var r: Dictionary = p["recipe"]
	assert_eq(r["mode"], &"echo_out")
	assert_eq(float(r["rate"]), 1.0, "the tail plays at 1.0")
	assert_eq(r["kinds"][&"bass"], [0.0, 0.125, &"cos"], "half a beat")
	assert_eq(r["kinds"][&"rhythm"], [0.0, 0.125, &"cos"])
	assert_eq(r["kinds"][&"linger"], [0.0, 1.0, &"cos"])
	assert_near(float(r["echo"]["delay_s"]), 0.75 * 60.0 / 140.0, 1e-12, "3/4 of an outgoing beat: 0.321 s at 140")
	assert_eq(float(r["echo"]["feedback"]), 0.4)
	assert_eq(float(r["echo"]["wet_db"]), -6.0)
	assert_eq(r["highpass"]["from_hz"], 200.0)
	assert_eq(r["highpass"]["to_hz"], 2000.0)
	assert_eq(r["highpass"]["end_bar"], 2.0, "over 0 to W")
	assert_near(float(r["cents"]), 0.0, 1e-12)


func test_cut_recipe_is_the_m1_cut() -> void:
	var p := _full(_out(), _inc(174.0, 0, 3))
	assert_eq(p["mode"], &"cut")
	assert_near(float(p["recipe"]["fade_s"]), 0.6, 1e-12)
	assert_near(float(p["recipe"]["tail_s"]), 0.6, 1e-12)
	assert_near(float(p["complete_t"]), T0 + 0.6, 1e-12)
	assert_near(float(p["incoming_bpm"]), 174.0, 1e-12)


# --- the loader ------------------------------------------------------------------------------------------------------------------

func _read_json(path: String) -> Variant:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _track_ids() -> Array[String]:
	var out: Array[String] = []
	var dir := DirAccess.open("res://content/music/tracks")
	for f in dir.get_files():
		if f.ends_with(".json") and f != "catalogue.json":
			out.append(f.trim_suffix(".json"))
	out.sort()
	return out


func test_sidecar_loader_on_the_committed_sidecars() -> void:
	var ids := _track_ids()
	assert_true(ids.size() >= 61, "61 tracks in Git, got %d" % ids.size())
	var bad := 0
	for id in ids:
		var tr: Dictionary = _read_json("res://content/music/tracks/%s.json" % id)
		var facts := {"bpm": float(tr["tempo"]["bpm"]), "duration_s": float(tr["duration_s"]), "voices": (tr["voices"] as Array).map(func(v: Dictionary) -> String: return str(v["key"]))}
		var r := TransitionSidecars.load_track(id, TransitionSidecars.DIR, facts)
		if r["state"] != "ok":
			bad += 1
			fail("sidecar %s: %s %s" % [id, r["state"], r["errors"]])
		else:
			assert_eq(r["sidecar"]["track"], id)
	assert_eq(bad, 0, "every track has a valid sidecar")


func test_sidecar_loader_missing_and_invalid() -> void:
	var dir := "user://transition_planner_test"
	DirAccess.make_dir_recursive_absolute(dir)
	var m := TransitionSidecars.load_track("nope", dir)
	assert_eq(m["state"], "missing")
	assert_eq(m["sidecar"], {})
	var good := {"format": TransitionSidecars.FORMAT, "track": "g", "first_drop_s": 40.0, "second_drop_s": null, "downbeat_offset_beats": 0, "intro_start_s": null, "outro_start_s": null,
		"mix_in_bar": null, "mix_out_bar": null, "no_blend": false, "linger": null, "checked": null, "note": ""}
	_write(dir + "/g.json", JSON.stringify(good))
	var g := TransitionSidecars.load_track("g", dir)
	assert_eq(g["state"], "ok", "the 3.2 example, without the tool's extra keys")
	assert_eq(g["sidecar"]["first_drop_s"], 40.0)
	var cases := {
		"bad_key": {"bogus": 1}, "bad_format": {"format": "v0"}, "bad_drop": {"first_drop_s": "soon"}, "bad_offset": {"downbeat_offset_beats": 4}, "bad_nb": {"no_blend": "yes"},
		"bad_date": {"checked": "yesterday"}, "bad_track": {"track": "other"}, "bad_origin": {"origin": {"first_drop_s": "guess"}}, "bad_mix": {"mix_in_bar": 2, "first_drop_bar": 31}}
	for name in cases:
		var d := good.duplicate()
		d["track"] = name if name != "bad_track" else "other"
		d.merge(cases[name], true)
		if name == "bad_origin" or name == "bad_mix":
			d["origin"] = d.get("origin", {})
		_write("%s/%s.json" % [dir, name], JSON.stringify(d))
		var r := TransitionSidecars.load_track(name, dir)
		assert_eq(r["state"], "invalid", name)
		assert_eq(r["sidecar"], {}, "an invalid sidecar is ignored as a whole: %s" % name)
		assert_true((r["errors"] as Array).size() >= 1)
		for e in r["errors"]:
			assert_true(str(e).begins_with("%s.json: " % name), "names the file: %s" % e)
	_write(dir + "/junk.json", "[1, 2")
	assert_eq(TransitionSidecars.load_track("junk", dir)["state"], "invalid")
	var da := DirAccess.open(dir)
	for f in da.get_files():
		da.remove(f)
	DirAccess.remove_absolute(dir)


func _write(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(text)
	f.close()


func test_grid_ok_and_snap_verdict() -> void:
	var beat_ms := 60000.0 / 174.0
	var sc := {"first_drop_snap_ms": 0.0}
	assert_true(TransitionSidecars.grid_ok(sc, 20.0, 174.0), "drift of exactly 20 ms is fine")
	assert_false(TransitionSidecars.grid_ok(sc, 20.1, 174.0))
	assert_eq(TransitionSidecars.snap_verdict({"first_drop_snap_ms": 0.24 * beat_ms}, 174.0), &"agrees")
	assert_eq(TransitionSidecars.snap_verdict({"first_drop_snap_ms": -0.24 * beat_ms}, 174.0), &"agrees")
	assert_eq(TransitionSidecars.snap_verdict({"first_drop_snap_ms": 0.99 * beat_ms}, 174.0), &"phase_suspect")
	assert_eq(TransitionSidecars.snap_verdict({"first_drop_snap_ms": 0.5 * beat_ms}, 174.0), &"grid_suspect")
	assert_false(TransitionSidecars.grid_ok({"first_drop_snap_ms": 0.5 * beat_ms}, 1.0, 174.0), "grid suspect: not trusted")
	assert_true(TransitionSidecars.grid_ok({"first_drop_snap_ms": 0.99 * beat_ms}, 1.0, 174.0), "phase suspect only proposes an offset")
	assert_true(TransitionSidecars.grid_ok({}, 1.0, 174.0), "no snap recorded")


func test_drop_bar_of() -> void:
	var info := {"bpm": 174.0, "first_downbeat_s": 0.5, "sections": [{"role": "intro", "start_s": 0.0}, {"role": "drop", "start_s": 0.5 + 32 * 240.0 / 174.0}, {"role": "drop", "start_s": 0.5 + 96 * 240.0 / 174.0}]}
	assert_eq(TransitionSidecars.drop_bar_of(info, "drop1"), 32)
	assert_eq(TransitionSidecars.drop_bar_of(info, "drop2"), 96)
	assert_eq(TransitionSidecars.drop_bar_of(info, "start"), 32, "the start rule still has the first drop")
	assert_eq(TransitionSidecars.drop_bar_of(info, "drop1", {"first_drop_s": 0.5 + 33 * 240.0 / 174.0}), 33, "the sidecar's corrected drop wins")
	var one := {"bpm": 174.0, "first_downbeat_s": 0.5, "sections": [{"role": "drop", "start_s": 0.5 + 16 * 240.0 / 174.0}]}
	assert_eq(TransitionSidecars.drop_bar_of(one, "drop2"), 16, "drop2 with one drop reads the first")
	assert_eq(TransitionSidecars.drop_bar_of({"bpm": 174.0, "first_downbeat_s": 0.5, "sections": []}, "drop1"), -1)
	assert_eq(TransitionSidecars.drop_bar_of({"bpm": 174.0, "first_downbeat_s": 1.1, "sections": [{"role": "drop", "start_s": 0.0}]}, "drop1"), 0, "a drop before the first downbeat is bar 0")


# --- the real tracks -------------------------------------------------------------------------------------------------------------

## What the planner reads of every track, from Git only: the RunTrackPlan info, the sidecar and the grid flag.
func _catalogue() -> Dictionary:
	var cat := {}
	for id in _track_ids():
		var tr: Dictionary = _read_json("res://content/music/tracks/%s.json" % id)
		var intensity := {}
		for s: Dictionary in tr["sections"]:
			if s.has("intensity_db"):
				intensity[str(s["id"])] = float(s["intensity_db"])
		var info := {"id": id, "dir": "", "bpm": float(tr["tempo"]["bpm"]), "first_downbeat_s": float(tr["tempo"]["first_downbeat_s"]), "duration_s": float(tr["duration_s"]), "sections": tr["sections"],
			"intensity": intensity, "charts": {}, "default_chart": ""}
		var sc: Dictionary = TransitionSidecars.load_track(id)["sidecar"]
		var ok := TransitionSidecars.grid_ok(sc, float(tr["tempo"].get("drift_ms_max", 0.0)), info["bpm"])
		var keys: Array = (tr["voices"] as Array).map(func(v: Dictionary) -> String: return str(v["key"]))
		cat[id] = {"info": info, "sidecar": sc, "grid_ok": ok, "stem_keys": keys, "drift": float(tr["tempo"].get("drift_ms_max", 0.0))}
	return cat


## The planner's inputs for track `a` leaving at the end of its lap 2 (or its last lap) into track `b` entered by `entry_b`.
func _pair(cat: Dictionary, a: String, entry_a: Dictionary, b: String, entry_b: Dictionary) -> Dictionary:
	var ca: Dictionary = cat[a]
	var cb: Dictionary = cat[b]
	var pa := RunTrackPlan.compute(ca["info"], entry_a)
	var pb := RunTrackPlan.compute(cb["info"], entry_b)
	if pa.has("error") or pb.has("error"):
		return {"error": true}
	var k := mini(2, int(pa["laps"]))
	var tt: float = float(pa["entry_t"]) + float(k) * float(pa["lap_s"])
	var role := ""
	for s: Dictionary in ca["info"]["sections"]:
		if tt >= float(s["start_s"]) and tt < float(s["end_s"]):
			role = str(s["role"])
	var rule := str(pb["entry"])
	var out := {"kind": &"track", "track": a, "node": a, "path": "main", "bpm": float(pa["bpm"]), "boundary_t": 1000.0, "duration_s": float(ca["info"]["duration_s"]), "track_t_at_T": tt,
		"first_downbeat_s": float(pa["first_downbeat_s"]), "section_role": role, "stem_keys": ca["stem_keys"]}
	var inc := {"kind": &"track", "track": b, "node": b, "path": "main", "bpm": float(pb["bpm"]), "ordinary_bpm": 174.0, "entry_bar": int(pb["entry_bar"]),
		"drop_bar": TransitionSidecars.drop_bar_of(cb["info"], rule, cb["sidecar"])}
	var meta := {"fade_s": 0.6, "out": ca["sidecar"], "in": cb["sidecar"], "out_grid_ok": ca["grid_ok"], "in_grid_ok": cb["grid_ok"]}
	return {"out": out, "inc": inc, "meta": meta}


func _label(p: Dictionary) -> String:
	if p["mode"] == &"cut":
		return "cut:%s" % p["recipe"].get("reason", "-")
	return str(p["mode"])


func test_all_pairs_of_the_61_real_tracks() -> void:
	var cat := _catalogue()
	var ids: Array = cat.keys()
	ids.sort()
	assert_true(ids.size() >= 61)
	var counts := {}
	var bad := 0
	var n := 0
	var blends_beyond := 0
	for a in ids:
		for b in ids:
			var inp := _pair(cat, a, {}, b, {})
			if inp.has("error"):
				counts["plan error"] = int(counts.get("plan error", 0)) + 1
				continue
			var p := _full(inp["out"], inp["inc"], inp["meta"])
			n += 1
			var lab := _label(p)
			counts[lab] = int(counts.get(lab, 0)) + 1
			var mode: StringName = p["mode"]
			if not TransitionPlanner.MODES.has(mode) or p.has("defer"):
				bad += 1
				continue
			var keys: Array = p.keys()
			keys.erase("recipe")
			keys.sort()
			var want: Array = TransitionPlanner.plan_keys()
			want.sort()
			if keys != want:
				bad += 1
			if mode == &"blend" and absf(float(p["recipe"]["cents"])) > 50.0 + 1e-6:
				blends_beyond += 1
			if mode == &"blend" and not (bool(cat[a]["grid_ok"]) and bool(cat[b]["grid_ok"])):
				bad += 1
			if mode != &"cut":
				var bar_in := 240.0 / float(p["incoming_bpm"])
				var lead := int(inp["inc"]["drop_bar"]) - int(inp["inc"]["entry_bar"])
				if float(p["complete_t"]) > 1000.0 + float(lead - 4) * bar_in + 1e-6:
					bad += 1
	assert_eq(n, ids.size() * ids.size(), "every pair got a plan")
	assert_eq(bad, 0, "every pair has a mode, the contract's keys, a trusted grid for a blend and the silence rule")
	assert_eq(blends_beyond, 0, "no blend beyond 50 cents")
	var lines: Array = counts.keys()
	lines.sort()
	print("")
	print("TRANSITION PLANNER, all %d x %d pairs of the committed tracks (a leaves at the end of its lap 2, b enters at its first drop minus 16 bars):" % [ids.size(), ids.size()])
	for l in lines:
		print("  %-22s %5d" % [l, counts[l]])
	print("  %-22s %5d" % ["total", n])
	# spot checks of the design's own examples
	var chase := _pair(cat, "chase_status_no_problem_original_mix", {}, "stimpy_party_last_sounds", {})
	var pc := _full(chase["out"], chase["inc"], chase["meta"])
	assert_eq(pc["mode"], &"blend", "balcony to chill, the design's worked example")
	assert_near(float(pc["recipe"]["cents"]), -29.9, 0.1)
	assert_eq(int(pc["blend_beats"]), 48)
	var mampi := _pair(cat, "chase_status_no_problem_original_mix", {}, "mampi_swift_soldiers_gyrhlx7pafa", {})
	assert_eq(_full(mampi["out"], mampi["inc"], mampi["meta"])["recipe"]["reason"], &"short_lead", "a drop at bar 0 is entered with cut")
	var tern := _pair(cat, "ternion_sound_artifice", {}, "stimpy_party_last_sounds", {})
	assert_eq(_full(tern["out"], tern["inc"], tern["meta"])["mode"], &"echo_out", "140 to 172: an echo-out")
	var teddy := _pair(cat, "chase_status_no_problem_original_mix", {}, "teddy_killerz_teddy_killerz_night_train_t3ggcfz1vs", {})
	assert_eq(_full(teddy["out"], teddy["inc"], teddy["meta"])["mode"], &"echo_out", "an untrusted grid never blends")
	var wide := _pair(cat, "unglued_telefonik", {}, "amplify_crossy_badman", {})
	var pw := _full(wide["out"], wide["inc"], wide["meta"])
	assert_eq(pw["mode"], &"blend", "172 to 177, the widest blend of the catalogue")
	assert_near(float(pw["recipe"]["cents"]), 49.6, 0.2)


func test_the_pairs_that_occur_in_the_game() -> void:
	var cat := _catalogue()
	var scenes: Dictionary = (_read_json("res://content/run/track_scenes.json") as Dictionary)
	var defaults: Dictionary = scenes["defaults"]
	var assigned := {}  # graph id -> {track, entry}
	for path in scenes["paths"]:
		for node in scenes["paths"][path]:
			var ent: Dictionary = scenes["paths"][path][node]
			var e := defaults.duplicate()
			for k in ent:
				if not ["track", "alternates", "note"].has(k):
					e[k] = ent[k]
			assigned["%s/%s" % [path, node]] = {"track": str(ent["track"]), "entry": e}
	var graph: Dictionary = _read_json("res://docs/parallel-development/graph/narrative_graph_target.json")
	var seen := {}
	var lines: Array[String] = []
	var counts := {}
	var bad := 0
	for e: Dictionary in graph["edges"]:
		if not ["scene", "quest_entry"].has(str(e["kind"])):
			continue
		var f := str(e["from"])
		var t := str(e["to"])
		if not assigned.has(f) or not assigned.has(t) or seen.has(f + ">" + t):
			continue
		seen[f + ">" + t] = true
		var a: Dictionary = assigned[f]
		var b: Dictionary = assigned[t]
		var inp := _pair(cat, a["track"], a["entry"], b["track"], b["entry"])
		if inp.has("error"):
			bad += 1
			continue
		var p := _full(inp["out"], inp["inc"], inp["meta"])
		if not TransitionPlanner.MODES.has(p["mode"]):
			bad += 1
		var lab := _label(p)
		counts[lab] = int(counts.get(lab, 0)) + 1
		var lead := int(inp["inc"]["drop_bar"]) - int(inp["inc"]["entry_bar"])
		lines.append("  %-34s -> %-34s %-26s -> %-26s %-14s %+6.1f cents  L=%2d W=%2d" % [f, t, a["track"].left(26), b["track"].left(26), lab,
			TransitionPlanner.cents(float(inp["inc"]["bpm"]) / float(inp["out"]["bpm"])), lead, int(p["blend_beats"]) / 4])
	assert_eq(bad, 0, "every occurring pair got a mode")
	assert_true(seen.size() > 100, "the target graph has more than 100 scene to scene pairs between track scenes, got %d" % seen.size())
	var keys: Array = counts.keys()
	keys.sort()
	print("")
	print("TRANSITION PLANNER, the %d scene pairs of the target graph that join two track scenes (first-choice tracks, default entries; the planner's own call):" % seen.size())
	for k in keys:
		print("  %-22s %5d" % [k, counts[k]])
	print("  scene pair with its mode (tempo ratio of the incoming over the outgoing; L = lead-in bars, W = blend window in bars):")
	for l in lines:
		print(l)
