class_name BlackjackPeople
extends RefCounted
## The blackjack drawing kit, part two: three expressive people seen from across the table (a parametric face, gaze, twelve arm gestures) and the player's own hands entering from the
## bottom edge. Everything is flat colours with dark outlines built from whole-pixel rect rows and polygons (see `BlackjackDraw`), sized from `u = canvas height / 230`.
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

## Palettes and looks. The three people differ in silhouette (visor and bare forearms, grey hair and glasses, big wild hair), skin and clothes.
const LOOKS := {
	"dealer": {
		"skin": Color("f0bd96"), "skin_shade": Color("c98a63"), "hair": Color("4a3020"), "brow": Color("3a2416"), "cloth": Color("e9edf2"), "cloth_shade": Color("b3bfce"),
		"cloth_dark": Color("8f9db1"), "accent": Color("b8323f"), "hw": 17.0, "hh": 19.0, "forearm_skin": true, "brow_dy": 0.0,
	},
	"npc_a": {
		"skin": Color("f6d6c0"), "skin_shade": Color("d9a98e"), "hair": Color("e6e6ee"), "brow": Color("a0a0b0"), "cloth": Color("d4a73e"), "cloth_shade": Color("a07d27"),
		"cloth_dark": Color("7a5e1c"), "accent": Color("f0e4c4"), "hw": 16.0, "hh": 19.0, "forearm_skin": false, "brow_dy": -3.0,
	},
	"npc_b": {
		"skin": Color("96623f"), "skin_shade": Color("6f4329"), "hair": Color("2a1f45"), "brow": Color("1d1530"), "cloth": Color("cc6a82"), "cloth_shade": Color("9c435d"),
		"cloth_dark": Color("742c43"), "accent": Color("5a7fd0"), "hw": 16.0, "hh": 18.0, "forearm_skin": false, "brow_dy": 0.0,
	},
}

const INK := BlackjackDraw.INK
const PUPIL := Color("14121f")
const WHITE := Color("f8f8f4")
const MOUTH_IN := Color("3a1424")
const TONGUE := Color("d4506a")
const BLUSH := Color("ee7f8f")
const SWEAT := Color("8fd4f4")
const GLOVE_SKIN := Color("cf9468")
const SLEEVE := Color("4c5b94")
const SLEEVE_LIGHT := Color("7183c4")
const SLEEVE_DARK := Color("2f3a66")
const CUFF := Color("ece5d0")
const LINING := Color("dcdce6")

const ARM_L := 28.0
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
## or paying gesture goes to (zero: a sensible default). `layer` is `"all"`, `"body"` (head and torso, draw before the table) or `"arms"` (draw after it).
## Gesture timing (gesture_t): `rest`, `invite`, `tap_table`, `wave_off`, `clap` loop (2 cycles per unit for tap, wave, clap; 1 for invite); `point_deck`, `point_hand` jab 2 times per unit and hold;
## `deal`, `sweep`, `pay`, `shrug`, `facepalm` are one-shots. Suggested lengths in beats: invite 2, point 2, deal 1, sweep 2, pay 2, shrug 2, clap 2, facepalm 3, tap_table 1, wave_off 2.
static func draw_person(ci: CanvasItem, who: String, center: Vector2, u: float, face: Dictionary, gaze_to: Vector2, gesture: String, gesture_t: float, beat_phase: float, point_to := Vector2.ZERO, layer := "all") -> void:
	var look: Dictionary = LOOKS.get(who, LOOKS["dealer"])
	var g := gesture if GESTURES.has(gesture) else "rest"
	var c := Vector2(roundf(center.x), roundf(center.y))
	var lift := 0.0
	if g == "shrug":
		lift = _trap(gesture_t, 0.0, 0.2, 0.8, 1.0)
	var rel := Vector2.ZERO
	if point_to != Vector2.ZERO:
		rel = (point_to - c) / u
	if layer != "arms":
		_body(ci, who, c, u, look, lift)
		var hm := _head_motion(g, gesture_t, rel)
		_head(ci, who, c + Vector2(roundf(hm.x * u), roundf(hm.y * u)), u, look, face, gaze_to, beat_phase, hm.z)
	if layer != "body":
		var poses := _poses(g, gesture_t, rel, lift, point_to != Vector2.ZERO)
		_arms(ci, who, c, u, look, poses, lift)


# ------------------------------------------------------------------ body

static func _body(ci: CanvasItem, who: String, c: Vector2, u: float, look: Dictionary, lift: float) -> void:
	var cloth: Color = look["cloth"]
	var shade: Color = look["cloth_shade"]
	var dark: Color = look["cloth_dark"]
	var accent: Color = look["accent"]
	var skin: Color = look["skin"]
	var sk: Color = look["skin_shade"]
	var lf := lift * 5.0
	var t := maxf(1.0, roundf(u))
	var pts := PackedVector2Array([
		c + Vector2(_p(-9.0, u), _p(15.0 - lf, u)), c + Vector2(_p(-22.0, u), _p(20.0 - lf, u)), c + Vector2(_p(-31.0, u), _p(28.0 - lf * 0.6, u)), c + Vector2(_p(-32.0, u), _p(52.0, u)),
		c + Vector2(_p(32.0, u), _p(52.0, u)), c + Vector2(_p(31.0, u), _p(28.0 - lf * 0.6, u)), c + Vector2(_p(22.0, u), _p(20.0 - lf, u)), c + Vector2(_p(9.0, u), _p(15.0 - lf, u)),
	])
	BlackjackDraw.rect(ci, c.x - _p(6.5, u) - t, c.y + _p(10.0, u), _p(13.0, u) + 2.0 * t, _p(12.0, u), INK)
	BlackjackDraw.poly_o(ci, pts, cloth, INK, t)
	# shaded lower half and shoulder fold
	BlackjackDraw.rect(ci, c.x - _p(31.0, u), c.y + _p(42.0, u), _p(62.0, u), _p(10.0, u), shade)
	BlackjackDraw.rect(ci, c.x - _p(31.0, u), c.y + _p(28.0, u) - lf * u * 0.6, t, _p(24.0, u), shade)
	BlackjackDraw.rect(ci, c.x + _p(30.0, u), c.y + _p(28.0, u) - lf * u * 0.6, t, _p(24.0, u), shade)
	BlackjackDraw.rect(ci, c.x - _p(6.5, u), c.y + _p(10.0, u), _p(13.0, u), _p(10.0, u), sk)
	match who:
		"dealer":
			var vee := PackedVector2Array([c + Vector2(_p(-8.0, u), _p(15.0 - lf, u)), c + Vector2(_p(8.0, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(27.0, u))])
			BlackjackDraw.poly_o(ci, vee, skin, INK, t)
			for sx in [-1.0, 1.0]:
				var col := PackedVector2Array([c + Vector2(sx * _p(9.0, u), _p(14.0 - lf, u)), c + Vector2(sx * _p(1.0, u), _p(27.0, u)), c + Vector2(sx * _p(13.0, u), _p(27.0, u)), c + Vector2(sx * _p(15.0, u), _p(19.0 - lf, u))])
				BlackjackDraw.poly_o(ci, col, cloth, INK, t)
				BlackjackDraw.rect(ci, c.x + sx * _p(13.0, u) - _p(2.5, u), c.y + _p(25.0, u), _p(5.0, u), _p(27.0, u), INK)
				BlackjackDraw.rect(ci, c.x + sx * _p(13.0, u) - _p(1.5, u), c.y + _p(25.0, u), _p(3.0, u), _p(27.0, u), accent)
		"npc_a":
			var vee := PackedVector2Array([c + Vector2(_p(-9.0, u), _p(15.0 - lf, u)), c + Vector2(_p(9.0, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(36.0, u))])
			BlackjackDraw.poly_o(ci, vee, accent, INK, t)
			BlackjackDraw.rect(ci, c.x, c.y + _p(34.0, u), t, _p(18.0, u), INK)
			for i in 3:
				BlackjackDraw.rect(ci, c.x + _p(3.0, u), c.y + _p(37.0 + 5.0 * i, u), maxf(2.0, _p(2.5, u)), maxf(2.0, _p(2.5, u)), dark)
		"npc_b":
			var vee := PackedVector2Array([c + Vector2(_p(-10.0, u), _p(15.0 - lf, u)), c + Vector2(_p(10.0, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(38.0, u))])
			BlackjackDraw.poly_o(ci, vee, dark, INK, t)
			var inner := PackedVector2Array([c + Vector2(_p(-5.0, u), _p(15.0 - lf, u)), c + Vector2(_p(5.0, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(30.0, u))])
			BlackjackDraw.poly(ci, inner, accent)
			BlackjackDraw.poly(ci, PackedVector2Array([c + Vector2(_p(-1.5, u), _p(15.0 - lf, u)), c + Vector2(_p(1.5, u), _p(15.0 - lf, u)), c + Vector2(0.0, _p(26.0, u))]), WHITE)
			for sx in [-1.0, 1.0]:
				BlackjackDraw.limb(ci, c + Vector2(sx * _p(9.0, u), _p(18.0 - lf, u)), c + Vector2(sx * _p(2.0, u), _p(40.0, u)), maxf(2.0, _p(3.5, u)), maxf(2.0, _p(3.5, u)), shade)


# ------------------------------------------------------------------ head and face

static func _head(ci: CanvasItem, who: String, c: Vector2, u: float, look: Dictionary, f: Dictionary, gaze_to: Vector2, beat: float, tilt_add := 0.0) -> void:
	var skin: Color = look["skin"]
	var sk: Color = look["skin_shade"]
	var hair: Color = look["hair"]
	var hw := _p(float(look["hw"]), u)
	var hh := _p(float(look["hh"]), u)
	var t := maxf(1.0, roundf(u))
	var laugh := float(f.get("crescent", 0.0)) > 0.5
	var bob_amp := (0.9 + float(f.get("head_bob", 0.0))) * u
	var bph := beat * (2.0 if laugh else 1.0)
	var bob := roundf(bob_amp * pow(0.5 + 0.5 * cos(TAU * bph), 2.0))
	var pull := roundf(float(f.get("pull", 0.0)) * u)
	var origin := c + Vector2(0.0, bob - pull)
	var tilt := deg_to_rad(float(f.get("head_tilt", 0.0)) + tilt_add)
	ci.draw_set_transform(origin, tilt, Vector2.ONE)
	# hair behind the head
	if who == "npc_b":
		_wild_hair_back(ci, u, look)
	elif who == "npc_a":
		BlackjackDraw.ell_o(ci, 0.0, -_p(2.0, u), hw + _p(2.0, u), hh - _p(3.0, u), hair, INK, t)
	# ears
	for sx in [-1.0, 1.0]:
		BlackjackDraw.ell_o(ci, sx * (hw + _p(0.5, u)), _p(2.0, u), maxf(2.0, _p(3.0, u)), maxf(3.0, _p(4.5, u)), sk, INK, t)
	# the head itself: shade ring at the chin, skin on top
	BlackjackDraw.ell_o(ci, 0.0, 0.0, hw, hh, sk, INK, t)
	BlackjackDraw.ell(ci, 0.0, 0.0, hw - 1.0 if hw > 8.0 else hw, hh - 1.0, skin, -1000, int(hh) - maxi(2, int(_p(3.0, u))))
	match who:
		"dealer":
			BlackjackDraw.rect(ci, -hw, -_p(13.0, u), t * 2.0, _p(10.0, u), look["hair"])
			BlackjackDraw.rect(ci, hw - 2.0 * t + 1.0, -_p(13.0, u), t * 2.0, _p(10.0, u), look["hair"])
	_face_features(ci, who, u, look, f, origin, tilt, gaze_to, beat)
	match who:
		"dealer":
			_visor(ci, u, hw, hh)
		"npc_a":
			_old_hair(ci, u, look, hw, hh)
		"npc_b":
			_wild_hair_front(ci, u, look)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


static func _visor(ci: CanvasItem, u: float, hw: float, hh: float) -> void:
	var t := maxf(1.0, roundf(u))
	var top := -hh - _p(1.0, u)
	var y0 := top
	var y1 := -_p(13.0, u)
	var w := hw + _p(4.0, u)
	var band := PackedVector2Array([Vector2(-w, y1), Vector2(-w + _p(2.0, u), y0), Vector2(w - _p(2.0, u), y0), Vector2(w, y1)])
	BlackjackDraw.poly_o(ci, band, Color("46a864"), INK, t)
	BlackjackDraw.rect(ci, -w + t, y0 + t, 2.0 * w - 2.0 * t, maxf(1.0, _p(1.5, u)), Color("7bd48e"))
	# the brim: a darker lip with the forehead shadow under it
	BlackjackDraw.rect(ci, -w + t, y1 - maxf(2.0, _p(2.5, u)), 2.0 * w - 2.0 * t, maxf(2.0, _p(2.5, u)), Color("2b7a45"))
	BlackjackDraw.rect(ci, -hw + t + 1.0, y1 + 1.0, 2.0 * hw - 2.0 * t - 2.0, maxf(1.0, _p(2.0, u)), Color("c98a63"))


static func _old_hair(ci: CanvasItem, u: float, look: Dictionary, hw: float, hh: float) -> void:
	var hair: Color = look["hair"]
	var t := maxf(1.0, roundf(u))
	# a thin wispy top and a bald shine, side tufts already drawn behind
	var wisp := PackedVector2Array([Vector2(-hw + 1.0, -_p(8.0, u)), Vector2(-hw + _p(3.0, u), -hh + 1.0), Vector2(-_p(4.0, u), -hh - _p(3.0, u)), Vector2(_p(1.0, u), -hh - _p(1.0, u)),
		Vector2(_p(7.0, u), -hh - _p(3.0, u)), Vector2(hw - _p(3.0, u), -hh + 1.0), Vector2(hw - 1.0, -_p(8.0, u)), Vector2(hw - _p(3.0, u), -_p(11.0, u)), Vector2(0.0, -hh + _p(3.0, u)), Vector2(-hw + _p(3.0, u), -_p(11.0, u))])
	BlackjackDraw.poly_o(ci, wisp, hair, INK, t)


static func _wild_hair_back(ci: CanvasItem, u: float, look: Dictionary) -> void:
	var hair: Color = look["hair"]
	var t := maxf(1.0, roundf(u))
	var pts := PackedVector2Array()
	var spikes := [
		Vector2(-27, 8), Vector2(-30, -2), Vector2(-25, -6), Vector2(-31, -14), Vector2(-22, -17), Vector2(-24, -28), Vector2(-14, -25), Vector2(-12, -34), Vector2(-5, -27), Vector2(1, -36),
		Vector2(7, -27), Vector2(13, -34), Vector2(15, -25), Vector2(24, -28), Vector2(22, -17), Vector2(31, -14), Vector2(25, -6), Vector2(30, -2), Vector2(27, 8), Vector2(18, 14),
		Vector2(-18, 14),
	]
	for s: Vector2 in spikes:
		pts.append(Vector2(_p(s.x, u), _p(s.y, u)))
	BlackjackDraw.poly_o(ci, pts, hair, INK, t)
	# a pink streak through the hair
	BlackjackDraw.poly(ci, PackedVector2Array([Vector2(_p(-4.0, u), _p(-27.0, u)), Vector2(_p(1.0, u), _p(-35.0, u)), Vector2(_p(6.0, u), _p(-27.0, u)), Vector2(_p(2.0, u), _p(-24.0, u))]), Color("e0508a"))


static func _wild_hair_front(ci: CanvasItem, u: float, look: Dictionary) -> void:
	var hair: Color = look["hair"]
	var t := maxf(1.0, roundf(u))
	var pts := PackedVector2Array()
	var fr := [
		Vector2(-17, -6), Vector2(-18, -16), Vector2(-14, -22), Vector2(-6, -25), Vector2(2, -25), Vector2(10, -24), Vector2(16, -20), Vector2(18, -14), Vector2(17, -6),
		Vector2(13, -10), Vector2(10, -16), Vector2(6, -9), Vector2(2, -17), Vector2(-2, -9), Vector2(-6, -17), Vector2(-10, -10), Vector2(-14, -15),
	]
	for s: Vector2 in fr:
		pts.append(Vector2(_p(s.x, u), _p(s.y, u)))
	BlackjackDraw.poly_o(ci, pts, hair, INK, t)
	# a hoop earring
	BlackjackDraw.ell(ci, -_p(17.0, u), _p(9.0, u), maxf(2.0, _p(2.5, u)), maxf(2.0, _p(3.5, u)), INK)
	BlackjackDraw.ell(ci, -_p(17.0, u), _p(9.0, u), maxf(1.0, _p(1.5, u)), maxf(1.0, _p(2.5, u)), Color("f2c14a"))
	BlackjackDraw.ell(ci, -_p(17.0, u), _p(9.0, u), maxf(0.0, _p(0.5, u)), maxf(1.0, _p(1.5, u)), look["skin_shade"])


## Eyes, brows, nose, mouth and extras, drawn in the head's local space (origin at the head centre).
static func _face_features(ci: CanvasItem, who: String, u: float, look: Dictionary, f: Dictionary, origin: Vector2, tilt: float, gaze_to: Vector2, beat: float) -> void:
	var t := maxf(1.0, roundf(u))
	var erx := maxf(2.0, _p(5.5, u))
	var ery := maxf(3.0, _p(6.0, u))
	var ex := maxf(erx + 3.0, _p(8.2, u))
	var ey := -_p(1.0, u)
	var seed_v := 0.0 if who == "dealer" else (2.3 if who == "npc_a" else 4.1)
	var blink := _blink(beat, seed_v)
	var glasses := who == "npc_a"
	var brow_col: Color = look["brow"]
	var sk: Color = look["skin_shade"]
	var gl: Vector2 = f.get("gaze_bias", Vector2.ZERO)
	var lock := float(f.get("gaze_lock", 0.0))
	var crescent := float(f.get("crescent", 0.0))
	var pupil_s := float(f.get("pupil", 1.0))
	var rot := Transform2D(tilt, Vector2.ZERO)
	# blush
	var bl := float(f.get("blush", 0.0))
	if bl > 0.05:
		for sx in [-1.0, 1.0]:
			BlackjackDraw.ell(ci, sx * ex * 1.25, _p(7.0, u), maxf(2.0, _p(3.5, u)), maxf(1.0, _p(2.0, u)), BlackjackDraw.shade(BLUSH, clampf(bl, 0.0, 1.0)))
	# eyes
	for si in 2:
		var sx := -1.0 if si == 0 else 1.0
		var lid := float(f.get("lid_l" if si == 0 else "lid_r", 0.9))
		if blink > 0.5 and crescent < 0.5:
			lid = minf(lid, 0.0)
		var cx := sx * ex
		if glasses and u >= LOW_U:
			var ro := maxf(1.0, _p(2.0, u))
			BlackjackDraw.ell(ci, cx, ey, erx + ro + t, ery + ro + t, INK)
			BlackjackDraw.ell(ci, cx, ey, erx + ro, ery + ro, Color("dff0f8"))
		var world := origin + rot * Vector2(cx, ey)
		var dir := gaze_to - world
		var dl := dir.length()
		var dv := Vector2.ZERO
		if dl > 0.5:
			dv = dir / dl * minf(1.0, dl / maxf(1.0, 16.0 * u))
		dv = dv.lerp(gl, lock)
		_eye(ci, cx, ey, erx, ery, lid, crescent, pupil_s, dv, u, sx)
	if glasses and u < LOW_U:  # at low detail the glasses are only a bridge and two rims over the eyes, so the eyes keep their shape
		BlackjackDraw.rect(ci, -ex + erx, ey - 1.0, 2.0 * (ex - erx) + 1.0, 1.0, INK)
		for sx2 in [-1.0, 1.0]:
			BlackjackDraw.rect(ci, sx2 * ex - erx - 1.0, ey - ery - 2.0, 2.0 * erx + 3.0, 1.0, INK)
	# brows (their movement is never smaller than at u 0.8, so moods still read at low detail)
	var ku := maxf(u, 0.8)
	for si in 2:
		var sx := -1.0 if si == 0 else 1.0
		var b: Vector2 = f.get("brow_l" if si == 0 else "brow_r", Vector2.ZERO)
		var by := ey - ery - _p(3.2, u) - b.x * roundf(4.5 * ku) + _p(float(look["brow_dy"]), u)
		var inner := Vector2(sx * maxf(erx * 0.5, _p(3.0, u)), by - b.y * roundf(4.6 * ku))
		var outer := Vector2(sx * (ex + erx), by + b.y * roundf(2.4 * ku))
		if who == "dealer":
			outer.x *= 0.92
		BlackjackDraw.limb(ci, Vector2(roundf(inner.x), roundf(inner.y)), Vector2(roundf(outer.x), roundf(outer.y)), maxf(2.0, _p(2.6, u)), maxf(2.0, _p(2.6, u)), brow_col)
	# nose
	BlackjackDraw.rect(ci, -_p(1.5, u), _p(4.5, u), maxf(2.0, _p(3.0, u)), maxf(2.0, _p(2.0, u)), sk)
	_mouth(ci, u, look, f)
	# extras
	if float(f.get("sweat", 0.0)) > 0.3:
		_drop(ci, Vector2(float(look["hw"]) * u - _p(1.0, u), -_p(11.0, u)), u, 1.0)
	if float(f.get("tear", 0.0)) > 0.3:
		for sx in [-1.0, 1.0]:
			var tx: float = sx * (ex + erx * 0.4)
			BlackjackDraw.rect(ci, tx - 1.0, ey + ery + _p(1.0, u), maxf(2.0, _p(2.0, u)), _p(6.0, u), SWEAT)
			_drop(ci, Vector2(tx, ey + ery + _p(9.0, u)), u, 0.7)


static func _drop(ci: CanvasItem, p: Vector2, u: float, k: float) -> void:
	var w := maxf(2.0, _p(3.0 * k, u))
	var h := maxf(3.0, _p(5.0 * k, u))
	var pts := PackedVector2Array([p + Vector2(0.0, -h), p + Vector2(w, h * 0.3), p + Vector2(w * 0.5, h), p + Vector2(-w * 0.5, h), p + Vector2(-w, h * 0.3)])
	BlackjackDraw.poly_o(ci, pts, SWEAT, INK, 1.0)
	BlackjackDraw.rect(ci, p.x - w * 0.4, p.y + h * 0.1, 1.0, 1.0, WHITE)


static func _eye(ci: CanvasItem, cx: float, cy: float, erx: float, ery: float, lid: float, crescent: float, pupil_s: float, dv: Vector2, u: float, side: float) -> void:
	var t := maxf(1.0, roundf(u))
	cx = roundf(cx)
	cy = roundf(cy)
	if lid < 0.12:
		var th := maxf(1.0, roundf(1.6 * u))
		if crescent > 0.5:
			var rise := maxf(2.0, _p(3.0, u))
			var x := -erx
			while x <= erx:
				var k := x / erx
				BlackjackDraw.rect(ci, cx + x, cy + rise * (k * k) - rise * 0.5, 1.0, th, INK)
				x += 1.0
		else:
			BlackjackDraw.rect(ci, cx - erx, cy + 1.0, erx * 2.0 + 1.0, th, INK)
			# little squeeze lines at the outer corner
			BlackjackDraw.rect(ci, cx + side * (erx + 1.0), cy - 1.0, 1.0, th + 1.0, INK)
		return
	var ry := ery
	var rx := erx
	if lid > 1.0:
		ry = ery * (1.0 + (lid - 1.0) * 0.9)
		rx = erx + roundf((lid - 1.0) * 2.0 * u)
	var top := -1000
	if lid < 1.0:
		top = -int(roundf(ry)) + int(roundf(2.0 * ry * (1.0 - lid)))
	BlackjackDraw.ell(ci, cx, cy, rx + t, ry + t, INK, -1000 if top == -1000 else top - t, 1000)
	BlackjackDraw.ell(ci, cx, cy, rx, ry, WHITE, top, 1000)
	if top != -1000:
		BlackjackDraw.rect(ci, cx - rx - t, cy + top - t, 2.0 * (rx + t) + 1.0, t + 1.0, INK)
	var pr := maxf(1.0, roundf(2.4 * u * pupil_s))
	var mx := maxf(0.0, rx - pr)
	var my := maxf(0.0, ry - pr)
	var po := Vector2(roundf(dv.x * mx), roundf(dv.y * my * 0.8))
	var vis_top := -1000 if top == -1000 else top
	BlackjackDraw.ell(ci, cx + po.x, cy + po.y, pr, pr, PUPIL, vis_top, 1000)
	if pr >= 2.0:
		BlackjackDraw.rect(ci, cx + po.x + 1.0, cy + po.y - 2.0, 1.0, 1.0, WHITE)


static func _mouth(ci: CanvasItem, u: float, look: Dictionary, f: Dictionary) -> void:
	var mw := maxf(3.0, _p(7.0 * float(f.get("mouth_w", 1.0)), u))
	var cx := roundf(float(f.get("mouth_x", 0.0)) * u)
	var y0 := _p(11.5, u)
	var curve := float(f.get("mouth_curve", 0.0))
	var skew := float(f.get("mouth_skew", 0.0))
	var open := float(f.get("mouth_open", 0.0))
	var th := maxf(2.0 if u < LOW_U else 1.0, roundf(1.6 * u))
	var t := maxf(1.0, roundf(u))
	var amp := maxf(3.6 * u, 2.6)  # how far a smile or frown bends (never under 2.6 pixels, so it reads at low detail)
	var samp := maxf(3.0 * u, 2.0)
	if float(f.get("grit", 0.0)) > 0.5:
		var gh := maxf(3.0, _p(5.5, u))
		BlackjackDraw.rect(ci, cx - mw - t, y0 - gh * 0.5 - t, 2.0 * mw + 2.0 * t + 1.0, gh + 2.0 * t, INK)
		BlackjackDraw.rect(ci, cx - mw, y0 - gh * 0.5, 2.0 * mw + 1.0, gh, WHITE)
		BlackjackDraw.rect(ci, cx - mw, y0 - 0.5, 2.0 * mw + 1.0, 1.0, INK)
		var x := -mw + maxf(2.0, _p(3.5, u))
		while x < mw - 1.0:
			BlackjackDraw.rect(ci, cx + x, y0 - gh * 0.5, 1.0, gh, INK)
			x += maxf(2.0, _p(3.5, u))
		return
	if open > 0.12:
		var h := maxf(3.0, _p(2.0 + open * 9.0, u))
		if curve > 0.25:  # a D-shaped grin: flat on top, round below
			var rows := int(h)
			for j in range(-1, rows + 2):
				var k := clampf(float(j) / (h + 0.5), 0.0, 1.0)
				var hwi := floorf(mw * sqrt(maxf(0.0, 1.0 - k * k)) + 0.5) + (t if j >= 0 else t)
				BlackjackDraw.rect(ci, cx - hwi, y0 + j - 1.0, 2.0 * hwi + 1.0, 1.0, INK)
			for j in range(0, rows + 1):
				var k := clampf(float(j) / (h + 0.5), 0.0, 1.0)
				var hwi := floorf(mw * sqrt(maxf(0.0, 1.0 - k * k)) + 0.5)
				var col := MOUTH_IN
				if float(f.get("teeth", 0.0)) > 0.5 and j < maxi(2, int(h * 0.38)):
					col = WHITE
				elif j >= rows - 2 and h >= 6.0:
					col = TONGUE
				BlackjackDraw.rect(ci, cx - hwi, y0 + j - 1.0, 2.0 * hwi + 1.0, 1.0, col)
		else:  # an O
			var ry := h * 0.5
			BlackjackDraw.ell_o(ci, cx, y0 + ry * 0.4, mw, ry, MOUTH_IN, INK, t)
			if ry >= 4.0:
				BlackjackDraw.ell(ci, cx, y0 + ry * 0.4 + ry * 0.5, maxf(1.0, mw * 0.6), maxf(1.0, ry * 0.4), TONGUE)
		return
	var x := -mw
	while x <= mw:
		var tt := x / mw
		var side := tt * signf(skew) if skew != 0.0 else 1.0
		var cw := 1.0 if side >= 0.0 else 0.15
		var y := y0 - curve * amp * tt * tt * cw - (skew * maxf(0.0, tt) * samp if skew > 0.0 else 0.0) + (skew * maxf(0.0, -tt) * samp if skew < 0.0 else 0.0)
		BlackjackDraw.rect(ci, cx + x, roundf(y), 1.0, th, INK)
		x += 1.0


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
			_arm(ci, who, c, u, look, sh, el, hp, String(po["kind"]), float(po["ang"]), float(po["k"]), side, dk)


static func _arm(ci: CanvasItem, who: String, c: Vector2, u: float, look: Dictionary, sh: Vector2, el: Vector2, hp: Vector2, kind: String, ang: float, k: float, side: float, dk: bool) -> void:
	var g := maxf(1.0, roundf(u)) if dk else 0.0
	var cloth: Color = look["cloth"]
	var shade: Color = look["cloth_shade"]
	var skin: Color = look["skin"]
	var fore_skin: bool = look["forearm_skin"]
	var s := c + Vector2(roundf(sh.x * u), roundf(sh.y * u))
	var e := c + Vector2(roundf(el.x * u), roundf(el.y * u))
	var h := c + Vector2(roundf(hp.x * u), roundf(hp.y * u))
	var wu := 10.0 * u
	var wf := 8.4 * u
	var ink := INK
	BlackjackDraw.limb(ci, s, e, wu + 2.0 * g, wu - 0.6 * u + 2.0 * g, ink if dk else cloth)
	if not dk:
		BlackjackDraw.limb(ci, s.lerp(e, 0.45), e, wu * 0.4, wu * 0.35, shade)
	var fcol: Color = skin if fore_skin else cloth
	var ee := e
	var fdir := (h - e).normalized() if (h - e).length() > 0.5 else Vector2(0.0, 1.0)
	BlackjackDraw.limb(ci, ee, h, wf + 2.0 * g, wf - 0.8 * u + 2.0 * g, ink if dk else fcol)
	if fore_skin:  # rolled sleeve at the elbow
		BlackjackDraw.limb(ci, ee - fdir * 1.0, ee + fdir * maxf(3.0, 5.0 * u), wf + 3.4 * u + 2.0 * g, wf + 3.4 * u + 2.0 * g, ink if dk else cloth)
		if not dk:
			BlackjackDraw.limb(ci, ee + fdir * maxf(3.0, 5.0 * u) - fdir, ee + fdir * maxf(3.0, 5.0 * u), wf + 3.4 * u, wf + 3.4 * u, look["cloth_shade"])
	elif not dk:
		var cuff: Color = look["accent"] if who == "npc_a" else Color("e8d8c8")
		BlackjackDraw.limb(ci, h - fdir * maxf(4.0, 6.0 * u), h - fdir * maxf(2.0, 3.0 * u), wf + 0.8 * u, wf + 0.8 * u, cuff)
	_hand(ci, h, ang, kind, k * 1.45, u, ink if dk else skin, g, side, skin if dk else look["skin_shade"])


## One hand at `p` with fingers pointing along `ang`. Kinds: `flat` (mitten and thumb), `fist`, `point` (index finger out), `open` (fanned fingers), `claw` (curled fingers).
## Drawn in two passes: `g` > 0 is the outline pass (every shape grown by g pixels, drawn in `col`), 0 the fill pass.
static func _hand(ci: CanvasItem, p: Vector2, ang: float, kind: String, k: float, u: float, col: Color, g: float, side: float, shade_col: Color) -> void:
	var d := Vector2(cos(ang), sin(ang))
	var n := Vector2(-d.y, d.x)
	var q := u * k
	var gg := g * 2.0
	match kind:
		"point":
			BlackjackDraw.limb(ci, p - d * 1.0 * q, p + d * 1.5 * q, 9.5 * q + gg, 9.5 * q + gg, col)
			BlackjackDraw.limb(ci, p + d * 3.0 * q, p + d * 17.0 * q, 4.2 * q + gg, 3.6 * q + gg, col)
			BlackjackDraw.limb(ci, p + n * side * 3.0 * q, p + n * side * 5.0 * q + d * 4.0 * q, 3.2 * q + gg, 3.0 * q + gg, col)
		"fist":
			BlackjackDraw.limb(ci, p - d * 1.0 * q, p + d * 2.0 * q, 10.0 * q + gg, 10.0 * q + gg, col)
			BlackjackDraw.limb(ci, p + n * side * 2.0 * q + d * 2.0 * q, p + n * side * 5.0 * q + d * 5.0 * q, 3.2 * q + gg, 3.0 * q + gg, col)
		"open", "claw":
			var fl := 10.0 if kind == "open" else 7.5
			BlackjackDraw.limb(ci, p - d * 1.0 * q, p + d * 2.0 * q, 9.0 * q + gg, 9.0 * q + gg, col)
			var spread := [-0.42, -0.14, 0.14, 0.42] if kind == "open" else [-0.2, -0.07, 0.07, 0.2]
			for a: float in spread:
				var fd := Vector2(cos(ang + a), sin(ang + a))
				BlackjackDraw.limb(ci, p + d * 3.0 * q + n * (a * 9.0 * q), p + fd * fl * q + n * (a * 3.0 * q), 2.9 * q + gg, 2.6 * q + gg, col)
			var td := Vector2(cos(ang - side * 1.2), sin(ang - side * 1.2))
			BlackjackDraw.limb(ci, p + n * side * 3.5 * q, p + td * 8.0 * q + n * side * 2.0 * q, 3.4 * q + gg, 3.0 * q + gg, col)
		_:  # flat: a palm and four fingers held together, the thumb out to the side
			BlackjackDraw.limb(ci, p - d * 2.0 * q, p + d * 2.0 * q, 9.6 * q + gg, 9.2 * q + gg, col)
			for fo: float in [-3.3, -1.1, 1.1, 3.3]:
				var fl2 := 8.5 - absf(fo) * 0.45
				BlackjackDraw.limb(ci, p + d * 2.0 * q + n * fo * q, p + d * fl2 * q + n * fo * 1.05 * q, 2.6 * q + gg, 2.4 * q + gg, col)
			BlackjackDraw.limb(ci, p + n * side * 4.0 * q - d * 1.0 * q, p + n * side * 6.5 * q + d * 3.0 * q, 3.4 * q + gg, 3.0 * q + gg, col)
	if g == 0.0 and kind == "fist":
		for fi in 3:
			var off := (float(fi) - 1.0) * 2.7 * q
			BlackjackDraw.limb(ci, p + n * off + d * 1.2 * q, p + n * off + d * 2.8 * q, 1.0, 1.0, shade_col)


# ------------------------------------------------------------------ the player's hands

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
			for sx in [-1.0, 1.0]:
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
	BlackjackDraw.poly_o(ci, pts, LINING, INK, maxf(1.0, roundf(u)))
	BlackjackDraw.rect(ci, p.x - 1.0, p.y - h * 0.8, 1.0, h * 0.6, Color("a8a8ba"))


static func _phand_pair(ci: CanvasItem, size: Vector2, u: float, lh: Dictionary, rh: Dictionary, wad: float) -> void:
	for pass_i in 2:
		var dk := pass_i == 0
		for si in 2:
			var po: Dictionary = lh if si == 0 else rh
			var side := -1.0 if si == 0 else 1.0
			var w: Vector2 = po["w"]
			if w.y > size.y + 60.0 * u:
				continue
			var g := maxf(1.0, roundf(u)) if dk else 0.0
			var ww := 21.0 * u
			var wr := Vector2(roundf(w.x), roundf(w.y))
			# a sleeve in two parts: the upper arm from below the picture to an elbow bent outward, then the forearm to the cuff
			var anchor := Vector2(w.x + (w.x - size.x * 0.5) * 0.35 + side * 26.0 * u, size.y + 70.0 * u)
			var elbow := anchor.lerp(wr, 0.5) + Vector2(side * 15.0 * u, 8.0 * u)
			var wrist := wr + Vector2(0.0, 3.0 * u)
			BlackjackDraw.limb(ci, anchor, elbow, ww * 1.75 + 2.0 * g, ww * 1.3 + 2.0 * g, INK if dk else SLEEVE)
			BlackjackDraw.limb(ci, elbow, wrist, ww * 1.3 + 2.0 * g, ww * 0.88 + 2.0 * g, INK if dk else SLEEVE)
			if not dk:
				var fd := (wrist - elbow).normalized()
				var fn := Vector2(-fd.y, fd.x) * (1.0 if Vector2(-fd.y, fd.x).x * side > 0.0 else -1.0)
				var ud := (elbow - anchor).normalized()
				var un := Vector2(-ud.y, ud.x) * (1.0 if Vector2(-ud.y, ud.x).x * side > 0.0 else -1.0)
				BlackjackDraw.limb(ci, anchor + un * ww * 0.55, elbow + un * ww * 0.4, ww * 0.32, ww * 0.26, SLEEVE_LIGHT)
				BlackjackDraw.limb(ci, elbow + fn * ww * 0.38, wrist - fd * 6.0 * u + fn * ww * 0.24, ww * 0.26, ww * 0.18, SLEEVE_LIGHT)
				# the crease inside the elbow
				BlackjackDraw.limb(ci, elbow - fn * ww * 0.45 - fd * 3.0 * u, elbow - fn * ww * 0.2 + fd * 4.0 * u, maxf(1.0, 2.0 * u), maxf(1.0, 1.5 * u), SLEEVE_DARK)
				# the shirt cuff and its button
				BlackjackDraw.limb(ci, wrist - fd * 6.0 * u, wrist - fd * 1.0 * u, ww * 0.82, ww * 0.82, CUFF)
				BlackjackDraw.rect(ci, wrist.x - fd.x * 4.0 * u + fn.x * ww * 0.2, wrist.y - fd.y * 4.0 * u + fn.y * ww * 0.2, maxf(1.0, 2.0 * u), maxf(1.0, 2.0 * u), SLEEVE_DARK)
			_hand(ci, wr, float(po["ang"]), String(po["kind"]), float(po["k"]), u, INK if dk else GLOVE_SKIN, g, side, Color("a06f48"))
	if wad > 0.5:  # the money in the hand: real fivers, the same notes that land on the table
		var lw: Vector2 = lh["w"]
		var rw: Vector2 = rh["w"]
		var mid := (lw + rw) * 0.5 if wad < 1.5 else rw
		mid += Vector2(0.0, -14.0 * u)
		for i in 3:
			MoneyDraw.draw_note(ci, 500, mid + Vector2(float(i) * 2.0 - 2.0, -float(i) * 3.0) * u, u * 1.25, (float(i) - 1.0) * 0.12)
