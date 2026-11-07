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
door, passage to `dk_floor_door`), `right` (street, yard to `dk_under`), `stumble`, `arrive`; each route ends at its threshold with `hold_bars` 1, `rail.exits` names the three. World `doom_dock` is depth 2: entry scene `doom_dock`, stand-ins
`doom_dock.mothership/.floor/.underworld`, exit scene `doom_dock.return`; three guide hotspots (figure staging, no rings) and the stay hotspot. The cast is empty (the painting has only its guides).

## Shots (docs/shots/doom/dock/)

`contact.jpg` (the painting beside `dk_ref`, then every viewpoint as a 16:9 | 20:9 pair) and `walk_strip.jpg` (three routes; pose tables `walk_up.txt`, `walk_left.txt`, `walk_right.txt`). Regenerate: `python3 tools/doom/shoot_dock.py`.

**What matches the painting:** the composition at `dk_ref`: brick wall and open club door with a figure at left, the street running to a violet figure at its end, the van and the lit furnace-side figure at right, the shutter wall and bollard in the near right,
yellow apron edge; the palette (red brick, dark blue towers with amber windows, sodium and blue light).

**What does not:** no rain falls and there are no wet reflections (only painted gloss on the floor tiles); the street is straight, the painting's curves left; the sky is a dark ceiling tile 7.5 m up, not a sky; the fence is a wall decal, the two near
bollards are small and the far-right pallets and case are fewer than the painting's; the Underworld guide stands (the painting seats him with a drum, which is a separate prop beside him); the Floor guide is the Lounge's sprite, not leaning on the door;
the wall tiles repeat. The three threshold shots (`route_*`) look at a wall a metre or two ahead (the street's end wall, the passage's end, the yard wall), so they read as blank surfaces.
Exposure (frame_check over the seven kept shots): p50 0.22, p95-p5 0.45, crushed 0 %, blown 0.2 %, under the 0.25 to 0.38 target in the median.

## Placeholders and not done

Placeholders: every texture, prop, decal and the three guides (`tools/doom/art/make_dock_art.py`, `make_dock_guides.py`, procedural); the stand-in destinations; the music (Warehouse arrangements). Hooks needed: a real sky (the map's `sky` is empty, the
ceiling tile stands in), rain particles and wet-floor reflection, the engine's geography hook H1.6 (the thresholds `dk_moth`, `dk_floor_door`, `dk_under` and `rail.exits` are in the data; the stand-ins are then deleted in `make_doom_dock.py`). No `src/` change was made.
