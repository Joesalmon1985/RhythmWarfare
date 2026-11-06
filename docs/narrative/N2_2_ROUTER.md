# N2.2: the quest router in the run

Work package N2.2 of the one-PC plan, branch `wip/narr-n2-2`, 6 November 2026. Design: `docs/parallel-development/NARRATIVE_GRAPH.md` (section 3) and `LEAD_RULINGS.md` (rulings 15 to 20).

## What a player can do now

- Every quest entrance that exists is a request through the port, taken at the lap's end. A missed block never stops it or changes where it goes.
- Leaving a quest (an ending's way back, the pause menu's "Leave this path", or a return object once N2.5 adds them) lands on the hub of the location the quest was entered from. Today that is always the Warehouse Floor, because the only entrances are in the Warehouse.
- Entering a quest again resumes at the scene that was left. The quest's own flags, and the Bassment's items, come back with it. A completed quest restarts at its first scene and stays completed.
- Route state is saved in the run save and survives a restart. An old save keeps everything it had, and a quest whose path already has an ending starts out completed.
- The Bassment can also be entered from a hub at the lap's end by a hotspot whose route is `"bassment"`. This is proven with test fixtures; the content arrives in N2.4.

## How a pick travels (all in `src/run/run_play.gd`, block "THE ROUTER IN THE RUN")

1. **Run start.** `_setup_router(start)` runs in `_ready`, after `run_started()` and after the run's flags are set:
   - It builds a `QuestRouter` from `NarrativeGraph.cached()` (one build per session) and a `NarrativeRunStore` on `Session.run_progress`.
   - It calls `router.load_state(store.extra())`. That load also migrates old saves.
   - It calls `router.start_run("<path>/<first scene>")`, then `router.attach(port())`. Attaching connects `request_closed`, `deferred` and `switched`, and sets the port's default.
   - It connects `router.committed` to `_on_route_committed` and `port().request_closed` to `_on_port_closed`.
   - It sets `choice_request_fn = _route_pick`, sets `choice_cancel_fn` to `port().cancel`, and sets `hotspots.ungated_quest_routes = true`.
2. **Pick.** The path is `hotspot_select`, then `_choice_picked`, then `_route_pick(id)`.
   - `_route_pick` calls `router.destination_for(id)`, then `port().request(dest)`, then `router.hold(id, dest)`. The router computes the change and holds it against the request id; nothing committed changes.
   - Return value `> 0`: the request id. `0`: the port refused at once; the object recoils and the previous pick comes back.
   - Return value `-1`: the port does not carry this pick. That is the case for the wizard (early window, legacy), a seat at a table (an activity), an object the graph does not know, and a hub's Bassment entrance, which RunPlay holds itself. The single pick slot is still respected: a port request that was pending is cancelled.
3. **Change of mind.** A second pick replaces the first (`request_closed(old, replaced)`). `hotspot_deselect` cancels the request. `router.discard` drops the held change. `_on_port_closed` then calls `choice_closed`, which deselects the object and makes it recoil if the reason was unavailable. The committed state is untouched.
4. **Lock and switch.** The director locks the request at the departure lap's lock.
   - On `switched`, the router's handler calls `router.commit(id, landed)`. This is the only place route state changes. The change is computed from `landed`, and recomputed if `fallback` is set. The router saves, then calls `set_default(router.default_destination())`, then emits `committed`.
   - `_on_route_committed` then restores the entered quest's flags (`restore_flags`) and makes sure a pending `keep:` flag is on disk.
5. **The `keep:` writes move to `switched`.** `_on_hotspot_commit` no longer saves at the lock while the router is on. It marks `_keep_unsaved`, and the router's save at the next `switched` writes the flag (`_after_route_commit`). The flag is still in memory from the lock, so gameplay is unchanged.
6. **Paths.** A quest entry into a path is resolved by the director into the route `path:<id>` with a start scene, and `_path_swap` starts there. A return to `main/<hub>` becomes `run:warehouse` with that hub as start.
   - Neither needs a director change.
   - The director's `path_data_fn` is now `_run_data_of`. It reads the main run's data lazily when the run began inside a path, and reads a shipped path's data lazily if no portal preloaded it.

## The save as built

- **Where.** The `narrative` key of `user://story_run.json`, written by `NarrativeRunStore.save()`, which sets `progress.data["narrative"]` and calls `RunProgress.save()`. That save writes `.tmp` and then renames it, so it is atomic. The file's `version` stays 2; the key carries its own `version: 1`.
- **Fields.** `RouteState.to_dict()`: `location`, `quest`, `entry_origin`, `checkpoint`, `quest_progress` (per quest: `scene`, `completed`, `visits`, plus `flags` for a path or `items` for the Bassment), and `history` (at most 32 entries).
- **Old save, no `narrative` key.** It loads with the default state. A quest whose `paths.<id>.endings` is not empty starts out completed. Nothing else in the file changes, and the key is added at the first save.
- **Repair.** A state with no location gets the location of the scene it stands on. This fixed a repair warning on every fresh save.
- **Newer version.** A `narrative` key with a newer version is ignored and never overwritten.
- **Save made mid-quest.** It is closed on load: the run starts as usual and the quest's progress is kept. `closed_on_load` now survives `start_run`.
- **Run started inside a quest** (the level list's path worlds, a retry inside a path). Settled here: the quest is entered from the hub of the location the save was last in. If the save was closed mid-quest, that is the old checkpoint, so a retry keeps it. Otherwise it is the Warehouse Floor.

## Decisions

- **The router is on in the game.** It is off with `RW_NARRATIVE=0`, with `RW_PATH_REMAP` (a remapped path is outside the graph), in a path the graph does not know (the stub), or if the graph does not load (a warning). When off, the run behaves exactly as in N2.1.
- **No rhythm gate on entering or leaving a quest.** A touched hotspot whose success route is `path:<id>`, `bassment` or `run:warehouse` always commits as a success while the router is on (`RunHotspots.ungated_quest_routes`, used by `commit_final`). Its success effects run, its failure outcome is never taken, and its destination has no `on_miss`.
  - One exception: when the hotspot's failure leads the same way as its success, the authored failure outcome stays, because it is no gate. The case today is the Ember pool's "snatched" ending: a miss still leaves by `run:warehouse` with its cinematic, which `test_run_ember` pins.
  - Ordinary scene choices keep their miss route; the router sends it as `on_miss`.
- **The three existing Warehouse portals** (the star, the radio, the ember) keep their availability flags (`wh_saw_floor`, `wh_vip_pass`) as an extra way in, as ruling 15 says. A miss no longer refuses them: before, the failure outcome "flickers out" and the scene went on; now the player enters.
- **A hotspot's own `commit_final` effects** (energy, flags, cinematic) still run when the port carries the route. They are gameplay results of the block (contract section 5). For a quest entrance or return they are the success effects, which are consistent with going.
- **The pause menu's "leave".** On a departure lap with selection open, it is a port request: the hidden leave edge, a `quest_return` to the checkpoint (`_route_leave_now`). It replaces the player's pick, which deselects.
  - On an earlier lap, or after the lock, the old mechanism runs (`force_leave` at beat 61). `_path_swap` aims that hand-off at the checkpoint, and the director reports it as a fallback or late landing, which the router recomputes from `landed`.
  - The same `_path_swap` rule covers an ending's way back that the player did not touch: the hotspot default was committed by the engine and observed by the director.
- **The wizard** shares the single pick slot. Picking him withdraws a pending request. He stays outside the port, and his entry is committed by `commit_legacy(object)` when the trial begins.
  - `commit_legacy` no longer re-reads the object's flags, because his own success sets `wh_wizard_met` before the trial begins.
  - He now resumes the saved passage, like every entrance.
- **The port's default.** It is set from the router at the run's start and on every switch. One guard is needed: when the player's own choice keeps the scene (a seat at a table committed in the last block), `_on_lock_point` does not hand the lock to the director. Otherwise the default would take the run away from the table. This behaves exactly as before N2.2.
- **The developer overlay line.** The F3 line has a route part (`_route_debug`): location, quest and checkpoint.

## The Bassment: the spike of ruling 20 and the decision

**Spike answer.** The Bassment can be entered at a lap's end and left back to the checkpoint without any change to the director, but not through the port. The director refuses `bassment/*` at once, and it never emits `switched` for the trial's entry or exit.

**Decision (lead, 6 November 2026; this closes ruling 20): the Bassment stays outside the port, and a Bassment change is always a cut.**

- **Entry.** `_route_pick` holds a hub entrance with route `"bassment"` (`_bassment_pick`) and preloads the pack silently. At the lap's lock, a wrapper RunPlay puts around the engine's `lock_hook` (`_on_lock_point`) sees the committed route `"bassment"` and arms the trial (`_arm_trial_at_lap_end`):
  - it calls `director.excursion(&"armed")`, so nothing locks;
  - the trial takes the pads 3.25 beats before the boundary, as the wizard's entry does;
  - the trial begins on the boundary, and the engine never reaches its commit.
  - If the trial cannot go, the scene's default exit is taken instead.
- **Commits outside `switched`.** The route state changes when the trial begins (`_route_enter_bassment`: the held destination for the hatch, `commit_legacy` for the wizard), when the dungeon moves to a new passage (`_trial_route_sync`), and when it is left (`trial_leave`, which lands on the checkpoint hub and commits the return).
  - Items are restored through `TrialScene.begin(..., carried)`, which passes them to `TrialEngine.begin` and `TrialFlow.begin`.
  - Death passages are not saved as the scene, so a re-entry resumes alive.
- **Reason.** The dungeon has its own engine and its own block clock, with no laps or boundaries the port can lock. Putting it behind the port would need new director states for "away" transitions, for no musical gain, because the hand-off is a cut either way. These commits extend the declared exception `legacy_wizard_entrance`: they are the only route state changes not made on `switched`.

## Graph tools

- **`tools/narrative/graph.py` and `src/narrative/narrative_graph.gd`, kept identical:**
  - The route `"bassment"` is a quest entry to `bassment/<start>`. It is not marked legacy on a `trial_gate` scene; only the wizard's passage-number route is.
  - An entrance object whose overlay status is `existing` is "authored". The hotspot's own edges are dropped and the overlay's ungated edge stands for it, with status `existing`. This applies to hub entrances and `extra_routes` quest entries.
- **The cap.** `graph.py`'s cap check reads a node without `max_hotspots` as the default cap of 8 (it was 4); hubs may go up to 10. There are new Python tests in `tools/narrative/test_graph.py`, class `N22Tools`.
- **`tools/run/make_ember.py`** writes `min_px` 88. Regenerating Ember into a temporary folder gives files identical to `content/paths/ember`, so nothing was rewritten.
- **Test fixtures.** `HotspotContract.extra_rows` adds hotspot rows as the content is read, both in `RunData` and in `NarrativeGraph`. It is empty in the game.

## What N2.4 and N2.5 must author

- **A path entrance in a hub** (N2.4). Add one hotspot row in `content/run/hotspots/<world>.json` on the hub scene:
  - the id from `content/narrative/graph.json` (for example `hospital.enter_gospel`);
  - `on_success.route` `path:<quest>`;
  - the portal rules: `kind` `secret`, `look.available` `pulse`, `repeatable` true, `on_failure` with an energy cost and no route;
  - plus its herald, and in the overlay set the object's `status` to `existing`.
  - A hub over 8 choices needs `max_hotspots` up to 10 on its node in `run.json`.
- **A Bassment entrance in a hub** (N2.4). Same, with `on_success.route` `"bassment"`. Any scene of the main run may carry it; a path may not.
- **A return object in a path scene** (N2.5). Add one row per scene in `content/paths/<quest>/hotspots/<world>.json` with `on_success.route` `run:warehouse` and the id `<quest>.return`. `RunData` now accepts that route in any path scene, and the router aims it at the checkpoint.
- **A visible return in the Bassment** (N2.5). Not built. The dungeon's existing exits (death and victory "wake" choices, the back key) already land on the checkpoint. A visible return is an exit choice (no `to`) in each passage of `content/trial/passages.json`, or one definition that `TrialData` appends to every passage. Either way it reaches `trial_leave`, so no router work is needed.

## Not done or not proven

- No real phone run.
- No audio check of a hatch entry with the real packs. In tests the hand-off is a cut on the virtual clock.
- The wizard's walk to the hatch is not played for a hub's Bassment entrance: there is no `hatch` waypoint outside the Warehouse map, and the passage frame closes on its own.
- An ending's way back that the player did not touch, and a late pause leave, land with `fallback` true instead of a clean lock.

## Tests

`tests/test_narrative_run.gd` runs the real `RunPlay` on its virtual clock with the real director:

- the three routes, with state, save and history checked at every step;
- the save reloaded in the middle of a route;
- an entry after a missed block, and a scene door's miss route;
- an old save migrating, a save closed mid-quest, and a newer version left alone;
- a `keep:` flag saved at `switched`;
- the pause leave through the port;
- the Floor's hatch, with items brought back;
- the on/off switch.

Baselines: none re-recorded (`docs/narrative/N2_2_BASELINE_CHANGES.md`).
