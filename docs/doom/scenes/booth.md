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

## Stage D polish, round 1 (docs/briefs/DOOM_POLISH_BRIEF.md)

**The five biggest differences from the painting at `bt_ref`, written before changing anything:**

1. The big desk: the painting's foreground is the desk (turntable with a red record, the mixer, the angled lamp, the mug, the headphones, the record crate); the scene had a 1 m railed dais with small flat turntable and mixer billboards, seen side-on.
2. The guides were procedural placeholders (no beard, no horns, flat colours).
3. The window: the painting shows rain and an empty iron balcony with the white-haired guide; the scene's Night One crowd danced outside the window and no rain fell.
4. The surfaces: flat 128 px tiles (no wedge foam, no tread plate, no corrugated cladding) and no wet floor in the dock annex.
5. The dock threshold held on a blank shutter wall (`route_right`), and the exposure was low (p50 0.23, p95 - p5 0.40).

**What was done about each:** (1) the desk is CROPPED from the painting (`tools/doom/art/make_booth_polish.py`, an outline polygon, hard alpha, 256 px tall) and stands as one foreground billboard `bt_desk_big` (1.6 m, in the aisle's west half, 3.4 m before `bt_ref`), so from the reference viewpoint it fills the lower left as the painting's desk does, the balcony guide visible through the window to its left; the dais is lowered to the floor (`booth_scene.py`) and its handrail removed (the painting has none); the window mesh runs floor to ceiling behind the desk; the old desk billboards (decks, mixer, lamp, records) are gone, the stool stands before the desk; a warm lamp light over it; (2) the three guides cropped (below); (3) the cast is empty; the balcony outside (terrace, porch, its stair) is open to a storm sky (`bt_sky`) with rain 0.85, wind 8, drips at the window's lintel and the balcony door; (4) 256 px olive wedge foam (ribs alternating per panel), diamond tread plate, the aisle's worn grate, corrugated steel cladding, riveted plate, a joisted ceiling; the dock annex wet (`wet` 0.6, roofed so no rain falls) with sodium and yellow-stripe gloss; (5) the annex's far wall carries an open roller shutter onto the rainy street (`bt_shutter_open`, emissive, a sodium light before it), the threshold hold faces it; light 1.0, `ambient` 0.7-0.75, lamps at the window, the desk and the terrace.

**Matches now:** the composition at `bt_ref`: the big desk in the lower left with its lamp lit, the window with the balcony guide in the rain beyond it, the aisle to the violet hatch with the Mothership guide, the dock door on the right with the Dock guide (bald, beard, green coat, yellow armband) in the sodium light; olive foam, caged lamps, red LEDs and screens; an empty booth.

**Does not match:** the desk is a flat cut-out: it turns with the camera and reads right only from about `bt_ref` (on the walks up the aisle it looms and turns); the steel door leaf of the dock door is not drawn (the painting's thick door with its louvre); no pipe runs along the ceiling; the shutter decal's street is crude; the Mothership's chamber is the earlier flat ribbed placeholder; `hold_window` and `route_left` (the rainy balcony) are under the median.

**Guides (ruling 36):** all three CROPPED from this painting (`tools/doom/art/make_dock_crop.py` CROPS `balcony_booth` 250 px, `mothership_booth` 216 px, `dock_booth` 466 px tall in the painting; `make_booth_polish.main` writes the four states). No rings or beacons.

**Exposure (tools/doom/frame_check.py, 16:9 shots, the picture only):** before (8 Nov, the same tool): ALL p50 0.23, p95 - p5 0.40. Now:

```
shot                      p5   p50   p95   sat   crush  blown  target
arrive                  0.10  0.24  0.45  0.43    0.1%   0.0%  off
hold_dock               0.14  0.26  0.40  0.40    0.0%   0.0%  off
hold_hatch              0.11  0.27  0.49  0.44    0.1%   0.0%  off
hold_window             0.11  0.20  0.34  0.36    0.0%   0.0%  off
ref                     0.10  0.23  0.45  0.43    0.1%   0.0%  off
route_ahead             0.16  0.33  0.67  0.46    0.0%   0.1%  ok
route_left              0.10  0.21  0.34  0.38    0.0%   0.0%  off
route_right             0.13  0.24  0.40  0.42    0.0%   0.0%  off
ALL                     0.11  0.24  0.47  0.42    0.0%   0.1%  contrast p95-p5 0.36
```

## Placeholders and not done

Placeholders: the textures, props and decals are procedural (`tools/doom/art/make_booth_art.py`, overwritten in part by `make_booth_polish.py`; the racks, cases, crystals, console, screens and the Mothership chamber's tiles are the earlier flat placeholders); the music (Warehouse arrangements). The desk and the guides are crops of the painting. No `src/` change was made. Regenerate: `python -I tools/doom/trace/booth_scene.py; python -I tools/doom/convert.py --scene booth --trace tools/doom/trace/booth_pilot.json; python -I tools/doom/art/make_booth_art.py; python -I tools/doom/author_booth.py`, then `--import`, then `python tools/doom/shoot_booth.py`.
