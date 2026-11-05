class_name StoryPlayer
extends RefCounted
## The player's rail camera (docs/STORY_25D_PLAN.md section 4): the authored journey through a StoryMap as a pure function of song time. Pure logic: no
## nodes, no renderer, no clock of its own. The director's actions are scheduled with their exact song times (player_move, player_look, player_role,
## fx_queasy, sick_beat); pose_at(t) then gives the same answer at any frame step, after a pause or after a restart.
##
## A move walks the route StoryMap.route() finds over the portals, to the waypoint, easing in and out, arriving at the waypoint's yaw; the eye height
## follows the floors (a ramp around each portal: a climb takes a longer one). Walk, stagger, run, climb and carried add a bob locked to the beat
## (footfalls on the beat, two per beat running), strongest mid-move. Reduced motion keeps the path but drops bob, roll and sway.
## The head turn (StoryFreeLook) is player input and is added by the node that applies the pose.

const STYLES := {  # vertical dip m, sideways m, roll deg, footfalls per beat, ground ramp half-width m, speed feel
	"walk": {"v": 0.045, "h": 0.03, "roll": 0.35, "rate": 1.0, "ramp": 0.8},
	"stagger": {"v": 0.05, "h": 0.09, "roll": 2.5, "rate": 0.5, "ramp": 0.8},
	"run": {"v": 0.08, "h": 0.04, "roll": 0.6, "rate": 2.0, "ramp": 0.8},
	"climb": {"v": 0.05, "h": 0.03, "roll": 0.5, "rate": 1.0, "ramp": 1.6},
	"carried": {"v": 0.02, "h": 0.05, "roll": 1.2, "rate": 0.5, "ramp": 0.8},
}
const CROUCH_M := 0.55  # eye drop with the head down (sick_beat)

var map: StoryMap
var bpm := 174.0
var reduced := false
var drift_on := true  # the idle head drift (also off whenever `reduced`)
var cut := false  # camera motion "none": a move or a turn cuts to its end half way through instead of travelling
var errors: Array = []

var _events: Array = []  # sorted by t0: {kind: move|look, t0, t1, seq, ...}
var _roles: Array = []  # {t0, role}
var _queasy: Array = []  # {t0, t1, amount}
var _sick: Array = []  # {t0, t1}
var _glances: Array = []  # {t0, t1, by, pitch}: authored head turns (yaw `by` and/or pitch up) on top of the rail's facing
var _faces: Array = []  # {t0, t1, pts: [Vector4 (x, z, 1 for the one to keep, height or NAN)], turn_s, release_s}: the head held on points of the room (player_look `face`), whatever the rail does underneath
var _seq := 0


func setup(p_map: StoryMap, p_bpm: float) -> void:
	map = p_map
	bpm = p_bpm
	reset()


func reset() -> void:
	_events = []
	_roles = []
	_queasy = []
	_sick = []
	_glances = []
	_faces = []
	_seq = 0
	errors = []


func bar_s() -> float:
	return 4.0 * 60.0 / bpm


func _initial_state() -> Dictionary:
	var w := map.start_waypoint()
	var sec := str(w.get("sector", ""))
	return {"pos": w.get("at", Vector2.ZERO), "sector": sec, "yaw": float(w.get("yaw", 0.0)), "ground": float(map.sector(sec).get("floor", 0.0))}


## Schedules one director action (the five journey actions); returns true when it was one of them. `a` = {t0, action, args}.
func apply_action(a: Dictionary) -> bool:
	var t0 := float(a["t0"])
	var args: Dictionary = a["args"]
	var dur := float(args.get("bars", 2.0)) * bar_s()
	match str(a["action"]):
		"player_move":
			_add({"kind": "move", "t0": t0, "t1": t0 + maxf(dur, 0.001), "to": str(args.get("to", "")), "style": str(args.get("style", "walk"))})
		"player_walk":  # a walk inside a room (relative to where the rail is when it starts): see _plan_walk
			_add({"kind": "move", "walk": args.duplicate(), "t0": t0, "t1": t0 + maxf(dur, 0.001), "to": str(args.get("to", "")), "style": str(args.get("style", "walk"))})
		"player_look":
			if args.has("face"):  # [[x, z, keep, height], ...]: the head turns to the best facing over these points (best_facing) over `turn_bars`, holds it from wherever the rail walks, hands back over `release_bars`
				var pts: Array = []
				for f in args["face"]:
					var fa: Array = f
					pts.append(Vector4(float(fa[0]), float(fa[1]), float(fa[2]) if fa.size() > 2 else 0.0, float(fa[3]) if fa.size() > 3 else NAN))
				var tot := maxf(dur, 0.001)
				var turn := clampf(float(args.get("turn_bars", 1.0)) * bar_s(), 0.001, tot)
				_faces.append({"t0": t0, "t1": t0 + tot, "pts": pts, "turn_s": turn, "release_s": clampf(float(args.get("release_bars", 1.0)) * bar_s(), 0.001, tot)})
				return true
			if args.has("by") or args.has("pitch"):  # a glance: the head turns `by` degrees (and tips `pitch` up, negative down) from wherever the rail faces and comes back; it never touches the route
				_glances.append({"t0": t0, "t1": t0 + maxf(dur, 0.001), "by": float(args.get("by", 0.0)), "pitch": float(args.get("pitch", 0.0))})
				return true
			_add({"kind": "look", "t0": t0, "t1": t0 + maxf(dur, 0.001), "at": str(args.get("at", "")), "yaw": args.get("yaw", null), "in": args.get("in", [])})
		"player_role":
			_roles.append({"t0": t0, "role": str(args.get("role", "dancer")), "seq": _seq})
			_seq += 1
			_roles.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["t0"] < y["t0"] if x["t0"] != y["t0"] else x["seq"] < y["seq"])
		"fx_queasy":
			_queasy.append({"t0": t0, "t1": t0 + maxf(dur, 0.001), "amount": clampf(float(args.get("amount", 0.5)), 0.0, 1.0), "seq": _seq})
			_seq += 1
			_queasy.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["t0"] < y["t0"] if x["t0"] != y["t0"] else x["seq"] < y["seq"])
		"sick_beat":
			_sick.append({"t0": t0, "t1": t0 + float(args.get("bars", 4.0)) * bar_s()})
		_:
			return false
	return true


func _add(ev: Dictionary) -> void:
	ev["seq"] = _seq
	_seq += 1
	_events.append(ev)
	_events.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["t0"] < y["t0"] if x["t0"] != y["t0"] else x["seq"] < y["seq"])
	_rebuild()


## Every event starts from where the one before it had got to at that moment (so a move can interrupt a move, and events may arrive out of order).
func _rebuild() -> void:
	errors = []
	var st := _initial_state()
	var prev: Dictionary = {}
	for ev in _events:
		ev["skip"] = false
		if not prev.is_empty():
			st = _state_in(prev, float(ev["t0"]))
		ev["start"] = st
		if ev["kind"] == "move" and ev.has("walk"):
			_plan_walk(ev)
			if not ev["skip"] and not prev.is_empty() and prev["kind"] == "move" and float(ev["t0"]) < float(prev["t1"]):
				ev["skip"] = true  # a stroll never interrupts a journey move that is still under way
		elif ev["kind"] == "move":
			_plan_move(ev)
		else:
			_plan_look(ev)
		if ev["skip"]:
			continue  # a skipped event is not part of the chain: the next one starts from the last real one
		prev = ev


func _plan_move(ev: Dictionary) -> void:
	var st: Dictionary = ev["start"]
	var target: Dictionary = map.waypoint(str(ev["to"]))
	if target.is_empty():
		errors.append("player_move to unknown waypoint %s" % ev["to"])
		ev["route"] = PackedVector2Array([st["pos"], st["pos"]])
		ev["legs"] = [st["sector"]]
		ev["end_yaw"] = st["yaw"]
		ev["end_sector"] = st["sector"]
		ev["cum"] = [0.0, 0.0]
		return
	var r := map.route(st["pos"], str(st["sector"]), target["at"], str(target["sector"]))
	if (r["points"] as PackedVector2Array).size() < 2:
		errors.append("no route from %s to %s" % [st["sector"], target["sector"]])
		r = {"points": PackedVector2Array([st["pos"], target["at"]]), "sectors": [target["sector"]], "length": (st["pos"] as Vector2).distance_to(target["at"])}
	ev["route"] = r["points"]
	ev["legs"] = r["sectors"]
	ev["end_yaw"] = float(target["yaw"])
	ev["end_sector"] = str(target["sector"])
	var cum: Array = [0.0]
	var pts: PackedVector2Array = r["points"]
	for i in range(1, pts.size()):
		cum.append(float(cum[i - 1]) + pts[i - 1].distance_to(pts[i]))
	ev["cum"] = cum


## An in-room walk (player_walk): resolved from the rail's own state when it starts, so it follows whatever branch the player is on and never drags them
## into a room they are not in. Args: `to` (a waypoint or an actor's home) or `fwd` / `right` metres relative to the facing; `stop` metres short of `to`;
## `face` (a waypoint or actor to turn towards at the end) or `turn` degrees; `in` (a room or sector, or a list of them: the walk only happens while the rail is in
## one of them, otherwise it does nothing at all; a stroll also never interrupts a journey move still under way). A relative walk is shortened until it ends inside the sector with a margin from the walls; the whole walk stays in the starting
## sector (a `to` walk may cross doors: it follows the portal route).
func _plan_walk(ev: Dictionary) -> void:
	var st: Dictionary = ev["start"]
	var a: Dictionary = ev["walk"]
	var pos: Vector2 = st["pos"]
	var sec := str(st["sector"])
	var hold := func() -> void:
		ev["route"] = PackedVector2Array([pos, pos])
		ev["legs"] = [sec]
		ev["end_yaw"] = float(st["yaw"])
		ev["end_sector"] = sec
		ev["cum"] = [0.0, 0.0]
	var rooms: Array = []
	if a.has("in"):
		rooms = a["in"] if typeof(a["in"]) == TYPE_ARRAY else [str(a["in"])]
	if not rooms.is_empty() and map.room_of(sec) not in rooms and sec not in rooms:
		hold.call()
		ev["skip"] = true  # not in the room it was written for: it does nothing at all
		return
	var target := pos
	var tsec := sec
	var end_yaw := float(st["yaw"])
	if str(a.get("to", "")) != "":
		var tp := _point_of(str(a["to"]))
		if tp.is_empty():
			errors.append("player_walk to unknown %s" % a["to"])
			hold.call()
			return
		target = tp["at"]
		if float(a.get("stop", 0.0)) > 0.0 and target.distance_to(pos) > 0.01:
			target -= (target - pos).normalized() * minf(float(a["stop"]), target.distance_to(pos))
		tsec = map.sector_at(target)
		if tsec == "":
			tsec = str(tp["sector"])
		if map.has_waypoint(str(a["to"])) and not a.has("face") and not a.has("turn"):
			end_yaw = float(map.waypoint(str(a["to"]))["yaw"])
	else:
		var off := map.forward_of_yaw(float(st["yaw"])) * float(a.get("fwd", 0.0)) + StoryProjector.right(float(st["yaw"])) * float(a.get("right", 0.0))
		var k := 1.0
		while k > 0.0 and not map.inside(pos + off * k, sec, 0.4):
			k -= 0.1
		target = pos + off * maxf(k, 0.0)
	var r := {"points": PackedVector2Array([pos, target]), "sectors": [tsec], "length": pos.distance_to(target)}
	if tsec != sec:
		r = map.route(pos, sec, target, tsec)
		if (r["points"] as PackedVector2Array).size() < 2:
			errors.append("no route from %s to %s" % [sec, tsec])
			hold.call()
			return
	if a.has("face"):
		var fp := _point_of(str(a["face"]))
		if fp.is_empty():
			errors.append("player_walk face unknown %s" % a["face"])
		elif (fp["at"] as Vector2).distance_to(target) > 0.01:
			var d: Vector2 = fp["at"] - target
			end_yaw = rad_to_deg(atan2(-d.x, -d.y))
	elif a.has("turn"):
		end_yaw = float(st["yaw"]) + float(a["turn"])
	ev["route"] = r["points"]
	ev["legs"] = r["sectors"]
	ev["end_yaw"] = end_yaw
	ev["end_sector"] = tsec
	var cum: Array = [0.0]
	var pts: PackedVector2Array = r["points"]
	for i in range(1, pts.size()):
		cum.append(float(cum[i - 1]) + pts[i - 1].distance_to(pts[i]))
	ev["cum"] = cum


## {at, sector} of a waypoint or of an actor's home, or {}.
func _point_of(id: String) -> Dictionary:
	if map.has_waypoint(id):
		return map.waypoint(id)
	var h := map.home(id)
	return h


func _plan_look(ev: Dictionary) -> void:
	var st: Dictionary = ev["start"]
	var yaw := float(st["yaw"])
	var rooms: Variant = ev.get("in", [])
	if typeof(rooms) != TYPE_ARRAY:
		rooms = [str(rooms)]
	if not (rooms as Array).is_empty() and map.room_of(str(st["sector"])) not in rooms and str(st["sector"]) not in rooms:
		ev["skip"] = true  # written for another room: it does nothing
		ev["end_yaw"] = yaw
		ev["end_sector"] = st["sector"]
		return
	if ev["yaw"] != null:
		yaw = float(ev["yaw"])
	elif str(ev["at"]) != "":
		var p := Vector2.ZERO
		var found := false
		if map.has_waypoint(str(ev["at"])):
			p = map.waypoint(str(ev["at"]))["at"]
			found = true
		elif not map.home(str(ev["at"])).is_empty():
			p = map.home(str(ev["at"]))["at"]
			found = true
		if found and (p - (st["pos"] as Vector2)).length() > 0.01:
			var d: Vector2 = p - (st["pos"] as Vector2)
			yaw = rad_to_deg(atan2(-d.x, -d.y))
		elif not found:
			errors.append("player_look at unknown %s" % ev["at"])
	ev["end_yaw"] = yaw
	ev["end_sector"] = st["sector"]


static func _smooth(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)


static func _lerp_yaw(a: float, b: float, e: float) -> float:
	return a + wrapf(b - a, -180.0, 180.0) * e


## {pos, sector, yaw, ground} of the rail while event `ev` is the latest one, at time t.
func _state_in(ev: Dictionary, t: float) -> Dictionary:
	var st: Dictionary = ev["start"]
	var u := clampf((t - float(ev["t0"])) / (float(ev["t1"]) - float(ev["t0"])), 0.0, 1.0)
	var e := _smooth(u)
	if cut:
		e = 0.0 if u < 0.5 else 1.0
	if ev["kind"] == "look":
		return {"pos": st["pos"], "sector": st["sector"], "yaw": _lerp_yaw(float(st["yaw"]), float(ev["end_yaw"]), e), "ground": st["ground"]}
	var pts: PackedVector2Array = ev["route"]
	var cum: Array = ev["cum"]
	var total := float(cum[cum.size() - 1])
	var d := e * total
	var leg := 0
	while leg < pts.size() - 2 and d > float(cum[leg + 1]):
		leg += 1
	var seg := float(cum[leg + 1]) - float(cum[leg])
	var pos: Vector2 = pts[leg].lerp(pts[leg + 1], clampf((d - float(cum[leg])) / seg, 0.0, 1.0) if seg > 1.0e-6 else 1.0)
	var sector := str((ev["legs"] as Array)[mini(leg, (ev["legs"] as Array).size() - 1)])
	if u >= 1.0:
		pos = pts[pts.size() - 1]
		sector = str(ev["end_sector"])
	return {"pos": pos, "sector": sector, "yaw": _lerp_yaw(float(st["yaw"]), float(ev["end_yaw"]), e), "ground": _ground(ev, d)}


## Floor height under the walker after d metres of the route: each portal crossed changes the floor over a smooth ramp centred on the portal.
func _ground(ev: Dictionary, d: float) -> float:
	var st: Dictionary = ev["start"]
	var legs: Array = ev["legs"]
	var cum: Array = ev["cum"]
	var ramp_half: float = STYLES.get(str(ev["style"]), STYLES["walk"])["ramp"]
	var h0 := float(map.sector(str(legs[0])).get("floor", 0.0))
	var h := h0
	var off := float(st["ground"]) - h0  # the height we started at, if not on a floor (a move interrupted on a ramp)
	if absf(off) > 1.0e-6:
		h += off * (1.0 - _smooth(d / ramp_half))
	for k in range(1, legs.size()):
		var hb := float(map.sector(str(legs[k - 1])).get("floor", 0.0))
		var ha := float(map.sector(str(legs[k])).get("floor", 0.0))
		var at := float(cum[k])
		var before := float(cum[k]) - float(cum[k - 1])
		var after := float(cum[k + 1]) - float(cum[k]) if k + 1 < cum.size() else INF
		var half := minf(ramp_half, 0.45 * minf(before, after))
		half = maxf(half, 0.05)
		h += (ha - hb) * _smooth((d - (at - half)) / (2.0 * half))
	return h


func _event_at(t: float) -> Dictionary:
	var found: Dictionary = {}
	for ev in _events:
		if float(ev["t0"]) <= t:
			if not bool(ev.get("skip", false)):
				found = ev
		else:
			break
	return found


func role_at(t: float) -> String:
	var r := "dancer"
	for x in _roles:
		if float(x["t0"]) <= t:
			r = str(x["role"])
		else:
			break
	return r


## The queasy look 0..1 at t: each fx_queasy eases from the level before it to its amount over its bars and holds.
func queasy_at(t: float) -> float:
	var level := 0.0
	for x in _queasy:
		if t < float(x["t0"]):
			break
		var u := _smooth((t - float(x["t0"])) / (float(x["t1"]) - float(x["t0"])))
		level = lerpf(level, float(x["amount"]), u)
	return level


## How much of the pad strip is the DJ deck (1) and how much the dancer's floor-tile rail (0) at song time t: a cross-fade of DECK_FADE_S after each role change.
const DECK_FADE_S := 1.5


static func role_is_deck(role: String) -> bool:
	return role == "on_stage" or role == "dj"


func deck_mix_at(t: float) -> float:
	var prev := 0.0  # the dancer rail is the start
	var cur := 0.0
	var t0 := -INF
	for x in _roles:
		if float(x["t0"]) > t:
			break
		prev = cur
		cur = 1.0 if role_is_deck(str(x["role"])) else 0.0
		t0 = float(x["t0"])
	return lerpf(prev, cur, _smooth((t - t0) / DECK_FADE_S))


## 0..1 head-down envelope inside a sick_beat (eased in and out).
func sick_at(t: float) -> float:
	for x in _sick:
		if t >= float(x["t0"]) and t < float(x["t1"]):
			var u := (t - float(x["t0"])) / (float(x["t1"]) - float(x["t0"]))
			return _smooth(minf(u / 0.2, 1.0)) * _smooth(minf((1.0 - u) / 0.2, 1.0))
	return 0.0


## The head turn in degrees at t from the authored glances (player_look with `by`): each rises and falls smoothly over its bars.
func glance_at(t: float) -> float:
	var sum := 0.0
	for g in _glances:
		if t >= float(g["t0"]) and t < float(g["t1"]):
			var u := (t - float(g["t0"])) / (float(g["t1"]) - float(g["t0"]))
			var e := sin(PI * u)
			sum += float(g["by"]) * e * e
	return sum


## The head tipped up (positive) or down (negative) in degrees at t from the authored glances with a `pitch`.
func pitch_at(t: float) -> float:
	var sum := 0.0
	for g in _glances:
		if t >= float(g["t0"]) and t < float(g["t1"]):
			var u := (t - float(g["t0"])) / (float(g["t1"]) - float(g["t0"]))
			var e := sin(PI * u)
			sum += float(g["pitch"]) * e * e
	return clampf(sum, -35.0, 35.0)


## The idle head drift: a slow wander of the gaze (yaw, pitch in degrees) between the authored moves, a function of song time only. Off in reduced motion.
const DRIFT_YAW := 1.4
const DRIFT_PITCH := 0.7


static func drift_at(t: float) -> Vector2:
	return Vector2(DRIFT_YAW * (0.65 * sin(TAU * t / 13.7) + 0.35 * sin(TAU * t / 5.3 + 1.3)), DRIFT_PITCH * (0.6 * sin(TAU * t / 9.1 + 0.7) + 0.4 * sin(TAU * t / 3.9 + 2.1)))


const FACE_HALF_DEG := 36.0  # a `face` look holds its points within this much either side of the axis (the run's stage strip shows about 53)
const FACE_NEAR_M := 1.5  # nearer than this a point is at the player's feet, under the picture whatever the facing
const FACE_SMOOTH_BEATS := 1.0  # the facing is the mean of the best facings over the last beat, so a change of the best group is a turn, not a cut


## The facing (degrees) that holds the most of `pts` (Vector3 or Vector4: x, z, keep > 0.5 for the one that must be held) within FACE_HALF_DEG either side, standing at `from`: of the groups that fit,
## the one holding the kept point, then the most points, then the narrowest; aimed at the middle of the group. NAN when every point is at the player's feet. Pure.
static func best_facing(pts: Array, from: Vector2) -> float:
	var angs: Array = []
	for q in pts:
		var v: Vector4 = Vector4(q.x, q.y, q.z, 0.0) if q is Vector3 else q
		var d := Vector2(v.x, v.y) - from
		if d.length() < FACE_NEAR_M:
			continue
		angs.append(Vector2(rad_to_deg(atan2(-d.x, -d.y)), v.z))
	if angs.is_empty():
		return NAN
	var best_aim := 0.0
	var best_n := -1
	var best_keep := false
	var best_span := INF
	for c in angs:
		var lo: float = c.x
		var n := 0
		var keep := false
		var span := 0.0
		for q in angs:
			var off := fposmod(float(q.x) - lo, 360.0)
			if off <= 2.0 * FACE_HALF_DEG + 1.0e-4:
				n += 1
				keep = keep or float(q.y) > 0.5
				span = maxf(span, off)
		if best_n < 0 or (keep and not best_keep) or (keep == best_keep and n > best_n) or (keep == best_keep and n == best_n and span < best_span - 1.0e-4):
			best_n = n
			best_keep = keep
			best_span = span
			best_aim = lo + span * 0.5
	return best_aim


const FACE_TIP_MAX := 28.0  # how far a `face` look tips the head down for points below the picture (standing above them: a balcony, a stair)
const FACE_TIP_MARGIN := 18.0  # the lowest held point is kept this far inside the bottom of the picture (the picture shows 26 degrees below the axis)


## How far (degrees, 0 or negative) to tip the head so the lowest of `pts` held by `aim` is in the picture, from `from` at eye height `eye`. Points without a height are left out. Pure.
static func face_tip(pts: Array, from: Vector2, aim: float, eye: float) -> float:
	var lowest := 0.0
	for q in pts:
		if not (q is Vector4) or is_nan(float(q.w)):
			continue
		var d := Vector2(q.x, q.y) - from
		var dist := d.length()
		if dist < FACE_NEAR_M:
			continue
		if absf(wrapf(rad_to_deg(atan2(-d.x, -d.y)) - aim, -180.0, 180.0)) > FACE_HALF_DEG + 6.0:
			continue
		lowest = minf(lowest, rad_to_deg(atan2(float(q.w) - eye, dist)))
	return clampf(minf(0.0, lowest + FACE_TIP_MARGIN), -FACE_TIP_MAX, 0.0)


## The face look's facing at t: the best facing from where the rail is, averaged over the last FACE_SMOOTH_BEATS (deterministic: five samples of song time). NAN when none.
func _face_yaw(pts: Array, t: float) -> float:
	var sum := Vector2.ZERO
	var step := FACE_SMOOTH_BEATS * 60.0 / bpm / 4.0
	for k in 5:
		var tk := t - float(k) * step
		var ev := _event_at(tk)
		var pos: Vector2 = (_initial_state() if ev.is_empty() else _state_in(ev, tk))["pos"]
		var a := best_facing(pts, pos)
		if not is_nan(a):
			sum += StoryProjector.forward(a)
	if sum.length() < 1.0e-4:
		return NAN
	return rad_to_deg(atan2(-sum.x, -sum.y))


## How much a held `face` look owns the head at t (0 none, 1 fully on its points) and the points: {w, pts}. The latest one that is active wins.
func face_at(t: float) -> Dictionary:
	var out := {"w": 0.0, "pts": []}
	for f in _faces:
		var t0 := float(f["t0"])
		var t1 := float(f["t1"])
		if t < t0 or t >= t1:
			continue
		var w := minf(_smooth((t - t0) / float(f["turn_s"])), _smooth((t1 - t) / float(f["release_s"])))
		out = {"w": w, "pts": f["pts"]}
	return out


## True while an authored player_look is turning the head.
func look_active(t: float) -> bool:
	var ev := _event_at(t)
	return not ev.is_empty() and ev["kind"] == "look" and t < float(ev["t1"])


## The camera at song time t. {cam: Vector3, yaw, rail_yaw (the facing without a held `face` look), pitch, roll (degrees), pos: Vector2 (ground, without sway), sector, ground, moving, style, u, role, queasy, sick}.
func pose_at(t: float) -> Dictionary:
	var ev := _event_at(t)
	var st: Dictionary
	var moving := false
	var style := ""
	var u := 0.0
	if ev.is_empty():
		st = _initial_state()
	else:
		st = _state_in(ev, t)
		u = clampf((t - float(ev["t0"])) / (float(ev["t1"]) - float(ev["t0"])), 0.0, 1.0)
		if ev["kind"] == "move" and t < float(ev["t1"]):
			moving = true
			style = str(ev["style"])
	var role := role_at(t)
	var q := queasy_at(t)
	var sick := sick_at(t)
	var beats := t * bpm / 60.0
	var bob := Vector3.ZERO  # x sideways (m), y vertical (m), z roll (deg)
	if not reduced:
		if moving:
			var p: Dictionary = STYLES.get(style, STYLES["walk"])
			var env := sin(PI * u)
			var ph := PI * float(p["rate"]) * beats
			bob = Vector3(float(p["h"]) * sin(ph), -float(p["v"]) * absf(cos(ph)), float(p["roll"]) * sin(ph)) * env
			if style == "stagger":  # a lurch off the beat every few beats
				var lurch := pow(sin(TAU * beats / 6.0), 3.0)
				bob.x += 0.12 * lurch * env
				bob.z += 3.0 * lurch * env
		else:
			match role:
				"dancer", "recovered":
					bob = Vector3(0.012 * sin(PI * 0.5 * beats), -0.03 * absf(sin(PI * beats)), 0.25 * sin(PI * 0.5 * beats))
				"queasy", "sick":
					bob = Vector3(0.02 * sin(PI * 0.25 * beats), -0.02 * absf(sin(PI * 0.5 * beats)), 0.6 * sin(PI * 0.25 * beats))
				_:
					bob = Vector3(0.008 * sin(PI * 0.25 * beats), -0.012 * absf(sin(PI * 0.5 * beats)), 0.1 * sin(PI * 0.125 * beats))
		bob.x += 0.05 * q * sin(PI * 0.25 * beats)
		bob.z += 2.5 * q * sin(PI * 0.25 * beats + 1.0)
	var drift := Vector2.ZERO if reduced or not drift_on else drift_at(t)
	var rail_yaw := float(st["yaw"]) + glance_at(t)
	var yaw := rail_yaw
	var face_pitch := 0.0
	if not _faces.is_empty():
		var fc := face_at(t)
		var fy := _face_yaw(fc["pts"], t) if float(fc["w"]) > 0.0 else NAN
		if not is_nan(fy):
			var fw := float(fc["w"])
			if cut:
				fw = 0.0 if fw < 0.5 else 1.0
			yaw = _lerp_yaw(yaw, fy, fw)
			face_pitch = face_tip(fc["pts"], st["pos"], fy, float(st["ground"]) + map.eye_height) * fw
	yaw += drift.x
	var pitch := pitch_at(t) + drift.y + face_pitch
	var pos: Vector2 = st["pos"]
	var ground := float(st["ground"])
	var eye := ground + map.eye_height + bob.y - CROUCH_M * sick
	var side := StoryProjector.right(yaw) * bob.x
	return {"cam": Vector3(pos.x + side.x, eye, pos.y + side.y), "yaw": yaw, "rail_yaw": rail_yaw + drift.x, "pitch": pitch, "roll": bob.z, "pos": pos, "sector": str(st["sector"]), "ground": ground,
		"moving": moving, "style": style, "u": u, "role": role, "queasy": q, "sick": sick}


## The roles held in order of their start (the starting role, dancer, is not included).
func role_list() -> Array:
	var out: Array = []
	for x in _roles:
		out.append(str(x["role"]))
	return out


## Every journey event scheduled so far (for the tests and the journey log): [{kind, t0, t1, to?, style?}].
func events() -> Array:
	var out: Array = []
	for ev in _events:
		if not bool(ev.get("skip", false)):
			out.append({"kind": ev["kind"], "t0": ev["t0"], "t1": ev["t1"], "to": ev.get("to", ""), "style": ev.get("style", ""), "walk": ev.has("walk")})
	return out
