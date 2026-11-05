extends TestCase
## The track pack loader: the fixture is accepted, and a pack that breaks a rule of docs/TRACK_PACK_FORMAT.md is refused
## with a sentence naming the field or the cue (one case per rule).

const FIX := "tests/fixtures/track_fixture/"


## A one-chart mutation. Each cue is [t, pad, dur] and, unless a fourth item names the voice, belongs to the voice whose
## stretch holds t in the fixture (drums 0 to 4, lead 4 to 8, a gap to 9, bass 9 to 16).
func _chart(cues: Array) -> Callable:
	return func(d: Dictionary) -> void:
		var list: Array = []
		for c in cues:
			var t: float = c[0]
			var voice: String = c[3] if c.size() > 3 else ("drums" if t < 4.0 else ("lead" if t < 8.0 else "bass"))
			list.append({"t": t, "pad": c[1], "dur": c[2], "conf": 0.9, "voice": voice})
		d["charts"] = {"normal": list}
		d["default_chart"] = "normal"


## Builds a pack with `mutate` applied, loads it, and checks it is refused with an error containing `needle`.
func _refused(label: String, mutate: Callable, needle: String, extra: Dictionary = {}, id: String = "track_fixture") -> void:
	var folder := TrackTestKit.make_pack(mutate, id, extra)
	var r := TrackPack.load_pack(folder)
	assert_true(r["pack"] == null, "%s: the pack must be refused" % label)
	assert_contains(r["errors"], needle, label)


func _accepted(label: String, mutate: Callable) -> void:
	var r := TrackPack.load_pack(TrackTestKit.make_pack(mutate))
	assert_eq(r["errors"], [], label)
	assert_true(r["pack"] != null, label)


func test_fixture_is_accepted() -> void:
	var r := TrackPack.load_pack(TrackTestKit.fixture_dir())
	assert_eq(r["errors"], [])
	var p: TrackPack = r["pack"]
	assert_true(p != null)
	if p == null:
		return
	assert_eq(p.id, "track_fixture")
	assert_eq(p.voices.size(), 3)
	assert_eq(p.backing.size(), 1)
	assert_eq(p.streams.size(), 4, "every stem decoded")
	assert_eq(p.charts["normal"].size(), 25)
	assert_eq(p.charts["easy"].size(), 7)
	assert_eq(p.default_chart, "normal")
	assert_near(p.beat_s(), 0.5, 1e-9)
	assert_near(float(p.stem_lengths["drums"]), 16.0, 0.005)
	assert_eq(p.voice_by_key("lead")["kind"], "pitched")
	assert_eq(p.voice_by_key("drums")["kind"], "drums")
	assert_near(float(p.voice_by_key("lead")["gain"]), 0.8, 1e-9)
	assert_eq(p.voice_by_key("nope"), {})
	assert_eq(p.focus.size(), 3)
	assert_eq(p.focus[2]["voice"], "bass")
	assert_eq(p.section_at(5.0), "main")
	assert_eq(p.stems_in_order().size(), 4)
	assert_eq(p.restore_after_idle_beats, 8.0)
	assert_eq(p.charts["normal"][0]["voice"], "drums")


func test_trailing_slash_and_header_only_load() -> void:
	var r := TrackPack.load_pack(TrackTestKit.fixture_dir() + "/", false)
	assert_eq(r["errors"], [])
	assert_true(r["pack"].streams.is_empty(), "no decoding when asked not to")


func test_folder_and_json_problems() -> void:
	var r := TrackPack.load_pack(TrackTestKit.temp_root().path_join("no_such_pack"))
	assert_true(r["pack"] == null)
	assert_contains(r["errors"], "does not exist")
	var folder := TrackTestKit.temp_root().path_join("no_json")
	DirAccess.make_dir_recursive_absolute(folder)
	DirAccess.remove_absolute(folder.path_join("track.json"))  # left over from an earlier run
	assert_contains(TrackPack.load_pack(folder)["errors"], "no track.json")
	var f := FileAccess.open(folder.path_join("track.json"), FileAccess.WRITE)
	f.store_string("{ not json")
	f.close()
	assert_contains(TrackPack.load_pack(folder)["errors"], "not valid JSON")


func test_version_1_is_refused_with_a_clear_sentence() -> void:
	var folder := TrackTestKit.make_pack(func(d: Dictionary) -> void: d["format"] = "rhythm_warfare.track.v1")
	var r := TrackPack.load_pack(folder)
	assert_true(r["pack"] == null)
	assert_eq(r["errors"].size(), 1)
	assert_contains(r["errors"], "is version 1")
	assert_contains(r["errors"], "must be re-imported")


func test_header_rules() -> void:
	_refused("format", func(d: Dictionary) -> void: d["format"] = "rhythm_warfare.track.v3", "format is")
	_refused("id differs from folder", func(d: Dictionary) -> void: d["id"] = "other_id", "must equal the folder name")
	_refused("id characters", func(d: Dictionary) -> void: d["id"] = "Bad-Id", "lower case letters, digits and underscores", {}, "Bad-Id")
	_refused("duration_s above 0", func(d: Dictionary) -> void: d["duration_s"] = 0, "duration_s must be a number above 0")
	_refused("duration_s equals the stems", func(d: Dictionary) -> void: d["duration_s"] = 13.0, "duration_s is 13.000 s but stem")
	_refused("tempo.bpm", func(d: Dictionary) -> void: d["tempo"]["bpm"] = 0, "tempo.bpm must be")
	_refused("tempo.first_downbeat_s", func(d: Dictionary) -> void: d["tempo"]["first_downbeat_s"] = -1, "tempo.first_downbeat_s")
	_refused("tempo.beats_per_bar", func(d: Dictionary) -> void: d["tempo"]["beats_per_bar"] = 3, "tempo.beats_per_bar must be 4")
	_refused("tempo.confidence", func(d: Dictionary) -> void: d["tempo"]["confidence"] = 1.5, "tempo.confidence")
	_refused("rules.restore_after_idle_beats", func(d: Dictionary) -> void: d["rules"]["restore_after_idle_beats"] = 0, "restore_after_idle_beats")


func test_voice_and_backing_rules() -> void:
	_refused("no voices", func(d: Dictionary) -> void: d["voices"] = [], "voices must hold one to six entries, found 0")
	_refused("seven voices", func(d: Dictionary) -> void:
		for i in 4:
			var v: Dictionary = d["voices"][0].duplicate()
			v["key"] = "extra%d" % i
			d["voices"].append(v), "voices must hold one to six entries, found 7")
	_refused("voice key repeated", func(d: Dictionary) -> void: d["voices"][1]["key"] = "drums", "repeats the key 'drums'")
	_refused("backing key repeats a voice", func(d: Dictionary) -> void: d["backing"][0]["key"] = "bass", "repeats the key 'bass'")
	_refused("key characters", func(d: Dictionary) -> void: d["voices"][0]["key"] = "Drums!", "lower case letters, digits and underscores")
	_refused("label", func(d: Dictionary) -> void: d["voices"][0]["label"] = "", "has no label")
	_refused("kind", func(d: Dictionary) -> void: d["voices"][0]["kind"] = "vocal", "kind 'vocal' but a kind is drums or pitched")
	_refused("gain range", func(d: Dictionary) -> void: d["voices"][0]["gain"] = 3, "gain is a number from 0 to 2")
	_refused("backing gain", func(d: Dictionary) -> void: d["backing"][0]["gain"] = -1, "gain is a number from 0 to 2")
	_accepted("empty backing is allowed", func(d: Dictionary) -> void: d["backing"] = [])
	_accepted("kind is optional", func(d: Dictionary) -> void: d["voices"][0].erase("kind"))
	_accepted("a voice has no pad and one is ignored", func(d: Dictionary) -> void: d["voices"][0]["pad"] = 9)


func test_focus_rules() -> void:
	_refused("focus missing", func(d: Dictionary) -> void: d.erase("focus"), "focus must be a list with at least one stretch")
	_refused("focus empty", func(d: Dictionary) -> void: d["focus"] = [], "focus must be a list with at least one stretch")
	_refused("stretch unknown voice", func(d: Dictionary) -> void: d["focus"][1]["voice"] = "vocals", "focus stretch #2 (4.000 to 8.000 s, voice 'vocals') names the voice 'vocals' but the pack has no such voice")
	_refused("stretch overlaps", func(d: Dictionary) -> void: d["focus"][1]["start_s"] = 3.0, "focus stretch #2 (3.000 to 8.000 s, voice 'lead') starts at 3.000 s, before the stretch before it ends at 4.000 s")
	_refused("stretches out of order", func(d: Dictionary) -> void:
		d["focus"] = [d["focus"][2], d["focus"][0], d["focus"][1]], "stretches must be in time order")
	_refused("stretch outside the track", func(d: Dictionary) -> void: d["focus"][2]["end_s"] = 17.0, "ends after the track ends at 16.000 s")
	_refused("stretch before the track", func(d: Dictionary) -> void: d["focus"][0]["start_s"] = -1.0, "must start at 0 or later")
	_refused("stretch backwards", func(d: Dictionary) -> void: d["focus"][0]["end_s"] = 0.0, "end after it starts")
	_refused("stretch under 8 beats", func(d: Dictionary) -> void: d["focus"][1]["end_s"] = 7.9, "is 3.900 s long but a stretch is at least 8 beats (4.000 s)")
	_refused("stretch needs numbers", func(d: Dictionary) -> void: d["focus"][1]["end_s"] = "x", "focus stretch #2 needs numeric start_s and end_s")
	_accepted("one stretch is enough", func(d: Dictionary) -> void:
		d["focus"] = [{"start_s": 0.0, "end_s": 16.0, "voice": "bass"}]
		d["charts"] = {"normal": [{"t": 2.0, "pad": 1, "dur": 0.0, "conf": 1.0, "voice": "bass"}]})
	_accepted("a stretch of exactly 8 beats", func(d: Dictionary) -> void: d["focus"][1]["end_s"] = 8.0)
	_accepted("the same voice in two stretches", func(d: Dictionary) -> void:
		d["focus"] = [{"start_s": 0.0, "end_s": 4.0, "voice": "drums"}, {"start_s": 4.0, "end_s": 8.0, "voice": "drums"}]
		d["charts"] = {"normal": [{"t": 2.0, "pad": 1, "dur": 0.0, "conf": 1.0, "voice": "drums"}]})


func test_cue_voice_rules() -> void:
	_refused("cue without a voice", func(d: Dictionary) -> void: d["charts"]["normal"][0].erase("voice"), "chart 'normal' cue #1 (t=1.000 s, pad 1) has no voice")
	_refused("cue unknown voice", func(d: Dictionary) -> void: d["charts"]["normal"][0]["voice"] = "vocals", "names the voice 'vocals' but the pack has no such voice")
	_refused("cue for the wrong voice", _chart([[2.0, 1, 0.0, "lead"]]), "is for voice 'lead' but the focus stretch at that time (0.000 to 4.000 s) belongs to 'drums'")
	_refused("cue in a gap", _chart([[8.5, 1, 0.0, "lead"]]), "lies outside every focus stretch")
	_refused("cue after the last stretch", _chart([[15.9, 1, 0.0, "bass"]]), "half a second before the track ends")
	_refused("hold running past its stretch", _chart([[7.0, 1, 1.5]]), "is a hold ending at 8.500 s, after its focus stretch ends at 8.000 s")
	_refused("hold running into a gap", _chart([[7.5, 2, 1.0]]), "a hold must end inside the same stretch")
	_refused("other charts are checked for voices", func(d: Dictionary) -> void:
		d["charts"]["easy"][0]["voice"] = "bass", "chart 'easy' cue #1 (t=2.000 s, pad 1 'bass') is for voice 'bass'")
	_accepted("a hold ending exactly at the stretch end", _chart([[6.0, 1, 2.0]]))
	_accepted("a cue exactly at a stretch start", _chart([[4.0, 1, 0.0]]))


func test_stem_rules() -> void:
	_refused("stem path with ..", func(d: Dictionary) -> void: d["voices"][0]["stem"] = "../drums.ogg", "relative path inside the pack")
	_refused("absolute stem path", func(d: Dictionary) -> void: d["voices"][0]["stem"] = "/etc/passwd.ogg", "relative path inside the pack")
	_refused("not an ogg name", func(d: Dictionary) -> void: d["voices"][0]["stem"] = "stems/drums.mp3", "Ogg Vorbis files")
	_refused("stem file missing", func(d: Dictionary) -> void: d["voices"][0]["stem"] = "stems/nope.ogg", "does not exist")
	_refused("stem is not audio", func(d: Dictionary) -> void: d["voices"][0]["stem"] = "stems/junk.ogg", "is not an Ogg Vorbis file",
		{"stems/junk.ogg": TrackTestKit.fixture_dir().path_join("track.json")})
	_refused("stem is mono", func(_d: Dictionary) -> void: pass, "48000 Hz stereo", {"stems/lead.ogg": TrackTestKit.fixture_dir().path_join("extra/mono.ogg")})
	_refused("stem is 44.1 kHz", func(_d: Dictionary) -> void: pass, "48000 Hz stereo", {"stems/lead.ogg": TrackTestKit.fixture_dir().path_join("extra/rate44.ogg")})
	_refused("stems of different length", func(_d: Dictionary) -> void: pass, "all stems must be the same length",
		{"stems/lead.ogg": TrackTestKit.fixture_dir().path_join("extra/short.ogg")})


func test_section_rules() -> void:
	_refused("sections overlap", func(d: Dictionary) -> void: d["sections"][1]["start_s"] = 3.0, "before the previous section 'intro' ends")
	_refused("section outside the track", func(d: Dictionary) -> void: d["sections"][2]["end_s"] = 17.0, "after the track ends")
	_refused("section role", func(d: Dictionary) -> void: d["sections"][0]["role"] = "verse", "role 'verse'")
	_refused("section backwards", func(d: Dictionary) -> void: d["sections"][0]["end_s"] = 0.0, "must start at 0 or later and end after")
	_accepted("no sections is allowed", func(d: Dictionary) -> void: d["sections"] = [])


func test_chart_header_rules() -> void:
	_refused("default_chart exists", func(d: Dictionary) -> void: d["default_chart"] = "nope", "default_chart 'nope' is not one of the charts")
	_refused("charts present", func(d: Dictionary) -> void: d["charts"] = {}, "charts must hold at least")
	_refused("cue pad", _chart([[2.0, 5, 0.0]]), "has pad 5")
	_refused("cue conf", func(d: Dictionary) -> void: d["charts"]["normal"][0]["conf"] = 2.0, "has conf 2.0")
	_refused("cue sorted", _chart([[2.0, 1, 0.0], [1.5, 2, 0.0]]), "must be sorted by time")
	_refused("cue after the first second", _chart([[0.5, 1, 0.0]]), "nothing may be cued in the first second")
	_refused("cue before the end", _chart([[15.6, 1, 0.0]]), "half a second before the track ends")
	_refused("hold inside the track", _chart([[14.0, 1, 2.0]]), "half a second before the track ends")
	_refused("other charts are checked too", func(d: Dictionary) -> void: d["charts"]["easy"] = [{"t": 0.2, "pad": 1, "dur": 0.0, "conf": 1.0, "voice": "drums"}], "chart 'easy' cue #1")


func test_playability_rules() -> void:
	_refused("same pad gap", _chart([[2.0, 1, 0.0], [2.2, 1, 0.0]]), "same pad needs at least half a beat")
	_refused("cue inside own hold", _chart([[2.0, 1, 1.0], [2.6, 1, 0.0]]), "starts inside the hold #1 on its own pad")
	_refused("cue soon after own hold", _chart([[2.0, 1, 1.0], [3.1, 1, 0.0]]), "needs at least a quarter beat")
	_refused("same thumb gap", _chart([[2.0, 1, 0.0], [2.1, 2, 0.0]]), "the same thumb needs at least half a beat")
	_refused("same thumb while held", _chart([[2.0, 3, 1.5], [3.0, 4, 0.0]]), "lands while pad 3 (the same thumb) is held")
	_refused("three pads at once", _chart([[2.0, 1, 0.0], [2.0, 2, 0.0], [2.0, 3, 0.0]]), "three pads at once")
	_refused("playability holds across voices", _chart([[3.9, 1, 0.0, "drums"], [4.0, 2, 0.0, "lead"]]), "the same thumb needs at least half a beat")
	_refused("hold length", _chart([[2.0, 1, 0.2]]), "a hold is at least half a beat")
	_accepted("a chord on two thumbs is fine", _chart([[2.0, 1, 0.0], [2.0, 3, 0.0]]))
	_accepted("exactly half a beat is fine", _chart([[2.0, 1, 0.0], [2.25, 1, 0.0], [2.5, 2, 0.0]]))
	_accepted("a hold then the same pad after a quarter beat", _chart([[2.0, 1, 1.0], [3.125, 1, 0.0]]))


func test_errors_name_the_cue() -> void:
	var folder := TrackTestKit.make_pack(_chart([[2.0, 3, 0.0], [2.1, 4, 0.0]]))
	var r := TrackPack.load_pack(folder)
	assert_contains(r["errors"], "chart 'normal' cue #2 (t=2.100 s, pad 4 'drums')")
