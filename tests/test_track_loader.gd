extends TestCase
## The track pack loader: the fixture is accepted, and a pack that breaks a rule of docs/TRACK_PACK_FORMAT.md is refused
## with a sentence naming the field or the cue (one case per rule).

const FIX := "tests/fixtures/track_fixture/"


func _chart(cues: Array) -> Callable:
	return func(d: Dictionary) -> void:
		var list: Array = []
		for c in cues:
			list.append({"t": c[0], "pad": c[1], "dur": c[2], "conf": c[3] if c.size() > 3 else 0.9})
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
	assert_eq(p.voices.size(), 4)
	assert_eq(p.backing.size(), 1)
	assert_eq(p.streams.size(), 5, "every stem decoded")
	assert_eq(p.charts["normal"].size(), 29)
	assert_eq(p.default_chart, "normal")
	assert_near(p.beat_s(), 0.5, 1e-9)
	assert_near(float(p.stem_lengths["drums"]), 12.0, 0.005)
	assert_eq(p.voice_of_pad(3)["key"], "pads")
	assert_near(float(p.voice_of_pad(3)["gain"]), 0.8, 1e-9)
	assert_eq(p.section_at(5.0), "main")
	assert_eq(p.stems_in_order().size(), 5)
	assert_eq(p.restore_after_idle_beats, 8.0)


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


func test_header_rules() -> void:
	_refused("format", func(d: Dictionary) -> void: d["format"] = "rhythm_warfare.track.v2", "format is")
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
	_refused("four voices", func(d: Dictionary) -> void: d["voices"].pop_back(), "exactly four entries")
	_refused("five voices", func(d: Dictionary) -> void: d["voices"].append(d["voices"][0].duplicate()), "exactly four entries")
	_refused("pad used twice", func(d: Dictionary) -> void: d["voices"][1]["pad"] = 1, "already has")
	_refused("pad out of range", func(d: Dictionary) -> void: d["voices"][1]["pad"] = 5, "must be 1, 2, 3 or 4")
	_refused("voice key repeated", func(d: Dictionary) -> void: d["voices"][1]["key"] = "drums", "repeats the key 'drums'")
	_refused("backing key repeats a voice", func(d: Dictionary) -> void: d["backing"][0]["key"] = "bass", "repeats the key 'bass'")
	_refused("key characters", func(d: Dictionary) -> void: d["voices"][0]["key"] = "Drums!", "lower case letters, digits and underscores")
	_refused("label", func(d: Dictionary) -> void: d["voices"][0]["label"] = "", "has no label")
	_refused("gain range", func(d: Dictionary) -> void: d["voices"][0]["gain"] = 3, "gain is a number from 0 to 2")
	_refused("backing gain", func(d: Dictionary) -> void: d["backing"][0]["gain"] = -1, "gain is a number from 0 to 2")
	_accepted("empty backing is allowed", func(d: Dictionary) -> void: d["backing"] = [])


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
	_refused("section outside the track", func(d: Dictionary) -> void: d["sections"][2]["end_s"] = 13.0, "after the track ends")
	_refused("section role", func(d: Dictionary) -> void: d["sections"][0]["role"] = "verse", "role 'verse'")
	_refused("section backwards", func(d: Dictionary) -> void: d["sections"][0]["end_s"] = 0.0, "must start at 0 or later and end after")
	_accepted("no sections is allowed", func(d: Dictionary) -> void: d["sections"] = [])


func test_chart_header_rules() -> void:
	_refused("default_chart exists", func(d: Dictionary) -> void: d["default_chart"] = "nope", "default_chart 'nope' is not one of the charts")
	_refused("charts present", func(d: Dictionary) -> void: d["charts"] = {}, "charts must hold at least")
	_refused("cue pad", _chart([[2.0, 5, 0.0]]), "has pad 5")
	_refused("cue conf", _chart([[2.0, 1, 0.0, 2.0]]), "has conf 2.0")
	_refused("cue sorted", _chart([[2.0, 1, 0.0], [1.5, 2, 0.0]]), "must be sorted by time")
	_refused("cue after the first second", _chart([[0.5, 1, 0.0]]), "nothing may be cued in the first second")
	_refused("cue before the end", _chart([[11.6, 1, 0.0]]), "half a second before the track ends")
	_refused("hold inside the track", _chart([[10.0, 1, 2.0]]), "half a second before the track ends")
	_refused("other charts are checked too", func(d: Dictionary) -> void: d["charts"]["easy"] = [{"t": 0.2, "pad": 1, "dur": 0.0, "conf": 1.0}], "chart 'easy' cue #1")


func test_playability_rules() -> void:
	_refused("same pad gap", _chart([[2.0, 1, 0.0], [2.2, 1, 0.0]]), "same pad needs at least half a beat")
	_refused("cue inside own hold", _chart([[2.0, 1, 1.0], [2.6, 1, 0.0]]), "starts inside the hold #1 on its own pad")
	_refused("cue soon after own hold", _chart([[2.0, 1, 1.0], [3.1, 1, 0.0]]), "needs at least a quarter beat")
	_refused("same thumb gap", _chart([[2.0, 1, 0.0], [2.1, 2, 0.0]]), "the same thumb needs at least half a beat")
	_refused("same thumb while held", _chart([[2.0, 3, 1.5], [3.0, 4, 0.0]]), "lands while pad 3 (the same thumb) is held")
	_refused("three pads at once", _chart([[2.0, 1, 0.0], [2.0, 2, 0.0], [2.0, 3, 0.0]]), "three pads at once")
	_refused("hold length", _chart([[2.0, 1, 0.2]]), "a hold is at least half a beat")
	_accepted("a chord on two thumbs is fine", _chart([[2.0, 1, 0.0], [2.0, 3, 0.0]]))
	_accepted("exactly half a beat is fine", _chart([[2.0, 1, 0.0], [2.25, 1, 0.0], [2.5, 2, 0.0]]))
	_accepted("a hold then the same pad after a quarter beat", _chart([[2.0, 1, 1.0], [3.125, 1, 0.0]]))


func test_errors_name_the_cue() -> void:
	var folder := TrackTestKit.make_pack(_chart([[2.0, 3, 0.0], [2.1, 4, 0.0]]))
	var r := TrackPack.load_pack(folder)
	assert_contains(r["errors"], "chart 'normal' cue #2 (t=2.100 s, pad 4 'Bass')")
