class_name RunTrackScenes
extends RefCounted
## Which scenes of a run are TRACK SCENES (docs/RUN_TRACK_SCENES.md): content/run/track_scenes.json assigns a recorded track (a TrackPack, docs/TRACK_PACK_FORMAT.md) to a scene; a scene whose
## track (or one of its alternates) has its pack on this machine plays that track at the track's own tempo for several laps. Everything else is an ordinary scene, exactly as before.
##
## One instance belongs to one RunData (the main run or a path; `paths.main` or `paths.<path id>` of the file): RunData.load_files attaches it as `data.track_scenes` when track scenes are on.
## Track scenes are ON in the game, OFF when RW_RUN_TRACKS=0, and OFF under the test runner (tests/run_tests.gd) unless a test sets `RunTrackScenes.enabled = 1` (or attaches one itself with
## `load_for`). Packs are looked up in RW_TRACKS_DIR, else user://track_packs (`packs_dir_override` for tests): `<dir>/<track id>/track.json`. Only track.json is read here (TrackPack.load_pack
## without decoding: the stems are checked by name and header only); the stems are the audio's business, and each plan carries the loaded pack and its folder for it.
##
## The pick between a scene's track and its alternates is made by the run's seed exactly as a scene's arrangement alternates are (RunData._resolve_arrangement: `"%d:%s" % [seed, scene]`, hashed),
## over the candidates whose pack is present (a missing pack is skipped). RunData.arrangement_override (Debug / Playtest) picks the same way here. Plans are made on first use and cached; `warm()`
## makes them ahead (it may run on a thread).

const PATH := "res://content/run/track_scenes.json"
const FORMAT := "rhythm_warfare.track_scenes.v1"
const MAIN_KEY := "main"
const PACKS_USER_DIR := "user://track_packs"
const ENTRY_KEYS := ["track", "entry", "chart", "start_bar", "laps", "doors_from_lap", "lead_in_bars", "max_laps", "alternates", "note"]
const DEFAULT_KEYS := ["entry", "lead_in_bars", "doors_from_lap", "chart", "max_laps", "note"]

## -1: automatic (on in the game, off under the test runner); 0: off; 1: on. RW_RUN_TRACKS=0 always wins.
static var enabled := -1
## Tests: the folder packs are looked up in ("" = RW_TRACKS_DIR, else user://track_packs) and the assignment file ("" = content/run/track_scenes.json).
static var packs_dir_override := ""
static var json_path_override := ""

var path_key := MAIN_KEY  # "main" or the path's id
var defaults: Dictionary = RunTrackPlan.DEFAULTS.duplicate()
var entries: Dictionary = {}  # scene id -> its entry as written ({track, entry?, ..., alternates?})
var packs_dir := ""  # absolute
var seed_value := 0
var errors: Array = []  # problems in the file (also appended to the RunData's errors)
var warnings: Array = []  # packs refused by the loader, tracks too short for a lap (the scene is then an ordinary one)
var _plans: Dictionary = {}  # scene id -> plan ({} for an ordinary scene)
var _mutex := Mutex.new()


## True when track scenes are on (see `enabled`).
static func active() -> bool:
	if OS.get_environment("RW_RUN_TRACKS") == "0":
		return false
	if enabled >= 0:
		return enabled == 1
	return not _under_test_runner()


static func _under_test_runner() -> bool:
	var loop := Engine.get_main_loop()
	var s: Variant = loop.get_script() if loop != null else null
	return s is Script and (s as Script).resource_path == "res://tests/run_tests.gd"


## The folder the packs are looked up in, absolute.
static func packs_root() -> String:
	var d := packs_dir_override
	if d == "":
		d = OS.get_environment("RW_TRACKS_DIR")
	if d == "":
		d = PACKS_USER_DIR
	return ProjectSettings.globalize_path(d) if d.begins_with("res://") or d.begins_with("user://") else d


## Called at the end of RunData.load_files: attaches the run's track scenes when they are on and the file exists (nothing otherwise: `d.track_scenes` stays null).
static func attach(d: RunData) -> void:
	if not active():
		return
	var path := json_path_override if json_path_override != "" else PATH
	if not FileAccess.file_exists(path):
		return
	load_for(d, path, packs_root())


## Reads `json_path` for the run `d` (its path id picks `paths.<id>`, the main run `paths.main`), checks it, and attaches the result as `d.track_scenes`; problems in the file are appended to
## `d.errors` as sentences naming the file, the path and the scene.
static func load_for(d: RunData, json_path: String, p_packs_dir: String) -> RunTrackScenes:
	var ts := RunTrackScenes.new()
	ts.path_key = d.path_id if d.path_id != "" else MAIN_KEY
	ts.packs_dir = ProjectSettings.globalize_path(p_packs_dir) if p_packs_dir.begins_with("res://") or p_packs_dir.begins_with("user://") else p_packs_dir
	ts.seed_value = d.seed_value
	var where := json_path.get_file()
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(json_path)) if FileAccess.file_exists(json_path) else null
	if typeof(v) != TYPE_DICTIONARY:
		ts.errors.append("%s is missing or is not one JSON object" % where)
	else:
		ts._read(v, where, d)
	d.track_scenes = ts
	d.errors.append_array(ts.errors)
	return ts


func _read(v: Dictionary, where: String, d: RunData) -> void:
	if str(v.get("format", "")) != FORMAT:
		errors.append("%s: format is '%s' but must be '%s'" % [where, v.get("format", ""), FORMAT])
	var dv: Variant = v.get("defaults", {})
	if typeof(dv) != TYPE_DICTIONARY:
		errors.append("%s: defaults must be an object" % where)
	else:
		for k in (dv as Dictionary):
			if not str(k) in DEFAULT_KEYS:
				errors.append("%s: defaults.%s is not a field (%s)" % [where, k, ", ".join(PackedStringArray(DEFAULT_KEYS))])
		_check_fields(dv, "%s defaults" % where, true)
		for k in (dv as Dictionary):
			if str(k) != "note":
				defaults[str(k)] = dv[k]
	var pv: Variant = v.get("paths", {})
	if typeof(pv) != TYPE_DICTIONARY:
		errors.append("%s: paths must be an object keyed by path id (\"main\" for the main run)" % where)
		return
	var known := RunData.path_ids()
	for pk in (pv as Dictionary):
		if str(pk) != MAIN_KEY and not known.has(str(pk)):
			errors.append("%s: paths.%s is neither \"main\" nor a path under content/paths" % [where, pk])
		if typeof(pv[pk]) != TYPE_DICTIONARY:
			errors.append("%s: paths.%s must be an object keyed by scene id" % [where, pk])
	var mine: Variant = (pv as Dictionary).get(path_key, {})
	if typeof(mine) != TYPE_DICTIONARY:
		return
	for sid in (mine as Dictionary):
		var w := "%s: paths.%s scene %s" % [where, path_key, sid]
		if not d.nodes.has(str(sid)):
			errors.append("%s: there is no such scene in this run" % w)
			continue
		var ent: Variant = mine[sid]
		if typeof(ent) != TYPE_DICTIONARY:
			errors.append("%s: the entry must be an object {track, ...}" % w)
			continue
		if _check_entry(ent, w, true):
			entries[str(sid)] = ent


## Checks one scene entry (or an alternate, `top` false). True when it can be used.
func _check_entry(ent: Dictionary, w: String, top: bool) -> bool:
	var ok := true
	for k in ent:
		if not str(k) in ENTRY_KEYS or (not top and str(k) == "alternates"):
			errors.append("%s: '%s' is not a field of %s (%s)" % [w, k, "a scene entry" if top else "an alternate", ", ".join(PackedStringArray(ENTRY_KEYS.filter(func(x: String) -> bool: return top or x != "alternates")))])
			ok = false
	var track := str(ent.get("track", ""))
	if not TrackPack._is_key(track):
		errors.append("%s: track '%s' must be a track id (lower case letters, digits and underscores)" % [w, track])
		ok = false
	if not _check_fields(ent, w, false):
		ok = false
	if ent.has("laps"):
		var cap := int(ent.get("max_laps", defaults.get("max_laps", 12)))
		if int(ent["laps"]) > cap:
			errors.append("%s: laps %d is more than max_laps %d" % [w, int(ent["laps"]), cap])
			ok = false
	if top and ent.has("alternates"):
		if typeof(ent["alternates"]) != TYPE_ARRAY:
			errors.append("%s: alternates must be a list of entries" % w)
			ok = false
		else:
			for i in (ent["alternates"] as Array).size():
				var a: Variant = ent["alternates"][i]
				if typeof(a) != TYPE_DICTIONARY:
					errors.append("%s alternate %d: must be an object {track, ...}" % [w, i + 1])
					ok = false
				elif not _check_entry(a, "%s alternate %d" % [w, i + 1], false):
					ok = false
	return ok


## The value rules shared by defaults and entries. True when every field present is right.
func _check_fields(ent: Dictionary, w: String, is_defaults: bool) -> bool:
	var ok := true
	if ent.has("entry") and not str(ent["entry"]) in RunTrackPlan.ENTRIES:
		errors.append("%s: entry '%s' is not one of %s" % [w, ent["entry"], ", ".join(PackedStringArray(RunTrackPlan.ENTRIES))])
		ok = false
	for k in ["start_bar", "lead_in_bars"]:
		if ent.has(k) and not _whole(ent[k], 0):
			errors.append("%s: %s must be a whole number of 0 or more" % [w, k])
			ok = false
	for k in ["laps", "doors_from_lap", "max_laps"]:
		if ent.has(k) and not _whole(ent[k], 1):
			errors.append("%s: %s must be a whole number of 1 or more" % [w, k])
			ok = false
	if ent.has("chart") and (typeof(ent["chart"]) != TYPE_STRING or str(ent["chart"]) == ""):
		errors.append("%s: chart must be a chart name" % w)
		ok = false
	if is_defaults and ent.has("start_bar"):
		errors.append("%s: start_bar belongs to a scene, not to the defaults" % w)
		ok = false
	return ok


static func _whole(v: Variant, lo: int) -> bool:
	return typeof(v) in [TYPE_INT, TYPE_FLOAT] and float(v) == floorf(float(v)) and int(v) >= lo


## True when the file assigns a track to scene `id` (whether or not its pack is here).
func has_entry(id: String) -> bool:
	return entries.has(id)


## The folder of track `track_id`'s pack (it may not exist).
func pack_dir(track_id: String) -> String:
	return packs_dir.path_join(track_id)


func pack_present(track_id: String) -> bool:
	return FileAccess.file_exists(pack_dir(track_id).path_join("track.json"))


## The candidates of scene `id` whose pack is present, in file order (the track, then its alternates): [entry over the defaults], each with `index` (0 the track, k the k-th alternate).
func candidates(id: String) -> Array:
	var out: Array = []
	if not entries.has(id):
		return out
	var ent: Dictionary = entries[id]
	var all: Array = [ent]
	all.append_array(ent.get("alternates", []))
	for i in all.size():
		var e: Dictionary = defaults.duplicate()
		for k in (all[i] as Dictionary):
			if str(k) != "alternates" and str(k) != "note":
				e[str(k)] = all[i][k]
		e["index"] = i
		if pack_present(str(e["track"])):
			out.append(e)
	return out


## The plan of scene `id` ({} when it is not a track scene here: no entry, no pack present, or every present pack refused). Cached; the same seed gives the same plan.
## The plan is RunTrackPlan.compute's, plus: node, pick (the chosen candidate's index in `candidates`), index (0 the track, k the k-th alternate), pack (the TrackPack, stems not decoded).
func plan_of(id: String) -> Dictionary:
	_mutex.lock()
	var have := _plans.has(id)
	var p: Dictionary = _plans.get(id, {})
	_mutex.unlock()
	if have:
		return p
	p = _make_plan(id)
	_mutex.lock()
	_plans[id] = p
	_mutex.unlock()
	return p


## Makes the plans of `ids` now (all assigned scenes when empty): call it ahead of time, on a thread if need be.
func warm(ids: Array = []) -> void:
	for id in (ids if not ids.is_empty() else entries.keys()):
		plan_of(str(id))


func is_track_scene(id: String) -> bool:
	return not plan_of(id).is_empty()


func _make_plan(id: String) -> Dictionary:
	var cands := candidates(id)
	if cands.is_empty():
		return {}
	var pick := 0 if cands.size() == 1 else absi(("%d:%s" % [seed_value, id]).hash()) % cands.size()
	if RunData.arrangement_override >= 0:
		pick = mini(RunData.arrangement_override, cands.size() - 1)
	for k in cands.size():  # the pick first; a pack the loader refuses passes the turn to the next candidate
		var c: Dictionary = cands[(pick + k) % cands.size()]
		var dir := pack_dir(str(c["track"]))
		var res := TrackPack.load_pack(dir, false)
		if res["pack"] == null:
			_warn("scene %s: the pack of track %s is refused: %s" % [id, c["track"], "; ".join(PackedStringArray(res["errors"]))])
			continue
		var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join("track.json")))
		var plan := RunTrackPlan.compute(RunTrackPlan.info_of(res["pack"], raw if typeof(raw) == TYPE_DICTIONARY else {}), c)
		if plan.has("error"):
			_warn("scene %s: %s" % [id, plan["error"]])
			continue
		plan["node"] = id
		plan["pick"] = (pick + k) % cands.size()
		plan["index"] = int(c["index"])
		plan["pack"] = res["pack"]
		add_transition_meta(plan, raw if typeof(raw) == TYPE_DICTIONARY else {})
		return plan
	return {}


## What the transition planner reads of a track scene (stage M2.4, docs/parallel-development/MUSIC_TRANSITIONS.md sections 3.5 and 4.1), made with the plan (off the frame, `warm`) so that
## the director's lock reads no file: sidecar (content/music/transitions/<track>.json, {} when missing or invalid), sidecar_state, drift_ms_max (the pack's source.tempo_detail.drift_ms_max_abs,
## 0 when absent), grid_ok (TransitionSidecars.grid_ok), drop_bar (the drop the plan's entry rule reads, the sidecar's first if it has one: TransitionSidecars.drop_bar_of; -1 for none).
static func add_transition_meta(plan: Dictionary, raw: Dictionary) -> void:
	var sc := TransitionSidecars.load_track(str(plan.get("track", "")))
	var side: Dictionary = sc["sidecar"]
	var src: Variant = raw.get("source", {})
	var td: Variant = (src as Dictionary).get("tempo_detail", {}) if typeof(src) == TYPE_DICTIONARY else {}
	var drift := float((td as Dictionary).get("drift_ms_max_abs", 0.0)) if typeof(td) == TYPE_DICTIONARY else 0.0
	plan["sidecar"] = side
	plan["sidecar_state"] = str(sc["state"])
	plan["drift_ms_max"] = drift
	plan["grid_ok"] = TransitionSidecars.grid_ok(side, drift, float(plan.get("bpm", 0.0)))
	var pack: Variant = plan.get("pack", null)
	var info := {"bpm": float(plan.get("bpm", 0.0)), "first_downbeat_s": float(plan.get("first_downbeat_s", 0.0)), "sections": (pack as TrackPack).sections if pack is TrackPack else []}
	plan["drop_bar"] = TransitionSidecars.drop_bar_of(info, "drop2" if str(plan.get("entry", "")) == "drop2" else "drop1", side)


func _warn(s: String) -> void:
	_mutex.lock()
	warnings.append(s)
	_mutex.unlock()
