extends Control
## Timing calibration: a generated metronome plays 16 clicks at 120 BPM; the player taps along (any lane key,
## touch or click). The average lateness of taps against the audio clock becomes calibration_ms.
## Positive = this device/player taps late. A manual slider is offered as well (docs/TIMING.md).

const CLICK_BPM := 120.0
const CLICKS := 16
const SAMPLE_RATE := 44100
const SKIP_FIRST := 4

var _player: AudioStreamPlayer
var _latency := 0.0
var _taps: Array[float] = []
var _running := false
var _done := false


func _ready() -> void:
	_player = AudioStreamPlayer.new()
	_player.stream = _make_metronome()
	add_child(_player)
	_player.finished.connect(_on_finished)
	$Box/Slider.value = Session.calibration_ms
	$Box/Slider.value_changed.connect(func(v: float) -> void: $Box/Readout.text = "Calibration %+.0f ms" % v)
	$Box/Readout.text = "Calibration %+.0f ms" % Session.calibration_ms
	$Box/Start.pressed.connect(_start)
	$Box/Save.pressed.connect(func() -> void:
		Session.calibration_ms = $Box/Slider.value
		Session.save_settings()
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	$Box/Back.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	$Box/Info.text = "Tap in time with the clicks (any lane key: F, Space, J, or touch the screen). The first %d clicks are ignored." % SKIP_FIRST


func _start() -> void:
	_taps.clear()
	_done = false
	_latency = AudioServer.get_output_latency()
	_player.play(0.0)
	_running = true
	$Box/Result.text = "listening..."


func _audio_time() -> float:
	return _player.get_playback_position() + AudioServer.get_time_since_last_mix() - _latency


func _input(event: InputEvent) -> void:
	if not _running:
		return
	var is_tap := false
	if event is InputEventScreenTouch and event.pressed:
		is_tap = true
	elif event is InputEventKey and event.pressed and not event.echo:
		is_tap = event.is_action("button_1") or event.is_action("button_2") or event.is_action("button_3") or event.is_action("button_4")
	if is_tap:
		_taps.append(_audio_time())
		$Box/Result.text = "taps: %d" % _taps.size()
		get_viewport().set_input_as_handled()


func _on_finished() -> void:
	_running = false
	var period := 60.0 / CLICK_BPM
	var offsets: Array[float] = []
	for t in _taps:
		var n := roundf(t / period)
		if n < SKIP_FIRST or n >= CLICKS:
			continue
		offsets.append((t - n * period) * 1000.0)
	if offsets.size() < 4:
		$Box/Result.text = "Not enough taps (%d). Try again." % offsets.size()
		return
	var mean := 0.0
	for o in offsets:
		mean += o
	mean /= offsets.size()
	var dev := 0.0
	for o in offsets:
		dev += (o - mean) * (o - mean)
	dev = sqrt(dev / offsets.size())
	$Box/Slider.value = roundf(mean)
	$Box/Result.text = "%d taps, average %+.0f ms late (spread ±%.0f ms). Press Save to keep %+.0f ms." % [offsets.size(), mean, dev, roundf(mean)]
	_done = true


static func _make_metronome() -> AudioStreamWAV:
	var period := 60.0 / CLICK_BPM
	var total := int(period * CLICKS * SAMPLE_RATE) + SAMPLE_RATE / 2
	var data := PackedByteArray()
	data.resize(total * 2)
	var click_len := int(0.03 * SAMPLE_RATE)
	for c in CLICKS:
		var start := int(c * period * SAMPLE_RATE)
		var freq := 1500.0 if c % 4 == 0 else 1000.0
		for i in click_len:
			var env := 1.0 - float(i) / click_len
			var v := sin(TAU * freq * float(i) / SAMPLE_RATE) * env * 0.8
			var s := int(clampf(v, -1.0, 1.0) * 32767.0)
			var idx := (start + i) * 2
			data[idx] = s & 0xFF
			data[idx + 1] = (s >> 8) & 0xFF
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = SAMPLE_RATE
	wav.stereo = false
	wav.data = data
	return wav
