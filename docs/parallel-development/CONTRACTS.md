# Shared contracts: bedsit raves (gameplay) and Doom worlds (environment)

Stage B1 of `LONG_RUN_PLAN.md`. Branch `wip/engine-contracts` -> `feature/shared-contracts`. Draft of 7 November 2026.
Both streams build against these shapes and the fixtures in `src/contracts/fixtures/`; `tests/test_contracts.gd` pins them
(`bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter contracts`).
Owners of the files named here: `OWNERSHIP.md`. A change to a shape is an amendment by the lead: this file, the fixture and the test together.

Code in `src/contracts/`: `ActivityMode` (contract 4/5 table), `RaveSave` (contract 2/6, pure functions on the save dict), `ContractShapes`
(a validator per shape plus the pure functions both streams must compute alike). Nothing there touches a node or the engine.

Timing words: song time `t` (seconds, the run's one clock, frozen by pause); a **block** is 16 beats, cues on beats 0..12, decision beat
`RunEngine._decision_beat()` about 12.75 (`run_engine.gd:325`), guard 12.75..16; a **phase/lap** is 4 blocks (64 beats). A block's cues are charted
at the previous block's decision beat (`_decide` -> `_chart_block`, `run_engine.gd:571`, `:762`).

**DISAGREE** marks a place where a brief and the code disagree; each says which way the contract goes.

---

## 1. Scene entry and exit

Purpose: one way in and out of any scene (bedsit, a rave, a Doom scene, a race's return), so the way home is always known.

```
SceneEntry = {scene_id: String, theme: "" | "space" | "magic" | "dinos" | "transport",
              arrival_pose: <waypoint id> | {at: [x, z], yaw: deg},
              entered_from: {} | {scene_id, spot},          # the way home: scene + the threshold spot it was left by
              transition: "world" | "passage"}
SceneExit  = {route: <route id> | "home", transition: "world" | "passage", threshold: <spot id>}
```

- `scene_id` is a run node id. Proposal: the opening is a path `content/paths/bedsit/run.json` (nodes `bedsit`, `rave.space`, `rave.magic`,
  `rave.dinos`, `rave.transport`), so RunData, RunEngine, the TransitionPort and the director work unchanged. `theme` is the rave's id.
- **world** transition (to another map): the player walks to `threshold` (a `player_move` started in the guard of the last block before the
  boundary), the passage frame shuts over the swap on the downbeat (as today, `run_journey.gd:81` `rail.arrival`), the new scene opens on
  `arrival_pose`. Requested through the port only: `port().request({id: "bedsit/rave.space", path: "bedsit", node: "rave.space", kind: &"scene", when: &"soonest"})`
  (`INTEGRATION_CONTRACT.md` section 3; `when: soonest` is what the Bassment uses, so leaving the bedsit does not wait a whole lap).
- **passage** (inside one map): a route (contract 3) or the existing same-world door walk (`RunJourney.leave_walk`, `run_journey.gd:100`); no port request.
- `"home"`: the destination is `bedsit` with `arrival_pose = bedsit_<facing>` where facing is `RaveSave` `bedsit_facing` (the player comes home facing the threshold they left by).
- `entered_from` is written by the gameplay host at entry; QuestRouter's `RouteState.history` stays the record of scenes (`route_state.gd:19`).

Sequence (bedsit -> rave): top region tap -> `RaveSave` facing -> theme -> port.request(soonest) -> `locked` -> approach walk to `threshold_<facing>` in the guard
-> `switched` on the downbeat -> `SceneEntry{scene_id: rave.<theme>, entered_from: {bedsit, threshold_<f>}, transition: world}` -> `rave_theme` saved.

Provided by: `TransitionPort`/`TransitionDirector` (lead), `RunJourney`/`RunRail` arrival and door walk (lead), path data (gameplay).
Fixture: `scene_entry.json`. Tests: `test_scene_entry_and_exit_shapes`.

- **DISAGREE (pose form)**: the Doom brief wants arrival poses; the engine moves only to waypoint ids (`story_player.gd:67`, `_plan_move`). The
  runtime takes a waypoint id; `{at, yaw}` is allowed in authoring data only and must be baked into a waypoint by `make_scenes.py` / the Doom converter.
- **Threshold (built, H1.6)**: the Doom scenes are **geography worlds** (`"geography": true` on the run.json `worlds` entry): one scene per world, its
  `down` route the stay (`loop: true`), its other routes leading to the entry scene of another geography world in any direction, at any depth, cycles
  through worlds allowed (`RunData._validate_geography_routes`). A route's threshold is the node's `thresholds[to]` when given, else the route's move
  `rail.routes[dir].to` (`RunJourney.threshold_of` / `threshold_move`). In a geography world a guide's tap is the decision (ruling 39): it commits at the
  tap and walks from there (`RunEngine.tap_commit` -> `hotspot_commit` -> `RunPlay._on_hotspot_commit` -> `RunJourney.commit_walk`); an untouched default walks from the lock, beat 61
  (`RunPlay._update_passage` -> `RunJourney.threshold_leave`). Either walk follows the move's `via` polyline over its `bars` (clamped 2..4), cut to
  end by the boundary, with its `hold_bars` only when there is time; the pads keep playing. Then the passage frame shuts, the stage swaps on the downbeat, and the destination's `rail.arrival` cuts to its `rail.arrive` and walks home.
  Shape for a generator: `docs/engine/GEOGRAPHY_WORLDS.md`.
- The bedsit must not be left by the rhythm (brief 2): its node's default destination is `{}` ("stay", port `set_default`) and it has no
  `on_miss`. Depletion would still end the run: hook H1.7.

## 2. Theme selection

Purpose: facing -> theme is data; a theme's look and placement are data; activity logic is shared.

`content/bedsit/themes.json` (fixture `bedsit_themes.json`):
```
{version: 1, scene_id: "bedsit", map: "bedsit", start_facing: "N",
 facings: {N: "space", E: "dinos", S: "magic", W: "transport"},          # fixed by the brief; the validator refuses another mapping
 facing_waypoints: {N: "bedsit_n", ...}, thresholds: {N: "threshold_n", ...}, turn_beats: 2.0,
 regions: {top|bottom|left|right: [x, y, w, h] fractions of the stage area},
 themes: {<theme>: "res://content/raves/<theme>.json"}}
```
`content/raves/<theme>.json` (fixture `theme_space.json`):
```
{id, scene_id, geography (the Doom map it borrows: mothership | chill | underworld | dock), map, track, arrival,
 props: [{id, role: stage_deck|bass_knob|cloakroom|bar|race_entrance|home_threshold|decor, sprite, spot | at}],
 customers: [{id, sprite_set, count, spot}],
 guides: [{id, sprite, spot, for: stage|cloakroom|bar|race|home}],               # one guide per destination (Doom brief 6)
 ingredients: 4 x {id, icon, color}, cloakroom_symbols: 4 x {id, icon} (distinct icons),
 stations: {stage|cloakroom|bar: {waypoint (the station's choice viewpoint), route (contract 3 id)}},
 race: {entrance: spot, course: <race course id>, activity: "race"}, home: {threshold: spot, route: "home"}}
```
Functions: `RaveSave.turn(facing, dir)` (-1 left, +1 right, 0 bottom: stay; wraps), `RaveSave.theme_of(facing, themes)`.
Sequence: left/right region tap -> `turn` -> `player_look`/`player_move` to `facing_waypoints[f]` over `turn_beats` (camera only) -> `bedsit_facing` saved.
Bottom: nothing moves. Top: contract 1.
Provided by: new content files (gameplay). Tests: `test_bedsit_themes_fixed_mapping`, `test_turning_wraps_and_bottom_stays`, `test_theme_data_shape`.

## 3. Rail destinations and arrival poses (with ruling 35a)

> Ruling 35 (a), the owner's direction of 7 November, game-wide: more moments with the camera relatively stationary: the rail arrives at a
> choice viewpoint and holds there, still, for the choice window, and journeys are paced with holds, not continuous drift.

```
Route = {id, map, from: waypoint,
         legs: [{to: waypoint, bars: 2..4, hold_bars: >= 0, style: walk|stagger|run|climb|carried, look?: waypoint | thing id}],
         arrive: {waypoint (= last leg's), choice_view: bool, hold: "window" (required when choice_view)},
         eye_m?: metres above the floor (default StoryMap.eye_height 1.6)}
```
- A leg is one `player_move {to, style, bars}`; the next leg starts after `bars + hold_bars` (move, then hold still). `ContractShapes.route_actions`
  gives the exact actions; `route_as_cinematic` gives the same route as a HotspotContract cinematic `{steps: [{move: walk, to, bars, style, look_at}]}`,
  so a route is played by the existing `RunJourney.hotspot_actions` (`run_journey.gd:116`) from a hotspot's `on_select` or outcome `cinematic`. Extension,
  not replacement: the song clock still starts every move (`t0` is a decision beat or the guard).
- Between waypoints StoryPlayer already walks the portal route `StoryMap.route()` (`story_map.gd:755`) and the eye follows the floors with a ramp at
  each portal (`story_player.gd:592`, `map.eye_height` `story_map.gd:29`). A polyline is the waypoint chain; corners are waypoints.
- **Choice viewpoint**: a waypoint with `choice_view: true`. The last leg holds at least `CHOICE_HOLD_BARS_MIN` = 4 bars (one block, the whole
  window) and `hold: "window"`: from arrival until the commit no move, no stroll, no glance, no head drift that moves a target under the finger.
  The touch targets are validated from that pose (contract 9).
- Recovery/failure moves (Doom brief 4) stay `rail.bad` places; each is also move-then-hold.

Provided by: `run_rail.gd`, `run_journey.gd`, `story_player.gd` (lead). Fixture: `route_space_to_stage.json`.
Tests: `test_route_shape_and_rail_actions`, `test_route_holds_at_choice_viewpoint`.

- **DISAGREE (leg length)**: a route wants bars per leg; `RunRail.pick_bars` clamps every move to 2..4 bars (`run_rail.gd:147`, `MOVE_BARS_MIN/MAX`
  `:14`). Contract keeps 2..4; a shorter leg needs H3.2.
- **DISAGREE (stillness)**: today every block adds a glance at beat 5 and a stroll at 6..9, also in the window block (`run_rail.gd:233` `ambient`,
  window glance clamped to 8 degrees) and the look-pass turns the head to the hotspots at beat 49 (`run_journey.gd:22`). Ruling 35 wants the
  camera still at a choice viewpoint: hook H3.1.

## 4. Activity entry, results and exit

```
enum ActivityMode.Mode {RHYTHM, REPLACE, OVERLAY}             # src/contracts/activity_mode.gd; json "mode", default "rhythm"
content/minigames/<id>.json += {kind, mode, controls: 0|2|4, control_ids, lead_in_beats (replace: >= 4), wobble_at/fall_at (0 outside rhythm),
                                theme_keys: [keys of the theme file merged into config], flags_on_complete: ["rave.{theme}.<puzzle>"]}
ActivityRequest = {activity_id, mode, theme, scene_id, return_pose: waypoint, config: <minigame json merged with theme_keys of the theme file>}
ActivityResult  = {activity_id, completed: bool, score: int, flags_to_set: [String], reason: done|left|fall|run_over|host,
                   race?: {won: bool, position: int, time_s: float}}
```
Modes: cloakroom and bar `replace` (2 and 4 controls), race `overlay`, the bass knob `rhythm` (proposal: it is short; the knob is a target in the
stage view like the blackjack table's), blackjack `replace` since A8b (ruling 40, owner 8 November: while seated the pad
slots are the four card controls and judging is suspended; getting up finishes on the resume boundary).

Entry (all modes): hotspot outcome `{"activity": id}` commits (`run_play.gd:1927`) -> host builds ActivityRequest -> `MinigameController.request(id,
t_commit, t_seat, exits)` (`minigame_controller.gd:80`; `t_seat` = the next block start) -> `engine.hold = true` (`:103`).
Replace adds, in `request`: `engine.suspend_rhythm(t_seat)` (H5.1). At `t_seat`: `lane_input.clear()`, `lane_input.enabled = false`, pads and note
lane hidden, the controls layer shown in the pad strip (H5.4).

Exit, replace (the clean boundary): the activity reports `is_done()` at `t_done` -> `B1 = ContractShapes.resume_boundary(t_done, t_phase0, beat_s)`:
the first block start not yet charted (its previous decision beat is after `t_done`) and at least `lead_in_beats` (4) after `t_done`
(at most about two blocks later) -> `engine.resume_rhythm(B1)` -> at `B1 - lead_in` the controls go, the pads and note lane return with the
cues of block B1 already falling (the lead-in), `lane_input.enabled = true` -> at `B1` the first judged cue; `engine.hold = false`, `_back_to_rail(B1)`.
Rhythm and overlay modes exit as today (`_finish` `minigame_controller.gd:187`).

Result: `MinigameActivity.result()` (H4.1) read once at `_finish`; the host applies `flags_to_set` (`RaveSave.apply_flag`, else `RunProgress.set_flag`),
`race` via `RaveSave.record_race`, then saves. Leaving mid-task (`reason: left`) keeps the activity's in-progress state in memory for the run
(`RaveSession`, gameplay-owned), keyed by theme + activity, so a return resumes (brief 5 "leave and return without corrupting").

Fixtures: `activity_cloakroom.json`, `activity_bar.json`, `activity_race.json`, `activity_bass.json`, `activity_request_result.json`.
Tests: `test_activity_configs`, `test_activity_requests_and_results`, `test_mode_rules_match_the_brief`, `test_resume_boundary`.

- **DISAGREE**: `MinigameActivity` views mount inside the stage's low-res viewport, stage area only (`run_minigame_host.gd:59`, layer 3); the replace
  controls must stand where the pads are, outside that viewport: H5.4.
- Entry from a final-window hotspot seats at the next phase start (as blackjack); an `any` window seats at the end of the touched block.

## 5. Input ownership and rhythm participation

Exactly one owner per tap: `hud` | `trial` | `pads` | `activity_controls` | `hotspots` | `world_regions` | `activity_view`.
`ContractShapes.tap_owner(area, mode, regions_on, trial, view_hit)` is the rule; the host's dispatcher must give the same answers.

| Situation | Mode | Pad strip | Stage area | Judging | Energy | Wobble/fall | Rail and route |
|---|---|---|---|---|---|---|---|
| Rave exploration | none | pads | hotspots | yes | yes | n/a | as today |
| Bedsit | none | pads | world_regions (4) | yes | no departure (H1.7) | n/a | stay by default |
| Cloakroom, bar | replace | activity_controls (2/4) | activity_view | **no** | **no** | **no** | held |
| Race | overlay | pads | world_regions (driving) | yes, feeds speed | yes | **no** | held |
| Blackjack, bass knob | rhythm | pads | activity_view | yes | yes | yes (2/3) | held |
| Bassment | (trial) | trial | trial | trial's | trial's | trial's | trial's |

`ActivityMode.rules(mode)` holds the same table. Regions: four fixed rects of the stage area (fixture `regions`, top 0.25..0.75 x 0..0.42, bottom
0.25..0.75 x 0.72..1, left 0..0.22, right 0.78..1), never overlapping, never over the pads (the pads are another area). These are screen regions
(bedsit, race), distinct from the Doom scenes' compositional choice regions, which are hotspots on world things (contract 9).

Replace mode, exactly: no cue charted for a block starting in `[t_seat, B1)`; cues already charted at or after `t_seat` are **withdrawn** (no
event, no miss, no mute, not drawn); such blocks decide as `neutral` (no energy, no stage step, `block_result.suspended = true`); the controller
ignores their results; `RunTrackMutes` sees no judge events, so no stem is muted for them; the journey is not fed (as today while `minigames.active()`,
`run_play.gd:995`); no hotspot commit (`engine.hold`, `run_engine.gd:597`). Music never pauses.

How this differs from today: `engine.hold` (`run_engine.gd:71`) holds the route and the hotspots only; its own comment says "phases, cues,
judging and energy go on as usual"; `MinigameController.on_block_result` (`minigame_controller.gd:136`) turns failed blocks into a wobble and a
fall; `RunPlay._handle` passes every `block_result` to it (`run_play.gd:1024`). A replace activity would today be thrown off the stool by
the notes it cannot play. Minimal engine change: H5.1 to H5.6 (below).

Fixture: `input_ownership.json`. Tests: `test_one_owner_per_tap`, `test_mode_rules_match_the_brief`.

## 6. Puzzle progression (save v3)

```
save (user://story_run.json) version 3 = version 2 keys + 
  bedsit_facing: "N"|"E"|"S"|"W"          per run  (a new run: "N")
  rave_theme: "" | <theme>                 per run  ("" in the bedsit / legacy run)
  raves: {<theme>: {bass_fixed: bool, cloakroom_done: bool, bar_done: bool,   # per run, per theme
                    race: {wins: int, runs: int, best: float (song s, 0 none)}}}   # kept across runs (career)
```
- `RaveSave.migrate(data)` fills missing or malformed keys (v2 -> v3) and is idempotent; `RaveSave.new_run(data)` (from `RunProgress.run_started`,
  `run_progress.gd:138`) resets the per-run keys and keeps race records. Written at every change (as the wallet is).
- Per visit vs per run (brief 4 "this visit/run", brief 10 "per rave theme within the run"): **per run**. Leaving a rave and coming back in the same
  run keeps all three flags; a new run clears them. Completion is shown in the world from these flags (changed props, guides' behaviour).
- Mid-activity progress (coats done, drinks served) is not saved; it lives in memory for the run.

Provided by: `run_progress.gd` (lead; calls RaveSave), `RaveSave` (contract). Fixtures: `save_v2.json`, `save_v3.json`.
Tests: `test_save_v3_fixture_and_migration`, `test_new_run_and_progress`.

- **DISAGREE (version)**: `RunProgress.load_data` treats any version but 2 as corrupt and renames the file `.corrupt` (`run_progress.gd:37`); the
  house convention so far is to add keys and keep 2 (wallet, paths, seed: `:46`-`:53`). The plan asks for v3. Contract: v3, and the loader must accept 2
  and 3 (H6.1). Hazard: a v3 save opened by an older build (main, another worktree pointed at the real save) is set aside as corrupt; worktrees use
  their own user folder (`tools/dev/godot.sh`), the owner's real save is the risk. Alternative if the lead prefers: keep version 2 and add the keys.
- **DISAGREE (load)**: there is no mid-run resume: every RunPlay start calls `run_started()` (`run_play.gd:181`), and `run_flags` are never saved
  (`run_progress.gd:17`). So "what persists across load" = the race records and keep: flags only; the per-run keys are saved for a future resume.
- Owner decision: race wins kept across runs (assumed) or per run.

## 7. Bass unlocking

Pack checked on disk: `C:\Users\joesa\rw-audio-work\packs\origin_unknown_valley_of_the_shadows_chase_status_remix\stems\bass.ogg`: Ogg Vorbis,
48000 Hz, stereo, 250.07 s, 11.9 MB, pack gain 1.266; voice key `bass` (kind pitched). The other stems: `drums.ogg`, `other.ogg`, `vocals.ogg`,
`backing.ogg`. The importer's note: bass "moves with drums (envelope correlation > 0.5: shared material or leakage)", so some bass is audible in
the drums stem with the lock on; the listening check must say whether that reads as "the bass is gone".

```
BassLock = {track, stem_key: "bass", stem_file: "stems/bass.ogg", locked_at_start: true,
            unlock: {boundary: "bar", ramp_beats: 2.0}, applies_to: "track_scenes", scope: "per_run_per_theme"}
StemTransport.set_stem_locked(key, locked, ramp_s := RAMP_S)  /  is_stem_locked(key)     # BUILT on this branch
```
- The lock is availability, apart from the mix: `_retarget` = program AND not muted AND **not locked** (`stem_transport.gd`); `apply_program`,
  a miss restore, the dip and the tail cannot lift it (they multiply a gain that is 0). A lock may be set before the stems load and survives a
  reload (`_apply_locks`, also called from `TrackTransport.load_pack_streams`). Unlocking only ramps the gain (over `ramp_s`); the stream never
  stops, so the bass enters at the current position, in sync.
- Sequence: entering `rave.<theme>` with `bass_fixed == false` -> RunTrackAudio locks `bass` on the group it makes for the scene (H7.1) -> the bass
  activity completes -> `flags_to_set: rave.<theme>.bass_fixed` -> host: `t_u = ContractShapes.unlock_time(t_fixed, t_phase0, beat_s, "bar")` ->
  `RunTrackAudio.unlock_stem_at("bass", t_u, ramp_beats * beat_s)` (H7.2, scheduled on its song-time schedule) -> at `t_u` `set_stem_locked(bass, false, ramp)`.
  Re-entering the rave with `bass_fixed` true: no lock. The mix rules (RunTrackMutes) then treat bass as any voice.
- The visible change (knob, deck, crowd) is gameplay's, timed to `t_u`.

Fixture: `bass_lock.json`. Tests: `test_bass_lock_fixture_and_unlock_time`, `test_stem_lock_holds_against_the_mix_and_unlocks_without_restart`.

- **DISAGREE (keys)**: the brief and plan point at `stem_transport.gd`'s keys `kick, snare, bass, other` (`:17`); those are the schema 1 duel's. The run
  plays a track scene through `TrackTransport` (extends StemTransport) with the pack's keys (`drums, bass, other, vocals, backing`), driven by
  `RunTrackAudio` (`run_track_audio.gd`). The lock lives in the base class (so both inherit it); the timing lives in RunTrackAudio. Ordinary
  loop scenes (RunAudio's own bass voice) have no lock; a rave must be a track scene.

## 8. Race environment rendering and camera poses

```
RaceCourse = {id, theme, map (a StoryMap: the road and building-block sectors), length_m, centreline: [[x, z], ...] (straight or gently curving),
              lanes: [{id, x (m from the centreline, increasing left to right)}], eye_m (cockpit eye, 1.15),
              blocks: [{side: L|R, from_m, to_m, height_m}] (authoring input for the converter), 
              camera: {fov_deg, pitch_deg, lane_ease_beats, speed_fov_gain, max_roll_deg <= 2},
              cockpit: {sprite, height_frac <= 0.35}, regions: (as contract 5)}
VehicleThing (sim -> renderer, every frame) = {id, kind: rival|traffic, sprite, lane: float (fractional mid-change), distance_m, brake: bool}
PlayerPose  (sim -> renderer) = {lane: float, distance_m, speed_mps}
ContractShapes.course_point(course, lane, distance_m) -> {at: Vector2 (map x, z), yaw (StoryMap: 0 looks -z)}
camera pose = {cam: Vector3(at.x, floor + eye_m, at.y), yaw, pitch: camera.pitch_deg, fov: fov_deg + speed_fov_gain * speed_frac, roll: 0, pos: at, sector}
```
Boundary: **gameplay** owns `RaceSim` (pure, deterministic: distance, speed, rivals, situations with a deadline in song time, decisions, rhythm input,
collisions, recovery, finish order; minimum speed; frozen by pause because it reads song time only) and the race activity's view (the four
driving regions' feedback, the countdown); it outputs `PlayerPose` and `VehicleThing`s. **Environment** owns the course maps and their tooling,
`course_point` in the engine, dynamic vehicle billboards (with brake-light frames), the camera pose override, the cockpit layer, and
the stage swap that shows the race map. Neither edits the other's side; the two dictionaries above are the whole interface.

Sequence: race entrance hotspot -> ActivityRequest(race, overlay) -> at `t_seat` the host shows the race stage (H8.4) and sets `pose_fn` -> every frame:
`sim.update(t)` -> renderer gets pose + vehicles -> pads judged as usual; judge events and block results reach `activity.on_judge` /
`on_block` (H4.2) -> finish -> `result.race` -> back to the rave stage at `race.entrance` (`return_pose`), theme and puzzle flags untouched.

Fixture: `race_course.json`. Tests: `test_race_course_shape_and_points`.

- **DISAGREE (dynamic things)**: map things are static and culled by their authored sector (`story_world.gd:624`); `thing_pose` moves a thing along
  world x only (`dx`, `:661`). Vehicles need x and z and a sector that follows them: H8.1. The camera comes only from `StoryPlayer.pose_at`
  or the RW_STORY_CAM screenshot override (`story_stage.gd:347`, `:384`): H8.2.

## 9. Choice states (ruling 35b)

> Ruling 35 (b): the red and green rings go: a choice's state (available, selected, committed, and the cost of a wrong one) is shown by the
> artwork itself and how it is animated and changes (a door that lights and opens, a figure that beckons or steps aside, a lamp that changes
> colour, a floor that glows under the thing), never by a routine uniform symbol drawn over the world. This applies to the legacy campaign's
> hotspots and marks as much as to the Doom scenes and the raves. The contracts (rail, choice states) carry it; a dedicated art and engine
> package (A7, Opus) replaces the rings in the existing worlds; the shoot sheets stay as the proof.

```
ChoiceState = idle | available | selected | committed | declined | cost
ChoiceThing = {hotspot, thing (map thing id or actor id), archetype (ChoiceStaging.ARCHETYPES),
               target: {bounds: "art", margin_px <= 24, min_px >= 88},
               states: {<every ChoiceState>: {frames: [sprite, ...], frame_beats?, motion: still|bob|beckon|slump|pulse|sway_left|sway_right|lean|step_aside|shake,
                                             light: {floor_glow: 0..1, tint?: "#hex", lamp?: off|dim|lit|open}, sound?: <sound id>}}}
timing = {respond_within_s: 0.1, swap_beats: 1.0 (ChoiceStaging.SWAP_BEATS), commit: "boundary", cost_beats: 2.0}
ContractShapes.choice_state(id, on_show, selected_id, committed_id, success, window_closed) -> ChoiceState
```
- State rules: not staged -> idle; staged -> available; touched -> selected (at once, within 0.1 s, a frame change or motion start, the sound,
  the floor glow); another touch moves selected; after the lock the rest are declined; at the boundary the chosen one is committed (success) or
  cost (a wrong one: slump, shake, dim lamp, red tint, its sound) and the others declined. Commit never happens on the tap: it is at the
  boundary (the hotspot window and the port as today).
- available, selected and committed must look different (the validator compares frames, motion and light); no frame may be a ring, mark or arrow.
- Touch target without a drawn ring: the thing's projected art bounds grown by at most 24 px, widened to 88 px (`HotspotView.touch_rect_of`,
  `hotspot_view.gd:301`; `HotspotContract.MIN_PX`/`TOUCH_MARGIN_PX` `hotspot_contract.gd:27`, `:29`), checked from every choice viewpoint pose
  (contract 3 hold): visible, inside the stage area, not behind a wall (the portal visibility of `StoryMap.visible_sectors`), no two overlapping,
  none over the pads. The check is a test over projected rects, not a picture.
- Today's vocabulary this replaces: `LOOK_SELECTED ["ring", "claim"]` (`hotspot_contract.gd:21`) and ChoiceStaging roles `current|other|touched|committed|declined`
  with go/stop lamps (`choice_staging.gd:27`-`:35`). A7 maps: available ~ (staged, no role), selected ~ current/touched, committed, declined, and adds cost.

Fixture: `choice_states.json`. Tests: `test_choice_states_shape_and_sequence`.

---

## 10. World-staged activities (ruling 38)

An activity is played in the room it is found in, through the stage, with the run's HUD. Nothing else is drawn.

- **Things**: an activity declares its things as dynamic props, `things() -> Array` of
  `{id, sprite, at: [x, z], sector, size: [w_m, h_m], frame, anchor?}` (H8.1 `StoryWorld.set_dynamic_things`): sprite
  sheets under the scene's `assets/story/<map>/sprites/`, one row per state, the activity sets `frame` (and `at`
  for a thing that moves: a coat handed over, a glass slid across) from its state machine, in song time. The stage
  draws them as billboards at depth, culled by sector, lit by the sector's light like the crowd. People in an
  activity (customers, the attendant, the bartender, the DJ) are crowd actors of the room (`crowd.direct`,
  `crowd.walk_to`, states idle, look, cheer, clap, hands_up, and the per-activity states the package adds:
  `waiting`, `happy`, `impatient`), never drawn by the activity.
- **Static set**: the counter, the shelf, the rail, the deck are map pieces (sprites or decals) authored in the
  scene's map, ids prefixed with the activity's (`cloak_counter`, `bar_shelf_3`); `piece_on`/`piece_off`/`piece_pulse`
  switch their lit states (a shelf glass lighting up is a piece turned on).
- **Camera**: the activity's hotspot route ends at a hold (`hold_bars`) at the spot, facing the things; the activity
  may ask for a pitch (`view_pitch`) and nothing else; no cut, no fade, no zoom. The hold lasts the activity; the
  rail restarts from there on the boundary the activity ends on.
- **HUD and controls**: `RunHud` stays (meter, pips, pause; text silent); the activity's `controls()` (contract 5)
  are drawn in the pad slots by the host's controls layer (`RunActivityInput`), morphing from the pads over the
  last beat before the boundary and back over the first beat after, in the pads' frame style, pictograms only.
  A canvas-layer view (`make_view`) is allowed only for that strip and for feedback attached to a thing
  (`feedback(thing_id, kind, t)`: tick, cross, glow, drawn by the host at the thing's screen point).
- **Sound**: the room's music never stops or ducks beyond the stem lock of contract 7; feedback cues are short
  one-shots on the sfx bus.
- **Tests**: an activity's state machine is tested without the stage (things()/frames as data); the view test
  shoots the scene at three moments with the things in place and checks each thing's screen rectangle is inside
  the stage strip and at least 48 px tall (as `test_doom_views` does for guides).
- **The card table** (blackjack) is converted to this contract by package A8b (merged on `feature/bedsit-raves`): cards, deck and
  chips as dynamic things, the dealer and players as crowd actors, bet/twist/stick/get-up in the pad slots, `replace` mode (ruling 40).

**Built (package A8, wip/engine-props).** The real signatures; the activity side's guide is `docs/engine/WORLD_THINGS.md`.

```
WorldThings (src/contracts/world_things.gd, the recording stub; the run hands a RunWorldPort that extends it, src/run/run_world_port.gd) = ctx["world"] in setup
  set_things(arr) | people(id, state, t0, dur = 0) | feedback(thing, kind, t) | piece_on(piece, t) | piece_off(piece, t) | piece_pulse(piece, t, bars = 2)
MinigameController.world_port (minigame_controller.gd:40, passed at :133); the host sets it to its port on its first step
thing = {id, sprite, at: [x, z], sector, size: [w_m, h_m], frame: int (row-major) | [row, col], y? (m above the floor), anchor?: "bottom" | "center", grid?: [cols, rows]}
StoryWorld.set_dynamic_things(arr)            story_world.gd:912   (StoryDynamicThings, src/story/world/story_dynamic_things.gd: 2D figures of the crowd's overlay)
StoryWorld.thing_screen_point(id) -> Vector2|null   story_world.gd:919  low-res px; a dynamic thing, a map thing or a piece (posed by thing_pose included)
StoryWorld.thing_screen_rect(id)  -> Rect2|null     story_world.gd:926
StoryStage.set_things(arr)                    story_stage.gd:837
StoryStage.people(id, state, t0, dur) -> {state, face, fallback, sheet_state} | {} (unknown id: a warning, a no-op)   story_stage.gd:845
StoryStage.thing_screen_point / thing_screen_rect (stage px)   story_stage.gd:861, :867
StoryCrowd.ACTIVITY_STATES, CROWD_FALLBACKS, resolve_state(id, state), person(id, state, t0, dur)   story_crowd.gd:876, :885, :896, :924
RunMinigameHost.feedback(thing, kind, t)      run_minigame_host.gd:489 (RunActivityFeedback, src/run/run_activity_feedback.gd: tick 1 beat, cross 1 beat, glow 1.5 beats)
RunMinigameHost.people / set_things / stage_action   run_minigame_host.gd:481, :476, :527; things pushed every frame from things() or the port, [] at the end (_step_things :458)
controls' morph: RunActivityInput.mix_at / slot (run_activity_input.gd:98, :132) through StoryPadView.slot_fn (story_pad_view.gd:107, _draw_pad :111);
  the layer stands from seat - 1 beat to hand-back + 1 beat (RunMinigameHost.wants_controls_layer :137), owns taps only from the seat to the hand-back (owns_strip :207)
control = {id, label: "", pictogram? | shape? + color? | icon?: res:// png | draw?: Callable(ci, rect[, alpha]), lit?: bool}   ControlPictograms (src/run/control_pictograms.gd)
```
- People states as baked today (the Warehouse barman b01's sheet): waiting -> idle, happy -> nod@happy, impatient -> look, frown -> idle@sad, beckon -> beckon,
  raise_glass -> cheer, clap -> cheer, hands_up -> cheer (fallbacks; the re-baked rave people should carry the six states as rows).
- `layers` on a thing (the bar's glass) is ignored: the frames carry the colour.
- The pads are never hidden now: they draw the controls in their own slots (the note lane is hidden and the lane input off while the controls own the strip).

## Engine hooks (lead-owned files; file:line, what changes)

Built on this branch (minimal, tested):
- H7.0 `src/audio/stem_transport.gd`: `_locked`, `_ramp`, `set_stem_locked`, `is_stem_locked`, `_apply_locks`; `_retarget` ANDs the lock; `_process` uses an unlock's ramp while rising. `src/track/track_transport.gd` `load_pack_streams`: calls `_apply_locks()`.

- H1.6 `run_journey.gd` / `run_play.gd` lock handler: a world exit's approach walk to the threshold spot in the guard before the boundary. **BUILT** (package
  engine-geography, wip/engine-geography):

**Built (H1.6, geography worlds).** The real signatures; the generator's guide is `docs/engine/GEOGRAPHY_WORLDS.md`. Tests: `tests/test_geography.gd`
(fixture `tests/fixtures/geography/`), `tests/test_run_relaxed_threshold.gd`.
```
RunData.is_geography(world) -> bool             worlds[world].geography
RunData.leaves_world(id) -> bool                a route of scene id leads to another world (a geography world's terminal: _terminal, _reaches_exit)
RunData._validate_geography_routes(id, n)       stay = dir "down" in-world loop; >= 2 routes; a route out -> the ENTRY scene of a geography world; no depth rule
RunRail.validate: rail.routes {up|left|right|stumble|arrive: {to, via?, bars > 0 (the walk clamps to 2..4), hold_bars >= 0, style?, role?, from?}}   (RunRail.ROUTE_KEYS)
RunData._validate_places: every routes[*].to / from / via waypoint is in the scene's map
RunJourney.threshold_of(from, to) -> wp         thresholds[to], else threshold_move(from, to).to, else ""
RunJourney.threshold_move(from, to) -> {}       the next entry to `to` gives dir; rail.routes[dir] ({} for down, same world, no move)
RunJourney.threshold_walk(t, t_boundary, wp, bars = 2, move = {})   one player_move {to, via?, style, bars <= boundary, hold_bars? (if time), threshold: true}
RunJourney.threshold_leave(t, t_boundary, from, to) -> Array        the walk out ([] when the route has no threshold); the lock handler's, beat 61
RunJourney.commit_walk(ev, engine) -> Array     a final-window hotspot_commit with tapped true and a route to another world: threshold_leave from ev.t
                                                ([] for the untouched default, a stay, a same-world route, an activity); RunPlay then latches _door_phase
RunHotspots.is_geography_exit(h) -> bool        a final-window hotspot of a geography scene whose success route is another geography world's scene
RunHotspots.commit_tap() -> outcome | {}        the selected geography exit commits now: success, `committed` at once (the others declined), at_tap: true
RunEngine.tap_commit(t) -> bool                 window open, last lap, not yet committed: hotspot_commit at t, choice set, route_commit now {t: boundary, at: t,
                                                tapped: true, same_world: false}; the block-3 decision and the boundary give no second commit (_tap_routed)
RunPlay.hotspot_select: after a pick, engine.tap_commit(now)   (a pick made before the window opens commits as it opens: _decide, b == 2)
RunJourney.leaving                              after a threshold walk, the rail takes no step (log kind "leaving") until the next phase
RunJourney player_hold {bars, hold: "window"}   the choice viewpoint's hold (beats 49 to 60.5)
StoryPlayer.end_window_holds(t)                 a player_move with threshold: true ends every window hold under way one beat after t (eased); drops one not begun
RunPlay.data_for_test (static, tests only)      the RunData the next run scene plays instead of content/run/run.json
```
- **Ruling 39 (lead)**: in a geography world a route guide's tap IS the decision. The choice viewpoint's hold runs through the window as before, but
  a tap on a guide whose route leads to another geography world commits at the tap's own beat (the hotspot goes `committed` at once, `route_commit`
  fires then, the other guides go `declined`); the walk then gets the authored leg and its hold whenever the tap comes early enough (a tap at beat 50
  has 14 beats). Second and later taps in the same window are ignored. An untouched window keeps the default at the lock (the 3-beat walk). Every
  non-geography hotspot keeps `window: "final"` (the tap an intent, the commit at the lock) exactly as before.
- The tap commit is a success whatever the rhythm (like a quest entrance under ruling 15): the way on is never gated. A late tap's leg is shortened
  to end on the boundary.
- The early `route_commit` keeps `t` = the boundary (the director's lock reads it as the boundary) and adds `at` = the tap.
- A geography world needs one entry scene whose id is the world id; `exit_scene` is optional (the entry may be the exit). In a path the flag is an error.
- Non-geography worlds (the main run, the paths, the bedsit) keep every rule they had; a route from one into a geography world follows the old rules.

Needed, not built:
- H1.7 `run_engine.gd:585` `_decide`: a node flag (`"relaxed": true`) keeps energy at or above 1 (the bedsit never forces a departure).
- H3.1 `run_rail.gd:233` `ambient` and `run_journey.gd:153` (window face): no stroll or glance while the rail stands at a `choice_view` waypoint; the window face only turns before the hold begins.
- H3.2 `run_rail.gd:147` `pick_bars`: only if legs under 2 bars are wanted.
- H4.1 `minigame_activity.gd:150`: `result() -> Dictionary`, `controls() -> Array`, `on_judge(ev, t)`, `on_block(result)` with inert defaults.
- H4.2 `run_play.gd:1003` (`"judge"`) and `:1024` (`block_result`): forward to `minigames.on_judge` / `on_block` for overlay.
- H4.3 `run_play.gd:1927`: build the ActivityRequest (theme, merged config, return_pose).
- H5.1 `run_engine.gd`: `suspend_rhythm(t_from)`, `resume_rhythm(t_at)`; `_chart_block` (`:762`, before the track branch) charts nothing for a block starting in the suspended span; `_decide` (`:573`) `neutral` for it and `block_result.suspended`; `block_credit_of` (`:750`) skips withdrawn cues.
- H5.2 `pad_judge.gd`: `withdraw_from(t) -> int` (pending cues at or after t: DONE, credit 0, flagged, no event, no miss count); `cue_state` (`:107`) answers `"withdrawn"`; the note lane skips them.
- H5.3 `minigame_controller.gd:80` `request` reads `mode`, calls `suspend_rhythm(t_seat)` for replace; `:136` `on_block_result` returns unless rhythm; `:187` `_finish` for replace computes B1, calls `resume_rhythm(B1)`, releases the hold at B1.
- H5.4 `run_minigame_host.gd:59` `_mount`: for replace a controls layer over the pad strip (rects from `pad_view.button_rects()`: 4 controls = the pads, 2 = left and right halves), `lane_input.clear()` and `enabled=false` at t_seat, restored at `B1 - lead_in`; for overlay a regions layer.
- H5.5 `run_play.gd:1885` `_input` / `:1842` `hotspot_tap`: one dispatcher implementing `tap_owner`; the pad-rect early return (`:1848`) hands a strip tap to the controls in replace mode; an `input_log`.
- H5.6 `run_play.gd:2018` `_on_button_pressed`: refuse while replace owns the strip (belt and braces).
- H6.1 `run_progress.gd:9` `VERSION := 3`; `:37` accept 2 and 3; `:64` `_fresh` via `RaveSave.migrate`; `:138` `run_started` calls `RaveSave.new_run`.
- H7.1 `run_track_audio.gd:345` `_make_group`: apply the scene's stem locks (`stem_locks: {track id: [keys]}` set by the host) before the group starts.
- H7.2 `run_track_audio.gd:317`/`:238`: `unlock_stem_at(key, t, ramp_s)` as a scheduled item run on song time.
- H8.1 `story_world.gd:624` (and `:354` `thing_pose`): dynamic billboards `set_dynamic_things([{id, sprite, at, sector, size, frame}])`, culled by their current sector. Package A8 (contract 10): plus `thing_screen_point(id)` for feedback, and the controls' morph in `RunActivityInput`. **BUILT** (A8, wip/engine-props): see contract 10, "Built".
- H8.2 `story_stage.gd:347`: `pose_fn: Callable` overriding `player.pose_at(t)` (race camera); fov from the pose.
- H8.3 the cockpit as a low-res overlay layer (`StoryLowRes.add_overlay`) under the activity view.
- H8.4 `run_play.gd:420` `_show_world`: an activity may ask for another map's stage at `t_seat` and back at exit (race), prebuilt in a guard.
- H9.1 `hotspot_view.gd` and `choice_staging.gd`: draw states from ChoiceThing data, no ring (package A7).
- H10 weather (rain scenes: Booth, Dock, Balcony, the Lounge's street; rulings 36, 38). **BUILT** (package A9, wip/engine-rain); guide `docs/engine/WEATHER.md`,
  tests `tests/test_weather.gd`, sheet `docs/shots/engine/weather/rain_sheet.jpg`:
  ```
  map  "weather": {"rain": 0..1, "wind": -60..60 (degrees of slant, + leans toward +x), "drips": [{"at": [x, z], "h": metres above the floor}]}   (StoryMap.weather; errors on bad values)
  sector "rain": true | false   (true: rain under a roof; false: an open sector kept dry; absent: open = ceil_tex "sky" or "*_sky")
  sector "wet": 0..1            (the floor gloss; absent: the map's rain on open sectors, 0 elsewhere)
  StoryMap.rain_open(sid) -> bool, wet_of(sid) -> float, has_weather() -> bool, sky_ceiling(sector) (static)
  StoryStage.weather: StoryWeather   built beside fx3d only when map.has_weather() (a dry map gets no node), updated in _update_world on song time
  StoryWeather.update(t, camera, sector_light, vis)   rain_mm / drip_mm / gloss_mm (one MultiMesh each), rain_at(p), streak_pos(i, t, lo), draw_calls()
  ```
  Cost at the Dock (640 x 231 low-res, rain 1): +3 draw calls, +886 primitives, weather.update ~8 us CPU on the dev PC; phone GPU time not measured.

## What is not settled (for the lead or the owner)

- The bass knob's mode (rhythm proposed) and whether leaving the bedsit uses `when: soonest` (proposed) or the lap end.
- Race records across runs (assumed kept) and whether race energy loss may end the run (brief: penalties active; assumed yes).
- Save version 3 vs keeping 2 (section 6).
- The opening as a path (`content/paths/bedsit`) rather than nodes in the main `run.json` (proposed: a path; the legacy run stays the main run).
- The race as an activity with a stage swap (proposed) rather than a scene of its own (a scene would wait for a lap end to start).
