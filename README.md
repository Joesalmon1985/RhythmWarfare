# Rhythm Warfare

A rhythm defense game: play a chart on four unlabelled buttons and every note you hit builds a group of Red Alert units
(the recipe of the instrument equipped in that note's slot) that holds one of three defense points; survive the enemy
waves until the song ends. Three campaign levels with a loadout screen, saved progress and unlocks; the older two-sided
drum and bass duel remains as "Free play". Standalone Godot 4.5 project; the PRD is the design authority
(`docs/PRD.md`, section 14 for the campaign).

## Layout

- `src/` game code: `core/` (clock, level loading), `audio/` (four-stem transport), `chart/` (JSON chart, scheduling), `input/` (touch and key judgement), `sim/` (deterministic battle simulation, no scene nodes), `ui/` (lanes, buttons, HUD), `scenes/` (entry points).
- `assets/openra/` Red Alert sprite frames at native pixel size plus `sequences.json` (every OpenRA sequence resolved to frame tables), `catalogue.json` (the player-colour ramp) and `PROVENANCE.md`; regenerate with `python -I tools/extract_openra.py` (needs the pinned OpenRA checkout and the Red Alert content; see the provenance file).
- `data/maps/strip_53x20.json` the temperate map (tiles, tree clumps, blocked cells) the battlefield layout `data/battlefields/mvp_mirrored_01.json` sits on.
- `src/sim/bot_ai.gd` OpenRA's Rush AI squad manager, driving both sides' units; `docs/OPENRA_BEHAVIOUR_SPEC.md` is the engine-sourced specification it and the unit behaviour follow, with the deviations noted in code.
- `data/openra_rules.json` actor, weapon, locomotor and repair values at the pinned OpenRA commit.
- `songs/<pack>/` a song pack: `level.json` plus `audio/` stems. `first_watch`, `second_pulse` and `hold_the_line` are the schema 2 campaign levels (placeholder audio), `level_01` and `test_16` the legacy duel packs.
- `data/campaign/` the campaign (ten levels, three playable) and the tuned waves; `data/instruments/catalogue.json` the instrument profiles and unit recipes; `data/battlefields/defense_01.json` the defense map.
- `tools/` authoring and import scripts (Python 3); `tools/campaign/` builds the campaign packs from the owner's MIDI (`build_defense_pack.py`), derives waves and checks rendered audio. `tests/` headless GDScript tests.
- `campaign/` the defense campaign starter pack (29 Oct 2026): first-three musical MIDI per slot, section focus maps, compiled reference charts, proposed waves, instrument catalogue, ten-level plan and the reference authoring tools. Source data, not docs; `.gdignore` keeps Godot out of it.

## Running

Godot 4.5.1: open `project.godot` and press Play, or run the Windows build from `build/windows/` after exporting
(`docs/EXPORT.md`). Keys on desktop: D, F, J, K = buttons 1 to 4 (kick on D, snare on K, bass holds on whichever
button the note is on), Esc = pause, F3 = debug panel with the stem mute toggles.

- Tests: `bash tools/test.sh` (headless; refreshes the class cache, then `tests/run_tests.gd`).
- Rebuild the campaign packs and placeholder stems: `python tools/campaign/build_defense_pack.py all` (needs `pip install mido==1.3.3`, numpy, ffmpeg).
- Balance runs: `RW_CHART=level_03.campaign RW_SEEDS="1 2 3" bash tools/balance.sh res://songs/hold_the_line 1.0 perfect "accuracy:0.85" none` (see `docs/BALANCE.md`).
- Scripted play in the real level screen: `RW_PACK=res://songs/hold_the_line RW_CHART=level_03.campaign RW_AUTOPLAY=perfect RW_SCENE=play godot --path .`
  prints a `PERF` line with p95 frame time and peak live units at the end (a normal run prints it too; phone via logcat).
- Rhythm-only playtest of any chart: `RW_PACK=res://songs/second_pulse RW_CHART=level_02.practice RW_BATTLE=off godot --path .`
- Screenshots: `godot --path . -s tools/shoot.gd -- res://src/scenes/play.tscn docs/shots 300:shot:name`.

## Handover

Start with `docs/HANDOVER.md`: milestone state, settled decisions, code map, deliberate deviations and the polish backlog.
The defense campaign was built from `docs/CAMPAIGN_PLAN.md` (`docs/NEXT_AGENT_PROMPT.md` was its brief); the handover lists every divergence and what was and was not verified.

## Design documents

`docs/PRD.md` (the product requirements), `docs/TIMING.md` (clocks and offset signs), `docs/BALANCE.md`
(duel schedule evidence and the campaign balance tables), `docs/OPENRA_BEHAVIOUR_SPEC.md` (unit and bot behaviour from the OpenRA source), `docs/EXPORT.md` (Android and Windows builds), `assets/openra/PROVENANCE.md`.
