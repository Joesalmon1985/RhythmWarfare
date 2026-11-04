extends Node
## Autoload "Session": the mission being set up or played, the player's settings and the last result.

const SETTINGS_PATH := "user://settings.cfg"
const SETTINGS_VERSION := 2
const MIX_VERSION := 2  # settings saved before the quieter battle effects (mix 2) get the default effects volume once

const PLAY_VERSION := 2  # settings saved before the falling notes (play 2) get the default note speed once

const LEAD_IN_MIN_S := 0.6  # the note speed: seconds a note takes to fall from the screen top onto its pad
const LEAD_IN_MAX_S := 2.0
const LEAD_IN_DEFAULT_S := 1.2
const PAD_SIZES := [0.30, 0.36, 0.42]  # share of the screen height the pad strip takes: compact, standard, large
const DEFAULTS := {"calibration_ms": 0.0, "cue_lead_in_s": LEAD_IN_DEFAULT_S, "pad_size": 1, "high_contrast": false,
	"reduced_effects": false, "story_motion": 0, "story_lines": 0, "vibration": true, "music_volume": 1.0, "sfx_volume": 0.5, "show_keys": true}

var campaign: Campaign  # saved progress (user://campaign.json) and the campaign data
var campaign_level_id := ""  # the mission being played ("" for free play and playtests)
var mission_number := 1  # the mission the setup screen shows
var practice := false  # a practice run: same cues and recognition, battlefield hidden, nothing saved
var practice_phase := -1  # practice one phase (index) instead of the whole song
var pack_dir := ""
var chart_id := ""  # schema 1 duel packs only
var battle_on := true  # false: rhythm only (practice and the developer playtest)
var last_result: Dictionary = {}
var story_progress: StoryProgress  # Story Campaign saves (user://story_campaign.json), separate from the military campaign
var story_chapter := "night_one"  # the chapter story_play loads
var story_interlude: Dictionary = {}  # {name, from, to, ending}: the cutscene story_interlude plays before the next chapter
var story_result: Dictionary = {}  # the last finished story set (StoryRun.summary plus the saved record)
var debug := false
var settings_migrated := false

# settings (user://settings.cfg)
var calibration_ms := 0.0
var cue_lead_in_s := LEAD_IN_DEFAULT_S  # how long a note takes to fall onto its pad (the note speed)
var pad_size := 1
var high_contrast := false
var reduced_effects := false
var story_motion := 0  # Story Campaign camera motion: 0 full, 1 reduced (no bob, roll or sway), 2 none (the camera cuts between places)
var story_lines := 0  # Story Campaign internal resolution: index into StoryLowRes.LINE_CHOICES (360p, 270p, 180p)
var vibration := true
var music_volume := 1.0
var sfx_volume := 0.5  # effects (gunfire, explosions, EVA voices) on the "SFX" bus
var show_keys := true  # desktop: the D F J K labels on the pads


func _ready() -> void:
	campaign = Campaign.load_data()
	story_progress = StoryProgress.load_data()
	load_settings()
	if OS.has_environment("RW_PACK"):  # scripted runs and tests pick a pack without touching saved settings
		pack_dir = OS.get_environment("RW_PACK")
	if OS.has_environment("RW_CHART"):
		chart_id = OS.get_environment("RW_CHART")
	if OS.has_environment("RW_BATTLE"):
		battle_on = OS.get_environment("RW_BATTLE") != "off"
	if OS.has_environment("RW_LEAD_IN"):
		cue_lead_in_s = clampf(float(OS.get_environment("RW_LEAD_IN")), LEAD_IN_MIN_S, LEAD_IN_MAX_S)
	if OS.has_environment("RW_MISSION"):  # screenshots and scripted runs open a mission's setup or play screen
		mission_number = int(OS.get_environment("RW_MISSION"))
	if OS.has_environment("RW_STORY_CHAPTER"):  # scripted runs and screenshots open a chapter directly
		story_chapter = OS.get_environment("RW_STORY_CHAPTER")
	if OS.has_environment("RW_PAD_SIZE"):  # 0 compact, 1 standard, 2 large: screenshots of the layouts
		pad_size = clampi(int(OS.get_environment("RW_PAD_SIZE")), 0, PAD_SIZES.size() - 1)
	if OS.has_environment("RW_STORY_MOTION"):  # 0 full, 1 reduced, 2 none: screenshots of the camera setting
		story_motion = clampi(int(OS.get_environment("RW_STORY_MOTION")), 0, 2)
	if OS.get_environment("RW_REDUCED") == "1":
		reduced_effects = true
	if OS.get_environment("RW_HIGH_CONTRAST") == "1":
		high_contrast = true
	if OS.has_environment("RW_CALIBRATION_MS"):
		calibration_ms = float(OS.get_environment("RW_CALIBRATION_MS"))
	apply_volume()


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) != OK:
		return
	calibration_ms = float(cfg.get_value("timing", "calibration_ms", 0.0))
	pack_dir = str(cfg.get_value("play", "pack_dir", ""))
	var version := int(cfg.get_value("meta", "version", 1))
	if version < SETTINGS_VERSION:
		# version 1 had a falling-note approach time (1.2 to 3 s); the pad lead-in is a different measure, so it starts
		# at its default. Calibration and the last pack carry over.
		settings_migrated = true
		save_settings()
		return
	cue_lead_in_s = clampf(float(cfg.get_value("play", "cue_lead_in_s", LEAD_IN_DEFAULT_S)), LEAD_IN_MIN_S, LEAD_IN_MAX_S)
	pad_size = clampi(int(cfg.get_value("play", "pad_size", 1)), 0, PAD_SIZES.size() - 1)
	high_contrast = bool(cfg.get_value("display", "high_contrast", false))
	reduced_effects = bool(cfg.get_value("display", "reduced_effects", false))
	story_motion = clampi(int(cfg.get_value("display", "story_motion", 0)), 0, 2)
	story_lines = clampi(int(cfg.get_value("display", "story_lines", 0)), 0, 2)
	vibration = bool(cfg.get_value("play", "vibration", true))
	music_volume = clampf(float(cfg.get_value("audio", "music_volume", 1.0)), 0.0, 1.0)
	show_keys = bool(cfg.get_value("display", "show_keys", true))
	sfx_volume = clampf(float(cfg.get_value("audio", "sfx_volume", DEFAULTS["sfx_volume"])), 0.0, 1.0)
	if int(cfg.get_value("audio", "mix_version", 1)) < MIX_VERSION:
		sfx_volume = DEFAULTS["sfx_volume"]
		save_settings()
	if int(cfg.get_value("play", "play_version", 1)) < PLAY_VERSION:
		cue_lead_in_s = LEAD_IN_DEFAULT_S
		save_settings()


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("meta", "version", SETTINGS_VERSION)
	cfg.set_value("timing", "calibration_ms", calibration_ms)
	cfg.set_value("play", "pack_dir", pack_dir)
	cfg.set_value("play", "cue_lead_in_s", cue_lead_in_s)
	cfg.set_value("play", "play_version", PLAY_VERSION)
	cfg.set_value("play", "pad_size", pad_size)
	cfg.set_value("play", "vibration", vibration)
	cfg.set_value("display", "high_contrast", high_contrast)
	cfg.set_value("display", "reduced_effects", reduced_effects)
	cfg.set_value("display", "story_motion", story_motion)
	cfg.set_value("display", "story_lines", story_lines)
	cfg.set_value("display", "show_keys", show_keys)
	cfg.set_value("audio", "music_volume", music_volume)
	cfg.set_value("audio", "sfx_volume", sfx_volume)
	cfg.set_value("audio", "mix_version", MIX_VERSION)
	cfg.save(SETTINGS_PATH)


## Back to the defaults (calibration kept unless `include_calibration`).
func reset_settings(include_calibration: bool = false) -> void:
	if include_calibration:
		calibration_ms = 0.0
	cue_lead_in_s = DEFAULTS["cue_lead_in_s"]
	pad_size = DEFAULTS["pad_size"]
	high_contrast = DEFAULTS["high_contrast"]
	reduced_effects = DEFAULTS["reduced_effects"]
	story_motion = DEFAULTS["story_motion"]
	story_lines = DEFAULTS["story_lines"]
	vibration = DEFAULTS["vibration"]
	music_volume = DEFAULTS["music_volume"]
	sfx_volume = DEFAULTS["sfx_volume"]
	show_keys = DEFAULTS["show_keys"]
	apply_volume()
	save_settings()


## The Story Campaign's effective camera motion: the setting, but never less calm than reduced effects (which imply reduced motion).
func effective_story_motion() -> int:
	return maxi(story_motion, 1 if reduced_effects else 0)


func apply_volume() -> void:
	var music_bus := StemTransport.ensure_music_bus()
	AudioServer.set_bus_volume_db(music_bus, -80.0 if music_volume <= 0.001 else linear_to_db(music_volume))
	var sfx_bus := BattleSfx.ensure_bus()
	AudioServer.set_bus_volume_db(sfx_bus, -80.0 if sfx_volume <= 0.001 else linear_to_db(sfx_volume))


## Set up a campaign (or practice) run of mission `number`. The loadout is global (Campaign.loadout()).
func start_mission(number: int, p_practice: bool, phase: int = -1) -> void:
	var data := campaign.level_data(number)
	mission_number = number
	pack_dir = campaign.pack_dir(number)
	chart_id = ""
	practice = p_practice
	practice_phase = phase if p_practice else -1
	battle_on = not p_practice
	campaign_level_id = str(data.get("level_id", ""))
	if not campaign_level_id.is_empty():
		campaign.progress["last_played"] = campaign_level_id
		campaign.save()


## The player's loadout, resolved against the library and what is unlocked.
func loadout() -> Dictionary:
	return campaign.loadout()


func library() -> LibraryIndex:
	return LibraryIndex.load_default()


## Song packs shipped inside the project plus any the player dropped into user://songs.
func available_packs() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for root: String in ["res://songs", "user://songs"]:
		var dir := DirAccess.open(root)
		if dir == null:
			continue
		dir.list_dir_begin()
		var name := dir.get_next()
		while not name.is_empty():
			if dir.current_is_dir() and not name.begins_with("."):
				var pack: String = root.path_join(name)
				var json: String = pack.path_join("level.json")
				if FileAccess.file_exists(json):
					var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(json))
					var title := name
					var schema := 1
					if typeof(parsed) == TYPE_DICTIONARY:
						title = str(parsed.get("title", name))
						schema = int(parsed.get("schema_version", 1))
					out.append({"dir": _globalize(pack), "title": title, "name": name, "schema": schema})
			name = dir.get_next()
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["name"] < b["name"])
	return out


static func _globalize(path: String) -> String:
	# Packs inside res:// must stay res:// paths in exports (files are packed), so only user:// is globalized.
	if path.begins_with("user://"):
		return ProjectSettings.globalize_path(path)
	return path
