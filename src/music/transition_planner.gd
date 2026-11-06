class_name TransitionPlanner
extends RefCounted
## The planner of a scene change (docs/parallel-development/MUSIC_TRANSITIONS.md section 4): a pure function of the two scenes, their metadata and the readiness of the
## incoming music. No nodes, no disk, no clock. TransitionDirector calls it at the lock point (through its `planner` Callable, so stage M2 replaces this function without touching
## the wiring) and sends the public part as the `plan` of `locked`; the private part, the recipe, goes to the audio class (RunAudio.prepare_transition).
##
## THIS IS THE M1 PLANNER: every transition is `&"cut"`, today's behaviour (the outgoing music fades linearly over mix.phase_fade_s from the boundary, the incoming starts on it).
## Of the decision table of section 4.2 it implements rows 1 to 3 and collapses rows 4 to 8 into `cut`:
##   row 1  the incoming scene is a track scene, its stems are still loading, the request may defer and has not deferred yet  -> {"defer": &"not_ready"}
##   row 2  the incoming track is still not ready after that (or its load failed, or it was never asked for)                  -> cut, fallback true (it plays as an ordinary scene)
##   else   cut, fallback false
##
## Inputs (all Dictionaries; a missing key reads as its default):
##   out    {kind: &"track" | &"ordinary" | &"none", node, path, bpm, boundary_t, family}        the outgoing scene, boundary_t = T
##   inc    {kind: &"track" | &"ordinary", node, path, bpm (the track's if a track scene), ordinary_bpm (the run's tempo when it plays as an ordinary scene), family}
##   meta   {fade_s (mix.phase_fade_s, 0.6), carry_beats, carry_gain (mix.carry_bass of the incoming run)}
##   ready  {state: "" (no track) | "ready" | "loading" | "failed" | "none", may_defer: bool, deferred_once: bool}
## Output: the contract's Plan {mode, fallback, outgoing_bpm, incoming_bpm, blend_beats, complete_t} plus "recipe" (stripped by the director before `locked`), or {"defer": reason}.
## The cut recipe: {mode: &"cut", fade_s, tail_s, carry, incoming: &"track" | &"ordinary"}. `tail_s` is how long after T the outgoing music can sound: the fade, or with a carried bass
## (two loop scenes of one music family, RunAudio._begin_phase) the carry's beats plus the fade. complete_t = T + tail_s is a promise: `completed` fires by then.

const MODES := [&"blend", &"halftime_blend", &"echo_out", &"cut"]


static func plan(out: Dictionary, inc: Dictionary, meta: Dictionary, ready: Dictionary) -> Dictionary:
	var t := float(out.get("boundary_t", 0.0))
	var state := str(ready.get("state", ""))
	if StringName(str(inc.get("kind", &"ordinary"))) == &"track" and state != "ready":
		if bool(ready.get("may_defer", false)) and not bool(ready.get("deferred_once", false)) and state == "loading":
			return {"defer": &"not_ready"}  # row 1
		return _cut(out, inc, meta, t, true)  # row 2: the scene plays as an ordinary one
	return _cut(out, inc, meta, t, false)


## The Plan's keys, exactly (a test checks every plan against them).
static func plan_keys() -> Array:
	return ["mode", "fallback", "outgoing_bpm", "incoming_bpm", "blend_beats", "complete_t"]


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
