extends TestCase
## A chapter may list `music_packs` (content/story/<chapter>.json): its own recording first, then pre-rendered arrangements (tools/content/arrange.py render, songs/story_<chapter>_<n>).
## StoryRun picks one by a seed (none = the first, so every existing test and tool is unchanged); the rendered pack plays through the normal recorded-music path.
## Every chapter lists two renders after its own recording.

const CHAPTERS := ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]
const OWN := {"night_one": "res://songs/story_n1_warehouse", "mothership": "res://songs/m10_last_light", "underworld": "res://songs/m09_iron_rhythm",
		"hospital": "res://songs/m05_counterpoint", "mental_hospital": "res://songs/m07_crossroads"}


func _path(ch: String) -> String:
	return "res://content/story/%s.json" % ch


func _raw(ch: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(_path(ch)))


func _seed_for(index: int, raw: Dictionary) -> int:
	for s in range(0, 400):
		if StoryRun.pick_music_pack(raw, s) == str((raw["music_packs"] as Array)[index]):
			return s
	return -1


func test_every_chapter_lists_its_own_recording_first_and_two_renders() -> void:
	for ch in CHAPTERS:
		var raw := _raw(ch)
		var packs: Array = raw["music_packs"]
		assert_eq(packs.size(), 3, ch + ": its own recording and two renders")
		assert_eq(packs[0], OWN[ch], ch + ": the existing recording stays first")
		assert_eq(packs[0], raw["music_pack"])
		assert_eq(packs[1], "res://songs/story_%s_1" % ch)
		assert_eq(packs[2], "res://songs/story_%s_2" % ch)


func test_the_pick_is_the_first_without_a_seed_and_deterministic_with_one() -> void:
	for ch in CHAPTERS:
		var raw := _raw(ch)
		var packs: Array = raw["music_packs"]
		assert_eq(StoryRun.pick_music_pack(raw, -1), packs[0], ch + " no seed: the chapter's own recording")
		var seen := {}
		for s in range(0, 60):
			var a := StoryRun.pick_music_pack(raw, s)
			assert_eq(StoryRun.pick_music_pack(raw, s), a)
			seen[a] = true
		assert_eq(seen.keys().size(), packs.size(), ch + ": every listed pack is reachable by some seed")
	var plain: Dictionary = {"id": "x", "music_pack": "res://songs/m01_first_watch"}
	assert_eq(StoryRun.pick_music_pack(plain, 7), "res://songs/m01_first_watch", "no list: music_pack as before")


func test_the_rendered_packs_load_as_recorded_music_of_the_whole_chapter() -> void:
	for ch in CHAPTERS:
		var raw := _raw(ch)
		var bars := int(raw["duration_bars"])
		for index in [1, 2]:
			var s := _seed_for(index, raw)
			assert_true(s >= 0, ch)
			var run := StoryRun.create({"music_seed": s}, _path(ch))
			assert_eq(run.errors, [], "%s render %d fits the chapter: %d bars, every sequence has cues" % [ch, index, bars])
			assert_true(run.level.recorded)
			assert_eq(run.level.stems.keys(), ["drums", "bass", "other"])
			for key in run.level.stems:
				assert_eq(int(run.level.stem_loop_bars[key]), bars, "the loop is the whole chapter")
				var st := LevelLoader.load_stream(run.level.stems[key])
				assert_true(st != null, key + " decodes")
				assert_near(st.get_length(), bars * 4.0 * 60.0 / 174.0, 0.1, "%s %s is %d bars long" % [ch, key, bars])
			var t := StemTransport.new()
			tree.root.add_child(t)
			assert_eq(t.load_level(run.level), "")
			assert_near(t.loop_seconds, bars * 4.0 * 60.0 / 174.0, 0.1)
			t.queue_free()
		var first := StoryRun.create({}, _path(ch))
		assert_eq(first.errors, [])
		assert_eq(first.level.recorded, ch == "night_one", ch + ": no seed: the chapter's own pack, unchanged (Night One's own pack is itself a recording)")


func test_the_rendered_packs_play_a_whole_chapter() -> void:
	for ch in CHAPTERS:
		var raw := _raw(ch)
		for index in [1, 2]:
			var s := _seed_for(index, raw)
			var top := StoryRun.autoplay("perfect", 1.0 / 60.0, 1, {"music_seed": s}, _path(ch))
			assert_true(not top.has("errors"), ch + " the chapter loads")
			assert_eq(top["sequences_passed"], top["sequences_total"], "%s render %d: perfect play passes every sequence of the rendered chart" % [ch, index])
			var none := StoryRun.autoplay("none", 1.0 / 60.0, 1, {"music_seed": s}, _path(ch))
			assert_true(none["run"].finished, ch + ": no input plays the whole song")
