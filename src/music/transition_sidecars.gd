class_name TransitionSidecars
extends RefCounted
## Read-only loader of the transition sidecars `content/music/transitions/<track id>.json` (docs/parallel-development/MUSIC_TRANSITIONS.md section 3.2; the tool that writes them is
## tools/music/transition_sidecars.py, which keeps this file's validation in step with its own). Small and static: no nodes, no caching, no writes.
##
## load_track(id) -> {state: "ok" | "missing" | "invalid", sidecar: Dictionary (empty unless ok), errors: Array[String]}. A missing file means "use the pack as it is" and an invalid sidecar
## is ignored as a whole (section 3.2, 3.5): both give an empty sidecar, so the planner reads the pack's values and no `no_blend`. The state travels so a caller can log it.
##
## Keys: section 3.2's, plus first_drop_bar, first_drop_snap_ms and origin (what the tool adds: the snapped bar, the snap error in ms, and per field "detected" or "owner").

const DIR := "res://content/music/transitions"
const FORMAT := "rhythm_warfare.transition.v1"
const KEYS := ["format", "track", "first_drop_s", "second_drop_s", "downbeat_offset_beats", "intro_start_s", "outro_start_s", "mix_in_bar", "mix_out_bar", "no_blend", "linger", "checked", "note",
	"first_drop_bar", "first_drop_snap_ms", "origin"]
const ORIGIN_FIELDS := ["first_drop_s", "second_drop_s", "outro_start_s"]
const GRID_DRIFT_MS := 20.0  # section 3.5: grid_ok needs drift_ms_max <= 20
const AGREE_BEATS := 0.25  # section 3.3


static func path_of(id: String, dir: String = DIR) -> String:
	return "%s/%s.json" % [dir, id]


## Loads and validates one sidecar. `facts` (optional: {bpm, duration_s, voices}) adds the checks that need the pack.
static func load_track(id: String, dir: String = DIR, facts: Dictionary = {}) -> Dictionary:
	var path := path_of(id, dir)
	if not FileAccess.file_exists(path):
		return {"state": "missing", "sidecar": {}, "errors": []}
	var text := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {"state": "invalid", "sidecar": {}, "errors": ["%s.json: not a JSON object" % id]}
	var errs := validate(parsed, id, facts)
	if not errs.is_empty():
		for e in errs:
			push_warning("transition sidecar ignored: %s" % e)
		return {"state": "invalid", "sidecar": {}, "errors": errs}
	return {"state": "ok", "sidecar": parsed, "errors": []}


## Section 3.2's validation as sentences naming the file and the field; empty when valid.
static func validate(d: Variant, id: String, facts: Dictionary = {}) -> Array[String]:
	var name := "%s.json" % id
	var errs: Array[String] = []
	if typeof(d) != TYPE_DICTIONARY:
		errs.append("%s: the sidecar is not an object" % name)
		return errs
	var sc: Dictionary = d
	for k in sc:
		if not KEYS.has(str(k)):
			errs.append("%s: unknown key '%s'" % [name, k])
	if str(sc.get("format", "")) != FORMAT:
		errs.append("%s: format must be exactly %s" % [name, FORMAT])
	if str(sc.get("track", "")) != id:
		errs.append("%s: track must be '%s' (the file name)" % [name, id])
	var bar_s := 240.0 / float(facts["bpm"]) if facts.has("bpm") and float(facts["bpm"]) > 0.0 else 0.0
	var first: Variant = _num(sc, "first_drop_s", 0.0, errs, name)
	var second: Variant = _num(sc, "second_drop_s", 0.0, errs, name)
	if bar_s > 0.0 and float(facts.get("duration_s", 0.0)) > 0.0:
		for key in ["first_drop_s", "second_drop_s"]:
			var v: Variant = first if key == "first_drop_s" else second
			if v != null and float(v) > float(facts["duration_s"]) - 16.0 * bar_s + 1e-6:
				errs.append("%s: %s %.3f is inside the last 16 bars (duration %.3f)" % [name, key, float(v), float(facts["duration_s"])])
	if first != null and second != null and bar_s > 0.0 and float(second) <= float(first) + 16.0 * bar_s - 1e-6:
		errs.append("%s: second_drop_s must be more than 16 bars after first_drop_s" % name)
	var off: Variant = sc.get("downbeat_offset_beats", null)
	if not (typeof(off) in [TYPE_INT, TYPE_FLOAT] and float(off) == floorf(float(off)) and absf(float(off)) <= 3.0):
		errs.append("%s: downbeat_offset_beats must be an integer from -3 to 3" % name)
	var intro: Variant = _num(sc, "intro_start_s", 0.0, errs, name)
	_num(sc, "outro_start_s", 0.0, errs, name)
	if intro != null and first != null and float(intro) >= float(first):
		errs.append("%s: intro_start_s must be before first_drop_s" % name)
	for key in ["mix_in_bar", "mix_out_bar", "first_drop_bar"]:
		var v: Variant = sc.get(key, null)
		if v != null and not _is_whole(v, 0):
			errs.append("%s: %s must be a whole bar number or null" % [name, key])
	var mix_in: Variant = sc.get("mix_in_bar", null)
	var fb: Variant = sc.get("first_drop_bar", null)
	if mix_in != null and fb != null and _is_whole(mix_in, 0) and _is_whole(fb, 0) and not (int(fb) - 16 <= int(mix_in) and int(mix_in) <= int(fb) - 6):
		errs.append("%s: mix_in_bar must lie between first drop bar - 16 and first drop bar - 6" % name)
	if typeof(sc.get("no_blend", null)) != TYPE_BOOL:
		errs.append("%s: no_blend must be true or false" % name)
	var lg: Variant = sc.get("linger", null)
	if lg != null:
		if typeof(lg) != TYPE_ARRAY or (lg as Array).any(func(x: Variant) -> bool: return typeof(x) != TYPE_STRING):
			errs.append("%s: linger must be a list of voice keys or null" % name)
		elif facts.has("voices"):
			for x in lg:
				if not (facts["voices"] as Array).has(x) and str(x) != "backing":
					errs.append("%s: linger key '%s' is not a voice of the pack" % [name, x])
	var ch: Variant = sc.get("checked", null)
	if ch != null and not (typeof(ch) == TYPE_STRING and _is_date(str(ch))):
		errs.append("%s: checked must be a date string YYYY-MM-DD or null" % name)
	if typeof(sc.get("note", null)) != TYPE_STRING:
		errs.append("%s: note must be a string" % name)
	var sn: Variant = sc.get("first_drop_snap_ms", null)
	if sn != null and typeof(sn) not in [TYPE_INT, TYPE_FLOAT]:
		errs.append("%s: first_drop_snap_ms must be a number or null" % name)
	var org: Variant = sc.get("origin", null)
	if org != null and typeof(org) != TYPE_DICTIONARY:
		errs.append("%s: origin must be an object" % name)
	elif org != null:
		for k in org:
			if not ORIGIN_FIELDS.has(str(k)):
				errs.append("%s: origin has an unknown field '%s'" % [name, k])
			if not ["detected", "owner"].has(str(org[k])):
				errs.append("%s: origin.%s must be 'detected' or 'owner'" % [name, k])
	return errs


## Section 3.5: true when the track's tempo is steady (drift_ms_max <= 20) and the sidecar's snap verdict is not "grid suspect". `bpm` is the pack's.
static func grid_ok(sidecar: Dictionary, drift_ms_max: float, bpm: float) -> bool:
	if drift_ms_max > GRID_DRIFT_MS:
		return false
	return snap_verdict(sidecar, bpm) != &"grid_suspect"


## Section 3.3's verdict of the recorded snap error: &"agrees", &"phase_suspect" (a whole number of beats out) or &"grid_suspect"; &"agrees" when none was recorded.
static func snap_verdict(sidecar: Dictionary, bpm: float) -> StringName:
	var ms: Variant = sidecar.get("first_drop_snap_ms", null)
	if ms == null or bpm <= 0.0:
		return &"agrees"
	var eb := float(ms) / 1000.0 / (60.0 / bpm)
	if absf(eb) <= AGREE_BEATS:
		return &"agrees"
	if absf(eb - roundf(eb)) <= AGREE_BEATS:
		return &"phase_suspect"
	return &"grid_suspect"


## The bar (from the pack's first downbeat, 4 beats a bar) of the drop a scene's entry rule reads: "drop2" the second drop (the first when there is only one), anything else the first;
## the sidecar's drop (owner's or detected, already snapped) wins over the pack's section when present. -1 when the track has no drop at all. `info` is RunTrackPlan.info_of's dictionary
## ({bpm, first_downbeat_s, sections}). The planner's `inc.drop_bar` is this and `inc.entry_bar` is RunTrackPlan's entry_bar.
static func drop_bar_of(info: Dictionary, rule: String, sidecar: Dictionary = {}) -> int:
	var bpm := float(info.get("bpm", 0.0))
	if bpm <= 0.0:
		return -1
	var bar := 240.0 / bpm
	var fd := float(info.get("first_downbeat_s", 0.0)) + float(sidecar.get("downbeat_offset_beats", 0)) * 60.0 / bpm
	var drops: Array = (info.get("sections", []) as Array).filter(func(s: Dictionary) -> bool: return str(s.get("role", "")) == "drop")
	var t := -1.0
	if rule == "drop2" and drops.size() > 1:
		t = float(drops[1]["start_s"])
		if sidecar.get("second_drop_s", null) != null:
			t = float(sidecar["second_drop_s"])
	elif not drops.is_empty():
		t = float(drops[0]["start_s"])
		if sidecar.get("first_drop_s", null) != null:
			t = float(sidecar["first_drop_s"])
	elif sidecar.get("first_drop_s", null) != null:
		t = float(sidecar["first_drop_s"])
	if t < 0.0:
		return -1
	return maxi(int(roundf((t - fd) / bar)), 0)


static func _num(sc: Dictionary, key: String, lo: float, errs: Array[String], name: String) -> Variant:
	var v: Variant = sc.get(key, null)
	if v == null:
		return null
	if typeof(v) not in [TYPE_INT, TYPE_FLOAT] or is_nan(float(v)) or is_inf(float(v)):
		errs.append("%s: %s must be a number or null" % [name, key])
		return null
	if float(v) < lo:
		errs.append("%s: %s must be at least %s" % [name, key, lo])
	return float(v)


static func _is_whole(v: Variant, lo: int) -> bool:
	return typeof(v) in [TYPE_INT, TYPE_FLOAT] and float(v) == floorf(float(v)) and int(v) >= lo


static func _is_date(s: String) -> bool:
	var re := RegEx.new()
	re.compile("^\\d{4}-\\d{2}-\\d{2}$")
	return re.search(s) != null
