class_name RunMinigameHost
extends RefCounted
## The run scene's side of a minigame (docs/BLACKJACK_INTEGRATION.md section 5.5): mounts the activity's view in the low-res viewport, hit-tests touches against it, plays the scripted taps
## (RW_MINIGAME_TAPS) and puts the journey back on the floor when the activity is done. RunPlay owns one and calls `step` after the controller's `update`.
##
## Exits while seated: `exits_for(scene)` lists the room's ways out for the activity (one per available exit hotspot, the default first). When the player gets up by one of its doors
## (the controller's `last_route`), the camera walks over to stand before that door and the door's exit hotspot is kept as the pending choice: it is selected through
## `RunPlay.hotspot_select` (the path a finger takes) as soon as it is on show (the final window, beat 48), so the last block then decides as if the player had touched that door in the room.
## A selection of anything else replaces it; it is dropped when the run leaves the scene or ends. While a door is pending, or armed and still selected, the rail takes no block steps:
## the camera waits by the door until the door walk.
##
## The view contract (every property is set only if the view has it; `hit` is required for touches to count):
##   now_fn: Callable () -> song time, beat_s: float, screen_size: Vector2 (the stage area's size in SCREEN pixels), reduced: bool, high_contrast: bool,
##   state_fn: Callable () -> Dictionary (the activity's `state()`; {} once it is gone), hit(local_pos: Vector2) -> String (the target id under `local_pos`, the tap position relative to the
##   stage area's top-left in screen pixels; "" for nothing). The view is a full-rect Control on canvas layer 3 inside the stage's low-res viewport, mouse_filter ignore.
##
## Modes (CONTRACTS.md 4 and 5, hook H5.4): while a REPLACE activity owns the pad strip (MinigameController.owns_strip: from the seat to a lead-in before the resume
## boundary) its `controls()` stand in the strip as a RunActivityInput "controls" layer: drawn by the pads themselves in their own slots (StoryPadView.slot_fn), morphing
## in over the beat before the seat and back over the beat after the strip is handed back (CONTRACTS.md 10); while the controls own it the note lane is hidden and the
## lane input is cleared and off; both come back when the strip is handed back. While an OVERLAY activity is seated a "regions" layer gives the four
## screen regions of the stage area (top, bottom, left, right): a tap there reaches the activity as `tap("region:<name>")`. RunPlay's dispatcher asks `control_tap` / `region_tap`.

## World-staged activities (CONTRACTS.md 10, ruling 38): the activity is handed `port` (a RunWorldPort, ctx["world"] in `setup`, through MinigameController.world_port) and
## stages itself with it: its things (`set_things`, or a `things()` method read every frame while it is seated) reach the active world's stage, its people the room's crowd
## (`people`), its feedback marks this host's feedback layer in the low-res viewport (`feedback`), its pieces the stage's piece switches. `make_view()` may return null.

const DOOR_STOP_M := 2.6  # how far short of a door the camera stops after getting up toward it: the door, its light and the far half of its floor ring stay in the picture (52 degree view, eye 1.6 m up)

var play: Control  # the RunPlay scene
var view: Control = null
var layer: CanvasLayer = null
var scripted: Array = []  # [{target, beats, done}] RW_MINIGAME_TAPS: target@beats after the player sat
var pending_exit := ""  # the exit hotspot the player got up toward, waiting for the final window ("" none)
var armed_exit := ""  # the pending exit once selected, until the selection changes or commits ("" none)
var _exit_scene := ""  # the scene the pending exit belongs to
var _viewed: MinigameActivity = null
var _was_active := false
var controls_layer: RunActivityInput = null  # replace mode: the activity's controls in the pad strip (null while the pads own it)
var regions_layer: RunActivityInput = null  # overlay mode: the four screen regions
var _strip_saved := {}  # the pads' and the note lane's visibility before the controls stood in
var _result_applied := false
var mode_log: Array = []  # [{kind: controls_on | controls_off | morph_in | morph_out | regions_on | regions_off | control | region | people | feedback | things_off, t, ...}]
var port: RunWorldPort  # the activity's world (CONTRACTS.md 10)
var feedback_layer: RunActivityFeedback = null  # the feedback marks, in the active stage's low-res viewport (made at the first feedback)
var _fb_stage: StoryStage = null  # the stage the feedback layer stands in
var _things_stage: StoryStage = null  # the stage the activity's things were last pushed to (null: none pushed)
var _port_things: Array = []  # the list the activity last gave through `port.set_things`
var _strip_owned := false  # the controls owned the strip last frame (the note lane and the lane input follow it)

const DEFAULT_REGIONS := {"top": [0.25, 0.0, 0.5, 0.42], "bottom": [0.25, 0.72, 0.5, 0.28], "left": [0.0, 0.0, 0.22, 1.0], "right": [0.78, 0.0, 0.22, 1.0]}  # CONTRACTS.md 5 (fixture input_ownership.json)


func _init(p_play: Control) -> void:
	play = p_play
	port = RunWorldPort.new(self)
	var spec := OS.get_environment("RW_MINIGAME_TAPS")
	for part in spec.split(",", false):
		var bits := part.strip_edges().split("@")
		if bits.size() == 2 and bits[0] != "":
			scripted.append({"target": bits[0], "beats": float(bits[1]), "done": false})


## Every frame after `minigames.update(t)`.
func step(t: float) -> void:
	var mg: MinigameController = play.minigames
	if mg.world_port == null:
		mg.world_port = port
	play.hud.silent = mg.active()
	if mg.activity != null and mg.activity != _viewed:
		_viewed = mg.activity
		_mount(_viewed)
	if mg.state == "active":
		for s in scripted:
			if not bool(s["done"]) and t >= mg.begin_t + float(s["beats"]) * play.engine.beat_s:
				s["done"] = true
				var ok := mg.tap(str(s["target"]), t)
				play.hotspot_log.append({"kind": "minigame_tap", "t": t, "target": str(s["target"]), "ok": ok, "scripted": true})
	_step_layers(t)
	_step_things(t)
	_step_view(t)
	if feedback_layer != null:
		feedback_layer.prune(t)
	if mg.done_t >= 0.0 and not _result_applied:  # (read once, when the activity is done: the flags are saved then, not at the boundary)
		_result_applied = true
		apply_result(mg.last_result, str(mg.request_info.get("theme", "")))
	elif mg.done_t < 0.0:
		_result_applied = false
	if _was_active and not mg.active():
		_unmount()
		_resume(mg.finish_t if mg.finish_t >= 0.0 and mg.finish_t <= t else t)  # (a replace activity: the camera goes back on the resume boundary)
	_was_active = mg.active()
	_step_exit(t)


## The controls layer while the activity owns the strip, the regions layer while an overlay activity is seated.
func _step_layers(t: float) -> void:
	var mg: MinigameController = play.minigames
	var want_layer := wants_controls_layer(mg, t, play.engine.beat_s)
	if want_layer and controls_layer == null:
		_show_controls(t)
	if controls_layer != null:
		controls_layer.t_in = mg.seat_t
		controls_layer.t_out = handback_t(mg)
		var own := mg.owns_strip(t)
		controls_layer.owning = own
		if own and not _strip_owned:
			_take_strip(t)
		elif not own and _strip_owned:
			_give_strip(t)
	if not want_layer and controls_layer != null:
		_hide_controls(t)
	var want_regions := mg.mode == ActivityMode.Mode.OVERLAY and mg.state in ["active", "leaving"]
	if want_regions and regions_layer == null:
		regions_layer = RunActivityInput.new()
		regions_layer.name = "ActivityRegions"
		regions_layer.kind = "regions"
		var regs: Dictionary = mg.activity.config.get("regions", {}) if mg.activity != null and typeof(mg.activity.config.get("regions", null)) == TYPE_DICTIONARY else {}
		if not ContractShapes.regions(regs).is_empty():
			regs = DEFAULT_REGIONS
		regions_layer.ids = ContractShapes.REGIONS.duplicate()
		regions_layer.show_regions = DevText.on()
		regions_layer.rects_fn = func() -> Array: return RunActivityInput.region_rects(regs, Rect2(play._stage_host.global_position, play._stage_host.size))
		_add_layer(regions_layer)
		mode_log.append({"kind": "regions_on", "t": t})
	elif not want_regions and regions_layer != null:
		regions_layer.queue_free()
		regions_layer = null
		mode_log.append({"kind": "regions_off", "t": t})


func _add_layer(l: Control) -> void:
	play.add_child(l)
	if play.hud != null and play.hud.get_parent() == play:  # under the HUD (the pause button stays on top)
		play.move_child(l, play.hud.get_index())


## Whether the controls layer stands now (a replace activity: from a beat before the seat until a beat after the strip is handed back; the morph needs it either side).
static func wants_controls_layer(mg: MinigameController, t: float, beat_s: float) -> bool:
	if mg.mode != ActivityMode.Mode.REPLACE or mg.activity == null or mg.state == "":
		return false
	if mg.owns_strip(t):
		return true
	var b := beat_s * RunActivityInput.MORPH_BEATS
	if mg.state == "entering":
		return t >= mg.seat_t - b
	return t < handback_t(mg) + b


## The song time the strip goes back to the pads (a lead-in before the resume boundary); INF while not known yet.
static func handback_t(mg: MinigameController) -> float:
	return mg.resume_t - mg.lead_in_s if mg.state == "resuming" and mg.resume_t >= 0.0 else INF


func _show_controls(t: float) -> void:
	var mg: MinigameController = play.minigames
	var specs: Array = mg.activity.controls() if mg.activity != null else []
	controls_layer = RunActivityInput.new()
	controls_layer.name = "ActivityControls"
	controls_layer.kind = "controls"
	for c: Variant in specs:
		var d: Dictionary = c if typeof(c) == TYPE_DICTIONARY else {"id": str(c)}
		controls_layer.ids.append(str(d.get("id", "")))
		controls_layer.labels.append(str(d.get("label", d.get("id", ""))))
		controls_layer.specs.append(d)
	var n := controls_layer.ids.size()
	var pv: Control = play.pad_view
	controls_layer.rects_fn = func() -> Array: return RunActivityInput.control_rects(pv.call("button_rects"), n)
	controls_layer.pad_view = pv
	controls_layer.beat_s = play.engine.beat_s
	controls_layer.now_fn = func() -> float: return play.hud.now_t
	controls_layer.t_in = mg.seat_t
	controls_layer.t_out = handback_t(mg)
	if "slot_fn" in pv:
		pv.set("slot_fn", controls_layer.slot)
	_add_layer(controls_layer)
	mode_log.append({"kind": "morph_in", "t": t, "ids": controls_layer.ids.duplicate(), "at": mg.seat_t})


func _hide_controls(t: float) -> void:
	if _strip_owned:
		_give_strip(t)
	if "slot_fn" in play.pad_view:
		play.pad_view.set("slot_fn", Callable())
	controls_layer.queue_free()
	controls_layer = null
	mode_log.append({"kind": "morph_out", "t": t})


## The controls take the strip's taps: the note lane goes (no cue is charted meanwhile) and the lane input is cleared and off. The pads stay drawn: they show the controls.
func _take_strip(t: float) -> void:
	_strip_owned = true
	_strip_saved = {"notes": play.note_lane.visible}
	play.lane_input.clear()
	play.lane_input.enabled = false
	play.note_lane.visible = false
	mode_log.append({"kind": "controls_on", "t": t, "ids": controls_layer.ids.duplicate()})


func _give_strip(t: float) -> void:
	_strip_owned = false
	play.note_lane.visible = bool(_strip_saved.get("notes", true))
	play.lane_input.enabled = true
	mode_log.append({"kind": "controls_off", "t": t})


## The activity's controls own the pad strip now (the pads are refused: RunPlay `_on_button_pressed`). The layer stands a beat longer either side for the morph, but
## owns no tap then.
func owns_strip() -> bool:
	return controls_layer != null and controls_layer.owning


## A tap in the pad strip while the controls own it: the control under it is pressed (the activity's `tap(id)`). Returns the id ("" for a gap).
func control_tap(pos: Vector2, t: float) -> String:
	if controls_layer == null:
		return ""
	var id := controls_layer.hit(pos)
	if id == "":
		return ""
	controls_layer.flash(id)
	var ok: bool = play.minigames.tap(id, t)
	mode_log.append({"kind": "control", "t": t, "id": id, "ok": ok})
	return id


## A tap in the stage area while an overlay activity is seated: the region under it reaches the activity as "region:<name>". Returns the region ("" for a gap).
func region_tap(pos: Vector2, t: float) -> String:
	if regions_layer == null:
		return ""
	var r := regions_layer.hit(pos)
	if r == "":
		return ""
	var ok: bool = play.minigames.tap("region:" + r, t)
	mode_log.append({"kind": "region", "t": t, "region": r, "ok": ok})
	return r


func _mount(a: MinigameActivity) -> void:
	var v: Control = a.make_view()
	if v == null or not play.stages.has(play.active_world):
		return
	var st: StoryStage = play.stages[play.active_world]["stage"]
	if st.lowres == null:
		return
	var mg: MinigameController = play.minigames
	v.set("now_fn", func() -> float: return play.hud.now_t)
	v.set("beat_s", play.engine.beat_s)
	v.set("reduced", Session.reduced_effects)
	v.set("high_contrast", Session.high_contrast)
	v.set("state_fn", func() -> Dictionary: return mg.activity.state() if mg.activity != null else {})
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer = st.lowres.add_overlay(v, "Minigame")
	layer.layer = 3
	view = v


func _unmount() -> void:
	if layer != null and is_instance_valid(layer):
		layer.queue_free()
	view = null
	layer = null
	_viewed = null


## The target under a touch: `local` is relative to the stage area's top-left in screen pixels, `area` the stage area's screen size. "" when there is no view or nothing is hit.
func hit(local: Vector2, area: Vector2) -> String:
	if view == null and play.has_method("rave_hit"):  # ruling 38: an activity with no view is touched in the room (a world region over its thing)
		return str(play.call("rave_hit", local, area))
	if view == null or not is_instance_valid(view) or not view.has_method("hit"):
		return ""
	view.set("screen_size", area)
	return str(view.call("hit", local))


## The activity is over: the camera walks back to the scene's home waypoint over two bars and the rail starts again from there, or, when the player got up by a door, toward that door.
func _resume(t: float) -> void:
	if play._door_phase == play.engine.phase_n:  # the sit latched this phase's door walk off; getting up inside the same phase hands it back (the walk still starts at beat 61 unless the route is already locked to here)
		play._door_phase = -1
	var mg: MinigameController = play.minigames
	if mg.last_route != "" and not _run_ending() and _leave_by(mg.last_route, t):
		return
	play._back_to_rail(t)


## The ActivityRequest for activity `id` in a rave (CONTRACTS.md 4, hook H4.3), from data: the registered config with the theme file's `theme_keys` merged in and
## "{theme}" filled in `flags_on_complete`; `mode` from the config; `return_pose` the station's choice viewpoint of the theme (`stations[kind].waypoint`, the race's
## `race.entrance`), else `home` (the scene's waypoint). {} outside a rave (`theme` ""): the activity keeps its registered config, as the blackjack table does.
static func build_request(id: String, cfg: Dictionary, theme: String, theme_data: Dictionary, scene_id: String, home: String) -> Dictionary:
	if theme == "" or cfg.is_empty():
		return {}
	var config: Dictionary = cfg.duplicate(true)
	for k: Variant in cfg.get("theme_keys", []):
		if theme_data.has(str(k)):
			config[str(k)] = (theme_data[str(k)] as Variant)
	var flags: Array = []
	for f: Variant in cfg.get("flags_on_complete", []):
		flags.append(str(f).replace("{theme}", theme))
	config["flags_on_complete"] = flags
	var kind := str(cfg.get("kind", id))
	var pose := ""
	var st: Variant = (theme_data.get("stations", {}) as Dictionary).get(kind, null)
	if typeof(st) == TYPE_DICTIONARY:
		pose = str((st as Dictionary).get("waypoint", ""))
	if pose == "" and kind == "race":
		pose = str((theme_data.get("race", {}) as Dictionary).get("entrance", ""))
	return {"activity_id": id, "mode": str(cfg.get("mode", "rhythm")), "theme": theme, "scene_id": scene_id, "return_pose": pose if pose != "" else home, "config": config}


## The theme file of rave `theme` (content/bedsit/themes.json names it; {} when there is none yet).
static func theme_data_of(theme: String, themes_path := "res://content/bedsit/themes.json") -> Dictionary:
	if theme == "" or not FileAccess.file_exists(themes_path):
		return {}
	var th: Variant = JSON.parse_string(FileAccess.get_file_as_string(themes_path))
	var p := str(((th as Dictionary).get("themes", {}) as Dictionary).get(theme, "")) if typeof(th) == TYPE_DICTIONARY else ""
	if p == "" or not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d if typeof(d) == TYPE_DICTIONARY else {}


## The activity's result once it is done (CONTRACTS.md 4): its flags go to the save (RunProgress.apply_activity_flag: "rave.<theme>.<puzzle>", else a run flag), a race
## record too. Applied once per activity.
func apply_result(res: Dictionary, theme: String) -> void:
	var prog: RunProgress = Session.run_progress
	if prog == null or res.is_empty():
		return
	for f: Variant in res.get("flags_to_set", []):
		prog.apply_activity_flag(str(f))
	var race: Variant = res.get("race", null)
	if typeof(race) == TYPE_DICTIONARY and theme != "":
		prog.record_race(theme, bool(race.get("won", false)), float(race.get("time_s", 0.0)))
	mode_log.append({"kind": "result", "activity": str(res.get("activity_id", "")), "flags": res.get("flags_to_set", []), "race": race != null})


## The ways out of scene `node_id` for the activity (MinigameActivity "exits"): one per exit hotspot of the scene available now (kind "exit", the final window, a scene route), the default first.
## The destination's scene and world come from the run data; its tint and light from the sector of its home waypoint when its map's stage is built (the art the door shows through it).
func exits_for(node_id: String) -> Array:
	return room_exits(play.data, play.hotspots, node_id, func(map_id: String) -> StoryMap:
		var rec: Variant = play.stages.get(map_id, null)
		var st: StoryStage = (rec as Dictionary).get("stage", null) if rec is Dictionary else null
		return st.map if st != null else null)


## `exits_for` without a scene (also the demo's): `hs` must be at `node_id`'s scene; `map_of(map id) -> StoryMap or null` gives the maps that may be read for colours.
static func room_exits(data: RunData, hs: RunHotspots, node_id: String, map_of: Callable) -> Array:
	var out: Array = []
	if hs == null or data == null or not data.nodes.has(node_id):
		return out
	var node: Dictionary = data.nodes[node_id]
	for h: Dictionary in hs.list():
		if str(h["kind"]) != "exit" or RunHotspots.window_of(h) != "final" or not hs.is_available(h):
			continue
		var to := str((h.get("on_success", {}) as Dictionary).get("route", ""))
		if to == "" or to == node_id or not data.nodes.has(to):
			continue
		var dest: Dictionary = data.nodes[to]
		var dir := ""
		for e: Dictionary in node.get("next", []):
			if str(e["to"]) == to:
				dir = str(e.get("dir", ""))
		var x := {"id": str(h["id"]), "route": to, "scene": str(dest.get("scene", "")), "world": str(dest.get("world", "")), "dir": dir, "default": bool(h.get("default", false))}
		x.merge(_light_of(dest, map_of.call(str(dest.get("map", ""))) if map_of.is_valid() else null))
		if bool(x["default"]):
			out.push_front(x)
		else:
			out.append(x)
	return out


## {tint (hex, "" unknown), light} of the sector a scene's home waypoint stands in on `map` (null: unknown).
static func _light_of(dest: Dictionary, map: Variant) -> Dictionary:
	if not (map is StoryMap) or not (map as StoryMap).has_waypoint(str(dest.get("waypoint", ""))):
		return {"tint": "", "light": 0.5}
	var m: StoryMap = map
	var sec := str(m.waypoint(str(dest["waypoint"])).get("sector", ""))
	for s: Dictionary in m.sectors:
		if str(s["id"]) == sec:
			return {"tint": (s["tint"] as Color).to_html(false), "light": float(s.get("light", 0.5))}
	return {"tint": "", "light": 0.5}


## The player got up by the door to `route`: the rail starts again from here, the camera walks over to stand before the door (two bars, stopping short and facing it, so the door stays
## in the picture), and the door's exit hotspot becomes the pending choice. False when no exit hotspot of this scene leads there now (the caller walks home instead).
func _leave_by(route: String, t: float) -> bool:
	var hs: RunHotspots = play.hotspots
	if hs == null or play.journey == null or play.journey.rail == null:
		return false
	var h := {}
	for c: Dictionary in hs.list():
		if str(c["kind"]) == "exit" and hs.is_available(c) and str((c.get("on_success", {}) as Dictionary).get("route", "")) == route:
			h = c
			break
	if h.is_empty():
		return false
	pending_exit = str(h["id"])
	armed_exit = ""
	_exit_scene = play.engine.node_id
	play.hotspot_log.append({"kind": "exit_pending", "t": t, "hotspot": pending_exit, "route": route, "phase": play.engine.phase_n})
	play.journey.rail.restart_here()
	var wp := str((h.get("anchor", {}) as Dictionary).get("waypoint", ""))
	if wp != "":
		play._journey_apply({"world": play.active_world, "t0": t, "action": "player_walk", "args": {"to": wp, "stop": DOOR_STOP_M, "face": wp, "bars": 2.0}})
	else:
		var home := str(play.data.nodes[play.engine.node_id].get("waypoint", ""))
		if home != "":
			play._journey_apply({"world": play.active_world, "t0": t, "action": "player_move", "args": {"to": home, "bars": 2.0, "style": "walk"}})
	play._journey_apply({"world": play.active_world, "t0": t, "action": "player_role", "args": {"role": "dancer"}})
	_step_exit(t)
	return true


## Every frame: the pending door is selected as soon as it is on show; a selection of anything else replaces it; leaving the scene or the run ending drops it.
func _step_exit(t: float) -> void:
	if pending_exit == "" and armed_exit == "":
		return
	var hs: RunHotspots = play.hotspots
	if hs == null or _run_ending() or play.engine.node_id != _exit_scene or play.minigames.active():
		_drop_exit(t, "gone")
		return
	if armed_exit != "" and hs.selected != armed_exit:
		armed_exit = ""
	if pending_exit == "":
		return
	if hs.selected != "" and hs.selected != pending_exit:
		_drop_exit(t, "replaced")
		return
	if hs.is_shown(pending_exit, play.engine.block, play.engine.window_open) and play.hotspot_select(pending_exit):
		armed_exit = pending_exit
		pending_exit = ""
		play.hotspot_log.append({"kind": "exit_armed", "t": t, "hotspot": armed_exit, "phase": play.engine.phase_n})


func _drop_exit(t: float, why: String) -> void:
	if pending_exit != "":
		play.hotspot_log.append({"kind": "exit_dropped", "t": t, "hotspot": pending_exit, "why": why})
	pending_exit = ""
	armed_exit = ""
	_exit_scene = ""


## True while the camera should wait by the chosen door: the rail takes no block steps (RunPlay `_handle`).
func holds_rail() -> bool:
	return pending_exit != "" or armed_exit != ""


func _run_ending() -> bool:
	return play._ended or play.engine.over or play.engine.energy <= 0.0


# --- world-staged activities (CONTRACTS.md 10, ruling 38) ----------------------------------------------------------------------------

## The stage of the active world (null when none is built).
func active_stage() -> StoryStage:
	if play.stages.has(play.active_world):
		return play.stages[play.active_world]["stage"]
	return null


## Every frame: while the activity is seated (active, leaving, or done and waiting for the resume boundary) its things reach the active stage, from its `things()` when it
## has one, else from the last `port.set_things`; once it is gone the stage gets [] (once).
func _step_things(t: float) -> void:
	var mg: MinigameController = play.minigames
	var st := active_stage()
	var seated := mg.activity != null and mg.state in ["active", "leaving", "resuming"]
	if seated and st != null:
		var arr: Array = mg.activity.call("things") if mg.activity.has_method("things") else _port_things
		if _things_stage != null and _things_stage != st:
			_things_stage.set_things([])
		st.set_things(arr)
		_things_stage = st
	elif _things_stage != null:
		_things_stage.set_things([])
		_things_stage = null
		_port_things = []
		mode_log.append({"kind": "things_off", "t": t})


## The activity's view (CONTRACTS.md 10, `view_pitch` in its config, degrees, negative down): seated, the camera stands where the hotspot's walk ended (the journey is
## not fed) and holds that pitch, a look of two bars put down every four beats from a beat before the seat until the activity is done (overlapping, so it never eases off
## in between); after that the last look eases out as the camera goes back to the rail. No cut, no fade, no zoom.
func _step_view(t: float) -> void:
	var mg: MinigameController = play.minigames
	if mg.activity == null or mg.state not in ["entering", "active", "leaving"]:
		_pitch_k = -1
		return
	var pitch := float(mg.activity.config.get("view_pitch", 0.0))
	if pitch == 0.0 or not play.stages.has(play.active_world):
		return
	var span := 4.0 * play.engine.beat_s
	var t0 := mg.seat_t - play.engine.beat_s
	if t < t0:
		return
	var k := int(floor((t - t0) / span))
	if k <= _pitch_k:
		return
	_pitch_k = k
	play._journey_apply({"world": play.active_world, "t0": t0 + float(k) * span, "action": "player_look", "args": {"by": 0.0, "pitch": pitch, "bars": 2.0}})
	mode_log.append({"kind": "view_pitch", "t": t0 + float(k) * span, "pitch": pitch})


var _pitch_k := -1  # the last four-beat slot the seated pitch was put down for (-1: none yet)


## RunWorldPort: the activity's things now (an activity without `things()` pushes them this way).
func set_things(arr: Array) -> void:
	_port_things = arr.duplicate(true)


## RunWorldPort: a named actor of the room plays `state` (StoryStage.people; an unknown actor is a no-op with a warning).
func people(id: String, state: String, t0: float, dur: float = 0.0) -> void:
	var st := active_stage()
	var r: Dictionary = st.people(id, state, t0, dur) if st != null else {}
	mode_log.append({"kind": "people", "t": t0, "id": id, "state": state, "dur": dur, "played": str(r.get("state", "")), "fallback": bool(r.get("fallback", false))})


## RunWorldPort: a feedback mark (tick, cross or glow) at thing `thing`'s screen point from song time `t` (RunActivityFeedback). Drawn in the active stage's low-res
## viewport, over the crowd; an unknown kind is ignored with a warning.
func feedback(thing: String, kind: String, t: float) -> void:
	if kind not in RunActivityFeedback.KINDS:
		push_warning("RunMinigameHost.feedback: unknown kind '%s' (tick, cross, glow)" % kind)
		return
	var st := active_stage()
	if st == null:
		return
	if feedback_layer == null or not is_instance_valid(feedback_layer) or _fb_stage != st:
		_make_feedback_layer(st)
	if feedback_layer != null:
		feedback_layer.entries.append({"thing": thing, "kind": kind, "t": t})
	mode_log.append({"kind": "feedback", "t": t, "thing": thing, "mark": kind})


func _make_feedback_layer(st: StoryStage) -> void:
	if feedback_layer != null and is_instance_valid(feedback_layer):
		var old: Node = feedback_layer.get_parent()
		feedback_layer.queue_free()
		if old != null and old is CanvasLayer:
			old.queue_free()
	feedback_layer = null
	_fb_stage = st
	var fb := RunActivityFeedback.new()
	fb.name = "ActivityFeedback"
	fb.beat_s = play.engine.beat_s
	fb.reduced = Session.reduced_effects
	fb.now_fn = func() -> float: return play.hud.now_t
	fb.point_fn = func(id: String) -> Variant: return st.world.thing_screen_point(id) if st.world != null else null
	fb.size_fn = func(id: String) -> float:
		var r: Variant = st.world.thing_screen_rect(id) if st.world != null else null
		return (r as Rect2).size.y if r != null else 0.0
	if st.lowres != null:
		var l := st.lowres.add_overlay(fb, "ActivityFeedback")
		l.layer = 4  # over the crowd and the things (1) and a view's layer (3)
	feedback_layer = fb


## RunWorldPort: a piece switch of the active stage ({t0, action: piece_on | piece_off | piece_pulse, args: {piece, bars?}}).
func stage_action(a: Dictionary) -> void:
	var st := active_stage()
	if st != null:
		st.apply(a)
