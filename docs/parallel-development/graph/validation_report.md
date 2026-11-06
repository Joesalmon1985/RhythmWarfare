# Validation report: narrative graph, 6 November 2026

Produced by a Python check script that reads `graph/narrative_graph_target.json`, `graph/overlay_proposed.json`, `graph/graph_today.json` and the repository's `content/` folder. The script is a planning tool (it lives outside the repository, in the planning scratch folder); the real validator is `tools/narrative/graph.py` (stage N1.1) and must reproduce these numbers. Everything here is computed on paper from data. Nothing was run in Godot.

Data read: `content/run/run.json` (36 scenes), `content/paths/{gospel,squadron,ember}/run.json` (46 scenes), `content/trial/passages.json` (64 passages), `content/run/track_scenes.json`, `content/run/hotspots/*.json`, `content/paths/*/hotspots/*.json`, `content/music/tracks/*.json`.

## 1. Today: rules 1 and 2 on `graph_today.json`

Rule 1 on today's graph. Fewest player choices from the first scene (The Floor, `warehouse`) to each quest's first scene. A choice is one touched object (or the default taken). Every touch is assumed to be passed. Search state is the scene plus the run flags that gate any edge.

| Quest | Visible options only | Counting the hidden leaves too (pause menu, system back key) | Within five? |
|---|---|---|---|
| Dungeon (Bassment) | 1 | 1 | yes |
| Jesus (gospel) | 25 | 6 | NO |
| Catch-22 (squadron) | 3 | 3 | yes |
| Lord of the Rings (ember) | 25 | 6 | NO |

Rule 1 today: FAIL. 2 of 4 quests are not within five visible choices (Jesus and Lord of the Rings need 25; they get to 6 only by using the hidden back key of the Bassment). This matches the inventory.

Rule 2 on today's graph. Quest entrances offered, by location (any scene of the location):

| Location | bassment | gospel | squadron | ember |
|---|---|---|---|---|
| Warehouse Rave | yes | yes | yes | yes |
| Hospital Ward | no | no | no | no |
| Mental Hospital | no | no | no | no |
| Alien Spaceship | no | no | no | no |
| Hell | no | no | no | no |

Rule 2 today: FAIL. 4 of 20 cells are filled, 16 are empty. The two late worlds offer none either.

## 2. Target: the ten rules on `narrative_graph_target.json`

Target graph: 146 nodes, 960 edges (existing 561, changed 131, proposed 268). By kind: scene 680, quest_entry 42, quest_return 238.

Simplification, stated once: an edge that requires a run flag is treated as unavailable, and an edge that needs a flag to be absent is treated as available. The paper check is therefore conservative for reachability. Flags are the runtime test's job.

### Rule 1. Every quest entry within five choices of the start

Breadth-first search by choice count from `main/warehouse`. One visible option is one choice. Hidden leaves and `on_miss` twins do not count. Run twice: with every visible entrance, and with only the entrances that are not rhythm-gated (the wizard is excluded).

| Quest | Choices, all visible entrances | Choices, ungated entrances only |
|---|---|---|
| bassment | 1 | 1 |
| gospel | 1 | 1 |
| squadron | 1 | 1 |
| ember | 1 | 1 |

Entrance gating audit: 2 entrance edges are rhythm-gated (the wizard, on the Floor and in the Chill-out). They stay as an extra way in beside the ungated Floor entrance of ruling 15; declared exception `legacy_wizard_entrance`. 0 other entrance edges carry a gate. Every other entrance edge has no flag, no pass condition and no `on_miss` twin.

Finding (ruling 15): every hub, the Floor included, has an ungated Dungeon entrance through the port, so every quest is 1 choice from the start without the wizard. Before ruling 15 the Warehouse offered the Dungeon only through the wizard, and the fewest ungated choices were 5 (Floor, Bar, Chill-out, Door, then the Alien Spaceship hub's hatch); now they are 1.

Rule 1: PASS (reported with the legacy wizard exception, which is an extra way in).

### Rule 2. All four quests from each mainline location, and the mainline still continues

For each location: the fewest choices to each quest from its hub, and the worst case over every scene of the location (late worlds included).

| Location | Scenes | Quest | From hub | Worst scene | Worst scene id |
|---|---|---|---|---|---|
| warehouse_rave | 6 | bassment | 1 | 2 | main/warehouse.bar |
| warehouse_rave | 6 | gospel | 1 | 2 | main/warehouse.bar |
| warehouse_rave | 6 | squadron | 1 | 2 | main/warehouse.bar |
| warehouse_rave | 6 | ember | 1 | 2 | main/warehouse.balcony |
| hospital_ward | 10 | bassment | 1 | 2 | main/hospital.corridor |
| hospital_ward | 10 | gospel | 1 | 2 | main/hospital.corridor |
| hospital_ward | 10 | squadron | 1 | 2 | main/hospital.corridor |
| hospital_ward | 10 | ember | 1 | 2 | main/hospital.corridor |
| mental_hospital | 10 | bassment | 1 | 2 | main/ward.dorm |
| mental_hospital | 10 | gospel | 1 | 2 | main/ward.art |
| mental_hospital | 10 | squadron | 1 | 2 | main/ward.art |
| mental_hospital | 10 | ember | 1 | 2 | main/ward.art |
| alien_spaceship | 5 | bassment | 1 | 2 | main/mothership.reactor |
| alien_spaceship | 5 | gospel | 1 | 2 | main/mothership.gallery |
| alien_spaceship | 5 | squadron | 1 | 2 | main/mothership.gallery |
| alien_spaceship | 5 | ember | 1 | 2 | main/mothership.gallery |
| hell | 5 | bassment | 1 | 2 | main/underworld.furnace |
| hell | 5 | gospel | 1 | 2 | main/underworld.court |
| hell | 5 | squadron | 1 | 2 | main/underworld.court |
| hell | 5 | ember | 1 | 2 | main/underworld.court |

Mainline continues after a return (the return lands on the hub; the hub must offer a mainline route):

| Location | Mainline routes from the hub | To |
|---|---|---|
| warehouse_rave | 3 | main/warehouse.balcony, main/warehouse.bar |
| hospital_ward | 5 | main/hospital.corridor, main/ward |
| mental_hospital | 6 | main/hospital, main/ward, main/ward.art, main/ward.dorm |
| alien_spaceship | 5 | main/mothership.gallery, main/mothership.reactor, main/underworld |
| hell | 5 | main/mothership, main/underworld.court, main/underworld.furnace |

Rule 2: PASS. Worst case over all 5 locations x 4 quests x every scene: 2 choices. 20 of 20 cells filled.

### Rule 3. Every quest has a working return

For each quest and each of the five origin locations: enter by that location's hub entrance, find every scene reachable inside the quest, and check that each one offers a visible return that lands on that location's hub. Hidden leaves are not counted as the return.

| Quest | Scenes | Scenes with a visible return | Reachable from entry | Landings (one per origin) |
|---|---|---|---|---|
| bassment | 64 | 64 | 64 of 64 | warehouse, hospital, ward, mothership, underworld |
| gospel | 17 | 17 | 17 of 17 | warehouse, hospital, ward, mothership, underworld |
| squadron | 14 | 14 | 14 of 14 | warehouse, hospital, ward, mothership, underworld |
| ember | 15 | 15 | 15 of 15 | warehouse, hospital, ward, mothership, underworld |

Scenes not reachable from the entry inside their quest: none.

Rule 3: PASS. Return objects: 110 (one per quest scene); authored returns kept: 18 edges; hidden leaves kept: 110.

### Rule 4. Mainline locations are traversable

From `main/warehouse`, following mainline scene edges only: 36 of 36 mainline scenes reachable. Unreachable: none.

| Location | Scenes reachable from the start | Of | Hub reaches all its scenes |
|---|---|---|---|
| warehouse_rave | 6 | 6 | yes |
| hospital_ward | 10 | 10 | yes |
| mental_hospital | 10 | 10 | yes |
| alien_spaceship | 5 | 5 | yes |
| hell | 5 | 5 | yes |

Mutual reachability among mainline scenes (components of more than one scene, by locations they join):

| Locations in the component | Scenes |
|---|---|
| warehouse_rave | 6 |
| alien_spaceship, hell | 10 |
| hospital_ward, mental_hospital | 20 |

No mainline route leads back to the Warehouse from any later location (`main/warehouse` reaches the other four locations; none reaches it): confirmed. This is by the owner's decision (no new routes beyond the paired hub links).

Rule 4: PASS.

### Rule 5. Every scene has at least three meaningful choices

A choice is a visible option with a distinct destination. For a scene with `previous_scene` options, the worst case over the possible previous scenes is used. `$checkpoint` counts as one destination. Hidden leaves, `on_miss` twins and options that need a flag are not counted.

| Group | Scenes | Under three | Fewest choices in the group |
|---|---|---|---|
| mainline | 36 | 0 | 3 |
| bassment | 64 | 41 | 1 |
| gospel | 17 | 0 | 3 |
| squadron | 14 | 0 | 3 |
| ember | 15 | 0 | 3 |

Scenes under three that are not covered by a declared exception: 0 . Declared exception `bassment_passages_under_three` lists 41 passages; all 41 really fail (none stale).
Bassment passages by number of choices including the new return: {1: 8, 2: 33, 3: 21, 4: 2}.

Mainline and path scenes reach three only with the proposed routes: `to_hub` on 31 mainline scenes, 17 extra quest entrances on non-hub mainline scenes, `back` on path scenes, and 5 `restart` and 2 second-route edges on path ending and entry scenes (overlay `extra_routes`, marked proposed; the two second routes need review).

Rule 5: EXCEPTION: 41 Bassment passages are reported as a named exception; every other scene has three or more. On paper this only proves distinct destinations exist in the data; whether each is a visible, meaningful object is the coverage audit's and the walk-through's job.

### Rule 6. No unintended dead ends

- Scenes with no visible way out: 0 .
- Scenes not reachable from the start by any route: 0 .
- Quest scenes from which the mainline cannot be reached: 0 .
- Mainline scenes from which the late loops cannot be reached: 0 .
- Late loops (`hospital_late`, `ward_late`, 8 scenes) leave to other mainline scenes: 8 routes (only the proposed `to_hub` routes back to the two hubs). They have no ending: declared terminal component `late_loops_have_no_ending`.

Rule 6: EXCEPTION (late loops declared, nothing else).

### Rule 7. Every reference resolves

1767 references checked: every node id against `run.json`, the three path `run.json` files and `passages.json`; every edge end; every existing object id against the hotspot files (main run and paths); the four reused Warehouse objects; hubs, worlds, entries and completion scenes of the overlay; 82 scenes against `track_scenes.json`; proposed object ids for collisions and duplicates.

Rule 7: PASS (0 unresolved).

### Rule 8. Scene and music metadata valid (partly checkable on paper)

- Scenes with a track assignment: 82 of 82 non-Bassment scenes. The Bassment plays its own pack through `passages.json` (`dd_part1`, fight `dd_part2`).
- Track assignment fields well-formed (a track id, alternate entries named): yes.
- Distinct track ids named in `track_scenes.json`: 61. With a catalogue file in `content/music/tracks/`: 44. Without: 17 (stage I4 of the plan adds the catalogue entries).
- Not checkable on paper: whether a usable pack exists for each track (the packs are outside the repository), beat grids, first-drop times, the sidecars of the music stream.

Rule 8: PARTIAL: references and shape OK on paper; pack and audio metadata could not be checked.

### Rules 9 and 10. Cycles, re-entry, route history and checkpoint (on a paper model of the specified `RouteState`)

These two rules are about behaviour over time, so the paper check is a small model of the specified `RouteState` (the transaction rule of the contract, section 5). It tests the design, not the code. The Godot test of stage N1.3 must do the same on the real classes.

- Random walks: 200 walks of up to 400 requests (80000 requests): 47661 scene moves, 8692 quest entries, 8592 returns, 12026 requests closed before the lock, 3029 failures after the lock. Invariants broken: 0.
  Invariants after every commit: quest, entry origin and checkpoint are all empty or all set; the checkpoint is the hub of the entry origin's location; the location does not change during a quest; the node belongs to the current quest; history is bounded at 32 and ends at the current node; a quest's saved scene belongs to that quest; a closed request leaves the committed state byte for byte unchanged.
- Re-entry, 4 quests x 5 origins = 20 scripted cases (enter, move on one scene, return, re-enter, play to an ending, return, re-enter): 20 pass. Return lands on the origin's hub; re-entry resumes at the scene left; a completed quest restarts at its first scene and keeps `completed`.
- Cycles: the quests have loops by design (the Squadron mission count, the Ember marsh, `back` and `restart` edges). Rule 6 shows every quest scene still reaches the mainline through its own return, so no cycle traps the player. The mainline's only cycles are the late loops (declared) and the proposed paired hub links and `to_hub` routes.

Rule 9: PASS on the model. Rule 10: PASS on the model. These are design checks; the code's proof is the Godot test.

## 3. Informational: objects on the hub scenes against the cap of eight and the hub limit of ten

Not one of the ten rules, but it decides whether the hub scenes can hold their choices. Existing hotspots counted as simultaneously visible (an object that needs a flag and one that needs it absent are never visible together). By lead rulings 1 and 16 the cap of 8 counts choices only and reactive objects are held apart; a hub scene may set `max_hotspots` up to 10. The totals below count every object, choice or not, so they are the worst case.

| Hub | Existing hotspots | Of which visible together | Added choices (entrances + hub link) | Total | Over 8 | Over the hub limit of 10 |
|---|---|---|---|---|---|---|
| main/warehouse | 5 | 4 | 4 | 8 | no | no |
| main/hospital | 4 | 4 | 5 | 9 | by 1 | no |
| main/ward | 5 | 5 | 5 | 10 | by 2 | no |
| main/mothership | 4 | 4 | 5 | 9 | by 1 | no |
| main/underworld | 5 | 4 | 5 | 9 | by 1 | no |

Where the total is above eight, the hub keeps its existing people and props as reactive objects (not capped, ruling 1) and sets `max_hotspots` for any that stay in the old list (up to 10, ruling 16); otherwise a reactive object is merged with an entrance or dropped. That is for the interaction design to decide.

## 4. Summary

| Rule | What | Result | Numbers |
|---|---|---|---|
| 1 | Quests within five choices of the start | PASS with exception (extra way in) | all visible: 1,1,1,1; ungated only: 1,1,1,1 |
| 2 | All four quests from each location | PASS | 20 of 20 cells; hub 1 choice; worst scene 2 |
| 3 | Every quest has a working return | PASS | 110 of 110 quest scenes have a visible return, to the hub of the origin |
| 4 | Mainline locations traversable | PASS | 36 of 36 scenes reachable from the start |
| 5 | Three meaningful choices in every scene | EXCEPTION | 105 of 146 scenes pass; 41 Bassment passages declared |
| 6 | No unintended dead ends | EXCEPTION | 0 scenes without a way out; 0 trapped; late loops declared as terminal |
| 7 | Every reference resolves | PASS | 1767 references, 0 unresolved |
| 8 | Scene and music metadata valid | PARTIAL | 82 of 82 scenes assigned; 17 track ids lack a catalogue file; packs not checkable |
| 9 | Cycles and re-entry behave | PASS on the model only | 200 random walks, 20 scripted re-entry cases |
| 10 | Route history and checkpoint consistent | PASS on the model only | invariants held after every commit and after every closed request |

## 5. What could not be checked on paper

- Rule 5 only proves that three distinct destinations exist in the data. It cannot show that each is a visible, tappable object of adequate size; that is the coverage audit (N1.5, N2.6) and the walk-through.
- Rule 8 is only partly checked: scene-to-track references and their shape are checked; the existence and quality of the packs, beat grids and first-drop times are not, because the packs are outside the repository and the music stream owns the sidecars.
- Rules 9 and 10 are checked on a model of the specified behaviour, not on the code; the Godot test of N1.3 must prove them on `RouteState`, `QuestRouter` and the real director.
- Flags: the check treats every edge that needs a flag as unavailable. Whether a flag-gated edge becomes available during play is not modelled.
- Timing: the transaction rule (state changes only on `switched`) and the lock point cannot be shown on a static graph; conformance cases 1 to 15 and the route tests (N1.6) cover them.
- The object totals on the hub scenes (section 3) are arithmetic on counts, not a layout check.
