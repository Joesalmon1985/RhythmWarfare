extends TestCase
## The run wallet (integer pence, holds that settle exactly once) and how RunProgress saves it.

var _emitted := 0


func _count() -> void:
	_emitted += 1


func _tmp(name: String) -> String:
	return "user://test_run_%s.json" % name


func _rm(path: String) -> void:
	for p in [path, path + ".tmp", path + ".corrupt"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)


func _write(path: String, d: Dictionary) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(d))
	f.close()


func test_starts_at_twenty_pounds() -> void:
	var w := RunWallet.new()
	assert_eq(w.balance_pence(), 2000)
	assert_eq(w.held_pence(), 0)
	assert_eq(RunWallet.START_PENCE, 2000)


func test_spend_add_refund_arithmetic() -> void:
	var w := RunWallet.new()
	assert_true(w.spend(500))
	assert_eq(w.balance_pence(), 1500)
	w.add(250)
	assert_eq(w.balance_pence(), 1750)
	w.refund(250)
	assert_eq(w.balance_pence(), 2000)
	assert_true(w.spend(2000), "can spend everything")
	assert_eq(w.balance_pence(), 0)


func test_cannot_overspend() -> void:
	var w := RunWallet.new()
	assert_false(w.can_afford(2001))
	assert_true(w.can_afford(2000))
	assert_false(w.spend(2001))
	assert_eq(w.balance_pence(), 2000)
	assert_false(w.hold("a", 2001))
	assert_eq(w.held_pence(), 0)


func test_zero_and_negative_amounts_change_nothing() -> void:
	var w := RunWallet.new()
	_emitted = 0
	w.changed.connect(_count)
	assert_false(w.spend(0))
	assert_false(w.spend(-100))
	w.add(0)
	w.add(-100)
	w.refund(-5)
	assert_false(w.hold("a", 0))
	assert_false(w.hold("a", -5))
	assert_false(w.can_afford(0))
	assert_eq(w.balance_pence(), 2000)
	assert_eq(w.held_pence(), 0)
	assert_eq(_emitted, 0, "no signal for refusals")


func test_hold_conserves_money() -> void:
	var w := RunWallet.new()
	assert_true(w.hold("hand", 500))
	assert_eq(w.balance_pence(), 1500)
	assert_eq(w.held_pence(), 500)
	assert_eq(w.balance_pence() + w.held_pence(), 2000)


func test_double_hold_of_a_tag_is_refused() -> void:
	var w := RunWallet.new()
	assert_true(w.hold("hand", 500))
	assert_false(w.hold("hand", 100))
	assert_eq(w.balance_pence(), 1500)
	assert_eq(w.held_pence(), 500)
	assert_true(w.hold("other", 100), "a different tag is fine")
	assert_eq(w.held_pence(), 600)


func test_settle_pays_exactly_once() -> void:
	var w := RunWallet.new()
	w.hold("hand", 500)
	assert_true(w.settle("hand", 1000))
	assert_eq(w.balance_pence(), 2500)
	assert_eq(w.held_pence(), 0)
	assert_false(w.settle("hand", 1000))
	assert_eq(w.balance_pence(), 2500)


func test_settle_lost_and_push() -> void:
	var w := RunWallet.new()
	w.hold("a", 500)
	assert_true(w.settle("a", 0))
	assert_eq(w.balance_pence(), 1500)
	w.hold("b", 500)
	assert_true(w.settle("b", 500))
	assert_eq(w.balance_pence(), 1500)


func test_blackjack_payout() -> void:
	var w := RunWallet.new()
	w.hold("hand", 500)
	assert_true(w.settle("hand", 1250))
	assert_eq(w.balance_pence(), 2750)


func test_unknown_tag_settle_and_release() -> void:
	var w := RunWallet.new()
	_emitted = 0
	w.changed.connect(_count)
	assert_false(w.settle("nope", 100))
	assert_false(w.release("nope"))
	assert_eq(w.balance_pence(), 2000)
	assert_eq(_emitted, 0)


func test_release_returns_exactly_once() -> void:
	var w := RunWallet.new()
	w.hold("hand", 700)
	assert_true(w.release("hand"))
	assert_eq(w.balance_pence(), 2000)
	assert_eq(w.held_pence(), 0)
	assert_false(w.release("hand"))
	assert_eq(w.balance_pence(), 2000)


func test_release_after_settle_is_refused() -> void:
	var w := RunWallet.new()
	w.hold("hand", 500)
	w.settle("hand", 0)
	assert_false(w.release("hand"))
	assert_eq(w.balance_pence(), 1500)


func test_settle_after_release_is_refused() -> void:
	var w := RunWallet.new()
	w.hold("hand", 500)
	w.release("hand")
	assert_false(w.settle("hand", 1000))
	assert_eq(w.balance_pence(), 2000)


func test_release_all() -> void:
	var w := RunWallet.new()
	w.hold("a", 300)
	w.hold("b", 400)
	assert_eq(w.release_all(), 700)
	assert_eq(w.balance_pence(), 2000)
	assert_eq(w.held_pence(), 0)
	assert_eq(w.release_all(), 0)


func test_reset() -> void:
	var w := RunWallet.new()
	w.hold("a", 300)
	w.add(5000)
	w.reset()
	assert_eq(w.balance_pence(), 2000)
	assert_eq(w.held_pence(), 0)
	assert_false(w.settle("a", 100), "holds are gone")


func test_dict_round_trip() -> void:
	var w := RunWallet.new()
	w.hold("a", 300)
	w.spend(50)
	var d := w.to_dict()
	assert_eq(d["pence"], 1650)
	assert_eq(d["held"], {"a": 300})
	var v := RunWallet.new()
	v.load_dict(d)
	assert_eq(v.balance_pence(), 1950, "held folds into the balance")
	assert_eq(v.held_pence(), 0)


func test_dict_round_trip_through_json() -> void:
	var w := RunWallet.new()
	w.spend(425)
	var v := RunWallet.new()
	v.load_dict(JSON.parse_string(JSON.stringify(w.to_dict())))
	assert_eq(v.balance_pence(), 1575)


func test_load_dict_garbage_is_sane() -> void:
	for bad in [null, "string", 12, [1, 2], {}, {"pence": -5}, {"pence": "lots"}, {"pence": 12.5}, {"pence": null, "held": 3}, {"held": {"a": 100}}]:
		var w := RunWallet.new()
		w.spend(700)
		w.load_dict(bad)
		assert_true(w.balance_pence() >= 0, "never negative: %s" % str(bad))
		assert_eq(w.held_pence(), 0)
	var w2 := RunWallet.new()
	w2.load_dict(null)
	assert_eq(w2.balance_pence(), 2000)
	w2.spend(100)
	w2.load_dict({"pence": -5})
	assert_eq(w2.balance_pence(), 2000)
	w2.load_dict({"pence": 12.5})
	assert_eq(w2.balance_pence(), 2000)
	w2.load_dict({"pence": 750.0})
	assert_eq(w2.balance_pence(), 750, "a whole float from JSON is fine")
	w2.load_dict({"pence": 500, "held": {"a": -100, "b": "x", "c": 1.5, "d": 200}})
	assert_eq(w2.balance_pence(), 700, "only valid held stakes are returned")


func test_changed_emitted_on_each_real_change() -> void:
	var w := RunWallet.new()
	w.changed.connect(_count)
	_emitted = 0
	w.spend(100)
	assert_eq(_emitted, 1)
	w.add(100)
	assert_eq(_emitted, 2)
	w.refund(100)
	assert_eq(_emitted, 3)
	w.hold("a", 100)
	assert_eq(_emitted, 4)
	w.settle("a", 0)
	assert_eq(_emitted, 5)
	w.hold("b", 100)
	w.release("b")
	assert_eq(_emitted, 7)
	w.hold("c", 100)
	w.release_all()
	assert_eq(_emitted, 9)
	w.reset()
	assert_eq(_emitted, 10)


func test_fresh_run_progress_has_a_wallet() -> void:
	var path := _tmp("wallet_fresh")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	assert_eq(p.wallet.balance_pence(), 2000)
	assert_eq(p.data["wallet"]["pence"], 2000)
	_rm(path)


func test_wallet_change_is_persisted() -> void:
	var path := _tmp("wallet_persist")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	assert_true(p.wallet.spend(750))
	var again := RunProgress.load_data(path, "user://none.json")
	assert_eq(again.wallet.balance_pence(), 1250)
	assert_false(again.recovered_from_corrupt)
	again.wallet.add(100)
	assert_eq(RunProgress.load_data(path, "user://none.json").wallet.balance_pence(), 1350)
	_rm(path)


func test_old_save_without_wallet_loads() -> void:
	var path := _tmp("wallet_old")
	_rm(path)
	_write(path, {"version": 2, "reached": {"mothership": {"entries": 1}}, "runs": 3, "best_phases": 2, "migrated_from": "", "flags": {}})
	var p := RunProgress.load_data(path, "user://none.json")
	assert_false(p.recovered_from_corrupt)
	assert_false(FileAccess.file_exists(path + ".corrupt"))
	assert_true(p.is_reached("mothership"))
	assert_eq(int(p.data["runs"]), 3)
	assert_eq(p.wallet.balance_pence(), 2000)
	_rm(path)


func test_held_stakes_in_a_save_return_to_the_balance() -> void:
	var path := _tmp("wallet_held")
	_rm(path)
	_write(path, {"version": 2, "reached": {}, "runs": 1, "best_phases": 0, "migrated_from": "", "flags": {}, "wallet": {"pence": 1000, "held": {"hand": 500}}})
	var p := RunProgress.load_data(path, "user://none.json")
	assert_eq(p.wallet.balance_pence(), 1500)
	assert_eq(p.wallet.held_pence(), 0)
	assert_eq(int(p.data["wallet"]["pence"]), 1500)
	assert_eq(p.data["wallet"]["held"], {})
	assert_false(p.wallet.settle("hand", 1000), "the hand does not resume")
	_rm(path)


func test_a_held_stake_in_the_file_is_refunded_on_reload() -> void:
	var path := _tmp("wallet_midhand")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	p.wallet.hold("hand", 500)
	var again := RunProgress.load_data(path, "user://none.json")
	assert_eq(again.wallet.balance_pence(), 2000, "an interrupted hand is refunded on load")
	_rm(path)


func test_run_started_resets_and_persists() -> void:
	var path := _tmp("wallet_run")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	p.wallet.spend(1900)
	p.run_started()
	assert_eq(p.wallet.balance_pence(), 2000)
	assert_eq(RunProgress.load_data(path, "user://none.json").wallet.balance_pence(), 2000)
	p.wallet.spend(100)
	assert_eq(RunProgress.load_data(path, "user://none.json").wallet.balance_pence(), 1900, "still saving after a reset")
	_rm(path)


func test_entering_levels_does_not_change_the_wallet() -> void:
	var path := _tmp("wallet_enter")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	p.wallet.spend(500)
	p.enter("mothership")
	p.enter("underworld")
	assert_eq(p.wallet.balance_pence(), 1500)
	assert_eq(RunProgress.load_data(path, "user://none.json").wallet.balance_pence(), 1500)
	_rm(path)
