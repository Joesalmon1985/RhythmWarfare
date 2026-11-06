# File ownership for the two parallel branches

Status: planning document, written 6 November 2026. It is the rulebook that stops the two implementation sessions editing the same files. It follows `/home/joe/rw-audio-work/planning/DECISIONS.md` (D0, D1, D2; D3 to D5 for the new files) and `docs/parallel-development/INTEGRATION_CONTRACT.md`. Where a file is not named in DECISIONS.md, this document assigns it and lists the assignment in the final section.

Names used throughout:

| Short name | Branch | Machine |
|---|---|---|
| Windows | `feature/adaptive-music-transitions` | Windows PC |
| Ubuntu | `feature/interactive-scene-choices` | Ubuntu laptop |
| Baseline | the commit `BASELINE_SHA` on `main`, from which both branches start | |
| W1 | milestone "track scenes finished and the transition seam installed"; pushed tag `w1-track-wiring` on the Windows branch | |

"Exists" in the matrix means the path is in `git ls-files` of the repository as it will be on `main` (checked against `/home/joe/Projects/MusicGame-tracks`). "new" means no such path exists at the baseline; the named side creates it.

---

## 1. The rules in one page

1. **Two phases.** Phase 1 is from the baseline until W1. Phase 2 is from W1 onwards. Only the run files in rule 4 change hands at W1; everything else has one owner for the whole job.
2. **"Owns" means: only the owner's branch changes the file.** Changing includes editing, renaming, deleting, reformatting, regenerating, and letting a tool rewrite it. The other side may read it, run it and depend on it. A file with no owner in the matrix is frozen for both sides.
3. **Frozen files** cannot be changed by either branch: `src/transition/transition_port.gd` (apart from the one-off first-commit copy), `project.godot`, `export_presets.cfg`, `docs/HANDOVER.md`, `README.md`, `docs/parallel-development/INTEGRATION_CONTRACT.md`, `docs/parallel-development/contract/**`, and the generated people sheets. They change only in the integration session (section 4).
4. **Time-sliced files.** Phase 1: Windows owns `src/run/run_play.gd`, `src/run/run_engine.gd`, `src/run/run_data.gd`, `src/run/run_audio.gd`, `content/run/run.json`. Ubuntu does not edit them and works against the mock. Phase 2: the first, second, third and fifth of those pass to Ubuntu. `src/run/run_audio.gd` stays with Windows.
5. **Asking for a change in the other side's file.** Write `docs/parallel-development/requests/<side>-NNN.md` on your own branch (`<side>` is `windows` or `ubuntu`; `NNN` counts up from 001 per side), push the branch, and carry on with something else. The request names the file, the function or key, the change wanted, and why it cannot be done in a file you own. The owner fetches your branch, applies the change in their own file (or answers in `docs/parallel-development/requests/<side>-NNN-reply.md` on their own branch), and records the outcome in their handover file. Nobody applies a request by editing the other side's file from their own branch. Requests are never merged into `main` by either worker; the integration session reads them.
6. **The contract file is copied and never edited.** `docs/parallel-development/contract/transition_port.gd` is copied byte for byte to `src/transition/transition_port.gd` as the first commit of each branch. Verify with `cmp docs/parallel-development/contract/transition_port.gd src/transition/transition_port.gd`. Nobody edits the copy. A contract change is a request; the owner (or the integration session) amends the contract on `main`, bumps `VERSION`, and both branches merge `main`. The copy's `.gd.uid` file is committed only by Windows (section 3, row 1).
7. **At W1, Ubuntu merges the tag into its own branch, not into `main`.** Command, run on the Ubuntu branch with a clean tree: `git fetch origin tag w1-track-wiring && git merge --no-ff w1-track-wiring`. Ubuntu has not touched any Windows-owned file in phase 1, so the merge should be clean; any conflict is a breach of this document and goes to the lead. After the merge Ubuntu runs the full suite and records the result in its handover. Windows may keep pushing further commits to its branch, but Ubuntu takes later Windows commits only by another explicit merge of a new tag (`w2-...`, named by the Windows worker in its handover) and only when it chooses to.
8. **Neither worker pushes `main`, merges the other branch into `main`, force-pushes, or rebases published commits.** Each pushes its own branch and writes its own handover file: `docs/parallel-development/handover/WINDOWS.md` and `docs/parallel-development/handover/UBUNTU.md`.
9. **Never `git add -A` or `git add .` in the main checkout.** `ToAddTry2/`, `ToAddTry3/`, `ToAddTry4/` (the owner's audio drops) and the planning folder are untracked there and must stay out of commits. Stage by explicit path.
10. **Before every push** run the checklist in section 7.

---

## 2. The ownership matrix

Owner column values: **W** = Windows, **U** = Ubuntu, **none** = frozen for both (change only in the integration session, or by a request to the lead), **W then U** = Windows until W1, Ubuntu after.

Globs: `*` matches within one folder, `**` matches any depth.

### 2.1 Source: `src/`

| Path or glob | Exists or new | Owner before W1 | Owner after W1 | Notes |
|---|---|---|---|---|
| `src/run/run_play.gd` | exists | W | U | Time-sliced (D2). The seam hooks are added by Windows in W1. See section 3. |
| `src/run/run_play.tscn` | exists | W | U | Goes with `run_play.gd`. |
| `src/run/run_engine.gd` | exists | W | U | Time-sliced. See section 3. |
| `src/run/run_data.gd` | exists | W | U | Time-sliced. See section 3. |
| `src/run/run_audio.gd` | exists | W | W | Music transport. Stays with Windows throughout (D2). |
| `src/run/run_track_plan.gd` | exists | W | W | Track scene planning (D2: `src/run/run_track_*.gd`). |
| `src/run/run_track_scenes.gd` | exists | W | W | Same. Its static `enabled` flag is read by the test runner; do not change its behaviour under the runner. |
| `src/run/run_track_*.gd` (further files) | new | W | W | Any new file with this prefix is Windows'. |
| `src/run/run_hotspots.gd` | exists | U | U | D2. |
| `src/run/hotspot_view.gd` | exists | U | U | D2. |
| `src/run/hotspot_contract.gd` | exists | U | U | D2. Route prefixes (`trial:`, `path:`, `run:`) live here; new quest route kinds go here. |
| `src/run/run_journey.gd` | exists | U | U | D2. Door-walk constants `DOOR_BEATS` and `CLOSE_BEATS` are Ubuntu's; Windows asks if a blend needs different timing. |
| `src/run/run_progress.gd` | exists | U | U | The save (`user://story_run.json`); D2 gives Ubuntu "the save format". |
| `src/run/run_rail.gd`, `src/run/run_passage.gd`, `src/run/run_passage_view.gd` | exists | U | U | Camera rail and passages: routing and visuals (finding D). |
| `src/run/choice_staging.gd`, `src/run/choice_props.gd`, `src/run/run_acting.gd` | exists | U | U | Choice visuals and acting. |
| `src/run/run_hud.gd`, `src/run/run_levels.gd`, `src/run/run_levels.tscn`, `src/run/run_over.gd`, `src/run/run_over.tscn`, `src/run/dev_text.gd` | exists | U | U | Run interface. |
| `src/run/run_card_table.gd`, `src/run/run_minigame_host.gd`, `src/run/run_wallet.gd` | exists | none | none | Blackjack and wallet; neither task needs them. Ask if a change is unavoidable. |
| `src/transition/transition_port.gd` | new | none (first-commit copy only) | none | Byte copy of the contract. See section 3. |
| `src/transition/transition_director.gd` and any other `src/transition/**` file | new | W | W | `TransitionDirector extends TransitionPort`. |
| `src/music/**` | new | W | W | Adaptive music transport and planner. |
| `src/narrative/**` | new | U | U | `NarrativeGraph`, `QuestRouter`, `RouteState`. |
| `src/track/**` (`track_*.gd`, `track_play.tscn`, `README.md`) | exists | W | W | D2. `src/track/README.md` has hard-coded paths Windows may fix (section 8). |
| `src/audio/stem_transport.gd` | exists | W | W | Stem playback. |
| `src/audio/battle_sfx.gd` | exists | none | none | Battle effects; unrelated to both tasks. |
| `src/core/song_clock.gd` | exists | W | W | The clock. `song_time()` must stay continuous (D5). |
| `src/core/session.gd` | exists | U | U | Autoload `Session`. Ubuntu owns `Session.run_progress` and the save (D2). Windows needs nothing from it: music code never reads the save (contract section 1). |
| `src/duel/duel_network.gd` | exists | none | none | Autoload `DuelNetwork`; neither task touches it. |
| `src/duel/**` (other files) | exists | none | none | Wizard duel. |
| `src/trial/**` (`trial_*.gd`, `trial_play.tscn`) | exists | U | U | The Bassment (D2). |
| `src/core/**` (other files), `src/input/**`, `src/sim/**`, `src/ui/**`, `src/scenes/**`, `src/minigames/**`, `src/debug/**` | exists | none | none | Legacy battle game, menus, minigames, debug overlay. Unassigned by DECISIONS.md; frozen. |
| `src/story/**` | exists | none | none | Legacy chapter campaign. Frozen. |
| `*.gd.uid` for any file above | exists / new | follows the `.gd` | follows the `.gd` | The side that creates a script commits its `.uid`. |

### 2.2 Content and data

| Path or glob | Exists or new | Owner before W1 | Owner after W1 | Notes |
|---|---|---|---|---|
| `content/run/run.json` | exists | W | U | Time-sliced. Key by key rules in section 3. |
| `content/run/track_scenes.json` | exists | W | W | Track per scene (D2). |
| `content/run/hotspots/*.json` (`warehouse`, `hospital`, `hospital_late`, `ward`, `ward_late`, `mothership`, `underworld`) | exists | U | U | Hotspot data. |
| `content/run/choice_staging.json` | exists | U | U | |
| `content/music/arrangements/**` | exists | W | W | Loop arrangements (D2: `content/music/**`). |
| `content/music/catalogue.json`, `content/music/mix_recipes.json`, `content/music/palettes.json` | exists | W | W | |
| `content/music/tracks/**` (`catalogue.json`, `ac13_shostakovich.json`, `acuna_go_back.json`) | exists | W | W | Metadata only, never audio. `catalogue.json` line 9 has a Linux path Windows may fix. |
| `content/music/transitions/**` (`<track id>.json`) | new | W | W | Per-track sidecars (D5). |
| `content/narrative/**` (`graph.json` and any overlay files) | new | U | U | Format `rhythm_warfare.narrative.v1` (D3). |
| `content/paths/**` (`ember/`, `gospel/`, `squadron/`, `stub/`: `run.json`, `music.json`, `walks.json`, `prompts.json`) | exists | U | U | D2. The `music.json` files are music data inside Ubuntu's folder; Windows reads them and asks by request. |
| `content/trial/**` (`passages.json`, `hotspots.json`, `layout/*.json`) | exists | U | U | D2. |
| `content/story/music.json` | exists | W | W | Recorded-music table. |
| `content/story/**` (other files, `maps/**`) | exists | none | none | Legacy chapters. |
| `content/library/**`, `content/missions/**`, `content/missions_legacy/**`, `content/fixtures/**`, `content/duel/**`, `content/minigames/**`, `content/sounds.json`, `content/build_state.json`, `content/README.md`, `content/REPORT.md` | exists | none | none | Legacy loop library, missions, duel, blackjack. `content/imports/` is in `.gitignore` but twelve files are tracked there; frozen. |
| `songs/**` | exists | W | W | Recorded loop packs the run plays; Windows' audio. `songs/*/audio/*.wav` is ignored and stays out of Git. |
| `data/**`, `campaign/**`, `midi_export/**`, `pixelexample/**`, `ToAddTry1/**`, `Rhythm_Warfare_Level_01_MIDI.zip` | exists | none | none | Legacy. |

### 2.3 Tools

| Path or glob | Exists or new | Owner before W1 | Owner after W1 | Notes |
|---|---|---|---|---|
| `tools/audio_import/**` | exists | W | W | D2. Contains the hard-coded paths in section 8. |
| `tools/run/coverage_audit.gd`, `tools/run/coverage_audit.py` (and `tools/run/coverage_audit.*`) | new | U | U | D2/D4. |
| `tools/run/check_hotspots.py` | exists | U | U | D2. |
| `tools/run/measure_mix.py` | exists | W | W | Mix measurement; audio. Assigned here. |
| `tools/run/transition_*` | new | W | W | Any Windows measuring tool for transitions. |
| `tools/run/**` (every other existing file: `check_path.gd`, `choice_audit.gd`, `choice_audit.py`, `make_hotspots.py`, `make_scenes.py`, `walk_run.sh`, `capture*.sh`, `laps*.py`/`.gd`, `acting_*.py`, and so on) | exists | U | U | Routing, hotspot and art builders. Assigned here. |
| `tools/narrative/**` (`graph.py`, tests) | new | U | U | D3. |
| `tools/story/check_run_audio.py`, `tools/story/check_music.py`, `tools/story/record_music.gd` | exists | W | W | Audio checks. Assigned here. |
| `tools/trial/check_trial_audio.py`, `tools/trial/check_transition_audio.py` | exists | W | W | Audio checks. Assigned here. |
| `tools/trial/**` (other files), `tools/paths/**` | exists | U | U | Bassment and path builders. |
| `tools/test.sh` | exists | none | none | Shared runner. Already defaults to the Windows Godot path. Neither side edits it; set `GODOT` in the environment. |
| `tools/content/**` | exists | none | none | Python content tools and their tests, used by `tools/test.sh`. A side that needs a change makes a request. Both sides run them read-only. |
| `tools/story/**` (other files, `tools/story/art/**`) | exists | none | none | Art builders; they regenerate committed sheets. Do not run them. |
| `tools/campaign/**`, `tools/duel/**`, `tools/minigames/**`, `tools/autoplay.gd`, `tools/balance*.py`, `tools/balance.sh`, `tools/export_smoke.gd`, `tools/probe.gd`, `tools/shoot.gd`, `tools/shrink_shots.py`, `tools/make_song_pack.py`, `tools/pck_*.py`, `tools/extract_openra*.py`, `tools/import_openra_assets.py`, `tools/test_extract_openra_sounds.py` | exists | none | none | Shared or legacy tooling. Run, do not edit. `tools/export_smoke.gd` belongs to the integration session. |

### 2.4 Tests

The runner only runs `tests/test_*.gd` (except `test_case.gd`), so file names are the ownership key. See section 5 for the rules.

| Path or glob | Exists or new | Owner before W1 | Owner after W1 | Notes |
|---|---|---|---|---|
| `tests/test_run_audio_polish.gd`, `tests/test_run_audio_sections.gd`, `tests/test_run_tracks_data.gd`, `tests/test_run_tracks_engine.gd`, `tests/test_run_tracks_plan.gd`, `tests/test_run_tracks_safety.gd` | exists | W | W | Audio and track scenes. `test_run_tracks_safety.gd` compares against `tests/fixtures/track_scenes/baseline_runs.json`; see section 5. |
| `tests/test_track_game.gd`, `tests/test_track_loader.gd`, `tests/test_track_scene.gd`, `tests/test_track_transport.gd`, `tests/test_transport.gd`, `tests/track_test_kit.gd` | exists | W | W | Track mode and transports. |
| `tests/test_story_music_packs.gd`, `tests/test_story_recorded_music.gd`, `tests/test_miss_mute.gd` | exists | W | W | Recorded music and stem muting. Assigned here. |
| `tests/test_run_engine.gd`, `tests/test_run_laps.gd`, `tests/test_run_lock.gd`, `tests/test_run_matrix.gd`, `tests/test_run_scene.gd` | exists | W | U | They test the time-sliced files, so they follow them. |
| `tests/test_hotspots_any_window.gd`, `tests/test_hotspots_data.gd`, `tests/test_hotspots_engine.gd`, `tests/test_hotspots_scene.gd`, `tests/test_hotspots_view.gd`, `tests/test_choice_clarity.gd` | exists | U | U | Interaction. |
| `tests/test_run_paths.gd`, `tests/test_run_ember.gd`, `tests/test_run_squadron.gd`, `tests/test_gospel.gd`, `tests/test_run_progress.gd`, `tests/test_run_rail.gd`, `tests/test_run_rail_scene.gd`, `tests/test_run_cast.gd`, `tests/test_run_hud_silent.gd`, `tests/test_run_home.gd`, `tests/test_trial.gd` | exists | U | U | Paths, progress, rail, cast, HUD, home, Bassment. |
| `tests/test_narrative_*.gd` | new | U | U | D2 pattern. |
| `tests/test_interaction_*.gd` | new | U | U | D2 pattern. |
| `tests/test_port_mock.gd` | new | U | U | Runs the conformance cases on the mock (contract section 9). |
| `tests/port_conformance.gd` | new | U | U | D2. Not named `test_*`, so the runner does not run it directly. |
| `tests/mocks/**` (`mock_transition_director.gd`) | new | U | U | D2. |
| `tests/test_transition_*.gd`, `tests/test_music_*.gd`, `tests/test_director_*.gd` | new | W | W | Windows' new patterns. These three prefixes are reserved for Windows. |
| `tests/test_port_real.gd` | new | none | none | Integration session only: runs `port_conformance.gd` on the real director (contract section 9). |
| `tests/run_tests.gd`, `tests/test_case.gd` | exists | none | none | Test harness. |
| `tests/fixtures/track_fixture/**`, `tests/fixtures/track_scenes/**`, `tests/fixtures/transport/**` | exists | W | W | Synthetic pack, baseline recorder, transport audio. |
| `tests/fixtures/transition/**` | new | W | W | Windows' new fixtures. |
| `tests/fixtures/narrative/**` | new | U | U | Ubuntu's new fixtures. |
| `tests/fixtures/save_v2.json` | exists | U | U | A save-format fixture. |
| `tests/fixtures/library_fixture/**`, `tests/fixtures/pack_v4/**`, `tests/fixtures/village_test.json`, `tests/fixtures/fake_minigame.gd`, `tests/fixtures/fake_minigame_view.gd`, `tests/fixtures/make_library_fixture.py` | exists | none | none | Legacy fixtures. |
| every other existing `tests/test_*.gd` (`test_all_missions`, `test_battle`, `test_battle_sfx`, `test_blackjack_*`, `test_campaign`, `test_civilian_art`, `test_duel`, `test_judge`, `test_level_loader`, `test_library_index`, `test_loadout*`, `test_match`, `test_minigame_*`, `test_mission*`, `test_money_*`, `test_note_lane`, `test_pad_judge`, `test_playtest`, `test_rewards`, `test_roster`, `test_scenes`, `test_section_input`, `test_sequences`, `test_story_*` other than the two above, `test_village_sim`, `test_wallet`) | exists | none | none | Legacy. Run them; if one fails because of your change, fix your change. |

### 2.5 Assets, project files, documents

| Path or glob | Exists or new | Owner before W1 | Owner after W1 | Notes |
|---|---|---|---|---|
| `assets/story/**` scene art (backgrounds, props, objects) | exists | U | U | D2: "scene art under `assets/`". New entrance and return objects go here. |
| `assets/story/*/people/**` (generated people sheets, `page_N.png` and `.import`) | exists | none | none | Frozen for both. See section 3 and section 6. |
| `assets/run/choice/**`, `assets/trial/art/**` | exists | U | U | Choice and Bassment art. |
| `assets/minigames/blackjack/**` | exists | none | none | |
| `assets/audio/**` or any new audio asset folder | new | W | W | Only if a small synthetic test sound is needed; no third-party audio (section 6). |
| `project.godot` | exists | none | none | Section 3. |
| `export_presets.cfg` | exists | none | none | Section 3. |
| `icon.svg`, `icon.svg.import` | exists | none | none | |
| `.gitignore`, `.gitattributes` | exists | none | none | Changed only at integration. |
| `README.md` | exists | none | none | Section 3. |
| `docs/HANDOVER.md` | exists | none | none | Section 3. |
| `docs/parallel-development/handover/WINDOWS.md` | new | W | W | Windows' handover. |
| `docs/parallel-development/handover/UBUNTU.md` | new | U | U | Ubuntu's handover. |
| `docs/parallel-development/requests/windows-NNN.md` (and `-NNN-reply.md`) | new | W | W | Windows' requests and replies. |
| `docs/parallel-development/requests/ubuntu-NNN.md` (and `-NNN-reply.md`) | new | U | U | Ubuntu's requests and replies. |
| `docs/parallel-development/graph/narrative_graph.json` and the Mermaid export | new | U | U | Output of `tools/narrative/graph.py` (D3). |
| `docs/parallel-development/INTEGRATION_CONTRACT.md`, `docs/parallel-development/contract/transition_port.gd`, `docs/parallel-development/FILE_OWNERSHIP.md` and the other planning documents committed at the baseline | exists | none | none | Frozen from the baseline. |
| `docs/TRACK_SCENES_HANDOVER.md` | exists in the worktree; untracked there, so the lead must commit it before the baseline | W | W | The W1 brief. |
| `docs/RUN_TRACK_SCENES.md`, `docs/TRACK_ASSIGNMENT.md`, `docs/TRACK_PACK_FORMAT.md`, `docs/MUSIC_CATALOGUE.md`, `docs/MUSIC_HANDOFF.md`, `docs/MUSIC_IMPORT.md`, `docs/MUSIC_LIBRARY_PLAN.md`, `docs/MUSIC_REPORT.md`, `docs/MUSIC_TRACKS.md`, `docs/MusicImportPlan.md`, `docs/TIMING.md`, `docs/RUN_DUNGEON_MUSIC_PLAN.md` | exists | W | W | Music documents. Assigned here. |
| `docs/CHOICE_CLARITY.md`, `docs/VisualChoicePlan.md`, `docs/VISUAL_COVERAGE.md`, `docs/CONTINUOUS_RUN.md`, `docs/TRIAL_OPENING.md`, `docs/choice/**`, `docs/paths/**` | exists | U | U | Routing and interaction documents. Assigned here. |
| `docs/music/**` | new | W | W | Any further Windows design note that is not its handover. |
| `docs/narrative/**` | new | U | U | Any further Ubuntu design note that is not its handover. |
| `docs/shots/**` | exists | none | none | Screenshots; any new screenshot goes into the owner's own subfolder `docs/shots/<side>/` (new) and is run through `tools/shrink_shots.py` first. |
| every other existing file under `docs/` | exists | none | none | Legacy documents. |

---

## 3. Files that cannot be modified independently

| File | Why | Procedure |
|---|---|---|
| `src/transition/transition_port.gd` | It is the contract as code. Two edits would silently split the interface. Both branches need it before W1 (Windows for the director, Ubuntu for the mock). | Each branch copies it as its first commit and checks it with `cmp`. Windows commits the file and its `transition_port.gd.uid`. Ubuntu commits only the `.gd`; it adds `src/transition/transition_port.gd.uid` to `.git/info/exclude` so its own generated `.uid` never reaches a commit. The two `.gd` copies are byte-identical, so the W1 merge adds them without conflict; if Git still reports a conflict on the `.uid`, take the tag's version (`git checkout --theirs`). Any change is a request, applied only on `main` by the owner or the integration session (rule 6). |
| `project.godot` | One shared `[autoload]` block (`Session`, `DuelNetwork`) and display and input settings. Both contract and D2 forbid a new autoload or global. Cold file, so conflicts are certain if touched twice. | Neither side edits it. A need (new input action, autoload, setting) goes into a request. The integration session decides (section 4). Godot may rewrite it when the editor opens the project; always `git checkout -- project.godot` before staging if `git diff --name-only` shows it. |
| `export_presets.cfg` | Holds the owner's Windows keystore path at line 65 and the Android and Windows presets. | Neither side edits it. Never run an export from either branch. Integration only. |
| `content/run/run.json` | 113 KB with 36 nodes and 141 cinematics inline; JSON conflicts line by line even when the sections differ. Time-sliced (D2). | Phase 1 (Windows): only these top-level keys may change, and only if the track scenes work needs it: `energy` (including `energy.track`), `mix`, `stages`, `effects`, `treatments`, `timing`, `judgement`. It must not touch `worlds`, `start_node`, `nodes`, `cinematics`. Phase 2 (Ubuntu): `worlds`, `start_node`, `nodes`, `cinematics` only, plus a hotspot reference if needed. The keys `energy`, `mix`, `stages`, `effects`, `treatments`, `timing`, `judgement` are then read-only for Ubuntu and are changed by request to Windows, who answers with the tuning in a new file under `content/music/transitions/` or `content/music/` where possible. New data does not go into `run.json` at all (narrative overlay in `content/narrative/`, music transition data in `content/music/transitions/`). Nobody reformats the file: keep key order and indent; any diff that touches a line you did not mean to change is reverted. |
| `src/run/run_play.gd` | 1781 lines, one class; audio and routing code share functions (`_ready`, `_handle`, `_open_routes`, `_path_swap`, `_on_phase_start`). | Phase 1: Windows only. In W1 it installs the hook points (listed in its handover with function names and line ranges) so that later music work needs no further edits. After W1: Ubuntu only. Windows asks for any change by request; the request names the function and the exact lines to add. |
| `src/run/run_engine.gd` | 906 lines; `_commit`, `_enter`, `_decide` interleave track and routing branches. | Same as `run_play.gd`. Windows adds the engine events and the `request`-facing API in W1 as new functions in a new region at the end of the file; Ubuntu does not rewrite those after W1, only calls them. |
| `src/run/run_data.gd` | `load_files` must end with `RunTrackScenes.attach(d)`; narrative loading also lives here. | Phase 1: Windows only. After W1: Ubuntu only, and `RunTrackScenes.attach(d)` stays the last call in `load_files`. Narrative graph loading is added as a separate call that does not reorder existing ones. |
| `docs/HANDOVER.md` | Append-only log that conflicted at every merge. | Nobody edits it (D0). Each side writes its own handover file. The integration session merges both into it (section 4). |
| `README.md` | Public description; the open decisions for the owner (D7) are listed there. | Nobody edits it. Integration only. |
| Generated people sheets (`assets/story/*/people/**`, `page_N.png` and `page_N.png.import`) | Committed output of art builders; binary, so any double change conflicts and cannot be merged. | Neither side runs `tools/story/figure_sheets.py`, `face_sheets.py`, `build_assets.py`, `build_gospel_art.py`, `build_ember.py` or `tools/story/art/**`. If a sheet must change, the integration session edits the sources and regenerates the sheets as a separate commit; never merge two versions. If a script is run by accident, `git checkout -- assets/` before staging. |

---

## 4. Integration-only changes

Done only by the integration session, after both branches are finished and their handovers read, on a branch created from `main` (for example `integrate/music-and-choices`) and merged to `main` by the lead.

| Change | Detail |
|---|---|
| Merge both branches | Merge `feature/adaptive-music-transitions` and `feature/interactive-scene-choices` (Ubuntu's branch already contains the W1 tag). Resolve conflicts using the requests folders and both handovers. |
| Wire the real director in place of the mock | Replace `MockTransitionDirector` by `TransitionDirector` in the run scene's construction; add `tests/test_port_real.gd` running `tests/port_conformance.gd` on the real director with a virtual clock; keep the mock for the unit tests. |
| `project.godot` | Any input action, autoload or setting either side asked for by request. Normally none. |
| `export_presets.cfg`, `.gitignore`, `.gitattributes` | Keystore path, preset changes, new ignore rules. |
| `README.md` and `docs/HANDOVER.md` | New sections for both workstreams; the owner's open decisions from D7; folding the two handover files into the log. |
| `tools/test.sh`, `tools/content/**`, `tools/export_smoke.gd` | Any change to the shared runner, and `-s tools/export_smoke.gd` after the merge. |
| Generated people sheets | Regenerated once, as their own commit, if needed. |
| Contract changes | Amend `contract/transition_port.gd` and `INTEGRATION_CONTRACT.md`, bump `VERSION`, update both copies. |
| Final checks | Full suite, `SCRIPT ERROR` count, `python tools/run/check_hotspots.py` for main and each path, `python tools/narrative/graph.py` validation, `python -m unittest discover -s tools/audio_import`, and an export smoke test. |

---

## 5. Tests: names, who changes what

1. **Names decide ownership.** Windows creates only `tests/test_transition_*.gd`, `tests/test_music_*.gd`, `tests/test_director_*.gd`, `tests/fixtures/transition/**`, and Python tests beside its tools (`tools/audio_import/test_*.py`). Ubuntu creates only `tests/test_narrative_*.gd`, `tests/test_interaction_*.gd`, `tests/test_port_mock.gd`, `tests/port_conformance.gd`, `tests/mocks/**`, `tests/fixtures/narrative/**`, and Python tests beside its tools (`tools/narrative/test_*.py`). Any new test file that fits neither list takes a prefix from the creator's list; if none fits, ask by request.
2. **Only the owner of a test file may change its assertions**, and never to make a failure pass. An assertion is changed only when the behaviour it checks was deliberately changed by the owner, and the commit message says what behaviour changed and why. Deleting or weakening an assertion to silence a failure is not allowed on either side.
3. **A failing test the other side owns** is a defect in your change until proved otherwise. Fix your change. If the test itself is wrong, write a request; the owner decides.
4. **Time-sliced tests** (`test_run_engine`, `test_run_laps`, `test_run_lock`, `test_run_matrix`, `test_run_scene`) follow the run files: Windows before W1, Ubuntu after.
5. **The baseline recording.** `tests/test_run_tracks_safety.gd` compares today's behaviour against `tests/fixtures/track_scenes/baseline_runs.json`. Ubuntu's routing changes may legitimately alter it. Ubuntu raises a request with the reason; Windows re-records (`record_baseline.gd`) and commits, or explains why the change is a defect.
6. **The track scenes switch.** Track scenes are off under the test runner unless a test sets the static `RunTrackScenes.enabled`; tests that do must reset it. Neither side changes that mechanism without a request.
7. **Full suite before any push:** `GODOT=<path> bash tools/test.sh`, plus `$GODOT --headless --path . -s tests/run_tests.gd 2>&1 | grep -c "SCRIPT ERROR"` must print 0 (the runner prints "0 failures" even when a script fails to parse). Record the counts in the handover.

---

## 6. Metadata and generated assets

| Kind | Where it lives | In Git? | Who regenerates |
|---|---|---|---|
| Track packs (stems, audio from the recordings) | outside the repository: `/home/joe/rw-audio-work/packs` (Ubuntu), copied by hand as an archive; the game finds them through `RW_TRACKS_DIR`, else `user://track_packs` | **Never.** Public repository, third-party releases. | Ubuntu machine only, with `tools/audio_import`; the owner copies the archive to Windows. |
| Anything derived from the recordings (stems, separated audio, charts as pack files, waveforms, previews, rendered or stretched tails, pitch-shifted files, caches) | outside the repository: `rw-audio-work/cache`, `user://` or a folder named by an `RW_*` variable | **Never.** The same rule as the packs. | Whoever needs them, locally. |
| Track metadata (`content/music/tracks/*.json`, `content/music/transitions/<id>.json`) | repository | Yes, text only. | Windows. |
| Synthetic test packs | `tests/fixtures/track_fixture/**` | Yes (small, synthetic). | Windows, with `make_fixture.py`. |
| Narrative overlay and exports | `content/narrative/**`, `docs/parallel-development/graph/**` | Yes. | Ubuntu, with `tools/narrative/graph.py`. |
| `.godot/` | each working copy | No (`.gitignore`). Run `$GODOT --headless --path . --import` once on each fresh checkout; `tools/test.sh` does it. | Godot. |
| `.import` files | beside the assets (7,411 tracked) | **Yes**, as the repository has it. Do not hand-edit. | Godot, when it imports a new asset; the side that adds the asset commits its `.import`. If an `.import` of an untouched asset shows as changed, revert it. |
| `.uid` files (253 tracked, one per `.gd` and some tools) | beside each script | **Yes.** | The side that creates the script commits its `.uid`. A new script without its `.uid` committed is incomplete. Never commit a `.uid` for the other side's script. |
| `build/`, `*.tmp`, `__pycache__/`, `songs/*/audio/*.wav`, `content/library/*/placeholder/`, `*.asd`, `midi_export/**/*.wav`, `/audition/`, `content/imports/` | | No (`.gitignore`). | |
| Generated people sheets | `assets/story/*/people/**` | Yes (committed output); frozen. | Integration session only. |
| Screenshots | `docs/shots/<side>/` | Yes, shrunk with `tools/shrink_shots.py` first. | The side that took them. |
| `user://story_run.json`, `user://track_packs` | the machine's user folder | No. | The game. |

Do not commit `ToAddTry2/`, `ToAddTry3/`, `ToAddTry4/`: they are untracked owner drops with recordings.

---

## 7. Checklist before every push

1. `git status --short` shows nothing unexpected; no `ToAddTry*`, no audio, no `.godot/`.
2. `git diff --name-only --no-renames BASELINE_SHA...HEAD` is compared against your allowed globs (snippet below). Every name must match, with the phase rule applied. Any name that does not match is reverted (`git checkout BASELINE_SHA -- <file>`) or moved into a request.
3. `cmp docs/parallel-development/contract/transition_port.gd src/transition/transition_port.gd` is silent.
4. Full suite, `SCRIPT ERROR` count 0, the tool checks for your side (section 5 point 7, and `check_hotspots.py` for Ubuntu, `python -m unittest discover -s tools/audio_import` for Windows).
5. Your handover file is updated and committed.
6. Push your own branch only: `git push origin HEAD:<your branch>`.

Suggested snippet (bash; in the patterns `*` also matches `/`, so `a/*` means everything below `a/`). Set `SIDE`, `PHASE` and the baseline once.

```bash
#!/usr/bin/env bash
# usage: SIDE=windows|ubuntu PHASE=1|2 BASELINE=BASELINE_SHA bash check_scope.sh
set -u
common_w=(
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
  'docs/RUN_DUNGEON_MUSIC_PLAN.md' 'docs/music/*' 'docs/shots/windows/*'
  'docs/parallel-development/handover/WINDOWS.md' 'docs/parallel-development/requests/windows-*'
)
phase1_w=( 'src/run/run_play.gd*' 'src/run/run_play.tscn' 'src/run/run_engine.gd*' 'src/run/run_data.gd*'
  'content/run/run.json' 'tests/test_run_engine.gd*' 'tests/test_run_laps.gd*' 'tests/test_run_lock.gd*'
  'tests/test_run_matrix.gd*' 'tests/test_run_scene.gd*' )
common_u=(
  'src/narrative/*' 'src/trial/*' 'src/core/session.gd*' 'src/run/run_hotspots.gd*' 'src/run/hotspot_*'
  'src/run/run_journey.gd*' 'src/run/run_progress.gd*' 'src/run/run_rail.gd*' 'src/run/run_passage*'
  'src/run/choice_*' 'src/run/run_acting.gd*' 'src/run/run_hud.gd*' 'src/run/run_levels.*'
  'src/run/run_over.*' 'src/run/dev_text.gd*'
  'src/transition/transition_port.gd'
  'content/narrative/*' 'content/paths/*' 'content/trial/*' 'content/run/hotspots/*' 'content/run/choice_staging.json'
  'assets/story/*' 'assets/run/choice/*' 'assets/trial/art/*'
  'tools/narrative/*' 'tools/paths/*' 'tools/trial/*' 'tools/run/*'
  'tests/test_narrative_*' 'tests/test_interaction_*' 'tests/test_port_mock.gd*' 'tests/port_conformance.gd*'
  'tests/mocks/*' 'tests/fixtures/narrative/*' 'tests/fixtures/save_v2.json'
  'tests/test_hotspots_*' 'tests/test_choice_clarity.gd*' 'tests/test_run_paths.gd*' 'tests/test_run_ember.gd*'
  'tests/test_run_squadron.gd*' 'tests/test_gospel.gd*' 'tests/test_run_progress.gd*' 'tests/test_run_rail*'
  'tests/test_run_cast.gd*' 'tests/test_run_hud_silent.gd*' 'tests/test_run_home.gd*' 'tests/test_trial.gd*'
  'docs/CHOICE_CLARITY.md' 'docs/VisualChoicePlan.md' 'docs/VISUAL_COVERAGE.md' 'docs/CONTINUOUS_RUN.md'
  'docs/TRIAL_OPENING.md' 'docs/choice/*' 'docs/paths/*' 'docs/narrative/*' 'docs/shots/ubuntu/*'
  'docs/parallel-development/handover/UBUNTU.md' 'docs/parallel-development/requests/ubuntu-*'
  'docs/parallel-development/graph/*'
)
phase2_u=( 'src/run/run_play.gd*' 'src/run/run_play.tscn' 'src/run/run_engine.gd*' 'src/run/run_data.gd*'
  'content/run/run.json' 'tests/test_run_engine.gd*' 'tests/test_run_laps.gd*' 'tests/test_run_lock.gd*'
  'tests/test_run_matrix.gd*' 'tests/test_run_scene.gd*' )
# tools/run/* above covers Ubuntu; the Windows-owned tools/run files are matched first below.
if [ "$SIDE" = windows ]; then allowed=("${common_w[@]}"); [ "$PHASE" = 1 ] && allowed+=("${phase1_w[@]}")
else allowed=("${common_u[@]}"); [ "$PHASE" = 2 ] && allowed+=("${phase2_u[@]}"); fi
bad=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for g in "${allowed[@]}"; do [[ $f == $g ]] && { ok=1; break; }; done
  # Ubuntu must not claim the two Windows tools under tools/run/
  if [ "$SIDE" = ubuntu ]; then case "$f" in tools/run/measure_mix.py|tools/run/transition_*) ok=0;; esac; fi
  if [ $ok = 0 ]; then echo "OUT OF SCOPE: $f"; bad=1; fi
done < <(git diff --name-only --no-renames "$BASELINE"...HEAD)
cmp docs/parallel-development/contract/transition_port.gd src/transition/transition_port.gd || bad=1
[ $bad = 0 ] && echo "scope ok"; exit $bad
```

Note for the Ubuntu run of the snippet: before W1 the tag merge brings Windows' files into `BASELINE...HEAD`. After the merge, compare against the tag instead of the baseline for Windows-owned paths: use `git diff --name-only --no-renames w1-track-wiring...HEAD` (Ubuntu's own work since the merge) plus the pre-merge list taken with `git diff --name-only --no-renames BASELINE_SHA...<commit before the merge>`. Record the pre-merge commit in the Ubuntu handover.

---

## 8. Windows Git settings and hard-coded Linux paths

### 8.1 Settings (Windows, once, before the first checkout)

```
git config --global core.autocrlf false
git config --global core.longpaths true
git config core.filemode false            # in the repository; 11 files carry the executable bit
```

`.gitattributes` already contains `* text=auto eol=lf` and marks `*.png *.ogg *.mp3 *.wav` as binary, so the working tree is LF on Windows as well. Therefore:

- keep `core.autocrlf=false` (with `true`, Git would convert and show every file as changed against the committed LF);
- configure the editor to write LF;
- Python scripts that write files on Windows can emit CRLF; check `git diff --stat` after running any generator and `git checkout --` the files it should not have touched;
- clone to a short path (under about 150 characters; the longest tracked path is 93);
- install Godot 4.5.1 stable and set `GODOT` to the console executable; Git Bash for the `.sh` scripts; Python 3.11 or newer with `numpy`, `mido==1.3.3`, `pillow`; `ffmpeg` and `ffprobe` on `PATH`;
- do not rely on the Windows default inside `tools/test.sh` (`$USERPROFILE/Downloads/...`); set `GODOT` explicitly.

### 8.2 Hard-coded Linux paths Windows may fix (files Windows owns)

Line numbers are from the repository at the baseline.

| File and line | Content | Fix |
|---|---|---|
| `tools/audio_import/audio_io.py:15` | `FFMPEG = "/usr/bin/ffmpeg"` | `shutil.which("ffmpeg")`, falling back to the old path. Blocker for the importer and its tests on Windows. |
| `tools/audio_import/audio_io.py:16` | `FFPROBE = "/usr/bin/ffprobe"` | Same, `ffprobe`. |
| `tools/audio_import/import_track.py:700` | `--out` default `"/home/joe/rw-audio-work"` (code) | Default from `RW_AUDIO_WORK` if set, else the old value. |
| `tools/audio_import/import_track.py:4`, `:5`, `:7` | venv path in the usage text | Text only; change to `python`. |
| `tools/audio_import/play_track.sh:8` | Godot default `/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64` | Already overridden by `GODOT`; change the default to fail with a clear message if unset. |
| `tools/audio_import/play_track.sh:9` | `/home/joe/rw-audio-work` | Already overridden by `RW_AUDIO_WORK`. |
| `tools/audio_import/catalogue_tracks.py:411`, `:412` | `--packs` and `--cache` defaults under `/home/joe/rw-audio-work` | Default from `RW_AUDIO_WORK`. |
| `tools/audio_import/validate_track.py:5` | usage text path | Text only. |
| `tools/audio_import/test_audio_import.py:3` | venv path in the docstring | Text only. |
| `tests/fixtures/track_fixture/make_fixture.py:7` | docstring names `/usr/bin/ffmpeg` | Text only. |
| `tests/fixtures/track_fixture/make_fixture.py:105` | `subprocess.run(["/usr/bin/ffmpeg", ...` | `shutil.which("ffmpeg")`. Only needed to regenerate the fixture; its output is committed. |
| `src/track/README.md:11`, `:12` | Godot and pack paths in the usage example | Text only. |
| `content/music/tracks/catalogue.json:9` | `"packs_live_at": "/home/joe/rw-audio-work/packs"` (data string, informational) | Leave unless a tool reads it; if changed, change it to a placeholder such as `"$RW_AUDIO_WORK/packs"`. |

Not Windows' to fix (files it does not own or that are frozen); work around them or request:

| File and line | Content | Workaround |
|---|---|---|
| `tools/trial/walk_trial.sh:10` | `mktemp -d /tmp/claude-1000/walk_trial.XXXXXX` (Ubuntu's file) | Create the folder first, or request `${TMPDIR:-/tmp}`. |
| `tools/run/*.sh` (`frames`, `capture`, `capture_path`, `capture_choice`, `walk_run`) and the other scripts with the Linux Godot default `$HOME/godot/Godot_v4.5.1-stable_linux.x86_64` | Default only | All honour `GODOT` first; `export GODOT=...`. |
| `tools/story/rooms.sh:7`, `tools/story/shoot_preview.sh:8`, `README.md` (the `/tmp/balance.md` example) | `/tmp/...` | Works in Git Bash. |
| `tools/test.sh:5` | Windows default for `GODOT` | Set `GODOT`. |
| `export_presets.cfg:65` | `keystore/debug="C:/Users/joesa/AppData/Roaming/Godot/keystores/debug.keystore"` | Frozen; no export from either branch. |

---

## Assigned by this document

DECISIONS.md does not name these; the lead should check each.

| Assignment | Reason |
|---|---|
| `src/run/run_progress.gd` to Ubuntu | It is the save (`Session.run_progress`, `user://story_run.json`). |
| `src/core/session.gd` to Ubuntu | Autoload that holds `run_progress`; Windows needs nothing from it. |
| `src/duel/duel_network.gd`, other autoload-adjacent code: none | Neither task needs it. |
| `src/run/run_rail.gd`, `run_passage*.gd`, `choice_*.gd`, `run_acting.gd`, `run_hud.gd`, `run_levels.*`, `run_over.*`, `dev_text.gd`, `run_play.tscn` | Routing and visuals (`run_play.tscn` follows `run_play.gd`). |
| `src/audio/stem_transport.gd`, `src/core/song_clock.gd` to Windows | The transport and clock. |
| `src/run/run_card_table.gd`, `run_minigame_host.gd`, `run_wallet.gd`, `src/minigames/**`, `src/story/**`, `src/debug/**`, `src/ui/**`, `src/scenes/**`, other `src/core/**`: none | Unrelated to either task. |
| `content/run/run.json` key split in section 3 | DECISIONS.md assigns only the whole file. |
| `songs/**`, `content/story/music.json` to Windows | Music data the run plays. |
| `content/paths/*/music.json` stays with Ubuntu | D2 gives `content/paths/**` to Ubuntu; this is the one place music data sits in Ubuntu's folder. |
| `tools/run/**` (all but `coverage_audit.*` and `check_hotspots.py`) to Ubuntu; `measure_mix.py` and `transition_*` to Windows | D2 names only two files. |
| `tools/story/check_run_audio.py`, `check_music.py`, `record_music.gd`, `tools/trial/check_*audio.py` to Windows; `tools/trial/**`, `tools/paths/**` to Ubuntu | Audio checks vs builders. |
| `tools/test.sh`, `tools/content/**`, other shared tools: none | Shared runner and content tests. |
| Test file split in section 2.4, including `test_miss_mute`, `test_story_music_packs`, `test_story_recorded_music` to Windows and `test_run_*` (non-time-sliced) to Ubuntu | D2 names patterns for Ubuntu only. |
| Windows reserved test prefixes `test_transition_*`, `test_music_*`, `test_director_*`; `tests/test_port_real.gd` integration only | D2 names none for Windows. |
| `tests/fixtures/save_v2.json` to Ubuntu | Save-format fixture. |
| `assets/run/choice/**`, `assets/trial/art/**` to Ubuntu; `assets/audio/**` to Windows | Extension of "scene art". |
| Documents by topic in section 2.5; `docs/music/**`, `docs/narrative/**`, `docs/shots/<side>/**` | D0 names only the handover files. |
| `docs/parallel-development/requests/` file naming and `-reply` suffix, `graph/` folder | D2 gives the request name; the reply name is new. |
| Ubuntu commits no `.uid` for `src/transition/transition_port.gd` (excluded locally); Windows commits it | Avoids an add/add conflict on a machine-generated file. |
| Ubuntu takes later Windows work only by named tags (`w2-...`) | D2 covers W1 only. |

### Where the two sides genuinely overlap after W1

| Overlap | How this document handles it |
|---|---|
| `run_play.gd` and `run_engine.gd`: Windows needs further hooks for later transition modes. | Hooks are installed in W1; later needs are requests to Ubuntu. |
| `run.json` tuning keys (`energy.track`, `mix`, `stages`, `treatments`) belong to Ubuntu's file but to Windows' work. | Requests to Ubuntu; new tuning goes to `content/music/transitions/`. |
| `content/paths/*/music.json`: music data in Ubuntu's folder. | Windows requests. |
| `tests/test_run_tracks_safety.gd` and its baseline against Ubuntu's routing changes. | Section 5 point 5. |
| Door and walk timing (`run_journey.gd` constants) against blend length. | Windows requests; Ubuntu decides. |
| `src/transition/transition_port.gd.uid`. | Section 3, row 1. |
