# The bedsit opening: how to launch it and what is in it

Package "bedsit" of `docs/briefs/BEDSIT_RAVES_BRIEF.md` section 2 (branch `wip/play-bedsit`, from `feature/bedsit-raves`). Contracts 1, 2, 6 and 9 of
`docs/parallel-development/CONTRACTS.md`; rulings 35 to 37 of `LEAD_RULINGS.md`.

## Launch

    tools\dev\play_bedsit.cmd          the bedsit, facing north        (PowerShell, cmd or a double-click)
    tools\dev\play_bedsit.cmd E        stand at the east viewpoint (N, E, S or W), a development aid

It sets `RW_BEDSIT=1` and `RW_RUN_PATH=bedsit` and runs `tools/dev/play_tracks.sh --run` (the play copy of the save, the imported track packs). **F3** shows the
overlay line; in the bedsit it ends with `compass N  theme Space` (and only then: the compass and the theme name are drawn nowhere else).

The flag, in the order the code reads it:

- `RW_RUN_PATH=bedsit` is the existing way to start any path (`run_play.gd` `_ready`).
- `RW_BEDSIT=1` starts the bedsit path when nothing else names a path (one added line in `run_play.gd` `_ready`, `BedsitNav.enabled()`). Unset or anything else: off. The main
  run, every other path, the saves and the tests do not change; `test_the_flag_is_off_by_default_and_the_legacy_run_is_untouched` pins it.
- `python3 tools/run/make_bedsit.py --bedsit` writes the path's files; without `--bedsit` the tool writes nothing.

## What is built (and what today's engine ignores)

| Piece | Where | Engine today |
| --- | --- | --- |
| The room | `content/story/maps/bedsit.json`, art in `assets/story/bedsit/` | drawn by StoryWorld as any map |
| The path | `content/paths/bedsit/` (`run.json`, `music.json`, `hotspots/bedsit.json`) | loads clean (`tools/run/check_path.gd bedsit`: 0 errors) |
| Themes and routes | `content/bedsit/themes.json` (the contract fixture's shape), `routes.json` | read by `BedsitNav` and the tests only |
| The four regions | `src/bedsit/bedsit_nav.gd` (`press(save, "left" / "right" / "bottom" / "top")`) | **not called by any tap**: the world-region dispatcher is hook H5.5 |
| `relaxed: true` on the node | `run.json` node `bedsit` | **ignored** (hook H1.7): energy still drains and a lap's default exit still fires |
| `hold_bars: 4`, `choice_view: true` | `run.json` node `bedsit.bedsit.viewpoint`, and `choice_view` on the four waypoints | **ignored** (hook H3.1): the rail still adds a glance and a stroll (both set to zero here) |
| The track | `content/run/track_scenes.json` `paths.bedsit.bedsit` (Chase & Status remix of Valley of the Shadows) | plays when the track pack is on the machine (`play_tracks.sh`); else the placeholder pack `bedsit_room` (174 BPM, synthesised) |
| Sound cues (traffic, wardrobe shimmer, jungle) | none | the project has no ambient-cue hook for a map; not done |

Because the engine does not yet read `relaxed`, a lap that ends takes the default exit, `bedsit.threshold_n`, to the north placeholder, which routes straight back to the bedsit: the
player stays in the room (the lap restarts at the bedsit), which is the intended "stay" by another road. Energy still moves with the play until H1.7.

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

`bedsit_facing` ("N" | "E" | "S" | "W"; a new run starts "N") is written by `BedsitNav.press` into the run-state dictionary it is given; the overlay reads
`Session.run_progress.data`. It never calls `RaveSave.migrate` (which stamps save version 3 on a file the loader still accepts only at version 2: hook H6.1 first). Turning wraps
through all four directions: four left turns or four right turns are the same facing, bottom keeps it (tests).

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
  therefore never seen; the lights still colour the walls. A waypoint carries no pitch today (only a rail glance does); a held downward tilt of about 10 degrees on the four viewpoints would bring the floor
  in (suggested for the hold hook H3.1). The blinking of the indicator and the traffic, wardrobe and jungle sounds cannot be seen or heard in a still: no ambient sound cue hook exists for a map.
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
