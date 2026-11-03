extends TestCase
## The Loadout screen's card model (pure functions of the library, the unlocks and the loadout) on the fixture library:
## which cards a row shows, what is locked, the unit icon strips, how a pick re-resolves the rest, and which loops a
## Listen button plays.

const SCREEN := "res://src/scenes/loadout.gd"


func _lo(idx: LibraryIndex, changes: Dictionary = {}) -> Dictionary:
	var d: Dictionary = idx.defaults.duplicate()
	for k in changes:
		d[k] = changes[k]
	return d


func _row(slot: String, current: Dictionary, unlocked: Array = [], locks: Dictionary = {}) -> Array:
	var screen: GDScript = load(SCREEN)
	return screen.row_items(TestCase.fixture_index(), unlocked, locks, slot, current)


func _ids(items: Array) -> Array:
	return items.map(func(i: Dictionary) -> String: return str(i["id"]))


func _by_id(items: Array, id: String) -> Dictionary:
	for i: Dictionary in items:
		if str(i["id"]) == id:
			return i
	return {}


func test_the_equipped_item_is_always_shown_and_lit() -> void:
	var idx := TestCase.fixture_index()
	for slot: String in Loadout.SLOTS:
		var cur := _lo(idx)
		var item := _by_id(_row(slot, cur), str(cur[slot]))
		assert_false(item.is_empty(), "%s shows its equipped item" % slot)
		assert_true(bool(item.get("equipped", false)), "%s equipped flag" % slot)
		assert_false(bool(item.get("locked", true)), "%s equipped is never locked (a default)" % slot)
	# even a pick that no longer fits the others (a stale loadout) is on the row, lit
	var stale := _lo(idx, {"groove": "groove_b", "kick_sound": "kick_b"})
	var kick := _row("kick_sound", stale)
	assert_eq(_ids(kick), ["kick_a", "kick_b"], "kick_a fits groove_b; kick_b is the equipped pick")
	assert_true(bool(_by_id(kick, "kick_b")["equipped"]))
	assert_false(bool(_by_id(kick, "kick_a")["equipped"]))


func test_incompatible_items_are_absent() -> void:
	var idx := TestCase.fixture_index()
	var all := idx.sounds.keys() + idx.clips.keys()
	# everything unlocked: still only what fits the other picks
	var cur := _lo(idx, {"groove": "groove_b"})
	assert_eq(_ids(_row("kick_sound", cur, all)), ["kick_a"], "groove_b plays kick_a only")
	assert_eq(_ids(_row("snare_sound", cur, all)), ["snare_a"])
	assert_eq(_ids(_row("bass_sound", _lo(idx), all)), ["bass_a", "bass_b"], "bass_line_1 is recorded with two sounds")
	assert_eq(_ids(_row("bass_sound", _lo(idx, {"bass": "bass_line_2", "bass_sound": "bass_c"}), all)), ["bass_c"])
	assert_eq(_ids(_row("backing", _lo(idx), all)), ["acc_a", "acc_b"], "the keyless backing and the C# minor one fit bass_line_1")
	assert_eq(_ids(_row("backing", _lo(idx, {"bass": "bass_line_2"}), all)), ["acc_a"], "acc_b is in C# minor, bass_line_2 in F minor")
	assert_eq(_ids(_row("groove", _lo(idx), all)), ["groove_a", "groove_b"])
	assert_eq(_ids(_row("bass", _lo(idx), all)), ["bass_line_1", "bass_line_2"])


func test_locked_items_are_shown_flagged_and_last() -> void:
	var idx := TestCase.fixture_index()
	var locks := {"groove_b": "Clear Mission 1 to unlock"}
	var row := _row("groove", _lo(idx), [], locks)
	assert_eq(_ids(row), ["groove_a", "groove_b"])
	var b := _by_id(row, "groove_b")
	assert_true(bool(b["locked"]))
	assert_eq(str(b["lock_text"]), "Clear Mission 1 to unlock")
	assert_false(bool(_by_id(row, "groove_a")["locked"]), "the default groove is always available")
	# unlocked: the same card is open, and no lock text
	var open := _by_id(_row("groove", _lo(idx), ["groove_b"], locks), "groove_b")
	assert_false(bool(open["locked"]))
	assert_eq(str(open["lock_text"]), "")
	# a locked item without lock text still says it is locked; unlocked ones come first whatever the library order
	var bass := _row("bass", _lo(idx), ["bass_line_2"])
	assert_false(bool(_by_id(bass, "bass_line_2")["locked"]))
	var sounds := _row("bass_sound", _lo(idx), ["bass_b"])
	assert_eq(_ids(sounds), ["bass_a", "bass_b"])
	var kicks := _row("kick_sound", _lo(idx), [])
	assert_eq(_ids(kicks), ["kick_a", "kick_b"])
	assert_eq(str(_by_id(kicks, "kick_b")["lock_text"]), "Locked")
	assert_eq(_ids(_row("snare_sound", _lo(idx), ["snare_b"])), ["snare_a", "snare_b"])


func test_the_fill_row_has_a_none_card() -> void:
	var idx := TestCase.fixture_index()
	var row := _row("fill", _lo(idx), ["fill_a"])
	assert_eq(_ids(row), ["", "fill_a"])
	assert_eq(str(row[0]["name"]), "None")
	assert_true(bool(row[0]["equipped"]), "no fill is the default")
	assert_false(bool(row[0]["locked"]))
	assert_false(bool(row[0]["listenable"]), "nothing to hear on the None card")
	assert_false(bool(row[1]["equipped"]))
	var with_fill := _row("fill", _lo(idx, {"fill": "fill_a"}), ["fill_a"])
	assert_true(bool(_by_id(with_fill, "fill_a")["equipped"]))
	assert_false(bool(_by_id(with_fill, "")["equipped"]))
	# a fill that plays only kick_a is not offered with kick_b equipped
	assert_eq(_ids(_row("fill", _lo(idx, {"kick_sound": "kick_b"}), ["fill_a"])), [""])


func test_icon_strips_match_the_reward_cycle() -> void:
	var idx := TestCase.fixture_index()
	for slot: String in ["kick_sound", "snare_sound", "bass_sound"]:
		var cur := _lo(idx)
		for item: Dictionary in _row(slot, cur, idx.sounds.keys()):
			var cycle := Loadout.reward_cycle(idx, str(item["id"]))
			assert_eq((item["icons"] as Array).size(), mini(cycle.size(), UiStyle.MAX_ICONS), "%s icon count" % item["id"])
	var kick := _by_id(_row("kick_sound", _lo(idx), ["kick_b"]), "kick_a")
	assert_eq(kick["icons"], [{"actor": "e1", "count": 3}, {"actor": "e1", "count": 3}, {"actor": "e2", "count": 3}], "2 rifle squads then a grenadier squad")
	assert_eq(str(kick["blurb"]), "rifles twice, then a grenadier")
	assert_eq(_by_id(_row("kick_sound", _lo(idx), ["kick_b"]), "kick_b")["icons"], [{"building": "pbox", "count": 1}])
	assert_eq(_by_id(_row("snare_sound", _lo(idx), ["snare_b"]), "snare_b")["icons"], [{"repair": true, "count": 1}], "a sound that builds nothing repairs")
	var bass := _row("bass_sound", _lo(idx), ["bass_b"])
	assert_eq(_by_id(bass, "bass_b")["icons"], [{"building": "gun", "count": 1}])
	assert_eq(_by_id(bass, "bass_a")["icons"], [{"actor": "e1", "count": 3}])
	assert_eq(_by_id(_row("bass_sound", _lo(idx, {"bass": "bass_line_2"}), ["bass_c"]), "bass_c")["icons"], [{"building": "ftur", "count": 1}])
	# at most six icons however long the cycle
	assert_true(UiStyle.reward_icons(idx, "kick_a", 2).size() == 2)
	# a mission without a war factory shows the bass vehicles as repairs
	assert_eq(UiStyle.without_vehicles([{"actor": "jeep", "count": 1}, {"actor": "e1", "count": 3}, {"building": "gun", "count": 1}]),
		[{"repair": true, "count": 1}, {"actor": "e1", "count": 3}, {"building": "gun", "count": 1}])
	# patterns carry no icons
	assert_eq(_by_id(_row("groove", _lo(idx)), "groove_a")["icons"], [])


func test_pattern_cards_show_key_and_cue_count() -> void:
	var idx := TestCase.fixture_index()
	var g := _by_id(_row("groove", _lo(idx)), "groove_a")
	assert_eq(str(g["meta"]), "32 cues / 8 bars", "16 kick and 16 snare cues")
	assert_eq(str(g["key"]), "")
	var b := _by_id(_row("bass", _lo(idx)), "bass_line_1")
	assert_eq(str(b["meta"]), "10 cues / 8 bars")
	assert_eq(str(b["key"]), "C# minor")
	assert_eq(str(_by_id(_row("backing", _lo(idx)), "acc_a")["meta"]), "8 bars", "a backing track has no cues")
	assert_eq(str(g["name"]), idx.name("groove_a"))


func test_a_pick_re_resolves_the_dependent_slots() -> void:
	var idx := TestCase.fixture_index()
	var screen: GDScript = load(SCREEN)
	var all := idx.sounds.keys() + idx.clips.keys()
	# kick_b fits groove_a only; moving to groove_b drops it back to kick_a
	var cur: Dictionary = screen.with_pick(idx, all, _lo(idx), "kick_sound", "kick_b")
	assert_eq(cur["kick_sound"], "kick_b")
	var moved: Dictionary = screen.with_pick(idx, all, cur, "groove", "groove_b")
	assert_eq(moved["groove"], "groove_b")
	assert_eq(moved["kick_sound"], "kick_a", "the sound slot falls back with the pattern")
	assert_true(Loadout.is_valid(idx, moved))
	# a locked pick is refused (the loadout stays valid and unchanged)
	var refused: Dictionary = screen.with_pick(idx, [], _lo(idx), "groove", "groove_b")
	assert_eq(refused["groove"], "groove_a")
	# a bass line change drops its sound and a backing in another key
	var bass: Dictionary = screen.with_pick(idx, all, _lo(idx, {"backing": "acc_b"}), "bass", "bass_line_2")
	assert_eq(bass["bass"], "bass_line_2")
	assert_eq(bass["bass_sound"], "bass_c")
	assert_eq(bass["backing"], "acc_a")
	assert_true(Loadout.is_valid(idx, bass))
	# choosing the fill "None" clears a fill
	var withfill: Dictionary = screen.with_pick(idx, all, _lo(idx), "fill", "fill_a")
	assert_eq(withfill["fill"], "fill_a")
	assert_eq((screen.with_pick(idx, all, withfill, "fill", "") as Dictionary)["fill"], "")


func test_listen_plays_the_loops_a_card_stands_for() -> void:
	var idx := TestCase.fixture_index()
	var screen: GDScript = load(SCREEN)
	var node: Control = screen.new()
	node._index = idx
	node._loadout = _lo(idx)
	var groove: Array = node.listen_paths("groove", "groove_b")
	assert_eq(groove.size(), 2, "a groove plays its kick and its snare together")
	assert_contains(groove[0], "groove_b__kick__kick_a")
	assert_contains(groove[1], "groove_b__snare__snare_a")
	var kick: Array = node.listen_paths("kick_sound", "kick_b")
	assert_eq(kick.size(), 1)
	assert_contains(kick[0], "groove_a__kick__kick_b")
	var bass: Array = node.listen_paths("bass_sound", "bass_b")
	assert_contains(bass[0], "bass_line_1__bass__bass_b")
	assert_contains((node.listen_paths("bass", "bass_line_2") as Array)[0], "bass_line_2__bass__bass_c", "a bass line plays with its first fitting sound")
	assert_contains((node.listen_paths("backing", "acc_a") as Array)[0], "acc_a__other__backing")
	assert_contains((node.listen_paths("backing", "acc_b") as Array)[0], "acc_b__other__backing")
	assert_eq((node.listen_paths("fill", "fill_a") as Array).size(), 2)
	node.free()
