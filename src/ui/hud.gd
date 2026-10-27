class_name Hud
extends Control
## Always-visible battle status: both main bases' health, the player's producer availability, aircraft readiness
## and ammunition, repair credits, combo and accuracy. Labels and shapes, not colour alone.

var match_ref: Match
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
	var w := size.x
	# main base bars
	_base_bar(Vector2(12, 10), 300, sim.main_base(0), "YOUR BASE", Color(0.35, 0.62, 1.0), false)
	_base_bar(Vector2(w - 312, 10), 300, sim.main_base(1), "ENEMY BASE", Color(1.0, 0.36, 0.30), true)
	# producers
	var y := 44.0
	var x := 12.0
	for item in [["factory", "FACTORY", "tanks"], ["barracks", "BARRACKS", "infantry"]]:
		var alive := sim.producer_alive(0, item[0])
		var label: String = "%s %s" % [item[1], "ready" if alive else "DESTROYED"]
		var col := Color(0.85, 1.0, 0.85) if alive else Color(1.0, 0.5, 0.45)
		draw_rect(Rect2(x, y, 10, 10), col if alive else Color(0.3, 0.3, 0.3))
		if not alive:
			draw_line(Vector2(x, y), Vector2(x + 10, y + 10), col, 2.0)
			draw_line(Vector2(x + 10, y), Vector2(x, y + 10), col, 2.0)
		draw_string(_font, Vector2(x + 16, y + 10), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, col)
		y += 18
	# air wing
	var pads := sim.pads_alive(0)
	var air_label := "AIR  pads %d/%d" % [pads, sim.slots[0].size()]
	draw_string(_font, Vector2(x, y + 10), air_label, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.8, 0.9, 1.0))
	var px := x + 120
	for i in sim.slots[0].size():
		var s: Dictionary = sim.slots[0][i]
		var pad: BattleSim.Ent = sim.get_entity(s["pad"])
		var a: BattleSim.Ent = sim.get_entity(s["aircraft"])
		var box := Rect2(px + i * 30, y, 26, 12)
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
			draw_string(_font, Vector2(box.position.x + 1, box.position.y + 10), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(1, 1, 1))
	y += 18
	draw_string(_font, Vector2(x, y + 10), "repair credits %d" % sim.credits[0], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.6))
	# combo and accuracy, centre top
	var mid := "combo %d   accuracy %.0f%%" % [judge.combo, judge.accuracy() * 100.0]
	draw_string(_font, Vector2(w * 0.5 - 150, 24), mid, HORIZONTAL_ALIGNMENT_CENTER, 300, 18, Color(1, 1, 1, 0.9))
	# enemy army size (information, not control)
	var enemy_units := sim.count_alive(1, BattleSim.Kind.UNIT)
	var my_units := sim.count_alive(0, BattleSim.Kind.UNIT)
	draw_string(_font, Vector2(w * 0.5 - 150, 44), "army %d  vs  %d" % [my_units, enemy_units], HORIZONTAL_ALIGNMENT_CENTER, 300, 14, Color(1, 1, 1, 0.6))


func _base_bar(pos: Vector2, width: float, base: BattleSim.Ent, label: String, col: Color, right: bool) -> void:
	var frac := 0.0 if base == null else float(base.hp) / maxf(1.0, float(base.max_hp))
	draw_rect(Rect2(pos, Vector2(width, 16)), Color(0, 0, 0, 0.55))
	var fill_x := pos.x if not right else pos.x + width * (1.0 - frac)
	draw_rect(Rect2(Vector2(fill_x, pos.y), Vector2(width * frac, 16)), col)
	draw_rect(Rect2(pos, Vector2(width, 16)), Color(1, 1, 1, 0.5), false, 1.0)
	var text := "%s  %d%%" % [label, int(round(frac * 100.0))]
	draw_string(_font, Vector2(pos.x + 6, pos.y + 13), text, HORIZONTAL_ALIGNMENT_RIGHT if right else HORIZONTAL_ALIGNMENT_LEFT, width - 12, 13, Color(1, 1, 1))
