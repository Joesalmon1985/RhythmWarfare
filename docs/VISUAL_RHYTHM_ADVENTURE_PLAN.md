# Visual rhythm adventure: architecture and implementation plan (Fable, 2026-11-04)

Executes the owner's brief `docs/VisualChoicePlan.md` on `main` at `3b74c67e`. Branch `feature/visual-adventure`. Companion: `docs/MUSIC_LIBRARY_PLAN.md`
on `feature/music-library` (file ownership in its section 6; this plan owns the scenes, worlds, trial, maps, assets and the run engine's routing).

## 1. Existing versus proposed

| Exists today | Proposed |
| --- | --- |
| Four pads; free look (drag/Q/E); route arrows (buttons) in the last block; `[DEFAULT]` text; floating text choices in the Bassment; "Enter the Trial" button | Four pads plus touching the world. Arrows, labels and the wizard's button removed from gameplay; free look kept as an accessibility option but never required |
| `RunExitsView` lights the doorway of each route; `StoryProjector` maps world positions to the low-res screen; things (billboards), lights, actors with activities | **Hotspots**: data-driven interactive targets anchored to things, doorways, actors or positions, projected to screen, hit-tested on tap, with available / selected / committed states |
| Route choice commits at the last decision (beat 60.5 lock); the block's pass/hold moves the rail | **Intent and outcome**: the tap is the intent; the last block's performance (pass or fail at the decision beat) picks `on_success` or `on_failure` of the selected hotspot |
| Rails (`RunRail`, `RunJourney`), passage frame, door walk, `player_move/look/walk/role`, queasy, sick beat | Cinematics are rail actions named by the hotspot's outcome; no new motion system |
| Trial items and flags (`grants`, `requires`), run energy, `reached` per world | **World state** per run: flags set by outcomes, saved in `RunProgress` (per run and persistent), driving availability |
| The Bassment: passage text, choices as lit exits plus floating labels, creatures as billboards | Choices become hotspots on the exits, creatures and objects; the passage text stays as a caption band (narrative, not navigation); labels go |

## 2. Hotspot data (the contract every workstream builds against; fixed in the first commit)

`content/run/hotspots/<world>.json` (run worlds) and `content/trial/hotspots.json` (the Bassment), validated by `RunData` / `TrialData`:

```
{"id": "warehouse.bar.bartender", "world": "warehouse", "scene": "warehouse.bar", "map": "night_one",
 "anchor": {"thing": "bar_lamp"} | {"waypoint": "booth_door"} | {"actor": "b01"} | {"pos": [x, y, z]},
 "kind": "exit" | "object" | "character" | "feature" | "encounter" | "secret",
 "radius_m": 0.8, "min_px": 72,
 "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": false},
 "look": {"available": "glow|pulse|beckon|flicker|open|crack", "selected": "ring", "committed": "flash"},
 "challenge": {"family": "drums" | "bass", "tier": 2} | null,
 "on_success": {"route": "warehouse.chill"} | {"flags_set": ["bar_drink"], "cinematic": "drink_at_bar", "energy": 6, "music": "variation"},
 "on_failure": {"route": "warehouse.toilets"} | {"flags_set": [...], "cinematic": "spill", "energy": -8},
 "cinematic": {"move": "walk", "to": "bar_counter", "bars": 3, "look_at": "b01"},
 "default": true, "repeatable": false}
```
Rules: every scene has 2 to 4 available hotspots at any time, exactly one `default` among its exits; every `route` is a scene route or a trial passage; every anchor exists in the map; every
outcome's cinematic resolves to rail actions that start in a cue-free guard; failure outcomes never dead-end (a route or a recoverable state); all existing routes and endings remain reachable.

## 3. Architecture

- `src/run/run_hotspots.gd` (pure): availability from world state and energy, selection with change-until-commit, commit at the scene's last decision beat (the existing lock), outcome from the
  block-4 result, world-state application, the default when nothing is chosen.
- `src/run/hotspot_view.gd` (node, inside the low-res viewport above the crowd): projects anchors through `StoryProjector` each frame, draws the three looks with the chapter palette
  (no floating rectangles: rings of light on the floor, a glow on the thing, a beckoning pose on an actor via `watch`/`wave`, a door swinging), handles taps: nearest hotspot within its
  projected radius and at least `min_px`, pads excluded (the stage area is already separate), one-finger taps only, keyboard 1 to 4 kept for desktop.
- `RunPlay`: the route window becomes the hotspot window (same beats); `RunExitsView` and the arrows are retired; the wizard becomes a character hotspot; outcomes feed `RunEngine.choose`
  (route) or `RunJourney` (cinematics) and `RunProgress.flags`.
- `TrialScene`: choices become hotspots (kind from the data: exit, encounter for fights, object for items, feature for luck tests), the caption band shows the passage text, the floating
  labels go, the four-bar window and default stay.
- World state: `RunProgress.run_flags` (cleared on a new run) and `RunProgress.flags` (persistent discoveries); `requires`/`grants` in the trial map onto the same mechanism.
- Determinism: the same taps at the same song times with the same inputs give the same outcomes (tests at 30, 60 and variable frame steps).

## 4. Conversion matrix (per scene: hotspots to author; S = success, F = failure)

| Scene | Exits (become hotspots) | New interactions (S / F) |
| --- | --- | --- |
| Warehouse floor | bar door, balcony stair | the wizard (enter the Bassment / he shrugs, nothing), a dancer beckoning (S: circle forms, energy; F: stumble, queasy), the LED wall (S: palette shift, music variation) |
| Warehouse bar | chill-out arch, booth steps | the bartender (S: a drink, energy, flag; F: spill, queasy), a stranger on a phone (secret: the balcony key flag) |
| Warehouse balcony | chill-out, booth | the rail (S: look over the floor, crowd wave; F: vertigo, queasy), a promoter (S: booth route opens direct) |
| Warehouse chill-out | the door | sofas (S: recover energy; F: fall asleep, a phase lost), the wizard again |
| Warehouse booth | the door | the decks (S: DJ role, drop; F: wrong record, crowd drifts), headphones (secret) |
| Warehouse door | Mothership light, Underworld crack | the bouncer (F: thrown out: Underworld) |
| Mothership deck / gallery / reactor / bridge / airlock | as the route map | a grey beckoning (S: examined gently; F: the probe light), the reactor core (S: power surge, music; F: alarm), the helm (S: warp; F: crash, airlock early), the planet window (feature) |
| Underworld arena / court / furnace / pit / throne | as the route map | the bouncer demon (S/F), the throne (S: resident DJ; F: devoured route), chains (F: dragged to the cage), the lava bridge (luck) |
| Hospital ward / corridor / day room / cafeteria / garden / bandstand | as the route map | the nurse (S: wheeled on; F: back to bed), the family (S: cheer; F: a visitor sleeps), the TV, the vending machine (secret), the bandstand mic |
| Ward day room / art / dorm / corridor / courtyard / stage | as the route map | the orderly (F: treatment room), the painter (S: a painting opens the courtyard), the barred window (feature), the talent stage (S: star; F: lights out) |
| Late worlds | as the route map | the loops' repeats vary by flags (a path taken before is lit differently) |
| The Bassment (63 passages) | every `exit_wp` becomes an exit hotspot; encounters become creature hotspots; items object hotspots; luck tests feature hotspots | no new passages; secrets and gates unchanged |

## 5. Workstreams (Sonnet, worktrees, explicit ownership)

- **A Core interaction engine** (owns `src/run/run_hotspots.gd`, `src/run/hotspot_view.gd`, the hotspot sections of `run_data.gd`/`trial_data.gd`, `RunProgress` flags, `tests/test_hotspots*.gd`):
  the data contract, projection, hit testing with phone targets, the three looks, selection and commit, the outcome resolver, world state, retirement of the arrows and labels behind a flag
  until C and D land, then for good. Also the Bassment scene's switch to hotspots (small, the data already has exits).
- **C Campaign conversion** (owns `content/run/hotspots/*.json`, the five maps' new anchors (things, waypoints), `content/run/run.json` cinematics, per-world art hooks in `tools/story/art/`):
  authors section 4 for the five worlds and the late worlds against the contract, with the looks drawn by the existing generators (a lamp thing that glows, a door that swings, an actor that
  beckons), reusing geometry and actors first. Starts in parallel with A against the contract; integrates when A lands.
- **D Bassment conversion** (owns `content/trial/hotspots.json`, `src/trial/trial_scene.gd` presentation, `tools/trial/*`): the 63 passages' choices to hotspots, the caption band, creature and
  item hotspots, the entry via the wizard hotspot, the screenshots.
- **E Validation** (owned by the coordinator, run by each workstream): `tests/test_hotspots_*.gd` (availability, selection, change, default, commit timing, success and failure branches,
  determinism at frame steps, phone hit targets never over the pads), the run matrix with tap policies (perfect, 0.8, 0.5, none; default taps, changed taps, failure taps), reachability
  of every route and ending with hotspots only, `walk_run.sh` / `walk_trial.sh` / `walk_campaign.sh` on the real scenes, screenshots before and after a selection and after each outcome,
  a coverage matrix `docs/VISUAL_COVERAGE.md` (every world, scene, hotspot, S/F outcome, test status), frame numbers.

## 6. Order
A and C and D start together (C and D author data and art against the contract; A builds the engine). Integration after A; then C and D's data light up; E throughout; then the Opus look pass
(section 7) and the performance pass.

## 7. Opus passes (after integration)
Look: hotspots obvious without text (silhouette, light, motion), selection and commit animations, the Bassment zones (the echo chamber, the warren), consistency across worlds, phone readability;
inspect screenshots and fix. Performance: stage build hitches (build on a thread or spread over guards), frame time per world, sheet memory, Android export smoke test if the SDK exists, no
regressions in the recordings.

## 8. Acceptance
Exactly four pads plus touching the world; no written directional choices in the converted experience; three visible states; change until commit; performance decides the outcome; music never
stops; every world, scene, route, ending, secret and encounter reachable; the coverage matrix complete; the suite, the three walks and the validators green.

## 9. Risks
Small projected targets on phones (minimum 72 px and nearest-within-radius); authoring volume (2 to 4 hotspots per scene, reconnecting branches); the Bassment's narrative without choice text
(captions carry it); two plans on one engine (ownership in the music plan's section 6; the coordinator integrates).
