class_name TransitionPlanner
extends RefCounted
## The planner of a scene change (docs/parallel-development/MUSIC_TRANSITIONS.md section 4): a pure function of the two scenes, their metadata and the readiness of the
## incoming music. No nodes, no disk, no clock. TransitionDirector calls it at the lock point (through its `planner` Callable, so stage M2 replaces this function without touching
## the wiring) and sends the public part as the `plan` of `locked`; the private part, the recipe, goes to the audio class (RunAudio.prepare_transition).
##
## TWO PLANNERS IN ONE FILE. `plan()` is what the director calls. While `modes_enabled` is false (the default, and the whole of the game until stage M2.4) it is the M1 planner: every
## transition is `&"cut"`, today's behaviour (the outgoing music fades linearly over mix.phase_fade_s from the boundary, the incoming starts on it):
##   row 1  the incoming scene is a track scene, its stems are still loading, the request may defer and has not deferred yet  -> {"defer": &"not_ready"}
##   row 2  the incoming track is still not ready after that (or its load failed, or it was never asked for)                  -> cut, fallback true (it plays as an ordinary scene)
##   else   cut, fallback false
## With modes on, `plan()` is `plan_full()`: the whole decision table of MUSIC_TRANSITIONS.md section 4.2 (first matching row wins; lead rulings 5 to 7).
##
## HOW M2.4 TURNS THE MODES ON (nothing else in this file changes): set `TransitionPlanner.modes_enabled = true` once at start-up (a static, so the director's `planner` Callable needs no
## change), or pass `modes_enabled: true` in `meta` of one call (the key wins over the static; a test, or a setting such as `transitions = full | cut`, can use it). The director must then
## also put the extra inputs below into `out`, `inc` and `meta`; without any of them `plan_full` returns `cut` with `fallback` true and reason `missing`. Nothing plays the recipes yet.
##
## Inputs (all Dictionaries; a missing key reads as its default):
##   out    {kind: &"track" | &"ordinary" | &"none", node, path, bpm, boundary_t, family}        the outgoing scene, boundary_t = T
##   inc    {kind: &"track" | &"ordinary", node, path, bpm (the track's if a track scene), ordinary_bpm (the run's tempo when it plays as an ordinary scene), family}
##   meta   {fade_s (mix.phase_fade_s, 0.6), carry_beats, carry_gain (mix.carry_bass of the incoming run)}
##   ready  {state: "" (no track) | "ready" | "loading" | "failed" | "none", may_defer: bool, deferred_once: bool}
## and, for `plan_full` between two track scenes, these more:
##   out   {track: id, duration_s (of the audio), track_t_at_T (outgoing track time at the boundary), first_downbeat_s (default 0), section_role (the outgoing section at T: "drop",
##          "breakdown", "outro", ..., "" unknown), stem_keys (the pack's stem keys; default drums bass other vocals backing)}
##   inc   {track: id, entry_bar (RunTrackPlan), drop_bar (the drop the entry rule reads: TransitionSidecars.drop_bar_of)}
##   meta  {out: sidecar Dictionary ({} for none), in: sidecar Dictionary, out_grid_ok: bool, in_grid_ok: bool (TransitionSidecars.grid_ok from the pack's drift), modes_enabled? bool,
##          sidecar_required? bool (see SIDECAR_REQUIRED), out_state, in_state (TransitionSidecars.load_track's state, only read when sidecars are required)}
## Output: the contract's Plan {mode, fallback, outgoing_bpm, incoming_bpm, blend_beats, complete_t} plus "recipe" (stripped by the director before `locked`), or {"defer": reason}.
## The cut recipe: {mode: &"cut", fade_s, tail_s, carry, incoming: &"track" | &"ordinary"}. `tail_s` is how long after T the outgoing music can sound: the fade, or with a carried bass
## (two loop scenes of one music family, RunAudio._begin_phase) the carry's beats plus the fade. complete_t = T + tail_s is a promise: `completed` fires by then.
## `plan_full` adds `recipe.reason` to a cut (&"not_ready", &"load_failed", &"not_track", &"no_blend", &"short_lead", &"missing", &"sidecar"); the recipe of a blend, half-time blend or
## echo-out is, in bars of the INCOMING tempo counted from T (bar_s = 240 / incoming bpm):
##   {mode, rate (the tail's pitch_scale), window_bars W, bar_s, long (the long recipe), stems {key: {kind, fade: [start_bar, end_bar, curve]}}, kinds {kind: [start_bar, end_bar, curve]},
##    highpass {from_hz, to_hz, start_bar, end_bar, curve}, echo {delay_s, feedback, wet_db} (echo_out only, else {}), drop_t, deadline_t (= drop_t - 4 bars), complete_t, floor_t (= complete_t:
##    the tail's hard floor), cents (the tail's pitch change), incoming: &"track"}
## A stem's gain is 1 before `start_bar`, falls by `curve` (&"cos": cos(pi/2 x), x from 0 to 1) to 0 at `end_bar`, and is 0 after; at `floor_t` everything of the tail stops whatever the curves say.

const MODES := [&"blend", &"halftime_blend", &"echo_out", &"cut"]

## The one switch (see above). false = cut only.
static var modes_enabled := false

## Section 3.2 says a missing sidecar means "use the pack as it is" and 3.5 repeats it: false (the default) plans from the pack's values. true reads "missing or invalid sidecar" as `cut`
## (reason &"sidecar"; needs `meta.out_state` and `meta.in_state`, TransitionSidecars.load_track's `state`). The 61 real sidecars exist, so this only matters for a new recording.
const SIDECAR_REQUIRED := false

const MAX_CENTS := 50.0  # lead ruling 5: a tempo ratio within 2.93%
const MIN_LEAD_BARS := 5  # lead ruling 7
const MAX_WINDOW_BARS := 12
const SAME_TRACK_WINDOW_BARS := 4
const SILENT_BARS_BEFORE_DROP := 4
const DEFAULT_STEMS := ["drums", "bass", "other", "vocals", "backing"]
const DEFAULT_LINGER := ["other", "vocals"]


static func plan(out: Dictionary, inc: Dictionary, meta: Dictionary, ready: Dictionary) -> Dictionary:
	if bool(meta.get("modes_enabled", modes_enabled)):
		return plan_full(out, inc, meta, ready)
	return plan_cut_only(out, inc, meta, ready)


## The M1 planner: rows 1 and 2 and `cut`.
static func plan_cut_only(out: Dictionary, inc: Dictionary, meta: Dictionary, ready: Dictionary) -> Dictionary:
	var t := float(out.get("boundary_t", 0.0))
	var state := str(ready.get("state", ""))
	if StringName(str(inc.get("kind", &"ordinary"))) == &"track" and state != "ready":
		if bool(ready.get("may_defer", false)) and not bool(ready.get("deferred_once", false)) and state == "loading":
			return {"defer": &"not_ready"}  # row 1
		return _cut(out, inc, meta, t, true)  # row 2: the scene plays as an ordinary one
	return _cut(out, inc, meta, t, false)


## The whole decision table of section 4.2, first matching row wins. A pure function of its inputs; always available whatever `modes_enabled` says (tests call it directly).
static func plan_full(out: Dictionary, inc: Dictionary, meta: Dictionary, ready: Dictionary) -> Dictionary:
	var t := float(out.get("boundary_t", 0.0))
	var state := str(ready.get("state", ""))
	var inc_track := StringName(str(inc.get("kind", &"ordinary"))) == &"track"
	if inc_track and state != "ready":  # rows 1 and 2
		if bool(ready.get("may_defer", false)) and not bool(ready.get("deferred_once", false)) and state == "loading":
			return {"defer": &"not_ready"}
		return _with_reason(_cut(out, inc, meta, t, true), &"load_failed" if state == "failed" else &"not_ready")
	if StringName(str(out.get("kind", &"none"))) != &"track" or not inc_track:  # row 3
		return _with_reason(_cut(out, inc, meta, t, false), &"not_track")
	var so: Dictionary = meta["out"] if typeof(meta.get("out", null)) == TYPE_DICTIONARY else {}
	var si: Dictionary = meta["in"] if typeof(meta.get("in", null)) == TYPE_DICTIONARY else {}
	if bool(meta.get("sidecar_required", SIDECAR_REQUIRED)) and (str(meta.get("out_state", "missing")) != "ok" or str(meta.get("in_state", "missing")) != "ok"):
		return _with_reason(_cut(out, inc, meta, t, true), &"sidecar")
	if bool(so.get("no_blend", false)) or bool(si.get("no_blend", false)):  # row 4
		return _with_reason(_cut(out, inc, meta, t, false), &"no_blend")
	if not _complete(out, inc, meta):  # anything the planner cannot compute: cut, forced
		return _with_reason(_cut(out, inc, meta, t, true), &"missing")
	var out_bpm := float(out["bpm"])
	var in_bpm := float(inc["bpm"])
	var bar_in := 240.0 / in_bpm
	var bar_out := 240.0 / out_bpm
	var lead := int(inc["drop_bar"]) - int(inc["entry_bar"])  # L
	var left := (float(out["duration_s"]) - float(out["track_t_at_T"])) / bar_out  # R
	if lead < MIN_LEAD_BARS or left < 1.0:  # row 5
		return _with_reason(_cut(out, inc, meta, t, false), &"short_lead")
	var rho := in_bpm / out_bpm
	var grid := bool(meta["out_grid_ok"]) and bool(meta["in_grid_ok"])
	var mode := &"echo_out"
	var rate := 1.0
	var window := 2 if lead >= 6 else 1  # row 8
	if grid and absf(cents(rho)) <= MAX_CENTS + 1e-9:  # row 6
		mode = &"blend"
		rate = rho
	elif grid and (absf(cents(rho / 2.0)) <= MAX_CENTS + 1e-9 or absf(cents(rho * 2.0)) <= MAX_CENTS + 1e-9):  # row 7
		mode = &"halftime_blend"
		rate = rho / 2.0 if rho > 1.5 else rho * 2.0
	if mode != &"echo_out":
		window = mini(MAX_WINDOW_BARS, mini(lead - SILENT_BARS_BEFORE_DROP, int(floor(left)) - 1))
		if str(out.get("track", "")) != "" and str(out.get("track", "")) == str(inc.get("track", "")):
			window = mini(window, SAME_TRACK_WINDOW_BARS)
		if window < 2:
			mode = &"echo_out"
			rate = 1.0
			window = 1
	var complete_t := t + float(window) * bar_in
	var drop_t := t + float(lead) * bar_in
	var deadline_t := drop_t - float(SILENT_BARS_BEFORE_DROP) * bar_in
	if complete_t > deadline_t + 1e-6:  # cannot happen by construction; the silence rule is the one thing never to break
		return _with_reason(_cut(out, inc, meta, t, true), &"missing")
	var recipe := _recipe(mode, window, rate, out, so, bar_in, bar_out, complete_t, drop_t, deadline_t)
	return {"mode": mode, "fallback": false, "outgoing_bpm": out_bpm, "incoming_bpm": in_bpm, "blend_beats": 4 * window, "complete_t": complete_t, "recipe": recipe}


## The Plan's keys, exactly (a test checks every plan against them).
static func plan_keys() -> Array:
	return ["mode", "fallback", "outgoing_bpm", "incoming_bpm", "blend_beats", "complete_t"]


## 1200 x log2(x): a tempo ratio in cents.
static func cents(ratio: float) -> float:
	return 1200.0 * log(ratio) / log(2.0)


## Which of the three kinds of stem fade a key belongs to (section 4.3): &"bass", &"linger" (the sidecar's `linger`, else other and vocals) or &"rhythm" (drums, kick, tops, backing, and any
## key the planner does not know: the safe side).
static func stem_kind(key: String, linger: Array) -> StringName:
	if key == "bass":
		return &"bass"
	if linger.has(key):
		return &"linger"
	return &"rhythm"


static func _cut(out: Dictionary, inc: Dictionary, meta: Dictionary, t: float, fallback: bool) -> Dictionary:
	var as_track := StringName(str(inc.get("kind", &"ordinary"))) == &"track" and not fallback
	var in_bpm := float(inc.get("bpm", 174.0)) if as_track else float(inc.get("ordinary_bpm", inc.get("bpm", 174.0)))
	var fade_s := float(meta.get("fade_s", 0.6))
	var tail_s := fade_s
	var fam_out := str(out.get("family", ""))
	var carry := not as_track and StringName(str(out.get("kind", &"none"))) == &"ordinary" and fam_out != "" and fam_out == str(inc.get("family", "")) \
		and float(meta.get("carry_gain", 0.0)) > 0.0
	if carry:  # the outgoing bass may carry on under the incoming drums-alone block, then fades (RunAudio._begin_phase, carry_end)
		tail_s = float(meta.get("carry_beats", 16.0)) * 60.0 / maxf(in_bpm, 1.0) + fade_s
	return {"mode": &"cut", "fallback": fallback, "outgoing_bpm": float(out.get("bpm", 174.0)), "incoming_bpm": in_bpm, "blend_beats": 0, "complete_t": t + tail_s,
		"recipe": {"mode": &"cut", "fade_s": fade_s, "tail_s": tail_s, "carry": carry, "incoming": &"track" if as_track else &"ordinary"}}


## ---------------------------------------------------------------- the full planner's helpers

static func _with_reason(p: Dictionary, reason: StringName) -> Dictionary:
	(p["recipe"] as Dictionary)["reason"] = reason
	return p


## True when every number plan_full needs is there and sane.
static func _complete(out: Dictionary, inc: Dictionary, meta: Dictionary) -> bool:
	for k in ["bpm", "duration_s", "track_t_at_T"]:
		if typeof(out.get(k, null)) not in [TYPE_INT, TYPE_FLOAT]:
			return false
	for k in ["bpm", "entry_bar", "drop_bar"]:
		if typeof(inc.get(k, null)) not in [TYPE_INT, TYPE_FLOAT]:
			return false
	if float(out["bpm"]) <= 0.0 or float(inc["bpm"]) <= 0.0 or float(out["duration_s"]) <= 0.0:
		return false
	if int(inc["drop_bar"]) < 0 or int(inc["entry_bar"]) < 0:  # a drop of -1 is a track without any drop (TransitionSidecars.drop_bar_of)
		return false
	return typeof(meta.get("out_grid_ok", null)) == TYPE_BOOL and typeof(meta.get("in_grid_ok", null)) == TYPE_BOOL


## The outgoing grid's first downbeat with the sidecar's bar-phase correction.
static func _grid_origin(out: Dictionary, so: Dictionary) -> float:
	return float(out.get("first_downbeat_s", 0.0)) + float(so.get("downbeat_offset_beats", 0)) * 60.0 / float(out["bpm"])


## The mix-out bar of the outgoing track: the sidecar's mix_out_bar, else the snapped bar of its outro_start_s, else -1.
static func _mix_out_bar(out: Dictionary, so: Dictionary) -> int:
	if so.get("mix_out_bar", null) != null:
		return int(so["mix_out_bar"])
	if so.get("outro_start_s", null) != null:
		return int(roundf((float(so["outro_start_s"]) - _grid_origin(out, so)) / (240.0 / float(out["bpm"]))))
	return -1


## Section 4.3: the long recipe applies when the tail starts at or after the mix-out bar, or inside a breakdown or outro section.
static func _is_long(out: Dictionary, so: Dictionary) -> bool:
	if ["breakdown", "outro"].has(str(out.get("section_role", ""))):
		return true
	var mob := _mix_out_bar(out, so)
	if mob < 0:
		return false
	var bar_at_t := (float(out["track_t_at_T"]) - _grid_origin(out, so)) / (240.0 / float(out["bpm"]))
	return bar_at_t >= float(mob) - 1e-9


static func _recipe(mode: StringName, window: int, rate: float, out: Dictionary, so: Dictionary, bar_in: float, bar_out: float, complete_t: float, drop_t: float, deadline_t: float) -> Dictionary:
	var w := float(window)
	var is_long := false
	var kinds: Dictionary
	var highpass: Dictionary
	var echo := {}
	if mode == &"echo_out":
		kinds = {&"bass": [0.0, 0.125, &"cos"], &"rhythm": [0.0, 0.125, &"cos"], &"linger": [0.0, 1.0, &"cos"]}
		highpass = {"from_hz": 200.0, "to_hz": 2000.0, "start_bar": 0.0, "end_bar": w, "curve": &"exp"}
		echo = {"delay_s": 0.75 * bar_out / 4.0, "feedback": 0.4, "wet_db": -6.0}  # 3/4 of an outgoing beat
	else:
		is_long = _is_long(out, so)
		kinds = {&"bass": [0.0, minf(1.0, w), &"cos"], &"rhythm": [0.0, minf(4.0 if is_long else 2.0, w), &"cos"], &"linger": [2.0, w, &"cos"]}
		highpass = {"from_hz": 20.0, "to_hz": 250.0, "start_bar": 0.0, "end_bar": minf(4.0, w), "curve": &"exp"}
	var linger: Array = DEFAULT_LINGER
	if typeof(so.get("linger", null)) == TYPE_ARRAY and not (so["linger"] as Array).is_empty():
		linger = so["linger"]
	var keys: Array = out["stem_keys"] if typeof(out.get("stem_keys", null)) == TYPE_ARRAY else DEFAULT_STEMS
	var stems := {}
	for k in keys:
		var kind := stem_kind(str(k), linger)
		stems[str(k)] = {"kind": kind, "fade": kinds[kind]}
	return {"mode": mode, "rate": rate, "window_bars": window, "bar_s": bar_in, "long": is_long, "stems": stems, "kinds": kinds, "highpass": highpass, "echo": echo, "drop_t": drop_t,
		"deadline_t": deadline_t, "complete_t": complete_t, "floor_t": complete_t, "cents": cents(rate), "incoming": &"track"}
