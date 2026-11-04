extends TestCase
## A chapter may list `music_packs` (content/story/<chapter>.json): its own recording first, then pre-rendered arrangements (tools/content/arrange.py render, songs/story_<chapter>_<n>).
## StoryRun picks one by a seed (none = the first, so every existing test and tool is unchanged); the rendered pack plays through the normal recorded-music path.

const MOTHERSHIP := "res://content/story/mothership.json"
const RENDERED := "res://songs/story_mothership_1"


func _seed_for(index: int, raw: Dictionary) -> int:
	for s in range(0, 200):
		if StoryRun.pick_music_pack(raw, s) == str((raw["music_packs"] as Array)[index]):
			return s
	return -1


func test_the_pick_is_the_first_without_a_seed_and_deterministic_with_one() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MOTHERSHIP))
	var packs: Array = raw["music_packs"]
	assert_true(packs.size() >= 2)
	assert_eq(StoryRun.pick_music_pack(raw, -1), packs[0], "no seed: the chapter's own recording")
	var seen := {}
	for s in range(0, 40):
		var a := StoryRun.pick_music_pack(raw, s)
		assert_eq(StoryRun.pick_music_pack(raw, s), a)
		seen[a] = true
	assert_eq(seen.keys().size(), packs.size(), "every listed pack is reachable by some seed")
	var plain: Dictionary = {"id": "x", "music_pack": "res://songs/m01_first_watch"}
	assert_eq(StoryRun.pick_music_pack(plain, 7), "res://songs/m01_first_watch", "no list: music_pack as before")
	var night: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/night_one.json"))
	assert_eq(StoryRun.pick_music_pack(night, 3), str(night["music_pack"]), "Night One keeps its recording")


func test_the_rendered_pack_loads_as_recorded_music_of_the_whole_chapter() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MOTHERSHIP))
	assert_eq((raw["music_packs"] as Array)[1], RENDERED)
	var s := _seed_for(1, raw)
	assert_true(s >= 0)
	var run := StoryRun.create({"music_seed": s}, MOTHERSHIP)
	assert_eq(run.errors, [], "the rendered pack fits the chapter: 80 bars, every sequence has cues")
	assert_true(run.level.recorded)
	assert_eq(run.level.stems.keys(), ["drums", "bass", "other"])
	for key in run.level.stems:
		assert_eq(int(run.level.stem_loop_bars[key]), 80, "the loop is the whole chapter")
		var st := LevelLoader.load_stream(run.level.stems[key])
		assert_true(st != null, key + " decodes")
		assert_near(st.get_length(), 80.0 * 4.0 * 60.0 / 174.0, 0.1, key + " is 80 bars long")
	var t := StemTransport.new()
	tree.root.add_child(t)
	assert_eq(t.load_level(run.level), "")
	assert_near(t.loop_seconds, 80.0 * 4.0 * 60.0 / 174.0, 0.1)
	t.queue_free()
	var first := StoryRun.create({}, MOTHERSHIP)
	assert_eq(first.errors, [])
	assert_false(first.level.recorded, "no seed: the chapter's own pack, unchanged")


func test_the_rendered_pack_plays_a_whole_chapter() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MOTHERSHIP))
	var s := _seed_for(1, raw)
	var top := StoryRun.autoplay("perfect", 1.0 / 60.0, 1, {"music_seed": s}, MOTHERSHIP)
	assert_true(not top.has("errors"), "the chapter loads")
	assert_eq(top["sequences_passed"], top["sequences_total"], "perfect play passes every sequence of the rendered chart")
	var none := StoryRun.autoplay("none", 1.0 / 60.0, 1, {"music_seed": s}, MOTHERSHIP)
	assert_true(none["run"].finished, "no input plays the whole song")
