extends Node
## The rain shot sheet (package A9, hook H10, docs/engine/WEATHER.md): the Dock map (content/story/maps/doom_dock.json, or RW_WEATHER_MAP=<file>) with weather rain 0, 0.5 and 1
## in the real run screen at 16:9 (1280 x 720: the 460 px stage strip, the pads, the note lane and the HUD of run_play.tscn around it). The run's own stage is hidden and a stage
## showing the Dock is put in its place (the run's crowd is Night One's and is not shown: the sheet is about the weather). The shot adds eave drips the Dock does not author.
## Also prints the cost: weather.update CPU time, draw calls and primitives of the low-res viewport, and its GPU time on this machine, rain 0 against rain 1.
##   RW_RUN_VIRTUAL=1 RW_WEATHER_MAP=<doom_dock.json> bash tools/dev/godot.sh --resolution 1280x720 --path . -s tools/engine/shoot_weather.gd
## Writes docs/shots/engine/weather/rain_sheet.jpg.

const OUT := "res://docs/shots/engine/weather/"
const RAINS := [0.0, 0.5, 1.0]
const CAM := "dk_ref"
const T := 12.0
const SCALE := 0.6
const DRIPS := [{"at": [4.15, -1.2], "h": 3.2}, {"at": [4.15, -3.3], "h": 3.2}, {"at": [-4.1, -7.0], "h": 2.6}, {"at": [-4.1, -8.6], "h": 2.6}]

var _shots: Array = []


func _ready() -> void:
	_run.call_deferred()


func _map_dict(rain: float) -> Dictionary:
	var path := OS.get_environment("RW_WEATHER_MAP") if OS.has_environment("RW_WEATHER_MAP") else ProjectSettings.globalize_path("res://content/story/maps/doom_dock.json")
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(d) != TYPE_DICTIONARY:
		push_error("no map at " + path)
		return {}
	var m: Dictionary = d
	m["weather"] = {"rain": rain, "wind": 8.0, "drips": DRIPS}
	return m


func _run() -> void:
	var tree := get_tree()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var play: Node = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	tree.root.add_child(play)
	for i in 90:
		await tree.process_frame
	var host: Control = play.get("_stage_host")
	for c in host.get_children():
		(c as CanvasItem).visible = false
	for r: float in RAINS:
		var md := _map_dict(r)
		if md.is_empty():
			tree.quit(1)
			return
		OS.set_environment("RW_STORY_CAM", CAM)
		var run := StoryRun.create({})
		var stage := StoryStage.new()
		stage.set_anchors_preset(Control.PRESET_FULL_RECT)
		host.add_child(stage)
		stage.setup(StoryAssets.load_default(), run.data, run)
		var m := StoryMap.from_dict(md, "doom_dock")
		m.art = str(md.get("art", "doom_dock"))
		if not m.errors.is_empty():
			print("map errors: ", m.errors)
		stage.attach_world(m, true)
		stage._overlay.visible = false  # (Night One's crowd does not belong in the Dock)
		var w := stage.weather
		RenderingServer.viewport_set_measure_render_time(stage.lowres.sub.get_viewport_rid(), true)
		for i in 8:
			stage.update(T, 50.0)
			await tree.process_frame
		await RenderingServer.frame_post_draw
		var img := tree.root.get_viewport().get_texture().get_image()
		var rid := stage.lowres.sub.get_viewport_rid()
		var calls := RenderingServer.viewport_get_render_info(rid, RenderingServer.VIEWPORT_RENDER_INFO_TYPE_VISIBLE, RenderingServer.VIEWPORT_RENDER_INFO_DRAW_CALLS_IN_FRAME)
		var prims := RenderingServer.viewport_get_render_info(rid, RenderingServer.VIEWPORT_RENDER_INFO_TYPE_VISIBLE, RenderingServer.VIEWPORT_RENDER_INFO_PRIMITIVES_IN_FRAME)
		var gpu := 0.0
		for i in 30:  # the low-res viewport's GPU time, averaged (this machine's GPU, not a phone's)
			stage.update(T + float(i) / 60.0, 50.0)
			await tree.process_frame
			gpu += RenderingServer.viewport_get_measured_render_time_gpu(rid)
		var cpu := 0
		if w != null:
			var t0 := Time.get_ticks_usec()
			for i in 200:
				w.update(T + float(i) / 60.0, stage.lowres.camera, Color.WHITE, stage._vis_geo)
			cpu = Time.get_ticks_usec() - t0
		print("rain %.1f: streaks %d, drips %d, gloss bands %d, weather draw calls %d | low-res viewport %s: draw calls %d, primitives %d, GPU %.3f ms | weather.update %.1f us" % [
			r, w.rain_mm.multimesh.instance_count if w != null else 0, w.drip_mm.multimesh.instance_count if w != null else 0, w.gloss_shown if w != null else 0,
			w.draw_calls() if w != null else 0, str(stage.lowres.sub.size), calls, prims, gpu / 30.0, float(cpu) / 200.0])
		_shots.append(["rain %.1f" % r, img])
		stage.queue_free()
		await tree.process_frame
	OS.set_environment("RW_STORY_CAM", "")
	_sheet()
	tree.quit(0)


func _sheet() -> void:
	if OS.has_environment("RW_WEATHER_FULL"):  # the full-size frames, for a close look (RW_WEATHER_FULL=<folder>; not committed)
		for s in _shots:
			(s[1] as Image).save_png(OS.get_environment("RW_WEATHER_FULL").path_join(str(s[0]).replace(" ", "_") + ".png"))
	var w := 0
	var h := 0
	for s in _shots:
		var img: Image = s[1]
		w = maxi(w, int(img.get_width() * SCALE))
		h += int(img.get_height() * SCALE) + 4
	var sheet := Image.create(w, h, false, Image.FORMAT_RGB8)
	sheet.fill(Color(0.05, 0.05, 0.08))
	var y := 0
	for s in _shots:
		var img: Image = s[1]
		img.convert(Image.FORMAT_RGB8)
		img.resize(int(img.get_width() * SCALE), int(img.get_height() * SCALE), Image.INTERPOLATE_BILINEAR)
		sheet.blit_rect(img, Rect2i(Vector2i.ZERO, img.get_size()), Vector2i(0, y))
		y += img.get_height() + 4
	var path := ProjectSettings.globalize_path(OUT + "rain_sheet.jpg")
	sheet.save_jpg(path, 0.88)
	print("sheet ", path)
