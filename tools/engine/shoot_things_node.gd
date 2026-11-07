extends Node
## Shots of world-staged things (CONTRACTS.md 10, package A8): the Warehouse bar (night_one) from the `bar` waypoint with two dynamic things (a crate on the floor of the bar,
## a glass at counter height) and the barman b01 directed to raise_glass, a glow feedback on the crate, at 16:9 (a 1280 x 460 stage strip) and 20:9 (1600 x 460), at three
## moments (frames change, the glass slides). Needs a renderer (not --headless):
##   bash tools/dev/godot.sh --path . -s tools/engine/shoot_things.gd   (that script loads this node once the autoloads are up)
## Writes docs/shots/engine/things/things_sheet.png (one sheet) and prints each thing's stage rect.

const OUT := "res://docs/shots/engine/things/"
const SIZES := {"16x9": Vector2i(1280, 460), "20x9": Vector2i(1600, 460)}
const MOMENTS := [4.0, 6.0, 8.0]  # song seconds
const CAM := "@7.3:3.1:-90:-4"  # just inside the bar's door, facing the counter and the shelves (x 7.3, z 3.1, yaw -90: toward +x, 4 degrees down)
const SCALE := 0.4  # the sheet's scale (one sheet under 1 MB)

var _shots: Array = []  # [label, Image]


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var root := get_tree().root
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for key: String in SIZES:
		var sz: Vector2i = SIZES[key]
		var vp := SubViewport.new()
		vp.size = sz
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(vp)
		OS.set_environment("RW_STORY_CAM", CAM)  # (a still camera at the bar: the rail would otherwise stroll)
		var run := StoryRun.create({})
		var stage := StoryStage.new()
		stage.size = Vector2(sz)
		vp.add_child(stage)
		stage.setup(StoryAssets.load_default(), run.data, run)
		stage.attach_world(stage.map, true)
		stage.lowres.size = Vector2(sz)
		stage.lowres._fit()
		stage.player.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": "bar", "bars": 0.01, "cut": true}})
		stage.apply({"t0": 0.0, "bar": 1.0, "action": "lights_warm", "args": {}, "block": "", "source": "block"})
		var res := stage.people("b01", "raise_glass", 0.0, 0.0)
		print("b01 raise_glass plays ", res)
		var fb := RunActivityFeedback.new()
		fb.beat_s = 60.0 / 174.0
		var now := [0.0]
		fb.now_fn = func() -> float: return now[0]
		fb.point_fn = func(id: String) -> Variant: return stage.world.thing_screen_point(id)
		fb.size_fn = func(id: String) -> float:
			var r: Variant = stage.world.thing_screen_rect(id)
			return (r as Rect2).size.y if r != null else 0.0
		stage.lowres.add_overlay(fb, "Feedback").layer = 4
		for k in MOMENTS.size():
			var t: float = MOMENTS[k]
			var slide := float(k) / float(MOMENTS.size() - 1)
			stage.set_things([
				{"id": "crate", "sprite": "engine_test_crate", "at": [10.6, 4.0], "sector": "bar", "size": [0.6, 0.6], "frame": k % 4},
				{"id": "glass", "sprite": "engine_test_glass", "at": [10.4, lerpf(2.2, 3.0, slide)], "sector": "bar", "size": [0.2, 0.3], "frame": k % 3, "y": 1.05, "anchor": "center"},
			])
			fb.entries = [{"thing": "crate", "kind": "glow", "t": t - 0.25}, {"thing": "glass", "kind": "tick", "t": t - 0.1}]
			now[0] = t
			for i in 4:
				stage.update(t, 60.0)
				await get_tree().process_frame
			await RenderingServer.frame_post_draw
			var img := vp.get_texture().get_image()
			for id in ["crate", "glass"]:
				print("%s t=%.1f %s rect %s" % [key, t, id, str(stage.thing_screen_rect(id))])
			_shots.append(["%s t=%.0fs" % [key, t], img])
		vp.queue_free()
	OS.set_environment("RW_STORY_CAM", "")
	_sheet()
	get_tree().quit(0)


func _sheet() -> void:
	var w := 0
	var h := 0
	for row in SIZES.size():
		var rw := 0
		var rh := 0
		for k in MOMENTS.size():
			var img: Image = _shots[row * MOMENTS.size() + k][1]
			rw += int(img.get_width() * SCALE) + 4
			rh = maxi(rh, int(img.get_height() * SCALE))
		w = maxi(w, rw)
		h += rh + 4
	var sheet := Image.create(w, h, false, Image.FORMAT_RGB8)
	sheet.fill(Color(0.05, 0.05, 0.08))
	var y := 0
	for row in SIZES.size():
		var x := 0
		var rh := 0
		for k in MOMENTS.size():
			var img: Image = _shots[row * MOMENTS.size() + k][1]
			img.convert(Image.FORMAT_RGB8)
			img.resize(int(img.get_width() * SCALE), int(img.get_height() * SCALE), Image.INTERPOLATE_BILINEAR)
			sheet.blit_rect(img, Rect2i(Vector2i.ZERO, img.get_size()), Vector2i(x, y))
			x += img.get_width() + 4
			rh = maxi(rh, img.get_height())
		y += rh + 4
	var path := ProjectSettings.globalize_path(OUT + "things_sheet.png")
	sheet.save_png(path)
	print("sheet ", path, " ", FileAccess.get_file_as_bytes(OUT + "things_sheet.png").size(), " bytes")
