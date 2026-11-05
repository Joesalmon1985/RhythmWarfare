class_name BlackjackPeople
extends RefCounted
## The blackjack drawing kit, part two: three expressive people seen from across the table (a parametric face, gaze, twelve arm gestures) and the player's own hands entering from the
## bottom edge, in the house look (see `LOOKS`): no dark outlines, each material in two or three tones stepped by ordered dithering, the lamp as the key light and the room's spill as a rim,
## all built from whole-pixel rect rows and triangle lists (see `BlackjackDraw`), sized from `u = canvas height / 230`.
##
## Coordinates: a person is drawn around `center`, the middle of the head (`BlackjackDraw.seat_pos`). The head is about 38 u tall, the shoulders 64 u wide and the torso is cut 52 u
## below the head centre where the table's far edge hides it. Draw order for a scene: room, `draw_exit`, every person with `layer = "body"`, the table, then every person with `layer = "arms"`
## (arms and hands lie on the table). `layer = "all"` draws everything at once, for galleries and simple callers.

const PEOPLE := ["npc_a", "dealer", "npc_b"]
const MOOD_NAMES := ["neutral", "happy", "laugh", "surprised", "annoyed", "sad", "wince", "concerned", "smug", "thinking"]
const GESTURES := ["rest", "invite", "point_deck", "point_hand", "deal", "sweep", "pay", "shrug", "clap", "facepalm", "tap_table", "wave_off"]
const PLAYER_GESTURES := ["none", "pockets", "lay_money", "push_bet", "reach_deck", "cover_cards", "drop_cards", "empty_pockets", "gather_money"]
const GAZE_TARGETS := ["player", "deck", "own_cards", "dealer", "npc_a", "npc_b", "pile", "bet", "away"]
## The keys every mood table has.
const FACE_KEYS := [
	"brow_l", "brow_r", "lid_l", "lid_r", "crescent", "pupil", "mouth_curve", "mouth_open", "mouth_w", "mouth_x", "mouth_skew", "teeth", "grit",
	"blush", "sweat", "tear", "head_tilt", "head_bob", "pull", "gaze_bias", "gaze_lock",
]

## One parameter set per mood. `brow_*` is Vector2(height -1..1, tilt -1..1) with tilt positive when the inner end is raised (sad, worried) and negative when it is lowered (angry);
## `lid_*` is how open the eye is (0 shut, 1 open, up to 1.4 for wide); `crescent` turns a shut eye into a happy arc; `pupil` scales the pupils; `mouth_curve` -1 frown to 1 smile;
## `mouth_open` 0..1; `mouth_w` scales the width; `mouth_x` shifts it sideways in u; `mouth_skew` raises one corner (positive: the right one on screen); `teeth` shows the top teeth in an open mouth;
## `grit` draws a gritted teeth bar; `blush`, `sweat`, `tear` 0..1 extras; `head_tilt` degrees; `head_bob` extra bounce in u; `pull` pulls the head back in u; `gaze_bias` is a look direction that
## replaces the gaze by `gaze_lock` (0..1) so the eyes can look up and aside.
const MOODS := {
	"neutral": {
		"brow_l": Vector2(0.0, 0.0), "brow_r": Vector2(0.0, 0.0), "lid_l": 0.9, "lid_r": 0.9, "crescent": 0.0, "pupil": 1.0, "mouth_curve": 0.05, "mouth_open": 0.0, "mouth_w": 1.0,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 0.0, "tear": 0.0, "head_tilt": 0.0, "head_bob": 0.0, "pull": 0.0,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"happy": {
		"brow_l": Vector2(0.5, 0.3), "brow_r": Vector2(0.5, 0.3), "lid_l": 0.85, "lid_r": 0.85, "crescent": 0.0, "pupil": 1.15, "mouth_curve": 1.0, "mouth_open": 0.4, "mouth_w": 1.15,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 1.0, "grit": 0.0, "blush": 0.8, "sweat": 0.0, "tear": 0.0, "head_tilt": -3.0, "head_bob": 0.8, "pull": 0.0,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"laugh": {
		"brow_l": Vector2(0.6, 0.4), "brow_r": Vector2(0.6, 0.4), "lid_l": 0.0, "lid_r": 0.0, "crescent": 1.0, "pupil": 1.0, "mouth_curve": 1.0, "mouth_open": 1.0, "mouth_w": 1.3,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 1.0, "grit": 0.0, "blush": 1.0, "sweat": 0.0, "tear": 0.0, "head_tilt": 4.0, "head_bob": 2.2, "pull": 1.0,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"surprised": {
		"brow_l": Vector2(1.0, 0.1), "brow_r": Vector2(1.0, 0.1), "lid_l": 1.4, "lid_r": 1.4, "crescent": 0.0, "pupil": 0.55, "mouth_curve": 0.0, "mouth_open": 0.85, "mouth_w": 0.4,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 0.0, "tear": 0.0, "head_tilt": 0.0, "head_bob": 0.0, "pull": 1.5,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"annoyed": {
		"brow_l": Vector2(-0.6, -1.0), "brow_r": Vector2(-0.6, -1.0), "lid_l": 0.55, "lid_r": 0.55, "crescent": 0.0, "pupil": 0.9, "mouth_curve": -0.35, "mouth_open": 0.0, "mouth_w": 0.9,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 0.0, "tear": 0.0, "head_tilt": 0.0, "head_bob": 0.0, "pull": 0.0,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"sad": {
		"brow_l": Vector2(0.15, 1.0), "brow_r": Vector2(0.15, 1.0), "lid_l": 0.65, "lid_r": 0.65, "crescent": 0.0, "pupil": 1.35, "mouth_curve": -1.0, "mouth_open": 0.0, "mouth_w": 0.8,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 0.0, "tear": 1.0, "head_tilt": 7.0, "head_bob": 0.0, "pull": -4.0,
		"gaze_bias": Vector2(0.0, 0.7), "gaze_lock": 0.7,
	},
	"wince": {
		"brow_l": Vector2(-0.4, -0.9), "brow_r": Vector2(0.2, -0.3), "lid_l": 0.0, "lid_r": 0.7, "crescent": 0.0, "pupil": 0.8, "mouth_curve": -0.2, "mouth_open": 0.0, "mouth_w": 1.15,
		"mouth_x": 0.0, "mouth_skew": 0.0, "teeth": 0.0, "grit": 1.0, "blush": 0.0, "sweat": 1.0, "tear": 0.0, "head_tilt": -6.0, "head_bob": 0.0, "pull": 3.0,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"concerned": {
		"brow_l": Vector2(0.9, 1.0), "brow_r": Vector2(0.9, 1.0), "lid_l": 1.2, "lid_r": 1.2, "crescent": 0.0, "pupil": 0.8, "mouth_curve": -0.8, "mouth_open": 0.0, "mouth_w": 0.95,
		"mouth_x": 0.0, "mouth_skew": -0.6, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 1.0, "tear": 0.0, "head_tilt": 7.0, "head_bob": 0.0, "pull": 1.0,
		"gaze_bias": Vector2.ZERO, "gaze_lock": 0.0,
	},
	"smug": {
		"brow_l": Vector2(1.0, 0.6), "brow_r": Vector2(-0.5, -0.6), "lid_l": 0.42, "lid_r": 0.42, "crescent": 0.0, "pupil": 1.0, "mouth_curve": 0.9, "mouth_open": 0.0, "mouth_w": 1.1,
		"mouth_x": 2.0, "mouth_skew": 1.4, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 0.0, "tear": 0.0, "head_tilt": -8.0, "head_bob": 0.0, "pull": 2.0,
		"gaze_bias": Vector2(0.9, 0.2), "gaze_lock": 0.6,
	},
	"thinking": {
		"brow_l": Vector2(0.9, 0.5), "brow_r": Vector2(-0.1, 0.0), "lid_l": 0.95, "lid_r": 0.95, "crescent": 0.0, "pupil": 1.0, "mouth_curve": -0.15, "mouth_open": 0.0, "mouth_w": 0.55,
		"mouth_x": 5.5, "mouth_skew": -1.0, "teeth": 0.0, "grit": 0.0, "blush": 0.0, "sweat": 0.0, "tear": 0.0, "head_tilt": 6.0, "head_bob": 0.0, "pull": 0.0,
		"gaze_bias": Vector2(-0.8, -0.9), "gaze_lock": 1.0,
	},
}

## Palettes and looks: the three are residents of the Ward seen close, in the house style (real proportions, a head about a third of the shoulders' width, no outlines, every material in
## three or four steps). `lx` is the side the lamp lights them from (+1 from screen right, -1 from screen left, 0 from above); `rim` the side the room's coloured spill catches
## (-1 left, magenta; +1 right, teal; 0 both, faintly). `hw`/`hh` the head's half width and half height in u.
const LOOKS := {
	"dealer": {
		"skin_light": Color("e6b28c"), "skin": Color("cc9673"), "skin_shade": Color("a06a53"), "skin_deep": Color("6c4034"), "lip": Color("b0705e"), "lip_dark": Color("6e3a32"),
		"hair": Color("4a3020"), "hair_light": Color("6e4a30"), "hair_shade": Color("2c1c14"), "brow": Color("3a2416"), "iris": Color("3e2a1c"),
		"cloth_light": Color("ece6d4"), "cloth": Color("cfc9b8"), "cloth_shade": Color("9c9a98"), "cloth_dark": Color("63666e"),
		"accent": Color("a3323a"), "accent_dark": Color("651c24"), "accent_light": Color("c85a58"),
		"hw": 11.0, "hh": 15.0, "lx": 0.0, "rim": 0, "forearm_skin": true,
	},
	"npc_a": {
		"skin_light": Color("eec6aa"), "skin": Color("d8a88c"), "skin_shade": Color("ad7c68"), "skin_deep": Color("774c44"), "lip": Color("b46c68"), "lip_dark": Color("7a3e40"),
		"hair": Color("cdcad4"), "hair_light": Color("f0eef2"), "hair_shade": Color("8e8a9e"), "brow": Color("a29eae"), "iris": Color("4c5c6c"),
		"cloth_light": Color("d6b058"), "cloth": Color("b08a3c"), "cloth_shade": Color("80622a"), "cloth_dark": Color("4e3a1a"),
		"accent": Color("e2d8c0"), "accent_dark": Color("a89c84"), "accent_light": Color("f2ead6"), "frame": Color("c0a468"),
		"hw": 10.5, "hh": 14.5, "lx": 1.0, "rim": -1, "forearm_skin": false,
	},
	"npc_b": {
		"skin_light": Color("aa7550"), "skin": Color("8a5638"), "skin_shade": Color("663c27"), "skin_deep": Color("44261b"), "lip": Color("7a3c3e"), "lip_dark": Color("40181e"),
		"hair": Color("3c2c5e"), "hair_light": Color("634c8e"), "hair_shade": Color("22193a"), "brow": Color("1c1430"), "iris": Color("2a1810"),
		"cloth_light": Color("d58498"), "cloth": Color("b25c76"), "cloth_shade": Color("843e58"), "cloth_dark": Color("56243c"),
		"accent": Color("5a88cc"), "accent_dark": Color("2c4a80"), "accent_light": Color("a8c8f0"), "gold": Color("d0a440"), "clip": Color("d8508a"),
		"hw": 10.5, "hh": 14.5, "lx": -1.0, "rim": 1, "forearm_skin": false,
	},
}

const INK := BlackjackDraw.INK
const SCLERA := Color("e2dccc")
const MOUTH_IN := Color("3a1820")
const TEETH := Color("e6dfcc")
const TONGUE := Color("b04a58")
const BLUSH := Color("d86a78")
const SWEAT := Color("9ad0e8")
const WHITE := Color("f4f0e6")
const GLOVE_SKIN := Color("c48e6a")
const GLOVE_LIGHT := Color("dcaa84")
const GLOVE_SHADE := Color("9a6a4e")
const GLOVE_DEEP := Color("6a4434")
const SLEEVE := Color("3a4262")
const SLEEVE_LIGHT := Color("566088")
const SLEEVE_DARK := Color("262b44")
const SLEEVE_DEEP := Color("181b2e")
const CUFF := Color("d8d0bc")
const CUFF_SHADE := Color("a8a090")
const LINING := Color("c8c6cc")

const ARM_L := 28.0
const HAND_K := 1.2  # a hand's drawing scale on the people (life size against their heads)
const LOW_U := 0.75  # below this unit (the 320 x 115 canvas) faces switch to their bolder low-detail drawing


# ------------------------------------------------------------------ moods

## The parameter set of `mood` (unknown names give `neutral`). The returned dictionary is a shared constant: do not modify it, use `blend`.
static func face_params(mood: String) -> Dictionary:
	var m: Variant = MOODS.get(mood)
	if m == null:
		return MOODS["neutral"]
	return m


## The parameters `w` of the way from `a` to `b` (both full parameter sets; `w` 0..1). Numbers and Vector2s are interpolated.
static func blend(a: Dictionary, b: Dictionary, w: float) -> Dictionary:
	var out := {}
	for k: String in a:
		var va: Variant = a[k]
		var vb: Variant = b.get(k, va)
		if va is Vector2 and vb is Vector2:
			out[k] = (va as Vector2).lerp(vb as Vector2, w)
		elif (va is float or va is int) and (vb is float or vb is int):
			out[k] = lerpf(float(va), float(vb), w)
		else:
			out[k] = va if w < 0.5 else vb
	return out


## The canvas point to look at for a gaze target id (`player`, `deck`, `own_cards`, `dealer`, `npc_a`, `npc_b`, `pile`, `bet`, `away`) from person `from_who`.
## `player` is just below the head so the pupils sit centred and a little low: eye contact. `away` looks off to the side.
static func gaze_point(target: String, from_who: String, size: Vector2) -> Vector2:
	var from := BlackjackDraw.seat_pos(from_who, size)
	var u := BlackjackDraw.unit(size)
	match target:
		"player":
			return from + Vector2(0.0, 8.0 * u)
		"deck":
			return BlackjackDraw.deck_spot(size)
		"own_cards":
			return BlackjackDraw.card_spot(from_who, 0, size)
		"dealer", "npc_a", "npc_b":
			return BlackjackDraw.seat_pos(target, size) + Vector2(0.0, 4.0 * u)
		"pile":
			return BlackjackDraw.pile_origin(size) + Vector2(40.0 * u, -20.0 * u)
		"bet":
			return BlackjackDraw.bet_spot(size)
	return from + Vector2((-60.0 if from.x > size.x * 0.5 else 60.0) * u, -18.0 * u)


# ------------------------------------------------------------------ small helpers

static func _p(v: float, u: float) -> float:
	return roundf(v * u)


static func _smooth(x: float) -> float:
	var c := clampf(x, 0.0, 1.0)
	return c * c * (3.0 - 2.0 * c)


## 0 before `a`, rising to 1 at `b`, holding until `c`, falling to 0 at `d`.
static func _trap(t: float, a: float, b: float, c: float, d: float) -> float:
	if t <= a or t >= d:
		return 0.0
	if t < b:
		return _smooth((t - a) / (b - a))
	if t <= c:
		return 1.0
	return 1.0 - _smooth((t - c) / (d - c))


static func _blink(beat: float, seed_v: float) -> float:
	var ph := fposmod(beat * 0.9 + seed_v, 6.1)
	return 1.0 if ph < 0.12 else 0.0


# ------------------------------------------------------------------ the person

## Draws person `who` (`npc_a`, `dealer`, `npc_b`) around `center` (the middle of the head). `face` is a parameter set from `face_params` / `blend`; `gaze_to` the canvas point the eyes look at;
## `gesture` one of `GESTURES` with `gesture_t` 0..1 (see the per-gesture notes below); `beat_phase` continuous beats (bob, blinks); `point_to` the canvas point a pointing, inviting, dealing, sweeping
## or paying gesture goes to (zero: a sensible default). `layer` is `"all"`, `"body"` (head and torso, draw before the table) or `"arms"` (draw after it); `"torso"` then `"head"` draw the body
## in two parts.
## Gesture timing (gesture_t): `rest`, `invite`, `tap_table`, `wave_off`, `clap` loop (2 cycles per unit for tap, wave, clap; 1 for invite); `point_deck`, `point_hand` jab 2 times per unit and hold;
## `deal`, `sweep`, `pay`, `shrug`, `facepalm` are one-shots. Suggested lengths in beats: invite 2, point 2, deal 1, sweep 2, pay 2, shrug 2, clap 2, facepalm 3, tap_table 1, wave_off 2.
static func draw_person(ci: CanvasItem, who: String, center: Vector2, u: float, face: Dictionary, gaze_to: Vector2, gesture: String, gesture_t: float, beat_phase: float, point_to := Vector2.ZERO, layer := "all") -> void:
	draw_person_state(ci, person_state(who, center, u, face, gaze_to, gesture, gesture_t, beat_phase, point_to, layer))


## What `draw_person` draws for `layer`, resolved from its arguments (same arguments; `layer` may also be `"torso"` or `"head"`, the two halves of `"body"`): the person's place and unit,
## for the torso the shrug's lift, for the head its motion, the face, the gaze point, the bob in whole pixels and the blink, for the arms the lift and the two arm poses. `draw_person_state`
## reads nothing else, so two equal states draw the same pixels: a caller may keep a drawn layer until the state changes (the beat moves a head only by whole pixels, a few times a beat, and
## a torso or resting arms not at all).
static func person_state(who: String, center: Vector2, u: float, face: Dictionary, gaze_to: Vector2, gesture: String, gesture_t: float, beat_phase: float, point_to := Vector2.ZERO, layer := "all") -> Dictionary:
	var g := gesture if GESTURES.has(gesture) else "rest"
	var c := Vector2(roundf(center.x), roundf(center.y))
	var lift := 0.0
	if g == "shrug":
		lift = _trap(gesture_t, 0.0, 0.2, 0.8, 1.0)
	var rel := Vector2.ZERO
	if point_to != Vector2.ZERO:
		rel = (point_to - c) / u
	var st := {"who": who, "c": c, "u": u}
	if layer != "head" and layer != "arms":
		st["torso_lift"] = lift
	if layer != "torso" and layer != "arms":
		st["head_motion"] = _head_motion(g, gesture_t, rel)
		st["face"] = face
		st["gaze"] = gaze_to
		st["bob"] = _bob(face, beat_phase, u)
		st["blink"] = _blink(beat_phase, _blink_seed(who))
	if layer == "all" or layer == "arms":
		st["arms_lift"] = lift
		st["poses"] = _poses(g, gesture_t, rel, lift, point_to != Vector2.ZERO)
	return st


## Draws a state from `person_state`: the torso, the head and the arms, as far as the state has them.
static func draw_person_state(ci: CanvasItem, st: Dictionary) -> void:
	var who: String = st["who"]
	var look: Dictionary = LOOKS.get(who, LOOKS["dealer"])
	var c: Vector2 = st["c"]
	var u: float = st["u"]
	if st.has("torso_lift"):
		_body(ci, who, c, u, look, st["torso_lift"])
	if st.has("face"):
		var hm: Vector3 = st["head_motion"]
		_head(ci, who, c + Vector2(roundf(hm.x * u), roundf(hm.y * u)), u, look, st["face"], st["gaze"], st["bob"], st["blink"], hm.z)
	if st.has("poses"):
		_arms(ci, who, c, u, look, st["poses"], st["arms_lift"])


# ------------------------------------------------------------------ body

const D_HALF := BlackjackDraw.D_HALF
const D_QUARTER := BlackjackDraw.D_QUARTER
const D_SPARSE := BlackjackDraw.D_SPARSE

static var _head_cache: Dictionary = {}  # [who, u] -> the head's and hair's shapes as triangle lists in head-local pixels (`_head_shapes`)


## A colour as the room's spill catches it on the `side` (-1 left magenta, +1 right teal) of a person.
static func _rimc(look: Dictionary, base: Color, side: int) -> Color:
	var spill := BlackjackDraw.SPILL_L if side < 0 else BlackjackDraw.SPILL_R
	return base.lerp(spill, 0.5 if int(look["rim"]) != 0 else 0.3).lightened(0.08)


static func _rim_sides(look: Dictionary) -> Array:
	var r := int(look["rim"])
	return [-1, 1] if r == 0 else [r]


## A one-pixel line from `a` to `b` (whole pixels, one rect per step along the longer axis).
static func _line(ci: CanvasItem, a: Vector2, b: Vector2, col: Color, px := 1.0) -> void:
	var d := b - a
	var n := int(maxf(absf(d.x), absf(d.y)) / px)
	for i in n + 1:
		var p := a + d * (float(i) / float(maxi(n, 1)))
		ci.draw_rect(Rect2(roundf(p.x), roundf(p.y), px, px), col)


## A one-pixel line (see `_line`) as a triangle list.
static func _line_tris(a: Vector2, b: Vector2, px := 1.0) -> PackedVector2Array:
	var out := PackedVector2Array()
	var d := b - a
	var n := int(maxf(absf(d.x), absf(d.y)) / px)
	for i in n + 1:
		var p := a + d * (float(i) / float(maxi(n, 1)))
		out.append_array(BlackjackDraw.rect_tris(roundf(p.x), roundf(p.y), px, px))
	return out


static func _body(ci: CanvasItem, who: String, c: Vector2, u: float, look: Dictionary, lift: float) -> void:
	var cloth: Color = look["cloth"]
	var light: Color = look["cloth_light"]
	var shade: Color = look["cloth_shade"]
	var dark: Color = look["cloth_dark"]
	var accent: Color = look["accent"]
	var lx := float(look["lx"])
	var lf := lift * 5.0
	var t := maxf(1.0, roundf(u))
	var bb := BlackjackDraw.Batch.new(ci)
	var pts := PackedVector2Array([
		c + Vector2(_p(-9.0, u), _p(15.0 - lf, u)), c + Vector2(_p(-21.0, u), _p(19.0 - lf, u)), c + Vector2(_p(-29.0, u), _p(27.0 - lf * 0.6, u)), c + Vector2(_p(-30.0, u), _p(53.0, u)),
		c + Vector2(_p(30.0, u), _p(53.0, u)), c + Vector2(_p(29.0, u), _p(27.0 - lf * 0.6, u)), c + Vector2(_p(21.0, u), _p(19.0 - lf, u)), c + Vector2(_p(9.0, u), _p(15.0 - lf, u)),
	])
	# the neck: in the chin's shadow at the top, lit down the lamp's side
	var nw := _p(4.5, u)
	var ny := c.y + _p(9.0, u)
	bb.add(BlackjackDraw.rect_tris(c.x - nw, ny, 2.0 * nw, _p(13.0, u)), look["skin_shade"])
	bb.add(BlackjackDraw.rect_tris(c.x - nw, ny, 2.0 * nw, _p(3.0, u)), look["skin_deep"])
	var lit_x := c.x - _p(1.5, u) if lx == 0.0 else (c.x + nw - _p(3.0, u) if lx > 0.0 else c.x - nw)
	bb.add(BlackjackDraw.rect_tris(lit_x, ny + _p(5.0, u), _p(3.0, u), _p(8.0, u)), look["skin"], D_HALF)
	# the room's coloured spill on the outer edge, then the cloth
	for sd: int in _rim_sides(look):
		bb.add(BlackjackDraw.tris_of(Transform2D(0.0, Vector2(float(sd) * t, 0.0)) * pts), _rimc(look, cloth, sd))
	bb.add(BlackjackDraw.tris_of(pts), cloth)
	if who == "npc_a":  # the knit of the cardigan
		bb.add(BlackjackDraw.tris_of(pts), shade, D_SPARSE)
	# the lamp from above lights the tops of the shoulders; the side away from it and the chest toward the table fall into shade: clean planes, a two-pixel dithered seam between them
	var top := c.y + _p(15.0 - lf, u)
	var seam := maxf(1.0, _p(2.0, u))
	_plane(bb, pts, c.x - _p(40.0, u), top - 4.0, _p(80.0, u), _p(5.0, u) + 4.0, light, 0, seam)
	var sides: Array = [-1.0, 1.0] if lx == 0.0 else [-lx]
	for sd: float in sides:
		var wide := _p(7.0 if lx != 0.0 else 4.0, u)
		var x0 := c.x + sd * _p(31.0, u)
		var xa := minf(x0, x0 - sd * wide)
		_plane(bb, pts, xa, top + _p(4.0, u), wide, _p(40.0, u), shade, int(sd), seam)
	_plane(bb, pts, c.x - _p(40.0, u), c.y + _p(45.0, u), _p(80.0, u), _p(10.0, u), shade, -2, seam)
	match who:
		"dealer":
			# an open collar: the throat in the shadow of the chin, the collar points lit, red braces over the shoulders with their shadow side
			var vee := PackedVector2Array([c + Vector2(_p(-6.0, u), _p(15.0 - lf, u)), c + Vector2(_p(6.0, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(25.0, u))])
			bb.add(BlackjackDraw.tris_of(vee), look["skin_shade"])
			bb.add(BlackjackDraw.tris_of(vee), look["skin"], D_HALF)
			for sx: float in [-1.0, 1.0]:
				var col := PackedVector2Array([c + Vector2(sx * _p(8.0, u), _p(14.0 - lf, u)), c + Vector2(sx * _p(1.0, u), _p(26.0, u)), c + Vector2(sx * _p(10.0, u), _p(24.0, u)), c + Vector2(sx * _p(13.0, u), _p(18.0 - lf, u))])
				bb.add(BlackjackDraw.tris_of(Transform2D(0.0, Vector2(0.0, t)) * col), shade)
				bb.add(BlackjackDraw.tris_of(col), look["cloth_light"])
				var bt := c + Vector2(sx * _p(16.0, u), _p(19.0 - lf, u))
				var bbot := c + Vector2(sx * _p(12.0, u), _p(53.0, u))
				bb.add_limb(bt + Vector2(-sx * t, 0.0), bbot + Vector2(-sx * t, 0.0), maxf(2.0, _p(3.6, u)), maxf(2.0, _p(3.6, u)), look["accent_dark"])
				bb.add_limb(bt, bbot, maxf(2.0, _p(3.0, u)), maxf(2.0, _p(3.0, u)), accent)
				bb.add(_line_tris(bt + Vector2(sx * t, 0.0), bt + Vector2(sx * t, _p(4.0, u)), t), look["accent_light"])
			# folds of the shirt under the arms
			for sx: float in [-1.0, 1.0]:
				bb.add(_line_tris(c + Vector2(sx * _p(27.0, u), _p(33.0, u)), c + Vector2(sx * _p(21.0, u), _p(40.0, u)), t), shade)
		"npc_a":
			# the cardigan open over a cream blouse, its ribbed front edges lit, three buttons
			var vee := PackedVector2Array([c + Vector2(_p(-8.0, u), _p(15.0 - lf, u)), c + Vector2(_p(8.0, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(36.0, u))])
			bb.add(BlackjackDraw.tris_of(vee), accent)
			bb.add(BlackjackDraw.clip_tris(BlackjackDraw.rect_points(c.x - _p(9.0, u), c.y + _p(26.0, u), _p(18.0, u), _p(12.0, u)), vee), look["accent_dark"], D_HALF)
			for sx: float in [-1.0, 1.0]:
				bb.add(BlackjackDraw.tris_of(PackedVector2Array([c + Vector2(sx * _p(5.0, u), _p(15.0 - lf, u)), c + Vector2(sx * _p(1.0, u), _p(19.0, u)), c + Vector2(sx * _p(3.0, u), _p(21.0, u)), c + Vector2(sx * _p(8.0, u), _p(16.0 - lf, u))])), look["accent_light"])
				bb.add(_line_tris(c + Vector2(sx * _p(9.0, u), _p(15.0 - lf, u)), c + Vector2(sx * _p(1.0, u), _p(52.0, u)), t), light)
				bb.add(_line_tris(c + Vector2(sx * _p(10.0, u), _p(15.0 - lf, u)), c + Vector2(sx * _p(2.0, u), _p(52.0, u)), t), shade)
			for i in 3:
				bb.add(BlackjackDraw.rect_tris(c.x + _p(3.0, u), c.y + _p(37.0 + 5.0 * i, u), maxf(1.0, _p(2.0, u)), maxf(1.0, _p(2.0, u))), dark)
		"npc_b":
			# a scoop neck: skin lit on the lamp's side, a fine gold chain and a blue pendant; drapery folds across the top
			var scoop := PackedVector2Array([c + Vector2(_p(-9.0, u), _p(15.0 - lf, u)), c + Vector2(_p(9.0, u), _p(15.0 - lf, u)), c + Vector2(_p(7.0, u), _p(22.0, u)), c + Vector2(0.0, _p(25.0, u)), c + Vector2(_p(-7.0, u), _p(22.0, u))])
			bb.add(BlackjackDraw.tris_of(scoop), look["skin"])
			bb.add(BlackjackDraw.clip_tris(BlackjackDraw.rect_points(c.x - _p(10.0, u), c.y + _p(14.0, u), _p(20.0, u), _p(4.0, u)), scoop), look["skin_shade"], D_HALF)
			bb.add(BlackjackDraw.clip_tris(BlackjackDraw.rect_points(c.x - _p(10.0, u), c.y + _p(15.0, u), _p(8.0, u), _p(10.0, u)), scoop), look["skin_light"], D_HALF)
			bb.add(_line_tris(c + Vector2(_p(-5.0, u), _p(16.0, u)), c + Vector2(0.0, _p(21.0, u)), t), look["gold"])
			bb.add(_line_tris(c + Vector2(_p(5.0, u), _p(16.0, u)), c + Vector2(0.0, _p(21.0, u)), t), look["gold"])
			bb.add(BlackjackDraw.rect_tris(c.x - t, c.y + _p(21.0, u), 2.0 * t, 2.0 * t), accent)
			bb.add(BlackjackDraw.rect_tris(c.x - t, c.y + _p(21.0, u), t, t), look["accent_light"])
			for sx: float in [-1.0, 1.0]:
				bb.add(_line_tris(c + Vector2(sx * _p(24.0, u), _p(31.0, u)), c + Vector2(sx * _p(9.0, u), _p(42.0, u)), t), shade)
				bb.add(_line_tris(c + Vector2(sx * _p(25.0, u), _p(38.0, u)), c + Vector2(sx * _p(13.0, u), _p(47.0, u)), t), shade)
	bb.flush()


## A plane of `col` over the part of polygon `pts` inside the rect (x, y, w, h), with a dithered seam `seam` pixels wide on its open side: `open` -2 the top, 0 the bottom,
## -1 the right (a plane on the left side), 1 the left (a plane on the right side).
static func _plane(bb: BlackjackDraw.Batch, pts: PackedVector2Array, x: float, y: float, w: float, h: float, col: Color, open: int, seam: float) -> void:
	bb.add(BlackjackDraw.clip_tris(BlackjackDraw.rect_points(x, y, w, h), pts), col)
	var r := Rect2()
	match open:
		0:
			r = Rect2(x, y + h, w, seam)
		-2:
			r = Rect2(x, y - seam, w, seam)
		-1:
			r = Rect2(x + w, y, seam, h)
		_:
			r = Rect2(x - seam, y, seam, h)
	bb.add(BlackjackDraw.clip_tris(BlackjackDraw.rect_points(r.position.x, r.position.y, r.size.x, r.size.y), pts), col, D_HALF)


# ------------------------------------------------------------------ head and face

## The head's bob on the beat in whole pixels (twice as fast in a laugh).
static func _bob(f: Dictionary, beat: float, u: float) -> float:
	var laugh := float(f.get("crescent", 0.0)) > 0.5
	var bob_amp := (0.9 + float(f.get("head_bob", 0.0))) * u
	var bph := beat * (2.0 if laugh else 1.0)
	return roundf(bob_amp * pow(0.5 + 0.5 * cos(TAU * bph), 2.0))


static func _blink_seed(who: String) -> float:
	return 0.0 if who == "dealer" else (2.3 if who == "npc_a" else 4.1)


## The head's outline `k` u in from its edge and moved by `off` u: a skull round on top, full cheeks, a jaw narrowing to the chin (head-local pixels).
static func _head_pts(hw: float, hh: float, u: float, k: float, off: Vector2) -> PackedVector2Array:
	var w := maxf(2.0, hw - k)
	var h := maxf(2.0, hh - k)
	var raw: Array = []
	for i in 13:
		var th := PI + PI * float(i) / 12.0
		raw.append(Vector2(cos(th) * w, -1.0 + sin(th) * (h - 1.0)))
	for q: Vector2 in [Vector2(1.0, 0.22), Vector2(0.93, 0.5), Vector2(0.76, 0.76), Vector2(0.45, 0.95), Vector2(0.0, 1.0), Vector2(-0.45, 0.95), Vector2(-0.76, 0.76), Vector2(-0.93, 0.5), Vector2(-1.0, 0.22)]:
		raw.append(Vector2(q.x * w, q.y * h))
	var out := PackedVector2Array()
	for p: Vector2 in raw:
		out.append(Vector2(roundf((p.x + off.x) * u), roundf((p.y + off.y) * u)))
	return out


## A curly mass: an ellipse whose edge is scalloped into `bumps` curls (head-local u, rounded to pixels).
static func _curls(cx: float, cy: float, rx: float, ry: float, bumps: int, amp: float, u: float, n := 54) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n:
		var th := TAU * float(i) / float(n)
		var r := 1.0 + amp * (absf(sin(th * float(bumps) * 0.5)) - 0.6)
		out.append(Vector2(roundf((cx + cos(th) * rx * r) * u), roundf((cy + sin(th) * ry * r) * u)))
	return out


static func _pts(raw: Array, u: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p: Vector2 in raw:
		out.append(Vector2(roundf(p.x * u), roundf(p.y * u)))
	return out


## The head and hair of `who` at unit `u` as triangle lists (head-local pixels), made once: the skin in four steps (shadow, a dithered step, the mid tone, a dithered step, the light,
## offset toward the lamp so the shadow lies on the far side and under the jaw), the hair behind and in front with its light and shade.
static func _head_shapes(who: String, look: Dictionary, u: float) -> Dictionary:
	var key := [who, u]
	var hit: Variant = _head_cache.get(key)
	if hit != null:
		return hit
	var hw := float(look["hw"])
	var hh := float(look["hh"])
	var lx := float(look["lx"])
	var d := {}
	d["head_pts"] = _head_pts(hw, hh, u, 0.0, Vector2.ZERO)
	d["head"] = BlackjackDraw.tris_of(d["head_pts"])
	d["head_e"] = BlackjackDraw.tris_of(_head_pts(hw, hh, u, 0.6, Vector2(lx * 0.6, -0.5)))
	d["head_mid"] = BlackjackDraw.tris_of(_head_pts(hw, hh, u, 1.4, Vector2(lx * 1.4, -1.0)))
	d["head_ld"] = BlackjackDraw.tris_of(_head_pts(hw, hh, u, 4.0, Vector2(lx * 2.6, -2.6)))
	d["head_lit"] = BlackjackDraw.tris_of(_head_pts(hw, hh, u, 6.5, Vector2(lx * 3.4, -4.0)))
	var back := PackedVector2Array()
	var front := PackedVector2Array()
	match who:
		"npc_b":  # a big mass of dark curls round the head, a curly fringe and locks down past the temples
			back = _curls(0.0, -3.0, hw + 6.5, hh + 1.5, 11, 0.12, u)
			front = _pts([
				Vector2(-hw - 2.5, -5.0), Vector2(-hw - 1.0, 4.0), Vector2(-hw + 0.5, 3.0), Vector2(-hw + 1.0, -4.0), Vector2(-hw + 2.5, -7.0), Vector2(-5.0, -9.0), Vector2(-3.0, -7.5),
				Vector2(-0.5, -10.0), Vector2(2.0, -8.0), Vector2(5.0, -9.5), Vector2(hw - 2.5, -7.0), Vector2(hw - 1.0, -4.0), Vector2(hw - 0.5, 3.0), Vector2(hw + 1.0, 4.0),
				Vector2(hw + 2.5, -5.0), Vector2(hw + 1.5, -11.0), Vector2(6.0, -hh - 2.5), Vector2(0.0, -hh - 3.5), Vector2(-6.0, -hh - 2.5), Vector2(-hw - 1.5, -11.0)], u)
		"npc_a":  # a short white perm: soft curls over the crown and puffed at the sides over the ears
			back = _curls(0.0, -4.0, hw + 2.5, hh - 0.5, 9, 0.14, u)
			front = _pts([
				Vector2(-hw - 2.0, -4.0), Vector2(-hw - 1.0, 3.0), Vector2(-hw + 0.5, 1.0), Vector2(-hw + 1.0, -5.0), Vector2(-6.0, -8.5), Vector2(-3.0, -9.5), Vector2(0.0, -8.5),
				Vector2(3.0, -9.5), Vector2(6.0, -8.5), Vector2(hw - 1.0, -5.0), Vector2(hw - 0.5, 1.0), Vector2(hw + 1.0, 3.0), Vector2(hw + 2.0, -4.0), Vector2(hw + 1.0, -11.0),
				Vector2(5.0, -hh - 1.5), Vector2(0.0, -hh - 2.0), Vector2(-5.0, -hh - 1.5), Vector2(-hw - 1.0, -11.0)], u)
		_:  # the dealer: short brown hair round the crown, sideburns, the visor over the forehead
			back = _head_pts(hw + 0.8, hh + 0.2, u, 0.0, Vector2(0.0, -1.0))
			front = _pts([
				Vector2(-hw - 0.8, -8.0), Vector2(-hw - 0.5, 1.0), Vector2(-hw + 1.0, 1.0), Vector2(-hw + 1.0, -8.0), Vector2(hw - 1.0, -8.0), Vector2(hw - 1.0, 1.0), Vector2(hw + 0.5, 1.0),
				Vector2(hw + 0.8, -8.0), Vector2(hw, -12.0), Vector2(5.0, -hh - 0.8), Vector2(0.0, -hh - 1.2), Vector2(-5.0, -hh - 0.8), Vector2(-hw, -12.0)], u)
	d["back_pts"] = back
	d["back"] = BlackjackDraw.tris_of(back)
	d["back_shade"] = BlackjackDraw.clip_tris(BlackjackDraw.rect_points(-40.0 * u, 2.0 * u, 80.0 * u, 40.0 * u), back)
	d["back_far"] = BlackjackDraw.clip_tris(BlackjackDraw.rect_points((-40.0 if lx >= 0.0 else 4.0) * u, -40.0 * u, (36.0 if lx >= 0.0 else 36.0) * u, 80.0 * u), back) if lx != 0.0 else PackedVector2Array()
	d["front"] = BlackjackDraw.tris_of(front)
	d["front_light"] = BlackjackDraw.clip_tris(BlackjackDraw.ell_points((lx * 4.0) * u, (-hh + 1.0) * u, 8.0 * u, 4.5 * u, 24), front)
	# everything under the face as recorded runs (the hair behind with its rim, shade and curls; the ears; the skin in clean planes with dithered seams), and the hair in front
	var t := maxf(1.0, roundf(u))
	var hair: Color = look["hair"]
	var b := BlackjackDraw.Batch.new()
	for sd: int in _rim_sides(look):
		b.add(Transform2D(0.0, Vector2(float(sd) * t, 0.0)) * (d["back"] as PackedVector2Array), _rimc(look, hair, sd))
	b.add(d["back"], hair)
	b.add(d["back_far"], look["hair_shade"], D_HALF)
	b.add(d["back_shade"], look["hair_shade"], D_HALF)
	if who != "dealer":
		b.add(d["back"], look["hair_light"], D_SPARSE)  # curls catching the light
	var hwp := _p(hw, u)
	for sx: float in [-1.0, 1.0]:
		var lit := lx * sx > 0.0
		b.add(BlackjackDraw.ell_tris(sx * hwp, _p(1.0, u), maxf(1.0, _p(1.6, u)), maxf(1.0, _p(3.0, u))), look["skin"] if lit else look["skin_shade"])
		b.add(BlackjackDraw.rect_tris(sx * hwp, 0.0, maxf(1.0, _p(1.0, u)), maxf(1.0, _p(2.0, u))), look["skin_deep"])
	for sd: int in _rim_sides(look):
		b.add(Transform2D(0.0, Vector2(float(sd) * t, 0.0)) * (d["head"] as PackedVector2Array), _rimc(look, look["skin_shade"], sd))
	b.add(d["head"], look["skin_shade"])
	b.add(d["head_mid"], look["skin"])
	b.add(d["head_lit"], look["skin_light"])
	var e_pts := _head_pts(hw, hh, u, 0.6, Vector2(lx * 0.6, -0.5))
	var mid_pts := _head_pts(hw, hh, u, 1.4, Vector2(lx * 1.4, -1.0))
	var ld_pts := _head_pts(hw, hh, u, 4.0, Vector2(lx * 2.6, -2.6))
	var lit_pts := _head_pts(hw, hh, u, 6.5, Vector2(lx * 3.4, -4.0))
	b.add(BlackjackDraw.ring_tris(e_pts, mid_pts), look["skin"], D_HALF)
	b.add(BlackjackDraw.ring_tris(ld_pts, lit_pts), look["skin_light"], D_HALF)
	b.flush()
	d["under"] = b.runs
	var f := BlackjackDraw.Batch.new()
	f.add(d["front"], hair)
	f.add(d["front_light"], look["hair_light"], D_HALF)
	if who != "dealer":
		f.add(d["front"], look["hair_light"], D_SPARSE)
	f.flush()
	d["over"] = f.runs
	if _head_cache.size() > 24:
		_head_cache.clear()
	_head_cache[key] = d
	return d


static func _head(ci: CanvasItem, who: String, c: Vector2, u: float, look: Dictionary, f: Dictionary, gaze_to: Vector2, bob: float, blink: float, tilt_add := 0.0) -> void:
	var hw := _p(float(look["hw"]), u)
	var t := maxf(1.0, roundf(u))
	var pull := roundf(float(f.get("pull", 0.0)) * u * 0.7)
	var origin := c + Vector2(0.0, bob - pull)
	var tilt := deg_to_rad(float(f.get("head_tilt", 0.0)) + tilt_add)
	var sh := _head_shapes(who, look, u)
	ci.draw_set_transform(origin, tilt, Vector2.ONE)
	BlackjackDraw.draw_runs(ci, sh["under"])
	_face_features(ci, who, u, look, f, origin, tilt, gaze_to, blink)
	BlackjackDraw.draw_runs(ci, sh["over"])
	match who:
		"dealer":
			_visor(ci, u, float(look["hw"]), float(look["hh"]))
		"npc_b":
			# a gold hoop in the ear on the left, a pink clip in the curls
			var ex := -hw - _p(0.5, u)
			var ey := _p(4.0, u)
			var g: Color = look["gold"]
			BlackjackDraw.rect(ci, ex - t, ey, t, _p(3.0, u), g)
			BlackjackDraw.rect(ci, ex + t, ey, t, _p(3.0, u), g.darkened(0.3))
			BlackjackDraw.rect(ci, ex - t, ey + _p(3.0, u), 3.0 * t, t, g.darkened(0.15))
			BlackjackDraw.rect(ci, _p(-6.0, u), _p(-float(look["hh"]) - 1.0, u), _p(3.0, u), maxf(1.0, _p(2.0, u)), look["clip"])
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


## The dealer's green celluloid visor: the band round the forehead, the brim, and the green-tinted shade it throws on the brow.
static func _visor(ci: CanvasItem, u: float, hw: float, hh: float) -> void:
	var t := maxf(1.0, roundf(u))
	var green := Color("3f8a55")
	var green_lit := Color("7cbf88")
	var green_dark := Color("22513a")
	BlackjackDraw.dither_fill(ci, BlackjackDraw.rect_tris(_p(-hw + 1.0, u), _p(-5.0, u), _p(2.0 * hw - 2.0, u), _p(3.0, u)), green_dark, D_HALF)
	var band := _pts([Vector2(-hw - 1.0, -11.5), Vector2(hw + 1.0, -11.5), Vector2(hw + 1.0, -8.0), Vector2(-hw - 1.0, -8.0)], u)
	BlackjackDraw.poly(ci, band, green)
	BlackjackDraw.rect(ci, _p(-hw - 1.0, u), _p(-11.5, u), _p(2.0 * hw + 2.0, u), t, green_lit)
	var brim := _pts([Vector2(-hw - 4.0, -8.0), Vector2(hw + 4.0, -8.0), Vector2(hw + 2.0, -5.0), Vector2(-hw - 2.0, -5.0)], u)
	BlackjackDraw.poly(ci, brim, green_dark)
	BlackjackDraw.rect(ci, _p(-hw - 4.0, u), _p(-8.0, u), _p(2.0 * hw + 8.0, u), t, green)
	BlackjackDraw.dither_fill(ci, BlackjackDraw.rect_tris(_p(-hw - 3.0, u), _p(-8.0, u) + t, _p(2.0 * hw + 6.0, u), t), green_lit, D_HALF)


## Eyes, brows, nose, mouth and extras: small pixel features in the head's local space (origin at the head centre), as the room's people have them, only closer.
static func _face_features(ci: CanvasItem, who: String, u: float, look: Dictionary, f: Dictionary, origin: Vector2, tilt: float, gaze_to: Vector2, blink: float) -> void:
	var px := maxf(1.0, roundf(u))
	var low := u < LOW_U
	var ex := maxf(2.0, _p(4.5, u))
	var ew := maxf(2.0, _p(4.0, u))
	var ey := 0.0
	var lx := float(look["lx"])
	var glasses := who == "npc_a"
	var gl: Vector2 = f.get("gaze_bias", Vector2.ZERO)
	var lock := float(f.get("gaze_lock", 0.0))
	var crescent := float(f.get("crescent", 0.0))
	var pupil_s := float(f.get("pupil", 1.0))
	var rot := Transform2D(tilt, Vector2.ZERO)
	var lash: Color = (look["skin_deep"] as Color).lerp(Color("140c10"), 0.65)
	# the socket's shade under the brow (lit faces only show it on the far side of the nose)
	var bt := BlackjackDraw.Batch.new(ci)
	if not low:
		for sx: float in [-1.0, 1.0]:
			bt.add(BlackjackDraw.rect_tris(sx * ex - ew * 0.5, ey - 2.0 * px, ew, px), look["skin_shade"], D_HALF)
	# blush: a dithered flush on the cheeks
	var bl := float(f.get("blush", 0.0))
	if bl > 0.05:
		for sx: float in [-1.0, 1.0]:
			bt.add(BlackjackDraw.rect_tris(sx * (ex + px) - _p(2.5, u), ey + _p(3.0, u), maxf(2.0, _p(5.0, u)), maxf(1.0, _p(2.0, u))), BlackjackDraw.shade(BLUSH, clampf(bl, 0.0, 1.0)), D_HALF)
	bt.flush()
	# eyes
	for si in 2:
		var sx := -1.0 if si == 0 else 1.0
		var lid := float(f.get("lid_l" if si == 0 else "lid_r", 0.9))
		if blink > 0.5 and crescent < 0.5:
			lid = minf(lid, 0.0)
		var cx := sx * ex
		var world := origin + rot * Vector2(cx, ey)
		var dir := gaze_to - world
		var dl := dir.length()
		var dv := Vector2.ZERO
		if dl > 0.5:
			dv = dir / dl * minf(1.0, dl / maxf(1.0, 16.0 * u))
		dv = dv.lerp(gl, lock)
		_eye(ci, cx, ey, ew, lid, crescent, pupil_s, dv, u, sx, look, lash, low)
	if glasses:
		var fr: Color = look["frame"]
		if low:
			BlackjackDraw.rect(ci, -ex + ew * 0.5, ey - px, 2.0 * ex - ew, px, fr)
		else:
			for sx: float in [-1.0, 1.0]:
				var x0 := roundf(sx * ex - ew * 0.5) - px
				var w := ew + 2.0 * px
				BlackjackDraw.rect(ci, x0 + px, ey - 3.0 * px, w - 2.0 * px, px, fr)
				BlackjackDraw.rect(ci, x0 + px, ey + 2.0 * px, w - 2.0 * px, px, fr.darkened(0.25))
				BlackjackDraw.rect(ci, x0, ey - 2.0 * px, px, 4.0 * px, fr if sx * lx < 0.0 or lx == 0.0 else fr.darkened(0.2))
				BlackjackDraw.rect(ci, x0 + w - px, ey - 2.0 * px, px, 4.0 * px, fr.darkened(0.2) if sx * lx < 0.0 else fr)
				BlackjackDraw.rect(ci, x0 + (w - 2.0 * px if lx > 0.0 else px), ey - 2.0 * px, px, px, WHITE)  # a glint on the lens toward the lamp
			BlackjackDraw.rect(ci, -ex + ew * 0.5 + px, ey - 2.0 * px, 2.0 * ex - ew - 2.0 * px, px, fr)
	# brows: one-pixel strokes in the brow colour; height and tilt carry the mood (never less than a pixel of movement, so moods read at low detail)
	var ku := maxf(u, 0.8)
	for si in 2:
		var sx := -1.0 if si == 0 else 1.0
		var b: Vector2 = f.get("brow_l" if si == 0 else "brow_r", Vector2.ZERO)
		var by := ey - _p(3.5, u) - (px if glasses and not low else 0.0) - roundf(b.x * 1.6 * ku)
		var yi := by - roundf(b.y * 1.3 * ku)
		var yo := by + roundf(b.y * 0.6 * ku)
		var xi := sx * maxf(1.0, _p(1.5, u))
		var xo := sx * (ex + ew * 0.5 + (0.0 if low else px))
		_line(ci, Vector2(xi, yi), Vector2(xo, yo), look["brow"], px)
		if not low and absf(b.y) > 0.6:  # a knit brow gets a crease
			BlackjackDraw.rect(ci, sx * px - (px if sx < 0.0 else 0.0), yi + px, px, px, look["skin_shade"])
	# the nose: a lit bridge, its shadow side, the nostrils' row under a lit tip
	var sd := -1.0 if lx > 0.0 else 1.0
	var nt := ey + _p(4.0, u)
	if not low:
		BlackjackDraw.rect(ci, sd * px, ey + px, px, nt - ey, look["skin_shade"])
		BlackjackDraw.rect(ci, 0.0, ey + px, px, nt - ey - px, look["skin_light"])
		BlackjackDraw.rect(ci, -px, nt + px, 3.0 * px, px, look["skin_shade"])
		BlackjackDraw.rect(ci, -px, nt + px, px, px, look["skin_deep"])
		BlackjackDraw.rect(ci, px, nt + px, px, px, look["skin_deep"])
		BlackjackDraw.rect(ci, 0.0, nt, px, px, look["skin_light"])
	_mouth(ci, u, look, f, low)
	if who == "npc_a" and not low:  # age: lines from the nose to the mouth's corners, soft bags under the eyes
		for sx: float in [-1.0, 1.0]:
			BlackjackDraw.rect(ci, sx * _p(4.0, u) - (px if sx < 0.0 else 0.0), nt + 2.0 * px, px, 2.0 * px, look["skin_shade"])
	# extras
	if float(f.get("sweat", 0.0)) > 0.3:
		_drop(ci, Vector2(_p(float(look["hw"]) - 2.0, u), -_p(6.0, u)), u, px)
	if float(f.get("tear", 0.0)) > 0.3:
		for sx: float in [-1.0, 1.0]:
			var tx := roundf(sx * ex + sx * ew * 0.25)
			BlackjackDraw.rect(ci, tx, ey + 2.0 * px, px, _p(4.0, u), SWEAT)
			BlackjackDraw.rect(ci, tx, ey + 2.0 * px + _p(4.0, u), px, px, WHITE)


## A bead of sweat at the temple: three pixels of pale blue and a glint.
static func _drop(ci: CanvasItem, p: Vector2, u: float, px: float) -> void:
	var h := maxf(2.0, _p(3.0, u))
	BlackjackDraw.rect(ci, p.x, p.y + px, maxf(1.0, _p(2.0, u)), h, SWEAT)
	BlackjackDraw.rect(ci, p.x, p.y, px, px, SWEAT)
	BlackjackDraw.rect(ci, p.x, p.y + px, px, px, WHITE)


## One eye `ew` pixels wide centred on (cx, cy): the lid / lash line, one to three rows of white (from a heavy lid to wide open), a two-pixel iris that follows `dv` (-1..1), the lower lid
## of a wide eye. Shut: a lash line; shut in a laugh (`crescent`): an arc bowed upward.
static func _eye(ci: CanvasItem, cx: float, cy: float, ew: float, lid: float, crescent: float, pupil_s: float, dv: Vector2, u: float, side: float, look: Dictionary, lash: Color, low: bool) -> void:
	var px := maxf(1.0, roundf(u))
	var x0 := roundf(cx - ew * 0.5)
	var x1 := x0 + ew - px
	var y := roundf(cy)
	var outer := x1 + px if side > 0.0 else x0 - px
	if lid < 0.12:
		if crescent > 0.5:
			BlackjackDraw.rect(ci, x0, y, px, px, lash)
			BlackjackDraw.rect(ci, x1, y, px, px, lash)
			BlackjackDraw.rect(ci, x0 + px, y - px, maxf(px, ew - 2.0 * px), px, lash)
			if not low:
				BlackjackDraw.rect(ci, x0, y + px, ew, px, look["skin_light"])  # the cheeks pushed up by the smile
		else:
			BlackjackDraw.rect(ci, x0, y, ew, px, lash)
			if not low:
				BlackjackDraw.rect(ci, outer, y - px, px, px, lash)
		return
	var rows := 1 if lid < 0.7 else (2 if lid <= 1.15 else 3)
	if low:
		rows = 1 if lid <= 1.15 else 2
	var top := y - (px if rows == 3 else 0.0)
	var sclera: Color = SCLERA.lerp(look["skin"], 0.22)
	if not low:
		BlackjackDraw.rect(ci, x0, top, ew, rows * px, sclera)
		BlackjackDraw.rect(ci, (x1 if side > 0.0 else x0), top, px, rows * px, sclera.lerp(look["skin_shade"], 0.5))  # the white darker in the outer corner
	var iw := px if (low or pupil_s < 0.7 or ew < 4.0 * px) else 2.0 * px
	var ih := rows * px if rows < 3 else 2.0 * px
	var iy := top
	if rows == 3:
		iy = top + (px if dv.y > -0.3 else 0.0)
	elif rows == 2 and dv.y > 0.45:
		ih = px
		iy = top + px
	var ix := roundf(x0 + (ew - iw) * 0.5 + dv.x * (ew - iw) * 0.5)
	ix = clampf(ix, x0, x1 - iw + px)
	BlackjackDraw.rect(ci, ix, iy, iw, ih, lash if low else look["iris"])
	if not low and iw >= 2.0 * px and pupil_s >= 1.1:
		BlackjackDraw.rect(ci, ix + (iw - px if side < 0.0 else 0.0), iy, px, px, sclera.lightened(0.2))  # a bright catch light
	# the upper lid and lashes (heavier, and over the iris, on a drooping lid); a lower lid under a wide eye
	BlackjackDraw.rect(ci, minf(x0, outer) if not low else x0, top - px, ew + (0.0 if low else px), px, lash)
	if rows == 3 and not low:
		BlackjackDraw.rect(ci, x0, top + 3.0 * px, ew, px, look["skin_shade"])


## The mouth at low detail (a head eleven pixels wide): three to five pixels, so it reads as a mouth and never as a moustache. Closed: the lip line in the lips' colour, its corners up in
## a smile and down in a frown; a grin: a row of teeth over a dark pixel row narrower than it; an O: a two-by-two dark pixel block.
static func _mouth_low(ci: CanvasItem, look: Dictionary, cx: float, y0: float, mw: float, curve: float, skew: float, open: float, teeth: bool) -> void:
	var lipd: Color = look["lip_dark"]
	if open > 0.12 and curve > 0.25:
		BlackjackDraw.rect(ci, cx - mw, y0 - 1.0, 2.0 * mw + 1.0, 1.0, TEETH if teeth else lipd)
		BlackjackDraw.rect(ci, cx - mw + 1.0, y0, 2.0 * mw - 1.0, 1.0 if open < 0.7 else 2.0, MOUTH_IN)
		return
	if open > 0.12:
		BlackjackDraw.rect(ci, cx - 1.0, y0 - 1.0, 2.0, 2.0, MOUTH_IN)
		return
	var lip: Color = (look["lip"] as Color).lerp(lipd, 0.5)
	BlackjackDraw.rect(ci, cx - mw + 1.0, y0, 2.0 * mw - 1.0, 1.0, lip)
	var lc := 0.0 if absf(curve) < 0.3 else (-1.0 if curve > 0.0 else 1.0)
	var lsk := 0.0 if absf(skew) < 0.5 else -1.0
	BlackjackDraw.rect(ci, cx - mw, y0 + lc, 1.0, 1.0, lip)
	BlackjackDraw.rect(ci, cx + mw, y0 + lc + lsk, 1.0, 1.0, lip)


## The mouth: the dark line between the lips (curving up in a smile, down in a frown, skewed in a smirk) over a lit lower lip; open: a grin with the top teeth, or an O; gritted teeth.
static func _mouth(ci: CanvasItem, u: float, look: Dictionary, f: Dictionary, low: bool) -> void:
	var px := maxf(1.0, roundf(u))
	var mw := maxf(1.0, roundf(3.2 * u * float(f.get("mouth_w", 1.0))))
	var cx := roundf(float(f.get("mouth_x", 0.0)) * u * 0.55)
	var y0 := _p(8.5, u)
	var curve := float(f.get("mouth_curve", 0.0))
	var skew := float(f.get("mouth_skew", 0.0))
	var open := float(f.get("mouth_open", 0.0))
	var lipd: Color = look["lip_dark"]
	var lip: Color = look["lip"]
	if float(f.get("grit", 0.0)) > 0.5:
		var gh := 3.0 * px if not low else 2.0 * px
		BlackjackDraw.rect(ci, cx - mw - px, y0 - px, 2.0 * mw + 3.0 * px, gh, lipd)
		BlackjackDraw.rect(ci, cx - mw, y0 - (0.0 if low else 0.0), 2.0 * mw + px, px, TEETH)
		var x := cx - mw + px
		while x < cx + mw:
			BlackjackDraw.rect(ci, x, y0, px, px, TEETH.darkened(0.3))
			x += 2.0 * px
		return
	if low:
		_mouth_low(ci, look, cx, y0, mw, curve, skew, open, float(f.get("teeth", 0.0)) > 0.5 or float(f.get("grit", 0.0)) > 0.5)
		return
	if open > 0.12:
		var h := maxf(2.0 * px, roundf((1.0 + open * 4.0) * u))
		if curve > 0.25:  # a grin: flat on top with the top teeth, round below, the corners lifted
			var rows := int(h / px)
			for j in rows:
				var k := float(j) / float(rows)
				var hwj := roundf(mw * sqrt(maxf(0.0, 1.0 - k * k)))
				var col := MOUTH_IN
				if float(f.get("teeth", 0.0)) > 0.5 and j == 0 and not low:
					col = TEETH
				elif j == rows - 1 and rows >= 4:
					col = TONGUE
				BlackjackDraw.rect(ci, cx - hwj, y0 - px + j * px, 2.0 * hwj + px, px, col)
			BlackjackDraw.rect(ci, cx - mw - px, y0 - 2.0 * px, px, px, lipd)
			BlackjackDraw.rect(ci, cx + mw + px, y0 - 2.0 * px, px, px, lipd)
			if not low:
				BlackjackDraw.rect(ci, cx - roundf(mw * 0.5), y0 - px + h, 2.0 * roundf(mw * 0.5) + px, px, lip)
				BlackjackDraw.rect(ci, cx - mw - 2.0 * px, y0 - 2.0 * px, px, 2.0 * px, look["skin_shade"])  # the cheeks crease
				BlackjackDraw.rect(ci, cx + mw + 2.0 * px, y0 - 2.0 * px, px, 2.0 * px, look["skin_shade"])
		else:  # an O
			var rx := maxf(1.0, roundf(mw * 0.6))
			var ry := maxf(1.0, roundf(h * 0.5))
			BlackjackDraw.ell(ci, cx, y0 + ry * 0.3, rx + (0.0 if low else px), ry + (0.0 if low else px), lipd)
			BlackjackDraw.ell(ci, cx, y0 + ry * 0.3, maxf(0.0, rx - (px if low else 0.0)), maxf(0.0, ry - (px if low else 0.0)), MOUTH_IN)
		return
	var amp := maxf(1.7 * u, 1.0)
	var samp := maxf(1.6 * u, 1.0)
	var x := -mw
	while x <= mw:
		var tt := x / mw
		var side := tt * signf(skew) if skew != 0.0 else 1.0
		var cw := 1.0 if side >= 0.0 else 0.15
		var yy := y0 - curve * amp * tt * tt * cw - (skew * maxf(0.0, tt) * samp if skew > 0.0 else 0.0) + (skew * maxf(0.0, -tt) * samp if skew < 0.0 else 0.0)
		BlackjackDraw.rect(ci, cx + x, roundf(yy), px, px, lipd)
		x += px
	if not low:
		var lw := roundf(mw * (0.55 if curve > 0.5 else 0.7))
		BlackjackDraw.rect(ci, cx - lw, y0 + px, 2.0 * lw + px, px, lip)
		BlackjackDraw.rect(ci, cx - roundf(mw * 0.4), y0 + 2.0 * px, 2.0 * roundf(mw * 0.4) + px, px, look["skin_shade"])  # the shadow under the lower lip
		if curve > 0.6:
			BlackjackDraw.rect(ci, cx - mw - px, y0 - roundf(amp) - px, px, px, look["skin_shade"])
			BlackjackDraw.rect(ci, cx + mw + px, y0 - roundf(amp) - px, px, px, look["skin_shade"])


# ------------------------------------------------------------------ arms

static func _pose(h: Vector2, kind: String, ang: float, k := 1.0) -> Dictionary:
	return {"h": h, "kind": kind, "ang": ang, "k": k}


static func _mix(a: Dictionary, b: Dictionary, w: float) -> Dictionary:
	var ang := lerp_angle(float(a["ang"]), float(b["ang"]), w)
	return {"h": (a["h"] as Vector2).lerp(b["h"] as Vector2, w), "kind": b["kind"] if w > 0.4 else a["kind"], "ang": ang, "k": lerpf(float(a["k"]), float(b["k"]), w)}


## A pose along keyframes: `ts` rising times 0..1, `ps` the poses at them; eased (smoothstep) between neighbours, so every move starts and lands softly.
static func _keys(t: float, ts: Array, ps: Array) -> Dictionary:
	if t <= float(ts[0]):
		return ps[0]
	for i in range(1, ts.size()):
		if t <= float(ts[i]):
			return _mix(ps[i - 1], ps[i], _smooth((t - float(ts[i - 1])) / maxf(float(ts[i]) - float(ts[i - 1]), 0.0001)))
	return ps[ps.size() - 1]


## The two arm poses (left of the screen first) for a gesture: hand position in u from the head centre, hand kind, finger angle (radians, 0 = right, down = PI/2) and hand scale.
## One-shots (deal, pay, sweep, shrug, facepalm) begin and end exactly at rest, with a wind-up before the move and a follow-through after it, so nothing snaps when they finish.
## Silhouettes differ: deal is a flick outward from the deck, pay a flat palm pushing a stack toward the player, sweep a long reach and a clawed rake back, invite an open palm offered toward
## the player's money, point a long arm and a big index finger.
static func _poses(g: String, t: float, pt: Vector2, lift: float, has_target: bool) -> Array:
	var rest_l := _pose(Vector2(-26.0, 70.0), "flat", PI * 0.5 - 0.35)
	var rest_r := _pose(Vector2(26.0, 70.0), "flat", PI * 0.5 + 0.35)
	var l := rest_l
	var r := rest_r
	var side := 1.0 if (pt.x >= 0.0 or not has_target) else -1.0
	var rest_s := rest_r if side > 0.0 else rest_l
	var sh := Vector2(side * 25.0, 27.0)
	var p := rest_s
	match g:
		"point_deck", "point_hand":
			var aim := pt
			if not has_target:
				aim = Vector2(74.0, 56.0) if g == "point_deck" else Vector2(6.0, 130.0)
			var dv := aim - sh
			var dn := dv / maxf(dv.length(), 0.01)
			var e := _smooth(t / 0.25)
			var wind := _trap(t, 0.0, 0.08, 0.1, 0.22)  # a small pull back before the arm shoots out
			var jab := 6.0 * maxf(0.0, sin(TAU * (t - 0.25) * 3.0)) if t > 0.25 else 0.0
			var reach := clampf(dv.length() - 12.0, 30.0, 54.0) * e + jab - 8.0 * wind
			var out := _pose(sh + dn * maxf(reach, 14.0), "point", dn.angle(), 1.3)
			p = _mix(rest_s, out, maxf(e, wind * 0.5))
		"invite":
			var aim := pt if has_target else Vector2(0.0, 130.0)
			var dn := (aim - sh).normalized()
			var reach := 42.0 + 6.0 * (0.5 - 0.5 * cos(TAU * t))
			var curl := 0.35 * maxf(0.0, sin(TAU * t * 2.0))  # the fingers curl in twice: come on, it is your turn
			p = _pose(sh + dn * reach, "open", dn.angle() - side * 0.25 - side * curl, 1.3)
		"tap_table":
			var up := pow(0.5 - 0.5 * cos(TAU * t * 2.0), 1.4)
			r = _pose(Vector2(32.0, 77.0 - 13.0 * up), "point", PI * 0.5 + 0.25, 1.15)
		"wave_off":
			var sw := sin(TAU * t * 2.0)
			r = _pose(Vector2(30.0 + 12.0 * sw, 26.0), "open", -PI * 0.5 + 0.35 * sw, 1.35)
		"deal":
			var aim := pt if has_target else Vector2(74.0, 56.0)
			var at := sh + (aim - sh).limit_length(50.0)
			var flick := (aim - sh).normalized().rotated(-0.9 if side > 0.0 else 0.9)
			p = _keys(t, [0.0, 0.25, 0.36, 0.52, 0.64, 1.0], [
				rest_s,
				_pose(at + Vector2(0.0, -2.0), "flat", PI * 0.5, 1.1),
				_pose(at + Vector2(side * 4.0, -8.0), "flat", PI * 0.5 - side * 0.4, 1.1),
				_pose(at + flick * 18.0 + Vector2(0.0, 10.0), "open", flick.angle(), 1.25),
				_pose(at + flick * 22.0 + Vector2(0.0, 14.0), "open", flick.angle() + side * 0.3, 1.25),
				rest_s])
		"sweep":
			var aim := pt if has_target else Vector2(-60.0, 70.0)
			var dn := (aim - sh).normalized()
			var far := sh + (aim - sh).limit_length(52.0)
			p = _keys(t, [0.0, 0.3, 0.4, 0.75, 1.0], [
				rest_s,
				_pose(far, "open", dn.angle(), 1.3),
				_pose(far + dn * 2.0, "claw", dn.angle() + side * 0.2, 1.3),
				_pose(Vector2(side * 14.0, 64.0), "claw", PI * 0.5 + side * 0.6, 1.3),
				rest_s])
		"pay":
			var aim := pt if has_target else Vector2(-52.0, 58.0)
			var at := sh + (aim - sh).limit_length(48.0)
			var toward := Vector2(side * -4.0, 34.0)
			p = _keys(t, [0.0, 0.2, 0.3, 0.6, 0.75, 1.0], [
				rest_s,
				_pose(at, "flat", PI * 0.5 + side * 0.2, 1.25),
				_pose(at + Vector2(0.0, 2.0), "flat", PI * 0.5 + side * 0.2, 1.25),
				_pose(at + toward, "flat", PI * 0.5, 1.3),
				_pose(at + toward + Vector2(0.0, 3.0), "open", PI * 0.5 - side * 0.3, 1.3),
				rest_s])
		"shrug":
			l = _mix(rest_l, _pose(Vector2(-43.0, 50.0), "open", -PI * 0.5 - 0.55, 1.2), lift)
			r = _mix(rest_r, _pose(Vector2(43.0, 50.0), "open", -PI * 0.5 + 0.55, 1.2), lift)
		"clap":
			var gap := 3.0 + 14.0 * (0.5 + 0.5 * cos(TAU * t * 2.0))
			l = _pose(Vector2(-gap, 42.0), "flat", -PI * 0.5 + 0.12, 1.2)
			r = _pose(Vector2(gap, 42.0), "flat", -PI * 0.5 - 0.12, 1.2)
		"facepalm":
			var w := _trap(t, 0.0, 0.3, 0.85, 1.0)
			r = _mix(rest_r, _pose(Vector2(2.0, 5.0), "flat", -PI * 0.5 - 0.1, 1.45), w)
	if g in ["point_deck", "point_hand", "invite", "deal", "sweep", "pay"]:
		if side > 0.0:
			r = p
		else:
			l = p
	return [l, r]


## How a gesture moves the head: Vector3(dx, dy, extra tilt in degrees). A nod with the invite, a lean toward what is pointed at, a shake with the wave-off, bobs with the clap.
static func _head_motion(g: String, t: float, pt: Vector2) -> Vector3:
	var side := 1.0 if pt.x >= 0.0 else -1.0
	match g:
		"invite":
			return Vector3(side * 2.0, 3.0 * maxf(0.0, sin(TAU * t * 2.0)), side * 4.0)
		"point_deck", "point_hand":
			var e := _smooth(t / 0.25)
			return Vector3(side * 4.0 * e, 2.0 * e, side * 5.0 * e)
		"deal", "pay", "sweep":
			var w := _trap(t, 0.0, 0.3, 0.7, 1.0)
			return Vector3(side * 3.0 * w, 2.0 * w, side * 3.0 * w)
		"wave_off":
			return Vector3(0.0, 0.0, 9.0 * sin(TAU * t * 2.0 + 0.6))
		"clap":
			return Vector3(0.0, 2.5 * absf(sin(TAU * t * 2.0)), 0.0)
	return Vector3.ZERO


static func _elbow(s: Vector2, h: Vector2, side: float) -> Vector2:
	var d := h - s
	var dist := d.length()
	if dist < 0.01:
		return s + Vector2(side * ARM_L, ARM_L * 0.5)
	var dir := d / dist
	var a := dist * 0.5
	var hh := sqrt(maxf(0.0, ARM_L * ARM_L - a * a))
	var n := Vector2(-dir.y, dir.x)
	if n.dot(Vector2(side * 0.6, 1.0)) < 0.0:
		n = -n
	return s + dir * a + n * hh


static func _arms(ci: CanvasItem, who: String, c: Vector2, u: float, look: Dictionary, poses: Array, lift: float) -> void:
	# the edge pass first (every shape grown a pixel, in the darkest step of its own material: sleeves in the cloth's, hands in the skin's), one triangle list each, then the fills
	var edge_cloth := PackedVector2Array()
	var edge_skin := PackedVector2Array()
	var bb := BlackjackDraw.Batch.new(ci)
	for pass_i in 2:
		var dk := pass_i == 0
		for si in 2:
			var side := -1.0 if si == 0 else 1.0
			var po: Dictionary = poses[si]
			var sh := Vector2(side * 25.0, 27.0 - lift * 5.0)
			var hp: Vector2 = po["h"]
			var dd := hp - sh
			if dd.length() > ARM_L * 2.0 - 1.0:
				hp = sh + dd.normalized() * (ARM_L * 2.0 - 1.0)
			var el := _elbow(sh, hp, side)
			_arm(bb, who, c, u, look, sh, el, hp, String(po["kind"]), float(po["ang"]), float(po["k"]), side, dk, edge_cloth, edge_skin)
		if dk:
			bb.add(edge_cloth, look["cloth_dark"])
			bb.add(edge_skin, look["skin_deep"])
	bb.flush()


## The side of segment a-b that faces up (toward the lamp), as a unit normal.
static func _up_normal(a: Vector2, b: Vector2) -> Vector2:
	var d := b - a
	if d.length() < 0.5:
		return Vector2(0.0, -1.0)
	var n := Vector2(-d.y, d.x).normalized()
	return n if n.y <= 0.0 else -n


## One arm: in the edge pass (`dk`) its shapes, grown, are added to the edge lists; in the fill pass they are drawn in their colours: the sleeve with the lamp's light along its upper side
## and shade along the lower, a bare forearm (the dealer's rolled sleeves) or a cuff, the hand lit on its back.
static func _arm(bb: BlackjackDraw.Batch, who: String, c: Vector2, u: float, look: Dictionary, sh: Vector2, el: Vector2, hp: Vector2, kind: String, ang: float, k: float, side: float, dk: bool, edge_cloth: PackedVector2Array, edge_skin: PackedVector2Array) -> void:
	var g := maxf(1.0, roundf(u)) if dk else 0.0
	var cloth: Color = look["cloth"]
	var skin: Color = look["skin"]
	var fore_skin: bool = look["forearm_skin"]
	var s := c + Vector2(roundf(sh.x * u), roundf(sh.y * u))
	var e := c + Vector2(roundf(el.x * u), roundf(el.y * u))
	var h := c + Vector2(roundf(hp.x * u), roundf(hp.y * u))
	var wu := 10.0 * u
	var wf := 8.4 * u
	var ee := e
	var fdir := (h - e).normalized() if (h - e).length() > 0.5 else Vector2(0.0, 1.0)
	var hk := k * HAND_K
	if dk:
		BlackjackDraw.limb_into(edge_cloth, s, e, wu + 2.0 * g, wu - 0.6 * u + 2.0 * g)
		if fore_skin:
			BlackjackDraw.limb_into(edge_skin, ee, h, wf + 2.0 * g, wf - 0.8 * u + 2.0 * g)
			BlackjackDraw.limb_into(edge_cloth, ee - fdir * 1.0, ee + fdir * maxf(3.0, 5.0 * u), wf + 3.4 * u + 2.0 * g, wf + 3.4 * u + 2.0 * g)
		else:
			BlackjackDraw.limb_into(edge_cloth, ee, h, wf + 2.0 * g, wf - 0.8 * u + 2.0 * g)
		_hand_into(edge_skin, h, ang, kind, hk, u, g, side)
		return
	var nu := _up_normal(s, e)
	bb.add_limb(s, e, wu, wu - 0.6 * u, cloth)
	bb.add_limb(s - nu * wu * 0.3, e - nu * wu * 0.3, wu * 0.4, wu * 0.35, look["cloth_shade"])
	bb.add_limb(s + nu * wu * 0.28, e + nu * wu * 0.28, wu * 0.3, wu * 0.26, look["cloth_light"])
	var nf := _up_normal(ee, h)
	var fcol: Color = skin if fore_skin else cloth
	bb.add_limb(ee, h, wf, wf - 0.8 * u, fcol)
	bb.add_limb(ee + nf * wf * 0.28, h + nf * wf * 0.28, wf * 0.28, wf * 0.24, look["skin_light"] if fore_skin else look["cloth_light"])
	if fore_skin:  # rolled sleeve at the elbow, lit on top
		bb.add_limb(ee - fdir * 1.0, ee + fdir * maxf(3.0, 5.0 * u), wf + 3.4 * u, wf + 3.4 * u, look["cloth"])
	elif who == "npc_a":  # the blouse's cuff
		bb.add_limb(h - fdir * maxf(4.0, 6.0 * u), h - fdir * maxf(2.0, 3.0 * u), wf + 0.8 * u, wf + 0.8 * u, look["accent"])
	else:  # gold bangles at the wrist
		bb.add_limb(h - fdir * maxf(4.0, 5.0 * u), h - fdir * maxf(3.0, 4.0 * u), wf + 0.4 * u, wf + 0.4 * u, look["gold"])
	_hand(bb, h, ang, kind, hk, u, skin, side, look["skin_shade"], look["skin_light"])


## A limb (see `BlackjackDraw.limb`) as a triangle list.
static func _lt(a: Vector2, b: Vector2, wa: float, wb: float) -> PackedVector2Array:
	var tris := PackedVector2Array()
	BlackjackDraw.limb_into(tris, a, b, wa, wb)
	return tris


## A hand's fill pass: its shapes in `col` as one triangle list, the back of the hand lit (dithered `light_col`), a fist's knuckle lines in `shade_col`.
static func _hand(bb: BlackjackDraw.Batch, p: Vector2, ang: float, kind: String, k: float, u: float, col: Color, side: float, shade_col: Color, light_col: Color) -> void:
	var tris := PackedVector2Array()
	_hand_into(tris, p, ang, kind, k, u, 0.0, side)
	bb.add(tris, col)
	var d := Vector2(cos(ang), sin(ang))
	var n := Vector2(-d.y, d.x)
	var q := u * k
	bb.add(BlackjackDraw.ell_tris(p.x + d.x * 0.5 * q, p.y + d.y * 0.5 * q - 1.5 * q, 2.4 * q, 1.4 * q), light_col)
	if kind == "fist":
		for fi in 3:
			var off := (float(fi) - 1.0) * 2.7 * q
			bb.add_limb(p + n * off + d * 1.2 * q, p + n * off + d * 2.8 * q, 1.0, 1.0, shade_col)
	elif kind == "flat":  # the fingers held together: a shade line between each
		for fo: float in [-2.2, 0.0, 2.2]:
			bb.add_limb(p + d * 3.5 * q + n * fo * q, p + d * 7.0 * q + n * fo * 1.05 * q, 1.0, 1.0, shade_col)


## One hand at `p` with fingers pointing along `ang`, added to a triangle list. Kinds: `flat` (mitten and thumb), `fist`, `point` (index finger out), `open` (fanned fingers), `claw` (curled fingers).
## Drawn in two passes: `g` > 0 is the edge pass (every shape grown by g pixels, drawn in a dark step of the skin), 0 the fill pass.
static func _hand_into(tris: PackedVector2Array, p: Vector2, ang: float, kind: String, k: float, u: float, g: float, side: float) -> void:
	var d := Vector2(cos(ang), sin(ang))
	var n := Vector2(-d.y, d.x)
	var q := u * k
	var gg := g * 2.0
	match kind:
		"point":
			BlackjackDraw.limb_into(tris, p - d * 1.0 * q, p + d * 1.5 * q, 9.5 * q + gg, 9.5 * q + gg)
			BlackjackDraw.limb_into(tris, p + d * 3.0 * q, p + d * 17.0 * q, 4.2 * q + gg, 3.6 * q + gg)
			BlackjackDraw.limb_into(tris, p + n * side * 3.0 * q, p + n * side * 5.0 * q + d * 4.0 * q, 3.2 * q + gg, 3.0 * q + gg)
		"fist":
			BlackjackDraw.limb_into(tris, p - d * 1.0 * q, p + d * 2.0 * q, 10.0 * q + gg, 10.0 * q + gg)
			BlackjackDraw.limb_into(tris, p + n * side * 2.0 * q + d * 2.0 * q, p + n * side * 5.0 * q + d * 5.0 * q, 3.2 * q + gg, 3.0 * q + gg)
		"open", "claw":
			var fl := 10.0 if kind == "open" else 7.5
			BlackjackDraw.limb_into(tris, p - d * 1.0 * q, p + d * 2.0 * q, 9.0 * q + gg, 9.0 * q + gg)
			var spread := [-0.42, -0.14, 0.14, 0.42] if kind == "open" else [-0.2, -0.07, 0.07, 0.2]
			for a: float in spread:
				var fd := Vector2(cos(ang + a), sin(ang + a))
				BlackjackDraw.limb_into(tris, p + d * 3.0 * q + n * (a * 9.0 * q), p + fd * fl * q + n * (a * 3.0 * q), 2.9 * q + gg, 2.6 * q + gg)
			var td := Vector2(cos(ang - side * 1.2), sin(ang - side * 1.2))
			BlackjackDraw.limb_into(tris, p + n * side * 3.5 * q, p + td * 8.0 * q + n * side * 2.0 * q, 3.4 * q + gg, 3.0 * q + gg)
		_:  # flat: a palm and four fingers held together, the thumb out to the side
			BlackjackDraw.limb_into(tris, p - d * 2.0 * q, p + d * 2.0 * q, 9.6 * q + gg, 9.2 * q + gg)
			for fo: float in [-3.3, -1.1, 1.1, 3.3]:
				var fl2 := 8.5 - absf(fo) * 0.45
				BlackjackDraw.limb_into(tris, p + d * 2.0 * q + n * fo * q, p + d * fl2 * q + n * fo * 1.05 * q, 2.6 * q + gg, 2.4 * q + gg)
			BlackjackDraw.limb_into(tris, p + n * side * 4.0 * q - d * 1.0 * q, p + n * side * 6.5 * q + d * 3.0 * q, 3.4 * q + gg, 3.0 * q + gg)


# ------------------------------------------------------------------ the player's hands

## The convex hull of a triangle list's points, as a polygon (to clip against).
static func _hull(tris: PackedVector2Array) -> PackedVector2Array:
	return Geometry2D.convex_hull(tris)


## The player's own hands in first person, entering from the bottom edge. `gesture` is one of `PLAYER_GESTURES`, `gesture_t` 0..1 through a one-shot; `targets` may hold canvas points
## `bet`, `deck`, `hand` (middle of the player's cards), `pile` and `pockets`; missing ones come from `BlackjackDraw`. Suggested lengths in beats: pockets 2, lay_money 2, push_bet 1.5, reach_deck 1,
## cover_cards 1.5, drop_cards 1.5, empty_pockets 2, gather_money 2. `none` draws nothing.
static func draw_player_hands(ci: CanvasItem, size: Vector2, u: float, gesture: String, gesture_t: float, targets: Dictionary = {}) -> void:
	if not PLAYER_GESTURES.has(gesture) or gesture == "none":
		return
	var t := clampf(gesture_t, 0.0, 1.0)
	var cx := size.x * 0.5
	var bot := size.y
	var bet: Vector2 = targets.get("bet", BlackjackDraw.bet_spot(size))
	var deck: Vector2 = targets.get("deck", BlackjackDraw.deck_spot(size))
	var hand: Vector2 = targets.get("hand", Vector2(cx, 190.0 * u))
	var pile: Vector2 = targets.get("pile", BlackjackDraw.pile_origin(size) + Vector2(46.0 * u, -26.0 * u))
	var pockets: Vector2 = targets.get("pockets", BlackjackDraw.pockets_spot(size))
	var lh := {"w": Vector2(cx - 60.0 * u, bot + 30.0 * u), "kind": "flat", "ang": -PI * 0.5 + 0.3, "k": 1.5, "wad": false}
	var rh := {"w": Vector2(cx + 60.0 * u, bot + 30.0 * u), "kind": "flat", "ang": -PI * 0.5 - 0.3, "k": 1.5, "wad": false}
	var extra := 0.0
	match gesture:
		"pockets":
			var down := _trap(t, -0.01, 0.3, 0.38, 0.5)
			var up := _trap(t, 0.5, 0.85, 1.01, 1.02)
			var hover := Vector2(cx - 62.0 * u, bot - 30.0 * u)
			var below := Vector2(cx - 62.0 * u, bot + 36.0 * u)
			var held := Vector2(cx - 17.0 * u, bot - 40.0 * u)
			var pl := hover.lerp(below, down) if t < 0.5 else below.lerp(held, up)
			var pr := Vector2(2.0 * cx - pl.x, pl.y) if t < 0.5 else Vector2(cx + 17.0 * u, pl.y)
			lh["w"] = pl
			rh["w"] = pr
			lh["kind"] = "fist" if t < 0.5 else "flat"
			rh["kind"] = "fist" if t < 0.5 else "flat"
			lh["ang"] = -PI * 0.5 + 0.3 if t < 0.5 else -PI * 0.5 + 0.55
			rh["ang"] = -PI * 0.5 - 0.3 if t < 0.5 else -PI * 0.5 - 0.55
			if t >= 0.5:
				extra = 1.0
		"lay_money":
			var come := _trap(t, 0.0, 0.45, 0.6, 0.9)
			var from_l := Vector2(cx - 90.0 * u, bot + 34.0 * u)
			var to_l := pile + Vector2(-16.0 * u, 0.0)
			lh["w"] = from_l.lerp(to_l, come)
			rh["w"] = Vector2(cx - 40.0 * u, bot + 34.0 * u).lerp(pile + Vector2(16.0 * u, 0.0), come)
			lh["ang"] = -PI * 0.5 + 0.5
			rh["ang"] = -PI * 0.5 - 0.1
			extra = 1.0 if t < 0.55 else 0.0
			if t >= 0.55:
				lh["kind"] = "open"
				rh["kind"] = "open"
		"push_bet":  # the hand takes the top fiver and carries it along its arc to the bet ring (the same easing and height as the note's own flight), then lets go
			var e := _smooth(t)
			var on_note := pile.lerp(bet, e) + Vector2(4.0 * u, 12.0 * u - sin(PI * t) * 16.0 * u)
			var come := _smooth(t / 0.12)
			var go := _smooth((t - 0.86) / 0.14)
			var below := Vector2(cx - 40.0 * u, bot + 40.0 * u)
			rh["w"] = below.lerp(on_note, come).lerp(below, go)
			rh["ang"] = -PI * 0.5 - 0.15
			rh["kind"] = "open" if t > 0.8 else "flat"
			lh["w"] = Vector2(cx - 60.0 * u, bot + 40.0 * u)
		"reach_deck":
			var go := _trap(t, 0.0, 0.4, 0.62, 1.0)
			var tap := maxf(0.0, sin((t - 0.4) / 0.22 * TAU)) * 5.0 * u if t > 0.4 and t < 0.62 else 0.0
			var ang := (deck - Vector2(cx + 50.0 * u, bot)).angle()
			rh["w"] = Vector2(cx + 56.0 * u, bot + 34.0 * u).lerp(deck + Vector2(0.0, 20.0 * u + tap), go)
			rh["kind"] = "point"
			rh["ang"] = lerp_angle(-PI * 0.5 - 0.3, ang, go)
			rh["k"] = 1.4
		"cover_cards":
			var go := _trap(t, 0.0, 0.4, 0.85, 1.0)
			rh["w"] = Vector2(cx + 56.0 * u, bot + 34.0 * u).lerp(hand + Vector2(0.0, 10.0 * u), go)
			rh["ang"] = lerp_angle(-PI * 0.5 - 0.3, -PI * 0.5, go)
			rh["k"] = 2.3
		"drop_cards":
			var fly := _smooth((t - 0.25) / 0.3)
			var away := _smooth((t - 0.55) / 0.45)
			var pl := hand + Vector2(-16.0 * u, 4.0 * u)
			var pr := hand + Vector2(16.0 * u, 4.0 * u)
			lh["w"] = pl + Vector2(-46.0 * u * fly - 40.0 * u * away, -34.0 * u * fly + 90.0 * u * away)
			rh["w"] = pr + Vector2(46.0 * u * fly + 40.0 * u * away, -34.0 * u * fly + 90.0 * u * away)
			if t < 0.25:
				lh["w"] = (pl + Vector2(-16.0 * u, 70.0 * u)).lerp(pl, _smooth(t / 0.25))
				rh["w"] = (pr + Vector2(16.0 * u, 70.0 * u)).lerp(pr, _smooth(t / 0.25))
			lh["kind"] = "fist" if t < 0.25 else "open"
			rh["kind"] = "fist" if t < 0.25 else "open"
			lh["ang"] = -PI * 0.5 + 0.1
			rh["ang"] = -PI * 0.5 - 0.1
		"empty_pockets":
			var rise := _trap(t, 0.0, 0.3, 0.8, 1.0)
			var turn := _smooth((t - 0.3) / 0.25)
			lh["w"] = Vector2(cx - 90.0 * u, bot + 34.0 * u).lerp(Vector2(cx - 40.0 * u, bot - 50.0 * u), rise)
			rh["w"] = Vector2(cx + 90.0 * u, bot + 34.0 * u).lerp(Vector2(cx + 40.0 * u, bot - 50.0 * u), rise)
			lh["kind"] = "open" if turn > 0.5 else "fist"
			rh["kind"] = "open" if turn > 0.5 else "fist"
			lh["ang"] = lerp_angle(-PI * 0.5 + 0.2, -PI * 0.5 + 0.9, turn)
			rh["ang"] = lerp_angle(-PI * 0.5 - 0.2, -PI * 0.5 - 0.9, turn)
			lh["k"] = 1.5
			rh["k"] = 1.5
			var pull := _trap(t, 0.1, 0.45, 0.85, 1.0)
			for sx: float in [-1.0, 1.0]:
				_lining(ci, Vector2(cx + sx * 105.0 * u, bot), u, pull)
		"gather_money":
			var reach := _smooth(t / 0.3)
			var scoop := _smooth((t - 0.3) / 0.45)
			var out := _smooth((t - 0.75) / 0.25)
			var base_l := pile + Vector2(-12.0 * u, -4.0 * u)
			var base_r := pile + Vector2(14.0 * u, -4.0 * u)
			var home_l := pockets + Vector2(-10.0 * u, -8.0 * u)
			var home_r := pockets + Vector2(26.0 * u, -8.0 * u)
			var start_l := Vector2(base_l.x, bot + 30.0 * u)
			var start_r := Vector2(base_r.x, bot + 30.0 * u)
			var pl := start_l.lerp(base_l, reach)
			var pr := start_r.lerp(base_r, reach)
			pl = pl.lerp(home_l, scoop)
			pr = pr.lerp(home_r, scoop)
			pl.y += out * 40.0 * u
			pr.y += out * 40.0 * u
			lh["w"] = pl
			rh["w"] = pr
			lh["kind"] = "claw"
			rh["kind"] = "claw"
			lh["ang"] = -PI * 0.5 + 0.5 + scoop * 0.8
			rh["ang"] = -PI * 0.5 - 0.5 - scoop * 0.8
			extra = 1.0 if (t > 0.45 and t < 0.9) else 0.0
	_phand_pair(ci, size, u, lh, rh, extra)


static func _lining(ci: CanvasItem, p: Vector2, u: float, pull: float) -> void:
	if pull <= 0.02:
		return
	var h := 30.0 * u * pull
	var w := 17.0 * u
	var pts := PackedVector2Array([Vector2(roundf(p.x - w * 0.5), roundf(p.y + 2.0)), Vector2(roundf(p.x - w * 0.5), roundf(p.y - h * 0.7)), Vector2(roundf(p.x - w * 0.3), roundf(p.y - h)),
		Vector2(roundf(p.x + w * 0.3), roundf(p.y - h)), Vector2(roundf(p.x + w * 0.5), roundf(p.y - h * 0.7)), Vector2(roundf(p.x + w * 0.5), roundf(p.y + 2.0))])
	BlackjackDraw.poly_o(ci, pts, LINING, LINING.darkened(0.45), maxf(1.0, roundf(u)))
	BlackjackDraw.dither_fill(ci, BlackjackDraw.tris_of(pts), LINING.darkened(0.25), D_QUARTER)
	BlackjackDraw.rect(ci, p.x - 1.0, p.y - h * 0.8, 1.0, h * 0.6, LINING.darkened(0.3))


## The player's own arms: a dark jacket sleeve from below the picture, its upper side lit by the lamp ahead and its near end lost in the dark, the shirt cuff, the hand lit on its back.
## Drawn in three runs for both arms together: the edges and the sleeves (solid), the light and the dark on the cloth (dithered), then the cuffs and the hands (solid).
static func _phand_pair(ci: CanvasItem, size: Vector2, u: float, lh: Dictionary, rh: Dictionary, wad: float) -> void:
	var edge_cloth := PackedVector2Array()
	var edge_skin := PackedVector2Array()
	var sleeves := PackedVector2Array()
	var dith := BlackjackDraw.Batch.new()
	var top := BlackjackDraw.Batch.new()
	for si in 2:
		var po: Dictionary = lh if si == 0 else rh
		var side := -1.0 if si == 0 else 1.0
		var w: Vector2 = po["w"]
		if w.y > size.y + 60.0 * u:
			continue
		var g := maxf(1.0, roundf(u))
		var ww := 21.0 * u
		var wr := Vector2(roundf(w.x), roundf(w.y))
		# a sleeve in two parts: the upper arm from below the picture to an elbow bent outward, then the forearm to the cuff
		var anchor := Vector2(w.x + (w.x - size.x * 0.5) * 0.35 + side * 26.0 * u, size.y + 70.0 * u)
		var elbow := anchor.lerp(wr, 0.5) + Vector2(side * 15.0 * u, 8.0 * u)
		var wrist := wr + Vector2(0.0, 3.0 * u)
		BlackjackDraw.limb_into(edge_cloth, anchor, elbow, ww * 1.75 + 2.0 * g, ww * 1.3 + 2.0 * g)
		BlackjackDraw.limb_into(edge_cloth, elbow, wrist, ww * 1.3 + 2.0 * g, ww * 0.88 + 2.0 * g)
		_hand_into(edge_skin, wr, float(po["ang"]), String(po["kind"]), float(po["k"]), u, g, side)
		BlackjackDraw.limb_into(sleeves, anchor, elbow, ww * 1.75, ww * 1.3)
		BlackjackDraw.limb_into(sleeves, elbow, wrist, ww * 1.3, ww * 0.88)
		var fd := (wrist - elbow).normalized()
		var fn := Vector2(-fd.y, fd.x) * (1.0 if Vector2(-fd.y, fd.x).x * side > 0.0 else -1.0)
		var ud := (elbow - anchor).normalized()
		var un := Vector2(-ud.y, ud.x) * (1.0 if Vector2(-ud.y, ud.x).x * side > 0.0 else -1.0)
		# the lamp ahead lights the forearm's top and the inside of the upper arm; the outer side and the near end are in the dark
		var light := PackedVector2Array()
		BlackjackDraw.limb_into(light, elbow - fn * ww * 0.1, wrist - fd * 6.0 * u - fn * ww * 0.05, ww * 0.7, ww * 0.5)
		dith.add(light, SLEEVE_LIGHT, D_HALF)
		var dark := PackedVector2Array()
		BlackjackDraw.limb_into(dark, anchor + un * ww * 0.55, elbow + un * ww * 0.45, ww * 0.55, ww * 0.4)
		BlackjackDraw.limb_into(dark, anchor, anchor.lerp(elbow, 0.45), ww * 1.75, ww * 1.5)
		dith.add(dark, SLEEVE_DARK, D_HALF)
		top.add_limb(elbow.lerp(wrist, 0.35) - fn * ww * 0.15, wrist - fd * 7.0 * u - fn * ww * 0.1, ww * 0.3, ww * 0.25, SLEEVE_LIGHT)
		# the crease inside the elbow
		top.add_limb(elbow - fn * ww * 0.45 - fd * 3.0 * u, elbow - fn * ww * 0.2 + fd * 4.0 * u, maxf(1.0, 2.0 * u), maxf(1.0, 1.5 * u), SLEEVE_DEEP)
		# the shirt cuff, shaded on its under side, and its button
		top.add_limb(wrist - fd * 6.0 * u, wrist - fd * 1.0 * u, ww * 0.82, ww * 0.82, CUFF_SHADE)
		top.add_limb(wrist - fd * 6.0 * u - fn * u, wrist - fd * 2.0 * u - fn * u, ww * 0.62, ww * 0.62, CUFF)
		top.add(BlackjackDraw.rect_tris(wrist.x - fd.x * 4.0 * u + fn.x * ww * 0.2, wrist.y - fd.y * 4.0 * u + fn.y * ww * 0.2, maxf(1.0, 2.0 * u), maxf(1.0, 2.0 * u)), SLEEVE_DARK)
		_hand(top, wr, float(po["ang"]), String(po["kind"]), float(po["k"]), u, GLOVE_SKIN, side, GLOVE_SHADE, GLOVE_LIGHT)
	var base := BlackjackDraw.Batch.new(ci)
	base.add(edge_cloth, SLEEVE_DEEP)
	base.add(edge_skin, GLOVE_DEEP)
	base.add(sleeves, SLEEVE)
	base.flush()
	dith.flush()
	BlackjackDraw.draw_runs(ci, dith.runs)
	top.flush()
	BlackjackDraw.draw_runs(ci, top.runs)
	if wad > 0.5:  # the money in the hand: real fivers, the same notes that land on the table
		var lw: Vector2 = lh["w"]
		var rw: Vector2 = rh["w"]
		var mid := (lw + rw) * 0.5 if wad < 1.5 else rw
		mid += Vector2(0.0, -14.0 * u)
		for i in 3:
			MoneyDraw.draw_note(ci, 500, mid + Vector2(float(i) * 2.0 - 2.0, -float(i) * 3.0) * u, u * 1.25, (float(i) - 1.0) * 0.12)
