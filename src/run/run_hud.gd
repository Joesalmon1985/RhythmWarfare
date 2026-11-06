class_name RunHud
extends Control
## The run's overlay on the stage. It is silent (docs/THREE_PATHS_AND_FACES_PLAN.md D3, 2.4): during play it draws no title card, no captions, no world or room names, no numeric countdown and no
## labels, only the four mix stages (a pip each, the current one lit), the crowd-energy meter that is also the survival meter, and a thin route-window bar that empties over the 16 beats of the choice
## window. What the text used to say is in the world: BASS ENTERS is the bass coming in and the lights lifting, ROUTE CHOSEN the hotspot's committed flash, a new room the door walk and a light swell
## on its downbeat (StoryStage "room_swell"), RISER / FALL are audible. `RW_DEV_TEXT=1` (DevText) brings all the old text back for debugging and for the tests that read it.
## Direction arrows are real Buttons made by RunPlay (touch targets), this only draws what is not interactive.

var engine: RunEngine
var data: RunData
var countdown := ""
var countdown_frac := 0.0
var reduced := false
var captions: Array = []  # [{text, tone, t0, hold}] in song time (RW_DEV_TEXT only)
var title_card := {}  # {kicker, text, t0} (RW_DEV_TEXT only)
var now_t := 0.0
var route_hint := ""
var stage_h := 0.0  # height of the stage area above the pads (0: the whole control)
var silent := false  # a minigame owns the picture: caption() and show_title() do nothing and no text is drawn while this is true (the meter and the stage pips stay)
var fade := 0.0  # 0..1 black overlay for the end of a run
var strings_drawn := 0  # draw_string calls made by `_outlined` (the silent-HUD test counts them)
var frames_drawn := 0  # `_draw` passes made (so that test can show the HUD really drew)

var _font: Font
var _plate := StyleBoxFlat.new()
var _pip := StyleBoxFlat.new()
var _shown_at := -10.0  # wall time the HUD was last shown: it fades in rather than popping back (after the Bassment, say)

const FADE_IN_S := 0.35
const INK := Color(0.075, 0.067, 0.122)  # #13111f


func _ready() -> void:
	_font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _notification(what: int) -> void:
	if what == NOTIFICATION_VISIBILITY_CHANGED and is_visible_in_tree():
		_shown_at = float(Time.get_ticks_msec()) / 1000.0


func caption(text: String, tone: String, t0: float, hold := 1.8) -> void:
	if silent or not DevText.on():
		return
	captions = captions.filter(func(c: Dictionary) -> bool: return now_t - float(c["t0"]) < float(c["hold"]) + 0.5)
	captions.append({"text": text, "tone": tone, "t0": t0, "hold": hold})


func show_title(kicker: String, text: String, t0: float) -> void:
	if silent or not DevText.on():
		return
	title_card = {"kicker": kicker, "text": text, "t0": t0}


func _outlined(pos: Vector2, s: String, fs: int, col: Color, w := -1.0, align := HORIZONTAL_ALIGNMENT_LEFT) -> void:
	if silent and (countdown.is_empty() or s != countdown):  # the count back in after a pause still shows
		return
	strings_drawn += 1
	draw_string_outline(_font, pos, s, align, w, fs, 6, Color(0, 0, 0, col.a * 0.85))
	draw_string(_font, pos, s, align, w, fs, col)


## The share of the choice window left at song time `t` (1 at beat 48, 0 at the downbeat), -1 when the window is not open. Pure: the bar is a function of the clock.
func window_left(t: float) -> float:
	if engine == null or not engine.window_open:
		return -1.0
	var span := engine.timing("block_beats") * engine.beat_s
	return clampf((engine.t_of(engine.timing("phase_beats")) - t) / span, 0.0, 1.0)


func _draw() -> void:
	if engine == null:
		return
	frames_drawn += 1
	var sz := size
	var text_on := DevText.on()
	var fs := int(clampf(sz.y * 0.045, 14.0, 28.0))
	modulate.a = 1.0 if reduced else clampf((float(Time.get_ticks_msec()) / 1000.0 - _shown_at) / FADE_IN_S, 0.0, 1.0)
	# the energy meter and the mix stages: top left, on one plate in the strip's style (the UI's corner radius, the shared ink, the neon edge)
	var pad := 14.0
	var bar := Rect2(pad + 12.0, pad + fs * 1.1, minf(sz.x * 0.26, 300.0), fs * 0.55)
	var e := clampf(engine.energy / float(engine.cfg["energy"]["max"]), 0.0, 1.0)
	if text_on:
		_outlined(Vector2(bar.position.x, pad + fs * 0.9), "CROWD", int(fs * 0.8), Color(0.85, 0.9, 1.0, 0.9))
	var py := bar.end.y + fs * 0.45
	var plate := Rect2(pad, bar.position.y - 10.0, bar.size.x + 24.0, py + fs * 0.42 + 10.0 - (bar.position.y - 10.0))
	_plate.bg_color = Color(INK, 0.72)
	_plate.border_color = Color(StoryStyle.EDGE, 0.55)
	_plate.set_border_width_all(2)
	_plate.set_corner_radius_all(10)
	draw_style_box(_plate, plate)
	var low := e < 0.25
	var cells := 24
	var cw := bar.size.x / float(cells)
	draw_rect(bar, Color(0.12, 0.14, 0.24))
	var pulse := 1.0 if (not low or reduced) else 0.65 + 0.35 * sin(Time.get_ticks_msec() / 120.0)
	for k in cells:
		var u := float(k) / float(cells)
		if u >= e:
			break
		var col := Color(1.0, 0.35, 0.3) if low else Color(0.35, 1.0, 0.8).lerp(Color(1.0, 0.85, 0.35), clampf((u - 0.6) / 0.4, 0.0, 1.0))
		draw_rect(Rect2(bar.position.x + cw * k + 1.0, bar.position.y, cw - 2.0, bar.size.y), Color(col, pulse))
	# mix stages: four pips under the meter, the current one lit
	var labels: Array = engine.cfg["stages"]
	var px := bar.position.x
	var pw := bar.size.x / 4.0
	for i in 4:
		var on := i == engine.stage
		var done := i < engine.stage
		var r := Rect2(px + i * pw + 2.0, py, pw - 4.0, fs * 0.42)
		_pip.bg_color = Color(0.35, 1.0, 0.8, 0.95) if on else (Color(0.3, 0.55, 0.9, 0.75) if done else Color(0.12, 0.14, 0.26, 0.9))
		_pip.set_corner_radius_all(3)
		draw_style_box(_pip, r)
	# the route window: a thin bar along the bottom of the stage that empties as the 16 beats run out (the same bar the Bassment's four-bar window uses)
	var left := window_left(now_t)
	if left >= 0.0:
		var sh := stage_h if stage_h > 0.0 else sz.y
		var bar_h := maxf(sh * 0.014, 4.0)
		var bw := sz.x * 0.95
		draw_rect(Rect2(sz.x * 0.025, sh - bar_h - 2.0, bw, bar_h), Color(0.05, 0.06, 0.14, 0.45))
		draw_rect(Rect2(sz.x * 0.025, sh - bar_h - 2.0, bw * left, bar_h), Color(1.0, 0.82, 0.5, 0.9))
	if text_on:
		_draw_text(sz, fs, px, py, labels)
	if fade > 0.0:
		draw_rect(Rect2(Vector2.ZERO, sz), Color(0, 0, 0, clampf(fade, 0.0, 1.0)))


## Everything that reads: the stage label, world and room names, captions, the route hint, the title card and the numeric countdown (RW_DEV_TEXT=1 only).
func _draw_text(sz: Vector2, fs: int, px: float, py: float, labels: Array) -> void:
	_outlined(Vector2(px, py + fs * 1.35), str(labels[engine.stage]["label"]).to_upper() + "  -  " + ("DRUM CUES" if str(labels[engine.stage]["cue"]) == "drums" else "BASS CUES"), int(fs * 0.7), Color(0.9, 0.93, 1.0, 0.9))
	var node: Dictionary = data.nodes[engine.node_id]
	_outlined(Vector2(px, py + fs * 2.3), "%s   LEVEL %d" % [str(node["world_title"]).to_upper(), engine.phase_n], int(fs * 0.7), Color(1.0, 0.82, 0.5, 0.9))
	_outlined(Vector2(px, py + fs * 3.2), str(node["title"]).to_upper(), int(fs * 0.62), Color(1.0, 0.9, 0.7, 0.78))
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
		_outlined(Vector2(0, (stage_h if stage_h > 0.0 else sz.y) - fs * 0.6), route_hint, int(fs * 0.8), Color(1, 1, 1, 0.85), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
	if not title_card.is_empty():
		var age2 := now_t - float(title_card["t0"])
		if age2 >= 0.0 and age2 < 3.4:
			var a2 := clampf(minf(age2 / 0.3, (3.4 - age2) / 0.6), 0.0, 1.0)
			_outlined(Vector2(0, sz.y * 0.4), str(title_card["kicker"]), int(fs * 0.9), Color(1.0, 0.8, 0.5, a2), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
			_outlined(Vector2(0, sz.y * 0.4 + fs * 2.0), str(title_card["text"]), int(fs * 2.2), Color(1, 1, 1, a2), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
	if not countdown.is_empty():
		_outlined(Vector2(0, sz.y * 0.5), countdown, int(fs * 4.0), Color(1, 1, 1, 0.5 + 0.5 * (1.0 - countdown_frac)), sz.x, HORIZONTAL_ALIGNMENT_CENTER)
