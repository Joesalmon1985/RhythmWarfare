extends SceneTree
## Writes tests/fixtures/track_scenes/baseline_runs.json from the engine as it is now (see tests/test_run_tracks_safety.gd).

const Recorder := preload("res://tests/fixtures/track_scenes/baseline_recorder.gd")


func _init() -> void:
	var f := FileAccess.open("res://tests/fixtures/track_scenes/baseline_runs.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(Recorder.record_all(), " "))
	f.close()
	print("baseline written")
	quit()
