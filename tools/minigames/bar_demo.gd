extends Control
## The bar without the whole game (the test scene fixture of the bar, also the shot rig): the REAL BarActivity and BarView in a low-res SubViewport shown nearest-neighbour over the stage area, and the
## activity's four controls in a strip below where the pads were (the real RunActivityInput; the pictograms on them are this demo's stand-in for host hook H-bar-1, see docs/briefs/BAR_HOOKS.md).
## A scripted player drives it on a virtual song clock, then the clock freezes at the moment asked for, so a screenshot at any frame is the same picture.
## Env:
##   RW_BAR_THEME=space|magic|dinos|transport  (default space)
##   RW_BAR_SCENE=demo | input | mistake | handover | complete     (default demo)
##       demo      the first drink, the second ingredient lit in the bubble
##       input     the first drink, one ingredient already in the glass, the bubble hidden
##       mistake   the first drink served, the second (three ingredients) gets two right and a wrong one, shown 1.0 s later
##       handover  the first drink served, the glass half way to the customer
##       complete  four drinks served, the payoff
##   RW_BAR_SEED=<n> (default 7)   RW_BAR_REDUCED=1   RW_BAR_HC=1

const BEAT := 60.0 / 174.0
const STRIP_FRACTION := 0.27

var _a: BarActivity
var _view: BarView
var _t := 0.0
var _sub: SubViewport
var _strip: RunActivityInput
var _icons: Control


class Icons:
	extends Control
	var specs: Array = []
	var rects_fn: Callable

	func _draw() -> void:
		var rs: Array = rects_fn.call()
		for i in mini(rs.size(), specs.size()):
			var r: Rect2 = rs[i]
			var sz := minf(r.size.x, r.size.y) * 0.7
			var tex := BarDraw.texture(str(specs[i]["shape"]), Color(str(specs[i]["color"])))
			draw_texture_rect(tex, Rect2(r.get_center() - Vector2(sz, sz) * 0.5, Vector2(sz, sz)), false)


func _ready() -> void:
	BarActivity.forget_all()
	var theme := OS.get_environment("RW_BAR_THEME") if OS.get_environment("RW_BAR_THEME") != "" else "space"
	var scene := OS.get_environment("RW_BAR_SCENE") if OS.get_environment("RW_BAR_SCENE") != "" else "demo"
	var seed_n := int(OS.get_environment("RW_BAR_SEED")) if OS.get_environment("RW_BAR_SEED") != "" else 7
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/bar.json"))
	_a = BarActivity.new()
	_a.setup({"seed": seed_n, "beat_s": BEAT, "config": cfg, "request": {"theme": theme}})
	_a.begin(0.0)
	_simulate(scene)
	var stage_h := size.y * (1.0 - STRIP_FRACTION)
	var low := Vector2i(640, maxi(int(640.0 * stage_h / size.x), 120))
	_sub = SubViewport.new()
	_sub.size = low
	_sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_sub)
	var rect := TextureRect.new()
	rect.texture = _sub.get_texture()
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.position = Vector2.ZERO
	rect.size = Vector2(size.x, stage_h)
	add_child(rect)
	_view = _a.make_view() as BarView
	_view.now_fn = func() -> float: return _t
	_view.state_fn = func() -> Dictionary: return _a.state()
	_view.beat_s = BEAT
	_view.reduced = OS.get_environment("RW_BAR_REDUCED") == "1"
	_view.high_contrast = OS.get_environment("RW_BAR_HC") == "1"
	_view.screen_size = Vector2(size.x, stage_h)
	_view.size = Vector2(low)
	_sub.add_child(_view)
	# the strip: four controls in the pads' places
	var strip_y := stage_h
	var strip_h := size.y - stage_h
	var rects_fn := func() -> Array:
		var out: Array = []
		var w := size.x / 4.0
		for i in 4:
			out.append(Rect2(w * float(i), strip_y, w, strip_h).grow_individual(-4, -6, -4, -8))
		return out
	_strip = RunActivityInput.new()
	_strip.kind = "controls"
	for c: Dictionary in _a.controls():
		_strip.ids.append(str(c["id"]))
		_strip.labels.append(str(c["label"]))
	_strip.rects_fn = rects_fn
	add_child(_strip)
	_icons = Icons.new()
	(_icons as Icons).specs = _a.controls()
	(_icons as Icons).rects_fn = rects_fn
	_icons.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_icons.set_anchors_preset(Control.PRESET_FULL_RECT)
	_icons.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_icons)


func _process(_delta: float) -> void:
	_view.screen_size = Vector2(size.x, size.y * (1.0 - STRIP_FRACTION))
	_icons.queue_redraw()


## Drives the activity with a scripted player to the moment of `scene`; leaves `_t` there.
func _simulate(scene: String) -> void:
	var t := 0.0
	var dt := 1.0 / 60.0
	var plan: Array = []  # [{t, id}]
	var planned_for := -1
	var served_goal := 0
	match scene:
		"mistake", "handover":
			served_goal = 1
		"complete":
			served_goal = 4
	var stop_t := -1.0
	for _i in 60 * 120:
		_a.update(t)
		var s := _a.state()
		var ph := str(s["phase"])
		var sig := int(s["served"]) * 100 + int(s["attempt"])
		if ph == "input" and planned_for != sig:
			planned_for = sig
			plan.clear()
			var recipe: Array = s["recipe"]
			var at := float(s["phase_t0"]) + 0.6
			var wrong_now := scene == "mistake" and int(s["served"]) == 1
			for k in recipe.size():
				var want := int(recipe[k])
				if wrong_now and k == recipe.size() - 1:
					want = (want + 1) % 4
				plan.append({"t": at, "id": "ing:%d" % want})
				at += 0.55
		while not plan.is_empty() and t >= float(plan[0]["t"]) and ph == "input":
			_a.tap(str(plan[0]["id"]), t)
			plan.remove_at(0)
			s = _a.state()
			ph = str(s["phase"])
		# the moment
		var p := t - float(s["phase_t0"])
		match scene:
			"demo":
				if ph == "demo" and p >= 0.8 + 0.35:
					stop_t = t
			"input":
				if ph == "input" and int(s["pos"]) >= 1:
					stop_t = t + 0.3
			"mistake":
				if int(s["served"]) == 1 and ph == "serve" and str(s["outcome"]) == "mistake" and p >= 1.0:
					stop_t = t
			"handover":
				if int(s["served"]) == served_goal and ph == "serve" and str(s["outcome"]) == "happy" and p >= 0.5:
					stop_t = t
			"complete":
				if ph == "payoff" and p >= 1.2:
					stop_t = t
		if stop_t >= 0.0:
			break
		t += dt
	_t = t if stop_t < 0.0 else stop_t
	_a.update(_t)
