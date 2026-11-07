class_name StoryDynamicThings
extends Node2D
## An activity's things in the room (CONTRACTS.md 10, ruling 38, hook H8.1): the coats on the rail, the glass on the counter, the knob on the deck. Unlike the map's things
## (StoryWorld: 3D billboards fixed at their authored place), these are given by the activity every frame and may move (`at`) and change frame (`frame`) in song time.
## They stand in the crowd's overlay inside the low-res viewport, drawn the way the crowd's figures and occluders are: projected through the same camera
## (StoryProjector, the pinhole the 3D world renders with), culled by the sector visibility the crowd uses, lit by their sector's song-time light times the lamps
## around them (the light a person standing there gets, as the card table's players are lit), faded into the fog with depth, and z-sorted with the crowd by distance
## (`sort_items`, merged by StoryStage._order_crowds), so a customer in front of the counter stands in front of the coat and one behind it behind.
##
## A thing: {id, sprite, at: [x, z], sector, size: [w_m, h_m], frame, y?, anchor?, grid?}
##   sprite   a sheet under assets/story/<map art>/sprites/<sprite>.png (or a res:// path); rows are states, columns frames
##   frame    int (row-major cell index) or [row, col]
##   size     metres on the ground's scale: the cell is drawn w_m wide and h_m tall wherever it stands
##   y        metres above the sector's floor (default 0): the thing's bottom edge, or its centre with anchor "center"
##   anchor   "bottom" (default: the feet, `y` is the bottom edge) | "center" (`y` is the centre)
##   grid     [cols, rows] of the sheet. Without it the sheet's sidecar <sprite>.json {"grid": [cols, rows]} (or {"cols", "rows"}) is read; without that the grid is
##            inferred: the row count whose cells' aspect is nearest the thing's `size` aspect, fewer rows on a tie (say the grid when a sheet is ambiguous)
## Pure presentation: the activity owns every value; this node only draws what it was last given.

const SPRITES_DIR := "res://assets/story/%s/sprites/%s.png"
const GAIN := 1.3  # the people's light, as their shader takes it (as RunCardTable)
const MIN_LIGHT := 0.55
const MAX_LIGHT := 1.12
const FOG_M := Vector2(5.5, 17.0)  # the crowd's depth fog (StoryCrowd.fog_m)
const MAX_ROWS := 8

var map: StoryMap
var assets: StoryAssets
var light_fn := Callable()  # (sector id, ground position, song: bool) -> Color: StoryStage._figure_light (null: white)
var fog_color := Color(0.03, 0.02, 0.08)
var high_contrast := false
var things: Array = []  # the normalized list last set (see set_things)
var sort_items: Array = []  # [[key: int, node: CanvasItem], ...] far to near, visible things only (the crowd's key: (4000000 - depth mm))
var drawn := 0  # things drawn last frame
var errors: Array = []  # sheets that could not be loaded (one line each, once)

var _nodes: Dictionary = {}  # id -> _Thing node
var _sheets: Dictionary = {}  # sprite -> {tex, grid: Vector2i (cols, rows) or ZERO when not known}
var _pose: Dictionary = {}
var _view := Vector2(480, 170)
var _vis: Dictionary = {}


## One drawn thing: a cell of its sheet in a rect (feet-origin coordinates), modulated by the light.
class _Thing extends Node2D:
	var tex: Texture2D
	var region := Rect2()
	var rect := Rect2()
	var col := Color.WHITE
	var depth := 0.0

	func _draw() -> void:
		if tex != null and region.size.x > 0.0:
			draw_texture_rect_region(tex, rect, region, col)


## The activity's things now (replaces the last list). Items without an id, a sprite or a size are dropped; `at` and `size` may be arrays or Vector2s.
func set_things(arr: Array) -> void:
	var out: Array = []
	var seen := {}
	for v: Variant in arr:
		if typeof(v) != TYPE_DICTIONARY:
			continue
		var d: Dictionary = v
		var id := str(d.get("id", ""))
		if id == "" or seen.has(id) or str(d.get("sprite", "")) == "":
			continue
		var at: Variant = _vec2(d.get("at", null))
		var sz: Variant = _vec2(d.get("size", null))
		if at == null or sz == null or (sz as Vector2).x <= 0.0 or (sz as Vector2).y <= 0.0:
			continue
		seen[id] = true
		var n := {"id": id, "sprite": str(d["sprite"]), "at": at, "sector": str(d.get("sector", "")), "size": sz, "frame": d.get("frame", 0),
			"y": float(d.get("y", 0.0)), "anchor": str(d.get("anchor", "bottom")), "grid": d.get("grid", null)}
		if n["sector"] == "" and map != null:
			n["sector"] = map.sector_at(at)
		out.append(n)
	things = out
	for id: String in _nodes.keys():
		if not seen.has(id):
			(_nodes[id] as Node).queue_free()
			_nodes.erase(id)
	for n: Dictionary in things:
		if not _nodes.has(n["id"]):
			var node := _Thing.new()
			node.name = "Thing_" + str(n["id"])
			node.visible = false
			add_child(node)
			_nodes[n["id"]] = node


static func _vec2(v: Variant) -> Variant:
	if v is Vector2:
		return v
	if typeof(v) == TYPE_ARRAY and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return null


## The camera this frame (the crowd's pose: {cam, yaw, pitch}), the low-res view size and the sector visibility (StoryMap.visible_sectors, the crowd's depth).
func set_camera(pose: Dictionary, size: Vector2, vis: Dictionary) -> void:
	_pose = pose
	_view = size
	_vis = vis


## Projects and lights every thing for song time `t` (call after set_camera and after the world's light for the frame is known).
func update(_t: float) -> void:
	sort_items = []
	drawn = 0
	var keyed: Array = []
	var nodes: Array = []
	for n: Dictionary in things:
		var node: _Thing = _nodes[n["id"]]
		var pl := placement(n)
		node.visible = not pl.is_empty()
		if pl.is_empty():
			continue
		var sh := sheet(str(n["sprite"]))
		node.tex = sh["tex"]
		node.region = cell_region(sh, n)
		node.position = pl["feet"]
		node.rect = Rect2(-(pl["w"] as float) * 0.5, -(pl["h"] as float) - float(pl["lift"]), pl["w"], pl["h"])
		node.depth = float(pl["depth"])
		node.col = _light(n, float(pl["depth"]))
		node.queue_redraw()
		drawn += 1
		nodes.append(node)
		keyed.append((4000000 - int(clampf(node.depth, 0.0, 3999.0) * 1000.0)) << 10 | (nodes.size() - 1))
	keyed.sort()
	for k: int in keyed:
		sort_items.append([k >> 10, nodes[k & 1023]])


## Where thing `n` stands on screen now: {feet: Vector2 (the ground point under it), lift: px from the feet to the bottom edge, w, h (px), depth, rect: Rect2 (low-res px)}, or {} when it
## is not drawn (no camera, its sector is not visible, behind the eye, off screen or its sheet is missing).
## `need_sheet` false: any box {at, sector, size, y, anchor} (a map thing's, StoryWorld.thing_screen_rect).
func placement(n: Dictionary, need_sheet := true) -> Dictionary:
	if _pose.is_empty() or map == null:
		return {}
	var sec := str(n["sector"])
	if not _vis.is_empty() and not _vis.has(sec):
		return {}
	if need_sheet and sheet(str(n["sprite"]))["tex"] == null:
		return {}
	var at: Vector2 = n["at"]
	var floor_y := float(map.sector(sec).get("floor", 0.0)) if sec != "" else 0.0
	var pr := StoryProjector.project_ground(at.x, at.y, floor_y, _pose, _view)
	if float(pr["depth"]) < StoryProjector.NEAR:
		return {}
	var ppm := float(pr["scale"])
	var sz: Vector2 = n["size"]
	var w := sz.x * ppm
	var h := sz.y * ppm
	var bottom := float(n["y"]) - (sz.y * 0.5 if str(n["anchor"]) == "center" else 0.0)
	var lift := bottom * ppm
	var feet: Vector2 = pr["screen"]
	var r := Rect2(feet.x - w * 0.5, feet.y - lift - h, w, h)
	if r.end.x < 0.0 or r.position.x > _view.x or r.end.y < 0.0 or r.position.y > _view.y:
		return {}
	return {"feet": feet, "lift": lift, "w": w, "h": h, "depth": float(pr["depth"]), "rect": r}


## The thing's screen rect (low-res viewport pixels) or null when it is not drawn.
func screen_rect(id: String) -> Variant:
	var n := thing(id)
	if n.is_empty():
		return null
	var pl := placement(n)
	return pl["rect"] if not pl.is_empty() else null


## The thing's anchor on screen (low-res viewport pixels): the centre of its drawn rect; null when it is not drawn.
func screen_point(id: String) -> Variant:
	var r: Variant = screen_rect(id)
	return (r as Rect2).get_center() if r != null else null


func thing(id: String) -> Dictionary:
	for n: Dictionary in things:
		if str(n["id"]) == id:
			return n
	return {}


func node_of(id: String) -> Node2D:
	return _nodes.get(id, null)


## The sheet of `sprite`: {tex: Texture2D or null, grid: Vector2i (ZERO: unknown, inferred per thing), path}. Loaded once. An unimported PNG is read from disk.
func sheet(sprite: String) -> Dictionary:
	if _sheets.has(sprite):
		return _sheets[sprite]
	var path := sprite if sprite.begins_with("res://") else SPRITES_DIR % [map.art if map != null else "", sprite]
	var tex: Texture2D = null
	if ResourceLoader.exists(path):
		tex = load(path) as Texture2D
	elif FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img != null:
			tex = ImageTexture.create_from_image(img)
	if tex == null and assets != null:  # (a sprite of the chapter's manifest)
		tex = assets.sprite(sprite).get("tex", null)
	if tex == null:
		errors.append("dynamic thing sheet %s not found (%s)" % [sprite, path])
	var grid := Vector2i.ZERO
	var meta := path.get_basename() + ".json"
	if FileAccess.file_exists(meta):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(meta))
		if typeof(d) == TYPE_DICTIONARY:
			var g: Variant = (d as Dictionary).get("grid", [d.get("cols", 0), d.get("rows", 0)])
			if typeof(g) == TYPE_ARRAY and (g as Array).size() == 2 and int(g[0]) > 0 and int(g[1]) > 0:
				grid = Vector2i(int(g[0]), int(g[1]))
	_sheets[sprite] = {"tex": tex, "grid": grid, "path": path}
	return _sheets[sprite]


## The grid of a sheet for thing `n`: the thing's own `grid`, else the sidecar's, else inferred from the thing's aspect (grid_for).
static func grid_of(sh: Dictionary, n: Dictionary) -> Vector2i:
	var g: Variant = n.get("grid", null)
	if typeof(g) == TYPE_ARRAY and (g as Array).size() == 2 and int(g[0]) > 0 and int(g[1]) > 0:
		return Vector2i(int(g[0]), int(g[1]))
	if (sh["grid"] as Vector2i) != Vector2i.ZERO:
		return sh["grid"]
	var tex: Texture2D = sh["tex"]
	if tex == null:
		return Vector2i.ONE
	var sz: Vector2 = n["size"]
	var key := snappedf(sz.x / sz.y, 0.001)
	var memo: Dictionary = sh.get("inferred", {})
	if not memo.has(key):
		memo[key] = grid_for(Vector2i(tex.get_width(), tex.get_height()), sz.x / sz.y)
		sh["inferred"] = memo
	return memo[key]


## The grid [cols, rows] of a sheet of `px` pixels whose cells are about `aspect` (w / h): for each row count that divides the height, the column count that divides the
## width with the cell aspect nearest `aspect`; the best of those, fewer rows on a tie.
static func grid_for(px: Vector2i, aspect: float) -> Vector2i:
	var best := Vector2i.ONE
	var best_err := INF
	for rows in range(1, MAX_ROWS + 1):
		if px.y % rows != 0:
			continue
		var ch := float(px.y) / float(rows)
		for cols in range(1, maxi(px.x, 1) + 1):
			if px.x % cols != 0:
				continue
			var cw := float(px.x) / float(cols)
			if cw < 4.0:
				break
			var err := absf(log((cw / ch) / maxf(aspect, 1.0e-3)))
			if err < best_err - 1.0e-6:
				best_err = err
				best = Vector2i(cols, rows)
	return best


## The sheet rect of thing `n`'s frame (an int, row-major, or [row, col]; out of range wraps).
static func cell_region(sh: Dictionary, n: Dictionary) -> Rect2:
	var tex: Texture2D = sh["tex"]
	if tex == null:
		return Rect2()
	var g := grid_of(sh, n)
	var cw := float(tex.get_width()) / float(g.x)
	var ch := float(tex.get_height()) / float(g.y)
	var f: Variant = n.get("frame", 0)
	var row := 0
	var col := 0
	if typeof(f) == TYPE_ARRAY and (f as Array).size() >= 2:
		row = posmod(int(f[0]), g.y)
		col = posmod(int(f[1]), g.x)
	else:
		var i := posmod(int(f), g.x * g.y)
		row = i / g.x
		col = i % g.x
	return Rect2(col * cw, row * ch, cw, ch)


## The light on thing `n` at `depth`: the sector's song-time light times the lamps around it, at the people's gain, clamped as the people are; faded toward the fog with depth.
func _light(n: Dictionary, depth: float) -> Color:
	var l := Color.WHITE
	if light_fn.is_valid():
		var sec := str(n["sector"])
		var at: Vector2 = n["at"]
		l = (light_fn.call(sec, at, true) as Color) * (light_fn.call(sec, at, false) as Color) * GAIN
		var lo := 0.8 if high_contrast else MIN_LIGHT
		l = Color(clampf(l.r, lo, MAX_LIGHT), clampf(l.g, lo, MAX_LIGHT), clampf(l.b, lo, MAX_LIGHT), 1.0)
	var fog := clampf((depth - FOG_M.x) / (FOG_M.y - FOG_M.x), 0.0, 1.0) * 0.7
	return Color(lerpf(l.r, fog_color.r, fog), lerpf(l.g, fog_color.g, fog), lerpf(l.b, fog_color.b, fog), 1.0)
