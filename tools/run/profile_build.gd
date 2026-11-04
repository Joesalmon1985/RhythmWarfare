extends Control
## How long does building each world's StoryStage take, and in which part? (the run builds a stage on the main thread in a cue-free guard; anything longer than the
## guard stalls the audio events that RunAudio schedules from _process.)  Needs a display:
##   RW_BUILD_WORLDS=night_one,hospital godot --path . res://tools/run/profile_build.tscn

const WORLDS := ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]


func _ready() -> void:
	size = Vector2(1152, 400)
	var worlds: Array = WORLDS
	if OS.has_environment("RW_BUILD_WORLDS"):
		worlds = OS.get_environment("RW_BUILD_WORLDS").split(",")
	for w in worlds:
		var t0 := Time.get_ticks_usec()
		var entry := StoryChapters.load_default().chapter(str(w))
		var sd: StoryData = StoryData.load_file(str(entry["data"]))["data"]
		var t1 := Time.get_ticks_usec()
		var assets := StoryAssets.load_art(sd.art)
		var t2 := Time.get_ticks_usec()
		var m := StoryMap.load_chapter(sd.id)
		var t3 := Time.get_ticks_usec()
		m.validate_chapter(sd.raw)
		var t4 := Time.get_ticks_usec()
		var people := StoryPeople.for_assets(assets)
		var t5 := Time.get_ticks_usec()
		var st := StoryStage.new()
		st.set_anchors_preset(Control.PRESET_FULL_RECT)
		st.visible = false
		add_child(st)
		var run := StoryRun.new()
		run.crowd = CrowdController.new()
		run.data = sd
		run.level = Level.new()
		run.crowd.setup(sd)
		var t6 := Time.get_ticks_usec()
		st.setup(assets, sd, run)
		var t7 := Time.get_ticks_usec()
		st.attach_world(st.map, true)
		var t8 := Time.get_ticks_usec()
		print("BUILD %-16s total %5.0f ms: data %4.0f art %4.0f map %4.0f validate %4.0f people(sheets) %4.0f crowd-ctl %4.0f stage.setup(rest) %4.0f world %4.0f" % [w, (t8 - t0) / 1000.0, (t1 - t0) / 1000.0, (t2 - t1) / 1000.0, (t3 - t2) / 1000.0,
			(t4 - t3) / 1000.0, (t5 - t4) / 1000.0, (t6 - t5) / 1000.0, (t7 - t6) / 1000.0, (t8 - t7) / 1000.0, ])
		print("   people loaded: %s" % [people != null and people.ok()])
	get_tree().quit()
