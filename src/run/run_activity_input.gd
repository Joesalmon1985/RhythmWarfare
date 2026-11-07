class_name RunActivityInput
extends Control
## The input layer an activity owns while it is seated (CONTRACTS.md 4 and 5, hook H5.4), drawn over the run scene by RunMinigameHost:
## - kind "controls" (replace mode: the cloakroom, the bar): the activity's 2 or 4 large buttons stand in the pad strip, where the pads were (4: the pads'
##   own rects; 2: the left pair and the right pair). The pads and the note lane are hidden meanwhile and the lane input is off.
## - kind "regions" (overlay mode: the race): the four screen regions of the stage area (top, bottom, left, right; ContractShapes.regions), apart from the pads.
## Pure presentation and hit-testing: it never takes a touch itself (mouse_filter ignore); RunPlay's tap dispatcher asks `hit`.

const FILL := Color(0.10, 0.10, 0.14, 0.92)
const EDGE := Color(0.85, 0.85, 0.95, 0.9)
const PRESSED := Color(0.35, 0.35, 0.5, 0.95)
const REGION_EDGE := Color(1.0, 1.0, 1.0, 0.10)
const PRESS_FLASH_S := 0.15

var kind := "controls"  # "controls" | "regions"
var ids: Array = []  # the control ids (left to right) or the region names
var labels: Array = []
var rects_fn: Callable  # () -> Array[Rect2] in viewport coordinates, one per id (asked every draw and every hit: the strip follows a resize)
var show_regions := false  # draw the regions' faint outlines (dev text on); the controls are always drawn
var _pressed := {}  # id -> wall time of the last press (a short flash)


## One rect per control in the pad strip: 4 controls take the pads' rects, 2 the left pair and the right pair, any other count splits the strip's span evenly.
static func control_rects(pad_rects: Dictionary, n: int) -> Array:
	var out: Array = []
	if pad_rects.is_empty() or n <= 0:
		return out
	var r: Array = []
	for p in [1, 2, 3, 4]:
		if pad_rects.has(p):
			r.append(pad_rects[p])
	if r.size() == 4 and n == 4:
		return r
	if r.size() == 4 and n == 2:
		return [(r[0] as Rect2).merge(r[1]), (r[2] as Rect2).merge(r[3])]
	var span: Rect2 = r[0]
	for x: Rect2 in r:
		span = span.merge(x)
	var w := span.size.x / float(n)
	for i in n:
		out.append(Rect2(span.position.x + w * float(i), span.position.y, w, span.size.y).grow_individual(-4.0, 0.0, -4.0, 0.0))
	return out


## The four regions as viewport rects of the stage area `stage` (Rect2 in viewport coordinates), in ContractShapes.REGIONS order.
static func region_rects(regions: Dictionary, stage: Rect2) -> Array:
	var out: Array = []
	for k in ContractShapes.REGIONS:
		var f: Array = regions.get(k, [0.0, 0.0, 0.0, 0.0])
		out.append(Rect2(stage.position + Vector2(float(f[0]), float(f[1])) * stage.size, Vector2(float(f[2]), float(f[3])) * stage.size))
	return out


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func rects() -> Array:
	return rects_fn.call() if rects_fn.is_valid() else []


## The id under `pos` (viewport coordinates), "" for none.
func hit(pos: Vector2) -> String:
	var rs := rects()
	for i in mini(rs.size(), ids.size()):
		if (rs[i] as Rect2).has_point(pos):
			return str(ids[i])
	return ""


func flash(id: String) -> void:
	_pressed[id] = Time.get_ticks_msec() / 1000.0
	queue_redraw()


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	var rs := rects()
	var inv := get_global_transform_with_canvas().affine_inverse()
	var font := ThemeDB.fallback_font
	var now := Time.get_ticks_msec() / 1000.0
	for i in mini(rs.size(), ids.size()):
		var g: Rect2 = rs[i]
		var r := Rect2(inv * g.position, g.size * inv.get_scale())
		if kind == "regions":
			if show_regions:
				draw_rect(r, REGION_EDGE, false, 2.0)
				draw_string(font, r.position + Vector2(8, 20), str(ids[i]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, REGION_EDGE * 3.0)
			continue
		var id := str(ids[i])
		var hot := now - float(_pressed.get(id, -10.0)) < PRESS_FLASH_S
		draw_rect(r.grow(-3.0), PRESSED if hot else FILL, true)
		draw_rect(r.grow(-3.0), EDGE, false, 3.0)
		var label := str(labels[i]) if i < labels.size() else id
		var fs := int(clampf(r.size.y * 0.28, 14.0, 48.0))
		var tw := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		draw_string(font, r.get_center() + Vector2(-tw * 0.5, fs * 0.35), label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, EDGE)
