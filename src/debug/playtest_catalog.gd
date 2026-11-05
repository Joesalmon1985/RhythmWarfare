class_name PlaytestCatalog
extends RefCounted
## The Debug / Playtest scene list as pure data (docs/DEBUG_MODE.md): every playable scene of the main 174 BPM run and of every path that ships, and for each the IDENTITY of what plays and
## what is drawn, read from the same loaders the game plays from (RunData: run.json, music.json, pack.json of every pack, the arrangements; the art maps). Nothing here is hard-coded to a
## file layout: a pack's stems are found through its pack.json (`stems`, `loops.<voice>.source_file`), so a moved or recompressed stem changes nothing but the `path` it reports.
##
## scene_info(data, scene_id) -> {run, run_title, id, title, world, world_title, map, depth, tier, role, bpm, audio, mix, visual}; audio.sections is what plays when (one entry for a plain scene,
## the arrangement's sections otherwise), each with the pack, its stems named exactly as the owner's files are, and the chart (MIDI) files the cues come from.

const VOICES := [["drums", "Drums"], ["bass", "Bass"], ["other", "Synth"]]  # pack stem key -> the owner's file-name part ("Beat Shaper - C07-Synth")
const PATH_ORDER := ["gospel", "squadron", "ember"]
const MAPS_DIR := "res://content/story/maps"
const SOURCE_LABELS := {"owner": "OWNER'S LOOP", "owner_standin": "OWNER'S LOOP (stand-in, temporary)", "placeholder": "PLACEHOLDER (synthesised, temporary)"}
const SOURCE_TAGS := {"owner": "OWNER", "owner_standin": "OWNER stand-in", "placeholder": "PLACEHOLDER"}

const ROLES := {"drums": "drums", "bass": "bass", "other": "synth"}  # the pack stem key -> the role named in the labels

static var _maps: Dictionary = {}
static var _users_key := ""
static var _users: Dictionary = {}  # simplified stem path -> ["<run>/<scene>", ...] of the scenes that play it under the current arrangement choice and seed


# --- the list --------------------------------------------------------------------------------------------------------------------

## The run ids the list shows, in order: "main" (the 174 run), then the paths that exist on disk (the Gospel, Squadron and Ember first, any other, such as the stub, after).
## The stub is excluded from exports (export_presets.cfg), so it appears in the editor and in test runs only.
static func run_ids() -> Array:
	var ids: Array = ["main"]
	for p in PATH_ORDER:
		if RunData.path_exists(str(p)):
			ids.append(p)
	for p in RunData.path_ids():
		if not ids.has(p) and RunData.path_exists(str(p)):
			ids.append(p)
	return ids


static func load_run(run_id: String) -> RunData:
	return RunData.load_default() if run_id == "main" else RunData.load_path(run_id)


## Every run with its worlds and scenes: [{id, title, bpm, dev, data, errors, worlds: [{id, title, scenes: [scene ids in run order]}], scene_count}].
static func runs() -> Array:
	var out: Array = []
	for rid in run_ids():
		out.append(run_entry(str(rid), load_run(str(rid))))
	return out


static func run_entry(run_id: String, data: RunData) -> Dictionary:
	var worlds: Array = []
	var count := 0
	for w in data.world_order:
		var scenes: Array = []
		for id in data.node_order:
			if str(data.nodes[id]["world"]) == str(w):
				scenes.append(str(id))
		count += scenes.size()
		worlds.append({"id": str(w), "title": str(data.worlds[w].get("title", w)), "scenes": scenes})
	var title := "Main run (the 174 BPM story run)" if run_id == "main" else str(data.path_info.get("title", run_id))
	return {"id": run_id, "title": title, "bpm": int(data.cfg.get("timing", {}).get("bpm", 0)), "dev": bool(data.path_info.get("dev", false)), "data": data,
		"errors": data.errors, "worlds": worlds, "scene_count": count}


static func path_of(run_id: String) -> String:
	return "" if run_id == "main" else run_id


# --- one scene's identity ---------------------------------------------------------------------------------------------------------

static func scene_info(data: RunData, scene_id: String) -> Dictionary:
	if not data.nodes.has(scene_id):
		return {}
	var node: Dictionary = data.nodes[scene_id]
	var run_id := data.path_id if data.is_path() else "main"
	var depth := int(node["depth"])
	var audio := _audio(data, node)
	return {"run": run_id, "run_title": "Main run" if run_id == "main" else str(data.path_info.get("title", run_id)), "id": scene_id, "title": str(node["title"]), "world": str(node["world"]),
		"world_title": str(node["world_title"]), "map": str(node["map"]), "depth": depth, "tier": mini(depth, RunData.TIERS), "role": str(node.get("role", "")), "entry": bool(node["entry"]),
		"exit": bool(node["exit_scene"]), "bpm": int(data.cfg["timing"]["bpm"]), "phase_beats": int(data.cfg["timing"]["phase_beats"]), "laps": int(node.get("laps", 1)), "audio": audio, "mix": _mix(data, node), "visual": _visual(data, node)}


## "The 174 BPM main run" / path title, then the world and scene, for headings.
static func scene_heading(info: Dictionary) -> String:
	return "%s  >  %s  >  %s (%s)" % [str(info["run_title"]), str(info["world_title"]), str(info["title"]), str(info["id"])]


static func _pack_label(data: RunData, pack_id: String) -> String:
	return str(data.packs[pack_id].get("label", pack_id)) if data.packs.has(pack_id) else "(missing pack)"


## Which scenes play each stem file. Stems are shared between packs on disk (songs/packs/_shared/<voice>_<sha>.wav, tools/content/stems.py), so one file can serve several scenes: the debug labels name the owner's
## export (pack.json loops.<voice>.source_file) and list the other scenes that play the same file. Built once from every run's data (cached per arrangement choice and seed).
static func stem_users() -> Dictionary:
	var key := "%d/%d" % [RunData.arrangement_override, RunData.run_seed()]
	if key == _users_key:
		return _users
	_users = {}
	_users_key = key
	for rid in run_ids():
		var data := load_run(str(rid))
		for id in data.node_order:
			var node: Dictionary = data.nodes[id]
			var packs: Array = []
			for s in node.get("sections", []):
				packs.append(str(s["pack"]))
			if packs.is_empty():
				packs.append(str(node["audio"]))
			for pk in packs:
				if not data.packs.has(pk):
					continue
				var p: Dictionary = data.packs[pk]
				for vk in (p.get("stems", {}) as Dictionary):
					var path := str(p["dir"]).path_join(str(p["stems"][vk])).simplify_path()
					if not _users.has(path):
						_users[path] = []
					var who := "%s/%s" % [rid, id]
					if not (_users[path] as Array).has(who):
						(_users[path] as Array).append(who)
	return _users


## A pack's three stems and its chart files, named as the pack.json names them: {voices: {drums|bass|other: {label, role, file (the owner's export name), owner_name, shared_file, stem, path, exists, shared_with}}, charts: {drums, bass}, loop_beats, loop_s, ...}.
static func pack_identity(data: RunData, pack_id: String) -> Dictionary:
	var out := {"id": pack_id, "known": data.packs.has(pack_id), "label": _pack_label(data, pack_id), "voices": {}, "charts": {}, "problems": [], "placeholder": false, "profile": "", "bpm": 0, "loop_beats": 0, "loop_s": 0.0}
	if not data.packs.has(pack_id):
		(out["problems"] as Array).append("pack '%s' is not loaded" % pack_id)
		return out
	var p: Dictionary = data.packs[pack_id]
	out["placeholder"] = bool(p.get("placeholder", false))
	out["profile"] = str(p.get("profile", ""))
	out["bpm"] = int(p.get("bpm", 0))
	out["loop_beats"] = int(p.get("phrase_beats", 0))
	var bpm := float(p.get("bpm", data.cfg["timing"]["bpm"]))
	out["loop_s"] = snappedf(float(out["loop_beats"]) * 60.0 / maxf(bpm, 1.0), 0.01)
	var stems: Dictionary = p.get("stems", {})
	var loops: Dictionary = p.get("loops", {})
	for pair in VOICES:
		var key := str(pair[0])
		var rel := str(stems.get(key, ""))
		var path := str(p.get("dir", "")).path_join(rel) if rel != "" else ""
		var file := str((loops.get(key, {}) as Dictionary).get("source_file", ""))
		var exists := path != "" and ResourceLoader.exists(path)
		var owner_name := file
		if file == "":
			file = rel.get_file() if rel != "" else "(none)"
		elif file.to_lower() == "synthesised":  # a placeholder: no owner's export exists, so say which stem of which pack it is
			owner_name = ""
			file = "synthesised placeholder (%s: %s)" % [pack_id, key]
		if not exists:
			(out["problems"] as Array).append("%s stem of %s is missing (%s)" % [str(pair[1]), pack_id, path])
		(out["voices"] as Dictionary)[key] = {"label": str(pair[1]), "role": str(ROLES[key]), "file": file, "owner_name": owner_name, "shared_file": rel.get_file(), "stem": rel, "path": path, "exists": exists, "shared_with": []}
	var src: Dictionary = p.get("source", {}) if typeof(p.get("source", {})) == TYPE_DICTIONARY else {}
	var files: Dictionary = src.get("files", {}) if typeof(src.get("files", {})) == TYPE_DICTIONARY else {}
	for pair in VOICES.slice(0, 2):  # the cues come from the Drums and Bass MIDI
		var key := str(pair[0])
		var name := str(pair[1])
		var mid := ""
		if files.has(name) and typeof(files[name]) == TYPE_DICTIONARY:
			mid = str((files[name] as Dictionary).get("mid", ""))
		elif files.has("midi") and typeof(files["midi"]) == TYPE_DICTIONARY:
			mid = str((files["midi"] as Dictionary).get(key, ""))
		(out["charts"] as Dictionary)[key] = mid if mid != "" else "(no MIDI named)"
	return out


static func _section(data: RunData, from_beat: float, beats: float, pack_id: String, chart_id: String, role: String, recipe: String, gains: Dictionary, tier: int) -> Dictionary:
	var ident := pack_identity(data, pack_id)
	var chart := ident if chart_id == pack_id else pack_identity(data, chart_id)
	return {"from_beat": from_beat, "beats": beats, "pack": pack_id, "chart_pack": chart_id, "role": role, "recipe": recipe, "recipe_gains": gains, "tier": tier, "audio": ident, "chart": chart}


static func _audio(data: RunData, node: Dictionary) -> Dictionary:
	var tier := mini(int(node["depth"]), RunData.TIERS)
	var phase_beats := float(data.cfg["timing"]["phase_beats"])
	var sections: Array = []
	var raw: Array = node.get("sections", [])
	if raw.is_empty():
		sections.append(_section(data, 0.0, phase_beats, str(node["audio"]), str(node["chart"]), "", "", {}, tier))
	else:
		for s in raw:
			sections.append(_section(data, float(s["start_beat"]), float(s["beats"]), str(s["pack"]), str(s["pack"]), str(s["role"]), str(s["mix"]), s["gains"], tier))
	var users := stem_users()
	for s in sections:  # which other scenes play the same stem files
		for vk in (s["audio"]["voices"] as Dictionary):
			var v: Dictionary = s["audio"]["voices"][vk]
			var others: Array = []
			var me := "%s/%s" % [data.path_id if data.is_path() else "main", str(node["id"])]
			for who in users.get(str(v["path"]).simplify_path(), []):
				if str(who) != me and not others.has(who):
					others.append(who)
			v["shared_with"] = others
	var packs: Array = []
	var problems: Array = []
	var placeholder := false
	for s in sections:
		for key in ["pack", "chart_pack"]:
			if not packs.has(s[key]):
				packs.append(s[key])
		for ident in [s["audio"], s["chart"]]:
			placeholder = placeholder or bool(ident["placeholder"])
			for pr in ident["problems"]:
				if not problems.has(pr):
					problems.append(pr)
	var temporary := bool(node["temporary"]) or placeholder
	var source := "placeholder" if placeholder else ("owner_standin" if bool(node["temporary"]) else "owner")
	var blocks: Array = []
	for b in 4:
		var beat := float(b) * float(data.cfg["timing"]["block_beats"])
		var sec := sections[0] as Dictionary
		for s in sections:
			if beat >= float(s["from_beat"]) - 1e-6:
				sec = s
		blocks.append({"block": b + 1, "from_beat": beat, "pack": str(sec["pack"]), "chart_pack": str(sec["chart_pack"]), "tier": tier})
	return {"source": source, "source_label": SOURCE_LABELS[source], "source_tag": SOURCE_TAGS[source], "temporary": temporary, "arrangement": str(node.get("arrangement", "")), "family": str(node.get("family", "")),
		"arrangement_ids": node.get("arrangement_ids", []), "arrangement_pick": int(node.get("arrangement_pick", 0)), "seed": data.seed_value,
		"treatment": str(node["treatment"]), "tier": tier, "sections": sections, "packs": packs, "blocks": blocks, "problems": problems, "switches": sections.size() > 1}


static func _mix(data: RunData, node: Dictionary) -> Dictionary:
	var m: Dictionary = data.cfg.get("mix", {})
	var stages: Array = []
	for s in data.cfg["stages"]:
		stages.append({"id": str(s["id"]), "label": str(s["label"]), "cue": str(s["cue"]), "gains": s["gains"]})
	var tr: Dictionary = data.cfg.get("treatments", {}).get(str(node["treatment"]), {})
	return {"stages": stages, "gain_db": float(m.get("gain_db", 0.0)), "bass_bus": node["bass_bus"], "recipe_bass_floor": float(m.get("recipe_bass_floor", 0.0)), "carry": m.get("carry_bass", {}),
		"dip_gain": float(m.get("dip_gain", RunAudio.DIP_GAIN)), "dip_beats": float(m.get("dip_beats", RunAudio.DIP_BEATS)), "ramp_s": float(m.get("ramp_s", 0.35)), "treatment": str(node["treatment"]), "treatment_def": tr}


# --- the visual -------------------------------------------------------------------------------------------------------------------

## An art map reduced to what the list needs: sectors by id, the sector each waypoint is in, the actors homed in each sector, the set pieces.
static func map_index(map_id: String) -> Dictionary:
	if _maps.has(map_id):
		return _maps[map_id]
	var out := {"found": false, "sectors": {}, "waypoint_sector": {}, "homes": {}, "pieces": []}
	var path := MAPS_DIR.path_join(map_id + ".json")
	if FileAccess.file_exists(path):
		var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if typeof(v) == TYPE_DICTIONARY:
			out["found"] = true
			for s in (v as Dictionary).get("sectors", []):
				(out["sectors"] as Dictionary)[str(s["id"])] = {"room": str(s.get("room", "")), "sky": str(s.get("sky", "")), "light": float(s.get("light", 1.0)), "tint": str(s.get("tint", "")),
					"fog": s.get("fog", {})}
			for w in (v as Dictionary).get("waypoints", []):
				(out["waypoint_sector"] as Dictionary)[str(w["id"])] = str(w.get("sector", ""))
			for h in (v as Dictionary).get("homes", []):
				var sec := str(h.get("sector", ""))
				if not (out["homes"] as Dictionary).has(sec):
					(out["homes"] as Dictionary)[sec] = []
				((out["homes"] as Dictionary)[sec] as Array).append(str(h["actor"]))
			for t in (v as Dictionary).get("things", []):
				var pc := str(t.get("piece", ""))
				if pc != "" and not (out["pieces"] as Array).has(pc):
					(out["pieces"] as Array).append(pc)
	_maps[map_id] = out
	return out


static func _visual(data: RunData, node: Dictionary) -> Dictionary:
	var map_id := str(node["map"])
	var mi := map_index(map_id)
	var view := str(node.get("waypoint", ""))
	var sector := str((mi["waypoint_sector"] as Dictionary).get(view, ""))
	var sec: Dictionary = (mi["sectors"] as Dictionary).get(sector, {})
	var sky := str(sec.get("sky", ""))
	var tod := ("%s sky" % sky) if sky != "" else "indoors (no sky)"
	var pieces_on: Array = []
	var on_v: Variant = (node.get("pieces", {}) as Dictionary).get("on", [])
	if typeof(on_v) == TYPE_ARRAY:
		for p in on_v:
			pieces_on.append(str(p))
	var pieces_off: Array = []
	for p in mi["pieces"]:
		if not pieces_on.has(p):
			pieces_off.append(p)
	var cast: Array = []
	for c in node.get("cast", []):
		var a := str((c as Dictionary).get("actor", ""))
		if a != "" and not cast.has(a):
			cast.append(a)
	var crowd: Array = (mi["homes"] as Dictionary).get(sector, []).duplicate()
	var hot: Array = []
	var flags: Array = []
	for h in data.hotspots_of(str(node["id"])):
		var d: Dictionary = h
		var acting: Dictionary = d.get("acting", {}) if typeof(d.get("acting", {})) == TYPE_DICTIONARY else {}
		hot.append({"id": str(d["id"]), "kind": str(d.get("kind", "")), "route": str((d.get("on_success", {}) as Dictionary).get("route", "")), "actor": str(acting.get("actor", "")),
			"look": str((d.get("look", {}) as Dictionary).get("available", "")), "default": bool(d.get("default", false))})
		for f in (d.get("available", {}) as Dictionary).get("flags_all", []):
			if not flags.has(str(f)):
				flags.append(str(f))
	var fog: Dictionary = sec.get("fog", {}) if typeof(sec.get("fog", {})) == TYPE_DICTIONARY else {}
	return {"map": map_id, "map_found": bool(mi["found"]), "stage": "Stage_" + map_id, "view": view, "sector": sector, "room": str(sec.get("room", "")), "sky": sky, "time_of_day": tod,
		"light": float(sec.get("light", 1.0)), "tint": str(sec.get("tint", "")), "fog": str(fog.get("color", "")), "pieces_on": pieces_on, "pieces_off": pieces_off, "cast": cast, "crowd": crowd,
		"hotspots": hot, "flags_needed": flags}


# --- text -------------------------------------------------------------------------------------------------------------------------

## The pack ids a scene's phase plays in order, with ">" where the arrangement switches: "lv1_warehouse > lv1_warehouse_v1".
static func packs_line(info: Dictionary) -> String:
	var parts: Array = []
	for s in info["audio"]["sections"]:
		if parts.is_empty() or parts[parts.size() - 1] != str(s["pack"]):
			parts.append(str(s["pack"]))
	return " > ".join(PackedStringArray(parts))


## The row's compact audio line: the pack ids, the set names as the owner's files have them, and where it comes from.
static func row_audio_line(info: Dictionary) -> String:
	var a: Dictionary = info["audio"]
	var labels: Array = []
	for s in a["sections"]:
		var l := str((s["audio"] as Dictionary)["label"])
		if not labels.has(l):
			labels.append(l)
	return "%s   [%s]   %s" % [" + ".join(PackedStringArray(labels)), packs_line(info), str(a["source_tag"]) + (" (temp)" if a["temporary"] and a["source"] != "placeholder" else "")]


static func gains_text(g: Dictionary) -> String:
	return "drums %.2f  bass %.2f  synth %.2f" % [float(g.get("drums", 0.0)), float(g.get("bass", 0.0)), float(g.get("other", 0.0))]


static func bus_text(bb: Dictionary) -> String:
	if not bool(bb.get("enabled", false)):
		return "off (the bass goes straight to its bus)"
	return "high-pass %.0f Hz, shelf %+.1f dB at %.0f Hz, drive %.2f, pre %+.1f dB, post %+.1f dB" % [float(bb["highpass_hz"]), float(bb["shelf_db"]), float(bb["shelf_hz"]), float(bb["drive"]), float(bb["pre_gain_db"]), float(bb["gain_db"])]


## "; also played in n other scenes: a, b" for a stem file that other scenes use too, else "; used by no other scene".
static func shared_text(v: Dictionary) -> String:
	var w: Array = v.get("shared_with", [])
	if w.is_empty():
		return "; used by no other scene"
	return "; also played in %d other scenes: %s" % [w.size(), ", ".join(PackedStringArray(w))]


## The audio detail as [[heading, [lines]], ...]; the detail screen draws it and `identity_text` joins it.
static func audio_sections(info: Dictionary) -> Array:
	var a: Dictionary = info["audio"]
	var out: Array = []
	var laps := int(info.get("laps", 1))
	var head: Array = ["Source: %s" % str(a["source_label"]), "Tempo %d BPM, %s, difficulty tier %d%s" % [int(info["bpm"]), ("phase %d beats" % int(info["phase_beats"])) if laps <= 1 else ("%d laps of %d beats (%d beats, the route window only in the last)" % [laps, int(info["phase_beats"]), laps * int(info["phase_beats"])]), int(a["tier"]), "" if str(a["arrangement"]) == "" else ", arrangement %s" % str(a["arrangement"])]]
	if (a["arrangement_ids"] as Array).size() > 1:
		head.append("Arrangement %d of %d (%s): %s" % [int(a["arrangement_pick"]) + 1, (a["arrangement_ids"] as Array).size(), ", ".join(PackedStringArray(a["arrangement_ids"])),
			("chosen in the Debug options" if RunData.arrangement_override >= 0 else "picked by the per-run seed %d, as the game does" % int(a["seed"]))])
	if str(a["family"]) != "":
		head.append("Music family %s (the bass carries between scenes of one family)" % str(a["family"]))
	if str(a["treatment"]) != "none":
		head.append("Sound treatment: %s" % str(a["treatment"]))
	out.append(["AUDIO", head])
	var i := 0
	for s in a["sections"]:
		i += 1
		var lines: Array = []
		var ident: Dictionary = s["audio"]
		lines.append("Pack %s  (%s)   loop %d beats, %.2f s%s" % [str(s["pack"]), str(ident["label"]), int(ident["loop_beats"]), float(ident["loop_s"]), "   PLACEHOLDER" if bool(ident["placeholder"]) else ""])
		for pair in VOICES:
			var v: Dictionary = (ident["voices"] as Dictionary).get(str(pair[0]), {})
			lines.append("   %s (%s): %s%s" % [str(pair[1]), str(v.get("role", "?")), str(v.get("file", "?")), "" if bool(v.get("exists", false)) else "   (STEM MISSING)"])
			lines.append("      file %s%s" % [str(v.get("shared_file", "?")), shared_text(v)])
		var chart: Dictionary = s["chart"]
		if str(s["chart_pack"]) != str(s["pack"]):
			lines.append("Chart pack %s (%s)" % [str(s["chart_pack"]), str(chart["label"])])
		lines.append("Cues (tier %d): drums from %s, bass from %s" % [int(s["tier"]), str((chart["charts"] as Dictionary).get("drums", "?")), str((chart["charts"] as Dictionary).get("bass", "?"))])
		if str(s["recipe"]) != "":
			lines.append("Section recipe '%s': %s" % [str(s["recipe"]), gains_text(s["recipe_gains"])])
		var title := "SECTION %d  beats %d to %d%s" % [i, int(s["from_beat"]), int(s["from_beat"] + s["beats"]), "  (%s)" % str(s["role"]) if str(s["role"]) != "" else ""] if a["switches"] else "PACK"
		out.append([title, lines])
	if a["switches"]:
		var bl: Array = []
		for b in a["blocks"]:
			bl.append("Block %d (beat %d): %s, tier %d" % [int(b["block"]), int(b["from_beat"]), str(b["chart_pack"]), int(b["tier"])])
		out.append(["CHART PACK PER BLOCK", bl])
	if not (a["problems"] as Array).is_empty():
		out.append(["PROBLEMS", a["problems"]])
	return out


static func mix_sections(info: Dictionary) -> Array:
	var m: Dictionary = info["mix"]
	var lines: Array = []
	for s in m["stages"]:
		lines.append("Stage %s (%s cues): %s" % [str(s["label"]), str(s["cue"]), gains_text(s["gains"])])
	lines.append("Run level %+.1f dB.  Bass bus: %s" % [float(m["gain_db"]), bus_text(m["bass_bus"])])
	var carry: Dictionary = m["carry"]
	lines.append("Bass carry: %s.  Recipe bass floor %.2f.  Hotspot dip %.2f for %.0f beats.  Ramp %.2f s" % [("%.2f for %.0f beats" % [float(carry.get("gain", 0.0)), float(carry.get("beats", 0.0))]) if float(carry.get("gain", 0.0)) > 0.0 else "off", float(m["recipe_bass_floor"]), float(m["dip_gain"]), float(m["dip_beats"]), float(m["ramp_s"])])
	if str(m["treatment"]) != "none":
		lines.append("Treatment %s: %s" % [str(m["treatment"]), JSON.stringify(m["treatment_def"])])
	return [["MIX IN FORCE", lines]]


static func visual_sections(info: Dictionary) -> Array:
	var v: Dictionary = info["visual"]
	var lines: Array = []
	lines.append("Map %s (stage %s)%s" % [str(v["map"]), str(v["stage"]), "" if bool(v["map_found"]) else "   (MAP FILE NOT FOUND)"])
	lines.append("View %s, sector %s, room %s" % [str(v["view"]), str(v["sector"]), str(v["room"])])
	lines.append("Light: %s, level %.2f, tint %s%s" % [str(v["time_of_day"]), float(v["light"]), str(v["tint"]) if str(v["tint"]) != "" else "none", (", fog " + str(v["fog"])) if str(v["fog"]) != "" else ""])
	lines.append("Pieces on: %s" % (", ".join(PackedStringArray(v["pieces_on"])) if not (v["pieces_on"] as Array).is_empty() else "none"))
	lines.append("Pieces off: %s" % (", ".join(PackedStringArray(v["pieces_off"])) if not (v["pieces_off"] as Array).is_empty() else "none"))
	lines.append("Cast (directed this scene): %s" % (", ".join(PackedStringArray(v["cast"])) if not (v["cast"] as Array).is_empty() else "none"))
	lines.append("Crowd homed in this room: %s" % (", ".join(PackedStringArray(v["crowd"])) if not (v["crowd"] as Array).is_empty() else "none"))
	var hl: Array = []
	for h in v["hotspots"]:
		hl.append("%s  (%s%s) -> %s%s" % [str(h["id"]), str(h["kind"]), (", " + str(h["actor"])) if str(h["actor"]) != "" else "", str(h["route"]), "  [default]" if bool(h["default"]) else ""])
	if hl.is_empty():
		hl.append("none")
	if not (v["flags_needed"] as Array).is_empty():
		hl.append("needs flags: " + ", ".join(PackedStringArray(v["flags_needed"])))
	return [["VISUAL", lines], ["HOTSPOTS ON OFFER", hl]]


## The whole identity as plain text (the detail screen's "Copy" button, and the tests).
static func identity_text(info: Dictionary) -> String:
	var lines: Array = [scene_heading(info)]
	for group in [audio_sections(info), mix_sections(info), visual_sections(info)]:
		for sec in group:
			lines.append("")
			lines.append(str(sec[0]))
			for l in sec[1]:
				lines.append(str(l))
	return "\n".join(PackedStringArray(lines))
