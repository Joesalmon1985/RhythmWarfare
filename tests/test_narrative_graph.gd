extends TestCase
## NarrativeGraph against the Python builder (tools/narrative/graph.py): the same nodes, edges, locations, quests and settings from the same inputs, read
## from the Python export docs/parallel-development/graph/narrative_graph.json (docs/ has a .gdignore, which stops importing, not reading).
## Also: the queries the router needs, the declared exceptions, bad data reported as sentences, and the build time.

const EXPORT_PATH := "res://docs/parallel-development/graph/narrative_graph.json"
const TODAY_PATH := "res://docs/parallel-development/graph/graph_today.json"

static var _shared: NarrativeGraph = null


static func graph() -> NarrativeGraph:
	if _shared == null:
		_shared = NarrativeGraph.load_default()
	return _shared


static func read_json(path: String) -> Variant:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	return JSON.parse_string(f.get_as_text())


static func canon(v: Variant) -> String:
	return JSON.stringify(v, "", true)


func _canon_list(items: Array) -> Array:
	var out: Array = []
	for x in items:
		out.append(canon(x))
	out.sort()
	return out


## Compares two lists of records as multisets and reports the first few that differ.
func _same_records(label: String, mine: Array, theirs: Array) -> void:
	var a := _canon_list(mine)
	var b := _canon_list(theirs)
	assert_eq(a.size(), b.size(), "%s: the count" % label)
	var only_mine: Array = []
	var only_theirs: Array = []
	var bset := {}
	for x in b:
		bset[x] = int(bset.get(x, 0)) + 1
	for x in a:
		if int(bset.get(x, 0)) > 0:
			bset[x] = int(bset[x]) - 1
		else:
			only_mine.append(x)
	for x in bset:
		for i in int(bset[x]):
			only_theirs.append(x)
	assert_eq(only_mine.size() + only_theirs.size(), 0, "%s: only in GDScript %s ... only in Python %s" % [label, str(only_mine.slice(0, 3)), str(only_theirs.slice(0, 3))])


func test_builds_without_errors() -> void:
	var g := graph()
	assert_eq(g.errors.size(), 0, "errors: %s" % str(g.errors))
	assert_true(g.is_valid())
	assert_eq(g.start, "main/warehouse")
	assert_eq(g.locations.size(), 5)
	assert_eq(g.quests.size(), 4)


func test_nodes_equal_the_python_export() -> void:
	var g := graph()
	var ex: Variant = read_json(EXPORT_PATH)
	assert_true(typeof(ex) == TYPE_DICTIONARY, "the export can be read")
	if typeof(ex) != TYPE_DICTIONARY:
		return
	var ids_mine: Array = g.nodes.keys()
	ids_mine.sort()
	var ids_py: Array = []
	for n in ex["nodes"]:
		ids_py.append(n["id"])
	ids_py.sort()
	assert_eq(ids_mine, ids_py, "the same node ids")
	assert_eq(g.nodes.size(), int(ex["meta"]["counts"]["nodes"]))
	_same_records("nodes", g.nodes.values(), ex["nodes"])


func test_edges_equal_the_python_export() -> void:
	var g := graph()
	var ex: Variant = read_json(EXPORT_PATH)
	if typeof(ex) != TYPE_DICTIONARY:
		fail("the export cannot be read")
		return
	assert_eq(g.edges.size(), int(ex["meta"]["counts"]["edges"]))
	# the key of the task: from, to, kind, via ...
	var keys_mine: Array = []
	for e in g.edges:
		keys_mine.append([e["from"], e["to"], e["kind"], e["via"], bool(e.get("hidden", false)), str(e["condition"].get("outcome", ""))])
	var keys_py: Array = []
	for e in ex["edges"]:
		keys_py.append([e["from"], e["to"], e["kind"], e["via"], bool(e.get("hidden", false)), str(e["condition"].get("outcome", ""))])
	_same_records("edge keys", keys_mine, keys_py)
	# ... and every other field: status, conditions, notes, gates, links
	_same_records("edges", g.edges, ex["edges"])
	var by_kind := {}
	for e in g.edges:
		by_kind[e["kind"]] = int(by_kind.get(e["kind"], 0)) + 1
	for k in ex["meta"]["counts"]["edges_by_kind"]:
		assert_eq(int(by_kind.get(k, 0)), int(ex["meta"]["counts"]["edges_by_kind"][k]), "edges of kind %s" % k)


func test_meta_equals_the_python_export() -> void:
	var g := graph()
	var ex: Variant = read_json(EXPORT_PATH)
	if typeof(ex) != TYPE_DICTIONARY:
		fail("the export cannot be read")
		return
	var meta: Dictionary = ex["meta"]
	assert_eq(g.start, meta["start"])
	assert_eq(canon(g.locations), canon(meta["locations"]))
	assert_eq(canon(g.quests), canon(meta["quests"]))
	for k in meta["settings"]:
		assert_eq(int(g.settings.get(k, -1)), int(meta["settings"][k]), "setting %s" % k)
	assert_eq(g.settings.size(), (meta["settings"] as Dictionary).size())


func test_todays_graph_equals_the_python_export() -> void:
	var errs: Array = []
	var game := NarrativeGraph.read_game(NarrativeGraph.CONTENT_DIR, errs)
	assert_eq(errs.size(), 0, str(errs))
	var t := NarrativeGraph.build_today(game)
	var ex: Variant = read_json(TODAY_PATH)
	if typeof(ex) != TYPE_DICTIONARY:
		fail("graph_today.json cannot be read")
		return
	_same_records("today nodes", t["nodes"].values(), ex["nodes"])
	_same_records("today edges", t["edges"], ex["edges"])
	assert_eq(canon(t["quests"]), canon(ex["meta"]["quests"]))


func test_declared_exceptions_equal_the_overlay() -> void:
	var g := graph()
	var ov: Variant = read_json(NarrativeGraph.OVERLAY_PATH)
	var ids: Array = []
	for x in ov["exceptions"]:
		ids.append(x["id"])
	assert_eq(g.exception_ids(), ids)
	assert_true(ids.has("bassment_passages_under_three"))
	assert_true(ids.has("legacy_wizard_entrance"))
	assert_true(ids.has("late_loops_have_no_ending"))
	var excused := g.excused_scenes()
	assert_eq(excused.size(), 42, "the 42 Bassment passages of the rule-5 exception")
	for s in excused:
		assert_eq(g.quest_of(s), "bassment")


func test_rule_5_counts_match_the_python_validator() -> void:
	var g := graph()
	var excused := g.excused_scenes()
	var enough := 0
	for id in g.nodes:
		var k := g.choice_count(id)
		if k >= 3:
			enough += 1
		else:
			assert_true(excused.has(id), "%s has %d choices and is not excused" % [id, k])
	assert_eq(enough, g.nodes.size() - 42, "104 of 146 scenes have three choices; the 42 others are the declared exception")
	for id in excused:
		assert_true(g.choice_count(id) < 3, "%s is excused and should be under three" % id)


func test_queries_the_router_needs() -> void:
	var g := graph()
	assert_true(g.resolves("main/warehouse"))
	assert_true(g.resolves("bassment/63"))
	assert_false(g.resolves("main/nowhere"))
	assert_false(g.resolves(""))
	assert_eq(g.hub_of_location("hospital_ward"), "main/hospital")
	assert_eq(g.hub_of_location("hell"), "main/underworld")
	assert_eq(g.hub_of_location("nowhere"), "")
	assert_eq(g.hub_of_scene("main/mothership.gallery"), "main/mothership")
	assert_eq(g.hub_of_scene("gospel/jordan"), "")
	assert_eq(g.location_of("main/hospital_late.cafe"), "hospital_ward")
	assert_eq(g.entry_of("gospel"), "gospel/jordan")
	assert_eq(g.entry_of("bassment"), "bassment/1")
	assert_eq(g.entry_of("squadron"), "squadron/base")
	assert_eq(g.entry_of("ember"), "ember/hollow")
	assert_true(g.is_completion("bassment/63"))
	assert_false(g.is_completion("bassment/62"))
	assert_eq(g.ending_of("bassment/13"), "death")
	# every quest scene has a visible return that lands on the checkpoint
	var without := 0
	for id in g.nodes:
		if g.quest_of(id) != "":
			var r := g.return_edge(id)
			if r.is_empty() or r["to"] != NarrativeGraph.CHECKPOINT:
				without += 1
	assert_eq(without, 0, "quest scenes without a visible return")
	assert_eq(g.return_edge("main/warehouse"), {}, "a mainline scene has no return")
	# every hub shows the four entrances, all ungated and through the port
	for loc in g.location_ids():
		var hub := g.hub_of_location(loc)
		var quests_seen := {}
		for e in g.entrances_from(hub):
			if not e.get("legacy", false):
				quests_seen[e["quest"]] = true
				assert_false(bool(e.get("rhythm_gate", true)), "%s: %s is rhythm-gated" % [hub, e["via"]])
				assert_eq(e.get("transition"), "port")
		assert_eq(quests_seen.size(), 4, "hub %s shows four quest entrances" % hub)
	# choices under flags: the wizard needs wh_wizard_met to be unset; a flag-gated route needs its flag
	var floor_vias: Array = []
	for e in g.choices_from("main/warehouse", {}):
		floor_vias.append(e["via"])
	assert_true(floor_vias.has("warehouse.enter_bassment"))
	assert_true(floor_vias.has("warehouse.wizard"))
	var met: Array = []
	for e in g.choices_from("main/warehouse", {"wh_wizard_met": true}):
		met.append(e["via"])
	assert_false(met.has("warehouse.wizard"), "the wizard is once a run")
	var dests := g.destinations_from("main/warehouse", {})
	assert_true(dests.has("bassment/1"))
	assert_true(dests.size() >= 6)


func test_late_worlds_belong_to_their_locations() -> void:
	var g := graph()
	var late := 0
	for id in g.nodes:
		var w := str(g.node(id).get("world", ""))
		if w == "hospital_late":
			assert_eq(g.location_of(id), "hospital_ward")
			late += 1
		elif w == "ward_late":
			assert_eq(g.location_of(id), "mental_hospital")
			late += 1
	assert_true(late > 0)


func test_bad_data_is_reported_as_sentences() -> void:
	# a folder with nothing in it
	var none := NarrativeGraph.load_files("res://content/does_not_exist", "res://content/narrative/missing.json")
	assert_false(none.is_valid())
	assert_true(none.errors.size() > 0)
	assert_contains(none.errors, "not found")
	# an overlay of another format
	var errs: Array = []
	var game := NarrativeGraph.read_game(NarrativeGraph.CONTENT_DIR, errs)
	var bad := NarrativeGraph.from_data(game, {"format": "something.else"})
	assert_false(bad.is_valid())
	assert_contains(bad.errors, "overlay format")
	# an overlay without required keys
	var thin := NarrativeGraph.from_data(game, {"format": NarrativeGraph.FORMAT})
	assert_false(thin.is_valid())
	assert_contains(thin.errors, "required key")
	# an overlay with a broken reference: the graph reports it and still answers queries without crashing
	var ov: Dictionary = read_json(NarrativeGraph.OVERLAY_PATH)
	ov["entrances"][0]["quest"] = "no_such_quest"
	ov["extra_routes"][0]["scene"] = "main/no_such_scene"
	var broken := NarrativeGraph.from_data(game, ov)
	assert_false(broken.is_valid())
	assert_contains(broken.errors, "no_such_quest")
	assert_contains(broken.errors, "no_such_scene")
	assert_eq(broken.choices_from("main/nowhere"), [])
	assert_eq(broken.hub_of_scene("main/nowhere"), "")
	# game data with a quest scene missing
	var game2 := NarrativeGraph.read_game(NarrativeGraph.CONTENT_DIR, [])
	(game2["passages"] as Dictionary).erase("63")
	var lost := NarrativeGraph.from_data(game2, read_json(NarrativeGraph.OVERLAY_PATH))
	assert_false(lost.is_valid(), "the victory passage is gone")
	assert_true(lost.errors.size() > 0)


func test_build_time_is_printed() -> void:
	var best := 1e9
	var errs: Array = []
	var game := NarrativeGraph.read_game(NarrativeGraph.CONTENT_DIR, errs)
	var ov: Dictionary = read_json(NarrativeGraph.OVERLAY_PATH)
	var read_t0 := Time.get_ticks_usec()
	NarrativeGraph.read_game(NarrativeGraph.CONTENT_DIR, [])
	var read_ms := float(Time.get_ticks_usec() - read_t0) / 1000.0
	for i in 5:
		best = minf(best, NarrativeGraph.from_data(game, ov).build_msec)
	var full := NarrativeGraph.load_default()
	print("NarrativeGraph: build from parsed data %.1f ms (best of 5); reading the content files %.1f ms; load_default() %.1f ms in all" % [best, read_ms, full.build_msec])
	assert_true(best < 1000.0, "the build is not absurdly slow")
