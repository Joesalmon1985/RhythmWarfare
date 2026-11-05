class_name TrackTransport
extends StemTransport
## StemTransport for a track pack: the stems are already decoded (TrackPack keeps them), so they are attached directly
## instead of through a Level, and every stem keeps the gain the pack gives it (the base class only knows 0 or 1).
## Everything else is the base class: one AudioStreamSynchronized on one player, one playhead, 30 ms gain ramps for
## mute and restore, start_at, pause and resume.

var _gain: Dictionary = {}  # key -> pack gain (linear, 0 to 2)


## Attaches the stems of `pack` in the order voices then backing. Returns an error string, empty on success.
func load_pack_streams(pack: TrackPack) -> String:
	if player == null:
		return "the transport must be in the scene tree before the stems are attached"
	var order := pack.stems_in_order()
	if order.is_empty() or order.size() > MAX_STREAMS:
		return "a track needs 1 to %d stems, this one has %d" % [MAX_STREAMS, order.size()]
	stem_keys = []
	loop_seconds = 0.0
	sync_stream = AudioStreamSynchronized.new()
	sync_stream.stream_count = order.size()
	_target.clear()
	_current.clear()
	_program.clear()
	_muted.clear()
	_gain.clear()
	for i in order.size():
		var key: String = order[i]["key"]
		var stream: AudioStream = pack.streams.get(key)
		if stream == null:
			return "stem '%s' was not decoded" % key
		stem_keys.append(key)
		_gain[key] = float(order[i]["gain"])
		sync_stream.set_sync_stream(i, stream)
		sync_stream.set_sync_stream_volume(i, StemTransport._to_db(_gain[key]))
		_target[key] = 1.0
		_current[key] = 1.0
		_program[key] = true
		_muted[key] = false
	_initial_program = []
	_low_keys = {}
	_bar_s = 0.0
	player.stream = sync_stream
	_loaded = true
	return ""


func effective_gain(key: String) -> float:
	return super.effective_gain(key) * float(_gain.get(key, 1.0))


## The gain the pack gives a stem.
func pack_gain(key: String) -> float:
	return float(_gain.get(key, 1.0))
