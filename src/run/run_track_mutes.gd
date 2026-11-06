class_name RunTrackMutes
extends RefCounted
## The mute rule of a track scene (docs/RUN_TRACK_SCENES.md "Audio", docs/TRACK_PACK_FORMAT.md "restore_after_idle_beats") as pure logic on song time, fed with the run judge's events. It is
## TrackGame's rule (src/track/track_game.gd) for the run's own judge and its growing list of cues (`level.notes`, charted one block ahead):
##
##  - every voice of the pack starts audible; backing is no voice here and never mutes;
##  - a missed cue, or a hold let go early, mutes that cue's `voice` (a hold ended by the pause menu is no mistake: `ignore_let_go_at`);
##  - the next cue of that voice that is hit (a tap, or a hold started) restores it;
##  - a muted voice also comes back by itself `restore_beats` beats after it was muted when no cue of that voice falls within those beats; every new mute restarts that wait.
##
## The idle check is made at the deadline itself (`advance`): by then the cues of the next block are charted, so "is a cue of this voice within the wait" reads the real cues. The result is the
## same as TrackGame's, which looks ahead in a chart it has whole. Only cues that carry `track_t` (a track scene's cues) count; every other cue is ignored. Changes come back as
## {kind: "mute" | "restore", voice, t, reason: miss | let_go | hit | idle} in time order, and are kept in `log`.

const EPS := 1e-9

var restore_beats := 8.0
var beat_s := 0.5
var log: Array = []

var _voices: Dictionary = {}  # voice key -> true
var _muted: Dictionary = {}  # voice key -> bool
var _wait: Dictionary = {}  # voice key -> {due, from, after}: the pending idle check (mute time `from`, the missed cue's index `after`)
var _ignore_t := -INF


func setup(voice_keys: Array, p_beat_s: float, p_restore_beats: float = 8.0) -> void:
	_voices.clear()
	_muted.clear()
	_wait.clear()
	log.clear()
	for k in voice_keys:
		_voices[str(k)] = true
		_muted[str(k)] = false
	beat_s = p_beat_s
	restore_beats = p_restore_beats
	_ignore_t = -INF


func is_muted(key: String) -> bool:
	return bool(_muted.get(key, false))


func muted_keys() -> Array:
	var out: Array = []
	for k in _muted:
		if bool(_muted[k]):
			out.append(k)
	out.sort()
	return out


## The pause menu ends every hold where it stands at judge time `t` (PadJudge.pause_interrupt): a hold let go at exactly that time mutes nothing.
func ignore_let_go_at(t: float) -> void:
	_ignore_t = t


## One judge event (PadJudge: perfect, great, ok, hold_start, miss, hold_partial ...) about `notes[ev.index]`. Idle restores due before it are made first. Returns the changes.
func on_judge(ev: Dictionary, notes: Array) -> Array:
	var i := int(ev.get("index", -1))
	if i < 0 or i >= notes.size():
		return []
	var n: Dictionary = notes[i]
	if not n.has("track_t"):
		return []
	var voice := str(n.get("voice", ""))
	if not _voices.has(voice):
		return []
	var t := float(ev.get("time", n["time"]))
	var out := advance(t, notes)
	match str(ev.get("kind", "")):
		"perfect", "great", "ok", "hold_start":
			out.append_array(_change(voice, false, t, "hit", i))
		"miss":
			out.append_array(_change(voice, true, t, "miss", i))
		"hold_partial":
			if absf(t - _ignore_t) > EPS:
				out.append_array(_change(voice, true, t, "let_go", i))
	return out


## The idle restores due by song time `now`, earliest first (ties by voice key).
func advance(now: float, notes: Array) -> Array:
	var due: Array = []
	for v in _wait:
		if float(_wait[v]["due"]) <= now + EPS:
			due.append(v)
	if due.is_empty():
		return []
	due.sort_custom(func(a: String, b: String) -> bool:
		var ta := float(_wait[a]["due"])
		var tb := float(_wait[b]["due"])
		return ta < tb if ta != tb else a < b)
	var out: Array = []
	for v in due:
		var w: Dictionary = _wait[v]
		_wait.erase(v)
		if _cue_within(str(v), int(w["after"]), float(w["from"]), notes):
			continue  # a cue of the voice comes within the wait: only a hit brings it back
		out.append_array(_change(str(v), false, float(w["due"]), "idle", -1))
	return out


## Whether a cue of `voice` after cue `after` falls no later than the wait after `from`.
func _cue_within(voice: String, after: int, from: float, notes: Array) -> bool:
	var limit := from + restore_beats * beat_s
	for j in range(after + 1, notes.size()):
		var n: Dictionary = notes[j]
		if n.has("track_t") and str(n.get("voice", "")) == voice and float(n["time"]) <= limit + EPS:
			return true
	return false


func _change(voice: String, muted: bool, t: float, reason: String, index: int) -> Array:
	if muted:
		_wait[voice] = {"due": t + restore_beats * beat_s, "from": t, "after": index}  # (every mute restarts the wait)
		if bool(_muted[voice]):
			return []
	else:
		_wait.erase(voice)
		if not bool(_muted[voice]):
			return []
	_muted[voice] = muted
	var ch := {"kind": "mute" if muted else "restore", "voice": voice, "t": t, "reason": reason}
	log.append(ch)
	return [ch]
