extends SceneTree
## Smoke test of an EXPORTED pack (docs/REPO_SIZE.md): the data a build must carry loads from the pack alone. tools/ is not
## exported, so run this file by absolute path, from a folder that is not a project:
##   GODOT --headless --main-pack <pack.pck> -s <repo>/tools/export_smoke.gd
## Prints one line per check and quits with 1 if anything failed. It loads: the main run and every path's run (RunData errors), every
## pack the runs use (stems load as audio streams), the story chapters, the duel rules, the campaign levels, the loop library and
## the stage manifest of each chapter.

var failed := 0


func _check(ok: bool, what: String) -> void:
	print(("ok   " if ok else "FAIL ") + what)
	if not ok:
		failed += 1


func _initialize() -> void:
	var rd := RunData.load_default()
	_check(rd.errors.is_empty() and not rd.packs.is_empty(), "main run: %d packs, %d errors %s" % [rd.packs.size(), rd.errors.size(), str(rd.errors.slice(0, 3))])
	_stems(rd, "main run")
	var ids := RunData.path_ids()
	_check(ids.size() >= 3, "path folders: %s" % str(ids))
	for id in ids:
		if not RunData.path_exists(id):
			continue
		var pd := RunData.load_path(id)
		_check(pd.errors.is_empty() and not pd.packs.is_empty(), "path %s: %d packs, %d errors %s" % [id, pd.packs.size(), pd.errors.size(), str(pd.errors.slice(0, 3))])
		_stems(pd, "path " + id)
	var sc := StoryChapters.load_default()
	_check(sc.chapters.size() > 0, "story chapters: %d" % sc.chapters.size())
	for c in sc.chapters:
		_check(FileAccess.file_exists(str(c["data"])), "chapter data " + str(c["data"]))
	_check(DuelRules.load_default() != null, "duel rules")
	_check(LibraryIndex.load_default() != null, "loop library index")
	_check(FileAccess.file_exists("res://songs/m01_first_watch/level.json") and FileAccess.file_exists("res://data/campaign/campaign.json"), "campaign data")
	_check(ResourceLoader.exists("res://src/scenes/main_menu.tscn"), "main scene")
	_check(ResourceLoader.exists("res://tools/autoplay.gd"), "tools/autoplay.gd is packed")
	print("export smoke: %d failure(s)" % failed)
	quit(1 if failed > 0 else 0)


func _stems(rd: RunData, label: String) -> void:
	var bad := 0
	var n := 0
	for pid in rd.packs:
		var p: Dictionary = rd.packs[pid]
		for k in p.get("stems", {}):
			n += 1
			var path := str(p["dir"]).path_join(str(p["stems"][k]))
			var s: AudioStream = load(path) if ResourceLoader.exists(path) else null
			var frames := -1
			if s is AudioStreamWAV:
				frames = int(round(s.get_length() * float((s as AudioStreamWAV).mix_rate)))
			if frames != int(p.get("loop_frames", -2)):  # the stem loads and is exactly one loop of the pack's frames
				bad += 1
				if bad <= 3:
					print("  bad stem %s (%d frames, pack says %s)" % [path, frames, str(p.get("loop_frames"))])
	_check(bad == 0, "%s: %d stems load, each exactly loop_frames long" % [label, n])
