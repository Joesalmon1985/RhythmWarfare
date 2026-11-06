# Schema of the narrative overlay: `content/narrative/graph.json`

Format string: `rhythm_warfare.narrative.v1`. Status: **proposed**. The file does not exist yet; stage N1.2 creates it.
A complete example is `overlay_proposed.json` in this folder. The design is in `../NARRATIVE_GRAPH.md`.

The overlay is data only. It does not repeat anything the game data already says. `NarrativeGraph` builds the
graph from four existing sources and adds the overlay on top:

| Source | What it gives | Node ids it creates |
|---|---|---|
| `content/run/run.json` and `content/run/hotspots/*.json` | The 36 main-run scenes, their worlds, their doors and objects | `main/<scene>` |
| `content/paths/<path>/run.json` and `hotspots/*.json` | The 46 scenes of `gospel`, `squadron`, `ember` | `<path>/<node>` |
| `content/trial/passages.json` | The 64 Bassment passages | `bassment/<passage>` |
| `content/run/track_scenes.json` and the Bassment's `music` block | Songs, by reference | none |

A graph id is `"<path>/<node>"`, as in `INTEGRATION_CONTRACT.md` section 3. `path` is `main`, a path id or `bassment`.

Marks used in this document: **required** (the loader refuses the file without it), **optional** (a default is
given), **planning** (kept in the proposed example for the owner's review; the loader may ignore it).

## 1. Top level

| Field | Type | Rule |
|---|---|---|
| `format` | string, required | Exactly `rhythm_warfare.narrative.v1`. Any other value: the loader refuses the file. |
| `start` | graph id, required | The first scene of a new run. Must be the hub of one location. Today `main/warehouse`. |
| `settings` | object, optional | See section 2. |
| `locations` | array of Location, required | Exactly the five mainline locations. Ids unique. |
| `quests` | array of Quest, required | Exactly the four quests. Ids unique. |
| `entrances` | array of Entrance, required | One per (location, quest) pair: 20. A missing pair is an error (rule 2). |
| `route_rules` | array of RouteRule, optional | Default routes placed on many scenes by a rule. |
| `extra_routes` | array of ExtraRoute, optional | Routes added to one named scene. |
| `exceptions` | array of Exception, optional | Named, reported exceptions to a rule. See section 8. |
| `status`, `date` | string, planning | Marks on the proposed example only. |

Unknown top-level keys are an error. A reader that finds a `format` it does not know refuses the file and
leaves the game on the data it has. A change that breaks readers is `v2`, never an edit of `v1`.

## 2. `settings`

| Field | Type | Default | Rule |
|---|---|---|---|
| `min_choices` | int | 3 | Rule 5 threshold. At least 1. |
| `max_choices_to_quest` | int | 5 | Rule 1 threshold. |
| `history_limit` | int | 32 | Length of `RouteState.history`. At least 8. |
| `max_choices_to_quest_in_location` | int | 2 | Rule 2: the most ungated choices from any scene of a location to any quest. Added by the validator (N1.1). |
| `hotspot_cap` | int | 8 | Choices per scene (lead rulings 1 and 16). Only used by the validator's hub-object report. |
| `hub_hotspot_cap` | int | 10 | The most a hub scene may set as `max_hotspots` (lead ruling 16). Only used by the same report. |

## 3. Location

A mainline location. One per owner-named place.

| Field | Type | Rule |
|---|---|---|
| `id` | string, required | Lower snake case. The five: `warehouse_rave`, `hospital_ward`, `mental_hospital`, `alien_spaceship`, `hell`. |
| `title` | string, required | Display name for tools and the developer overlay. |
| `worlds` | array of string, required | World ids from `content/run/run.json`. Each world belongs to one location only. The late worlds `hospital_late` and `ward_late` are parts of their locations. Every world of the main run must belong to a location. |
| `hub` | graph id, required | The hub scene: the location's entry scene. Must be a `main/` scene of one of its worlds. Every hub shows all four quest entrances and at least one mainline exit (rule 2). |
| `hub_links` | array of HubLink, optional | Direct links from this hub to another hub. Used for the paired locations. |
| `music` | object, optional | `{ "registry": "content/run/track_scenes.json", "path": "main" }`. A reference, never a song name. Scene tracks are looked up in the registry by node id. |
| `status`, `note` | string, planning | |

**HubLink**: `{ "to_location": id, "to": graph id, "object": Object }`. `to` must be the hub of `to_location`.

## 4. Quest

| Field | Type | Rule |
|---|---|---|
| `id` | string, required | `bassment`, `gospel`, `squadron`, `ember`. These are the repository's ids. Titles and quotations from other works are not used. |
| `title` | string, required | The repository's title: The Bassment, The Life of Jesus, The Mission Count, The Ember Road. |
| `owner_label` | string, planning | The owner's name for the slot. |
| `system` | `"path"` or `"trial"`, required | `path`: a rhythm run in `content/paths/<path>/`. `trial`: the text-and-choice Bassment in `src/trial`. Decides which scene source is read. |
| `path` | string, required | Path id (`gospel`...) or `bassment`. The first part of every scene id of the quest. |
| `scenes_source` | repo path, required | The file the scenes come from. Must exist (rule 7). |
| `entry` | graph id, required | First scene. Must be a scene of this quest. |
| `entry_conditions` | array of Condition, required, may be empty | Only conditions that are genuinely needed. Today none. A condition may not name a rhythm result or another quest (validator error). See section 9. |
| `completion` | `{ "scenes": [graph id] }`, required | Landing on one of these scenes sets `completed`. Must be scenes of the quest. Death passages are not completions. |
| `return` | Return, required | Section 5. |
| `progress` | object, planning | Documents what is saved per quest. The stored fields are fixed by `NARRATIVE_GRAPH.md` section 3. |
| `flag_prefixes` | array of string, optional | Run-flag prefixes saved with the quest's progress (`ember_`, `sq_`, `gospel_`). Empty for the Bassment, whose carried items are saved instead. |
| `music` | object, optional | For a path: `{ "registry": "content/run/track_scenes.json", "path": "<path>" }`. For the trial: `{ "registry": "content/trial/passages.json", "key": "music" }` (the Bassment reads its own `music` block: `audio`, `fight_audio`). |

**Return** (one definition per quest, placed by a rule, with overrides):

| Field | Type | Rule |
|---|---|---|
| `landing` | `"checkpoint"`, required | The only value in v1. A return lands on `RouteState.checkpoint`. Never a fixed scene. |
| `object` | string, required | Id of the return object, `<quest>.return`. |
| `placement` | `"all_scenes"` or `"listed"`, required | `all_scenes`: every scene of the quest shows the return. `listed`: only the scenes in `scenes`. Preferred: `all_scenes`. |
| `scenes` | array of graph id | Only with `listed`. |
| `overrides` | array of `{ "scene": id, "object": string }` | A scene that needs its own object instead of the default. |
| `hidden_fallbacks` | array of `"pause_menu_leave"` / `"system_back_key"` | Existing ways out that stay and land on the checkpoint. They never count as choices. |

## 5. Entrance

One per (location, quest) pair. It says which object in the hub scene is the way into the quest. The destination
is never stated here: it is the quest's `entry`, or the saved scene when the quest is resumed.

| Field | Type | Rule |
|---|---|---|
| `id` | string, required | `<location>.<quest>`. Unique. |
| `location` | location id, required | |
| `quest` | quest id, required | |
| `scene` | graph id, required | The scene holding the object. For the 20 hub entrances it is the location's hub. |
| `object` | Object, required | The visible thing the player touches. |
| `transition` | `"port"` or `"legacy_mid_scene"`, required | `port`: requested through `TransitionPort` (`kind: quest_entry`, `when: lap_end`). Every one of the 20 hub entrances is `port` (lead ruling 15). `legacy_mid_scene` is used only inside `legacy_way`. |
| `rhythm_gate` | bool, required | `false` for every entrance. A `true` is allowed only inside `legacy_way` and needs an exception that names this entrance. |
| `conditions` | array of Condition, required, may be empty | Same rule as `entry_conditions`. |
| `exception` | exception id, optional | Required when `rhythm_gate` is true or `transition` is `legacy_mid_scene`. |
| `legacy_way` | object, optional | An extra, older way into the same quest that stays as it is: `{ object, transition, rhythm_gate, conditions, also_in, exception }`, with the same rules as above. Only the Warehouse's Dungeon entrance has one (the wizard, decision 5). It never replaces the ungated `port` entrance and does not count toward rule 1. |
| `also_in`, `also_in_today` | array or string, planning | Other scenes that hold an object for the same quest. |
| `status` | `existing` / `partial` / `proposed`, planning | |

**Object**: `{ "id": string, "status": "existing" | "partial" | "proposed", "illustrative_idea": string }`.
`id` is a hotspot id. For `existing` it must be a hotspot id in `content/` (rule 7). For `proposed` it must not collide with any hotspot id. A `partial` object is a new placement of an existing one: its `id` must not collide either, and the field `copy_of` (added by the validator, N1.1) names the existing hotspot id it copies; the validator removes the gate of that original in the target graph.
`illustrative_idea` is a one-line suggestion. The visual design belongs to the interaction work; the validator ignores the idea.

## 6. RouteRule

A default route placed on many scenes. The validator expands it into edges.

| Field | Type | Rule |
|---|---|---|
| `id` | string, required | `to_hub`, `back` or `return`. Other ids are reserved for later versions. |
| `applies_to` | string, required | Plain text in the example. In the real file one of: `mainline_non_hub`, `path_quest_scenes`, `all_quest_scenes`. |
| `target` | string, required | `hub_of_location`, `previous_scene` or `checkpoint`. |
| `object` | string, required | Object id pattern: `<scene>.to_hub`, `<quest>.back`, `<quest>.return`. |
| `kind` | `scene` / `quest_return`, required | Edge kind produced. |
| `status`, `note` | string, planning | |

`previous_scene` is resolved from the route history. In the graph it becomes one edge per scene from which the
current scene can be reached, each carrying `condition.previous_scene = true`.

## 7. ExtraRoute

A route added to one scene, because rule 5 needs it there.

| Field | Type | Rule |
|---|---|---|
| `scene` | graph id, required | |
| `kind` | `quest_entry`, `restart` or `second_route`, required | `quest_entry`: an extra entrance for `quest` on a non-hub mainline scene; the return still lands on the hub of the scene's location. `restart`: from a quest ending scene to the quest's first scene. `second_route`: a second onward route inside a quest. |
| `quest` | quest id | Required for `quest_entry`. |
| `to` | graph id | Required for `restart` and `second_route`. |
| `object` | Object, required | |
| `owner_to_confirm` | bool | `true` on every `restart` and `second_route` (lead ruling 17): the owner confirms or replaces them. The validator requires it. Added by the validator (N1.1). |
| `reason`, `needs_review` | string, planning | `needs_review` marks a destination chosen only so the graph is valid. |

## 8. Exception

An exception is a named, reported deviation. The validator never passes it silently and never fails it. It prints
it as `EXCEPTION` with the id and reason, and it fails if the exception is **stale** (it names something that
no longer deviates) or **wider than needed** (a scene in a rule 5 exception that has three choices).

| Field | Type | Rule |
|---|---|---|
| `id` | string, required | Unique. |
| `rule` | int 1 to 10, required | The rule it relaxes. |
| `kind` | `named_exception` / `terminal_component`, required | `terminal_component` (rule 6 only): a set of scenes with no way to leave by design. |
| `scope` | object, required | Rule 5: `{ "quest": id, "scenes": [graph id] }`. Rule 1: `{ "entrances": [ids], "objects": [ids] }`. Rule 6: `{ "worlds": [ids] }`. |
| `reason` | string, required | One or two sentences. Printed in the report. |
| `tracked_by` | string, required | Where the later piece of work is recorded. An exception with no tracker is an error. |
| `report_as` | `"exception"`, required | Fixed. |
| `status` | string, planning | |

Exceptions in the proposed example: `bassment_passages_under_three` (rule 5, 41 passages),
`legacy_wizard_entrance` (rule 1), `late_loops_have_no_ending` (rule 6).

## 9. Condition

`{ "flag_all": [string], "flag_none": [string], "window": string }`. A condition is allowed only where it is
genuinely needed. It may not contain `passed_block`, `on_miss`, an energy test or a flag set by another quest.
The proposed overlay has none except the legacy wizard (`flag_none: wh_wizard_met`, `window: blocks 1-2`), which is an
exception.

## 10. What the validator derives (not written in the overlay)

| Derived | From |
|---|---|
| All scene-to-scene edges | Hotspot `on_success.route` and `on_failure.route` in `content/**` |
| Edge `kind` | `quest_entry` when the destination is a quest `entry`; `quest_return` for returns and for `to: $checkpoint`; otherwise `scene` |
| Hub entrance edges | `entrances` |
| `to_hub`, `back`, `return` edges | `route_rules` |
| Extra edges | `extra_routes`, `hub_links` |
| The hidden leaves | `return.hidden_fallbacks` |

`$checkpoint` in a graph export is a placeholder: it resolves to the hub of the location of the entry origin
when the router builds the destination.

## 11. Loading rules

1. Unknown `format`: refuse, keep the game on its built-in data.
2. Any reference that does not resolve (rule 7): refuse. The game does not start with a half-resolved graph.
3. The loader never writes this file. It is content, edited by hand and reviewed.
4. The same loader code runs in `tools/narrative/graph.py` (Python) and in `src/narrative/narrative_graph.gd` (Godot). A Godot test builds the graph and compares it with the Python export.
