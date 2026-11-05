class_name TrackPadView
extends PadView
## The four pads for track mode (a developer view). All four pads play the one voice that has the focus, so the pads
## carry no instrument or lane names, only their key letters. When that voice is muted all four pads are drawn dark
## with "MUTED" on them; between focus stretches (nothing to play) they are drawn dim with no mark. Geometry, key
## labels, touch rectangles and the feedback text are PadView's; only the drawing is replaced because PadView names
## pads by mission family.

const PAD_COLOR := {1: Color(0.98, 0.62, 0.25), 2: Color(0.35, 0.85, 0.98), 3: Color(0.72, 0.55, 1.0), 4: Color(0.55, 0.9, 0.5)}

## () -> String: "play" (the focus voice is sounding), "muted" (it is silent) or "rest" (nothing to play now).
var state_fn: Callable


func _ready() -> void:
	_font = ThemeDB.fallback_font


func _draw() -> void:
	var wall := float(Time.get_ticks_msec()) / 1000.0
	var now := clock.judge_time() if clock != null else 0.0
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.06, 0.08, 0.92))
	draw_line(Vector2(0, 0), Vector2(size.x, 0), Color(0.3, 0.32, 0.36), 2.0)
	var rects := _pad_rects()
	var state := str(state_fn.call()) if state_fn.is_valid() else "play"
	for pad in range(1, BUTTONS + 1):
		_draw_track_pad(pad, rects[pad], now, wall, state)


func _draw_track_pad(pad: int, r: Rect2, now: float, wall: float, state: String) -> void:
	var base: Color = PAD_COLOR[pad]
	if high_contrast:
		base = base.lightened(0.25)
	var muted := state == "muted"
	var rest := state == "rest"
	var hold := float(holding_fn.call(pad, now)) if holding_fn.is_valid() else -1.0
	var down: bool = button_down.get(pad, false)
	var fill := Color(0.1, 0.1, 0.11) if (muted or rest) else base.darkened(0.7)
	if hold >= 0.0 and not muted:
		fill = base.darkened(0.25)
	if down:
		fill = fill.lightened(0.18)
	var radius := r.size.x * 0.12
	_round_rect(r, fill, radius)
	if hold >= 0.0:
		var hr := Rect2(r.position.x, r.end.y - r.size.y * hold, r.size.x, r.size.y * hold)
		_round_rect(hr, (Color(0.35, 0.35, 0.37) if muted else base.lightened(0.15)), radius)
	_round_outline(r, (Color(0.3, 0.3, 0.32) if (muted or rest) else base).lightened(0.2 if down else 0.0), radius, 2.0 if muted else 4.0)
	var fs := int(clampf(r.size.x * 0.13, 12.0, 24.0))
	if muted:
		draw_string(_font, Vector2(r.position.x, r.get_center().y + fs * 0.4), "MUTED", HORIZONTAL_ALIGNMENT_CENTER, r.size.x,
			int(fs * 1.1), Color(1.0, 0.45, 0.4, 0.9))
	if show_keys and not OS.has_feature("mobile"):
		draw_string(_font, Vector2(r.end.x - fs * 1.4, r.end.y - 8.0), PadView.key_name(pad), HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1, 1, 1, 0.45))
	var fb: Dictionary = _feedback.get(pad, {})
	if not fb.is_empty() and wall < float(fb["until"]):
		var a := clampf((float(fb["until"]) - wall) / FEEDBACK_S, 0.0, 1.0)
		draw_string(_font, Vector2(r.position.x - 20.0, r.position.y - 10.0), str(fb["text"]), HORIZONTAL_ALIGNMENT_CENTER,
			r.size.x + 40.0, int(fs * 1.1), Color(fb["color"], a))
