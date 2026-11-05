class_name TrackTestKit
extends RefCounted
## Helpers shared by the track mode tests: the fixture pack, temporary packs built from it with one rule broken, and a
## frame-stepped driver for TrackGame.

const FIXTURE_REL := "tests/fixtures/track_fixture"


static func fixture_dir() -> String:
	return TestCase.project_path(FIXTURE_REL)


static func fixture_pack() -> TrackPack:
	var r := TrackPack.load_pack(fixture_dir())
	assert(r["pack"] != null, "the fixture pack must load: " + str(r["errors"]))
	return r["pack"]


static func temp_root() -> String:
	return OS.get_user_data_dir().path_join("track_tests")


## Writes a copy of the fixture to a temporary folder named `id`, with the parsed track.json changed by `mutate`
## (a Callable taking the Dictionary), and returns the folder. `extra_files` is {relative path: source path} copied in.
static func make_pack(mutate: Callable, id: String = "track_fixture", extra_files: Dictionary = {}) -> String:
	var folder := temp_root().path_join(id)
	DirAccess.make_dir_recursive_absolute(folder.path_join("stems"))
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fixture_dir().path_join("track.json")))
	if mutate.is_valid():
		mutate.call(data)
	for k in ["drums", "lead", "pads", "bass", "backing"]:
		DirAccess.copy_absolute(fixture_dir().path_join("stems/%s.ogg" % k), folder.path_join("stems/%s.ogg" % k))
	for rel in extra_files:
		DirAccess.copy_absolute(str(extra_files[rel]), folder.path_join(rel))
	var f := FileAccess.open(folder.path_join("track.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(data, " "))
	f.close()
	return folder


## A game on the fixture. `from_s` skips the cues before it.
static func game(chart: String = "", from_s: float = 0.0, pack: TrackPack = null) -> TrackGame:
	var g := TrackGame.new()
	g.setup(pack if pack != null else fixture_pack(), chart, from_s)
	return g


## Plays `g` from its start second to `t_end` in steps of `dt` with the autoplay policy; `skip` leaves cues out.
## Returns the game (finish() is not called: the caller decides).
static func run(g: TrackGame, policy: String, t_end: float, dt: float = 1.0 / 60.0, skip: Callable = Callable()) -> TrackGame:
	var a := TrackAutoplay.new()
	a.setup(g.cues, policy, skip)
	var t := g.start_s
	while t < t_end:
		a.step(g, t)
		g.advance(t)
		t += dt
	a.step(g, t_end)
	g.advance(t_end)
	return g


static func events_of(g: TrackGame, kind: String, pad: int = 0) -> Array:
	var out: Array = []
	for e in g.log:
		if e["kind"] == kind and (pad == 0 or int(e["pad"]) == pad):
			out.append(e)
	return out


static func voice(summary: Dictionary, key: String) -> Dictionary:
	for v in summary["voices"]:
		if v["key"] == key:
			return v
	return {}
