extends RefCounted
## Synthetic track packs and assignment files for the track scene tests (tests/test_run_tracks_*.gd), written by the tests themselves under user:// (nothing of them is committed but this script).
## A pack is a rhythm_warfare.track.v2 track.json that obeys every rule TrackPack.load_pack checks, with the tiny stems of tests/fixtures/track_fixture copied in (the loader only reads their
## headers when it does not decode, which is how track scenes read a pack). Two voices: "drums" (kind drums) and "bass" (pitched).

const STEMS_FROM := "res://tests/fixtures/track_fixture/stems"
const ROOT := "user://test_track_scene_packs"
const SCENES_JSON := "user://test_track_scenes.json"


## The folder the tests' packs are written to, absolute.
static func root() -> String:
	return ProjectSettings.globalize_path(ROOT)


## Removes every pack written so far.
static func clear() -> void:
	_rm_tree(root())


static func _rm_tree(dir: String) -> void:
	var d := DirAccess.open(dir)
	if d == null:
		return
	for f in d.get_files():
		DirAccess.remove_absolute(dir.path_join(f))
	for s in d.get_directories():
		_rm_tree(dir.path_join(s))
	DirAccess.remove_absolute(dir)


## Writes pack `id`: `spec` = {bpm, first_downbeat_s (0), bars (the length in bars; or duration_s), sections: [[id, role, first bar, end bar]], intensity: {section id: dB},
## cue_bars: [first bar, end bar) with a tap on every beat (or every step_beats beats; pads 1 3 2 4 in turn by beat, voice drums), bass_from_bar (the voice is "bass" from this bar on; -1 never), extra: [{beat, pad, dur_beats, voice}]
## (beats counted from the first downbeat, added to the taps; a tap of the grid on the same beat is left out), gap_bars: [[from, to)] with no cues, charts: names (["normal"])}.
## Returns the pack's folder.
static func write_pack(id: String, spec: Dictionary) -> String:
	var bpm := float(spec.get("bpm", 174.0))
	var beat := 60.0 / bpm
	var fd := float(spec.get("first_downbeat_s", 0.0))
	var dur := float(spec.get("duration_s", fd + float(spec.get("bars", 128)) * 4.0 * beat))
	var bass_from := int(spec.get("bass_from_bar", -1))
	var voice_at := func(b: float) -> String: return "bass" if bass_from >= 0 and b >= float(bass_from * 4) else "drums"
	var cues: Array = []
	var extra: Array = spec.get("extra", [])
	var taken := {}
	for x: Dictionary in extra:
		taken[snappedf(float(x["beat"]), 0.001)] = true
	var cb: Array = spec.get("cue_bars", [])
	var gaps: Array = spec.get("gap_bars", [])
	if not cb.is_empty():
		var k := 0
		for bt in range(int(cb[0]) * 4, int(cb[1]) * 4):
			var in_gap := false
			for g in gaps:
				if bt >= int(g[0]) * 4 and bt < int(g[1]) * 4:
					in_gap = true
			if in_gap or taken.has(snappedf(float(bt), 0.001)) or _near_extra(float(bt), extra):
				k += 1
				continue
			var t := fd + float(bt) * beat
			if (bt - int(cb[0]) * 4) % int(spec.get("step_beats", 1)) != 0:  # (a sparser grid: a tap every step_beats beats)
				k += 1
				continue
			if t >= 1.0 and t <= dur - 0.6:
				cues.append({"t": t, "pad": [1, 3, 2, 4][k % 4], "dur": 0.0, "conf": 0.9, "voice": voice_at.call(float(bt))})
			k += 1
	for x: Dictionary in extra:
		cues.append({"t": fd + float(x["beat"]) * beat, "pad": int(x["pad"]), "dur": float(x.get("dur_beats", 0.0)) * beat, "conf": 0.9, "voice": str(x.get("voice", voice_at.call(float(x["beat"]))))})
	cues.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["t"]) < float(b["t"]) if float(a["t"]) != float(b["t"]) else int(a["pad"]) < int(b["pad"]))
	var focus: Array = []
	if bass_from > 0:
		focus.append({"start_s": 0.0, "end_s": fd + float(bass_from * 4) * beat, "voice": "drums"})
		focus.append({"start_s": fd + float(bass_from * 4) * beat, "end_s": dur, "voice": "bass"})
	else:
		focus.append({"start_s": 0.0, "end_s": dur, "voice": "bass" if bass_from == 0 else "drums"})
	var sections: Array = []
	var details: Array = []
	for s in spec.get("sections", []):
		sections.append({"id": str(s[0]), "role": str(s[1]), "start_s": maxf(fd + float(int(s[2]) * 4) * beat, 0.0), "end_s": minf(fd + float(int(s[3]) * 4) * beat, dur)})
	var inten: Dictionary = spec.get("intensity", {})
	for sid in inten:
		details.append({"id": sid, "intensity_db": float(inten[sid])})
	var charts := {}
	for name in spec.get("charts", ["normal"]):
		charts[str(name)] = cues
	var pack := {"format": TrackPack.FORMAT, "id": id, "title": id, "artist": "synthetic", "duration_s": dur,
		"tempo": {"bpm": bpm, "first_downbeat_s": fd, "beats_per_bar": 4, "confidence": 0.9},
		"voices": [{"key": "drums", "label": "Drums", "kind": "drums", "stem": "stems/drums.ogg", "gain": 1.0}, {"key": "bass", "label": "Bass", "kind": "pitched", "stem": "stems/bass.ogg", "gain": 1.0}],
		"backing": [{"key": "backing", "stem": "stems/backing.ogg", "gain": 1.0}], "sections": sections, "focus": focus, "charts": charts,
		"default_chart": str((spec.get("charts", ["normal"]) as Array)[0]), "rules": {"restore_after_idle_beats": 8}, "source": {"sections_detail": details}}
	if bool(spec.get("other", false)):  # (a third voice, "other", a pitched synth: what a transition's tail lets linger)
		(pack["voices"] as Array).append({"key": "other", "label": "Synths", "kind": "pitched", "stem": "stems/other.ogg", "gain": 1.0})
	var dir := root().path_join(id)
	DirAccess.make_dir_recursive_absolute(dir.path_join("stems"))
	for f in ["drums", "bass", "backing"]:
		DirAccess.copy_absolute(ProjectSettings.globalize_path(STEMS_FROM.path_join(f + ".ogg")), dir.path_join("stems").path_join(f + ".ogg"))
	if bool(spec.get("other", false)):
		DirAccess.copy_absolute(ProjectSettings.globalize_path(STEMS_FROM.path_join("lead.ogg")), dir.path_join("stems").path_join("other.ogg"))
	var fa := FileAccess.open(dir.path_join("track.json"), FileAccess.WRITE)
	fa.store_string(JSON.stringify(pack, " "))
	fa.close()
	return dir


## A grid tap too close to an extra cue on the same thumb (the pack's playability rules) is left out.
static func _near_extra(bt: float, extra: Array) -> bool:
	for x: Dictionary in extra:
		var a := float(x["beat"])
		var b := a + float(x.get("dur_beats", 0.0))
		if bt > a - 1.0 and bt < b + 1.0:
			return true
	return false


## "Go Back" as the contract's worked example has it: 174.0032 BPM, first downbeat 0.0013 s, 298.5594 s, drop1 at bar 56, drop2 at bar 160; taps on every beat from bar 36 to bar 110.
static func go_back_spec() -> Dictionary:
	return {"bpm": 174.0032, "first_downbeat_s": 0.0013, "duration_s": 298.5594, "cue_bars": [36, 110],
		"sections": [["intro1", "intro", 0, 48], ["build1", "build", 48, 56], ["drop1", "drop", 56, 96], ["breakdown1", "breakdown", 96, 152], ["build2", "build", 152, 160], ["drop2", "drop", 160, 208], ["outro1", "outro", 208, 216]]}


## Writes the assignment file (format v1) with `paths` and returns its path.
static func write_scenes(paths: Dictionary, defaults: Dictionary = {}) -> String:
	var v := {"format": RunTrackScenes.FORMAT, "defaults": defaults, "paths": paths}
	var fa := FileAccess.open(SCENES_JSON, FileAccess.WRITE)
	fa.store_string(JSON.stringify(v, " "))
	fa.close()
	return SCENES_JSON


## The main run's data with track scenes attached from `paths` (the packs in root()).
static func main_data(paths: Dictionary, p_seed := 7, defaults: Dictionary = {}) -> RunData:
	var d := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, p_seed)
	RunTrackScenes.load_for(d, write_scenes(paths, defaults), root())
	return d
