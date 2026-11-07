extends SceneTree
## Shots of a rave's three activities in the real run scene (ruling 38, contract 10; docs/shots/bedsit/<theme>/activities.jpg; the theme is the second argument: space (the default), magic,
## dinos or transport): the cloakroom (demonstration, mid-way, payoff), the bar
## (demonstration, mistake, payoff) and the deck (stuck, free), with the pad strip showing the activity's controls. Needs a renderer and a window size (--resolution):
##   bash tools/dev/godot.sh --path . --resolution 1280x720 -s tools/engine/shoot_space_activities.gd -- <out dir> [theme]
##   bash tools/dev/godot.sh --path . --resolution 1600x720 -s tools/engine/shoot_space_activities.gd -- <out dir> [theme]
## Writes <out dir>/<name>_<w>x<h>.png; tools/dev/space_activities_sheet.py <out dir> [out.jpg] [theme] makes the contact sheet from both sizes. (tools/dev/shoot_activities.sh <theme> does all of it.)

var Driver: GDScript  # (loaded in _go: the driver names the Session autoload, which is not there when this script compiles)
var _out := ""
var _p := "space"  # the scene id prefix of the theme (space, magic, dino, transport)


func _init() -> void:
	_go.call_deferred()


func _snap(name: String) -> void:
	for i in 12:  # (real frames at a still song time: RW_STORY_RATE is ~0 below, so the clock stands while the picture is drawn)
		await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	var path := "%s/%s_%dx%d.png" % [_out, name, img.get_width(), img.get_height()]
	img.save_png(path)
	print("shot ", path)


func _go() -> void:
	await process_frame
	Driver = load("res://tests/fixtures/space_run_driver.gd")
	OS.set_environment("RW_STORY_RATE", "0.000001")  # the scene steps the clock by this per real frame in virtual mode; the driver steps it by hand
	var args := OS.get_cmdline_user_args()
	_out = args[0] if args.size() > 0 else "user://space_shots"
	var theme: String = args[1] if args.size() > 1 else "space"
	_p = {"space": "space", "magic": "magic", "dinos": "dino", "transport": "transport"}.get(theme, theme)
	DirAccess.make_dir_recursive_absolute(_out)
	var size := Vector2(root.size)
	# --- the cloakroom
	var dr: Variant = Driver.new()
	dr.start(self, size, "%s_rave" % _p)
	dr.select("%s_rave.cloakroom" % _p)
	dr.in_node("%s_cloakroom" % _p)
	dr.select("%s_cloakroom.cloakroom" % _p)
	dr.seated()
	dr.run_for(1.6)
	await _snap("cloak_1_demonstration")
	var a: CloakroomActivity = dr.act()
	var guard := 0
	while dr.mg().state == "active" and guard < 4000 and a.answers.size() < 3:
		dr.cloak_bot()
		dr.step()
		guard += 1
	dr.until(func() -> bool: return str(a.state()["phase"]) == "await", 8.0)
	dr.run_for(0.5)
	await _snap("cloak_2_midway")
	while dr.mg().state == "active" and guard < 8000 and str(a.state()["phase"]) != "payoff":
		dr.cloak_bot()
		dr.step()
		guard += 1
	dr.run_for(1.2)
	await _snap("cloak_3_payoff")
	dr.until(func() -> bool: return dr.mg().state == "", 30.0)
	dr.finish()
	# --- the bar
	dr = Driver.new()
	dr.start(self, size, "%s_rave" % _p)
	dr.select("%s_rave.bar" % _p)
	dr.in_node("%s_bar" % _p)
	dr.select("%s_bar.bar" % _p)
	dr.seated()
	var b: BarActivity = dr.act()
	dr.until(func() -> bool: return str(b.state()["phase"]) == "demo", 12.0)
	dr.run_for(0.7)
	await _snap("bar_1_demonstration")
	guard = 0
	while dr.mg().state == "active" and guard < 4000 and str(b.state()["outcome"]) != "mistake":
		dr.bar_bot(0)
		dr.step()
		guard += 1
	dr.run_for(0.5)
	await _snap("bar_2_mistake")
	while dr.mg().state == "active" and guard < 12000 and str(b.state()["phase"]) != "payoff":
		dr.bar_bot()
		dr.step()
		guard += 1
	dr.run_for(1.2)
	await _snap("bar_3_payoff")
	dr.until(func() -> bool: return dr.mg().state == "", 30.0)
	dr.finish()
	# --- the deck
	dr = Driver.new()
	dr.start(self, size, "%s_rave" % _p)
	dr.select("%s_rave.stage" % _p)
	dr.in_node("%s_stage" % _p)
	dr.select("%s_stage.deck" % _p)
	dr.seated()
	dr.run_for(1.5)
	await _snap("deck_1_stuck")
	for i in 3:
		var kp: Variant = dr.knob_point()
		if kp != null:
			dr.scene.dispatch_tap(kp)
		dr.run_for(0.9 if i < 2 else 0.5)
	await _snap("deck_2_free")
	dr.finish()
	quit(0)
