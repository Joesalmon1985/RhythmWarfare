# Rhythm Warfare

A rhythm defense game in landscape for phones: play four illuminated instrument pads in time with a 174 BPM drum and bass
track; every completed sequence builds one defense (a pillbox, a turret, a flame tower) or sends one unit to hold an
approach, and your Red Alert base in the middle of the screen must survive the enemy waves until the song ends. Ten
missions, each a battlefield, a set of waves and a form of drum and bass phases; the music is your one loadout (drum
pattern, fill, kick, snare, bass line, bass sound, backing track), played from a loop library in every mission, and its
instruments decide what a passed sequence builds (kicks make infantry, snares defenses, bass sounds vehicles). The older
two-sided duel stays in the developer area for a later multiplayer mode. Standalone Godot 4.5.1 project; the rule set is
`docs/PRD.md` sections 15 and 16 and `data/campaign/rules.json`.

## Story Campaign (Night One)

A separate mode on the main menu: `Story Campaign` > `Night One` is the first drum and bass set played from the DJ's position at a
fixed, illustrated nightclub with an animated crowd. It plays the same 128-bar First Watch music (the global Loadout), the same four
pads, falling notes and judgement; the two-bar sequence results drive the crowd's energy, three authored good/bad moments and one of
three endings. Saves are separate (`user://story_campaign.json`); the military campaign is untouched. See
`docs/STORY_CAMPAIGN_HANDOVER.md` (architecture, tuning, art pipeline, tests) and `docs/STORY_CAMPAIGN_PRD.md` (the brief).

```
godot --path . res://src/scenes/story_play.tscn                       # straight into Night One
bash tools/story/capture.sh                                            # real screenshots of the running scene (docs/shots/story)
python3 tools/story/build_assets.py                                    # regenerate only the original story art
godot --headless --path . -s tools/story/tune.gd -- perfect none       # endings under scripted skill levels
```

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
