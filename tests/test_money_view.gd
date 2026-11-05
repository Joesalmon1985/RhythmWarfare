extends TestCase
## The pixel glyph font and the money drawing kit's pure parts: layout, bounds, touch target and the transition data.

const U_SIZES: Array[float] = [0.5, 1.0, 1.5]


func _sum(items: Array) -> int:
	var t := 0
	for it in items:
		t += int(it["denomination"])
	return t


func _amounts() -> Array:
	var out: Array = []
	var p := 0
	while p <= 5000:
		out.append(p)
		p += 50
	for extra in [1, 7, 99, 337, 2750, 4999, 7777, 12345, 20000, 40050]:
		out.append(extra)
	return out


func _count(items: Array) -> Dictionary:
	var c := {}
	for it in items:
		var d: int = it["denomination"] if it is Dictionary else int(it)
		c[d] = int(c.get(d, 0)) + 1
	return c


func test_glyph_widths() -> void:
	assert_eq(PixelGlyphs.text_width("", 1.0), 0.0)
	assert_eq(PixelGlyphs.text_width("5", 1.0), 3.0)
	assert_eq(PixelGlyphs.text_width("10", 1.0), 7.0)
	assert_eq(PixelGlyphs.text_width("£20", 1.0), 11.0)
	assert_eq(PixelGlyphs.text_width("10", 2.0), 14.0)
	assert_eq(PixelGlyphs.text_width("5?", 1.0), 3.0, "unknown characters are skipped")
	assert_eq(PixelGlyphs.text_height(1.0), 5.0)
	assert_eq(PixelGlyphs.text_height(3.0), 15.0)
	for ch in "0123456789AJQK£p":
		assert_true(PixelGlyphs.ROWS.has(ch), ch)
		assert_eq((PixelGlyphs.ROWS[ch] as Array).size(), 5, ch)


func test_pile_matches_amount() -> void:
	for p in _amounts():
		var items := MoneyDraw.pile_layout(p, Vector2(10, 10), 1.0)
		assert_eq(_sum(items), p, "sum at %d" % p)
		var parts := MoneyBreakdown.breakdown(p)
		assert_eq(items.size(), parts.size())
		for i in items.size():
			assert_eq(items[i]["denomination"], parts[i], "denomination %d at %d" % [i, p])


func test_layout_deterministic() -> void:
	for p in [0, 500, 2750, 4000, 12345]:
		assert_eq(MoneyDraw.pile_layout(p, Vector2(30, 40), 1.3), MoneyDraw.pile_layout(p, Vector2(30, 40), 1.3))


func test_items_inside_bounds() -> void:
	for u in U_SIZES:
		for p in _amounts():
			var o := Vector2(100, 120)
			var b := MoneyDraw.pile_bounds(p, o, u)
			for it in MoneyDraw.pile_layout(p, o, u):
				var sz := MoneyDraw.item_size(it["denomination"], u)
				var r := Rect2(it["pos"] - sz * 0.5, sz)
				assert_true(b.encloses(r), "item %d inside bounds at %d u=%f" % [it["denomination"], p, u])


func test_items_do_not_overlap_other_denominations_badly() -> void:
	# coins of different denominations and notes never share space (same-denomination stacks may overlap)
	for p in [2750, 499, 3599, 1999, 4000]:
		var items := MoneyDraw.pile_layout(p, Vector2.ZERO, 1.0)
		for i in items.size():
			for j in range(i + 1, items.size()):
				if items[i]["denomination"] == items[j]["denomination"]:
					continue
				var a := Rect2(items[i]["pos"] - MoneyDraw.item_size(items[i]["denomination"], 1.0) * 0.5, MoneyDraw.item_size(items[i]["denomination"], 1.0))
				var b := Rect2(items[j]["pos"] - MoneyDraw.item_size(items[j]["denomination"], 1.0) * 0.5, MoneyDraw.item_size(items[j]["denomination"], 1.0))
				assert_false(a.intersects(b), "%d and %d overlap at %d" % [items[i]["denomination"], items[j]["denomination"], p])


func test_top_note_rect() -> void:
	for p in _amounts():
		var o := Vector2(50, 60)
		var r := MoneyDraw.top_note_rect(p, o, 1.0)
		if p >= 500:
			assert_true(r.size.x > 0.0 and r.size.y > 0.0, "target at %d" % p)
			assert_true(MoneyDraw.pile_bounds(p, o, 1.0).encloses(r), "target inside bounds at %d" % p)
		else:
			assert_eq(r.size, Vector2.ZERO, "no fiver at %d" % p)


func test_notes_stay_countable() -> void:
	var items := MoneyDraw.pile_layout(2000, Vector2.ZERO, 1.0)
	assert_eq(items.size(), 4)
	for i in range(1, 4):
		assert_true(items[i]["pos"].y - items[i - 1]["pos"].y >= 7.0, "each fiver's top strip shows")


func test_empty_pile() -> void:
	assert_eq(MoneyDraw.pile_layout(0, Vector2.ZERO, 1.0).size(), 0)
	assert_eq(MoneyDraw.pile_bounds(0, Vector2(5, 5), 1.0).size, Vector2.ZERO)


func test_sizes_scale_linearly() -> void:
	for d in MoneyBreakdown.DENOMINATIONS:
		var a := MoneyDraw.item_size(d, 1.0)
		var b := MoneyDraw.item_size(d, 2.5)
		assert_near(b.x, a.x * 2.5, 0.001, "w %d" % d)
		assert_near(b.y, a.y * 2.5, 0.001, "h %d" % d)
	assert_true(MoneyDraw.item_size(200, 1.0).x > MoneyDraw.item_size(5, 1.0).x)
	assert_true(MoneyDraw.item_size(2000, 1.0).x > MoneyDraw.item_size(200, 1.0).x)


func test_pile_places_scale_with_u() -> void:
	var a := MoneyDraw.pile_layout(2750, Vector2.ZERO, 1.0)
	var b := MoneyDraw.pile_layout(2750, Vector2.ZERO, 2.0)
	for i in a.size():
		assert_near(b[i]["pos"].x, a[i]["pos"].x * 2.0, 1.0)
		assert_near(b[i]["pos"].y, a[i]["pos"].y * 2.0, 1.0)


func test_transition_ends() -> void:
	var pairs := [[2000, 1500], [1500, 2750], [4000, 3500], [0, 500], [500, 0], [2750, 2750], [799, 1234], [10000, 45], [4500, 9050]]
	for pr in pairs:
		var o := Vector2(40, 50)
		var away := Vector2(300, -20)
		assert_eq(_sum(MoneyDraw.transition_items(pr[0], pr[1], 0.0, o, 1.0, away)), pr[0], "start %s" % str(pr))
		assert_eq(_sum(MoneyDraw.transition_items(pr[0], pr[1], 1.0, o, 1.0, away)), pr[1], "end %s" % str(pr))
		var final := MoneyDraw.transition_items(pr[0], pr[1], 1.0, o, 1.0, away)
		var lay := MoneyDraw.pile_layout(pr[1], o, 1.0)
		assert_eq(final.size(), lay.size(), "end count %s" % str(pr))
		for it in final:
			assert_false(it["moving"])
		assert_eq(_count(final), _count(lay))


func test_transition_middle_never_invents() -> void:
	var pairs := [[2000, 1500], [1500, 2750], [4000, 3500], [4500, 9050], [10000, 45], [0, 3000]]
	for pr in pairs:
		var d := MoneyBreakdown.diff(pr[0], pr[1])
		var keep := _count(d["keep"])
		var rem := _count(d["remove"])
		var add := _count(d["add"])
		var step := 0.0
		while step <= 1.0001:
			var items := MoneyDraw.transition_items(pr[0], pr[1], step, Vector2(40, 50), 1.0, Vector2(300, -20))
			var have := _count(items)
			for den in have:
				var lo: int = int(keep.get(den, 0))
				var hi: int = lo + int(rem.get(den, 0)) + int(add.get(den, 0))
				assert_true(int(have[den]) >= lo and int(have[den]) <= hi, "%d count %d at %f for %s" % [den, have[den], step, str(pr)])
			for den in keep:
				assert_true(int(have.get(den, 0)) >= int(keep[den]), "keep %d present" % den)
			for it in items:
				assert_true(it["alpha"] >= 0.0 and it["alpha"] <= 1.0)
			step += 0.05


func test_fiver_leaves_one_at_a_time() -> void:
	var moving_seen := 0
	var step := 0.0
	while step <= 1.0:
		var items := MoneyDraw.transition_items(2000, 1500, step, Vector2.ZERO, 1.0, Vector2(200, -40))
		var mv := 0
		for it in items:
			if it["moving"]:
				mv += 1
		assert_true(mv <= 1, "one item in flight")
		moving_seen += mv
		step += 0.02
	assert_true(moving_seen > 3, "the fiver is seen travelling")


func _places(items: Array, den: int) -> Array:
	var out: Array = []
	for it in items:
		if it["denomination"] == den:
			out.append(it["pos"])
	return out


func test_keep_items_do_not_move() -> void:
	var pairs := [[2000, 1500], [1500, 2750], [4000, 3500], [4500, 9050], [799, 1234]]
	for pr in pairs:
		var o := Vector2(40, 50)
		var keep := _count(MoneyBreakdown.diff(pr[0], pr[1])["keep"])
		var from_lay := MoneyDraw.pile_layout(pr[0], o, 1.0)
		var to_lay := MoneyDraw.pile_layout(pr[1], o, 1.0)
		var start := MoneyDraw.transition_items(pr[0], pr[1], 0.0, o, 1.0, Vector2(300, 0))
		var mid := MoneyDraw.transition_items(pr[0], pr[1], 0.5, o, 1.0, Vector2(300, 0))
		var end := MoneyDraw.transition_items(pr[0], pr[1], 1.0, o, 1.0, Vector2(300, 0))
		for den in keep:
			var n: int = keep[den]
			var a := _places(from_lay, den).slice(0, n)
			assert_eq(a, _places(to_lay, den).slice(0, n), "layouts agree on kept %d for %s" % [den, str(pr)])
			for frame in [start, mid, end]:
				var shown := _places(frame, den)
				for pos in a:
					assert_true(shown.has(pos), "kept %d stays put for %s" % [den, str(pr)])


func test_transition_same_amount_is_the_pile() -> void:
	var o := Vector2(20, 30)
	for p in [0, 750, 2750]:
		var items := MoneyDraw.transition_items(p, p, 0.5, o, 1.0, Vector2(100, 0))
		var lay := MoneyDraw.pile_layout(p, o, 1.0)
		assert_eq(items.size(), lay.size())
		for it in items:
			assert_false(it["moving"])
