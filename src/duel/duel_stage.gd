class_name DuelStage
extends Control
## The duel's picture (presentation only, drawn in one _draw): the arena, the two wizards (this player on the left on both phones),
## health bars, streak pips, the spells flying between them with their impacts, damage numbers and the banner text. It knows nothing
## of rules: the scene feeds it phrase events ({spells, hp10, results}) and it shows them, landing the health change when the spell arrives.

const FIRE_CORE := Color(1.0, 0.92, 0.55)
const FIRE_EDGE := Color(1.0, 0.45, 0.12)
const ARCANE_CORE := Color(0.92, 0.82, 1.0)
const ARCANE_EDGE := Color(0.55, 0.3, 1.0)
const ME_TINT := Color(1.0, 1.0, 1.0)
const OPP_TINT := Color(1.0, 0.62, 0.58)
const BAR_BACK := Color(0.04, 0.04, 0.08, 0.85)

var backdrop: Texture2D
var wizard: Texture2D
var names: Array = ["You", "Rival"]
var max_hp10 := 1500
var flight_s := 0.95
var banner := ""
var banner_color := Color(1, 0.95, 0.8)
var sub_banner := ""
var phrase_text := ""
var streak: Array = [0, 0]
var streak_cap := 5
var reduced_effects := false

var _hp_shown: Array = [1500.0, 1500.0]
var _hp_target: Array = [1500, 1500]
var _spells: Array = []
var _bursts: Array = []
var _floaters: Array = []
var _anim: Array = [{"cast": -9.0, "hit": -9.0, "fizzle": -9.0}, {"cast": -9.0, "hit": -9.0, "fizzle": -9.0}]
var _down := -1  # the wizard that fell
var _down_t := 0.0
var _wall := 0.0


func setup(p_max_hp10: int, p_flight_s: float, p_streak_cap: int) -> void:
	max_hp10 = p_max_hp10
	flight_s = p_flight_s
	streak_cap = p_streak_cap
	_hp_shown = [float(max_hp10), float(max_hp10)]
	_hp_target = [max_hp10, max_hp10]
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true


func now() -> float:
	return float(Time.get_ticks_msec()) / 1000.0


## A phrase landed (both results in): launch the spells, fizzle the failed ones, schedule the health change for when they arrive.
func add_phrase(ev: Dictionary) -> void:
	var t := now()
	var cast_sides := {}
	for s in ev["spells"]:
		cast_sides[int(s["from"])] = true
		_spells.append({"from": int(s["from"]), "to": int(s["to"]), "p": float(s["power10"]) / 10.0, "family": str(s["family"]), "t0": t, "landed": false,
			"hp_all": (ev["hp10"] as Array).duplicate()})
		(_anim[int(s["from"])] as Dictionary)["cast"] = t
	for side in 2:
		if not cast_sides.has(side):
			(_anim[side] as Dictionary)["fizzle"] = t
			_floaters.append({"side": side, "text": "fizzle", "t": t, "color": Color(0.75, 0.75, 0.8), "rise": 0.5})
	if ev["spells"].is_empty():
		_hp_target = (ev["hp10"] as Array).duplicate()
	queue_redraw()


func knock_out(side: int) -> void:
	_down = side
	_down_t = now()


func hp_shown10(side: int) -> int:
	return int(round(float(_hp_shown[side])))


func pending_spells() -> int:
	return _spells.size()


# --- layout ---------------------------------------------------------------------------------------------------------------------

func _foot(side: int) -> Vector2:
	return Vector2(size.x * (0.24 if side == 0 else 0.76), size.y * 0.86)


func _wiz_size() -> float:
	return minf(size.y * 0.56, size.x * 0.25)


func _hand(side: int) -> Vector2:
	var f := _foot(side)
	var s := _wiz_size()
	return Vector2(f.x + (0.34 if side == 0 else -0.34) * s, f.y - s * 0.66)


func _chest(side: int) -> Vector2:
	var f := _foot(side)
	return Vector2(f.x, f.y - s_half())


func s_half() -> float:
	return _wiz_size() * 0.5


# --- drawing --------------------------------------------------------------------------------------------------------------------

func _process(_delta: float) -> void:
	_wall = now()
	for sp in _spells:
		if not bool(sp["landed"]) and _wall - float(sp["t0"]) >= flight_s:
			_land(sp)
	_spells = _spells.filter(func(sp: Dictionary) -> bool: return not bool(sp["landed"]) or _wall - float(sp["t0"]) < flight_s + 0.05)
	_bursts = _bursts.filter(func(b: Dictionary) -> bool: return _wall - float(b["t"]) < 0.6)
	_floaters = _floaters.filter(func(f: Dictionary) -> bool: return _wall - float(f["t"]) < 1.2)
	for side in 2:
		var step := float(max_hp10) * 1.4 * get_process_delta_time()
		var target := float(_hp_target[side])
		_hp_shown[side] = move_toward(float(_hp_shown[side]), target, step)
	queue_redraw()


func _land(sp: Dictionary) -> void:
	sp["landed"] = true
	var to := int(sp["to"])
	_hp_target = (sp["hp_all"] as Array).duplicate()
	(_anim[to] as Dictionary)["hit"] = _wall
	var col := _edge(str(sp["family"]))
	_bursts.append({"pos": _chest(to), "t": _wall, "color": col, "p": float(sp["p"])})
	_floaters.append({"side": to, "text": "-%.1f" % float(sp["p"]), "t": _wall, "color": Color(1.0, 0.9, 0.75), "rise": 1.0})


func _core(fam: String) -> Color:
	return ARCANE_CORE if fam == "bass" else FIRE_CORE


func _edge(fam: String) -> Color:
	return ARCANE_EDGE if fam == "bass" else FIRE_EDGE


func _draw() -> void:
	if size.x < 4.0:
		return
	if backdrop != null:
		draw_texture_rect(backdrop, Rect2(Vector2.ZERO, size), false)
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.0, 0.0, 0.05, 0.32))
	draw_rect(Rect2(0, size.y * 0.8, size.x, size.y * 0.2), Color(0.0, 0.0, 0.03, 0.28))
	for side in 2:
		_draw_wizard(side)
	for sp in _spells:
		if not bool(sp["landed"]):
			_draw_spell(sp)
	for b in _bursts:
		_draw_burst(b)
	for f in _floaters:
		_draw_floater(f)
	_draw_hud()
	if banner != "":
		var fs := int(clampf(size.y * 0.13, 22.0, 90.0))
		_text_centered(banner, Vector2(size.x * 0.5, size.y * 0.42), fs, banner_color)
		if sub_banner != "":
			_text_centered(sub_banner, Vector2(size.x * 0.5, size.y * 0.42 + fs * 1.0), int(fs * 0.38), Color(0.9, 0.92, 1.0))


func _draw_wizard(side: int) -> void:
	if wizard == null:
		return
	var a: Dictionary = _anim[side]
	var s := _wiz_size()
	var f := _foot(side)
	var dir := 1.0 if side == 0 else -1.0
	var bob := sin(_wall * 2.1 + float(side) * 1.7) * size.y * 0.008
	var since_cast := _wall - float(a["cast"])
	var lunge := 0.0
	if since_cast >= 0.0 and since_cast < 0.4:
		lunge = sin(since_cast / 0.4 * PI) * s * 0.12 * dir
	var since_hit := _wall - float(a["hit"])
	var shake := 0.0
	var tint := ME_TINT if side == 0 else OPP_TINT
	if since_hit >= 0.0 and since_hit < 0.35 and not reduced_effects:
		shake = sin(since_hit * 70.0) * s * 0.05 * (1.0 - since_hit / 0.35)
		tint = tint.lerp(Color(1.0, 0.3, 0.25), 1.0 - since_hit / 0.35)
	var angle := 0.0
	var alpha := 1.0
	var drop := 0.0
	if _down == side:
		var k := clampf((_wall - _down_t) / 0.9, 0.0, 1.0)
		angle = k * 1.3 * -dir
		alpha = 1.0 - k * 0.55
		drop = k * s * 0.12
	var pos := Vector2(f.x + lunge + shake, f.y + bob + drop)
	# a soft light behind each wizard (cool for this player, warm for the rival) and a shadow on the floor, so the dark robes read against the dark arena
	var glow_col := Color(0.4, 0.7, 1.0) if side == 0 else Color(1.0, 0.45, 0.35)
	var centre := Vector2(f.x, f.y - s * 0.5)
	for i in 4:
		draw_circle(centre, s * (0.62 - float(i) * 0.11), Color(glow_col.r, glow_col.g, glow_col.b, 0.07))
	draw_set_transform(Vector2(f.x, f.y), 0.0, Vector2(1.0, 0.22))
	draw_circle(Vector2.ZERO, s * 0.42, Color(0, 0, 0, 0.4))
	draw_set_transform(pos, angle, Vector2(-1.0 if side == 0 else 1.0, 1.0))  # the staff is on the inner side of each wizard
	draw_texture_rect(wizard, Rect2(Vector2(-s * 0.5, -s), Vector2(s, s)), false, Color(tint.r, tint.g, tint.b, alpha))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# the staff glows while casting, a puff of smoke when the spell fizzles
	if since_cast >= 0.0 and since_cast < 0.5:
		var k2 := 1.0 - since_cast / 0.5
		var h := _hand(side) + Vector2(lunge, bob)
		draw_circle(h, s * 0.16 * (0.6 + k2), Color(1.0, 0.8, 0.4, 0.35 * k2))
		draw_circle(h, s * 0.07 * (0.6 + k2), Color(1.0, 1.0, 0.8, 0.8 * k2))
	var since_fz := _wall - float(a["fizzle"])
	if since_fz >= 0.0 and since_fz < 0.7:
		var k3 := since_fz / 0.7
		var h2 := _hand(side)
		for i in 4:
			var o := Vector2(cos(float(i) * 1.9 + 0.5) * s * 0.1 * k3, -k3 * s * 0.25 - float(i) * s * 0.03)
			draw_circle(h2 + o, s * (0.05 + 0.05 * k3), Color(0.6, 0.6, 0.66, 0.5 * (1.0 - k3)))


func _draw_spell(sp: Dictionary) -> void:
	var u := clampf((_wall - float(sp["t0"])) / flight_s, 0.0, 1.0)
	var from := _hand(int(sp["from"]))
	var to := _chest(int(sp["to"]))
	var fam := str(sp["family"])
	var r := size.y * (0.022 + 0.0016 * float(sp["p"]))
	var core := _core(fam)
	var edge := _edge(fam)
	var arch := -sin(u * PI) * size.y * (0.1 if fam == "drums" else 0.04)
	for i in range(9, -1, -1):
		var uu := clampf(u - float(i) * 0.028, 0.0, 1.0)
		var p := from.lerp(to, uu) + Vector2(0, -sin(uu * PI) * size.y * (0.1 if fam == "drums" else 0.04))
		var k := 1.0 - float(i) / 10.0
		draw_circle(p, r * (0.4 + 0.6 * k), Color(edge.r, edge.g, edge.b, 0.22 * k))
	var pos := from.lerp(to, u) + Vector2(0, arch)
	var wob := 1.0 + sin(_wall * 30.0) * 0.06
	draw_circle(pos, r * 1.9 * wob, Color(edge.r, edge.g, edge.b, 0.25))
	draw_circle(pos, r * 1.25 * wob, Color(edge.r, edge.g, edge.b, 0.7))
	draw_circle(pos, r * 0.7, core)


func _draw_burst(b: Dictionary) -> void:
	var k := clampf((_wall - float(b["t"])) / 0.55, 0.0, 1.0)
	var p: Vector2 = b["pos"]
	var col: Color = b["color"]
	var rad := size.y * (0.05 + 0.0035 * float(b["p"])) * (0.4 + k * 1.6)
	draw_arc(p, rad, 0.0, TAU, 32, Color(col.r, col.g, col.b, 0.9 * (1.0 - k)), maxf(2.0, size.y * 0.012) * (1.0 - k * 0.7))
	draw_circle(p, rad * 0.55, Color(1.0, 1.0, 0.9, 0.55 * (1.0 - k)))
	if not reduced_effects:
		for i in 10:
			var ang := float(i) * TAU / 10.0 + 0.3
			var d := rad * (0.9 + 0.7 * k)
			draw_line(p + Vector2(cos(ang), sin(ang)) * rad * 0.7, p + Vector2(cos(ang), sin(ang)) * d, Color(col.r, col.g, col.b, 0.8 * (1.0 - k)), 2.0)


func _draw_floater(f: Dictionary) -> void:
	var k := clampf((_wall - float(f["t"])) / 1.1, 0.0, 1.0)
	var side := int(f["side"])
	var p := _foot(side) + Vector2(0, -_wiz_size() * (0.95 + 0.25 * float(f["rise"]) * k))
	var c: Color = f["color"]
	_text_centered(str(f["text"]), p, int(clampf(size.y * 0.07, 14.0, 44.0)), Color(c.r, c.g, c.b, 1.0 - k * k))


func _draw_hud() -> void:
	var fs := int(clampf(size.y * 0.052, 11.0, 24.0))
	var bw := size.x * 0.4
	var bh := maxf(size.y * 0.05, 12.0)
	var y := size.y * 0.085
	for side in 2:
		var x := size.x * 0.03 if side == 0 else size.x * 0.97 - bw
		var frac := clampf(float(_hp_shown[side]) / float(max_hp10), 0.0, 1.0)
		draw_rect(Rect2(x - 2, y - 2, bw + 4, bh + 4), BAR_BACK)
		var col := Color(0.35, 0.85, 0.5).lerp(Color(0.95, 0.25, 0.2), 1.0 - frac) if frac < 0.5 else Color(0.35, 0.85, 0.5)
		if side == 0:
			draw_rect(Rect2(x, y, bw * frac, bh), col)
		else:
			draw_rect(Rect2(x + bw * (1.0 - frac), y, bw * frac, bh), col)
		var nm := str(names[side])
		var font := ThemeDB.fallback_font
		var tw := font.get_string_size(nm, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		_text(nm, Vector2(x if side == 0 else x + bw - tw, y - 6.0), fs, Color(0.95, 0.95, 1.0))
		var hp_text := str(int(ceil(float(_hp_shown[side]) / 10.0)))
		var hw := font.get_string_size(hp_text, HORIZONTAL_ALIGNMENT_LEFT, -1, int(fs * 0.9)).x
		_text(hp_text, Vector2(x + bw * 0.5 - hw * 0.5, y + bh * 0.5 + fs * 0.32), int(fs * 0.9), Color(1, 1, 1, 0.95))
		var st := int(streak[side])
		var pip := bh * 0.55
		for i in streak_cap:
			var px := x + pip * 0.7 + float(i) * pip * 1.5 if side == 0 else x + bw - pip * 0.7 - float(i) * pip * 1.5
			var on := i < st
			draw_circle(Vector2(px, y + bh + pip * 1.2), pip * 0.5, Color(1.0, 0.82, 0.35, 0.95) if on else Color(1, 1, 1, 0.12))
		if st > streak_cap:
			_text("x%d" % st, Vector2(x + (pip * 8.2 if side == 0 else bw - pip * 8.2 - 30.0), y + bh + pip * 1.6), int(fs * 0.8), Color(1.0, 0.82, 0.35))
	if phrase_text != "":
		_text_centered(phrase_text, Vector2(size.x * 0.5, y + bh + fs * 1.3), int(fs * 0.85), Color(0.8, 0.85, 1.0, 0.85))


func _text(s: String, pos: Vector2, fs: int, col: Color) -> void:
	var font := ThemeDB.fallback_font
	draw_string_outline(font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, maxi(fs / 5, 3), Color(0, 0, 0, 0.9))
	draw_string(font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)


func _text_centered(s: String, centre: Vector2, fs: int, col: Color) -> void:
	var font := ThemeDB.fallback_font
	var w := font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	_text(s, Vector2(centre.x - w * 0.5, centre.y), fs, col)
