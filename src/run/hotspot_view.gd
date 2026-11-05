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
const CURRENT_COL := Color(0.25, 1.0, 0.45)
const OTHER_COL := Color(1.0, 0.32, 0.22)
const CLAIM_BURST_S := 0.35  # the touch burst of the "claim" look
const CLAIM_REFUSE_S := 0.8  # the refusal (a waved-off claim) plays out over this long

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

## The choice layer (docs/CHOICE_CLARITY.md): () -> {staged: [hotspot], current: id, committed: id, dest: route, default: id, touched: {id: song time of the last touch}}; empty or
## unset: no staging (the old look). From the scene's first beat every staged option shows whether it is the current choice (ChoiceStaging), not only in the window.
var choice_fn: Callable
var props: ChoiceProps = null
var touch_rects := false  # a generous touch area on the thing itself (ChoiceStaging `touch`), besides the ring's radius
var last_snapshot: Dictionary = {}
var _mem: Dictionary = {}  # hotspot id -> {role, t_role, open, t_open, key_act, key_steps}


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
static func layout(entries: Array, map: StoryMap, crowds: Dictionary, pose: Dictionary, view: Vector2, rects := false) -> Array:
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
		var entry := {"id": str(h["id"]), "hotspot": h, "state": str(e["state"]), "t_state": float(e.get("t_state", 0.0)), "t_commit": float(e.get("t_commit", 0.0)), "success": bool(e.get("success", true)), "world": p, "ground_y": float(r["ground"]), "actor": bool(r["actor"]), "edge": false, "ok": true,
			"finished": bool(e.get("finished", false))}
		var on_screen: bool = bool(pc["visible"]) and float(pc["depth"]) > 0.4 and pc["screen"].x >= 0.0 and pc["screen"].x <= view.x and (pc["screen"].y >= 0.0 and pc["screen"].y <= view.y or str((h["look"] as Dictionary).get("selected", "")) == "claim")  # a "claim" thing standing just below the picture still counts as in view (its beam rises into it)
		if on_screen:
			var sc := float(pc["scale"])
			var rad := minf(maxf(float(h["radius_m"]) * sc, min_r), minf(view.x, view.y) * 0.5)
			var sp: Vector2 = pc["screen"]
			entry["centre"] = Vector2(clampf(sp.x, rad, view.x - rad), clampf(sp.y, rad, view.y - rad))  # the whole touch target stays inside the stage view, so never over the pads below it
			entry["ground"] = pg["screen"] if bool(pg["visible"]) else pc["screen"]
			entry["scale"] = sc
			entry["depth"] = float(pc["depth"])
			entry["radius_px"] = rad
			if rects:  # the thing itself is touchable: a rectangle of the staging's {w, h} metres standing on the floor under the anchor, inside the view
				var tch: Dictionary = ChoiceStaging.of(h).get("touch", {})
				var hw := float(tch.get("w", 1.2)) * sc * 0.5
				var gy: float = (entry["ground"] as Vector2).y
				var top := StoryProjector.project(Vector3(p.x, float(r["ground"]) + float(tch.get("h", 2.0)), p.z), pose, view)
				var ty: float = top["screen"].y if bool(top["visible"]) else gy - float(tch.get("h", 2.0)) * sc
				var rr := Rect2(Vector2(sp.x - hw, ty), Vector2(hw * 2.0, maxf(gy - ty, 1.0)))
				entry["touch_rect"] = rr.intersection(Rect2(Vector2.ZERO, view))
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
		var inside: bool = d <= float(e["radius_px"]) or (e.has("touch_rect") and (e["touch_rect"] as Rect2).has_point(point))
		if inside and d < best_d - 1.0e-6:
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
	var snap := choice_snapshot(t)
	_stage_choice(snap, t)
	_manage_acting(items, t, snap)
	var lay := layout(items, stage.map, stage.crowds, pose, size)
	lay.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["depth"]) > float(b["depth"]))  # far first
	var opts: Dictionary = snap.get("options", {})
	var shown_again := {}  # a "claim" hotspot waved off stays on show: its refusal replaces the plain look for a moment
	for e in lay:
		if str(e["state"]) == "committed":
			shown_again[str(e["id"])] = true
	for e in lay:
		if opts.has(str(e["id"])):
			e["role"] = str(opts[str(e["id"])]["role"])
		if str(e["state"]) == "available" and shown_again.has(str(e["id"])):
			continue
		_draw_entry(e, pose, t)


func _pulse(t: float, per_beats: float) -> float:
	return 0.5 + 0.5 * sin(t / (beat_s * per_beats) * TAU)


## The people the hotspots on show direct (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3a): a hotspot with an `acting` block has its person do the `available` act while it waits and the `selected` act
## once touched; one with no block at all keeps the old wave at the player. When the hotspot leaves (committed, or its window shut) the view stands its own act down; the commit's outcome acts
## are RunPlay's and play on. A story beat (`cast`) already in force on the person is not interrupted by the available act (it waits its turn); a touch always is.
func _manage_acting(items: Array, t: float, snap: Dictionary = {}) -> void:
	var want := {}  # actor id -> {key, spec}
	var staged_people: Dictionary = snap.get("people", {})
	for e in items:
		var h: Dictionary = e["hotspot"]
		var st := str(e["state"])
		if st == "committed":
			continue
		var aid := RunActing.actor_of(h)
		if aid == "" or staged_people.has(aid):  # (an option of a staged choice is played by the choice layer)
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
	var r_m := float((look as Dictionary).get("ring_m", h["radius_m"]))  # the drawn ring: the touch radius unless look.ring_m says the thing is smaller
	var u := maxf(t - float(e["t_state"]), 0.0)
	var base := tint
	var finished := bool(e.get("finished", false))  # a portal whose path has been finished (plan D10): its own tint and look
	if finished:
		base = Color.html(str((look["finished"] as Dictionary).get("tint", HotspotContract.FINISHED_TINT)))
	if high_contrast:
		base = Color(1.0, 1.0, 0.4)
	var role := str(e.get("role", ""))
	if role != "" and not finished and not high_contrast:  # the current choice: green and doubled; another option: red and dashed (shape as well as colour)
		base = CURRENT_COL if role == "current" or role == "committed" else OTHER_COL
		is_default = role == "current"
	var pulse := 0.0 if reduced else _pulse(t, 4.0 if str(look["available"]) != "pulse" else 1.0)
	var strength := 0.32 + 0.3 * pulse + (0.2 if is_default else 0.0)
	var white := base.lerp(Color(1, 1, 1), 0.7)
	if bool(e["edge"]):
		if str(look["selected"]) == "claim":  # a big touch target is not a big beacon
			e = e.duplicate()
			e["radius_px"] = minf(float(e["radius_px"]), size.y * 0.16)
		_glow(c, float(e["radius_px"]) * (1.0 + 0.2 * pulse), white if state == "selected" else base, 0.45 + 0.3 * pulse + (0.25 if state == "selected" else 0.0))
		draw_arc(c, float(e["radius_px"]) * 0.8, 0.0, TAU, 24, Color(white.r, white.g, white.b, 0.5 + 0.4 * pulse), maxf(1.0, sc * 0.02))
		return
	var width := maxf(1.0, sc * 0.035)
	if str(look["selected"]) == "claim" and state in ["selected", "committed"]:
		_draw_claim(e, state, pose, t, u, base, white)
		return
	match state:
		"available":
			var look_a := str(look["available"]) if not finished else str((look["finished"] as Dictionary).get("available", "crown"))
			var ring := _ring_points(world, float(e["ground_y"]), r_m, pose)
			if ring.size() > 2:
				draw_polyline(ring, Color(base.r, base.g, base.b, strength), width * (1.6 if is_default else 1.0))
				if is_default:  # the default exit: a second ring and a brighter light
					draw_polyline(_ring_points(world, float(e["ground_y"]), r_m * 0.66, pose), Color(white.r, white.g, white.b, strength * 0.9), width)
			var flick := 1.0
			if look_a == "flicker" and not reduced:
				flick = 0.35 + 0.65 * float(int(floor(t * 14.0)) * 7919 % 5) / 4.0
			if role != "":  # a staged option: the thing itself shows its state (ChoiceStaging); the light stays on the floor and never covers a face or a door
				return
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
				"crown":  # a finished path: the portal's pulse ringed by three motes circling it, a ring of light round its heart
					var orb := r_m * sc * 0.62
					var spin := 0.0 if reduced else t * TAU / (beat_s * 8.0)
					draw_arc(c, orb, 0.0, TAU, 32, Color(base.r, base.g, base.b, 0.6 + 0.3 * pulse), width * 1.6)
					_glow(c, orb * 0.8, base, 0.45 + 0.3 * pulse)
					for k in 3:
						var ang := spin + TAU * float(k) / 3.0
						var mp := c + Vector2(cos(ang), sin(ang) * 0.55) * orb
						_glow(mp, maxf(5.0, sc * 0.16), base, 0.9)
						draw_circle(mp, maxf(2.0, sc * 0.05), Color(base.lerp(Color(1, 1, 1), 0.5), 1.0))
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
			if role != "":
				return
			_glow(c + Vector2(0.0, -lift), r_m * sc * 0.75, white, 0.7)
			draw_circle(c + Vector2(0.0, -lift), maxf(2.0, sc * 0.07), Color(1, 1, 1, 0.95))
			draw_line(g, c + Vector2(0.0, -lift), Color(white.r, white.g, white.b, 0.5), width)
		"committed":
			var k := clampf(u / FLASH_S, 0.0, 1.0)
			var out_r := r_m * (1.0 + 2.2 * k)
			var ring3 := _ring_points(world, float(e["ground_y"]), out_r, pose)
			if ring3.size() > 2:
				draw_polyline(ring3, Color(1, 1, 1, 0.95 * (1.0 - k)), width * 3.0 * (1.0 - k) + 1.0)
			if role == "":  # (a staged option's commit is its door swinging wide and its people reacting: no flash over them)
				_glow(c + Vector2(0.0, -LIFT_M * sc), r_m * sc * (0.8 + 1.4 * k), Color(1, 1, 1), 0.95 * (1.0 - k) + 0.1)


# --- the "claim" look: touching a place you can sit at (the blackjack table). Bold shapes, no text: the picture is small and the eyes are on the pads. --------------------------

## A warm wash round the edge of the whole picture (peripheral vision sees a touch counted); `a` is its strength at the very edge.
func _frame_wash(col: Color, a: float) -> void:
	var th := size.y * 0.035
	for i in 6:
		var f := 1.0 - float(i) / 6.0
		var c := Color(col.r, col.g, col.b, a * f)
		var o := th * float(i)
		draw_rect(Rect2(0.0, o, size.x, th), c)
		draw_rect(Rect2(0.0, size.y - o - th, size.x, th), c)
		draw_rect(Rect2(o, 0.0, th, size.y), c)
		draw_rect(Rect2(size.x - o - th, 0.0, th, size.y), c)


## A ring on the floor drawn as far as it is in front of the camera (a ring round a table the camera stands close to reaches behind it).
func _claim_ring(world: Vector3, ground_y: float, r: float, pose: Dictionary, col: Color, width: float) -> void:
	var run := PackedVector2Array()
	for i in SEGMENTS * 2 + 1:
		var a := TAU * float(i) / float(SEGMENTS * 2)
		var pr := StoryProjector.project(Vector3(world.x + cos(a) * r, ground_y, world.z + sin(a) * r), pose, size)
		if float(pr["depth"]) < StoryProjector.NEAR:
			if run.size() > 1:
				draw_polyline(run, col, width)
			run = PackedVector2Array()
		else:
			run.append(pr["screen"])
	if run.size() > 1:
		draw_polyline(run, col, width)


## The floor disc inside a ring of radius `r` metres, filled with light.
func _disc(world: Vector3, ground_y: float, r: float, pose: Dictionary, col: Color) -> void:
	var pts := _ring_points(world, ground_y, r, pose)
	if pts.size() > 3:
		draw_colored_polygon(pts.slice(0, pts.size() - 1), col)


## A tall beam of light standing on `g`, fading out at the top.
func _claim_beam(g: Vector2, h_px: float, w_px: float, col: Color, a: float) -> void:
	var top := g + Vector2(0.0, -h_px)
	var cols := PackedColorArray([Color(col.r, col.g, col.b, a), Color(col.r, col.g, col.b, a), Color(col.r, col.g, col.b, 0.0), Color(col.r, col.g, col.b, 0.0)])
	draw_polygon(PackedVector2Array([g + Vector2(-w_px, 0.0), g + Vector2(w_px, 0.0), top + Vector2(w_px * 0.45, 0.0), top + Vector2(-w_px * 0.45, 0.0)]), cols)
	draw_line(g, top.lerp(g, 0.15), Color(1, 1, 1, a), maxf(2.0, w_px * 0.35))


func _draw_claim(e: Dictionary, state: String, pose: Dictionary, t: float, u: float, base: Color, white: Color) -> void:
	var h: Dictionary = e["hotspot"]
	var sc := float(e["scale"])
	var g: Vector2 = e["ground"]
	var world: Vector3 = e["world"]
	var gy := float(e["ground_y"])
	var r_m := float((h["look"] as Dictionary).get("ring_m", h["radius_m"]))
	var thick := maxf(3.0, sc * 0.11)
	if state == "committed":
		if bool(e["success"]):
			_claim_success(pose, u, white, g, world, gy, r_m, sc, thick)
		else:
			_claim_refused(pose, u, g, world, gy, r_m, sc, thick)
		return
	var beat_ph := fmod(t, beat_s) / beat_s
	var throb := 0.0 if reduced else pow(1.0 - beat_ph, 3.0)
	# the whole floor disc: warm light, the ring throbbing on every beat, a tall beam over the table
	_disc(world, gy, r_m, pose, Color(base.r, base.g, base.b, 0.3 + 0.12 * throb))
	_claim_beam(g, sc * 3.0, maxf(5.0, sc * 0.3) * (1.0 + 0.2 * throb), white, 0.75)
	_claim_ring(world, gy, r_m * (1.0 + 0.04 * throb), pose, Color(white.r, white.g, white.b, 0.85 + 0.15 * throb), thick * (1.0 + 0.5 * throb))
	# the countdown: a ring closing in from well outside, on the main ring exactly at the decision (reduced: an arc filling clockwise)
	var span := maxf(float(e["t_commit"]) - float(e["t_state"]), 0.05)
	var left := clampf((float(e["t_commit"]) - t) / span, 0.0, 1.0)
	if reduced:
		draw_arc(g, r_m * sc * 0.5 + thick * 2.0, -PI * 0.5, -PI * 0.5 + TAU * (1.0 - left), 40, Color(1, 1, 1, 0.95), thick)
	else:
		_claim_ring(world, gy, r_m * (1.0 + 1.6 * left), pose, Color(1, 1, 1, 0.55 + 0.4 * (1.0 - left)), maxf(2.0, thick * 0.8))
	# the instant of the touch: a flash on the floor, a thick ring flying out, and the picture's edge washed with light
	if u < CLAIM_BURST_S and not reduced:
		var k := u / CLAIM_BURST_S
		_disc(world, gy, r_m, pose, Color(1, 1, 1, 0.55 * (1.0 - k)))
		_claim_ring(world, gy, r_m * (1.0 + 1.4 * k), pose, Color(1, 1, 1, 0.95 * (1.0 - k)), thick * 2.2 * (1.0 - k) + 2.0)
		_frame_wash(white, 0.5 * (1.0 - k))
		_glow(Vector2(g.x, minf(g.y - sc * 0.5, size.y * 0.8)), r_m * sc * (0.9 + 0.8 * k), Color(1, 1, 1), 0.6 * (1.0 - k))


## Sat down: a bigger, brighter version of the plain flash (the walk to the chair follows).
func _claim_success(pose: Dictionary, u: float, white: Color, g: Vector2, world: Vector3, gy: float, r_m: float, sc: float, thick: float) -> void:
	var k := clampf(u / (FLASH_S * 1.6), 0.0, 1.0)
	_disc(world, gy, r_m, pose, Color(1, 1, 1, 0.85 * (1.0 - k) + 0.1))
	_claim_ring(world, gy, r_m * (1.0 + 2.6 * k), pose, Color(1, 1, 1, 0.98 * (1.0 - k)), thick * 2.6 * (1.0 - k) + 2.0)
	_claim_beam(g, sc * (3.0 + 2.0 * k), maxf(6.0, sc * 0.4), white, 0.95 * (1.0 - 0.6 * k))
	_glow(Vector2(g.x, minf(g.y - sc * 0.6, size.y * 0.8)), r_m * sc * (1.0 + 1.6 * k), Color(1, 1, 1), 0.95 * (1.0 - k) + 0.1)
	if not reduced:
		_frame_wash(white, 0.8 * (1.0 - k))


## Waved off: cold grey light, the ring breaks into segments that drop and fade, a short sideways shake. Nothing of it is warm or white.
func _claim_refused(pose: Dictionary, u: float, g: Vector2, world: Vector3, gy: float, r_m: float, sc: float, thick: float) -> void:
	var k := clampf(u / CLAIM_REFUSE_S, 0.0, 1.0)
	var cold := Color(0.55, 0.62, 0.75) if not high_contrast else Color(0.75, 0.8, 0.9)
	var shake := 0.0 if reduced else sin(u * 70.0) * (1.0 - k) * sc * 0.14
	draw_set_transform(Vector2(shake, 0.0))
	_disc(world, gy, r_m, pose, Color(cold.r, cold.g, cold.b, 0.35 * (1.0 - k)))
	var ring := _ring_points(world, gy, r_m, pose)
	if ring.size() > 2:
		var per := 4
		for i in 7:
			var seg := PackedVector2Array()
			var fall := 0.0 if reduced else k * k * sc * (0.9 + 0.35 * float(i % 3))
			for j in range(i * per, i * per + per):  # four points per arc: three segments drawn, one left out as the gap
				seg.append(ring[mini(j, ring.size() - 1)] + Vector2(0.0, fall))
			draw_polyline(seg, Color(cold.r, cold.g, cold.b, 0.9 * (1.0 - k)), thick * (1.0 - 0.4 * k))
	_claim_beam(g, sc * 3.0 * (1.0 - k), maxf(4.0, sc * 0.2), cold, 0.5 * (1.0 - k))
	draw_set_transform(Vector2.ZERO)


# --- the choice layer (docs/CHOICE_CLARITY.md) ----------------------------------------------------------------------------------

## The staged options now: {current, default, committed, dest, options: {id: {role, archetype, open (target), open_k (0..1 now), lamp, since_role_s, since_touch_s}},
## people: {actor id: hotspot id}, hotspots: {id: hotspot}}. The roles' change times are remembered here (song time), so a door swings and a touched person nods over the next
## beat whatever the frame step. Empty when fewer than two options are staged (no choice to show).
func choice_snapshot(t: float) -> Dictionary:
	if not choice_fn.is_valid():
		return {}
	var c: Dictionary = choice_fn.call()
	if c.is_empty() or (c.get("staged", []) as Array).size() < 2:
		if not _mem.is_empty():
			clear_choice()
		last_snapshot = {}
		return {}
	var staged: Array = c["staged"]
	var roles := ChoiceStaging.roles(staged, str(c.get("current", "")), str(c.get("committed", "")), str(c.get("dest", "")))
	var out := {"current": str(c.get("current", "")), "default": str(c.get("default", "")), "committed": str(c.get("committed", "")), "dest": str(c.get("dest", "")), "options": {}, "people": {}, "hotspots": {}}
	var touched: Dictionary = c.get("touched", {})
	for h in staged:
		var id := str(h["id"])
		var r: Dictionary = roles[id]
		var m: Dictionary = _mem.get(id, {})
		if m.is_empty():  # first seen: already in its role and its door already where it belongs (the default stands open from the scene's first beat)
			m = {"role": r["role"], "t_role": -INF, "open": r["open"], "t_open": -INF}
		var t_ch := minf(float(c.get("changed_t", t)), t)  # (the song time of the touch or the commit that changed it, from the data: the same at any frame step)
		if str(m["role"]) != str(r["role"]):
			m["role"] = r["role"]
			m["t_role"] = t_ch
		if bool(m["open"]) != bool(r["open"]):
			m["open"] = r["open"]
			m["t_open"] = t_ch
		_mem[id] = m
		var st := ChoiceStaging.of(h)
		var open_k := ChoiceStaging.open_amount(bool(r["open"]), t - float(m["t_open"]), beat_s)
		var o := {"role": str(r["role"]), "archetype": str(r["archetype"]), "open": bool(r["open"]), "open_k": open_k, "since_role_s": t - float(m["t_role"]),
			"since_touch_s": t - float(touched[id]) if touched.has(id) else INF}
		o["lamp"] = ChoiceStaging.lamp_of(st, str(r["role"]), bool(r["open"]))
		out["options"][id] = o
		out["hotspots"][id] = h
		if str(st["archetype"]) == "person" and str(st.get("actor", "")) != "":
			out["people"][str(st["actor"])] = id
	for id in _mem.keys():
		if not (out["options"] as Dictionary).has(id):
			_forget(str(id))
	last_snapshot = out
	return out


## Computes the snapshot and plays it (what _draw does each frame; the tests call it on the virtual clock, where nothing is drawn).
func refresh_choice(t: float) -> Dictionary:
	var snap := choice_snapshot(t)
	_stage_choice(snap, t)
	return snap


## Plays a snapshot in the world: the people's acts and faces, the billboards' textures and motions, the set pieces, and the props (doors, boards, lamps, spills, `states` props).
func _stage_choice(snap: Dictionary, t: float) -> void:
	if stage == null or stage.world == null:
		return
	if props == null and not snap.is_empty():
		props = ChoiceProps.new()
		props.name = "ChoiceProps"
		stage.world.add_child(props)
	if props != null:
		props.begin_frame()
	var opts: Dictionary = snap.get("options", {})
	var u := (t / beat_s) if beat_s > 0.0 else 0.0
	for id in opts:
		var o: Dictionary = opts[id]
		var h: Dictionary = snap["hotspots"][id]
		var st := ChoiceStaging.of(h)
		var role := str(o["role"])
		var lit := role == "current" or role == "committed"
		var r := resolve(h["anchor"], stage.map, stage.crowds)
		var foot := Vector3.ZERO
		var centre_y := 1.0
		if bool(r.get("ok", false)):
			var p: Vector3 = r["pos"]
			foot = Vector3(p.x, float(r["ground"]), p.z)
			centre_y = p.y - float(r["ground"])
		if st.has("door_at"):
			var da: Array = st["door_at"]
			foot = Vector3(float(da[0]), foot.y, float(da[1]))
		var touched_now := float(o["since_touch_s"]) < 1.5 * beat_s and role == "current"
		match str(st["archetype"]):
			"person":
				_stage_person(id, h, st, o, t)
			"figure":
				var th := str(st.get("thing", ""))
				if th != "":
					var mo := ChoiceStaging.motion(str(st.get("current_motion" if lit else "other_motion", "still")), u)
					var tx := str(st.get("current_tex" if lit else "other_tex", ""))
					if tx != "":
						mo["tex"] = ChoiceProps.tex(tx)
					stage.world.thing_pose[th] = mo
					_mem[id]["thing"] = th
			"door":
				var hgt := float(st.get("height_m", 2.4))
				match str(st.get("door", "drawn")):
					"drawn":
						props.put(id + "#door", ChoiceProps.door_frame(float(o["open_k"])), foot, hgt, 0.85)
						if float(o["open_k"]) > 0.05:
							props.put(id + "#spill", "spill", foot, 1.6, 1.0, float(o["open_k"]) * 0.8, true)
					"bars":
						props.put(id + "#bars", "bars", foot + Vector3(0.0, hgt * 0.15, 0.0), hgt * 0.7, 0.9, 1.0 - float(o["open_k"]))
						if float(o["open_k"]) > 0.05:
							props.put(id + "#spill", "spill", foot, 1.6, 1.0, float(o["open_k"]) * 0.8, true)
					"sign":
						props.put(id + "#door", "sign_go" if float(o["open_k"]) >= 0.5 else "sign_stop", foot, hgt, 0.85)
					"pieces":
						_piece(id, str(st["open_piece"]) if bool(o["open"]) else str(st["shut_piece"]), str(st["shut_piece"]) if bool(o["open"]) else str(st["open_piece"]), t)
			"object", "feature":
				var an: Dictionary = h["anchor"]
				if an.has("thing"):
					stage.world.thing_pose[str(an["thing"])] = ChoiceStaging.motion(str(st.get("current_motion" if lit else "other_motion", "still")), u)
					_mem[id]["thing"] = str(an["thing"])
		var lamp := str(o["lamp"])
		if lamp != "none" and props != null:
			var ly := float(st.get("lamp_y", float(st.get("height_m", 2.4)) + 0.15 if str(st["archetype"]) == "door" else centre_y + 0.6))
			props.put(id + "#lamp", "lamp_go" if lamp == "go" else "lamp_stop", foot + Vector3(0.0, ly, 0.0), 0.34, 1.0)
		_play_steps(id, st, role, touched_now, foot, u, t)
	if props != null:
		props.end_frame()


func _stage_person(id: String, h: Dictionary, st: Dictionary, o: Dictionary, t: float) -> void:
	var aid := str(st.get("actor", ""))
	var role := str(o["role"])
	var m: Dictionary = _mem[id]
	m["actor"] = aid
	if role == "committed" and RunActing.has_acting(h):
		return  # (the outcome's own acts play: RunPlay._act_outcome)
	var spec := ChoiceStaging.person_spec(st, role, float(o["since_role_s"]), float(o["since_touch_s"]), beat_s)
	var key := "%s|%s|%s" % [role, str(spec.get("act", "")), str(spec.get("face", ""))]
	for rid in stage.crowds:
		var c := stage.crowds[rid] as StoryCrowd
		if not c.actors.has(aid):
			continue
		var cur_src := c.directing(aid, t)
		if str(m.get("key_act", "")) == key and (cur_src == "choice" or spec.is_empty()):
			return  # (told already and still doing it; a story beat that took the person over and ended hands them back here)
		if spec.is_empty():
			c.stand_down(aid, "choice")
			m["key_act"] = key
			return
		var fresh := float(o["since_role_s"]) < beat_s or float(o["since_touch_s"]) < beat_s
		if cur_src == "outcome" or (cur_src == "cast" and not fresh):
			return  # (an outcome's act or a story beat first; this tries again next frame)
		c.ensure_present(aid)
		if c.direct_actor(aid, str(spec.get("act", "")), str(spec.get("face", "")), t, t + RunActing.STATE_S, str(spec.get("look_at", "")), "choice"):
			m["key_act"] = key
		return


## The `states` steps of an option's role: pieces and directed people once per role change, billboards and props every frame.
func _play_steps(id: String, st: Dictionary, role: String, touched_now: bool, foot: Vector3, u: float, t: float) -> void:
	var steps := ChoiceStaging.steps(st, role, touched_now)
	var m: Dictionary = _mem[id]
	var key := "%s|%s" % [role, str(touched_now)]
	var once := str(m.get("key_steps", "")) != key
	m["key_steps"] = key
	var i := 0
	for s in steps:
		var sp: Dictionary = s
		i += 1
		if sp.has("piece"):
			if once:
				stage.apply({"t0": t, "action": "piece_on" if str(sp["op"]) == "on" else "piece_off", "args": {"piece": str(sp["piece"])}})
		elif sp.has("actor"):
			if once:
				for rid in stage.crowds:
					var c := stage.crowds[rid] as StoryCrowd
					if c.actors.has(str(sp["actor"])):
						c.ensure_present(str(sp["actor"]))
						c.direct_actor(str(sp["actor"]), str(sp.get("act", "")), str(sp.get("face", "")), t, t + RunActing.STATE_S, str(sp.get("look_at", "")), "choice")
				var extra: Array = m.get("extra_actors", [])
				if not extra.has(str(sp["actor"])):
					extra.append(str(sp["actor"]))
				m["extra_actors"] = extra
		elif sp.has("thing"):
			var mo := ChoiceStaging.motion(str(sp.get("motion", "still")), u)
			if sp.has("tex"):
				mo["tex"] = ChoiceProps.tex(str(sp["tex"]))
			elif sp.has("sprite") and stage.assets != null:  # a frame of the map's own art (a sibling sprite of the thing: the bar lifted, the receiver off the hook)
				mo["tex"] = stage.assets.sprite(str(sp["sprite"])).get("tex", null)
			stage.world.thing_pose[str(sp["thing"])] = mo
		elif sp.has("prop") and props != null:
			var at: Array = sp.get("at", [0.0, 0.0, 0.0])
			var mo2 := ChoiceStaging.motion(str(sp.get("motion", "still")), u)
			props.put("%s#prop%d" % [id, i], str(sp["prop"]), foot + Vector3(float(at[0]) + float(mo2["dx"]), float(at[1]) + float(mo2["dy"]), float(at[2])), float(sp.get("size", 1.0)) * float(mo2["sy"]), 0.9)


func _piece(id: String, on_id: String, off_id: String, t: float) -> void:
	var m: Dictionary = _mem[id]
	if str(m.get("piece_on", "")) == on_id:
		return
	stage.apply({"t0": t, "action": "piece_on", "args": {"piece": on_id}})
	stage.apply({"t0": t, "action": "piece_off", "args": {"piece": off_id}})
	m["piece_on"] = on_id


## An option that is no longer staged lets go of what it held: its people's acts, its billboard's pose.
func _forget(id: String) -> void:
	var m: Dictionary = _mem.get(id, {})
	_mem.erase(id)
	if stage == null:
		return
	var who: Array = (m.get("extra_actors", []) as Array).duplicate()
	if str(m.get("actor", "")) != "":
		who.append(str(m["actor"]))
	for aid in who:
		for rid in stage.crowds:
			(stage.crowds[rid] as StoryCrowd).stand_down(str(aid), "choice")
	if stage.world != null and str(m.get("thing", "")) != "":
		stage.world.thing_pose.erase(str(m["thing"]))


## Clears the choice layer: every act of the layer stood down, every billboard pose dropped (a new scene, or no choice on show).
func clear_choice() -> void:
	for id in _mem.keys():
		_forget(str(id))
	_mem = {}
	if stage != null and stage.world != null:
		stage.world.thing_pose = {}
