# Rhythm Warfare

Play a drum and bass track to command an army. Kicks make tanks, snares make infantry, bass holds build and launch helicopters.
Standalone Godot 4.5 project; the PRD is the design authority (`docs/PRD.md`).

## Layout

- `src/` game code: `core/` (clock, level loading), `audio/` (four-stem transport), `chart/` (JSON chart, scheduling), `input/` (touch and key judgement), `sim/` (deterministic battle simulation, no scene nodes), `ui/` (lanes, buttons, HUD), `scenes/` (entry points).
- `assets/openra/` Red Alert sprites plus `catalogue.json` and `PROVENANCE.md`; regenerate with `python -I tools/import_openra_assets.py`.
- `data/openra_rules.json` actor, weapon, locomotor and repair values at the pinned OpenRA commit.
- `songs/<pack>/` a song pack: `level.json` plus `audio/` stems.
- `tools/` authoring and import scripts (Python 3). `tests/` headless GDScript tests.

## Running

Godot 4.5.1: open `project.godot`, or headless `godot --headless --path . --quit-after 3`.
