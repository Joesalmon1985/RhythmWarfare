extends TestCase
## Debug / Playtest (docs/DEBUG_MODE.md): the scene list covers EVERY scene of every run and path, each row's audio identity resolves through the loaders to packs and stems that exist, every scene
## starts through the debug route on the virtual clock (the same machinery as RW_RUN_START / RW_RUN_PATH), the notes are written and read back, the throwaway save leaves the real one alone, and with
## the mode off the run has no overlay and its HUD stays silent.

const TMP_SAVE := "user://test_playtest_save.json"
const NOTES_DIR := "user://test_playtest_notes"

var _saved: RunProgress


func _begin() -> void:
	_saved = Session.run_progress
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	PlaytestNotes.dir = NOTES_DIR
	PlaytestNotes.delete_files()
	PlaytestMode.end_session()
	PlaytestMode.reset_options()


func _end() -> void:
	PlaytestMode.end_session()
	PlaytestMode.reset_options()
	PlaytestNotes.delete_files()
	PlaytestNotes.dir = "user://"
	Session.run_progress = _saved
	Session.run_start_node = ""
	Session.run_start_path = ""
	for v in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_DEBUG", "RW_DEV_TEXT"]:
		OS.set_environment(v, "")
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)


func _scene(size: Vector2) -> Dictionary:
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	var n := 0
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
		n += 1
		if n % 20 == 0:
			(scene.hud as Control).queue_redraw()
			await tree.process_frame


# --- the list: every scene, each with an audio identity that resolves ---------------------------------------------------------------

func test_the_catalogue_lists_exactly_every_scene_of_every_run_and_path() -> void:
	var runs := PlaytestCatalog.runs()
	var ids: Array = runs.map(func(r: Dictionary) -> String: return str(r["id"]))
	assert_eq(ids.slice(0, 4), ["main", "gospel", "squadron", "ember"], "the main run, then the three paths")
	for pid in RunData.path_ids():
		assert_eq(ids.has(pid), RunData.path_exists(str(pid)), "path %s is listed exactly when it can be played" % pid)
	var by := {}
	for r in runs:
		by[str(r["id"])] = r
	assert_eq(int(by["main"]["scene_count"]), 36, "the main run has 36 scenes")
	assert_eq(int(by["gospel"]["scene_count"]), 17)
	assert_eq(int(by["squadron"]["scene_count"]), 14)
	assert_eq(int(by["ember"]["scene_count"]), 15)
	for r in runs:
		var d := PlaytestCatalog.load_run(str(r["id"]))
		assert_eq(d.errors, [], "%s loads clean" % str(r["id"]))
		var listed: Array = []
		for w in r["worlds"]:
			listed.append_array(w["scenes"])
		var want: Array = d.node_order.duplicate()
		listed.sort()
		want.sort()
		assert_eq(listed, want, "%s: the list holds exactly the run's scenes, none twice" % str(r["id"]))
		assert_eq(int(r["bpm"]), int(d.cfg["timing"]["bpm"]))
	assert_eq(int(by["main"]["bpm"]), 174)
	assert_eq(int(by["gospel"]["bpm"]), 124)
	assert_eq(int(by["squadron"]["bpm"]), 140)
	assert_eq(int(by["ember"]["bpm"]), 145)


func test_every_rows_audio_identity_resolves_to_packs_and_stems_that_exist() -> void:
	var owner_names := 0
	var placeholders := 0
	for r in PlaytestCatalog.runs():
		var data: RunData = r["data"]
		for w in r["worlds"]:
			for sid in w["scenes"]:
				var info := PlaytestCatalog.scene_info(data, str(sid))
				var tag := "%s/%s" % [str(r["id"]), str(sid)]
				var a: Dictionary = info["audio"]
				assert_eq(a["problems"], [], "%s: nothing unresolved (%s)" % [tag, str(a["problems"])])
				assert_false((a["sections"] as Array).is_empty(), tag + ": at least one section")
				assert_eq(bool(a["temporary"]), bool(data.nodes[str(sid)]["temporary"]) or a["source"] == "placeholder", tag + ": the temporary flag is music.json's")
				var covered := 0.0
				for s in a["sections"]:
					covered += float(s["beats"])
					assert_true(data.packs.has(str(s["pack"])), "%s: pack %s exists" % [tag, str(s["pack"])])
					assert_true(data.packs.has(str(s["chart_pack"])), "%s: chart pack %s exists" % [tag, str(s["chart_pack"])])
					for pair in PlaytestCatalog.VOICES:
						var v: Dictionary = s["audio"]["voices"][str(pair[0])]
						assert_true(bool(v["exists"]), "%s: the %s stem of %s exists (%s)" % [tag, str(pair[1]), str(s["pack"]), str(v["path"])])
						assert_true(str(v["file"]) != "" and str(v["file"]) != "(none)", tag + ": the stem has a name")
						if str(s["audio"]["profile"]).begins_with("beat_shaper") or str(s["audio"]["profile"]).begins_with("squadron"):
							assert_true(str(v["file"]).begins_with("Beat Shaper - "), "%s: %s is named as the owner's file" % [tag, str(v["file"])])
							owner_names += 1
						if bool(s["audio"]["placeholder"]):
							placeholders += 1
				assert_near(covered, float(info["phase_beats"]), 1e-6, tag + ": the sections tile the phase")
				assert_true(str(a["source_label"]) != "")
				assert_true(PlaytestCatalog.row_audio_line(info).contains(str(s_first(a)["pack"])), tag + ": the row's audio line names the pack")
				assert_true(bool(info["visual"]["map_found"]), tag + ": the art map is found")
				assert_true(str(info["visual"]["sector"]) != "", tag + ": the home view sits in a sector")
				assert_eq((info["visual"]["hotspots"] as Array).size(), data.hotspots_of(str(sid)).size(), tag + ": the hotspots on offer")
	assert_true(owner_names > 100, "the owner's file names were seen (%d)" % owner_names)
	assert_true(placeholders > 40, "the placeholders were seen (%d)" % placeholders)


func s_first(a: Dictionary) -> Dictionary:
	return a["sections"][0]


func test_the_arrangement_option_picks_the_same_arrangement_in_the_list_and_in_the_game() -> void:
	_begin()
	var ids: Array = []
	for choice in [1, 2, 3]:
		PlaytestMode.set_arrangement(choice)
		var info := PlaytestCatalog.scene_info(RunData.load_default(), "mothership.bridge")
		assert_eq(int(info["audio"]["arrangement_pick"]), choice - 1)
		assert_eq((info["audio"]["arrangement_ids"] as Array).size(), 3)
		ids.append(info["audio"]["arrangement"])
	assert_eq(ids, ["mothership_1", "mothership_2", "mothership_3"], "the three arrangements of the Bridge")
	PlaytestMode.set_arrangement(0)
	assert_eq(RunData.arrangement_override, -1, "off: the game's own seeded pick")
	var picked := PlaytestCatalog.scene_info(RunData.load_default(), "mothership.bridge")
	assert_true(str(picked["audio"]["arrangement"]) in ids)
	assert_contains(PlaytestCatalog.identity_text(picked), "per-run seed", "the detail says the seed picked it")
	PlaytestMode.set_arrangement(2)
	PlaytestMode.begin_session()
	PlaytestMode.prepare("main", "mothership.bridge")
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	assert_eq(scene.data.nodes["mothership.bridge"]["arrangement"], "mothership_2", "the game plays the arrangement the list showed")
	(d["host"] as Control).queue_free()
	PlaytestMode.end_session()
	assert_eq(RunData.arrangement_override, -1, "and the override ends with the session")
	_end()


func test_source_labels_follow_music_json() -> void:
	var main := RunData.load_default()
	var under := PlaytestCatalog.scene_info(main, "underworld")["audio"] as Dictionary
	assert_eq(under["source"], "owner_standin", "the Underworld plays the owner's Lv2 loops as a temporary stand-in")
	assert_true(bool(under["temporary"]))
	assert_eq(PlaytestCatalog.scene_info(main, "warehouse")["audio"]["source"], "owner")
	assert_false(bool(PlaytestCatalog.scene_info(main, "warehouse")["audio"]["temporary"]))
	var gospel := RunData.load_path("gospel")
	var g := PlaytestCatalog.scene_info(gospel, gospel.start_node())["audio"] as Dictionary
	assert_eq(g["source"], "placeholder")
	assert_true(bool(g["temporary"]))
	var sq := RunData.load_path("squadron")
	var c07 := PlaytestCatalog.scene_info(sq, "city")["audio"] as Dictionary
	assert_eq(c07["source"], "owner")
	assert_eq(c07["sections"][0]["audio"]["voices"]["bass"]["file"], "Beat Shaper - C07-Bass.wav", "named exactly as the owner's export")
	assert_eq(c07["sections"][0]["chart"]["charts"]["bass"], "Beat Shaper - C07-Bass.mid")


func test_stems_show_role_owner_name_shared_file_and_the_scenes_that_share_it() -> void:
	var sq := RunData.load_path("squadron")
	var info := PlaytestCatalog.scene_info(sq, "city")
	var voices: Dictionary = info["audio"]["sections"][0]["audio"]["voices"]
	for pair in [["drums", "drums", "Beat Shaper - C07-Drums.wav"], ["bass", "bass", "Beat Shaper - C07-Bass.wav"], ["other", "synth", "Beat Shaper - C07-Synth.wav"]]:
		var v: Dictionary = voices[str(pair[0])]
		assert_eq(v["role"], pair[1])
		assert_eq(v["owner_name"], pair[2], "the owner's export name, not the shared file")
		assert_eq(v["file"], pair[2])
		assert_true(str(v["stem"]).contains("_shared/") or str(v["shared_file"]) != "", "the shared file name is kept")
		assert_true(str(v["shared_file"]).get_extension() == "wav" and str(v["shared_file"]) != str(v["owner_name"]), "small print: %s" % str(v["shared_file"]))
	var text := PlaytestCatalog.identity_text(info)
	assert_contains(text, "Bass (bass): Beat Shaper - C07-Bass.wav")
	assert_contains(text, "file " + str(voices["bass"]["shared_file"]))
	assert_false(text.contains("../_shared"), "the label never shows the relative path")
	# several scenes share one file: every owner of it names the others, and it is symmetrical
	var users := PlaytestCatalog.stem_users()
	var checked := 0
	for path in users:
		var who: Array = users[path]
		if who.size() < 2:
			continue
		var a_run := str(who[0]).get_slice("/", 0)
		var a_scene := str(who[0]).get_slice("/", 1)
		var d := PlaytestCatalog.load_run(a_run)
		var inf := PlaytestCatalog.scene_info(d, a_scene)
		var found := false
		for s in inf["audio"]["sections"]:
			for vk in s["audio"]["voices"]:
				var v2: Dictionary = s["audio"]["voices"][vk]
				if str(v2["path"]).simplify_path() == path:
					found = true
					assert_eq((v2["shared_with"] as Array).size(), who.size() - 1, "%s: the other scenes sharing %s" % [str(who[0]), str(path)])
					assert_false((v2["shared_with"] as Array).has(str(who[0])))
		assert_true(found)
		checked += 1
		if checked >= 6:
			break
	assert_true(checked > 0, "some stem file is played by several scenes")
	var gospel := PlaytestCatalog.scene_info(RunData.load_path("gospel"), "jordan")["audio"]["sections"][0]["audio"]["voices"]["bass"] as Dictionary
	assert_eq(gospel["owner_name"], "", "a placeholder has no owner's export")
	assert_contains(gospel["file"], "synthesised placeholder")
	assert_eq(gospel["role"], "bass")


func test_an_arrangement_scene_names_each_sections_pack_and_the_pack_per_block() -> void:
	var main := RunData.load_default()
	var info := PlaytestCatalog.scene_info(main, "warehouse.bar")
	var a: Dictionary = info["audio"]
	assert_true(a["switches"], "the Warehouse bar's arrangement switches section inside the phase")
	assert_eq((a["sections"] as Array).size(), 2)
	assert_eq((a["blocks"] as Array).size(), 4)
	assert_eq(a["blocks"][0]["pack"], a["sections"][0]["pack"])
	assert_eq(a["blocks"][3]["pack"], a["sections"][1]["pack"])
	assert_true(PlaytestCatalog.packs_line(info).contains(" > "))
	var text := PlaytestCatalog.identity_text(info)
	for want in ["AUDIO", "MIX IN FORCE", "VISUAL", "HOTSPOTS ON OFFER", "Beat Shaper - ", "Bass carry", "Bass bus", "warehouse.bar", "Pieces on", "SECTION 2"]:
		assert_contains(text, want, "the identity text has " + want)


# --- the notes -----------------------------------------------------------------------------------------------------------------------

func test_notes_are_written_to_both_files_and_read_back() -> void:
	_begin()
	var main := RunData.load_default()
	var info := PlaytestCatalog.scene_info(main, "warehouse.bar")
	var live := {"phase": 3, "block": 2, "stage": 1, "stage_label": "Bass enters", "beat": 21.5, "t": 40.1, "energy": 55.0, "pack": str(info["audio"]["sections"][0]["pack"])}
	var e1 := PlaytestNotes.make_entry(info, live, "music_dislike")
	var e2 := PlaytestNotes.make_entry(info, live, "like")
	var e3 := PlaytestNotes.make_entry(PlaytestCatalog.scene_info(RunData.load_path("gospel"), "jordan"), live, "visual_dislike", "too dark, \"quoted\" and\nmultiline")
	assert_true(PlaytestNotes.append(e1))
	assert_true(PlaytestNotes.append(e2))
	assert_true(PlaytestNotes.append(e3))
	assert_true(FileAccess.file_exists(PlaytestNotes.md_path()) and FileAccess.file_exists(PlaytestNotes.jsonl_path()))
	var back := PlaytestNotes.read_all()
	assert_eq(back.size(), 3)
	assert_eq(back[0]["verdict"], "music_dislike")
	assert_eq(back[0]["scene"], "warehouse.bar")
	assert_eq(back[0]["run"], "main")
	assert_eq(back[0]["packs"], info["audio"]["packs"])
	assert_eq(back[0]["stems"]["bass"], info["audio"]["sections"][0]["audio"]["voices"]["bass"]["file"], "the stem file names are in the entry")
	assert_eq(back[0]["temporary"], false)
	assert_eq(back[0]["stem_roles"]["other"], "synth")
	assert_eq(back[0]["stem_files"]["bass"], info["audio"]["sections"][0]["audio"]["voices"]["bass"]["shared_file"], "the shared file name is in the entry too")
	assert_true(back[0]["stem_shared_with"].has("bass"))
	assert_eq(back[0]["phase"], 3)
	assert_eq(back[0]["visual"]["map"], "night_one")
	assert_eq(back[2]["run"], "gospel")
	assert_eq(back[2]["temporary"], true, "the Gospel placeholder is marked temporary")
	assert_eq(back[2]["text"], "too dark, \"quoted\" and\nmultiline", "free text survives a round trip")
	var md := PlaytestNotes.all_markdown()
	for want in ["DON'T LIKE THE MUSIC", "LIKE IT", "DON'T LIKE THE VISUALS", "warehouse.bar", "Beat Shaper - ", "[TEMPORARY]", "block 2", "Bass (bass):", "[file "]:
		assert_contains(md, want, "the readable file has " + want)
	assert_eq(PlaytestNotes.count(), 3)
	assert_contains(PlaytestNotes.summary_line(back[0]), "MUSIC -")
	_end()


func test_the_notes_screen_lists_the_notes_and_copy_all_hands_over_the_file() -> void:
	_begin()
	var main := RunData.load_default()
	var info := PlaytestCatalog.scene_info(main, "hospital")
	PlaytestNotes.append(PlaytestNotes.make_entry(info, {"phase": 1, "block": 1, "stage_label": "Drums", "beat": 3.0, "pack": str(info["audio"]["sections"][0]["pack"])}, "music_dislike"))
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scr: Control = (load(PlaytestMode.NOTES_SCENE) as PackedScene).instantiate()
	host.add_child(scr)
	scr.size = Vector2(844, 390)
	await tree.process_frame
	scr.copy_text(PlaytestNotes.all_markdown())
	assert_contains(scr.copied, "hospital", "Copy all puts the notes on the clipboard")
	assert_contains(scr.where_text(), "playtest_notes.md", "the screen says where the files are")
	assert_contains(scr.where_text(), "APPDATA", "and where on Windows")
	assert_contains(scr.where_text(), "Android", "and on a phone")
	host.queue_free()
	_end()


# --- the mode, the options and the throwaway save --------------------------------------------------------------------------------------

func test_a_debug_session_plays_in_a_throwaway_save_and_gives_the_real_one_back() -> void:
	_begin()
	Session.run_progress.enter("warehouse")
	var real := Session.run_progress
	PlaytestMode.begin_session()
	assert_true(PlaytestMode.on() and PlaytestMode.active)
	assert_true(Session.run_progress != real, "a fresh save stands in")
	Session.run_progress.enter("hospital")
	assert_true(Session.run_progress.data["reached"].has("hospital"))
	PlaytestMode.end_session()
	assert_true(Session.run_progress == real, "the real progress is back")
	assert_false(real.data["reached"].has("hospital"), "nothing leaked into it")
	assert_false(PlaytestMode.active)
	_end()


func test_prepare_uses_the_run_start_machinery() -> void:
	_begin()
	PlaytestMode.energy_choice = 1
	PlaytestMode.autoplay = true
	PlaytestMode.prepare("ember", "hollow.ford")
	assert_eq(Session.run_start_node, "hollow.ford")
	assert_eq(Session.run_start_path, "ember")
	var l := PlaytestMode.consume_launch()
	assert_eq(l["scene"], "hollow.ford")
	assert_eq(float(l["energy"]), 100.0)
	assert_true(bool(l["autoplay"]))
	assert_true(PlaytestMode.consume_launch().is_empty(), "consumed once")
	PlaytestMode.prepare("main", "ward.dorm")
	assert_eq(Session.run_start_path, "")
	PlaytestMode.consume_launch()
	_end()


func test_home_has_a_plain_debug_playtest_button_that_points_at_the_list() -> void:
	_begin()
	for size in [Vector2(844, 390), Vector2(1152, 648), Vector2(1024, 768)]:
		var host := Control.new()
		host.size = size
		tree.root.add_child(host)
		var scene: Control = (load("res://src/scenes/main_menu.tscn") as PackedScene).instantiate()
		host.add_child(scene)
		scene.size = size
		await tree.process_frame
		await tree.process_frame
		var stack: Array = [scene]
		var found: Button = null
		var buttons: Array = []
		while not stack.is_empty():
			var n: Node = stack.pop_back()
			if n is Button:
				buttons.append(n)
				if (n as Button).text.begins_with("Debug / Playtest"):
					found = n
			stack.append_array(n.get_children())
		assert_true(found != null, "the home screen has a Debug / Playtest button at %s" % str(size))
		if found != null:
			assert_eq(found.get_meta("scene"), PlaytestMode.LIST_SCENE)
			assert_true(ResourceLoader.exists(PlaytestMode.LIST_SCENE))
			var r := Rect2(found.global_position, found.size)
			assert_true(Rect2(Vector2.ZERO, size).encloses(r), "it is on screen at %s (%s)" % [str(size), str(r)])
			assert_true(r.size.y >= 44.0, "a touch target")
			for b in buttons:
				if b != found and (b as Button).visible:
					assert_false(r.intersects(Rect2((b as Button).global_position, (b as Button).size)), "%s does not overlap it" % (b as Button).text)
		host.queue_free()
	_end()


func test_the_picker_builds_one_row_per_scene_with_its_audio_line_and_an_info_view() -> void:
	_begin()
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scr: Control = (load(PlaytestMode.LIST_SCENE) as PackedScene).instantiate()
	host.add_child(scr)
	scr.size = Vector2(844, 390)
	await tree.process_frame
	var total := 0
	for r in PlaytestCatalog.runs():
		total += int(r["scene_count"])
	assert_eq(scr.rows.size(), total, "one row per scene of every run and path")
	assert_eq(scr.info_buttons.size(), total)
	assert_true(total >= 82, "at least 36 + 17 + 14 + 15 scenes (%d)" % total)
	var b: Button = scr.rows["squadron/city"]
	assert_contains(b.text, "city", "the row names the scene id")
	assert_contains(b.text, "140 BPM")
	assert_contains(b.text, "squadron_c07", "and the pack")
	assert_contains(b.text, "OWNER", "and where the music comes from")
	assert_contains((scr.rows["gospel/jordan"] as Button).text, "PLACEHOLDER")
	for run_id in ["main", "gospel", "squadron", "ember"]:
		assert_true(scr.headers.has(run_id), "a heading for " + run_id)
	scr.open_detail("main", "warehouse.bar")
	assert_false(scr._list_view.visible)
	assert_true(scr._detail_view.visible)
	assert_eq(scr.detail_info["id"], "warehouse.bar")
	assert_true(scr._detail_body.get_child_count() > 20, "the detail lists audio, mix, visual and hotspots")
	scr.close_detail()
	assert_true(scr._list_view.visible)
	host.queue_free()
	_end()


# --- the run: overlay, feedback, every scene starts ---------------------------------------------------------------------------------------

func test_with_the_mode_off_there_is_no_overlay_and_the_hud_stays_silent() -> void:
	_begin()
	Session.run_start_node = ""
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	assert_true(scene.playtest_overlay == null, "no overlay node in regular play")
	await _run_to(scene, 64.0 * 60.0 / 174.0 + 4.0 * 60.0 / 174.0)
	assert_eq(scene.hud.strings_drawn, 0, "not one draw_string")
	assert_true(scene.hud.frames_drawn > 20)
	assert_true(scene.playtest.is_empty())
	(d["host"] as Control).queue_free()
	_end()


func test_in_debug_mode_the_overlay_shows_the_live_identity_and_the_hud_still_writes_nothing() -> void:
	_begin()
	PlaytestMode.begin_session()
	PlaytestMode.prepare("squadron", "city")
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	assert_eq(scene.run_path, "squadron")
	assert_eq(scene.engine.node_id, "city", "the debug route starts AT the chosen scene")
	var ov: PlaytestOverlay = scene.playtest_overlay
	assert_true(ov != null)
	await _run_to(scene, 3.0 * 60.0 / 140.0)
	var txt := ov.last_text
	for want in ["SQUADRON", "city", "140 BPM", "squadron_c07", "Beat Shaper - C07-Bass.wav", "Beat Shaper - C07-Drums.wav", "Beat Shaper - C07-Synth.wav", "OWNER", "phase 1", "block 1/4", "stage 1", "VISUAL", "map city", "hotspots", "bass bus"]:
		assert_contains(txt, want, "the overlay shows " + want)
	assert_eq(scene.hud.strings_drawn, 0, "the HUD itself is still silent: the overlay is a separate node")
	for n in ["Btn_music_dislike", "Btn_visual_dislike", "Btn_like"]:
		assert_true(ov._row.get_node(n) is Button, n + " exists")
		assert_true((ov._row.get_node(n) as Button).custom_minimum_size.y >= 48.0, n + " is a big touch target")
	# the buttons write the notes and show a toast
	(ov._row.get_node("Btn_music_dislike") as Button).pressed.emit()
	(ov._row.get_node("Btn_visual_dislike") as Button).pressed.emit()
	(ov._row.get_node("Btn_like") as Button).pressed.emit()
	var notes := PlaytestNotes.read_all()
	assert_eq(notes.size(), 3)
	assert_eq(notes.map(func(e: Dictionary) -> String: return str(e["verdict"])), ["music_dislike", "visual_dislike", "like"])
	assert_eq(notes[0]["scene"], "city")
	assert_eq(notes[0]["run"], "squadron")
	assert_eq(notes[0]["pack_playing"], "squadron_c07")
	assert_eq(notes[0]["stems"]["bass"], "Beat Shaper - C07-Bass.wav")
	assert_eq(notes[0]["phase"], 1)
	assert_eq(notes[0]["visual"]["map"], "city")
	assert_eq(notes[0]["temporary"], false)
	assert_true(ov._toast.visible and ov._toast.text.contains("Saved"), "a toast confirms")
	# hide / show
	assert_true(ov.shown)
	ov.toggle()
	assert_false(ov._panel.visible or ov._row.visible, "hidden")
	ov.toggle()
	assert_true(ov._panel.visible and ov._row.visible)
	# the free-text note from the pause panel
	scene._pause_note.text = "the bass is thin here"
	scene._playtest_save_note()
	assert_eq(PlaytestNotes.read_all()[3]["text"], "the bass is thin here")
	(d["host"] as Control).queue_free()
	_end()


func test_hotkeys_m_v_l_write_the_notes() -> void:
	_begin()
	PlaytestMode.begin_session()
	PlaytestMode.prepare("main", "ward.dorm")
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	await _run_to(scene, 1.0)
	var ov: PlaytestOverlay = scene.playtest_overlay
	for k in [KEY_M, KEY_V, KEY_L]:
		var ev := InputEventKey.new()
		ev.keycode = k
		ev.pressed = true
		ov._unhandled_key_input(ev)
	var notes := PlaytestNotes.read_all()
	assert_eq(notes.map(func(e: Dictionary) -> String: return str(e["verdict"])), ["music_dislike", "visual_dislike", "like"], "M, V and L")
	assert_eq(notes[0]["scene"], "ward.dorm")
	assert_eq(notes[0]["phase"], 1)
	(d["host"] as Control).queue_free()
	_end()


func test_the_options_apply_to_the_scene_that_is_started() -> void:
	_begin()
	PlaytestMode.begin_session()
	PlaytestMode.energy_choice = 2
	PlaytestMode.autoplay = true
	PlaytestMode.continue_run = false
	PlaytestMode.prepare("main", "ward.dorm")
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	assert_near(scene.engine.energy, 25.0, 1e-6, "start energy")
	assert_eq(str(scene._bot.get("policy", "")), "perfect", "autoplay is the test bot")
	var flags: Array = PlaytestCatalog.scene_info(scene.data, "ward.dorm")["visual"]["flags_needed"]
	for f in flags:
		assert_true(scene.hotspots.has_flag(str(f)), "the flag %s the scene's hotspots need is set" % str(f))
	# the scene ends: with 'continue' off the run leaves for the list at the downbeat of the next scene
	await _run_to(scene, 64.0 * 60.0 / 174.0 + 0.5)
	assert_true(scene._ended, "the scene ended at its own end")
	var backs: Array = scene.event_log.filter(func(e: Dictionary) -> bool: return str(e["kind"]) == "playtest_back")
	assert_eq(backs.size(), 1, "back to the list, once")
	assert_eq(backs[0]["phase"], 2)
	(d["host"] as Control).queue_free()
	_end()


func test_with_continue_on_the_run_goes_on_into_the_next_scene() -> void:
	_begin()
	PlaytestMode.begin_session()
	PlaytestMode.autoplay = true
	PlaytestMode.prepare("main", "warehouse")
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	await _run_to(scene, 64.0 * 60.0 / 174.0 + 2.0)
	assert_false(scene._ended)
	assert_eq(scene.engine.phase_n, 2, "the second scene began, as the game would")
	assert_true(scene.engine.node_id != "warehouse")
	assert_true(scene.playtest_overlay.last_text.contains("phase 2"), "and the overlay follows")
	(d["host"] as Control).queue_free()
	_end()


func test_every_scene_of_every_run_starts_through_the_debug_route() -> void:
	_begin()
	PlaytestMode.begin_session()
	PlaytestMode.autoplay = true
	PlaytestMode.set_arrangement(1)  # (the per-run seed moves on with every start: fix the arrangement so the list and the scene agree)
	var started := 0
	for r in PlaytestCatalog.runs():
		var data: RunData = r["data"]
		for w in r["worlds"]:
			for sid in w["scenes"]:
				PlaytestMode.prepare(str(r["id"]), str(sid))
				var d := _scene(Vector2(844, 390))
				var scene: Node = d["scene"]
				var tag := "%s/%s" % [str(r["id"]), str(sid)]
				assert_false(scene._ended, tag + ": no fatal error on load")
				assert_eq(scene.engine.node_id, str(sid), tag + ": starts AT the scene")
				assert_eq(scene.run_path, PlaytestCatalog.path_of(str(r["id"])), tag + ": in the right run")
				assert_true(scene.playtest_overlay != null)
				await _run_to(scene, 2.0 * 60.0 / float(data.cfg["timing"]["bpm"]) + 0.6)  # the count-in and a beat or two of play
				assert_false(scene._ended, tag + ": still playing")
				assert_eq(scene.engine.phase_n, 1)
				assert_true(scene.playtest_overlay.last_text.contains(str(sid)), tag + ": the overlay names the scene")
				assert_true(scene.playtest_overlay.last_text.contains(str(PlaytestCatalog.scene_info(data, str(sid))["audio"]["sections"][0]["pack"])), tag + ": and its pack")
				assert_eq(scene.hud.strings_drawn, 0, tag + ": the HUD writes nothing")
				(d["host"] as Control).queue_free()
				await tree.process_frame
				started += 1
	assert_true(started >= 82, "every scene started (%d)" % started)
	_end()
