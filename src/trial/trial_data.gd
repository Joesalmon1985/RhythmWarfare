class_name TrialData
extends RefCounted
## The Deathtrap Dungeon opening's data (content/trial/passages.json): the passage links as the book verifies them, the text and scene of each passage,
## the rhythm phrases and the one encounter. validate() checks everything a run of it depends on; errors name the passage.

const PATH := "res://content/trial/passages.json"

var raw: Dictionary = {}
var passages: Dictionary = {}  # int passage -> entry
var phrases: Dictionary = {}
var encounters: Dictionary = {}
var scenes: Dictionary = {}
var start := 1
var errors: Array = []


static func load_default() -> TrialData:
	return load_file(PATH)


static func load_file(path: String, run_data: RunData = null) -> TrialData:
	var d := TrialData.new()
	if not FileAccess.file_exists(path):
		d.errors.append("%s not found" % path)
		return d
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(v) != TYPE_DICTIONARY:
		d.errors.append("%s is not a JSON object" % path)
		return d
	d.raw = v
	d.start = int(v.get("start", 1))
	for k in (v.get("passages", {}) as Dictionary):
		d.passages[int(k)] = v["passages"][k]
	d.phrases = v.get("phrases", {})
	d.encounters = v.get("encounters", {})
	d.scenes = v.get("scenes", {})
	d.validate(run_data if run_data != null else RunData.load_default())
	return d


func passage(n: int) -> Dictionary:
	return passages.get(n, {})


func choices(n: int) -> Array:
	return passage(n).get("choices", [])


func validate(run_data: RunData) -> void:
	if not passages.has(start):
		errors.append("start passage %d does not exist" % start)
	var music: Dictionary = raw.get("music", {})
	for key in ["audio", "chart"]:
		if not run_data.packs.has(str(music.get(key, ""))):
			errors.append("music.%s pack '%s' does not exist" % [key, music.get(key, "")])
	if not (run_data.cfg.get("treatments", {}) as Dictionary).has(str(music.get("treatment", "none"))):
		errors.append("music.treatment '%s' is not in run.json" % music.get("treatment", ""))
	for pid in phrases:
		var ph: Dictionary = phrases[pid]
		if str(ph.get("family", "")) not in ["drums", "bass"]:
			errors.append("phrase %s: family must be drums or bass" % pid)
		if int(ph.get("tier", 0)) < 1 or int(ph.get("tier", 0)) > RunData.TIERS:
			errors.append("phrase %s: tier must be 1 to %d" % [pid, RunData.TIERS])
		if int(ph.get("beats", 0)) < 4 or int(ph.get("beats", 0)) > 14:
			errors.append("phrase %s: beats must be 4 to 14 (a phrase fits inside one 16-beat block)" % pid)
	for n in passages:
		var p: Dictionary = passages[n]
		if not scenes.has(str(p.get("scene", ""))):
			errors.append("passage %d: scene '%s' is not defined" % [n, p.get("scene", "")])
		elif not FileAccess.file_exists(str(scenes[str(p["scene"])]["file"])) and not ResourceLoader.exists(str(scenes[str(p["scene"])]["file"])):
			errors.append("passage %d: scene file %s is missing" % [n, scenes[str(p["scene"])]["file"]])
		var cs: Array = p.get("choices", [])
		if cs.is_empty():
			errors.append("passage %d has no choices (an endpoint still offers a way out)" % n)
		for c in cs:
			var to: Variant = c.get("to", null)
			if to == null:
				if str(c.get("exit", "")) == "":
					errors.append("passage %d: choice '%s' has neither a destination nor an exit" % [n, c.get("label", "")])
			elif not passages.has(int(to)):
				errors.append("passage %d: choice '%s' leads to %d, which has no entry (add it, or make that passage an endpoint)" % [n, c.get("label", ""), int(to)])
			var ph: Variant = c.get("phrase", null)
			if ph != null and not phrases.has(str(ph)):
				errors.append("passage %d: choice '%s' uses phrase '%s', which is not defined" % [n, c.get("label", ""), ph])
			if c.has("encounter") and not encounters.has(str(c["encounter"])):
				errors.append("passage %d: encounter '%s' is not defined" % [n, c["encounter"]])
			if str(c.get("label", "")) == "" or str(c.get("book", "")) == "":
				errors.append("passage %d: every choice needs a label and the book's wording of the link" % n)
		if str(p.get("status", "")) not in ["BOOK_VERIFIED", "PROTOTYPE_ENDPOINT", "ADAPTED", "LEGACY"]:
			errors.append("passage %d: status must be BOOK_VERIFIED, PROTOTYPE_ENDPOINT, ADAPTED or LEGACY" % n)
	for eid in encounters:
		var e: Dictionary = encounters[eid]
		for key in ["portrait", "portrait_hit"]:
			if not ResourceLoader.exists(str(e.get(key, ""))) and not FileAccess.file_exists(str(e.get(key, ""))):
				errors.append("encounter %s: %s %s is missing" % [eid, key, e.get(key, "")])
		if str(e.get("placement", "")) != "ADAPTED" and str(e.get("placement", "")) != "BOOK":
			errors.append("encounter %s: placement must say ADAPTED or BOOK" % eid)


## Passages reachable from the start (a link map for tests and the docs).
func reachable() -> Array:
	var seen := {}
	var queue: Array = [start]
	while not queue.is_empty():
		var n: int = queue.pop_back()
		if seen.has(n) or not passages.has(n):
			continue
		seen[n] = true
		for c in choices(n):
			if c.get("to", null) != null:
				queue.append(int(c["to"]))
	var out: Array = seen.keys()
	out.sort()
	return out
