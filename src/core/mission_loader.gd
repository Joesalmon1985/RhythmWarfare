class_name MissionLoader
extends RefCounted
## Schema 4 mission packs (songs/<pack>/level.json, written by tools/content/build.py): a mission authors no music. It
## gives the length, the form (which eight-bar phases are drums and which bass), the battlefield and the waves. The
## player's loadout (a clip and sound per slot, from the loop library) decides everything musical: the cues of each
## phase (the loops' cue patterns tiled over the phase), the loop stems the transport plays, the sequences' rewards
## (what each instrument's sound produces) and the per-bar gain program that switches drums and bass.
##
## options: {"loadout": Dictionary, "library": LibraryIndex, "unlocked": Array of library ids, "practice": bool}. A
## wanted loadout that is unknown, locked or incompatible falls back (Loadout.resolve) with a warning, so a stale
## save can never break a mission. Without "unlocked" every library item counts as unlocked.

const SCHEMA_VERSION := 4
const FILL_BAR := 7  # the fill replaces bar 8 of every eight bars (0-based within the loop)
const LOOP_BARS := 8


static func parse(d: Dictionary, pack_dir: String, options: Dictionary, errors: Array, warnings: Array) -> Level:
	var level := Level.new()
	level.pack_dir = pack_dir
	level.schema_version = SCHEMA_VERSION
	level.mode = "defense"
	level.level_id = str(d.get("level_id", ""))
	level.title = str(d.get("title", level.level_id))
	level.campaign_level = int(d.get("number", d.get("campaign_level", 0)))
	level.bpm = float(d.get("bpm", 174))
	level.ticks_per_beat = int(d.get("ticks_per_beat", 960))
	var ts: Array = d.get("time_signature", [4, 4])
	level.beats_per_bar = int(ts[0])
	level.song_offset_ms = int(d.get("song_offset_ms", 0))
	level.duration_ticks = int(d.get("duration_ticks", 0))
	level.seed = int(d.get("seed", 0))
	level.battlefield = str(d.get("battlefield", "defense_02"))
	level.roster = str(d.get("roster", "openra_mvp_01"))
	level.rules = d.get("rules", {})
	level.base = d.get("base", {}) if typeof(d.get("base", {})) == TYPE_DICTIONARY else {}
	level.sequence_threshold = float(d.get("sequence_threshold", 0.6))
	level.sequence_bars = maxi(int(d.get("sequence_bars", 2)), 1)
	level.intro = str(d.get("intro", ""))
	level.intro_bar = int(d.get("intro_bar", 1))
	var intros: Variant = d.get("intros", [])
	level.intros = intros if typeof(intros) == TYPE_ARRAY else []
	if level.intros.is_empty() and not level.intro.is_empty():
		level.intros = [{"bar": level.intro_bar, "text": level.intro}]
	elif level.intro.is_empty() and not level.intros.is_empty():
		level.intro = str(level.intros[0].get("text", ""))
		level.intro_bar = int(level.intros[0].get("bar", 1))
	level.play_mode = "practice" if bool(options.get("practice", false)) else "campaign"
	level.progression = level.play_mode == "campaign"
	if level.level_id.is_empty() or level.duration_ticks <= 0 or level.bpm <= 0.0:
		errors.append("level_id, bpm and duration_ticks are required")
		return level
	var index: LibraryIndex = options.get("library", null)
	if index == null:
		index = LibraryIndex.load_default()
	if index.is_empty():
		errors.append("the loop library is missing (%s); build it with tools/content/build.py" % (index.error if not index.error.is_empty() else "empty index"))
		return level
	var unlocked: Array = options.get("unlocked", []) if options.has("unlocked") else everything(index)
	var wanted: Variant = options.get("loadout", {})
	level.loadout = Loadout.resolve(index, unlocked, wanted if typeof(wanted) == TYPE_DICTIONARY else {}, warnings)
	for id in index.clips:
		level.names[id] = index.name(id)
	for id in index.sounds:
		level.names[id] = index.name(id)
	for p in d.get("phases", []):
		var mode := str(p["mode"])
		var phase := {"id": str(p["id"]), "start_tick": int(p["start_tick"]), "end_tick": int(p["end_tick"]),
			"length_bars": (int(p["end_tick"]) - int(p["start_tick"])) / level.ticks_per_bar(), "mode": mode, "pads": _pads(mode, level.loadout)}
		level.sections.append(phase)
	if level.sections.is_empty():
		errors.append("a mission needs phases")
		return level
	_stems(index, level, errors)
	_cues(index, level, errors)
	_sequences(index, level, errors, warnings)
	_gain_program(level)
	var waves: Variant = d.get("waves", [])
	level.waves = waves if typeof(waves) == TYPE_ARRAY else []
	level.waves.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["start_tick"]) < int(b["start_tick"]))
	return level


## Every clip and sound id of the library (what "nothing is locked" means).
static func everything(index: LibraryIndex) -> Array:
	var out: Array = []
	out.append_array(index.clips.keys())
	out.append_array(index.sounds.keys())
	return out


## The pads of a phase: drums put the kick sound on pad 1 and the snare sound on pad 4; bass uses all four for the bass sound.
static func _pads(mode: String, loadout: Dictionary) -> Dictionary:
	if mode == "drums":
		return {"1": {"family": "kick", "ref": str(loadout["kick_sound"])}, "4": {"family": "snare", "ref": str(loadout["snare_sound"])}}
	var pads := {}
	for b in range(1, 5):
		pads[str(b)] = {"family": "bass", "ref": str(loadout["bass_sound"])}
	return pads


## stem key -> [clip, part, sound] for the loadout; the fill stems only with a fill.
static func stem_sources(lo: Dictionary) -> Dictionary:
	var out := {"kick": [lo["groove"], "kick", lo["kick_sound"]], "snare": [lo["groove"], "snare", lo["snare_sound"]]}
	if not str(lo.get("fill", "")).is_empty():
		out["fill_kick"] = [lo["fill"], "kick", lo["kick_sound"]]
		out["fill_snare"] = [lo["fill"], "snare", lo["snare_sound"]]
	out["bass"] = [lo["bass"], "bass", lo["bass_sound"]]
	out["other"] = [lo["backing"], "other", ""]
	return out


static func _stems(index: LibraryIndex, level: Level, errors: Array) -> void:
	var sources := stem_sources(level.loadout)
	for key in sources:
		var src: Array = sources[key]
		var path := index.loop_path(str(src[0]), str(src[1]), str(src[2]))
		if path.is_empty():
			errors.append("no loop for %s (%s, %s, %s): rebuild the library with tools/content/build.py" % [key, src[0], src[1], src[2]])
			continue
		level.stems[key] = path
		level.stem_family[key] = key.trim_prefix("fill_") if key.begins_with("fill_") else key
		level.stem_loop_bars[key] = index.clip_bars(str(src[0]))


## The cues of the loadout tiled over every phase. A loop is one clip-length of song time starting at tick 0 (the
## stems loop from the song start, so cue and sound stay locked whatever the phase boundaries); a drums phase plays
## the groove's kick and snare cues, with the fill's cues in place of the groove's in bar 8 of every eight when a fill
## is equipped; a bass phase plays the bass line's cues.
static func _cues(index: LibraryIndex, level: Level, errors: Array) -> void:
	var lo := level.loadout
	var tpb := level.ticks_per_bar()
	var raw: Array = []
	for pi in level.sections.size():
		var ph: Dictionary = level.sections[pi]
		var a := int(ph["start_tick"])
		var b := int(ph["end_tick"])
		var plans: Array = []  # [clip, part, sound, family, replace_fill_bar]
		if str(ph["mode"]) == "drums":
			plans.append([lo["groove"], "kick", lo["kick_sound"], "kick", false])
			plans.append([lo["groove"], "snare", lo["snare_sound"], "snare", false])
			if not str(lo.get("fill", "")).is_empty():
				plans.append([lo["fill"], "kick", lo["kick_sound"], "kick", true])
				plans.append([lo["fill"], "snare", lo["snare_sound"], "snare", true])
		else:
			plans.append([lo["bass"], "bass", lo["bass_sound"], "bass", false])
		var has_fill := not str(lo.get("fill", "")).is_empty() and str(ph["mode"]) == "drums"
		for plan in plans:
			var clip := str(plan[0])
			var loop_ticks := index.clip_bars(clip) * tpb
			if loop_ticks <= 0:
				continue
			var is_fill: bool = plan[4]
			var cues := index.cues(clip, str(plan[1]))
			var loops := int(ceil(float(b) / float(loop_ticks)))
			for k in range(a / loop_ticks, loops):
				for c in cues:
					var tick := k * loop_ticks + int(c[0])
					if tick < a or tick >= b:
						continue
					var in_fill_bar := has_fill and (tick / tpb) % LOOP_BARS == FILL_BAR
					if in_fill_bar != is_fill:
						continue  # the groove's bar 8 is replaced by the fill's; the fill sounds only there
					raw.append({"tick": tick, "duration_ticks": int(c[1]), "pad": int(c[2]), "family": str(plan[3]),
						"voice": str(plan[2]), "phase": pi})
	raw.sort_custom(func(x: Dictionary, y: Dictionary) -> bool:
		return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	var i := 0
	for n in raw:
		n["id"] = "c%04d" % i
		n["type"] = "hold" if int(n["duration_ticks"]) > 0 else "tap"
		n["end_tick"] = int(n["tick"]) + int(n["duration_ticks"])
		n["time"] = level.tick_to_seconds(n["tick"])
		n["end_time"] = level.tick_to_seconds(n["end_tick"])
		n["button"] = n["pad"]
		n["lane"] = n["family"]
		n["slot_id"] = n["voice"]
		n["seq"] = -1
		level.notes.append(n)
		i += 1
	if level.notes.is_empty():
		errors.append("the loadout has no cues in this mission")


## Sequences of sequence_bars bars inside each phase (never across a phase). A drums sequence with 0-based drum counter
## k pays the kick instrument's next reward when k is even and the snare instrument's when odd; a bass sequence pays
## the bass instrument's. Each instrument's cycle advances once per use across the whole mission.
static func _sequences(index: LibraryIndex, level: Level, errors: Array, warnings: Array) -> void:
	var lo := level.loadout
	var cycles := {"kick": Loadout.reward_cycle(index, str(lo["kick_sound"])), "snare": Loadout.reward_cycle(index, str(lo["snare_sound"])),
		"bass": Loadout.reward_cycle(index, str(lo["bass_sound"]))}
	var used := {"kick": 0, "snare": 0, "bass": 0}
	var span := level.sequence_bars * level.ticks_per_bar()
	var drum_count := 0
	for pi in level.sections.size():
		var ph: Dictionary = level.sections[pi]
		var a := int(ph["start_tick"])
		var b := int(ph["end_tick"])
		var count := (b - a) / span
		if (b - a) % span != 0:
			warnings.append("phase %s is not a whole number of %d-bar sequences; the last bars hold no sequence" % [ph["id"], level.sequence_bars])
		for k in count:
			var who := "bass"
			if str(ph["mode"]) == "drums":
				who = "kick" if drum_count % 2 == 0 else "snare"
				drum_count += 1
			var cycle: Array = cycles[who]
			var reward := str(cycle[int(used[who]) % cycle.size()])
			used[who] = int(used[who]) + 1
			var seq := {"index": level.sequences.size(), "phase": pi, "mode": str(ph["mode"]), "start_tick": a + k * span,
				"end_tick": a + (k + 1) * span, "reward": reward, "instrument": who}
			seq["start_time"] = level.tick_to_seconds(seq["start_tick"])
			seq["end_time"] = level.tick_to_seconds(seq["end_tick"])
			if MissionRules.reward(reward).is_empty():
				errors.append("sequence %d: unknown reward %s" % [seq["index"], reward])
			level.sequences.append(seq)
	for n in level.notes:
		for s in level.sequences:
			if n["tick"] >= s["start_tick"] and n["tick"] < s["end_tick"]:
				n["seq"] = s["index"]
				if n["end_tick"] > s["end_tick"]:
					errors.append("cue %s holds past the end of its sequence" % n["id"])
				break
		if int(n["seq"]) < 0:
			errors.append("cue %s lies in no sequence" % n["id"])
	for s in level.sequences:
		var count := 0
		for n in level.notes:
			if int(n["seq"]) == int(s["index"]):
				count += 1
		s["cues"] = count
		if count == 0:
			errors.append("sequence %d has no cues" % int(s["index"]))


## The per-bar gain program: which stems sound in each bar. Drums phases play kick and snare (the fill loops instead in
## bar 8 of every eight when a fill is equipped), bass phases play bass; the backing always plays.
static func _gain_program(level: Level) -> void:
	var fill := level.stems.has("fill_kick")
	var tpb := level.ticks_per_bar()
	for bar in level.bar_count():
		var mode := str(level.phase_at(bar * tpb).get("mode", ""))
		var in_fill := fill and mode == "drums" and bar % LOOP_BARS == FILL_BAR
		var prog := {}
		for key in level.stems:
			var on := false
			match key:
				"kick", "snare":
					on = mode == "drums" and not in_fill
				"fill_kick", "fill_snare":
					on = in_fill
				"bass":
					on = mode == "bass"
				"other":
					on = true
			prog[key] = on
		level.gain_program.append(prog)
