class_name RunTrackPlan
extends RefCounted
## The plan of a track scene (docs/RUN_TRACK_SCENES.md "The scene plan"), as one pure function of the pack's track.json and the scene's assignment: the tempo, the bar the scene enters the
## track at, how many 64-beat laps it lasts, from which lap its doors open, which chart it plays, and the scene time of every lap boundary. Nothing here touches the disk, the clock or the audio.
##
## With B = 60 / tempo.bpm seconds a beat and bars of 4 beats counted from tempo.first_downbeat_s:
## - entry bar E: "drop1": the first bar of the first `drop` section minus lead_in_bars (not below 0); "drop2": the same from the second `drop` (the first when there is only one); "start": 0; a
##   track without a drop enters at its loudest section (source.sections_detail intensity_db; without those, its longest section that is not an intro or an outro; without sections, bar 0) minus
##   the lead-in. `start_bar` overrides all of it. When fewer than 16 whole bars are left after E, E moves back so one lap fits (a short track); a track of fewer than 16 bars cannot be a scene.
## - laps: drop1 / start (and the no-drop case): the whole number of laps whose end is nearest half-way through the track (duration_s / 2), at least 2; drop2: the laps that fit before the track's
##   last 2 bars, at least 2. Never more than max_laps, never past the end of the audio (the audio wins over "at least 2"). `laps` overrides (still never past the end of the audio).
## - doors_from_lap: the first lap whose doors open (default 2); a plan with fewer laps opens them on its last.
## - chart: the chart named by `chart`, else the pack's default_chart.
## Scene time 0 is the downbeat of bar E (track time `entry_t`); lap k (from 1) is bars E + 16(k-1) to E + 16k.

const LAP_BARS := 16
const BEATS_PER_BAR := 4
const DEFAULTS := {"entry": "drop1", "lead_in_bars": 16, "doors_from_lap": 2, "chart": "normal", "max_laps": 12}
const ENTRIES := ["drop1", "drop2", "start"]


## The facts of a pack the plan reads: {id, dir, bpm, first_downbeat_s, duration_s, sections: [{id, role, start_s, end_s}], intensity: {section id: dB}, charts: {name: [cue]}, default_chart}.
## `raw` is the parsed track.json (for source.sections_detail, which TrackPack does not keep); {} when it is not at hand.
static func info_of(pack: TrackPack, raw: Dictionary = {}) -> Dictionary:
	var intensity := {}
	var src: Variant = raw.get("source", {})
	if typeof(src) == TYPE_DICTIONARY and typeof((src as Dictionary).get("sections_detail", null)) == TYPE_ARRAY:
		for s in (src as Dictionary)["sections_detail"]:
			if typeof(s) == TYPE_DICTIONARY and (s as Dictionary).has("id") and typeof((s as Dictionary).get("intensity_db")) in [TYPE_INT, TYPE_FLOAT]:
				intensity[str(s["id"])] = float(s["intensity_db"])
	return {"id": pack.id, "dir": pack.dir, "bpm": pack.bpm, "first_downbeat_s": pack.first_downbeat_s, "duration_s": pack.duration_s, "sections": pack.sections, "intensity": intensity,
		"charts": pack.charts, "default_chart": pack.default_chart}


## The plan for `info` (info_of) and `entry` (the assignment's fields over DEFAULTS). Returns the plan, or {"error": sentence} when the track cannot be a scene.
## Plan fields: track, dir, bpm, beat_s, bar_s, lap_s, first_downbeat_s, duration_s, entry (the rule used), entry_bar, entry_t (track time of bar E's downbeat), laps, max_laps, doors_from_lap
## (effective: at most laps), chart (the name played), cues (that chart's cues, in track seconds), total_bars (whole bars of audio from the first downbeat), lap_scene_t ([0, lap_s, .., laps * lap_s]:
## the scene time of every lap boundary), end_t (track time the plan ends at), half_bar (the track's half-way point in bars), laps_rule ("half" | "drop2" | "override").
static func compute(info: Dictionary, p_entry: Dictionary) -> Dictionary:
	var entry := DEFAULTS.duplicate()
	entry.merge(p_entry, true)
	var bpm := float(info.get("bpm", 0.0))
	var dur := float(info.get("duration_s", 0.0))
	var fd := float(info.get("first_downbeat_s", 0.0))
	if bpm <= 0.0 or dur <= 0.0:
		return {"error": "track %s has no tempo or no length" % info.get("id", "?")}
	var beat := 60.0 / bpm
	var bar := beat * BEATS_PER_BAR
	var total_bars := int(floor((dur - fd) / bar + 1e-6))
	if total_bars < LAP_BARS:
		return {"error": "track %s has %d whole bars, fewer than the %d of one lap" % [info.get("id", "?"), total_bars, LAP_BARS]}
	var lead := int(entry["lead_in_bars"])
	var rule := str(entry["entry"])
	var drops: Array = (info.get("sections", []) as Array).filter(func(s: Dictionary) -> bool: return str(s.get("role", "")) == "drop")
	var e_bar := 0
	if entry.has("start_bar"):
		e_bar = int(entry["start_bar"])
	elif rule == "start":
		e_bar = 0
	elif drops.is_empty():
		var loud := _loudest(info)
		e_bar = (_bar_of(float(loud["start_s"]), fd, bar) - lead) if not loud.is_empty() else 0
	else:
		var d: Dictionary = drops[1] if rule == "drop2" and drops.size() > 1 else drops[0]
		e_bar = _bar_of(float(d["start_s"]), fd, bar) - lead
	e_bar = maxi(e_bar, 0)
	if total_bars - e_bar < LAP_BARS:  # a short track, or an entry too near its end: move back so one whole lap fits
		e_bar = maxi(total_bars - LAP_BARS, 0)
	var fit := (total_bars - e_bar) / LAP_BARS  # whole laps before the end of the audio
	var max_laps := int(entry["max_laps"])
	var half_bar := (dur * 0.5 - fd) / bar
	var laps := 0
	var laps_rule := ""
	if entry.has("laps"):
		laps = int(entry["laps"])
		laps_rule = "override"
	elif rule == "drop2":
		laps = maxi((total_bars - 2 - e_bar) / LAP_BARS, 2)
		laps_rule = "drop2"
	else:
		laps = maxi(int(round((half_bar - float(e_bar)) / float(LAP_BARS))), 2)
		laps_rule = "half"
	if laps_rule != "override":
		laps = mini(laps, max_laps)
	laps = clampi(laps, 1, fit)
	var chart := str(entry["chart"])
	var charts: Dictionary = info.get("charts", {})
	if not charts.has(chart):
		chart = str(info.get("default_chart", ""))
	var lap_s := float(LAP_BARS * BEATS_PER_BAR) * beat
	var bounds: Array = []
	for k in laps + 1:
		bounds.append(float(k) * lap_s)
	var entry_t := fd + float(e_bar) * bar
	return {"track": str(info.get("id", "")), "dir": str(info.get("dir", "")), "bpm": bpm, "beat_s": beat, "bar_s": bar, "lap_s": lap_s, "first_downbeat_s": fd, "duration_s": dur,
		"entry": rule, "entry_bar": e_bar, "entry_t": entry_t, "laps": laps, "max_laps": max_laps, "doors_from_lap": mini(maxi(int(entry["doors_from_lap"]), 1), laps), "chart": chart,
		"cues": charts.get(chart, []), "total_bars": total_bars, "lap_scene_t": bounds, "end_t": entry_t + float(laps) * lap_s, "half_bar": half_bar, "laps_rule": laps_rule}


## The bar (from the first downbeat) a track time falls on, to the nearest bar line (the tools put sections on bar lines).
static func _bar_of(t: float, fd: float, bar: float) -> int:
	return int(round((t - fd) / bar))


## The loudest section by source.sections_detail's intensity; without intensities the longest section that is not an intro or an outro ({} when there is none).
static func _loudest(info: Dictionary) -> Dictionary:
	var best: Dictionary = {}
	var inten: Dictionary = info.get("intensity", {})
	for s: Dictionary in info.get("sections", []):
		if inten.has(str(s.get("id", ""))):
			if best.is_empty() or float(inten[str(s["id"])]) > float(inten.get(str(best["id"]), -INF)):
				best = s
	if not best.is_empty():
		return best
	for s: Dictionary in info.get("sections", []):
		if str(s.get("role", "")) in ["intro", "outro"]:
			continue
		if best.is_empty() or float(s["end_s"]) - float(s["start_s"]) > float(best["end_s"]) - float(best["start_s"]):
			best = s
	return best
