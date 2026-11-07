extends TestCase
## The heralds of the quest entrances (lead ruling 25, docs/art/HERALDS.md, src/story/story_heralds.gd): every shipped herald block is good and has its art, a herald is never a
## hotspot (the choice counts, the selectable list and the routes are exactly what they are without it), the gesture loops on the beat and is mirrored towards its entrance, and
## a herald stands in the crowd of its room only while its entrance is on offer.

const BEAT := 60.0 / 174.0
const ENTRANCES := {"warehouse.wizard": "dungeon", "warehouse.balcony.star": "gospel", "warehouse.booth.radio": "squadron", "warehouse.bar.ember": "ember", "warehouse.chill.wizard": "dungeon"}


func _all_hotspots() -> Array:
	var out: Array = []
	var d := RunData.load_default()
	for scene in d.hotspots:
		out.append_array(d.hotspots[scene])
	return out


func test_the_art_has_every_quest_with_a_full_loop_at_both_sizes() -> void:
	var doc := StoryHeralds.doc()
	assert_false(doc.is_empty(), "assets/story/heralds/heralds.json is there")
	assert_true(StoryHeralds.sheet() != null, "and its sheet")
	var n := int(doc["frames_per_beat"]) * int(doc["loop_beats"])
	assert_eq(n, 8)
	for q in StoryHeralds.QUESTS:
		var m: Dictionary = doc["heralds"].get(q, {})
		assert_false(m.is_empty(), "a herald for %s" % q)
		for lod in ["1", "2"]:
			assert_eq((m["lods"][lod]["frames"] as Array).size(), n, "%s lod %s: one frame per step of the loop" % [q, lod])
		assert_false((m.get("mark", {}) as Dictionary).is_empty(), "%s has its mark" % q)
	for i in n:
		assert_true(StoryHeralds.self_tex("dungeon", i, false) != null and StoryHeralds.self_tex("dungeon", i, true) != null, "the wizard's billboard frame %d, both ways" % i)


func test_every_quest_entrance_carries_its_quests_herald_and_every_block_is_good() -> void:
	var seen := {}
	var by_world := {}  # world -> {quest: true}, from the herald blocks the hotspot tables carry
	for h in _all_hotspots():
		if not (h as Dictionary).has("herald"):
			continue
		var errs := StoryHeralds.validate(h["herald"], str(h["id"]))
		assert_eq(errs, [], "%s: the herald block is good" % h["id"])
		seen[str(h["id"])] = str(h["herald"]["quest"])
		if not by_world.has(str(h["world"])):
			by_world[str(h["world"])] = {}
		by_world[str(h["world"])][str(h["herald"]["quest"])] = true
	# the Warehouse's five (the ones of the first herald work) are still there, each with its own quest; worlds that got entrances since add theirs (data-driven, not pinned)
	for id in ENTRANCES:
		assert_eq(seen.get(id, ""), ENTRANCES[id], "%s: the herald of its quest" % id)
	# a herald is of the quest its entrance leads to: the path quests route to path:<quest>; the dungeon to the lap's lock ("1", the Floor's hatch) or to the Bassment ("bassment", ruling 32)
	for h in _all_hotspots():
		if not (h as Dictionary).has("herald"):
			continue
		var q := str(h["herald"]["quest"])
		var route := str(h["on_success"].get("route", ""))
		if q == "dungeon":
			assert_true(route in ["1", "bassment"], "%s: a dungeon herald's entrance routes to 1 or bassment (it is %s)" % [h["id"], route])
		else:
			assert_eq(route, "path:" + q, "%s: the herald is of the quest the entrance leads to" % h["id"])
	# every world that has entrances has one of each quest the graph lists for its location (content/narrative/graph.json "entrances"; "bassment" there is the herald's "dungeon")
	var graph: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/narrative/graph.json"))
	var worlds_of := {}
	for loc in graph["locations"]:
		worlds_of[str(loc["id"])] = loc.get("worlds", [])
	var wanted := {}  # location -> {herald quest: true}
	for e in graph["entrances"]:
		if not wanted.has(str(e["location"])):
			wanted[str(e["location"])] = {}
		wanted[str(e["location"])]["dungeon" if str(e["quest"]) == "bassment" else str(e["quest"])] = true
	for loc in wanted:
		var have := {}
		for w in worlds_of.get(loc, []):
			have.merge(by_world.get(str(w), {}))
		if have.is_empty():
			continue  # no entrances authored for this location yet (hospital, ward, mothership at the time of writing)
		for q in wanted[loc]:
			assert_true(have.has(q), "%s has entrances, so it has one for the %s quest" % [loc, q])


func test_validate_refuses_a_bad_block() -> void:
	assert_false(StoryHeralds.validate({"quest": "disco", "at": [0, 0], "toward": [1, 1]}, "x").is_empty(), "an unknown quest")
	assert_false(StoryHeralds.validate({"quest": "gospel", "toward": [1, 1]}, "x").is_empty(), "a standing herald needs a place")
	assert_false(StoryHeralds.validate({"quest": "gospel", "at": [0, 0], "toward": [1, 1], "route": "x"}, "x").is_empty(), "a herald has no routes or other fields")
	assert_false(StoryHeralds.validate({"quest": "gospel", "self": "wizard_floor", "toward": [1, 1]}, "x").is_empty(), "only the wizard has billboard frames")
	assert_eq(StoryHeralds.validate({"quest": "ember", "at": [0, 0], "toward": [1, 1], "mark_y": 1.5}, "x"), [])
	assert_eq(StoryHeralds.validate({"quest": "gospel", "at": [0, 0], "toward": [1, 1], "mark_y": 2.55, "gate": true}, "x"), [], "a gate: a lit doorway at the entrance")
	assert_false(StoryHeralds.validate({"quest": "gospel", "at": [0, 0], "toward": [1, 1], "gate": "yes"}, "x").is_empty(), "gate is a bool")
	assert_false(StoryHeralds.validate({"quest": "gospel", "at": [0, 0], "toward": [1, 1], "gate": true, "mark_at": [2, 2]}, "x").is_empty(), "a gate stands under its own mark")
	assert_eq(StoryHeralds.validate({"quest": "dungeon", "self": "wizard_chill", "at": [0, 0], "toward": [1, 1], "mark_at": [0, 0], "mark_y": 2.1}, "x"), [], "a self herald may carry the mark over himself")


func test_a_herald_is_never_a_choice_the_counts_and_the_routes_are_as_without_it() -> void:
	var d := RunData.load_default()
	for scene in ["warehouse", "warehouse.balcony", "warehouse.booth", "warehouse.bar", "warehouse.chill"]:
		var with := RunHotspots.new(d, {"wh_saw_floor": true, "wh_vip_pass": true}, {})
		with.begin_scene(scene, 60.0)
		var bare := RunData.load_default()
		for h in bare.hotspots[scene]:
			(h as Dictionary).erase("herald")
		var without := RunHotspots.new(bare, {"wh_saw_floor": true, "wh_vip_pass": true}, {})
		without.begin_scene(scene, 60.0)
		for blk in [0, 3]:
			assert_eq(with.shown(blk, blk == 3).size(), without.shown(blk, blk == 3).size(), "%s block %d: the same number of choices on show" % [scene, blk])
			assert_eq(with.staged(blk).size(), without.staged(blk).size(), "%s: the same options staged" % scene)
		assert_eq(with.default_route(), without.default_route(), "%s: the same default" % scene)
		for h in with.list():
			assert_false(str(h["id"]).contains("herald"), "no hotspot is a herald")


func test_the_gesture_loops_on_the_beat_and_holds_the_point_in_reduced_motion() -> void:
	assert_eq(StoryHeralds.frame_of(0.0, BEAT), 0, "the loop starts on the beat")
	assert_eq(StoryHeralds.frame_of(BEAT * 1.0, BEAT), 4, "the second beat is the thrust of the point")
	assert_eq(StoryHeralds.frame_of(BEAT * 2.0, BEAT), 0, "two beats a loop")
	assert_eq(StoryHeralds.frame_of(BEAT * 0.5, BEAT), 2)
	assert_eq(StoryHeralds.frame_of(BEAT * 7.75, BEAT), 7)
	for t in [0.0, 1.3, 9.9]:
		assert_eq(StoryHeralds.frame_of(t, BEAT, true), StoryHeralds.POINT_FRAME, "reduced motion: the point held still")


func test_the_gesture_points_at_the_entrance_whatever_the_camera() -> void:
	var at := Vector2(0, 0)
	assert_false(StoryHeralds.flip_of(at, Vector2(2, 0), 0.0), "looking along -z, an entrance at +x is on screen right: the frames as baked")
	assert_true(StoryHeralds.flip_of(at, Vector2(-2, 0), 0.0), "at -x: mirrored")
	assert_true(StoryHeralds.flip_of(at, Vector2(2, 0), 180.0), "turned round, the same entrance is on the left")
	assert_true(StoryHeralds.flip_of(at, Vector2(0.01, -3), 0.0, true), "straight ahead keeps the last facing")
	assert_false(StoryHeralds.flip_of(at, Vector2(0.01, -3), 0.0, false))


func _stage() -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	return stage


func test_a_herald_stands_in_its_rooms_crowd_while_its_entrance_is_on_offer_and_never_otherwise() -> void:
	var stage := _stage()
	var ember: Dictionary = {}
	for h in RunData.load_default().hotspots["warehouse.bar"]:
		if str(h["id"]) == "warehouse.bar.ember":
			ember = h
	assert_false(ember.is_empty())
	var hd := StoryHeralds.new(stage)
	hd.begin_frame(1.0)
	hd.put(ember, "other")
	hd.end_frame()
	assert_eq(hd.shown(), ["warehouse.bar.ember"])
	var rec: Dictionary = hd._recs["warehouse.bar.ember"]
	var crowd: StoryCrowd = rec["crowd"]
	assert_true(crowd.props.has(rec["herald"]) and crowd.props.has(rec["mark"]), "the herald and its mark are props of the crowd: projected, culled and sorted with the people")
	var room := stage.map.room_of(stage.map.sector_at(Vector2(ember["herald"]["at"][0], ember["herald"]["at"][1])))
	assert_true(crowd == stage.crowds.get(room, stage.crowds["main"]), "the crowd of the room it stands in")
	var w: Dictionary = stage.map.waypoint("bar")
	var pose := {"cam": Vector3(w["at"].x, stage.map.eye_y(str(w["sector"])), w["at"].y), "yaw": -110.0}
	crowd.set_camera(pose, Vector2(480, 170), {})
	crowd.set_time(1.0)
	crowd.update(1.0, 60.0)
	var hp: StoryCrowdProp = rec["herald"]
	assert_true(hp.visible and not hp.items.is_empty(), "seen from the bar's corner the herald is projected")
	hd.begin_frame(2.0)
	hd.end_frame()
	assert_eq(hd.shown(), [], "not on offer: gone")
	hd.begin_frame(3.0)
	hd.put(ember, "current")
	hd.end_frame()
	assert_eq(hd.shown(), ["warehouse.bar.ember"], "back, the same props")
	assert_eq(crowd.props.filter(func(p: Variant) -> bool: return p == rec["herald"]).size(), 1, "never stood twice")
	hd.clear()
	assert_false(crowd.props.has(hp), "cleared")
	stage.queue_free()
