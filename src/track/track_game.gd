class_name TrackGame
extends RefCounted
## The rules of track mode as a plain class: no nodes, no audio, driven by the song time passed in, so a test can step
## it exactly. It owns the cues of the chosen chart, judges presses and releases through the existing PadJudge (same
## windows and hold rules as missions), and keeps one mute flag per voice, keyed by the voice the cue belongs to (the
## four pads all play the voice that has the focus, so a pad says nothing about the voice):
##
##  - every voice starts audible;
##  - a missed cue (resolved at the cue time plus the accept window) or a hold let go early mutes that cue's voice;
##  - the next cue hit for that voice (a tap, or a hold started, on any pad that cue asks for) restores it;
##  - a muted voice also restores by itself `restore_after_idle_beats` beats after it was muted, when it has no cue
##    left to hit before then (so a miss just before the focus moves on, or ahead of a long rest, does not silence
##    the rest);
##  - backing is not a voice here and never mutes; a voice that is not the focus has no cues, so nothing the player
##    does can mute it;
##  - a press on the wrong pad does not play a cue (the cue is missed when its window closes) and a press with no cue
##    near is a stray and costs nothing.
##
## Everything resolves at a deterministic time (the press, the release, the cue plus the window, the idle deadline), so
## the event log and the numbers are the same at any frame rate. Events are drained with drain_events() and also kept
## in `log`. Kinds: "hit" (grade, hold), "miss", "hold_kept", "hold_let_go", "stray", "mute" (reason miss | let_go),
## "restore" (reason hit | idle). Events carry the `pad` they are about (0 for an idle restore) and, except "stray", the cue's `voice`.

const GRADES := ["perfect", "great", "ok"]

var pack: TrackPack
var chart_name := ""
var start_s := 0.0
var cues: Array = []  # the judge's notes: {time, end_time, type, pad, seq, family (= voice), voice, t, dur, conf}; cues before start_s are left out
var judge: PadJudge
var log: Array = []  # every event, in order
var voices: Array = []  # [{key, label, kind}] in the pack's order
var focus: TrackFocus  # which voice is being played when

var _events: Array = []
var _muted: Dictionary = {}  # voice key -> bool
var _muted_since: Dictionary = {}  # voice key -> song time the voice went silent (-1 when audible)
var _muted_total: Dictionary = {}  # voice key -> seconds silent so far
var _restore_at: Dictionary = {}  # voice key -> song time of the pending idle restore
var _voice_cues: Dictionary = {}  # voice key -> Array of cue indexes in time order
var _stats: Dictionary = {}  # voice key -> counters
var _strays := 0
var _suppress_mutes := false
var _finished_at := -1.0


## Sets up the game on `p`'s chart `chart` (an empty name means the pack's default chart), skipping the cues before `from_s`.
func setup(p: TrackPack, chart: String = "", from_s: float = 0.0) -> void:
	pack = p
	chart_name = chart if not chart.is_empty() else p.default_chart
	start_s = from_s
	cues.clear()
	log.clear()
	_events.clear()
	_suppress_mutes = false
	_finished_at = -1.0
	voices.clear()
	_voice_cues.clear()
	_muted.clear()
	_muted_since.clear()
	_muted_total.clear()
	_stats.clear()
	_strays = 0
	focus = p.focus_state()
	for v in p.voices:
		var key: String = v["key"]
		voices.append({"key": key, "label": str(v["label"]), "kind": str(v["kind"])})
		_voice_cues[key] = []
		_muted[key] = false
		_muted_since[key] = -1.0
		_muted_total[key] = 0.0
		_stats[key] = {"cues": 0, "perfect": 0, "great": 0, "ok": 0, "misses": 0, "holds": 0, "hold_let_go": 0}
	_restore_at.clear()
	var raw: Array = p.charts.get(chart_name, [])
	for c in raw:
		var t: float = c["t"]
		if t < from_s:
			continue
		var i := cues.size()
		var pad: int = c["pad"]
		var voice: String = c["voice"]
		cues.append({"time": t, "end_time": t + float(c["dur"]), "type": "hold" if float(c["dur"]) > 0.0 else "tap", "pad": pad,
			"seq": i, "family": voice, "voice": voice, "t": t, "dur": float(c["dur"]), "conf": float(c["conf"])})
		_voice_cues[voice].append(i)
		_stats[voice]["cues"] += 1
	judge = PadJudge.new()
	judge.setup(cues)


## Whether the voice with key `key` is silent now.
func is_muted(key: String) -> bool:
	return bool(_muted.get(key, false))


## The key of every voice that is silent now.
func muted_keys() -> Array:
	var out: Array = []
	for v in voices:
		if bool(_muted[v["key"]]):
			out.append(v["key"])
	return out


## The voice being played at song time `t` ("" when nothing is to be played).
func focus_voice(t: float) -> String:
	return focus.voice_at(t)


## The label of a voice (its key when it has none).
func label_of(key: String) -> String:
	for v in voices:
		if v["key"] == key:
			return str(v["label"])
	return key


func drain_events() -> Array:
	var out := _events
	_events = []
	return out


## Resolves everything that is due by song time `now`: misses, finished holds, idle restores.
func advance(now: float) -> void:
	judge.update(now)
	_pump(now)


## A pad goes down at `now`. Returns the judge's result for the press ("perfect", "great", "ok", "hold_start", "stray", "ignored").
func press(pad: int, now: float, touch_id: int = 0) -> Dictionary:
	var r := judge.press(pad, now, touch_id)
	_pump(now)
	return r


## A pad comes up at `now`. A hold released more than the tolerance before its tail is let go early.
func release(pad: int, now: float, touch_id: int = 0) -> Dictionary:
	var r := judge.release(pad, now, touch_id)
	_pump(now)
	return r


## The game was paused at `now`: holds in progress end where they stand without muting (a pause is not a mistake).
func pause(now: float) -> void:
	judge.update(now)
	_pump(now)
	_suppress_mutes = true
	judge.pause_interrupt(now)
	_pump(now)
	_suppress_mutes = false


## The track is over at song time `end_s`: resolves what is left and closes the sounding-time books.
func finish(end_s: float) -> void:
	advance(end_s)
	_finished_at = end_s
	for v in voices:
		var key: String = v["key"]
		if float(_muted_since[key]) >= 0.0:
			_muted_total[key] += maxf(end_s - float(_muted_since[key]), 0.0)
			_muted_since[key] = end_s


## State of cue `i` for the falling-note display: "pending", "hit" or "miss".
func cue_state(i: int) -> String:
	return judge.cue_state(i)


## Hold progress 0..1 on a pad, -1 when it holds nothing.
func hold_progress(pad: int, now: float) -> float:
	return judge.hold_progress(pad, now)


func hits(key: String) -> int:
	var s: Dictionary = _stats[key]
	return int(s["perfect"]) + int(s["great"]) + int(s["ok"])


func total_hits() -> int:
	var n := 0
	for v in voices:
		n += hits(v["key"])
	return n


func total_misses() -> int:
	var n := 0
	for v in voices:
		n += int(_stats[v["key"]]["misses"])
	return n


func total_strays() -> int:
	return _strays


## Per voice: cues, hits by grade, misses, holds let go, muted seconds, and the share of the track's time (from the
## start second to the end) the voice was sounding; in total: cues, hits, misses and strays. Call after finish() for
## the final numbers.
func summary() -> Dictionary:
	var end := _finished_at if _finished_at >= 0.0 else float(judge._now if judge._now > -INF else start_s)
	var span := maxf(end - start_s, 0.0)
	var out_voices: Array = []
	var cue_total := 0
	var hit_total := 0
	var miss_total := 0
	for v in voices:
		var key: String = v["key"]
		var s: Dictionary = _stats[key]
		var muted_s: float = _muted_total[key]
		if _finished_at < 0.0 and float(_muted_since[key]) >= 0.0:
			muted_s += maxf(end - float(_muted_since[key]), 0.0)
		var h := hits(key)
		out_voices.append({"key": key, "label": v["label"], "kind": v["kind"], "cues": int(s["cues"]),
			"hits": {"perfect": int(s["perfect"]), "great": int(s["great"]), "ok": int(s["ok"])}, "hit_total": h,
			"misses": int(s["misses"]), "holds": int(s["holds"]), "hold_let_go": int(s["hold_let_go"]),
			"muted_s": snappedf(muted_s, 0.001), "sounding_share": snappedf(1.0 - muted_s / span, 0.0001) if span > 0.0 else 1.0})
		cue_total += int(s["cues"])
		hit_total += h
		miss_total += int(s["misses"])
	return {"id": pack.id, "title": pack.title, "chart": chart_name, "start_s": start_s, "end_s": snappedf(end, 0.001),
		"cues": cue_total, "hits": hit_total, "misses": miss_total, "strays": _strays, "voices": out_voices}


## Takes what the judge resolved and turns it into game events and mute changes, in time order.
func _pump(now: float) -> void:
	var batch := judge.drain_events()
	# the judge resolves pad by pad; the game's log is in time order (ties by pad, then the judge's order), whatever the frame size
	for i in batch.size():
		batch[i]["_n"] = i
	batch.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var ta: float = a["time"]
		var tb: float = b["time"]
		if ta != tb:
			return ta < tb
		return int(a["_n"]) < int(b["_n"]))
	for ev in batch:
		var t := float(ev["time"])
		_fire_idle_restores(t)
		var pad := int(ev["pad"])
		var voice := str(ev.get("family", ""))
		match str(ev["kind"]):
			"perfect", "great", "ok", "hold_start":
				var grade: String = str(ev["grade"]) if ev["kind"] == "hold_start" else str(ev["kind"])
				_stats[voice][grade] += 1
				if ev["kind"] == "hold_start":
					_stats[voice]["holds"] += 1
				_emit({"kind": "hit", "pad": pad, "voice": voice, "time": t, "grade": grade, "hold": ev["kind"] == "hold_start", "cue": int(ev["index"]),
					"delta_ms": snappedf(float(ev["delta_ms"]), 0.1)})
				_set_muted(voice, pad, false, t, "hit")
			"hold_complete":
				_emit({"kind": "hold_kept", "pad": pad, "voice": voice, "time": t, "cue": int(ev["index"])})
			"hold_partial":
				_stats[voice]["hold_let_go"] += 1
				_emit({"kind": "hold_let_go", "pad": pad, "voice": voice, "time": t, "cue": int(ev["index"]), "coverage": snappedf(float(ev["coverage"]), 0.001)})
				if not _suppress_mutes:
					_set_muted(voice, pad, true, t, "let_go", int(ev["index"]))
			"miss":
				_stats[voice]["misses"] += 1
				_emit({"kind": "miss", "pad": pad, "voice": voice, "time": t, "cue": int(ev["index"])})
				_set_muted(voice, pad, true, t, "miss", int(ev["index"]))
			"stray":
				_strays += 1
				_emit({"kind": "stray", "pad": pad, "time": t})
	_fire_idle_restores(now)


func _emit(ev: Dictionary) -> void:
	_events.append(ev)
	log.append(ev)


func _set_muted(voice: String, pad: int, muted: bool, t: float, reason: String, cue_index: int = -1) -> void:
	if muted:
		# the idle deadline restarts at every mute (a second miss while silent), unless a cue is near enough to bring it back
		var wait := pack.restore_after_idle_beats * pack.beat_s()
		var next_t := _next_cue_time(voice, cue_index)
		if next_t < 0.0 or next_t - t > wait + 1e-9:
			_restore_at[voice] = t + wait
		else:
			_restore_at.erase(voice)
		if bool(_muted[voice]):
			return
		_muted[voice] = true
		_muted_since[voice] = t
		_emit({"kind": "mute", "pad": pad, "voice": voice, "time": t, "reason": reason})
	else:
		_restore_at.erase(voice)
		if not bool(_muted[voice]):
			return
		_muted[voice] = false
		_muted_total[voice] += maxf(t - float(_muted_since[voice]), 0.0)
		_muted_since[voice] = -1.0
		_emit({"kind": "restore", "pad": pad, "voice": voice, "time": t, "reason": reason})


## Time of the first cue of `voice` after cue `index` (-1 when there is none).
func _next_cue_time(voice: String, index: int) -> float:
	for i in _voice_cues[voice]:
		if int(i) > index:
			return float(cues[i]["time"])
	return -1.0


func _fire_idle_restores(upto: float) -> void:
	if _restore_at.is_empty():
		return
	var due: Array = []
	for voice in _restore_at:
		if float(_restore_at[voice]) <= upto:
			due.append(voice)
	due.sort_custom(func(a: String, b: String) -> bool:
		var ta: float = _restore_at[a]
		var tb: float = _restore_at[b]
		return ta < tb if ta != tb else a < b)
	for voice in due:
		_set_muted(str(voice), 0, false, float(_restore_at[voice]), "idle")
