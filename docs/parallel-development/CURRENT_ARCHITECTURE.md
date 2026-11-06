# RhythmWarfare: current architecture (the verified state before the two streams work)

This document describes what exists today. It does not describe the target. The target is in `DECISIONS.md` (the lead's decisions, outside the
repository) and `INTEGRATION_CONTRACT.md`. Where today and target differ, this file says "today". It was written on the morning of 6 November 2026 for
two machines and re-worded the same day for one PC (`ONE_PC_PLAN.md`): "Windows" is the music stream and "Ubuntu" the narrative stream.

## How to read this document

Baseline: the handover branch `feature/laptop-handover-2026-11-06` at `90a42877` (`main` at `86950290` plus 14 commits: the engine half of track scenes,
the importer fixes, four planning documents), verified on this PC (`ONE_PC_PLAN.md` section 3). On 6 November 2026 the facts below were re-checked in
the worktree `MusicGame-docs` (branch `wip/docs`), which holds that code plus later merges of the planning documents, the importer work (stage I1), the
mock director and its tests. Every line count in section 2 and every function line number in `run_play.gd`, `run_engine.gd` and `run_audio.gd` matched;
line numbers drift as soon as anyone edits a file.

How facts were checked:

- Every file path, class, function and event name below was checked by `grep` in that tree.
- Facts marked **[R]** come from the five investigation reports (A to E, outside the repository) and were not re-run here. Most are numbers computed
  over the JSON data, or statements about behaviour that needs a running game.
- Nobody ran Godot for this document. No sound was heard and no device was used.

Vocabulary (from `DECISIONS.md`): a *scene* is one node of `run.json`. A *phase* is 64 beats: four blocks of 16 beats. A *lap* is one pass through a
scene. A *track scene* is a scene whose music is a whole recorded track and whose length is several laps. A *quest* is one of Bassment, Jesus
(`gospel`), Catch-22 (`squadron`), Lord of the Rings (`ember`). A *location* is one of the five mainline places.

---------------------------------------------------------------------------------------------------------

## 1. What the game is today

RhythmWarfare is a Godot 4.5.1 rhythm game for Windows and Android (arm64). The player taps four pads in time with falling cues. Between the pads and
the top of the screen is a 2.5D world drawn in low resolution.

### 1.1 The run (the main mode, reachable from the main menu "Play")

- One continuous run. The scene is `src/scenes/main_menu.tscn`; Play sets `Session.run_start_node = ""` and loads `run_play.tscn` (`RunPlay`, one
  Control node that owns everything).
- Data: `content/run/run.json` (36 scenes, start node `warehouse`, 174 BPM, 7 worlds).
- Time: `timing.phase_beats` 64, `block_beats` 16, `cue_span_beats` 12 (cues occupy the first 12 beats of a block), `decision_beat` 12.5 (a block is
  judged 12.5 beats in).
- A scene is one 64-beat phase: four blocks. Each block judged "passed" steps the mix stage and takes the next step along the camera rail. Energy rises
  and falls. Energy 0 ends the run. There is no ending.
- **Doors.** In the last block (from the block-2 decision, beat 44.5, to the commit, beat 60.5) the exits of the scene are touchable. The player taps a
  door, a person or an object (a *hotspot*). Touching nothing takes the scene's default exit. The destination is fixed at beat 60.5 and the scene
  changes on the downbeat at beat 64.
- **Worlds and scenes (main run).**

| World id | Meaning | Scenes |
|---|---|---|
| `warehouse` | Warehouse Rave, the start and hub | 6 |
| `mothership` | Alien Spaceship | 5 |
| `underworld` | Hell | 5 |
| `hospital` | Hospital Ward | 6 |
| `ward` | Mental Hospital (the data calls it "The Ward") | 6 |
| `hospital_late` | late looping variant of the Hospital | 4 |
| `ward_late` | late looping variant of the Mental Hospital | 4 |

  36 scenes in all. A run goes: Warehouse, then Alien Spaceship or Hell (by the Door), then Hospital Ward or Mental Hospital, then the two late worlds,
  which loop into each other for ever. A run visits 3 of the 5 locations. It cannot return to the Warehouse and never ends **[R: B]**.
- **Track scenes (logic only).** `content/run/track_scenes.json` assigns a recorded track to all 36 main scenes and to all 46 scenes of the three paths
  (82 scenes). A scene becomes a multi-lap track scene only when its pack is on the machine. Packs are not in the repository. Without packs every scene
  plays as one ordinary pass. The audio for track scenes does not exist yet (section 5.6).

### 1.2 The side paths (quests entered from the Warehouse)

Each path has its own `run.json` under `content/paths/<id>/`, its own tempo and its own scenes. A path is entered through a portal hotspot in the
Warehouse. The run hands over to a new engine at a tempo change.

| Path id | Title | BPM | Scenes | Entry in the Warehouse | Reachable in play |
|---|---|---|---|---|---|
| `gospel` | The Life of Jesus | 124 | 17 | `warehouse.balcony.star` | yes |
| `squadron` | The Mission Count (Catch-22 shape) | 140 | 14 | `warehouse.booth.radio` | yes |
| `ember` | The Ember Road (LOTR shape) | 145 | 15 | `warehouse.bar.ember` | yes |
| `stub` | developer test | 124 | 2 | none | no (needs `RW_PATH_REMAP` or `RW_RUN_PATH`) |

Every path scene plays two laps. The doors work in lap 2 only (the openers and Golgotha differ) **[R: B, C]**. A path returns to the Warehouse floor
(`path.returns_to` must be `"warehouse"`, `run_data.gd:181`).

### 1.3 The Bassment (the dungeon)

A separate system: text-and-choice passages with rhythm tests, in `src/trial/` and `content/trial/` (`passages.json` has 64 passages, `hotspots.json` is
generated from it). It is a *hosted* trial: it runs inside `RunPlay` on the same clock and audio, with its own engine (`trial.engine`). The player
enters it by touching the wizard in the Warehouse floor or the chill-out (scenes with `trial_gate` in `run.json`). The wizard is in the "early" window
(blocks 0 and 1 only). The player leaves by death (7 passages), by victory (passage 63) or by the system back key. There is no on-screen back button
**[R: B]**. Its music note says the fight pack (`fight_audio`, `dd_part2`) is read and checked "but not yet switched to by the scene"; one pack plays
throughout (`content/trial/passages.json`, `music.note`).

### 1.4 Other modes

| Mode | Reachable in play? | Note |
|---|---|---|
| Story chapters (older chapter campaign) | yes, main menu | five chapters, own save `story_campaign.json` |
| Start from a reached level | yes, main menu | `src/run/run_levels.gd`; starts a new run at a reached world |
| Debug / Playtest | yes, main menu button | `src/debug/`; lists all 82 playable scenes; throwaway save |
| Wizard Duel (wifi) | yes, main menu | two players; `DuelNetwork` autoload; no story |
| Ten military missions | no, not from the menu | Developer screen only (editor build or `RW_DEV=1`) |
| Track mode (whole songs) | test scene only | `src/track/`, scene `track_play.tscn`; the owner played one track |
| Blackjack | yes, inside the run | the card table in `ward` (Mental Hospital Day Room) is a minigame, not a quest |

**[R: B]** for reachability. The Blackjack table sits in `run.json` node `ward`, which has `max_hotspots: 5` (`content/run/run.json:3068`, written by
`tools/run/make_scenes.py:290`).

---------------------------------------------------------------------------------------------------------

## 2. Source map

Line counts are as of 6 November 2026 (`wc -l`). "Stream" means the stream that edits the file under `DECISIONS.md` D2 and `FILE_OWNERSHIP.md`: **M**
the music stream, **N** the narrative stream, **M then N** the music stream until milestone M1 is merged, then the narrative stream, **F** frozen (only
the lead changes it), **-** not touched.

### 2.1 The run

| Path | Lines | Role | Stream |
|---|---|---|---|
| `src/run/run_play.gd` (`RunPlay`) | 1781 | the whole run scene: engine, audio, clock, pads, HUD, stages, hotspot UI, journey, minigames, Bassment host, path hand-off, pause menu, bot | M then N (shared hot file) |
| `src/run/run_engine.gd` (`RunEngine`) | 906 | pure logic: phases, blocks, laps, judging, energy, charting, route lock, commit, track-scene logic | M then N |
| `src/run/run_data.gd` (`RunData`) | 828 | static data load and validation: run.json, music, packs, hotspots, track scenes | M then N |
| `src/run/run_audio.gd` (`RunAudio`) | 570 | all run audio (extends `StemTransport`) | M |
| `src/audio/stem_transport.gd` | 263 | base class: players, mute, gain program, `playback_position()` | M |
| `src/core/song_clock.gd` (`SongClock`) | 104 | audio-derived song time and judge time | M |
| `src/run/run_track_scenes.gd` (`RunTrackScenes`) | 281 | which scenes are track scenes, pack lookup, seeded pick | M |
| `src/run/run_track_plan.gd` (`RunTrackPlan`) | 120 | the plan of one track scene: entry bar, laps, chart | M |
| `src/run/run_hotspots.gd` (`RunHotspots`) | 287 | pure logic: what is touchable, selected, committed | N (M for stage M1 only) |
| `src/run/hotspot_contract.gd` (`HotspotContract`) | 588 | hotspot schema and validator; route prefixes `trial:`, `path:`, `run:` | N |
| `src/run/hotspot_view.gd` (`HotspotView`) | 1098 | drawing, layout and hit test of hotspots | N |
| `src/run/choice_staging.gd`, `choice_props.gd` | 297, 91 | door, person and object staging for choices | N |
| `src/run/run_journey.gd`, `run_rail.gd` | 156, 294 | camera rail and door walk | N (`run_journey.gd`: M for stage M1 only) |
| `src/run/run_passage.gd` | 38 | iris frame at a world change; `DOOR_BEATS` 3, `CLOSE_BEATS` 2 | N |
| `src/run/run_progress.gd` (`RunProgress`) | 192 | the run save `user://story_run.json` | N |
| `src/run/run_minigame_host.gd` | 217 | `RunPlay`'s side of minigames (sets `engine.hold`) | N |
| `src/run/run_levels.gd` | 70 | "Start from a reached level" | N |
| `content/run/run.json` | 6,653 lines | timing, judgement, energy, stages, mix, 36 nodes, cinematics | M then N |
| `content/run/hotspots/<world>.json` | 7 files | hotspots of the main run | N |
| `content/run/track_scenes.json` | 1,108 lines [R] | scene to track assignment (first choice and 2 alternates) | M |
| `content/paths/<id>/` | 4 dirs | each path's `run.json`, hotspots, music | N |

### 2.2 The Bassment, tracks, narrative-adjacent

| Path | Lines | Role | Stream |
|---|---|---|---|
| `src/trial/` (`trial_scene.gd` 1062, `trial_engine.gd` 332, `trial_data.gd` 332, `trial_flow.gd` 154, `trial_hotspots.gd` 133) | 2,000+ | the Bassment | N |
| `content/trial/passages.json`, `hotspots.json` | - | 64 passages; generated hotspots | N |
| `src/track/` (`track_pack.gd` 484, `track_play.gd` 384, `track_game.gd` 317, `track_transport.gd` 54, ...) | 1,428 | standalone track mode and the pack loader | M |
| `tools/audio_import/` | - | track importer (Python); runs on Windows and the GPU since stage I1 (it was written on Linux) | M |
| `content/music/tracks/` | 45 files | `catalogue.json` (61 recordings; `counts.imported` is 44) and 44 per-track metadata files | M |
| `docs/RUN_TRACK_SCENES.md`, `docs/TRACK_SCENES_HANDOVER.md`, `docs/TRACK_ASSIGNMENT.md`, `docs/TRACK_PACK_FORMAT.md` | - | the track scenes contract and briefs | M |

### 2.3 Global and tooling

| Path | Role | Stream |
|---|---|---|
| `src/core/session.gd` (221 lines, autoload `Session`) | settings, saves, hand-off fields | N (`run_progress`, save format), otherwise F |
| `src/duel/duel_network.gd` (autoload `DuelNetwork`) | wifi duel only | - |
| `project.godot`, `export_presets.cfg` | engine and export settings | F |
| `docs/HANDOVER.md`, `README.md` | shared logs | F |
| `tests/run_tests.gd`, `tests/test_*.gd` (87 run at `90a42877`, 88 on this branch with `test_port_mock.gd`; `test_case.gd`, the base class, is not counted), `tests/fixtures/` | the Godot suite | both |
| `tools/test.sh` | wrapper: import, suite, content tests | F (the lead changes it) |
| `tools/dev/godot.sh` | the Godot queue wrapper: one Godot at a time, because every worktree shares one `user://` (stage 0.4) | F (the lead) |
| `tools/run/check_hotspots.py` (500 lines) | hotspot data validator, no Godot | N |
| `tools/run/choice_audit.gd` (118 lines) | per-option legibility probe | N |
| `tools/run/make_hotspots.py`, `make_scenes.py`, `staging_data.py`, `apply_staging.py` | generators of hotspot and scene data | N |

### 2.4 Files that exist now because of the work of 6 November, and those that do not

Exist (checked by `ls` in the worktree): `src/transition/transition_port.gd` and its `.uid` (the byte copy of the contract, stage 0.3),
`tests/mocks/mock_transition_director.gd`, `tests/port_conformance.gd`, `tests/test_port_mock.gd` (stage N1.4), `tools/dev/godot.sh` (stage 0.4).

Named in `DECISIONS.md` as targets and still absent: `src/transition/transition_director.gd`, `src/narrative/`, `src/music/`, `content/narrative/`,
`content/music/transitions/`, `tools/narrative/`, `tools/run/coverage_audit.*`. There is no `.github/`, and no `docs/parallel-development/handover/`
(this PC uses reports, not handover files).

---------------------------------------------------------------------------------------------------------

## 3. The scene-change sequence today

The scene change is driven by song time, not by a call. `RunPlay._process` (`run_play.gd:646`) ticks the clock, calls `_advance` (`:708`), which calls
`_handle(engine.update(t))` (`:745`). `_handle` (`:877`) fans each event out. Beats below are beats of the 64-beat phase. Block 0 is beats 0 to 16,
block 3 is beats 48 to 64.

### 3.1 Ordinary scene (main run, one lap)

| Beat | What happens | Owner |
|---|---|---|
| 0 | `phase_start` emitted at the downbeat. `_on_phase_start` (`:934`) calls `Session.run_progress.enter(world)` (a disk write), swaps the stage, prewarms routes. `RunAudio._begin_phase` fades the old group over 0.6 s and starts the new drums | `RunEngine._enter` (`:198`), `RunPlay`, `RunAudio` |
| 12.5, 28.5 | block 0 and 1 judged (`_decide`, `:543`); energy, mix stage and camera step | `RunEngine` |
| any time in the window | touch: `_input` (`:1332`) to `hotspot_tap` (`:1306`) to `hotspot_select` (`:1228`) to `RunHotspots.select` (`run_hotspots.gd:118`). Selection is free to change | `RunPlay`, `RunHotspots` |
| 44.5 | block 2 judged. `_decide` sets `window_open = true` and emits `route_window`, stamped t = beat 48 (`run_engine.gd:586-592`). `RunPlay._open_routes` (`:1143`) runs and `RunAudio` schedules the riser or fall | `RunEngine` |
| 48 | the stamped time of the `route_window` event; the riser/fall one-shot starts here | `RunAudio` |
| 49 (about) | the camera holds the window's hotspots (`_window_face`, `StoryPlayer.best_facing`) [R: C] | `RunPlay` |
| 60.5 | block 3 judged. `_hotspot_decision` (`run_engine.gd:651`) resolves the touched hotspot or the default exit. Flags and energy change. `_chart_next_phase` (`:708`) charts the next scene's first block into `level.notes` and sets `route_locked`. `hotspot_commit` emitted. `RunPlay._on_hotspot_commit` (`:1353`) saves persistent flags | `RunEngine`, `RunHotspots`, `RunPlay` |
| 61 | door walk starts (`_update_passage`, `:765`, at `64 - DOOR_BEATS`) | `RunPlay`, `RunJourney` |
| 62 | for a change of world, the passage iris closes (`64 - CLOSE_BEATS`) | `RunPassage` |
| 64 | `RunEngine.update` calls `_commit` (`:487`). Not the last lap: `_start_lap`. Otherwise `route_commit`, then `_enter(to)` for the next scene | `RunEngine` |

The destination is fixed in two steps, 3.5 beats apart (about 1.2 s at 174 BPM): meaning at 60.5, structure at 64. Nothing undoes the first step
(section 8.3 and 8.4).

Event stamping: `mix` and `route_window` are emitted at the previous block's decision beat 12.5 but carry the time of the next boundary, so schedule by
`ev["t"]`, as `RunAudio` does. `phase_start` and `track_start` are emitted at the boundary itself. The audio side has no look-ahead for the scene start.
It starts late and seeks into the stream to compensate **[R: D]**.

Window beat: reports A and the docs say the window opens at "beat 48" (or 49). In code `window_open` becomes true at the block-2 decision (beat 44.5)
and the `route_window` event is stamped 48 (`run_engine.gd:586-592`, re-read on 6 November). A touch is accepted from 44.5 on (**[R: C]**; whether the
picture gates it at 48 was not checked).

### 3.2 Several laps in one scene (path scenes and track scenes)

- `_commit` with `lap < laps` and no leave request calls `_start_lap` (`:517`) and emits `lap_start`. No scene change, no audio event
  (`RunAudio.on_event` has no `lap_start` branch).
- The window opens only in the last lap of a path scene (`lap == laps`). In a track scene it opens from lap `doors_from_lap` (default 2)
  (`_doors_open`).
- Track scene, open lap: touching an exit makes that lap the last (`track_last_lap`, `laps = lap`). Touching nothing: nothing commits, the window closes
  at the choice beat, `RunHotspots.begin_lap` (`:50`) resets selection, and the scene goes on.

### 3.3 Path hand-off (portal into a path, or an ending back to the Warehouse)

1. The route is `path:<id>` or `run:warehouse`. At beat 64, `_commit` emits `route_commit`, then `path_handoff` (`run_engine.gd:497`), sets
   `engine.away`, and calls `_track_end(t0, "handoff", to)`.
2. `_handle` stores the event and calls `_path_swap` after the batch (`run_play.gd:1614`).
3. `_path_swap` loads the other `RunData` (`_path_cache` or `RunData.load_path`). For the way back it uses `main_data` and starts at `"warehouse"`. If
   the load fails it stays in the current run on the default exit (the portal's flags and energy have already been applied).
4. If the data differs, `audio.schedule_clock_swap(new_data, t_swap)` (`run_audio.gd:228`) queues one `clock` item. At the downbeat `_swap_clock`
   (`:365`) replaces the clock stream with a new silent 64-beat loop at the new tempo and sets `song_base = t - mix_period`. Song time stays continuous.
5. `RunPlay` makes a **new** `RunEngine`, a new `RunHotspots` and a new `RunJourney`, then calls `engine.arrive(start, t_swap, energy, phase_n,
   lap_extra)` (`run_engine.gd:190`). Only energy, phase count, lap count and grid origin carry over. The main engine is thrown away. It re-points the
   pad view, note lane, HUD, stage tempo and hotspot view `beat_s`.
6. The old music fades through the ordinary 0.6 s fade at the next `phase_start`. The new scene opens with drums alone at its own tempo. There is no
   crossfade and no tempo ramp.

### 3.4 The minigame hold

`RunPlay._on_hotspot_commit` asks `minigames.request(activity, ...)` (`minigame_controller.gd`), which sets `engine.hold = true`. While held,
`selected_route()` returns the current node, `_decide` skips the hotspot decision, and `_chart_next_phase` charts the same scene. At beat 64 the same
scene starts again as a new phase (ordinary scene) or gains one lap (`track_extend`, track scene). `_finish` clears `hold`. `RunMinigameHost` then keeps
the door the player was walking to as a pending selection. `RunPlay` runs `minigames.update(t)` right after `engine.update(t)`.

### 3.5 The Bassment hand-off

1. The wizard hotspot's route is `trial:<n>`. On commit, `RunPlay` calls `trial_launcher` (a Callable, set at `run_play.gd:526`), which calls
   `arm_trial` (`:1709`). `arm_trial` returns false if fewer than two guards are left in the phase.
2. `trial_state = "armed"`. `engine.update` is then capped just before `trial_entry_t`. The walk to the hatch is scheduled on a cue-free guard. The
   dungeon pack is preloaded.
3. `trial_begin_now` (`:1746`) gives the pads to `TrialScene`, runs `engine.phase_n += 1` by hand, and sets `trial_state = "in"`.
4. Leaving (death, victory, back key) calls `trial_leave` (`:1760`). It picks `"warehouse"` and calls `engine.resume("warehouse", t_swap)`. Energy and
   phase count stay. The player is back on the Warehouse floor, not in the scene they came from.
5. The engine emits no `track_end` for this exit **[R: A, D]**. If a track scene were playing, the audio would have to stop its group itself.

### 3.6 Everything else that ends a scene

- Depletion at the last block: `_hotspot_decision` runs only when `energy > 0` (`run_engine.gd` about `:573`), so a run that dies on the last block
  applies no outcome. `depleted` then `run_over`.
- Pause menu "Leave this path": `request_path_leave` (`:1602`), `force_leave` (`run_engine.gd:368`) sets `choice = run:warehouse`. Allowed from beat 61
  (after the route lock). The old engine is frozen by `away`.

---------------------------------------------------------------------------------------------------------

## 4. Engine events

`RunEngine._emit` (`run_engine.gd:285`) appends events to the list returned by `update(t)`. Fourteen kinds exist for every scene. Seven more are emitted
only for track scenes. The header comment at `run_engine.gd:25-45` documents the track ones.

### 4.1 Events and consumers

"RunPlay" means `RunPlay._handle` (`run_play.gd:877`). "Audio" means `RunAudio.on_event` (`run_audio.gd:196`). "Journey" means `RunJourney.on_event`
(`run_journey.gd:30`). `_handle` also appends every event except `judge` and `cues` to `event_log`, which the tests read.

| Event | Emitted by (function) | Consumed by |
|---|---|---|
| `judge` | `RunEngine.update` | RunPlay (`_on_judge_event`) |
| `cues` | `_chart_block`, `_chart_track_block` | RunPlay (refreshes pad view and note lane) |
| `phase_start` | `_enter` | Journey, Audio (phase item and section items), RunPlay (`_on_phase_start`) |
| `lap_start` | `_start_lap` | Journey, RunPlay (`_on_lap_start`). Audio ignores it |
| `mix` | `_enter` (stage 0), `_decide` (later stages) | Audio (gains), RunPlay (`_on_mix`) |
| `reveal` | `_decide` (first time stage 1 is reached) | Audio (starts bass and synth), RunPlay (caption) |
| `block_result` | `_decide` | Journey, RunPlay, `minigames.on_block_result` |
| `route_window` | `_decide` (block 2) | Audio (riser or fall one-shot), RunPlay (`_open_routes`) |
| `hotspot_commit` | `_hotspot_decision` | Audio (only the music "dip"), RunPlay (`_on_hotspot_commit`) |
| `route_commit` | `_commit` | RunPlay (`_close_routes`) |
| `path_handoff` | `_commit` | RunPlay (stored, then `_path_swap`) |
| `cast` | queue in `update` | RunPlay (`_on_cast`) |
| `depleted` | `_decide` | Audio (fade), RunPlay (caption, `_end_fade`) |
| `run_over` | `update` | RunPlay, `minigames.on_run_over` |

### 4.2 Track events: emitted, consumed by nobody in `src/`

| Event | Emitted by | Fields (main ones) | Consumers in `src/` |
|---|---|---|---|
| `tempo` | `_enter` (before `phase_start`) | `bpm`, `beat_s`, `from_bpm` | none |
| `track_start` | `_enter` (after `phase_start`) | `track`, `dir`, `bpm`, `entry_bar`, `track_t`, `laps`, `duration_s` | none |
| `track_lap` | `_start_lap` | `lap`, `laps`, `track_t`, `doors_open` | none |
| `track_last_lap` | `_track_last_block` (choice beat) | `lap`, `ends_t`, `route` | none |
| `track_extend` | `_track_last_block` (hold) | `laps` | none |
| `track_wrap` | next-lap charting | `track_t`, `from_track_t`, `decided_t` | none |
| `track_end` | `_track_end` | `reason` route, handoff or depleted; `to`; `track_t` | none |

Checked by `grep` over `src/` and `tools/`: no file outside `run_engine.gd` handles these seven kinds. The tests read them
(`tests/test_run_tracks_engine.gd`, `tests/fixtures/track_scenes/track_scene_fixtures.gd`). Extra fields on ordinary events: `phase_start.track`,
`block_result.neutral` and `.track`, `route_window.last` and `.track`, `cues.track` and `.lap`.

### 4.3 What is missing from the event stream

- No event for "the player selected a hotspot". Selection is a call (`hotspot_select`) and a log entry (`hotspot_log`). Nothing is emitted.
- No "transition complete" or "transition requested" signal. Tests read `event_log`, `phase_log` and `path_log`.
- No event for a Bassment entry or exit. `trial_log` records them in `RunPlay`.

---------------------------------------------------------------------------------------------------------

## 5. Music

### 5.1 The pipelines that exist

| # | Pipeline | Output | In Git? | Status |
|---|---|---|---|---|
| 1 | Legacy duel packs (schema 1) | `songs/level_01/`, `songs/test_16/` | partly | implemented, legacy |
| 2 | Loop library and missions (schema 4) | 8-bar Ogg loops in `songs/library/`, built by `tools/content/build.py` | loops tracked | implemented |
| 3 | Beat Shaper WAV and MIDI to run packs | `songs/packs/<id>/pack.json` plus shared 3-stem WAV loops (75 packs, 302 MB [R]) | tracked | implemented (`docs/MUSIC_IMPORT.md`) |
| 4 | Arrangements | `content/music/arrangements/*.json`, `content/story/music.json` maps each scene to an arrangement | tracked | implemented |
| 5 | Path packs | same as 3, with `"path"` in `pack.json` | tracked | implemented |
| 6 | **Track packs v2** | `<id>/track.json` (`rhythm_warfare.track.v2`) plus `stems/*.ogg` | **never** | importer implemented; packs outside the repo |

Pipelines 2 to 5 are loop systems on a 174-BPM grid. Every loop is a whole number of frames and tiles a 64-beat phase. Pipeline 6 is not a grid: free
float tempo, full-length unlooped stems. Pipeline 1 is a different engine (schema 1, duel).

Standalone track mode (`src/track/`, `track_play.tscn`) works and the owner played one track ("Go Back").

### 5.2 The run clock

- Classes: `SongClock` (`src/core/song_clock.gd`), `StemTransport` (`src/audio/stem_transport.gd`), `RunAudio extends StemTransport`.
- Derivation: `audio_time = transport.playback_position() + AudioServer.get_time_since_last_mix() - output_latency`. `judge_time()` (`song_clock.gd:75`)
  subtracts `Session.calibration_ms`. Calibration moves judging and note drawing, never what is heard.
- `playback_position()` (`stem_transport.gd:168`) is the player's position unwrapped across loop restarts. Song time is monotonic and frozen while
  paused.
- **The run's clock is a silent 8-bit mono looping `AudioStreamWAV` of exactly 64 beats** (`silent_loop`, `run_audio.gd:125`) on `RunAudio.player`. Its
  mix rate is chosen so one beat is a whole number of frames (`CLOCK_RATES := {174: 8700, 124: 8680, 140: 8400, 145: 8700}` at `:104`; other integer BPM
  get the smallest rate at or above 8000 that works). `clock_rate(bpm: int)`, `frames_per_beat(bpm: int)` and `silent_loop(beats, bpm: int)` all take an
  **int**. Track tempos are floats (for example 174.0032).
- Every scene's music is a separate `AudioStreamPlayer`, started "on the clock" and not the clock itself.
- Output latency is read once, in `begin_countdown` (`song_clock.gd:30`). `RunAudio.now_t()` (`run_audio.gd:189`) reads it live on each call. So clock
  and scheduler can disagree if the reported latency changes mid-run **[R: A]**.
- The pre-song countdown is wall-clock (`COUNTDOWN_S` 2.0). Resume after pause is 3.0 s.
- Judge windows (`run.json` `judgement`): perfect 45 ms, great 90 ms, accept 140 ms **[R]**.
- Measured accuracy exists only with the headless dummy audio driver **[R: A]**: mix chunk 88.5 ms, phase boundary error about -6 ms, spread 6 to 13 ms.
  The docs say nobody has played it on a phone or heard it (`docs/HANDOVER.md`, `docs/CONTINUOUS_RUN.md`). No Windows or Android audio measurement
  exists.

### 5.3 How a scene's music plays and changes today

Loop scenes (all scenes without a pack on the machine):

- Per phase, `_begin_phase` (`run_audio.gd:397`) starts a "group" of looping voices. Drums start at the downbeat. Bass and synth start at the `reveal`
  event and keep running. Each voice is one `AudioStreamPlayer` with its own `play(from)` (lateness compensation). `RunAudio` does **not** use
  `AudioStreamSynchronized`.
- Stage gains (`run.json` `stages`) ramp over `mix.ramp_s` 0.35 s, set per rendered frame on `volume_db`.
- A scene may have two sections (8-bar halves). `_switch_section` (`:481`) is a hard cut on the grid.
- Buses are created at runtime (`project.godot` has no bus layout): `Music`, `RunMix`, and two alternating pairs `RunDrumsA/B`, `RunBassA/B`, plus bass
  tone buses. Treatments (filters, drive, reverb) are effects on the pair's buses.
- **There is no limiter on the run's bus.** `AudioEffectHardLimiter` appears only in `src/track/track_play.gd` (standalone mode).
  `docs/RUN_TRACK_SCENES.md` says "through the music bus with the run's limiter". That limiter does not exist in the run.

Every musical transition that exists:

| Transition | What happens | Evidence |
|---|---|---|
| Scene to scene, same tempo | old group fades to 0 over `mix.phase_fade_s` 0.6 s starting at the new downbeat; new drums start at gain 0 and ramp over 0.35 s; new bass and synth wait for `reveal` | `_begin_phase`, `run.json` `mix` |
| Bass carry | if both scenes share a music `family`, the old bass stays at gain 0.5 under the new drums for 16 beats | `run.json` `carry_bass` |
| Riser or fall | one-shot `assets/run/riser.wav` or `fall.wav` (5.517 s, 16 beats at 174) at `route_window` stamped time; same file at every tempo | `RunAudio.on_event`, `route_window` |
| Section switch in a scene | hard cut on the grid | `_switch_section` |
| Lap boundary in a path scene | nothing; loops tile the lap | `RunAudio` ignores `lap_start` |
| Path hand-off | hard cut on the downbeat plus 0.6 s old fade; clock stream swapped to the new integer tempo | section 3.3 |
| Hotspot "dip" | non-drum voices drop to `dip_gain` 0.55 for `dip_beats` | `hotspot_commit` branch |
| Depletion | `fade_out` of the master over `fade_s` | `depleted` branch |
| Pause | `stream_paused` on everything | `RunAudio` |
| Bassment entry | its pack is preloaded; same clock and audio | section 3.5 |

There is **no crossfade between songs, no tempo ramp, no time-stretch and no pitch shift**. `grep` over `src/` finds no `pitch_scale` assignment, no
`AudioEffectPitchShift`, no `AudioStreamInteractive` and no `AudioStreamPlaylist`.

Preloading: `preload_pack` (`run_audio.gd:234`) uses `ResourceLoader.load_threaded_request`. It is called at `phase_start` for the scene's sections, at
`route_window` for every option (`_open_routes`, `:1143`), for path portals before the countdown (`_preload_portals`, `:201`) and for the Bassment
(`arm_trial`). All of these load **loop** packs by id. None loads a track pack.

### 5.4 Tempo handling

- BPM sources: `run.json` `timing.bpm` (174; paths 124, 140, 145) feeds `RunEngine.beat_s`, `RunAudio.beat_s` (`retarget`, `:94`), `Level.bpm`,
  `StoryStage.set_tempo`, `HotspotView.beat_s`, `CardTable.beat_s`.
- A path hand-off swaps everything (new engine, new clock stream).
- A track scene re-grids inside **one** engine. `_enter` calls `_regrid(t0, bpm)` (`run_engine.gd:249`) when the scene is a track scene or follows one.
  `_regrid` moves `grid_origin` and `grid_beat0`, sets `beat_s` and `level.bpm`, and adjusts `level.song_offset_ms` so tick counting stays continuous.
  It emits `tempo`. **The audio clock stream is not swapped.** The silent 64-beat loop stays at the old tempo and nothing in `src/` hears `tempo`.
- Song time stays continuous because it is the unwrapped playhead of the silent stream. Wrap detection depends on `loop_seconds`, not on the engine
  tempo. Whether this is right in `RunPlay` with a real track has never been run **[R: A]**.
- Things that assume a constant integer tempo or 174: `clock_rate`, `frames_per_beat`, `silent_loop`, loop-scene audio, riser and fall length, the plan
  arithmetic in `run_track_plan.gd` (constant `bpm` from `first_downbeat_s`), `phase_n_for_first_beat`, cast `at_beat`, the passage aperture, the card
  table, the hotspot view (`beat_s` is cached; section 11).
- Track tempos in the 44 imported packs **[R: A]**: 20 at 174, 17 at 175 (rounded), 3 at 172, one each at 140, 168, 173, 177. `DECISIONS.md` quotes "58
  of 61 between 172 and 176"; that figure covers all 61 recordings in the catalogue and is consistent with this.

### 5.5 Track packs and their metadata

- Format: `docs/TRACK_PACK_FORMAT.md`; validator `tools/audio_import/validate_track.py`. Stems are Vorbis 48 kHz stereo, one to six voices plus a
  backing stem, equal length within 5 ms. Pack sizes are 50 to 97 MB **[R]**.
- Location: outside the repository. `RW_TRACKS_DIR` or `user://track_packs` (`run_track_scenes.gd:55`), `<dir>/<track id>/track.json`. Standalone mode
  uses `RW_TRACK=<dir>`.
- Never committed (owner rule: third-party recordings). In Git: `content/music/tracks/catalogue.json` (61 recordings; its `counts.imported` says 44), 44
  per-track metadata files, `docs/MUSIC_TRACKS.md`, and a synthetic fixture `tests/fixtures/track_fixture` (120 BPM, 16 s).
- Packs on this PC (`ONE_PC_PLAN.md` section 3): 47 folders in `NewMusicTry5\packs`, 46 with `track.json`; the assignment names 61 tracks, 41 have a
  usable pack, 5 failed validation on the laptop and 15 have no pack. (The laptop's report A counted 44.)

What `track.json` carries (usable by a transition engine):

| Field | Note |
|---|---|
| `duration_s`, `tempo.bpm` (float), `tempo.first_downbeat_s`, `tempo.confidence`, `beats_per_bar` 4 | one constant tempo and one origin |
| `sections[]` with `role` intro, build, drop, breakdown, outro, other | bar-aligned, estimated by the tool, not verified |
| `voices[]`, `backing[]`, stem gains | for per-stem control |
| `focus[]` | stretches where one voice leads |
| `charts{easy,normal,hard}` | cues `{t, pad, dur, conf, voice}` |
| `source.sections_detail[]`, `source.tempo_detail` | extra detail; the plan reads `sections_detail`, nothing reads `tempo_detail` |

Absent **[R: A]**: manual first-drop time, intro and outro cue points, musical key, per-bar beat map for a drifting tempo, loudness per section inside
the pack (the repo-side `quick` data has some), loopable regions, transition suitability scores. The only manual hook today is the per-scene
`start_bar`, `laps` and `entry` override in `track_scenes.json`.

### 5.6 What "track scenes" has built, and what is unbuilt

Built (logic half, on a virtual clock with synthetic fixtures):

- Assignment: `content/run/track_scenes.json`, format `rhythm_warfare.track_scenes.v1`; defaults entry `drop1`, `lead_in_bars` 16, `doors_from_lap` 2,
  `chart` normal, `max_laps` 12. Counts: main 36, gospel 17, squadron 14, ember 15 (checked in the JSON). Loader `RunTrackScenes`: seeded pick between
  first choice and alternates, skips a missing or refused pack.
- Switching: on in the game, off with `RW_RUN_TRACKS=0`, **off under `tests/run_tests.gd`** unless a test sets `RunTrackScenes.enabled = 1`
  (`run_track_scenes.gd:40-51`).
- Plan: `RunTrackPlan.compute` (`run_track_plan.gd:39`): entry bar from the first drop minus 16 bars, laps near half-way, scene time 0 at bar E.
- Engine: re-grid, laps from the plan, doors closed on lap 1, open laps, minigame hold adds a lap (`track_extend`), track wrap, cues from the chart
  (`_chart_track_block`, `:801`), neutral blocks, `energy.track`, the seven events of section 4.2.
- Tests: `tests/test_run_tracks_{plan,data,engine,safety}.gd` on synthetic packs. A safety test (`baseline_runs.json`) proves that with track scenes off
  the event stream equals the pre-change stream. The engine report states the full suite passed with 0 failures and no `SCRIPT ERROR` on the Linux
  laptop **[R]**.

Unbuilt (confirmed by `grep`: the word "track" does not appear in `run_audio.gd` or `run_play.gd` in a track scene sense):

1. Start all stems of the track as one synchronised group on `track_start` at `track_t`.
2. Seek on `track_wrap`; fade or stop on `track_end`; stop on Bassment entry.
3. Per-voice mutes in the run (miss mutes `cue.voice`; logic exists in `src/track/track_game.gd`).
4. A limiter on the run's music path.
5. Loading: off-thread decode of the stems of possible next packs, keep current and next only, fall back to an ordinary scene if not ready.
   `TrackPack.load_pack(decode=true)` (`track_pack.gd:82`) is synchronous.
6. Consumers of `tempo`: `card_table.beat_s`, `HotspotView.beat_s`, stage tempo; doors following `route_window.last`; a dev overlay line; bot policy
   (`_bot_taps` leaves every track scene at lap 2).
7. Riser, fall, dip and treatments on the track group (optional, decision pending).
8. Measurements with real packs (cue against audio, load time, frame time at entry, memory) and automated playthroughs with real packs.
9. A decision on the clock stream: swap it at a float tempo or leave it.

The brief for 1 to 9 is `docs/TRACK_SCENES_HANDOVER.md` ("What is left") **[R: A]**. Nobody has heard a track scene. Until the audio half exists, do not
point the game at the packs for normal play: the engine would run at the track's tempo while the old loops play.

### 5.7 Stems and synchronised playback

- `AudioStreamSynchronized` is in use in `StemTransport` (up to `MAX_STREAMS` 32, one player) and `TrackTransport.load_pack_streams`
  (`src/track/track_transport.gd:12`) for a track's stems.
- Per-stem volume: `set_sync_stream_volume`, driven in `_process` with a 0.03 s linear ramp (`RAMP_S`). Per rendered frame, main thread, not
  sample-accurate.
- Seek accuracy of Vorbis substreams in a synchronised stream, and mid-playback seek, are not tested for sound (`tests/test_track_transport.gd` asserts
  structure and monotonic time only). Memory per loaded pack, decode cost and load time are unmeasured on any platform **[R: A]**.

### 5.8 Android audio

`export_presets.cfg`: Android preset (template export, no gradle, arm64-v8a only, package `com.joesalmon.rhythmwarfare`) and a Windows Desktop preset.
`project.godot` sets `audio/driver/mix_rate=48000` and nothing else for audio. There are no packs in any export (they are outside the project folder).
Getting packs onto a phone is out of scope in `docs/RUN_TRACK_SCENES.md` ("Not in scope") and has no mechanism. See section 9.

---------------------------------------------------------------------------------------------------------

## 6. Narrative

### 6.1 Locations (mapping to the five mainline places)

| Target location | Exists as | Scenes | Note |
|---|---|---|---|
| Warehouse Rave | world `warehouse` | 6 | the start, all quest portals, the wizard |
| Hospital Ward | world `hospital` | 6 | plus `hospital_late` (4) |
| Mental Hospital | world `ward` | 6 | plus `ward_late` (4); includes the blackjack table |
| Alien Spaceship | world `mothership` | 5 | |
| Hell | world `underworld` | 5 | its music is marked temporary (a stand-in track) **[R]** |

Naming trap: the world id `hospital` is the Hospital Ward. The world id `ward` is the Mental Hospital, and its title in the data is also "The Ward".

Routes of the main run: Warehouse, then (Mothership or Underworld) by the Door, then (Hospital or Ward) by the Airlock or the Throne, then the late
worlds. The Door's bouncer sends a pass to the Mothership and a miss to the Underworld. The Airlock examiner and the Throne send a pass to the Hospital
and a miss to the Ward. There is no route between Alien and Hell, none back to the Warehouse and none out of the late loops **[R: B]**.

### 6.2 Quests

| Quest | Exists as | Scenes | Endings | Entry |
|---|---|---|---|---|
| Dungeon | the Bassment (`src/trial`) | 64 passages | 7 deaths, 1 victory | wizard in `warehouse` and `warehouse.chill` |
| Jesus | path `gospel` | 17 | `tomb`, `road` | `warehouse.balcony.star` |
| Catch-22 | path `squadron` | 14 | `free` | `warehouse.booth.radio` |
| LOTR | path `ember` | 15 | `quenched`, `kept` | `warehouse.bar.ember` |

The repository uses original names and contains no quotations or character names from the sources (a search for the novels' names found nothing **[R:
B]**).

### 6.3 How a quest is entered and left

Entered:

- Only from the Warehouse, only by a hotspot, and always rhythm-gated. The hotspot's `on_success` route is `path:<id>` (or `trial:1` for the Bassment).
  A missed final block takes `on_failure`, which stays in the Warehouse chain.
- The Jesus star needs flag `wh_saw_floor` (set by the balcony rail on a pass). The LOTR ember needs `wh_vip_pass` (set by the Bar stranger on a pass);
  a miss there sets `wh_stranger_gone` and locks Ember out for the run. The Catch-22 radio has no flag gate. The wizard is in the early window and needs
  flag `wh_wizard_met` to be unset, so the Bassment can be entered once per run.
- Once the player leaves through the Door, no quest is reachable again in that run.

Left:

| Quest | Authored way back | Lands on | Other way |
|---|---|---|---|
| Gospel | ending scenes `jerusalem.tomb`, `jerusalem.road` (2 of 17) | `warehouse` floor | pause menu "Leave this path" |
| Squadron | `escape.c13` (1 of 14) | `warehouse` floor | pause menu |
| Ember | `mountain.spring`, `mountain.keeper` (2 of 15) | `warehouse` floor | pause menu |
| Bassment | 7 death passages, victory passage 63 | `warehouse` floor | system back key (no on-screen button) |

The landing is always `"warehouse"` (`_path_swap` start; `trial_leave` node). It is never the room the player came from. Energy and phase count carry
over. Pause-menu leave acts at the end of the phase.

### 6.4 The numbers **[R: B]**

Computed by script over the JSON data by report B and not recomputed here. The same figures, with the target graph, are in `NARRATIVE_GRAPH.md` section
1.2 and `graph/validation_report.md` section 1.

Minimum player choices from the first scene (the Floor) to each quest entry, every touch passed: Dungeon 1 (the wizard on the Floor, blocks 0 or 1);
Catch-22 3 (Floor, Bar, Booth, radio); Jesus 6 and LOTR 6, but only by using the Bassment back key as a shortcut to the Floor (Floor, Balcony or Bar,
the wizard in the Chill-out, back key, Floor, Balcony or Bar, star or ember); without the back key both cost 25. Mothership and Underworld cost 4;
Hospital and Mental Hospital cost 8.

The 5 by 4 hub table (does a mainline location offer an entry to each quest?): only the Warehouse row is filled (Dungeon yes, the wizard on the Floor
and in the Chill-out; Jesus yes, gated; Catch-22 yes; LOTR yes, gated). Hospital Ward, Mental Hospital, Alien Spaceship, Hell and the late worlds offer
none: 4 of 20 cells.

Choices per scene. Two different definitions give different numbers. State which one you mean.

| Group | Scenes | Touchable at the final window, no flags (C) | Touchable in any window (B) | Distinct destinations (B) |
|---|---|---|---|---|
| Main run | 36 | 3 or 4 in 35, 2 in 1 | 2 to 5 | 1 to 3 (1 in 18 scenes) |
| Gospel | 17 | 3 in 9, 2 in 8 | 2 to 3 | 1 to 2 |
| Squadron | 14 | 3 in 1, 2 in 13 | 2 to 3 | 1 to 2 |
| Ember | 15 | 3 in 5, 2 in 10 | 2 to 3 | 1 to 3 |
| Bassment | 64 | not applicable (text choices) | 1 to 3 visible | 1 to 3; 62 of 64 passages show fewer than 3 |

Of the main run's 117 final-window hotspots, 52 are exits **[R: C]**. Pass and miss routes differ on 59 hotspots (11 main, 15 Gospel, 15 Squadron, 18
Ember). Every route comes from the hotspot data; the `next` lists in `run.json` agree with it **[R: B]**. `energy_min` is 0 on every hotspot, so energy
never gates a door.

### 6.5 What is remembered and what is saved

In memory during a run:

- `RunProgress.run_flags` (a dict passed by reference into every `RunHotspots`). Cleared by `run_started()` with `.clear()` so the references stay
  valid. Flags survive path hand-offs and Bassment trips.
- `RunEngine`: `energy`, `phase_n`, `lap_extra`, `node_id`, stage, block, `choice`, `window_open`, `route_locked`, `hold`, `away`, `level.notes`, track
  fields.
- `RunPlay` logs: `phase_log`, `event_log`, `hotspot_log`, `lap_log`, `path_log`, `trial_log`. They are for tests and walks, grow without a bound and
  are not saved.
- There is **no route history** and no visited-scenes list in the engine.

Saved between runs, `user://story_run.json` (`RunProgress`, `VERSION := 2`, atomic write, a bad file is renamed `.corrupt`; `run_progress.gd:7-9`):

| Key | Content |
|---|---|
| `reached` | world id to entry count (main run worlds only) |
| `runs`, `best_phases` | counters |
| `flags` | only flags prefixed `keep:` |
| `paths` | `{path: {reached: [worlds], endings: [names]}}` |
| `wallet` | blackjack money |
| `seed` | per-run seed, advanced in `run_started` |

Save points: `enter` and `path_enter` at every `phase_start` (a disk write each scene), `path_ending`, `set_flag` for `keep:` flags, wallet changes,
`run_started`, `run_ended`, and after a hotspot commit when `persist_dirty`.

Other saves: `user://settings.cfg` (`Session`), `user://campaign.json`, `user://story_campaign.json` (older modes; read once for migration, never
written).

Not remembered **[R: B, D]**: the scene the player left; the player's position inside a quest (re-entry restarts at the quest's first scene, and the
Bassment restarts at passage 1 with no items); which hotspots were used up; energy and phase count between runs. "Start from a reached level" restarts
at the world's entry scene. No `keep:` flag gates any hotspot today. They only change how a portal looks.

---------------------------------------------------------------------------------------------------------

## 7. Interaction

### 7.1 The hotspot system

- Data: `content/run/hotspots/<world>.json` (7 files) with `{"world", "hotspots": [...]}`; paths in `content/paths/<id>/hotspots/`; Bassment in
  `content/trial/hotspots.json`. Schema and validator: `HotspotContract` (`hotspot_contract.gd`).
- A hotspot has an `anchor` (exactly one of `thing`, `waypoint`, `actor`, `pos`), a `kind` (`exit`, `object`, `character`, `feature`, `encounter`,
  `secret`), `radius_m`, `min_px`, `available` conditions (flags, energy, `once`), `look`, `on_success` and `on_failure` (route, flags, cinematic,
  energy, music, pieces, activity), `default` (exactly one exit per scene), `window` and optional `staging` and `acting`.
- Limits in code: `MIN_PX := 72.0`, `MIN_PER_SCENE := 2`, `MAX_PER_SCENE := 4` (`hotspot_contract.gd:27-29`). A scene may raise its own cap with
  `max_hotspots`. One node does: `ward`, with 5 (the card table; `content/run/run.json:3068`, written by `tools/run/make_scenes.py:290`). Lead ruling 16
  lets a hub set up to 10. `check_hotspots.py` reads the same field (default 4, line 288).
- Windows: "final" (default), "early" (route `trial:`), "any" (an activity such as the card table). The window kinds are in `RunHotspots.window_of`
  (`run_hotspots.gd:87`).
- Kinds of outcome: exit (a door; failure is the same door with a stagger and -5 energy), stay-in-scene (flags, energy, a music variation or dip, a set
  piece), secret (flag gated, may be a portal), wizard (early window), card table (`window: "any"`).

### 7.2 The selection window and how a touch becomes a choice

1. Godot delivers `InputEventScreenTouch` and an emulated mouse event (`project.godot:63-64`, both emulations on). `LaneInput` takes touches that begin
   on a pad.
2. `RunPlay._input` (`run_play.gd:1332`) takes the press, drops a duplicate within 80 ms and 3 px, and calls `hotspot_tap(pos)` (`:1306`). There is no
   release or drag logic.
3. `hotspot_tap` rejects a position outside `_stage_host`, inside a (grown) pad rectangle, or while a minigame is active. Otherwise it calls
   `HotspotView.layout` (`hotspot_view.gd:172`) with the current camera pose and `HotspotView.hit` (`:226`), which picks the nearest centre among
   entries whose circle or touch rectangle contains the point. Then `hotspot_select(id)`.
4. `RunHotspots.select` (`run_hotspots.gd:118`) accepts a hotspot only while it is *shown* (available, window open, nothing committed). Changing the
   selection is always allowed. There is no deselect and no confirm.
5. Feedback within one beat (`SWAP_BEATS := 1.0` in `choice_staging.gd:35`): ring and thump, other hotspots dim, a person nods, a door swings open with
   a green lamp. No sound on selection was found **[R: C]**.
6. A tap that hits nothing is logged as `tap_miss` (`run_play.gd:1327`) and does nothing else.
7. Commit at beat 60.5 (`commit_final`): passed block gives `on_success`, missed block gives `on_failure`, nothing selected gives the default exit.

Desktop keys 1 to 4 pick the hotspots on show (`_unhandled_key_input`, `:1155`). `preselect` (run.json `choice.preselect`, off by default, an owner
decision pending) would allow touching a staged option before its window. An anchor out of sight becomes an edge beacon (72 px circle at the picture's
side) that is still touchable.

When a hotspot can be touched:

| Class | Touchable when | Share of scene |
|---|---|---|
| Ordinary scene, final window | beat 44.5 to 60.5 | 16 of 64 beats, 25% |
| Path scene (2 laps) | last lap only | 16 of 128 beats, 12.5% |
| Track scene | each lap from lap 2, in the lap's last block | 25% of laps 2 and later, none in lap 1 |
| Early (wizard) | blocks 0 and 1 until committed | |
| `window: "any"` | every block | |

### 7.3 Screen layout

- Viewport 1280 by 720, `stretch/mode=canvas_items`, `aspect=expand`, sensor landscape (`project.godot:28-36`). On a 20:9 phone the viewport widens to
  about 1600 by 720.
- `RunPlay` splits the screen: `_stage_host` on top, pad view at the bottom. `Session.PAD_SIZES = [0.30, 0.36, 0.42]` of the height; the default index 1
  gives 36%. So the world area is 1280 by 460.8 px (589,824 px2).
- Pads: four square pads, side `min(0.84 h, 0.15 w)` (192 px at the default), hit rectangles grown by 8% (`src/ui/pad_view.gd`). The pads sit below the
  world area, so pads and hotspots do not overlap by construction, and `layout` clamps touch centres inside the stage view.
- The world is a real 3D scene (Camera3D, vertical FOV 52) rendered into a low-resolution SubViewport (360, 270 or 180 lines, `story_lowres.gd:8`).
  People and things are sprites placed by a pinhole projector. The hotspot view is an overlay on that viewport.
- The HUD is silent (no text). The gold route-window bar lies on the bottom edge of the picture. The pause button is 72 by 56 px, top right.
- The camera pose changes all the time (rail, window camera, head tip). Hotspot rectangles follow it every frame and exist only for hotspots on show.
- Safe area is applied to the pads only. Edge-to-edge is off.

Touch sizes (`content/run/choice_staging.json`): person 1.2 by 2.1 m, door 1.7 by 2.6 m, object and feature 1.4 by 1.6 m, figure 1.4 by 2.0 m.
Per-hotspot override `staging.touch`.

### 7.4 Coverage figures and how they were obtained

**This is a model over the data, not a measurement in the running game.** Nothing in the repository measures touch coverage and nobody ran Godot. Report
C wrote a Python script (kept outside the repository) that re-implements `HotspotView.resolve`, `StoryProjector.project`, `HotspotView.layout` and the
`ChoiceStaging` touch sizes and rasterises the union of circles and rectangles over a 1280 by 460.8 view at 1 px. Exact: the geometry of one hotspot for
a given camera pose, the touch sizes, which hotspots are touchable in the window with no flags, the 72 px floor. Assumed: the camera pose, at the last
stop of the scene's `good` rail chain (perfect play), at eye height, pitch 0 (a second variant used the start waypoint; the medians are 6.3% and 5.9%,
but per-scene values swing by tens of points). People stand at their map `home`. Flag-gated extras and the wizard are excluded. The only independent
data are the legibility numbers in `docs/CHOICE_CLARITY.md`, taken with an older camera. The method, the per-scene rows and the targets are in
`INTERACTION_DESIGN.md` sections 1.2, 3 and 8.

Results **[R: C]**, union of touch area as a share of the world area, scenes with a window open (min / median / max %; scenes with 3 or more touchable):
main run 1.7 / 8.6 / 54.4 (35 of 36); Gospel 2.4 / 5.3 / 10.6 (9 of 17); Squadron 0.7 / 6.7 / 30.1 (1 of 14); Ember 1.6 / 5.8 / 20.4 (5 of 15); all 82:
0.7 / 6.3 / 54.4 (50), mean 10.2%, median 5.9% with the start-waypoint camera.

- Only `warehouse.booth` reaches 50%, and that is a near-camera artefact. Weighted by time (the window is 25% of an ordinary scene), the median area
  times time is about 1.6% of the world area over the scene. The owner's target is 50% for 80% of the time.
- In the picture at the window: 3 or more things in view in 13 of 36 main scenes, 8 of 17 Gospel, 0 of 14 Squadron, 3 of 15 Ember. Edge beacons: 38 of
  117 main-run hotspots.
- Smallest target: 72 px (the floor) is reached by 52 of 117 main-run hotspots. 72 px is about 41 dp on a 2400 by 1080 phone (report C's arithmetic; the
  repository states no dp or mm target).
- Visual coverage (how much of the picture is a distinct object) has not been measured by anything.

### 7.5 What exists to check hotspots

| Tool | What it checks | Limit |
|---|---|---|
| `tools/run/check_hotspots.py` | fields, anchors, routes, 2 to cap per scene over every flag combination, one default exit, reachability, path and lap rules | data only: no geometry, sizes or time |
| `tests/test_hotspots_{data,engine,view,scene,any_window}.gd`, `test_choice_clarity.gd` | contract, selection, windows, projection and the 72 px floor, touch to select in a scene | no coverage figure |
| `tools/run/choice_audit.gd` and `choice_audit.py` | plays every scene on the virtual clock and, at beats 4, 30, 50, 56, places each hotspot with the real `HotspotView.layout`; verdict CLEAR, UNCLEAR or INVISIBLE | single view size (1152 by 648); predates the window camera; does not rasterise a union |
| `tools/run/capture*.sh`, `contact_hotspots.py` | screenshots | for looking, not measuring |
| `RW_RUN_TAPS`, `RW_RUN_SELECT` | scripted selection | goes through `hotspot_select`, not `hotspot_tap`, so it does not exercise the touch geometry |

The cost of adding one tappable object today is a map `thing` (or an actor with a home and a people-sheet re-bake), a hotspot row in
`tools/run/make_hotspots.py`, optionally a `staging` row, a cap change if it would be the fifth, and a validator run. Each object is authored by hand
through code tables **[R: C]**.

---------------------------------------------------------------------------------------------------------

## 8. Shared state

### 8.1 Autoloads (`project.godot:23-26`)

Exactly two:

| Autoload | File | Holds |
|---|---|---|
| `Session` | `src/core/session.gd` | settings (`calibration_ms`, `cue_lead_in_s`, `pad_size`, volumes, ...), the save objects (`campaign`, `story_progress`, `run_progress`), hand-off fields (`run_start_node`, `run_start_path`, `trial_direct`, `run_result`, `last_result`, `story_*`, `debug`) |
| `DuelNetwork` | `src/duel/duel_network.gd` | wifi duel state; irrelevant to the run |

There is no global run-state autoload. The run lives inside one `RunPlay` node. Either stream may want to add a service. `project.godot` is frozen for
both (`DECISIONS.md` D2), so that is a need reported to the lead.

### 8.2 Other global state

- Statics: `RunTrackScenes.enabled`, `packs_dir_override`, `json_path_override`; `RunData.arrangement_override`; `PlaytestMode` statics (`active`,
  `continue_run`, `autoplay`, ...).
- `PlaytestMode` replaces `Session.run_progress` with a sandbox object (`playtest_mode.gd`). Code that caches `Session.run_progress` earlier would write
  the real save.
- Static read-only caches (`HotspotContract._maps`, `ChoiceStaging._defaults`) are not game state.
- Buses are created at runtime by `RunAudio`, not in `project.godot`.

### 8.3 Where route state changes relative to the commit **[R: D, code checked for the line numbers]**

| When | What changes | Where |
|---|---|---|
| Before 60.5 | only `hotspots.selected`, selection times, camera walks, `hotspot_log`. All revisable | `run_hotspots.gd`, `run_play.gd` |
| 60.5 | `block_result`; energy; the hotspot outcome resolved: `run_flags` and `keep:` flags set (a `keep:` flag is saved at once), `spent`, `committed_count`, `committed`, `last_outcome`; outcome energy applied; `engine.choice` set; the cinematic queued; `_chart_next_phase`: the next scene's block-0 cues appended to `level.notes`; `route_locked` | `run_engine.gd:543-607, 651-671, 708-717` |
| 61 and 62 | door walk latched (`_door_phase`), passage swap time set | `run_play.gd:765-781` |
| 64 | `route_commit`; `node_id`, `phase_n`, `phase_t0`, `lap`, stage reset in `_enter`; `begin_scene`; for a track scene `_regrid` | `run_engine.gd:198-247` |
| 64, same frame | `Session.run_progress.enter` or `path_enter` (a disk write); stage swap. For a hand-off: new engine, hotspots, journey, data | `run_play.gd:934-975, 1614-1682` |

### 8.4 Why there is no rollback

- State is committed in two stages 3.5 beats apart and there is no pending-transition object.
- The engine API cannot un-commit. After the lock `choose` returns false and `route_allowed` refuses other chart packs. Un-doing the lock would mean
  removing the already-charted next-scene cues from `level.notes` (the judge shares that array), clearing `route_locked`, and still leaving flags and
  energy applied.
- Persisted side effects are immediate: `keep:` flags at 60.5, `reached` at `phase_start`, wallet on every change.
- The only existing way to "stay" is `engine.hold`, which must be set before the lock (the minigame). It makes `selected_route()` return the current
  node.
- A failed path load fails forward. The portal outcome's flags and energy are already applied, a new engine and hotspots are built on the old data at
  the default exit, and the old `RunHotspots` state (`spent`, `committed_count`) is lost.
- A run that dies on the last block applies no outcome. Outcome energy cannot kill (clamped to at least 1.0).
- The pause menu's leave can overwrite `choice` after the lock; the old engine is then frozen.

### 8.5 Return checkpoint

Nothing like it exists. The nearest things are `run:warehouse` with the hard-coded `returns_to`, the world-level `reached` and `paths.reached` records,
`RunEngine.resume(id, t0)` (`:159`, used for the Bassment exit) and `RunEngine.arrive` (`:190`, used to enter another run).

---------------------------------------------------------------------------------------------------------

## 9. Tests, tools and Git

### 9.1 The Godot suite

- Runner: `tests/run_tests.gd` (extends `SceneTree`). Command: `godot --headless --path . -s tests/run_tests.gd -- [--filter substr]`. It lists
  `res://tests`, takes files named `test_*.gd` except `test_case.gd` (87 files at `90a42877`, 88 on this branch), runs every method starting `test_`,
  awaits coroutines, prints `N checks, M failures` and exits 0 or 1. `--filter` matches the file path, not test names.
- Wrapper: `tools/test.sh`. It runs `--import` first (needed on a fresh checkout because `.godot/` is ignored), then the runner, then (only with no
  arguments) `python -m unittest discover -s tools/content`. The default `GODOT` is the Windows console exe in
  `$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/`. Godot runs go through `tools/dev/godot.sh` (one at a time; stage 0.4).
- On this PC the whole suite at `90a42877` ran 12.5 minutes after a 2.5 minute first import: 127,906 checks, 0 failures, 0 `SCRIPT ERROR` lines. The
  laptop counted 127,940 on the track-scenes branch; the 34 checks of difference are not yet explained (`ONE_PC_PLAN.md` stage 0.1).
- Track scenes are off under the runner, so the suite never needs real packs.

### 9.2 The "0 failures on a parse error" trap

The runner prints `0 failures` even when a script has a parse error, because it records "failed to load" only when `load()` returns null
(`run_tests.gd:23-26`). A parse error inside a method may only show in the log. So after every full run also count script errors:

```
GODOT=... bash tools/test.sh 2>&1 | grep -c "SCRIPT ERROR"      # must print 0
```

`tools/test.sh` filters stdout but does not count them for you. A green summary plus a non-zero count is a failure. This is from
`docs/BLACKJACK_INTEGRATION.md:158` **[R: E]** and from reading `run_tests.gd`.

Other traps **[R: E]**: new `class_name` scripts need `--import` once in every worktree; new `.gd` files bring `.gd.uid` files that are committed (the
handover branch lacked five, which the lead commits in stage 0.3); in Godot 4.5 `var x := dict["k"]` is a parse error; tests that set the
`RunTrackScenes` statics must reset them; expected log noise includes "non-equal opposite anchors" and a `Parse JSON failed` line from the corrupt-save
test. Some art tools (`check_assets.py --determinism`) rewrite committed art; run `git checkout` afterwards.

### 9.3 Other checks

| Command | Purpose |
|---|---|
| `python tools/run/check_hotspots.py [world] [--path gospel\|squadron\|ember]` | hotspot data; pure Python; baseline 0 errors **[R]** |
| `godot --headless -s tools/run/check_path.gd -- gospel` | path data |
| `godot --headless -s tools/trial/validate.gd` | Bassment data |
| `godot --headless -s tools/export_smoke.gd` | the exported pack holds what the game loads |
| `python -m unittest discover -s tools/audio_import -p 'test_*.py'` | importer tests; not run by `test.sh` |
| `python tools/content/beatshaper.py validate` | loop pack warnings |
| `tools/run/walk_run.sh [--path ...]` | a whole run on the virtual clock; needs a display |
| `tools/run/choice_audit.gd` | see section 7.5 |

### 9.4 Environment variables that matter

About 81 distinct `RW_*` names are read in `src/` and about 140 across `src` and `tools` **[R: E]**. They are the de facto scripting interface. The ones
both streams will meet:

| Variable | Effect |
|---|---|
| `GODOT`, `PYTHON` | binary for every script; Python for `test.sh` |
| `RW_TRACKS_DIR` | folder of track packs; else `user://track_packs`. Not set machine-wide until M1 is merged (`ONE_PC_PLAN.md` stage 0.2) |
| `RW_RUN_TRACKS=0` | switch track scenes off (always wins) |
| `RW_RUN_VIRTUAL=1` | no audio, stepped clock (tests and walkers); `RunPlay.audio` is null |
| `RW_RUN_BOT=perfect\|none\|accuracy:<f>\|blocks:<...>` | automated player |
| `RW_RUN_ROUTES`, `RW_RUN_TAPS`, `RW_RUN_SELECT` | scripted route and tap policy |
| `RW_RUN_START`, `RW_RUN_PATH`, `RW_RUN_PATH_START`, `RW_PATH_REMAP` | where the run starts; which path a portal enters |
| `RW_RUN_UNTIL_PHASE`, `RW_STORY_QUIT=1` | stop and quit |
| `RW_RUN_SEED` | fixes the per-run seed (arrangement and track picks) |
| `RW_RUN_FLAGS` | preset story flags |
| `RW_RUN_MUSIC` | replace `music.json` |
| `RW_DEBUG=1`, `RW_DEV=1` | playtest overlay; developer button |
| `RW_CALIBRATION_MS` | override calibration |
| `RW_TRACK`, `RW_TRACK_START`, `RW_TRACK_CHART`, `RW_TRACK_QUIT` | standalone track mode |
| `RW_AUDIO_WORK` | importer work folder (else `~/rw-audio-work`; on this PC `C:\Users\joesa\rw-audio-work`) |
| `RW_CHOICE_PRESELECT=1` | enable `preselect` |

### 9.5 Git, CI and branches

- **No CI.** There is no `.github/` directory and the API reported zero workflows **[R: E]**.
- **`main` is unprotected** (API reported "Branch not protected") **[R: E]**. Protection against a push is discipline only: no agent pushes `main`.
- `main` is at `86950290`. The integration branch is `feature/one-pc`, created from the plan commit on `feature/one-pc-plan`; agents work on `wip/`
  branches in sibling worktrees (`C:\Users\joesa\Documents\Cursor\MusicGame-<name>`) and the lead merges with `--no-ff` (`ONE_PC_PLAN.md` section 5).
  The owner's checkout is on `feature/wizard-duel-lan`.
- Untracked in the owner's checkout: `NewMusic/` and `NewMusicTry5/` (the owner's audio drops, with the packs). Stage 0.2 adds them to
  `.git/info/exclude`, which every worktree shares. Do not run `git add -A`.
- Commit style: an area prefix then a sentence ("Track scenes: ...", "Audio import: ...", "Docs: ...", "Merge wip/x: ..."), long subjects allowed.
- `docs/HANDOVER.md` conflicts on every merge, so only the lead edits it. Third-party audio is never committed (public repository, owner rule).

### 9.6 What a checkout needs (all of it is in place on this PC)

| Need | Detail |
|---|---|
| Godot | exactly 4.5.1 stable, console exe; `tools/dev/godot.sh` and `tools/test.sh` default to the one in `Downloads` |
| Git Bash | the `.sh` tools and `bash tools/test.sh` |
| First import | `godot --headless --path . --import` in every new worktree (`.godot/` is ignored; 17,429 tracked files, 7,411 are `.import`) |
| Python | the venv `C:\Users\joesa\rw-audio-work\venv` (Python 3.13: `numpy`, `mido==1.3.3`, `pillow`); ffmpeg on `PATH` for the audio tools |
| Line endings | `.gitattributes` forces `eol=lf`; `core.autocrlf false`; scripts that write files on Windows can emit CRLF (`build_gospel_art.py`); `git checkout` them. `core.fileMode false` (11 files carried the executable bit) |
| Size | first clone about 0.85 GB; exported pack 184 to 240 MB **[R]**; paths: no case clashes, no symlinks, longest 93 characters **[R: E]** |
| Hard-coded Linux paths | the importer's were fixed in stage I1; what remains is in `FILE_OWNERSHIP.md` section 8.2 (`play_track.sh`, README text, `catalogue.json:9`, `tools/trial/walk_trial.sh` using `/tmp/claude-1000/...`). The Godot suite is not affected |
| Packs | not in Git; made on this PC; `RW_TRACKS_DIR` points at them for the music stream's own commands only |
| Export | `export_presets.cfg` has the owner's Windows keystore path (line 65); APK builds need export templates, JDK 17, Android SDK 35 |

### 9.7 Android device testing today

The export presets exist. `docs/EXPORT.md` documents `adb install -r`, `am start` and `adb logcat -s godot`. The APK has never been installed on a phone
**[R: E, docs/PICKUP.md]**. The last exports predate the loadout redesign. Permissions in the preset: INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE
(`docs/EXPORT.md` says "no permissions" and is out of date; `export_presets.cfg:77-79` shows the two ACCESS entries true). No frame time, memory, Ogg
decode cost or output-latency figure from a device exists anywhere.

---------------------------------------------------------------------------------------------------------

## 10. Status table

Status: **implemented**, **partial**, **missing**. Size is the remaining work: **straightforward**, **complex**, **uncertain** (not enough known to size
it). "n/a" means nothing remains.

| Capability | Status | Size | One line of evidence |
|---|---|---|---|
| Track packs (format, importer, validator) | implemented | n/a | `tools/audio_import/`, `validate_track.py`; runs on Windows and the GPU since stage I1; packs outside Git |
| Track packs for all 61 recordings | partial | straightforward | 46 packs with `track.json` on this PC, 41 usable; 5 failed validation, 15 recordings have no pack (stage I3 finishes the import) |
| Track scenes engine (plan, laps, doors, re-grid, cues, events) | implemented | n/a | `run_engine.gd` +299 lines, `run_track_*.gd`, 4 test files; virtual clock and synthetic packs only |
| Track scenes audio (group, mutes, wrap, end, load) | missing | complex | no track handling in `run_audio.gd` or `run_play.gd`; nine items in section 5.6 |
| Limiter on the run bus | missing | straightforward | `AudioEffectHardLimiter` only in `track_play.gd` |
| Clock with float tempo | missing | uncertain | `clock_rate`, `frames_per_beat`, `silent_loop` take `int`; engine re-grids, clock does not; the choice (swap or keep) is undecided |
| Crossfade between songs | missing | complex | scene change is a 0.6 s fade-out and a start on the downbeat; no overlap of two songs |
| Stem fades | partial | straightforward | per-stem `set_sync_stream_volume` with a 0.03 s ramp exists (`StemTransport`, `TrackTransport`); not used in the run, no timed fade API |
| Tempo ramp, time-stretch, pitch shift | missing | uncertain | no `pitch_scale`, `AudioEffectPitchShift` or stretching in `src/`; technology unevaluated |
| Transition metadata (first drop, mix points, no-blend) | missing | straightforward | `content/music/transitions/` absent; packs carry sections and tempo only; manual drop time absent |
| Transition port and director | partial | straightforward | the port (a byte copy of the contract) and the mock director with 15 conformance cases exist; `transition_director.gd` does not |
| Track-event consumers (`tempo` and six more) | missing | straightforward | no handler outside `run_engine.gd` (section 4.2) |
| Real-hardware audio measurement | missing | uncertain | only dummy-driver figures exist **[R: A]** |
| Narrative graph (data-driven, validated) | missing | complex | no `NarrativeGraph`, no `content/narrative/`; graph exists only as hotspot data, `run.json` `next`, and report B's JSON |
| Quest entry from every location | partial | complex | 4 of 20 hub cells filled, all in the Warehouse; all rhythm-gated, two flag-gated |
| Quest entry never rhythm-gated | missing | straightforward | all four entries use `on_success`/`on_failure` on a passed block; the data change is small, but the Bassment entry is mid-scene |
| Return checkpoint | missing | complex | returns are hard-coded to `"warehouse"` (`_path_swap`, `trial_leave`, `run_data.gd:181`); `resume`/`arrive` are the nearest hooks |
| Return from every quest scene | partial | straightforward | pause-menu "Leave this path" works; in-world returns on 5 of 46 path scenes plus Bassment endings; Bassment has no on-screen back |
| Quest progress persistence | missing | straightforward | `story_run.json` keeps worlds reached and endings only; re-entry restarts at the first scene |
| Transactional route state (pending transition, rollback) | missing | complex | two-stage commit, no pending object, no undo (section 8.4) |
| Three choices per scene | partial | complex | main run 35 of 36 scenes have 3 or more touchables but 1 to 3 destinations; quests 2 to 3 touchables, 1 to 2 destinations; Bassment 62 of 64 below 3 **[R]** |
| More than four hotspots | partial | straightforward | cap is `MAX_PER_SCENE := 4`; per-node `max_hotspots` works (one node uses 5); the contract and validator default stay 4 |
| Always-open selection | missing | complex | window is 16 of 64 beats; `preselect` exists but is off; lap 1 of a track scene has none |
| Selection feedback within one beat | partial | straightforward | swap within `SWAP_BEATS` 1.0 inside the window; no sound on selection **[R]** |
| Coverage measurement tool | missing | straightforward | `tools/run/coverage_audit.*` absent; `choice_audit.gd` and the real `HotspotView.layout` are reusable |
| Coverage target met (50% of world for 80% of time) | missing | complex | modelled median 6.3% for 25% of the time **[R: C]** (a model, not a measurement) |
| Touch targets at 48 dp | partial | straightforward | floor is 72 px (about 41 dp, derived); 52 of 117 main hotspots sit near it |
| Android device testing | missing | uncertain | APK never installed on a phone; no device figures anywhere |
| Pack delivery to Android | missing | uncertain | packs outside every export; no copy-to-`user://` mechanism; out of scope in `docs/RUN_TRACK_SCENES.md`; stage X4 of the plan adds one |
| CI and branch protection | missing | straightforward | no `.github/`; `main` unprotected **[R: E]** |

---------------------------------------------------------------------------------------------------------

## 11. Things that will surprise a newcomer

1. **The clock is silent.** Song time is the playhead of a silent 8-bit loop. All music is separate players started "on" that clock. A track scene
   changes the engine's tempo but not the clock stream.
2. **`beat_s` now changes inside one engine.** `card_table.beat_s` and `HotspotView.beat_s` are cached when set (in `_path_swap` and at setup) and are
   stale after a `tempo` event. `RunPassage` and the door walk read `engine.beat_s` live.
3. **Track scenes silently do not exist on most machines.** Without packs every scene is ordinary. The game runs fine and looks as if nothing is wrong.
   Under `tests/run_tests.gd` they are off by a check of the main loop's script path (`run_track_scenes.gd:48`). A different runner changes behaviour.
4. **Nobody has heard a track scene, and the docs assume a limiter that is not there.**
5. **The safety test is strict.** `test_run_tracks_safety` compares the event stream with `tests/fixtures/track_scenes/baseline_runs.json`. Adding an
   event or changing order in `run_engine.gd` can break it **[R: D]**.
6. **A path hand-off discards the main engine and builds new ones.** Anything holding a reference to the old `engine`, `hotspots`, `journey` or `data`
   (a quest tracker, a music director, a view callback) must be re-wired in `_path_swap`. `RunPlay.live_engine()` (`:1684`) returns the Bassment's
   engine while in the dungeon.
7. **`phase_n` is not "scenes".** Laps and holds also count. `scene_index() = phase_n - lap_extra`. `trial_begin_now` adds 1 by hand.
   `RunProgress.enter` is called at every `phase_start`, so entry counts include laps.
8. **The route lock compares chart keys, not destinations.** `route_allowed` (`run_engine.gd:345`) refuses a second choice after the lock if the chart
   pack or track differs.
9. **Disk writes happen in the frame loop** at every `phase_start` (`RunProgress.enter`) and at `keep:` flag changes. The track plan's JSON parse is
   also on-frame unless `warm()` was called.
10. **Content is validated at load and a failure is fatal.** `RunData._validate()` collects errors and `RunPlay` calls `_fatal`. Rules include 2 to cap
    hotspots per scene, one default exit, a lit doorway for every route, acyclic world graphs except `loop` routes, `path.returns_to == "warehouse"`. A
    narrative graph must pass these or change them.
11. **Seed order matters.** `RunProgress.run_started()` runs after the first `RunData` load in `RunPlay._ready`, so the seed used for the first data is
    the previous run's "next seed". Track and arrangement picks use `hash("%d:%s" % [seed, scene])`.
12. **`RunTrackScenes.attach(d)` must be the last step of `RunData.load_files`.** It needs seed, nodes and path id.
13. **Virtual mode has no audio.** With `RW_RUN_VIRTUAL=1` `audio` is null. The run tests and walkers use it. Audio paths run only in real playback and
    in the dedicated `test_run_audio_*` tests with the dummy driver (mix period 88.5 ms against 6 to 20 ms on devices).
14. **The bot leaves every track scene at lap 2.** `_bot_taps` taps whenever `engine.window_open`, which is true from lap 2 on a track scene.
15. **Quest entrances look like flavour objects.** In the data a quest entrance is a `secret` hotspot with a `path:<id>` route, gated by flags that
    other hotspots set on a pass. A missed block can lock Ember out for the whole run (`wh_stranger_gone`).
16. **`.import` and `.uid` files are committed.** Opening the editor can rewrite them. A different Godot version changes them.
17. **Art is generated by code.** Hotspot art, maps and scenes come from Python generators (`tools/story/art/`, `tools/run/make_*.py`). Editing the JSON
    by hand is overwritten by the next generator run. People sheets are generated and committed; never merge them, regenerate.
