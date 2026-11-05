class_name RunCardTable
extends RefCounted
## The day room's card table as the room shows it (docs/BLACKJACK_INTEGRATION.md, "The table in the room"): the table, its lamp, the empty chair and the three players of the
## close-up, drawn by the Story people's pixel rig (tools/minigames/make_world_table.py) and played here as loops of a sheet, two frames a beat, on the map's `cards_table`
## occluder in place of its still (StoryCrowdProp.drawer). Which loop shows follows the table's hotspot: `idle` (they play among themselves), `invite` (the table is on show:
## they look at you and wave you over), `pleased` (it is touched: arms up and grins until the block is judged), `welcome` (seated: until the close-up has risen over them), `refuse`
## (waved off: the dealer shakes his head, the others shrug, then they invite again); while the player is seated the close-up owns the table and the room's version is not
## drawn. Everything is a pure function of song time and the hotspot state (`mood_of`, `frame_of`); nothing is generated at run time.

const SHEET := "res://assets/minigames/blackjack/world_table_sheet.png"
const META := "res://assets/minigames/blackjack/world_table_sheet.json"
const OCCLUDER := "cards_table"  # the map's occluder the table is drawn on
const REFUSE_BEATS := 4.0  # the refusal plays once over this many beats from the decision, then they invite again
const BURST_BEATS := 0.5  # the touch: the first pose of `pleased` (arms up) shows at once, then the loop follows the beat
const LOD2_BELOW := 0.72  # screen pixels per sheet pixel under which the half-size frames are drawn (a far table stays clean pixels)
const GAIN := 1.3  # the people's light, as their shader takes it (src/story/story_people.gdshader: gain, min_light, the 1.12 ceiling)
const MIN_LIGHT := 0.55
const MAX_LIGHT := 1.12

var tex: Texture2D
var meta: Dictionary = {}
var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var mood: Dictionary = {"loop": "idle", "t0": 0.0}  # what the table shows now ({loop, t0}; loop "hidden": nothing), set by the run each frame
var now := 0.0  # the song time the mood was set at
var _lamp: Dictionary = {}  # prop instance id -> the static lamp light at the table (looked up once)


func _init() -> void:
	if ResourceLoader.exists(SHEET):
		tex = load(SHEET)
	var f := FileAccess.open(META, FileAccess.READ)
	if f != null:
		var d: Variant = JSON.parse_string(f.get_as_text())
		meta = d if typeof(d) == TYPE_DICTIONARY else {}


func ok() -> bool:
	return tex != null and meta.has("lods")


## True for the hotspot the table's players answer to: the one whose success sits the player at an activity.
static func is_table(h: Dictionary) -> bool:
	return str((h.get("on_success", {}) as Dictionary).get("activity", "")) != ""


## What the players do at song time `t`. `entry`: the table's hotspot_items() entry on show now ({} when it is not on show); `last_commit`: {t, success} of the table's latest
## decision ({} none); `mg_state`: the minigame controller's state ("" | "entering" | "active" | "leaving"); `closeup_up`: the close-up's picture covers the table now
## (`closeup_up`, below: false while it rises at the sitting down and sinks at the getting up, so the room's table is not missing behind it). Returns {loop, t0}
## (t0: when the loop started).
static func mood_of(entry: Dictionary, last_commit: Dictionary, mg_state: String, t: float, p_beat_s: float, p_closeup_up := true) -> Dictionary:
	if mg_state == "active" or mg_state == "leaving":
		if p_closeup_up:
			return {"loop": "hidden", "t0": 0.0}  # seated: the close-up is the table
		if mg_state == "active" and not last_commit.is_empty() and bool(last_commit["success"]):
			return {"loop": "welcome", "t0": float(last_commit["t"])}  # the close-up still rising over them
		return {"loop": "invite", "t0": 0.0}  # the close-up sinking away: the table is free again
	if not last_commit.is_empty() and t >= float(last_commit["t"]):
		if bool(last_commit["success"]) and mg_state == "entering":
			return {"loop": "welcome", "t0": float(last_commit["t"])}
		if not bool(last_commit["success"]) and t - float(last_commit["t"]) < REFUSE_BEATS * p_beat_s:
			return {"loop": "refuse", "t0": float(last_commit["t"])}
	if not entry.is_empty():
		if str(entry["state"]) == "selected":
			return {"loop": "pleased", "t0": float(entry["t_state"])}
		return {"loop": "invite", "t0": 0.0}
	return {"loop": "idle", "t0": 0.0}


## The frame of `loop` at song time `t` (0 .. n - 1 for a loop of n frames, FPB a beat): the looping moods follow the song's own beats (every pose lands on a half beat);
## `pleased` shows its first pose (arms up) for the first half beat after the touch; the one-shot `refuse` runs from its start and holds its last frame. Reduced motion: the
## first (key) pose only.
static func frame_of(loop: String, t0: float, t: float, n: int, fpb: int, p_beat_s: float, p_reduced: bool) -> int:
	if n <= 0:
		return 0
	if p_reduced:
		return 0
	if loop == "refuse":
		return clampi(int(floor((t - t0) / p_beat_s * float(fpb))), 0, n - 1)
	if loop == "pleased" and t - t0 < BURST_BEATS * p_beat_s:
		return 0
	return posmod(int(floor(t / p_beat_s * float(fpb) + 1.0e-6)), n)


## Whether the close-up's picture is up over the room at song time `t`, from the activity's `state()` snapshot ({} none): the blackjack view raises it over its first
## RISE_BEATS when the player sits and lowers it over the last SINK_BEATS of the getting up (src/minigames/blackjack/blackjack_view.gd `_pose`); it counts as up from half
## way. A pure function of the snapshot and song time.
static func closeup_up(snap: Dictionary, t: float, p_beat_s: float) -> bool:
	if snap.is_empty():
		return false
	var t0 := float(snap.get("phase_t0", 0.0))
	match str(snap.get("phase", "")):
		"sitting":
			return t - t0 >= 0.5 * BlackjackView.RISE_BEATS * p_beat_s
		"leaving":
			var pile: Dictionary = snap.get("pile", {})
			var end := t0
			if str(pile.get("via", "")) == "pockets":
				end = float(pile.get("t0", t0)) + float(pile.get("dur", 0.0))
			return t < end - 0.5 * BlackjackView.SINK_BEATS * p_beat_s
	return true


func set_mood(m: Dictionary, t: float) -> void:
	mood = m
	now = t


## The sheet rect of the frame on show for a view `lod` ("1" full size, "2" half): Rect2() when nothing is drawn.
func region(lod: String) -> Rect2:
	var loop := str(mood["loop"])
	var e: Dictionary = (meta.get("lods", {}) as Dictionary).get(lod, {})
	var rects: Array = (e.get("loops", {}) as Dictionary).get(loop, [])
	if rects.is_empty():
		return Rect2()
	var r: Array = rects[frame_of(loop, float(mood["t0"]), now, rects.size(), int(meta.get("frames_per_beat", 2)), beat_s, reduced)]
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))


## StoryCrowdProp.drawer for the table's occluder: the frame in the light a person standing at the table gets (the room's song-time light times the lamps around it, as
## the dancers are lit), then the lamp's glow unlit over it. The prop's own `items` (placed by the crowd) give the rect on screen.
func draw_on(prop: StoryCrowdProp) -> void:
	if prop.items.is_empty() or not ok() or str(mood["loop"]) == "hidden":
		return
	var rect: Rect2 = prop.items[0][1]
	var lod := "1"
	var full: Dictionary = (meta["lods"] as Dictionary).get("1", {})
	var fw := float((full.get("glow", [0, 0, 1, 1]) as Array)[2])
	if rect.size.x / maxf(fw, 1.0) < LOD2_BELOW and (meta["lods"] as Dictionary).has("2"):
		lod = "2"
	var reg := region(lod)
	if reg.size.x <= 0.0:
		return
	prop.draw_texture_rect_region(tex, rect, reg, _light(prop))
	var g: Array = ((meta["lods"] as Dictionary)[lod] as Dictionary).get("glow", [])
	if g.size() == 4:
		prop.draw_texture_rect_region(tex, rect, Rect2(float(g[0]), float(g[1]), float(g[2]), float(g[3])), Color(1, 1, 1, 1))


func _light(prop: StoryCrowdProp) -> Color:
	var crowd := prop.get_parent() as StoryCrowd
	var o: Dictionary = prop.get_meta("def", {})
	if crowd == null or o.is_empty() or not crowd.light_fn.is_valid():
		return Color.WHITE
	var sec := str(o["sector"])
	var at: Vector2 = o["at"]
	var key := prop.get_instance_id()
	if not _lamp.has(key):
		_lamp[key] = crowd.light_fn.call(sec, at, false)
	var l: Color = (crowd.light_fn.call(sec, at, true) as Color) * (_lamp[key] as Color) * GAIN
	var lo := 0.8 if high_contrast else MIN_LIGHT
	return Color(clampf(l.r, lo, MAX_LIGHT), clampf(l.g, lo, MAX_LIGHT), clampf(l.b, lo, MAX_LIGHT), 1.0)


## Puts the table on every crowd prop of `stage` that stands for the map's `cards_table` occluder. Returns how many it took.
func attach(stage: StoryStage) -> int:
	var n := 0
	for rid in stage.crowds:
		for p in (stage.crowds[rid] as StoryCrowd).props:
			var pr := p as StoryCrowdProp
			if pr.kind == "occluder" and str((pr.get_meta("def", {}) as Dictionary).get("id", "")) == OCCLUDER:
				pr.drawer = draw_on
				n += 1
	return n
