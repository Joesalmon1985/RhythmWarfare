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

## Checks

    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter bedsit
    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/run/check_path.gd -- bedsit
    bash tools/dev/shoot_bedsit.sh            (the shots in docs/shots/bedsit/)

Camera clearance: the walls are 2.0 m (east, west) and 2.5 m (north, south) from the camera, so the 2.5 m magnification rule of `docs/art/CAMERA_CLEARANCE.md` would flag the
east and west facings (the room is not in that check's scene list). The 0.6 m rule the brief asks for holds with a wide margin; the art is drawn at 160 texels per metre to
keep the magnification near 1.4x at 2 m.
