class_name RunHotspots
extends RefCounted
## The hotspot engine, pure logic (no nodes, no clock, no audio): what the player may touch in a scene, what is selected, what commits and what comes of it.
##
## The player's tap is an intent; the performance decides. A scene shows its hotspots in two windows: the FINAL window (beats 49 to 64, the choice window, an exit or an object) and the EARLY
## window (blocks 1 and 2 only) for a hotspot whose success leaves the run for the Bassment (route "trial:<n>": the wizard), which the run has to arm two guards ahead. Selection changes freely until
## the commit: the decision beat of the window's last block (the early one's block, for the final window the last block, beat 60.5 to 60.75, the existing route lock). At the commit the block just
## judged decides: passed -> the hotspot's on_success, missed -> its on_failure. Nothing tapped -> the scene's default exit, whatever the performance.
##
## World state: flags_set names go to `run_flags` (per run, cleared when a run starts) or, with the "keep:" prefix, to `flags` (persistent, saved by RunProgress). Availability reads both.
## The same taps at the same block results always give the same outcomes: nothing here depends on frame timing.

var data: RunData
var run_flags: Dictionary
var flags: Dictionary
var node := ""
var energy := 60.0  # the crowd's energy, kept in step by the engine (availability reads it)
var selected := ""  # id of the selected hotspot ("" none)
var committed := ""  # id of the hotspot committed in this visit's final window ("" none yet)
var committed_early := ""  # id of the hotspot committed in this visit's early window
var spent: Dictionary = {}  # hotspot id -> times it was committed and used up (once, or a success of a non-repeatable object)
var committed_count: Dictionary = {}  # hotspot id -> times committed this run (any outcome)
var last_outcome: Dictionary = {}
var log: Array = []  # every outcome: the tests and the walks read it
var persist_dirty := false  # a persistent flag changed since the owner last saved

var _list: Array = []


func _init(p_data: RunData = null, p_run_flags: Dictionary = {}, p_flags: Dictionary = {}) -> void:
	data = p_data
	run_flags = p_run_flags
	flags = p_flags


## A scene begins (every phase start): fresh selection, the scene's hotspots, the crowd's energy.
func begin_scene(node_id: String, p_energy: float) -> void:
	node = node_id
	energy = p_energy
	selected = ""
	committed = ""
	committed_early = ""
	last_outcome = {}
	_list = data.hotspots_of(node_id) if data != null else []


func list() -> Array:
	return _list


func get_hotspot(id: String) -> Dictionary:
	for h in _list:
		if str(h["id"]) == id:
			return h
	return {}


func has_flag(name: String) -> bool:
	return run_flags.has(name) or flags.has(name)


## True when a hotspot's world-state conditions hold now (flags, energy, not used up). Whether its window is open is `shown()`.
func is_available(h: Dictionary) -> bool:
	var a: Dictionary = h["available"]
	for f in a["flags_all"]:
		if not has_flag(str(f)):
			return false
	for f in a["flags_none"]:
		if has_flag(str(f)):
			return false
	if energy < float(a["energy_min"]):
		return false
	return not spent.has(str(h["id"]))


## "early" for a hotspot that leaves the run for the Bassment, "final" for every other.
static func window_of(h: Dictionary) -> String:
	return "early" if HotspotContract.is_trial_route(str((h.get("on_success", {}) as Dictionary).get("route", ""))) else "final"


## The hotspots on show: `block` is the engine's block counter (0 to 3, the block being played), `final_open` the choice window (beat 48 on). The early window shows in blocks 0 and 1.
func shown(block: int, final_open: bool) -> Array:
	var out: Array = []
	for h in _list:
		if not is_available(h):
			continue
		if window_of(h) == "early":
			if block <= 1 and committed_early == "":
				out.append(h)
		elif final_open and committed == "":
			out.append(h)
	return out


func is_shown(id: String, block: int, final_open: bool) -> bool:
	for h in shown(block, final_open):
		if str(h["id"]) == id:
			return true
	return false


## The player touches a hotspot. Allowed while it is on show and nothing has committed; changing the selection is always allowed until then. False when it cannot be selected.
func select(id: String, block: int, final_open: bool) -> bool:
	if not is_shown(id, block, final_open):
		return false
	selected = id
	return true


## The first hotspot on show whose success route is `to` (scripted play, desktop keys).
func select_route(to: String, block: int, final_open: bool) -> bool:
	for h in shown(block, final_open):
		if str((h["on_success"] as Dictionary).get("route", "")) == to:
			selected = str(h["id"])
			return true
	return false


## The nth hotspot on show (keyboard 1 to 4 on the desktop), in file order.
func select_index(i: int, block: int, final_open: bool) -> bool:
	var s := shown(block, final_open)
	if i < 0 or i >= s.size():
		return false
	selected = str(s[i]["id"])
	return true


func default_hotspot() -> Dictionary:
	for h in _list:
		if bool(h["default"]) and window_of(h) == "final":
			return h
	return {}


func default_route() -> String:
	return str((default_hotspot().get("on_success", {}) as Dictionary).get("route", ""))


## "available" | "selected" | "committed" | "" (not on show) for the view.
func state_of(id: String, block: int, final_open: bool) -> String:
	if id == committed or id == committed_early:
		return "committed"
	if not is_shown(id, block, final_open):
		return ""
	return "selected" if id == selected else "available"


## A block decision (`b` 0 to 2) with its result: the early window commits here. Returns the outcome ({} when nothing committed). At b == 2 an early selection expires (too late to arm the Bassment).
func on_block(b: int, passed: bool) -> Dictionary:
	if selected == "":
		return {}
	var h := get_hotspot(selected)
	if h.is_empty() or window_of(h) != "early":
		return {}
	if b > 1:
		selected = ""
		return {}
	var out := _resolve(h, passed, true, "early")
	committed_early = str(h["id"]) if not _repeatable_now(h, out) else ""
	selected = ""
	return out


## The final commit at the decision of the last block (the route lock beat): the selected hotspot resolves by `passed`; nothing selected is the default exit. Returns the outcome; its
## `route` is always a scene route (an object or a failure without a route continues by the default exit).
func commit_final(passed: bool) -> Dictionary:
	var h := get_hotspot(selected) if selected != "" else {}
	var tapped := not h.is_empty() and window_of(h) == "final" and is_available(h)
	if not tapped:
		h = default_hotspot()
		if h.is_empty():
			return {}
	var out := _resolve(h, passed or not tapped, tapped, "final")
	committed = str(h["id"])
	if out["route"] == "":
		out["route"] = default_route()
		out["continued"] = true
	selected = ""
	return out


func _repeatable_now(h: Dictionary, out: Dictionary) -> bool:
	return bool(h["repeatable"]) and not bool(out["success"])


func _resolve(h: Dictionary, success: bool, tapped: bool, window: String) -> Dictionary:
	var key := "on_success" if success else "on_failure"
	var oc: Dictionary = h.get(key, {})
	var id := str(h["id"])
	var out := {"hotspot": id, "kind": str(h["kind"]), "scene": node, "window": window, "success": success, "tapped": tapped, "defaulted": not tapped, "route": str(oc.get("route", "")),
		"flags_set": (oc.get("flags_set", []) as Array).duplicate(), "cinematic": HotspotContract.resolve_cinematic(h, oc, data.cfg.get("cinematics", {}) if data != null else {}), "cinematic_name": str(oc.get("cinematic", "")) if typeof(oc.get("cinematic", "")) != TYPE_DICTIONARY else "inline",
		"energy": float(oc.get("energy", 0.0)), "music": str(oc.get("music", "")), "look": h["look"], "continued": false}
	for f in out["flags_set"]:
		if HotspotContract.is_keep(str(f)):
			if not flags.has(str(f)):
				flags[str(f)] = true
				persist_dirty = true
		else:
			run_flags[str(f)] = true
	committed_count[id] = int(committed_count.get(id, 0)) + 1
	var av: Dictionary = h["available"]
	if bool(av["once"]) or (success and not bool(h["repeatable"]) and str((h["on_success"] as Dictionary).get("route", "")) == "" and str(h["kind"]) != "exit"):
		spent[id] = int(spent.get(id, 0)) + 1
	last_outcome = out
	log.append(out)
	return out
