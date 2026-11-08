class_name BedsitRoom
extends RefCounted
## The bedsit as a running scene (docs/briefs/BEDSIT_RAVES_BRIEF.md section 2, CONTRACTS.md 5 hook H5.5, rulings 35 and 41; docs/bedsit/LAUNCH.md "Playing it").
## RunPlay owns one (`bedsit`) and calls `enter` on every scene start; while the scene is the bedsit (its node carries a `bedsit` block) RunPlay's `world_regions` are the four
## regions of content/bedsit/themes.json and RunPlay.dispatch_tap hands every stage tap to `tap` (owner `world_regions`, ContractShapes.tap_owner):
##
##   left / right   BedsitNav.press turns 90 degrees: the camera turns on the spot to the facing's waypoint (bedsit_n/e/s/w) over one bar and then holds still (ruling 35a:
##                  a held, stationary result, no drift); the facing is written to the save (RunProgress.set_bedsit_facing) and a pending threshold pick is withdrawn
##   bottom         stays: the facing is kept and a pending threshold pick is withdrawn
##   top            the threshold of the current facing (bedsit.threshold_<f>) is selected: the route to that rave commits at the scene's lock and leaves on the boundary
##   the gap        the middle of the picture between the regions (x 0.25..0.75, y 0.42..0.72) is the room itself: a tap there hits the room's own hotspots that are not thresholds,
##                  i.e. the way out (bedsit.way_out, on the door in the WEST facing, needs the run flag bedsit_way_out, ruling 41) and the development exit
##
## Coming home (any scene start of the bedsit after another scene, and the run's first scene) faces the save's `bedsit_facing`: a cut to that facing's waypoint, the rail retargeted to it.
## Only the threshold of the current facing is on show (`items` filters the others out), so the touch target and the lit threshold follow the facing.

const TURN_BARS := BedsitNav.TURN_BARS  # one bar
const HOLD_BARS := 16.0  # after a turn (and from a scene start) the camera holds still: a whole scene's length, renewed by the next turn
const WAY_OUT := "bedsit.way_out"
const THRESHOLD_PREFIX := "bedsit.threshold_"
const START_FACING_ENV := "RW_BEDSIT_FACING"  # N, E, S or W: the run's first bedsit scene starts facing that way (written to the save like a turn); unset: the save's (a new run: north)

var scene: Node = null  # RunPlay
var active := false
var facing := "N"
var world := ""
var log: Array = []  # [{kind: enter | turn | stay | leave | room | refused, t, facing, region?, target?, ok?}] for the tests and the playtests


func _init(p_scene: Node = null) -> void:
	scene = p_scene


static func waypoint_of(f: String) -> String:
	return "bedsit_" + f.to_lower()


static func threshold_of(f: String) -> String:
	return THRESHOLD_PREFIX + f.to_lower()


static func is_threshold(id: String) -> bool:
	return id.begins_with(THRESHOLD_PREFIX)


## The four regions of the opening (content/bedsit/themes.json `regions`); {} when the file is damaged (ContractShapes.regions finds a fault).
static func regions() -> Dictionary:
	var r: Variant = BedsitNav.themes().get("regions", {})
	if typeof(r) != TYPE_DICTIONARY or not ContractShapes.regions(r).is_empty():
		return {}
	return r


## The gap between the four regions, as fractions of the stage area: the room's own things are touched there (the way out).
static func gap(regs: Dictionary) -> Rect2:
	if regs.is_empty():
		return Rect2()
	var top: Array = regs["top"]
	var bottom: Array = regs["bottom"]
	var left: Array = regs["left"]
	var right: Array = regs["right"]
	var x0 := maxf(float(left[0]) + float(left[2]), float(top[0]))
	var x1 := minf(float(right[0]), float(top[0]) + float(top[2]))
	var y0 := float(top[1]) + float(top[3])
	var y1 := float(bottom[1])
	return Rect2(x0, y0, x1 - x0, y1 - y0)


static func is_bedsit_node(node: Dictionary) -> bool:
	return typeof(node.get("bedsit", null)) == TYPE_DICTIONARY


## A scene starts at song time `t0` (RunPlay._on_phase_start, after the journey's own actions).
func enter(node_id: String, t0: float) -> void:
	var node: Dictionary = scene.data.nodes[node_id]
	if not is_bedsit_node(node):
		if active:
			active = false
			scene.world_regions = {}
			log.append({"kind": "away", "t": t0, "node": node_id})
		return
	var was := active
	active = true
	world = str(node["map"])
	scene.world_regions = regions()
	if not was and int(scene.engine.phase_n) == 1 and OS.get_environment(START_FACING_ENV) in RaveSave.FACINGS:  # (tools\dev\play_bedsit.cmd E: start facing east, a development aid)
		Session.run_progress.set_bedsit_facing(OS.get_environment(START_FACING_ENV))
	facing = BedsitNav.facing_of(Session.run_progress.data)
	_retarget(waypoint_of(facing), t0)
	if not was:  # coming home (or the run's first scene): the camera faces the saved facing, cut while the passage frame is shut, and holds
		scene._journey_apply({"world": world, "t0": t0, "action": "player_move", "args": {"to": waypoint_of(facing), "bars": 0.01, "style": "walk", "hold_bars": HOLD_BARS}})
		log.append({"kind": "enter", "t": t0, "facing": facing, "node": node_id})


## The rail of the bedsit stands on the facing's waypoint (home, every good and bad place, so a block decision never turns the camera back) and holds from `t` for HOLD_BARS:
## no rail step, glance or stroll while the camera turns and stands (RunRail._in_hold), so a turn lands in its one bar and stays put.
func _retarget(wp: String, t: float) -> void:
	var rail: RunRail = scene.journey.rail if scene.journey != null else null
	if rail == null:
		return
	rail.home = wp
	for list in [rail.good, rail.bad]:
		for p in list:
			(p as Dictionary)["to"] = wp
	rail.hold_from = t
	rail.busy_until = t + (TURN_BARS + HOLD_BARS) * rail.bar_s()


## A tap on the stage area while the bedsit is the scene. `at`: fractions of the stage area; `pos`: the tap in viewport coordinates (for the room's own hotspots). Returns the target
## ("left", "right", "bottom", "top", a hotspot id hit in the gap, or "").
func tap(at: Vector2, pos: Vector2, t: float) -> String:
	var regs: Dictionary = scene.world_regions
	if regs.is_empty():
		return ""
	var region := ContractShapes.region_at(regs, at)
	if region != "":
		region_tapped(region, t)
		return region
	if not gap(regs).has_point(at):
		return ""
	var id := room_hit(pos)
	if id != "":
		var ok: bool = scene.hotspot_select(id)
		log.append({"kind": "room", "t": t, "facing": facing, "target": id, "ok": ok})
		return id if ok else ""
	return ""


## One of the four regions (the dispatcher's tap, or a desktop arrow key). Returns BedsitNav.press's answer ({} when nothing happened).
func region_tapped(region: String, t: float) -> Dictionary:
	if not active:
		return {}
	var act := BedsitNav.region_action(region)
	var hs: RunHotspots = scene.hotspots
	match str(act["action"]):
		"turn":
			if hs.committed != "" or (hs.selected != "" and not scene.selection_open()):  # the way out is decided: the camera stays on it
				log.append({"kind": "refused", "t": t, "region": region, "facing": facing})
				return {}
			var r := BedsitNav.press({"bedsit_facing": facing}, region)
			facing = str(r["facing_after"])
			Session.run_progress.set_bedsit_facing(facing)
			_withdraw_threshold()
			_retarget(waypoint_of(facing), t)
			scene._journey_apply({"world": world, "t0": t, "action": "player_move", "args": {"to": waypoint_of(facing), "bars": TURN_BARS, "style": "walk", "hold_bars": HOLD_BARS}})
			log.append({"kind": "turn", "t": t, "region": region, "facing": facing, "from": r["facing_before"]})
			return r
		"stay":
			_withdraw_threshold()
			log.append({"kind": "stay", "t": t, "region": region, "facing": facing})
			return BedsitNav.press({"bedsit_facing": facing}, region)
		"leave":
			var id := threshold_of(facing)
			var ok: bool = scene.hotspot_select(id)
			log.append({"kind": "leave", "t": t, "region": region, "facing": facing, "target": id, "ok": ok})
			var res := BedsitNav.press({"bedsit_facing": facing}, region)
			res["ok"] = ok
			return res
	return {}


func _withdraw_threshold() -> void:
	var hs: RunHotspots = scene.hotspots
	if hs != null and is_threshold(hs.selected):
		scene.hotspot_deselect(hs.selected)


## Only the current facing's threshold is a choice on show in the bedsit (the others are behind or beside the camera): RunPlay.hotspot_items filters by this.
func shows(id: String) -> bool:
	return not active or not is_threshold(id) or id == threshold_of(facing)


## The room's own hotspot (not a threshold) under `pos` (viewport coordinates), "" for none.
func room_hit(pos: Vector2) -> String:
	var lay := room_layout()
	if lay.is_empty():
		return ""
	var host: Control = scene._stage_host
	return HotspotView.hit(lay, pos - host.global_position)


func room_layout() -> Array:
	if scene._stage_host == null or not scene.stages.has(scene.active_world):
		return []
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var pose: Dictionary = scene._exit_pose()
	if st.map == null or pose.is_empty():
		return []
	var items: Array = scene.hotspot_items().filter(func(e: Dictionary) -> bool: return not is_threshold(str((e["hotspot"] as Dictionary)["id"])) and str(e["state"]) != "committed")
	var host: Control = scene._stage_host
	return HotspotView.layout(items, st.map, st.crowds, pose, host.size, true, HotspotView.thing_widths(st))


## Where the way out stands on screen now (viewport coordinates): the projection of its anchor, whether or not it is open; null when it is out of the picture (another facing).
## The tests tap here.
func way_out_point() -> Variant:
	if scene._stage_host == null or not scene.stages.has(scene.active_world):
		return null
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var h: Dictionary = scene.hotspots.get_hotspot(WAY_OUT)
	var pose: Dictionary = scene._exit_pose()
	if h.is_empty() or st.map == null or pose.is_empty():
		return null
	var host: Control = scene._stage_host
	var lay := HotspotView.layout([{"hotspot": h, "state": "available"}], st.map, st.crowds, pose, host.size, true, HotspotView.thing_widths(st))
	if lay.is_empty():
		return null
	return host.global_position + (lay[0]["centre"] as Vector2)
