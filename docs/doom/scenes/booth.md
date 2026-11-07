# DJ Booth scene (doom_booth): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Rhythm Booth, Three Hidden Routes-5.png`. Map: `content/story/maps/doom_booth.json` (MAP04 The Focus), APPROXIMATE and **invented from the painting**:
the render trace of MAP04 (`tools/doom/trace/booth.json`) gives only a macro footprint (a big hall, an S-corridor), not the tight windowed control rooms the brief and the painting want, so
`tools/doom/trace/booth_scene.py` builds the room from the painting on a 0.25 m grid (`booth_pilot.json`) and `tools/doom/author_booth.py` dresses it. Routing from the Booth: ahead Mothership, left Balcony, right Dock.

## What the reference shows, and where it is in the map (metres, x east, y north)

| Painting | Map piece |
| --- | --- |
| Narrow control-room aisle, foam walls, caged lamps, grate floor | `aisle` 3.5 x 11 m, 2.75 m ceiling; viewer at its south end |
| Long DJ desk on the left (decks, mixer, lamp, records, headphones, stool), racks under it | `dais` +1 m with the **railing** (`bt_rail`) on its aisle edge; turntable, mixer, lamp, records, cable billboards on it; desk stairs (`dstep_a/b`) at its north end |
| Wire-mesh window above the desk onto the rainy balcony, Balcony guide outside | window = railing wall `bt_window` (1.75 m) between the dais and `terrace`; skyline decal on the terrace's far wall; balcony guide at (-5.6, 7.8) |
| Balcony route (left) | landing, double door (`bal_door`), `porch`, a three-step stair (`bal_step_a/b`, `bal_top`, 0.375 m risers); threshold `bt_bal_top` |
| Hatch ahead onto a violet chamber, Mothership guide | `hatch` then `moth` (violet ribs, crystals, console); guide at (0.25, 14.2); threshold `bt_hatch` |
| Steel door (open) on the right onto the dock, Dock guide in the green raincoat | `dock_door` then `dock` annex (wet concrete, yellow stripes, flight cases, sodium pendants, shutter decal); guide at (4.0, 6.8); threshold `bt_dock_in` |
| Red LEDs, screens, pipes, cable shelf, vent door leaf | wall **decals** (`kind: decal`), the LEDs and screens `emissive`; racks and cases billboards; 15 light things (amber task light, red LED glow, violet, moon blue, sodium) |

Reference viewpoint `bt_ref` (0.5, 1.9) looks north (choice viewpoint, 8 bars still). In the 460 px stage strip the guides are 84 px (Mothership, 13 m), 174 px (Balcony, 6 m) and 213 px (Dock, 6 m)
at 16:9 and 20:9 alike (`tests/test_doom_views.gd`, booth block, requires 60 px, inside the picture, apart, clear of the HUD).

Rail (`tools/run/make_doom_booth.py`, merged by `make_doom.py`): stay loop = hatch view, window view (the landing), dock view (each 2 bars still, via polylines), then `bt_ref` (choice, 8 bars). `rail.routes`: `up` (aisle to the
hatch), `left` (aisle, landing, door, porch, up the stair), `right` (aisle, through the dock door), `stumble`, `arrive`. One scene `doom_booth` (geography world, depth 2), its routes straight to `doom_mothership` (up), `doom_balcony` (left), `doom_dock` (right)
(the Warehouse pilot's pattern); three guide hotspots (`staging` figure sprites per state and `show: figure`, no rings) and the stay hotspot.

## Shots (docs/shots/doom/booth/)

`contact.jpg` (the painting beside `bt_ref`, then every viewpoint as a 16:9 | 20:9 pair) and `walk_strip.jpg` (the three routes, six frames each; the pose tables in `walk_*.txt`). Regenerate: `python3 tools/doom/shoot_booth.py`.

**What matches the painting:** the narrow aisle with the guides at left (through the window), centre (the hatch, violet) and right (the open door onto a wet, striped dock); olive foam walls, caged lamps, red LED strips, wall screens, the
wire-mesh window, dense rack and case billboards, the violet chamber with crystals; the warm, dark exposure (frame_check over all shots: p50 0.23, p95-p5 0.40, slightly under the 0.25 to 0.38 target: sector light is already near its 1.0 ceiling, so only the lamp pools could lift it).

**What does not:** the desk is a lattice-railed 1 m dais seen from 2 m back, not the painting's big foreground desk (decks and mixer are small flat billboards, no big record turntable, no headphones, mug or sleeves in close-up); the balcony guide is
small and half hidden by the crowd and the mesh; the walls are flat tiles (no pipe runs along the ceiling, no thick door leaf, no puddle reflections); the painting's rain and wet-floor gloss are absent; the dock guide's beard and the Mothership guide's horns are not drawn (procedural placeholder sprites,
far below `art/reference/standard/guide_floor_sprite_standard.png`); the balcony route's stair is three plain steps. The brief's "dance pit in front" is not in the painting and is not modelled: the Night One crowd dances on the **balcony outside the window** instead (57 homes, kept off the line of sight to the balcony guide).

## Placeholders and not done

Placeholders: every texture, prop, decal and the three guides (`tools/doom/art/make_booth_art.py`, procedural); the music (Warehouse arrangements). Not done: no state-driven guide animation beyond the sprite per state; no `src/` hook was needed.

Regenerate: see `docs/doom/LAUNCH.md` (booth block).
