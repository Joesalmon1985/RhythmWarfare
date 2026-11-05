class_name TrackGame
extends RefCounted
## The rules of track mode as a plain class: no nodes, no audio, driven by the song time passed in, so a test can step
## it exactly. It owns the cues of the chosen chart, judges presses and releases through the existing PadJudge (same
## windows and hold rules as missions), and keeps one mute flag per voice:
##
##  - every voice starts audible;
##  - a missed cue (resolved at the cue time plus the accept window) or a hold let go early mutes that pad's voice;
##  - the next cue hit on that pad (a tap, or a hold started) restores it;
##  - a muted voice also restores by itself `restore_after_idle_beats` beats after it was muted, when it has no cue
##    left to hit before then (so a miss ahead of a long rest does not silence the rest);
##  - backing is not a voice here and never mutes; a press with no cue near is a stray and costs nothing.
##
## Everything resolves at a deterministic time (the press, the release, the cue plus the window, the idle deadline), so
## the event log and the numbers are the same at any frame rate. Events are drained with drain_events() and also kept
## in `log`. Kinds: "hit" (grade, hold), "miss", "hold_kept", "hold_let_go", "stray", "mute" (reason miss | let_go),
## "restore" (reason hit | idle).

const GRADES := ["perfect", "great", "ok"]

var pack: TrackPack
var chart_name := ""
var start_s := 0.0
var cues: Array = []  # the judge's notes: {time, end_time, type, pad, seq, family, t, dur, conf}; cues before start_s are left out
var judge: PadJudge
var log: Array = []  # every event, in order
var voices: Array = []  # [{key, label, pad}] in pad order, index = pad - 1

var _events: Array = []
var _muted: Dictionary = {}  # pad -> bool
var _muted_since: Dictionary = {}  # pad -> song time the voice went silent (-1 when audible)
var _muted_total: Dictionary = {}  # pad -> seconds silent so far
var _restore_at: Dictionary = {}  # pad -> song time of the pending idle restore
var _pad_cues: Dictionary = {}  # pad -> Array of cue indexes in time order
var _stats: Dictionary = {}  # pad -> counters
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
	_pad_cues = {1: [], 2: [], 3: [], 4: []}
	for pad in range(1, 5):
		var v := p.voice_of_pad(pad)
		voices.append({"key": str(v.get("key", "")), "label": str(v.get("label", "")), "pad": pad})
		_muted[pad] = false
		_muted_since[pad] = -1.0
		_muted_total[pad] = 0.0
		_stats[pad] = {"cues": 0, "perfect": 0, "great": 0, "ok": 0, "misses": 0, "holds": 0, "hold_let_go": 0, "strays": 0}
	_restore_at.clear()
	var raw: Array = p.charts.get(chart_name, [])
	for c in raw:
		var t: float = c["t"]
		if t < from_s:
			continue
		var i := cues.size()
		var pad: int = c["pad"]
		cues.append({"time": t, "end_time": t + float(c["dur"]), "type": "hold" if float(c["dur"]) > 0.0 else "tap", "pad": pad,
			"seq": i, "family": str(p.voice_of_pad(pad).get("key", "")), "t": t, "dur": float(c["dur"]), "conf": float(c["conf"])})
		_pad_cues[pad].append(i)
		_stats[pad]["cues"] += 1
	judge = PadJudge.new()
	judge.setup(cues)


func is_muted(pad: int) -> bool:
	return bool(_muted.get(pad, false))


## The key of every voice that is silent now.
func muted_keys() -> Array:
	var out: Array = []
	for v in voices:
		if bool(_muted[int(v["pad"])]):
			out.append(v["key"])
	return out


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
	for pad in range(1, 5):
		if float(_muted_since[pad]) >= 0.0:
			_muted_total[pad] += maxf(end_s - float(_muted_since[pad]), 0.0)
			_muted_since[pad] = end_s


## State of cue `i` for the falling-note display: "pending", "hit" or "miss".
func cue_state(i: int) -> String:
	return judge.cue_state(i)


## Hold progress 0..1 on a pad, -1 when it holds nothing.
func hold_progress(pad: int, now: float) -> float:
	return judge.hold_progress(pad, now)


func hits(pad: int) -> int:
	var s: Dictionary = _stats[pad]
	return int(s["perfect"]) + int(s["great"]) + int(s["ok"])


func total_hits() -> int:
	var n := 0
	for pad in range(1, 5):
		n += hits(pad)
	return n


func total_misses() -> int:
	var n := 0
	for pad in range(1, 5):
		n += int(_stats[pad]["misses"])
	return n


func total_strays() -> int:
	var n := 0
	for pad in range(1, 5):
		n += int(_stats[pad]["strays"])
	return n


## Per voice and in total: cues, hits by grade, misses, holds let go, strays, and the share of the track's time (from
## the start second to the end) the voice was sounding. Call after finish() for the final numbers.
func summary() -> Dictionary:
	var end := _finished_at if _finished_at >= 0.0 else float(judge._now if judge._now > -INF else start_s)
	var span := maxf(end - start_s, 0.0)
	var out_voices: Array = []
	var cue_total := 0
	var hit_total := 0
	var miss_total := 0
	for v in voices:
		var pad: int = v["pad"]
		var s: Dictionary = _stats[pad]
		var muted_s: float = _muted_total[pad]
		if _finished_at < 0.0 and float(_muted_since[pad]) >= 0.0:
			muted_s += maxf(end - float(_muted_since[pad]), 0.0)
		var h := hits(pad)
		out_voices.append({"key": v["key"], "label": v["label"], "pad": pad, "cues": int(s["cues"]),
			"hits": {"perfect": int(s["perfect"]), "great": int(s["great"]), "ok": int(s["ok"])}, "hit_total": h,
			"misses": int(s["misses"]), "holds": int(s["holds"]), "hold_let_go": int(s["hold_let_go"]), "strays": int(s["strays"]),
			"muted_s": snappedf(muted_s, 0.001), "sounding_share": snappedf(1.0 - muted_s / span, 0.0001) if span > 0.0 else 1.0})
		cue_total += int(s["cues"])
		hit_total += h
		miss_total += int(s["misses"])
	return {"id": pack.id, "title": pack.title, "chart": chart_name, "start_s": start_s, "end_s": snappedf(end, 0.001),
		"cues": cue_total, "hits": hit_total, "misses": miss_total, "strays": total_strays(), "voices": out_voices}


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
		match str(ev["kind"]):
			"perfect", "great", "ok", "hold_start":
				var grade: String = str(ev["grade"]) if ev["kind"] == "hold_start" else str(ev["kind"])
				_stats[pad][grade] += 1
				if ev["kind"] == "hold_start":
					_stats[pad]["holds"] += 1
				_emit({"kind": "hit", "pad": pad, "time": t, "grade": grade, "hold": ev["kind"] == "hold_start", "cue": int(ev["index"]),
					"delta_ms": snappedf(float(ev["delta_ms"]), 0.1)})
				_set_muted(pad, false, t, "hit")
			"hold_complete":
				_emit({"kind": "hold_kept", "pad": pad, "time": t, "cue": int(ev["index"])})
			"hold_partial":
				_stats[pad]["hold_let_go"] += 1
				_emit({"kind": "hold_let_go", "pad": pad, "time": t, "cue": int(ev["index"]), "coverage": snappedf(float(ev["coverage"]), 0.001)})
				if not _suppress_mutes:
					_set_muted(pad, true, t, "let_go", int(ev["index"]))
			"miss":
				_stats[pad]["misses"] += 1
				_emit({"kind": "miss", "pad": pad, "time": t, "cue": int(ev["index"])})
				_set_muted(pad, true, t, "miss", int(ev["index"]))
			"stray":
				_stats[pad]["strays"] += 1
				_emit({"kind": "stray", "pad": pad, "time": t})
	_fire_idle_restores(now)


func _emit(ev: Dictionary) -> void:
	_events.append(ev)
	log.append(ev)


func _set_muted(pad: int, muted: bool, t: float, reason: String, cue_index: int = -1) -> void:
	if muted:
		# the idle deadline restarts at every mute (a second miss while silent), unless a cue is near enough to bring it back
		var wait := pack.restore_after_idle_beats * pack.beat_s()
		var next_t := _next_cue_time(pad, cue_index)
		if next_t < 0.0 or next_t - t > wait + 1e-9:
			_restore_at[pad] = t + wait
		else:
			_restore_at.erase(pad)
		if bool(_muted[pad]):
			return
		_muted[pad] = true
		_muted_since[pad] = t
		_emit({"kind": "mute", "pad": pad, "voice": voices[pad - 1]["key"], "time": t, "reason": reason})
	else:
		_restore_at.erase(pad)
		if not bool(_muted[pad]):
			return
		_muted[pad] = false
		_muted_total[pad] += maxf(t - float(_muted_since[pad]), 0.0)
		_muted_since[pad] = -1.0
		_emit({"kind": "restore", "pad": pad, "voice": voices[pad - 1]["key"], "time": t, "reason": reason})


## Time of the first cue on `pad` after cue `index` (-1 when there is none).
func _next_cue_time(pad: int, index: int) -> float:
	for i in _pad_cues[pad]:
		if int(i) > index:
			return float(cues[i]["time"])
	return -1.0


func _fire_idle_restores(upto: float) -> void:
	if _restore_at.is_empty():
		return
	var due: Array = []
	for pad in _restore_at:
		if float(_restore_at[pad]) <= upto:
			due.append(pad)
	due.sort_custom(func(a: int, b: int) -> bool:
		var ta: float = _restore_at[a]
		var tb: float = _restore_at[b]
		return ta < tb if ta != tb else a < b)
	for pad in due:
		_set_muted(int(pad), false, float(_restore_at[pad]), "idle")
