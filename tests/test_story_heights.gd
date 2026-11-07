extends TestCase
## Heights in the 2.5D renderer (docs/story/HEIGHTS_AND_PATHS.md), on a small map built from a Dictionary (tests/fixtures/story_heights_fixture.gd): step faces and lips at portals whose
## floors or ceilings differ (with the sector's step_tex / lip_tex), floor changes classed as steps, drops and voids, voids (marked or by depth) drawn as cliffs hazed toward the fog,
## never stood in, and railings: a see-through, non-occluding strip on a portal edge that nobody walks across.

const FX := preload("res://tests/fixtures/story_heights_fixture.gd")


func _map(changes: Dictionary = {}) -> StoryMap:
	var d: Dictionary = FX.data()
	d.merge(changes, true)
	return StoryMap.from_dict(d)


func _world(m: StoryMap) -> StoryWorld:
	var w := StoryWorld.new()
	w.build(m, null)
	return w


func _faces(w: StoryWorld, sector: String, kind: String, portal := "") -> Array:
	return w.faces.filter(func(f: Dictionary) -> bool: return f["sector"] == sector and f["kind"] == kind and (portal == "" or f["portal"] == portal))


func test_the_fixture_builds() -> void:
	var m := _map()
	assert_eq(m.errors, [], "the heights map builds")
	var w := _world(m)
	assert_eq(w.errors, [], "every tile loads")
	w.free()


func test_a_step_face_and_a_lip_at_a_portal() -> void:
	var w := _world(_map())
	var steps := _faces(w, "west", "step", "step")
	assert_eq(steps.size(), 1, "the walkway draws the riser up to the step")
	assert_near(float(steps[0]["y0"]), 0.0, 1e-6, "from the walkway floor")
	assert_near(float(steps[0]["y1"]), 0.3, 1e-6, "to the step's floor")
	assert_eq(steps[0]["tex"], "riser", "the higher sector's step_tex")
	var lips := _faces(w, "west", "lip", "step")
	assert_eq(lips.size(), 1, "the walkway draws the lip down to the step's lower ceiling")
	assert_near(float(lips[0]["y0"]), 3.5, 1e-6)
	assert_near(float(lips[0]["y1"]), 4.0, 1e-6)
	assert_eq(lips[0]["tex"], "lip", "the lower-ceilinged sector's lip_tex")
	assert_true(_faces(w, "step", "step", "west").is_empty(), "the higher side draws no riser")
	var high := _faces(w, "east", "step", "high")
	assert_eq(high.size(), 1, "the ledge's riser")
	assert_near(float(high[0]["y1"]) - float(high[0]["y0"]), 1.2, 1e-6)
	w.free()


func test_a_flat_portal_draws_nothing_and_a_wall_falls_back_to_wall_tex() -> void:
	var d: Dictionary = FX.data()
	for s in d["sectors"]:
		s.erase("step_tex")
		s.erase("lip_tex")
	var w := _world(StoryMap.from_dict(d))
	var steps := _faces(w, "west", "step", "step")
	assert_eq(steps[0]["tex"], "w", "with no step_tex the riser keeps the wall's texture, as before")
	assert_true(_faces(w, "bridge", "step", "east").is_empty() and _faces(w, "east", "step", "bridge").is_empty(), "a level portal has no face")
	w.free()


func test_floor_changes_are_steps_drops_and_voids() -> void:
	var m := _map()
	assert_eq(m.floor_change("west", "step")["kind"], "step", "0.3 m up")
	assert_eq(m.floor_change("step", "west")["kind"], "step", "0.3 m down")
	assert_eq(m.floor_change("step", "bridge")["kind"], "level")
	assert_eq(m.floor_change("east", "high")["kind"], "drop", "1.2 m is a drop for a walker")
	assert_eq(m.floor_change("east", "high", "climb")["kind"], "step", "and a step for a climb")
	assert_eq(m.floor_change("bridge", "pit_n")["kind"], "void", "nobody walks into a void")
	var marked := _map({"sectors": FX.data()["sectors"].map(func(s: Dictionary) -> Dictionary: return s.merged({"drop": true}) if s["id"] == "step" else s)})
	assert_eq(marked.floor_change("west", "step")["kind"], "drop", "a sector marked drop is never a step")
	var tall := _map({"max_step": 0.2})
	assert_eq(tall.floor_change("west", "step")["kind"], "drop", "max_step decides")


func test_voids_by_mark_and_by_depth_and_never_stood_in() -> void:
	var m := _map()
	assert_true(m.is_void("pit_n"), "marked")
	assert_true(m.is_void("pit_s"), "10 m below every neighbour with nobody in it")
	assert_true(bool(m.sector("pit_s").get("void_auto", false)))
	assert_near(float(m.sector("pit_n")["void_top"]), 0.3, 1e-6, "the haze starts at the lowest floor around it")
	assert_false(m.is_void("west") or m.is_void("bridge") or m.is_void("east"))
	var off := _map({"void_drop": 0.0})
	assert_false(off.is_void("pit_s"), "void_drop 0 turns the depth rule off")
	assert_true(off.is_void("pit_n"), "a marked void stays one")
	var d: Dictionary = FX.data()
	d["waypoints"].append({"id": "in_pit", "at": [2, 2.5], "yaw": 0, "sector": "pit_n"})
	var bad := StoryMap.from_dict(d)
	assert_true(" ".join(PackedStringArray(bad.errors)).contains("is a void"), "a waypoint in a marked void is an error: %s" % str(bad.errors))
	d = FX.data()
	d["waypoints"].append({"id": "in_pit_s", "at": [2, -2.5], "yaw": 0, "sector": "pit_s"})
	var room := StoryMap.from_dict(d)
	assert_eq(room.errors, [], "a deep sector someone stands in is a room, not a void (the Mothership's reactor)")
	assert_false(room.is_void("pit_s"))


func test_a_void_is_a_cliff_hazed_by_depth() -> void:
	var m := _map()
	var w := _world(m)
	var cliffs := _faces(w, "pit_n", "cliff")
	assert_true(cliffs.size() >= 3, "the pit draws cliffs under the step, the bridge and the far walkway (%d)" % cliffs.size())
	for f in cliffs:
		assert_near(float(f["y0"]), -10.0, 1e-6, "down to the void's floor")
		assert_near(float(f["y1"]), 0.3, 1e-6, "up to the walkway")
	var under_step := _faces(w, "pit_n", "cliff", "step")
	assert_eq(under_step[0]["tex"], "riser", "the neighbour's step_tex when it has one")
	var under_east := _faces(w, "pit_n", "cliff", "east")
	assert_eq(under_east[0]["tex"], "w", "else the neighbour's wall going on down")
	var top := w.haze_at(m.sector("pit_n"), 0.3)
	var mid := w.haze_at(m.sector("pit_n"), -5.0)
	var bottom := w.haze_at(m.sector("pit_n"), -10.0)
	assert_near(top, 0.0, 1e-6, "no haze at the walkway")
	assert_true(mid > 0.2 and mid < bottom, "deeper is hazier (%.2f, %.2f)" % [mid, bottom])
	assert_eq(w.haze_at(m.sector("bridge"), -5.0), 0.0, "only a void is hazed")
	var pit := (w.sector_node("pit_n").mesh as ArrayMesh)
	var darkest := 9.0
	var brightest := 0.0
	for k in pit.get_surface_count():
		for c in (pit.surface_get_arrays(k)[Mesh.ARRAY_COLOR] as PackedColorArray):
			darkest = minf(darkest, c.r + c.g + c.b)
			brightest = maxf(brightest, c.r + c.g + c.b)
	assert_true(darkest < 0.5 * brightest, "the bottom of the pit is dark and tinted (%.2f vs %.2f)" % [darkest, brightest])
	var hazed := w.haze_color(Color(1, 1, 1), 1.0)
	assert_true(hazed.r > hazed.g and hazed.r > hazed.b, "toward the map's crimson fog: %s" % hazed)
	w.free()


func test_railings_are_see_through_and_block_walking() -> void:
	var m := _map()
	var w := _world(m)
	var rails := w.faces.filter(func(f: Dictionary) -> bool: return f["kind"] == "railing")
	assert_eq(rails.size(), 2, "one railing per declared edge, drawn once")
	for f in rails:
		assert_eq(f["sector"], "bridge", "in the walkway's mesh (the higher side)")
		assert_near(float(f["y0"]), 0.3, 1e-6, "standing on the bridge")
		assert_near(float(f["y1"]), 1.3, 1e-6, "a metre high")
		assert_eq(f["tex"], "rail")
	var mesh := (w.sector_node("bridge").mesh as ArrayMesh)
	var found := false
	for k in mesh.get_surface_count():
		var mat := mesh.surface_get_material(k) as StandardMaterial3D
		if mat.albedo_texture == w._tex["rail"]:
			found = true
			assert_eq(mat.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR, "a cut-out, no blending")
			assert_eq(mat.texture_filter, BaseMaterial3D.TEXTURE_FILTER_NEAREST)
			assert_eq(mat.shading_mode, BaseMaterial3D.SHADING_MODE_UNSHADED)
			assert_eq(mat.cull_mode, BaseMaterial3D.CULL_DISABLED)
	assert_true(found, "the railing has its own cut-out surface")
	assert_false("pit_n" in m.neighbors("bridge"), "nobody walks across a railing")
	var vis := m.visible_sectors(Vector2(2, 0), 0.0, "bridge", 2.8)
	assert_true(vis.has("pit_s"), "the view goes over the railing into the pit: %s" % str(vis))
	assert_true(_faces(w, "bridge", "step").is_empty() and _faces(w, "bridge", "wall", "pit_n").is_empty(), "no wall is drawn under a railing on the walkway's side")
	var d: Dictionary = FX.data()
	d["walls"].append({"sector": "west", "from": [-10, -4], "to": [-10, 4], "kind": "railing", "tex": "rail"})
	assert_true(" ".join(PackedStringArray(StoryMap.from_dict(d).errors)).contains("railing"), "a railing needs a portal edge")
	w.free()


func test_flat_maps_are_unchanged_by_the_height_keys() -> void:
	for id in ["night_one", "mothership", "underworld", "bassment_mirrors", "bassment_stacks"]:
		var m := StoryMap.load_chapter(id)
		assert_eq(m.errors, [], id)
		for s in m.sectors:
			assert_false(bool(s.get("void", false)), "%s: %s is not a void (the depth rule is off for hand-made maps, and spares a room someone stands in)" % [id, s["id"]])
		assert_eq(m.vis_mode, "flood", "%s keeps the portal flood" % id)
