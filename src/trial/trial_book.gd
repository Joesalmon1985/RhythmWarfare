class_name TrialBook
extends RefCounted
## Composes the 400 passages of the whole dungeon from three files, hand-authored passages first:
##   content/trial/passages.json    the hand-authored passages (they win), phrases, scenes, encounters, music
##   content/trial/book_graph.json  for every passage 1 to 400: status, zone, kind (normal/death/victory), tier, default link, links (with where each came from), enemy, luck test
##   content/trial/book_text.json   a short original description per passage and a label per link target (tools/trial/build_book.py writes both graph and text)
## and one synthetic passage, 0, the one a lost fight leads to. Every passage ends up with the same shape the hand-authored ones have: scene, title, text, status, tier and choices
## [{label, to, book, phrase, consequence, default, src, ...}], where a choice may also carry `encounter` + `lives` (a fight), `test` {pass, fail} (a luck test: no retry) or `exit`.

const GRAPH_PATH := "res://content/trial/book_graph.json"
const TEXT_PATH := "res://content/trial/book_text.json"
const ZONE_TITLE := {"dd_entrance": "The Crystal Entrance", "dd_fork": "The Footprint Fork", "dd_galleries": "The Footprint Galleries", "dd_pit": "Throm's Pit", "dd_lower": "The Lower Route",
	"dd_trialmaster": "The Trialmaster's Complex", "dd_idol": "The Idol Cavern", "dd_grotto": "The Drowned Grotto", "dd_vaults": "The Sapphire Vaults", "dd_vault_inner": "The Inner Vault",
	"dd_service": "The Service Tunnels", "dd_mirror": "The Mirror Gallery", "dd_blood": "The Bloodbeast's Lair", "dd_grub": "The Grub Tunnels", "dd_troglodytes": "The Troglodyte Cavern",
	"dd_manticore": "The Manticore's Gate", "dd_igbut": "Igbut's Door"}
const SCENE_OF := {"dd_entrance": "entrance", "dd_fork": "fork", "dd_galleries": "gallery"}
const ENEMY_ART := {"giant_fly": "giant_fly", "manticore": "manticore", "bloodbeast": "bloodbeast", "poison_ivy": "poison_ivy", "flying_guardian": "flying_guardian",
	"cave_troll": "cave_troll", "throm": "throm_duel"}
const ENEMY_TINT := {"orc": Color(0.55, 0.85, 0.5), "hobgoblin": Color(0.9, 0.7, 0.4), "skeleton": Color(0.95, 0.95, 0.85), "pit_fiend": Color(1.0, 0.45, 0.35), "caveman": Color(0.8, 0.65, 0.5),
	"creature": Color(0.7, 0.55, 1.0), "scorpion": Color(0.9, 0.8, 0.4), "goblin": Color(0.6, 0.9, 0.6), "dwarf": Color(0.8, 0.6, 0.4), "minotaur": Color(0.85, 0.5, 0.35), "rock_grub": Color(0.9, 0.85, 0.6),
	"mirror_demon": Color(0.6, 0.8, 1.0), "guard_dog": Color(0.75, 0.7, 0.6)}
const LIVES := 3


## Adds the book's passages to `d` (hand-authored ones in d.passages are kept as they are). Returns the number composed.
static func compose(d: TrialData) -> int:
	if not FileAccess.file_exists(GRAPH_PATH):
		return 0
	var gv: Variant = JSON.parse_string(FileAccess.get_file_as_string(GRAPH_PATH))
	var tv: Variant = JSON.parse_string(FileAccess.get_file_as_string(TEXT_PATH)) if FileAccess.file_exists(TEXT_PATH) else {}
	if typeof(gv) != TYPE_DICTIONARY:
		d.errors.append("book_graph.json is not valid")
		return 0
	var graph: Dictionary = gv["passages"]
	var text: Dictionary = (tv as Dictionary).get("passages", {}) if typeof(tv) == TYPE_DICTIONARY else {}
	var n := 0
	for k in graph:
		var id := int(k)
		if d.passages.has(id):
			continue
		d.passages[id] = _entry(d, id, graph[k], text.get(k, {}))
		n += 1
	d.passages[0] = {"title": "Defeated", "scene": "death", "status": "SYNTHETIC", "kind": "death", "tier": 1,
		"text": "The creature is too much for you. Your adventure ends here, in the dark of the dungeon.",
		"choices": [{"label": "Wake in the Warehouse", "to": null, "exit": "warehouse", "book": "(defeat)", "phrase": null, "consequence": "", "default": true, "src": "synthetic"}]}
	return n


static func _entry(d: TrialData, id: int, g: Dictionary, t: Dictionary) -> Dictionary:
	var zone := str(g["zone"])
	var kind := str(g["kind"])
	var tier := int(g["tier"])
	var scene := "death" if kind == "death" else ("victory" if kind == "victory" else str(SCENE_OF.get(zone, zone)))
	var title := "%s  ·  %d" % [ZONE_TITLE.get(zone, "The Dungeon"), id]
	var body := str(t.get("text", ""))
	if body == "":
		body = "This passage's own text has not been written or verified yet. You are in %s." % str(ZONE_TITLE.get(zone, "the dungeon")).to_lower()
	var entry := {"title": title, "scene": scene, "status": str(g["status"]), "kind": kind, "tier": tier, "text": body, "text_source": str(t.get("how", "placeholder")), "choices": []}
	var labels: Dictionary = t.get("labels", {})
	if kind == "death":
		entry["choices"] = [{"label": "Wake in the Warehouse", "to": null, "exit": "warehouse", "book": "(death)", "phrase": null, "consequence": "", "default": true, "src": "synthetic"}]
		return entry
	if kind == "victory":
		entry["choices"] = [{"label": "Walk out into daylight", "to": null, "exit": "warehouse", "book": "(victory)", "phrase": null, "consequence": "", "default": true, "src": "synthetic"}]
		return entry
	var links: Array = g["links"]
	var def_to: int = int(links[int(g["default"])]["to"]) if not links.is_empty() else 0
	var choices: Array = []
	var luck: Dictionary = g.get("luck", {})
	var enemy: Dictionary = g.get("enemy", {})
	var luck_targets: Array = []
	if not luck.is_empty():
		for key in ["pass", "fail"]:
			if luck.get(key, null) != null:
				luck_targets.append(int(luck[key]))
	var win_to: Variant = g.get("win_to", null)
	var idx := 0
	var fight_done := false
	for l in links:
		var to := int(l["to"])
		if to in luck_targets and not luck_targets.is_empty():
			continue  # replaced by one luck-test choice below
		var label := str(labels.get(str(to), ""))
		if label == "":
			label = "Take the side passage" if l.get("side", false) else "Press on"
		var c := {"label": label, "to": to, "book": str(l.get("book", "(adapted)")), "src": str(l.get("src", "bridge")), "consequence": "",
			"phrase": _phrase(id, idx, tier)}
		if not enemy.is_empty() and not fight_done and (win_to == null or int(win_to) == to):
			fight_done = true
			c["label"] = "Fight the %s" % str(enemy["name"])
			c["encounter"] = str(enemy["id"])
			c["lives"] = LIVES
			c["phrase"] = "fight_t%d" % clampi(2 if int(enemy["skill"]) <= 7 else (3 if int(enemy["skill"]) <= 9 else 4), 2, 4)
			c["consequence"] = ""
			d.encounters[str(enemy["id"])] = d.encounters.get(str(enemy["id"]), _encounter(d, enemy))
		choices.append(c)
		idx += 1
	if not enemy.is_empty() and not fight_done and not choices.is_empty():
		choices[0]["label"] = "Fight the %s" % str(enemy["name"])
		choices[0]["encounter"] = str(enemy["id"])
		choices[0]["lives"] = LIVES
		choices[0]["phrase"] = "fight_t%d" % clampi(2 if int(enemy["skill"]) <= 7 else (3 if int(enemy["skill"]) <= 9 else 4), 2, 4)
		d.encounters[str(enemy["id"])] = d.encounters.get(str(enemy["id"]), _encounter(d, enemy))
	if not luck_targets.is_empty():
		var pass_to: int = int(luck["pass"]) if luck.get("pass", null) != null else (int(choices[0]["to"]) if not choices.is_empty() else int(luck["fail"]))
		var fail_to: int = int(luck["fail"]) if luck.get("fail", null) != null else pass_to
		choices.append({"label": "Trust to luck", "to": pass_to, "book": "(luck test)", "src": "pack", "consequence": "", "phrase": "luck", "test": {"pass": pass_to, "fail": fail_to}})
	if choices.is_empty() and not links.is_empty():
		choices.append({"label": "Press on", "to": int(links[0]["to"]), "book": "(adapted)", "src": "bridge", "consequence": "", "phrase": _phrase(id, 0, tier)})
	# the default: the choice that goes the way the graph's shortest route goes
	var di := 0
	for i in choices.size():
		var c2: Dictionary = choices[i]
		var tos: Array = [int(c2["to"])]
		if c2.has("test"):
			tos = [int(c2["test"]["pass"]), int(c2["test"]["fail"])]
		if def_to in tos:
			di = i
			break
	for i in choices.size():
		if i == di:
			choices[i]["default"] = true
	entry["choices"] = choices
	return entry


static func _phrase(id: int, idx: int, tier: int) -> String:
	if (id * 7 + idx * 3) % 4 == 0:
		return "p_b%d" % mini(tier, 3)
	return "p_d%d" % tier


static func _encounter(d: TrialData, enemy: Dictionary) -> Dictionary:
	var ident := str(enemy["id"])
	var art := str(ENEMY_ART.get(ident, ""))
	var name := str(enemy["name"])
	var e := {"name": name, "intro": "A %s bars the way." % name.to_lower(), "on_win": "The %s is beaten." % name.to_lower(),
		"on_fail": "The %s hurts you badly. Steady yourself and fight on." % name.to_lower(), "source": "adapted", "placement": "ADAPTED",
		"bestiary": "A %s (skill %d in the book's numbers)." % [name.to_lower(), int(enemy["skill"])]}
	if art != "":
		e["portrait"] = "res://assets/trial/art/%s_portrait_0.png" % art
		e["portrait_hit"] = "res://assets/trial/art/%s_portrait_1.png" % art
	else:
		e["portrait"] = "res://assets/trial/art/monster_0.png"
		e["portrait_hit"] = "res://assets/trial/art/monster_1.png"
		e["tint"] = ENEMY_TINT.get(ident, Color(0.7, 0.7, 0.7)).to_html()
	return e
