class_name TrackFocus
extends RefCounted
## Which voice the player is playing at a given moment, as plain logic with no nodes: the focus stretches of a track
## pack (docs/TRACK_PACK_FORMAT.md), the tempo that turns seconds into beats, and what the display should announce.
## A stretch covers its start up to, not including, its end, so at the boundary between two stretches the later one
## is current. Between stretches (and before the first, after the last) nothing is current.

## The announcement of a change starts this many beats before the next stretch begins.
const ANNOUNCE_BEATS := 8.0
const EPS := 1e-6

var stretches: Array = []  # [{start_s, end_s, voice}] in time order
var bpm := 120.0


## `p_stretches` are the pack's focus stretches (in time order), `p_bpm` the tempo (a beat is 60 / bpm seconds).
func setup(p_stretches: Array, p_bpm: float) -> void:
	stretches = p_stretches
	bpm = p_bpm


func beat_s() -> float:
	return 60.0 / bpm


## Index of the stretch holding second `t`, or -1 in a gap, before the first stretch or after the last.
func index_at(t: float) -> int:
	for i in stretches.size():
		if t >= float(stretches[i]["start_s"]) and t < float(stretches[i]["end_s"]):
			return i
	return -1


## The stretch holding second `t` ({} when there is none).
func stretch_at(t: float) -> Dictionary:
	var i := index_at(t)
	return stretches[i] if i >= 0 else {}


## The key of the voice being played at `t` ("" when there is nothing to play).
func voice_at(t: float) -> String:
	return str(stretch_at(t).get("voice", ""))


## The next stretch that starts after `t` ({} when there is none). When `t` is inside a stretch this is the one after it.
func next_stretch(t: float) -> Dictionary:
	for s in stretches:
		if float(s["start_s"]) > t:
			return s
	return {}


## How many beats from `t` until the next stretch starts (-1.0 when there is none).
func beats_until_next(t: float) -> float:
	var n := next_stretch(t)
	if n.is_empty():
		return -1.0
	return (float(n["start_s"]) - t) / beat_s()


## What to announce at `t`: {showing, voice, beats, count}. It shows from 8 beats ahead of a stretch whose voice differs
## from the one being played, or that follows a gap (nothing is being played, or the current stretch ends before it
## begins). `beats` is the exact distance, `count` the whole number to display (rounded up, 8 down to 1).
func announcement(t: float) -> Dictionary:
	var none := {"showing": false, "voice": "", "beats": -1.0, "count": 0}
	var n := next_stretch(t)
	if n.is_empty():
		return none
	var beats := (float(n["start_s"]) - t) / beat_s()
	if beats > ANNOUNCE_BEATS + EPS:
		return none
	var cur := stretch_at(t)
	var change := cur.is_empty() or str(cur["voice"]) != str(n["voice"]) or float(n["start_s"]) > float(cur["end_s"]) + EPS
	if not change:
		return none
	return {"showing": true, "voice": str(n["voice"]), "beats": beats, "count": clampi(ceili(beats - EPS), 1, int(ANNOUNCE_BEATS))}
