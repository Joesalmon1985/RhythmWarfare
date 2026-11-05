extends TestCase
## Arrangements in the run: a scene's music.json entry names an `arrangement`; RunData resolves the sections of its 64-beat phase (two 8-bar sections or one 16-bar one, by `slot`),
## the engine charts each block from the section playing then, RunAudio switches the pack voices on the section's first beat (a voice group per section, the clock untouched), the
## section's mix recipe scales the phase mix, and the route lock compares the chart pack of block 0 exactly as before. Scenes that still name audio/chart are unchanged.

const DIR := "user://test_arr"
const A := "lv2_alien_spaceship"
const B := "lv2_alien_spaceship_v3"
const C := "lv2_alien_spaceship_v2"

## Every scene as it played before the arrangements (one pack for audio and chart): the baseline these tests compare against, whatever the shipped music.json names.
const PLAIN := {
	"warehouse": "lv1_warehouse",
	"warehouse.bar": "lv1_warehouse_v1",
	"warehouse.balcony": "lv1_warehouse_v2",
	"warehouse.chill": "lv1_warehouse_v2",
	"warehouse.booth": "lv1_warehouse_v1",
	"warehouse.exit": "lv1_warehouse",
	"mothership": "lv2_alien_spaceship",
	"mothership.gallery": "lv2_alien_spaceship_v1",
	"mothership.reactor": "lv2_alien_spaceship_v3",
	"mothership.bridge": "lv2_alien_spaceship_v2",
	"mothership.exit": "lv2_alien_spaceship",
	"underworld": "lv2_alien_spaceship_v2",
	"underworld.court": "lv2_alien_spaceship_v3",
	"underworld.furnace": "lv2_alien_spaceship_v2",
	"underworld.pit": "lv2_alien_spaceship_v3",
	"underworld.exit": "lv2_alien_spaceship_v2",
	"hospital": "lv4_hospital",
	"hospital.corridor": "lv4_hospital_v2",
	"hospital.dayroom": "lv4_hospital_v3",
	"hospital.cafeteria": "lv4_hospital_v2",
	"hospital.garden": "lv4_hospital_v3",
	"hospital.exit": "lv4_hospital",
	"ward": "lv5_asylum",
	"ward.art": "lv5_asylum_v1",
	"ward.dorm": "lv5_asylum_v3",
	"ward.corridor": "lv5_asylum_v1",
	"ward.courtyard": "lv5_asylum_v3",
	"ward.exit": "lv5_asylum",
	"hospital_late": "lv4_hospital_v1",
	"hospital_late.cafe": "lv4_hospital_v3",
	"hospital_late.quiet": "lv4_hospital_v2",
	"hospital_late.exit": "lv4_hospital_v1",
	"ward_late": "lv5_asylum_v2",
	"ward_late.treat": "lv5_asylum_v2",
	"ward_late.dorm": "lv5_asylum_v3",
	"ward_late.exit": "lv5_asylum_v2",
}


func _write(path: String, v: Variant) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(v, "\t"))
	f.close()


func _arrangement(id: String, secs: Array) -> Dictionary:
	var bars := 0
	for s in secs:
		bars += int(s["bars"])
	return {"schema": 1, "id": id, "family": A, "seed": 1, "bars": bars, "use": "run", "compatible": [], "identity": {"palette": "mothership", "filters": {}}, "sections": secs}


func _sec(bars: int, role: String, pack: String, mix: String) -> Dictionary:
	return {"bars": bars, "role": role, "pack": pack, "mix": mix, "fills": []}


## A run whose Warehouse plays t_a slot 0 (A then B), its bar slot 1 (C alone, 16 bars) and its balcony slot 0 again; every other scene as shipped.
func _data(seed_value: int = 1, alternates: Array = []) -> RunData:
	DirAccess.make_dir_recursive_absolute(DIR)
	_write(DIR + "/t_a.json", _arrangement("t_a", [_sec(8, "intro", A, "intro"), _sec(8, "drop", B, "drop"), _sec(16, "variation", C, "variation")]))
	_write(DIR + "/t_b.json", _arrangement("t_b", [_sec(8, "intro", B, "build"), _sec(8, "drop", C, "full"), _sec(16, "variation", A, "full")]))
	var music: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.MUSIC_PATH))
	for n in music["nodes"]:
		var plan: Dictionary = {"warehouse": 0, "warehouse.bar": 1, "warehouse.balcony": 0}
		for k in ["arrangement", "slot", "alternates"]:
			n.erase(k)
		if plan.has(str(n["id"])):
			n.erase("audio")
			n.erase("chart")
			n["arrangement"] = "t_a"
			n["slot"] = plan[str(n["id"])]
			if not alternates.is_empty():
				n["alternates"] = alternates
		else:
			n["audio"] = PLAIN[str(n["id"])]
			n["chart"] = PLAIN[str(n["id"])]
	_write(DIR + "/music.json", music)
	return RunData.load_files(RunData.RUN_PATH, DIR + "/music.json", RunData.PACKS_DIR, seed_value, DIR)


## The run as it played before the arrangements: every scene plain.
func _plain_data() -> RunData:
	DirAccess.make_dir_recursive_absolute(DIR)
	var music: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.MUSIC_PATH))
	for n in music["nodes"]:
		for k in ["arrangement", "slot", "alternates"]:
			n.erase(k)
		n["audio"] = PLAIN[str(n["id"])]
		n["chart"] = PLAIN[str(n["id"])]
	_write(DIR + "/music_plain.json", music)
	return RunData.load_files(RunData.RUN_PATH, DIR + "/music_plain.json", RunData.PACKS_DIR, 1, DIR)


func test_a_scene_resolves_the_sections_of_its_phase() -> void:
	var d := _data()
	assert_eq(d.errors, [])
	var w: Dictionary = d.nodes["warehouse"]
	assert_eq(w["arrangement"], "t_a")
	var secs: Array = w["sections"]
	assert_eq(secs.size(), 2, "two 8-bar sections in slot 0")
	assert_eq([int(secs[0]["start_beat"]), int(secs[0]["beats"]), int(secs[1]["start_beat"]), int(secs[1]["beats"])], [0, 32, 32, 32])
	assert_eq([secs[0]["pack"], secs[1]["pack"]], [A, B])
	assert_near(float(secs[1]["gains"]["drums"]), 1.0, 1e-9)
	assert_near(float(secs[0]["gains"]["bass"]), 0.7, 1e-9, "the intro recipe")
	assert_eq(w["audio"], A, "audio and chart are the first section's pack: the lock compares block 0's chart pack")
	assert_eq(w["chart"], A)
	var bar: Array = d.nodes["warehouse.bar"]["sections"]
	assert_eq(bar.size(), 1, "slot 1 is the 16-bar section")
	assert_eq([int(bar[0]["beats"]), bar[0]["pack"]], [64, C])


func test_scenes_that_name_audio_and_chart_are_unchanged() -> void:
	var plain := _plain_data()
	var d := _data()
	for id in d.node_order:
		if id in ["warehouse", "warehouse.bar", "warehouse.balcony"]:
			continue
		assert_eq(d.nodes[id]["audio"], plain.nodes[id]["audio"])
		assert_eq(d.nodes[id]["chart"], plain.nodes[id]["chart"])
		assert_eq(d.nodes[id]["sections"], [])
		assert_eq(d.chart_pack_at(id, 40.0), str(plain.nodes[id]["chart"]))
	assert_eq(plain.errors, [])


func test_the_per_run_seed_picks_between_arrangements_of_one_family_and_is_deterministic() -> void:
	var picks := {}
	for s in range(0, 24):
		var d := _data(s, ["t_b"])
		assert_eq(d.errors, [])
		picks[str(d.nodes["warehouse"]["arrangement"])] = true
		assert_eq(_data(s, ["t_b"]).nodes["warehouse"]["sections"], d.nodes["warehouse"]["sections"], "the same seed, the same sections")
	assert_eq(picks.keys().size(), 2, "both arrangements occur across seeds")
	var none := _data(5)
	assert_eq(none.nodes["warehouse"]["arrangement"], "t_a", "no alternates: always the named one")


func test_errors_name_the_scene() -> void:
	var d := _data()
	_write(DIR + "/t_a.json", _arrangement("t_a", [_sec(8, "intro", "no_such_pack", "intro"), _sec(8, "drop", B, "drop")]))
	var bad := RunData.load_files(RunData.RUN_PATH, DIR + "/music.json", RunData.PACKS_DIR, 1, DIR)
	var found := false
	for e in bad.errors:
		if "warehouse" in str(e) and "no_such_pack" in str(e):
			found = true
	assert_true(found, "a missing section pack is an error naming the scene")
	assert_eq(d.errors, [])


# --- the engine charts each block from the section playing then --------------------------------------------------------------

func _play(e: RunEngine, until_t: float, picks: Dictionary = {}) -> void:
	var t := 0.0
	var pressed := {}
	var done := {}
	while t < until_t and not e.over:
		for at in picks:
			if t >= float(at) and not done.has(at):
				done[at] = true
				e.choose(str(picks[at]))
		e.update(t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
		t += 1.0 / 60.0


func _block(e: RunEngine, phase: int, block: int) -> Array:
	var rows: Array = []
	var start := ((phase - 1) * 64 + block * 16) * 960
	for n in e.level.notes:
		if int(n["phase"]) == phase and int(n["block"]) == block:
			rows.append([int(n["tick"]) - start, int(n["pad"]), str(n["voice"])])
	return rows


func _expect(d: RunData, pack: String, fam: String) -> Array:
	var rows: Array = []
	for c in d.packs[pack]["tiers"]["1"][fam]:
		if int(c[0]) <= 12 * 960:
			rows.append([int(c[0]), int(c[2]), "drums" if fam == "drums" else "bass"])
	return rows


func test_each_block_is_charted_from_the_section_playing_then() -> void:
	var d := _data()
	var e := RunEngine.new(d)
	e.begin("warehouse")
	_play(e, 62.0 * e.beat_s)
	assert_eq(e.stage_of_block.size(), 4, "a perfect player reaches the fourth block")
	assert_eq(_block(e, 1, 0), _expect(d, A, "drums"), "block 0: the first section's drum chart")
	assert_eq(_block(e, 1, 1), _expect(d, A, "bass"), "block 1: the first section's bass line, from the reveal")
	assert_eq(_block(e, 1, 2), _expect(d, B, "drums"), "block 2: the second section's drums, its phrase starting with the section")
	assert_eq(_block(e, 1, 3), _expect(d, B, "bass"), "block 3: the second section's bass")
	assert_true(_expect(d, A, "drums") != _expect(d, B, "drums"), "the two packs chart differently (the test means something)")


func test_a_scene_without_an_arrangement_charts_exactly_as_before() -> void:
	var d := _plain_data()
	var e := RunEngine.new(d)
	e.begin("warehouse")
	_play(e, 62.0 * e.beat_s)
	var pack: Dictionary = d.packs[str(d.nodes["warehouse"]["chart"])]
	var want: Array = []
	for c in pack["tiers"]["1"]["drums"]:
		if int(c[0]) <= 12 * 960:
			want.append([int(c[0]), int(c[2]), "drums"])
	assert_eq(_block(e, 1, 0), want)


func test_the_route_lock_compares_the_chart_pack_of_block_zero() -> void:
	var d := _data()
	assert_true(str(d.nodes["warehouse.bar"]["chart"]) != str(d.nodes["warehouse.balcony"]["chart"]), "slot 1 charts C, slot 0 charts A")
	var e2 := RunEngine.new(d)
	e2.begin("warehouse")
	_play(e2, 62.5 * e2.beat_s, {50.0 * e2.beat_s: "warehouse.bar"})
	assert_true(e2.route_locked, "the lock falls at the last block's decision")
	assert_false(e2.route_allowed("warehouse.balcony"), "another chart pack than the chosen scene's first section is locked out")
	assert_true(e2.route_allowed("warehouse.bar"))
	assert_eq(e2._locked_chart, C, "the lock holds the chart pack of block 0 of the next scene")
	var e3 := RunEngine.new(d)
	e3.begin("warehouse")
	_play(e3, 62.5 * e3.beat_s, {50.0 * e3.beat_s: "warehouse.balcony"})
	assert_eq(e3._locked_chart, A)
	assert_true(e3.route_allowed("warehouse.balcony"))
	assert_false(e3.route_allowed("warehouse.bar"))


# --- RunAudio ----------------------------------------------------------------------------------------------------------------

func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	return a


func _phase_ev(d: RunData, node: String, t: float) -> Dictionary:
	return {"kind": "phase_start", "node": node, "t": t, "phase": 1, "treatment": "none", "audio": d.nodes[node]["audio"], "temporary": false, "fresh": true, "world": "warehouse"}


func test_the_section_switch_is_scheduled_on_the_grid() -> void:
	var d := _data()
	var a := _audio(d)
	a.on_event(_phase_ev(d, "warehouse", 3.0))
	var kinds: Array = []
	for item in a._schedule:
		kinds.append([str(item["kind"]), snappedf(float(item["t"]), 0.0001)])
	assert_eq(kinds[0], ["phase", 3.0])
	assert_eq(kinds[1][0], "section")
	assert_near(float(kinds[1][1]), 3.0 + 32.0 * a.beat_s, 1e-3, "the second 8-bar section starts 32 beats after the phase")
	a.on_event(_phase_ev(d, "warehouse.bar", 40.0))
	assert_eq(a._schedule.size(), 3, "a 16-bar section has no switch")
	a.queue_free()


func test_a_switch_replaces_the_voice_group_without_touching_the_clock() -> void:
	var d := _data()
	var a := _audio(d)
	var stream_before: AudioStream = a.player.stream
	a._begin_phase(_phase_ev(d, "warehouse", 0.0), 0.0, 0.0, 0.0)
	assert_eq(a.active_phase_count(), 1)
	assert_eq(a._live_group()["pack"], A)
	assert_near(a.gains()["drums"], 0.0, 1e-9, "the drums ramp in")
	assert_near(float(a._live_group()["voices"]["drums"]["target"]), 1.0, 1e-9, "stage 0 drums 1.0 x the intro recipe 1.0")
	# the bass reveals at beat 16 (stage 1: drums 0.5, bass 1.0, synth 0.45) with the intro recipe (drums 1, bass 0.7, synth 0.6)
	a._run({"t": 16.0 * a.beat_s, "kind": "mix", "gains": d.cfg["stages"][1]["gains"]}, 0.0, 0.0)
	a._run({"t": 16.0 * a.beat_s, "kind": "reveal"}, 0.0, 0.0)
	var g: Dictionary = a._live_group()
	assert_near(float(g["voices"]["bass"]["target"]), 1.0 * maxf(0.7, float(d.cfg["mix"].get("recipe_bass_floor", 0.0))), 1e-6, "bass: stage gain x the section's recipe (lifted to the run's recipe_bass_floor)")
	assert_near(float(g["voices"]["other"]["target"]), 0.45 * 0.6, 1e-6)
	assert_near(float(g["voices"]["drums"]["target"]), 0.5 * 1.0, 1e-6)
	var t_switch := 32.0 * a.beat_s
	a._run({"t": t_switch, "kind": "section", "phase": 1, "index": 1, "section": d.nodes["warehouse"]["sections"][1]}, t_switch + 0.004, 0.003)
	assert_eq(a.active_phase_count(), 1, "one voice group per section: the old section's voices are gone")
	var n: Dictionary = a._live_group()
	assert_eq([n["pack"], int(n["section"])], [B, 1])
	assert_true(n["voices"].has("drums") and n["voices"].has("bass") and n["voices"].has("other"), "the bass was revealed, so the new section carries it")
	assert_near(float(n["voices"]["bass"]["gain"]), 0.5 * 0 + 1.0 * 1.0, 1e-6, "stage 1 bass 1.0 x the drop recipe 1.0, at once (a cut on the grid)")
	assert_near(float(n["voices"]["drums"]["gain"]), 0.5, 1e-6, "stage 1 drums 0.5 x 1.0")
	var logs: Array = a.voice_log.filter(func(v: Dictionary) -> bool: return int(v["section"]) == 1)
	assert_eq(logs.size(), 3)
	for v in logs:
		assert_eq(v["pack"], B)
		assert_near(float(v["target"]), t_switch, 1e-9)
		assert_near(float(v["lateness_ms"]), 7.0, 1e-6, "the same lateness compensation as a phase start: it begins that far into the loop")
	assert_true(a.player.stream == stream_before, "the 64-beat clock stream is not replaced")
	# a mix event after the switch reaches the new group
	a._run({"t": t_switch + 1.0, "kind": "mix", "gains": d.cfg["stages"][2]["gains"]}, 0.0, 0.0)
	assert_near(float(a._live_group()["voices"]["drums"]["target"]), 1.0, 1e-6)
	a.queue_free()


func test_a_switch_before_the_reveal_starts_only_the_drums() -> void:
	var d := _data()
	var a := _audio(d)
	a._begin_phase(_phase_ev(d, "warehouse", 0.0), 0.0, 0.0, 0.0)
	a._run({"t": 32.0 * a.beat_s, "kind": "section", "phase": 1, "index": 1, "section": d.nodes["warehouse"]["sections"][1]}, 32.0 * a.beat_s, 0.0)
	var v: Dictionary = a._live_group()["voices"]
	assert_eq(v.keys(), ["drums"], "the bass enters at the reveal, whichever section is playing")
	a._run({"t": 33.0 * a.beat_s, "kind": "reveal"}, 33.0 * a.beat_s, 0.0)
	assert_true(a._live_group()["voices"].has("bass"))
	assert_eq(str(a.voice_log[-1]["pack"]), B, "the reveal starts the second section's bass")
	a.queue_free()


func test_a_hotspot_dip_sinks_the_non_drum_voices_then_restores_them() -> void:
	var d := _data()
	var a := _audio(d)
	a._begin_phase(_phase_ev(d, "warehouse", 0.0), 0.0, 0.0, 0.0)
	a._run({"t": 16.0 * a.beat_s, "kind": "mix", "gains": d.cfg["stages"][1]["gains"]}, 0.0, 0.0)
	a._run({"t": 16.0 * a.beat_s, "kind": "reveal"}, 0.0, 0.0)
	var v: Dictionary = a._live_group()["voices"]
	var bass0 := float(v["bass"]["target"])
	var drums0 := float(v["drums"]["target"])
	a.on_event({"kind": "hotspot_commit", "t": 20.0 * a.beat_s, "outcome": {"music": "variation"}})
	var n0: int = a._schedule.size()
	a.on_event({"kind": "hotspot_commit", "t": 20.0 * a.beat_s, "outcome": {"music": "dip"}})
	assert_eq(a._schedule.size(), n0 + 2, "a dip schedules its start and its end; any other music value schedules nothing")
	a._run({"t": 20.0 * a.beat_s, "kind": "dip", "on": true}, 0.0, 0.0)
	assert_near(float(v["bass"]["target"]), bass0 * a.dip_gain(), 1e-6, "the bass aims lower")
	assert_near(float(v["drums"]["target"]), drums0, 1e-9, "the drums carry on")
	a._run({"t": 28.0 * a.beat_s, "kind": "dip", "on": false}, 0.0, 0.0)
	assert_near(float(v["bass"]["target"]), bass0, 1e-6, "the dip ends back at the mix")
	a.queue_free()


func test_a_stale_switch_after_the_phase_is_dropped() -> void:
	var d := _data()
	var a := _audio(d)
	a._begin_phase(_phase_ev(d, "warehouse", 0.0), 0.0, 0.0, 0.0)
	var ev2 := _phase_ev(d, "warehouse.bar", 64.0 * a.beat_s)
	ev2["phase"] = 2
	a._begin_phase(ev2, 64.0 * a.beat_s, 64.0 * a.beat_s, 0.0)
	var before: int = a.voice_log.size()
	a._run({"t": 32.0 * a.beat_s, "kind": "section", "phase": 1, "index": 1, "section": d.nodes["warehouse"]["sections"][1]}, 70.0 * a.beat_s, 0.0)
	assert_eq(a.voice_log.size(), before, "phase 1's switch does nothing once phase 2 is the live group")
	a.queue_free()


# --- the per-run seed ---------------------------------------------------------------------------------------------------------

func test_the_run_seed_is_stored_migrates_and_can_be_overridden() -> void:
	var path := "user://test_run_seed.json"
	for p in [path, path + ".tmp", path + ".corrupt"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
	var old := FileAccess.open(path, FileAccess.WRITE)  # a version 2 save from before the arrangements: no seed
	old.store_string(JSON.stringify({"version": 2, "reached": {"mothership": {"entries": 3}}, "runs": 4, "best_phases": 9, "migrated_from": ""}))
	old.close()
	var p := RunProgress.load_data(path, "user://none.json")
	assert_false(p.recovered_from_corrupt, "an older save is not set aside")
	assert_true(p.is_reached("mothership"), "its levels are kept")
	assert_true(p.data.has("seed") and p.run_seed() >= 0)
	var s0 := p.run_seed()
	p.run_started()
	assert_true(p.run_seed() != s0, "a run advances the seed for the next one")
	assert_eq(int(RunProgress.load_data(path, "user://none.json").data["seed"]), p.run_seed(), "the seed is saved")
	assert_eq(int(RunProgress.load_data(path, "user://none.json").data["version"]), 2, "the save version is unchanged")
	OS.set_environment("RW_RUN_SEED", "4242")
	assert_eq(RunData.run_seed(), 4242, "RW_RUN_SEED overrides the stored seed")
	OS.set_environment("RW_RUN_SEED", "")
	for q in [path, path + ".tmp"]:
		if FileAccess.file_exists(q):
			DirAccess.remove_absolute(q)
