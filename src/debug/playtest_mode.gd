class_name PlaytestMode
extends RefCounted
## The Debug / Playtest switch (docs/DEBUG_MODE.md). It is ON after the home screen's "Debug / Playtest" button has opened the scene list, or for a whole launch with RW_DEBUG=1. While it is on, the
## run shows the playtest overlay (the identity of what plays and what is drawn, the phase clock, the feedback buttons) and the pause panel offers "Back to scene list". Regular play never sees
## any of it: the silent HUD (docs/THREE_PATHS_AND_FACES_PLAN.md D3) is a separate thing and is not touched (the overlay is its own node, and only exists while this is on).
##
## A scene started from the list plays in a THROWAWAY save (user://playtest_run_save.json) so debugging never marks levels reached in the owner's real progress; the real save is put back when
## the home screen is shown again. The options below are what the list's toggles set (statics: they live as long as the app).

const LIST_SCENE := "res://src/debug/playtest_list.tscn"
const NOTES_SCENE := "res://src/debug/playtest_notes_screen.tscn"
const HOME_SCENE := "res://src/scenes/main_menu.tscn"
const RUN_SCENE := "res://src/run/run_play.tscn"
const SANDBOX_SAVE := "user://playtest_run_save.json"
const ENERGY_CHOICES := [["Run's own start (60)", -1.0], ["Full (100)", 100.0], ["Low (25)", 25.0]]

static var active := false  # chosen from the menu
static var dev_text := false  # also bring back the old play text (title cards, captions, the numeric countdown): DevText.on()
static var continue_run := true  # a finished scene goes on into the next one, as the game would; false: back to the list at the end of the scene
static var autoplay := false  # the pads are played by the test bot (RW_RUN_BOT=perfect): hear the whole arrangement without playing
static var give_flags := true  # the world-state flags the scene's hotspots need are set, so every hotspot of the scene is on offer
static var energy_choice := 0  # index into ENERGY_CHOICES
static var overlay_shown := true  # the corner panel and the feedback buttons (hidden: only the small toggle stays)
static var arrangement := 0  # 0: each scene's arrangement as the game picks it (the per-run seed); 1 to 3: the scene's 1st, 2nd or 3rd arrangement (RunData.arrangement_override)

static var list_scroll := 0  # the list's scroll position across the reload an option change makes

static var _launch := {}
static var _real_progress: RunProgress = null


## Every switch back to its default (the tests, and the home screen).
static func reset_options() -> void:
	set_arrangement(0)
	dev_text = false
	continue_run = true
	autoplay = false
	give_flags = true
	energy_choice = 0
	overlay_shown = true


## The arrangement choice (every main-run scene has three arrangements of its music family and the game picks one by the per-run seed, so a heard song changes from run to run).
static func set_arrangement(choice: int) -> void:
	arrangement = clampi(choice, 0, 3)
	RunData.arrangement_override = arrangement - 1


static func on() -> bool:
	return active or OS.get_environment("RW_DEBUG") == "1"


static func start_energy() -> float:
	return float((ENERGY_CHOICES[clampi(energy_choice, 0, ENERGY_CHOICES.size() - 1)] as Array)[1])


## Debug mode begins: the list is about to open. The real run save is set aside and a fresh throwaway one used until `end_session`.
static func begin_session() -> void:
	active = true
	if _real_progress == null and Session.run_progress != null:
		_real_progress = Session.run_progress
		if FileAccess.file_exists(SANDBOX_SAVE):
			DirAccess.remove_absolute(SANDBOX_SAVE)
		Session.run_progress = RunProgress.load_data(SANDBOX_SAVE, "user://none.json")


## Debug mode ends (the home screen is shown): the real save comes back and the switches reset. RW_DEBUG=1 keeps `on()` true regardless.
static func end_session() -> void:
	set_arrangement(0)
	active = false
	dev_text = false
	overlay_shown = true
	_launch = {}
	if _real_progress != null:
		Session.run_progress = _real_progress
		_real_progress = null
		if FileAccess.file_exists(SANDBOX_SAVE):
			DirAccess.remove_absolute(SANDBOX_SAVE)


## Everything a start needs, without changing the scene: the run machinery's own start (Session.run_start_node / run_start_path, what RW_RUN_START and RW_RUN_PATH set) and the options.
static func prepare(run_id: String, scene_id: String) -> void:
	Session.run_start_node = scene_id
	Session.run_start_path = PlaytestCatalog.path_of(run_id)
	_launch = {"run": run_id, "scene": scene_id, "energy": start_energy(), "autoplay": autoplay, "continue_run": continue_run, "give_flags": give_flags}


## Starts the game at a scene (the list's row).
static func start(tree: SceneTree, run_id: String, scene_id: String) -> void:
	begin_session()
	prepare(run_id, scene_id)
	tree.change_scene_to_file(RUN_SCENE)


## What the run scene reads once when it starts: {} unless the start came from the list.
static func consume_launch() -> Dictionary:
	var l := _launch
	_launch = {}
	return l


static func open_list(tree: SceneTree) -> void:
	begin_session()
	tree.change_scene_to_file(LIST_SCENE)


static func back_to_list(tree: SceneTree) -> void:
	_launch = {}
	begin_session()
	tree.change_scene_to_file(LIST_SCENE)
