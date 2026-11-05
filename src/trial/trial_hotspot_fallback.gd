class_name TrialHotspotFallback
extends Control
## THIN FALLBACK, to be deleted when the engine workstream's hotspot_view (src/run/hotspot_view.gd) is merged: TrialScene feeds its hotspots to this node, which draws them as
## lights in the room (no text, no numbers) and turns a tap into the index of the hotspot hit. A hotspot is a ring of light on the floor under its anchor plus a glow on the anchor
## itself; the default one is brighter and breathes on the beat, the selected one is gold with a second ring, an available one is cool and dim, and a committed one flashes for a beat.
## A hotspot out of sight (behind the camera) is a chevron at the screen edge on the side it lies, so every hotspot can be tapped without turning. Targets are at least MIN_PX
## across; a tap picks the nearest centre among the targets it falls in.

signal tapped(index: int)

const MIN_PX := 72.0
const MAX_HALF := 110.0

var items: Array = []  # [{index: choice index in the engine's list, pos: Vector3 anchor, ground: float, radius_m, kind, default: bool, selected: bool}]
var pose_fn: Callable  # () -> {cam: Vector3, yaw, pitch}
var now_fn: Callable  # () -> song time
var beat_s := 60.0 / 174.0
var fade_from := 0.0  # song time the window opened (the lights come up over one beat)
var flash: Dictionary = {}  # {item, t0}: the committed hotspot, flashing for a beat after the commit


func _process(_d: float) -> void:
	if visible:
		queue_redraw()


## Where an item is on screen now: {visible, screen, half (the target's half size in px), scale} or, out of sight, {visible: false, screen (the edge marker), half}.
func place(it: Dictionary, pose: Dictionary) -> Dictionary:
	var p := StoryProjector.project(it["pos"], pose, size)
	var r := float(it["radius_m"])
	if p["visible"] and float(p["depth"]) > 0.4:
		var half := clampf(r * float(p["scale"]), MIN_PX * 0.5, MAX_HALF)
		return {"visible": true, "screen": p["screen"], "half": half, "scale": float(p["scale"])}
	var cam: Vector3 = pose["cam"]
	var pos: Vector3 = it["pos"]
	var d := Vector2(pos.x - cam.x, pos.z - cam.z)
	var side := 1.0 if d.dot(StoryProjector.right(float(pose["yaw"]))) >= 0.0 else -1.0
	var x := size.x - MIN_PX * 0.6 if side > 0.0 else MIN_PX * 0.6
	var step := clampf((size.y - 100.0) / 3.0, 40.0, MIN_PX * 1.05)
	return {"visible": false, "screen": Vector2(x, 50.0 + float(int(it["index"])) * step), "half": MIN_PX * 0.5, "scale": 0.0, "side": side}


## The target rectangles now, one per item (what a tap must fall in).
func rects() -> Array:
	var out: Array = []
	var pose: Dictionary = pose_fn.call() if pose_fn.is_valid() else {}
	if pose.is_empty():
		return out
	for it in items:
		var pl := place(it, pose)
		var c: Vector2 = pl["screen"]
		var h := float(pl["half"])
		out.append(Rect2(c - Vector2(h, h), Vector2(h, h) * 2.0))
	return out


## The index (an item's `index`) of the hotspot a tap at `pos` (this control's own coordinates) hits, or -1.
func hit(pos: Vector2) -> int:
	var best := -1
	var best_d := INF
	var rs := rects()
	for k in rs.size():
		var r: Rect2 = rs[k]
		if r.has_point(pos):
			var dd := pos.distance_to(r.get_center())
			if dd < best_d:
				best_d = dd
				best = int((items[k] as Dictionary)["index"])
	return best


func tap_at(pos: Vector2) -> int:
	var i := hit(pos)
	if i >= 0:
		tapped.emit(i)
	return i


## A real press through the hit test: the centre of hotspot `index`'s target (a script's or a test's finger). Returns the index hit (-1 when it cannot be reached).
func tap_index(index: int) -> int:
	for k in items.size():
		if int((items[k] as Dictionary)["index"]) == index:
			var rs := rects()
			if k < rs.size():
				return tap_at((rs[k] as Rect2).get_center())
	return -1


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT and not items.is_empty():
		if tap_at((event as InputEventMouseButton).position) >= 0:
			accept_event()


func flashing(t: float) -> bool:
	return not flash.is_empty() and t < float(flash["t0"]) + beat_s * 1.0


func _draw() -> void:
	if not pose_fn.is_valid():
		return
	var pose: Dictionary = pose_fn.call()
	if pose.is_empty():
		return
	var t := float(now_fn.call()) if now_fn.is_valid() else 0.0
	if not flash.is_empty():
		_draw_flash(pose, t)
	if items.is_empty():
		return
	var up := clampf((t - fade_from) / beat_s, 0.0, 1.0)
	var beat_phase := fposmod(t / beat_s, 1.0)
	for it in items:
		var pl := place(it, pose)
		var dflt := bool(it["default"])
		var sel := bool(it["selected"])
		var col := Color(0.55, 0.8, 1.0)
		var a := 0.45
		if dflt:
			col = Color(1.0, 0.82, 0.45)
			a = 0.9
		if sel:
			col = Color(1.0, 0.95, 0.55)
			a = 1.0
		a *= up
		var pulse := 0.75 + 0.25 * (1.0 - beat_phase) if (dflt or sel) else 0.8 + 0.2 * sin(t * 2.0)
		var c: Vector2 = pl["screen"]
		var h := float(pl["half"])
		if bool(pl["visible"]):
			var ground := StoryProjector.project(Vector3((it["pos"] as Vector3).x, float(it["ground"]), (it["pos"] as Vector3).z), pose, size)
			var gc: Vector2 = ground["screen"] if bool(ground["visible"]) else c + Vector2(0, h)
			var rw := h * 1.1
			_ring(gc, rw, rw * 0.32, Color(col.r, col.g, col.b, a * pulse), 3.0 if (dflt or sel) else 2.0)
			if sel:
				_ring(gc, rw * 1.35, rw * 0.43, Color(col.r, col.g, col.b, a * 0.6), 2.0)
			draw_circle(c, h * 0.55 * pulse, Color(col.r, col.g, col.b, a * 0.2))
			draw_circle(c, h * 0.28 * pulse, Color(col.r, col.g, col.b, a * 0.35))
			if dflt or sel:  # corner ticks round the target: the default or chosen light is easy to find at a glance
				var tick := h * 0.3
				for sx in [-1.0, 1.0]:
					for sy in [-1.0, 1.0]:
						var cc := c + Vector2(sx * h, sy * h)
						draw_line(cc, cc - Vector2(sx * tick, 0.0), Color(col.r, col.g, col.b, a), 3.0)
						draw_line(cc, cc - Vector2(0.0, sy * tick), Color(col.r, col.g, col.b, a), 3.0)
		else:
			var side := float(pl["side"])
			var pts := PackedVector2Array([c + Vector2(side * 16.0, 0.0), c + Vector2(-side * 12.0, -22.0), c + Vector2(-side * 12.0, 22.0)])
			draw_colored_polygon(pts, Color(col.r, col.g, col.b, a * pulse))


func _ring(c: Vector2, rx: float, ry: float, col: Color, w: float) -> void:
	var pts := PackedVector2Array()
	for k in 33:
		var a := TAU * float(k) / 32.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	draw_polyline(pts, col, w, true)


func _draw_flash(pose: Dictionary, t: float) -> void:
	var k := clampf((t - float(flash["t0"])) / beat_s, 0.0, 1.0)
	if k >= 1.0:
		return
	var pl := place(flash["item"], pose)
	var c: Vector2 = pl["screen"]
	var h := float(pl["half"])
	draw_circle(c, h * (0.6 + k * 1.6), Color(1.0, 0.95, 0.7, (1.0 - k) * 0.5))
	draw_arc(c, h * (0.8 + k * 1.2), 0.0, TAU, 40, Color(1.0, 0.95, 0.7, 1.0 - k), 3.0, true)
