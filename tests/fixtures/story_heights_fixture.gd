extends RefCounted
## A small map with heights for the tests (docs/story/HEIGHTS_AND_PATHS.md): a walkway (west), a step up with a lower ceiling (step), a bridge between two pits (one marked
## "void", one a void by its depth) with railings on both edges, the far walkway (east) and a ledge 1.2 m above it (high, a drop for a walker, a step for a climb), and a closet
## behind a solid wall of the walkway (reached through the step). Textures are real tiles of the Mothership.
##
##   z  8 +-----------closet----------+
##      4 +---- west ----+-step-+--pit_n (void)--+---- east ----+-high-+
##      1 |              |      |=====bridge=====|              |      |
##     -1 |              |      |                |              |      |
##     -4 +--------------+------+--pit_s---------+--------------+------+
##       -10            -4     -2                6             12     14   x

const T := "res://assets/story/mothership/textures/%s.png"


static func data() -> Dictionary:
	return {
		"units_per_m": 1.0, "eye_height": 1.6, "start": "w0", "void_drop": 3.0,
		"fog": {"color": "#2a0a08", "density": 0.02},
		"textures": {"w": T % "wall_hull", "fl": T % "floor_grate", "ce": T % "ceil_hull", "riser": T % "floor_dais", "lip": T % "trim", "rail": T % "thing_pipes", "cliff": T % "wall_tube"},
		"sectors": [
			{"id": "west", "polygon": [[-10, -4], [-4, -4], [-4, 4], [-10, 4]], "floor": 0.0, "ceiling": 4.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "w"},
			{"id": "step", "polygon": [[-4, -4], [-2, -4], [-2, 4], [-4, 4]], "floor": 0.3, "ceiling": 3.5, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "w", "step_tex": "riser", "lip_tex": "lip"},
			{"id": "closet", "polygon": [[-10, 4], [-2, 4], [-2, 8], [-10, 8]], "floor": 0.3, "ceiling": 3.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "w"},
			{"id": "pit_n", "polygon": [[-2, 1], [6, 1], [6, 4], [-2, 4]], "floor": -10.0, "ceiling": 6.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "cliff", "void": true},
			{"id": "pit_s", "polygon": [[-2, -4], [6, -4], [6, -1], [-2, -1]], "floor": -10.0, "ceiling": 6.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "cliff"},
			{"id": "bridge", "polygon": [[-2, -1], [6, -1], [6, 1], [-2, 1]], "floor": 0.3, "ceiling": 6.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "w"},
			{"id": "east", "polygon": [[6, -4], [12, -4], [12, 4], [6, 4]], "floor": 0.3, "ceiling": 4.0, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "w"},
			{"id": "high", "polygon": [[12, -4], [14, -4], [14, 4], [12, 4]], "floor": 1.5, "ceiling": 4.5, "floor_tex": "fl", "ceil_tex": "ce", "wall_tex": "w", "step_tex": "riser"},
		],
		"walls": [
			{"sector": "west", "from": [-4, -4], "to": [-4, 4], "portal": "step"},
			{"sector": "step", "from": [-4, 4], "to": [-2, 4], "portal": "closet"},
			{"sector": "step", "from": [-2, -1], "to": [-2, 1], "portal": "bridge"},
			{"sector": "step", "from": [-2, 1], "to": [-2, 4], "portal": "pit_n"},
			{"sector": "step", "from": [-2, -4], "to": [-2, -1], "portal": "pit_s"},
			{"sector": "bridge", "from": [-2, 1], "to": [6, 1], "portal": "pit_n", "kind": "railing", "tex": "rail", "height": 1.0},
			{"sector": "bridge", "from": [-2, -1], "to": [6, -1], "portal": "pit_s", "kind": "railing", "tex": "rail"},
			{"sector": "bridge", "from": [6, -1], "to": [6, 1], "portal": "east"},
			{"sector": "pit_n", "from": [6, 1], "to": [6, 4], "portal": "east"},
			{"sector": "pit_s", "from": [6, -4], "to": [6, -1], "portal": "east"},
			{"sector": "east", "from": [12, -4], "to": [12, 4], "portal": "high"},
		],
		"waypoints": [
			{"id": "w0", "at": [-8, 0], "yaw": -90, "sector": "west"},
			{"id": "s1", "at": [-3, 0], "yaw": -90, "sector": "step"},
			{"id": "b1", "at": [2, 0], "yaw": -90, "sector": "bridge"},
			{"id": "e1", "at": [9, 0], "yaw": -90, "sector": "east"},
			{"id": "h1", "at": [13, 0], "yaw": -90, "sector": "high"},
			{"id": "c1", "at": [-8, 6], "yaw": 0, "sector": "closet"},
		],
	}
