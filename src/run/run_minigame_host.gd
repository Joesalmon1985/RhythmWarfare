class_name RunMinigameHost
extends RefCounted
## The run scene's side of a minigame (docs/BLACKJACK_INTEGRATION.md section 5.5): mounts the activity's view in the low-res viewport, hit-tests touches against it, plays the scripted taps
## (RW_MINIGAME_TAPS) and puts the journey back on the floor when the activity is done. RunPlay owns one and calls `step` after the controller's `update`.
##
## The view contract (every property is set only if the view has it; `hit` is required for touches to count):
##   now_fn: Callable () -> song time, beat_s: float, screen_size: Vector2 (the stage area's size in SCREEN pixels), reduced: bool, high_contrast: bool,
##   state_fn: Callable () -> Dictionary (the activity's `state()`; {} once it is gone), hit(local_pos: Vector2) -> String (the target id under `local_pos`, the tap position relative to the
##   stage area's top-left in screen pixels; "" for nothing). The view is a full-rect Control on canvas layer 3 inside the stage's low-res viewport, mouse_filter ignore.

var play: Control  # the RunPlay scene
var view: Control = null
var layer: CanvasLayer = null
var scripted: Array = []  # [{target, beats, done}] RW_MINIGAME_TAPS: target@beats after the player sat
var _viewed: MinigameActivity = null
var _was_active := false


func _init(p_play: Control) -> void:
	play = p_play
	var spec := OS.get_environment("RW_MINIGAME_TAPS")
	for part in spec.split(",", false):
		var bits := part.strip_edges().split("@")
		if bits.size() == 2 and bits[0] != "":
			scripted.append({"target": bits[0], "beats": float(bits[1]), "done": false})


## Every frame after `minigames.update(t)`.
func step(t: float) -> void:
	var mg: MinigameController = play.minigames
	play.hud.silent = mg.active()
	if mg.activity != null and mg.activity != _viewed:
		_viewed = mg.activity
		_mount(_viewed)
	if mg.state == "active":
		for s in scripted:
			if not bool(s["done"]) and t >= mg.begin_t + float(s["beats"]) * play.engine.beat_s:
				s["done"] = true
				var ok := mg.tap(str(s["target"]), t)
				play.hotspot_log.append({"kind": "minigame_tap", "t": t, "target": str(s["target"]), "ok": ok, "scripted": true})
	if _was_active and not mg.active():
		_unmount()
		_resume(t)
	_was_active = mg.active()


func _mount(a: MinigameActivity) -> void:
	var v: Control = a.make_view()
	if v == null or not play.stages.has(play.active_world):
		return
	var st: StoryStage = play.stages[play.active_world]["stage"]
	if st.lowres == null:
		return
	var mg: MinigameController = play.minigames
	v.set("now_fn", func() -> float: return play.hud.now_t)
	v.set("beat_s", play.engine.beat_s)
	v.set("reduced", Session.reduced_effects)
	v.set("high_contrast", Session.high_contrast)
	v.set("state_fn", func() -> Dictionary: return mg.activity.state() if mg.activity != null else {})
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer = st.lowres.add_overlay(v, "Minigame")
	layer.layer = 3
	view = v


func _unmount() -> void:
	if layer != null and is_instance_valid(layer):
		layer.queue_free()
	view = null
	layer = null
	_viewed = null


## The target under a touch: `local` is relative to the stage area's top-left in screen pixels, `area` the stage area's screen size. "" when there is no view or nothing is hit.
func hit(local: Vector2, area: Vector2) -> String:
	if view == null or not is_instance_valid(view) or not view.has_method("hit"):
		return ""
	view.set("screen_size", area)
	return str(view.call("hit", local))


## The activity is over: the camera walks back to the scene's home waypoint over two bars and the rail starts again from there.
func _resume(t: float) -> void:
	if play._door_phase == play.engine.phase_n:  # the sit latched this phase's door walk off; getting up inside the same phase hands it back (the walk still starts at beat 61 unless the route is already locked to here)
		play._door_phase = -1
	play._back_to_rail(t)
