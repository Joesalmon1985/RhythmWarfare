# The bedsit opening: how to launch it and what is in it

Package "bedsit" of `docs/briefs/BEDSIT_RAVES_BRIEF.md` section 2 (branch `wip/play-bedsit`, from `feature/bedsit-raves`). Contracts 1, 2, 6 and 9 of
`docs/parallel-development/CONTRACTS.md`; rulings 35 to 37 of `LEAD_RULINGS.md`.

## Launch

    tools\dev\play_bedsit.cmd          the bedsit, facing north        (PowerShell, cmd or a double-click)
    tools\dev\play_bedsit.cmd E        start facing east (N, E, S or W: RW_BEDSIT_FACING, written to the save as a turn is), a development aid
    tools\dev\play_bedsit.cmd --dev-keys     number keys 1 to 8 pick any choice on show in the bedsit too (RW_DEV_KEYS=1; off there by default)

Touch (or click): the left fifth of the picture turns left, the right fifth turns right, the bottom middle stays, the top middle leaves through the threshold you face, and the
middle of the picture is the room itself (the way out, once it is open). Desktop: the arrow keys are the same four regions (left, right, down = stay, up = leave). The number keys
1 to 8, which pick the choices on show elsewhere in the game (INTERACTION_DESIGN.md 2.6), are off in the bedsit (they would pick any threshold whatever the facing) unless
`RW_DEV_KEYS=1`. See "Playing it" at the end.

It sets `RW_BEDSIT=1` and `RW_RUN_PATH=bedsit` and runs `tools/dev/play_tracks.sh --run` (the play copy of the save, the imported track packs). **F3** shows the
overlay line; in the bedsit it ends with `compass N  theme Space` (and only then: the compass and the theme name are drawn nowhere else).

The flag, in the order the code reads it:

- `RW_RUN_PATH=bedsit` is the existing way to start any path (`run_play.gd` `_ready`).
- `RW_BEDSIT=1` starts the bedsit path when nothing else names a path (one added line in `run_play.gd` `_ready`, `BedsitNav.enabled()`). Unset or anything else: off. The main
  run, every other path, the saves and the tests do not change; `test_the_flag_is_off_by_default_and_the_legacy_run_is_untouched` pins it.
- `python3 tools/run/make_bedsit.py --bedsit` writes the path's files; without `--bedsit` the tool writes nothing.

## What is built

| Piece | Where | Engine today |
| --- | --- | --- |
| The room | `content/story/maps/bedsit.json`, art in `assets/story/bedsit/` | drawn by StoryWorld as any map |
| The path | `content/paths/bedsit/` (`run.json`, `music.json`, `hotspots/bedsit.json`) | loads clean (`tools/run/check_path.gd bedsit`: 0 errors) |
| Themes and routes | `content/bedsit/themes.json` (the contract fixture's shape), `routes.json` | read by `BedsitNav` and the tests only |
| The four regions | `content/bedsit/themes.json` `regions`; `src/bedsit/bedsit_room.gd` (`BedsitRoom`) on `src/bedsit/bedsit_nav.gd` (`press`) | **played by touch**: `RunPlay.dispatch_tap` (H5.5) gives a stage tap to the `world_regions` owner while the bedsit is the scene and `BedsitRoom.tap` turns, stays, leaves or touches the room ("Playing it") |
| `relaxed: true` on the node | `run.json` node `bedsit` | **read** (`run_engine.gd`, hook H1.7): a failed block costs no energy, and with nothing touched the scene stays (no default exit fires) |
| `hold_bars: 4`, `choice_view: true` | `run.json` node `bedsit.bedsit.viewpoint`, and `choice_view` on the four waypoints | descriptive: the camera is held by `BedsitRoom` instead (the rail retargeted to the facing's waypoint and held: no glance, stroll or drift, ruling 35a) |
| The track | `content/run/track_scenes.json` `paths.bedsit.bedsit` (Chase & Status remix of Valley of the Shadows) | plays when the track pack is on the machine (`play_tracks.sh`); else the placeholder pack `bedsit_room` (174 BPM, synthesised) |
| Sound cues (traffic, wardrobe shimmer, jungle) | none | the project has no ambient-cue hook for a map; not done |

Relaxed inspection (brief section 2) is real: the engine reads `relaxed` (`run_engine.gd`, H1.7), so a scene in which nothing is touched ends by staying in the bedsit with the
facing kept, and missed blocks cost nothing; the rhythm never forces a departure. Only the top region (the facing's threshold) or the way out leaves.

## The routes and the placeholders

Facing to rave (fixed by the brief, `content/bedsit/themes.json`): **N Space, E Dinosaurs, S Magic and unicorns, W Transport**. The top region leaves for the scene id in
`content/bedsit/routes.json`: `space_rave`, `dino_rave`, `magic_rave`, `transport_rave`. (CONTRACTS.md writes the scene ids `rave.<theme>`; routes.json carries both, `scene` and
`scene_contract_id`, so the lead picks one name when the raves land.)

Those scenes do not exist, so in `content/paths/bedsit/run.json` each id is a **placeholder node** (`"placeholder": true`) that resolves to the bedsit itself: its route `bedsit`
(a `loop`) comes home facing the same way. A second route `out` leads to `bedsit.end`, the development way back to the Warehouse (a path must end somewhere; its hotspot is locked
behind the flag `bedsit_dev_exit` in the bedsit itself).

**The exact change when a rave lands** (for the lead): in `content/bedsit/routes.json` set `"placeholder": {"active": false, ...}`; then in `tools/run/make_bedsit.py` take that
rave out of the `PLACEHOLDER_RAVES` table, regenerate with `python3 tools/run/make_bedsit.py --bedsit`, and route the facing's `next` edge to the real node (or, across paths, request
`{path, node, kind: scene, when: soonest}` through the TransitionPort, contract 1; ruling 37: leaving goes at the next block boundary). The data an engine hook reads per facing is
`run.json` node `bedsit.bedsit.facings.<N|E|S|W>`: `{yaw, waypoint, threshold, theme, route, shows}`.

## State

`bedsit_facing` ("N" | "E" | "S" | "W"; a new run starts "N") is part of the version 3 save (`RunProgress` VERSION 3; the loader takes 2 and 3 and migrates a 2: CONTRACTS.md 6,
H6.1). Every turn in play writes it at once (`BedsitRoom` calls `RunProgress.set_bedsit_facing`, which saves), and every homecoming to the bedsit (from a rave, or the run's first
scene) cuts the camera to the saved facing while the passage frame is shut. `BedsitNav.press` stays a pure function on the dictionary it is given (BedsitRoom hands it a copy).
A new run (`run_started`) faces north again. The overlay reads `Session.run_progress.data`. Turning wraps through all four directions: four left or four right turns are the same
facing, bottom keeps it (tests/test_bedsit.gd; by tap in the running scene, tests/test_bedsit_play.gd).

## The room

One sector, 4 x 5 m (x -2..2, z -2.5..2.5), 2.5 m high, eye 1.6 m, the camera at the middle (0, 0); `bedsit_n/e/s/w` are that one point at yaw 0, -90, 180 and 90 (270 is -90).
Every wall picture is a decal on its own wall, so the room is the same room from every facing; small things are billboards. 160 texels per metre throughout (style guide section 7).
Art: `python3 tools/story/build_bedsit.py` (art in `tools/story/art/tex_bedsit.py`, a pixel-painting kit in `bedsit_draw.py`), which also writes the map. Contact sheet of every
texture: `python3 tools/story/build_bedsit.py --sheet <file.png>`.

| Facing | The wall | The threshold (no label) |
| --- | --- | --- |
| North, Space | the window: night sky, ringed planet, a nebula glow behind the rooftops; curtains; radiator; two posters | a model rocket on the sill, a star mobile, cold violet light across the boards |
| East, Dinosaurs | the desk with decks, a mixer and monitors; headphones; coat hooks; a poster | a jungle poster whose middle is a real opening (glowing jungle, an eye, leaves breaking out over the paper), a plastic dinosaur on the desk, a fern, green light |
| South, Magic and unicorns | the wardrobe, one door ajar; a shelf; a clothes rail | iridescent light pouring from the gap and across the floor, a unicorn figurine, fairy lights, pink and cyan light |
| West, Transport | the bed (headboard to the north), two posters over it, a mirror | the door with a bus timetable pinned on it, a toy car, a blinking amber indicator, orange street light under the door |

Floor: oak boards with a kilim rug, a record, socks, slippers, a laundry heap, the headphone lead and painted pools of each threshold's light. Lived-in and warm; the
thresholds are the strange part.

## The shots (what reads and what does not)

`docs/shots/bedsit/bedsit_contact.jpg`: the four facings at 16:9 (top row) and 20:9 (bottom), made by `tools/dev/shoot_bedsit.sh` (the map through the game's low-res pipeline).

- Reads at a glance: **North** the window with the night sky, planet and rooftop glow, rocket on the sill, star mobile. **East** the jungle poster with its glowing circular opening and leaves breaking out
  over the paper, the decks, the plastic dinosaur. **South** the wardrobe with the iridescent slot, the unicorn on the shelf, fairy lights, the clothes rail. **West** the door with the bus timetable,
  the amber fanlight with a bus passing, the indicator lamp.
- Does not read yet: with the camera 2 m from the east and west walls (2.5 m from north and south) at eye 1.6 m and a level gaze, the picture spans 0.63 m to 2.57 m up the wall, so **the floor, the rug,
  the bed's mattress, the desk's legs and the toy car are out of frame** in every facing (the headboard, the posters over it and the desk top show). The painted pools of coloured light on the boards are
  therefore never seen; the lights still colour the walls. The engine now has a held, authored pitch at a choice viewpoint (a rail place's `pitch`, `player_hold` with a pitch,
  merged into this branch), but the bedsit does not use it yet (its camera is held level by `BedsitRoom` on the four waypoints); a steady tilt of about 10 degrees down would bring the
  floor in. The blinking of the indicator and the traffic, wardrobe and jungle sounds cannot be seen or heard in a still: no ambient sound cue hook exists for a map.
- The dado (the lower wall, olive) is about a third of every frame; it could go warmer.

## Checks

    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter bedsit
    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/run/check_path.gd -- bedsit
    bash tools/dev/shoot_bedsit.sh            (the shots in docs/shots/bedsit/)

Camera clearance: the walls are 2.0 m (east, west) and 2.5 m (north, south) from the camera, so the 2.5 m magnification rule of `docs/art/CAMERA_CLEARANCE.md` would flag the
east and west facings (the room is not in that check's scene list). The 0.6 m rule the brief asks for holds with a wide margin; the art is drawn at 160 texels per metre to
keep the magnification near 1.4x at 2 m.


## The Space rave (package "space", branch `wip/play-space`)

Brief sections 3 and 4. A real node now: `space_rave` replaces its placeholder (`routes.json` `landed`, `LANDED` in `tools/run/make_bedsit.py`; the other three raves are still placeholders).

    tools\dev\play_bedsit.cmd --rave space             start inside the rave (RW_RUN_START=space_rave), the bass locked
    tools\dev\play_bedsit.cmd --rave space --fixed     the same with the bass already fixed (RW_SPACE_BASS_FIXED=1)
    python3 tools/story/build_space_rave.py             the map, story file, theme file and placeholder sprites
    python3 tools/run/make_bedsit.py --bedsit           the path (nodes, hotspots/space_rave.json, music and track entries)
    bash tools/dev/shoot_space.sh                       docs/shots/bedsit/space/space_contact.jpg

- **Place**: `content/story/maps/space_rave.json`, the Mothership's ring (traced MAP11 in `doom_mothership.json`, copied without a merge from `feature/doom-layout-worlds`) rebuilt approximately: twelve ring
  pieces round a 12-sided void 9 m down, railings on every void edge, void haze, `visibility: clip`. Piece 0 (south) is the hub with the airlock behind it (arrival, the way home), piece 6 the stage (a dais 0.9 m up two
  0.3 m steps), 7 the cloakroom, 5 the bar, 8 the hangar (a big door, a racer glimpsed). Art: the Mothership's ribs, mint light, windows, planets, LED bars, speakers; placeholders drawn by
  `build_space_rave.py` (`sr_rail`, `sr_deck`, `sr_knob_0..3`, `sr_hatch`, `sr_racer`).
- **Scenes** (`content/paths/bedsit/run.json`, world `space_rave`): `space_rave` (hub: choice viewpoint `hub_view`, `hold_bars` 8, arrival `space_arrive`; choices are the DJ waving, the attendant, the bartender, the pilot and
  the airlock hatch; relaxed, stays by default), `space_stage` (rail steps, then the deck; the deck hotspot runs the activity), and placeholders `space_cloakroom`, `space_bar`, `space_race` that loop back. The activity id
  per station is in `content/raves/space.json` `activities` (the hook for the other agents: `cloakroom`, `bar`, `race`). The routes of contract 3 (via polylines with holds) are in that file's `routes`.
- **Bass puzzle**: `SpaceRaveHost` (`src/bedsit/space_rave_host.gd`) locks `bass` on entry unless `bass_fixed`; `BassKnobActivity` (`content/minigames/bass_knob.json`, rhythm mode): two resisting touches, the third frees the knob;
  the host then schedules `unlock_stem_at` for the next bar line (one-bar ramp) and, on the same line, the stage lights (`piece_on` of `pylon_beams`, `ring_lights`, `hologram_dome`) and the crowd (`crowd_cap` 100, quiet 25 before).
  The flag `rave.space.bass_fixed` is set by the result and kept for the run. Per ruling 38 there is no close-up: the knob is the map thing `bass_knob` (frames by `thing_pose`) and the touch is a world region over its screen point (`SpaceRaveHost.hit`).
- Lines touched outside the new files: `src/run/run_play.gd` (member `rave_host`; `_rave_enter` call at the top of `_on_phase_start`; `_rave_step` after `minigames.update`; the helpers `_rave_enter`, `_rave_step`, `rave_hit`),
  `src/run/run_minigame_host.gd` (`hit`: a view-less activity asks `rave_hit`), `src/story/story_stage.gd` (`crowd_cap` and its action), `src/story/world/story_map.gd` (a marked void is exempt from the reachability check),
  `tools/story/preview_map.gd` (screenshot env vars), `tests/test_bedsit.gd` (a landed rave is not a placeholder).

## The Space rave's activities (integration, ruling 38, contract 10)

`tools\dev\play_bedsit.cmd --rave space`: hub, then the west alcove (cloakroom), the east alcove (bar) and the stage (the bass knob) each play in the room, with the pads morphing into the activity's controls.

| Scene | Route from the hub | Hold (the camera while the activity is seated) | Hotspot (window `any`) | The activity's things |
| --- | --- | --- | --- | --- |
| `space_cloakroom` | hub `w`: `cloak_door`, walks to `cloak_hold` (2 bars, then holds 10) | `cloak_hold`, in ring piece r7 facing the alcove | `space_cloakroom.cloakroom` on the map thing `cloak_counter` | coats on `cloak_rail`, the tag symbol over the counter; the customers `customer_0..7` and the `attendant` are crowd actors of the alcove; `cloak_lamp` lights when it is done |
| `space_bar` | hub `e`: `bar_door`, walks to `bar_hold` | `bar_hold`, in ring piece r5 | `space_bar.bar` on `bar_counter` | the glass and the order bubble; the `customer` and `bartender`; `bar_shelf_1..4` light as drinks are served |
| `space_stage` | hub `n` | `deck_view` | `space_stage.deck` | the bass knob (0.35 m, frames stuck, straining, free, up); the DJ beckons, waits, cheers |

- Layouts (where the things stand) are in `content/bedsit/themes.json`: `cloakroom.space.layout` and `bar.space.layout`, written by `tools/story/build_space_rave.py` from the same numbers as the map, so they cannot drift. `tools/run/make_bedsit.py --bedsit` now keeps those blocks.
- Placeholder art: the sheets under `assets/story/mothership/sprites/` (`cloak_coat`, `cloak_symbols_space`, `bar_glass_space`, `bar_order_space`, `sr_knob`, each with a `{"grid": [cols, rows]}` sidecar), the two piece sprites (`pc_lamp_lit`, `pc_glass_lit`) and every person (the ring's alien rigs).
- A finished activity sets `rave.space.<activity>_done`; `SpaceRaveHost` re-lights its pieces on every entry and sets the run flag `space_<activity>_done` that hides the activity hotspot.
- Shots: `tools/engine/shoot_space_activities.gd` (two window sizes) and `tools/dev/space_activities_sheet.py`: `docs/shots/bedsit/space/activities.jpg`.
- Not done: the hangar (`space_race`) is still a placeholder; `view_pitch` is not implemented by the engine (no waypoint pitch), none is used.


## The street race (package "race", branch `wip/play-race`)

Brief sections 8 to 10; the whole account is `docs/bedsit/RACE.md`.

    tools\dev\play_bedsit.cmd --rave space     the hub; the pilot (south-west) leads to the hangar; touch the racer
    tools\dev\play_bedsit.cmd --race space     start in the hangar (RW_RUN_START=space_race); touch the racer
    python3 tools/story/build_race.py --theme space     the street map, story file, course file and placeholder art
    python3 tools/run/make_bedsit.py --bedsit           the path (the hangar node and its race hotspot)
    bash tools/dev/shoot_race.sh                        docs/shots/bedsit/race/contact.jpg

- The hangar `space_race` is a real scene now: the route from the hub ends at `hangar_view` facing the racer; the hotspot `space_race.race` (the racer, window `any`) seats the
  race on the next block start; it stays available after a race (replay), and needs none of the three tasks.
- The race plays on the street stage `race_space` (cut on the seat's downbeat, no fade), pads judged, the four regions of the picture drive; afterwards the hangar is back,
  `raves.space.race` (runs, wins, best) is saved, and the way back to the hub is selected.


## The other three raves (branch `wip/play-raves`): Magic, Dinosaurs, Transport

All four raves are real nodes now (`LANDED` in `tools/run/make_bedsit.py`: N space, S magic, E dinos, W transport; `routes.json` `landed` is true for each). One shared generator
(`tools/story/rave_builder.py`, art kit `rave_art.py`, themed rigs `rave_people.py`) builds every rave; `SpaceRaveHost` serves every theme (the theme is read from the scene id prefix);
`tests/rave_theme_test.gd` is the shared test body.

    tools\dev\play_bedsit.cmd --rave magic          start in the Magic rave (RW_RUN_START=magic_rave)
    tools\dev\play_bedsit.cmd --rave dinos          start in the Dinosaur rave (RW_RUN_START=dino_rave)
    tools\dev\play_bedsit.cmd --rave transport      start in the Transport rave (RW_RUN_START=transport_rave); add --fixed for the bass already fixed
    python3 tools/story/build_<magic|dinos|transport>_rave.py    the map, story file, theme file, activity layouts and art of that rave
    python3 tools/run/make_bedsit.py --bedsit                    the path (every landed rave's nodes and hotspots; keeps every theme's cloakroom/bar blocks in themes.json)
    bash tools/dev/shoot_rave.sh <theme>                         docs/shots/bedsit/<theme>/<theme>_contact.jpg (hub, approach, deck before/after, cloakroom and bar holds)
    bash tools/dev/shoot_activities.sh <theme>                   docs/shots/bedsit/<theme>/activities.jpg (the three activities in the run scene, 16:9 and 20:9)

| Rave | Scene prefix | Geography (approximate, hand-built) | Shape | Stations |
| --- | --- | --- | --- | --- |
| Magic and unicorns | `magic_` | the Chill-out lounge | an octagonal bowl of stepped tiers round a sunken dance well | stage N, cloakroom NW, bar NE, carriage house beside the cloakroom |
| Dinosaurs | `dino_` | the Underworld | a basalt ledge, a railed causeway over a lava gulf, two islands | stage N at the causeway's end, cloakroom cave and garage on the west island, tent bar on the east island |
| Transport | `transport_` | the Dock | a wet street forecourt (rain, `weather` on the map), a pair of tracks a step down, a long roofed depot hall | stage N (a loading dock, a locomotive's face behind the DJ), left-luggage cloakroom bay W, ticket-office bar bay E, garage beside the stage |

- Every stage is north (frame phi 180, origin 0): `BassKnobActivity` puts the knob at world (0, -25.12) in the sector `stage`.
- Every theme has a race (`content/races/<theme>.json`, built by `tools/story/build_race.py --theme <x>`): Space's rules and numbers on four courses
  (`race_space`, `race_magic` the Moonlit Lane, `race_dinos` the Lava Ledge, `race_transport` the Wet Rally Street). The Magic, Dinos and Transport race art is a
  PLACEHOLDER (`manifest.json` `placeholder: true`: not drawn from a painting, Space's cell size not the 256 px class, no race sounds). The `<prefix>_race` hangar node
  is a real race scene in all four (`activity_scenes` in `make_bedsit.py`; the race hotspot is replayable). `play_bedsit.cmd --race <theme>` starts in that hangar.
- **The bedsit's way out (ruling 41).** The opening is finished once ANY ONE rave has all three of its activities done: the bass fixed, the cloakroom done and the bar done
  (the save's `raves.<theme>.bass_fixed`, `cloakroom_done`, `bar_done`). The player does not have to visit all four raves (brief section 10), and a visit alone, or two of the
  three activities, does not open it. `SpaceRaveHost.opening_done` checks this at every scene start and sets the run flag `bedsit_way_out`; the bedsit's hotspot `bedsit.way_out`
  (on the door in the WEST facing, anchor `{"pos": [-1.9, 1.35, 0.6]}`: see "Playing it") needs that flag and leads to `bedsit.end`, then the Warehouse. Once open it stays open for the run (the puzzles are kept for the run, and a new run
  starts them over); the four raves stay reachable from the bedsit all the while. The development exit `bedsit.dev_exit` (flag `bedsit_dev_exit`) is unchanged. The path declares
  the gate (`run.json` `path.ending_gate`), so `tests/test_run_matrix.gd`, whose bot plays no activities, lets the bedsit live in its loop; `tests/test_bedsit_opening_end.gd`
  proves the gate (`--filter bedsit`).

### Magic and unicorns (`tools/story/build_magic_rave.py`): PLACEHOLDER art

- Tiles **borrowed** from the Chill-out lounge (`tools/story/borrowed/doom_lounge/`: curtain, marble, wood, rug, potion shelf, lamp, plant), recoloured violet and pearl.
- **Drawn here, all PLACEHOLDER** (procedural, not hand-finished; ruling 36): everything iridescent (the pearl walkway, the moss ring and its toadstools, the velvet ring, the
  well's floor), the deck, the knob frames, the door home and the three stage pieces (`mg_aurora`, `mg_sparkle_ring`, `mg_orb_dome`).
- **People**: the Mothership's alien rigs recoloured pastel with a spiral unicorn horn (`rave_people.py`): PLACEHOLDER figures, not the 256 px Floor-guide standard. The bar's
  customer is this rave's own `antenna` rig in that dress (`themes.json` `bar.magic.customers[].kind` is `horn`: the dress named; nothing draws `kind` on its own).
- Activity sheets (copied PLACEHOLDERS): `cloak_symbols_magic`, `bar_glass_magic`, `bar_order_magic`, `cloak_coat`, `sr_knob`. The art's manifest and every sheet's sidecar say
  `"placeholder": true` (`tests/rave_theme_test.gd` asserts it for Magic, Dinosaurs and Transport).

### Dinosaurs (`tools/story/build_dinos_rave.py`): PLACEHOLDER art

- Tiles **borrowed** from the Underworld (`tools/story/borrowed/doom_underworld/`).
- **Drawn here, all PLACEHOLDER**: the ledge's dressing, the causeway railings, the lava, the tent bar, the cloakroom cave's desk and hides, the ribcage arch, the deck, the knob
  frames, the door home and the three stage pieces (`dn_lava_sheets`, `dn_fire_ring`, `dn_ember_dome`).
- **People**: the alien rigs recoloured in scaled greens, oranges and teals with crest spikes and two brow horns (`rave_people.py`): PLACEHOLDER figures, not dinosaurs drawn to the
  Floor-guide standard. The bar's customer is this rave's own crested `antenna` rig (`kind` `crest`).
- Activity sheets (copied PLACEHOLDERS): `cloak_symbols_dinos`, `bar_glass_dinos`, `bar_order_dinos`, `cloak_coat`, `sr_knob`; manifest and sidecars `"placeholder": true`.

### Transport (`tools/story/build_transport_rave.py`)

- Map `content/story/maps/transport_rave.json` (10 sectors): `yard` (x -9..9, z 4..18, open sky, `weather` rain 0.75 with drips off the hall roof's edge), `tracks` (x -13..13, z 0..4,
  floor -0.2), `hall` (x -13..13, z -17..0, a truss roof at 9 m), the stage alcoves `ap6_a`, `ap6_b`, `stage`, `cloak` (phi 270), `bar` (phi 90), `hangar` (phi 180 at x 9.5) and `home` (a
  bus-stop door behind the forecourt). Routes from `hub_view` (0, 15): over the crossing (`cross`) to `hall_c`, then to each station. Hub bearings: attendant 36, bartender -36, pilot -14 degrees.
- Art in `assets/story/rave_transport/`. **Borrowed** from the Dock (`tools/story/borrowed/doom_dock/`): asphalt, concrete, walkway and blue floors, brick, steel, warehouse, shutter and blue walls,
  trim, truss roof, bollard, street, hanging and wall lamps, neon, crate, case, drum, pallets, van, fence, lit windows, towers. **Drawn here, all PLACEHOLDER** (procedural, not
  hand-finished; ruling 36): the track ballast and rails, the station wall tiles, the dock chequer plate, the warehouse shutter up on a purple-lit crowd (after the Dock painting), the
  locomotive's face, the double-decker, the rally racer, the colour-light signals, the departures board, the garage door, the bus-stop timetable, the cone, the left-luggage hatch,
  the ticket counter, the left-luggage desk, the lockers, the hi-vis vest rail, the console, the deck, the door home, the knob frames, the sky and the three stage pieces
  (`tr_signal_beams`, `tr_track_lights`, `tr_headlamp_dome`). **People**: the Mothership's alien rigs recoloured hi-vis with a hard hat (`rave_people.py`): PLACEHOLDER figures, not the
  256 px Floor-guide standard.
- Activity sheets (copied PLACEHOLDERS): `cloak_symbols_transport` (bus, bike, train, boat), `bar_glass_transport`, `bar_order_transport` (diesel cola, tyre liquorice, road salt, headlamp lemon), `cloak_coat`, `sr_knob`;
  manifest and sidecars `"placeholder": true`. The bar's customer is this rave's own hard-hatted `antenna` rig (`kind` `hard_hat`).
- The bar's pad pictograms 1 and 2 (diesel cola `#6b3a1e`, tyre liquorice `#2a2a33`) were dark on the dark slot: `ControlPictograms` now draws any control colour under
  luminance 0.35 lifted toward white (hue kept) with a pale rim; every other theme's ingredients are above it and unchanged (`tests/test_bar.gd`).
- Shots: `docs/shots/bedsit/transport/transport_contact.jpg`, `docs/shots/bedsit/transport/activities.jpg`. The rain cannot be judged from the preview stills (the preview pipeline
  draws no motion); people are absent from the map preview (the activity sheet shows them).
- Test: `tests/test_transport_rave.gd` (the shared body, `--filter test_transport_rave`).


## Playing it: the four regions, the facing, the way out (play round 2, branch `wip/play-round2`)

`src/bedsit/bedsit_room.gd` (`BedsitRoom`, owned by RunPlay as `bedsit`) is the bedsit as a running scene. While the scene is the bedsit, `RunPlay.world_regions` holds the four
regions of `content/bedsit/themes.json` and the one dispatcher (`RunPlay.dispatch_tap`, H5.5: `ContractShapes.tap_owner` gives a stage tap to `world_regions`) hands every stage
tap to `BedsitRoom.tap`; a pad-strip tap stays the pads'. In fractions of the picture (the stage area above the pads):

| Region | Where | What it does |
| --- | --- | --- |
| left | x 0 to 0.22, full height | turn 90 degrees left: the camera turns on the spot over one bar to the facing's waypoint (`bedsit_n/e/s/w`) and holds still (no glance, stroll or drift: ruling 35a); the facing is saved at once; a pending threshold pick is withdrawn |
| right | x 0.78 to 1, full height | turn 90 degrees right, the same |
| bottom | x 0.25 to 0.75, y 0.72 to 1 | stay: the facing is kept, a pending threshold pick is withdrawn |
| top | x 0.25 to 0.75, y 0 to 0.42 | leave: the threshold of the current facing (`bedsit.threshold_<f>`) is picked; the route to its rave commits at the scene's lock and leaves on the boundary (ruling 37) |
| the room | x 0.25 to 0.75, y 0.42 to 0.72 (the gap) | the room's own hotspots that are not thresholds: the way out (and the development exit) |

Only the threshold of the facing is on show (lit, and the only one the top region can pick), so the touch target follows the facing. A turn after the lock with a pick standing is
refused (the way out is decided). The F3 overlay ends with `compass <f>  theme <name>`.

**The way out** (`bedsit.way_out`, ruling 41) stands on the room's door in the **west** facing: anchor `{"pos": [-1.9, 1.35, 0.6]}` (just off the west wall, 1.35 m up, the
door's middle; `WAY_OUT_ANCHOR` in `tools/run/make_bedsit.py`), which from the camera lands in the gap in the middle of the picture, about a third of the way across from the left.
The top of that same door (its fanlight, the timetable) is in the top region and is the Transport threshold; the middle of the door is the way out. It is on show and touchable only
while the run flag `bedsit_way_out` is set (`SpaceRaveHost.opening_done`, at every scene start, once any one rave's three activities are in the save). It never shares an anchor
with a threshold, and the thresholds are not in the gap's hit list at all, so it never loses a tie (`HotspotView.hit` gives ties to the earlier entry). From the other three facings
the door is out of the picture and the way out has no touch target.

### The player's path to the ending, tap by tap

The shortest: the Space rave, straight ahead.

1. **North** (the start): the window, the rocket on the sill, the star mobile. Tap the **top middle** of the picture: the threshold is picked; at the end of the scene the camera
   walks to the window and the Space rave's hub comes in.
2. **The Space rave's hub**: tap the **DJ** waving on the stage: the walk to the deck. Tap the **deck**, then the **knob**: it resists twice, the third touch frees it; the bass
   comes in on the next bar line, the stage lights come up, the crowd dances. Tap the **stage's foot** (the way back) to the hub.
3. Tap the **cloakroom attendant**: the cloakroom; tap the **counter**; the pads become SAME (left) and DIFFERENT (right): eight coats. The counter lamp stays lit. Back to the
   hub (its door, or the scene's default).
4. Tap the **bartender**: the bar; tap the **counter**; the pads become the four ingredients: four drinks. The shelf glasses light. Back to the hub.
5. Tap the **airlock hatch** (the way home): the bedsit again, **facing north** (the saved facing). The way out is now open.
6. Tap the **left fifth** of the picture once: the camera turns to the **west** (the bed, the door, the bus timetable) and holds.
7. Tap the **middle of the door** (the middle of the picture, a little left of centre): the way out is picked; at the end of the scene `bedsit.end`, then the Warehouse.

Any rave does instead: facing **east** (one tap on the right) the jungle poster leads to the Dinosaurs, facing **south** (two taps on either side) the wardrobe to Magic and
unicorns, facing **west** (one tap on the left) the top of the door to Transport. Coming home faces the way you left; from there turn to the west (from the south one tap on the
right, from the east two taps on either side, from the west none) and tap the middle of the door. A visit alone, or two of the three activities, leaves the door shut: a tap on it
does nothing.

Proven by `tests/test_bedsit_play.gd` (the running scene, by taps through the dispatcher: all four facings, each rave's threshold and home again with the facing kept, the way out hit
at its screen position after one rave's three activities and not before) and by the virtual run `tools/dev/bedsit_virtual_run.gd` (right, right, top into Magic, home, the facing
checked in the save file):

    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter bedsit
    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/dev/bedsit_virtual_run.gd
