# Chill-out Lounge scene (doom_lounge): composition and mapping to the trace

Reference: `art/reference/doom_worlds/Mustard octagonal lounge of three routes-2.png` (secondary: `Mustard lounge with three new paths-5.png`). Map: `content/story/maps/doom_lounge.json`, an APPROXIMATE
reconstruction of MAP08 Tricks and Traps: the central octagonal hub read from the render trace (`tools/doom/trace/lounge.json`, 510 units across, sunken middle) plus everything the painting needs
(`tools/doom/trace/lounge_scene.py` writes `lounge_pilot.json`). No WAD geometry exists. Rebuild: `docs/doom/LAUNCH.md`. Result: 27 Doom sectors, 93 convex pieces, 168 portals (7 shut to walkers: the sofa-back
sides and the bar counter), 0 unreachable.

## What the painting shows, and where it is in the map

| Painting | Map (names are stable: the Magic rave borrows this geography) |
| --- | --- |
| Octagonal hall, tall beamed ceiling with a gold coffer | `concourse` (the walkway ring, floor 0, ceiling 5.5 m, texture `ceil_beam`), `step_ring` and the pit under a 7 m dome |
| Sunken conversation pit, two shallow steps down, a curved mustard tufted sofa, a rug of concentric octagons, a low octagonal table with a glowing mushroom lamp and red flowers | `step_ring` (-0.375 m), `back_n/back_s` (sofa backs), `seat_n/seat_s` (seats, -0.31 m), `gap_e/gap_w` (the pit stairs, east and west), rug bands `rug_rim`, `rug_stripe_a`, `rug_mid`, `rug_stripe_b`, `rug_in` (-0.75 m), `table`; billboards `lg_lamp_table`, `lg_vase`, `lg_cushion_*` |
| Ahead: a doorway up three steps onto a rain-slick street, the broad bald **Dock guide** in a long green coat with an armband | N face: `ahead_step_a/b` (two 0.25 m steps), `ahead_street` (cool grey-blue light, wet floor); guide `lg_guide_dock`; threshold `lg_ahead_door` |
| Left: the copper-tiled bar counter, bottle shelves, a record on the wall, the **Bar guide** in a waistcoat with open palm | NW face: `left_vest`, `left_bar`, `left_counter` (1.1 m island); decals `lg_bottles`, `lg_vinyl`; guide `lg_guide_bar`; threshold `lg_bar_door` |
| Right: a curving blue-lit glass passage with a rail, the **Floor guide** (braids, magenta sequin top, silver trousers, hand on hip) | NE face: `right_vest`, `right_passage` (cobalt deck, glass walls, cobalt light); guide `lg_guide_floor`; threshold `lg_floor_door` |
| Stone pilasters with brass sconces and gold studded acoustic panels between the doorways; palms in copper pots; curtains and bead curtains | the octagon's solid wall segments carry decals `lg_sc_*` (emissive sconces), `lg_studs_*` (studded panels); `lg_plant_*` billboards; five curtained niches `niche_e/w/s/se/sw` (velvet walls, `lg_beads_*` decals) |

The octagon is the render's hub (the brief's "eight doors" are its eight faces here: three open, five curtained). The render's big rooms radiating from the hub are not built.

**Reference viewpoint** `lg_ref` (0, -196 Doom units; 0, 6.1 m): the south walkway behind the near sofa, looking north. The Dock guide is dead ahead 16 m away, the Bar guide 26 degrees left (the NW arch), the Floor
guide 29 degrees right (the NE passage): all three stand inside their openings on clear sightlines (`test_lounge_each_guide_is_seen_...`). At 16:9 (460 px stage strip) they are 66, 72 and 86 px tall; the test asks 60.

**Exposure** (A1 night interior): sector lights 0.85 to 1.0 (`LIGHT_FLOOR` and per-sector values in `tools/doom/author_lounge.py`; the street and the blue passage 1.0 since stage D), tints lifted towards white 72 %, brown fog `#2a1608` (0.016),
18 light things (amber lamps over the pit and at the diagonals, a table lamp, a cool pool beyond each doorway, a key and a warm fill on the Dock guide, three street lamps), wet marble and street (the weather engine's gloss) and
rain in the street (`weather`: rain 0.8, only `ahead_street` lets it in). Measured with `python -I tools/doom/frame_check.py` on the 16:9 frames of `shoot_lounge.sh` (RW_KEEP), 8 November: see the table below.

## The camera (rail data: `tools/run/make_doom_lounge.py`)

* Stay rail (round 2): west reveal `lg_west` (2 bars out, 1.5 still), `lg_ref` (choice viewpoint, 3 bars back, hold 8 still, **pitch -12**), south-east reveal `lg_se_view` (2 out, 1.5 still), `lg_ref` again. Round 1's north and east reveals are off the rail (their waypoints stay for the shots).
* `rail.routes`: `up` (ahead: round the east side to `lg_ahead_door`, at the foot of the street steps 3.2 m before the Dock guide), `left` (west side to `lg_bar_door`), `right` (east side to `lg_floor_door`, at the blue passage's mouth), each ending with a 1 bar hold; `stumble`, `arrive` (from the blue passage mouth `lg_arrive`).
* `check_rail_paths`: 0 problems (8 November run). The doorway thresholds are where the world transition happens; the walks are checked as data.

## Stage D polish (8 November): the painting beside the reference viewpoint

The five biggest differences at `lg_ref` before this pass (shot 8 November, beside `Mustard octagonal lounge of three routes-2.png`), and what was done:

1. **The curtained niches at the frame's edges read as bright orange slabs** (the painting's edges are dark: foliage, the bar's shadow, the blue passage). `wall_curtain` is now deep oxblood velvet in shadow (`make_lounge_art.py` `OXBLOOD`).
2. **The Floor guide's passage was a bright, flat tiled blue box**; the painting's is dark cobalt glass lit by streaks and an LED strip. `wall_blue` redrawn: deep glass, diagonal light streaks, an LED strip at each mullion's foot.
3. **The Dock guide was a dark silhouette in the doorway.** A cool key light from a street lamp over him and a warm fill from the hub (`lg_lt_dock_key`, `lg_lt_dock_warm`): his green coat, armband and face now read.
4. **The street beyond the Dock door was a dry grey box**; the painting's is a rain-slick street with wall lamps. Rain (the weather engine, only in `ahead_street`), a wet street floor (gloss), three emissive wall lamps with pools (`lg_st_lamp_*`).
5. **The marble walkway was dry and the brass sconces small**; the painting's floor is polished and the sconces glow. Wet marble on the walkway and step ring (gloss of the practicals), sconces 1.25 m (were 0.95).

Measured exposure (16:9, `frame_check.py`): before (quick shots of the first-pass build) ref p50 0.25 / contrast 0.39, Floor threshold 0.29 / 0.36.
After, all 13 shots: ALL p50 **0.25**, contrast **0.39** (p5 0.10, p95 0.49); per shot inside the rule: reveal_east, stay_2, stay_3, stay_4 (4 of 13); the rest have p50 0.23 to 0.28 and contrast 0.35 to 0.47 (approach_dock 0.23 / 0.27 and reveal_north 0.24 / 0.28 are the darkest: the rain street). The ALL contrast is 0.01 under the rule.
For reference the painting itself measures p50 0.18, p95 - p5 0.38: the exposure rule asks for a brighter frame than the painting.

Guides: the Dock guide and the Floor guide are CROPS from the paintings (stage D round 1, `make_lounge_guides.py`); the Bar guide is the Warehouse's `bar` set, a CROP from `Midnight dance hall with three guides-1.png`. No ring or beacon under any of them.

## What matches, and what does not

MATCHES (read by eye on `contact_lounge.jpg`): the sunken octagonal pit with the mustard tufted sofa ring, the oxblood and cream octagonal rug, the low table with its glowing lamp and flowers; three openings with a guide in each (the Dock guide lit in the rain street straight ahead, the Bar guide in his waistcoat with bottle shelves and a record behind the copper counter on the left, the Floor guide in magenta and silver in the dark cobalt glass passage on the right); brass sconces and gold studded panels on the stone pilasters; palms in copper pots; warm amber against the cool doorways; rain in the street.

DOES NOT MATCH:
* (Round 1.) The foreground sofa and the pit were under the pad strip at a level eye; round 2 pitches the choice hold -12 degrees (below): the pit and the near sofa ring are in the picture; the cut-out near sofa with its cushion still sits mostly under the pads.
* The camera is 6 m back (the painting's is much closer, the Floor guide 3 m away and large); the room is larger than the painting's.
* Flat walls (no arched lintels, fat pilasters, octagonal beam ribs), no glowing ceiling coffer (a flat coffered tile), no hanging vines, a straight bar counter, a straight passage (no curving glass bridge with a rail), a straight street.
* (Round 1: the guides were 66 to 86 px at `lg_ref`. Round 2: 83 to 88 px at the pitched pose, below.)
* (Round 1: ALL contrast 0.39; 9 of 13 shots off. Round 2: below.)

## Placeholders

Every texture, decal and prop is procedural placeholder pixel art or a cut from the painting (`tools/doom/art/make_lounge_art.py`); the painting's richness (reflective marble, leather grain, copper gleam, volumetric rain) is not reached. The music is a placeholder.

## Hooks wanted (nothing in `src/` was touched)

* The lounge is the geography world `doom_lounge` (one scene); the Warehouse's right guide leads straight here, and its guides lead straight to `doom_dock` (up), `doom_bar` (left), `doom_warehouse` (right).
* (Done in round 2 with the engine's `pitch` hook.)

## Shots (8 November, `docs/shots/doom/lounge/`)

`contact_lounge.jpg` (the painting, then the reference viewpoint, the three reveals, the arrival, the three thresholds, the stumble and the stay loop at four song times, each at 16:9 and 20:9), `walk_strip.jpg` (ahead, left, right and the stay loop, 6 frames each at the eye's real height),
`walk_*.txt` (pose tables), `art_sheet.png` and `guides_sheet.png`.

## Polish round 2 (9 November, `docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md`)

**The choice window and the reference viewpoint.** The rail climbs one place per block decision (phase beats 12.5, 28.5, 44.5) and the window opens at beat 49: with round 1's
four-place loop the first phase's window found the camera walking to `lg_east` (a drive of the run data), so a first visit never chose from `lg_ref` and an authored pitch would
never have been seen there. The stay rail is now a near reveal and back (above). `tests/test_doom_views.gd`
`test_lounge_first_window_finds_the_camera_at_the_reference_viewpoint_with_its_pitch` drives three phases (still window hold at `lg_ref` each time; the first hold carries pitch
-12), and the guide-state captures of a real run (`RW_RUN_VIRTUAL`, the bot, a tap at beat 50) show the camera at `lg_ref` looking down into the pit.

Done:
* **The sunken sofa pit in the reference shot**: `lg_ref` holds a steady **-12 degree pitch** through the choice window (`tools/run/make_doom_lounge.py` `REF_PITCH`; the engine's
  `pitch` hook). At 16:9 the sofa ring, the rug and the table with its lamp fill the middle of the picture above the pads; `ref` in the shot set is shot at that pitch
  (`RW_STORY_CAM=lg_ref,0,-12`), `ref_level` without it. The viewpoint's floor was not lowered nor the pit raised (not needed).
* **The guides brought forward** (66 to 86 px before, the smallest in any scene): the Dock guide stands on the first street step (2.6 m in front of his threshold, which moved
  back into the hub), the Bar guide straight in his arch's mouth (the threshold at the arch's face). At the pitched pose they are Dock 83, Bar 84, Floor 88 px at 16:9, at least
  60 px apart, clear of the HUD and the pads (`test_lounge_guides_read_at_the_pitched_reference_pose`, which asks 80).
* **Coffered panelling, columns, a vault frieze**: the gold studded panels (the "gold cubes") are warm coffered timber panels now (`deco_coffer`), a coffer frieze runs over each
  of the eight faces under the vault (`deco_frieze`, fixed-yaw decals) and a carved stone pilaster with a brass capital stands on each corner (`deco_pilaster`). The ceiling ribs
  stay the round 1 coffered tile (with the pitch, the vault is above the picture).
* **The Floor threshold**: the passage's glass is redrawn as cobalt glass with the city's lit windows beyond it, a thin streak and the LED strip at the foot (the bright striped
  tile is gone), a cool key on the Floor guide and a far violet-blue light down the passage. It is still the round 1 passage geometry.
* **Exposure**: tints lifted 0.8 (was 0.72), lamp pools wider (x1.6), the walkway and step ring at light 1.0, two more street lamps and a warm glow at the street's far end,
  two wall lamps in the bar, the street a step lighter, and a warm halo (`lg_halo`, additive) on every sconce and over the table lamp.

Exposure (16:9, `frame_check.py` on the `RW_KEEP` frames of `shoot_lounge.sh`, `frame_check.txt`), p50 / contrast before (round 1) and after:

| shot | before | after |
| --- | --- | --- |
| `approach_bar` | 0.28 / 0.35 | 0.30 / 0.40 |
| `approach_dock` | 0.23 / 0.27 | 0.26 / 0.36 |
| `approach_floor` | 0.25 / 0.34 | 0.19 / 0.31 |
| `arrive_passage` | 0.24 / 0.37 | 0.28 / 0.42 |
| `ref` | 0.25 / 0.42 | 0.29 / 0.49 |
| `ref_level` | (new) | 0.27 / 0.47 |
| `reveal_east` | 0.26 / 0.41 | 0.29 / 0.47 |
| `reveal_north` | 0.24 / 0.28 | 0.26 / 0.37 |
| `reveal_se` | (new) | 0.26 / 0.43 |
| `reveal_west` | 0.25 / 0.39 | 0.26 / 0.42 |
| `state_bar_committed` | (new) | 0.28 / 0.40 |
| `state_bar_selected` | (new) | 0.28 / 0.47 |
| `state_dock_committed` | (new) | 0.28 / 0.42 |
| `state_dock_selected` | (new) | 0.29 / 0.47 |
| `state_floor_committed` | (new) | 0.29 / 0.43 |
| `state_floor_selected` | (new) | 0.29 / 0.47 |
| `stay_1` | 0.26 / 0.38 | 0.28 / 0.49 |
| `stay_2` | 0.27 / 0.45 | 0.30 / 0.53 |
| `stay_3` | 0.26 / 0.43 | 0.30 / 0.51 |
| `stay_4` | 0.27 / 0.47 | 0.29 / 0.51 |
| `stumble` | 0.24 / 0.40 | 0.26 / 0.45 |

After: **17 of 21** inside the rule; ALL p50 0.27, contrast 0.45 (before: 4 of 13, ALL 0.25 / 0.39). Off: `approach_floor` (p50 0.19, contrast 0.31: the dark glass passage;
lightening its glass until it passed made it the bright blue box again, so the darker glass is kept), `approach_dock` and `reveal_north` (0.26 / 0.36 and 0.26 / 0.37: the grey
rain street behind the Dock guide), `state_bar_committed` (0.28 / 0.40, a walk frame).

Guides: unchanged sprites (Dock and Floor CROPS from the paintings, the Bar guide the Warehouse's bar CROP). No ring or beacon. The lounge block of `test_doom_views.gd` already had
the wall-sightline check; it passes with the guides moved.

Shots (`docs/shots/doom/lounge/`): `contact_lounge.jpg` (the painting, `ref` at the held pitch and `ref_level`, the reveals, the arrival, the thresholds, the stumble, the stay rail
at four song times, and the guide-state captures `state_<guide>_selected` (beat 50.4) and `_committed` (beat 52) of a real run), `walk_strip.jpg` and `walk_*.txt`, `frame_check.txt`, `art_sheet.png`.

### The lead's list

- [x] The sunken sofa pit in the reference shot: pitch -12 at `lg_ref`, held through the window, and the first window now happens there.
- [x] The gold cubes: coffered timber panels, a coffer frieze under the vault, stone pilasters with brass capitals. CARRIED: the ceiling ribs as geometry or sky (the pitched view does not show the vault).
- [~] The Floor threshold: dark cobalt glass with city lights and a far light; CARRIED: its shot is under the exposure rule (above), and the passage is still straight (no curving glass bridge).
- [~] Contrast: 17 of 21 shots in (was 4 of 13); four CARRIED (above).
- [x] Added (the independent review): the guides 66 to 86 px: now 83 to 88 px at the pitched reference pose.
