extends TestCase
## Work package N2.1 in the real run scene on the virtual clock (docs/parallel-development/INTERACTION_DESIGN.md 2.2 to 2.6, 7.2): selection is open from the first bar to the lock (the port's
## selection_open()), one tap selects and the object answers within a beat, a second tap moves the pick and the first deselects at once, the selected one tapped again stays (A1), the pick
## commits exactly once at the departure boundary (the director's lock), nothing picked is the scene's default, a tap in the lock window is refused once, a path scene holds a first-lap pick
## for its last lap, the bot changes its mind twice over a whole scene, keys 1 to 8, the touch regions stay off the pads and the pause button, a world tap works while a pad is held, and a
## reactive object reacts without touching the pick or the port.

const TMP_SAVE := "user://test_interaction_scene_save.json"
const VIEW := Vector2(1280, 720)

var _saved: RunProgress


func _scene(env: Dictionary = {}) -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	var base := {"RW_RUN_VIRTUAL": "1", "RW_RUN_BOT": "perfect", "RW_RUN_ROUTES": "", "RW_RUN_TAPS": "none"}
	for k in env:
		base[k] = env[k]
	for k in base:
		OS.set_environment(k, str(base[k]))
	Session.run_start_node = ""
	var host := Control.new()
	host.size = VIEW
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = VIEW
	return {"host": host, "scene": scene, "env": base.keys()}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in d["env"]:
		OS.unset_environment(str(k))
	for k in ["RW_RUN_START", "RW_RUN_PATH"]:
		OS.unset_environment(k)


func _to_beat(scene: Node, beat: float) -> void:  # a beat of the current scene's first lap (beats past 64 run into the next lap)
	var t_end: float = scene.engine.scene_t0 + beat * scene.engine.beat_s
	var t: float = scene._vt
	while t < t_end:
		t = minf(t + 1.0 / 30.0, t_end)
		scene._vt = t
		scene._step_virtual(t)


func _log(scene: Node, kind: String) -> Array:
	return (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == kind)


func _ids(items: Array) -> Array:
	return items.map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))


func _state_of(scene: Node, id: String) -> String:
	for e in scene.hotspot_items():
		if str(e["hotspot"]["id"]) == id:
			return str(e["state"])
	return ""


## The layout the taps use right now (RunPlay.hotspot_tap), in stage-host coordinates.
func _lay(scene: Node, items: Array) -> Array:
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var host: Control = scene._stage_host
	return HotspotView.layout(items, st.map, st.crowds, scene._exit_pose(), host.size, true, HotspotView.thing_widths(st))


## A point (viewport coordinates) that taps `id` and only it, or Vector2(-1, -1).
func _tap_point(scene: Node, id: String) -> Vector2:
	var items: Array = (scene.hotspot_items() as Array).filter(func(e: Dictionary) -> bool: return str(e["state"]) != "committed")
	var lay := _lay(scene, items)
	for e in lay:
		if str(e["id"]) == id:
			var p: Vector2 = e.get("hit_centre", e["centre"])
			if HotspotView.hit(lay, p) == id:
				return p + (scene._stage_host as Control).global_position
	return Vector2(-1, -1)


# --- selection open from the first bar to the lock ------------------------------------------------------------------------------

func test_selection_is_open_from_the_first_bar_to_the_lock_and_the_choices_are_on_show_all_scene() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var port: TransitionPort = scene.port()
	_to_beat(scene, 0.5)
	assert_true(port.selection_open(), "open on the first beat")
	assert_true(_ids(scene.hotspot_items()).has("warehouse.exit_balcony"), "the doors are on show from the first beat, not only in the window")
	assert_true(scene.hotspot_select("warehouse.exit_balcony"), "and touchable")
	var open_beats := 0
	for b in 64:
		_to_beat(scene, float(b) + 0.25)
		if port.selection_open():
			open_beats += 1
			assert_eq(scene.hotspots.selected, "warehouse.exit_balcony", "the pick is held at beat %d" % b)
	assert_eq(open_beats, 61, "open on beats 0 to 60 (60.5 is the lock): %d of 64, 95%%" % open_beats)
	assert_false(port.selection_open(), "closed from the lock to the boundary")
	assert_false(scene.hotspot_select("warehouse.exit_bar"), "a touch in the lock window is not taken")
	var refused := _log(scene, "refused")
	assert_eq(refused.size(), 1, "it is refused once")
	assert_eq(str(refused[0]["reason"]), "locked")
	assert_eq(_state_of(scene, "warehouse.exit_bar"), "refused", "the door recoils")
	_to_beat(scene, 64.4)
	assert_eq(scene.engine.node_id, "warehouse.balcony", "the pick of the first beat is where the run went")
	assert_true(port.selection_open(), "open again in the next scene")
	assert_true(_ids(scene.hotspot_items()).all(func(i: String) -> bool: return i.begins_with("warehouse.balcony.")), "with its own choices on show from its first beat")
	_free(d)


func test_one_tap_selects_and_the_object_answers_within_a_beat_and_a_second_tap_moves_it() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 3.0)
	var p := _tap_point(scene, "warehouse.exit_balcony")
	assert_true(p.x >= 0.0, "the balcony stair can be tapped from the start camera")
	assert_eq(scene.hotspot_tap(p), "warehouse.exit_balcony", "one tap selects")
	assert_eq(_state_of(scene, "warehouse.exit_balcony"), "selected", "selected in the same frame (the first sign of the tap)")
	var hv: HotspotView = scene.stages[scene.active_world]["hotspot_view"]
	_to_beat(scene, 4.0)
	var s := hv.refresh_choice(float(scene.hud.now_t))
	assert_eq(str(s["current"]), "warehouse.exit_balcony")
	assert_true(float(s["options"]["warehouse.exit_balcony"]["open_k"]) > 0.99, "its door is open within a beat")
	assert_true(float(s["options"]["warehouse.exit_bar"]["open_k"]) < 0.01, "and the default's is shut")
	assert_true(scene.hotspot_select("warehouse.exit_bar"), "a second tap on another choice")
	assert_eq(_state_of(scene, "warehouse.exit_bar"), "selected")
	assert_eq(_state_of(scene, "warehouse.exit_balcony"), "available", "the old pick deselects in the same frame")
	assert_true(scene.hotspot_select("warehouse.exit_bar"), "the selected one tapped again (assumption A1)")
	assert_eq(scene.hotspots.selected, "warehouse.exit_bar", "stays selected")
	var sel := _log(scene, "select")
	assert_eq(sel.size(), 3)
	assert_true(bool(sel[2]["again"]) and not bool(sel[1]["again"]), "the repeat is logged as one")
	assert_true(float(sel[0]["beat"]) < 4.0, "the first touch was in the first block")
	_free(d)


func test_the_pick_commits_exactly_once_at_the_lock_and_nothing_picked_is_the_default() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 2.0)
	assert_true(scene.hotspot_select("warehouse.exit_balcony"))
	_to_beat(scene, 60.0)
	assert_eq(_log(scene, "commit").size(), 0, "nothing commits before the lock")
	_to_beat(scene, 64.4)
	var c := _log(scene, "commit")
	assert_eq(c.size(), 1, "one commit")
	assert_eq(str(c[0]["hotspot"]), "warehouse.exit_balcony")
	assert_true(bool(c[0]["tapped"]))
	var beat_c: float = (float(c[0]["t"]) - 0.0) / scene.engine.beat_s
	assert_true(beat_c >= 60.0 and beat_c < 61.0, "at the lock beat (%f)" % beat_c)
	var locks: Array = (scene.director as TransitionDirector).lock_log
	assert_eq(locks.size(), 1, "the director locked once")
	assert_eq(str(locks[0]["route"]), "warehouse.balcony")
	assert_eq(scene.engine.node_id, "warehouse.balcony")
	_free(d)
	var d2 := _scene()
	var s2: Node = d2["scene"]
	_to_beat(s2, 64.4)
	var c2 := _log(s2, "commit")
	assert_eq(c2.size(), 1)
	assert_false(bool(c2[0]["tapped"]), "nothing picked")
	assert_eq(s2.engine.node_id, "warehouse.bar", "the scene's default, as today")
	_free(d2)


func test_a_path_scene_holds_a_first_lap_pick_until_the_lock_of_its_last_lap() -> void:
	var d := _scene({"RW_RUN_PATH": "gospel", "RW_RUN_START": "jordan.baptism"})
	var scene: Node = d["scene"]
	var e: RunEngine = scene.engine
	assert_eq(e.laps, 2)
	_to_beat(scene, 4.0)
	var other := ""
	for h in scene.hotspots.shown(e.block, true):
		var r := str((h["on_success"] as Dictionary).get("route", ""))
		if not bool(h["default"]) and RunHotspots.window_of(h) == "final" and r != "" and r != e.default_route() and scene.data.nodes.has(r):
			other = str(h["id"])
			break
	assert_true(other != "", "a second way on in the first lap")
	assert_true(scene.hotspot_select(other), "touched in the first lap")
	_to_beat(scene, 62.0)
	assert_eq(e.lap, 1)
	assert_true(scene.port().selection_open(), "no lock on a lap that is no departure lap")
	assert_eq(_log(scene, "commit").size(), 0, "nothing commits at the first lap's last decision")
	assert_eq(scene.hotspots.selected, other, "the pick is held")
	_to_beat(scene, 64.0 + 61.0)
	assert_eq(e.lap, 2)
	var c := _log(scene, "commit")
	assert_eq(c.size(), 1, "it commits once, at the second lap's lock")
	assert_eq(str(c[0]["hotspot"]), other)
	var want := str((scene.hotspots.get_hotspot(other)["on_success"] as Dictionary)["route"])
	_to_beat(scene, 128.4)
	assert_eq(scene.engine.node_id, want, "and the run goes there")
	_free(d)


func test_the_bot_changes_its_mind_twice_over_a_whole_scene_and_the_last_pick_goes() -> void:
	var d := _scene({"RW_RUN_TAPS": "mind", "RW_RUN_ROUTES": "up"})  # the floor: up is the balcony
	var scene: Node = d["scene"]
	_to_beat(scene, 64.4)
	var sel: Array = _log(scene, "select").filter(func(x: Dictionary) -> bool: return int(x["phase"]) == 1)
	assert_eq(sel.size(), 3, "three touches: the pick, a change of mind, a change back: %s" % str(sel))
	assert_eq(str(sel[0]["hotspot"]), "warehouse.exit_balcony")
	assert_true(float(sel[0]["beat"]) < 3.0, "early in the scene")
	assert_true(str(sel[1]["hotspot"]) != "warehouse.exit_balcony", "a decoy")
	assert_eq(str(sel[2]["hotspot"]), "warehouse.exit_balcony")
	assert_true(float(sel[2]["beat"]) > 57.0 and float(sel[2]["beat"]) < 60.5, "late, before the lock (%f)" % float(sel[2]["beat"]))
	var c: Array = _log(scene, "commit").filter(func(x: Dictionary) -> bool: return int(x["phase"]) == 1)
	assert_eq(c.size(), 1, "one commit")
	assert_eq(str(c[0]["hotspot"]), "warehouse.exit_balcony")
	assert_eq(scene.engine.node_id, "warehouse.balcony")
	_free(d)
	var d2 := _scene({"RW_RUN_TAPS": "early", "RW_RUN_ROUTES": "up"})
	var s2: Node = d2["scene"]
	_to_beat(s2, 64.4)
	assert_eq(_log(s2, "select").size(), 1, "early: one touch")
	assert_eq(s2.engine.node_id, "warehouse.balcony", "held to the end")
	_free(d2)


func test_keys_one_to_eight_pick_the_choices_on_show() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 2.0)
	var shown: Array = scene.hotspots.shown(scene.engine.block, true)
	assert_true(shown.size() >= 4, "four choices on the floor's first beat (%d)" % shown.size())
	var ev := InputEventKey.new()
	ev.pressed = true
	ev.keycode = KEY_4
	scene._unhandled_key_input(ev)
	assert_eq(scene.hotspots.selected, str(shown[3]["id"]), "key 4 in the first block")
	ev.keycode = KEY_8
	scene._unhandled_key_input(ev)
	assert_eq(scene.hotspots.selected, str(shown[3]["id"]) if shown.size() < 8 else str(shown[7]["id"]), "key 8: the eighth, or nothing when there are fewer")
	_free(d)


# --- touch ergonomics -------------------------------------------------------------------------------------------------------------

func test_no_touch_region_meets_a_pad_or_leaves_the_picture_and_the_pause_button_is_never_a_target() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var host: Control = scene._stage_host
	var pads: Dictionary = scene.pad_view.button_rects()
	for beat in [2.0, 20.0, 50.0]:
		_to_beat(scene, beat)
		var lay := _lay(scene, scene.hotspot_items())
		assert_true(lay.size() >= (2 if HotspotView.RINGS else (1 if beat >= 48.0 else 0)), "choices on show at beat %.0f (%s)" % [beat, str(lay.map(func(e: Dictionary) -> String: return str(e["id"])))])  # (package A7: a choice out of the picture has no target any more; mid-scene the rail's drift may hold none of them, the window holds at least one)
		for e in lay:
			var regions: Array = []
			if e.has("touch_rect"):
				regions.append(e["touch_rect"])
			if float(e["radius_px"]) > 0.0:
				var c: Vector2 = e["centre"]
				var rr := float(e["radius_px"])
				regions.append(Rect2(c - Vector2(rr, rr), Vector2(rr, rr) * 2.0))
			for r in regions:
				var g := Rect2((r as Rect2).position + host.global_position, (r as Rect2).size)
				assert_true(Rect2(host.global_position, host.size).grow(0.01).encloses(g), "%s stays in the picture at beat %.0f" % [e["id"], beat])
				for p in pads:
					assert_false(g.intersects(pads[p] as Rect2), "%s never meets pad %s" % [e["id"], str(p)])
				var tr := r as Rect2
				assert_true(minf(tr.size.x, tr.size.y) >= 88.0 - 1e-3, "%s is at least 88 px (%s)" % [e["id"], str(tr.size)])
	var pb: Button = scene._pause_btn
	assert_eq(scene.hotspot_tap(pb.get_global_rect().get_center()), "", "the pause button is never a touch target")
	_free(d)


func _touch(scene: Node, index: int, pos: Vector2, pressed := true) -> void:  # what the viewport does with a touch: the pads (LaneInput) first, the world (RunPlay._input -> hotspot_tap) when the pads leave it
	var ev := InputEventScreenTouch.new()
	ev.index = index
	ev.pressed = pressed
	ev.position = pos
	var before: int = (scene.lane_input as LaneInput)._touch_button.size()
	scene.lane_input._input(ev)
	var taken: bool = (scene.lane_input as LaneInput)._touch_button.size() != before
	if pressed and not taken:
		scene.hotspot_tap(pos)


func test_a_world_tap_selects_while_a_pad_is_held_and_a_pad_tap_never_selects() -> void:  # (INTERACTION_DESIGN.md 7.2; on a phone this needs eyes too, 10.2 item 6)
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 3.0)
	var pads: Dictionary = scene.pad_view.button_rects()
	var p := _tap_point(scene, "warehouse.exit_balcony")
	assert_true(p.x >= 0.0)
	_touch(scene, 0, (pads[1] as Rect2).get_center())
	assert_true(scene.lane_input.is_button_down(1), "the first finger holds pad 1")
	assert_eq(scene.hotspots.selected, "", "a pad touch never selects")
	_touch(scene, 1, p)
	assert_eq(scene.hotspots.selected, "warehouse.exit_balcony", "a second finger on the world selects while the pad is held")
	assert_true(scene.lane_input.is_button_down(1), "and the pad stays held")
	_touch(scene, 2, (pads[3] as Rect2).get_center())
	assert_true(scene.lane_input.is_button_down(3), "a third finger taps pad 3")
	assert_eq(scene.hotspots.selected, "warehouse.exit_balcony", "which leaves the pick alone")
	assert_eq(scene.hotspot_tap((pads[2] as Rect2).get_center()), "", "a point over a pad is never a target")
	_touch(scene, 0, (pads[1] as Rect2).get_center(), false)
	_touch(scene, 2, (pads[3] as Rect2).get_center(), false)
	assert_false(scene.lane_input.is_button_down(1))
	_free(d)


# --- reactive objects in the scene ------------------------------------------------------------------------------------------------

func test_a_reactive_object_reacts_and_never_touches_the_pick_or_the_port() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 2.0)
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var host: Control = scene._stage_host
	var choices := _lay(scene, scene.hotspot_items())
	var chosen := {}
	var point := Vector2(-1, -1)
	for t in st.map.things:  # a thing of the floor in view whose region no choice covers
		var r := HotspotContract.normalize_reactive({"id": "warehouse.r_" + str(t["id"]), "scene": "warehouse", "anchor": {"thing": str(t["id"])}, "reaction": "flare"}, "warehouse", "night_one")
		var lay := _lay(scene, [{"hotspot": r, "state": "idle", "t_state": 0.0}])
		if lay.is_empty() or bool(lay[0]["edge"]) or not lay[0].has("touch_rect"):
			continue
		var c: Vector2 = lay[0]["hit_centre"]
		if HotspotView.hit(choices, c) == "":
			chosen = r
			point = c + host.global_position
			break
	assert_false(chosen.is_empty(), "a thing of the floor can stand in as a reactive object")
	scene.data.reactives["warehouse"] = [chosen]
	var port: TransitionPort = scene.port()
	var before := port.current()
	var log_n: int = (scene.director as TransitionDirector).log.size()
	assert_eq(scene.hotspot_tap(point), "", "a reactive object is no choice")
	assert_eq(_log(scene, "react").size(), 1, "it reacted")
	assert_eq(str(scene.reactive_items()[0]["state"]), "reacting")
	assert_eq(scene.hotspots.selected, "", "nothing selected")
	assert_eq(port.current(), before, "the port's request is untouched")
	assert_eq((scene.director as TransitionDirector).log.size(), log_n, "no port signal")
	assert_true(scene.hotspot_select("warehouse.exit_balcony"))
	scene.hotspot_tap(point)
	assert_eq(_log(scene, "react").size(), 2)
	assert_eq(scene.hotspots.selected, "warehouse.exit_balcony", "a reaction leaves the pick alone")
	assert_false(_ids(scene.hotspot_items()).has(str(chosen["id"])), "never on the choices' list")
	_to_beat(scene, 62.0)
	assert_true(scene.reactive_tap(str(chosen["id"])), "it still reacts in the lock window (it is only a picture)")
	assert_eq(_log(scene, "react").size(), 3)
	_to_beat(scene, 64.4)
	assert_eq(str(_log(scene, "commit")[0]["hotspot"]), "warehouse.exit_balcony", "the commit is the choice's")
	assert_eq(scene.engine.node_id, "warehouse.balcony")
	_free(d)
