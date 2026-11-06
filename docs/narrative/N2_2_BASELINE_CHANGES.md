# N2.2: what changed in the baselines and the pinned checks

**None.** `tests/test_run_tracks_safety.gd` drives `RunEngine` and `RunHotspots` directly without the router. `RunHotspots.ungated_quest_routes` is off by default and only `RunPlay` turns it on, so the recording `tests/fixtures/track_scenes/baseline_runs.json` is untouched and was not re-recorded.

No existing check was changed. One check caught a behaviour change during the work, `test_run_ember.gd` `test_the_snatched_failure_of_the_pool_is_the_same_ending_with_its_cinematic`. The code was fixed rather than the test: a quest route whose failure leads the same way keeps its authored failure outcome (see `N2_2_ROUTER.md`, "Decisions").
