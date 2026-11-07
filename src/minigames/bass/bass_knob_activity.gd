class_name BassKnobActivity
extends MinigameActivity
## Puzzle one of the bedsit raves (docs/briefs/BEDSIT_RAVES_BRIEF.md section 4, CONTRACTS.md 4 and 7): the DJ deck's bass knob is stuck. Rhythm mode (ruling 37: the pads stay live and the
## judging goes on): the player touches the knob; it resists twice (a visible wobble, a strained frame) and the third touch frees it (config `resist_turns`, 3). The knob frames are a sprite
## sheet of four: stuck, straining, free, up (assets/story/mothership/textures/sr_knob_0..3.png, placeholder art). The activity is a pure function of the touches so far and song time.
##
## (No view: ruling 38. The touch is a world region over the knob's screen point, SpaceRaveHost.hit.)
## The change the world shows (the stage lights, the crowd dancing) and the audio (the bass stem unlocked at the next bar line) are the host's: SpaceRaveHost reads `freed_t` from `state()`
## the frame the knob comes free and schedules both, so they land together on the bar. The result sets `rave.<theme>.bass_fixed` (and a run flag the deck's hotspot hides itself by).

const FRAME_STUCK := 0
const FRAME_STRAIN := 1
const FRAME_FREE := 2
const FRAME_UP := 3
const STRAIN_BEATS := 0.6
const FREE_BEATS := 1.0
const RISE_BEATS := 2.0
const HOLD_BEATS := 3.0  # the knob stays up this long (a happy deck) before the activity is done

var turns := 0
var last_tap_t := -100.0
var freed_t := -1.0
var _now := 0.0
var _theme := "space"


func begin(t: float) -> void:
	super.begin(t)
	_now = t


func update(t: float) -> void:
	_now = t
	if freed_t >= 0.0 and not _done and t >= freed_t + HOLD_BEATS * beat_s:
		_finish("done")


func targets() -> Array:
	return [] if _done else ["knob"] + exit_targets()


func tap(target: String, t: float) -> bool:
	if _done:
		return false
	if is_exit_target(target):
		request_leave(t)
		return true
	if target != "knob" or freed_t >= 0.0:
		return false
	turns += 1
	last_tap_t = t
	if turns >= int(config.get("resist_turns", 3)):
		freed_t = t
	return true


func request_leave(t: float) -> void:
	_finish("done" if freed_t >= 0.0 else "left")


func frame_at(t: float) -> int:
	if freed_t >= 0.0:
		return FRAME_FREE if t < freed_t + FREE_BEATS * beat_s else FRAME_UP
	return FRAME_STRAIN if t - last_tap_t < STRAIN_BEATS * beat_s else FRAME_STUCK


## How far the knob is turned up, 0 stuck .. config `knob_target` once it is free and has risen.
func level_at(t: float) -> float:
	if freed_t < 0.0:
		return 0.0
	return float(config.get("knob_target", 0.85)) * clampf((t - freed_t) / (RISE_BEATS * beat_s), 0.0, 1.0)


## The wobble of the knob (-1..1): a decaying shake after a resisting touch.
func wobble_at(t: float) -> float:
	var age := (t - last_tap_t) / beat_s
	if freed_t >= 0.0 or age < 0.0 or age > 1.5:
		return 0.0
	return sin(age * TAU * 3.0) * (1.0 - age / 1.5)


func state() -> Dictionary:
	var s := super.state()
	s.merge({"turns": turns, "frame": frame_at(_now), "level": level_at(_now), "wobble_amt": wobble_at(_now), "freed_t": freed_t, "freed": freed_t >= 0.0, "need": int(config.get("resist_turns", 3))})
	return s


func result() -> Dictionary:
	var theme := str(config.get("theme", _theme))
	var flags: Array = []
	if _reason == "done":
		for f: Variant in config.get("flags_on_complete", ["rave.{theme}.bass_fixed"]):
			flags.append(str(f).replace("{theme}", theme))
	var r := super.result()
	r["activity_id"] = "bass_knob"
	r["flags_to_set"] = flags
	r["score"] = turns
	r["t_fixed"] = freed_t
	return r


## Ruling 38 / contract 10: the activity draws nothing. Its things are dynamic props of the room (the knob: a sprite sheet of four frames, `frame` set from the state machine in song time);
## the host/stage draws them in the room's light (StoryWorld.set_dynamic_things when it lands; until then SpaceRaveHost poses the map's own `bass_knob` thing by `thing_pose`).
func things() -> Array:
	var wob := wobble_at(_now) * 0.012
	return [{"id": "bass_knob", "sprite": "sr_knob", "at": [KNOB_AT.x + wob, KNOB_AT.y], "sector": "stage", "size": [0.2, 0.2], "frame": frame_at(_now)}]


## The people of the activity, directed through the crowd (contract 10): the DJ waits at the stuck knob and cheers when it is free.
func people() -> Array:
	return [{"id": "dj", "state": "cheer" if freed_t >= 0.0 else "waiting", "t0": freed_t if freed_t >= 0.0 else 0.0}]


## The knob's place on the map (the deck's middle, content/story/maps/space_rave.json thing `bass_knob`) and the radius of its tap region in metres.
const KNOB_AT := Vector2(0.0, -25.12)
const KNOB_TAP_M := 0.45
