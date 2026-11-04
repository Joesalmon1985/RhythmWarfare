extends TestCase
## WP8 policy matrix (docs/STORY_25D_PLAN.md 8.1), headless: every chapter, eight input policies, seeds 1 to 3. The ending is one of the chapter's, perfect play gets the top
## ending and no input the bottom one, the places the rail camera was sent to match the authored lists (rebuilt here from the chapter file and the outcomes of its decisions),
## the camera stands inside a room at every bar, no authored move overlaps a dense run, and every eight-bar block has a camera beat.

const CHAPTERS := ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]
const POLICIES := ["perfect", "accuracy:0.9", "accuracy:0.8", "accuracy:0.7", "accuracy:0.5", "beginner", "sloppy", "none"]
## The journey under perfect play and under no input, as the chapters author it (places in order, the ending's tableau last).
const TOP := {
	"night_one": ["steps", "stage", "balcony", "booth", "booth"],
	"mothership": ["gallery_in", "reactor_in", "bridge_in", "helm", "helm"],
	"underworld": ["court_in", "throne", "pit_stage", "pit_stage"],
	"hospital": ["corridor_in", "cafe_in", "bandstand", "bandstand"],
	"mental_hospital": ["corridor_in", "art_in", "stage", "stage"],
}
const BOTTOM := {
	"night_one": ["floor_edge", "corridor", "cubicle", "floor_edge", "door"],
	"mothership": ["gallery_in", "medbay", "exam", "medbay", "airlock"],
	"underworld": ["furnace_chains", "cage", "cage"],
	"hospital": ["ward_chair", "quiet", "bed", "bed"],
	"mental_hospital": ["treat", "quiet", "quiet"],
}


func _path(id: String) -> String:
	return "res://content/story/%s.json" % id


func _exists(id: String) -> bool:
	return FileAccess.file_exists(StoryMap.PATH % id) and FileAccess.file_exists(_path(id))


## The journey a chapter file authors for the decision outcomes `outcomes` ({decision id: "good"|"bad"}) and the ending: [[time in bars, waypoint]] sorted by time.
func _authored(raw: Dictionary, outcomes: Dictionary, ending: String) -> Array:
	var moves: Array = []
	var k := 0
	for b in raw["blocks"]:
		for e in b["events"]:
			if str(e["action"]) == "player_move":
				moves.append([float(e["at_bar"]), k, str(e["to"])])
				k += 1
	for d in raw["decisions"]:
		for a in d[outcomes[str(d["id"])]]:
			if typeof(a) == TYPE_DICTIONARY and str(a["action"]) == "player_move":
				moves.append([float(d["at_bar"]) + float(a.get("after_bars", 0.0)), k, str(a["to"])])
				k += 1
	var end_bar := float(raw["duration_bars"]) + 1.0
	for a in raw["endings"][ending].get("journey", []):
		if str(a["action"]) == "player_move":
			moves.append([end_bar + float(a.get("after_bars", 0.0)), k, str(a["to"])])
			k += 1
	moves.sort_custom(func(x: Array, y: Array) -> bool: return x[0] < y[0] if x[0] != y[0] else x[1] < y[1])
	return moves.map(func(m: Array) -> String: return m[2])


func test_every_chapter_under_every_policy() -> void:
	for id in CHAPTERS:
		if not _exists(id):
			continue
		var data: StoryData = StoryData.load_file(_path(id))["data"]
		var map := StoryMap.load_chapter(id)
		var top: String = data.ending_order[0]
		var bottom: String = data.ending_order[2]
		for policy in POLICIES:
			for seed_value in [1, 2, 3]:
				var tag := "%s %s seed %d" % [id, policy, seed_value]
				var r := StoryRun.autoplay(policy, 1.0 / 30.0, seed_value, {}, _path(id))
				assert_false(r.has("errors"), tag + " plays")
				if r.has("errors"):
					continue
				assert_true(str(r["ending"]) in data.ending_order, tag + ": an ending of the chapter")
				if policy == "perfect":
					assert_eq(r["ending"], top, tag + ": the top ending")
				if policy == "none":
					assert_eq(r["ending"], bottom, tag + ": the bottom ending")
				var outcomes := {}
				for b in r["branches"]:
					outcomes[str(b["id"])] = str(b["outcome"])
				var places: Array = r["journey"]["places"]
				assert_eq(places, _authored(data.raw, outcomes, str(r["ending"])), tag + ": the journey is the authored one for these outcomes")
				if policy == "perfect" and TOP.has(id):
					assert_eq(places, TOP[id], tag + ": the top journey")
				if policy == "none" and BOTTOM.has(id):
					assert_eq(places, BOTTOM[id], tag + ": the bottom journey")
				if seed_value == 1:
					_check_camera(map, data, r, tag)


## The rail camera built from the fired actions: inside a room at every bar and on every frame of a move; a camera beat in every eight-bar block.
func _check_camera(map: StoryMap, data: StoryData, r: Dictionary, tag: String) -> void:
	var bpm: float = StoryRun.create({}, _path(data.id)).level.bpm
	var player := StoryPlayer.new()
	player.setup(map, bpm)
	var beats: Dictionary = {}
	for a in r["log"]:
		if str(a["action"]) in ["player_move", "player_look", "player_role", "fx_queasy", "sick_beat"]:
			player.apply_action(a)
		if str(a["action"]) in ["player_move", "player_look"]:
			beats[data.block_of_bar(float(a["bar"]))] = true
	assert_eq(player.errors, [], tag + ": every journey target is reachable")
	var bar_s := 4.0 * 60.0 / bpm
	var t := 0.0
	while t < float(data.duration_bars + 4) * bar_s:
		var pose := player.pose_at(t)
		assert_true(map.sector_at(pose["pos"]) != "", "%s: the camera stands in a room at bar %.1f" % [tag, t / bar_s + 1.0])
		t += bar_s * 0.5
	for k in data.blocks.size():
		assert_true(beats.has(k), "%s: block %d has a camera beat" % [tag, k + 1])


func test_no_authored_move_warns_in_any_chapter() -> void:
	for id in CHAPTERS:
		if not _exists(id):
			continue
		for loadout in [{}, {"difficulty": "hard"}]:
			var run := StoryRun.create(loadout, _path(id))
			assert_eq(run.errors, [], id)
			assert_eq(run.director.warnings, [], "%s %s: no move overlaps a dense run or lasts outside 2 to 4 bars" % [id, str(loadout)])
