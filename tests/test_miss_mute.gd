extends TestCase
## A missed cue silences its instrument's stem until the next hit on it; the backing track never mutes; a phase that
## does not cue a family brings it back; a restart starts unmuted.

const PACK := "m01_first_watch"


func _level(pack: String = PACK) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack))
	assert_eq(loaded["errors"], [], pack)
	return loaded["level"]


func _stem_keys(level: Level, family: String) -> Array:
	var keys: Array = []
	for k in level.stem_family:
		if level.stem_family[k] == family:
			keys.append(k)
	return keys


## Plays the mission in 1/60 s frames until `t_end`; a note is pressed at its time (a hold is released at its tail) when
## `hit` says so. Returns the "stem" events the match produced, each with the frame time it was drained at.
func _run(m: Match, level: Level, t_end: float, hit: Callable) -> Array:
	var stems: Array = []
	var t := 0.0
	var next := 0
	var holding := {}
	while t < t_end:
		for pad in holding.keys():
			if t >= holding[pad]:
				m.release(pad, holding[pad], 1)
				holding.erase(pad)
		while next < level.notes.size() and float(level.notes[next]["time"]) <= t:
			var n: Dictionary = level.notes[next]
			if hit.call(n):
				m.press(int(n["pad"]), float(n["time"]), 1)
				if n["type"] == "hold":
					holding[int(n["pad"])] = float(n["end_time"])
			next += 1
		m.advance(t)
		for ev in m.drain_events():
			if ev["kind"] == "stem":
				var e: Dictionary = ev.duplicate()
				e["frame_time"] = t
				stems.append(e)
		t += 1.0 / 60.0
	return stems


func _notes_of(level: Level, family: String) -> Array:
	var out: Array = []
	for n in level.notes:
		if n["family"] == family:
			out.append(n)
	return out


func _events_for(stems: Array, keys: Array, muted: bool) -> Array:
	var out: Array = []
	for e in stems:
		if keys.has(e["stem"]) and e["muted"] == muted:
			out.append(e)
	return out


func _phase_of(level: Level, tick: int) -> int:
	for i in level.sections.size():
		if tick >= int(level.sections[i]["start_tick"]) and tick < int(level.sections[i]["end_tick"]):
			return i
	return -1


func test_a_missed_cue_mutes_its_stem_and_the_next_hit_restores_it() -> void:
	var level := _level()
	var kicks := _notes_of(level, "kick")
	var keys := _stem_keys(level, "kick")
	assert_true(kicks.size() >= 3 and not keys.is_empty(), "the pack has kick cues and a kick stem")
	var first_id: String = kicks[0]["id"]
	var m := Match.new()
	m.setup(level)
	var stems := _run(m, level, float(kicks[1]["time"]) + 0.3, func(n: Dictionary) -> bool: return n["id"] != first_id)
	var mutes := _events_for(stems, keys, true)
	var unmutes := _events_for(stems, keys, false)
	assert_eq(mutes.size(), keys.size(), "one mute per kick stem")
	assert_eq(unmutes.size(), keys.size(), "one unmute per kick stem")
	if mutes.is_empty() or unmutes.is_empty():
		return
	assert_near(float(mutes[0]["time"]), float(kicks[0]["time"]) + m.pad_judge.accept_s, 0.001, "muted when the cue's window closes")
	assert_near(float(unmutes[0]["time"]), float(kicks[1]["time"]), 0.001, "restored by the next kick hit")
	assert_true(float(mutes[0]["frame_time"]) <= float(mutes[0]["time"]) + 0.05, "the event is produced in the frame of the miss")
	for k in keys:
		assert_false(m.stems_muted[k], "%s is back" % k)
	assert_false(m.family_muted("kick"))


func test_a_missed_bass_cue_leaves_the_kick_alone() -> void:
	var level := _level()
	var bass := _notes_of(level, "bass")
	var kick_keys := _stem_keys(level, "kick")
	var bass_keys := _stem_keys(level, "bass")
	assert_true(not bass.is_empty() and not kick_keys.is_empty() and not bass_keys.is_empty())
	var m := Match.new()
	m.setup(level)
	var stems := _run(m, level, float(bass[0]["time"]) + m.pad_judge.accept_s + 0.1, func(n: Dictionary) -> bool: return n["family"] != "bass")
	assert_true(_events_for(stems, bass_keys, true).size() >= 1, "bass is silenced")
	for k in kick_keys:
		assert_eq(_events_for(stems, [k], true).size(), 0, "no mute event for kick stem %s" % k)
		assert_false(m.stems_muted[k])
	assert_true(m.family_muted("bass"))
	assert_false(m.family_muted("kick"))
	assert_false(m.family_muted("snare"))


func test_the_backing_track_never_mutes() -> void:
	var level := _level()
	var other := _stem_keys(level, "other")
	assert_false(other.is_empty(), "the pack has a backing stem")
	var m := Match.new()
	m.setup(level)
	# no input at all: every cue is missed
	var stems := _run(m, level, level.duration_seconds() * 0.5, func(_n: Dictionary) -> bool: return false)
	assert_true(stems.size() > 0, "the other stems did mute")
	for k in other:
		assert_eq(_events_for(stems, [k], true).size(), 0, "no mute for %s" % k)
		assert_false(m.stems_muted[k])
	# and a judge event that claims the backing family is ignored
	m._judge_to_stems([{"kind": "miss", "family": "other", "pad": 1, "index": 0, "seq": 0, "time": 1.0}], 1.0)
	for k in other:
		assert_false(m.stems_muted[k])
	assert_false(m.family_muted("other"))


func test_a_phase_that_does_not_cue_a_family_restores_it() -> void:
	var level := _level()
	# a phase p that cues family F while phase p + 1 does not
	for p in level.sections.size() - 1:
		for fam in ["kick", "snare", "bass"]:
			var in_p := 0
			var in_next := 0
			for n in level.notes:
				if n["family"] != fam:
					continue
				var ph := _phase_of(level, int(n["tick"]))
				if ph == p:
					in_p += 1
				elif ph == p + 1:
					in_next += 1
			if in_p == 0 or in_next > 0:
				continue
			var boundary := level.tick_to_seconds(int(level.sections[p]["end_tick"]))
			var keys := _stem_keys(level, fam)
			var m := Match.new()
			m.setup(level)
			var stems := _run(m, level, boundary + 0.5, func(n: Dictionary) -> bool: return n["family"] != fam)
			var mutes := _events_for(stems, keys, true)
			var unmutes := _events_for(stems, keys, false)
			assert_true(mutes.size() >= keys.size(), "%s muted in phase %d" % [fam, p])
			assert_eq(unmutes.size(), keys.size(), "%s restored once" % fam)
			if not unmutes.is_empty():
				assert_near(float(unmutes[0]["time"]), boundary, 0.03, "%s restored at the phase change" % fam)
			for k in keys:
				assert_false(m.stems_muted[k], "%s is back after the phase change" % k)
			return
	fail("the pack has no family that one phase cues and the next does not")


func test_a_failed_hold_mutes_and_a_partial_hold_with_credit_restores() -> void:
	var level := _level("m03_hold_the_line")
	var holds: Array = []
	for n in level.notes:
		if n["type"] == "hold" and n["family"] == "bass":
			holds.append(n)
	assert_true(holds.size() >= 2, "mission 3 holds bass")
	if holds.size() < 2:
		return
	var keys := _stem_keys(level, "bass")
	var m := Match.new()
	m.setup(level)
	# the first hold is never started (a miss), the second is pressed and let go halfway (partial credit)
	var a: Dictionary = holds[0]
	var b: Dictionary = holds[1]
	m.advance(float(a["time"]) + m.pad_judge.accept_s + 0.05)
	assert_true(m.family_muted("bass"), "an unheld hold mutes its family")
	m.drain_events()
	m.press(int(b["pad"]), float(b["time"]), 1)
	var mid := (float(b["time"]) + float(b["end_time"])) * 0.5
	m.advance(mid)
	m.release(int(b["pad"]), mid, 1)
	m.advance(mid + 0.02)
	var restored := false
	for ev in m.drain_events():
		if ev["kind"] == "stem" and keys.has(ev["stem"]) and not ev["muted"]:
			restored = true
	assert_true(restored, "a partly held hold counts as a hit")
	assert_false(m.family_muted("bass"))


func test_restart_starts_unmuted() -> void:
	var level := _level()
	var m := Match.new()
	m.setup(level)
	_run(m, level, 6.0, func(_n: Dictionary) -> bool: return false)
	assert_true(m.family_muted("kick") or m.family_muted("snare"), "misses muted something")
	m.setup(level)
	for k in m.stems_muted:
		assert_false(m.stems_muted[k], "%s starts unmuted" % k)
	assert_true(m.drain_events().is_empty())
