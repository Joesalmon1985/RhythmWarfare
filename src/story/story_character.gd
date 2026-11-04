class_name StoryCharacter
extends Node2D
## One crowd dancer: a rig of textured parts (from the art manifest) drawn in one _draw call by forward kinematics, so draw order
## between dancers is just the stage's y-sort and a part's order is its manifest z. Poses are sampled analytically from the song
## position in beats (never accumulated frame time) and eased toward by song-time deltas, so pausing freezes everything and a replay
## is identical. States: idle, dance, cheer, sad, clap, hands_up, walk, footwork, look.

## Activities (docs/STORY_25D_ART_DIRECTION.md 2.C): what a person does when they are not dancing, appropriate to the place and the mood. "stand" is idle; "dance"
## is the existing dance set (the crowd maps it to dance / cheer by energy). `pace` and `serve` also move the person (the crowd walks them to and fro).
const ACTIVITIES := ["stand", "dance", "drink", "toast", "chat", "point", "phone", "lean_wall", "sit", "lie", "sleep", "paint", "pace", "carry", "serve", "check", "stare", "rock",
	"hug", "queue", "wave", "watch", "mix"]
## The activities that need a partner (they stand facing them) and the ones that face a target (a waypoint, a person or the stage).
const PAIRED := ["chat", "hug", "toast"]
const TARGETED := ["watch", "stare", "point"]
const PROPS := ["", "cup", "bottle", "tray", "phone", "clipboard", "tickets", "brush", "sketchbook", "drip", "headphones", "headphones_wrong", "mug"]
const STATES := ["idle", "dance", "cheer", "sad", "clap", "hands_up", "walk", "footwork", "look", "solo", "drink", "toast", "chat", "point", "phone", "lean_wall", "sit", "lie", "sleep",
	"paint", "pace", "carry", "serve", "check", "stare", "rock", "hug", "queue", "wave", "watch", "mix", "stand"]
const FACE_OF := {"idle": "neutral", "dance": "happy", "cheer": "cheer", "sad": "sad", "clap": "happy", "hands_up": "cheer", "walk": "neutral",
	"footwork": "happy", "look": "neutral", "solo": "cheer", "toast": "happy", "chat": "happy", "hug": "happy", "wave": "happy", "mix": "happy", "drink": "neutral",
	"sleep": "neutral", "rock": "sad", "stare": "neutral"}
const BLEND_S := 0.32  # seconds of song time a state change cross-fades
const STYLES := 5  # personal dance styles: arm pump, fist pump, shimmy, raised V, head-nod groove
const POSE_KEYS := ["bob", "jump", "lean", "head_tilt", "head_drop", "arm_l", "arm_r", "elb_l", "elb_r", "leg_l", "leg_r", "sway_x", "squash", "spin", "roll"]

var rig: Dictionary = {}  # the variant's manifest entry: {joints, parts, faces, glow_hand?, height}
var assets: StoryAssets
var actor_id := ""
var state := "idle"
var amp := 1.0  # personal energy scale 0.6..1.2
var rate := 0.5  # dance cycles per beat
var phase := 0.0  # personal offset in cycles (synchronised moves use 0)
var sync := false  # true: phase offset 0 (deliberate group moves)
var style := 0  # personal dance style 0..STYLES-1
var walk_dir := 0.0  # -1 walking left, 1 right, 0 standing (set by the crowd)
var glow := false  # carries a glow stick
var glow_color := Color(0.4, 1.0, 1.0)
var held := ""  # a prop in the right hand (PROPS), drawn at the hand by _draw_held
var toward := 0.0  # -1 .. 1: the screen side of the partner or target (the figure faces and turns its head that way), 0 none
var chat_role := 0  # in a pair: 0 talks first, 1 listens first
var reduced := false
var cur: Dictionary = {}
var _last_t := -1.0
var _swing := 0.0
var _swing_v := 0.0
var _joints: Dictionary = {}
var _parts: Array = []


func setup(p_assets: StoryAssets, rig_entry: Dictionary, id: String, p_seed: int) -> void:
	assets = rig_entry.get("_assets", p_assets)  # a borrowed archetype keeps its own set's textures
	rig = rig_entry
	actor_id = id
	var rng := RandomNumberGenerator.new()
	rng.seed = p_seed
	amp = rng.randf_range(0.8, 1.15)
	rate = 0.5 if rng.randf() < 0.75 else 1.0
	phase = rng.randf()
	style = rng.randi() % STYLES
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
		if e["swing"]:
			var sp: Array = p.get("swing_pivot", p.get("pivot", [0, 0]))
			e["swing_pivot"] = Vector2(float(sp[0]), float(sp[1]))
		e["name"] = str(p.get("name", ""))
		_parts.append(e)
	_parts.append({"face": true, "z": int(rig.get("face_z", 12)), "joint": "head"})
	_parts.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["z"] < b["z"])
	_face_entries = {}
	for k in rig.get("faces", {}):
		_face_entries[k] = assets._entry(rig["faces"][k])
	z_as_relative = true


var _face_entries: Dictionary = {}


## Target pose for a state at song position `beats` (a pure function: the same inputs give the same pose). Every dancer bounces on
## the beat (down on the kick, up between beats); the arm pattern, sway and accents follow the dancer's own style and phase, so the
## floor never moves in lockstep. A synchronised move (sync) drops the personal phase, rate, amplitude and style, so a group jump or
## clap is genuinely simultaneous. `out` may be passed to fill an existing dictionary (no allocation per frame).
func sample(st: String, beats: float, energy01: float, out: Dictionary = {}) -> Dictionary:
	var r := 0.5 if sync else rate
	var ph := (0.0 if sync else phase) + beats * r
	var w := TAU * ph
	var a := (1.0 if sync else amp) * (0.55 + 0.7 * energy01)
	var bf := fposmod(beats, 1.0)  # position inside the beat: 0 on the beat
	var kick := exp(-10.0 * bf)  # 1 on the beat, gone by the next eighth
	var rise := sin(PI * bf)  # 0 on the beat, 1 half way
	var sty := 0 if sync else style
	var p := out
	for k in POSE_KEYS:
		p[k] = 0.0
	match st:
		"idle":  # weight shifts, a small nod on the bar, arms loose
			p["bob"] = 1.0 * rise
			p["lean"] = 0.035 * sin(w * 0.5)
			p["sway_x"] = 2.5 * sin(w * 0.5)
			p["arm_l"] = 0.14 + 0.04 * sin(w)
			p["arm_r"] = 0.14 - 0.04 * sin(w)
			p["elb_l"] = 0.18 + 0.05 * sin(w * 0.5)
			p["elb_r"] = 0.22 - 0.05 * sin(w * 0.5)
			p["head_tilt"] = 0.05 * sin(w * 0.5 + 0.6)
			p["head_drop"] = 1.6 * exp(-32.0 * fposmod(beats * 0.25, 1.0))
			p["squash"] = 0.01 * kick
		"dance":
			p["bob"] = 5.0 * a * rise
			p["squash"] = 0.045 * a * kick
			p["head_drop"] = 2.6 * a * kick
			p["head_tilt"] = 0.1 * sin(w)
			p["leg_l"] = 0.08 + 0.07 * a * sin(w * 2.0)
			p["leg_r"] = 0.08 - 0.07 * a * sin(w * 2.0)
			match sty:
				1:  # fist pump: one arm punches up on every beat, the other hand on the hip
					p["arm_r"] = 1.25 + 0.55 * a * (1.0 - bf) * (1.0 - bf)
					p["elb_r"] = 0.35 + 0.9 * bf
					p["arm_l"] = 0.55 + 0.3 * a * sin(w * 2.0)
					p["elb_l"] = 1.85
					p["lean"] = -0.05 + 0.04 * sin(w)
					p["sway_x"] = 3.0 * a * sin(w)
				2:  # shimmy: side steps with bent arms swinging across
					var sw := sin(w)
					p["sway_x"] = 11.0 * a * sw
					p["lean"] = 0.11 * a * sw
					p["arm_l"] = 0.55 + 0.35 * a * sin(w * 2.0)
					p["arm_r"] = 0.55 - 0.35 * a * sin(w * 2.0)
					p["elb_l"] = 1.45
					p["elb_r"] = 1.45
					p["leg_l"] = 0.06 + 0.2 * a * maxf(0.0, sw)
					p["leg_r"] = 0.06 + 0.2 * a * maxf(0.0, -sw)
				3:  # arms raised in a V, swaying over the head
					p["arm_l"] = 1.55 + 0.3 * a * sin(w)
					p["arm_r"] = 1.55 - 0.3 * a * sin(w)
					p["elb_l"] = 0.35 + 0.25 * sin(w * 2.0)
					p["elb_r"] = 0.35 - 0.25 * sin(w * 2.0)
					p["sway_x"] = 7.0 * a * sin(w)
					p["lean"] = 0.07 * sin(w)
				4:  # head-nodding groove: forearms low and pumping, a big nod on the kick
					p["arm_l"] = 0.45 + 0.3 * a * sin(w * 2.0)
					p["arm_r"] = 0.45 + 0.3 * a * sin(w * 2.0 + PI)
					p["elb_l"] = 1.1 + 0.3 * kick
					p["elb_r"] = 1.1 + 0.3 * kick
					p["head_drop"] = 4.5 * a * kick
					p["head_tilt"] = 0.06 * sin(w)
					p["lean"] = 0.05 * sin(w) + 0.03 * kick
					p["sway_x"] = 4.0 * a * sin(w)
				_:  # arm pump: forearms pumping alternately
					p["arm_l"] = 0.8 + 0.5 * a * sin(w * 2.0)
					p["arm_r"] = 0.8 + 0.5 * a * sin(w * 2.0 + PI)
					p["elb_l"] = 0.75 + 0.45 * a * sin(w * 2.0 + 1.0)
					p["elb_r"] = 0.75 + 0.45 * a * sin(w * 2.0 + 1.0 + PI)
					p["lean"] = 0.09 * a * sin(w)
					p["sway_x"] = 6.0 * a * sin(w)
		"cheer":  # jumps every second beat: crouch, spring, hang, land (synchronised jumps share the same beat)
			var cf := fposmod(beats * 0.5 + (0.0 if sync else 0.5 * float(style % 2)), 1.0)
			var air := clampf((cf - 0.12) / 0.62, 0.0, 1.0)
			var hop := sin(PI * air) if cf >= 0.12 and cf <= 0.74 else 0.0
			p["jump"] = 22.0 * a * pow(hop, 0.8)
			var sq := 0.0
			if cf < 0.12:
				sq = 0.07 * a * (1.0 - cf / 0.12) * 0.6 + 0.07 * a * 0.4
			elif cf > 0.74:
				sq = 0.07 * a * sin(PI * 0.5 * clampf((cf - 0.74) / 0.12, 0.0, 1.0))
			p["squash"] = sq - 0.035 * a * hop  # crouch before, land into it, stretch in the air
			p["arm_l"] = 2.45 + 0.2 * hop + 0.12 * sin(w * 4.0)
			p["arm_r"] = 2.45 + 0.2 * hop + 0.12 * sin(w * 4.0 + 1.5)
			p["elb_l"] = 0.12 + 0.35 * (1.0 - hop)
			p["elb_r"] = 0.12 + 0.35 * (1.0 - hop)
			p["leg_l"] = 0.14 * hop
			p["leg_r"] = 0.14 * hop
			p["head_tilt"] = -0.08 + 0.05 * sin(w)
			p["lean"] = 0.03 * sin(w)
		"hands_up":
			p["bob"] = 3.0 * a * rise
			p["squash"] = 0.03 * a * kick
			var hs := sin(TAU * beats / 8.0 + (0.0 if sync else phase * TAU))  # a slow sway over two bars
			p["arm_l"] = 2.75 + 0.14 * hs
			p["arm_r"] = 2.75 - 0.14 * hs
			p["elb_l"] = 0.06 + 0.06 * rise
			p["elb_r"] = 0.06 + 0.06 * rise
			p["sway_x"] = 9.0 * hs
			p["lean"] = 0.07 * hs
			p["head_tilt"] = -0.1 + 0.04 * hs
		"sad":  # slumped, head down, arms hanging, a slow listless sway
			p["head_drop"] = 7.0
			p["head_tilt"] = 0.15 + 0.04 * sin(w * 0.25)
			p["lean"] = 0.06 + 0.02 * sin(w * 0.25)
			p["arm_l"] = 0.03
			p["arm_r"] = 0.03
			p["elb_l"] = 0.2
			p["elb_r"] = 0.25
			p["sway_x"] = 1.5 * sin(w * 0.25)
			p["squash"] = 0.025
		"clap":  # hands meet on beats two and four, a bounce on every beat
			var cf2 := fposmod((beats - 1.0) * 0.5, 1.0)
			var tog := pow(0.5 + 0.5 * cos(TAU * cf2), 3.0)
			p["bob"] = 3.0 * a * rise
			p["squash"] = 0.03 * a * kick
			p["arm_l"] = 0.62 - 0.22 * tog
			p["arm_r"] = 0.62 - 0.22 * tog
			p["elb_l"] = 1.15 + 0.45 * tog
			p["elb_r"] = 1.15 + 0.45 * tog
			p["head_tilt"] = 0.06 * sin(w)
			p["head_drop"] = 1.5 * tog
			p["lean"] = 0.04 * sin(w)
		"walk":  # a step on every beat, arms swinging against the legs, leaning into the walk
			var sw2 := sin(PI * beats)
			p["bob"] = 3.5 * absf(sw2)
			p["leg_l"] = 0.38 * sw2
			p["leg_r"] = -0.38 * sw2
			p["arm_l"] = 0.18 - 0.32 * sw2
			p["arm_r"] = 0.18 + 0.32 * sw2
			p["elb_l"] = 0.35
			p["elb_r"] = 0.35
			p["head_tilt"] = 0.03 * sw2
			p["lean"] = 0.07 * walk_dir
			p["spin"] = 0.45 * absf(walk_dir)  # a three-quarter turn into the walk
		"footwork":  # quick drum and bass footwork: legs kick out on the beat, arms pumping, the body twisting
			var f := sin(PI * beats)
			p["bob"] = 7.0 * a * rise
			p["squash"] = 0.05 * a * kick
			p["leg_l"] = 0.42 * a * f
			p["leg_r"] = -0.42 * a * f
			p["arm_l"] = 0.55 + 0.4 * f
			p["arm_r"] = 0.55 - 0.4 * f
			p["elb_l"] = 1.3
			p["elb_r"] = 1.3
			p["lean"] = 0.12 * f
			p["sway_x"] = 8.0 * f
			p["head_tilt"] = 0.1 * f
			p["spin"] = 0.25 * f
		"look":  # arms crossed, glancing around: holds one side, then turns the head to the other
			var g := sin(TAU * (beats / 8.0) + phase * TAU)
			var glance := clampf(g * 2.5, -1.0, 1.0)
			p["bob"] = 0.8 * rise
			p["head_tilt"] = 0.16 * glance
			p["arm_l"] = 0.22
			p["arm_r"] = 0.26
			p["elb_l"] = 1.95
			p["elb_r"] = 1.85
			p["lean"] = 0.03 * glance
			p["sway_x"] = 2.0 * glance
		"stand":
			sample("idle", beats, energy01, p)
		"drink":  # a cup to the mouth every eight beats, head back
			var dq := fposmod(beats / 8.0 + phase, 1.0)
			var sip := _smooth01((dq - 0.5) / 0.1) * (1.0 - _smooth01((dq - 0.78) / 0.1))
			p["bob"] = 0.8 * rise
			p["lean"] = 0.03 * sin(w * 0.5) - 0.02 * sip
			p["sway_x"] = 2.0 * sin(w * 0.5)
			p["arm_l"] = 0.16
			p["elb_l"] = 0.2
			p["arm_r"] = lerpf(0.4, 1.0, sip)
			p["elb_r"] = lerpf(0.9, 2.15, sip)
			p["head_tilt"] = -0.14 * sip + 0.04 * sin(w * 0.5)
		"toast":  # the cup held up, a clink on every fourth beat
			var ck := exp(-8.0 * fposmod(beats * 0.25, 1.0))
			p["bob"] = 2.0 * rise
			p["squash"] = 0.02 * kick
			p["arm_r"] = 1.35 + 0.18 * ck
			p["elb_r"] = 0.7 - 0.3 * ck
			p["arm_l"] = 0.16
			p["elb_l"] = 0.25
			p["head_tilt"] = -0.06 + 0.04 * sin(w)
			p["lean"] = 0.05 * toward
		"chat":  # one talks with open hands and nods, the other listens, then they swap
			var tk := fposmod(beats / 16.0 + 0.5 * float(chat_role), 1.0) < 0.5
			p["bob"] = 0.8 * rise
			p["lean"] = 0.05 * toward + 0.02 * sin(w * 0.5)
			p["sway_x"] = 1.5 * sin(w * 0.5)
			if tk:
				p["arm_r"] = 0.55 + 0.3 * sin(w * 1.3)
				p["elb_r"] = 1.2 + 0.3 * sin(w * 1.3 + 1.0)
				p["arm_l"] = 0.3 + 0.1 * sin(w * 0.9)
				p["elb_l"] = 0.9
				p["head_tilt"] = 0.08 * sin(w * 1.3)
			else:
				p["arm_l"] = 0.16
				p["arm_r"] = 0.16
				p["elb_l"] = 0.25
				p["elb_r"] = 0.3
				p["head_tilt"] = 0.04 + 0.08 * maxf(0.0, sin(w * 0.75))  # nods
				p["head_drop"] = 2.5 * maxf(0.0, sin(w * 0.75))
		"point":  # an arm out towards the target, a small jab on the beat
			p["bob"] = 1.2 * rise
			p["arm_r"] = 1.5 + 0.1 * kick
			p["elb_r"] = 0.08
			p["arm_l"] = 0.2
			p["elb_l"] = 0.3
			p["lean"] = 0.04 * toward
			p["head_tilt"] = 0.06 * toward
		"phone":  # head down, a lit phone in the hand at the face
			p["bob"] = 0.4 * rise
			p["head_drop"] = 4.0
			p["arm_r"] = 1.0
			p["elb_r"] = 2.2 + 0.05 * sin(w)
			p["arm_l"] = 0.16
			p["elb_l"] = 0.2
			p["lean"] = 0.05
			p["head_tilt"] = 0.1
			p["sway_x"] = 1.0 * sin(w * 0.25)
		"lean_wall":  # weight on the wall, arms folded, a foot crossed, a nod now and then
			p["lean"] = 0.2 * (toward if toward != 0.0 else 1.0)
			p["sway_x"] = 7.0 * (toward if toward != 0.0 else 1.0)
			p["arm_l"] = 0.22
			p["arm_r"] = 0.26
			p["elb_l"] = 1.95
			p["elb_r"] = 1.85
			p["leg_l"] = 0.12
			p["head_tilt"] = 0.06 * sin(w * 0.25)
			p["bob"] = 0.6 * rise
		"sit":  # sunk onto a seat, hands in the lap, a slow shift
			p["squash"] = 0.3
			p["bob"] = -3.0
			p["arm_l"] = 0.3
			p["arm_r"] = 0.3
			p["elb_l"] = 0.9
			p["elb_r"] = 0.9
			p["leg_l"] = 0.7
			p["leg_r"] = 0.7
			p["head_tilt"] = 0.05 * sin(w * 0.25)
			p["sway_x"] = 1.5 * sin(w * 0.25)
		"lie":  # flat on a bed
			p["roll"] = -1.5 * (toward if toward != 0.0 else 1.0)
			p["bob"] = 0.0
			p["arm_l"] = 0.3
			p["arm_r"] = 0.3
			p["elb_l"] = 0.3
			p["elb_r"] = 0.3
			p["squash"] = 0.012 * sin(w * 0.5)  # breathing
		"sleep":  # slumped in a chair, head on the chest, a slow breath
			var br := sin(PI * beats / 4.0)
			p["squash"] = 0.3 + 0.008 * br
			p["bob"] = -3.0
			p["head_drop"] = 9.0
			p["head_tilt"] = 0.32
			p["lean"] = 0.08
			p["arm_l"] = 0.3
			p["arm_r"] = 0.3
			p["elb_l"] = 1.0
			p["elb_r"] = 1.0
			p["leg_l"] = 0.7
			p["leg_r"] = 0.7
		"paint":  # brush strokes at an easel
			var bs := sin(w * 1.5)
			p["bob"] = 0.6 * rise
			p["arm_r"] = 0.95 + 0.22 * bs
			p["elb_r"] = 1.2 + 0.4 * sin(w * 1.5 + 1.0)
			p["arm_l"] = 0.5
			p["elb_l"] = 1.4
			p["lean"] = 0.07 + 0.03 * bs
			p["head_tilt"] = 0.05 * bs
			p["sway_x"] = 2.0 * bs
		"pace", "serve":  # a walk (the crowd moves the person to and fro); serve carries a tray
			sample("walk", beats, energy01, p)
			if st == "serve":
				p["arm_l"] = 0.7
				p["arm_r"] = 0.7
				p["elb_l"] = 1.55
				p["elb_r"] = 1.55
			else:
				p["arm_l"] = 0.3
				p["arm_r"] = 0.35
				p["elb_l"] = 1.7
				p["elb_r"] = 1.6  # hands behind the back or clasped, a worried walk
		"carry":  # standing with a tray or a stand held in front
			p["bob"] = 0.8 * rise
			p["arm_l"] = 0.7
			p["arm_r"] = 0.7
			p["elb_l"] = 1.55
			p["elb_r"] = 1.55
			p["sway_x"] = 1.5 * sin(w * 0.5)
			p["lean"] = 0.02 * sin(w * 0.5)
		"check":  # a clipboard or a monitor: look down, look up, tick
			var ch := fposmod(beats / 6.0 + phase, 1.0)
			var dn := _smooth01((ch - 0.2) / 0.1) * (1.0 - _smooth01((ch - 0.6) / 0.1))
			p["bob"] = 0.6 * rise
			p["arm_r"] = 0.75
			p["elb_r"] = 1.85
			p["arm_l"] = 0.3
			p["elb_l"] = 1.6
			p["head_drop"] = 4.5 * dn
			p["head_tilt"] = 0.1 * toward - 0.04 * (1.0 - dn)
			p["lean"] = 0.03 + 0.03 * dn
		"stare":  # standing very still, looking at one thing; a very slow sway
			p["bob"] = 0.3 * rise
			p["arm_l"] = 0.08
			p["arm_r"] = 0.08
			p["elb_l"] = 0.15
			p["elb_r"] = 0.15
			p["head_tilt"] = 0.14 * toward
			p["lean"] = 0.03 * toward + 0.01 * sin(w * 0.25)
			p["sway_x"] = 0.8 * sin(w * 0.125)
		"rock":  # hugging the knees, rocking back and forth
			p["squash"] = 0.34
			p["bob"] = -3.0
			p["arm_l"] = 0.55
			p["arm_r"] = 0.55
			p["elb_l"] = 2.1
			p["elb_r"] = 2.1
			p["lean"] = 0.13 * sin(w * 0.5)
			p["sway_x"] = 3.0 * sin(w * 0.5)
			p["head_drop"] = 4.0
			p["leg_l"] = 0.5
			p["leg_r"] = 0.5
		"hug":  # a pair holding each other, swaying
			p["bob"] = 0.8 * rise
			p["arm_l"] = 0.95
			p["arm_r"] = 0.95
			p["elb_l"] = 1.5
			p["elb_r"] = 1.5
			p["lean"] = 0.1 * toward + 0.03 * sin(w * 0.5)
			p["sway_x"] = 4.0 * toward + 2.0 * sin(w * 0.5)
			p["head_tilt"] = 0.15 * toward
		"queue":  # standing in line facing front, a shuffle forward every eight beats, a glance at the watch
			var qs := fposmod(beats / 8.0 + phase, 1.0)
			var step := _smooth01((qs - 0.9) / 0.1)
			p["bob"] = 0.6 * rise + 1.5 * sin(PI * step)
			p["sway_x"] = 2.0 * sin(w * 0.25) + 2.5 * step
			p["arm_l"] = 0.14
			p["arm_r"] = 0.9 if fposmod(beats / 16.0 + phase, 1.0) > 0.85 else 0.14
			p["elb_l"] = 0.2
			p["elb_r"] = 1.9 if fposmod(beats / 16.0 + phase, 1.0) > 0.85 else 0.25
			p["head_tilt"] = 0.04 * sin(w * 0.25)
			p["head_drop"] = 1.5 * exp(-8.0 * fposmod(beats * 0.125, 1.0))
		"wave":  # a hand up, waving
			p["bob"] = 1.5 * rise
			p["arm_r"] = 2.5 + 0.1 * sin(w * 2.0)
			p["elb_r"] = 0.45 + 0.55 * sin(w * 4.0)
			p["arm_l"] = 0.16
			p["elb_l"] = 0.2
			p["head_tilt"] = -0.06
			p["lean"] = 0.03 * sin(w)
		"watch":  # arms folded, head turned to what they are watching
			p["bob"] = 0.8 * rise
			p["arm_l"] = 0.22
			p["arm_r"] = 0.26
			p["elb_l"] = 1.95
			p["elb_r"] = 1.85
			p["head_tilt"] = 0.18 * toward + 0.03 * sin(w * 0.5)
			p["lean"] = 0.04 * toward
			p["head_drop"] = 1.6 * kick
		"mix":  # hands on the mixer, headphones on, nodding to the beat
			p["bob"] = 2.5 * a * rise
			p["squash"] = 0.03 * a * kick
			p["head_drop"] = 3.5 * a * kick
			p["head_tilt"] = 0.08 * sin(w * 0.5)
			p["arm_l"] = 0.6 + 0.1 * sin(w * 2.0)
			p["arm_r"] = 0.6 - 0.1 * sin(w * 2.0)
			p["elb_l"] = 1.15
			p["elb_r"] = 1.15
			p["lean"] = 0.06 + 0.02 * sin(w)
		"solo":  # the hero's moment: every move in turn, a jump bar, and a spin on every fourth bar
			var bar := int(floorf(beats / 4.0))
			var keep := style
			style = bar % STYLES
			sample("dance" if bar % 4 != 2 else "cheer", beats, maxf(energy01, 0.85), p)
			style = keep
			var sp := fposmod(beats, 16.0)
			if sp >= 12.0 and sp < 13.0:
				var u := sp - 12.0
				p["spin"] = TAU * u * u * (3.0 - 2.0 * u)
	return p


static func _smooth01(x: float) -> float:
	x = clampf(x, 0.0, 1.0)
	return x * x * (3.0 - 2.0 * x)


## Show the state's pose at song time `t`. A state change cross-fades from the pose on screen to the new state's live pose over
## BLEND_S seconds of song time; otherwise the pose IS the sampled target, so it never lags behind the beat. Pausing freezes it.
func update_pose(t: float, bpm: float, energy01: float) -> void:
	if t < _last_t:  # the song went back (a restart): no blend from the old pose
		_first = true
	var dt := 0.0 if _last_t < 0.0 or _first else clampf(t - _last_t, 0.0, 0.25)
	_last_t = t
	var beats := t * bpm / 60.0
	if state != _shown_state:
		if not _first:
			for key in POSE_KEYS:
				_from[key] = cur[key]
			_blend_t0 = t
			_blend_len = BLEND_S * (0.6 if state == "cheer" or _shown_state == "walk" else 1.0)
		_shown_state = state
	sample(state, beats, energy01, _target)
	var u := 1.0 if _first or _blend_t0 < 0.0 else clampf((t - _blend_t0) / _blend_len, 0.0, 1.0)
	var k := u * u * (3.0 - 2.0 * u)
	_first = false
	for key in POSE_KEYS:
		cur[key] = lerpf(float(_from.get(key, 0.0)), float(_target[key]), k) if k < 1.0 else float(_target[key])
	if k >= 1.0:
		_blend_t0 = -1.0
	_swing_v += ((-_swing * 40.0) - _swing_v * 5.0 - float(cur["sway_x"]) * 0.18 - float(cur["jump"]) * 0.02) * dt
	_swing = clampf(_swing + _swing_v * dt, -0.6, 0.6)
	queue_redraw()


var _first := true
var _shown_state := ""
var _from: Dictionary = {}
var _target: Dictionary = {}
var _blend_t0 := -1.0
var _blend_len := 0.3


func face_name() -> String:
	return str(FACE_OF.get(state, "neutral"))


const JOINT_ORDER := ["hips", "torso", "head", "shoulder_l", "elbow_l", "hip_l", "shoulder_r", "elbow_r", "hip_r"]
const J_HIPS := 0
const J_TORSO := 1
const J_HEAD := 2
const J_SH_L := 3
const J_EL_L := 4
const J_HP_L := 5
const J_SH_R := 6
const J_EL_R := 7
const J_HP_R := 8
var _xfs: Array = []  # reused every frame: the transform of each joint, by JOINT_ORDER index
var _joint_idx: Dictionary = {}  # part -> index into _xfs (resolved once)


func _draw() -> void:
	if rig.is_empty() or _parts.is_empty():
		return
	if _xfs.is_empty():
		_xfs.resize(JOINT_ORDER.size())
		for part in _parts:
			part["ji"] = maxi(JOINT_ORDER.find(str(part["joint"])), 0)  # an unknown joint rides on the hips, as before
	var P: Dictionary = cur
	var j_hips: Vector2 = _joints.get("hips", Vector2(0, -110))
	var j_torso: Vector2 = _joints.get("torso", j_hips)
	var j_head: Vector2 = _joints.get("head", Vector2(0, -200))
	var sq := float(P["squash"])
	var turn := cos(float(P["spin"]))  # a spin (or a three-quarter turn) narrows the figure; past 90 degrees it shows mirrored
	if absf(turn) < 0.12:
		turn = 0.12 * (1.0 if turn >= 0.0 else -1.0)
	var flip := -1.0 if toward < -0.01 else 1.0  # facing the partner or target on the left of the screen: the figure is mirrored
	var root := Transform2D(float(P["roll"]), Vector2(float(P["sway_x"]) * flip, -float(P["jump"]))) * Transform2D(0.0, Vector2((1.0 + sq * 0.6) * turn * flip, 1.0 - sq), 0.0, Vector2.ZERO)
	var hip_xf := root * Transform2D(0.0, j_hips + Vector2(0, -float(P["bob"]) * 0.5))
	var torso_xf := hip_xf * Transform2D(float(P["lean"]), j_torso - j_hips)
	var head_drop := float(P["head_drop"])
	var head_xf := torso_xf * Transform2D(float(P["head_tilt"]), j_head - j_torso + Vector2(0, head_drop))
	_xfs[J_HIPS] = hip_xf
	_xfs[J_TORSO] = torso_xf
	_xfs[J_HEAD] = head_xf
	for side in 2:
		var sg := 1.0 if side == 0 else -1.0
		var sfx := "_l" if side == 0 else "_r"
		var j_sh: Vector2 = _joints.get("shoulder" + sfx, Vector2(sg * 30, -186))
		var j_el: Vector2 = _joints.get("elbow" + sfx, Vector2(sg * 35, -144))
		var sh_xf: Transform2D = torso_xf * Transform2D(sg * float(P["arm" + sfx]), j_sh - j_torso + Vector2(0, head_drop * 0.5))
		_xfs[J_SH_L + side * 3] = sh_xf
		_xfs[J_EL_L + side * 3] = sh_xf * Transform2D(-sg * float(P["elb" + sfx]), j_el - j_sh)
		var j_hp: Vector2 = _joints.get("hip" + sfx, Vector2(sg * 11, -108))
		_xfs[J_HP_L + side * 3] = hip_xf * Transform2D(sg * float(P["leg" + sfx]), j_hp - j_hips)
	for part in _parts:
		if part.get("face", false):
			_draw_face(head_xf)
			continue
		var xf: Transform2D = _xfs[int(part["ji"])]
		var sc: float = part["scale"]
		var tex: Texture2D = part["tex"]
		if tex == null:
			continue
		if part["swing"]:
			var off: Vector2 = ((part["swing_pivot"] as Vector2) - (part["pivot"] as Vector2)) * sc
			xf = xf * Transform2D(0.0, off) * Transform2D(_swing, Vector2.ZERO) * Transform2D(0.0, -off)
		draw_set_transform_matrix(xf * Transform2D().scaled(Vector2(sc, sc)))
		draw_texture(tex, -part["pivot"], Color.WHITE)
	if glow:
		_draw_glow(_xfs_dict())
	if held != "" or state in ["sit", "sleep", "phone"]:
		_draw_held(head_xf, hip_xf)
	draw_set_transform_matrix(Transform2D.IDENTITY)


func _xfs_dict() -> Dictionary:  # the glow stick looks a joint up by name
	var d := {}
	for i in JOINT_ORDER.size():
		d[JOINT_ORDER[i]] = _xfs[i]
	return d


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
	for part in _parts:
		if part.get("joint", "") == j and not part.get("face", false) and part["name"].ends_with("fore"):
			var hand := Vector2(float(at[0]), float(at[1])) - (part["pivot"] as Vector2)
			var xf: Transform2D = (xfs[j] as Transform2D) * Transform2D(0.0, hand * float(part["scale"]))
			draw_set_transform_matrix(xf * Transform2D(0.3, Vector2.ZERO) * Transform2D().scaled(Vector2(gs["scale"], gs["scale"])))
			draw_texture(gs["tex"], -gs["pivot"], glow_color)
			return


## The right hand's transform (the glow stick's hand point on the forearm), or hips when the rig has none.
func _hand_xf(fallback: Transform2D) -> Transform2D:
	var gh: Dictionary = rig.get("glow_hand", {})
	if gh.is_empty():
		return fallback
	var j := str(gh.get("joint", "elbow_r"))
	var at: Array = gh.get("at", [0, 0])
	for part in _parts:
		if part.get("joint", "") == j and not part.get("face", false) and str(part["name"]).ends_with("fore"):
			var hand := Vector2(float(at[0]), float(at[1])) - (part["pivot"] as Vector2)
			return (_xfs[JOINT_ORDER.find(j)] as Transform2D) * Transform2D(0.0, hand * float(part["scale"]))
	return fallback


## Props in the hand and a few things that go with a pose (a seat under a sitter, the phone's light), drawn with plain shapes in the rig's own units (about 300 high):
## the polish pass restyles them, the hand point and the call sites are the contract.
func _draw_held(head_xf: Transform2D, hip_xf: Transform2D) -> void:
	var hx := _hand_xf(hip_xf)
	if state in ["sit", "sleep"]:  # a plain seat under the hips
		draw_set_transform_matrix(hip_xf)
		draw_rect(Rect2(-34, -6, 68, 14), Color(0.32, 0.2, 0.34))
		draw_rect(Rect2(-30, 8, 6, 26), Color(0.2, 0.14, 0.22))
		draw_rect(Rect2(24, 8, 6, 26), Color(0.2, 0.14, 0.22))
	if state == "sleep":  # drifting Zs
		draw_set_transform_matrix(head_xf)
		var zt := fposmod(_last_t * 0.6, 1.0)
		for k in 2:
			var zk := fposmod(zt + 0.5 * float(k), 1.0)
			var zc := Color(0.8, 0.85, 1.0, 1.0 - zk)
			var o := Vector2(30.0 + 18.0 * zk, -70.0 - 50.0 * zk)
			var sz := 8.0 + 6.0 * zk
			draw_polyline(PackedVector2Array([o + Vector2(-sz, -sz), o + Vector2(sz, -sz), o + Vector2(-sz, sz), o + Vector2(sz, sz)]), zc, 3.0)
	if state == "phone" or held == "phone":
		draw_set_transform_matrix(hx)
		draw_rect(Rect2(-5, -18, 10, 17), Color(0.1, 0.1, 0.14))
		draw_rect(Rect2(-4, -17, 8, 14), Color(0.6, 0.95, 1.0))
		draw_set_transform_matrix(head_xf)  # the lit face
		draw_circle(Vector2(8, -52), 40.0, Color(0.55, 0.9, 1.0, 0.16))
		draw_circle(Vector2(8, -52), 24.0, Color(0.55, 0.9, 1.0, 0.14))
		return
	draw_set_transform_matrix(hx)
	match held:
		"cup", "mug":
			draw_rect(Rect2(-6, -20, 12, 18), Color(0.95, 0.9, 0.8) if held == "cup" else Color(0.8, 0.5, 0.35))
			draw_rect(Rect2(-5, -20, 10, 4), Color(0.9, 0.7, 0.3, 0.9))
		"bottle":
			draw_rect(Rect2(-4, -22, 8, 20), Color(0.2, 0.55, 0.3))
			draw_rect(Rect2(-2, -32, 4, 11), Color(0.2, 0.55, 0.3))
		"tray":
			draw_rect(Rect2(-34, -4, 68, 5), Color(0.75, 0.75, 0.8))
			draw_circle(Vector2(-14, -9), 7, Color(0.95, 0.85, 0.6))
			draw_circle(Vector2(8, -9), 7, Color(0.9, 0.55, 0.45))
			draw_rect(Rect2(18, -16, 8, 12), Color(0.85, 0.9, 0.95))
		"clipboard":
			draw_rect(Rect2(-12, -30, 24, 32), Color(0.55, 0.38, 0.22))
			draw_rect(Rect2(-9, -27, 18, 26), Color(0.95, 0.95, 0.9))
		"tickets":
			draw_rect(Rect2(-8, -16, 16, 11), Color(1.0, 0.9, 0.35))
			draw_rect(Rect2(-5, -19, 16, 11), Color(0.95, 0.35, 0.3))
		"brush":
			draw_line(Vector2(0, 2), Vector2(4, -34), Color(0.5, 0.35, 0.2), 3.0)
			draw_circle(Vector2(4, -36), 4.0, Color(0.9, 0.2, 0.4))
		"sketchbook":
			draw_rect(Rect2(-13, -30, 26, 32), Color(0.3, 0.4, 0.6))
			draw_rect(Rect2(-11, -28, 22, 28), Color(0.95, 0.93, 0.85))
		"drip":  # a drip stand held beside the body: pole, hook, bag and a line to the hand
			var base := Vector2(34, 0)
			draw_line(base + Vector2(0, 2), base + Vector2(0, -190), Color(0.78, 0.8, 0.85), 4.0)
			draw_line(base + Vector2(-14, 2), base + Vector2(14, 2), Color(0.78, 0.8, 0.85), 4.0)
			draw_rect(Rect2(base.x - 11, -190, 22, 34), Color(0.75, 0.9, 1.0, 0.9))
			draw_polyline(PackedVector2Array([base + Vector2(0, -156), base + Vector2(-8, -100), Vector2(0, 0)]), Color(0.8, 0.9, 1.0, 0.8), 2.0)
		"headphones", "headphones_wrong":
			draw_set_transform_matrix(head_xf)
			var wrong := held == "headphones_wrong"
			if wrong:  # one cup on the forehead, the band slipped down the back of the head, the other cup hanging at the neck
				draw_circle(Vector2(-8, -150), 14, Color(0.15, 0.15, 0.2))
				draw_circle(Vector2(-8, -150), 8, Color(0.9, 0.3, 0.5))
				draw_arc(Vector2(0, -140), 46.0, deg_to_rad(200), deg_to_rad(340), 12, Color(0.15, 0.15, 0.2), 5.0)
				draw_circle(Vector2(36, -96), 14, Color(0.15, 0.15, 0.2))
			else:
				draw_arc(Vector2(0, -92), 50.0, deg_to_rad(180), deg_to_rad(360), 16, Color(0.15, 0.15, 0.2), 6.0)
				draw_circle(Vector2(-50, -92), 15, Color(0.15, 0.15, 0.2))
				draw_circle(Vector2(50, -92), 15, Color(0.15, 0.15, 0.2))
