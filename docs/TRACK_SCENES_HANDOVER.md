# Track scenes: hand-over to the Windows PC

Written on 6 November 2026 on the Ubuntu laptop. The work of putting the imported recordings into every scene
of the run is half done. This file says what exists, what is left, and how to carry on from another machine.
The contract for the whole feature is `docs/RUN_TRACK_SCENES.md`; it is binding and has not changed.

## State

| Part | State | Where |
|---|---|---|
| Importer (recordings to track packs), hardened for a whole folder | done, in `main` | `tools/audio_import/`, `docs/TRACK_PACK_FORMAT.md` |
| Standalone track mode (one track, four pads, mute on a miss) | done, in `main`, played and approved by the owner on "Go Back" | `src/track/` |
| A track for every scene (first choice and two alternates, 82 scenes) | done, in `main` | `content/run/track_scenes.json`, `docs/TRACK_ASSIGNMENT.md` |
| Track scenes, logic half: assignment loader, scene plan, engine (own tempo per scene, laps with doors that open from lap 2, cues from the chart, neutral blocks, energy numbers, events) | done, in `main`, tests green | `src/run/run_track_scenes.gd`, `src/run/run_track_plan.gd`, `src/run/run_engine.gd`, `tests/test_run_tracks*.gd`, `tests/fixtures/track_scenes/` |
| Track scenes, audio and wiring half | **not started** | `src/run/run_play.gd` and a small audio class; see "What is left" |
| Automated playthroughs with real packs, owner's guide update | not started | |
| The packs themselves (audio) | on the laptop only, never in Git | see "The audio" |

Nobody has heard a track scene. The engine is proven on a virtual clock only.

**Why the game still plays as before.** A scene is a track scene only if its assigned pack is found on the
machine. Packs are looked up in the folder named by `RW_TRACKS_DIR`, else in `user://track_packs`. With no
packs there, every scene is an ordinary scene and the run is identical to before (checked: the real assignment
file loads with 0 errors, 0 track scenes without packs, 81 of 82 with the 44 packs present on 6 November).
`RW_RUN_TRACKS=0` switches the feature off whatever is present. **Until the audio half is built, do not point
the game at the packs for normal play**: the engine would run the scene at the track's tempo with the old
loops playing.

## The audio

The recordings are other artists' commercial releases and the repository is public, so by the owner's decision
no audio derived from them is ever committed: not stems, not previews, not caches. Commit only tools, game
code, tests, docs, metadata and synthetic fixtures.

The packs are made on the laptop and reach other machines as one archive that the owner copies across:
`rw-track-packs.tar` (the folder `packs/`, one sub-folder per track id holding `track.json`, `stems/*.ogg`,
`report.txt`). Unpack it anywhere and set `RW_TRACKS_DIR` to the unpacked `packs` folder. The importer does not
need to run on the Windows PC. Its defaults are Linux paths (`/home/joe/rw-audio-work`, a venv under
`/home/joe/.venvs`), all overridable by options, if it is ever needed there.

What each track is (tempo, length, sections, which instrument is played when, cue counts) is in Git as
metadata: `content/music/tracks/catalogue.json`, `content/music/tracks/<id>.json`, `docs/MUSIC_TRACKS.md`.

## What is left (the audio and wiring half)

Read `docs/RUN_TRACK_SCENES.md` (sections "Audio", "What the player sees", the loading rules, merge checks 2
and 3), then the engine report appended below: its section 1 is the brief for this work (how the feature
switches on, the events to react to, the fields on cues, the exact places in `run_play.gd` to change).
`src/track/track_transport.gd` and `src/track/track_play.gd` already play a pack's stems as one synchronised
group, mute a voice on a miss with a ramp, and limit the music bus: reuse them.

1. On `track_start`, all the pack's stems play as one synchronised group from `track_t` at song time `t`, at
   pack gains, through the music bus with the limiter; the scene's loops do not start. The group plays across
   laps with no restart. `track_wrap` seeks it. `track_end` fades it with the door while the next scene's music
   starts on its own downbeat. Entering the Bassment stops it (no `track_end` is sent there).
2. Mutes: a missed cue or a hold let go early mutes that cue's `voice`; the next hit cue of that voice restores
   it; a muted voice returns by itself after 8 beats if its next cue is further away; backing never mutes;
   30 ms ramps.
3. Loading: decode the stems of the packs a scene can lead to off the main thread once that scene's doors
   first open (and for the first scene before the run starts). Entering a scene must not stall a frame. A pack
   not ready in time means the scene plays as an ordinary scene. Call `warm()` so `plan_of` never parses on a
   frame. Keep only the current and next candidates in memory.
4. An ordinary scene sounds exactly as today, also right before and after a track scene.
5. The `tempo` event: beat-synced visuals and cached `beat_s` values follow the scene's tempo.
6. Doors and their lights on open laps, closed laps and the final lap as the contract says; no new text for
   the player. The developer overlay shows the track id, lap k of n and the entry bar.
7. `RW_RUN_BOT` must not leave every track scene at lap 2 by accident: one option to play to the default end,
   one to leave at the first open lap.
8. The riser, fall, hotspot dip and world treatments apply to the group only if simple; otherwise leave them
   out for track scenes and say so.
9. Tests on synthetic fixture packs only (`tests/fixtures/track_scenes/track_scene_fixtures.gd` writes them).
   The suite must never depend on the machine's packs, and with track scenes off everything stays identical
   (`test_run_tracks_safety` compares against a recording made before the engine work).
10. With real packs: an automated main-run pass and one pass of each path (gospel, squadron, ember) with 0
    script errors and track scenes of the planned lengths. Measure and report the agreement between cue times
    and the audio (the contract asks for within one mix chunk), the load time of a real pack, the worst frame
    time at a scene entry, and memory with packs loaded.
11. Update `docs/GAME_GUIDE.md` (scenes now last several laps, how leaving works) and `docs/HANDOVER.md`.

Then the owner listens. Only their ear can judge whether the charts feel right in the run, whether dropping
every fourth bar of the chart (the run's 12 beats of cues, 4 of rest) suits the music, and whether scene
lengths of 88 to 176 seconds are right.

## Running the tests

    godot --headless --path . -s tests/run_tests.gd -- --filter <part of a test file name>

The whole suite (no filter) takes about 20 minutes on the laptop. The runner prints "N checks, 0 failures"
even when a script failed to parse, so always also count the lines containing `SCRIPT ERROR`. New `class_name`
scripts need one `godot --headless --path . --import` first. Results on this commit's parent, with track
scenes off: see `docs/HANDOVER.md`; the engine agent's own figures are in its report below.

## Known gaps on the import side

- Seven of the first 43 recordings failed to import and are being fixed on the laptop; scenes assigned to them
  use an alternate until their packs exist. The archive carries whatever is complete when it is made.
- Scene lengths come from each track's detected first drop. A track whose drop was detected wrongly can be
  corrected per scene in `content/run/track_scenes.json` (`start_bar`, `laps`) without re-importing.

---

# Appendix: report of the agent that built the logic half (5 to 6 November 2026)

### Track scenes, logic half: report (branch feature/track-scenes, worktree /home/joe/Projects/MusicGame-tracks)

The logic half is built and the tests are green. The full suite gives **127,940 checks, 0 failures, 0 SCRIPT ERROR** (87 test files). With track scenes off, ordinary runs come out event for event and cue for cue the same as a recording made before any engine edit. I did not edit the contract.

#### 1. Brief for the audio and wiring agent

**How it switches on.** `RunData.load_files` ends with `RunTrackScenes.attach(d)`, which sets `d.track_scenes` (a `RunTrackScenes`, or null).
- Off when `RW_RUN_TRACKS=0`.
- Off under `tests/run_tests.gd` unless a test sets `RunTrackScenes.enabled = 1`. The switch is static: -1 automatic, 0 off, 1 on. Tests can also set `packs_dir_override` and `json_path_override`, or call `RunTrackScenes.load_for(d, json_path, packs_dir)` directly.
- Otherwise on, if `content/run/track_scenes.json` exists.
- Packs are looked up in `RW_TRACKS_DIR`, else `user://track_packs` (globalized), as `<dir>/<track>/track.json`.

**Is this a track scene?**
- During play: `engine.is_track_scene()`, `engine.track_info()` (track, lap, laps, entry_bar, doors_from_lap, bpm, chart, doors_open), and `engine.track_t_at(t)` (track seconds at song time t).
- For any scene, including the routes' scenes when loading ahead: `engine.track_plan_of(id)` or `data.track_scenes.plan_of(id)`. An empty dictionary means an ordinary scene.

**`RunTrackScenes` (src/run/run_track_scenes.gd):**
- `plan_of(id) -> Dictionary`: cached, protected by a Mutex.
- `warm(ids := [])`: call it on a thread when doors open, so that `plan_of` never parses JSON on a frame.
- Also: `is_track_scene(id)`, `has_entry(id)`, `candidates(id)`, `pack_dir(track)`, `pack_present(track)`, `errors`, `warnings`, `packs_dir`.

**`RunTrackPlan.compute(info, entry)` (src/run/run_track_plan.gd)** is the pure plan function. `RunTrackPlan.info_of(pack, raw)` builds its input.

**Plan fields:** track, dir, bpm, beat_s, bar_s, lap_s, first_downbeat_s, duration_s, entry, entry_bar, entry_t (track time of bar E), laps, max_laps, doors_from_lap (effective), chart, cues, total_bars, lap_scene_t, end_t, half_bar, laps_rule, node, pick, index (0 is the track, k the k-th alternate), and `pack`.

**Getting the pack:** `plan["pack"]` is the `TrackPack`, loaded with decode=false, so its `streams` are empty. Decode the stems from `pack.dir` using `pack.stems_in_order()`; there is no need to load track.json again.

**New events.** All go through `engine.update()` and are documented at the top of run_engine.gd.
- `tempo` {t, node, bpm, beat_s, from_bpm}: fires before the scene's phase_start whenever the beat changes (into a track scene, or out of one into a scene at another tempo). Use it to refresh cached `beat_s` values: `card_table.beat_s` and `hv.beat_s` in run_play.gd (about lines 284, 297, 1660).
- `track_start` {t, node, track, dir, chart, bpm, beat_s, entry, entry_bar, track_t, laps, doors_from_lap, duration_s, index, phase}: fires just after phase_start. Start every stem from `track_t` at song time `t`, and do not start the scene's loops.
- `track_lap` {t, node, track, lap, laps, track_t, doors_open, last, phase}: fires after every `lap_start`. The track should already be at `track_t`; do nothing unless there was a wrap.
- `track_last_lap` {t, node, track, lap, ends_t, route}: fires at the choice beat (60.5) of an open lap where an exit was touched. The scene now ends at `ends_t`.
- `track_extend` {t, node, track, laps}: a minigame hold has run past the plan, so one more lap is added.
- `track_wrap` {t, node, track, lap, track_t, from_track_t, decided_t}: emitted at the lap's last decision, 3.5 beats ahead. Seek the group to `track_t` (the entry bar) at song time `t`.
- `track_end` {t, node, track, track_t, reason: route | handoff | depleted, to}: fade out with the door, as a scene's music does today.

**Extra fields on existing events, track scenes only:** `phase_start.track`; `block_result.neutral` and `.track`; `route_window.last` (false on an open lap) and `.track`; `cues.track` and `.lap` (with `cues.family` set to "track").

**Notes (cues)** carry: `voice` (the pack's voice key, to drive mutes), `lap`, and `track_t` (the cue's time in the track). `time` equals the lap's downbeat plus (track_t minus the lap's track time), so a cue lands exactly where the audio plays it.

**What you must not do:**
- Do not call `apply_part_offset` for a track scene; it is ignored.
- Do not apply stage gains to track scenes.
- Do not read `engine.track` and change it.

**What you must change in run_play.gd:**
- `_bot_taps` (about line 584) taps whenever `window_open` is true. On a track scene that window is open from lap 2, so `RW_RUN_BOT` with a tap policy will leave every track scene at lap 2. Skip laps where `engine.lap < engine.laps` unless you mean to leave.
- `_scripted_select` (about line 621) and the pause menu's leave (line 766) use `engine.lap < engine.laps` as "a lap before the last". That still holds; on open laps the leave now ends the lap.
- The hotspots' `current_id()` and `destination()` show the default exit when nothing is touched. On an open lap, doing nothing means staying, so the doors' green or red state must follow `route_window.last`.
- The playtest overlay can read `track_info()` to show the track id, lap k of n and the entry bar.
- Entering the Bassment from a track scene (the wizard) sends no `track_end`. The audio side must stop the group itself on the trial hand-off.

#### 2. Edits to existing files

- **src/run/run_data.gd:** 2 lines. A `track_scenes` field (line 42) and `RunTrackScenes.attach(d)` before `return d` in `load_files` (line 163). The laps validator and `MAX_LAPS` (still 4) are untouched: track laps live in the plan, so data laps stay as they are.
- **src/run/run_hotspots.gd:** a new `begin_lap(energy)` (lines 48 to 56). It clears `selected`, `committed` and `last_outcome`, and is called only for track scenes.
- **content/run/run.json:** `energy.track` {pass_gain 1.25, pass_bonus 1.5, fail_loss 1.75, fail_flat 0.75, note}.
- **src/run/run_engine.gd** (+299 lines). Every behaviour change sits behind a non-empty `track`, or behind `_regridded`, which only a track scene sets.
  - Header comment block and new fields: `track`, `doors_from_lap`, `grid_beat0`, `_regridded`, and the lap track times.
  - `begin`: resets a re-gridded grid.
  - `_enter`: re-grids, takes laps from the plan, emits `tempo` and `track_start`, adds `track` to phase_start.
  - New `_regrid`, `track_plan_of`, `is_track_scene`, `track_info`, `track_t_at`, `_doors_open`.
  - `choose`: allowed on open laps.
  - `route_allowed` and `_chart_next_phase` now compare `_chart_key`. For an ordinary scene that is the same chart string as before; for a track scene it is "track:id:chart".
  - `_commit`: emits `track_end`.
  - `_start_lap`: track lap position, `begin_lap`, `track_lap`.
  - `_decide`: neutral blocks, the `energy.track` numbers, the window on open laps, `_track_last_block`.
  - `_hotspot_decision`: commits on an open lap only if an exit was touched.
  - `_chart_next_lap`: works out the next lap's track position and the wrap.
  - `_chart_block`: sends track scenes to `_chart_track_block`. After a re-grid, ordinary cue times use `grid_beat0`. The original arithmetic is kept exactly for runs that never re-grid; the bit-identical baseline proves it.
  - `phase_n_for_first_beat`: adds `grid_beat0` (0 when unused).
  - `apply_part_offset`: ignored in a track scene.
  - `_regrid` also sets `level.song_offset_ms` so that `Level.seconds_to_tick`, which the pad view reads, matches the cues' ticks.
- **Existing test assertions changed: none.**

#### 3. Decisions the contract left open

- **Re-grid inside one engine, not a new-engine hand-off.**
  - Main-run scene changes never build a new engine, and building one would mean rewiring RunPlay.
  - Ticks stay exact: `grid_beat0` carries the run's beat count, so ticks keep growing across tempos.
  - Cue times are computed from track seconds, not from ticks.
  - The path hand-off still works: `arrive` sets `grid_origin`, then `_enter` re-grids if the scene is a track scene.
- **Middle laps:**
  - The wizard (early window) keeps today's path-lap rule: it is offered in blocks 0 and 1 of every lap until it is committed, and `committed_early` is kept.
  - "Any" hotspots such as the card table work in every block of every lap.
  - Final-window hotspots: from `doors_from_lap` on, on every lap.
  - An activity committed on an open lap (one that keeps the player in the room) does not end the scene.
- **What counts as touching an exit:** an available final-window hotspot that is selected, a plain `choose()`, or the pause menu's leave.
- **Path scenes' authored acts:** later laps play none. Cast lines past beat 127 do not exist, and `block_fx` entries match lap 1 or 2 only. Lines a generator moved to "the last lap" (beat 48 + 64) now fire in lap 2, not at the real commit.
- **Hold:** a lap is added (`track_extend`) instead of re-entering the scene. The track wraps to the entry bar when fewer than 16 bars would be left. When the hold is released, that lap is the last and its default exit applies.
- **Cue on beat 12:** a cue exactly at beat 12.0 is kept, using the run's own `≤ cue_span + 1e-6` rule.
- **`family`:** for a drums-kind voice it is "kick" on pads 1 and 2 and "snare" on pads 3 and 4; for any other voice it is "bass". These are the palette and icon keys.
- **No drop section:** the loudest section is read from track.json `source.sections_detail[].intensity_db`. Without that, the longest section that is not an intro or outro; with no sections, bar 0.
- **Short track:** if fewer than 16 bars are left after E, E moves back so one lap fits. The audio's end wins over "at least 2 laps". A track under 16 bars is not a scene.
- **An assigned `laps`** is still cut to the audio. A `laps` above `max_laps` is a data error.
- **Errors:** problems in the file are appended to `d.errors` as sentences. A refused pack or a track too short is a warning, and the scene becomes ordinary.
- **Seed:** the pick is `"%d:%s"` of seed and scene, hashed, over the candidates whose pack is present. The Debug/Playtest `arrangement_override` also applies here.

#### 4. Energy (24 seeds, main run, default exits, cap 40 scenes; synthetic packs of about 7 cues a block, 1 block in 7 empty, 4 laps, 165 to 178 BPM)

Each cell is scenes survived, as a mean.

| accuracy | today | track scenes, today's numbers | track scenes, new numbers |
|---|---|---|---|
| 0.30 | 3.0 | 1.0 | 3.5 |
| 0.40 | 3.7 | 1.3 | 4.4 |
| 0.45 | 5.0 | 1.8 | 5.7 |
| 0.50 | 9.8 | 2.9 | 9.4 |
| 0.55 | 27.8 (10/24 reach the cap) | 4.8 | 19.6 |
| 0.60 | 40 (all) | 32.7 (15/24 at the cap) | 40 (all), lowest energy 24 against 21 today |
| 0.70 | 40 | 40 | 40 |

I also tried 0.3 times today's numbers (3.2, 4.0, 5.4, 9.0, 18.7) and 0.2 times (4.0, 5.4, 7.0, 11.1, 23.7), and chose 0.25.

At 0.55 track scenes stay harsher. Smaller steps mean less noise, and the 0.55 player sits just below break-even, so with any linear scaling you can match either the average loss per scene or its spread, not both.

The script is `tests/fixtures/track_scenes/track_energy.gd` (the A12 `laps_energy.gd` method). Logs are in `/home/joe/rw-audio-work/overnight/engine/sim*.log`.

#### 5. Test results (Godot 4.5.1, flock and XDG as instructed)

| filter | checks | failures | SCRIPT ERROR |
|---|---|---|---|
| `test_run_tracks` (plan, data, engine, safety: 20 tests) | 2,347 | 0 | 0 |
| `run_` | 15,724 | 0 | 0 |
| `hotspot` | 2,112 | 0 | 0 |
| `minigame` | 250 | 0 | 0 |
| `test_track` | 598 | 0 | 0 |
| full suite | 127,940 | 0 | 0 |

- **Safety net:** `tests/fixtures/track_scenes/baseline_runs.json` was recorded before the engine edits (commit 9eb5a3c6). It holds four runs: the main run missing every fourth cue, the main run taking the second route, a run held by a minigame, and a two-lap Gospel run. `test_run_tracks_safety` checks that the current engine reproduces it line for line.
- **Synthetic packs** are written by `tests/fixtures/track_scenes/track_scene_fixtures.gd` under user://, using the track_fixture stems.

#### 6. Warnings and things not verified

- Nothing has been heard or tested in RunPlay. The engine is proven on the virtual clock only.
- Every scene change into or out of a track scene changes `level.bpm`. Anything else that reads `level.bpm` or `seconds_to_tick` will now follow the scene's tempo.
- `plan_of` called for the first time on a frame parses track.json there; call `warm()` ahead.
- The contract's "The first lap has no doors" holds only while `doors_from_lap` is 2 or more. An assignment of 1 opens them on lap 1.

#### 7. Git

```
d762647f Track scenes: the energy balance script (bot players, today against track scenes on synthetic packs) kept beside the fixtures
f290c7f6 Track scenes: energy.track in run.json (a quarter of the per-block numbers, from bot players over 24 seeds), the pad view's ticks follow a re-grid, and the tests (plan, data, engine, safety net) with their synthetic packs
6fd83801 Track scenes: the data (track_scenes.json, packs, the seed's pick), the scene plan, and the engine (re-grid at the scene's downbeat, open laps, hold past the plan with the wrap, cues from the chart, neutral blocks, track energy, events); the safety net test
9eb5a3c6 Track scenes: recording of ordinary runs (events and cues) made from the engine before the track scene work, the safety net's baseline
```
`git status --short` is empty.
