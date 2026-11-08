extends TestCase
## Ruling 41: the bedsit opening finishes (its way out, hotspot bedsit.way_out -> bedsit.end -> the Warehouse) once ANY one rave has its three activities done in the save
## (raves.<theme>.bass_fixed, cloakroom_done, bar_done); a visit alone does not open it; once open it stays open for the run, and every rave stays reachable from the bedsit.
## The gate: SpaceRaveHost.opening_done sets the run flag SpaceRaveHost.WAY_OUT_FLAG at every scene start (tools/run/make_bedsit.py WAY_OUT).

const TMP := "user://test_bedsit_opening_end.json"


func _progress() -> RunProgress:
	for f in [TMP, TMP + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var p := RunProgress.load_data(TMP, "user://none.json")
	p.run_started()
	return p


func _host(p: RunProgress) -> SpaceRaveHost:
	var h := SpaceRaveHost.new()
	h.progress = p
	return h


func _open(d: RunData, p: RunProgress) -> bool:
	var hs := RunHotspots.new(d, p.run_flags, p.flags)
	hs.begin_scene("bedsit", 50.0)
	var h := hs.get_hotspot("bedsit.way_out")
	assert_false(h.is_empty(), "the bedsit has a way-out hotspot")
	return hs.is_available(h)


func _thresholds_open(d: RunData, p: RunProgress) -> bool:
	var hs := RunHotspots.new(d, p.run_flags, p.flags)
	hs.begin_scene("bedsit", 50.0)
	for f in ["n", "e", "s", "w"]:
		if not hs.is_available(hs.get_hotspot("bedsit.threshold_" + f)):
			return false
	return true


func test_the_way_out_leads_to_the_warehouse_and_is_gated_on_the_flag() -> void:
	var d := RunData.load_path("bedsit")
	assert_eq(d.errors, [])
	var hs := RunHotspots.new(d, {}, {})
	hs.begin_scene("bedsit", 50.0)
	var h := hs.get_hotspot("bedsit.way_out")
	assert_eq(str((h["on_success"] as Dictionary)["route"]), "bedsit.end")
	assert_eq(h["available"]["flags_all"], [SpaceRaveHost.WAY_OUT_FLAG])
	var routes: Array = (d.nodes["bedsit.end"]["next"] as Array).map(func(e: Dictionary) -> String: return str(e["to"]))
	assert_eq(routes, ["run:warehouse"], "bedsit.end hands the run back to the Warehouse")
	assert_true(str(d.nodes["bedsit.end"]["ending"]) != "", "bedsit.end is an ending")


func test_a_visit_alone_does_not_finish_the_opening() -> void:
	var d := RunData.load_path("bedsit")
	var p := _progress()
	var host := _host(p)
	host.enter("bedsit", 0.0)
	assert_false(_open(d, p), "closed at the start")
	for th in ["space", "magic", "dino", "transport"]:  # every rave visited, every station walked into, nothing done
		for sc in ["rave", "stage", "cloakroom", "bar", "race"]:
			host.enter("%s_%s" % [th, sc], 1.0)
		host.enter("bedsit", 2.0)
		assert_false(_open(d, p), "a visit to %s does not open the way out" % th)
	p.apply_activity_flag("rave.space.bass_fixed")  # two of one rave's three, and the third of another: still not one complete rave
	p.apply_activity_flag("rave.space.cloakroom_done")
	p.apply_activity_flag("rave.magic.bar_done")
	host.enter("bedsit", 3.0)
	assert_false(_open(d, p), "two of the three activities are not enough")
	assert_true(_thresholds_open(d, p), "every rave is reachable from the bedsit")


func test_one_raves_three_activities_finish_the_opening_and_it_stays_open() -> void:
	var d := RunData.load_path("bedsit")
	for th: String in RaveSave.THEMES:
		var p := _progress()
		var host := _host(p)
		var pre: String = "dino" if th == "dinos" else th
		host.enter("%s_rave" % pre, 0.0)
		for pz in RaveSave.PUZZLES:
			assert_false(_open(d, p), "%s: not open before %s" % [th, pz])
			p.apply_activity_flag("rave.%s.%s" % [th, pz])
			host.enter("%s_stage" % pre, 1.0)
		host.enter("bedsit", 2.0)
		assert_true(_open(d, p), "%s: the three activities of one rave open the way out" % th)
		assert_true(_thresholds_open(d, p), "%s: the four raves stay reachable" % th)
		host.enter("space_rave", 3.0)  # off to another rave and home again: still open
		host.enter("bedsit", 4.0)
		assert_true(_open(d, p), "%s: once open it stays open" % th)
		assert_true(SpaceRaveHost.opening_done(p))
