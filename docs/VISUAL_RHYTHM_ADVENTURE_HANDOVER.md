# Visual rhythm adventure: handover

Branch `feature/visual-adventure` (the integration branch; workstreams A, C and D are merged and the old navigation is removed). The final commit is the head of that branch after the integration
commits listed in `docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md` section 10 ("Integration"). Read the plan (`docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md`) and the owner's brief (`docs/VisualChoicePlan.md`, sections 2 and 9)
first; the engine is documented in `docs/CONTINUOUS_RUN.md` "Hotspots" and the Bassment in `docs/TRIAL_OPENING.md`; every world, scene and hotspot with its S and F outcomes is in `docs/VISUAL_COVERAGE.md`.

## What the game is now

Four pads plus touching the world. In the last block of a scene the room's things light up (a doorway, a person, an object, a creature); the player touches one (touch another to change, keys 1 to 4 on a
desktop), and the performance of the last block decides: passed gives the hotspot's success outcome, missed its failure outcome. Nothing touched takes the brighter default exit whatever the
performance. There are no arrows, no choice text, no `[DEFAULT]` tags, no "Enter the Trial" button: the wizard is a character in the room. The Bassment (63 passages, 16 zones) uses the same
hotspot contract and the same `HotspotView`; its passage text is a caption band (narrative, not navigation) and a thin bar shows the four-bar window.

| Piece | Where |
| --- | --- |
| Contract (fields, vocabularies, validator; a non-exit default and `trial_kind` for the Bassment) | `src/run/hotspot_contract.gd` |
| Pure engine: availability, selection, commit, outcome, world state | `src/run/run_hotspots.gd` |
| View: looks, projection, hit test, edge beacons | `src/run/hotspot_view.gd` (one per run stage and one per Bassment zone stage) |
| Run scene: taps, keys, wizard, outcomes to the engine and the rails | `src/run/run_play.gd` |
| Bassment: caption band, hotspots from the passage's choices, creatures standing as hotspots, touches | `src/trial/trial_scene.gd`, `src/trial/trial_hotspots.gd` (data loader and agreement check), `tools/trial/make_hotspots.py` |
| Data | `content/run/hotspots/<world>.json` (127), `content/trial/hotspots.json` (95), `content/run/run.json` `cinematics` (138) |

Failure semantics: a run scene's failed hotspot has its own `on_failure` (a setback or another door). In the Bassment they stay in `TrialFlow` (a failed plain choice holds the place and becomes the
default, a lost fight counts toward three, a luck miss goes its other way); the data only names the luck test's other passage.

## How to launch

No flags are needed: open `project.godot` and press Play (Home, Play enters the run), or `godot --path . res://src/run/run_play.tscn`. Scripted play for tests and recordings (virtual clock, no audio):
`RW_RUN_VIRTUAL=1 RW_RUN_BOT=perfect|none|accuracy:<f>|blocks:<bits> RW_RUN_ROUTES=<dir per phase> RW_RUN_TAPS=scripted|none|changed|failure RW_RUN_START=<scene> RW_RUN_UNTIL_PHASE=<n>`; the Bassment:
`RW_TRIAL_ENTER=1` from the Warehouse (the wizard), `RW_TRIAL_DIRECT=1 RW_TRIAL_START=<passage>`, `RW_TRIAL_TAPS="1;d;0"` (one token per window: a hotspot index to touch, or d for none).
`RW_RUN_ARROWS` no longer exists.

## Tests executed on the integrated branch

* Full Godot suite: `godot --headless --path . -s tests/run_tests.gd`: 62344 checks, 0 failures (on the final code).
* `tests/test_hotspots_engine.gd`: 684 checks, 0 failures (includes the new test that resolves every shipped run hotspot both ways, success and failure).
* Run matrix `--filter run_matrix` under every tap policy (scripted 651, none 652, changed 649, failure 635 checks): 0 failures. The perfect-play "never visits the bad rail" assertion is skipped under `failure`, which misses the last block on purpose.
* `tools/run/walk_run.sh` for all seven paths and every `RW_RUN_TAPS` policy (scripted, none, changed, failure): OK; the scripted and changed walks visit 36 of 36 scenes.
* `tools/trial/walk_trial.sh` (the defaults to the victory, and by real taps: 3 made, 3 hit the hotspot aimed at): OK. `tools/story/walk_campaign.sh`: OK.
* `python3 tools/run/check_hotspots.py`: 0 errors, 5 warnings (the known route-lock chart-pack differences, safe because the outcome is resolved before the chart is fixed); reachability 36 of 36 scenes,
  52 routes, 93 flags, the Bassment via the wizard. `tools/trial/validate.gd` (63 of 63 reachable from passage 1) and `check_maps.gd` (95 hotspots, all maps) OK.
* Determinism at 30 fps, 60 fps and a variable frame step (`test_the_same_taps_give_the_same_outcomes_at_any_frame_step`) and the Bassment's tap tests.
* Screenshots regenerated: `tools/run/capture.sh` (hotspot window per scene; contact sheets `docs/shots/run/contact_hotspots_<world>.jpg`) and `tools/trial/capture.sh` (`docs/shots/trial/contact_bassment.jpg`).
* Frame time per world (`tools/run/frames.sh`, two phases of perfect play, not an idle machine): mean 11.8 to 14.5 ms, p95 14.5 to 18.9 ms in all seven worlds, one frame over 50 ms (a stage build in Ward late); the view costs under 1 ms.

## Known limitations

* The look is first-pass: the edge beacons for hotspots behind the camera are dim, and the camera faces away from the exits when the window opens (the Opus look pass).
* `challenge` on a run hotspot is validated but not consumed (the last block decides); the Bassment's per-hotspot `challenge.phrase` is likewise informational (the choice's phrase is played by `TrialEngine`).
* Five hotspot outcomes divert to a route with another chart pack than the default (the checker's warnings); they are safe because the outcome is resolved at the decision beat, before the next scene is charted.
* Music outcomes (merged with the music branch): `dip` is wired (`RunAudio`: bass and synth to 0.35 of their gain for 8 beats from the commit beat, through the gain ramps); `variation` stays a documented no-op, because the arrangement of a scene is resolved once at load by the per-run seed and re-picking it for the next scene would change its chart pack after the route lock compared it.
* Android export was not smoke-tested here; screenshots use the desktop renderer.
* Free look (drag, Q/E) is kept as an accessibility option and is never required.

## Remaining work

The Opus look pass (hotspots obvious without text: silhouette, light and motion; selection and commit animations; the echo chamber and the warren; phone readability), the performance pass
(stage build hitches, sheet memory, Android), and merging the music branch (`feature/music-library`), which owns the music files and will consume the outcomes' `music` field.
