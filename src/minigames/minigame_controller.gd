class_name MinigameController
extends RefCounted
## Owns the life of one minigame inside the run (docs/BLACKJACK_INTEGRATION.md section 5.4), pure logic: no nodes, no clock. RunPlay feeds it song time and the judge's block results.
##
## States: "" (none), "entering" (requested at the commit; the run is held at its scene until the seat time), "active" (seated), "leaving" (an exit or a fall was asked for; the activity
## finishes its animation). While a minigame lives `engine.hold` is true; it is released when the activity reports `is_done()`. The generic rhythm rule lives here: failed blocks in a row
## wobble the player (`wobble_at`, 2) and then drop them (`fall_at`, 3); a pass resets the count. Both come from the activity's config. Same calls give the same log.
## The room's exits are handed to the activity at the request; a door the player gets up by is logged (`leave` with its route) and, once the activity is done, is `last_route` for the host.
##
## MODES (CONTRACTS.md 4 and 5, ActivityMode; hooks H5.3, H4.2): the config's `mode` ("rhythm" when absent: the blackjack table, unchanged).
## - rhythm: as above.
## - replace (cloakroom, bar): the request suspends the rhythm from the seat (`engine.suspend_rhythm`), block results never wobble or drop the player, the activity's
##   `controls()` own the pad strip (`owns_strip`). When it is done the state is "resuming" until the boundary B1 (`ContractShapes.resume_boundary`, with the config's
##   `lead_in_beats`): the engine judges again from B1, the strip goes back to the pads `lead_in_beats` before it, and the hold is released at B1 (`finished` logged then).
## - overlay (the race): the pads play on and are judged, block results never wobble or drop the player, and judge events and block results reach the activity
##   (`on_judge`, `on_block`).
## The activity's `result()` is read once when it is done (`last_result`).

const DIR := "res://content/minigames"

var engine: RunEngine
var wallet: Variant = null  # the run's RunWallet, handed to every activity (null in tests)
var run_seed := 0  # the host's run seed: the activity's seed derives from it and the number started so far
var state := ""
var activity: MinigameActivity = null
var activity_id := ""
var log: Array = []  # [{kind: request | begin | wobble | interrupt | leave | finished | tap, t, ...}] every lifecycle step with its song time
var started := 0  # activities started so far in this run
var last_seed := 0
var begin_t := -1.0  # song time the player was seated
var seat_t := -1.0  # song time the player will be seated (the next downbeat after the request)
var last_route := ""  # the route of the door the last activity was left by ("" none: it ended otherwise, or the room had no exits); set when it finishes
var mode := ActivityMode.Mode.RHYTHM  # the living activity's ActivityMode (its config's "mode")
var request_info: Dictionary = {}  # the ActivityRequest the host built ({} when it built none: the activity's own config only)
var last_result: Dictionary = {}  # the last activity's result() (CONTRACTS.md 4), read once when it was done
var done_t := -1.0  # song time the last activity reported done
var resume_t := -1.0  # replace mode: the block start judging resumes on (B1), -1 until the activity is done
var lead_in_s := 0.0  # replace mode: the pads come back this long before resume_t
var finish_t := -1.0  # song time the last activity was finished (the hold released): B1 for a replace activity
var world_port: Object = null  # the room the activity stages itself through (CONTRACTS.md 10: a WorldThings, the run's RunWorldPort), handed over as ctx["world"]; null: none

var _registry: Dictionary = {}  # id -> {script: GDScript | String, config: Dictionary}
var _fails := 0
var _config: Dictionary = {}


func _init(p_engine: RunEngine = null, p_wallet: Variant = null, p_run_seed := 0) -> void:
	engine = p_engine
	wallet = p_wallet
	run_seed = p_run_seed


## Registers an activity: `script` is a GDScript or a `res://` path to one; `config` is handed to the activity whole.
func register(id: String, script: Variant, config: Dictionary = {}) -> void:
	_registry[id] = {"script": script, "config": config}


## Reads every `*.json` in `dir` ({"id", "script", ...}; the whole JSON is the activity's config). A missing directory is an empty registry.
func load_registry(dir := DIR) -> void:
	for d in _read_dir(dir):
		register(str(d["id"]), str(d.get("script", "")), d)


## The ids of the activities in `dir` (the validators call this; empty when the directory does not exist).
static func registered_ids(dir := DIR) -> Array:
	var out: Array = []
	for d in _read_dir(dir):
		out.append(str(d["id"]))
	return out


static func _read_dir(dir: String) -> Array:
	var out: Array = []
	if not DirAccess.dir_exists_absolute(dir):
		return out
	var files := DirAccess.get_files_at(dir)
	files.sort()
	for f in files:
		if not f.ends_with(".json"):
			continue
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join(f)))
		if typeof(parsed) != TYPE_DICTIONARY:
			continue
		var d: Dictionary = parsed
		if not d.has("id"):
			d["id"] = f.get_basename()
		out.append(d)
	return out


## The registered config of activity `id` (its content/minigames json; {} when unknown).
func config_of(id: String) -> Dictionary:
	return (_registry.get(id, {}) as Dictionary).get("config", {})


func is_registered(id: String) -> bool:
	return _registry.has(id)


## The player sits: the run is held at its scene from now, `begin` is called at `t_seat` (the next downbeat). False for an unknown id or while another activity lives.
## `exits`: the room's ways out (MinigameActivity, "exits"), handed to the activity.
## `req`: the host's ActivityRequest (CONTRACTS.md 4: {activity_id, mode, theme, scene_id, return_pose, config}); its `config` (the minigame json merged with the theme's keys)
## replaces the registry's for this activity. {}: the registry's config.
func request(id: String, t_commit: float, t_seat: float, exits: Array = [], req: Dictionary = {}) -> bool:
	if state != "" or not _registry.has(id):
		return false
	var rec: Dictionary = _registry[id]
	var script: Variant = rec["script"]
	if typeof(script) == TYPE_STRING:
		script = load(str(script))
	if script == null or not (script is GDScript):
		return false
	var a: Variant = (script as GDScript).new()
	if not (a is MinigameActivity):
		return false
	activity = a
	activity_id = id
	_config = req["config"] if typeof(req.get("config", null)) == TYPE_DICTIONARY else rec["config"]
	request_info = req
	mode = maxi(ActivityMode.of_config(_config), 0)
	done_t = -1.0
	resume_t = -1.0
	finish_t = -1.0
	last_result = {}
	lead_in_s = maxf(float(_config.get("lead_in_beats", 4.0)), 4.0) * (engine.beat_s if engine != null else 60.0 / 174.0)
	started += 1
	last_seed = _next_seed()
	_fails = 0
	begin_t = -1.0
	seat_t = t_seat
	last_route = ""
	var ctx := {"wallet": wallet, "seed": last_seed, "beat_s": engine.beat_s if engine != null else 60.0 / 174.0, "config": _config, "exits": exits, "request": req}
	if world_port != null:
		ctx["world"] = world_port
	activity.setup(ctx)
	if engine != null:
		engine.hold = true
	state = "entering"
	log.append({"kind": "request", "id": id, "t": t_commit, "seat": t_seat, "seed": last_seed})
	if mode != ActivityMode.Mode.RHYTHM:
		log[log.size() - 1]["mode"] = ActivityMode.name_of(mode)
	if mode == ActivityMode.Mode.REPLACE and engine != null:
		var n := engine.suspend_rhythm(t_seat)
		log.append({"kind": "suspend", "t": t_commit, "from": t_seat, "withdrawn": n})
	return true


func _next_seed() -> int:
	if OS.get_environment("RW_MINIGAME_SEED") != "":
		return int(OS.get_environment("RW_MINIGAME_SEED"))
	return absi(run_seed * 2654435761 + started * 40503 + 12345) % 2147483647


func active() -> bool:
	return state != ""


## The activity's controls own the pad strip at song time `t` (replace mode: from the seat until a lead-in before the resume boundary).
func owns_strip(t: float) -> bool:
	if mode != ActivityMode.Mode.REPLACE or activity == null:
		return false
	match state:
		"active", "leaving":
			return true
		"resuming":
			return t < resume_t - lead_in_s - 1e-9
	return false


## The mode that decides who owns a tap at `t` (ContractShapes.tap_owner): -1 with no activity; a replace activity counts as rhythm while the pads own the strip
## (before the seat, and from the lead-in on), so a strip tap is the pads' and a stage tap still the activity view's.
func input_mode(t: float) -> int:
	if state == "":
		return -1
	if mode == ActivityMode.Mode.REPLACE and not owns_strip(t):
		return ActivityMode.Mode.RHYTHM
	return mode


## The rules of the living activity's mode (ActivityMode.rules; {} with none).
func rules() -> Dictionary:
	return ActivityMode.rules(mode) if state != "" else {}


## Advance to song time `t`: seats the player on the downbeat, advances the activity, and finishes when it is done.
func update(t: float) -> void:
	if state == "":
		return
	if state == "resuming":  # (replace: the activity is done, judging comes back at resume_t)
		if t >= resume_t:
			_end(resume_t, str(last_result.get("reason", "host")))
		return
	if state == "entering":
		if t < seat_t:
			return
		begin_t = seat_t
		state = "active"
		activity.begin(seat_t)
		log.append({"kind": "begin", "t": seat_t})
	activity.update(t)
	if activity.is_done():
		_finish(t)


## A block was judged (`passed`); counts only while seated.
## Only a rhythm-mode activity wobbles and falls (replace and overlay never do: CONTRACTS.md 5).
func on_block_result(passed: bool, t: float) -> void:
	if state != "active" or not bool(ActivityMode.rules(mode).get("wobble_fall", true)):
		return
	if passed:
		_fails = 0
		activity.set_wobble(0, t)
		log.append({"kind": "wobble", "level": 0, "t": t})
		return
	_fails += 1
	if _fails >= int(_config.get("fall_at", 3)):
		_interrupt("fall", t)
	elif _fails >= int(_config.get("wobble_at", 2)):
		activity.set_wobble(1, t)
		log.append({"kind": "wobble", "level": 1, "t": t})


## Overlay mode (H4.2): a judge event of the pads reaches the activity while it is seated.
func on_judge(ev: Dictionary, t: float) -> void:
	if state == "active" and bool(ActivityMode.rules(mode).get("rhythm_to_activity", false)):
		activity.on_judge(ev, t)


## Overlay mode (H4.2): a block result (the engine's event) reaches the activity while it is seated.
func on_block(result: Dictionary) -> void:
	if state == "active" and bool(ActivityMode.rules(mode).get("rhythm_to_activity", false)):
		activity.on_block(result)


## The run ended. Before the player was seated there is nothing to refund: the activity is dropped unbegun.
func on_run_over(t: float) -> void:
	if state == "resuming":
		_end(t, "run_over")
		return
	if state == "entering":
		_finish(t, "run_over")
	elif state == "active":
		_interrupt("run_over", t)


## The player chose to get up (the host's own exit, a scripted tap), by the door to `route` ("" none: the room decides). The activity's exit targets do the same through `tap`.
func request_leave(t: float, route := "") -> void:
	if state == "active":
		if activity.leave_route == "":  # a door already chosen stays chosen
			activity.leave_route = route
		activity.request_leave(t)
		state = "leaving"
		log.append({"kind": "leave", "t": t, "route": route})


## A touch on an activity target; forwarded only while seated. Returns whether the activity took it.
func tap(target: String, t: float) -> bool:
	if state != "active":
		return false
	var ok := activity.tap(target, t)
	log.append({"kind": "tap", "target": target, "ok": ok, "t": t})
	if ok and MinigameActivity.is_exit_target(target):
		log.append({"kind": "leave", "t": t, "route": activity.leave_route, "target": target})
	return ok


func _interrupt(reason: String, t: float) -> void:
	activity.interrupt(reason, t)
	state = "leaving"
	log.append({"kind": "interrupt", "reason": reason, "t": t})


func _finish(t: float, reason := "") -> void:
	var why := reason if reason != "" else activity.done_reason()
	last_route = activity.done_route() if why == "left" else ""
	done_t = t
	last_result = activity.result()
	if str(last_result.get("activity_id", "")) == "":
		last_result["activity_id"] = activity_id
	if reason != "":  # (the host ended it: the run is over, or it never began)
		last_result["reason"] = reason
	if mode == ActivityMode.Mode.REPLACE and engine != null and why != "run_over":  # the clean boundary (CONTRACTS.md 4): judging resumes on a block not yet charted, a lead-in after now
		resume_t = ContractShapes.resume_boundary(t, engine.phase_t0, engine.beat_s, int(engine.timing("block_beats")), engine._decision_beat(), lead_in_s / engine.beat_s)
		engine.resume_rhythm(resume_t)
		state = "resuming"
		log.append({"kind": "resume", "t": t, "at": resume_t, "lead_in_s": lead_in_s, "reason": why})
		return
	_end(t, why)


func _end(t: float, why: String) -> void:
	if engine != null:
		engine.hold = false
		if mode == ActivityMode.Mode.REPLACE and resume_t < 0.0:  # (ended before a boundary was set: the run is over; nothing more is suspended)
			engine.resume_rhythm(t)
	finish_t = t
	state = ""
	log.append({"kind": "finished", "reason": why, "t": t})
	activity = null
	activity_id = ""
