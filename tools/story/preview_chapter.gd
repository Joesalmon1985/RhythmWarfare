extends "res://tools/story/preview_art.gd"
## Review contact sheet for the chapter art (underworld, mothership ...), built on Night One's preview_art.gd.
##   RW_CHAPTER = underworld (default) | mothership | night_one
##   RW_PREVIEW = chars | chars_b | heads | joints | sil | stage | stage_low | deck   (inherited sheets)
##                set         the empty stage (no crowd, no beams) to inspect the room and the pieces
##                close       RW_ARCHS=a,b,c large rigs (idle, dance, cheer) to check joints and details
##                pieces      the stage with every authored `stage.pieces` entry switched on, plus the pieces alone
##                interlude   the `interlude` sprites composited over Night One's club backdrop
##   godot --path . -s tools/shoot.gd -- res://tools/story/preview_chapter.tscn /tmp/shots 30:shot:name

var chapter := "underworld"


func tex(p: String) -> Texture2D:
	if not _tcache.has(p):
		_tcache[p] = load("res://assets/story/%s/%s" % [chapter, p])
	return _tcache[p]


func _ready() -> void:
	if OS.has_environment("RW_CHAPTER"):
		chapter = OS.get_environment("RW_CHAPTER")
	M = JSON.parse_string(FileAccess.get_file_as_string("res://assets/story/%s/manifest.json" % chapter))
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
		"stage", "stage_low":
			_stage(mode == "stage_low")
		"sil":
			_sil()
		"joints":
			_joints()
		"deck":
			_deck()
		"set":
			_stage(true)
			for c in get_children():
				if c is Rig or (c is Sprite2D and c.z_index == 50):
					c.queue_free()
		"close":
			_close()
		"pieces":
			_pieces_sheet()
		"interlude":
			_interlude()


func _add(id_tex: String, pos: Vector2, size: Vector2, z: int, add := false, mod := Color.WHITE) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex(id_tex)
	s.centered = false
	s.position = pos
	s.scale = Vector2(size.x / s.texture.get_width(), size.y / s.texture.get_height())
	s.z_as_relative = false
	s.z_index = z
	s.modulate = mod
	if add:
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		s.material = mat
	add_child(s)
	return s


func _stage(low: bool, deck_only := false) -> void:
	super._stage(low, deck_only)
	for p in M["stage"].get("pieces", []):
		var z := 1400 if p["z"] == "front" else (-2880 if p["id"] == "skull_throne" else -2950)
		_add(p["file"], Vector2(p["pos"][0], p["pos"][1]), Vector2(p["size"][0], p["size"][1]), z, p.get("blend", "mix") == "add")


func _pieces_sheet() -> void:
	var ps: Array = M["stage"].get("pieces", [])
	var x := 10.0
	var y := 10.0
	var rowh := 0.0
	for p in ps:
		var sz := Vector2(p["size"][0], p["size"][1])
		var k := minf(1.0, 400.0 / maxf(sz.x, sz.y))
		if x + sz.x * k > 1270:
			x = 10.0
			y += rowh + 30
			rowh = 0.0
		var back := ColorRect.new()
		back.color = Color(0.05, 0.02, 0.06)
		back.position = Vector2(x, y)
		back.size = sz * k
		back.z_index = -3000
		back.z_as_relative = false
		add_child(back)
		var s := _add(p["file"], Vector2(x, y), sz * k, 0, p.get("blend", "mix") == "add")
		_label("%s (%s, %s)" % [p["id"], p["anim"], p["z"]], Vector2(x, y + sz.y * k + 2), 12)
		x += sz.x * k + 16
		rowh = maxf(rowh, sz.y * k)


func _interlude() -> void:
	var IL: Dictionary = M["interlude"]
	var S: Dictionary = IL["sprites"]
	var A: Dictionary = IL["anchors"]
	var no := "res://assets/story/night_one/"
	var bgs := Sprite2D.new()
	bgs.texture = load(no + "source/backdrop.svg")
	bgs.centered = false
	bgs.scale = Vector2(0.5, 0.5)
	bgs.z_index = -3000
	bgs.z_as_relative = false
	add_child(bgs)
	var dk := Sprite2D.new()
	dk.texture = load(no + "source/desk_top.svg")
	dk.centered = false
	dk.position = Vector2(0, 460)
	dk.scale = Vector2(0.5, 0.5)
	dk.z_index = 2000
	dk.z_as_relative = false
	add_child(dk)
	var sp := func(id: String, pos: Vector2, add: bool, mod: Color, mul: float, z: int, flip := false) -> Sprite2D:
		var d: Dictionary = S[id]
		var s := Sprite2D.new()
		s.texture = tex(d["file"])
		s.centered = false
		var k := float(d["px_scale"]) * mul
		s.scale = Vector2(-k if flip else k, k)
		s.position = pos - Vector2(d["pivot"][0] * (-1.0 if flip else 1.0), d["pivot"][1]) * k
		s.modulate = mod
		s.z_as_relative = false
		s.z_index = z
		if add:
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			s.material = mat
		add_child(s)
		return s
	var wash: Sprite2D = sp.call("dark_wash", Vector2(640, 360), false, Color(1, 1, 1, 0.8), 1.0, 600)
	var co: Array = A["crack_origin"]
	var ce: Array = A.get("crack_end", [640, 450])
	sp.call("crack_glow", Vector2(co[0], co[1]), true, Color.WHITE, 1.0, 700)
	var pc: Array = A["portal_centre"]
	sp.call("portal_vortex", Vector2(pc[0], pc[1]), false, Color.WHITE, 1.0, 800)
	for i in 2:
		var fp: Array = A["flame_jets"][i]
		sp.call("flame_jet", Vector2(fp[0], fp[1]), false, Color.WHITE, 1.0, 900, i == 1)
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in 40:
		var e: Dictionary = S["embers"]
		var s: Sprite2D = sp.call("embers", Vector2(rng.randf_range(100, 1180), rng.randf_range(80, 440)), true, Color.WHITE, rng.randf_range(0.5, 1.0), 1000)
		s.region_enabled = true
		var fs: Array = e["frame_size"]
		s.region_rect = Rect2((i % int(e["frames"])) * fs[0], 0, fs[0], fs[1])
		s.position = Vector2(rng.randf_range(100, 1180), rng.randf_range(80, 440))
	_label("interlude sprites over Night One", Vector2(10, 4), 14)


func _close() -> void:
	var names := (OS.get_environment("RW_ARCHS") if OS.has_environment("RW_ARCHS") else "imp,brute,fiend").split(",")
	var poses := ["idle", "dance", "cheer"]
	var variant := OS.get_environment("RW_VARIANT") if OS.has_environment("RW_VARIANT") else "a"
	for c in names.size():
		for r in poses.size():
			var rig := make_rig(names[c], variant, poses[r], 0)
			rig.scale = Vector2(1.18, 1.18)
			rig.position = Vector2(215 + c * 420 + (r - 1) * 125, 690)
			add_child(rig)
