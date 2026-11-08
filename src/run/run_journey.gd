class_name RunJourney
extends RefCounted
## Turns the run engine's events into the player's journey: one RunRail per node (kept across a loop, restarted for a new node), the glance and stroll of every
## block, and the walk through the doorway into a new world. Pure logic: events in, stage actions out ({world, t0, action, args}). The run scene hands them to the
## stages; the playtests feed the same events and read the same log, so what they check is what the player sees.

var data: RunData
var rail: RunRail
var node_id := ""
var world := ""  # the art world (the stage) the player is in
var run_world := ""  # the run world (the save's id)
var door_target := ""  # the scene a door walk was started toward ("" none)
var skip_arrival := false  # the next phase start is a resume (the Bassment's return): the scene walks the camera itself
var log: Array = []  # [{phase, block, node, place, kind, role, pos}] one per block decision
var actions: Array = []  # every action emitted, with its world
var door_style := "walk"  # the walking style of the next door walk (an exit failure staggers)
var leaving := false  # a threshold walk out of this phase's scene is under way (H1.6, ruling 39): the rail takes no more steps until the next phase
var cine_until := -1.0  # song time a hotspot cinematic's move ends (the next scene's door walk waits for it)
## A walk-out at a walking pace (LEAD_RULINGS 42) may need longer than the beats left before the phase's boundary: the walk and its doorway hold then run on into the next phase
## while its music plays, and the world swap (the passage frame, the cut to the new world's doorway, the arrival) waits for the hold to end, on a whole beat (`cut_t`, song time; -1:
## the swap is on the boundary as before). At the next phase's start it becomes `swap_t` (RunPlay shows the new world then) and the new scene's rail waits for the arrival (`arriving_until`).
var cut_t := -1.0
var swap_t := -1.0
var arriving_until := -1.0
var walk_offs: Array = []  # [{t, node, to, from, length, bars, pace, hold_bars, cut_t, paced}] one per walk-out from a choice tap (the tests and the playtests read it)
## (node id, the rail's place after the block-2 decision) -> [[x, z, keep, height], ...]: the window's hotspots, the default kept ([] none). The run scene gives it; the camera frames them with a
## StoryPlayer `face` look (StoryPlayer.best_facing from wherever the rail is); unset, block 3 keeps its ordinary glance and stroll.
var face_fn: Callable

const FACE_TURN_BEAT := 49.0  # the phase beat the window's hotspots are framed by
const FACE_RELEASE_BEAT := 60.5  # the head hands back to the rail from the lock beat (the commit), by the phase's end
## The latest beat of the next phase a walk-out's cut may fall on: the arrival walk (3 bars at most, from 2 beats before the cut) is then over before the next scene's block-2
## decision (beat 44.75), which walks to its choice viewpoint for the next choice window (beat 49). A walk-out that would end later loses its hold first, then is shortened.
const CUT_LATEST_BEAT := 32.0
## The heralds' look (docs/art/HERALDS.md, the visibility rule): in the opening of a scene the head turns to each quest entrance on offer and its herald, one entrance a block
## (the first in block 0, the next in block 1, at most three), from HERALD_LOOK_FROM to HERALD_LOOK_TO beats into its block, turning in and handing back over HERALD_TURN_BARS.
## A look, never a move: the rail and the route are untouched, and the block's own glance is left out so it never swings the entrance away.
const HERALD_LOOK_FROM := 0.5
const HERALD_LOOK_TO := 15.0
const HERALD_TURN_BARS := 1.0
const HERALD_MAX_LOOKS := 3

var walk_pace := true  # the walk-out from a choice tap at a walking pace (ruling 42; the tests of ruling 39's authored bars turn it off)
var look_heralds := true  # the heralds' look and the window's herald points (the tests turn it off to see the rail's own camera)
var glance_skips: Dictionary = {}  # why a block got no glance of its own -> count (RunRail.last_skip; tools/run/walk_run.sh prints it)
var _herald_blocks: Dictionary = {}  # block -> true: the blocks of this phase whose glance a herald look replaces
static var _maps: Dictionary = {}


func _init(p_data: RunData) -> void:
	data = p_data


func on_event(ev: Dictionary, engine: RunEngine) -> Array:
	var out: Array = []
	match str(ev["kind"]):
		"phase_start":
			out = _phase_start(ev, engine)
		"block_result":
			out = _block_result(ev, engine)
		"lap_start":  # the same scene again, the rail where it has got to: only the glance and the stroll of the lap's first block
			_herald_blocks = {}  # the heralds' look is the scene's opening (its first lap): a later lap's blocks keep their own glances
			out = _tag(_ambient(float(ev["t"]), int(ev["phase"]), 0, engine.level.notes), world)
	actions.append_array(out)
	return out


func _tag(list: Array, w: String) -> Array:
	var out: Array = []
	for a in list:
		var b: Dictionary = (a as Dictionary).duplicate()
		b["world"] = w
		out.append(b)
	return out


func _phase_start(ev: Dictionary, engine: RunEngine) -> Array:
	var id := str(ev["node"])
	var node: Dictionary = data.nodes[id]
	var w := str(node["map"])
	var rw := str(node["world"])
	var t0 := float(ev["t"])
	var first := int(ev["phase"]) == 1
	var changed := rw != run_world  # another world: the passage frame is shut over the swap and the camera steps in from the doorway
	var out: Array = []
	var new_scene := id != node_id
	if new_scene:  # the same scene again keeps the player where the rail has got to
		rail = RunRail.new()
		rail.setup(id, node, float(data.cfg["timing"]["bpm"]))
	if first:
		out.append({"t0": t0, "action": "player_role", "args": {"role": "dancer"}})
	elif skip_arrival:
		skip_arrival = false
	elif changed and cut_t > t0 + 1.0e-6:  # the walk-out is still under way in the world being left (ruling 42): the cut and the arrival wait for its hold to end
		swap_t = cut_t
		out.append_array(rail.arrival(swap_t, engine.level.notes))
		arriving_until = maxf(rail.busy_until, swap_t)
	elif changed:
		out.append_array(rail.arrival(t0, engine.level.notes))
	elif new_scene:  # a path inside the world: a plain door walk, the stage stays (after a hotspot cinematic that is still under way: when it has finished, if that is soon)
		var t_walk := t0
		var walked := door_target == id
		if cine_until > t0:
			walked = cine_until > t0 + 6.0 * engine.beat_s  # too long to wait: the cinematic is where the camera stays
			t_walk = cine_until
		out.append_array(rail.door_walk(t_walk, engine.level.notes, walked))
	if not (changed and cut_t > t0 + 1.0e-6):
		swap_t = -1.0
		arriving_until = -1.0
	cut_t = -1.0
	door_target = ""
	leaving = false
	var looks := herald_looks(id, t0, engine)
	if arriving_until > t0:  # (still walking out, then arriving: block 0's glance and stroll, and the heralds' looks that start before the arrival is over, are left out)
		looks = looks.filter(func(a: Dictionary) -> bool: return float(a["t0"]) >= arriving_until)
		var bb := float(engine.timing("block_beats"))
		for blk in _herald_blocks.keys():
			if t0 + (float(blk) * bb + HERALD_LOOK_FROM) * engine.beat_s < arriving_until:
				_herald_blocks.erase(blk)
	else:
		out.append_array(_without_glance(_ambient(t0, int(ev["phase"]), 0, engine.level.notes), 0))
	out.append_array(looks)
	node_id = id
	world = w
	run_world = rw
	return _tag(out, w)


## A path inside the world: the walk through the door toward the selected route's scene, started three beats before the phase ends (the scene latches it once per phase).
func leave_walk(t: float, to: String, engine: RunEngine) -> Array:
	var target: Dictionary = data.nodes[to]
	var wp := str((target["rail"] as Dictionary).get("arrive", ""))
	if wp == "":
		wp = str(target["waypoint"])
	door_target = to
	var tagged := _tag(rail.leave(t, wp, engine.level.notes, door_style), world)
	door_style = "walk"
	actions.append_array(tagged)
	return tagged


## A world exit's approach (CONTRACTS.md 1, H1.6): the player walks to the threshold spot `wp` from song time `t` and is there by the boundary `t_boundary`, where the
## world transition (the passage frame, the stage swap) takes over: walk first, then the transition. `bars` is the leg's length (2 to 4); a walk that would run past
## the boundary is shortened to end on it (the guard before a boundary is shorter than a bar: CONTRACTS.md 3, the leg-length disagreement).
## `move` (optional) is the route's move {to, via?, bars?, hold_bars?, style?} (threshold_move): the walk follows its `via` polyline over its bars, still ending by the boundary, and keeps
## its hold at the threshold only when there is time for it before the boundary.
## `paced_from` (a walk-out from a choice tap, ruling 42: the rail's place at the tap): the leg's length from there (RunRail.leg_length) sets the least bars, at no more than
## RunRail.WALK_PACE_MAX m/s (RunRail.walk_off_bars, 2 to 8). A leg the authored bars already walk at that pace is exactly as before. A longer one keeps its paced bars and its hold
## even past the boundary, up to the next phase's CUT_LATEST_BEAT (the hold goes first, then the leg is shortened), and the world swap waits for it on a whole beat (`cut_t`).
func threshold_walk(t: float, t_boundary: float, wp: String, bars := 2.0, move: Dictionary = {}, paced_from := "") -> Array:
	if rail == null or wp == "" or t_boundary <= t:
		return []
	var bar := rail.bar_s()
	var beat := bar / 4.0
	var avail := (t_boundary - t) / bar
	var want := float(move.get("bars", bars)) if not move.is_empty() else bars
	var b := clampf(want, RunRail.MOVE_BARS_MIN, RunRail.MOVE_BARS_MAX)
	var length := -1.0
	var paced := false
	if paced_from != "":
		length = RunRail.leg_length(_map_of(node_id), paced_from, {"to": wp, "via": move.get("via", [])})
		if length > RunRail.WALK_PACE_MAX * b * bar + 1.0e-6:  # the authored bars would walk it faster than walking pace
			paced = true
			b = maxf(b, RunRail.walk_off_bars(length, bar))
			avail = (t_boundary + CUT_LATEST_BEAT * beat - t) / bar
	b = minf(b, avail)
	var style := str(move.get("style", door_style)) if door_style == "walk" else door_style  # (an exit failure's stagger wins over the route's own style)
	var args := {"to": wp, "style": style, "bars": b, "threshold": true}
	if typeof(move.get("via")) == TYPE_ARRAY and not (move["via"] as Array).is_empty():
		args["via"] = (move["via"] as Array).duplicate()
	var hold := minf(maxf(float(move.get("hold_bars", 0.0)), 0.0), avail - b)
	cut_t = -1.0
	var t_end := t + (b + maxf(hold, 0.0)) * bar
	if paced and t_end > t_boundary + 1.0e-6:  # past the boundary: the swap waits for the hold to end, on the next whole beat (the hold runs on to it)
		cut_t = t_boundary + ceilf((t_end - t_boundary) / beat - 1.0e-6) * beat
		hold = (cut_t - t) / bar - b
	if paced_from != "":
		var pace := length / (b * bar) if length > 0.0 and b > 0.0 else 0.0
		walk_offs.append({"t": t, "node": node_id, "to": wp, "from": paced_from, "length": length, "bars": b, "pace": pace, "hold_bars": maxf(hold, 0.0), "cut_t": cut_t, "paced": paced})
		var cut_txt := "the cut %.2f beats after the boundary" % ((cut_t - t_boundary) / beat) if cut_t > 0.0 else "the cut on the boundary"
		print("RUN walk-off %s %s -> %s: leg %.1f m, %.2f bars (%.2f m/s, at most %.1f), hold %.2f bars, %s" % [node_id, paced_from, wp, length, b, pace, RunRail.WALK_PACE_MAX, maxf(hold, 0.0), cut_txt])
	if hold > 1.0e-6:
		args["hold_bars"] = hold
	if hold > 1.0e-6:
		rail.hold_from = t + b * rail.bar_s()
	rail.busy_until = t + (b + maxf(hold, 0.0)) * rail.bar_s()
	var tagged := _tag([{"t0": t, "action": "player_move", "args": args}], world)
	door_style = "walk"
	leaving = true
	actions.append_array(tagged)
	return tagged


## The walk out of scene `from` toward `to` in another world, started at `t` and ending by the boundary `t_boundary` (the lock handler, RunPlay._update_passage): the route's
## move when the scene has one (its polyline), else a straight walk to the threshold spot; [] when the route has no threshold.
## `paced` (the walk-out from a choice tap, commit_walk): at a walking pace from the rail's place (threshold_walk's `paced_from`).
func threshold_leave(t: float, t_boundary: float, from: String, to: String, paced := false) -> Array:
	var wp := threshold_of(from, to)
	if wp == "":
		return []
	var move := threshold_move(from, to)
	return threshold_walk(t, t_boundary, wp, 2.0, move if str(move.get("to", "")) == wp else {}, rail.place() if paced and walk_pace and rail != null else "")


## The walk out at a committed choice (lead ruling on H1.6, "you chose, you go"): a `hotspot_commit` event `ev` of the final window for a touched choice (not the untouched default)
## whose route leads to another world with a threshold starts the threshold walk at the commit's own time, with the route move's authored bars (clamped 2 to 4) and its hold, each only
## as far as it fits before the phase's boundary (a late commit is shortened, never run past it); a leg those bars would walk faster than RunRail.WALK_PACE_MAX takes its paced bars
## instead (2 to 8, ruling 42) and may run on past the boundary (threshold_walk). [] otherwise: the lock (beat 61) then walks the default as before.
func commit_walk(ev: Dictionary, engine: RunEngine) -> Array:
	var out: Dictionary = ev.get("outcome", {})
	if out.is_empty() or str(out.get("window", "")) != "final" or not bool(out.get("tapped", false)) or bool(out.get("stays", false)):
		return []
	var to := str(out.get("route", ""))
	var from := str(ev.get("node", engine.node_id))
	if not data.nodes.has(to) or not data.nodes.has(from) or to == from or str(data.nodes[to]["world"]) == str(data.nodes[from]["world"]):
		return []
	return threshold_leave(float(ev["t"]), engine.t_of(float(engine.timing("phase_beats"))), from, to, true)


## The threshold spot of the route out of scene `from` to `to` in another world: the node's `thresholds` {route id: waypoint} (data of contract 1), else the route's own move
## (threshold_move: its `to`); "" when there is neither.
func threshold_of(from: String, to: String) -> String:
	var explicit := str(((data.nodes.get(from, {}) as Dictionary).get("thresholds", {}) as Dictionary).get(to, ""))
	if explicit != "":
		return explicit
	return str(threshold_move(from, to).get("to", ""))


## The route move of scene `from` toward `to` (docs/engine/GEOGRAPHY_WORLDS.md): the `next` entry leading to `to` gives the direction, the rail's `routes[dir]` is the move
## {to (the threshold waypoint), via?, bars?, hold_bars?, style?}. {} when the route is the stay (`down`), is not a world exit, or the rail has no move for it.
func threshold_move(from: String, to: String) -> Dictionary:
	var n: Dictionary = data.nodes.get(from, {})
	if n.is_empty() or not data.nodes.has(to) or str(data.nodes[to]["world"]) == str(n["world"]):
		return {}
	for e in n.get("next", []):
		if str(e["to"]) != to:
			continue
		var dir := str(e["dir"])
		if dir == "down":
			return {}
		var mv: Variant = ((n.get("rail", {}) as Dictionary).get("routes", {}) as Dictionary).get(dir)
		return (mv as Dictionary) if typeof(mv) == TYPE_DICTIONARY and str((mv as Dictionary).get("to", "")) != "" else {}
	return {}


## The rail actions of a hotspot outcome's cinematic ({steps: [{move, to, bars, role, style, look_at}]}, see HotspotContract) starting at song time `t` (a decision beat, inside the cue-free
## guard). The steps run one after another: a `walk` is a rail move (style, 2 to 4 bars, shortened where the chart is dense: RunRail.pick_bars), a `place` a cut, `role` a role change and `look_at` a
## glance at the target (`look_fn(id) -> degrees`, NAN when it cannot be placed). With `move_ok` false (the outcome names a route: the door walk toward it is the camera's move) only the roles and
## glances are given, and a step's walking style becomes the style of the door walk (an exit failure staggers through the same door).
func hotspot_actions(spec: Dictionary, t: float, engine: RunEngine, look_fn: Callable, move_ok: bool) -> Array:
	var out: Array = []
	if rail == null or spec.is_empty():
		return out
	var cur := t
	var first_hold := -1.0
	for st in spec.get("steps", []):
		if st.has("role"):
			out.append({"t0": cur, "action": "player_role", "args": {"role": str(st["role"])}})
			rail.role = str(st["role"])
		if st.has("look_at") and look_fn.is_valid():
			var by: float = look_fn.call(str(st["look_at"]))
			if not is_nan(by):
				out.append({"t0": cur, "action": "player_look", "args": {"by": by, "pitch": 0.0, "bars": 2.0}})
		if not st.has("to") or not st.has("move"):
			continue
		if not move_ok:
			door_style = str(st.get("style", "walk"))
			continue
		if str(st["move"]) == "place":
			out.append({"t0": cur, "action": "player_move", "args": {"to": str(st["to"]), "style": "walk", "bars": 0.01, "cut": true}})
		else:
			var style := str(st.get("style", st["move"] if str(st["move"]) in RunRail.STYLES else "walk"))
			var hb := maxf(float(st.get("hold_bars", 0.0)), 0.0)  # a route leg (CONTRACTS.md 3, ruling 35a): move, then hold still; RunRail._move_to puts the hold on the move (StoryPlayer stands still)
			var bars := rail._move_to(out, cur, str(st["to"]), style, float(st.get("bars", 3.0)), engine.level.notes, {"hold_bars": hb} if hb > 0.0 else {})
			if hb > 0.0 and first_hold < 0.0:
				first_hold = rail.hold_from
			cur += (bars + hb) * rail.bar_s()
	if first_hold >= 0.0:  # (the route's holds, and the moves between them, are one span the rail's glances and steps keep out of: RunRail._in_hold)
		rail.hold_from = first_hold
		rail.busy_until = maxf(rail.busy_until, cur)
	if move_ok:
		cine_until = maxf(cine_until, cur)
	var tagged := _tag(out, world)
	actions.append_array(tagged)
	return tagged


func _block_result(ev: Dictionary, engine: RunEngine) -> Array:
	var b := int(ev["block"])
	var notes := engine.level.notes
	if leaving:  # (the player is walking out to another world: no rail step, no glance, no stroll; the walk is the camera's move)
		log.append({"phase": int(ev["phase"]), "block": b, "node": str(ev["node"]), "place": rail.place(), "kind": "leaving", "role": rail.role, "pos": rail.pos})
		return []
	if float(ev["t"]) < arriving_until:  # (a walk-out ran on into this phase: the camera is still arriving; the rail takes its first step after the arrival)
		log.append({"phase": int(ev["phase"]), "block": b, "node": str(ev["node"]), "place": rail.place(), "kind": "arriving", "role": rail.role, "pos": rail.pos})
		return []
	var out: Array = rail.step(bool(ev["passed"]), float(ev["t"]), notes, engine.t_of(FACE_TURN_BEAT) if b == 2 else -1.0)
	var last: Dictionary = rail.visited[rail.visited.size() - 1]
	log.append({"phase": int(ev["phase"]), "block": b, "node": str(ev["node"]), "place": last["place"], "kind": last["kind"], "role": last["role"], "pos": last["pos"]})
	if b == 2 and rail.at_choice():  # a choice viewpoint (docs/story/HEIGHTS_AND_PATHS.md): the camera stands still through the whole choice window, the viewpoint frames the choices
		var w0 := engine.t_of(FACE_TURN_BEAT)
		var hold := {"bars": (engine.t_of(FACE_RELEASE_BEAT) - w0) / rail.bar_s(), "hold": "window"}
		var vp := float(rail.place_spec().get("pitch", 0.0))
		if vp != 0.0:  # the viewpoint's authored steady pitch (RunRail place `pitch`, degrees, negative down): held through the window, released by the walk-off; unauthored, the hold is as before
			hold["pitch"] = vp
		out.append({"t0": w0, "action": "player_hold", "args": hold})
	elif b < 3:  # the glance and the stroll of the next block; the last block's is the turn to the window's hotspots
		var face: Array = face_fn.call(str(ev["node"]), rail.place()) if b == 2 and face_fn.is_valid() else []
		if not face.is_empty():
			out.append(window_face(face, float(ev["t"]), engine))
		else:
			out.append_array(_without_glance(_ambient(engine.t_of(float(b + 1) * engine.timing("block_beats")), int(ev["phase"]), b + 1, notes), b + 1))
	return _tag(out, world)


## The rail's glance and stroll of a block, with the reason tallied when the rail gives no glance.
func _ambient(t_block: float, phase_n: int, block: int, notes: Array) -> Array:
	var out := rail.ambient(t_block, phase_n, block, notes)
	if rail.last_skip != "":
		glance_skips[rail.last_skip] = int(glance_skips.get(rail.last_skip, 0)) + 1
	return out


## The map of a run node (the heralds' points need its floors), loaded once.
func _map_of(id: String) -> StoryMap:
	var m := str((data.nodes.get(id, {}) as Dictionary).get("map", ""))
	if m == "":
		return null
	if not _maps.has(m):
		var sm := StoryMap.load_chapter(m, false)
		_maps[m] = sm if sm.errors.is_empty() else null
	return _maps[m]


## The heralds of scene `id` on offer from its first beat (RunHotspots.staged: an entrance behind a flag only when the flag is set), in file order: [herald block, ...].
func staged_heralds(id: String, engine: RunEngine) -> Array:
	var out: Array = []
	if engine == null or engine.hotspots == null or engine.hotspots.node != id:
		return out
	for h in engine.hotspots.staged(0):
		if (h as Dictionary).has("herald"):
			out.append(h["herald"])
	return out


## The heralds' opening look (the visibility rule, docs/art/HERALDS.md): one `face` look a staged entrance, in blocks 0, 1 and 2 of the phase starting at `t0`, holding the entrance,
## its mark and its herald in the picture from wherever the rail is (StoryPlayer.best_facing), and the other staged entrances with it where they fit (their points, not kept). Data only:
## the herald blocks' points, never a hand-tuned angle. The turn stops short of a near wall (StoryPlayer.herald_cap) and never starts in a door walk's last beat.
func herald_looks(id: String, t0: float, engine: RunEngine) -> Array:
	_herald_blocks = {}
	var out: Array = []
	if not look_heralds:
		return out
	var m := _map_of(id)
	var heralds := staged_heralds(id, engine)
	var beat := engine.beat_s
	var bb := float(engine.timing("block_beats"))
	for i in mini(heralds.size(), HERALD_MAX_LOOKS):
		var pts := StoryHeralds.look_points(heralds[i], m)
		if pts.is_empty():
			continue
		for k in heralds.size():  # a scene with more entrances than one look a block plus the window can show (the Floor: four gates and its wizard): the others ride along, not kept
			if k != i and heralds.size() > HERALD_MAX_LOOKS + 1:
				pts.append_array(StoryHeralds.look_points(heralds[k], m, 0.0))
		var t_look := t0 + (float(i) * bb + HERALD_LOOK_FROM) * beat
		var t_end := t0 + (float(i) * bb + HERALD_LOOK_TO) * beat
		if rail != null and rail.busy_until > t_look and rail.busy_until - t_look <= beat:  # never start in a door walk's last beat: the walk turns the body to its arrival yaw there (docs/art/CAMERA_CLEARANCE.md, "The herald look")
			t_look = rail.busy_until
		var b := (t_end - t_look) / rail.bar_s()
		if b <= HERALD_TURN_BARS:  # no room for the look: the block keeps its own glance
			continue
		_herald_blocks[i] = true
		out.append({"t0": t_look, "action": "player_look", "args": {"face": pts, "bars": b, "turn_bars": HERALD_TURN_BARS, "release_bars": HERALD_TURN_BARS, "herald": true}})
	return out


## `list` (a block's ambient actions) without its glance when a herald look holds that block.
func _without_glance(list: Array, block: int) -> Array:
	if not _herald_blocks.has(block):
		return list
	return list.filter(func(a: Dictionary) -> bool: return not (str(a["action"]) == "player_look" and not (a["args"] as Dictionary).has("face")))


## The last block's look: from the block-2 decision (in its cue-free guard) the head turns to frame `pts` ([[x, z, keep, height], ...], the window's hotspots) by beat 49, holds them from wherever the
## rail walks underneath, and hands back to the rail from the lock beat to the phase's end (where a door walk takes over). A look, never a move: the route is untouched.
func window_face(pts: Array, t: float, engine: RunEngine) -> Dictionary:
	var bar := rail.bar_s()
	var t_end := engine.t_of(4.0 * engine.timing("block_beats"))
	var turn := maxf(engine.t_of(FACE_TURN_BEAT) - t, 0.5 * bar)
	var release := maxf(t_end - engine.t_of(FACE_RELEASE_BEAT), 0.25 * bar)
	return {"t0": t, "action": "player_look", "args": {"face": with_heralds(pts, engine), "bars": (t_end - t) / bar, "turn_bars": turn / bar, "release_bars": release / bar}}


## The window look's weights (docs/art/HERALDS.md, the window rule): of the groups of choices the head can hold with the default exit, the one holding the most weight is framed. A quest
## entrance weighs WINDOW_ENTRANCE_W, a way back (a path's `<quest>.return`, a scene's `<scene>.to_hub`) WINDOW_RETURN_W, every other choice 1: a way back never pulls the picture off the
## quest entrances, and it is framed beside them when it fits (its placement keeps it in the picture at the window: tests/test_heralds_view.gd).
const WINDOW_ENTRANCE_W := 2.0
const WINDOW_RETURN_W := 0.5


static func is_way_back(h: Dictionary) -> bool:
	var id := str(h.get("id", ""))
	return id.ends_with(".return") or id.ends_with(".to_hub")


## The window look's points [[x, z, keep (the default), height, weight], ...] of hotspot rows `rows` (RunHotspots.shown in the last block): the rows on show in the final window, resolved
## on map `m` (and the crowd, for a person); the run scene (RunPlay._window_face) and the tests that replay its journey build the same list here.
static func window_points(rows: Array, m: StoryMap, crowds: Variant = {}) -> Array:
	var pts: Array = []
	for h in rows:
		if RunHotspots.window_of(h) != "final":
			continue
		var r := HotspotView.resolve(h["anchor"], m, crowds)
		if bool(r["ok"]):
			var p: Vector3 = r["pos"]
			var w := WINDOW_ENTRANCE_W if (h as Dictionary).has("herald") else (WINDOW_RETURN_W if is_way_back(h) else 1.0)
			pts.append([p.x, p.z, 1.0 if bool(h["default"]) else 0.0, p.y, w])
	return pts


## The window's points with the herald of every quest entrance on show in the window added (where it stands, not kept: the default exit still decides the group, and of the
## groups holding it the one with the entrance and its herald counts one more, so it is framed whenever it fits beside the default).
func with_heralds(pts: Array, engine: RunEngine) -> Array:
	var out := pts.duplicate(true)
	if not look_heralds or engine == null or engine.hotspots == null:
		return out
	var m := _map_of(engine.hotspots.node)
	for h in engine.hotspots.shown(3, true):
		if (h as Dictionary).has("herald") and RunHotspots.window_of(h) == "final":
			var hp := StoryHeralds.look_points(h["herald"], m, 0.0)
			if hp.size() >= 3:
				var q: Array = (hp[2] as Array).duplicate()
				while q.size() < 4:
					q.append(NAN if q.size() == 3 else 0.0)
				q.append(WINDOW_ENTRANCE_W)
				out.append(q)  # (the herald's feet: one point, weighing what its entrance weighs, so the window frames the pair whenever it fits beside the default)
	return out
