class_name BarActivity
extends MinigameActivity
## The bar recipe memory game (bedsit brief section 6; CONTRACTS.md 4 and 5). Mode "replace": the rhythm is suspended while it is seated and its four ingredient controls stand where the pads were.
## Pure logic: no nodes, no clock of its own. Every step happens at its own song time, so the snapshot at time T is the same however often `update` ran; a tap takes effect at the tap's time.
##
## One drink: a customer arrives with an order (a recipe of ingredients: `start_len` long for the first drink, one longer after each success up to `max_len`, so 2 then 3), the order is
## demonstrated ingredient by ingredient (`show_s_per_ingredient` each), then hidden, and the player presses the ingredients in order. A wrong press ends the attempt: the mistake is shown, the drink
## is remade slowly (`serve_slow_s`) and the SAME order is demonstrated again (no limit on tries). The whole recipe pressed in order is served quickly and happily (`serve_fast_s`) and counts.
## `drinks_to_serve` (config "drinks", default 4) served drinks complete the bar: a short payoff, then done with the flags of `flags_on_complete` ("rave.<theme>.bar_done") in `result()`.
##
## Phases: "arrive" (the customer comes, the order shows as a bubble from the next phase on), "demo" (bubble up, ingredients lit one by one), "input" (bubble hidden, taps count), "serve"
## (outcome "happy" or "mistake"), "payoff" (the last drink is served). Targets: "ing:0".."ing:3" in the input phase, and the exits always (leaving is always possible; a drink in the making is dropped).
## Leaving and coming back (a new activity in the same run and theme) keeps the order: the served count and the current recipe are remembered (`_memory`, per theme and wallet) until the bar is done.
##
## Config (content/minigames/bar.json, merged with the theme's keys): drinks | drinks_to_serve, start_len, max_len, show_s_per_ingredient, arrive_s, serve_fast_s, serve_slow_s (remake_s),
## payoff_s, debounce_s (a press on the same ingredient within it is ignored), plus the content (BarData: ingredients, recipes, customers per theme).
##
## STAGING (ruling 38, CONTRACTS.md 10): the bar is played in the room through the stage; this class draws nothing and makes no view. It stages itself through a WorldThings port (ctx["world"], the
## host's, else a recording stub: `world()`): `things()` (the glass, frames empty / 1 / 2 / 3 layers / overflow / tipped, sliding to the customer when served; the order bubble, one frame per ingredient,
## only while the order is demonstrated) is pushed with `set_things` at every update; the customer and the bartender are directed with `people(id, state, t0, dur)` ("customer": waiting, happy,
## frown, hands_up; "bartender": idle, clap, hands_up, raise_glass); a press ticks or crosses the glass and a served drink glows the counter (`feedback`); each served drink turns a shelf glass piece
## on (`piece_on` "bar_shelf_<i>") and the payoff pulses them all. The counter and the shelf are map pieces authored in the scene's map (tests/fixtures/bar_scene/bar_room.json).
##
## state(): {phase, phase_t0, phase_dur (-1 open ended), t, drink (1 based), served, drinks, len, recipe [index], ingredients [{id, color, shape, index}], customer {id, body, kind},
##   attempt (1 based), pos (steps right so far), glass [{ing, wrong, t}], outcome ("" | happy | mistake), wrong (index pressed wrongly, -1), bubble (bool), shown (index into the recipe lit now, -1),
##   show_s, last_press {id, t}, ignored (count), mistakes, targets, theme, done, done_reason}.

const ING_PREFIX := "ing:"
const ING_COUNT := 4

static var _memory: Dictionary = {}  # key (theme + wallet) -> {served, recipe}

var _theme := ""
var _data: Dictionary = {}
var _drinks := 4
var _start_len := 2
var _max_len := 3
var _show_s := 0.8
var _arrive_s := 1.0
var _fast_s := 1.4
var _slow_s := 3.0
var _payoff_s := 3.0
var _debounce_s := 0.3
var _rng := RandomNumberGenerator.new()
var _recipe: Array = []
var _served := 0
var _mistakes := 0
var _attempt := 1
var _pos := 0
var _glass: Array = []
var _outcome := ""
var _wrong := -1
var _customer := 0
var _phase := ""
var _phase_t0 := 0.0
var _phase_dur := -1.0
var _last := 0.0
var _last_tap: Dictionary = {}
var _last_press := {"id": "", "t": -100.0}
var _ignored := 0
var _recipes_seen: Array = []
var _world: Object = null
var _layout: Dictionary = {}


## Forget every remembered order (a new run; the tests).
static func forget_all() -> void:
	_memory.clear()


func setup(ctx: Dictionary) -> void:
	super.setup(ctx)
	var req: Variant = ctx.get("request", {})
	_theme = str((req as Dictionary).get("theme", "")) if typeof(req) == TYPE_DICTIONARY else ""
	if _theme == "":
		_theme = str(config.get("theme", ""))
	_data = BarData.resolve(config, _theme)
	_drinks = maxi(int(config.get("drinks_to_serve", config.get("drinks", 4))), 1)
	_start_len = clampi(int(config.get("start_len", 2)), 2, 3)
	_max_len = clampi(int(config.get("max_len", 3)), _start_len, 3)
	_show_s = maxf(float(config.get("show_s_per_ingredient", 0.8)), 0.05)
	_arrive_s = maxf(float(config.get("arrive_s", 1.0)), 0.0)
	_fast_s = maxf(float(config.get("serve_fast_s", 1.4)), 0.05)
	_slow_s = maxf(float(config.get("serve_slow_s", config.get("remake_s", 3.0))), _fast_s)
	_payoff_s = maxf(float(config.get("payoff_s", 3.0)), 0.05)
	_debounce_s = maxf(float(config.get("debounce_s", 0.3)), 0.0)
	_layout = BarData.layout(config, _theme)
	var w: Variant = ctx.get("world", null)
	_world = w if w is Object and (w as Object).has_method("set_things") else WorldThings.new()
	_rng.seed = rng_seed
	var mem: Variant = _memory.get(_key(), null)
	if typeof(mem) == TYPE_DICTIONARY:
		_served = clampi(int((mem as Dictionary).get("served", 0)), 0, _drinks - 1)
		var r: Variant = (mem as Dictionary).get("recipe", [])
		if typeof(r) == TYPE_ARRAY and (r as Array).size() == _len_for(_served):
			_recipe = (r as Array).duplicate()
	if _recipe.is_empty():
		_new_order()


func begin(t: float) -> void:
	super.begin(t)
	_last = t
	for i in _served:
		_world.piece_on("%s%d" % [_layout["shelf_prefix"], i], t)
	_enter("arrive", t, _arrive_s)
	_push()


## The recipe on order now (ingredient indices 0..3).
func recipe() -> Array:
	return _recipe.duplicate()


func served() -> int:
	return _served


func theme() -> String:
	return _theme


func update(t: float) -> void:
	_advance(t)
	_push()


func targets() -> Array:
	var out: Array = []
	if _phase == "input" and not _done:
		for i in ING_COUNT:
			out.append(ING_PREFIX + str(i))
	if not _done:
		out.append_array(exit_targets())
	return out


func tap(target: String, t: float) -> bool:
	if _done or not began:
		return false
	_advance(t)
	if _done:
		return false
	if is_exit_target(target):
		if exit_alias(target) not in exit_targets():
			return false
		leave_route = exit_route(target)
		request_leave(t)
		return true
	if not target.begins_with(ING_PREFIX) or _phase != "input":
		return false
	var idx := int(target.substr(ING_PREFIX.length())) if target.substr(ING_PREFIX.length()).is_valid_int() else -1
	if idx < 0 or idx >= ING_COUNT:
		return false
	if _last_tap.has(target) and t - float(_last_tap[target]) < _debounce_s and t >= float(_last_tap[target]):
		_ignored += 1  # a bounce or a double tap: one press per step
		return false
	_last_tap[target] = t
	_last_press = {"id": target, "t": t}
	if idx == int(_recipe[_pos]):
		_glass.append({"ing": idx, "wrong": false, "t": t})
		_world.feedback("bar_glass", "tick", t)
		_pos += 1
		if _pos >= _recipe.size():
			_outcome = "happy"
			_served += 1
			_save()
			_enter("serve", t, _fast_s)
	else:
		_glass.append({"ing": idx, "wrong": true, "t": t})
		_world.feedback("bar_glass", "cross", t)
		_wrong = idx
		_outcome = "mistake"
		_mistakes += 1
		_enter("serve", t, _slow_s)
	_push()
	return true


func request_leave(t: float) -> void:
	_advance(t)
	_save()
	_finish("left")
	_push()


func interrupt(reason: String, t: float) -> void:
	_advance(t)
	_save()
	_finish(reason)


func controls() -> Array:
	var out: Array = []
	for e: Dictionary in _data["ingredients"]:
		# no words: `label` is empty; `icon` (the ingredient id) and `shape`/`color` let the host draw the pictogram (hook H-bar-1)
		out.append({"id": ING_PREFIX + str(e["index"]), "label": "", "icon": str(e["id"]), "shape": str(e["shape"]), "color": (e["color"] as Color).to_html(false)})
	return out


func result() -> Dictionary:
	var done := _reason == "done"
	var flags: Array = []
	if done:
		for f: Variant in config.get("flags_on_complete", []):
			flags.append(str(f).replace("{theme}", _theme))
		if flags.is_empty() and _theme != "":
			flags.append("rave.%s.bar_done" % _theme)
	return {"activity_id": str(config.get("id", "bar")), "completed": done, "score": _served, "flags_to_set": flags,
		"reason": _reason if _reason in ["done", "left", "fall", "run_over", "host"] else "host"}


## The bar has no canvas view (ruling 38): the room's stage draws its things; the strip is the host's controls layer.
func make_view() -> Control:
	return null


func world() -> Object:
	return _world


## The bar's dynamic things at the last update's song time (CONTRACTS.md 10): [{id, sprite, at: [x, z], sector, size: [w, h], frame, y (centre height, m), anchor, layers? (hex colours of the glass's layers)}].
## "bar_glass": frame 0 empty, 1 / 2 / 3 that many layers, 4 overflow (a wrong press), 5 tipped (being thrown away); a happy drink slides to the customer, a mistake's glass is gone and a fresh one appears.
## "bar_order": the speech bubble, only while the order is demonstrated; frame = the ingredient shown now (0..3).
func things() -> Array:
	var out: Array = []
	if not began or (_done and _reason != "done"):
		return out
	var sheet := _theme if _theme != "" else "space"
	var sector := str(_layout["sector"])
	var p := _last - _phase_t0
	var u := clampf(p / _phase_dur, 0.0, 1.0) if _phase_dur > 0.0 else 0.0
	var gat: Array = (_layout["glass_at"] as Array).duplicate()
	var shown := true
	var correct: Array = []
	for g: Dictionary in _glass:
		if not bool(g["wrong"]):
			correct.append((_data["ingredients"][int(g["ing"])]["color"] as Color).to_html(false))
	var frame := mini(correct.size(), 3)
	if _phase == "serve" and _outcome == "happy":
		var slide := clampf((u - 0.15) / 0.45, 0.0, 1.0)
		slide = slide * slide * (3.0 - 2.0 * slide)
		var cg: Array = _layout["customer_glass_at"]
		gat = [lerpf(float(gat[0]), float(cg[0]), slide), lerpf(float(gat[1]), float(cg[1]), slide)]
		shown = u < 0.8  # the customer leaves with it
	elif _phase == "serve" and _outcome == "mistake":
		if u < 0.4:
			frame = 4
		elif u < 0.65:
			frame = 5
			gat = [float(gat[0]) + 0.4 * (u - 0.4) / 0.25, float(gat[1])]
		elif u < 0.8:
			shown = false
		else:
			frame = 0
			correct = []
	elif _phase == "payoff":
		var cg2: Array = _layout["customer_glass_at"]
		gat = [float(cg2[0]), float(cg2[1])]
	if shown:
		var t_glass := {"id": "bar_glass", "sprite": "bar_glass_" + sheet, "at": gat, "sector": sector, "size": (_layout["glass_size"] as Array).duplicate(), "frame": frame,
			"y": float(_layout["glass_y"]), "anchor": "center"}
		if not correct.is_empty():
			t_glass["layers"] = correct
		out.append(t_glass)
	if _phase == "demo":
		var sh := clampi(int(floorf(p / _show_s)), 0, _recipe.size() - 1)
		out.append({"id": "bar_order", "sprite": "bar_order_" + sheet, "at": (_layout["bubble_at"] as Array).duplicate(), "sector": sector, "size": (_layout["bubble_size"] as Array).duplicate(),
			"frame": int(_recipe[sh]), "y": float(_layout["bubble_y"]), "anchor": "center"})
	return out


## Pushes the things to the stage's port.
func _push() -> void:
	_world.set_things(things())


## Directs the people and the lit pieces for the phase just entered (at song time `t`, lasting `dur`).
func _direct(phase: String, t: float, dur: float) -> void:
	match phase:
		"arrive", "demo", "input":
			_world.people("customer", "waiting", t, maxf(dur, 0.0))
			_world.people("bartender", "idle", t, 0.0)
		"serve":
			if _outcome == "happy":
				_world.people("customer", "happy", t, dur)
				_world.people("bartender", "clap", t, dur)
				_world.feedback(str(_layout["counter_piece"]), "glow", t)
				_world.piece_on("%s%d" % [_layout["shelf_prefix"], _served - 1], t)
			else:
				_world.people("customer", "frown", t, dur)
				_world.people("bartender", "hands_up", t, dur)
		"payoff":
			_world.people("customer", "hands_up", t, dur)
			_world.people("bartender", "raise_glass", t, dur)
			_world.feedback(str(_layout["counter_piece"]), "glow", t)
			for i in _drinks:
				_world.piece_pulse("%s%d" % [_layout["shelf_prefix"], i], t, 2.0)


## How long the shown ingredient lights, seconds.
func show_s() -> float:
	return _show_s


## The recipe length of drink number `served` + 1: `start_len`, one longer after every success, up to `max_len`.
func _len_for(served: int) -> int:
	return clampi(_start_len + served, _start_len, _max_len)


func state() -> Dictionary:
	var shown := -1
	if _phase == "demo":
		shown = clampi(int(floorf((_last - _phase_t0) / _show_s)), 0, _recipe.size() - 1)
	return {"phase": _phase, "phase_t0": _phase_t0, "phase_dur": _phase_dur, "t": _last, "drink": _served + (0 if _phase in ["payoff"] or (_phase == "serve" and _outcome == "happy") else 1),
		"served": _served, "drinks": _drinks, "len": _recipe.size(), "recipe": _recipe.duplicate(), "ingredients": _data["ingredients"], "customer": _customer_look(),
		"attempt": _attempt, "pos": _pos, "glass": _glass.duplicate(), "outcome": _outcome, "wrong": _wrong, "bubble": _phase == "demo", "shown": shown, "show_s": _show_s,
		"last_press": _last_press.duplicate(), "ignored": _ignored, "mistakes": _mistakes, "targets": targets(), "theme": _theme, "done": _done, "done_reason": _reason,
		"leave_route": leave_route}


# --- the timeline --------------------------------------------------------------------------------------------------------------

func _enter(phase: String, t: float, dur: float) -> void:
	_phase = phase
	_phase_t0 = t
	_phase_dur = dur
	_direct(phase, t, dur)


## Runs every phase that ended at or before `t` at its own end time; song time only increases.
func _advance(t: float) -> void:
	if not began:
		return
	_last = maxf(_last, t)
	var guard := 0
	while not _done and _phase_dur >= 0.0 and _last >= _phase_t0 + _phase_dur and guard < 64:
		guard += 1
		var at := _phase_t0 + _phase_dur
		match _phase:
			"arrive":
				_enter("demo", at, float(_recipe.size()) * _show_s)
			"demo":
				_pos = 0
				_glass = []
				_wrong = -1
				_outcome = ""
				_enter("input", at, -1.0)
			"serve":
				if _outcome == "happy":
					if _served >= _drinks:
						_enter("payoff", at, _payoff_s)
					else:
						_attempt = 1
						_new_order()
						_save()
						_pos = 0
						_glass = []
						_outcome = ""
						_wrong = -1
						_enter("arrive", at, _arrive_s)
				else:
					_attempt += 1
					_pos = 0
					_glass = []
					_outcome = ""
					_wrong = -1
					_enter("demo", at, float(_recipe.size()) * _show_s)
			"payoff":
				_memory.erase(_key())
				_finish("done")
			_:
				_phase_dur = -1.0


## The next order: the theme's recipes of the right length (not the last one served), else generated from the four ingredients, no ingredient twice running.
func _new_order() -> void:
	var n := _len_for(_served)
	var pool: Array = []
	for r: Array in _data["recipes"]:
		if r.size() == n and not _recipes_seen.has(r):
			pool.append(r)
	if pool.is_empty():
		for r: Array in _data["recipes"]:
			if r.size() == n and r != _recipe:
				pool.append(r)
	if not pool.is_empty():
		_recipe = (pool[_rng.randi() % pool.size()] as Array).duplicate()
	else:
		for _try in 8:
			var r: Array = []
			while r.size() < n:
				var c := _rng.randi() % ING_COUNT
				if r.is_empty() or int(r[-1]) != c:
					r.append(c)
			_recipe = r
			if not _recipes_seen.has(r):
				break
	_recipes_seen.append(_recipe.duplicate())
	if _recipes_seen.size() > 6:
		_recipes_seen.pop_front()
	_customer = _rng.randi() % (_data["customers"] as Array).size()


func _customer_look() -> Dictionary:
	var cs: Array = _data["customers"]
	return cs[clampi(_customer, 0, cs.size() - 1)]


func _key() -> String:
	return "%s:%d" % [_theme, wallet.get_instance_id() if wallet != null and wallet is Object else 0]


func _save() -> void:
	if _done:
		return
	var keep: Array = _recipe.duplicate()
	if _outcome == "happy":
		keep = []  # served: the next customer orders something new
	_memory[_key()] = {"served": _served, "recipe": keep}
