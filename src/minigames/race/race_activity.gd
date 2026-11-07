class_name RaceActivity
extends MinigameActivity
## The street race every rave leads to (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 8 to 10, docs/bedsit/RACE.md; CONTRACTS.md 4, 5, 8, 10). OVERLAY mode: the pads stay live
## and judged, their judge events reach `on_judge` and feed the car's speed; the stage area's four screen regions are the driving choices (`tap("region:<top|bottom|left|right>")`).
##
## A pure, deterministic simulation in song time (no clock of its own, no node): `update(t)` integrates in fixed steps of `timing.dt` from the start lights to `t`, so
## the same taps and judge events at the same song times give the same race whatever the frame rate, and a paused song (t frozen) freezes everything, deadlines included.
##
## The race: the player starts at the back of the grid in the middle lane, three rivals ahead (`rivals`). Speed: the target is min + (top - min) x (floor + (1 - floor) x rhythm), rhythm an
## average of the pads' recent judgements (perfect 1 ... miss 0), so good play sustains speed and poor play slows the car, never below `min_frac` x top (the race always
## finishes: brief 9). Every `decision_s + gap_s` seconds a situation (`situations`, picked by a seeded draw, weights in the data) puts something in the road ahead:
##   braking_car    traffic ahead in your lane brakes        safe: bottom (brake) or a lane change to a lane that exists
##   rival_opening  a rival ahead in your lane, one side open safe: the open side (an OVERTAKE: a boost, the rival drops back), top (follow), bottom (drop behind)
##   blocked_lane   roadworks close your lane                 safe: a lane change, or bottom (brake and squeeze across)
##   narrowing      cones close your lane, a van alongside   safe: bottom (drop behind the van and merge), or the free lane on the other side when there is one
## Every situation has bottom safe (tests enumerate every generated situation). The selection is free to change until the deadline and the CURRENT selection is resolved AT
## the deadline (no selection = top). Penalties are bounded: contact halves the speed (floor `min_frac`) and caps it for two seconds, braking costs 28 %, a kerb scrape 35 %.
## Win = the car crosses the finish line before every rival (`result().race`: won, position, time_s from the green light).
##
## In the world (ruling 38, contract 10): `things()` is the car's bonnet and dash (frames: steady, leaning left or right, braking, jolted), the countdown gauge and the speed bar
## on the dash, the rivals' and the traffic's cars (frames: cruising, BRAKE LIGHTS, contact), the roadworks and cones, the chosen opening lit on the road, the start lights
## and the rain; `camera_pose(t)` is the cockpit camera (RaceStageHost hands it to the race stage: StoryStage.pose_fn): the car's place on the course, its lane eased over
## `lane_ease_beats`, a small yaw into a lane change, no roll and no shake. Feedback marks through the port (`world.feedback`): glow on the chosen opening, tick on what you
## got past, cross on what you hit.

const REGIONS := ["top", "bottom", "left", "right"]
const SAFE := ["clear", "overtake", "follow", "brake"]
const QUALITY := {"perfect": 1.0, "great": 0.9, "good": 0.75, "ok": 0.5, "hold_complete": 1.0, "hold_partial": 0.5, "miss": 0.0, "stray": 0.3}

var world: Object = null  # the room (WorldThings), null in a pure test
var data: Dictionary = {}  # content/races/<theme>.json
var course: RaceCourse
var theme := "space"
var rng := RandomNumberGenerator.new()

# timing and tuning (from data)
var dt := 1.0 / 120.0
var decision_s := 4.0
var gap_s := 1.6
var first_s := 4.5
var no_last_m := 180.0
var finish_hold_s := 3.0
var grid_s := 2.76
var lane_ease_s := 0.52
var v_top := 38.0
var v_min := 13.3
var accel := 5.0
var decel := 9.0
var rhythm_rate := 0.15
var rhythm_floor := 0.25  # the share of the speed range a car with no rhythm at all still gets (above the minimum)

# state
var t_begin := -1.0
var t_go := -1.0
var t_sim := -1.0  # the song time the simulation has been integrated to
var rhythm := 0.6
var judged := 0
var player := {}
var rivals: Array = []
var traffic: Array = []
var cur: Dictionary = {}  # the live situation ({} none)
var sits: Array = []  # every situation so far (resolved ones carry `result`)
var next_spawn := INF
var finish_t := -1.0
var position := 0
var log: Array = []  # [{kind: go | spawn | select | resolve | finish | rhythm, t, ...}]
var _pending: Array = []  # judge qualities not yet applied: [[t, q]]
var _n := 0
var _now := 0.0
var _flash_until := -1.0  # the gauge's deadline flash
var _jolt_until := -1.0
var _brake_until := -1.0
var _judged_since_block := 0
var max_s := 0.0  # a race longer than this (song s from the green light) is a bug: the minimum speed finishes sooner


func setup(ctx: Dictionary) -> void:
	super.setup(ctx)
	world = ctx.get("world", null)
	var req: Dictionary = ctx.get("request", {}) if typeof(ctx.get("request", {})) == TYPE_DICTIONARY else {}
	theme = str(req.get("theme", config.get("theme", "space")))
	if theme == "":
		theme = "space"
	var path := str(config.get("races", "res://content/races/{theme}.json")).replace("{theme}", theme)
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
	data = d if typeof(d) == TYPE_DICTIONARY else {}
	if typeof(config.get("race_data", null)) == TYPE_DICTIONARY:  # (a test's own table)
		data = config["race_data"]
	var tm: Dictionary = data.get("timing", {})
	var sp: Dictionary = data.get("speed", {})
	dt = float(tm.get("dt", dt))
	decision_s = float(config.get("decision_s_override", tm.get("decision_s", config.get("decision_s", decision_s))))
	gap_s = float(tm.get("gap_s", gap_s))
	first_s = float(tm.get("first_s", first_s))
	no_last_m = float(tm.get("no_situation_last_m", no_last_m))
	finish_hold_s = float(tm.get("finish_hold_s", finish_hold_s))
	grid_s = float(tm.get("grid_beats", 8.0)) * beat_s
	lane_ease_s = float(tm.get("lane_ease_beats", 1.5)) * beat_s
	v_top = float(sp.get("top_mps", v_top))
	v_min = v_top * float(sp.get("min_frac", config.get("min_speed_frac", 0.35)))
	accel = float(sp.get("accel", accel))
	decel = float(sp.get("decel", decel))
	rhythm = float(sp.get("start_rhythm", rhythm))
	rhythm_rate = float(sp.get("rhythm_rate", rhythm_rate))
	rhythm_floor = float(sp.get("rhythm_floor", rhythm_floor))
	course = RaceCourse.load_id(str(data.get("course", (config.get("race", {}) as Dictionary).get("course", "race_space") if typeof(config.get("race", null)) == TYPE_DICTIONARY else "race_space")))
	rng.seed = int(config.get("seed", rng_seed))
	max_s = course.length_m / maxf(v_min, 0.1) + 30.0
	var mid := int(course.lane_count() / 2)
	player = {"s": 0.0, "v": 0.0, "lane_from": mid, "lane_to": mid, "lane_t0": -100.0, "boost": 0.0, "boost_until": -1.0, "recover_until": -1.0, "recover_cap": 1.0,
		"contacts": 0, "overtakes": 0, "brakes": 0}
	rivals = []
	for r: Dictionary in data.get("rivals", []):
		rivals.append({"id": str(r["id"]), "sprite": str(r["sprite"]), "s": float(r["start_m"]), "v": 0.0, "lane_from": int(r["lane"]), "lane_to": int(r["lane"]), "lane_t0": -100.0,
			"pace": float(r["pace"]), "wobble": float(r.get("wobble", 0.0)), "period": float(r.get("period_s", 10.0)), "phase": float(r.get("phase", 0.0)),
			"slow_until": -1.0, "slow_mul": 1.0, "finish_t": -1.0, "contact_until": -1.0})


func begin(t: float) -> void:
	super.begin(t)
	t_begin = t
	t_go = t + grid_s
	t_sim = t
	_now = t
	next_spawn = t_go + first_s


# --- input ------------------------------------------------------------------------------------------------------------------------

func targets() -> Array:
	return [] if _done else ["region:top", "region:bottom", "region:left", "region:right"] + exit_targets()


## A driving region (the stage area's top, bottom, left or right) or an exit. A region while a situation is open selects (or re-selects) that response; outside a situation
## it is accepted and does nothing (the regions are always the driver's: they never fall through to anything else).
func tap(target: String, t: float) -> bool:
	if _done:
		return false
	if is_exit_target(target):
		request_leave(t)
		return true
	if not target.begins_with("region:"):
		return false
	var dir := target.substr(7)
	if dir not in REGIONS:
		return false
	update(t)
	if cur.is_empty() or t >= float(cur["t_dead"]):
		return true
	cur["selected"] = dir
	log.append({"kind": "select", "t": t, "n": int(cur["n"]), "dir": dir})
	if world != null:
		world.feedback("race_choice" if dir != "bottom" else "race_dash", "glow", t)
	return true


## The pads (overlay mode): every judgement moves the rhythm average, in song-time order.
func on_judge(ev: Dictionary, t: float) -> void:
	var k := str(ev.get("kind", ""))
	if k == "hold_start":
		k = str(ev.get("grade", "good"))
	if not QUALITY.has(k):
		return
	_pending.append([float(ev.get("time", t)), float(QUALITY[k])])
	_judged_since_block += 1


## A block's result: only when no single judgement arrived in the block (a run without per-note events) does it count, as a pass (0.9) or a fail (0.2).
func on_block(result: Dictionary) -> void:
	if _judged_since_block == 0 and result.has("passed"):
		_pending.append([float(result.get("t", t_sim)), 0.9 if bool(result["passed"]) else 0.2])
	_judged_since_block = 0


func request_leave(t: float) -> void:
	_finish("left")


# --- the simulation ---------------------------------------------------------------------------------------------------------------

func update(t: float) -> void:
	if not began:
		return
	_now = maxf(_now, t)
	while t_sim + dt <= t + 1e-9:
		_step(t_sim + dt)
	if finish_t >= 0.0 and not _done and t >= finish_t + finish_hold_s:
		_finish("done")


func _step(tt: float) -> void:
	t_sim = tt
	while not _pending.is_empty() and float(_pending[0][0]) <= tt:
		var q: Array = _pending.pop_front()
		rhythm = clampf(rhythm + (float(q[1]) - rhythm) * rhythm_rate, 0.0, 1.0)
	if tt < t_go:
		return
	if not bool(player.get("went", false)):
		player["went"] = true
		log.append({"kind": "go", "t": t_go})
	if cur.is_empty() and tt >= next_spawn and finish_t < 0.0 and float(player["s"]) < course.length_m - no_last_m:
		_spawn(tt)
	if not cur.is_empty() and tt >= float(cur["t_dead"]):
		_resolve(tt)
	_move_player(tt)
	_move_rivals(tt)
	_move_traffic(tt)


func _move_player(tt: float) -> void:
	var v := float(player["v"])
	var vt := v_min + (v_top - v_min) * (rhythm_floor + (1.0 - rhythm_floor) * rhythm)
	if tt < float(player["recover_until"]):
		vt *= float(player["recover_cap"])
	if tt < float(player["boost_until"]):
		vt += float(player["boost"])
	if finish_t >= 0.0:
		vt = 0.0
	v = minf(vt, v + accel * dt) if v < vt else maxf(vt, v - decel * dt)
	if finish_t < 0.0:
		v = maxf(v, v_min * clampf((tt - t_go) / 2.0, 0.0, 1.0))  # the floor: every race finishes (it rises over the first two seconds from the lights)
	player["v"] = v
	var s0 := float(player["s"])
	var s1 := s0 + v * dt
	player["s"] = s1
	if finish_t < 0.0 and s1 >= course.length_m:
		finish_t = tt - dt + dt * (course.length_m - s0) / maxf(s1 - s0, 1e-6)
		position = 1
		for r: Dictionary in rivals:
			if float(r["finish_t"]) >= 0.0 and float(r["finish_t"]) < finish_t:
				position += 1
		log.append({"kind": "finish", "t": finish_t, "time_s": finish_t - t_go, "position": position})
		if world != null:
			world.feedback("race_dash", "glow" if position == 1 else "cross", finish_t)


func _move_rivals(tt: float) -> void:
	var held := str(cur.get("rival", "")) if not cur.is_empty() else ""
	var plane := int(player["lane_to"])
	for r: Dictionary in rivals:
		var vt := float(r["pace"]) * v_top * (1.0 + float(r["wobble"]) * sin(TAU * (tt - t_go) / float(r["period"]) + float(r["phase"])))
		if tt < float(r["slow_until"]):
			vt *= float(r["slow_mul"])
		if str(r["id"]) == held:  # the situation's rival: held up so the gap closes to `gap_m` by the deadline
			var gap := float(r["s"]) - float(player["s"])
			vt = clampf(float(player["v"]) - (gap - float(cur.get("gap_m", 6.0))) / maxf(float(cur["t_dead"]) - tt, 0.4), 0.3 * v_top, v_top)
		var v := float(r["v"])
		v = minf(vt, v + accel * dt) if v < vt else maxf(vt, v - decel * dt)
		r["v"] = v
		var s0 := float(r["s"])
		r["s"] = s0 + v * dt
		if float(r["finish_t"]) < 0.0 and float(r["s"]) >= course.length_m:
			r["finish_t"] = tt - dt + dt * (course.length_m - s0) / maxf(float(r["s"]) - s0, 1e-6)
		if str(r["id"]) != held and int(r["lane_to"]) == plane:  # a rival never sits in the car's lane right in front of it or behind it: it moves over
			var g := float(r["s"]) - float(player["s"])
			if g > -10.0 and g < 14.0:
				var to := _free_lane(int(r["lane_to"]), str(r["id"]), float(r["s"]), tt)
				if to >= 0:
					_shift(r, to, tt)


func _move_traffic(tt: float) -> void:
	var keep: Array = []
	for tr: Dictionary in traffic:
		if bool(tr.get("rel", false)):  # still part of the live situation: placed relative to the car
			var u := clampf((tt - float(tr["t0"])) / maxf(float(tr["t1"]) - float(tr["t0"]), 0.01), 0.0, 1.0)
			tr["s"] = float(player["s"]) + lerpf(float(tr["g0"]), float(tr["g1"]), u)
			tr["v"] = float(player["v"])
		else:
			tr["s"] = float(tr["s"]) + float(tr["v"]) * dt
		var g := float(tr["s"]) - float(player["s"])
		if g > -15.0 and g < 220.0:
			keep.append(tr)
	traffic = keep


## A lane next to `lane` with nothing within 12 m of `s` (rivals and traffic), nearer the middle first; -1 when both are taken or do not exist.
func _free_lane(lane: int, who: String, s: float, tt: float) -> int:
	var order := [lane + 1, lane - 1] if lane < course.lane_count() / 2 else [lane - 1, lane + 1]
	for l: int in order:
		if l < 0 or l >= course.lane_count() or l == int(player["lane_to"]):
			continue
		var busy := false
		for r: Dictionary in rivals:
			if str(r["id"]) != who and int(r["lane_to"]) == l and absf(float(r["s"]) - s) < 12.0:
				busy = true
		for tr: Dictionary in traffic:
			if int(tr["lane"]) == l and absf(float(tr["s"]) - s) < 12.0:
				busy = true
		if not busy:
			return l
	return -1


func _shift(who: Dictionary, to: int, tt: float) -> void:
	who["lane_from"] = lane_of(who, tt)
	who["lane_to"] = to
	who["lane_t0"] = tt


## The fractional lane of a car at song time `t` (eased over `lane_ease_s`).
func lane_of(who: Dictionary, t: float) -> float:
	var u := clampf((t - float(who["lane_t0"])) / lane_ease_s, 0.0, 1.0)
	u = u * u * (3.0 - 2.0 * u)
	return lerpf(float(who["lane_from"]), float(who["lane_to"]), u)


# --- situations -------------------------------------------------------------------------------------------------------------------

func _pick_kind() -> String:
	var table: Array = data.get("situations", [])
	var total := 0.0
	for s: Dictionary in table:
		total += float(s.get("weight", 1.0))
	var x := rng.randf() * total
	for s: Dictionary in table:
		x -= float(s.get("weight", 1.0))
		if x <= 0.0:
			return str(s["kind"])
	return "braking_car"


func _sit_def(kind: String) -> Dictionary:
	for s: Dictionary in data.get("situations", []):
		if str(s["kind"]) == kind:
			return s
	return {}


func _spawn(tt: float) -> void:
	var kind := _pick_kind()
	var p := int(player["lane_to"])
	var nl := course.lane_count()
	var sit := {"n": _n, "kind": kind, "t_spawn": tt, "t_dead": tt + decision_s, "lane": p, "selected": "", "outcomes": {}, "shift": {}, "subject": "", "rival": ""}
	_n += 1
	if kind == "rival_opening":
		var reach: Array = _sit_def(kind).get("reach_m", [3.0, 80.0])
		var best: Dictionary = {}
		for r: Dictionary in rivals:
			var g := float(r["s"]) - float(player["s"])
			if g > float(reach[0]) and g < float(reach[1]) and (best.is_empty() or g < float(best["s"]) - float(player["s"])):
				best = r
		if best.is_empty():
			kind = "braking_car"
			sit["kind"] = kind
		else:
			sit["rival"] = str(best["id"])
			sit["subject"] = str(best["id"])
			sit["gap_m"] = float(_sit_def("rival_opening").get("gap_m", 6.0))
			if int(best["lane_to"]) != p:
				_shift(best, p, tt)
	var d := _sit_def(kind)
	var o := {}
	var sh := {}
	var left := p - 1 if p - 1 >= 0 else -1
	var right := p + 1 if p + 1 < nl else -1
	match kind:
		"braking_car":
			var id := "tr_%d" % sit["n"]
			var g: Array = d.get("gap_m", [55.0, 7.0])
			traffic.append({"id": id, "sprite": str(d.get("sprite", "car_taxi")), "kind": "car", "lane": p, "s": float(player["s"]) + float(g[0]), "v": 0.0, "rel": true,
				"t0": tt, "t1": tt + decision_s, "g0": float(g[0]), "g1": float(g[1]), "brake_from": tt + float(d.get("brake_after_s", 0.8)), "contact_until": -1.0})
			sit["subject"] = id
			o = {"top": "contact", "bottom": "brake", "left": "clear" if left >= 0 else "kerb", "right": "clear" if right >= 0 else "kerb"}
			sh = {"left": left, "right": right}
		"blocked_lane":
			var id := "bar_%d" % sit["n"]
			var g: Array = d.get("gap_m", [60.0, 8.0])
			traffic.append({"id": id, "sprite": str(d.get("sprite", "barrier")), "kind": "barrier", "lane": p, "s": float(player["s"]) + float(g[0]), "v": 0.0, "rel": true,
				"t0": tt, "t1": tt + decision_s, "g0": float(g[0]), "g1": float(g[1]), "contact_until": -1.0})
			sit["subject"] = id
			var out_lane := right if right >= 0 else left
			o = {"top": "contact", "bottom": "brake", "left": "clear" if left >= 0 else "kerb", "right": "clear" if right >= 0 else "kerb"}
			sh = {"top": out_lane, "bottom": out_lane, "left": left if left >= 0 else out_lane, "right": right if right >= 0 else out_lane}
		"rival_opening":
			var sides := []
			if left >= 0:
				sides.append(left)
			if right >= 0:
				sides.append(right)
			var open_lane: int = sides[rng.randi() % sides.size()] if not sides.is_empty() else -1
			for l: int in sides:
				if l != open_lane:  # the other side is shut by a van alongside
					var id := "tr_%d" % sit["n"]
					traffic.append({"id": id, "sprite": str(d.get("traffic_sprite", "car_van")), "kind": "car", "lane": l, "s": float(player["s"]) + 10.0, "v": 0.0, "rel": true,
						"t0": tt, "t1": tt + decision_s, "g0": 30.0, "g1": 2.5, "contact_until": -1.0})
					sit["blocker"] = id
			for dir in ["left", "right"]:
				var l: int = left if dir == "left" else right
				o[dir] = "kerb" if l < 0 else ("overtake" if l == open_lane else "contact")
				if l == open_lane:
					sh[dir] = l
			o["top"] = "follow"
			o["bottom"] = "brake"
			sit["open"] = open_lane
		"narrowing":
			var id := "cone_%d" % sit["n"]
			var g: Array = d.get("gap_m", [60.0, 8.0])
			traffic.append({"id": id, "sprite": str(d.get("sprite", "cones")), "kind": "cones", "lane": p, "s": float(player["s"]) + float(g[0]), "v": 0.0, "rel": true,
				"t0": tt, "t1": tt + decision_s, "g0": float(g[0]), "g1": float(g[1]), "contact_until": -1.0})
			sit["subject"] = id
			var sides := []
			if left >= 0:
				sides.append(left)
			if right >= 0:
				sides.append(right)
			var along: int = sides[rng.randi() % sides.size()]
			var vid := "tr_%d" % sit["n"]
			var al: Array = d.get("alongside_m", [26.0, 1.5])
			traffic.append({"id": vid, "sprite": str(d.get("traffic_sprite", "car_van")), "kind": "car", "lane": along, "s": float(player["s"]) + float(al[0]), "v": 0.0, "rel": true,
				"t0": tt, "t1": tt + decision_s, "g0": float(al[0]), "g1": float(al[1]), "contact_until": -1.0})
			sit["blocker"] = vid
			for dir in ["left", "right"]:
				var l: int = left if dir == "left" else right
				o[dir] = "kerb" if l < 0 else ("contact" if l == along else "clear")
				sh[dir] = l if l >= 0 and l != along else along
			o["top"] = "contact"
			o["bottom"] = "brake"
			sh["top"] = along
			sh["bottom"] = along
			sit["along"] = along
	sit["outcomes"] = o
	sit["shift"] = sh
	cur = sit
	sits.append(sit)
	log.append({"kind": "spawn", "t": tt, "n": int(sit["n"]), "sit": str(sit["kind"]), "lane": p, "dead": float(sit["t_dead"]), "outcomes": o.duplicate()})


func _resolve(tt: float) -> void:
	var dir := str(cur["selected"]) if str(cur["selected"]) != "" else "top"
	var out := str((cur["outcomes"] as Dictionary).get(dir, "contact"))
	var oc: Dictionary = (data.get("outcomes", {}) as Dictionary).get(out, {})
	var v := float(player["v"])
	player["v"] = maxf(v * float(oc.get("speed_mul", 1.0)), v_min)
	match out:
		"contact", "kerb":
			player["contacts"] = int(player["contacts"]) + 1
			player["recover_until"] = tt + float(oc.get("recover_s", 2.0))
			player["recover_cap"] = float(oc.get("recover_cap", 0.7))
			_jolt_until = tt + 0.7
		"overtake":
			player["overtakes"] = int(player["overtakes"]) + 1
			player["boost"] = float(oc.get("boost_mps", 4.0))
			player["boost_until"] = tt + float(oc.get("boost_s", 2.0))
			for r: Dictionary in rivals:
				if str(r["id"]) == str(cur["rival"]):
					r["slow_mul"] = float(oc.get("rival_mul", 0.72))
					r["slow_until"] = tt + float(oc.get("rival_s", 2.5))
		"brake", "follow":
			player["brakes"] = int(player["brakes"]) + 1
			_brake_until = tt + 0.8
	var to := int((cur["shift"] as Dictionary).get(dir, -1))
	if to >= 0 and to != int(player["lane_to"]):
		_shift(player, to, tt)
	var stayed := int(player["lane_to"]) == int(cur["lane"])
	for tr: Dictionary in traffic:  # the situation's things go on in the world: what you passed stays slow behind, what you stayed behind pulls away
		if not bool(tr.get("rel", false)):
			continue
		tr["rel"] = false
		var hit := (out == "contact" and (str(tr["id"]) == str(cur["subject"]) or (str(tr["id"]) == str(cur.get("blocker", "")) and dir in ["left", "right"])))
		if hit:
			tr["contact_until"] = tt + 0.8
		if str(tr["kind"]) != "car":
			tr["v"] = 0.0
		elif stayed and int(tr["lane"]) == int(cur["lane"]):
			tr["v"] = float(player["v"]) + 8.0
		else:
			tr["v"] = float(player["v"]) * 0.6
	var subj := str(cur["subject"])
	for r: Dictionary in rivals:
		if str(r["id"]) == subj and out == "contact":
			r["contact_until"] = tt + 0.8
	cur["result"] = out
	cur["resolved_dir"] = dir
	cur["resolved_t"] = tt
	log.append({"kind": "resolve", "t": tt, "n": int(cur["n"]), "sit": str(cur["kind"]), "dir": dir, "outcome": out, "safe": out in SAFE})
	if world != null:
		world.feedback(subj, "tick" if out in SAFE else "cross", tt)
	_flash_until = tt + 0.5
	next_spawn = tt + gap_s
	cur = {}


## Which responses of situation `sit` are safe (no contact, no kerb): the tests' "every situation has a reachable safe response".
static func safe_responses(sit: Dictionary) -> Array:
	var out: Array = []
	for dir in REGIONS:
		if str((sit.get("outcomes", {}) as Dictionary).get(dir, "contact")) in SAFE:
			out.append(dir)
	return out


# --- what the host reads ----------------------------------------------------------------------------------------------------------

func finished() -> bool:
	return finish_t >= 0.0


func race_time() -> float:
	return finish_t - t_go if finish_t >= 0.0 else -1.0


## The order now (1 = leading): finished cars by finish time, the rest by distance.
func standing() -> int:
	if finish_t >= 0.0:
		return position
	var p := 1
	for r: Dictionary in rivals:
		if float(r["s"]) > float(player["s"]):
			p += 1
	return p


func state() -> Dictionary:
	var s := super.state()
	s.merge({"t": t_sim, "s": float(player.get("s", 0.0)), "v": float(player.get("v", 0.0)), "lane": lane_of(player, _now) if not player.is_empty() else 0.0, "rhythm": rhythm,
		"situation": str(cur.get("kind", "")), "selected": str(cur.get("selected", "")), "deadline": float(cur.get("t_dead", -1.0)), "left_s": maxf(float(cur.get("t_dead", _now)) - _now, 0.0),
		"standing": standing(), "finished": finished(), "position": position, "time_s": race_time(), "contacts": int(player.get("contacts", 0)),
		"overtakes": int(player.get("overtakes", 0)), "situations": sits.size(), "go_t": t_go})
	return s


func result() -> Dictionary:
	var r := super.result()
	r["activity_id"] = "race"
	r["flags_to_set"] = []
	if finished():
		r["race"] = {"won": position == 1, "position": position, "time_s": snappedf(race_time(), 0.001)}
		r["score"] = maxi(0, 5 - position) * 100 + int(player["overtakes"]) * 10 - int(player["contacts"]) * 10
	return r


## The cockpit camera at song time `t` (the stage's pose: StoryStage.pose_fn): on the course at the car's distance (carried on by its speed from the last step), its eased
## lane, the course's heading plus a small yaw into a lane change, the course camera's pitch (a degree more down while braking), no roll.
func camera_pose(t: float) -> Dictionary:
	var s := float(player.get("s", 0.0)) + float(player.get("v", 0.0)) * clampf(t - t_sim, 0.0, dt)
	var lane := lane_of(player, t)
	var x := course.lane_x(lane)
	var x2 := course.lane_x(lane_of(player, t - 0.05))
	var p := course.point(s, x)
	var v := maxf(float(player.get("v", 0.0)), 4.0)
	var yaw := float(p["yaw"]) - clampf(rad_to_deg(atan2((x - x2) / 0.05, v)), -10.0, 10.0)
	var at: Vector2 = p["at"]
	var pitch := float(course.camera.get("pitch_deg", -2.0)) - (1.0 if t < _brake_until or t < _jolt_until else 0.0)
	return {"cam": Vector3(at.x, course.eye_m, at.y), "yaw": yaw, "pitch": pitch, "roll": 0.0, "pos": at, "sector": course.road_at(s), "ground": 0.0, "moving": true}


## The race's things in the world this frame (contract 10): see the header. Ids: race_dash, race_gauge, race_speedo, race_rain, race_choice, race_lights, the rivals' ids,
## the traffic's (tr_<n>, bar_<n>, cone_<n>).
func things() -> Array:
	var out: Array = []
	if course == null or player.is_empty():
		return out
	var t := _now
	var vw: Dictionary = data.get("view", {})
	var pose := camera_pose(t)
	var cam := Vector2((pose["cam"] as Vector3).x, (pose["cam"] as Vector3).z)
	var f := RaceCourse.fwd(float(pose["yaw"]))
	var rt := RaceCourse.right(float(pose["yaw"]))
	var sec := str(pose["sector"])
	var dsh: Dictionary = vw.get("dash", {"ahead_m": 1.4, "y": 0.42, "size": [3.4, 0.46]})
	var row := 0
	var sel := str(cur.get("selected", ""))
	if t < _jolt_until:
		row = 4
	elif sel == "bottom" or t < _brake_until:
		row = 3
	elif sel == "left":
		row = 1
	elif sel == "right":
		row = 2
	var at := cam + f * float(dsh["ahead_m"])
	out.append({"id": "race_dash", "sprite": "dash", "at": [at.x, at.y], "sector": course.road_at(float(player["s"]) + float(dsh["ahead_m"])), "size": dsh["size"], "frame": [row, 0],
		"y": float(dsh["y"]), "grid": [1, 5]})
	if not cur.is_empty() or t < _flash_until:
		var g: Dictionary = vw.get("gauge", {"ahead_m": 1.3, "y": 0.8, "size": [0.17, 0.17]})
		var k := 0 if cur.is_empty() else clampi(int(ceil(8.0 * (float(cur["t_dead"]) - t) / decision_s)), 1, 8)
		var ga := cam + f * float(g["ahead_m"])
		out.append({"id": "race_gauge", "sprite": "gauge", "at": [ga.x, ga.y], "sector": sec, "size": g["size"], "frame": k, "y": float(g["y"]), "anchor": "center", "grid": [9, 1]})
	var sp: Dictionary = vw.get("speedo", {"ahead_m": 1.32, "side_m": -0.55, "y": 0.79, "size": [0.36, 0.12]})
	var sa := cam + f * float(sp["ahead_m"]) + rt * float(sp["side_m"])
	out.append({"id": "race_speedo", "sprite": "speedo", "at": [sa.x, sa.y], "sector": sec, "size": sp["size"], "frame": clampi(int(float(player["v"]) / v_top * 8.0), 0, 7),
		"y": float(sp["y"]), "anchor": "center", "grid": [8, 1]})
	if not cur.is_empty() and sel in ["top", "left", "right"]:
		var p := int(player["lane_to"])
		var l := p if sel == "top" else (p - 1 if sel == "left" else p + 1)
		if l >= 0 and l < course.lane_count():
			var ahead := float(player["s"]) + float(vw.get("glow_ahead_m", 14.0))
			var gp: Vector2 = course.point(ahead, course.lane_x(l))["at"]
			out.append({"id": "race_choice", "sprite": "lane_glow", "at": [gp.x, gp.y], "sector": course.road_at(ahead), "size": [2.8, 0.4], "frame": 1 if fmod(t / beat_s, 1.0) < 0.75 else 0,
				"y": 0.02, "grid": [2, 1]})
	var sl: Dictionary = vw.get("start_lights", {"s": 16.0, "y": 4.6, "size": [3.2, 1.1]})
	if t < t_go + 3.0:
		var lp: Vector2 = course.point(float(sl["s"]), 0.0)["at"]
		var lk := 3 if t >= t_go else clampi(int(floor((t - t_begin) / maxf(grid_s / 3.0, 0.01))), 0, 2)
		out.append({"id": "race_lights", "sprite": "start_lights", "at": [lp.x, lp.y], "sector": course.road_at(float(sl["s"])), "size": sl["size"], "frame": lk, "y": float(sl["y"]), "grid": [4, 1]})
	var cs: Array = vw.get("car_size", [2.0, 1.3])
	var cy := float(vw.get("car_y", 0.22))
	for r: Dictionary in rivals:
		var g := float(r["s"]) - float(player["s"])
		if g < 2.0 or g > 160.0:
			continue
		var rp: Vector2 = course.point(float(r["s"]), course.lane_x(lane_of(r, t)))["at"]
		var fr := 2 if t < float(r["contact_until"]) else (1 if t < float(r["slow_until"]) or float(r["v"]) < float(player["v"]) - 3.0 else 0)
		out.append({"id": str(r["id"]), "sprite": str(r["sprite"]), "at": [rp.x, rp.y], "sector": course.road_at(float(r["s"])), "size": cs, "frame": fr, "y": cy, "grid": [3, 1]})
	for tr: Dictionary in traffic:
		var g := float(tr["s"]) - float(player["s"])
		if g < 2.0:
			continue
		var tp: Vector2 = course.point(float(tr["s"]), course.lane_x(float(tr["lane"])))["at"]
		var kind := str(tr["kind"])
		var fr := 0
		var size: Array = cs
		var y := cy
		if kind == "car":
			fr = 2 if t < float(tr["contact_until"]) else (1 if t >= float(tr.get("brake_from", INF)) else 0)
			if str(tr["sprite"]) == "car_van":
				size = vw.get("van_size", [2.2, 2.0])
		else:
			fr = 1 if fmod(t / beat_s, 1.0) < 0.5 else 0
			size = vw.get("barrier_size", [3.0, 1.25]) if kind == "barrier" else vw.get("cones_size", [3.2, 1.05])
			y = 0.0
		out.append({"id": str(tr["id"]), "sprite": str(tr["sprite"]), "at": [tp.x, tp.y], "sector": course.road_at(float(tr["s"])), "size": size, "frame": fr, "y": y,
			"grid": [3, 1] if kind == "car" else [2, 1]})
	var rn: Dictionary = vw.get("rain", {"ahead_m": 2.6, "size": [6.4, 3.0]})
	var ra := cam + f * float(rn["ahead_m"])
	out.append({"id": "race_rain", "sprite": "rain", "at": [ra.x, ra.y], "sector": sec, "size": rn["size"], "frame": int(floor(t / (beat_s * 0.5))) % 4, "y": course.eye_m,
		"anchor": "center", "grid": [4, 1]})
	return out


## The pads stay (overlay): no controls of its own.
func controls() -> Array:
	return []
