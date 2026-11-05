extends TestCase
## The blackjack table view's testable parts (headless, so layout, hit-testing and the money it would draw, not pixels): touch targets in every phase, the visible money against the wallet,
## the pile's room on the canvas, and the rule that nothing under src/minigames draws or makes text.

const BEAT := 60.0 / 174.0
const CONFIG_PATH := "res://content/minigames/blackjack.json"
const SIZES := [Vector2(640, 230), Vector2(780, 231), Vector2(320, 115), Vector2(914, 360)]
const SCREENS := [Vector2(844, 250), Vector2(1280, 461)]
const FORBIDDEN := ["draw_string", "Label.new", "Button.new", "RichTextLabel", "tooltip_text", "FontFile", "SystemFont", "FontVariation", ".ttf", ".otf", ".woff"]


# helpers

func _cards(ranks: Array) -> Array:
	var out: Array = []
	for i in ranks.size():
		out.append({"rank": int(ranks[i]), "suit": i % 4})
	return out


## An exact deal: npc_a, player, npc_b, dealer ([up, hole]); then `extra` draws in order.
func _deal(player: Array, dealer: Array, extra: Array = []) -> Array:
	var order: Array = [10, player[0], 10, dealer[0], 7, player[1], 7, dealer[1]]
	order.append_array(extra)
	return _cards(order)


func _rig(size: Vector2, seed: int = 7, pence: int = 2000, cards: Array = [], begin := true) -> Dictionary:
	var w := RunWallet.new()
	if pence < 2000:
		w.spend(2000 - pence)
	elif pence > 2000:
		w.add(pence - 2000)
	var a := BlackjackActivity.new()
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	var ctx := {"wallet": w, "seed": seed, "beat_s": BEAT, "config": cfg}
	if not cards.is_empty():
		ctx["deck"] = BlackjackDeck.stacked(cards, 99)
	a.setup(ctx)
	var clock := {"t": 0.0}
	var v := BlackjackView.new()
	v.size = size
	v.beat_s = BEAT
	v.screen_size = SCREENS[0]
	v.now_fn = func() -> float: return clock["t"]
	v.state_fn = func() -> Dictionary: return a.state()
	if begin:
		a.begin(0.0)
	return {"a": a, "w": w, "v": v, "clock": clock, "size": size, "bets": 1, "twists": 0}


func _free(rig: Dictionary) -> void:
	(rig["v"] as BlackjackView).free()


func _t(rig: Dictionary) -> float:
	return float(rig["clock"]["t"])


func _upd(rig: Dictionary, t: float) -> void:
	rig["clock"]["t"] = t
	(rig["a"] as BlackjackActivity).update(t)


func _st(rig: Dictionary) -> Dictionary:
	return (rig["a"] as BlackjackActivity).state()


## Taps like a finger: the centre of the target's rectangle, through the view's own hit test.
func _tap(rig: Dictionary, id: String) -> bool:
	var v: BlackjackView = rig["v"]
	var rects := v.target_rects()
	if not rects.has(id):
		return false
	var sz: Vector2 = rig["size"]
	var c: Vector2 = (rects[id] as Rect2).get_center()
	var hit := v.hit(Vector2(c.x * v.screen_size.x / sz.x, c.y * v.screen_size.y / sz.y))
	return hit == id and (rig["a"] as BlackjackActivity).tap(hit, _t(rig))


## The bot of these tests: bets while it has bets, twists `twists` times then sticks, and gets up when it has no more bets.
func _policy(rig: Dictionary) -> void:
	var tg: Array = _st(rig)["targets"]
	if "bet" in tg:
		if int(rig["bets"]) > 0:
			rig["bets"] = int(rig["bets"]) - 1
			_tap(rig, "bet")
		else:
			_tap(rig, "exit")
	elif "deck" in tg and "hand" in tg:
		if int(rig["twists"]) > 0:
			rig["twists"] = int(rig["twists"]) - 1
			_tap(rig, "deck")
		else:
			_tap(rig, "hand")
	elif tg == ["exit"] and str(_st(rig)["phase"]) == "broke":
		_tap(rig, "exit")


## Runs the bot until the activity is done (at most `max_s` seconds), calling `check` after every step.
func _run(rig: Dictionary, check: Callable, dt := 0.07, max_s := 240.0) -> void:
	var a: BlackjackActivity = rig["a"]
	while not a.is_done() and _t(rig) < max_s:
		_upd(rig, _t(rig) + dt)
		check.call(rig)
		_policy(rig)


func _sum(items: Array) -> int:
	var s := 0
	for d in items:
		s += int(d)
	return s


func _counts(items: Array) -> Dictionary:
	var c := {}
	for d in items:
		c[int(d)] = int(c.get(int(d), 0)) + 1
	return c


# empty snapshot

func test_nothing_is_live_before_the_player_sits() -> void:
	for size: Vector2 in SIZES:
		var rig := _rig(size, 7, 2000, [], false)
		var v: BlackjackView = rig["v"]
		assert_eq(str(_st(rig)["phase"]), "")
		assert_eq(v.target_rects().size(), 0)
		for sc: Vector2 in SCREENS:
			v.screen_size = sc
			for fx in [0.02, 0.2, 0.4, 0.5, 0.6, 0.8, 0.98]:
				for fy in [0.02, 0.2, 0.5, 0.8, 0.98]:
					assert_eq(v.hit(Vector2(sc.x * fx, sc.y * fy)), "")
		assert_eq(v.shown_pile(0.0).size(), 0)
		assert_eq(v.shown_bet(0.0).size(), 0)
		_free(rig)
	var empty := BlackjackView.new()
	empty.size = SIZES[0]
	empty.state_fn = func() -> Dictionary: return {}
	assert_eq(empty.hit(Vector2(400, 100)), "")
	assert_eq(empty.target_rects().size(), 0)
	empty.free()
	var bare := BlackjackView.new()  # no callables at all
	bare.size = SIZES[0]
	assert_eq(bare.hit(Vector2(400, 100)), "")
	assert_eq(bare.target_rects().size(), 0)
	bare.free()


# touch targets

func _check_layout(rig: Dictionary, seen: Dictionary) -> void:
	var v: BlackjackView = rig["v"]
	var sz: Vector2 = rig["size"]
	var snap := _st(rig)
	var tg: Array = snap["targets"]
	var rects := v.target_rects()
	var phase := str(snap["phase"])
	seen[phase] = true
	var ids := rects.keys()
	ids.sort()
	var want := tg.duplicate()
	want.sort()
	assert_eq(ids, want, "live ids in " + phase)
	var canvas := Rect2(Vector2.ZERO, sz)
	for id: String in rects:
		var r: Rect2 = rects[id]
		assert_true(canvas.encloses(r), "%s inside the canvas in %s at %s: %s" % [id, phase, str(sz), str(r)])
		for sc: Vector2 in SCREENS:
			assert_true(r.size.x * sc.x / sz.x >= 72.0 - 0.01 and r.size.y * sc.y / sz.y >= 72.0 - 0.01, "%s is 72 px on %s (%s)" % [id, str(sc), str(r.size)])
		for other: String in rects:
			if other < id:
				assert_false(r.intersects(rects[other]), "%s and %s overlap in %s" % [id, other, phase])
		for sc: Vector2 in SCREENS:
			v.screen_size = sc
			var c := r.get_center()
			assert_eq(v.hit(Vector2(c.x * sc.x / sz.x, c.y * sc.y / sz.y)), id, "tap on the centre of " + id)
		v.screen_size = SCREENS[0]
	# a tap outside every rectangle, and the kit's rectangle of a target that is not live
	var out := Vector2(3.0, 3.0)
	var inside_any := false
	for id: String in rects:
		inside_any = inside_any or (rects[id] as Rect2).has_point(out)
	assert_false(inside_any)
	assert_eq(v.hit(Vector2(out.x * v.screen_size.x / sz.x, out.y * v.screen_size.y / sz.y)), "")
	for id in BlackjackDraw.TARGETS:
		if not (id in tg):
			var c := BlackjackDraw.target_rect(id, sz, 2).get_center()
			assert_true(v.hit(Vector2(c.x * v.screen_size.x / sz.x, c.y * v.screen_size.y / sz.y)) != id, "%s is not live in %s" % [id, phase])


func test_targets_follow_the_snapshot_through_every_phase_and_size() -> void:
	var seen := {}
	for size: Vector2 in SIZES:
		var rig := _rig(size, 7)
		rig["bets"] = 2
		rig["twists"] = 1
		_run(rig, func(r: Dictionary) -> void: _check_layout(r, seen), 0.11)
		assert_true((rig["a"] as BlackjackActivity).is_done())
		_free(rig)
	for p in ["sitting", "await_bet", "dealing", "player_turn", "others", "settling", "leaving"]:
		assert_true(seen.has(p), "phase %s was visited" % p)
	# broke and falling too
	var broke := _rig(SIZES[0], 7, 400)
	_run(broke, func(r: Dictionary) -> void: _check_layout(r, seen), 0.11, 30.0)
	assert_true(seen.has("broke"))
	_free(broke)
	var fall := _rig(SIZES[2], 7)
	_upd(fall, 6.0 * BEAT)
	_upd(fall, 8.0 * BEAT)
	(fall["a"] as BlackjackActivity).interrupt("fall", 8.0 * BEAT)
	for i in 30:
		_upd(fall, 8.0 * BEAT + i * 0.1)
		_check_layout(fall, seen)
	assert_true(seen.has("falling"))
	assert_eq((fall["v"] as BlackjackView).target_rects().size(), 0)
	_free(fall)


func test_the_deck_target_is_only_live_when_the_snapshot_says_so() -> void:
	var rig := _rig(SIZES[0])
	_upd(rig, 5.0 * BEAT)
	var v: BlackjackView = rig["v"]
	var c := BlackjackDraw.deck_spot(SIZES[0])
	var s: Vector2 = v.screen_size
	assert_eq(v.hit(Vector2(c.x * s.x / 640.0, c.y * s.y / 230.0)), "")
	var guard := 0
	while str(_st(rig)["phase"]) != "await_bet" and guard < 400:
		_upd(rig, _t(rig) + 0.05)
		guard += 1
	assert_eq(str(_st(rig)["phase"]), "await_bet")
	assert_false(v.target_rects().has("deck"))
	assert_eq(v.hit(Vector2(c.x * s.x / 640.0, c.y * s.y / 230.0)), "")
	_free(rig)


func test_the_picture_wobbles_and_hit_follows_it() -> void:
	var rig := _rig(SIZES[0])
	var a: BlackjackActivity = rig["a"]
	var v: BlackjackView = rig["v"]
	_upd(rig, 5.0 * BEAT)
	var guard := 0
	while str(_st(rig)["phase"]) != "await_bet" and guard < 400:
		_upd(rig, _t(rig) + 0.05)
		guard += 1
	var c := v.target_rects()["bet"].get_center() as Vector2
	var s := v.screen_size
	var pos := Vector2(c.x * s.x / 640.0, c.y * s.y / 230.0)
	assert_eq(v.hit(pos), "bet")
	a.set_wobble(1, _t(rig))
	for k in [0.0, 0.5, 1.0, 2.0, 3.5]:
		_upd(rig, _t(rig) + k * BEAT)
		assert_eq(v.hit(pos), "bet", "a rocking picture still takes the touch (a few degrees)")
	_free(rig)


# the money on show

func _money_check(rig: Dictionary, log: Dictionary) -> void:
	var v: BlackjackView = rig["v"]
	var w: RunWallet = rig["w"]
	var snap := _st(rig)
	var now := _t(rig)
	var pile: Dictionary = snap["pile"]
	var bet: Dictionary = snap["bet"]
	var phase := str(snap["phase"])
	var sp := v.shown_pile(now)
	var sb := v.shown_bet(now)
	for pair in [[pile, sp, "pile"], [bet, sb, "bet"]]:
		var m: Dictionary = pair[0]
		var shown: Array = pair[1]
		var to := int(m["pence"])
		var from := int(m["from_pence"])
		var dur := float(m["dur"])
		var done := dur <= 0.0 or now >= float(m["t0"]) + dur or from == to
		if done:
			assert_eq(_sum(shown), to, "%s at rest at %f in %s" % [pair[2], now, phase])
			assert_eq(_counts(shown), _counts(MoneyBreakdown.breakdown(to)))
		else:
			log["moving"] = int(log.get("moving", 0)) + 1
			assert_true(_sum(shown) <= maxi(from, to), "%s never more than the larger of the two piles (%d from %d to %d)" % [pair[2], _sum(shown), from, to])
			var a := _counts(MoneyBreakdown.breakdown(from))
			var b := _counts(MoneyBreakdown.breakdown(to))
			for d in _counts(shown):
				assert_true(int(_counts(shown)[d]) <= maxi(int(a.get(d, 0)), int(b.get(d, 0))), "%s shows only items of the old or the new pile (%d)" % [pair[2], d])
	if phase != "leaving":
		assert_eq(int(pile["pence"]), w.balance_pence())
	assert_eq(int(bet["pence"]), w.held_pence())
	# the three phases whose motion is specified
	if phase == "sitting":
		var s := _sum(sp)
		assert_true(s >= int(log.get("sit", 0)), "the pile only grows while sitting")
		log["sit"] = s
	elif phase == "leaving":
		var s := _sum(sp)
		assert_true(s <= int(log.get("leave", 1 << 30)), "the pile only empties while leaving")
		log["leave"] = s
		assert_eq(w.balance_pence(), int(log.get("leave_balance", w.balance_pence())), "the wallet does not change while leaving")
		log["leave_balance"] = w.balance_pence()


func _money_run(cards: Array, twists: int, seed: int, pence := 2000, bets := 1) -> Dictionary:
	var rig := _rig(SIZES[0], seed, pence, cards)
	rig["bets"] = bets
	rig["twists"] = twists
	var log := {}
	_run(rig, func(r: Dictionary) -> void: _money_check(r, log), 0.05)
	log["balance"] = (rig["w"] as RunWallet).balance_pence()
	log["done"] = (rig["a"] as BlackjackActivity).is_done()
	_free(rig)
	return log


func test_the_visible_money_is_the_wallet_in_every_kind_of_hand() -> void:
	var win := _money_run(_deal([10, 10], [10, 7]), 0, 1)
	assert_eq(int(win["balance"]), 2500)
	assert_true(bool(win["done"]))
	assert_true(int(win.get("moving", 0)) > 10, "money was seen moving")
	assert_eq(int(win.get("sit", 0)), 2000, "the pile grew to the balance while sitting")
	assert_eq(int(win.get("leave", -1)), 0, "and emptied while leaving")
	var lose := _money_run(_deal([10, 7], [10, 10]), 0, 1)
	assert_eq(int(lose["balance"]), 1500)
	var push := _money_run(_deal([10, 8], [10, 8]), 0, 1)
	assert_eq(int(push["balance"]), 2000)
	var natural := _money_run(_deal([1, 13], [10, 7]), 0, 1)
	assert_eq(int(natural["balance"]), 2000 + 750)
	var bust := _money_run(_deal([10, 6], [10, 7], [10]), 1, 1)
	assert_eq(int(bust["balance"]), 1500)
	var two := _money_run(_deal([10, 10], [10, 7]), 0, 1, 2000, 2)
	assert_true(bool(two["done"]))
	var seeded := _money_run([], 1, 5, 2000, 3)
	assert_true(bool(seeded["done"]))


func test_the_bet_target_holds_the_top_fiver() -> void:
	for size: Vector2 in SIZES:
		for pence in [500, 750, 2000, 2500, 3500, 4000, 6000, 10000]:
			var rig := _rig(size, 7, pence)
			_upd(rig, 3.9 * BEAT)
			var guard := 0
			while str(_st(rig)["phase"]) != "await_bet" and guard < 400:
				_upd(rig, _t(rig) + 0.05)
				guard += 1
			var v: BlackjackView = rig["v"]
			var rects := v.target_rects()
			assert_true(rects.has("bet"), "bet is live for %d" % pence)
			var pg := BlackjackView.pile_geometry(size)
			var note := MoneyDraw.top_note_rect(pence, pg["origin"], pg["scale"])
			assert_true(note.size.x > 0.0)
			assert_true((rects["bet"] as Rect2).encloses(note), "the bet rect %s holds the top note %s (%d at %s)" % [str(rects["bet"]), str(note), pence, str(size)])
			assert_true(Rect2(Vector2.ZERO, size).encloses(note))
			_free(rig)


func test_the_pile_fits_the_canvas_and_stays_clear_of_what_the_player_touches() -> void:
	for size: Vector2 in SIZES:
		var pg := BlackjackView.pile_geometry(size)
		var u := BlackjackDraw.unit(size)
		var canvas := Rect2(Vector2.ZERO, size)
		var hand := BlackjackDraw.target_rect("hand", size, 2)
		for n in range(2, 8):
			hand = hand.merge(BlackjackDraw.target_rect("hand", size, n))
		var bet_spot := BlackjackDraw.bet_spot(size)
		var bet_item := Rect2(bet_spot - MoneyDraw.item_size(500, float(pg["scale"])) * 0.5, MoneyDraw.item_size(500, float(pg["scale"])))
		var deck := BlackjackDraw.target_rect("deck", size)
		for pence in range(500, 10001, 250):
			var b := MoneyDraw.pile_bounds(pence, pg["origin"], pg["scale"])
			assert_true(canvas.encloses(b), "pile %d inside the canvas %s: %s" % [pence, str(size), str(b)])
			assert_false(b.intersects(hand), "pile %d clear of the player's cards at %s" % [pence, str(size)])
			assert_false(b.intersects(bet_item), "pile %d clear of the bet spot at %s" % [pence, str(size)])
			assert_false(b.intersects(deck), "pile %d clear of the deck" % pence)
			assert_false(b.intersects(BlackjackDraw.exit_rect(size)))


# structure

func test_make_view_gives_a_blackjack_view() -> void:
	var v := BlackjackActivity.new().make_view()
	assert_true(v is BlackjackView)
	v.free()


func test_there_is_no_text_anywhere_under_src_minigames() -> void:
	var files := _gd_files("res://src/minigames")
	assert_true(files.size() >= 8, "found the minigame sources")
	for path in files:
		var text := FileAccess.get_file_as_string(path)
		for bad in FORBIDDEN:
			assert_false(text.contains(bad), "%s contains %s" % [path, bad])


func _gd_files(dir: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".gd"):
			out.append(dir.path_join(f))
	for sub in d.get_directories():
		out.append_array(_gd_files(dir.path_join(sub)))
	return out
