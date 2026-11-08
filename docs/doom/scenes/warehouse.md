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

**Reference viewpoint** `wh_ref` (-620, -600), looking north-east: the courtyard's near corner is 4 m away and the V of the railing opens ahead. The bar guide stands at 41 degrees to the left (9.4 m), the lounge guide to the right
(5.4 m since stage D), the stage guide dead ahead at 16 m (64 px tall at 16:9; `tests/test_doom_views.gd` requires 60).

**Exposure** (A1 night interior): every sector is lit 1.0 (`LIGHT_GAIN`, `LIGHT_FLOOR` in `tools/doom/author_warehouse.py`), tints are lifted towards white, the haze is cobalt (`#3654b8`, 0.021; stage D lifted it from `#2f48ac`).
The light is carried by practicals: 42 light things plus the three guide lamps (cobalt over the floor and the ring, amber in the bar and the lounge, a cool pool and a warm key on the stage, amber floor lights at the plinths, an amber pool under every
walkway pendant and every wall lantern), 10 emissive walkway and stage pendants and 12 caged wall lanterns along the terrace riser (both cut from the painting: `wh_p_pendant`, `wh_p_sconce`), nine additive spotlight shafts, and a wet
walkway and dance floor (sector `wet`: the weather engine's gloss of the practicals, on a dry map). `python -I tools/doom/frame_check.py docs/shots/doom/warehouse` prints the figures (before shrinking); `frame_check.txt` keeps them.

## Stage D polish (7 and 8 November)

Round 1 (7 November, committed then): the Warehouse's own 256 px tiles (`tools/doom/art/make_warehouse_art.py`: riveted steel and brick walls in three variants each, wet steel walkway, LED dance floor, velvet, roof), the riveted steel half-wall
railing with a copper top rail, props cut from the painting (banners, hanging speakers, back bar, counter, copper lamp, the stage window onto the night city, the lounge lamp and pelmet), a 0.5 m steel plate under `wh_ref`, the crowd on the
near half of the floor with a sightline lane to the stage, and the three guides cropped from `Midnight dance hall with three guides-1.png`.

Round 2 (8 November), the exposure rule. Before (17 shots at 16:9): ALL p50 **0.26**, contrast **0.42**, 8 of 17 shots inside the rule (p50 0.25 to 0.38 and p95 - p5 over 0.40 per shot). The off shots were the threshold holds and the
views across the floor into the hall's far walls, which the cobalt haze flattened to one mid-blue with nothing bright in them. Done, with practicals rather than a flat ambient: the walkway pendants and wall lanterns with their amber pools
(see above), five more spotlight shafts (the painting has six or more) and brighter shafts, a wet walkway and floor, steel, walkway and dance tiles a notch lighter (more and larger LED dots), the haze a notch lighter.
After: ALL p50 **0.27**, contrast **0.51** (p5 0.13, p95 0.64); **13 of 17** shots inside the rule. Still off: `approach_bar_b` (p50 0.26, contrast 0.38), `approach_stage_c` (0.27 / 0.35), `stay_2` (0.28 / 0.35), `stumble` (0.28 / 0.38):
p50 in range, contrast short (no bright practical in those frames). The painting itself measures p50 0.17, contrast 0.33: the rule asks for a brighter frame than the painting.

Also: the lounge guide stands 0.5 m deeper in the lounge (`(-448, -604)`), so from the raised plate his feet clear the pad strip (`test_doom_views.gd` failed two checks on it after round 1).

Guides: all three are CROPS from `Midnight dance hall with three guides-1.png` (`tools/doom/art/make_guides.py` `CROPS`, `crop_guide`); below the painting's cut the legs (and the stage guide's coat to the knee) are continued from the
painting's own pixels (`continue_down`). No ring or beacon under any guide.

## What matches the painting, and what does not

MATCHES (`ref_16x9.jpg` / `ref_20x9.jpg` beside the painting): the fenced dance floor seen along its diagonal with the steel half-wall's V toward the viewer and a copper top rail; the wet cobalt floor with LED dots; the crowd on the floor;
the blue spotlight shafts and hanging amber pendants; the stage ahead with the white-haired guide before a window onto the night city; the bar on the left under copper lamps, its back shelves glowing, the waistcoated guide behind the counter;
the lounge on the right with velvet curtains, a fringed lamp and the cardigan guide with his cushion; cobalt against amber throughout.

DOES NOT MATCH:
* The room is far larger than the painting's (the render's courtyard is 32 m across, the painting's room about a third of that): the stage stands on the dance floor 16 m away, not against a far wall, and the stage guide is small (64 px at 16:9; the test asks 60).
* No raised central platform with the glowing equaliser cube in the picture from `wh_ref` (the pedestal is there, the crowd screens it); no steel trusses overhead in the picture, no glazed roof, no treble-clef banners in view from `wh_ref`.
* The bar and lounge are seen through flat door openings (the painting shows them as open bays); the bar counter is two flat cut halves that read as panels from `wh_bar_door`.
* The railing is one strip per portal edge (no posts or thickness beyond the tile's own); the drain grating along the fence is not visible.
* The wet floor's gloss is faint (the engine's fake highlight, `GLOSS_K`); the painting's cobalt reflections are much stronger.
* 4 of 17 shots are under the contrast rule (above).

## Placeholders, and what the render and the pilot still lack

* Every tile and prop is placeholder art (drawn in code or cut from the painting); the crowd is the Night One cast.
* The bar counter, taps, curtains and sofa are billboards and decals; the rooms are plain boxes.
* The terrace (+96) and the nub: no stairs; the render draws ramps (untraced).

Regenerate: see `docs/doom/LAUNCH.md`. Trace result: 22 Doom sectors, 72 convex pieces, 141 portals (6 blocked: the ledge), 0 unreachable; 9 pieces not on foot (the platforms and the terrace, on purpose).

## Heights, rail and the camera path (7 November)

* `max_step` 0.5 and `visibility` clip (72 pieces) are set in the map. Every portal whose floors differ by more than 0.5 m is shut to walkers (`blocked`) when the map stays reachable without it (the sides of the stage and pedestal stairs, the pits, the terrace); `tools/doom/author_warehouse.py` does this after every convert (`barriers`).
* Rail data (`tools/run/make_doom.py`): the stay loop is four places, each a `via` polyline move: the west band north of the bar (hold 2 bars), the pedestal (hold 2), against the south railing on the floor (hold 2), and back to `wh_ref`, a choice viewpoint (`"choice": true`, hold 8). `rail.routes` carries the other routes as moves: `up` (the walk to the stage: out past the lounge, through the south gate, up the west steps), `left`, `right`, `stumble`, `arrive`. Via points are the `wh_v_*` waypoints (corners only, never stood on).
* `check_rail_paths.gd` (and `StoryRailCheck.check_rail`, which now also checks `rail.routes`) reports 0 problems on the Doom scenes. The Warehouse is one geography scene (`doom_warehouse`, depth 1): its guides lead straight to `doom_balcony` (up), `doom_bar` (left), `doom_lounge` (right); no stand-ins.
* `python3 tools/doom/shoot_scene.py walk docs/shots/doom/warehouse` (or `RW_WALK=1` with shoot_scene.sh) writes `walk_ahead.jpg` and `walk_stay.jpg` (12 frames each along the move, the eye's real height; the pose tables and hold figures are in `walk_*.txt`).
