class_name BedsitNav
extends RefCounted
## The bedsit's four world regions as pure functions (docs/briefs/BEDSIT_RAVES_BRIEF.md section 2, CONTRACTS.md contracts 1, 2 and 6): the opening is one room seen from one spot in four
## directions; the four screen regions are NOT the pads: left turns 90 degrees left, right turns 90 degrees right, bottom stays, top leaves for the rave of the current facing.
## Nothing here touches a node. The engine hook that calls `press` when a region is tapped is built on another branch (H1/H3/H5); until it lands the data, the tests and the dev overlay
## line are the whole of it. The facing lives in the save's `bedsit_facing` (RaveSave): `press` writes it into the dict it is given and nothing else (it never calls RaveSave.migrate,
## which would stamp version 3 on a save the loader still wants at version 2).
##
## Yaw: 0 faces -z (north), a positive yaw turns left, so facings are N 0, E -90, S 180, W 90 degrees (the map's waypoints bedsit_n/e/s/w, content/story/maps/bedsit.json).

const FLAG := "RW_BEDSIT"
const PATH_ID := "bedsit"
const THEMES_PATH := "res://content/bedsit/themes.json"
const ROUTES_PATH := "res://content/bedsit/routes.json"
const YAWS := {"N": 0.0, "E": -90.0, "S": 180.0, "W": 90.0}
const REGIONS := {"left": -1, "right": 1, "bottom": 0}  # turn direction per region (RaveSave.turn); "top" leaves
const THEME_NAMES := {"space": "Space", "magic": "Magic and unicorns", "dinos": "Dinosaurs", "transport": "Transport"}
const TURN_BARS := 1.0  # the camera turns smoothly over one bar and holds (the node's bedsit.viewpoint.turn_bars)


## RW_BEDSIT=1: the opening starts instead of the main run (default off). Also true when the run is the bedsit path.
static func enabled() -> bool:
	return OS.get_environment(FLAG) == "1"


static func load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


static func themes() -> Dictionary:
	return load_json(THEMES_PATH)


static func routes() -> Dictionary:
	return load_json(ROUTES_PATH)


## The facing the save holds ("N" when the key is missing or damaged).
static func facing_of(save: Dictionary) -> String:
	var f := str(save.get("bedsit_facing", "N"))
	return f if f in RaveSave.FACINGS else "N"


static func yaw_of(facing: String) -> float:
	return float(YAWS.get(facing, 0.0))


## The yaw after a turn from `yaw` (degrees, unwrapped so the camera takes the short way round): left adds 90, right subtracts 90, stay keeps it.
static func turned_yaw(yaw: float, dir: int) -> float:
	return yaw - 90.0 * float(dir)


## What a region does: {"action": "turn" | "stay" | "leave", "dir": -1 | 0 | 1}. An unknown region does nothing ("none").
static func region_action(region: String) -> Dictionary:
	if region == "top":
		return {"action": "leave", "dir": 0}
	if not REGIONS.has(region):
		return {"action": "none", "dir": 0}
	var d: int = REGIONS[region]
	return {"action": "stay" if d == 0 else "turn", "dir": d}


## The rave scene id a facing leaves for. While the raves do not exist (routes.json placeholder.active) it is still the id of the placeholder node that resolves to the bedsit.
static func route_for(facing: String, routes_data: Dictionary = {}) -> String:
	var r: Dictionary = routes_data if not routes_data.is_empty() else routes()
	return str(((r.get("routes", {}) as Dictionary).get(facing, {}) as Dictionary).get("scene", ""))


static func theme_for(facing: String, themes_data: Dictionary = {}) -> String:
	return RaveSave.theme_of(facing, themes_data if not themes_data.is_empty() else themes())


## One tap on a region. Writes the new facing into `save` (the run state) and returns what the host must do:
## {region, action, facing_before, facing_after, yaw_from, yaw_to, turn_bars, theme, route, leave (bool)}. `yaw_from` is the camera's current yaw when given (else the facing's own).
static func press(save: Dictionary, region: String, yaw_now: float = NAN, themes_data: Dictionary = {}, routes_data: Dictionary = {}) -> Dictionary:
	var act := region_action(region)
	var before := facing_of(save)
	var after := before
	var yaw_from := yaw_of(before) if is_nan(yaw_now) else yaw_now
	var yaw_to := yaw_from
	if str(act["action"]) == "turn":
		after = RaveSave.turn(before, int(act["dir"]))
		yaw_to = turned_yaw(yaw_from, int(act["dir"]))
		save["bedsit_facing"] = after
	var leave := str(act["action"]) == "leave"
	return {"region": region, "action": act["action"], "facing_before": before, "facing_after": after, "yaw_from": yaw_from, "yaw_to": yaw_to,
			"turn_bars": TURN_BARS if str(act["action"]) == "turn" else 0.0, "theme": theme_for(after, themes_data), "leave": leave,
			"route": route_for(after, routes_data) if leave else ""}


## The development overlay's part of the F3 line: compass letter and theme name. "" outside the bedsit path and when the overlay is off (the caller only asks while it is on).
static func debug_line(save: Dictionary, in_bedsit: bool) -> String:
	if not in_bedsit:
		return ""
	var f := facing_of(save)
	var th := theme_for(f)
	return "  compass %s  theme %s" % [f, str(THEME_NAMES.get(th, th))]
