class_name DuelEngine
extends RefCounted
## One wizard's side of the duel (no nodes, no clock of its own: song time in, events out). The music never stops: every two
## bars (a phrase) carries cues on the four pads, drums or bass by the pattern in duel.json, taken from the same recorded pack
## the opponent plays, at the tier that rises as the duel goes on. Phrase j covers beats 8j to 8j+8; at beat 8j+7.5, after
## its last cue's window has closed, the phrase is judged:
##   passed (at least pass_credit of its cues hit)  a spell of the power its precision, family, tier and streak earn, and the streak grows;
##   failed                                          the spell fizzles and the streak is lost.
## The result goes to the DuelMatch (and to the other phone), which lands both wizards' spells together.

const TICKS := 960
const CUE_AHEAD := 2  # phrases charted ahead of the one being played (the notes fall for up to two seconds)

var rules: DuelRules
var rdata: RunData
var level: Level
var judge := PadJudge.new()
var beat_s := 60.0 / 174.0
var streak := 0
var stopped := false
var results: Array = []  # every result made, in order

var _pack: Dictionary = {}
var _events: Array = []
var _note_id := 0
var _charted := -1
var _next_decision := 0
var _first_note_of := {}
var _count_of := {}
var _strays_at_last := 0


func _init(p_rules: DuelRules = null, p_rdata: RunData = null) -> void:
	if p_rules != null:
		setup(p_rules, p_rdata)


func setup(p_rules: DuelRules, p_rdata: RunData) -> void:
	rules = p_rules
	rdata = p_rdata
	beat_s = 60.0 / float(rdata.cfg["timing"]["bpm"])
	_pack = rdata.packs[str(rules.cfg["music"]["chart"])]


func t_of(beat: float) -> float:
	return beat * beat_s


func phrase_s() -> float:
	return float(rules.phrase_beats()) * beat_s


func decision_t(j: int) -> float:
	return t_of(float(j * rules.phrase_beats()) + float(rules.cfg["timing"]["decision_beat"]))


func count_in_s() -> float:
	return t_of(float(rules.cfg["timing"]["count_in_beats"]))


func phrase_at(t: float) -> int:
	return int(floor(maxf(t, 0.0) / phrase_s()))


func begin() -> void:
	level = Level.new()
	level.mode = "defense"
	level.bpm = float(rdata.cfg["timing"]["bpm"])
	level.ticks_per_beat = TICKS
	level.beats_per_bar = 4
	level.sequence_threshold = float(rules.cfg["pass_credit"])
	judge = PadJudge.new()
	var w: Dictionary = rdata.cfg["judgement"]["windows_ms"]
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(rdata.cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	streak = 0
	stopped = false
	results = []
	_events = []
	_note_id = 0
	_charted = -1
	_next_decision = 0
	_first_note_of = {}
	_count_of = {}
	_strays_at_last = 0
	_chart_to(CUE_AHEAD)


func press(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.press(pad, t, touch)


func release(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.release(pad, t, touch)


## Advance to song time `t`; returns the events that became due: {"kind": "result", ...}, {"kind": "judge", ...}, {"kind": "cues", ...}.
func update(t: float) -> Array:
	if level == null:
		return []
	judge.update(t)
	for ev in judge.drain_events():
		_events.append({"kind": "judge", "event": ev, "t": t})
	_chart_to(phrase_at(t) + CUE_AHEAD)
	var guard := 0
	while not stopped and guard < 8 and t >= decision_t(_next_decision):
		guard += 1
		_decide(_next_decision)
		_next_decision += 1
	var out := _events
	_events = []
	return out


func _decide(j: int) -> void:
	var td := decision_t(j)
	_chart_to(j + CUE_AHEAD)
	judge.update(td)
	var fam := rules.family_of(j)
	var tier := rules.tier_of(j)
	var n := int(_count_of.get(j, 0))
	var first := int(_first_note_of.get(j, 0))
	var credit := 1.0
	var weighted := 0.0
	var perfect := 0
	var hit := 0
	if n > 0:
		var sum := 0.0
		var w: Dictionary = rdata.cfg["judgement"]["windows_ms"]
		for i in range(first, first + n):
			var c: float = judge.credit[i] if judge.is_resolved(i) else 0.0
			sum += c
			if c > 0.0:
				hit += 1
				var d := absf(judge.delta_ms[i]) if not is_nan(judge.delta_ms[i]) else float(w["accept"])
				var g := rules.grade_weight(d, float(w["perfect"]), float(w["great"]))
				weighted += g * minf(c, 1.0)
				if d <= float(w["perfect"]):
					perfect += 1
		credit = sum / float(n)
	var strays := judge.strays - _strays_at_last
	_strays_at_last = judge.strays
	var passed := credit >= float(rules.cfg["pass_credit"]) - 1e-9
	var prec := rules.precision(weighted, n, strays)
	var power := 0
	if passed:
		power = rules.power10(prec, fam, tier, streak)
		streak += 1
	else:
		streak = 0
	var res := {"kind": "result", "t": td, "j": j, "cast": passed, "power10": power, "credit": snappedf(credit, 0.001), "precision": snappedf(prec, 0.001),
		"family": fam, "tier": tier, "cues": n, "hit": hit, "perfect": perfect, "strays": strays, "streak": streak}
	results.append(res)
	_events.append(res)


## Charts every phrase up to `last` that is not charted yet.
func _chart_to(last: int) -> void:
	while _charted < last:
		_charted += 1
		_chart_phrase(_charted)


## The cues of phrase `j`: the drums or bass of the pack's chart at its tier, taken from the loop position the music is at in that phrase.
func _chart_phrase(j: int) -> void:
	var fam := rules.family_of(j)
	var tier := rules.tier_of(j)
	var span := rules.phrase_beats()
	var cues: Array = _pack["tiers"][str(clampi(tier, 1, RunData.TIERS))]["drums" if fam == "drums" else "bass"]
	var pack_beats := int(_pack["phrase_beats"])
	var pos := (j * span) % pack_beats
	var last_beat := float(rules.cfg["timing"]["decision_beat"]) - 0.25  # a hold must end before the judgement
	var added: Array = []
	for c in cues:
		var off: int = int(c[0]) - pos * TICKS
		if off < 0 or off >= span * TICKS:
			continue
		var bib := float(off) / float(TICKS)
		if bib > last_beat + 1e-6:
			continue
		var dur: int = int(c[1])
		if dur > 0:
			dur = mini(dur, int(round((last_beat - bib) * TICKS)))
			if dur < 480:
				dur = 0
		var gbeat := float(j * span) + bib
		var tm := gbeat * beat_s
		var fam_c := str(c[3]) if c.size() > 3 else fam
		added.append({"id": "w%05d" % _note_id, "tick": int(round(gbeat * TICKS)), "duration_ticks": dur, "end_tick": int(round(gbeat * TICKS)) + dur, "time": tm,
			"end_time": tm + float(dur) / float(TICKS) * beat_s, "pad": int(c[2]), "button": int(c[2]), "family": fam_c, "lane": fam_c, "slot_id": fam_c,
			"type": "hold" if dur > 0 else "tap", "seq": j, "phase": 0, "block": j, "voice": fam, "kind": "phrase", "enc": ""})
		_note_id += 1
	added.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	_first_note_of[j] = level.notes.size()
	_count_of[j] = added.size()
	for a in added:
		level.notes.append(a)
	var pads := {}
	if fam == "drums":
		pads = {"1": {"family": "kick", "ref": ""}, "4": {"family": "snare", "ref": ""}}
	else:
		for p in range(1, 5):
			pads[str(p)] = {"family": "bass", "ref": ""}
	var s_tick := j * span * TICKS
	level.sections.append({"id": "duel_p%d" % j, "start_tick": s_tick, "end_tick": s_tick + span * TICKS, "mode": fam, "length_bars": span / 4, "pads": pads})
	level.duration_ticks = maxi(level.duration_ticks, s_tick + span * TICKS)
	judge.sync_notes()
	_events.append({"kind": "cues", "phrase": j, "family": fam, "tier": tier, "count": added.size()})


## The pad strip's meter: the credit of the phrase being played.
func progress_at(t: float) -> Dictionary:
	var j := phrase_at(t)
	if not _first_note_of.has(j) or int(_count_of[j]) == 0:
		return {}
	var first := int(_first_note_of[j])
	var got := 0.0
	var done := 0
	for i in range(first, first + int(_count_of[j])):
		if judge.is_resolved(i):
			done += 1
			got += judge.credit[i]
	return {"index": j, "cues": int(_count_of[j]), "resolved": done, "credit": got}
