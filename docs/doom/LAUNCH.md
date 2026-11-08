# Launching the Doom worlds (eight geography worlds)

Written 9 November 2026 on `feature/doom-layout-worlds`. Your checkout is `C:\Users\joesa\Documents\Cursor\MusicGame-env`.
The old worktrees (`MusicGame-envwh`, `MusicGame-env-chill`, `MusicGame-env-bar`, branch `wip/env-bar`) no longer carry the work. Do not use them.

The Doom worlds sit behind a flag and an overlay. Nothing in `content/run/run.json` or the legacy campaign changes. With no flag set, the game is as before.

Nobody has yet played a Doom world on a screen or a phone. Everything below was checked headless or from shots. Please say what feels wrong.

## How to play

You need the track packs: `RW_TRACKS_DIR`, or `<RW_AUDIO_WORK>\packs`, as for `play_tracks.cmd`. Without a pack, that world plays its procedural arrangement instead.

`play_doom_worlds.cmd` takes one flag, `--scene <id>`. It sets `RW_DOOM_WORLDS=1` and `RW_RUN_START=<id>`, then runs `play_tracks.sh --run` through Git Bash. The scene defaults to `doom_warehouse`.

PowerShell:

```
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd"
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_warehouse
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_bar
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_lounge
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_booth
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_dock
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_balcony
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_mothership
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_underworld
```

By hand: set `RW_DOOM_WORLDS=1` and `RW_RUN_START=doom_<scene>`, then run `src/run/run_play.tscn`. `bash tools/dev/play_tracks.sh --run` passes the variables through.

Regenerate the data: `python tools/run/make_scenes.py --doom` (or `RW_DOOM_WORLDS=1`), or `python tools/run/make_doom.py` for the overlay alone.

## What the flag adds

`RW_DOOM_WORLDS=1` makes `RunData` merge `content/run/doom/` into the main run: eight GEOGRAPHY worlds (`docs/engine/GEOGRAPHY_WORLDS.md`, hook H1.6). Each is ONE scene whose id is the world id. `doom_warehouse` is depth 1; the other seven are depth 2.
Each has a music entry, its hotspots in `content/run/doom/hotspots/<world>.json` (three guides and the stay) and a StoryData file `story_doom_<world>.json`. There are no stand-in and no return scenes.

Each scene's `down` route is the stay loop. Its three guides lead straight to the entry scenes of other worlds (ahead = `up`, left, right):

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

Picking a guide walks the route move (`rail.routes[dir]`, ending at its threshold `rail.exits[dir]`), the passage frame shuts, the stage swaps to the destination's map and the arrival walks home. `RW_RUN_START` starts you in any of the eight.

## Walk pace (rulings 42, 42b, 43)

Walk-outs run at 3 m/s or less, over 2 to 8 bars. The doorway hold and the cut are unchanged and the music keeps playing.
On a long leg (over about 14.5 m from a tap at beat 50) the next phase and its music start on time, but the picture swaps worlds only when the hold ends, never later than beat 32 of the next phase. So on a long leg the cut lands after the drop. This is accepted for the first playable, and you may overrule it.
`check_rail_paths.gd -- res://content/run/doom/run.json` prints each leg's WALKOFF line, measured from the worst-case rail place (ruling 43). Today: 8 scenes, 0 problems, 1 warning (Warehouse, up from `wh_platform`, 53.7 m; agent A is fixing it).

## What to expect, scene by scene

Each line gives the painting in `art/reference/doom_worlds/` and the lead's verdict (ruling 36: the paintings are the bar). Contact sheets are `docs/shots/doom/<scene>/contact.jpg`.

Round 2 of polish is merged for the Underworld, Mothership, Dock, Balcony and Booth. Round 2 for the Warehouse, Bar and Lounge is in progress (agent A).

* **The Floor, `doom_warehouse`** (`Cobalt Warehouse Dance Floor-1.png`; guides cropped from `Midnight dance hall with three guides-1.png`). A fenced cobalt dance floor seen along its diagonal; stage ahead, bar left, lounge right. No lead verdict yet (round 2 pending). Exposure: 13 of 17 shots in the rule at the last measure; four are short of contrast. The room is far larger than the painting's, and the stage guide is small (64 px at 16:9).
* **Copper Bar, `doom_bar`** (`Copper Basement Bar, Three Hidden Routes-3.png`). A long stone passage under copper mains to a lit booth, the Floor guide at her post, a copper counter. No lead verdict yet (round 2 pending). At the last measure 4 of 21 shots were in the rule; the Booth guide is procedural and small.
* **Chill-out Lounge, `doom_lounge`** (`Mustard octagonal lounge of three routes-2.png`). A sunken octagonal pit with a mustard sofa ring; the Dock guide ahead in a rain street, the Bar guide left, the Floor guide right in a cobalt glass passage. No lead verdict yet (round 2 pending). At the last measure 4 of 13 shots were in the rule.
* **DJ Booth, `doom_booth`** (`Rhythm Booth, Three Hidden Routes-5.png`). Reads "a desk in a corridor to a violet door", but the room is a mustard foam tile box that repeats. Exposure: 2 of 8 shots in the rule; its tiles are flat mid-tones and need an art pass.
* **Loading Dock, `doom_dock`** (`Rainy Rhythm Club Loading Dock-6.png`). Reads "a rainy brick alley at night". Short: the street is a blue-grey mid-tone, not black tarmac with sodium pools; bright brick; the club door is a flat magenta rectangle. Exposure 8 of 8.
* **Balcony, `doom_balcony`** (`Rainy industrial rooftop, three musical paths-8.png`). Reads "a rooftop deck under the moon". Short: the facades are a grid of candy-coloured window squares; you do not see down into the drop; magenta deck grid lines; flat decal doors left and right; the dish is a placeholder. Exposure 8 of 8.
* **Mothership, `doom_mothership`** (`Mothership Ringwalk Over the Void-7.png`). Reads "a bone ring walk over a glowing pool". Short: the bone is violet, not cream; the pool is a corner; the arches are flat decals; the Booth guide is procedural. Exposure 8 of 8.
* **Underworld, `doom_underworld`** (`Three Paths Across the Basalt Abyss-4.png`; secondary `Three Visitors in the Basalt Underworld-6.png`). Reads "a lava canyon under a red sky". Short: the lava is a river, not a lake; the basalt stripes repeat and are brown-grey, not near-black; the cave and the left tunnel are blue-grey; the Mothership guide is procedural. Exposure 8 of 8.

Exposure rule: p50 0.25 to 0.38 and contrast (p95 - p5) of 0.40 or more, per 16:9 shot.

## Music

Each world is a track scene: it plays one recorded track at its own tempo from the first drop, with 16 lead-in bars and the normal chart. The full table (pack ids, titles, bpm, why) is `docs/doom/MUSIC.md`:

| World | Title | bpm |
| --- | --- | --- |
| Floor | Valley of the Shadows (Chase & Status Remix) | 174 |
| Bar | Warm Roller "Memory" | 174 |
| Lounge | In The Clouds | 175 |
| Booth | T-2000 | 174 |
| Dock | Shostakovich | 175 |
| Balcony | Zephyr | 172 |
| Mothership | Phantasm (Original Mix) | 174 |
| Underworld | Teddy Killerz - Night Train | 175 |

The picks were made from titles, artists, tempos and section structure in each pack's `track.json`. Nobody has listened. Please audition them.

To swap one: change one line in `content/run/track_scenes.json`, `"doom_<world>": {"track": "<pack id>"}`, and the matching row in `docs/doom/MUSIC.md`. The pack id is the folder name in the packs folder. Prefer 172 to 177 bpm so the downbeat lands on the stage's 174 clock.
If a pack is missing, or track scenes are off (`RW_RUN_TRACKS=0`), the scene falls back to its procedural arrangement.

Cuts: the two-cut virtual run (`RW_DOOM_WORLDS=1 RW_RUN_VIRTUAL=1 RW_RUN_BOT=perfect RW_RUN_ROUTES=left,right RW_RUN_START=doom_warehouse RW_RUN_UNTIL_PHASE=3` on `src/run/run_play.tscn`) played Warehouse, Bar, Lounge with blended cuts at 174 to 174 and 174 to 175 bpm. That is data; nobody has listened.
Note: a virtual run with `RW_RUN_UNTIL_PHASE` does not quit after printing its summary and holds the worktree's `godot.sh` lock until it is killed.

## How to shoot and measure

All need a window. Run from the repo root.

| Scene | Shots |
| --- | --- |
| Warehouse | `bash tools/doom/shoot_scene.sh --scene doom_warehouse`; walks: `python3 tools/doom/shoot_scene.py walk docs/shots/doom/warehouse` (or `RW_WALK=1`) |
| Bar | `python3 tools/doom/shoot_bar.py [--walk]` |
| Lounge | `bash tools/doom/shoot_lounge.sh`, then `python3 tools/doom/shoot_lounge.py walk docs/shots/doom/lounge` |
| Booth | `python3 tools/doom/shoot_booth.py` |
| Dock | `python3 tools/doom/shoot_dock.py` |
| Balcony | `python3 tools/doom/shoot_balcony.py` |
| Mothership | `python3 tools/doom/shoot_mothership.py` |
| Underworld | `python3 tools/doom/shoot_underworld.py` |
| A cut | `python3 tools/doom/shoot_cut.py` (`docs/shots/doom/cuts/warehouse_to_bar.jpg`) |

Output goes to `docs/shots/doom/<scene>/` (`contact.jpg`, and `walk_strip.jpg` with pose tables `walk_*.txt` where the scene has them). The Dock, Balcony and Booth contact sheets end with a row of guide states (selected, committed), made by `tools/doom/guide_states.py`; the Underworld sheet has the same pair.
`RW_KEEP=<dir>` keeps the full-size frames. Measure exposure before shrinking: `python -I tools/doom/frame_check.py <dir>` prints p5, p50 and p95 per 16:9 shot and for all together.

Tests: `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter doom_views` (also `doom_cuts`). Map check: `... -s tools/doom/check_doom_map.gd -- doom_<scene>`.

Verified headless on ab6dcf43: doom 2872, doom_cuts 46, choice_pitch 28, split_void 22, rail_paths 652, transition 17579, run_ 16695, playtest 2949, story 52991 checks, all 0 failures, 0 SCRIPT ERROR.

## Two engine findings from round 2

1. **The choice window did not hold at the reference viewpoint.** The rail moves one place per passed block, so with round 1's four-place stay loop the camera was still on its way when the window opened. Fixed on five scenes (Underworld, Mothership, Dock, Balcony, Booth): the loop is now one reveal plus the choice viewpoint. The Warehouse's loop is still the four places of round 1 (`warehouse.md`); agent A's round 2 should check the Warehouse, Bar and Lounge loops.
2. **The engine haze over a connected void darkens what should glow.** `void_top` puts a depth haze on the whole void group, which turned the Underworld's lava dark red and the Mothership's pool dark violet. Both scenes opt out with a shore piece (a small piece of lava or pool at the right level, not a void). A per-void "glow, no haze" key would say this directly; that engine hook is not built.

The `pitch` field (a downward look at the choice hold) works; see `docs/engine/GEOGRAPHY_WORLDS.md`. After a tap the camera turns toward the tapped guide and the walk-off starts at once.

## Rebuild commands (carried from the earlier sheet and the scene docs)

Per scene, then `python tools/run/make_doom.py` and `godot --headless --import`. Replace `<s>` with the scene name: warehouse, bar, lounge, booth, dock, balcony, mothership, underworld.

* Geometry: `python -I tools/doom/trace/<s>_scene.py && python -I tools/doom/convert.py --scene <s> --trace tools/doom/trace/<s>_pilot.json && python -I tools/doom/author_<s>.py`
* Art: `python -I tools/doom/art/make_<s>_art.py`. Exceptions: the Warehouse's art is `make_warehouse_art.py` plus `make_guides.py`; the Underworld, Mothership, Bar and Lounge also run `make_<s>_guides.py`; the Dock and Balcony art scripts call their guides script themselves. The Bar's trace script (`bar_scene.py`) is the one the old sheet ran before convert; its other old steps are in `docs/doom/scenes/bar.md`.

Details per scene: `docs/doom/scenes/<s>.md`.

## Round 2 list: still to tick

Underworld, Mothership, Dock, Balcony and Booth are ticked or carried in their scene docs (Booth's exposure item is partial). For the lead to tick when agent A merges (round 2 pending):

* [ ] Warehouse (round 2 pending): exposure (four short-contrast shots), the up walk from `wh_platform` (the 53.7 m warning), the stay loop.
* [ ] Bar (round 2 pending): exposure (17 of 21 shots outside the rule at the last measure), the stay loop, the procedural Booth guide.
* [ ] Lounge (round 2 pending): exposure (9 of 13 shots outside the rule at the last measure), the stay loop.

## Known limits (9 November)

* No human has played any Doom world on a screen or a phone. 16 of the 24 cuts were never looked at by eye. The two-cut run covers Warehouse, Bar, Lounge; `tests/test_doom_cuts.gd` covers the engine.
* The music is chosen by title, not by ear, and nobody has listened to the cuts.
* Exposure: 8 of 8 shots in the rule for Underworld, Mothership, Dock and Balcony; Booth 2 of 8 (flat mid-tone tiles, needs an art pass). Warehouse, Bar and Lounge are on their round 1 figures (round 2 pending).
* Long legs: the world swap can land after the drop (rulings 42, 42b). The Warehouse up leg from `wh_platform` is 53.7 m, over the 8-bar limit, and is being fixed.
* Guides still procedural: the Underworld's Mothership guide (95 px), the Mothership's Booth guide, the Bar's Booth guide. The Balcony's Mothership guide is 76 px at 16:9; its dish is a placeholder.
* Balcony: the viewpoint is 7 m back from the deck edge, so the drop is not seen into. Dock: the near right of the painting is thin; the furnace and van are flat billboards; the fence is a wall decal. Booth: the drop's facade reads as a flat blue wall in `route_left`.
* Underworld: the lava is a 6 m river; the tower is a terrace and billboard pillars, not nested rings. Mothership: the arches are flat decals.
* Warehouse: the terrace (+96) has no stairs. Every texture, prop and decal in the eight scenes is placeholder art or a cut from a painting.
* Lounge: the foreground sofa is never seen (the camera is not pitched down at the choice hold there).
* Engine: no per-void "glow, no haze" key; the workaround is a shore piece.
* Stale, not confirmed: the 7 November lines "no state-driven guides beyond what the existing choice staging does (sprite per state, no loop playback, no brightening lamp)", "the exits' door walks are played to the threshold before the cut" and "the terrace and the north-west nub are not connected to the ring". Guide-state captures and paced walk-outs now exist; I could not confirm the rest, so read them as stale.
