# Camera clearance (package A5: audit findings F5 and F16)

The run camera must not stare into a wall from arm's length. This page says how that is checked, what the thresholds are and why, and lists
the failing poses before and after the fixes. The check is `tools/art/camera_clearance.gd` (the runner) over `tools/art/camera_clearance_check.gd`
(the check itself); `tests/test_camera_clearance.gd` runs the same check in the suite, so a scene added later cannot bring the problem back.

    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/art/camera_clearance.gd -- [--only <regex>] [--doc after] [--direct-all]
    bash tools/dev/godot.sh --headless --path . -s tools/art/camera_clearance.gd -- --waypoints <map id>     (every waypoint of a map: clearance at its yaw and +-30 degrees)
    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/art/camera_clearance.gd -- --search <scene id>   (tries smaller strolls and glances, other places)

Every failing row gives the camera as `RW_STORY_CAM=@x:z:yaw:pitch`, so the frame can be shot with the screenshot aid of `src/story/story_stage.gd`.

## What is checked

- **Every scene, every way in.** The 36 scenes of the main run and the 46 of the three paths (gospel, squadron, ember). Each is played the way a player
  comes into it: the run's first scene from its start; a world's scenes by **arrival** (the passage from another world: the cut to `rail.arrive` and the walk
  home, F16) wherever a route comes in from another world (and a path's first scene, and the Warehouse back from a path); and by the **door walk** from each
  scene of the same world that routes into it, the camera starting where the previous scene's rail ends (its top place). `--direct-all` adds every scene
  started on its own (`RW_RUN_START`, what `tools/art/audit_capture.sh` shoots).
- **The real camera.** The scene runs on `RunEngine` with the perfect bot and the default exit, its journey through `RunJourney` (the rail's places, the
  glances and strolls of every block, the heralds' opening look, the window's look at the hotspots, the walk out at beat 61) and the camera is
  `StoryPlayer.pose_at(t)`, as in `tests/test_heralds_view.gd`. A later scene is played at nine consecutive phase numbers (2 to 10): the block's glance and
  stroll are picked by `(phase * 4 + block + len(id))`, so these are every combination it can meet in a run.
- **Every half beat** (the tool and the test alike), over every lap, from the first downbeat (a door walk: from the moment it starts, three beats before).
  The run data is loaded with seed 0, so the arrangement (and with it the chart's density, which shortens moves) is the same on every run of the check.
- **Eleven rays across the picture** at the camera's pitch, edge to edge of the stage strip of a 1280 x 720 window (52 degrees high, 2.78 wide: the
  narrowest picture we ship), cast through the map's sectors: solid walls, the step walls and lintels at portals the ray cannot pass, floors and ceilings
  (sky sectors have no ceiling). The distance is the camera depth (along the view axis), which is what sets how far a wall's texels are magnified.

## The thresholds, and why

A pose **fails** when the centre ray meets a surface nearer than **2.5 m** *and* more than **half of the picture's width** meets surfaces nearer than
**2.5 m**, counting a wall only when it faces the eye within **60 degrees**.

- **2.5 m** is the audit's number. A wall face-on at 2.5 m fills the 52-degree picture from floor to well over head height (2.4 m of it) and its 128 px/m
  texels are drawn about 1.5 times their size in a 720 px window; at 1 m it is 3.7 times, the mosaic of F1/F5. Beyond 2.5 m a room starts to show its floor,
  its people and its far side.
- **The centre and half the width.** The centre alone flags a frame whose middle grazes a pillar or a door jamb with the room around it; the width alone
  flags a corridor seen along its length. Together they catch what the audit saw (the balcony's brick, the gallery's planet wall, the quiet room's door:
  80 to 100 % of the width) and pass the frames it liked (the hospital corridor, the Warehouse floor from the door). The frames used to set it:
  `warehouse_balcony__mid` (100 %, 0.8 m: fails), `mothership_reactor__end` (55 %, 2.5 m, the tube wall face-on: fails), `hospital_dayroom__mid`
  (90 %, 1.9 m: fails), `warehouse_exit__win` and `hospital_corridor__mid` (55 %, the near wall seen at a slant: pass).
- **Facing within 60 degrees.** A wall seen at a slant recedes in perspective (a corridor's side, the near jamb of a door the camera looks past); it is not a
  magnified block. Floors and ceilings always count when the centre ray meets them nearer than 2.5 m (only a look well up or down does: the dormitory's
  alcove ceiling).
- **Held for a beat.** A stare shorter than one beat (two samples; 0.35 to 0.43 s at these tempos) is a head turning past a wall, not a pose.
- **Doorways in passing are not judged**: while a journey move (a door walk, an arrival walk, a rail move; not a stroll) walks the camera through a doorway
  (within 0.9 m of a portal its route crosses) or through a sector it only passes (a stair, a corridor between two rooms); and while a move walks along a
  wall's own line (the gospel maps' spine: the route runs through the doorway midpoints on the rooms' wall line), where that wall is edge-on and the shots show
  the room beyond. Strolls are always judged.

## What it does not see

- Billboards, occluders and the choice layer's doors (a sprite can still fill the picture: look at the shots), people, and the herald.
- The bad rail (the perfect bot never holds a block) and hotspot cinematics.
- A camera off the scripted rail (a sloppy run stands elsewhere).

## The fixes (package A5)

All in the generators' data, the run files regenerated (`python tools/run/make_scenes.py`, `python tools/paths/make_squadron.py`,
`python tools/run/make_ember.py --run-only`). Each generator has a `CAMERA` table of per-scene overrides of the rail's camera fields (`good`, `arrive`,
`glances`, `strolls`); `"no turn"`, `"half"` and `"quarter"` keep the scene's own list and drop a stroll's turn or scale its distances and angles. No map,
waypoint, hotspot, route, scene length or beat changed. Regenerating also rewrote two blocks that had drifted from their generators, unchanged in value: the
main run's `mix.carry_bass` / `mix.bass_bus` (one key per line again) and the Ember run's `mix` (moved after `timing`).

| scene | change | why |
| --- | --- | --- |
| warehouse.balcony | good `balcony_rail, balcony_far` -> `balcony_rail, balcony` | `balcony_far` faced the end wall from 0.8 m (the audit's mid and end frames) |
| warehouse.chill | good `sofa_nook, sofa_front` -> `sofa_nook, chill`; strolls no turn, half | `sofa_front` stands in the sofa alcove facing its wall from 0.7 m |
| warehouse.exit | strolls no turn | the 35-degree turn ended on the tunnel wall |
| mothership.gallery | good `gallery_mid, planet_window` -> `gallery_mid, gallery_east`; strolls no turn, half | `planet_window` faced the window wall from 0.5 m |
| mothership.reactor | good `catwalk_mid, reactor_core` -> `catwalk_mid, catwalk_bridge` (still `on_stage`) | `reactor_core` faced the core's tube wall from 1.4 m |
| mothership.exit | good `airlock_door, airlock` -> `exam`; strolls no turn, half | `airlock` faced the hatch from 1.8 m; the strolls walked into the ramp's wall |
| underworld | good `arena_gate, gate_dais` -> `gate_dais`; arrive `arena_tier_l` -> `arena_edge` | the arrival (the passage window, F16) and `arena_gate` faced the tier and dais walls from 0.5 m |
| hospital | strolls no turn, half | the window's turn from the strolled spot met the ward wall by the door |
| hospital.corridor | strolls no turn | the window look met the corridor's door wall from 0.5 m |
| hospital.dayroom | good `dayroom_mid, day_tv_in` -> `dayroom_mid` | `day_tv_in` faced the television wall from 2.1 m |
| hospital.cafeteria | good `cafe_mid, cafe_serving` -> `cafe_mid` | a glance from the counter met the end wall |
| hospital.exit, hospital_late.exit | strolls no turn | the turn ended on the bandstand's hedge |
| ward.dorm | good `dorm_mid, dorm_bed` -> `dorm_door`; strolls no turn, half; glances half | `dorm_bed` faced the alcove window from 1.1 m; the look up met the alcove's low ceiling |
| ward.corridor | good `corr_mid, corr_east` -> `corr_mid`; arrive `corr_west` -> `corr_art_door`; strolls no turn, half | the window look met the door wall by `corr_east` from 2 m |
| hospital_late.quiet | good `quiet_far` -> `quiet` (home); arrive `quiet_door` -> `quiet`; strolls no turn, quarter; glances half | `quiet_far` faced the end wall from 1.5 m; the room is 2.4 m wide, so the turn from the door's facing to the room's swept a side wall; standing at `quiet_door` puts its choice door over the whole picture |
| ward_late.treat | glances half | the look up met the bed alcove's low ceiling |
| ward_late.dorm | good `dorm_mid, dorm_bed` -> `dorm_mid`; strolls no turn, half; glances half | as ward.dorm |
| squadron base.c03, air.c05 | strolls no turn, half | the turn ended on the berm and on the hangar wall |
| squadron air | good `c04_g1, c04_g2` -> `c04_g1`; strolls no turn, quarter | `c04_g2` and the strolls faced the bomber's flak windows |
| squadron city | good `c07_g1, c07_g2` -> `c07_home`; strolls no turn, quarter; glances half | inside the bomber: every step and turn met its wall |
| squadron city.c09, escape.c14 | good `g1, g2` -> `g1`; strolls no turn, half | `c09_g2` faced the office wall, `c14_g2` the cell's tally-mark wall |
| squadron escape.c13 | arrive `c13_arrive` -> `c13_home` | from `c13_arrive` the first glance met the quay wall from 1.3 m |
| ember hollow.inn | strolls no turn, half | the turn ended on the inn's wall |

The gospel path needed nothing: its scenes stand in open rooms, and the walks between them run along the spine on the rooms' wall line (judged edge-on,
above). The audit's `gospel jordan.baptism -> next` frame is that walk.

## Exceptions

| scene | pose | why it stays | shot |
| --- | --- | --- | --- |
| hospital_late.quiet | the window look's turn in (beats 46 to 48) and its hand-back (61.5 to 62.5) | the quiet room is 2.4 m wide and its default exit is behind the standpoint: the turn to the choices (the exit and the nightlights on the side walls) sweeps across a side wall whichever way it turns. Only the map (a wider room: W4) or the hotspots (the nightlights off the side walls) can change it; reported to the lead | `docs/shots/art/a5/exception_hospital_late_quiet.jpg` |

## Shots

`docs/shots/art/a5/before_after_<main|squadron|ember>.jpg`: every changed scene, `tools/art/audit_capture.sh` frames (the scene started on its own, the
perfect bot) at a24, mid, win and end, each before then after. `exception_hospital_late_quiet.jpg`: the quiet room's window turn at its worst
(`RW_STORY_CAM=@14.20:10.31:-279.3:-0.2`, beat 47).

## What still looks weak

- Door walks look sideways: `StoryPlayer` turns the head from the start place's yaw to the arrival place's over the walk, not along the route, so a long
  walk through a corridor shows its side wall for a few beats (judged as passing). A look along the route during door walks would be a `run_journey.gd` change.
- The walk out of a scene is judged as passing and still shows a corridor wall close by for a beat or two (the quiet room's and the dormitories' `end`
  frames).
- Some after frames pass the check but are still mostly wall a few metres off: the Ember inn's fireplace wall (`hollow.inn` mid), the cell
  (`escape.c14` mid), the reactor's tubes in the route window (`mothership.reactor` win), the exam room's tiles (`mothership.exit` mid).
- Several waypoints still face a wall at arm's length and are simply no longer used by the rails (`balcony_far`, `planet_window`, `reactor_core`, `airlock`,
  `day_tv_in`, `quiet_far`, `dorm_bed`, `sofa_front`, `arena_gate`, `arena_tier_l`, the squadron `g2` waypoints of C04, C07, C09, C14): their yaw is map data
  (world packages). The bad rails still use some that face walls (`cubicle`, `bed_corner`, `day_corner`): the check plays the perfect bot only.

## Before

<!-- clearance:before -->
| world | failing poses | scenes with one |
| --- | --- | --- |
| warehouse | 34 | warehouse.balcony, warehouse.chill, warehouse.booth, warehouse.exit |
| mothership | 27 | mothership.gallery, mothership.reactor, mothership.bridge, mothership.exit |
| underworld | 3 | underworld |
| hospital | 19 | hospital, hospital.corridor, hospital.dayroom, hospital.cafeteria, hospital.exit |
| ward | 18 | ward.dorm, ward.corridor |
| hospital_late | 28 | hospital_late.quiet, hospital_late.exit |
| ward_late | 13 | ward_late.treat, ward_late.dorm, ward_late.exit |
| gospel/jordan | 0 | - |
| gospel/galilee | 0 | - |
| gospel/road | 0 | - |
| gospel/jerusalem | 0 | - |
| squadron/base | 10 | base.c03 |
| squadron/air | 44 | air, air.c05 |
| squadron/city | 94 | city, city.c09 |
| squadron/escape | 29 | escape.c13, escape.c14 |
| ember/hollow | 20 | hollow.inn |
| ember/north | 0 | - |
| ember/deeps | 0 | - |
| ember/marsh | 0 | - |
| ember/mountain | 0 | - |
| **all** | **339** | 117 scene entries, 214166 samples |

| scene | entry | phases | beats (from the scene's first downbeat) | pose | centre m | width near | nearest surface at the centre | camera (RW_STORY_CAM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warehouse.balcony | door from warehouse | 2,4 | 32.5 to 37.5 | move to balcony_far | 1.30 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-9.83:3.10:-244.4:-0.1 |
| warehouse.balcony | door from warehouse | all | 38.0 to 45.0 | glance | 0.81 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-10.20:2.99:-270.3:8.3 |
| warehouse.balcony | door from warehouse | 2,3,5,7,8,9,10 | 45.5 to 46.5 | window look | 0.83 | 85% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-10.20:2.99:-282.6:8.7 |
| warehouse.balcony | door from warehouse | 2,3,5,8,10 | 62.5 to 63.5 | window look | 1.28 | 75% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-9.86:1.79:-296.7:-1.6 |
| warehouse.balcony | door from warehouse | 3,6,8,9,10 | 32.0 to 37.5 | move to balcony_far | 1.26 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-9.85:3.10:-245.7:-0.1 |
| warehouse.balcony | door from warehouse | 4,6 | 45.5 to 47.0 | window look | 0.67 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-10.34:3.03:-272.3:8.7 |
| warehouse.balcony | door from warehouse | 4,6 | 62.0 to 63.5 | window look | 0.72 | 75% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-10.36:2.31:-296.8:-1.3 |
| warehouse.balcony | door from warehouse | 5,7 | 31.5 to 37.5 | move to balcony_far | 1.23 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-9.87:3.17:-245.7:-0.1 |
| warehouse.balcony | door from warehouse | 7,9 | 63.0 to 63.5 | window look | 1.44 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-9.56:-0.11:-266.6:-0.1 |
| warehouse.chill | door from warehouse.bar | all | 40.5 to 44.5 | glance | 0.70 | 100% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.03:11.30:179.9:-0.1 |
| warehouse.chill | door from warehouse.bar | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 0.71 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @8.96:11.30:187.0:-0.1 |
| warehouse.chill | door from warehouse.bar | 2,9 | 45.5 to 46.0 | window look | 0.77 | 80% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @8.90:11.29:203.0:-0.1 |
| warehouse.chill | door from warehouse.bar | 2,9 | 48.0 to 61.0 | window look | 0.51 | 80% | sofa_a wall (8.0, 10.8)-(9.0, 10.8) wall_chill | @8.51:11.30:349.1:-0.1 |
| warehouse.chill | door from warehouse.bar | 3,4,6,10 | 33.5 to 34.0 | move to sofa_front | 1.84 | 70% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill | @10.14:9.64:128.9:0.5 |
| warehouse.chill | door from warehouse.bar | 3,4,5,7,10 | 45.5 to 47.0 | window look | 0.72 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.53:11.34:203.7:-0.1 |
| warehouse.chill | door from warehouse.bar | 4,7,10 | 45.0 to 45.0 | place sofa_front | 0.70 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.49:11.30:187.2:-0.1 |
| warehouse.chill | door from warehouse.bar | 6,8 | 45.5 to 47.5 | window look | 0.74 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.52:11.39:214.2:-0.1 |
| warehouse.chill | door from warehouse.balcony | all | -3.0 to 1.0 | door walk to chill_door | 0.80 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-10.20:3.00:89.6:0.1 |
| warehouse.chill | door from warehouse.balcony | all | 40.5 to 44.5 | glance | 0.70 | 100% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.03:11.30:179.9:-0.1 |
| warehouse.chill | door from warehouse.balcony | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 0.71 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @8.96:11.30:187.0:-0.1 |
| warehouse.chill | door from warehouse.balcony | 2,9 | 45.5 to 46.0 | window look | 0.77 | 80% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @8.90:11.29:203.0:-0.1 |
| warehouse.chill | door from warehouse.balcony | 2,9 | 48.0 to 61.0 | window look | 0.51 | 80% | sofa_a wall (8.0, 10.8)-(9.0, 10.8) wall_chill | @8.51:11.30:349.1:-0.1 |
| warehouse.chill | door from warehouse.balcony | 3,4,6,10 | 33.5 to 34.0 | move to sofa_front | 1.84 | 70% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill | @10.14:9.64:128.9:0.5 |
| warehouse.chill | door from warehouse.balcony | 3,4,5,7,10 | 45.5 to 47.0 | window look | 0.72 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.53:11.34:203.7:-0.1 |
| warehouse.chill | door from warehouse.balcony | 4,7,10 | 45.0 to 45.0 | place sofa_front | 0.70 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.49:11.30:187.2:-0.1 |
| warehouse.chill | door from warehouse.balcony | 6,8 | 45.5 to 47.5 | window look | 0.74 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill | @9.52:11.39:214.2:-0.1 |
| warehouse.booth | door from warehouse.balcony | all | -3.0 to 1.0 | door walk to stage_edge | 0.80 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-10.20:3.00:89.6:0.1 |
| warehouse.booth | door from warehouse.balcony | all | 1.5 to 2.0 | herald look | 1.60 | 95% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel | @-9.42:0.26:81.6:0.4 |
| warehouse.exit | door from warehouse.chill | 7 | 40.0 to 45.0 | glance | 1.86 | 65% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick | @-0.00:15.40:-305.1:10.4 |
| warehouse.exit | door from warehouse.chill | 7 | 45.5 to 46.0 | window look | 2.00 | 55% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick | @-0.02:15.42:-311.3:8.7 |
| warehouse.exit | door from warehouse.chill | 7 | 63.0 to 63.5 | window look | 1.66 | 75% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick | @-0.00:15.41:-295.7:-0.1 |
| warehouse.exit | door from warehouse.booth | 7 | 40.0 to 45.0 | glance | 1.86 | 65% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick | @-0.00:15.40:-305.1:10.4 |
| warehouse.exit | door from warehouse.booth | 7 | 45.5 to 46.0 | window look | 2.00 | 55% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick | @-0.02:15.42:-311.3:8.7 |
| warehouse.exit | door from warehouse.booth | 7 | 63.0 to 63.5 | window look | 1.66 | 75% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick | @-0.00:15.41:-295.7:-0.1 |
| mothership.gallery | door from mothership | 2,4,5,6,7,8,9 | 35.5 to 37.0 | move to planet_window | 1.39 | 85% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.41:8.68:-162.2:-0.2 |
| mothership.gallery | door from mothership | all | 37.5 to 44.5 | glance | 0.48 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.00:9.52:-182.0:-0.1 |
| mothership.gallery | door from mothership | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 0.48 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.00:9.53:-186.1:-0.1 |
| mothership.gallery | door from mothership | all | 45.5 to 46.5 | window look | 0.47 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.03:9.53:-176.3:-0.1 |
| mothership.gallery | door from mothership | 2,9 | 62.0 to 63.5 | window look | 0.58 | 75% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.62:9.47:-156.3:-0.2 |
| mothership.gallery | door from mothership | 3,10 | 36.0 to 37.0 | move to planet_window | 1.52 | 85% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.41:8.56:-162.2:-0.2 |
| mothership.gallery | door from mothership | 3,4,5,6,7,8,10 | 62.5 to 63.5 | window look | 0.80 | 75% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @18.34:9.29:-152.9:-0.2 |
| mothership.gallery | door from mothership | 4,7,10 | 45.0 to 45.0 | place planet_window | 0.50 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @15.99:9.50:-175.0:-0.1 |
| mothership.reactor | door from mothership | all | 42.0 to 44.5 | glance | 1.40 | 100% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube | @34.00:-1.60:0.1:-0.1 |
| mothership.reactor | door from mothership | all | 45.0 to 45.0 | place reactor_core | 1.40 | 100% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube | @33.99:-1.60:-4.0:-0.1 |
| mothership.reactor | door from mothership | all | 45.5 to 46.0 | window look | 1.46 | 85% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube | @33.99:-1.60:-17.2:-0.1 |
| mothership.reactor | door from mothership | all | 63.0 to 63.5 | window look | 2.43 | 55% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube | @34.00:-0.93:-31.8:-0.2 |
| mothership.bridge | door from mothership.gallery | all | -3.0 to 3.0 | door walk to bridge_door | 0.50 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet | @16.00:9.50:-180.4:0.1 |
| mothership.bridge | door from mothership.reactor | all | -3.0 to -0.5 | door walk to bridge_door | 1.40 | 100% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube | @34.00:-1.60:-0.4:0.1 |
| mothership.exit | door from mothership.bridge | 2,3,5,7,8,9,10 | 38.0 to 44.5 | glance | 1.49 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @33.98:17.51:182.1:-0.1 |
| mothership.exit | door from mothership.bridge | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 1.42 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @34.00:17.59:186.8:-0.1 |
| mothership.exit | door from mothership.bridge | 2,9 | 45.5 to 47.5 | window look | 1.45 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @34.03:17.66:202.3:-0.1 |
| mothership.exit | door from mothership.bridge | 2,6,8,9 | 63.0 to 63.5 | window look | 0.45 | 95% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @34.01:18.55:170.7:-0.1 |
| mothership.exit | door from mothership.bridge | 3,5 | 45.5 to 47.0 | window look | 1.80 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @34.02:17.53:144.8:-0.1 |
| mothership.exit | door from mothership.bridge | 3,5 | 62.5 to 63.5 | window look | 1.35 | 90% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @34.01:18.11:131.5:-0.1 |
| mothership.exit | door from mothership.bridge | 4,6 | 38.5 to 44.5 | glance | 1.80 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @33.99:17.20:182.1:-0.1 |
| mothership.exit | door from mothership.bridge | 4,7,10 | 45.0 to 45.0 | place airlock | 1.81 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @33.99:17.20:186.8:-0.1 |
| mothership.exit | door from mothership.bridge | 4,7,10 | 45.5 to 45.5 | window look | 1.94 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch | @33.99:17.20:202.2:-0.1 |
| mothership.exit | door from mothership.bridge | 4,7,10 | 46.5 to 48.0 | window look | 1.85 | 55% | airlock_ramp wall (35.0, 15.0)-(35.0, 16.0) wall_airlock | @34.00:17.20:327.4:-0.3 |
| mothership.exit | door from mothership.bridge | 4,7,10 | 61.5 to 63.5 | window look | 1.73 | 65% | airlock wall (35.0, 16.0)-(36.0, 16.0) wall_airlock | @34.01:17.21:314.2:-0.1 |
| mothership.exit | door from mothership.bridge | 6,8 | 45.5 to 46.0 | window look | 1.42 | 100% | airlock wall (36.0, 16.0)-(36.0, 19.0) wall_airlock | @34.94:17.20:227.9:-0.2 |
| mothership.exit | door from mothership.bridge | 6,8 | 48.5 to 60.5 | window look | 1.21 | 70% | airlock wall (35.0, 16.0)-(36.0, 16.0) wall_airlock | @35.31:17.20:6.9:0.6 |
| underworld | arrival | all | 0.0 to 2.0 | passage window | 1.08 | 100% | step up to tier_l: arena wall (-7.0, 9.0)-(-7.0, -3.0) wall_arena | @-5.93:4.19:83.8:0.5 |
| underworld | arrival | all | 21.0 to 21.5 | move to arena_gate | 1.91 | 100% | step up to gate_dais: arena wall (-3.0, -3.0)-(3.0, -3.0) wall_arena | @-0.02:-1.09:-0.5:-0.2 |
| underworld | arrival | all | 22.0 to 28.0 | glance | 0.50 | 100% | step up to gate_dais: arena wall (-3.0, -3.0)-(3.0, -3.0) wall_arena | @0.00:-2.50:-0.8:-1.1 |
| hospital | arrival | 4,6 | 62.5 to 63.0 | window look | 0.83 | 65% | ward wall (5.0, 2.0)-(5.0, 5.0) wall_ward | @4.27:2.09:-118.7:-0.2 |
| hospital.corridor | door from hospital | 7,9 | 46.5 to 47.0 | window look | 0.51 | 95% | corridor wall (29.0, 3.0)-(15.0, 3.0) wall_door | @22.95:2.50:-187.7:-0.2 |
| hospital.corridor | door from hospital | 7,9 | 62.0 to 63.5 | window look | 0.87 | 95% | corridor wall (29.0, 3.0)-(15.0, 3.0) wall_door | @22.81:2.14:-190.8:-0.2 |
| hospital.dayroom | door from hospital.corridor | 2,6,8,9 | 36.0 to 36.0 | move to day_tv_in | 2.13 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.23:-12.87:-0.7:0.0 |
| hospital.dayroom | door from hospital.corridor | all | 36.5 to 37.0 | place day_tv_in | 2.05 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.26:-12.95:-0.7:-0.1 |
| hospital.dayroom | door from hospital.corridor | all | 37.5 to 44.5 | glance | 1.39 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.26:-13.76:-27.1:-0.1 |
| hospital.dayroom | door from hospital.corridor | 2,4,5,7,8,10 | 45.0 to 45.0 | stroll | 1.42 | 90% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.25:-13.81:-32.9:-0.1 |
| hospital.dayroom | door from hospital.corridor | 2,3,4,5,6,7,9 | 45.5 to 45.5 | window look | 1.71 | 90% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.25:-13.84:-47.5:-0.1 |
| hospital.dayroom | door from hospital.corridor | 3,6,9 | 45.0 to 45.0 | place day_tv_in | 2.06 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.26:-12.95:-5.1:-0.1 |
| hospital.dayroom | door from hospital.corridor | 8,10 | 45.5 to 46.0 | window look | 0.71 | 75% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv | @20.24:-14.34:-21.6:-0.1 |
| hospital.cafeteria | door from hospital.corridor | 2,9 | 43.5 to 44.0 | glance | 2.25 | 55% | cafeteria wall (47.0, -6.0)-(47.0, -3.0) wall_cafe | @44.75:-3.00:-87.8:-1.0 |
| hospital.cafeteria | door from hospital.corridor | 2,9 | 44.5 to 44.5 | stroll | 2.18 | 55% | cafeteria wall (47.0, -6.0)-(47.0, -3.0) wall_cafe | @44.83:-2.98:-88.7:-0.4 |
| hospital.exit | door from hospital.garden | 3,5 | 36.0 to 36.5 | stroll | 2.35 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:59.4:-0.1 |
| hospital.exit | door from hospital.garden | 3,5 | 37.0 to 37.0 | place stroll end | 2.36 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:59.3:-0.2 |
| hospital.exit | door from hospital.garden | 3 | 37.5 to 44.0 | glance | 1.56 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:39.8:-0.4 |
| hospital.exit | door from hospital.garden | 5 | 37.5 to 44.5 | glance | 0.93 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.81:-2.22:32.9:-0.1 |
| hospital.exit | door from hospital.garden | 5 | 45.0 to 45.0 | stroll | 0.97 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.75:-2.23:37.7:-0.1 |
| hospital.exit | door from hospital.garden | 5 | 45.5 to 45.5 | window look | 1.21 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.73:-2.24:51.3:-0.1 |
| hospital.exit | door from hospital.garden | 7 | 41.5 to 43.0 | glance | 2.26 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.88:-1.83:58.7:-0.3 |
| ward.dorm | door from ward | 2,4,7,9,10 | 38.0 to 45.0 | glance | 0.99 | 100% | ceiling of dorm_alcove | @26.41:15.40:-179.4:11.6 |
| ward.dorm | door from ward | 2,9 | 45.5 to 46.0 | window look | 1.16 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.92:15.41:-198.8:7.4 |
| ward.dorm | door from ward | 3,4,6,10 | 37.5 to 37.5 | move to dorm_bed | 1.58 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.02:14.92:-180.7:-0.1 |
| ward.dorm | door from ward | 3,5,6,8 | 38.0 to 45.0 | glance | 0.94 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.00:15.57:-184.6:8.9 |
| ward.dorm | door from ward | 3,5 | 45.5 to 47.0 | window look | 0.94 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.03:15.62:-199.6:7.4 |
| ward.dorm | door from ward | 3,5 | 62.0 to 62.5 | window look | 2.03 | 65% | dorm_alcove wall (24.0, 16.5)-(24.0, 14.0) wall_dwindow | @26.00:15.70:-279.3:-0.2 |
| ward.dorm | door from ward | 4,7,10 | 45.5 to 47.5 | window look | 1.18 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @25.99:15.40:-199.5:7.4 |
| ward.dorm | door from ward | 6,8 | 45.5 to 46.5 | window look | 0.87 | 95% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.03:15.65:-189.9:7.4 |
| ward.dorm | door from ward | 6,8 | 62.5 to 63.0 | window look | 2.02 | 75% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow | @26.00:15.45:-82.6:-0.2 |
| ward.corridor | door from ward.art | 2,4 | 61.0 to 63.0 | window look | 1.71 | 55% | corridor wall (33.0, 4.0)-(33.0, 5.0) wall_cdoor | @31.89:6.00:-40.2:-0.2 |
| ward.corridor | door from ward.art | 8,10 | 47.0 to 48.5 | window look | 2.00 | 65% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor | @31.11:6.00:2.5:-0.3 |
| ward.corridor | door from ward.art | 8,10 | 61.0 to 62.0 | window look | 2.04 | 75% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor | @31.91:6.00:-11.9:-0.2 |
| ward.corridor | door from ward.dorm | all | -3.0 to -2.0 | door walk to corr_west | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.00:15.40:-180.4:0.1 |
| ward.corridor | door from ward.dorm | all | 5.0 to 5.0 | door walk to corr_west | 0.86 | 55% | corridor wall (22.0, 8.0)-(17.0, 8.0) wall_cdoor2 | @20.45:7.40:-134.5:0.1 |
| ward.corridor | door from ward.dorm | all | 5.5 to 6.0 | glance | 1.19 | 55% | corridor wall (22.0, 8.0)-(17.0, 8.0) wall_cdoor2 | @19.26:7.24:-129.4:0.1 |
| ward.corridor | door from ward.dorm | 2,4 | 61.0 to 63.0 | window look | 1.71 | 55% | corridor wall (33.0, 4.0)-(33.0, 5.0) wall_cdoor | @31.89:6.00:-40.2:-0.2 |
| ward.corridor | door from ward.dorm | 8,10 | 47.0 to 48.5 | window look | 2.00 | 65% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor | @31.11:6.00:2.5:-0.3 |
| ward.corridor | door from ward.dorm | 8,10 | 61.0 to 62.0 | window look | 2.04 | 75% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor | @31.91:6.00:-11.9:-0.2 |
| hospital_late.quiet | door from hospital_late | all | 16.0 to 16.0 | glance | 2.03 | 60% | quiet wall (15.4, 3.0)-(15.4, 16.0) wall_quiet | @14.20:5.92:-36.2:-0.0 |
| hospital_late.quiet | door from hospital_late | all | 16.5 to 21.0 | move to quiet_far | 1.20 | 100% | quiet wall (15.4, 3.0)-(15.4, 16.0) wall_quiet | @14.20:9.13:-89.7:-0.4 |
| hospital_late.quiet | door from hospital_late | all | 22.5 to 28.5 | glance | 1.50 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @13.84:14.50:-179.6:0.2 |
| hospital_late.quiet | door from hospital_late | 2,9 | 29.0 to 32.5 | stroll | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @13.77:14.50:-180.6:0.3 |
| hospital_late.quiet | door from hospital_late | 2,9 | 33.0 to 37.5 | place stroll end | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @13.49:14.50:-180.6:0.3 |
| hospital_late.quiet | door from hospital_late | all | 38.0 to 44.0 | glance | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @13.48:14.50:-179.2:-1.3 |
| hospital_late.quiet | door from hospital_late | 2,4,5,7,10 | 44.5 to 45.0 | stroll | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @13.46:14.50:-178.7:-0.4 |
| hospital_late.quiet | door from hospital_late | 2,4,9 | 46.0 to 47.5 | window look | 0.49 | 95% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet | @13.48:14.51:-282.0:-5.6 |
| hospital_late.quiet | door from hospital_late | all | 61.5 to 63.0 | window look | 0.84 | 55% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet | @13.51:13.88:-321.3:-12.9 |
| hospital_late.quiet | door from hospital_late | 3,5,6,8 | 29.0 to 36.5 | stroll | 0.52 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.20:15.48:-180.7:-0.1 |
| hospital_late.quiet | door from hospital_late | 3,5,6,8 | 37.0 to 37.5 | place stroll end | 0.52 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.19:15.48:-180.3:-0.5 |
| hospital_late.quiet | door from hospital_late | 3,6,9 | 44.5 to 45.0 | place stroll end | 0.52 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.19:15.48:-178.7:-0.4 |
| hospital_late.quiet | door from hospital_late | 3,5,7 | 45.5 to 48.0 | window look | 0.56 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.19:15.48:-200.4:-0.3 |
| hospital_late.quiet | door from hospital_late | 4,7,10 | 29.0 to 37.5 | place quiet_far | 1.50 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.21:14.50:-180.6:0.3 |
| hospital_late.quiet | door from hospital_late | 6,10 | 45.5 to 47.5 | window look | 0.88 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.19:15.39:-226.6:-0.4 |
| hospital_late.quiet | door from hospital_late | 8 | 44.5 to 44.5 | stroll | 0.84 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.11:15.53:-235.9:-0.4 |
| hospital_late.quiet | door from hospital_late | 8 | 45.5 to 47.5 | window look | 1.11 | 100% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet | @14.11:15.56:-267.8:-0.5 |
| hospital_late.exit | door from hospital_late.cafe | 3,10 | 36.0 to 36.5 | stroll | 2.35 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:-300.6:-0.1 |
| hospital_late.exit | door from hospital_late.cafe | 3,10 | 37.0 to 37.5 | place stroll end | 2.36 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:-300.7:-0.2 |
| hospital_late.exit | door from hospital_late.cafe | 3 | 41.5 to 44.0 | glance | 1.03 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.84:-2.18:-323.1:-1.0 |
| hospital_late.exit | door from hospital_late.cafe | 3 | 44.5 to 45.0 | stroll | 0.94 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.81:-2.22:-325.9:-0.4 |
| hospital_late.exit | door from hospital_late.cafe | 3 | 45.5 to 45.5 | window look | 1.21 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.73:-2.24:-308.7:-0.1 |
| hospital_late.exit | door from hospital_late.quiet | all | -3.0 to -2.0 | door walk to garden_door_e | 1.50 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet | @14.20:14.50:-180.4:0.1 |
| hospital_late.exit | door from hospital_late.quiet | 3,10 | 36.0 to 36.5 | stroll | 2.35 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:-300.6:-0.1 |
| hospital_late.exit | door from hospital_late.quiet | 3,10 | 37.0 to 37.5 | place stroll end | 2.36 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @61.50:-1.80:-300.7:-0.2 |
| hospital_late.exit | door from hospital_late.quiet | 3 | 41.5 to 44.0 | glance | 1.03 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.84:-2.18:-323.1:-1.0 |
| hospital_late.exit | door from hospital_late.quiet | 3 | 44.5 to 45.0 | stroll | 0.94 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.81:-2.22:-325.9:-0.4 |
| hospital_late.exit | door from hospital_late.quiet | 3 | 45.5 to 45.5 | window look | 1.21 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge | @60.73:-2.24:-308.7:-0.1 |
| ward_late.treat | door from ward_late | all | 25.5 to 28.5 | glance | 1.92 | 100% | ceiling of quiet_bed | @16.01:15.60:-180.9:12.0 |
| ward_late.dorm | door from ward_late | 2,4 | 25.5 to 28.5 | glance | 1.95 | 100% | ceiling of dorm_alcove | @26.02:12.20:-180.9:11.9 |
| ward_late.dorm | door from ward_late | 2,4,5,7 | 37.5 to 44.5 | glance | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @25.99:15.40:-180.1:-0.1 |
| ward_late.dorm | door from ward_late | 2,5,8 | 45.0 to 45.0 | place dorm_bed | 1.11 | 95% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @25.99:15.40:-173.3:-0.1 |
| ward_late.dorm | door from ward_late | 2,4,5,6,8 | 45.5 to 47.5 | window look | 1.18 | 90% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @25.99:15.40:-158.2:-0.1 |
| ward_late.dorm | door from ward_late | 3,5,6,7,8,9,10 | 25.5 to 28.5 | glance | 2.04 | 100% | lintel over dorm_alcove: dorm wall (28.0, 14.0)-(24.0, 14.0) wall_dado | @26.00:12.00:-181.0:11.2 |
| ward_late.dorm | door from ward_late | 3,6,8,9,10 | 38.0 to 44.5 | glance | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.60:15.40:-180.1:-0.1 |
| ward_late.dorm | door from ward_late | 3,4,6,7,9,10 | 45.0 to 45.0 | stroll | 1.11 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.77:15.40:-173.2:-0.1 |
| ward_late.dorm | door from ward_late | 3,10 | 45.5 to 47.5 | window look | 0.79 | 95% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow | @27.23:15.40:-78.5:-0.2 |
| ward_late.dorm | door from ward_late | 3,10 | 61.5 to 62.5 | window look | 0.86 | 85% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow | @27.18:15.18:-74.4:-0.2 |
| ward_late.dorm | door from ward_late | 4,6,7,9 | 62.0 to 62.5 | window look | 2.03 | 65% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow | @26.00:15.68:-79.7:-0.2 |
| ward_late.dorm | door from ward_late | 7,9 | 45.5 to 47.0 | window look | 1.02 | 90% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.02:15.63:-148.5:-0.1 |
| ward_late.exit | door from ward_late.dorm | all | -3.0 to -2.0 | door walk to day_door_a | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow | @26.00:15.40:-180.4:0.1 |
| squadron: base.c03 | door from base | 4 | 95.0 to 97.5 | stroll | 2.31 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.48:-7.75:12.5:-0.3 |
| squadron: base.c03 | door from base | 4 | 98.0 to 101.5 | place stroll end | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.48:-7.76:12.7:-0.2 |
| squadron: base.c03 | door from base | 4 | 102.0 to 109.0 | glance | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.48:-7.76:13.0:0.6 |
| squadron: base.c03 | door from base | 4 | 109.5 to 110.0 | window look | 2.28 | 100% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.49:-7.76:-3.1:9.4 |
| squadron: base.c03 | door from base | 4,6 | 127.0 to 127.5 | window look | 2.25 | 95% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.47:-7.75:5.0:0.5 |
| squadron: base.c03 | arrival | 4 | 95.0 to 97.5 | stroll | 2.31 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.48:-7.75:12.5:-0.3 |
| squadron: base.c03 | arrival | 4 | 98.0 to 101.5 | place stroll end | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.48:-7.76:12.7:-0.2 |
| squadron: base.c03 | arrival | 4 | 102.0 to 109.0 | glance | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.48:-7.76:13.0:0.6 |
| squadron: base.c03 | arrival | 4 | 109.5 to 110.0 | window look | 2.28 | 100% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.49:-7.76:-3.1:9.4 |
| squadron: base.c03 | arrival | 4,6 | 127.0 to 127.5 | window look | 2.25 | 95% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent | @6.47:-7.75:5.0:0.5 |
| squadron: air | arrival | 2 | 103.0 to 108.0 | glance | 2.07 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.61:20.10:203.5:0.2 |
| squadron: air | arrival | 3 | 86.5 to 92.0 | glance | 1.67 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.79:20.35:189.2:1.4 |
| squadron: air | arrival | 3,8 | 92.5 to 97.5 | stroll | 1.10 | 95% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.92:20.93:192.5:-0.3 |
| squadron: air | arrival | 3,5,8 | 98.0 to 101.0 | place stroll end | 1.09 | 85% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.91:20.94:193.1:-0.2 |
| squadron: air | arrival | 3,8,10 | 101.5 to 108.5 | glance | 1.07 | 100% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.93:20.93:178.8:-0.3 |
| squadron: air | arrival | 3 | 109.0 to 109.0 | place stroll end | 1.12 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.91:20.94:197.9:0.5 |
| squadron: air | arrival | 3 | 109.5 to 110.0 | window look | 1.25 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.91:20.94:212.3:-0.1 |
| squadron: air | arrival | 3,5 | 127.0 to 127.5 | window look | 1.14 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.93:20.93:200.5:0.2 |
| squadron: air | arrival | 4,7,10 | 46.5 to 62.5 | window look | 1.31 | 95% | bomber wall (10.0, 22.0)-(10.0, 14.0) wall_bomber | @11.30:18.40:98.1:0.3 |
| squadron: air | arrival | 5 | 97.0 to 97.5 | stroll | 2.30 | 60% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.67:19.75:192.5:-0.3 |
| squadron: air | arrival | 5,9 | 102.0 to 108.5 | glance | 1.61 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.78:20.43:191.4:0.7 |
| squadron: air | arrival | 5 | 109.0 to 109.0 | stroll | 1.59 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.82:20.49:198.6:0.7 |
| squadron: air | arrival | 5 | 109.5 to 109.5 | window look | 1.77 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.86:20.55:215.0:0.6 |
| squadron: air | arrival | 6,8 | 46.5 to 48.0 | window look | 1.52 | 100% | bomber wall (10.0, 22.0)-(10.0, 14.0) wall_bomber | @11.51:19.39:96.7:0.4 |
| squadron: air | arrival | 6,8 | 61.5 to 62.5 | window look | 1.55 | 100% | bomber wall (10.0, 22.0)-(10.0, 14.0) wall_bomber | @11.55:19.57:92.0:0.3 |
| squadron: air | arrival | 6,8 | 63.5 to 63.5 | window look | 2.43 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.56:19.57:183.2:0.5 |
| squadron: air | arrival | 6,8 | 64.0 to 69.0 | place stroll end | 2.48 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.54:19.58:192.3:0.2 |
| squadron: air | arrival | 6,8 | 69.5 to 69.5 | glance | 2.49 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.54:19.58:193.3:0.2 |
| squadron: air | arrival | 6 | 76.0 to 76.5 | glance | 2.36 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.62:20.03:213.5:-0.7 |
| squadron: air | arrival | 6 | 77.0 to 81.5 | stroll | 2.33 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.66:20.21:219.9:-0.5 |
| squadron: air | arrival | 6,10 | 82.0 to 85.5 | place stroll end | 2.36 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.71:20.36:226.1:0.3 |
| squadron: air | arrival | 6,8,10 | 86.0 to 92.0 | glance | 2.04 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.77:20.43:218.8:8.2 |
| squadron: air | arrival | 6 | 92.5 to 97.5 | stroll | 1.72 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.30:20.90:262.4:-0.3 |
| squadron: air | arrival | 6 | 98.0 to 101.0 | place stroll end | 1.71 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.30:20.89:263.0:-0.1 |
| squadron: air | arrival | 6 | 101.5 to 108.5 | glance | 1.72 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.30:20.91:262.0:-0.2 |
| squadron: air | arrival | 6 | 109.0 to 109.0 | place stroll end | 1.70 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.30:20.91:266.9:0.7 |
| squadron: air | arrival | 6,8 | 109.5 to 110.5 | window look | 1.72 | 95% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.30:20.91:278.5:0.6 |
| squadron: air | arrival | 6,8 | 126.5 to 127.5 | window look | 1.70 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.30:20.89:268.8:0.5 |
| squadron: air | arrival | 8 | 76.5 to 76.5 | glance | 2.50 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.54:19.58:193.8:-0.7 |
| squadron: air | arrival | 8 | 77.0 to 85.5 | place stroll end | 2.47 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.54:19.58:191.1:0.3 |
| squadron: air | arrival | 8 | 109.0 to 109.0 | stroll | 2.00 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @12.08:20.70:254.1:0.7 |
| squadron: air | arrival | 9 | 88.5 to 92.0 | glance | 2.36 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.56:20.15:217.8:6.1 |
| squadron: air | arrival | 9 | 92.5 to 92.5 | stroll | 2.49 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.46:20.26:225.5:0.4 |
| squadron: air | arrival | 9 | 93.5 to 93.5 | stroll | 2.49 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.45:20.27:226.1:-0.2 |
| squadron: air | arrival | 9 | 94.0 to 94.0 | place stroll end | 2.49 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @10.44:20.28:226.2:-0.3 |
| squadron: air | arrival | 10 | 81.0 to 81.5 | stroll | 2.48 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.55:19.57:191.3:0.1 |
| squadron: air | arrival | 10 | 92.5 to 101.0 | place stroll end | 2.47 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber | @11.54:19.58:190.5:0.4 |
| squadron: air | arrival | 10 | 110.0 to 110.5 | window look | 2.35 | 90% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @11.67:20.15:261.7:0.5 |
| squadron: air | arrival | 10 | 126.5 to 127.0 | window look | 2.33 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber | @11.72:20.34:258.0:0.5 |
| squadron: air.c05 | arrival | 2 | 101.5 to 104.0 | glance | 2.44 | 85% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar | @35.56:7.67:-91.2:-0.3 |
| squadron: air.c05 | arrival | 2 | 106.0 to 108.5 | glance | 2.45 | 75% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar | @35.56:7.67:-91.6:0.5 |
| squadron: air.c05 | arrival | 2 | 109.0 to 109.0 | place stroll end | 2.48 | 55% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar | @35.56:7.69:-80.5:0.7 |
| squadron: air.c05 | arrival | 2 | 109.5 to 110.0 | window look | 2.45 | 85% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar | @35.56:7.69:-88.8:0.6 |
| squadron: air.c05 | arrival | 2,4 | 127.0 to 127.5 | window look | 2.46 | 55% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar | @35.56:7.67:-96.0:0.5 |
| squadron: city | arrival | 2 | 87.0 to 92.5 | glance | 2.06 | 70% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.39:-6.10:22.3:0.6 |
| squadron: city | arrival | 2 | 93.5 to 93.5 | stroll | 2.49 | 70% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.55:-6.27:46.1:-0.2 |
| squadron: city | arrival | 2 | 94.0 to 94.0 | place stroll end | 2.49 | 70% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.56:-6.28:46.2:-0.3 |
| squadron: city | arrival | 3,6,9 | 46.5 to 48.5 | window look | 1.32 | 95% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber | @12.70:-4.41:-82.4:-7.7 |
| squadron: city | arrival | 3,6,9 | 61.0 to 62.5 | window look | 1.33 | 100% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber | @12.70:-4.40:-86.2:-11.7 |
| squadron: city | arrival | 3 | 81.0 to 81.5 | stroll | 2.48 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.45:-5.57:11.3:0.1 |
| squadron: city | arrival | 3,8 | 82.0 to 85.0 | place stroll end | 2.47 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.46:-5.58:11.5:0.0 |
| squadron: city | arrival | 3 | 85.5 to 88.0 | glance | 2.43 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.44:-5.57:-2.4:0.2 |
| squadron: city | arrival | 3 | 90.0 to 92.5 | glance | 2.43 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.44:-5.57:2.4:0.4 |
| squadron: city | arrival | 3 | 93.0 to 101.5 | place stroll end | 2.47 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.46:-5.58:11.0:-0.1 |
| squadron: city | arrival | 3 | 102.0 to 108.5 | glance | 2.39 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.38:-6.03:32.2:12.6 |
| squadron: city | arrival | 3 | 110.0 to 110.5 | window look | 2.38 | 90% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @12.33:-6.15:80.7:6.9 |
| squadron: city | arrival | 3 | 126.5 to 127.0 | window look | 2.34 | 80% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @12.25:-5.49:73.3:-0.7 |
| squadron: city | arrival | 5 | 86.0 to 92.5 | glance | 1.60 | 85% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.22:-6.43:9.9:0.1 |
| squadron: city | arrival | 5,10 | 93.0 to 97.5 | stroll | 1.10 | 95% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.08:-6.93:12.5:-0.3 |
| squadron: city | arrival | 5,7,10 | 98.0 to 101.5 | place stroll end | 1.09 | 85% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.09:-6.94:13.1:-0.2 |
| squadron: city | arrival | 5,7 | 102.0 to 109.0 | glance | 1.09 | 85% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.08:-6.93:13.0:0.6 |
| squadron: city | arrival | 5 | 109.5 to 110.0 | window look | 1.30 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.09:-6.94:34.5:8.2 |
| squadron: city | arrival | 5,7 | 127.0 to 127.5 | window look | 2.21 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.94:-6.05:-28.0:-0.3 |
| squadron: city | arrival | 7 | 97.0 to 97.5 | stroll | 2.30 | 60% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.33:-5.75:12.5:-0.3 |
| squadron: city | arrival | 7 | 109.5 to 109.5 | window look | 1.79 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @13.14:-6.55:34.5:9.3 |
| squadron: city | arrival | 8,10 | 46.5 to 48.0 | window look | 1.44 | 100% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber | @12.57:-5.02:-85.1:-2.7 |
| squadron: city | arrival | 8,10 | 61.5 to 62.5 | window look | 1.55 | 100% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber | @12.45:-5.57:-90.8:-3.5 |
| squadron: city | arrival | 8,10 | 63.5 to 63.5 | window look | 2.43 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.44:-5.57:2.9:0.2 |
| squadron: city | arrival | 8,10 | 64.0 to 69.5 | place stroll end | 2.48 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.46:-5.58:11.9:0.5 |
| squadron: city | arrival | 8,10 | 70.0 to 76.0 | glance | 2.27 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.42:-5.83:16.1:5.2 |
| squadron: city | arrival | 8 | 76.5 to 81.5 | stroll | 2.33 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.38:-6.03:32.1:-0.4 |
| squadron: city | arrival | 8,10 | 85.5 to 92.5 | glance | 1.70 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.19:-6.44:23.9:0.6 |
| squadron: city | arrival | 8 | 93.0 to 97.5 | stroll | 1.72 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.70:-6.90:82.4:-0.3 |
| squadron: city | arrival | 8 | 98.0 to 101.5 | place stroll end | 1.71 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.70:-6.89:83.0:-0.1 |
| squadron: city | arrival | 8 | 102.0 to 109.0 | glance | 1.71 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.70:-6.89:82.9:1.7 |
| squadron: city | arrival | 8 | 109.5 to 110.0 | window look | 1.74 | 95% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.70:-6.91:99.4:9.1 |
| squadron: city | arrival | 8,10 | 126.5 to 127.5 | window look | 1.79 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.76:-5.53:79.1:0.3 |
| squadron: city | arrival | 10 | 76.5 to 85.0 | place stroll end | 2.47 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.46:-5.58:11.3:0.1 |
| squadron: city | arrival | 10 | 102.0 to 103.0 | glance | 2.45 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber | @12.28:-6.36:48.1:1.7 |
| squadron: city | arrival | 10 | 106.5 to 109.0 | glance | 2.03 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.92:-6.70:74.4:11.0 |
| squadron: city | arrival | 10 | 109.5 to 110.5 | window look | 1.91 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber | @11.88:-6.70:89.6:8.8 |
| squadron: city.c09 | door from city.c08 | 2,8 | 109.5 to 112.0 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.23:14.16:-188.7:3.8 |
| squadron: city.c09 | door from city.c08 | 2,8 | 125.5 to 127.5 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.22:14.15:-171.1:0.5 |
| squadron: city.c09 | door from city.c08 | 4 | 77.5 to 77.5 | stroll | 2.49 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.07:13.57:-167.5:-0.6 |
| squadron: city.c09 | door from city.c08 | 4 | 78.0 to 85.0 | place stroll end | 2.46 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.06:13.58:-168.7:0.1 |
| squadron: city.c09 | door from city.c08 | 4 | 85.5 to 92.5 | glance | 1.37 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.28:14.65:-170.1:0.1 |
| squadron: city.c09 | door from city.c08 | 4,10 | 93.0 to 93.5 | stroll | 1.28 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.74:-168.9:-0.2 |
| squadron: city.c09 | door from city.c08 | 4,6,10 | 94.0 to 101.5 | place stroll end | 1.27 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.76:-168.8:-0.3 |
| squadron: city.c09 | door from city.c08 | 4,6,10 | 102.0 to 109.0 | glance | 1.28 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.76:-167.0:0.6 |
| squadron: city.c09 | door from city.c08 | 4,6 | 109.5 to 110.5 | window look | 1.41 | 75% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.31:14.76:-153.1:9.4 |
| squadron: city.c09 | door from city.c08 | 4,6 | 126.5 to 127.5 | window look | 1.31 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.33:14.75:-161.9:0.5 |
| squadron: city.c09 | door from city.c08 | 5 | 110.5 to 112.5 | window look | 2.30 | 90% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.29:13.71:-185.0:2.2 |
| squadron: city.c09 | door from city.c08 | 5 | 125.0 to 126.5 | window look | 2.29 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.28:13.71:-176.1:0.4 |
| squadron: city.c09 | door from city.c08 | 6 | 93.5 to 93.5 | stroll | 2.48 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.07:13.57:-168.9:-0.2 |
| squadron: city.c09 | door from city.c08 | 7 | 72.5 to 75.0 | glance | 2.40 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.12:13.85:-154.2:5.2 |
| squadron: city.c09 | door from city.c08 | 7 | 86.0 to 90.5 | glance | 1.92 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.40:14.33:-150.5:0.6 |
| squadron: city.c09 | door from city.c08 | 7,9 | 110.0 to 112.0 | window look | 1.30 | 100% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.81:14.70:-184.5:3.8 |
| squadron: city.c09 | door from city.c08 | 7,9 | 125.5 to 127.0 | window look | 1.31 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.80:14.70:-188.6:0.4 |
| squadron: city.c09 | door from city.c08 | 9 | 88.5 to 92.0 | glance | 2.21 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.12:13.84:-167.5:0.6 |
| squadron: city.c09 | door from city.c08 | 10 | 88.0 to 92.5 | glance | 2.06 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @4.85:14.16:-153.2:0.6 |
| squadron: city.c09 | door from city.c10 | 2,8 | 109.5 to 112.0 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.23:14.16:-188.7:3.8 |
| squadron: city.c09 | door from city.c10 | 2,8 | 125.5 to 127.5 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.22:14.15:-171.1:0.5 |
| squadron: city.c09 | door from city.c10 | 4 | 77.5 to 77.5 | stroll | 2.49 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.07:13.57:-167.5:-0.6 |
| squadron: city.c09 | door from city.c10 | 4 | 78.0 to 85.0 | place stroll end | 2.46 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.06:13.58:-168.7:0.1 |
| squadron: city.c09 | door from city.c10 | 4 | 85.5 to 92.5 | glance | 1.37 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.28:14.65:-170.1:0.1 |
| squadron: city.c09 | door from city.c10 | 4,10 | 93.0 to 93.5 | stroll | 1.28 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.74:-168.9:-0.2 |
| squadron: city.c09 | door from city.c10 | 4,6,10 | 94.0 to 101.5 | place stroll end | 1.27 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.76:-168.8:-0.3 |
| squadron: city.c09 | door from city.c10 | 4,6,10 | 102.0 to 109.0 | glance | 1.28 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.76:-167.0:0.6 |
| squadron: city.c09 | door from city.c10 | 4,6 | 109.5 to 110.5 | window look | 1.41 | 75% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.31:14.76:-153.1:9.4 |
| squadron: city.c09 | door from city.c10 | 4,6 | 126.5 to 127.5 | window look | 1.31 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.33:14.75:-161.9:0.5 |
| squadron: city.c09 | door from city.c10 | 5 | 110.5 to 112.5 | window look | 2.30 | 90% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.29:13.71:-185.0:2.2 |
| squadron: city.c09 | door from city.c10 | 5 | 125.0 to 126.5 | window look | 2.29 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.28:13.71:-176.1:0.4 |
| squadron: city.c09 | door from city.c10 | 6 | 93.5 to 93.5 | stroll | 2.48 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.07:13.57:-168.9:-0.2 |
| squadron: city.c09 | door from city.c10 | 7 | 72.5 to 75.0 | glance | 2.40 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.12:13.85:-154.2:5.2 |
| squadron: city.c09 | door from city.c10 | 7 | 86.0 to 90.5 | glance | 1.92 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.40:14.33:-150.5:0.6 |
| squadron: city.c09 | door from city.c10 | 7,9 | 110.0 to 112.0 | window look | 1.30 | 100% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.81:14.70:-184.5:3.8 |
| squadron: city.c09 | door from city.c10 | 7,9 | 125.5 to 127.0 | window look | 1.31 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.80:14.70:-188.6:0.4 |
| squadron: city.c09 | door from city.c10 | 9 | 88.5 to 92.0 | glance | 2.21 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.12:13.84:-167.5:0.6 |
| squadron: city.c09 | door from city.c10 | 10 | 88.0 to 92.5 | glance | 2.06 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @4.85:14.16:-153.2:0.6 |
| squadron: city.c09 | arrival | 2,8 | 109.5 to 112.0 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.23:14.16:-188.7:3.8 |
| squadron: city.c09 | arrival | 2,8 | 125.5 to 127.5 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.22:14.15:-171.1:0.5 |
| squadron: city.c09 | arrival | 4 | 77.5 to 77.5 | stroll | 2.49 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.07:13.57:-167.5:-0.6 |
| squadron: city.c09 | arrival | 4 | 78.0 to 85.0 | place stroll end | 2.46 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.06:13.58:-168.7:0.1 |
| squadron: city.c09 | arrival | 4 | 85.5 to 92.5 | glance | 1.37 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.28:14.65:-170.1:0.1 |
| squadron: city.c09 | arrival | 4,10 | 93.0 to 93.5 | stroll | 1.28 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.74:-168.9:-0.2 |
| squadron: city.c09 | arrival | 4,6,10 | 94.0 to 101.5 | place stroll end | 1.27 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.76:-168.8:-0.3 |
| squadron: city.c09 | arrival | 4,6,10 | 102.0 to 109.0 | glance | 1.28 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.32:14.76:-167.0:0.6 |
| squadron: city.c09 | arrival | 4,6 | 109.5 to 110.5 | window look | 1.41 | 75% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.31:14.76:-153.1:9.4 |
| squadron: city.c09 | arrival | 4,6 | 126.5 to 127.5 | window look | 1.31 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.33:14.75:-161.9:0.5 |
| squadron: city.c09 | arrival | 5 | 110.5 to 112.5 | window look | 2.30 | 90% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.29:13.71:-185.0:2.2 |
| squadron: city.c09 | arrival | 5 | 125.0 to 126.5 | window look | 2.29 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.28:13.71:-176.1:0.4 |
| squadron: city.c09 | arrival | 6 | 93.5 to 93.5 | stroll | 2.48 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @5.07:13.57:-168.9:-0.2 |
| squadron: city.c09 | arrival | 7 | 72.5 to 75.0 | glance | 2.40 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.12:13.85:-154.2:5.2 |
| squadron: city.c09 | arrival | 7 | 86.0 to 90.5 | glance | 1.92 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.40:14.33:-150.5:0.6 |
| squadron: city.c09 | arrival | 7,9 | 110.0 to 112.0 | window look | 1.30 | 100% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.81:14.70:-184.5:3.8 |
| squadron: city.c09 | arrival | 7,9 | 125.5 to 127.0 | window look | 1.31 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.80:14.70:-188.6:0.4 |
| squadron: city.c09 | arrival | 9 | 88.5 to 92.0 | glance | 2.21 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @6.12:13.84:-167.5:0.6 |
| squadron: city.c09 | arrival | 10 | 88.0 to 92.5 | glance | 2.06 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel | @4.85:14.16:-153.2:0.6 |
| squadron: escape.c13 | door from escape.c12 | all | 6.5 to 7.0 | glance | 1.32 | 80% | quay wall (22.0, 0.0)-(22.0, 10.8) wall_quay | @20.69:10.82:-85.8:3.8 |
| squadron: escape.c14 | door from escape.c12 | 2,4 | 63.0 to 63.5 | window look | 2.30 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.74:-5.77:14.6:0.5 |
| squadron: escape.c14 | door from escape.c12 | 2,4 | 64.0 to 69.5 | place stroll end | 2.28 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.76:-5.78:12.3:0.2 |
| squadron: escape.c14 | door from escape.c12 | 2,4 | 70.0 to 80.0 | glance | 2.08 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.64:-6.41:39.9:4.7 |
| squadron: escape.c14 | door from escape.c12 | 2,6,8 | 80.5 to 81.5 | stroll | 2.07 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.60:-6.53:44.9:0.3 |
| squadron: escape.c14 | door from escape.c12 | 2,6,8 | 82.0 to 85.0 | place stroll end | 2.08 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.59:-6.56:46.5:0.0 |
| squadron: escape.c14 | door from escape.c12 | 2 | 85.5 to 86.5 | glance | 2.13 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.59:-6.56:47.4:0.0 |
| squadron: escape.c14 | door from escape.c12 | 4 | 80.5 to 85.0 | place stroll end | 2.27 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.76:-5.78:11.3:0.1 |
| squadron: escape.c14 | door from escape.c12 | 4,6 | 85.5 to 87.0 | glance | 2.28 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.76:-5.78:12.4:0.0 |
| squadron: escape.c14 | door from escape.c12 | 4,6 | 91.0 to 92.5 | glance | 2.08 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.68:-6.23:31.6:0.1 |
| squadron: escape.c14 | door from escape.c12 | 4,8 | 93.0 to 97.5 | stroll | 2.05 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.64:-6.41:39.2:-0.4 |
| squadron: escape.c14 | door from escape.c12 | 4,8,10 | 98.0 to 101.5 | place stroll end | 2.13 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.59:-6.56:47.6:0.1 |
| squadron: escape.c14 | door from escape.c12 | 4 | 102.0 to 107.5 | glance | 1.80 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.53:-6.63:39.9:7.5 |
| squadron: escape.c14 | door from escape.c12 | 5 | 91.5 to 92.5 | glance | 1.77 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.15:-6.79:46.9:0.1 |
| squadron: escape.c14 | door from escape.c12 | 5 | 93.0 to 93.5 | stroll | 1.68 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.19:-6.83:46.1:-0.2 |
| squadron: escape.c14 | door from escape.c12 | 5 | 94.0 to 101.5 | place stroll end | 1.67 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.20:-6.85:46.2:-0.3 |
| squadron: escape.c14 | door from escape.c12 | 5,6,8,10 | 102.0 to 108.0 | glance | 1.42 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.21:-6.85:35.4:7.9 |
| squadron: escape.c14 | door from escape.c12 | 5,8 | 108.5 to 109.0 | place stroll end | 1.69 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.20:-6.85:47.0:1.0 |
| squadron: escape.c14 | door from escape.c12 | 5,7 | 109.5 to 110.0 | window look | 1.88 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.20:-6.85:52.3:0.6 |
| squadron: escape.c14 | door from escape.c12 | 6 | 79.0 to 80.0 | glance | 2.36 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.77:-5.69:11.5:0.8 |
| squadron: escape.c14 | door from escape.c12 | 6 | 93.0 to 101.5 | place stroll end | 2.27 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.76:-5.78:11.0:-0.1 |
| squadron: escape.c14 | door from escape.c12 | 6,7,10 | 108.5 to 109.0 | stroll | 2.08 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.68:-6.23:31.7:1.0 |
| squadron: escape.c14 | door from escape.c12 | 6 | 109.5 to 109.5 | window look | 2.30 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @5.62:-6.29:41.8:0.6 |
| squadron: escape.c14 | door from escape.c12 | 7 | 103.0 to 108.0 | glance | 1.82 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @7.09:-6.73:45.7:1.8 |
| squadron: escape.c14 | door from escape.c12 | 8 | 77.5 to 80.0 | glance | 2.15 | 75% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @6.75:-5.89:11.5:0.8 |
| squadron: escape.c14 | door from escape.c12 | 8 | 85.5 to 92.5 | glance | 1.38 | 95% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @6.62:-6.65:11.9:0.1 |
| squadron: escape.c14 | door from escape.c12 | 8,10 | 109.5 to 111.0 | window look | 0.91 | 75% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @6.49:-7.16:22.2:0.6 |
| squadron: escape.c14 | door from escape.c12 | 8,10 | 126.0 to 127.5 | window look | 1.59 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @6.41:-6.80:41.3:0.5 |
| squadron: escape.c14 | door from escape.c12 | 10 | 93.5 to 97.5 | stroll | 2.07 | 75% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell | @6.73:-5.97:12.5:-0.3 |
| ember: hollow.inn | door from hollow.ford | 2 | 79.5 to 80.0 | glance | 2.47 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.50:-20.07:-147.0:0.3 |
| ember: hollow.inn | door from hollow.ford | 2 | 80.5 to 81.5 | stroll | 2.45 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.50:-20.01:-145.2:-0.4 |
| ember: hollow.inn | door from hollow.ford | 2 | 82.0 to 85.0 | place stroll end | 2.41 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.49:-19.99:-145.8:0.2 |
| ember: hollow.inn | door from hollow.ford | 2 | 85.5 to 85.5 | glance | 2.44 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.49:-20.00:-144.9:0.2 |
| ember: hollow.inn | door from hollow.ford | 2 | 104.5 to 105.5 | glance | 2.30 | 55% | o_inn wall (27.0, -18.0)-(23.0, -18.0) wall_inn_window | @21.07:-19.17:-120.9:7.8 |
| ember: hollow.inn | door from hollow.ford | 4 | 94.0 to 98.0 | stroll | 2.42 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.49:-20.04:-147.5:-0.1 |
| ember: hollow.inn | door from hollow.ford | 4,8 | 98.5 to 101.5 | place stroll end | 2.43 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.51:-20.00:-145.4:-0.5 |
| ember: hollow.inn | door from hollow.ford | 4 | 102.0 to 107.5 | glance | 2.17 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @20.59:-19.87:-150.5:7.8 |
| ember: hollow.inn | door from hollow.ford | 5 | 93.0 to 93.5 | stroll | 2.42 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @18.22:-20.01:-145.8:0.6 |
| ember: hollow.inn | door from hollow.ford | 5 | 94.0 to 101.5 | place stroll end | 2.40 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @18.20:-19.99:-146.0:-0.1 |
| ember: hollow.inn | door from hollow.ford | 5,8 | 102.0 to 108.0 | glance | 2.20 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @18.20:-19.99:-155.9:7.8 |
| ember: hollow.inn | door from hollow.ford | 5 | 108.5 to 108.5 | place stroll end | 2.43 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @18.20:-19.99:-145.0:0.2 |
| ember: hollow.inn | door from hollow.ford | 8 | 91.0 to 92.5 | glance | 2.10 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.07:-20.10:-179.8:0.6 |
| ember: hollow.inn | door from hollow.ford | 8 | 93.0 to 98.0 | stroll | 1.40 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.10:-19.40:-180.6:-0.5 |
| ember: hollow.inn | door from hollow.ford | 8 | 108.5 to 109.0 | place stroll end | 1.40 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.09:-19.40:-180.0:0.2 |
| ember: hollow.inn | door from hollow.ford | 8 | 109.5 to 110.5 | window look | 1.45 | 85% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.09:-19.40:-164.4:0.1 |
| ember: hollow.inn | door from hollow.ford | 8,10 | 126.5 to 127.5 | window look | 1.41 | 95% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.11:-19.40:-173.6:-0.4 |
| ember: hollow.inn | door from hollow.ford | 10 | 107.0 to 108.0 | glance | 2.20 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.10:-20.20:-181.2:1.0 |
| ember: hollow.inn | door from hollow.ford | 10 | 108.5 to 109.0 | stroll | 2.01 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.10:-20.00:-175.6:0.0 |
| ember: hollow.inn | door from hollow.ford | 10 | 109.5 to 110.0 | window look | 1.98 | 75% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn | @19.13:-19.91:-164.7:0.1 |

339 failing poses over 117 scene entries (step 0.50 beats).
<!-- /clearance:before -->

## After

<!-- clearance:after -->
| world | failing poses | scenes with one |
| --- | --- | --- |
| warehouse | 0 | - |
| mothership | 0 | - |
| underworld | 0 | - |
| hospital | 0 | - |
| ward | 0 | - |
| hospital_late | 0 | - |
| ward_late | 0 | - |
| gospel/jordan | 0 | - |
| gospel/galilee | 0 | - |
| gospel/road | 0 | - |
| gospel/jerusalem | 0 | - |
| squadron/base | 0 | - |
| squadron/air | 0 | - |
| squadron/city | 0 | - |
| squadron/escape | 0 | - |
| ember/hollow | 0 | - |
| ember/north | 0 | - |
| ember/deeps | 0 | - |
| ember/marsh | 0 | - |
| ember/mountain | 0 | - |
| **all** | **0** | 117 scene entries, 214166 samples |

| scene | entry | phases | beats (from the scene's first downbeat) | pose | centre m | width near | nearest surface at the centre | camera (RW_STORY_CAM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

0 failing poses over 117 scene entries (step 0.50 beats).

Accepted exceptions (4 poses):

| scene | entry | phases | beats (from the scene's first downbeat) | pose | centre m | width near | nearest surface at the centre | camera (RW_STORY_CAM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hospital_late.quiet | door from hospital_late | 2,4,9 | 46.0 to 47.5 | window look | 0.61 | 85% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet | @13.60:10.01:-283.0:-0.2 |
| hospital_late.quiet | door from hospital_late | 2,4,5,8,9 | 61.5 to 62.5 | window look | 1.07 | 55% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet | @13.64:9.43:-322.9:-2.1 |
| hospital_late.quiet | door from hospital_late | 3,5,6,7,8,10 | 46.0 to 48.0 | window look | 1.21 | 95% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet | @14.20:10.31:-279.3:-0.2 |
| hospital_late.quiet | door from hospital_late | 3,6,7,10 | 61.5 to 62.5 | window look | 1.23 | 95% | quiet wall (15.4, 3.0)-(15.4, 16.0) wall_quiet | @14.20:5.57:-101.4:-0.5 |
<!-- /clearance:after -->
