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
| Fenced dance floor | `courtyard`, lowered to **+16** (0.5 m up, from the render's guessed +32); its four edges are the **fence** (impassable lines), two gates (south x -400..-320, west y -120..-40) | centre |
| Four speaker plinths | `plat_n/e/w/s` (210 square, +80: 2 m over the floor) | one per quadrant |
| Lit cube | `pedestal` (+64), two stair strips on its south side (`ped_step_a/b`, 28 and 40) | centre |
| Stage (guide: ahead) | `stage` island, +60, two steps (`stage_step_a/b`) on its south side | the ring's north-east corner, on the diagonal ahead |
| Bar (guide: left) | `bar` island, +24, 4 m canopy | the ring's west band, y -400..-200 |
| Lounge (guide: right) | `lounge` island, +12, 4 m canopy | the ring's south band, x -540..-400 |
| Arrival | `wh_arrive`, the ring's north-west corner (the nub is not connected: no stairs were traced) | |

**Reference viewpoint** `wh_ref` (-650, -600), looking north-east: the courtyard's near corner is 4 m away and the V of the fence opens ahead. The bar guide stands at 45 degrees to the left (9.4 m), the lounge guide at 45 degrees to the right
(5.6 m), the stage guide dead ahead at 45 m.

## What the render and the pilot still lack

* **Railings**: the fence is impassable lines at a 0.5 m ledge, not a railing (the renderer extension adds railings for blocked portals).
* The islands have no side walls: the bar and lounge are raised floors under a low canopy, open on all sides (a hole's edges are portals). The bar counter, taps, curtains and sofa are not modelled (one sofa billboard, pendants, truss towers, lights).
* The stage is 45 m from the reference viewpoint (the painting's is about 20 m): its guide is a 20 px figure at the reference view. The painting's room is about a third the size of the render's.
* The terrace (+96) and the nub: no stairs; the render draws ramps (untraced).
* The window with the moon, the banners, the hanging speaker cage, the spotlight shafts: textures and things still to draw.

Regenerate: see `docs/doom/LAUNCH.md`. Trace result: 20 Doom sectors, 67 convex pieces, 138 portals (6 blocked: the fence), 0 unreachable; 9 pieces not on foot (the platforms and the terrace, on purpose).
