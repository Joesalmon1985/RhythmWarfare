# Loading Dock scene (doom_dock): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Rainy Rhythm Club Loading Dock-6.png` (also `Rainy Dock of Three Paths-7.png`, not used). Map: `content/story/maps/doom_dock.json` (MAP13 Downtown), APPROXIMATE and **invented from the painting**:
the render trace of MAP13 (`tools/doom/trace/dock.json`) is one open plaza with fourteen diamond city blocks, no loading dock, shutter or door, so `tools/doom/trace/dock_scene.py` builds the place on a 0.25 m grid
(`dock_pilot.json`) and `tools/doom/author_dock.py` dresses it. It takes from the render only the open street and the blocks as walls round it. Routing: ahead Mothership, left Floor, right Underworld.

## What the painting shows, and where it is in the map (metres, x east, y north)

| Painting | Map piece |
| --- | --- |
| Wet concrete apron with yellow-striped edge, bollards, drain, flight cases, pallets | `apron` (11.5 m with `canopy`), floor +0.25, `dk_floor_conc`; bollards, case, pallets are billboards |
| Steel canopy and roller shutter on the right, caged hanging lamp, chain | `canopy` (3.5 m ceiling, truss texture), east wall `dk_wall_shutter` plus a shutter decal, `dk_hang_lamp`, `dk_chain` |
| Red brick wall on the left, drainpipes, sodium wall lamp, treble clef graffiti, steel door ajar | `apron`/`walk` west wall `dk_wall_brick`, pipe and clef decals, door-leaf decal, `dk_door_lamp` |
| The blue-lit doorway, **Floor guide** (braids, magenta top, silver trousers) | `floor_door` (4 m wide, opening in the brick wall) then `floor_hall` (blue passage); guide at (-4.8, 7.3); threshold `dk_floor_door` |
| Wet asphalt street running away between dark towers, street lamp | `street` (9 m x 15.5 m, floor 0), `walk` sidewalk (+0.25, kerb 0.25), tower walls with lit-window decals, `dk_towers` decal at the end, two lamp billboards |
| **Mothership guide** (violet, pale hair, horns) at the street's end | guide at (-0.6, 16.0); threshold `dk_moth` (0.8, 18.8) |
| Van, pallet stacks, chain-link fence, domed furnace with a glowing mouth, **Underworld guide** on crates with a drum | `yard` (6 x 7.5 m) east of the street; `dk_van`, `dk_stack_*`, `dk_furnace`, `dk_drum`, crates, a fence decal; guide at (10.0, 12.6); threshold `dk_under` (12.2, 14.9) |

Reference viewpoint `dk_ref` (1.0, 1.5) looks north (choice viewpoint, 8 bars still). In the 460 px stage strip the guides are 163 px (Floor, 5.8 m), 103 px (Underworld, 11 m) and 74 px (Mothership, 14.5 m)
at 16:9 and 20:9 alike (`tests/test_doom_views.gd`, dock block: 60 px minimum, inside the picture, apart, clear of the HUD, and a sightline test against the solid walls).

Rail (`tools/run/make_doom_dock.py`, merged by `make_doom.py`): stay loop = street view, door view, yard view (each 2 bars still, via polylines), then `dk_ref` (choice, 8 bars). `rail.routes`: `up` (street to `dk_moth`), `left` (apron, sidewalk,
door, passage to `dk_floor_door`), `right` (street, yard to `dk_under`), `stumble`, `arrive`; each route ends at its threshold with `hold_bars` 1, `rail.exits` names the three. World `doom_dock` is depth 2, geography: one scene `doom_dock`, its routes straight to
`doom_mothership` (up), `doom_warehouse` (left), `doom_underworld` (right); three guide hotspots (figure staging, no rings) and the stay hotspot. The cast is empty (the painting has only its guides).

## Shots (docs/shots/doom/dock/)

`contact.jpg` (the painting beside `dk_ref`, then every viewpoint as a 16:9 | 20:9 pair) and `walk_strip.jpg` (three routes; pose tables `walk_up.txt`, `walk_left.txt`, `walk_right.txt`). Regenerate: `python3 tools/doom/shoot_dock.py`.

## Stage D polish, round 1 (docs/briefs/DOOM_POLISH_BRIEF.md)

**The five biggest differences from the painting at `dk_ref`, written before the second half of the work (the first agent had done the sky, the street, the passage, the tiles and the crops):**

1. Exposure and contrast: the painting has deep darks (the towers, the corners) and bright warm reflections; the scene was a flat violet mid-grey (p50 0.22, p95 - p5 0.32 over the shots).
2. The wet floor: the painting's lamps throw long vertical reflections on standing water; the baked gloss broke into grain at mid distance (1-texel dither under nearest sampling, no mipmaps) and no rain fell.
3. The towers: the painting's buildings are dark masses with a few lit windows; ours were evenly gridded with many lit windows and a lifted haze.
4. The club passage behind the door: the painting's blue doorway is a dark blue with a bright light; ours was a flat bright-blue wash with no contrast.
5. The far street (the ahead hold): dark and lamp-less beyond the second street lamp, so the threshold read as a dim corridor.

**What was done about each:** (1) every sector's song-time light is 1.0 and the flat light away from the lamps is cut to `ambient` 0.4-0.5 (0.7 in the passage), the fog and the sky are darker (`#17152e`, sky lift 0.04); (2) the gloss and the floors' ramps dither in 2 x 2 texel blocks, a solid bright core in each smear, two-texel ripple rings, 2 x 2 grit (`make_dock_art.wet_gloss`, `ramp(cell=2)`); the map's `weather` (rain 0.8, wind 10, drips at the canopy's edge and the club door's lintel) adds the rain streaks and the engine's gloss bands; (3) tower faces darker with fewer lit windows (11 to 17 %), brighter mid-tones so the median holds; (4) the passage's panels dark navy with a bright LED strip and its glow, the floor dark rubber with the strip's long blue reflections; (5) a fourth street lamp (east side, 27.5 m) and two lamp pools on the far street.

**Matches now:** the composition at `dk_ref` as before (brick wall and lit club door with the Floor guide left, the street to the violet Mothership guide, the van, the furnace and the seated Underworld guide right, the bollards and the yellow apron edge); rain falling on the six open sectors, lit by the lamps (orange by the sodium lamps, blue in the open), the canopy and the passage dry, drips at the eaves; the wet gloss bands under the lamps; the storm sky; the palette (red brick, dark blue towers with amber windows, sodium against the cool rain light).

**Does not match:** the street is straight (the painting's curves left); the near right of the painting (a big flight case, more pallets, the shutter close by) is thinner here; the fence is a wall decal; the caged hanging lamp and the chain read small; the floor gloss is the engine's bands, not a mirror (nothing is reflected); the furnace and van are flat billboards; `route_ahead` stays dark (it looks up the street at the dark towers, p50 0.2) and `route_left` (the blue passage) is low in contrast.

**Guides (ruling 36):** all three CROPPED (`tools/doom/art/make_dock_crop.py`): Floor from this painting (350 px there), Mothership from the Booth's painting (200 px there; 130 px in this one), Underworld from `Rainy Dock of Three Paths-7.png` (seated behind crates; his legs are hidden in that painting). No rings or beacons.

**Exposure (tools/doom/frame_check.py, 16:9 shots, the picture only):** before this round's second half (same tool, 8 Nov): ALL p50 0.22, p95 - p5 0.32. Now:

```
shot                      p5   p50   p95   sat   crush  blown  target
arrive                  0.15  0.29  0.54  0.34    0.0%   0.0%  off
hold_door               0.13  0.28  0.50  0.51    0.0%   0.1%  off
hold_street             0.13  0.25  0.61  0.38    0.0%   0.1%  ok
hold_yard               0.12  0.33  0.60  0.25    0.0%   0.0%  ok
ref                     0.14  0.29  0.54  0.35    0.0%   0.0%  ok
route_ahead             0.12  0.22  0.48  0.43    0.0%   0.0%  off
route_left              0.13  0.26  0.40  0.64    0.0%   0.1%  off
route_right             0.11  0.29  0.58  0.29    0.0%   0.1%  ok
ALL                     0.13  0.28  0.56  0.40    0.0%   0.1%  contrast p95-p5 0.43
```

## Placeholders and not done

Placeholders: the textures, props and decals are procedural (`tools/doom/art/make_dock_art.py`; the 256 px tiles drawn to the style guide, the props older); the music (Warehouse arrangements). The guides are crops of the paintings, not placeholders. No `src/` change was made. Regenerate: `python -I tools/doom/art/make_dock_art.py; python -I tools/doom/author_dock.py`, then `--import`, then `python tools/doom/shoot_dock.py`.
