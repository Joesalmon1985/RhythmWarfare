extends TestCase
## The silent HUD (docs/THREE_PATHS_AND_FACES_PLAN.md D3, 2.4): with RW_DEV_TEXT unset the run draws no title card, no captions, no world or room names, no labels and no numeric countdown while it plays
## (the HUD's `_outlined`, the only way it writes, is never called over a scripted two-phase run, from the count-in to the second scene); the stage pips, the energy meter and the thin route-window
## bar stay; RW_DEV_TEXT=1 brings every word back. The new room's light swell and the Bassment's silent caption band are tested here too.

var _saved: RunProgress
const TMP_SAVE := "user://test_run_hud_silent_save.json"


func _scene(size: Vector2, dev_text: bool) -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_DEV_TEXT", "1" if dev_text else "")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	(d["host"] as Control).queue_free()
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	OS.set_environment("RW_DEV_TEXT", "")
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


## Steps the scene's virtual clock to song time `t_end`, letting the HUD draw every few steps (a draw needs a frame).
func _run_to(scene: Node, t_end: float, captured: Array = []) -> void:
	var t: float = scene._vt
	var n := 0
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
		n += 1
		if n % 12 == 0:
			(scene.hud as Control).queue_redraw()
			await tree.process_frame
			captured.append(scene.hud.captions.size() + scene.hud.title_card.size())


func test_without_the_dev_switch_the_hud_writes_nothing_over_two_scenes() -> void:
	var d := _scene(Vector2(844, 390), false)
	var scene: Node = d["scene"]
	var hud: RunHud = scene.hud
	var seen: Array = []
	await _run_to(scene, 64.0 * 60.0 / 174.0 + 12.0 * 60.0 / 174.0, seen)  # from the count-in (-2 s) through the first scene's whole phase into the second scene
	assert_true(scene.engine.phase_n >= 2, "the scripted run is two scenes long (phase %d)" % scene.engine.phase_n)
	assert_true(hud.frames_drawn > 40, "the HUD really drew (%d frames)" % hud.frames_drawn)
	assert_eq(hud.strings_drawn, 0, "not one draw_string: no title card, captions, names, labels or countdown")
	assert_true(hud.captions.is_empty() and hud.title_card.is_empty(), "nothing was even queued")
	assert_eq(scene.pad_view.banner_text, "", "and the pads' own banner (DRUMS / BASS) is off too")
	assert_true(scene.hud.countdown == "", "the count-in had run out")
	# the dev switch is not sticky: it is read when the text is asked for
	_free(d)


func test_with_the_dev_switch_all_the_old_text_comes_back() -> void:
	var d := _scene(Vector2(844, 390), true)
	var scene: Node = d["scene"]
	var hud: RunHud = scene.hud
	var seen: Array = []
	await _run_to(scene, 64.0 * 60.0 / 174.0 + 5.0 * 60.0 / 174.0, seen)
	assert_true(hud.strings_drawn > 50, "the title card, captions, labels and countdown are drawn (%d strings)" % hud.strings_drawn)
	assert_true(seen.max() > 0, "captions and the title card were on show at some frame")
	_free(d)


func test_the_route_window_is_a_thin_bar_that_empties_over_the_sixteen_beats() -> void:
	var d := _scene(Vector2(844, 390), false)
	var scene: Node = d["scene"]
	var hud: RunHud = scene.hud
	var bs: float = scene.engine.beat_s
	assert_eq(hud.window_left(1.0), -1.0, "no window before the choice")
	await _run_to(scene, 47.0 * bs)
	assert_true(scene.engine.window_open, "the choice window is open from the third block's decision")
	assert_near(hud.window_left(48.0 * bs), 1.0, 1.0e-6, "full at beat 48")
	assert_near(hud.window_left(56.0 * bs), 0.5, 1.0e-6, "half at beat 56")
	assert_near(hud.window_left(64.0 * bs), 0.0, 1.0e-6, "empty on the downbeat")
	assert_true(hud.window_left(52.0 * bs) > hud.window_left(60.0 * bs), "it only empties")
	_free(d)


func test_a_new_room_swells_its_light_over_two_beats_from_the_downbeat() -> void:
	var d := _scene(Vector2(844, 390), false)
	var scene: Node = d["scene"]
	var bs: float = scene.engine.beat_s
	await _run_to(scene, 64.0 * bs + 0.1)
	assert_true(scene.engine.phase_n >= 2)
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var t0: float = scene.engine.phase_t0
	var kinds: Array = st.action_log.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "room_swell").map(func(a: Dictionary) -> float: return float(a["t0"]))
	assert_true(kinds.has(t0), "the second scene began with a room swell on its downbeat")
	assert_near(st.swell_gain(t0), StoryStage.SWELL_FROM, 1.0e-6, "the lamps start low")
	assert_true(st.swell_gain(t0 + 1.0 * bs) > st.swell_gain(t0), "and rise")
	assert_near(st.swell_gain(t0 + 2.0 * bs + 0.01), 1.0, 1.0e-6, "to the full light in two beats")
	assert_eq(st.swell_gain(t0 - 5.0), 1.0, "nothing before the downbeat")
	var first_swell := st.action_log.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "room_swell" and float(a["t0"]) < 1.0)
	assert_eq(first_swell.size(), 0, "the very first scene has no swell (the doors open instead)")
	var lit := StoryWorld.light_of({"light": 0.6, "tint": Color(1, 0.8, 0.6), "flags": []}, 5.0, {"bpm": 174.0, "energy": 50.0, "swell_gain": 0.5})
	var plain := StoryWorld.light_of({"light": 0.6, "tint": Color(1, 0.8, 0.6), "flags": []}, 5.0, {"bpm": 174.0, "energy": 50.0})
	assert_true(lit.r < plain.r, "a swell below 1 dims the sector's light")
	_free(d)
