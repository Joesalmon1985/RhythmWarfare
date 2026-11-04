extends SceneTree
## The bake source of the figures' sprite sheets: every state's pose over one cycle (StoryCharacter.SHEET_CYCLES), sampled from StoryCharacter.sample() with the canonical
## personal values, written to assets/story/people_poses.json for tools/story/art/people.py. Headless, no renderer:
##   godot --headless --path . -s tools/story/dump_poses.gd
## The dance is written once per personal style (dance_s0 .. dance_s4). Deterministic (fixed formatting, sorted keys).

const OUT := "res://assets/story/people_poses.json"
const LIMB_KEYS := ["arm_l", "arm_r", "elb_l", "elb_r", "leg_l", "leg_r", "lean", "head_tilt", "head_drop", "squash", "roll"]


func _init() -> void:
	var c := StoryCharacter.new()
	c.amp = 1.0
	c.rate = 0.5
	c.phase = 0.0
	c.sync = false
	var energy := 0.45 / 0.7  # the dance amplitude is exactly 1 at this energy
	var states := {}
	var names: Array = StoryCharacter.SHEET_CYCLES.keys()
	names.sort()
	for st in names:
		var cyc: Array = StoryCharacter.SHEET_CYCLES[st]
		var variants := [[str(st), 0]]
		if st == "dance":
			variants = []
			for k in StoryCharacter.STYLES:
				variants.append(["dance_s%d" % k, k])
		for v in variants:
			c.style = int(v[1])
			c.toward = 1.0 if st in ["lean_wall", "hug"] else 0.0
			c.walk_dir = 0.0
			var frames: Array = []
			for i in int(cyc[1]):
				var beats := float(cyc[0]) * float(i) / float(cyc[1])
				var p := c.sample(str(st), beats, energy)
				var row: Array = []
				for k in LIMB_KEYS:
					row.append(snappedf(float(p[k]), 0.0001))
				frames.append(row)
			states[v[0]] = {"beats": float(cyc[0]), "frames": frames}
	var out := {"keys": LIMB_KEYS, "face_of": StoryCharacter.FACE_OF, "kicked": StoryCharacter.SHEET_KICKED, "states": states}
	var f := FileAccess.open(OUT, FileAccess.WRITE)
	f.store_string(JSON.stringify(out, " ", true) + "\n")
	f.close()
	c.free()
	print("people poses: %d states" % states.size())
	quit(0)
