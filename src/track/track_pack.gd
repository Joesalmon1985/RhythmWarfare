class_name TrackPack
extends RefCounted
## A `rhythm_warfare.track.v1` pack (docs/TRACK_PACK_FORMAT.md): one recording as four playable voices (one per pad)
## plus backing, with charts in seconds. `TrackPack.load_pack(folder)` reads track.json, checks every rule of the
## contract that needs no audio analysis, decodes the stems, and either returns the pack or the list of problems
## (clear sentences naming the field or the cue). A pack that breaks a rule is refused, never played.

const FORMAT := "rhythm_warfare.track.v1"
const ROLES := ["intro", "build", "drop", "breakdown", "outro", "other"]
const STEM_RATE := 48000
const STEM_CHANNELS := 2
const LENGTH_TOLERANCE_S := 0.005  # stems agree with each other and with duration_s to within 5 ms
const MIN_CUE_T := 1.0
const END_MARGIN_S := 0.5
const DEFAULT_RESTORE_BEATS := 8.0
const EPS := 1e-6  # float slack on the gap rules (a gap of exactly half a beat is allowed)
const THUMB_OF_PAD := {1: 0, 2: 0, 3: 1, 4: 1}
const OTHER_PAD_OF_THUMB := {1: 2, 2: 1, 3: 4, 4: 3}

var dir := ""
var id := ""
var title := ""
var artist := ""
var duration_s := 0.0
var bpm := 120.0
var first_downbeat_s := 0.0
var voices: Array = []  # [{key, label, pad, stem, gain}] in pad order 1 to 4
var backing: Array = []  # [{key, stem, gain}]
var sections: Array = []  # [{id, role, start_s, end_s}]
var charts: Dictionary = {}  # name -> Array of {t, pad, dur, conf}
var default_chart := ""
var restore_after_idle_beats := DEFAULT_RESTORE_BEATS
var streams: Dictionary = {}  # stem key -> decoded AudioStream (only when loaded with decode on)
var stem_lengths: Dictionary = {}  # stem key -> seconds


## One beat in seconds (60 / tempo.bpm).
func beat_s() -> float:
	return 60.0 / bpm


## The voice of a pad (1 to 4), or {} when there is none.
func voice_of_pad(pad: int) -> Dictionary:
	for v in voices:
		if int(v["pad"]) == pad:
			return v
	return {}


## Voices then backing: [{key, stem, gain, voice: bool}], the order the transport plays them in.
func stems_in_order() -> Array:
	var out: Array = []
	for v in voices:
		out.append({"key": v["key"], "stem": v["stem"], "gain": v["gain"], "voice": true})
	for b in backing:
		out.append({"key": b["key"], "stem": b["stem"], "gain": b["gain"], "voice": false})
	return out


## The section containing second `t` ("" when none).
func section_at(t: float) -> String:
	for s in sections:
		if t >= float(s["start_s"]) and t < float(s["end_s"]):
			return str(s["id"])
	return ""


## Loads and checks the pack in `folder` (an absolute path). Returns {"pack": TrackPack or null, "errors": Array[String]}.
## With `decode` false the stems are only checked by name and header (a quick look at a pack's data).
static func load_pack(folder: String, decode: bool = true) -> Dictionary:
	var errors: Array[String] = []
	var root := folder.simplify_path()
	if root.length() > 1 and root.ends_with("/"):
		root = root.trim_suffix("/")
	var json_path := root.path_join("track.json")
	if not DirAccess.dir_exists_absolute(root):
		return _refused(["The pack folder %s does not exist." % root])
	if not FileAccess.file_exists(json_path):
		return _refused(["The pack folder %s has no track.json." % root])
	var json := JSON.new()
	var parse_err := json.parse(FileAccess.get_file_as_string(json_path))
	if parse_err != OK:
		return _refused(["track.json is not valid JSON: %s (line %d)." % [json.get_error_message(), json.get_error_line()]])
	if typeof(json.data) != TYPE_DICTIONARY:
		return _refused(["track.json must hold one JSON object."])
	var d: Dictionary = json.data
	var p := TrackPack.new()
	p.dir = root

	# header
	if str(d.get("format", "")) != FORMAT:
		errors.append("format is '%s' but must be exactly '%s'." % [str(d.get("format", "")), FORMAT])
	p.id = str(d.get("id", ""))
	if not _is_key(p.id):
		errors.append("id '%s' must be lower case letters, digits and underscores." % p.id)
	elif p.id != root.get_file():
		errors.append("id '%s' must equal the folder name '%s'." % [p.id, root.get_file()])
	p.title = str(d.get("title", p.id))
	p.artist = str(d.get("artist", ""))
	if not _is_number(d.get("duration_s")) or float(d["duration_s"]) <= 0.0:
		errors.append("duration_s must be a number above 0.")
	else:
		p.duration_s = float(d["duration_s"])

	# tempo
	var tempo: Variant = d.get("tempo")
	if typeof(tempo) != TYPE_DICTIONARY:
		errors.append("tempo is missing: it must hold bpm, first_downbeat_s, beats_per_bar and confidence.")
	else:
		var t: Dictionary = tempo
		if not _is_number(t.get("bpm")) or float(t["bpm"]) <= 0.0:
			errors.append("tempo.bpm must be a number above 0.")
		else:
			p.bpm = float(t["bpm"])
		if not _is_number(t.get("first_downbeat_s")) or float(t["first_downbeat_s"]) < 0.0:
			errors.append("tempo.first_downbeat_s must be a number of 0 or more.")
		else:
			p.first_downbeat_s = float(t["first_downbeat_s"])
		if not _is_number(t.get("beats_per_bar")) or int(t["beats_per_bar"]) != 4:
			errors.append("tempo.beats_per_bar must be 4.")
		if not _is_number(t.get("confidence")) or float(t["confidence"]) < 0.0 or float(t["confidence"]) > 1.0:
			errors.append("tempo.confidence must be a number from 0 to 1.")

	# voices and backing
	var keys: Dictionary = {}
	var pads_seen: Dictionary = {}
	var voices_raw: Variant = d.get("voices")
	if typeof(voices_raw) != TYPE_ARRAY or (voices_raw as Array).size() != 4:
		errors.append("voices must hold exactly four entries (one per pad), found %s." % (str((voices_raw as Array).size()) if typeof(voices_raw) == TYPE_ARRAY else "none"))
	if typeof(voices_raw) == TYPE_ARRAY:
		for i in (voices_raw as Array).size():
			var v: Variant = (voices_raw as Array)[i]
			if typeof(v) != TYPE_DICTIONARY:
				errors.append("voices[%d] must be an object." % i)
				continue
			var vd: Dictionary = v
			var key := str(vd.get("key", ""))
			var name := "voice '%s'" % key if not key.is_empty() else "voices[%d]" % i
			_check_key(key, name, keys, errors)
			var label := str(vd.get("label", ""))
			if label.strip_edges().is_empty():
				errors.append("%s has no label." % name)
			var pad := -1
			if _is_number(vd.get("pad")) and float(vd["pad"]) == floorf(float(vd["pad"])):
				pad = int(vd["pad"])
			if pad < 1 or pad > 4:
				errors.append("%s has pad %s but a voice's pad must be 1, 2, 3 or 4." % [name, str(vd.get("pad", "(none)"))])
			elif pads_seen.has(pad):
				errors.append("%s uses pad %d, which voice '%s' already has: the four voices need pads 1, 2, 3 and 4 once each." % [name, pad, pads_seen[pad]])
			else:
				pads_seen[pad] = key
			var gain := _gain_of(vd, name, errors)
			var stem := str(vd.get("stem", ""))
			_check_stem_path(stem, name, errors)
			p.voices.append({"key": key, "label": label, "pad": pad, "stem": stem, "gain": gain})
		p.voices.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["pad"]) < int(b["pad"]))
	var backing_raw: Variant = d.get("backing", [])
	if typeof(backing_raw) != TYPE_ARRAY:
		errors.append("backing must be a list (it may be empty).")
	else:
		for i in (backing_raw as Array).size():
			var b: Variant = (backing_raw as Array)[i]
			if typeof(b) != TYPE_DICTIONARY:
				errors.append("backing[%d] must be an object." % i)
				continue
			var bd: Dictionary = b
			var key := str(bd.get("key", ""))
			var name := "backing stem '%s'" % key if not key.is_empty() else "backing[%d]" % i
			_check_key(key, name, keys, errors)
			var stem := str(bd.get("stem", ""))
			_check_stem_path(stem, name, errors)
			p.backing.append({"key": key, "stem": stem, "gain": _gain_of(bd, name, errors)})

	# stems on disk
	if errors.is_empty():
		_check_stems(p, decode, errors)

	# sections
	var sections_raw: Variant = d.get("sections", [])
	if typeof(sections_raw) != TYPE_ARRAY:
		errors.append("sections must be a list (it may be empty).")
	else:
		var prev_end := 0.0
		var prev_id := ""
		for i in (sections_raw as Array).size():
			var s: Variant = (sections_raw as Array)[i]
			if typeof(s) != TYPE_DICTIONARY:
				errors.append("sections[%d] must be an object." % i)
				continue
			var sd: Dictionary = s
			var sid := str(sd.get("id", ""))
			var name := "section '%s'" % sid if not sid.is_empty() else "sections[%d]" % i
			if not str(sd.get("role", "")) in ROLES:
				errors.append("%s has role '%s' but a role is one of %s." % [name, str(sd.get("role", "")), ", ".join(PackedStringArray(ROLES))])
			if not _is_number(sd.get("start_s")) or not _is_number(sd.get("end_s")):
				errors.append("%s needs numeric start_s and end_s." % name)
				continue
			var a := float(sd["start_s"])
			var b := float(sd["end_s"])
			if a < 0.0 or b <= a:
				errors.append("%s runs from %.3f to %.3f s: it must start at 0 or later and end after it starts." % [name, a, b])
			elif p.duration_s > 0.0 and b > p.duration_s + EPS:
				errors.append("%s ends at %.3f s, after the track ends at %.3f s." % [name, b, p.duration_s])
			if a < prev_end - EPS and i > 0:
				errors.append("%s starts at %.3f s, before the previous section '%s' ends at %.3f s: sections must be in time order and not overlap." % [name, a, prev_id, prev_end])
			prev_end = maxf(prev_end, b)
			prev_id = sid
			p.sections.append({"id": sid, "role": str(sd.get("role", "other")), "start_s": a, "end_s": b})

	# rules
	var rules: Variant = d.get("rules", {})
	if typeof(rules) != TYPE_DICTIONARY:
		errors.append("rules must be an object.")
	elif (rules as Dictionary).has("restore_after_idle_beats"):
		var r: Variant = (rules as Dictionary)["restore_after_idle_beats"]
		if not _is_number(r) or float(r) <= 0.0:
			errors.append("rules.restore_after_idle_beats must be a number above 0.")
		else:
			p.restore_after_idle_beats = float(r)

	# charts
	var charts_raw: Variant = d.get("charts")
	p.default_chart = str(d.get("default_chart", ""))
	if typeof(charts_raw) != TYPE_DICTIONARY or (charts_raw as Dictionary).is_empty():
		errors.append("charts must hold at least the chart named by default_chart.")
	else:
		var cd: Dictionary = charts_raw
		if not cd.has(p.default_chart):
			errors.append("default_chart '%s' is not one of the charts (%s)." % [p.default_chart, ", ".join(PackedStringArray(cd.keys()))])
		for chart_name in cd:
			var parsed := _parse_chart(str(chart_name), cd[chart_name], p, errors)
			p.charts[str(chart_name)] = parsed
	if not errors.is_empty():
		return _refused(errors)
	return {"pack": p, "errors": errors}


static func _refused(errors: Array) -> Dictionary:
	return {"pack": null, "errors": errors}


static func _is_number(v: Variant) -> bool:
	return typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT


static func _is_key(s: String) -> bool:
	if s.is_empty():
		return false
	for i in s.length():
		var c := s.unicode_at(i)
		if not ((c >= 97 and c <= 122) or (c >= 48 and c <= 57) or c == 95):
			return false
	return true


static func _check_key(key: String, name: String, keys: Dictionary, errors: Array[String]) -> void:
	if not _is_key(key):
		errors.append("%s has key '%s' but a key is lower case letters, digits and underscores." % [name, key])
	elif keys.has(key):
		errors.append("%s repeats the key '%s': keys must be unique across voices and backing." % [name, key])
	keys[key] = true


static func _gain_of(d: Dictionary, name: String, errors: Array[String]) -> float:
	if not d.has("gain"):
		return 1.0
	if not _is_number(d["gain"]) or float(d["gain"]) < 0.0 or float(d["gain"]) > 2.0:
		errors.append("%s has gain %s but gain is a number from 0 to 2." % [name, str(d["gain"])])
		return 1.0
	return float(d["gain"])


static func _check_stem_path(stem: String, name: String, errors: Array[String]) -> void:
	var bad := stem.is_empty() or stem.begins_with("/") or stem.contains("\\") or stem.contains(":") or ".." in stem.split("/")
	if bad:
		errors.append("%s has stem path '%s' but a stem must be a relative path inside the pack (no '..', no leading '/')." % [name, stem])
	elif stem.get_extension().to_lower() != "ogg":
		errors.append("%s has stem '%s' but stems are Ogg Vorbis files (.ogg)." % [name, stem])


## Reads the Ogg Vorbis identification header: {channels, rate}, or {} when the bytes are not Ogg Vorbis.
static func ogg_vorbis_info(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var head := f.get_buffer(128)
	f.close()
	if head.size() < 40 or head.slice(0, 4).get_string_from_ascii() != "OggS":
		return {}
	var marker := PackedByteArray([1, 118, 111, 114, 98, 105, 115])  # 0x01 "vorbis"
	for i in range(0, head.size() - 20):
		if head.slice(i, i + 7) == marker:
			return {"channels": int(head[i + 11]), "rate": int(head.decode_u32(i + 12))}
	return {}


static func _check_stems(p: TrackPack, decode: bool, errors: Array[String]) -> void:
	var first_key := ""
	for s in p.stems_in_order():
		var key: String = s["key"]
		var rel: String = s["stem"]
		var full := p.dir.path_join(rel)
		var name := "stem '%s' (%s)" % [key, rel]
		if not FileAccess.file_exists(full):
			errors.append("%s does not exist in the pack." % name)
			continue
		var info := ogg_vorbis_info(full)
		if info.is_empty():
			errors.append("%s is not an Ogg Vorbis file." % name)
			continue
		if int(info["rate"]) != STEM_RATE or int(info["channels"]) != STEM_CHANNELS:
			errors.append("%s is %d Hz with %d channel(s) but stems are 48000 Hz stereo." % [name, int(info["rate"]), int(info["channels"])])
			continue
		if not decode:
			continue
		var stream := LevelLoader.load_stream(full)
		if stream == null or stream.get_length() <= 0.0:
			errors.append("%s cannot be decoded." % name)
			continue
		p.streams[key] = stream
		p.stem_lengths[key] = stream.get_length()
		if first_key.is_empty():
			first_key = key
	if first_key.is_empty():
		return
	for key in p.stem_lengths:
		if absf(float(p.stem_lengths[key]) - float(p.stem_lengths[first_key])) > LENGTH_TOLERANCE_S:
			errors.append("stem '%s' is %.3f s long but stem '%s' is %.3f s: all stems must be the same length to within 5 ms." % [
				key, p.stem_lengths[key], first_key, p.stem_lengths[first_key]])
	if p.duration_s > 0.0:
		for key in p.stem_lengths:
			if absf(float(p.stem_lengths[key]) - p.duration_s) > LENGTH_TOLERANCE_S:
				errors.append("duration_s is %.3f s but stem '%s' is %.3f s long: they must match to within 5 ms." % [p.duration_s, key, p.stem_lengths[key]])


## Parses one chart and checks its ordering, bounds and playability. Returns the cues as {t, pad, dur, conf}; problems
## go to `errors`, each naming the chart, the cue's number, time and pad.
static func _parse_chart(chart_name: String, raw: Variant, p: TrackPack, errors: Array[String]) -> Array:
	var cues: Array = []
	if typeof(raw) != TYPE_ARRAY:
		errors.append("chart '%s' must be a list of cues." % chart_name)
		return cues
	for i in (raw as Array).size():
		var c: Variant = (raw as Array)[i]
		if typeof(c) != TYPE_DICTIONARY:
			errors.append("chart '%s' cue #%d must be an object {t, pad, dur, conf}." % [chart_name, i + 1])
			continue
		var cd: Dictionary = c
		if not _is_number(cd.get("t")) or not _is_number(cd.get("pad")) or not _is_number(cd.get("dur", 0.0)):
			errors.append("chart '%s' cue #%d needs numeric t, pad and dur." % [chart_name, i + 1])
			continue
		var conf := float(cd.get("conf", 1.0)) if _is_number(cd.get("conf", 1.0)) else -1.0
		var cue := {"t": float(cd["t"]), "pad": int(cd["pad"]), "dur": float(cd.get("dur", 0.0)), "conf": conf}
		var label := _cue_name(chart_name, i, cue, p)
		if float(cd["pad"]) != floorf(float(cd["pad"])) or cue["pad"] < 1 or cue["pad"] > 4:
			errors.append("%s has pad %s but a cue's pad is 1, 2, 3 or 4." % [label, str(cd["pad"])])
			continue
		if conf < 0.0 or conf > 1.0:
			errors.append("%s has conf %s but conf is a number from 0 to 1." % [label, str(cd.get("conf"))])
		cues.append(cue)
	if p.bpm <= 0.0 or p.duration_s <= 0.0:
		return cues
	var beat := p.beat_s()
	var last: Dictionary = {}  # pad -> the previous cue on it {t, end, index}
	var prev_t := -INF
	for i in cues.size():
		var cue: Dictionary = cues[i]
		var t: float = cue["t"]
		var dur: float = cue["dur"]
		var end := t + dur
		var pad: int = cue["pad"]
		var label := _cue_name(chart_name, i, cue, p)
		if t < prev_t - EPS:
			errors.append("%s comes before the cue before it (%.3f s): cues must be sorted by time." % [label, prev_t])
		prev_t = maxf(prev_t, t)
		if t < MIN_CUE_T - EPS:
			errors.append("%s is before 1.0 s: nothing may be cued in the first second." % label)
		if end > p.duration_s - END_MARGIN_S + EPS:
			errors.append("%s ends at %.3f s but must end by %.3f s (half a second before the track ends)." % [label, end, p.duration_s - END_MARGIN_S])
		if dur < 0.0:
			errors.append("%s has a negative dur." % label)
		elif dur > 0.0 and dur < 0.5 * beat - EPS:
			errors.append("%s is a hold of %.3f s but a hold is at least half a beat (%.3f s)." % [label, dur, 0.5 * beat])
		var prev: Dictionary = last.get(pad, {})
		if not prev.is_empty():
			if t - float(prev["t"]) < 0.5 * beat - EPS:
				errors.append("%s is %.3f s after the cue before it on the same pad (#%d) but the same pad needs at least half a beat (%.3f s)." % [label, t - float(prev["t"]), int(prev["index"]) + 1, 0.5 * beat])
			if float(prev["end"]) > float(prev["t"]) and t < float(prev["end"]) - EPS:
				errors.append("%s starts inside the hold #%d on its own pad (which lasts until %.3f s)." % [label, int(prev["index"]) + 1, float(prev["end"])])
			elif float(prev["end"]) > float(prev["t"]) and t < float(prev["end"]) + 0.25 * beat - EPS:
				errors.append("%s starts %.3f s after the hold #%d on its own pad ends but needs at least a quarter beat (%.3f s)." % [label, t - float(prev["end"]), int(prev["index"]) + 1, 0.25 * beat])
		var other_pad: int = OTHER_PAD_OF_THUMB[pad]
		var other: Dictionary = last.get(other_pad, {})
		if not other.is_empty():
			if t - float(other["t"]) < 0.5 * beat - EPS:
				errors.append("%s is %.3f s after cue #%d on pad %d, the same thumb, but the same thumb needs at least half a beat (%.3f s)." % [label, t - float(other["t"]), int(other["index"]) + 1, other_pad, 0.5 * beat])
			elif float(other["end"]) > float(other["t"]) and t < float(other["end"]) - EPS:
				errors.append("%s lands while pad %d (the same thumb) is held by cue #%d until %.3f s." % [label, other_pad, int(other["index"]) + 1, float(other["end"])])
		var busy := 0
		for q in last:
			if q != pad and (absf(float(last[q]["t"]) - t) <= EPS or float(last[q]["end"]) > t + EPS):
				busy += 1
		if busy >= 2:
			errors.append("%s makes three pads at once: at most two pads (one per thumb) may be down together." % label)
		last[pad] = {"t": t, "end": end, "index": i}
	return cues


static func _cue_name(chart_name: String, i: int, cue: Dictionary, p: TrackPack) -> String:
	var v := p.voice_of_pad(int(cue["pad"]))
	var voice := " '%s'" % str(v.get("label", "")) if not v.is_empty() else ""
	return "chart '%s' cue #%d (t=%.3f s, pad %d%s)" % [chart_name, i + 1, float(cue["t"]), int(cue["pad"]), voice]
