class_name ChoiceStaging
extends RefCounted
## The choice language (docs/CHOICE_CLARITY.md section 2), pure: how each option of a branching scene shows in the world that it is the CURRENT choice (the one that happens if
## the player does nothing more) or NOT, when it was just TOUCHED, and after the commit (COMMITTED: the one that happened; DECLINED: the others). Nothing here touches a node or a
## clock; the view (HotspotView) plays what these functions say, with times the caller gives, so the same taps at the same song times always look the same.
##
## A hotspot may carry a `staging` block (validated here, called from HotspotContract._validate_one); with none, the defaults of its archetype (content/run/choice_staging.json)
## are derived from its kind and anchor, so every shipped hotspot is staged without hand data:
##   person   the anchor's (or acting's) person: CURRENT beckons happy at the camera, OTHER pleads sad at the camera (still inviting), TOUCHED a quick happy nod,
##            COMMITTED a cheer, DECLINED a sad plead that fades. (StoryCrowd.direct_actor: these acts and faces are baked by tools/story/art/directed.py from the same file.)
##   door     an exit: a door stands at the anchor (`door`: "drawn" a door prop of assets/run/choice that swings open or shut; "bars" two boards nailed across a doorway that is
##            already a thing of the map; "sign" a wooden post whose arrow board points on (go) or hangs down crossed (not this way), for a road or a shore; "pieces" two set pieces of the map, `open_piece` / `shut_piece`; "none"), a lamp above it (round green with a chevron = this way;
##            square red with a bar = not this way) and a spill of light on the floor when open. The door is open when its route is the DESTINATION (the current option's
##            route, or the default way on when the current option has no route of its own).
##   object / feature   a lamp over the thing, and a motion on the thing when it is a billboard of the map (`current_motion` / `other_motion`).
##   figure   a billboard person of the map (the Warehouse wizard): its texture and motion per state (`current_tex`, `other_tex`: names in assets/run/choice).
##   custom   nothing by default: everything comes from `states`.
## Every archetype may also carry `states` {current?, other?, touched?, committed?, declined?}, each a list of steps played on top of the archetype's own look:
##   {piece: <map piece id>, op: on|off}                 a set piece of the map (a sail furled, a hatch chained, a lantern lit: art drawn as pieces)
##   {actor: <id>, act, face?, look_at?}                  another person of the room directed (the fishermen behind Simon, the friend who shrugs)
##   {thing: <map thing id>, tex?: <assets/run/choice name> | sprite?: <a sprite of the map's art>, motion?: still|bob|beckon|slump|pulse|sway_left|sway_right|lean}   a billboard's frame and pose
##   {lamp: go|stop|none}                                 the option's own lamp, overriding the archetype's
##   {prop: <assets/run/choice name>, at?: [dx, dy, dz] metres from the anchor, size?: metres, motion?}   a prop of the choice art stood at the anchor (an arrow sign, a sail)

const PATH := "res://content/run/choice_staging.json"
const ARCHETYPES := ["person", "door", "object", "feature", "figure", "custom", "none"]
const ROLES := ["current", "other", "committed", "declined"]
const STATE_KEYS := ["current", "other", "touched", "committed", "declined"]
const KEYS := ["archetype", "actor", "current", "other", "touched", "committed", "declined", "door", "open_piece", "shut_piece", "door_at", "width_m", "height_m", "lamp",
	"lamp_y", "current_tex", "other_tex", "thing", "current_motion", "other_motion", "touch", "states"]
const DOOR_STYLES := ["drawn", "bars", "sign", "pieces", "none"]
const MOTIONS := ["still", "bob", "beckon", "slump", "pulse", "sway_left", "sway_right", "lean"]
const LAMPS := ["go", "stop", "none"]
const ART_DIR := "res://assets/run/choice/"
const SWAP_BEATS := 1.0  # a door swings, a lamp swaps, within one beat of the touch

static var _defaults: Dictionary = {}


static func defaults() -> Dictionary:
	if _defaults.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH)) if FileAccess.file_exists(PATH) else null
		_defaults = parsed if typeof(parsed) == TYPE_DICTIONARY else {}
	return _defaults


## The archetype a hotspot is staged as: its own `staging.archetype`, else a person when it directs one, an exit is a door, a feature or an encounter a feature, anything else an object.
static func archetype_of(h: Dictionary) -> String:
	var s: Variant = h.get("staging", null)
	if typeof(s) == TYPE_DICTIONARY and (s as Dictionary).has("archetype"):
		return str(s["archetype"])
	if typeof(s) == TYPE_DICTIONARY and str((s as Dictionary).get("actor", "")) != "":
		return "person"
	if RunActing.actor_of(h) != "":
		return "person"
	match str(h.get("kind", "")):
		"exit":
			return "door"
		"feature", "encounter":
			return "feature"
	return "object"


## The full staging of a hotspot: the archetype's defaults with the hotspot's own block merged over them (a state's act spec key by key). Always has `archetype` and `touch`.
static func of(h: Dictionary) -> Dictionary:
	var arch := archetype_of(h)
	var d: Dictionary = (defaults().get(arch, {}) as Dictionary).duplicate(true) if arch != "custom" and arch != "none" else {"touch": {"w": 1.4, "h": 1.8}}
	d["archetype"] = arch
	var own: Variant = h.get("staging", null)
	if typeof(own) == TYPE_DICTIONARY:
		for k in own:
			if typeof(own[k]) == TYPE_DICTIONARY and typeof(d.get(k, null)) == TYPE_DICTIONARY and str(k) != "states":
				var m: Dictionary = (d[k] as Dictionary).duplicate(true)
				m.merge(own[k], true)
				d[k] = m
			else:
				d[k] = own[k] if typeof(own[k]) != TYPE_DICTIONARY and typeof(own[k]) != TYPE_ARRAY else own[k].duplicate(true)
	if arch == "person" and str(d.get("actor", "")) == "":
		d["actor"] = RunActing.actor_of(h)
	if arch == "door" and not (typeof(own) == TYPE_DICTIONARY and (own as Dictionary).has("door")):
		var an: Dictionary = h.get("anchor", {})
		if an.has("thing") or an.has("actor"):
			d["door"] = "bars"  # the doorway is a thing of the map already (a crack, a hatch): boards across it when shut, nothing drawn over it
	if arch == "figure" and str(d.get("thing", "")) == "":
		d["thing"] = str((h.get("anchor", {}) as Dictionary).get("thing", ""))
	if not d.has("states"):
		d["states"] = {}
	return d


## The role of an option: before the commit the current one is "current" and every other "other"; after it the committed one is "committed" and the rest "declined".
static func role_of(id: String, current: String, committed: String) -> String:
	if committed != "":
		return "committed" if id == committed else "declined"
	return "current" if id == current else "other"


## Whether an exit's door stands open: its success route is where the player is going (the destination).
static func door_open(h: Dictionary, dest: String) -> bool:
	var r := str((h.get("on_success", {}) as Dictionary).get("route", ""))
	return r != "" and r == dest


## How far a door stands open (0 shut .. 1 wide) `since_s` seconds after its target last changed, swinging over SWAP_BEATS.
static func open_amount(target_open: bool, since_s: float, beat_s: float) -> float:
	var k := clampf(since_s / maxf(SWAP_BEATS * beat_s, 0.001), 0.0, 1.0)
	k = k * k * (3.0 - 2.0 * k)
	return k if target_open else 1.0 - k


## The act a person option plays now: {act, face, look_at} ({} for nothing). `since_role_s`: seconds in this role; `since_touch_s`: since the player last touched it (INF never).
static func person_spec(st: Dictionary, role: String, since_role_s: float, since_touch_s: float, beat_s: float) -> Dictionary:
	match role:
		"current":
			var tc: Dictionary = st.get("touched", {})
			if not tc.is_empty() and since_touch_s < float(tc.get("beats", 1.5)) * beat_s:
				return tc
			return st.get("current", {})
		"other":
			return st.get("other", {})
		"committed":
			var c: Dictionary = st.get("committed", {})
			return c if since_role_s < float(c.get("beats", 4.0)) * beat_s else {}
		"declined":
			var dc: Dictionary = st.get("declined", {})
			return dc if since_role_s < float(dc.get("beats", 2.0)) * beat_s else {}
	return {}


## The steps of `states` for a role (a just-touched current option plays `touched`'s steps on top of `current`'s).
static func steps(st: Dictionary, role: String, touched_now := false) -> Array:
	var s: Dictionary = st.get("states", {})
	var out: Array = (s.get(role, []) as Array).duplicate()
	if touched_now and role == "current":
		out.append_array(s.get("touched", []) as Array)
	return out


## The lamp an option shows: "go", "stop" or "none" (a step {lamp} of its states wins over the archetype's `lamp`).
static func lamp_of(st: Dictionary, role: String, is_open: bool) -> String:
	for s in steps(st, role):
		if (s as Dictionary).has("lamp"):
			return str(s["lamp"])
	if not bool(st.get("lamp", false)):
		return "none"
	if str(st.get("archetype", "")) == "door":
		return "go" if is_open else "stop"
	return "go" if role == "current" or role == "committed" else "stop"


## A billboard's pose for a motion `u` beats in: {dy, sx, sy} (metres and scale; the feet stay on the floor).
static func motion(name: String, u: float) -> Dictionary:
	var m := {"dy": 0.0, "sx": 1.0, "sy": 1.0, "dx": 0.0}
	match name:
		"bob":
			m["dy"] = 0.05 * absf(sin(u * PI * 0.5))
		"beckon":  # a little hop towards you on every beat
			m["dy"] = 0.07 * absf(sin(u * PI))
			m["sy"] = 1.0 + 0.03 * absf(sin(u * PI))
		"slump":  # shrunk and still: shoulders down
			m["sy"] = 0.9
			m["sx"] = 1.04
		"pulse":
			m["sx"] = 1.0 + 0.06 * absf(sin(u * PI))
			m["sy"] = m["sx"]
		"sway_left":
			m["dx"] = -0.12 * absf(sin(u * PI * 0.5))
		"sway_right":
			m["dx"] = 0.12 * absf(sin(u * PI * 0.5))
		"lean":
			m["sx"] = 1.06
			m["dy"] = 0.03 * sin(u * PI * 0.5)
	return m


## The roles of a scene's staged options at once: {id: {role, open (door target), archetype}} for the snapshot the view plays and the tests read.
static func roles(staged: Array, current: String, committed: String, dest: String) -> Dictionary:
	var out := {}
	for h in staged:
		var id := str(h["id"])
		var st := of(h)
		out[id] = {"role": role_of(id, current, committed), "archetype": str(st["archetype"]), "open": door_open(h, dest) if str(st["archetype"]) == "door" else false}
	return out


# --- validation ----------------------------------------------------------------------------------------------------------------

static func _art_ok(name: String) -> bool:
	return ResourceLoader.exists(ART_DIR + name + ".png")


static func validate(h: Dictionary, hw: String, idx: Dictionary, errors: Array) -> void:
	var s: Variant = h.get("staging", null)
	if s == null:
		return
	if typeof(s) != TYPE_DICTIONARY:
		errors.append("%s: staging must be an object" % hw)
		return
	var st: Dictionary = s
	for k in st:
		if str(k) not in KEYS:
			errors.append("%s: staging.%s is not a field (%s)" % [hw, k, ", ".join(PackedStringArray(KEYS))])
	if st.has("archetype") and str(st["archetype"]) not in ARCHETYPES:
		errors.append("%s: staging.archetype '%s' is not one of %s" % [hw, st["archetype"], ", ".join(PackedStringArray(ARCHETYPES))])
	var ok_map := bool(idx.get("ok", false))
	if st.has("actor") and ok_map and not (idx["actors"] as Dictionary).has(str(st["actor"])):
		errors.append("%s: staging.actor '%s' has no home in the map" % [hw, st["actor"]])
	for ph in ["current", "other", "touched", "committed", "declined"]:
		if st.has(ph):
			var sub: Array = []
			HotspotContract._validate_act(st[ph], "%s staging.%s" % [hw, ph], idx, sub)
			errors.append_array(sub)
	if st.has("door") and str(st["door"]) not in DOOR_STYLES:
		errors.append("%s: staging.door '%s' is not one of %s" % [hw, st["door"], ", ".join(PackedStringArray(DOOR_STYLES))])
	if str(st.get("door", "")) == "pieces":
		for k in ["open_piece", "shut_piece"]:
			if not st.has(k):
				errors.append("%s: staging.door pieces needs %s" % [hw, k])
			elif ok_map and not (idx["pieces"] as Dictionary).has(str(st[k])):
				errors.append("%s: staging.%s '%s' is not a piece of the map" % [hw, k, st[k]])
	if st.has("door_at"):
		var da: Variant = st["door_at"]
		if typeof(da) != TYPE_ARRAY or (da as Array).size() != 2:
			errors.append("%s: staging.door_at must be [x, z]" % hw)
	for k in ["current_motion", "other_motion"]:
		if st.has(k) and str(st[k]) not in MOTIONS:
			errors.append("%s: staging.%s '%s' is not one of %s" % [hw, k, st[k], ", ".join(PackedStringArray(MOTIONS))])
	for k in ["current_tex", "other_tex"]:
		if st.has(k) and not _art_ok(str(st[k])):
			errors.append("%s: staging.%s '%s' is not in %s" % [hw, k, st[k], ART_DIR])
	if st.has("thing") and ok_map and not (idx["things"] as Dictionary).has(str(st["thing"])):
		errors.append("%s: staging.thing '%s' is not a thing of the map" % [hw, st["thing"]])
	if st.has("touch"):
		var t: Variant = st["touch"]
		if typeof(t) != TYPE_DICTIONARY or float((t as Dictionary).get("w", 0.0)) <= 0.0 or float((t as Dictionary).get("h", 0.0)) <= 0.0 or float(t.get("w", 0.0)) > 6.0 or float(t.get("h", 0.0)) > 6.0:
			errors.append("%s: staging.touch must be {w, h} in metres, above 0 and at most 6" % hw)
	if st.has("lamp") and typeof(st["lamp"]) != TYPE_BOOL:
		errors.append("%s: staging.lamp is true or false" % hw)
	if st.has("states"):
		_validate_states(st["states"], hw, idx, errors)


static func _validate_states(v: Variant, hw: String, idx: Dictionary, errors: Array) -> void:
	if typeof(v) != TYPE_DICTIONARY:
		errors.append("%s: staging.states must be an object {current, other, touched, committed, declined}" % hw)
		return
	var ok_map := bool(idx.get("ok", false))
	for role in v:
		var where := "%s staging.states.%s" % [hw, role]
		if str(role) not in STATE_KEYS:
			errors.append("%s: not a state (%s)" % [where, ", ".join(PackedStringArray(STATE_KEYS))])
			continue
		if typeof(v[role]) != TYPE_ARRAY:
			errors.append("%s: must be a list of steps" % where)
			continue
		var i := 0
		for step in v[role]:
			var sw := "%s[%d]" % [where, i]
			i += 1
			if typeof(step) != TYPE_DICTIONARY:
				errors.append("%s: a step is an object" % sw)
				continue
			var sp: Dictionary = step
			if sp.has("piece"):
				if str(sp.get("op", "")) not in ["on", "off"]:
					errors.append("%s: a piece step needs op on|off" % sw)
				if ok_map and not (idx["pieces"] as Dictionary).has(str(sp["piece"])):
					errors.append("%s: piece '%s' is not a piece of the map" % [sw, sp["piece"]])
			elif sp.has("actor"):
				if ok_map and not (idx["actors"] as Dictionary).has(str(sp["actor"])):
					errors.append("%s: actor '%s' has no home in the map" % [sw, sp["actor"]])
				var a := sp.duplicate()
				a.erase("actor")
				var sub: Array = []
				HotspotContract._validate_act(a, sw, idx, sub)
				errors.append_array(sub)
			elif sp.has("thing"):
				if ok_map and not (idx["things"] as Dictionary).has(str(sp["thing"])):
					errors.append("%s: thing '%s' is not a thing of the map" % [sw, sp["thing"]])
				if sp.has("sprite") and (typeof(sp["sprite"]) != TYPE_STRING or str(sp["sprite"]) == ""):
					errors.append("%s: sprite must name a sprite of the map's art" % sw)
				if sp.has("tex") and not _art_ok(str(sp["tex"])):
					errors.append("%s: tex '%s' is not in %s" % [sw, sp["tex"], ART_DIR])
				if sp.has("motion") and str(sp["motion"]) not in MOTIONS:
					errors.append("%s: motion '%s' is not one of %s" % [sw, sp["motion"], ", ".join(PackedStringArray(MOTIONS))])
			elif sp.has("prop"):
				if not _art_ok(str(sp["prop"])):
					errors.append("%s: prop '%s' is not in %s" % [sw, sp["prop"], ART_DIR])
				if sp.has("at") and (typeof(sp["at"]) != TYPE_ARRAY or (sp["at"] as Array).size() != 3):
					errors.append("%s: at must be [dx, dy, dz]" % sw)
				if sp.has("motion") and str(sp["motion"]) not in MOTIONS:
					errors.append("%s: motion '%s' is not one of %s" % [sw, sp["motion"], ", ".join(PackedStringArray(MOTIONS))])
			elif sp.has("lamp"):
				if str(sp["lamp"]) not in LAMPS:
					errors.append("%s: lamp '%s' is not one of %s" % [sw, sp["lamp"], ", ".join(PackedStringArray(LAMPS))])
			else:
				errors.append("%s: a step is a piece, an actor, a thing, a prop or a lamp" % sw)
