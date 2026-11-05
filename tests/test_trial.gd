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
	var play := FileAccess.get_file_as_string("res://src/trial/trial_scene.gd").to_lower()
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
	assert_true(str(m["fight_audio"]) != "" and str(m["fight_chart"]) != "", "the music block names a fight pack (dd_part2, read and checked; the scene still plays one pack)")
	assert_true(d.errors.is_empty(), "the named fight packs exist")
	var bad := FileAccess.get_file_as_string(PATH).replace("\"fight_chart\": \"%s\"" % str(m["fight_chart"]), "\"fight_chart\": \"nowhere\"")
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


# --- the scene: the Bassment in 2.5D inside the run scene -----------------------------------------------------------------------------

## A run scene launched straight into the dungeon (RW_TRIAL_DIRECT), virtual clock, on a phone-shaped window.
func _trial_scene(bot: String) -> Dictionary:
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_TRIAL_DIRECT", "1")
	OS.set_environment("RW_TRIAL_BOT", bot)
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save3.json", "user://none.json")
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	OS.set_environment("RW_TRIAL_DIRECT", "")
	OS.set_environment("RW_TRIAL_BOT", "")
	return {"host": host, "scene": scene, "tr": scene.trial, "saved": saved}


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
	Session.run_progress = d["saved"]
	DirAccess.remove_absolute("user://test_trial_save3.json")
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_TRIAL_START", "")


func _scene_at(title: String, bot: String) -> Dictionary:
	OS.set_environment("RW_TRIAL_START", str(_id(_data(), title)))
	var d := _trial_scene(bot)
	OS.set_environment("RW_TRIAL_START", "")
	return d


func _title_is(tr: TrialScene, title: String) -> bool:
	return str(tr.engine.flow.current()["title"]) == title


func _left(scene: Node) -> Array:
	return scene.trial_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "left")


func test_the_scene_is_the_2d5_world_with_lit_exits_and_floating_labels() -> void:
	var d := _trial_scene("perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	scene._vt += 1.0 / 30.0
	scene._step_virtual(scene._vt)
	assert_eq(tr.zone, "hatch", "the first zone is shown at once in a direct launch")
	assert_true(tr.zone_stages["hatch"]["stage"].visible and tr.zone_stages["hatch"]["stage"].world_active, "a 2.5D stage")
	assert_eq(tr._buttons.size(), 2, "two floating choices")
	for b in tr._buttons:
		assert_true((b as Button).size.x >= 140.0 and (b as Button).size.y >= 40.0, "a big enough target on a phone")
	assert_true(tr._buttons[0].text.contains("[DEFAULT]"))
	assert_false(tr._buttons[1].text.contains("[DEFAULT]"))
	assert_eq(tr._exits.items.size(), 2, "both choices are lit as exits in the room")
	assert_true(tr._desc.text.length() > 40)
	assert_eq(tr._title.text, "THE SERVICE HATCH")
	assert_eq(tr._tag.text, "The Service Hatch")
	assert_true(tr._choice_layer.visible)
	tr.pick(1)
	assert_true(tr._buttons[1].text.contains("[CHOSEN]") and not tr._buttons[0].text.contains("[DEFAULT]"))
	tr.pick(0)
	assert_true(tr._buttons[0].text.contains("[CHOSEN]"))
	tr.pick(1)
	var cues_before: int = tr.engine.level.notes.size()
	assert_true(_until(scene, func() -> bool: return _title_is(tr, "Chalk on the Wall")))
	assert_true(tr.engine.level.notes.size() > cues_before, "cues were being charted all along")
	var free := 0
	var t := 0.0
	while t < 40.0 and _title_is(tr, "Chalk on the Wall"):
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		t += 1.0 / 30.0
		if tr.engine.window_open and tr._timer_label.text.begins_with("4 bar"):
			free += 1
		if free > 3:
			break
	assert_true(free > 0, "the window shows how many bars are left")
	_free_scene(d)


func test_the_phone_layout_keeps_choices_clear_of_the_pads() -> void:
	var d := _trial_scene("perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	var area_h: float = tr._area().size.y
	for b in tr._buttons:
		assert_true((b as Button).position.y + (b as Button).size.y <= area_h + 1.0, "the labels stay in the picture above the pads")
	var rects: Dictionary = scene.pad_view.button_rects()
	assert_true(rects.size() == 4)
	_free_scene(d)


func test_nothing_chosen_means_the_default_and_the_dungeon_goes_on_through_zones() -> void:
	var d := _trial_scene("perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	assert_true(_until(scene, func() -> bool: return _title_is(tr, "The Crystal Stacks"), 160.0))
	assert_eq(_left(scene), [], "nothing sent the player back to the Warehouse")
	var titles: Array = []
	for e in tr.trace:
		if e["kind"] == "passage":
			titles.append(str(tr.tdata.passage(int(e["passage"]))["title"]))
	assert_eq(titles.slice(0, 6), ["The Service Hatch", "The Ladder Foot", "The Cable Run", "The Live Junction", "The Cable Nest", "The Crystal Stacks"], "by defaults alone")
	assert_true(tr.zone_stages.has("cables") and tr.zone_stages.has("stacks"), "each zone got its own stage")
	assert_true(_until(scene, func() -> bool: return tr.zone == "stacks", 10.0), "the shown zone follows the passage, on the downbeat")
	var defaulted: Array = tr.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "commit" and bool(e["defaulted"]))
	assert_true(defaulted.size() >= 4)
	_free_scene(d)


func test_a_zone_swap_happens_on_a_downbeat_through_the_passage_frame() -> void:
	var d := _trial_scene("perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	var beat := 60.0 / 174.0
	assert_true(_until(scene, func() -> bool: return tr.swap_t >= 0.0, 120.0), "a swap is scheduled when the passage leaves the zone")
	var st: float = tr.swap_t
	var k := (st - tr.origin) / (16.0 * beat)
	assert_true(absf(k - roundf(k)) < 1.0e-6, "on a block's downbeat")
	var closed := false
	while scene._vt < st - 0.05:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		if scene._passage.aperture < 0.5:
			closed = true
	assert_true(closed, "the frame closed before the swap")
	assert_eq(tr.zone, "hatch", "still the old zone until the downbeat")
	assert_true(_until(scene, func() -> bool: return tr.zone != "hatch", 5.0))
	assert_eq(tr.zone, "cables")
	_free_scene(d)


func test_a_death_walks_back_to_the_warehouse_after_its_window() -> void:
	var d := _scene_at("Fried", "perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	assert_true(tr._msg.text.contains("DIED"), "the death is shown: " + tr._msg.text)
	assert_eq(tr._buttons.size(), 1)
	assert_eq(tr._buttons[0].text.contains("Wake in the Warehouse"), true)
	assert_true(_until(scene, func() -> bool: return not _left(scene).is_empty(), 60.0))
	assert_eq(_left(scene)[0]["reason"], "death")
	assert_eq(scene.trial_state, "")
	assert_eq(scene.engine.node_id, "warehouse", "the run resumed in the Warehouse")
	assert_false(tr.active)
	_free_scene(d)


func test_the_victory_walks_back_too() -> void:
	var d := _scene_at("Daylight", "perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	assert_true(tr._msg.text.contains("VICTORY"))
	assert_true(_until(scene, func() -> bool: return not _left(scene).is_empty(), 60.0))
	assert_eq(_left(scene)[0]["reason"], "victory")
	_free_scene(d)


func test_three_lost_phrases_in_a_fight_end_the_adventure_in_the_scene() -> void:
	var d := _scene_at("The Flooded Boiler Room", "no_fights")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	var guard := 0
	while _left(scene).is_empty() and guard < 8:
		guard += 1
		assert_true(_until(scene, func() -> bool: return tr.engine.window_open and tr._buttons.size() > 0 and tr._outcome.is_empty(), 60.0))
		if tr.engine.flow.passage == 0:
			break
		tr.pick(0)
	assert_true(_until(scene, func() -> bool: return not _left(scene).is_empty(), 90.0), "after the third defeat the way back to the Warehouse")
	var lost: Array = tr.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "result" and bool(e.get("defeated", false)))
	assert_eq(lost.size(), 1, "the third defeat is the end")
	assert_eq(tr.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "exit")[0]["reason"], "death")
	_free_scene(d)


func test_the_fight_puts_the_creature_in_the_room_fails_then_is_retried_and_won() -> void:
	var d := _scene_at("The Flooded Boiler Room", "perfect")
	var tr: TrialScene = d["tr"]
	var scene: Node = d["scene"]
	var win_window := func(title: String) -> bool: return tr.engine.window_open and _title_is(tr, title) and tr._buttons.size() > 0
	assert_true(_until(scene, func() -> bool: return win_window.call("The Flooded Boiler Room")))
	tr.bot = "no_fights"
	tr.pick(0)  # the cable eel
	assert_true(_until(scene, func() -> bool: return tr.figure_pose() != ""), "the eel is in the room for the fight")
	assert_eq(tr.figure_pose(), "idle")
	var spot: Vector2 = tr._fig["pos"]
	assert_true(tr._map("boiler").sector_at(spot) != "", "standing on the floor of the zone")
	var seen := {"attack": false, "struck": false}
	assert_true(_until(scene, func() -> bool:
		seen["attack"] = seen["attack"] or tr.figure_pose() == "attack"
		return not tr._outcome.is_empty()), "an outcome animation plays")
	assert_true(_until(scene, func() -> bool:
		seen["attack"] = seen["attack"] or tr.figure_pose() == "attack"
		return win_window.call("The Flooded Boiler Room") and tr._outcome.is_empty()))
	assert_true(seen["attack"], "the creature lunges when the phrase is lost")
	assert_true(tr._buttons[0].text.contains("Try again"), "the retry is offered: " + tr._buttons[0].text)
	assert_true(tr._news.text.contains("arcs"), tr._news.text)
	tr.bot = "perfect"
	assert_true(_until(scene, func() -> bool:
		seen["struck"] = seen["struck"] or tr.figure_pose() == "struck"
		return _title_is(tr, "The Dry Landing")), "the retry is passed")
	assert_true(seen["struck"], "the won fight shows the struck pose")
	var results: Array = []
	for e in tr.trace:
		if e["kind"] == "result":
			results.append(str(e["result"]))
	assert_eq(results, ["fail", "pass"], "the lost fight, the won retry")
	_free_scene(d)


func test_an_item_is_shown_in_the_footer_once_it_is_found() -> void:
	var d := _scene_at("The Brass Lamp", "perfect")
	var tr: TrialScene = d["tr"]
	assert_eq(tr.engine.flow.flags, ["lamp"])
	assert_true(tr._tag.text.contains("carrying the brass lamp"), tr._tag.text)
	assert_true(tr._tag.text.begins_with("Lost Property"))
	_free_scene(d)


func test_every_passage_stands_in_a_reachable_place_of_its_zone_map() -> void:
	var d := _data()
	assert_true(d.errors.is_empty(), str(d.errors))
	for n in d.passages:
		var p: Dictionary = d.passages[n]
		var m := TrialData.map_of(str(p["map"]))
		var w: Dictionary = m.waypoint(str(p["waypoint"]))
		assert_false(w.is_empty(), "passage %d waypoint" % n)
		var from: Dictionary = m.waypoint(m.start_id)
		var r := m.route(from["at"], str(from["sector"]), w["at"], str(w["sector"]))
		assert_true((r["points"] as PackedVector2Array).size() >= 2, "passage %d is reachable from its zone's entrance" % n)
		for c in p["choices"]:
			var x: Dictionary = m.waypoint(str(c["exit_wp"]))
			var r2 := m.route(w["at"], str(w["sector"]), x["at"], str(x["sector"]))
			assert_true((r2["points"] as PackedVector2Array).size() >= 2, "passage %d: the exit '%s' can be walked to" % [n, c["exit_wp"]])
			assert_true((x["at"] as Vector2).distance_to(w["at"]) > 0.5, "passage %d: the exit is somewhere else in the room" % n)
	for zid in d.zones:
		var m2 := TrialData.map_of(d.zone_map(zid))
		assert_true(m2.sectors.size() >= 2 and m2.sectors.size() <= 4, "%s has 2 to 4 sectors" % zid)
		assert_true(str(m2.art) == "bassment")
		assert_true(m2.lights.size() >= 2, "%s is lit by placed lights" % zid)


func test_the_data_refuses_a_missing_waypoint_or_exit() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	raw["passages"]["1"]["waypoint"] = "nowhere"
	raw["passages"]["3"]["choices"][0]["exit_wp"] = "nowhere"
	var f := FileAccess.open("user://bad_trial.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(raw))
	f.close()
	var d := TrialData.load_file("user://bad_trial.json")
	var text := " ".join(PackedStringArray(d.errors))
	assert_true(text.contains("passage 1: waypoint 'nowhere'"), text)
	assert_true(text.contains("passage 3") and text.contains("exit_wp 'nowhere'"), text)
	DirAccess.remove_absolute("user://bad_trial.json")


# --- the wizard in the Warehouse and the seamless entry -----------------------------------------------------------------------------

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


func _end_run(d: Dictionary, saved: RunProgress, path: String) -> void:
	(d["host"] as Control).queue_free()
	Session.run_progress = saved
	DirAccess.remove_absolute(path)
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


func _step_to(scene: Node, t_end: float) -> void:
	while scene._vt < t_end:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)


func test_the_wizard_offers_the_trial_in_the_warehouse_only() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	assert_true(scene._gate.visible, "the wizard is in the Warehouse")
	assert_true(scene._gate_btn == null, "and carries no written option: he is a character hotspot")
	var launched: Array = []
	scene.trial_launcher = func() -> void: launched.append("trial")
	var beat := 60.0 / 174.0
	_step_to(scene, 3.0 * beat)
	assert_true(scene._gate_wizard.visible, "his picture stands in the room while his window is open")
	var rects: Dictionary = scene.pad_view.button_rects()
	for p in rects:
		assert_false(Rect2(scene._gate_wizard.position, scene._gate_wizard.size).intersects(rects[p] as Rect2), "the wizard does not sit on pad %d" % p)
	assert_true(scene.hotspot_select("warehouse.floor.wizard"), "touching him selects him")
	assert_eq(launched, [], "a selection alone leaves the run as it was: the performance decides")
	_step_to(scene, 13.5 * beat)
	assert_eq(launched, ["trial"], "the block he waited for was passed: the dungeon is asked for")
	_end_run(d, saved, "user://test_trial_save.json")
	var m := _run_scene("mothership")
	assert_false((m["scene"] as Node)._gate.visible, "no wizard outside the Warehouse")
	(m["host"] as Control).queue_free()
	Session.run_progress = saved
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


func test_ignoring_the_wizard_leaves_the_warehouse_the_ordinary_way() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save2.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	_step_to(scene, 64.0 * 60.0 / 174.0 + 0.3)
	assert_eq(scene.trial_state, "", "nothing took the player into the dungeon")
	assert_eq(scene.engine.node_id, "warehouse.bar", "the run went on by its default route: the bar")
	assert_false(scene._gate.visible, "and the wizard stayed behind in the Warehouse")
	_end_run(d, saved, "user://test_trial_save2.json")


func test_entering_the_trial_is_a_seamless_walk_through_the_hatch() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save4.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	var beat := 60.0 / 174.0
	_step_to(scene, 3.0 * beat)
	var notes_before: int = scene.engine.level.notes.size()
	assert_true(scene.arm_trial(), "chosen early in the phase")
	assert_eq(scene.trial_state, "armed")
	var log: Dictionary = (scene.trial_log as Array)[0]
	assert_true(absf(float(log["g1"]) - (12.75 * beat)) < 1.0e-6, "the walk to the hatch starts on the next cue-free guard")
	assert_true(absf(float(log["entry"]) - 32.0 * beat) < 1.0e-6, "the dungeon is entered on a downbeat two blocks on")
	_step_to(scene, float(log["g1"]) + 0.2)
	var moves: Array = scene.journey_log.filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and a["args"].get("to", "") == "hatch")
	assert_eq(moves.size(), 1, "the camera is sent to the hatch")
	var wh_stage: StoryStage = scene.stages["night_one"]["stage"]
	assert_true(wh_stage.map.has_waypoint("hatch"))
	_step_to(scene, float(log["g2"]) + 0.1)
	assert_eq(scene.trial_state, "in", "the dungeon owns the pads from the guard before the downbeat")
	assert_true(scene.trial.engine.level != scene.engine.level)
	assert_eq(scene.trial.zone, "", "the hatch is not shown yet")
	var audio_ok := true
	_step_to(scene, float(log["entry"]) - 0.02)
	assert_true(wh_stage.visible, "the Warehouse is still on screen until the downbeat")
	assert_true(scene._passage.aperture < 0.5, "the frame is closed on the hatch")
	_step_to(scene, float(log["entry"]) + 0.05)
	assert_eq(scene.trial.zone, "hatch", "the Service Hatch opens on the downbeat")
	assert_false(wh_stage.visible)
	assert_true(scene.trial.engine.origin == float(log["entry"]), "the dungeon's beat grid starts on that downbeat")
	var first_cue: float = 1.0e9
	for n in scene.trial.engine.level.notes:
		first_cue = minf(first_cue, float(n["time"]))
	var k := (first_cue - float(log["entry"])) / beat
	assert_true(k >= -1.0e-6 and absf(k - roundf(k * 4.0) / 4.0) < 1.0e-3, "the first dungeon cue sits on the run's grid")
	assert_eq(scene.clock.state, SongClock.State.PAUSED, "(virtual clock) never restarted")
	assert_true(audio_ok)
	assert_true(scene.engine.level.notes.size() >= notes_before)
	_end_run(d, saved, "user://test_trial_save4.json")


func test_leaving_the_dungeon_resumes_the_run_on_the_same_grid_with_energy_kept() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save5.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	var beat := 60.0 / 174.0
	_step_to(scene, 3.0 * beat)
	scene.arm_trial()
	var entry: float = float(scene.trial_log[0]["entry"])
	_step_to(scene, entry + 0.2)
	var energy_before: float = scene.engine.energy
	var tr: TrialScene = scene.trial
	tr.request_leave()  # the system back key
	assert_true(_until(scene, func() -> bool: return not _left(scene).is_empty(), 60.0))
	var t_left: float = float(_left(scene)[0]["t"])
	var k := (t_left - entry) / (16.0 * beat)
	assert_true(absf(k - roundf(k)) < 1.0e-6, "the way back lands on a downbeat of the same grid")
	assert_eq(_left(scene)[0]["reason"], "normal")
	assert_eq(scene.trial_state, "")
	assert_eq(scene.engine.node_id, "warehouse")
	assert_true(absf(scene.engine.phase_t0 - t_left) < 1.0e-6, "a fresh phase begins on that downbeat")
	assert_true(absf(scene.engine.energy - energy_before) < 1.0e-6, "the crowd's energy is kept")
	assert_true(scene.engine.level.notes.size() > 0 and float(scene.engine.level.notes[0]["time"]) >= t_left - 1.0e-6, "its first cues are after the return")
	var stage: StoryStage = scene.stages["night_one"]["stage"]
	assert_true(stage.visible, "the Warehouse is back on screen")
	assert_true(_until(scene, func() -> bool: return scene.engine.phase_beat_at(scene._vt) > 20.0, 20.0))
	assert_eq(scene.trial_state, "", "and the run goes on")
	_end_run(d, saved, "user://test_trial_save5.json")
