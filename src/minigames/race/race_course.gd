class_name RaceCourse
extends RefCounted
## A street race's course (content/races/courses/race_<theme>.json, written by tools/story/build_race.py with tools/story/race_course.py): the analytic centreline
## (straight runs and circular bends, `segments`), the lanes, the map pieces (which road sector holds a distance) and the camera numbers. Pure: no nodes.
## The same formulas as race_course.py, so a point the game computes lies where the generator cut the sectors. CONTRACTS.md 8's RaceCourse keys are all present
## (ContractShapes.race_course validates the file; ContractShapes.course_point on the dense `centreline` agrees with `point` to within the chord error).
##
## StoryMap conventions: ground (x, z), yaw degrees, 0 looks toward -z, positive turns left; forward (-sin, -cos), right (cos, -sin).

const DIR := "res://content/races/courses/%s.json"

var raw: Dictionary = {}
var id := ""
var length_m := 0.0  # the finish line
var runoff_m := 0.0  # the street goes on this far past the finish
var lanes: Array = []  # [{id, x}] left to right
var eye_m := 1.15
var camera: Dictionary = {}
var segs: Array = []
var pieces: Array = []  # [{i, s0, s1, road}]
var errors: Array = []


static func load_id(course_id: String) -> RaceCourse:
	var c := RaceCourse.new()
	var path := DIR % course_id
	if not FileAccess.file_exists(path):
		c.errors.append("course file missing: " + path)
		return c
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(d) != TYPE_DICTIONARY:
		c.errors.append("%s is not a JSON object" % path)
		return c
	c.build(d)
	return c


func build(d: Dictionary) -> void:
	raw = d
	id = str(d.get("id", ""))
	length_m = float(d.get("length_m", 0.0))
	runoff_m = float(d.get("runoff_m", 0.0))
	lanes = d.get("lanes", [])
	eye_m = float(d.get("eye_m", 1.15))
	camera = d.get("camera", {})
	segs = d.get("segments", [])
	pieces = d.get("pieces", [])
	errors.append_array(ContractShapes.race_course(d))
	if segs.is_empty():
		errors.append("course %s has no segments" % id)
	if pieces.is_empty():
		errors.append("course %s has no pieces" % id)


func lane_count() -> int:
	return lanes.size()


## The lateral offset (metres right of the centreline) of a fractional lane index.
func lane_x(lane: float) -> float:
	if lanes.is_empty():
		return 0.0
	var li := clampf(lane, 0.0, float(lanes.size() - 1))
	var i0 := int(floor(li))
	var i1 := mini(i0 + 1, lanes.size() - 1)
	return lerpf(float(lanes[i0]["x"]), float(lanes[i1]["x"]), li - float(i0))


static func fwd(yaw_deg: float) -> Vector2:
	var r := deg_to_rad(yaw_deg)
	return Vector2(-sin(r), -cos(r))


static func right(yaw_deg: float) -> Vector2:
	var r := deg_to_rad(yaw_deg)
	return Vector2(cos(r), -sin(r))


static func _arc(p0: Vector2, yaw0: float, turn: float, rad: float, s: float) -> Array:
	var sign := 1.0 if turn > 0.0 else -1.0
	var c := p0 - right(yaw0) * rad * sign
	var yaw := yaw0 + sign * rad_to_deg(s / rad)
	return [c + right(yaw) * rad * sign, yaw]


## {at: Vector2, yaw: float} of the point `s` metres along the centreline and `x` metres to its right (before 0 / past the end: straight on).
func point(s: float, x := 0.0) -> Dictionary:
	if segs.is_empty():
		return {"at": Vector2.ZERO, "yaw": 0.0}
	var g: Dictionary = segs[0]
	for sg: Dictionary in segs:
		if s >= float(sg["s0"]):
			g = sg
	var u := s - float(g["s0"])
	var p0 := Vector2(float(g["at"][0]), float(g["at"][1]))
	var c: Vector2
	var yaw: float
	if str(g["kind"]) == "arc" and u >= 0.0 and u <= float(g["len"]):
		var r: Array = _arc(p0, float(g["yaw"]), float(g["turn"]), float(g["radius"]), u)
		c = r[0]
		yaw = r[1]
	elif str(g["kind"]) == "arc" and u > float(g["len"]):
		var e: Array = _arc(p0, float(g["yaw"]), float(g["turn"]), float(g["radius"]), float(g["len"]))
		yaw = e[1]
		c = (e[0] as Vector2) + fwd(yaw) * (u - float(g["len"]))
	else:
		yaw = float(g["yaw"])
		c = p0 + fwd(yaw) * u
	return {"at": c + right(yaw) * x, "yaw": yaw}


## The road sector holding distance `s` (the first / last piece outside the course).
func road_at(s: float) -> String:
	if pieces.is_empty():
		return ""
	var lo := 0
	var hi := pieces.size() - 1
	if s < float(pieces[0]["s0"]):
		return str(pieces[0]["road"])
	while lo < hi:  # (pieces are in order of distance)
		var mid := (lo + hi + 1) / 2
		if float(pieces[mid]["s0"]) <= s:
			lo = mid
		else:
			hi = mid - 1
	return str(pieces[lo]["road"])


## The lane waypoint ids, per lane (the map's `ln<k>_<i>`).
func lane_waypoints() -> Array:
	return raw.get("lane_waypoints", [])
