# The street race (package "race", branch `wip/play-race`)

Brief sections 8 to 10 (`docs/briefs/BEDSIT_RAVES_BRIEF.md`); contracts 4, 5, 8 and 10 (`docs/parallel-development/CONTRACTS.md`); rulings 35 to 38. The Space rave's hangar
(`space_race`) is the race's entrance; the other three raves reuse the generator and the simulation with their own data.

## Play it

    tools\dev\play_bedsit.cmd --rave space      then the pilot in the hub (south-west), then touch the racer in the hangar
    tools\dev\play_bedsit.cmd --race space      straight into the hangar (RW_RUN_START=space_race): touch the racer

The race seats on the next block start: on that downbeat the picture is the street, from the driver's seat (no fade, no card). The pads go on being judged; the four
large regions of the picture are the driving choices (contract 5's `world_regions`): **top** carry on / commit to the opening ahead, **bottom** brake / drop behind,
**left** and **right** move a lane. Good pad play keeps the car fast, poor play slows it (never below the minimum travelling speed). When the car crosses the finish line
and has rolled to a stop, the picture is the hangar again, the record is saved, and the way back to the hub is chosen for you (it goes at the scene's boundary). The race
can be run again from the hub; it never needs the three rave tasks.

## What is built

| Piece | Where |
| --- | --- |
| Course generator (any theme) | `tools/story/build_race.py --theme space` (+ `--sheet F`), geometry `tools/story/race_course.py`, placeholder art `tools/story/race_art.py` |
| The street (story map) | `content/story/maps/race_space.json` (535 sectors: per piece of street a block, a pavement, the road, a pavement, a block), `content/story/race_space.json` |
| The course | `content/races/courses/race_space.json` (contract 8's RaceCourse + analytic `segments`, `pieces`, `lane_waypoints`) |
| Race data | `content/races/space.json` (course, rivals, situation table, timings, speeds, outcomes, view sizes) |
| Activity config | `content/minigames/race.json` (kind race, mode overlay, controls 0) |
| Simulation | `src/minigames/race/race_activity.gd` (`RaceActivity`), `src/minigames/race/race_course.gd` (`RaceCourse`) |
| Stage swap | `src/minigames/race/race_stage_host.gd` (`RaceStageHost`, owned by RunPlay) |
| Scene | `content/paths/bedsit/run.json` node `space_race` (no longer a placeholder) and hotspot `space_race.race` on the map thing `hangar_racer` (window `any`, replayable) — written by `tools/run/make_bedsit.py --bedsit` |
| Tests | `tests/test_race.gd` (10), bot `tests/fixtures/race_bot.gd`, balance grid `tools/race/calibrate_race.gd` |
| Shots | `tools/engine/shoot_race.gd`, `tools/dev/shoot_race.sh`, `tools/dev/race_sheet.py` -> `docs/shots/bedsit/race/contact.jpg` |

### The course

Straight runs and circular bends (`THEMES.space.layout`: 260 m, 40 degrees left at r 90, 300 m, 60 right at r 80, 220 m, 30 right at r 120, 340 m, 50 left at r 90, 260 m,
20 left at r 150, then the long finishing straight): 2200 m to the finish line, 160 m of run-off to a building at the street's end, 30 m of street behind the grid. Three
lanes of 3.4 m, 3 m kerbed pavements, buildings 7 m deep. Pieces are cut every 30 m on the straights and every 6 degrees on the bends; neighbours share their cut, so every
portal meets (`StoryMap` loads it with 0 errors). Buildings are Doom-style blocks: a sector whose floor is the roof (9 to 30 m, in runs of one to three pieces), so the
step face up to it is the facade and the skyline varies; their outer walls are `sky` (not drawn). Lamps every 40 m alternate sides (their pools reach the road and
pavements of three pieces), cat's eyes every 9 m on the lane lines, shop windows and neon signs as emissive decals with their own light, three chequered banners over the
road 400, 200 and 80 m before the finish, the finish gantry, a big neon at the street's end. The eye is 1.15 m (`eye_height`), visibility `clip` (depth 60, far 170 m).
Waypoints: `ln<lane>_<piece>` (each lane's middle in each piece, 3 x 107), `race_grid`, `race_finish`, `race_end`.

The game computes the centreline from the same `segments` (`RaceCourse.point`); `ContractShapes.course_point` on the 5 m `centreline` agrees to within 0.6 m (tested).

### The simulation (`RaceActivity`, overlay mode)

Pure and deterministic in song time: `update(t)` integrates fixed steps (`timing.dt`, 1/120 s) up to `t`; judge events are applied at their own song times. Same seed and
inputs give the same log at any frame rate (tested at 60 and 47 fps); a paused song (t frozen) freezes the car, the rivals and every deadline (tested: 600 frames at one t
change nothing; three pauses in a race change nothing).

- **Speed**: target = min + (top - min) x (0.25 + 0.75 x rhythm). Top 38 m/s, min 0.35 x top (13.3 m/s). Rhythm = a running average of the pads' judgements (perfect 1,
  great 0.9, good 0.75, ok 0.5, hold complete 1, hold partial 0.5, stray 0.3, miss 0; 15 % per judgement); a block result counts only when no judgement arrived in it.
  Acceleration 5 m/s2, deceleration 9 m/s2. The floor (min) rises over the first two seconds after the green light.
- **Grid**: the player at the back in the middle lane; three rivals 6, 12, 18 m ahead (`rivals`: paces 0.88, 0.855, 0.83 of top with a slow wobble). Start lights over the
  road: one, two, three reds over `grid_beats` (8), then green.
- **Situations**: the first 4.5 s after the green, then every 4 s + 1.6 s; none in the last 180 m. Picked by a seeded draw from `situations` (weights 3, 3, 2, 2):

| Situation | Top | Bottom | Toward a lane that exists | Toward no lane |
| --- | --- | --- | --- | --- |
| braking_car (a taxi ahead in your lane, brake lights 0.8 s in) | contact | brake | clear (pass it) | kerb |
| rival_opening (the nearest rival 3..80 m ahead pulls into your lane and is held up; one side open, a van alongside on the other) | follow | brake | overtake (open side) / contact (van side) | kerb |
| blocked_lane (roadworks in your lane) | contact, knocked across | brake, squeeze across | clear | kerb |
| narrowing (cones close your lane, a van alongside in one neighbour) | contact, merge | brake, merge behind the van | clear (free side) / contact (van side) | kerb |

  Bottom is safe in every situation; several responses are safe where the road allows (tested over every kind, seeds and lanes). The selection may change until the
  deadline; the CURRENT selection is resolved AT the deadline; no selection is top.
- **Outcomes** (`outcomes`, bounded, recoverable): clear x0.97; overtake +4 m/s for 2 s and the rival at x0.72 for 2.5 s; follow x0.85; brake x0.72; contact x0.5 and capped
  at 70 % for 2 s; kerb x0.65, capped at 80 % for 1.5 s. Never below the minimum: the worst play still finishes (about 130 s; the bound is length / min + 30 s).
- **Rivals** keep their lanes and move aside (to a free lane) when within 14 m ahead or 10 m behind in the car's lane, so no car is driven through.
- **Finish**: the exact crossing time; position = 1 + rivals that crossed earlier; the car rolls to a stop and the activity is done `finish_hold_s` (3 s) later.
  `result().race = {won: position == 1, position, time_s (from the green light)}`.

### Calibration (`tools/race/calibrate_race.gd`, seeds 7 and 23)

| Rhythm (bot quality) | Best driving | No driving (always top) | Worst driving |
| --- | --- | --- | --- |
| perfect | 1st, 61.5 s | 2nd/3rd, 70-71 s, 8-9 contacts | 4th, 72-74 s |
| good (0.75) | 2nd, 69 s | 4th, 79 s | 4th, 82 s |
| ok (0.5) | 4th, 78 s | 4th, 91-93 s | 4th, 93 s |
| poor (ok/miss mix) | 4th, 104 s | 4th, 119 s | 4th, 119 s |
| all misses | 4th, 114 s | 4th, 130 s | 4th, 131 s |

Rivals finish at about 69, 70.5 and 72 s. Winning needs both near-perfect rhythm and good driving.

### In the world (ruling 38, contract 10)

The race's `things()` (dynamic things through the A8 port; sheets under `assets/story/race_space/sprites/` with grid sidecars):

| Thing | Sheet | Frames |
| --- | --- | --- |
| `race_dash` the bonnet and dash, 1.4 m ahead of the eye, 3.4 x 0.42 m | `dash` [1, 5] | steady, leaning left, leaning right, braking (dash brake lamp), jolted (sparks) |
| `race_gauge` the countdown, on the dash, during a situation | `gauge` [9, 1] | eight segments down to the deadline (green, amber, red), then a red flash |
| `race_speedo` the speed bar | `speedo` [8, 1] | speed in eighths |
| `race_choice` the chosen opening lit on the road, 12 m ahead | `lane_glow` [2, 1] | pulsing on the beat |
| rivals `rival_0..2` | `car_rival_0..2` [3, 1] | cruising, brake lights, contact (sparks) |
| traffic `tr_<n>`, roadworks `bar_<n>`, cones `cone_<n>` | `car_taxi`, `car_van`, `barrier`, `cones` | brake lights / contact; lamps flashing on the beat |
| `race_lights` | `start_lights` [4, 1] | one, two, three reds, green |
| `race_rain` | `rain` [4, 1] | falling streaks (every half beat) |

Feedback marks (`world.feedback`): a glow on the chosen opening (or on the dash for bottom) at the tap; a tick on what you got past or a cross on what you hit at the deadline;
a glow (won) or a cross on the dash at the finish. The camera: `RaceActivity.camera_pose(t)` through the stage's new `pose_fn` (hook H8.2): on the course at the car's
distance and eased lane (1.5 beats, smoothstep), the course heading plus a yaw of at most 10 degrees into a lane change, pitch -2 degrees (-3 for a second when braking or hit),
**no roll and no shake**. Nothing is drawn on the canvas except the feedback marks; the HUD and the pads are the run's.

### Entry and return (`RaceStageHost`)

- On the phase start of a race scene (`content/races/<theme>.json` `scene`) the street's stage is built once, hidden (measured in the build log; a hitch at the hangar's
  arrival, not at the seat).
- The hangar's hotspot `space_race.race` (the racer) seats the race (contract 4: `{"activity": "race"}`; RunMinigameHost builds the ActivityRequest with the theme's `race` block).
- On the seat's downbeat the street becomes the active stage (`play.active_world = race_space`), its camera the car's. RunPlay keeps it through the race scene's phase starts.
- When the activity is done the rave's stage is shown again (`RunPlay._show_world`), the camera at the racer; RunMinigameHost applies the result
  (`RaveSave.record_race(theme, won, time_s)`: runs, wins, best time); then `return_hotspot` (`space_race.back`) is selected when selection opens and the run walks back to the hub.

### Lead-file lines touched

- `src/run/run_play.gd`: member `race_host` (+1), `race_host = RaceStageHost.new(self)` in `_ready` (+1), `race_host.step(t)` after `minigames.update(t)` in `_advance` (+1),
  `_on_phase_start`: `if world != active_world and not race_host.owns_stage():` (1 changed).
- `src/story/story_stage.gd`: member `pose_fn` (+1), in `update` `if pose_fn.is_valid(): pose = pose_fn.call(t)` (+2) (hook H8.2).
- Not touched: `run_minigame_host.gd`, `run_data.gd`.
- Also changed: `tools/run/make_bedsit.py` (the hangar as an activity scene, the race hotspot replayable), regenerated `content/paths/bedsit/run.json` and
  `hotspots/space_rave.json`; `tools/story/build_space_rave.py` and `content/raves/space.json` (`race.course` = `race_space`).

## The four races (per theme)

`python3 tools/story/build_race.py --theme <space|magic|dinos|transport>` writes the street map, story file, course and art; for a theme other than Space it also writes the race data
`content/races/<theme>.json` (Space's rules and numbers, the theme's own course, scene and return hotspot). That data file is the switch: `make_bedsit.py` makes the rave's race entrance
(`<prefix>_race`) a real hangar scene wherever it exists, and `rave_builder.py` names `race_<theme>` as the theme file's `race.course` then. Shots: `docs/shots/bedsit/<theme>/race_contact.jpg`
(`RACE_PREFIX=<space|magic|dino|transport> bash tools/dev/shoot_race.sh <out dir> <sheet.jpg>`). Tests: `tests/test_race_themes.gd` (all four) and `tests/test_race.gd` (Space numbers).

| | Space | Magic | Dinos | Transport |
| --- | --- | --- | --- | --- |
| Street (scene prefix) | The Mothership Strip, `race_space` (`space`) | The Moonlit Lane, `race_magic` (`magic`) | The Lava Ledge, `race_dinos` (`dino`) | The Wet Rally Street, `race_transport` (`transport`) |
| Course (2200 m + run-off) | 5 bends, long finishing straight | 6 gentle alternating bends (r 70 to 130) | 6 tighter bends up to 90 degrees (r 45 to 90), run-off 170 m | S-bends and one 90 degree corner (r 60) |
| Setting | wet neon city, rain, Mothership in the sky | moonlit cobbles, castle walls with arched windows, castle and hills on the horizon, drifting fireflies | basalt cliffs with lava cracks and caves, torches, volcano and pterosaurs, falling embers | wet terraces and depots, sodium lamps, signal and bus-stop signs, cooling tower and gasometer, rain |
| Vehicle (dash) | hover racer bonnet | broomstick: handle, gloved hands, lantern (brake light) | ranger jeep: bonnet, roll bar, spare wheel | rally hatchback: chequered stripe, number roundel |
| Rivals (3) | hover racers | witches on brooms | jeeps | rally hatchbacks |
| Traffic (braking car, van) | taxi, van | gilded coach, hay cart | ranger pick-up, truck (the van, recoloured) | black cab, double-decker bus |
| Roadworks, cones | striped barrier, cones | planks with cream stripes, blue crystal cones (recoloured) | fallen planks with amber stripes, lava-red cones (recoloured) | striped barrier, cones |
| Signs | neon noodles, alien, planet, cocktail, rocket | neon crescent, star, flask, wand, key | footprint, egg, bone, fern, volcano | arrow, signal, P roundel, bus, chevrons |
| Art status | placeholder | placeholder | placeholder | placeholder |
| Placeholder (all) | everything | everything: no painting; vehicles and signs are first drawings; traffic cart, coach and witches are simple sprites; no people in the lane | everything: no painting; the jeep, ute and truck are boxy; truck = recoloured Space van; barrier and cones are recolours of Space's | everything: no painting; barrier and cones identical to Space's; the bus is the van with a second window row |

## Placeholders (not finished art)

Everything under `assets/story/race_space/` is PLACEHOLDER art drawn by `tools/story/race_art.py`: the asphalt, paving, kerb and roof tiles, the three facades, the sky
strip (the Mothership over a skyline), the lamp, cat's eye, gantry, banner, five neon signs, three shop fronts, the cars (three rivals, a taxi, a van), the roadworks and
cones, the bonnet and dash, the gauge, the speed bar, the lane glow, the start lights and the rain. No people stand in the street (the story file casts no actors). No
engine sound, no tyre or contact sound (the run's sfx bus has no race cues yet).

## Hooks for the other raves

- A theme is a `THEMES` entry in `tools/story/build_race.py` (palette, layout, lengths) plus `content/races/<theme>.json` (course id, rivals, situations, timings,
  `scene`, `stage_world`, `return_hotspot`) and the theme file's `race` block. The simulation, the stage host and the tests read only data.
- `RaceStageHost` finds race scenes by scanning `content/races/*.json`.

## Not done / open

- `RaveSave.record_race` (contract 2/6) stores wins, runs and the best time, not the position; the position is in the result (`result().race.position`) and the host's
  log only. Storing it is a contract amendment for the lead.
- The swap is a cut on the seat's downbeat from the hangar's racer to the driver's seat (ruling 37's "stage swap"); ruling 38's "seamless" is met by no fade, no card and
  the same HUD and pads, not by a continuous camera move from the room into the street.
- No speed FOV effect (`speed_fov_gain` 0): the projector's field of view is fixed (`StoryProjector.FOV_V`), the dynamic things would drift off their places.
- Nothing has been tried on a phone.
- The three new streets have no concept painting behind them (`art/reference/doom_worlds/` is not in this branch): all their art is placeholder, labelled so in each
  `assets/story/race_<theme>/manifest.json` (`placeholder: true`, `px_scale_note`). Sprite cells are at the Space race's size (160 x 104 vehicles, 448 x 56 dash cells), not yet at the
  ruling 36 256 px class. No engine, tyre or contact sound for any theme.
- Ride heights, speeds and the calibration table above were measured on Space only; the other themes use the same numbers (same rules), so their finish times match Space's for the
  same play (a race is a function of distance, not of the street's bends).
