class_name HotspotView
extends Control
## The hotspots drawn in the world and hit-tested on screen. It lives inside the low-res viewport above the crowd (StoryLowRes.add_overlay), so its light pixelates with the picture; the
## input is taken by the run scene on the stage area only (the pads are elsewhere) and resolved with the same pure `layout` and `hit` below at screen resolution.
##
## One visual language in every world and in the Bassment (docs/VISUAL_RHYTHM_ADVENTURE_HANDOVER.md "Look"), no text, no arrows, no widgets; every value is a function of song time:
## AVAILABLE: a pool of light on the floor under the anchor (added to the picture like real light), a thick ring with a dark pixel outline, a ripple that leaves the ring on every beat, a soft
## shaft rising from the pool with motes riding it, and a glow on the thing itself. `look.available` adds its character: a door ajar (a lit slit standing in the doorway, its light spilling toward
## the player), a beckoning figure (the crowd's own wave, a taller shaft), a slow pulse (a harder beat), a flicker, a crack in the floor. The default is brighter, with a second ring inside.
## SELECTED: the ring goes white-hot and thumps on every beat, four motes circle it once a bar, the pool and the shaft brighten and the glow lifts; the other hotspots dim so the pick reads by contrast.
## COMMITTED: a white flash bursting outward (FLASH_S), then the pool settles to a steady warm light that fades (SETTLE_S).
## An anchor out of sight (behind the camera, off to a side) is a beacon at the edge on the side it lies: light leaking in from beyond the frame, a half-sun at the border and the same ring,
## ripple and core as a hotspot in view, pulsing on the beat; still touchable: free look is never needed.

const SEGMENTS := 24
const EDGE_MARGIN := 0.07  # of the view's short side
const LIFT_M := 0.28
const FLASH_S := 0.3
const SETTLE_S := 0.9
const SHAFT_M := 2.4  # how high the shaft of light rises above the floor
const DIM_OTHERS := 0.45  # the available hotspots' strength while another one is selected
const GLOW_MAX := 0.11  # the glow on a thing never grows past this share of the view's height (a hotspot at the player's elbow)
const SHAFT_MAX_W := 0.025  # nor a shaft past this share of its width, each side
const OUTLINE := Color(0.02, 0.01, 0.04, 0.75)  # the dark pixel edge that keeps a ring readable on a bright floor

var items_fn: Callable  # () -> Array of {hotspot: Dictionary, state: "available" | "selected" | "committed", t_state: float (song time the state began)}
var pose_fn: Callable  # () -> {cam: Vector3, yaw, pitch} (empty: nothing to draw)
var now_fn: Callable  # () -> song time
var stage: StoryStage
var beat_s := 60.0 / 174.0
var tint := Color(1.0, 0.85, 0.5)  # the chapter palette's accent as light (see `light_tint`)
var reduced := false
var high_contrast := false
var glow_tex: Texture2D = null

var _beckoning: Dictionary = {}  # actor id -> true while the crowd was told to wave at the player
var _light: Control  # the additive pass (pools, shafts, glows, edge leaks), drawn behind the rings
var _lay: Array = []  # this frame's layout, shared by both passes
var _t := 0.0
var _any_sel := false
# the camera of this frame, unpacked once, so the rings are projected without building a dictionary per point
var _cam := Vector3.ZERO
var _fw := Vector2.ZERO
var _rt := Vector2.ZERO
var _f := 1.0
var _cp := 1.0
var _sp := 0.0
var _ring := PackedVector2Array()
var _quad := PackedVector2Array()
var _quad_c := PackedColorArray()


## The chapter's warm accent as hotspot light: its hue kept, the saturation held in a band and the value at full, so every world's lights are equally bright and still in its palette.
static func light_tint(accent: Color) -> Color:
	return Color.from_hsv(accent.h, clampf(accent.s, 0.35, 0.6), 1.0)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 5
	_ring.resize(SEGMENTS + 1)
	_quad.resize(4)
	_quad_c.resize(4)
	_light = Control.new()
	_light.name = "Light"
	_light.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_light.show_behind_parent = true
	_light.set_anchors_preset(Control.PRESET_FULL_RECT)
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_light.material = mat
	_light.draw.connect(_draw_light)
	add_child(_light)


func _process(_d: float) -> void:
	if not visible:
		return
	var had := not _lay.is_empty()
	_lay = []
	if items_fn.is_valid() and pose_fn.is_valid() and stage != null and stage.map != null:
		var pose: Dictionary = pose_fn.call()
		if not pose.is_empty():
			_t = float(now_fn.call()) if now_fn.is_valid() else 0.0
			var items: Array = items_fn.call()
			_manage_beckons(items, _t)
			if not items.is_empty():
				_set_camera(pose)
				_lay = layout(items, stage.map, stage.crowds, pose, size)
				_lay.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["depth"]) > float(b["depth"]))  # far first
				_any_sel = false
				for e in _lay:
					if str(e["state"]) == "selected":
						_any_sel = true
	if had or not _lay.is_empty():  # nothing on show: nothing to redraw
		queue_redraw()
		_light.queue_redraw()


# --- pure projection and hit testing -------------------------------------------------------------------------------------------

## Where an anchor stands in the world: {ok, pos: Vector3 (the point the glow and the touch centre on), ground: float (the floor under it), actor: bool}. `crowds`: room id -> StoryCrowd.
static func resolve(anchor: Dictionary, map: StoryMap, crowds: Dictionary) -> Dictionary:
	if map == null:
		return {"ok": false}
	var key := str(anchor.keys()[0]) if not anchor.is_empty() else ""
	match key:
		"thing":
			for t in map.things:
				if str(t["id"]) == str(anchor["thing"]):
					var fl := float(map.sector(str(t["sector"])).get("floor", 0.0))
					var at: Vector2 = t["at"]
					return {"ok": true, "pos": Vector3(at.x, fl + float(t.get("y", float(t.get("size", 1.0)) * 0.5)), at.y), "ground": fl, "actor": false}
			for l in map.lights:
				if str(l["id"]) == str(anchor["thing"]):
					var fl2 := float(map.sector(str(l["sector"])).get("floor", 0.0))
					var at2: Vector2 = l["at"]
					return {"ok": true, "pos": Vector3(at2.x, fl2 + float(l["y"]), at2.y), "ground": fl2, "actor": false}
		"waypoint":
			if map.has_waypoint(str(anchor["waypoint"])):
				var w: Dictionary = map.waypoint(str(anchor["waypoint"]))
				var fl3 := float(map.sector(str(w["sector"])).get("floor", 0.0))
				var at3: Vector2 = w["at"]
				return {"ok": true, "pos": Vector3(at3.x, fl3 + 1.0, at3.y), "ground": fl3, "actor": false}
		"actor":
			for rid in crowds:
				var c: StoryCrowd = crowds[rid]
				if c.actors.has(str(anchor["actor"])):
					var a: Dictionary = c.actors[str(anchor["actor"])]
					var p: Vector2 = a["pos"]
					var fl4 := float(map.sector(str(a.get("sec", ""))).get("floor", 0.0))
					return {"ok": true, "pos": Vector3(p.x, fl4 + 1.0, p.y), "ground": fl4, "actor": true, "room": rid}
		"pos":
			var v: Array = anchor["pos"]
			var sid := map.sector_at(Vector2(float(v[0]), float(v[2])))
			var fl5 := float(map.sector(sid).get("floor", 0.0))
			return {"ok": true, "pos": Vector3(float(v[0]), fl5 + float(v[1]), float(v[2])), "ground": fl5, "actor": false}
	return {"ok": false}


## Screen placement of every entry ({hotspot, state}) for a camera pose in a view of `view` pixels: [{id, hotspot, state, centre, ground, scale, depth, radius_px, edge, ok}]. A hotspot whose
## anchor is out of sight is placed at the edge of the picture on the side it lies (edge: true), so it can still be seen and touched. The touch radius is the projected radius_m, never under half of min_px.
static func layout(entries: Array, map: StoryMap, crowds: Dictionary, pose: Dictionary, view: Vector2) -> Array:
	var out: Array = []
	if pose.is_empty() or view.x <= 1.0:
		return out
	var margin := minf(view.x, view.y) * EDGE_MARGIN
	var edge_n := {}
	for e in entries:
		var h: Dictionary = e["hotspot"]
		var r := resolve(h["anchor"], map, crowds)
		if not bool(r["ok"]):
			continue
		var p: Vector3 = r["pos"]
		var pc := StoryProjector.project(p, pose, view)
		var pg := StoryProjector.project(Vector3(p.x, float(r["ground"]), p.z), pose, view)
		var min_r := float(h["min_px"]) * 0.5
		var entry := {"id": str(h["id"]), "hotspot": h, "state": str(e["state"]), "t_state": float(e.get("t_state", 0.0)), "world": p, "ground_y": float(r["ground"]), "actor": bool(r["actor"]), "edge": false, "ok": true}
		var on_screen: bool = bool(pc["visible"]) and float(pc["depth"]) > 0.4 and pc["screen"].x >= 0.0 and pc["screen"].x <= view.x and pc["screen"].y >= 0.0 and pc["screen"].y <= view.y
		if on_screen:
			var sc := float(pc["scale"])
			var rad := minf(maxf(float(h["radius_m"]) * sc, min_r), minf(view.x, view.y) * 0.5)
			var sp: Vector2 = pc["screen"]
			entry["centre"] = Vector2(clampf(sp.x, rad, view.x - rad), clampf(sp.y, rad, view.y - rad))  # the whole touch target stays inside the stage view, so never over the pads below it
			entry["ground"] = pg["screen"] if bool(pg["visible"]) else pc["screen"]
			entry["scale"] = sc
			entry["depth"] = float(pc["depth"])
			entry["radius_px"] = rad
		else:  # out of sight: a beacon at the edge on the side it lies
			var cam: Vector3 = pose["cam"]
			var d := Vector2(p.x - cam.x, p.z - cam.z)
			var side := 1.0 if d.dot(StoryProjector.right(float(pose["yaw"]))) >= 0.0 else -1.0
			var n_side := int(edge_n.get(side, 0))  # beacons on one side stack down the edge, never on top of each other
			edge_n[side] = n_side + 1
			var y := clampf(view.y * 0.3 + float(n_side) * min_r * 2.2, min_r, view.y - min_r)
			var x := view.x - margin - min_r if side > 0.0 else margin + min_r
			entry["centre"] = Vector2(x, y)
			entry["ground"] = Vector2(x, y + min_r * 0.6)
			entry["scale"] = view.y * 0.2
			entry["depth"] = 99.0
			entry["radius_px"] = min_r
			entry["edge"] = true
		out.append(entry)
	return out


## The id of the entry a tap at `point` hits: the nearest centre among those within their own radius (ties: the earlier in the list). "" when none.
static func hit(layout_entries: Array, point: Vector2) -> String:
	var best := ""
	var best_d := INF
	for e in layout_entries:
		var d := (e["centre"] as Vector2).distance_to(point)
		if d <= float(e["radius_px"]) and d < best_d - 1.0e-6:
			best_d = d
			best = str(e["id"])
	return best


# --- drawing -----------------------------------------------------------------------------------------------------------------

func _manage_beckons(items: Array, t: float) -> void:
	var want := {}
	for e in items:
		var h: Dictionary = e["hotspot"]
		var an: Dictionary = h["anchor"]
		if an.has("actor") and str(e["state"]) != "committed":
			want[str(an["actor"])] = true
	for id in want:
		if not _beckoning.has(id):
			_beckoning[id] = true
			for rid in stage.crowds:
				(stage.crowds[rid] as StoryCrowd).beckon(str(id), t, t + 30.0)
	for id in _beckoning.keys():
		if not want.has(id):
			_beckoning.erase(id)
			for rid in stage.crowds:
				(stage.crowds[rid] as StoryCrowd).stand_down(str(id))


func _set_camera(pose: Dictionary) -> void:
	_cam = pose["cam"]
	var yaw := float(pose["yaw"])
	_fw = StoryProjector.forward(yaw)
	_rt = StoryProjector.right(yaw)
	_f = StoryProjector.focal_px(size.y)
	var pr := deg_to_rad(float(pose.get("pitch", 0.0)))
	_cp = cos(pr)
	_sp = sin(pr)


## StoryProjector.project for this frame's camera without the dictionary: (screen x, screen y, depth); depth below NEAR is behind the camera.
func _pj(x: float, y: float, z: float) -> Vector3:
	var dx := x - _cam.x
	var dz := z - _cam.z
	var along := dx * _fw.x + dz * _fw.y
	var up := y - _cam.y
	var depth := along * _cp + up * _sp
	if depth < StoryProjector.NEAR:
		return Vector3(0.0, 0.0, -1.0)
	var cy := up * _cp - along * _sp
	return Vector3(size.x * 0.5 + _f * (dx * _rt.x + dz * _rt.y) / depth, size.y * 0.5 - _f * cy / depth, depth)


## Fills `_ring` with a circle of radius r (metres) on the floor at height gy around `world`; false when part of it is behind the camera.
func _fill_ring(world: Vector3, gy: float, r: float) -> bool:
	for i in SEGMENTS + 1:
		var a := TAU * float(i) / float(SEGMENTS)
		var p := _pj(world.x + cos(a) * r, gy, world.z + sin(a) * r)
		if p.z < StoryProjector.NEAR:
			return false
		_ring[i] = Vector2(p.x, p.y)
	return true


## 1 on each beat falling to 0 before the next (a kick), steady in reduced motion.
func _thump() -> float:
	if reduced:
		return 0.35
	var bp := fposmod(_t / beat_s, 1.0)
	return pow(1.0 - bp, 3.0)


func _beat_phase() -> float:
	return 0.0 if reduced else fposmod(_t / beat_s, 1.0)


func _colours() -> Array:  # [base, hot]
	var base := Color(1.0, 1.0, 0.4) if high_contrast else tint
	return [base, base.lerp(Color(1, 1, 1), 0.55)]


## How strongly an entry is lit: dimmed while another hotspot is selected, and its flicker.
func _strength(e: Dictionary) -> float:
	var k := DIM_OTHERS if (_any_sel and str(e["state"]) == "available") else 1.0
	if str((e["hotspot"]["look"] as Dictionary)["available"]) == "flicker" and str(e["state"]) == "available" and not reduced:
		k *= 0.45 + 0.55 * float((int(floor(_t * 14.0)) * 7919) % 5) / 4.0
	return k


func _glow(c: Vector2, r: float, col: Color, a: float) -> void:
	var ci := _light if _light != null else self
	if glow_tex != null:
		var s := r * 2.6
		ci.draw_texture_rect(glow_tex, Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s)), false, Color(col.r, col.g, col.b, clampf(a, 0.0, 1.0)))
		return
	for k in 4:
		ci.draw_circle(c, r * (1.0 - float(k) * 0.22), Color(col.r, col.g, col.b, a * 0.28))


## A soft vertical band (a shaft of light, a door's slit): bottom corners b0 b1 at alpha a_bottom, top corners t1 t0 at alpha a_top.
func _band(ci: CanvasItem, b0: Vector2, b1: Vector2, t1: Vector2, t0: Vector2, col: Color, a_bottom: float, a_top: float) -> void:
	_quad[0] = b0
	_quad[1] = b1
	_quad[2] = t1
	_quad[3] = t0
	_quad_c[0] = Color(col.r, col.g, col.b, a_bottom)
	_quad_c[1] = _quad_c[0]
	_quad_c[2] = Color(col.r, col.g, col.b, a_top)
	_quad_c[3] = _quad_c[2]
	ci.draw_polygon(_quad, _quad_c)


func _mote(ci: CanvasItem, p: Vector2, s: float, col: Color) -> void:
	ci.draw_rect(Rect2(Vector2(floorf(p.x - s * 0.5), floorf(p.y - s * 0.5)), Vector2(s, s)), col)


# The rings, motes and edges: the crisp half, drawn over the light.
func _draw() -> void:
	if _lay.is_empty():
		return
	var cols := _colours()
	for e in _lay:
		if bool(e["edge"]):
			_draw_edge(e, cols[0], cols[1])
		else:
			_draw_marks(e, cols[0], cols[1])


# The light: pools on the floor, shafts, glows, the door's slit and the edge leaks, added to the picture.
func _draw_light() -> void:
	if _lay.is_empty():
		return
	var cols := _colours()
	for e in _lay:
		if bool(e["edge"]):
			_light_edge(e, cols[0], cols[1])
		else:
			_light_entry(e, cols[0], cols[1])


func _light_entry(e: Dictionary, base: Color, hot: Color) -> void:
	var h: Dictionary = e["hotspot"]
	var state := str(e["state"])
	var look := str((h["look"] as Dictionary)["available"])
	var is_default := bool(h["default"])
	var world: Vector3 = e["world"]
	var gy := float(e["ground_y"])
	var r_m := float(h["radius_m"])
	var sc := float(e["scale"])
	var c: Vector2 = e["centre"]
	var u := maxf(_t - float(e["t_state"]), 0.0)
	var th := _thump()
	var k := _strength(e)
	if look == "pulse" and state == "available":
		th = minf(th * 1.5, 1.0)
	var L := _light
	var pool_a := 0.0
	var pool_col := base
	var shaft_a := 0.0
	match state:
		"available":
			pool_a = (0.2 + 0.16 * th + (0.1 if is_default else 0.0)) * k
			shaft_a = (0.22 + 0.12 * th + (0.08 if is_default else 0.0)) * k
			_glow(c, minf(r_m * sc * 0.6, size.y * GLOW_MAX), base, (0.32 + 0.28 * th + (0.12 if is_default else 0.0)) * k)
		"selected":
			pool_a = 0.42 + 0.22 * th
			pool_col = hot
			shaft_a = 0.5 + 0.2 * th
			var lift := minf(u / 0.25, 1.0)
			lift = lift * lift * (3.0 - 2.0 * lift) * LIFT_M * sc
			_glow(c + Vector2(0.0, -lift), minf(r_m * sc * 0.8, size.y * GLOW_MAX * 1.3), hot, 0.75 + 0.2 * th)
		"committed":
			var fk := clampf(u / FLASH_S, 0.0, 1.0)
			var settle := 1.0 - _smooth01((u - FLASH_S) / SETTLE_S)
			pool_a = 0.95 * (1.0 - fk) + 0.4 * settle * fk
			pool_col = Color(1, 1, 1).lerp(hot, fk)
			shaft_a = 0.6 * settle
			_glow(c + Vector2(0.0, -LIFT_M * sc), minf(r_m * sc, size.y * GLOW_MAX * 1.5) * (0.9 + 1.8 * fk), Color(1, 1, 1), 0.95 * (1.0 - fk))
			_glow(c, minf(r_m * sc * 0.7, size.y * GLOW_MAX), hot, 0.5 * settle * fk)
	if pool_a > 0.005 and _fill_ring(world, gy, r_m * 1.05):  # the pool: light on the floor, brighter at its heart
		L.draw_colored_polygon(_ring, Color(pool_col.r, pool_col.g, pool_col.b, pool_a))
		if _fill_ring(world, gy, r_m * 0.55):
			L.draw_colored_polygon(_ring, Color(pool_col.r, pool_col.g, pool_col.b, pool_a * 0.8))
	var g := _pj(world.x, gy, world.z)
	if g.z < StoryProjector.NEAR:
		return
	var gs := Vector2(g.x, g.y)
	shaft_a *= clampf((g.z - 1.0) / 3.0, 0.35, 1.0)  # a shaft at the player's elbow is mostly the pool
	var tall := SHAFT_M * (1.35 if (look == "beckon" or bool(e["actor"])) else 1.0)
	var top3 := _pj(world.x, gy + tall, world.z)
	if shaft_a > 0.005 and top3.z >= StoryProjector.NEAR:  # the shaft: a soft column rising from the pool, fading upward
		var top := Vector2(top3.x, top3.y)
		var hw := clampf(r_m * 0.42 * sc, 2.0, size.x * SHAFT_MAX_W)  # a near one stays a shaft, not a wash over the picture
		var tw := hw * 0.55
		_band(L, gs + Vector2(-hw, 0.0), gs + Vector2(hw, 0.0), top + Vector2(tw, 0.0), top + Vector2(-tw, 0.0), pool_col, shaft_a, 0.0)
		if not reduced:  # motes riding up the shaft, one every two beats
			for i in 3:
				var ph := fposmod(_t / (beat_s * 2.0) + float(i) / 3.0, 1.0)
				var p := gs.lerp(top, ph * 0.85) + Vector2(sin((_t / beat_s + float(i) * 1.7) * 1.3) * hw * 0.6, 0.0)
				_mote(L, p, 2.0, Color(hot.r, hot.g, hot.b, (1.0 - ph) * 0.9 * minf(shaft_a * 2.5, 1.0)))
	if look == "open" and state != "committed":  # a door ajar: a lit slit standing in the doorway, its light spilling across the floor toward the player
		var ajar := (0.42 if is_default else 0.3) * r_m
		var rv := _rt
		var b0 := _pj(world.x - rv.x * ajar, gy, world.z - rv.y * ajar)
		var b1 := _pj(world.x + rv.x * ajar, gy, world.z + rv.y * ajar)
		var t0 := _pj(world.x - rv.x * ajar * 0.8, gy + 2.1, world.z - rv.y * ajar * 0.8)
		var t1 := _pj(world.x + rv.x * ajar * 0.8, gy + 2.1, world.z + rv.y * ajar * 0.8)
		var s_far := 1.6  # the spill reaches this far toward the camera and widens as it comes
		var toward := Vector2(_cam.x - world.x, _cam.z - world.z)
		var dist := toward.length()
		if dist > 0.01 and b0.z >= StoryProjector.NEAR and b1.z >= StoryProjector.NEAR and t0.z >= StoryProjector.NEAR and t1.z >= StoryProjector.NEAR:
			var slit_a := ((0.38 + 0.2 * th) * k if state == "available" else 0.6) * clampf((g.z - 1.0) / 3.0, 0.2, 1.0)  # fainter at the player's elbow, where it would wash the picture
			var slit_c := base.lerp(hot, 0.5)
			_band(L, Vector2(b0.x, b0.y), Vector2(b1.x, b1.y), Vector2(t1.x, t1.y), Vector2(t0.x, t0.y), slit_c, slit_a, slit_a * 0.6)
			var dn := toward / dist * minf(s_far, dist * 0.6)
			var w2 := ajar * 2.2
			var n0 := _pj(world.x + dn.x - rv.x * w2, gy, world.z + dn.y - rv.y * w2)
			var n1 := _pj(world.x + dn.x + rv.x * w2, gy, world.z + dn.y + rv.y * w2)
			if n0.z >= StoryProjector.NEAR and n1.z >= StoryProjector.NEAR:
				_band(L, Vector2(b0.x, b0.y), Vector2(b1.x, b1.y), Vector2(n1.x, n1.y), Vector2(n0.x, n0.y), slit_c, slit_a * 0.7, 0.0)


func _draw_marks(e: Dictionary, base: Color, hot: Color) -> void:
	var h: Dictionary = e["hotspot"]
	var state := str(e["state"])
	var look := str((h["look"] as Dictionary)["available"])
	var is_default := bool(h["default"])
	var world: Vector3 = e["world"]
	var gy := float(e["ground_y"])
	var r_m := float(h["radius_m"])
	var sc := float(e["scale"])
	var c: Vector2 = e["centre"]
	var u := maxf(_t - float(e["t_state"]), 0.0)
	var th := _thump()
	var bp := _beat_phase()
	var k := _strength(e)
	var white := Color(1, 1, 1)
	match state:
		"available":
			if _fill_ring(world, gy, r_m):
				var w := 3.0 if is_default else 2.0
				draw_polyline(_ring, Color(OUTLINE.r, OUTLINE.g, OUTLINE.b, OUTLINE.a * k), w + 2.0)
				draw_polyline(_ring, Color(hot.r, hot.g, hot.b, (0.72 + 0.28 * th) * k), w)
			if is_default and _fill_ring(world, gy, r_m * 0.66):  # the default: a second ring inside
				draw_polyline(_ring, Color(hot.r, hot.g, hot.b, 0.75 * k), 1.0)
			if not reduced and _fill_ring(world, gy, r_m * (1.0 + (0.9 if look == "pulse" else 0.6) * bp)):  # the ripple leaving the ring on every beat
				var ra := (1.0 - bp) * (1.0 - bp) * 0.75 * k
				if ra > 0.01:
					draw_polyline(_ring, Color(hot.r, hot.g, hot.b, ra), 1.0)
			if look == "crack":  # a crack in the floor, glowing from inside
				var g := _pj(world.x, gy, world.z)
				if g.z >= StoryProjector.NEAR:
					var gs := Vector2(g.x, g.y)
					var rr := r_m * sc * 0.9
					var pts := PackedVector2Array([gs + Vector2(-rr, 0.0), gs + Vector2(-rr * 0.45, -rr * 0.12), gs + Vector2(-rr * 0.2, rr * 0.1), gs + Vector2(rr * 0.15, -rr * 0.08), gs + Vector2(rr * 0.5, rr * 0.12), gs + Vector2(rr, 0.0)])
					draw_polyline(pts, Color(OUTLINE.r, OUTLINE.g, OUTLINE.b, 0.6 * k), 4.0)
					draw_polyline(pts, Color(white.r, white.g, white.b, (0.6 + 0.4 * th) * k), 2.0)
		"selected":
			var rs := r_m * 1.06 * (1.0 + 0.08 * th)  # the held pulse: the ring thumps on every beat
			if _fill_ring(world, gy, rs):
				draw_polyline(_ring, OUTLINE, 5.0)
				draw_polyline(_ring, Color(white.r, white.g, white.b, 0.92 + 0.08 * th), 3.0)
			var close := 1.0 - minf(u / 0.3, 1.0)  # a second ring closes in on the moment of the touch
			if close > 0.02 and _fill_ring(world, gy, r_m * (1.06 + 0.9 * close)):
				draw_polyline(_ring, Color(hot.r, hot.g, hot.b, 0.9 * close), 2.0)
			var spin := 0.0 if reduced else TAU * fposmod(_t / (beat_s * 4.0), 1.0)  # four motes circle the ring once a bar
			for i in 4:
				var a := spin + TAU * float(i) / 4.0
				var p := _pj(world.x + cos(a) * rs, gy, world.z + sin(a) * rs)
				if p.z >= StoryProjector.NEAR:
					_mote(self, Vector2(p.x, p.y), 4.0, OUTLINE)
					_mote(self, Vector2(p.x, p.y), 2.0, white)
			var lift := minf(u / 0.25, 1.0)
			lift = lift * lift * (3.0 - 2.0 * lift) * LIFT_M * sc
			_mote(self, c + Vector2(0.0, -lift), 3.0, white)
		"committed":
			var fk := clampf(u / FLASH_S, 0.0, 1.0)
			if fk < 1.0 and _fill_ring(world, gy, r_m * (1.0 + 2.2 * fk)):  # the flash: the ring bursts outward
				draw_polyline(_ring, Color(1, 1, 1, 0.95 * (1.0 - fk)), 4.0 * (1.0 - fk) + 1.0)
			var settle := 1.0 - _smooth01((u - FLASH_S) / SETTLE_S)  # then settles: a calm ring that fades
			if settle > 0.01 and _fill_ring(world, gy, r_m):
				draw_polyline(_ring, Color(hot.r, hot.g, hot.b, 0.85 * settle * fk), 2.0)


## The beacon of a hotspot out of sight: the same ring, ripple and core as one in view, at the edge on its side.
func _draw_edge(e: Dictionary, base: Color, hot: Color) -> void:
	var c: Vector2 = e["centre"]
	var R := float(e["radius_px"]) * 0.7
	var state := str(e["state"])
	var th := _thump()
	var bp := _beat_phase()
	var k := _strength(e)
	var sel := state == "selected"
	var col := Color(1, 1, 1) if sel else hot
	var rr := R * (1.0 + (0.08 * th if sel else 0.0))
	draw_arc(c, rr, 0.0, TAU, SEGMENTS, Color(OUTLINE.r, OUTLINE.g, OUTLINE.b, OUTLINE.a * k), 5.0 if sel else 4.0)
	draw_arc(c, rr, 0.0, TAU, SEGMENTS, Color(col.r, col.g, col.b, (0.8 + 0.2 * th) * k), 3.0 if sel else 2.0)
	if not reduced and not sel:
		var ra := (1.0 - bp) * (1.0 - bp) * 0.75 * k
		if ra > 0.01:
			draw_arc(c, R * (1.0 + 0.6 * bp), 0.0, TAU, SEGMENTS, Color(hot.r, hot.g, hot.b, ra), 1.0)
	_mote(self, c, 4.0 if sel else 3.0, Color(1, 1, 1, (0.85 + 0.15 * th) * k))
	if sel:
		var spin := 0.0 if reduced else TAU * fposmod(_t / (beat_s * 4.0), 1.0)
		for i in 4:
			var a := spin + TAU * float(i) / 4.0
			var p := c + Vector2(cos(a), sin(a) * 0.9) * rr
			_mote(self, p, 4.0, OUTLINE)
			_mote(self, p, 2.0, Color(1, 1, 1))
	elif state == "committed":
		var fk := clampf(maxf(_t - float(e["t_state"]), 0.0) / FLASH_S, 0.0, 1.0)
		if fk < 1.0:
			draw_arc(c, R * (1.0 + 1.5 * fk), 0.0, TAU, SEGMENTS, Color(1, 1, 1, 0.95 * (1.0 - fk)), 3.0)


## The light of a beacon: a leak of light along the border on its side and a half-sun at the border behind the ring.
func _light_edge(e: Dictionary, base: Color, hot: Color) -> void:
	var c: Vector2 = e["centre"]
	var R := float(e["radius_px"]) * 0.7
	var th := _thump()
	var k := _strength(e)
	var sel := str(e["state"]) == "selected"
	var side := 1.0 if c.x > size.x * 0.5 else -1.0
	var xe := size.x if side > 0.0 else 0.0
	var xi := xe - side * R * 4.0
	var a := ((0.95 if sel else 0.7) + 0.3 * th) * k
	var col := Color(1, 1, 1) if sel else hot
	var top := Vector2(xe, c.y - R * 4.0)
	var bot := Vector2(xe, c.y + R * 4.0)
	_quad_c[0] = Color(col.r, col.g, col.b, a)
	_quad_c[1] = Color(col.r, col.g, col.b, 0.0)
	_quad_c[2] = _quad_c[1]
	_quad_c[3] = _quad_c[1]
	_quad[0] = Vector2(xe, c.y)
	_quad[1] = Vector2(xi, c.y)
	_quad[2] = Vector2(xi, top.y)
	_quad[3] = top
	_light.draw_polygon(_quad, _quad_c)
	_quad[2] = Vector2(xi, bot.y)
	_quad[3] = bot
	_light.draw_polygon(_quad, _quad_c)
	_glow(Vector2(xe, c.y), R * 2.4 * (1.0 + 0.15 * th), col, a)
	_glow(c, R * 1.3, Color(1, 1, 1) if sel else hot, (0.6 + 0.35 * th) * k)


static func _smooth01(x: float) -> float:
	x = clampf(x, 0.0, 1.0)
	return x * x * (3.0 - 2.0 * x)
