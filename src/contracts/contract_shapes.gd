class_name ContractShapes
extends RefCounted
## The shapes of docs/parallel-development/CONTRACTS.md as validators (each returns a list of problems, [] when the data fits) and the few pure functions
## both streams must compute the same way (the resume boundary, the tap owner, a route's rail actions, a point on a race course). The fixtures in
## src/contracts/fixtures/ fit these; tests/test_contracts.gd pins both. Nothing here reads the engine or a node.

const FIXTURES := "res://src/contracts/fixtures/"
const TRANSITIONS := ["world", "passage"]
const FIXED_FACINGS := {"N": "space", "E": "dinos", "S": "magic", "W": "transport"}  # the brief's fixed mapping (bedsit brief section 2)
const PROP_ROLES := ["stage_deck", "bass_knob", "cloakroom", "bar", "race_entrance", "home_threshold", "decor"]
const REQUIRED_PROP_ROLES := ["stage_deck", "bass_knob", "cloakroom", "bar", "race_entrance", "home_threshold"]
const GUIDE_FOR := ["stage", "cloakroom", "bar", "race", "home"]
const STATIONS := ["stage", "cloakroom", "bar"]
const MOVE_STYLES := ["walk", "stagger", "run", "climb", "carried"]  # RunRail.STYLES
const LEG_BARS_MIN := 2.0  # RunRail.MOVE_BARS_MIN: a shorter leg is clamped by RunRail.pick_bars (CONTRACTS.md 3, a flagged disagreement)
const LEG_BARS_MAX := 4.0
const CHOICE_HOLD_BARS_MIN := 4.0  # a choice viewpoint holds at least one block (the window is the last block, 16 beats) (ruling 35)
const CHOICE_STATES := ["idle", "available", "selected", "committed", "declined", "cost"]  # contract 9
const CHOICE_MOTIONS := ["still", "bob", "beckon", "slump", "pulse", "sway_left", "sway_right", "lean", "step_aside", "shake"]
const CHOICE_LIGHT_KEYS := ["floor_glow", "tint", "lamp"]
const CHOICE_LAMPS := ["off", "dim", "lit", "open"]
const REGIONS := ["top", "bottom", "left", "right"]
const ACTIVITY_KINDS := {"cloakroom": ["coats", "symbols", "correct_s", "wrong_s", "match_share", "demo_trials"],
	"bar": ["drinks", "start_len", "max_len", "show_s_per_ingredient", "remake_s"],
	"race": ["course", "decision_s", "rivals", "min_speed_frac", "target_s"],
	"bass": ["resist_turns", "knob_target"]}
const CONTROL_COUNT := {"cloakroom": 2, "bar": 4, "race": 0, "bass": 0}
const RESULT_REASONS := ["done", "left", "fall", "run_over", "host"]


static func load_fixture(name: String) -> Variant:
	var path := FIXTURES + name
	if not FileAccess.file_exists(path):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))


static func _is_num(v: Variant) -> bool:
	return typeof(v) == TYPE_INT or typeof(v) == TYPE_FLOAT


static func _is_str(v: Variant) -> bool:
	return typeof(v) == TYPE_STRING and str(v) != ""


static func _is_xz(v: Variant) -> bool:
	return typeof(v) == TYPE_ARRAY and (v as Array).size() == 2 and _is_num(v[0]) and _is_num(v[1])


# --- 1. scene entry and exit -------------------------------------------------------------------------------------------------

## SceneEntry: {scene_id, theme, arrival_pose (a waypoint id, or {at: [x, z], yaw} which tooling bakes into a waypoint), entered_from: {} | {scene_id, spot}, transition}.
static func scene_entry(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["scene entry is not a dictionary"]
	if not _is_str(d.get("scene_id")):
		e.append("scene_id missing")
	var th := str(d.get("theme", "<missing>"))
	if th != "" and th not in RaveSave.THEMES:
		e.append("theme %s is not \"\" or a rave theme" % th)
	var ap: Variant = d.get("arrival_pose")
	if typeof(ap) == TYPE_DICTIONARY:
		if not _is_xz(ap.get("at")) or not _is_num(ap.get("yaw")):
			e.append("arrival_pose {at: [x, z], yaw} malformed")
	elif not _is_str(ap):
		e.append("arrival_pose is neither a waypoint id nor {at, yaw}")
	var ef: Variant = d.get("entered_from")
	if typeof(ef) != TYPE_DICTIONARY:
		e.append("entered_from missing ({} for the opening)")
	elif not (ef as Dictionary).is_empty() and (not _is_str(ef.get("scene_id")) or not _is_str(ef.get("spot"))):
		e.append("entered_from needs scene_id and spot")
	if str(d.get("transition", "")) not in TRANSITIONS:
		e.append("transition is world or passage")
	return e


## SceneExit: {route: <route id> | "home", transition, threshold: <spot id the approach walk ends at>}.
static func scene_exit(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["scene exit is not a dictionary"]
	if not _is_str(d.get("route")):
		e.append("route missing (a route id or \"home\")")
	if str(d.get("transition", "")) not in TRANSITIONS:
		e.append("transition is world or passage")
	if not _is_str(d.get("threshold")):
		e.append("threshold spot missing")
	return e


# --- 2. theme selection ----------------------------------------------------------------------------------------------------

static func bedsit_themes(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["themes file is not a dictionary"]
	if str(d.get("start_facing", "")) != "N":
		e.append("start_facing must be N (bedsit brief section 2)")
	var f: Variant = d.get("facings")
	if typeof(f) != TYPE_DICTIONARY:
		return e + ["facings missing"]
	for k in FIXED_FACINGS:
		if str((f as Dictionary).get(k, "")) != FIXED_FACINGS[k]:
			e.append("facing %s must lead to %s" % [k, FIXED_FACINGS[k]])
	if (f as Dictionary).size() != 4:
		e.append("exactly four facings")
	var th: Variant = d.get("themes")
	if typeof(th) != TYPE_DICTIONARY:
		e.append("themes (id -> data file) missing")
	else:
		for t in RaveSave.THEMES:
			if not _is_str((th as Dictionary).get(t)):
				e.append("no data file for theme %s" % t)
	return e


## One rave's data file (content/raves/<theme>.json).
static func theme_data(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["theme data is not a dictionary"]
	if str(d.get("id", "")) not in RaveSave.THEMES:
		e.append("id is not a rave theme")
	for k in ["geography", "map", "track", "scene_id"]:
		if not _is_str(d.get(k)):
			e.append("%s missing" % k)
	var roles := {}
	for p in d.get("props", []):
		if typeof(p) != TYPE_DICTIONARY or not _is_str(p.get("id")) or not _is_str(p.get("sprite")):
			e.append("a prop needs id and sprite")
			continue
		if str(p.get("role", "")) not in PROP_ROLES:
			e.append("prop %s: role %s unknown" % [p["id"], p.get("role")])
		if not _is_str(p.get("spot")) and not _is_xz(p.get("at")):
			e.append("prop %s: needs spot or at" % p["id"])
		roles[str(p.get("role", ""))] = true
	for r in REQUIRED_PROP_ROLES:
		if not roles.has(r):
			e.append("no prop with role %s" % r)
	for c in d.get("customers", []):
		if typeof(c) != TYPE_DICTIONARY or not _is_str(c.get("id")) or not _is_str(c.get("sprite_set")) or not _is_num(c.get("count")):
			e.append("a customer group needs id, sprite_set, count")
	if (d.get("customers", []) as Array).is_empty():
		e.append("no customers")
	var fors := {}
	for g in d.get("guides", []):
		if typeof(g) != TYPE_DICTIONARY or not _is_str(g.get("id")) or not _is_str(g.get("sprite")) or not _is_str(g.get("spot")):
			e.append("a guide needs id, sprite, spot")
			continue
		if str(g.get("for", "")) not in GUIDE_FOR:
			e.append("guide %s: for %s unknown" % [g["id"], g.get("for")])
		fors[str(g.get("for", ""))] = true
	for want in GUIDE_FOR:
		if not fors.has(want):
			e.append("no guide for %s" % want)
	e.append_array(_four_distinct(d.get("ingredients"), "ingredients", ["id", "icon", "color"]))
	e.append_array(_four_distinct(d.get("cloakroom_symbols"), "cloakroom_symbols", ["id", "icon"]))
	var race: Variant = d.get("race")
	if typeof(race) != TYPE_DICTIONARY or not _is_str(race.get("entrance")) or not _is_str(race.get("course")):
		e.append("race {entrance, course} missing")
	var home: Variant = d.get("home")
	if typeof(home) != TYPE_DICTIONARY or not _is_str(home.get("threshold")) or str(home.get("route", "")) != "home":
		e.append("home {threshold, route: home} missing")
	var st: Variant = d.get("stations")
	for s in STATIONS:
		if typeof(st) != TYPE_DICTIONARY or typeof(st.get(s)) != TYPE_DICTIONARY or not _is_str(st[s].get("waypoint")) or not _is_str(st[s].get("route")):
			e.append("station %s {waypoint, route} missing" % s)
	return e


static func _four_distinct(list: Variant, name: String, keys: Array) -> Array:
	if typeof(list) != TYPE_ARRAY or (list as Array).size() != 4:
		return ["%s: exactly four" % name]
	var e: Array = []
	var seen := {}
	for x in list:
		for k in keys:
			if typeof(x) != TYPE_DICTIONARY or not _is_str(x.get(k)):
				e.append("%s: an entry lacks %s" % [name, k])
				return e
		if seen.has(str(x["id"])) or seen.has("icon:" + str(x["icon"])):
			e.append("%s: %s repeats" % [name, x["id"]])
		seen[str(x["id"])] = true
		seen["icon:" + str(x["icon"])] = true
	return e


# --- 3. rail destinations and arrival poses --------------------------------------------------------------------------------

## Route: {id, map, from: waypoint, legs: [{to: waypoint, bars 2..4, style, look?: waypoint or thing id}], arrive: {waypoint (the last leg's), choice_view: bool}, eye_m?: number}.
static func route(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["route is not a dictionary"]
	for k in ["id", "map", "from"]:
		if not _is_str(d.get(k)):
			e.append("%s missing" % k)
	var legs: Variant = d.get("legs")
	if typeof(legs) != TYPE_ARRAY or (legs as Array).is_empty():
		return e + ["legs: at least one"]
	var last := ""
	for l in legs:
		if typeof(l) != TYPE_DICTIONARY or not _is_str(l.get("to")):
			e.append("a leg needs to")
			continue
		var b := float(l.get("bars", 0.0))
		if b < LEG_BARS_MIN or b > LEG_BARS_MAX:
			e.append("leg to %s: %.1f bars (2 to 4, RunRail.pick_bars)" % [l["to"], b])
		if str(l.get("style", "walk")) not in MOVE_STYLES:
			e.append("leg to %s: style %s unknown" % [l["to"], l.get("style")])
		if not _is_num(l.get("hold_bars")) or float(l["hold_bars"]) < 0.0:
			e.append("leg to %s: hold_bars (>= 0) missing (ruling 35: move, then hold)" % l["to"])
		last = str(l["to"])
	var ar: Variant = d.get("arrive")
	if typeof(ar) != TYPE_DICTIONARY or str(ar.get("waypoint", "")) != last:
		e.append("arrive.waypoint must be the last leg's waypoint")
	elif typeof(ar.get("choice_view", null)) != TYPE_BOOL:
		e.append("arrive.choice_view (bool) missing")
	elif bool(ar["choice_view"]):
		if str(ar.get("hold", "")) != "window":
			e.append("a choice viewpoint holds for the whole window (arrive.hold: \"window\")")
		var lh := float((legs as Array)[-1].get("hold_bars", 0.0)) if typeof((legs as Array)[-1]) == TYPE_DICTIONARY else 0.0
		if lh < CHOICE_HOLD_BARS_MIN:
			e.append("the last leg holds %.1f bars at the choice viewpoint; at least %.0f" % [lh, CHOICE_HOLD_BARS_MIN])
	if d.has("eye_m") and (not _is_num(d["eye_m"]) or float(d["eye_m"]) < 0.5 or float(d["eye_m"]) > 3.0):
		e.append("eye_m is 0.5 to 3 m above the floor")
	return e


## The run's actions for a route started at song time `t0` (a decision beat or the cue-free guard): one `player_move` per leg, back to back, then a face
## look when a leg names one. The same mapping RunJourney.hotspot_actions makes of a cinematic's walk steps (without its dense-chart shortening), so a
## route IS a cinematic: {steps: [{move: "walk", to, bars, style, look_at}]}.
static func route_actions(r: Dictionary, t0: float, bar_s: float) -> Array:
	var out: Array = []
	var t := t0
	for l in r["legs"]:
		var bars := clampf(float(l.get("bars", 3.0)), LEG_BARS_MIN, LEG_BARS_MAX)
		out.append({"t0": t, "action": "player_move", "args": {"to": str(l["to"]), "style": str(l.get("style", "walk")), "bars": bars}})
		t += (bars + maxf(float(l.get("hold_bars", 0.0)), 0.0)) * bar_s  # move, then hold still (ruling 35): the next leg starts after the hold
	return out


static func route_as_cinematic(r: Dictionary) -> Dictionary:
	var steps: Array = []
	for l in r["legs"]:
		var s := {"move": "walk", "to": str(l["to"]), "bars": float(l.get("bars", 3.0)), "style": str(l.get("style", "walk"))}
		if float(l.get("hold_bars", 0.0)) > 0.0:  # (RunJourney.hotspot_actions holds the camera still for it: the next step starts after the hold, as route_actions)
			s["hold_bars"] = float(l["hold_bars"])
		if l.has("look"):
			s["look_at"] = str(l["look"])
		steps.append(s)
	return {"steps": steps}


# --- 4. activity entry, results and exit -----------------------------------------------------------------------------------

## An activity's content/minigames/<id>.json (the whole file is MinigameActivity.config). `kind` names the shared logic; the theme's data fills the rest.
static func activity_config(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["activity config is not a dictionary"]
	if not _is_str(d.get("id")) or not str(d.get("script", "")).begins_with("res://"):
		e.append("id and script (res://) missing")
	var mode := ActivityMode.of_config(d)
	if mode < 0:
		e.append("mode %s unknown" % d.get("mode"))
	var kind := str(d.get("kind", ""))
	if not ACTIVITY_KINDS.has(kind):
		return e + ["kind %s unknown" % kind]
	for k in ACTIVITY_KINDS[kind]:
		if not d.has(k):
			e.append("%s: %s missing" % [kind, k])
	if int(d.get("controls", -1)) != int(CONTROL_COUNT[kind]):
		e.append("%s: controls must be %d" % [kind, CONTROL_COUNT[kind]])
	if mode == ActivityMode.Mode.REPLACE and int(d.get("controls", 0)) not in [2, 4]:
		e.append("a replace activity has 2 or 4 controls (they stand where the pads were)")
	if mode == ActivityMode.Mode.REPLACE and float(d.get("lead_in_beats", -1.0)) < 4.0:
		e.append("a replace activity needs lead_in_beats >= 4 (one bar)")
	if mode != ActivityMode.Mode.RHYTHM and (int(d.get("wobble_at", 0)) != 0 or int(d.get("fall_at", 0)) != 0):
		e.append("wobble_at and fall_at are 0 outside rhythm mode")
	if kind == "bar" and (int(d.get("start_len", 0)) != 2 or int(d.get("max_len", 0)) != 3):
		e.append("bar: two ingredients, then three")
	if kind == "cloakroom" and int(d.get("symbols", 0)) != 4:
		e.append("cloakroom: exactly four symbols")
	if kind == "race":
		var ts: Variant = d.get("target_s")
		if not _is_xz(ts) or float(ts[0]) < 60.0 or float(ts[1]) > 90.0:
			e.append("race: target_s [60, 90]")
		if float(d.get("min_speed_frac", 0.0)) <= 0.0:
			e.append("race: min_speed_frac > 0 (every race finishes)")
	return e


## ActivityRequest: {activity_id, mode, theme, scene_id, config: Dictionary (the minigame json merged with the theme's data), return_pose: waypoint}.
static func activity_request(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["activity request is not a dictionary"]
	for k in ["activity_id", "scene_id", "return_pose"]:
		if not _is_str(d.get(k)):
			e.append("%s missing" % k)
	if ActivityMode.parse(d.get("mode")) < 0:
		e.append("mode unknown")
	if str(d.get("theme", "")) not in RaveSave.THEMES:
		e.append("theme must be a rave theme")
	if typeof(d.get("config")) != TYPE_DICTIONARY:
		e.append("config missing")
	return e


## ActivityResult (MinigameActivity.result()): {activity_id, completed, score, flags_to_set: [String], reason, race?: {won, position, time_s}}.
static func activity_result(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["activity result is not a dictionary"]
	if not _is_str(d.get("activity_id")):
		e.append("activity_id missing")
	if typeof(d.get("completed")) != TYPE_BOOL:
		e.append("completed (bool) missing")
	if typeof(d.get("score")) != TYPE_INT and not (typeof(d.get("score")) == TYPE_FLOAT and float(d["score"]) == floorf(float(d["score"]))):
		e.append("score (int) missing")
	if typeof(d.get("flags_to_set")) != TYPE_ARRAY:
		e.append("flags_to_set (Array) missing")
	else:
		for f in d["flags_to_set"]:
			if not _is_str(f):
				e.append("a flag is not a string")
	if str(d.get("reason", "")) not in RESULT_REASONS:
		e.append("reason %s unknown" % d.get("reason"))
	if d.has("race"):
		var r: Variant = d["race"]
		if typeof(r) != TYPE_DICTIONARY or typeof(r.get("won")) != TYPE_BOOL or not _is_num(r.get("position")) or not _is_num(r.get("time_s")):
			e.append("race {won, position, time_s} malformed")
	return e


## The block boundary judging resumes on after a replace activity finished at song time `t_done` (CONTRACTS.md 4, the exit sequence). The block
## whose start is chosen must not have been charted yet (its chart is made at the previous block's decision beat), and the pads must be back at least
## `lead_in_beats` before it. `t_phase0` is the downbeat of the current phase; blocks are `block_beats` long from there.
static func resume_boundary(t_done: float, t_phase0: float, beat_s: float, block_beats := 16, decision_beat := 12.75, lead_in_beats := 4.0) -> float:
	var k := int(floor((t_done - t_phase0) / (float(block_beats) * beat_s))) + 1  # the next block start after t_done
	for _i in 8:
		var start := t_phase0 + float(k * block_beats) * beat_s
		var charted_at := start - (float(block_beats) - decision_beat) * beat_s  # the previous block's decision beat
		if charted_at > t_done and start - t_done >= lead_in_beats * beat_s - 1e-9:
			return start
		k += 1
	return INF


# --- 5. input ownership ------------------------------------------------------------------------------------------------------

## The one owner of a tap. `area`: "hud" (the pause button), "strip" (the pad strip), "stage" (the picture). `mode`: an ActivityMode of the seated
## activity, -1 when none. `regions_on`: the scene's world regions are live (the bedsit; a race is an overlay activity and has them by its mode).
## `trial`: the Bassment owns the scene. `view_hit`: the activity's view has a target under the tap (rhythm/replace), else the tap belongs to no one ("").
static func tap_owner(area: String, mode: int, regions_on: bool, trial := false, view_hit := true) -> String:
	if area == "hud":
		return "hud"
	if trial:
		return "trial"
	if area == "strip":
		return "activity_controls" if mode == ActivityMode.Mode.REPLACE else "pads"
	if mode == ActivityMode.Mode.OVERLAY:
		return "world_regions"
	if mode >= 0:
		return "activity_view" if view_hit else ""
	return "world_regions" if regions_on else "hotspots"


## The four screen regions as [x, y, w, h] fractions of the stage area: inside it, never overlapping (they may leave gaps: a tap in a gap is no one's).
static func regions(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["regions is not a dictionary"]
	var rects := {}
	for k in REGIONS:
		var r: Variant = d.get(k)
		if typeof(r) != TYPE_ARRAY or (r as Array).size() != 4:
			e.append("region %s: [x, y, w, h]" % k)
			continue
		var rc := Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
		if rc.position.x < 0.0 or rc.position.y < 0.0 or rc.end.x > 1.0 + 1e-6 or rc.end.y > 1.0 + 1e-6 or rc.size.x <= 0.0 or rc.size.y <= 0.0:
			e.append("region %s leaves the stage area" % k)
		rects[k] = rc
	var ks := rects.keys()
	for i in ks.size():
		for j in range(i + 1, ks.size()):
			var a: Rect2 = rects[ks[i]]
			var b: Rect2 = rects[ks[j]]
			if a.intersection(b).get_area() > 1e-6:
				e.append("regions %s and %s overlap" % [ks[i], ks[j]])
	return e


## The region under a point given as fractions of the stage area ("" for none).
static func region_at(d: Dictionary, p: Vector2) -> String:
	for k in REGIONS:
		var r: Array = d[k]
		if Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])).has_point(p):
			return k
	return ""


# --- 6. save v3 ------------------------------------------------------------------------------------------------------------

static func save_v3(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["save is not a dictionary"]
	if int(d.get("version", 0)) != RaveSave.VERSION:
		e.append("version is not 3")
	for k in ["reached", "flags", "paths", "wallet"]:
		if typeof(d.get(k)) != TYPE_DICTIONARY:
			e.append("v2 key %s missing" % k)
	if str(d.get("bedsit_facing", "")) not in RaveSave.FACINGS:
		e.append("bedsit_facing")
	var th := str(d.get("rave_theme", "<missing>"))
	if th != "" and th not in RaveSave.THEMES:
		e.append("rave_theme")
	var raves: Variant = d.get("raves")
	if typeof(raves) != TYPE_DICTIONARY:
		return e + ["raves missing"]
	for t in RaveSave.THEMES:
		var r: Variant = (raves as Dictionary).get(t)
		if typeof(r) != TYPE_DICTIONARY:
			e.append("raves.%s missing" % t)
			continue
		for p in RaveSave.PUZZLES:
			if typeof(r.get(p)) != TYPE_BOOL:
				e.append("raves.%s.%s (bool)" % [t, p])
		var rc: Variant = r.get("race")
		if typeof(rc) != TYPE_DICTIONARY or not _is_num(rc.get("wins")) or not _is_num(rc.get("runs")) or not _is_num(rc.get("best")):
			e.append("raves.%s.race {wins, runs, best}" % t)
		elif int(rc["wins"]) > int(rc["runs"]):
			e.append("raves.%s.race: more wins than runs" % t)
	return e


# --- 7. bass lock ------------------------------------------------------------------------------------------------------------

## BassLock: {track, pack_dir (outside Git), stem_key, stem_file, locked_at_start, unlock: {boundary: "bar", ramp_beats}, applies_to: "track_scenes"}.
static func bass_lock(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["bass lock is not a dictionary"]
	for k in ["track", "stem_key", "stem_file"]:
		if not _is_str(d.get(k)):
			e.append("%s missing" % k)
	if typeof(d.get("locked_at_start")) != TYPE_BOOL:
		e.append("locked_at_start (bool)")
	var u: Variant = d.get("unlock")
	if typeof(u) != TYPE_DICTIONARY or str(u.get("boundary", "")) not in ["bar", "beat", "block"] or not _is_num(u.get("ramp_beats")):
		e.append("unlock {boundary: bar|beat|block, ramp_beats}")
	elif float(u["ramp_beats"]) <= 0.0 or float(u["ramp_beats"]) > 8.0:
		e.append("unlock.ramp_beats is above 0 and at most 8")
	return e


## The song time the unlock lands on: the first `boundary` at or after `t_fixed` (+ a small margin so the transport has a frame to act), on the grid
## that starts at `t_phase0`.
static func unlock_time(t_fixed: float, t_phase0: float, beat_s: float, boundary := "bar", margin_s := 0.05) -> float:
	var unit := {"beat": 1.0, "bar": 4.0, "block": 16.0}.get(boundary, 4.0) as float
	var span := unit * beat_s
	return t_phase0 + ceilf((t_fixed + margin_s - t_phase0) / span) * span


# --- 8. race course ----------------------------------------------------------------------------------------------------------

static func race_course(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["race course is not a dictionary"]
	for k in ["id", "map"]:
		if not _is_str(d.get(k)):
			e.append("%s missing" % k)
	if float(d.get("length_m", 0.0)) <= 0.0:
		e.append("length_m > 0")
	var cl: Variant = d.get("centreline")
	if typeof(cl) != TYPE_ARRAY or (cl as Array).size() < 2:
		e.append("centreline: at least two [x, z] points")
	else:
		var total := 0.0
		for i in range(1, (cl as Array).size()):
			if not _is_xz(cl[i]) or not _is_xz(cl[i - 1]):
				e.append("centreline point %d malformed" % i)
				return e
			total += Vector2(float(cl[i - 1][0]), float(cl[i - 1][1])).distance_to(Vector2(float(cl[i][0]), float(cl[i][1])))
		if total + 1e-6 < float(d.get("length_m", 0.0)):
			e.append("the centreline is shorter than length_m")
	var lanes: Variant = d.get("lanes")
	if typeof(lanes) != TYPE_ARRAY or (lanes as Array).size() < 2:
		e.append("lanes: at least two")
	else:
		var prev := -INF
		for l in lanes:
			if typeof(l) != TYPE_DICTIONARY or not _is_str(l.get("id")) or not _is_num(l.get("x")) or float(l["x"]) <= prev:
				e.append("lanes: {id, x} with x increasing left to right")
				break
			prev = float(l["x"])
	if not _is_num(d.get("eye_m")) or float(d["eye_m"]) <= 0.0:
		e.append("eye_m missing")
	var cam: Variant = d.get("camera")
	if typeof(cam) != TYPE_DICTIONARY:
		e.append("camera missing")
	else:
		for k in ["fov_deg", "pitch_deg", "lane_ease_beats", "speed_fov_gain", "max_roll_deg"]:
			if not _is_num(cam.get(k)):
				e.append("camera.%s missing" % k)
		if absf(float(cam.get("max_roll_deg", 0.0))) > 2.0:
			e.append("camera.max_roll_deg at most 2 (no roll that makes the pads hard to read)")
	var ck: Variant = d.get("cockpit")
	if typeof(ck) != TYPE_DICTIONARY or not _is_str(ck.get("sprite")) or not _is_num(ck.get("height_frac")) or float(ck["height_frac"]) > 0.35:
		e.append("cockpit {sprite, height_frac <= 0.35}")
	for b in d.get("blocks", []):
		if typeof(b) != TYPE_DICTIONARY or str(b.get("side", "")) not in ["L", "R"] or float(b.get("to_m", 0.0)) <= float(b.get("from_m", 0.0)):
			e.append("a building block needs side L|R and from_m < to_m")
	for v in d.get("sample_vehicles", []):
		e.append_array(vehicle(v))
	e.append_array(regions(d.get("regions")))
	return e


## VehicleThing (simulation -> renderer, every frame): {id, kind: rival|traffic, sprite, lane: float (lane index, fractional mid-change), distance_m, brake: bool}.
static func vehicle(v: Variant) -> Array:
	if typeof(v) != TYPE_DICTIONARY or not _is_str(v.get("id")) or str(v.get("kind", "")) not in ["rival", "traffic"] or not _is_str(v.get("sprite")) \
			or not _is_num(v.get("lane")) or not _is_num(v.get("distance_m")) or typeof(v.get("brake")) != TYPE_BOOL:
		return ["vehicle {id, kind, sprite, lane, distance_m, brake} malformed: %s" % str(v)]
	return []


## A point of the course: `distance_m` along the centreline, `lane` a lane index (fractional between lanes). {at: Vector2 (map ground x, z), yaw: degrees
## (StoryMap convention: 0 looks toward -z, forward = (-sin, -cos))}. Beyond the ends it clamps. The reference both streams compute the same way.
static func course_point(d: Dictionary, lane: float, distance_m: float) -> Dictionary:
	var pts: Array = d["centreline"]
	var lanes: Array = d["lanes"]
	var li := clampf(lane, 0.0, float(lanes.size() - 1))
	var i0 := int(floor(li))
	var i1 := mini(i0 + 1, lanes.size() - 1)
	var x_off := lerpf(float(lanes[i0]["x"]), float(lanes[i1]["x"]), li - float(i0))
	var left := maxf(distance_m, 0.0)
	for i in range(1, pts.size()):
		var a := Vector2(float(pts[i - 1][0]), float(pts[i - 1][1]))
		var b := Vector2(float(pts[i][0]), float(pts[i][1]))
		var seg := a.distance_to(b)
		if left <= seg or i == pts.size() - 1:
			var fwd := (b - a).normalized()
			var right := Vector2(-fwd.y, fwd.x)
			var at := a + fwd * minf(left, seg) + right * x_off
			return {"at": at, "yaw": rad_to_deg(atan2(-fwd.x, -fwd.y))}
		left -= seg
	return {}


# --- 9. choice states (ruling 35) ------------------------------------------------------------------------------------------

## ChoiceThing: {hotspot, thing (map thing id or actor), archetype, target: {bounds: "art", margin_px, min_px}, states: {<state>: {frames: [sprite], motion,
## frame_beats?, light: {floor_glow 0..1, tint?, lamp?}, sound?}}}. Every state of CHOICE_STATES is present; no state names a ring, mark or symbol.
static func choice_thing(d: Variant) -> Array:
	var e: Array = []
	if typeof(d) != TYPE_DICTIONARY:
		return ["choice thing is not a dictionary"]
	for k in ["hotspot", "thing", "archetype"]:
		if not _is_str(d.get(k)):
			e.append("%s missing" % k)
	var tg: Variant = d.get("target")
	if typeof(tg) != TYPE_DICTIONARY or str(tg.get("bounds", "")) != "art" or float(tg.get("margin_px", 99.0)) > HotspotContract.TOUCH_MARGIN_PX \
			or float(tg.get("min_px", 0.0)) < HotspotContract.MIN_PX:
		e.append("target {bounds: art, margin_px <= %d, min_px >= %d}" % [int(HotspotContract.TOUCH_MARGIN_PX), int(HotspotContract.MIN_PX)])
	var st: Variant = d.get("states")
	if typeof(st) != TYPE_DICTIONARY:
		return e + ["states missing"]
	for s in CHOICE_STATES:
		var x: Variant = (st as Dictionary).get(s)
		if typeof(x) != TYPE_DICTIONARY:
			e.append("state %s missing" % s)
			continue
		var fr: Variant = x.get("frames")
		if typeof(fr) != TYPE_ARRAY or (fr as Array).is_empty():
			e.append("state %s: frames (at least one sprite)" % s)
		else:
			for f in fr:
				var fs := str(f).to_lower()
				if fs.contains("ring") or fs.contains("mark") or fs.contains("arrow"):
					e.append("state %s: %s looks like a drawn symbol, not the artwork" % [s, f])
		if str(x.get("motion", "")) not in CHOICE_MOTIONS:
			e.append("state %s: motion %s unknown" % [s, x.get("motion")])
		var li: Variant = x.get("light", {})
		if typeof(li) != TYPE_DICTIONARY:
			e.append("state %s: light is a dictionary" % s)
		else:
			for k in li:
				if str(k) not in CHOICE_LIGHT_KEYS:
					e.append("state %s: light key %s unknown" % [s, k])
			if li.has("floor_glow") and (float(li["floor_glow"]) < 0.0 or float(li["floor_glow"]) > 1.0):
				e.append("state %s: floor_glow 0..1" % s)
			if li.has("lamp") and str(li["lamp"]) not in CHOICE_LAMPS:
				e.append("state %s: lamp %s unknown" % [s, li["lamp"]])
	# the states must read differently: available, selected and committed may not be the same picture
	var sig := {}
	for s in ["available", "selected", "committed"]:
		if typeof((st as Dictionary).get(s)) == TYPE_DICTIONARY:
			var x2: Dictionary = st[s]
			var key := JSON.stringify([x2.get("frames"), x2.get("motion"), x2.get("light", {})])
			if sig.has(key):
				e.append("states %s and %s look the same" % [sig[key], s])
			sig[key] = s
	return e


## The state a choice shows. `on_show`: it is staged in this block; `selected_id` / `committed_id`: the current selection and the commit ("" none);
## `success`: the committed outcome succeeded (cost when it did not); `window_closed`: the lock has passed.
static func choice_state(id: String, on_show: bool, selected_id: String, committed_id: String, success := true, window_closed := false) -> String:
	if committed_id != "":
		if committed_id == id:
			return "committed" if success else "cost"
		return "declined" if on_show else "idle"
	if not on_show:
		return "idle"
	if selected_id == id:
		return "selected"
	return "declined" if window_closed else "available"
