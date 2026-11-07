class_name ChoiceShow
extends RefCounted
## How a choice shows its state with its own artwork (lead ruling 35b, contract 9, docs/art/CHOICE_STATES.md), pure: no node, no clock. HotspotView plays what `look` says.
##
## A hotspot may carry a `show` block; with none, the defaults of its show archetype (content/run/choice_show.json) apply, the archetype derived from its staging:
##   door    a door, boards, a sign or two set pieces of the map (ChoiceStaging `door`), a quest's gate: its frames are door_0 (shut) .. door_3 (wide); a lamp over it, a light on the floor.
##   figure  a person of the room, a billboard person of the map (the wizard), a herald: its frames are poses (FIGURE_FRAMES); a light on the floor under it.
##   object  a thing of the map: its frames are `self` (its own sprite) or sprites of the map's art; its own brightness is its lamp (`light: "self"`).
##   none    nothing is shown.
## The block: {archetype?, light?, floor_light?, set?, states?: {<state>: {frames?, frame_beats?, over_s?, motion?, light?: {floor_glow?, lamp?, tint?}, sound?}}}.
##   light        what light.lamp drives: "lamp" (the practical lamp of the choice art over the thing), "self" (the thing's own brightness), "gate" (a herald's gate), a thing id
##                of the map, or "none".
##   floor_light  what light.floor_glow drives: "spill" (the floor light under the thing), "pool" (a herald's pool of the quest's light), a thing id of the map, or "none".
##   set          a choice art set that wins over the map's (the quest paths' return door is the Warehouse's own: "warehouse").

const PATH := "res://content/run/choice_show.json"
const ARCHETYPES := ["door", "figure", "object", "none"]
const KEYS := ["archetype", "light", "floor_light", "set", "states"]
const STATE_KEYS := ["frames", "frame_beats", "over_s", "motion", "light", "sound"]
const LIGHTS := ["lamp", "self", "gate", "none"]  # or a thing id of the map
const FLOOR_LIGHTS := ["spill", "pool", "none"]  # or a thing id of the map
const DOOR_FRAMES := ["door_0", "door_1", "door_2", "door_3"]
const FIGURE_FRAMES := ["idle", "beckon", "step_toward", "gesture", "step_back", "recoil"]
const OFF_LIGHT := 0.8  # a thing whose own light is its lamp: its brightness at lamp "off" ..
const OPEN_LIGHT := 1.3  # .. and at "open"
const WARM := Color(1.0, 0.76, 0.48)  # the practical lamps' colour when a state gives no tint
const REFUSE_S := 0.4  # a refused tap shakes the thing and flickers its lamp this long (HotspotView.REFUSE_S)

static var _defaults: Dictionary = {}


static func defaults() -> Dictionary:
	if _defaults.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH)) if FileAccess.file_exists(PATH) else null
		_defaults = parsed if typeof(parsed) == TYPE_DICTIONARY else {}
	return _defaults


## The show archetype of a hotspot: its own `show.archetype`, else a quest entrance (a herald block) is a door (its gate, its pool), else from its staging: a door is a door, a person
## or a billboard figure a figure, anything else an object (a staging of `none`: nothing).
static func archetype_of(h: Dictionary) -> String:
	var s: Variant = h.get("show", null)
	if typeof(s) == TYPE_DICTIONARY and (s as Dictionary).has("archetype"):
		return str(s["archetype"])
	return default_archetype(h)


## The archetype the tables declare for a hotspot with no hand-made show block (tools/run/apply_staging.py writes it; the tests compare).
static func default_archetype(h: Dictionary) -> String:
	if typeof(h.get("herald", null)) == TYPE_DICTIONARY and not (h["herald"] as Dictionary).has("self"):
		return "door"
	match ChoiceStaging.archetype_of(h):
		"door":
			return "door"
		"person", "figure":
			return "figure"
		"none":
			return "none"
	return "object"


## The full show of a hotspot: the archetype's defaults with its own block merged over them. Always has archetype, light, floor_light, set and every state of ContractShapes.CHOICE_STATES.
static func of(h: Dictionary) -> Dictionary:
	var arch := archetype_of(h)
	var base: Dictionary = (defaults().get(arch, {}) as Dictionary).duplicate(true) if arch != "none" else {}
	var out := {"archetype": arch, "light": str(base.get("light", "none")), "floor_light": str(base.get("floor_light", "none")), "set": "", "states": base.get("states", {})}
	var b: Dictionary = h.get("herald", {}) if typeof(h.get("herald", null)) == TYPE_DICTIONARY else {}
	if arch == "door" and not b.is_empty():  # a quest entrance: its gate is the lamp (a herald with no gate: its pool alone), its pool the floor light
		out["light"] = "gate" if bool(b.get("gate", false)) else "none"
		out["floor_light"] = "pool"
	var an: Dictionary = h.get("anchor", {})
	if out["light"] == "self" and not an.has("thing"):  # (an object with no thing of its own: a lamp over the spot)
		out["light"] = "lamp"
	var own: Variant = h.get("show", null)
	if typeof(own) == TYPE_DICTIONARY:
		for k in own:
			if str(k) == "states" and typeof(own[k]) == TYPE_DICTIONARY:
				var sts: Dictionary = (out["states"] as Dictionary).duplicate(true)
				for s in own[k]:
					var m: Dictionary = (sts.get(s, {}) as Dictionary).duplicate(true)
					for kk in own[k][s]:
						if str(kk) == "light" and typeof(own[k][s][kk]) == TYPE_DICTIONARY:
							var li: Dictionary = (m.get("light", {}) as Dictionary).duplicate()
							li.merge(own[k][s][kk], true)
							m["light"] = li
						else:
							m[kk] = own[k][s][kk]
					sts[s] = m
				out["states"] = sts
			elif str(k) != "archetype":
				out[k] = own[k]
	return out


## The contract's ChoiceThing of a hotspot (ContractShapes.choice_thing validates it): the show's states with the touch target of the art.
static func choice_thing(h: Dictionary) -> Dictionary:
	var sh := of(h)
	var an: Dictionary = h.get("anchor", {})
	var thing := str(an.values()[0]) if not an.is_empty() and typeof(an.values()[0]) == TYPE_STRING else str(h.get("id", ""))
	var states := {}
	for s in sh["states"]:
		var x: Dictionary = (sh["states"][s] as Dictionary).duplicate(true)
		x.erase("over_s")
		states[s] = x
	return {"hotspot": str(h.get("id", "")), "thing": thing, "archetype": str(sh["archetype"]),
		"target": {"bounds": "art", "margin_px": HotspotContract.TOUCH_MARGIN_PX, "min_px": float(h.get("min_px", HotspotContract.MIN_PX))}, "states": states}


## The level of a lamp word (off, dim, lit, open) 0..1.
static func lamp_level(word: String) -> float:
	return float((defaults().get("lamp_levels", {}) as Dictionary).get(word, 0.0))


## The light of a state, before easing: [lamp level, floor glow, tint].
static func _light_of(sh: Dictionary, state: String) -> Array:
	var x: Dictionary = (sh["states"] as Dictionary).get(state, {})
	var li: Dictionary = x.get("light", {})
	var tint := Color.html(str(li["tint"])) if li.has("tint") else WARM
	return [lamp_level(str(li.get("lamp", "off"))), float(li.get("floor_glow", 0.0)), tint]


## What a choice shows `since_s` seconds into `state` (song time `t`, for the beat), having come from `prev`: {state, frame (a name of the archetype's frames), frame_i, motion,
## pose {dx, dy, sx, sy} (metres and scale), lamp (0..1), floor (0..1), tint (Color), sound (the state's cue), flicker (bool)}. The light eases from `prev`'s over ease_s; a cost
## flickers its lamp for cost_beats; `refused_s` (seconds since a refused tap, INF none) shakes it and flickers its lamp for REFUSE_S. Pure: the same arguments, the same look.
static func look(sh: Dictionary, state: String, since_s: float, beat_s: float, prev := "", t := 0.0, reduced := false, refused_s := INF) -> Dictionary:
	var x: Dictionary = (sh["states"] as Dictionary).get(state, {})
	var frames: Array = x.get("frames", [])
	var n := frames.size()
	var fi := 0
	if n > 1:
		if x.has("over_s"):  # played once and held
			fi = clampi(int(floor(maxf(since_s, 0.0) / maxf(float(x["over_s"]), 0.001) * float(n))), 0, n - 1)
		elif x.has("frame_beats") and not reduced:  # looped
			fi = posmod(int(floor(maxf(since_s, 0.0) / maxf(float(x["frame_beats"]) * beat_s, 0.001))), n)
	var cur := _light_of(sh, state)
	var lamp := float(cur[0])
	var flo := float(cur[1])
	var tint: Color = cur[2]
	var ease_s := float(defaults().get("ease_s", 0.25))
	if prev != "" and prev != state and since_s < ease_s:
		var was := _light_of(sh, prev)
		var k := clampf(maxf(since_s, 0.0) / ease_s, 0.0, 1.0)
		k = k * k * (3.0 - 2.0 * k)
		lamp = lerpf(float(was[0]), lamp, k)
		flo = lerpf(float(was[1]), flo, k)
		if state != "cost":  # (a cost goes red at once)
			tint = (was[2] as Color).lerp(tint, k)
	var motion := str(x.get("motion", "still"))
	var beats := t / beat_s if beat_s > 0.0 else 0.0
	var pose := ChoiceStaging.motion(motion, beats) if not reduced else ChoiceStaging.motion("still", 0.0)
	var flicker := false
	var cost_s := float(defaults().get("cost_beats", 2.0)) * beat_s
	if state == "cost" and since_s < cost_s:
		flicker = true
		pose = shake_pose(since_s / cost_s, reduced)
		if not reduced:
			lamp = lamp_level("dim") + (lamp_level("lit") - lamp_level("dim")) * float(int(floor(since_s / (beat_s * 0.125))) % 2)
	elif motion == "shake":
		pose = ChoiceStaging.motion("still", 0.0)
	if motion == "pulse" and not reduced and state != "cost":  # a pulse of its own light on the beat
		lamp *= 0.82 + 0.18 * pow(1.0 - fposmod(beats, 1.0), 3.0)
	if refused_s < REFUSE_S:  # a refused tap: a short shake and the lamp flickering red
		flicker = true
		pose = shake_pose(refused_s / REFUSE_S, reduced)
		tint = Color(1.0, 0.3, 0.2)
		if not reduced:
			lamp = lamp_level("dim") * float(int(floor(refused_s / 0.05)) % 2)
	return {"state": state, "frame": str(frames[fi]) if n > 0 else "", "frame_i": fi, "motion": motion, "pose": pose, "lamp": lamp, "floor": flo, "tint": tint,
		"sound": str(x.get("sound", "")), "flicker": flicker}


## A shake `k` (0..1) through it: side to side, fading (still in reduced motion).
static func shake_pose(k: float, still := false) -> Dictionary:
	var m := {"dy": 0.0, "sx": 1.0, "sy": 1.0, "dx": 0.0}
	if not still:
		m["dx"] = 0.06 * sin(clampf(k, 0.0, 1.0) * TAU * 4.0) * (1.0 - clampf(k, 0.0, 1.0))
	return m


## How far a door frame stands open, 0 (door_0) .. 1 (door_3); a frame with a set prefix ("warehouse/door_2") counts the same; anything else 0.
static func open_of(frame: String) -> float:
	var f := frame.get_file()
	var i := DOOR_FRAMES.find(f)
	return float(maxi(i, 0)) / float(DOOR_FRAMES.size() - 1)


## The brightness multiplier of a thing whose own light is its lamp, at lamp level `level`.
static func self_light(level: float) -> float:
	return lerpf(OFF_LIGHT, OPEN_LIGHT, clampf(level, 0.0, 1.0))


## The colour a lamp of the choice art is drawn in at `level` and `tint`: an unlit fixture is dark, a lit one takes the tint, an open one goes toward white-hot.
static func lamp_colour(level: float, tint: Color) -> Color:
	var l := clampf(level, 0.0, 1.0)
	var c := Color(0.42, 0.42, 0.46).lerp(tint, minf(l / 0.65, 1.0))
	if l > 0.65:
		c = c.lerp(Color(1.0, 0.97, 0.9), (l - 0.65) / 0.35 * 0.5)
	return Color(c.r, c.g, c.b, 1.0)


# --- validation ----------------------------------------------------------------------------------------------------------------

static func validate(h: Dictionary, hw: String, idx: Dictionary, errors: Array) -> void:
	var s: Variant = h.get("show", null)
	if s == null:
		return
	if typeof(s) != TYPE_DICTIONARY:
		errors.append("%s: show must be an object" % hw)
		return
	var sb: Dictionary = s
	var ok_map := bool(idx.get("ok", false))
	for k in sb:
		if str(k) not in KEYS:
			errors.append("%s: show.%s is not a field (%s)" % [hw, k, ", ".join(PackedStringArray(KEYS))])
	if sb.has("archetype") and str(sb["archetype"]) not in ARCHETYPES:
		errors.append("%s: show.archetype '%s' is not one of %s" % [hw, sb["archetype"], ", ".join(PackedStringArray(ARCHETYPES))])
	for pair in [["light", LIGHTS], ["floor_light", FLOOR_LIGHTS]]:
		var k2: String = pair[0]
		if sb.has(k2) and str(sb[k2]) not in pair[1] and not (ok_map and (idx["things"] as Dictionary).has(str(sb[k2]))):
			errors.append("%s: show.%s '%s' is not one of %s nor a thing of the map" % [hw, k2, sb[k2], ", ".join(PackedStringArray(pair[1]))])
	if sb.has("set") and typeof(sb["set"]) != TYPE_STRING:
		errors.append("%s: show.set names a set of the choice art" % hw)
	if not sb.has("states"):
		return
	if typeof(sb["states"]) != TYPE_DICTIONARY:
		errors.append("%s: show.states must be an object" % hw)
		return
	var arch := archetype_of(h)
	for st in sb["states"]:
		var where := "%s show.states.%s" % [hw, st]
		if str(st) not in ContractShapes.CHOICE_STATES:
			errors.append("%s: not a state (%s)" % [where, ", ".join(PackedStringArray(ContractShapes.CHOICE_STATES))])
			continue
		var x: Variant = sb["states"][st]
		if typeof(x) != TYPE_DICTIONARY:
			errors.append("%s: must be an object" % where)
			continue
		for k in x:
			if str(k) not in STATE_KEYS:
				errors.append("%s.%s is not a field (%s)" % [where, k, ", ".join(PackedStringArray(STATE_KEYS))])
		if x.has("frames"):
			if typeof(x["frames"]) != TYPE_ARRAY or (x["frames"] as Array).is_empty():
				errors.append("%s.frames: a list of at least one frame" % where)
			else:
				for f in x["frames"]:
					var fs := str(f)
					if fs.to_lower().contains("ring") or fs.to_lower().contains("mark") or fs.to_lower().contains("arrow"):
						errors.append("%s.frames: %s is a drawn symbol, not the artwork" % [where, fs])
					elif arch == "door" and fs.get_file() not in DOOR_FRAMES:
						errors.append("%s.frames: %s is not a door frame (%s)" % [where, fs, ", ".join(PackedStringArray(DOOR_FRAMES))])
					elif arch == "figure" and fs not in FIGURE_FRAMES:
						errors.append("%s.frames: %s is not a figure's pose (%s)" % [where, fs, ", ".join(PackedStringArray(FIGURE_FRAMES))])
		if x.has("motion") and str(x["motion"]) not in ContractShapes.CHOICE_MOTIONS:
			errors.append("%s.motion '%s' is not one of %s" % [where, x["motion"], ", ".join(PackedStringArray(ContractShapes.CHOICE_MOTIONS))])
		for k in ["frame_beats", "over_s"]:
			if x.has(k) and (typeof(x[k]) not in [TYPE_INT, TYPE_FLOAT] or float(x[k]) <= 0.0):
				errors.append("%s.%s is a number above 0" % [where, k])
		if x.has("light"):
			var li: Variant = x["light"]
			if typeof(li) != TYPE_DICTIONARY:
				errors.append("%s.light must be an object" % where)
			else:
				for k in li:
					if str(k) not in ContractShapes.CHOICE_LIGHT_KEYS:
						errors.append("%s.light.%s is not a field" % [where, k])
				if li.has("lamp") and str(li["lamp"]) not in ContractShapes.CHOICE_LAMPS:
					errors.append("%s.light.lamp '%s' is not one of %s" % [where, li["lamp"], ", ".join(PackedStringArray(ContractShapes.CHOICE_LAMPS))])
				if li.has("floor_glow") and (float(li["floor_glow"]) < 0.0 or float(li["floor_glow"]) > 1.0):
					errors.append("%s.light.floor_glow is 0..1" % where)
				if li.has("tint") and not Color.html_is_valid(str(li["tint"])):
					errors.append("%s.light.tint '%s' is not a colour" % [where, li["tint"]])
