class_name NoteLane
extends Control
## Falling notes (Magic Tiles style): every cue is a translucent shape that falls straight down the screen and lands
## exactly on its pad at the cue's hit time. A hold is a long bar whose bottom square lands on the pad at press time and
## keeps passing through until the hold ends. The lane covers the whole screen (battlefield and pad strip) and draws
## nothing but the notes. Everything comes from the song clock, so pausing and calibration need no special handling.
##
## The geometry is pure (`shape_rect`): a note is its pad rectangle moved up by dt / travel_s of the pad's distance to
## the top of the screen, a hold additionally grows upward by its length at the same speed.

const VISIBLE_AFTER_S := 0.25  # a resolved miss keeps falling this long (a hold: after its end), fading out
const DUEL_ACCEPT_S := 0.14  # the legacy duel has no judge state: a tap is pending until this long after its hit time
const FILL_ALPHA := 0.40
const HC_FILL_ALPHA := 0.75
const MISS_TINT := Color(1.0, 0.25, 0.22)

var level: Level
var clock: SongClock
var pad_view: PadView
var travel_s := 1.2  # seconds a note takes to fall from the screen top to its pad
var high_contrast := false
var reduced_effects := false
var state_fn: Callable  # (cue index: int) -> "pending" | "hit" | "miss"; unset in the duel

var _order: Array[int] = []  # note indexes sorted by hit time
var _cursor := 0
var _last_now := -INF
var _fill_box := StyleBoxFlat.new()
var _line_box := StyleBoxFlat.new()


func setup(p_level: Level, p_clock: SongClock, p_pad_view: PadView) -> void:
	level = p_level
	clock = p_clock
	pad_view = p_pad_view
	_order.clear()
	for i in level.notes.size():
		_order.append(i)
	_order.sort_custom(func(a: int, b: int) -> bool:
		var ta: float = float(level.notes[a]["time"])
		var tb: float = float(level.notes[b]["time"])
		return ta < tb if ta != tb else a < b)
	_cursor = 0
	_last_now = -INF


## The shape of a note `dt` seconds before its hit time (negative: after it), `hold_s` long (0 for a tap), on `pad`.
## `travel_px` is the distance a note covers in `travel_s`: at dt = travel_s the shape has just left the top of the screen.
static func shape_rect(pad: Rect2, dt: float, hold_s: float, travel_s: float, travel_px: float) -> Rect2:
	var per_s := travel_px / travel_s
	var r := Rect2(pad)
	r.position.y -= dt * per_s
	if hold_s > 0.0:
		r.position.y -= hold_s * per_s
		r.size.y += hold_s * per_s
	return r


## The notes to draw at song time `now`: {index, pad, rect, hold, state, dt, end_dt}. `pad_rects` (pad -> Rect2 in this
## control's coordinates) defaults to the pad view's. O(visible) per frame: a cursor skips the notes already gone.
func visible_notes(now: float, pad_rects: Dictionary = {}) -> Array:
	var out: Array = []
	if level == null:
		return out
	if pad_rects.is_empty():
		pad_rects = _pad_rects_local()
	if now < _last_now:  # the clock went back (a restart): rescan from the start
		_cursor = 0
	_last_now = now
	while _cursor < _order.size() and _last_visible_time(level.notes[_order[_cursor]]) - now <= -VISIBLE_AFTER_S:
		_cursor += 1
	for k in range(_cursor, _order.size()):
		var i: int = _order[k]
		var n: Dictionary = level.notes[i]
		var dt: float = float(n["time"]) - now
		if dt >= travel_s:
			break
		var pad := PadView._pad_of(n)
		if not pad_rects.has(pad):
			continue
		var hold := str(n.get("type", "tap")) == "hold"
		var hold_s := maxf(float(n.get("end_time", n["time"])) - float(n["time"]), 0.0) if hold else 0.0
		hold = hold and hold_s > 0.0
		var end_dt := dt + hold_s
		if end_dt <= -VISIBLE_AFTER_S:
			continue
		var state := _state_of(i, dt, end_dt)
		if state == "hit" and dt < 0.0:
			continue
		var pr: Rect2 = pad_rects[pad]
		out.append({"index": i, "pad": pad, "rect": shape_rect(pr, dt, hold_s, travel_s, pr.end.y), "hold": hold,
			"state": state, "dt": dt, "end_dt": end_dt})
	return out


func _last_visible_time(n: Dictionary) -> float:
	return float(n.get("end_time", n["time"])) if str(n.get("type", "tap")) == "hold" else float(n["time"])


func _state_of(i: int, dt: float, end_dt: float) -> String:
	if state_fn.is_valid():
		return str(state_fn.call(i))
	# the duel: pending through the accept window (a hold through its length), gone after
	return "pending" if (dt >= -DUEL_ACCEPT_S or end_dt >= 0.0) else "hit"


## The pads in this control's coordinates (the pad view reports them in viewport coordinates).
func _pad_rects_local() -> Dictionary:
	if pad_view == null:
		return {}
	var inv := get_global_transform_with_canvas().affine_inverse()
	var out := {}
	var rects := pad_view.pad_rects_global()
	for pad in rects:
		var r: Rect2 = rects[pad]
		out[pad] = Rect2(inv * r.position, r.size * inv.get_scale())
	return out


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if level == null or clock == null or pad_view == null:
		return
	var palette: Dictionary = PadView.HC_COLOR if high_contrast else PadView.FAMILY_COLOR
	var fill_a := HC_FILL_ALPHA if high_contrast else FILL_ALPHA
	var line_w := 3.0 if high_contrast else 2.0
	for v in visible_notes(clock.judge_time()):
		var n: Dictionary = level.notes[int(v["index"])]
		var r: Rect2 = v["rect"]
		var col: Color = palette.get(str(n.get("family", n.get("lane", ""))), Color(0.7, 0.72, 0.76))
		var fade := 1.0
		if v["state"] == "miss":
			col = col.lerp(MISS_TINT, 0.7)
			if not reduced_effects and float(v["end_dt"]) < 0.0:
				fade = clampf(1.0 + float(v["end_dt"]) / VISIBLE_AFTER_S, 0.0, 1.0)
		var radius := r.size.x * 0.12
		_round_rect(r, Color(col, fill_a * fade), radius)
		_round_outline(r, Color(1, 1, 1, 0.8 * fade), radius, line_w)
		if v["hold"]:
			var cap := Rect2(r.position.x, r.end.y - 6.0, r.size.x, 6.0)
			_round_rect(cap, Color(col.lightened(0.45), minf(fade * 0.95, 1.0)), minf(radius, 3.0))


func _round_rect(r: Rect2, col: Color, radius: float) -> void:
	_fill_box.bg_color = col
	_fill_box.set_corner_radius_all(int(radius))
	draw_style_box(_fill_box, r)


func _round_outline(r: Rect2, col: Color, radius: float, width: float) -> void:
	_line_box.draw_center = false
	_line_box.border_color = col
	_line_box.set_border_width_all(int(width))
	_line_box.set_corner_radius_all(int(radius))
	draw_style_box(_line_box, r)
