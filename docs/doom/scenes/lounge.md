# Chill-out Lounge scene (doom_lounge): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Mustard octagonal lounge of three routes-2.png` (secondary: `Mustard lounge with three new paths-5.png`). Map: `content/story/maps/doom_lounge.json`, an APPROXIMATE
reconstruction of MAP08 Tricks and Traps: the central octagonal hub read from the render trace (`tools/doom/trace/lounge.json`, 510 units across, sunken middle) plus everything the painting needs
(`tools/doom/trace/lounge_scene.py` writes `lounge_pilot.json`). No WAD geometry exists. Rebuild: `docs/doom/LAUNCH.md`. Result: 27 Doom sectors, 93 convex pieces, 168 portals (7 shut to walkers: the sofa-back
sides and the bar counter), 0 unreachable.

## What the painting shows, and where it is in the map

| Painting | Map (names are stable: the Magic rave borrows this geography) |
| --- | --- |
| Octagonal hall, tall beamed ceiling with a gold coffer | `concourse` (the walkway ring, floor 0, ceiling 5.5 m, texture `ceil_beam`), `step_ring` and the pit under a 7 m dome |
| Sunken conversation pit, two shallow steps down, a curved mustard tufted sofa, a rug of concentric octagons, a low octagonal table with a glowing mushroom lamp and red flowers | `step_ring` (-0.375 m), `back_n/back_s` (sofa backs), `seat_n/seat_s` (seats, -0.31 m), `gap_e/gap_w` (the pit stairs, east and west), rug bands `rug_rim`, `rug_stripe_a`, `rug_mid`, `rug_stripe_b`, `rug_in` (-0.75 m), `table`; billboards `lg_lamp_table`, `lg_vase`, `lg_cushion_*` |
| Ahead: a doorway up three steps onto a rain-slick street, the broad bald **Dock guide** in a long green coat with an armband | N face: `ahead_step_a/b` (two 0.25 m steps), `ahead_street` (cool grey-blue light, wet floor); guide `lg_guide_dock`; threshold `lg_ahead_door` |
| Left: the copper-tiled bar counter, bottle shelves, a record on the wall, the **Bar guide** in a waistcoat with open palm | NW face: `left_vest`, `left_bar`, `left_counter` (1.1 m island); decals `lg_bottles`, `lg_vinyl`; guide `lg_guide_bar`; threshold `lg_bar_door` |
| Right: a curving blue-lit glass passage with a rail, the **Floor guide** (braids, magenta sequin top, silver trousers, hand on hip) | NE face: `right_vest`, `right_passage` (cobalt deck, glass walls, cobalt light); guide `lg_guide_floor`; threshold `lg_floor_door` |
| Stone pilasters with brass sconces and gold studded acoustic panels between the doorways; palms in copper pots; curtains and bead curtains | the octagon's solid wall segments carry decals `lg_sc_*` (emissive sconces), `lg_studs_*` (studded panels); `lg_plant_*` billboards; five curtained niches `niche_e/w/s/se/sw` (velvet walls, `lg_beads_*` decals) |

The octagon is the render's hub (the brief's "eight doors" are its eight faces here: three open, five curtained). The render's big rooms radiating from the hub are not built.

**Reference viewpoint** `lg_ref` (0, -196 Doom units; 0, 6.1 m): the south walkway behind the near sofa, looking north. The Dock guide is dead ahead 16 m away, the Bar guide 26 degrees left (the NW arch), the Floor
guide 29 degrees right (the NE passage): all three stand inside their openings on clear sightlines (`test_lounge_each_guide_is_seen_...`). At 16:9 (460 px stage strip) they are 66, 72 and 86 px tall; the test asks 60.

**Exposure** (A1 night interior): sector lights 0.8 to 1.0 (`LIGHT_FLOOR` and per-sector values in `tools/doom/author_lounge.py`), tints lifted towards white 72 %, brown fog `#2a1608` (0.016), 13 light things: amber lamps
over the pit and at the four diagonals, a table lamp, and a cool pool beyond each doorway (grey-blue rain, amber bar, cobalt passage). `python -I tools/doom/frame_check.py <dir>` on the shots: p50 0.24 to 0.33,
crushed 0 %, blown 0.1 %.

## The camera (rail data: `tools/run/make_doom_lounge.py`)

* Stay loop (via polylines with holds, round the ring of walkway at inradius 6.1 m, via points `lg_v_*`): west reveal `lg_west` (hold 2 bars), north reveal `lg_north` under the Dock door (2), east reveal `lg_east` looking back across the pit (2), then `lg_ref`, the choice viewpoint (`"choice": true`, hold 8, still).
* `rail.routes`: `up` (ahead: round the east side and up the two steps to `lg_ahead_door`), `left` (west side to `lg_bar_door`), `right` (east side to `lg_floor_door`), each ending with a 1 bar hold; `stumble`, `arrive` (from the blue passage mouth `lg_arrive`).
* `check_rail_paths`: 0 problems on all ten Doom scenes (the lounge's five and the Warehouse's five). The doorway thresholds are where the world transition happens; the walks are checked as data, the engine still jumps from the threshold to the next scene's arrival (same limit as the Warehouse).

## Placeholders, and what does not match the painting

* The three guides are PLACEHOLDER procedural sprites (160 x 256, dithered capsule limbs), below `art/reference/standard/guide_floor_sprite_standard.png` (a painted portrait): costumes, colours and silhouettes follow the painting, faces and hands do not. The Bar guide is the Warehouse's `bar` set, shared.
* All textures and props (`tools/doom/art/make_lounge_art.py`) are placeholder pixel art made procedurally; the painting's richness (reflective marble, tufted leather grain, copper gleam, volumetric rain) is not reached.
* Geometry is simpler: flat walls (no arched lintels, fat pilasters or the octagonal beam ribs of the ceiling, only a ceiling texture with gold inlay lines), no hanging vines, no curved sofa (octagonal rings stand in), no ceiling coffer glow, the bar counter is a straight block, the passage to the Floor is a straight box (no curving glass bridge with a rail), the street is a straight alley.
* The painting's viewpoint is much closer (the near sofa and cushions fill the foreground, the Floor guide is 3 m away and large); here the camera is 6 m back so that all three guides are legible at 16:9 and 20:9. There is no foreground sofa; the near sofa back is a low ledge.
* No crowd (the painting has none; the world's story has an empty cast).
* The concourse is 2.8 m wide (the painting's feels wider) and the pit has no E/W sofa ends.
* Doors do not open and guides do not move beyond the existing choice staging (see `LAUNCH.md` limits).

## Hooks wanted (nothing in `src/` was touched)

* A route out of a world only through the world's exit scene: the lounge is its own world and the Warehouse reaches it through `doom_warehouse.return` (route `right`), not straight from the chill-out stand-in. A direct Floor-to-lounge route needs either the run graph to allow cross-world routes from a doom scene or both scenes to share a world with a per-scene map.
* The walks to the thresholds (`rail.routes`) are not played by the run yet.

## Shots (7 November, `docs/shots/doom/lounge/`)

`contact_lounge.jpg` (690 KB: the painting, then the reference viewpoint, the three reveals, the arrival, the three thresholds, the stumble and the stay loop at four song times, each at 16:9 and 20:9), `walk_strip.jpg` (380 KB: ahead, left, right and the stay loop, 6 frames each at the eye's real height, 1.57 to 1.60 m over the floor throughout), `walk_*.txt` (pose tables; every hold moves the camera 0.003 m and turns it 0 degrees: still), `art_sheet.png` and `guides_sheet.png` (the placeholder art).

Read by eye against the painting. MATCHES: the composition from the south walkway (sunken octagonal pit with mustard tufted sofa ring, striped octagonal rug, low table with a glowing lamp and flowers), three openings with a guide in each (the Dock guide in the green coat in the rain street straight ahead, the Bar guide in his waistcoat with bottle shelves and a record behind the copper counter on the left, the Floor guide in magenta and silver in the cobalt glass passage on the right), brass sconces and gold studded panels on the stone pilasters, palms in copper pots, velvet curtains, warm amber with a cool pool beyond each door; the guides stay in frame and apart at 20:9; the pads are never covered. DOES NOT MATCH: see the placeholder list above (the camera is much further back, no foreground sofa and cushion, flat stone walls without arches and ribbed octagonal ceiling, the rug reads orange rather than oxblood, guides are small procedural figures and the Dock and Floor guides stand in the doorways at 16 m and 15 m, the passage and the street are straight boxes). At the thresholds the guide fills the frame and the pad strip covers her waist (the pads, not the picture, sit there).
