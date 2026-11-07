# Warehouse pilot scene (doom_warehouse): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Cobalt Warehouse Dance Floor-1.png` (secondary: `Midnight dance hall with three guides-1.png`).
Map: `content/story/maps/doom_warehouse.json`, an APPROXIMATE trace of MAP07 (second pass, 7 November): no real geometry exists (the supplied WAD has empty map lumps).

## What the reference shows

* The viewer stands on a steel-plated circulation walkway outside the near corner of a **fenced square dance floor** seen along its diagonal, so the fence makes a V with its apex towards the viewer (about 4 m away). Wet floor, cobalt reflections, a drain grating along the fence.
* On the floor: a crowd of dancers (silhouettes, raised arms), a **raised central platform with a glowing equaliser cube**, and four **speaker plinths** (steel boxes with cones and amber floor lights) round it.
* Far side, centred: a **raised stage with steps and a rail**, the **Balcony guide** on it (white hair, long coat, red scarf, arm out): route ahead. Behind her a window onto a night city with a moon and a water tower.
* Left, near: the **bar** under a copper lamp (bottles, counter, taps, a plant, a flight case); the **Bar guide** leans on the counter in a waistcoat and beckons with an open palm: route left.
* Right, near: the **lounge** doorway with curtains, a lamp, a tufted sofa and a rug; the **Chill-out guide** in a mustard cardigan holds a patterned cushion and beckons: route right.
* Above: **steel trusses**, a cage of hanging **speaker stacks**, hanging pendant lamps, **blue spotlight shafts**, treble-clef **banners**, and the glazed roof. Palette: cobalt, steel, copper and amber.

## Mapping onto the trace (Doom units, 32 = 1 m; x east, y north; the viewer looks north)

| Reference element | Trace piece | Where |
| --- | --- | --- |
| Circulation walkway (floor 0, wet steel) | sector `arena_floor`: a 1000 unit square minus the diamond | all round the floor |
| Fenced dance floor | `dance_floor`, a diamond (half diagonal 280, centre (0, 40)) at -16 (0.5 m down), 6 of its 8 edges impassable (the fence), 2 gates (SE and SW edges) | centre |
| Raised platform with the cube | `platform` +32 with stair arms `platform_step_s` / `_n` (+8) | centre of the diamond |
| Speaker plinths | `plinth0..3` (50 units square, +56) | round the platform |
| Stage | `stage` +60, `stage_step_a` +20, `stage_step_b` +40 | north wall, centred, x -200..200 |
| Bar | `bar` alcove 200 x 260 units, ceiling 4 m, warm | west wall, y 40..300 |
| Lounge | `lounge` alcove, floor +12 | east wall, y 40..300 |
| Arrival | `arrival_corridor` and `arrival_room` | north-west corner, invented |

**Reference viewpoint** (`wh_ref`): (0, -380) in Doom units (about 4.4 m from the apex of the fence), yaw 0, looking north along the diagonal axis. Stage ahead (distance about 24 m), bar and lounge at about 40 degrees left and right.

## What the traced map lacks (and so what the scene still needs)

* **Fence geometry**: the fence is only impassable lines at equal height; the renderer shows a 0.5 m ledge, not a railing (the renderer agent adds railings for blocked portals).
* Crowd (dancers on the floor), the cube, hanging speakers, trusses as geometry, banners, spotlight shafts, the window with the moon: textures and things, not map pieces.
* Real MAP07 proportions, rim, raised areas and exits (all uncertain, listed in `doom.uncertain` in the map JSON).
* Bar counter, curtains, sofa: small props (things) to place; the alcoves are plain rooms for now.

Regenerate: `python -I tools/doom/trace/make_traces.py`, `python -I tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse.json`, `python tools/doom/author_warehouse.py` (waypoints, textures, things; run after every convert), `python -I tools/doom/check_world.py content/story/maps/doom_warehouse.json`.
Trace result: 16 Doom sectors, 50 convex pieces, 93 portals (6 blocked), 0 unreachable, 4 pieces off foot (the plinths, on purpose).
