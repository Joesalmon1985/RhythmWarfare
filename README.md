# Rhythm Warfare

Play a drum and bass track to command an army. Kicks make tanks, snares make infantry, bass holds build and launch helicopters.
Standalone Godot 4.5 project; the PRD is the design authority (`docs/PRD.md`).

## Layout

- `src/` game code: `core/` (clock, level loading), `audio/` (four-stem transport), `chart/` (JSON chart, scheduling), `input/` (touch and key judgement), `sim/` (deterministic battle simulation, no scene nodes), `ui/` (lanes, buttons, HUD), `scenes/` (entry points).
- `assets/openra/` Red Alert sprite frames at native pixel size plus `sequences.json` (every OpenRA sequence resolved to frame tables), `catalogue.json` (the player-colour ramp) and `PROVENANCE.md`; regenerate with `python -I tools/extract_openra.py` (needs the pinned OpenRA checkout and the Red Alert content; see the provenance file).
- `data/maps/strip_53x20.json` the temperate map (tiles, tree clumps, blocked cells) the battlefield layout `data/battlefields/mvp_mirrored_01.json` sits on.
- `src/sim/bot_ai.gd` OpenRA's Rush AI squad manager, driving both sides' units; `docs/OPENRA_BEHAVIOUR_SPEC.md` is the engine-sourced specification it and the unit behaviour follow, with the deviations noted in code.
- `data/openra_rules.json` actor, weapon, locomotor and repair values at the pinned OpenRA commit.
- `songs/<pack>/` a song pack: `level.json` plus `audio/` stems.
- `tools/` authoring and import scripts (Python 3). `tests/` headless GDScript tests.

## Running

Godot 4.5.1: open `project.godot` and press Play, or run the Windows build from `build/windows/` after exporting
(`docs/EXPORT.md`). Keys on desktop: F = kick, Space = bass (hold), J = snare, Esc = pause, F3 = debug panel with
the stem mute toggles.

- Tests: `bash tools/test.sh` (headless; refreshes the class cache, then `tests/run_tests.gd`).
- Balance runs: `bash tools/balance.sh res://songs/level_01 1.0 perfect "accuracy:0.85" none` (see `docs/BALANCE.md`).
- Scripted play in the real level screen: `RW_PACK=res://songs/level_01 RW_AUTOPLAY=perfect godot --path .`
  prints a `PERF` line with p95 frame time and peak live units at the end (A13 evidence on a phone via logcat).
- Screenshots: `godot --path . -s tools/shoot.gd -- res://src/scenes/play.tscn docs/shots 300:shot:name`.

## Handover

Start with `docs/HANDOVER.md`: milestone state, settled decisions, code map, deliberate deviations and the polish backlog.

## Design documents

`docs/PRD.md` (the product requirements), `docs/TIMING.md` (clocks and offset signs), `docs/BALANCE.md`
(enemy schedule evidence), `docs/OPENRA_BEHAVIOUR_SPEC.md` (unit and bot behaviour from the OpenRA source), `docs/EXPORT.md` (Android and Windows builds), `assets/openra/PROVENANCE.md`.
