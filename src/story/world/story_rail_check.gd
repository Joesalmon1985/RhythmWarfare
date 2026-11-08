class_name StoryRailCheck
extends RefCounted
## The rail-path check (docs/story/HEIGHTS_AND_PATHS.md): a rail move is data, and a move that would cross a wall, a railing, a drop that is not a step or a void is a data
## error found here, never a glitch at run time. A move is checked the way StoryPlayer plays it:
##   * every straight leg of a `via` / `path` polyline is traced through the map (StoryMap.trace_segment): it may only cross portals that are open to walkers, into sectors
##     that are not voids, over floor changes that are steps for its style, through openings with room for the eye;
##   * a plain move follows StoryMap.route (portal midpoints): each portal it crosses is checked the same way;
##   * the move is played on a StoryPlayer (reduced motion: no bob, no drift) and sampled EYE_SAMPLES times: the camera stays in a walkable sector, never in a void, and its eye
##     stays within [EYE_MIN, EYE_MAX] metres above the local floor and below the ceiling. The local floor is the floor of the sector under the camera, except across a step,
##     where it is the stair line: the straight line from one floor to the other over the same span the player's eye ramps over (StoryPlayer.ramp_span);
##   * a choice viewpoint (a rail place with "choice": true) holds for at least RunRail.CHOICE_HOLD_BARS (the whole choice window): a choice viewpoint with no hold is an error.

const EYE_MIN := 1.4
const EYE_MAX := 1.8
const HEADROOM := 0.1  # metres between the eye and the ceiling
const EYE_SAMPLES := 96


## Errors of one move from waypoint `from_wp` with player_move args {to, via?, path?, style?, bars?}. `where` prefixes every message.
static func check_move(map: StoryMap, from_wp: String, args: Dictionary, where: String) -> Array:
	var errors: Array = []
	var a := args.duplicate()
	var via: Array = StoryPlayer.via_of(a)
	var to := StoryPlayer.target_of(a)
	var style := str(a.get("style", "walk"))
	if not map.has_waypoint(from_wp):
		return ["%s: starts at %s, which is not a waypoint" % [where, from_wp]]
	for wid in via + [to]:
		if not map.has_waypoint(str(wid)):
			errors.append("%s: %s is not a waypoint" % [where, wid])
	if not errors.is_empty():
		return errors
	for wid in [from_wp] + via + [to]:
		if map.is_void(str(map.waypoint(str(wid))["sector"])):
			errors.append("%s: waypoint %s stands in a void" % [where, wid])
	if not via.is_empty():  # every straight leg of the polyline
		var chain: Array = [from_wp] + via + [to]
		for i in range(1, chain.size()):
			var wa := map.waypoint(str(chain[i - 1]))
			var wb := map.waypoint(str(chain[i]))
			var tr := map.trace_segment(wa["at"], wb["at"], str(wa["sector"]), style)
			for e in tr["errors"]:
				errors.append("%s: leg %s to %s %s" % [where, chain[i - 1], chain[i], e])
	else:
		var wa2 := map.waypoint(from_wp)
		var wb2 := map.waypoint(to)
		var r := map.route(wa2["at"], str(wa2["sector"]), wb2["at"], str(wb2["sector"]))
		var legs: Array = r["sectors"]
		if (r["points"] as PackedVector2Array).size() < 2:
			errors.append("%s: no route from %s to %s" % [where, from_wp, to])
		for k in range(1, legs.size()):
			if str(legs[k]) == str(legs[k - 1]):
				continue
			var fc := map.floor_change(str(legs[k - 1]), str(legs[k]), style)
			if str(fc["kind"]) in ["drop", "void"]:
				errors.append("%s: the route from %s to %s crosses a %s from %s to %s (%.2f m, style %s)" % [where, from_wp, to, fc["kind"], legs[k - 1], legs[k], float(fc["dh"]), style])
	if not errors.is_empty():
		return errors
	errors.append_array(eye_samples(map, from_wp, a, where))
	return errors


## The move played on a StoryPlayer, sampled: the camera's sector and its eye above the local floor (see the header).
static func eye_samples(map: StoryMap, from_wp: String, args: Dictionary, where: String) -> Array:
	var errors: Array = []
	var p := StoryPlayer.new()
	p.setup(map, 120.0)
	p.start_at = from_wp
	p.reset()
	p.reduced = true
	p.drift_on = false
	var a := args.duplicate()
	a["bars"] = maxf(float(a.get("bars", 3.0)), 0.25)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": a})
	for e in p.errors:
		errors.append("%s: %s" % [where, e])
	var ev: Dictionary = p.move_plan(0.0)
	if ev.is_empty():
		return errors + ["%s: the move was not planned" % where]
	var t1 := float(ev["t1"])
	var bad := 0
	for k in EYE_SAMPLES + 1:
		var t := t1 * float(k) / float(EYE_SAMPLES)
		var pose := p.pose_at(t)
		var pos: Vector2 = pose["pos"]
		var sid := map.sector_at(pos)
		var why := ""
		if sid == "":
			why = "outside every sector"
		elif map.is_void(sid):
			why = "in the void %s" % sid
		else:
			var ref := stair_floor(map, ev, StoryPlayer.distance_at(ev, t), sid)
			var eye := (pose["cam"] as Vector3).y
			var above := eye - ref
			if above < EYE_MIN - 1.0e-4 or above > EYE_MAX + 1.0e-4:
				why = "the eye is %.2f m above the floor (%.1f to %.1f)" % [above, EYE_MIN, EYE_MAX]
			elif eye > float(map.sector(sid)["ceiling"]) - HEADROOM:
				why = "the eye is in the ceiling of %s" % sid
		if why != "":
			bad += 1
			if bad <= 3:
				errors.append("%s: at %.0f%% of the move (%.2f, %.2f) %s" % [where, 100.0 * float(k) / EYE_SAMPLES, pos.x, pos.y, why])
	if bad > 3:
		errors.append("%s: ... and %d more samples" % [where, bad - 3])
	return errors


## The local floor at distance d along a planned move: the floor of `sid`, or across a step the stair line over the span the player's eye ramps over.
static func stair_floor(map: StoryMap, ev: Dictionary, d: float, sid: String) -> float:
	var legs: Array = ev["legs"]
	var cum: Array = ev["cum"]
	var ramp := float(StoryPlayer.STYLES.get(str(ev["style"]), StoryPlayer.STYLES["walk"])["ramp"])
	for k in range(1, legs.size()):
		var hb := float(map.sector(str(legs[k - 1])).get("floor", 0.0))
		var ha := float(map.sector(str(legs[k])).get("floor", 0.0))
		if absf(ha - hb) < 1.0e-4:
			continue
		var before := float(cum[k]) - float(cum[k - 1])
		var after := float(cum[k + 1]) - float(cum[k]) if k + 1 < cum.size() else INF
		var half := StoryPlayer.ramp_span(ramp, before, after)
		var at := float(cum[k])
		if absf(d - at) <= half:
			return lerpf(hb, ha, (d - (at - half)) / (2.0 * half))
	return float(map.sector(sid).get("floor", 0.0))


## Every move a run scene's rail can make ({from, args, where}): home to the first good and bad places, up the good rail, down and back along the bad rail (a back move
## reverses the leg's `via`), a good place's drop to the bad rail, the arrival walk, and each of the scene's `routes` (the polyline moves out to the thresholds and back).
static func rail_moves(node_id: String, home: String, rail: Dictionary) -> Array:
	var out: Array = []
	var good: Array = rail.get("good", [])
	var bad: Array = rail.get("bad", [])
	var prev := home
	for i in good.size():
		var g: Dictionary = good[i]
		out.append({"from": prev, "args": g, "where": "%s good %d (%s to %s)" % [node_id, i + 1, prev, g["to"]]})
		if not bad.is_empty():
			out.append({"from": str(g["to"]), "args": {"to": str(bad[0]["to"]), "style": str(bad[0].get("style", "walk"))}, "where": "%s drop from %s" % [node_id, g["to"]]})
		prev = str(g["to"])
	prev = home
	for j in bad.size():
		var b: Dictionary = bad[j]
		out.append({"from": prev, "args": b, "where": "%s bad %d (%s to %s)" % [node_id, j + 1, prev, b["to"]]})
		var back := {"to": prev, "style": "walk"}
		if b.has("via"):
			var rv: Array = (b["via"] as Array).duplicate()
			rv.reverse()
			back["via"] = rv
		out.append({"from": str(b["to"]), "args": back, "where": "%s back %d (%s to %s)" % [node_id, j + 1, b["to"], prev]})
		prev = str(b["to"])
	if str(rail.get("arrive", "")) != "" and str(rail["arrive"]) != home:
		out.append({"from": str(rail["arrive"]), "args": {"to": home, "style": "walk"}, "where": "%s arrival (%s to %s)" % [node_id, rail["arrive"], home]})
	var routes: Variant = rail.get("routes", {})  # the routes out and in (rail.routes: {name: a move spec {to, via?, style?, bars?, from?}}), each from `from` or home
	if typeof(routes) == TYPE_DICTIONARY:
		for k in (routes as Dictionary):
			var spec: Variant = routes[k]
			if typeof(spec) == TYPE_DICTIONARY and (spec as Dictionary).has("to"):
				var from_wp := str((spec as Dictionary).get("from", home))
				out.append({"from": from_wp, "args": spec, "where": "%s route %s (%s to %s)" % [node_id, k, from_wp, spec["to"]]})
	return out


## Errors of a run scene's rail on its map: every move (check_move) and every choice viewpoint's hold.
static func check_rail(map: StoryMap, node_id: String, home: String, rail: Dictionary) -> Array:
	var errors: Array = []
	for key in ["good", "bad"]:
		for p in rail.get(key, []):
			if typeof(p) == TYPE_DICTIONARY and bool(p.get("choice", false)) and float(p.get("hold_bars", 0.0)) < RunRail.CHOICE_HOLD_BARS - 1.0e-6:
				errors.append("%s: the choice viewpoint %s holds %.1f bars; a choice viewpoint holds at least %.1f (the whole choice window)" % [node_id, p.get("to", "?"), float(p.get("hold_bars", 0.0)), RunRail.CHOICE_HOLD_BARS])
	for mv in rail_moves(node_id, home, rail):
		errors.append_array(check_move(map, str(mv["from"]), mv["args"], str(mv["where"])))
	return errors


## The walk-outs of run scene `n` (a run.json node; `place` its place block, `world_of` node id -> world, `bpm` the run's tempo), LEAD_RULINGS 42: every route of rail.routes whose
## `next` entry leads to another world, measured from the scene's choice viewpoint (else its home) along its authored leg (RunRail.leg_length), with the bars it gets (the authored
## bars clamped 2 to 4, or more when they would walk it faster than RunRail.WALK_PACE_MAX: RunRail.walk_off_bars, at most 8) and the pace, and `warn` when it would need more than
## RunRail.WALK_OFF_BARS_MAX bars at that pace (the scene's fault): [{dir, from, to, length (-1 unknown), bars, pace, need, warn}].
static func walk_offs(map: StoryMap, n: Dictionary, place: Dictionary, world_of: Dictionary, bpm: float) -> Array:
	var out: Array = []
	var rail: Dictionary = place.get("rail", {})
	var routes: Dictionary = rail.get("routes", {}) if typeof(rail.get("routes")) == TYPE_DICTIONARY else {}
	var from := RunRail.walk_off_from(rail, str(place.get("waypoint", "")))
	var bar := 4.0 * 60.0 / bpm
	for e in n.get("next", []):
		var dir := str(e.get("dir", ""))
		if dir == "down" or not routes.has(dir) or typeof(routes[dir]) != TYPE_DICTIONARY or str(world_of.get(str(e.get("to", "")), "")) == str(n.get("world", "")):
			continue
		var mv: Dictionary = routes[dir]
		var length := RunRail.leg_length(map, from, mv)
		var b := clampf(float(mv.get("bars", 3.0)), RunRail.MOVE_BARS_MIN, RunRail.MOVE_BARS_MAX)
		if length > RunRail.WALK_PACE_MAX * b * bar + 1.0e-6:
			b = maxf(b, RunRail.walk_off_bars(length, bar))
		var need := RunRail.walk_off_bars_needed(length, bar) if length >= 0.0 else 0.0
		out.append({"dir": dir, "from": from, "to": str(mv.get("to", "")), "length": length, "bars": b, "pace": length / (b * bar) if length >= 0.0 else 0.0, "need": need, "warn": need > RunRail.WALK_OFF_BARS_MAX})
	return out
