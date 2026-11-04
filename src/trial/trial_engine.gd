class_name TrialEngine
extends RefCounted
## The dungeon as one unbroken piece of rhythm play (no nodes, no clock of its own: song time in, events out).
##
## The music game never stops: every 16-beat block (four bars) carries cues on the four pads. Blocks alternate between
##   AMBIENT  cues of the passage's own tier, while the choices float over the scene, and
##   PHRASE   the cues of the chosen option (a fight gets its own, harder one), judged for a pass.
## Every 16 beats, at beat 12.75 of a block (after its last cue's window has closed, with the next block's cues about to fall in), a decision tick happens:
##   after a PHRASE block   it is judged. A pass moves to the option's passage (the consequence and the next choices appear and a 4-bar choice window opens);
##                          a fail keeps the passage, the failed option becomes the default, and the window opens again.
##   after an AMBIENT block the window that opened 16 beats ago closes: the option the player selected, or the marked default when they selected none, is
##                          committed. An option with a phrase charts that phrase as the next block; one without moves on at once; an exit leaves.
## So the player always has exactly four bars to choose, and if they do not the game moves on with the default. The first window opens during the count-in.

const TICKS := 960
const BLOCK_BEATS := 16
const DECISION_BEAT := 12.75
const CUE_SPAN := 12.0

var data: TrialData
var rdata: RunData
var flow: TrialFlow
var level: Level
var judge := PadJudge.new()
var beat_s := 60.0 / 174.0
var pass_credit := 0.6

var block := 0  # the block being played (the one containing song time t)
var kind := "ambient"  # kind of block `block`: "ambient" | "phrase"
var window_open := false
var window_t0 := 0.0
var window_t1 := 0.0
var selected := -1  # the player's pick in the open window (-1: none, so the default applies)
var exited := false
var exit_to := ""
var fight_open := ""  # encounter id of the phrase block being played ("" when none)
var phrase_choice := -1
var blocks_log: Array = []  # [{block, kind, passage, credit}]

var _events: Array = []
var _pack: Dictionary = {}
var _note_id := 0
var _next_tick := 0  # index j of the next decision tick
var _credit_of_block := {}
var _first_note_of := {}
var _count_of := {}


func _init(p_data: TrialData = null, p_rdata: RunData = null) -> void:
	if p_data != null:
		setup(p_data, p_rdata)


func setup(p_data: TrialData, p_rdata: RunData) -> void:
	data = p_data
	rdata = p_rdata
	beat_s = 60.0 / float(rdata.cfg["timing"]["bpm"])
	pass_credit = float(data.raw.get("pass_credit", 0.6))
	_pack = rdata.packs[str(data.raw["music"]["chart"])]


## Song time of beat `b` (the first downbeat is time 0).
func t_of(b: float) -> float:
	return b * beat_s


func decision_t(j: int) -> float:
	return t_of(float(j * BLOCK_BEATS) + DECISION_BEAT)


## Length of the count-in (the first window opens at the start of it, so it too lasts four bars).
func count_in_s() -> float:
	return t_of(float(BLOCK_BEATS) - DECISION_BEAT)


func begin() -> void:
	flow = TrialFlow.new(data)
	level = Level.new()
	level.mode = "defense"
	level.bpm = float(rdata.cfg["timing"]["bpm"])
	level.ticks_per_beat = TICKS
	level.beats_per_bar = 4
	level.sequence_threshold = pass_credit
	judge = PadJudge.new()
	var w: Dictionary = rdata.cfg["judgement"]["windows_ms"]
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(rdata.cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	block = 0
	kind = "ambient"
	_events = []
	_note_id = 0
	_next_tick = 0
	selected = -1
	exited = false
	exit_to = ""
	fight_open = ""
	phrase_choice = -1
	blocks_log = []
	_chart_block(0, "ambient", {})
	_emit({"kind": "passage", "passage": flow.passage, "t": -count_in_s(), "consequence": "", "failure": ""})
	_open_window(-count_in_s())


func _emit(ev: Dictionary) -> void:
	_events.append(ev)


func choices() -> Array:
	return flow.choices()


## The option that applies if the player does not choose: the failed option after a failure (try it again), else the one marked `default`.
func default_index() -> int:
	if flow.retry_index >= 0:
		return flow.retry_index
	var cs := flow.choices()
	for i in cs.size():
		if bool(cs[i].get("default", false)):
			return i
	return 0


func effective_choice() -> int:
	return selected if selected >= 0 else default_index()


## The player picks (or changes their pick) while the window is open.
func select(i: int) -> bool:
	if not window_open or i < 0 or i >= flow.choices().size():
		return false
	selected = i
	return true


func press(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.press(pad, t, touch)


func release(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.release(pad, t, touch)


## Seconds left in the open window (0 when none).
func window_left(t: float) -> float:
	return maxf(window_t1 - t, 0.0) if window_open else 0.0


func _open_window(t0: float) -> void:
	window_open = true
	window_t0 = t0
	window_t1 = t0 + float(BLOCK_BEATS) * beat_s
	selected = -1
	_emit({"kind": "window_open", "t": t0, "closes": window_t1, "default": default_index(), "passage": flow.passage})


## Advance to song time `t`; returns the events that became due.
func update(t: float) -> Array:
	if level == null:
		return []
	judge.update(t)
	for ev in judge.drain_events():
		_emit({"kind": "judge", "event": ev, "t": t})
	var guard := 0
	while not exited and guard < 8 and t >= decision_t(_next_tick):
		guard += 1
		_decide(_next_tick)
		_next_tick += 1
	block = int(floor(maxf(t, 0.0) / (float(BLOCK_BEATS) * beat_s)))
	var out := _events
	_events = []
	return out


func _decide(j: int) -> void:
	var td := decision_t(j)
	judge.update(td)
	if kind == "phrase" and j == phrase_block():
		_judge_phrase(j, td)
	else:
		_commit_window(j, td)


func phrase_block() -> int:
	return _phrase_j


var _phrase_j := -1


func _judge_phrase(j: int, td: float) -> void:
	var credit := _block_credit(j)
	blocks_log.append({"block": j, "kind": "phrase", "passage": flow.passage, "credit": credit})
	var res := flow.phrase_done(credit >= pass_credit, credit)
	_phrase_j = -1
	fight_open = ""
	_emit({"kind": "result", "t": td, "result": res["kind"], "fight": res["fight"], "outcome": res["outcome"], "credit": credit, "text": res["text"], "passage": flow.passage})
	_emit({"kind": "passage", "passage": flow.passage, "t": td, "consequence": flow.consequence, "failure": flow.failure})
	kind = "ambient"
	_chart_block(j + 1, "ambient", {})
	_emit({"kind": "mix", "t": t_of(float((j + 1) * BLOCK_BEATS)), "gains": {"drums": 1.0, "bass": 0.45, "other": 0.45}})
	_open_window(td)


func _commit_window(j: int, td: float) -> void:
	var i := effective_choice()
	var defaulted := selected < 0
	window_open = false
	blocks_log.append({"block": j, "kind": "ambient", "passage": flow.passage, "credit": _block_credit(j)})
	var r := flow.select(i)
	_emit({"kind": "commit", "t": td, "choice": i, "defaulted": defaulted, "passage": flow.passage, "label": str(flow.choices()[i].get("label", "")) if r["kind"] != "move" else ""})
	match str(r["kind"]):
		"phrase":
			kind = "phrase"
			_phrase_j = j + 1
			phrase_choice = i
			fight_open = str(r["encounter"])
			_chart_block(j + 1, "phrase", r["phrase"])
			var fam := str(r["phrase"]["family"])
			_emit({"kind": "mix", "t": t_of(float((j + 1) * BLOCK_BEATS)), "gains": {"drums": 1.0, "bass": 0.5, "other": 0.45} if fam == "drums" else {"drums": 0.5, "bass": 1.0, "other": 0.5}})
			_emit({"kind": "phrase", "t": td, "block": j + 1, "choice": i, "encounter": fight_open, "label": str(r["phrase"].get("label", ""))})
		"move":
			kind = "ambient"
			_emit({"kind": "passage", "passage": flow.passage, "t": td, "consequence": flow.consequence, "failure": ""})
			_chart_block(j + 1, "ambient", {})
			_open_window(td)
		"exit":
			exited = true
			exit_to = str(r["exit"])
			_emit({"kind": "exit", "t": td, "to": exit_to})
		_:
			kind = "ambient"
			_chart_block(j + 1, "ambient", {})
			_open_window(td)


func _block_credit(b: int) -> float:
	if not _first_note_of.has(b):
		return 1.0
	var n := int(_count_of[b])
	if n == 0:
		return 1.0
	var sum := 0.0
	var first := int(_first_note_of[b])
	for i in range(first, first + n):
		sum += judge.credit[i] if judge.is_resolved(i) else 0.0
	return sum / float(n)


## Appends the cues of block `b`: the drums or bass of the pack's chart at the tier of the phrase (or of the passage, for ambient blocks), on the loop position
## the music is at in that block. Cues sit in beats 0 to 12 of the block; the last four are empty.
func _chart_block(b: int, k: String, spec: Dictionary) -> void:
	var fam := "drums"
	var tier := int(flow.current().get("tier", 1))
	if k == "phrase":
		fam = str(spec["family"])
		tier = int(spec["tier"])
	var cues: Array = _pack["tiers"][str(clampi(tier, 1, RunData.TIERS))]["drums" if fam == "drums" else "bass"]
	var phrase_beats := int(_pack["phrase_beats"])
	var pos := (b * BLOCK_BEATS) % phrase_beats
	var added: Array = []
	for c in cues:
		var off: int = int(c[0]) - pos * TICKS
		if off < 0 or off >= BLOCK_BEATS * TICKS:
			continue
		var bib := float(off) / float(TICKS)
		if bib > CUE_SPAN + 1e-6:
			continue
		var dur: int = int(c[1])
		if dur > 0:
			dur = mini(dur, int(round((CUE_SPAN - bib) * TICKS)))
			if dur < 480:
				dur = 0
		var gbeat := float(b * BLOCK_BEATS) + bib
		var tm := gbeat * beat_s
		var fam_c := str(c[3]) if c.size() > 3 else fam
		added.append({"id": "d%05d" % _note_id, "tick": int(round(gbeat * TICKS)), "duration_ticks": dur, "end_tick": int(round(gbeat * TICKS)) + dur, "time": tm,
			"end_time": tm + float(dur) / float(TICKS) * beat_s, "pad": int(c[2]), "button": int(c[2]), "family": fam_c, "lane": fam_c, "slot_id": fam_c,
			"type": "hold" if dur > 0 else "tap", "seq": b, "phase": 0, "block": b, "voice": fam, "kind": k, "enc": fight_open if k == "phrase" else ""})
		_note_id += 1
	added.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	_first_note_of[b] = level.notes.size()
	_count_of[b] = added.size()
	for a in added:
		level.notes.append(a)
	var pads := {}
	if fam == "drums":
		pads = {"1": {"family": "kick", "ref": ""}, "4": {"family": "snare", "ref": ""}}
	else:
		for p in range(1, 5):
			pads[str(p)] = {"family": "bass", "ref": ""}
	var s_tick := b * BLOCK_BEATS * TICKS
	level.sections.append({"id": "trial_b%d" % b, "start_tick": s_tick, "end_tick": s_tick + BLOCK_BEATS * TICKS, "mode": fam, "length_bars": 4, "pads": pads})
	level.duration_ticks = maxi(level.duration_ticks, s_tick + BLOCK_BEATS * TICKS)
	judge.sync_notes()
	_emit({"kind": "cues", "block": b, "family": fam, "count": added.size(), "phrase": k == "phrase"})


## The pad strip's meter: the credit of the block being played.
func progress_at(_t: float) -> Dictionary:
	if not _first_note_of.has(block) or int(_count_of[block]) == 0:
		return {}
	var first := int(_first_note_of[block])
	var got := 0.0
	var done := 0
	for i in range(first, first + int(_count_of[block])):
		if judge.is_resolved(i):
			done += 1
			got += judge.credit[i]
	return {"index": block, "cues": int(_count_of[block]), "resolved": done, "credit": got}
