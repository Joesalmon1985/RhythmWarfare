extends Node2D
## Review contact sheet for the Night One art; independent of src/story/. Builds rigs from
## assets/story/night_one/manifest.json exactly the way the contract describes (also a reference for the runtime).
##   RW_PREVIEW = chars (default) | chars_b | heads | joints | stage | stage_low | sil | deck | pieces | interlude
##   RW_CHAPTER = night_one (default) | mothership | underworld
##   godot --path . -s tools/shoot.gd -- res://tools/story/preview_art.tscn /tmp/shots 30:shot:name

var ROOT := "res://assets/story/night_one/"
const FLOOR_Z := 0

var M: Dictionary = {}
var _tcache: Dictionary = {}


func tex(p: String) -> Texture2D:
	if not _tcache.has(p):
		_tcache[p] = load(ROOT + p)
	return _tcache[p]


func _ready() -> void:
	if OS.has_environment("RW_CHAPTER"):
		ROOT = "res://assets/story/%s/" % OS.get_environment("RW_CHAPTER")
	var txt := FileAccess.get_file_as_string(ROOT + "manifest.json")
	M = JSON.parse_string(txt)
	var bg := ColorRect.new()
	bg.color = Color(0.13, 0.12, 0.2)
	bg.size = Vector2(1280, 720)
	bg.z_index = -4000
	add_child(bg)
	var mode := OS.get_environment("RW_PREVIEW") if OS.has_environment("RW_PREVIEW") else "chars"
	match mode:
		"chars", "chars_b":
			_chars("b" if mode == "chars_b" else "a")
		"heads":
			_heads()
		"stage", "stage_low", "set":
			_stage(mode == "stage_low", false, mode == "set")
		"sil":
			_sil()
		"joints":
			_joints()
		"deck":
			_deck()
		"pieces":
			_pieces_sheet()
		"interlude", "interlude_flood":
			_interlude(mode == "interlude_flood")


# ---- the rig --------------------------------------------------------------------------------------------------------------

class Rig:
	extends Node2D
	var J: Dictionary
	var N: Dictionary = {}
	var face: Sprite2D
	var faces: Dictionary = {}
	var swing: Array = []  # [{node, pivot_node}]

	func build(owner_scene: Node, arch: Dictionary, variant: String, zbase: int) -> void:
		J = arch["joints"]
		var V: Dictionary = arch["variants"][variant]
		N["root"] = self
		var hips := _joint("hips", self, null)
		var torso := _joint("torso", hips, "hips")
		_joint("head", torso, "torso")
		_joint("shoulder_l", torso, "torso")
		_joint("shoulder_r", torso, "torso")
		_joint("elbow_l", N["shoulder_l"], "shoulder_l")
		_joint("elbow_r", N["shoulder_r"], "shoulder_r")
		_joint("hip_l", hips, "hips")
		_joint("hip_r", hips, "hips")
		for p in V["parts"]:
			var s := Sprite2D.new()
			s.texture = owner_scene.tex(p["file"])
			s.centered = false
			var pv := Vector2(p["pivot"][0], p["pivot"][1])
			var k: float = p["px_scale"]
			s.scale = Vector2(k, k)
			s.z_index = zbase + int(p["z"])
			s.z_as_relative = false
			if p.get("swing", false):
				var sp := Vector2(p["swing_pivot"][0], p["swing_pivot"][1])
				var holder := Node2D.new()
				N[p["joint"]].add_child(holder)
				holder.position = (sp - pv) * k
				s.position = -sp * k
				holder.add_child(s)
				swing.append(holder)
			else:
				s.position = -pv * k
				N[p["joint"]].add_child(s)
		face = Sprite2D.new()
		face.centered = false
		face.z_as_relative = false
		face.z_index = zbase + int(V["face_z"])
		N["head"].add_child(face)
		for e in V["faces"]:
			faces[e] = V["faces"][e]
			faces[e]["tex"] = owner_scene.tex(V["faces"][e]["file"])
		set_face("neutral")

	func _joint(name: String, parent: Node2D, parent_name) -> Node2D:
		var n := Node2D.new()
		parent.add_child(n)
		var p := Vector2(J[name][0], J[name][1])
		n.position = p - (Vector2(J[parent_name][0], J[parent_name][1]) if parent_name else Vector2.ZERO)
		N[name] = n
		return n

	func set_face(e: String) -> void:
		var f: Dictionary = faces[e]
		face.texture = f["tex"]
		face.scale = Vector2(f["px_scale"], f["px_scale"])
		face.position = -Vector2(f["pivot"][0], f["pivot"][1]) * float(f["px_scale"])

	## Angles in degrees, "outward positive" for arms (left arm clockwise, right arm counter-clockwise).
	func pose(p: Dictionary) -> void:
		N["hips"].position = Vector2(J["hips"][0], J["hips"][1] + float(p.get("bob", 0.0)))
		N["torso"].rotation_degrees = float(p.get("torso", 0.0))
		N["head"].rotation_degrees = float(p.get("head", 0.0))
		N["shoulder_l"].rotation_degrees = float(p.get("sh_l", 5.0))
		N["elbow_l"].rotation_degrees = -float(p.get("el_l", 10.0))
		N["shoulder_r"].rotation_degrees = -float(p.get("sh_r", 5.0))
		N["elbow_r"].rotation_degrees = float(p.get("el_r", 10.0))
		N["hip_l"].rotation_degrees = float(p.get("hip_l", 0.0))
		N["hip_r"].rotation_degrees = float(p.get("hip_r", 0.0))
		var sw := float(p.get("swing", 0.0))
		for h in swing:
			h.rotation_degrees = sw


const POSES := {
	"idle": {"bob": 1.0, "torso": 2.0, "head": -2.0, "sh_l": 8, "el_l": 14, "sh_r": 8, "el_r": 14, "hip_l": 2, "hip_r": -2, "face": "neutral", "swing": 2.0},
	"dance": {"bob": 4.0, "torso": -6.0, "head": 4.0, "sh_l": 52, "el_l": 78, "sh_r": 118, "el_r": 30, "hip_l": 14, "hip_r": -9, "face": "happy", "swing": -9.0},
	"cheer": {"bob": -14.0, "torso": 0.0, "head": -5.0, "sh_l": 160, "el_l": 14, "sh_r": 164, "el_r": 8, "hip_l": 18, "hip_r": -18, "face": "cheer", "swing": 8.0},
	"sad": {"bob": 4.0, "torso": 4.0, "head": 11.0, "sh_l": 2, "el_l": 24, "sh_r": 2, "el_r": 24, "hip_l": 0, "hip_r": 0, "face": "sad", "swing": 0.0},
}


func make_rig(arch: String, variant: String, pose_name: String, zbase: int = 0) -> Rig:
	var r := Rig.new()
	r.build(self, M["archetypes"][arch], variant, zbase)
	var p: Dictionary = POSES[pose_name]
	r.pose(p)
	r.set_face(str(p["face"]))
	return r


func _label(text: String, pos: Vector2, size := 14) -> void:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.add_theme_font_size_override("font_size", size)
	l.z_index = 3000
	l.z_as_relative = false
	add_child(l)


# ---- sheets ----------------------------------------------------------------------------------------------------------------

func _chars(variant: String) -> void:
	var archs: Array = M["archetypes"].keys()
	var rows := ["idle", "dance", "cheer", "sad"]
	for c in archs.size():
		_label(archs[c] + " " + variant, Vector2(30 + c * 205, 4))
		for r in rows.size():
			var rig := make_rig(archs[c], variant, rows[r], 0)
			rig.scale = Vector2(0.52, 0.52)
			rig.position = Vector2(110 + c * 205, 170 + r * 175)
			add_child(rig)
	for r in rows.size():
		_label(rows[r], Vector2(4, 90 + r * 175), 12)


func _heads() -> void:
	var archs: Array = M["archetypes"].keys()
	var exprs := ["neutral", "happy", "cheer", "sad"]
	for c in archs.size():
		for e in exprs.size():
			var arch: Dictionary = M["archetypes"][archs[c]]
			var cell := Control.new()
			cell.position = Vector2(4 + c * 212, 4 + e * 178)
			cell.size = Vector2(206, 172)
			cell.clip_contents = true
			add_child(cell)
			var rig := make_rig(archs[c], "a" if (c + e) % 2 == 0 else "b", "idle", 0)
			rig.set_face(exprs[e])
			rig.pose({"bob": 0.0, "sh_l": 8, "sh_r": 8})
			var cy: float = arch["joints"]["head"][1] - 26.0
			rig.scale = Vector2(1.8, 1.8)
			rig.position = Vector2(103, 90 - cy * 1.8)
			cell.add_child(rig)


func _joints() -> void:
	var archs: Array = M["archetypes"].keys()
	for c in 3:
		var a: String = archs[c * 2]
		var rig := make_rig(a, "a", "dance", 0)
		rig.scale = Vector2(1.45, 1.45)
		rig.position = Vector2(220 + c * 420, 700)
		add_child(rig)
		var rig2 := make_rig(archs[c * 2 + 1], "b", "cheer", 0)
		rig2.scale = Vector2(0.7, 0.7)
		rig2.position = Vector2(330 + c * 420, 700)
		add_child(rig2)


func _sil() -> void:
	var names: Array = M["silhouettes"].keys()
	for i in names.size():
		for st in 2:
			var d: Dictionary = M["silhouettes"][names[i]]
			var f: Dictionary = d["idle" if st == 0 else "up"]
			var s := Sprite2D.new()
			s.texture = tex(f["file"])
			s.centered = false
			s.scale = Vector2.ONE * float(f["px_scale"]) * 2.0
			s.position = Vector2(100 + i * 300 + st * 140, 360) - Vector2(f["pivot"][0], f["pivot"][1]) * s.scale.x
			add_child(s)


func _deck() -> void:
	_stage(false, true)


# ---- the composed stage -----------------------------------------------------------------------------------------------------

func _sprite(id: String, pos: Vector2, add := false, tint := Color.WHITE, scale_mul := 1.0, z := 0) -> Sprite2D:
	var d: Dictionary = M["stage"]["sprites"][id]
	var s := Sprite2D.new()
	s.texture = tex(d["file"])
	s.centered = false
	var k := float(d.get("px_scale", 0.5)) * scale_mul
	s.scale = Vector2(k, k)
	s.position = pos - Vector2(d["pivot"][0], d["pivot"][1]) * k
	s.modulate = tint
	s.z_as_relative = false
	s.z_index = z
	if add:
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		s.material = mat
	add_child(s)
	return s


func _stage(low: bool, deck_only := false, empty := false) -> void:
	if not M.has("stage"):
		_label("no stage in the manifest yet", Vector2(20, 20), 24)
		return
	var st: Dictionary = M["stage"]
	var A: Dictionary = st["anchors"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for L in st["layers"]:
		var s := Sprite2D.new()
		s.texture = tex(L["file"])
		s.centered = false
		s.position = Vector2(L["pos"][0], L["pos"][1])
		var sz: Array = L["size"]
		s.scale = Vector2(sz[0] / s.texture.get_width(), sz[1] / s.texture.get_height())
		s.z_as_relative = false
		s.z_index = {"backdrop": -3000, "riser": -2900, "speaker_l": -2800, "speaker_r": -2800, "desk_top": 2000}.get(L["id"], -2500)
		if L["id"] == "desk_top":
			s.position.y = 460
			s.scale = Vector2(1280.0 / s.texture.get_width(), 260.0 / s.texture.get_height())
		add_child(s)
	_pieces("behind")
	# LED screen: a simple equaliser painted into the panel
	var led: Array = A["led_screen"]
	var panel := ColorRect.new()
	panel.position = Vector2(led[0] + 4, led[1] + 4)
	panel.size = Vector2(led[2] - 8, led[3] - 8)
	panel.color = Color(0.06, 0.04, 0.16)
	panel.z_as_relative = false
	panel.z_index = -2990
	add_child(panel)
	for i in 28:
		var h: float = (0.25 + 0.7 * absf(sin(i * 0.7 + 0.4))) * (led[3] - 18)
		var bar := ColorRect.new()
		bar.size = Vector2((led[2] - 16) / 28.0 - 3, h)
		bar.position = Vector2(led[0] + 8 + i * (led[2] - 16) / 28.0, led[1] + led[3] - 8 - h)
		bar.color = Color(1.0, 0.2, 0.62) if i % 3 else Color(0.1, 0.82, 1.0)
		bar.z_as_relative = false
		bar.z_index = -2989
		add_child(bar)
	# woofers
	for w in A["woofers"]:
		var r: float = w[2]
		_sprite("woofer", Vector2(w[0], w[1]), false, Color.WHITE, r / float(st["sprites"]["woofer"]["radius"]), -2790)
	# disco ball
	_sprite("disco_ball", Vector2(A["disco_ball"][0], A["disco_ball"][1]), false, Color.WHITE, 1.0, -2700)
	# moving heads with beams
	var tints := [Color(1.0, 0.2, 0.65), Color(0.1, 0.85, 1.0), Color(0.62, 0.35, 1.0), Color(1.0, 0.78, 0.25)]
	if ROOT.contains("hospital"):  # a daylight palette: lamp gold, sun yellow, soft coral and teal
		tints = [Color(1.0, 0.78, 0.4), Color(0.45, 0.85, 0.78), Color(1.0, 0.6, 0.5), Color(1.0, 0.9, 0.6)]
	var lp: Array = A["light_points"]
	for i in lp.size():
		var p := Vector2(lp[i][0], lp[i][1])
		var ang := -26.0 + 52.0 * ((i * 5) % 8) / 7.0
		var fx := _sprite("fixture", p, false, Color.WHITE, 1.0, -2600)
		fx.rotation_degrees = 0.0
		if not low and not empty:
			var b := _sprite("beam", p + Vector2(0, 10), true, tints[i % 4] * Color(1, 1, 1, 0.55), 1.0, -2500)
			b.rotation_degrees = ang * 0.9
			b.position = p + Vector2(0, 10) - Vector2(M["stage"]["sprites"]["beam"]["pivot"][0], M["stage"]["sprites"]["beam"]["pivot"][1]).rotated(deg_to_rad(ang * 0.9)) * 0.5
	# floor pools
	var fp: Array = A["floor_rows"]
	for i in 3:
		_sprite("spot_pool", Vector2(330 + i * 310, fp[2]["y"] + 24), true, tints[i] * Color(1, 1, 1, 0.7), 1.0, -2400)
	# doorway glow
	var dw: Array = A["doorway"]
	if not low and st["sprites"].has("door_open") and st["sprites"]["door_open"].has("pos"):
		var dop: Array = st["sprites"]["door_open"]["pos"]
		_sprite("door_open", Vector2(dop[0], dop[1]), false, Color.WHITE, 1.0, -2850)
	if empty:  # the bare set: no crowd, no haze, no beams
		_pieces("front")
		_deck_pieces()
		return
	# crowd: silhouettes behind, dancers in rows
	var sils: Array = M["silhouettes"].keys()
	var rows: Array = A["floor_rows"]
	for k in 16:
		var d: Dictionary = M["silhouettes"][sils[k % 3]]
		var f: Dictionary = d["up" if k % 3 == 0 else "idle"]
		var s := Sprite2D.new()
		s.texture = tex(f["file"])
		s.centered = false
		var sc: float = float(f["px_scale"]) * (rows[0]["scale"] * 1.0)
		s.scale = Vector2(sc, sc)
		var x := 330.0 + (k % 8) * 86 + (k / 8) * 40 + rng.randf_range(-10, 10)
		var y := float(rows[0]["y"]) - 4 - (k / 8) * 0
		s.position = Vector2(x, y) - Vector2(f["pivot"][0], f["pivot"][1]) * sc
		s.modulate = Color(0.8, 0.8, 1.0)
		s.z_as_relative = false
		s.z_index = 50
		add_child(s)
	var archs: Array = M["archetypes"].keys()
	var poses := ["dance", "idle", "cheer", "dance", "sad", "dance", "cheer", "idle"]
	var n := 0
	for ri in range(1, rows.size()):
		var count := 4 + ri
		for k in count:
			var rowy: float = rows[ri]["y"]
			var sc2: float = rows[ri]["scale"]
			var x := 140.0 + (k + 0.5) * (1000.0 / count) + rng.randf_range(-24, 24) + (140 if ri % 2 == 0 else 100) * 0.0
			var a: String = archs[(n + ri) % archs.size()]
			var rig := make_rig(a, "a" if (n % 2) == 0 else "b", poses[(n * 3) % poses.size()], 100 + ri * 100)
			rig.scale = Vector2(sc2, sc2) * 0.78
			rig.position = Vector2(x, rowy)
			rig.pose(rig_pose_variant(POSES[poses[(n * 3) % poses.size()]], n))
			if n % 3 == 0:
				_glowstick(rig, a, "a" if (n % 2) == 0 else "b", tints[n % 4])
			add_child(rig)
			n += 1
	# haze
	if not low:
		for i in 2:
			_sprite("haze_a" if i == 0 else "haze_b", Vector2(640, 270 + i * 60), false, Color(1, 1, 1, 0.5), 1.0, 1500)
	# vignette
	var vg: Dictionary = st["sprites"]["vignette"]
	var vs := Sprite2D.new()
	vs.texture = tex(vg["file"])
	vs.centered = false
	vs.scale = Vector2(1280.0 / vs.texture.get_width(), 720.0 / vs.texture.get_height())
	vs.z_as_relative = false
	vs.z_index = 3500
	add_child(vs)
	_pieces("front")
	_deck_pieces()


func _glowstick(rig: Rig, arch: String, variant: String, tint: Color) -> void:
	var v: Dictionary = M["archetypes"][arch]["variants"][variant]
	var gh: Dictionary = v["glow_hand"]
	var fore: Dictionary = {}
	for p in v["parts"]:
		if p["name"] == "arm_r_fore":
			fore = p
	var d: Dictionary = M["stage"]["sprites"]["glowstick"]
	var s := Sprite2D.new()
	s.texture = tex(d["file"])
	s.centered = false
	var k := float(d["px_scale"])
	s.scale = Vector2(k, k)
	s.position = -Vector2(d["pivot"][0], d["pivot"][1]) * k
	var holder := Node2D.new()
	holder.position = (Vector2(gh["at"][0], gh["at"][1]) - Vector2(fore["pivot"][0], fore["pivot"][1])) * float(fore["px_scale"])
	holder.rotation_degrees = 180.0 - 25.0
	holder.add_child(s)
	s.modulate = tint
	s.z_as_relative = false
	s.z_index = int(fore["z"]) + 150
	rig.N["elbow_r"].add_child(holder)
	var gl := Sprite2D.new()
	gl.texture = tex(M["stage"]["sprites"]["glow"]["file"])
	gl.position = Vector2(0, -22)
	gl.scale = Vector2(0.22, 0.22)
	gl.modulate = Color(tint, 0.6)
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	gl.material = mat
	holder.add_child(gl)


func rig_pose_variant(p: Dictionary, n: int) -> Dictionary:
	var q := p.duplicate()
	var s := 1.0 if n % 2 == 0 else -1.0
	q["torso"] = float(p["torso"]) * s
	q["hip_l"] = float(p["hip_l"]) * s
	q["hip_r"] = float(p["hip_r"]) * s
	return q


func _deck_pieces() -> void:
	var st: Dictionary = M["stage"]
	if not st["sprites"].has("pad_bezel"):
		return
	var h := 260.0
	var s := minf(h * 0.84, 1280.0 * 0.15)
	var gap := s * 0.12
	var y := 460.0 + (h - s) * 0.55
	var left := gap * 2.0
	var right := 1280.0 - gap * 2.0
	var xs := [left, left + s + gap, right - 2.0 * s - gap, right - s]
	var cols := [Color(1.0, 0.62, 0.25), Color(0.35, 0.85, 0.98), Color(0.72, 0.55, 1.0), Color(0.72, 0.55, 1.0)]
	for i in 4:
		var cx: float = xs[i] + s * 0.5
		var cy := y + s * 0.5
		var plat_pos := Vector2(cx, cy)
		if i % 2 == 0:  # one platter behind each pad pair, centred in the gap
			_sprite("platter", Vector2(xs[i] + s + gap * 0.5, cy), false, Color.WHITE, (s * 1.22) / 240.0, 2010)
		var pad := ColorRect.new()
		pad.position = Vector2(xs[i], y)
		pad.size = Vector2(s, s)
		pad.color = cols[i].darkened(0.6)
		pad.z_as_relative = false
		pad.z_index = 2020
		add_child(pad)
		var inner := float(st["sprites"]["pad_bezel"].get("inner_ratio", 0.8333))
		_sprite("pad_bezel", plat_pos, false, Color.WHITE, (s * 1.0 / inner) / 240.0 * 1.0, 2030)
	# centre mixer parts
	var cxm := 640.0
	_sprite("crossfader", Vector2(cxm, 460 + 205), false, Color.WHITE, 1.0, 2040)
	if st["sprites"].has("fader_slot"):
		for i in 2:
			_sprite("fader_slot", Vector2(cxm - 130 + i * 260, 460 + 150), false, Color.WHITE, 1.0, 2040)
			_sprite("fader_cap", Vector2(cxm - 130 + i * 260, 460 + 150 + (i * 40 - 20)), false, Color.WHITE, 1.0, 2041)
	for i in 6:
		_sprite("knob", Vector2(cxm - 110 + i * 44, 460 + 60), false, Color.WHITE, 1.0, 2040)
	if st["sprites"].has("desk_lip_glow"):
		_sprite("desk_lip_glow", Vector2(640, 460), true, Color.WHITE, 1.0, 2050)


# ---- chapter set pieces and interlude --------------------------------------------------------------------------------------

func _piece_sprite(p: Dictionary, add: bool) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex(p["file"])
	s.centered = false
	var k := float(p.get("px_scale", 0.5))
	s.scale = Vector2(k, k)
	s.position = Vector2(p["pos"][0], p["pos"][1])
	s.z_as_relative = false
	if add:
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		s.material = mat
	return s


func _pieces(where: String) -> void:
	var st: Dictionary = M.get("stage", {})
	for p in st.get("pieces", []):
		if p["z"] != where:
			continue
		if p["id"] == "warp_streaks" and OS.get_environment("RW_WARP") != "1":
			continue  # off by default: only shown when asked for
		var s := _piece_sprite(p, p["id"] != "alien_banner" and p["id"] != "saucer_flyby")
		s.z_index = -2450 if where == "behind" else 1700
		if p["id"] == "alien_banner" or p["id"] == "saucer_flyby":
			s.z_index = -2440
		add_child(s)


func _pieces_sheet() -> void:
	var st: Dictionary = M["stage"]
	var i := 0
	for p in st["pieces"]:
		var cell := Control.new()
		cell.position = Vector2(8 + (i % 4) * 318, 8 + (i / 4) * 350)
		cell.size = Vector2(310, 340)
		cell.clip_contents = true
		add_child(cell)
		var bgc := ColorRect.new()
		bgc.color = Color(0.02, 0.03, 0.1)
		bgc.size = cell.size
		cell.add_child(bgc)
		var s := _piece_sprite(p, true)
		var sz: Array = p["size"]
		var k := minf(300.0 / sz[0], 300.0 / sz[1])
		s.scale *= k
		s.position = Vector2(5, 30)
		s.z_index = 0
		s.material = null
		cell.add_child(s)
		var l := Label.new()
		l.text = "%s  %s  z=%s" % [p["id"], p["anim"], p["z"]]
		l.position = Vector2(5, 4)
		l.add_theme_font_size_override("font_size", 13)
		cell.add_child(l)
		i += 1


func _interlude(flood: bool) -> void:
	var chap_root := ROOT
	var chap: Dictionary = M
	ROOT = "res://assets/story/night_one/"
	M = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "manifest.json"))
	_tcache.clear()
	_stage(false)
	ROOT = chap_root
	M = chap
	_tcache.clear()
	var il: Dictionary = M["interlude"]
	var sp: Dictionary = il["sprites"]
	var an: Dictionary = il["anchors"]
	var hv := Vector2(an["ufo_hover"][0], an["ufo_hover"][1])
	var bf := Vector2(an["beam_floor"][0], an["beam_floor"][1])
	var mk := func(id: String, pos: Vector2, add: bool, tint: Color, sc: Vector2, z: int) -> Sprite2D:
		var d: Dictionary = sp[id]
		var s := Sprite2D.new()
		s.texture = tex(d["file"])
		s.centered = false
		var k := float(d["px_scale"])
		s.scale = Vector2(k, k) * sc
		s.position = pos - Vector2(d["pivot"][0], d["pivot"][1]) * s.scale
		s.modulate = tint
		s.z_as_relative = false
		s.z_index = z
		if add:
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			s.material = mat
		add_child(s)
		return s
	mk.call("ufo_glow", hv + Vector2(0, 30), true, Color(0.5, 1.0, 0.8, 0.8), Vector2.ONE, 2400)
	var beam_top := hv + Vector2(0, 30)
	var beam_h: float = float(sp["tractor_beam"]["size"][1])
	mk.call("tractor_beam", beam_top, true, Color(0.55, 1.0, 0.85, 0.9), Vector2(1.0, (bf.y - beam_top.y + 20.0) / beam_h), 2401)
	mk.call("ufo", hv, false, Color.WHITE, Vector2.ONE, 2402)
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in 16:
		var p := Vector2(bf.x + rng.randf_range(-170, 170), rng.randf_range(bf.y - 180, bf.y + 30))
		mk.call("sparkle", p, true, Color(0.8, 1.0, 0.9, rng.randf_range(0.5, 1.0)), Vector2.ONE * rng.randf_range(0.5, 1.2), 2403)
	if flood:
		mk.call("light_flood", Vector2(640, 360), true, Color(1, 1, 1, 0.7), Vector2.ONE, 2600)
