class_name TrialPhrase
extends RefCounted
## One rhythm phrase on the four pads, built from a pack's chart (the same WAV/MIDI import the run uses) and judged by the same PadJudge.
##
## A phrase is the cues of one difficulty tier of a pack's drums (or bass) over `beats` beats. It sits on the audio clock: `t0` is the song time its music
## group starts, cues fall at t0 + (window_from + k) beats for the cue at phrase beat k of the loop, so a hit lands on a beat of the music that is
## actually playing. Attempts append to one shared note list (the pad view and note lane read it), each attempt judged on its own.

const TICKS := 960
const COUNT_IN_BEATS := 2.0  # the music plays this long before the first cue so its gain ramp is over

var level: Level
var judge: PadJudge
var beat_s := 60.0 / 174.0
var pass_credit := 0.6
var t0 := 0.0  # song time the attempt's music starts
var end_t := 0.0  # song time the last cue's window has closed
var first := 0  # index of this attempt's first note
var count := 0
var family := "drums"
var done := false
var passed := false
var credit := 0.0
var _seq := 0
var _next_id := 0


func setup(p_level: Level, p_judge: PadJudge, bpm: float, p_pass: float) -> void:
	level = p_level
	judge = p_judge
	beat_s = 60.0 / bpm
	pass_credit = p_pass


## Charts an attempt. `pack` is a RunData pack, `spec` a phrase of passages.json, `start_t` the song time of the attempt's music. Returns the note count.
func start(pack: Dictionary, spec: Dictionary, start_t: float) -> int:
	t0 = start_t
	family = str(spec["family"])
	done = false
	passed = false
	credit = 0.0
	first = level.notes.size()
	var beats := float(spec["beats"])
	var from := 0.0 if family == "bass" else COUNT_IN_BEATS  # the bass starts with its phrase; the drums have a count-in
	var cues: Array = pack["tiers"][str(int(spec["tier"]))]["drums" if family == "drums" else "bass"]
	var added: Array = []
	for c in cues:
		var beat := float(int(c[0])) / float(TICKS)
		if beat < from - 1e-6 or beat > from + beats - 1.5 + 1e-6:
			continue  # the last beats and a half stay empty: the final window and hold tails close before the result
		var local := beat - from
		var dur: int = int(c[1])
		if dur > 0:
			dur = mini(dur, int(round((beats - 1.0 - local) * TICKS)))
			if dur < 480:
				dur = 0
		var tm := t0 + (beat) * beat_s
		var fam := str(c[3]) if c.size() > 3 else family
		added.append({"id": "t%05d" % _next_id, "tick": int(round(tm / beat_s * TICKS)), "duration_ticks": dur, "end_tick": int(round(tm / beat_s * TICKS)) + dur, "time": tm,
			"end_time": tm + float(dur) / float(TICKS) * beat_s, "pad": int(c[2]), "button": int(c[2]), "family": fam, "lane": fam, "slot_id": fam,
			"type": "hold" if dur > 0 else "tap", "seq": _seq, "phase": 0, "block": _seq, "voice": family})
		_next_id += 1
	added.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	for a in added:
		level.notes.append(a)
	count = added.size()
	var pads := {}
	if family == "drums":
		pads = {"1": {"family": "kick", "ref": ""}, "4": {"family": "snare", "ref": ""}}
	else:
		for p in range(1, 5):
			pads[str(p)] = {"family": "bass", "ref": ""}
	var s_tick := int(round(t0 / beat_s * TICKS))
	level.sections.append({"id": "trial_%d" % _seq, "start_tick": s_tick, "end_tick": s_tick + int((from + beats) * TICKS), "mode": family, "length_bars": int(beats / 4.0), "pads": pads})
	level.duration_ticks = maxi(level.duration_ticks, s_tick + int((from + beats) * TICKS))
	_seq += 1
	end_t = t0 + (from + beats) * beat_s
	judge.sync_notes()
	return count


## Advance to song time `t`; returns {passed, credit} once the attempt is over (the same dictionary again afterwards), else {}.
func update(t: float) -> Dictionary:
	if level == null:
		return {}
	judge.update(t)
	if done:
		return {"passed": passed, "credit": credit}
	if t < end_t:
		return {}
	var sum := 0.0
	for i in range(first, first + count):
		sum += judge.credit[i] if judge.is_resolved(i) else 0.0
	credit = 1.0 if count == 0 else sum / float(count)
	passed = credit >= pass_credit
	done = true
	return {"passed": passed, "credit": credit}


## Credit so far (for the pad strip's meter).
func progress() -> Dictionary:
	var got := 0.0
	var res := 0
	for i in range(first, first + count):
		if judge.is_resolved(i):
			res += 1
			got += judge.credit[i]
	return {"index": _seq, "cues": count, "resolved": res, "credit": got}
