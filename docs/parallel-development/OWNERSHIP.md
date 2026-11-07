# Ownership and integration: bedsit raves and Doom worlds (from 7 November 2026)

For stage B onward of `LONG_RUN_PLAN.md`. The older `FILE_OWNERSHIP.md` (music and narrative streams, one-pc) still governs its own
stage; where they differ for the two new streams, this file wins. Contracts: `CONTRACTS.md`.

Streams: **ENV** = environment stream (`feature/doom-layout-worlds`, `wip/env-*`, `wip/polish-*`); **PLAY** = gameplay stream
(`feature/bedsit-raves`, `wip/play-*`); **LEAD** = the lead and the engine agent it assigns (`feature/shared-contracts`, `wip/engine-*`).
Rules: one writer per file; agents commit only on their own `wip/` branch, never push, merge, rebase or reset; the lead merges with `--no-ff` and pushes;
a change wanted in a file you do not own goes to the lead in your report (file, function, change, why), never as an edit from your worktree.

## Shared files: one owner each (LEAD / engine agent)

| File | Owner | Contract it serves | Who asks for changes |
|---|---|---|---|
| `src/run/run_play.gd` | LEAD | 1, 4, 5, 8 (dispatcher, activity hosting, stage swap) | both |
| `src/run/run_minigame_host.gd` | LEAD | 4, 5 (controls layer, regions layer) | PLAY |
| `src/minigames/minigame_controller.gd`, `minigame_activity.gd` | LEAD | 4, 5 (modes, result) | PLAY |
| `src/run/run_engine.gd` | LEAD | 5 (suspend/resume rhythm), 1 (relaxed node) | PLAY |
| the judge: `src/input/pad_judge.gd`, `src/input/judge.gd`, `src/input/lane_input.gd` | LEAD | 5 (withdrawn cues) | PLAY |
| `src/audio/stem_transport.gd`, `src/track/track_transport.gd` | LEAD | 7 (stem lock; built in B1) | PLAY |
| `src/run/run_track_audio.gd`, `src/run/run_audio.gd` | LEAD | 7 (lock on the group, unlock schedule) | PLAY |
| `src/transition/transition_director.gd` (`transition_port.gd` stays frozen) | LEAD | 1 | both |
| `src/story/world/story_world.gd` | LEAD | 8 (dynamic things), 9 (state art) | ENV |
| `src/story/world/story_map.gd` | LEAD | 3, 8 (waypoints, spots, sectors) | ENV |
| `src/story/story_stage.gd`, `src/story/world/story_player.gd` | LEAD | 3 (holds), 8 (pose_fn) | ENV, PLAY |
| `src/run/run_rail.gd`, `src/run/run_journey.gd` | LEAD | 3 (move-then-hold, choice viewpoint), 1 (threshold walk) | ENV |
| `tools/run/make_scenes.py` | LEAD | 1, 3 (waypoints baked from poses) | ENV |
| `src/run/run_progress.gd` | LEAD | 6 (save v3) | PLAY |
| `src/run/hotspot_view.gd`, `src/run/choice_staging.gd`, `src/run/hotspot_contract.gd` | LEAD (package A7) | 9 (choice states, no rings) | ENV, PLAY |
| `src/contracts/**`, `tests/test_contracts.gd`, `docs/parallel-development/CONTRACTS.md`, this file | LEAD | all | both |

## Stream-owned (one stream writes; the other reads)

| Path | Owner |
|---|---|
| `tools/doom/**`, `art/reference/doom_worlds/**`, `content/story/maps/<doom scene>.json`, `content/story/maps/rave_*.json`, `content/story/maps/race_street_*.json`, `content/race/courses/*.json`, `assets/story/<doom and rave sets>/**`, `assets/race/**` (road, buildings, vehicles, cockpit art) | ENV |
| `tools/run/hotspot_tables/<doom scene>.py`, the eight-scene narrative graph behind the flag | ENV |
| `content/bedsit/**`, `content/raves/*.json`, `content/paths/bedsit/**`, `content/minigames/{cloakroom,bar,race,bass_knob}.json` | PLAY |
| `src/minigames/{cloakroom,bar,race,bass}/**` (activities, views, `RaceSim`), `src/bedsit/**`, `RaveSession` | PLAY |
| `tools/run/hotspot_tables/{bedsit,rave_*}.py`, `tests/test_{bedsit,cloakroom,bar,race,rave}*.gd` | PLAY |
| `tests/test_doom_*.gd`, `tests/test_rail_*.gd` (new) | ENV |

Generated files (`content/run/hotspots/*.json`, `content/run/run.json`, `docs/VISUAL_COVERAGE.md`): never merged by hand; regenerate with the
generators after a merge (`python tools/run/make_hotspots.py && python tools/run/make_scenes.py && git checkout -- content/story/music.json && python tools/run/check_hotspots.py`).

## Integration checklist: environment stream

Before asking the lead to merge a `wip/env-*` branch:
1. `git merge feature/shared-contracts` into the stream branch is done by the lead; the agent starts its `wip/` from the stream branch after it.
2. No edit to a LEAD file in the diff (`git diff --name-only <base>..` against the table above). Needs go in the report.
3. Data fits the contracts: rave maps carry every spot the theme file names (contract 2); every route passes `ContractShapes.route` (hold_bars on
   every leg, a choice viewpoint holds a block); race courses pass `ContractShapes.race_course`; choice things pass `ContractShapes.choice_thing` (no ring frames).
4. Tests: `--filter contracts`, `--filter story_map`, `--filter run_rail`, `--filter hotspots`, the scene's own view test (targets visible, not
   behind walls, not overlapping, not on the pads, from every choice viewpoint), `python tools/doom/check_world.py`.
5. `SCRIPT ERROR` count 0 in every run's raw output (the runner prints 0 failures on a parse error).
6. Shots: reference viewpoint, two rail viewpoints, a selected state, desktop and 20:9; named in the report. No WAD, Doom texture or audio staged.

## Integration checklist: gameplay stream

Before asking the lead to merge a `wip/play-*` branch:
1. As 1 and 2 above.
2. Activities: config passes `ContractShapes.activity_config`; `result()` passes `activity_result`; replace activities use only the controls the host
   gives (2 or 4 in the pad strip), never a pad; flags only as `rave.<theme>.<puzzle>` or ordinary run flags.
3. Progress only through `RaveSave` and the host; no direct write of `user://story_run.json`.
4. The bass: only `rave.<theme>.bass_fixed` and the host's unlock call; never a gain change on the transport from gameplay code.
5. Race: `RaceSim` reads song time only (pause freezes it); it outputs `PlayerPose` and `VehicleThing`s and nothing else to the renderer.
6. Tests: `--filter contracts`, `--filter minigame`, `--filter blackjack` (the rhythm-mode activity must be unchanged), the stream's own tests
   (`--filter bedsit`, `cloakroom`, `bar`, `race`, `rave`), and once H5 lands the phantom-failure test (a replace activity through four
   blocks of no input: no energy change, no miss, no mute, no wobble; judging resumes on the boundary with a bar of lead-in).
7. `SCRIPT ERROR` count 0; launch check with `tools\dev\play_bedsit.cmd`.

## Integration checklist: the lead, for `feature/shared-contracts`

1. Each engine hook (CONTRACTS.md, "Engine hooks") on its own `wip/engine-<topic>` branch with its test; merged one at a time.
2. After each merge: `--filter contracts` plus the suites of the files it touched (`transport`, `track_transport`, `run_track_audio`,
   `minigame`, `blackjack`, `run_engine`, `run_rail`, `story_map`), then the full suite at a pause point.
3. Both stream branches merge **from** `feature/shared-contracts` after each pause point; never the reverse.
4. A contract amendment changes CONTRACTS.md, the fixture and `tests/test_contracts.gd` in one commit and is announced to both streams.
