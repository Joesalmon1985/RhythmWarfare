class_name StemTransport
extends Node
## Plays the level's stems (four in schema 1; one per equipped slot plus "other" in schema 2, up to the 32 that
## AudioStreamSynchronized allows) as one AudioStreamSynchronized through one AudioStreamPlayer: one start, one transport,
## one pause state, one playhead. Muting only changes a substream's gain with a short ramp; it never stops or
## restarts a stem, so a muted stem keeps its position and comes back at the current song position.

signal song_finished

const RAMP_S := 0.03
const SILENT_DB := -80.0
const STEM_ORDER := ["kick", "snare", "bass", "other"]  # the schema 1 stem keys
const MAX_STREAMS := 32

var stem_keys: Array = []  # the loaded level's stem keys, in substream order
var player: AudioStreamPlayer
var sync_stream: AudioStreamSynchronized
var _target: Dictionary = {}  # key -> linear gain target (0 or 1)
var _current: Dictionary = {}  # key -> linear gain now
var _fade_master := 1.0
var _fade_target := 1.0
var _fade_speed := 0.0
var _loaded := false


func _ready() -> void:
	player = AudioStreamPlayer.new()
	player.name = "StemPlayer"
	player.bus = "Master"
	add_child(player)
	player.finished.connect(func() -> void: song_finished.emit())


## Decodes and attaches the level's stems. Returns an error string, empty on success.
func load_level(level: Level) -> String:
	stem_keys = level.stems.keys()
	if stem_keys.is_empty() or stem_keys.size() > MAX_STREAMS:
		return "a level needs 1 to %d stems, this one has %d" % [MAX_STREAMS, stem_keys.size()]
	sync_stream = AudioStreamSynchronized.new()
	sync_stream.stream_count = stem_keys.size()
	_target.clear()
	_current.clear()
	for i in stem_keys.size():
		var key: String = stem_keys[i]
		var path: String = level.stems.get(key, "")
		var stream := LevelLoader.load_stream(path)
		if stream == null:
			return "could not load stem '%s' from %s" % [key, path]
		sync_stream.set_sync_stream(i, stream)
		sync_stream.set_sync_stream_volume(i, 0.0)
		_target[key] = 1.0
		_current[key] = 1.0
	player.stream = sync_stream
	_loaded = true
	return ""


func start() -> void:
	if not _loaded:
		push_error("StemTransport.start before load_level")
		return
	_fade_master = 1.0
	_fade_target = 1.0
	player.volume_db = 0.0
	player.play(0.0)


func pause() -> void:
	player.stream_paused = true


func resume() -> void:
	player.stream_paused = false


func stop() -> void:
	player.stop()
	player.stream_paused = false


func is_playing() -> bool:
	return player.playing and not player.stream_paused


func is_paused() -> bool:
	return player.stream_paused


## Seconds into the stems as mixed so far (the audio thread's position). Sub-mix accuracy comes from
## AudioServer.get_time_since_last_mix(); SongClock adds that and subtracts the output latency.
func playback_position() -> float:
	return player.get_playback_position()


func set_stem_muted(key: String, muted: bool) -> void:
	if _target.has(key):
		_target[key] = 0.0 if muted else 1.0


func is_stem_muted(key: String) -> bool:
	return _target.get(key, 1.0) < 0.5


func stem_gain(key: String) -> float:
	return _current.get(key, 1.0)


## Fade the whole mix to silence over `seconds` (used at victory or defeat).
func fade_out(seconds: float) -> void:
	_fade_target = 0.0
	_fade_speed = 1.0 / maxf(seconds, 0.001)


func _process(delta: float) -> void:
	if not _loaded:
		return
	var step := delta / RAMP_S
	for i in stem_keys.size():
		var key: String = stem_keys[i]
		var cur: float = _current[key]
		var tgt: float = _target[key]
		if cur != tgt:
			cur = move_toward(cur, tgt, step)
			_current[key] = cur
			sync_stream.set_sync_stream_volume(i, _to_db(cur))
	if _fade_master != _fade_target:
		_fade_master = move_toward(_fade_master, _fade_target, _fade_speed * delta)
		player.volume_db = _to_db(_fade_master)


static func _to_db(linear: float) -> float:
	return SILENT_DB if linear <= 0.0001 else linear_to_db(linear)
