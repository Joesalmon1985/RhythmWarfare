extends Control
## A DATA PREVIEW of the bar (dev tool, the test scene fixture and the shot rig): the REAL BarActivity runs on a virtual song clock with a scripted player, and what it tells the world through its
## WorldThings port (things(), people(), feedback(), pieces) is drawn here as a flat elevation of tests/fixtures/bar_scene/bar_room.json seen from its bar_view waypoint with a simple pinhole.
## This is NOT the stage: the game draws these things with StoryWorld (engine package A8). People are marked by a block and their state name (this tool may print text; the bar's own code never does).
## The four controls stand in a strip below where the pads were (the real RunActivityInput; the pictograms on them stand in for host hook H-bar-1, see docs/briefs/BAR_HOOKS.md).
## Env: RW_BAR_THEME=space|magic|dinos|transport (default space), RW_BAR_SCENE=demo | input | mistake | handover | complete (default demo), RW_BAR_SEED=<n> (default 7)
##   demo the first drink, the second ingredient lit in the bubble; input one ingredient in the glass; mistake the first drink served, the second gets two right and a wrong one;
##   handover the glass half way to the customer; complete four drinks served, the payoff.

const BEAT := 60.0 / 174.0
const STRIP_FRACTION := 0.27
const CAM := Vector3(0.0, 1.6, 0.5)
const STATE_COLORS := {"waiting": Color(0.7, 0.7, 0.8), "happy": Color(0.4, 0.9, 0.5), "frown": Color(0.9, 0.35, 0.35), "clap": Color(0.4, 0.9, 0.5), "hands_up": Color(1.0, 0.85, 0.3),
	"raise_glass": Color(1.0, 0.85, 0.3), "idle": Color(0.7, 0.7, 0.8)}

var _a: BarActivity
var _w: WorldThings
var _t := 0.0
var _theme := "space"
var _preview: Control
var _strip: RunActivityInput
var _icons: Control
var _sheets: Dictionary = {}


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


class Preview:
	extends Control
	var demo: Node

	func _draw() -> void:
		demo.call("_paint", self)


func _ready() -> void:
	BarActivity.forget_all()
	_theme = OS.get_environment("RW_BAR_THEME") if OS.get_environment("RW_BAR_THEME") != "" else "space"
	var scene := OS.get_environment("RW_BAR_SCENE") if OS.get_environment("RW_BAR_SCENE") != "" else "demo"
	var seed_n := int(OS.get_environment("RW_BAR_SEED")) if OS.get_environment("RW_BAR_SEED") != "" else 7
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/bar.json"))
	_w = WorldThings.new()
	_a = BarActivity.new()
	_a.setup({"seed": seed_n, "beat_s": BEAT, "config": cfg, "request": {"theme": _theme}, "world": _w})
	_a.begin(0.0)
	_simulate(scene)
	_preview = Preview.new()
	(_preview as Preview).demo = self
	_preview.size = Vector2(size.x, size.y * (1.0 - STRIP_FRACTION))
	_preview.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_preview)
	var strip_y := size.y * (1.0 - STRIP_FRACTION)
	var strip_h := size.y - strip_y
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
	_icons.queue_redraw()
	_preview.queue_redraw()


func _sheet(sprite: String) -> ImageTexture:
	if not _sheets.has(sprite):
		_sheets[sprite] = ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/bar_test/sprites/%s.png" % sprite)))
	return _sheets[sprite]


func _paint(c: Control) -> void:
	var sz := c.size
	var f := sz.y * 0.8
	var o := Vector2(sz.x * 0.5, sz.y * 0.5)
	var proj := func(x: float, y: float, z: float) -> Vector2: return o + Vector2((x - CAM.x) / (z - CAM.z) * f, -(y - CAM.y) / (z - CAM.z) * f)
	var scl := func(m: float, z: float) -> float: return m / (z - CAM.z) * f
	var floor_y: float = (proj.call(0.0, 0.0, 4.0) as Vector2).y
	c.draw_rect(Rect2(0, 0, sz.x, floor_y), Color("4a3040"), true)
	c.draw_rect(Rect2(0, floor_y, sz.x, sz.y - floor_y), Color("3a2a22"), true)
	var lit := {}
	var pulsed := {}
	for e: Dictionary in _w.piece_log:
		if e["op"] == "on":
			lit[str(e["piece"])] = true
		elif e["op"] == "pulse":
			lit[str(e["piece"])] = true
			pulsed[str(e["piece"])] = true
	var sh0: Vector2 = proj.call(-2.0, 1.55, 3.85)
	c.draw_rect(Rect2(sh0, Vector2(scl.call(4.0, 3.85), scl.call(0.12, 3.85))), Color("6a4a2a"), true)
	for i in 4:
		var gp: Vector2 = proj.call(-1.5 + float(i), 1.85, 3.8)
		var gs: float = scl.call(0.45, 3.8)
		var on := lit.has("bar_shelf_%d" % i)
		if on and pulsed.has("bar_shelf_%d" % i):
			c.draw_circle(gp, gs * 0.9, Color(1.0, 0.9, 0.5, 0.35))
		var r := Rect2(gp - Vector2(gs * 0.35, gs * 0.5), Vector2(gs * 0.7, gs))
		c.draw_rect(r, Color(1.0, 0.85, 0.35) if on else Color(0.45, 0.5, 0.6), true)
		c.draw_rect(r, Color(0.9, 0.95, 1.0), false, 2.0)
	_person(c, proj, scl, "bartender", Vector3(0.6, 0.0, 2.9), Color("e8b98a"))
	var glow := false
	for e: Dictionary in _w.feedback_log:
		if str(e["thing"]) == "bar_counter" and _t - float(e["t"]) < 0.8:
			glow = true
	var ctl: Vector2 = proj.call(-3.0, 1.1, 2.3)
	var cw: float = scl.call(6.0, 2.3)
	c.draw_rect(Rect2(ctl, Vector2(cw, sz.y - ctl.y)), Color("a07a4a") if glow else Color("7a5232"), true)
	c.draw_rect(Rect2(ctl, Vector2(cw, scl.call(0.08, 2.3))), Color("a8885a"), true)
	_person(c, proj, scl, "customer", Vector3(-1.2, 0.0, 1.4), Color("6fcf7f"))
	for t: Dictionary in _a.things():
		var at: Array = t["at"]
		var z := float(at[1])
		var sm: Array = t["size"]
		var ctr: Vector2 = proj.call(float(at[0]), float(t["y"]), z)
		var wpx: float = scl.call(float(sm[0]), z)
		var hpx: float = scl.call(float(sm[1]), z)
		var tex := _sheet(str(t["sprite"]))
		var fr := int(t["frame"])
		var fw := tex.get_width() / (6 if str(t["sprite"]).begins_with("bar_glass") else 4)
		var dst := Rect2(ctr - Vector2(wpx, hpx) * 0.5, Vector2(wpx, hpx))
		c.draw_texture_rect_region(tex, dst, Rect2(fw * fr, 0, fw, tex.get_height()))
		if t.has("layers") and fr >= 1 and fr <= 3:  # the stage tints a layer to the order's colour; the sheet holds the theme's first three
			var cols: Array = t["layers"]
			for k in cols.size():
				var y0 := 96.0 - 6.0 - 4.0 - 22.0 * float(k + 1)
				c.draw_rect(Rect2(dst.position + Vector2(dst.size.x * 12.0 / 64.0, dst.size.y * y0 / 96.0), Vector2(dst.size.x * 40.0 / 64.0, dst.size.y * 22.0 / 96.0)), Color(str(cols[k])), true)
	for e: Dictionary in _w.feedback_log:
		if str(e["thing"]) == "bar_glass" and _t - float(e["t"]) < 0.4:
			c.draw_circle(proj.call(0.0, 2.0, 2.0), 14.0, Color(0.3, 0.9, 0.4) if str(e["kind"]) == "tick" else Color(0.95, 0.25, 0.25))
	c.draw_string(ThemeDB.fallback_font, Vector2(8, 18), "DATA PREVIEW of things(), people() and pieces on bar_room.json, not the stage (%s)" % _theme, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1, 1, 1, 0.6))


func _person(c: Control, proj: Callable, scl: Callable, who: String, at: Vector3, body: Color) -> void:
	var st := _w.state_of(who)
	var top: Vector2 = proj.call(at.x, 1.7, at.z)
	var w: float = scl.call(0.5, at.z)
	var h: float = scl.call(1.7, at.z)
	var r := Rect2(top - Vector2(w * 0.5, 0), Vector2(w, h))
	var edge: Color = STATE_COLORS.get(st, Color.WHITE)
	c.draw_rect(r, body, true)
	c.draw_rect(r, edge, false, 4.0)
	c.draw_circle(top + Vector2(0, -w * 0.2), w * 0.4, body.lightened(0.15))
	if st in ["hands_up", "raise_glass", "clap", "happy"]:
		c.draw_line(top + Vector2(w * 0.5, h * 0.2), top + Vector2(w * 0.8, -w * 0.4), edge, 4.0)
		c.draw_line(top + Vector2(-w * 0.5, h * 0.2), top + Vector2(-w * 0.8, -w * 0.4), edge, 4.0)
	c.draw_string(ThemeDB.fallback_font, top + Vector2(-w * 0.5, h + 16), "%s: %s" % [who, st], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color.WHITE)


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
		var p := t - float(s["phase_t0"])
		match scene:
			"demo":
				if ph == "demo" and p >= 0.8 + 0.35:
					stop_t = t
			"input":
				if ph == "input" and int(s["pos"]) >= 1:
					stop_t = t + 0.3
			"mistake":
				if int(s["served"]) == 1 and ph == "serve" and str(s["outcome"]) == "mistake" and p >= 0.6:
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
