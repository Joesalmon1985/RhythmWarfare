extends Control
## Level select: the available song packs, the control explanation and calibration.


func _ready() -> void:
	if OS.has_environment("RW_SCENE") and OS.get_environment("RW_SCENE") == "play":
		# scripted runs on exported builds (which take no scene argument) jump straight into the level
		get_tree().change_scene_to_file.call_deferred("res://src/scenes/play.tscn")
		return
	var list: VBoxContainer = $Box/Packs
	var packs := Session.available_packs()
	if packs.is_empty():
		var l := Label.new()
		l.text = "No song packs found. Put a pack in songs/ (see songs/README.md)."
		list.add_child(l)
	for p in packs:
		var b := Button.new()
		b.text = "Play: %s" % p["title"]
		b.custom_minimum_size = Vector2(0, 56)
		b.add_theme_font_size_override("font_size", 24)
		b.pressed.connect(func() -> void:
			Session.pack_dir = p["dir"]
			Session.save_settings()
			get_tree().change_scene_to_file("res://src/scenes/play.tscn"))
		list.add_child(b)
		if Session.pack_dir == p["dir"]:
			b.grab_focus()
	$Box/Calibrate.text = "Calibrate timing (now %+.0f ms)" % Session.calibration_ms
	$Box/Calibrate.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/calibration.tscn"))
	$Box/Help.text = "Three buttons. KICK (left) makes a tank. SNARE (right) makes five infantry. BASS (middle, tap or hold) builds and launches helicopters.\nHit each note as it reaches the line. Lose a factory and its instrument falls silent. Destroy the enemy base before the song ends."
	$Box/Version.text = "Rhythm Warfare  ·  Godot %s" % Engine.get_version_info()["string"]
