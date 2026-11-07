class_name SpaceRaveHost
extends RefCounted
## The Space rave's gameplay side (docs/briefs/BEDSIT_RAVES_BRIEF.md section 4, CONTRACTS.md 7): the bass puzzle's lock and its release, the rave's theme in the save, and the visible
## change (the stage lights come up, the crowd stands about until then and dances after). RunPlay owns one (a few lines: see docs/bedsit/LAUNCH.md) and calls `enter` on every scene start
## and `step` every frame; nothing here touches a node: the track audio, the progress and the stage actions are handed in.
##
## On entering the rave (`space_rave`, `space_stage`) with `bass_fixed` false for the theme, the bass stem is LOCKED (RunTrackAudio.lock_stems: availability, apart from the mix) and the
## stage starts dim (light group off) with the crowd capped at the quiet band. When the knob comes free (BassKnobActivity `freed_t`) the host schedules, at the next bar boundary
## (ContractShapes.unlock_time), `unlock_stem_at("bass", t_u, one bar)` and, at the same time, the stage lights and the crowd's dancing. The flag lands with the activity's result
## (RunMinigameHost.apply_result -> RunProgress.apply_activity_flag) and is kept for the run: re-entering the stage finds the bass free and the lights up. Leaving the rave frees the stem.
## Dev flag: RW_SPACE_BASS_FIXED=1 starts with the bass already fixed.

const THEME := "space"
const NODES := ["space_rave", "space_stage", "space_cloakroom", "space_bar", "space_race"]
const TRACK := "origin_unknown_valley_of_the_shadows_chase_status_remix"
const STEM := "bass"
const LIGHT_GROUP := ["pylon_beams", "ring_lights", "hologram_dome"]  # the stage's set pieces (content/story/maps/space_rave.json): the light group
const ACTIVITY_PIECES := {"cloakroom": ["cloak_lamp"], "bar": ["bar_shelf_1", "bar_shelf_2", "bar_shelf_3", "bar_shelf_4"]}  # what a finished activity leaves lit (the maps' pieces)
const QUIET_CAP := 25.0  # the crowd shows at most this energy (the quiet band) until the bass is back
const RAMP_BEATS := 4.0  # one bar

var progress: Variant = null  # RunProgress
var track_audio: Variant = null  # RunTrackAudio (lock_stems, unlock_stem_at)
var apply_fn: Callable = Callable()  # (action: Dictionary {t0, action, args}) -> void: a stage action on the rave's stage
var beat_s := 60.0 / 174.0
var phase_t0_fn: Callable = Callable()  # () -> float: the song time of the current phase's start (the bar grid)
var track := TRACK  # the track whose bass stem is locked (a test uses its fixture's)
var in_rave := false
var locked := false
var unlock_t := -1.0  # the bar line the bass comes in on once the knob is freed (-1: not scheduled)
var log: Array = []  # [{kind: enter | lock | unlock | leave | lights, t, ...}] for tests and playtests


static func is_rave_node(id: String) -> bool:
	return id in NODES


static func dev_bass_fixed() -> bool:
	return OS.get_environment("RW_SPACE_BASS_FIXED") == "1"


func bass_fixed() -> bool:
	return progress != null and bool(progress.puzzle_done(THEME, "bass_fixed"))


## A scene starts at song time `t` (every phase start, and the run's first scene).
func enter(node_id: String, t: float) -> void:
	if not is_rave_node(node_id):
		if in_rave:
			leave(t)
		return
	var first := not in_rave
	in_rave = true
	if progress != null and str(progress.rave_theme()) != THEME:
		progress.set_rave_theme(THEME)
	if dev_bass_fixed() and not bass_fixed() and progress != null:
		progress.apply_activity_flag("rave.%s.bass_fixed" % THEME)
	_activity_marks(t)
	if bass_fixed():
		_set_run_flag()
		locked = false
		_stage(t, true)
	else:
		locked = true
		if track_audio != null:
			track_audio.lock_stems(track, [STEM])
		unlock_t = -1.0
		_stage(t, false)
		log.append({"kind": "lock", "t": t, "node": node_id})
	if first:
		log.append({"kind": "enter", "t": t, "node": node_id, "bass_fixed": bass_fixed()})


## The two activities' visible change (ruling 38): once the cloakroom is done its counter lamp stays lit, once the bar is done its shelf glasses stay lit (pieces of the map, switched on
## when the room is entered, as the activities switched them on at the payoff), and the run flags `space_<activity>_done` the activity hotspots hide themselves by are set.
func _activity_marks(t: float) -> void:
	if progress == null:
		return
	for act in ACTIVITY_PIECES:
		var puzzle: String = "%s_done" % act
		if progress.puzzle_done(THEME, puzzle):
			progress.set_flag("%s_%s" % [THEME, puzzle])
			if apply_fn.is_valid():
				for p: String in ACTIVITY_PIECES[act]:
					apply_fn.call({"t0": t, "action": "piece_on", "args": {"piece": p}})
				log.append({"kind": "marks", "t": t, "activity": act})


## The rave is left (home, or the run goes on elsewhere): the bass stem is free again for whatever plays next.
func leave(t: float) -> void:
	in_rave = false
	if progress != null and str(progress.rave_theme()) == THEME:
		progress.set_rave_theme("")
	if locked and unlock_t < 0.0 and track_audio != null:
		track_audio.unlock_stem_at(STEM, _bar_after(t), RAMP_BEATS * beat_s)
	locked = false
	log.append({"kind": "leave", "t": t})


## Every frame with the live activity's state (`{}` when none): the frame the knob comes free, the unlock and the visible change are scheduled together on the next bar line.
func step(t: float, activity_state: Dictionary) -> void:
	if not in_rave or not locked or unlock_t >= 0.0:
		return
	if bool(activity_state.get("freed", false)):
		free_at(float(activity_state.get("freed_t", t)))


## The knob came free at song time `t_fixed`: the bass comes in on the next bar line, over one bar, and the stage answers on the same line. Returns that song time.
func free_at(t_fixed: float) -> float:
	if unlock_t >= 0.0:
		return unlock_t
	unlock_t = _bar_after(t_fixed)
	if track_audio != null:
		track_audio.unlock_stem_at(STEM, unlock_t, RAMP_BEATS * beat_s)
	locked = false
	_stage(unlock_t, true)
	log.append({"kind": "unlock", "t": t_fixed, "t_unlock": unlock_t, "ramp_s": RAMP_BEATS * beat_s})
	return unlock_t


func _bar_after(t: float) -> float:
	var t0: float = float(phase_t0_fn.call()) if phase_t0_fn.is_valid() else 0.0
	return ContractShapes.unlock_time(t, t0, beat_s, "bar")


## The stage's look: the light group on or off, the crowd's cap.
func _stage(t0: float, up: bool) -> void:
	if not apply_fn.is_valid():
		return
	for p in LIGHT_GROUP:
		apply_fn.call({"t0": t0, "action": "piece_on" if up else "piece_off", "args": {"piece": p}})
	apply_fn.call({"t0": t0, "action": "crowd_cap", "args": {"cap": 100.0 if up else QUIET_CAP}})
	log.append({"kind": "lights", "t": t0, "up": up})


func _set_run_flag() -> void:
	if progress != null:
		progress.set_flag("%s_bass_fixed" % THEME)


# --- ruling 38: the knob is a thing in the room ---------------------------------------------------------------------------------

## The world region over the knob: a touch at `local` (stage pixels from the stage area's top-left) is "knob" when it lies within the circle round the knob's drawn rect (`rect`: what
## StoryStage.thing_screen_rect("bass_knob") gives, null when it is not in the picture), at least 44 px wide on screen (the touch minimum) and 60 % of the rect's width otherwise.
static func hit_rect(local: Vector2, rect: Variant) -> String:
	if rect == null:
		return ""
	var r: Rect2 = rect
	var radius := maxf(44.0, maxf(r.size.x, r.size.y) * 0.6)
	return "knob" if local.distance_to(r.get_center()) <= radius else ""
