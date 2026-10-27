class_name LaneView
extends Control
## Four note columns, one per touch button, with a timing line and four large unlabelled buttons below it.
## Notes fall from the top of this control to the timing line; a hold is a bar from its start to its tail.
## A note's column is its button; its colour and shape are its lane (kick: round, snare: diamond, bass: bar), so
## the player can see what a note will produce without any label on the button. Draws from the judge's note
## states and the song clock; never owns timing.

const BUTTONS := 4
const LANE_COLORS := {
	"kick": Color(0.97, 0.84, 0.47),
	"bass": Color(0.31, 0.63, 0.88),
	"snare": Color(0.88, 0.35, 0.31),
}
const BUTTON_COLOR := Color(0.85, 0.88, 0.95)
const LOOKAHEAD_S := 1.2
const BUTTON_H := 100.0
const LINE_FROM_BOTTOM := 84.0
const FEEDBACK_S := 0.5

var level: Level
var judge: Judge
var clock: SongClock
var button_down: Dictionary = {1: false, 2: false, 3: false, 4: false}
var _feedback: Dictionary = {}  # button -> {"text", "color", "until"}
var _font: Font


func _ready() -> void:
	_font = ThemeDB.fallback_font


func setup(p_level: Level, p_judge: Judge, p_clock: SongClock) -> void:
	level = p_level
	judge = p_judge
	clock = p_clock


func column_x(button: int) -> float:
	return (button - 1) * column_width()


func column_width() -> float:
	return size.x / BUTTONS


func hit_y() -> float:
	return size.y - LINE_FROM_BOTTOM


## Button rectangles in viewport coordinates, for LaneInput (keys: button 1 -> Dictionary key 1).
func button_rects() -> Dictionary:
	var out := {}
	var origin := get_global_rect().position
	for b in range(1, BUTTONS + 1):
		out[b] = Rect2(origin + Vector2(column_x(b), size.y - BUTTON_H), Vector2(column_width(), BUTTON_H))
	return out


func show_feedback(button: int, text: String, color: Color, now_wall: float) -> void:
	_feedback[button] = {"text": text, "color": color, "until": now_wall + FEEDBACK_S}


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.07, 0.08, 0.11))
	var w := column_width()
	var hy := hit_y()
	var now := clock.judge_time() if clock != null else 0.0
	var wall := float(Time.get_ticks_msec()) / 1000.0
	for b in range(1, BUTTONS + 1):
		var x := column_x(b)
		draw_rect(Rect2(x, 0, w, size.y), Color(1, 1, 1, 0.02 if b % 2 == 0 else 0.0))
		draw_line(Vector2(x, 0), Vector2(x, size.y), Color(1, 1, 1, 0.12), 1.0)
		# button: a plain pad with no label; it lights up while it is held
		var brect := Rect2(x + 8, size.y - BUTTON_H + 8, w - 16, BUTTON_H - 16)
		var pressed: bool = button_down.get(b, false)
		var fill := Color(BUTTON_COLOR, 0.55 if pressed else 0.16)
		draw_rect(brect, fill, true)
		draw_rect(brect, Color(BUTTON_COLOR, 0.95 if pressed else 0.6), false, 3.0)
		# hold progress
		if judge != null:
			var prog := judge.active_hold_progress(b)
			if prog >= 0.0:
				draw_rect(Rect2(x + 10, hy + 6, (w - 20) * prog, 10), Color(LANE_COLORS["bass"], 0.9))
		# feedback
		if _feedback.has(b):
			var fb: Dictionary = _feedback[b]
			if wall < fb["until"]:
				var a: float = clampf((fb["until"] - wall) / FEEDBACK_S, 0.0, 1.0)
				draw_string(_font, Vector2(x, hy - 70), fb["text"], HORIZONTAL_ALIGNMENT_CENTER, w, 28, Color(fb["color"], a))
	# timing line (kept clear of effects)
	draw_line(Vector2(0, hy), Vector2(size.x, hy), Color(1, 1, 1, 0.85), 3.0)
	if level == null or judge == null:
		return
	# notes: time -> y. A note at `now` sits on the line; LOOKAHEAD_S earlier is the top edge.
	var px_per_s := hy / LOOKAHEAD_S
	for i in level.notes.size():
		var n: Dictionary = level.notes[i]
		var t_start: float = n["time"]
		var t_end: float = n["end_time"] if n["type"] == "hold" else t_start
		if t_end < now - 0.25 or t_start > now + LOOKAHEAD_S:
			continue
		var st := judge.state_of(i)
		if st == Judge.State.HIT or st == Judge.State.VOID:
			continue
		var lane: String = n["lane"]
		var col: Color = LANE_COLORS[lane]
		var cx := column_x(int(n["button"])) + w * 0.5
		var y0 := hy - (t_start - now) * px_per_s
		if y0 > hy + 28.0 and n["type"] != "hold":
			continue  # past the line and resolved: keep the button area clear
		var alpha := 1.0
		if st == Judge.State.MISS:
			alpha = 0.35
		elif st == Judge.State.UNAVAILABLE or not judge.is_lane_available(lane):
			alpha = 0.18
		if n["type"] == "hold":
			var y1 := hy - (t_end - now) * px_per_s
			var holding := st == Judge.State.HOLDING
			var bottom := minf(y0, hy) if (holding or st == Judge.State.MISS) else y0
			if y1 > hy:
				continue  # whole hold is behind the line
			var top := minf(y1, bottom)
			draw_rect(Rect2(cx - w * 0.22, top, w * 0.44, bottom - top), Color(col, (0.75 if holding else 0.45) * alpha), true)
			draw_rect(Rect2(cx - w * 0.22, top, w * 0.44, bottom - top), Color(col, alpha), false, 2.0)
			_draw_note_head(lane, cx, bottom, col, alpha)
		else:
			_draw_note_head(lane, cx, y0, col, alpha)


func _draw_note_head(lane: String, cx: float, y: float, col: Color, alpha: float) -> void:
	var c := Color(col, alpha)
	match lane:
		"kick":
			draw_circle(Vector2(cx, y), 16.0, c)
			draw_arc(Vector2(cx, y), 16.0, 0.0, TAU, 24, Color(1, 1, 1, alpha), 2.0)
		"snare":
			var pts := PackedVector2Array([Vector2(cx, y - 18), Vector2(cx + 18, y), Vector2(cx, y + 18), Vector2(cx - 18, y)])
			draw_colored_polygon(pts, c)
			draw_polyline(pts + PackedVector2Array([pts[0]]), Color(1, 1, 1, alpha), 2.0)
		_:
			draw_rect(Rect2(cx - column_width() * 0.22, y - 9, column_width() * 0.44, 18), c, true)
			draw_rect(Rect2(cx - column_width() * 0.22, y - 9, column_width() * 0.44, 18), Color(1, 1, 1, alpha), false, 2.0)
