# Rhythm Warfare

A rhythm game in landscape for phones: play four illuminated pads in time with a 174 BPM drum and bass track while your camera is carried through five small
2.5D, Doom-style worlds (a warehouse club, an alien mothership, an underworld arena, a night hospital, a ward). The story is one continuous run: every world is a
series of rooms (scenes) and each scene is a 64-beat phase that starts with drums alone, brings the bass in as you play well, brings the drums back, then lets the bass take over while you choose which way to go
next. Good play keeps the mix building, a missed block holds it for another go, and the crowd's energy is the meter that ends the run if it runs out. Standalone Godot 4.5.1
project. Home has six buttons: Play (the run), Story chapters (the finished chapter-by-chapter campaign, with its own saves), Start from a reached level, Wizard Duel (wifi) (two phones or windows on one network, or practise alone), Settings, Debug / Playtest (pick any of the 82 scenes, see exactly which song files and visuals it uses, and log what you do not like: `docs/DEBUG_MODE.md`).
Three more adventures branch off the Warehouse (the Gospel at 124 BPM, the Mission Count at 140, the Ember Road at 145; see below). Inside the run the camera rides a rail through each world: a pass at a block steps you one place up the room (floor, steps, stage, balcony, booth), a miss steps you down
the bad rail (floor edge, corridor, cubicle), and the route window lights the room's exits, doorways and things in the world to touch (no arrows, no written choices). Each world is a small graph of rooms with paths to choose between
(the Warehouse floor > bar or balcony > chill-out or booth > the door; 3 to 5 phases, 66 to 110 s, each room with its own variant of the world's music); a path inside a world is a plain
door walk, a change of world keeps the passage frame.

* Playtesting: the home screen's **Debug / Playtest** lists every scene of the run and the three paths with the audio files and visual ids in use, and writes your "don't like the music / visuals" notes to a file you can paste back: `docs/DEBUG_MODE.md` (`python tools/run/playtest_notes_summary.py <notes.jsonl>` ranks them).
* Design, route map, rails, paths, portals, tunables and verification: `docs/CONTINUOUS_RUN.md`; the plan and its progress log: `docs/RUN_DUNGEON_MUSIC_PLAN.md`.
* Adding music (Beat Shaper exports, one command per level): `docs/MUSIC_IMPORT.md`; what each level and path plays and what to export (the Gospel and Ember prompts): `docs/MUSIC_HANDOFF.md`.
* Authoring the worlds' scenes (rooms, paths, doorway waypoints, each scene's music): `tools/run/make_scenes.py`, described in `docs/CONTINUOUS_RUN.md`.
* The Bassment, the wizard's dungeon under the club (a wizard in the Warehouse offers it; 63 passages in 16 zones, each a 2.5D map; entered and left seamlessly on the same pads, clock and music): `docs/TRIAL_OPENING.md`.
* Wizard Duel, local wifi multiplayer: two wizards play the same notes and cast spells at each other when they pass a phrase (home > Wizard Duel, or practise alone against a scripted rival): `docs/DUEL.md`.
* The 2.5D world, art and authoring pipeline: `docs/STORY_CAMPAIGN_HANDOVER.md`, `docs/STORY_25D_PLAN.md`, `docs/STORY_ART.md`.
* Three paths branch off the Warehouse, each a sister run at its own tempo with its own music, rooms and endings, entered and left by a tempo handoff on the same pads: **The Life of Jesus** (`gospel`, house 124 BPM, 17 scenes, from the star on the balcony),
  **The Mission Count** (`squadron`, dubstep 140 BPM, 14 scenes, from the radio in the booth) and **The Ember Road** (`ember`, psytrance 145 BPM, 15 scenes, from the ember in a glass at the bar). Their notes: `docs/paths/{gospel,squadron,ember}.md`; the engine:
  `docs/CONTINUOUS_RUN.md` "Paths". Across every world the people's faces and acts carry the story and nothing is written during play (`RW_DEV_TEXT=1` brings the text back): `docs/THREE_PATHS_AND_FACES_PLAN.md`. Start with `docs/HANDOVER.md`.

```
godot --path .                                                         # home screen
godot --path . res://src/run/run_play.tscn                             # straight into the run (RW_RUN_START=<level id> picks the level)
RW_RUN_BOT=perfect RW_RUN_ROUTES=up,left godot --path . res://src/run/run_play.tscn   # scripted play: perfect | none | accuracy:<f> | blocks:<1011...>
RW_RUN_VIRTUAL=1 RW_RUN_BOT=perfect RW_RUN_UNTIL_PHASE=3 RW_STORY_QUIT=1 godot --headless --path . res://src/run/run_play.tscn   # no audio, stepped clock
RW_DEV_TEXT=1 godot --path . res://src/run/run_play.tscn               # the run writes nothing during play; this brings back the title card, captions, names, countdown and the Bassment's caption band
godot --headless --path . -s tests/run_tests.gd -- --filter run_      # the run's tests
RW_DEBUG=1 godot --path . res://src/run/run_play.tscn                  # the playtest overlay and feedback buttons on any run (docs/DEBUG_MODE.md); godot --path . res://src/debug/playtest_list.tscn opens the scene list
bash tools/run/shoot_debug.sh                                           # screenshots of the list, a scene's Info, the overlay and the notes into docs/shots/debug (needs a display)
godot --path . res://src/trial/trial_play.tscn                         # straight into the Bassment dungeon (RW_TRIAL_START=<passage>)
bash tools/trial/walk_trial.sh                                          # scripted walk: Warehouse > hatch > the dungeon to the victory > back up into the Warehouse
godot --path . res://src/duel/duel_lobby.tscn                          # the Wizard Duel lobby (host, join or practise); bash tools/duel/two_players.sh checks two processes agree
GODOT=<godot> bash tools/duel/two_players.sh                              # the duel: two headless processes over loopback must agree (PASS: both phones agree)
godot --headless --path . -s tools/duel/simulate.gd -- 5 adept apprentice   # scripted duels, for tuning duel.json
godot --headless --path . -s tools/trial/validate.gd                   # check the dungeon's data
godot --headless --path . -s tests/run_tests.gd -- --filter run_      # the run's tests (engine, saves, home, rails, scene, the policy matrix)
bash tools/run/walk_run.sh                                              # the run on the real scenes, scripted, all 36 scenes of the seven worlds, isolated save (needs a display)
bash tools/run/capture.sh                                               # screenshots per scene, rail place, door walk and passage into docs/shots/run (needs a display)
bash tools/run/frames.sh                                                # frame times per world (needs a display, an idle machine)
bash tools/story/walk_campaign.sh                                       # the chapter campaign end to end, scripted
python tools/content/beatshaper.py validate                             # music data
godot --headless --path . -s tools/story/record_music.gd -- <out> 70 res://src/run/run_play.tscn   # record the Music bus of a real run
python tools/story/check_run_audio.py <out>                             # fit the recording to the mix the engine reported
```

The chapter campaign is reachable from home as "Story chapters" (`docs/STORY_CAMPAIGN_HANDOVER.md`) and the Wizard Duel as its own button (`docs/DUEL.md`). The military campaign and the loadout are not on the home
screen (nor is the loadout button in the chapter menu); their code is still in the repository (the art pipeline, the tests and the developer button, shown only in the editor
or with `RW_DEV=1`, use it); the run does not depend on it.

## Layout

- `src/` game code: `core/` (song clock, pack loading: `mission_loader.gd` for missions, `level_loader.gd` for the duel;
  `library_index.gd` and `loadout.gd` the loop library and the player's loadout; `match.gd` drives a run; `sequence_tracker.gd`, `mission_rules.gd`, `campaign.gd` saves and unlocks, `session.gd`
  settings), `audio/` (one synchronized transport for the loadout's looping stems), `input/` (`pad_judge.gd` for missions, `judge.gd` for the
  duel, `lane_input.gd` touches, section taps and keys), `sim/` (deterministic 25 Hz OpenRA battle simulation, no
  scene nodes; civilians, wave target classes, start units, the active section), `ui/` (`pad_view.gd` the pads,
  `note_lane.gd` the falling notes, `battle_view.gd` sprites only, `hud.gd` the legacy duel's bar only, `section_picker.gd`, `ui_style.gd`, `settings_panel.gd`),
  `audio/` (`stem_transport.gd` the song, `battle_sfx.gd` the Red Alert effects), `scenes/` (home, missions, mission
  briefing, loadout, play, result, settings, calibration, developer).
- `content/paths/<id>/` the three paths' data (`run.json`, `music.json`, `hotspots/`, `walks.json`); their maps are in `content/story/maps/`, their art in `assets/story/<map>/`, their packs in `songs/packs/<id>_*`, the owner's drops in `content/imports/<id>/` (git-ignored). Tools: `tools/content/make_gospel.py`, `tools/paths/` (Squadron), `tools/run/make_ember.py`, `tools/story/build_gospel_art.py`, `build_ember.py`.
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
Controls: four pads (D F J K on a desktop) plus touching the world: when a scene's choice window opens (and in the Bassment), things in the room light up (a doorway, a person, an object, a creature);
touch one to choose it (touch another to change your mind; keys 1 to 4 on a desktop) and your playing in the last block decides how it goes. Nothing tapped takes the brighter default. Esc = pause, F3 = debug line.
The game needs no flags to launch: open `project.godot` and press Play.

```
bash tools/test.sh                                   # all headless tests + the content build tests
python tools/content/import_ableton.py content/imports/first_watch.json   # file your Ableton exports (ToAddTry1/) into content/library
python tools/extract_openra.py --no-map              # sprites from your OpenRA content (allow-list in the script)
python tools/extract_openra_sounds.py                # Red Alert sounds into assets/sfx
python tools/campaign/build_battlefield.py           # regenerate the maps and battlefields (add village_01 for the village only)
```

The three paths (`gospel`, `squadron`, `ember`; `stub` is a two-scene proof path). `<godot>` is the console binary; `walk_run.sh` and the capture scripts read `GODOT` (their default is the Linux path), `tools/test.sh` reads it too.

```
RW_RUN_PATH=gospel <godot> --path . res://src/run/run_play.tscn        # start inside a path (RW_RUN_START=<scene id> picks its scene, e.g. jerusalem.trial); without RW_RUN_PATH the paths are entered through the Warehouse portals
RW_RUN_PORTAL=warehouse.booth.radio RW_RUN_START=warehouse.booth RW_RUN_BOT=perfect <godot> --path . res://src/run/run_play.tscn   # the bot touches a portal (a gated portal needs its flag: RW_RUN_FLAGS=wh_saw_floor for the star, wh_vip_pass for the ember)
RW_PATH_REMAP=gospel=stub RW_RUN_FLAGS=wh_saw_floor RW_RUN_PORTAL=warehouse.balcony.star RW_RUN_START=warehouse.balcony <godot> --path . res://src/run/run_play.tscn   # play the stub path through another path's portal
RW_DEV_TEXT=1 <godot> --path . res://src/run/run_play.tscn             # the play text (title card, captions, names, countdown) is off by default; this restores it for debugging
GODOT=<godot> bash tools/run/walk_run.sh --path squadron               # a path on the real scenes, virtual clock, isolated save: perfect, loop, clause, sloppy, none (names: python3 tools/run/path_walk_spec.py <id> names); needs a display
python tools/run/check_hotspots.py --path gospel                       # a path's hotspots and reachability (also: squadron, ember; without --path: the main run); it also lists the laps of the scenes
python tools/run/measure_mix.py --run gospel [--force-laps 1]          # the mix of every scene, dwell per scene and per route; --force-laps 1 measures the paths as they were before the two laps (docs/HANDOVER.md A12)
python tools/run/laps.py content/paths/gospel/run.json                 # prints each scene's laps and cast beats (the cast is re-timed by the generators: docs/CONTINUOUS_RUN.md "Two laps per path scene")
python tools/content/beatshaper.py --path squadron survey "<folder>"   # the owner's loops for a path, measured at the path's tempo (validate, scan, check, import, apply: docs/MUSIC_IMPORT.md section 7)
python tools/content/beatshaper.py --path squadron import content/imports/squadron/C06 --set C06 --id squadron_c06 --max-error-ms 40   # --max-error-ms N loosens the drum-hit check from its 12 ms default and records it; nothing is stretched
python tools/content/make_path_placeholders.py gospel [--force]        # synthesised, bass-forward stand-in WAV loops for every scene of a path without an import (also: ember, stub)
python tools/content/import_squadron.py [--only C06,C07] [--check]     # the Mission Count's 14 loops from NewMusic/C level Music (source folder untouched)
python tools/content/music_handoff.py                                  # regenerate docs/MUSIC_HANDOFF.md (the shopping lists, including the three paths')
bash tools/run/capture_path.sh ember [--acting]                        # screenshots of every scene of a path (and of every character hotspot in five states) into docs/shots/
godot --headless --path . -s tools/run/check_path.gd -- gospel         # a path's run data: errors and warnings
python tools/story/check_assets.py                                     # the art contract (the five chapters and the three Squadron worlds)
```

```
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

`docs/HANDOVER.md` (start here: state, decisions, what was verified and what was not, the open decisions for the owner), `docs/THREE_PATHS_AND_FACES_PLAN.md` (the plan the three paths and the acting system were built from), `docs/paths/` (one note per path, the Mission Count's music report), `docs/PRD.md` (sections 15 and 16 the
mission rules and the loadout model; 1 to 13 the duel), `docs/CONTENT_TO_RENDER.md` (every WAV and MIDI to make in Ableton),
`docs/BALANCE.md` (seeded trials, coverage and tuning), `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (the brief this
build implements), `docs/EXPORT.md` (Android and Windows builds), `docs/TIMING.md`, `docs/OPENRA_BEHAVIOUR_SPEC.md`,
`content/README.md`, `songs/README.md`.
