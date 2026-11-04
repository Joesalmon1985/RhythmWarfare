extends TestCase
## The Bassment, the wizard's dungeon: the curated passages, the walk by defaults, reachability, items and secrets, fights with retry, luck tests, deaths and the victory,
## the four-bar window with its default, the music that never stops, the phone-sized scene and the wizard's option in the Warehouse.

const PATH := "res://content/trial/passages.json"


func _data() -> TrialData:
	var d := TrialData.load_default()
	assert_eq(d.errors, [], "the dungeon data validates")
	return d


## The id of the passage titled `title` (titles are unique).
func _id(d: TrialData, title: String) -> int:
	for n in d.passages:
		if str(d.passages[n]["title"]) == title:
			return int(n)
	fail("no passage titled '%s'" % title)
	return -1


## Plays a route through the flow alone: every phrase passes. `picks` are choice indexes.
func _walk(picks: Array, start: int = -1) -> TrialFlow:
	var f := TrialFlow.new(_data(), start)
	for i in picks:
		var r := f.select(i)
		if r["kind"] == "phrase":
			f.phrase_done(true, 1.0)
	return f


func _default_index(f: TrialFlow) -> int:
	var cs: Array = f.choices()
	for i in cs.size():
		if bool(cs[i].get("default", false)):
			return i
	return 0


func _count(d: TrialData, what: String) -> int:
	var n := 0
	for k in d.passages:
		var p: Dictionary = d.passages[k]
		if what == "side" or what == "secret":
			n += 1 if bool(p.get(what, false)) else 0
		elif what == "death" or what == "victory":
			n += 1 if str(p.get("kind", "")) == what else 0
		for c in p["choices"]:
			if what == "fight" and c.has("encounter"):
				n += 1
			if what == "luck" and c.has("test"):
				n += 1
			if what == "gated" and c.has("requires"):
				n += 1
	return n


# --- the content -----------------------------------------------------------------------------------------------------------

func test_the_dungeon_is_curated_and_complete() -> void:
	var d := _data()
	assert_eq(str(d.raw["title"]), "The Bassment")
	var real := d.passages.size() - 1
	assert_true(real >= 60 and real <= 80, "60 to 80 passages (%d), plus the defeat passage 0" % real)
	assert_true(d.zones.size() >= 12 and d.zones.size() <= 17, "12 to 17 zones (%d)" % d.zones.size())
	var fights := _count(d, "fight")
	assert_true(fights >= 8 and fights <= 12, "about ten fights (%d)" % fights)
	assert_eq(d.encounters.size(), fights, "each fight is a different creature")
	assert_true(_count(d, "luck") >= 5 and _count(d, "luck") <= 8, "about six luck tests (%d)" % _count(d, "luck"))
	assert_true(_count(d, "death") >= 6 and _count(d, "death") <= 9, "about six deaths, with the defeat passage (%d)" % _count(d, "death"))
	assert_eq(_count(d, "victory"), 1, "one victory")
	assert_true(_count(d, "side") >= 12, "side passages that rejoin (%d)" % _count(d, "side"))
	assert_true(_count(d, "secret") >= 4 and _count(d, "gated") >= 3, "secrets that need an item (%d passages, %d gated choices)" % [_count(d, "secret"), _count(d, "gated")])
	var titles := {}
	for n in d.passages:
		var p: Dictionary = d.passages[n]
		assert_false(titles.has(str(p["title"])), "titles are unique: " + str(p["title"]))
		titles[str(p["title"])] = true
		var sentences: int = str(p["text"]).count(". ") + str(p["text"]).count("? ") + 1
		assert_true(sentences >= 2 and sentences <= 5, "passage %d has two to four sentences of text (%d)" % [n, sentences])
		assert_eq(int(p["tier"]), int(d.zones[str(p["zone"])]["tier"]), "passage %d's tier is its zone's" % n)
	for z in d.zones:
		assert_true(str(d.zones[z]["look"]).length() > 20, "zone %s has its one-line look" % z)


func test_no_trace_of_the_book_it_was_adapted_from_remains() -> void:
	var text := FileAccess.get_file_as_string(PATH).to_lower()
	for word in ["throm", "igbut", "bloodbeast", "sukumvit", "manticore", "deathtrap", "livingstone", "emerald", "sapphire", "diamond", "ocr", "verified", "trial of champions", "troglodyte"]:
		assert_false(text.contains(word), "'%s' does not appear in the dungeon data" % word)
	for gone in ["res://content/trial/book_graph.json", "res://content/trial/book_text.json", "res://content/trial/quest_map.json", "res://src/trial/trial_book.gd", "res://tools/trial/build_book.py"]:
		assert_false(FileAccess.file_exists(gone), "%s is removed" % gone)
	var play := FileAccess.get_file_as_string("res://src/trial/trial_play.gd").to_lower()
	assert_false(play.contains("verified") or play.contains("ocr "), "the scene shows no provenance footer")


func test_every_passage_is_reachable_and_only_deaths_and_the_victory_end() -> void:
	var d := _data()
	var reach := d.reachable()
	assert_eq(reach.size(), d.passages.size() - 1, "all passages but the defeat one can be reached from the start")
	var exits := []
	for n in d.passages:
		var kind := str(d.passage(n).get("kind", "normal"))
		for c in d.choices(n):
			if c.has("exit"):
				exits.append(n)
				assert_true(kind in ["death", "victory"], "passage %d offers an exit but is %s" % [n, kind])
				assert_eq((c as Dictionary).get("default", false), true)
			else:
				assert_true(passages_has(d, int(c["to"])), "link valid")
		if kind == "death" or kind == "victory":
			assert_eq((d.choices(n) as Array).size(), 1)
		else:
			assert_true((d.choices(n) as Array).size() >= 1)
	assert_eq(exits.size(), _count(d, "death") + 1, "every death and the victory has the way back")


func passages_has(d: TrialData, n: int) -> bool:
	return d.passages.has(n)


func test_the_defaults_alone_walk_from_the_entrance_to_the_victory() -> void:
	var d := _data()
	var walk := d.default_walk()
	assert_true(walk.size() >= 25 and walk.size() <= 45, "a real walk in a reasonable number of steps (%d)" % walk.size())
	assert_eq(walk[0], d.start)
	assert_eq(str(d.passage(int(walk[walk.size() - 1]))["kind"]), "victory")
	var f := TrialFlow.new(d)
	var steps := 0
	while f.state != TrialFlow.State.ENDED and steps < 200:
		f.select(_default_index(f))
		if f.state == TrialFlow.State.PHRASE:
			f.phrase_done(true, 1.0)
		steps += 1
	assert_eq(f.exit, "warehouse")
	assert_eq(f.passage, int(walk[walk.size() - 1]), "the flow walks the same way")
	assert_eq(f.visited, walk)
	var zones_seen := {}
	var last_tier := 0
	for n in walk:
		zones_seen[str(d.passage(int(n))["zone"])] = true
		assert_true(int(d.passage(int(n))["tier"]) >= last_tier, "the tier rises with depth along the walk")
		last_tier = int(d.passage(int(n))["tier"])
	assert_true(zones_seen.size() >= 12, "the walk crosses many zones (%d)" % zones_seen.size())
	assert_eq(last_tier, 4)


func test_tiers_run_from_one_to_four_and_fights_are_harder_than_the_phrases_around_them() -> void:
	var d := _data()
	var tiers := {}
	for n in d.passages:
		tiers[int(d.passage(n)["tier"])] = true
		for c in d.choices(n):
			if c.has("encounter"):
				assert_eq(int(c["lives"]), 3, "three lost phrases end the trial")
				var ft := int(d.phrases[str(c["phrase"])]["tier"])
				assert_true(ft >= 2, "a fight is never the easiest phrase")
				for c2 in d.choices(n):
					if not c2.has("encounter") and c2.get("phrase", null) != null:
						assert_true(ft >= int(d.phrases[str(c2["phrase"])]["tier"]), "passage %d: the fight's phrase is the harder one" % n)
	assert_eq(tiers.keys().size(), 4)


func test_the_music_block_names_a_pack_for_fights_too() -> void:
	var d := _data()
	var m: Dictionary = d.raw["music"]
	assert_eq(m["fight_audio"], m["audio"], "the fight pack defaults to the dungeon's pack")
	assert_eq(m["fight_chart"], m["chart"])
	var bad := FileAccess.get_file_as_string(PATH).replace("\"fight_chart\": \"lv1_warehouse_v1\"", "\"fight_chart\": \"nowhere\"")
	var f := FileAccess.open("user://test_trial_badpack.json", FileAccess.WRITE)
	f.store_string(bad)
	f.close()
	var d2 := TrialData.load_file("user://test_trial_badpack.json")
	assert_true(d2.errors.any(func(e: String) -> bool: return e.contains("fight_chart")), "a pack that does not exist is reported")
	DirAccess.remove_absolute("user://test_trial_badpack.json")


# --- items and secrets -------------------------------------------------------------------------------------------------------

func test_an_item_opens_a_shortcut_and_is_needed_to_see_it() -> void:
	var d := _data()
	var back := _id(d, "Behind the Counter")
	var plain := TrialFlow.new(d, back)
	assert_eq((plain.choices() as Array).size(), 1, "without the lamp only the trapdoor is on offer")
	assert_eq(plain.flags, [])
	var lit := TrialFlow.new(d, back)
	lit.flags = ["lamp"]
	assert_eq((lit.choices() as Array).size(), 2, "with the lamp the dark archway appears")
	assert_eq(str(lit.choices()[1]["requires"]), "lamp")
	lit.select(1)
	lit.phrase_done(true, 1.0)
	assert_eq(str(lit.current()["title"]), "The Dark Corridor")
	lit.select(0)
	lit.phrase_done(true, 1.0)
	lit.select(0)
	lit.phrase_done(true, 1.0)
	assert_eq(str(lit.current()["title"]), "The Mirror Mezzanine", "the shortcut skips the whole Fungus Farm")
	assert_false(_id(d, "The Mildew Pond") in lit.visited)
	var fork := TrialFlow.new(d, _id(d, "The Hall of Hands"))
	assert_eq((fork.choices() as Array).size(), 2)
	fork.flags = ["fork"]
	assert_eq((fork.choices() as Array).size(), 3)
	var token := TrialFlow.new(d, _id(d, "The Vault of Records"))
	token.flags = ["token"]
	assert_eq((token.choices() as Array).size(), 3)
	assert_eq((TrialFlow.new(d, _id(d, "The Vault of Records")).choices() as Array).size(), 2)


func test_items_are_found_by_winning_a_fight_or_taking_a_risk_and_announced() -> void:
	var d := _data()
	var f := TrialFlow.new(d, _id(d, "Lost Property"))
	assert_eq(f.select(0)["encounter"], "lampmoth")
	var r := f.phrase_done(true, 0.9)
	assert_eq(r["outcome"], "win")
	assert_eq(f.flags, ["lamp"], "beating the moth gives the lamp")
	assert_true(f.consequence.contains("You now carry the brass lamp"), f.consequence)
	var g := TrialFlow.new(d, _id(d, "The Humming Hall"))
	g.select(1)
	g.phrase_done(true, 1.0)
	assert_eq(g.flags, ["token"])
	var h := TrialFlow.new(d, _id(d, "The Rope Ledge"))
	h.select(1)
	h.phrase_done(true, 1.0)
	assert_eq(h.flags, ["fork"], "the luck test's pass finds the fork")
	var h2 := TrialFlow.new(d, _id(d, "The Rope Ledge"))
	h2.select(1)
	h2.phrase_done(false, 0.0)
	assert_eq(str(h2.current()["kind"]), "death")
	assert_eq(h2.flags, [])
	var all := TrialFlow.new(d, _id(d, "The Pit Floor"))
	all.select(0)
	all.phrase_done(true, 1.0)
	assert_eq(all.flags, ["fork"], "an item is held once")
	all.flags = ["fork"]
	all.select(0)  # the item is already held
	assert_eq((all.flags as Array).size(), 1)


func test_the_data_refuses_a_choice_that_needs_an_unknown_item_or_is_the_default() -> void:
	var text := FileAccess.get_file_as_string(PATH)
	var f := FileAccess.open("user://test_trial_badflag.json", FileAccess.WRITE)
	f.store_string(text.replace("\"requires\": \"lamp\"", "\"requires\": \"sword\""))
	f.close()
	var d := TrialData.load_file("user://test_trial_badflag.json")
	assert_true(d.errors.any(func(e: String) -> bool: return e.contains("sword")), "an unknown item is reported: %s" % str(d.errors))
	var f2 := FileAccess.open("user://test_trial_badflag.json", FileAccess.WRITE)
	f2.store_string(text.replace("\"requires\": \"token\"", "\"requires\": \"token\", \"default\": true"))
	f2.close()
	var d2 := TrialData.load_file("user://test_trial_badflag.json")
	assert_true(d2.errors.any(func(e: String) -> bool: return e.contains("default")), "a gated default is reported")
	DirAccess.remove_absolute("user://test_trial_badflag.json")
	var data := _data()
	for n in data.passages:  # the default of every passage is available to a player with no items
		var open: Array = data.choices_for(n, [])
		assert_true(open.any(func(c: Dictionary) -> bool: return bool(c.get("default", false))), "passage %d has a default for an empty-handed player" % n)


# --- routes, fights, luck, deaths ---------------------------------------------------------------------------------------------

func test_routes_rejoin() -> void:
	var d := _data()
	var ladder := _id(d, "The Ladder Foot")
	assert_eq(_walk([0]).passage, ladder, "the hatch")
	assert_eq(_walk([1, 0]).passage, ladder, "the chalk marks lead back to the same ladder")
	var cable := _id(d, "The Cable Run")
	var via_lamp := _walk([0, 0, 1, 1])  # ladder > cables > lost property > (leave) back to the cable run
	assert_eq(via_lamp.passage, cable)
	var stacks := _id(d, "The Crystal Stacks")
	assert_eq(_walk([0, 0, 0, 0, 0]).passage, stacks, "cables > junction > nest > stacks")
	assert_eq(_walk([0, 0, 0, 1]).passage, stacks, "the dash under the sparks (a pass) reaches the same hall")
	var boiler := _walk([0, 1, 0])
	assert_eq(str(boiler.current()["title"]), "The Flooded Boiler Room")
	assert_eq(str(_walk([0, 1, 0, 0]).current()["title"]), "The Dry Landing")
	assert_eq(_walk([0, 1, 0, 0, 0]).passage, stacks, "the boiler route and the cable route meet at the crystal hall")
	var rejoin := TrialFlow.new(d)
	for i in [1, 0, 0, 0, 0]:
		rejoin.select(i)
		if rejoin.state == TrialFlow.State.PHRASE:
			rejoin.phrase_done(true, 1.0)
	assert_true(_id(d, "The Ladder Foot") in rejoin.visited)


func test_a_failed_phrase_can_be_retried_and_a_fight_has_an_outcome() -> void:
	var d := _data()
	var f := TrialFlow.new(d, _id(d, "The Flooded Boiler Room"))
	var r := f.select(0)
	assert_eq(r["encounter"], "cable_eel")
	var lose := f.phrase_done(false, 0.2)
	assert_eq(lose["kind"], "fail")
	assert_eq(lose["outcome"], "lose", "a lost fight plays the losing animation")
	assert_eq(str(f.current()["title"]), "The Flooded Boiler Room", "still in the same passage with the same choices")
	assert_eq(f.retry_index, 0, "the failed choice is marked for a retry")
	assert_eq(f.failure, str(d.encounters["cable_eel"]["on_fail"]))
	assert_eq((f.choices() as Array).size(), 2)
	f.select(0)
	var win := f.phrase_done(true, 0.8)
	assert_eq(win["outcome"], "win")
	assert_eq(str(f.current()["title"]), "The Dry Landing")
	assert_true(f.consequence.begins_with(str(d.encounters["cable_eel"]["on_win"])))
	assert_eq(f.attempts, 0)
	var kinds: Array = f.history.map(func(h: Dictionary) -> String: return str(h["result"]))
	assert_eq(kinds.count("fail"), 1)


func test_every_fight_can_be_started_lost_and_won() -> void:
	var d := _data()
	var seen := {}
	for n in d.passages:
		for i in (d.choices(n) as Array).size():
			var c: Dictionary = d.choices(n)[i]
			if not c.has("encounter"):
				continue
			var f := TrialFlow.new(d, n)
			f.flags = ["lamp", "token", "fork"]
			var idx: int = (f.choices() as Array).find(c)
			assert_eq(f.select(idx)["encounter"], c["encounter"])
			assert_eq(f.phrase_done(false, 0.0)["outcome"], "lose")
			f.select(idx)
			assert_eq(f.phrase_done(true, 1.0)["outcome"], "win")
			assert_eq(f.passage, int(c["to"]))
			seen[str(c["encounter"])] = true
	assert_eq(seen.size(), d.encounters.size())


func test_only_death_and_victory_lead_back_to_the_warehouse_and_a_lost_fight_is_a_death() -> void:
	var d := _data()
	var dead := TrialFlow.new(d, _id(d, "Fried"))
	assert_eq(str(dead.current()["kind"]), "death")
	assert_eq(dead.select(0)["kind"], "exit")
	assert_eq(dead.exit, "warehouse")
	var f := TrialFlow.new(d, _id(d, "The Echo Chamber"))
	for k in 3:
		assert_eq(f.select(0)["kind"], "phrase")
		var r := f.phrase_done(false, 0.1)
		assert_eq(r["kind"], "fail")
		if k < 2:
			assert_eq(str(f.current()["title"]), "The Echo Chamber", "the first two defeats are retries")
	assert_eq(f.passage, 0, "the third is the end")
	assert_true(f.consequence.contains("Echo"), "with the creature's own defeat text")
	assert_eq(f.select(0)["kind"], "exit")
	var g := TrialFlow.new(d, _id(d, "The Service Hatch"))
	for k in 12:  # an ordinary phrase never ends the adventure however often it is failed
		g.select(0)
		g.phrase_done(false, 0.0)
	assert_eq(str(g.current()["title"]), "The Service Hatch")
	assert_eq(g.state, TrialFlow.State.SCENE)


func test_a_luck_test_goes_one_way_or_the_other_with_no_retry() -> void:
	var d := _data()
	var n := _id(d, "The Live Junction")
	for passed in [true, false]:
		var f := TrialFlow.new(d, n)
		f.select(1)
		var r := f.phrase_done(passed, 1.0 if passed else 0.0)
		assert_eq(r["kind"], "pass" if passed else "fail")
		assert_eq(str(f.current()["title"]), "The Crystal Stacks" if passed else "Singed")
		assert_eq(f.retry_index, -1, "no second go at luck")
		assert_eq(f.state, TrialFlow.State.SCENE)
	var door := TrialFlow.new(d, _id(d, "The Resonance Door"))
	door.select(0)
	door.phrase_done(false, 0.0)
	assert_eq(str(door.current()["title"]), "The Door Says No")
	door.select(0)
	door.phrase_done(true, 1.0)
	door.select(0)
	door.phrase_done(true, 1.0)
	assert_eq(str(door.current()["title"]), "The Echo Chamber")


func test_the_final_test_is_a_held_note_then_the_echo_not_a_lock() -> void:
	var d := _data()
	var door: Dictionary = d.choices(_id(d, "The Resonance Door"))[0]
	assert_true(door.has("test"))
	assert_eq(str(d.phrases[str(door["phrase"])]["family"]), "bass", "a held note on the bass")
	var echo: Dictionary = d.choices(_id(d, "The Echo Chamber"))[0]
	assert_eq(str(echo["encounter"]), "echo")
	assert_eq(int(d.phrases[str(echo["phrase"])]["tier"]), 4)
	var win: Dictionary = d.choices(_id(d, "The Last Landing"))[0]
	assert_eq(str(d.passage(int(win["to"]))["kind"]), "victory")


# --- the engine ----------------------------------------------------------------------------------------------------------------

## Plays the engine by hand: `bot` is "perfect" (every cue), "none" or "no_fights" (every cue but a fight's); `picks` is [[song time, choice index], ...].
func _drive(e: TrialEngine, bot: String, until: float, picks: Array = []) -> Array:
	var log: Array = []
	var t := -e.count_in_s()
	var pressed := {}
	var released := {}
	var done := {}
	while t < until and not e.exited:
		for k in picks.size():
			if t >= float(picks[k][0]) and not done.has(k):
				done[k] = true
				e.select(int(picks[k][1]))
		log.append_array(e.update(t))
		if bot != "none":
			for i in range(maxi(e.level.notes.size() - 300, 0), e.level.notes.size()):
				var n: Dictionary = e.level.notes[i]
				if bot == "no_fights" and str(n.get("enc", "")) != "":
					continue
				if not pressed.has(i) and float(n["time"]) <= t:
					pressed[i] = true
					e.press(int(n["pad"]), float(n["time"]))
				if pressed.has(i) and not released.has(i) and n["type"] == "hold" and float(n["end_time"]) <= t:
					released[i] = true
					e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return log


func _kinds(log: Array, kind: String) -> Array:
	return log.filter(func(x: Dictionary) -> bool: return x["kind"] == kind)


func _engine() -> TrialEngine:
	var e := TrialEngine.new(_data(), RunData.load_default())
	e.begin()
	return e


func _titles(e: TrialEngine, log: Array) -> Array:
	return _kinds(log, "passage").map(func(p: Dictionary) -> String: return str(e.data.passage(int(p["passage"]))["title"]))


func test_the_music_game_never_stops() -> void:
	var e := _engine()
	_drive(e, "perfect", 70.0 * e.beat_s)
	var times: Array = []
	for n in e.level.notes:
		times.append(float(n["time"]))
	times.sort()
	var max_gap := 0.0
	for i in range(1, times.size()):
		if times[i] > 0.0 and times[i] < 60.0 * e.beat_s:
			max_gap = maxf(max_gap, (times[i] - times[i - 1]) / e.beat_s)
	assert_true(max_gap <= 6.0, "no more than six beats without a cue, through windows, phrases and results (longest %.2f beats)" % max_gap)
	for b in 4:
		var count := 0
		for n in e.level.notes:
			if int(n["block"]) == b:
				count += 1
		assert_true(count >= 3, "block %d carries cues (%d)" % [b, count])
	assert_true(e.level.notes.size() > 0 and float(e.level.notes[0]["time"]) >= 0.0)


func test_a_choice_window_is_four_bars_and_the_default_is_taken_when_nobody_chooses() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 120.0 * e.beat_s)
	var opens := _kinds(log, "window_open")
	assert_true(opens.size() >= 3)
	for o in opens:
		assert_near((float(o["closes"]) - float(o["t"])) / e.beat_s, 16.0, 1e-6, "the window is 16 beats: four bars")
	var commits := _kinds(log, "commit")
	assert_true(commits.size() >= 2)
	for c in commits:
		assert_true(bool(c["defaulted"]), "nobody chose")
	assert_eq(_titles(e, log).slice(0, 4), ["The Service Hatch", "The Ladder Foot", "The Cable Run", "The Live Junction"], "the defaults go down the ladder and along the cables")
	assert_false(e.exited, "and the dungeon goes on: nothing here sends the player back")


func test_a_perfect_player_who_never_chooses_walks_to_the_victory_and_only_then_leaves() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 1800.0 * e.beat_s)
	assert_true(e.exited, "the walk ended")
	assert_eq(e.exit_reason, "victory")
	var passages: Array = _kinds(log, "passage").map(func(p: Dictionary) -> int: return int(p["passage"]))
	assert_eq(str(e.data.passage(passages[passages.size() - 1])["title"]), "Daylight")
	assert_eq(passages, e.data.default_walk(), "the engine walks the default walk")
	assert_eq(_kinds(log, "exit").size(), 1, "one exit, at the end")
	var results: Array = _kinds(log, "result")
	assert_true(results.all(func(r: Dictionary) -> bool: return r["result"] == "pass"))


func test_the_commit_lands_on_the_decision_beat_of_the_window_that_closes() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 20.0 * e.beat_s)
	var c: Dictionary = _kinds(log, "commit")[0]
	assert_near(float(c["t"]), e.decision_t(0), 1e-6)
	assert_near(float(c["t"]) / e.beat_s, 12.75, 1e-6)
	assert_near(e.count_in_s() / e.beat_s, 3.25, 1e-6, "the first window opens in the count-in")


func test_a_pick_beats_the_default_and_can_be_changed_until_the_window_closes() -> void:
	var e := _engine()
	var t := e.decision_t(0)
	var log := _drive(e, "perfect", 40.0 * e.beat_s, [[1.0, 0], [2.0, 1], [t + 0.5, 0]])
	var first: Dictionary = _kinds(log, "commit")[0]
	assert_eq(int(first["choice"]), 1, "the last pick before the window closed (the later one came too late)")
	assert_false(bool(first["defaulted"]))
	assert_true(e.select(0) == false or e.window_open, "after the commit the old window no longer takes picks")
	assert_true("Chalk on the Wall" in _titles(e, log), "the chalk marks")


func test_a_pass_shows_the_consequence_and_the_next_choices() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 40.0 * e.beat_s)
	var res: Dictionary = _kinds(log, "result")[0]
	assert_eq(res["result"], "pass")
	var ladder := _id(e.data, "The Ladder Foot")
	var after := _kinds(log, "passage").filter(func(p: Dictionary) -> bool: return int(p["passage"]) == ladder)
	assert_eq(after.size(), 1)
	assert_true(str(after[0]["consequence"]) != "")
	var ev := _kinds(log, "window_open").filter(func(w: Dictionary) -> bool: return int(w["passage"]) == ladder)
	assert_eq(ev.size(), 1, "and its choices are open at once")
	assert_near(float(ev[0]["t"]), float(res["t"]), 1e-6)


func test_a_failed_phrase_reopens_the_window_with_the_failed_option_as_the_default() -> void:
	var e := _engine()
	var log := _drive(e, "none", 36.0 * e.beat_s)
	var res := _kinds(log, "result")
	assert_true(res.size() >= 1)
	assert_eq(res[0]["result"], "fail")
	assert_eq(str(e.flow.current()["title"]), "The Service Hatch", "still in the first passage")
	assert_eq(e.flow.retry_index, 0)
	assert_eq(e.default_index(), 0, "doing nothing tries the same option again")
	assert_true(e.window_open)


func _pick_time(e: TrialEngine, window: int) -> float:
	return 1.0 if window == 0 else e.decision_t(2 * window - 1) + 1.0


func test_the_fight_loses_then_the_retry_wins() -> void:
	var e := _engine()
	var block := 16.0 * e.beat_s
	# hatch (default), the warm stairs (pick 1), the stairs (default), then the eel (default fight) played badly, then retried
	var picks := [[_pick_time(e, 1), 1]]
	var log := _drive(e, "no_fights", 9.0 * block, picks)
	var results: Array = _kinds(log, "result")
	var fights := results.filter(func(r: Dictionary) -> bool: return bool(r["fight"]))
	assert_true(fights.size() >= 1, str(results.map(func(r: Dictionary) -> String: return str(r["result"]))))
	assert_eq(fights[0]["outcome"], "lose")
	assert_eq(str(e.flow.current()["title"]), "The Flooded Boiler Room", "the lost fight stays in the boiler room")
	var e2 := _engine()
	var log2 := _drive(e2, "perfect", 10.0 * block, picks)
	assert_true("The Dry Landing" in _titles(e2, log2), "a perfect player passes the fight: %s" % str(_titles(e2, log2)))
	assert_true(_kinds(log2, "result").any(func(r: Dictionary) -> bool: return bool(r["fight"]) and r["outcome"] == "win"))


# --- the scene -------------------------------------------------------------------------------------------------------------------

func _trial_scene(bot: String) -> Dictionary:
	OS.set_environment("RW_TRIAL_VIRTUAL", "1")
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/trial/trial_play.tscn") as PackedScene).instantiate()
	scene.bot = bot
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	var exits: Array = []
	scene.exit_launcher = func(where: String) -> void: exits.append(where)
	return {"host": host, "scene": scene, "exits": exits}


## Steps the scene's virtual clock until `cond` holds (or `limit_s` of song time has passed). Returns whether it held.
func _until(scene: Node, cond: Callable, limit_s: float = 90.0) -> bool:
	var t := 0.0
	while t < limit_s:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		t += 1.0 / 30.0
		if cond.call():
			return true
	return false


func _free_scene(d: Dictionary) -> void:
	(d["host"] as Control).queue_free()
	OS.set_environment("RW_TRIAL_VIRTUAL", "")


func _scene_at(title: String, bot: String) -> Dictionary:
	OS.set_environment("RW_TRIAL_START", str(_id(_data(), title)))
	var d := _trial_scene(bot)
	OS.set_environment("RW_TRIAL_START", "")
	return d


func _title_is(scene: Node, title: String) -> bool:
	return str(scene.engine.flow.current()["title"]) == title


func test_the_scene_floats_choices_over_pads_that_keep_playing() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	assert_eq(scene._buttons.size(), 2, "two floating choices")
	for b in scene._buttons:
		assert_true((b as Button).size.x >= 140.0 and (b as Button).size.y >= 40.0, "a big enough target on a phone")
	assert_true(scene._buttons[0].text.contains("[DEFAULT]"), "one is marked as the default")
	assert_false(scene._buttons[1].text.contains("[DEFAULT]"))
	assert_true(scene._pic.texture != null, "a fixed illustrated scene")
	assert_true(scene._desc.text.length() > 40, "with a short description")
	assert_eq(scene._title.text, "THE SERVICE HATCH")
	assert_eq(scene._tag.text, "The Service Hatch", "the footer names the zone and makes no claim about where the text came from")
	assert_true(scene._choice_layer.visible)
	scene.pick(1)
	assert_true(scene._buttons[1].text.contains("[CHOSEN]") and not scene._buttons[0].text.contains("[DEFAULT]"), "a pick replaces the default mark")
	scene.pick(0)
	assert_true(scene._buttons[0].text.contains("[CHOSEN]"), "and can be changed")
	scene.pick(1)
	var cues_before: int = scene.engine.level.notes.size()
	assert_true(_until(scene, func() -> bool: return _title_is(scene, "Chalk on the Wall")))
	assert_true(scene.engine.level.notes.size() > cues_before, "cues were being charted all along")
	var saw_phrase_hidden := false
	var t := 0.0
	var free := 0
	while t < 40.0 and _title_is(scene, "Chalk on the Wall"):
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		t += 1.0 / 30.0
		if scene.engine.kind == "phrase" and not scene.engine.window_open:
			saw_phrase_hidden = saw_phrase_hidden or not scene._choice_layer.visible
		if scene.engine.window_open and scene._timer_label.text.begins_with("4 bar"):
			free += 1
		if free > 3:
			break
	assert_true(free > 0, "the window shows how many bars are left")
	_free_scene(d)


func test_nothing_chosen_means_the_default_and_the_dungeon_goes_on() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	assert_true(_until(scene, func() -> bool: return _title_is(scene, "The Crystal Stacks"), 160.0))
	assert_eq(d["exits"], [], "nothing sent the player back to the Warehouse")
	var titles: Array = []
	for e in scene.trace:
		if e["kind"] == "passage":
			titles.append(str(scene.tdata.passage(int(e["passage"]))["title"]))
	assert_eq(titles.slice(0, 6), ["The Service Hatch", "The Ladder Foot", "The Cable Run", "The Live Junction", "The Cable Nest", "The Crystal Stacks"], "by defaults alone")
	var defaulted: Array = scene.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "commit" and bool(e["defaulted"]))
	assert_true(defaulted.size() >= 4)
	_free_scene(d)


func test_a_death_returns_to_the_warehouse_after_its_window() -> void:
	var d := _scene_at("Fried", "perfect")
	var scene: Node = d["scene"]
	assert_true(scene._msg.text.contains("DIED"), "the death is shown: " + scene._msg.text)
	assert_eq(scene._buttons.size(), 1)
	assert_eq(scene._buttons[0].text.begins_with("Wake in the Warehouse"), true)
	assert_true(_until(scene, func() -> bool: return not (d["exits"] as Array).is_empty(), 60.0))
	assert_eq(d["exits"], ["warehouse"])
	var ex: Array = scene.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "exit")
	assert_eq(ex[0]["reason"], "death")
	_free_scene(d)


func test_the_victory_returns_to_the_warehouse_too() -> void:
	var d := _scene_at("Daylight", "perfect")
	var scene: Node = d["scene"]
	assert_true(scene._msg.text.contains("VICTORY"))
	assert_true(_until(scene, func() -> bool: return not (d["exits"] as Array).is_empty(), 60.0))
	var ex: Array = scene.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "exit")
	assert_eq(ex[0]["reason"], "victory")
	_free_scene(d)


func test_three_lost_phrases_in_a_fight_end_the_adventure_in_the_scene() -> void:
	var d := _scene_at("The Flooded Boiler Room", "no_fights")
	var scene: Node = d["scene"]
	var guard := 0
	while (d["exits"] as Array).is_empty() and guard < 8:
		guard += 1
		assert_true(_until(scene, func() -> bool: return scene.engine.window_open and scene._buttons.size() > 0 and scene._outcome.is_empty(), 60.0))
		if scene.engine.flow.passage == 0:
			break
		scene.pick(0)
	assert_true(_until(scene, func() -> bool: return not (d["exits"] as Array).is_empty(), 90.0), "after the third defeat the way back to the Warehouse")
	var lost: Array = scene.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "result" and bool(e.get("defeated", false)))
	assert_eq(lost.size(), 1, "the third defeat is the end")
	assert_eq(scene.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "exit")[0]["reason"], "death")
	assert_true(scene._news.text.contains("eel") or scene._desc.text.contains("Bassment"), "with the creature's defeat text or the defeat passage")
	_free_scene(d)


func test_the_fight_fails_then_is_retried_and_won_in_the_scene() -> void:
	var d := _scene_at("The Flooded Boiler Room", "perfect")
	var scene: Node = d["scene"]
	var win_window := func(title: String) -> bool: return scene.engine.window_open and _title_is(scene, title) and scene._buttons.size() > 0
	assert_true(_until(scene, func() -> bool: return win_window.call("The Flooded Boiler Room")))
	scene.bot = "no_fights"  # the player sits this one out
	scene.pick(0)  # the cable eel
	assert_true(_until(scene, func() -> bool: return scene._enemy.visible), "the eel is on screen for the fight")
	assert_true(scene._enemy.texture != null)
	assert_true(_until(scene, func() -> bool: return not scene._outcome.is_empty()), "an outcome animation plays")
	assert_true(_until(scene, func() -> bool: return win_window.call("The Flooded Boiler Room") and scene._outcome.is_empty()))
	assert_true(scene._buttons[0].text.begins_with("Try again"), "the retry is offered: " + scene._buttons[0].text)
	assert_true(scene._news.text.contains("arcs"), scene._news.text)
	assert_true(scene._buttons[0].text.contains("[DEFAULT]"), "and doing nothing retries it")
	scene.bot = "perfect"
	assert_true(_until(scene, func() -> bool: return _title_is(scene, "The Dry Landing")), "the retry is passed")
	var results: Array = []
	for e in scene.trace:
		if e["kind"] == "result":
			results.append(str(e["result"]))
	assert_eq(results, ["fail", "pass"], "the lost fight, the won retry")
	_free_scene(d)


func test_an_item_is_shown_in_the_footer_once_it_is_found() -> void:
	var d := _scene_at("The Brass Lamp", "perfect")
	var scene: Node = d["scene"]
	assert_eq(scene.engine.flow.flags, ["lamp"], "starting on the passage that grants it")
	assert_true(scene._tag.text.contains("carrying the brass lamp"), scene._tag.text)
	assert_true(scene._tag.text.begins_with("Lost Property"))
	_free_scene(d)


# --- the wizard in the Warehouse -----------------------------------------------------------------------------------------------------

func _run_scene(start: String) -> Dictionary:
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = start
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	return {"host": host, "scene": scene}


func test_the_wizard_offers_the_trial_in_the_warehouse_only() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	assert_true(scene._gate.visible, "the wizard is in the Warehouse")
	assert_eq(scene._gate_btn.text, "Enter the Trial")
	var launched: Array = []
	scene.trial_launcher = func() -> void: launched.append("trial")
	scene._gate_btn.pressed.emit()
	assert_eq(launched, ["trial"], "choosing the option leaves for the dungeon")
	var gate_rect := Rect2(scene._gate_btn.position, scene._gate_btn.size).merge(Rect2(scene._gate_wizard.position, scene._gate_wizard.size))
	var rects: Dictionary = scene.pad_view.button_rects()
	for p in rects:
		assert_false(gate_rect.intersects(rects[p] as Rect2), "the option does not sit on pad %d" % p)
	(d["host"] as Control).queue_free()
	var m := _run_scene("mothership")
	assert_false((m["scene"] as Node)._gate.visible, "no wizard outside the Warehouse")
	(m["host"] as Control).queue_free()
	Session.run_progress = saved
	DirAccess.remove_absolute("user://test_trial_save.json")
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


func test_ignoring_the_wizard_leaves_the_warehouse_the_ordinary_way() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save2.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	var launched: Array = []
	scene.trial_launcher = func() -> void: launched.append("trial")
	var beat := 60.0 / 174.0
	var t: float = scene._vt
	while t < 64.0 * beat + 0.3:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
	assert_eq(launched, [], "nothing took the player into the dungeon")
	assert_eq(scene.engine.node_id, "mothership", "the run went on by its default route")
	assert_false(scene._gate.visible, "and the wizard stayed behind in the Warehouse")
	(d["host"] as Control).queue_free()
	Session.run_progress = saved
	DirAccess.remove_absolute("user://test_trial_save2.json")
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")
