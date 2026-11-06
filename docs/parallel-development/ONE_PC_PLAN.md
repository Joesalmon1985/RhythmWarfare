# One-PC master plan (6 November 2026)

All the work that was split between a Windows PC and an Ubuntu laptop is now done on one machine: the
owner's Windows PC (Ryzen 7 5800X, 32 GB, RTX 3060 12 GB, Windows 11, Godot 4.5.1). This file is the plan
for that. It replaces the two implementation plans, the merge and test plan and the two worker prompts of
the original twelve-document set. The paste-ready prompt that starts the work is
`docs/parallel-development/ONE_PC_PROMPT.md`.

This is a plan. No game code was changed in writing it.

## 1. What "all of this work" is

| # | Work | State today | Section |
|---|---|---|---|
| 1 | Verify the handover branch (track scenes engine half, importer fixes) on this PC | Suite run on this PC: see section 3 | 6, stage 0 |
| 2 | Finish importing the 61 recordings | 41 packs usable, 5 failed validation, 15 have no pack | 6, stage I |
| 3 | Finish the planning documents (narrative graph, interaction design, music transitions) | 3 of them not written; 3 written but not reviewed | 6, stage D |
| 4 | Track scenes, audio and wiring half, and the seam between music and narrative | Not started. Nobody has heard a track scene | 6, stage M1 |
| 5 | Narrative graph, quests from every location, returns, saved progress, three choices | Not started | 6, stages N1, N2 |
| 6 | Interaction density: half the world touchable for 80% of play | Not started; today a median 6% for 25% of a scene | 6, stages N1, N2 |
| 7 | DJ transitions between scenes | Not started | 6, stage M2 |
| 8 | Integration, phone build, owner's play and listen, merge to `main` | Not started | 6, stage X |

## 2. The owner's decisions for this plan (6 November 2026)

1. This session writes the master plan first. The three missing design documents are the first stage of
   the work, not part of this planning session.
2. One lead session (Fable). The music work and the narrative work run as subagents in separate worktrees
   on `wip/` branches. The music stream owns the run files until track wiring is done, then the narrative
   stream takes them. Godot runs are queued, one at a time.
3. The import is finished on this PC, on the RTX 3060.
4. The plan lives on the branch `feature/one-pc-plan`, pushed. `main` is not touched until the suite is
   green and the owner says so.

Earlier decisions that still stand (from the laptop sessions; the full text is in the hand-copied
`planning/DECISIONS.md` and `planning/claude_memory/`):

- Third-party audio is never committed: not recordings, stems, previews or caches. The repository is public.
- Tracks play as recorded. The incoming track is never stretched or re-pitched.
- Each scene has its own track, entered about 16 bars before its first drop; staying is the default until
  half-way through the track; leaving is touching a door.
- Track scenes go to `main` only when the full suite and the automated playthroughs are green.
- Work is delegated to the cheapest model that can do it: Sonnet for documents, tests, data entry and
  mechanical edits; Opus for hard engine and timing work; anything repeatable is a script with no model in
  the loop. Subagent worktrees sit on `wip/` branches with checkpoint commits.
- Nothing is rewritten in pushed history. Nothing is force-pushed.

## 3. Verified state on this PC

Checked on 6 November 2026 on this machine, not taken from the laptop's notes.

| Item | Finding |
|---|---|
| Branch | `feature/laptop-handover-2026-11-06` at `90a42877` = `main` (`86950290`) + 14 commits (track scenes engine half, importer fixes, four planning documents). No conflicts. |
| Worktree for this plan | `C:\Users\joesa\Documents\Cursor\MusicGame-onepc`, branch `feature/one-pc-plan` |
| Owner's checkout | `C:\Users\joesa\Documents\Cursor\MusicGame`, branch `feature/wizard-duel-lan`, with untracked `NewMusic/` and `NewMusicTry5/` and one deleted zip. Not touched. |
| Godot | 4.5.1 console exe in `Downloads\Godot_v4.5.1-stable_win64.exe\`; `tools/test.sh` already defaults to it |
| Full Godot suite on `90a42877` | Green on this PC: 127,906 checks, 0 failures, 0 `SCRIPT ERROR` lines, exit 0, 12.5 minutes after a 2.5 minute first import (88 test files, Godot runner only). The laptop reported 127,940 checks on the track-scenes branch; the difference of 34 is not explained yet and stage 0.1 looks at it. The Python content tests were not run (the default Python has no mido): stage 0.5 |
| Python | 3.14 (default; has numpy, no mido) and 3.13. No PyTorch, no Demucs. ffmpeg 9.0.1 full build on PATH |
| Packs | `NewMusicTry5\packs`: 47 folders, 46 with `track.json`, 3.6 GB. `su3_ject_crystal_eyes` is empty |
| Recordings | `NewMusicTry5\ToAddTry4`: the 61 source files (has a `.gdignore`) |
| Planning inputs | `NewMusicTry5\planning`: `DECISIONS.md`, `OWNER_BRIEF.md`, reports A to E, agent briefs, memory notes |
| Assignment against packs | `content/run/track_scenes.json` names 61 tracks. 41 have a usable pack. 20 do not: 5 failed validation on the laptop (`exile_destructive_vibrations`, `particle_pyro`, `moving_fusion_makosa`, `mantra_decibella_tim_reaper_stars_are_calling`, `paralel_in_the_clouds`) and 15 have no pack |
| Importer | `tools/audio_import/separate.py:47` passes `device="cpu"`; `audio_io.py` hard-codes `/usr/bin/ffmpeg`; `import_track.py:700` defaults `--out` to `/home/joe/rw-audio-work`. The laptop's versions: Python 3.12.3, torch 2.15.0, torchaudio 2.11.1, demucs 4.1.0, librosa 1.0.0, numpy 2.5.4, scipy 1.18.1, soundfile 0.14.0 |
| New code folders | `src/transition`, `src/narrative`, `src/music`, `content/narrative`, `tools/narrative`, `tests/mocks` do not exist yet |

Not verified here: whether `bad_company_uk_trace_nitrous_audio_remix` on disk is the re-imported pack (the
laptop's note says its re-import finished). Stage I validates every pack and lets the validator decide.

## 4. What changes because there is one machine

| Two-machine plan | One PC |
|---|---|
| Two Fable sessions, two prompts | One Fable lead, one prompt. Streams are subagents |
| "Windows" side | The **music stream** (M). Same files as the Windows column of `FILE_OWNERSHIP.md` |
| "Ubuntu" side | The **narrative stream** (N). Same files as the Ubuntu column |
| Branches `feature/adaptive-music-transitions`, `feature/interactive-scene-choices` | One integration branch `feature/one-pc`; streams work on `wip/` branches the lead merges into it |
| Tag `w1-track-wiring`, Ubuntu merges it | Milestone M1: the lead merges the music stream into `feature/one-pc`, then the narrative stream starts from that commit |
| `requests/<side>-NNN.md` files to ask the other side for a change | The agent reports the need to the lead; the lead decides and assigns it |
| Packs copied by hand as an archive | Packs are made and kept on this PC |
| The laptop imports, Windows does not | This PC imports |
| Shared baseline SHA on `main` | Baseline is the plan commit on `feature/one-pc-plan` (child of `90a42877`) |

What does not change: `INTEGRATION_CONTRACT.md` and `contract/transition_port.gd` stay the one interface
between the two streams, and the ownership matrix stays. They are worth keeping on one PC because the two
streams still run at the same time in different worktrees, and because the mock lets the narrative stream
be tested without audio. Read "Windows" as the music stream and "Ubuntu" as the narrative stream; stage D
re-words them.

New constraints that the two-machine plan did not have:

1. **One Godot at a time.** Every worktree of this project shares one `user://` folder
   (`%APPDATA%\Godot\app_userdata\Rhythm Warfare`), and tests write there. Two suites at once would corrupt
   each other. Stage 0 builds a queue for Godot runs (section 7.2).
2. **Windows on the desktop.** The walkers (`tools/run/walk_run.sh` and others) need a display. On this PC
   they open a window on the owner's desktop while they run.
3. **The GPU is shared.** A Demucs batch and a rendered walker both use it. The import runs with the
   walkers held back, or at night.
4. **A restart loses everything uncommitted.** Worktrees are sibling folders of the checkout (never a temp
   folder), each on its own `wip/` branch, with a checkpoint commit after every finished step.

## 5. Branches, worktrees, models

| Thing | Value |
|---|---|
| Plan branch | `feature/one-pc-plan` (this commit). Pushed |
| Integration branch | `feature/one-pc`, created from the plan commit. The lead merges into it with `--no-ff` and a named merge commit, and pushes it at every milestone |
| Stream branches | `wip/import`, `wip/doc-graph`, `wip/doc-interaction`, `wip/doc-music`, `wip/music-m1`, `wip/narr-n1`, then `wip/music-m2`, `wip/narr-n2-<world>`. Local only; deleted after their merge |
| Worktrees | `C:\Users\joesa\Documents\Cursor\MusicGame-<name>`, one per stream branch, removed after the merge |
| Audio work folder | `C:\Users\joesa\rw-audio-work\` (`packs\`, `ToAddTry4\`, `cache\`, `venv\`, `planning\`), outside every repository. `RW_TRACKS_DIR` and `RW_AUDIO_WORK` point there. See stage 0.2 |
| `main` | Never pushed to by an agent. The owner says when |

| Model | Used for |
|---|---|
| Fable (lead) | Briefs, reading reports, reviewing diffs, merges, the decisions in section 9, short status notes to the owner |
| Opus | M1 audio class and `run_play.gd` wiring; M2 transition engine and its spike; `MUSIC_TRANSITIONS.md`; selection model change in `HotspotView`; the final visual polish |
| Sonnet | The other documents, validators, tests, mocks, importer portability, data entry for entrances and return objects, measurement tools, guide and hand-over updates, the independent reviews |
| No model | The import batch, the catalogue, the suite, the walkers, the coverage audit |

The lead says in every status note which model did what, and does not claim an agent ran without its report.

## 6. Stages

```
 0 foundation ──┬─ I import (script, background) ───────────────────────────────┐
                ├─ D design docs (3 agents) ── owner answers section 9 ──┐      │
                ├─ M1 track audio + seam ── owner listens ───────────────┼─ M2 DJ transitions ─┐
                └─ N1 graph, validator, mock, coverage tool ─────────────┴─ N2 world wiring ───┴─ X integration, phone, main
```

Stages I, D, M1 and N1 run at the same time after stage 0. Each stage below states the files its agents
may touch and its risks; each work package states its objective, the work and how it is accepted.

The gates, stated once:

- N1's code packages (N1.2 on) start when D1 and D2 have a complete first draft. M1 does not wait for stage D.
- N2 starts when M1 is merged **and** stage D is accepted (the owner has answered decisions 2 to 5 and 7).
- M2 starts when M1 is merged and D3 is accepted. The owner's first listen after M1 does not hold M2 back:
  what it decides (decision 6: scene lengths, the rest bar) is data in `track_scenes.json` and `run.json`,
  not the transition engine. If the owner's verdict is that track scenes are wrong in kind, the lead stops
  M2 and reports.
- Stage X starts when N2 and M2 are both merged.

### Stage 0. Foundation (lead, half a day)

| WP | Objective and work | Accepted when |
|---|---|---|
| 0.1 | Baseline: the full Godot suite on the handover branch is green on this PC (section 3). Left to do: explain the 34 checks fewer than the laptop counted (a per-file comparison of check counts), and run the Python content tests once 0.5 is done | The difference is explained or shown to be platform-dependent tests; content tests OK |
| 0.2 | Audio out of the checkout. `NewMusicTry5\` sits untracked inside the owner's checkout of a public repository, and `packs\` has no `.gdignore`, so opening that checkout in the Godot editor imports 333 Ogg files and one `git add -A` publishes other artists' music. Move `packs`, `ToAddTry4`, `planning` to `C:\Users\joesa\rw-audio-work\`. **The owner does this move or says yes to it** (section 9, decision 1) | `git status` in the owner's checkout no longer lists `NewMusicTry5/`; a pack loads in track mode with `RW_TRACK` set for that one command. `RW_TRACKS_DIR` is **not** set machine-wide: until M1 is merged, pointing the run at the packs plays track tempo over the old loops, so only the music stream's own commands set it, and every other run (N1.5's baseline, the walkers) uses `RW_RUN_TRACKS=0`. At once, whatever the owner decides about the move: `NewMusic/` and `NewMusicTry5/` are added to `.git/info/exclude`, which every worktree shares, so that no `git add` can pick them up |
| 0.3 | `feature/one-pc` created from the plan commit; `git config core.fileMode false` in the repository (11 files carry the executable bit). Its first commit: `contract/transition_port.gd` and its `.uid` copied byte for byte to `src/transition/` (the mock of N1.4 extends it, so it cannot wait for M1), and the five `.gd.uid` files that the first import on this PC created and the handover branch lacks (`tests/test_run_tracks_{data,engine,plan}.gd.uid`, `tests/fixtures/track_scenes/track_{energy,scene_fixtures}.gd.uid`), so that every later worktree does not mint its own | Branch exists and is pushed; `cmp` on the port reports no difference; `git status` is clean after an `--import` in a fresh worktree |
| 0.4 | Godot queue: `tools/dev/godot.sh`, a wrapper that takes a lock for one Godot invocation (a `mkdir` lock in the audio work folder, since Git Bash has no `flock`), releases it in a `trap`, and clears a lock whose owning process is gone. `tools/test.sh` and the walkers call it for each Godot they start, through a `GODOT_RUN` variable, not by pointing `GODOT` at it (which would deadlock). A full suite holds the lock for its whole test run, so the lead schedules full suites and agents use `--filter` runs in between. Walkers keep their own throwaway `APPDATA` | Two suites started together run one after the other; a killed run leaves no lock behind |
| 0.5 | Python: `py -3.13 -m venv C:\Users\joesa\rw-audio-work\venv`; numpy, `mido==1.3.3`, pillow for the content tests; `PYTHON` points at it for `tools/test.sh` | `bash tools/test.sh` content tests all OK (216 at the last recorded run) |

### Stage I. Import (Sonnet for the tool, then no model)

| WP | Objective and work | Files | Accepted when | Risk and fallback |
|---|---|---|---|---|
| I1 | Importer runs on Windows and on the GPU. `audio_io.py`: find ffmpeg and ffprobe with `shutil.which`. `separate.py`: a `--device` option, default `cuda` when available, else `cpu`. `import_track.py`, `catalogue_tracks.py`, `play_track.sh`: defaults from `RW_AUDIO_WORK`, no `/home/joe`. `tests/fixtures/track_fixture/make_fixture.py`: same ffmpeg fix | `tools/audio_import/**`, that one fixture script | The 41 importer unit tests pass on Windows; `test_track` Godot tests still pass | None of substance |
| I2 | Environment: into the venv, the CUDA build of the laptop's versions (torch 2.15.0, torchaudio 2.11.1), then demucs 4.1.0, librosa, soundfile, pinned with a constraints file kept in `tools/audio_import/` | `tools/audio_import/README.md`, `constraints-windows.txt` | `torch.cuda.is_available()` is true; one recording separates on the GPU | No CUDA wheel for Python 3.13 at those versions: use Python 3.12 from `py`, or the nearest CUDA build, and note it. Last resort is CPU (about 8 minutes a track on this CPU; 20 tracks is under 3 hours) |
| I3 | Validate all 46 packs with `validate_track.py`. Then one batch over `ToAddTry4` with `--skip-imported --prune-cache`: the 5 failed packs and the empty one are moved aside first (not deleted) so they import from scratch (their caches stayed on the laptop) | none in Git | 61 packs, each with 0 violations; a per-track summary; any refusal is listed with its reason, not hidden | GPU separation is not bit-identical to the laptop's CPU separation. Packs that are already good are not re-imported, so their charts do not change. A recording that still fails gets one Sonnet look; if the fix is not small, its scenes keep their alternates |
| I4 | `catalogue_tracks.py` brings `content/music/tracks/` and `docs/MUSIC_TRACKS.md` up to 61 (metadata only). Check that every one of the 82 scenes resolves to a present pack | `content/music/tracks/**`, `docs/MUSIC_TRACKS.md` | `catalogue.json` says 61 imported; assignment loads with 0 errors and 82 of 82 track scenes | A scene with no usable candidate is reported to the owner, not reassigned silently |

### Stage D. Design documents (three agents in parallel, then one review)

The briefs exist in `planning/agent_briefs/` and are reissued with this PC's paths. Each agent works in its
own worktree and reads `DECISIONS.md`, the contract and the reports. None changes game code.

| WP | Document | Model | Must contain |
|---|---|---|---|
| D1 | `NARRATIVE_GRAPH.md`, `graph/graph_today.json`, `graph/narrative.schema.md` | Sonnet | Today's graph and the target graph; a Mermaid diagram; the overlay format `rhythm_warfare.narrative.v1`; the 20 hub entrances; return rule and checkpoint; the ten validation rules as assertions; computed choice counts from the start to each quest, today and target |
| D2 | `INTERACTION_DESIGN.md` | Sonnet | The scene audit of all 82 scenes and the Bassment (choices, destinations, coverage, smallest target, what to add); the two kinds of object; the 50% and 80% definitions and how they are measured; target sizes; the documented exceptions |
| D3 | `MUSIC_TRANSITIONS.md` | Opus | The four modes and the planner's rules; the sidecar format; the grid and drop snapping; the clock hand-over; the spike's questions; what is measured on real packs |
| D4 | Review and re-word | Sonnet, independent | `INTEGRATION_CONTRACT.md`, `FILE_OWNERSHIP.md`, `CURRENT_ARCHITECTURE.md` checked against the code on this branch and re-worded for one PC (streams, not machines; no `requests/` files); a short `README.md` for the folder with the reading order and the open decisions; all six documents checked against `OWNER_BRIEF.md` and against each other; `RESUME.md` deleted |

Files: only `docs/parallel-development/**`. D4 changes wording, not meaning: no signal, argument, state or
rule of the contract changes, because M1 and N1 are already building against it. A real defect found in
the contract goes to the lead, who changes `contract/transition_port.gd` and tells both streams.

Accepted when the reviewer's list of contradictions is empty and the owner has answered decisions 2 to 5
and 7 of section 9. Risk: the interaction audit needs measured coverage, which N1.5 produces; D2 uses
report C's model first and is updated with N1.5's figures.

### Stage M1. Track scenes are heard; the seam goes in (music stream, Opus with Sonnet for tests)

The music stream owns `src/run/run_play.gd`, `run_engine.gd`, `run_data.gd`, `run_audio.gd` and
`content/run/run.json` for this stage, and for this stage only also `src/run/run_hotspots.gd` and
`src/run/run_journey.gd` (door state and door timing on open laps; N1 does not touch them). New files go
under `src/transition/`, `src/music/`, `src/run/run_track_*.gd` and `tests/test_run_track*`. The brief is `docs/TRACK_SCENES_HANDOVER.md` ("What is left", items
1 to 11, and section 1 of its appendix) with `docs/RUN_TRACK_SCENES.md` as the contract.

| WP | Objective and work | Accepted when |
|---|---|---|
| M1.1 | The track group: on `track_start` the pack's stems play as one synchronised group from `track_t`, through the music bus with the limiter; `track_wrap` seeks; `track_end` fades with the door; the Bassment hand-off stops it. Reuse `src/track/track_transport.gd` | Fixture-pack tests: start, wrap, end, Bassment stop; an ordinary scene before and after sounds as today |
| M1.2 | Mutes: a missed cue mutes its voice, the next hit restores it, a muted voice returns after 8 beats, backing never mutes, 30 ms ramps | Unit tests on the mute state machine |
| M1.3 | Loading off the main thread once a scene's doors first open; `warm()` so no JSON is parsed on a frame; only the current and next candidates in memory; a pack not ready means an ordinary scene | No frame over budget at a scene entry in `tools/run/frames.sh`; memory figure reported |
| M1.4 | The clock follows a float tempo (`clock_rate`, `frames_per_beat`, `silent_loop` are integer today); the `tempo` event refreshes every cached `beat_s` | Cue time against audio time within one mix chunk, measured on real packs |
| M1.5 | Doors and lights on open, closed and final laps; the developer overlay shows track, lap and entry bar; `RW_RUN_BOT` gains "play to the default end" and "leave at the first open lap" | Walkers reach the planned scene lengths with each bot option |
| M1.6 | The seam: `TransitionDirector` (on the port copied in 0.3) in `&"cut"` mode reproducing today's transitions; the hook points in `run_play.gd` and `run_engine.gd` that M2 and N2 need, so that neither edits those functions for music reasons again | `test_run_tracks_safety` still matches its baseline line for line; the conformance cases that apply to `cut` mode pass on the real director with a virtual clock (all 15 are run at X1) |
| M1.7 | Real packs: an automated main-run pass and one pass each of gospel, squadron, ember (walkers, dummy audio driver: script errors and scene lengths). Then a measured run with the **real** audio driver, because cue against audio and pack load time cannot be measured on the dummy driver: it runs after I3 has finished, on an otherwise idle machine, and reports cue against audio, pack load time, worst frame at a scene entry and memory | 0 script errors; figures in the hand-over, each marked with the driver it was measured on |
| M1.8 | `docs/GAME_GUIDE.md` and a section in `docs/HANDOVER.md` (Sonnet) | Written |

Milestone **M1**: full suite green, M1.7 done, merged to `feature/one-pc`, pushed. Then the owner plays and
listens for the first time (section 8). Risk: the riser, fall, hotspot dip and world treatments may not
apply cleanly to a track group; the hand-over allows leaving them out for track scenes if that is said.

### Stage N1. Narrative and interaction with no run-file edits (narrative stream, Sonnet)

Runs beside M1 and touches none of M1's files. Starts as soon as D1 and D2 have a first complete draft.

| WP | Objective and work | Files (all new) | Accepted when |
|---|---|---|---|
| N1.1 | `tools/narrative/graph.py`: builds the graph from `content/run/run.json`, the three paths' `run.json`, the Bassment passages and the overlay; checks the ten rules; exports `graph/narrative_graph.json` and a Mermaid file | `tools/narrative/**`, `docs/parallel-development/graph/**` | Run on today's data it reports today's failures (16 of 20 hub cells empty, Jesus and LOTR at 6 choices, and so on), matching report B |
| N1.2 | `content/narrative/graph.json`: locations, quests, the 20 hub entrances, return rules, exceptions. Data only, not yet read by the run | `content/narrative/**` | The validator passes all ten rules on the target graph, with the Bassment passages that offer fewer than three choices listed in the overlay as a named exception (they are a later piece; see the end of N2) and reported as such, not passed silently |
| N1.3 | `NarrativeGraph`, `RouteState`, `QuestRouter` with unit tests; the transactional rule of contract section 5 (state changes only on `switched`, from `landed`) | `src/narrative/**`, `tests/test_narrative_*.gd` | Tests green, including failed and cancelled transitions leaving the saved state untouched, and a Godot test that the runtime graph equals the Python export |
| N1.4 | `MockTransitionDirector` and `tests/port_conformance.gd` with its 15 cases; `test_port_mock.gd` | `tests/mocks/**`, `tests/port_conformance.gd`, `tests/test_port_mock.gd` | 15 cases pass on the mock |
| N1.5 | `tools/run/coverage_audit.gd` and its Python summary: real `HotspotView` projection and camera rail, every beat, per scene the touch union, visual union, share of frames at 50% or more, smallest target, overlaps; pads and HUD excluded; at 16:9 (1280x720) and 20:9 (the shape of a 2400x1080 phone) and at the three pad-size settings; run with `RW_RUN_TRACKS=0` until M1 | `tools/run/coverage_audit.*` | A baseline table for all 82 scenes, in line with report C's model (median about 6%) |
| N1.6 | The three illustrative routes of the owner's brief as tests on the mock (Warehouse to Dungeon and back, and so on) | `tests/test_narrative_routes.gd` | Green on the mock |

Milestone **N1**: merged to `feature/one-pc` when its tests are green. It has no file in common with M1,
so the order of the two merges does not matter. N1.4's conformance script is needed by M1.6: the lead
merges N1.4 first, or hands the music stream that one file.

### Stage N2. The world is wired (narrative stream; starts from the M1 merge)

The narrative stream now owns `run_play.gd`, `run_engine.gd`, `run_data.gd`, `content/run/run.json`, the
hotspot files, `run_hotspots.gd`, `run_journey.gd` and the save.

Order: N2.1, N2.2 and N2.3 first, one after the other (they share the run files). Then N2.4 to N2.6 by
world in parallel. A world agent edits only its own world's files: its table file from N2.3, its
`content/run/hotspots/<world>.json`, its map and art generators. Edits to the shared files
(`content/run/run.json`, `content/narrative/graph.json`) are delivered as a short list in the agent's
report and applied by the lead, one world at a time, so that no two branches change those files. People
sheets are rebuilt once by the lead after all worlds are merged.

| WP | Objective and work | Model | Accepted when |
|---|---|---|---|
| N2.1 | Selection open for the whole scene (`port.selection_open()`); one tap selects, the object reacts within a beat, the previous pick deselects, the pick commits at the next departure boundary; cap raised from 4 to 8; smallest target 88 px; touch region within the object's bounds plus 24 px | Opus (`hotspot_view.gd`, `run_hotspots.gd`, `hotspot_contract.gd`) | Interaction tests; the changed safety baseline is re-recorded on purpose with the difference written down |
| N2.2 | Router in the run: quest entry and return go through the port; entries are never rhythm-gated; returning lands on the hub scene the player came from; progress per quest in `user://story_run.json` under a versioned `narrative` key, written atomically | Sonnet, reviewed by the lead | The three routes pass on the real director; old saves load |
| N2.3 | Split the per-world tables of `tools/run/make_hotspots.py` (597 lines, every world in one file) so that world agents do not edit the same file | Sonnet | The generator output is byte-identical before and after the split |
| N2.4 | Content, one agent per location in parallel (Hospital, Mental Hospital, Alien Spaceship, Hell; then the Warehouse hub): four quest entrances in the hub scene as objects that belong to the place, at least one mainline exit, a way to the hub from the other scenes, so that every main-run scene has three choices that lead somewhere different. 20 new entrances (`LEAD_RULINGS.md`, ruling 15: 16 in the four new hubs, and on the Floor an ungated Dungeon hatch and three copies of the Balcony, Booth and Bar entrances). The hub-to-hub links between the paired locations (the default of decision 3) are added here | Sonnet, one worktree each | Validator: 20 of 20 cells; every quest within 5 choices of the start (target 1); three distinct destinations in all 36 main-run scenes; `check_hotspots.py` 0 errors |
| N2.5 | Return objects: one definition per quest placed by a default rule with per-scene override, in the 46 path scenes; a visible return in the Bassment | Sonnet | Every quest scene has a return; three choices in every path scene (onward, back, return) |
| N2.6 | Reactive objects (dancers, lights, props that answer a tap and lead nowhere) until the coverage audit passes, world by world | Sonnet, parallel by world | Coverage audit: 50% or more of the world in 80% or more of sampled frames; choices alone 25% or more; exceptions listed |
| N2.7 | People sheets are regenerated, never merged; `python tools/shrink_shots.py` before any new shot is committed | lead | Art build is its own commit |

Risk: this stage is mostly content, and it is the largest piece of the whole plan. Report C puts the gap at
about 8 times in area and 3 times in time. If reactive objects alone cannot reach 50% in a scene, the
fallback is a documented exception for that scene, not an invisible enlarged hit area.

Not in this stage, and said plainly: raising the Bassment's 62 passages with fewer than three choices, and
moving the wizard's mid-scene entrance behind the port. Both are a later, separately sized piece.

### Stage M2. DJ transitions (music stream, Opus; starts from the M1 merge, beside N2)

Everything happens behind the seam, in `src/music/**`, `src/transition/transition_director.gd`,
`src/run/run_audio.gd`, `src/track/**` and `content/music/transitions/**`. No edit to the files N2 owns.

| WP | Objective and work | Accepted when |
|---|---|---|
| M2.1 | Spike, time-boxed to one day: a second synchronised group for the tail; `pitch_scale` for small ratios; `AudioEffectPitchShift`; tails pre-rendered offline with ffmpeg; `AudioStreamInteractive`. The simplest that passes a listening test wins | A written verdict with CPU and memory figures on this PC |
| M2.2 | Sidecars `content/music/transitions/<track>.json`: `first_drop_s` (owner's value, snapped to the nearest bar of the pack's grid, snap distance reported), optional intro, outro, mix-in and mix-out bars, `no_blend`. A script prints the detected drop of every track as a sheet the owner corrects | 61 sidecars; a large snap distance is flagged as a wrong grid |
| M2.3 | The planner, a pure function from two tracks' metadata to a plan: `blend` (within 3%), `halftime_blend` (within 3% of 2:1), `echo_out` (larger differences such as 174 to 140), `cut` (always available, used when anything is missing) | Unit tests over all 61 by 61 pairs: every pair gets a mode; no pair crashes |
| M2.4 | The blend: the incoming track starts on the boundary's downbeat at its own tempo and becomes the clock; the outgoing tail fades stem by stem, drums and bass within 2 bars, and is silent at least 4 bars before the incoming drop; `completed` fires then; a limiter on the run bus | Tests on fixture packs: order of signals, fade ends before the drop, `song_time()` never decreases |
| M2.5 | Drift and hit windows: ten transitions in a row keep cue time and audio time within one mix chunk; a cue that falls inside a blend is judged against the incoming grid with the same window as anywhere else (a perfect bot scores perfect through every transition; an early and a late bot score as they do in mid-scene); missing metadata and unready audio fall back to `cut` | Tests on a virtual clock, and a measured run on real packs with the real audio driver |
| M2.6 | Listening builds for the owner: three pairs chosen to cover blend, half-time and echo-out | The owner's verdict |

### Stage X. Integration, phone, `main` (lead, with Sonnet for tests and Opus for polish)

| WP | Objective and work | Accepted when |
|---|---|---|
| X1 | Merge M2 and N2 into `feature/one-pc`; `test_port_real.gd` runs the 15 conformance cases on the real director | Green |
| X2 | The combined routes of the owner's brief, automated on real packs: navigation, saved state, choices available, the track changes, cues stay on the beat | 0 script errors; a table of routes and results |
| X3 | Full suite, `SCRIPT ERROR` count, `check_hotspots.py` for the main run and the three paths, importer tests, `tools/export_smoke.gd`, narrative validator, coverage audit | All green; counts written in the hand-over |
| X4 | Phone: a debug APK. Packs on the device need a small code change that no earlier package owns: packs are found only in `RW_TRACKS_DIR` or `user://track_packs`, and `user://` on Android is app-private, where `adb push` cannot write. The music stream adds a third place to look that `adb` can reach (the app's external files folder) and a script that pushes a chosen subset of packs (all 61 are several GB). Then latency, worst frame time and memory are measured on the phone. For the owner's own testing only: a build with these recordings cannot be given to anyone | Figures in the hand-over. Needs the owner's phone on USB |
| X5 | Visual polish (Opus): the 20 entrances (ruling 15), the selection feedback, the reactive objects | Before and after shots |
| X6 | Docs: `GAME_GUIDE.md`, `HANDOVER.md` section, `PICKUP.md`; worktrees and `wip/` branches removed | Written |
| X7 | The owner plays and listens, then says whether `feature/one-pc` is merged into `main` | The owner's word |

## 7. Rules for the lead and the agents

### 7.1 Git
- Agents commit only on their own `wip/` branch, with explicit paths (never `git add -A`), and never push,
  merge, rebase or reset. The lead merges.
- A checkpoint commit after every finished step.
- The lead pushes `feature/one-pc` at each milestone. Nobody pushes `main`.
- `docs/HANDOVER.md` is edited only by the lead at a merge. Agents write their report in their final message.
- Nothing derived from the recordings is ever staged. Before every merge the lead runs
  `git diff --stat <base>..<branch> -- '*.ogg' '*.wav' '*.mp3' '*.flac'` and expects only fixture files.

### 7.2 Godot and tests
- Godot runs only through `tools/dev/godot.sh` (stage 0.4), so that one runs at a time.
- `--import` once in every new worktree before any headless run.
- The runner prints `0 failures` even when a script failed to parse. Always count `SCRIPT ERROR` lines too.
- While working, run the files that matter with `--filter`. The full suite runs before a stream branch is
  offered for merging and again by the lead after the merge.
- The suite never depends on the packs on this machine: tests use the synthetic fixture packs only.
- A claim of "verified" states the checks, failures, script errors and minutes of the run that verified it.

### 7.3 Unattended running
- The lead does not rely on a background notification to move an unattended run forward (a laptop run sat
  idle for seven hours that way). Long jobs are scripts that write a log; the lead schedules its own check.
- The owner's stop rule for a long run is asked for at its start (the last one was "stop at 35% of the
  weekly usage").

## 8. Where the owner comes in

| When | What the owner does |
|---|---|
| Before stage 0 | Answers decision 1 of section 9 (moving the audio out of the checkout) |
| After stage D | Reads the folder's `README.md` and answers decisions 2 to 7 |
| After M1 | Plays a run with real tracks: are the charts right in the run, is the every-fourth-bar rest right, are scenes of 88 to 176 seconds the right length |
| During M2 | Corrects the sheet of first-drop times; listens to three transition pairs |
| After N2 | Plays for the feel of selection and the quest entrances |
| At X4 | Connects the phone |
| At X7 | Says whether it goes to `main` |

## 9. Open decisions for the owner

The plan carries a default for each so that work is not blocked; the default is used unless the owner says
otherwise.

| # | Decision | Default in this plan |
|---|---|---|
| 1 | Move `NewMusicTry5\{packs,ToAddTry4,planning}` out of the checkout to `C:\Users\joesa\rw-audio-work\`? | Yes. Until it is done, nothing is moved, and agents read the folder where it is |
| 2 | Do objects that react to a tap but lead nowhere count toward the 50%? | Yes |
| 3 | Should one run be able to reach all five locations, and should the story end? Today a run visits three of the five and never ends | Keep today's routes; add hub-to-hub links between the paired locations; no ending yet |
| 4 | Public names and framing of the Catch-22 and LOTR quests (the repository uses original names and no quotations) | Keep the original names |
| 5 | Should the wizard's mid-scene entrance to the Bassment stay as it is? | Yes, for now |
| 6 | Scene lengths and the every-fourth-bar rest | Decided by ear after M1 |
| 7 | May the planning inputs (`DECISIONS.md`, reports A to E; no audio) be committed to the public repository so that the documents can cite them? | No; the documents restate what they need |

Publication and licences, kept apart from the engineering: the 61 recordings are other artists' commercial
releases and cannot be distributed with a build without licences; the game can be developed and tested
with them on the owner's own devices only. The Jesus quest uses traditional biblical episodes. The
Catch-22 and LOTR quests are original-name stories that follow the shape of those books; whether that is
enough for publication is a question for someone qualified, before any release.

## 10. Risks

| Risk | Effect | Answer |
|---|---|---|
| CUDA build of the pinned versions does not install on Python 3.13 | Import delayed | Python 3.12, or nearest build, or CPU (stage I2) |
| Two Godot runs at once | Corrupt test results | The queue (0.4) |
| `run_play.gd` edited by both streams | Merge conflicts in a 1,781-line file | Ownership by time: music until M1, narrative after; the seam's hook points |
| The safety baseline (`test_run_tracks_safety`) against N2's routing changes | A red test that is not a defect | Re-record deliberately in N2.1 with the difference written down |
| Door timing in `run_journey.gd` against the length of a blend | The walk to the door ends before or after the music does | The plan's `blend_beats` is given to the narrative side in `locked`; visuals must work for `cut` |
| 50% coverage cannot be reached in some scenes | Target missed | Documented exceptions; never invisible hit areas |
| Nothing has been measured on a phone | Unknown latency, frame time and memory with packs | X4, and no claim before it |
| A restart of the PC | Lost agent work | `wip/` branches, checkpoint commits, sibling worktrees |
| `docs/shots` is 228 MiB | The repository grows | Shrink before commit; only shots that prove something |

## 11. Validation map

| The owner's brief asks | Where it is checked |
|---|---|
| Every quest within five choices of the start; every location offers every quest; every quest returns; no dead ends; references resolve; three choices everywhere | `tools/narrative/graph.py` (N1.1), `tests/test_narrative_*.gd` (N1.3) |
| Return restores the right place; re-entry keeps progress; state right after a failed or cancelled transition | `tests/test_narrative_*.gd`, `tests/port_conformance.gd` cases 3, 8, 10 |
| Selection changes with one tap, before the commit | `tests/test_interaction_*.gd` (N2.1), conformance case 2 |
| 50% of the world for 80% of frames; target sizes; no overlap with the pads | `tools/run/coverage_audit.gd` (N1.5, N2.6) |
| Grid, stems in sync, fades end before the drop, boundaries, hit windows, large tempo differences, drift, missing metadata | M1.4, M2.3, M2.4, M2.5 |
| Combined routes | N1.6 on the mock, X2 on real packs |
| By eye and by ear only | Section 8 |
| Android | X4 |
