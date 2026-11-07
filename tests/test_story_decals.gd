extends TestCase
## Wall decals (docs/art/WALL_DECALS.md): a map thing of kind "decal" is a picture flat on a wall. In a small fixture room a decal on each of the four walls faces into
## the room, sits on the wall plane, keeps its metres, does not turn with the camera, takes `yaw` when given, takes the wall's light (shade, lamps, song-time light),
## is not a billboard, a person or a hotspot, and a decal far from every wall with no `yaw` is an error of the map.

const CC := preload("res://tools/art/camera_clearance_check.gd")
const BOARD := "res://assets/story/hospital/processed/prop_noticeboard.png"  # 141 x 102 texels


## A 6 x 4 m room (x 0..6, z 0..4) with a decal on each wall 0.07 m off it, one placed by yaw in the middle of the room, and an emissive one.
func _room(extra: Array = [], lamp := false) -> Dictionary:
	var things: Array = [
		{"id": "d_n", "kind": "decal", "sprite": "board", "at": [2.0, 0.07], "y": 1.2, "size": 0.8},
		{"id": "d_s", "kind": "decal", "sprite": "board", "at": [3.0, 3.93], "y": 1.2, "size": 0.8},
		{"id": "d_w", "kind": "decal", "sprite": "board", "at": [0.07, 2.0], "y": 1.2, "size": 0.8},
		{"id": "d_e", "kind": "decal", "sprite": "board", "at": [5.93, 1.5], "y": 0.0, "size": 2.0},
		{"id": "d_yaw", "kind": "decal", "sprite": "board", "at": [3.0, 2.0], "y": 1.0, "size": 0.5, "yaw": 90.0},
		{"id": "d_lit", "kind": "decal", "sprite": "board", "at": [4.5, 0.05], "y": 1.0, "size": 0.6, "emissive": true},
		{"id": "bb", "kind": "billboard", "sprite": "board", "at": [3.0, 1.0], "size": 0.8}]
	if lamp:
		things.append({"id": "lamp", "kind": "light", "at": [2.0, 0.6], "y": 1.6, "radius": 3.0, "color": "#ffc080", "strength": 1.2})
	things.append_array(extra)
	return {"id": "decals", "start": "a", "textures": {"w": BOARD, "board": BOARD},
		"sectors": [{"id": "room", "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]], "floor": 0, "ceiling": 3, "wall_tex": "w", "floor_tex": "w", "ceil_tex": "w", "light": 0.5, "tint": "#ffffff"}],
		"walls": [], "things": things, "waypoints": [{"id": "a", "at": [3, 2], "yaw": 0, "sector": "room"}], "homes": []}


func _world(d: Dictionary) -> StoryWorld:
	var m := StoryMap.from_dict(d, "decals")
	assert_eq(m.errors, [], "the fixture map builds")
	var w := StoryWorld.new()
	w.build(m, null)
	assert_eq(w.errors, [], "the fixture world builds")
	return w


func _normal_of(mi: MeshInstance3D) -> Vector2:
	var z := mi.transform.basis.z  # (its sector node and the world sit at the origin)
	return Vector2(z.x, z.z).normalized()


func test_a_decal_on_each_wall_faces_into_the_room_and_lies_on_it() -> void:
	var w := _world(_room())
	(Engine.get_main_loop() as SceneTree).root.add_child(w)
	var want := {"d_n": [Vector2(0, 1), "z", 0.0], "d_s": [Vector2(0, -1), "z", 4.0], "d_w": [Vector2(1, 0), "x", 0.0], "d_e": [Vector2(-1, 0), "x", 6.0]}
	for id in want:
		var mi := w.decal_node(id)
		assert_true(mi != null, "%s is drawn" % id)
		if mi == null:
			continue
		var n := _normal_of(mi)
		assert_true(rad_to_deg(n.angle_to(want[id][0])) < 1.0, "%s faces into the room: %s" % [id, n])
		var o := mi.global_position
		var off := absf((o.z if want[id][1] == "z" else o.x) - float(want[id][2]))
		assert_true(off > 0.0005 and off < 0.02, "%s stands %.4f m off its wall (on it, not in it)" % [id, off])
		var aabb := mi.get_aabb()
		var tex_aspect := 141.0 / 102.0
		var h := 2.0 if id == "d_e" else 0.8
		assert_near(aabb.size.y, h, 0.001, "%s keeps its height in metres" % id)
		assert_near(aabb.size.x, h * tex_aspect, 0.002, "%s keeps the sprite's aspect" % id)
		assert_near(aabb.size.z, 0.0, 1.0e-5, "%s is flat" % id)
		assert_near(o.y, 0.0 if id == "d_e" else 1.2, 1.0e-4, "%s: `y` is its bottom edge above the floor" % id)
		var mat := (mi.mesh as ArrayMesh).surface_get_material(0) as StandardMaterial3D
		assert_eq(mat.billboard_mode, BaseMaterial3D.BILLBOARD_DISABLED, "%s never turns to the camera" % id)
		assert_eq(mat.texture_filter, BaseMaterial3D.TEXTURE_FILTER_NEAREST, "%s is nearest-filtered" % id)
		assert_eq(mat.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR, "%s has hard alpha (the opaque pass, as the walls)" % id)
		assert_eq(mat.shading_mode, BaseMaterial3D.SHADING_MODE_UNSHADED)
	# the doors foot: `at` is dropped onto the wall, so a decal sits where the map says along it
	assert_near(w.decal_node("d_n").global_position.x, 2.0, 1.0e-4, "the decal's centre stays at its `at` along the wall")
	# the camera moves; the decals do not turn
	var cam := Camera3D.new()
	w.add_child(cam)
	cam.current = true
	cam.global_position = Vector3(1, 1.6, 3)
	cam.look_at(Vector3(5, 1.2, 0))
	var before := {}
	for id in want:
		before[id] = w.decal_node(id).global_transform.basis
	cam.global_position = Vector3(5, 1.6, 1)
	cam.look_at(Vector3(0, 1.2, 3))
	for id in want:
		assert_true((w.decal_node(id).global_transform.basis as Basis).is_equal_approx(before[id]), "%s keeps its basis when the camera moves" % id)
	w.queue_free()


func test_yaw_overrides_the_wall_and_a_decal_far_from_a_wall_without_yaw_fails() -> void:
	var w := _world(_room())
	var mi := w.decal_node("d_yaw")
	var n := _normal_of(mi)
	assert_true(rad_to_deg(n.angle_to(Vector2(-1, 0))) < 1.0, "yaw 90 looks toward -x (forward_of_yaw): %s" % n)
	assert_near(mi.position.x, 3.0 - StoryWorld.DECAL_GAP, 1.0e-4, "a yaw decal stands at its `at`")
	w.free()
	var m := StoryMap.from_dict(_room([{"id": "d_far", "kind": "decal", "sprite": "board", "at": [3.0, 2.5], "y": 1.0, "size": 0.5}]), "decals")
	assert_true(" ".join(PackedStringArray(m.errors)).contains("decal d_far: no solid wall"), "a decal in the middle of the room with no yaw is an error: %s" % [m.errors])
	var m2 := StoryMap.from_dict(_room([{"id": "d_near", "kind": "decal", "sprite": "board", "at": [3.0, 0.3], "size": 0.5}]), "decals")
	assert_eq(m2.errors, [], "0.3 m from a wall is close enough")
	var m3 := StoryMap.from_dict(_room([{"id": "d_n", "kind": "decal", "sprite": "board", "at": [1.0, 0.07]}]), "decals")
	assert_true(" ".join(PackedStringArray(m3.errors)).contains("duplicated"), "decal ids share the things' id space")


func test_decals_are_scenery_not_billboards_people_or_hotspots() -> void:
	var w := _world(_room())
	assert_eq(w.thing_count(), 1, "only the billboard is a thing node")
	assert_eq(w.decal_count(), 6, "six decals")
	for th in w._thing_nodes:
		assert_eq(str(th["thing"]["id"]), "bb", "no decal in the billboard list (hotspot widths, the coverage audit)")
	assert_eq(w.map.things.size(), 1, "no decal in map.things (hotspot anchors, crowd targets, heralds)")
	assert_eq(w.map.decals.size(), 6)
	assert_eq(HotspotView.resolve({"thing": "d_n"}, w.map, {}).get("ok", false), false, "a decal is no hotspot anchor")
	assert_eq(w.shadow_count, 1, "a contact shadow under the billboard only")
	w.free()


func test_a_decal_takes_the_light_of_the_wall_behind_it() -> void:
	# unlit room: the wall's flat shade (x-facing walls are darker), song-time light through the sector's materials
	var w := _world(_room())
	var cols := ((w.decal_node("d_w").mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_COLOR] as PackedColorArray)
	assert_near(cols[0].r, StoryWorld.WALL_SHADE_X, 0.005, "a decal on an x-facing wall has its shade")
	cols = ((w.decal_node("d_n").mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_COLOR] as PackedColorArray)
	assert_near(cols[0].r, 1.0, 0.005, "a decal on a z-facing wall has its shade")
	w.update(1.3, {"bpm": 120.0})
	var wall_mat := (w.sector_node("room").mesh as ArrayMesh).surface_get_material(0) as StandardMaterial3D
	var dmat := (w.decal_node("d_n").mesh as ArrayMesh).surface_get_material(0) as StandardMaterial3D
	assert_true(dmat.albedo_color.is_equal_approx(wall_mat.albedo_color), "the song-time light of the room multiplies the decal as it does the wall")
	assert_false(dmat.albedo_color.is_equal_approx(Color.WHITE), "(and it is not white)")
	var emi := ((w.decal_node("d_lit").mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_COLOR] as PackedColorArray)
	assert_true(emi[0].is_equal_approx(Color.WHITE), "an emissive decal keeps its own colours")
	w.free()
	# a lamp near the north wall: the decal there is lit as the wall is at the same points, and brighter than one away from the lamp
	var wl := _world(_room([], true))
	var mi := wl.decal_node("d_n")
	var arr := (mi.mesh as ArrayMesh).surface_get_arrays(0)
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var lc: PackedColorArray = arr[Mesh.ARRAY_COLOR]
	assert_true(verts.size() > 4, "a lit decal is cut on the wall's light cells (%d vertices)" % verts.size())
	var s := wl.map.sector("room")
	var lit := wl.map.lights_reaching("room")
	var worst := 0.0
	for i in verts.size():
		var p := mi.transform * verts[i]
		var on_wall := Vector3(p.x, p.y, 0.0)
		var exact := wl._vertex_light(on_wall, 1.0, s, lit)
		worst = maxf(worst, absf(lc[i].r - exact.r) + absf(lc[i].g - exact.g) + absf(lc[i].b - exact.b))
	assert_true(worst < 0.12, "the decal's light follows the wall's baked light (largest difference %.3f, the wall's own cell interpolation)" % worst)
	var far_cols := ((wl.decal_node("d_s").mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_COLOR] as PackedColorArray)
	assert_true(lc[0].r > far_cols[0].r + 0.05, "the lamp lights the near decal more than the far one (%.2f vs %.2f)" % [lc[0].r, far_cols[0].r])
	wl.free()


func test_a_decal_does_not_change_what_the_camera_check_sees() -> void:
	var with_d := StoryMap.from_dict(_room(), "decals")
	var d0 := _room()
	d0["things"] = (d0["things"] as Array).filter(func(t: Dictionary) -> bool: return str(t["kind"]) != "decal")
	var without := StoryMap.from_dict(d0, "decals")
	for yaw in [0.0, 90.0, 180.0, 270.0]:
		var pose := {"cam": Vector3(3, 1.6, 2), "yaw": yaw, "pitch": 0.0, "sector": "room"}
		var a: Dictionary = CC.clearance(with_d, pose)
		var b: Dictionary = CC.clearance(without, pose)
		assert_near(float(a["centre"]), float(b["centre"]), 1.0e-6, "yaw %d: the same wall distance" % yaw)
		assert_near(float(a["share"]), float(b["share"]), 1.0e-6, "yaw %d: the same share" % yaw)
