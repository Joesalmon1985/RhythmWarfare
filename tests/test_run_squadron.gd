extends TestCase
## The Mission Count (`squadron`, docs/THREE_PATHS_AND_FACES_PLAN.md section 5, stage 4): 14 scenes at 140 BPM on the owner's loops, the Clause (only in C06, C09 and C11), the loop with its way out,
## the cast and the acting in data, the three maps and the people baked for them. The matrix per path (test_run_matrix.gd) and tools/run/walk_run.sh --path squadron play it.

const CLAUSE := {"squadron.double_stamp": "air.c06", "squadron.medal_pinned": "city.c09", "squadron.count_raised": "escape"}


func _data() -> RunData:
	return RunData.load_path("squadron")


func test_the_path_loads_with_fourteen_scenes_at_140_bpm() -> void:
	var d := _data()
	assert_eq(d.errors, [], "the path validates")
	assert_eq(d.path_id, "squadron")
	assert_eq(d.node_order.size(), 14)
	assert_eq(float(d.cfg["timing"]["bpm"]), 140.0)
	assert_eq(d.start_node(), "base")
	assert_eq(d.world_order, ["base", "air", "city", "escape"])
	var endings: Array = d.node_order.filter(func(i: String) -> bool: return str(d.nodes[i]["ending"]) != "")
	assert_eq(endings, ["escape.c13"], "one escape ending")
	assert_eq(str(d.nodes["escape.c13"]["ending"]), "free")
	assert_true(HotspotContract.is_run_route(str(d.nodes["escape.c13"]["next"][0]["to"])))


func test_every_scene_plays_one_of_the_owners_loops_not_a_stand_in() -> void:
	var d := _data()
	var seen := {}
	for i in range(d.node_order.size()):
		var id := str(d.node_order[i])
		var n: Dictionary = d.nodes[id]
		var want := "squadron_c%02d" % (i + 1)
		assert_eq(str(n["audio"]), want, "%s plays %s" % [id, want])
		assert_eq(str(n["chart"]), want)
		assert_false(bool(n.get("temporary", false)), "%s is not a stand-in" % id)
		assert_true(d.packs.has(want), "the pack %s is imported" % want)
		assert_eq(str(d.packs[want].get("path", "")), "squadron")
		seen[want] = true
	assert_eq(seen.size(), 14)


func test_the_phase_reveals_drums_then_bass_then_synth_with_the_bass_prominent() -> void:
	var st: Array = _data().cfg["stages"]
	assert_eq(st.size(), 4)
	assert_eq(float(st[0]["gains"]["bass"]), 0.0, "drums alone first")
	assert_eq(float(st[1]["gains"]["bass"]), 1.0, "the bass enters at full gain")
	assert_eq(float(st[1]["gains"]["other"]), 0.0, "the synth waits")
	assert_true(float(st[2]["gains"]["other"]) > 0.0, "the synth joins on the drums' return")
	for k in [1, 2, 3]:
		assert_true(float(st[k]["gains"]["bass"]) >= 0.9, "the bass stays prominent in stage %d" % k)
	assert_eq(str(st[1]["cue"]), "bass")


func test_the_clause_is_in_three_scenes_and_nowhere_else() -> void:
	var d := _data()
	var found := {}
	for sid in d.node_order:
		for h in d.hotspots_of(str(sid)):
			for key in ["on_success", "on_failure"]:
				var oc: Dictionary = h[key]
				if not oc.has("cinematic") or str(oc.get("route", "")) == "":
					continue
				var name := str(oc["cinematic"])
				if name.begins_with("squadron.") and CLAUSE.has(name):
					found[name] = {"scene": str(sid), "key": key, "route": str(oc["route"])}
					assert_true(d.cfg["cinematics"].has(name))
	assert_eq(found.size(), 3, str(found))
	for name in CLAUSE:
		assert_eq(found[name]["scene"], CLAUSE[name], "%s lives in %s" % [name, CLAUSE[name]])
	# C06 and C09: the SUCCESS carries the cinematic and a route that is not the obvious one; C11: the failure's
	assert_eq(found["squadron.double_stamp"]["key"], "on_success")
	assert_eq(found["squadron.double_stamp"]["route"], "city.c09")
	assert_eq(found["squadron.medal_pinned"]["key"], "on_success")
	assert_eq(found["squadron.medal_pinned"]["route"], "escape")
	assert_eq(found["squadron.count_raised"]["key"], "on_failure")
	assert_eq(found["squadron.count_raised"]["route"], "base.c02")
	# no other scene has a success that carries a cinematic and a route
	for sid in d.node_order:
		for h in d.hotspots_of(str(sid)):
			var oc: Dictionary = h["on_success"]
			if oc.has("cinematic") and str(oc.get("route", "")) != "":
				assert_true(str(sid) in ["air.c06", "city.c09"], "%s: a success with a cinematic and a route outside the Clause scenes" % h["id"])


func test_the_loop_has_the_radio_as_its_way_out() -> void:
	var d := _data()
	var routes: Array = d.nodes["escape"]["next"]
	var loop_back := {}
	for r in routes:
		if str(r["to"]) == "base.c02":
			loop_back = r
	assert_true(bool(loop_back.get("loop", false)), "C11 -> C02 is the loop")
	var radio: Dictionary = {}
	for h in d.hotspots_of("escape"):
		if str(h["id"]) == "escape.radio":
			radio = h
	assert_false(radio.is_empty(), "the broken radio is in the scene")
	assert_eq(str(radio["on_success"]["route"]), "escape.c12", "its success breaks out north")
	assert_true(str(radio["on_failure"]["cinematic"]) == "squadron.count_raised")
	# the way out reaches the ending without going through the loop
	var seen := {}
	var queue: Array = ["escape.c12"]
	while not queue.is_empty():
		var cur: String = queue.pop_back()
		if seen.has(cur):
			continue
		seen[cur] = true
		for e in d.nodes[cur]["next"]:
			if d.nodes.has(str(e["to"])):
				queue.append(str(e["to"]))
	assert_true(seen.has("escape.c13"), "C12 reaches the neutral coast")
	assert_true(d.hotspots_of("escape.c14").size() >= 2 and bool(d.nodes["escape.c14"]["exit_scene"]), "the cell has its own way out (the latch) too")


func test_flags_cast_and_acting_are_in_data() -> void:
	var d := _data()
	var shore: Dictionary = {}
	for h in d.hotspots_of("escape.c13"):
		if bool(h["default"]):
			shore = h
	assert_true((shore["on_success"]["flags_set"] as Array).has("keep:path_squadron_free"), "the ending sets its flag")
	var keeps := {}
	var characters := 0
	for sid in d.node_order:
		var n: Dictionary = d.nodes[sid]
		assert_true((n.get("cast", []) as Array).size() >= 3, "%s has its cast" % sid)
		for h in d.hotspots_of(str(sid)):
			for key in ["on_success", "on_failure"]:
				for f in (h[key] as Dictionary).get("flags_set", []):
					if HotspotContract.is_keep(str(f)):
						keeps[str(f)] = true
			if str(h["kind"]) == "character":
				characters += 1
				var ac: Dictionary = h.get("acting", {})
				for ph in HotspotContract.ACTING_PHASES:
					assert_true(ac.has(ph), "%s acts its %s" % [h["id"], ph])
	assert_eq(characters, 2)
	for k in ["keep:path_squadron_free", "keep:path_squadron_clause", "keep:path_squadron_met_surgeon"]:
		assert_true(keeps.has(k), k)
	# the cast of the Clause scenes
	for name in CLAUSE:
		assert_true((d.cfg["cinematics"][name]["cast"] as Array).size() >= 2, "%s is acted" % name)
	# C07: no cheering whatever the play: the crowd's mood is pinned sad, and the cast has no cheer
	for line in d.nodes["city"]["cast"]:
		assert_false(str(line["act"]) in ["cheer", "wave", "laugh"], "no cheering in the Gunner's last flight")


func test_the_three_maps_validate_and_their_people_are_baked() -> void:
	for m in ["airfield", "city", "harbour"]:
		var sd: StoryData = StoryData.load_file("res://content/story/%s.json" % m)["data"]
		var map := StoryMap.load_chapter(m)
		map.validate_chapter(sd.raw)
		assert_eq(map.errors, [], "%s map" % m)
		assert_true(map.sectors.size() >= 4)
		var assets := StoryAssets.load_art(sd.art)
		assert_true(assets.ok(), m)
		assert_true(bool(assets.manifest.get("borrow_sprites", false)))
		var people: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/story/%s/people/people.json" % m))
		for a in sd.actors:
			assert_true((people["actors"] as Dictionary).has(str(a["id"])), "%s: %s is baked" % [m, a["id"]])
			assert_false(assets.rig(str(a["archetype"]), str(a["variant"]), str(a.get("art", ""))).is_empty(), "%s: %s has a rig to fall back on" % [m, a["id"]])
		assert_true(assets.sprite("glow").has("tex"), "%s borrows Night One's light sprites" % m)


func test_the_booth_radio_portal_is_in_play() -> void:
	OS.unset_environment("RW_PATH_REMAP")
	var w := RunData.load_default()
	assert_eq(w.errors, [])
	assert_true(RunData.path_exists("squadron"))
	var found := false
	for h in w.hotspots_of("warehouse.booth"):
		if str(h["id"]) == "warehouse.booth.radio":
			found = true
			assert_eq(str(h["on_success"]["route"]), "path:squadron")
	assert_true(found, "the radio is among the booth's hotspots")
	var skipped: Array = w.skipped_portals.map(func(s: Dictionary) -> String: return str(s["hotspot"]))
	assert_false(skipped.has("warehouse.booth.radio"))
	var m := StoryMap.load_chapter("night_one")
	assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t["id"]) == "booth_radio"), "the radio and the bomber's shadow stand in the booth")
