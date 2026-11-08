class_name CloakroomActivity
extends MinigameActivity
## The cloakroom same/different puzzle (docs/briefs/BEDSIT_RAVES_BRIEF.md section 5; CONTRACTS.md 4, 5, 6). Mode REPLACE: the rhythm is suspended while it is seated and two
## large controls, SAME on the left and DIFFERENT on the right, stand where the pads were. A pure function of the taps so far and song time; no node, no wall clock.
##
## Flow: a short demonstration (a reference, then `demo_trials` auto-played trials with the answer shown), the unscored reference symbol, then one scored trial per coat:
## "await" (the current symbol is shown; exactly one answer is taken), "process" (the coat is handled: `correct_s` song seconds after a right answer, `wrong_s` after a wrong one;
## taps are ignored), the next coat. After the last coat: "payoff" (the rail is empty, the attendant waves, the lamp changes), then done with the flag.
## Scoring always compares the current symbol with the IMMEDIATELY previous one (a wrong answer does not change what the next trial is compared with).
##
## Leave and return: the progress (sequence, answers, whether the demonstration was seen) is saved in CloakroomSession (process-static, keyed "<theme>/cloakroom"; it stands in for
## RaveSession) on every change, so a new activity object for a re-request resumes the queue where it was. Done or run over clears it.
##
## STAGING (CONTRACTS.md 10, ruling 38): nothing is drawn by the activity. It declares `things()` (the coats, the current and the previous symbol as dynamic props of the room, sheets
## `cloak_coat` and `cloak_symbols_<theme>`, frame set from the state machine in song time), directs the crowd actors (`customer_<k>`, `attendant`) with `world.people(id, state, t0, dur)`
## and asks for in-world feedback with `world.feedback(thing, kind, t)`; `world` is the WorldThings interface the host gives in `setup(ctx["world"])` (a recording stub in tests). The
## counter, the rail and the tag board are map pieces (`cloak_counter`, `cloak_rail`, `cloak_tag_board`) authored in the scene's map. The two controls are `controls()`, pictograms only.
##
## Config (the registered content/minigames/cloakroom.json merged with the theme's keys): coats 8, correct_s / fast_s 1.0, wrong_s / slow_s 3.0, symbols 4, match_share 0.5,
## demo_trials 2, demo_step_beats 3, ref_beats 2, payoff_beats 4, cloakroom_symbols [{id, ...}] (four ids the art knows), flags_on_complete.

const SHOW_PREVIOUS_TRIALS := 3
const SECTOR := "cloak"
const COAT_COLS := 4  # sheet cloak_coat: 4 colours across, one row per state: 0 on the rail, 1 carried, 2 handed over; frame = row * 4 + colour
const SYMBOL_COLS := 4  # sheet cloak_symbols_<theme>: the four symbols across, row 0 the tag's, row 1 the faded previous one; frame = row * 4 + symbol
## Where the things stand in the room's map: these are the test scene's (tests/fixtures/cloakroom_scene); a rave overrides any key in content/bedsit/themes.json "cloakroom.<theme>.layout"
## (or the request config's "layout"). Metres: `at` is [x, z] on the ground plane, `y` the height of a thing's bottom edge above the floor. `customer_slots` is one standing place per
## customer (the coat is carried from there); a layout with one slot uses it for every customer. The rail's coat j hangs at `rail_at + rail_step * j`.
const LAYOUT := {
	"sector": "cloak", "customer_slots": [[1.8, -1.7]], "hand_off": [-0.3, 0.0], "attendant_at": [-0.8, -2.7], "rail_at": [-3.7, -2.55], "rail_step": [0.3, 0.0], "rail_y": 1.0,
	"coat_size": [0.5, 0.8], "symbol_at": [0.0, -2.15], "symbol_y": 1.15, "symbol_size": [0.8, 0.8], "prev_at": [-0.9, -2.15], "prev_y": 1.25, "prev_size": [0.5, 0.5],
	"counter_piece": "cloak_counter", "lamp_piece": "",
}

var theme := ""
var symbol_ids: Array = []  # four symbol ids of the theme (CloakroomArt)
var coats := 8
var fast_s := 1.0
var slow_s := 3.0
var seq: Array = []  # coats + 1 symbol indices; seq[0] is the reference
var expected: Array = []
var answers: Array = []  # [{trial, answer, expected, correct, t}] one per answered trial
var ignored_taps := 0  # taps refused (during demonstration, processing, after the answer): never scored
var _phase := "demo"
var _phase_t0 := 0.0
var _phase_end := 0.0
var _demo: Array = []  # [{symbol, previous, answer, beats}]
var _demo_i := 0
var _demo_done := false
var _now := 0.0
var _key := ""
var _sig := ""
var _demo_step_beats := 3.0
var _ref_beats := 2.0
var _payoff_beats := 4.0
var _restored := false
var world: Object = null  # the room (WorldThings interface), null in a pure test
var _pushed := ""
var _layout: Dictionary = {}


func setup(ctx: Dictionary) -> void:
	super.setup(ctx)
	var req: Dictionary = ctx.get("request", {}) if typeof(ctx.get("request", null)) == TYPE_DICTIONARY else {}
	theme = str(req.get("theme", config.get("theme", "")))
	coats = maxi(int(config.get("coats", 8)), 1)
	fast_s = maxf(float(config.get("fast_s", config.get("correct_s", 1.0))), 0.0)
	slow_s = maxf(float(config.get("slow_s", config.get("wrong_s", 3.0))), fast_s)
	_demo_step_beats = float(config.get("demo_step_beats", 3.0))
	_ref_beats = float(config.get("ref_beats", 2.0))
	_payoff_beats = float(config.get("payoff_beats", 4.0))
	symbol_ids = CloakroomArt.symbols_for(theme, config.get("cloakroom_symbols", []))
	_key = "%s/cloakroom" % theme
	world = ctx.get("world", null)
	_layout = layout(config, theme)
	_sig = "%d|%s" % [coats, ",".join(PackedStringArray(symbol_ids))]
	var saved := CloakroomSession.load_state(_key)
	if not saved.is_empty() and str(saved.get("sig", "")) == _sig:
		seq = saved["seq"]
		expected = saved["expected"]
		answers = saved["answers"]
		_demo_done = bool(saved.get("demo_done", false))
		_restored = true
	else:
		var g := CloakroomTrials.generate(rng_seed, coats, float(config.get("match_share", 0.5)), symbol_ids.size())
		seq = g["seq"]
		expected = g["expected"]
	_build_demo()


## The layout of theme `theme`: LAYOUT with the theme's (themes.json), then the config's, overrides.
static func layout(cfg: Dictionary, th: String) -> Dictionary:
	var out: Dictionary = LAYOUT.duplicate(true)
	var l: Variant = CloakroomArt.theme_data(th).get("layout", {}) if th != "" else {}
	if typeof(l) == TYPE_DICTIONARY:
		out.merge(l, true)
	if typeof(cfg.get("layout", null)) == TYPE_DICTIONARY:
		out.merge(cfg["layout"], true)
	return out


func _slot(j: int) -> Vector2:
	var slots: Array = _layout["customer_slots"]
	var v: Array = slots[mini(j, slots.size() - 1)]
	return Vector2(float(v[0]), float(v[1]))


func _v2(key: String) -> Vector2:
	var v: Array = _layout[key]
	return Vector2(float(v[0]), float(v[1]))


func _build_demo() -> void:
	_demo = []
	var n := maxi(int(config.get("demo_trials", 2)), 0)
	var a := 0
	var b := 1
	_demo.append({"symbol": a, "previous": -1, "answer": "", "beats": _ref_beats})
	var cur := a
	for i in n:
		if i % 2 == 0:
			_demo.append({"symbol": cur, "previous": cur, "answer": "same", "beats": _demo_step_beats})
		else:
			var nxt := b if cur == a else a
			_demo.append({"symbol": nxt, "previous": cur, "answer": "different", "beats": _demo_step_beats})
			cur = nxt


func begin(t: float) -> void:
	super.begin(t)
	_now = t
	if answers.size() >= coats:
		_enter("payoff", t, t + _payoff_beats * beat_s)
	elif not answers.is_empty() or _demo_done or _demo.size() <= 1:
		_demo_done = true
		if answers.is_empty():
			_enter("reference", t, t + _ref_beats * beat_s)
		else:
			_enter("await", t, INF)
	else:
		_demo_i = 0
		_enter("demo", t, t + float((_demo[0] as Dictionary)["beats"]) * beat_s)
	_save()
	_push()


func _enter(phase: String, t0: float, t_end: float) -> void:
	_phase = phase
	_phase_t0 = t0
	_phase_end = t_end
	_direct(phase, t0, t_end)


func update(t: float) -> void:
	_advance(t)
	_push()


## Moves the state machine to song time `t`, taking every transition whose time has passed (each starts where the last one ended).
func _advance(t: float) -> void:
	if not began or _done:
		return
	_now = maxf(_now, t)
	while _now >= _phase_end and not _done:
		var e := _phase_end
		match _phase:
			"demo":
				_demo_i += 1
				if _demo_i < _demo.size():
					_enter("demo", e, e + float((_demo[_demo_i] as Dictionary)["beats"]) * beat_s)
				else:
					_demo_done = true
					_enter("reference", e, e + _ref_beats * beat_s)
					_save()
			"reference":
				_enter("await", e, INF)
			"process":
				if answers.size() >= coats:
					_enter("payoff", e, e + _payoff_beats * beat_s)
				else:
					_enter("await", e, INF)
			"payoff":
				_close("done")


func targets() -> Array:
	var out: Array = ["same", "different"] if _phase == "await" else []
	out.append_array(exit_targets())
	return out


func tap(target: String, t: float) -> bool:
	_advance(t)
	if _done:
		return false
	if MinigameActivity.is_exit_target(target):
		var alias := exit_alias(target)
		if alias != "exit" and exit_route(alias) == "":
			return false
		leave_route = exit_route(alias)
		request_leave(t)
		return true
	if target != "same" and target != "different":
		return false
	if _phase != "await":
		ignored_taps += 1
		return false
	var i := answers.size()
	var right: String = expected[i]
	var ok := target == right
	answers.append({"trial": i, "answer": target, "expected": right, "correct": ok, "t": t})
	_enter("process", t, t + (fast_s if ok else slow_s))
	_save()
	if world != null:
		world.feedback("cloak_symbol_current", "tick" if ok else "cross", t)
	_advance(t)  # (a zero-length process moves on at once)
	_push()
	return true


func request_leave(t: float) -> void:
	_advance(t)
	if _done:
		return
	_close("done" if answers.size() >= coats else "left")  # (every coat answered: the work is complete, only the handover animation is skipped)


func interrupt(reason: String, t: float) -> void:
	_advance(t)
	_close(reason)


func _close(reason: String) -> void:
	if _done:
		return
	if reason == "done":
		_phase = "done"
		CloakroomSession.clear(_key)
	elif reason == "run_over":
		CloakroomSession.clear(_key)
	else:
		_save()
	_finish(reason)


func _save() -> void:
	if _done:
		return
	CloakroomSession.save(_key, {"sig": _sig, "seq": seq, "expected": expected, "answers": answers, "demo_done": _demo_done})


func controls() -> Array:
	return [{"id": "same", "label": "", "pictogram": "same"}, {"id": "different", "label": "", "pictogram": "different"}]


func correct_count() -> int:
	return answers.filter(func(a: Dictionary) -> bool: return bool(a["correct"])).size()


func result() -> Dictionary:
	var r := super.result()
	var flags: Array = []
	if _reason == "done":
		for f: Variant in config.get("flags_on_complete", []):
			if theme != "" or not str(f).contains("{theme}"):  # (no rave, no rave flag)
				flags.append(str(f).replace("{theme}", theme))
		if flags.is_empty() and theme != "":
			flags.append("rave.%s.cloakroom_done" % theme)
	r["completed"] = _reason == "done"
	r["score"] = correct_count()
	r["flags_to_set"] = flags
	return r


## No canvas view: the room is drawn by the stage (things, pieces, crowd actors), the strip by the host's controls layer.
func make_view() -> Control:
	return null


# --- the staging ------------------------------------------------------------------------------------------------------------------

func _customer_id(j: int) -> String:
	return "customer_%d" % j


func _handled() -> int:
	return answers.size() - (1 if _phase == "process" else 0)


## The crowd directions for entering `phase` at t0 (the people actors are the host's; the activity only names a state).
func _direct(phase: String, t0: float, t_end: float) -> void:
	if world == null:
		return
	var j := clampi(_handled(), 0, coats - 1)
	var dur := t_end - t0 if t_end < INF else 0.0
	match phase:
		"demo", "reference", "await":
			world.people(_customer_id(j), "waiting", t0, 0.0)
			world.people("attendant", "idle", t0, 0.0)
		"process":
			var ok := bool(answers[-1]["correct"])
			world.people(_customer_id(j), "happy" if ok else "impatient", t0, dur)
			world.people("attendant", "happy" if ok else "waiting", t0, dur)
		"payoff":
			world.people("attendant", "clap", t0, dur)
			world.people(_customer_id(clampi(coats - 1, 0, coats - 1)), "hands_up", t0, dur)
			world.feedback(str(_layout["counter_piece"]), "glow", t0)
			if str(_layout["lamp_piece"]) != "":
				world.piece_on(str(_layout["lamp_piece"]), t0)


func _push() -> void:
	if world == null:
		return
	var arr := things()
	var key := JSON.stringify(arr)
	if key != _pushed:
		_pushed = key
		world.set_things(arr)


## 0..1 progress of the handover across the process time: a quick answer is a quick swing, a slow one fumbles first.
func handover() -> float:
	if _phase != "process":
		return 0.0
	var span := maxf(_phase_end - _phase_t0, 0.1)
	var age := _now - _phase_t0
	if span > 1.5:
		return clampf((age - 1.0) / (span - 1.0), 0.0, 1.0)
	return clampf(age / (span * 0.8), 0.0, 1.0)


func _thing(id: String, sprite: String, at: Vector2, size: Vector2, frame: int, y := 0.0) -> Dictionary:
	return {"id": id, "sprite": sprite, "at": [at.x, at.y], "sector": str(_layout["sector"]), "size": [size.x, size.y], "frame": frame, "y": y}


## The dynamic things of the room at the last song time: [{id, sprite, at: [x, z], sector, size: [w_m, h_m], frame, y}], in a fixed order. One coat per coat still to come hangs on the
## rail (`cloak_coat_<j>`, j the customer it belongs to); the customer's own coat is carried, then handed across to the attendant while it is processed, then gone. The current symbol sits
## on the tag board; the previous one beside it, faded, for the first three trials only (and the demonstration).
func things() -> Array:
	var out: Array = []
	var done := _phase in ["payoff", "done"]
	var cur := _handled()
	var coat_size := _v2("coat_size")
	var rail0 := _v2("rail_at")
	var step := _v2("rail_step")
	var ry := float(_layout["rail_y"])
	for j in coats:
		var col := j % COAT_COLS
		if done or j < cur:
			continue
		var hand := _slot(j) + _v2("hand_off")
		if j > cur:
			out.append(_thing("cloak_coat_%d" % j, "cloak_coat", rail0 + step * float(j), coat_size, col, ry))
		elif _phase == "process":
			var h := handover()
			if h <= 0.0:
				out.append(_thing("cloak_coat_%d" % j, "cloak_coat", hand, coat_size, COAT_COLS + col, ry))
			else:
				var p := hand.lerp(_v2("attendant_at") - _v2("hand_off"), h)
				out.append(_thing("cloak_coat_%d" % j, "cloak_coat", p, coat_size, 2 * COAT_COLS + col, ry + sin(h * PI) * 0.4))
		else:
			out.append(_thing("cloak_coat_%d" % j, "cloak_coat", hand, coat_size, COAT_COLS + col, ry))
	var st := state()
	var sheet := "cloak_symbols_%s" % (theme if theme != "" else "space")
	if str(st["current"]) != "":
		out.append(_thing("cloak_symbol_current", sheet, _v2("symbol_at"), _v2("symbol_size"), symbol_ids.find(st["current"]), float(_layout["symbol_y"])))
	if str(st["previous"]) != "" and bool(st["show_previous"]):
		out.append(_thing("cloak_symbol_previous", sheet, _v2("prev_at"), _v2("prev_size"), SYMBOL_COLS + symbol_ids.find(st["previous"]), float(_layout["prev_y"])))
	return out


## The snapshot the view and the tests read. `trial` is the scored trial being shown (-1 in the demonstration and the reference), `current`/`previous` symbol ids ("" none).
func state() -> Dictionary:
	var i := answers.size()
	var cur_idx := -1
	var prev_idx := -1
	var trial := -1
	var demo_answer := ""
	match _phase:
		"demo":
			var d: Dictionary = _demo[mini(_demo_i, _demo.size() - 1)]
			cur_idx = int(d["symbol"])
			prev_idx = int(d["previous"])
			demo_answer = str(d["answer"])
		"reference":
			cur_idx = int(seq[0])
		"await":
			trial = i
			cur_idx = int(seq[i + 1])
			prev_idx = int(seq[i])
		"process":
			trial = i - 1
			cur_idx = int(seq[i])
			prev_idx = int(seq[i - 1])
		"payoff", "done":
			trial = coats - 1
			cur_idx = int(seq[coats])
			prev_idx = int(seq[coats - 1])
	var last: Dictionary = answers[-1] if not answers.is_empty() else {}
	var reaction := "waiting"
	if _phase == "process":
		reaction = "happy" if bool(last.get("correct", true)) else "impatient"
	elif _phase in ["payoff", "done"]:
		reaction = "happy"
	var handled := i - (1 if _phase == "process" else 0)  # (coats fully handled: the one being processed is still at the counter)
	return {"began": began, "done": _done, "reason": _reason, "wobble": wobble, "theme": theme, "phase": _phase, "phase_t0": _phase_t0, "phase_end": _phase_end,
		"coats": coats, "remaining": coats - handled, "answered": i, "trial": trial, "correct": correct_count(), "wrong": i - correct_count(),
		"symbols": symbol_ids, "current": str(symbol_ids[cur_idx]) if cur_idx >= 0 else "", "previous": str(symbol_ids[prev_idx]) if prev_idx >= 0 else "",
		"show_previous": prev_idx >= 0 and (_phase == "demo" or trial < SHOW_PREVIOUS_TRIALS), "demo_answer": demo_answer, "demo_step": _demo_i if _phase == "demo" else -1,
		"demo_steps": _demo.size(), "last": last, "reaction": reaction, "customer": clampi(handled, 0, coats - 1), "t": _now,
		"fast_s": fast_s, "slow_s": slow_s, "ignored": ignored_taps, "restored": _restored}
