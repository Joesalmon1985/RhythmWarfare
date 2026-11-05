class_name RunActing
extends RefCounted
## The acting contract's pure helpers (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3): what a hotspot's `acting` block and a scene's `cast` lines tell a person to do, as plain data the crowd
## can play. Nothing here touches a node or a clock; times are song seconds the caller passes in, so the same data at the same beats always gives the same segments.
##
## A segment is {act, face, look_at, from, until} (song seconds); a chain is segments end to end, played one after the other by StoryCrowd.direct_chain.
##   hotspot  acting {actor?, available?, selected?, committed?, success?, failure?}; each state {act, face?, look_at?, beats?, then?}
##   cast     {actor, at_beat, act, face?, look_at?, beats?, if_energy_below?, if_energy_above?, if_flags_all?, if_flags_none?}

const HOLD_BEATS := 8.0  # an outcome or cast act holds this long when the data gives no `beats`
const THEN_BEATS := 16.0  # a `then` act (what the person settles into) holds this long unless it names `beats`
const COMMITTED_BEATS := 2.0  # the commit flash: the `committed` act shows this long before the outcome's act
const STATE_S := 30.0  # an available or selected act lasts until the state changes (the old beckon's 30 s)
const LEGACY_ACT := "wave"  # a hotspot anchored on a person that carries no `acting` block: the crowd's wave, exactly as before the acting contract


static func has_acting(h: Dictionary) -> bool:
	return typeof(h.get("acting", null)) == TYPE_DICTIONARY and not (h["acting"] as Dictionary).is_empty()


## The person a hotspot directs: `acting.actor`, else the anchor's actor ("" when it has none, e.g. a thing and no actor named).
static func actor_of(h: Dictionary) -> String:
	if has_acting(h) and str((h["acting"] as Dictionary).get("actor", "")) != "":
		return str(h["acting"]["actor"])
	var an: Variant = h.get("anchor", {})
	if typeof(an) == TYPE_DICTIONARY and (an as Dictionary).has("actor"):
		return str(an["actor"])
	return ""


## One state of a hotspot's acting ({} when it has none): the data dictionary as authored.
static func spec_of(h: Dictionary, phase: String) -> Dictionary:
	if not has_acting(h):
		return {}
	var s: Variant = (h["acting"] as Dictionary).get(phase, {})
	return s if typeof(s) == TYPE_DICTIONARY else {}


## What the person does while the hotspot is on show: the authored `available` act, or for a hotspot with no acting block at all the old wave at the player.
static func available_spec(h: Dictionary) -> Dictionary:
	if has_acting(h):
		return spec_of(h, "available")
	return {"act": LEGACY_ACT, "face": "", "look_at": ""} if actor_of(h) != "" else {}


## What the person does while the hotspot is selected: the authored `selected` act, else whatever they were doing while it was available.
static func selected_spec(h: Dictionary) -> Dictionary:
	var s := spec_of(h, "selected")
	return s if not s.is_empty() else available_spec(h)


static func segment(spec: Dictionary, from_t: float, until_t: float) -> Dictionary:
	return {"act": str(spec.get("act", "")), "face": str(spec.get("face", "")), "look_at": str(spec.get("look_at", "")), "from": from_t, "until": until_t}


## The chain of acts after a commit at song time `t0`: the `committed` act for the flash, then the success or failure act for its `beats`, then each `then` in turn. Empty when the hotspot has none.
static func outcome_chain(h: Dictionary, success: bool, t0: float, beat_s: float) -> Array:
	var chain: Array = []
	var t := t0
	var c := spec_of(h, "committed")
	if not c.is_empty():
		var dc := float(c.get("beats", COMMITTED_BEATS)) * beat_s
		chain.append(segment(c, t, t + dc))
		t += dc
	var s := spec_of(h, "success" if success else "failure")
	var first := true
	while not s.is_empty() and str(s.get("act", "")) != "":
		var d := float(s.get("beats", HOLD_BEATS if first else THEN_BEATS)) * beat_s
		chain.append(segment(s, t, t + d))
		t += d
		first = false
		var nx: Variant = s.get("then", {})
		s = nx if typeof(nx) == TYPE_DICTIONARY else {}
	return chain


## A cast line as one segment starting at song time `t0`.
static func cast_segment(line: Dictionary, t0: float, beat_s: float) -> Dictionary:
	return segment(line, t0, t0 + float(line.get("beats", HOLD_BEATS)) * beat_s)


## Whether a cast line's conditions hold now: the crowd's energy and the world-state flags (`has_flag`: Callable(String) -> bool).
static func conditions_hold(line: Dictionary, energy: float, has_flag: Callable) -> bool:
	if line.has("if_energy_below") and not energy < float(line["if_energy_below"]):
		return false
	if line.has("if_energy_above") and not energy > float(line["if_energy_above"]):
		return false
	for f in line.get("if_flags_all", []):
		if not has_flag.is_valid() or not bool(has_flag.call(str(f))):
			return false
	for f in line.get("if_flags_none", []):
		if has_flag.is_valid() and bool(has_flag.call(str(f))):
			return false
	return true


## A Bassment creature's body language for an act, in metres and scale: {dx, dy, dz (towards the player), sx, sy}. `u` is beats since the act began. The creatures are billboard figures, not
## people, so their acts are motions on the figure (the same data, `acting.figure`).
static func figure_motion(act: String, u: float) -> Dictionary:
	var m := {"dx": 0.0, "dy": 0.0, "dz": 0.0, "sx": 1.0, "sy": 1.0}
	var frac := fposmod(u, 1.0)
	match act:
		"block":  # planted, wide, a slow heave
			m["sx"] = 1.07
			m["dy"] = 0.03 * sin(u * PI * 0.5)
		"offer":  # leans in with a bob
			m["dz"] = 0.18 * (0.5 + 0.5 * sin(u * PI))
			m["dy"] = 0.05 * sin(u * PI)
		"laugh":  # bounces on the half beat
			m["dy"] = 0.1 * absf(sin(u * TAU))
			m["sy"] = 1.0 + 0.04 * absf(sin(u * TAU))
		"stamp":  # drops on the beat
			m["dy"] = -0.1 * pow(1.0 - frac, 3.0)
		"recoil":  # a step back, held
			m["dz"] = -0.4 * smoothstep(0.0, 1.0, u)
		"bow":  # folds forward and stays
			m["sy"] = 1.0 - 0.14 * smoothstep(0.0, 1.0, u)
			m["dz"] = 0.1 * smoothstep(0.0, 1.0, u)
		"collapse":  # sinks
			m["dy"] = -0.3 * smoothstep(0.0, 2.0, u)
			m["sy"] = 1.0 - 0.2 * smoothstep(0.0, 2.0, u)
		"shake_head":
			m["dx"] = 0.12 * sin(u * TAU)
		"nod":
			m["dy"] = 0.05 * sin(u * TAU)
		"plead":
			m["dz"] = 0.1 * smoothstep(0.0, 1.0, u)
			m["sy"] = 1.0 - 0.05 * smoothstep(0.0, 1.0, u)
		"stare":
			m["dz"] = 0.05 * smoothstep(0.0, 2.0, u)
	return m
