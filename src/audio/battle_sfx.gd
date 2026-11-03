class_name BattleSfx
extends Node
## Red Alert sound effects for the battle: a pool of AudioStreamPlayers on the "SFX" bus fed the same event list as the
## BattleView (push_events). data/sfx_map.json says which event plays which assets/sfx/<name>.ogg. At most `max_voices`
## sounds play at once (a new one steals the oldest non-EVA voice), EVA lines never overlap each other (one waits in a
## queue; the mission outcome lines cut in), and shots, deaths and EVA lines have cooldowns. Rules of one "group"
## (the weapons) share a smaller cap: a new sound beyond it is dropped rather than stealing a voice. The SFX bus carries
## a limiter so a burst of effects can never clip over the music.
## Tests set `record_only`: plays are appended to `played` and no audio is touched.

const MAP_PATH := "res://data/sfx_map.json"
const SFX_DIR := "res://assets/sfx/"
const META_PATH := "res://assets/sfx/sfx.json"
const BUS := "SFX"
const DEFAULT_SECONDS := 0.5
const LIMITER_CEILING_DB := -1.0

var primary_role := ""  # roster role of the objective whose damage triggers "base under attack"
var record_only := false
var played: Array = []  # record_only: {name, volume_db, eva, time}
var stolen: Array = []  # record_only: names of voices cut short
var map: Dictionary = {}

var _time := 0.0
var _last: Dictionary = {}  # cooldown key -> time of the last play
var _voices: Array = []  # {name, eva, priority, group, start, end, player}
var _eva_queue: Dictionary = {}  # {name, volume_db, priority} or {}
var _pool: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _seconds: Dictionary = {}
var _alternate := 0


func _init() -> void:
	map = load_map()
	var meta: Variant = JSON.parse_string(FileAccess.get_file_as_string(META_PATH)) if FileAccess.file_exists(META_PATH) else null
	if typeof(meta) == TYPE_DICTIONARY:
		for k in meta:
			_seconds[k] = float(meta[k].get("seconds", DEFAULT_SECONDS))


static func load_map() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MAP_PATH)) if FileAccess.file_exists(MAP_PATH) else null
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


## Every sound name a map refers to (recursively, from the "sounds" arrays).
static func sound_names(node: Variant) -> Array:
	var out: Array = []
	if typeof(node) == TYPE_DICTIONARY:
		for k in node:
			if k == "sounds" and typeof(node[k]) == TYPE_ARRAY:
				for n in node[k]:
					if not out.has(str(n)):
						out.append(str(n))
			else:
				for n in sound_names(node[k]):
					if not out.has(n):
						out.append(n)
	return out


## The "SFX" audio bus (sending to Master), created when the project has none. Returns its index.
static func ensure_bus() -> int:
	var i := AudioServer.get_bus_index(BUS)
	if i < 0:
		AudioServer.add_bus()
		i = AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, BUS)
		AudioServer.set_bus_send(i, "Master")
	var has_limiter := false
	for e in AudioServer.get_bus_effect_count(i):
		if AudioServer.get_bus_effect(i, e) is AudioEffectLimiter:
			has_limiter = true
	if not has_limiter:
		var limiter := AudioEffectLimiter.new()
		limiter.ceiling_db = LIMITER_CEILING_DB
		AudioServer.add_bus_effect(i, limiter)
	return i


func _process(delta: float) -> void:
	advance_time(delta)


## Moves the clock (cooldowns, voice ends, the EVA queue). _process calls it; tests call it directly.
func advance_time(dt: float) -> void:
	_time += dt
	_prune()
	if not _eva_queue.is_empty() and not _eva_active():
		var q := _eva_queue
		_eva_queue = {}
		_start(str(q["name"]), float(q["volume_db"]), true, int(q["priority"]))


func now() -> float:
	return _time


func active_voices() -> int:
	_prune()
	return _voices.size()


func push_events(events: Array) -> void:
	for ev in events:
		_handle(ev)


func _handle(ev: Dictionary) -> void:
	match str(ev.get("kind", "")):
		"shot":
			var rule: Dictionary = map.get("shot", {}).get(str(ev.get("weapon", "")), {})
			if not rule.is_empty():
				_play_rule(rule, "shot:" + str(ev["weapon"]), int(ev.get("from", 0)))
		"destroyed":
			var ekind := str(ev.get("ekind", "unit"))
			var civilian := bool(ev.get("civilian", false))
			var key := "vehicle"
			if ekind == "building":
				key = "building"
			elif ekind == "aircraft":
				key = "aircraft"
			elif civilian:
				key = "civilian"
			elif str(ev.get("role", "")) == "infantry":
				key = "infantry"
			var rules: Dictionary = map.get("destroyed", {})
			if rules.has(key):
				_play_rule(rules[key], "destroyed:" + key, int(ev.get("id", 0)))
			if int(ev.get("side", 1)) == 0 and not civilian and ekind != "building" and rules.has("unit_lost"):
				_play_rule(rules["unit_lost"], "destroyed:unit_lost", 0)
		"hit":
			if int(ev.get("side", 1)) == 0 and not bool(ev.get("civilian", false)) and not primary_role.is_empty() and str(ev.get("role", "")) == primary_role:
				_play_rule(map.get("hit_objective", {}), "hit_objective", 0)
		"reward_scheduled":
			var entry: Dictionary = ev.get("entry", {})
			var rule: Dictionary = map.get("reward_scheduled", {}).get(str(entry.get("kind", "")), {})
			if not rule.is_empty():
				_play_rule(rule, "reward_scheduled:" + str(entry["kind"]), 0)
		"reward_done":
			var rule: Dictionary = map.get("reward_done", {}).get(str(ev.get("result", "")), {})
			if not rule.is_empty():
				_play_rule(rule, "reward_done:" + str(ev["result"]), 0)
		"wave_warning":
			_play_rule(map.get("wave_warning", {}), "wave_warning", 0)
		"section":
			if int(ev.get("point", -1)) >= 0:
				_play_rule(map.get("section", {}), "section", 0)
		"outcome":
			var rule: Dictionary = map.get("outcome", {}).get(str(ev.get("outcome", "")), {})
			if not rule.is_empty():
				_play_rule(rule, "outcome", 0)


func _play_rule(rule: Dictionary, key: String, id: int) -> void:
	var sounds: Array = rule.get("sounds", [])
	if sounds.is_empty():
		return
	var cooldown := float(rule.get("cooldown", 0.0))
	if cooldown > 0.0:
		if _time - float(_last.get(key, -INF)) < cooldown:
			return
		_last[key] = _time
	var volume := float(rule.get("volume_db", 0.0))
	var eva := bool(rule.get("eva", false))
	var names: Array = []
	match str(rule.get("pick", "first")):
		"all":
			names = sounds
		"id":
			names = [sounds[posmod(id, sounds.size())]]
		"parity":
			names = [sounds[posmod(id, 2) % sounds.size()]]
		"alternate":
			names = [sounds[_alternate % sounds.size()]]
			_alternate += 1
		_:
			names = [sounds[0]]
	for n in names:
		if eva:
			_request_eva(str(n), volume, int(rule.get("priority", 0)))
		else:
			_start(str(n), volume, false, 0, str(rule.get("group", "")))


## EVA lines are voices of their own: one at a time. A new request waits (the newest replaces an older waiting one of
## equal or lower priority); a higher priority line cuts the playing one off.
func _request_eva(sound: String, volume: float, priority: int) -> void:
	_prune()
	for v in _voices:
		if bool(v["eva"]):
			if priority > int(v["priority"]):
				_stop_voice(v)
				break
			if _eva_queue.is_empty() or priority >= int(_eva_queue["priority"]):
				_eva_queue = {"name": sound, "volume_db": volume, "priority": priority}
			return
	_start(sound, volume, true, priority)


func _eva_active() -> bool:
	for v in _voices:
		if bool(v["eva"]):
			return true
	return false


func _start(sound: String, volume: float, eva: bool, priority: int, group: String = "") -> void:
	_prune()
	if not group.is_empty():
		var cap := int(map.get("group_voices", {}).get(group, 0))
		if cap > 0:
			var playing := 0
			for v in _voices:
				if str(v.get("group", "")) == group:
					playing += 1
			if playing >= cap:
				return  # the group is full: drop the new sound, never steal
	var max_voices := int(map.get("max_voices", 8))
	while _voices.size() >= max_voices:
		var oldest: Dictionary = {}
		for v in _voices:
			if not bool(v["eva"]) and (oldest.is_empty() or float(v["start"]) < float(oldest["start"])):
				oldest = v
		if oldest.is_empty():
			return
		_stop_voice(oldest)
	var voice := {"name": sound, "eva": eva, "priority": priority, "group": group, "start": _time, "end": _time + float(_seconds.get(sound, DEFAULT_SECONDS)), "player": null}
	if record_only:
		played.append({"name": sound, "volume_db": volume, "eva": eva, "time": _time})
	else:
		var player := _free_player()
		var stream := _stream(sound)
		if player == null or stream == null:
			return
		player.stream = stream
		player.volume_db = volume
		player.play()
		voice["player"] = player
	_voices.append(voice)


func _stop_voice(v: Dictionary) -> void:
	_voices.erase(v)
	if record_only:
		stolen.append(str(v["name"]))
	elif v["player"] != null:
		(v["player"] as AudioStreamPlayer).stop()


func _prune() -> void:
	var keep: Array = []
	for v in _voices:
		if _time < float(v["end"]):
			keep.append(v)
	_voices = keep


func _free_player() -> AudioStreamPlayer:
	if _pool.is_empty():
		ensure_bus()
		for i in int(map.get("pool", 12)):
			var p := AudioStreamPlayer.new()
			p.bus = BUS
			add_child(p)
			_pool.append(p)
	var used := {}
	for v in _voices:
		if v["player"] != null:
			used[v["player"]] = true
	for p in _pool:
		if not used.has(p):
			return p
	return null


func _stream(sound: String) -> AudioStream:
	if _streams.has(sound):
		return _streams[sound]
	var path := SFX_DIR + sound + ".ogg"
	var s: AudioStream = load(path) if ResourceLoader.exists(path) else null
	if s == null:
		push_warning("missing sound " + path)
	_streams[sound] = s
	return s
