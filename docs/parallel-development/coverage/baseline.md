# Touch coverage baseline

First measurement of how much of the visible world the player can touch, and for how much of the play time. Measured in the running game's own code (no game file changed), tree of `wip/narr-n1` on 6 Nov 2026, 82 scenes (main run 36, Gospel 17, Squadron 14, Ember 15). Targets (owner): touch regions cover at least 50% of the world in at least 80% of samples of active play; choices alone at least 25%; no region over 1.5x its visible object; smallest target 88 px in the 1280x720 design.

## Five findings

1. Far from the target. Over all 82 scenes the touch regions cover a **mean 2.2%** of the world, and only **0.2%** of samples reach 50% (the best single sample of 7,754 is 51.5%). The target needs 50% in 80% of samples: **0 of 82 scenes pass**. Per criterion: 0 meet touch, 0 meet choice, 12 meet the 1.5x object ratio, 7 meet the 88 px minimum.
2. Against the desk model (about 6% while touchable, touchable about 25% of a scene): measured **median 7.5% while something is selectable** (7.7% median over scenes), so the 6% was about right, slightly low. Time touchable: **18.2%** of samples overall; main-run scenes 26.2% (16 of the 61 sampled beats, the model's 25%), path scenes only 12.8% (16 of 125 beats, two laps), so paths are worse than the model. Choices alone: median 5.6% while selectable, and 25% is reached in only 2.2% of samples.
3. Best scenes: `ward` (22.7% mean; its card table is touchable all the time, the only scene on show 100% of samples), `ward.exit` 11.1%, `hospital.exit` 10.4%, `hospital_late.exit` 10.3%, `hospital_late` 9.8%. Worst: `squadron city.c10` 0.2%, `ember deeps` 0.2%, `gospel jordan.wilderness` 0.3%, `ember north.pass` 0.3%, `squadron city.c08` 0.4%.
4. Time is the bigger lever, not size: 82% of samples have nothing selectable (a 16-beat window), and even inside the window the median touch union is 7.5% of the world. Where regions exist they are also big for what they surround: 70 of 82 scenes have a region over 1.5x its object by area (people and doors 2 to 3x, small lamps and baskets up to 37x), and the smallest target is 72 px (`MIN_PX`), under 88 px in 75 scenes.
5. 20:9 is a little worse than 16:9 (mean 1.8% against 2.2%; no sample reaches 50%), because the same metre-scaled regions cover a wider picture; the pad size hardly matters (30 / 36 / 42%: 2.3 / 2.2 / 2.0%).

## How to run

```
export RW_AUDIO_WORK=C:/Users/joesa/rw-audio-work RW_RUN_TRACKS=0; export GODOT="$PWD/tools/dev/godot.sh"
"$GODOT" --headless --path . --import      # once per fresh worktree
"$GODOT" --headless --path . -s tools/run/coverage_audit.gd -- --run=main --aspect=16:9 --pad=36 --out=C:/Users/joesa/rw-audio-work/coverage/main_169_36.jsonl
python tools/run/coverage_audit.py <the .jsonl files> --detail=16:9/36 --out=tables.md
```

Options: `--run=main|gospel|squadron|ember|all` (or a comma list), `--scene=<substring of a scene id>`, `--aspect=16:9|20:9` (1280x720 or 1600x720), `--pad=30|36|42`, `--out=<file>`. It runs headless (no window). The main run's 36 scenes take about 105 s, each path under a minute. The raw lines (about 230 KB per configuration) are not committed; the tables below are the result. `SCRIPT ERROR` count over all 12 runs and the test runs: 0.

## Definitions

- **Sample**: one beat of active play of one scene, taken when the virtual clock reaches it, with the live camera (`RunPlay._exit_pose()`) and the hotspots of `RunPlay.hotspot_items()` (the list the taps use; the committed one is left out as in `hotspot_tap`). The scene is played by the perfect bot with no taps (default exits), a fresh save, track scenes off.
- **Active play**: beats k = 0, 1, 2, ... from the scene's first downbeat, in all laps of the scene (run scenes one lap = 61 samples, path scenes two laps = 125), up to beat 60 of the last lap. Excluded: the count-in; the last lap's beats 61 to 63 (door walk / world-change close; the choice has committed and nothing is selectable); minigames and the Bassment (dropped if they occurred; the no-tap bot starts none). A sample with nothing selectable counts as **0%**.
- **World rectangle**: the stage host (full width, above the pad strip: 1280 x 461 at 36%) minus the HUD zones: the crowd meter and mix-stage blocks top left (about 320 x 47 px) and the route-window bar on the stage's bottom edge (about 6 px). The falling notes are drawn over the picture but take no touches and are not excluded.
- **Touch coverage**: the union of every hotspot's touch region, laid out by `HotspotView.layout(..., rects = true)` in the stage host's size exactly as `RunPlay.hotspot_tap` does: the ring circle (`radius_px`, at least `min_px / 2`) plus the touch rectangle of the staging; edge beacons (anchor out of sight) are touchable and counted. Divided by the world area. **Rasterisation**: exact in x (interval union per row), rows every 2 px in y (230 rows), so within about 1% of the true union.
- **Choice coverage**: the same for hotspots whose `on_success.route` is non-empty and not the scene itself. A scene meets the choice target when choice coverage is at least 25% in at least 80% of samples (my reading of the rule).
- **Visual coverage** (kept apart): `vis hs` = union of the drawn objects of the hotspots on show: the map thing's quad (its real mesh size, transparent margin of the sprite included), a person as 0.6 x 1.7 m (`StoryCrowd.HERO_M` tall), a staged exit as its `width_m` x `height_m` door at the anchor, a sign post as 0.8 x 1.6 m. `vis all` = all opaque, visible billboard things of the map plus all present people. Not included: additive or alpha-blended glows and banners, hidden set pieces, the choice art's props, door offsets (`door_at`), and the 3D walls and floor. So `vis all` understates what the eye sees.
- **Smallest target**: per hotspot the larger of the ring diameter and the shorter side of its touch rectangle; the tables show the minimum over all samples with something on show.
- **Ratio**: a hotspot's touch-region area (circle union rectangle) over the area of its visual box, worst sample; over 1.5 is a violation. A hotspot with no drawn object (an empty spot or waypoint with no staged door) cannot be compared and is counted in "no object". An edge beacon has no object on screen and is skipped. The linear reading (width or height ratio over 1.5, field `ratio_lin` in the data) is stricter: 72 of 82 scenes fail it.
- **Pad overlap**: a touch region meeting a pad's hit rectangle (`pad_view.button_rects()`). None, by construction (`layout` keeps regions inside the stage).
- **PASS** needs all of: touch at least 50% in at least 80% of samples; choice at least 25% in at least 80% of samples; no region over 1.5x its object (area); smallest target at least 88 px; no pad overlap.

## Limits (approximated or not measured)

- Perfect bot, no taps, fresh save: hotspots behind a flag or energy condition that a real run would have set are not on show. Selecting a hotspot does not change its touch region, so the no-tap run shows what is touchable. Minigames, the Bassment, cinematics and the card-table close-up are not entered.
- Visual bounds are approximate as listed (sprite quad with transparent margin, fixed person size, door at the anchor). The ratio verdicts depend on them; the coverage numbers do not.
- The tap code's world is the stage host rectangle; the measurement uses the same size.
- Touchable time counts beats 0 to 60 of the last lap, not the 64 of the model, so 16 of 61 = 26.2%.
- Samples are once per beat on the 30 Hz virtual clock, not per frame.
- `PAD_SIZES` is copied into the tool (an autoload cannot be named by a SceneTree script), and the game classes are reached through `load()` so the tool compiles with 0 script errors.

## Results

## Configuration 16:9/36 (aspect / pad size %)

| | scenes | samples | touch mean | touch median | median while selectable | any selectable | at least 50% | choice mean | choice at least 25% | visual (hotspot objects) | visual (all things and people) | smallest target | scenes passing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Main run | 36 | 2196 | 4.4% | 0.0% | 8.8% | 30.9% | 0.5% | 2.8% | 5.2% | 2.3% | 34.9% | 72 px | 0 / 36 |
| Gospel | 17 | 1997 | 1.3% | 0.0% | 7.2% | 13.6% | 0.0% | 1.1% | 0.8% | 0.7% | 32.0% | 72 px | 0 / 17 |
| Squadron | 14 | 1750 | 1.6% | 0.0% | 9.7% | 12.8% | 0.0% | 1.5% | 2.5% | 2.2% | 40.0% | 72 px | 0 / 14 |
| Ember | 15 | 1811 | 1.0% | 0.0% | 5.2% | 13.3% | 0.0% | 0.9% | 0.0% | 0.8% | 29.8% | 72 px | 0 / 15 |
| **All** | 82 | 7754 | 2.2% | 0.0% | 7.5% | 18.2% | 0.2% | 1.7% | 2.2% | 1.5% | 34.1% | 72 px | 0 / 82 |

Scenes meeting each target: touch >=50% in 80% of samples 0 of 82; choice >=25% in 80% of samples 0; no region over 1.5 x its object 12; smallest target >=88 px 7; no pad overlap 82. Median over scenes of the scene's mean touch coverage: 1.5%; of the scene's median while selectable: 7.7%.

### Per scene, 16:9/36

| run | scene | samples | touch mean | median | at least 50% | any selectable | choice mean | choice at least 25% | vis hs | vis all | min target | hs on show | ratio over 1.5 | pad overlap | no object | result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| main | warehouse | 61 | 2.3% | 0.7% | 0.0% | 73.8% | 1.8% | 0.0% | 1.0% | 49.3% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | warehouse.bar | 61 | 8.6% | 0.0% | 0.0% | 26.2% | 7.5% | 24.6% | 5.0% | 54.3% | 72 px | 0-4 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | warehouse.balcony | 61 | 6.1% | 0.0% | 0.0% | 26.2% | 6.0% | 21.3% | 3.6% | 40.4% | 72 px | 0-4 | 3 | 0 | 1 | FAIL (touch, choice, ratio, px) |
| main | warehouse.chill | 61 | 6.0% | 0.7% | 0.0% | 73.8% | 4.6% | 1.6% | 4.1% | 61.7% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | warehouse.booth | 61 | 3.9% | 0.0% | 0.0% | 26.2% | 3.7% | 0.0% | 0.0% | 61.9% | 72 px | 0-3 | 0 | 0 | 1 | FAIL (touch, choice, px) |
| main | warehouse.exit | 61 | 3.6% | 0.0% | 0.0% | 26.2% | 3.6% | 0.0% | 3.0% | 51.2% | 72 px | 0-3 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | mothership | 61 | 1.2% | 0.0% | 0.0% | 26.2% | 0.6% | 0.0% | 0.6% | 27.2% | 72 px | 0-4 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | mothership.gallery | 61 | 1.0% | 0.0% | 0.0% | 26.2% | 0.4% | 0.0% | 0.5% | 28.9% | 72 px | 0-3 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | mothership.reactor | 61 | 0.7% | 0.0% | 0.0% | 26.2% | 0.4% | 0.0% | 0.2% | 33.5% | 72 px | 0-3 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | mothership.bridge | 61 | 0.5% | 0.0% | 0.0% | 26.2% | 0.3% | 0.0% | 0.2% | 32.7% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | mothership.exit | 61 | 7.7% | 0.0% | 0.0% | 26.2% | 7.4% | 21.3% | 5.0% | 32.4% | 72 px | 0-4 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | underworld | 61 | 1.2% | 0.0% | 0.0% | 26.2% | 0.7% | 0.0% | 0.7% | 28.3% | 72 px | 0-4 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | underworld.court | 61 | 2.3% | 0.0% | 0.0% | 26.2% | 1.0% | 0.0% | 4.8% | 78.9% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | underworld.furnace | 61 | 2.1% | 0.0% | 0.0% | 26.2% | 0.6% | 0.0% | 1.5% | 41.1% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | underworld.pit | 61 | 0.7% | 0.0% | 0.0% | 26.2% | 0.3% | 0.0% | 0.3% | 31.7% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | underworld.exit | 61 | 4.3% | 0.0% | 0.0% | 26.2% | 4.1% | 0.0% | 2.4% | 46.5% | 72 px | 0-3 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital | 61 | 1.8% | 0.0% | 0.0% | 26.2% | 0.2% | 0.0% | 0.5% | 35.3% | 72 px | 0-4 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital.corridor | 61 | 4.6% | 0.0% | 0.0% | 26.2% | 3.4% | 0.0% | 2.3% | 22.9% | 72 px | 0-4 | 3 | 0 | 1 | FAIL (touch, choice, ratio, px) |
| main | hospital.dayroom | 61 | 1.8% | 0.0% | 0.0% | 26.2% | 0.3% | 0.0% | 1.6% | 24.3% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital.cafeteria | 61 | 3.0% | 0.0% | 0.0% | 26.2% | 2.6% | 0.0% | 1.6% | 35.8% | 72 px | 0-3 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital.garden | 61 | 4.4% | 0.0% | 0.0% | 26.2% | 3.9% | 0.0% | 2.7% | 33.3% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital.exit | 61 | 10.4% | 0.0% | 0.0% | 26.2% | 7.8% | 23.0% | 6.8% | 38.7% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward | 61 | 22.7% | 21.6% | 0.0% | 100.0% | 0.6% | 0.0% | 2.2% | 25.5% | 77 px | 1-5 | 3 | 0 | 1 | FAIL (touch, choice, ratio, px) |
| main | ward.art | 61 | 1.0% | 0.0% | 0.0% | 26.2% | 0.5% | 0.0% | 0.4% | 30.7% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward.dorm | 61 | 1.5% | 0.0% | 0.0% | 26.2% | 1.0% | 0.0% | 0.8% | 13.0% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward.corridor | 61 | 2.4% | 0.0% | 0.0% | 26.2% | 1.5% | 3.3% | 1.1% | 30.7% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward.courtyard | 61 | 8.8% | 0.0% | 0.0% | 26.2% | 7.4% | 21.3% | 5.0% | 20.9% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward.exit | 61 | 11.1% | 0.0% | 19.7% | 26.2% | 7.0% | 23.0% | 4.2% | 17.8% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital_late | 61 | 9.8% | 0.0% | 0.0% | 26.2% | 9.5% | 21.3% | 6.0% | 41.8% | 72 px | 0-4 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital_late.cafe | 61 | 0.8% | 0.0% | 0.0% | 26.2% | 0.2% | 0.0% | 0.5% | 33.4% | 72 px | 0-3 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital_late.quiet | 61 | 2.2% | 0.0% | 0.0% | 26.2% | 0.3% | 0.0% | 0.2% | 28.3% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | hospital_late.exit | 61 | 10.3% | 0.0% | 0.0% | 26.2% | 10.1% | 26.2% | 7.0% | 38.0% | 72 px | 0-3 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| main | ward_late | 61 | 2.9% | 0.0% | 0.0% | 26.2% | 1.3% | 0.0% | 5.6% | 19.8% | 72 px | 0-4 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward_late.treat | 61 | 2.6% | 0.0% | 0.0% | 26.2% | 0.2% | 0.0% | 0.8% | 29.6% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward_late.dorm | 61 | 1.6% | 0.0% | 0.0% | 26.2% | 1.0% | 0.0% | 0.8% | 13.3% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| main | ward_late.exit | 61 | 1.7% | 0.0% | 0.0% | 26.2% | 0.7% | 0.0% | 0.9% | 23.4% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | jordan | 61 | 1.1% | 0.0% | 0.0% | 26.2% | 0.5% | 0.0% | 0.5% | 29.3% | 89 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio) |
| gospel | jordan.baptism | 125 | 1.0% | 0.0% | 0.0% | 12.8% | 1.0% | 0.0% | 2.4% | 31.7% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| gospel | jordan.wilderness | 125 | 0.3% | 0.0% | 0.0% | 12.8% | 0.3% | 0.0% | 0.0% | 24.0% | 72 px | 0-2 | 1 | 0 | 1 | FAIL (touch, choice, ratio, px) |
| gospel | jordan.nazareth | 125 | 0.9% | 0.0% | 0.0% | 12.8% | 0.9% | 0.0% | 0.8% | 16.2% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | galilee | 125 | 0.9% | 0.0% | 0.0% | 12.8% | 0.9% | 0.0% | 0.3% | 47.6% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | galilee.capernaum | 125 | 0.8% | 0.0% | 0.0% | 12.8% | 0.8% | 0.0% | 0.6% | 25.1% | 81 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | galilee.mount | 125 | 1.6% | 0.0% | 0.0% | 12.8% | 1.6% | 0.8% | 0.6% | 34.9% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | galilee.storm | 125 | 0.8% | 0.0% | 0.0% | 12.8% | 0.8% | 0.0% | 0.4% | 28.6% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | road | 125 | 0.8% | 0.0% | 0.0% | 12.8% | 0.8% | 0.0% | 0.4% | 17.6% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | road.loaves | 125 | 3.8% | 0.0% | 0.0% | 12.8% | 3.8% | 11.2% | 0.8% | 40.7% | 72 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | road.entry | 125 | 1.0% | 0.0% | 0.0% | 12.8% | 1.0% | 0.0% | 0.6% | 59.2% | 72 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | jerusalem | 125 | 1.3% | 0.0% | 0.0% | 12.8% | 1.3% | 0.0% | 0.5% | 42.6% | 77 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | jerusalem.gethsemane | 125 | 2.2% | 0.0% | 0.0% | 12.8% | 2.2% | 0.0% | 1.0% | 35.6% | 126 px | 0-3 | 3 | 0 | 0 | FAIL (touch, choice, ratio) |
| gospel | jerusalem.trial | 125 | 0.7% | 0.0% | 0.0% | 12.8% | 0.7% | 0.0% | 0.4% | 22.1% | 72 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | jerusalem.golgotha | 61 | 1.6% | 0.0% | 0.0% | 26.2% | 0.6% | 0.0% | 0.7% | 34.9% | 99 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio) |
| gospel | jerusalem.tomb | 125 | 1.2% | 0.0% | 0.0% | 12.8% | 1.2% | 0.0% | 0.7% | 32.1% | 72 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| gospel | jerusalem.road | 125 | 1.9% | 0.0% | 0.0% | 12.8% | 0.4% | 0.0% | 0.8% | 21.4% | 72 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| squadron | base | 125 | 1.3% | 0.0% | 0.0% | 12.8% | 1.3% | 0.0% | 0.4% | 38.7% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| squadron | base.c02 | 125 | 0.9% | 0.0% | 0.0% | 12.8% | 0.9% | 0.0% | 1.6% | 42.8% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | base.c03 | 125 | 2.3% | 0.0% | 0.0% | 12.8% | 2.3% | 0.0% | 1.7% | 28.5% | 72 px | 0-3 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | air | 125 | 1.1% | 0.0% | 0.0% | 12.8% | 1.1% | 0.0% | 0.3% | 48.1% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| squadron | air.c05 | 125 | 3.5% | 0.0% | 0.0% | 12.8% | 3.5% | 11.2% | 11.3% | 58.3% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | air.c06 | 125 | 0.9% | 0.0% | 0.0% | 12.8% | 0.9% | 0.0% | 0.8% | 39.2% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | city | 125 | 2.9% | 0.0% | 0.0% | 12.8% | 2.9% | 10.4% | 1.1% | 50.2% | 72 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| squadron | city.c08 | 125 | 0.4% | 0.0% | 0.0% | 12.8% | 0.4% | 0.0% | 0.9% | 43.7% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | city.c09 | 125 | 1.0% | 0.0% | 0.0% | 12.8% | 1.0% | 0.0% | 0.3% | 50.5% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| squadron | city.c10 | 125 | 0.2% | 0.0% | 0.0% | 12.8% | 0.2% | 0.0% | 0.3% | 29.7% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | escape | 125 | 0.6% | 0.0% | 0.0% | 12.8% | 0.6% | 0.0% | 0.5% | 36.9% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| squadron | escape.c12 | 125 | 1.9% | 0.0% | 0.0% | 12.8% | 1.9% | 0.8% | 5.7% | 39.2% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| squadron | escape.c13 | 125 | 1.7% | 0.0% | 0.0% | 12.8% | 0.4% | 0.0% | 0.8% | 32.9% | 106 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio) |
| squadron | escape.c14 | 125 | 4.4% | 0.0% | 0.0% | 12.8% | 4.4% | 12.8% | 5.3% | 20.8% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | hollow | 61 | 4.9% | 0.0% | 0.0% | 26.2% | 1.5% | 0.0% | 1.7% | 65.0% | 158 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio) |
| ember | hollow.ford | 125 | 1.0% | 0.0% | 0.0% | 12.8% | 1.0% | 0.0% | 0.3% | 14.9% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | hollow.inn | 125 | 1.1% | 0.0% | 0.0% | 12.8% | 1.1% | 0.0% | 0.4% | 25.6% | 72 px | 0-2 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | north | 125 | 0.6% | 0.0% | 0.0% | 12.8% | 0.6% | 0.0% | 0.3% | 68.2% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | north.pass | 125 | 0.3% | 0.0% | 0.0% | 12.8% | 0.3% | 0.0% | 0.8% | 26.4% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| ember | deeps | 125 | 0.2% | 0.0% | 0.0% | 12.8% | 0.2% | 0.0% | 1.5% | 66.8% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | deeps.falls | 125 | 1.5% | 0.0% | 0.0% | 12.8% | 1.5% | 0.0% | 0.7% | 13.7% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | marsh | 125 | 0.6% | 0.0% | 0.0% | 12.8% | 0.6% | 0.0% | 0.1% | 24.8% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | marsh.wall | 125 | 0.5% | 0.0% | 0.0% | 12.8% | 0.5% | 0.0% | 1.4% | 21.6% | 72 px | 0-2 | 0 | 0 | 0 | FAIL (touch, choice, px) |
| ember | marsh.stair | 125 | 0.5% | 0.0% | 0.0% | 12.8% | 0.5% | 0.0% | 0.3% | 21.8% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | marsh.plain | 125 | 0.4% | 0.0% | 0.0% | 12.8% | 0.4% | 0.0% | 1.7% | 41.8% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | mountain | 125 | 2.9% | 0.0% | 0.0% | 12.8% | 2.9% | 0.0% | 1.7% | 16.7% | 72 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio, px) |
| ember | mountain.spring | 125 | 1.1% | 0.0% | 0.0% | 12.8% | 1.1% | 0.0% | 0.8% | 8.8% | 149 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio) |
| ember | mountain.keeper | 125 | 0.7% | 0.0% | 0.0% | 12.8% | 0.7% | 0.0% | 0.7% | 12.4% | 151 px | 0-2 | 1 | 0 | 0 | FAIL (touch, choice, ratio) |
| ember | mountain.taken | 125 | 1.0% | 0.0% | 0.0% | 12.8% | 1.0% | 0.0% | 0.7% | 36.4% | 72 px | 0-3 | 2 | 0 | 0 | FAIL (touch, choice, ratio, px) |

### Hotspots by anchor and archetype, 16:9/36

| anchor / archetype | hotspots seen | with a drawn object to compare | touch area over 1.5 x object |
|---|---|---|---|
| actor/person | 47 | 38 | 38 |
| pos/feature | 1 | 0 | 0 |
| pos/object | 3 | 0 | 0 |
| thing/door | 11 | 11 | 1 |
| thing/feature | 21 | 16 | 5 |
| thing/figure | 2 | 1 | 1 |
| thing/object | 31 | 21 | 14 |
| thing/person | 25 | 21 | 9 |
| waypoint/door | 84 | 73 | 71 |
| waypoint/object | 1 | 0 | 0 |
| waypoint/person | 1 | 0 | 0 |

### Largest touch-to-object ratios (area), 16:9/36 (top 15)

| ratio | run | scene | hotspot | anchor | touch px2 | object px2 | radius_m |
|---|---|---|---|---|---|---|---|
| 37.2 | main | hospital_late.quiet | hospital_late.quiet.nightlight | thing/object | 7190 | 193 | 0.80 |
| 33.6 | main | hospital_late.quiet | hospital_late.quiet.nightlight_b | thing/feature | 44809 | 1331 | 0.80 |
| 27.6 | main | ward.exit | ward.exit.talent_lamp | thing/object | 119295 | 4328 | 0.80 |
| 22.0 | main | ward_late | ward_late.stage_lamp | thing/feature | 8139 | 369 | 0.80 |
| 18.5 | gospel | road.loaves | road.loaves.baskets | thing/object | 171431 | 9248 | 1.20 |
| 8.9 | ember | marsh | marsh.lights | thing/feature | 18609 | 2078 | 1.40 |
| 7.5 | gospel | jordan.wilderness | jordan.wilderness.fires | thing/person | 4886 | 652 | 1.00 |
| 7.3 | main | ward.corridor | ward.corridor.king | actor/person | 4076 | 561 | 0.80 |
| 7.1 | gospel | galilee.mount | galilee.mount.crowd | actor/person | 157489 | 22211 | 1.20 |
| 7.0 | squadron | city | city.medkit | thing/person | 76683 | 10918 | 0.90 |
| 6.3 | main | hospital | hospital.monitor | thing/feature | 8875 | 1404 | 0.80 |
| 6.0 | ember | hollow | hollow.ember_bowl | thing/object | 103414 | 17345 | 0.90 |
| 4.9 | squadron | city.c09 | city.c09.medal | thing/person | 91240 | 18612 | 0.90 |
| 4.0 | ember | deeps.falls | deeps.falls.boat | actor/person | 129879 | 32498 | 0.90 |
| 3.9 | gospel | galilee.storm | galilee.storm.beacon | thing/person | 36266 | 9389 | 1.20 |

## Configuration 20:9/36 (aspect / pad size %)

| | scenes | samples | touch mean | touch median | median while selectable | any selectable | at least 50% | choice mean | choice at least 25% | visual (hotspot objects) | visual (all things and people) | smallest target | scenes passing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Main run | 36 | 2196 | 3.6% | 0.0% | 7.9% | 30.9% | 0.0% | 2.3% | 3.3% | 1.9% | 33.4% | 72 px | 0 / 36 |
| Gospel | 17 | 1997 | 1.1% | 0.0% | 5.8% | 13.6% | 0.0% | 0.9% | 0.7% | 0.6% | 29.5% | 72 px | 0 / 17 |
| Squadron | 14 | 1750 | 1.3% | 0.0% | 7.8% | 12.8% | 0.0% | 1.3% | 1.0% | 2.0% | 37.3% | 72 px | 0 / 14 |
| Ember | 15 | 1811 | 0.8% | 0.0% | 4.2% | 13.3% | 0.0% | 0.7% | 0.0% | 0.7% | 28.4% | 72 px | 0 / 15 |
| **All** | 82 | 7754 | 1.8% | 0.0% | 6.5% | 18.2% | 0.0% | 1.4% | 1.3% | 1.3% | 32.1% | 72 px | 0 / 82 |

Scenes meeting each target: touch >=50% in 80% of samples 0 of 82; choice >=25% in 80% of samples 0; no region over 1.5 x its object 12; smallest target >=88 px 7; no pad overlap 82. Median over scenes of the scene's mean touch coverage: 1.2%; of the scene's median while selectable: 6.5%.

## Configuration 16:9/30 (aspect / pad size %)

| | scenes | samples | touch mean | touch median | median while selectable | any selectable | at least 50% | choice mean | choice at least 25% | visual (hotspot objects) | visual (all things and people) | smallest target | scenes passing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Main run | 36 | 2196 | 4.7% | 0.0% | 9.6% | 30.9% | 0.5% | 3.1% | 5.2% | 2.5% | 35.3% | 72 px | 0 / 36 |
| Gospel | 17 | 1997 | 1.4% | 0.0% | 7.9% | 13.6% | 0.0% | 1.2% | 0.7% | 0.7% | 32.8% | 72 px | 0 / 17 |
| Squadron | 14 | 1750 | 1.8% | 0.0% | 10.5% | 12.8% | 0.0% | 1.7% | 2.5% | 2.3% | 40.9% | 72 px | 0 / 14 |
| Ember | 15 | 1811 | 1.1% | 0.0% | 5.7% | 13.3% | 0.0% | 1.0% | 0.1% | 0.9% | 30.3% | 72 px | 0 / 15 |
| **All** | 82 | 7754 | 2.3% | 0.0% | 8.1% | 18.2% | 0.2% | 1.8% | 2.3% | 1.6% | 34.7% | 72 px | 0 / 82 |

Scenes meeting each target: touch >=50% in 80% of samples 0 of 82; choice >=25% in 80% of samples 0; no region over 1.5 x its object 11; smallest target >=88 px 8; no pad overlap 82. Median over scenes of the scene's mean touch coverage: 1.6%; of the scene's median while selectable: 8.3%.

## Configuration 16:9/42 (aspect / pad size %)

| | scenes | samples | touch mean | touch median | median while selectable | any selectable | at least 50% | choice mean | choice at least 25% | visual (hotspot objects) | visual (all things and people) | smallest target | scenes passing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Main run | 36 | 2196 | 4.1% | 0.0% | 8.8% | 30.9% | 0.1% | 2.6% | 4.6% | 2.1% | 34.4% | 72 px | 0 / 36 |
| Gospel | 17 | 1997 | 1.2% | 0.0% | 6.6% | 13.6% | 0.0% | 1.1% | 0.8% | 0.6% | 31.1% | 72 px | 0 / 17 |
| Squadron | 14 | 1750 | 1.5% | 0.0% | 9.0% | 12.8% | 0.0% | 1.4% | 1.8% | 2.1% | 38.9% | 72 px | 0 / 14 |
| Ember | 15 | 1811 | 1.0% | 0.0% | 4.9% | 13.3% | 0.0% | 0.9% | 0.0% | 0.8% | 29.3% | 72 px | 0 / 15 |
| **All** | 82 | 7754 | 2.0% | 0.0% | 7.4% | 18.2% | 0.0% | 1.5% | 1.9% | 1.4% | 33.4% | 72 px | 0 / 82 |

Scenes meeting each target: touch >=50% in 80% of samples 0 of 82; choice >=25% in 80% of samples 0; no region over 1.5 x its object 12; smallest target >=88 px 6; no pad overlap 82. Median over scenes of the scene's mean touch coverage: 1.3%; of the scene's median while selectable: 7.5%.

