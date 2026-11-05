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
var cine_until := -1.0  # song time a hotspot cinematic's move ends (the next scene's door walk waits for it)
## (node id, the rail's place after the block-2 decision) -> [[x, z, keep, height], ...]: the window's hotspots, the default kept ([] none). The run scene gives it; the camera frames them with a
## StoryPlayer `face` look (StoryPlayer.best_facing from wherever the rail is); unset, block 3 keeps its ordinary glance and stroll.
var face_fn: Callable

const FACE_TURN_BEAT := 49.0  # the phase beat the window's hotspots are framed by
const FACE_RELEASE_BEAT := 60.5  # the head hands back to the rail from the lock beat (the commit), by the phase's end


func _init(p_data: RunData) -> void:
	data = p_data


func on_event(ev: Dictionary, engine: RunEngine) -> Array:
	var out: Array = []
	match str(ev["kind"]):
		"phase_start":
			out = _phase_start(ev, engine)
		"block_result":
			out = _block_result(ev, engine)
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
	out.append_array(rail.ambient(t0, int(ev["phase"]), 0, engine.level.notes))
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


## The rail actions of a hotspot outcome's cinematic ({steps: [{move, to, bars, role, style, look_at}]}, see HotspotContract) starting at song time `t` (a decision beat, inside the cue-free
## guard). The steps run one after another: a `walk` is a rail move (style, 2 to 4 bars, shortened where the chart is dense: RunRail.pick_bars), a `place` a cut, `role` a role change and `look_at` a
## glance at the target (`look_fn(id) -> degrees`, NAN when it cannot be placed). With `move_ok` false (the outcome names a route: the door walk toward it is the camera's move) only the roles and
## glances are given, and a step's walking style becomes the style of the door walk (an exit failure staggers through the same door).
func hotspot_actions(spec: Dictionary, t: float, engine: RunEngine, look_fn: Callable, move_ok: bool) -> Array:
	var out: Array = []
	if rail == null or spec.is_empty():
		return out
	var cur := t
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
			var bars := rail._move_to(out, cur, str(st["to"]), style, float(st.get("bars", 3.0)), engine.level.notes)
			cur += bars * rail.bar_s()
	if move_ok:
		cine_until = maxf(cine_until, cur)
	var tagged := _tag(out, world)
	actions.append_array(tagged)
	return tagged


func _block_result(ev: Dictionary, engine: RunEngine) -> Array:
	var b := int(ev["block"])
	var notes := engine.level.notes
	var out: Array = rail.step(bool(ev["passed"]), float(ev["t"]), notes)
	var last: Dictionary = rail.visited[rail.visited.size() - 1]
	log.append({"phase": int(ev["phase"]), "block": b, "node": str(ev["node"]), "place": last["place"], "kind": last["kind"], "role": last["role"], "pos": last["pos"]})
	if b < 3:  # the glance and the stroll of the next block; the last block's is the turn to the window's hotspots
		var face: Array = face_fn.call(str(ev["node"]), rail.place()) if b == 2 and face_fn.is_valid() else []
		if not face.is_empty():
			out.append(window_face(face, float(ev["t"]), engine))
		else:
			out.append_array(rail.ambient(engine.t_of(float(b + 1) * engine.timing("block_beats")), int(ev["phase"]), b + 1, notes))
	return _tag(out, world)


## The last block's look: from the block-2 decision (in its cue-free guard) the head turns to frame `pts` ([[x, z, keep, height], ...], the window's hotspots) by beat 49, holds them from wherever the
## rail walks underneath, and hands back to the rail from the lock beat to the phase's end (where a door walk takes over). A look, never a move: the route is untouched.
func window_face(pts: Array, t: float, engine: RunEngine) -> Dictionary:
	var bar := rail.bar_s()
	var t_end := engine.t_of(4.0 * engine.timing("block_beats"))
	var turn := maxf(engine.t_of(FACE_TURN_BEAT) - t, 0.5 * bar)
	var release := maxf(t_end - engine.t_of(FACE_RELEASE_BEAT), 0.25 * bar)
	return {"t0": t, "action": "player_look", "args": {"face": pts.duplicate(true), "bars": (t_end - t) / bar, "turn_bars": turn / bar, "release_bars": release / bar}}
