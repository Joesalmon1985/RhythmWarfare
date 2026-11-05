class_name RunEngine
extends RefCounted
## The continuous run as pure logic (no nodes, no audio, no clock of its own): it is advanced with song time and answers with events.
##
## A phase is 64 beats at 174 BPM: four blocks of 16. Block b of a phase plays the cue family of the current mix stage (drums alone,
## bass enters, drums return, bass strongest). At each block's decision beat the block is judged: a pass moves the stage one step on, a
## miss holds the stage (and so the cue family) for the next block. The phase length never changes; the last block carries the
## direction choice. Cues are appended to `level.notes` one block ahead (the judge, pad view and note lane read the growing list), and
## the first block of the next phase is charted at the last block's decision from the selected route (the default, or the player's pick), and the chart is then locked: a route
## whose scene charts another pack can no longer be chosen. A scene is one phase at a place in a world; a world is a small graph of scenes (RunData).
##
## Everything is a function of (song time, the judge's results, the player's choice), so any frame step, a pause or a calibration change
## gives the same events at the same song times.
##
## LAPS (docs/CONTINUOUS_RUN.md "Two laps"): a scene may play `laps` phases in a row (a path's `path.laps`, or the scene's own `laps`; 1 everywhere in the 174 run). Each lap is a phase of its own (its
## own phase number, blocks, cues and judge results; the energy rules are per block as ever). Only the LAST lap carries the hotspot window, the route window and the commit; the laps before it end
## on the downbeat in the same scene, with the mix stage of the last block carried (a pass of that block steps it on) so the bass already in stays in, and the bass phrase and the cast go on.
##
## TRACK SCENES (docs/RUN_TRACK_SCENES.md): a scene that `data.track_scenes` gives a plan (RunTrackScenes.plan_of, RunTrackPlan) plays a whole recorded track. Everything below applies only while
## `track` is not empty (is_track_scene()); with track scenes off, or in a scene without a plan, nothing here runs and the engine is the one described above, event for event.
## - Tempo: the scene runs at the track's tempo (a float). The engine re-grids itself at `_enter`: `grid_origin` becomes the scene's first downbeat, `grid_beat0` the run's beat count there (so ticks
##   keep growing across tempos), `beat_s` and `level.bpm` the scene's. The scene after it re-grids back (to its own tempo) the same way. The phase structure is unchanged: 64 beats, 4 blocks of 16, cues
##   in the first 12, the decision at 12.5, the window from the third block's decision, the choice at 60.5.
## - Laps: the plan's `laps` (up to the assignment's max_laps, on any path). From `doors_from_lap` the window opens on EVERY lap (an "open lap"). An exit (any final-window hotspot that is available, or
##   a plain `choose()`, or the pause menu's leave) touched before the choice beat makes that lap the last: it commits, is judged and walked as a last lap's is. Nothing touched: nothing commits, the
##   window closes at the choice beat (no door walk), the hotspots reset for the next lap (RunHotspots.begin_lap) and the scene goes on. The plan's final lap is a last lap as ever (default exit).
## - Hold (a minigame): laps keep counting; at the end of the plan's final lap the scene gets one more lap (instead of re-entering the scene), and so on; a lap that would start with fewer than 16 bars
##   of the track left starts again from the entry bar (`track_wrap`).
## - Cues: from the plan's chart (`_chart_track_block`), moved to scene time, tagged with phase (the lap's), block and `lap`; cues in the last 4 beats of a block left out (the run's 12-beat rule), holds
##   cut to end by beat 12 (shorter than half a beat: a tap). `voice` is the pack's voice key; `family` is "kick" (pads 1, 2) or "snare" (pads 3, 4) for a voice of kind "drums", else "bass" (the
##   palette and icons of the note lane and the pads); `track_t` the cue's time in the track.
## - A block without cues is neutral: it passes, its energy is unchanged and the stage does not step (block_result.neutral). The energy of the other blocks follows `energy.track` in run.json.
##
## Events only a track scene emits (every other event keeps firing as in any scene; those of a track scene may carry the extra fields named here):
##   {kind: "tempo", t, node, bpm, beat_s, from_bpm}  the beat changes at a scene's first downbeat (before its phase_start): entering a track scene, or the scene after one at another tempo.
##   {kind: "track_start", t, node, track, dir, chart, bpm, beat_s, entry, entry_bar, track_t, laps, doors_from_lap, duration_s, index, phase}  just after the scene's phase_start: the track plays from
##       track time `track_t` (the downbeat of bar `entry_bar`) at song time `t`; `dir` is the pack's folder (TrackPack there: data.track_scenes.plan_of(node)["pack"]); index 0 the track, k its k-th alternate.
##   {kind: "track_lap", t, node, track, lap, laps, track_t, doors_open, last, phase}  every lap start after the first (just after its lap_start): the track should be at `track_t` at song time `t`.
##   {kind: "track_last_lap", t, node, track, lap, ends_t, route}  at the choice beat of an open lap where an exit was touched: this lap is now the last, the scene ends at `ends_t`.
##   {kind: "track_extend", t, node, track, laps}  at the choice beat of the final lap while a minigame holds the run: one more lap (now `laps`).
##   {kind: "track_wrap", t, node, track, lap, track_t, from_track_t, decided_t}  decided at the last decision of a lap (`decided_t`), due at the next lap's downbeat `t`: the track restarts at
##       `track_t` (the entry bar) instead of going on to `from_track_t` (fewer than 16 bars would be left).
##   {kind: "track_end", t, node, track, track_t, reason, to}  the track scene ends at song time `t` (track time `track_t`): reason "route" (the next scene starts on `t`), "handoff" (a path hand-off)
##       or "depleted" (the run is over; `t` is the depletion boundary).
##   Extra fields: phase_start.track (the track id); block_result.neutral and .track; route_window.last (false on an open lap) and .track; cues.track and .lap.

const TICKS := 960
const GUARD_NOTE := "cue_free_guard"
const LEAVE_ROUTE := "run:warehouse"  # the way back from a path (an ending's route, or the pause menu's "Leave this path")

var data: RunData
var cfg: Dictionary
var level: Level
var judge := PadJudge.new()
var beat_s := 60.0 / 174.0

var energy := 60.0
var over := false  # the run has ended (depleted); the scene shows the game-over screen
var node_id := ""
var depth := 1
var phase_n := 0  # phases entered so far in this run, counting the current one (1 for the first)
var phase_t0 := 0.0  # song time of the current phase's downbeat
var stage := 0  # mix stage in force for the current block
var block := 0  # block being played (0..3)
var bass_origin := -1  # phase beat the bass and synth started from (-1: not revealed yet)
var stage_of_block: Array = []
var block_credit: Array = []
var choice := ""  # the chosen destination node id ("" until the player picks one)
var window_open := false
var hotspots: RunHotspots = null  # when set, the route is the outcome of a hotspot (the tap is the intent, block 4 decides): see _hotspot_decision; null keeps the plain route choice (tests, RW_RUN_ARROWS=1)
var hold := false  # a minigame owns the scene (MinigameController): the run stays here, no hotspot commits, the chart and the route lock agree on this node; phases, cues, judging and energy go on as usual
var route_locked := false  # block 0 of the next phase has been charted: routes with another chart pack can no longer be chosen
var _locked_chart := ""
var grid_origin := 0.0  # song time this engine's beat grid starts at (0 for the run's own clock; a path's engine starts on the downbeat its clock was swapped in, docs/CONTINUOUS_RUN.md "Paths")
var lap := 1  # the lap being played (1..laps) of the current scene
var laps := 1  # laps of the current scene (data: path.laps / the scene's `laps`)
var scene_t0 := 0.0  # song time of the current scene's first downbeat (lap 1)
var lap_extra := 0  # laps played beyond the first, over the whole run: phase_n - lap_extra counts scenes
var away := ""  # the route the engine was handed off by ("path:<id>" or "run:warehouse"): the run left this engine's world, it is frozen and gives no more events

var _events: Array = []
var _cast_queue: Array = []  # the story beats still to come, earliest first: [{t, seq, beat, index, line, source, node, phase, name}] (the scene's `cast` lines, and a committed outcome's cinematic cast)
var _cast_seq := 0
var _next_block_notes := {}  # block index -> true once charted
var _next_phase_charted := false
var _depleted_t := -1.0
var _over_t := -1.0
var _lap_stage := 0  # the mix stage the next lap starts in (decided at the last block's decision of a lap that is not the final one)
var _lap_bass_origin := -1  # the bass phrase origin the next lap charts from
var _blocks_total := 0  # blocks charted in this run (for sequence ids)
var _note_id := 0
var part_offset := {"drums": 0.0, "bass": 0.0}  # seconds the audible part sits from the grid in the current phase (RunAudio measures it)
var track: Dictionary = {}  # the current scene's track plan (RunTrackScenes.plan_of); {} in an ordinary scene
var doors_from_lap := 0  # a track scene: the first lap whose window opens (0 in an ordinary scene)
var grid_beat0 := 0  # the run's beat count at grid_origin (0 until a track scene re-grids the engine)
var _regridded := false  # a track scene has re-gridded this engine: every later scene re-grids on its own first downbeat
var _lap_track_t0 := 0.0  # a track scene: the track time at the current lap's downbeat
var _next_lap_track_t0 := 0.0  # ... and at the next lap's (decided at the lap's last decision; a wrap goes back to the entry bar)
var _track_e: Dictionary = {}  # the energy numbers of a track scene's blocks (run.json energy, with energy.track over it)


func _init(p_data: RunData = null) -> void:
	if p_data != null:
		setup(p_data)


func setup(p_data: RunData) -> void:
	data = p_data
	cfg = data.cfg
	beat_s = 60.0 / float(cfg["timing"]["bpm"])


func timing(key: String) -> float:
	return float(cfg["timing"][key])


func phase_s() -> float:
	return timing("phase_beats") * beat_s


## Starts a run at `start_id` with fresh energy. Song time 0 is the first downbeat.
func begin(start_id: String) -> void:
	level = Level.new()
	level.mode = "defense"
	level.bpm = float(cfg["timing"]["bpm"])
	level.ticks_per_beat = TICKS
	level.beats_per_bar = 4
	level.title = "Continuous run"
	level.sequence_threshold = float(cfg["judgement"]["pass_credit"])
	judge = PadJudge.new()
	var w: Dictionary = cfg["judgement"]["windows_ms"]  # the run's own windows: nothing is read from the old campaign rules
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	energy = float(cfg["energy"]["start"])
	over = false
	_events = []
	_cast_queue = []
	_depleted_t = -1.0
	_over_t = -1.0
	if _regridded:  # (a track scene re-gridded this engine in an earlier run: song time 0 is the first downbeat again)
		grid_origin = 0.0
		grid_beat0 = 0
		beat_s = 60.0 / float(cfg["timing"]["bpm"])
		_regridded = false
	_blocks_total = 0
	_note_id = 0
	phase_n = 0
	lap_extra = 0
	phase_t0 = 0.0
	_next_phase_charted = false
	_enter(start_id, 0.0, true)


## Starts again after an excursion (the Bassment): the song clock has run on, so the new phase begins at song time `t0` (a downbeat); a fresh level and judge, the
## crowd's energy kept, the phase count carried on. The cues and ticks are absolute, so nothing but `phase_t0` knows the run was away.
func resume(start_id: String, t0: float) -> void:
	var keep := energy
	var n := phase_n
	level = Level.new()
	level.mode = "defense"
	level.bpm = float(cfg["timing"]["bpm"])
	level.ticks_per_beat = TICKS
	level.beats_per_bar = 4
	level.title = "Continuous run"
	level.sequence_threshold = float(cfg["judgement"]["pass_credit"])
	judge = PadJudge.new()
	var w: Dictionary = cfg["judgement"]["windows_ms"]
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	energy = keep
	over = false
	away = ""
	_events = []
	_cast_queue = []
	_depleted_t = -1.0
	_over_t = -1.0
	_next_phase_charted = false
	phase_n = n
	_enter(start_id, t0, true)


## The run arrives here from another run (a portal into a path, or an ending back to the Warehouse): this engine's grid starts on the downbeat `t0` of the new clock, the crowd's energy and the phase
## count are carried over, and the scene `start_id` begins on drums alone.
func arrive(start_id: String, t0: float, p_energy: float, p_phase_n: int, p_lap_extra: int = 0) -> void:
	grid_origin = t0
	energy = p_energy
	phase_n = p_phase_n
	lap_extra = p_lap_extra
	resume(start_id, t0)


func _enter(id: String, t0: float, chart_now: bool) -> void:
	var prev := node_id if phase_n > 0 else ""
	var tp := track_plan_of(id)  # ({} for an ordinary scene, and always when track scenes are off)
	var from_bpm := 60.0 / beat_s
	if not tp.is_empty() or _regridded:
		_regrid(t0, float(tp["bpm"]) if not tp.is_empty() else float(cfg["timing"]["bpm"]))
	track = tp
	node_id = id
	var n: Dictionary = data.nodes[id]
	depth = int(n["depth"])
	phase_n += 1
	phase_t0 = t0
	scene_t0 = t0
	lap = 1
	laps = data.laps_of(id) if tp.is_empty() else int(tp["laps"])
	doors_from_lap = int(tp.get("doors_from_lap", 0))
	_lap_track_t0 = float(tp.get("entry_t", 0.0))
	_lap_stage = 0
	_lap_bass_origin = -1
	stage = 0
	block = 0
	bass_origin = -1
	choice = ""
	window_open = false
	route_locked = false
	_locked_chart = ""
	stage_of_block = [0]
	block_credit = []
	_next_block_notes = {}
	part_offset = {"drums": 0.0, "bass": 0.0}
	if chart_now or not _next_phase_charted:
		_chart_block(0, 0, depth)
	_next_phase_charted = false
	_next_block_notes[0] = true
	if hotspots != null:
		hotspots.begin_scene(id, energy)
	_queue_scene_cast(id, t0)
	if _regridded and absf(60.0 / beat_s - from_bpm) > 1e-9:
		_emit({"kind": "tempo", "t": t0, "node": id, "bpm": 60.0 / beat_s, "beat_s": beat_s, "from_bpm": from_bpm})
	var ps := {"kind": "phase_start", "node": id, "world": n["world"], "scene": n["scene"], "from": prev, "depth": depth, "t": t0, "phase": phase_n, "treatment": n["treatment"],
		"audio": n["audio"], "temporary": n["temporary"], "fresh": phase_n == 1, "path": data.path_id, "lap": 1, "laps": laps, "lap_extra": lap_extra}
	if not tp.is_empty():
		ps["track"] = str(tp["track"])
	_emit(ps)
	if not tp.is_empty():
		_emit({"kind": "track_start", "t": t0, "node": id, "track": str(tp["track"]), "dir": str(tp["dir"]), "chart": str(tp["chart"]), "bpm": float(tp["bpm"]), "beat_s": beat_s, "entry": str(tp["entry"]),
			"entry_bar": int(tp["entry_bar"]), "track_t": float(tp["entry_t"]), "laps": laps, "doors_from_lap": doors_from_lap, "duration_s": float(tp["duration_s"]), "index": int(tp.get("index", 0)), "phase": phase_n})
	_emit({"kind": "mix", "stage": 0, "t": t0, "gains": cfg["stages"][0]["gains"], "cue": cfg["stages"][0]["cue"]})


## A new beat grid from the downbeat `t0` at `bpm` (a track scene, or the scene after one): the run's beat count goes on from where the old grid had got to, so ticks keep growing.
func _regrid(t0: float, bpm: float) -> void:
	grid_beat0 += int(round((t0 - grid_origin) / beat_s))
	grid_origin = t0
	beat_s = 60.0 / bpm
	level.bpm = bpm
	level.song_offset_ms = int(round((grid_origin - float(grid_beat0) * beat_s) * 1000.0))  # (so Level.seconds_to_tick, which the pad view reads, counts the same ticks as the cues, to the millisecond)
	_regridded = true


## The track plan of scene `id` ({} when it is not a track scene: no track_scenes data, no assignment, no pack). Data, not engine state: safe to call for any scene (the routes' scenes, for loading ahead).
func track_plan_of(id: String) -> Dictionary:
	return data.track_scenes.plan_of(id) if data != null and data.track_scenes != null else {}


func is_track_scene() -> bool:
	return not track.is_empty()


## The current track scene for overlays and the HUD ({} in an ordinary scene): {track, lap, laps, entry_bar, doors_from_lap, bpm, chart, doors_open}.
func track_info() -> Dictionary:
	if track.is_empty():
		return {}
	return {"track": str(track["track"]), "lap": lap, "laps": laps, "entry_bar": int(track["entry_bar"]), "doors_from_lap": doors_from_lap, "bpm": float(track["bpm"]), "chart": str(track["chart"]),
		"doors_open": _doors_open()}


## Where the track is (track seconds) at song time `t` of the current lap (-1 in an ordinary scene).
func track_t_at(t: float) -> float:
	return _lap_track_t0 + (t - phase_t0) if not track.is_empty() else -1.0


## A track scene's lap whose window opens (doors_from_lap on); false in every ordinary scene.
func _doors_open() -> bool:
	return not track.is_empty() and lap >= doors_from_lap


func _emit(ev: Dictionary) -> void:
	_events.append(ev)


## Scenes entered so far in this run, counting the current one (phase_n counts every lap).
func scene_index() -> int:
	return phase_n - lap_extra


## Song time of a beat of the current phase.
func t_of(phase_beat: float) -> float:
	return phase_t0 + phase_beat * beat_s


## The beat of a block at which it is judged (and a hotspot commits).
func _decision_beat() -> float:
	return maxf(timing("decision_beat"), timing("cue_span_beats") + judge.accept_s / beat_s + 0.05)


## The routes out of the current scene: [{to, dir, label, default, in_world, title}]: the paths inside the world, or at the exit scene the other worlds.
func options() -> Array:
	var out: Array = []
	var first := true
	for e in data.nodes[node_id]["next"]:
		var o: Dictionary = (e as Dictionary).duplicate()
		o["default"] = first
		o["in_world"] = data.nodes.has(str(e["to"])) and str(data.nodes[str(e["to"])]["world"]) == str(data.nodes[node_id]["world"])  # (an ending's "run:warehouse" is no scene)
		o["title"] = data.route_title(node_id, str(e["to"]))
		first = false
		out.append(o)
	return out


func default_route() -> String:
	return str(data.nodes[node_id]["next"][0]["to"])


## The player picks a route (by destination id); allowed until the phase ends. Returns false when the id is not one of the routes.
func choose(to: String) -> bool:
	if lap < laps and not _doors_open():  # a lap before the last has no choice to make (the window and the commit belong to the final lap; a track scene's open laps excepted)
		return false
	if hotspots != null:  # with hotspots the route is the outcome of the selected one: choosing a route taps the hotspot that leads there (scripted play, old callers)
		return hotspots.select_route(to, block, window_open)
	for e in data.nodes[node_id]["next"]:
		if str(e["to"]) == to:
			if not route_allowed(to):
				return false
			choice = to
			return true
	return false


func choose_dir(dir: String) -> bool:
	for e in data.nodes[node_id]["next"]:
		if str(e["dir"]) == dir:
			return choose(str(e["to"]))
	return false


## False for a route whose chart pack differs from the one already charted for the next phase's first block (the lock falls at the last block's decision, beat 60.5).
func route_allowed(to: String) -> bool:
	return not route_locked or not data.nodes.has(to) or _chart_key(to) == _locked_chart


## What the route lock compares: a scene's chart pack, or for a track scene its track and chart (two routes into different tracks chart differently, whatever their packs).
func _chart_key(to: String) -> String:
	var tp := track_plan_of(to)
	return str(data.nodes[to]["chart"]) if tp.is_empty() else "track:%s:%s" % [tp["track"], tp["chart"]]


func selected_route() -> String:
	if hold:
		return node_id
	if choice != "":
		return choice
	if hotspots != null and hotspots.selected != "":  # the route the selected hotspot leads to on success (the final outcome is only known at the commit)
		var r := str((hotspots.get_hotspot(hotspots.selected).get("on_success", {}) as Dictionary).get("route", ""))
		if r != "" and not HotspotContract.is_special_route(r):  # (the Bassment, a portal or the way back are known only at the commit)
			return r
	return default_route()


## The player leaves the path by the pause menu: the way back to the Warehouse becomes the choice. Allowed in a path only; returns false elsewhere.
func force_leave() -> bool:
	if not data.is_path() or away != "":
		return false
	choice = LEAVE_ROUTE
	return true


## True when this phase ends by leaving the scene: the choice window is open (the final lap), or the player has asked to leave the path during a lap before the last (the lap then ends the scene).
func exit_pending() -> bool:
	return window_open or (lap < laps and choice == LEAVE_ROUTE)


## The special route the phase ends by ("path:<id>" / "run:warehouse"), "" when it ends in a scene of this run.
func special_route() -> String:
	var r := selected_route()
	return r if HotspotContract.is_special_route(r) and not data.nodes.has(r) else ""


func press(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.press(pad, t, touch)


func release(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.release(pad, t, touch)


## The family cued in block `b` of the current phase.
func cue_family(b: int) -> String:
	return str(cfg["stages"][int(stage_of_block[mini(b, stage_of_block.size() - 1)])]["cue"])


## Advance to song time `t`; returns the events that became due, in order.
func update(t: float) -> Array:
	if level == null:
		return []
	if away != "":  # handed off: the run lives in another engine now
		var rest := _events
		_events = []
		return rest
	judge.update(t)
	for ev in judge.drain_events():
		_emit({"kind": "judge", "event": ev, "t": t})
	if _depleted_t >= 0.0:
		if not over and t >= _over_t:
			over = true
			_emit({"kind": "run_over", "t": _over_t, "energy": energy, "phase": phase_n, "scenes": scene_index(), "node": node_id})
	else:
		_run_due(t)
		if _depleted_t < 0.0 and block == 4 and t >= t_of(timing("phase_beats")):
			_commit()
			var first := _events
			_events = []
			first.append_array(update(t))
			return first
	var out := _events
	_events = []
	return out


## Everything due by song time `t` inside the current phase, in time order: the blocks' decisions and the cast lines (a line on the same instant as a decision goes first, so its conditions read
## the energy as it stood at that beat). A stall across several of either gives the same events as small steps would.
func _run_due(t: float) -> void:
	var bb := int(timing("block_beats"))
	var guard := 0
	while guard < 96 and _depleted_t < 0.0:
		var t_dec := t_of(float(block * bb) + _decision_beat()) if block <= 3 else INF
		var t_cast: float = float(_cast_queue[0]["t"]) if not _cast_queue.is_empty() else INF
		if t_cast >= t_of(timing("phase_beats")) and lap < laps:  # a line of a later lap waits for its lap (a stall must not fire it before the lap begins)
			t_cast = INF
		if minf(t_dec, t_cast) > t:
			break
		guard += 1
		if t_cast <= t_dec:
			_fire_cast(_cast_queue.pop_front())
		else:
			_decide(block, t_dec)


## The scene's cast lines, scheduled on the clock: line k fires at `t0 + at_beat * beat_s` (ties in file order); `at_beat` counts from the scene's first downbeat across all its laps. Lines of the scene just left that never fired are dropped; a committed outcome's
## cinematic cast, already queued, plays on.
func _queue_scene_cast(id: String, t0: float) -> void:
	_cast_queue = _cast_queue.filter(func(q: Dictionary) -> bool: return str(q["source"]) != "scene")
	var lines: Array = data.nodes[id].get("cast", [])
	for i in lines.size():
		var line: Dictionary = lines[i]
		_cast_queue.append({"t": t0 + float(line["at_beat"]) * beat_s, "seq": _cast_seq, "beat": float(line["at_beat"]), "index": i, "line": line, "source": "scene", "node": id, "phase": phase_n + int(floor(float(line["at_beat"]) / timing("phase_beats"))), "name": ""})
		_cast_seq += 1
	_sort_cast()


func _sort_cast() -> void:
	_cast_queue.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["t"]) < float(b["t"]) if float(a["t"]) != float(b["t"]) else int(a["seq"]) < int(b["seq"]))


## An outcome's cinematic with cast lines: each line is due `at_beat` beats after the commit at `t_commit`.
func _queue_cinematic_cast(cin: Dictionary, name: String, t_commit: float) -> void:
	var lines: Array = cin.get("cast", [])
	for i in lines.size():
		var line: Dictionary = lines[i]
		_cast_queue.append({"t": t_commit + float(line["at_beat"]) * beat_s, "seq": _cast_seq, "beat": float(line["at_beat"]), "index": i, "line": line, "source": "cinematic", "node": node_id, "phase": phase_n, "name": name})
		_cast_seq += 1
	_sort_cast()


## A cast line comes due: if its conditions hold (the crowd's energy, the world-state flags) one `cast` event goes out, stamped with the line's own time. RunPlay hands it to the crowd.
func _fire_cast(q: Dictionary) -> void:
	var line: Dictionary = q["line"]
	var has_flag := func(f: String) -> bool: return hotspots != null and hotspots.has_flag(f)
	if not RunActing.conditions_hold(line, energy, has_flag):
		return
	if line.has("piece"):  # a set piece switched on, off or pulsed (the river rising, the storm calming)
		_emit({"kind": "cast", "t": float(q["t"]), "beat": float(q["beat"]), "index": int(q["index"]), "source": str(q["source"]), "name": str(q["name"]), "node": str(q["node"]), "phase": int(q["phase"]),
			"actor": "", "act": "", "face": "", "look_at": "", "beats": 0.0, "piece": str(line["piece"]), "op": str(line["op"]), "hide": false})
		return
	_emit({"kind": "cast", "t": float(q["t"]), "beat": float(q["beat"]), "index": int(q["index"]), "source": str(q["source"]), "name": str(q["name"]), "node": str(q["node"]), "phase": int(q["phase"]),
		"actor": str(line["actor"]), "act": str(line.get("act", "")), "face": str(line.get("face", "")), "look_at": str(line.get("look_at", "")), "beats": float(line.get("beats", RunActing.HOLD_BEATS)),
		"piece": "", "op": "", "hide": bool(line.get("hide", false))})


func _commit() -> void:
	var t0 := t_of(timing("phase_beats"))
	if lap < laps and choice != LEAVE_ROUTE:  # not the last lap: the scene goes on, the same music, the bass already in staying in
		_start_lap(t0)
		return
	var to := selected_route()
	if HotspotContract.is_path_route(to) or HotspotContract.is_run_route(to):  # leaves this run's worlds: no next scene here, the scene hands the clock and the pads to the other run
		_emit({"kind": "route_commit", "from": node_id, "to": to, "chosen": true, "t": t0, "treatment": "none", "same_world": false})
		window_open = false
		away = to
		_emit({"kind": "path_handoff", "route": to, "target": HotspotContract.path_of(to) if HotspotContract.is_path_route(to) else "warehouse", "from": node_id, "path": data.path_id,
			"ending": str(data.nodes[node_id].get("ending", "")), "t": t0, "energy": energy, "phase": phase_n, "world": str(data.nodes[node_id]["world"]), "lap_extra": lap_extra})
		_track_end(t0, "handoff", to)
		return
	_emit({"kind": "route_commit", "from": node_id, "to": to, "chosen": choice != "", "t": t0, "treatment": data.nodes[to]["treatment"],
		"same_world": str(data.nodes[to]["world"]) == str(data.nodes[node_id]["world"])})
	window_open = false
	_track_end(t0, "route", to)
	_enter(to, t0, false)


## A track scene ends at song time `t` (nothing in an ordinary scene).
func _track_end(t: float, reason: String, to: String) -> void:
	if track.is_empty():
		return
	_emit({"kind": "track_end", "t": t, "node": node_id, "track": str(track["track"]), "track_t": track_t_at(t), "reason": reason, "to": to})


## The next lap of the same scene begins on the downbeat `t0`: a new phase number (its own cues, blocks and judge results), the mix stage decided at the last block's decision (the stage of the last block, one
## step on after a pass), the bass phrase as it was (`bass_origin` is kept: every pack's phrase tiles a lap, so the origin counts modulo the phrase), no window and no commit until the last lap.
func _start_lap(t0: float) -> void:
	lap += 1
	phase_n += 1
	lap_extra += 1
	phase_t0 = t0
	stage = _lap_stage
	block = 0
	if _lap_bass_origin >= 0:
		bass_origin = _lap_bass_origin
	stage_of_block = [stage]
	block_credit = []
	_next_block_notes = {0: true}
	_next_phase_charted = false
	window_open = false
	if hotspots != null:
		hotspots.energy = energy
	_emit({"kind": "lap_start", "node": node_id, "lap": lap, "laps": laps, "t": t0, "phase": phase_n, "stage": stage, "lap_extra": lap_extra, "scene_t0": scene_t0})
	if not track.is_empty():  # a track scene's next lap: the track goes on (or has wrapped), the touch state starts over
		_lap_track_t0 = _next_lap_track_t0
		choice = ""
		if hotspots != null:
			hotspots.begin_lap(energy)
		_emit({"kind": "track_lap", "t": t0, "node": node_id, "track": str(track["track"]), "lap": lap, "laps": laps, "track_t": _lap_track_t0, "doors_open": _doors_open(), "last": lap == laps, "phase": phase_n})


## Judge block `b` at its decision beat, update the mix stage and energy, chart what comes next.
func _decide(b: int, t_dec: float) -> void:
	judge.update(t_dec)
	var credit := block_credit_of(b)
	var passed := credit >= float(cfg["judgement"]["pass_credit"])
	var neutral := not track.is_empty() and _block_cue_count(b) == 0  # a track scene's block without cues (the focus rests): it passes, no energy, no stage step
	block_credit.append(credit)
	var e: Dictionary = cfg["energy"] if track.is_empty() else _track_energy()
	var pc := float(cfg["judgement"]["pass_credit"])
	if neutral:
		pass
	elif passed:
		energy += float(e["pass_gain"]) + float(e["pass_bonus"]) * (credit - pc) / maxf(1.0 - pc, 0.001)
	else:
		energy -= float(e["fail_loss"]) * (pc - credit) / pc + (3.0 if track.is_empty() else float(e["fail_flat"]))
	energy = clampf(energy, 0.0, float(e["max"]))
	var boundary_beat := float((b + 1) * int(timing("block_beats")))
	var next_stage := stage
	if b < 3 and passed and not neutral:
		next_stage = mini(stage + 1, 3)
	var br := {"kind": "block_result", "block": b, "credit": credit, "passed": passed, "energy": energy, "stage": stage, "next_stage": next_stage, "t": t_dec,
		"node": node_id, "phase": phase_n, "lap": lap, "laps": laps}
	if not track.is_empty():
		br["neutral"] = neutral
		br["track"] = str(track["track"])
	_emit(br)
	block = b + 1
	if hotspots != null and energy > 0.0 and not hold:
		_hotspot_decision(b, passed, t_dec, credit)
	if energy <= 0.0:
		_depleted_t = t_of(boundary_beat)
		_over_t = _depleted_t + float(cfg["timing"]["fade_beats"]) * beat_s
		_emit({"kind": "depleted", "t": _depleted_t, "fade_s": _over_t - _depleted_t, "node": node_id})
		_track_end(_depleted_t, "depleted", "")
		return
	if b == 3 and not track.is_empty():
		_track_last_block(t_dec)
	if b < 3:
		stage = next_stage
		stage_of_block.append(stage)
		var st: Dictionary = cfg["stages"][stage]
		if stage >= 1 and bass_origin < 0:
			bass_origin = int(boundary_beat)
			_emit({"kind": "reveal", "beat": bass_origin, "t": t_of(boundary_beat), "node": node_id, "block": b + 1})
		_emit({"kind": "mix", "stage": stage, "t": t_of(boundary_beat), "gains": st["gains"], "cue": st["cue"], "beat": boundary_beat})
		_chart_block(b + 1, b + 1, depth)
		_next_block_notes[b + 1] = true
		if b == 2 and (lap == laps or _doors_open()):  # the choice window is the last block of the last lap: riser when the final bass stage is reached by beat 49, a fall otherwise (and of a track scene's open laps)
			window_open = true
			var rw := {"kind": "route_window", "t": t_of(boundary_beat), "effect": "riser" if stage == 3 else "fall", "options": options(),
				"default": default_route(), "stage": stage, "lap": lap}
			if not track.is_empty():
				rw["last"] = lap == laps
				rw["track"] = str(track["track"])
			_emit(rw)
	elif lap < laps:
		_chart_next_lap(passed and not neutral)  # the scene goes on: the next lap's first block, in the stage this block leaves the mix in
	else:
		# the last block is over: chart the next phase's first block now from the selected route, and lock it
		if hold:
			choice = node_id
		_chart_next_phase()


## A track scene's last block of a lap has been judged (and the hotspots have committed, or not). An open lap where an exit was touched (the commit made `choice` a route out, or a plain choose(),
## or the pause menu's leave) becomes the last lap; an open lap where nothing was touched closes its window (no door walk) and the scene goes on. A minigame holding the run past the plan's final
## lap adds one more lap.
func _track_last_block(t_dec: float) -> void:
	if lap < laps and _doors_open():
		if choice != "" and choice != node_id and not hold:
			laps = lap
			_emit({"kind": "track_last_lap", "t": t_dec, "node": node_id, "track": str(track["track"]), "lap": lap, "ends_t": t_of(timing("phase_beats")), "route": choice})
		else:
			if choice == node_id:  # (an activity that keeps the player here: nothing about leaving was chosen)
				choice = ""
			window_open = false
	elif lap >= laps and hold:
		laps = lap + 1
		window_open = false
		_emit({"kind": "track_extend", "t": t_dec, "node": node_id, "track": str(track["track"]), "laps": laps})


## Cues charted for block `b` of the current phase.
func _block_cue_count(b: int) -> int:
	var n := 0
	for i in range(level.notes.size() - 1, -1, -1):
		var note: Dictionary = level.notes[i]
		if int(note["phase"]) < phase_n:
			break
		if int(note["phase"]) == phase_n and int(note["block"]) == b:
			n += 1
	return n


## The energy numbers of a track scene's block: run.json `energy`, with `energy.track` over it (`fail_flat` is the fixed part of a fail's loss, 3 in an ordinary scene).
func _track_energy() -> Dictionary:
	if _track_e.is_empty():
		_track_e = (cfg["energy"] as Dictionary).duplicate()
		_track_e["fail_flat"] = 3.0
		var over: Variant = (cfg["energy"] as Dictionary).get("track", {})
		if typeof(over) == TYPE_DICTIONARY:
			for k in (over as Dictionary):
				if str(k) != "note":
					_track_e[str(k)] = float(over[k])
	return _track_e


## The hotspot window's decisions at the block's decision beat (inside the cue-free guard): the early window (a way into the Bassment) commits at blocks 0 and 1, the final one at block 3 (the route
## lock beat), where the outcome's route becomes the engine's choice before the next phase is charted from it. The outcome's energy is applied here (never to the point of depletion).
func _hotspot_decision(b: int, passed: bool, t_dec: float, credit := -1.0) -> void:
	hotspots.energy = energy
	var out: Dictionary = {}
	if b <= 2:
		out = hotspots.on_block(b, passed, credit)
	elif lap < laps and not (_doors_open() and _exit_touched()):
		return  # (no window, no commit before the last lap; on a track scene's open lap, none unless an exit was touched)
	else:
		out = hotspots.commit_final(passed, credit)
		if not out.is_empty():
			choice = str(out["route"])
	if out.is_empty():
		return
	if float(out["energy"]) != 0.0:
		energy = clampf(energy + float(out["energy"]), 1.0, float(cfg["energy"]["max"]))
		hotspots.energy = energy
	_emit({"kind": "hotspot_commit", "t": t_dec, "block": b, "node": node_id, "phase": phase_n, "outcome": out, "energy": energy})
	if (out["cinematic"] as Dictionary).has("cast"):  # a setback that is acted: the cinematic's cast lines run from the commit
		_queue_cinematic_cast(out["cinematic"], str(out["cinematic_name"]), t_dec)


## On a track scene's open lap: an available final-window hotspot is selected (touching it leaves by it, or by its outcome's route).
func _exit_touched() -> bool:
	var h := hotspots.get_hotspot(hotspots.selected) if hotspots.selected != "" else {}
	return not h.is_empty() and RunHotspots.window_of(h) == "final" and hotspots.is_available(h)


## The last block of a lap that is not the final one has been judged: the next lap starts in the stage this block leaves the mix in (a pass steps it on, as at every block; the bass already in stays in), its
## first block is charted now (one block ahead, as ever) and the mix change and a first reveal at the boundary are announced at the boundary's song time.
func _chart_next_lap(passed: bool) -> void:
	var boundary := timing("phase_beats")
	var next_stage := mini(stage + 1, 3) if passed else stage
	_lap_stage = next_stage
	_lap_bass_origin = bass_origin
	if next_stage >= 1 and bass_origin < 0:
		_lap_bass_origin = 0  # revealed on this very downbeat: lap-relative beat 0
	var st: Dictionary = cfg["stages"][next_stage]
	if next_stage != stage:
		_emit({"kind": "mix", "stage": next_stage, "t": t_of(boundary), "gains": st["gains"], "cue": st["cue"], "beat": 0.0, "lap": lap + 1})
	if _lap_bass_origin == 0 and bass_origin < 0:
		_emit({"kind": "reveal", "beat": 0, "t": t_of(boundary), "node": node_id, "block": 0, "lap": lap + 1})
	if not track.is_empty():
		_track_next_lap_position(t_of(boundary))
	_chart_block(0, 0, depth, node_id, true, next_stage)


## Where the track will be at the next lap's downbeat `t_next`: on from this lap, or back to the entry bar when fewer than 16 bars of the track would be left (a hold past the plan).
func _track_next_lap_position(t_next: float) -> void:
	var lap_s := float(track["lap_s"])
	var nxt := _lap_track_t0 + lap_s
	if nxt + lap_s > float(track["duration_s"]) + 1e-6:
		_emit({"kind": "track_wrap", "t": t_next, "node": node_id, "track": str(track["track"]), "lap": lap + 1, "track_t": float(track["entry_t"]), "from_track_t": nxt,
			"decided_t": t_of(3.0 * timing("block_beats") + _decision_beat())})
		nxt = float(track["entry_t"])
	_next_lap_track_t0 = nxt


func _chart_next_phase() -> void:
	var to := selected_route()  # the player's pick so far, else the default: the chosen world's own chart, then locked
	if not data.nodes.has(to):  # the phase ends by a path portal or an ending's way back: there is no next scene to chart
		return
	_chart_block(0, 0, int(data.nodes[to]["depth"]), to, true)
	_next_phase_charted = true
	route_locked = true
	_locked_chart = _chart_key(to)


## Credit of block `b` of the current phase: the mean credit of its cues (1 when it has none).
func block_credit_of(b: int) -> float:
	var sum := 0.0
	var n := 0
	for i in level.notes.size():
		var note: Dictionary = level.notes[i]
		if int(note["phase"]) == phase_n and int(note["block"]) == b:
			n += 1
			sum += judge.credit[i] if judge.is_resolved(i) else 0.0
	return 1.0 if n == 0 else sum / float(n)


## Appends the cues of block `b` (stage `stage_i` of the phase) to the level and the judge.
func _chart_block(b: int, stage_i: int, at_depth: int, node_for_chart: String = "", next_phase := false, lap_stage := -1) -> void:
	var nid := node_for_chart if node_for_chart != "" else node_id
	var new_scene := next_phase and lap_stage < 0  # (lap_stage >= 0: the first block of the next lap of this scene, in that stage, with the bass phrase going on)
	if (new_scene and not track_plan_of(nid).is_empty()) or (not new_scene and not track.is_empty()):
		_chart_track_block(b, next_phase, new_scene, nid)
		return
	var st_idx := lap_stage if lap_stage >= 0 else (int(stage_of_block[stage_i]) if stage_i < stage_of_block.size() and not next_phase else 0)
	var fam := str(cfg["stages"][st_idx]["cue"])
	var block_beats := int(timing("block_beats"))
	var start_beat := b * block_beats
	var pack: Dictionary = data.packs[data.chart_pack_at(nid, start_beat)]  # the pack of the section playing at this block (the scene's chart pack when it has no arrangement)
	var tier := str(data.tier_of(at_depth))
	var cues: Array = pack["tiers"][tier]["drums" if fam == "drums" else "bass"]
	var phrase_beats := int(pack["phrase_beats"])
	var origin := 0 if fam == "drums" or new_scene else maxi(_lap_bass_origin if lap_stage >= 0 else bass_origin, 0)
	origin = maxi(origin, data.section_start_at(nid, start_beat))  # a new section's loops start with the section, so its phrase does too
	var pos := ((start_beat - origin) % phrase_beats + phrase_beats) % phrase_beats  # phrase beat the block starts at
	var span := timing("cue_span_beats")
	var tpb := level.ticks_per_beat
	var phase_n_for := phase_n + 1 if next_phase else phase_n
	var phase_beat0 := phase_n_for_first_beat(phase_n_for)
	var added: Array = []
	for c in cues:
		var off: int = int(c[0]) - pos * tpb
		if off < 0 or off >= block_beats * tpb:
			continue
		var beat_in_block := float(off) / float(tpb)
		if beat_in_block > span + 1e-6:
			continue
		var dur: int = int(c[1])
		if dur > 0:
			dur = mini(dur, int(round((span - beat_in_block) * tpb)))
			if dur < 480:
				dur = 0
		var gbeat := phase_beat0 + start_beat + off / float(tpb)
		var tick := int(round(gbeat * tpb))
		var tm := grid_origin + float(tick) * 60.0 / (level.bpm * float(tpb)) + (float(part_offset["drums"]) if fam == "drums" else float(part_offset["bass"])) * (0.0 if new_scene else 1.0)
		var dur_s := float(dur) * 60.0 / (level.bpm * float(tpb))
		if _regridded:  # (after a track scene: the grid starts at this scene's downbeat, `grid_beat0` beats in; the next scene's first block is on its own tempo from the next downbeat)
			var bs := beat_s if not new_scene else 60.0 / float(cfg["timing"]["bpm"])
			var t_base := grid_origin if not new_scene else t_of(timing("phase_beats"))
			var b_base := grid_beat0 if not new_scene else phase_beat0
			tm = t_base + (float(tick) / float(tpb) - float(b_base)) * bs + (float(part_offset["drums"]) if fam == "drums" else float(part_offset["bass"])) * (0.0 if new_scene else 1.0)
			dur_s = float(dur) / float(tpb) * bs
		var fam_c := str(c[3]) if c.size() > 3 else fam
		added.append({"id": "r%05d" % _note_id, "tick": tick, "duration_ticks": dur, "end_tick": tick + dur, "time": tm, "end_time": tm + dur_s,
			"pad": int(c[2]), "button": int(c[2]), "family": fam_c, "lane": fam_c, "slot_id": fam_c, "type": "hold" if dur > 0 else "tap", "seq": _blocks_total,
			"phase": phase_n_for, "block": b, "voice": fam})
		_note_id += 1
	added.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	for a in added:
		level.notes.append(a)
	var block_start_tick := int(round((phase_beat0 + start_beat) * tpb))
	var pads := {}
	if fam == "drums":
		pads = {"1": {"family": "kick", "ref": ""}, "4": {"family": "snare", "ref": ""}}
	else:
		for p in range(1, 5):
			pads[str(p)] = {"family": "bass", "ref": ""}
	level.sections.append({"id": "p%d_b%d" % [phase_n_for, b], "start_tick": block_start_tick, "end_tick": block_start_tick + block_beats * tpb, "mode": fam,
		"length_bars": block_beats / 4, "pads": pads, "phase": phase_n_for, "block": b})
	level.duration_ticks = maxi(level.duration_ticks, block_start_tick + block_beats * tpb)
	_blocks_total += 1
	judge.sync_notes()
	_emit({"kind": "cues", "phase": phase_n_for, "block": b, "family": fam, "count": added.size(), "first": level.notes.size() - added.size()})


## Appends the cues of block `b` of a track scene (docs/RUN_TRACK_SCENES.md "Cues"): the chart's cues whose track time falls in the block's 16 beats, moved to song time (the lap's downbeat plus the
## cue's distance from the lap's track time, so a cue sits exactly where the audio plays it), those after beat 12 of the block left out, a hold cut to end by beat 12 (a tap when less than half a beat
## is left). `next_phase`: the first block of the next lap (or, `new_scene`, of the next scene `nid`), charted one block ahead as ever.
func _chart_track_block(b: int, next_phase: bool, new_scene: bool, nid: String) -> void:
	var plan: Dictionary = track_plan_of(nid) if new_scene else track
	var lap_k := 1 if new_scene else (lap + 1 if next_phase else lap)
	var trk0 := float(plan["entry_t"]) if new_scene else (_next_lap_track_t0 if next_phase else _lap_track_t0)
	var t_lap := t_of(timing("phase_beats")) if next_phase else phase_t0
	var bs := float(plan["beat_s"])
	var block_beats := int(timing("block_beats"))
	var span := timing("cue_span_beats")
	var tpb := level.ticks_per_beat
	var phase_n_for := phase_n + 1 if next_phase else phase_n
	var phase_beat0 := phase_n_for_first_beat(phase_n_for)
	var w0 := trk0 + float(b * block_beats) * bs
	var w1 := w0 + float(block_beats) * bs
	var pack: TrackPack = plan.get("pack", null)
	var added: Array = []
	for c: Dictionary in plan["cues"]:
		var ct := float(c["t"])
		if ct < w0 - 1e-6:
			continue
		if ct >= w1 - 1e-6:
			break  # (a chart is sorted by time)
		var beat_in := (ct - w0) / bs
		if beat_in > span + 1e-6:  # the last 4 beats of a block are rest (the run's rule)
			continue
		var dur_b := float(c["dur"]) / bs
		if dur_b > 0.0:
			dur_b = minf(dur_b, span - beat_in)
			if dur_b < 0.5:
				dur_b = 0.0
		var tick := int(round((float(phase_beat0 + b * block_beats) + beat_in) * tpb))
		var dur := int(round(dur_b * tpb))
		var tm := t_lap + (ct - trk0)
		var pad := int(c["pad"])
		var voice := str(c["voice"])
		var kind := str(pack.voice_by_key(voice).get("kind", "")) if pack != null else ""
		var fam := ("kick" if pad <= 2 else "snare") if kind == "drums" else "bass"
		added.append({"id": "r%05d" % _note_id, "tick": tick, "duration_ticks": dur, "end_tick": tick + dur, "time": tm, "end_time": tm + dur_b * bs,
			"pad": pad, "button": pad, "family": fam, "lane": fam, "slot_id": fam, "type": "hold" if dur > 0 else "tap", "seq": _blocks_total,
			"phase": phase_n_for, "block": b, "voice": voice, "lap": lap_k, "track_t": ct})
		_note_id += 1
	added.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	for a in added:
		level.notes.append(a)
	var block_start_tick := int(round(float(phase_beat0 + b * block_beats) * tpb))
	var pads := {}
	for a in added:
		pads[str(a["pad"])] = {"family": a["family"], "ref": a["voice"]}
	level.sections.append({"id": "p%d_b%d" % [phase_n_for, b], "start_tick": block_start_tick, "end_tick": block_start_tick + block_beats * tpb, "mode": "track",
		"length_bars": block_beats / 4, "pads": pads, "phase": phase_n_for, "block": b})
	level.duration_ticks = maxi(level.duration_ticks, block_start_tick + block_beats * tpb)
	_blocks_total += 1
	judge.sync_notes()
	_emit({"kind": "cues", "phase": phase_n_for, "block": b, "family": "track", "count": added.size(), "first": level.notes.size() - added.size(), "track": str(plan["track"]), "lap": lap_k})


## Global beat index of the first beat of phase number `n` (1-based): the current phase (`phase_n`) starts at `phase_t0`; the next one 64 beats later.
func phase_n_for_first_beat(n: int) -> int:
	return grid_beat0 + int(round((phase_t0 - grid_origin) / beat_s)) + (n - phase_n) * int(timing("phase_beats"))


## Block `b` credit summary for tests and the HUD.
func progress_in_block(t: float) -> float:
	return clampf((t - t_of(float(block) * timing("block_beats"))) / (timing("block_beats") * beat_s), 0.0, 1.0)


## Clock-to-beat helper: the phase beat (0..64) a song time falls in.
func phase_beat_at(t: float) -> float:
	return (t - phase_t0) / beat_s


## The pad strip's meter: the current block's cues and the credit earned so far (an empty dictionary outside a cue span).
func progress_at(_t: float) -> Dictionary:
	if level == null or block > 3:
		return {}
	var n := 0
	var got := 0.0
	var done := 0
	for i in range(level.notes.size() - 1, -1, -1):
		var note: Dictionary = level.notes[i]
		if int(note["phase"]) < phase_n:
			break
		if int(note["phase"]) == phase_n and int(note["block"]) == block:
			n += 1
			if judge.is_resolved(i):
				done += 1
				got += judge.credit[i]
	if n == 0:
		return {}
	return {"index": block, "cues": n, "resolved": done, "credit": got}


## RunAudio measured that a part (drums, or bass with the synth) actually started `offset` seconds after its nominal grid time: its cues in this phase
## move by the change, so they sit on what the player hears. Cues already resolved keep their result.
func apply_part_offset(part: String, phase: int, offset: float) -> void:
	if phase != phase_n or not part_offset.has(part) or not track.is_empty():  # (a track scene's cues are the track's own times: no loop part to follow)
		return
	var delta := offset - float(part_offset[part])
	part_offset[part] = offset
	var fam_ok := (func(f: String) -> bool: return f == "kick" or f == "snare") if part == "drums" else (func(f: String) -> bool: return f == "bass")
	for i in range(level.notes.size() - 1, -1, -1):
		var n: Dictionary = level.notes[i]
		if int(n["phase"]) < phase_n:
			break
		if fam_ok.call(str(n["family"])) and not judge.is_resolved(i):
			n["time"] = float(n["time"]) + delta
			n["end_time"] = float(n["end_time"]) + delta
