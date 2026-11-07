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

Scenes (placeholders, see `tools/run/make_doom.py`): `doom_warehouse` (entry; routes: stay on the floor (default), `doom_balcony` ahead, `doom_bar` left, `doom_warehouse.chill` right: the stand-in for the lounge world below). The three destinations
are ALIASES of the same scene and map until the real ones exist; each leads on to `doom_warehouse.return`, the world's exit scene, whose two routes loop back to the floor.

## The Copper Bar (`doom_bar`, docs/doom/scenes/bar.md)

A second world in the overlay: `doom_bar` (map `doom_bar`, depth 2), entry scene `doom_bar` (the Copper Bar: guides for the Booth ahead, the Floor left, the Chill-out right, and a stay hotspot), three in-world
stand-ins `doom_bar.booth`, `doom_bar.floor`, `doom_bar.chill` and the exit scene `doom_bar.return` (loops back); its data is in `tools/run/make_doom_bar.py`. It is reached from the Warehouse through the Warehouse's
exit scene (`doom_warehouse.return`, route left): a run node takes its map from its world and only an exit scene may leave a world, so the Warehouse's own "bar" stand-in is now `doom_warehouse.bar` (it leads to
the return scene). `RW_RUN_START=doom_bar` plays the Bar directly. The guides' real thresholds (a walk to the threshold, then the other world's arrival) wait for engine hook H1.6.

## The Chill-out Lounge (`doom_lounge`, MAP08; `docs/doom/scenes/lounge.md`)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "C:\Users\joesa\Documents\Cursor\MusicGame-env-chill\tools\dev\play_doom_worlds.cmd" --scene doom_lounge` (same track packs as above) |
| By hand | `RW_DOOM_WORLDS=1 RW_RUN_START=doom_lounge`, then `src/run/run_play.tscn` |
| Rebuild the geometry | `python -I tools/doom/trace/lounge_scene.py && python -I tools/doom/convert.py --scene lounge --trace tools/doom/trace/lounge_pilot.json && python -I tools/doom/author_lounge.py` |
| Rebuild the art | `python -I tools/doom/art/make_lounge_art.py && python -I tools/doom/art/make_lounge_guides.py`, then `godot --headless --import` |
| Regenerate the data | `python tools/run/make_doom.py` (the lounge's world, scenes, rail, hotspots and story come from `tools/run/make_doom_lounge.py`) |
| Shots | `bash tools/doom/shoot_lounge.sh` (one contact sheet in `docs/shots/doom/lounge/`; `RW_KEEP=<dir>` keeps the per-frame jpgs for looking), then `python3 tools/doom/shoot_lounge.py walk docs/shots/doom/lounge` (the walk strip) |
| Tests | `... -- --filter doom_views` (the `test_lounge_*` block), `check_rail_paths.gd -- res://content/run/doom/run.json` |

The lounge is its own WORLD (`doom_lounge`, depth 2, map `doom_lounge`) because a scene's map is its world's map and only a world's exit scene may route to another world. Entry scene `doom_lounge`; stand-ins
`doom_lounge.dock` (ahead), `.bar` (left), `.floor` (right), each leading on to the exit scene `doom_lounge.return`. The Warehouse floor reaches it through ITS exit scene (`doom_warehouse.return`, route `right`);
the Warehouse's old `doom_lounge` alias is now the stand-in `doom_warehouse.chill`.

## Known limits (7 November)

No state-driven guides beyond what the existing choice staging does (sprite per state, no loop playback, no brightening lamp); the rail's moves are polylines with holds, but the exits' door walks (ahead, left, right) still go straight to the next scene's arrival (`rail.routes` is checked, not yet played); the terrace and the north-west nub are not connected to the ring; the guides are placeholder art.

## The DJ Booth (scene `doom_booth`, env-booth block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_booth` (world `doom_booth`; routes: stay in the booth (default), `doom_booth.mothership` ahead, `doom_booth.balcony` left, `doom_booth.dock` right: stand-ins that lead to `doom_booth.return`) |
| Rebuild the geometry | `python -I tools/doom/trace/booth_scene.py && python -I tools/doom/convert.py --scene booth --trace tools/doom/trace/booth_pilot.json && python -I tools/doom/author_booth.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_booth_art.py`, then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_booth.py`) |
| Shots | `python3 tools/doom/shoot_booth.py` (`docs/shots/doom/booth/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the booth block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_booth` |

Details: `docs/doom/scenes/booth.md`.

## The Loading Dock (scene `doom_dock`, env-dock block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_dock` (world `doom_dock`, depth 2; routes: stay on the dock (default), `doom_dock.mothership` ahead, `doom_dock.floor` left, `doom_dock.underworld` right: stand-ins that lead to `doom_dock.return`) |
| Rebuild the geometry | `python -I tools/doom/trace/dock_scene.py && python -I tools/doom/convert.py --scene dock --trace tools/doom/trace/dock_pilot.json && python -I tools/doom/author_dock.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_dock_art.py` (calls `make_dock_guides.py`), then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_dock.py`) |
| Shots | `python3 tools/doom/shoot_dock.py` (`docs/shots/doom/dock/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the dock block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_dock` |

Details: `docs/doom/scenes/dock.md`.



## The Underworld (scene `doom_underworld`, MAP29, env-underworld block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_underworld` (world `doom_underworld`, depth 2; routes: stay on the plateau (default), `doom_underworld.mothership` ahead, `doom_underworld.floor` left, `doom_underworld.dock` right: stand-ins that lead to `doom_underworld.return`) |
| Rebuild the geometry | `python -I tools/doom/trace/underworld_scene.py && python -I tools/doom/convert.py --scene underworld --trace tools/doom/trace/underworld_pilot.json && python -I tools/doom/author_underworld.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_underworld_art.py && python -I tools/doom/art/make_underworld_guides.py`, then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_underworld.py`, which also writes `content/run/doom/story_doom_underworld.json`) |
| Shots | `python3 tools/doom/shoot_underworld.py` (`docs/shots/doom/underworld/contact.jpg`, `walk_strip.jpg`, `walk_*.txt`; `RW_KEEP=<dir>` keeps the per-frame jpgs for `tools/doom/frame_check.py`) |
| Tests | `--filter doom_views` (the underworld block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_underworld` |

The abyss is a set of `abyss_*` sectors the engine treats as a void; every portal onto it is a `railing` (chain strip) shut to walkers, but one dead-end portal on the tower's north rim (6.0, 35.5) that the map loader
needs to keep the map connected. Details: `docs/doom/scenes/underworld.md`.


## The Mothership (scene `doom_mothership`, env-mothership block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_mothership` (world `doom_mothership`; routes: stay on the ring (default), `doom_mothership.underworld` ahead, `doom_mothership.booth` left, `doom_mothership.dock` right: stand-ins that lead to `doom_mothership.return`) |
| Rebuild the geometry | `python -I tools/doom/trace/mothership_scene.py && python -I tools/doom/convert.py --scene mothership --trace tools/doom/trace/mothership_pilot.json && python -I tools/doom/author_mothership.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_mothership_art.py && python -I tools/doom/art/make_mothership_guides.py`, then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_mothership.py`) |
| Shots | `python3 tools/doom/shoot_mothership.py` (`docs/shots/doom/mothership/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the mothership block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_mothership` |

Details: `docs/doom/scenes/mothership.md`.


## The Balcony (scene `doom_balcony`, env-balcony block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_balcony` (world `doom_balcony`; routes: stay on the roof (default), `doom_balcony.mothership` ahead, `doom_balcony.floor` left, `doom_balcony.booth` right: stand-ins that lead to `doom_balcony.return`). The Warehouse's own stand-in is now `doom_warehouse.balcony`. |
| Rebuild the geometry | `python -I tools/doom/trace/balcony_scene.py && python -I tools/doom/convert.py --scene balcony --trace tools/doom/trace/balcony_pilot.json && python -I tools/doom/author_balcony.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_balcony_art.py` (calls `make_balcony_guides.py`), then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_balcony.py`) |
| Shots | `python3 tools/doom/shoot_balcony.py` (`docs/shots/doom/balcony/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the balcony block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_balcony` |

Details: `docs/doom/scenes/balcony.md`.
