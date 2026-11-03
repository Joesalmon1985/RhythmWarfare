class_name StoryCharacter
extends Node2D
## One crowd dancer: a rig of textured parts (from the art manifest) drawn in one _draw call by forward kinematics, so draw order
## between dancers is just the stage's y-sort and a part's order is its manifest z. Poses are sampled analytically from the song
## position in beats (never accumulated frame time) and eased toward by song-time deltas, so pausing freezes everything and a replay
## is identical. States: idle, dance, cheer, sad, clap, hands_up, walk, footwork, look.

const STATES := ["idle", "dance", "cheer", "sad", "clap", "hands_up", "walk", "footwork", "look"]
const FACE_OF := {"idle": "neutral", "dance": "happy", "cheer": "cheer", "sad": "sad", "clap": "happy", "hands_up": "cheer", "walk": "neutral",
	"footwork": "happy", "look": "neutral"}
const BLEND_RATE := 7.0
const POSE_KEYS := ["bob", "jump", "lean", "head_tilt", "head_drop", "arm_l", "arm_r", "elb_l", "elb_r", "leg_l", "leg_r", "sway_x", "squash"]

var rig: Dictionary = {}  # the variant's manifest entry: {joints, parts, faces, glow_hand?, height}
var assets: StoryAssets
var actor_id := ""
var state := "idle"
var amp := 1.0  # personal energy scale 0.6..1.2
var rate := 0.5  # dance cycles per beat
var phase := 0.0  # personal offset in cycles (synchronised moves use 0)
var sync := false  # true: phase offset 0 (deliberate group moves)
var glow := false  # carries a glow stick
var glow_color := Color(0.4, 1.0, 1.0)
var reduced := false
var cur: Dictionary = {}
var _last_t := -1.0
var _swing := 0.0
var _swing_v := 0.0
var _joints: Dictionary = {}
var _parts: Array = []


func setup(p_assets: StoryAssets, rig_entry: Dictionary, id: String, p_seed: int) -> void:
	assets = p_assets
	rig = rig_entry
	actor_id = id
	var rng := RandomNumberGenerator.new()
	rng.seed = p_seed
	amp = rng.randf_range(0.8, 1.15)
	rate = 0.5 if rng.randf() < 0.75 else 1.0
	phase = rng.randf()
	for k in POSE_KEYS:
		cur[k] = 0.0
	_joints = {}
	for j in rig.get("joints", {}):
		var p: Array = rig["joints"][j]
		_joints[j] = Vector2(float(p[0]), float(p[1]))
	_parts = []
	for p in rig.get("parts", []):
		var e := assets._entry(p)
		if e.is_empty():
			continue
		e["joint"] = str(p["joint"])
		e["z"] = int(p.get("z", 0))
		e["swing"] = bool(p.get("swing", false))
		e["name"] = str(p.get("name", ""))
		_parts.append(e)
	_parts.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["z"] < b["z"])
	_face_entries = {}
	for k in rig.get("faces", {}):
		_face_entries[k] = assets._entry(rig["faces"][k])
	z_as_relative = true


var _face_entries: Dictionary = {}


## Target pose for `state` at song position `beats` (a pure function: the same inputs give the same pose).
func sample(st: String, beats: float, energy01: float) -> Dictionary:
	var ph := (0.0 if sync else phase) + beats * rate
	var w := TAU * ph
	var a := amp * (0.55 + 0.7 * energy01)
	var p := {}
	for k in POSE_KEYS:
		p[k] = 0.0
	match st:
		"idle":
			p["bob"] = 1.5 * sin(w)
			p["lean"] = 0.03 * sin(w * 0.5)
			p["arm_l"] = 0.14 + 0.05 * sin(w)
			p["arm_r"] = 0.14 - 0.05 * sin(w)
			p["elb_l"] = 0.15
			p["elb_r"] = 0.15
			p["head_tilt"] = 0.04 * sin(w * 0.5)
			p["sway_x"] = 2.0 * sin(w * 0.5)
		"dance":
			p["bob"] = 7.0 * a * (0.5 + 0.5 * cos(w * 2.0))
			p["lean"] = 0.1 * a * sin(w)
			p["arm_l"] = 0.8 + 0.55 * a * sin(w * 2.0)
			p["arm_r"] = 0.8 + 0.55 * a * sin(w * 2.0 + PI)
			p["elb_l"] = 0.7 + 0.45 * a * sin(w * 2.0 + 1.0)
			p["elb_r"] = 0.7 + 0.45 * a * sin(w * 2.0 + 1.0 + PI)
			p["head_tilt"] = 0.12 * sin(w)
			p["leg_l"] = 0.1 + 0.08 * a * sin(w * 2.0)
			p["leg_r"] = 0.1 - 0.08 * a * sin(w * 2.0)
			p["sway_x"] = 6.0 * a * sin(w)
			p["squash"] = 0.03 * a * sin(w * 4.0)
		"cheer":
			var hop := absf(sin(w * 2.0))
			p["jump"] = 20.0 * a * hop
			p["lean"] = 0.04 * sin(w)
			p["arm_l"] = 2.55 + 0.25 * a * sin(w * 4.0)
			p["arm_r"] = 2.55 + 0.25 * a * sin(w * 4.0 + 1.5)
			p["elb_l"] = 0.1 + 0.2 * hop
			p["elb_r"] = 0.1 + 0.2 * hop
			p["head_tilt"] = -0.08 + 0.06 * sin(w)
			p["leg_l"] = 0.12 * hop
			p["leg_r"] = 0.12 * hop
		"hands_up":
			p["bob"] = 3.0 * a * (0.5 + 0.5 * cos(w * 2.0))
			p["arm_l"] = 2.75 + 0.2 * sin(w * 2.0)
			p["arm_r"] = 2.75 + 0.2 * sin(w * 2.0 + PI)
			p["elb_l"] = 0.06
			p["elb_r"] = 0.06
			p["sway_x"] = 8.0 * sin(w)
			p["lean"] = 0.06 * sin(w)
			p["head_tilt"] = -0.1
		"sad":
			p["bob"] = 0.0
			p["head_drop"] = 7.0
			p["head_tilt"] = 0.16 + 0.03 * sin(w * 0.5)
			p["lean"] = 0.05
			p["arm_l"] = 0.04
			p["arm_r"] = 0.04
			p["elb_l"] = 0.55
			p["elb_r"] = 0.55
			p["sway_x"] = 1.5 * sin(w * 0.5)
		"clap":
			var c := 0.5 + 0.5 * sin(w * 4.0)
			p["bob"] = 3.0 * a * (0.5 + 0.5 * cos(w * 2.0))
			p["arm_l"] = 0.42 + 0.12 * c
			p["arm_r"] = 0.42 + 0.12 * c
			p["elb_l"] = 2.0 - 0.5 * c
			p["elb_r"] = 2.0 - 0.5 * c
			p["head_tilt"] = 0.06 * sin(w)
			p["lean"] = 0.04 * sin(w)
		"walk":
			var s := sin(TAU * beats * 1.3 + phase * TAU)
			p["bob"] = 3.5 * absf(s)
			p["leg_l"] = 0.4 * s
			p["leg_r"] = -0.4 * s
			p["arm_l"] = 0.16 - 0.35 * s
			p["arm_r"] = 0.16 + 0.35 * s
			p["elb_l"] = 0.3
			p["elb_r"] = 0.3
			p["head_tilt"] = 0.03 * s
		"footwork":
			var f := sin(w * 2.0)
			p["bob"] = 8.0 * a * (0.5 + 0.5 * cos(w * 4.0))
			p["leg_l"] = 0.45 * a * f
			p["leg_r"] = -0.45 * a * f
			p["arm_l"] = 0.5 + 0.4 * f
			p["arm_r"] = 0.5 - 0.4 * f
			p["elb_l"] = 1.2
			p["elb_r"] = 1.2
			p["lean"] = 0.12 * f
			p["sway_x"] = 8.0 * f
			p["head_tilt"] = 0.1 * f
		"look":
			p["bob"] = 1.0 * sin(w)
			p["head_tilt"] = 0.2 * sin(w * 0.5 + 1.0)
			p["arm_l"] = 0.5
			p["arm_r"] = 0.5
			p["elb_l"] = 1.0
			p["elb_r"] = 1.0
			p["lean"] = 0.03 * sin(w * 0.5)
	return p


## Ease toward the state's pose. `t` is song seconds (audio time); dt comes from it, so nothing runs while the song is paused.
func update_pose(t: float, bpm: float, energy01: float) -> void:
	var dt := 0.0 if _last_t < 0.0 else clampf(t - _last_t, 0.0, 0.25)
	_last_t = t
	var beats := t * bpm / 60.0
	var target := sample(state, beats, energy01)
	var k := 1.0 - exp(-dt * BLEND_RATE)
	if dt == 0.0 and _first:
		k = 1.0
	_first = false
	for key in POSE_KEYS:
		cur[key] = lerpf(float(cur[key]), float(target[key]), k)
	_swing_v += ((-_swing * 40.0) - _swing_v * 5.0 - float(cur["sway_x"]) * 0.18) * dt
	_swing = clampf(_swing + _swing_v * dt, -0.6, 0.6)
	queue_redraw()


var _first := true


func face_name() -> String:
	return str(FACE_OF.get(state, "neutral"))


func _draw() -> void:
	if rig.is_empty() or _parts.is_empty():
		return
	var P: Dictionary = cur
	var hips := _joints.get("hips", Vector2(0, -95))
	var root := Transform2D(0.0, Vector2(float(P["sway_x"]), -float(P["jump"])))
	var hip_xf := root * Transform2D(0.0, hips + Vector2(0, -float(P["bob"]) * 0.5))
	var torso_xf := hip_xf * Transform2D(float(P["lean"]), Vector2.ZERO)
	var neck := _joints.get("neck", Vector2(0, -190)) - hips
	var head_xf := torso_xf * Transform2D(float(P["head_tilt"]), neck + Vector2(0, float(P["head_drop"])))
	var xfs := {"hips": hip_xf, "torso": torso_xf, "head": head_xf}
	for side in ["l", "r"]:
		var sg := 1.0 if side == "l" else -1.0
		var sh_pos: Vector2 = _joints.get("shoulder_" + side, Vector2(sg * 30, -170)) - hips
		var sh_xf: Transform2D = torso_xf * Transform2D(sg * float(P["arm_" + side]), sh_pos + Vector2(0, float(P["head_drop"]) * 0.5))
		xfs["shoulder_" + side] = sh_xf
		var el_off: Vector2 = _joints.get("elbow_" + side, Vector2(sg * 36, -130)) - _joints.get("shoulder_" + side, Vector2(sg * 30, -170))
		xfs["elbow_" + side] = sh_xf * Transform2D(-sg * float(P["elb_" + side]), el_off)
		var hp_pos: Vector2 = _joints.get("hip_" + side, Vector2(sg * 14, -92)) - hips
		xfs["hip_" + side] = hip_xf * Transform2D(sg * float(P["leg_" + side]), hp_pos)
	for part in _parts:
		var j: String = part["joint"]
		var xf: Transform2D = xfs.get(j, hip_xf)
		if part["swing"]:
			xf = xf * Transform2D(_swing, Vector2.ZERO)
		var sc: float = part["scale"]
		var tex: Texture2D = part["tex"]
		if tex == null:
			continue
		draw_set_transform_matrix(xf * Transform2D().scaled(Vector2(sc, sc)))
		draw_texture(tex, -part["pivot"], Color.WHITE)
	_draw_face(head_xf)
	if glow:
		_draw_glow(xfs)
	draw_set_transform_matrix(Transform2D.IDENTITY)


func _draw_face(head_xf: Transform2D) -> void:
	var f: Dictionary = _face_entries.get(face_name(), _face_entries.get("neutral", {}))
	if f.is_empty() or f["tex"] == null:
		return
	draw_set_transform_matrix(head_xf * Transform2D().scaled(Vector2(f["scale"], f["scale"])))
	draw_texture(f["tex"], -f["pivot"], Color.WHITE)


var glow_on := false


func _draw_glow(xfs: Dictionary) -> void:
	if not glow_on:
		return
	var gs := assets.sprite("glowstick")
	var gh: Dictionary = rig.get("glow_hand", {})
	if gs.is_empty() or gs["tex"] == null or gh.is_empty():
		return
	var j := str(gh.get("joint", "elbow_r"))
	var at: Array = gh.get("at", [0, 0])
	var fore_scale := 1.0
	for part in _parts:
		if part["joint"] == j:
			fore_scale = part["scale"]
			var xf: Transform2D = (xfs[j] as Transform2D) * Transform2D(0.0, Vector2(float(at[0]) - part["pivot"].x, float(at[1]) - part["pivot"].y) * fore_scale)
			draw_set_transform_matrix(xf * Transform2D(0.25 + 0.3 * sin(float(cur["sway_x"]) * 0.2), Vector2.ZERO) * Transform2D().scaled(Vector2(gs["scale"], gs["scale"])))
			draw_texture(gs["tex"], -gs["pivot"], glow_color)
			return
