extends SceneTree
## Shots of the street race in the real run scene (docs/shots/bedsit/race/contact.jpg, docs/bedsit/RACE.md): the grid's lights, the approach to a situation with the
## countdown and the chosen opening lit, an overtake, a contact, the finish; the pads and the HUD in frame. Needs a renderer and a window size (--resolution):
##   bash tools/dev/godot.sh --path . --resolution 1280x720 -s tools/engine/shoot_race.gd -- <out dir>
##   bash tools/dev/godot.sh --path . --resolution 1600x720 -s tools/engine/shoot_race.gd -- <out dir>
## Writes <out dir>/race_<n>_<moment>_<w>x<h>.png; tools/dev/race_sheet.py makes the contact sheet from both sizes. The race's seed is fixed (RW_MINIGAME_SEED=7).

const RANK := {"overtake": 0, "clear": 1, "follow": 2, "brake": 3, "kerb": 4, "contact": 5}

var Driver: GDScript
var _out := ""


func _init() -> void:
	_go.call_deferred()


func _snap(name: String) -> void:
	for i in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	var path := "%s/%s_%dx%d.png" % [_out, name, img.get_width(), img.get_height()]
	img.save_png(path)
	print("shot ", path)


func _dir(sit: Dictionary, worst: bool) -> String:
	var o: Dictionary = sit["outcomes"]
	var best := ""
	for d: String in ["top", "bottom", "left", "right"]:
		var r := int(RANK[str(o[d])])
		if best == "" or (r > int(RANK[str(o[best])]) if worst else r < int(RANK[str(o[best])])):
			best = d
	return best


func _go() -> void:
	await process_frame
	Driver = load("res://tests/fixtures/space_run_driver.gd")
	OS.set_environment("RW_STORY_RATE", "0.000001")
	OS.set_environment("RW_MINIGAME_SEED", "7")
	var args := OS.get_cmdline_user_args()
	_out = args[0] if args.size() > 0 else "user://race_shots"
	DirAccess.make_dir_recursive_absolute(_out)
	var dr: Variant = Driver.new()
	dr.start(self, Vector2(root.size), "space_rave")
	dr.select("space_rave.race")
	dr.in_node("space_race")
	await _snap("race_0_hangar")
	dr.select("space_race.race")
	dr.seated()
	dr.run_for(1.2)
	await _snap("race_1_grid")
	var sc: Node = dr.scene
	var a: RaceActivity = dr.act()
	var shot := {}
	var contact_n := -1
	var guard := 0
	while dr.mg().state != "" and guard < 12000:
		guard += 1
		var sit: Dictionary = a.cur
		if not sit.is_empty():
			if str(sit["selected"]) == "" and dr.t() - float(sit["t_spawn"]) > 0.6:
				var worst := contact_n < 0 and int(sit["n"]) >= 2 and str((sit["outcomes"] as Dictionary)["top"]) == "contact"
				if worst:
					contact_n = int(sit["n"])
				var layer: RunActivityInput = sc._mg.regions_layer
				var d := _dir(sit, worst)
				sc.dispatch_tap((layer.rects()[ContractShapes.REGIONS.find(d)] as Rect2).get_center())
			if not shot.has("approach") and str(sit["selected"]) in ["left", "right"] and float(sit["t_dead"]) - dr.t() < 1.6:
				shot["approach"] = true
				await _snap("race_2_approach")
		for e: Dictionary in a.log:
			if e["kind"] != "resolve" or shot.has(str(e["outcome"])):
				continue
			var age: float = dr.t() - float(e["t"])
			if str(e["outcome"]) == "overtake" and age > 0.35:
				shot["overtake"] = true
				await _snap("race_3_overtake")
			elif str(e["outcome"]) == "contact" and age > 0.12:
				shot["contact"] = true
				await _snap("race_4_contact")
		if a.finished() and not shot.has("finish") and dr.t() > a.finish_t - 0.6:
			shot["finish"] = true
			await _snap("race_5_finish")
		if not a.finished() and not shot.has("gantry") and float(a.player["s"]) > a.course.length_m - 160.0:
			shot["gantry"] = true
			await _snap("race_5a_approach_finish")
		dr.step()
	dr.run_for(1.0)
	await _snap("race_6_back_in_the_hangar")
	print("RACE ", JSON.stringify(a.result()), " shots ", JSON.stringify(shot.keys()))
	dr.finish()
	quit(0)
