class_name CloakroomArt
extends RefCounted
## The cloakroom's procedural art: sixteen 64 px symbols (four per rave), the two control pictograms, and per-theme palettes. PLACEHOLDER: the symbols are chunky silhouettes
## drawn from a few primitives on a 32 x 32 grid and doubled to 64 px with a dark one-pixel outline; they are clear and distinct but below the art standard in
## art/reference/standard/ (no shading, no hand-placed detail). Everything is drawn once and cached as textures; nothing here reads a file.

const SIZE := 64
const GRID := 32
const OUTLINE := Color("1a1626")
const DEFAULTS := {
	"space": ["planet", "rocket", "star", "comet"],
	"magic": ["unicorn", "wand", "potion", "crown"],
	"dinos": ["egg", "claw", "fern", "skull"],
	"transport": ["bus", "bike", "train", "boat"],
}
const ALIASES := {"ringed_planet": "planet"}
const THEMES_PATH := "res://content/bedsit/themes.json"
const CUSTOMER_KINDS := ["alien", "wizard", "fairy", "dino", "commuter", "cyclist"]

static var _cache: Dictionary = {}


## The four symbol ids of `theme`: the config's `cloakroom_symbols` ([{id, icon}] or ids) when it names four distinct symbols the art can draw, else the theme's defaults.
static func symbols_for(theme: String, cfg: Variant) -> Array:
	var out: Array = []
	if typeof(cfg) == TYPE_ARRAY:
		for s: Variant in cfg:
			var id := str((s as Dictionary).get("id", "")) if typeof(s) == TYPE_DICTIONARY else str(s)
			id = ALIASES.get(id, id)
			if _known(id) and id not in out:
				out.append(id)
	if out.size() == 4:
		return out
	var data := theme_data(theme)
	var listed: Array = []
	for id: Variant in data.get("symbols", []):
		if _known(str(id)) and str(id) not in listed:
			listed.append(str(id))
	if listed.size() == 4:
		return listed
	return (DEFAULTS.get(theme, DEFAULTS["space"]) as Array).duplicate()


## The rave's entry of content/bedsit/themes.json "cloakroom" ({symbols, customers, attendant}; {} when there is none).
static func theme_data(theme: String) -> Dictionary:
	if not _cache.has("themes"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(THEMES_PATH)) if FileAccess.file_exists(THEMES_PATH) else null
		_cache["themes"] = (parsed as Dictionary).get("cloakroom", {}) if typeof(parsed) == TYPE_DICTIONARY else {}
	var d: Variant = (_cache["themes"] as Dictionary).get(theme, {})
	return d if typeof(d) == TYPE_DICTIONARY else {}


static func _known(id: String) -> bool:
	for k: String in DEFAULTS:
		if id in (DEFAULTS[k] as Array):
			return true
	return false


## The 64 px texture of symbol `id` (cached).
static func symbol_texture(id: String) -> Texture2D:
	id = ALIASES.get(id, id)
	var key := "sym:" + id
	if not _cache.has(key):
		_cache[key] = ImageTexture.create_from_image(symbol_image(id))
	return _cache[key]


static func symbol_image(id: String) -> Image:
	var c := _Canvas.new()
	match ALIASES.get(id, id):
		"planet": _planet(c)
		"rocket": _rocket(c)
		"star": _star(c)
		"comet": _comet(c)
		"unicorn": _unicorn(c)
		"wand": _wand(c)
		"potion": _potion(c)
		"crown": _crown(c)
		"egg": _egg(c)
		"claw": _claw(c)
		"fern": _fern(c)
		"skull": _skull(c)
		"bus": _bus(c)
		"bike": _bike(c)
		"train": _train(c)
		"boat": _boat(c)
		_: c.circle(16, 16, 9, Color("c0c0c8"))
	return c.finish()


## The pictogram of a control id ("same": two identical shapes joined by a bar; "different": two contrasting shapes) centred in `r` of canvas item `ci`, `a` the alpha.
## No words. Used by the view's tutorial and by the host's controls layer (hook: it only draws labels today).
static func draw_pictogram(ci: CanvasItem, r: Rect2, kind: String, a := 1.0) -> void:
	var s := minf(r.size.x * 0.5, r.size.y) * 0.62
	var c := r.get_center()
	var left := c + Vector2(-s * 0.62, 0)
	var right := c + Vector2(s * 0.62, 0)
	var ink := Color(0.10, 0.10, 0.14, 0.95 * a)
	var green := Color(0.30, 0.85, 0.55, a)
	var orange := Color(1.0, 0.62, 0.20, a)
	var blue := Color(0.35, 0.65, 1.0, a)
	if kind == "same":
		for p: Vector2 in [left, right]:
			ci.draw_circle(p, s * 0.5 + 2.0, ink)
			ci.draw_circle(p, s * 0.5, green)
		ci.draw_rect(Rect2(c + Vector2(-s * 0.14, -s * 0.2), Vector2(s * 0.28, s * 0.12)), Color(1, 1, 1, a))
		ci.draw_rect(Rect2(c + Vector2(-s * 0.14, s * 0.08), Vector2(s * 0.28, s * 0.12)), Color(1, 1, 1, a))
	else:
		ci.draw_circle(left, s * 0.5 + 2.0, ink)
		ci.draw_circle(left, s * 0.5, blue)
		var tri := PackedVector2Array([right + Vector2(0, -s * 0.62), right + Vector2(s * 0.58, s * 0.42), right + Vector2(-s * 0.58, s * 0.42)])
		var tri_ink := PackedVector2Array([right + Vector2(0, -s * 0.62 - 3), right + Vector2(s * 0.58 + 3, s * 0.42 + 2), right + Vector2(-s * 0.58 - 3, s * 0.42 + 2)])
		ci.draw_colored_polygon(tri_ink, ink)
		ci.draw_colored_polygon(tri, orange)


# --- the drawing kit -------------------------------------------------------------------------------------------------------------

class _Canvas:
	extends RefCounted
	var img: Image

	func _init() -> void:
		img = Image.create(CloakroomArt.GRID, CloakroomArt.GRID, false, Image.FORMAT_RGBA8)

	func px(x: int, y: int, col: Color) -> void:
		if x >= 0 and y >= 0 and x < CloakroomArt.GRID and y < CloakroomArt.GRID:
			img.set_pixel(x, y, col)

	func rect(x: float, y: float, w: float, h: float, col: Color) -> void:
		for j in range(int(floor(y)), int(ceil(y + h))):
			for i in range(int(floor(x)), int(ceil(x + w))):
				px(i, j, col)

	func circle(cx: float, cy: float, r: float, col: Color) -> void:
		ellipse(cx, cy, r, r, col)

	func ellipse(cx: float, cy: float, rx: float, ry: float, col: Color, rot := 0.0, inner := 0.0) -> void:
		var cs := cos(rot)
		var sn := sin(rot)
		for j in CloakroomArt.GRID:
			for i in CloakroomArt.GRID:
				var dx := float(i) + 0.5 - cx
				var dy := float(j) + 0.5 - cy
				var u := (dx * cs + dy * sn) / rx
				var v := (-dx * sn + dy * cs) / ry
				var d := u * u + v * v
				if d <= 1.0 and d >= inner * inner:
					px(i, j, col)

	func poly(pts: Array, col: Color) -> void:
		var arr := PackedVector2Array()
		for p: Variant in pts:
			arr.append(p as Vector2)
		for j in CloakroomArt.GRID:
			for i in CloakroomArt.GRID:
				if Geometry2D.is_point_in_polygon(Vector2(float(i) + 0.5, float(j) + 0.5), arr):
					px(i, j, col)

	func line(a: Vector2, b: Vector2, w: float, col: Color) -> void:
		var steps := int(a.distance_to(b) * 2.0) + 1
		for s in steps + 1:
			var p := a.lerp(b, float(s) / float(steps))
			circle(p.x, p.y, w * 0.5, col)

	## The outline pass and the doubling to 64 px.
	func finish() -> Image:
		var src := img.duplicate() as Image
		for j in CloakroomArt.GRID:
			for i in CloakroomArt.GRID:
				if src.get_pixel(i, j).a > 0.0:
					continue
				for o: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
					var x: int = i + o.x
					var y: int = j + o.y
					if x >= 0 and y >= 0 and x < CloakroomArt.GRID and y < CloakroomArt.GRID and src.get_pixel(x, y).a > 0.0:
						img.set_pixel(i, j, CloakroomArt.OUTLINE)
						break
		img.resize(CloakroomArt.SIZE, CloakroomArt.SIZE, Image.INTERPOLATE_NEAREST)
		return img


# --- space ----------------------------------------------------------------------------------------------------------------------

static func _planet(c: _Canvas) -> void:
	c.ellipse(16, 16, 15, 4.2, Color("f2c14e"), -0.45)
	c.circle(16, 16, 9.5, Color("7a5cd6"))
	c.circle(13, 13, 4, Color("9d86ee"))
	c.ellipse(16, 16, 15, 4.2, Color("ffe08a"), -0.45, 0.8)  # (the ring's front edge)
	c.rect(4, 20, 4, 1, Color("ffe08a"))


static func _rocket(c: _Canvas) -> void:
	c.poly([Vector2(16, 2), Vector2(22, 10), Vector2(22, 22), Vector2(10, 22), Vector2(10, 10)], Color("e9edf5"))
	c.poly([Vector2(16, 2), Vector2(21, 9), Vector2(11, 9)], Color("e8503a"))
	c.poly([Vector2(10, 16), Vector2(4, 25), Vector2(10, 22)], Color("e8503a"))
	c.poly([Vector2(22, 16), Vector2(28, 25), Vector2(22, 22)], Color("e8503a"))
	c.circle(16, 14, 3.2, Color("5ec8f2"))
	c.poly([Vector2(12, 22), Vector2(20, 22), Vector2(16, 30)], Color("ffb23f"))


static func _star(c: _Canvas) -> void:
	var pts: Array = []
	for k in 10:
		var ang := -PI / 2.0 + float(k) * PI / 5.0
		var rad := 14.5 if k % 2 == 0 else 6.0
		pts.append(Vector2(16.0 + cos(ang) * rad, 16.5 + sin(ang) * rad))
	c.poly(pts, Color("ffd93d"))
	c.circle(16, 16.5, 3, Color("fff1a8"))


static func _comet(c: _Canvas) -> void:
	c.poly([Vector2(21, 9), Vector2(28, 12), Vector2(3, 28), Vector2(8, 24)], Color("5ec8f2"))
	c.poly([Vector2(23, 12), Vector2(28, 17), Vector2(6, 29), Vector2(10, 24)], Color("a8e6ff"))
	c.circle(21, 15, 7, Color("e9edf5"))
	c.circle(19, 13, 3, Color("ffffff"))


# --- magic ----------------------------------------------------------------------------------------------------------------------

static func _unicorn(c: _Canvas) -> void:
	c.poly([Vector2(14, 2), Vector2(17, 9), Vector2(11, 9)], Color("ffd93d"))  # horn
	c.poly([Vector2(8, 10), Vector2(18, 9), Vector2(23, 14), Vector2(29, 20), Vector2(28, 25), Vector2(20, 26), Vector2(14, 22), Vector2(8, 24)], Color("f6f1ff"))
	c.poly([Vector2(6, 10), Vector2(13, 8), Vector2(11, 18), Vector2(7, 26), Vector2(4, 18)], Color("e45bd4"))  # mane
	c.rect(18, 15, 2, 2, Color("1a1626"))  # eye
	c.circle(26.5, 22.5, 1, Color("e8a0c8"))


static func _wand(c: _Canvas) -> void:
	c.line(Vector2(6, 27), Vector2(21, 12), 3.2, Color("6b4a2e"))
	c.line(Vector2(6, 27), Vector2(10, 23), 3.2, Color("ffe08a"))
	var pts: Array = []
	for k in 10:
		var ang := -PI / 2.0 + float(k) * PI / 5.0
		var rad := 8.0 if k % 2 == 0 else 3.4
		pts.append(Vector2(22.0 + cos(ang) * rad, 9.0 + sin(ang) * rad))
	c.poly(pts, Color("ff8fe0"))
	c.circle(22, 9, 2, Color("fff"))


static func _potion(c: _Canvas) -> void:
	c.rect(12, 2, 8, 4, Color("a8744a"))
	c.rect(13, 6, 6, 6, Color("d8f0ff"))
	c.circle(16, 20, 10.5, Color("d8f0ff"))
	c.circle(16, 21.5, 8.5, Color("a23fe8"))
	c.rect(7, 18, 18, 2, Color("a23fe8"))
	c.circle(13, 22, 2, Color("e0a8ff"))
	c.circle(19, 19, 1.4, Color("e0a8ff"))


static func _crown(c: _Canvas) -> void:
	c.poly([Vector2(3, 24), Vector2(3, 9), Vector2(10, 16), Vector2(16, 5), Vector2(22, 16), Vector2(29, 9), Vector2(29, 24)], Color("ffd93d"))
	c.rect(3, 22, 26, 5, Color("e0a420"))
	c.circle(16, 17, 2.4, Color("e8503a"))
	c.circle(8, 21, 1.6, Color("3fb8ff"))
	c.circle(24, 21, 1.6, Color("3fe89a"))


# --- dinos ----------------------------------------------------------------------------------------------------------------------

static func _egg(c: _Canvas) -> void:
	c.ellipse(16, 18, 9.5, 12.5, Color("f1ead0"))
	c.circle(16, 10, 6.5, Color("f1ead0"))
	c.circle(12, 17, 2.2, Color("7fbf5a"))
	c.circle(20, 22, 2.6, Color("7fbf5a"))
	c.circle(18, 13, 1.6, Color("7fbf5a"))
	c.circle(12, 24, 1.4, Color("7fbf5a"))


static func _claw(c: _Canvas) -> void:
	c.poly([Vector2(4, 4), Vector2(10, 4), Vector2(13, 20), Vector2(10, 29)], Color("f2ece0"))
	c.poly([Vector2(12, 3), Vector2(18, 3), Vector2(20, 20), Vector2(16, 30)], Color("f2ece0"))
	c.poly([Vector2(20, 4), Vector2(27, 5), Vector2(27, 20), Vector2(23, 29)], Color("f2ece0"))
	c.rect(3, 2, 25, 4, Color("c97b3c"))


static func _fern(c: _Canvas) -> void:
	c.line(Vector2(16, 30), Vector2(16, 3), 2.2, Color("3d8a3a"))
	for k in 6:
		var y := 6.0 + float(k) * 4.2
		var len := 12.0 - float(k) * 0.9
		c.poly([Vector2(16, y + 2), Vector2(16 - len, y - 3), Vector2(16, y - 0.5)], Color("5ec04a"))
		c.poly([Vector2(16, y + 2), Vector2(16 + len, y - 3), Vector2(16, y - 0.5)], Color("5ec04a"))


static func _skull(c: _Canvas) -> void:
	c.circle(16, 13, 11.5, Color("efe9da"))
	c.rect(9, 18, 14, 9, Color("efe9da"))
	c.circle(11.5, 14, 3.4, Color("1a1626"))
	c.circle(20.5, 14, 3.4, Color("1a1626"))
	c.poly([Vector2(16, 17), Vector2(14.5, 21), Vector2(17.5, 21)], Color("1a1626"))
	for x in [11, 14, 17, 20]:
		c.rect(x, 24, 1, 3, Color("1a1626"))


# --- transport ------------------------------------------------------------------------------------------------------------------

static func _bus(c: _Canvas) -> void:
	c.rect(2, 6, 28, 18, Color("e8503a"))
	c.rect(2, 16, 28, 3, Color("ffd93d"))
	for x in [4, 11, 18]:
		c.rect(x, 9, 6, 5, Color("a8e6ff"))
	c.rect(25, 9, 4, 8, Color("a8e6ff"))
	c.circle(9, 24, 3.4, Color("2a2a34"))
	c.circle(23, 24, 3.4, Color("2a2a34"))
	c.circle(9, 24, 1.2, Color("c0c0c8"))
	c.circle(23, 24, 1.2, Color("c0c0c8"))


static func _bike(c: _Canvas) -> void:
	c.ellipse(8, 21, 6.5, 6.5, Color("2a2a34"), 0.0, 0.7)
	c.ellipse(24, 21, 6.5, 6.5, Color("2a2a34"), 0.0, 0.7)
	c.line(Vector2(8, 21), Vector2(15, 11), 2, Color("3fa0ff"))
	c.line(Vector2(15, 11), Vector2(24, 21), 2, Color("3fa0ff"))
	c.line(Vector2(8, 21), Vector2(18, 21), 2, Color("3fa0ff"))
	c.line(Vector2(18, 21), Vector2(15, 11), 2, Color("3fa0ff"))
	c.line(Vector2(24, 21), Vector2(22, 8), 2, Color("3fa0ff"))
	c.rect(19, 6, 6, 2, Color("e8503a"))
	c.rect(11, 8, 6, 2, Color("e8503a"))


static func _train(c: _Canvas) -> void:
	c.rect(6, 4, 20, 20, Color("3fa0ff"))
	c.rect(6, 4, 20, 5, Color("e9edf5"))
	c.rect(9, 11, 6, 6, Color("a8e6ff"))
	c.rect(17, 11, 6, 6, Color("a8e6ff"))
	c.circle(10, 21, 1.8, Color("ffd93d"))
	c.circle(22, 21, 1.8, Color("ffd93d"))
	c.rect(3, 26, 26, 2, Color("8a8a96"))
	c.rect(8, 24, 3, 3, Color("2a2a34"))
	c.rect(21, 24, 3, 3, Color("2a2a34"))


static func _boat(c: _Canvas) -> void:
	c.rect(15, 3, 2, 18, Color("6b4a2e"))
	c.poly([Vector2(17, 4), Vector2(28, 19), Vector2(17, 19)], Color("f6f1ff"))
	c.poly([Vector2(15, 7), Vector2(15, 19), Vector2(6, 19)], Color("e8503a"))
	c.poly([Vector2(3, 21), Vector2(29, 21), Vector2(24, 28), Vector2(8, 28)], Color("7a4a2a"))
	c.rect(3, 29, 26, 2, Color("3fa0ff"))


# --- the people and the room (palettes per rave; the view draws them from shapes) ---------------------------------------------------

## The look of a rave's cloakroom: {wall, floor, counter, lamp_off, lamp_on, customers: [{kind, body, skin, extra}], attendant: {kind, body, skin}}.
static func look(theme: String) -> Dictionary:
	var out := _look(theme)
	var data := theme_data(theme)
	if data.has("customers"):
		out["customers"] = (data["customers"] as Array).map(_person)
	if data.has("attendant"):
		out["attendant"] = _person(data["attendant"])
	return out


static func _person(p: Variant) -> Dictionary:
	var d: Dictionary = p
	return {"kind": str(d.get("kind", "alien")), "body": Color(str(d.get("body", "#888888"))), "skin": Color(str(d.get("skin", "#dddddd"))), "extra": Color(str(d.get("extra", "#ffffff")))}


static func _look(theme: String) -> Dictionary:
	match theme:
		"magic":
			return {"wall": Color("2d1f4d"), "floor": Color("3b2a63"), "counter": Color("7a4a8a"), "customers": [
				{"kind": "wizard", "body": Color("4a6fd8"), "skin": Color("f1c9a5"), "extra": Color("ffd93d")},
				{"kind": "fairy", "body": Color("e45bd4"), "skin": Color("f8d8c8"), "extra": Color("a8e6ff")},
				{"kind": "wizard", "body": Color("2fa86a"), "skin": Color("d9a77f"), "extra": Color("e8503a")}],
				"attendant": {"kind": "wizard", "body": Color("7a3fd0"), "skin": Color("f1c9a5"), "extra": Color("ffd93d")}}
		"dinos":
			return {"wall": Color("2a3a1f"), "floor": Color("4a3f26"), "counter": Color("8a6a3a"), "customers": [
				{"kind": "dino", "body": Color("5ec04a"), "skin": Color("5ec04a"), "extra": Color("ffd93d")},
				{"kind": "dino", "body": Color("e88a3a"), "skin": Color("e88a3a"), "extra": Color("a23fe8")},
				{"kind": "dino", "body": Color("3fa0c8"), "skin": Color("3fa0c8"), "extra": Color("e8503a")}],
				"attendant": {"kind": "dino", "body": Color("a8c83f"), "skin": Color("a8c83f"), "extra": Color("e8503a")}}
		"transport":
			return {"wall": Color("22303f"), "floor": Color("35393f"), "counter": Color("6a7a8a"), "customers": [
				{"kind": "commuter", "body": Color("3a8ad8"), "skin": Color("f1c9a5"), "extra": Color("e8503a")},
				{"kind": "cyclist", "body": Color("e8c83a"), "skin": Color("d9a77f"), "extra": Color("3fe89a")},
				{"kind": "commuter", "body": Color("d8503a"), "skin": Color("8a5a3a"), "extra": Color("ffffff")}],
				"attendant": {"kind": "commuter", "body": Color("2a6a4a"), "skin": Color("f1c9a5"), "extra": Color("ffd93d")}}
	return {"wall": Color("1a1f3d"), "floor": Color("272a4a"), "counter": Color("5a5f8a"), "customers": [
		{"kind": "alien", "body": Color("4ad88a"), "skin": Color("7fe8b0"), "extra": Color("ffd93d")},
		{"kind": "alien", "body": Color("a77fe8"), "skin": Color("c9a8f8"), "extra": Color("5ec8f2")},
		{"kind": "alien", "body": Color("e8803a"), "skin": Color("f8b08a"), "extra": Color("ffffff")}],
		"attendant": {"kind": "alien", "body": Color("5ec8f2"), "skin": Color("a8e6ff"), "extra": Color("e8503a")}}
