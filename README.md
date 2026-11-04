# Rhythm Warfare

A rhythm game in landscape for phones: play four illuminated pads in time with a 174 BPM drum and bass track while your camera is carried through five small
2.5D, Doom-style worlds (a warehouse club, an alien mothership, an underworld arena, a night hospital, a ward). The story is one continuous run: every level is a
64-beat phase that starts with drums alone, brings the bass in as you play well, brings the drums back, then lets the bass take over while you choose which way to go
next. Good play keeps the mix building, a missed block holds it for another go, and the crowd's energy is the meter that ends the run if it runs out. Standalone Godot 4.5.1
project. Home has three buttons: Play, Start from a reached level, Settings.

* Design, route map, tunables and verification: `docs/CONTINUOUS_RUN.md`.
* Adding music (Beat Shaper exports, one command per level): `docs/MUSIC_IMPORT.md`; what each level plays and what to export: `docs/MUSIC_HANDOFF.md`.
* The 2.5D world, art and authoring pipeline: `docs/STORY_CAMPAIGN_HANDOVER.md`, `docs/STORY_25D_PLAN.md`, `docs/STORY_ART.md`.

```
godot --path .                                                         # home screen
godot --path . res://src/run/run_play.tscn                             # straight into the run (RW_RUN_START=<level id> picks the level)
RW_RUN_BOT=perfect RW_RUN_ROUTES=up,left godot --path . res://src/run/run_play.tscn   # scripted play: perfect | none | accuracy:<f> | blocks:<1011...>
RW_RUN_VIRTUAL=1 RW_RUN_BOT=perfect RW_RUN_UNTIL_PHASE=3 RW_STORY_QUIT=1 godot --headless --path . res://src/run/run_play.tscn   # no audio, stepped clock
godot --headless --path . -s tests/run_tests.gd -- --filter run_      # the run's tests
python tools/content/beatshaper.py validate                             # music data
godot --headless --path . -s tools/story/record_music.gd -- <out> 70 res://src/run/run_play.tscn   # record the Music bus of a real run
python tools/story/check_run_audio.py <out>                             # fit the recording to the mix the engine reported
```

The older chapter-by-chapter Story Campaign scenes, the military campaign and the legacy duel are no longer reachable from the home screen. Their code is still in the
repository (the art pipeline, the tests and the editor-only Developer button use it); the run does not depend on it. `docs/STORY_CAMPAIGN_HANDOVER.md` still describes it.

## Layout

- `src/` game code: `core/` (song clock, pack loading: `mission_loader.gd` for missions, `level_loader.gd` for the duel;
  `library_index.gd` and `loadout.gd` the loop library and the player's loadout; `match.gd` drives a run; `sequence_tracker.gd`, `mission_rules.gd`, `campaign.gd` saves and unlocks, `session.gd`
  settings), `audio/` (one synchronized transport for the loadout's looping stems), `input/` (`pad_judge.gd` for missions, `judge.gd` for the
  duel, `lane_input.gd` touches, section taps and keys), `sim/` (deterministic 25 Hz OpenRA battle simulation, no
  scene nodes; civilians, wave target classes, start units, the active section), `ui/` (`pad_view.gd` the pads,
  `note_lane.gd` the falling notes, `battle_view.gd` sprites only, `hud.gd` the legacy duel's bar only, `section_picker.gd`, `ui_style.gd`, `settings_panel.gd`),
  `audio/` (`stem_transport.gd` the song, `battle_sfx.gd` the Red Alert effects), `scenes/` (home, missions, mission
  briefing, loadout, play, result, settings, calibration, developer).
- `content/` the loop library (`library/<clip>/`: MIDI per part, owner WAV renders, generated placeholders), sounds,
  the ten slim mission files (`missions/`; `missions_legacy/` is the old authoring the MIDI exporter reads), fixtures;
  Godot ignores it. `tools/content/build.py` turns it into `songs/library/` and `songs/m01_*` to `m10_*`.
- `songs/` the built content: `library/` (`index.json` and 117 eight-bar Ogg loops in `loops/`), the mission packs
  (schema 4: `level.json` only, no audio) and the two legacy duel packs (`level_01`, `test_16`, schema 1).
- `data/` OpenRA rules, roster, maps, battlefields (`defense_02.json` the mission map with building sockets,
  `village_01.json` mission 1's village with the barracks, houses and civilians), `sfx_map.json` (simulation event
  to sound), `campaign/` (`campaign.json` the mission ladder and unlocks, `rules.json` the rule set, `instruments.json` what each
  sound builds, `loadouts.json` the default and heavy presets for the tools, `waves/` per mission).
- `assets/openra/` Red Alert sprite frames at native pixel size, sequences and provenance; `assets/sfx/` the Red Alert
  sound effects and EVA lines as Ogg (`tools/extract_openra_sounds.py`).
- `campaign/` the owner's original starter pack (First_Three MIDI is the default content of missions 1 to 3; never edit it).
- `tools/` authoring scripts; `tests/` headless GDScript tests; `tools/content/test_content.py` the content build tests.

## Running

Godot 4.5.1: open `project.godot` and press Play, or run the Windows build from `build/windows/` (`docs/EXPORT.md`).
Desktop keys: D F J K = pads 1 to 4, Esc = pause, F3 = debug line.

```
bash tools/test.sh                                   # all headless tests + the content build tests
python tools/content/import_ableton.py content/imports/first_watch.json   # file your Ableton exports (ToAddTry1/) into content/library
python tools/extract_openra.py --no-map              # sprites from your OpenRA content (allow-list in the script)
python tools/extract_openra_sounds.py                # Red Alert sounds into assets/sfx
python tools/campaign/build_battlefield.py           # regenerate the maps and battlefields (add village_01 for the village only)
python tools/content/build.py                        # rebuild the loop library and every mission pack from content/ (about 23 s)
python tools/content/render_list.py                  # rewrite docs/CONTENT_TO_RENDER.md
python tools/balance_missions.py > /tmp/balance.md   # seeded trials, every mission (docs/BALANCE.md); --loadout heavy for the other preset
RW_SEEDS="1 2 3" bash tools/balance.sh res://songs/m03_hold_the_line 1.0 perfect beginner sloppy none   # one mission
RW_MISSION=3 RW_SCENE=play RW_AUTOPLAY=perfect godot --path .    # scripted run in the real play screen, prints PERF
RW_UNLOCK_ALL=1 godot --path .                       # every mission and option open for one run (developer switch)
```

Screenshots: `godot --path . -s tools/shoot.gd -- res://src/scenes/mission_setup.tscn <out_dir> 20:shot:name`; the play
screen of a mission: `RW_MISSION=1 RW_SCENE=play RW_AUTOPLAY=perfect godot --path . -s tools/shoot.gd -- res://src/scenes/main_menu.tscn <out_dir> 400:touch:200,250 405:release:200,250 500:shot:left_flag`.

## Documents

`docs/HANDOVER.md` (start here: state, decisions, what was verified and what was not), `docs/PRD.md` (sections 15 and 16 the
mission rules and the loadout model; 1 to 13 the duel), `docs/CONTENT_TO_RENDER.md` (every WAV and MIDI to make in Ableton),
`docs/BALANCE.md` (seeded trials, coverage and tuning), `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (the brief this
build implements), `docs/EXPORT.md` (Android and Windows builds), `docs/TIMING.md`, `docs/OPENRA_BEHAVIOUR_SPEC.md`,
`content/README.md`, `songs/README.md`.
