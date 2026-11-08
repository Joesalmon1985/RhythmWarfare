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
## (node id, the rail's place after the block-2 decision) -> [[x, z, keep, height], ...]: the window's hotspots, the default kept ([] none). The run scene gives it; the camera frames them with a
## StoryPlayer `face` look (StoryPlayer.best_facing from wherever the rail is); unset, block 3 keeps its ordinary glance and stroll.
var face_fn: Callable

const FACE_TURN_BEAT := 49.0  # the phase beat the window's hotspots are framed by
const FACE_RELEASE_BEAT := 60.5  # the head hands back to the rail from the lock beat (the commit), by the phase's end
## The heralds' look (docs/art/HERALDS.md, the visibility rule): in the opening of a scene the head turns to each quest entrance on offer and its herald, one entrance a block
## (the first in block 0, the next in block 1, at most three), from HERALD_LOOK_FROM to HERALD_LOOK_TO beats into its block, turning in and handing back over HERALD_TURN_BARS.
## A look, never a move: the rail and the route are untouched, and the block's own glance is left out so it never swings the entrance away.
const HERALD_LOOK_FROM := 0.5
const HERALD_LOOK_TO := 15.0
const HERALD_TURN_BARS := 1.0
const HERALD_MAX_LOOKS := 3

var look_heralds := true  # the heralds' look and the window's herald points (the tests turn it off to see the rail's own camera)
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
			out = _tag(rail.ambient(float(ev["t"]), int(ev["phase"]), 0, engine.level.notes), world)
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
	elif changed:
		out.append_array(rail.arrival(t0, engine.level.notes))
	elif new_scene:  # a path inside the world: a plain door walk, the stage stays (after a hotspot cinematic that is still under way: when it has finished, if that is soon)
		var t_walk := t0
		var walked := door_target == id
		if cine_until > t0:
			walked = cine_until > t0 + 6.0 * engine.beat_s  # too long to wait: the cinematic is where the camera stays
			t_walk = cine_until
		out.append_array(rail.door_walk(t_walk, engine.level.notes, walked))
	door_target = ""
	leaving = false
	var looks := herald_looks(id, t0, engine)
	out.append_array(_without_glance(rail.ambient(t0, int(ev["phase"]), 0, engine.level.notes), 0))
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
func threshold_walk(t: float, t_boundary: float, wp: String, bars := 2.0, move: Dictionary = {}) -> Array:
	if rail == null or wp == "" or t_boundary <= t:
		return []
	var avail := (t_boundary - t) / rail.bar_s()
	var want := float(move.get("bars", bars)) if not move.is_empty() else bars
	var b := minf(clampf(want, RunRail.MOVE_BARS_MIN, RunRail.MOVE_BARS_MAX), avail)
	var style := str(move.get("style", door_style)) if door_style == "walk" else door_style  # (an exit failure's stagger wins over the route's own style)
	var args := {"to": wp, "style": style, "bars": b, "threshold": true}
	if typeof(move.get("via")) == TYPE_ARRAY and not (move["via"] as Array).is_empty():
		args["via"] = (move["via"] as Array).duplicate()
	var hold := minf(maxf(float(move.get("hold_bars", 0.0)), 0.0), avail - b)
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
func threshold_leave(t: float, t_boundary: float, from: String, to: String) -> Array:
	var wp := threshold_of(from, to)
	if wp == "":
		return []
	var move := threshold_move(from, to)
	return threshold_walk(t, t_boundary, wp, 2.0, move if str(move.get("to", "")) == wp else {})


## The walk out at a committed choice (lead ruling on H1.6, "you chose, you go"): a `hotspot_commit` event `ev` of the final window for a touched choice (not the untouched default)
## whose route leads to another world with a threshold starts the threshold walk at the commit's own time, with the route move's authored bars (clamped 2 to 4) and its hold, each only
## as far as it fits before the phase's boundary (a late commit is shortened, never run past it). [] otherwise: the lock (beat 61) then walks the default as before.
func commit_walk(ev: Dictionary, engine: RunEngine) -> Array:
	var out: Dictionary = ev.get("outcome", {})
	if out.is_empty() or str(out.get("window", "")) != "final" or not bool(out.get("tapped", false)) or bool(out.get("stays", false)):
		return []
	var to := str(out.get("route", ""))
	var from := str(ev.get("node", engine.node_id))
	if not data.nodes.has(to) or not data.nodes.has(from) or to == from or str(data.nodes[to]["world"]) == str(data.nodes[from]["world"]):
		return []
	return threshold_leave(float(ev["t"]), engine.t_of(float(engine.timing("phase_beats"))), from, to)


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
			out.append_array(_without_glance(rail.ambient(engine.t_of(float(b + 1) * engine.timing("block_beats")), int(ev["phase"]), b + 1, notes), b + 1))
	return _tag(out, world)


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
## its mark and its herald in the picture from wherever the rail is (StoryPlayer.best_facing). Data only: the herald block's points, never a hand-tuned angle.
func herald_looks(id: String, t0: float, engine: RunEngine) -> Array:
	_herald_blocks = {}
	var out: Array = []
	if not look_heralds:
		return out
	var m := _map_of(id)
	var heralds := staged_heralds(id, engine)
	var beat := engine.beat_s
	var bb := float(engine.timing("block_beats"))
	var bars := (HERALD_LOOK_TO - HERALD_LOOK_FROM) * beat / rail.bar_s()
	for i in mini(heralds.size(), HERALD_MAX_LOOKS):
		var pts := StoryHeralds.look_points(heralds[i], m)
		if pts.is_empty():
			continue
		_herald_blocks[i] = true
		out.append({"t0": t0 + (float(i) * bb + HERALD_LOOK_FROM) * beat, "action": "player_look", "args": {"face": pts, "bars": bars, "turn_bars": HERALD_TURN_BARS, "release_bars": HERALD_TURN_BARS, "herald": true}})
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
				out.append(hp[2])  # (the herald's feet: one point, like every option, so the window never trades the other choices for the herald)
	return out
