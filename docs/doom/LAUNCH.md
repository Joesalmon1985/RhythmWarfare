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

`RW_DOOM_WORLDS=1` makes `RunData` merge `content/run/doom/` into the main run: eight GEOGRAPHY worlds (`docs/engine/GEOGRAPHY_WORLDS.md`, hook H1.6), each ONE scene whose id is the world id
(`doom_warehouse` depth 1, the other seven depth 2), with its music entry (the Warehouse arrangements as the fallback; with the track packs present each world plays its own recorded track, table in `docs/doom/MUSIC.md`), its hotspots in `content/run/doom/hotspots/<world>.json` (three guides and the stay) and its
StoryData `story_doom_<world>.json`. There are no stand-in and no return scenes.

Each scene's `down` route is the stay loop; its three guides lead straight to the entry scenes of other worlds, per the brief's table (ahead = `up`, left, right):

| Scene | up | left | right |
| --- | --- | --- | --- |
| `doom_warehouse` (the Floor) | `doom_balcony` | `doom_bar` | `doom_lounge` |
| `doom_bar` | `doom_booth` | `doom_warehouse` | `doom_lounge` |
| `doom_balcony` | `doom_mothership` | `doom_warehouse` | `doom_booth` |
| `doom_lounge` (the Chill-out) | `doom_dock` | `doom_bar` | `doom_warehouse` |
| `doom_booth` | `doom_mothership` | `doom_balcony` | `doom_dock` |
| `doom_dock` | `doom_mothership` | `doom_warehouse` | `doom_underworld` |
| `doom_mothership` | `doom_underworld` | `doom_booth` | `doom_dock` |
| `doom_underworld` | `doom_mothership` | `doom_warehouse` | `doom_dock` |

Picking a guide walks the route move (`rail.routes[dir]`, ending at its threshold `rail.exits[dir]`) by the boundary, the passage frame shuts, the stage swaps to the destination's map on the
downbeat and the arrival walks home. `RW_RUN_START=doom_<scene>` still starts in any of the eight. Tests: `tests/test_doom_views.gd` (`test_the_overlay_is_one_geography_graph_per_the_brief_table`),
`tests/test_doom_cuts.gd` (a real Warehouse to Bar to Floor cut on the run scene). Shot of that cut: `python3 tools/doom/shoot_cut.py` (`docs/shots/doom/cuts/warehouse_to_bar.jpg`).

## The Copper Bar (`doom_bar`, docs/doom/scenes/bar.md)

The world `doom_bar` (map `doom_bar`, depth 2), one scene `doom_bar` (the Copper Bar: guides for the Booth ahead, the Floor left, the Chill-out right, and a stay hotspot); its data is in
`tools/run/make_doom_bar.py`. The Warehouse's left guide leads straight here. `RW_RUN_START=doom_bar` plays the Bar directly.

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

The lounge is the geography world `doom_lounge` (depth 2, map `doom_lounge`), one scene: ahead the Dock, left the Bar, right the Floor. The Warehouse's right guide leads straight here.

## Known limits (7 November)

No state-driven guides beyond what the existing choice staging does (sprite per state, no loop playback, no brightening lamp); the rail's moves are polylines with holds, and the exits' door walks (ahead, left, right) are played to the threshold before the cut; the terrace and the north-west nub are not connected to the ring; the guides are placeholder art.

## The DJ Booth (scene `doom_booth`, env-booth block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_booth` (world `doom_booth`; depth 2; routes: stay in the booth (default), `doom_mothership` ahead, `doom_balcony` left, `doom_dock` right) |
| Rebuild the geometry | `python -I tools/doom/trace/booth_scene.py && python -I tools/doom/convert.py --scene booth --trace tools/doom/trace/booth_pilot.json && python -I tools/doom/author_booth.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_booth_art.py`, then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_booth.py`) |
| Shots | `python3 tools/doom/shoot_booth.py` (`docs/shots/doom/booth/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the booth block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_booth` |

Details: `docs/doom/scenes/booth.md`.

## The Loading Dock (scene `doom_dock`, env-dock block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_dock` (world `doom_dock`, depth 2; routes: stay on the dock (default), `doom_mothership` ahead, `doom_warehouse` left, `doom_underworld` right) |
| Rebuild the geometry | `python -I tools/doom/trace/dock_scene.py && python -I tools/doom/convert.py --scene dock --trace tools/doom/trace/dock_pilot.json && python -I tools/doom/author_dock.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_dock_art.py` (calls `make_dock_guides.py`), then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_dock.py`) |
| Shots | `python3 tools/doom/shoot_dock.py` (`docs/shots/doom/dock/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the dock block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_dock` |

Details: `docs/doom/scenes/dock.md`.



## The Underworld (scene `doom_underworld`, MAP29, env-underworld block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_underworld` (world `doom_underworld`, depth 2; routes: stay on the plateau (default), `doom_mothership` ahead, `doom_warehouse` left, `doom_dock` right) |
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
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_mothership` (world `doom_mothership`; routes: stay on the ring (default), `doom_underworld` ahead, `doom_booth` left, `doom_dock` right) |
| Rebuild the geometry | `python -I tools/doom/trace/mothership_scene.py && python -I tools/doom/convert.py --scene mothership --trace tools/doom/trace/mothership_pilot.json && python -I tools/doom/author_mothership.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_mothership_art.py && python -I tools/doom/art/make_mothership_guides.py`, then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_mothership.py`) |
| Shots | `python3 tools/doom/shoot_mothership.py` (`docs/shots/doom/mothership/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the mothership block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_mothership` |

Details: `docs/doom/scenes/mothership.md`.


## The Balcony (scene `doom_balcony`, env-balcony block)

| What | How |
| --- | --- |
| Play it | PowerShell: `& "<this checkout>\tools\dev\play_doom_worlds.cmd" --scene doom_balcony` (world `doom_balcony`; routes: stay on the roof (default), `doom_mothership` ahead, `doom_warehouse` left, `doom_booth` right). The Warehouse's up guide leads straight here. |
| Rebuild the geometry | `python -I tools/doom/trace/balcony_scene.py && python -I tools/doom/convert.py --scene balcony --trace tools/doom/trace/balcony_pilot.json && python -I tools/doom/author_balcony.py` |
| Rebuild the art and guides | `python -I tools/doom/art/make_balcony_art.py` (calls `make_balcony_guides.py`), then `godot --headless --import` |
| Regenerate the overlay | `python tools/run/make_doom.py` (calls `tools/run/make_doom_balcony.py`) |
| Shots | `python3 tools/doom/shoot_balcony.py` (`docs/shots/doom/balcony/contact.jpg`, `walk_strip.jpg`) |
| Tests | `--filter doom_views` (the balcony block at the end), `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_balcony` |

Details: `docs/doom/scenes/balcony.md`.
