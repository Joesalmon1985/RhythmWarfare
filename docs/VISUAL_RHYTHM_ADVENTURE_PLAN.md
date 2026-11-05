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

## 10. Progress log

### Workstream C: campaign conversion content (Sonnet, 2026-11-04)

Data and art for all seven run worlds are in; the engine (A) is not wired yet, so none of it lights up in play. 127 hotspots in 36 scenes (Warehouse 24, Mothership 17, Underworld 17,
Hospital 20, Ward 20, Hospital late 16, Ward late 13), 138 named cinematics, `python3 tools/run/check_hotspots.py` green (0 errors, 5 route-lock warnings, below). Coverage matrix: `docs/VISUAL_COVERAGE.md`.

What A needs to know to wire it:
- **Files**: `content/run/hotspots/<world>.json` is `{"world": id, "hotspots": [...]}` (hotspot fields exactly as section 2). Authored by `tools/run/make_hotspots.py` (tables) via `tools/run/make_scenes.py`
  (the single entry point; it also writes the cinematics, the new things and lights). Do not hand-edit the JSON; edit the tables and run make_scenes.py.
- **Cinematics**: `run.json` gets a top-level `cinematics`: `{name: {"world", "steps": [{"move": "walk" | "place", "to": waypoint, "bars": 2..4, "role", "style", "look_at"?}]}}`. `walk` is
  `player_walk` (in the room the rail is in), `place` is `player_move` (a journey place; used only for being dragged to the cage and carried to the treatment room), `role` and `style` use the rail's
  vocabulary, `look_at` is a waypoint, thing or actor id. A hotspot's own `cinematic` field is the same step inline (the approach walk when it is selected); outcomes name an entry of `cinematics`.
- **Outcome fields used**: `route` (a scene id of the scene's `next`, or `"1"`, the Bassment's first passage, for the wizard), `flags_set`, `cinematic`, `energy` (int, -12 to +10), `music`
  (`"variation"` or `"dip"`). `challenge` is null everywhere (the last block decides). Flags are one namespace, prefixed per world (`wh_`, `ms_`, `uw_`, `hp_`, `wd_`, `hl_`, `wl_`).
- **Exits**: one per route, anchored to the route's doorway waypoint (`place.rail.exits`), the first route the default with look `open`, the others `glow`, the Underworld door `crack` (anchored to
  the new `crack_door` thing). A failed exit still takes the same door (stagger cinematic, -5 energy): exit failures are setbacks, not other destinations.
- **Interactions** pick the scene's default route when they carry no `route`. Route outcomes on interactions: the Warehouse promoter (S: booth), the bouncer (F: Underworld), the Mothership exam
  (F: Ward), the Underworld grudge bouncer (F: furnace), the throne (F: Ward), the Ward's painted door (S: courtyard). Five of these differ in chart pack from the default route (the checker
  lists them as warnings): the route lock (beat 60.5) must either chart from the hotspot's `on_success.route` and treat a diverting failure as a late swap, or the engine must decide the
  outcome before the chart is fixed. A decides; the data is final either way.
- **Availability**: `flags_all` / `flags_none` / `energy_min` / `once`; the checker proves 2 to 4 hotspots available at any time over every flag combination (once-only ones counted present and used).
  Flags that open things later: `wh_vip_pass` (bar stranger: booth headphones, the bouncer's VIP variant), `wh_thrown_out` (the Underworld bouncer's grudge), `ms_badge` (bridge star chart),
  `wd_painted` (the corridor's painted door), `hp_token` (late cafeteria's free drink), `hp_lamp_lit` and `hp_sang` (the late garden lamp and the bandstand encore play differently on the second round).
- **New anchors**: things `wizard_floor`, `wizard_chill`, `headphones_booth`, `crack_door` (Night One), `mic_band` (Hospital), `mural_door` (Ward), lights `lt_crack`, `lt_ship_beam`, `lt_wizard_*`,
  `lt_band_mic`, `lt_mural`. Sprites `thing_wizard`, `thing_headphones`, `thing_crack`, `thing_mic`, `thing_mural` come from the chapters' generators (`tex_night_one.py`, `tex_hospital.py`,
  `tex_mental_hospital.py`, listed in `tiles.py`; `build_assets.py <chapter> tiles` is deterministic). The wizard billboard reuses the trial's wizard portrait; A should hide the
  `_gate` button and wizard `TextureRect` of `run_play.gd` when the hotspot is live. The balcony rail and the decks are `pos` anchors (they are occluders, not things).
- No new routes, scenes or waypoints were added: all existing routes remain, each is taken by an exit hotspot (the checker's reachability walks success and failure branches from `warehouse`; the
  Bassment is entered by the wizard's route `"1"` and returns to the entry scene).

Checks run: `check_hotspots.py` (0 errors), `--filter story_map` (16748 checks, 0 failures), `--filter run_` (0 failures), `--filter story_world`, `tools/story/check_assets.py` (OK), `make_scenes.py`
idempotent. Screenshots of the new things in their rooms: wizard on the floor, headphones on the decks, the crack, the bandstand mic, the painted door.

### Workstream A: the core interaction engine (Sonnet, 2026-11-04/05)

Commits "Visual, A contract and validation / engine / view / RunPlay". `HotspotContract` (validator, vocabularies), `RunData` and `TrialData` load and validate the hotspot files, `RunHotspots` (pure
engine), `HotspotView` (looks, projection, nearest-within-radius hit test, edge beacons), `RunPlay` (taps, keys 1 to 4, wizard as a character hotspot, outcomes to `RunEngine` / `RunJourney`), arrows and
exits view behind `RW_RUN_ARROWS=1` (default off; the coordinator removes them once D has landed). Documented in `docs/CONTINUOUS_RUN.md` "Hotspots".
Decisions: the outcome is resolved at the last block's decision (beat 60.5 to 60.75) *before* the next phase is charted, so the chart pack is the resolved route's (no late swap, section C's five
diverting outcomes are safe); nothing tapped is the default exit regardless of performance; the wizard (route `"1"` or `"trial:N"`) has an *early* window (blocks 1 and 2) because the entry needs two
guards; keep-flags are `keep:`-prefixed; the Bassment's minimum is 1 hotspot per passage (37 passages have one way on); `challenge` is validated but not consumed. Verified against C's 127 hotspots:
validator 0 errors, `walk_run.sh perfect_a` OK, `walk_trial.sh` OK (the entry from the wizard hotspot), run and hotspot tests green.

### D, the Bassment conversion (Sonnet, 2026-11-05)

Commits "Visual, D hotspots", "Visual, D scene", "Visual, D tests, walks, shots and docs". `docs/VisualChoicePlan.md` was not in the repository when this was built: the plan's sections were the brief.

* **Data**: `content/trial/hotspots.json` (made by `tools/trial/make_hotspots.py` from `passages.json`, never edited by hand): 95 hotspots for the 64 passages (63 plus the defeat passage), keyed by passage, `trial.<passage>.<n>` (n is the index in the passage's full choice list,
  gated choices included): 74 exit (anchor `{"waypoint": exit_wp}`), 10 encounter (anchor a marker thing `hs_<creature>` at the figure's spot), 7 feature (the luck tests: junction box, pipes, barrels, mirror (marker `hs_mirror`), rope, palm path, the door), 4 object (the cracked crystal,
  the dark archway, the velvet-rope token, the stone palm). Beyond the contract's keys each carries `choice` (the index) and `challenge.phrase`; `on_success.caption` is the consequence text; `on_failure` is `{hold, make_default, caption}` for a plain choice,
  `{hold, make_default, lives, on_defeat: {route: "0"}, caption}` for a fight, `{route: <fail passage>}` for a luck test, null for the way out. The only edit to the zone maps is the 11 marker `thing` lines (ids starting `hs_`, `thing_glow` at size 0.05, rewritten on every run of the script).
  `src/trial/trial_hotspots.gd` loads it (visible-with-items, anchor point) and validates it against `passages.json` and the maps; `check_maps.gd` and `tests/test_trial.gd` run that. It lives outside `trial_data.gd`, which the engine workstream owns.
* **Scene**: caption band (narrative only; consequence and stumble lines kept), no floating labels or numbers, a thin no-text bar for the four bars, hotspots as light in the room (ring and glow, the default brighter with corner ticks, the selected gold with a second ring, a committed one flashing a beat), creatures standing in the room as soon as the window opens
  (the fight is a tap on them), keys 1 to 4 kept, the wizard entry untouched (`run_play.gd` is not mine). `RW_TRIAL_TAPS` makes scripted picks real taps.
* **Fallback to delete at the merge with A**: `src/trial/trial_hotspot_fallback.gd` (the lights, the hit test, edge chevrons for hotspots behind the camera) and in `trial_scene.gd` the `_hot` field, `_sync_hotspots`, `hotspot_items/rects`, `tap_at`, `tap_hotspot` and the `_hot_key` re-sync in `update`, replaced by A's `hotspot_view` fed the same data
  (`TrialHotspots.visible`/`anchor_point` give availability and the anchor's world position; `hotspot_of(index)` the data). `RunExitsView` is no longer used by the Bassment.

### Integration (Sonnet, 2026-11-05)

A, C and D merged on `feature/visual-adventure`; the old navigation is gone. Details and the launch notes: `docs/VISUAL_RHYTHM_ADVENTURE_HANDOVER.md`; the matrix: `docs/VISUAL_COVERAGE.md` (127 run hotspots in 36 scenes and the Bassment's 95, all `verified`).

* **Merge of D**: conflicts were only in this file (both notes kept); `tests/test_trial.gd` and `trial_scene.gd` merged cleanly (A's hotspot wizard test and D's tests both stand).
* **One engine for both**: deleted `src/trial/trial_hotspot_fallback.gd` and in `trial_scene.gd` the `_hot`, `_sync_hotspots`, `_hot_key` re-sync, `hotspot_rects`, `tap_at`, `tap_hotspot`. `TrialScene` builds one `HotspotView` per zone stage (inside its low-res picture, like the run's) and feeds it
  `hotspot_items` (the open window's hotspots, the default brighter only while nothing is picked, the selected one, the committed one for a flash, only once the passage's zone is the one on screen). Touches arrive from `RunPlay._input` to `TrialScene.hotspot_tap(pos)` (stage area only, never over a pad,
  nearest within the projected radius, at least min_px); `tap_centre(index)` is the scripted finger. `TrialHotspots` stays (it loads and normalises the passage-keyed data, `visible` for availability against the held items, and the agreement check against `passages.json` and the maps); `anchor_point` is gone (`HotspotView.resolve`).
* **Contract change** (`hotspot_contract.gd`): the Bassment's default may be any kind (a fight, a luck test or an item), through validator context `default_any_kind` (TrialData sets it; a run scene's default is still an exit and unconditional); `trial_kind` is a contract field (the Bassment's own name for `kind`, validated to equal it);
  `tools/trial/make_hotspots.py` now writes the real `kind` for defaults (it used to write `exit`), and the Bassment's failure semantics stay in `TrialFlow` (documented in the contract header).
* **Retired for good**: `RW_RUN_ARROWS`, the route buttons and `_sync_route_buttons`, `exit_items`, `RunExitsView` (file deleted), the wizard's overlay picture and "Enter the Trial" button, the arrow keys, and their tests (the arrows-behind-the-flag tests, the lit-exit placement test); the hotspot touch-target tests stay.
* **Fixed on integration**: the matrix test's "perfect play never visits the bad rail" is skipped under the `failure` tap policy (it misses the last block on purpose); `capture.sh` no longer lets ffmpeg or godot read the scene list from stdin.
* **Added**: a test resolving every shipped run hotspot both ways, hotspot-window shots of every scene and a contact sheet per world (`tools/run/contact_hotspots.py`), the Bassment section of the coverage matrix.
* **Verified**: full suite, the matrix under every tap policy, `walk_run.sh` (all paths, all four policies), `walk_trial.sh`, `walk_campaign.sh`, `check_hotspots.py`, `validate.gd`, `check_maps.gd`; frames per world (perfect play, two phases, not an idle machine): Warehouse mean 11.8 ms p95 14.5, Mothership 12.5 / 16.3, Underworld 12.3 / 17.0, Hospital 14.5 / 17.5,
  Ward 13.0 / 16.7, Hospital late 13.1 / 16.9, Ward late 12.5 / 18.9 (one frame over 50 ms, a stage build); against the pre-hotspot numbers in `docs/CONTINUOUS_RUN.md` (Warehouse 12.1, Mothership 13.4, Underworld 13.6, Hospital 13.8) the view costs well under 1 ms.
* **For the Opus look pass**: the edge beacons (hotspots behind the camera) are dim; the camera faces away from the exits when the window opens; the lights read faint at the contact-sheet size (`docs/shots/run/contact_hotspots_<world>.jpg`, `docs/shots/trial/contact_bassment.jpg`).
