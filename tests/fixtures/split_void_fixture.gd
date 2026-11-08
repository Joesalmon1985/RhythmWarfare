extends RefCounted
## A small map with one pit split into three convex wedges (as a converted Doom map splits a pit: tests/test_split_void.gd) and one pit left whole. The rim is the walkway (west,
## floor 0.5) and the ledge (east, floor 1.0); the wedges are all marked "void" at -8 m, so the middle one touches only its sibling wedges. The well (north of the walkway) is an
## unsplit void at -5 m. Textures are real tiles of the Mothership.
##
##   z  8 +--- well (void) ---+
##      4 +------ west -------+-- w1 --+-- w2 --+-- w3 --+---- east ----+
##        |      (0.5)        | (void) | (void) | (void) |    (1.0)     |
##     -4 +-------------------+--------+--------+--------+--------------+
##       -10                 -4        0        4        8             14   x

const T := "res://assets/story/mothership/textures/%s.png"


static func data() -> Dictionary:
	var sec := func(id: String, poly: Array, floor_m: float, void_on: bool) -> Dictionary:
		var s := {"id": id, "polygon": poly, "floor": floor_m, "ceiling": 6.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "cliff" if void_on else "w"}
		if void_on:
			s["void"] = true
		return s
	return {
		"units_per_m": 1.0, "eye_height": 1.6, "start": "w0",
		"fog": {"color": "#2a0a08", "density": 0.02},
		"textures": {"w": T % "wall_hull", "fl": T % "floor_grate", "ce": T % "ceil_hull", "cliff": T % "wall_tube"},
		"sectors": [
			sec.call("west", [[-10, -4], [-4, -4], [-4, 4], [-10, 4]], 0.5, false),
			sec.call("w1", [[-4, -4], [0, -4], [0, 4], [-4, 4]], -8.0, true),
			sec.call("w2", [[0, -4], [4, -4], [4, 4], [0, 4]], -8.0, true),
			sec.call("w3", [[4, -4], [8, -4], [8, 4], [4, 4]], -8.0, true),
			sec.call("east", [[8, -4], [14, -4], [14, 4], [8, 4]], 1.0, false),
			sec.call("well", [[-10, 4], [-4, 4], [-4, 8], [-10, 8]], -5.0, true),
		],
		"walls": [
			{"sector": "west", "from": [-4, -4], "to": [-4, 4], "portal": "w1"},
			{"sector": "w1", "from": [0, -4], "to": [0, 4], "portal": "w2"},
			{"sector": "w2", "from": [4, -4], "to": [4, 4], "portal": "w3"},
			{"sector": "w3", "from": [8, -4], "to": [8, 4], "portal": "east"},
			{"sector": "west", "from": [-10, 4], "to": [-4, 4], "portal": "well"},
		],
		"waypoints": [
			{"id": "w0", "at": [-8, 0], "yaw": -90, "sector": "west"},
			{"id": "e1", "at": [11, 0], "yaw": 90, "sector": "east"},
		],
	}
