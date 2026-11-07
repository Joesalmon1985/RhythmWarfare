extends TestCase
## The bedsit opening (docs/briefs/BEDSIT_RAVES_BRIEF.md section 2, CONTRACTS.md contracts 1, 2, 6): the four world regions as pure functions (BedsitNav), the path content/paths/bedsit
## (relaxed node, hold_bars, forward routes to the rave of each facing, placeholders that resolve to the bedsit) and the room's map (one coherent room, four viewpoints, clearance).

const CC := preload("res://tools/art/camera_clearance_check.gd")
const TRACK := "origin_unknown_valley_of_the_shadows_chase_status_remix"
const RAVES := {"N": "space_rave", "E": "dino_rave", "S": "magic_rave", "W": "transport_rave"}
const THEMES := {"N": "space", "E": "dinos", "S": "magic", "W": "transport"}


func _press(save: Dictionary, region: String) -> Dictionary:
	return BedsitNav.press(save, region)


# --- turning

func test_four_left_turns_return_to_north() -> void:
	var save := {}
	var facings: Array = []
	for i in 4:
		var r := _press(save, "left")
		facings.append(r["facing_after"])
		assert_eq(r["action"], "turn")
	assert_eq(facings, ["W", "S", "E", "N"], "left from north goes west, south, east, north")
	assert_eq(BedsitNav.facing_of(save), "N", "four left turns return to north")


func test_four_right_turns_return_to_north() -> void:
	var save := {}
	var facings: Array = []
	for i in 4:
		facings.append(_press(save, "right")["facing_after"])
	assert_eq(facings, ["E", "S", "W", "N"], "right from north goes east, south, west, north")
	assert_eq(save["bedsit_facing"], "N")


func test_bottom_keeps_the_facing_from_every_facing() -> void:
	for start in RaveSave.FACINGS:
		var save := {"bedsit_facing": start}
		var r := _press(save, "bottom")
		assert_eq(r["action"], "stay")
		assert_eq(r["facing_after"], start, "bottom keeps %s" % start)
		assert_eq(BedsitNav.facing_of(save), start)
		assert_near(float(r["yaw_to"]), float(r["yaw_from"]), 0.0001, "the camera does not move")
		assert_eq(float(r["turn_bars"]), 0.0)


func test_a_turn_turns_the_camera_ninety_degrees_over_one_bar() -> void:
	var left := _press({}, "left")
	assert_near(float(left["yaw_to"]) - float(left["yaw_from"]), 90.0, 0.0001, "a left turn adds 90 degrees (a positive yaw turns left)")
	assert_eq(float(left["turn_bars"]), 1.0, "over one bar")
	var right := _press({}, "right")
	assert_near(float(right["yaw_to"]) - float(right["yaw_from"]), -90.0, 0.0001)
	var yaw := 0.0
	for i in 4:
		yaw = BedsitNav.turned_yaw(yaw, -1)
	assert_near(yaw, 360.0, 0.0001, "four left turns are a whole circle")
	var m := StoryMap.load_chapter("bedsit", false)
	for f in RaveSave.FACINGS:  # the waypoints' own yaws are the facings' yaws (mod 360)
		var wp := m.waypoint("bedsit_" + str(f).to_lower())
		assert_near(fposmod(float(wp["yaw"]) - BedsitNav.yaw_of(f), 360.0), 0.0, 0.0001, "bedsit_%s yaw" % str(f).to_lower())


# --- leaving

func test_each_facings_forward_route_is_the_right_rave() -> void:
	for f in RAVES:
		var save := {"bedsit_facing": f}
		var r := _press(save, "top")
		assert_true(bool(r["leave"]), "top leaves")
		assert_eq(r["route"], RAVES[f], "facing %s leaves for %s" % [f, RAVES[f]])
		assert_eq(r["theme"], THEMES[f], "facing %s is %s" % [f, THEMES[f]])
		assert_eq(BedsitNav.facing_of(save), f, "leaving does not turn")
	# the same answer from the data the path's node carries, its routes and the hotspots the engine draws today
	var d := RunData.load_path("bedsit")
	var node: Dictionary = d.nodes["bedsit"]
	var spots: Dictionary = {}
	for h in (d.hotspots["bedsit"] as Array):
		spots[str(h["id"])] = h
	for f in RAVES:
		var low := str(f).to_lower()
		assert_eq(((node["bedsit"]["facings"] as Dictionary)[f] as Dictionary)["route"], RAVES[f], "node data, facing %s" % f)
		var edge := {}
		for e in node["next"]:
			if str(e["dir"]) == low:
				edge = e
		assert_eq(edge.get("to", ""), RAVES[f], "run.json next, facing %s" % f)
		assert_true(spots.has("bedsit.threshold_" + low), "a threshold hotspot for %s" % f)
		if spots.has("bedsit.threshold_" + low):
			assert_eq((spots["bedsit.threshold_" + low]["on_success"] as Dictionary)["route"], RAVES[f], "hotspot, facing %s" % f)


func test_the_themes_data_keeps_the_fixed_mapping() -> void:
	var t := BedsitNav.themes()
	assert_eq(ContractShapes.bedsit_themes(t), [], "content/bedsit/themes.json fits its shape")
	for f in THEMES:
		assert_eq(RaveSave.theme_of(f, t), THEMES[f])
	assert_eq(t["start_facing"], "N")
	assert_eq(t["facing_waypoints"], {"N": "bedsit_n", "E": "bedsit_e", "S": "bedsit_s", "W": "bedsit_w"})


func test_the_regions_are_not_the_pads() -> void:
	assert_eq(BedsitNav.region_action("left"), {"action": "turn", "dir": -1})
	assert_eq(BedsitNav.region_action("right"), {"action": "turn", "dir": 1})
	assert_eq(BedsitNav.region_action("bottom"), {"action": "stay", "dir": 0})
	assert_eq(BedsitNav.region_action("top"), {"action": "leave", "dir": 0})
	for pad in ["d", "f", "j", "k", "pad_1"]:
		assert_eq(BedsitNav.region_action(pad)["action"], "none", "a pad name is not a region")
	var node: Dictionary = RunData.load_path("bedsit").nodes["bedsit"]
	assert_eq((node["bedsit"]["regions"] as Dictionary).keys().size(), 4)


# --- the path

func test_the_path_loads_clean_and_the_bedsit_node_is_relaxed() -> void:
	var d := RunData.load_path("bedsit")
	assert_eq(d.errors, [], "the bedsit path validates")
	assert_eq(d.path_id, "bedsit")
	var n: Dictionary = d.nodes["bedsit"]
	assert_true(bool(n.get("relaxed", false)), "the bedsit node is relaxed in the data (H1.7, not yet read by the engine)")
	assert_true(bool(n["entry"]) and d.start_node() == "bedsit")
	var vp: Dictionary = n["bedsit"]["viewpoint"]
	assert_true(bool(vp["choice_view"]), "the viewpoint is a choice view")
	assert_true(int(vp["hold_bars"]) >= 4, "hold_bars: the whole choice window, one block (H3.1)")
	assert_eq(int(d.cfg["timing"]["bpm"]), 174)
	assert_eq(n["map"], "bedsit")


func test_the_raves_are_placeholders_that_end_the_path() -> void:
	var d := RunData.load_path("bedsit")
	var routes := BedsitNav.routes()
	assert_true(bool(routes["placeholder"]["active"]), "the placeholder flag is on until the raves land")
	for f in RAVES:
		var id: String = RAVES[f]
		assert_true(d.nodes.has(id), "%s exists as a placeholder node" % id)
		var n: Dictionary = d.nodes[id]
		assert_true(bool(n.get("placeholder", false)), "%s is marked placeholder" % id)
		assert_eq((n["next"] as Array).size(), 1, "one route")
		assert_eq(n["next"][0]["to"], "run:warehouse", "%s is a one-scene ending that returns to the Warehouse" % id)
		assert_true(str(n["ending"]) != "", "%s is an ending" % id)
		assert_eq(n["waypoint"], "bedsit_" + str(f).to_lower(), "and comes home facing %s" % f)


func test_the_flag_is_off_by_default_and_the_legacy_run_is_untouched() -> void:
	if OS.get_environment(BedsitNav.FLAG) == "":
		assert_false(BedsitNav.enabled(), "RW_BEDSIT unset: off")
	var main := RunData.load_default()
	assert_false(main.nodes.has("bedsit"), "the main run has no bedsit node")
	assert_false(main.nodes.has("space_rave"))
	assert_true(RunData.path_exists("bedsit"), "the path exists for RW_RUN_PATH=bedsit")


func test_the_track_is_the_chase_and_status_remix() -> void:
	var ts: Dictionary = BedsitNav.load_json("res://content/run/track_scenes.json")
	assert_eq(ts["paths"]["bedsit"]["bedsit"]["track"], TRACK)
	assert_true(FileAccess.file_exists("res://content/music/tracks/%s.json" % TRACK), "the track is in the catalogue")
	var mus := BedsitNav.load_json("res://content/paths/bedsit/music.json")
	assert_eq(mus["nodes"][0]["audio"], "bedsit_room", "the placeholder pack stands in when the track pack is not on the machine")


func test_the_save_key_and_the_overlay_line() -> void:
	var save := {"version": 2}
	_press(save, "right")
	assert_eq(save["bedsit_facing"], "E")
	assert_eq(int(save["version"]), 2, "press never stamps a version")
	assert_contains(BedsitNav.debug_line(save, true), "compass E")
	assert_contains(BedsitNav.debug_line(save, true), "Dinosaurs")
	assert_eq(BedsitNav.debug_line(save, false), "", "nothing outside the bedsit path")
	assert_eq(BedsitNav.facing_of({"bedsit_facing": "Q"}), "N", "a damaged facing reads as north")


# --- the room

func test_the_map_loads_clean_with_one_room_and_four_viewpoints() -> void:
	var m := StoryMap.load_chapter("bedsit")
	assert_eq(m.errors, [], "the bedsit map builds, with its textures present")
	assert_eq(m.sectors.size(), 1, "one room")
	assert_near(m.eye_height, 1.6, 0.0001)
	var poly: PackedVector2Array = m.sector("room")["poly"]
	assert_near(absf(StoryMap._signed_area(poly)), 20.0, 0.01, "about 4 x 5 m")
	var at0 := Vector2.ZERO
	var yaws := {}
	var raw_wps: Array = m.raw["waypoints"]
	for f in RaveSave.FACINGS:
		var low := str(f).to_lower()
		var wp := m.waypoint("bedsit_" + low)
		assert_false(wp.is_empty(), "bedsit_%s is a waypoint" % low)
		var at: Vector2 = wp["at"]
		if f == "N":
			at0 = at
		assert_eq(at, at0, "the four viewpoints stand on one spot")
		assert_true(m.inside(at, "room", 0.6), "%s: inside the room, no wall within 0.6 m" % f)
		yaws[f] = fposmod(float(wp["yaw"]), 360.0)
		assert_true(bool((raw_wps[RaveSave.FACINGS.find(f)] as Dictionary).get("choice_view", false)), "%s is a choice viewpoint" % f)
		assert_true(m.waypoints.has("threshold_" + low), "%s has a threshold waypoint" % f)
	assert_eq(yaws, {"N": 0.0, "E": 270.0, "S": 180.0, "W": 90.0}, "yaws 0, 90, 180 and 270 round the compass")
	assert_true(m.inside(at0, "room", 1.9), "the spot is the middle of the room")


func test_no_wall_within_arms_length_in_any_facing() -> void:
	var m := StoryMap.load_chapter("bedsit", false)
	for f in RaveSave.FACINGS:
		var wp := m.waypoint("bedsit_" + str(f).to_lower())
		var at: Vector2 = wp["at"]
		var pose := {"cam": Vector3(at.x, m.eye_height, at.y), "yaw": float(wp["yaw"]), "pitch": 0.0, "sector": "room"}
		var c := CC.clearance(m, pose)
		assert_true(float(c["centre_d"]) >= 1.9, "%s: the wall ahead is %.2f m away (camera_clearance_check)" % [f, float(c["centre_d"])])
		var fwd := m.forward_of_yaw(float(wp["yaw"]))
		assert_true(m.inside(at + fwd * 0.6, "room", 0.0), "%s: 0.6 m ahead is still in the room" % f)


func test_each_facing_carries_its_threshold_objects() -> void:
	var m := StoryMap.load_chapter("bedsit", false)
	var ids := {}
	for t in m.things:
		ids[str(t["id"])] = true
	for d in m.decals:
		ids[str(d["id"])] = true
	for l in m.lights:
		ids[str(l["id"])] = true
	var want := {
		"N (space)": ["n_window", "n_glass", "n_rocket", "n_mobile", "n_moon"],
		"S (magic)": ["s_wardrobe", "s_wardrobe_light", "s_unicorn", "s_fairy", "s_leak_pink"],
		"E (dinos)": ["e_jungle", "e_jungle_glow", "e_dino", "e_fern", "e_jungle_light"],
		"W (transport)": ["w_door", "w_timetable", "w_car", "w_indicator", "w_street"],
		"the room": ["w_bed", "e_desk", "e_headphones", "n_lamp", "w_mirror", "n_radiator", "s_rail", "s_shelf", "n_poster_a"]}
	for k in want:
		for id in want[k]:
			assert_true(ids.has(id), "%s: %s is in the room" % [k, id])
	# the facing's threshold lies on the wall that facing looks at (north wall z -2.5, east x 2, south z 2.5, west x -2)
	var wall := {"n_glass": ["z", -2.5], "e_jungle_glow": ["x", 2.0], "s_wardrobe_light": ["z", 2.5], "w_door_light": ["x", -2.0]}
	for id in wall:
		var dd := {}
		for d in m.decals:
			if str(d["id"]) == id:
				dd = d
		assert_false(dd.is_empty(), id)
		if dd.is_empty():
			continue
		var at: Vector2 = dd["at"]
		var v := at.y if wall[id][0] == "z" else at.x
		assert_true(absf(v - float(wall[id][1])) < 0.02, "%s lies on its wall" % id)
