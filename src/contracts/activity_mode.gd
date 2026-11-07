class_name ActivityMode
extends RefCounted
## The rhythm participation of an activity (docs/parallel-development/CONTRACTS.md sections 4 and 5). Pure data: the host reads `rules()` and does what the
## row says; nothing here touches the engine. An activity's mode is the `mode` key of its content/minigames/<id>.json ("rhythm" when absent, so the
## blackjack table keeps today's behaviour).

enum Mode { RHYTHM, REPLACE, OVERLAY }

const NAMES := ["rhythm", "replace", "overlay"]

## The owners a tap can have (section 5). Exactly one per tap.
const OWNERS := ["pads", "hotspots", "world_regions", "activity_controls", "activity_view", "hud", "trial"]


static func parse(name: Variant) -> int:
	var i := NAMES.find(str(name) if name != null else "rhythm")
	return i if i >= 0 else -1


static func name_of(mode: int) -> String:
	return NAMES[mode] if mode >= 0 and mode < NAMES.size() else ""


## The mode named by an activity config ({} or no `mode`: rhythm). -1 for an unknown name.
static func of_config(config: Dictionary) -> int:
	return parse(config.get("mode", "rhythm"))


## What the host does while an activity of `mode` is seated (from beat 0 of the seat block until the resume boundary). The brief's table (section 7) plus
## the engine consequences. Keys:
##   pads: "active" | "replaced"           the pad strip plays, or the activity's 2 or 4 controls stand where the pads were
##   stage_input: owner of a tap in the stage area ("activity_view" | "world_regions")
##   strip_input: owner of a tap in the pad strip ("pads" | "activity_controls")
##   judging: bool                         cues are charted and judged
##   energy: bool                          block results move the crowd energy (and can deplete it)
##   wobble_fall: bool                     MinigameController counts failed blocks into wobble and a fall
##   rhythm_to_activity: bool              block results and judge events are forwarded to the activity (race speed)
##   rail: "held"                          the journey is not fed (all three modes; engine.hold)
##   route: "held"                         no hotspot commit, no scene departure (engine.hold)
##   resume: "now" | "boundary"            on exit: judging was never stopped, or resumes on a clean block boundary after a lead-in
static func rules(mode: int) -> Dictionary:
	match mode:
		Mode.RHYTHM:
			return {"pads": "active", "stage_input": "activity_view", "strip_input": "pads", "judging": true, "energy": true, "wobble_fall": true,
				"rhythm_to_activity": false, "rail": "held", "route": "held", "resume": "now"}
		Mode.REPLACE:
			return {"pads": "replaced", "stage_input": "activity_view", "strip_input": "activity_controls", "judging": false, "energy": false, "wobble_fall": false,
				"rhythm_to_activity": false, "rail": "held", "route": "held", "resume": "boundary"}
		Mode.OVERLAY:
			return {"pads": "active", "stage_input": "world_regions", "strip_input": "pads", "judging": true, "energy": true, "wobble_fall": false,
				"rhythm_to_activity": true, "rail": "held", "route": "held", "resume": "now"}
	return {}
