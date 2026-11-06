extends TestCase
## Track scenes, the safety net (docs/RUN_TRACK_SCENES.md "Where packs are found"): with track scenes compiled in but off, a run is exactly what it was before the feature. A few runs on the virtual
## clock (the main run with a scripted player who misses some cues, the main run choosing the second route, a two-lap path, a run held by a minigame) are recorded event by event and cue by cue; the
## recording in tests/fixtures/track_scenes/baseline_runs.json was made from the engine BEFORE the track scene work, and every run here must reproduce it line for line (song times to 1e-9 s).
##
## Re-record (only when an intended change of the ordinary run moves these numbers):
##   godot --headless --path . -s tests/fixtures/track_scenes/record_baseline.gd   (uses baseline_recorder.gd, as this test does)

const BASELINE := "res://tests/fixtures/track_scenes/baseline_runs.json"


const Recorder := preload("res://tests/fixtures/track_scenes/baseline_recorder.gd")


func test_with_track_scenes_off_the_runs_are_the_recorded_ones() -> void:
	assert_false(RunTrackScenes.active(), "track scenes are off under the test runner unless a test turns them on")
	var base: Variant = JSON.parse_string(FileAccess.get_file_as_string(BASELINE))
	assert_true(typeof(base) == TYPE_DICTIONARY, "the recording exists")
	if typeof(base) != TYPE_DICTIONARY:
		return
	var now := Recorder.record_all()
	for name in base:
		var want: Array = base[name]
		var got: Array = now.get(name, [])
		assert_eq(got.size(), want.size(), "%s: as many events and cues as recorded" % name)
		var first_diff := -1
		for i in mini(got.size(), want.size()):
			if str(got[i]) != str(want[i]):
				first_diff = i
				break
		assert_eq(first_diff, -1, "%s: identical to the recording (first difference at line %d: %s / recorded %s)" % [name, first_diff,
			str(got[first_diff]) if first_diff >= 0 else "", str(want[first_diff]) if first_diff >= 0 else ""])


func test_the_switch_and_the_environment_keep_track_scenes_off() -> void:
	var d := RunData.load_default()
	assert_eq(d.errors, [], "run data validates")
	assert_true(d.track_scenes == null, "no track scene data is attached under the test runner")
	RunTrackScenes.enabled = 1
	OS.set_environment("RW_RUN_TRACKS", "0")
	assert_false(RunTrackScenes.active(), "RW_RUN_TRACKS=0 wins over the switch")
	OS.unset_environment("RW_RUN_TRACKS")
	assert_true(RunTrackScenes.active(), "the switch turns them on")
	RunTrackScenes.enabled = -1
	assert_false(RunTrackScenes.active(), "and back off")
