class_name TestCase
extends RefCounted
## Base class for headless tests. Methods named test_* run in order; assertions record failures without halting.

var failures: Array[String] = []
var checks := 0
var tree: SceneTree
var _current := ""


func set_current(name: String) -> void:
	_current = name


func fail(message: String) -> void:
	failures.append("%s: %s" % [_current, message])


func assert_true(cond: bool, message: String = "") -> void:
	checks += 1
	if not cond:
		fail("expected true. %s" % message)


func assert_false(cond: bool, message: String = "") -> void:
	checks += 1
	if cond:
		fail("expected false. %s" % message)


func assert_eq(actual: Variant, expected: Variant, message: String = "") -> void:
	checks += 1
	if actual != expected:
		fail("expected %s, got %s. %s" % [str(expected), str(actual), message])


func assert_near(actual: float, expected: float, tolerance: float, message: String = "") -> void:
	checks += 1
	if absf(actual - expected) > tolerance:
		fail("expected %f within %f, got %f. %s" % [expected, tolerance, actual, message])


func assert_contains(haystack: Variant, needle: Variant, message: String = "") -> void:
	checks += 1
	var found := false
	if typeof(haystack) == TYPE_STRING:
		found = str(haystack).contains(str(needle))
	elif typeof(haystack) == TYPE_ARRAY:
		for item in haystack:
			if str(item).contains(str(needle)):
				found = true
				break
	if not found:
		fail("expected to find %s in %s. %s" % [str(needle), str(haystack), message])


## Project-root absolute path for test fixtures and song packs.
static func project_path(rel: String) -> String:
	return ProjectSettings.globalize_path("res://").path_join(rel)


const FIXTURE_LIBRARY := "tests/fixtures/library_fixture/index.json"
const FIXTURE_PACK := "tests/fixtures/pack_v4"


## The tiny fixture library (two grooves, one fill, two bass lines, two backings; see tests/fixtures/make_library_fixture.py).
static func fixture_index() -> LibraryIndex:
	return LibraryIndex.load_from(project_path(FIXTURE_LIBRARY))


## The fixture mission (four eight-bar phases "drums drums bass drums" on village_01) built with the fixture library and
## the fixture defaults changed by `changes`; null (and an error printed) when it does not load.
static func fixture_level(changes: Dictionary = {}, practice: bool = false) -> Level:
	var idx := fixture_index()
	var lo: Dictionary = idx.defaults.duplicate()
	for k in changes:
		lo[k] = changes[k]
	var loaded := LevelLoader.load_pack(project_path(FIXTURE_PACK), {"library": idx, "loadout": lo, "practice": practice})
	if loaded["level"] == null:
		push_error("fixture mission rejected: " + str(loaded["errors"]))
	return loaded["level"]
