extends Node
## The card table's shots (package A8b, ruling 38): the real run scene in the ward's day room on the virtual clock, at the window's size: the walk-up (the table touched,
## the camera on its way to the chair), the hold with a dealt hand, a bust (the cross on the card that went over), a payout (the glow on the player's stack), each with the
## pad strip showing the table's controls in the pads' slots. Needs a renderer (not --headless); one size per run (the window's):
##   bash tools/minigames/shoot_cardtable.sh   (both sizes and the contact sheet docs/shots/bedsit/cardtable/contact.jpg)
## Writes <RW_SHOT_DIR>/<w>x<h>_<moment>.png and prints every table thing's stage rect at each moment.

const BEAT := 60.0 / 174.0
const STEP := 1.0 / 60.0
const SEED := 7

var _scene: Control
var _out := ""
var _label := ""


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	_out = OS.get_environment("RW_SHOT_DIR") if OS.get_environment("RW_SHOT_DIR") != "" else OS.get_user_data_dir().path_join("cardtable_shots")
	DirAccess.make_dir_recursive_absolute(_out)
	var sz := get_tree().root.size
	_label = "%dx%d" % [sz.x, sz.y]
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_RUN_START", "ward")
	OS.set_environment("RW_MINIGAME_TAPS", "")
	OS.set_environment("RW_MINIGAME_SEED", str(SEED))
	Session.run_start_node = ""
	Session.run_progress = RunProgress.load_data("user://cardtable_shots_save.json", "user://none.json")
	_scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	get_tree().root.add_child(_scene)
	_scene.set_anchors_preset(Control.PRESET_FULL_RECT)
	await get_tree().process_frame
	_scene.set_process(false)  # (this node drives the virtual clock)
	await _to(_scene.engine.t_of(6.0))
	_scene.hotspot_select("ward.cards")
	await _to(float(_scene._vt) + 2.5 * BEAT)
	await _shot("1_walkup")
	await _to(_scene.engine.t_of(16.0) + 5.0 * BEAT)
	var mg: MinigameController = _scene.minigames
	mg.tap("bet", _scene._vt)
	await _to(float(_scene._vt) + 5.5 * BEAT)
	await _shot("2_hold_dealt")
	var tb := await _play_until("cross")
	await _to(tb + 0.25 * BEAT)
	await _shot("3_bust")
	var tp := await _play_until("glow")
	await _to(tp + 0.35 * BEAT)
	await _shot("4_payout")
	get_tree().quit(0)


func _to(t_end: float) -> void:
	var t: float = _scene._vt
	var n := 0
	while t < t_end:
		t = minf(t + STEP, t_end)
		_scene._vt = t
		_scene._step_virtual(t)
		n += 1
		if n % 8 == 0:
			await get_tree().process_frame


func _play_until(want: String) -> float:
	var mg: MinigameController = _scene.minigames
	var a: BlackjackActivity = mg.activity
	var n0 := a.feedback_log.size()
	var end: float = float(_scene._vt) + 400.0 * BEAT
	while float(_scene._vt) < end:
		await _to(float(_scene._vt) + 2.0 * STEP)
		var t: float = _scene._vt
		var s := a.state()
		match str(s["phase"]):
			"await_bet":
				mg.tap("bet", t)
			"player_turn":
				if "deck" in (s["targets"] as Array):
					mg.tap("deck" if want == "cross" or int(s["seats"]["player"]["total"]) < 13 else "hand", t)
		for f: Dictionary in a.feedback_log.slice(n0):
			if str(f["kind"]) == want:
				return float(f["t"])
	return float(_scene._vt)


func _shot(name: String) -> void:
	for i in 3:
		_scene._step_virtual(_scene._vt)
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	var path := _out.path_join("%s_%s.png" % [_label, name])
	img.save_png(path)
	var st: StoryStage = _scene._mg.active_stage()
	var parts: Array = []
	if st != null and st.world != null:
		for x: Dictionary in st.world.dynamic.things:
			var r: Variant = st.thing_screen_rect(str(x["id"]))
			parts.append("%s %s" % [str(x["id"]), str(r)])
	print("shot %s  pitch %.1f  %s" % [path, float(st.player.pose_at(_scene._vt).get("pitch", 0.0)) if st != null else 0.0, "; ".join(PackedStringArray(parts))])
