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

const BUS := "RunTrack"
const LIMIT_CEILING_DB := -0.3

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
var _groups: Array = []  # {transport: TrackTransport, node, track, dir, t0, track_t0, beat_s, fading, mutes: RunTrackMutes}
var _cache: Dictionary = {}  # pack folder -> {state: loading | ready | failed, track, pack, job, task, keep}
var _tasks: Array = []  # worker tasks not yet waited for (decodes and warms)
var _pinned: Dictionary = {}  # pack folder -> true: kept by _retain (request_scene with pin, the director's destinations)


# --- the interface ------------------------------------------------------------------------------------------------------------

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


## One frame of RunAudio (song time `now` of the sound reaching the listener, `ttnm` the time to the next mix): due items run, idle restores come back, finished loads are taken, faded groups go.
func step(now: float, ttnm: float) -> void:
	while not _schedule.is_empty() and float(_schedule[0]["t"]) <= now + ttnm:
		run_item(_schedule.pop_front(), now, ttnm)
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
			_start(item["ev"], t, late)
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
				if not bool(x["fading"]):
					_fade(x, float(item.get("seconds", fade_s)), t, str(item["reason"]))
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
		if not bool(_groups[i]["fading"]):
			return _groups[i]
	return {}


## The track scene's group starts on its downbeat `t`, `late` seconds late: the stems start that far past `track_t`, so the group sits where the cues are.
func _start(ev: Dictionary, t: float, late: float) -> void:
	for x in _groups:
		if not bool(x["fading"]):
			_fade(x, fade_s, t, "replaced")
	_poll()
	var dir := str(ev["dir"])
	var e: Dictionary = _cache.get(dir, {})
	if e.is_empty() or str(e["state"]) != "ready":
		push_error("track audio: the stems of %s are not loaded at its start (%s)" % [str(ev["track"]), str(e.get("state", "none"))])
		log.append({"kind": "unloaded", "t": t, "node": str(ev["node"]), "track": str(ev["track"])})
		return
	var pack: TrackPack = e["pack"]
	var tr := TrackTransport.new()
	tr.name = "Track_" + str(ev["track"])
	add_child(tr)
	tr.player.bus = BUS
	pack.streams = (e["job"] as Dictionary)["streams"]
	var err := tr.load_pack_streams(pack)
	pack.streams = {}  # (the plan's pack keeps no audio: the cache and the playing group do)
	if err != "":
		push_error("track audio: %s: %s" % [str(ev["track"]), err])
		tr.queue_free()
		return
	tr.start_at = maxf(float(ev["track_t"]) + late, 0.0)
	tr.start()
	var mutes := RunTrackMutes.new()
	mutes.setup(pack.voices.map(func(v: Dictionary) -> String: return str(v["key"])), float(ev["beat_s"]), pack.restore_after_idle_beats)
	_groups.append({"transport": tr, "node": str(ev["node"]), "track": str(ev["track"]), "dir": dir, "t0": t, "track_t0": float(ev["track_t"]), "beat_s": float(ev["beat_s"]), "fading": false,
		"mutes": mutes, "pack": pack})
	log.append({"kind": "start", "t": t, "node": str(ev["node"]), "track": str(ev["track"]), "track_t": float(ev["track_t"]), "from": tr.start_at, "lateness_ms": late * 1000.0,
		"stems": tr.stem_keys.duplicate(), "gains": tr.stem_keys.map(func(k: String) -> float: return tr.pack_gain(k))})


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
	for k in AudioServer.get_bus_effect_count(i):
		if AudioServer.get_bus_effect(i, k) is AudioEffectHardLimiter:
			return
	var lim := AudioEffectHardLimiter.new()
	lim.ceiling_db = LIMIT_CEILING_DB
	AudioServer.add_bus_effect(i, lim)


## Track groups still fading out (the outgoing music of a transition; RunAudio.outgoing_sounding).
func fading_count() -> int:
	var n := 0
	for g in _groups:
		if bool(g["fading"]):
			n += 1
	return n
