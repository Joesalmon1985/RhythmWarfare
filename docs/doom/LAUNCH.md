# Launching the Doom worlds pilot (Warehouse)

The Doom scenes are behind a flag and an overlay: nothing in `content/run/run.json` or the legacy campaign changes.

| What | How |
| --- | --- |
| Play the pilot | PowerShell: `& "C:\Users\joesa\Documents\Cursor\MusicGame-envwh\tools\dev\play_doom_worlds.cmd" --scene doom_warehouse` (needs the track packs: `RW_TRACKS_DIR` or `<RW_AUDIO_WORK>\packs`, as `play_tracks.cmd`) |
| By hand | `RW_DOOM_WORLDS=1 RW_RUN_START=doom_warehouse` then run `src/run/run_play.tscn` (`bash tools/dev/play_tracks.sh --run` passes the variables through) |
| Play the Copper Bar | `tools\dev\play_doom_worlds.cmd --scene doom_bar` (from the `MusicGame-env-bar` checkout, branch `wip/env-bar`) |
| Rebuild the Copper Bar | `python -I tools/doom/trace/bar_scene.py && python -I tools/doom/convert.py --scene bar --trace tools/doom/trace/bar_pilot.json && python -I tools/doom/art/make_bar_art.py && python -I tools/doom/art/make_bar_guides.py && python -I tools/doom/author_bar.py`, then `python tools/run/make_doom.py` and `godot --headless --import` |
| Bar shots | `python3 tools/doom/shoot_bar.py [--walk]` (one contact sheet, plus the walk strips with `--walk`, in `docs/shots/doom/bar/`) |
| Legacy campaign | no variable set: the game is as before |
| Regenerate the data | `python tools/run/make_scenes.py --doom` (or `RW_DOOM_WORLDS=1`), or `python tools/run/make_doom.py` for the overlay alone |
| Rebuild the geometry | `python -I tools/doom/trace/warehouse_scene.py && python -I tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse_pilot.json && python -I tools/doom/author_warehouse.py` |
| Rebuild the guides | `python -I tools/doom/art/make_guides.py`, then `godot --headless --import` |
| Shots | `bash tools/doom/shoot_scene.sh --scene doom_warehouse` (contact sheets in `docs/shots/doom/warehouse/`) |
| Tests | `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter doom_views` |

## What the flag adds

`RW_DOOM_WORLDS=1` makes `RunData` merge `content/run/doom/` into the main run: the world `doom_warehouse` (its StoryData `story_doom_warehouse.json` is the Night One cast with the camera moves taken out),
five scenes, their music entries (the Warehouse arrangements), the hotspots in `content/run/doom/hotspots/doom_warehouse.json` and three cinematics.

Scenes (placeholders, see `tools/run/make_doom.py`): `doom_warehouse` (entry; routes: stay on the floor (default), `doom_balcony` ahead, `doom_bar` left, `doom_lounge` right). The three destinations
are ALIASES of the same scene and map until the real ones exist; each leads on to `doom_warehouse.return`, the world's exit scene, whose two routes loop back to the floor.

## The Copper Bar (`doom_bar`, docs/doom/scenes/bar.md)

A second world in the overlay: `doom_bar` (map `doom_bar`, depth 2), entry scene `doom_bar` (the Copper Bar: guides for the Booth ahead, the Floor left, the Chill-out right, and a stay hotspot), three in-world
stand-ins `doom_bar.booth`, `doom_bar.floor`, `doom_bar.chill` and the exit scene `doom_bar.return` (loops back); its data is in `tools/run/make_doom_bar.py`. It is reached from the Warehouse through the Warehouse's
exit scene (`doom_warehouse.return`, route left): a run node takes its map from its world and only an exit scene may leave a world, so the Warehouse's own "bar" stand-in is now `doom_warehouse.bar` (it leads to
the return scene). `RW_RUN_START=doom_bar` plays the Bar directly. The guides' real thresholds (a walk to the threshold, then the other world's arrival) wait for engine hook H1.6.

## Known limits (7 November)

No state-driven guides beyond what the existing choice staging does (sprite per state, no loop playback, no brightening lamp); the rail's moves are polylines with holds, but the exits' door walks (ahead, left, right) still go straight to the next scene's arrival (`rail.routes` is checked, not yet played); the terrace and the north-west nub are not connected to the ring; the guides are placeholder art.
