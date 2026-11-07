class_name RaveSave
extends RefCounted
## The bedsit and rave progress in the run save (docs/parallel-development/CONTRACTS.md sections 2 and 6), as pure static functions on the save's
## `data` dictionary. RunProgress (lead-owned) calls `migrate` on load and `new_run` from run_started(); the gameplay stream calls the rest. No file I/O here.
##
## Save version 3 adds three top-level keys to version 2:
##   bedsit_facing: "N" | "E" | "S" | "W"     the way the player faces in the bedsit (per run: a new run faces N)
##   rave_theme: "" | <theme id>               the rave the player is in ("" in the bedsit or the legacy run) (per run)
##   raves: {<theme>: {bass_fixed: bool, cloakroom_done: bool, bar_done: bool, race: {wins: int, runs: int, best: float}}}
##          the three puzzle flags are per run (cleared by new_run); `race` is kept across runs (a career record; best = fastest finish in song seconds, 0 = none)

const VERSION := 3
const FACINGS := ["N", "E", "S", "W"]  # clockwise: a right turn is +1
const THEMES := ["space", "magic", "dinos", "transport"]
const PUZZLES := ["bass_fixed", "cloakroom_done", "bar_done"]
const FLAG_PREFIX := "rave."  # an activity's flags_to_set entry "rave.<theme>.<puzzle>" sets that puzzle flag (section 4)


static func fresh_rave() -> Dictionary:
	return {"bass_fixed": false, "cloakroom_done": false, "bar_done": false, "race": {"wins": 0, "runs": 0, "best": 0.0}}


static func fresh_raves() -> Dictionary:
	var out := {}
	for th in THEMES:
		out[th] = fresh_rave()
	return out


## Brings a version 2 (or a damaged version 3) save's data up to version 3 in place: missing or malformed keys get their defaults, a known race record is
## kept. Returns the list of keys it had to add or repair.
static func migrate(data: Dictionary) -> Array:
	var fixed: Array = []
	if str(data.get("bedsit_facing", "")) not in FACINGS:
		data["bedsit_facing"] = "N"
		fixed.append("bedsit_facing")
	var th := str(data.get("rave_theme", "<none>"))
	if th != "" and th not in THEMES:
		data["rave_theme"] = ""
		fixed.append("rave_theme")
	if typeof(data.get("raves", null)) != TYPE_DICTIONARY:
		data["raves"] = {}
		fixed.append("raves")
	var raves: Dictionary = data["raves"]
	for t in THEMES:
		var r: Variant = raves.get(t, null)
		if typeof(r) != TYPE_DICTIONARY:
			raves[t] = fresh_rave()
			fixed.append("raves." + t)
			continue
		var d: Dictionary = r
		for p in PUZZLES:
			if typeof(d.get(p, null)) != TYPE_BOOL:
				d[p] = false
				fixed.append("raves.%s.%s" % [t, p])
		var race: Variant = d.get("race", null)
		if typeof(race) != TYPE_DICTIONARY:
			d["race"] = {"wins": 0, "runs": 0, "best": 0.0}
			fixed.append("raves.%s.race" % t)
		else:
			var rc: Dictionary = race
			rc["wins"] = maxi(int(rc.get("wins", 0)), 0)
			rc["runs"] = maxi(int(rc.get("runs", 0)), int(rc["wins"]))
			rc["best"] = maxf(float(rc.get("best", 0.0)), 0.0)
	data["version"] = VERSION
	return fixed


## A new run: facing north in the bedsit, in no rave, every puzzle unsolved. Race records stay.
static func new_run(data: Dictionary) -> void:
	migrate(data)
	data["bedsit_facing"] = "N"
	data["rave_theme"] = ""
	for t in THEMES:
		for p in PUZZLES:
			data["raves"][t][p] = false


## The facing after a turn: dir -1 left, +1 right, 0 stay (bottom). Wraps.
static func turn(facing: String, dir: int) -> String:
	var i := FACINGS.find(facing)
	if i < 0:
		i = 0
	return FACINGS[posmod(i + dir, FACINGS.size())]


## The rave a facing leads to, from the bedsit themes data ({"facings": {"N": "space", ...}}). "" when the facing has none.
static func theme_of(facing: String, themes_data: Dictionary) -> String:
	return str((themes_data.get("facings", {}) as Dictionary).get(facing, ""))


## Applies one `flags_to_set` entry of an activity result. "rave.<theme>.<puzzle>" sets the puzzle flag; anything else is not a rave flag (false: the
## host hands it to RunProgress.set_flag as an ordinary run flag). True when the save changed.
static func apply_flag(data: Dictionary, flag: String) -> bool:
	if not flag.begins_with(FLAG_PREFIX):
		return false
	var bits := flag.substr(FLAG_PREFIX.length()).split(".")
	if bits.size() != 2 or bits[0] not in THEMES or bits[1] not in PUZZLES:
		return false
	var r: Dictionary = data["raves"][bits[0]]
	if bool(r[bits[1]]):
		return false
	r[bits[1]] = true
	return true


## One finished race of `theme`: `won` when the player finished ahead of every rival, `time_s` the finish time in song seconds (0: not finished).
static func record_race(data: Dictionary, theme: String, won: bool, time_s: float) -> void:
	var rc: Dictionary = data["raves"][theme]["race"]
	rc["runs"] = int(rc["runs"]) + 1
	if won:
		rc["wins"] = int(rc["wins"]) + 1
	if time_s > 0.0 and (float(rc["best"]) <= 0.0 or time_s < float(rc["best"])):
		rc["best"] = time_s


static func puzzle_done(data: Dictionary, theme: String, puzzle: String) -> bool:
	return bool(((data.get("raves", {}) as Dictionary).get(theme, {}) as Dictionary).get(puzzle, false))
