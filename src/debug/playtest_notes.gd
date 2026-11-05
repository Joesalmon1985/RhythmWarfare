class_name PlaytestNotes
extends RefCounted
## The playtest notes file (docs/DEBUG_MODE.md): one entry per press of "Don't like the MUSIC / VISUALS", "Like it" or a typed note, appended to two files in the app's user folder,
## `playtest_notes.md` (to read and paste back) and `playtest_notes.jsonl` (one JSON object per line, for tools/run/playtest_notes_summary.py). Each entry names the scene, the phase clock,
## the packs and the stem / MIDI files that were playing (exactly as the owner's files are named), whether the music is a placeholder, and the visual ids.

const MD_NAME := "playtest_notes.md"
const JSONL_NAME := "playtest_notes.jsonl"
const VERDICTS := {
	"music_dislike": "DON'T LIKE THE MUSIC",
	"visual_dislike": "DON'T LIKE THE VISUALS",
	"like": "LIKE IT",
	"note": "NOTE",
}

static var dir := "user://"  # the tests point this at a folder of their own


static func md_path() -> String:
	return dir.path_join(MD_NAME)


static func jsonl_path() -> String:
	return dir.path_join(JSONL_NAME)


## Where the files really are on this machine (shown on the notes screen).
static func real_dir() -> String:
	return ProjectSettings.globalize_path(dir)


static func timestamp() -> String:
	var d := Time.get_datetime_dict_from_system()
	return "%04d-%02d-%02d %02d:%02d:%02d" % [int(d["year"]), int(d["month"]), int(d["day"]), int(d["hour"]), int(d["minute"]), int(d["second"])]


## The entry for a press. `info` is PlaytestCatalog.scene_info of the scene on screen, `live` the clock {phase, block, stage, stage_label, beat, energy, section, pack, chart_pack, t}.
static func make_entry(info: Dictionary, live: Dictionary, verdict: String, text := "") -> Dictionary:
	var a: Dictionary = info.get("audio", {})
	var v: Dictionary = info.get("visual", {})
	var live_pack := str(live.get("pack", ""))
	var stems := {}
	var charts := {}
	var label := ""
	for s in a.get("sections", []):
		if str(s["pack"]) == live_pack or (live_pack == "" and stems.is_empty()):
			live_pack = str(s["pack"])
			label = str((s["audio"] as Dictionary).get("label", ""))
			for key in (s["audio"] as Dictionary)["voices"]:
				stems[key] = str(s["audio"]["voices"][key]["file"])
			charts = (s["chart"] as Dictionary).get("charts", {}).duplicate()
	return {"ts": timestamp(), "verdict": verdict, "run": str(info.get("run", "")), "scene": str(info.get("id", "")), "scene_title": str(info.get("title", "")), "world": str(info.get("world", "")),
		"phase": int(live.get("phase", 0)), "block": int(live.get("block", 0)), "stage": str(live.get("stage_label", "")), "beat": snappedf(float(live.get("beat", 0.0)), 0.1), "song_t": snappedf(float(live.get("t", 0.0)), 0.01),
		"bpm": int(info.get("bpm", 0)), "energy": snappedf(float(live.get("energy", 0.0)), 0.1),
		"packs": a.get("packs", []), "pack_playing": live_pack, "pack_label": label, "stems": stems, "charts": charts, "source": str(a.get("source", "")), "temporary": bool(a.get("temporary", false)),
		"arrangement": str(a.get("arrangement", "")), "tier": int(a.get("tier", 0)),
		"visual": {"map": str(v.get("map", "")), "view": str(v.get("view", "")), "sector": str(v.get("sector", "")), "light": str(v.get("time_of_day", "")), "pieces_on": v.get("pieces_on", []),
			"cast": v.get("cast", []), "hotspots": (v.get("hotspots", []) as Array).map(func(h: Dictionary) -> String: return str(h["id"]))},
		"text": text}


## One entry as the readable block of the .md file.
static func entry_markdown(e: Dictionary) -> String:
	var lines: Array = []
	lines.append("## %s   %s" % [str(e.get("ts", "")), str(VERDICTS.get(str(e.get("verdict", "")), str(e.get("verdict", ""))))])
	lines.append("- run: %s   scene: %s (%s)   world: %s" % [str(e.get("run", "")), str(e.get("scene", "")), str(e.get("scene_title", "")), str(e.get("world", ""))])
	lines.append("- clock: phase %d, block %d, stage \"%s\", beat %.1f, %d BPM, energy %.0f" % [int(e.get("phase", 0)), int(e.get("block", 0)), str(e.get("stage", "")), float(e.get("beat", 0.0)), int(e.get("bpm", 0)), float(e.get("energy", 0.0))])
	lines.append("- music: %s (%s)   %s%s" % [str(e.get("pack_playing", "")), str(e.get("pack_label", "")), str(PlaytestCatalog.SOURCE_LABELS.get(str(e.get("source", "")), str(e.get("source", "")))), "   [TEMPORARY]" if bool(e.get("temporary", false)) else ""])
	lines.append("  - packs in this scene: %s   tier %d%s" % [", ".join(PackedStringArray(e.get("packs", []))), int(e.get("tier", 0)), ("   arrangement " + str(e["arrangement"])) if str(e.get("arrangement", "")) != "" else ""])
	var st: Dictionary = e.get("stems", {})
	for pair in PlaytestCatalog.VOICES:
		if st.has(str(pair[0])):
			lines.append("  - %s: %s" % [str(pair[1]), str(st[str(pair[0])])])
	var ch: Dictionary = e.get("charts", {})
	if not ch.is_empty():
		lines.append("  - cues: drums %s, bass %s" % [str(ch.get("drums", "?")), str(ch.get("bass", "?"))])
	var vis: Dictionary = e.get("visual", {})
	lines.append("- visual: map %s, view %s, sector %s, %s; pieces on: %s; cast: %s; hotspots: %s" % [str(vis.get("map", "")), str(vis.get("view", "")), str(vis.get("sector", "")), str(vis.get("light", "")),
		", ".join(PackedStringArray(vis.get("pieces_on", []))), ", ".join(PackedStringArray(vis.get("cast", []))), ", ".join(PackedStringArray(vis.get("hotspots", [])))])
	if str(e.get("text", "")) != "":
		lines.append("- note: %s" % str(e["text"]))
	return "\n".join(PackedStringArray(lines)) + "\n"


## Appends one entry to both files. False when a file could not be written.
static func append(e: Dictionary) -> bool:
	DirAccess.make_dir_recursive_absolute(dir)
	var ok := true
	var md_new := not FileAccess.file_exists(md_path())
	var f := FileAccess.open(md_path(), FileAccess.READ_WRITE if not md_new else FileAccess.WRITE)
	if f == null:
		ok = false
	else:
		if md_new:
			f.store_string("# Rhythm Warfare playtest notes\n\nOne entry per press. Paste this file back to Claude, or run tools/run/playtest_notes_summary.py on playtest_notes.jsonl.\n\n")
		else:
			f.seek_end()
		f.store_string(entry_markdown(e) + "\n")
		f.close()
	var j_new := not FileAccess.file_exists(jsonl_path())
	var g := FileAccess.open(jsonl_path(), FileAccess.READ_WRITE if not j_new else FileAccess.WRITE)
	if g == null:
		ok = false
	else:
		if not j_new:
			g.seek_end()
		g.store_string(JSON.stringify(e) + "\n")
		g.close()
	return ok


## Every entry in the .jsonl file, oldest first (a line that does not parse is skipped).
static func read_all() -> Array:
	var out: Array = []
	if not FileAccess.file_exists(jsonl_path()):
		return out
	for line in FileAccess.get_file_as_string(jsonl_path()).split("\n", false):
		var v: Variant = JSON.parse_string(line)
		if typeof(v) == TYPE_DICTIONARY:
			out.append(v)
	return out


static func count() -> int:
	return read_all().size()


## The whole readable file (for "Copy all").
static func all_markdown() -> String:
	return FileAccess.get_file_as_string(md_path()) if FileAccess.file_exists(md_path()) else ""


static func all_jsonl() -> String:
	return FileAccess.get_file_as_string(jsonl_path()) if FileAccess.file_exists(jsonl_path()) else ""


## Removes both files (the tests' clean-up; there is no button for it).
static func delete_files() -> void:
	for p in [md_path(), jsonl_path()]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)


## One line per entry for the notes screen, newest first: "14:03:22  MUSIC -  jordan.baptism  gospel_bethlehem  PLACEHOLDER".
static func summary_line(e: Dictionary) -> String:
	var tag: String = {"music_dislike": "MUSIC -", "visual_dislike": "VISUAL -", "like": "LIKE", "note": "NOTE"}.get(str(e.get("verdict", "")), str(e.get("verdict", "")))
	return "%s   %s   %s/%s   %s   %s%s" % [str(e.get("ts", "")).substr(11), tag, str(e.get("run", "")), str(e.get("scene", "")), str(e.get("pack_playing", "")),
		str(PlaytestCatalog.SOURCE_TAGS.get(str(e.get("source", "")), "")), ("   \"" + str(e["text"]) + "\"") if str(e.get("text", "")) != "" else ""]
