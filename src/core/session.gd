extends Node
## Autoload "Session": the selected song pack, player settings (calibration) and the last result.

const SETTINGS_PATH := "user://settings.cfg"

var pack_dir := ""
var calibration_ms := 0.0
var last_result: Dictionary = {}
var debug := false


func _ready() -> void:
	load_settings()


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) == OK:
		calibration_ms = float(cfg.get_value("timing", "calibration_ms", 0.0))
		pack_dir = str(cfg.get_value("play", "pack_dir", ""))


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("timing", "calibration_ms", calibration_ms)
	cfg.set_value("play", "pack_dir", pack_dir)
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
					if typeof(parsed) == TYPE_DICTIONARY:
						title = str(parsed.get("title", name))
					out.append({"dir": _globalize(pack), "title": title, "name": name})
			name = dir.get_next()
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["name"] < b["name"])
	return out


static func _globalize(path: String) -> String:
	# Packs inside res:// must stay res:// paths in exports (files are packed), so only user:// is globalized.
	if path.begins_with("user://"):
		return ProjectSettings.globalize_path(path)
	return path
