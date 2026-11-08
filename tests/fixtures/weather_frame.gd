extends RefCounted
## One low-res frame of a stage (package A9, weather): the Night One stage at a fixed camera and song time, the low-res viewport's own image (before the stretch to the
## stage strip). Used by tests/fixtures/weather_baseline.gd (writes the baseline, run once before the weather code existed) and tests/test_weather.gd (compares a map
## without `weather` against it). Needs a renderer: under --headless the image is empty and the caller skips.

const BASELINE := "res://tests/fixtures/weather/night_one_frame.png"
const CAM := "floor_edge"
const T := 6.0
const SIZE := Vector2i(1280, 460)


## The frame as an Image (null when nothing was drawn). `map_dict`: a map to attach instead of the chapter's own (a dictionary, StoryMap.from_dict, art night_one).
static func shoot(tree: SceneTree, map_dict: Dictionary = {}) -> Image:
	OS.set_environment("RW_STORY_CAM", CAM)
	OS.set_environment("RW_STORY_DITHER", "0")
	var vp := SubViewport.new()
	vp.size = SIZE
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	tree.root.add_child(vp)
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(SIZE)
	vp.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	var m: StoryMap = stage.map
	if not map_dict.is_empty():
		m = StoryMap.from_dict(map_dict, "night_one")
	stage.attach_world(m, true)
	stage.lowres.size = Vector2(SIZE)
	stage.lowres._fit()
	for i in 4:
		stage.update(T, 50.0)
		await tree.process_frame
	await RenderingServer.frame_post_draw
	var img: Image = stage.lowres.sub.get_texture().get_image()
	vp.queue_free()
	OS.set_environment("RW_STORY_CAM", "")
	OS.unset_environment("RW_STORY_DITHER")
	if img == null or img.is_empty():
		return null
	img.convert(Image.FORMAT_RGB8)
	return img
