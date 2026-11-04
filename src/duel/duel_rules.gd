class_name DuelRules
extends RefCounted
## The wizard duel's numbers (content/duel/duel.json) and the pure rules built on them: which family and tier a phrase is,
## and how much power a played phrase casts. No nodes, no clock. Power and health are integers in tenths so that both
## phones add exactly the same numbers in the same order and always agree on the result.

const PATH := "res://content/duel/duel.json"

var cfg: Dictionary = {}
var errors: Array = []


static func load_default() -> DuelRules:
	return load_file(PATH)


static func load_file(path: String) -> DuelRules:
	var r := DuelRules.new()
	if not FileAccess.file_exists(path):
		r.errors.append("%s not found" % path)
		return r
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(v) != TYPE_DICTIONARY:
		r.errors.append("%s is not valid JSON" % path)
		return r
	r.cfg = v
	for key in ["music", "timing", "pattern", "tiers", "pass_credit", "hp", "max_phrases", "power", "port", "discovery_port"]:
		if not r.cfg.has(key):
			r.errors.append("duel.json is missing %s" % key)
	if r.errors.is_empty():
		var pat := str(r.cfg["pattern"])
		if pat.is_empty() or pat.replace("D", "").replace("B", "") != "":
			r.errors.append("duel.json pattern must be made of D and B")
		if float(r.cfg["timing"]["decision_beat"]) >= float(r.cfg["timing"]["phrase_beats"]):
			r.errors.append("the decision beat must fall inside the phrase")
	return r


func phrase_beats() -> int:
	return int(cfg["timing"]["phrase_beats"])


func max_hp10() -> int:
	return int(round(float(cfg["hp"]) * 10.0))


## "drums" or "bass" for phrase `j`.
func family_of(j: int) -> String:
	var pat := str(cfg["pattern"])
	return "bass" if pat[j % pat.length()] == "B" else "drums"


## Difficulty tier (1 to 4) of phrase `j`.
func tier_of(j: int) -> int:
	var tier := 1
	for e in cfg["tiers"]:
		if j >= int(e[0]):
			tier = int(e[1])
	return tier


## Weight of one accepted cue by how far from the beat it was played (perfect, great or ok).
func grade_weight(abs_delta_ms: float, perfect_ms: float, great_ms: float) -> float:
	var w: Dictionary = cfg["power"]["grade_weights"]
	if abs_delta_ms <= perfect_ms:
		return float(w["perfect"])
	if abs_delta_ms <= great_ms:
		return float(w["great"])
	return float(w["ok"])


## Precision of a played phrase, 0..1: the summed weights of its cues (0 for a missed one) over the cue count, less a cost per stray press.
func precision(weighted_sum: float, cues: int, strays: int) -> float:
	if cues <= 0:
		return 1.0
	return clampf(weighted_sum / float(cues) - float(cfg["power"]["stray_cost"]) * float(strays), 0.0, 1.0)


## The spell's power in tenths for a passed phrase. `streak` is the number of casts in a row before this one.
func power10(prec: float, family: String, tier: int, streak: int) -> int:
	var p: Dictionary = cfg["power"]
	var quality := clampf((prec - 0.4) / 0.6, 0.0, 1.0)
	var base := lerpf(float(p["min"]), float(p["max"]), quality)
	var mult := 1.0 + float(p["streak_bonus"]) * float(mini(streak, int(p["streak_cap"])))
	if family == "bass":
		mult *= float(p["bass_mult"])
	mult *= 1.0 + float(p["tier_step"]) * float(tier - 1)
	return int(round(base * mult * 10.0))
