class_name RaceStageHost
extends RefCounted
## The race's stage in the run (docs/bedsit/RACE.md; CONTRACTS.md 8 "the stage swap that shows the race map", hooks H8.2 and H8.4; rulings 37 and 38). RunPlay owns one and calls
## `step(t)` every frame right after `minigames.update(t)` (before RunMinigameHost.step, so the room is back before the host walks the camera home).
##
## - On entering a race scene (a content/races/<theme>.json `scene`, e.g. space_race: the hangar) the race's street stage (its `stage_world`, content/story/<world>.json and
##   map content/story/maps/<world>.json) is built once, hidden, beside the rave's (a build at the scene start, not at the seat).
## - When the RaceActivity is seated (the block start after the racer is chosen) the street becomes the active stage ON THAT DOWNBEAT, with no fade: the camera is the car's
##   (StoryStage.pose_fn = RaceActivity.camera_pose), the run's HUD and pads stay, the activity's things are pushed to it by RunMinigameHost, the four regions are the
##   driving choices (RunMinigameHost's regions layer, overlay mode).
## - When the race is done the rave's stage is shown again (RunPlay._show_world: the same deck, the same pads) with the camera where it stood, at the racer; the theme and the
##   puzzle flags were never touched. The race's `return_hotspot` (space_race.back, the way back to the hub) is selected as soon as selection is open, so the run walks
##   back to the hub at the scene's boundary. The race can be played again from the hub.
## While the street is shown, RunPlay keeps it on at a phase start of the race scene (`owns_stage`).

const RACES_DIR := "res://content/races"

var play: Control  # the RunPlay scene
var activity: RaceActivity = null
var world := ""  # the street's stage id (also its key in play.stages)
var owning := false  # the street is the active stage
var log: Array = []  # [{kind: build | swap_in | swap_out | return_selected, t, ...}]
var _prev_world := ""
var _return_id := ""
var _races: Array = []  # [{scene, stage_world, return_hotspot}] from content/races/*.json


func _init(p_play: Control) -> void:
	play = p_play
	if DirAccess.dir_exists_absolute(RACES_DIR):
		for f in DirAccess.get_files_at(RACES_DIR):
			if f.ends_with(".json"):
				var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(RACES_DIR.path_join(f)))
				if typeof(d) == TYPE_DICTIONARY and str(d.get("stage_world", "")) != "":
					_races.append(d)


## The street is the active stage (RunPlay keeps it on at a phase start).
func owns_stage() -> bool:
	return owning


func step(t: float) -> void:
	var mg: MinigameController = play.minigames
	if play.engine != null and not owning:
		for r: Dictionary in _races:
			if str(r.get("scene", "")) == str(play.engine.node_id):
				build(str(r["stage_world"]), t)
	var a: RaceActivity = mg.activity if mg.activity is RaceActivity else null
	if a != null and a != activity:
		activity = a
		world = str(a.data.get("stage_world", "race_" + a.theme))
		_return_id = str(a.data.get("return_hotspot", ""))
		build(world, t)
	if activity != null and not owning and mg.activity == activity and mg.state == "active" and t >= mg.seat_t:
		_swap_in(t)
	if owning and (mg.activity != activity or activity.is_done()):
		_swap_out(t)
	if not owning and _return_id != "" and not mg.active() and play.selection_open():
		if play.hotspot_select(_return_id):
			log.append({"kind": "return_selected", "t": t, "hotspot": _return_id})
			_return_id = ""


## Builds the street's stage (once): the same parts as RunPlay._build_stage, without the hotspot view and the deck (the rave's pads and deck stay).
func build(w: String, t: float) -> StoryStage:
	if play.stages.has(w):
		return play.stages[w]["stage"]
	var path := "res://content/story/%s.json" % w
	var loaded := StoryData.load_file(path)
	var sd: StoryData = loaded["data"]
	if sd == null:
		push_warning("RaceStageHost: %s does not load: %s" % [path, str(loaded["errors"])])
		return null
	var t0 := Time.get_ticks_usec()
	var assets := StoryAssets.load_art(sd.art)
	var st := StoryStage.new()
	st.name = "Stage_" + w
	st.set_anchors_preset(Control.PRESET_FULL_RECT)
	st.reduced = Session.reduced_effects
	st.high_contrast = Session.high_contrast
	st.motion = Session.effective_story_motion()
	st.lines = StoryLowRes.LINE_CHOICES[clampi(Session.story_lines, 0, 2)]
	st.visible = false
	st.process_mode = Node.PROCESS_MODE_DISABLED
	play._stage_host.add_child(st)
	var proxy: StoryRun = play.proxy
	var keep: StoryData = proxy.data
	proxy.data = sd
	proxy.crowd.setup(sd)
	st.setup(assets, sd, proxy)
	if st.map != null:
		st.attach_world(st.map, true)
	if keep != null:  # (the run's proxy goes back to the rave's data)
		proxy.data = keep
		proxy.crowd.setup(keep)
	if play.engine != null:
		st.set_tempo(60.0 / float(play.engine.beat_s))
	play.stages[w] = {"stage": st, "assets": assets, "data": sd, "deck": null, "waypoint": st.map.start_id if st.map != null else "", "race": true}
	log.append({"kind": "build", "t": t, "world": w, "ms": snappedf(float(Time.get_ticks_usec() - t0) / 1000.0, 0.1)})
	return st


func _swap_in(t: float) -> void:
	var st := build(world, t)
	if st == null:
		return
	_prev_world = str(play.active_world)
	for w in play.stages:
		var other: StoryStage = play.stages[w]["stage"]
		other.visible = w == world
		other.process_mode = Node.PROCESS_MODE_INHERIT if w == world else Node.PROCESS_MODE_DISABLED
	var act := activity
	st.pose_fn = func(tt: float) -> Dictionary: return act.camera_pose(tt)
	play.active_world = world
	owning = true
	log.append({"kind": "swap_in", "t": t, "from": _prev_world, "to": world})


func _swap_out(t: float) -> void:
	var st: StoryStage = play.stages[world]["stage"] if play.stages.has(world) else null
	if st != null:
		st.pose_fn = Callable()
		st.set_things([])
	owning = false
	if _prev_world != "" and play.stages.has(_prev_world):
		play._show_world(_prev_world)
	log.append({"kind": "swap_out", "t": t, "to": _prev_world, "result": activity.result() if activity != null else {}})
	activity = null
