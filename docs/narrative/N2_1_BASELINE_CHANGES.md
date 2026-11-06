# N2.1: what changed in the baselines and the pinned checks

Work package N2.1 of the one-PC plan (selection open for the whole scene, `docs/parallel-development/INTERACTION_DESIGN.md` section 2). Branch `wip/narr-n2-1`, 6 November 2026.

## The event baseline (`tests/test_run_tracks_safety.gd`)

**Unchanged; not re-recorded.** The four recorded runs (`main_misses`, `main_second_route`, `main_held`, `gospel_laps`) drive `RunEngine` and `RunHotspots` directly and pick through `RunEngine.choose()` inside the route window. N2.1 changes what the run scene passes (`selection_open()`), not the engine, so every event and cue line is identical: `--filter run_tracks_safety`, 15 checks, 0 failures, 0 SCRIPT ERROR. `tests/fixtures/track_scenes/baseline_runs.json` is untouched.

## Checks that pinned the old window or the old numbers, and how they changed

| Test | Old check | New check | Why |
|---|---|---|---|
| `tests/test_hotspots_data.gd` `test_the_two_to_four_rule_and_the_single_default` (renamed `..._two_to_eight_...`) | five hotspots available at the start are refused ("5 hotspots are available") | eight fit; nine are refused ("9 hotspots are available at the start; a scene shows 2 to 8") | the cap of choices is 8 (lead ruling 1) |
| `tests/test_hotspots_data.gd` `test_a_hotspot_is_normalised_with_the_contract_defaults` | `min_px >= 72` | `min_px >= 88` | lead ruling 3 |
| `tests/test_hotspots_data.gd` `test_routes_anchors_sizes_and_kinds_are_checked` | "min_px must be at least 72" for 40 px | "min_px must be at least 88" for 40 px and for 72 px | lead ruling 3; the design asks that 72 now fails |
| `tests/test_hotspots_view.gd` `test_a_touch_target_is_never_under_min_px_and_stays_inside_the_view` | every target at least 72 px | at least 88 px | lead ruling 3 |
| `tests/test_hotspots_view.gd` `test_hotspot_items_carry_the_decision_time_and_the_outcome` | "only the table is on show in block 0" (ward) | in block 0 the table and every choice of the room are on show, and a choice touched then still waits for the lock at the last block's decision | selection is open for the whole scene |
| `tests/test_run_rail_scene.gd` (two places) | "the hotspots go out with the window": nothing on show at beat 0.4 of the next scene | the old scene's hotspots are gone and the new scene's are on show from its first beat | same |
| `tests/test_run_laps.gd` `test_the_scene_plays_both_laps_of_a_path_scene_and_shows_the_hotspots_in_the_second_only` (renamed `..._in_both`) | no hotspot on show at beat 55 of a path scene's first lap; two to four in the second | two to eight on show in both laps; the engine's route window is still the second lap's only | same, and the cap of 8 |

| `tests/test_gospel.gd` `test_a_result_switches_the_pieces_the_tables_fall_and_the_next_scene_starts_clean` | the money-changers' tables cannot be touched at beat 51 of the first lap | they can (selection open), and the engine's route window is still closed in the first lap | selection is open for the whole scene; the touch waits for the second lap's lock |
| `tests/test_minigame_lifecycle.gd` `test_a_scene_may_raise_its_cap_and_the_default_stays_four` (renamed `..._default_is_eight`) | five hotspots break the default cap of 4; `max_available` 5 allows them | nine break the default cap of 8; `max_available` 9 allows them; five fit | the cap of 8 |

No check of `test_hotspots_engine`, `test_hotspots_scene`, `test_hotspots_any_window`, `test_choice_*`, `test_heralds`, `test_port_*` or `test_narrative_*` needed a change.

Also changed in code, outside the pinned checks: `RunHotspots.begin_lap` keeps a final-window pick across a track scene's lap (an activity or the wizard touched after its block's decision is still cleared, which `test_run_tracks_engine` pins and still passes).

## Measured (Warehouse, 6 scenes, 16:9, 36% pads, `tools/run/coverage_audit.gd`)

| | before | after |
|---|---|---|
| samples with anything selectable | 42.1% | 100.0% |
| touch mean / median | 5.1% / 0.0% | 14.9% / 11.9% |
| choice mean | 4.5% | 10.0% |
| smallest target | 72 px | 88 px |
| scenes with no region over 1.5x its object | 1 of 6 | 0 of 6 (objects under 88 px are widened to 88 plus margin; T5b exempts them, the audit does not yet) |
| pad overlap | none | none |

## Decisions where the document and the code disagreed

- **Where the window lives.** `RunHotspots.select(id, block, final_open)` and `shown(block, final_open)` keep their meaning ("may final-window choices be touched now"). The engine's own callers still pass its route window, so `RunEngine.choose()` and every engine-level test and the event baseline are unchanged; the run scene passes the port's `selection_open()`. No engine edit was needed.
- **No port request yet.** The director's header says nobody calls `request()` before N2.2. N2.1 keeps the engine's commit (the director observes it as today); the pick is `RunHotspots.selected`. The seam N2.2 fills is in `RunPlay` (`choice_request_fn`, `choice_cancel_fn`, `choice_closed`, `hotspot_deselect`, `show_refused`).
- **A track scene's laps before the doors open.** `RunHotspots.begin_lap` used to clear the pick at every lap. It now keeps it, so a pick made before `doors_from_lap` waits for the first departure lap (contract rule: a request on a lap that is no departure lap stays pending). On an open lap an exit pick ends the lap anyway, so nothing else changes. Track scenes are off in every baseline.
- **The 88 px floor against the 24 px margin (A4).** An object less than 40 px across cannot meet both. The 88 px floor wins: the touch rectangle is widened about the object's middle. Such objects are rare at the run's camera distances; the coverage audit reports them.
- **No visual bounds.** A hotspot on an empty spot or a waypoint with nothing drawn (no staged door) keeps only the ring's circle (88 px at least): the old metre rectangle round nothing is gone (3.6, "no invisible hitboxes"). The card table (claim look, a minigame) keeps its old region.
- **Overlap between two choices** is settled by the existing nearer-middle rule of `HotspotView.hit` (now measured from the middle of each touch rectangle); no layout pass pushes regions apart. 7.1's 16 px gap is not enforced.
- **HUD.** The pause button rejects taps (`hotspot_tap`). The crowd meter is not interactive and is left to the audit, which already removes it from the world.
- **Lock-window refusal.** In the run the lock is the engine's commit at beat 60.5, so a choice is already committed when the player taps; the tap is refused against the choices still standing (`RunHotspots.staged`), and the object recoils for 0.4 s (`HotspotView.REFUSE_S`, the claim look's refusal drawing, without the dark wash).
- **The wizard** (early window, blocks 0 and 1) shares the one selection slot: picking him replaces an earlier pick, and after his commit (pass or shrug) the slot is empty again. The design keeps him outside the port (ruling 15); N2.2 decides more.
- **A touched person keeps the touch's act** (`_touched_actor`), so a pick on a person at beat 2 holds that person's scene cast lines for the rest of the scene. Unchanged rule, longer effect.
- **Generators.** `tools/run/hotspots_common.py` (`add(min_px=88)`), `tools/content/make_gospel.py` and `tools/paths/make_squadron.py` default to 88; the path JSON files were edited in place (only `min_px`). `tools/run/make_ember.py` (art stream, ruling 26) still writes 72 at line 179: regenerating Ember with it would fail the new floor. One-line change for the art stream or the lead. `tools/narrative/graph.py` still reads `max_hotspots` with a default of 4 (narrative tools, not this package).
