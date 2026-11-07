class_name RunTrackAudio
extends Node
## Track scenes, the audio half (docs/RUN_TRACK_SCENES.md "Audio"): a whole recorded track (a TrackPack's separated stems) plays as ONE synchronised group under a track scene, instead of the
## scene's loops. A child of RunAudio, which owns the song clock and hands it every engine event (`on_event`) and its own frame step (`step`), so the group is scheduled on exactly the clock and
## the lateness rule the loop voices use. RunPlay talks to it only through the few functions under "the interface"; so will the DJ transition engine (src/transition, stage M2).
##
## - The group: on `track_start` every stem of the pack (voices, then backing) starts in one AudioStreamSynchronized (TrackTransport) at track time `track_t` on song time `t`, started late by as
##   much as the call is late (the loop voices' rule, RunAudio._start_voice), at the pack's gains, on the bus RunTrack (a hard limiter, then the Music bus; the loops' buses are not touched). It
##   plays on across laps with no restart. `track_wrap` seeks it to the entry bar on its downbeat. `track_end` fades it over the run's phase fade (mix.phase_fade_s) from its downbeat, while the
##   next scene's music starts there on its own; any scene that begins without a track (the next ordinary scene, and the Bassment, which sends no track_end) fades it too. `depleted` fades it with
##   the run.
## - Mutes: RunTrackMutes, fed with the judge's events about the scene's cues; a voice's stem ramps to silence and back over 30 ms (StemTransport.RAMP_S). Backing never mutes.
## - The hotspot "dip": the stems that are not drums (the pitched voices and the backing) sink to mix.dip_gain for mix.dip_beats of the track's beat, ramped over mix.ramp_s. The riser and the fall
##   at the window, the world treatments and the bass tone bus are NOT applied to a track (see the report in docs/TRACK_SCENES_HANDOVER.md): they are built for the loops' drum and bass buses.
## - Loading: `prefetch_for` decodes the stems of the packs a scene can lead to on worker threads (AudioStreamOggVorbis.load_from_file) when its doors first open, and keeps only those and the
##   one playing; `prepare` does the same for the run's first scene and waits for it (before the countdown). `is_ready` is the engine's gate (RunEngine.track_gate): a pack whose stems are not
##   decoded when the engine first needs the scene makes it an ordinary scene for that visit. `warm` makes the scene plans (track.json parsing) on a thread, so the engine never parses on a frame.

##
## TRANSITIONS (stage M2.4, docs/music/TRANSITIONS_BUILT.md). Every group plays on one of two SLOT buses (RunTrackA, RunTrackB: a high-pass and a delay, both off, then RunTrack with its limiter),
## the slots alternating, so the group of the scene before can carry on as a TAIL with its own rate and effects while the next one plays. TransitionDirector hands every locked transition to
## `prepare_transition(T, recipe)` (through RunAudio): the recipe of TransitionPlanner, plus `in` (the incoming track scene's {node, track, dir, entry_t, beat_s}) and `out` (the outgoing one's).
## - THE START (every track scene entered through a lock, `cut` included). A group started on the frame of its downbeat lands one or two mix periods later than the lateness rule says (WASAPI:
##   8.0 or 18.7 ms; docs/music/TRANSITION_SPIKE.md section 6). So the incoming group starts at the lock, about a second early and MUTED, at `entry_t - (T - x)`; every frame its playhead is read
##   against the clock's under AudioServer.lock, and the error is absorbed by a small pitch_scale on the still-muted group (at most CORRECT_MAX_RATE), back to exactly 1.0 two mix periods before T;
##   it is unmuted just before T (its own lead-in, a few ms, under the outgoing music) and the engine's track_start at T finds it running and only adopts it. A start that cannot be prepared (a
##   lock later than PREP_MIN_S before T, the run's first scene, the return from the Bassment) starts at T by the lateness rule as before.
## - THE TAIL (blend, halftime_blend, echo_out). At T the outgoing group is not faded: its player's pitch_scale becomes the recipe's rate (its bars on the incoming bars), its level steps to
##   recipe.tail_gain_db, every stem follows the recipe's fade as a function of song time (TrackTransport.set_tail_gain, every frame, so a pause freezes it), the slot's high-pass rises (and for
##   echo_out its delay is on). At the recipe's floor_t (complete_t) it stops whatever the curves say, its slot's effects go off and are made afresh (no echo left in the delay line), and it is
##   freed: RunAudio then reports the silence. The incoming group is never rate-changed while it can be heard.

const BUS := "RunTrack"
const LIMIT_CEILING_DB := -0.3
const SLOT_BUSES := ["RunTrackA", "RunTrackB"]
const FX_HIGHPASS := 0  # effect indices on a slot bus
const FX_DELAY := 1
const TAIL_MODES := [&"blend", &"halftime_blend", &"echo_out"]
const PREP_MIN_S := 0.15  # a prepared start needs at least this long before T to be measured and corrected
const CORRECT_MAX_RATE := 0.10  # the muted group's pitch_scale stays within 1 +- this while it is pulled onto the clock
const CORRECT_DEADBAND_S := 0.00005  # under 0.05 ms of error the group plays at exactly 1.0
const SILENCE_GAIN := 0.001  # -60 dB: a tail stem under it is silent

## Tests: () -> [clock position, group playhead] for a group ({} -> the real readings); the mix period (s) to assume (-1: the engine's).
var position_fn: Callable = Callable()
var period_override := -1.0
var _preps: Array = []  # [{t (the boundary T), recipe, group, skip, unmuted, tail, err_ms, final_ms, readings}] the locked transitions not yet over

var run_audio: RunAudio  # the parent: the clock, the music bus, the run's fade
var notes_fn: Callable = Callable()  # () -> Array: the run's cues (engine.level.notes), which the mute rule reads
var log: Array = []  # {kind: start | seek | end | fade | stop | mute | restore | dip | not_ready | unloaded, t, ...} (tests and the walks read it)
var load_log: Array = []  # {track, dir, ms, stems, ok, error} one per decoded pack
var fade_s := 0.6
var ramp_s := 0.35
var dip_gain := 0.55
var dip_beats := 6.0

var _schedule: Array = []
var _seq := 0
var _groups: Array = []  # {transport: TrackTransport, node, track, dir, t0, track_t0, beat_s, fading, mutes: RunTrackMutes, slot, pending (started muted for a boundary, not adopted yet), tail (its recipe, or {})}
var _cache: Dictionary = {}  # pack folder -> {state: loading | ready | failed, track, pack, job, task, keep}
var _tasks: Array = []  # worker tasks not yet waited for (decodes and warms)
var _pinned: Dictionary = {}  # pack folder -> true: kept by _retain (request_scene with pin, the director's destinations)
## Stem locks (CONTRACTS.md 7, hooks H7.1 and H7.2): track id -> [stem keys] locked on every group made for that track (a rave whose bass is not fixed yet). Set by the
## host before the scene starts (`lock_stems`); `unlock_stem_at` frees one on song time with a ramp, the stream never stops.
var stem_locks: Dictionary = {}


# --- the interface ------------------------------------------------------------------------------------------------------------

## Locks `keys` of `track` on every group made for it from now (the group already playing too). The lock is availability, apart from the mix: StemTransport.set_stem_locked.
func lock_stems(track: String, keys: Array) -> void:
	var list: Array = stem_locks.get(track, [])
	for k: Variant in keys:
		if not list.has(str(k)):
			list.append(str(k))
	stem_locks[track] = list
	for g in _groups:
		if str(g["track"]) == track:
			for k: Variant in keys:
				(g["transport"] as TrackTransport).set_stem_locked(str(k), true)


## Unlocks stem `key` at song time `t` (ContractShapes.unlock_time: a bar line), rising over `ramp_s` (H7.2): scheduled on the song-time schedule like every other
## item, so a pause holds it; the playing group's stem comes in where the stream is (no restart), and later groups of the track are made unlocked.
func unlock_stem_at(key: String, t: float, ramp_s: float) -> void:
	_add({"t": t, "kind": "unlock", "key": key, "ramp_s": ramp_s})


## The run's mix settings (fade, ramp, dip) from its run.json `mix`.
func configure(cfg: Dictionary) -> void:
	var m: Dictionary = cfg.get("mix", {})
	fade_s = float(m.get("phase_fade_s", fade_s))
	ramp_s = float(m.get("ramp_s", ramp_s))
	dip_gain = float(m.get("dip_gain", dip_gain))
	dip_beats = float(m.get("dip_beats", dip_beats))
	_ensure_bus()


## The engine's gate (RunEngine.track_gate): true when the plan's stems are decoded and in memory. False is logged; the scene then plays as an ordinary scene for this visit.
func is_ready(plan: Dictionary) -> bool:
	_poll()
	var e: Dictionary = _cache.get(str(plan.get("dir", "")), {})
	var ok := not e.is_empty() and str(e["state"]) == "ready"
	if not ok:
		log.append({"kind": "not_ready", "node": str(plan.get("node", "")), "track": str(plan.get("track", "")), "state": str(e.get("state", "none"))})
	return ok


## The run's first scene: its pack is decoded on a worker thread and waited for here, before the countdown (no frame of play waits). Returns the milliseconds it took (0 when it is no track scene).
func prepare(data: RunData, node_id: String) -> float:
	var p := _plan(data, node_id)
	if p.is_empty():
		return 0.0
	var t0 := Time.get_ticks_usec()
	_retain([p])
	var e: Dictionary = _cache[str(p["dir"])]
	if str(e["state"]) == "loading":
		WorkerThreadPool.wait_for_task_completion(int(e["task"]))
		_tasks.erase(int(e["task"]))
		_finish(e)
	return float(Time.get_ticks_usec() - t0) / 1000.0


## The doors of scene `node_id` open (its first route window): the packs of the scenes it can lead to are decoded ahead on worker threads (its routes, a portal's path's first scene, the way back
## to the Warehouse), and every other pack but the one playing is let go. `paths`: path id -> RunData read ahead (RunPlay's portal cache); `main`: the main run's data when a path is played.
func prefetch_for(data: RunData, node_id: String, paths: Dictionary = {}, main: RunData = null) -> void:
	if not data.nodes.has(node_id):
		return
	var plans: Array = []
	for e in data.nodes[node_id]["next"]:
		var to := str(e["to"])
		if data.nodes.has(to):
			plans.append(_plan(data, to))
		elif to == RunEngine.LEAVE_ROUTE and main != null and main.nodes.has("warehouse"):
			plans.append(_plan(main, "warehouse"))
	for h in data.hotspots_of(node_id):
		var r := str((h.get("on_success", {}) as Dictionary).get("route", ""))
		var pid := HotspotContract.path_of(r)
		if pid != "" and paths.has(pid) and (paths[pid] as RunData).errors.is_empty():
			var pd: RunData = paths[pid]
			plans.append(_plan(pd, pd.start_node()))
		elif r == RunEngine.LEAVE_ROUTE and main != null and main.nodes.has("warehouse"):
			plans.append(_plan(main, "warehouse"))
	_retain(plans.filter(func(p: Dictionary) -> bool: return not p.is_empty()))


## Loads the stems of scene `node_id` ahead, at any time, without letting anything go (safe for a pack already loading or loaded). Returns its state: "" (no track scene), loading, ready or failed.
## `pin`: the pack is also kept when the doors of a scene open (prefetch_for lets go of every pack but those of the routes and the one playing) until release_pins(): the director pins
## the destinations it was asked for (the pending request, its on_miss, the default), at most three packs besides the routes' and the playing one.
func request_scene(data: RunData, node_id: String, pin := false) -> String:
	var p := _plan(data, node_id)
	if p.is_empty():
		return ""
	if pin:
		_pinned[str(p["dir"])] = true
	_request(p)
	return state_of(p)


## Lets the pinned packs go back to the ordinary rule (they stay in memory until the next prefetch_for lets them go).
func release_pins() -> void:
	_pinned.clear()


## The state of a plan's stems: "none" (not asked for), loading, ready or failed.
func state_of(plan: Dictionary) -> String:
	_poll()
	return str((_cache.get(str(plan.get("dir", "")), {}) as Dictionary).get("state", "none"))


## Makes every scene plan of these runs on a worker thread (RunTrackScenes.warm), so that RunEngine.track_plan_of never parses a track.json on a frame.
func warm(datas: Array) -> void:
	var list: Array = datas.filter(func(d: Variant) -> bool: return d != null and (d as RunData).track_scenes != null)
	if list.is_empty():
		return
	_tasks.append(WorkerThreadPool.add_task(func() -> void:
		for d in list:
			(d as RunData).track_scenes.warm()))


## The pause menu ends the holds at judge time `t`: a hold let go then mutes nothing.
func note_pause(t: float) -> void:
	for g in _groups:
		(g["mutes"] as RunTrackMutes).ignore_let_go_at(t)


## The live track for overlays and tests: {node, track, dir, t0, track_t0, muted: [voice keys], position (the group's playhead, track seconds)}; {} when none plays.
func live() -> Dictionary:
	var g := _live()
	if g.is_empty():
		return {}
	var tr: TrackTransport = g["transport"]
	return {"node": g["node"], "track": g["track"], "dir": g["dir"], "t0": g["t0"], "track_t0": g["track_t0"], "muted": (g["mutes"] as RunTrackMutes).muted_keys(),
		"position": tr.player.get_playback_position() if tr.player.playing else -1.0}


## Packs in memory now: {folder: state}.
func cached() -> Dictionary:
	var out := {}
	for d in _cache:
		out[d] = str(_cache[d]["state"])
	return out


func active_group_count() -> int:
	return _groups.size()


# --- RunAudio's side ----------------------------------------------------------------------------------------------------------

## An engine event (RunAudio.on_event hands it every one): the track's start, wrap and end, the scene changes, the judge (mutes), a dip, the end of the run.
func on_event(ev: Dictionary) -> void:
	match str(ev["kind"]):
		"track_start":
			_add({"t": float(ev["t"]), "kind": "start", "ev": ev})
		"track_wrap":
			_add({"t": float(ev["t"]), "kind": "seek", "track_t": float(ev["track_t"]), "node": str(ev["node"])})
		"track_end":
			if str(ev.get("reason", "")) != "depleted":  # (the run's own fade, below, takes the track down with the rest)
				_add({"t": float(ev["t"]), "kind": "end", "reason": str(ev.get("reason", "")), "node": str(ev["node"])})
		"phase_start":
			if not ev.has("track"):  # a scene without a track begins (an ordinary scene, the Bassment): a track still playing fades from its downbeat
				_add({"t": float(ev["t"]), "kind": "end", "reason": "scene", "node": str(ev.get("node", ""))})
			if not _preps.is_empty():
				_add({"t": float(ev["t"]), "kind": "scene", "track": str(ev.get("track", ""))})  # (a group started muted for another scene at this boundary goes)
		"depleted":
			_add({"t": float(ev["t"]), "kind": "end", "reason": "depleted", "seconds": float(ev.get("fade_s", fade_s)), "node": str(ev.get("node", ""))})
		"hotspot_commit":
			if str((ev.get("outcome", {}) as Dictionary).get("music", "")) == "dip":
				var g := _live()
				var bs := float(g["beat_s"]) if not g.is_empty() else 0.0
				if bs > 0.0:
					_add({"t": float(ev["t"]), "kind": "dip", "on": true})
					_add({"t": float(ev["t"]) + dip_beats * bs, "kind": "dip", "on": false})
		"judge":
			_on_judge(ev["event"])


## One frame of RunAudio (song time `now` of the sound reaching the listener, `ttnm` the time to the next mix): the locked transitions move on (a muted start, its correction, the unmute, the tail,
## its fades and floor), due items run, idle restores come back, finished loads are taken, faded groups go.
func step(now: float, ttnm: float) -> void:
	_step_preps(now, ttnm)
	while not _schedule.is_empty() and float(_schedule[0]["t"]) <= now + ttnm:
		run_item(_schedule.pop_front(), now, ttnm)
	_step_tails(now + ttnm)
	var g := _live()
	if not g.is_empty() and notes_fn.is_valid():
		_apply(g, (g["mutes"] as RunTrackMutes).advance(now, notes_fn.call()))
	_poll()
	for x in _groups.duplicate():
		var tr: TrackTransport = x["transport"]
		if bool(x["fading"]) and tr._fade_master <= 0.0001:
			_free_group(x)


## Runs one scheduled item as if the frame were at `now` with `ttnm` to the next mix (the tests call it on a virtual clock). The stems start as far into the track as the call is late: the loops'
## rule (now + ttnm, RunAudio._start_voice), measured on the Dummy driver to put a group on the running clock (tests/fixtures/track_scenes/measure_track_audio.gd). `chunk_t` (given): the song time
## to start from instead (start_with_clock: 0, the clock's own start); `late` may then be negative, the group starting that much earlier in the track.
func run_item(item: Dictionary, now: float, ttnm: float, chunk_t: float = NAN) -> void:
	var t := float(item["t"])
	var late := (chunk_t - t) if not is_nan(chunk_t) else maxf(now + ttnm - t, 0.0)
	match str(item["kind"]):
		"start":
			if not _adopt(item["ev"], t, now + ttnm):
				_start(item["ev"], t, late)
		"scene":
			_drop_orphans(t, str(item.get("track", "")))
		"unlock":
			var key := str(item["key"])
			for tk in stem_locks:
				(stem_locks[tk] as Array).erase(key)
			var n := 0
			for x in _groups:
				var trx: TrackTransport = x["transport"]
				if trx.is_stem_locked(key):
					trx.set_stem_locked(key, false, float(item["ramp_s"]))
					n += 1
			log.append({"kind": "unlock", "t": t, "key": key, "ramp_s": float(item["ramp_s"]), "groups": n, "lateness_ms": late * 1000.0})
		"seek":
			var g := _live()
			if not g.is_empty():
				var tr: TrackTransport = g["transport"]
				tr.player.play(maxf(float(item["track_t"]) + late, 0.0))
				g["track_t0"] = float(item["track_t"])
				g["t0"] = t
				log.append({"kind": "seek", "t": t, "node": g["node"], "track": g["track"], "track_t": float(item["track_t"]), "from": float(item["track_t"]) + late, "lateness_ms": late * 1000.0})
		"end":
			for x in _groups:
				if not bool(x["fading"]) and not bool(x.get("pending", false)):
					if str(item["reason"]) != "depleted" and _tail_for(x, t):
						continue  # (the transition's tail took it at T: it fades by its recipe)
					_fade(x, float(item.get("seconds", fade_s)), t, str(item["reason"]))
			if str(item["reason"]) == "depleted":
				for x in _groups:  # (the run's own fade takes everything down, a tail and a muted start included)
					if bool(x.get("pending", false)) or not (x.get("tail", {}) as Dictionary).is_empty():
						if not (x.get("tail", {}) as Dictionary).is_empty():
							var sb := AudioServer.get_bus_index(str(SLOT_BUSES[int(x["slot"])]))
							if sb >= 0:
								AudioServer.set_bus_effect_enabled(sb, FX_HIGHPASS, false)
								AudioServer.set_bus_effect_enabled(sb, FX_DELAY, false)
						x["pending"] = false
						x["tail"] = {}
						_fade(x, float(item.get("seconds", fade_s)), t, "depleted")
		"dip":
			var g2 := _live()
			if not g2.is_empty():
				var tr2: TrackTransport = g2["transport"]
				tr2.scale_ramp_s = ramp_s
				for key in _dip_keys(g2):
					tr2.set_scale(str(key), dip_gain if bool(item["on"]) else 1.0)
				log.append({"kind": "dip", "t": t, "on": bool(item["on"])})


## The run's clock starts now (RunAudio.start, the end of the countdown): a group due on the first downbeat starts in the same call, at its own `track_t`, so the clock stream and the stems are
## new streams together and share their first mix (a group started a frame later reads the clock's start-up position and lands up to a mix period off: measured 83 ms on the Dummy driver).
func start_with_clock() -> void:
	while not _schedule.is_empty() and float(_schedule[0]["t"]) <= 1e-9:
		var item: Dictionary = _schedule.pop_front()
		run_item(item, float(item["t"]), 0.0, float(item["t"]))


func pause() -> void:
	for g in _groups:
		(g["transport"] as TrackTransport).pause()


func resume() -> void:
	for g in _groups:
		(g["transport"] as TrackTransport).resume()


## Everything stops at once (the run is left, restarted or over): no fade.
func stop() -> void:
	for g in _groups.duplicate():
		log.append({"kind": "stop", "node": g["node"], "track": g["track"]})
		_free_group(g)
	_schedule.clear()
	_preps.clear()


func _exit_tree() -> void:
	for id in _tasks:
		WorkerThreadPool.wait_for_task_completion(int(id))
	_tasks.clear()


# --- inside -------------------------------------------------------------------------------------------------------------------

func _add(item: Dictionary) -> void:
	item["seq"] = _seq
	_seq += 1
	_schedule.append(item)
	_schedule.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["t"]) < float(b["t"]) if float(a["t"]) != float(b["t"]) else int(a["seq"]) < int(b["seq"]))


func _live() -> Dictionary:
	for i in range(_groups.size() - 1, -1, -1):
		if not bool(_groups[i]["fading"]) and not bool(_groups[i].get("pending", false)):
			return _groups[i]
	return {}


## The track scene's group starts on its downbeat `t`, `late` seconds late: the stems start that far past `track_t`, so the group sits where the cues are.
func _start(ev: Dictionary, t: float, late: float) -> void:
	for x in _groups:
		if not bool(x["fading"]) and not bool(x.get("pending", false)):
			_fade(x, fade_s, t, "replaced")
	var g := _make_group(str(ev["node"]), str(ev["track"]), str(ev["dir"]), float(ev["beat_s"]), float(ev["track_t"]), t, maxf(float(ev["track_t"]) + late, 0.0), false)
	if g.is_empty():
		return
	var tr: TrackTransport = g["transport"]
	log.append({"kind": "start", "t": t, "node": str(ev["node"]), "track": str(ev["track"]), "track_t": float(ev["track_t"]), "from": tr.start_at, "lateness_ms": late * 1000.0,
		"stems": tr.stem_keys.duplicate(), "gains": tr.stem_keys.map(func(k: String) -> float: return tr.pack_gain(k)), "prepared": false, "slot": int(g["slot"])})


## A group of the pack in `dir`, playing from track time `from` on the free slot (muted when `muted`), its scene's downbeat `t` on track time `track_t`. {} when the stems are not in memory.
func _make_group(node: String, track: String, dir: String, beat_s: float, track_t: float, t: float, from: float, muted: bool) -> Dictionary:
	_poll()
	var e: Dictionary = _cache.get(dir, {})
	if e.is_empty() or str(e["state"]) != "ready":
		push_error("track audio: the stems of %s are not loaded at its start (%s)" % [track, str(e.get("state", "none"))])
		log.append({"kind": "unloaded", "t": t, "node": node, "track": track})
		return {}
	var pack: TrackPack = e["pack"]
	var tr := TrackTransport.new()
	tr.name = "Track_" + track
	add_child(tr)
	for k: Variant in stem_locks.get(track, []):  # (H7.1: before the load, so a locked stem is silent from the first sample; load_pack_streams applies it)
		tr.set_stem_locked(str(k), true)
	var slot := _free_slot()
	tr.player.bus = str(SLOT_BUSES[slot])
	pack.streams = (e["job"] as Dictionary)["streams"]
	var err := tr.load_pack_streams(pack)
	pack.streams = {}  # (the plan's pack keeps no audio: the cache and the playing group do)
	if err != "":
		push_error("track audio: %s: %s" % [track, err])
		tr.queue_free()
		return {}
	tr.start_at = from
	if muted:
		AudioServer.lock()  # (no mix between the start and the mute)
		tr.start()
		tr.player.volume_db = StemTransport.SILENT_DB
		AudioServer.unlock()
	else:
		tr.start()
	var mutes := RunTrackMutes.new()
	mutes.setup(pack.voices.map(func(v: Dictionary) -> String: return str(v["key"])), beat_s, pack.restore_after_idle_beats)
	var g := {"transport": tr, "node": node, "track": track, "dir": dir, "t0": t, "track_t0": track_t, "beat_s": beat_s, "fading": false, "mutes": mutes, "pack": pack, "slot": slot,
		"pending": muted, "tail": {}}
	_groups.append(g)
	return g


## The slot bus for a new group: the one no sounding group uses (the other one's group is the scene playing, or a tail); with both in use, the one whose groups are only fading out by a cut.
func _free_slot() -> int:
	var used := [0, 0]
	var busy := [false, false]
	for g in _groups:
		var s := int(g.get("slot", 0))
		used[s] += 1
		if not bool(g["fading"]) or not (g.get("tail", {}) as Dictionary).is_empty():
			busy[s] = true
	for s in 2:
		if used[s] == 0:
			return s
	for s in 2:
		if not busy[s]:
			return s
	return 0 if used[0] <= used[1] else 1


func _fade(g: Dictionary, seconds: float, t: float, reason: String) -> void:
	g["fading"] = true
	(g["transport"] as TrackTransport).fade_out(seconds)
	log.append({"kind": "end", "t": t, "node": g["node"], "track": g["track"], "reason": reason, "seconds": seconds})


func _free_group(g: Dictionary) -> void:
	var tr: TrackTransport = g["transport"]
	tr.stop()
	tr.queue_free()
	_groups.erase(g)


## The stems a dip lowers: every voice that is not of kind drums, and the backing.
func _dip_keys(g: Dictionary) -> Array:
	var pack: TrackPack = g["pack"]
	var out: Array = []
	for s in pack.stems_in_order():
		if not bool(s["voice"]) or str(pack.voice_by_key(str(s["key"])).get("kind", "")) != "drums":
			out.append(str(s["key"]))
	return out


func _on_judge(jev: Dictionary) -> void:
	var g := _live()
	if g.is_empty() or not notes_fn.is_valid():
		return
	_apply(g, (g["mutes"] as RunTrackMutes).on_judge(jev, notes_fn.call()))


func _apply(g: Dictionary, changes: Array) -> void:
	for ch in changes:
		(g["transport"] as TrackTransport).set_stem_muted(str(ch["voice"]), str(ch["kind"]) == "mute")
		var rec: Dictionary = (ch as Dictionary).duplicate()
		rec["node"] = g["node"]
		log.append(rec)


static func _plan(data: RunData, node_id: String) -> Dictionary:
	return data.track_scenes.plan_of(node_id) if data != null and data.track_scenes != null and data.nodes.has(node_id) else {}


## Keeps the packs of `plans` (and of every group still sounding) and lets every other one go; starts the decodes still missing.
func _retain(plans: Array) -> void:
	var keep := _pinned.duplicate()
	for p in plans:
		keep[str(p["dir"])] = true
	for g in _groups:
		keep[str(g["dir"])] = true
	var dropped: Array = []
	for d in _cache.keys():
		if not keep.has(d):
			if str(_cache[d]["state"]) == "loading":
				_cache[d]["keep"] = false  # (dropped when its decode is done)
			else:
				dropped.append(_cache[d]["job"])
				_cache.erase(d)
	_release(dropped)
	for p in plans:
		_request(p)


## Lets packs go on a worker thread: a decoded stem is thousands of Ogg packets, and freeing a pack on the main thread stalled a frame for up to 190 ms (measured on the Dummy driver).
func _release(jobs: Array) -> void:
	if jobs.is_empty():
		return
	_tasks.append(WorkerThreadPool.add_task(func() -> void:
		for j in jobs:
			(j as Dictionary)["streams"] = {}
		jobs.clear()))


func _request(plan: Dictionary) -> void:
	var dir := str(plan["dir"])
	if _cache.has(dir):
		_cache[dir]["keep"] = true
		return
	var pack: TrackPack = plan["pack"]
	var job := {"dir": dir, "stems": pack.stems_in_order(), "streams": {}, "error": "", "us": 0}
	var task := WorkerThreadPool.add_task(_decode.bind(job), false, "track stems " + str(plan["track"]))
	_tasks.append(task)
	_cache[dir] = {"state": "loading", "track": str(plan["track"]), "pack": pack, "job": job, "task": task, "keep": true}


## On a worker thread: every stem of the pack is read and set up for playback (Ogg Vorbis is decoded as it plays; this reads the file and its pages).
static func _decode(job: Dictionary) -> void:
	var t0 := Time.get_ticks_usec()
	var out := {}
	for s in job["stems"]:
		var path := str(job["dir"]).path_join(str(s["stem"]))
		var stream := AudioStreamOggVorbis.load_from_file(path)
		if stream == null or stream.get_length() <= 0.0:
			job["error"] = "cannot decode " + path
			break
		out[str(s["key"])] = stream
	job["streams"] = out
	job["us"] = Time.get_ticks_usec() - t0


## Takes the decodes that are done.
func _poll() -> void:
	for d in _cache.keys():
		var e: Dictionary = _cache[d]
		if str(e["state"]) == "loading" and WorkerThreadPool.is_task_completed(int(e["task"])):
			WorkerThreadPool.wait_for_task_completion(int(e["task"]))
			_tasks.erase(int(e["task"]))
			_finish(e)
			if not bool(e["keep"]):
				_cache.erase(d)
				_release([e["job"]])
	for id in _tasks.duplicate():  # (the warms)
		if WorkerThreadPool.is_task_completed(int(id)):
			WorkerThreadPool.wait_for_task_completion(int(id))
			_tasks.erase(id)


func _finish(e: Dictionary) -> void:
	var job: Dictionary = e["job"]
	e["state"] = "ready" if str(job["error"]) == "" else "failed"
	load_log.append({"track": str(e["track"]), "dir": str(job["dir"]), "ms": snappedf(float(job["us"]) / 1000.0, 0.1), "stems": (job["streams"] as Dictionary).size(), "ok": str(job["error"]) == "",
		"error": str(job["error"])})
	if str(job["error"]) != "":
		push_warning("track audio: " + str(job["error"]))


## RunTrack: the group's own bus, a hard limiter (separated stems summed peak above full scale where the master does, src/track/track_play.gd), then the Music bus. The loops never pass here.
static func _ensure_bus() -> void:
	var music := AudioServer.get_bus_name(StemTransport.ensure_music_bus())
	if AudioServer.get_bus_index(BUS) < 0:
		AudioServer.add_bus()
		AudioServer.set_bus_name(AudioServer.bus_count - 1, BUS)
	var i := AudioServer.get_bus_index(BUS)
	if i < AudioServer.get_bus_index(music):
		AudioServer.move_bus(i, AudioServer.bus_count)
		i = AudioServer.get_bus_index(BUS)
	AudioServer.set_bus_send(i, music)
	var has_lim := false
	for k in AudioServer.get_bus_effect_count(i):
		has_lim = has_lim or AudioServer.get_bus_effect(i, k) is AudioEffectHardLimiter
	if not has_lim:
		var lim := AudioEffectHardLimiter.new()
		lim.ceiling_db = LIMIT_CEILING_DB
		AudioServer.add_bus_effect(i, lim)
	for name in SLOT_BUSES:  # the two slots, after RunTrack in the bus list (a bus sends only to one mixed after it)
		if AudioServer.get_bus_index(str(name)) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, str(name))
		var s := AudioServer.get_bus_index(str(name))
		if s < AudioServer.get_bus_index(BUS):
			AudioServer.move_bus(s, AudioServer.bus_count)
			s = AudioServer.get_bus_index(str(name))
		AudioServer.set_bus_send(s, BUS)
		if AudioServer.get_bus_effect_count(s) != 2 or not AudioServer.get_bus_effect(s, FX_HIGHPASS) is AudioEffectHighPassFilter or not AudioServer.get_bus_effect(s, FX_DELAY) is AudioEffectDelay:
			_reset_slot_fx(s)


## The slot's two effects made afresh, both off: a high-pass (the tail's rising filter) and a delay (echo_out). Made new so that no echo of an earlier tail is left in the delay line.
static func _reset_slot_fx(bus: int) -> void:
	while AudioServer.get_bus_effect_count(bus) > 0:
		AudioServer.remove_bus_effect(bus, 0)
	var hp := AudioEffectHighPassFilter.new()
	hp.cutoff_hz = 20.0
	hp.resonance = 0.5
	AudioServer.add_bus_effect(bus, hp)
	var dl := AudioEffectDelay.new()
	dl.dry = 1.0
	dl.tap1_active = false
	dl.tap2_active = false
	dl.feedback_active = false
	AudioServer.add_bus_effect(bus, dl)
	AudioServer.set_bus_effect_enabled(bus, FX_HIGHPASS, false)
	AudioServer.set_bus_effect_enabled(bus, FX_DELAY, false)


# --- transitions (stage M2.4) ----------------------------------------------------------------------------------------------------

## The director locked a transition at boundary `boundary_t` (RunAudio.prepare_transition): the incoming track scene's group starts early and muted, the outgoing one may become a tail at T.
func prepare_transition(boundary_t: float, recipe: Dictionary) -> void:
	for p in _preps:
		if absf(float(p["t"]) - boundary_t) < 1e-4:
			_preps.erase(p)  # (a boundary locked again replaces what was prepared for it)
			_drop_pending(p, "relocked")
			break
	_preps.append({"t": boundary_t, "recipe": recipe.duplicate(true), "group": {}, "skip": false, "unmuted": false, "tail": false, "err_ms": NAN, "final_ms": NAN, "readings": 0,
		"rate_min": 1.0, "rate_max": 1.0})


## The transitions of the boundaries prepared so far (tests, the walks): [{t, mode, err_ms (the muted start's error, measured), final_ms (left at T), readings, prepared (started early)}].
func prep_log() -> Array:
	return log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["prestart", "corrected", "tail", "floor", "orphan"])


func _period(ttnm: float) -> float:
	if period_override >= 0.0:
		return period_override
	return clampf(AudioServer.get_time_since_last_mix() + ttnm, 0.0, 0.25)


func _step_preps(now: float, ttnm: float) -> void:
	if _preps.is_empty():
		return
	var x := now + ttnm  # the song time the next mix chunk starts at (the scheduler's rule)
	var period := _period(ttnm)
	for p in _preps.duplicate():
		var T := float(p["t"])
		var r: Dictionary = p["recipe"]
		var inc: Dictionary = r.get("in", {})
		var g: Dictionary = p["group"]
		if g.is_empty() and not bool(p["skip"]) and not inc.is_empty() and StringName(str(r.get("incoming", ""))) == &"track":
			var lead := T - x
			var from := float(inc["entry_t"]) - lead
			if lead < PREP_MIN_S:
				p["skip"] = true  # too late to measure and correct: the engine's track_start starts it at T by the lateness rule
			else:
				# an entry nearer the start of the audio than the lead (entry bar 0): no audio before it to pre-roll from, so the muted group is a PROBE started further in, whose
				# restarts learn how late a start lands; the real start is made at T with that lag taken off (_final_start)
				var probe := from < 0.0
				var f0 := 1.0 if probe else from
				g = _make_group(str(inc["node"]), str(inc["track"]), str(inc["dir"]), float(inc["beat_s"]), float(inc["entry_t"]), T, f0, true)
				if g.is_empty():
					p["skip"] = true
				else:
					g["prep_t"] = T
					g["entry_t"] = f0 + lead if probe else float(inc["entry_t"])
					g["real_entry_t"] = float(inc["entry_t"])
					g["probe"] = probe
					g["start_x"] = x
					p["group"] = g
					log.append({"kind": "prestart", "t": T, "at": x, "node": g["node"], "track": g["track"], "from": f0, "slot": int(g["slot"]), "probe": probe})
		if not g.is_empty() and bool(p.get("final", false)) and is_instance_valid(g["transport"]):
			_measure_final(g, p)
		elif not g.is_empty() and bool(g.get("pending", false)) and is_instance_valid(g["transport"]):
			if bool(g.get("probe", false)) and not bool(p.get("final", false)):
				_correct(g, p, x, period)
				var from_real := float(g["real_entry_t"]) - (T - x) + float(p.get("comp", 0.0))
				if from_real >= 0.0 and x >= T - period - 0.02:
					_final_start(g, p, x, from_real)
			else:
				_correct(g, p, x, period)
				if not bool(p["unmuted"]) and x >= T - period - 0.02:
					_unmute(g, p)
		if not bool(p["tail"]) and x >= T:
			p["tail"] = true
			if TAIL_MODES.has(StringName(str(r.get("mode", "")))):
				var out := _outgoing_of(p)
				if not out.is_empty():
					_make_tail(out, r, T, x)
		if x > T + 1.0 and (g.is_empty() or not bool(g.get("pending", false))):
			_preps.erase(p)  # (done: adopted, or never started)
		elif x > T + 1.0:
			_preps.erase(p)
			_drop_pending(p, "never adopted")


## Pulls a muted group onto the clock: its playhead against the clock's, read together under AudioServer.lock, gives the start error e (> 0: the group is ahead).
## FIRST BY RESTARTS: the muted group is started again with the error it showed taken off (a start lands one or two mix periods late, so the same compensation lands it exactly about every
## other try), until it reads within RESTART_TOL_S; a fresh start at rate 1.0 is what the run's first scene has, so its audio sits against its playhead exactly as every other group's does.
## (Measured on WASAPI: a group pulled in by pitch_scale alone reads 0.00 ms on its playhead but its audio sat 0.7 to 1.5 ms off the others: the resampler's buffer phase moves with the rate.)
## ONLY IF THAT RUNS OUT OF TIME: the group plays at 1 - e / tau (within CORRECT_MAX_RATE). Either way exactly 1.0 from two mix periods before T.
const RESTART_TOL_S := 0.0001
const RESTART_MAX := 16
const RESTART_MARGIN_S := 0.12


func _correct(g: Dictionary, p: Dictionary, x: float, period: float) -> void:
	var tr: TrackTransport = g["transport"]
	var T := float(p["t"])
	var rd := _positions(g)
	var stop_at := T - 2.0 * period - 0.02
	if rd.is_empty():
		if x >= stop_at:
			tr.player.pitch_scale = 1.0
		return
	var e := float(rd[1]) - (float(g["entry_t"]) + float(rd[0]) - T)
	p["readings"] = int(p["readings"]) + 1
	if is_nan(float(p["err_ms"])):
		p["err_ms"] = e * 1000.0
	if absf(e) <= RESTART_TOL_S and tr.player.pitch_scale == 1.0:
		p["landed"] = true
	if not bool(p.get("landed", false)) and int(p.get("restarts", 0)) < RESTART_MAX and x < stop_at - RESTART_MARGIN_S:
		var lags: Array = p.get("lags", [])
		lags.append(float(p.get("comp", 0.0)) - e)  # how late this start landed
		p["lags"] = lags
		var comp := _likeliest(lags)
		var from := float(g["entry_t"]) - (T - x) + comp
		if from >= 0.0:
			p["comp"] = comp
			p["restarts"] = int(p.get("restarts", 0)) + 1
			AudioServer.lock()
			tr.player.pitch_scale = 1.0
			tr.player.play(from)
			tr.start_at = from
			AudioServer.unlock()
			return
	if bool(p.get("landed", false)):
		tr.player.pitch_scale = 1.0
		if x >= stop_at and is_nan(float(p["final_ms"])):
			p["final_ms"] = e * 1000.0
		return
	if x >= stop_at:
		tr.player.pitch_scale = 1.0
		if is_nan(float(p["final_ms"])):
			p["final_ms"] = e * 1000.0
		return
	var tau := maxf(0.05, 1.5 * period)
	var rate := 1.0 if absf(e) < CORRECT_DEADBAND_S else clampf(1.0 - e / tau, 1.0 - CORRECT_MAX_RATE, 1.0 + CORRECT_MAX_RATE)
	tr.player.pitch_scale = rate
	p["rate_min"] = minf(float(p["rate_min"]), rate)
	p["rate_max"] = maxf(float(p["rate_max"]), rate)


## The landing lag seen most often so far (lags within 0.2 ms count as one; a tie goes to the latest): the compensation for the next restart.
static func _likeliest(lags: Array) -> float:
	var best := float(lags[lags.size() - 1])
	var best_n := 0
	for i in range(lags.size() - 1, -1, -1):
		var n := 0
		for y in lags:
			if absf(float(y) - float(lags[i])) <= 0.0002:
				n += 1
		if n > best_n:
			best_n = n
			best = float(lags[i])
	return best


## [clock position, group playhead] read in one lock, or [] while the group has not been mixed yet (its playhead still reads its start).
func _positions(g: Dictionary) -> Array:
	if position_fn.is_valid():
		return position_fn.call(g)
	var tr: TrackTransport = g["transport"]
	if run_audio == null or not tr.player.playing:
		return []
	AudioServer.lock()
	var cp := run_audio.playback_position()
	var gp := tr.player.get_playback_position()
	AudioServer.unlock()
	if absf(gp - tr.start_at) < 1e-9:
		return []
	return [cp, gp]


func _unmute(g: Dictionary, p: Dictionary) -> void:
	var tr: TrackTransport = g["transport"]
	tr.player.pitch_scale = 1.0
	tr.player.volume_db = 0.0
	p["unmuted"] = true
	if is_nan(float(p["final_ms"])):
		var rd := _positions(g)
		if not rd.is_empty():
			p["final_ms"] = (float(rd[1]) - (float(g["entry_t"]) + float(rd[0]) - float(p["t"]))) * 1000.0
	log.append({"kind": "corrected", "t": float(p["t"]), "track": g["track"], "err_ms": float(p["err_ms"]), "final_ms": float(p["final_ms"]), "readings": int(p["readings"]),
		"rate_min": float(p["rate_min"]), "rate_max": float(p["rate_max"]), "restarts": int(p.get("restarts", 0)), "landed": bool(p.get("landed", false)),
		"comp_ms": float(p.get("comp", 0.0)) * 1000.0})


## The real start of a probed group (its entry too near the audio's start to pre-roll): at song time x, from track time `from` (the entry, as late as the call is, with the probes' landing
## lag taken off), heard at once. It is not corrected after this (it is heard); what it measures is logged.
func _final_start(g: Dictionary, p: Dictionary, x: float, from: float) -> void:
	var tr: TrackTransport = g["transport"]
	AudioServer.lock()
	tr.player.pitch_scale = 1.0
	tr.player.play(maxf(from, 0.0))
	tr.start_at = maxf(from, 0.0)
	tr.player.volume_db = 0.0
	AudioServer.unlock()
	g["entry_t"] = float(g["real_entry_t"])
	p["final"] = true
	p["unmuted"] = true
	p["landed"] = true
	p["final_ms"] = NAN
	log.append({"kind": "final_start", "t": float(p["t"]), "at": x, "track": g["track"], "from": maxf(from, 0.0), "comp_ms": float(p.get("comp", 0.0)) * 1000.0, "probe_restarts": int(p.get("restarts", 0))})


func _measure_final(g: Dictionary, p: Dictionary) -> void:
	if not is_nan(float(p["final_ms"])):
		return
	var rd := _positions(g)
	if rd.is_empty():
		return
	p["final_ms"] = (float(rd[1]) - (float(g["entry_t"]) + float(rd[0]) - float(p["t"]))) * 1000.0
	log.append({"kind": "corrected", "t": float(p["t"]), "track": g["track"], "err_ms": float(p["err_ms"]), "final_ms": float(p["final_ms"]), "readings": int(p["readings"]),
		"rate_min": 1.0, "rate_max": 1.0, "restarts": int(p.get("restarts", 0)), "landed": absf(float(p["final_ms"])) < 0.1, "comp_ms": float(p.get("comp", 0.0)) * 1000.0, "probe": true})


## The engine's track_start at T for a group started early: it is adopted (no second start). False when there is none for this scene and boundary.
func _adopt(ev: Dictionary, t: float, x: float) -> bool:
	for p in _preps:
		var g: Dictionary = p["group"]
		if g.is_empty() or not bool(g.get("pending", false)) or absf(float(p["t"]) - t) > 1e-4 or str(g["dir"]) != str(ev["dir"]):
			continue
		if bool(g.get("probe", false)) and not bool(p.get("final", false)):
			_final_start(g, p, x, float(g["real_entry_t"]) - (t - x) + float(p.get("comp", 0.0)))
		elif not bool(p["unmuted"]):
			_unmute(g, p)
		for y in _groups:
			if not is_same(y, g) and not bool(y["fading"]) and not bool(y.get("pending", false)):
				_fade(y, fade_s, t, "replaced")
		g["pending"] = false
		g["track_t0"] = float(ev["track_t"])
		g["t0"] = t
		var tr: TrackTransport = g["transport"]
		log.append({"kind": "start", "t": t, "node": str(ev["node"]), "track": str(ev["track"]), "track_t": float(ev["track_t"]), "from": tr.start_at, "lateness_ms": float(p["err_ms"]),
			"residual_ms": float(p["final_ms"]), "adopted_at": x, "stems": tr.stem_keys.duplicate(), "gains": tr.stem_keys.map(func(k: String) -> float: return tr.pack_gain(k)), "prepared": true,
			"slot": int(g["slot"])})
		return true
	return false


## A scene began at T: a group started muted for this boundary whose track is not the scene's goes (the scene really entered is another one: a fallback, a route changed after the lock).
func _drop_orphans(t: float, track: String) -> void:
	for p in _preps:
		var g: Dictionary = p["group"]
		if not g.is_empty() and bool(g.get("pending", false)) and absf(float(p["t"]) - t) < 1e-4 and str(g["track"]) != track:
			_drop_pending(p, "another scene began")


func _drop_pending(p: Dictionary, why: String) -> void:
	var g: Dictionary = p["group"]
	if g.is_empty() or not bool(g.get("pending", false)) or not _groups.any(func(y: Dictionary) -> bool: return is_same(y, g)):
		return
	g["pending"] = false
	log.append({"kind": "orphan", "t": float(p["t"]), "track": g["track"], "why": why})
	_fade(g, 0.03, float(p["t"]), "orphan")


## The outgoing group of a prepared boundary: the scene playing (not the muted incoming one, not a tail).
func _outgoing_of(p: Dictionary) -> Dictionary:
	var want := str((p["recipe"].get("out", {}) as Dictionary).get("dir", ""))
	for i in range(_groups.size() - 1, -1, -1):
		var g: Dictionary = _groups[i]
		if bool(g["fading"]) or bool(g.get("pending", false)):
			continue
		if want == "" or str(g["dir"]) == want:
			return g
	return {}


## True when group `g` is (or has just become) the tail of the transition at boundary `t` ("end" items of the boundary leave it to its recipe).
func _tail_for(g: Dictionary, t: float) -> bool:
	if not (g.get("tail", {}) as Dictionary).is_empty():
		return true
	for p in _preps:
		if absf(float(p["t"]) - t) < 1e-4 and TAIL_MODES.has(StringName(str((p["recipe"] as Dictionary).get("mode", "")))) and is_same(_outgoing_of(p), g):
			p["tail"] = true
			_make_tail(g, p["recipe"], t, t)
			return true
	return false


## The outgoing group becomes the tail at T (see the header): its rate, its level, its slot's effects; the fades run in _step_tails.
func _make_tail(g: Dictionary, r: Dictionary, T: float, x: float) -> void:
	var tr: TrackTransport = g["transport"]
	var rec: Dictionary = r.duplicate(true)
	rec["T"] = T
	g["tail"] = rec
	g["fading"] = true  # (RunAudio.outgoing_sounding counts it until its floor)
	tr.player.pitch_scale = float(r.get("rate", 1.0))
	tr.player.volume_db = float(r.get("tail_gain_db", 0.0))
	var bus := AudioServer.get_bus_index(str(SLOT_BUSES[int(g["slot"])]))
	var hp_r: Dictionary = r.get("highpass", {})
	if bus >= 0 and not hp_r.is_empty():
		var hp := AudioServer.get_bus_effect(bus, FX_HIGHPASS) as AudioEffectHighPassFilter
		if hp != null:
			hp.cutoff_hz = float(hp_r.get("from_hz", 20.0))
			AudioServer.set_bus_effect_enabled(bus, FX_HIGHPASS, true)
	var echo: Dictionary = r.get("echo", {})
	if bus >= 0 and not echo.is_empty():
		var dl := AudioServer.get_bus_effect(bus, FX_DELAY) as AudioEffectDelay
		if dl != null:
			dl.dry = 1.0
			dl.tap1_active = false
			dl.tap2_active = false
			dl.feedback_active = true
			dl.feedback_delay_ms = float(echo.get("delay_s", 0.25)) * 1000.0
			dl.feedback_level_db = linear_to_db(float(echo.get("feedback", 0.4)))
			AudioServer.set_bus_effect_enabled(bus, FX_DELAY, true)
	log.append({"kind": "tail", "t": T, "at": x, "track": g["track"], "mode": str(r.get("mode", "")), "rate": float(r.get("rate", 1.0)), "tail_gain_db": float(r.get("tail_gain_db", 0.0)),
		"floor_t": float(r.get("floor_t", T)), "slot": int(g["slot"])})
	_tail_gains(g, x)


## Every tail's gains, filter and floor at song time `x` (the start of the next mix chunk).
func _step_tails(x: float) -> void:
	for g in _groups.duplicate():
		if (g.get("tail", {}) as Dictionary).is_empty():
			continue
		if x >= float((g["tail"] as Dictionary).get("floor_t", 0.0)) - 1e-9:
			_floor(g, x)
		else:
			_tail_gains(g, x)


## The recipe's gain of one stem `key` of the tail at song time `x` (1 before its fade, 0 after, `cos` between; under -60 dB it is 0).
static func tail_gain_at(rec: Dictionary, key: String, x: float) -> float:
	var st: Dictionary = (rec.get("stems", {}) as Dictionary).get(key, {})
	var fade: Array = st.get("fade", [])
	if fade.is_empty():
		var kind := TransitionPlanner.stem_kind(key, TransitionPlanner.DEFAULT_LINGER)
		fade = (rec.get("kinds", {}) as Dictionary).get(kind, [0.0, 0.0, &"cos"])
	var b := (x - float(rec["T"])) / maxf(float(rec.get("bar_s", 1.0)), 1e-6)
	var s := float(fade[0])
	var e := float(fade[1])
	var gl := 1.0
	if b >= e:
		gl = 0.0
	elif b > s:
		gl = cos(PI * 0.5 * clampf((b - s) / maxf(e - s, 1e-9), 0.0, 1.0))
	return 0.0 if gl < SILENCE_GAIN else gl


func _tail_gains(g: Dictionary, x: float) -> void:
	var rec: Dictionary = g["tail"]
	var tr: TrackTransport = g["transport"]
	for key in tr.stem_keys:
		tr.set_tail_gain(str(key), tail_gain_at(rec, str(key), x))
	var hp_r: Dictionary = rec.get("highpass", {})
	var bus := AudioServer.get_bus_index(str(SLOT_BUSES[int(g["slot"])]))
	if bus >= 0 and not hp_r.is_empty():
		var hp := AudioServer.get_bus_effect(bus, FX_HIGHPASS) as AudioEffectHighPassFilter
		if hp != null:
			var b := (x - float(rec["T"])) / maxf(float(rec.get("bar_s", 1.0)), 1e-6)
			var s := float(hp_r.get("start_bar", 0.0))
			var e := float(hp_r.get("end_bar", 1.0))
			var k := clampf((b - s) / maxf(e - s, 1e-9), 0.0, 1.0)
			var f0 := float(hp_r.get("from_hz", 20.0))
			hp.cutoff_hz = f0 * pow(float(hp_r.get("to_hz", f0)) / f0, k)


## The hard floor (planner: floor_t = complete_t, at least 4 incoming bars before the drop): the tail stops whatever its curves say, its slot's effects go off and are made afresh.
func _floor(g: Dictionary, x: float) -> void:
	var rec: Dictionary = g["tail"]
	var tr: TrackTransport = g["transport"]
	var loud: Array = []
	for key in tr.stem_keys:
		if tail_gain_at(rec, str(key), float(rec.get("floor_t", x)) - 1e-6) > SILENCE_GAIN:
			loud.append(str(key))  # (a recipe bug: the curves should be down by the floor)
	tr.player.volume_db = StemTransport.SILENT_DB
	g["tail"] = {}
	var bus := AudioServer.get_bus_index(str(SLOT_BUSES[int(g["slot"])]))
	if bus >= 0:
		AudioServer.set_bus_effect_enabled(bus, FX_HIGHPASS, false)
		AudioServer.set_bus_effect_enabled(bus, FX_DELAY, false)
	_free_group(g)
	if bus >= 0:
		_reset_slot_fx(bus)
	log.append({"kind": "floor", "t": float(rec["T"]), "at": x, "floor_t": float(rec.get("floor_t", x)), "track": g["track"], "still_sounding": loud})
	if not loud.is_empty():
		push_warning("track audio: the tail of %s reached its floor with %s above -60 dB" % [str(g["track"]), str(loud)])


## Tails still playing (tests, the walks).
func tail_count() -> int:
	var n := 0
	for g in _groups:
		if not (g.get("tail", {}) as Dictionary).is_empty():
			n += 1
	return n


## Track groups still fading out (the outgoing music of a transition; RunAudio.outgoing_sounding).
func fading_count() -> int:
	var n := 0
	for g in _groups:
		if bool(g["fading"]):
			n += 1
	return n
