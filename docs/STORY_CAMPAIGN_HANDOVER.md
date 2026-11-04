# Story Campaign: handover

Branch `feature/story-campaign-night-one` (from `main` at `dc7f73c`). The brief is `docs/STORY_CAMPAIGN_PRD.md`; it was extended during the build with four more
chapters (below). The military Campaign, Continue, Practice, Loadout, Settings, Developer and the legacy duel are untouched and still selectable.

## What a player gets

Main menu, **Story Campaign**: five chapters, each a full drum and bass set played on the four deck pads (same falling notes, judgement, SongClock, StemTransport and
global Loadout as the campaign). Every two-bar sequence result moves the crowd's energy; authored good/bad moments and three endings per chapter follow.

| # | Chapter | Music pack (existing, unchanged) | Camera | Unlocked by |
| --- | --- | --- | --- | --- |
| 1 | **Night One** (nightclub) | `m01_first_watch`, 128 bars | fixed, DJ's eye line | always |
| 2 | **The Mothership** (aliens take the rave) | `m10_last_light`, 80 bars | moves between 4 rooms | Night One: Legendary Set or Good Night |
| 3 | **The Underworld** (taken to hell, entertain the demons) | `m09_iron_rhythm`, 64 bars | moves between 4 rooms | Night One: Lost the Floor |
| 4 | **The Hospital** (you wake with your loving family) | `m05_counterpoint`, 56 bars | moves between 4 rooms | chapter 2 or 3 with a top or middle ending |
| 5 | **The Ward** (you come to on a ward of costumed eccentrics) | `m07_crossroads`, 64 bars | moves between 4 rooms | chapter 2 or 3 with the lowest ending |

Between chapters a short silent cutscene plays on the same camera: `abduction` (UFO and tractor beam), `descent` (floor cracks, fire, portal), `awakening` (eyelids, heart monitor),
`sectioned` (cold light, tunnel, a ward door opens). Chapters 2 to 5 reuse existing music packs at their own length (no new music was authored, by design). Chapters 4 and 5 are the
current end of the story ("To be continued").

## Run it

```
godot --path .                                       # main menu > Story Campaign
godot --path . res://src/scenes/story_play.tscn      # straight into Night One (RW_STORY_CHAPTER=mothership|underworld|hospital|mental_hospital for the others)
RW_AUTOPLAY=perfect godot --path . res://src/scenes/story_play.tscn   # scripted play: perfect | none | beginner | sloppy | accuracy:<f>  (RW_SEED=n)
bash tools/story/capture.sh [out_dir]                # real screenshots of the running scene on a virtual song clock (RW_SHOTS=regex to pick)
python3 tools/story/build_assets.py [night_one|mothership|underworld|hospital|mental_hospital]   # regenerate only the story art
python3 tools/story/check_assets.py --determinism    # manifest checks and the double-build hash
godot --headless --path . -s tools/story/tune.gd -- [chapter:<id>] perfect sloppy none   # endings under scripted skill levels
godot --headless --path . -s tests/run_tests.gd -- --filter story                        # the story tests
GODOT=<godot> bash tools/test.sh                     # everything
```
Godot 4.5.1 (`~/godot/Godot_v4.5.1-stable_linux.x86_64` on this machine). Other env switches: `RW_STORY_VIRTUAL=1` (no audio, stepped clock), `RW_STORY_UNTIL_BAR`, `RW_STORY_RATE`,
`RW_PAD_SIZE=0|1|2`, `RW_REDUCED=1`, `RW_HIGH_CONTRAST=1`, `RW_STORY_QUIT=1`, `RW_STORY_INTERLUDE=<name>` with `RW_STORY_INTERLUDE_T` and `RW_STORY_INTERLUDE_HOLD=1`.

## Architecture (all under `src/story/`, scenes in `src/scenes/story_*`)

- Logic with no nodes: `StoryData` (chapter file + validation), `CrowdController` (energy model, decision and ending rules), `StoryDirector` (schedules authored actions on exact song ticks; a decision waits for
  its sequences to be final), `StoryRun` (wraps the existing `Match` in rhythm-only mode, so judgement and sequence results are the campaign's own; also the headless autoplay harness), `StoryChapters`
  (registry, routes, unlocks), `StoryProgress` (`user://story_campaign.json`, atomic, corrupt files set aside; never touches `user://campaign.json`).
- Presentation: `StoryStage` (the camera, rooms, actions) > `StoryView` (one room: layers, `StoryFx` light/set effects, `StoryCrowd`) > `StoryCharacter` (a rig drawn by forward kinematics
  with analytic poses of the beat), `StoryDeck` / `StoryPadView` / `StoryNoteLane` (the DJ deck skin: PadView and NoteLane are subclassed, their semantics unchanged), `StoryHud`, `StoryStyle`,
  `StoryInterludeFx` and the interlude scene.
- Everything visual is a function of song time (the audio clock) and of action start times: pause freezes it, restart replays it, frame step does not change it (tested at 30, 60 and variable steps).
- The moving camera (chapters 2 to 5): `move_to {view, style: walk|step|turn_left|turn_right, bars}`, `camera_look`, `camera_push`; rooms are art-manifest `stage.views`; each room has its own crowd.

## Data and art

- `content/story/chapters.json` (registry and routes), `interludes.json`, one file per chapter: blocks of eight bars with authored actions (`when`/`else` guards on energy), decisions (smoothed energy with a dead
  band plus recent pass rate; a win-back beat after a bad branch), endings (energy and pass-rate thresholds), actors (archetype, variant, room, group, personal threshold), palettes. All tunable.
- Defaults: start energy 45; sharp +4, steady +3, loose +2, failed sequence -5; bands 0-29 / 30-64 / 65-84 / 85-100; top ending needs energy 85+ and 94% of sequences passed, the middle 40+ and 50%.
- Art: original, drawn by script. `tools/story/art/*.py` write SVG (imported natively by Godot, editable in Inkscape) and a few Pillow PNGs (glow, haze, beams) into `assets/story/<chapter>/` with a
  `manifest.json`. Contracts: `tools/story/ART_CONTRACT*.md`; provenance and how to edit: `docs/STORY_ART.md`. No OpenRA art, stock assets or downloads.

## Verification that was run

- Full Godot suite (`tools/test.sh`) on the final branch: 13,274 checks, 0 failures (the original game's suite was 11,664 checks before this work); the story subset is about 1,600 of them (logic, energy and bands, frame-step determinism,
  sequence fidelity against the original mission run, endings under perfect / mixed / no input for every chapter, save isolation and corruption, camera moves, per-room crowds, art validation, polish behaviours).
- Real-time headless runs of the whole 128-bar Night One through the actual audio transport and clock: perfect play gave Legendary Set (64/64), no input gave Lost the Floor (0/64, full song), sloppy play gave Good Night (45/64).
- Real screenshots of the running scene for every chapter, ending, camera move, layout (compact, standard, large pads; 4:3 and 20:9), reduced effects and high contrast: `docs/shots/story/` (27 compressed JPEGs: one set per chapter, the endings, camera moves) and `tools/story/capture.sh` (regenerates them).

## Known limitations

- `tools/test.sh` exits non-zero on this laptop because the Python content tests need the `mido` module, which is not installed (unrelated to the story code; `tools/content` is untouched).
- Not run on Android or any phone: touch is handled by the same LaneInput as the campaign, but there was no on-device check or export smoke test.
- Frame rate was measured only on this laptop's Intel HD 520 (the busiest Night One moments average about 25 ms a frame, 40 fps, while other jobs were using the machine); not measured on a desktop GPU.
- The cutscenes are silent; no crowd or cheer sound effects were added (the brief allows a silent crowd, and no legal recorded audio exists in the repo).
- The current Loadout has no hold notes in Night One, so the redesigned hold-note look has never been seen on screen.
- Chapters 2 to 5 use existing music packs at their native lengths (40, 32, 28 and 32 two-bar sequences), shorter than Night One.
- Hospital and Ward are intentionally gentle in tone; if that tone is not what was wanted it is a content change in the chapter JSON and art modules, not an engine change.
