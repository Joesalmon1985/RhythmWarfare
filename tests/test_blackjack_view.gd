extends TestCase
## The card table as the player sees it from the chair (package A8b, CONTRACTS.md 10 "Tests", ruling 38): the real run scene in the day room, the table touched and the player
## seated, shot (as projected rects, headless) at three moments, a hand dealt, a bust, a payout, at 16:9 (1280 x 720) and 20:9 (1600 x 720). Every thing of the table is on
## the stage strip (inside it, never over the pads), every card at least 48 px tall and every chip stack at least 32 px, measured with StoryStage.thing_screen_rect; the
## camera holds at the chair tipped down to the felt; nothing is mounted on a canvas layer but the feedback marks.

const BEAT := 60.0 / 174.0
const STEP := 1.0 / 30.0
const TMP_SAVE := "user://test_blackjack_view_save.json"
const SIZES := [Vector2(1280, 720), Vector2(1600, 720)]
const CARD_MIN_PX := 48.0
const STACK_MIN_PX := 32.0

var _saved: RunProgress


func _scene(size: Vector2, seed: int) -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_RUN_START", "ward")
	OS.set_environment("RW_MINIGAME_TAPS", "")
	OS.set_environment("RW_MINIGAME_SEED", str(seed))
	Session.run_start_node = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS", "RW_MINIGAME_SEED"]:
		OS.set_environment(k, "")
	OS.unset_environment("RW_RUN_START")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += STEP
		scene._vt = t
		scene._step_virtual(t)


## Plays the table from the seat: the first hand twists until it busts, later hands stick from 13 up, until `want` (a feedback kind: "cross" or "glow") is asked for.
## Returns the song time of that mark (-1 when it never came within `limit_beats`).
func _play_until(scene: Node, want: String, limit_beats := 400.0) -> float:
	var mg: MinigameController = scene.minigames
	var a: BlackjackActivity = mg.activity
	var end: float = float(scene._vt) + limit_beats * BEAT
	var n0 := a.feedback_log.size()
	while float(scene._vt) < end:
		_run_to(scene, float(scene._vt) + STEP)
		var t: float = scene._vt
		var s := a.state()
		match str(s["phase"]):
			"await_bet":
				mg.tap("bet", t)
			"player_turn":
				var tot := int(s["seats"]["player"]["total"])
				if "deck" in (s["targets"] as Array):
					mg.tap("deck" if want == "cross" or tot < 13 else "hand", t)
		for f: Dictionary in a.feedback_log.slice(n0):
			if str(f["kind"]) == want:
				return float(f["t"])
	return -1.0


## Every table thing on the active stage now: inside the stage strip, the cards and stacks tall enough. Returns the problems.
func _check(scene: Node, label: String) -> Array:
	var bad: Array = []
	var st: StoryStage = scene._mg.active_stage()
	var strip := Rect2(Vector2.ZERO, scene._stage_host.size)
	var things: Array = st.world.dynamic.things
	if things.is_empty():
		bad.append("%s: no things on the stage" % label)
	var cards := 0
	for x: Dictionary in things:
		var id := str(x["id"])
		var r: Variant = st.thing_screen_rect(id)
		if r == null:
			bad.append("%s: %s is not drawn" % [label, id])
			continue
		var rr: Rect2 = r
		if not strip.encloses(rr):
			bad.append("%s: %s %s is not inside the strip %s" % [label, id, str(rr), str(strip)])
		if id.begins_with("bj_card_") or id == "bj_deck":
			cards += 1
			if rr.size.y < CARD_MIN_PX:
				bad.append("%s: card %s is %.1f px tall" % [label, id, rr.size.y])
		elif id.begins_with("bj_chips_") or id == "bj_bet":
			if rr.size.y < STACK_MIN_PX:
				bad.append("%s: stack %s is %.1f px tall" % [label, id, rr.size.y])
	if cards < 2:
		bad.append("%s: only %d cards" % [label, cards])
	print("  %s: %s" % [label, ", ".join(PackedStringArray(things.map(func(x: Dictionary) -> String:
		var rr: Variant = st.thing_screen_rect(str(x["id"]))
		return "%s %s" % [str(x["id"]).trim_prefix("bj_"), ("%dx%d@%d,%d" % [int(rr.size.x), int(rr.size.y), int(rr.position.x), int(rr.position.y)]) if rr != null else "-"])))])
	return bad


func _seat(scene: Node) -> void:
	_run_to(scene, scene.engine.t_of(6.0))
	assert_true(scene.hotspot_select("ward.cards"), "the table touched in block 0")
	_run_to(scene, scene.engine.t_of(16.0) + 5.0 * BEAT)
	assert_eq(scene.minigames.state, "active", "seated at beat 16")


func test_from_the_chair_every_card_and_stack_reads_inside_the_strip_at_a_deal_a_bust_and_a_payout_at_16_9_and_20_9() -> void:
	for size: Vector2 in SIZES:
		var d := _scene(size, 7)
		var scene: Node = d["scene"]
		_seat(scene)
		var host: RunMinigameHost = scene._mg
		assert_true(host.view == null and host.layer == null, "%s: no canvas view mounted" % str(size))
		var label := "%dx%d" % [int(size.x), int(size.y)]
		# the hold: at the chair, tipped down
		var cam: Vector3 = scene._exit_pose()["cam"]
		var chair: Vector2 = (scene.stages[scene.active_world]["stage"] as StoryStage).map.waypoint("day_cards")["at"]
		assert_true(Vector2(cam.x, cam.z).distance_to(chair) < 0.3, "%s: the camera holds at the chair" % label)
		# 1: a hand dealt
		var mg: MinigameController = scene.minigames
		mg.tap("bet", scene._vt)
		_run_to(scene, float(scene._vt) + 5.0 * BEAT)
		var pose: Dictionary = (scene.stages[scene.active_world]["stage"] as StoryStage).player.pose_at(scene._vt)
		assert_true(float(pose.get("pitch", 0.0)) < -8.0, "%s: tipped down to the felt (pitch %.1f)" % [label, float(pose.get("pitch", 0.0))])
		assert_eq(_check(scene, label + " deal"), [], "%s: a dealt hand" % label)
		# 2: a bust
		var tb := _play_until(scene, "cross")
		assert_true(tb > 0.0, "%s: a bust came" % label)
		_run_to(scene, tb + 0.3 * BEAT)
		assert_eq(_check(scene, label + " bust"), [], "%s: the bust" % label)
		assert_true(host.feedback_layer != null and host.feedback_layer.entries.any(func(e: Dictionary) -> bool: return str(e["kind"]) == "cross"), "%s: the cross is drawn by the host" % label)
		# 3: a payout
		var tp := _play_until(scene, "glow")
		assert_true(tp > 0.0, "%s: a payout came" % label)
		_run_to(scene, tp + 0.3 * BEAT)
		assert_eq(_check(scene, label + " payout"), [], "%s: the payout" % label)
		assert_true(host.feedback_layer.entries.any(func(e: Dictionary) -> bool: return str(e["kind"]) == "glow" and str(e["thing"]) == "bj_chips_player"), "%s: the glow on the stack" % label)
		assert_true(scene.hud.silent, "%s: the HUD draws no text" % label)
		_free(d)
