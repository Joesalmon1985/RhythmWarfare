# Copper Bar (doom_bar): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Copper Basement Bar, Three Hidden Routes-3.png`. Map: `content/story/maps/doom_bar.json` (MAP02 Underhalls, APPROXIMATE). Pipeline as the Warehouse's
(`docs/doom/scenes/warehouse.md`): `tools/doom/trace/bar_scene.py` (trace) -> `convert.py --scene bar --trace tools/doom/trace/bar_pilot.json` -> `tools/doom/author_bar.py` (waypoints, textures, decals, things, lights, cast).
Art: `tools/doom/art/make_bar_art.py` (tiles, decals, props) and `make_bar_guides.py` (guides), into `assets/story/doom_bar/textures/`. Rebuild line: `docs/doom/LAUNCH.md`.

## What the reference shows

* The viewer stands at the south end of a **brick passage**, wet purple-blue cobbles, copper pipes along the ceiling, a pillar of pipe with crates at its foot, a **treble-clef tapestry** and a lantern on the left wall.
* Ahead, **four stairs up** to a raised **DJ booth** behind a desk, windowed, racks glowing: the Booth guide (teal hair, headphones, orange jacket) beckons: route ahead.
* Left, at a doorway in a blue-lit space under ivy: the **Floor guide** (braids, hoops, magenta sequin top, silver trousers): route left, back to the Floor.
* Right, beyond a **drain channel** crossed by iron grates: the **bar nook**, a step up, a red tufted sofa, tapestries and the Chill-out guide (mustard cardigan, glasses) beckoning; in the foreground a curved copper counter, bottles, taps, a red stool, pendant cage lamps: route right.

## The trace, and why it is not cut from the render

MAP02's render (`tools/doom/trace/bar.json`: a nukage channel loop, a plateau, plazas, 2400 units) is a hall complex and holds nothing like a 10 m passage. `bar_scene.py` therefore keeps MAP02's ideas (the drain channel with crossings,
brown brick rooms, short stairs) and lays them out as the painting shows them, as 20 non-overlapping rectangles (metres, edges split at every neighbour's corner). NOTHING is read from the render or the WAD; it is flagged in `uncertain`.

| Reference element | Sectors | Floor (m) |
| --- | --- | --- |
| Passage, cobbles | `pass` (3.2 x 9.2 m) | 0 |
| Way to the Floor (left) | `way_w` (5.2 x 2.7, ends at the blue door) | 0 |
| Four stairs | `stair_1..4` (0.4 m deep, 0.3 m risers) | 0.3 .. 1.2 |
| Booth landing, desk, booth | `booth`, `desk` (+1 m, blocked: a solid desk), `booth_back` | 1.5, 2.5, 1.5 |
| Drain channel, two grated crossings | `chan_a/b/c` (-1 m), `bridge_1/2` (0, grate floor) | -1 / 0 |
| Bar, counter, stools | `bar_w`, `bar_back`, `bar_e`, `bar_front`, `counter` (an island, +1 m, blocked) | 0.3 / 1.3 |
| Chill-out nook (right) | `lounge_n` (0.4 m up, sofa, tapestries, curtain) | 0.4 |

**Heights.** `max_step` 0.5 (the largest open step is 0.4). Every drop over 0.5 m is shut to walkers (`blocked`) while the map stays reachable (the channel, the counter and the booth behind the desk each keep one open portal, the farthest, a dead end no
route uses). The channel's long banks (passage, stairs, landing, nook) carry the renderer's `railing` wall kind (copper lattice, `bar_railing`, 1 m); the sides of the two grates are open drops without a rail (the painting has none). `visibility` is `clip`.
**Exposure**: sector light 1.0 throughout (floor 0.66, gain 2), tints lifted 0.7, violet-brown haze (`#3a2448`, 0.032; stage D lifted it from `#2a1838`), 15 practical lights (warm pendants and lanterns, teal over the water, blue in the Floor way, red and teal in the booth; radius x1.7 since stage D) plus the three guide lamps; wet cobbles, channel and grates (sector `wet`: the weather engine's gloss of the practicals, a dry map).
**Decals** (25, kind `decal`): tapestries, posters, copper pipes, ivy, three signs (pictograms: headphones, note, sofa), the back-bar shelf, the booth window and racks, the blue Floor door, the curtain, two lanterns. Billboards: pendants, taps, bottles, stools, crates, jug, the downpipes and the Floor guide's post (cut from the painting), the foreground stool and counter (cut from the painting), sofa.

## Camera, routes, guides

* **Reference viewpoint** `wb_ref` (0.1, -0.5), yaw 0 (north): the stairs ahead, the Floor guide 37 degrees left (3.9 m, 241 px at 16:9), the Chill-out guide 34 degrees right (7.4 m, 140 px; clear of the foreground counter since stage D), the Booth guide dead ahead (11.7 m, 71 px; the test needs 60).
* **Arrival** `wb_arrive`: the west end of the way from the Floor (you came in that way), a 3 bar walk to `wb_ref`.
* **Stay loop** (`good`, polyline moves with holds): the first grate crossing `wb_bridge` (hold 2), the counter `wb_counter` (2), the way to the Floor `wb_way` (2), back to `wb_ref` (choice viewpoint, `"choice": true`, 8 bars).
* **Routes** (`rail.routes`): `up` through the stair foot to `wb_booth_door` (on the landing, 2.1 m from the desk guide), `left` through `wb_v_jamb` to `wb_floor_door`, `right` onto the first grate to `wb_chill_door` (held a step back from the Chill-out guide in round 1), `stumble`, `arrive`. `check_rail_paths`: 0 problems.
* **Guides**: `wb_guide_booth/floor/chill`, 1.8 m, 256 px sheets (idle 1, available 5, selected 2, committed 2). Hotspot rows `doom_bar.exit_*` declare `show: {archetype: figure, light: wb_lamp_<who>}` (A7): the figure beckons when available, leans in when touched, gestures when committed, and the lamp over it brightens; no ring.
* **Worlds**: the Bar is the geography world `doom_bar` (depth 2), one scene, entered from the Warehouse's left guide; its guides lead straight to `doom_booth` (up), `doom_warehouse` (left) and `doom_lounge` (right) (H1.6; see LAUNCH.md and `tests/test_doom_cuts.gd`).

## Stage D polish (7 and 8 November): the painting beside the reference viewpoint

Round 1 (7 November): dark mossy stone in three variants, wet violet cobbles, copper mains in the ceiling tile, a lighter water tile; the red stool and the copper counter with its whisky glass cut from the painting as foreground billboards; the Floor guide cropped from the painting.

Round 2 (8 November). The five biggest differences at `wb_ref` beside `Copper Basement Bar, Three Hidden Routes-3.png` (shot before changing anything), and what was done:

1. **The Chill-out guide was hidden** behind the foreground counter cut (it stood at 31 degrees, the guide at 34). The counter now stands at 47 degrees (`(1.45, 0.75)`): the guide stands clear beyond it, as the painting has him beyond the counter's end.
2. **Night One patrons crowded the nook** (four figures round the sofa; the painting has none there). The cast's homes are all at the bar now, outside the reference picture at 16:9 and 20:9.
3. **The ceiling's copper mains ran across the passage as glowing bars**; the painting's run along it. The tile is turned (one main per 2 m, along the passage) and its copper dimmed a step. They still read brighter than the painting's.
4. **The pipe column was a flat drawn plank.** Both downpipes are now the painting's riveted copper downpipe, cut from it (`bar_p_pipe`).
5. **The floor was dry and the channel invisible.** Wet cobbles, channel and grates (gloss of the lanterns and pendants); the bridge hold turned off the channel's end wall to look up the channel into the nook.

Also: the Floor guide's hand rested on nothing; the painting's stone post she leans on is cut from it (`bar_p_post`) and stands under her hand. A second lantern on the passage's west wall and a pendant over the stair foot, each with a pool; the stone palette a notch lighter.

Measured exposure (16:9, `frame_check.py` on the `RW_KEEP` frames of `shoot_bar.py`, table in `frame_check.txt`): before (quick shots of the round-1 build) ref p50 0.24 / contrast 0.46, chill threshold 0.25 / 0.44.
After, 21 shots: ALL p50 **0.26**, contrast **0.39** (p5 0.12, p95 0.51); inside the rule per shot: hold_counter, rail_0, rail_1, rail_3 (4 of 21). The rest have p50 0.23 to 0.28 with contrast 0.31 to 0.40: the walks up to the booth and left to the Floor
are the darkest (stone walls and the booth's racks, no bright practical in frame). The ALL contrast is 0.01 under the rule and fell from the round-1 ref figure: the counter cut no longer fills the right of the reference frame with its lit copper.
The painting itself measures p50 0.14, contrast 0.32: the rule asks for a brighter frame than the painting.

Guides: the Floor guide is a CROP from this painting (420 px tall in it); the Chill-out guide is the Warehouse's lounge CROP (`Midnight dance hall with three guides-1.png`, the same man); the Booth guide is PROCEDURAL (the painting shows her about 90 px tall, too small to crop): a PLACEHOLDER below the sprite standard (blocky face). No ring or beacon under any guide.

## What matches, and what does not

MATCHES (`contact_bar.jpg`): the long stone passage under a timber ceiling with copper mains along it, the stairs rising to a lit, windowed booth with racks and a teal-haired guide behind a desk; the riveted copper downpipe with crates and a jug at the left; the treble-clef tapestry and lantern;
the ivy; the Floor guide leaning on her post in the blue-lit way; the copper counter with the whisky glass and lanterns in the right foreground and, beyond it, the Chill-out guide by the red sofa, teal curtain and tapestries of the nook; the copper-lattice rail along the channel; warm lamps against a violet ambience.

DOES NOT MATCH:
* The channel water is still hardly seen from `wb_ref` (behind the bank and rail); the gloss on the wet cobbles is faint (the engine's fake highlight).
* The Booth guide is small at `wb_ref` (11.7 m) and procedural; the Chill-out guide stands (the painting seats him on the sofa).
* The passage is straight and 3.2 m wide (the painting's is wider, the Floor opening nearer); the mains are a ceiling tile, not geometry, and read as glowing.
* The `left` walk passes the Floor guide within 1 m (she fills the frame's edge); `wb_way` stares at the blue door across a bare wall.
* The patrons at the bar are the Night One figures, not bar people.
* 17 of 21 shots are outside the exposure rule (above).

## Shots (8 November, `docs/shots/doom/bar/`)

`contact_bar.jpg` (one sheet, 848 KB: the painting, the reference viewpoint, the three stay holds, the stumble, the rail camera at four song times, and the three route walks in four frames each, at 16:9 and 20:9),
`walk_stay.jpg` / `walk_ahead.jpg` (12-frame strips with pose tables `walk_*.txt`), `frame_check.txt` (the exposure table), `guides_sheet.png`, `art_sheet.png`. What matches and what does not: the section above.

## Placeholders and not done

Placeholders: every texture, decal and prop (procedural, or cut from the painting), the Booth guide (procedural), the cast, the music (the Warehouse's arrangement `warehouse_1`). Not done: curved counter, reflections beyond the engine's gloss, ceiling mains as geometry, water movement, per-scene music, the guides' loop playback beyond the frames (engine).
