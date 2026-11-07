class_name RunCardTable
extends RefCounted
## The day room's card table as the room shows it before and after a game (docs/BLACKJACK_INTEGRATION.md, "The table in the room"; package A8b, ruling 38). The table, its lamp
## and the empty chair are the map's `cards_table` occluder (`world_table_empty.png`, nobody at it, nothing on it); the three players are crowd actors of the day room
## (BlackjackActivity.ACTORS: `cards_dealer`, `cards_a`, `cards_b`, standing at the table) and this directs them through the stage's `people` as the table's hotspot goes:
## `idle` (they play among themselves), `invite` (the table is on show: they beckon), `pleased` (it is touched: happy, a clap), `welcome` (seated, until the game takes them over:
## happy and clapping), `refuse` (waved off: the dealer frowns, the others look, then they invite again). While the player is seated (`seated`) the blackjack activity directs
## them itself (its `people` calls through the world port) and nothing is directed here. `mood_of` is a pure function of song time and the hotspot state.

const OCCLUDER := "cards_table"  # the map's occluder the table is drawn on
const REFUSE_BEATS := 4.0  # the refusal plays over this many beats from the decision, then they invite again
## What each player does in each loop (people states, CONTRACTS.md 10; StoryCrowd resolves them to their sheet's rows or the named fallbacks).
const PEOPLE := {
	"idle": {"dealer": "idle", "npc_a": "idle", "npc_b": "idle"},
	"invite": {"dealer": "beckon", "npc_a": "beckon", "npc_b": "look"},
	"pleased": {"dealer": "happy", "npc_a": "clap", "npc_b": "happy"},
	"welcome": {"dealer": "happy", "npc_a": "clap", "npc_b": "clap"},
	"refuse": {"dealer": "frown", "npc_a": "look", "npc_b": "look"},
}

var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var mood: Dictionary = {"loop": "idle", "t0": 0.0}  # what the table shows now ({loop, t0}; loop "seated": the activity directs the players), set by the run each frame
var now := 0.0  # the song time the mood was set at
var stage: StoryStage = null  # the stage whose crowd holds the players (attach)
var directed: Array = []  # [{t, loop, id, state}] every direction given, for tests and walks
var _last_key := ""


## The table's players are cast in this stage's crowd.
func ok() -> bool:
	if stage == null:
		return false
	for seat: String in BlackjackActivity.ACTORS:
		var found := false
		for rid in stage.crowds:
			found = found or (stage.crowds[rid] as StoryCrowd).actors.has(BlackjackActivity.ACTORS[seat])
		if not found:
			return false
	return true


## True for the hotspot the table's players answer to: the one whose success sits the player at an activity.
static func is_table(h: Dictionary) -> bool:
	return str((h.get("on_success", {}) as Dictionary).get("activity", "")) != ""


## What the players do at song time `t`. `entry`: the table's hotspot_items() entry on show now ({} when it is not on show); `last_commit`: {t, success} of the table's latest
## decision ({} none); `mg_state`: the minigame controller's state ("" | "entering" | "active" | "leaving" | "resuming"). Returns {loop, t0} (t0: when the loop started).
static func mood_of(entry: Dictionary, last_commit: Dictionary, mg_state: String, t: float, p_beat_s: float) -> Dictionary:
	if mg_state == "active" or mg_state == "leaving":
		return {"loop": "seated", "t0": float(last_commit["t"]) if not last_commit.is_empty() else 0.0}  # the game directs them
	if not last_commit.is_empty() and t >= float(last_commit["t"]):
		if bool(last_commit["success"]) and mg_state == "entering":
			return {"loop": "welcome", "t0": float(last_commit["t"])}
		if not bool(last_commit["success"]) and t - float(last_commit["t"]) < REFUSE_BEATS * p_beat_s:
			return {"loop": "refuse", "t0": float(last_commit["t"])}
	if not entry.is_empty():
		if str(entry["state"]) == "selected":
			return {"loop": "pleased", "t0": float(entry["t_state"])}
		return {"loop": "invite", "t0": 0.0}
	return {"loop": "idle", "t0": 0.0}


## The run's mood for song time `t`; a new loop directs the players from `t` (once per change).
func set_mood(m: Dictionary, t: float) -> void:
	mood = m
	now = t
	var key := "%s@%.4f" % [str(m.get("loop", "")), float(m.get("t0", 0.0))]
	if key == _last_key:
		return
	_last_key = key
	var states: Dictionary = PEOPLE.get(str(m.get("loop", "")), {})
	if states.is_empty() or stage == null:
		return
	for seat: String in states:
		var id: String = BlackjackActivity.ACTORS[seat]
		stage.people(id, str(states[seat]), t, 0.0)
		directed.append({"t": t, "loop": str(m["loop"]), "id": id, "state": str(states[seat])})


## The players stand in `stage`'s crowd: the table directs them there from now. Returns 1 when the map has the table's occluder (0 otherwise).
func attach(st: StoryStage) -> int:
	stage = st
	_last_key = ""
	var n := 0
	for rid in st.crowds:
		for p in (st.crowds[rid] as StoryCrowd).props:
			var pr := p as StoryCrowdProp
			if pr.kind == "occluder" and str((pr.get_meta("def", {}) as Dictionary).get("id", "")) == OCCLUDER:
				n = 1
	return n
