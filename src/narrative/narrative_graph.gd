class_name NarrativeGraph
extends RefCounted
## The narrative graph at run time: locations, hubs, quests, scenes and the routes between them, built from the game data plus the
## overlay content/narrative/graph.json. It builds exactly the graph tools/narrative/graph.py builds (a test compares the two), and answers
## the questions QuestRouter asks: what can be chosen from a scene, which scene is a quest's entry, which edge is a quest scene's return.
##
## A graph id is "<path>/<node>": main/<scene>, gospel/<node>, squadron/<node>, ember/<node>, bassment/<passage>. "$checkpoint" in an edge
## stands for the hub of the location a quest was entered from; QuestRouter resolves it from the route state.
##
## Loading never crashes on bad data: every problem is a sentence in `errors` (the convention of RunData), and is_valid() is false.
## The loader never writes the overlay. Design: docs/parallel-development/NARRATIVE_GRAPH.md; overlay format: graph/narrative.schema.md.

const FORMAT := "rhythm_warfare.narrative.v1"
const CHECKPOINT := "$checkpoint"
const CONTENT_DIR := "res://content"
const OVERLAY_PATH := "res://content/narrative/graph.json"
const MISS_OUTCOMES: Array = ["on_miss", "test_fail", "fight_lost"]
const SHIPPED_PATHS: Array = ["gospel", "squadron", "ember"]  # the fourth path, `stub`, is a developer test
const QUEST_IDS: Array = ["bassment", "gospel", "squadron", "ember"]
const QUEST_TITLES := {"bassment": "The Bassment", "gospel": "The Life of Jesus", "squadron": "The Mission Count", "ember": "The Ember Road"}
## [id, title, worlds, hub]: what the graph is built on when there is no overlay.
const BUILTIN_LOCATIONS: Array = [
	["warehouse_rave", "Warehouse Rave", ["warehouse"], "main/warehouse"],
	["hospital_ward", "Hospital Ward", ["hospital", "hospital_late"], "main/hospital"],
	["mental_hospital", "Mental Hospital", ["ward", "ward_late"], "main/ward"],
	["alien_spaceship", "Alien Spaceship", ["mothership"], "main/mothership"],
	["hell", "Hell", ["underworld"], "main/underworld"],
]
## The hidden ways out the code gives every quest scene (the pause menu's "Leave this path", the trial's system back key).
const BUILTIN_HIDDEN := {"bassment": "system_back_key", "gospel": "pause_menu_leave", "squadron": "pause_menu_leave", "ember": "pause_menu_leave"}
const HIDDEN_VIA := {"system_back_key": "system back key", "pause_menu_leave": "pause menu: Leave this path"}
const DEFAULT_SETTINGS := {"min_choices": 3, "max_choices_to_quest": 5, "max_choices_to_quest_in_location": 2, "history_limit": 32, "hotspot_cap": 8, "hub_hotspot_cap": 10}

## id -> {id, title, world, category ("mainline" or "quest"), location (mainline), quest (quest scenes), hub, status, ending?}
var nodes: Dictionary = {}
## Every route: {from, to, via, kind ("scene", "quest_entry", "quest_return"), status, condition{flags_all, flags_none, flags_set, outcome?, ...}, quest?, hidden?, ...}
var edges: Array = []
var locations: Array = []  # {id, title, worlds, hub}
var quests: Array = []  # {id, title, entry, completion: [ids]}
var settings: Dictionary = {}
var start := ""
var exceptions: Array = []  # the overlay's declared exceptions, as written
## quest id -> {system ("path" or "trial"), path, flag_prefixes: [String], title, return_object}
var quest_meta: Dictionary = {}
var errors: Array = []
var build_msec := 0.0

var _out: Dictionary = {}  # scene id -> Array of its edges
var _hub_of: Dictionary = {}  # location id -> hub scene id
var _entry_of: Dictionary = {}  # quest id -> entry scene id
var _completion: Dictionary = {}  # scene id -> true


## ---------------------------------------------------------------- loading

static func load_default() -> NarrativeGraph:
	return load_files(CONTENT_DIR, OVERLAY_PATH)


static var _cached: NarrativeGraph = null


## The game's graph, built once per session (the content does not change while the game runs): RunPlay asks for it at every run start. clear_cache() makes the next call build it again
## (tests that add fixture rows through HotspotContract.extra_rows).
static func cached() -> NarrativeGraph:
	if _cached == null:
		_cached = load_default()
	return _cached


static func clear_cache() -> void:
	_cached = null


## Reads the game data under `content_dir` and the overlay, and builds the target graph.
static func load_files(content_dir: String = CONTENT_DIR, overlay_path: String = OVERLAY_PATH) -> NarrativeGraph:
	var t0 := Time.get_ticks_usec()
	var errs: Array = []
	var game := read_game(content_dir, errs)
	var ov: Variant = _read_json(overlay_path, errs)
	var g := NarrativeGraph.new()
	g.errors = errs
	if bool(game["ok"]) and typeof(ov) == TYPE_DICTIONARY:
		g._build(game, ov)
	elif typeof(ov) != TYPE_DICTIONARY and not errs.is_empty() and not _mentions(errs, overlay_path):
		errs.append("%s: the overlay is not an object" % overlay_path)
	g.build_msec = float(Time.get_ticks_usec() - t0) / 1000.0
	return g


## Builds from data already read: `game` as read_game() returns it, `overlay` as parsed from graph.json.
static func from_data(game: Dictionary, overlay: Dictionary) -> NarrativeGraph:
	var t0 := Time.get_ticks_usec()
	var g := NarrativeGraph.new()
	g._build(game, overlay)
	g.build_msec = float(Time.get_ticks_usec() - t0) / 1000.0
	return g


func is_valid() -> bool:
	return errors.is_empty() and not nodes.is_empty()


## The game data the graph is built from: {ok, main: {id: node}, main_order, start_id, start, hotspots: {graph id: [hotspot]}, hotspot_ids,
## paths: {path: {nodes: {id: node}, start}}, passages: {key: passage}, passage_start}. Problems are appended to `errs`.
static func read_game(content_dir: String, errs: Array) -> Dictionary:
	var game := {"ok": false, "main": {}, "main_order": [], "start_id": "", "start": "", "hotspots": {}, "hotspot_ids": {},
		"paths": {}, "passages": {}, "passage_start": "1"}
	var before := errs.size()
	var run: Variant = _read_json(content_dir.path_join("run/run.json"), errs)
	if typeof(run) == TYPE_DICTIONARY:
		var r: Dictionary = run
		if typeof(r.get("nodes")) != TYPE_ARRAY or typeof(r.get("start_node")) != TYPE_STRING:
			errs.append("%s needs a nodes array and a start_node" % content_dir.path_join("run/run.json"))
		else:
			for n in r["nodes"]:
				if typeof(n) == TYPE_DICTIONARY and (n as Dictionary).has("id"):
					game["main"][str(n["id"])] = n
					game["main_order"].append(str(n["id"]))
			game["start_id"] = str(r["start_node"])
			game["start"] = "main/" + str(r["start_node"])
	_read_hotspot_dir(content_dir.path_join("run/hotspots"), "main/", game, errs)
	for p in SHIPPED_PATHS:
		var pr: Variant = _read_json(content_dir.path_join("paths/%s/run.json" % p), errs)
		if typeof(pr) != TYPE_DICTIONARY or typeof((pr as Dictionary).get("nodes")) != TYPE_ARRAY:
			errs.append("%s: path %s has no nodes" % [content_dir.path_join("paths/%s/run.json" % p), p])
			continue
		var pn: Dictionary = {}
		for n in (pr as Dictionary)["nodes"]:
			if typeof(n) == TYPE_DICTIONARY and (n as Dictionary).has("id"):
				pn[str(n["id"])] = n
		game["paths"][p] = {"nodes": pn, "start": str((pr as Dictionary).get("start_node", ""))}
		_read_hotspot_dir(content_dir.path_join("paths/%s/hotspots" % p), p + "/", game, errs)
	var trial: Variant = _read_json(content_dir.path_join("trial/passages.json"), errs)
	if typeof(trial) == TYPE_DICTIONARY and typeof((trial as Dictionary).get("passages")) == TYPE_DICTIONARY:
		game["passages"] = (trial as Dictionary)["passages"]
		game["passage_start"] = _s((trial as Dictionary).get("start", 1))
	else:
		errs.append("%s has no passages" % content_dir.path_join("trial/passages.json"))
	var hs := content_dir.path_join("trial/hotspots.json")
	if FileAccess.file_exists(hs):
		var th: Variant = _read_json(hs, errs)
		if typeof(th) == TYPE_DICTIONARY and typeof((th as Dictionary).get("hotspots")) == TYPE_ARRAY:
			for h in (th as Dictionary)["hotspots"]:
				if typeof(h) == TYPE_DICTIONARY:
					game["hotspot_ids"][str(h.get("id", ""))] = true
	game["ok"] = errs.size() == before and not (game["main"] as Dictionary).is_empty() and (game["paths"] as Dictionary).size() == SHIPPED_PATHS.size()
	return game


static func _read_hotspot_dir(dir_path: String, prefix: String, game: Dictionary, errs: Array) -> void:
	if not DirAccess.dir_exists_absolute(dir_path):
		errs.append("%s not found" % dir_path)
		return
	var files := Array(DirAccess.get_files_at(dir_path))
	files.sort()
	var lists: Array = []
	for f in files:
		if not str(f).ends_with(".json"):
			continue
		var d: Variant = _read_json(dir_path.path_join(str(f)), errs)
		if typeof(d) != TYPE_DICTIONARY or typeof((d as Dictionary).get("hotspots")) != TYPE_ARRAY:
			errs.append("%s has no hotspots array" % dir_path.path_join(str(f)))
			continue
		lists.append((d as Dictionary)["hotspots"])
	lists.append(HotspotContract.extra_rows.get(prefix.trim_suffix("/"), []))  # (test fixtures only; empty in the game)
	for hl in lists:
		for h in hl:
			if typeof(h) != TYPE_DICTIONARY:
				continue
			var key: String = prefix + str(h.get("scene", ""))
			if not game["hotspots"].has(key):
				game["hotspots"][key] = []
			game["hotspots"][key].append(h)
			game["hotspot_ids"][str(h.get("id", ""))] = true


static func _read_json(path: String, errs: Array) -> Variant:
	if not FileAccess.file_exists(path):
		errs.append("%s not found" % path)
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		errs.append("%s cannot be opened" % path)
		return null
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed == null:
		errs.append("%s is not valid JSON" % path)
	return parsed


static func _mentions(errs: Array, text: String) -> bool:
	for e in errs:
		if str(e).contains(text):
			return true
	return false


## ---------------------------------------------------------------- small helpers (the same readings as the Python tool)

static func _truthy(v: Variant) -> bool:
	match typeof(v):
		TYPE_NIL:
			return false
		TYPE_BOOL:
			return bool(v)
		TYPE_INT:
			return int(v) != 0
		TYPE_FLOAT:
			return float(v) != 0.0
		TYPE_STRING, TYPE_STRING_NAME:
			return str(v) != ""
		TYPE_ARRAY:
			return not (v as Array).is_empty()
		TYPE_DICTIONARY:
			return not (v as Dictionary).is_empty()
	return true


## An id read from JSON: a whole number is written without ".0" (JSON numbers arrive as floats).
static func _s(v: Variant) -> String:
	if typeof(v) == TYPE_FLOAT and is_equal_approx(float(v), roundf(float(v))):
		return str(int(v))
	return str(v)


static func _all_digits(s: String) -> bool:
	if s.is_empty():
		return false
	for i in s.length():
		var c := s.unicode_at(i)
		if c < 48 or c > 57:
			return false
	return true


static func _arr(v: Variant) -> Array:
	return (v as Array).duplicate(true) if typeof(v) == TYPE_ARRAY else []


## A new edge, with the fields tools/narrative/graph.py gives it. `extra` keys with a null value are left out; "condition" is merged into the condition.
static func _edge(frm: String, to: String, via: String, kind: String, status: String, quest_id: String = "", extra: Dictionary = {}) -> Dictionary:
	var e := {"from": frm, "to": to, "via": via, "kind": kind, "status": status,
		"condition": {"flags_all": [], "flags_none": [], "flags_set": []}}
	if quest_id != "":
		e["quest"] = quest_id
	for k in extra:
		if k == "condition":
			(e["condition"] as Dictionary).merge(extra[k], true)
		elif extra[k] != null:
			e[k] = extra[k]
	return e


static func entry_scene(game: Dictionary, quest_id: String) -> String:
	if quest_id == "bassment":
		return "bassment/" + str(game["passage_start"])
	return quest_id + "/" + str((game["paths"][quest_id] as Dictionary)["start"])


## ---------------------------------------------------------------- today's graph (the game data alone)

## {nodes, edges, locations, quests}: the graph of the game data alone. Same as `build_today` of the Python tool.
static func build_today(game: Dictionary) -> Dictionary:
	var loc_of_world := {}
	var hub_of := {}
	for l in BUILTIN_LOCATIONS:
		hub_of[l[0]] = l[3]
		for w in l[2]:
			loc_of_world[w] = l[0]
	var nodes_out := {}
	var edges_out: Array = []
	var main_nodes: Dictionary = game["main"]
	for k in game["main_order"]:
		var n: Dictionary = main_nodes[k]
		var gid := "main/" + str(k)
		var loc: Variant = loc_of_world.get(str(n.get("world", "")), null)
		nodes_out[gid] = {"id": gid, "title": n.get("title", ""), "world": n.get("world", ""), "category": "mainline", "location": loc,
			"hub": loc != null and gid == hub_of[loc], "status": "existing"}
		edges_out.append_array(_scene_edges(game, gid, "", main_nodes, "main/"))
	for p in SHIPPED_PATHS:
		if not (game["paths"] as Dictionary).has(p):
			continue
		var pnodes: Dictionary = game["paths"][p]["nodes"]
		for k in pnodes:
			var n: Dictionary = pnodes[k]
			var gid: String = str(p) + "/" + str(k)
			nodes_out[gid] = {"id": gid, "title": n.get("title", ""), "world": n.get("world", ""), "category": "quest", "quest": p, "hub": false, "status": "existing"}
			if _truthy(n.get("ending")):
				nodes_out[gid]["ending"] = n["ending"]
			edges_out.append_array(_scene_edges(game, gid, p, pnodes, p + "/"))
	var passages: Dictionary = game["passages"]
	var grants := {}
	for k in passages:
		var x: Dictionary = passages[k]
		if _truthy(x.get("grants")):
			grants[str(k)] = x["grants"]
	for k in passages:
		var x: Dictionary = passages[k]
		var gid := "bassment/" + str(k)
		nodes_out[gid] = {"id": gid, "title": x.get("title", ""), "world": x.get("zone", ""), "category": "quest", "quest": "bassment", "hub": false, "status": "existing"}
		var pk := str(x.get("kind", ""))
		if pk == "death" or pk == "victory":
			nodes_out[gid]["ending"] = pk
		var choices: Array = x.get("choices", [])
		for i in choices.size():
			var c: Dictionary = choices[i]
			var via := "trial.%s.%d" % [str(k), i]
			if c.get("to") == null:
				edges_out.append(_edge(gid, game["start"], via, "quest_return", "existing", "bassment", {"condition": {"outcome": "exit", "default": _truthy(c.get("default"))}}))
				continue
			var dests: Array = [["take", _s(c["to"])]]
			if c.has("test"):
				dests = [["test_pass", _s(c["test"]["pass"])], ["test_fail", _s(c["test"]["fail"])]]
			elif _truthy(c.get("encounter")):
				dests = [["win_or_take", _s(c["to"])]]
			for d in dests:
				var e := _edge(gid, "bassment/" + str(d[1]), via, "scene", "existing")
				var items: Array = []
				for gr in grants.get(str(d[1]), []):
					items.append("item:%s" % str(gr))
				(e["condition"] as Dictionary).merge({"outcome": d[0], "flags_set": items}, true)
				if _truthy(c.get("default")):
					e["condition"]["default"] = true
				if _truthy(c.get("requires")):
					e["condition"]["flags_all"] = ["item:%s" % str(c["requires"])]
				edges_out.append(e)
			if _truthy(c.get("encounter")) and int(c.get("lives", 0) if c.get("lives") != null else 0) > 0:  # trial_flow.gd: a fight lost `lives` times ends the adventure at passage 0
				var fe := _edge(gid, "bassment/0", via, "scene", "existing", "", {"condition": {"outcome": "fight_lost"}})
				fe["note"] = "engine rule (trial_flow.gd): a fight lost for good goes to passage 0"
				edges_out.append(fe)
	for q in QUEST_IDS:  # the hidden ways out
		for gid in nodes_out:
			if nodes_out[gid].get("quest", "") == q:
				edges_out.append(_edge(gid, game["start"], HIDDEN_VIA[BUILTIN_HIDDEN[q]], "quest_return", "existing", q, {"hidden": true}))
	for e in edges_out:
		if e["kind"] == "quest_return" and not e.has("quest"):
			e["quest"] = nodes_out[e["from"]].get("quest")  # null for a mainline scene, as in the Python tool
	var locs: Array = []
	for l in BUILTIN_LOCATIONS:
		locs.append({"id": l[0], "title": l[1], "worlds": l[2].duplicate(), "hub": l[3]})
	var qs: Array = []
	for q in QUEST_IDS:
		qs.append({"id": q, "title": QUEST_TITLES[q], "entry": entry_scene(game, q), "completion": _endings(game, q)})
	return {"nodes": nodes_out, "edges": edges_out, "locations": locs, "quests": qs}


static func _endings(game: Dictionary, q: String) -> Array:
	var out: Array = []
	if q == "bassment":
		for k in game["passages"]:
			if str(game["passages"][k].get("kind", "")) == "victory":
				out.append("bassment/" + str(k))
	else:
		var pnodes: Dictionary = game["paths"][q]["nodes"]
		for k in pnodes:
			if _truthy(pnodes[k].get("ending")):
				out.append(q + "/" + str(k))
	out.sort()
	return out


## The edges leaving one main-run or path scene: for each hotspot its success outcome (a block passed) and its failure outcome (a block missed).
## An outcome with no route of its own goes on by the scene's default exit.
static func _scene_edges(game: Dictionary, gid: String, quest_id: String, nodes_of_run: Dictionary, prefix: String) -> Array:
	var hs: Array = (game["hotspots"] as Dictionary).get(gid, [])
	var default_route := ""
	for h in hs:
		if _truthy(h.get("default")):
			default_route = str((h.get("on_success", {}) as Dictionary).get("route", ""))
	var node: Dictionary = nodes_of_run[gid.substr(gid.find("/") + 1)]
	var out: Array = []
	for h in hs:
		for pair in [["on_success", "on_pass"], ["on_failure", "on_miss"]]:
			var o: Dictionary = h.get(pair[0]) if typeof(h.get(pair[0])) == TYPE_DICTIONARY else {}
			var route := str(o.get("route", ""))
			var cont := false
			if route == "":
				route = default_route
				cont = true
			if route == "":
				continue
			var t := _target(game, route, nodes_of_run, prefix, quest_id)
			if t.is_empty():
				continue
			var kind: String = t[1]
			var av: Dictionary = h.get("available") if typeof(h.get("available")) == TYPE_DICTIONARY else {}
			var e := _edge(gid, t[0], str(h["id"]), kind, "existing", str(t[2]) if kind != "scene" else "")
			(e["condition"] as Dictionary).merge({"flags_all": _arr(av.get("flags_all", [])), "flags_none": _arr(av.get("flags_none", [])),
				"flags_set": _arr(o.get("flags_set", [])), "outcome": pair[1], "object_kind": str(h.get("kind", ""))}, true)
			if _truthy(h.get("default")):
				e["condition"]["default"] = true
			if cont:
				e["condition"]["continues_by_default_exit"] = true
			if kind == "quest_entry":
				e["rhythm_gate"] = pair[1] == "on_pass"  # the entrance is touched in the final window; a miss does not enter
				if str(node.get("trial_gate", "")) != "" and t[2] == "bassment" and route != HotspotContract.DUNGEON_ROUTE:
					e["legacy"] = true  # the wizard: a mid-scene entrance outside the port
			out.append(e)
	if hs.is_empty():  # an automatic scene goes on by itself, which costs no choice
		for nx in node.get("next", []):
			var e := _edge(gid, prefix + str(nx["to"]), "auto", "scene", "existing")
			e["condition"]["auto"] = true
			out.append(e)
	return out


## [to, kind, quest] for a hotspot route, or [] when it leads nowhere the graph knows.
static func _target(game: Dictionary, route: String, nodes_of_run: Dictionary, prefix: String, here_quest: String) -> Array:
	if nodes_of_run.has(route):
		return [prefix + route, "scene", ""]
	if _all_digits(route) and (game["passages"] as Dictionary).has(route):
		return ["bassment/" + route, "quest_entry", "bassment"]
	if route.begins_with("path:"):
		var p := route.substr(5)
		if not (game["paths"] as Dictionary).has(p):
			return []
		return [entry_scene(game, p), "quest_entry", p]
	if route == "run:warehouse":
		return [game["start"], "quest_return", here_quest]
	if route == HotspotContract.DUNGEON_ROUTE:  # a hub's entrance into the Bassment at the lap's end (ruling 15; N2.2), not the wizard's mid-scene passage number
		return [entry_scene(game, "bassment"), "quest_entry", "bassment"]
	return []


## ---------------------------------------------------------------- the target graph (today's, changed by the overlay)

func _build(game: Dictionary, ov: Dictionary) -> void:
	if str(ov.get("format", "")) != FORMAT:
		errors.append("the overlay format is '%s', expected '%s'" % [str(ov.get("format", "")), FORMAT])
		return
	for k in ["start", "locations", "quests", "entrances"]:
		if not ov.has(k):
			errors.append("the overlay is missing the required key '%s'" % k)
	if not errors.is_empty():
		return
	var base := build_today(game)
	var problems: Array = []
	var locs: Array = ov["locations"]
	var qdefs: Array = ov["quests"]
	var loc_of_world := {}
	var hubs := {}
	for l in locs:
		hubs[str(l["id"])] = str(l["hub"])
		for w in l.get("worlds", []):
			loc_of_world[str(w)] = str(l["id"])
	nodes = {}
	for k in base["nodes"]:
		nodes[k] = (base["nodes"][k] as Dictionary).duplicate()
	for k in nodes:
		var d: Dictionary = nodes[k]
		if d["category"] == "mainline":
			var loc: Variant = loc_of_world.get(str(d["world"]), null)
			if loc == null:
				problems.append("world %s of %s belongs to no location" % [d["world"], k])
			d["location"] = loc
			d["hub"] = loc != null and hubs.get(loc, "") == k
	var entry_of := {}
	for q in qdefs:
		entry_of[str(q["id"])] = str(q["entry"])
	var entrances: Array = ov["entrances"]
	var originals := {}  # existing objects whose gate the overlay removes (a "partial" entrance is a copy of one)
	var authored := {}  # entrance objects the content now has as hotspots (status "existing"): the overlay's ungated edge stands for the hotspot's own edges (N2.2)
	for en in entrances:
		var o: Dictionary = en.get("object", {})
		if (o.get("status") == "partial" or o.get("status") == "existing") and _truthy(o.get("copy_of")):  # (an authored copy on the hub keeps naming its original)
			originals[str(o["copy_of"])] = true
		if o.get("status") == "existing" and _truthy(o.get("id")):
			authored[str(o["id"])] = true
	for x in ov.get("extra_routes", []):
		var xo0: Dictionary = x.get("object", {})
		if str(x.get("kind", "")) == "quest_entry" and xo0.get("status") == "existing" and _truthy(xo0.get("id")):
			authored[str(xo0["id"])] = true

	# hub links and ways back to the hub that the content has as hotspots (status "existing"): the data's own edges are the routes; they carry the overlay's `link` (tools/narrative/graph.py)
	var rules0 := {}
	for r0 in ov.get("route_rules", []):
		rules0[str(r0.get("id", ""))] = r0
	var linked := {}  # hotspot id -> link kind
	var confirm := {}  # "scene|hotspot id" of an authored route the owner is still to confirm
	for l in locs:
		for hl in l.get("hub_links", []):
			if (hl.get("object", {}) as Dictionary).get("status") == "existing":
				linked[str(hl["object"]["id"])] = "hub_to_hub"
	if rules0.has("to_hub") and (rules0["to_hub"] as Dictionary).get("status") == "existing":
		for n in nodes:
			var d0: Dictionary = nodes[n]
			if d0["category"] == "mainline" and not d0["hub"] and d0.get("location") != null:
				linked[_pattern(str(rules0["to_hub"]["object"]), n, "")] = "to_hub"
	for x0 in ov.get("extra_routes", []):
		var xk := str(x0.get("kind", ""))
		if (xk == "restart" or xk == "second_route") and (x0.get("object", {}) as Dictionary).get("status") == "existing":
			linked["%s|%s" % [str(x0["scene"]), str(x0["object"]["id"])]] = xk
			if _truthy(x0.get("owner_to_confirm")):
				confirm["%s|%s" % [str(x0["scene"]), str(x0["object"]["id"])]] = true

	var out: Array = []
	for e0 in base["edges"]:
		var e: Dictionary = e0
		if e.get("hidden", false):
			continue  # the hidden leaves are rebuilt from the quests' `hidden_fallbacks`
		if linked.has(e["via"]) or linked.has("%s|%s" % [e["from"], e["via"]]):
			e = e.duplicate(true)
			e["link"] = linked.get(e["via"], linked.get("%s|%s" % [e["from"], e["via"]], ""))
			if confirm.has("%s|%s" % [e["from"], e["via"]]):
				e["owner_to_confirm"] = true
		var c: Dictionary = e["condition"]
		if authored.has(e["via"]) and e["kind"] != "quest_return":
			continue  # an authored entrance: the overlay's edge below is its route (ungated, through the port)
		if originals.has(e["via"]):
			if c.get("outcome") == "on_miss":
				continue  # an ungated entrance has no miss twin
			e = e.duplicate(true)
			e["condition"] = {"flags_all": [], "flags_none": [], "flags_set": []}
			if e["kind"] == "quest_entry":
				e["rhythm_gate"] = false
				e["transition"] = "port"
			e["status"] = "changed"
			e["note"] = "today gated by a passed block and flags; in the target not gated"
		elif e["kind"] == "quest_return":
			if c.get("outcome") == "on_miss":
				continue  # a return is not rhythm-gated: no miss twin
			e = e.duplicate(true)
			e["to"] = CHECKPOINT
			e["status"] = "changed"
			e["note"] = "authored way back; lands on the Floor today, on the checkpoint in the target"
		elif e["kind"] == "quest_entry" and e.get("legacy", false):  # the wizard: a legacy way of the Warehouse's Dungeon entrance
			e = e.duplicate(true)
			e["transition"] = "legacy_mid_scene"
		out.append(e)

	# 1. the hub entrances
	for en in entrances:
		var q := str(en.get("quest", ""))
		if not entry_of.has(q):
			problems.append("entrance %s: unknown quest %s" % [str(en.get("id", "")), q])
			continue
		var o: Dictionary = en.get("object", {})
		var e := _edge(str(en["scene"]), entry_of[q], str(o.get("id", "")), "quest_entry", "existing" if authored.has(str(o.get("id", ""))) else "proposed", q,
			{"entrance": en["id"], "rhythm_gate": bool(en.get("rhythm_gate", false)), "transition": en.get("transition")})
		out.append(e)
		if o.get("status") == "partial":
			e["note"] = "a copy of " + str(o.get("copy_of")) + " on the hub"
		for cnd in en.get("conditions", []):
			e["condition"]["flags_all"] += _arr(cnd.get("flag_all", []))
			var fn: Variant = cnd.get("flag_none", [])
			e["condition"]["flags_none"] += [fn] if typeof(fn) == TYPE_STRING else _arr(fn)
	# 2. the links between the hubs of a pair of locations
	for l in locs:
		for hl in l.get("hub_links", []):
			if linked.has(str(hl["object"]["id"])):
				if not _has_edge(base["edges"], str(l["hub"]), str(hl["to"]), str(hl["object"]["id"])):
					problems.append("hub link %s: existing, but the data has no route from %s to %s by it" % [hl["object"]["id"], l["hub"], hl["to"]])
				continue
			out.append(_edge(str(l["hub"]), str(hl["to"]), str(hl["object"]["id"]), "scene", "proposed", "", {"link": "hub_to_hub"}))
	# 3. the route rules
	var rules := {}
	for r in ov.get("route_rules", []):
		rules[str(r.get("id", ""))] = r
	for rid in rules:
		if not ["to_hub", "back", "return"].has(rid):
			problems.append("route rule %s: reserved id" % rid)
	var sorted_ids: Array = nodes.keys()
	sorted_ids.sort()
	if rules.has("to_hub"):
		var r: Dictionary = rules["to_hub"]
		for n in sorted_ids:
			var d: Dictionary = nodes[n]
			if d["category"] == "mainline" and not d["hub"] and d.get("location") != null:
				var oid := _pattern(str(r["object"]), n, "")
				if linked.has(oid):
					if not _has_edge(base["edges"], n, hubs[d["location"]], oid):
						problems.append("to_hub %s: existing, but the data has no route from %s to %s by it" % [oid, n, hubs[d["location"]]])
					continue
				out.append(_edge(n, hubs[d["location"]], oid, str(r.get("kind", "scene")), "proposed", "", {"link": "to_hub"}))
	if rules.has("back"):
		var r: Dictionary = rules["back"]
		var preds := {}
		for e0 in base["edges"]:
			var e: Dictionary = e0
			var fr: String = e["from"]
			if e["kind"] == "scene" and nodes[fr]["category"] == "quest" and nodes[fr].get("quest") != "bassment" and not e.get("hidden", false) \
					and not MISS_OUTCOMES.has(e["condition"].get("outcome", "")) and fr != e["to"] and nodes.has(e["to"]) \
					and nodes[e["to"]].get("quest") == nodes[fr].get("quest"):
				if not preds.has(e["to"]):
					preds[e["to"]] = []
				if not (preds[e["to"]] as Array).has(fr):
					preds[e["to"]].append(fr)
		for n in sorted_ids:
			var d: Dictionary = nodes[n]
			if d["category"] == "quest" and d.get("quest") != "bassment":
				var pl: Array = (preds.get(n, []) as Array).duplicate()
				pl.sort()
				for p in pl:
					out.append(_edge(n, p, _pattern(str(r["object"]), "", str(d["quest"])), str(r.get("kind", "scene")), "proposed", "",
						{"link": "back", "condition": {"previous_scene": true}}))
	# 4. the returns of the quests and their hidden leaves
	for q in qdefs:
		var rt: Dictionary = q.get("return", {})
		var qid := str(q["id"])
		var all_scenes: Array = []
		for n in sorted_ids:
			if nodes[n].get("quest", "") == qid:
				all_scenes.append(n)
		var scenes: Array = all_scenes
		if rt.get("placement") == "listed":
			scenes = _arr(rt.get("scenes", []))
			scenes.sort()
		var over := {}
		for o in rt.get("overrides", []):
			over[str(o["scene"])] = str(o["object"])
		if rules.has("return"):
			for n in scenes:
				if nodes.has(n):
					out.append(_edge(n, CHECKPOINT, over.get(n, str(rt.get("object", qid + ".return"))), "quest_return", "proposed", qid, {"link": "return"}))
		for fb in rt.get("hidden_fallbacks", []):
			for n in all_scenes:
				out.append(_edge(n, CHECKPOINT, str(HIDDEN_VIA.get(fb, fb)), "quest_return", "changed", qid,
					{"hidden": true, "note": "exists today and lands on the Warehouse Floor; in the target it lands on the checkpoint"}))
	# 5. routes added to one scene
	for x in ov.get("extra_routes", []):
		var kind := str(x.get("kind", ""))
		var xo: Dictionary = x.get("object", {})
		if not nodes.has(str(x.get("scene", ""))):
			problems.append("extra route %s: scene %s does not exist" % [str(xo.get("id", "")), str(x.get("scene", ""))])
			continue
		if kind == "quest_entry":
			var q2 := str(x.get("quest", ""))
			if not entry_of.has(q2):
				problems.append("extra route on %s: unknown quest %s" % [str(x["scene"]), q2])
				continue
			out.append(_edge(str(x["scene"]), entry_of[q2], str(xo["id"]), "quest_entry", "existing" if authored.has(str(xo["id"])) else "proposed", q2,
				{"link": "extra_entrance", "rhythm_gate": false, "transition": "port"}))
		elif kind == "restart" or kind == "second_route":
			if not nodes.has(str(x.get("to", ""))):
				problems.append("extra route %s: destination %s does not exist" % [str(xo.get("id", "")), str(x.get("to", ""))])
				continue
			if xo.get("status") == "existing":  # authored (tools/run/path_routes.py): the data's own edge is the route
				if not _has_edge(base["edges"], str(x["scene"]), str(x["to"]), str(xo["id"])):
					problems.append("extra route %s: existing, but the data has no route from %s to %s by it" % [xo["id"], x["scene"], x["to"]])
				continue
			var e := _edge(str(x["scene"]), str(x["to"]), str(xo["id"]), "scene", "proposed", "", {"link": kind})
			out.append(e)
			if _truthy(x.get("owner_to_confirm")):
				e["owner_to_confirm"] = true
		else:
			problems.append("extra route on %s: unknown kind %s" % [str(x["scene"]), kind])

	locations = []
	for l in locs:
		locations.append({"id": l["id"], "title": l.get("title", l["id"]), "worlds": _arr(l.get("worlds", [])), "hub": l["hub"]})
	quests = []
	for q in qdefs:
		quests.append({"id": q["id"], "title": q.get("title", ""), "entry": q["entry"], "completion": _arr((q.get("completion", {}) as Dictionary).get("scenes", []))})
		var system := str(q.get("system", "path"))
		var prefixes: Array = _arr(q.get("flag_prefixes", []))
		if system == "trial":
			prefixes = ["item:"]  # the Bassment carries items; the engine's grants are the flags "item:<name>"
		quest_meta[str(q["id"])] = {"system": system, "path": str(q.get("path", q["id"])), "flag_prefixes": prefixes,
			"title": str(q.get("title", "")), "return_object": str((q.get("return", {}) as Dictionary).get("object", ""))}
	edges = []
	for e in out:  # an edge end must be a scene (or the checkpoint placeholder); the rest is a problem, and the edge is left out
		var bad := ""
		for end in [e["from"], e["to"]]:
			if end != CHECKPOINT and not nodes.has(end):
				bad = end
				break
		if bad != "":
			problems.append("edge %s: %s is not a scene" % [e["via"], bad])
		else:
			edges.append(e)
	settings = DEFAULT_SETTINGS.duplicate()
	for k in (ov.get("settings", {}) as Dictionary):
		var v: Variant = ov["settings"][k]
		settings[k] = int(v) if typeof(v) == TYPE_FLOAT and is_equal_approx(float(v), roundf(float(v))) else v
	start = str(ov["start"])
	exceptions = _arr(ov.get("exceptions", []))
	errors.append_array(problems)
	_check_references(ov)
	_index()


static func _has_edge(edges: Array, frm: String, to: String, via: String) -> bool:
	for e in edges:
		if e["via"] == via and e["from"] == frm and e["to"] == to:
			return true
	return false


func _pattern(pattern: String, scene_id: String, quest_id: String) -> String:
	var out := pattern
	if scene_id != "":
		out = out.replace("<scene>", scene_id.substr(scene_id.find("/") + 1))
	if quest_id != "":
		out = out.replace("<quest>", quest_id)
	return out


## References that do not resolve are errors (rule 7 of the design): the game must not start on a half-resolved graph.
func _check_references(ov: Dictionary) -> void:
	if not nodes.has(start):
		errors.append("the overlay start %s is not a scene" % start)
	for l in locations:
		if not nodes.has(str(l["hub"])):
			errors.append("the hub %s of location %s is not a scene" % [l["hub"], l["id"]])
	for q in quests:
		if not nodes.has(str(q["entry"])):
			errors.append("the entry %s of quest %s is not a scene" % [q["entry"], q["id"]])
		for c in q["completion"]:
			if not nodes.has(str(c)):
				errors.append("the completion scene %s of quest %s is not a scene" % [c, q["id"]])
	for en in ov.get("entrances", []):
		if not nodes.has(str(en.get("scene", ""))):
			errors.append("entrance %s: scene %s is not a scene" % [str(en.get("id", "")), str(en.get("scene", ""))])
	for x in exceptions:
		for k in ["id", "rule", "reason", "tracked_by"]:
			if not (x as Dictionary).has(k):
				errors.append("exception %s has no %s" % [str((x as Dictionary).get("id", "?")), k])


func _index() -> void:
	_out = {}
	for e in edges:
		var f: String = e["from"]
		if not _out.has(f):
			_out[f] = []
		_out[f].append(e)
	_hub_of = {}
	for l in locations:
		_hub_of[str(l["id"])] = str(l["hub"])
	_entry_of = {}
	_completion = {}
	for q in quests:
		_entry_of[str(q["id"])] = str(q["entry"])
		for c in q["completion"]:
			_completion[str(c)] = true


## ---------------------------------------------------------------- queries

func resolves(id: String) -> bool:
	return nodes.has(id)


func node(id: String) -> Dictionary:
	return nodes.get(id, {})


func edges_from(id: String) -> Array:
	return _out.get(id, [])


## The location id of a mainline scene; "" for a quest scene or an unknown id.
func location_of(id: String) -> String:
	return str(node(id).get("location", "")) if node(id).get("location") != null else ""


## The quest id of a quest scene; "" for a mainline scene.
func quest_of(id: String) -> String:
	return str(node(id).get("quest", ""))


func is_mainline(id: String) -> bool:
	return node(id).get("category", "") == "mainline"


func hub_of_location(location_id: String) -> String:
	return str(_hub_of.get(location_id, ""))


## The hub of the location a mainline scene belongs to; "" for anything else.
func hub_of_scene(id: String) -> String:
	return hub_of_location(location_of(id))


func entry_of(quest_id: String) -> String:
	return str(_entry_of.get(quest_id, ""))


func quest_ids() -> Array:
	return _entry_of.keys()


func location_ids() -> Array:
	return _hub_of.keys()


func is_completion(id: String) -> bool:
	return _completion.has(id)


func ending_of(id: String) -> String:
	return str(node(id).get("ending", ""))


## The saved-with-the-quest flag prefixes of a quest ("item:" for the Bassment), [] for an unknown quest.
func flag_prefixes(quest_id: String) -> Array:
	return (quest_meta.get(quest_id, {}) as Dictionary).get("flag_prefixes", [])


## The visible (not hidden) return edge of a quest scene; {} when it has none.
func return_edge(id: String) -> Dictionary:
	var first: Dictionary = {}
	for e in edges_from(id):
		if e["kind"] == "quest_return" and not e.get("hidden", false) and e["to"] == CHECKPOINT:
			if e.get("link", "") == "return":
				return e
			if first.is_empty():
				first = e
	return first


## The quest entrances shown in a scene (hub entrances and extra entrances, ungated or not).
func entrances_from(id: String) -> Array:
	var out: Array = []
	for e in edges_from(id):
		if e["kind"] == "quest_entry":
			out.append(e)
	return out


## Distinct predecessors of a quest scene, sorted: the scenes a `back` option can lead to.
func predecessors(id: String) -> Array:
	var out: Array = []
	for e in edges_from(id):
		if (e["condition"] as Dictionary).get("previous_scene", false):
			out.append(e["to"])
	out.sort()
	return out


## The flags as a set {name: true}: from a Dictionary (name -> truthy) or an Array of names.
static func flag_set(flags: Variant) -> Dictionary:
	var out := {}
	if typeof(flags) == TYPE_DICTIONARY:
		for k in (flags as Dictionary):
			if _truthy(flags[k]):
				out[str(k)] = true
	elif typeof(flags) == TYPE_ARRAY:
		for k in (flags as Array):
			out[str(k)] = true
	return out


## True when the edge can be offered as a choice under `fset` (a flag set): not hidden, not automatic, not a miss twin, its flags satisfied.
static func offered(e: Dictionary, fset: Dictionary) -> bool:
	var c: Dictionary = e["condition"]
	if e.get("hidden", false) or c.get("auto", false) or MISS_OUTCOMES.has(c.get("outcome", "")):
		return false
	for f in c.get("flags_all", []):
		if not fset.has(str(f)):
			return false
	for f in c.get("flags_none", []):
		if fset.has(str(f)):
			return false
	return true


## The edges a player can choose in a scene under `flags`: visible, not a miss twin, flags satisfied, not "stay here". A `back` edge is offered only
## when it leads to `previous` (all of them when `previous` is "", for counting).
func choices_from(id: String, flags: Variant = {}, previous: String = "") -> Array:
	var fset := flag_set(flags)
	var out: Array = []
	for e in edges_from(id):
		if e["to"] == id or not offered(e, fset):
			continue
		if (e["condition"] as Dictionary).get("previous_scene", false) and previous != "" and e["to"] != previous:
			continue
		out.append(e)
	return out


## Distinct destinations the player can choose from a scene under `flags`, sorted. `$checkpoint` is one destination (or `checkpoint` when it is given).
func destinations_from(id: String, flags: Variant = {}, previous: String = "", checkpoint: String = "") -> Array:
	var seen := {}
	for e in choices_from(id, flags, previous):
		var t: String = e["to"]
		if t == CHECKPOINT and checkpoint != "":
			t = checkpoint
		seen[t] = true
	var out: Array = seen.keys()
	out.sort()
	return out


## The number of choices of a scene as rule 5 counts them: distinct destinations of the flag-free choices, a `back` option counted as one (the worst case
## over the possible predecessors).
func choice_count(id: String) -> int:
	var base := {}
	var backs := {}
	for e in choices_from(id, {}):
		if (e["condition"] as Dictionary).get("previous_scene", false):
			backs[e["to"]] = true
		else:
			base[e["to"]] = true
	if backs.is_empty():
		return base.size()
	var worst := 1 << 30
	for p in backs:
		var s := base.duplicate()
		s[p] = true
		worst = mini(worst, s.size())
	return worst


## The scenes whose rule-5 shortfall is declared as an exception in the overlay: {scene id: exception id}.
func excused_scenes() -> Dictionary:
	var out := {}
	for x in exceptions:
		if int((x as Dictionary).get("rule", 0)) == 5:
			for s in ((x as Dictionary).get("scope", {}) as Dictionary).get("scenes", []):
				out[str(s)] = str(x["id"])
	return out


func exception_ids() -> Array:
	var out: Array = []
	for x in exceptions:
		out.append(str((x as Dictionary).get("id", "")))
	return out
