# Doom II geometry to StoryMap: conversion record (7 November 2026)

Tools in `tools/doom/` (Python 3, standard library only): `wad.py` (reader), `geom.py` (exact integer geometry), `convert.py`
(WAD map to StoryMap JSON), `check_world.py` (validator), `render_plan.py` (plan PNG), `check_doom_map.gd` (Godot load check),
`scenes.json` (scene table), `test_doom.py` (tests), `convert_all.sh` (everything).

## Status: the supplied WAD holds no map geometry

`C:\Users\joesa\rw-audio-work\doom\doom2.wad` (identical bytes, SHA-256 `eaaeda05...da08b1b`, to `doom II wads\doom2.wad`) is an IWAD with
3342 lumps and 4,945,006 bytes. All 32 map markers (MAP01 to MAP32) are present, but **every map's VERTEXES, LINEDEFS, SIDEDEFS and
SECTORS lump is 0 bytes** (also SEGS, NODES, REJECT, and every THINGS except one of 2030 bytes). The textures (PLAYPAL, TEXTURE1,
PNAMES) and some sound and music lumps are present; the level data was removed. A genuine `doom2.wad` is about 14.6 MB.

| Map | VERTEXES | LINEDEFS | SIDEDEFS | SECTORS |
| --- | --- | --- | --- | --- |
| MAP02, MAP04, MAP07, MAP08, MAP11, MAP13, MAP15, MAP29 | 0 B | 0 B | 0 B | 0 B |

So **no real map can be converted from this file**: `python tools/doom/wad.py` prints the report, and `convert.py` stops with
`map MAP07 lacks VERTEXES, LINEDEFS, SIDEDEFS, SECTORS`. The conversion chain is built and tested on a synthetic WAD; it needs a
complete `doom2.wad` (or Freedoom's `freedoom2.wad`, which has different maps, or the owner's Steam/GOG `DOOM2.WAD`) at
`RW_DOOM_WAD`. Then `bash tools/doom/convert_all.sh` produces everything below. No approximate reconstruction was made here.

## Conventions (all explicit, all in `convert.py`)

| Quantity | Choice | Why |
| --- | --- | --- |
| Horizontal scale | 32 Doom units = 1 m (`UNITS_PER_M`) | a 64 unit texture is 2 m; a 128 wide corridor is 4 m; Doom's 24 unit step is 0.75 m |
| Vertical scale | 32 Doom units = 1 m times `--vscale` (default 1.0) | the player is 56 units = 1.75 m; a 72 unit door is 2.25 m; 128 ceilings are 4 m. Doom's 1.2 vertical aspect is a screen-pixel effect, not a geometry one; pass `--vscale 1.2` to exaggerate heights if a scene wants more drama |
| Eye height | StoryMap's `eye_height` 1.6 m, `units_per_m` 1 (the output is in metres) | Doom's own eye (41 units) would be 1.28 m at this scale, too low for the rail camera; the maps of the project all use 1.6 |
| Axes | `x_m = x / 32`, `z_m = -y / 32` | Doom north (+y) becomes StoryMap -z, which is "ahead" at yaw 0, so a plan view has the same top as the ian-albert renders and nothing is mirrored |
| Yaw | `yaw = doom_angle - 90` degrees | Doom 0 is east, 90 is north; StoryMap yaw 0 looks toward -z (north) and a positive yaw turns left |
| Polygon winding | counter-clockwise in StoryMap's (x, z) shoelace sense (positive `_signed_area`) | the flip mirrors orientation, so Doom's counter-clockwise rings are reversed after it; `check_world.py` errors on clockwise |
| Heights | `floor`/`ceiling` = Doom value `/ 32 * vscale` m, no offset | relative heights stay exact (steps, drops, plinths) |
| Light | `0.2 + 0.7 * light / 255` | StoryMap light is 0..1 |
| Textures | placeholders: `floor_grate`, `floor_bridge`, `floor_airlock` (by a hash of the Doom flat name), `ceil_hull`, `wall_hull`, `trim` (steps), `sky` ceilings for `F_SKY1`; art folder `mothership` | all exist in `assets/story/mothership/textures`, so maps load with no new art; the art agents replace the ids per scene. The Doom flat names are kept in `doom.sector_map` (names only, no Doom art) |

## Method

1. **Rings.** Per Doom sector, every linedef side that faces it gives a directed edge with the sector on its left (right sidedef:
   `v2 -> v1`; left sidedef: `v1 -> v2`). Linedefs with the same sector on both sides are ignored. Edges are chained into closed rings; at
   a pinch vertex the sharpest left turn is taken. Positive-area rings are outers, negative-area rings are holes (pillars, islands),
   each hole belongs to the smallest outer that contains it. Open chains (a broken sector) are recorded in `doom.broken_sectors`.
2. **Decomposition into convex pieces**, all in exact integer Doom coordinates (so shared edges are bit-identical): holes are bridged into
   their outer ring, the ring is ear-clipped (a colinear vertex is never an ear tip, so a vertex that a neighbour shares is never lost and
   no T-junction crack appears), then Hertel-Mehlhorn merges triangles across diagonals while the result stays convex. The area of the
   pieces must equal the area of the sector or the sector is recorded in `doom.dropped_unbuildable_sectors`.
3. **Ids and the sector map.** Pieces are `"<doom sector>_<n>"`. `doom.sector_map` maps every Doom sector to its piece ids with its original
   floor, ceiling, light, flats, special and tag (in Doom units).
4. **Portals.** Every polygon edge shared by exactly two pieces is declared once as a portal wall (`sector` = lower id, `portal` = other),
   including the diagonals between pieces of one Doom sector; an edge with one owner is left to StoryMap's default solid wall. A portal gets
   `lower_tex`/`upper_tex` `trim` where the floors or ceilings differ. So walls exist exactly where the Doom map has a one-sided line,
   and steps and drops exist where neighbouring heights differ.
5. **Blocked portals** (`"blocked": true`, StoryMap does not path through them): a line with Doom's *impassable* flag (railings, windows) or an
   opening lower than 1.2 m. Steps and drops are **not** blocked; `check_world.py` reports them (steps over 0.6 m, ledges over 0.75 m).
6. **Tiny sectors** (area under 0.05 m2, control sectors, trim) are dropped and listed in `doom.dropped_tiny`; their edges become walls.
7. **Closed doors** (ceiling equals floor) are opened to the tallest neighbouring ceiling (`doom.doors_opened`).
8. **Reachability.** StoryMap rejects a map with a sector unreachable from the start, so pieces not reachable through unblocked portals are
   pruned (`doom.dropped_unreachable_pieces`: closets, secret rooms behind windows).
9. **Start waypoint** `doom_start`: the Player 1 start (thing 1) when it has 0.3 m clear of every wall, otherwise the widest spot of the
   largest piece. Scene authors add their own waypoints.

**Exact (from the WAD):** every vertex, every wall, floor and ceiling heights, light, which side is which sector, sky ceilings.
**Choices:** scale and axes above, the decomposition, placeholder textures, dropped tiny sectors, opened doors, the blocked rule, pruning, the
start. **Not carried over:** things, specials (lifts, doors, switches), textures, sidedef offsets. A lift or door sector sits at its Doom
rest heights.

## Curated regions

`--bbox x0,y0,x1,y1` (Doom units, y up) keeps the sectors with a linedef vertex inside; `--sectors 12,13,40` keeps listed Doom sectors.
Both can also be set per scene in `scenes.json` (`"bbox"`, `"sectors"`); unreachable remainders are pruned automatically. MAP13 and MAP29
are large: cut a curated region per journey instead of converting the whole map.

## Re-running

```
bash tools/doom/convert_all.sh        # tests, lump report, convert, validate, plan PNGs, Godot load check
python tools/doom/convert.py --scene warehouse && python tools/doom/check_world.py content/story/maps/doom_warehouse.json
python tools/doom/render_plan.py content/story/maps/doom_warehouse.json docs/shots/doom/plan_warehouse.png
python -I tools/doom/test_doom.py     # 25 tests on a synthetic WAD, no Doom data needed
bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_warehouse
```
`tools/story/check_map.gd` also loads a chapter file `content/story/<id>.json`, which Doom maps do not have, hence `check_doom_map.gd`.
Count `SCRIPT ERROR` lines in the Godot output: the runner can print success on parse errors.

## Scenes

| Scene | Map | Output | Concept image (`Concept art/`) |
| --- | --- | --- | --- |
| warehouse | MAP07 Dead Simple | `content/story/maps/doom_warehouse.json` | Cobalt Warehouse Dance Floor-1.png |
| bar | MAP02 Underhalls | `doom_bar.json` | Copper Basement Bar, Three Hidden Routes-3.png |
| balcony | MAP15 Industrial Zone | `doom_balcony.json` | Rainy industrial rooftop, three musical paths-8.png |
| lounge | MAP08 Tricks and Traps | `doom_lounge.json` | Mustard octagonal lounge of three routes-2.png |
| booth | MAP04 The Focus | `doom_booth.json` | Rhythm Booth, Three Hidden Routes-5.png |
| dock | MAP13 Downtown | `doom_dock.json` | Rainy Rhythm Club Loading Dock-6.png |
| mothership | MAP11 Circle of Death | `doom_mothership.json` | Mothership Ringwalk Over the Void-7.png |
| underworld | MAP29 The Living End | `doom_underworld.json` | Three Paths Across the Basalt Abyss-4.png |

(`tools/doom/scenes.json` is the machine-readable table. Output files do not exist until a WAD with geometry is supplied.)
