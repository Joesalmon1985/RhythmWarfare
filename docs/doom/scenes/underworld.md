# Underworld scene (doom_underworld): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Three Paths Across the Basalt Abyss-4.png` (secondary: `Three Visitors in the Basalt Underworld-6.png`). Map: `content/story/maps/doom_underworld.json` (MAP29 The Living End), APPROXIMATE and **invented from the painting**:
the render trace of MAP29 (`tools/doom/trace/underworld.json`) gives a lava basin and a central rock mass with no way across (its `uncertain` says so), not a plateau with three ways on, so `tools/doom/trace/underworld_scene.py` builds the room from the painting
on a 0.25 m grid (`underworld_pilot.json`) and `tools/doom/author_underworld.py` dresses it. Routing from the Underworld: ahead Mothership, left Floor (Warehouse), right Dock.

## What the painting shows, and where it is in the map (metres, x east, y north)

| Painting | Map piece |
| --- | --- |
| Foreground basalt slabs with lava in the cracks, rock stumps, gong and drums | `plateau_s/_se/_ss/_n/_w` (floor 0) round `plateau_dais` (+0.5 m, x -0.5 to 2.5, y -1 to 3: the viewer's raised outcrop at the rim), `uw_floor_slab`; `uw_stub` billboards; `uw_gong`, `uw_drum` at the reference view's left edge; viewer at `uw_ref` (1.0, 0.6) on the dais looking north (yaw 8), the run's choice hold pitched -14 |
| Left rock wall with bone chimes, red cloth | solid west wall at x = -6.5 (12 m; the east side, stair and shelf, stands 6 m so the sky shows over it); `uw_bones` decals, `uw_cloth`, a third drum by the wall |
| Blue-lit tunnel at the left, Floor guide at its mouth | `cave_mouth` + `cave` (rock roof 4.5 / 3.5 m, dark basalt catching the blue lamps, a lava-cracked path), then `cave_deep` (round 2: a narrower, lower passage 4 m on, 2.75 m roof: depth), guide at (-5.4, 7.2); threshold `uw_cave_in` (-10.5, 7) looks down the passage to its dark far end (`uw_tunnel`: a tunnel mouth in near black, one lantern, a lava crack along the path) and the lantern `uw_cave_lantern` at its frame |
| Ledge climbing along the cliff to the tusk gate, Mothership guide | `ledge_1..4` (3.5 m wide, 0.375 m steps to +1.5), `gate_pad`, `causeway` to the tower; guide at (-3.5, 14.2) with `uw_tusks` (round 2: 2 m nearer, 95 px); lantern posts `uw_post_a..i`; threshold `uw_gate` (-2.75, 22) |
| Stair up to a ledge under a patched tent, Dock guide in the green coat | `dstair_1..4` and `shelf` (+1.5): `uw_tent`, `uw_lantern`, `uw_crate`; guide at (8.5, 10.6); threshold `uw_shelf_end` (11, 12.6) faces north-east over the lava to the lit path `uw_passage` on the far cliff |
| Lava chasm between them | `abyss_00..08`: 3 m below the paths (floor -3), x -4.5 to 30, y 5.5 to 50 plus the POCKET below the dais (x -1 to 5, y 3 to 5.5), `void: true`, ceiling 2 m (sky; its lips `sky`, not drawn), so the far cliffs stand 5 m over the lava and the red sky shows above them; the lava lit by a lamp grid 2 m over it and the far cliffs' feet by `uw_lt_farglow_*`; `lavashore` (x 5 to 7, y 39.5 to 40.5, behind the tower) is the lake at its own level and NOT a void (see the hooks) |
| Stepped tower with banners at the far side | `tstair_1..4` (+3 m), `tower_s/w/e` terrace, `ttop_1..4` to +5 m, `uw_pillar` billboards with red banners |
| Red cloud sky | the map's `sky` (`uw_sky`, cylinder, horizon 0.76): near black at the zenith, the lava's glow on the cloud bottoms and a far terraced range at the horizon; every piece but the cave is open to it |

The abyss is a void the player cannot enter: every portal between a walkable piece and an abyss piece is `kind: railing` (`uw_rail`: a low kerb of basalt stumps on a 0.9 m strip, see-through between the stones, `blocked: true`). One portal stays open (the loader demands every sector reachable through open portals): the tower's north rim at (6.0, 39.5) onto the lava shore, a dead end no route or waypoint goes near; the rail check refuses to step into a void or down a drop.

Rail (`tools/run/make_doom_underworld.py`, merged by `make_doom.py`): stay loop = ledge view (2 bars, 1 still), then `uw_ref` (choice, 8 bars still, `pitch` -14). Round 2: the rail steps one place per passed block and the choice hold is set at block 2 only if the rail stands at the choice place; with round 1's four places the camera was still walking to the stair view when the window opened (seen on the real run), so the loop is one reveal and the choice viewpoint; the cave and stair views stay as waypoints and shots, not run holds. `rail.routes`: `up`, `left`, `right`, `stumble`, `arrive`. One scene `doom_underworld` (geography world, depth 2), routes straight to `doom_mothership` (up), `doom_warehouse` (left), `doom_dock` (right); three figure guide hotspots (no rings) and the stay hotspot.

## Light and exposure (stage D polish round 2)

Round 1's lilac came from two lifts: the basalt tiles drawn 1.6 to 1.7 times lighter (`LIFT`) and every sector tint pushed 55 % toward white (`TINT_LIFT`). Both are gone (the tiles
keep no lift; `TINT_LIFT` 0.15, warm tints). The basalt (`basalt()` in `make_underworld_art.py`) is warm near-black prisms: irregular column widths across a 256 px tile, staggered
block breaks, a dithered lit face and a deep shadowed face, thin lava cracks; three variants on the rock walls (`uw_wall_rock`, `_b`, `_c`, cycled per wall) and three on the cliffs into
the lava (`uw_wall_abyss`, `_b`, `_c`). The light on it is the lava's: a warm lamp every 3 m along every rim, 0.6 m under the walkway's edge (`RIM_*`, 40 lamps, lighting the walkway
only), the lake's lamp grid 2 m over the lava, the far cliffs' feet (`FAR_*`), the lanterns (posts `uw_post_a..i`). The lava (`floor_lava_r2`) is an orange melt under dark crust rafts with
thin bright flow lines, unhazed (the shore, below). The sky keeps a lift graded toward the horizon (the zenith stays near black); its far terraces are near-black rock with lit ledges.

The basalt is lighter than the painting's (the painting measures p50 0.17, contrast 0.31, its rock 0.11 to 0.15): the exposure rule wants every shot's median at 0.25 or more, so the
rock is drawn at about the painting's lit faces (mean 0.2 to 0.23 in the tile) and lit warm. It is warm grey-brown now, not lilac.

`tools/doom/frame_check.py` per 16:9 shot (world band), p50 / p95 - p5. Before = this branch at the start of round 2 (round 1's state with the engine hooks merged); after = the final shots.

| shot | before | after | rule |
| --- | --- | --- | --- |
| ref (the run's choice hold, pitch -14) | 0.25 / 0.41 (off: p50 just under 0.25) | 0.29 / 0.48 | ok |
| hold_ledge (the stay loop's reveal) | 0.24 / 0.46 (off) | 0.29 / 0.41 | ok |
| hold_cave (a view) | 0.29 / 0.48 | 0.28 / 0.46 | ok |
| hold_stair (a view) | 0.25 / 0.42 (off: p50 just under 0.25) | 0.28 / 0.42 | ok |
| route_ahead | 0.26 / 0.42 | 0.27 / 0.41 | ok |
| route_left | 0.25 / 0.52 | 0.28 / 0.44 | ok |
| route_right | 0.22 / 0.35 (off) | 0.26 / 0.51 | ok |
| arrive | 0.26 / 0.42 | 0.29 / 0.43 | ok |
| all eight | 0.25 / 0.45 | 0.28 / 0.45 | 8 of 8 in the rule (4 of 8 before) |

The guide-state captures (not in the eight): selected 0.31 / 0.47, committed 0.31 / 0.52.

## The guides (ruling 36)

| guide | source | at `uw_ref`, the pitched choice hold (16:9, figure box height, `test_doom_views`) |
| --- | --- | --- |
| Floor (left, braids, magenta top, silver trousers) | CROP from the Underworld painting (286 px tall there) | 138 px |
| Dock (right, green coat, yellow armband) | CROP from the Mothership painting (335 px there) | 136 px |
| Mothership (ahead, pale lilac figure, white crest, purple robe) | PROCEDURAL placeholder (78 px in this painting; the one large view of her, `Three Visitors in the Basalt Underworld-6.png`, cuts her at the hips behind the cliffs, so a crop would be a torso) | 95 px (was 82: she stands 2 m nearer, at the tusks on the gate pad) |

The three are 60 px or more, apart, clear of the HUD corner and above the pads at the pitched pose (the test now applies the rail place's `pitch` to the pose). No ring or beacon.

## Shots (docs/shots/doom/underworld/)

`contact.jpg`: the painting beside `ref` (the run's choice hold: `uw_ref` pitched -14), every viewpoint at 16:9 | 20:9, and the guide-state pair (`selected`: the run's own camera just
after the Mothership guide is tapped at beat 50 of the window; `committed`: the first frame of the walk-off). `walk_strip.jpg` and `walk_up/left/right.txt` (the three routes),
`guides_sheet.png`. Regenerate: `python3 tools/doom/shoot_underworld.py` (needs a window); `RW_KEEP=<dir>` keeps the full-size frames for `frame_check.py`.

Walk legs (ruling 42 is not in this branch; lengths from the map's waypoints): up 22.9 m, left 13.6 m, right 21.9 m (was 22.7), all under 33 m.

**What matches the painting:** the choice view looks down across the abyss from a raised slab at the rim: the lava runs away below between the ledge (left) and the stair (right) to the
tower, the red sky over the far cliffs; dark warm basalt prisms lit orange from the lava; cracked slabs with lava in the cracks, the gong and drums in the left foreground; the bone
chimes; the cave mouth with the Floor guide; the ledge and tusk gate with the Mothership guide; the stair, tent and lantern with the Dock guide; lava falls on the far cliffs; banner
pillars on the tower.

**What does not match:** the lava is a river 6 m wide between the paths' cliffs, not the wide lake the painting looks down on (the ledge and the stair close it in; it fills the lower
centre of the reference shot, not the whole lower half); the rock is lighter than the painting's (the exposure rule); the tower is a terrace and billboard pillars, not nested rings; the
far side is a 5 m cliff and the sky's painted terraces, not modelled terraces; the cave is still blue-violet on its walls (the painting's cave is blue-lit, but our walls read lilac in
`hold_cave` / `route_left`); the rim kerb stones are not in the painting; the Mothership guide is procedural and the smallest (95 px).

## The lead's list (round 2)

- [x] Lilac corridors to near-black basalt over a lava lake under a red sky: `pitch` -14 authored on `uw_ref` (`tools/run/make_doom_underworld.py`), the viewer on a dais at the rim with the abyss brought to it (the pocket), the abyss 3 m deep with a 2 m sky ceiling so the far side is cliffs and sky; the lava fills the lower centre (a river, not a lake: see above).
- [x] Basalt near-black with lava rim light from below; the stripe tile's repeat: no lift, warm dark prisms, three variants per surface, rim lamps along every edge.
- [x] The blue tunnel decal and the striped arch tunnel: `cave_deep` gives the tunnel real depth, its far end a dark tunnel mouth with one lantern and a lava crack along the path; no blue stripes.
- [x] `hold_ledge`, `route_left`, `route_right` on the rule's lower edge: all eight shots now inside (table above).
- [ ] The Mothership guide: carried procedural (no full-length view of her in any painting); nearer, 95 px (was 82).
- [x] Round 1's flat lift on the basalt tiles: removed.
- [x] Added: the choice window was not at `uw_ref` on the real run (four stay places); the loop is now one reveal and the choice viewpoint.
- [x] Added: selected and committed guide-state captures in the contact sheet.

## Placeholders and hooks

Placeholders: every texture, prop and decal (`tools/doom/art/make_underworld_art.py`), the Mothership guide (procedural), the music (Warehouse arrangements). The two cropped guides are cut from the owner's paintings.

Hooks and engine notes (engine not changed here): (1) the `pitch` hook works: the choice hold looks down -14 through the window; after a tap the camera turns toward the tapped guide
and the walk-off starts at once (the `selected` capture shows the turned view, not the pitched framing). (2) `void_top` over the connected group puts the depth haze on the whole
abyss, and that haze (a multiplier toward 30 % of the fog colour) turns the lava dark red; the scene opts out with the LAVA SHORE (`lavashore`, a 2 x 1 m piece of the lake behind
the tower at the lava's level, not a void): the group's lowest rim floor is then the lava itself and the haze is zero. A per-void "no haze" or "glow" key would say this directly.
(3) The rail steps one place per passed block, so a choice viewpoint must be at most the second place of a stay loop to be reached by the window (the round 1 loops of other scenes
with four places may have the same problem: worth checking on the real run).

Regenerate: `python -I tools/doom/trace/underworld_scene.py; python -I tools/doom/convert.py --scene underworld --trace tools/doom/trace/underworld_pilot.json; python -I tools/doom/art/make_underworld_art.py; python -I tools/doom/art/make_underworld_guides.py; python -I tools/doom/author_underworld.py; python tools/run/make_doom.py`, then `--import` (see `docs/doom/LAUNCH.md`).
