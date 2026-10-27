class_name Hud
extends Control
## Always-visible battle status, kept in the midfield band at the top so it never covers either base: both main
## bases' health, the player's producer availability, aircraft readiness and ammunition, repair credits, combo and
## accuracy. Labels and shapes, not colour alone.

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


func _base_bar(pos: Vector2, width: float, base: BattleSim.Ent, label: String, col: Color, right: bool) -> void:
	var frac := 0.0 if base == null else float(base.hp) / maxf(1.0, float(base.max_hp))
	draw_rect(Rect2(pos, Vector2(width, 14)), Color(0, 0, 0, 0.55))
	var fill_x := pos.x if not right else pos.x + width * (1.0 - frac)
	draw_rect(Rect2(Vector2(fill_x, pos.y), Vector2(width * frac, 14)), col)
	draw_rect(Rect2(pos, Vector2(width, 14)), Color(1, 1, 1, 0.5), false, 1.0)
	var text := "%s %d%%" % [label, int(round(frac * 100.0))]
	draw_string(_font, Vector2(pos.x + 5, pos.y + 11), text, HORIZONTAL_ALIGNMENT_RIGHT if right else HORIZONTAL_ALIGNMENT_LEFT, width - 10, 11, Color(1, 1, 1))
