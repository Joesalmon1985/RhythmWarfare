# Balcony scene (doom_balcony): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Rainy industrial rooftop, three musical paths-8.png`. Map: `content/story/maps/doom_balcony.json` (MAP15 Industrial Zone), APPROXIMATE and **invented from the painting**:
the render trace of MAP15 (`tools/doom/trace/balcony.json`) is a grass plateau, a lake and brown towers: no rooftop, no ledges, no bridges (its own `uncertain` says so). So
`tools/doom/trace/balcony_scene.py` builds the place from the painting on a 0.25 m grid (`balcony_pilot.json`) and `tools/doom/author_balcony.py` dresses it. Routing from the Balcony: ahead Mothership, left Floor, right Booth.

## What the reference shows, and where it is in the map (metres, x east, y north)

| Painting | Map piece |
| --- | --- |
| Wet diamond-plate roof deck, puddles with magenta/cyan/red reflections, flight cases and cable at the right | `deck` 7 x 9 m, `bc_floor_wet` (puddles baked into the tile), case and cable billboards |
| Brick wall on the left with a lamp and pink equalizer graffiti, iron stair running down, the Floor guide at the rail on the landing | `landing` and five 0.375 m treads `s_a..s_e` (west of the deck, behind a railing), brick walls, `bc_dc_eq_*` decals, lamp billboard; guide at (-5.2, 7.2); threshold `bc_stair_foot` |
| Control cabin on the right, lit window with violet equalizer light, open door, Booth guide (teal hair, orange jacket) in it | `bdoor` and `cabin` (amber lit, racks), window decal on the deck's east wall; guide at (5.6, 7.0); threshold `bc_cabin_in` |
| Bridge over the drop to a tower with a white lace dome, the Mothership guide on it, far | three 1 m steps `b_a..b_c`, `bridge` and `isle`, lace decal; guide at (0.25, 17.5); threshold `bc_bridge_end` |
| Rusty railings along every open edge | `kind: railing` walls (`bc_rail`, 1.1 m) on the deck, stair, bridge and platform edges (all blocked to walkers) |
| The city, far roofs, towers, the yard with forklift and blue-lit shutters far below | four **voids** (`vw1 vw2 ve1 ve2`, 9 m deep) with tower billboards, skyline/window/shutter decals, a forklift and cases; fog `#0e1626` |

Reference viewpoint `bc_ref` (0.5, 1.9) looks north (choice viewpoint, 8 bars still). In the 460 px stage strip the guides are 73 px (Mothership, 15.5 m), 191 px (Floor) and 208 px (Booth) at 16:9 and 20:9 alike
(`tests/test_doom_views.gd`, balcony block: 60 px minimum, inside the picture, apart, clear of the HUD, sightline clear of solid walls).

Rail (`tools/run/make_doom_balcony.py`, merged by `make_doom.py`): stay loop = bridge view, stair view, cabin view (each 2 bars still, via polylines), then `bc_ref` (choice, 8 bars). `rail.routes`: `up` (deck, three bridge steps, to the bridge end),
`left` (deck, landing, down the five treads), `right` (deck, through the cabin door), `stumble`, `arrive`. World `doom_balcony` (depth 2): entry `doom_balcony`, stand-ins `doom_balcony.mothership/.floor/.booth`, exit scene
`doom_balcony.return`. Data for the real cut: threshold = `to` of each route move, doorway = `rail.exits[dir]`, labels name the destinations.

## Shots (docs/shots/doom/balcony/)

`contact.jpg` (the painting beside `bc_ref`, then every viewpoint as a 16:9 | 20:9 pair) and `walk_strip.jpg` (three routes, six frames each; pose tables `walk_up.txt`, `walk_left.txt`, `walk_right.txt`). Regenerate: `python3 tools/doom/shoot_balcony.py`.
frame_check over the shots: p50 0.08, p95-p5 0.37: **under-exposed** (target p50 0.25 to 0.38); the rooftop is darker than the painting.

**What matches the painting:** the three guides at three ways off the roof (brick-stair landing left, lit cabin door right, the bridge and lace dome ahead), the red brick wall with pink equalizer graffiti, the railed stair, the amber cabin, the violet window,
railings on every edge, the dark drop with towers and red lamps beyond, a wet blue-grey night palette.

**What does not:** no rain, no moon, no puddle reflections that move (floor tile only), no cloud sky (a flat storm ceiling); the far buildings are billboards and decals, not geometry, so there is no stepped skyline and no high walkway on the right; the deck is a plain
rectangle (no pipes along the cabin wall, no roof parapet); the stair is a straight run of five treads (the painting's turns); the Night One crowd stands on the deck and in the cabin and crowds the middle of the reference view (the painting is empty); the Mothership
guide is small (73 px). All figures and art are procedural placeholders.

## Placeholders and not done

Placeholders: every texture, prop, decal and the three guides (`tools/doom/art/make_balcony_art.py`, `make_balcony_guides.py`; the Floor guide is the Lounge's sprite set, the Mothership guide the Booth's, the Booth guide a recolour); the stand-in destinations; the music
(Warehouse arrangements). Two plain drops (`isle` to `vw2`, `isle` to `ve2`) stay open without a railing because the loader needs every void joined to the map by one open portal. The Warehouse's stand-in for this scene was renamed `doom_warehouse.balcony`
(`doom_balcony` is now this world's entry); `doom_warehouse.return` offers no route to `doom_balcony` (its `up` is "Round again"): reach it with `--scene doom_balcony`. Hook needed (no `src/` change made): H1.6 to route the threshold waypoints into the other worlds.

Regenerate: see `docs/doom/LAUNCH.md` (balcony block).
