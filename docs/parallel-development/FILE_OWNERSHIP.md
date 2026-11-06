# File ownership for the two streams

Status: planning document, written 6 November 2026 for two machines and re-worded the same day for one PC (`ONE_PC_PLAN.md` sections 4 and 5). It is the rulebook that stops the music stream and the narrative stream editing the same files. It follows the lead's decisions file `DECISIONS.md` (outside the repository; its numbers D0, D1, D2 and D3 to D5 are used below), `INTEGRATION_CONTRACT.md` and `ONE_PC_PLAN.md`. Where a file is not named in DECISIONS.md, this document assigns it and lists the assignment in the final section.

Names used throughout:

| Short name | Meaning |
|---|---|
| Music stream (M) | The subagents that do the music work, each in a sibling worktree `C:\Users\joesa\Documents\Cursor\MusicGame-<name>` on a `wip/` branch (`wip/import`, `wip/doc-music`, `wip/music-m1`, `wip/music-m2`). Formerly "Windows" |
| Narrative stream (N) | The subagents that do the narrative and interaction work, on `wip/doc-graph`, `wip/doc-interaction`, `wip/narr-n1`, `wip/narr-n2-<world>`. Formerly "Ubuntu" |
| Lead | The one lead session (Fable). It merges the `wip/` branches into `feature/one-pc` with `--no-ff`, pushes it at each milestone, and is the only one who changes frozen files |
| Baseline | The plan commit on `feature/one-pc-plan` (a child of `90a42877`), from which `feature/one-pc` is created. A `wip/` branch starts from `feature/one-pc` |
| M1 | Milestone "track scenes finished and the transition seam installed": the lead merges the music stream's M1 branch into `feature/one-pc`, and the narrative stream's N2 worktrees start from that commit. Formerly W1 and the tag `w1-track-wiring` |

"Exists" in the matrix means the path is in `git ls-files` of the repository at the baseline (checked on the handover branch and on `feature/wizard-duel-lan`). "new" means no such path exists at the baseline; the named stream creates it.

---

## 1. The rules in one page

1. **Two phases.** Phase 1 is from the baseline until M1 is merged. Phase 2 is from the M1 merge onwards. Only the run files in rule 4 change hands at M1; everything else has one owner for the whole job.
2. **"Owns" means: only the owner's stream changes the file** (in its own worktree, on its own `wip/` branch). Changing includes editing, renaming, deleting, reformatting, regenerating, and letting a tool rewrite it. The other stream may read it, run it and depend on it. A file with no owner in the matrix is frozen for both streams.
3. **Frozen files** cannot be changed by either stream: `src/transition/transition_port.gd` (the byte copy made in stage 0.3), `project.godot`, `export_presets.cfg`, `docs/HANDOVER.md`, `README.md`, `docs/parallel-development/INTEGRATION_CONTRACT.md`, `docs/parallel-development/contract/**`, and the generated people sheets. Only the lead changes them (section 4).
4. **Time-sliced files.** Phase 1: the music stream owns `src/run/run_play.gd`, `src/run/run_engine.gd`, `src/run/run_data.gd`, `src/run/run_audio.gd`, `content/run/run.json`, and for stage M1 only also `src/run/run_hotspots.gd` and `src/run/run_journey.gd` (door state and door timing on open laps). The narrative stream does not edit them and works against the mock. Phase 2: the first, second, third and fifth of the first list, and the two M1 files, pass to the narrative stream. `src/run/run_audio.gd` stays with the music stream.
5. **Asking for a change in the other stream's file.** The agent reports the need to the lead in its final message: the file, the function or key, the change wanted, and why it cannot be done in a file it owns. The lead decides and assigns it, usually to the owning stream. Nobody applies a change by editing the other stream's file from their own worktree. There is no `requests/` folder.
6. **The contract file is copied and never edited.** The lead copied `docs/parallel-development/contract/transition_port.gd` and its `.gd.uid` byte for byte to `src/transition/` in stage 0.3. Verify with `cmp docs/parallel-development/contract/transition_port.gd src/transition/transition_port.gd`. Nobody edits the copy. A contract change is reported to the lead; only the lead amends the contract and `INTEGRATION_CONTRACT.md`, bumps `VERSION`, copies the file again and tells both streams.
7. **At M1 the lead merges, the narrative stream starts from the result.** The lead merges the music stream's M1 branch into `feature/one-pc` with `--no-ff`, runs the full suite, and creates the narrative stream's N2 worktrees from that commit (`ONE_PC_PLAN.md` section 6, gates). The narrative stream's N1 branch has no file in common with M1, so the order of those two merges does not matter. The narrative stream has not touched any music-owned file in phase 1, so the merge should be clean; any conflict is a breach of this document and goes to the lead. Later music-stream work (M2) reaches the narrative stream only through the lead's merges of `feature/one-pc`.
8. **No agent pushes, merges, rebases or resets.** Agents commit only on their own `wip/` branch, with explicit paths, and a checkpoint commit after every finished step. The lead merges into `feature/one-pc`, pushes it at each milestone, and never pushes `main`. Agents write their report in their final message; `docs/HANDOVER.md` is edited only by the lead at a merge (`ONE_PC_PLAN.md` section 7.1). There are no per-stream handover files.
9. **Never `git add -A` or `git add .`.** `NewMusic/` and `NewMusicTry5/` (the owner's audio drops, in the owner's checkout) and any `ToAddTry*/` folder must stay out of commits; stage 0.2 adds the first two to `.git/info/exclude`, which every worktree shares. Stage by explicit path.
10. **Before every merge offer** run the checklist in section 7.

---

## 2. The ownership matrix

Owner column values: **M** = music stream, **N** = narrative stream, **none** = frozen for both (the lead changes it, or an agent reports the need to the lead), **M then N** = music stream until M1, narrative stream after.

Globs: `*` matches within one folder, `**` matches any depth.

### 2.1 Source: `src/`

| Path or glob | Exists or new | Owner before M1 | Owner after M1 | Notes |
|---|---|---|---|---|
| `src/run/run_play.gd` | exists | M | N | Time-sliced (D2). The seam hooks are added by the music stream in M1. See section 3. |
| `src/run/run_play.tscn` | exists | M | N | Goes with `run_play.gd`. |
| `src/run/run_engine.gd` | exists | M | N | Time-sliced. See section 3. |
| `src/run/run_data.gd` | exists | M | N | Time-sliced. See section 3. |
| `src/run/run_audio.gd` | exists | M | M | Music transport. Stays with the music stream throughout (D2). |
| `src/run/run_track_plan.gd` | exists | M | M | Track scene planning (D2: `src/run/run_track_*.gd`). |
| `src/run/run_track_scenes.gd` | exists | M | M | Same. Its static `enabled` flag is read by the test runner; do not change its behaviour under the runner. |
| `src/run/run_track_*.gd` (further files) | new | M | M | Any new file with this prefix is the music stream's. |
| `src/run/run_hotspots.gd` | exists | M | N | D2 gives it to the narrative stream; the plan lends it to the music stream for M1 only (door state on open laps). The narrative stream does not touch it until M1 is merged. |
| `src/run/hotspot_view.gd` | exists | N | N | D2. |
| `src/run/hotspot_contract.gd` | exists | N | N | D2. Route prefixes (`trial:`, `path:`, `run:`) live here; new quest route kinds go here. |
| `src/run/run_journey.gd` | exists | M | N | D2 gives it to the narrative stream; the plan lends it to the music stream for M1 only (door timing on open laps). The door-walk constants `DOOR_BEATS` and `CLOSE_BEATS` are in `run_passage.gd` (narrative stream's); the music stream reports to the lead if a blend needs different timing. |
| `src/run/run_progress.gd` | exists | N | N | The save (`user://story_run.json`); D2 gives the narrative stream "the save format". |
| `src/run/run_rail.gd`, `src/run/run_passage.gd`, `src/run/run_passage_view.gd` | exists | N | N | Camera rail and passages: routing and visuals (finding D). |
| `src/run/choice_staging.gd`, `src/run/choice_props.gd`, `src/run/run_acting.gd` | exists | N | N | Choice visuals and acting. |
| `src/run/run_hud.gd`, `src/run/run_levels.gd`, `src/run/run_levels.tscn`, `src/run/run_over.gd`, `src/run/run_over.tscn`, `src/run/dev_text.gd` | exists | N | N | Run interface. |
| `src/run/run_card_table.gd`, `src/run/run_minigame_host.gd`, `src/run/run_wallet.gd` | exists | none | none | Blackjack and wallet; neither task needs them. Report to the lead if a change is unavoidable. |
| `src/transition/transition_port.gd` and its `.gd.uid` | new (copied in stage 0.3; exists on `feature/one-pc`) | none | none | Byte copy of the contract, made by the lead. See section 3. |
| `src/transition/transition_director.gd` and any other `src/transition/**` file | new | M | M | `TransitionDirector extends TransitionPort`. |
| `src/music/**` | new | M | M | Adaptive music transport and planner. |
| `src/narrative/**` | new | N | N | `NarrativeGraph`, `QuestRouter`, `RouteState`. |
| `src/track/**` (`track_*.gd`, `track_play.tscn`, `README.md`) | exists | M | M | D2. `src/track/README.md` has hard-coded paths the music stream may fix (section 8). |
| `src/audio/stem_transport.gd` | exists | M | M | Stem playback. |
| `src/audio/battle_sfx.gd` | exists | none | none | Battle effects; unrelated to both tasks. |
| `src/core/song_clock.gd` | exists | M | M | The clock. `song_time()` must stay continuous (D5). |
| `src/core/session.gd` | exists | N | N | Autoload `Session`. The narrative stream owns `Session.run_progress` and the save (D2). The music stream needs nothing from it: music code never reads the save (contract section 1). |
| `src/duel/duel_network.gd` | exists | none | none | Autoload `DuelNetwork`; neither task touches it. |
| `src/duel/**` (other files) | exists | none | none | Wizard duel. |
| `src/trial/**` (`trial_*.gd`, `trial_play.tscn`) | exists | N | N | The Bassment (D2). |
| `src/core/**` (other files), `src/input/**`, `src/sim/**`, `src/ui/**`, `src/scenes/**`, `src/minigames/**`, `src/debug/**` | exists | none | none | Legacy battle game, menus, minigames, debug overlay. Unassigned by DECISIONS.md; frozen. |
| `src/story/**` | exists | none | none | Legacy chapter campaign. Frozen. |
| `*.gd.uid` for any file above | exists / new | follows the `.gd` | follows the `.gd` | The stream that creates a script commits its `.uid`. The five `.uid` files that the first import on this PC created and the handover branch lacked were committed by the lead in stage 0.3. |

### 2.2 Content and data

| Path or glob | Exists or new | Owner before M1 | Owner after M1 | Notes |
|---|---|---|---|---|
| `content/run/run.json` | exists | M | N | Time-sliced. Key by key rules in section 3. |
| `content/run/track_scenes.json` | exists | M | M | Track per scene (D2). |
| `content/run/hotspots/*.json` (`warehouse`, `hospital`, `hospital_late`, `ward`, `ward_late`, `mothership`, `underworld`) | exists | N | N | Hotspot data. |
| `content/run/choice_staging.json` | exists | N | N | |
| `content/music/arrangements/**` | exists | M | M | Loop arrangements (D2: `content/music/**`). |
| `content/music/catalogue.json`, `content/music/mix_recipes.json`, `content/music/palettes.json` | exists | M | M | |
| `content/music/tracks/**` (`catalogue.json`, `ac13_shostakovich.json`, `acuna_go_back.json`) | exists | M | M | Metadata only, never audio. `catalogue.json` line 9 has a Linux path the music stream may fix. |
| `content/music/transitions/**` (`<track id>.json`) | new | M | M | Per-track sidecars (D5). |
| `content/narrative/**` (`graph.json` and any overlay files) | new | N | N | Format `rhythm_warfare.narrative.v1` (D3). |
| `content/paths/**` (`ember/`, `gospel/`, `squadron/`, `stub/`: `run.json`, `music.json`, `walks.json`, `prompts.json`) | exists | N | N | D2. The `music.json` files are music data inside the narrative stream's folder; the music stream reads them and reports a needed change to the lead. |
| `content/trial/**` (`passages.json`, `hotspots.json`, `layout/*.json`) | exists | N | N | D2. |
| `content/story/music.json` | exists | M | M | Recorded-music table. |
| `content/story/**` (other files, `maps/**`) | exists | none | none | Legacy chapters. |
| `content/library/**`, `content/missions/**`, `content/missions_legacy/**`, `content/fixtures/**`, `content/duel/**`, `content/minigames/**`, `content/sounds.json`, `content/build_state.json`, `content/README.md`, `content/REPORT.md` | exists | none | none | Legacy loop library, missions, duel, blackjack. `content/imports/` is in `.gitignore` but twelve files are tracked there; frozen. |
| `songs/**` | exists | M | M | Recorded loop packs the run plays; the music stream's audio. `songs/*/audio/*.wav` is ignored and stays out of Git. |
| `data/**`, `campaign/**`, `midi_export/**`, `pixelexample/**`, `ToAddTry1/**`, `Rhythm_Warfare_Level_01_MIDI.zip` | exists | none | none | Legacy. |

### 2.3 Tools

| Path or glob | Exists or new | Owner before M1 | Owner after M1 | Notes |
|---|---|---|---|---|
| `tools/audio_import/**` | exists | M | M | D2. Stage I1 (merged from `wip/import`) made it run on Windows and the GPU; the paths still hard-coded are in section 8. |
| `tools/run/coverage_audit.gd`, `tools/run/coverage_audit.py` (and `tools/run/coverage_audit.*`) | new | N | N | D2/D4. |
| `tools/run/check_hotspots.py` | exists | N | N | D2. |
| `tools/run/measure_mix.py` | exists | M | M | Mix measurement; audio. Assigned here. |
| `tools/run/transition_*` | new | M | M | Any music-stream measuring tool for transitions. |
| `tools/run/**` (every other existing file: `check_path.gd`, `choice_audit.gd`, `choice_audit.py`, `make_hotspots.py`, `make_scenes.py`, `walk_run.sh`, `capture*.sh`, `laps*.py`/`.gd`, `acting_*.py`, and so on) | exists | N | N | Routing, hotspot and art builders. Assigned here. |
| `tools/narrative/**` (`graph.py`, tests) | new | N | N | D3. |
| `tools/story/check_run_audio.py`, `tools/story/check_music.py`, `tools/story/record_music.gd` | exists | M | M | Audio checks. Assigned here. |
| `tools/trial/check_trial_audio.py`, `tools/trial/check_transition_audio.py` | exists | M | M | Audio checks. Assigned here. |
| `tools/trial/**` (other files), `tools/paths/**` | exists | N | N | Bassment and path builders. |
| `tools/test.sh` | exists | none | none | Shared runner. Defaults to the Godot 4.5.1 console exe in Downloads. Neither stream edits it; the lead changes it in stage 0.4 (a `GODOT_RUN` variable so that each Godot start goes through `tools/dev/godot.sh`). |
| `tools/dev/godot.sh` | exists (stage 0.4; on the branch) | none | none | The Godot queue wrapper: one Godot at a time, because every worktree shares one `user://` folder. Written by the lead. Every Godot start goes through it. |
| `tools/content/**` | exists | none | none | Python content tools and their tests, used by `tools/test.sh`. A stream that needs a change reports it to the lead. Both streams run them read-only. |
| `tools/story/**` (other files, `tools/story/art/**`) | exists | none | none | Art builders; they regenerate committed sheets. Do not run them. |
| `tools/campaign/**`, `tools/duel/**`, `tools/minigames/**`, `tools/autoplay.gd`, `tools/balance*.py`, `tools/balance.sh`, `tools/export_smoke.gd`, `tools/probe.gd`, `tools/shoot.gd`, `tools/shrink_shots.py`, `tools/make_song_pack.py`, `tools/pck_*.py`, `tools/extract_openra*.py`, `tools/import_openra_assets.py`, `tools/test_extract_openra_sounds.py` | exists | none | none | Shared or legacy tooling. Run, do not edit. `tools/export_smoke.gd` belongs to the lead. |

### 2.4 Tests

The runner only runs `tests/test_*.gd` (except `test_case.gd`), so file names are the ownership key. See section 5 for the rules.

| Path or glob | Exists or new | Owner before M1 | Owner after M1 | Notes |
|---|---|---|---|---|
| `tests/test_run_audio_polish.gd`, `tests/test_run_audio_sections.gd`, `tests/test_run_tracks_data.gd`, `tests/test_run_tracks_engine.gd`, `tests/test_run_tracks_plan.gd`, `tests/test_run_tracks_safety.gd` | exists | M | M | Audio and track scenes. `test_run_tracks_safety.gd` compares against `tests/fixtures/track_scenes/baseline_runs.json`; see section 5. |
| `tests/test_track_game.gd`, `tests/test_track_loader.gd`, `tests/test_track_scene.gd`, `tests/test_track_transport.gd`, `tests/test_transport.gd`, `tests/track_test_kit.gd` | exists | M | M | Track mode and transports. |
| `tests/test_story_music_packs.gd`, `tests/test_story_recorded_music.gd`, `tests/test_miss_mute.gd` | exists | M | M | Recorded music and stem muting. Assigned here. |
| `tests/test_run_engine.gd`, `tests/test_run_laps.gd`, `tests/test_run_lock.gd`, `tests/test_run_matrix.gd`, `tests/test_run_scene.gd` | exists | M | N | They test the time-sliced files, so they follow them. |
| `tests/test_hotspots_any_window.gd`, `tests/test_hotspots_data.gd`, `tests/test_hotspots_engine.gd`, `tests/test_hotspots_scene.gd`, `tests/test_hotspots_view.gd`, `tests/test_choice_clarity.gd` | exists | N | N | Interaction. |
| `tests/test_run_paths.gd`, `tests/test_run_ember.gd`, `tests/test_run_squadron.gd`, `tests/test_gospel.gd`, `tests/test_run_progress.gd`, `tests/test_run_rail.gd`, `tests/test_run_rail_scene.gd`, `tests/test_run_cast.gd`, `tests/test_run_hud_silent.gd`, `tests/test_run_home.gd`, `tests/test_trial.gd` | exists | N | N | Paths, progress, rail, cast, HUD, home, Bassment. |
| `tests/test_narrative_*.gd` | new | N | N | D2 pattern. |
| `tests/test_interaction_*.gd` | new | N | N | D2 pattern. |
| `tests/test_port_mock.gd` | new (written in N1.4) | N | N | Runs the conformance cases on the mock (contract section 9). |
| `tests/port_conformance.gd` | new (written in N1.4) | N | N | D2. Not named `test_*`, so the runner does not run it directly. |
| `tests/mocks/**` (`mock_transition_director.gd`) | new (written in N1.4) | N | N | D2. |
| `tests/test_transition_*.gd`, `tests/test_music_*.gd`, `tests/test_director_*.gd` | new | M | M | The music stream's new patterns. These three prefixes are reserved for it. |
| `tests/test_port_real.gd` | new | none | none | The lead only, at stage X1: runs `port_conformance.gd` on the real director (contract section 9). |
| `tests/run_tests.gd`, `tests/test_case.gd` | exists | none | none | Test harness. |
| `tests/fixtures/track_fixture/**`, `tests/fixtures/track_scenes/**`, `tests/fixtures/transport/**` | exists | M | M | Synthetic pack, baseline recorder, transport audio. |
| `tests/fixtures/transition/**` | new | M | M | The music stream's new fixtures. |
| `tests/fixtures/narrative/**` | new | N | N | The narrative stream's new fixtures. |
| `tests/fixtures/save_v2.json` | exists | N | N | A save-format fixture. |
| `tests/fixtures/library_fixture/**`, `tests/fixtures/pack_v4/**`, `tests/fixtures/village_test.json`, `tests/fixtures/fake_minigame.gd`, `tests/fixtures/fake_minigame_view.gd`, `tests/fixtures/make_library_fixture.py` | exists | none | none | Legacy fixtures. |
| every other existing `tests/test_*.gd` (`test_all_missions`, `test_battle`, `test_battle_sfx`, `test_blackjack_*`, `test_campaign`, `test_civilian_art`, `test_duel`, `test_judge`, `test_level_loader`, `test_library_index`, `test_loadout*`, `test_match`, `test_minigame_*`, `test_mission*`, `test_money_*`, `test_note_lane`, `test_pad_judge`, `test_playtest`, `test_rewards`, `test_roster`, `test_scenes`, `test_section_input`, `test_sequences`, `test_story_*` other than the two above, `test_village_sim`, `test_wallet`) | exists | none | none | Legacy. Run them; if one fails because of your change, fix your change. |

### 2.5 Assets, project files, documents

| Path or glob | Exists or new | Owner before M1 | Owner after M1 | Notes |
|---|---|---|---|---|
| `assets/story/**` scene art (backgrounds, props, objects) | exists | N | N | D2: "scene art under `assets/`". New entrance and return objects go here. |
| `assets/story/*/people/**` (generated people sheets, `page_N.png` and `.import`) | exists | none | none | Frozen for both. See section 3 and section 6. |
| `assets/run/choice/**`, `assets/trial/art/**` | exists | N | N | Choice and Bassment art. |
| `assets/minigames/blackjack/**` | exists | none | none | |
| `assets/audio/**` or any new audio asset folder | new | M | M | Only if a small synthetic test sound is needed; no third-party audio (section 6). |
| `project.godot` | exists | none | none | Section 3. |
| `export_presets.cfg` | exists | none | none | Section 3. |
| `icon.svg`, `icon.svg.import` | exists | none | none | |
| `.gitignore`, `.gitattributes` | exists | none | none | Changed only at integration. |
| `README.md` | exists | none | none | Section 3. |
| `docs/HANDOVER.md` | exists | none | none | Section 3. |
| `docs/parallel-development/graph/narrative_graph.json` and the Mermaid export | new | N | N | Output of `tools/narrative/graph.py` (D3). |
| `docs/parallel-development/INTEGRATION_CONTRACT.md`, `docs/parallel-development/contract/**`, `docs/parallel-development/FILE_OWNERSHIP.md` and the other planning documents | exists | none | none | Frozen from the baseline; only the lead changes them. |
| `docs/TRACK_SCENES_HANDOVER.md` | exists (tracked on the handover branch) | M | M | The M1 brief. |
| `docs/RUN_TRACK_SCENES.md`, `docs/TRACK_ASSIGNMENT.md`, `docs/TRACK_PACK_FORMAT.md`, `docs/MUSIC_CATALOGUE.md`, `docs/MUSIC_HANDOFF.md`, `docs/MUSIC_IMPORT.md`, `docs/MUSIC_LIBRARY_PLAN.md`, `docs/MUSIC_REPORT.md`, `docs/MUSIC_TRACKS.md`, `docs/MusicImportPlan.md`, `docs/TIMING.md`, `docs/RUN_DUNGEON_MUSIC_PLAN.md` | exists | M | M | Music documents. Assigned here. |
| `docs/CHOICE_CLARITY.md`, `docs/VisualChoicePlan.md`, `docs/VISUAL_COVERAGE.md`, `docs/CONTINUOUS_RUN.md`, `docs/TRIAL_OPENING.md`, `docs/choice/**`, `docs/paths/**` | exists | N | N | Routing and interaction documents. Assigned here. |
| `docs/music/**` | new | M | M | Any further music-stream design note. |
| `docs/narrative/**` | new | N | N | Any further narrative-stream design note. |
| `docs/shots/**` | exists | none | none | Screenshots; any new screenshot goes into the stream's own subfolder `docs/shots/music/` or `docs/shots/narrative/` (new) and is run through `tools/shrink_shots.py` first. |
| every other existing file under `docs/` | exists | none | none | Legacy documents. |

---

## 3. Files that cannot be modified independently

| File | Why | Procedure |
|---|---|---|
| `src/transition/transition_port.gd` | It is the contract as code. Two edits would silently split the interface. Both streams need it before M1 (the music stream for the director, the narrative stream for the mock). | The lead copied the file and its `transition_port.gd.uid` to `src/transition/` as the first commit of `feature/one-pc` (stage 0.3) and checked it with `cmp`. Every worktree then has the one copy with the one `.uid`, so no stream commits either. Any change is reported to the lead and made by the lead only (rule 6). |
| `project.godot` | One shared `[autoload]` block (`Session`, `DuelNetwork`) and display and input settings. Both contract and D2 forbid a new autoload or global. Cold file, so conflicts are certain if touched twice. | Neither stream edits it. A need (new input action, autoload, setting) is reported to the lead, who decides (section 4). Godot may rewrite it when the editor opens the project; always `git checkout -- project.godot` before staging if `git diff --name-only` shows it. |
| `export_presets.cfg` | Holds the owner's Windows keystore path at line 65 and the Android and Windows presets. | Neither stream edits it. Never run an export from a stream's worktree. The lead (stage X4, the phone build) only. |
| `content/run/run.json` | 113 KB with 36 nodes and 141 cinematics inline; JSON conflicts line by line even when the sections differ. Time-sliced (D2). | Phase 1 (music stream): only these top-level keys may change, and only if the track scenes work needs it: `energy` (including `energy.track`), `mix`, `stages`, `effects`, `treatments`, `timing`, `judgement`. It must not touch `worlds`, `start_node`, `nodes`, `cinematics`. Phase 2 (narrative stream): `worlds`, `start_node`, `nodes`, `cinematics` only, plus a hotspot reference if needed. The keys `energy`, `mix`, `stages`, `effects`, `treatments`, `timing`, `judgement` are then read-only for the narrative stream and a needed change is reported to the lead, who has the music stream make it, in a new file under `content/music/transitions/` or `content/music/` where possible. In stage N2 the world agents do not edit this file at all: their changes to `content/run/run.json` and `content/narrative/graph.json` are delivered as a short list in the agent's report and applied by the lead, one world at a time (`ONE_PC_PLAN.md` section 6, stage N2). New data does not go into `run.json` at all (narrative overlay in `content/narrative/`, music transition data in `content/music/transitions/`). Nobody reformats the file: keep key order and indent; any diff that touches a line you did not mean to change is reverted. |
| `src/run/run_play.gd` | 1781 lines, one class; audio and routing code share functions (`_ready`, `_handle`, `_open_routes`, `_path_swap`, `_on_phase_start`). | Phase 1: music stream only. In M1 it installs the hook points (listed in its report with function names and line ranges, and in `MUSIC_TRANSITIONS.md` section 12) so that later music work needs no further edits. After M1: narrative stream only. The music stream reports any further change it needs to the lead; the report names the function and the exact lines to add. |
| `src/run/run_engine.gd` | 906 lines; `_commit`, `_enter`, `_decide` interleave track and routing branches. | Same as `run_play.gd`. The music stream adds the engine events and the `request`-facing API in M1 as new functions in a new region at the end of the file; the narrative stream does not rewrite those after M1, only calls them. |
| `src/run/run_data.gd` | `load_files` must end with `RunTrackScenes.attach(d)`; narrative loading also lives here. | Phase 1: music stream only. After M1: narrative stream only, and `RunTrackScenes.attach(d)` stays the last call in `load_files`. Narrative graph loading is added as a separate call that does not reorder existing ones. |
| `docs/HANDOVER.md` | Append-only log that conflicted at every merge. | No agent edits it (D0). Each agent writes its report in its final message. The lead edits it at a merge (`ONE_PC_PLAN.md` section 7.1). |
| `README.md` | Public description; the open decisions for the owner (D7) are listed there. | No agent edits it. The lead only, at integration. |
| Generated people sheets (`assets/story/*/people/**`, `page_N.png` and `page_N.png.import`) | Committed output of art builders; binary, so any double change conflicts and cannot be merged. | Neither stream runs `tools/story/figure_sheets.py`, `face_sheets.py`, `build_assets.py`, `build_gospel_art.py`, `build_ember.py` or `tools/story/art/**`. If a sheet must change, the lead regenerates the sheets once after all worlds are merged (stage N2.7), as a separate commit; never merge two versions. If a script is run by accident, `git checkout -- assets/` before staging. |

---

## 4. Integration-only changes

Done only by the lead, in stage X of the plan and at the earlier milestone merges, on `feature/one-pc`, after both streams' branches are finished and their reports read. `main` is not touched until the suite is green and the owner says so.

| Change | Detail |
|---|---|
| Merge the streams | Merge each finished `wip/` branch into `feature/one-pc` with `--no-ff` and a merge commit that says what it brings; at stage X1 merge M2 and N2 (the narrative stream's N2 worktrees already contain the M1 merge). Resolve conflicts using the agents' reports. |
| Wire the real director in place of the mock | Replace `MockTransitionDirector` by `TransitionDirector` in the run scene's construction; add `tests/test_port_real.gd` running `tests/port_conformance.gd` on the real director with a virtual clock; keep the mock for the unit tests. |
| `project.godot` | Any input action, autoload or setting either stream reported a need for. Normally none. |
| `export_presets.cfg`, `.gitignore`, `.gitattributes` | Keystore path, preset changes, new ignore rules. |
| `README.md` and `docs/HANDOVER.md` | New sections for both streams; the owner's open decisions from D7. |
| `tools/test.sh`, `tools/content/**`, `tools/export_smoke.gd` | Any change to the shared runner, and `-s tools/export_smoke.gd` after the merge. |
| Generated people sheets | Regenerated once, as their own commit, if needed (N2.7). |
| Contract changes | Amend `contract/transition_port.gd` and `INTEGRATION_CONTRACT.md`, bump `VERSION`, copy the file to `src/transition/` again, tell both streams. |
| Final checks | Full suite, `SCRIPT ERROR` count, `python tools/run/check_hotspots.py` for main and each path, `python tools/narrative/graph.py` validation, `python -m unittest discover -s tools/audio_import`, and an export smoke test. |

---

## 5. Tests: names, who changes what

1. **Names decide ownership.** The music stream creates only `tests/test_transition_*.gd`, `tests/test_music_*.gd`, `tests/test_director_*.gd`, `tests/fixtures/transition/**`, and Python tests beside its tools (`tools/audio_import/test_*.py`). The narrative stream creates only `tests/test_narrative_*.gd`, `tests/test_interaction_*.gd`, `tests/test_port_mock.gd`, `tests/port_conformance.gd`, `tests/mocks/**`, `tests/fixtures/narrative/**`, and Python tests beside its tools (`tools/narrative/test_*.py`). Any new test file that fits neither list takes a prefix from the creator's list; if none fits, the agent reports it to the lead.
2. **Only the owner of a test file may change its assertions**, and never to make a failure pass. An assertion is changed only when the behaviour it checks was deliberately changed by the owner, and the commit message says what behaviour changed and why. Deleting or weakening an assertion to silence a failure is not allowed on either stream.
3. **A failing test the other stream owns** is a defect in your change until proved otherwise. Fix your change. If the test itself is wrong, report it to the lead; the lead decides.
4. **Time-sliced tests** (`test_run_engine`, `test_run_laps`, `test_run_lock`, `test_run_matrix`, `test_run_scene`) follow the run files: the music stream before M1, the narrative stream after.
5. **The baseline recording.** `tests/test_run_tracks_safety.gd` compares today's behaviour against `tests/fixtures/track_scenes/baseline_runs.json`. The narrative stream's routing changes may legitimately alter it. In stage N2.1 it is re-recorded on purpose (`record_baseline.gd`), with the difference written down in the report, and the lead reviews that diff; otherwise a difference is a defect.
6. **The track scenes switch.** Track scenes are off under the test runner unless a test sets the static `RunTrackScenes.enabled`; tests that do must reset it. Neither stream changes that mechanism without the lead's say.
7. **Full suite before a branch is offered for merging:** every Godot start goes through `tools/dev/godot.sh` (one Godot at a time; `--filter` runs while working, a full suite only when the lead schedules it). `bash tools/test.sh`, plus the same run's `SCRIPT ERROR` count, which must be 0 (the runner prints "0 failures" even when a script fails to parse). Put the counts and the minutes in the report.

---

## 6. Metadata and generated assets

| Kind | Where it lives | In Git? | Who regenerates |
|---|---|---|---|
| Track packs (stems, audio from the recordings) | outside the repository: `C:\Users\joesa\rw-audio-work\packs`, made and kept on this PC; the game finds them through `RW_TRACKS_DIR`, else `user://track_packs`. `RW_TRACKS_DIR` is not set machine-wide: only the music stream's own commands set it until M1 is merged, and every other run uses `RW_RUN_TRACKS=0` | **Never.** Public repository, third-party releases. | This PC, with `tools/audio_import` (stage I, no model in the loop). |
| Anything derived from the recordings (stems, separated audio, charts as pack files, waveforms, previews, rendered or stretched tails, pitch-shifted files, caches) | outside the repository: `rw-audio-work\cache`, `user://` or a folder named by an `RW_*` variable | **Never.** The same rule as the packs. Before every merge the lead runs `git diff --stat <base>..<branch> -- '*.ogg' '*.wav' '*.mp3' '*.flac'` and expects only fixture files. | Whoever needs them, locally. |
| Track metadata (`content/music/tracks/*.json`, `content/music/transitions/<id>.json`) | repository | Yes, text only. | The music stream. |
| Synthetic test packs | `tests/fixtures/track_fixture/**` | Yes (small, synthetic). | The music stream, with `make_fixture.py`. |
| Narrative overlay and exports | `content/narrative/**`, `docs/parallel-development/graph/**` | Yes. | The narrative stream, with `tools/narrative/graph.py`. |
| `.godot/` | each worktree | No (`.gitignore`). Run `--import` once in every new worktree before any headless run; `tools/test.sh` does it. | Godot. |
| `.import` files | beside the assets (7,411 tracked) | **Yes**, as the repository has it. Do not hand-edit. | Godot, when it imports a new asset; the stream that adds the asset commits its `.import`. If an `.import` of an untouched asset shows as changed, revert it. |
| `.uid` files (263 tracked on this branch, one per `.gd` and some tools) | beside each script | **Yes.** | The stream that creates the script commits its `.uid`. A new script without its `.uid` committed is incomplete. Never commit a `.uid` for the other stream's script. |
| `build/`, `*.tmp`, `__pycache__/`, `songs/*/audio/*.wav`, `content/library/*/placeholder/`, `*.asd`, `midi_export/**/*.wav`, `/audition/`, `content/imports/` | | No (`.gitignore`). | |
| Generated people sheets | `assets/story/*/people/**` | Yes (committed output); frozen. | The lead only (N2.7). |
| Screenshots | `docs/shots/music/` or `docs/shots/narrative/` | Yes, shrunk with `tools/shrink_shots.py` first (`docs/shots` is 228 MiB already). | The stream that took them. |
| `user://story_run.json`, `user://track_packs` | the machine's user folder | No. | The game. |

Do not commit `NewMusic/`, `NewMusicTry5/` or any `ToAddTry*/` folder: they are untracked owner drops with recordings (the first two are in `.git/info/exclude` from stage 0.2).

---

## 7. Checklist before a branch is offered for merging

1. `git status --short` shows nothing unexpected; no `NewMusic*`, no `ToAddTry*`, no audio, no `.godot/`.
2. `git diff --name-only --no-renames BASE...HEAD` is compared against your allowed globs (snippet below). `BASE` is the commit your `wip/` branch was created from. Every name must match, with the phase rule applied. Any name that does not match is reverted (`git checkout BASE -- <file>`) or reported to the lead.
3. `cmp docs/parallel-development/contract/transition_port.gd src/transition/transition_port.gd` is silent.
4. Full suite, `SCRIPT ERROR` count 0, the tool checks for your stream (section 5 point 7, and `check_hotspots.py` for the narrative stream, `python -m unittest discover -s tools/audio_import` for the music stream).
5. Your report (the final message) says what changed, the counts and minutes of the run that verified it, and what you did not verify.
6. Commit on your own `wip/` branch with explicit paths. Do not push, merge, rebase or reset; the lead merges.

Suggested snippet (bash; in the patterns `*` also matches `/`, so `a/*` means everything below `a/`). Set `SIDE`, `PHASE` and `BASE` once.

```bash
#!/usr/bin/env bash
# usage: SIDE=music|narrative PHASE=1|2 BASE=<commit the wip branch was created from> bash check_scope.sh
set -u
common_m=(
  'src/run/run_audio.gd*' 'src/run/run_track_*' 'src/track/*' 'src/audio/stem_transport.gd*'
  'src/core/song_clock.gd*' 'src/transition/*' 'src/music/*'
  'content/run/track_scenes.json' 'content/music/*' 'content/story/music.json' 'songs/*'
  'tools/audio_import/*' 'tools/run/measure_mix.py' 'tools/run/transition_*'
  'tools/story/check_run_audio.py' 'tools/story/check_music.py' 'tools/story/record_music.gd*'
  'tools/trial/check_trial_audio.py' 'tools/trial/check_transition_audio.py'
  'tests/test_run_audio_*' 'tests/test_run_tracks_*' 'tests/test_track_*' 'tests/test_transport.gd*'
  'tests/track_test_kit.gd*' 'tests/test_story_music_packs.gd*' 'tests/test_story_recorded_music.gd*'
  'tests/test_miss_mute.gd*' 'tests/test_transition_*' 'tests/test_music_*' 'tests/test_director_*'
  'tests/fixtures/track_fixture/*' 'tests/fixtures/track_scenes/*' 'tests/fixtures/transport/*'
  'tests/fixtures/transition/*' 'assets/audio/*'
  'docs/TRACK_*' 'docs/RUN_TRACK_SCENES.md' 'docs/MUSIC_*' 'docs/MusicImportPlan.md' 'docs/TIMING.md'
  'docs/RUN_DUNGEON_MUSIC_PLAN.md' 'docs/music/*' 'docs/shots/music/*'
)
# phase 1 only: the run files, and (stage M1 only) the two files lent by the narrative stream
phase1_m=( 'src/run/run_play.gd*' 'src/run/run_play.tscn' 'src/run/run_engine.gd*' 'src/run/run_data.gd*'
  'src/run/run_hotspots.gd*' 'src/run/run_journey.gd*'
  'content/run/run.json' 'tests/test_run_engine.gd*' 'tests/test_run_laps.gd*' 'tests/test_run_lock.gd*'
  'tests/test_run_matrix.gd*' 'tests/test_run_scene.gd*' )
common_n=(
  'src/narrative/*' 'src/trial/*' 'src/core/session.gd*' 'src/run/hotspot_*'
  'src/run/run_progress.gd*' 'src/run/run_rail.gd*' 'src/run/run_passage*'
  'src/run/choice_*' 'src/run/run_acting.gd*' 'src/run/run_hud.gd*' 'src/run/run_levels.*'
  'src/run/run_over.*' 'src/run/dev_text.gd*'
  'content/narrative/*' 'content/paths/*' 'content/trial/*' 'content/run/hotspots/*' 'content/run/choice_staging.json'
  'assets/story/*' 'assets/run/choice/*' 'assets/trial/art/*'
  'tools/narrative/*' 'tools/paths/*' 'tools/trial/*' 'tools/run/*'
  'tests/test_narrative_*' 'tests/test_interaction_*' 'tests/test_port_mock.gd*' 'tests/port_conformance.gd*'
  'tests/mocks/*' 'tests/fixtures/narrative/*' 'tests/fixtures/save_v2.json'
  'tests/test_hotspots_*' 'tests/test_choice_clarity.gd*' 'tests/test_run_paths.gd*' 'tests/test_run_ember.gd*'
  'tests/test_run_squadron.gd*' 'tests/test_gospel.gd*' 'tests/test_run_progress.gd*' 'tests/test_run_rail*'
  'tests/test_run_cast.gd*' 'tests/test_run_hud_silent.gd*' 'tests/test_run_home.gd*' 'tests/test_trial.gd*'
  'docs/CHOICE_CLARITY.md' 'docs/VisualChoicePlan.md' 'docs/VISUAL_COVERAGE.md' 'docs/CONTINUOUS_RUN.md'
  'docs/TRIAL_OPENING.md' 'docs/choice/*' 'docs/paths/*' 'docs/narrative/*' 'docs/shots/narrative/*'
  'docs/parallel-development/graph/*'
)
# phase 2 only: the run files, and the two files lent to the music stream for M1
phase2_n=( 'src/run/run_play.gd*' 'src/run/run_play.tscn' 'src/run/run_engine.gd*' 'src/run/run_data.gd*'
  'src/run/run_hotspots.gd*' 'src/run/run_journey.gd*'
  'content/run/run.json' 'tests/test_run_engine.gd*' 'tests/test_run_laps.gd*' 'tests/test_run_lock.gd*'
  'tests/test_run_matrix.gd*' 'tests/test_run_scene.gd*' )
# tools/run/* above covers the narrative stream; the music stream's two tools under tools/run/ are matched first below.
if [ "$SIDE" = music ]; then allowed=("${common_m[@]}"); [ "$PHASE" = 1 ] && allowed+=("${phase1_m[@]}")
else allowed=("${common_n[@]}"); [ "$PHASE" = 2 ] && allowed+=("${phase2_n[@]}"); fi
bad=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for g in "${allowed[@]}"; do [[ $f == $g ]] && { ok=1; break; }; done
  # the narrative stream must not claim the two music tools under tools/run/
  if [ "$SIDE" = narrative ]; then case "$f" in tools/run/measure_mix.py|tools/run/transition_*) ok=0;; esac; fi
  # neither stream may change the contract copy (the lead did, in stage 0.3)
  case "$f" in src/transition/transition_port.gd*) ok=0;; esac
  if [ $ok = 0 ]; then echo "OUT OF SCOPE: $f"; bad=1; fi
done < <(git diff --name-only --no-renames "$BASE"...HEAD)
cmp docs/parallel-development/contract/transition_port.gd src/transition/transition_port.gd || bad=1
[ $bad = 0 ] && echo "scope ok"; exit $bad
```

Note on `BASE`: the narrative stream's N2 worktrees are created from the M1 merge commit, so the music stream's phase 1 work never shows in their diff. The narrative stream's N1 worktree is created from `feature/one-pc` before M1 and merges none of the music stream's work.

---

## 8. Git settings on this PC and hard-coded Linux paths

### 8.1 Settings (this PC, once)

```
git config --global core.autocrlf false
git config --global core.longpaths true
git config core.fileMode false            # in the repository (stage 0.3); 11 files carried the executable bit at the baseline, 12 with tools/dev/godot.sh
```

`.gitattributes` already contains `* text=auto eol=lf` and marks `*.png *.ogg *.mp3 *.wav` as binary, so the working tree is LF on Windows as well. Therefore:

- keep `core.autocrlf=false` (with `true`, Git would convert and show every file as changed against the committed LF);
- configure the editor to write LF;
- Python scripts that write files on Windows can emit CRLF (this review's regenerated graph files did); check `git diff --stat` after running any generator and fix or `git checkout --` the files it should not have touched;
- worktrees are sibling folders of the checkout (`C:\Users\joesa\Documents\Cursor\MusicGame-<name>`), never a temp folder; paths stay short (the longest tracked path is 93 characters);
- Godot 4.5.1 stable is the console exe in `Downloads`, which `tools/test.sh` and `tools/dev/godot.sh` default to; Git Bash for the `.sh` scripts; Python is the venv `C:\Users\joesa\rw-audio-work\venv` with `numpy`, `mido==1.3.3`, `pillow` (stage 0.5; `PYTHON` points at it for `tools/test.sh`); `ffmpeg` and `ffprobe` are on `PATH`.

### 8.2 Hard-coded Linux paths

Stage I1 (branch `wip/import`, merged) fixed the importer: `audio_io.py` finds `ffmpeg` and `ffprobe` on `PATH`, `import_track.py` takes its work folder from `RW_AUDIO_WORK` (else `~/rw-audio-work`), and the importer's Godot and pack defaults were made portable. What was checked on this branch as still hard-coded:

| File and line | Content | Fix (the music stream may make it) |
|---|---|---|
| `tools/audio_import/play_track.sh:11` | Godot default `/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64` | Already overridden by `GODOT`; fail with a clear message if unset. |
| `tools/audio_import/README.md` (several lines), `import_track.py:9`, `test_audio_import.py:3` | `/home/joe/...` and `/usr/bin/ffmpeg` in usage text | Text only. |
| `src/track/README.md:11`, `:12` | Godot and pack paths in the usage example | Text only. |
| `content/music/tracks/catalogue.json:9` | `"packs_live_at": "/home/joe/rw-audio-work/packs"` (data string, informational) | Leave unless a tool reads it; if changed, use a placeholder such as `"$RW_AUDIO_WORK/packs"`. |

Not the music stream's to fix (files it does not own or that are frozen); work around them or report to the lead:

| File and line | Content | Workaround |
|---|---|---|
| `tools/trial/walk_trial.sh:10` | `mktemp -d /tmp/claude-1000/walk_trial.XXXXXX` (the narrative stream's file) | Create the folder first, or the lead has the narrative stream use `${TMPDIR:-/tmp}`. |
| `tools/run/*.sh` (`frames`, `capture`, `capture_path`, `capture_choice`, `walk_run`) and the other scripts with the Linux Godot default `$HOME/godot/Godot_v4.5.1-stable_linux.x86_64` | Default only | All honour `GODOT` first; `export GODOT=...` (or the queue wrapper, stage 0.4). |
| `tools/story/rooms.sh:7`, `tools/story/shoot_preview.sh:8`, `README.md` (the `/tmp/balance.md` example) | `/tmp/...` | Works in Git Bash. |
| `export_presets.cfg:65` | `keystore/debug="C:/Users/joesa/AppData/Roaming/Godot/keystores/debug.keystore"` | Frozen; no export from a stream's worktree. |

---

## Assigned by this document

DECISIONS.md does not name these; the lead should check each.

| Assignment | Reason |
|---|---|
| `src/run/run_progress.gd` to the narrative stream | It is the save (`Session.run_progress`, `user://story_run.json`). |
| `src/core/session.gd` to the narrative stream | Autoload that holds `run_progress`; the music stream needs nothing from it. |
| `src/duel/duel_network.gd`, other autoload-adjacent code: none | Neither task needs it. |
| `src/run/run_rail.gd`, `run_passage*.gd`, `choice_*.gd`, `run_acting.gd`, `run_hud.gd`, `run_levels.*`, `run_over.*`, `dev_text.gd`, `run_play.tscn` | Routing and visuals (`run_play.tscn` follows `run_play.gd`). |
| `src/run/run_hotspots.gd`, `src/run/run_journey.gd` to the music stream for M1 only, then the narrative stream | `ONE_PC_PLAN.md` section 6, stage M1: door state and door timing on open laps. |
| `src/audio/stem_transport.gd`, `src/core/song_clock.gd` to the music stream | The transport and clock. |
| `src/run/run_card_table.gd`, `run_minigame_host.gd`, `run_wallet.gd`, `src/minigames/**`, `src/story/**`, `src/debug/**`, `src/ui/**`, `src/scenes/**`, other `src/core/**`: none | Unrelated to either task. |
| `content/run/run.json` key split in section 3 | DECISIONS.md assigns only the whole file. |
| `songs/**`, `content/story/music.json` to the music stream | Music data the run plays. |
| `content/paths/*/music.json` stays with the narrative stream | D2 gives `content/paths/**` to the narrative stream; this is the one place music data sits in its folder. |
| `tools/run/**` (all but `coverage_audit.*` and `check_hotspots.py`) to the narrative stream; `measure_mix.py` and `transition_*` to the music stream | D2 names only two files. |
| `tools/story/check_run_audio.py`, `check_music.py`, `record_music.gd`, `tools/trial/check_*audio.py` to the music stream; `tools/trial/**`, `tools/paths/**` to the narrative stream | Audio checks vs builders. |
| `tools/test.sh`, `tools/dev/godot.sh`, `tools/content/**`, other shared tools: none (the lead changes them) | Shared runner, queue wrapper and content tests. |
| Test file split in section 2.4, including `test_miss_mute`, `test_story_music_packs`, `test_story_recorded_music` to the music stream and `test_run_*` (non-time-sliced) to the narrative stream | D2 names patterns for the narrative stream only. |
| Reserved test prefixes `test_transition_*`, `test_music_*`, `test_director_*` for the music stream; `tests/test_port_real.gd` for the lead | D2 names none for the music stream. |
| `tests/fixtures/save_v2.json` to the narrative stream | Save-format fixture. |
| `assets/run/choice/**`, `assets/trial/art/**` to the narrative stream; `assets/audio/**` to the music stream | Extension of "scene art". |
| Documents by topic in section 2.5; `docs/music/**`, `docs/narrative/**`, `docs/shots/music/`, `docs/shots/narrative/` | D0 names only the handover files, which this PC does not use. |
| The agent reports its need to the lead in place of the earlier `requests/` files and the `handover/` files | `ONE_PC_PLAN.md` section 4. |

### Where the two streams genuinely overlap after M1

| Overlap | How this document handles it |
|---|---|
| `run_play.gd` and `run_engine.gd`: the music stream needs further hooks for later transition modes. | Hooks are installed in M1 (`MUSIC_TRANSITIONS.md` section 12); later needs are reported to the lead, who has the narrative stream make the edit. |
| `run.json` tuning keys (`energy.track`, `mix`, `stages`, `treatments`) belong to the narrative stream's file but to the music stream's work. | Reported to the lead; new tuning goes to `content/music/transitions/`. |
| `content/paths/*/music.json`: music data in the narrative stream's folder. | Reported to the lead. |
| `tests/test_run_tracks_safety.gd` and its baseline against the narrative stream's routing changes. | Section 5 point 5 (re-recorded on purpose in N2.1). |
| Door and walk timing (`run_journey.gd`, `run_passage.gd` constants) against blend length. | The music stream reports; the lead decides. The plan's `blend_beats` is given to the narrative side in `locked`. |
| `src/transition/transition_port.gd.uid`. | Section 3, row 1: one copy, made by the lead. |
