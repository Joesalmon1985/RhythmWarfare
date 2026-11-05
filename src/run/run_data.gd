class_name RunData
extends RefCounted
## The continuous run's data: content/run/run.json (timing, thresholds, stages, route map), content/story/music.json (which pack's
## recordings and which pack's chart each node plays) and the packs under songs/packs/ written by tools/content/beatshaper.py.
## load() merges them into one node table and validates everything a run depends on; errors name the file and the node.

const RUN_PATH := "res://content/run/run.json"
const MUSIC_PATH := "res://content/story/music.json"
const PACKS_DIR := "res://songs/packs"
const ARRANGEMENTS_DIR := "res://content/music/arrangements"
const RECIPES_PATH := "res://content/music/mix_recipes.json"
const HOTSPOTS_DIR := "res://content/run/hotspots"  # <world>.json per run world: the scenes' hotspots (HotspotContract)
const PATHS_DIR := "res://content/paths"  # <id>/run.json, music.json, hotspots/<world>.json: a sister run at its own tempo (docs/THREE_PATHS_AND_FACES_PLAN.md section 3)
const INHERITED := ["judgement", "energy", "stages", "mix", "effects", "treatments"]  # a path's run.json may leave these out: the main run's apply
const TIERS := 4  # difficulty tiers (pack.tiers "1".."4"); a node's tier is min(depth, TIERS)

var cfg: Dictionary = {}
## A node is a SCENE: one 64-beat phase at a place in a world. id -> {id, world (the run world's id: the save and the home cards), map (the art world the stage is built from), scene, title (the room),
## world_title, entry, exit_scene, depth (the world's), waypoint (home), rail, role, blurb, next: [{to, dir, label, loop?}], audio, chart, treatment, temporary}
var nodes: Dictionary = {}
var node_order: Array = []
var worlds: Dictionary = {}  # world id -> {id, title, map, depth, blurb}
var world_order: Array = []
var packs: Dictionary = {}  # id -> pack.json (+ "dir")
var arrangements: Dictionary = {}  # id -> content/music/arrangements/<id>.json (docs/CONTINUOUS_RUN.md, "Arrangements")
var recipes: Dictionary = {}  # mix recipe name -> {drums, bass, other}
var seed_value := 0  # the per-run seed that picks between a scene's alternate arrangements (RW_RUN_SEED, else the save's)
var hotspots: Dictionary = {}  # scene id -> Array of normalised hotspot dictionaries (the authored ones, else one exit per route made from the scene's doorways)
var hotspots_authored: Dictionary = {}  # scene id -> true when its hotspots come from content/run/hotspots/<world>.json
var errors: Array = []
var warnings: Array = []
var path_id := ""  # the path this data belongs to ("" for the main run): run.json carries "path": {id, title, entry_from, returns_to, opens}
var path_info: Dictionary = {}
var skipped_portals: Array = []  # [{hotspot, scene, path}] portals whose path has no run.json yet: left out of play, logged (a dev note, not an error)


static func load_default() -> RunData:
	return load_files(RUN_PATH, OS.get_environment("RW_RUN_MUSIC") if OS.get_environment("RW_RUN_MUSIC") != "" else MUSIC_PATH, PACKS_DIR)


## RW_PATH_REMAP="gospel=stub,ember=stub": a portal's path id is looked up under another id (the review of the stub path through the balcony portal; empty = no remap).
static func resolve_path_id(id: String) -> String:
	for pair in OS.get_environment("RW_PATH_REMAP").split(",", false):
		if pair.contains("=") and pair.get_slice("=", 0) == id:
			return pair.get_slice("=", 1)
	return id


static func path_dir(id: String) -> String:
	return PATHS_DIR.path_join(id)


## True when the path can be played: its run.json and music.json exist (the portals of paths that are not written yet stay hidden).
static func path_exists(id: String) -> bool:
	var rid := resolve_path_id(id)
	return rid.is_valid_identifier() and FileAccess.file_exists(path_dir(rid).path_join("run.json")) and FileAccess.file_exists(path_dir(rid).path_join("music.json"))


## The path ids that have a folder under content/paths (any state), sorted.
static func path_ids() -> Array:
	var out: Array = []
	var dir := DirAccess.open(PATHS_DIR)
	if dir != null:
		for sub in dir.get_directories():
			out.append(sub)
	out.sort()
	return out


## A path's own run: content/paths/<id>/run.json (+ music.json, hotspots/), the packs of songs/packs whose pack.json names this path. `id` is looked up through RW_PATH_REMAP.
static func load_path(id: String, p_seed: int = -1) -> RunData:
	var dir := path_dir(resolve_path_id(id))
	return load_files(dir.path_join("run.json"), dir.path_join("music.json"), PACKS_DIR, p_seed, dir.path_join("arrangements"), dir.path_join("hotspots"))


## The run's per-run seed: RW_RUN_SEED when set, else the one RunProgress stores (a new one is drawn each run), else 0 (tests and tools without the autoload).
static func run_seed() -> int:
	if OS.get_environment("RW_RUN_SEED") != "":
		return int(OS.get_environment("RW_RUN_SEED"))
	var loop := Engine.get_main_loop()
	if loop is SceneTree:
		var s: Node = (loop as SceneTree).root.get_node_or_null("Session")
		if s != null and s.get("run_progress") != null:
			return (s.get("run_progress") as RunProgress).run_seed()
	return 0


## `p_seed` < 0 takes run_seed(); RW_RUN_MUSIC (an absolute path) replaces music_path in load_default (tools and recordings).
static func load_files(run_path: String, music_path: String, packs_dir: String, p_seed: int = -1, arrangements_dir: String = ARRANGEMENTS_DIR, hotspots_dir: String = HOTSPOTS_DIR) -> RunData:
	var d := RunData.new()
	d.seed_value = run_seed() if p_seed < 0 else p_seed
	var run: Variant = _json(run_path, d.errors)
	var music: Variant = _json(music_path, d.errors)
	if typeof(run) != TYPE_DICTIONARY or typeof(music) != TYPE_DICTIONARY:
		return d
	d.cfg = run
	if (run as Dictionary).has("path"):
		d._setup_path(run)
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
				if str(p.get("path", "")) != d.path_id:  # a path's packs belong to its run only (they are at its tempo); the main run never loads them
					continue
				d.packs[str(p["id"])] = p
	var assign: Dictionary = {}
	for m in music.get("nodes", []):
		assign[str(m["id"])] = m
	d._load_arrangements(arrangements_dir, assign)
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
		node["ending"] = str(node.get("ending", ""))
		var m: Dictionary = assign.get(id, {})
		if m.is_empty():
			d.errors.append("music.json has no entry for node %s" % id)
		node["audio"] = str(m.get("audio", ""))
		node["chart"] = str(m.get("chart", ""))
		node["arrangement"] = ""
		node["sections"] = []
		node["treatment"] = str(m.get("treatment", "none"))
		node["temporary"] = bool(m.get("temporary", false))
		d.nodes[id] = node
		d.node_order.append(id)
		if m.has("arrangement"):
			d._resolve_arrangement(id, m)
	for id in assign:
		if not d.nodes.has(id):
			d.errors.append("music.json lists node %s that run.json does not have" % id)
	d._validate()
	d._load_hotspots(hotspots_dir)
	return d


## A path's run.json: its `path` block is checked, and the sections it leaves out (judgement, energy, stages, mix, effects, treatments) are the main run's.
func _setup_path(run: Dictionary) -> void:
	var pi: Variant = run["path"]
	if typeof(pi) != TYPE_DICTIONARY:
		errors.append("run.json: path must be an object {id, title, entry_from, returns_to}")
		return
	path_info = pi
	path_id = str(path_info.get("id", ""))
	if path_id == "" or not path_id.is_valid_identifier():
		errors.append("run.json path.id '%s' is not an identifier" % path_id)
		path_id = "?"
	for k in ["title", "entry_from"]:
		if str(path_info.get(k, "")) == "":
			errors.append("run.json path.%s is missing" % k)
	if str(path_info.get("returns_to", "")) != "warehouse":
		errors.append("run.json path.returns_to must be \"warehouse\" (the only run a path returns to)")
	var base: Variant = _json(RUN_PATH, errors)
	if typeof(base) == TYPE_DICTIONARY:
		for k in INHERITED:
			if not run.has(k) and (base as Dictionary).has(k):
				run[k] = (base as Dictionary)[k].duplicate(true) if typeof(base[k]) in [TYPE_DICTIONARY, TYPE_ARRAY] else base[k]


func is_path() -> bool:
	return path_id != ""


## Reads the arrangements and the mix recipes (only when some scene names an arrangement).
func _load_arrangements(dir_path: String, assign: Dictionary) -> void:
	var wanted := false
	for id in assign:
		if (assign[id] as Dictionary).has("arrangement"):
			wanted = true
	if not wanted:
		return
	var rc: Variant = _json(RECIPES_PATH, errors)
	if typeof(rc) == TYPE_DICTIONARY:
		recipes = rc.get("recipes", {})
	var dir := DirAccess.open(dir_path)
	if dir == null:
		errors.append("%s: arrangements folder missing" % dir_path)
		return
	for f in dir.get_files():
		if f.get_extension() == "json":
			var a: Variant = _json(dir_path.path_join(f), errors)
			if typeof(a) == TYPE_DICTIONARY:
				arrangements[str(a.get("id", f.get_basename()))] = a


## A scene that names an arrangement plays a 16-bar window of it: `slot` k (default 0) is bars 16k+1 to 16k+16 (wrapping), one 16-bar section or two 8-bar ones.
## `alternates` lists other arrangements of the same family; the per-run seed picks between the scene's arrangement and its alternates (the same seed, the same pick).
## node.sections is [{bars, role, pack, mix, gains, start_beat, beats, fills}] over the 64-beat phase; node.audio and node.chart become the first section's pack, so the route
## lock compares the chart pack of block 0 exactly as for a plain scene.
func _resolve_arrangement(id: String, m: Dictionary) -> void:
	var node: Dictionary = nodes[id]
	var ids: Array = [str(m["arrangement"])]
	ids.append_array(m.get("alternates", []))
	var fams := {}
	for a in ids:
		if not arrangements.has(str(a)):
			errors.append("node %s: arrangement '%s' does not exist" % [id, a])
			return
		fams[str(arrangements[str(a)].get("family", ""))] = true
	if fams.size() > 1:
		errors.append("node %s: its arrangement and alternates are of several families (%s)" % [id, ", ".join(PackedStringArray(fams.keys()))])
		return
	var pick := 0 if ids.size() == 1 else absi(("%d:%s" % [seed_value, id]).hash()) % ids.size()
	var arr: Dictionary = arrangements[str(ids[pick])]
	var total := int(arr.get("bars", 0))
	var phase_bars := int(cfg.get("timing", {}).get("phase_beats", 64)) / 4
	if total <= 0 or total % phase_bars != 0:
		errors.append("node %s: arrangement %s has %d bars, a multiple of %d is needed (use \"run\")" % [id, arr.get("id", "?"), total, phase_bars])
		return
	var first_bar := (int(m.get("slot", 0)) * phase_bars) % total
	var sections: Array = []
	var bar := 0
	for s in arr.get("sections", []):
		var b := int(s.get("bars", 0))
		if bar >= first_bar and bar < first_bar + phase_bars:
			if bar + b > first_bar + phase_bars:
				errors.append("node %s: a %d-bar section of %s straddles the phase (slot %d)" % [id, b, arr["id"], int(m.get("slot", 0))])
				return
			if not s.has("pack"):
				errors.append("node %s: section of %s plays library stems, which the run cannot play yet (packs only)" % [id, arr["id"]])
				return
			var mix: Variant = s.get("mix", "full")
			var gains: Dictionary = {}
			if typeof(mix) == TYPE_STRING:
				if not recipes.has(str(mix)):
					errors.append("node %s: mix recipe '%s' is not in %s" % [id, mix, RECIPES_PATH])
					return
				gains = (recipes[str(mix)] as Dictionary).duplicate()
			elif typeof(mix) == TYPE_DICTIONARY:
				gains = (mix as Dictionary).duplicate()
			sections.append({"bars": b, "role": str(s.get("role", "")), "pack": str(s["pack"]), "mix": str(mix), "gains": {"drums": float(gains.get("drums", 1.0)),
				"bass": float(gains.get("bass", 1.0)), "other": float(gains.get("other", 1.0))}, "start_beat": (bar - first_bar) * 4, "beats": b * 4, "fills": s.get("fills", [])})
		bar += b
	if sections.is_empty():
		errors.append("node %s: arrangement %s has no section in bars %d to %d" % [id, arr["id"], first_bar + 1, first_bar + phase_bars])
		return
	for s in sections:
		if not packs.has(str(s["pack"])):
			errors.append("node %s: section pack '%s' of arrangement %s does not exist" % [id, s["pack"], arr["id"]])
			return
		var ph := int(packs[str(s["pack"])]["phrase_beats"])
		if int(s["beats"]) % ph != 0:
			errors.append("node %s: the %d-beat phrase of pack %s does not tile its %d-bar section" % [id, ph, s["pack"], int(s["bars"])])
	node["arrangement"] = str(arr["id"])
	node["sections"] = sections
	node["audio"] = str(sections[0]["pack"])
	node["chart"] = str(sections[0]["pack"])


## The section of scene `id` playing at phase beat `beat` ({} for a scene without an arrangement).
func section_at(id: String, beat: float) -> Dictionary:
	var secs: Array = nodes[id].get("sections", [])
	for i in range(secs.size() - 1, -1, -1):
		if beat >= float(secs[i]["start_beat"]) - 1e-6:
			return secs[i]
	return {}


## The pack whose chart is played at phase beat `beat` of scene `id`: the section playing then, else the scene's chart pack.
func chart_pack_at(id: String, beat: float) -> String:
	var s := section_at(id, beat)
	return str(s["pack"]) if not s.is_empty() else str(nodes[id]["chart"])


## The phase beat the section playing at `beat` began on (0 for a scene without an arrangement).
func section_start_at(id: String, beat: float) -> int:
	var s := section_at(id, beat)
	return int(s["start_beat"]) if not s.is_empty() else 0


static func _json(path: String, errors: Array) -> Variant:
	if not FileAccess.file_exists(path):
		errors.append("%s not found" % path)
		return null
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if v == null:
		errors.append("%s is not valid JSON" % path)
	return v


## The name a route button shows: the room for a path inside the world, the world's title for a world exit.
func route_title(from_id: String, to_id: String) -> String:
	if not nodes.has(to_id):
		return to_id
	var t: Dictionary = nodes[to_id]
	return str(t["title"]) if str(t["world"]) == str(nodes[from_id]["world"]) else str(t["world_title"])


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
	_validate_casts(errors)
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
			errors.append("pack %s is %d BPM, the run is %d" % [pid, int(p["bpm"]), int(tm.get("bpm", 174))])
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
	if is_path():
		_validate_path_graph()


func _validate_routes(id: String, n: Dictionary) -> void:
	var routes: Array = n["next"]
	var need := 2 if bool(n["exit_scene"]) and not is_path() else 1  # (a path's exit scene may lead to a single world)
	if routes.size() < need:
		errors.append("scene %s needs at least %d route%s" % [id, need, "s" if need > 1 else ""])
	var dirs := {}
	for e in routes:
		var to := str(e["to"])
		if HotspotContract.is_run_route(to):  # an ending's way back to the main run
			if not is_path() or str(n["ending"]) == "":
				errors.append("scene %s: the route '%s' is only for an ending scene of a path" % [id, to])
			if routes.size() != 1:
				errors.append("scene %s: an ending scene has the one route '%s'" % [id, to])
			if dirs.has(str(e["dir"])):
				errors.append("scene %s: two routes use the direction %s" % [id, e["dir"]])
			dirs[str(e["dir"])] = true
			if not (n.get("rail", {}) as Dictionary).get("exits", {}).has(str(e["dir"])):
				errors.append("scene %s: the route %s has no exit doorway in rail.exits" % [id, e["dir"]])
			continue
		if not nodes.has(to):
			errors.append("scene %s: route to unknown scene %s" % [id, to])
			continue
		var t: Dictionary = nodes[to]
		var same_world := str(t["world"]) == str(n["world"])
		if bool(n["exit_scene"]):
			if same_world and not bool(e.get("loop", false)) and not is_path():  # (a path's exit scene may also lead on inside its world)
				errors.append("exit scene %s: the route to %s stays in the world; mark it \"loop\": true or lead to another world" % [id, to])
			if not bool(t["entry"]) and not (is_path() and same_world):
				errors.append("exit scene %s: the route to %s must lead to the entry scene of a world" % [id, to])
			var nd := int(t["depth"])
			if not same_world and nd != mini(int(n["depth"]) + 1, 99) and not (tier_of(int(n["depth"])) == TIERS and nd == int(n["depth"])):
				errors.append("exit scene %s (depth %d): route to %s at depth %d (world exits go one level deeper, or stay at the last depth)" % [id, int(n["depth"]), to, nd])
		else:
			if not same_world:
				errors.append("scene %s: the route to %s leaves the world, only the exit scene may" % [id, to])
			elif bool(t["entry"]) and not bool(e.get("loop", false)) and not is_path():  # (a path world may have several entries: a cycle is caught by the graph check)
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
		if is_path():  # a path world: several entry scenes and exit scenes are allowed; its id stays an entry (the first) and it needs a way out (an exit scene or an ending)
			if entries.is_empty() or not entries.has(w):
				errors.append("world %s: the world's own id must be one of its entry scenes (entries: %s)" % [w, ", ".join(PackedStringArray(entries))])
			var terminals := scenes.filter(func(i: String) -> bool: return _terminal(i))
			if terminals.is_empty() and not scenes.is_empty():
				errors.append("world %s has no exit scene and no ending" % w)
		else:
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


## An exit scene (leaves the world) or an ending (leaves the path): where a world's scenes must all lead.
func _terminal(id: String) -> bool:
	return bool(nodes[id]["exit_scene"]) or str(nodes[id]["ending"]) != ""


## A path as a whole: every scene reaches an ending over all its routes, an ending's route is the way back, the start scene is an entry.
func _validate_path_graph() -> void:
	if nodes.has(start_node()) and not bool(nodes[start_node()]["entry"]):
		errors.append("path %s: start_node %s must be an entry scene" % [path_id, start_node()])
	var endings: Array = node_order.filter(func(i: String) -> bool: return str(nodes[i]["ending"]) != "")
	if endings.is_empty():
		errors.append("path %s has no ending scene (a scene with \"ending\": \"<name>\")" % path_id)
	var names := {}
	for e in endings:
		var nm := str(nodes[e]["ending"])
		if names.has(nm) or not nm.is_valid_identifier():
			errors.append("path %s: ending '%s' of %s is not a unique identifier" % [path_id, nm, e])
		names[nm] = true
		var nx: Array = nodes[e]["next"]
		if nx.size() != 1 or not HotspotContract.is_run_route(str(nx[0]["to"])):
			errors.append("path %s: the ending scene %s must have the one route \"run:warehouse\"" % [path_id, e])
	for id in node_order:
		if not _reaches_ending(str(id), {}):
			errors.append("scene %s cannot reach an ending of path %s" % [id, path_id])


func _reaches_ending(id: String, seen: Dictionary) -> bool:
	if str(nodes[id]["ending"]) != "":
		return true
	seen[id] = true
	for e in nodes[id]["next"]:
		var to := str(e["to"])
		if nodes.has(to) and not seen.has(to) and _reaches_ending(to, seen):
			return true
	return false


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
	if _terminal(id) if is_path() else bool(nodes[id]["exit_scene"]):
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


## The acting contract's cast lines (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3b, 2.3c): the `cast` of every scene and of every cinematic in run.json is checked against its scene's map.
func _validate_casts(out: Array) -> void:
	for id in node_order:
		var n: Dictionary = nodes[id]
		if n.has("cast"):
			validate_cast_lines(n, n["cast"], "scene %s" % id, out)
		_validate_stage_fx(id, n, out)
	var cines: Dictionary = cfg.get("cinematics", {})
	for name in cines:
		var c: Variant = cines[name]
		if typeof(c) != TYPE_DICTIONARY or not (c as Dictionary).has("cast"):
			continue
		var wd: Dictionary = worlds.get(str((c as Dictionary).get("world", "")), {})
		if wd.is_empty():
			out.append("cinematic %s: cast needs the cinematic's `world`" % name)
			continue
		HotspotContract.validate_cast(c["cast"], "cinematic %s" % name, HotspotContract.map_index(str(wd["map"])), out, HotspotContract.CINE_CAST_LAST_BEAT)


## A scene may switch set pieces (`pieces`: {on, off}, applied at its downbeat) and stage its blocks (`block_fx`: [{block 0..3, pass?, miss?}] where each side is {pieces?, cast?}: what the block's result
## does at its boundary, docs/CONTINUOUS_RUN.md "Paths": the Golgotha rule). Cast lines there use `at_beat` 0 (the boundary) and the same conditions as a scene's.
func _validate_stage_fx(id: String, n: Dictionary, out: Array) -> void:
	var idx := HotspotContract.map_index(str(n["map"]))
	if n.has("pieces"):
		HotspotContract.validate_pieces(n["pieces"], "scene %s pieces" % id, idx, out)
	if not n.has("block_fx"):
		return
	if typeof(n["block_fx"]) != TYPE_ARRAY:
		out.append("scene %s: block_fx must be a list" % id)
		return
	for fx in n["block_fx"]:
		if typeof(fx) != TYPE_DICTIONARY or not (fx as Dictionary).has("block") or int(fx["block"]) < 0 or int(fx["block"]) > 3:
			out.append("scene %s: a block_fx entry needs block 0 to 3" % id)
			continue
		for side in ["pass", "miss"]:
			if not fx.has(side):
				continue
			var w := "scene %s block_fx %d %s" % [id, int(fx["block"]), side]
			for k in (fx[side] as Dictionary):
				if str(k) not in ["pieces", "cast"]:
					out.append("%s: '%s' is not a field (pieces, cast)" % [w, k])
			if (fx[side] as Dictionary).has("pieces"):
				HotspotContract.validate_pieces(fx[side]["pieces"], w + " pieces", idx, out)
			if (fx[side] as Dictionary).has("cast"):
				HotspotContract.validate_cast(fx[side]["cast"], w, idx, out, 0.0)


## Checks `lines` (a scene node's `cast`) against the map of scene node `n`.
func validate_cast_lines(n: Dictionary, lines: Variant, where: String, out: Array) -> void:
	HotspotContract.validate_cast(lines, where, HotspotContract.map_index(str(n["map"])), out)


## The scenes of a world in file order.
func scenes_of(world: String) -> Array:
	return node_order.filter(func(i: String) -> bool: return str(nodes[i]["world"]) == world)


func entry_of(world: String) -> String:
	if nodes.has(world) and bool(nodes[world]["entry"]) and str(nodes[world]["world"]) == world:
		return world
	for i in node_order:
		if str(nodes[i]["world"]) == world and bool(nodes[i]["entry"]):
			return str(i)
	return ""


# --- hotspots ---------------------------------------------------------------------------------------------------------------

## Loads content/run/hotspots/<world>.json for every world, normalises and validates it (HotspotContract). A scene with no authored hotspot gets one exit hotspot per route, anchored on the
## doorway the rail already knows (rail.exits), the first route the default: the run is playable and the old route graph reachable before a world's hotspots are authored.
func _load_hotspots(dir_path: String) -> void:
	var by_scene: Dictionary = {}
	for w in world_order:
		var path := dir_path.path_join("%s.json" % w)
		if not FileAccess.file_exists(path):
			continue
		var v: Variant = _json(path, errors)
		if typeof(v) != TYPE_DICTIONARY:
			continue
		if str(v.get("world", w)) != w:
			errors.append("%s: world '%s' is not '%s'" % [path, v.get("world", ""), w])
		for h in v.get("hotspots", []):
			if typeof(h) != TYPE_DICTIONARY:
				errors.append("%s: a hotspot is not an object" % path)
				continue
			var sid := str(h.get("scene", ""))
			if not nodes.has(sid) or str(nodes[sid]["world"]) != w:
				errors.append("%s: hotspot %s: scene '%s' is not a scene of world %s" % [path, h.get("id", ""), sid, w])
				continue
			if not by_scene.has(sid):
				by_scene[sid] = []
			by_scene[sid].append(HotspotContract.normalize(h, w, str(nodes[sid]["map"])))
	var start_e := float((cfg.get("energy", {}) as Dictionary).get("start", 60.0))
	for sid in node_order:
		var n: Dictionary = nodes[sid]
		if not by_scene.has(sid):
			hotspots[sid] = _synth_hotspots(sid, n)
			continue
		hotspots[sid] = by_scene[sid]
		hotspots_authored[sid] = true
		var routes: Array = []
		for e in n["next"]:
			routes.append(str(e["to"]))
		var required: Array = routes.duplicate()
		for h in by_scene[sid]:  # the wizard's way into the Bassment ("trial:<passage>") and a portal's way into a path ("path:<id>") are routes of their own kind
			var r := str((h.get("on_success", {}) as Dictionary).get("route", ""))
			if HotspotContract.is_path_route(r):
				_check_portal(sid, h, r)
				if not routes.has(r):
					routes.append(r)
			elif HotspotContract.is_trial_route(r):
				var num := r.trim_prefix(HotspotContract.TRIAL_PREFIX)
				if str(n.get("trial_gate", "")) == "":
					errors.append("scene %s hotspot %s: the route '%s' (the Bassment) is only for a scene with a trial_gate" % [sid, h["id"], r])
				elif not num.is_valid_int() or int(num) < 1:
					errors.append("scene %s hotspot %s: the route '%s' needs a passage number" % [sid, h["id"], r])
				else:
					routes.append(r)
		HotspotContract.validate_scene(by_scene[sid], {"where": "scene %s" % sid, "map": str(n["map"]), "world": str(n["world"]), "routes": routes, "start_energy": start_e, "cinematics": cfg.get("cinematics", {}),
			"default_route": str(n["next"][0]["to"]) if not (n["next"] as Array).is_empty() else "", "exit_routes_required": required}, errors)
		if str(n["ending"]) != "":  # an ending's default hotspot is the way back to the main run and marks the ending as reached
			var want_flag := "keep:path_%s_%s" % [path_id, n["ending"]]
			for h in by_scene[sid]:
				if bool(h["default"]) and not ((h["on_success"] as Dictionary).get("flags_set", []) as Array).has(want_flag):
					errors.append("scene %s hotspot %s: the default exit of an ending sets the flag '%s'" % [sid, h["id"], want_flag])
		var playable: Array = by_scene[sid].filter(func(h: Dictionary) -> bool: return not _portal_missing(sid, h))  # a portal into a path that is not written yet stays out of play (logged)
		hotspots[sid] = playable


## A portal (a hotspot whose success route is "path:<id>") follows the portal rules of docs/THREE_PATHS_AND_FACES_PLAN.md 3.3: a secret, pulsing, never the default, repeatable, failing to the default route
## with a small energy dip; only the main run has them.
func _check_portal(sid: String, h: Dictionary, route: String) -> void:
	var hw := "scene %s hotspot %s" % [sid, h["id"]]
	var pid := HotspotContract.path_of(route)
	if is_path():
		errors.append("%s: the route '%s': a path does not lead into another path" % [hw, route])
	if not pid.is_valid_identifier():
		errors.append("%s: the route '%s' needs a path id" % [hw, route])
	if str(h["kind"]) != "secret" or str((h["look"] as Dictionary)["available"]) != "pulse":
		errors.append("%s: a portal is a secret with look.available 'pulse'" % hw)
	if bool(h["default"]):
		errors.append("%s: a portal is never the default" % hw)
	if not bool(h["repeatable"]):
		errors.append("%s: a portal is repeatable" % hw)
	var f: Dictionary = h.get("on_failure", {})
	if str(f.get("route", "")) != "" or float(f.get("energy", 0.0)) >= 0.0:
		errors.append("%s: a portal that fails flickers out: no route (the scene's default exit takes over) and an energy cost" % hw)
	for key in ["on_failure"]:
		if HotspotContract.is_path_route(str((h.get(key, {}) as Dictionary).get("route", ""))):
			errors.append("%s: only on_success may lead into a path" % hw)


func _portal_missing(sid: String, h: Dictionary) -> bool:
	var r := str((h.get("on_success", {}) as Dictionary).get("route", ""))
	if not HotspotContract.is_path_route(r) or path_exists(HotspotContract.path_of(r)):
		return false
	skipped_portals.append({"hotspot": str(h["id"]), "scene": sid, "path": HotspotContract.path_of(r)})
	return true


func _synth_hotspots(sid: String, n: Dictionary) -> Array:
	var out: Array = []
	var first := true
	var default_to := str(n["next"][0]["to"]) if not (n["next"] as Array).is_empty() else ""
	for e in n["next"]:
		var dir := str(e["dir"])
		var wp := str((n.get("exits", {}) as Dictionary).get(dir, n.get("waypoint", "")))
		var h := {"id": "%s.exit_%s" % [sid, dir], "scene": sid, "kind": "exit", "anchor": {"waypoint": wp}, "dir": dir, "default": first,
			"look": {"available": "open", "selected": "ring", "committed": "flash"}, "on_success": {"route": str(e["to"])}, "on_failure": {"route": default_to}}
		out.append(HotspotContract.normalize(h, str(n["world"]), str(n["map"])))
		first = false
	return out


## The scene's hotspots in file order (normalised dictionaries).
func hotspots_of(scene_id: String) -> Array:
	return hotspots.get(scene_id, [])
