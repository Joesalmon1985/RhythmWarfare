class_name StoryDeck
extends RefCounted
## The pad strip's skin: PadView stays the only input (its pads, hit rectangles and falling-note landing zones are unchanged); this draws
## the board around and under them in the look of the world's family (lead ruling 29, style guide section 11): the club desk in the
## Warehouse, a ship console, hell's copper, a clinical panel in the Hospital and (in green) the Ward, a cedar board for Galilee and
## Jerusalem, an instrument panel for the Squadron, a carved board on the Ember road, stone and iron in the Bassment, a neutral board
## elsewhere. One layout and one construction for every family: a tileable surface, a lip along the top, a raised plate under each pad
## pair, a recessed well round each pad, a bezel round the middle display and four lamps that count the beats of the bar. The pictures
## are drawn by tools/art/make_decks.py into assets/run/deck/<family>/ at the picture's internal pixel size and scaled here by
## screen height / 360 with nearest filtering, so the strip has the world's pixel grain; skins.json carries each family's colours and
## which art world uses which family. A new family is an entry there plus its pictures.
##
## The look belongs to the world, never to the player's role: the strip does not change inside a scene (it used to cut between a dancer's
## rail and the DJ desk when the journey's role changed). It changes only when the world does (and when the run goes down into the
## Bassment, whose dungeon borrows the run's strip), cross-fading over 0.4 s. Hooks: PadView.deck_under / deck_over.

const DIR := "res://assets/run/deck/"
const INTERNAL_LINES := 360.0  # the picture's internal resolution (StoryLowRes): the strip's pixels are the same size
const FADE_S := 0.4

var assets: StoryAssets
var run: StoryRun
var stage: StoryStage
var reduced := false
var high_contrast := false
var family_override := ""  # a fixed family (the title screen, tests); "" = from the world

static var _data: Dictionary = {}
static var _tex: Dictionary = {}


func setup(p_assets: StoryAssets, p_run: StoryRun, p_stage: StoryStage) -> void:
	assets = p_assets
	run = p_run
	stage = p_stage


static func data() -> Dictionary:
	if _data.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DIR + "skins.json")) if FileAccess.file_exists(DIR + "skins.json") else null
		_data = parsed if typeof(parsed) == TYPE_DICTIONARY else {"worlds": {}, "skins": {}}
	return _data


## The family of an art world (assets/story/<art>): "neutral" when the world has none.
static func family_of(art: String) -> String:
	return str((data().get("worlds", {}) as Dictionary).get(art, "neutral"))


static func skin_of(family: String) -> Dictionary:
	var skins: Dictionary = data().get("skins", {})
	return skins.get(family, skins.get("neutral", {}))


static func texture(family: String, part: String) -> Texture2D:
	var key := family + "/" + part
	if not _tex.has(key):
		var path := DIR + key + ".png"
		_tex[key] = load(path) as Texture2D if ResourceLoader.exists(path) else null
	return _tex[key]


## A skin colour by key (hex in skins.json).
static func color_of(skin: Dictionary, key: String, fallback: Color) -> Color:
	return Color.html(str(skin[key])) if skin.has(key) else fallback


## The family shown now: the world's, or the Bassment's while the run's dungeon has the strip (the run scene that owns the pad view
## says so through its `trial`; read, never changed).
func family(ci: CanvasItem = null) -> String:
	if family_override != "":
		return family_override
	if ci != null and ci.get_parent() != null:
		var tr: Variant = ci.get_parent().get("trial")
		if tr is Node and is_instance_valid(tr) and bool((tr as Node).get("active")) and bool((tr as Node).get("visible")):
			return "bassment"
	return family_of(assets.art if assets != null else "")


func skin(ci: CanvasItem = null) -> Dictionary:
	return skin_of(family(ci))


func _beats(now: float) -> float:
	var bpm: float = run.level.bpm if run != null and run.level != null else 120.0
	return maxf(now, 0.0) * bpm / 60.0


## 0 (the dancer) .. 1 (on stage as the DJ) at song time `now`, from the journey's roles. The strip's look no longer follows it (one
## look per world); kept as the journey's query.
func deck_mix(now: float) -> float:
	return stage.player.deck_mix_at(now) if stage != null and stage.player != null else 1.0


## A node that draws once through a callable (CanvasItem draw commands are kept until it is asked to redraw): the static layers cost
## nothing per frame.
class _Painter extends Node2D:
	var fn := Callable()

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)


var _layer: Node2D  # behind the pad view: the board (static), the club's platters (turned, not redrawn), the lamps and meters (per frame)
var _layer_key := ""
var _old: Node2D  # the layer being faded out
var _fade_t0 := -10.0
var _platters: Array = []
var _live: _Painter
var _live_args := {}


static func scale_of(ci: CanvasItem) -> float:
	var h := ci.get_viewport_rect().size.y if ci.is_inside_tree() else 720.0
	return maxf(h / INTERNAL_LINES, 1.0)


## The middle display's rectangle (the pad view draws its contents there; the deck its bezel).
static func display_rect(rects: Dictionary, size: Vector2) -> Rect2:
	var x0: float = (rects[2] as Rect2).end.x + (rects[2] as Rect2).size.x * 0.11 + 26.0
	var x1: float = (rects[3] as Rect2).position.x - (rects[3] as Rect2).size.x * 0.11 - 26.0
	return Rect2(x0, size.y * 0.2, x1 - x0, size.y * 0.5)


func _sync_layer(ci: CanvasItem, size: Vector2, rects: Dictionary, fam: String) -> void:
	var k := scale_of(ci)
	var key := "%s|%s|%s|%.3f" % [fam, size, str(rects), k]
	var wall := float(Time.get_ticks_msec()) / 1000.0
	if _layer == null or not is_instance_valid(_layer) or key != _layer_key:
		var first_look := _layer == null or not is_instance_valid(_layer) or _layer_key.get_slice("|", 0) == fam
		if _old != null and is_instance_valid(_old):
			_old.queue_free()
		_old = _layer if (_layer != null and is_instance_valid(_layer)) else null
		_layer_key = key
		_layer = _build_layer(ci, size, rects, fam, k)
		if not first_look:
			_fade_t0 = wall  # a new family: cross-fade
		elif _old != null:
			_old.queue_free()  # only the size changed: no fade
			_old = null
	if not ci.has_meta("deck_layer") or ci.get_meta("deck_layer") != _layer:  # another world's deck drew last: bring this one to the top and fade it in
		var prev: Variant = ci.get_meta("deck_layer") if ci.has_meta("deck_layer") else null
		ci.set_meta("deck_layer", _layer)
		ci.move_child(_layer, -1)
		if prev != null and is_instance_valid(prev):
			_fade_t0 = wall
	var a := 1.0 if reduced else clampf((wall - _fade_t0) / FADE_S, 0.0, 1.0)
	_layer.modulate.a = a
	_layer.visible = true
	if a >= 1.0:
		if _old != null and is_instance_valid(_old):
			_old.queue_free()
		_old = null
		for c in ci.get_children():  # the other worlds' boards stay built (a world comes back) but are not drawn
			if c != _layer and str(c.name).begins_with("DeckLayer"):
				(c as CanvasItem).visible = false


func _build_layer(ci: CanvasItem, size: Vector2, rects: Dictionary, fam: String, k: float) -> Node2D:
	var layer := Node2D.new()
	layer.name = "DeckLayer"
	layer.show_behind_parent = true
	layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	layer.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	ci.add_child(layer)
	_platters = []
	var sk := skin_of(fam)
	var bottom := _Painter.new()
	bottom.scale = Vector2(k, k)
	bottom.fn = func(c: CanvasItem) -> void: _draw_board(c, size / k, fam)
	layer.add_child(bottom)
	if bool(sk.get("spinners", false)) and texture(fam, "platter") != null:  # the club: a platter under each pad pair, turning on the beat
		for pair in [[rects[1], rects[2]], [rects[3], rects[4]]]:
			var a: Rect2 = pair[0]
			var b: Rect2 = pair[1]
			var rad := a.size.x * 1.13
			var pn := _Painter.new()
			pn.position = Vector2((a.position.x + b.end.x) * 0.5, a.get_center().y)
			pn.scale = Vector2(k, k)
			var tex := texture(fam, "platter")
			var half := rad / k
			pn.fn = func(c: CanvasItem) -> void: c.draw_texture_rect(tex, Rect2(-half, -half, half * 2.0, half * 2.0), false, Color(1, 1, 1, 0.9))
			layer.add_child(pn)
			_platters.append(pn)
	var top := _Painter.new()
	top.scale = Vector2(k, k)
	top.fn = func(c: CanvasItem) -> void: _draw_fittings(c, size, rects, fam, k)
	layer.add_child(top)
	_live = _Painter.new()
	_live.scale = Vector2(k, k)
	_live.fn = func(c: CanvasItem) -> void: _draw_live(c)
	layer.add_child(_live)
	return layer


func _nine(part: String, fam: String) -> StyleBoxTexture:
	var sizes: Dictionary = data().get("sizes", {})
	var m := int((sizes.get(part, [0, 8]) as Array)[1])
	var sb := StyleBoxTexture.new()
	sb.texture = texture(fam, part)
	sb.set_texture_margin_all(m)
	sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	sb.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	return sb


## Rounded to whole internal pixels (the board's edges on the picture's pixel grid).
static func _snap(r: Rect2) -> Rect2:
	var p := r.position.floor()
	return Rect2(p, (r.end.ceil() - p))


## The surface and the lip (internal pixels).
func _draw_board(c: CanvasItem, isz: Vector2, fam: String) -> void:
	var panel := texture(fam, "panel")
	if panel != null:
		c.draw_texture_rect(panel, Rect2(Vector2.ZERO, isz.ceil()), true)
	else:
		c.draw_rect(Rect2(Vector2.ZERO, isz.ceil()), Color(0.075, 0.067, 0.12))
	var trim := texture(fam, "trim")
	if trim != null:
		c.draw_texture_rect(trim, Rect2(0, 0, ceilf(isz.x), trim.get_height()), true)


## The plates, the wells, the display's bezel and the club's knobs (internal pixels; `rects` in the pad view's pixels).
func _draw_fittings(c: CanvasItem, size: Vector2, rects: Dictionary, fam: String, k: float) -> void:
	var ki := 1.0 / k
	if texture(fam, "plate") != null:
		var sb := _nine("plate", fam)
		for pair in [[rects[1], rects[2]], [rects[3], rects[4]]]:
			var bank := (pair[0] as Rect2).merge(pair[1]).grow((pair[0] as Rect2).size.x * 0.11)
			c.draw_style_box(sb, _snap(Rect2(bank.position * ki, bank.size * ki)))
	if texture(fam, "well") != null:
		var sw := _nine("well", fam)
		for pad in rects:
			var r: Rect2 = rects[pad]
			var w := r.grow(4.0 * k)
			c.draw_style_box(sw, _snap(Rect2(w.position * ki, w.size * ki)))
	var lcd := display_rect(rects, size)
	if lcd.size.x >= 80.0 and texture(fam, "bezel") != null:
		var g := lcd.grow(3.0 + 5.0 * k)
		c.draw_style_box(_nine("bezel", fam), _snap(Rect2(g.position * ki, g.size * ki)))
	var knob := texture(fam, "knob")
	if knob != null and bool(skin_of(fam).get("knobs", false)) and lcd.size.x >= 120.0:
		var n := 6
		var y := (lcd.end.y + (size.y - lcd.end.y) * 0.5) * ki - knob.get_height() * 0.5
		for i in n:
			var x := (lcd.position.x + lcd.size.x * (float(i) + 0.5) / float(n)) * ki - knob.get_width() * 0.5
			c.draw_texture(knob, Vector2(x, y).round())


func draw_under(ci: CanvasItem, size: Vector2, rects: Dictionary, now: float) -> void:
	var fam := family(ci)
	_sync_layer(ci, size, rects, fam)
	var rot := 0.0 if reduced else _beats(now) * 0.35
	for pn in _platters:
		(pn as Node2D).rotation = rot
	if _live != null and is_instance_valid(_live):
		_live_args = {"size": size, "rects": rects, "now": now, "fam": fam, "k": scale_of(ci)}
		_live.queue_redraw()


## The lamps (one per beat of the bar, the current one lit) above the display and the two level meters beside it (internal pixels).
func _draw_live(c: CanvasItem) -> void:
	if _live_args.is_empty():
		return
	var size: Vector2 = _live_args["size"]
	var rects: Dictionary = _live_args["rects"]
	var now: float = _live_args["now"]
	var fam: String = _live_args["fam"]
	var k: float = _live_args["k"]
	var ki := 1.0 / k
	var lcd := display_rect(rects, size)
	if lcd.size.x < 80.0:
		return
	var b := _beats(now)
	var lamp := texture(fam, "lamp")
	if lamp != null:
		var l := float(lamp.get_height())
		var trim_h := float(texture(fam, "trim").get_height()) if texture(fam, "trim") != null else 6.0
		var top := lcd.position.y * ki - 3.0 - 5.0 - l - 2.0
		top = maxf(top, trim_h + 2.0)
		var cx := lcd.get_center().x * ki
		var beat := int(floor(b)) % 4 if now >= 0.0 else -1
		var glow := 0.85 if reduced else exp(-3.0 * (b - floor(b)))
		for i in 4:
			var p := Vector2(roundf(cx + (float(i) - 1.5) * (l + 4.0) - l * 0.5), roundf(top))
			c.draw_texture_rect_region(lamp, Rect2(p, Vector2(l, l)), Rect2(0, 0, l, l))
			if i == beat:
				c.draw_texture_rect_region(lamp, Rect2(p, Vector2(l, l)), Rect2(l, 0, l, l), Color(1, 1, 1, 0.35 + 0.65 * glow))
	var e := clampf(run.crowd.energy / 100.0, 0.0, 1.0) if run != null and run.crowd != null else 0.5
	var r2: Rect2 = rects[2]
	var r3: Rect2 = rects[3]
	var h := size.y * 0.5 * ki
	var xl := (r2.end.x + r2.size.x * 0.11) * ki + 2.0
	var xr := (r3.position.x - r3.size.x * 0.11) * ki - 6.0
	var y0 := (r2.position.y + r2.size.y * 0.1) * ki
	var sk := skin_of(fam)
	var vu: Array = sk.get("vu", ["#3ae0a0", "#ffcc40", "#ff5068"])
	for x in [xl, xr]:
		_draw_vu(c, Vector2(roundf(x), roundf(y0)), h, b, e, x, vu, color_of(sk, "ink", Color(0.07, 0.07, 0.12)))


func _draw_vu(c: CanvasItem, at: Vector2, h: float, b: float, e: float, seed_x: float, vu: Array, ink: Color) -> void:
	var segs := 10
	var kp := 0.5 if reduced else exp(-6.0 * (b - floor(b)))  # peaks on every beat, decays before the next one
	var wob := 0.5 if reduced else 0.5 + 0.5 * sin(b * PI * 0.5 + seed_x * 0.13)
	var lit := int(clampf((0.2 + 0.8 * e) * (0.45 + 0.4 * kp + 0.15 * wob) * float(segs) + 0.5, 0.0, float(segs)))
	var sh := floorf(h / float(segs))
	c.draw_rect(Rect2(at - Vector2(1, 1), Vector2(6, sh * segs + 1)), ink)
	for i in segs:
		var col := Color.html(str(vu[0 if i < 6 else (1 if i < 8 else 2)]))
		var rr := Rect2(at.x, at.y + sh * float(segs - 1 - i), 4.0, sh - 1.0)
		c.draw_rect(rr, Color(col, 0.95) if i < lit else col.darkened(0.75))


func draw_over(_ci: CanvasItem, _size: Vector2, _rects: Dictionary, _now: float) -> void:
	pass  # the skinned pads (StoryPadView) light themselves
