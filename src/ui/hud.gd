class_name Hud
extends Control
## Always-visible battle status, kept in the midfield band at the top so it never covers either base: both main
## bases' health, the player's producer availability, aircraft readiness and ammunition, repair credits, combo and
## accuracy. Labels and shapes, not colour alone.

var match_ref: Match
var view: BattleView  # the battlefield behind this overlay (defense mode draws points and routes on it)
var _font: Font


func _ready() -> void:
	_font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if match_ref == null:
		return
	var sim := match_ref.sim
	var judge := match_ref.judge
	if sim.defense:
		_draw_defense()
		return
	var cx := size.x * 0.5
	var band := Rect2(cx - 300, 0, 600, 58)
	draw_rect(band, Color(0, 0, 0, 0.45))
	_base_bar(Vector2(cx - 292, 6), 200, sim.main_base(0), "YOU", Color(0.35, 0.62, 1.0), false)
	_base_bar(Vector2(cx + 92, 6), 200, sim.main_base(1), "ENEMY", Color(1.0, 0.36, 0.30), true)
	var mid := "combo %d   %.0f%%" % [judge.combo, judge.accuracy() * 100.0]
	draw_string(_font, Vector2(cx - 80, 20), mid, HORIZONTAL_ALIGNMENT_CENTER, 160, 15, Color(1, 1, 1, 0.95))
	# producers
	var y := 40.0
	var x := cx - 292
	for item in [["factory", "FACTORY"], ["barracks", "BARRACKS"]]:
		var alive := sim.producer_alive(0, item[0])
		var col := Color(0.85, 1.0, 0.85) if alive else Color(1.0, 0.5, 0.45)
		draw_rect(Rect2(x, y - 8, 8, 8), col if alive else Color(0.3, 0.3, 0.3))
		if not alive:
			draw_line(Vector2(x, y - 8), Vector2(x + 8, y), col, 2.0)
			draw_line(Vector2(x + 8, y - 8), Vector2(x, y), col, 2.0)
		draw_string(_font, Vector2(x + 12, y), item[1] if alive else item[1] + " LOST", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, col)
		x += 110
	# air wing pips
	var pads := sim.pads_alive(0)
	draw_string(_font, Vector2(x, y), "AIR %d/%d" % [pads, sim.slots[0].size()], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.8, 0.9, 1.0))
	var px := x + 60
	for i in sim.slots[0].size():
		var s: Dictionary = sim.slots[0][i]
		var pad: BattleSim.Ent = sim.get_entity(int(s["pad"]))
		var a: BattleSim.Ent = sim.get_entity(int(s["aircraft"]))
		var box := Rect2(px + i * 30, y - 10, 27, 12)
		var pad_ok := pad != null and pad.alive
		draw_rect(box, Color(0.25, 0.35, 0.5, 0.8) if pad_ok else Color(0.2, 0.2, 0.2, 0.6))
		draw_rect(box, Color(1, 1, 1, 0.3), false, 1.0)
		if a != null and a.alive:
			var txt := ""
			match a.air:
				BattleSim.Air.READY:
					txt = "RDY"
				BattleSim.Air.SORTIE:
					txt = "OUT"
				BattleSim.Air.RETURNING, BattleSim.Air.LANDING:
					txt = "RTB"
				BattleSim.Air.REARMING:
					txt = "%d/%d" % [a.ammo, a.ammo_max]
				BattleSim.Air.WAITING:
					txt = "NOPAD"
			draw_string(_font, Vector2(box.position.x + 2, box.position.y + 10), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(1, 1, 1))
	draw_string(_font, Vector2(cx + 186, y), "army %d v %d" % [sim.count_alive(0, BattleSim.Kind.UNIT), sim.count_alive(1, BattleSim.Kind.UNIT)], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.7))


## Defense mode: objective health, time left, producers, the three defense points with their defenders and the
## telegraphed route of the next wave (entry marker and a line to its defense point).
func _draw_defense() -> void:
	var sim := match_ref.sim
	var judge := match_ref.judge
	var level := match_ref.level
	var cx := size.x * 0.5
	var now := float(match_ref.sim_ticks) * BattleSim.TICK_S
	draw_rect(Rect2(cx - 300, 0, 600, 58), Color(0, 0, 0, 0.45))
	for i in sim.objectives.size():
		var o: Dictionary = sim.objectives[i]
		var hp := sim.objective_hp(o["id"])
		var frac := float(hp) / float(maxi(sim.objective_max_hp(o["id"]), 1))
		var pos := Vector2(cx - 292, 6 + 18 * i)
		draw_rect(Rect2(pos, Vector2(230, 14)), Color(0, 0, 0, 0.55))
		draw_rect(Rect2(pos, Vector2(230 * frac, 14)), Color(0.35, 0.62, 1.0) if frac > 0.34 else Color(1.0, 0.45, 0.35))
		draw_rect(Rect2(pos, Vector2(230, 14)), Color(1, 1, 1, 0.5), false, 1.0)
		draw_string(_font, pos + Vector2(5, 11), "%s %d%%" % [str(o["id"]).replace("_", " ").to_upper(), int(round(frac * 100.0))], HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 1, 1))
	var left := maxf(level.duration_seconds() - now, 0.0)
	draw_string(_font, Vector2(cx - 40, 20), "%d:%02d  combo %d  %.0f%%" % [int(left) / 60, int(left) % 60, judge.combo, judge.accuracy() * 100.0], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1, 1, 1, 0.95))
	var x := cx - 292
	for item in [["factory", "FACTORY"], ["barracks", "BARRACKS"]]:
		var alive := sim.producer_alive(0, item[0])
		var col := Color(0.85, 1.0, 0.85) if alive else Color(1.0, 0.5, 0.45)
		draw_string(_font, Vector2(x, 50), item[1] if alive else item[1] + " LOST", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, col)
		x += 120
	draw_string(_font, Vector2(cx + 180, 50), "enemies %d" % sim.count_alive(1, BattleSim.Kind.UNIT), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.8))
	if view == null:
		return
	var counts := match_ref.defenders_per_point()
	for i in sim.defense_points.size():
		var p: Vector2 = view.to_px(sim.defense_points[i]["pos"]) - global_position + view.global_position
		draw_arc(p, 20.0, 0.0, TAU, 28, Color(0.7, 0.9, 1.0, 0.55), 2.0)
		draw_string(_font, p + Vector2(-5, 5), str(i + 1), HORIZONTAL_ALIGNMENT_CENTER, 12, 16, Color(0.8, 0.95, 1.0, 0.9))
		draw_string(_font, p + Vector2(-40, 36), "%d defenders" % counts[i], HORIZONTAL_ALIGNMENT_CENTER, 80, 10, Color(0.8, 0.95, 1.0, 0.8))
	var w := match_ref.upcoming_wave()
	if not w.is_empty() and float(w["in_s"]) <= 8.0 and sim.entries.has(w["entry"]):
		var pulse := 0.55 + 0.45 * sin(float(Time.get_ticks_msec()) / 120.0)
		var shift := view.global_position - global_position
		var win := view.window_px()
		win.position += shift
		var entry_px: Vector2 = view.to_px(sim.entries[w["entry"]]) + shift
		var via := entry_px
		for dp in sim.defense_points:
			if dp["id"] == w["via"]:
				via = view.to_px(dp["pos"]) + shift
		# the entry lies outside the picture: mark the edge it will come in at and draw the route from there
		var inner := Rect2(win.position + Vector2(26.0, 40.0), win.size - Vector2(52.0, 66.0))  # clear of the top bar
		var edge := Vector2(clampf(entry_px.x, inner.position.x, inner.end.x), clampf(entry_px.y, inner.position.y, inner.end.y))
		var dir := (entry_px - win.get_center()).normalized()
		var side := _direction_word(entry_px, win)
		draw_line(edge, via, Color(1.0, 0.4, 0.3, 0.6 * pulse), 3.0)
		var tip := edge + dir * 16.0
		var across := Vector2(-dir.y, dir.x) * 16.0
		draw_colored_polygon(PackedVector2Array([tip, edge - dir * 10.0 + across, edge - dir * 10.0 - across]), Color(1.0, 0.35, 0.3, 0.55 + 0.4 * pulse))
		draw_string(_font, Vector2(cx - 250, 124), "WAVE %d INCOMING FROM THE %s  %.0f s" % [int(w["number"]), side, float(w["in_s"])], HORIZONTAL_ALIGNMENT_CENTER, 500, 18, Color(1.0, 0.7, 0.55, pulse))


## LEFT, RIGHT or TOP (BOTTOM for completeness): the side of the window an entry lies beyond.
func _direction_word(entry_px: Vector2, win: Rect2) -> String:
	var d := entry_px - win.get_center()
	var nx := d.x / maxf(win.size.x, 1.0)
	var ny := d.y / maxf(win.size.y, 1.0)
	if absf(nx) >= absf(ny):
		return "RIGHT" if nx > 0.0 else "LEFT"
	return "BOTTOM" if ny > 0.0 else "TOP"


func _base_bar(pos: Vector2, width: float, base: BattleSim.Ent, label: String, col: Color, right: bool) -> void:
	var frac := 0.0 if base == null else float(base.hp) / maxf(1.0, float(base.max_hp))
	draw_rect(Rect2(pos, Vector2(width, 14)), Color(0, 0, 0, 0.55))
	var fill_x := pos.x if not right else pos.x + width * (1.0 - frac)
	draw_rect(Rect2(Vector2(fill_x, pos.y), Vector2(width * frac, 14)), col)
	draw_rect(Rect2(pos, Vector2(width, 14)), Color(1, 1, 1, 0.5), false, 1.0)
	var text := "%s %d%%" % [label, int(round(frac * 100.0))]
	draw_string(_font, Vector2(pos.x + 5, pos.y + 11), text, HORIZONTAL_ALIGNMENT_RIGHT if right else HORIZONTAL_ALIGNMENT_LEFT, width - 10, 11, Color(1, 1, 1))
