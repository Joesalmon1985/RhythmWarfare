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
**Exposure**: sector light at least 0.66 (the Warehouse uses 0.9: the bar is meant darker), tints lifted 0.7, violet-brown fog (`#2a1838`, 0.032), 13 practical lights (warm pendants and lanterns, teal over the water, blue in the Floor way, red and teal in the booth).
**Decals** (24, kind `decal`): tapestries, posters, copper pipes, ivy, three signs (pictograms: headphones, note, sofa), the back-bar shelf, the booth window and racks, the blue Floor door, the curtain. Billboards: pendants, taps, bottles, stools, crates, jug, pipe columns, sofa.

## Camera, routes, guides

* **Reference viewpoint** `wb_ref` (0.1, -0.5), yaw 0 (north): the stairs ahead, the Floor guide 37 degrees left (3.9 m, 241 px at 16:9), the Chill-out guide 34 degrees right (7.4 m, 140 px), the Booth guide dead ahead (11.7 m, 71 px; the test needs 60).
* **Arrival** `wb_arrive`: the west end of the way from the Floor (you came in that way), a 3 bar walk to `wb_ref`.
* **Stay loop** (`good`, polyline moves with holds): the first grate crossing `wb_bridge` (hold 2), the counter `wb_counter` (2), the way to the Floor `wb_way` (2), back to `wb_ref` (choice viewpoint, `"choice": true`, 8 bars).
* **Routes** (`rail.routes`): `up` through the stair foot to `wb_booth_door` (on the landing, 2.1 m from the desk guide), `left` through `wb_v_jamb` to `wb_floor_door`, `right` across the first grate to `wb_chill_door` (1.6 m from the Chill-out guide), `stumble`, `arrive`. `check_rail_paths`: 0 problems.
* **Guides**: `wb_guide_booth/floor/chill`, 1.8 m, 256 px sheets (idle 1, available 5, selected 2, committed 2). Hotspot rows `doom_bar.exit_*` declare `show: {archetype: figure, light: wb_lamp_<who>}` (A7): the figure beckons when available, leans in when touched, gestures when committed, and the lamp over it brightens; no ring.
* **Worlds**: the Bar is the world `doom_bar` (depth 2), entered from the Warehouse's exit scene; the guides lead to in-world stand-ins (`doom_bar.booth/floor/chill`) that loop back through `doom_bar.return`. The real cut to the Booth, the Floor and the Chill-out waits for hook H1.6 (see LAUNCH.md).

## Shots (`docs/shots/doom/bar/`)

`contact_bar.jpg` (one sheet, 790 KB: the painting, the reference viewpoint, the three stay holds, the stumble, the rail camera at four song times, and the three route walks in four frames each, all at 16:9 and 20:9),
`walk_stay.jpg` / `walk_ahead.jpg` (12-frame strips with pose tables `walk_*.txt`; holds move 0.003 m), `guides_sheet.png`, `art_sheet.png`. Read by eye:

What matches the painting: the long brick passage under timber and copper-pipe ceiling with the stairs rising to a lit, windowed booth with racks and a teal-haired guide behind a desk; the copper pillar with crates and a jug at the left; the treble-clef tapestry and lantern on the left wall; the ivy at the top left;
the blue-lit Floor way with its guide; the red sofa, teal curtain, tapestry and stools of the nook at the right; the copper-lattice rail along the channel; the back-bar shelves of bottles and the taps along the counter; warm lamp light against a violet ambience; the three guides in the picture, apart, at human scale.

What does not: the cobbles are purple but not wet-blue with warm reflections; the brick is one even orange where the painting is dark, mossy and stained; the **channel water is hardly visible** from the reference viewpoint (the bank and rail hide it, and it is dark: the painting shows it glittering between the grates);
the counter is not in the foreground as in the painting (it lies at 56 degrees, just outside the 16:9 picture; the first view of it is the `wb_counter` hold); the passage is straight and 3 m wide, the painting's is wider with the Floor opening nearer; the pipes along the ceiling are a texture, not the thick riveted mains;
the guides' faces are weak and their poses stiff (placeholders, well below `art/reference/standard/guide_floor_sprite_standard.png`); the Floor guide is passed within 1 m on the `left` walk and the Chill-out guide ends 1.6 m away (large in frame); at `wb_bridge` the view up the channel is mostly brick wall; the patrons are the Night One figures, not bar people; the red stool is the only foreground prop.

## Placeholders and not done

Placeholders: every texture, decal and prop (procedural), the three guides, the cast, the music (the Warehouse's arrangement `warehouse_1`). Not done: curved counter, wet reflections, ceiling mains as geometry, water movement, the Floor/Booth/Chill-out transitions (H1.6), per-scene music, the guides' loop playback beyond the frames (engine).
