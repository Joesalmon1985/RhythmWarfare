# Defense campaign: implementation plan

> **Superseded on 31 October 2026.** This plan built the schema 2 campaign (per-note production, instrument recipes, a lane
> view). `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` replaced that model with pads, sequences and ten missions; the rules are
> `docs/PRD.md` section 15 and the current state is `docs/HANDOVER.md`. Kept for the record.


Written 29 October 2026 after reading the starter pack (`campaign/`) against the code on `main` at commit
`3b84de2`. This is the working plan for the next agent. The owner's decisions in
`campaign/Claude_Defense_Campaign_Prompt.md` are the requirements; this document maps them onto the existing
code, fixes the problems found in the pack, and orders the work so each stage leaves `main` playable and green.

Read in this order: `docs/HANDOVER.md` (what exists), this file, `campaign/START_HERE.md`,
`campaign/Defense_Campaign_Design_and_Workflow.md`, `campaign/Rhythm_Game_Research_and_Refinements.md`,
`campaign/Plan/*.json`, then one level folder under `campaign/First_Three/`.

## 1. Where the pack lives and what it is

| Path | What | Status |
| --- | --- | --- |
| `campaign/First_Three/level_0N/Music/*.mid` | The complete musical parts per slot (kick_1, kick_2, snare_1, bass_1, other_*) | Source of truth; never edit; SHA-256 in `campaign/Musical_Source_Integrity.json` |
| `campaign/First_Three/level_0N/song.json` | Parts, slots, default loadout, export recommendation | Authoring input |
| `campaign/First_Three/level_0N/chart_rules.json` (+ `chart_rules.practice.json` for level 2) | Section focus map, button placement, thumb constraints, explicit overrides | Authoring input |
| `campaign/First_Three/level_0N/player_chart.json` | Compiled chart (64 / 96 / 89 events; level 2 practice 80) | Reference output; the in-repo build must reproduce it exactly |
| `campaign/First_Three/level_0N/waves.proposed.json` | Enemy waves | Untuned; entries and timing must change (section 4) |
| `campaign/Plan/instrument_catalogue.proposed.json` | 11 instrument profiles with recipes and producer tags | Design examples; becomes `data/instruments/catalogue.json` |
| `campaign/Plan/campaign.proposed.json` | Ten levels, caps 2/2/3, unlock policy | Becomes `data/campaign/campaign.json` |
| `campaign/Plan/defense_rules.proposed.json`, `chart_design_refinement.proposed.json` | Rule statements | Read; encode in code and tests |
| `campaign/Authoring_Tools/*.py` | Reference converter, validator, example generator (`mido==1.3.3`) | Move to `tools/campaign/`; the validator's relative paths then point at `campaign/` |
| `campaign/.gdignore` | Keeps Godot from importing the pack's CSV files as translations | Keep |

`mido` is not installed on this machine (Python 3.14, numpy 2.4, ffmpeg on PATH). Install it with
`pip install mido==1.3.3` before running the reference tools. Run project scripts as `python tools/campaign/x.py`;
`python -I` drops the script directory from `sys.path`, so a script that imports a sibling must add its own directory
to `sys.path` explicitly.

## 2. What changes in the code, file by file

The current game is a two-sided duel (schema 1, four fixed stems, `lane` decides production, Rush AI on both sides,
win by destroying the enemy construction yard). The campaign is a one-sided defense. Keep the duel path loadable as a
legacy mode behind `schema_version` 1 while the campaign is built: the existing 425 headless checks are the regression
net for the simulation, the judge and the transport, and `songs/level_01` and `songs/test_16` keep working. Retire
the duel path only when the owner asks.

| File | Change |
| --- | --- |
| `src/core/level.gd`, `src/core/level_loader.gd` | `schema_version` 2 with `mode: "defense"`. Notes carry `button` (required, 1-4), `slot_id`, `part_id`, `source_note_id`, `family`; no `lane`, no default buttons, no fixed kick/snare buttons. Sections carry `mode: drums|bass`; whole-bar exclusivity including hold tails is an error. `stems` is keyed by slot id plus `other`; `renders` maps slot -> profile -> file with `source_sha256`, `sample_rate`, `frames`, `placeholder`. `charts` holds one or more charts (`chart_id`, `play_mode`, `notes`); the loader selects one. `waves`, `objectives`, `defense_points`, `loadout` (active slots, default profiles). Thumb check: a note on button 2 while button 1 is held (or 3 while 4, and the reverse) is an error; same-thumb gaps under 960 ticks after a tap or 480 after a hold end are warnings. Keep the stem length check (all streams equal, covering `duration_ticks`). |
| `src/input/judge.gd` | Availability and reward counts keyed by `slot_id` instead of lane; `set_slot_available(slot_id, bool)`. Matching stays by button. Everything else (windows, holds rewarded once at the tail, pause voids holds) is already right. |
| `src/audio/stem_transport.gd` | Generic over the level's stem keys (3 to 8 streams; `AudioStreamSynchronized` allows 32). One player, one playhead, per-stream gain ramps as now. |
| `src/core/match.gd` | Reward -> `slot_id` -> equipped profile -> recipe step (deterministic per-slot counter, advanced only on a successful available reward) -> `sim.produce_group(0, units, group_id, point)`. Round-robin defense point advanced once per successfully queued group; `production_log` records `group_id`, `point`, `slot_id`, `profile_id`, units. Per-slot muting from the profile's `required_producers`. Outcome: `end_by_song()` now means survival. Waves scheduled by time, bypassing producers. Practice charts: no waves, no progression, no persistent rewards. |
| `src/sim/battle_sim.gd` | `setup` takes objectives, defense points, entries and an AI choice per side. `produce_group(side, units, group_id, point)` checks each actor's producer through `build_at` in `data/openra_rules.json` (the catalogue's `barracks` / `war_factory` / `air_support` tags map onto roles `barracks` / `factory` / pads) and queues the units with their group id. `spawn_wave_group(side, actor, count, spacing_ticks, entry, via, objective)` spawns at the entry with no producer. `_check_outcome` in defense mode: any required objective dead -> `defeat`, reason `objective_destroyed:<id>`; `end_by_song()` -> `victory`, reason `survived`. Same-tick order is already right (ticks, then the song-end check in `Match.advance`); add the test. |
| `src/sim/defense_ai.gd` (new) | Side 0: a group walks to its point, engages within a leash (about 6 cells), returns after a short pursuit. Side 1: each wave unit attack-moves to its via point, then to its objective, fighting what it meets (`attack_move` and `resume_attack_move` exist). Leave `bot_ai.gd` for the legacy duel. |
| `data/battlefields/defense_01.json` (new) | One base on the left (reuse the player half of `mvp_mirrored_01`), `objectives: [{"id": "command_core", "role": "main"}]`, three `defense_points`, three `entries`. See section 4 for placement. Lightly defended at level 1 (walls and the two pillboxes at the opening; no gun turrets or SAM sites) so that no input loses. Later levels add defenses through battlefield variants, not through bigger waves alone. |
| `data/instruments/catalogue.json`, `data/campaign/campaign.json` (new) | From the pack's `Plan/` files, with `.proposed` dropped once the loader validates them: every recipe actor exists in `openra_rules.json` and in `assets/openra/sequences.json`; caps 2/2/3; distinct profiles within a family. |
| `src/core/campaign.gd` (new) | Progress in `user://campaign.json` (`version`, `cleared` with best results, `unlocked_profiles`, `loadouts` per level). Atomic write: temp file then `DirAccess.rename_absolute`; a corrupt file is kept as `.bad` and replaced. Clearing level n unlocks n+1 and its entry profiles. Replays never reset; practice never writes. |
| `src/scenes/loadout.gd/.tscn` (new), `main_menu`, `result` | Campaign level list (locked levels greyed), loadout screen per level (slot rows, locked profiles show "unlocks after level N", unit mix text, validation), Play and Practice buttons, a result screen that reports the clear and the unlocks. The legacy pack list stays as "Free play". |
| `src/ui/lane_view.gd`, `src/ui/hud.gd` | `LOOKAHEAD_S` becomes `Session.lookahead_s` (default 2.2, saved in settings, adjustable from the menu); a DRUMS / BASS cue scrolls in one bar before a focus change; hold progress is already available (`active_hold_progress`). HUD in defense mode: objective health, wave warning, groups per point; no enemy base bar. |
| `src/core/session.gd`, `src/scenes/play.gd` | Session carries `chart_id`, loadout and lookahead. `RW_CHART=level_02.practice`, `RW_BATTLE=off` (hide the battlefield; the rhythm-only playtest). `_on_song_finished` becomes a fallback only: the stems carry a one-bar tail, so survival resolves at `duration_ticks`, not at audio end. |
| `tools/campaign/build_defense_pack.py` (new) | One command per level: compile every chart from the part MIDIs and rules (must equal the pack's `player_chart.json` note for note), synthesise placeholder stems per part (reuse the synth functions in `tools/make_song_pack.py`), encode Ogg, write `level.json` v2 with hashes and the render manifest, validate like the loader. `tools/campaign/audio_preflight.py` for owner WAVs: exists, decodes, same rate and frame count, covers the chart, peak level, hash provenance, and prints the listening timestamps (start, each focus change, end). |
| `tools/autoplay.gd`, `tools/balance.sh` | Chart selection, loadout, objective health timeline, per-wave arrival and clear times, groups per point; policies perfect / 0.85 / 0.6 / none over seeds 1-3. |
| `tests/` | New: `test_defense_loader.gd`, `test_defense_match.gd`, `test_defense_sim.gd`, `test_campaign.gd`, `test_catalogue.gd`. Existing tests stay green (legacy mode). |
| Docs | `docs/PRD.md` gets a section 14 "Defense campaign (supersedes 2, 5, 6 and 9 for schema 2 packs)"; `songs/README.md` describes schema 2; `docs/BALANCE.md` gains the campaign tables; `docs/HANDOVER.md` is rewritten at the end. |

## 3. Design calls that improve on the pack

1. **Same branch.** The owner wants this on `main`: commit at the end of every stage with tests green, push each time.
2. **The rhythm-only playtest is practice mode with the battlefield hidden**, not a separate screen. Build the loader,
   importer, transport and judge first; the playtest falls out of them and stays useful afterwards.
3. **Keep the duel path as legacy** rather than deleting it mid-build. Delete it at the end only on the owner's word.
4. **Producer gating by actor, not by family.** `openra_rules.json` already says where every actor is built
   (`build_at`, `queue`). A recipe is available when every actor in its next step has its producer alive; the
   catalogue's `required_producers` tags must agree with that and the loader checks they do.
5. **Entries are not the map edge.** Riflemen cover about 1.3 cells per second, jeeps about 4.0. Place each entry so
   infantry reach the wall opening in roughly 10-12 seconds (about 14-16 cells out; `x` near 30 on the 53-cell
   strip, or crop the map to about 36 cells wide and keep the base as it is). Print the travel time per actor in
   the pack build so the wave author can see it. The pack's wave ticks assume arrival soon after spawn; with correct
   travel times the last authored waves of every level still arrive before the deadline, and the four opening bars
   plus travel give the player time to build before first contact.
6. **Defense points in a shallow arc that all cover the one corridor** (for example cells (19,5), (20,10) and
   (19,15) on the current layout, in front of the wall opening at rows 6-13), with the group leash reaching the
   corridor from every point. Round-robin assignment is the owner's rule; this placement keeps groups at points 1
   and 3 useful even when a level's waves all come through the centre.
7. **Lighter static defenses at level 1.** The fortified duel base (two gun turrets, two SAMs, pillboxes) would hold
   seven rifle waves on its own and the "no input loses" acceptance would fail. Start with walls plus the two
   pillboxes and add the rest through later battlefields.
8. **Thumb rules split into errors and warnings.** Same-thumb hold-plus-tap is a chart error (the loader rejects it).
   The 960 / 480 tick gaps are authoring targets awaiting phone testing, so they are warnings that the build prints.
9. **One build command, exact reproduction as the test.** The repo build must reproduce the pack's compiled charts
   byte-for-byte in their note lists (64 / 96 / 89 and the 80-note practice chart). That is the regression test for
   the importer and the proof the pack and the game agree.
10. **Stem files are per slot and per profile** (`audio/kick_1__kick_march.ogg`). Swapping a profile swaps a file.
    A profile with no render for a song's part is shown locked for that song, with the reason.

## 4. Stages, each a commit on `main` with tests green

**Stage 0, tooling and contract (small).** Move the three reference scripts to `tools/campaign/`, fix the
validator's root path, install `mido`, rerun the pack's validator and confirm the 102 checks still pass from
`campaign/`. Write the schema 2 contract into `docs/PRD.md` section 14 and `songs/README.md` before writing code.

**Stage 1, rhythm feel.** Importer and placeholder stems for all three levels (`songs/first_watch`,
`songs/second_pulse`, `songs/hold_the_line`), loader v2, judge by slot, generic transport, lookahead setting, focus
cue, practice mode with the battlefield hidden. Done when: all three packs load with aligned stems; level 2 practice
(80) and campaign (96) charts play over the same audio with separate chart ids; level 3's bass holds run across all
four buttons with full lengths and the alternating-thumb placement; pause, resume and calibration still work; the
owner can play it on Windows.

**Stage 2, the defense battle.** Battlefield, objectives, entries, defense points, waves with travel-time-aware
entries, defender and wave AI, outcome rules, HUD, balance harness. Done when: level 1 is playable end to end;
no-input loses to the waves; perfect play survives; the same-tick tie resolves as a loss; the headless harness
prints objective health and wave outcomes.

**Stage 3, instruments and production.** Catalogue, recipes, per-slot counters, group round-robin with group ids in
the log, producer gating and per-slot muting with gain restored in place, air-support profile type recognised but
not used by levels 1-3. Done when: a kick profile produces infantry and another alternates vehicles regardless of
button; the same bass slot produces its group on each of buttons 1-4; unavailable notes are inert, excluded from
accuracy and do not advance counters; a destroyed core still ends the run.

**Stage 4, campaign and loadout.** Campaign data, save file, unlocks, level list, loadout screen with validation
and locked choices, result screen, settings. Done when: a first clear unlocks the next level and its profiles;
replaying never resets; practice writes nothing; the save survives a corrupt file; loadout rejects duplicate
profiles in a family, wrong families, missing required slots and caps beyond 2/2/3.

**Stage 5, levels 2 and 3, balance and evidence.** Waves and recipes tuned per level with the harness (perfect and
0.85 survive, none fails, 0.6 reported honestly, seeds 1-3); tables in `docs/BALANCE.md`; Windows and Android
exports; `PERF` line on desktop; phone run left to the owner with exact instructions; docs and handover rewritten.

## 5. Acceptance tests to write (names are suggestions)

- Loader: rejects `lane`, missing `button`, mixed drum/bass bars including hold tails, same-thumb hold-plus-tap,
  a hold crossing a focus change, a wave after the deadline, a recipe actor without a producer, a render whose hash
  does not match; warns on thumb gaps and on placeholder renders; loads all three packs and the practice chart.
- Importer: the in-repo compile of each level equals the pack's `player_chart.json` notes; the 18 MIDI hashes are
  unchanged; placeholder stems have equal frame counts and cover `duration_ticks` plus the tail bar.
- Match: hold reward once at the tail; miss on an uncharted accompaniment note never happens (there is no such
  note); unavailable slot excluded from accuracy and counters; muting per slot and gain restored at the current
  position; focus change never mutes; practice chart produces no waves and no progression write.
- Sim: survival victory at `duration_ticks` with enemies alive; defeat the moment the core dies; same-tick tie is a
  defeat; waves spawn without producers and with authored spacing; groups keep together and the point advances
  only on a successful queue; a kick profile with an infantry recipe produces infantry from button 1 and from
  button 3 alike.
- Campaign: clear, unlock, replay, corrupt save, loadout validation.
- Determinism: same seed and trace, same production log (already a test in duel mode; add the defense version).

## 6. Open questions for the owner (proceed with the defaults in brackets)

- Level 1 static defenses: walls plus two pillboxes only [yes].
- Keep the old duel packs in the menu under "Free play" [yes, until told otherwise].
- Default lookahead 2.2 s and a slider from 1.2 to 3.0 s [yes].
- Pack folder names `first_watch`, `second_pulse`, `hold_the_line` with campaign ids `level_01..03` [yes].

## 7. Known environment facts

Godot 4.5.1 console binary: `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe`
(`tools/test.sh` and `tools/balance.sh` default to it). New `class_name` scripts need `--import` before headless
runs (`test.sh` does it). Untyped `var x := dict["k"]` is a parse error in 4.5; annotate the type. Long quoted
Python inside Bash heredocs fails in this shell; write scripts to a file and run them. Exports per `docs/EXPORT.md`;
the owner sideloads the APK and reports. `DuelMasterBattle` is an asset source only, never edited.
