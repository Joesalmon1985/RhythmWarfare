extends Node
## Autoload "Session": the selected song pack, player settings (calibration) and the last result.

const SETTINGS_PATH := "user://settings.cfg"

const LOOKAHEAD_MIN_S := 1.2
const LOOKAHEAD_MAX_S := 3.0

var pack_dir := ""
var chart_id := ""  # schema 2: which chart of the pack to play ("" = the pack's first)
var battle_on := true  # false: the rhythm-only playtest (battlefield hidden, no waves)
var loadout: Dictionary = {}  # schema 2: slot id -> profile id chosen on the loadout screen ({} = pack default)
var lookahead_s := 2.2  # note approach window; a readability setting, independent of tempo and calibration
var calibration_ms := 0.0
var last_result: Dictionary = {}
var debug := false


func _ready() -> void:
	load_settings()
	if OS.has_environment("RW_PACK"):  # scripted runs and tests pick a pack without touching saved settings
		pack_dir = OS.get_environment("RW_PACK")
	if OS.has_environment("RW_CHART"):
		chart_id = OS.get_environment("RW_CHART")
	if OS.has_environment("RW_BATTLE"):
		battle_on = OS.get_environment("RW_BATTLE") != "off"
	if OS.has_environment("RW_LOOKAHEAD"):
		lookahead_s = clampf(float(OS.get_environment("RW_LOOKAHEAD")), LOOKAHEAD_MIN_S, LOOKAHEAD_MAX_S)
	if OS.has_environment("RW_CALIBRATION_MS"):
		calibration_ms = float(OS.get_environment("RW_CALIBRATION_MS"))


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) == OK:
		calibration_ms = float(cfg.get_value("timing", "calibration_ms", 0.0))
		pack_dir = str(cfg.get_value("play", "pack_dir", ""))
		lookahead_s = clampf(float(cfg.get_value("play", "lookahead_s", 2.2)), LOOKAHEAD_MIN_S, LOOKAHEAD_MAX_S)


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("timing", "calibration_ms", calibration_ms)
	cfg.set_value("play", "pack_dir", pack_dir)
	cfg.set_value("play", "lookahead_s", lookahead_s)
	cfg.save(SETTINGS_PATH)


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
					var charts: Array = []
					if typeof(parsed) == TYPE_DICTIONARY:
						title = str(parsed.get("title", name))
						schema = int(parsed.get("schema_version", 1))
						for c in parsed.get("charts", []):
							charts.append({"chart_id": str(c.get("chart_id", "")), "play_mode": str(c.get("play_mode", "")), "notes": c.get("notes", []).size()})
					out.append({"dir": _globalize(pack), "title": title, "name": name, "schema": schema, "charts": charts})
			name = dir.get_next()
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["name"] < b["name"])
	return out


static func _globalize(path: String) -> String:
	# Packs inside res:// must stay res:// paths in exports (files are packed), so only user:// is globalized.
	if path.begins_with("user://"):
		return ProjectSettings.globalize_path(path)
	return path
