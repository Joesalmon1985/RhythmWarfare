# Validation report: narrative graph

Written by `tools/narrative/graph.py`; do not edit, rerun the tool. This replaces the paper check that was made before the tool existed.

Command: `python tools/narrative/graph.py --graph both --export --report docs/parallel-development/graph/validation_report.md`

Data read: `content/run/run.json`, `content/run/hotspots/*.json`, `content/paths/{gospel,squadron,ember}/run.json` and their hotspot files, `content/trial/passages.json`, `content/run/track_scenes.json`, `content/music/tracks/*.json`, and for the target graph `content/narrative/graph.json`. Nothing was run in Godot.

Counting rule for choices (NARRATIVE_GRAPH.md 2.5): a choice is one touched door, person or object, or the default taken. Automatic scenes, hidden options (pause menu, back key), miss twins, options that need a flag or an item the player does not have, and staying in the scene are not choices. Rule 1 follows the flags and items the player picks up on the way (a touch is assumed passed); the other rules use flag-free edges only, which is conservative.

## Today: game data alone

146 nodes, 702 edges (by status {"existing": 702}; by kind {"quest_entry": 5, "quest_return": 138, "scene": 559}).

| Rule | What | Result | Numbers |
|---|---|---|---|
| 1 | Each quest entry within the limit of choices from the start; entry never gated by rhythm or another quest | FAIL | quests within 5 choices: bassment 1, gospel 26, squadron 3, ember 26 (ungated entrances only: none, none, none, none) |
| 2 | All four quests from every mainline location and every scene of it; the mainline continues after a return | FAIL | 0 of 20 cells have an ungated entrance on the hub (4 have one in some scene of the location); worst scene not reachable |
| 3 | Every quest has a working return to the hub of the location it was entered from | FAIL | 0 of 110 quest scenes have a visible return to the checkpoint; 13 have one that lands on a fixed scene (main/warehouse); 97 have none; 0 not reachable from the entry |
| 4 | Mainline locations are traversable | PASS | 36 of 36 mainline scenes reached from the start; components: hospital_ward+mental_hospital (8 scenes); no mainline route leads back to the first location |
| 5 | Every scene has at least the minimum number of choices | FAIL | 2 of 146 scenes have 3 or more choices; 0 excused by exception; 144 under without excuse |
| 6 | No unintended dead ends | FAIL | 0 scenes without a way out; 0 unreachable; 0 trapped in a quest; 8 scenes in 1 terminal component(s) |
| 7 | Every reference resolves | PASS | 930 references checked, 0 unresolved |
| 8 | Scene and music metadata valid | PASS | 82 of 82 non-Bassment scenes assigned; 61 track ids named, 17 without a catalogue file (warning) |
| 9 | Cycles and re-entry behave | FAIL | not modelled: the graph has no checkpoint; 0 cycle(s) that cannot be left |
| 10 | Route history and checkpoint stay consistent | FAIL | not modelled: the graph has no checkpoint |
| cap | Choices shown per scene against the cap (informational check, rulings 1 and 16) | PASS | most choices in one scene: 3 (bassment/20); hubs: hospital 1, mothership 2, underworld 2, ward 2, warehouse 3 |

Summary: pass 3, exception 0 (0 declared exception(s) listed), fail 7, parts not checkable from data 4.

### Rule 1. Each quest entry within the limit of choices from the start; entry never gated by rhythm or another quest

Statement: Rule 1. Each quest's entry is at most `max_choices_to_quest` (default 5) choices from `start`, counted twice: over all visible entrances, and over the entrances that are not gated by a passed block; both must reach every quest within the limit. No entrance edge may be gated by a passed block, by a flag, or name another quest, unless a declared exception lists its object; an exception that lists an object that is not gated (or does not exist) is stale and fails. Hidden leaves, miss twins and options that need a flag do not count as choices; the search follows the flags and items the player picks up on the way.

| Quest | Choices, any entrance | Choices, ungated entrances only | Counting the hidden leaves too |
|---|---|---|---|
| bassment | 1 | not reachable | 1 |
| gospel | 26 | not reachable | 6 |
| squadron | 3 | not reachable | 3 |
| ember | 26 | not reachable | 6 |

Result: **FAIL**. quests within 5 choices: bassment 1, gospel 26, squadron 3, ember 26 (ungated entrances only: none, none, none, none)

Offending (11):
- bassment: not reachable (ungated entrances only; limit 5)
- gospel: 26 choices (any entrance; limit 5)
- gospel: not reachable (ungated entrances only; limit 5)
- squadron: not reachable (ungated entrances only; limit 5)
- ember: 26 choices (any entrance; limit 5)
- ember: not reachable (ungated entrances only; limit 5)
- undeclared gated entrance warehouse.balcony.star in main/warehouse.balcony (gated by a passed block; needs flags wh_saw_floor)
- undeclared gated entrance warehouse.bar.ember in main/warehouse.bar (gated by a passed block; needs flags wh_vip_pass)
- undeclared gated entrance warehouse.booth.radio in main/warehouse.booth (gated by a passed block)
- undeclared gated entrance warehouse.chill.wizard in main/warehouse.chill (gated by a passed block; needs flags wh_wizard_met)
- undeclared gated entrance warehouse.wizard in main/warehouse (gated by a passed block; needs flags wh_wizard_met)

### Rule 2. All four quests from every mainline location and every scene of it; the mainline continues after a return

Statement: Rule 2. Each of the 5 locations offers each of the 4 quests: the hub shows an entrance for every quest that is not gated by a passed block (20 cells); from every scene of the location (late worlds included) every quest is at most `max_choices_to_quest_in_location` (default 2) ungated choices away; and the hub has a mainline exit (a scene route that is neither a `to_hub` nor a hub link), so that after a return the mainline continues.

| Location | Quest | Entrance in some scene | Entrance on the hub | Ungated entrance on the hub |
|---|---|---|---|---|
| warehouse_rave | bassment | yes | yes | no |
| warehouse_rave | gospel | yes | no | no |
| warehouse_rave | squadron | yes | no | no |
| warehouse_rave | ember | yes | no | no |
| hospital_ward | bassment | no | no | no |
| hospital_ward | gospel | no | no | no |
| hospital_ward | squadron | no | no | no |
| hospital_ward | ember | no | no | no |
| mental_hospital | bassment | no | no | no |
| mental_hospital | gospel | no | no | no |
| mental_hospital | squadron | no | no | no |
| mental_hospital | ember | no | no | no |
| alien_spaceship | bassment | no | no | no |
| alien_spaceship | gospel | no | no | no |
| alien_spaceship | squadron | no | no | no |
| alien_spaceship | ember | no | no | no |
| hell | bassment | no | no | no |
| hell | gospel | no | no | no |
| hell | squadron | no | no | no |
| hell | ember | no | no | no |

Worst scene of any location: None ungated choices to a quest (limit 2). Mainline exits of each hub:

| Location | Mainline exits from the hub |
|---|---|
| warehouse_rave | main/warehouse.balcony, main/warehouse.bar |
| hospital_ward | main/hospital.corridor |
| mental_hospital | main/ward.art, main/ward.dorm |
| alien_spaceship | main/mothership.gallery, main/mothership.reactor |
| hell | main/underworld.court, main/underworld.furnace |

Result: **FAIL**. 0 of 20 cells have an ungated entrance on the hub (4 have one in some scene of the location); worst scene not reachable

Offending (164):
- warehouse_rave.bassment: the hub main/warehouse shows no entrance that is not gated (an entrance exists elsewhere in the location)
- warehouse_rave.gospel: the hub main/warehouse shows no entrance that is not gated (an entrance exists elsewhere in the location)
- warehouse_rave.squadron: the hub main/warehouse shows no entrance that is not gated (an entrance exists elsewhere in the location)
- warehouse_rave.ember: the hub main/warehouse shows no entrance that is not gated (an entrance exists elsewhere in the location)
- hospital_ward.bassment: the hub main/hospital shows no entrance that is not gated
- hospital_ward.gospel: the hub main/hospital shows no entrance that is not gated
- hospital_ward.squadron: the hub main/hospital shows no entrance that is not gated
- hospital_ward.ember: the hub main/hospital shows no entrance that is not gated
- mental_hospital.bassment: the hub main/ward shows no entrance that is not gated
- mental_hospital.gospel: the hub main/ward shows no entrance that is not gated
- mental_hospital.squadron: the hub main/ward shows no entrance that is not gated
- mental_hospital.ember: the hub main/ward shows no entrance that is not gated
- alien_spaceship.bassment: the hub main/mothership shows no entrance that is not gated
- alien_spaceship.gospel: the hub main/mothership shows no entrance that is not gated
- alien_spaceship.squadron: the hub main/mothership shows no entrance that is not gated
- alien_spaceship.ember: the hub main/mothership shows no entrance that is not gated
- hell.bassment: the hub main/underworld shows no entrance that is not gated
- hell.gospel: the hub main/underworld shows no entrance that is not gated
- hell.squadron: the hub main/underworld shows no entrance that is not gated
- hell.ember: the hub main/underworld shows no entrance that is not gated
- main/warehouse to bassment: not reachable (limit 2)
- main/warehouse to gospel: not reachable (limit 2)
- main/warehouse to squadron: not reachable (limit 2)
- main/warehouse to ember: not reachable (limit 2)
- main/warehouse.balcony to bassment: not reachable (limit 2)
- ... and 139 more

### Rule 3. Every quest has a working return to the hub of the location it was entered from

Statement: Rule 3. Every quest scene offers a visible return (not hidden, not a miss twin, not flag-locked) whose landing is `$checkpoint`, the hub of the location the quest was entered from, and every quest scene is reachable from the quest's entry inside the quest. A return that lands on a fixed scene fails (it cannot land where the player entered). Hidden leaves never count. For each quest and each origin location with a hub entrance the check is the same, as the landing is the origin's hub.

Quest scenes: 110. With a visible return: 13 (on the checkpoint 0, on a fixed scene 13). Without: 97. Fixed landings of visible returns: {"main/warehouse": 18}. Not reachable from the entry: 0. Hub entrances per quest (origins): {"bassment": 1}. Hidden leaves: 110 (never counted). Authored returns re-pointed: 0.

Result: **FAIL**. 0 of 110 quest scenes have a visible return to the checkpoint; 13 have one that lands on a fixed scene (main/warehouse); 97 have none; 0 not reachable from the entry

Offending (110):
- bassment/13: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/22: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/33: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/39: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/50: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/60: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/63: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/0: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- gospel/jerusalem.tomb: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- gospel/jerusalem.road: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- squadron/escape.c13: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- ember/mountain.spring: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- ember/mountain.keeper: the visible return lands on the fixed scene main/warehouse, not on the checkpoint
- bassment/1: no visible return
- bassment/2: no visible return
- bassment/3: no visible return
- bassment/4: no visible return
- bassment/5: no visible return
- bassment/6: no visible return
- bassment/7: no visible return
- bassment/8: no visible return
- bassment/9: no visible return
- bassment/10: no visible return
- bassment/11: no visible return
- bassment/12: no visible return
- ... and 85 more

### Rule 4. Mainline locations are traversable

Statement: Rule 4. Searching from `start` over mainline scene edges only (flag-free, not hidden), every mainline scene is reached; from each hub every scene of its location is reached. The mutually reachable groups of locations are reported, and a mainline route back to the first location, if any.

Reached from `main/warehouse`: 36 of 36.

| Locations in the group | Scenes |
|---|---|
| alien_spaceship | 1 |
| alien_spaceship | 1 |
| alien_spaceship | 1 |
| alien_spaceship | 1 |
| alien_spaceship | 1 |
| hell | 1 |
| hell | 1 |
| hell | 1 |
| hell | 1 |
| hell | 1 |
| hospital_ward | 1 |
| hospital_ward | 1 |
| hospital_ward | 1 |
| hospital_ward | 1 |
| hospital_ward | 1 |
| hospital_ward | 1 |
| hospital_ward, mental_hospital | 8 |
| mental_hospital | 1 |
| mental_hospital | 1 |
| mental_hospital | 1 |
| mental_hospital | 1 |
| mental_hospital | 1 |
| mental_hospital | 1 |
| warehouse_rave | 1 |
| warehouse_rave | 1 |
| warehouse_rave | 1 |
| warehouse_rave | 1 |
| warehouse_rave | 1 |
| warehouse_rave | 1 |

No mainline route leads back to the first location.

Result: **PASS**. 36 of 36 mainline scenes reached from the start; components: hospital_ward+mental_hospital (8 scenes); no mainline route leads back to the first location

### Rule 5. Every scene has at least the minimum number of choices

Statement: Rule 5. Every scene has at least `min_choices` (default 3) choices: distinct destinations among its visible, non-miss, flag-free, non-hidden edges (`$checkpoint` is one destination; for a `previous_scene` option the worst case over the possible predecessors). A declared exception lists the scenes of one quest that are excused; it fails when it is stale (a listed scene does not exist, belongs to another quest, or has enough choices: too wide) and every unlisted scene under the minimum fails.

| Group | Scenes | Under the minimum | Fewest choices in the group |
|---|---|---|---|
| mainline | 36 | 35 | 1 |
| gospel | 17 | 17 | 1 |
| squadron | 14 | 14 | 1 |
| ember | 15 | 15 | 1 |
| bassment | 64 | 63 | 1 |

Mainline scenes by number of choices: {"1": 18, "2": 17, "3": 1}. Bassment passages by number of choices (with the return, if the graph has one): {"1": 42, "2": 21, "3": 1}.

Result: **FAIL**. 2 of 146 scenes have 3 or more choices; 0 excused by exception; 144 under without excuse

Offending (144):
- bassment/0: 1 choices (minimum 3)
- bassment/1: 2 choices (minimum 3)
- bassment/10: 2 choices (minimum 3)
- bassment/11: 1 choices (minimum 3)
- bassment/12: 1 choices (minimum 3)
- bassment/13: 1 choices (minimum 3)
- bassment/14: 1 choices (minimum 3)
- bassment/15: 2 choices (minimum 3)
- bassment/16: 2 choices (minimum 3)
- bassment/17: 1 choices (minimum 3)
- bassment/18: 2 choices (minimum 3)
- bassment/19: 1 choices (minimum 3)
- bassment/2: 1 choices (minimum 3)
- bassment/20: 2 choices (minimum 3)
- bassment/21: 1 choices (minimum 3)
- bassment/22: 1 choices (minimum 3)
- bassment/23: 1 choices (minimum 3)
- bassment/24: 1 choices (minimum 3)
- bassment/25: 1 choices (minimum 3)
- bassment/26: 2 choices (minimum 3)
- bassment/27: 1 choices (minimum 3)
- bassment/28: 2 choices (minimum 3)
- bassment/29: 1 choices (minimum 3)
- bassment/3: 2 choices (minimum 3)
- bassment/30: 2 choices (minimum 3)
- ... and 119 more

NOT CHECKABLE: not checkable from data: that each destination is a visible, tappable object of adequate size (checked by the coverage audit, N1.5 and N2.6).

### Rule 6. No unintended dead ends

Statement: Rule 6. (a) Every scene has a visible way out (a choice edge to another scene). (b) Every scene is reachable from `start` by some route (all edges but the hidden leaves; flags and items followed). (c) Every quest scene reaches a mainline scene (a return, a hub). (d) Every mainline scene reaches a terminal component. (e) A terminal component (a closed group of mainline scenes with no route out apart from `to_hub` routes and quests, and no ending) must be declared by an exception that lists its worlds; a declared component that is not closed is stale.

Terminal component: 8 scene(s): main/hospital_late, main/hospital_late.cafe, main/hospital_late.exit, main/hospital_late.quiet, main/ward_late, main/ward_late.dorm, main/ward_late.exit, main/ward_late.treat.

Result: **FAIL**. 0 scenes without a way out; 0 unreachable; 0 trapped in a quest; 8 scenes in 1 terminal component(s)

Offending (8):
- main/hospital_late: in a terminal component with no way on (no ending) that no exception declares
- main/hospital_late.cafe: in a terminal component with no way on (no ending) that no exception declares
- main/hospital_late.exit: in a terminal component with no way on (no ending) that no exception declares
- main/hospital_late.quiet: in a terminal component with no way on (no ending) that no exception declares
- main/ward_late: in a terminal component with no way on (no ending) that no exception declares
- main/ward_late.dorm: in a terminal component with no way on (no ending) that no exception declares
- main/ward_late.exit: in a terminal component with no way on (no ending) that no exception declares
- main/ward_late.treat: in a terminal component with no way on (no ending) that no exception declares

### Rule 7. Every reference resolves

Statement: Rule 7. Every reference resolves: every edge end is a scene; every route of the game data resolves; every overlay reference (start, locations, worlds, hubs, quests, entries, completion scenes, source files, entrances, objects, extra routes, exceptions) resolves against the game data; an `existing` object is a hotspot, a `partial` object names the hotspot it copies, a `proposed` object id collides with no hotspot id and is unique; every non-Bassment scene has an entry in `track_scenes.json`.

References checked: 930.

Result: **PASS**. 930 references checked, 0 unresolved

### Rule 8. Scene and music metadata valid

Statement: Rule 8. Every non-Bassment scene has a well-formed track assignment in `track_scenes.json` (a `track` id, alternates that each name a track); the Bassment's `music` block names its audio and chart (and its fight audio and chart). A track named in the registry without a catalogue file in `content/music/tracks/` is a warning, not a failure, until stage I4 has added the catalogue entries.

Non-Bassment scenes with a track assignment: 82 of 82. Track ids named: 61; without a catalogue file: 17.

Result: **PASS**. 82 of 82 non-Bassment scenes assigned; 61 track ids named, 17 without a catalogue file (warning)

Warning: 17 of 61 track ids named in track_scenes.json have no catalogue file in content/music/tracks/ (stage I4 adds them).

NOT CHECKABLE: not checkable from data: that a usable pack exists for each track, beat grids, first-drop times, the music sidecars (packs are outside the repository; checked by the Godot test tests/test_narrative_*.gd with the music stream's validator).

### Rule 9. Cycles and re-entry behave

Statement: Rule 9. (a) No group of quest scenes leads only to itself: every cycle inside a quest has a way out along the non-hidden edges (the mainline cycles that cannot be left are rule 6's declared terminal component). (b) For each quest and each origin location the scripted case holds: enter from the hub, move one scene, return (lands on the hub, the scene left is saved), re-enter (resumes there), play to an ending (completed), return, re-enter (restarts at the entry, `completed` kept). (c) 200 seeded random walks with closed and failed requests never get stuck. (b) and (c) run on a model of the route state; a graph with no checkpoint fails.

{"case_failures": 0, "cases": 0, "closed_cycles": 0, "model": false, "walks": 0}

Result: **FAIL**. not modelled: the graph has no checkpoint; 0 cycle(s) that cannot be left

Offending (1):
- no route state is possible on this graph: no return lands on a checkpoint, so a return always lands on a fixed scene and a re-entry cannot resume

NOT CHECKABLE: not checkable from data: the real RouteState, QuestRouter and director (the model tests the design; checked by the Godot test tests/test_narrative_*.gd).

### Rule 10. Route history and checkpoint stay consistent

Statement: Rule 10. On the model of the route state, after every `switched` the invariants of NARRATIVE_GRAPH.md 3.1 hold (quest, entry origin and checkpoint all empty or all set; the checkpoint is the hub of the entry origin's location; the location does not change during a quest; the current scene belongs to the current quest; the history is at most `history_limit` and ends at the current scene; a quest's saved scene belongs to that quest); a request closed before the lock leaves the committed state byte for byte unchanged; a fallback landing recomputes the change.

{"broken": 0, "model": false, "walks": 0}

Result: **FAIL**. not modelled: the graph has no checkpoint

Offending (1):
- no route state is possible on this graph: no return lands on a checkpoint

NOT CHECKABLE: not checkable from data: the invariants on the real classes against the mock and the real director (checked by the Godot test tests/test_narrative_*.gd).

### Check: Choices shown per scene against the cap (informational check, rulings 1 and 16)

Statement: Informational check beside the ten rules (rulings 1 and 16): the choices a scene shows (objects that lead somewhere; reactive objects are a separate list and are not capped) are at most `hotspot_cap` (8), and in a hub at most `hub_hotspot_cap` (10). The hubs and scenes that need a `max_hotspots` override in run.json are listed.

| Hub | Choices shown |
|---|---|
| main/hospital | 1 |
| main/mothership | 2 |
| main/underworld | 2 |
| main/ward | 2 |
| main/warehouse | 3 |

Cap 8; hub cap 10. Hubs that need a `max_hotspots` override in run.json above the node's own limit: none.

Result: **PASS**. most choices in one scene: 3 (bassment/20); hubs: hospital 1, mothership 2, underworld 2, ward 2, warehouse 3

## Target: game data plus content/narrative/graph.json

146 nodes, 957 edges (by status {"changed": 131, "existing": 558, "proposed": 268}; by kind {"quest_entry": 42, "quest_return": 238, "scene": 677}).

| Rule | What | Result | Numbers |
|---|---|---|---|
| 1 | Each quest entry within the limit of choices from the start; entry never gated by rhythm or another quest | EXCEPTION | quests within 5 choices: bassment 1, gospel 1, squadron 1, ember 1 (ungated entrances only: 1, 1, 1, 1) |
| 2 | All four quests from every mainline location and every scene of it; the mainline continues after a return | PASS | 20 of 20 cells have an ungated entrance on the hub (20 have one in some scene of the location); worst scene 2 choices |
| 3 | Every quest has a working return to the hub of the location it was entered from | PASS | 110 of 110 quest scenes have a visible return to the checkpoint; 0 have one that lands on a fixed scene (none); 0 have none; 0 not reachable from the entry |
| 4 | Mainline locations are traversable | PASS | 36 of 36 mainline scenes reached from the start; components: alien_spaceship+hell (10 scenes); hospital_ward+mental_hospital (20 scenes); warehouse_rave (6 scenes); no mainline route leads back to the first location |
| 5 | Every scene has at least the minimum number of choices | EXCEPTION | 104 of 146 scenes have 3 or more choices; 42 excused by exception; 0 under without excuse |
| 6 | No unintended dead ends | EXCEPTION | 0 scenes without a way out; 0 unreachable; 0 trapped in a quest; 8 scenes in 1 terminal component(s) |
| 7 | Every reference resolves | PASS | 1639 references checked, 0 unresolved |
| 8 | Scene and music metadata valid | PASS | 82 of 82 non-Bassment scenes assigned; 61 track ids named, 17 without a catalogue file (warning) |
| 9 | Cycles and re-entry behave | PASS | 20 of 20 scripted re-entry cases pass; 200 random walks (80000 requests, 11995 closed, 2944 fallbacks), 0 stuck; 0 cycle(s) that cannot be left |
| 10 | Route history and checkpoint stay consistent | PASS | 200 random walks, 80000 requests (11995 closed before the lock, 2944 fallback landings): 0 walks with a broken invariant |
| cap | Choices shown per scene against the cap (informational check, rulings 1 and 16) | PASS | most choices in one scene: 7 (main/mothership); hubs: hospital 6, mothership 7, underworld 7, ward 7, warehouse 7 |

Summary: pass 7, exception 3 (3 declared exception(s) listed), fail 0, parts not checkable from data 4.

### Rule 1. Each quest entry within the limit of choices from the start; entry never gated by rhythm or another quest

Statement: Rule 1. Each quest's entry is at most `max_choices_to_quest` (default 5) choices from `start`, counted twice: over all visible entrances, and over the entrances that are not gated by a passed block; both must reach every quest within the limit. No entrance edge may be gated by a passed block, by a flag, or name another quest, unless a declared exception lists its object; an exception that lists an object that is not gated (or does not exist) is stale and fails. Hidden leaves, miss twins and options that need a flag do not count as choices; the search follows the flags and items the player picks up on the way.

| Quest | Choices, any entrance | Choices, ungated entrances only | Counting the hidden leaves too |
|---|---|---|---|
| bassment | 1 | 1 | 1 |
| gospel | 1 | 1 | 1 |
| squadron | 1 | 1 | 1 |
| ember | 1 | 1 | 1 |

Result: **EXCEPTION**. quests within 5 choices: bassment 1, gospel 1, squadron 1, ember 1 (ungated entrances only: 1, 1, 1, 1)

EXCEPTION `legacy_wizard_entrance`: 2 gated entrance edges (warehouse.wizard, warehouse.chill.wizard). The wizard's mid-scene entrance to the Bassment stays as it is for now, as an extra way in beside the ungated Floor entrance of ruling 15 (owner, 6 Nov 2026; ruling 15): it is outside the port, gated by a passed block in blocks 1 and 2 and by the flag wh_wizard_met (once per run). Tracked by: later piece: move the entrance behind the port (when: soonest).

### Rule 2. All four quests from every mainline location and every scene of it; the mainline continues after a return

Statement: Rule 2. Each of the 5 locations offers each of the 4 quests: the hub shows an entrance for every quest that is not gated by a passed block (20 cells); from every scene of the location (late worlds included) every quest is at most `max_choices_to_quest_in_location` (default 2) ungated choices away; and the hub has a mainline exit (a scene route that is neither a `to_hub` nor a hub link), so that after a return the mainline continues.

| Location | Quest | Entrance in some scene | Entrance on the hub | Ungated entrance on the hub |
|---|---|---|---|---|
| warehouse_rave | bassment | yes | yes | yes |
| warehouse_rave | gospel | yes | yes | yes |
| warehouse_rave | squadron | yes | yes | yes |
| warehouse_rave | ember | yes | yes | yes |
| hospital_ward | bassment | yes | yes | yes |
| hospital_ward | gospel | yes | yes | yes |
| hospital_ward | squadron | yes | yes | yes |
| hospital_ward | ember | yes | yes | yes |
| mental_hospital | bassment | yes | yes | yes |
| mental_hospital | gospel | yes | yes | yes |
| mental_hospital | squadron | yes | yes | yes |
| mental_hospital | ember | yes | yes | yes |
| alien_spaceship | bassment | yes | yes | yes |
| alien_spaceship | gospel | yes | yes | yes |
| alien_spaceship | squadron | yes | yes | yes |
| alien_spaceship | ember | yes | yes | yes |
| hell | bassment | yes | yes | yes |
| hell | gospel | yes | yes | yes |
| hell | squadron | yes | yes | yes |
| hell | ember | yes | yes | yes |

Worst scene of any location: 2 ungated choices to a quest (limit 2). Mainline exits of each hub:

| Location | Mainline exits from the hub |
|---|---|
| warehouse_rave | main/warehouse.balcony, main/warehouse.bar |
| hospital_ward | main/hospital.corridor |
| mental_hospital | main/ward.art, main/ward.dorm |
| alien_spaceship | main/mothership.gallery, main/mothership.reactor |
| hell | main/underworld.court, main/underworld.furnace |

Result: **PASS**. 20 of 20 cells have an ungated entrance on the hub (20 have one in some scene of the location); worst scene 2 choices

### Rule 3. Every quest has a working return to the hub of the location it was entered from

Statement: Rule 3. Every quest scene offers a visible return (not hidden, not a miss twin, not flag-locked) whose landing is `$checkpoint`, the hub of the location the quest was entered from, and every quest scene is reachable from the quest's entry inside the quest. A return that lands on a fixed scene fails (it cannot land where the player entered). Hidden leaves never count. For each quest and each origin location with a hub entrance the check is the same, as the landing is the origin's hub.

Quest scenes: 110. With a visible return: 110 (on the checkpoint 110, on a fixed scene 0). Without: 0. Fixed landings of visible returns: {}. Not reachable from the entry: 0. Hub entrances per quest (origins): {"bassment": 5, "ember": 5, "gospel": 5, "squadron": 5}. Hidden leaves: 110 (never counted). Authored returns re-pointed: 18.

Result: **PASS**. 110 of 110 quest scenes have a visible return to the checkpoint; 0 have one that lands on a fixed scene (none); 0 have none; 0 not reachable from the entry

### Rule 4. Mainline locations are traversable

Statement: Rule 4. Searching from `start` over mainline scene edges only (flag-free, not hidden), every mainline scene is reached; from each hub every scene of its location is reached. The mutually reachable groups of locations are reported, and a mainline route back to the first location, if any.

Reached from `main/warehouse`: 36 of 36.

| Locations in the group | Scenes |
|---|---|
| alien_spaceship, hell | 10 |
| hospital_ward, mental_hospital | 20 |
| warehouse_rave | 6 |

No mainline route leads back to the first location.

Result: **PASS**. 36 of 36 mainline scenes reached from the start; components: alien_spaceship+hell (10 scenes); hospital_ward+mental_hospital (20 scenes); warehouse_rave (6 scenes); no mainline route leads back to the first location

### Rule 5. Every scene has at least the minimum number of choices

Statement: Rule 5. Every scene has at least `min_choices` (default 3) choices: distinct destinations among its visible, non-miss, flag-free, non-hidden edges (`$checkpoint` is one destination; for a `previous_scene` option the worst case over the possible predecessors). A declared exception lists the scenes of one quest that are excused; it fails when it is stale (a listed scene does not exist, belongs to another quest, or has enough choices: too wide) and every unlisted scene under the minimum fails.

| Group | Scenes | Under the minimum | Fewest choices in the group |
|---|---|---|---|
| mainline | 36 | 0 | 3 |
| gospel | 17 | 0 | 3 |
| squadron | 14 | 0 | 3 |
| ember | 15 | 0 | 3 |
| bassment | 64 | 42 | 1 |

Mainline scenes by number of choices: {"3": 29, "4": 2, "6": 2, "7": 3}. Bassment passages by number of choices (with the return, if the graph has one): {"1": 8, "2": 34, "3": 21, "4": 1}.

Result: **EXCEPTION**. 104 of 146 scenes have 3 or more choices; 42 excused by exception; 0 under without excuse

EXCEPTION `bassment_passages_under_three`: 42 scenes of bassment under 3 choices. The Bassment is a text-and-choice crawl; only the return is added in phase 1 (ruling 19). Raising the choices of these passages is a later, separately sized piece (owner decision, 6 Nov 2026). The list has 42 passages: ruling 19 says 41, but passage 23 offers its third way (the lamp door) only to a player who carries the lamp, and an option that needs an item the player has not got is not counted. Tracked by: later piece after N2 (ONE_PC_PLAN.md, end of stage N2).

NOT CHECKABLE: not checkable from data: that each destination is a visible, tappable object of adequate size (checked by the coverage audit, N1.5 and N2.6).

### Rule 6. No unintended dead ends

Statement: Rule 6. (a) Every scene has a visible way out (a choice edge to another scene). (b) Every scene is reachable from `start` by some route (all edges but the hidden leaves; flags and items followed). (c) Every quest scene reaches a mainline scene (a return, a hub). (d) Every mainline scene reaches a terminal component. (e) A terminal component (a closed group of mainline scenes with no route out apart from `to_hub` routes and quests, and no ending) must be declared by an exception that lists its worlds; a declared component that is not closed is stale.

Terminal component: 8 scene(s): main/hospital_late, main/hospital_late.cafe, main/hospital_late.exit, main/hospital_late.quiet, main/ward_late, main/ward_late.dorm, main/ward_late.exit, main/ward_late.treat.

Result: **EXCEPTION**. 0 scenes without a way out; 0 unreachable; 0 trapped in a quest; 8 scenes in 1 terminal component(s)

EXCEPTION `late_loops_have_no_ending`: terminal component of 8 scenes in worlds hospital_late, ward_late. There is no ending yet (owner decision, 6 Nov 2026): the two late worlds loop on themselves and into each other. Tracked by: future decision on an ending.

### Rule 7. Every reference resolves

Statement: Rule 7. Every reference resolves: every edge end is a scene; every route of the game data resolves; every overlay reference (start, locations, worlds, hubs, quests, entries, completion scenes, source files, entrances, objects, extra routes, exceptions) resolves against the game data; an `existing` object is a hotspot, a `partial` object names the hotspot it copies, a `proposed` object id collides with no hotspot id and is unique; every non-Bassment scene has an entry in `track_scenes.json`.

References checked: 1639.

Result: **PASS**. 1639 references checked, 0 unresolved

### Rule 8. Scene and music metadata valid

Statement: Rule 8. Every non-Bassment scene has a well-formed track assignment in `track_scenes.json` (a `track` id, alternates that each name a track); the Bassment's `music` block names its audio and chart (and its fight audio and chart). A track named in the registry without a catalogue file in `content/music/tracks/` is a warning, not a failure, until stage I4 has added the catalogue entries.

Non-Bassment scenes with a track assignment: 82 of 82. Track ids named: 61; without a catalogue file: 17.

Result: **PASS**. 82 of 82 non-Bassment scenes assigned; 61 track ids named, 17 without a catalogue file (warning)

Warning: 17 of 61 track ids named in track_scenes.json have no catalogue file in content/music/tracks/ (stage I4 adds them).

NOT CHECKABLE: not checkable from data: that a usable pack exists for each track, beat grids, first-drop times, the music sidecars (packs are outside the repository; checked by the Godot test tests/test_narrative_*.gd with the music stream's validator).

### Rule 9. Cycles and re-entry behave

Statement: Rule 9. (a) No group of quest scenes leads only to itself: every cycle inside a quest has a way out along the non-hidden edges (the mainline cycles that cannot be left are rule 6's declared terminal component). (b) For each quest and each origin location the scripted case holds: enter from the hub, move one scene, return (lands on the hub, the scene left is saved), re-enter (resumes there), play to an ending (completed), return, re-enter (restarts at the entry, `completed` kept). (c) 200 seeded random walks with closed and failed requests never get stuck. (b) and (c) run on a model of the route state; a graph with no checkpoint fails.

{"case_failures": 0, "cases": 20, "closed_cycles": 0, "model": true, "walk_moves": {"closed": 11995, "fallback": 2944, "quest_entry": 8903, "quest_return": 8800, "scene": 47358}, "walks": 200}

Result: **PASS**. 20 of 20 scripted re-entry cases pass; 200 random walks (80000 requests, 11995 closed, 2944 fallbacks), 0 stuck; 0 cycle(s) that cannot be left

NOT CHECKABLE: not checkable from data: the real RouteState, QuestRouter and director (the model tests the design; checked by the Godot test tests/test_narrative_*.gd).

### Rule 10. Route history and checkpoint stay consistent

Statement: Rule 10. On the model of the route state, after every `switched` the invariants of NARRATIVE_GRAPH.md 3.1 hold (quest, entry origin and checkpoint all empty or all set; the checkpoint is the hub of the entry origin's location; the location does not change during a quest; the current scene belongs to the current quest; the history is at most `history_limit` and ends at the current scene; a quest's saved scene belongs to that quest); a request closed before the lock leaves the committed state byte for byte unchanged; a fallback landing recomputes the change.

{"broken": 0, "model": true, "walk_moves": {"closed": 11995, "fallback": 2944, "quest_entry": 8903, "quest_return": 8800, "scene": 47358}, "walks": 200}

Result: **PASS**. 200 random walks, 80000 requests (11995 closed before the lock, 2944 fallback landings): 0 walks with a broken invariant

NOT CHECKABLE: not checkable from data: the invariants on the real classes against the mock and the real director (checked by the Godot test tests/test_narrative_*.gd).

### Check: Choices shown per scene against the cap (informational check, rulings 1 and 16)

Statement: Informational check beside the ten rules (rulings 1 and 16): the choices a scene shows (objects that lead somewhere; reactive objects are a separate list and are not capped) are at most `hotspot_cap` (8), and in a hub at most `hub_hotspot_cap` (10). The hubs and scenes that need a `max_hotspots` override in run.json are listed.

| Hub | Choices shown |
|---|---|
| main/hospital | 6 |
| main/mothership | 7 |
| main/underworld | 7 |
| main/ward | 7 |
| main/warehouse | 7 |

Cap 8; hub cap 10. Hubs that need a `max_hotspots` override in run.json above the node's own limit: main/hospital (6 choices, node limit 4), main/mothership (7 choices, node limit 4), main/underworld (7 choices, node limit 4), main/ward (7 choices, node limit 5), main/warehouse (7 choices, node limit 4).

Result: **PASS**. most choices in one scene: 7 (main/mothership); hubs: hospital 6, mothership 7, underworld 7, ward 7, warehouse 7

## Not checkable from data

- Rule 5 shows that the distinct destinations exist, not that each is a visible, tappable object of adequate size (the coverage audit, N1.5 and N2.6).
- Rule 8: packs, beat grids, first-drop times and the music sidecars (the Godot test `tests/test_narrative_*.gd` with the music stream's validator).
- Rules 9 and 10: the real `RouteState`, `QuestRouter` and director (the Godot test `tests/test_narrative_*.gd`); the tool runs a model of the specified behaviour.
- Timing: the transaction rule (state changes only on `switched`) cannot be shown on a static graph; the port conformance cases and the route tests cover it.
