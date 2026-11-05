extends TestCase
## The real track_play scene on the fixture under autoplay: it plays to the end and reports the summary; a refused pack
## is reported and does not play. Real time: the fixture is 12 s plus a 2 s countdown, so the full run takes about 14 s.

const SCENE := "res://src/track/track_play.tscn"


func _env(values: Dictionary) -> void:
	for k in ["RW_TRACK", "RW_TRACK_CHART", "RW_TRACK_START", "RW_TRACK_QUIT", "RW_AUTOPLAY"]:
		OS.unset_environment(k)
	for k in values:
		OS.set_environment(k, str(values[k]))


## Adds the scene and waits for it to finish (or `limit_s` of real time). Returns the scene.
func _play(values: Dictionary, limit_s: float) -> Node:
	_env(values)
	var scene: Node = (load(SCENE) as PackedScene).instantiate()
	tree.root.add_child(scene)
	var waited := 0.0
	while not scene.ended and waited < limit_s:
		await tree.create_timer(0.25).timeout
		waited += 0.25
	return scene


func test_perfect_autoplay_runs_the_whole_track() -> void:
	var scene := await _play({"RW_TRACK": TrackTestKit.fixture_dir(), "RW_AUTOPLAY": "perfect"}, 30.0)
	_env({})
	assert_true(scene.ended, "the track ended by itself")
	var s: Dictionary = scene.summary
	assert_false(s.is_empty(), "a summary was produced")
	if not s.is_empty():
		assert_eq(s["cues"], 29)
		assert_eq(s["hits"], 29)
		assert_eq(s["misses"], 0)
		assert_eq(s["autoplay"], "perfect")
		for v in s["voices"]:
			assert_eq(v["sounding_share"], 1.0, str(v["key"]))
		assert_near(float(s["end_s"]), 12.0, 0.001)
		assert_eq(JSON.parse_string(JSON.stringify(s))["cues"], 29, "the summary is plain JSON")
	scene.queue_free()
	await tree.process_frame


func test_start_part_way_and_missing_everything() -> void:
	var scene := await _play({"RW_TRACK": TrackTestKit.fixture_dir(), "RW_AUTOPLAY": "none", "RW_TRACK_START": 9.0, "RW_TRACK_CHART": "normal"}, 20.0)
	_env({})
	assert_true(scene.ended)
	var s: Dictionary = scene.summary
	if not s.is_empty():
		assert_eq(s["cues"], 5, "only the cues from 9.0 s on")
		assert_eq(s["misses"], 5)
		assert_eq(s["hits"], 0)
		assert_near(float(s["start_s"]), 9.0, 1e-9)
	scene.queue_free()
	await tree.process_frame


func test_a_refused_pack_does_not_play() -> void:
	var folder := TrackTestKit.make_pack(func(d: Dictionary) -> void: d["format"] = "nope")
	var scene := await _play({"RW_TRACK": folder}, 3.0)
	_env({})
	assert_true(scene.ended)
	assert_true(scene.game == null, "no game was built")
	assert_contains(scene.refused, "format is")
	scene.queue_free()
	var unset := await _play({}, 3.0)
	assert_contains(unset.refused, "RW_TRACK is not set")
	unset.queue_free()
	var bad_chart := await _play({"RW_TRACK": TrackTestKit.fixture_dir(), "RW_TRACK_CHART": "nope"}, 3.0)
	assert_contains(bad_chart.refused, "no chart named 'nope'")
	bad_chart.queue_free()
	await tree.process_frame
