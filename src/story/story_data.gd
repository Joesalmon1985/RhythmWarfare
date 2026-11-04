class_name StoryData
extends RefCounted
## The Story Campaign chapter definition (content/story/night_one.json): loaded and validated against the actions the stage
## knows, the actor roster and the music pack. Pure data, no nodes. Bars are 1-based and may be fractional (bar 3.5 = beat 3 of
## bar 3's second half); ticks are derived with the loaded level's ticks per bar, never wall-clock time.

const PATH := "res://content/story/night_one.json"

## Every action the StoryStage implements. A chapter file may only name these.
const ACTIONS := [
	# light and set
	"doors_open", "lights_low_pulse", "lights_warm", "lights_cool", "lights_rave", "beams_sweep", "beams_fan", "beams_cross",
	"beams_off", "bass_reveal", "haze_burst", "led_eq", "led_rings", "led_bars", "led_wave", "disco_ball_on", "woofer_pump_on",
	"woofer_pump_off", "spotlight_hero", "spotlight_sweep", "spotlight_off", "riser_up", "riser_down", "confetti",
	"glowsticks_on", "glowsticks_off", "light_wave", "floor_ripple", "rave_peak",
	# crowd
	"front_row_sway", "clap_sync", "wave_across", "jump_sync", "hands_up_all", "circle_form", "hero_center", "hero_solo",
	"group_footwork", "bring_in", "gather_at_door", "regroup", "applause", "look_around", "ending_lean",
	# decision outcomes
	"new_dancers_enter", "dancers_step_back", "circle_spotlight_cheer", "circle_breaks_awkward", "drop_synchronised_jump",
	"drop_stumble", "final_chant", "final_flicker", "winback_cheer",
	# chapter set pieces (art manifest stage.pieces): args {piece, bars?}
	"piece_on", "piece_off", "piece_pulse",
	# the moving camera (chapters with extra rooms): move_to {view, style: walk|step|turn_left|turn_right, bars}, camera_look {dx, bars}, camera_push {zoom, bars}
	"move_to", "camera_look", "camera_push",
	# the player's journey in the 2.5D world (docs/STORY_25D_PLAN.md section 4.1): player_move {to: waypoint, style, bars}, player_look {yaw | at, bars},
	# player_role {role}, fx_queasy {amount 0..1, bars}, sick_beat {bars}
	"player_move", "player_look", "player_role", "fx_queasy", "sick_beat",
]

var raw: Dictionary = {}
var id := ""
var title := ""
var duration_bars := 128
var sequence_bars := 2
var initial_energy := 45.0
var blocks: Array = []
var decisions: Array = []
var endings: Dictionary = {}
var ending_order: Array = []
var actors: Array = []
var silhouettes: Array = []
var groups: Dictionary = {}
var acts: Array = []
var energy_cfg: Dictionary = {}
var art := "night_one"  # the art folder under assets/story/
var palettes: Dictionary = {}  # optional per-chapter light palettes {low, cool, warm, rave: [hex colours]}


static func load_file(path: String = PATH) -> Dictionary:
	var out := {"data": null, "errors": []}
	var text := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		out["errors"].append("%s is not a JSON object" % path)
		return out
	var d := StoryData.new()
	d.raw = parsed
	d.id = str(parsed.get("id", ""))
	d.title = str(parsed.get("title", ""))
	d.duration_bars = int(parsed.get("duration_bars", 128))
	d.sequence_bars = int(parsed.get("sequence_bars", 2))
	d.initial_energy = float(parsed.get("initial_energy", 45))
	d.blocks = parsed.get("blocks", [])
	d.decisions = parsed.get("decisions", [])
	d.endings = parsed.get("endings", {})
	d.ending_order = parsed.get("ending_order", [])
	d.actors = parsed.get("actors", [])
	d.silhouettes = parsed.get("silhouettes", [])
	d.groups = parsed.get("groups", {})
	d.acts = parsed.get("acts", [])
	d.energy_cfg = parsed.get("energy", {})
	d.art = str(parsed.get("art", "night_one"))
	d.palettes = parsed.get("palettes", {})
	d.validate(out["errors"])
	out["data"] = d
	return out


## Checks every reference. Appends a message per problem.
func validate(errors: Array) -> void:
	if blocks.size() != duration_bars / 8:
		errors.append("expected %d eight-bar blocks, found %d" % [duration_bars / 8, blocks.size()])
	var seen_actors := {}
	for a in actors:
		seen_actors[str(a["id"])] = true
	for k in blocks.size():
		var b: Dictionary = blocks[k]
		if int(b["start_bar"]) != 1 + 8 * k or int(b["bars"]) != 8:
			errors.append("block %s does not start at bar %d with 8 bars" % [b.get("id", "?"), 1 + 8 * k])
		if (b["events"] as Array).is_empty() and not _block_has_decision(str(b["id"])):
			errors.append("block %s has no authored action" % b["id"])
		for e in b["events"]:
			_check_event(e, errors, str(b["id"]))
	for d in decisions:
		for key in ["good", "bad"]:
			for a in d.get(key, []):
				var an := str(a["action"]) if typeof(a) == TYPE_DICTIONARY else str(a)
				if not (an in ACTIONS):
					errors.append("decision %s names unknown action %s" % [d["id"], an])
				elif typeof(a) == TYPE_DICTIONARY:
					_check_journey_args(an, a, errors, str(d["id"]))
		if float(d["at_bar"]) < 1.0 or float(d["at_bar"]) > float(duration_bars):
			errors.append("decision %s outside the song" % d["id"])
	for key in ending_order:
		if not endings.has(key):
			errors.append("ending %s is not defined" % key)
		else:  # an ending may stage where the player ends up: journey actions with the same arguments as a decision's
			for a in endings[key].get("journey", []):
				var an2 := str(a.get("action", ""))
				if not (an2 in ACTIONS) or not an2.begins_with("player_"):
					errors.append("ending %s journey names %s: only player_* actions" % [key, an2])
				else:
					_check_journey_args(an2, a, errors, "ending " + str(key))
	if ending_order.size() != 3:
		errors.append("three endings are required")
	for g in groups:
		for a in groups[g]:
			if not seen_actors.has(str(a)):
				errors.append("group %s names unknown actor %s" % [g, a])
	for a in actors:
		if str(a.get("archetype", "")).is_empty() or str(a.get("variant", "")).is_empty():
			errors.append("actor %s needs an archetype and a variant" % a["id"])


## Checks the chapter against its art set: every archetype/variant, silhouette shape and set piece it names must exist.
func validate_art(assets: StoryAssets, errors: Array) -> void:
	for a in actors:
		if assets.rig(str(a["archetype"]), str(a["variant"]), str(a.get("art", ""))).is_empty():
			errors.append("actor %s: no art for %s/%s" % [a["id"], a["archetype"], a["variant"]])
	for s in silhouettes:
		if not assets.manifest.get("silhouettes", {}).has(str(s["shape"])):
			errors.append("silhouette %s: unknown shape %s" % [s["id"], s["shape"]])
	var check := func(action: String, args: Dictionary, where: String) -> void:
		if action == "move_to" and not (str(args.get("view", "")) in assets.view_ids()):
			errors.append("%s: unknown view %s" % [where, args.get("view", "")])
		if action.begins_with("piece_") and assets.piece(str(args.get("piece", ""))).is_empty():
			errors.append("%s: unknown set piece %s" % [where, args.get("piece", "")])
	for b in blocks:
		for e in b["events"]:
			check.call(str(e["action"]), e, str(b["id"]))
			if e.has("else"):
				check.call(str(e["else"]), e, str(b["id"]))
	for d in decisions:
		for key in ["good", "bad"]:
			for entry in d.get(key, []):
				if typeof(entry) == TYPE_DICTIONARY:
					check.call(str(entry["action"]), entry, str(d["id"]))


func _block_has_decision(block_id: String) -> bool:
	for d in decisions:
		if str(d.get("block", "")) == block_id:
			return true
	return false


func _check_event(e: Dictionary, errors: Array, where: String) -> void:
	if not (str(e.get("action", "")) in ACTIONS):
		errors.append("%s: unknown action %s" % [where, e.get("action", "")])
	var bar := float(e.get("at_bar", 0))
	var span := float(e.get("bars", 0))
	if bar < 1.0 or bar >= float(duration_bars) + 1.0 or bar + span > float(duration_bars) + 1.0:
		errors.append("%s: action %s at bar %s runs outside the song" % [where, e.get("action", ""), bar])
	if e.has("else") and not (str(e["else"]) in ACTIONS):
		errors.append("%s: unknown else-action %s" % [where, e["else"]])
	_check_journey_args(str(e.get("action", "")), e, errors, where)
	if e.has("else"):
		_check_journey_args(str(e["else"]), e, errors, where)
	if e.has("group") and not groups.has(str(e["group"])) and not _group_in_actors(str(e["group"])):
		errors.append("%s: unknown group %s" % [where, e["group"]])


## Argument checks of the journey actions (the map checks that their targets exist: StoryMap.validate_chapter).
func _check_journey_args(action: String, args: Dictionary, errors: Array, where: String) -> void:
	match action:
		"player_move":
			if str(args.get("to", "")) == "":
				errors.append("%s: player_move needs a target waypoint (to)" % where)
			if str(args.get("style", "walk")) not in StoryMap.MOVE_STYLES:
				errors.append("%s: unknown move style %s" % [where, args.get("style")])
			if float(args.get("bars", 2.0)) <= 0.0:
				errors.append("%s: player_move needs a positive bars" % where)
		"player_role":
			if str(args.get("role", "")) not in StoryMap.ROLES:
				errors.append("%s: unknown role %s" % [where, args.get("role", "")])
		"fx_queasy":
			if float(args.get("amount", 0.5)) < 0.0 or float(args.get("amount", 0.5)) > 1.0:
				errors.append("%s: fx_queasy amount is 0..1" % where)


func _group_in_actors(group: String) -> bool:
	for a in actors:
		if str(a.get("group", "")) == group:
			return true
	return false


## "legendary" / "good" / "lost": the staged tableau of an ending (its position in ending_order, best first), so every chapter's own
## endings share the three crowd tableaux.
func tableau_of(ending: String) -> String:
	var i := ending_order.find(ending)
	return ["legendary", "good", "lost"][clampi(i, 0, 2)] if i >= 0 else "lost"


## The journey actions an ending stages (where the player ends up in its tableau), as director-style actions starting at t0: [{t0, bar, action, args, block, source}].
func ending_journey(ending: String, t0: float, bar_s: float) -> Array:
	var out: Array = []
	for ja in endings.get(ending, {}).get("journey", []):
		var args: Dictionary = (ja as Dictionary).duplicate()
		var an := str(args["action"])
		var after := float(args.get("after_bars", 0.0))
		args.erase("action")
		args.erase("after_bars")
		out.append({"t0": t0 + after * bar_s, "bar": 0.0, "action": an, "args": args, "block": "closing_tableau", "source": "ending"})
	return out


func ending_rank(ending: String) -> int:
	return 2 - clampi(maxi(ending_order.find(ending), 0), 0, 2)


func block_of_bar(bar: float) -> int:
	return clampi(int(floor((bar - 1.0) / 8.0)), 0, blocks.size() - 1)


func act_of_bar(bar: float) -> int:
	var idx := 0
	for i in acts.size():
		if bar >= float(acts[i]["start_bar"]):
			idx = i
	return idx


func band_of(energy: float) -> String:
	for b in energy_cfg.get("bands", []):
		if energy <= float(b["max"]):
			return str(b["id"])
	return "euphoric"


static func band_rank(band: String) -> int:
	return ["quiet", "dancing", "hype", "euphoric"].find(band)
