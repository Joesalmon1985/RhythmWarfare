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
var nodes: Dictionary = {}  # id -> {id, title, world, waypoint, role, depth, blurb, next: [{to, dir, label}], audio, chart, treatment, temporary}
var node_order: Array = []
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
	for n in run.get("nodes", []):
		var id := str(n["id"])
		var node: Dictionary = n.duplicate(true)
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
		if (n["next"] as Array).size() < 2:
			errors.append("node %s needs at least two routes" % id)
		var dirs := {}
		for e in n["next"]:
			if not nodes.has(str(e["to"])):
				errors.append("node %s: route to unknown node %s" % [id, e["to"]])
				continue
			var nd := int(nodes[str(e["to"])]["depth"])
			if nd != mini(int(n["depth"]) + 1, 99) and not (tier_of(int(n["depth"])) == TIERS and nd == int(n["depth"])):
				errors.append("node %s (depth %d): route to %s at depth %d (routes go one level deeper, or stay at the last depth)" % [id, int(n["depth"]), e["to"], nd])
			if dirs.has(str(e["dir"])):
				errors.append("node %s: two routes use the direction %s" % [id, e["dir"]])
			dirs[str(e["dir"])] = true
	# the same progression point plays the same chart: all nodes at one depth share one chart pack
	var chart_at: Dictionary = {}
	for id in nodes:
		var n: Dictionary = nodes[id]
		var dp := tier_of(int(n["depth"]))
		if chart_at.has(dp) and chart_at[dp] != n["chart"]:
			errors.append("depth %d: nodes use different charts (%s and %s); siblings must share one chart" % [dp, chart_at[dp], n["chart"]])
		chart_at[dp] = n["chart"]
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
