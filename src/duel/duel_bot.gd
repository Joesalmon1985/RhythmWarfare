class_name DuelBot
extends RefCounted
## A scripted player for one DuelEngine: it presses the charted cues with a skill (the share it plays at all, how far from the beat it
## lands, how many stray presses it makes). It is the Apprentice you can duel alone, and the player in tests and in the two-window check
## (RW_DUEL_BOT). It uses only the engine's public press and release, so everything it does is judged exactly as a finger would be.

var hit := 0.9
var sigma_ms := 45.0
var strays := 0.01  # stray presses per cue
var skip_blocks: Dictionary = {}  # phrase -> true: sits that phrase out (tests)
var rng := RandomNumberGenerator.new()

var _planned := 0  # notes before this index have been planned
var _plan: Array = []  # [{pad, press_t, release_t, pressed, released}]


static func from_skill(rules: DuelRules, skill: String, seed_value: int) -> DuelBot:
	var b := DuelBot.new()
	var s: Dictionary = rules.cfg["bot_skills"].get(skill, rules.cfg["bot_skills"]["adept"])
	b.hit = float(s["hit"])
	b.sigma_ms = float(s["sigma_ms"])
	b.strays = float(s["strays"])
	b.rng.seed = seed_value
	return b


## Plays up to song time `t`. Returns [{"pad", "down": bool}] so a scene can light its pads.
func step(engine: DuelEngine, t: float) -> Array:
	var out: Array = []
	var notes := engine.level.notes
	while _planned < notes.size():
		var n: Dictionary = notes[_planned]
		_planned += 1
		if skip_blocks.has(int(n["block"])):
			continue
		if rng.randf() < hit:
			var off := clampf(rng.randfn(0.0, sigma_ms), -110.0, 110.0) / 1000.0
			var press_t := float(n["time"]) + off
			var rel := float(n["end_time"]) if n["type"] == "hold" else press_t + 0.07
			_plan.append({"pad": int(n["pad"]), "press_t": press_t, "release_t": maxf(rel, press_t + 0.05), "pressed": false, "released": false})
		if rng.randf() < strays:
			var st := float(n["time"]) + rng.randf_range(0.2, 0.5)
			_plan.append({"pad": rng.randi_range(1, 4), "press_t": st, "release_t": st + 0.05, "pressed": false, "released": false})
	var keep: Array = []
	for p in _plan:
		if not p["pressed"] and float(p["press_t"]) <= t:
			p["pressed"] = true
			engine.press(int(p["pad"]), float(p["press_t"]), int(p["pad"]))
			out.append({"pad": int(p["pad"]), "down": true})
		if p["pressed"] and not p["released"] and float(p["release_t"]) <= t:
			p["released"] = true
			engine.release(int(p["pad"]), float(p["release_t"]), int(p["pad"]))
			out.append({"pad": int(p["pad"]), "down": false})
		if not p["released"]:
			keep.append(p)
	_plan = keep
	return out
