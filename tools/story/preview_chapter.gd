extends "res://tools/story/preview_art.gd"
## Review contact sheet for the chapter art (underworld, mothership ...), built on Night One's preview_art.gd.
##   RW_CHAPTER = underworld (default) | mothership | night_one
##   RW_PREVIEW = chars | chars_b | heads | joints | sil | stage | stage_low | deck   (inherited sheets)
##                set         the empty stage (no crowd, no beams) to inspect the room and the pieces
##                close       RW_ARCHS=a,b,c large rigs (idle, dance, cheer) to check joints and details
##                pieces      the stage with every authored `stage.pieces` entry switched on, plus the pieces alone
##                interlude   the `interlude` sprites composited over Night One's club backdrop
##   godot --path . -s tools/shoot.gd -- res://tools/story/preview_chapter.tscn /tmp/shots 30:shot:name
##   RW_VIEW = court | pit | furnace (any id in stage.views): render that room with the crowd rig in `stage`, `stage_low`, `set`, `pieces` modes
##                passage     the stage.sprites.passage_frame arch at 2x over a lava-orange backdrop

var chapter := "underworld"
var _front_layers: Array = []


func _ready() -> void:
	if OS.has_environment("RW_CHAPTER"):
		chapter = OS.get_environment("RW_CHAPTER")
	ROOT = "res://assets/story/%s/" % chapter
	M = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "manifest.json"))
	if OS.has_environment("RW_VIEW"):
		_select_view(OS.get_environment("RW_VIEW"))
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
			_stage(true, false, true)
		"close":
			_close()
		"pieces":
			_pieces_sheet()
		"interlude", "interlude_flood":
			_interlude(mode == "interlude_flood")
		"passage":
			_passage()


## RW_VIEW=<id>: render one of `stage.views` (court, pit, furnace ...) instead of the main room. The view's backdrop replaces the
## main one, its anchors override the main anchors (missing optional features are switched off, as the runtime does), its pieces
## replace stage.pieces, and its `z: front` layers are drawn over the crowd.
func _select_view(id: String) -> void:
	var st: Dictionary = M["stage"]
	var view := {}
	for v in st.get("views", []):
		if v["id"] == id:
			view = v
	if view.is_empty():
		push_error("no view " + id)
		return
	var A: Dictionary = st["anchors"].duplicate(true)
	for k in view["anchors"]:
		A[k] = view["anchors"][k]
	if not view["anchors"].has("woofers"):
		A["woofers"] = []
	if not view["anchors"].has("led_screen"):
		A["led_screen"] = [-900, -900, 10, 10]
	if not view["anchors"].has("doorway"):
		A["doorway"] = [-900, -900, 10, 10]
	if not view["anchors"].has("disco_ball"):
		A["disco_ball"] = [640, -400]
	st["anchors"] = A
	st["sprites"].erase("door_open")
	var layers: Array = []
	_front_layers = []
	for L in view["layers"]:
		if L.get("z", "") == "front":
			_front_layers.append(L)
		else:
			layers.append(L)
	for L in st["layers"]:
		if L["id"] == "desk_top":
			layers.append(L)
	st["layers"] = layers
	st["pieces"] = view.get("pieces", [])


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


func _stage(low: bool, deck_only := false, empty := false) -> void:
	super._stage(low, deck_only, empty)
	for L in _front_layers:
		_add(L["file"], Vector2(L["pos"][0], L["pos"][1]), Vector2(L["size"][0], L["size"][1]), 1400)


## stage.pieces with their `blend` (parent's _pieces guesses it from the id, which is only right for the mothership)
func _pieces(where: String) -> void:
	for p in M.get("stage", {}).get("pieces", []):
		if p["z"] != where:
			continue
		var z := 1400 if where == "front" else (-2880 if p["id"] == "skull_throne" else -2950)
		_add(p["file"], Vector2(p["pos"][0], p["pos"][1]), Vector2(p["size"][0], p["size"][1]), z, p.get("blend", "mix") == "add")


## the passage_frame sprite at 1x and 2x over the main room
func _passage() -> void:
	var sp: Dictionary = M["stage"]["sprites"]["passage_frame"]
	var k := float(sp["px_scale"])
	var back := ColorRect.new()
	back.color = Color(0.9, 0.3, 0.1)
	back.size = Vector2(1280, 720)
	back.z_index = -3000
	add_child(back)
	var s := Sprite2D.new()
	s.texture = tex(sp["file"])
	s.centered = false
	s.scale = Vector2(k, k) * 2.0
	s.position = Vector2(640, 360) - Vector2(sp["pivot"][0], sp["pivot"][1]) * s.scale
	add_child(s)


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


## hospital waking interlude: Underworld's room under half-open eyelids, a soft white wash and the heartbeat trace
func _interlude_hospital() -> void:
	var chap_root := ROOT
	var chap: Dictionary = M
	ROOT = "res://assets/story/underworld/"
	M = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "manifest.json"))
	_tcache.clear()
	_stage(true)
	ROOT = chap_root
	M = chap
	_tcache.clear()
	var S: Dictionary = M["interlude"]["sprites"]
	var gap := 90.0 if OS.get_environment("RW_OPEN") == "" else float(OS.get_environment("RW_OPEN"))
	var put := func(id: String, pos: Vector2, add: bool, mod: Color, z: int, mul := 1.0) -> Sprite2D:
		var d: Dictionary = S[id]
		var s := Sprite2D.new()
		s.texture = tex(d["file"])
		s.centered = false
		var k := float(d["px_scale"]) * mul
		s.scale = Vector2(k, k)
		s.position = pos - Vector2(d["pivot"][0], d["pivot"][1]) * k
		s.modulate = mod
		s.z_as_relative = false
		s.z_index = z
		if add:
			var mat := CanvasItemMaterial.new()
			mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
			s.material = mat
		add_child(s)
		return s
	put.call("white_wash", Vector2(640, 360), false, Color(1, 1, 1, 0.25), 2500)
	put.call("eyelid_top", Vector2(640, 360 - gap), false, Color.WHITE, 2600)
	put.call("eyelid_bottom", Vector2(640, 360 + gap), false, Color.WHITE, 2600)
	put.call("monitor_line", Vector2(128, 600), true, Color(0.6, 1.0, 0.8, 0.9), 2700)
	_label("hospital interlude: eyelids open %d px, white wash, heartbeat trace" % int(gap), Vector2(10, 4), 14)


func _interlude(_flood := false) -> void:
	if chapter == "hospital":
		_interlude_hospital()
		return
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
