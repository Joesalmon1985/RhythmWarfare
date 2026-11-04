class_name RunRail
extends RefCounted
## The player's journey inside one run node, as pure logic (no nodes, no clock, no renderer): the chapters' rails on the run's phase engine.
##
## A node has a good rail (an ordered list of places up from the floor, e.g. steps > stage > balcony > booth) and a bad rail (floor edge > corridor >
## cubicle). At each block decision a pass steps one place up the good rail (and stays at the top once there) and a hold steps one place along the bad
## rail; two holds in a row start the queasy look, the bottom of the bad rail plays the sick beat, and a pass from the bad rail walks back towards the
## floor (the chapters' win-back). The role follows the place (dancer, on_stage, dj, queasy, sick, recovered).
##
## `step()` answers with director-style actions ({t0, action, args}) that the run scene hands to StoryStage.apply(); nothing here knows the stage. Moves start
## on the decision beat, which is in the block's cue-free guard (beats 12.75 to 16), last 2 to 4 bars and are shortened where the chart is dense
## (pick_bars), so the camera never moves mostly under a dense run of cues.

const MOVE_BARS_MIN := 2.0
const MOVE_BARS_MAX := 4.0
const DENSE_PER_BAR := 4  # more notes than this in a bar (one per beat) is a dense bar
const ROLES := ["dancer", "on_stage", "dj", "queasy", "sick", "recovered"]
const STYLES := ["walk", "stagger", "run", "climb", "carried"]

var node_id := ""
var home := ""
var good: Array = []  # [{to, role, style, bars}]
var bad: Array = []
var glances: Array = []  # [{by, pitch, bars}]
var strolls: Array = []  # [{fwd, right, turn, bars}]
var arrive := ""  # where the player steps in from another world (a waypoint of this node's world), "" = at home
var exits: Dictionary = {}  # dir -> waypoint of the doorway toward that route's world
var bpm := 174.0

var pos := 0  # 0 at home, 1.. up the good rail, -1.. down the bad rail
var holds := 0  # consecutive holds
var role := "dancer"
var queasy := 0.0
var sick_played := false
var busy_until := -1.0  # song time until which a journey move is under way
var visited: Array = []  # [{place, pos, role, kind}] one entry per block decision (tests and playtests read it)
var places_seen: Dictionary = {}  # place waypoint -> times stood there


func bar_s() -> float:
	return 4.0 * 60.0 / bpm


## Problems with one node's rail data (waypoint existence is checked against the map by tests/test_run_rail.gd).
static func validate(id: String, rail: Variant) -> Array:
	var errors: Array = []
	if typeof(rail) != TYPE_DICTIONARY:
		return ["node %s: has no rail" % id]
	var r: Dictionary = rail
	for key in ["good", "bad"]:
		if typeof(r.get(key)) != TYPE_ARRAY or (r[key] as Array).is_empty():
			errors.append("node %s: rail.%s needs at least one place" % [id, key])
			continue
		for p in r[key]:
			if typeof(p) != TYPE_DICTIONARY or str(p.get("to", "")) == "":
				errors.append("node %s: a rail.%s place needs `to`" % [id, key])
				continue
			if str(p.get("role", "dancer")) not in ROLES:
				errors.append("node %s: rail.%s place %s has unknown role %s" % [id, key, p["to"], p.get("role")])
			if str(p.get("style", "walk")) not in STYLES:
				errors.append("node %s: rail.%s place %s has unknown style %s" % [id, key, p["to"], p.get("style")])
			var b := float(p.get("bars", 3.0))
			if b < MOVE_BARS_MIN or b > MOVE_BARS_MAX:
				errors.append("node %s: rail.%s place %s lasts %.1f bars; moves last %d to %d bars" % [id, key, p["to"], b, int(MOVE_BARS_MIN), int(MOVE_BARS_MAX)])
	if (r.get("glances", []) as Array).is_empty() or (r.get("strolls", []) as Array).is_empty():
		errors.append("node %s: every block needs a glance and a stroll to draw from (rail.glances and rail.strolls)" % id)
	return errors


func setup(p_node_id: String, node: Dictionary, p_bpm: float) -> void:
	node_id = p_node_id
	home = str(node["waypoint"])
	var r: Dictionary = node["rail"]
	good = (r["good"] as Array).duplicate(true)
	bad = (r["bad"] as Array).duplicate(true)
	glances = (r.get("glances", []) as Array).duplicate(true)
	strolls = (r.get("strolls", []) as Array).duplicate(true)
	arrive = str(r.get("arrive", ""))
	exits = (r.get("exits", {}) as Dictionary).duplicate()
	bpm = p_bpm
	reset()


func reset() -> void:
	pos = 0
	holds = 0
	role = "dancer"
	queasy = 0.0
	sick_played = false
	busy_until = -1.0


## The waypoint of rail position `p` (home for 0).
func place_at(p: int) -> String:
	if p > 0:
		return str((good[mini(p, good.size()) - 1] as Dictionary)["to"])
	if p < 0:
		return str((bad[mini(-p, bad.size()) - 1] as Dictionary)["to"])
	return home


func place() -> String:
	return place_at(pos)


func at_top() -> bool:
	return pos >= good.size()


func at_bottom() -> bool:
	return pos <= -bad.size()


# --- chart density ---------------------------------------------------------------------------------------------------------

## Notes of `notes` (the level's cue list) that start inside bar `k` (0-based from `t0`) of a move starting at t0.
static func notes_in_bar(notes: Array, t0: float, k: int, p_bpm: float) -> int:
	var bar := 4.0 * 60.0 / p_bpm
	var a := t0 + float(k) * bar
	var b := a + bar
	var n := 0
	for i in range(notes.size() - 1, -1, -1):  # newest first: stop once the notes are older than the span
		var nt := float((notes[i] as Dictionary)["time"])
		if nt < a - 4.0 * bar and nt < t0:
			break
		if nt >= a and nt < b:
			n += 1
	return n


## How many of the first `ceil(bars)` bars of a move starting at t0 are dense (more than one note per beat).
static func dense_bars(notes: Array, t0: float, bars: float, p_bpm: float) -> int:
	var d := 0
	for k in int(ceil(bars)):
		if notes_in_bar(notes, t0, k, p_bpm) > DENSE_PER_BAR:
			d += 1
	return d


## The warning the chapter director raises for a move: starts on a dense bar, or runs mostly (more than half its bars) over dense ones.
static func move_is_dense(notes: Array, t0: float, bars: float, p_bpm: float) -> bool:
	return notes_in_bar(notes, t0, 0, p_bpm) > DENSE_PER_BAR or float(dense_bars(notes, t0, bars, p_bpm)) > bars * 0.5


## The longest length of 2 to 4 bars, no longer than `want`, that the director's dense-run rule accepts; the shortest allowed one when none does.
static func pick_bars(want: float, notes: Array, t0: float, p_bpm: float) -> float:
	var b := clampf(floorf(want), MOVE_BARS_MIN, MOVE_BARS_MAX)
	while b > MOVE_BARS_MIN and move_is_dense(notes, t0, b, p_bpm):
		b -= 1.0
	return b


# --- the journey -------------------------------------------------------------------------------------------------------------

func _action(t0: float, action: String, args: Dictionary) -> Dictionary:
	return {"t0": t0, "action": action, "args": args}


func _move_to(out: Array, t0: float, wp: String, style: String, want_bars: float, notes: Array) -> float:
	var bars := pick_bars(want_bars, notes, t0, bpm)
	out.append(_action(t0, "player_move", {"to": wp, "style": style, "bars": bars}))
	busy_until = t0 + bars * bar_s()
	return bars


## A block decision at song time `t` (the decision beat of the block). Returns the actions it causes, steps the rail and records the place.
## `notes` is the level's cue list (the next block is already charted when a decision is made).
func step(passed: bool, t: float, notes: Array) -> Array:
	var out: Array = []
	var before := pos
	var kind := ""
	if passed:
		holds = 0
		if pos < 0:  # winning back: one place towards the floor
			pos += 1
			kind = "back" if pos < 0 else "home"
			role = "recovered" if pos < 0 else "dancer"
			var spec := _spec_back(pos)
			var bars := _move_to(out, t, place_at(pos), "walk", float(spec.get("bars", 3.0)), notes)
			out.append(_action(t, "player_role", {"role": "recovered"}))
			if queasy > 0.0:
				queasy = 0.0
				out.append(_action(t, "fx_queasy", {"amount": 0.0, "bars": 2.0}))
			if pos == 0:
				out.append(_action(t + bars * bar_s(), "player_role", {"role": "dancer"}))
			sick_played = false
		elif pos < good.size():
			pos += 1
			kind = "up"
			var spec2: Dictionary = good[pos - 1]
			var bars2 := _move_to(out, t, str(spec2["to"]), str(spec2.get("style", "walk")), float(spec2.get("bars", 3.0)), notes)
			role = str(spec2.get("role", "dancer"))
			out.append(_action(t + bars2 * bar_s(), "player_role", {"role": role}))  # you are on the stage once you have got there
		else:
			kind = "top"
	else:
		holds += 1
		if pos > -bad.size():
			pos = -1 if pos > 0 else pos - 1
			kind = "down"
			var spec3: Dictionary = bad[-pos - 1]
			var bars3 := _move_to(out, t, str(spec3["to"]), str(spec3.get("style", "walk")), float(spec3.get("bars", 3.0)), notes)
			role = str(spec3.get("role", "queasy"))
			out.append(_action(t, "player_role", {"role": role}))
			if at_bottom():
				kind = "bottom"
				sick_played = true
				out.append(_action(t + bars3 * bar_s(), "player_role", {"role": "sick"}))
				out.append(_action(t + bars3 * bar_s(), "sick_beat", {"bars": 4.0}))
				role = "sick"
		else:
			kind = "bottom_held"
		if holds >= 2:
			var amount := minf(0.3 + 0.15 * float(holds - 2), 0.8)
			if amount > queasy + 1.0e-6:
				queasy = amount
				out.append(_action(t, "fx_queasy", {"amount": amount, "bars": 3.0}))
	places_seen[place()] = int(places_seen.get(place(), 0)) + 1
	visited.append({"place": place(), "pos": pos, "from": before, "role": role, "kind": kind, "t": t, "queasy": queasy})
	return out


## A passed block from the bad rail goes back through the bad places and then home: the spec of the move to position `p` (<= 0).
func _spec_back(p: int) -> Dictionary:
	if p < 0:
		return bad[-p - 1]
	return {"bars": 3.0}


## The glance (and, when no journey move is under way, a stroll) of block `block` of phase `phase_n`, which starts at song time `t_block`. Varied from block to
## block by an index that runs through the node's lists. The glance sits at beat 5 (it never touches the route); the stroll at beat 6 to 9.
func ambient(t_block: float, phase_n: int, block: int, notes: Array) -> Array:
	var out: Array = []
	var beat := 60.0 / bpm
	var idx := phase_n * 4 + block + node_id.length()
	if not glances.is_empty():
		var g: Dictionary = glances[idx % glances.size()]
		out.append(_action(t_block + 5.0 * beat, "player_look", {"by": float(g.get("by", 0.0)), "pitch": float(g.get("pitch", 0.0)), "bars": float(g.get("bars", 2.0))}))
	if not strolls.is_empty() and idx % 3 != 0:
		var s: Dictionary = strolls[floori(idx / 3.0) % strolls.size()]
		var t_s := maxf(t_block + 6.0 * beat, busy_until + 0.25 * beat)
		if t_s <= t_block + 9.0 * beat:
			var bars := pick_bars(float(s.get("bars", 3.0)), notes, t_s, bpm)
			var args := {"bars": bars}
			for k in ["fwd", "right", "turn"]:
				if s.has(k):
					args[k] = float(s[k])
			out.append(_action(t_s, "player_walk", args))
	return out


## Stepping into this node's world from another one (the passage walk): a cut to the doorway, then the walk to the floor, starting in the guard two beats before
## the downbeat `t0`. Nothing when the node has no separate doorway.
func arrival(t0: float, notes: Array) -> Array:
	var out: Array = []
	var beat := 60.0 / bpm
	var t_walk := t0 - 2.0 * beat
	if arrive != "" and arrive != home:
		out.append(_action(t_walk - 0.5 * beat, "player_move", {"to": arrive, "style": "walk", "bars": 0.01, "cut": true}))
		_move_to(out, t_walk, home, "walk", 3.0, notes)
	out.append(_action(t0, "player_role", {"role": "dancer"}))
	return out


## Moving to a new node of the same world (the stage stays): the rail starts again from home; the camera stays where it is until the first decision moves it.
func restart_here() -> void:
	reset()
