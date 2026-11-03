class_name Loadout
extends RefCounted
## The player's one loadout, applied to every mission: {groove, fill, kick_sound, snare_sound, bass, bass_sound, backing}
## (library ids; fill may be ""). Helpers to resolve a wanted loadout against the library and the unlocked items.

const SLOTS := ["groove", "fill", "kick_sound", "snare_sound", "bass", "bass_sound", "backing"]
const CLIP_SLOTS := ["groove", "fill", "bass", "backing"]


## True when `id` may be picked: "" (no fill), a default (always unlocked) or an unlocked id.
static func is_available(index: LibraryIndex, unlocked: Array, id: String) -> bool:
	return id.is_empty() or index.defaults.values().has(id) or unlocked.has(id)


## A complete, compatible, unlocked loadout from the wanted one. Slot by slot in SLOTS order a wanted id is kept when
## it exists, is unlocked and fits the picks so far; else the default, else the first compatible unlocked id. Every
## fallback of a slot the caller asked for is said in `warnings`.
static func resolve(index: LibraryIndex, unlocked: Array, wanted: Dictionary, warnings: Array) -> Dictionary:
	var out := {}
	for slot: String in SLOTS:
		var options := _available(index, unlocked, slot, _probe(index, unlocked, slot, out, wanted))
		var want := str(wanted.get(slot, ""))
		var pick := ""
		if options.has(want) and (not want.is_empty() or slot == "fill"):
			pick = want
		else:
			var def := str(index.defaults.get(slot, ""))
			if options.has(def):
				pick = def
			elif not options.is_empty():
				pick = str(options[0])
			elif slot != "fill":
				warnings.append("loadout %s: nothing in the library fits" % slot)
			if wanted.has(slot) and want != pick:
				warnings.append("loadout %s: %s is not available here, using %s" % [slot, want if not want.is_empty() else "none", pick if not pick.is_empty() else "none"])
		out[slot] = pick
	return out


## The picks the compatibility of `slot` is judged against: the picks so far, and for the fill the wanted kick and
## snare sounds when they fit the groove (so a fill never costs the player a sound they chose).
static func _probe(index: LibraryIndex, unlocked: Array, slot: String, picks: Dictionary, wanted: Dictionary) -> Dictionary:
	var probe := picks.duplicate()
	if slot == "fill":
		for s in ["kick_sound", "snare_sound"]:
			var w := str(wanted.get(s, ""))
			if not w.is_empty() and index.compatible(s, {"groove": picks.get("groove", "")}).has(w) and is_available(index, unlocked, w):
				probe[s] = w
	return probe


static func _available(index: LibraryIndex, unlocked: Array, slot: String, probe: Dictionary) -> Array:
	var out: Array = []
	for id in index.compatible(slot, probe):
		if is_available(index, unlocked, str(id)):
			out.append(str(id))
	return out


## Whether `d` is a complete loadout whose every pick fits the others (unlocks are not considered).
static func is_valid(index: LibraryIndex, d: Dictionary) -> bool:
	for slot: String in SLOTS:
		if not d.has(slot):
			return false
		if not index.compatible(slot, d).has(str(d[slot])):
			return false
	return true


## The rewards a sound's instrument hands out in turn: the shares expanded in order (2 rifle squads then 1 grenadier
## squad gives [rifle_squad, rifle_squad, grenadier_squad]); a sound that produces nothing repairs.
static func reward_cycle(index: LibraryIndex, sound: String) -> Array:
	var out: Array = []
	for p in index.produces(sound):
		for _i in maxi(int(round(float(p.get("share", 1)))), 0):
			out.append(str(p["reward"]))
	if out.is_empty():
		out.append("repair")
	return out


## Every library id the loadout names (clips and sounds), for the unlock checks.
static func ids(d: Dictionary) -> Array:
	var out: Array = []
	for slot: String in SLOTS:
		var id := str(d.get(slot, ""))
		if not id.is_empty():
			out.append(id)
	return out
