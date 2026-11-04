class_name StemTransport
extends Node
## Plays the level's stems (four in the schema 1 duel; the loop stems of a schema 4 mission, up to the 32 that
## AudioStreamSynchronized allows) as one AudioStreamSynchronized through one AudioStreamPlayer: one start, one transport,
## one pause state, one playhead. A gain change only ramps a substream's volume; it never stops or restarts a stem, so
## a silent stem keeps its position and comes back at the current song position.
##
## Missions play eight-bar (or longer) loops, every substream with loop = true so they stay locked for as long as the
## song lasts. A stem sounds when the mission's gain program says so (apply_program: drums bars, bass bars, fill bar)
## and no miss has muted it (set_stem_muted); the target is the AND of the two. The song position is unwrapped so it
## keeps growing past the loop length.

signal song_finished

const RAMP_S := 0.03
const SILENT_DB := -80.0
const STEM_ORDER := ["kick", "snare", "bass", "other"]  # the schema 1 stem keys
const MAX_STREAMS := 32

var stem_keys: Array = []  # the loaded level's stem keys, in substream order
var start_at := 0.0  # song second the transport starts from (practice of one phase); 0 for a whole run
var loop_seconds := 0.0  # the longest loop's length; 0 when the stems are not loops (the duel)
var song_base := 0.0  # song seconds before the loop position the player started at (practice of a later phase)
var player: AudioStreamPlayer
var sync_stream: AudioStreamSynchronized
var _program: Dictionary = {}  # key -> bool, the gain program's flag (default on)
var _muted: Dictionary = {}  # key -> bool, silenced by a miss
var _initial_program: Array = []  # the level's gain_program, applied at start() for the starting bar
var _bar_s := 0.0
var _wraps := 0
var _last_raw := 0.0
var _target: Dictionary = {}  # key -> linear gain target (0 or 1)
var _current: Dictionary = {}  # key -> linear gain now
var _duck := 0.0  # 0..1: the story's sick beat. The mix gets quieter and the stems that are not low (kick and bass families) fall away, a muffled "behind a door" music
var _duck_applied := -1.0
var _low_keys: Dictionary = {}  # stem keys that stay audible under the duck
var _fade_master := 1.0
var _fade_target := 1.0
var _fade_speed := 0.0
var _loaded := false


## The "Music" bus (created on first use, sends to Master) so the music volume never scales the battle effects.
static func ensure_music_bus() -> int:
	var i := AudioServer.get_bus_index("Music")
	if i < 0:
		AudioServer.add_bus()
		i = AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, "Music")
		AudioServer.set_bus_send(i, "Master")
	return i


func _ready() -> void:
	player = AudioStreamPlayer.new()
	player.name = "StemPlayer"
	player.bus = AudioServer.get_bus_name(ensure_music_bus())
	add_child(player)
	player.finished.connect(func() -> void: song_finished.emit())


## Decodes and attaches the level's stems. Returns an error string, empty on success. Stems with a loop length in
## level.stem_loop_bars are set to loop, and the substreams are ordered longest loop first.
func load_level(level: Level) -> String:
	var keys: Array = level.stems.keys()
	if keys.is_empty() or keys.size() > MAX_STREAMS:
		return "a level needs 1 to %d stems, this one has %d" % [MAX_STREAMS, keys.size()]
	var streams: Dictionary = {}
	loop_seconds = 0.0
	for key in keys:
		var path: String = level.stems.get(key, "")
		var stream := LevelLoader.load_stream(path)
		if stream == null:
			return "could not load stem '%s' from %s" % [key, path]
		streams[key] = stream
		if int(level.stem_loop_bars.get(key, 0)) > 0:
			_set_loop(stream)
			loop_seconds = maxf(loop_seconds, stream.get_length())
	if loop_seconds > 0.0:  # longest loop first (stable for equal lengths)
		var original := keys.duplicate()
		keys.sort_custom(func(a: String, b: String) -> bool:
			var la: int = level.stem_loop_bars.get(a, 0)
			var lb: int = level.stem_loop_bars.get(b, 0)
			return la > lb or (la == lb and original.find(a) < original.find(b)))
	stem_keys = keys
	sync_stream = AudioStreamSynchronized.new()
	sync_stream.stream_count = stem_keys.size()
	_target.clear()
	_current.clear()
	_program.clear()
	_muted.clear()
	for i in stem_keys.size():
		var key: String = stem_keys[i]
		sync_stream.set_sync_stream(i, streams[key])
		sync_stream.set_sync_stream_volume(i, 0.0)
		_target[key] = 1.0
		_current[key] = 1.0
		_program[key] = true
		_muted[key] = false
	_initial_program = level.gain_program
	_low_keys = {}
	for k in stem_keys:
		if str(level.stem_family.get(k, k)) in ["kick", "bass", "drums"]:
			_low_keys[k] = true
	_bar_s = level.ticks_per_bar() * 60.0 / (level.bpm * float(level.ticks_per_beat))
	player.stream = sync_stream
	_loaded = true
	return ""


static func _set_loop(stream: AudioStream) -> void:
	if stream is AudioStreamOggVorbis:
		(stream as AudioStreamOggVorbis).loop = true
	elif stream is AudioStreamMP3:
		(stream as AudioStreamMP3).loop = true
	elif stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = int(round(wav.get_length() * float(wav.mix_rate)))


func start() -> void:
	if not _loaded:
		push_error("StemTransport.start before load_level")
		return
	_fade_master = 1.0
	_fade_target = 1.0
	player.volume_db = 0.0
	_wraps = 0
	_last_raw = 0.0
	var from := start_at
	song_base = 0.0
	if loop_seconds > 0.0:
		from = fmod(start_at, loop_seconds)
		song_base = start_at - from
		if not _initial_program.is_empty() and _bar_s > 0.0:  # the starting bar's program sounds from the first sample
			apply_program(_initial_program[clampi(int(start_at / _bar_s), 0, _initial_program.size() - 1)], true)
	player.play(from)


func pause() -> void:
	player.stream_paused = true


func resume() -> void:
	player.stream_paused = false


func stop() -> void:
	player.stop()
	_wraps = 0
	_last_raw = 0.0
	player.stream_paused = false


func is_playing() -> bool:
	return player.playing and not player.stream_paused


func is_paused() -> bool:
	return player.stream_paused


## Seconds into the song as mixed so far (the audio thread's position). Sub-mix accuracy comes from
## AudioServer.get_time_since_last_mix(); SongClock adds that and subtracts the output latency. With looping stems the
## player's own position may wrap at the loop length; it is unwrapped here and offset by song_base.
func playback_position() -> float:
	var raw := player.get_playback_position()
	if loop_seconds <= 0.0:
		return raw
	if raw < _last_raw - loop_seconds * 0.5:
		_wraps += 1
	_last_raw = raw
	return song_base + float(_wraps) * loop_seconds + raw


## A miss silences (or a hit restores) a stem; combined with the gain program.
func set_stem_muted(key: String, muted: bool) -> void:
	if _target.has(key):
		_muted[key] = muted
		_retarget(key)


## True while a miss has silenced the stem (the gain program is separate).
func is_stem_muted(key: String) -> bool:
	return bool(_muted.get(key, false))


## The gain program of the current bar: {stem key: bool}. Keys the transport does not play are ignored; keys left out
## keep their flag. `snap` skips the ramp (the first bar of a run).
func apply_program(on: Dictionary, snap: bool = false) -> void:
	for key in on:
		if _target.has(key):
			_program[key] = bool(on[key])
			_retarget(key)
			if snap:
				_current[key] = _target[key]
				sync_stream.set_sync_stream_volume(stem_keys.find(key), _to_db(effective_gain(key)))


## Whether the gain program has the stem sounding (a miss mute is separate).
func is_stem_programmed(key: String) -> bool:
	return bool(_program.get(key, true))


## Whether the stem is meant to be heard now: programmed on and not muted by a miss.
func stem_target(key: String) -> float:
	return _target.get(key, 1.0)


func _retarget(key: String) -> void:
	_target[key] = 1.0 if bool(_program.get(key, true)) and not bool(_muted.get(key, false)) else 0.0


func stem_gain(key: String) -> float:
	return _current.get(key, 1.0)


## Fade the whole mix to silence over `seconds` (used at victory or defeat).
func fade_out(seconds: float) -> void:
	_fade_target = 0.0
	_fade_speed = 1.0 / maxf(seconds, 0.001)


## The story's sick beat: `amount` 0..1 quietens the mix and lets the non-low stems fall away (existing stem gains only, no new audio). 0 leaves the mix as it was.
func set_duck(amount: float) -> void:
	_duck = clampf(amount, 0.0, 1.0)


func duck() -> float:
	return _duck


## The gain actually sent to a stem: its ramped gain, scaled by the duck (low stems to 0.45, the others to 0.1 at full duck).
func effective_gain(key: String) -> float:
	var g: float = _current.get(key, 1.0)
	if _duck <= 0.0:
		return g
	return g * lerpf(1.0, 0.45 if _low_keys.has(key) else 0.1, _duck)


func _process(delta: float) -> void:
	if not _loaded:
		return
	var step := delta / RAMP_S
	var duck_changed := not is_equal_approx(_duck, _duck_applied)
	_duck_applied = _duck
	for i in stem_keys.size():
		var key: String = stem_keys[i]
		var cur: float = _current[key]
		var tgt: float = _target[key]
		if cur != tgt or duck_changed:
			cur = move_toward(cur, tgt, step)
			_current[key] = cur
			sync_stream.set_sync_stream_volume(i, _to_db(effective_gain(key)))
	if _fade_master != _fade_target:
		_fade_master = move_toward(_fade_master, _fade_target, _fade_speed * delta)
		player.volume_db = _to_db(_fade_master)


static func _to_db(linear: float) -> float:
	return SILENT_DB if linear <= 0.0001 else linear_to_db(linear)
