class_name StoryLight
extends RefCounted
## The nightclub's light as pure functions of song time and the stage's action state: the same maths the 2D StoryFx used (beam angles and strength, LED screen,
## floor tile chase, haze, mood dimming, ending fades), without any drawing, so the 3D StoryWorldFx and the tests read the same numbers. `stage` is a StoryStage;
## `t` is song time. Reduced effects softens (no kick flashes, half speed, calm fan), high contrast steps the room back, neither ever moves the camera.

static func e01(stage: StoryStage) -> float:
	return clampf(stage.energy / 100.0, 0.0, 1.0)


static func beats(stage: StoryStage, t: float) -> float:
	return t * stage.bpm / 60.0


## 1 on the beat, gone by the next eighth.
static func kick(stage: StoryStage, t: float) -> float:
	var b := beats(stage, t)
	return exp(-7.0 * (b - floor(b)))


static func pal(stage: StoryStage, i: int) -> Color:
	var p: Array = stage.palette_colors()
	return p[i % p.size()]


## Overall strength of the moving-head beams.
static func beam_intensity(stage: StoryStage, t: float) -> float:
	var e := e01(stage)
	var inten := (0.18 + 0.6 * e) * (0.6 if stage.reduced else 1.0) * (0.55 if stage.high_contrast else 1.0)
	if stage.is_active("bass_reveal", t) or stage.is_active("burst", t):
		inten += 0.3
	if stage.lean_tableau() == "legendary" or stage.tableau() == "legendary":
		inten += 0.2
	if stage.tableau() == "lost":
		inten *= 0.25
	if stage.flickering(t):
		inten *= 0.35 + 0.3 * (0.5 + 0.5 * sin(t * 9.0)) if not stage.reduced else 0.4
	if stage.beam_mode() == "off":
		inten *= clampf(1.0 - (t - stage.beam_since()) / 0.6, 0.0, 1.0) if t - stage.beam_since() < 4.0 else 0.0
	return inten


## The beam alpha: strength with a kick breath (a calmer one when reduced).
static func beam_alpha(stage: StoryStage, t: float) -> float:
	return clampf(beam_intensity(stage, t) * (0.7 + 0.3 * kick(stage, t) * (0.3 if stage.reduced else 1.0)), 0.0, 0.9)


## Sideways swing (radians) of fixture i.
static func fixture_angle(stage: StoryStage, i: int, t: float) -> float:
	var b := beats(stage, t)
	var since := t - stage.beam_since()
	if stage.reduced:  # reduced effects: the rig holds a calm fan that breathes over four bars, whatever the cue
		return (float(i) - 3.5) * 0.12 + 0.06 * sin(TAU * b / 16.0 + float(i) * 0.7)
	match stage.beam_mode():
		"sweep":
			return 0.55 * sin(TAU * b / 32.0 + float(i) * 0.8)
		"fan":
			return (float(i) - 3.5) * 0.15 + 0.08 * sin(b * 0.4 + float(i))
		"cross":
			var dirn := 1.0 if i % 2 == 0 else -1.0
			return dirn * (0.15 + 0.4 * (0.5 + 0.5 * sin(TAU * b / 24.0)))
		_:
			return 0.1 * sin(float(i) + since * 0.3)


## A short white flash on a drop (never in reduced effects), 0 outside it. The only strobe the light has: it is tied to the authored drop and burst actions.
static func strobe_at(stage: StoryStage, t: float) -> float:
	if stage.reduced:
		return 0.0
	var s := INF
	for name in ["bass_reveal", "burst"]:
		if stage.is_active(name, t):
			s = minf(s, stage.since(name, t))
	if s > 0.45:
		return 0.0
	return 0.3 * exp(-s * 9.0) * (0.5 if stage.high_contrast else 1.0)


## A soft swell off the floor for 1.6 s after a drop (2D: one bloom). 0..1.
static func bloom_at(stage: StoryStage, t: float) -> float:
	var since := INF
	for name in ["bass_reveal", "burst"]:
		if stage.is_active(name, t):
			since = minf(since, stage.since(name, t))
	if since > 1.6 or stage.tableau() == "lost":
		return 0.0
	var u := since / 1.6
	return (1.0 - u) * (1.0 - u) * (0.22 if stage.reduced else 0.45) * minf(since / 0.08, 1.0)


## The mood dimming: a quiet room is darker, a lost night darker still, a failed sequence dips for under a second, a flicker adds.
static func dim_at(stage: StoryStage, t: float) -> float:
	var dim := 0.4 if stage.tableau() == "lost" else clampf(0.32 - e01(stage) * 0.45, 0.0, 0.32)
	for p in stage.fx_pulses():
		var age: float = t - float(p["t0"])
		if age >= 0.0 and age < 0.9 and not p["passed"] and not stage.reduced:
			dim += 0.12 * (1.0 - age / 0.9)
	if stage.flickering(t):
		dim += 0.15
	return dim


## The ending fade: 0 while the set runs; after the last bar the lost night sinks into the dark over four seconds, a good night warms and settles, a legendary one stays bright.
static func fade_at(stage: StoryStage, t: float) -> float:
	var since := stage.since("ending", t)
	if since == INF or since < 0.0:
		return 0.0
	match stage.tableau():
		"lost":
			return clampf(since / 4.0, 0.0, 1.0) * 0.55
		"good":
			return clampf(since / 4.0, 0.0, 1.0) * 0.12
		_:
			return 0.0


## Haze strength (the two scrolling bands): the set's own breath plus a burst after a drop.
static func haze_alpha(stage: StoryStage, t: float) -> float:
	var burst := 0.0
	for b0 in stage.fx_bursts():
		if t >= float(b0):
			burst = maxf(burst, exp(-(t - float(b0)) / 3.2))
	return (0.06 + 0.1 * e01(stage) + 0.35 * burst) * (0.5 if stage.reduced else 1.0) * (0.35 if stage.high_contrast else 1.0)


## Colour and strength of the floor glow under the whole dance floor.
static func floor_glow(stage: StoryStage, t: float) -> float:
	var a := (0.04 + 0.13 * e01(stage)) * (0.5 + 0.5 * kick(stage, t)) * (0.4 if stage.reduced else 1.0)
	if stage.tableau() == "lost":
		a *= 0.2
	return a


## Strength of the woofer glow.
static func woofer_glow(stage: StoryStage, t: float) -> float:
	if stage.tableau() == "lost":
		return 0.0
	return kick(stage, t) * (0.5 + 0.5 * e01(stage)) * (1.0 if stage.woofer_pump() else 0.35) * (0.4 if stage.reduced else 1.0)


## The LED floor: brightness 0..0.85 of the tile (i, j) of a w x h grid whose centre is `c` metres from the circle... `p` is the tile centre in metres, `circle` the ring's centre, `h` a fixed
## random 0..1 per tile. Chases, ripples out of the circle at a drop or a pass, a sweep with the light wave, a slow breathing when quiet.
static func tile_alpha(stage: StoryStage, t: float, i: int, j: int, h: float, p: Vector2, circle: Vector2, floor_x: Vector2) -> float:
	return tile_alpha_ctx(tile_context(stage, t), i, j, h, p, circle, floor_x)


## Everything a floor tile's brightness needs that does not depend on the tile, worked out once per refresh.
static func tile_context(stage: StoryStage, t: float) -> Dictionary:
	var b := beats(stage, t)
	var ripple_t := -1.0
	for name in ["bass_reveal", "burst"]:
		if stage.is_active(name, t):
			ripple_t = maxf(ripple_t, stage.since(name, t))
	var last_pass := -INF
	for q in stage.fx_pulses():
		if q["passed"] and float(q["t0"]) <= t:
			last_pass = maxf(last_pass, float(q["t0"]))
	return {"e": e01(stage), "b": b, "beat": floorf(b), "kp": kick(stage, t), "reduced": stage.reduced, "t": t, "ripple_t": ripple_t, "last_pass": last_pass,
		"wave_u": stage.progress("light_wave", t),
		"level": (0.1 + 0.55 * e01(stage)) * (0.25 if stage.tableau() == "lost" else 1.0) * (0.55 if stage.reduced else 1.0) * (0.5 if stage.high_contrast else 1.0)}


static func tile_alpha_ctx(c: Dictionary, i: int, j: int, h: float, p: Vector2, circle: Vector2, floor_x: Vector2) -> float:
	var e: float = c["e"]
	var b: float = c["b"]
	var kp: float = c["kp"]
	var a := 0.0
	if c["reduced"]:
		a = 0.35 * (0.5 + 0.5 * sin(TAU * (b / 8.0) + float(i) * 0.6 + float(j) * 0.4))
	elif e < 0.3:
		a = 0.4 * maxf(0.0, sin(TAU * (b / 8.0 + h)))
	else:
		var lane := (i + j + int(c["beat"])) % 4
		a = (0.75 if lane == 0 else 0.0) * (0.45 + 0.55 * kp)
		if fposmod(h * 7.0 + float(c["beat"]) * 0.618, 1.0) < 0.12 + 0.18 * e:
			a = maxf(a, kp)
	var ripple_t: float = c["ripple_t"]
	var last_pass: float = c["last_pass"]
	var t: float = c["t"]
	var wave_u: float = c["wave_u"]
	if ripple_t >= 0.0 or t - last_pass < 1.2:
		var d := p.distance_to(circle)
		if ripple_t >= 0.0:
			a = maxf(a, 1.2 * exp(-pow((d - ripple_t * 5.0) / 1.2, 2.0)) * exp(-ripple_t * 0.35))
		if t - last_pass < 1.2:
			a = maxf(a, 0.8 * exp(-pow((d - (t - last_pass) * 7.0) / 1.0, 2.0)) * (1.0 - (t - last_pass) / 1.2))
	if wave_u >= 0.0:
		var wx := lerpf(floor_x.x - 2.0, floor_x.y + 2.0, wave_u)
		a = maxf(a, exp(-pow((p.x - wx) / 1.4, 2.0)))
	return clampf(a * float(c["level"]), 0.0, 0.85)


## The followspots: [{kind, at: Vector2 (ground x, z), color, size m}] for the hero, the sweep and the circle.
static func spots(stage: StoryStage, t: float) -> Array:
	var out: Array = []
	var crowd := stage.crowd
	if stage.is_active("spot_hero", t) and crowd.hero_id() != "":
		out.append({"kind": "hero", "at": crowd.actors[crowd.hero_id()]["pos"], "color": Color(1.0, 0.92, 0.7, 0.75), "size": 2.2})
	if stage.is_active("spot_sweep", t):
		var u := stage.progress("spot_sweep", t)
		var fx := crowd.floor_x
		out.append({"kind": "sweep", "at": Vector2(lerpf(fx.x + 0.5, fx.y - 0.5, u), crowd.circle_c.y + 1.0 * sin(u * PI)), "color": Color(0.8, 0.9, 1.0, 0.65), "size": 2.0})
	if stage.is_active("spot_circle", t):
		out.append({"kind": "circle", "at": crowd.circle_c, "color": Color(1.0, 0.85, 0.5, 0.7), "size": 3.4})
	return out


## The LED screen word at an ending ("" while the set runs), as stacked lines.
static func led_word(stage: StoryStage) -> Array:
	match stage.tableau():
		"legendary":
			return ["ENCORE!"]
		"good":
			return ["THANK", "YOU"]
		"lost":
			return ["GOOD", "NIGHT"]
	return []


## Brightness 0..1 of the LED dot at (u, v) (0..1 across, 0 top .. 1 bottom) for a screen mode.
static func led_value(mode: String, u: float, v: float, i: int, b: float, e: float, kp: float) -> float:
	match mode:
		"eq":
			var h := 0.12 + 0.88 * absf(sin(b * PI * 0.5 * (1.0 + float(i % 20) * 0.11) + float(i) * 1.7)) * (0.35 + 0.65 * e)
			h = clampf(h * (0.8 + 0.3 * kp), 0.0, 1.0)
			return 1.0 if 1.0 - v < h else 0.0
		"bars":
			var k := int(v * 6.0)
			var ww := 0.2 + 0.8 * absf(sin(b * 0.5 + float(k) * 0.9))
			return 0.9 if absf(u - 0.5) < ww * 0.5 else 0.0
		"rings":
			var d := Vector2((u - 0.5) * 3.6, v - 0.5).length()
			var best := 0.0
			for k in 4:
				var rad := fposmod(b * 0.25 + float(k) * 0.25, 1.0) * 1.9
				best = maxf(best, (1.0 - rad / 1.9) * clampf(1.0 - absf(d - rad) / 0.09, 0.0, 1.0))
			return best
		"wave":
			var best2 := 0.0
			for k in 3:
				var y := 0.5 + sin(u * TAU * (1.5 + float(k)) + b * 1.3 + float(k)) * (0.36 - 0.08 * float(k)) * (0.5 + 0.5 * e)
				best2 = maxf(best2, clampf(1.0 - absf(v - y) / 0.09, 0.0, 1.0))
			return best2
	return 0.0


## The LED screen's brightness scale (dimmer at a lost night and a quiet room).
static func led_dim(stage: StoryStage) -> float:
	return 0.35 if stage.tableau() == "lost" else lerpf(0.45, 1.0, e01(stage))


## Confetti: [{pos: Vector3-ish (x fraction 0..1 across the floor, y metres above the floor, z fraction), rot, color}] while it falls; empty outside.
static func confetti(stage: StoryStage, t: float, count: int) -> Array:
	var u := stage.progress("confetti", t)
	var out: Array = []
	if u < 0.0:
		return out
	var age := u * 5.0
	var n := mini(count, 24 if stage.reduced else 70)
	for i in n:
		var h := fposmod(sin(float(i) * 12.9898) * 43758.5453, 1.0)
		var h2 := fposmod(sin(float(i) * 78.233) * 12345.678, 1.0)
		var y := 3.4 - age * (0.55 + 0.8 * h2) + h2 * 0.8
		if y < 0.0:
			continue
		out.append({"u": h, "v": fposmod(h * 7.3 + h2, 1.0), "y": y, "sway": sin(age * 2.0 + float(i)) * 0.18, "color": pal(stage, i).lightened(0.3), "alpha": 1.0 - u * 0.5})
	return out


## Everything the post-process and the HUD need at song time t, in one dictionary.
static func post_state(stage: StoryStage, t: float) -> Dictionary:
	var q := 0.0
	var sick := 0.0
	if stage.player != null:
		q = stage.player.queasy_at(t)
		sick = stage.player.sick_at(t)
	var dim := clampf(dim_at(stage, t) * 0.8 + fade_at(stage, t) + 0.3 * sick, 0.0, 0.92)
	return {
		"queasy": 0.0 if stage.reduced else q,  # reduced effects keeps the picture steady: no warp, split or desaturation
		"sick": sick,
		"time": t,
		"dim": dim,
		"strobe": strobe_at(stage, t),
		"flash": bloom_at(stage, t) * 0.25,
		"vignette": 0.0 if stage.reduced else 0.5 * q,  # the steady vignette is a sprite over the image (StoryLowRes); the shader only breathes it in with the queasy look
	}
