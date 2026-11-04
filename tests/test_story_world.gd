extends TestCase
## StoryWorld (built headless from the Night One map) and the light as a function of song time.


func _build_world() -> StoryWorld:
	var map := StoryMap.load_chapter("night_one")
	var assets := StoryAssets.load_default()
	var w := StoryWorld.new()
	w.build(map, assets)
	return w


func test_world_builds_every_sector_wall_and_thing() -> void:
	var w := _build_world()
	assert_true(w.errors.is_empty(), str(w.errors))
	for s in w.map.sectors:
		var mi := w.sector_node(str(s["id"]))
		assert_true(mi != null and (mi.mesh as ArrayMesh).get_surface_count() >= 1, "sector %s has geometry" % s["id"])
	assert_eq(w.thing_count(), w.map.things.size(), "every billboard thing has a node")
	assert_true(w.triangle_count > 150 and w.triangle_count < 4000, "a Doom-sized scene: %d triangles" % w.triangle_count)
	assert_true(w.env.fog_enabled)
	# the stage riser is higher than the floor: a lower step wall exists on the floor side only
	var floor_mesh := (w.sector_node("floor").mesh as ArrayMesh)
	var aabb := floor_mesh.get_aabb()
	assert_near(aabb.size.y, 3.6, 0.2, "the dance floor is 3.6 m high")
	w.free()


func test_surfaces_are_unshaded_nearest_and_double_sided() -> void:
	var w := _build_world()
	var mi := w.sector_node("floor")
	var mesh := mi.mesh as ArrayMesh
	for k in mesh.get_surface_count():
		var m := mesh.surface_get_material(k) as StandardMaterial3D
		assert_eq(m.shading_mode, BaseMaterial3D.SHADING_MODE_UNSHADED)
		assert_eq(m.texture_filter, BaseMaterial3D.TEXTURE_FILTER_NEAREST)
		assert_true(m.albedo_texture != null)
	w.free()


func test_light_is_a_function_of_song_time_and_pulses_on_the_beat() -> void:
	var map := StoryMap.load_chapter("night_one")
	var floor_sec := map.sector("floor")
	var ctx := {"bpm": 174.0, "palette": [Color(1, 0, 0), Color(0, 1, 0)], "energy": 60.0}
	var beat := 60.0 / 174.0
	var on := StoryWorld.light_of(floor_sec, 8.0 * beat, ctx)
	var off := StoryWorld.light_of(floor_sec, 8.5 * beat, ctx)
	assert_true(on.get_luminance() > off.get_luminance(), "brighter on the kick than between kicks")
	assert_eq(StoryWorld.light_of(floor_sec, 3.3, ctx), StoryWorld.light_of(floor_sec, 3.3, ctx), "the same time gives the same colour")
	var quiet := StoryWorld.light_of(floor_sec, 3.3, {"bpm": 174.0, "palette": ctx["palette"], "energy": 5.0})
	var loud := StoryWorld.light_of(floor_sec, 3.3, {"bpm": 174.0, "palette": ctx["palette"], "energy": 95.0})
	assert_true(loud.get_luminance() > quiet.get_luminance(), "a hotter crowd lights the floor more")
	var cold := StoryWorld.light_of(map.sector("corridor"), 3.3, ctx)
	assert_true(cold.b > cold.r, "the toilet corridor keeps its own cold tint, not the stage palette")
	var flick := StoryWorld.light_of(floor_sec, 0.01, {"bpm": 174.0, "palette": ctx["palette"], "energy": 60.0, "flicker": true})
	assert_true(flick.get_luminance() < StoryWorld.light_of(floor_sec, 0.01, ctx).get_luminance() + 0.001)
	var white := StoryWorld.light_of(floor_sec, 3.3, {"bpm": 174.0, "palette": [], "energy": 60.0, "strobe": 1.0})
	assert_true(white.r >= 1.9, "a full strobe whites the sector out")


func test_world_update_writes_the_sector_colours_each_frame() -> void:
	var w := _build_world()
	w.update(1.0, {"bpm": 174.0, "palette": [Color(1, 0.2, 0.2)], "energy": 80.0})
	var m := (w.sector_node("floor").mesh as ArrayMesh).surface_get_material(0) as StandardMaterial3D
	var c1 := m.albedo_color
	w.update(1.0 + 0.5 * 60.0 / 174.0, {"bpm": 174.0, "palette": [Color(1, 0.2, 0.2)], "energy": 80.0})
	assert_true(m.albedo_color != c1, "the light moved with the beat")
	w.update(1.0, {"bpm": 174.0, "palette": [Color(1, 0.2, 0.2)], "energy": 80.0})
	assert_eq(m.albedo_color, c1, "and returns exactly at the same time (pause and restart replay)")
	w.free()
