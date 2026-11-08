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
`left` (deck, landing, down the five treads), `right` (deck, through the cabin door), `stumble`, `arrive`. World `doom_balcony` (depth 2, geography): one scene `doom_balcony`, its routes straight to `doom_mothership` (up), `doom_warehouse` (left),
`doom_booth` (right). The threshold is the `to` of each route move, the doorway `rail.exits[dir]`.

## Shots (docs/shots/doom/balcony/)

`contact.jpg` (the painting beside `bc_ref`, then every viewpoint as a 16:9 | 20:9 pair) and `walk_strip.jpg` (three routes, six frames each; pose tables `walk_up.txt`, `walk_left.txt`, `walk_right.txt`). Regenerate: `python3 tools/doom/shoot_balcony.py`.
frame_check over the shots: p50 0.08, p95-p5 0.37: **under-exposed** (target p50 0.25 to 0.38); the rooftop is darker than the painting.

## Stage D polish, round 1 (docs/briefs/DOOM_POLISH_BRIEF.md)

**The five biggest differences from the painting at `bc_ref`, written before changing anything:**

1. The sky and the city: the painting has a full moon in torn cloud, a searchlight and a deep skyline of dark towers with lit windows over the drop; the scene had a flat ceiling tile 8 m up and the drops' walls rose to it, so no sky and no city.
2. The Night One crowd filled the deck and the cabin (the painting's roof is empty but for the three guides).
3. Exposure: p50 0.17, p95 - p5 0.37 over the shots (under), against the painting's moonlit blue with warm cabin light.
4. The three thresholds stared at walls: the stair foot at a brick wall a metre away, the cabin's hold at its back wall, the bridge end at the tower's blank base.
5. The guides were procedural placeholders (the Lounge's Floor sprite, recolours), and the surfaces flat 128 px tiles (no wet diamond plate, no puddle reflections, no rain).

**What was done about each:** (1) the map's `sky` (`bc_sky.png`: moon at the upper left of the view north, two searchlight beams, a three-layer skyline with amber/violet/cyan windows and red mast lamps) on every open sector; the drops' ceilings lowered to 2.4 m (`balcony_scene.py`) so their far walls stop under a metre above the eye and the sky shows over them, `upper_tex: sky` between open sectors; three 256 px tower billboards (dark floor bands, sparse lit windows, a lit penthouse band, roof plant, a red mast lamp) in place of the flat ones; (2) the cast is empty (`story_doom_balcony.json`, no homes); (3) light 1.0 with `ambient` 0.62-0.75, lamp pools on the deck (moon blue, a red and a cyan puddle light, the cabin door's amber spill, a brick wash), lights on the towers, a lighter haze (`#1c2848`); (4) new geometry: an **alley** (3 x 7 m) runs south from the stair's foot to the club's lit side door (`bc_alley_door`, emissive, with its blue spill and an orange lamp), the cabin has a **back door** (`cback`, 1.5 x 2 m) onto a warm-lit stairwell going down (`bc_stair_glow`, emissive), and the tower base on the platform has a lit violet **door** under the lace dome; each threshold hold faces its opening; (5) guides cropped (below), 256 px tiles on the Dock's helpers (wet diamond plate with magenta/cyan/red/amber gloss and ripples, iron chequer treads with lit nosings, bar grating over the drop, riveted rusty steel, rain-streaked concrete, panelled cabin wall with rack LEDs, two brick faces), rain 0.85 with wind -12, drips at the cabin's eave and at the stair head, the cabin's door floor wet.

**Matches now:** the three guides at the three ways off the roof (the brick stair landing left, the cabin doorway right, the bridge and the lace dome ahead); the moon and the city over the drop; rain on the open roof lit by the lamps; the wet deck's coloured reflections; the amber cabin against the cool blue night; an empty roof.

**Does not match:** the far city is billboards (flat towers that turn with the camera) and a sky strip, not the painting's stepped roofs and high walkway; the moon is visible from the bridge and stair views, not prominent at `bc_ref` (the towers stand in front of it); the stair is five straight treads (the painting's turns); there is no parapet or pipe run along the cabin wall; the satellite dish and the lace dome are the earlier flat placeholders; the drops are dark pits (no lit yard with the forklift reads at this exposure); `hold_bridge` and `route_ahead` stay under the median (they look into the dark drop).

**Guides (ruling 36):** all three CROPPED (`tools/doom/art/make_dock_crop.py`, `make_balcony_guides.main_cropped`): the **Booth** guide from this painting (`booth_balcony8`, 225 px tall there, leaning in the cabin door; a polygon outline, the dark door's colours dropped, the boots kept by hand); the **Floor** guide from the Dock's painting (`floor_dock`, 350 px there; in this painting the stair's railing crosses her legs); the **Mothership** guide from the Booth's painting (`mothership_booth`, 200 px there; 85 px in this one). No rings or beacons. The guide test (`tests/test_doom_views.gd`, balcony block) passes: 72 px (Mothership), 191 px (Floor), 208 px (Booth).

**Exposure (tools/doom/frame_check.py, 16:9 shots, the picture only):** before (8 Nov, the same tool): ALL p50 0.17, p95 - p5 0.37. Now:

```
shot                      p5   p50   p95   sat   crush  blown  target
arrive                  0.09  0.24  0.44  0.46    0.0%   0.0%  off
hold_bridge             0.06  0.17  0.59  0.52    0.0%   0.1%  off
hold_cabin              0.12  0.24  0.43  0.40    0.0%   0.0%  off
hold_stair              0.10  0.28  0.48  0.47    0.0%   0.1%  off
ref                     0.09  0.24  0.43  0.44    0.0%   0.1%  off
route_ahead             0.06  0.17  0.49  0.56    0.0%   0.4%  off
route_left              0.13  0.27  0.42  0.46    0.0%   0.0%  off
route_right             0.14  0.29  0.43  0.44    0.0%   0.0%  off
ALL                     0.08  0.24  0.46  0.47    0.0%   0.1%  contrast p95-p5 0.39
```

## Placeholders and not done

Placeholders: the textures, props and decals are procedural (`tools/doom/art/make_balcony_art.py`: the stage D 256 px tiles, sky and tower billboards on the Dock's helpers; the dish, lace dome, forklift, racks and cases are the earlier flat placeholders); the music (Warehouse arrangements). The guides are crops. Two plain drops (`isle` to `vw2`, `isle` to `ve2`) stay open without a railing because the loader needs every void joined to the map by one open portal. No `src/` change was made. Regenerate: `python -I tools/doom/trace/balcony_scene.py; python -I tools/doom/convert.py --scene balcony --trace tools/doom/trace/balcony_pilot.json; python -I tools/doom/art/make_balcony_art.py; python -I tools/doom/author_balcony.py`, then `--import`, then `python tools/doom/shoot_balcony.py`.

## Stage D polish, round 2 (docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md)

**Correction to round 1:** the round 1 section above claims "the moon and the city over the drop" as matching. The round 1 sheet did not show that: at `bc_ref` the towers hid the moon and the drops were dark pits.

**The lead's list, ticked or carried:**

- [~] **The drop and the city must dominate the reference view (lower the parapets, the moon in frame, the wet deck reflecting the city, the brick box open on three sides).**
  - Done: the drop's walls stop at 1.25 m, under the eye. They were 2.4 m, a dark band across the view. Seen over them, the drop's far walls are the lit facades of the buildings below: concrete in three variants with single windows on a jittered grid (`facade_windows()`, about half lit) and the yard's blue-lit shutters at their feet.
  - Done: the drop is wider (32 x 24 m, five voids). The deck's own walls (the cabin front) stop at 4 m and the brick stair-house at 7 m, so the box is open ahead and over both sides.
  - Done: the tower billboards that hid the moon are gone. The moon is redrawn over a lower skyline (az -21, 16 degrees up) and is in the 16:9 and 20:9 reference shots. The choice viewpoint holds a pitch of -4 (`make_doom_balcony.PITCH`).
  - Carried: from `bc_ref`, 7 m back from the deck's edge, the eye cannot see down into the drop. It shows as the far facades and the yard's lights, not as the painting's plunging view, which would need the viewpoint at the edge and the stair and cabin guides would then be out of frame. The deck's gloss is the engine's lamp bands, not a reflection of the city.
- [x] **The pink equaliser shapes at `hold_stair` go.** All four `bc_eq_*` decals are removed. The stair view now looks over the landing towards the drop, the lace dome and the city.
- [x] **`hold_bridge` and `route_ahead` at p50 0.17: the drop needs its own light.** The drop is lit by its lit windows, the blue shutter lamps and sodium lamps on the yard floor. The skyline and storm sky are lighter (moonlit blue), the fog is thinner (0.008) and the bridge grating shows the hazy drop, not black. All eight shots are inside the rule (table below).
- [~] **The dish and lace dome are flat placeholders; the Mothership guide is 85 px; the moon is hidden.**
  - Done: the lace dome is new (`p_lace`: a cream filigree half-dome with open holes and warm lamps at its foot, emissive) and is 4.2 m over the tower's violet door.
  - Done: the moon is in frame (above).
  - Carried: the Mothership guide is 76 px at 16:9 (`test_doom_views`). The dish moved onto the cabin's roof but is still the flat placeholder.
- [x] **(Review) 0 of 8 shots in the rule; the Mothership guide cannot be picked out by eye.** All 8 shots are in the rule now. She stands at the platform's front edge (-0.7, 16.7) under a warm key light, with a violet rim light and the violet door behind her.
- [x] **(Review) Selected and committed guide-state captures.** They are the last row of `contact.jpg` (`tools/doom/guide_states.py`, the Mothership guide tapped).
- [x] **(Found in round 2) The choice window was not held at the reference viewpoint on a real run.** The stay loop is now one reveal (`bc_bridge_view`) and the choice viewpoint. A real-run timeline shows `bc_ref` held from beat 44 to 62. `bc_stair_view` and `bc_cabin_view` are views in the map, no longer on the rail.

**Other changes:**
- The bridge and the platform are level with the deck. The three 1 m steps went: the drop's walls must stay above a railing's top.
- The left threshold is at the alley's end, before the club's side door (the door's light is brighter).
- The right threshold is at the cabin's back door.
- The cabin view turns to the painting's composition: the lit cabin window with its equaliser glow, the Booth guide in the door, the drop and the city on the left.

**Guides at the reference viewpoint (`test_doom_views`, 16:9 and 20:9 alike):** Mothership 76 px, Floor 190 px, Booth 206 px (at the pitched pose, -4); all three CROPPED (unchanged from round 1). No rings or beacons.

**Exposure (`tools/doom/frame_check.py`, 16:9 shots, the picture only), 8 of 8 shots inside the rule (p50 0.25 to 0.38, p95 - p5 over 0.4).** Before round 2 (the merged head, same tool):

```
shot                      p5   p50   p95   sat   crush  blown  target
arrive                  0.09  0.24  0.44  0.46    0.0%   0.0%  off
hold_bridge             0.07  0.17  0.59  0.52    0.0%   0.1%  off
hold_cabin              0.12  0.24  0.43  0.40    0.0%   0.0%  off
hold_stair              0.10  0.28  0.48  0.47    0.0%   0.1%  off
ref                     0.09  0.24  0.43  0.44    0.0%   0.1%  off
route_ahead             0.06  0.17  0.49  0.56    0.0%   0.4%  off
route_left              0.13  0.27  0.42  0.46    0.0%   0.0%  off
route_right             0.14  0.29  0.43  0.44    0.0%   0.0%  off
ALL                     0.08  0.24  0.46  0.47    0.0%   0.1%  contrast p95-p5 0.39
```

After:

```
shot                      p5   p50   p95   sat   crush  blown  target
arrive                  0.11  0.26  0.53  0.43    0.0%   0.6%  ok
hold_bridge             0.11  0.26  0.66  0.43    0.0%   1.5%  ok
hold_cabin              0.11  0.25  0.53  0.43    0.0%   0.0%  ok
hold_stair              0.13  0.27  0.55  0.45    0.0%   0.1%  ok
ref                     0.12  0.26  0.53  0.41    0.0%   0.7%  ok
route_ahead             0.11  0.26  0.70  0.44    0.0%   1.9%  ok
route_left              0.14  0.26  0.70  0.36    0.0%   0.0%  ok
route_right             0.13  0.25  0.59  0.35    0.0%   0.0%  ok
ALL                     0.12  0.26  0.62  0.41    0.0%   0.6%  contrast p95-p5 0.50
```

**Shots:** `docs/shots/doom/balcony/contact.jpg` (the painting beside the reference shot, every viewpoint at 16:9 and 20:9, and a last row of guide states on the real rail: selected at beat 47, committed at 51.5 and the walk at 52.5. The tap commits at its own beat (ruling 39), so the committed frame is already on the walk-off. At the reference view the tapped guide's state sprite is small) and `walk_strip.jpg` with `walk_*.txt`. Regenerate them with `python3 tools/doom/shoot_balcony.py` (`RW_KEEP=<dir>` keeps the full-size frames for `frame_check`). The hold views that left the rail (see above) are still shot as views.
