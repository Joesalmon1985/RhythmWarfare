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
##
## The choice layer (docs/CHOICE_CLARITY.md) plays on top: an option of a staged choice is lit green when it is the current choice and red when it is not (the same shapes, the colour only), and the
## thing itself shows its state (a person beckons or pleads, a door stands open or shut), so a staged option keeps its pool, ring and ripple on the floor but no shaft, glow or slit over the person or
## the door. An actor anchor acts from the moment it is on show (its `acting` block, else the crowd's own `wave`). A finished path's portal is the crown (a ring of light with three motes circling it).

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
const CURRENT_COL := Color(0.25, 1.0, 0.45)  # the choice layer: the current choice is lit green, any other option red
const OTHER_COL := Color(1.0, 0.32, 0.22)
const DIM_STAGED := 0.75  # a staged option that is not the current choice stays this bright while another is selected (the red must still read)

var items_fn: Callable  # () -> Array of {hotspot: Dictionary, state: "available" | "selected" | "committed", t_state: float (song time the state began)}
var pose_fn: Callable  # () -> {cam: Vector3, yaw, pitch} (empty: nothing to draw)
var now_fn: Callable  # () -> song time
var stage: StoryStage
var beat_s := 60.0 / 174.0
var tint := Color(1.0, 0.85, 0.5)  # the chapter palette's accent as light (see `light_tint`)
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
			var snap := choice_snapshot(_t)  # (the choice layer plays every frame the view is up, with hotspots on show or not: it also lets go of the world when the choice ends)
			_stage_choice(snap, _t)
			_manage_acting(items, _t, snap)
			if not items.is_empty():
				_set_camera(pose)
				_lay = layout(items, stage.map, stage.crowds, pose, size)
				_lay.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["depth"]) > float(b["depth"]))  # far first
				var opts: Dictionary = snap.get("options", {})
				_any_sel = false
				for e in _lay:
					if opts.has(str(e["id"])):
						e["role"] = str(opts[str(e["id"])]["role"])
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
		var entry := {"id": str(h["id"]), "hotspot": h, "state": str(e["state"]), "t_state": float(e.get("t_state", 0.0)), "world": p, "ground_y": float(r["ground"]), "actor": bool(r["actor"]), "edge": false, "ok": true,
			"finished": bool(e.get("finished", false))}
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


## An entry's colours [base, hot]: the world's light (`tint`), a finished path's portal its own tint (plan D10), and for a staged option of a choice the role: green when current, red when not.
func _colours_of(e: Dictionary) -> Array:
	var base := tint
	var finished := bool(e.get("finished", false))
	if finished:
		base = Color.html(str(((e["hotspot"]["look"] as Dictionary)["finished"] as Dictionary).get("tint", HotspotContract.FINISHED_TINT)))
	if high_contrast:
		base = Color(1.0, 1.0, 0.4)
	var role := str(e.get("role", ""))
	if role != "" and not finished and not high_contrast:
		base = CURRENT_COL if role == "current" or role == "committed" else OTHER_COL
	return [base, base.lerp(Color(1, 1, 1), 0.55)]


## The look of an entry: its `look.available`, or the finished portal's (crown).
func _look_of(e: Dictionary) -> String:
	var look: Dictionary = e["hotspot"]["look"]
	if bool(e.get("finished", false)):
		return str((look["finished"] as Dictionary).get("available", "crown"))
	return str(look["available"])


## The brighter, double-ringed one: the data's default, or in a staged choice the current option.
func _is_default(e: Dictionary) -> bool:
	if str(e.get("role", "")) != "" and not bool(e.get("finished", false)) and not high_contrast:
		return str(e["role"]) == "current"
	return bool(e["hotspot"]["default"])


## An option of a staged choice: the thing itself shows its state, so only floor light is drawn for it (no shaft, glow or slit over a person or a door).
func _staged(e: Dictionary) -> bool:
	return str(e.get("role", "")) != ""


## How strongly an entry is lit: dimmed while another hotspot is selected (a staged option less, so its red still reads), and its flicker.
func _strength(e: Dictionary) -> float:
	var k := (DIM_STAGED if _staged(e) else DIM_OTHERS) if (_any_sel and str(e["state"]) == "available") else 1.0
	if _look_of(e) == "flicker" and str(e["state"]) == "available" and not reduced:
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
	for e in _lay:
		var cols := _colours_of(e)
		if bool(e["edge"]):
			_draw_edge(e, cols[0], cols[1])
		else:
			_draw_marks(e, cols[0], cols[1])


# The light: pools on the floor, shafts, glows, the door's slit and the edge leaks, added to the picture.
func _draw_light() -> void:
	if _lay.is_empty():
		return
	for e in _lay:
		var cols := _colours_of(e)
		if bool(e["edge"]):
			_light_edge(e, cols[0], cols[1])
		else:
			_light_entry(e, cols[0], cols[1])


func _light_entry(e: Dictionary, base: Color, hot: Color) -> void:
	var h: Dictionary = e["hotspot"]
	var state := str(e["state"])
	var look := _look_of(e)
	var is_default := _is_default(e)
	var staged := _staged(e)
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
			if not staged:
				_glow(c, minf(r_m * sc * 0.6, size.y * GLOW_MAX), base, (0.32 + 0.28 * th + (0.12 if is_default else 0.0)) * k)
			if look == "crown":  # a finished path: a ring of light round the portal's heart, three motes circling it (the ring and the motes are the crisp pass)
				var orb := minf(r_m * sc * 0.62, size.y * GLOW_MAX)
				_glow(c, orb * 0.8, base, 0.45 + 0.3 * th)
				var spin := 0.0 if reduced else _t * TAU / (beat_s * 8.0)
				for i in 3:
					var ang := spin + TAU * float(i) / 3.0
					_glow(c + Vector2(cos(ang), sin(ang) * 0.55) * orb, maxf(5.0, sc * 0.16), base, 0.9)
		"selected":
			pool_a = 0.42 + 0.22 * th
			pool_col = hot
			shaft_a = 0.5 + 0.2 * th
			var lift := minf(u / 0.25, 1.0)
			lift = lift * lift * (3.0 - 2.0 * lift) * LIFT_M * sc
			if not staged:
				_glow(c + Vector2(0.0, -lift), minf(r_m * sc * 0.8, size.y * GLOW_MAX * 1.3), hot, 0.75 + 0.2 * th)
		"committed":
			var fk := clampf(u / FLASH_S, 0.0, 1.0)
			var settle := 1.0 - _smooth01((u - FLASH_S) / SETTLE_S)
			pool_a = 0.95 * (1.0 - fk) + 0.4 * settle * fk
			pool_col = Color(1, 1, 1).lerp(hot, fk)
			shaft_a = 0.6 * settle
			if not staged:  # (a staged option's commit is its door swinging wide and its people reacting: no flash over them)
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
	if staged:  # (the light stays on the floor and never covers a face or a door)
		shaft_a = 0.0
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
	if look == "open" and state != "committed" and not staged:  # a door ajar: a lit slit standing in the doorway, its light spilling across the floor toward the player
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
	var look := _look_of(e)
	var is_default := _is_default(e)
	var staged := _staged(e)
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
	var sel_col := hot if staged else white  # the touched ring is white-hot; a staged option's keeps its role colour (pale green) so it still reads as the current choice
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
			if look == "crown":  # a finished path: the ring round the portal's heart and three motes circling it
				var orb := minf(r_m * sc * 0.62, size.y * GLOW_MAX)
				var spin := 0.0 if reduced else _t * TAU / (beat_s * 8.0)
				draw_arc(c, orb, 0.0, TAU, 32, Color(OUTLINE.r, OUTLINE.g, OUTLINE.b, 0.6), 4.0)
				draw_arc(c, orb, 0.0, TAU, 32, Color(base.r, base.g, base.b, 0.6 + 0.3 * th), 2.0)
				for i in 3:
					var ang := spin + TAU * float(i) / 3.0
					var mp := c + Vector2(cos(ang), sin(ang) * 0.55) * orb
					_mote(self, mp, 4.0, OUTLINE)
					_mote(self, mp, 2.0, Color(hot.r, hot.g, hot.b, 1.0))
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
				draw_polyline(_ring, Color(sel_col.r, sel_col.g, sel_col.b, 0.92 + 0.08 * th), 3.0)
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
	var col := Color(1, 1, 1) if sel and not _staged(e) else hot
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
	var col := Color(1, 1, 1) if sel and not _staged(e) else hot
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
	_glow(c, R * 1.3, col, (0.6 + 0.35 * th) * k)


static func _smooth01(x: float) -> float:
	x = clampf(x, 0.0, 1.0)
	return x * x * (3.0 - 2.0 * x)


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
