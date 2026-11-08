# Underworld scene (doom_underworld): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Three Paths Across the Basalt Abyss-4.png` (secondary: `Three Visitors in the Basalt Underworld-6.png`). Map: `content/story/maps/doom_underworld.json` (MAP29 The Living End), APPROXIMATE and **invented from the painting**:
the render trace of MAP29 (`tools/doom/trace/underworld.json`) gives a lava basin and a central rock mass with no way across (its `uncertain` says so), not a plateau with three ways on, so `tools/doom/trace/underworld_scene.py` builds the room from the painting
on a 0.25 m grid (`underworld_pilot.json`) and `tools/doom/author_underworld.py` dresses it. Routing from the Underworld: ahead Mothership, left Floor (Warehouse), right Dock.

## What the painting shows, and where it is in the map (metres, x east, y north)

| Painting | Map piece |
| --- | --- |
| Foreground basalt slabs with lava in the cracks, rock stumps, gong and drums | `plateau_s/_n/_w` (floor 0), `uw_floor_slab`; `uw_stub` billboards; `uw_gong`, `uw_drum` at the reference view's left edge; viewer at `uw_ref` (0, 1.6) looking north |
| Left rock wall with bone chimes, red cloth | solid west wall at x = -6.5; `uw_bones` decals, `uw_cloth`, a third drum by the wall |
| Blue-lit tunnel at the left, Floor guide at its mouth | `cave_mouth` + `cave` (rock roof 4.5 / 3.5 m, blue texture and pale blue lamps), guide at (-5.4, 7.2); threshold `uw_cave_in` (-10.5, 7) faces the lit tunnel decal `uw_tunnel` on the cave's end |
| Ledge climbing along the cliff to the tusk gate, Mothership guide | `ledge_1..4` (3.5 m wide, 0.375 m steps to +1.5), `gate_pad`, `causeway` to the tower; guide at (-3.7, 16.2) with `uw_tusks`; lantern posts `uw_post_a..d`; threshold `uw_gate` (-2.75, 22) |
| Stair up to a ledge under a patched tent, Dock guide in the green coat | `dstair_1..4` and `shelf` (+1.5): `uw_tent`, `uw_lantern`, `uw_crate`; guide at (8.5, 10.6); threshold `uw_shelf_end` (11, 12.6) faces north-east over the lava to the lit path `uw_passage` on the far cliff |
| Lava chasm between them | `abyss_00..05`: 5 m below the paths (floor -5), x -4.5 to 30, y 5.5 to 50, `void: true`, bright lava texture lit by a grid of lava lamps 0.6 m over it; the far cliffs 12 m with `uw_lavafall` decals, each fall lighting the cliff round it |
| Stepped tower with banners at the far side | `tstair_1..4` (+3 m), `tower_s/w/e` terrace, `ttop_1..4` to +5 m, `uw_pillar` billboards with red banners |
| Red cloud sky | the map's `sky` (`uw_sky`, cylinder, horizon 0.76): near black at the zenith, the lava's glow on the cloud bottoms and a far terraced range at the horizon; every piece but the cave is open to it |

The abyss is a void the player cannot enter: every portal between a walkable piece and an abyss piece is `kind: railing` (`uw_rail`: a low kerb of basalt stumps on a 0.9 m strip, see-through between the stones, `blocked: true`). One portal stays open (the loader demands every sector reachable through open portals): the tower's north rim at (6.0, 39.5), a dead end no route or waypoint goes near; the rail check refuses to step into a void.

Rail (`tools/run/make_doom_underworld.py`, merged by `make_doom.py`): stay loop = ledge view, cave view, stair view (each 2 bars still), then `uw_ref` (choice, 8 bars still). `rail.routes`: `up`, `left`, `right`, `stumble`, `arrive`. One scene `doom_underworld` (geography world, depth 2), routes straight to `doom_mothership` (up), `doom_warehouse` (left), `doom_dock` (right); three figure guide hotspots (no rings) and the stay hotspot.

## Light and exposure (stage D round 2)

The light is carried by practicals and emissives, not a flat lift: the walkable rock's ambient is 0.5 away from the lamps (`WALK_AMBIENT`, below the engine's 0.62); the lamps are pools (`LAMP_REACH` 1.35: warm yellow-amber lantern posts, the rim's lava glow, pale blue in the cave); the lava floor is emissive (white tint, a lava lamp every 6 m); each lava fall lights the far cliff round it (`uw_lt_fall_*`, `uw_lt_passage`); the haze is a thinner warm red (`#7a2210`, density 0.007). The basalt prism tiles (`columns` in `make_underworld_art.py`) have a 6 px deep seam and a lit, dithered edge per prism, so the walls keep their contrast at distance; the sky is near black at the zenith; the tunnel decal is lit. (The basalt tiles still carry round 1's texture lift, `LIFT` in the art script.)

`tools/doom/frame_check.py` (16:9 shots, world band): before this round (the state round 1 left) and after.

| shot | before p50 / p95-p5 | after p50 / p95-p5 |
| --- | --- | --- |
| ref | 0.25 / 0.37 | 0.27 / 0.47 |
| hold_ledge | 0.25 / 0.35 | 0.25 / 0.47 |
| hold_cave | 0.27 / 0.35 | 0.29 / 0.48 |
| hold_stair | 0.24 / 0.32 | 0.26 / 0.42 |
| route_ahead | 0.25 / 0.30 | 0.26 / 0.41 |
| route_left | 0.23 / 0.33 | 0.25 / 0.52 |
| route_right | 0.21 / 0.41 | 0.25 / 0.49 |
| arrive | 0.26 / 0.38 | 0.27 / 0.45 |
| all eight | 0.24 / 0.35 | 0.26 / 0.47 |

Every shot is inside the rule (p50 0.25 to 0.38, p95 - p5 over 0.40); hold_ledge, route_left and route_right sit on its lower edge (0.25). The painting itself measures p50 0.17, p95 - p5 0.31: it is darker than the rule.

## The guides (ruling 36)

| guide | source | at `uw_ref` (16:9, figure box height) |
| --- | --- | --- |
| Floor (left, braids, magenta top, silver trousers) | CROP from the Underworld painting (286 px tall there) | 169 px |
| Dock (right, green coat, yellow armband) | CROP from the Mothership painting (335 px there; the Underworld painting's figure is cut by rock and crates) | 134 px |
| Mothership (ahead, pale lilac figure, white crest, purple robe) | PROCEDURAL placeholder (78 px in the painting, under 180 px) toward the standard: warm and cool rims, dithered sequins | 82 px |

States are small edits of the one figure (available: a lamp-lit rim that breathes; selected: a brighter rim and the hand raised; committed: turned away). No ring or beacon. `tools/doom/art/make_underworld_guides.py`; sheet `docs/shots/doom/underworld/guides_sheet.png`.

## Shots (docs/shots/doom/underworld/)

`contact.jpg` (the painting beside `uw_ref`, then every viewpoint as a 16:9 | 20:9 pair, and `preview_pitch14`), `walk_strip.jpg` (three routes, six frames each; pose tables `walk_up.txt`, `walk_left.txt`, `walk_right.txt`), `guides_sheet.png`. Regenerate: `python3 tools/doom/shoot_underworld.py` (needs a window). `preview_pitch14` is `uw_ref` pitched down 14 degrees through `RW_STORY_CAM`: a preview of what the choice hold would show with a pitch, NOT what the run shows (see hooks); it measures p50 0.31, p95 - p5 0.44.

**What matches the painting:** cracked basalt slabs with lava in the cracks and the gong and drums in the left foreground; the bone chimes on the left wall; the blue cave with the Floor guide at its mouth; the ledge and tusk gate with the Mothership guide in the middle; the stair, tent and lantern with the Dock guide on the right; a lava chasm with lava falls on the far cliffs; a red cloud sky over the far side; banner pillars on the tower; warm practicals against the cave's blue; the basalt reads as prisms with dark seams and lit edges.

**What does not match:** the basalt is lilac-grey where the painting's is near black (lifted to meet the exposure rule, which the painting itself does not meet); the lava is a band seen past the rim, not the wide river and lake the painting looks down on (the run's choice hold cannot pitch; `preview_pitch14` shows what a pitch gives); the tower is a terrace, a stair and billboard pillars, not nested rings with sheer columns; the far cliffs are a tiled terraced texture, not modelled terraces; the cave's tunnel is a decal at a dead end; the kerb stones on the rim are not in the painting (the abyss must be shut); the Mothership guide is far and small (82 px) and procedural; the cave roof is the cave floor's stone tile.

## Placeholders and hooks

Placeholders: every texture, prop and decal (`tools/doom/art/make_underworld_art.py`), the Mothership guide (procedural), the music (Warehouse arrangements). The two cropped guides are cut from the owner's paintings.
Hooks (engine, not changed here): (1) the run's choice hold carries no pitch (`RunJourney.window_face` emits a `player_look` with `face` and no pitch field), so the choice viewpoint cannot look down into the lava as the painting does; (2) StoryMap's `void_top` is the LOWEST neighbouring floor, so a void split into rectangles has `void_top` equal to its own floor and the engine's void haze is off (the abyss is lit by its lava lamps instead).

Regenerate: `python -I tools/doom/trace/underworld_scene.py; python -I tools/doom/convert.py --scene underworld --trace tools/doom/trace/underworld_pilot.json; python -I tools/doom/art/make_underworld_art.py; python -I tools/doom/art/make_underworld_guides.py; python -I tools/doom/author_underworld.py`, then `--import` (see `docs/doom/LAUNCH.md`).
