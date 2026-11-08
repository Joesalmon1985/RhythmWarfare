class_name RunActivityInput
extends Control
## The input layer an activity owns while it is seated (CONTRACTS.md 4 and 5, hook H5.4), drawn over the run scene by RunMinigameHost:
## - kind "controls" (replace mode: the cloakroom, the bar): the activity's 2 or 4 large buttons stand in the pad strip, where the pads were (4: the pads'
##   own rects; 2: the left pair and the right pair). The pads and the note lane are hidden meanwhile and the lane input is off.
## - kind "regions" (overlay mode: the race): the four screen regions of the stage area (top, bottom, left, right; ContractShapes.regions), apart from the pads.
## Pure presentation and hit-testing: it never takes a touch itself (mouse_filter ignore); RunPlay's tap dispatcher asks `hit`.
##
## The controls' morph (CONTRACTS.md 10, ruling 38): the controls are drawn by the pads themselves, in the pads' own frame (StoryPadView `slot_fn` = `slot`): the same
## well, rubber face, rim and lit/unlit look, the control's pictogram in place of the pad's glyph and no words. Over the last beat before `t_in` (the seat) the pad's glyph
## cross-fades into the pictogram with a short scale pulse (and for two controls each pair of pads grows into one wide slot); over the first beat after `t_out` (the strip
## handed back, a lead-in before the resume boundary) it goes back. All of it from song time (`now_fn`), so the strip never jumps and never shows nothing. While the layer
## stands before `t_in` or after `t_out` the pads still own the taps (`owning` false: the host's owns_strip). A pad view without `slot_fn` gets plain boxes with pictograms.

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
var specs: Array = []  # the activity's control dicts, left to right ({id, label, pictogram?, icon?, shape?, color?, lit?, draw?: Callable(ci, rect, alpha)})
var now_fn := Callable()  # () -> song time
var beat_s := 60.0 / 174.0
var t_in := -INF  # the boundary the controls take the strip on (the seat): fully controls from here
var t_out := INF  # the boundary the pads take it back on: fully pads one beat after
var owning := false  # the controls own the strip's taps now (the host: MinigameController.owns_strip)
var pad_view: Control = null  # the pads (a StoryPadView draws the controls in its slots)
var _pressed := {}  # id -> wall time of the last press (a short flash)

const MORPH_BEATS := 1.0
const PULSE := 0.07  # the scale pulse's peak (7 %) at the middle of a morph


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


## How far the strip is the controls' at song time `t`: 0 pads, 1 controls; the morph in over the beat before t_in, out over the beat after t_out.
func mix_at(t: float) -> float:
	var b := maxf(beat_s * MORPH_BEATS, 1.0e-3)
	if t >= t_out:
		return 1.0 - _ease(clampf((t - t_out) / b, 0.0, 1.0))
	return _ease(clampf((t - (t_in - b)) / b, 0.0, 1.0))


## The scale pulse at `t`: 1 outside the morphs, up to 1 + PULSE in their middle.
func pulse_at(t: float) -> float:
	var b := maxf(beat_s * MORPH_BEATS, 1.0e-3)
	var u := -1.0
	if t >= t_in - b and t < t_in:
		u = (t - (t_in - b)) / b
	elif t >= t_out and t < t_out + b:
		u = (t - t_out) / b
	return 1.0 + PULSE * sin(PI * u) if u >= 0.0 else 1.0


static func _ease(u: float) -> float:
	return u * u * (3.0 - 2.0 * u)


## The control index that stands in pad `pad`'s slot (-1 none) and whether the pad is the slot's primary one (the one that draws the pictogram): 4 controls one each,
## 2 controls one per pair (pads 1 and 3 primary).
func control_of(pad: int) -> Array:
	var n := ids.size()
	if n == 4:
		return [pad - 1, true]
	if n == 2:
		return [0 if pad <= 2 else 1, pad == 1 or pad == 3]
	return [-1, false]


## StoryPadView.slot_fn: what pad `pad`'s slot shows at song time `now` ({}: the pad as it is). `r` is the pad's rect in the pad view's coordinates.
func slot(pad: int, r: Rect2, now: float) -> Dictionary:
	var ci := control_of(pad)
	if int(ci[0]) < 0 or kind != "controls":
		return {}
	var m := mix_at(now)
	if m <= 0.0:
		return {}
	var k := int(ci[0])
	var spec: Dictionary = specs[k] if k < specs.size() and typeof(specs[k]) == TYPE_DICTIONARY else {"id": str(ids[k])}
	var out := {"mix": m, "scale": pulse_at(now), "lit": bool(spec.get("lit", true)), "down": now_wall() - float(_pressed.get(str(spec.get("id", "")), -10.0)) < PRESS_FLASH_S}
	if spec.has("color"):
		out["color"] = Color.from_string(str(spec["color"]), Color.WHITE) if typeof(spec["color"]) == TYPE_STRING else spec["color"]
	else:
		out["color"] = CONTROL_COL
	if ids.size() == 2 and pad_view != null and pad_view.has_method("_pad_rects"):
		var pr: Dictionary = pad_view.call("_pad_rects")
		var first := 1 if pad <= 2 else 3
		var wide: Rect2 = (pr[first] as Rect2).merge(pr[first + 1])
		out["rect"] = Rect2(r.position.lerp(wide.position, m), r.size.lerp(wide.size, m))
		if not bool(ci[1]) and m >= 0.999:
			return {"skip": true}  # (the pair is one slot now: the primary pad draws it)
	if bool(ci[1]):
		out["glyph"] = func(c: CanvasItem, face: Rect2, a: float, base: Color, lit: bool) -> void: draw_pictogram(c, spec, face, a, base, lit)
	return out


const CONTROL_COL := Color(0.78, 0.74, 1.0)  # a control's light when the activity gives it no colour


func now_wall() -> float:
	return Time.get_ticks_msec() / 1000.0


## Whether the pad view draws the controls (a StoryPadView with `slot_fn`): then this layer draws nothing itself.
func drawn_by_pads() -> bool:
	return pad_view != null and "slot_fn" in pad_view


## A control's pictogram in `face` (the slot's face rect, in the pad view's coordinates) at alpha `a` (ControlPictograms.draw): the control's own `draw` callable, a texture `icon`,
## a built-in silhouette (`pictogram`, else `shape`), else its `label` as a last resort (an activity should give a pictogram: no words in the strip).
static func draw_pictogram(ci: CanvasItem, spec: Dictionary, face: Rect2, a: float, base: Color, lit: bool) -> void:
	if ControlPictograms.draw(ci, spec, face, a, base, lit):
		return
	var label := str(spec.get("label", ""))
	if label == "":
		return
	var font := ThemeDB.fallback_font
	var fs := int(clampf(face.size.y * 0.24, 12.0, 40.0))
	var tw := font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	ci.draw_string(font, face.get_center() + Vector2(-tw * 0.5, fs * 0.35), label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(base.lightened(0.5), a))


func _draw() -> void:
	if kind == "controls" and drawn_by_pads():
		return  # (the pads draw the controls in their own slots: slot)
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
		var spec: Dictionary = specs[i] if i < specs.size() and typeof(specs[i]) == TYPE_DICTIONARY else {"id": id}
		draw_pictogram(self, spec, r.grow(-3.0), 1.0, EDGE, true)
