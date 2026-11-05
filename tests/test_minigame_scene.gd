extends TestCase
## A minigame inside the real run scene on the virtual clock (docs/BLACKJACK_INTEGRATION.md 5.5): a fake activity is registered and the Warehouse's dancer hotspot is made to lead to it. The run stays at its
## scene while it lasts (cues, judging and energy go on, the bot keeps playing), the journey and the hotspot view are quiet, the HUD is silent, taps reach the activity through the view, and when it is
## done the adventure continues by the default exit.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_minigame_scene_save.json"

var _saved: RunProgress


func _scene(taps := "", bot := "perfect") -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_MINIGAME_TAPS", taps)
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
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS"]:
		OS.set_environment(k, "")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


## Registers the fake and makes the dancer's success sit the player down (with the join-the-circle walk as the outcome's cinematic).
func _arm(scene: Node, with_view := true) -> void:
	scene.minigames.register("fake", FakeMinigame, {"with_view": with_view})
	for h in scene.data.hotspots["warehouse"]:
		if h["id"] == "warehouse.dancer":
			h["on_success"] = {"activity": "fake", "cinematic": "warehouse.join_circle"}


func _blocks(scene: Node) -> Array:
	return (scene.event_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "block_result")


func _journey_moves(scene: Node) -> int:
	return (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move").size()


func test_a_run_that_never_touches_the_hotspot_is_unaffected() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_arm(scene)
	_run_to(scene, 130.0 * BEAT)
	assert_eq(scene.minigames.state, "")
	assert_eq(scene.minigames.log, [])
	assert_false(scene.hud.silent)
	assert_false(scene.engine.hold)
	assert_eq((scene.phase_log as Array).map(func(p: Dictionary) -> String: return str(p["node"])).slice(0, 2), ["warehouse", "warehouse.bar"], "the default exit as ever")
	_free(d)


func test_the_player_sits_the_run_stays_and_the_adventure_continues_when_it_is_over() -> void:
	var d := _scene("bet@2,zzz@3,exit@100")
	var scene: Node = d["scene"]
	_arm(scene)
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	_run_to(scene, 61.0 * BEAT)
	var mg: MinigameController = scene.minigames
	assert_eq(mg.state, "entering", "requested at the commit")
	assert_true(scene.engine.hold)
	var c: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")[0]
	assert_eq(c["route"], "warehouse", "the scene itself")
	assert_true(bool(c["success"]))
	assert_near(float(mg.log[0]["seat"]), 64.0 * BEAT, 1e-6, "the next downbeat")
	var fake := mg.activity as FakeMinigame
	assert_eq(fake.count("begin"), 0)
	assert_eq(scene.journey_log.filter(func(a: Dictionary) -> bool: return a["action"] == "player_move").size() > 0, true, "the cinematic walk to the chair may move the camera")
	_run_to(scene, 64.0 * BEAT - 0.05)
	assert_eq(fake.count("begin"), 0, "not before the downbeat")
	_run_to(scene, 64.5 * BEAT)
	assert_eq(mg.state, "active")
	assert_eq(fake.count("begin"), 1)
	assert_near(float(fake.calls[1]["t"]), 64.0 * BEAT, 1e-9, "seated on the downbeat")
	assert_true(scene.hud.silent, "the HUD is silent while seated")
	assert_true((scene.hotspot_items() as Array).is_empty(), "no hotspot is shown while seated")
	assert_false(scene.hotspot_select("warehouse.exit_bar"), "and none can be selected")
	assert_eq(scene.engine.node_id, "warehouse")
	# the view
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var layer: Node = st.lowres.sub.get_node_or_null("Minigame")
	assert_true(layer != null and int(layer.get("layer")) == 3, "the view is mounted on canvas layer 3 of the low-res viewport")
	var view := layer.get_child(0) as FakeMinigameView
	assert_true(view != null and view.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	assert_true(view.now_fn.is_valid() and view.beat_s > 0.0)
	var moves0 := _journey_moves(scene)
	var jlog0: int = scene.journey_log.size()
	var rail0: int = scene.journey.log.size()
	var blocks0 := _blocks(scene).size()
	var notes0: int = scene.engine.level.notes.size()
	# a scripted tap reaches the activity (bet@2 beats after sitting, zzz@3 is refused)
	_run_to(scene, 68.0 * BEAT)
	assert_eq(fake.count("tap"), 2)
	var mtaps: Array = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "minigame_tap")
	assert_eq(mtaps.map(func(e: Dictionary) -> bool: return bool(e["ok"])), [true, false], "both logged, the refused one too")
	# a touch is hit-tested by the view in stage-area screen pixels; a pad is never a target
	var host: Control = scene._stage_host
	scene.hotspot_tap(host.global_position + Vector2(host.size.x * 0.25, host.size.y * 0.3))
	assert_eq(view.screen_size, host.size, "the view is told the stage area's screen size")
	assert_true(view.hits[view.hits.size() - 1].is_equal_approx(Vector2(host.size.x * 0.25, host.size.y * 0.3)), "local to the stage area's top-left")
	assert_eq(fake.count("tap"), 3, "a touch on the left half is 'bet'")
	var pad_rect: Rect2 = scene.pad_view.button_rects()[1]
	var hits0 := view.hits.size()
	assert_eq(scene.hotspot_tap(pad_rect.get_center()), "", "a point over a pad is never a target")
	assert_eq(view.hits.size(), hits0, "the view is not even asked")
	# the run goes on under the table
	_run_to(scene, 150.0 * BEAT)
	assert_eq(scene.engine.node_id, "warehouse", "still the same scene two phases on")
	assert_eq(scene.engine.phase_n, 3)
	assert_true(scene.engine.hold)
	assert_true(_blocks(scene).size() >= blocks0 + 5, "blocks keep being judged")
	assert_true(_blocks(scene).slice(blocks0).all(func(e: Dictionary) -> bool: return bool(e["passed"])), "the bot still plays the pads")
	assert_true(scene.engine.level.notes.size() > notes0 + 10, "cues keep being charted")
	assert_eq(_journey_moves(scene), moves0, "no journey move while seated")
	assert_eq(scene.journey_log.size(), jlog0, "no journey action at all while seated")
	assert_eq(scene.journey.log.size(), rail0, "the rail took no step")
	assert_true(scene.hud.silent)
	assert_eq(fake.wobble, 0)
	# the exit tap (100 beats after sitting, i.e. phase 3 beat 36)
	_run_to(scene, 170.0 * BEAT)
	assert_eq(mg.state, "", "done")
	assert_eq(fake.done_reason(), "left")
	assert_false(scene.engine.hold)
	assert_false(scene.hud.silent)
	assert_true(layer.is_queued_for_deletion(), "the view is freed")
	var last_move: Dictionary = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move").back()
	assert_eq(last_move["args"]["to"], str(scene.data.nodes["warehouse"]["waypoint"]), "the camera walks back to the scene's home")
	assert_eq(last_move["args"]["bars"], 2.0)
	_run_to(scene, 200.0 * BEAT)
	assert_eq((scene.phase_log as Array).map(func(p: Dictionary) -> String: return str(p["node"])).slice(0, 4), ["warehouse", "warehouse", "warehouse", "warehouse.bar"], "the adventure continues by the default exit")
	_free(d)


func test_a_failed_last_block_is_the_dealer_waving_you_off() -> void:
	var d := _scene("", "blocks:1110")
	var scene: Node = d["scene"]
	_arm(scene)
	_run_to(scene, 49.5 * BEAT)
	scene.hotspot_select("warehouse.dancer")
	_run_to(scene, 66.0 * BEAT)
	var c: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")[0]
	assert_false(bool(c["success"]), "the last block was missed")
	assert_eq(scene.minigames.log, [], "no activity was requested")
	assert_false(scene.engine.hold)
	assert_eq((scene.phase_log as Array).map(func(p: Dictionary) -> String: return str(p["node"])).slice(0, 2), ["warehouse", "warehouse.bar"], "the scene went on by its default exit")
	_free(d)


func test_three_failed_blocks_at_the_table_make_the_player_fall() -> void:
	var d := _scene("", "blocks:1111")  # phase 1 is played, everything after is missed
	var scene: Node = d["scene"]
	_arm(scene, false)
	_run_to(scene, 49.5 * BEAT)
	scene.hotspot_select("warehouse.dancer")
	_run_to(scene, 64.5 * BEAT)
	var fake := scene.minigames.activity as FakeMinigame
	assert_eq(scene.minigames.state, "active")
	_run_to(scene, 64.0 * BEAT + 3.0 * 16.0 * BEAT)
	assert_eq(fake.wobble, 1, "two misses wobbled")
	assert_eq(fake.count("interrupt"), 1, "the third made the player fall")
	assert_eq(fake.done_reason(), "fall")
	assert_eq(scene.minigames.state, "")
	assert_false(scene.engine.hold)
	assert_false(scene.hud.silent)
	_free(d)


## Exits while seated, through the generic layer: the room's ways out reach the activity, a door touched in the minigame travels to the run scene, the camera walks toward that door, and
## the door's exit hotspot is selected when the final window opens, so the last block decides as if the player had touched that door in the room.
func test_a_door_taken_in_the_minigame_is_the_rooms_exit_at_the_next_route_lock() -> void:
	var d := _scene("exit:warehouse.balcony@6")
	var scene: Node = d["scene"]
	_arm(scene, false)
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	_run_to(scene, 64.5 * BEAT)
	var mg: MinigameController = scene.minigames
	var fake := mg.activity as FakeMinigame
	assert_eq(fake.exits.map(func(e: Dictionary) -> String: return str(e["route"])), ["warehouse.bar", "warehouse.balcony"], "the room's two exits, the default first")
	assert_eq(str(fake.exits[1]["id"]), "warehouse.exit_balcony")
	assert_eq(str(fake.exits[1]["dir"]), "up")
	assert_eq(str(fake.exits[1]["world"]), "warehouse")
	assert_eq(str(fake.exits[1]["scene"]), str(scene.data.nodes["warehouse.balcony"]["scene"]))
	assert_true(bool(fake.exits[0]["default"]))
	fake.taken = ["bet"] + fake.exit_targets()
	_run_to(scene, 71.0 * BEAT)
	assert_eq(mg.state, "", "left at beat 6 after sitting")
	assert_eq(mg.last_route, "warehouse.balcony")
	assert_eq((mg.log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "leave")[0]["route"], "warehouse.balcony", "the route is logged")
	assert_eq(scene._mg.pending_exit, "warehouse.exit_balcony", "the door waits for the final window")
	var walk: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_walk" and str(a["args"].get("to", "")) == "to_balcony")
	assert_eq(walk.size(), 1, "the camera walks toward that door")
	assert_eq(str(walk[0]["args"]["face"]), "to_balcony")
	_run_to(scene, (64.0 + 49.0) * BEAT)
	assert_eq(scene.hotspots.selected, "warehouse.exit_balcony", "selected as the window opens")
	assert_eq(scene._mg.pending_exit, "")
	assert_true((scene.hotspot_log as Array).any(func(e: Dictionary) -> bool: return e["kind"] == "select" and e["hotspot"] == "warehouse.exit_balcony"), "through the same path a finger takes")
	_run_to(scene, (64.0 + 66.0) * BEAT)
	assert_eq((scene.phase_log as Array).map(func(p: Dictionary) -> String: return str(p["node"])).slice(0, 3), ["warehouse", "warehouse", "warehouse.balcony"], "out by the balcony")
	_free(d)
