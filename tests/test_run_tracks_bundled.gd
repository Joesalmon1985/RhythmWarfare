extends TestCase
## Stage E (docs/APK_61_TRACKS.md): with no RW_TRACKS_DIR and no user://track_packs, packs_root() is the bundled res://track_packs, kept as a res:// path (inside an APK it is not a disk folder),
## and DirAccess reads the pack folders through it. The folder is git-ignored (tools/audio_import/build_android_packs.py makes it), so where it is absent or where a user folder / RW_TRACKS_DIR wins the test prints a SKIP line with the reason and counts one passing check.


func test_the_bundled_folder_is_the_fallback_and_stays_res() -> void:
	var saved := RunTrackScenes.packs_dir_override
	RunTrackScenes.packs_dir_override = ""
	var why := ""
	if OS.get_environment("RW_TRACKS_DIR") != "":
		why = "RW_TRACKS_DIR is set, so it wins over the bundle"
	elif DirAccess.dir_exists_absolute(RunTrackScenes.PACKS_USER_DIR):
		why = "%s exists, so it wins over the bundle" % RunTrackScenes.PACKS_USER_DIR
	elif not DirAccess.dir_exists_absolute(RunTrackScenes.PACKS_BUNDLED_DIR):
		why = "%s is absent (git-ignored; tools/audio_import/build_android_packs.py makes it)" % RunTrackScenes.PACKS_BUNDLED_DIR
	if why != "":  # a visible, counted skip: the filter never reports 0 checks without saying why
		RunTrackScenes.packs_dir_override = saved
		print("  SKIP test_run_tracks_bundled: the bundled-folder checks did not run: %s" % why)
		assert_true(true, "skipped: %s" % why)
		return
	var root := RunTrackScenes.packs_root()
	RunTrackScenes.packs_dir_override = saved
	assert_eq(root, "res://track_packs", "the bundle is used as a res:// path, not globalized")
	var dir := DirAccess.open(root)
	assert_true(dir != null, "DirAccess opens the bundled folder")
	if dir == null:
		return
	var n := 0
	for sub in dir.get_directories():
		if FileAccess.file_exists(root.path_join(sub).path_join("track.json")):
			n += 1
	assert_eq(n, 61, "the 61 packs are listed with their track.json")
	var r := TrackPack.load_pack(root.path_join(dir.get_directories()[0]), false)
	assert_true(r["pack"] != null, "TrackPack.load_pack accepts a res:// pack folder: %s" % str(r["errors"]))
