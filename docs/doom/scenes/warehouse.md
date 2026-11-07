# Warehouse pilot scene (doom_warehouse): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Cobalt Warehouse Dance Floor-1.png` (secondary: `Midnight dance hall with three guides-1.png`).
Map: `content/story/maps/doom_warehouse.json`, an APPROXIMATE reconstruction of MAP07 Dead Simple: the tools agent's trace read from the ian-albert render (`tools/doom/trace/warehouse.json`,
a 2100 unit arena) plus the pilot's additions (`tools/doom/trace/warehouse_scene.py` writes `warehouse_pilot.json`). No WAD geometry exists (the supplied WAD has empty map lumps).

## What the reference shows

* The viewer stands on a steel-plated walkway outside the near corner of a **fenced square dance floor** seen along its diagonal, so the fence makes a V with its apex toward the viewer (about 4 m away). Wet floor, cobalt reflections, a drain grating along the fence.
* On the floor: a crowd of dancers (silhouettes, raised arms), a **raised central platform with a glowing equaliser cube**, and four **speaker plinths** (steel boxes with cones and amber floor lights) round it.
* Far side, centred: a **raised stage with steps and a rail**, the **Balcony guide** on it (white hair, long coat, red scarf, arm out): route ahead. Behind her a window onto a night city with a moon and a water tower.
* Left, near: the **bar** under a copper lamp (bottles, counter, taps, a plant, a flight case); the **Bar guide** leans on the counter in a waistcoat and beckons with an open palm: route left.
* Right, near: the **lounge** doorway with curtains, a lamp, a tufted sofa and a rug; the **Chill-out guide** in a mustard cardigan holds a patterned cushion and beckons: route right.
* Above: **steel trusses**, a cage of hanging **speaker stacks**, hanging pendant lamps, **blue spotlight shafts**, treble-clef **banners**, the glazed roof. Palette: cobalt, steel, copper and amber.

## The render's geometry, and how the reference maps onto it

The render shows (Doom units, 32 = 1 m, x east, y north): an outer terrace +96 (2100 across), a grey **stone ring** at 0 (1520 across, a 243 unit band), an inner **courtyard** (1034 square, guessed +32) with
**four square platforms** (210, +80) and a small **central pedestal** (163, +64), four dark slots in the ring (-96) and a room nub off the terrace's north-west. That is the painting's room almost directly:

| Reference element | Trace piece | Where |
| --- | --- | --- |
| Walkway round the floor (steel, wet) | `stone_ring`, 0 | the band round the courtyard; the viewer stands in its **south-west corner** |
| Fenced dance floor | `courtyard`, +32 (the render's guess): its 1 m ledge carries the renderer's **`railing` wall kind** all round (a see-through lattice strip, tile `wh_railing`, 1 m: the floor is seen through the fence; closed to walkers), with two gates (south x -400..-320, west y -120..-40), each a 0.5 m step island (`gate_step_s/w`) | centre |
| Four speaker plinths | `plat_n/e/w/s` (210 square, lowered to +48: 0.5 m over the floor, a step a walker can take) | one per quadrant |
| Lit cube | `pedestal` (+64), two stair strips on its south side (`ped_step_a/b`, 40 and 52) | centre |
| Stage (guide: ahead) | `stage` island in the courtyard, +68, two steps (`stage_step_a/b`, 0.375 m risers) on its WEST side | south-west part of the floor, 16 m from the reference viewpoint on the diagonal ahead |
| Bar (guide: left) | `bar`: a room cut out of the ring's west band, three solid walls, 5 m opening to the south (towards the viewer), floor +16 (a 0.5 m step), 4 m ceiling | west band, y -400..-200 |
| Lounge (guide: right) | `lounge`: a room cut out of the ring's south band, three solid walls, opening to the west, floor +12, 4 m ceiling | south band, x -540..-400 |
| Arrival | `wh_arrive`: the ring's south-west corner facing the floor (a cut, then a 3 bar walk to the reference viewpoint) | |

**Reference viewpoint** `wh_ref` (-620, -600), looking north-east: the courtyard's near corner is 4 m away and the V of the railing opens ahead. The bar guide stands at 41 degrees to the left (9.4 m), the lounge guide at 41 degrees to the right
(4.8 m), the stage guide dead ahead at 16 m (64 px tall at 16:9; `tests/test_doom_views.gd` requires 60).

**Exposure** (A1 night interior): the Doom lights are too low for this renderer, so every sector is lit at least 0.9 (`LIGHT_GAIN`, `LIGHT_FLOOR` in `tools/doom/author_warehouse.py`), tints are lifted towards white, the fog is cobalt (`#2f48ac`, 0.021) and 16 light things carry the colour (cobalt over the floor and the ring, amber in the bar and the lounge, a cool pool on the stage). `python -I tools/doom/frame_check.py docs/shots/doom/warehouse` prints the figures (before shrinking).

## What the render and the pilot still lack

* The railing is one strip per portal edge (no posts, no thickness; the lattice tile has its own posts every metre); the pits' rims in the ring (four -3 m slots) carry the same railing, each pit keeping one open rim on its far side (the map loader wants every piece reachable).
* The bar counter, taps, curtains and sofa are not modelled (one sofa billboard, pendants, truss towers, lights); the rooms are plain boxes.
* The stage is on the dance floor, not against a far wall as in the painting (the render's courtyard is 32 m across, the painting's room about a third of that); no window with the moon, banners, hanging speaker cage or light shafts.
* The terrace (+96) and the nub: no stairs; the render draws ramps (untraced).

Regenerate: see `docs/doom/LAUNCH.md`. Trace result: 22 Doom sectors, 72 convex pieces, 141 portals (6 blocked: the ledge), 0 unreachable; 9 pieces not on foot (the platforms and the terrace, on purpose).

## Heights, rail and the camera path (7 November)

* `max_step` 0.5 and `visibility` clip (72 pieces) are set in the map. Every portal whose floors differ by more than 0.5 m is shut to walkers (`blocked`) when the map stays reachable without it (the sides of the stage and pedestal stairs, the pits, the terrace); `tools/doom/author_warehouse.py` does this after every convert (`barriers`).
* Rail data (`tools/run/make_doom.py`): the stay loop is four places, each a `via` polyline move: the west band north of the bar (hold 2 bars), the pedestal (hold 2), against the south railing on the floor (hold 2), and back to `wh_ref`, a choice viewpoint (`"choice": true`, hold 8). `rail.routes` carries the other routes as moves: `up` (the walk to the stage: out past the lounge, through the south gate, up the west steps), `left`, `right`, `stumble`, `arrive`. Via points are the `wh_v_*` waypoints (corners only, never stood on).
* `check_rail_paths.gd` (and `StoryRailCheck.check_rail`, which now also checks `rail.routes`) reports 0 problems on the five Doom scenes.
* `python3 tools/doom/shoot_scene.py walk docs/shots/doom/warehouse` (or `RW_WALK=1` with shoot_scene.sh) writes `walk_ahead.jpg` and `walk_stay.jpg` (12 frames each along the move, the eye's real height; the pose tables and hold figures are in `walk_*.txt`).
