# Story Campaign: handover (2.5D version)

Branch `feature/story-25d` (from `feature/story-campaign-night-one`; the painted 2D version is intact on that branch). Briefs: `docs/STORY_CAMPAIGN_PRD.md` (original), `docs/STORY_25D_PLAN.md`
(the 2.5D plan; section 13 is the progress log with every convention), `docs/STORY_25D_ART_DIRECTION.md` (the owner's art notes: layout variety, movement frequency, figures doing things, the pixel look).
The military Campaign, Continue, Practice, Loadout, Settings, Developer and the legacy duel are untouched.

## What a player gets

Main menu, **Story Campaign**: five chapters, each a full drum and bass set on the four deck pads (same falling notes, judgement, SongClock, StemTransport and global Loadout as the campaign).
Each chapter is a small Doom-style 3D world rendered at a low internal resolution (360 lines by default; the settings keep 270 and 180), seen from a camera that is *you* on authored rails: you start as a dancer, and as you play
well the camera is carried up (stage and booth, holo-dais and helm, throne and pit stage, the garden bandstand, the courtyard talent stage); play badly and you feel ill (a queasy look, a sick beat) and are
led away (toilets, medical bay, furnace and cage, back to bed, treatment room). Every two-bar sequence result moves the crowd's energy; authored good/bad decisions, three endings per chapter and
the interludes between chapters follow. Free look: drag or Q/E.

| # | Chapter | Music pack (existing) | Places (crowd rooms in bold) | Good journey > bad journey | Unlocked by |
| --- | --- | --- | --- | --- | --- |
| 1 | **Night One** | `m01_first_watch`, 128 bars | entrance vestibule + a three-sector tunnel under a stepped stair underside; **floor** (a 6.4 m hall under trusses) with steps, riser, raised booth behind speaker stacks, a steel stair up to a **balcony** that looks over the floor through a blocked opening; low warm bar alcove; chill-out room with two sofa alcoves; an 18 m tiled corridor to the toilets and two cubicles | steps, stage, balcony, booth > floor edge, corridor, cubicle | always |
| 2 | **The Mothership** | `m10_last_light`, 80 bars | a curved **deck** (hexagon plus angled glass wings, lounge bays, ramps up to the dais), **gallery** (glass roof, planet), **reactor** (catwalk over a 4 m drop to the core), **bridge** (ramped helm dais), medical bay (ward, alcove, exam table platform, airlock) | gallery, reactor, bridge, helm > medbay, exam, airlock | Night One: Legendary Set or Good Night |
| 3 | **The Underworld** | `m09_iron_rhythm`, 64 bars | sunken **arena** with tiers, **court** (columns, a three-step throne stair), **pit** (causeway, deck, platform over lava), **furnace** (anvils), cage | court, throne, pit stage > furnace chains, cage | Night One: Lost the Floor |
| 4 | **The Hospital** (a night ward) | `m05_counterpoint`, 56 bars | **ward** (bed below the floor), long **corridor** to the nurses' station, day room with a raised TV alcove, quiet corridor, tall **cafeteria**, moonlit **garden** (benches, bandstand) | corridor, cafeteria, bandstand (carried) > quiet corridor, bed | chapter 2 or 3, top or middle ending |
| 5 | **The Ward** (grim green) | `m07_crossroads`, 64 bars | day room (+ stage), long **corridor** of locked doors (lit office), dormitory, tall **art room**, walled **courtyard** (+ talent stage), treatment room, quiet room with a bed apse and a barred slit | corridor, art room, stage > treatment room, quiet room | chapter 2 or 3, lowest ending |

Interludes (`abduction`, `descent`, `awakening`, `sectioned`) are silent 2D cutscenes drawn over the 3D club the player left, in its ending tableau.

## Run it

```
godot --path .                                       # main menu > Story Campaign
godot --path . res://src/scenes/story_play.tscn      # Night One (RW_STORY_CHAPTER=mothership|underworld|hospital|mental_hospital)
RW_AUTOPLAY=perfect godot --path . res://src/scenes/story_play.tscn   # scripted play: perfect | none | beginner | sloppy | accuracy:<f>  (RW_SEED=n)
bash tools/story/walk_campaign.sh [perfect none sloppy2 mixed_a mixed_b]   # the real scene chain, five paths, isolated save (needs a display; about 40 minutes for all five)
bash tools/story/capture.sh [out_dir]                # screenshots (RW_SHOTS=regex; up to four runs in parallel; PNG out, docs/shots/story holds JPEGs)
RW_STORY_VIRTUAL=1 RW_AUTOPLAY=perfect RW_STORY_PROFILE_FROM=57 RW_STORY_UNTIL_BAR=73 RW_STORY_CHAPTER=mothership godot --path . --disable-vsync --resolution 1280x720 res://src/scenes/story_play.tscn   # frame times
bash tools/story/rooms.sh [png_dir] [sheet_dir]          # one shot per place of every chapter + docs/shots/story/contact_<chapter>.jpg (RW_ROOMS=regex, RW_JOBS=4)
bash tools/story/profile_all.sh [chapter...]        # frame time of the busiest 16 bars (needs an idle machine); RW_STORY_HIDE=crowd,world,fx,pads,notes,hud,stage and RW_STORY_NOSTAGE=1 split the cost
python3 tools/story/build_assets.py [chapter] [tiles]   # regenerate the story art and its texture tiles (then godot --headless --path . --import)
python3 tools/story/check_assets.py --determinism    # manifest checks and the double-build hash
godot --headless --path . -s tools/story/tune.gd -- [chapter:<id>] perfect sloppy none   # endings AND the journey under scripted skill levels
godot --headless --path . -s tests/run_tests.gd -- --filter story                        # the story tests (tools/test.sh --filter story)
GODOT=<godot> bash tools/test.sh                     # everything
```
Godot 4.5.1 (`~/godot/Godot_v4.5.1-stable_linux.x86_64` here). Env switches: `RW_STORY_VIRTUAL=1` (no audio, stepped clock), `RW_STORY_UNTIL_BAR`, `RW_STORY_RATE`, `RW_STORY_LINES=360|270|180`, `RW_STORY_MOTION=0|1|2`,
`RW_STORY_FOG=0`, `RW_STORY_CAM=<waypoint>[,yaw[,pitch]]` or `@x:z:yaw[:pitch]` (a screenshot camera at a place, the crowd of that room directed), `RW_STORY_NOATLAS=1` (dancer parts drawn one by one),  `RW_PAD_SIZE=0|1|2`, `RW_REDUCED=1`, `RW_HIGH_CONTRAST=1`, `RW_STORY_INTERLUDE=<name>` (+ `_T`, `_HOLD=1`), and for scripted chains `RW_STORY_AUTO_ADVANCE=1` (result after 1 s, interlude played fast),
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

### WP9 additions to the map and the journey

- `palette_weight` (0..1, default 0.25; Night One 1.0): how much the stage palette overrides the tint of dance-floor and stage sectors, and how bright the LED floor tiles are
  (`lerp(0.35, 1, weight)`). Outside the club the sector's own tint wins, so the Hospital reads night blue and the Ward green.
- A wall with `"blocked": true` and a portal is an opening you look through (a balcony rail, a window): rooms and crowds show through it, but routes and reachability ignore it.
- `activities` per sector (below), `ambient` per sector (flat light kept away from lights, default 0.62 where lights reach, 1 elsewhere) and things with `"kind": "light"`:
  `{id, kind: "light", at: [x, z], y: height above the floor (2.4), radius: m, color: "#hex", strength: 0..2.5, cone?: {yaw, angle}, sectors?: [ids]}`. A light reaches its own sector and the ones
  next to it through a portal (or exactly `sectors`). `StoryWorld` bakes them once into vertex colours: surfaces a light reaches are cut into 1.2 m cells and each vertex gets the flat shade
  times `ambient` plus every light's colour with a squared falloff (a cone for a window's patch or a doorway's spill); the sector's song-time light (`light_of`) still multiplies the result every frame.
  Place lamps to pool light, a cone at a door to spill into a dark corridor, a cone from a window for moonlight across a floor.
- Journey actions added: `player_walk {to | fwd, right, face | turn, stop, in, style, bars}` (a walk inside the room the rail is in, resolved from where the rail is when it starts; `in` lists rooms or
  sectors it applies to, otherwise it does nothing; it never interrupts a `player_move` under way and never counts as a place in the journey), `player_look {pitch}` (a glance up or down, with or
  without `by`), `player_look {at, in}` (a persistent turn, only where the player is). The camera also drifts a little between authored moves (`StoryPlayer.drift_at`: about 1.4 degrees of yaw, 0.7 of
  pitch, a function of song time, off in reduced motion). The camera now has a pitch (`pose["pitch"]`), applied to the Camera3D and to the crowd's projection.
- Every eight-bar block of every chapter has at least two camera beats and its beats differ from the previous block's (`test_story_matrix`); a block mixes a glance up or down, a sweep, a look at a
  character, a walk to a spot, forward, back or sideways, and (Mothership, Hospital) a climb. Walks that only make sense in one place carry `in`, so the bad branches simply skip them.

### Figures doing things (activities)

`StoryCharacter.ACTIVITIES`: stand, dance, drink, toast, chat, point, phone, lean_wall, sit, lie, sleep, paint, pace, carry, serve, check, stare, rock, hug, queue, wave, watch, mix, each an analytic
song-time pose like the dance set (`StoryCharacter.sample`). A sector's `activities` is `{quiet, dancing, hype, euphoric?: [names]}` (bands from the chapter's energy bands; euphoric falls back to hype);
`StoryMap` rejects unknown names, `dance` anywhere but a `dance_floor` or `stage` sector and `dance` in any quiet list, and requires quiet, dancing and hype. Each actor picks from the list of the sector it
stands in, by its own seed (`StoryCrowd.pick_activity`: stable, never random per frame). Directives (clap_sync, hands_up_all, wave...) and the ending tableaux only move people on dancing sectors
(dance_floor, stage, stage_steps, booth) and never a character with a locked activity. Actor fields: `activity` (locks the person to one activity: the DJ mixing, the bouncer checking tickets),
`prop` (cup, bottle, tray, phone, clipboard, tickets, brush, sketchbook, drip, headphones, headphones_wrong, mug: drawn at the right hand by `StoryCharacter._draw_held`; the shapes are plain
placeholders, the hand point and the call site are the contract), `target` (a waypoint or actor: what `watch`, `stare`, `point` and `check` face), `pace_axis` / `pace_m` (the to-and-fro of `pace` and
`serve`, clamped to the sector). `chat`, `hug` and `toast` pair the nearest free person in the same sector doing the same thing (a lone one falls back to stand or drink); pairs face each other (the
figure mirrors towards its partner on the screen). Homes may be in any sector: a crowd also owns the sectors its actors stand in. The fun beats: Night One a bartender who serves, a sleeper and a chatting pair on
the sofas, balcony watchers, a bouncer checking tickets; Mothership an alien DJ with the headphones on wrong, a grey examining a dancer on the exam table, a blob bartender, window pointers, engineers
checking the core; Underworld a demon bouncer checking tickets with a queue of imps, a bartender on the tier, demons lounging on the throne stair and the tiers, smiths at the anvils, a prisoner rocking in the
cage; Hospital a patient dancing with a drip stand, a nurse checking the monitor, family at the bed and a sleeping visitor, queues at the vending machines, granny watching the TV; Ward a chef serving at
the talent show, painters at the easels, a medication queue with the orderly checking, residents pacing and rocking, one staring at the barred window, sleepers in the dormitory.

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

- Frame time (this laptop, Intel HD 520, windowed 1280x720, vsync off, perfect play, the 16 busiest bars of each chapter, 1,325 frames, machine idle; `tools/story/profile_all.sh`). Mean ms (p95):

| Chapter | bars | end of WP8 (270 lines) | WP9 content, before the performance pass (360) | WP9 final, 360 lines | WP9 final, 270 lines |
| --- | --- | --- | --- | --- | --- |
| Night One | 105 to 121 | 14.3 (15.0) | 17.0 (18.1) | 15.5 (16.7) | 15.3 (16.7) |
| The Mothership | 57 to 73 | 18.8 (20.4) | 17.0 (20.8) | 15.4 (18.3) | 15.3 (19.7) |
| The Underworld | 41 to 57 | 18.6 (21.4) | 20.5 (25.0) | 18.5 (22.0) | 17.9 (21.1) |
| The Hospital | 33 to 49 | 16.0 (19.1) | 19.5 (24.2) | 17.6 (21.0) | not measured |
| The Ward | 41 to 57 | 17.2 (22.2) | 19.7 (25.8) | 17.5 (22.2) | 17.2 (21.9) |

  The budget (12 ms mean, 20 ms p95) is not met by any chapter, and the architecture does not allow it on this machine. Measured with `RW_STORY_HIDE` and `RW_STORY_NOSTAGE` on the Underworld (360 lines): with every
  visible node hidden and the stage not updating a frame still costs 7.9 ms (the engine, the virtual-clock harness, Match and the judge), the pad strip adds 3.9 ms, the falling notes 2.0, the stage's scripts 1.6,
  and drawing the stage 6.4 (the 2D crowd about 5, the 3D world 2.4, the light show 1.2). The 3.5 to 4 ms of content growth in WP9 (13 to 14 more people per chapter doing things, more lit geometry, 360 lines instead of 270)
  was bought back by: dancer parts packed into one atlas so the canvas batches them (about 1.3 ms), hidden sectors not drawn or lit, unchanged light left alone, a 30 Hz pose rate, the cached static deck layers
  (together about 1.5 to 2 ms; the deck cache itself measured under 0.3 ms: the pad boxes dominate, anti-aliasing them off would save 0.4 more). What is left is the pad strip and notes (5.9 ms of UI that has never
  been optimised), the crowd's draw calls (the sprite-sheet bake planned for the polish session removes most of them) and the engine floor. Resolution barely matters (360 vs 270: 0 to 0.6 ms).
- Tests: the Godot suite (`tools/test.sh`) is 39,660 checks, 0 failures (29,001 at the end of WP8; the matrix alone is about 7,600, `test_story_activities` adds 6,700); the three remaining Python errors are the known `mido` content tests.
- Maps: see `content/story/maps/<chapter>.json`; every chapter now has 22 to 29 sectors, 12 to 15 lights and 13 to 15 characters with a part to play (homes: about 115 per chapter).
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
- Art-direction sections 2.A (layouts), 2.B (movement) and 2.C (activities) and the data hook of 2.D (lights) are built (WP9). Sections 2.D's look (textures, haze, windows with skies, far crowd silhouettes) and
  2.E (the figures: wardrobe, sprite sheets, depth) are the polish session's. The activity props are plain shapes; the cubicles and the Mothership airlock are still bare boxes; the Ward day room and corridor stay
  pastel-lit by the beams and the room palette (the LED floor is dimmed outside the club, nothing else is).
- Light bleeds through walls (a light reaches its own sector and its portal neighbours, there is no occlusion); `sectors` limits it.
- A bad-branch player has no walk back from the Underworld cage or the Ward quiet room (the win-back beat comes four bars after the sick beat there).
