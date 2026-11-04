# Story Campaign: handover (2.5D version)

Branch `feature/story-25d` (from `feature/story-campaign-night-one`; the painted 2D version is intact on that branch). Briefs: `docs/STORY_CAMPAIGN_PRD.md` (original), `docs/STORY_25D_PLAN.md`
(the 2.5D plan; section 13 is the progress log with every convention), `docs/STORY_25D_ART_DIRECTION.md` (the owner's art notes: layout variety, movement frequency, figures doing things, the pixel look).
The military Campaign, Continue, Practice, Loadout, Settings, Developer and the legacy duel are untouched.

## What a player gets

Main menu, **Story Campaign**: five chapters, each a full drum and bass set on the four deck pads (same falling notes, judgement, SongClock, StemTransport and global Loadout as the campaign).
Each chapter is a small Doom-style 3D world rendered at a low internal resolution (270 lines by default), seen from a camera that is *you* on authored rails: you start as a dancer, and as you play
well the camera is carried up (stage and booth, holo-dais and helm, throne and pit stage, the garden bandstand, the courtyard talent stage); play badly and you feel ill (a queasy look, a sick beat) and are
led away (toilets, medical bay, furnace and cage, back to bed, treatment room). Every two-bar sequence result moves the crowd's energy; authored good/bad decisions, three endings per chapter and
the interludes between chapters follow. Free look: drag or Q/E.

| # | Chapter | Music pack (existing) | Rooms (crowd rooms in bold) | Good journey > bad journey | Unlocked by |
| --- | --- | --- | --- | --- | --- |
| 1 | **Night One** | `m01_first_watch`, 128 bars | **floor** (+steps, riser, booth), entrance, bar, corridor, toilets, cubicles | steps, stage, booth > floor edge, corridor, cubicle | always |
| 2 | **The Mothership** | `m10_last_light`, 80 bars | **deck**, **gallery** (glass roof, planet), **reactor** (catwalk over a 2.5 m drop to the core), **bridge** (+ helm dais), medical bay (+ exam, airlock) | gallery, reactor, bridge, helm > medbay, exam, airlock | Night One: Legendary Set or Good Night |
| 3 | **The Underworld** | `m09_iron_rhythm`, 64 bars | sunken **arena** with tiers, **court** (+ throne stair), **pit** (causeway, deck, platform over lava), **furnace**, cage | court, throne, pit stage > furnace chains, cage | Night One: Lost the Floor |
| 4 | **The Hospital** (a night ward) | `m05_counterpoint`, 56 bars | **ward** (bed below the floor), long **corridor** to the nurses' station, day room, quiet corridor, tall **cafeteria**, moonlit **garden** (+ bandstand) | corridor, cafeteria, bandstand (carried) > quiet corridor, bed | chapter 2 or 3, top or middle ending |
| 5 | **The Ward** (grim green) | `m07_crossroads`, 64 bars | day room (+ stage), long **corridor** of locked doors (lit office), tall **art room**, walled **courtyard** (+ talent stage), treatment room, quiet room | corridor, art room, stage > treatment room, quiet room | chapter 2 or 3, lowest ending |

Interludes (`abduction`, `descent`, `awakening`, `sectioned`) are silent 2D cutscenes drawn over the 3D club the player left, in its ending tableau.

## Run it

```
godot --path .                                       # main menu > Story Campaign
godot --path . res://src/scenes/story_play.tscn      # Night One (RW_STORY_CHAPTER=mothership|underworld|hospital|mental_hospital)
RW_AUTOPLAY=perfect godot --path . res://src/scenes/story_play.tscn   # scripted play: perfect | none | beginner | sloppy | accuracy:<f>  (RW_SEED=n)
bash tools/story/walk_campaign.sh [perfect none sloppy2 mixed_a mixed_b]   # the real scene chain, five paths, isolated save (needs a display; about 40 minutes for all five)
bash tools/story/capture.sh [out_dir]                # screenshots (RW_SHOTS=regex; up to four runs in parallel; PNG out, docs/shots/story holds JPEGs)
RW_STORY_VIRTUAL=1 RW_AUTOPLAY=perfect RW_STORY_PROFILE_FROM=57 RW_STORY_UNTIL_BAR=73 RW_STORY_CHAPTER=mothership godot --path . --disable-vsync --resolution 1280x720 res://src/scenes/story_play.tscn   # frame times
python3 tools/story/build_assets.py [chapter] [tiles]   # regenerate the story art and its texture tiles (then godot --headless --path . --import)
python3 tools/story/check_assets.py --determinism    # manifest checks and the double-build hash
godot --headless --path . -s tools/story/tune.gd -- [chapter:<id>] perfect sloppy none   # endings AND the journey under scripted skill levels
godot --headless --path . -s tests/run_tests.gd -- --filter story                        # the story tests (tools/test.sh --filter story)
GODOT=<godot> bash tools/test.sh                     # everything
```
Godot 4.5.1 (`~/godot/Godot_v4.5.1-stable_linux.x86_64` here). Env switches: `RW_STORY_VIRTUAL=1` (no audio, stepped clock), `RW_STORY_UNTIL_BAR`, `RW_STORY_RATE`, `RW_STORY_LINES=360|270|180`, `RW_STORY_MOTION=0|1|2`,
`RW_STORY_FOG=0`, `RW_PAD_SIZE=0|1|2`, `RW_REDUCED=1`, `RW_HIGH_CONTRAST=1`, `RW_STORY_INTERLUDE=<name>` (+ `_T`, `_HOLD=1`), and for scripted chains `RW_STORY_AUTO_ADVANCE=1` (result after 1 s, interlude played fast),
`RW_STORY_TRACE=<file>` (one line per scene), `RW_STORY_POLICIES="night_one=perfect;mothership=accuracy:0.8@2"` (policy and seed per chapter), `RW_STORY_RECORD=1` (a scripted run writes the story save: point `XDG_DATA_HOME` at a
throwaway folder first, as the walk script does).

## Architecture (all under `src/story/` and `src/story/world/`, scenes in `src/scenes/story_*`)

- Logic with no nodes: `StoryData`, `CrowdController`, `StoryDirector` (schedules authored actions on song ticks; warns at load about a `player_move` on a dense run), `StoryRun` (wraps `Match` in rhythm-only
  mode; also the headless autoplay harness), `StoryChapters` (routes, unlocks), `StoryProgress` (`user://story_campaign.json`), `StoryMap` (the world's data and validation), `StoryPlayer` (the rail camera: routes over
  portals, move styles, glances, roles, queasy and sick envelopes), `StoryProjector` (pinhole maths), `StoryJourney`, `StoryLight` (all light maths as functions of song time), `StoryTrace` (scripted-run helpers).
- Presentation: `StoryStage` owns the map, the player, one `StoryCrowd` per room (`crowds`, `current_view` = the room the player last walked into: authored crowd actions direct that crowd), the `StoryLowRes` viewport,
  `StoryWorld` (sector meshes, things, sky, fog, animated surfaces) and `StoryWorldFx` (beams, pools, haze, LED, floor tiles, rings, confetti: all from `StoryLight`). Crowds are drawn by the 2D `StoryCrowd` /
  `StoryCharacter` rig inside the low-res viewport, projected from the map homes, culled by sector visibility, sorted by distance; a crowd whose room is out of sight only keeps its walks and fades.
- The 2D painted rooms (`StoryView`, `StoryFx`, the dolly camera, 2D crowd placement) are gone; the art files they used remain as tile sources and menu thumbnails.
- Everything visual is a function of song time: pause freezes it, restart replays it, frame step does not change it (tested at 30, 60 and variable steps, per chapter).

## Map data (`content/story/maps/<chapter>.json`)

Conventions are in plan 13.1/13.2; additions made in WP7: `rooms {room: {palette}}` (the light a room switches to), `fog {color, density}`, `animated [{tex, mode scroll|pulse|flicker|swap, speed, rate, amount, bright, frames}]`
(lava, reactor glass, window light, bulbs: every surface showing that tile), things with `piece` (a set piece of the art shown while `piece_on` says so) and `blend` (add|mix), spots per room (`"<room>.door"`
with eight `slots`, `circle`, `riser`, `side_l`, `side_r`; the plain names are the main room's), `dance_floor` on exactly one sector per crowd room (the light show's floor follows the crowd room), `sky` (a 256 x 64 strip),
sectors lit at least `StoryWorld.MIN_GAIN` (no room reads as black). Journey actions in chapter JSON: `player_move`, `player_look` with `yaw`, `at` or `by` (a glance: the head turns `by` degrees from the rail and back, never
touching the route), `player_role`, `fx_queasy`, `sick_beat`; every eight-bar block carries two glances (a camera beat), decisions carry the branch moves (`after_bars` offsets), endings carry `journey`.

## Tuning

Chapter files hold thresholds, actors, groups, palettes, blocks, decisions and endings (energy defaults: start 45; sharp +4, steady +3, loose +2, failed -5; top ending needs energy 85+ and 94% of sequences, the middle 40+ and 50%).
`tune.gd` shows ending, branches and journey per policy and seed. Journeys are authored in the chapter JSON next to the decisions; the matrix test recomputes the expected places from the file and the outcomes.

## Art pipeline

`tools/story/art/*.py` write the SVG art; `tools/story/bake_tiles.gd` bakes each chapter's world tiles from those SVGs (recipes `_<chapter>()`; metres per repeat in `tools/story/art/tiles.py`); `build_assets.py` runs both and strips the
manifest fields only the old 2D rooms read. After new tiles: `godot --headless --path . --import`. Provenance and how to edit: `docs/STORY_ART.md`. No downloaded art, no new audio.

## Tests

`tests/test_story_*.gd`: logic, chapters (routes, endings, determinism, art), map (every chapter map validates, every crowd room has its spots and eight door slots, homes keep 1 m from every waypoint, no sector reads black),
world, player, camera (rooms, glances), crowd and fx (world), journey, polish, stage, and `test_story_matrix.gd`: every chapter x perfect, accuracy 0.9/0.8/0.7/0.5, beginner, sloppy, none x seeds 1 to 3: the ending is in the chapter's set,
perfect gets the top ending and none the bottom, the journey equals the authored list for the outcomes reached (and the literal top and bottom lists), the camera stands in a room at every half bar, every block has a camera beat, no move warns
about a dense run (default and hard loadouts). The Python `mido` content-test failure on `tools/test.sh` is known and unrelated.

## Numbers

- Frame time (this laptop, Intel HD 520, windowed 1280x720, vsync off, 270 lines, perfect play, 16 busiest bars of each chapter, 1,325 frames; the machine was otherwise idle):

| Chapter | bars | mean ms | p95 ms |
| --- | --- | --- | --- |
| Night One | 105 to 121 | 14.3 | 15.0 |
| The Mothership | 57 to 73 | 18.8 | 20.4 |
| The Underworld | 41 to 57 | 18.6 | 21.4 |
| The Hospital | 33 to 49 | 16.0 | 19.1 |
| The Ward | 41 to 57 | 17.2 | 22.2 |

  The plan's budget (12 ms mean, 20 ms p95) is not met by any chapter, Night One included; chapters 2 to 5 are 2 to 4.5 ms above Night One. Measured why: the set pieces and props as billboards cost about 1.6 ms
  (50 to 65 things against Night One's 14; each is a draw call), one crowd per room (about 100 actors updated instead of 30; now skipped while a room is out of sight, which saved about 0.5 ms), and more dancers on screen at once in the
  long rooms. The resolution does not matter (180 and 270 lines are the same): the cost is CPU. Next levers: merge the piece things into one mesh per room, cache the static deck layer and pad boxes (about 1.8 ms), bake the dancers to sprite sheets.
- Tests: the Godot suite (`tools/test.sh`) is 29,001 checks, 0 failures (16,982 at the start of WP7; the matrix alone is about 7,500); the three remaining Python errors are the known `mido` content tests.
- Maps: Mothership 10 sectors, 5 rooms, 62 things; Underworld 19, 5, 55; Hospital 9, 6, 52; Ward 9, 5, 65 (Night One 10, 4, 14). About 100 homes per chapter.
- Walk-through (`tools/story/walk_campaign.sh`, every path OK; each line is one result scene):

```
# path perfect
play chapter=night_one policy=perfect seed=1
result chapter=night_one policy=perfect ending=legendary_set route=mothership interlude=abduction unlocked=night_one,mothership
interlude name=abduction from=night_one to=mothership ending=legendary_set
play chapter=mothership policy=perfect seed=1
result chapter=mothership policy=perfect ending=galactic_headliner route=hospital interlude=awakening unlocked=night_one,mothership,hospital
interlude name=awakening from=mothership to=hospital ending=galactic_headliner
play chapter=hospital policy=perfect seed=1
result chapter=hospital policy=perfect ending=family_celebration route=end interlude= unlocked=night_one,mothership,hospital
menu unlocked=night_one,mothership,hospital
# path none
play chapter=night_one policy=none seed=1
result chapter=night_one policy=none ending=lost_the_floor route=underworld interlude=descent unlocked=night_one,underworld
interlude name=descent from=night_one to=underworld ending=lost_the_floor
play chapter=underworld policy=none seed=1
result chapter=underworld policy=none ending=devoured route=mental_hospital interlude=sectioned unlocked=night_one,underworld,mental_hospital
interlude name=sectioned from=underworld to=mental_hospital ending=devoured
play chapter=mental_hospital policy=none seed=1
result chapter=mental_hospital policy=none ending=lights_out route=end interlude= unlocked=night_one,underworld,mental_hospital
menu unlocked=night_one,underworld,mental_hospital
# path sloppy2
play chapter=night_one policy=sloppy seed=2
result chapter=night_one policy=sloppy ending=good_night route=mothership interlude=abduction unlocked=night_one,mothership
interlude name=abduction from=night_one to=mothership ending=good_night
play chapter=mothership policy=sloppy seed=2
result chapter=mothership policy=sloppy ending=honoured_guest route=hospital interlude=awakening unlocked=night_one,mothership,hospital
interlude name=awakening from=mothership to=hospital ending=honoured_guest
play chapter=hospital policy=sloppy seed=2
result chapter=hospital policy=sloppy ending=on_the_mend route=end interlude= unlocked=night_one,mothership,hospital
menu unlocked=night_one,mothership,hospital
# path mixed_a
play chapter=night_one policy=perfect seed=1
result chapter=night_one policy=perfect ending=legendary_set route=mothership interlude=abduction unlocked=night_one,mothership
interlude name=abduction from=night_one to=mothership ending=legendary_set
play chapter=mothership policy=none seed=1
result chapter=mothership policy=none ending=beamed_home route=mental_hospital interlude=sectioned unlocked=night_one,mothership,mental_hospital
interlude name=sectioned from=mothership to=mental_hospital ending=beamed_home
play chapter=mental_hospital policy=none seed=1
result chapter=mental_hospital policy=none ending=lights_out route=end interlude= unlocked=night_one,mothership,mental_hospital
menu unlocked=night_one,mothership,mental_hospital
# path mixed_b
play chapter=night_one policy=none seed=1
result chapter=night_one policy=none ending=lost_the_floor route=underworld interlude=descent unlocked=night_one,underworld
interlude name=descent from=night_one to=underworld ending=lost_the_floor
play chapter=underworld policy=perfect seed=1
result chapter=underworld policy=perfect ending=resident_dj route=hospital interlude=awakening unlocked=night_one,underworld,hospital
interlude name=awakening from=underworld to=hospital ending=resident_dj
play chapter=hospital policy=perfect seed=1
result chapter=hospital policy=perfect ending=family_celebration route=end interlude= unlocked=night_one,underworld,hospital
menu unlocked=night_one,underworld,hospital
```

## Known limitations

- The Python content tests need the `mido` module, so `tools/test.sh` exits non-zero here (unrelated; `tools/content` is untouched).
- Not run on Android or a phone; no export smoke test; the touch drag for free look is untested on a device. Frame rate was measured only on this laptop (above).
- The cutscenes are silent and still 2D over the 3D tableau (the owner may want them restaged: plan 9.6). No crowd or cheer audio exists.
- Dancers are still the 2D rig projected into the world (no sprite sheets): near dancers are large, and a dancer passing the eye fades out.
- The room lists of docs/STORY_25D_ART_DIRECTION.md section 2.A are applied to the four chapters built in WP7 (Mothership, Underworld, Hospital, Ward) in a first pass (see the plan's progress log); Night One still has the WP1 layout (no
  balcony, chill-out room or entrance tunnel) and the curved Mothership deck is a rectangle: that is WP9. Art-direction sections 2.C to 2.E (activities, pixel look, figure look) are not started.
- Tiles are plain crops of the old art: the Hospital and Ward read lighter than the owner's night-blue and grim-green tone (sector tints and fog are set to it, the dance-floor palette overrides them in the dancing rooms).
- A bad-branch player has no walk back from the Underworld cage or the Ward quiet room (the win-back beat comes four bars after the sick beat there).
