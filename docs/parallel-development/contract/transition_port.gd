class_name TransitionPort
extends RefCounted
## The one interface between the narrative / interaction side and the music side of the run.
##
## THIS FILE IS THE CONTRACT. It lives in docs/parallel-development/contract/ and is copied, byte for byte, to
## src/transition/transition_port.gd by each implementation branch as its first commit. Nobody edits the copy.
## A change is a contract amendment: made to this file on main by the owner or the integration session, then
## merged by both branches. docs/parallel-development/INTEGRATION_CONTRACT.md explains every member.
##
## Two implementations exist:
##   TransitionDirector      src/transition/transition_director.gd   the real one (music side, Windows PC)
##   MockTransitionDirector  tests/mocks/mock_transition_director.gd  virtual clock, no audio (Ubuntu laptop)
##
## Narrative code talks only to this class. Music code learns about destinations only through this class.

const VERSION := 1

## Life of one request. Terminal states: CLOSED (before the lock) and COMPLETED.
enum State { NONE, PENDING, LOCKED, SWITCHED, COMPLETED, CLOSED }

## Reasons, as StringName. Refusal / close reasons:
##   &"replaced"     a newer request took the slot
##   &"cancelled"    cancel() was called
##   &"locked"       a transition is already locked; no request is taken until it has switched
##   &"invalid"      the destination dictionary is malformed
##   &"unavailable"  the destination could not be loaded or validated before the lock
## Defer reasons: &"not_ready" (destination still loading), &"blending" (the last blend has not completed),
##   &"doors_closed" (this lap is not a departure lap), &"held" (a minigame holds the scene).
## Plan modes: &"blend", &"halftime_blend", &"echo_out", &"cut" (today's behaviour, always available).

## ---------------------------------------------------------------- signals (emitted by the director)

## Answer to request(). accepted=false carries the refusal reason; the id is then dead.
signal request_acknowledged(id: int, accepted: bool, reason: StringName)
## The destination's scene data and music are loaded. Informational; may never fire if loading is instant.
signal destination_ready(id: int)
## A pending request ended without a transition (replaced, cancelled, unavailable).
signal request_closed(id: int, reason: StringName)
## A lock point passed with a request pending, but the scene will not change at this boundary. The request
## stays PENDING and is tried again at next_boundary_t.
signal deferred(id: int, next_boundary_t: float, reason: StringName)
## The lock point of boundary_t was reached: the transition will happen and can no longer be cancelled or
## replaced. dest is the destination actually taken (the request's "on_miss" destination if the last block
## was missed). plan describes the musical transition (see INTEGRATION_CONTRACT.md, "Plan").
signal locked(id: int, dest: Dictionary, boundary_t: float, plan: Dictionary)
## Song time reached the boundary and the scene has changed. landed is the scene really entered: equal to
## the locked dest, or a fallback scene with landed["fallback"] == true if the destination failed after the
## lock. Route state is written from landed, in this signal, and nowhere earlier.
signal switched(id: int, landed: Dictionary, t: float)
## The outgoing music is silent; the transition is over. Always fires exactly once after switched.
signal completed(id: int)
## The beat length changed (a scene at another tempo began at song time t).
signal tempo_changed(bpm: float, beat_s: float, t: float)

## ---------------------------------------------------------------- requests (called by the narrative side)

## Ask to go to dest at the next departure boundary. Returns the request id (> 0), or 0 if refused at once
## (the reason arrives in request_acknowledged with id 0 and is also returned by last_refusal()).
## A new request replaces the pending one. dest: see INTEGRATION_CONTRACT.md, "Destination".
func request(_dest: Dictionary) -> int:
	push_error("TransitionPort.request is abstract")
	return 0

## Withdraw a pending request (the player deselected). True if it was pending; false once locked.
func cancel(_id: int) -> bool:
	push_error("TransitionPort.cancel is abstract")
	return false

## The destination used when the scene's final lap locks with nothing pending. Set on every scene entry.
## An empty dictionary means "stay": the scene goes on for another lap.
func set_default(_dest: Dictionary) -> void:
	push_error("TransitionPort.set_default is abstract")

## The current request: {"id": int, "dest": Dictionary, "state": State, "ready": bool}, or {} when NONE.
func current() -> Dictionary:
	return {}

func state() -> int:
	return State.NONE

func last_refusal() -> StringName:
	return &""

## ---------------------------------------------------------------- the musical clock (read by both sides)

## Seconds on the run's authoritative clock. Never goes backwards; continuous across scene changes.
func song_time() -> float:
	return 0.0

## Length of one beat of the current scene, in seconds, and its tempo.
func beat_s() -> float:
	return 0.0

func bpm() -> float:
	return 0.0

## Beat within the current 64-beat lap, 0.0 <= b < 64.0.
func lap_beat() -> float:
	return 0.0

## Song time of the next boundary at which this scene can be left, or INF if none is scheduled yet.
func next_boundary_t() -> float:
	return INF

## Song time of the lock point belonging to that boundary. Never assume a fixed number of beats.
func lock_t(_boundary_t: float) -> float:
	return INF

## True from the moment requests are taken in this scene until the lock (the "selection is open" time).
func selection_open() -> bool:
	return false
