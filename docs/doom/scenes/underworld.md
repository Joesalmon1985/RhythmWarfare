# Underworld scene (doom_underworld): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Three Paths Across the Basalt Abyss-4.png` (secondary: `Three Visitors in the Basalt Underworld-6.png`). Map: `content/story/maps/doom_underworld.json` (MAP29 The Living End), APPROXIMATE and **invented from the painting**:
the render trace of MAP29 (`tools/doom/trace/underworld.json`) gives a lava basin and a central rock mass with no way across (its `uncertain` says so), not a plateau with three ways on, so `tools/doom/trace/underworld_scene.py` builds the room from the painting
on a 0.25 m grid (`underworld_pilot.json`) and `tools/doom/author_underworld.py` dresses it. Routing from the Underworld: ahead Mothership, left Floor, right Dock.

## What the painting shows, and where it is in the map (metres, x east, y north)

| Painting | Map piece |
| --- | --- |
| Foreground basalt slabs with lava in the cracks, rock stumps | `plateau_s/_n/_w` (floor 0), floor texture `uw_floor_slab`, `uw_stub` billboards; viewer at `uw_ref` (0, 1.6) looking north |
| Left rock wall with bone chimes, gong, drums, red cloth | solid west wall at x = -6.5; `uw_bones` decals, `uw_gong`, `uw_drum`, `uw_cloth` billboards |
| Blue-lit tunnel at the left, Floor guide at its mouth | `cave_mouth` + `cave` (ceiling 4.5 / 3.5 m, blue texture and light), guide at (-5.4, 7.2), threshold `uw_cave_in` (-10.5, 7) |
| Ledge climbing along the cliff to the tusk gate, Mothership guide | `ledge_1..4` (3.5 m wide, 0.375 m steps every 2 m to +1.5), `gate_pad`, `causeway` over the abyss to the tower; guide at (-3.7, 16.2) with `uw_tusks`; threshold `uw_gate` (-2.75, 22) |
| Stair up to a ledge under a patched tent, Dock guide in the green coat | `dstair_1..4` (0.375 m risers) and `shelf` (+1.5): `uw_tent`, `uw_lantern`, `uw_crate`; guide at (6.5, 10.6); threshold `uw_shelf_end` (9.5, 13.5) |
| Lava chasm between them | `abyss_00..05`: 4 m below the paths, `void: true`, bright lava texture, red fog and lights, `uw_lavafall` decals on the far walls |
| Stepped tower with banners at the far side | `tstair_1..4` (+3 m), `tower_s/w/e` terrace, `ttop_1..4` small stair to +5 m, `uw_pillar` billboards with red banners |

The abyss is a void the player cannot enter: every portal between a walkable piece and an abyss piece is `kind: railing` (`uw_rail`, a chain strip 0.9 m, `blocked: true`). One portal stays open: the map loader requires every sector reachable through open portals, so the
abyss keeps the one farthest from the origin (the tower's north rim at (6.0, 35.5), a dead end no route or waypoint goes near; the engine's rail check refuses to step into a void). The west cliff wall stands directly against the ledge and the tower (no abyss strip there: it would be a second closed void needing a second open portal).

Reference viewpoint `uw_ref` looks north (choice viewpoint, 8 bars still). The plateau's north edge is only 3.9 m from it so that the lava shows beyond the rim (a viewer at eye height cannot see a floor 14 m down from 10 m back: tried first and rejected, the abyss floor was 14 m down and invisible).
Guides at the reference viewpoint, 460 px stage strip (16:9 and 20:9 alike in height): Mothership 84 px (13.9 m), Floor 184 px, Dock 121 px (`tests/test_doom_views.gd`, underworld block: requires 60 px, inside the picture, apart, clear of the HUD, a sightline free of solid walls).

Rail (`tools/run/make_doom_underworld.py`, merged by `make_doom.py`): stay loop = ledge view, cave view, stair view (each 2 bars still, via polylines), then `uw_ref` (choice, 8 bars). `rail.routes`: `up` (plateau, ledge, past the Mothership guide, causeway), `left`, `right`, `stumble`, `arrive`.
One scene `doom_underworld` (geography world, depth 2), its routes straight to `doom_mothership` (up), `doom_warehouse` (left), `doom_dock` (right); three guide hotspots (figure staging, no rings) and the stay hotspot. The thresholds are the `to` of each route move and `rail.exits`.

## Shots (docs/shots/doom/underworld/)

`contact.jpg` (the painting beside `uw_ref`, then every viewpoint as a 16:9 | 20:9 pair), `walk_strip.jpg` (three routes, six frames each; pose tables in `walk_*.txt`), `guides_sheet.png`. Regenerate: `python3 tools/doom/shoot_underworld.py`.

**What matches the painting:** a plateau of cracked basalt with lava glowing in the cracks, the blue cave with the Floor guide at its mouth on the left, the ledge climbing to the Mothership guide and tusk gate in the middle, the stair and tent with the Dock guide on the right, a lava patch between with chain rails, red banner pillars on a tower terrace, a red haze.

**What does not:** the lava is a small patch in the gap between ledge and stair, not the wide river and lake of the painting (the engine camera cannot look down; see above); the abyss is 4 m deep, not a vast chasm, and the tower is a terrace and a four-step stair with billboard pillars, not nested rings with sheer columns; the far wall is a flat red cliff texture; there is no red cloud sky (a ceiling texture at 22 m); the cave is a dead end (walking left ends facing its wall); the railings are not in the painting (the brief wants the abyss shut); the Mothership guide is far and small; the walls are flat tiles, no hexagonal column relief; exposure is dark (frame_check over all shots: p50 0.17, p95-p5 0.30, against the 0.25 to 0.38 target: sector light is already 1.0).

## Placeholders and not done

Placeholders: every texture, prop, decal and the three guides (`tools/doom/art/make_underworld_art.py`, `make_underworld_guides.py`; floor and dock are the Lounge's drawings, the Mothership guide the Booth's violet variant recoloured); the music (Warehouse arrangements). Not done: no state-driven guide animation beyond the sprite per state; no `src/` hook was needed. A camera pitch on a waypoint or place would let the choice viewpoint look down into the abyss as the painting does.

Regenerate: see `docs/doom/LAUNCH.md` (underworld block).
