class_name SpaceRunDriver
extends RefCounted
## Drives the real run scene (src/run/run_play.tscn) through the Space rave on a stepped clock, as a player would: select a hotspot, wait for the seat, tap the pad strip's controls, wait
## for the hand-back. Used by tests/test_space_rave.gd (the whole rave) and tools/engine/shoot_space_activities.gd (the shots). Needs `Session` (an autoload) and, for pictures, a renderer.

const TMP_SAVE := "user://space_run_driver_save.json"
const STEP := 1.0 / 30.0
const ENV_KEYS := ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_PATH", "RW_RUN_START", "RW_RUN_TAPS", "RW_MINIGAME_TAPS", "RW_RUN_FLAGS", "RW_SPACE_BASS_FIXED"]

var host: Control
var scene: Node
var saved: RunProgress = null
var log: Array = []  # [{t, what, ...}]
var on_step: Callable = Callable()  # (t: float) -> void, after every step


func start(tree: SceneTree, size: Vector2, start_node := "space_rave", bot := "perfect") -> void:
	saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_PATH", "bedsit")
	OS.set_environment("RW_RUN_START", start_node)
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_MINIGAME_TAPS", "")
	Session.run_start_node = ""
	Session.run_start_path = ""
	host = Control.new()
	host.size = size
	tree.root.add_child(host)
	scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size


func finish() -> void:
	if saved != null:
		Session.run_progress = saved
		saved = null
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	if host != null:
		host.queue_free()
		host = null
	for k in ENV_KEYS:
		OS.unset_environment(k)


func t() -> float:
	return float(scene._vt)


func node() -> String:
	return str(scene.engine.node_id)


func mg() -> MinigameController:
	return scene.minigames


func act() -> Variant:
	return scene.minigames.activity if scene.minigames.state == "active" else null


func step() -> void:
	var tt: float = float(scene._vt) + STEP
	scene._vt = tt
	scene._step_virtual(tt)
	if on_step.is_valid():
		on_step.call(tt)


## Steps until `cond` holds (true) or `max_s` song seconds have passed (false).
func until(cond: Callable, max_s := 60.0) -> bool:
	var end := t() + max_s
	while t() < end:
		if cond.call():
			return true
		step()
	return cond.call()


func run_for(seconds: float) -> void:
	var end := t() + seconds
	while t() < end:
		step()


func in_node(id: String, max_s := 60.0) -> bool:
	return until(func() -> bool: return node() == id and not mg().active(), max_s)


## Selects hotspot `id` as soon as selection is open; false when it never opens or the hotspot refuses.
func select(id: String, max_s := 30.0) -> bool:
	if not until(func() -> bool: return scene.selection_open(), max_s):
		return false
	var ok: bool = scene.hotspot_select(id)
	log.append({"t": t(), "what": "select", "id": id, "ok": ok})
	return ok


## The activity seats (state "active") within `max_s`.
func seated(max_s := 60.0) -> bool:
	return until(func() -> bool: return mg().state == "active", max_s)


func pad(i: int) -> Vector2:
	return (scene.pad_view.button_rects()[i] as Rect2).get_center()


## One bot decision for the seated cloakroom: the right control when a coat waits. Returns true when it tapped.
func cloak_bot(wrong_at := -1) -> bool:
	var a: Variant = act()
	if not (a is CloakroomActivity):
		return false
	var s: Dictionary = a.state()
	if str(s["phase"]) != "await":
		return false
	var i: int = (a.answers as Array).size()
	var right: String = (a.expected as Array)[i]
	var want := right
	if i == wrong_at:
		want = "different" if right == "same" else "same"
	scene.dispatch_tap(pad(1) if want == "same" else pad(4))
	return true


## One bot decision for the seated bar: the next ingredient of the recipe in the input phase (pad k + 1 is ingredient k), spaced past the debounce. `mistake_on` is a drink number
## (0 based) whose first press is the wrong ingredient. Returns true when it tapped.
var _last_bar_tap := -10.0
var _mistook := false


func bar_bot(mistake_on := -1) -> bool:
	var a: Variant = act()
	if not (a is BarActivity):
		return false
	var s: Dictionary = a.state()
	if str(s["phase"]) != "input" or t() - _last_bar_tap < 0.45:
		return false
	var rec: Array = s["recipe"]
	var pos := int(s["pos"])
	if pos >= rec.size():
		return false
	var want := int(rec[pos])
	if int(s["served"]) == mistake_on and pos == 0 and not _mistook:
		_mistook = true
		want = (want + 1) % 4
	_last_bar_tap = t()
	scene.dispatch_tap(pad(want + 1))
	return true


## The bass knob's screen point in the window (stage px plus the stage host's offset), or null when it is not drawn.
func knob_point() -> Variant:
	var st: Variant = scene.stages.get(scene.active_world, {}).get("stage", null)
	if st == null:
		return null
	var p: Variant = (st as StoryStage).thing_screen_point("bass_knob")
	return (p as Vector2) + scene._stage_host.global_position if p != null else null
