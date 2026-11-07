extends TestCase
## The bar recipe memory game (bedsit brief section 6): the recipe grows from two ingredients to three after a success, the order is demonstrated then hidden, a correct sequence is served fast and
## counts, a wrong press serves slow and repeats the same order with its demonstration, bounces are ignored, four served drinks complete the bar and set its flag, leaving and returning keeps the
## order, the rhythm is suspended while it is seated (no misses, no energy loss) and judging resumes on the boundary, the pad strip's taps reach the four controls.

const BEAT := 60.0 / 174.0
const CONFIG_PATH := "res://content/minigames/bar.json"
const SCRIPT_PATH := "res://src/minigames/bar/bar_activity.gd"
const TMP_SAVE := "user://test_bar_save.json"

var _saved: RunProgress


func _cfg(extra: Dictionary = {}) -> Dictionary:
	var c: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	c.merge(extra, true)
	return c


## A seated bar activity (theme `theme`, seed `seed`), begun at song time 0.
func _bar(theme := "space", seed := 7, extra: Dictionary = {}, wallet: Variant = null) -> BarActivity:
	var a := BarActivity.new()
	a.setup({"seed": seed, "beat_s": BEAT, "config": _cfg(extra), "wallet": wallet, "request": {"theme": theme}})
	a.begin(0.0)
	return a


## Updates to the start of the input phase; returns that song time.
func _to_input(a: BarActivity) -> float:
	var t := 0.0
	var guard := 0
	while str(a.state()["phase"]) != "input" and guard < 40:
		var s := a.state()
		t = float(s["phase_t0"]) + float(s["phase_dur"]) + 0.001
		a.update(t)
		guard += 1
	return t


## Presses the recipe in order (0.4 s apart) starting at `t`; returns the time after the last press.
func _press_all(a: BarActivity, t: float) -> float:
	for i: Variant in a.recipe():
		assert_true(a.tap("ing:%d" % int(i), t), "press %d accepted" % int(i))
		t += 0.4
	return t


## A wrong press: an ingredient that is not the next one.
func _wrong_press(a: BarActivity, t: float) -> void:
	var s := a.state()
	var want := int((s["recipe"] as Array)[int(s["pos"])])
	assert_true(a.tap("ing:%d" % ((want + 1) % 4), t), "the wrong press is taken")


## Past the serve phase of the last drink: returns the time.
func _past_serve(a: BarActivity) -> float:
	var s := a.state()
	var t := float(s["phase_t0"]) + float(s["phase_dur"]) + 0.001
	a.update(t)
	return t


## Serves one drink correctly from the start of its phases; returns the time after the serve.
func _serve_one(a: BarActivity) -> float:
	var t := _to_input(a)
	t = _press_all(a, t)
	return _past_serve(a)


# --- the game ------------------------------------------------------------------------------------------------------------------

func test_the_recipe_is_two_ingredients_then_three_after_a_success() -> void:
	BarActivity.forget_all()
	var a := _bar()
	assert_eq(a.recipe().size(), 2, "the first drink has two ingredients")
	assert_eq(int(a.state()["len"]), 2)
	_serve_one(a)
	assert_eq(a.served(), 1)
	assert_eq(a.recipe().size(), 3, "three after a success")
	_serve_one(a)
	assert_eq(a.recipe().size(), 3, "and it stays three")
	for r: Variant in a.recipe():
		assert_true(int(r) >= 0 and int(r) < 4, "an ingredient of the four")
	# a recipe is not a run of the same ingredient
	var rec := a.recipe()
	for i in range(1, rec.size()):
		assert_true(int(rec[i]) != int(rec[i - 1]), "no ingredient twice running")


func test_recipes_come_from_the_themes_list_or_are_generated_from_the_four_ingredients_and_the_seed() -> void:
	BarActivity.forget_all()
	var listed := _bar("space", 3)
	var space: Dictionary = BarData.resolve({}, "space")
	assert_eq(space["source"], "themes")
	assert_true((space["recipes"] as Array).has(listed.recipe()), "from the theme's list")
	# no list: generated, and the same seed gives the same recipes
	BarActivity.forget_all()
	var cfg := {"ingredients": [{"id": "a", "color": "#ff0000"}, {"id": "b", "color": "#00ff00"}, {"id": "c", "color": "#0000ff"}, {"id": "d", "color": "#ffff00"}]}
	var g1 := BarActivity.new()
	g1.setup({"seed": 11, "config": _cfg(cfg), "request": {}})
	g1.begin(0.0)
	var d: Dictionary = BarData.resolve(cfg, "")
	assert_eq(d["source"], "config")
	assert_eq((d["recipes"] as Array).size(), 0)
	BarActivity.forget_all()
	var g2 := BarActivity.new()
	g2.setup({"seed": 11, "config": _cfg(cfg), "request": {}})
	assert_eq(g1.recipe(), g2.recipe(), "seeded")
	assert_eq(g1.recipe().size(), 2)


func test_the_order_is_demonstrated_one_ingredient_at_a_time_then_hidden() -> void:
	BarActivity.forget_all()
	var a := _bar()
	var s := a.state()
	assert_eq(s["phase"], "arrive")
	assert_false(bool(s["bubble"]), "no bubble while the customer arrives")
	var t_demo := float(s["phase_t0"]) + float(s["phase_dur"]) + 0.001
	a.update(t_demo)
	s = a.state()
	assert_eq(s["phase"], "demo")
	assert_true(bool(s["bubble"]), "the pictorial order is up")
	assert_eq(int(s["shown"]), 0, "the first ingredient")
	assert_near(float(s["show_s"]), 0.8, 1e-9, "presentation time from the config")
	a.update(t_demo + 0.8)
	assert_eq(int(a.state()["shown"]), 1, "the second after show_s")
	assert_false(a.targets().has("ing:0"), "no presses while it is shown")
	assert_false(a.tap("ing:0", t_demo + 0.9), "a press during the demonstration is not taken")
	a.update(t_demo + 1.6 + 0.01)
	s = a.state()
	assert_eq(s["phase"], "input", "then hidden: the player's turn")
	assert_false(bool(s["bubble"]), "the order is hidden")
	assert_eq(int(s["shown"]), -1)
	assert_true(a.targets().has("ing:0") and a.targets().has("ing:3"), "the four ingredients are live")
	# a different presentation time
	var b := _bar("space", 7, {"show_s_per_ingredient": 0.3})
	var tb := float(b.state()["phase_t0"]) + float(b.state()["phase_dur"]) + 0.001
	b.update(tb + 0.65)
	assert_eq(b.state()["phase"], "input", "two ingredients at 0.3 s each: done after 0.6 s")


func test_a_correct_sequence_serves_fast_and_counts() -> void:
	BarActivity.forget_all()
	var a := _bar()
	var t := _to_input(a)
	var t_after := _press_all(a, t)
	var s := a.state()
	assert_eq(s["phase"], "serve")
	assert_eq(s["outcome"], "happy")
	assert_eq(a.served(), 1, "counted at once")
	assert_near(float(s["phase_dur"]), 1.4, 1e-9, "serve_fast_s")
	assert_eq((s["glass"] as Array).size(), 2, "one layer per ingredient")
	assert_true((s["glass"] as Array).all(func(g: Dictionary) -> bool: return not bool(g["wrong"])))
	assert_eq(int(s["mistakes"]), 0)
	assert_false(a.tap("ing:0", t_after), "no presses while serving")
	var next := _past_serve(a)
	s = a.state()
	assert_eq(s["phase"], "arrive", "the next customer")
	assert_eq((s["glass"] as Array).size(), 0, "a fresh glass")
	assert_true(next > t_after)


func test_a_wrong_press_ends_the_attempt_serves_slow_and_repeats_the_same_order() -> void:
	BarActivity.forget_all()
	var a := _bar()
	var order := a.recipe()
	var t := _to_input(a)
	# one right, then a wrong one
	assert_true(a.tap("ing:%d" % int(order[0]), t))
	t += 0.4
	var want := int(order[1])
	assert_true(a.tap("ing:%d" % ((want + 1) % 4), t))
	var s := a.state()
	assert_eq(s["phase"], "serve")
	assert_eq(s["outcome"], "mistake", "the attempt is over at the wrong press")
	assert_eq(int(s["wrong"]), (want + 1) % 4)
	assert_near(float(s["phase_dur"]), 3.0, 1e-9, "serve_slow_s: slower than the happy handover")
	assert_true(float(s["phase_dur"]) > 1.4)
	assert_eq(a.served(), 0, "not counted")
	assert_true((s["glass"] as Array)[-1]["wrong"], "the wrong layer is in the glass")
	assert_false(a.tap("ing:%d" % want, t + 0.5), "no more presses while the mistake is shown")
	var t2 := _past_serve(a)
	s = a.state()
	assert_eq(s["phase"], "demo", "the demonstration is repeated")
	assert_eq(s["recipe"], order, "the same order")
	assert_eq(int(s["attempt"]), 2)
	assert_true(bool(s["bubble"]))
	assert_eq((s["glass"] as Array).size(), 0, "a fresh glass")
	assert_eq(a.recipe().size(), 2, "still two: no success yet")
	# and it can be got right now
	var t3 := _to_input(a)
	_press_all(a, t3)
	assert_eq(a.state()["outcome"], "happy")
	assert_eq(a.served(), 1)
	assert_true(t3 > t2)
	assert_eq(int(a.state()["mistakes"]), 1)


func test_repeated_presses_within_the_debounce_are_ignored() -> void:
	BarActivity.forget_all()
	var a := _bar()
	var order := a.recipe()
	var t := _to_input(a)
	var id := "ing:%d" % int(order[0])
	assert_true(a.tap(id, t))
	assert_false(a.tap(id, t + 0.05), "a bounce")
	assert_false(a.tap(id, t + 0.2), "a double tap")
	assert_eq(int(a.state()["pos"]), 1, "one step")
	assert_eq(int(a.state()["ignored"]), 2)
	assert_eq(a.state()["phase"], "input", "and not a mistake either")
	assert_true(a.tap("ing:%d" % int(order[1]), t + 0.25), "the next ingredient straight after is fine")
	assert_eq(a.state()["outcome"], "happy")
	# the debounce is configurable
	var b := _bar("space", 7, {"debounce_s": 0.0})
	var tb := _to_input(b)
	var o2 := b.recipe()
	assert_true(b.tap("ing:%d" % int(o2[0]), tb))
	assert_false(b.tap("ing:%d" % int(o2[0]), tb + 0.01), "a second press of the same one is the wrong ingredient now (recipes never repeat): a mistake, not ignored")
	assert_eq(int(b.state()["ignored"]), 0)


func test_four_served_drinks_complete_the_bar_and_set_its_flag() -> void:
	BarActivity.forget_all()
	var a := _bar("magic")
	var t := 0.0
	for k in 3:
		t = _serve_one(a)
		assert_false(a.is_done(), "not yet after %d" % (k + 1))
		assert_eq(a.state()["phase"], "arrive")
	var ti := _to_input(a)
	_press_all(a, ti)
	assert_eq(a.served(), 4)
	var s := a.state()
	assert_eq(s["phase"], "serve")
	assert_false(a.is_done())
	_past_serve(a)
	assert_eq(a.state()["phase"], "payoff", "the last drink gets the payoff")
	assert_false(a.is_done(), "the bartender raises a glass first")
	assert_eq(a.result()["flags_to_set"], [], "no flag before it is done")
	_past_serve(a)
	assert_true(a.is_done())
	assert_eq(a.done_reason(), "done")
	var r := a.result()
	assert_true(bool(r["completed"]))
	assert_eq(r["flags_to_set"], ["rave.magic.bar_done"], "bar_done for the theme")
	assert_eq(int(r["score"]), 4)
	assert_eq(r["activity_id"], "bar")
	assert_true(ContractShapes.activity_result(r).is_empty(), str(ContractShapes.activity_result(r)))
	assert_true(t >= 0.0)
	# a smaller workload is configurable
	BarActivity.forget_all()
	var b := _bar("space", 7, {"drinks_to_serve": 2, "drinks": 2})
	_serve_one(b)
	_serve_one(b)
	_past_serve(b)
	_past_serve(b)
	assert_true(b.is_done(), "two drinks when configured")


func test_leaving_and_coming_back_keeps_the_order() -> void:
	BarActivity.forget_all()
	var w := RunWallet.new()
	var a := _bar("dinos", 5, {}, w)
	_serve_one(a)
	var order := a.recipe()
	assert_eq(order.size(), 3)
	var t := _to_input(a)
	a.tap("ing:%d" % int(order[0]), t)  # half way through
	a.request_leave(t + 1.0)
	assert_true(a.is_done())
	assert_eq(a.done_reason(), "left")
	assert_false(bool(a.result()["completed"]))
	assert_eq(a.result()["flags_to_set"], [], "no flag for leaving")
	# a new activity (another seed, as the controller gives) in the same run and theme
	var b := BarActivity.new()
	b.setup({"seed": 999, "beat_s": BEAT, "config": _cfg(), "wallet": w, "request": {"theme": "dinos"}})
	b.begin(100.0)
	assert_eq(b.served(), 1, "the served count is kept")
	assert_eq(b.recipe(), order, "and the order on the counter")
	assert_eq(b.state()["phase"], "arrive")
	# another theme or another run starts afresh
	var c := BarActivity.new()
	c.setup({"seed": 999, "beat_s": BEAT, "config": _cfg(), "wallet": RunWallet.new(), "request": {"theme": "dinos"}})
	assert_eq(c.served(), 0, "another run: from the start")
	var d := BarActivity.new()
	d.setup({"seed": 999, "beat_s": BEAT, "config": _cfg(), "wallet": w, "request": {"theme": "space"}})
	assert_eq(d.served(), 0, "another rave: from the start")
	# done forgets
	BarActivity.forget_all()


func test_leaving_by_an_exit_door_and_an_interrupt_both_end_it() -> void:
	BarActivity.forget_all()
	var a := BarActivity.new()
	a.setup({"seed": 7, "config": _cfg(), "request": {"theme": "space"}, "exits": [{"id": "x.a", "route": "space.floor"}, {"id": "x.b", "route": "space.cloak"}]})
	a.begin(0.0)
	assert_true(a.targets().has("exit:space.floor") and a.targets().has("exit:space.cloak"))
	assert_true(a.tap("exit:space.cloak", 0.5))
	assert_true(a.is_done())
	assert_eq(a.done_route(), "space.cloak")
	var b := _bar()
	b.interrupt("host", 1.0)
	assert_eq(b.done_reason(), "host")
	assert_eq(b.result()["reason"], "host")


func test_the_controls_are_four_pictures_without_words() -> void:
	var a := _bar("transport")
	var cs := a.controls()
	assert_eq(cs.size(), 4)
	var ids: Array = cs.map(func(c: Dictionary) -> String: return str(c["id"]))
	assert_eq(ids, ["ing:0", "ing:1", "ing:2", "ing:3"])
	var shapes := {}
	var colors := {}
	for c: Dictionary in cs:
		assert_eq(c["label"], "", "no words on the buttons")
		shapes[c["shape"]] = true
		colors[c["color"]] = true
	assert_eq(shapes.size(), 4, "four distinct silhouettes")
	assert_eq(colors.size(), 4, "and four distinct colours")


# --- the content -----------------------------------------------------------------------------------------------------------------

func test_every_theme_has_four_distinct_ingredients_recipes_and_customers() -> void:
	var names := {
		"space": ["nebula_syrup", "comet_ice", "star_dust", "moon_milk"], "magic": ["rainbow_nectar", "unicorn_foam", "glitter_sugar", "dragonfruit"],
		"dinos": ["fern_juice", "lava_sauce", "amber_resin", "egg_cream"], "transport": ["diesel_cola", "tyre_liquorice", "road_salt", "headlamp_lemon"]}
	for th: String in names:
		var d: Dictionary = BarData.resolve({}, th)
		assert_eq(d["source"], "themes", th)
		var got: Array = (d["ingredients"] as Array).map(func(e: Dictionary) -> String: return str(e["id"]))
		assert_eq(got, names[th], th)
		var shapes := {}
		var cols := {}
		for e: Dictionary in d["ingredients"]:
			shapes[e["shape"]] = true
			cols[(e["color"] as Color).to_html(false)] = true
		assert_eq(shapes.size(), 4, "%s: four silhouettes" % th)
		assert_eq(cols.size(), 4, "%s: four colours" % th)
		var by_len := {2: 0, 3: 0}
		for r: Array in d["recipes"]:
			by_len[r.size()] += 1
		assert_true(int(by_len[2]) >= 3 and int(by_len[3]) >= 3, "%s: recipes of both lengths: %s" % [th, str(by_len)])
		assert_true((d["customers"] as Array).size() >= 2)
	# a theme whose list names an unknown ingredient drops that recipe
	assert_eq(BarData.recipe_indices(["a", "zzz"], {"a": 0}), [])
	assert_eq(BarData.recipe_indices(["a", "a"], {"a": 0}), [], "no repeat")
	assert_eq(BarData.recipe_indices(["a", "b", "a"], {"a": 0, "b": 1}), [0, 1, 0])
	assert_eq(BarData.recipe_indices(["a"], {"a": 0}), [], "two or three")


func test_ingredient_sprites_are_64_px_with_a_silhouette_each() -> void:
	var masks := {}
	for shape: String in BarData.SHAPES:
		var img := BarDraw.image(shape, Color("ff8800"))
		assert_eq(img.get_size(), Vector2i(64, 64), shape)
		var n := 0
		var sig := ""
		for y in 64:
			for x in 64:
				if img.get_pixel(x, y).a > 0.5:
					n += 1
					if x % 4 == 0 and y % 4 == 0:
						sig += "1"
				elif x % 4 == 0 and y % 4 == 0:
					sig += "0"
		assert_true(n > 300 and n < 3800, "%s fills a sensible part of the sprite: %d" % [shape, n])
		masks[sig] = true
	assert_eq(masks.size(), BarData.SHAPES.size(), "sixteen distinct silhouettes")
	assert_true(BarDraw.texture("star", Color.RED) == BarDraw.texture("star", Color.RED), "cached")


func test_the_registered_config_agrees_with_the_contract_fixture() -> void:
	var fx: Dictionary = ContractShapes.load_fixture("activity_bar.json")
	var cfg := _cfg()
	for k: String in fx:
		assert_eq(cfg.get(k), fx[k], "bar.json keeps the fixture's %s" % k)
	assert_eq(ActivityMode.of_config(cfg), ActivityMode.Mode.REPLACE)
	var theme: Dictionary = ContractShapes.load_fixture("theme_space.json")
	var req := RunMinigameHost.build_request("bar", cfg, "space", theme, "rave.space", "space_floor")
	assert_true(ContractShapes.activity_request(req).is_empty(), str(ContractShapes.activity_request(req)))
	assert_eq(req["return_pose"], "bar_view")
	assert_eq(req["config"]["flags_on_complete"], ["rave.space.bar_done"])
	# the activity seats with the request and the themes.json content wins over the theme file's own list
	var a := BarActivity.new()
	a.setup({"seed": 1, "config": req["config"], "request": req})
	assert_eq(a.theme(), "space")
	assert_eq(str(a.controls()[0]["icon"]), "nebula_syrup")


func test_no_text_is_drawn_anywhere_in_the_bar() -> void:
	for f: String in ["bar_activity.gd", "bar_view.gd", "bar_draw.gd", "bar_data.gd"]:
		var src := FileAccess.get_file_as_string("res://src/minigames/bar/" + f)
		for bad in ["draw_string", "Label.new", "Button.new", "RichTextLabel", "tooltip_text", "FontFile", "SystemFont"]:
			assert_false(src.contains(bad), "%s has no %s" % [f, bad])


# --- the view --------------------------------------------------------------------------------------------------------------------

func test_the_view_hits_the_four_ingredients_and_the_door_only_when_live() -> void:
	BarActivity.forget_all()
	var a := _bar()
	var clock := {"t": 0.0}
	var v := BarView.new()
	v.size = Vector2(640, 190)
	v.screen_size = Vector2(844, 250)
	v.now_fn = func() -> float: return clock["t"]
	v.state_fn = func() -> Dictionary: return a.state()
	var to_screen := func(p: Vector2) -> Vector2: return p * v.screen_size / v.size
	var rects := v.target_rects()
	assert_false(rects.has("ing:0"), "no ingredient is live while the customer arrives")
	assert_true(rects.has("exit"), "the door always is")
	assert_eq(v.hit(to_screen.call((rects["exit"] as Rect2).get_center())), "exit")
	clock["t"] = _to_input(a)
	rects = v.target_rects()
	for i in 4:
		var id := "ing:%d" % i
		assert_true(rects.has(id))
		assert_eq(v.hit(to_screen.call((rects[id] as Rect2).get_center())), id, "the bottle is a touch target")
	assert_eq(v.hit(to_screen.call(Vector2(250, 40))), "", "nothing in the empty air")
	# a taller or wider view keeps the same canvas, centred
	v.size = Vector2(1000, 190)
	rects = v.target_rects()
	var lay := v.layout()
	assert_near(float((lay["offset"] as Vector2).x), 180.0, 1e-6)
	assert_eq(v.hit(Vector2(v.screen_size.x * 0.5, v.screen_size.y * 0.5)), "", "the middle of the counter is no target")
	v.free()


# --- the engine and the run scene --------------------------------------------------------------------------------------------------

func test_the_controller_seats_the_bar_in_replace_mode_with_four_controls() -> void:
	BarActivity.forget_all()
	var c := MinigameController.new(null)
	c.register("bar", SCRIPT_PATH, _cfg())
	var theme: Dictionary = ContractShapes.load_fixture("theme_space.json")
	var req := RunMinigameHost.build_request("bar", _cfg(), "space", theme, "rave.space", "space_floor")
	assert_true(c.request("bar", 0.0, 1.0, [], req))
	assert_eq(c.mode, ActivityMode.Mode.REPLACE)
	assert_true(c.activity is BarActivity)
	c.update(1.0)
	assert_true(c.owns_strip(1.0), "the ingredients own the strip")
	assert_eq((c.activity.controls() as Array).size(), 4)
	assert_true(c.activity.make_view() is BarView, "its view")
	assert_eq(c.activity.config["flags_on_complete"], ["rave.space.bar_done"])


func _scene(bot: String) -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_MINIGAME_TAPS", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS"]:
		OS.set_environment(k, "")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_in_the_scene_the_bar_replaces_the_pads_costs_no_rhythm_and_resumes_on_the_boundary() -> void:
	BarActivity.forget_all()
	# the bot plays phase 1, nothing in phase 2 and block 0 of phase 3 (the bar owns the strip there), then everything again
	var d := _scene("blocks:1111" + "00000" + "111111111111")
	var scene: Node = d["scene"]
	scene.minigames.register("bar", SCRIPT_PATH, _cfg())
	for h in scene.data.hotspots["warehouse"]:
		if h["id"] == "warehouse.dancer":
			h["on_success"] = {"activity": "bar"}
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	var pad1: Rect2 = scene.pad_view.button_rects()[1]
	var pad2: Rect2 = scene.pad_view.button_rects()[2]
	_run_to(scene, 64.5 * BEAT)
	var mg: MinigameController = scene.minigames
	assert_eq(mg.state, "active", "seated on the downbeat")
	assert_eq(mg.mode, ActivityMode.Mode.REPLACE)
	var bar := mg.activity as BarActivity
	var e: RunEngine = scene.engine
	var misses0: int = e.judge.misses
	var energy0: float = e.energy
	var moves0: int = (scene.journey_log as Array).size()
	var layer: RunActivityInput = scene._mg.controls_layer
	assert_true(layer != null and layer.ids == ["ing:0", "ing:1", "ing:2", "ing:3"], "four ingredient controls")
	assert_false(scene.pad_view.visible, "the pads are hidden")
	assert_false(scene.lane_input.enabled, "the lane input is off")
	assert_true(scene._mg.view != null and scene._mg.view is BarView, "the bar's view is up in the stage")
	# arrive, demonstration: the strip taps are the controls' but not live yet
	assert_eq(scene.dispatch_tap(pad1.get_center()), "activity_controls", "a strip tap reaches the controls, never a pad")
	assert_eq(int(bar.state()["pos"]), 0)
	assert_true(str(bar.state()["phase"]) in ["arrive", "demo"], "still being shown")
	# into the input phase: pad 1's centre is ingredient 0
	var order := bar.recipe()
	var s := bar.state()
	_run_to(scene, 64.0 * BEAT + 1.0 + 1.6 + 0.6)  # seated + arrive_s + two ingredients shown
	s = bar.state()
	assert_eq(s["phase"], "input", "hidden demo, the player's turn: %s" % str(s["phase"]))
	var strays0: int = e.judge.strays
	var first := int(order[0])
	var pads := [pad1, pad2, scene.pad_view.button_rects()[3], scene.pad_view.button_rects()[4]]
	assert_eq(scene.dispatch_tap((pads[first] as Rect2).get_center()), "activity_controls")
	assert_eq(int(bar.state()["pos"]), 1, "the right strip tap is the right ingredient")
	assert_eq((bar.state()["last_press"] as Dictionary)["id"], "ing:%d" % first)
	scene._on_button_pressed(1, 0)
	assert_eq(e.judge.strays, strays0, "no pad was pressed")
	# a tap on a bottle in the stage is the same press (the view's hit), never a world choice
	var sel0: String = scene.hotspots.selected
	_run_to(scene, scene._vt + 0.5)
	assert_eq(scene.dispatch_tap(scene._stage_host.global_position + scene._stage_host.size * 0.5), "activity_view")
	assert_eq(scene.hotspots.selected, sel0, "no world choice")
	# leaving: the activity is done, judging resumes on the boundary with the strip back a bar before
	var t_leave: float = scene._vt
	assert_true(mg.tap("exit", t_leave))
	_run_to(scene, t_leave + 0.2)
	assert_eq(mg.state, "resuming")
	assert_true(mg.resume_t > t_leave, "resumes on a later boundary")
	assert_true(scene.engine.hold)
	_run_to(scene, mg.resume_t + 0.1)
	assert_eq(mg.state, "")
	assert_false(scene.engine.hold)
	assert_true(scene.pad_view.visible and scene.lane_input.enabled, "the pads are back")
	var fin: Dictionary = mg.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "finished")[0]
	assert_near(float(fin["t"]), mg.resume_t, 1e-6, "released on the boundary")
	assert_eq(e.judge.misses, misses0, "zero misses while the bar owned the strip")
	assert_near(e.energy, energy0, 1e-9, "zero energy loss")
	var seated_moves: Array = (scene.journey_log as Array).slice(moves0).filter(func(a: Dictionary) -> bool: return str(a["action"]) in ["player_move", "player_walk"] and float(a["t0"]) < mg.resume_t - 0.05)
	assert_eq(seated_moves.size(), 0, "no rail step while seated")
	_free(d)
