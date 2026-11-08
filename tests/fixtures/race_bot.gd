class_name RaceBot
extends RefCounted
## Plays a RaceActivity without the stage (tests/test_race.gd, the calibration in docs/bedsit/RACE.md): pads judged at a fixed quality four times a beat, and a driver policy.
##   drive "best"   picks the best safe response of every situation (overtake, clear, follow, brake), a beat after it appears
##   drive "none"   never touches a region (every deadline resolves the default, top)
##   drive "worst"  picks a contact (or a kerb) whenever there is one
##   drive "dither" changes its mind every half second and lands on the best one only in the last half second
## `step_s`: the frame length (the result must not depend on it). `pauses`: [[t_from, wall_frames]]: the song time stands still for that many frames.

const BEAT := 60.0 / 174.0
const RANK := {"overtake": 0, "clear": 1, "follow": 2, "brake": 3, "kerb": 4, "contact": 5}


static func make(seed := 7, theme := "space", world: Object = null, cfg_extra := {}) -> RaceActivity:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/race.json"))
	cfg["seed"] = seed
	cfg.merge(cfg_extra, true)
	var a := RaceActivity.new()
	var ctx := {"seed": seed, "beat_s": BEAT, "config": cfg, "request": {"theme": theme}}
	if world != null:
		ctx["world"] = world
	a.setup(ctx)
	return a


static func best_dir(sit: Dictionary, worst := false) -> String:
	var o: Dictionary = sit["outcomes"]
	var best := ""
	for dir: String in ["top", "bottom", "left", "right"]:
		var r := int(RANK[str(o[dir])])
		if best == "" or (r > int(RANK[str(o[best])]) if worst else r < int(RANK[str(o[best])])):
			best = dir
	return best


static func play(a: RaceActivity, drive: String, quality: float, step_s := 1.0 / 60.0, pauses: Array = [], t0 := 0.0, max_s := 400.0) -> RaceActivity:
	a.begin(t0)
	var t := t0
	var next_note := t0
	var kind := "perfect" if quality >= 0.95 else ("great" if quality >= 0.85 else ("good" if quality >= 0.7 else ("ok" if quality >= 0.45 else "miss")))
	var last_dither := -1.0
	var pause_i := 0
	while not a.is_done() and t < t0 + max_s:
		if pause_i < pauses.size() and t >= float(pauses[pause_i][0]):
			for _k in int(pauses[pause_i][1]):
				a.update(t)  # frames go by, the song does not
			pause_i += 1
		t += step_s
		while next_note <= t:
			var k := kind
			if quality < 0.45 and quality > 0.0:  # (a mix: some hits among the misses)
				k = "ok" if fmod(next_note / BEAT, 4.0) < 4.0 * quality else "miss"
			a.on_judge({"kind": k, "time": next_note}, next_note)
			next_note += BEAT / 4.0
		a.update(t)
		var sit: Dictionary = a.cur
		if sit.is_empty() or drive == "none":
			continue
		var age := t - float(sit["t_spawn"])
		match drive:
			"best", "worst":
				if age >= BEAT and str(sit["selected"]) == "":
					a.tap("region:" + best_dir(sit, drive == "worst"), t)
			"dither":
				if float(sit["t_dead"]) - t < 0.5:
					if str(sit["selected"]) != best_dir(sit):
						a.tap("region:" + best_dir(sit), t)
				elif t - last_dither >= 0.5:
					last_dither = t
					a.tap("region:" + ["left", "right", "top", "bottom"][int(t * 2.0) % 4], t)
	return a


static func summary(a: RaceActivity) -> Dictionary:
	var s := a.state()
	return {"pos": a.position, "time": snappedf(a.race_time(), 0.001), "contacts": s["contacts"], "overtakes": s["overtakes"], "situations": s["situations"],
		"rivals": a.rivals.map(func(r: Dictionary) -> float: return snappedf(float(r["finish_t"]) - a.t_go, 0.01))}
