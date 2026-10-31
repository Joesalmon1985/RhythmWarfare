# Rhythm Warfare

A rhythm defense game in landscape for phones: play four illuminated instrument pads in time with a 174 BPM drum and bass
track; every completed sequence builds one defense (a pillbox, a turret, a flame tower) or sends one unit to hold an
approach, and your Red Alert base in the middle of the screen must survive the enemy waves until the song ends. Ten
missions, each an arrangement of a loop library with a few musical choices of your own. The older two-sided duel stays
in the developer area for a later multiplayer mode. Standalone Godot 4.5.1 project; the rule set is `docs/PRD.md`
section 15 and `data/campaign/rules.json`.

## Layout

- `src/` game code: `core/` (song clock, pack loading: `mission_loader.gd` for missions, `level_loader.gd` for the duel;
  `match.gd` drives a run; `sequence_tracker.gd`, `mission_rules.gd`, `campaign.gd` saves and unlocks, `session.gd`
  settings), `audio/` (one synchronized transport for all stems), `input/` (`pad_judge.gd` for missions, `judge.gd` for the
  duel, `lane_input.gd` touches and keys), `sim/` (deterministic 25 Hz OpenRA battle simulation, no scene nodes), `ui/`
  (`pad_view.gd` the pads, `battle_view.gd`, `hud.gd`, `ui_style.gd`, `settings_panel.gd`), `scenes/` (home, missions,
  mission setup, play, result, settings, calibration, developer).
- `content/` the loop library (`library/<clip>/`: MIDI per part, owner WAV renders, generated placeholders), sounds,
  the ten mission files, fixtures; Godot ignores it. `tools/content/build.py` turns it into `songs/m01_*` to `m10_*`.
- `songs/` the built mission packs (schema 3: `level.json`, `audio/` stems, `preview/` auditions) and the two legacy duel
  packs (`level_01`, `test_16`, schema 1).
- `data/` OpenRA rules, roster, maps, battlefields (`defense_02.json` is the mission map with building sockets),
  `campaign/` (`campaign.json` the mission ladder and unlocks, `rules.json` the rule set, `waves/` per mission).
- `assets/openra/` Red Alert sprite frames at native pixel size, sequences and provenance.
- `campaign/` the owner's original starter pack (First_Three MIDI is the default content of missions 1 to 3; never edit it).
- `tools/` authoring scripts; `tests/` headless GDScript tests; `tools/content/test_content.py` the content build tests.

## Running

Godot 4.5.1: open `project.godot` and press Play, or run the Windows build from `build/windows/` (`docs/EXPORT.md`).
Desktop keys: D F J K = pads 1 to 4, Esc = pause, F3 = debug line.

```
bash tools/test.sh                                   # all headless tests + the content build tests
python tools/content/build.py                        # rebuild every mission pack from content/ (placeholders and your renders)
python tools/content/render_list.py                  # rewrite docs/CONTENT_TO_RENDER.md
python tools/balance_missions.py > /tmp/balance.md   # seeded trials, every mission (docs/BALANCE.md)
RW_SEEDS="1 2 3" bash tools/balance.sh res://songs/m03_hold_the_line 1.0 perfect beginner sloppy none   # one mission
RW_MISSION=3 RW_SCENE=play RW_AUTOPLAY=perfect godot --path .    # scripted run in the real play screen, prints PERF
RW_UNLOCK_ALL=1 godot --path .                       # every mission and option open for one run (developer switch)
```

Screenshots: `godot --path . -s tools/shoot.gd -- res://src/scenes/mission_setup.tscn <out_dir> 20:shot:name`.

## Documents

`docs/HANDOVER.md` (start here: state, decisions, what was verified and what was not), `docs/PRD.md` (section 15 the
mission rules; 1 to 13 the duel), `docs/CONTENT_TO_RENDER.md` (every WAV and MIDI to make in Ableton),
`docs/BALANCE.md` (seeded trials, coverage and tuning), `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (the brief this
build implements), `docs/EXPORT.md` (Android and Windows builds), `docs/TIMING.md`, `docs/OPENRA_BEHAVIOUR_SPEC.md`,
`content/README.md`, `songs/README.md`.
