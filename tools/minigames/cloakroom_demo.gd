extends Control
## The cloakroom without a rave map (the test scene fixture, and the host scene of the shots): the REAL CloakroomActivity on its own song clock at 174 BPM, its CloakroomView in a
## SubViewport the shape of the run's stage area (the top 64 % of the window), and under it the pad strip as the host's controls layer would draw it (SAME on the left,
## DIFFERENT on the right, with the pictograms; RunActivityInput draws labels only today, so this stands in for the hook). Every frame advances the song time by RW_DEMO_STEP.
## Env:
##   RW_DEMO_THEME=space|magic|dinos|transport   (default space)
##   RW_MINIGAME_SEED=<n>                        (default 7)
##   RW_DEMO_PLAN="RRWRRRRR"                     the player's answers, one letter per coat: R right, W wrong (default all right)
##   RW_DEMO_THINK=<seconds>                     how long after a coat appears the player answers (default 0.6)
##   RW_DEMO_STEP=<seconds>                      song seconds per rendered frame (default 0.05)
##   RW_DEMO_COATS=<n>                           the workload (default the config's)
##   RW_DEMO_REDUCED=1, RW_DEMO_HC=1             reduced motion, high contrast

const BEAT := 60.0 / 174.0
const STAGE_FRAC := 0.64

class Strip:
	extends Control
	var host: Node

	func _draw() -> void:
		host.call("draw_strip", self)

var _sub: SubViewport
var _view: CloakroomView
var _activity: CloakroomActivity
var _strip: Strip
var _rect: TextureRect
var _t := 0.0
var _step := 0.05
var _plan := ""
var _think := 0.6
var _pressed := {"id": "", "t": -10.0}


func _ready() -> void:
	CloakroomSession.reset()
	if OS.has_environment("RW_DEMO_STEP"):
		_step = float(OS.get_environment("RW_DEMO_STEP"))
	_plan = OS.get_environment("RW_DEMO_PLAN")
	if OS.has_environment("RW_DEMO_THINK"):
		_think = float(OS.get_environment("RW_DEMO_THINK"))
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/cloakroom.json"))
	if OS.has_environment("RW_DEMO_COATS"):
		cfg["coats"] = int(OS.get_environment("RW_DEMO_COATS"))
	var theme := OS.get_environment("RW_DEMO_THEME") if OS.has_environment("RW_DEMO_THEME") else "space"
	_activity = CloakroomActivity.new()
	_activity.setup({"seed": int(OS.get_environment("RW_MINIGAME_SEED")) if OS.has_environment("RW_MINIGAME_SEED") else 7, "beat_s": BEAT, "config": cfg, "request": {"theme": theme}})
	_activity.begin(0.0)
	_sub = SubViewport.new()
	_sub.transparent_bg = false
	_sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_sub)
	_rect = TextureRect.new()
	_rect.texture = _sub.get_texture()
	_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_rect.stretch_mode = TextureRect.STRETCH_SCALE
	_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_rect)
	_view = _activity.make_view() as CloakroomView
	_view.now_fn = func() -> float: return _t
	_view.state_fn = func() -> Dictionary: return _activity.state()
	_view.beat_s = BEAT
	_view.reduced = OS.get_environment("RW_DEMO_REDUCED") == "1"
	_view.high_contrast = OS.get_environment("RW_DEMO_HC") == "1"
	_sub.add_child(_view)
	_strip = Strip.new()
	_strip.host = self
	add_child(_strip)
	resized.connect(_layout)
	_layout()


func _layout() -> void:
	var stage := Vector2(size.x, size.y * STAGE_FRAC)
	_rect.position = Vector2.ZERO
	_rect.size = stage
	var h := 230
	_sub.size = Vector2i(int(round(float(h) * stage.x / stage.y)), h)
	_view.size = Vector2(_sub.size)
	_view.screen_size = stage
	_strip.position = Vector2(0, stage.y)
	_strip.size = Vector2(size.x, size.y - stage.y)


func _process(_delta: float) -> void:
	_advance(_t + _step)
	_strip.queue_redraw()


func _advance(t: float) -> void:
	_t = t
	_activity.update(_t)
	var s := _activity.state()
	var i := int(s["answered"])
	if str(s["phase"]) == "await" and _t - float(s["phase_t0"]) >= _think and i < _plan.length() + (0 if _plan != "" else 99):
		var right := str(_activity.expected[i])
		var wrong := "different" if right == "same" else "same"
		var pick := wrong if (_plan.length() > i and _plan[i] == "W") else right
		_pressed = {"id": pick, "t": _t}
		_activity.tap(pick, _t)


## The controls layer as the host would draw it: two large buttons where the pads were, a pictogram each, no words.
func draw_strip(ci: Control) -> void:
	var r := Rect2(Vector2.ZERO, ci.size)
	ci.draw_rect(r, Color(0.06, 0.06, 0.09))
	var half := (r.size.x - 24.0) * 0.5
	for k in 2:
		var id := "same" if k == 0 else "different"
		var b := Rect2(Vector2(8.0 + float(k) * (half + 8.0), 8.0), Vector2(half, r.size.y - 16.0))
		var hot := str(_pressed["id"]) == id and _t - float(_pressed["t"]) < 0.15
		ci.draw_rect(b, Color(0.35, 0.35, 0.5, 0.95) if hot else Color(0.10, 0.10, 0.14, 0.92))
		ci.draw_rect(b, Color(0.85, 0.85, 0.95, 0.9), false, 3.0)
		CloakroomArt.draw_pictogram(ci, b.grow(-10.0), id)
