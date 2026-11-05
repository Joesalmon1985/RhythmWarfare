extends TestCase
## How an amount of pence is split into notes and coins, and the pile diff between two amounts.


func _sum(a: Array) -> int:
	var t := 0
	for d in a:
		t += int(d)
	return t


func _sorted_desc(a: Array) -> bool:
	for i in range(1, a.size()):
		if a[i] > a[i - 1]:
			return false
	return true


func _merged(a: Array, b: Array) -> Array:
	var m := a.duplicate()
	m.append_array(b)
	m.sort()
	return m


func _sorted(a: Array) -> Array:
	var m := a.duplicate()
	m.sort()
	return m


func test_examples() -> void:
	assert_eq(MoneyBreakdown.breakdown(2000), [500, 500, 500, 500])
	assert_eq(MoneyBreakdown.breakdown(4000), [2000, 500, 500, 500, 500])
	assert_eq(MoneyBreakdown.breakdown(2750), [500, 500, 500, 500, 500, 200, 50])
	assert_eq(MoneyBreakdown.breakdown(750), [500, 200, 50])
	assert_eq(MoneyBreakdown.breakdown(500), [500])
	assert_eq(MoneyBreakdown.breakdown(1), [1])
	assert_eq(MoneyBreakdown.breakdown(499), [200, 200, 50, 20, 20, 5, 2, 2])


func test_empty_for_zero_and_negative() -> void:
	assert_eq(MoneyBreakdown.breakdown(0), [])
	assert_eq(MoneyBreakdown.breakdown(-50), [])


func test_sum_is_the_amount() -> void:
	var p := 0
	while p <= 30000:
		var b := MoneyBreakdown.breakdown(p)
		assert_eq(_sum(b), p, "sum at %d" % p)
		assert_true(_sorted_desc(b), "sorted at %d" % p)
		p += 1 if p < 1000 else 50


func test_only_known_denominations() -> void:
	for p in [1, 37, 999, 2750, 12345]:
		for d in MoneyBreakdown.breakdown(p):
			assert_true(MoneyBreakdown.DENOMINATIONS.has(d), "%d" % d)


func test_deterministic() -> void:
	for p in [0, 1, 750, 2750, 4000, 12345]:
		assert_eq(MoneyBreakdown.breakdown(p), MoneyBreakdown.breakdown(p))


func test_is_note() -> void:
	assert_true(MoneyBreakdown.is_note(2000))
	assert_true(MoneyBreakdown.is_note(1000))
	assert_true(MoneyBreakdown.is_note(500))
	assert_false(MoneyBreakdown.is_note(200))
	assert_false(MoneyBreakdown.is_note(1))


func _check_diff(a: int, b: int) -> void:
	var d := MoneyBreakdown.diff(a, b)
	assert_eq(_merged(d["keep"], d["remove"]), _sorted(MoneyBreakdown.breakdown(a)), "keep+remove %d->%d" % [a, b])
	assert_eq(_merged(d["keep"], d["add"]), _sorted(MoneyBreakdown.breakdown(b)), "keep+add %d->%d" % [a, b])
	assert_eq(_sum(d["keep"]) + _sum(d["add"]), b)
	assert_eq(_sum(d["keep"]) + _sum(d["remove"]), a)
	for part in ["keep", "remove", "add"]:
		assert_true(_sorted_desc(d[part]), "%s sorted %d->%d" % [part, a, b])
	for x in d["remove"]:
		assert_false(d["add"].has(x), "a denomination is not both removed and added")


func test_diff_properties() -> void:
	var amounts := [0, 1, 50, 500, 750, 1500, 2000, 2500, 2750, 4000, 6000, 12345]
	for a in amounts:
		for b in amounts:
			_check_diff(a, b)


func test_diff_blackjack_cases() -> void:
	for pair in [[2000, 1500], [1500, 2750], [1500, 2500], [500, 0], [0, 500]]:
		_check_diff(pair[0], pair[1])
	var lose := MoneyBreakdown.diff(2000, 1500)
	assert_eq(lose["remove"], [500])
	assert_eq(lose["add"], [])
	assert_eq(lose["keep"], [500, 500, 500])
	var gone := MoneyBreakdown.diff(500, 0)
	assert_eq(gone["remove"], [500])
	assert_eq(gone["keep"], [])
	var fresh := MoneyBreakdown.diff(0, 500)
	assert_eq(fresh["add"], [500])
	var same := MoneyBreakdown.diff(750, 750)
	assert_eq(same["keep"], [500, 200, 50])
	assert_eq(same["remove"], [])
	assert_eq(same["add"], [])
