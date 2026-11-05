class_name HotspotView
extends Control
## The hotspots drawn in the world and hit-tested on screen. It lives inside the low-res viewport above the crowd (StoryLowRes.add_overlay), so a ring of light pixelates with the picture; the
## input is taken by the run scene on the stage area only (the pads are elsewhere) and resolved with the same pure `layout` and `hit` below at screen resolution.
##
## Looks, with no text and no floating rectangles: AVAILABLE a ring of light on the floor under the anchor and a glow on the thing (`look.available` picks the character: glow, a slow pulse, a
## beckoning light column, a flicker, a door ajar with its light spilling, a crack in the floor); the default exit is brighter and its ring is doubled, its door wider ajar. SELECTED: a bright ring
## and a lift (the glow rises and a second ring closes in). COMMITTED: a flash and the ring opening out; an actor anchor acts from the moment it is on show (its `acting` block, else the crowd's own `wave`).
## An anchor out of sight (behind the camera, off to a side) is a soft beacon of light at the edge of the picture, still touchable: free look is never needed.

const SEGMENTS := 28
const EDGE_MARGIN := 0.07  # of the view's short side
const LIFT_M := 0.28
const FLASH_S := 0.5

var items_fn: Callable  # () -> Array of {hotspot: Dictionary, state: "available" | "selected" | "committed", t_state: float (song time the state began)}
var pose_fn: Callable  # () -> {cam: Vector3, yaw, pitch} (empty: nothing to draw)
var now_fn: Callable  # () -> song time
var stage: StoryStage
var beat_s := 60.0 / 174.0
var tint := Color(1.0, 0.85, 0.5)  # the chapter palette's accent
var reduced := false
var high_contrast := false
var glow_tex: Texture2D = null

var _acting: Dictionary = {}  # actor id -> "<state>|<hotspot id>" of the act the crowd was last told (so it is told once per change)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 5


func _process(_d: float) -> void:
	if visible:
		queue_redraw()


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

func _draw() -> void:
	if not items_fn.is_valid() or not pose_fn.is_valid() or stage == null or stage.map == null:
		return
	var pose: Dictionary = pose_fn.call()
	if pose.is_empty():
		return
	var t := float(now_fn.call()) if now_fn.is_valid() else 0.0
	var items: Array = items_fn.call()
	_manage_acting(items, t)
	var lay := layout(items, stage.map, stage.crowds, pose, size)
	lay.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["depth"]) > float(b["depth"]))  # far first
	for e in lay:
		_draw_entry(e, pose, t)


func _pulse(t: float, per_beats: float) -> float:
	return 0.5 + 0.5 * sin(t / (beat_s * per_beats) * TAU)


## The people the hotspots on show direct (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3a): a hotspot with an `acting` block has its person do the `available` act while it waits and the `selected` act
## once touched; one with no block at all keeps the old wave at the player. When the hotspot leaves (committed, or its window shut) the view stands its own act down; the commit's outcome acts
## are RunPlay's and play on. A story beat (`cast`) already in force on the person is not interrupted by the available act (it waits its turn); a touch always is.
func _manage_acting(items: Array, t: float) -> void:
	var want := {}  # actor id -> {key, spec}
	for e in items:
		var h: Dictionary = e["hotspot"]
		var st := str(e["state"])
		if st == "committed":
			continue
		var aid := RunActing.actor_of(h)
		if aid == "":
			continue
		var spec := RunActing.selected_spec(h) if st == "selected" else RunActing.available_spec(h)
		if spec.is_empty():
			continue
		want[aid] = {"key": st + "|" + str(h["id"]), "spec": spec, "touch": st == "selected"}
	for id in want:
		var w: Dictionary = want[id]
		if _acting.get(id, "") == str(w["key"]):
			continue
		var done := false
		for rid in stage.crowds:
			var c := stage.crowds[rid] as StoryCrowd
			if not c.actors.has(id):
				continue
			if not bool(w["touch"]) and c.directing(str(id), t) == "cast":
				break  # (their story beat first; this tries again next frame)
			var sp: Dictionary = w["spec"]
			c.ensure_present(str(id))  # (a gatherer or a late arrival the hotspot anchors on is there when it asks for you)
			done = c.direct_actor(str(id), str(sp["act"]), str(sp.get("face", "")), t, t + RunActing.STATE_S, str(sp.get("look_at", "")), "hotspot")
			break
		if done:
			_acting[id] = str(w["key"])
	for id in _acting.keys():
		if not want.has(id):
			_acting.erase(id)
			for rid in stage.crowds:
				(stage.crowds[rid] as StoryCrowd).stand_down(str(id), "hotspot")


func _ring_points(world: Vector3, ground_y: float, r: float, pose: Dictionary) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in SEGMENTS + 1:
		var a := TAU * float(i) / float(SEGMENTS)
		var pr := StoryProjector.project(Vector3(world.x + cos(a) * r, ground_y, world.z + sin(a) * r), pose, size)
		if float(pr["depth"]) < StoryProjector.NEAR:
			return PackedVector2Array()
		pts.append(pr["screen"])
	return pts


func _glow(c: Vector2, r: float, col: Color, a: float) -> void:
	if glow_tex != null:
		var s := r * 2.6
		draw_texture_rect(glow_tex, Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s)), false, Color(col.r, col.g, col.b, clampf(a * 1.6, 0.0, 1.0)))
		return
	for k in 4:
		var f := 1.0 - float(k) * 0.22
		draw_circle(c, r * f, Color(col.r, col.g, col.b, a * 0.28))


func _draw_entry(e: Dictionary, pose: Dictionary, t: float) -> void:
	var h: Dictionary = e["hotspot"]
	var state := str(e["state"])
	var look: Dictionary = h["look"]
	var is_default := bool(h["default"])
	var sc := float(e["scale"])
	var c: Vector2 = e["centre"]
	var g: Vector2 = e["ground"]
	var world: Vector3 = e["world"]
	var r_m := float(h["radius_m"])
	var u := maxf(t - float(e["t_state"]), 0.0)
	var base := tint
	if high_contrast:
		base = Color(1.0, 1.0, 0.4)
	var pulse := 0.0 if reduced else _pulse(t, 4.0 if str(look["available"]) != "pulse" else 1.0)
	var strength := 0.32 + 0.3 * pulse + (0.2 if is_default else 0.0)
	var white := base.lerp(Color(1, 1, 1), 0.7)
	if bool(e["edge"]):
		_glow(c, float(e["radius_px"]) * (1.0 + 0.2 * pulse), white if state == "selected" else base, 0.45 + 0.3 * pulse + (0.25 if state == "selected" else 0.0))
		draw_arc(c, float(e["radius_px"]) * 0.8, 0.0, TAU, 24, Color(white.r, white.g, white.b, 0.5 + 0.4 * pulse), maxf(1.0, sc * 0.02))
		return
	var width := maxf(1.0, sc * 0.035)
	match state:
		"available":
			var look_a := str(look["available"])
			var ring := _ring_points(world, float(e["ground_y"]), r_m, pose)
			if ring.size() > 2:
				draw_polyline(ring, Color(base.r, base.g, base.b, strength), width * (1.6 if is_default else 1.0))
				if is_default:  # the default exit: a second ring and a brighter light
					draw_polyline(_ring_points(world, float(e["ground_y"]), r_m * 0.66, pose), Color(white.r, white.g, white.b, strength * 0.9), width)
			var flick := 1.0
			if look_a == "flicker" and not reduced:
				flick = 0.35 + 0.65 * float(int(floor(t * 14.0)) * 7919 % 5) / 4.0
			_glow(c, r_m * sc * 0.55, base, (0.3 + 0.25 * pulse + (0.15 if is_default else 0.0)) * flick)
			match look_a:
				"open":  # a door ajar: a slit of light standing at the doorway, spilling on the floor
					var ajar := 0.5 if is_default else 0.3
					var hw := r_m * ajar
					var rv := StoryProjector.right(float(pose["yaw"]))
					var b0 := StoryProjector.project(Vector3(world.x - rv.x * hw, float(e["ground_y"]), world.z - rv.y * hw), pose, size)
					var b1 := StoryProjector.project(Vector3(world.x + rv.x * hw, float(e["ground_y"]), world.z + rv.y * hw), pose, size)
					var t0p := StoryProjector.project(Vector3(world.x - rv.x * hw * 0.5, float(e["ground_y"]) + 2.0, world.z - rv.y * hw * 0.5), pose, size)
					var t1p := StoryProjector.project(Vector3(world.x + rv.x * hw * 0.5, float(e["ground_y"]) + 2.0, world.z + rv.y * hw * 0.5), pose, size)
					if float(b0["depth"]) > StoryProjector.NEAR and float(t0p["depth"]) > StoryProjector.NEAR:
						draw_colored_polygon(PackedVector2Array([b0["screen"], b1["screen"], t1p["screen"], t0p["screen"]]), Color(white.r, white.g, white.b, 0.22 + 0.2 * pulse + (0.15 if is_default else 0.0)))
				"beckon":  # a light column rising from the floor with a mote riding it
					var top := Vector2(g.x, g.y - sc * 1.7)
					draw_line(g, top, Color(white.r, white.g, white.b, 0.28 + 0.25 * pulse), width * 1.4)
					draw_circle(top.lerp(g, 0.5 + 0.35 * sin(t * 3.0)), maxf(1.5, sc * 0.05), Color(white.r, white.g, white.b, 0.8))
				"crack":  # a crack in the floor, glowing from inside
					var rr := r_m * sc * 0.9
					var pts := PackedVector2Array([g + Vector2(-rr, 0.0), g + Vector2(-rr * 0.45, -rr * 0.12), g + Vector2(-rr * 0.2, rr * 0.1), g + Vector2(rr * 0.15, -rr * 0.08), g + Vector2(rr * 0.5, rr * 0.12), g + Vector2(rr, 0.0)])
					draw_polyline(pts, Color(white.r, white.g, white.b, 0.45 + 0.35 * pulse), width * 1.5)
		"selected":
			var lift := minf(u / 0.25, 1.0)
			lift = lift * lift * (3.0 - 2.0 * lift) * LIFT_M * sc
			var ring2 := _ring_points(world, float(e["ground_y"]), r_m * 1.08, pose)
			if ring2.size() > 2:
				draw_polyline(ring2, Color(white.r, white.g, white.b, 0.95), width * 2.4)
				var close := 1.0 - minf(u / 0.3, 1.0)  # a second ring closes in on the selected one
				if close > 0.02:
					draw_polyline(_ring_points(world, float(e["ground_y"]), r_m * (1.08 + 0.8 * close), pose), Color(white.r, white.g, white.b, 0.8 * close), width)
			_glow(c + Vector2(0.0, -lift), r_m * sc * 0.75, white, 0.7)
			draw_circle(c + Vector2(0.0, -lift), maxf(2.0, sc * 0.07), Color(1, 1, 1, 0.95))
			draw_line(g, c + Vector2(0.0, -lift), Color(white.r, white.g, white.b, 0.5), width)
		"committed":
			var k := clampf(u / FLASH_S, 0.0, 1.0)
			var out_r := r_m * (1.0 + 2.2 * k)
			var ring3 := _ring_points(world, float(e["ground_y"]), out_r, pose)
			if ring3.size() > 2:
				draw_polyline(ring3, Color(1, 1, 1, 0.95 * (1.0 - k)), width * 3.0 * (1.0 - k) + 1.0)
			_glow(c + Vector2(0.0, -LIFT_M * sc), r_m * sc * (0.8 + 1.4 * k), Color(1, 1, 1), 0.95 * (1.0 - k) + 0.1)
