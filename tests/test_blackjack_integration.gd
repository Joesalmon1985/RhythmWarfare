extends TestCase
## Blackjack inside the real run scene on the virtual clock (docs/BLACKJACK_INTEGRATION.md sections 0, 5 and 6): the day room's `ward.cards` hotspot, the real BlackjackActivity, the real wallet
## (an isolated RunProgress, so the player's save is never touched). Play is driven with `scene.minigames.tap(...)` (the same call a touch on the view makes) or RW_MINIGAME_TAPS, and read back from
## the activity's snapshot, the controller's log, the scene's logs and the wallet, so every test passes with or without the close-up view. RW_MINIGAME_SEED fixes the cards.

const BEAT := 60.0 / 174.0
const STEP := 1.0 / 30.0
const TMP_SAVE := "user://test_blackjack_integration_save.json"
const CFG := "res://content/minigames/blackjack.json"
const QUIET := ["", "sitting", "leaving", "falling"]

var _saved: RunProgress


# ---- harness ----------------------------------------------------------------------------------------------------------------------------------

func _scene(bot := "perfect", seed := 7, taps := "", size := Vector2(1152, 648), start := "ward") -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_RUN_START", start)
	OS.set_environment("RW_MINIGAME_TAPS", taps)
	OS.set_environment("RW_MINIGAME_SEED", str(seed))
	Session.run_start_node = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS", "RW_MINIGAME_SEED"]:
		OS.set_environment(k, "")
	OS.unset_environment("RW_RUN_START")


func _run_to(scene: Node, t_end: float, step := STEP) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += step
		scene._vt = t
		scene._step_virtual(t)


## Runs to beat `beat` of the scene's current phase.
func _to_beat(scene: Node, beat: float) -> void:
	_run_to(scene, scene.engine.t_of(beat))


func _wallet() -> RunWallet:
	return Session.run_progress.wallet


func _mg(scene: Node) -> MinigameController:
	return scene.minigames


func _snap(scene: Node) -> Dictionary:
	var a: MinigameActivity = _mg(scene).activity
	return a.state() if a != null else {}


func _phase(scene: Node) -> String:
	return str(_snap(scene).get("phase", ""))


func _events(scene: Node, kind: String) -> Array:
	return (scene.event_log as Array).filter(func(e: Dictionary) -> bool: return str(e["kind"]) == kind)


func _log(scene: Node, kind: String) -> Array:
	return (_mg(scene).log as Array).filter(func(e: Dictionary) -> bool: return str(e["kind"]) == kind)


func _nodes(scene: Node) -> Array:
	return (scene.phase_log as Array).map(func(p: Dictionary) -> String: return str(p["node"]))


## Touches the table in the final window of the current phase (beat 50) and runs on to just past the next downbeat (seated when the last block passed). Returns the downbeat's song time.
func _sit(scene: Node) -> float:
	var down: float = scene.engine.t_of(64.0)
	_to_beat(scene, 50.0)
	assert_true(scene.hotspot_select("ward.cards"), "the table can be touched in the final window")
	_run_to(scene, down + 0.02)
	return down


## A bot pattern for `blocks:` that passes the first phase and then follows `rest` (a miss once the pattern is over).
func _pattern(rest: String) -> String:
	return "blocks:1111" + rest


## Plays blackjack through the controller: bet, then twist or stick by `plan` ("stick": always at once, "mix": every other hand twists once if it can, "at:<n>": twist under n). Every frame
## also checks that the visible pile is the wallet's balance and the bet spot its held stake (outside sitting and leaving), and records each settled hand in ctx["hands"].
func _frame(scene: Node, ctx: Dictionary, step := STEP) -> void:
	var t: float = scene._vt + step
	scene._vt = t
	scene._step_virtual(t)
	var mg := _mg(scene)
	if mg.state != "active" or mg.activity == null:
		return
	var w := _wallet()
	var s := mg.activity.state()
	var phase := str(s["phase"])
	if not (phase in QUIET):
		if int(s["pile"]["pence"]) != w.balance_pence() or int(s["bet"]["pence"]) != w.held_pence():
			ctx["viol"].append("%s at %.2f: pile %d balance %d bet %d held %d" % [phase, t, int(s["pile"]["pence"]), w.balance_pence(), int(s["bet"]["pence"]), w.held_pence()])
	if not bool(ctx.get("play", true)):
		return
	var tg: Array = s["targets"]
	match phase:
		"await_bet":
			if "bet" in tg and not bool(ctx.get("hand_open", false)) and (ctx["hands"] as Array).size() < int(ctx.get("max_hands", 1000)):
				ctx["bal_before"] = w.balance_pence()
				ctx["hand_open"] = true
				ctx["tw"] = 0
				if not mg.tap("bet", t):
					ctx["viol"].append("bet refused at %.2f" % t)
				elif w.balance_pence() != int(ctx["bal_before"]) - 500 or w.held_pence() != 500:
					ctx["viol"].append("bet did not move 500 to the hold: %d/%d" % [w.balance_pence(), w.held_pence()])
		"player_turn":
			if "deck" in tg:
				var plan := str(ctx.get("plan", "stick"))
				var total := _total_of(s, "player")
				var twist := false
				if plan == "mix":
					twist = (ctx["hands"] as Array).size() % 2 == 0 and int(ctx["tw"]) == 0 and total <= 16
				elif plan.begins_with("at:"):
					twist = total < int(plan.get_slice(":", 1))
				if twist:
					ctx["tw"] = int(ctx["tw"]) + 1
					ctx["twists"] = int(ctx.get("twists", 0)) + 1
					if not mg.tap("deck", t):
						ctx["viol"].append("twist refused at %.2f" % t)
				else:
					ctx["sticks"] = int(ctx.get("sticks", 0)) + 1
					if not mg.tap("hand", t):
						ctx["viol"].append("stick refused at %.2f" % t)
		"settling":
			if bool(ctx.get("hand_open", false)) and str((s["seats"]["player"] as Dictionary)["result"]) != "":
				ctx["hand_open"] = false
				var ex := _expected(s)
				ctx["hands"].append({"result": ex["result"], "snap_result": s["seats"]["player"]["result"], "payout": ex["payout"], "bal_before": ctx["bal_before"], "bal_after": w.balance_pence(),
					"held_after": w.held_pence(), "player": _cards_key(s, "player"), "dealer": _cards_key(s, "dealer"), "hand": int(s["hand"])})


func _live(s: Dictionary, seat: String) -> Array:
	return ((s["seats"][seat] as Dictionary)["cards"] as Array).filter(func(c: Dictionary) -> bool: return float(c["t_clear"]) < 0.0)


func _cards_key(s: Dictionary, seat: String) -> String:
	return ",".join(PackedStringArray(_live(s, seat).map(func(c: Dictionary) -> String: return "%d.%d" % [int(c["rank"]), int(c["suit"])])))


func _total_of(s: Dictionary, seat: String) -> int:
	var seen := _live(s, seat).filter(func(c: Dictionary) -> bool: return bool(c["face_up"]) and float(c["t_land"]) <= float(s["t"]))
	return int(BlackjackGame.hand_value(seen)["total"])


## The result and the money back for the player's settled hand, worked out from the snapshot's cards alone (the rules of docs section 4).
func _expected(s: Dictionary) -> Dictionary:
	var pv := BlackjackGame.hand_value(_live(s, "player"))
	var dv := BlackjackGame.hand_value(_live(s, "dealer"))
	var res := "lose"
	if pv["bust"]:
		res = "bust"
	elif pv["natural"]:
		res = "push" if dv["natural"] else "blackjack"
	elif dv["natural"]:
		res = "lose"
	elif dv["bust"] or int(pv["total"]) > int(dv["total"]):
		res = "win"
	elif int(pv["total"]) == int(dv["total"]):
		res = "push"
	var stake := 500
	var pays: Dictionary = {"blackjack": stake * 5 / 2, "win": stake * 2, "push": stake}
	return {"result": res, "payout": int(pays.get(res, 0))}


func _ctx(plan := "stick") -> Dictionary:
	return {"viol": [], "hands": [], "plan": plan}


## Runs frames until `done` returns true (or `limit_beats` of song time pass); returns whether it did.
func _until(scene: Node, ctx: Dictionary, done: Callable, limit_beats: float, step := STEP) -> bool:
	var end: float = float(scene._vt) + limit_beats * BEAT
	while float(scene._vt) < end:
		_frame(scene, ctx, step)
		if done.call():
			return true
	return false


## The seed's first hand played by always sticking, in a bare activity with its own wallet: {result, natural}. Seeds are searched with this so a test can have a hand it knows.
func _first_hand(seed: int) -> Dictionary:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CFG))
	var w := RunWallet.new()
	var a := BlackjackActivity.new()
	a.setup({"wallet": w, "seed": seed, "beat_s": BEAT, "config": cfg})
	a.begin(0.0)
	var t := 0.0
	while t < 300.0 * BEAT:
		t += STEP
		a.update(t)
		var s := a.state()
		match str(s["phase"]):
			"await_bet":
				a.tap("bet", t)
			"player_turn":
				a.tap("hand", t)
			"settling":
				if str(s["seats"]["player"]["result"]) != "":
					return {"result": str(s["seats"]["player"]["result"]), "natural": bool(BlackjackGame.hand_value(_live(s, "player"))["natural"]), "balance": w.balance_pence()}
	return {}


func _seed_where(pred: Callable) -> int:
	for sd in range(1, 400):
		var h := _first_hand(sd)
		if not h.is_empty() and pred.call(h):
			return sd
	return -1


# ---- 1: the hotspot ----------------------------------------------------------------------------------------------------------------------------

func test_the_table_is_a_72_px_touch_target_on_the_stage_and_the_day_room_alone_has_five_hotspots() -> void:
	var d := _scene("perfect", 7, "", Vector2(844, 390))
	var scene: Node = d["scene"]
	_to_beat(scene, 52.0)
	var items: Array = scene.hotspot_items()
	var ids: Array = items.map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_contains(ids, "ward.cards", "the table is on show in the day room's final window: %s" % str(ids))
	assert_eq(items.size(), 5, "the day room shows five hotspots")
	var stage := Rect2(scene._stage_host.global_position, scene._stage_host.size)
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var lay := HotspotView.layout(items, st.map, st.crowds, scene._exit_pose(), stage.size)
	assert_eq(lay.size(), 5, "every hotspot has a place on the 844x390 screen")
	var pads: Dictionary = scene.pad_view.button_rects()
	var found := false
	for e in lay:
		if str(e["id"]) != "ward.cards":
			continue
		found = true
		var c: Vector2 = (e["centre"] as Vector2) + stage.position
		var rad := float(e["radius_px"])
		var r := Rect2(c - Vector2(rad, rad), Vector2(rad, rad) * 2.0)
		assert_true(r.size.x >= 72.0 - 0.01, "the table's touch target is at least 72 px (%s)" % str(r.size))
		assert_true(stage.has_point(c), "the table's target centres on the stage")
		assert_true(stage.encloses(r) or stage.grow(0.5).encloses(r), "the whole target lies on the stage (%s in %s)" % [str(r), str(stage)])
		for p in pads:
			assert_false(r.intersects(pads[p] as Rect2), "the table's target does not touch pad %s" % str(p))
	assert_true(found, "the table has a layout entry")
	var data: RunData = scene.data
	assert_true(data.errors.is_empty(), "the content validates (at most four hotspots on show anywhere but the day room, five there): %s" % str(data.errors))
	assert_eq(int(data.nodes["ward"].get("max_hotspots", 4)), 5, "the day room raises its own cap")
	assert_eq((data.hotspots["ward"] as Array).size(), 5)
	assert_true(data.hotspots.keys().all(func(k: Variant) -> bool: return str(k) == "ward" or int(data.nodes[k].get("max_hotspots", 4)) == 4), "every other scene keeps the cap of four")
	for id in data.nodes:
		if str(id) == "ward":
			continue
		assert_false(data.nodes[id].has("max_hotspots"), "%s keeps the default cap" % str(id))
	_free(d)


# ---- 2 and 3: sitting down or being waved off ---------------------------------------------------------------------------------------------------

func test_a_passed_last_block_sits_the_player_on_the_next_downbeat() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var down: float = scene.engine.t_of(64.0)
	assert_eq(_wallet().balance_pence(), 2000, "a new run starts with 20 pounds")
	_to_beat(scene, 50.0)
	assert_true(scene.hotspot_select("ward.cards"))
	_run_to(scene, down - 0.2)
	assert_eq(_mg(scene).state, "entering", "requested at the commit, not yet seated")
	assert_true(scene.engine.hold)
	_run_to(scene, down + 0.02)
	var mg := _mg(scene)
	assert_eq(mg.state, "active")
	var commit: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")[0]
	assert_true(bool(commit["success"]), "the last block was passed")
	assert_eq(str(commit["route"]), "ward", "the run stays in the day room")
	var begin: Dictionary = _log(scene, "begin")[0]
	assert_near(float(begin["t"]), down, 1e-9, "seated exactly on the downbeat")
	var walked: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and str((a["args"] as Dictionary).get("to", "")) == "day_cards")
	assert_false(walked.is_empty(), "the camera was walked to the chair (day_cards)")
	assert_eq(_wallet().balance_pence(), 2000, "sitting costs nothing")
	_run_to(scene, down + 5.0 * BEAT)
	var s := _snap(scene)
	assert_eq(str(s["phase"]), "await_bet", "the pockets are emptied and the dealer waits for a bet")
	assert_eq(int(s["pile"]["pence"]), 2000, "the pile on the table is the whole 20 pounds")
	assert_eq(int(s["pile"]["from_pence"]), 0, "it came out of the pockets")
	assert_true(float(s["pile"]["t0"]) + float(s["pile"]["dur"]) <= float(s["t"]), "the movement is over")
	assert_eq(_wallet().balance_pence(), 2000)
	_free(d)


func test_a_missed_last_block_is_the_dealer_waving_you_off() -> void:
	var d := _scene("blocks:1110")
	var scene: Node = d["scene"]
	_to_beat(scene, 50.0)
	assert_true(scene.hotspot_select("ward.cards"))
	_to_beat(scene, 66.0)
	var commit: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")[0]
	assert_false(bool(commit["success"]), "the last block was missed")
	assert_eq(_mg(scene).log, [], "not seated: no activity was requested")
	assert_false(scene.engine.hold)
	assert_false(scene.hud.silent)
	var blocks := _events(scene, "block_result").filter(func(e: Dictionary) -> bool: return float(e["t"]) < float(commit["t"]) + 1e-6)
	var before := float((blocks.back() as Dictionary)["energy"])
	assert_near(float(commit["energy"]), before - 3.0, 0.001, "the failure costs three energy")
	var waved: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and str((a["args"] as Dictionary).get("to", "")) == "day_cards")
	assert_false(waved.is_empty(), "the failure cinematic walks to the table and looks")
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"], "the run leaves by the default exit (decision B2)")
	assert_eq(_wallet().balance_pence(), 2000)
	_free(d)


# ---- 4: hands --------------------------------------------------------------------------------------------------------------------------------

func test_hands_are_played_with_the_right_money_for_each_result() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit(scene)
	var ctx := _ctx("mix")
	assert_true(_until(scene, ctx, func() -> bool: return (ctx["hands"] as Array).size() >= 4, 240.0), "four hands were played: %d" % (ctx["hands"] as Array).size())
	assert_eq(ctx["viol"], [], "the pile is the wallet's balance and the bet spot the held stake at every frame")
	var w := _wallet()
	var total := 2000
	for h in ctx["hands"]:
		var hand: Dictionary = h
		assert_eq(str(hand["snap_result"]), str(hand["result"]), "hand %d: the snapshot's result is the one the cards give" % int(hand["hand"]))
		assert_eq(int(hand["bal_after"]), int(hand["bal_before"]) - 500 + int(hand["payout"]), "hand %d (%s): the balance moved by the payout of a %s" % [int(hand["hand"]), str(hand["player"]), str(hand["result"])])
		assert_eq(int(hand["held_after"]), 0, "the stake is no longer held once settled")
		total += int(hand["payout"]) - 500
	assert_eq(w.balance_pence() + w.held_pence(), total, "the money adds up: balance plus a live stake is 20 pounds plus the hands' winnings and losses")
	assert_true(int(ctx.get("twists", 0)) >= 1, "a twist was played")
	assert_true(int(ctx.get("sticks", 0)) >= 1, "a stick was played")
	var taps := _log(scene, "tap")
	assert_true(taps.size() >= 8 and taps.all(func(e: Dictionary) -> bool: return bool(e["ok"])), "every tap the player made was taken")
	assert_eq(_mg(scene).state, "active", "still seated")
	_free(d)


# ---- 5: the run goes on under the table -------------------------------------------------------------------------------------------------------

func test_the_run_stays_in_the_day_room_across_phase_boundaries_while_seated() -> void:
	var d := _scene(_pattern("01".repeat(30)))
	var scene: Node = d["scene"]
	var down := _sit(scene)
	var mg := _mg(scene)
	assert_eq(mg.state, "active")
	var e0: int = scene.event_log.size()
	var commits0 := _events(scene, "hotspot_commit").size()
	_run_to(scene, down + BEAT)
	var jlog0: int = scene.journey_log.size()
	var rail0: int = scene.journey.log.size()
	var notes0: int = scene.engine.level.notes.size()
	var t_end := down + 3.0 * 64.0 * BEAT + 8.0 * BEAT
	while float(scene._vt) < t_end:
		_run_to(scene, float(scene._vt) + 0.5)
		assert_true(scene.hud.silent, "the HUD stays silent")
		assert_true((scene.hotspot_items() as Array).is_empty(), "the hotspot view stays empty at beat %.1f" % scene.engine.phase_beat_at(scene._vt))
		assert_eq(scene.engine.node_id, "ward", "still in the day room")
		assert_true(scene.engine.hold)
	var fresh: Array = (scene.event_log as Array).slice(e0)
	var starts := fresh.filter(func(e: Dictionary) -> bool: return str(e["kind"]) == "phase_start")
	assert_true(starts.size() >= 3, "three phase boundaries passed (%d)" % starts.size())
	for i in starts.size():
		assert_eq(str(starts[i]["node"]), "ward", "phase_start %d is the same node" % i)
		if i > 0:
			assert_near(float(starts[i]["t"]) - float(starts[i - 1]["t"]), 64.0 * BEAT, 1e-6, "phase starts are exactly 64 beats apart")
	assert_near(float(starts[0]["t"]) - down, 64.0 * BEAT, 1e-6, "the first boundary after the seat is a whole phase later")
	assert_eq(_events(scene, "hotspot_commit").size(), commits0, "no hotspot committed while seated")
	assert_eq(scene.journey_log.size(), jlog0, "no journey action while seated")
	assert_eq(scene.journey.log.size(), rail0, "the rail took no step")
	assert_true(scene.engine.level.notes.size() > notes0 + 30, "cues keep being charted")
	var blocks := fresh.filter(func(e: Dictionary) -> bool: return str(e["kind"]) == "block_result")
	assert_true(blocks.size() >= 12, "block results keep arriving (%d)" % blocks.size())
	assert_true(blocks.any(func(e: Dictionary) -> bool: return bool(e["passed"])) and blocks.any(func(e: Dictionary) -> bool: return not bool(e["passed"])), "the bot's hits and misses are both judged")
	var en: Array = blocks.map(func(e: Dictionary) -> float: return float(e["energy"]))
	assert_true(en.max() - en.min() > 1.0, "energy keeps changing (%s)" % str(en))
	assert_eq(_mg(scene).state, "active", "never fell: passes and misses alternate")
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward"], "the second phase is the day room again")
	_free(d)


# ---- 6: pads and cards are independent -----------------------------------------------------------------------------------------------------

func _session(bot: String, seed: int, hands: int) -> Dictionary:
	var d := _scene(bot, seed)
	var scene: Node = d["scene"]
	_sit(scene)
	var ctx := _ctx("mix")
	_until(scene, ctx, func() -> bool: return (ctx["hands"] as Array).size() >= hands, 200.0)
	var out := {"hands": ctx["hands"], "balance": _wallet().balance_pence(), "viol": ctx["viol"], "wobble": int(_snap(scene).get("wobble", {}).get("level", 0)), "state": _mg(scene).state}
	_free(d)
	return out


func test_the_pads_never_change_the_cards_or_the_money() -> void:
	var a := _session("perfect", 11, 3)
	var b := _session(_pattern("01".repeat(30)), 11, 3)
	assert_eq((a["hands"] as Array).size(), 3)
	assert_eq(a["viol"], [])
	assert_eq(b["viol"], [])
	assert_eq(int(b["wobble"]), 0, "the missing run never wobbled (no two misses in a row)")
	assert_eq(b["state"], "active")
	assert_eq(a["hands"], b["hands"], "identical cards, results and money hand by hand")
	assert_eq(a["balance"], b["balance"], "identical balance")


# ---- 7: wobble and fall --------------------------------------------------------------------------------------------------------------------

func test_two_failed_blocks_wobble_a_pass_steadies_and_three_make_the_player_fall() -> void:
	var d := _scene(_pattern("00" + "1" + "000" + "0".repeat(20)))
	var scene: Node = d["scene"]
	scene.engine.energy = 100.0
	var down := _sit(scene)
	var mg := _mg(scene)
	var w := _wallet()
	var ctx := _ctx("stick")
	ctx["max_hands"] = 1
	var seen: Array = []  # [passed, wobble level after] per block result since the seat
	var counted := 0
	var fell := false
	var bal_pre := 0
	var held_pre := 0
	var staked := false
	var after_hand := 0
	var guard := 0
	while mg.state != "" and guard < 6000:
		guard += 1
		var in_hand: bool = not staked and (ctx["hands"] as Array).size() >= 1 and _phase(scene) == "await_bet"
		if in_hand:
			ctx["play"] = false
			assert_true(mg.tap("bet", scene._vt), "the second hand's stake is placed")
			staked = true
			after_hand = int((ctx["hands"] as Array)[0]["bal_after"])
			assert_eq(w.balance_pence(), after_hand - 500, "second stake held")
		bal_pre = w.balance_pence()
		held_pre = w.held_pence()
		_frame(scene, ctx)
		var results := _events(scene, "block_result").filter(func(e: Dictionary) -> bool: return float(e["t"]) >= down)
		while counted < results.size():
			var lvl := int(_snap(scene).get("wobble", {}).get("level", -1)) if mg.state != "" else -1
			seen.append([bool(results[counted]["passed"]), lvl, mg.state])
			counted += 1
		if mg.state == "" and not fell:
			fell = true
			assert_eq(w.held_pence(), 0, "the hold is released")
			assert_eq(w.balance_pence() + w.held_pence(), bal_pre + held_pre, "balance and held are conserved across the fall")
			assert_eq(w.balance_pence(), after_hand, "the live stake came back exactly once: earlier results kept, the second stake refunded")
	assert_true(fell, "the player fell")
	assert_eq(ctx["viol"], [])
	assert_true(seen.size() >= 6, "six block results since the seat (%s)" % str(seen))
	assert_eq(seen[0].slice(0, 2), [false, 0], "one miss: steady")
	assert_eq(seen[1].slice(0, 2), [false, 1], "two misses in a row: wobble level 1")
	assert_eq(seen[2].slice(0, 2), [true, 0], "a pass: back to 0")
	assert_eq(seen[3].slice(0, 2), [false, 0])
	assert_eq(seen[4].slice(0, 2), [false, 1])
	assert_false(bool(seen[5][0]), "the third miss in a row")
	assert_eq(_log(scene, "interrupt").map(func(e: Dictionary) -> String: return str(e["reason"])), ["fall"], "one interrupt, a fall")
	assert_eq(_log(scene, "finished").map(func(e: Dictionary) -> String: return str(e["reason"])), ["fall"])
	assert_false(scene.engine.hold, "the hold is released")
	assert_false(scene.hud.silent)
	assert_true(_events(scene, "run_over").is_empty(), "the run is not over merely because of the fall")
	_run_to(scene, float(scene._vt) + 70.0 * BEAT)
	assert_true(_nodes(scene).size() > 3, "later phases are routed")
	assert_true(_nodes(scene).has("ward.art"), "the adventure carries on by the default exit: %s" % str(_nodes(scene)))
	_free(d)


# ---- 8: leaving and sitting again ------------------------------------------------------------------------------------------------------------

func test_leaving_keeps_the_wallet_forfeits_a_live_hand_and_the_table_can_be_sat_at_again() -> void:
	var seed := _seed_where(func(h: Dictionary) -> bool: return not bool(h["natural"]) and str(h["result"]) in ["win", "lose", "bust"])
	assert_true(seed > 0, "a seed with a plain first hand exists")
	var d := _scene("perfect", seed)
	var scene: Node = d["scene"]
	var w := _wallet()
	_sit(scene)
	var mg := _mg(scene)
	var ctx := _ctx("stick")
	ctx["max_hands"] = 1
	assert_true(_until(scene, ctx, func() -> bool: return (ctx["hands"] as Array).size() >= 1 and _phase(scene) == "await_bet", 120.0), "one hand played and the dealer waits again")
	var kept: int = w.balance_pence()
	assert_true(kept != 2000, "the hand moved the money")
	assert_eq(kept, int((ctx["hands"] as Array)[0]["bal_after"]))
	assert_true(mg.tap("exit", scene._vt), "the exit between hands")
	assert_eq(_phase(scene), "leaving")
	var t_leave: float = scene._vt
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return mg.state == "", 8.0), "left")
	assert_eq(_log(scene, "finished").map(func(e: Dictionary) -> String: return str(e["reason"])), ["left"])
	assert_eq(w.balance_pence(), kept, "leaving between hands keeps the wallet")
	assert_eq(w.held_pence(), 0)
	assert_false(scene.engine.hold)
	var back: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_walk" and float(a["t0"]) >= t_leave and str((a["args"] as Dictionary).get("to", "")) == "day_door_a")
	assert_false(back.is_empty(), "the camera walks toward the default exit's door (the bare exit is the default door)")
	assert_eq(float(back[0]["args"]["bars"]), 2.0)
	assert_true(scene.engine.phase_beat_at(scene._vt) < 48.0, "still before the final window of this phase")
	_to_beat(scene, 50.0)
	var ids: Array = (scene.hotspot_items() as Array).map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_contains(ids, "ward.cards", "the hotspots show again in the next final window")
	# sit again: the new activity starts from the kept balance
	var down: float = scene.engine.t_of(64.0)
	assert_true(scene.hotspot_select("ward.cards"))
	_run_to(scene, down + 5.0 * BEAT)
	assert_eq(mg.started, 2, "a second activity")
	assert_eq(_phase(scene), "await_bet")
	assert_eq(int(_snap(scene)["pile"]["pence"]), kept, "the pile is the kept balance, not 20 pounds")
	assert_eq(w.balance_pence(), kept)
	# a live hand: the exit forfeits the stake (decision B4)
	var ctx2 := _ctx("stick")
	ctx2["play"] = false
	assert_true(mg.tap("bet", scene._vt))
	assert_true(_until(scene, ctx2, func() -> bool: return _phase(scene) == "player_turn", 30.0), "the player's turn")
	assert_eq(w.held_pence(), 500)
	assert_true(mg.tap("exit", scene._vt), "leaving during the player's turn")
	assert_eq(w.held_pence(), 0, "the stake is settled at once")
	assert_eq(w.balance_pence(), kept - 500, "and forfeited, not refunded")
	assert_true(_until(scene, ctx2, func() -> bool: return mg.state == "", 8.0))
	assert_eq(w.balance_pence(), kept - 500)
	assert_eq(_log(scene, "finished").map(func(e: Dictionary) -> String: return str(e["reason"])), ["left", "left"])
	assert_eq(ctx2["viol"], [])
	_free(d)


# ---- 9: broke ---------------------------------------------------------------------------------------------------------------------------------

func test_a_player_without_the_stake_is_broke_and_can_only_leave() -> void:
	# a wallet of 3 pounds: broke from the first moment
	var d := _scene()
	var scene: Node = d["scene"]
	var w := _wallet()
	assert_true(w.spend(1700))
	_sit(scene)
	_run_to(scene, float(scene._vt) + 5.0 * BEAT)
	var s := _snap(scene)
	assert_eq(str(s["phase"]), "broke")
	assert_eq(s["targets"], ["exit:ward.art", "exit:ward.dorm"], "only the room's doors are targets")
	assert_true(bool(s["hints"]["exit_urged"]))
	assert_false(_mg(scene).tap("bet", scene._vt), "a bet is refused")
	assert_eq(w.balance_pence(), 300)
	assert_eq(w.held_pence(), 0)
	_free(d)
	# a wallet of exactly one stake and a hand that loses it
	var seed := _seed_where(func(h: Dictionary) -> bool: return str(h["result"]) in ["lose", "bust"])
	assert_true(seed > 0, "a losing first hand exists")
	d = _scene("perfect", seed)
	scene = d["scene"]
	w = _wallet()
	assert_true(w.spend(1500))
	_sit(scene)
	var ctx := _ctx("stick")
	assert_true(_until(scene, ctx, func() -> bool: return _phase(scene) == "broke", 120.0), "the lost stake leaves the player broke")
	assert_eq(w.balance_pence(), 0)
	assert_eq(w.held_pence(), 0)
	s = _snap(scene)
	assert_eq(s["targets"], ["exit:ward.art", "exit:ward.dorm"])
	assert_false(_mg(scene).tap("bet", scene._vt), "a bet is refused")
	assert_eq(w.balance_pence(), 0)
	assert_eq(ctx["viol"], [])
	assert_true(_mg(scene).tap("exit", scene._vt), "the exit works")
	_free(d)


# ---- 10: rapid taps ------------------------------------------------------------------------------------------------------------------------------

func test_rapid_repeated_taps_change_money_only_by_the_rules() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var w := _wallet()
	_sit(scene)
	var mg := _mg(scene)
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return _phase(scene) == "await_bet", 20.0))
	var trail: Array = [[w.balance_pence(), w.held_pence()]]
	var oks := 0
	for i in 5:  # the same target five times in one frame
		if mg.tap("bet", scene._vt):
			oks += 1
	assert_eq(oks, 1, "only the first of five bets is taken")
	assert_eq([w.balance_pence(), w.held_pence()], [1500, 500])
	# every target every frame, junk too, until the hand is settled
	var settled := false
	var frames := 0
	while not settled and frames < 6000:
		frames += 1
		for tgt in ["bet", "deck", "hand", "deck", "bet", "zzz", ""]:
			mg.tap(tgt, scene._vt)
		_frame(scene, ctx)
		var st := [w.balance_pence(), w.held_pence()]
		if st != trail.back():
			trail.append(st)
		var s := _snap(scene)
		settled = str(s["phase"]) == "settling" and str(s["seats"]["player"]["result"]) != ""
		if settled:
			var ex := _expected(s)
			assert_eq(w.balance_pence(), 1500 + int(ex["payout"]), "settled by the rules for a %s" % str(ex["result"]))
	assert_true(settled)
	assert_eq(trail[0], [2000, 0])
	assert_eq(trail[1], [1500, 500])
	assert_eq(trail.size(), 3, "exactly one hold and one settlement: %s" % str(trail))
	assert_eq(w.held_pence(), 0)
	assert_eq(ctx["viol"], [])
	var total_after := w.balance_pence()
	# the exit hammered in one frame leaves once and moves no money
	for i in 4:
		mg.tap("exit", scene._vt)
	assert_eq(_log(scene, "tap").filter(func(e: Dictionary) -> bool: return str(e["target"]) == "exit" and bool(e["ok"])).size(), 1, "one exit was taken")
	_run_to(scene, float(scene._vt) + 5.0 * BEAT)
	assert_eq(w.balance_pence(), total_after)
	assert_eq(mg.state, "")
	_free(d)


# ---- 11: the run ends ------------------------------------------------------------------------------------------------------------------------

func test_the_run_ending_at_the_table_refunds_a_live_stake_once() -> void:
	var d := _scene(_pattern("0".repeat(40)))
	var scene: Node = d["scene"]
	var w := _wallet()
	_sit(scene)
	var mg := _mg(scene)
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return _phase(scene) == "await_bet", 20.0))
	assert_true(mg.tap("bet", scene._vt))
	assert_true(_until(scene, ctx, func() -> bool: return _phase(scene) == "player_turn", 30.0))
	assert_eq([w.balance_pence(), w.held_pence()], [1500, 500], "a live stake")
	scene.engine.energy = 1.0
	assert_true(_until(scene, ctx, func() -> bool: return not _events(scene, "run_over").is_empty() or mg.state == "", 80.0), "the crowd left")
	assert_false(_events(scene, "run_over").is_empty(), "the run is over")
	assert_eq(_log(scene, "interrupt").map(func(e: Dictionary) -> String: return str(e["reason"])), ["run_over"], "interrupted once, by the run ending")
	assert_eq([w.balance_pence(), w.held_pence()], [2000, 0], "the stake was refunded, once")
	assert_eq(ctx["viol"], [])
	_free(d)


# ---- 12: a run that never touches the table ----------------------------------------------------------------------------------------------------

func test_a_run_through_the_day_room_that_ignores_the_table_is_unaffected() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 200.0 * BEAT)
	assert_eq(_mg(scene).log, [], "no minigame ever started")
	assert_eq(_mg(scene).state, "")
	assert_false(scene.engine.hold)
	assert_false(scene.hud.silent)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"], "the default exit, as ever")
	assert_eq(_wallet().balance_pence(), 2000)
	assert_eq(_wallet().held_pence(), 0)
	assert_true((scene.hotspot_log as Array).all(func(e: Dictionary) -> bool: return str(e["kind"]) != "minigame_tap"))
	_free(d)


# ---- 13: determinism ----------------------------------------------------------------------------------------------------------------------------

func _scripted(step: float) -> Dictionary:
	var d := _scene("perfect", 5, "bet@5,deck@12,hand@16,exit@40")
	var scene: Node = d["scene"]
	_to_beat_step(scene, 50.0, step)
	scene.hotspot_select("ward.cards")
	_run_to(scene, scene.engine.t_of(64.0) + 48.0 * BEAT, step)
	var log := (_mg(scene).log as Array).map(func(e: Dictionary) -> String: return "%s:%s:%s" % [str(e["kind"]), str(e.get("target", e.get("reason", ""))), str(e.get("ok", ""))])
	var times := (_mg(scene).log as Array).map(func(e: Dictionary) -> float: return float(e["t"]))
	var out := {"log": log, "times": times, "balance": _wallet().balance_pence(), "held": _wallet().held_pence(), "started": _mg(scene).started}
	_free(d)
	return out


func _to_beat_step(scene: Node, beat: float, step: float) -> void:
	_run_to(scene, scene.engine.t_of(beat), step)


func test_the_same_scripted_run_gives_the_same_log_and_wallet_at_30_and_60_steps_a_second() -> void:
	var a := _scripted(1.0 / 30.0)
	var b := _scripted(1.0 / 60.0)
	assert_true((a["log"] as Array).size() >= 6, "the script played: %s" % str(a["log"]))
	assert_eq(a["log"], b["log"], "the same lifecycle log")
	assert_eq(a["balance"], b["balance"], "the same final wallet")
	assert_eq(a["held"], b["held"])
	for i in (a["times"] as Array).size():
		assert_near(float(a["times"][i]), float(b["times"][i]), 1.0 / 30.0 + 1e-6, "log entry %d lands at the same song time (to a frame)" % i)


# ---- 14: joining at any block, the touch walks the camera to the table -----------------------------------------------------------------------------

func _cam_dist(scene: Node, wp: String) -> float:
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var at: Vector2 = st.map.waypoint(wp)["at"]
	var cam: Vector3 = scene._exit_pose()["cam"]
	return Vector2(cam.x, cam.z).distance_to(at)


func _moves_to(scene: Node, wp: String, from_t := -1.0) -> Array:
	return (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and str((a["args"] as Dictionary).get("to", "")) == wp and float(a["t0"]) >= from_t)


func test_a_touch_in_block_1_seats_the_player_at_the_end_of_that_block_and_the_run_stays_in_the_room() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 20.0)
	assert_true(scene.hotspot_select("ward.cards"), "the table can be touched in block 1")
	_to_beat(scene, 31.0)
	assert_eq(_mg(scene).state, "entering")
	assert_true(scene.engine.hold)
	_to_beat(scene, 32.3)
	assert_eq(_mg(scene).state, "active")
	assert_near(_mg(scene).begin_t, scene.engine.t_of(32.0), 1e-9, "seated at the end of block 1")
	var commit: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")[0]
	assert_eq(str(commit["window"]), "any")
	assert_true(bool(commit["success"]))
	assert_eq(scene.journey.door_target, "", "no door walk started")
	_to_beat(scene, 140.0)
	assert_true(_nodes(scene).size() >= 2 and _nodes(scene).all(func(n: Variant) -> bool: return str(n) == "ward"), "the hold keeps the run in the day room across the phase ends")
	assert_true(scene.engine.hold)
	_free(d)


func test_a_weak_block_between_the_tables_credit_and_the_runs_still_seats_the_player() -> void:
	var d := _scene("none")
	var scene: Node = d["scene"]
	var e: RunEngine = scene.engine
	var pressed := {}
	var released := {}
	var t_end := e.t_of(33.0)
	var t: float = scene._vt
	while t < t_end:  # block 1 played by hand: one cue in three is hit on time, the rest are missed (deterministic)
		t += STEP
		scene._vt = t
		scene._step_virtual(t)
		if scene.hotspots.selected == "" and e.phase_beat_at(t) >= 20.0 and scene._claim_id == "" and e.block == 1:
			scene.hotspot_select("ward.cards")
		var notes: Array = e.level.notes
		for i in range(maxi(notes.size() - 400, 0), notes.size()):
			var n: Dictionary = notes[i]
			if int(n["phase"]) != 1 or int(n["block"]) != 1 or i % 3 != 0:
				continue
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]), int(n["pad"]))
	var res: Dictionary = (_events(scene, "block_result").filter(func(x: Dictionary) -> bool: return int(x["phase"]) == 1 and int(x["block"]) == 1))[0]
	var credit := float(res["credit"])
	var passed := bool(res["passed"])
	assert_true(credit >= 0.25 and credit < 0.6, "the bot's weak block lands between 0.25 and 0.6 (credit %.3f)" % credit)
	assert_false(passed, "the run's own rule fails it")
	assert_true(_mg(scene).state != "", "and the table's lenient rule still seats the player")
	assert_true(bool(((scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit"))[0]["success"]))
	_free(d)


func test_no_pad_input_waves_the_player_off_and_the_table_can_be_touched_again_later_in_the_phase() -> void:
	var d := _scene("none")
	var scene: Node = d["scene"]
	_to_beat(scene, 20.0)
	assert_true(scene.hotspot_select("ward.cards"))
	_to_beat(scene, 30.0)
	var commits: Array = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")
	assert_eq(commits.size(), 1)
	assert_false(bool(commits[0]["success"]), "no input: waved off")
	assert_eq(_mg(scene).log, [], "no activity requested")
	assert_false(scene.engine.hold)
	var ids: Array = (scene.hotspot_items() as Array).filter(func(e: Dictionary) -> bool: return str(e["state"]) == "available").map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_contains(ids, "ward.cards", "still on show after the wave-off")
	_to_beat(scene, 36.0)
	assert_true(scene.hotspot_select("ward.cards"), "touched again later in the phase")
	assert_eq(scene.hotspots.selected, "ward.cards")
	_to_beat(scene, 62.0)
	assert_eq(_nodes(scene), ["ward"], "the scene's default exit is untouched so far")
	_to_beat(scene, 66.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"], "and still commits at the final")
	_free(d)


func test_a_touch_near_the_tables_edge_hits_it_and_every_other_day_room_hotspot_keeps_its_own_centre() -> void:
	var d := _scene("perfect", 7, "", Vector2(844, 390))
	var scene: Node = d["scene"]
	_to_beat(scene, 52.0)
	var items: Array = scene.hotspot_items()
	var stage := Rect2(scene._stage_host.global_position, scene._stage_host.size)
	var st: StoryStage = scene.stages[scene.active_world]["stage"]
	var pose: Dictionary = scene._exit_pose()
	var lay := HotspotView.layout(items, st.map, st.crowds, pose, stage.size)
	var table: Dictionary = {}
	for e in lay:
		if str(e["id"]) == "ward.cards":
			table = e
	assert_false(table.is_empty())
	assert_true(float(table["radius_px"]) >= 110.0 - 0.01, "a 220 px target: %s" % str(table["radius_px"]))
	var w: Vector3 = table["world"]
	for off in [Vector3(1.2, 0, 0), Vector3(-1.2, 0, 0), Vector3(0, 0, -1.2), Vector3(0.9, 0, 0.9)]:
		var pr := StoryProjector.project(Vector3(w.x, float(table["ground_y"]), w.z) + off, pose, stage.size)
		if bool(pr["visible"]) and float(pr["depth"]) > 0.4:
			assert_eq(HotspotView.hit(lay, pr["screen"]), "ward.cards", "a touch %s from the table's middle hits it" % str(off))
	for e in lay:
		assert_eq(HotspotView.hit(lay, e["centre"]), str(e["id"]), "a touch on %s's centre selects it, not the table" % str(e["id"]))
	_free(d)


func test_after_getting_up_mid_phase_the_table_is_on_show_again() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 20.0)
	scene.hotspot_select("ward.cards")
	_to_beat(scene, 38.0)
	var mg := _mg(scene)
	assert_eq(mg.state, "active")
	assert_true(mg.tap("exit", scene._vt), "the exit between hands")
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return mg.state == "", 8.0), "left")
	assert_true(scene.engine.phase_beat_at(scene._vt) < 64.0 and scene.engine.phase_n == 1, "still inside the phase")
	var ids: Array = (scene.hotspot_items() as Array).map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_contains(ids, "ward.cards", "on show again straight away")
	assert_true(scene.hotspot_select("ward.cards"), "and touchable")
	_free(d)


func test_a_touch_at_beat_52_still_sits_at_the_next_phase_start() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var down := _sit(scene)
	assert_near(_mg(scene).begin_t, down, 1e-9)
	_free(d)


func test_the_touch_walks_the_camera_to_the_table_at_once_and_the_rail_stands_still() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	var home := str(scene.data.nodes["ward"]["waypoint"])
	_to_beat(scene, 6.0)
	var before := _cam_dist(scene, "day_cards")
	var rail_log: int = scene.journey.log.size()
	var t_touch: float = scene._vt
	assert_true(scene.hotspot_select("ward.cards"))
	assert_eq(_moves_to(scene, "day_cards", t_touch - 0.001).size(), 1, "the walk is scheduled by the touch itself")
	_run_to(scene, t_touch + 0.2)
	assert_true(_cam_dist(scene, "day_cards") < before - 0.05, "the camera is under way within a few frames (%.2f -> %.2f)" % [before, _cam_dist(scene, "day_cards")])
	_to_beat(scene, 14.5)
	assert_true(_cam_dist(scene, "day_cards") < 0.3, "arrived and standing at the table before the next decision: %.2f" % _cam_dist(scene, "day_cards"))
	assert_eq(scene.journey.log.size(), rail_log, "the rail made no step meanwhile (no block decision reached it)")
	assert_true(_moves_to(scene, home, t_touch).is_empty(), "nothing walked the camera home")
	_to_beat(scene, 16.5)
	assert_eq(_mg(scene).state, "active", "seated at the block end")
	assert_eq(_moves_to(scene, "day_cards", t_touch - 0.001).size(), 1, "the sit cinematic added no second walk")
	assert_true(_cam_dist(scene, "day_cards") < 0.3, "no snap away")
	assert_eq(scene.journey.door_target, "")
	scene.hotspot_select("ward.cards")
	assert_eq(_moves_to(scene, "day_cards", t_touch - 0.001).size(), 1, "a repeat touch does not restart the walk")
	_free(d)


func test_a_repeat_touch_keeps_the_claim_and_does_not_restart_the_walk_or_the_burst() -> void:
	var d := _scene("none")
	var scene: Node = d["scene"]
	_to_beat(scene, 6.0)
	scene.hotspot_select("ward.cards")
	var t_state: float = scene._sel_t["ward.cards"]
	_to_beat(scene, 8.0)
	assert_true(scene.hotspot_select("ward.cards"))
	assert_near(float(scene._sel_t["ward.cards"]), t_state, 1e-9, "the burst keeps its start")
	assert_eq(_moves_to(scene, "day_cards").size(), 1)
	_free(d)


func test_a_wave_off_gives_the_camera_back_to_the_rail_and_the_table_stays_on_show() -> void:
	var d := _scene("none")
	var scene: Node = d["scene"]
	var home := str(scene.data.nodes["ward"]["waypoint"])
	_to_beat(scene, 6.0)
	scene.hotspot_select("ward.cards")
	var d0 := _cam_dist(scene, "day_cards")
	_to_beat(scene, 12.0)
	assert_true(_cam_dist(scene, "day_cards") < d0 - 0.5, "under way to the table before the decision")
	_to_beat(scene, 13.5)
	var commit: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit")[0]
	assert_false(bool(commit["success"]))
	assert_false(_moves_to(scene, home, float(commit["t"]) - 0.001).is_empty(), "the camera walks back to the room's home")
	_to_beat(scene, 24.0)
	assert_true(_cam_dist(scene, home) < 0.5, "and is there: %.2f" % _cam_dist(scene, home))
	var ids: Array = (scene.hotspot_items() as Array).map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_contains(ids, "ward.cards")
	_free(d)


func test_touching_another_hotspot_after_the_table_restores_the_normal_progression() -> void:
	var d := _scene("perfect")
	var scene: Node = d["scene"]
	var home := str(scene.data.nodes["ward"]["waypoint"])
	_to_beat(scene, 49.5)
	var d0 := _cam_dist(scene, "day_cards")
	scene.hotspot_select("ward.cards")
	_to_beat(scene, 55.0)
	assert_true(_cam_dist(scene, "day_cards") < d0 - 0.5, "walking to the table")
	var t_sel: float = scene._vt
	assert_true(scene.hotspot_select("ward.exit_art"))
	assert_false(_moves_to(scene, home, t_sel - 0.001).is_empty(), "the camera goes back")
	assert_eq(scene._claim_id, "")
	var rail_log: int = scene.journey.log.size()
	_to_beat(scene, 62.0)
	assert_true(scene.journey.log.size() > rail_log, "the rail steps at the last decision again")
	_free(d)


func test_a_failed_last_block_after_touching_the_table_still_leaves_by_the_default_exit() -> void:
	var d := _scene("blocks:1110")
	var scene: Node = d["scene"]
	_to_beat(scene, 49.5)
	scene.hotspot_select("ward.cards")
	_to_beat(scene, 60.3)
	assert_eq(scene.journey.door_target, "", "the door walk does not start while the table is selected")
	_to_beat(scene, 62.0)
	assert_eq(scene.journey.door_target, "ward.art", "the door walk starts from wherever the camera stands")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"])
	_free(d)


func test_getting_up_in_the_phase_the_player_sat_down_in_still_walks_to_the_door_and_moves_on() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 6.0)
	assert_true(scene.hotspot_select("ward.cards"), "touched in block 0")
	_to_beat(scene, 20.0)
	var mg := _mg(scene)
	assert_eq(mg.state, "active", "seated at beat 16")
	assert_true(mg.tap("exit", scene._vt), "the exit between hands")
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return mg.state == "", 8.0), "left")
	assert_true(scene.engine.phase_n == 1 and scene.engine.phase_beat_at(scene._vt) < 50.0, "still inside the first phase, well before the door")
	_to_beat(scene, 62.0)
	assert_eq(scene.journey.door_target, "ward.art", "the door walk starts at beat 61 although the player sat down in this phase")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"], "the run moves on")
	_free(d)


func test_getting_up_after_the_route_lock_of_a_held_phase_keeps_the_run_in_the_day_room() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_to_beat(scene, 6.0)
	scene.hotspot_select("ward.cards")
	_to_beat(scene, 20.0)
	var mg := _mg(scene)
	assert_eq(mg.state, "active")
	_to_beat(scene, 50.0)
	_to_beat(scene, 62.0)  # past the route lock (beat 60.5) of the phase the player sat down in
	assert_true(scene.engine.hold and scene.engine.phase_n == 1, "still seated in the first phase after the lock")
	assert_true(mg.tap("exit", scene._vt), "the exit between hands")
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return mg.state == "", 8.0), "left")
	assert_eq(scene.journey.door_target, "", "no door walk: the route was locked to the day room")
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward"], "the next phase is the day room again")
	_free(d)


# ---- 15: exits while seated: each door of the room is a door at the table, and touching one sends you that way ---------------------------------------

## Sits in block 0 of the first phase (touched at beat 6, seated at beat 16) and runs to beat 18.
func _sit_early(scene: Node) -> void:
	_to_beat(scene, 6.0)
	assert_true(scene.hotspot_select("ward.cards"), "the table touched in block 0")
	_to_beat(scene, 18.0)
	assert_eq(_mg(scene).state, "active", "seated at beat 16")


## Touches `target` at the table and runs until the player is up. Returns the song time of the touch.
func _leave_by(scene: Node, target: String) -> float:
	var mg := _mg(scene)
	var t: float = scene._vt
	assert_true(mg.tap(target, t), "%s taken" % target)
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return mg.state == "", 8.0), "up after %s" % target)
	return t


func _walks_to(scene: Node, wp: String, from_t: float) -> Array:
	return (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_walk" and str((a["args"] as Dictionary).get("to", "")) == wp and float(a["t0"]) >= from_t)


func test_the_rooms_exits_are_doors_at_the_table_each_its_own_target() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 22.0)
	var s := _snap(scene)
	assert_eq(str(s["phase"]), "await_bet")
	assert_eq(s["targets"], ["bet", "exit:ward.art", "exit:ward.dorm"], "one target per door")
	var ex: Array = s["exits"]
	assert_eq(ex.map(func(e: Dictionary) -> String: return str(e["id"])), ["ward.exit_art", "ward.exit_dorm"], "the day room's exits, the default first")
	assert_eq(ex.map(func(e: Dictionary) -> String: return str(e["scene"])), ["art", "dorm"], "where each leads")
	assert_eq(ex.map(func(e: Dictionary) -> String: return str(e["dir"])), ["right", "up"])
	assert_true(str(ex[0]["tint"]) != "" and str(ex[1]["tint"]) != "", "the destinations' colours come from the map")
	assert_true(str(ex[0]["tint"]) != str(ex[1]["tint"]), "and differ")
	# the view draws a door for each and hit-tests it
	var view: Control = scene._mg.view
	assert_true(view is BlackjackView, "the table's view is mounted")
	var rects: Dictionary = view.target_rects()
	assert_true(rects.has("exit:ward.art") and rects.has("exit:ward.dorm"), "both doors are live")
	var host: Control = scene._stage_host
	var cv: Vector2 = view.size
	for id in ["exit:ward.art", "exit:ward.dorm"]:
		var c: Vector2 = (rects[id] as Rect2).get_center()
		var local := Vector2(c.x * host.size.x / cv.x, c.y * host.size.y / cv.y)
		assert_eq(scene._mg.hit(local, host.size), id, "a touch on the %s door hits it" % id)
	_free(d)


func test_leaving_by_the_dormitory_door_before_the_window_arms_it_walks_there_and_the_run_goes_to_the_dormitory() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 20.0)
	var t_leave := _leave_by(scene, "exit:ward.dorm")
	assert_eq((_log(scene, "leave") as Array)[0]["route"], "ward.dorm", "the controller logs the route")
	assert_eq(scene._mg.pending_exit, "ward.exit_dorm", "the dormitory door waits for the window")
	assert_eq(scene.hotspots.selected, "", "not on show yet: nothing selected")
	var walk := _walks_to(scene, "day_door_b", t_leave)
	assert_eq(walk.size(), 1, "the camera walks toward the dormitory's door, not home")
	assert_true(_moves_to(scene, "day_centre", t_leave).is_empty(), "nothing walks it home")
	var before := _cam_dist(scene, "day_door_b")
	_to_beat(scene, 40.0)
	assert_true(_cam_dist(scene, "day_door_b") < before - 0.5, "nearer the door (%.2f -> %.2f)" % [before, _cam_dist(scene, "day_door_b")])
	assert_true(absf(_cam_dist(scene, "day_door_b") - RunMinigameHost.DOOR_STOP_M) < 0.3, "standing before it: %.2f" % _cam_dist(scene, "day_door_b"))
	var rail_log: int = scene.journey.log.size()
	_to_beat(scene, 48.2)
	assert_eq(scene.hotspots.selected, "ward.exit_dorm", "selected as soon as it is on show")
	var items: Array = (scene.hotspot_items() as Array).filter(func(e: Dictionary) -> bool: return str(e["hotspot"]["id"]) == "ward.exit_dorm")
	assert_eq(str(items[0]["state"]), "selected", "the normal selected look")
	var sel: Array = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "select" and e["hotspot"] == "ward.exit_dorm")
	assert_eq(sel.size(), 1, "logged as a touch is")
	assert_true(scene.engine.phase_beat_at(float(sel[0]["t"])) < 48.2)
	_to_beat(scene, 60.3)
	assert_eq(scene.journey.log.size(), rail_log, "the camera waited by the door: no rail step")
	_to_beat(scene, 62.0)
	assert_eq(scene.journey.door_target, "ward.dorm", "the door walk at beat 61 goes through it")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.dorm"], "the run is in the dormitory")
	assert_eq(scene._mg.pending_exit, "")
	assert_eq(scene._mg.armed_exit, "", "used up")
	_free(d)


func test_leaving_by_the_art_room_door_goes_to_the_art_room() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 20.0)
	var t_leave := _leave_by(scene, "exit:ward.art")
	assert_eq(scene._mg.pending_exit, "ward.exit_art")
	assert_eq(_walks_to(scene, "day_door_a", t_leave).size(), 1, "toward the art room's door")
	_to_beat(scene, 50.0)
	assert_eq(scene.hotspots.selected, "ward.exit_art")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"])
	_free(d)


func test_the_bare_exit_tap_is_the_default_door() -> void:
	var d := _scene("perfect", 7, "exit@4")
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 24.0)
	assert_eq(_mg(scene).state, "", "up after the scripted bare exit")
	assert_eq(_mg(scene).last_route, "ward.art", "the default exit's route")
	assert_eq(scene._mg.pending_exit, "ward.exit_art")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"])
	_free(d)


func test_a_scripted_door_tap_names_its_route() -> void:
	var d := _scene("perfect", 7, "exit:ward.dorm@4")
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 24.0)
	assert_eq(_mg(scene).last_route, "ward.dorm")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.dorm"])
	_free(d)


func test_touching_the_other_exit_in_the_room_wins_over_the_door_taken_at_the_table() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 20.0)
	_leave_by(scene, "exit:ward.dorm")
	_to_beat(scene, 50.0)
	assert_eq(scene.hotspots.selected, "ward.exit_dorm")
	assert_true(scene.hotspot_select("ward.exit_art"), "the player touches the art room's door in the room")
	_to_beat(scene, 51.0)
	assert_eq(scene.hotspots.selected, "ward.exit_art", "and it stays: the pending door does not take it back")
	assert_eq(scene._mg.armed_exit, "")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"], "the other door won")
	_free(d)


func test_touching_the_table_again_seats_the_player_and_the_pending_door_is_gone() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 20.0)
	_leave_by(scene, "exit:ward.dorm")
	_to_beat(scene, 26.0)
	assert_eq(scene._mg.pending_exit, "ward.exit_dorm")
	assert_true(scene.hotspot_select("ward.cards"), "the table again, in block 1")
	_to_beat(scene, 27.0)
	assert_eq(scene._mg.pending_exit, "", "replaced by the touch")
	assert_true((scene.hotspot_log as Array).any(func(e: Dictionary) -> bool: return e["kind"] == "exit_dropped" and e["why"] == "replaced"))
	_to_beat(scene, 33.0)
	assert_eq(_mg(scene).state, "active", "seated again at the end of block 1")
	assert_eq(_mg(scene).started, 2)
	_to_beat(scene, 50.0)
	assert_eq(scene.hotspots.selected, "", "no door is selected for the seated player")
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward"], "held in the day room")
	_free(d)


func test_leaving_by_a_door_after_the_route_lock_stays_one_more_phase_then_goes_that_way() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 62.0)
	assert_true(scene.engine.hold, "still seated after the lock")
	var down: float = scene.engine.t_of(64.0)
	_leave_by(scene, "exit:ward.dorm")
	assert_eq(scene.journey.door_target, "", "no door walk: the route was locked to the day room")
	assert_eq(scene._mg.pending_exit, "ward.exit_dorm", "kept for the next phase")
	_run_to(scene, maxf(down + 0.1, float(scene._vt)))
	assert_eq(scene.engine.phase_n, 2)
	assert_true(scene.engine.phase_beat_at(scene._vt) < 40.0, "early in the next phase")
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward"], "one more phase in the day room")
	assert_eq(scene._mg.pending_exit, "ward.exit_dorm", "still pending in the same room")
	_to_beat(scene, 48.5)
	assert_eq(scene.hotspots.selected, "ward.exit_dorm", "selected when that phase's window opens")
	_run_to(scene, scene.engine.t_of(64.0) + 4.0 * BEAT)
	assert_eq(_nodes(scene).slice(0, 3), ["ward", "ward", "ward.dorm"], "then out by the chosen door")
	_free(d)


func test_a_failed_last_block_after_leaving_by_a_door_follows_that_doors_failure() -> void:
	var d := _scene("blocks:1110")
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 20.0)
	_leave_by(scene, "exit:ward.dorm")
	_to_beat(scene, 62.0)
	var commit: Dictionary = (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "commit" and e["hotspot"] == "ward.exit_dorm")[0]
	assert_false(bool(commit["success"]), "the last block failed")
	var h: Dictionary = scene.hotspots.get_hotspot("ward.exit_dorm")
	assert_eq(str(commit["route"]), str(h["on_failure"]["route"]), "that exit's on_failure route")
	var out: Dictionary = (_events(scene, "hotspot_commit").filter(func(e: Dictionary) -> bool: return str(e["outcome"]["hotspot"]) == "ward.exit_dorm"))[0]["outcome"]
	assert_eq(str(out["cinematic_name"]), str(h["on_failure"]["cinematic"]), "with its stagger")
	assert_near(float(out["energy"]), float(h["on_failure"]["energy"]), 1e-9)
	_to_beat(scene, 68.0)
	assert_eq(_nodes(scene).slice(0, 2), ["ward", str(h["on_failure"]["route"])])
	_free(d)


func test_the_run_ending_clears_a_pending_door_and_a_door_taken_while_the_run_ends_is_not_carried_out() -> void:
	# a pending door, then the crowd leaves before the window opens
	var d := _scene(_pattern("0".repeat(40)).replace("blocks:1111", "blocks:1"))
	var scene: Node = d["scene"]
	_sit_early(scene)
	_to_beat(scene, 20.0)
	_leave_by(scene, "exit:ward.dorm")
	assert_eq(scene._mg.pending_exit, "ward.exit_dorm")
	scene.engine.energy = 1.0
	_to_beat(scene, 30.0)
	assert_false(_events(scene, "depleted").is_empty(), "the crowd is leaving")
	assert_eq(scene._mg.pending_exit, "", "the pending door is dropped")
	assert_true((scene.hotspot_log as Array).any(func(e: Dictionary) -> bool: return e["kind"] == "exit_dropped" and e["why"] == "gone"))
	_run_to(scene, float(scene._vt) + 20.0 * BEAT)
	assert_false(_events(scene, "run_over").is_empty())
	assert_eq(scene.hotspots.selected, "", "nothing selected")
	_free(d)
	# a door touched while the run is ending: the player gets up, nothing is carried out
	d = _scene(_pattern("0".repeat(40)))
	scene = d["scene"]
	var w := _wallet()
	_sit(scene)
	var mg := _mg(scene)
	var ctx := _ctx("stick")
	ctx["play"] = false
	assert_true(_until(scene, ctx, func() -> bool: return _phase(scene) == "await_bet", 20.0))
	assert_true(mg.tap("bet", scene._vt))
	scene.engine.energy = 1.0
	assert_true(_until(scene, ctx, func() -> bool: return not _events(scene, "depleted").is_empty(), 40.0), "the crowd is leaving")
	assert_true(mg.tap("exit:ward.dorm", scene._vt), "a door while the run ends")
	assert_true(_until(scene, ctx, func() -> bool: return mg.state == "" and not _events(scene, "run_over").is_empty(), 40.0))
	assert_eq(scene._mg.pending_exit, "", "nothing pending")
	assert_eq(scene._mg.armed_exit, "")
	assert_false((scene.hotspot_log as Array).any(func(e: Dictionary) -> bool: return e["kind"] == "exit_pending"), "never carried out")
	assert_eq(w.held_pence(), 0, "no stake left held")
	assert_false(scene.engine.hold)
	_free(d)


func test_with_the_table_never_touched_the_doors_change_nothing() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 140.0 * BEAT)
	assert_eq(scene._mg.pending_exit, "")
	assert_false((scene.hotspot_log as Array).any(func(e: Dictionary) -> bool: return str(e["kind"]).begins_with("exit_")), "no exit bookkeeping at all")
	assert_eq(_nodes(scene).slice(0, 2), ["ward", "ward.art"])
	_free(d)
