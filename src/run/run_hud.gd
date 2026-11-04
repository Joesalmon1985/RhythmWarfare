class_name RunHud
extends Control
## The run's overlay on the stage: the level title card, the four mix stages (a pip each, the current one lit), the crowd-energy meter that is
## also the survival meter, short captions (BASS ENTERS, RISER / FALL, ROUTE CHOSEN) and the countdown. Direction arrows are real Buttons made
## by RunPlay (touch targets), this only draws what is not interactive.

var engine: RunEngine
var data: RunData
var countdown := ""
var countdown_frac := 0.0
var reduced := false
var captions: Array = []  # [{text, tone, t0, hold}] in song time
var title_card := {}  # {kicker, text, t0}
var now_t := 0.0
var route_hint := ""
var fade := 0.0  # 0..1 black overlay for the end of a run

var _font: Font


func _ready() -> void:
	_font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func caption(text: String, tone: String, t0: float, hold := 1.8) -> void:
	captions = captions.filter(func(c: Dictionary) -> bool: return now_t - float(c["t0"]) < float(c["hold"]) + 0.5)
	captions.append({"text": text, "tone": tone, "t0": t0, "hold": hold})


func show_title(kicker: String, text: String, t0: float) -> void:
	title_card = {"kicker": kicker, "text": text, "t0": t0}


func _outlined(pos: Vector2, s: String, fs: int, col: Color, w := -1.0, align := HORIZONTAL_ALIGNMENT_LEFT) -> void:
	draw_string_outline(_font, pos, s, align, w, fs, 6, Color(0, 0, 0, col.a * 0.85))
	draw_string(_font, pos, s, align, w, fs, col)


func _draw() -> void:
	if engine == null:
		return
	var sz := size
	var fs := int(clampf(sz.y * 0.045, 14.0, 28.0))
	# energy meter: top left
	var pad := 14.0
	var bar := Rect2(pad, pad + fs * 1.1, minf(sz.x * 0.28, 320.0), fs * 0.55)
	var e := clampf(engine.energy / float(engine.cfg["energy"]["max"]), 0.0, 1.0)
	_outlined(Vector2(pad, pad + fs * 0.9), "CROWD", int(fs * 0.8), Color(0.85, 0.9, 1.0, 0.9))
	draw_rect(bar, Color(0.05, 0.06, 0.14, 0.85))
	var low := e < 0.25
	var col := Color(1.0, 0.35, 0.3) if low else Color(0.35, 1.0, 0.8).lerp(Color(1.0, 0.85, 0.35), clampf((e - 0.6) / 0.4, 0.0, 1.0))
	if low and not reduced:
		col.a = 0.65 + 0.35 * sin(Time.get_ticks_msec() / 120.0)
	draw_rect(Rect2(bar.position, Vector2(bar.size.x * e, bar.size.y)), col)
	draw_rect(bar, Color(1, 1, 1, 0.35), false, 1.5)
	# mix stages
	var labels: Array = engine.cfg["stages"]
	var px := bar.position.x
	var py := bar.end.y + fs * 0.7
	var pw := bar.size.x / 4.0
	for i in 4:
		var on := i == engine.stage
		var done := i < engine.stage
		var r := Rect2(px + i * pw + 2.0, py, pw - 4.0, fs * 0.42)
		draw_rect(r, Color(0.35, 1.0, 0.8, 0.9) if on else (Color(0.3, 0.55, 0.9, 0.7) if done else Color(0.12, 0.14, 0.26, 0.8)))
	_outlined(Vector2(px, py + fs * 1.35), str(labels[engine.stage]["label"]).to_upper() + "  -  " + ("DRUM CUES" if str(labels[engine.stage]["cue"]) == "drums" else "BASS CUES"), int(fs * 0.7), Color(0.9, 0.93, 1.0, 0.9))
	var node: Dictionary = data.nodes[engine.node_id]
	_outlined(Vector2(px, py + fs * 2.3), "%s   LEVEL %d" % [str(node["title"]).to_upper(), engine.phase_n], int(fs * 0.7), Color(1.0, 0.82, 0.5, 0.9))
	# captions
	var y := sz.y * 0.2
	for c in captions:
		var age := now_t - float(c["t0"])
		if age < 0.0 or age > float(c["hold"]):
			continue
		var a := clampf(minf(age / 0.2, (float(c["hold"]) - age) / 0.4), 0.0, 1.0)
		var tone: Color = {"good": Color(0.5, 1.0, 0.85), "bad": Color(1.0, 0.7, 0.45), "info": Color(0.9, 0.9, 1.0)}.get(str(c["tone"]), Color(0.9, 0.9, 1.0))
		_outlined(Vector2(0, y), str(c["text"]), int(fs * 1.5), Color(tone, a), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
		y += fs * 1.8
	if not route_hint.is_empty():
		_outlined(Vector2(0, sz.y * 0.88), route_hint, int(fs * 0.9), Color(1, 1, 1, 0.85), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
	if not title_card.is_empty():
		var age2 := now_t - float(title_card["t0"])
		if age2 >= 0.0 and age2 < 3.4:
			var a2 := clampf(minf(age2 / 0.3, (3.4 - age2) / 0.6), 0.0, 1.0)
			_outlined(Vector2(0, sz.y * 0.4), str(title_card["kicker"]), int(fs * 0.9), Color(1.0, 0.8, 0.5, a2), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
			_outlined(Vector2(0, sz.y * 0.4 + fs * 2.0), str(title_card["text"]), int(fs * 2.2), Color(1, 1, 1, a2), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
	if not countdown.is_empty():
		_outlined(Vector2(0, sz.y * 0.5), countdown, int(fs * 4.0), Color(1, 1, 1, 0.5 + 0.5 * (1.0 - countdown_frac)), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
	if fade > 0.0:
		draw_rect(Rect2(Vector2.ZERO, sz), Color(0, 0, 0, clampf(fade, 0.0, 1.0)))
