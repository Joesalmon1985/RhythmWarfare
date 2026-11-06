extends TestCase
## The Gospel path (docs/THREE_PATHS_AND_FACES_PLAN.md section 4, Stage 3): 17 scenes at 124 BPM in four worlds, each a view of one of four maps. Data first (the graph, the maps, the cast and the acting,
## the placeholder music), then the engine's additions the path uses (set pieces switched by a scene, a result or a block; the sky of a sector), then the real scene on its virtual clock to both endings.

const TMP_SAVE := "user://test_gospel_save.json"
const SCENES := ["jordan", "jordan.baptism", "jordan.wilderness", "jordan.nazareth", "galilee", "galilee.capernaum", "galilee.mount", "galilee.storm", "road", "road.loaves", "road.entry", "jerusalem",
	"jerusalem.gethsemane", "jerusalem.trial", "jerusalem.golgotha", "jerusalem.tomb", "jerusalem.road"]
const MAPS := {"jordan": "galilee_shore", "galilee": "hillside", "road": "bethany", "jerusalem": "jerusalem"}

var _saved: RunProgress


func test_the_path_loads_with_its_seventeen_scenes_at_124_bpm() -> void:
	var d := RunData.load_path("gospel")
	assert_eq(d.errors, [], "the gospel path validates")
	assert_eq(d.path_id, "gospel")
	assert_eq(d.node_order, SCENES, "the scenes in the plan's order")
	assert_eq(int(d.cfg["timing"]["bpm"]), 124)
	for w in MAPS:
		assert_eq(str(d.worlds[w]["map"]), MAPS[w], "world %s is drawn on the map %s" % [w, MAPS[w]])
		assert_true(FileAccess.file_exists(str(d.worlds[w]["story"]).replace("res://", "res://")), "the world's story data exists")
	assert_eq(d.nodes["jerusalem.tomb"]["ending"], "tomb")
	assert_eq(d.nodes["jerusalem.road"]["ending"], "road")
	for id in d.node_order:
		assert_true(bool(d.nodes[id]["temporary"]), "%s plays a placeholder" % id)
		assert_true(str(d.packs[str(d.nodes[id]["audio"])].get("path", "")) == "gospel", "%s's pack belongs to the path" % id)
		assert_eq(int(d.packs[str(d.nodes[id]["audio"])]["bpm"]), 124)
	assert_eq(d.skipped_portals, [], "no portal of the path is skipped")


func test_the_graph_reaches_every_scene_and_both_endings_and_sets_their_flags() -> void:
	var d := RunData.load_path("gospel")
	var seen := {"jordan": true}
	var flags := {}
	var queue: Array = ["jordan"]
	var endings := {}
	while not queue.is_empty():
		var sid: String = queue.pop_front()
		for h in d.hotspots_of(sid):
			for key in ["on_success", "on_failure"]:
				var oc: Dictionary = h[key]
				var r := str(oc.get("route", ""))
				if r == "run:warehouse":
					endings[sid] = true
					for f in oc.get("flags_set", []):
						flags[str(f)] = true
				elif r != "" and d.nodes.has(r) and not seen.has(r):
					seen[r] = true
					queue.append(r)
	assert_eq(seen.size(), 17, "every scene is reachable from the first")
	assert_true(endings.has("jerusalem.tomb") and endings.has("jerusalem.road"))
	assert_true(flags.has("keep:path_gospel_tomb") and flags.has("keep:path_gospel_road"), "the endings set their keep: flags")
	for sid in ["jerusalem.tomb", "jerusalem.road"]:
		var defaults: Array = d.hotspots_of(sid).filter(func(h: Dictionary) -> bool: return bool(h["default"]))
		assert_eq(defaults.size(), 1)
		assert_eq(str(defaults[0]["on_success"]["route"]), "run:warehouse")
		assert_true((defaults[0]["on_success"]["flags_set"] as Array)[0].begins_with("keep:path_gospel_"))


func test_every_scene_has_cast_and_every_character_hotspot_has_its_acting() -> void:
	var d := RunData.load_path("gospel")
	for sid in SCENES:
		var n: Dictionary = d.nodes[sid]
		assert_true((n.get("cast", []) as Array).size() >= 2 or sid == "jerusalem.golgotha", "%s has cast lines" % sid)
		var shown := d.hotspots_of(sid)
		assert_true(shown.size() >= 2 and shown.size() <= 4, "%s: %d hotspots" % [sid, shown.size()])
		for h in shown:
			if str(h["kind"]) == "character":
				var act: Dictionary = h.get("acting", {})
				assert_false(act.is_empty(), "%s has acting" % h["id"])
				for st in ["available", "selected", "committed", "success", "failure"]:
					assert_true(act.has(st), "%s acting.%s" % [h["id"], st])
	assert_true(d.nodes["jerusalem.golgotha"].has("block_fx"), "Golgotha is staged by the play")
	assert_eq((d.nodes["jerusalem.golgotha"]["block_fx"] as Array).size(), 4)
	assert_true(d.nodes["jordan.wilderness"]["cast"].size() >= 3, "the tempter acts")


func test_the_disciples_are_stable_ids_and_the_people_sheets_carry_them() -> void:
	for m in ["hillside", "bethany", "jerusalem"]:
		var data := StoryData.load_file("res://content/story/%s.json" % m)["data"] as StoryData
		var ids: Array = data.actors.map(func(a: Dictionary) -> String: return str(a["id"]))
		var base := ids.map(func(i: String) -> String: return i.get_slice("_", 0))
		assert_true("d01" in base or "d09" in base, "%s has disciples" % m)
		var people: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/story/%s/people/people.json" % m))
		for id in ids:
			assert_true((people["actors"] as Dictionary).has(id), "%s: %s is baked" % [m, id])
		for a in data.actors:
			if str(a["id"]).begins_with("d") and str(a.get("seed_id", "")).length() == 3:
				assert_eq(str(a["seed_id"]), str(a["id"]).get_slice("_", 0), "a disciple's look comes from its stable id")


func test_the_placeholder_mix_is_bass_forward() -> void:
	var d := RunData.load_path("gospel")
	for sid in d.node_order:
		var p: Dictionary = d.packs[str(d.nodes[sid]["audio"])]
		var lv: Dictionary = p["levels"]
		var bass := float(lv["bass"]["rms_db"])
		assert_true(bass > float(lv["drums"]["rms_db"]) + 5.0, "%s: the bass is clearly louder than the drums" % sid)
		assert_true(bass > float(lv["other"]["rms_db"]) + 10.0, "%s: and than the pad" % sid)
		assert_true(float(lv["bass"]["sub_share"]) >= 0.5, "%s: a present sub" % sid)


func test_the_maps_name_the_skies_their_sectors_use() -> void:
	for m in MAPS.values():
		var mp := StoryMap.load_chapter(str(m))
		assert_eq(mp.errors, [], "%s validates with its files" % m)
		var names: Dictionary = mp.sky.get("by_name", {})
		assert_false(names.is_empty())
		for s in mp.sectors:
			if str(s.get("sky", "")) != "":
				assert_true(names.has(str(s["sky"])), "%s: sector %s names a sky" % [m, s["id"]])
		var assets := StoryAssets.load_art(str(m))
		assert_true(assets.ok())
		for p in mp.things:
			if p.has("piece"):
				assert_false(assets.piece(str(p["piece"])).is_empty(), "%s: piece %s is in the manifest" % [m, p["piece"]])


# --- the engine's additions ------------------------------------------------------------------------------------------------------

func test_the_pieces_contract_rejects_a_piece_the_map_does_not_have() -> void:
	var errors: Array = []
	var idx := HotspotContract.map_index("jerusalem")
	HotspotContract.validate_pieces({"on": ["temple.t1_over"], "off": ["temple.t1_up"]}, "x", idx, errors)
	assert_eq(errors, [])
	HotspotContract.validate_pieces({"on": ["nope"], "typo": []}, "x", idx, errors)
	assert_eq(errors.size(), 2, "an unknown piece and an unknown field: %s" % str(errors))


# --- the real scene -----------------------------------------------------------------------------------------------------------------

func _isolate_save() -> void:
	_saved = Session.run_progress
	var f := FileAccess.open(TMP_SAVE, FileAccess.WRITE)
	f.store_string("{}")
	f.close()
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")


func _scene(env: Dictionary) -> Dictionary:
	_isolate_save()
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_PATH", "gospel")
	for k in env:
		OS.set_environment(str(k), str(env[k]))
	Session.run_start_node = ""
	Session.run_start_path = ""
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	return {"host": host, "scene": scene, "env": env.keys()}


func _free(d: Dictionary) -> void:
	if _saved != null:
		Session.run_progress = _saved
		_saved = null
	DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_FLAGS", "RW_RUN_START", "RW_RUN_PATH", "RW_RUN_TAPS", "RW_RUN_PATH_START"]:
		OS.unset_environment(k)


func _run_until(scene: Node, t_end: float, stop: Callable) -> void:
	var t: float = scene._vt
	while t < t_end and not stop.call():
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_golgotha_darkens_block_by_block_and_the_play_decides_who_acts() -> void:
	var d := _scene({"RW_RUN_START": "jerusalem.golgotha", "RW_RUN_TAPS": "none"})
	var scene: Node = d["scene"]
	_run_until(scene, 64.0 * 60.0 / 124.0 - 0.5, func() -> bool: return false)
	var ons: Array = []
	for p in scene.piece_log:
		ons.append_array(p["on"])
	for k in ["hill.dark1", "hill.dark2", "hill.dark3"]:
		assert_true(k in ons, "%s is switched on by its block (%s)" % [k, str(ons)])
	var gst: StoryStage = scene.stages["jerusalem"]["stage"]
	var gt: float = scene._vt
	assert_true(gst.people_gain(gt) < 0.8, "the darkened sky dims the people in front of the hill too, not only the sky behind it (%.2f)" % gst.people_gain(gt))
	assert_true(gst.people_gain(gt) > 0.45, "but they still read (%.2f)" % gst.people_gain(gt))
	var who: Array = scene.cast_log.filter(func(c: Dictionary) -> bool: return str(c["source"]) == "block").map(func(c: Dictionary) -> String: return "%s:%s" % [c["actor"], c["act"]])
	assert_true("x1:kneel" in who and "x2:kneel" in who and "x3:kneel" in who, "perfect play brings a witness forward each block: %s" % str(who))
	assert_false("s1:laugh" in who, "and no soldier laughs")
	_free(d)
	d = _scene({"RW_RUN_START": "jerusalem.golgotha", "RW_RUN_TAPS": "none", "RW_RUN_BOT": "none"})
	scene = d["scene"]
	_run_until(scene, 64.0 * 60.0 / 124.0 - 0.5, func() -> bool: return false)
	who = scene.cast_log.filter(func(c: Dictionary) -> bool: return str(c["source"]) == "block").map(func(c: Dictionary) -> String: return "%s:%s" % [c["actor"], c["act"]])
	assert_true("s1:laugh" in who and "s2:laugh" in who, "a missed block brings a soldier's laugh: %s" % str(who))
	assert_false("x1:kneel" in who, "and no witness")
	_free(d)


func test_a_result_switches_the_pieces_the_tables_fall_and_the_next_scene_starts_clean() -> void:
	var d := _scene({"RW_RUN_START": "jerusalem", "RW_RUN_TAPS": "none"})
	var scene: Node = d["scene"]
	var st: StoryStage = scene.stages["jerusalem"]["stage"]
	_run_until(scene, 6.0, func() -> bool: return false)
	assert_true(bool(st.piece_state("temple.t2_up", scene._vt)["visible"]), "the tables stand at first")
	assert_false(bool(st.piece_state("temple.t2_over", scene._vt)["visible"]))
	_run_until(scene, 51.0 * 60.0 / 124.0, func() -> bool: return false)
	assert_true(scene.hotspot_select("jerusalem.tables"), "the scene plays two laps; selection is open for the whole scene (N2.1), so the tables can be touched in the first lap too")
	assert_false(scene.engine.window_open, "but the engine's route window is the second lap's: the touch waits for its lock")
	_run_until(scene, (64.0 + 51.0) * 60.0 / 124.0, func() -> bool: return false)
	assert_true(scene.hotspot_select("jerusalem.tables"), "the money-changers' tables can be touched in the window (the second lap's)")
	_run_until(scene, (64.0 + 63.0) * 60.0 / 124.0, func() -> bool: return false)
	var t: float = scene._vt + 1.5
	assert_true(bool(st.piece_state("temple.t2_over", t)["visible"]), "they are overturned after the commit")
	assert_false(bool(st.piece_state("temple.t2_up", t)["visible"]), "and the standing ones are gone")
	assert_true(scene.hotspots.has_flag("gospel_tables"))
	_free(d)


func test_the_tomb_stone_rolls_at_the_first_block_and_the_tomb_ending_sets_its_flag() -> void:
	var d := _scene({"RW_RUN_START": "jerusalem.tomb", "RW_RUN_TAPS": "none"})
	var scene: Node = d["scene"]
	var st: StoryStage = scene.stages["jerusalem"]["stage"]
	_run_until(scene, 8.0, func() -> bool: return false)
	assert_true(bool(st.piece_state("tomb.stone_closed", scene._vt)["visible"]))
	_run_until(scene, 20.0 * 60.0 / 124.0, func() -> bool: return false)
	assert_false(bool(st.piece_state("tomb.stone_closed", scene._vt + 1.5)["visible"]), "the stone has moved")
	assert_true(bool(st.piece_state("tomb.stone_rolled", scene._vt + 1.5)["visible"]))
	_run_until(scene, 200.0, func() -> bool: return not scene.path_log.is_empty())
	assert_eq(scene.path_log.size(), 1)
	assert_eq(str(scene.path_log[0]["ending"]), "tomb")
	assert_true(Session.run_progress.flags.has("keep:path_gospel_tomb"))
	assert_eq(Session.run_progress.path_endings("gospel"), ["tomb"])
	assert_eq(scene.run_path, "", "and the run is back in the Warehouse")
	_free(d)


func test_the_road_ending_sets_its_flag_and_the_storm_is_on_in_its_scene() -> void:
	var d := _scene({"RW_RUN_START": "jerusalem.road", "RW_RUN_TAPS": "none"})
	var scene: Node = d["scene"]
	_run_until(scene, 200.0, func() -> bool: return not scene.path_log.is_empty())
	assert_eq(str(scene.path_log[0]["ending"]), "road")
	assert_true(Session.run_progress.flags.has("keep:path_gospel_road"))
	_free(d)
	d = _scene({"RW_RUN_START": "galilee.storm", "RW_RUN_TAPS": "none"})
	scene = d["scene"]
	var st: StoryStage = scene.stages["hillside"]["stage"]
	_run_until(scene, 6.0, func() -> bool: return false)
	for pid in ["storm.storm_cloud", "storm.rain", "storm.lightning"]:
		assert_true(bool(st.piece_state(pid, scene._vt)["visible"]), "%s is on in the storm" % pid)
	_free(d)


func test_the_balcony_star_opens_the_path_for_real_and_the_walk_runs_the_whole_way() -> void:
	var d := _scene({"RW_RUN_PATH": "", "RW_RUN_FLAGS": "wh_saw_floor", "RW_RUN_PORTAL": "warehouse.balcony.star", "RW_RUN_START": "warehouse.balcony", "RW_RUN_TAPS": "scripted"})
	var scene: Node = d["scene"]
	assert_eq(scene.run_path, "")
	_run_until(scene, 40.0, func() -> bool: return not scene.path_log.is_empty())
	assert_eq(scene.path_log.size(), 1, "the portal was entered without any remap")
	assert_eq(scene.run_path, "gospel")
	assert_eq(scene.engine.node_id, "jordan")
	assert_near(scene.engine.beat_s, 60.0 / 124.0, 1e-12)
	assert_true(scene.stages.has("galilee_shore"), "its first art world is built")
	_free(d)
