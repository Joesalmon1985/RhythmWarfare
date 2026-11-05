extends TestCase
## The hotspot window in the real run scene on the virtual clock: a tap selects, a second tap changes, the commit is at the last decision beat and the last block decides success or failure, nothing
## tapped takes the default exit, a cinematic replaces the door walk, the wizard is a character hotspot that arms the Bassment, keys 1 to 4 select, and the flag brings the arrows back.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_hotspots_scene_save.json"

var _saved: RunProgress


func _scene(bot := "perfect", start := "") -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	if start != "":
		OS.set_environment("RW_RUN_START", start)
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES"]:
		OS.set_environment(k, "")
	OS.unset_environment("RW_RUN_START")
	OS.unset_environment("RW_RUN_ARROWS")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func _commits(scene: Node) -> Array:
	return (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")


func test_the_view_lives_inside_the_low_res_viewport_above_the_crowd() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var rec: Dictionary = scene.stages[scene.active_world]
	assert_true(rec.has("hotspot_view"), "a hotspot view per stage")
	var hv: HotspotView = rec["hotspot_view"]
	assert_true((rec["stage"] as StoryStage).lowres.sub.is_ancestor_of(hv), "inside the low-res sub viewport")
	assert_eq(hv.get_parent().get("layer"), 2, "on its own canvas layer above the crowd's")
	_free(d)


func test_a_tap_then_a_change_then_the_commit_at_the_last_decision_beat() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.exit_bar"))
	assert_eq(scene.hotspots.selected, "warehouse.exit_bar")
	_run_to(scene, 55.0 * BEAT)
	assert_true(scene.hotspot_select("warehouse.exit_balcony"), "changed his mind")
	_run_to(scene, 60.0 * BEAT)
	assert_eq(_commits(scene).size(), 0, "nothing commits before the last block's decision")
	_run_to(scene, 61.0 * BEAT)
	var c: Array = _commits(scene)
	assert_eq(c.size(), 1)
	assert_eq(c[0]["hotspot"], "warehouse.exit_balcony")
	assert_true(bool(c[0]["success"]), "perfect play: the intent happens")
	assert_true(float(c[0]["t"]) >= 60.0 * BEAT and float(c[0]["t"]) < 61.0 * BEAT, "at the decision beat inside the guard: %f" % (float(c[0]["t"]) / BEAT))
	assert_false(scene.hotspot_select("warehouse.exit_bar"), "after the commit nothing can be selected")
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.engine.node_id, "warehouse.balcony")
	_free(d)


func test_nothing_tapped_is_the_default_exit() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.engine.node_id, "warehouse.bar", "the first route: the door that stands ajar")
	var c: Array = _commits(scene)
	assert_false(bool(c[0]["tapped"]))
	_free(d)


func test_a_missed_last_block_fails_the_tapped_hotspot() -> void:
	var d := _scene("blocks:1110")
	var scene: Node = d["scene"]
	_run_to(scene, 52.0 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	var energy_before: float = scene.engine.energy
	_run_to(scene, 61.0 * BEAT)
	var c: Array = _commits(scene)
	assert_false(bool(c[0]["success"]), "the last block was missed")
	assert_false(scene.run_flag_set("wh_circle"), "the circle did not form")
	assert_true(scene.engine.energy < energy_before, "the failure cost energy")
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.engine.node_id, "warehouse.bar", "an interaction without a route continues by the default exit")
	_free(d)


func test_a_cinematic_is_the_move_when_the_scene_continues_by_its_default() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 52.0 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	_run_to(scene, 63.0 * BEAT)
	assert_true(scene.run_flag_set("wh_circle"), "success: the flag")
	var moves: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and float(a["t0"]) > 59.0 * BEAT and float(a["t0"]) < 64.0 * BEAT)
	var cine: Array = moves.filter(func(a: Dictionary) -> bool: return a["args"]["to"] == "floor_centre")
	assert_eq(cine.size(), 1, "the cinematic: a walk to the circle")
	assert_true(fposmod(float(cine[0]["t0"]) / BEAT, 16.0) >= 12.0, "starting inside a cue-free guard")
	assert_eq(moves.filter(func(a: Dictionary) -> bool: return absf(float(a["t0"]) - 61.0 * BEAT) < 0.05).size(), 0, "and no door walk at beat 61: the cinematic is the move")
	_free(d)


func test_the_wizard_is_a_character_hotspot_that_arms_the_bassment_when_the_block_is_passed() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	assert_true(scene._gate_btn == null, "no written button")
	_run_to(scene, 3.0 * BEAT)
	assert_true(scene.hotspot_items().any(func(e: Dictionary) -> bool: return e["hotspot"]["id"] == "warehouse.wizard"), "he is on show in the first blocks")
	assert_true(scene.hotspot_select("warehouse.wizard"))
	assert_eq(scene.trial_state, "", "a touch alone does nothing")
	_run_to(scene, 13.5 * BEAT)
	assert_eq(scene.trial_state, "armed", "the first block passed: the walk to the hatch is scheduled (the existing seamless entry)")
	_free(d)


func test_the_wizard_shrugs_when_the_block_is_missed() -> void:
	var d := _scene("blocks:0111")
	var scene: Node = d["scene"]
	_run_to(scene, 3.0 * BEAT)
	assert_true(scene.hotspot_select("warehouse.wizard"))
	_run_to(scene, 13.5 * BEAT)
	assert_eq(scene.trial_state, "", "no dungeon")
	assert_false(bool(_commits(scene)[0]["success"]))
	assert_true(scene.run_flag_set("wh_wizard_shrug"))
	_free(d)


func test_keys_one_to_four_select_the_hotspots_in_order() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	var shown: Array = scene.hotspots.shown(scene.engine.block, scene.engine.window_open)
	var ev := InputEventKey.new()
	ev.pressed = true
	ev.keycode = KEY_2
	scene._unhandled_key_input(ev)
	assert_eq(scene.hotspots.selected, str(shown[1]["id"]), "key 2 is the second hotspot on show")
	_free(d)


func test_the_arrows_come_back_behind_the_flag() -> void:
	OS.set_environment("RW_RUN_ARROWS", "1")
	var d := _scene()
	var scene: Node = d["scene"]
	assert_true(scene.hotspots == null and scene.engine.hotspots == null)
	_run_to(scene, 50.0 * BEAT)
	assert_true(scene._route_buttons.size() >= 2, "the old arrows")
	assert_true(scene._gate_btn != null, "and the old wizard button")
	_free(d)
