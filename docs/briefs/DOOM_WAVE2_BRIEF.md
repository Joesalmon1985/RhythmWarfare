# Doom worlds, wave 2: one brief for the Balcony, the Dock, the Mothership and the Underworld

Read first: `docs/briefs/DOOM_WORLDS_BRIEF.md` (the owner's brief, the routing table), `docs/parallel-development/LEAD_RULINGS.md` rulings 35–38
(stationary choice moments, no rings, concept paintings are the bar, one world one HUD), `docs/doom/CONVERSION.md`, `docs/doom/LAUNCH.md`, and the
three finished scene docs `docs/doom/scenes/warehouse.md`, `booth.md`, `bar.md`, `lounge.md`. The Booth is the pattern to copy (its files are listed in
`booth.md`; its generator `tools/run/make_doom_booth.py` has the signature `add(P, worlds, nodes, cin, music, extra_hot)` that `make_doom.py` calls).

## Each scene

| Scene | Map | Painting (`art/reference/doom_worlds/`) | Trace | Routes (ahead / left / right) |
| --- | --- | --- | --- | --- |
| Balcony `doom_balcony` | MAP15 Industrial Zone | `Rainy industrial rooftop, three musical paths-8.png` (also `Rain-Slick Rooftop Crossroads-3.png`) | `tools/doom/trace/balcony.json` | Mothership / Floor / Booth |
| Dock `doom_dock` | MAP13 Downtown | `Rainy Rhythm Club Loading Dock-6.png` (also `Rainy Dock of Three Paths-7.png`) | `tools/doom/trace/dock.json` | Mothership / Floor / Underworld |
| Mothership `doom_mothership` | MAP11 Circle of Death | `Mothership Ringwalk Over the Void-7.png` (also `Mothership atrium_ three paths, one stay-8.png`) | `tools/doom/trace/mothership.json` | Underworld / Booth / Dock |
| Underworld `doom_underworld` | MAP29 The Living End | `Three Paths Across the Basalt Abyss-4.png` (also `Three Visitors in the Basalt Underworld-6.png`) | `tools/doom/trace/underworld.json` | Mothership / Floor / Dock |

The render trace gives the macro footprint; where it does not give the room the painting wants (the Booth's case), build the room from the painting on a
0.25 m grid in `tools/doom/trace/<scene>_scene.py` + `<scene>_pilot.json`, and say so in the scene doc. The map is `content/story/maps/doom_<scene>.json`
(APPROXIMATE flag, `max_step` 0.5, `visibility.mode` clip, fog), authored by `tools/doom/author_<scene>.py`; art by `tools/doom/art/make_<scene>_art.py`
and `make_<scene>_guides.py` into `assets/story/doom_<scene>/textures/` (procedural placeholders, named as placeholders; keep the guide sprite stems
`guide_<dest>_<state>_0` for `idle`, `available`, `selected`, `committed`).

## The world shape (this wave is the LAST with stand-ins)

Build the world as the Booth did: entry scene `doom_<scene>` (the real room, reference viewpoint `<xx>_ref` holding 8 bars, a stay loop of three 2-bar
reveal viewpoints then `<xx>_ref`, `rail.routes` `up`/`left`/`right` as via polylines WITH `hold_bars` at the threshold waypoint, plus `stumble` and
`arrive`), stand-ins `doom_<scene>.<dest>` and the exit scene `doom_<scene>.return` looping back. Worlds are depth 2. An engine package (geography
worlds, hook H1.6) is being built in parallel that will let the entry scene route straight into the other worlds; the stand-ins will then be deleted by a
generator change. So: put every piece of knowledge the real cut will need into the DATA now — the threshold waypoint is the `to` of each route move, the
doorway is `rail.exits[dir]`, the route labels are the destination names — and keep the stand-ins trivial.

The generator: `tools/run/make_doom_<scene>.py` exposing `add(P, worlds, nodes, cin, music, extra_hot)` exactly like the Booth's, and in
`tools/run/make_doom.py` add ONLY a two-line marked block right after the Lounge's block (`# --- the <Scene> (env-<scene>): ...` then `import` + `add`).
Nothing else in `make_doom.py` changes. Run `python tools/run/make_doom.py` and commit the regenerated `content/run/doom/*` (the lead regenerates again at
the merge). Music: the Warehouse arrangements as the others do.

Tests: a separate block at the END of `tests/test_doom_views.gd` (`# --- the <Scene> ...`, its own `<XX>_*` constants, the same checks as the Booth block:
map loads clean with every route waypoint and hold; the guides inside the 16:9 and 20:9 picture, apart, off the pad strip, at least 60 px tall at the
reference viewpoint, with a sightline test against the solid walls; every via stands in a walkable piece and `StoryRailCheck.check_rail` finds nothing; the
overlay's world, nodes, hotspots and rail validate; the art is in the map). Do not edit the earlier blocks. `docs/doom/LAUNCH.md`: one new section appended
at the END of the file. `docs/doom/scenes/<scene>.md` like the Booth's (what matches the painting, what does not, placeholders, hooks needed).

Shots in `docs/shots/doom/<scene>/`: `contact.jpg` (the painting beside the reference viewpoint, then every viewpoint as a 16:9 | 20:9 pair) and
`walk_strip.jpg` with `walk_*.txt` pose tables, by `tools/doom/shoot_<scene>.py` (copy `shoot_booth.py`). Look at your own shots before reporting: a
guide must read as a figure at a doorway, the room as the painting's room. Run `tools/doom/frame_check.py` for exposure.

## Commands

- Tests: `RW_AUDIO_WORK="C:/Users/joesa/rw-audio-work" bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter doom`
  then `rail_paths`, `run_`, `playtest`, `story`. The runner prints "0 failures" on a parse error: ALWAYS count `SCRIPT ERROR` lines too. First run
  `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . --import` in the fresh worktree (else "Could not find type TestCase").
- `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/story/check_rail_paths.gd -- res://content/run/doom/run.json` → 0 problems.
- `python tools/doom/check_world.py`, `... -s tools/doom/check_doom_map.gd -- doom_<scene>`.
- Play: `tools/dev/play_doom_worlds.cmd --scene doom_<scene>` (see LAUNCH.md).

## Rules

Work only in your worktree. Never push, merge, rebase or reset; commit WIP checkpoints ("WIP: ..."). Never touch `src/` (report a hook instead). The WAD,
Doom textures/sprites/audio and the renders are never committed (`.gitignore` has `*.wad`, `/doom II wads/`); the track packs are never committed. Do not
claim anything you did not run. Report at the end: commits, every test count (checks, failures, SCRIPT ERROR count), what matches the painting and what
does not, what is placeholder, the hooks you would need.
