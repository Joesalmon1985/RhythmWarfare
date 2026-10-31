class_name SongClock
extends RefCounted
## The one song clock (PRD section 8, Godot audio-sync guidance). Song time is derived from the audio playhead,
## never from accumulated frame deltas: mixed position + time since the last mix - cached output latency.
## It is monotonic (audio-thread jitter can never move it backwards) and it freezes while paused.
##
## Two offsets, kept apart (docs/TIMING.md):
##  - the chart's song_offset_ms lives in Level.tick_to_seconds (positive = every chart event later);
##  - calibration_ms is the device/player offset: the measured average lateness of the player's taps.
##    Positive = taps arrive late, so it is subtracted from the audio time before judgement.

enum State { IDLE, COUNTDOWN, PLAYING, PAUSED, ENDED }

var transport: StemTransport
var calibration_ms := 0.0
var state := State.IDLE
var output_latency := 0.0

var _last := -INF
var _frozen := 0.0
var _countdown_len := 0.0
var _countdown_started_usec := 0


func _init(stem_transport: StemTransport) -> void:
	transport = stem_transport


## Begin a countdown of `seconds`; audio starts when it reaches zero (call tick() every frame).
func begin_countdown(seconds: float) -> void:
	output_latency = AudioServer.get_output_latency()
	_countdown_len = seconds
	_countdown_started_usec = Time.get_ticks_usec()
	_last = -INF
	state = State.COUNTDOWN


## Advances the countdown; starts the transport when it elapses. Returns true on the frame audio starts.
func tick() -> bool:
	if state != State.COUNTDOWN:
		return false
	if _countdown_remaining() <= 0.0:
		transport.start()
		state = State.PLAYING
		_last = -INF
		return true
	return false


func _countdown_remaining() -> float:
	return _countdown_len - float(Time.get_ticks_usec() - _countdown_started_usec) / 1_000_000.0


func countdown_remaining() -> float:
	return maxf(_countdown_remaining(), 0.0) if state == State.COUNTDOWN else 0.0


## Song position of the sound reaching the listener, in seconds. Negative during the countdown.
func audio_time() -> float:
	match state:
		State.IDLE:
			return 0.0
		State.COUNTDOWN:
			return transport.start_at - _countdown_remaining()
		State.PAUSED, State.ENDED:
			return _frozen
	var t := transport.playback_position() + AudioServer.get_time_since_last_mix() - output_latency
	if t < _last:
		t = _last
	_last = t
	return t


## The time used for judgement and for drawing notes: audio time corrected by the player's calibration.
func judge_time() -> float:
	return audio_time() - calibration_ms / 1000.0


func pause() -> void:
	if state == State.PLAYING:
		_frozen = audio_time()
		transport.pause()
		state = State.PAUSED
	elif state == State.COUNTDOWN:
		_frozen = transport.start_at - _countdown_remaining()
		state = State.PAUSED


## Resume after a pause: the caller shows its own countdown, then calls this. Time re-anchors at the frozen value.
func resume() -> void:
	if state != State.PAUSED:
		return
	if _frozen < transport.start_at:
		begin_countdown(transport.start_at - _frozen)
		return
	_last = _frozen
	transport.resume()
	state = State.PLAYING


func end() -> void:
	if state == State.PLAYING or state == State.PAUSED:
		_frozen = audio_time() if state == State.PLAYING else _frozen
	state = State.ENDED
