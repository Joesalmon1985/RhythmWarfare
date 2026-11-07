class_name StoryHeralds
extends RefCounted
## The heralds of the quest entrances (lead ruling 25, docs/art/HERALDS.md): a character from the quest standing beside its entrance and gesturing towards it on the beat, with
## the quest's mark (a small lit sign in its colour) over the entrance. A herald is scenery of its entrance: it comes from the entrance hotspot's `herald` block (written by
## tools/run/heralds.py), it is never a hotspot, never touched, never counted, and takes no part in routing. HotspotView plays it while the entrance is staged (on offer in this
## visit), so a herald behind a flag appears when its entrance does.
##
## How it stands in the world: like the day room's card table (RunCardTable), a StoryCrowdProp of the crowd of the room it stands in, as an "occluder" the crowd projects, culls
## by sector and sorts by distance with the dancers every frame; its `drawer` draws the herald's frame (assets/story/heralds, tools/story/art/heralds.py) in the light a person
## standing there gets. The frames point to screen right; the drawer mirrors them whenever the entrance is on the herald's left on screen, so the gesture always points at it.
## A `self` herald (the Warehouse wizard, who IS the entrance) plays the gesture on the entrance's own billboard while the entrance is on offer and not the current choice
## (in place of the choice layer's sad slump: from the scene's first beat he points the way down); once touched he is the current choice and beckons happy as the choice
## layer says, and once another option has been taken (declined) its look is left alone.
## Everything is a pure function of song time and the camera: the same frame at the same time.

const DOC := "res://assets/story/heralds/heralds.json"
const GAIN := 1.3  # the people's light, as their shader takes it (story_people.gdshader: gain, min_light, the 1.12 ceiling)
const MIN_LIGHT := 0.55
const MAX_LIGHT := 1.12
const LOD2_BELOW := 0.72  # screen pixels per sheet pixel under which the half-size frames are drawn
const FOG_MIX := 0.82  # how far the depth fog takes a herald into the dark at its fullest (story_people.gdshader: fog * 0.82)
const POOL_M := 1.1  # the radius of the quest's light on the floor round the entrance
const FLIP_DEAD := 0.08  # metres: the entrance this close to straight ahead of the herald keeps the last facing (no flicker)
const QUESTS := ["dungeon", "gospel", "squadron", "ember"]
const POINT_FRAME := 4  # reduced motion: the point held still
const LOOK_KNEE := 0.5  # metres: the lowest of a herald a camera look tips the head for
const ENTRANCE_BELOW_MARK := 1.3  # metres: what a camera holds of an entrance reaches this far below its mark (the mark hangs 1.05 m over the anchor)

static var _doc: Dictionary = {}
static var _tex: Texture2D = null
static var _self_tex: Dictionary = {}

var stage: StoryStage
var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var now := 0.0
var _recs: Dictionary = {}  # hotspot id -> {herald: prop, mark: prop, block, on}
var _seen: Dictionary = {}
var _flip: Dictionary = {}  # hotspot id -> bool (last facing)


static func doc() -> Dictionary:
	if _doc.is_empty() and FileAccess.file_exists(DOC):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(DOC))
		_doc = d if typeof(d) == TYPE_DICTIONARY else {}
	return _doc


static func sheet() -> Texture2D:
	if _tex == null and not doc().is_empty() and ResourceLoader.exists(str(doc()["sheet"])):
		_tex = load(str(doc()["sheet"]))
	return _tex


static func self_tex(quest: String, i: int, left: bool) -> Texture2D:
	var key := "%s|%d|%s" % [quest, i, left]
	if not _self_tex.has(key):
		var m: Dictionary = (doc().get("heralds", {}) as Dictionary).get(quest, {})
		var lst: Array = m.get("self_frames_left" if left else "self_frames", [])
		_self_tex[key] = load(str(lst[i])) if i < lst.size() and ResourceLoader.exists(str(lst[i])) else null
	return _self_tex[key]


## The frame of the loop at song time `t`: frames_per_beat a beat, looping every loop_beats; reduced motion holds the point.
static func frame_of(t: float, p_beat_s: float, p_reduced := false) -> int:
	var d := doc()
	var n := int(d.get("frames_per_beat", 4)) * int(d.get("loop_beats", 2))
	if p_reduced or n <= 0:
		return mini(POINT_FRAME, maxi(n - 1, 0))
	return posmod(int(floor(t / p_beat_s * float(d.get("frames_per_beat", 4)) + 1.0e-6)), n)


## Whether the gesture is mirrored: the entrance (`toward`) is on the herald's (`at`) left as the camera of `yaw` sees it. `last`: the previous answer, kept when it is straight ahead.
static func flip_of(at: Vector2, toward: Vector2, yaw: float, last := false) -> bool:
	var d := (toward - at).dot(StoryProjector.right(yaw))
	if absf(d) < FLIP_DEAD:
		return last
	return d < 0.0


## A herald block's errors (the tests check every shipped one): [] when it is good.
static func validate(block: Variant, where: String) -> Array:
	var errs: Array = []
	if typeof(block) != TYPE_DICTIONARY:
		return ["%s: herald must be an object" % where]
	var b: Dictionary = block
	if str(b.get("quest", "")) not in QUESTS:
		errs.append("%s: herald.quest '%s' is not one of %s" % [where, b.get("quest", ""), QUESTS])
	elif not (doc().get("heralds", {}) as Dictionary).has(str(b["quest"])):
		errs.append("%s: no herald art for %s" % [where, b["quest"]])
	for k in b:
		if str(k) not in ["quest", "at", "toward", "mark_y", "self", "gate", "mark_at"]:
			errs.append("%s: herald.%s is not a field" % [where, k])
	if typeof(b.get("toward", null)) != TYPE_ARRAY or (b["toward"] as Array).size() != 2:
		errs.append("%s: herald.toward must be [x, z]" % where)
	if b.has("self"):
		if typeof(b["self"]) != TYPE_STRING or str(b["self"]) == "":
			errs.append("%s: herald.self names the entrance's own billboard thing" % where)
		elif ((doc().get("heralds", {}) as Dictionary).get(str(b.get("quest", "")), {}) as Dictionary).get("self_frames", []).is_empty():
			errs.append("%s: the %s herald has no billboard frames to play on a thing" % [where, b.get("quest", "")])
	elif typeof(b.get("at", null)) != TYPE_ARRAY or (b["at"] as Array).size() != 2:
		errs.append("%s: herald.at must be [x, z]" % where)
	if b.has("mark_at") and (typeof(b["mark_at"]) != TYPE_ARRAY or (b["mark_at"] as Array).size() != 2):
		errs.append("%s: herald.mark_at must be [x, z]" % where)
	if b.has("gate") and typeof(b["gate"]) != TYPE_BOOL:
		errs.append("%s: herald.gate is true or false" % where)
	if typeof(b.get("gate", false)) == TYPE_BOOL and b.get("gate", false) and b.has("mark_at"):
		errs.append("%s: a gate stands at the entrance under its mark: no mark_at with a gate" % where)
	return errs


## Where the entrance's mark (and its light pool, and its gate) stands: `mark_at` when the block gives one (a self herald that carries its own sign), else what it points at.
static func mark_point(b: Dictionary) -> Vector2:
	var a: Array = b.get("mark_at", b["toward"])
	return Vector2(float(a[0]), float(a[1]))


## What a camera look holds in the picture for the herald block `b` of an entrance (the visibility rule, docs/art/HERALDS.md): the entrance (its ground and the top of its
## mark) and the herald (knees and head), as `face` points [x, z, keep, height in world metres] (StoryPlayer `face` look). A `self` herald stands where its thing is (`at`).
## Heights come from the floors of `map` (the balcony is 2.6 m up). [] when the block cannot be placed.
static func look_points(b: Dictionary, map: StoryMap, keep := 1.0) -> Array:
	if map == null or typeof(b.get("toward", null)) != TYPE_ARRAY:
		return []
	var toward := mark_point(b)
	var out: Array = []
	var ft := _floor_at(map, toward)
	var my := float(b.get("mark_y", 1.5))
	out.append([toward.x, toward.y, keep, ft + maxf(0.0, my - ENTRANCE_BELOW_MARK)])  # (the entrance itself: what the mark hangs over)
	out.append([toward.x, toward.y, keep, ft + my + 0.25])  # (the top of the mark)
	if typeof(b.get("at", null)) == TYPE_ARRAY:
		var a: Array = b["at"]
		var at := Vector2(float(a[0]), float(a[1]))
		var fa := _floor_at(map, at)
		var m: Dictionary = (doc().get("heralds", {}) as Dictionary).get(str(b.get("quest", "")), {})
		out.append([at.x, at.y, keep, fa + LOOK_KNEE])  # (the knees, not the feet: a look tips the head down far enough for these, and a near herald's feet may go under the picture's edge)
		out.append([at.x, at.y, keep, fa + float(m.get("height_m", 1.7))])
	return out


static func _floor_at(map: StoryMap, p: Vector2) -> float:
	var sid := map.sector_at(p)
	return float(map.sector(sid).get("floor", 0.0)) if sid != "" else 0.0


func _init(p_stage: StoryStage = null) -> void:
	stage = p_stage


func begin_frame(t: float) -> void:
	now = t
	_seen = {}


## The entrance `h` (a staged option in `role`) is on offer this frame: its herald stands and gestures.
func put(h: Dictionary, role: String) -> void:
	var b: Dictionary = h.get("herald", {})
	if b.is_empty() or stage == null or stage.map == null or not validate(b, "").is_empty():
		return
	var id := str(h["id"])
	_seen[id] = true
	var tw: Array = b["toward"]
	var toward := Vector2(float(tw[0]), float(tw[1]))
	if b.has("self"):
		_pose_self(id, b, toward, role)
	var rec: Dictionary = _recs.get(id, {})
	var key_prop: Variant = rec.get("mark" if b.has("self") else "herald", null)
	if rec.is_empty() or key_prop == null or not is_instance_valid(key_prop) or not is_instance_valid(rec["crowd"]) or not (rec["crowd"] as StoryCrowd).props.has(key_prop):
		rec = _make(id, b, toward)
		if rec.is_empty():
			return
		_recs[id] = rec
	rec["on"] = true


func end_frame() -> void:
	for id in _recs:
		(_recs[id] as Dictionary)["on"] = _seen.has(id)


## Every herald taken down (a new stage, the run over).
func clear() -> void:
	for id in _recs:
		var rec: Dictionary = _recs[id]
		for k in ["herald", "mark"]:
			var p: Variant = rec.get(k, null)
			if p != null and is_instance_valid(p):
				var c: StoryCrowd = rec["crowd"]
				if is_instance_valid(c):
					c.props.erase(p)
				(p as Node).queue_free()
	_recs = {}


## The ids of the heralds standing now (the tests and the shots read it).
func shown() -> Array:
	var out: Array = []
	for id in _recs:
		if bool((_recs[id] as Dictionary)["on"]):
			out.append(id)
	return out


func _make(id: String, b: Dictionary, toward: Vector2) -> Dictionary:
	var m: Dictionary = (doc().get("heralds", {}) as Dictionary).get(str(b["quest"]), {})
	if m.is_empty() or sheet() == null:
		return {}
	var a: Array = b["toward"] if b.has("self") else b["at"]  # (a `self` herald is its thing (its `at` only tells the camera where): only its mark is made, over what it points at)
	var at := Vector2(float(a[0]), float(a[1]))
	var sec := stage.map.sector_at(at)
	var room := stage.map.room_of(sec) if sec != "" else ""
	var crowd: StoryCrowd = crowd_for_room(room)
	if crowd == null or sec == "":
		return {}
	var rec := {"herald": null, "crowd": crowd, "block": b, "on": true, "at": at, "toward": toward, "quest": str(b["quest"])}
	if not b.has("self"):
		rec["herald"] = _herald_prop(id, m, sec, at, crowd)
	var mpt := mark_point(b)
	var msec := stage.map.sector_at(mpt)
	if msec != "" and (m.get("mark", {}) as Dictionary).size() > 0:
		var mp := StoryCrowdProp.new()
		mp.kind = "occluder"
		mp.name = "HeraldMark_" + id.replace(".", "_")
		mp.set_meta("def", {"id": "herald_mark:" + id, "sector": msec, "at": mpt, "width": 0.4, "height": float(b.get("mark_y", 1.5)) + 0.25})
		mp.set_meta("tex", sheet())
		mp.set_meta("herald", id)
		mp.drawer = _draw_mark
		mp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		crowd.add_child(mp)
		crowd.props.append(mp)
		rec["mark"] = mp
	return rec


## The crowd that is drawn while the camera is in `room`: the room's own crowd; for a room without one (the Hospital's day room and quiet room hold no crowd of their own) the crowd whose
## actors have a home in that room's sectors (StoryStage._enter_room keeps showing the crowd of the last room that has one, and that is where the room's own people are drawn); else the crowd
## shown now (the room the rail came from); else main. A prop in any other crowd would never be drawn there.
func crowd_for_room(room: String) -> StoryCrowd:
	if stage == null:
		return null
	if stage.crowds.has(room):
		return stage.crowds[room]
	if stage.map != null:
		for vid in stage.crowds:
			var c: StoryCrowd = stage.crowds[vid]
			for id in c.actors:
				var h: Dictionary = stage.map.home(str(id))
				if not h.is_empty() and stage.map.room_of(str(h["sector"])) == room:
					return c
	if stage.crowds.has(stage.current_view):
		return stage.crowds[stage.current_view]
	return stage.crowds.get("main", null)


func _herald_prop(id: String, m: Dictionary, sec: String, at: Vector2, crowd: StoryCrowd) -> StoryCrowdProp:
	var h_m := float(m.get("height_m", 1.7))
	var hp := StoryCrowdProp.new()
	hp.kind = "occluder"  # (the crowd projects, culls and sorts it as it does the map's occluders)
	hp.name = "Herald_" + id.replace(".", "_")
	hp.set_meta("def", {"id": "herald:" + id, "sector": sec, "at": at, "width": h_m * 0.6, "height": h_m})
	hp.set_meta("tex", sheet())
	hp.set_meta("herald", id)
	hp.drawer = _draw_herald
	hp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST  # (clean pixels, as the people are drawn: the low-res viewport's default is linear)
	crowd.add_child(hp)
	crowd.props.append(hp)
	return hp


func _rec_of(prop: StoryCrowdProp) -> Dictionary:
	return _recs.get(str(prop.get_meta("herald", "")), {})


func _yaw_of(crowd: StoryCrowd) -> float:
	return float(crowd.cam_pose.get("yaw", 0.0)) if not crowd.cam_pose.is_empty() else 0.0


func _draw_herald(prop: StoryCrowdProp) -> void:
	var rec := _rec_of(prop)
	if rec.is_empty() or not bool(rec["on"]) or prop.items.is_empty():
		return
	var m: Dictionary = doc()["heralds"][rec["quest"]]
	var rect: Rect2 = prop.items[0][1]
	var spm := rect.size.y / float(m.get("height_m", 1.7))  # screen pixels per metre
	var lod := "1" if spm / float(m["px_per_m"]["1"]) >= LOD2_BELOW or not (m["lods"] as Dictionary).has("2") else "2"
	var i := frame_of(now, beat_s, reduced)
	var fr: Array = m["lods"][lod]["frames"][i]
	var k := spm / float(m["px_per_m"][lod])  # screen pixels per sheet pixel
	var id := str(prop.get_meta("herald"))
	var fl := flip_of(rec["at"], rec["toward"], _yaw_of(rec["crowd"]), bool(_flip.get(id, false)))
	_flip[id] = fl
	var sx := -1.0 if fl else 1.0
	prop.draw_set_transform(Vector2.ZERO, 0.0, Vector2(sx * k, k))
	var src := Rect2(float(fr[0]), float(fr[1]), float(fr[2]), float(fr[3]))
	var dst := Rect2(-float(fr[4]), -float(fr[5]), float(fr[2]), float(fr[3]))
	prop.draw_texture_rect_region(sheet(), dst, src, _light(prop, rec))
	var g: Array = m["lods"][lod]["glow"][i]
	if g.size() == 4:
		var pulse := 0.8 + 0.2 * absf(cos(PI * now / beat_s))
		prop.draw_texture_rect_region(sheet(), dst, Rect2(float(g[0]), float(g[1]), float(g[2]), float(g[3])), Color(pulse, pulse, pulse, 1.0))
	prop.draw_set_transform_matrix(Transform2D.IDENTITY)


## The quest's mark over the entrance, and under it the entrance's light: a pool of the quest's colour on the floor and, for an entrance with no thing of its own
## (`gate`), a lit doorway. The mark and the gate's light are their own light (unlit by the room), the gate's frame takes the room's light like a person; all of it swells a
## little on every beat and fades into the room's depth fog as the people do.
func _draw_mark(prop: StoryCrowdProp) -> void:
	var rec := _rec_of(prop)
	if rec.is_empty() or not bool(rec["on"]) or prop.items.is_empty():
		return
	var hm: Dictionary = doc()["heralds"][rec["quest"]]
	var mk: Dictionary = hm.get("mark", {})
	if mk.is_empty():
		return
	var b: Dictionary = rec["block"]
	var rect: Rect2 = prop.items[0][1]
	var spm := rect.size.y / (float(b.get("mark_y", 1.5)) + 0.25)
	var beat_u := fposmod(now / beat_s, 1.0)
	var hit := 0.0 if reduced else maxf(0.0, 1.0 - beat_u * 3.0)  # 1 on the beat, gone by a third of it
	var fog := _fog_of(prop, rec)
	var keep := 1.0 - 0.6 * fog  # (lights carry through the haze further than people do)
	var col := Color.html(str(mk["colour"]))
	# the pool: the quest's light on the floor round the entrance, an ellipse as flat as the floor looks from the eye
	var flat := clampf(_eye_over_floor(prop, rec) / maxf(prop.depth, 0.5), 0.12, 0.65)
	var pr := POOL_M * spm
	for k in 4:
		var f := 1.0 - 0.22 * float(k)
		prop.draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, flat))
		prop.draw_circle(Vector2.ZERO, pr * f, Color(col.r, col.g, col.b, (0.07 + 0.05 * hit) * keep))
	prop.draw_set_transform_matrix(Transform2D.IDENTITY)
	var gt: Dictionary = hm.get("gate", {})
	if typeof(b.get("gate", false)) == TYPE_BOOL and b.get("gate", false) and not gt.is_empty():
		var gk := spm / float(gt["px_per_m"])
		var gr: Array = gt["rect"]
		var gg: Array = gt["glow"]
		var pv: Array = gt["pivot"]
		var dst := Rect2(-float(pv[0]) * gk, -float(pv[1]) * gk, float(gr[2]) * gk, float(gr[3]) * gk)
		var glow := (0.7 + 0.15 * hit) * keep  # (a doorway lit from inside, not a lamp: below the mark's own light)
		prop.draw_texture_rect_region(sheet(), dst, Rect2(float(gg[0]), float(gg[1]), float(gg[2]), float(gg[3])), Color(glow, glow, glow, 1.0))
		prop.draw_texture_rect_region(sheet(), dst, Rect2(float(gr[0]), float(gr[1]), float(gr[2]), float(gr[3])), _light(prop, rec))
	var r: Array = mk["rect"]
	var swell := 1.0 + 0.12 * hit
	var k2 := spm / float(mk["px_per_m"]) * swell
	var c := Vector2(0.0, -float(b.get("mark_y", 1.5)) * spm)
	var half := Vector2(float(r[2]), float(r[3])) * 0.5 * k2
	prop.draw_circle(c, half.x * 1.8, Color(col.r, col.g, col.b, (0.14 + 0.1 * hit) * keep))  # a soft halo of its light on the wall behind
	prop.draw_texture_rect_region(sheet(), Rect2(c - half, half * 2.0), Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])), Color(keep, keep, keep, 1.0))


## The depth fog where the prop stands, 0 to 1, as the crowd fades its people (StoryCrowd.fog_m).
func _fog_of(prop: StoryCrowdProp, rec: Dictionary) -> float:
	var crowd: StoryCrowd = rec["crowd"]
	if not is_instance_valid(crowd) or crowd.fog_m.y <= crowd.fog_m.x:
		return 0.0
	return clampf((prop.depth - crowd.fog_m.x) / (crowd.fog_m.y - crowd.fog_m.x), 0.0, 1.0)


## How high the eye is over the floor the prop stands on (metres): the flattening of its light pool.
func _eye_over_floor(prop: StoryCrowdProp, rec: Dictionary) -> float:
	var crowd: StoryCrowd = rec["crowd"]
	var o: Dictionary = prop.get_meta("def", {})
	if not is_instance_valid(crowd) or crowd.cam_pose.is_empty() or stage == null or stage.map == null:
		return 1.6
	return maxf((crowd.cam_pose["cam"] as Vector3).y - _floor_at(stage.map, o["at"]), 0.2)


func _light(prop: StoryCrowdProp, rec: Dictionary) -> Color:
	var crowd: StoryCrowd = rec["crowd"]
	var o: Dictionary = prop.get_meta("def", {})
	if not crowd.light_fn.is_valid():
		return Color.WHITE
	if not prop.has_meta("lamp"):  # (the lamps round the spot, once: each prop of the entrance has its own spot)
		prop.set_meta("lamp", crowd.light_fn.call(str(o["sector"]), o["at"], false))
	var l: Color = (crowd.light_fn.call(str(o["sector"]), o["at"], true) as Color) * (prop.get_meta("lamp") as Color) * GAIN
	var lo := 0.8 if high_contrast else MIN_LIGHT
	var fade := 1.0 - FOG_MIX * _fog_of(prop, rec)  # (the depth fog, as the people's shader mixes them into the dark: the fog colour is near black)
	return Color(clampf(l.r, lo, MAX_LIGHT) * fade, clampf(l.g, lo, MAX_LIGHT) * fade, clampf(l.b, lo, MAX_LIGHT) * fade, 1.0)


## A `self` herald: the entrance's own billboard plays the gesture while the entrance is on offer and not current (in place of the sad frame; the red light on the floor still
## says it is not the current choice); current, committed or declined, the choice layer's own look plays.
func _pose_self(id: String, b: Dictionary, toward: Vector2, role: String) -> void:
	if stage.world == null or role != "other":
		return
	var th := str(b["self"])
	var at := Vector2.ZERO
	for t in stage.map.things:
		if str(t["id"]) == th:
			at = t["at"]
	var yaw := 0.0
	var c: StoryCrowd = stage.crowds.get("main", null)
	if c != null:
		yaw = _yaw_of(c)
	var fl := flip_of(at, toward, yaw, bool(_flip.get(id, false)))
	_flip[id] = fl
	var tx := self_tex(str(b["quest"]), frame_of(now, beat_s, reduced), fl)
	if tx == null:
		return
	var tp: Dictionary = stage.world.thing_pose.get(th, {})
	if tp.is_empty():
		tp = {"dy": 0.0, "sx": 1.0, "sy": 1.0, "dx": 0.0}
	tp["tex"] = tx
	stage.world.thing_pose[th] = tp
