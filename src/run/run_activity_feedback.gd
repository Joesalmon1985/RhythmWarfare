class_name RunActivityFeedback
extends Control
## In-world feedback for an activity (CONTRACTS.md 10, ruling 38): a tick, a cross or a glow drawn at a thing's screen point inside the stage's low-res viewport (so it
## pixelates like the room), by the host (RunMinigameHost.feedback), never by the activity. Song time drives everything: a tick pops and fades over one beat, a cross
## shakes and fades over one beat, a glow swells and fades over GLOW_BEATS (one and a half). No text. Besides the controls strip this is the only canvas drawing an
## activity may rely on.
##
## `entries`: [{thing, kind, t}]; `point_fn(thing) -> Vector2 | null` gives the low-res point (StoryWorld.thing_screen_point); `size_fn(thing) -> float` the thing's drawn
## height in low-res pixels (0 unknown: a default size). An entry whose thing is not on screen is not drawn but still runs out on time.

const KINDS := ["tick", "cross", "glow"]
const TICK_BEATS := 1.0
const CROSS_BEATS := 1.0
const GLOW_BEATS := 1.5
const TICK_COL := Color(0.45, 1.0, 0.55)
const CROSS_COL := Color(1.0, 0.32, 0.3)
const GLOW_COL := Color(1.0, 0.9, 0.55)
const INK := Color(0.04, 0.03, 0.08)

var entries: Array = []
var now_fn := Callable()  # () -> song time
var beat_s := 60.0 / 174.0
var reduced := false
var point_fn := Callable()
var size_fn := Callable()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


static func beats_of(kind: String) -> float:
	match kind:
		"tick":
			return TICK_BEATS
		"cross":
			return CROSS_BEATS
		"glow":
			return GLOW_BEATS
	return 0.0


## The look of a `kind` cue `age_beats` after it began: {alpha, scale, dx (the shake, in units of the mark's size), radius (glow, in units of its size)}; {} once it is over
## (or before it starts, or for an unknown kind). Pure: the tests read it.
static func look(kind: String, age_beats: float, p_reduced := false) -> Dictionary:
	var dur := beats_of(kind)
	if dur <= 0.0 or age_beats < 0.0 or age_beats >= dur:
		return {}
	var u := age_beats / dur
	match kind:
		"tick":  # a pop: overshoot in the first fifth, then settle, then fade over the second half
			var pop := 0.6 + 0.55 * sin(clampf(u / 0.2, 0.0, 1.0) * PI * 0.5) - 0.15 * clampf((u - 0.2) / 0.15, 0.0, 1.0)
			return {"alpha": 1.0 - clampf((u - 0.5) / 0.5, 0.0, 1.0), "scale": 1.0 if p_reduced else pop, "dx": 0.0, "radius": 0.0}
		"cross":  # a shake that dies away, then a fade
			var sh := 0.0 if p_reduced else sin(u * TAU * 4.0) * 0.18 * (1.0 - u)
			return {"alpha": 1.0 - clampf((u - 0.55) / 0.45, 0.0, 1.0), "scale": 1.0, "dx": sh, "radius": 0.0}
		"glow":  # a swell to full then a fade
			var sw := sin(clampf(u / 0.4, 0.0, 1.0) * PI * 0.5)
			return {"alpha": (1.0 - clampf((u - 0.4) / 0.6, 0.0, 1.0)) * 0.75, "scale": 1.0, "dx": 0.0, "radius": 0.6 + 0.6 * sw}
	return {}


## Drops the entries that have run out by song time `t`.
func prune(t: float) -> void:
	entries = entries.filter(func(e: Dictionary) -> bool: return t < float(e["t"]) + beats_of(str(e["kind"])) * beat_s)


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	var t: float = now_fn.call() if now_fn.is_valid() else 0.0
	for e: Dictionary in entries:
		var lk := look(str(e["kind"]), (t - float(e["t"])) / maxf(beat_s, 1.0e-3), reduced)
		if lk.is_empty():
			continue
		var p: Variant = point_fn.call(str(e["thing"])) if point_fn.is_valid() else null
		if p == null:
			continue
		var h: float = float(size_fn.call(str(e["thing"]))) if size_fn.is_valid() else 0.0
		var s := clampf(h * 0.45 if h > 0.0 else 10.0, 6.0, 28.0)  # the mark's size in low-res pixels
		draw_mark(self, str(e["kind"]), (p as Vector2).round(), s, lk)


## Draws one mark of `kind` at `c` (low-res pixels), size `s`, with look `lk` (look()): blocky pixel strokes on a dark outline, or a dithered glow.
static func draw_mark(ci: CanvasItem, kind: String, c: Vector2, s: float, lk: Dictionary) -> void:
	var a := float(lk["alpha"])
	var k := float(lk["scale"]) * s
	var o := c + Vector2(float(lk["dx"]) * s, 0.0)
	match kind:
		"tick":
			var pts := [o + Vector2(-0.5, 0.0) * k, o + Vector2(-0.15, 0.35) * k, o + Vector2(0.55, -0.4) * k]
			_stroke(ci, pts, maxf(2.0, roundf(k * 0.16)), Color(TICK_COL, a))
		"cross":
			_stroke(ci, [o + Vector2(-0.4, -0.4) * k, o + Vector2(0.4, 0.4) * k], maxf(2.0, roundf(k * 0.16)), Color(CROSS_COL, a))
			_stroke(ci, [o + Vector2(0.4, -0.4) * k, o + Vector2(-0.4, 0.4) * k], maxf(2.0, roundf(k * 0.16)), Color(CROSS_COL, a))
		"glow":
			var r := float(lk["radius"]) * s * 1.6
			var cell := 2.0
			var n := int(ceilf(r / cell))
			for iy in range(-n, n + 1):
				for ix in range(-n, n + 1):
					var d := Vector2(ix, iy).length() * cell / maxf(r, 1.0)
					if d > 1.0:
						continue
					var dith := float(((ix + iy * 3) % 4 + 4) % 4) / 4.0  # an ordered dither on the falloff: pixel art, no smooth gradient
					var w := (1.0 - d) * 1.3
					if w < dith * 0.6:
						continue
					ci.draw_rect(Rect2(o + Vector2(ix, iy) * cell - Vector2(cell, cell) * 0.5, Vector2(cell, cell)), Color(GLOW_COL, a * clampf(w, 0.0, 1.0)))


## A blocky polyline: square pixels stamped along each segment, an ink outline first.
static func _stroke(ci: CanvasItem, pts: Array, w: float, col: Color) -> void:
	for pass_i in 2:
		var ww := w + (2.0 if pass_i == 0 else 0.0)
		var cc := Color(INK, col.a * 0.9) if pass_i == 0 else col
		for i in pts.size() - 1:
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			var steps := maxi(int(ceilf(a.distance_to(b))), 1)
			for k in steps + 1:
				var p := a.lerp(b, float(k) / float(steps)).round()
				ci.draw_rect(Rect2(p - Vector2(ww, ww) * 0.5, Vector2(ww, ww)), cc)
