extends TestCase
## The shared body of tests/test_magic_rave.gd, test_dinos_rave.gd and test_transport_rave.gd: the Space rave's test (tests/test_space_rave.gd) for any of the other three raves. A theme's file extends
## this one and sets `cfg` in `_init`:
##   theme, prefix (the scene id prefix: magic, dino, transport), map (the map and story id: <prefix>_rave), art (assets/story/<art>), facing (N E S W), cloak_hold_sector, bar_hold_sector, lights
## (the stage's three pieces), mood (what the stage lights are called in the log).
## It checks the map and rails, the way in from the bedsit and the way home, puzzle one's bass lock through the host, the three activity nodes (holds, hotspots, things inside their sectors),
## the cast (actors, rigs, sheets), the hub's choices being in the picture, the three-moment view test of every activity at 1280x460 and 1600x460, and a whole run: bedsit, rave, cloakroom, hub,
## bar, stage, knob, home, with the save flags.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const Driver := preload("res://tests/fixtures/space_run_driver.gd")
const BEAT := 60.0 / 174.0

var cfg: Dictionary = {}
var _made: Array = []


func _tmp() -> String:
	return "user://test_%s_rave.json" % str(cfg["prefix"])


func _theme() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://content/raves/%s.json" % cfg["theme"]))


func _progress() -> RunProgress:
	for f in [_tmp(), _tmp() + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var p := RunProgress.load_data(_tmp(), "user://none.json")
	p.run_started()
	return p


func _ids() -> Array:
	var p := str(cfg["prefix"])
	return ["%s_rave" % p, "%s_stage" % p, "%s_cloakroom" % p, "%s_bar" % p, "%s_race" % p]


# --- the map and its rails

func test_the_map_loads_clean_with_every_waypoint_in_a_real_sector() -> void:
	var m := StoryMap.load_chapter(str(cfg["map"]))
	assert_eq(m.errors, [], "the map builds, with its textures present")
	for w in m.waypoints:
		assert_false(m.is_void(str(m.waypoints[w]["sector"])), "waypoint %s is not in a void" % w)
	for need in ["hub_view", "deck_view", "stage_foot", "stage_steps", "cloak_hold", "bar_hold", "hangar_view", "hangar_door", "home_door", "%s_arrive" % cfg["prefix"]]:
		assert_true(m.has_waypoint(need), "waypoint %s" % need)
	assert_true(float(m.sector("stage")["floor"]) > float(m.sector(str(m.waypoint("stage_foot")["sector"]))["floor"]), "the stage is up on a dais")
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % cfg["map"]))
	assert_true(raw["waypoints"].any(func(w: Dictionary) -> bool: return w["id"] == "hub_view" and bool(w.get("choice_view", false))), "hub_view is a choice_view waypoint")
	assert_eq(raw["art"], cfg["art"])


func test_the_rails_and_routes_check_clean_with_holds() -> void:
	var d := RunData.load_path("bedsit")
	assert_eq(d.errors, [])
	var m := StoryMap.load_chapter(str(cfg["map"]))
	var problems: Array = []
	for id in _ids():
		var n: Dictionary = d.nodes[id]
		problems.append_array(StoryRailCheck.check_rail(m, id, str(n["waypoint"]), n["rail"]))
	assert_eq(problems, [], "check_rail_paths: 0 problems on the %s nodes" % cfg["theme"])
	var hub: Dictionary = (d.nodes["%s_rave" % cfg["prefix"]]["rail"]["good"] as Array)[0]
	assert_true(bool(hub["choice"]) and float(hub["hold_bars"]) >= 8.0, "the hub is a choice viewpoint holding 8 bars")
	var routes: Dictionary = _theme()["routes"]
	assert_eq(routes.size(), 3, "a route per station")
	for rid in routes:
		var r: Dictionary = routes[rid]
		assert_eq(ContractShapes.route(r), [], "route %s has the contract shape" % rid)
		var from := str(r["from"])
		for lg in r["legs"]:
			var args := {"to": str(lg["to"]), "via": lg.get("via", []), "style": str(lg["style"]), "bars": float(lg["bars"])}
			assert_eq(StoryRailCheck.check_move(m, from, args, rid), [], "%s leg to %s is a clean walk" % [rid, lg["to"]])
			assert_true(float(lg["hold_bars"]) >= 1.0, "each leg holds still after the move")
			from = str(lg["to"])
		assert_true(float(r["legs"][r["legs"].size() - 1]["hold_bars"]) >= 4.0, "%s ends in a choice-window hold" % rid)
	var stage: Array = d.nodes["%s_stage" % cfg["prefix"]]["rail"]["good"]
	assert_eq(stage[stage.size() - 1]["to"], "deck_view", "the stage route ends at the deck")
	assert_true(float(stage[stage.size() - 1]["hold_bars"]) >= 4.0)


func test_the_hub_leads_to_five_places_and_the_stations_loop_back() -> void:
	var d := RunData.load_path("bedsit")
	var theme := _theme()
	var p := str(cfg["prefix"])
	for k in ["stage", "cloakroom", "bar", "race"]:
		assert_true((theme["activities"] as Dictionary).has(k), "an activity id per station: %s" % k)
	var next: Array = d.nodes["%s_rave" % p]["next"].map(func(e: Dictionary) -> String: return str(e["to"]))
	for to in [_ids()[1], _ids()[2], _ids()[3], _ids()[4], "bedsit"]:
		assert_true(to in next, "the hub leads to %s" % to)
	for id in [_ids()[2], _ids()[3], _ids()[4]]:
		var race_real := FileAccess.file_exists("res://content/races/%s.json" % cfg["theme"])  # (the race data is the switch: tests/test_race_themes.gd)
		assert_eq(bool(d.nodes[id].get("placeholder", false)), id == _ids()[4] and not race_real, "%s: the race entrance is a placeholder only until the theme has race data" % id)
		assert_true(d.nodes[id]["next"].any(func(e: Dictionary) -> bool: return str(e["to"]) == "%s_rave" % p and bool(e.get("loop", false))), "%s loops back to the hub" % id)
	assert_eq(ContractShapes.theme_data(theme), [], "content/raves/%s.json has the contract-2 shape" % cfg["theme"])
	assert_eq(theme["race"]["entrance"], "hangar_view", "the race entrance is a placeholder pose the race agent wires")
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % cfg["map"]))
	assert_true(raw["things"].any(func(t: Dictionary) -> bool: return str(t["id"]) == "hangar_racer"), "a vehicle glimpsed at the race entrance")
	assert_true(raw["things"].any(func(t: Dictionary) -> bool: return str(t["id"]) == "home_hatch"), "the way home is a thing")


# --- the way in and the way home

func test_the_bedsit_route_lands_in_the_real_rave_and_home_comes_back_to_the_same_wall() -> void:
	var save := {"bedsit_facing": str(cfg["facing"])}
	var r := BedsitNav.press(save, "top")
	assert_eq(r["route"], str(cfg["map"]), "the top region of that facing leaves for the rave")
	var d := RunData.load_path("bedsit")
	var n: Dictionary = d.nodes[str(cfg["map"])]
	assert_false(bool(n.get("placeholder", false)), "a real node now")
	assert_eq(n["world"], str(cfg["map"]))
	assert_eq((n["rail"] as Dictionary)["arrive"], "%s_arrive" % cfg["prefix"], "an arrival pose")
	var home: Dictionary = ((n["next"] as Array).filter(func(e: Dictionary) -> bool: return str(e["to"]) == "bedsit"))[0]
	assert_eq(home["dir"], "up")
	assert_eq(BedsitNav.facing_of(save), str(cfg["facing"]), "the rave does not change the facing the player comes home to")
	assert_eq(_theme()["home"]["route"], "home")
	var routes := BedsitNav.routes()
	assert_true(bool((routes["landed"] as Dictionary)[str(cfg["map"])]), "routes.json marks the rave as landed")
	var themes: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/bedsit/themes.json"))
	assert_eq((themes["facings"] as Dictionary)[str(cfg["facing"])], str(cfg["theme"]))


# --- the stage and the knob

func _stage(size: Vector2) -> StoryStage:
	var run := StoryRun.create({}, "res://content/story/%s.json" % cfg["map"])
	var stage := StoryStage.new()
	stage.size = size
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_art(str(cfg["art"])), run.data, run)
	stage.attach_world(stage.map, true)
	stage.lowres.size = size
	stage.lowres._fit()
	return stage


func _knob(beat_s: float) -> BassKnobActivity:
	var a := BassKnobActivity.new()
	var conf: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/bass_knob.json"))
	conf["theme"] = str(cfg["theme"])  # (a run's request carries the theme; this stands in for it)
	a.setup({"beat_s": beat_s, "config": conf})
	a.begin(0.0)
	return a


func test_the_knob_is_touched_through_a_world_region_over_its_screen_point_at_the_deck() -> void:
	var stage := _stage(Vector2(1280, 460))
	assert_eq(stage.world.errors, [], "the world builds without texture errors")
	stage.player.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": "deck_view", "bars": 0.01, "cut": true}})
	var a := _knob(BEAT)
	stage.set_things(a.things())
	stage.update(2.0, 60.0)
	var r: Variant = stage.thing_screen_rect("bass_knob")
	assert_true(r != null, "the knob is in the picture from the deck")
	if r != null:
		var rr: Rect2 = r
		assert_true(Rect2(Vector2.ZERO, stage.size).encloses(rr) and rr.size.y >= 48.0, "inside the strip and at least 48 px tall (%s)" % str(rr))
		assert_eq(SpaceRaveHost.hit_rect(rr.get_center(), rr), "knob")
		assert_true(stage.thing_screen_rect("deck") != null, "the deck is in the picture behind it")
	stage.free()


func test_the_stage_light_group_is_pieces_of_the_art_manifest() -> void:
	var assets := StoryAssets.load_art(str(cfg["art"]))
	assert_true(assets.ok() and assets.errors.is_empty(), "the art manifest loads (%s)" % str(assets.errors))
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % cfg["map"]))
	var pieces: Array = []
	for t: Dictionary in raw["things"]:
		if t.has("piece"):
			pieces.append(str(t["piece"]))
	for p in cfg["lights"]:
		assert_true(p in pieces, "the stage has the piece %s" % p)
		assert_false(assets.piece(str(p)).is_empty(), "the manifest names the piece %s" % p)
		assert_true(assets.texture(str(assets.piece(str(p))["file"])) != null, "and its texture loads: %s" % p)
	assert_eq(SpaceRaveHost.LIGHT_GROUPS[str(cfg["theme"])], cfg["lights"], "the host switches the same three pieces")


# --- the bass lock

func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	_made.append(a)
	return a


func _cleanup() -> void:
	for a in _made:
		if is_instance_valid(a):
			(a as RunAudio).stop()
			(a as RunAudio).free()
	_made.clear()
	Fx.clear()


func _pump(a: RunAudio, t: float) -> void:
	for path in a._requested:
		for _i in 400:
			if ResourceLoader.load_threaded_get_status(str(path)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				break
			OS.delay_msec(5)
	while not a._schedule.is_empty() and float(a._schedule[0]["t"]) <= t:
		var item: Dictionary = a._schedule.pop_front()
		a._run(item, float(item["t"]), 0.0)
	while not a.track._schedule.is_empty() and float(a.track._schedule[0]["t"]) <= t:
		var it: Dictionary = a.track._schedule.pop_front()
		a.track.run_item(it, float(it["t"]), 0.0)
	a.track.step(t, 0.0)


func _run(e: RunEngine, a: RunAudio, t_end: float, from := -0.5) -> float:
	var t := from
	var pressed := {}
	while t < t_end and not e.over:
		for ev in e.update(t):
			a.on_event(ev)
		_pump(a, t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
				e.release(int(n["pad"]), float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.06, int(n["pad"]))
		t += 1.0 / 30.0
	return t


func _count(a: RunAudio, kind: String) -> int:
	return a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == kind).size()


func test_the_bass_is_locked_on_entry_freed_by_the_knob_on_a_bar_line_without_a_restart_and_kept() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	assert_eq(d.errors, [])
	var a := _audio(d)
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.track_gate = a.track.is_ready
	a.track.notes_fn = func() -> Array: return e.level.notes
	a.track.prepare(d, "warehouse")
	var prog := _progress()
	var host := SpaceRaveHost.new()
	host.progress = prog
	host.track_audio = a.track
	host.track = "acuna_go_back"
	host.beat_s = e.beat_s
	host.phase_t0_fn = func() -> float: return e.phase_t0
	var stage_log: Array = []
	host.apply_fn = func(act: Dictionary) -> void: stage_log.append(act)
	var th := str(cfg["theme"])
	host.enter("%s_rave" % cfg["prefix"], 0.0)
	assert_true(host.locked, "locked on entry: bass_fixed is false")
	assert_eq(host.theme, th)
	assert_eq(prog.rave_theme(), th)
	assert_true(stage_log.any(func(x: Dictionary) -> bool: return x["action"] == "crowd_cap" and float(x["args"]["cap"]) <= 25.0), "the crowd is capped quiet")
	var off: Array = stage_log.filter(func(x: Dictionary) -> bool: return x["action"] == "piece_off").map(func(x: Dictionary) -> String: return str(x["args"]["piece"]))
	assert_eq(off, cfg["lights"], "the stage lights of this rave are down")
	e.begin("warehouse")
	host.beat_s = e.beat_s
	var t := _run(e, a, 20.0 * e.beat_s)
	var tr: TrackTransport = a.track._live()["transport"]
	assert_true(tr.is_stem_locked("bass"))
	assert_eq(tr.stem_gain("bass"), 0.0)
	var starts0 := _count(a, "start")
	var act := _knob(e.beat_s)
	var t_fixed := 21.3 * e.beat_s
	for tt in [18.5 * e.beat_s, 20.0 * e.beat_s]:
		act.tap("knob", tt)
		host.step(tt, act.state())
	assert_true(tr.is_stem_locked("bass"), "two touches: the bass stays locked")
	act.tap("knob", t_fixed)
	act.update(t_fixed)
	host.step(t_fixed, act.state())
	var t_u := host.unlock_t
	assert_near(t_u, 24.0 * e.beat_s, 1e-6, "the next bar line (beat 24)")
	var on: Array = stage_log.filter(func(x: Dictionary) -> bool: return x["action"] == "piece_on" and absf(float(x["t0"]) - t_u) < 1e-9).map(func(x: Dictionary) -> String: return str(x["args"]["piece"]))
	assert_eq(on, cfg["lights"], "this rave's stage lights come up on the same line")
	assert_true(stage_log.any(func(x: Dictionary) -> bool: return x["action"] == "crowd_cap" and float(x["args"]["cap"]) >= 100.0 and absf(float(x["t0"]) - t_u) < 1e-9), "the crowd dances from the same line")
	t = _run(e, a, 26.0 * e.beat_s, t)
	assert_eq(a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "unlock").size(), 1)
	assert_false(tr.is_stem_locked("bass"))
	assert_eq(_count(a, "start"), starts0, "no restart")
	assert_eq(_count(a, "seek") + _count(a, "stop"), 0, "the transport position is continuous: no seek")
	act.update(t_fixed + 4.0 * e.beat_s)
	assert_true(act.is_done())
	assert_true(("rave.%s.bass_fixed" % th) in act.result()["flags_to_set"], "the result sets this rave's flag")
	for f in act.result()["flags_to_set"]:
		prog.apply_activity_flag(str(f))
	assert_true(prog.puzzle_done(th, "bass_fixed"))
	assert_false(prog.puzzle_done("space" if th != "space" else "magic", "bass_fixed"), "another rave's puzzle is untouched")
	host.leave(32.0 * e.beat_s)
	assert_eq(prog.rave_theme(), "")
	host.enter("%s_stage" % cfg["prefix"], 40.0 * e.beat_s)
	assert_false(host.locked, "re-entering the stage does not lock the bass again")
	assert_true(prog.has_flag("%s_bass_fixed" % th), "the deck's hotspot is hidden by its run flag")
	_cleanup()


func test_the_host_reads_the_theme_from_the_scene_id() -> void:
	assert_eq(SpaceRaveHost.theme_of("%s_stage" % cfg["prefix"]), str(cfg["theme"]))
	assert_eq(SpaceRaveHost.theme_of("%s_race" % cfg["prefix"]), str(cfg["theme"]))
	assert_eq(SpaceRaveHost.theme_of("bedsit"), "")
	assert_eq(SpaceRaveHost.theme_of("magic_rave_extra"), "")
	var host := SpaceRaveHost.new()
	host.progress = _progress()
	host.enter("space_rave", 0.0)
	host.enter("%s_rave" % cfg["prefix"], 4.0)  # straight from one rave to another
	assert_eq(host.theme, str(cfg["theme"]))
	assert_eq(host.progress.rave_theme(), str(cfg["theme"]))


# --- the cast and the stations

func test_the_three_activity_nodes_exist_with_their_holds_hotspots_and_things_in_the_rooms_sectors() -> void:
	var d := RunData.load_path("bedsit")
	var m := StoryMap.load_chapter(str(cfg["map"]))
	var themes: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/bedsit/themes.json"))
	var p := str(cfg["prefix"])
	var want := {"%s_cloakroom" % p: ["cloak_hold", "cloak_counter", "cloakroom"], "%s_bar" % p: ["bar_hold", "bar_counter", "bar"]}
	for id: String in want:
		var cloak := id.ends_with("cloakroom")
		var n: Dictionary = d.nodes[id]
		assert_false(bool(n.get("placeholder", false)), "%s is a real scene" % id)
		var good: Array = n["rail"]["good"]
		assert_eq(str(good[good.size() - 1]["to"]), want[id][0], "%s: the route from the hub ends at the hold" % id)
		assert_true(float(good[good.size() - 1]["hold_bars"]) >= 4.0, "%s: a hold for the activity" % id)
		var hold: Dictionary = m.waypoint(str(want[id][0]))
		assert_eq(str(hold["sector"]), str(cfg["cloak_hold_sector"] if cloak else cfg["bar_hold_sector"]), "the hold stands just outside the alcove, facing it")
		var rows: Array = (d.hotspots[id] as Array).filter(func(h: Dictionary) -> bool: return (h["on_success"] as Dictionary).has("activity"))
		assert_eq(rows.size(), 1, "%s: one hotspot carries the activity" % id)
		assert_eq(str(rows[0]["on_success"]["activity"]), want[id][2])
		assert_eq(str(rows[0]["anchor"]["thing"]), want[id][1], "anchored on the counter")
		assert_eq((rows[0]["window"] as String), "any", "any window seats it")
		assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t["id"]) == want[id][1]), "the counter is a map thing")
		var layout: Dictionary = (themes["cloakroom" if cloak else "bar"][cfg["theme"]] as Dictionary)["layout"]
		assert_eq(str(layout["sector"]), "cloak" if cloak else "bar")
		var poly: PackedVector2Array = m.sector(str(layout["sector"]))["poly"]
		var pts: Array = []
		if cloak:
			pts.append_array(layout["customer_slots"])
			for k in ["attendant_at", "rail_at", "symbol_at", "prev_at"]:
				pts.append(layout[k])
			var r0: Array = layout["rail_at"]
			var st: Array = layout["rail_step"]
			pts.append([float(r0[0]) + 7.0 * float(st[0]), float(r0[1]) + 7.0 * float(st[1])])
		else:
			for k in ["customer_at", "customer_glass_at", "glass_at", "bubble_at"]:
				pts.append(layout[k])
			assert_eq(str(layout["map"]), str(cfg["art"]), "the bar's layout names this rave's art")
		for pt: Array in pts:
			assert_true(Geometry2D.is_point_in_polygon(Vector2(float(pt[0]), float(pt[1])), poly), "%s: %s is inside the %s" % [id, str(pt), str(layout["sector"])])
	var story: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/%s.json" % cfg["map"]))
	assert_eq(story["art"], cfg["art"])
	var actors := (story["actors"] as Array).map(func(a: Dictionary) -> String: return str(a["id"]))
	var homes: Dictionary = m.homes
	var slots: Array = (themes["cloakroom"][cfg["theme"]]["layout"] as Dictionary)["customer_slots"]
	for k in 8:
		assert_true(("customer_%d" % k) in actors and homes.has("customer_%d" % k), "customer_%d is a crowd actor with a home" % k)
		assert_eq(str(homes["customer_%d" % k]["sector"]), "cloak")
		assert_true((homes["customer_%d" % k]["at"] as Vector2).distance_to(Vector2(float(slots[k][0]), float(slots[k][1]))) < 0.05, "customer_%d's home is its slot in the layout" % k)
	for id in ["attendant", "bartender", "customer", "dj", "pilot"]:
		assert_true(id in actors and homes.has(id), "%s is a crowd actor with a home" % id)
	assert_eq(str(homes["customer"]["sector"]), "bar")
	assert_eq(str(homes["attendant"]["sector"]), "cloak")
	assert_eq(str(homes["bartender"]["sector"]), "bar")
	assert_eq(str(homes["dj"]["sector"]), "stage")
	assert_eq(str(homes["pilot"]["sector"]), "hangar")
	assert_true(actors.size() >= 36, "a crowd: %d people (the Space rave has 37)" % actors.size())
	for pc in ["cloak_lamp", "bar_shelf_1", "bar_shelf_2", "bar_shelf_3", "bar_shelf_4"]:
		assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t.get("piece", "")) == pc), "%s is a map piece" % pc)
	for sheet in ["cloak_coat", "cloak_symbols_%s" % cfg["theme"], "bar_glass_%s" % cfg["theme"], "bar_order_%s" % cfg["theme"], "sr_knob"]:
		var base := "res://assets/story/%s/sprites/%s" % [cfg["art"], sheet]
		assert_true(FileAccess.file_exists(base + ".png") and FileAccess.file_exists(base + ".json"), "%s has its sheet and its grid sidecar" % sheet)
		var g: Variant = JSON.parse_string(FileAccess.get_file_as_string(base + ".json"))
		assert_true(typeof(g) == TYPE_DICTIONARY and (g as Dictionary).has("grid"), "%s: {grid}" % sheet)


func test_every_person_has_a_rig_in_this_raves_art_and_the_sheets_are_named_placeholders() -> void:
	var assets := StoryAssets.load_art(str(cfg["art"]))
	var story: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/%s.json" % cfg["map"]))
	var kinds := {}
	for a: Dictionary in story["actors"]:
		var rig := assets.rig(str(a["archetype"]), str(a["variant"]))
		assert_false(rig.is_empty(), "%s: rig %s_%s exists" % [a["id"], a["archetype"], a["variant"]])
		assert_true((rig["_assets"] as StoryAssets).art == str(cfg["art"]), "%s: the rig is this rave's own, not the Mothership's" % a["id"])
		kinds["%s_%s" % [a["archetype"], a["variant"]]] = true
	assert_true(kinds.size() >= 6, "at least six different clubgoers (%d)" % kinds.size())
	var first: Dictionary = assets.rig("grey", "a")
	for part: Dictionary in first["parts"]:
		assert_true(assets.texture(str(part["file"])) != null, "rig part %s loads" % part["name"])
	var mani: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/story/%s/manifest.json" % cfg["art"]))
	assert_eq(mani["archetypes"].keys().size(), 6)
	assert_true(FileAccess.file_exists("res://tools/story/rave_people.gd") or FileAccess.file_exists("res://tools/story/rave_people.py"), "the generator is in the tree")


func test_every_hub_choice_is_in_the_picture_from_the_hub_viewpoint() -> void:
	var m := StoryMap.load_chapter(str(cfg["map"]))
	var hub: Dictionary = m.waypoint("hub_view")
	var at: Vector2 = hub["at"]
	var yaw := float(hub["yaw"])
	for id in ["dj", "attendant", "bartender", "pilot"]:
		var home: Vector2 = m.homes[id]["at"]
		var d := home - at
		var bearing := rad_to_deg(atan2(-d.x, -d.y))
		var off := wrapf(bearing - yaw, -180.0, 180.0)
		assert_true(absf(off) <= 40.0, "%s stands %.1f degrees off the hub's line of sight (inside the 16:9 view)" % [id, off])
		assert_true(d.length() > 8.0, "%s is across the room, not at the camera" % id)
	var hatch: Variant = null
	for t: Dictionary in m.things:
		if str(t["id"]) == "home_hatch":
			hatch = t
	assert_true(hatch != null, "the home hatch is a thing")


# --- the whole rave in the real run scene (integration: ruling 38, contract 10) ---------------------------------------------------------------------

func test_the_run_plays_hub_cloakroom_hub_bar_stage_knob_and_home_with_the_save_flags_set() -> void:
	var dr := Driver.new()
	var p := str(cfg["prefix"])
	var th := str(cfg["theme"])
	dr.start(tree, Vector2(1280, 720), "%s_rave" % p)
	var sc: Node = dr.scene
	var prog: RunProgress = Session.run_progress
	assert_eq(dr.node(), "%s_rave" % p)
	# --- the cloakroom
	assert_true(dr.select("%s_rave.cloakroom" % p), "the attendant is chosen in the hub")
	assert_true(dr.in_node("%s_cloakroom" % p), "the route leads to the cloakroom scene (%s)" % dr.node())
	assert_true(dr.select("%s_cloakroom.cloakroom" % p), "the counter is chosen")
	assert_true(dr.seated(), "the cloakroom seats")
	var cloak: Variant = dr.act()
	assert_true(cloak is CloakroomActivity, "it is the cloakroom")
	var layer: RunActivityInput = sc._mg.controls_layer
	assert_true(layer != null and layer.ids == ["same", "different"], "two controls in the pad slots")
	var guard := 0
	while dr.mg().state == "active" and guard < 3000:
		dr.cloak_bot()
		dr.step()
		guard += 1
	assert_true(prog.puzzle_done(th, "cloakroom_done"), "the cloakroom flag is set in the save")
	assert_true(dr.until(func() -> bool: return dr.mg().state == "", 30.0), "the strip is handed back")
	assert_true(dr.select("%s_cloakroom.back" % p), "the way back is chosen")
	assert_true(dr.in_node("%s_rave" % p, 60.0), "leaving returns to the hub (%s)" % dr.node())
	assert_true(prog.has_flag("%s_cloakroom_done" % th), "and the activity's hotspot is gone for the run")
	# --- the bar
	assert_true(dr.select("%s_rave.bar" % p), "the bartender is chosen in the hub")
	assert_true(dr.in_node("%s_bar" % p), "the route leads to the bar scene (%s)" % dr.node())
	assert_true(dr.select("%s_bar.bar" % p), "the counter is chosen")
	assert_true(dr.seated(), "the bar seats")
	assert_true(dr.act() is BarActivity)
	guard = 0
	while dr.mg().state == "active" and guard < 6000:
		dr.bar_bot()
		dr.step()
		guard += 1
	assert_true(prog.puzzle_done(th, "bar_done"), "the bar flag is set in the save")
	assert_true(dr.until(func() -> bool: return dr.mg().state == "", 30.0))
	assert_true(dr.select("%s_bar.back" % p))
	assert_true(dr.in_node("%s_rave" % p, 60.0), "back in the hub (%s)" % dr.node())
	# --- the stage and the knob
	assert_true(dr.select("%s_rave.stage" % p))
	assert_true(dr.in_node("%s_stage" % p), "the stage (%s)" % dr.node())
	assert_true(dr.select("%s_stage.deck" % p))
	assert_true(dr.seated(), "the deck seats the knob")
	assert_true(dr.act() is BassKnobActivity)
	for i in 3:
		var kp: Variant = dr.knob_point()
		assert_true(kp != null, "the knob is in the picture")
		if kp == null:
			break
		assert_eq(sc.dispatch_tap(kp), "activity_view", "the tap is the room's")
		dr.run_for(1.0)
	assert_true(prog.puzzle_done(th, "bass_fixed") or dr.until(func() -> bool: return prog.puzzle_done(th, "bass_fixed"), 10.0), "the bass is fixed in the save")
	assert_true(dr.until(func() -> bool: return dr.mg().state == "", 30.0))
	# --- home
	assert_true(dr.select("%s_stage.home" % p))
	assert_true(dr.in_node("bedsit", 60.0), "home is the bedsit (%s)" % dr.node())
	for q in ["bass_fixed", "cloakroom_done", "bar_done"]:
		assert_true(prog.puzzle_done(th, q), "saved: %s" % q)
	assert_false(prog.puzzle_done("space", "bass_fixed"), "the Space rave's puzzle is untouched")
	dr.finish()


func test_the_race_entrance_is_a_placeholder_node_that_loops_back_to_the_hub() -> void:
	var dr := Driver.new()
	var p := str(cfg["prefix"])
	dr.start(tree, Vector2(1280, 720), "%s_rave" % p)
	assert_true(dr.select("%s_rave.race" % p), "the pilot is chosen in the hub")
	assert_true(dr.in_node("%s_race" % p), "the route leads to the race placeholder (%s)" % dr.node())
	assert_true(dr.select("%s_race.back" % p))
	assert_true(dr.in_node("%s_rave" % p, 60.0), "and back to the hub (%s)" % dr.node())
	dr.finish()


# --- the three-moment view test (contract 10): the things at the hold, in the real map ------------------------------------------------------------

func _cloak_moments() -> Array:
	CloakroomSession.reset()
	var cfgj: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/cloakroom.json"))
	var a := CloakroomActivity.new()
	a.setup({"seed": 7, "beat_s": BEAT, "config": cfgj, "request": {"theme": cfg["theme"]}, "world": WorldThings.new()})
	a.begin(0.0)
	var out: Array = []
	a.update(1.0 * BEAT)
	out.append(["demonstration", 1.0 * BEAT, a.things()])
	var t := 11.0 * BEAT
	a.update(t)
	for i in 3:
		a.tap(a.expected[a.answers.size()], t)
		t += 1.2
		a.update(t)
	out.append(["mid-way", t, a.things()])
	var guard := 0
	while str(a.state()["phase"]) != "payoff" and guard < 40:
		if str(a.state()["phase"]) == "await":
			a.tap(a.expected[a.answers.size()], t)
		t += 0.6
		a.update(t)
		guard += 1
	out.append(["payoff", t, a.things()])
	CloakroomSession.reset()
	return out


func _bar_moments() -> Array:
	BarActivity.forget_all()
	var cfgj: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/bar.json"))
	var a := BarActivity.new()
	a.setup({"seed": 7, "beat_s": BEAT, "config": cfgj, "wallet": null, "request": {"theme": cfg["theme"]}})
	a.begin(0.0)
	var out: Array = []
	var t := 0.0
	var wrong_done := false
	var shot_demo := false
	var guard := 0
	while str(a.state()["phase"]) != "payoff" and guard < 4000:
		t += 0.05
		a.update(t)
		var s := a.state()
		if str(s["phase"]) == "demo" and not shot_demo:
			shot_demo = true
			out.append(["demonstration", t, a.things()])
		if str(s["phase"]) == "input":
			var rec: Array = s["recipe"]
			var pos := int(s["pos"])
			if not wrong_done and pos == 0:
				wrong_done = true
				a.tap("ing:%d" % ((int(rec[0]) + 1) % 4), t)
				a.update(t + 0.05)
				out.append(["mistake", t + 0.05, a.things()])
			elif fmod(t, 0.5) < 0.05 and pos < rec.size():
				a.tap("ing:%d" % int(rec[pos]), t)
		guard += 1
	out.append(["payoff", t, a.things()])
	BarActivity.forget_all()
	return out


func test_every_thing_of_each_activity_is_inside_the_strip_and_at_least_48_px_tall_at_the_hold_in_three_moments() -> void:
	var cases := {"cloak_hold": _cloak_moments(), "bar_hold": _bar_moments()}
	cases["deck_view"] = [["stuck", 1.0, _knob(BEAT).things()]]
	var freed := _knob(BEAT)
	freed.tap("knob", 1.0)
	freed.tap("knob", 2.0)
	freed.tap("knob", 3.0)
	freed.update(7.0)
	cases["deck_view"].append(["free", 7.0, freed.things()])
	for sz: Vector2 in [Vector2(1280, 460), Vector2(1600, 460)]:
		var stage := _stage(sz)
		for hold: String in cases:
			stage.player.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": hold, "bars": 0.01, "cut": true}})
			var moments: Array = cases[hold]
			assert_true(moments.size() >= 2, "%s: moments shot" % hold)
			for mo: Array in moments:
				stage.set_things(mo[2])
				stage.update(float(mo[1]), 60.0)
				assert_eq(stage.world.dynamic.errors, [], "%s %s: the sheets load" % [hold, mo[0]])
				assert_true((mo[2] as Array).size() >= 1, "%s %s: something to see" % [hold, mo[0]])
				for th: Dictionary in mo[2]:
					var r: Variant = stage.thing_screen_rect(str(th["id"]))
					assert_true(r != null, "%s %s %s %s: drawn" % [str(sz), hold, mo[0], th["id"]])
					if r == null:
						continue
					var rr: Rect2 = r
					assert_true(Rect2(Vector2.ZERO, sz).encloses(rr), "%s %s %s %s: inside the strip (%s)" % [str(sz), hold, mo[0], th["id"], str(rr)])
					assert_true(rr.size.y >= 48.0, "%s %s %s %s: at least 48 px tall (%.1f)" % [str(sz), hold, mo[0], th["id"], rr.size.y])
		stage.free()
