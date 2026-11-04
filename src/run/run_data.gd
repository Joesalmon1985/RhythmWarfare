class_name RunData
extends RefCounted
## The continuous run's data: content/run/run.json (timing, thresholds, stages, route map), content/story/music.json (which pack's
## recordings and which pack's chart each node plays) and the packs under songs/packs/ written by tools/content/beatshaper.py.
## load() merges them into one node table and validates everything a run depends on; errors name the file and the node.

const RUN_PATH := "res://content/run/run.json"
const MUSIC_PATH := "res://content/story/music.json"
const PACKS_DIR := "res://songs/packs"
const TIERS := 4  # difficulty tiers (pack.tiers "1".."4"); a node's tier is min(depth, TIERS)

var cfg: Dictionary = {}
## A node is a SCENE: one 64-beat phase at a place in a world. id -> {id, world (the run world's id: the save and the home cards), map (the art world the stage is built from), scene, title (the room),
## world_title, entry, exit_scene, depth (the world's), waypoint (home), rail, role, blurb, next: [{to, dir, label, loop?}], audio, chart, treatment, temporary}
var nodes: Dictionary = {}
var node_order: Array = []
var worlds: Dictionary = {}  # world id -> {id, title, map, depth, blurb}
var world_order: Array = []
var packs: Dictionary = {}  # id -> pack.json (+ "dir")
var errors: Array = []
var warnings: Array = []


static func load_default() -> RunData:
	return load_files(RUN_PATH, MUSIC_PATH, PACKS_DIR)


static func load_files(run_path: String, music_path: String, packs_dir: String) -> RunData:
	var d := RunData.new()
	var run: Variant = _json(run_path, d.errors)
	var music: Variant = _json(music_path, d.errors)
	if typeof(run) != TYPE_DICTIONARY or typeof(music) != TYPE_DICTIONARY:
		return d
	d.cfg = run
	var dir := DirAccess.open(packs_dir)
	if dir == null:
		d.errors.append("%s: packs folder missing" % packs_dir)
		return d
	for sub in dir.get_directories():
		var pj := packs_dir.path_join(sub).path_join("pack.json")
		if FileAccess.file_exists(pj):
			var p: Variant = _json(pj, d.errors)
			if typeof(p) == TYPE_DICTIONARY:
				p["dir"] = packs_dir.path_join(sub)
				d.packs[str(p["id"])] = p
	var assign: Dictionary = {}
	for m in music.get("nodes", []):
		assign[str(m["id"])] = m
	for w in run.get("worlds", []):
		d.worlds[str(w["id"])] = w
		d.world_order.append(str(w["id"]))
	for n in run.get("nodes", []):
		var id := str(n["id"])
		var node: Dictionary = n.duplicate(true)
		if node.has("place"):  # the scene's place: its home waypoint and its rail, flattened
			for k in (node["place"] as Dictionary):
				node[k] = node["place"][k]
			node.erase("place")
		var wd: Dictionary = d.worlds.get(str(node.get("world", "")), {})
		if wd.is_empty():
			d.errors.append("scene %s: world '%s' is not in run.json worlds" % [id, node.get("world", "")])
		node["map"] = str(wd.get("map", ""))
		node["depth"] = int(wd.get("depth", 1))
		node["world_title"] = str(wd.get("title", ""))
		node["entry"] = bool(node.get("entry", false))
		node["exit_scene"] = bool(node.get("exit_scene", false))
		var m: Dictionary = assign.get(id, {})
		if m.is_empty():
			d.errors.append("music.json has no entry for node %s" % id)
		node["audio"] = str(m.get("audio", ""))
		node["chart"] = str(m.get("chart", ""))
		node["treatment"] = str(m.get("treatment", "none"))
		node["temporary"] = bool(m.get("temporary", false))
		d.nodes[id] = node
		d.node_order.append(id)
	for id in assign:
		if not d.nodes.has(id):
			d.errors.append("music.json lists node %s that run.json does not have" % id)
	d._validate()
	return d


static func _json(path: String, errors: Array) -> Variant:
	if not FileAccess.file_exists(path):
		errors.append("%s not found" % path)
		return null
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if v == null:
		errors.append("%s is not valid JSON" % path)
	return v


func tier_of(depth: int) -> int:
	return clampi(depth, 1, TIERS)


func start_node() -> String:
	return str(cfg.get("start_node", node_order[0] if not node_order.is_empty() else ""))


func _validate() -> void:
	if not nodes.has(start_node()):
		errors.append("start_node %s is not a node" % start_node())
	var tm: Dictionary = cfg.get("timing", {})
	for k in ["bpm", "phase_beats", "block_beats", "cue_span_beats", "decision_beat"]:
		if not tm.has(k):
			errors.append("run.json timing.%s is missing" % k)
	if int(tm.get("phase_beats", 0)) != 4 * int(tm.get("block_beats", 1)):
		errors.append("a phase is four blocks (phase_beats %s, block_beats %s)" % [tm.get("phase_beats"), tm.get("block_beats")])
	if (cfg.get("stages", []) as Array).size() != 4:
		errors.append("run.json needs four mix stages")
	for id in nodes:
		var n: Dictionary = nodes[id]
		for key in ["audio", "chart"]:
			if not packs.has(str(n[key])):
				errors.append("node %s: %s pack '%s' does not exist" % [id, key, n[key]])
		if not (cfg.get("treatments", {}) as Dictionary).has(str(n["treatment"])):
			errors.append("node %s: treatment '%s' is not in run.json" % [id, n["treatment"]])
		errors.append_array(RunRail.validate(id, n.get("rail")))
		_validate_routes(id, n)
	_validate_worlds()
	_validate_places()
	# sibling scenes (the routes of one scene) may chart different packs: the route lock then applies between them (the engine greys the others out at the last block's decision)
	for id in nodes:
		var charts := {}
		for e in nodes[id]["next"]:
			if nodes.has(str(e["to"])):
				charts[str(nodes[str(e["to"])]["chart"])] = true
		if charts.size() > 1:
			warnings.append("scene %s: its routes chart different packs (%s); the route lock applies, the chart is fixed 3.5 beats before the phase ends" % [id, ", ".join(PackedStringArray(charts.keys()))])
	for id in nodes:
		var n2: Dictionary = nodes[id]
		if packs.has(str(n2["audio"])) and packs.has(str(n2["chart"])):
			if int(packs[str(n2["audio"])]["phrase_beats"]) != int(packs[str(n2["chart"])]["phrase_beats"]):
				errors.append("node %s: audio and chart packs have different phrase lengths" % id)
	for pid in packs:
		var p: Dictionary = packs[pid]
		if int(p["bpm"]) != int(tm.get("bpm", 174)):
			errors.append("pack %s is %s BPM, the run is %s" % [pid, p["bpm"], tm.get("bpm")])
		if int(tm.get("phase_beats", 64)) % int(p["phrase_beats"]) != 0:
			errors.append("pack %s: %d-beat phrase does not tile a phase" % [pid, int(p["phrase_beats"])])
		for t in range(1, TIERS + 1):
			if not (p["tiers"] as Dictionary).has(str(t)):
				errors.append("pack %s has no tier %d" % [pid, t])
	# reachability: every node can be reached from the start node
	var seen := {}
	var queue: Array = [start_node()]
	while not queue.is_empty():
		var cur: String = queue.pop_back()
		if seen.has(cur) or not nodes.has(cur):
			continue
		seen[cur] = true
		for e in nodes[cur]["next"]:
			queue.append(str(e["to"]))
	for id in nodes:
		if not seen.has(id):
			warnings.append("node %s cannot be reached from the start" % id)


func _validate_routes(id: String, n: Dictionary) -> void:
	var routes: Array = n["next"]
	if routes.size() < (2 if bool(n["exit_scene"]) else 1):
		errors.append("scene %s needs at least %d route%s" % [id, 2 if bool(n["exit_scene"]) else 1, "s" if bool(n["exit_scene"]) else ""])
	var dirs := {}
	for e in routes:
		var to := str(e["to"])
		if not nodes.has(to):
			errors.append("scene %s: route to unknown scene %s" % [id, to])
			continue
		var t: Dictionary = nodes[to]
		var same_world := str(t["world"]) == str(n["world"])
		if bool(n["exit_scene"]):
			if same_world and not bool(e.get("loop", false)):
				errors.append("exit scene %s: the route to %s stays in the world; mark it \"loop\": true or lead to another world" % [id, to])
			if not bool(t["entry"]):
				errors.append("exit scene %s: the route to %s must lead to the entry scene of a world" % [id, to])
			var nd := int(t["depth"])
			if not same_world and nd != mini(int(n["depth"]) + 1, 99) and not (tier_of(int(n["depth"])) == TIERS and nd == int(n["depth"])):
				errors.append("exit scene %s (depth %d): route to %s at depth %d (world exits go one level deeper, or stay at the last depth)" % [id, int(n["depth"]), to, nd])
		else:
			if not same_world:
				errors.append("scene %s: the route to %s leaves the world, only the exit scene may" % [id, to])
			elif bool(t["entry"]) and not bool(e.get("loop", false)):
				errors.append("scene %s: the route back to the entry scene %s must be marked \"loop\": true" % [id, to])
		if dirs.has(str(e["dir"])):
			errors.append("scene %s: two routes use the direction %s" % [id, e["dir"]])
		dirs[str(e["dir"])] = true
		if not (n.get("rail", {}) as Dictionary).get("exits", {}).has(str(e["dir"])):
			errors.append("scene %s: the route %s has no exit doorway in rail.exits" % [id, e["dir"]])


## One entry scene per world (its id is the world's id: the save's "reached" and the home cards), one exit scene, every scene reaches the exit, no cycle inside a world
## except through a route marked `loop`.
func _validate_worlds() -> void:
	for w in worlds:
		var entries: Array = []
		var exits: Array = []
		var scenes: Array = []
		for id in nodes:
			if str(nodes[id]["world"]) != w:
				continue
			scenes.append(id)
			if bool(nodes[id]["entry"]):
				entries.append(id)
			if bool(nodes[id]["exit_scene"]):
				exits.append(id)
		if entries.size() != 1:
			errors.append("world %s needs exactly one entry scene (has %d)" % [w, entries.size()])
		elif str(entries[0]) != w:
			errors.append("world %s: the entry scene's id must be the world's id (found %s)" % [w, entries[0]])
		if exits.size() != 1:
			errors.append("world %s needs exactly one exit scene (has %d)" % [w, exits.size()])
		if scenes.is_empty():
			errors.append("world %s has no scenes" % w)
			continue
		var state := {}  # 1 = on the DFS stack, 2 = done
		for id in scenes:
			_dfs_cycle(str(id), state, w)
		for id in scenes:  # every scene reaches the exit scene over routes that stay in the world
			if not _reaches_exit(str(id), {}):
				errors.append("scene %s cannot reach the exit scene of world %s" % [id, w])


func _in_world_routes(id: String) -> Array:
	var out: Array = []
	for e in nodes[id]["next"]:
		var to := str(e["to"])
		if nodes.has(to) and str(nodes[to]["world"]) == str(nodes[id]["world"]) and not bool(e.get("loop", false)):
			out.append(to)
	return out


func _dfs_cycle(id: String, state: Dictionary, w: String) -> void:
	if int(state.get(id, 0)) == 2:
		return
	state[id] = 1
	for to in _in_world_routes(id):
		if int(state.get(to, 0)) == 1:
			errors.append("world %s: a cycle through %s and %s (a route that goes back must be marked \"loop\": true)" % [w, id, to])
		else:
			_dfs_cycle(str(to), state, w)
	state[id] = 2


func _reaches_exit(id: String, seen: Dictionary) -> bool:
	if bool(nodes[id]["exit_scene"]):
		return true
	seen[id] = true
	for to in _in_world_routes(id):
		if not seen.has(to) and _reaches_exit(str(to), seen):
			return true
	return false


## Every home waypoint, rail place, arrival and doorway exists in the scene's map (the maps' own validation covers the geometry).
func _validate_places() -> void:
	var known := {}  # map id -> {waypoint id -> true}
	for id in nodes:
		var n: Dictionary = nodes[id]
		var mp := str(n["map"])
		if not known.has(mp):
			var ids := {}
			var path: String = StoryMap.PATH % mp
			var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
			if typeof(parsed) != TYPE_DICTIONARY:
				errors.append("scene %s: map %s not found (%s)" % [id, mp, path])
			else:
				for wp in parsed.get("waypoints", []):
					ids[str(wp["id"])] = true
			known[mp] = ids
		var ids2: Dictionary = known[mp]
		if ids2.is_empty():
			continue
		var want: Array = [str(n.get("waypoint", ""))]
		var r: Dictionary = n.get("rail", {})
		for key in ["good", "bad"]:
			for p in r.get(key, []):
				want.append(str(p.get("to", "")))
		if str(r.get("arrive", "")) != "":
			want.append(str(r["arrive"]))
		for dir in (r.get("exits", {}) as Dictionary):
			want.append(str(r["exits"][dir]))
		for wid in want:
			if not ids2.has(wid):
				errors.append("scene %s: waypoint '%s' is not in map %s" % [id, wid, mp])


## The scenes of a world in file order.
func scenes_of(world: String) -> Array:
	return node_order.filter(func(i: String) -> bool: return str(nodes[i]["world"]) == world)


func entry_of(world: String) -> String:
	for i in node_order:
		if str(nodes[i]["world"]) == world and bool(nodes[i]["entry"]):
			return str(i)
	return ""
