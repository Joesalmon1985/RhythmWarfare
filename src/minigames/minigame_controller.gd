class_name MinigameController
extends RefCounted
## Owns the life of one minigame inside the run (docs/BLACKJACK_INTEGRATION.md section 5.4), pure logic: no nodes, no clock. RunPlay feeds it song time and the judge's block results.
##
## States: "" (none), "entering" (requested at the commit; the run is held at its scene until the seat time), "active" (seated), "leaving" (an exit or a fall was asked for; the activity
## finishes its animation). While a minigame lives `engine.hold` is true; it is released when the activity reports `is_done()`. The generic rhythm rule lives here: failed blocks in a row
## wobble the player (`wobble_at`, 2) and then drop them (`fall_at`, 3); a pass resets the count. Both come from the activity's config. Same calls give the same log.

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


func is_registered(id: String) -> bool:
	return _registry.has(id)


## The player sits: the run is held at its scene from now, `begin` is called at `t_seat` (the next downbeat). False for an unknown id or while another activity lives.
func request(id: String, t_commit: float, t_seat: float) -> bool:
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
	_config = rec["config"]
	started += 1
	last_seed = _next_seed()
	_fails = 0
	begin_t = -1.0
	seat_t = t_seat
	activity.setup({"wallet": wallet, "seed": last_seed, "beat_s": engine.beat_s if engine != null else 60.0 / 174.0, "config": _config})
	if engine != null:
		engine.hold = true
	state = "entering"
	log.append({"kind": "request", "id": id, "t": t_commit, "seat": t_seat, "seed": last_seed})
	return true


func _next_seed() -> int:
	if OS.get_environment("RW_MINIGAME_SEED") != "":
		return int(OS.get_environment("RW_MINIGAME_SEED"))
	return absi(run_seed * 2654435761 + started * 40503 + 12345) % 2147483647


func active() -> bool:
	return state != ""


## Advance to song time `t`: seats the player on the downbeat, advances the activity, and finishes when it is done.
func update(t: float) -> void:
	if state == "":
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
func on_block_result(passed: bool, t: float) -> void:
	if state != "active":
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


## The run ended. Before the player was seated there is nothing to refund: the activity is dropped unbegun.
func on_run_over(t: float) -> void:
	if state == "entering":
		_finish(t, "run_over")
	elif state == "active":
		_interrupt("run_over", t)


## The player chose to get up (the host's own exit, a scripted tap). The activity's exit target does the same through `tap`.
func request_leave(t: float) -> void:
	if state == "active":
		activity.request_leave(t)
		state = "leaving"
		log.append({"kind": "leave", "t": t})


## A touch on an activity target; forwarded only while seated. Returns whether the activity took it.
func tap(target: String, t: float) -> bool:
	if state != "active":
		return false
	var ok := activity.tap(target, t)
	log.append({"kind": "tap", "target": target, "ok": ok, "t": t})
	return ok


func _interrupt(reason: String, t: float) -> void:
	activity.interrupt(reason, t)
	state = "leaving"
	log.append({"kind": "interrupt", "reason": reason, "t": t})


func _finish(t: float, reason := "") -> void:
	var why := reason if reason != "" else activity.done_reason()
	if engine != null:
		engine.hold = false
	state = ""
	log.append({"kind": "finished", "reason": why, "t": t})
	activity = null
	activity_id = ""
