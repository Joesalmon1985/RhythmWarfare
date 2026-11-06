# Camera clearance (package A5: audit findings F5 and F16)

The run camera must not stare into a wall from arm's length. This page says how that is checked, what the thresholds are and why, and lists
the failing poses before and after the fixes. The check is `tools/art/camera_clearance.gd` (the runner) over `tools/art/camera_clearance_check.gd`
(the check itself); `tests/test_camera_clearance.gd` runs the same check in the suite, so a scene added later cannot bring the problem back.

    bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/art/camera_clearance.gd -- [--only <regex>] [--doc after] [--direct-all]
    bash tools/dev/godot.sh --headless --path . -s tools/art/camera_clearance.gd -- --waypoints <map id>     (every waypoint of a map: clearance at its yaw and +-30 degrees)

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
- **Every half beat** (the test: every beat), over every lap, from the first downbeat (a door walk: from the moment it starts, three beats before).
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
- **Doorways in passing are not judged**: while a journey move is walking the camera through a doorway (within 0.9 m of a portal its route crosses), the
  jambs pass in a beat; and while a move walks along a wall's own line (the gospel maps' spine: the route runs through the doorway midpoints on the rooms'
  wall line) that wall is edge-on and the shots show the room beyond. Strolls are always judged.

## What it does not see

- Billboards, occluders and the choice layer's doors (a sprite can still fill the picture: look at the shots), people, and the herald.
- The bad rail (the perfect bot never holds a block) and hotspot cinematics.
- A camera off the scripted rail (a sloppy run stands elsewhere).

<!-- clearance:before -->
| world | failing poses | scenes with one |
| --- | --- | --- |
| warehouse | 51 | warehouse, warehouse.bar, warehouse.balcony, warehouse.chill, warehouse.booth, warehouse.exit |
| mothership | 31 | mothership.gallery, mothership.reactor, mothership.bridge, mothership.exit |
| underworld | 8 | underworld, underworld.court, underworld.furnace, underworld.pit |
| hospital | 24 | hospital, hospital.corridor, hospital.dayroom, hospital.cafeteria, hospital.garden, hospital.exit |
| ward | 23 | ward.art, ward.dorm, ward.corridor |
| hospital_late | 30 | hospital_late.quiet, hospital_late.exit |
| ward_late | 18 | ward_late, ward_late.treat, ward_late.dorm, ward_late.exit |
| gospel/jordan | 0 | - |
| gospel/galilee | 0 | - |
| gospel/road | 0 | - |
| gospel/jerusalem | 0 | - |
| squadron/base | 14 | base.c03 |
| squadron/air | 46 | air, air.c05, air.c06 |
| squadron/city | 108 | city, city.c09, city.c10 |
| squadron/escape | 30 | escape, escape.c13, escape.c14 |
| ember/hollow | 20 | hollow.inn |
| ember/north | 0 | - |
| ember/deeps | 0 | - |
| ember/marsh | 1 | marsh.stair |
| ember/mountain | 0 | - |
| **all** | **404** | 117 scene entries, 214166 samples |

| scene | entry | phases | beats (from the scene's first downbeat) | pose | centre m | width near | nearest surface at the centre |
| --- | --- | --- | --- | --- | --- | --- | --- |
| warehouse | direct | 1 | 52.0 to 52.5 | window look | 0.99 | 75% | bstair_1 wall (-4.0, -3.0)-(-7.0, -3.0) wall_panel |
| warehouse | arrival | 2,3,4,5,7,9,10 | 52.0 to 52.5 | window look | 0.92 | 65% | bstair_1 wall (-4.0, -3.0)-(-7.0, -3.0) wall_panel |
| warehouse | arrival | 6,8 | 52.5 to 52.5 | window look | 0.97 | 75% | bstair_1 wall (-4.0, -3.0)-(-7.0, -3.0) wall_panel |
| warehouse.bar | door from warehouse | all | 18.5 to 18.5 | move to bar_taps | 2.35 | 60% | bar wall (8.5, 6.0)-(7.0, 6.0) wall_bar |
| warehouse.balcony | door from warehouse | all | 6.0 to 6.0 | herald look | 1.32 | 55% | bstair_1 wall (-4.0, -3.0)-(-7.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 2,4 | 32.5 to 37.5 | move to balcony_far | 1.30 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | all | 38.0 to 45.0 | glance | 0.81 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 2,3,5,7,8,9,10 | 45.5 to 46.5 | window look | 0.83 | 85% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 2,3,5,8,10 | 62.5 to 63.5 | window look | 1.28 | 75% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 3,6,8,9,10 | 32.0 to 37.5 | move to balcony_far | 1.26 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 4,6 | 45.5 to 47.0 | window look | 0.67 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 4,6 | 62.0 to 63.5 | window look | 0.72 | 75% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 5,7 | 31.5 to 37.5 | move to balcony_far | 1.23 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.balcony | door from warehouse | 7,9 | 63.0 to 63.5 | window look | 1.44 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.chill | door from warehouse.bar | 2,5,8 | 34.0 to 34.0 | move to sofa_front | 1.86 | 60% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.bar | all | 40.5 to 44.5 | glance | 0.70 | 100% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 0.71 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 2,9 | 45.5 to 46.0 | window look | 0.77 | 80% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 2,9 | 48.0 to 61.0 | window look | 0.51 | 80% | sofa_a wall (8.0, 10.8)-(9.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.bar | 3,4,6,10 | 33.5 to 34.0 | move to sofa_front | 1.84 | 70% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.bar | 3,4,5,7,10 | 45.5 to 47.0 | window look | 0.72 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 4,6 | 35.0 to 35.0 | move to sofa_front | 2.50 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 4,7,10 | 45.0 to 45.0 | place sofa_front | 0.70 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 6,8 | 45.5 to 47.5 | window look | 0.74 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.bar | 7,9 | 34.5 to 34.5 | move to sofa_front | 1.88 | 70% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.bar | 7,9 | 35.5 to 35.5 | move to sofa_front | 2.49 | 70% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | all | -3.0 to 1.0 | door walk to chill_door | 0.80 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.chill | door from warehouse.balcony | all | 3.0 to 3.0 | herald look | 0.75 | 100% | bstair_1 wall (-4.0, -3.0)-(-7.0, -3.0) wall_panel |
| warehouse.chill | door from warehouse.balcony | all | 9.5 to 9.5 | herald look | 2.02 | 65% | bar wall (8.5, 6.0)-(7.0, 6.0) wall_bar |
| warehouse.chill | door from warehouse.balcony | 2,5,8 | 34.0 to 34.0 | move to sofa_front | 1.86 | 60% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.balcony | all | 40.5 to 44.5 | glance | 0.70 | 100% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 0.71 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 2,9 | 45.5 to 46.0 | window look | 0.77 | 80% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 2,9 | 48.0 to 61.0 | window look | 0.51 | 80% | sofa_a wall (8.0, 10.8)-(9.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.balcony | 3,4,6,10 | 33.5 to 34.0 | move to sofa_front | 1.84 | 70% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.balcony | 3,4,5,7,10 | 45.5 to 47.0 | window look | 0.72 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 4,6 | 35.0 to 35.0 | move to sofa_front | 2.50 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 4,7,10 | 45.0 to 45.0 | place sofa_front | 0.70 | 95% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 6,8 | 45.5 to 47.5 | window look | 0.74 | 90% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.chill | door from warehouse.balcony | 7,9 | 34.5 to 34.5 | move to sofa_front | 1.88 | 70% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.chill | door from warehouse.balcony | 7,9 | 35.5 to 35.5 | move to sofa_front | 2.49 | 70% | sofa_a wall (11.0, 12.0)-(8.0, 12.0) wall_chill |
| warehouse.booth | door from warehouse.balcony | all | -3.0 to 1.0 | door walk to stage_edge | 0.80 | 100% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.booth | door from warehouse.balcony | all | 1.5 to 2.0 | herald look | 1.60 | 95% | balcony wall (-11.0, 5.0)-(-11.0, -3.0) wall_panel |
| warehouse.exit | door from warehouse.chill | all | 0.0 to 0.5 | door walk to floor_centre | 1.80 | 80% | chill wall (9.0, 10.8)-(7.0, 10.8) wall_chill |
| warehouse.exit | door from warehouse.chill | all | 4.0 to 4.0 | door walk to floor_centre | 1.47 | 75% | bar wall (7.0, 6.0)-(7.0, 4.0) wall_bar |
| warehouse.exit | door from warehouse.chill | 7 | 40.0 to 45.0 | glance | 1.86 | 65% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick |
| warehouse.exit | door from warehouse.chill | 7 | 45.5 to 46.0 | window look | 2.00 | 55% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick |
| warehouse.exit | door from warehouse.chill | 7 | 63.0 to 63.5 | window look | 1.66 | 75% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick |
| warehouse.exit | door from warehouse.booth | 7 | 40.0 to 45.0 | glance | 1.86 | 65% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick |
| warehouse.exit | door from warehouse.booth | 7 | 45.5 to 46.0 | window look | 2.00 | 55% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick |
| warehouse.exit | door from warehouse.booth | 7 | 63.0 to 63.5 | window look | 1.66 | 75% | tunnel_c wall (-1.5, 15.0)-(-1.5, 13.0) wall_brick |
| mothership.gallery | door from mothership | 2,4,5,6,7,8,9 | 35.5 to 37.0 | move to planet_window | 1.39 | 85% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | all | 37.5 to 44.5 | glance | 0.48 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 0.48 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | all | 45.5 to 46.5 | window look | 0.47 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | 2,9 | 62.0 to 63.5 | window look | 0.58 | 75% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | 3,10 | 36.0 to 37.0 | move to planet_window | 1.52 | 85% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | 3,4,5,6,7,8,10 | 62.5 to 63.5 | window look | 0.80 | 75% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.gallery | door from mothership | 4,7,10 | 45.0 to 45.0 | place planet_window | 0.50 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.reactor | door from mothership | all | 42.0 to 44.5 | glance | 1.40 | 100% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube |
| mothership.reactor | door from mothership | all | 45.0 to 45.0 | place reactor_core | 1.40 | 100% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube |
| mothership.reactor | door from mothership | all | 45.5 to 46.0 | window look | 1.46 | 85% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube |
| mothership.reactor | door from mothership | all | 63.0 to 63.5 | window look | 2.43 | 55% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube |
| mothership.bridge | door from mothership.gallery | all | -3.0 to 3.0 | door walk to bridge_door | 0.50 | 100% | gallery wall (27.0, 10.0)-(7.0, 10.0) wall_planet |
| mothership.bridge | door from mothership.gallery | all | 5.0 to 5.5 | door walk to bridge_door | 2.14 | 55% | catwalk wall (31.0, 9.0)-(27.0, 9.0) wall_tube |
| mothership.bridge | door from mothership.reactor | all | -3.0 to -0.5 | door walk to bridge_door | 1.40 | 100% | reactor wall (27.0, -3.0)-(41.0, -3.0) wall_tube |
| mothership.exit | door from mothership.bridge | all | 6.0 to 6.0 | glance | 2.32 | 55% | catwalk wall (41.0, 9.0)-(40.0, 9.0) wall_tube |
| mothership.exit | door from mothership.bridge | all | 7.0 to 10.0 | glance | 0.28 | 95% | catwalk wall (37.0, 9.0)-(35.0, 9.0) wall_window |
| mothership.exit | door from mothership.bridge | 2,3,5,7,8,9,10 | 38.0 to 44.5 | glance | 1.49 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 2,3,5,6,8,9 | 45.0 to 45.0 | stroll | 1.42 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 2,9 | 45.5 to 47.5 | window look | 1.45 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 2,9 | 62.0 to 62.0 | window look | 2.04 | 80% | airlock wall (32.0, 19.0)-(32.0, 16.0) wall_airlock |
| mothership.exit | door from mothership.bridge | 2,6,8,9 | 63.0 to 63.5 | window look | 0.45 | 95% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 3,5 | 45.5 to 47.0 | window look | 1.80 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 3,5 | 62.5 to 63.5 | window look | 1.35 | 90% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 4,6 | 38.5 to 44.5 | glance | 1.80 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 4,7,10 | 45.0 to 45.0 | place airlock | 1.81 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 4,7,10 | 45.5 to 45.5 | window look | 1.94 | 100% | airlock wall (36.0, 19.0)-(32.0, 19.0) wall_hatch |
| mothership.exit | door from mothership.bridge | 4,7,10 | 46.5 to 48.0 | window look | 1.85 | 55% | airlock_ramp wall (35.0, 15.0)-(35.0, 16.0) wall_airlock |
| mothership.exit | door from mothership.bridge | 4,7,10 | 61.5 to 63.5 | window look | 1.73 | 65% | airlock wall (35.0, 16.0)-(36.0, 16.0) wall_airlock |
| mothership.exit | door from mothership.bridge | 6,8 | 45.5 to 46.0 | window look | 1.42 | 100% | airlock wall (36.0, 16.0)-(36.0, 19.0) wall_airlock |
| mothership.exit | door from mothership.bridge | 6,8 | 48.5 to 60.5 | window look | 1.21 | 70% | airlock wall (35.0, 16.0)-(36.0, 16.0) wall_airlock |
| underworld | arrival | all | 0.0 to 2.0 | passage window | 1.08 | 100% | step up to tier_l: arena wall (-7.0, 9.0)-(-7.0, -3.0) wall_arena |
| underworld | arrival | all | 21.0 to 21.5 | move to arena_gate | 1.91 | 100% | step up to gate_dais: arena wall (-3.0, -3.0)-(3.0, -3.0) wall_arena |
| underworld | arrival | all | 22.0 to 28.0 | glance | 0.50 | 100% | step up to gate_dais: arena wall (-3.0, -3.0)-(3.0, -3.0) wall_arena |
| underworld.court | door from underworld | all | 5.5 to 5.5 | door walk to court_door | 2.31 | 55% | step up to tier_r: arena wall (7.0, -3.0)-(7.0, 9.0) wall_arena |
| underworld.court | door from underworld | all | 6.0 to 6.5 | glance | 0.84 | 65% | step up to tier_r: arena wall (7.0, -3.0)-(7.0, 9.0) wall_arena |
| underworld.furnace | door from underworld | all | 5.5 to 6.0 | glance | 1.28 | 65% | step up to tier_l: arena wall (-7.0, 9.0)-(-7.0, -3.0) wall_arena |
| underworld.pit | door from underworld.furnace | all | 3.5 to 3.5 | door walk to causeway_in | 1.66 | 65% | step up to tier_l: arena wall (-7.0, 9.0)-(-7.0, -3.0) wall_arena |
| underworld.pit | door from underworld.furnace | all | 9.5 to 9.5 | glance | 1.90 | 70% | court wall (16.0, 8.0)-(11.0, 8.0) wall_column |
| hospital | arrival | 4,6 | 46.5 to 46.5 | window look | 1.56 | 80% | ward wall (5.0, 2.0)-(5.0, 5.0) wall_ward |
| hospital | arrival | 4,6 | 62.5 to 63.0 | window look | 0.83 | 65% | ward wall (5.0, 2.0)-(5.0, 5.0) wall_ward |
| hospital.corridor | door from hospital | 7,9 | 46.5 to 47.0 | window look | 0.51 | 95% | corridor wall (29.0, 3.0)-(15.0, 3.0) wall_door |
| hospital.corridor | door from hospital | 7,9 | 62.0 to 63.5 | window look | 0.87 | 95% | corridor wall (29.0, 3.0)-(15.0, 3.0) wall_door |
| hospital.dayroom | door from hospital.corridor | 2,6,8,9 | 36.0 to 36.0 | move to day_tv_in | 2.13 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.dayroom | door from hospital.corridor | all | 36.5 to 37.0 | place day_tv_in | 2.05 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.dayroom | door from hospital.corridor | all | 37.5 to 44.5 | glance | 1.39 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.dayroom | door from hospital.corridor | 2,4,5,7,8,10 | 45.0 to 45.0 | stroll | 1.42 | 90% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.dayroom | door from hospital.corridor | 2,3,4,5,6,7,9 | 45.5 to 45.5 | window look | 1.71 | 90% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.dayroom | door from hospital.corridor | 3,6,9 | 45.0 to 45.0 | place day_tv_in | 2.06 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.dayroom | door from hospital.corridor | 8,10 | 45.5 to 46.0 | window look | 0.71 | 75% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.cafeteria | door from hospital.corridor | 2,9 | 43.5 to 44.0 | glance | 2.25 | 55% | cafeteria wall (47.0, -6.0)-(47.0, -3.0) wall_cafe |
| hospital.cafeteria | door from hospital.corridor | 2,9 | 44.5 to 44.5 | stroll | 2.18 | 55% | cafeteria wall (47.0, -6.0)-(47.0, -3.0) wall_cafe |
| hospital.cafeteria | door from hospital.corridor | 3,5 | 43.5 to 43.5 | glance | 2.38 | 55% | cafeteria wall (47.0, -6.0)-(47.0, -3.0) wall_cafe |
| hospital.garden | door from hospital.dayroom | all | -3.0 to -3.0 | door walk to garden_door_w | 2.05 | 100% | day_tv wall (17.0, -15.0)-(23.0, -15.0) wall_tv |
| hospital.garden | door from hospital.dayroom | all | 5.0 to 5.0 | door walk to garden_door_w | 2.49 | 55% | corridor wall (26.0, -1.0)-(29.0, -1.0) wall_door |
| hospital.exit | door from hospital.garden | 3,5 | 36.0 to 36.5 | stroll | 2.35 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 3,5 | 37.0 to 37.0 | place stroll end | 2.36 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 3 | 37.5 to 44.0 | glance | 1.56 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 5 | 37.5 to 44.5 | glance | 0.93 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 5 | 45.0 to 45.0 | stroll | 0.97 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 5 | 45.5 to 45.5 | window look | 1.21 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 5 | 63.5 to 63.5 | window look | 0.96 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital.exit | door from hospital.garden | 7 | 41.5 to 43.0 | glance | 2.26 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| ward.art | door from ward | all | 3.5 to 4.0 | door walk to art_door | 2.34 | 65% | corridor wall (15.0, 8.0)-(7.0, 8.0) wall_cdoor2 |
| ward.dorm | door from ward | 2,4,7,9,10 | 38.0 to 45.0 | glance | 0.99 | 100% | ceiling of dorm_alcove |
| ward.dorm | door from ward | 2,9 | 45.5 to 46.0 | window look | 1.16 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.dorm | door from ward | 3,4,6,10 | 37.5 to 37.5 | move to dorm_bed | 1.58 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.dorm | door from ward | 3,5,6,8 | 38.0 to 45.0 | glance | 0.94 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.dorm | door from ward | 3,5 | 45.5 to 47.0 | window look | 0.94 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.dorm | door from ward | 3,5 | 62.0 to 62.5 | window look | 2.03 | 65% | dorm_alcove wall (24.0, 16.5)-(24.0, 14.0) wall_dwindow |
| ward.dorm | door from ward | 4,7,10 | 45.5 to 47.5 | window look | 1.18 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.dorm | door from ward | 4,7,10 | 62.0 to 62.0 | window look | 2.02 | 65% | dorm_alcove wall (24.0, 16.5)-(24.0, 14.0) wall_dwindow |
| ward.dorm | door from ward | 6,8 | 45.5 to 46.5 | window look | 0.87 | 95% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.dorm | door from ward | 6,8 | 62.5 to 63.0 | window look | 2.02 | 75% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow |
| ward.corridor | door from ward.art | all | 3.5 to 3.5 | door walk to corr_west | 2.34 | 65% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward.corridor | door from ward.art | 2,4 | 48.5 to 48.5 | window look | 2.03 | 75% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward.corridor | door from ward.art | 2,4 | 61.0 to 63.0 | window look | 1.71 | 55% | corridor wall (33.0, 4.0)-(33.0, 5.0) wall_cdoor |
| ward.corridor | door from ward.art | 8,10 | 47.0 to 48.5 | window look | 2.00 | 65% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward.corridor | door from ward.art | 8,10 | 61.0 to 62.0 | window look | 2.04 | 75% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward.corridor | door from ward.dorm | all | -3.0 to -2.0 | door walk to corr_west | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward.corridor | door from ward.dorm | all | 5.0 to 5.0 | door walk to corr_west | 0.86 | 55% | corridor wall (22.0, 8.0)-(17.0, 8.0) wall_cdoor2 |
| ward.corridor | door from ward.dorm | all | 5.5 to 6.0 | glance | 1.19 | 55% | corridor wall (22.0, 8.0)-(17.0, 8.0) wall_cdoor2 |
| ward.corridor | door from ward.dorm | 2,4 | 48.5 to 48.5 | window look | 2.03 | 75% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward.corridor | door from ward.dorm | 2,4 | 61.0 to 63.0 | window look | 1.71 | 55% | corridor wall (33.0, 4.0)-(33.0, 5.0) wall_cdoor |
| ward.corridor | door from ward.dorm | 8,10 | 47.0 to 48.5 | window look | 2.00 | 65% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward.corridor | door from ward.dorm | 8,10 | 61.0 to 62.0 | window look | 2.04 | 75% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| hospital_late.quiet | door from hospital_late | all | 16.0 to 16.0 | glance | 2.03 | 60% | quiet wall (15.4, 3.0)-(15.4, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | all | 16.5 to 21.0 | move to quiet_far | 1.20 | 100% | quiet wall (15.4, 3.0)-(15.4, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | all | 22.5 to 28.5 | glance | 1.50 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 2,9 | 29.0 to 32.5 | stroll | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 2,9 | 33.0 to 37.5 | place stroll end | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | all | 38.0 to 44.0 | glance | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 2,4,5,7,10 | 44.5 to 45.0 | stroll | 1.50 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 2,4,9 | 46.0 to 47.5 | window look | 0.49 | 95% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 2,4,9 | 61.5 to 63.5 | window look | 0.20 | 95% | corridor wall (29.0, 3.0)-(15.0, 3.0) wall_door |
| hospital_late.quiet | door from hospital_late | 3,5,6,8 | 29.0 to 36.5 | stroll | 0.52 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 3,5,6,8 | 37.0 to 37.5 | place stroll end | 0.52 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 3,6,9 | 44.5 to 45.0 | place stroll end | 0.52 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 3,5,7 | 45.5 to 48.0 | window look | 0.56 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 3,5,6,7,8,10 | 61.5 to 63.0 | window look | 1.25 | 95% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 4,7,10 | 29.0 to 37.5 | place quiet_far | 1.50 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 6,10 | 45.5 to 47.5 | window look | 0.88 | 90% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 8 | 44.5 to 44.5 | stroll | 0.84 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.quiet | door from hospital_late | 8 | 45.5 to 47.5 | window look | 1.11 | 100% | quiet wall (13.0, 16.0)-(13.0, 3.0) wall_quiet |
| hospital_late.exit | door from hospital_late.cafe | 3,10 | 36.0 to 36.5 | stroll | 2.35 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.cafe | 3,10 | 37.0 to 37.5 | place stroll end | 2.36 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.cafe | 3 | 41.5 to 44.0 | glance | 1.03 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.cafe | 3 | 44.5 to 45.0 | stroll | 0.94 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.cafe | 3 | 45.5 to 45.5 | window look | 1.21 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.quiet | all | -3.0 to -2.0 | door walk to garden_door_e | 1.50 | 100% | quiet wall (15.4, 16.0)-(13.0, 16.0) wall_quiet |
| hospital_late.exit | door from hospital_late.quiet | all | 2.0 to 4.0 | door walk to garden_door_e | 0.20 | 75% | corridor wall (29.0, 3.0)-(15.0, 3.0) wall_door |
| hospital_late.exit | door from hospital_late.quiet | 3,10 | 36.0 to 36.5 | stroll | 2.35 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.quiet | 3,10 | 37.0 to 37.5 | place stroll end | 2.36 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.quiet | 3 | 41.5 to 44.0 | glance | 1.03 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.quiet | 3 | 44.5 to 45.0 | stroll | 0.94 | 65% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| hospital_late.exit | door from hospital_late.quiet | 3 | 45.5 to 45.5 | window look | 1.21 | 55% | bandstand wall (59.0, -3.0)-(63.0, -3.0) wall_hedge |
| ward_late | door from ward_late.exit | all | 2.5 to 3.0 | door walk to court_door_w | 2.20 | 55% | corridor wall (15.0, 8.0)-(7.0, 8.0) wall_cdoor2 |
| ward_late.treat | door from ward_late | all | 25.5 to 28.5 | glance | 1.92 | 100% | ceiling of quiet_bed |
| ward_late.dorm | door from ward_late | all | 8.0 to 8.0 | glance | 2.34 | 70% | corridor wall (30.0, 4.0)-(33.0, 4.0) wall_cdoor |
| ward_late.dorm | door from ward_late | 2,4 | 25.5 to 28.5 | glance | 1.95 | 100% | ceiling of dorm_alcove |
| ward_late.dorm | door from ward_late | 2,4,5,7 | 37.5 to 44.5 | glance | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 2,5,8 | 45.0 to 45.0 | place dorm_bed | 1.11 | 95% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 2,4,5,6,8 | 45.5 to 47.5 | window look | 1.18 | 90% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 2,5,8 | 62.0 to 62.0 | window look | 2.03 | 65% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 3,5,6,7,8,9,10 | 25.5 to 28.5 | glance | 2.04 | 100% | lintel over dorm_alcove: dorm wall (28.0, 14.0)-(24.0, 14.0) wall_dado |
| ward_late.dorm | door from ward_late | 3,6,8,9,10 | 38.0 to 44.5 | glance | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 3,4,6,7,9,10 | 45.0 to 45.0 | stroll | 1.11 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 3,10 | 45.5 to 47.5 | window look | 0.79 | 95% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 3,10 | 61.5 to 62.5 | window look | 0.86 | 85% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 4,6,7,9 | 62.0 to 62.5 | window look | 2.03 | 65% | dorm_alcove wall (28.0, 14.0)-(28.0, 16.5) wall_dwindow |
| ward_late.dorm | door from ward_late | 7,9 | 45.5 to 47.0 | window look | 1.02 | 90% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.exit | door from ward_late.dorm | all | -3.0 to -2.0 | door walk to day_door_a | 1.10 | 100% | dorm_alcove wall (28.0, 16.5)-(24.0, 16.5) wall_dwindow |
| ward_late.exit | door from ward_late.dorm | all | 4.5 to 5.5 | door walk to day_door_a | 0.68 | 65% | corridor wall (22.0, 8.0)-(17.0, 8.0) wall_cdoor2 |
| ward_late.exit | door from ward_late.dorm | all | 6.0 to 6.0 | glance | 1.59 | 55% | corridor wall (22.0, 8.0)-(17.0, 8.0) wall_cdoor2 |
| squadron: base.c03 | door from base | all | 6.0 to 6.0 | glance | 2.16 | 55% | line wall (0.0, 3.0)-(0.0, 0.0) wall_berm |
| squadron: base.c03 | door from base | all | 7.5 to 7.5 | glance | 2.18 | 55% | line wall (0.0, 0.0)-(3.0, 0.0) wall_berm |
| squadron: base.c03 | door from base | 4 | 95.0 to 97.5 | stroll | 2.31 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | door from base | 4 | 98.0 to 101.5 | place stroll end | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | door from base | 4 | 102.0 to 109.0 | glance | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | door from base | 4 | 109.5 to 110.0 | window look | 2.28 | 100% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | door from base | 4,6 | 127.0 to 127.5 | window look | 2.25 | 95% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | door from base | 9 | 110.5 to 110.5 | window look | 2.42 | 100% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | arrival | 4 | 95.0 to 97.5 | stroll | 2.31 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | arrival | 4 | 98.0 to 101.5 | place stroll end | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | arrival | 4 | 102.0 to 109.0 | glance | 2.30 | 65% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | arrival | 4 | 109.5 to 110.0 | window look | 2.28 | 100% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | arrival | 4,6 | 127.0 to 127.5 | window look | 2.25 | 95% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: base.c03 | arrival | 9 | 110.5 to 110.5 | window look | 2.42 | 100% | tent wall (0.0, -10.0)-(10.0, -10.0) wall_tent |
| squadron: air | arrival | 2 | 103.0 to 108.0 | glance | 2.07 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3 | 86.5 to 92.0 | glance | 1.67 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3,8 | 92.5 to 97.5 | stroll | 1.10 | 95% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3,5,8 | 98.0 to 101.0 | place stroll end | 1.09 | 85% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3,8,10 | 101.5 to 108.5 | glance | 1.07 | 100% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3 | 109.0 to 109.0 | place stroll end | 1.12 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3 | 109.5 to 110.0 | window look | 1.25 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 3,5 | 127.0 to 127.5 | window look | 1.14 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 4,7,10 | 46.5 to 62.5 | window look | 1.31 | 95% | bomber wall (10.0, 22.0)-(10.0, 14.0) wall_bomber |
| squadron: air | arrival | 5 | 97.0 to 97.5 | stroll | 2.30 | 60% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 5,9 | 102.0 to 108.5 | glance | 1.61 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 5 | 109.0 to 109.0 | stroll | 1.59 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 5 | 109.5 to 109.5 | window look | 1.77 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,8 | 46.5 to 48.0 | window look | 1.52 | 100% | bomber wall (10.0, 22.0)-(10.0, 14.0) wall_bomber |
| squadron: air | arrival | 6,8 | 61.5 to 62.5 | window look | 1.55 | 100% | bomber wall (10.0, 22.0)-(10.0, 14.0) wall_bomber |
| squadron: air | arrival | 6,8 | 63.5 to 63.5 | window look | 2.43 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,8 | 64.0 to 69.0 | place stroll end | 2.48 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,8 | 69.5 to 69.5 | glance | 2.49 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6 | 76.0 to 76.5 | glance | 2.36 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6 | 77.0 to 81.5 | stroll | 2.33 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,10 | 82.0 to 85.5 | place stroll end | 2.36 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,8,10 | 86.0 to 92.0 | glance | 2.04 | 90% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 6 | 92.5 to 97.5 | stroll | 1.72 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 6 | 98.0 to 101.0 | place stroll end | 1.71 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 6 | 101.5 to 108.5 | glance | 1.72 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 6 | 109.0 to 109.0 | place stroll end | 1.70 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,8 | 109.5 to 110.5 | window look | 1.72 | 95% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 6,8 | 126.5 to 127.5 | window look | 1.70 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 8 | 76.5 to 76.5 | glance | 2.50 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 8 | 77.0 to 85.5 | place stroll end | 2.47 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 8 | 109.0 to 109.0 | stroll | 2.00 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 9 | 88.5 to 92.0 | glance | 2.36 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 9 | 92.5 to 92.5 | stroll | 2.49 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 9 | 93.5 to 93.5 | stroll | 2.49 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 9 | 94.0 to 94.0 | place stroll end | 2.49 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 10 | 81.0 to 81.5 | stroll | 2.48 | 80% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 10 | 92.5 to 101.0 | place stroll end | 2.47 | 70% | bomber wall (14.0, 22.0)-(10.0, 22.0) wall_bomber |
| squadron: air | arrival | 10 | 110.0 to 110.5 | window look | 2.35 | 90% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air | arrival | 10 | 126.5 to 127.0 | window look | 2.33 | 100% | bomber wall (14.0, 14.0)-(14.0, 22.0) wall_bomber |
| squadron: air.c05 | arrival | 2 | 101.5 to 104.0 | glance | 2.44 | 85% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar |
| squadron: air.c05 | arrival | 2 | 106.0 to 108.5 | glance | 2.45 | 75% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar |
| squadron: air.c05 | arrival | 2 | 109.0 to 109.0 | place stroll end | 2.48 | 55% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar |
| squadron: air.c05 | arrival | 2 | 109.5 to 110.0 | window look | 2.45 | 85% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar |
| squadron: air.c05 | arrival | 2,4 | 127.0 to 127.5 | window look | 2.46 | 55% | store wall (38.0, 0.0)-(38.0, 12.0) wall_hangar |
| squadron: air.c06 | door from air.c05 | all | 5.5 to 7.0 | glance | 1.49 | 55% | line wall (7.0, 0.0)-(26.0, 0.0) wall_berm |
| squadron: air.c06 | door from air.c05 | all | 10.0 to 10.0 | glance | 1.79 | 65% | tent wall (0.0, 0.0)-(0.0, -4.0) wall_tent |
| squadron: city | arrival | 2,4,5,7,8,10 | 42.5 to 42.5 | glance | 2.47 | 90% | ceiling of bomber_r |
| squadron: city | arrival | 2,4,5,7,8,10 | 43.5 to 43.5 | glance | 2.43 | 100% | ceiling of bomber_r |
| squadron: city | arrival | 2 | 87.0 to 92.5 | glance | 2.06 | 70% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 2 | 93.5 to 93.5 | stroll | 2.49 | 70% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 2 | 94.0 to 94.0 | place stroll end | 2.49 | 70% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 2 | 107.0 to 107.0 | glance | 2.40 | 100% | ceiling of bomber_r |
| squadron: city | arrival | 3,6,9 | 43.0 to 43.0 | glance | 2.41 | 90% | ceiling of bomber_r |
| squadron: city | arrival | 3,6,9 | 46.5 to 48.5 | window look | 1.32 | 95% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber |
| squadron: city | arrival | 3,6,9 | 61.0 to 62.5 | window look | 1.33 | 100% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber |
| squadron: city | arrival | 3 | 81.0 to 81.5 | stroll | 2.48 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 3,8 | 82.0 to 85.0 | place stroll end | 2.47 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 3 | 85.5 to 88.0 | glance | 2.43 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 3 | 90.0 to 92.5 | glance | 2.43 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 3 | 93.0 to 101.5 | place stroll end | 2.47 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 3 | 102.0 to 108.5 | glance | 2.39 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 3 | 110.0 to 110.5 | window look | 2.38 | 90% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 3 | 126.5 to 127.0 | window look | 2.34 | 80% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 4,6,9 | 106.5 to 106.5 | glance | 2.46 | 100% | ceiling of bomber_r |
| squadron: city | arrival | 4,6,9 | 107.5 to 107.5 | glance | 2.42 | 100% | ceiling of bomber_r |
| squadron: city | arrival | 5 | 86.0 to 92.5 | glance | 1.60 | 85% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 5,10 | 93.0 to 97.5 | stroll | 1.10 | 95% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 5,7,10 | 98.0 to 101.5 | place stroll end | 1.09 | 85% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 5,7 | 102.0 to 109.0 | glance | 1.09 | 85% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 5 | 109.5 to 110.0 | window look | 1.30 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 5,7 | 127.0 to 127.5 | window look | 2.21 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 7 | 97.0 to 97.5 | stroll | 2.30 | 60% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 7 | 109.5 to 109.5 | window look | 1.79 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 8,10 | 46.5 to 48.0 | window look | 1.44 | 100% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber |
| squadron: city | arrival | 8,10 | 61.5 to 62.5 | window look | 1.55 | 100% | bomber_r wall (14.0, -8.0)-(14.0, 0.0) wall_bomber |
| squadron: city | arrival | 8,10 | 63.5 to 63.5 | window look | 2.43 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 8,10 | 64.0 to 69.5 | place stroll end | 2.48 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 8,10 | 70.0 to 76.0 | glance | 2.27 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 8 | 76.5 to 81.5 | stroll | 2.33 | 90% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 8,10 | 85.5 to 92.5 | glance | 1.70 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 8 | 93.0 to 97.5 | stroll | 1.72 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 8 | 98.0 to 101.5 | place stroll end | 1.71 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 8 | 102.0 to 109.0 | glance | 1.71 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 8 | 109.5 to 110.0 | window look | 1.74 | 95% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 8,10 | 126.5 to 127.5 | window look | 1.79 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 10 | 76.5 to 85.0 | place stroll end | 2.47 | 80% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 10 | 102.0 to 103.0 | glance | 2.45 | 100% | bomber_r wall (10.0, -8.0)-(14.0, -8.0) wall_bomber |
| squadron: city | arrival | 10 | 106.5 to 109.0 | glance | 2.03 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city | arrival | 10 | 109.5 to 110.5 | window look | 1.91 | 100% | bomber_r wall (10.0, 0.0)-(10.0, -8.0) wall_bomber |
| squadron: city.c09 | door from city.c08 | 2,8 | 109.5 to 112.0 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 2,8 | 125.5 to 127.5 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 3 | 108.5 to 108.5 | glance | 2.44 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 3,10 | 127.5 to 127.5 | window look | 2.47 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4 | 77.5 to 77.5 | stroll | 2.49 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4 | 78.0 to 85.0 | place stroll end | 2.46 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4 | 85.5 to 92.5 | glance | 1.37 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4,10 | 93.0 to 93.5 | stroll | 1.28 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4,6,10 | 94.0 to 101.5 | place stroll end | 1.27 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4,6,10 | 102.0 to 109.0 | glance | 1.28 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4,6 | 109.5 to 110.5 | window look | 1.41 | 75% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 4,6 | 126.5 to 127.5 | window look | 1.31 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 5 | 110.5 to 112.5 | window look | 2.30 | 90% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 5 | 125.0 to 126.5 | window look | 2.29 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 6 | 93.5 to 93.5 | stroll | 2.48 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 7 | 72.5 to 75.0 | glance | 2.40 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 7 | 86.0 to 90.5 | glance | 1.92 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 7,9 | 110.0 to 112.0 | window look | 1.30 | 100% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 7,9 | 125.5 to 127.0 | window look | 1.31 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 9 | 88.5 to 92.0 | glance | 2.21 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c08 | 10 | 88.0 to 92.5 | glance | 2.06 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | all | 6.5 to 9.5 | glance | 0.55 | 95% | street wall (24.0, 8.0)-(9.0, 8.0) wall_stucco |
| squadron: city.c09 | door from city.c10 | 2,8 | 109.5 to 112.0 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 2,8 | 125.5 to 127.5 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 3 | 108.5 to 108.5 | glance | 2.44 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 3,10 | 127.5 to 127.5 | window look | 2.47 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4 | 77.5 to 77.5 | stroll | 2.49 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4 | 78.0 to 85.0 | place stroll end | 2.46 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4 | 85.5 to 92.5 | glance | 1.37 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4,10 | 93.0 to 93.5 | stroll | 1.28 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4,6,10 | 94.0 to 101.5 | place stroll end | 1.27 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4,6,10 | 102.0 to 109.0 | glance | 1.28 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4,6 | 109.5 to 110.5 | window look | 1.41 | 75% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 4,6 | 126.5 to 127.5 | window look | 1.31 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 5 | 110.5 to 112.5 | window look | 2.30 | 90% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 5 | 125.0 to 126.5 | window look | 2.29 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 6 | 93.5 to 93.5 | stroll | 2.48 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 7 | 72.5 to 75.0 | glance | 2.40 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 7 | 86.0 to 90.5 | glance | 1.92 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 7,9 | 110.0 to 112.0 | window look | 1.30 | 100% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 7,9 | 125.5 to 127.0 | window look | 1.31 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 9 | 88.5 to 92.0 | glance | 2.21 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | door from city.c10 | 10 | 88.0 to 92.5 | glance | 2.06 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 2,8 | 109.5 to 112.0 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 2,8 | 125.5 to 127.5 | window look | 1.87 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 3 | 108.5 to 108.5 | glance | 2.44 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 3,10 | 127.5 to 127.5 | window look | 2.47 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4 | 77.5 to 77.5 | stroll | 2.49 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4 | 78.0 to 85.0 | place stroll end | 2.46 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4 | 85.5 to 92.5 | glance | 1.37 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4,10 | 93.0 to 93.5 | stroll | 1.28 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4,6,10 | 94.0 to 101.5 | place stroll end | 1.27 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4,6,10 | 102.0 to 109.0 | glance | 1.28 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4,6 | 109.5 to 110.5 | window look | 1.41 | 75% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 4,6 | 126.5 to 127.5 | window look | 1.31 | 85% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 5 | 110.5 to 112.5 | window look | 2.30 | 90% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 5 | 125.0 to 126.5 | window look | 2.29 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 6 | 93.5 to 93.5 | stroll | 2.48 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 7 | 72.5 to 75.0 | glance | 2.40 | 55% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 7 | 86.0 to 90.5 | glance | 1.92 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 7,9 | 110.0 to 112.0 | window look | 1.30 | 100% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 7,9 | 125.5 to 127.0 | window look | 1.31 | 95% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 9 | 88.5 to 92.0 | glance | 2.21 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c09 | arrival | 10 | 88.0 to 92.5 | glance | 2.06 | 65% | office_c wall (12.0, 16.0)-(2.0, 16.0) wall_panel |
| squadron: city.c10 | door from city | all | 3.0 to 5.0 | door walk to c10_arrive | 0.49 | 70% | street wall (13.0, 0.0)-(24.0, 0.0) wall_stucco |
| squadron: escape | door from escape.c14 | all | 7.5 to 8.0 | glance | 1.66 | 55% | quay wall (0.0, 3.0)-(0.0, 0.0) wall_quay |
| squadron: escape.c13 | door from escape.c12 | all | 6.5 to 7.0 | glance | 1.32 | 80% | quay wall (22.0, 0.0)-(22.0, 10.8) wall_quay |
| squadron: escape.c14 | door from escape.c12 | 2,4 | 63.0 to 63.5 | window look | 2.30 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 2,4 | 64.0 to 69.5 | place stroll end | 2.28 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 2,4 | 70.0 to 80.0 | glance | 2.08 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 2,6,8 | 80.5 to 81.5 | stroll | 2.07 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 2,6,8 | 82.0 to 85.0 | place stroll end | 2.08 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 2 | 85.5 to 86.5 | glance | 2.13 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 4 | 80.5 to 85.0 | place stroll end | 2.27 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 4,6 | 85.5 to 87.0 | glance | 2.28 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 4,6 | 91.0 to 92.5 | glance | 2.08 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 4,8 | 93.0 to 97.5 | stroll | 2.05 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 4,8,10 | 98.0 to 101.5 | place stroll end | 2.13 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 4 | 102.0 to 107.5 | glance | 1.80 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 5 | 91.5 to 92.5 | glance | 1.77 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 5 | 93.0 to 93.5 | stroll | 1.68 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 5 | 94.0 to 101.5 | place stroll end | 1.67 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 5,6,8,10 | 102.0 to 108.0 | glance | 1.42 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 5,8 | 108.5 to 109.0 | place stroll end | 1.69 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 5,7 | 109.5 to 110.0 | window look | 1.88 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 6 | 79.0 to 80.0 | glance | 2.36 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 6 | 93.0 to 101.5 | place stroll end | 2.27 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 6,7,10 | 108.5 to 109.0 | stroll | 2.08 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 6 | 109.5 to 109.5 | window look | 2.30 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 7 | 103.0 to 108.0 | glance | 1.82 | 55% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 8 | 77.5 to 80.0 | glance | 2.15 | 75% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 8 | 85.5 to 92.5 | glance | 1.38 | 95% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 8,10 | 109.5 to 111.0 | window look | 0.91 | 75% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 8,10 | 126.0 to 127.5 | window look | 1.59 | 65% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| squadron: escape.c14 | door from escape.c12 | 10 | 93.5 to 97.5 | stroll | 2.07 | 75% | cell wall (0.0, -8.0)-(10.0, -8.0) wall_cell |
| ember: hollow.inn | door from hollow.ford | 2 | 79.5 to 80.0 | glance | 2.47 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 2 | 80.5 to 81.5 | stroll | 2.45 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 2 | 82.0 to 85.0 | place stroll end | 2.41 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 2 | 85.5 to 85.5 | glance | 2.44 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 2 | 104.5 to 105.5 | glance | 2.30 | 55% | o_inn wall (27.0, -18.0)-(23.0, -18.0) wall_inn_window |
| ember: hollow.inn | door from hollow.ford | 4 | 94.0 to 98.0 | stroll | 2.42 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 4,8 | 98.5 to 101.5 | place stroll end | 2.43 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 4 | 102.0 to 107.5 | glance | 2.17 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 5 | 93.0 to 93.5 | stroll | 2.42 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 5 | 94.0 to 101.5 | place stroll end | 2.40 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 5,8 | 102.0 to 108.0 | glance | 2.20 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 5 | 108.5 to 108.5 | place stroll end | 2.43 | 55% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 8 | 91.0 to 92.5 | glance | 2.10 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 8 | 93.0 to 98.0 | stroll | 1.40 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 8 | 108.5 to 109.0 | place stroll end | 1.40 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 8 | 109.5 to 110.5 | window look | 1.45 | 85% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 8,10 | 126.5 to 127.5 | window look | 1.41 | 95% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 10 | 107.0 to 108.0 | glance | 2.20 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 10 | 108.5 to 109.0 | stroll | 2.01 | 100% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: hollow.inn | door from hollow.ford | 10 | 109.5 to 110.0 | window look | 1.98 | 75% | o_inn wall (23.0, -18.0)-(12.0, -18.0) wall_inn |
| ember: marsh.stair | door from marsh.wall | all | 6.5 to 6.5 | glance | 1.45 | 65% | al_wall wall (2.5, -24.0)-(11.0, -24.0) wall_obsidian |

404 failing poses over 117 scene entries (step 0.50 beats).
<!-- /clearance:before -->
