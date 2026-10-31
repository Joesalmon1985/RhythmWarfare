class_name PadView
extends Control
## The four illuminated pads (PRD section 15): the only play interface. Pads 1 and 2 sit under the left thumb, 3 and 4
## under the right, at fixed positions; the centre between them shows the current sequence and what it will earn.
##
## Everything is drawn from the song clock: a cue's ring closes onto its pad over `lead_in_s` and the pad pulses at the
## onset; a hold keeps the pad lit and fills it to its tail, then flashes. A pad with no cue in the current phase is
## dim. Shapes as well as colours tell the families apart (kick: disc, snare: diamond, bass: bars). Feedback text sits
## above a pad so it never hides the next ring. Works for missions (cue "pad") and the legacy duel (note "button").

const BUTTONS := 4
const FAMILY_COLOR := {"kick": Color(0.98, 0.62, 0.25), "snare": Color(0.35, 0.85, 0.98), "bass": Color(0.72, 0.55, 1.0)}
const HC_COLOR := {"kick": Color(1.0, 0.75, 0.2), "snare": Color(0.2, 1.0, 1.0), "bass": Color(1.0, 0.4, 1.0)}
const KEY_NAMES := {1: "D", 2: "F", 3: "J", 4: "K"}
const FEEDBACK_S := 0.45
const PULSE_S := 0.12

var level: Level
var clock: SongClock
var lead_in_s := 0.7
var high_contrast := false
var reduced_effects := false
var show_keys := true
var holding_fn: Callable  # (pad: int, now: float) -> float: hold progress 0..1, or -1 when the pad holds nothing
var progress_fn: Callable  # (now: float) -> Dictionary: the current sequence's progress (missions), {} otherwise
var button_down: Dictionary = {1: false, 2: false, 3: false, 4: false}
var status_text := ""  # the centre line under the sequence meter (reward results, preparing defenses)
var status_color := Color.WHITE
var status_until := 0.0
var banner_text := ""

var _pad_notes: Dictionary = {}  # pad -> Array[int] note indexes in time order
var _cursor: Dictionary = {}
var _feedback: Dictionary = {}  # pad -> {text, color, until}
var _complete_flash: Dictionary = {}  # pad -> wall time a hold completed
var _font: Font


func setup(p_level: Level, p_clock: SongClock) -> void:
	level = p_level
	clock = p_clock
	_font = ThemeDB.fallback_font
	_pad_notes = {1: [], 2: [], 3: [], 4: []}
	_cursor = {1: 0, 2: 0, 3: 0, 4: 0}
	for i in level.notes.size():
		var pad := _pad_of(level.notes[i])
		if _pad_notes.has(pad):
			_pad_notes[pad].append(i)


static func _pad_of(n: Dictionary) -> int:
	return int(n.get("pad", n.get("button", 0)))


## Pad rectangles in viewport coordinates (for touch hit tests); slightly larger than drawn so a thumb need not be exact.
func button_rects() -> Dictionary:
	var out := {}
	var rects := _pad_rects()
	var xf := get_global_transform_with_canvas()
	for pad in rects:
		var r: Rect2 = rects[pad]
		out[pad] = Rect2(xf * r.position, r.size * xf.get_scale()).grow(r.size.x * 0.08)
	return out


func _pad_rects() -> Dictionary:
	var safe := _safe_margins()
	var h := size.y
	var s := minf(h * 0.84, size.x * 0.15)
	var gap := s * 0.12
	var y := (h - s) * 0.55
	var left := safe.x + gap * 2.0
	var right := size.x - safe.y - gap * 2.0
	return {
		1: Rect2(left, y, s, s), 2: Rect2(left + s + gap, y, s, s),
		3: Rect2(right - 2.0 * s - gap, y, s, s), 4: Rect2(right - s, y, s, s),
	}


func _safe_margins() -> Vector2:
	var vp := get_viewport_rect().size
	var safe := DisplayServer.get_display_safe_area()
	var screen := DisplayServer.screen_get_size()
	if screen.x <= 0 or safe.size.x <= 0:
		return Vector2.ZERO
	var k := vp.x / float(screen.x)
	return Vector2(float(safe.position.x) * k, float(screen.x - safe.end.x) * k)


func show_feedback(pad: int, text: String, color: Color, wall: float) -> void:
	_feedback[pad] = {"text": text, "color": color, "until": wall + FEEDBACK_S}


func flash_complete(pad: int, wall: float) -> void:
	_complete_flash[pad] = wall


func show_status(text: String, color: Color, wall: float, seconds: float = 2.2) -> void:
	status_text = text
	status_color = color
	status_until = wall + seconds


func _process(_delta: float) -> void:
	queue_redraw()


func _family_at(pad: int, tick: int) -> String:
	if level.is_mission():
		var ph := level.phase_at(tick)
		var info: Dictionary = ph.get("pads", {}).get(str(pad), {})
		return str(info.get("family", ""))
	var list: Array = _pad_notes.get(pad, [])
	for i in list:  # the duel: the family of the pad's next note
		if int(level.notes[i]["tick"]) >= tick - 480:
			return str(level.notes[i]["lane"])
	return ""


func _label_at(pad: int, tick: int) -> String:
	if not level.is_mission():
		return ""
	var info: Dictionary = level.phase_at(tick).get("pads", {}).get(str(pad), {})
	return level.voice_name(str(info.get("ref", ""))) if not info.is_empty() else ""


func _draw() -> void:
	if level == null or clock == null:
		return
	var now := clock.judge_time()
	var wall := float(Time.get_ticks_msec()) / 1000.0
	var tick := level.seconds_to_tick(maxf(now, 0.0))
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.06, 0.08, 0.92))
	draw_line(Vector2(0, 0), Vector2(size.x, 0), Color(0.3, 0.32, 0.36), 2.0)
	var rects := _pad_rects()
	for pad in range(1, BUTTONS + 1):
		_draw_pad(pad, rects[pad], now, tick, wall)
	_draw_centre(rects, now, wall)


func _draw_pad(pad: int, r: Rect2, now: float, tick: int, wall: float) -> void:
	var fam := _family_at(pad, tick)
	var palette: Dictionary = HC_COLOR if high_contrast else FAMILY_COLOR
	var base: Color = palette.get(fam, Color(0.45, 0.47, 0.5))
	var active := not fam.is_empty()
	# the nearest coming cue on this pad: preparatory brightening and the approach ring
	var list: Array = _pad_notes[pad]
	var c: int = _cursor[pad]
	while c < list.size() and float(level.notes[list[c]]["end_time" if level.notes[list[c]]["type"] == "hold" else "time"]) < now - 0.2:
		c += 1
	_cursor[pad] = c
	var glow := 0.0
	var rings: Array = []
	var pulse := 0.0
	for k in range(c, mini(c + 6, list.size())):
		var n: Dictionary = level.notes[list[k]]
		var dt: float = float(n["time"]) - now
		if dt > lead_in_s:
			break
		if dt >= 0.0:
			rings.append({"f": dt / lead_in_s, "hold": n["type"] == "hold"})
			glow = maxf(glow, 1.0 - dt / lead_in_s)
		elif dt > -PULSE_S:
			pulse = maxf(pulse, 1.0 + dt / PULSE_S)
	var hold := float(holding_fn.call(pad, now)) if holding_fn.is_valid() else -1.0
	var down: bool = button_down.get(pad, false)
	var fill := base.darkened(0.78) if active else Color(0.12, 0.13, 0.15)
	if active:
		fill = fill.lerp(base.darkened(0.35), glow * 0.55)
	if hold >= 0.0:
		fill = base.darkened(0.25)
	if down:
		fill = fill.lightened(0.18)
	var radius := r.size.x * 0.12
	_round_rect(r, fill, radius)
	if hold >= 0.0:  # the hold fills the pad bottom to top until its tail
		var hr := Rect2(r.position.x, r.end.y - r.size.y * hold, r.size.x, r.size.y * hold)
		_round_rect(hr, base.lightened(0.15), radius)
	if pulse > 0.0:
		_round_rect(r, Color(1, 1, 1, (0.25 if reduced_effects else 0.55) * pulse), radius)
	var flash_at: float = _complete_flash.get(pad, -10.0)
	if wall - flash_at < 0.35:
		var a := 1.0 - (wall - flash_at) / 0.35
		_round_rect(r.grow(r.size.x * 0.04 * (1.0 - a)), Color(base.lightened(0.5), 0.6 * a), radius)
	var border := base if active else Color(0.3, 0.32, 0.35)
	_round_outline(r, border.lightened(0.2 if down else 0.0), radius, 4.0 if active else 2.0)
	for ring in rings:  # rings close onto the pad edge exactly at the onset; a hold's ring is doubled
		var f: float = ring["f"]
		var grow := r.size.x * 0.32 * f
		var col := Color(base.lightened(0.3), 0.25 + 0.75 * (1.0 - f))
		_round_outline(r.grow(grow), col, radius + grow * 0.5, 3.0 if not ring["hold"] else 5.0)
		if ring["hold"]:
			_round_outline(r.grow(grow + 7.0), Color(col, col.a * 0.6), radius + grow * 0.5 + 6.0, 2.0)
	_draw_icon(fam, r, base if active else Color(0.35, 0.37, 0.4), glow, hold >= 0.0)
	var label := _label_at(pad, tick)
	var fs := int(clampf(r.size.x * 0.11, 12.0, 22.0))
	if not label.is_empty():
		draw_string(_font, Vector2(r.position.x, r.position.y + fs + 6.0), label, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs,
			Color(1, 1, 1, 0.92 if active else 0.4))
	if show_keys and not OS.has_feature("mobile"):
		draw_string(_font, Vector2(r.end.x - fs * 1.4, r.end.y - 8.0), KEY_NAMES[pad], HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1, 1, 1, 0.45))
	var fb: Dictionary = _feedback.get(pad, {})
	if not fb.is_empty() and wall < float(fb["until"]):
		var a := clampf((float(fb["until"]) - wall) / FEEDBACK_S, 0.0, 1.0)
		var fy := r.position.y - 10.0 - (0.0 if reduced_effects else (1.0 - a) * 14.0)
		draw_string(_font, Vector2(r.position.x - 20.0, fy), str(fb["text"]), HORIZONTAL_ALIGNMENT_CENTER, r.size.x + 40.0,
			int(fs * 1.15), Color(fb["color"], a))


func _draw_icon(fam: String, r: Rect2, col: Color, glow: float, holding: bool) -> void:
	var c := r.get_center() + Vector2(0, r.size.y * 0.06)
	var s := r.size.x * 0.17 * (1.0 + 0.12 * glow)
	var ic := col.lightened(0.25 + 0.4 * glow) if not holding else Color.WHITE
	match fam:
		"kick":
			draw_circle(c, s, ic)
		"snare":
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -s * 1.2), c + Vector2(s * 1.2, 0), c + Vector2(0, s * 1.2), c + Vector2(-s * 1.2, 0)]), ic)
		"bass":
			for k in 3:
				var w := s * (2.2 - 0.5 * absf(k - 1))
				draw_rect(Rect2(c.x - w * 0.5, c.y - s + k * s * 0.8, w, s * 0.42), ic)
		_:
			draw_arc(c, s * 0.8, 0.0, TAU, 24, Color(ic, 0.5), 2.0)


func _draw_centre(rects: Dictionary, now: float, wall: float) -> void:
	var x0: float = (rects[2] as Rect2).end.x + 20.0
	var x1: float = (rects[3] as Rect2).position.x - 20.0
	var w := x1 - x0
	if w < 80.0:
		return
	var y := size.y * 0.24
	var fs := int(clampf(size.y * 0.085, 14.0, 26.0))
	if not banner_text.is_empty():
		draw_string(_font, Vector2(x0, y), banner_text, HORIZONTAL_ALIGNMENT_CENTER, w, int(fs * 1.25), Color(1.0, 0.9, 0.55))
	var p: Dictionary = progress_fn.call(now) if progress_fn.is_valid() else {}
	if not p.is_empty():
		var cues := int(p["cues"])
		var seg_w := minf(w / float(maxi(cues, 1)), 26.0)
		var total_w := seg_w * cues
		var sx := x0 + (w - total_w) * 0.5
		var sy := size.y * 0.42
		var need := level.sequence_threshold * float(cues)
		for k in cues:
			var filled := float(p["credit"]) - float(k)
			var rr := Rect2(sx + k * seg_w + 2.0, sy, seg_w - 4.0, fs * 0.6)
			draw_rect(rr, Color(0.2, 0.22, 0.26))
			if filled > 0.0:
				draw_rect(Rect2(rr.position, Vector2(rr.size.x * clampf(filled, 0.0, 1.0), rr.size.y)), Color(0.55, 0.9, 0.55))
		var mark := sx + need * seg_w
		draw_line(Vector2(mark, sy - 4.0), Vector2(mark, sy + fs * 0.6 + 4.0), Color(1, 1, 1, 0.6), 2.0)
		draw_string(_font, Vector2(x0, sy + fs * 0.6 + fs + 6.0), "→ " + MissionRules.reward_name(str(p["reward"])), HORIZONTAL_ALIGNMENT_CENTER, w, fs, Color(0.85, 0.88, 0.92))
	if not status_text.is_empty() and wall < status_until:
		draw_string(_font, Vector2(x0, size.y * 0.9), status_text, HORIZONTAL_ALIGNMENT_CENTER, w, int(fs * 0.85), Color(status_color, clampf(status_until - wall, 0.0, 1.0)))


var _fill_box := StyleBoxFlat.new()
var _line_box := StyleBoxFlat.new()


func _round_rect(r: Rect2, col: Color, radius: float) -> void:
	_fill_box.bg_color = col
	_fill_box.set_corner_radius_all(int(radius))
	draw_style_box(_fill_box, r)  # the box is drawn now, so reusing it for the next call is safe


func _round_outline(r: Rect2, col: Color, radius: float, width: float) -> void:
	_line_box.draw_center = false
	_line_box.border_color = col
	_line_box.set_border_width_all(int(width))
	_line_box.set_corner_radius_all(int(radius))
	draw_style_box(_line_box, r)
