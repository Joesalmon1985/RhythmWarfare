class_name StoryJourney
extends RefCounted
## The journey a player took through a chapter's map, from the director's fired actions alone (no scene needed): the places reached in order, the roles held, and a
## short name for the result screen ("Dancer > On stage > DJ"). Pure logic; the stage's own action log gives the same places (StoryStage.journey()).

const NAMES := {"dancer": "Dancer", "on_stage": "On stage", "dj": "DJ", "queasy": "Feeling rough", "sick": "Sick in the cubicle", "recovered": "Recovered", "out": "Out cold"}


## `fired` is StoryDirector.fired ([{t0, bar, action, args}]); `data` the chapter. {} for a chapter without a map.
static func summarize(fired: Array, data: StoryData, bpm: float) -> Dictionary:
	if not FileAccess.file_exists(StoryMap.PATH % data.id):
		return {}
	var map := StoryMap.load_chapter(data.id)
	if not map.errors.is_empty():
		return {}
	return of_actions(expand(fired, data, bpm), map, bpm)


## The fired actions with each ending's own journey actions added (what StoryStage.apply does on "ending").
static func expand(fired: Array, data: StoryData, bpm: float) -> Array:
	var out: Array = []
	for a in fired:
		out.append(a)
		if str(a["action"]) == "ending":
			out.append_array(data.ending_journey(str(a["args"].get("ending", "")), float(a["t0"]), 4.0 * 60.0 / bpm))
	return out


static func of_actions(actions: Array, map: StoryMap, bpm: float) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(map, bpm)
	for a in actions:
		if str(a["action"]).begins_with("player_") or str(a["action"]) in ["fx_queasy", "sick_beat"]:
			p.apply_action(a)
	var places: Array = []
	for ev in p.events():
		if ev["kind"] == "move" and not bool(ev.get("walk", false)):  # strolls inside a room are not places
			places.append(str(ev["to"]))
	var roles: Array = ["dancer"]
	for r in p.role_list():
		if r != roles[roles.size() - 1]:
			roles.append(r)
	var names: Array = []
	for r in roles:
		names.append(NAMES.get(r, r))
	return {"places": places, "roles": roles, "name": " > ".join(PackedStringArray(names))}
